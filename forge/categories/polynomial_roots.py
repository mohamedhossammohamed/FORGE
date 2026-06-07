"""
Category 2: Polynomial Root Finding

Generates polynomials via expansion of seeded roots and asks for all roots.
Difficulty scales from high school (degree 2, integer roots) to frontier (degree 7, complex).
"""

import sympy
from sympy import Symbol, expand, roots, Rational, I, sqrt, solve

from ..core.generator import ForgeCategory, Problem


class PolynomialRootsCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "polynomial_roots"
    
    @property
    def display_name(self) -> str:
        return "Polynomial Root Finding"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"degree": 2, "use_complex": False, "magnitude": 10},
            2: {"degree": 3, "use_complex": False, "magnitude": 15},
            3: {"degree": 4, "use_complex": False, "magnitude": 20},
            4: {"degree": 5, "use_complex": True, "magnitude": 10},
            5: {"degree": 7, "use_complex": True, "magnitude": 15},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        degree = params["degree"]
        use_complex = params["use_complex"]
        magnitude = params["magnitude"]
        
        x = Symbol('x')
        
        # Generate roots
        root_list = []
        while len(root_list) < degree:
            if use_complex and rng.random() < 0.3 and len(root_list) < degree - 1:
                # Complex conjugate pair
                real = Rational(int(rng.integers(-magnitude, magnitude + 1)), 
                              int(rng.integers(1, 4)))
                imag = Rational(int(rng.integers(1, magnitude // 2 + 1)),
                              int(rng.integers(1, 4)))
                root_list.append(real + I * imag)
                root_list.append(real - I * imag)
            else:
                # Real root (possibly rational)
                if rng.random() < 0.5:
                    root_list.append(int(rng.integers(-magnitude, magnitude + 1)))
                else:
                    root_list.append(Rational(int(rng.integers(-magnitude, magnitude + 1)),
                                            int(rng.integers(2, 5))))
        
        root_list = root_list[:degree]
        
        # Build polynomial: (x - r1)(x - r2)...(x - rn)
        poly = 1
        for r in root_list:
            poly *= (x - r)
        poly = expand(poly)
        
        # Format polynomial
        poly_str = str(poly).replace("**", "^")
        
        # Format answer (sorted roots)
        def sort_key(r):
            r_sympy = sympy.sympify(r)
            if r_sympy.is_real:
                return (0, float(r_sympy), 0)
            else:
                return (1, float(sympy.re(r_sympy)), float(sympy.im(r_sympy)))
        
        sorted_roots = sorted(root_list, key=sort_key)
        answer_parts = []
        for r in sorted_roots:
            r_sympy = sympy.sympify(r)
            if r_sympy.is_integer:
                answer_parts.append(str(int(r_sympy)))
            else:
                answer_parts.append(str(r_sympy))
        
        answer = ", ".join(answer_parts)
        
        question = (
            f"Find all roots of the following polynomial (including multiplicity):\n\n"
            f"P(x) = {poly_str}\n\n"
            f"List all roots separated by commas. "
            f"Use 'i' for the imaginary unit if needed."
        )
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "polynomial": str(poly),
                "roots": [str(r) for r in root_list],
                "degree": degree,
            },
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade by checking if all predicted roots are correct (accounting for multiplicity)."""
        try:
            # Parse predicted roots
            pred_roots = self._parse_roots(prediction)
            ans_roots = self._parse_roots(answer)
            
            if len(pred_roots) != len(ans_roots):
                return False
            
            # Compare sets of roots
            # Convert to comparable forms
            pred_set = set(str(r) for r in pred_roots)
            ans_set = set(str(r) for r in ans_roots)
            
            return pred_set == ans_set
        except:
            return False
    
    def _parse_roots(self, text: str) -> list:
        """Parse comma-separated root string into SymPy expressions."""
        roots = []
        for part in text.split(","):
            part = part.strip()
            if part:
                try:
                    roots.append(sympy.sympify(part))
                except:
                    # Try common formats
                    part = part.replace("i", "I")
                    try:
                        roots.append(sympy.sympify(part))
                    except:
                        pass
        return roots
