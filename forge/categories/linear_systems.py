"""
Category 15: Systems of Linear Equations

Generates N×N linear systems with guaranteed integer/fractional solutions.
Difficulty scales from high school (N=2) to frontier (N=6, dense fractional).
"""

import numpy as np
from fractions import Fraction
import sympy
from sympy import Matrix, Rational

from ..core.generator import ForgeCategory, Problem


class LinearSystemsCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "linear_systems"
    
    @property
    def display_name(self) -> str:
        return "Systems of Linear Equations"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n": 2, "magnitude": 10, "use_fractions": False},
            2: {"n": 3, "magnitude": 15, "use_fractions": False},
            3: {"n": 4, "magnitude": 20, "use_fractions": True},
            4: {"n": 5, "magnitude": 30, "use_fractions": True},
            5: {"n": 6, "magnitude": 50, "use_fractions": True},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n = params["n"]
        magnitude = params["magnitude"]
        use_fractions = params["use_fractions"]
        
        # Generate solution first
        if use_fractions:
            solution = [Rational(int(rng.integers(-magnitude, magnitude + 1)), 
                               int(rng.integers(1, 6))) for _ in range(n)]
        else:
            solution = [int(rng.integers(-magnitude, magnitude + 1)) for _ in range(n)]
        
        # Generate coefficient matrix with full rank
        while True:
            A = Matrix([[int(rng.integers(-10, 11)) for _ in range(n)] for _ in range(n)])
            if A.det() != 0:
                break
        
        # Compute right-hand side: b = A * x
        x = Matrix(solution)
        b = A * x
        
        # Format system
        variables = [f"x{i+1}" for i in range(n)]
        equations = []
        for i in range(n):
            terms = []
            for j in range(n):
                coeff = A[i, j]
                var = variables[j]
                if coeff == 0:
                    continue
                elif coeff == 1:
                    terms.append(var)
                elif coeff == -1:
                    terms.append(f"-{var}")
                else:
                    terms.append(f"{coeff}{var}")
            
            eq_str = " + ".join(terms).replace("+ -", "- ")
            equations.append(f"{eq_str} = {b[i]}")
        
        system_str = "\n".join(equations)
        
        # Format solution
        solution_str = ", ".join(
            f"{var} = {val}" for var, val in zip(variables, solution)
        )
        
        question = (
            f"Solve the following system of {n} linear equations:\n\n"
            f"{system_str}\n\n"
            f"Provide the solution as exact values (fractions if needed)."
        )
        
        return Problem(
            question=question,
            answer=solution_str,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "A": A.tolist(),
                "b": [int(v) for v in b],
                "solution": [str(s) for s in solution],
            },
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade by parsing and comparing solution vectors."""
        try:
            # Parse prediction
            pred_values = self._parse_solution(prediction)
            ans_values = self._parse_solution(answer)
            
            if len(pred_values) != len(ans_values):
                return False
            
            # Compare each value
            for p, a in zip(pred_values, ans_values):
                if isinstance(a, int):
                    if p != a:
                        return False
                else:
                    # Fraction comparison
                    if Fraction(p) != Fraction(a):
                        return False
            
            return True
        except:
            return False
    
    def _parse_solution(self, text: str) -> list:
        """Parse solution string into list of values."""
        import re
        # Extract values from "x1 = val, x2 = val, ..."
        matches = re.findall(r'=\s*([^,]+)', text)
        values = []
        for m in matches:
            m = m.strip()
            if '/' in m:
                values.append(Fraction(m))
            else:
                try:
                    values.append(int(m))
                except:
                    values.append(Fraction(m))
        return values
