import os
import sys
import base64
import logging
import traceback
import warnings

import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify


# --------------------------------------------------
# Ensure project root is available for imports
# --------------------------------------------------

parent_dir = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


from backend.algorithms.watermark_embedding import WatermarkEmbedder
from backend.algorithms.watermark_extraction import WatermarkExtractor


# --------------------------------------------------
# Application Factory
# --------------------------------------------------

def create_app():
    app = Flask(__name__)

    # Maximum upload size: 20 MB
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)

    # --------------------------------------------------
    # Home Page
    # --------------------------------------------------

    @app.route("/")
    def index():
        return render_template("index.html")

    # --------------------------------------------------
    # Health Check
    # --------------------------------------------------

    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "message": "Digital Watermarking System is running"
        }), 200

    # --------------------------------------------------
    # Embed Watermark
    # --------------------------------------------------

    @app.route("/embed", methods=["POST"])
    def embed():

        try:
            logger.info("Starting watermark embedding process")

            # Validate uploaded files
            if "cover" not in request.files:
                return jsonify({
                    "error": "Cover image is required"
                }), 400

            if "watermark" not in request.files:
                return jsonify({
                    "error": "Watermark image is required"
                }), 400

            cover_file = request.files["cover"]
            watermark_file = request.files["watermark"]

            # Validate filenames
            if cover_file.filename == "":
                return jsonify({
                    "error": "No cover image selected"
                }), 400

            if watermark_file.filename == "":
                return jsonify({
                    "error": "No watermark image selected"
                }), 400

            logger.info(
                f"Cover image: {cover_file.filename}"
            )

            logger.info(
                f"Watermark image: {watermark_file.filename}"
            )

            # Read uploaded files
            cover_bytes = cover_file.read()
            watermark_bytes = watermark_file.read()

            if not cover_bytes:
                return jsonify({
                    "error": "Cover image file is empty"
                }), 400

            if not watermark_bytes:
                return jsonify({
                    "error": "Watermark image file is empty"
                }), 400

            # Decode cover image
            cover_array = cv2.imdecode(
                np.frombuffer(cover_bytes, np.uint8),
                cv2.IMREAD_GRAYSCALE
            )

            # Decode watermark image
            watermark_array = cv2.imdecode(
                np.frombuffer(watermark_bytes, np.uint8),
                cv2.IMREAD_GRAYSCALE
            )

            # Validate decoded images
            if cover_array is None:
                logger.error("Failed to decode cover image")

                return jsonify({
                    "error": (
                        "Invalid cover image format. "
                        "Please use PNG, JPG, or JPEG."
                    )
                }), 400

            if watermark_array is None:
                logger.error("Failed to decode watermark image")

                return jsonify({
                    "error": (
                        "Invalid watermark image format. "
                        "Please use PNG, JPG, or JPEG."
                    )
                }), 400

            if cover_array.size == 0:
                return jsonify({
                    "error": "Cover image is empty"
                }), 400

            if watermark_array.size == 0:
                return jsonify({
                    "error": "Watermark image is empty"
                }), 400

            logger.info(
                f"Cover image shape: {cover_array.shape}"
            )

            logger.info(
                f"Watermark image shape: {watermark_array.shape}"
            )

            # --------------------------------------------------
            # Perform Watermark Embedding
            # --------------------------------------------------

            try:
                embedder = WatermarkEmbedder()

                result = embedder.embed(
                    cover_array,
                    watermark_array
                )

                if not isinstance(result, dict):
                    raise ValueError(
                        "Embedding algorithm returned an invalid result"
                    )

                if "watermarked_image" not in result:
                    raise ValueError(
                        "Embedding failed to produce watermarked_image"
                    )

                logger.info(
                    f"Embedding successful. "
                    f"Alpha: {result.get('alpha', 'N/A')}"
                )

            except Exception as e:

                logger.error(
                    "Watermark embedding failed:\n%s",
                    traceback.format_exc()
                )

                return jsonify({
                    "error": f"Embedding process failed: {str(e)}"
                }), 500

            # --------------------------------------------------
            # Process Watermarked Image
            # --------------------------------------------------

            watermarked_img = result["watermarked_image"]

            if not isinstance(watermarked_img, np.ndarray):
                watermarked_img = np.asarray(
                    watermarked_img
                )

            # Convert color image to grayscale if necessary
            if watermarked_img.ndim == 3:

                watermarked_img = cv2.cvtColor(
                    watermarked_img,
                    cv2.COLOR_BGR2GRAY
                )

            if watermarked_img.ndim != 2:
                raise ValueError(
                    f"Invalid watermarked image dimensions: "
                    f"{watermarked_img.ndim}"
                )

            # Convert safely to uint8
            watermarked_img = np.nan_to_num(
                watermarked_img,
                nan=0,
                posinf=255,
                neginf=0
            )

            watermarked_img = np.clip(
                watermarked_img,
                0,
                255
            ).astype(np.uint8)

            # Encode image
            success, img_encoded = cv2.imencode(
                ".png",
                watermarked_img
            )

            if not success or img_encoded is None:
                raise ValueError(
                    "Failed to encode watermarked image"
                )

            img_base64 = base64.b64encode(
                img_encoded.tobytes()
            ).decode("utf-8")

            logger.info(
                "Watermark embedding completed successfully"
            )

            # --------------------------------------------------
            # Return Response
            # --------------------------------------------------

            return jsonify({
                "success": True,
                "image": (
                    f"data:image/png;base64,{img_base64}"
                ),
                "alpha": float(
                    result.get("alpha", 0)
                ),
                "metrics": result.get(
                    "metrics",
                    {}
                )
            }), 200

        except Exception as e:

            logger.error(
                "Unexpected embedding error:\n%s",
                traceback.format_exc()
            )

            return jsonify({
                "error": f"Unexpected server error: {str(e)}"
            }), 500

    # --------------------------------------------------
    # Extract Watermark
    # --------------------------------------------------

    @app.route("/extract", methods=["POST"])
    def extract():

        try:
            logger.info(
                "Starting watermark extraction process"
            )

            # Validate uploaded files
            if "watermarked" not in request.files:
                return jsonify({
                    "error": "Watermarked image is required"
                }), 400

            if "original" not in request.files:
                return jsonify({
                    "error": "Original cover image is required"
                }), 400

            if "alpha" not in request.form:
                return jsonify({
                    "error": "Alpha value is required"
                }), 400

            watermarked_file = request.files[
                "watermarked"
            ]

            original_file = request.files[
                "original"
            ]

            # Validate alpha
            try:

                alpha = float(
                    request.form["alpha"]
                )

                if alpha <= 0:
                    raise ValueError(
                        "Alpha must be greater than zero"
                    )

            except (ValueError, TypeError):

                return jsonify({
                    "error": (
                        "Invalid alpha value. "
                        "Please enter a number greater than 0."
                    )
                }), 400

            # Validate filenames
            if watermarked_file.filename == "":
                return jsonify({
                    "error": "No watermarked image selected"
                }), 400

            if original_file.filename == "":
                return jsonify({
                    "error": "No original cover image selected"
                }), 400

            # Read files
            watermarked_bytes = watermarked_file.read()
            original_bytes = original_file.read()

            if not watermarked_bytes:
                return jsonify({
                    "error": "Watermarked image is empty"
                }), 400

            if not original_bytes:
                return jsonify({
                    "error": "Original image is empty"
                }), 400

            # Decode images
            watermarked_array = cv2.imdecode(
                np.frombuffer(
                    watermarked_bytes,
                    np.uint8
                ),
                cv2.IMREAD_GRAYSCALE
            )

            original_array = cv2.imdecode(
                np.frombuffer(
                    original_bytes,
                    np.uint8
                ),
                cv2.IMREAD_GRAYSCALE
            )

            if watermarked_array is None:
                return jsonify({
                    "error": "Invalid watermarked image format"
                }), 400

            if original_array is None:
                return jsonify({
                    "error": "Invalid original image format"
                }), 400

            if (
                watermarked_array.size == 0
                or original_array.size == 0
            ):
                return jsonify({
                    "error": "One or more images are empty"
                }), 400

            logger.info(
                f"Watermarked shape: "
                f"{watermarked_array.shape}"
            )

            logger.info(
                f"Original shape: "
                f"{original_array.shape}"
            )

            # Ensure matching dimensions
            if (
                watermarked_array.shape
                != original_array.shape
            ):

                logger.warning(
                    "Image dimensions differ. "
                    "Resizing watermarked image."
                )

                watermarked_array = cv2.resize(
                    watermarked_array,
                    (
                        original_array.shape[1],
                        original_array.shape[0]
                    )
                )

            # --------------------------------------------------
            # Perform Watermark Extraction
            # --------------------------------------------------

            try:

                extractor = WatermarkExtractor()

                result = extractor.extract(
                    watermarked_array,
                    original_array,
                    alpha
                )

                if not isinstance(result, dict):
                    raise ValueError(
                        "Extraction algorithm returned an invalid result"
                    )

                if not result.get(
                    "extraction_successful",
                    False
                ):
                    raise ValueError(
                        result.get(
                            "error",
                            "Watermark extraction failed"
                        )
                    )

                logger.info(
                    "Watermark extraction successful"
                )

            except Exception as e:

                logger.error(
                    "Watermark extraction failed:\n%s",
                    traceback.format_exc()
                )

                return jsonify({
                    "error": (
                        f"Extraction process failed: {str(e)}"
                    )
                }), 500

            # --------------------------------------------------
            # Process Extracted Watermark
            # --------------------------------------------------

            extracted = result.get(
                "extracted_watermark"
            )

            if extracted is None:
                raise ValueError(
                    "No extracted watermark returned"
                )

            if not isinstance(
                extracted,
                np.ndarray
            ):
                extracted = np.asarray(
                    extracted
                )

            # Handle 1D data
            if extracted.ndim == 1:

                extracted = extracted.flatten()

                size = int(
                    np.ceil(
                        np.sqrt(extracted.size)
                    )
                )

                padded = np.zeros(
                    size * size,
                    dtype=np.float64
                )

                padded[:extracted.size] = extracted

                extracted = padded.reshape(
                    (size, size)
                )

            # Convert 3D image if necessary
            elif extracted.ndim == 3:

                extracted = cv2.cvtColor(
                    extracted,
                    cv2.COLOR_BGR2GRAY
                )

            if extracted.ndim != 2:
                raise ValueError(
                    "Extracted watermark has invalid dimensions"
                )

            # Normalize safely
            extracted = np.nan_to_num(
                extracted,
                nan=0,
                posinf=255,
                neginf=0
            )

            extracted_min = np.min(extracted)
            extracted_max = np.max(extracted)

            if extracted_max > extracted_min:

                extracted = (
                    (extracted - extracted_min)
                    / (extracted_max - extracted_min)
                    * 255
                )

            extracted = np.clip(
                extracted,
                0,
                255
            ).astype(np.uint8)

            # Encode image
            success, img_encoded = cv2.imencode(
                ".png",
                extracted
            )

            if not success or img_encoded is None:
                raise ValueError(
                    "Failed to encode extracted watermark"
                )

            img_base64 = base64.b64encode(
                img_encoded.tobytes()
            ).decode("utf-8")

            logger.info(
                "Watermark extraction completed successfully"
            )

            # --------------------------------------------------
            # Return Response
            # --------------------------------------------------

            return jsonify({
                "success": True,
                "image": (
                    f"data:image/png;base64,{img_base64}"
                ),
                "metrics": result.get(
                    "metrics",
                    {}
                )
            }), 200

        except Exception as e:

            logger.error(
                "Unexpected extraction error:\n%s",
                traceback.format_exc()
            )

            return jsonify({
                "error": (
                    f"Unexpected server error: {str(e)}"
                )
            }), 500

    # --------------------------------------------------
    # Handle Large File Upload
    # --------------------------------------------------

    @app.errorhandler(413)
    def request_entity_too_large(error):

        return jsonify({
            "error": (
                "File is too large. "
                "Maximum allowed size is 20 MB."
            )
        }), 413

    return app


# --------------------------------------------------
# Create application for Gunicorn / Render
# --------------------------------------------------

app = create_app()


# --------------------------------------------------
# Local Development Server
# --------------------------------------------------

if __name__ == "__main__":

    warnings.filterwarnings(
        "ignore",
        category=RuntimeWarning,
        message=".*overflow.*"
    )

    port = int(
        os.environ.get("PORT", 5000)
    )

    logging.getLogger(__name__).info(
        f"Starting server on 0.0.0.0:{port}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )