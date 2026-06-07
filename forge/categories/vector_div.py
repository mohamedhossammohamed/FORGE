"""
Category 17: Vector Calculus - Divergence

Generates 3D vector fields and computes divergence.
Difficulty scales from undergraduate (linear polynomials) to frontier (nested transcendentals).
"""

import sympy
from sympy import symbols, diff, sin, cos, exp, ln, simplify, sympify

from ..core.generator import ForgeCategory, Problem


class VectorDivCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "vector_div"
    
    @property
    def display_name(self) -> str:
        return "Vector Calculus: Divergence"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n_terms": 1, "max_degree": 1, "use_transcendental": False},
            2: {"n_terms": 2, "max_degree": 2, "use_transcendental": False},
            3: {"n_terms": 3, "max_degree": 2, "use_transcendental": True},
            4: {"n_terms": 4, "max_degree": 3, "use_transcendental": True},
            5: {"n_terms": 5, "max_degree": 4, "use_transcendental": True},
        }
        return params.get(difficulty, params[3])
    
    def _generate_term(self, x, y, z, degree, use_transcendental, rng):
        """Generate a single term for a vector field component."""
        # Choose variables
        vars_used = []
        for var in [x, y, z]:
            if rng.random() < 0.5:
                vars_used.append(var)
        
        if not vars_used:
            vars_used = [x]
        
        # Build monomial
        term = 1
        remaining_degree = degree
        for var in vars_used:
            exponent = int(rng.integers(0, remaining_degree + 1))
            term *= var ** exponent
            remaining_degree -= exponent
        
        # Add coefficient
        coeff = int(rng.integers(-5, 6))
        term *= coeff
        
        # Optionally add transcendental function
        if use_transcendental and rng.random() < 0.3:
            func_choice = rng.integers(0, 3)
            var = [x, y, z][int(rng.integers(0, 3))]
            if func_choice == 0:
                term = term * sin(var)
            elif func_choice == 1:
                term = term * cos(var)
            else:
                term = term * exp(var)
        
        return term
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        x, y, z = symbols('x y z')
        
        # Generate each component of F = (Fx, Fy, Fz)
        Fx = 0
        Fy = 0
        Fz = 0
        
        for _ in range(params["n_terms"]):
            Fx += self._generate_term(x, y, z, params["max_degree"], 
                                     params["use_transcendental"], rng)
            Fy += self._generate_term(x, y, z, params["max_degree"],
                                     params["use_transcendental"], rng)
            Fz += self._generate_term(x, y, z, params["max_degree"],
                                     params["use_transcendental"], rng)
        
        # Compute divergence: div F = dFx/dx + dFy/dy + dFz/dz
        div_F = diff(Fx, x) + diff(Fy, y) + diff(Fz, z)
        div_F = simplify(div_F)
        
        # Format
        F_str = f"F(x,y,z) = ({Fx}, {Fy}, {Fz})"
        
        question = (
            f"Compute the divergence of the following vector field "
            f"in Cartesian coordinates:\n\n"
            f"{F_str}\n\n"
            f"The divergence is ∇·F = ∂Fx/∂x + ∂Fy/∂y + ∂Fz/∂z\n"
            f"Simplify your answer."
        )
        
        answer = str(div_F)
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"F": [str(Fx), str(Fy), str(Fz)], "div_F": str(div_F)},
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade using symbolic equivalence."""
        try:
            pred = sympify(prediction.strip())
            target = sympify(answer)
            
            # Check symbolic equivalence
            diff = simplify(pred - target)
            return diff == 0
        except:
            return False
