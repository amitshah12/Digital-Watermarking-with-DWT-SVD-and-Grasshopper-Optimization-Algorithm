import numpy as np
from typing import Dict, Optional
import logging
import cv2

from .dwt_transform import DWTTransform
from .svd_transform import SVDTransform
from .goa_optimizer import GrasshopperOptimizer
from ..utils.metrics import MetricsCalculator


class WatermarkEmbedder:
    """
    Main watermark embedding class that orchestrates the
    DWT-SVD-GOA watermarking pipeline.
    """

    def __init__(
        self,
        goa_params: Optional[Dict] = None,
        dwt_params: Optional[Dict] = None
    ):
        """
        Initialize the watermark embedder.
        """

        self.dwt = DWTTransform(**(dwt_params or {}))
        self.svd = SVDTransform()

        # Use smaller defaults for web deployment.
        # These can still be overridden through goa_params.
        default_goa_params = {
            "n_grasshoppers": 8,
            "max_iterations": 10,
            "c_min": 0.00001,
            "c_max": 1.0,
            "f_min": 0.01,
            "f_max": 1.0
        }

        if goa_params:
            default_goa_params.update(goa_params)

        self.goa = GrasshopperOptimizer(**default_goa_params)
        self.metrics = MetricsCalculator()
        self.logger = logging.getLogger(__name__)

    def fitness_function(self, alpha) -> float:
        """
        Fitness function used by GOA.

        This version avoids unnecessary image reconstruction during
        optimization. Instead, it estimates the embedding strength
        directly from the singular value modification.

        Lower fitness is better.
        """

        if not hasattr(self, "_temp_data"):
            raise RuntimeError("Temporary embedding data not set")

        try:
            # Convert alpha safely to scalar
            if isinstance(alpha, (list, tuple, np.ndarray)):
                alpha = float(np.asarray(alpha).flatten()[0])
            else:
                alpha = float(alpha)

            # Keep alpha inside valid range
            alpha = float(np.clip(alpha, 0.01, 1.0))

            original_s = self._temp_data["S"]
            watermark = self._temp_data["resized_watermark"]

            # Resize watermark if necessary
            if watermark.shape != original_s.shape:
                watermark = cv2.resize(
                    watermark,
                    (original_s.shape[1], original_s.shape[0]),
                    interpolation=cv2.INTER_AREA
                )

            # Estimate modification caused by alpha.
            #
            # This is much cheaper than performing:
            # SVD reconstruction -> inverse DWT -> PSNR -> SSIM
            modified_s = self.svd.modify_singular_values(
                original_s,
                alpha,
                watermark
            )

            # Calculate normalized distortion
            distortion = np.mean(
                np.abs(modified_s - original_s)
            )

            # Normalize distortion relative to the singular values
            scale = np.mean(np.abs(original_s)) + 1e-8
            normalized_distortion = distortion / scale

            # Encourage reasonable embedding strength while
            # penalizing excessive distortion.
            #
            # A very small alpha is also discouraged because the
            # watermark may become too weak.
            strength_penalty = 0.02 / (alpha + 1e-8)

            fitness = normalized_distortion + strength_penalty

            if not np.isfinite(fitness):
                return 1e10

            return float(fitness)

        except Exception as e:
            self.logger.warning(
                f"Fitness evaluation failed: {str(e)}"
            )
            return 1e10

    def embed(
        self,
        cover_image: np.ndarray,
        watermark: np.ndarray
    ) -> Dict:
        """
        Embed watermark into cover image using DWT-SVD-GOA.

        Args:
            cover_image: Original image to watermark
            watermark: Watermark image to embed

        Returns:
            Dict containing:
                - watermarked_image
                - alpha
                - metrics
        """

        try:
            # --------------------------------------------------
            # 1. Validate input images
            # --------------------------------------------------

            if cover_image is None or cover_image.size == 0:
                raise ValueError("Cover image is invalid")

            if watermark is None or watermark.size == 0:
                raise ValueError("Watermark image is invalid")

            cover_image = np.asarray(cover_image)
            watermark = np.asarray(watermark)

            # Convert cover image to grayscale if required
            if cover_image.ndim == 3:
                cover_image = cv2.cvtColor(
                    cover_image,
                    cv2.COLOR_BGR2GRAY
                )

            # Convert watermark to grayscale if required
            if watermark.ndim == 3:
                watermark = cv2.cvtColor(
                    watermark,
                    cv2.COLOR_BGR2GRAY
                )

            if cover_image.ndim != 2:
                raise ValueError(
                    "Cover image must be a 2D grayscale image"
                )

            if watermark.ndim != 2:
                raise ValueError(
                    "Watermark must be a 2D grayscale image"
                )

            # Ensure uint8 format
            cover_image = np.clip(
                cover_image,
                0,
                255
            ).astype(np.uint8)

            watermark = np.clip(
                watermark,
                0,
                255
            ).astype(np.uint8)

            # --------------------------------------------------
            # 2. Ensure dimensions are even for DWT
            # --------------------------------------------------

            height, width = cover_image.shape[:2]

            even_height = height if height % 2 == 0 else height - 1
            even_width = width if width % 2 == 0 else width - 1

            if (
                even_height != height
                or even_width != width
            ):
                cover_image = cv2.resize(
                    cover_image,
                    (even_width, even_height),
                    interpolation=cv2.INTER_AREA
                )

            original_cover = cover_image.copy()

            # --------------------------------------------------
            # 3. DWT decomposition
            # --------------------------------------------------

            dwt_components = self.dwt.decompose(
                cover_image
            )

            ll_band = np.asarray(
                dwt_components["ll_band"]
            )

            if ll_band.ndim != 2:
                raise ValueError(
                    f"Expected 2D LL band, got shape {ll_band.shape}"
                )

            # --------------------------------------------------
            # 4. Resize watermark to LL band
            # --------------------------------------------------

            resized_watermark = cv2.resize(
                watermark,
                (ll_band.shape[1], ll_band.shape[0]),
                interpolation=cv2.INTER_AREA
            )

            resized_watermark = np.asarray(
                resized_watermark,
                dtype=np.float64
            )

            # --------------------------------------------------
            # 5. SVD decomposition
            # --------------------------------------------------

            svd_components = self.svd.decompose(
                ll_band
            )

            U = np.asarray(svd_components["U"])
            S = np.asarray(svd_components["S"])
            V = np.asarray(svd_components["V"])

            # --------------------------------------------------
            # 6. Store only required data for GOA
            # --------------------------------------------------

            self._temp_data = {
                "S": S,
                "resized_watermark": resized_watermark
            }

            # --------------------------------------------------
            # 7. GOA optimization
            #
            # 8 grasshoppers × 10 iterations = approximately
            # 80 lightweight fitness evaluations.
            # --------------------------------------------------

            try:
                goa_result = self.goa.optimize(
                    self.fitness_function
                )

                best_solution = goa_result.get(
                    "best_solution"
                )

                if best_solution is None:
                    optimal_alpha = 0.05
                else:
                    optimal_alpha = float(
                        np.asarray(best_solution).flatten()[0]
                    )

            except Exception as e:
                self.logger.warning(
                    "GOA optimization failed. "
                    f"Using default alpha. Error: {str(e)}"
                )

                optimal_alpha = 0.05

            # Keep alpha within valid range
            optimal_alpha = float(
                np.clip(
                    optimal_alpha,
                    0.01,
                    1.0
                )
            )

            self.logger.info(
                f"Optimal alpha found: {optimal_alpha}"
            )

            # --------------------------------------------------
            # 8. Final watermark embedding
            # --------------------------------------------------

            modified_S = self.svd.modify_singular_values(
                S,
                optimal_alpha,
                resized_watermark
            )

            # --------------------------------------------------
            # 9. Reconstruct modified LL band
            # --------------------------------------------------

            modified_ll = self.svd.reconstruct(
                U,
                modified_S,
                V
            )

            modified_ll = np.asarray(
                modified_ll
            )

            # Ensure correct LL band dimensions
            if modified_ll.shape != ll_band.shape:
                modified_ll = cv2.resize(
                    modified_ll,
                    (ll_band.shape[1], ll_band.shape[0]),
                    interpolation=cv2.INTER_CUBIC
                )

            # --------------------------------------------------
            # 10. Replace LL band in DWT coefficients
            # --------------------------------------------------

            coefficients = list(
                dwt_components["coefficients"]
            )

            if len(coefficients) == 0:
                raise ValueError(
                    "DWT coefficient list is empty"
                )

            coefficients[0] = modified_ll

            # --------------------------------------------------
            # 11. Inverse DWT
            # --------------------------------------------------

            watermarked_image = self.dwt.reconstruct(
                coefficients
            )

            watermarked_image = np.asarray(
                watermarked_image
            )

            # Ensure output dimensions match cover image
            if watermarked_image.shape != original_cover.shape:
                watermarked_image = cv2.resize(
                    watermarked_image,
                    (
                        original_cover.shape[1],
                        original_cover.shape[0]
                    ),
                    interpolation=cv2.INTER_CUBIC
                )

            # Convert to valid image
            watermarked_image = np.clip(
                watermarked_image,
                0,
                255
            ).astype(np.uint8)

            # --------------------------------------------------
            # 12. Calculate final metrics
            #
            # Metrics are calculated only once, after optimization.
            # --------------------------------------------------

            final_metrics = (
                self.metrics.calculate_all_metrics(
                    original_cover,
                    watermarked_image
                )
            )

            self.logger.info(
                f"Embedding completed successfully. "
                f"Alpha: {optimal_alpha}, "
                f"Metrics: {final_metrics}"
            )

            return {
                "watermarked_image": watermarked_image,
                "alpha": optimal_alpha,
                "metrics": final_metrics
            }

        except Exception as e:
            self.logger.error(
                f"Embedding failed: {str(e)}",
                exc_info=True
            )
            raise

        finally:
            # Clean up temporary optimization data
            if hasattr(self, "_temp_data"):
                del self._temp_data