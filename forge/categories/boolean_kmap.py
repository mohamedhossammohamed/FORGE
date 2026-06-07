"""
Category 6: Boolean Logic Minimization

Generates truth tables and asks for minimized Boolean expressions.
Difficulty scales from undergraduate (3 variables) to frontier (6 variables).
"""

import sympy
from sympy import symbols, simplify_logic, SOPform, POSform
from sympy.logic.boolalg import truth_table

from ..core.generator import ForgeCategory, Problem


class BooleanKmapCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "boolean_kmap"
    
    @property
    def display_name(self) -> str:
        return "Boolean Logic Minimization"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n_vars": 3, "n_minterms": 3, "include_dont_care": False},
            2: {"n_vars": 3, "n_minterms": 4, "include_dont_care": True},
            3: {"n_vars": 4, "n_minterms": 5, "include_dont_care": True},
            4: {"n_vars": 5, "n_minterms": 8, "include_dont_care": True},
            5: {"n_vars": 6, "n_minterms": 12, "include_dont_care": True},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_vars = params["n_vars"]
        n_minterms = params["n_minterms"]
        include_dc = params["include_dont_care"]
        
        # Create symbolic variables
        var_names = [chr(65 + i) for i in range(n_vars)]
        syms = symbols(' '.join(var_names))
        if n_vars == 1:
            syms = (syms,)
        
        # Generate minterms
        all_terms = list(range(2 ** n_vars))
        minterms = []
        while len(minterms) < n_minterms and all_terms:
            idx = int(rng.integers(0, len(all_terms)))
            minterms.append(all_terms.pop(idx))
        
        # Generate don't cares
        dont_cares = []
        if include_dc and all_terms:
            n_dc = min(int(rng.integers(1, 4)), len(all_terms))
            for _ in range(n_dc):
                if all_terms:
                    idx = int(rng.integers(0, len(all_terms)))
                    dont_cares.append(all_terms.pop(idx))
        
        # Compute minimized SOP
        minimized = SOPform(syms, minterms, dont_cares)
        
        # Format truth table
        truth_table_str = "Truth table:\n"
        truth_table_str += "  " + "  ".join(var_names) + " | F\n"
        truth_table_str += "  " + "-" * (4 * n_vars + 3) + "\n"
        
        for i in range(2 ** n_vars):
            binary = format(i, f'0{n_vars}b')
            bits = "  ".join(binary)
            output = "1" if i in minterms else ("X" if i in dont_cares else "0")
            truth_table_str += f"  {bits} | {output}\n"
        
        minterms_str = ", ".join(str(m) for m in sorted(minterms))
        dc_str = f"\nDon't care conditions: {', '.join(str(d) for d in sorted(dont_cares))}" if dont_cares else ""
        
        question = (
            f"Minimize the following Boolean function using Sum of Products (SOP) form.\n\n"
            f"Variables: {', '.join(var_names)}\n"
            f"Minterms: {minterms_str}{dc_str}\n\n"
            f"{truth_table_str}\n"
            f"Provide the minimized Boolean expression in SOP form."
        )
        
        answer = str(minimized)
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "n_vars": n_vars,
                "minterms": minterms,
                "dont_cares": dont_cares,
                "minimized": str(minimized),
            },
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade by checking logical equivalence of Boolean expressions."""
        try:
            n_vars = answer.count('A') + answer.count('B') + answer.count('C') + \
                     answer.count('D') + answer.count('E') + answer.count('F')
            # Rough estimate, but works for our purposes
            
            # Parse prediction
            pred_expr = sympy.sympify(prediction.strip())
            ans_expr = sympy.sympify(answer)
            
            # Check equivalence via truth table
            return sympy.simplify_logic(pred_expr) == sympy.simplify_logic(ans_expr)
        except:
            return False
