"""
Category 16: Modular Exponentiation

Generates expressions of the form a^b mod c.
Difficulty scales from middle school (small numbers) to frontier (exponents > 10^6).
"""

from ..core.generator import ForgeCategory, Problem


class ModExpCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "mod_exp"
    
    @property
    def display_name(self) -> str:
        return "Modular Exponentiation"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"base_range": (2, 10), "exp_range": (2, 5), "mod_range": (3, 20)},
            2: {"base_range": (2, 50), "exp_range": (3, 10), "mod_range": (10, 100)},
            3: {"base_range": (2, 100), "exp_range": (5, 100), "mod_range": (50, 500)},
            4: {"base_range": (2, 500), "exp_range": (100, 10000), "mod_range": (100, 10000)},
            5: {"base_range": (2, 1000), "exp_range": (1000000, 100000000), "mod_range": (1000, 100000)},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        base = int(rng.integers(*params["base_range"]))
        exponent = int(rng.integers(*params["exp_range"]))
        modulus = int(rng.integers(*params["mod_range"]))
        
        # Ensure modulus > 1
        modulus = max(2, modulus)
        
        # Compute answer
        answer = pow(base, exponent, modulus)
        
        question = (
            f"Compute {base}^{exponent} mod {modulus}\n\n"
            f"Provide the exact integer result."
        )
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"base": base, "exponent": exponent, "modulus": modulus},
        )
    
    def grade(self, prediction: str, answer: int) -> bool:
        try:
            pred = prediction.strip().replace(',', '').replace(' ', '')
            return int(pred) == int(answer)
        except (ValueError, TypeError):
            return False
