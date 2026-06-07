"""
Category 3: Matrix Determinants

Generates N×N integer matrices and computes determinants.
Difficulty scales from undergraduate (N=3) to frontier (N=8, dense).
"""

import numpy as np
from ..core.generator import ForgeCategory, Problem


class MatrixDetCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "matrix_det"
    
    @property
    def display_name(self) -> str:
        return "Matrix Determinants"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n": 2, "magnitude": 10, "sparsity": 0.0},
            2: {"n": 3, "magnitude": 20, "sparsity": 0.0},
            3: {"n": 4, "magnitude": 50, "sparsity": 0.1},
            4: {"n": 6, "magnitude": 100, "sparsity": 0.2},
            5: {"n": 8, "magnitude": 200, "sparsity": 0.3},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n = params["n"]
        magnitude = params["magnitude"]
        sparsity = params["sparsity"]
        
        # Generate matrix
        matrix = rng.integers(-magnitude, magnitude + 1, size=(n, n))
        
        # Apply sparsity
        if sparsity > 0:
            mask = rng.random(size=(n, n)) < sparsity
            matrix[mask] = 0
        
        # Compute determinant
        det = int(round(np.linalg.det(matrix)))
        
        # Format matrix
        matrix_str = "\n".join(
            "[" + "  ".join(f"{x:4d}" for x in row) + "]"
            for row in matrix
        )
        
        question = (
            f"Compute the determinant of the following {n}×{n} matrix:\n\n"
            f"{matrix_str}\n\n"
            f"Provide the exact integer result."
        )
        
        return Problem(
            question=question,
            answer=det,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"matrix": matrix.tolist(), "n": n},
        )
    
    def grade(self, prediction: str, answer: int) -> bool:
        try:
            pred = prediction.strip().replace(',', '').replace(' ', '')
            return int(pred) == int(answer)
        except (ValueError, TypeError):
            return False
