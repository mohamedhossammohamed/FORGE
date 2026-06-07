"""
Category 21: Taylor Series Coefficients

Generates compound transcendental functions for Maclaurin series expansion.
Difficulty scales from undergraduate (degree 3) to frontier (degree 8).
"""

import sympy
from sympy import Symbol, exp, sin, cos, ln, factorial, series, Rational, oo

from ..core.generator import ForgeCategory, Problem


class TaylorSeriesCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "taylor_series"
    
    @property
    def display_name(self) -> str:
        return "Taylor Series Coefficients"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"target_degree": 3, "n_functions": 1, "use_composition": False},
            2: {"target_degree": 4, "n_functions": 1, "use_composition": False},
            3: {"target_degree": 5, "n_functions": 2, "use_composition": False},
            4: {"target_degree": 6, "n_functions": 2, "use_composition": True},
            5: {"target_degree": 8, "n_functions": 3, "use_composition": True},
        }
        return params.get(difficulty, params[3])
    
    def _generate_function(self, x, rng, use_composition=False):
        """Generate a random function for Taylor series expansion."""
        choice = rng.integers(0, 5)
        
        if choice == 0:
            return exp(x)
        elif choice == 1:
            return sin(x)
        elif choice == 2:
            return cos(x)
        elif choice == 3:
            coeff = int(rng.integers(2, 5))
            return exp(coeff * x)
        elif choice == 4:
            coeff = int(rng.integers(2, 5))
            return sin(coeff * x)
        else:
            return cos(x)
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        x = Symbol('x')
        target_degree = params["target_degree"]
        n_functions = params["n_functions"]
        
        # Generate compound function
        func = self._generate_function(x, rng, params["use_composition"])
        for _ in range(n_functions - 1):
            other_func = self._generate_function(x, rng, params["use_composition"])
            op = rng.integers(0, 3)
            if op == 0:
                func = func * other_func
            elif op == 1:
                func = func + other_func
            else:
                func = func * x  # Multiply by x
        
        # Compute Taylor series
        taylor = series(func, x, 0, target_degree + 1)
        
        # Extract the coefficient of x^n
        coeff = taylor.coeff(x, target_degree)
        
        # Ensure coefficient is non-zero
        while coeff == 0:
            # Regenerate with slight modification
            func = func * x + self._generate_function(x, rng)
            taylor = series(func, x, 0, target_degree + 1)
            coeff = taylor.coeff(x, target_degree)
        
        # Format
        func_str = str(func).replace("**", "^")
        
        # Simplify coefficient to fraction if possible
        coeff_simplified = sympy.nsimplify(coeff, rational=False)
        
        question = (
            f"Find the coefficient of x^{target_degree} in the Maclaurin series "
            f"(Taylor series at x=0) expansion of:\n\n"
            f"f(x) = {func_str}\n\n"
            f"Provide the coefficient as an exact fraction."
        )
        
        answer = str(coeff_simplified)
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "function": str(func),
                "target_degree": target_degree,
                "coefficient": str(coeff_simplified),
            },
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade using symbolic equivalence of the coefficient."""
        try:
            pred = sympy.sympify(prediction.strip())
            target = sympy.sympify(answer)
            
            # Check symbolic equivalence
            diff = sympy.simplify(pred - target)
            return diff == 0
        except:
            return False
