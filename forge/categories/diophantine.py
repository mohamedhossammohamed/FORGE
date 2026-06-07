"""
Category 22: Diophantine Equations

Generates linear Diophantine equations ax + by = c with constraint bounds.
Difficulty scales from high school (small integers) to frontier (large primes).
"""

import sympy
from sympy import gcd

from ..core.generator import ForgeCategory, Problem


class DiophantineCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "diophantine"
    
    @property
    def display_name(self) -> str:
        return "Diophantine Equations"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"magnitude": 10, "constraint_range": (1, 20)},
            2: {"magnitude": 30, "constraint_range": (1, 50)},
            3: {"magnitude": 100, "constraint_range": (1, 100)},
            4: {"magnitude": 500, "constraint_range": (1, 500)},
            5: {"magnitude": 2000, "constraint_range": (1, 2000)},
        }
        return params.get(difficulty, params[3])
    
    def _extended_gcd(self, a: int, b: int) -> tuple[int, int, int]:
        """Extended Euclidean Algorithm: returns (g, x, y) such that ax + by = g."""
        if a == 0:
            return b, 0, 1
        g, x1, y1 = self._extended_gcd(b % a, a)
        return g, y1 - (b // a) * x1, x1
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        magnitude = params["magnitude"]
        
        # Generate coefficients
        a = int(rng.integers(2, magnitude + 1))
        b = int(rng.integers(2, magnitude + 1))
        
        # Ensure gcd(a,b) divides c
        g = gcd(a, b)
        
        # Generate a valid c
        c = g * int(rng.integers(1, magnitude // g + 1))
        
        # Find the particular solution with smallest positive x
        # Using extended Euclidean algorithm
        g_val, x0, y0 = self._extended_gcd(a, b)
        
        # Scale to get solution for ax + by = c
        x0 = x0 * (c // g_val)
        y0 = y0 * (c // g_val)
        
        # General solution: x = x0 + (b/g)t, y = y0 - (a/g)t
        # Find smallest positive x
        b_div_g = b // g_val
        a_div_g = a // g_val
        
        # Adjust to smallest positive x
        if x0 <= 0:
            t = (-x0) // b_div_g + 1
            x_sol = x0 + b_div_g * t
            y_sol = y0 - a_div_g * t
        else:
            x_sol = x0
            y_sol = y0
        
        # Verify
        assert a * x_sol + b * y_sol == c
        
        question = (
            f"Find the solution (x, y) to the linear Diophantine equation:\n\n"
            f"{a}x + {b}y = {c}\n\n"
            f"where x is the smallest positive integer solution.\n"
            f"Provide x and y as integers."
        )
        
        answer = f"({x_sol}, {y_sol})"
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"a": a, "b": b, "c": c, "x": x_sol, "y": y_sol},
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade by parsing and verifying the solution."""
        try:
            # Parse prediction
            pred_clean = prediction.strip().replace(" ", "").strip("()")
            parts = pred_clean.split(",")
            if len(parts) != 2:
                return False
            
            x_pred = int(parts[0])
            y_pred = int(parts[1])
            
            # Parse answer
            ans_clean = answer.strip().replace(" ", "").strip("()")
            ans_parts = ans_clean.split(",")
            x_ans = int(ans_parts[0])
            y_ans = int(ans_parts[1])
            
            # Verify it's a valid solution
            # We need the metadata to verify
            # For now, check if it matches the expected answer
            return x_pred == x_ans and y_pred == y_ans
        except (ValueError, TypeError):
            return False
