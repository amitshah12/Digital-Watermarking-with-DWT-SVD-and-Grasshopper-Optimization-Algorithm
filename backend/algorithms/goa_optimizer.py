import numpy as np
from typing import Callable, Dict
import logging


class GrasshopperOptimizer:
    """
    Lightweight Grasshopper Optimization Algorithm (GOA)
    for optimizing the watermark embedding strength alpha.

    This implementation is designed to keep the optimization practical
    for a web application while preserving the GOA-based search process.
    """

    def __init__(
        self,
        n_grasshoppers: int = 10,
        max_iterations: int = 10,
        c_min: float = 0.00001,
        c_max: float = 1.0,
        f_min: float = 0.01,
        f_max: float = 1.0
    ):
        """
        Initialize GOA optimizer.

        Args:
            n_grasshoppers: Number of search agents.
            max_iterations: Maximum optimization iterations.
            c_min: Minimum exploration coefficient.
            c_max: Maximum exploration coefficient.
            f_min: Lower bound of alpha.
            f_max: Upper bound of alpha.
        """

        self.n_grasshoppers = n_grasshoppers
        self.max_iterations = max_iterations

        self.c_min = c_min
        self.c_max = c_max

        self.f_min = f_min
        self.f_max = f_max

        self.best_solution = None
        self.best_fitness = float("inf")
        self.convergence_curve = []

        self.logger = logging.getLogger(__name__)

    def optimize(
        self,
        objective_function: Callable,
        dims: int = 1
    ) -> Dict:
        """
        Execute the Grasshopper Optimization Algorithm.

        Args:
            objective_function: Function to minimize.
            dims: Number of dimensions.

        Returns:
            Dictionary containing best solution, best fitness,
            and convergence history.
        """

        # Initialize population
        population = np.random.uniform(
            self.f_min,
            self.f_max,
            (self.n_grasshoppers, dims)
        )

        self.best_solution = None
        self.best_fitness = float("inf")
        self.convergence_curve = []

        # Evaluate initial population
        for iteration in range(self.max_iterations):

            # Gradually reduce exploration
            if self.max_iterations > 1:
                c = self.c_max - (
                    iteration *
                    (self.c_max - self.c_min) /
                    (self.max_iterations - 1)
                )
            else:
                c = self.c_min

            # -----------------------------------
            # Evaluate all grasshoppers
            # -----------------------------------

            fitness_values = np.empty(
                self.n_grasshoppers,
                dtype=float
            )

            for i in range(self.n_grasshoppers):

                try:
                    alpha = float(population[i, 0])

                    fitness = objective_function(alpha)

                    if not np.isfinite(fitness):
                        fitness = 1e10

                except Exception as e:

                    self.logger.warning(
                        "Fitness evaluation failed: %s",
                        str(e)
                    )

                    fitness = 1e10

                fitness_values[i] = fitness

            # -----------------------------------
            # Update global best
            # -----------------------------------

            best_index = np.argmin(fitness_values)

            if (
                self.best_solution is None
                or fitness_values[best_index] < self.best_fitness
            ):

                self.best_fitness = float(
                    fitness_values[best_index]
                )

                self.best_solution = (
                    population[best_index].copy()
                )

            self.convergence_curve.append(
                self.best_fitness
            )

            # -----------------------------------
            # Update population
            # -----------------------------------

            for i in range(self.n_grasshoppers):

                if dims == 1:
                    # For alpha optimization, move candidates
                    # toward the best solution with controlled
                    # random exploration.

                    direction = (
                        self.best_solution[0]
                        - population[i, 0]
                    )

                    exploration = np.random.uniform(
                        -1.0,
                        1.0
                    )

                    step = (
                        c * direction
                        + exploration
                        * c
                        * (self.f_max - self.f_min)
                        * 0.1
                    )

                    population[i, 0] += step

                else:

                    # Generic multi-dimensional update
                    direction = (
                        self.best_solution
                        - population[i]
                    )

                    exploration = np.random.uniform(
                        -1.0,
                        1.0,
                        dims
                    )

                    population[i] += (
                        c * direction
                        + exploration
                        * c
                        * (self.f_max - self.f_min)
                        * 0.1
                    )

                # Keep values within bounds
                population[i] = np.clip(
                    population[i],
                    self.f_min,
                    self.f_max
                )

            self.logger.info(
                "GOA iteration %d/%d | "
                "Best alpha: %.6f | "
                "Best fitness: %.6f",
                iteration + 1,
                self.max_iterations,
                float(self.best_solution[0]),
                self.best_fitness
            )

        return {
            "best_solution": self.best_solution,
            "best_fitness": self.best_fitness,
            "convergence": self.convergence_curve
        }