"""
Category 11: Information Theory - Entropy

Generates discrete probability distributions and computes Shannon entropy.
Difficulty scales from undergraduate (3 symbols) to frontier (20 symbols).
"""

import math
from fractions import Fraction

from ..core.generator import ForgeCategory, Problem


class InfoEntropyCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "info_entropy"
    
    @property
    def display_name(self) -> str:
        return "Information Theory: Entropy"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"alphabet_size": (2, 3), "base": 2, "skewness": "uniform"},
            2: {"alphabet_size": (3, 5), "base": 2, "skewness": "moderate"},
            3: {"alphabet_size": (5, 10), "base": 2, "skewness": "any"},
            4: {"alphabet_size": (10, 15), "base": "e", "skewness": "highly_skewed"},
            5: {"alphabet_size": (15, 20), "base": "e", "skewness": "highly_skewed"},
        }
        return params.get(difficulty, params[3])
    
    def _generate_distribution(self, n: int, skewness: str, rng) -> list[Fraction]:
        """Generate a probability distribution with specified skewness."""
        if skewness == "uniform":
            return [Fraction(1, n)] * n
        
        # Generate random weights
        weights = [Fraction(int(rng.integers(1, 100))) for _ in range(n)]
        total = sum(weights)
        return [w / total for w in weights]
    
    def _compute_entropy(self, distribution: list[Fraction], base: int | str = 2) -> float:
        """Compute Shannon entropy: H(X) = -sum(p * log(p))"""
        entropy = 0.0
        for p in distribution:
            if p > 0:
                p_float = float(p)
                if base == 2:
                    entropy -= p_float * math.log2(p_float)
                else:  # base = e
                    entropy -= p_float * math.log(p_float)
        return entropy
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        alphabet_size = int(rng.integers(*params["alphabet_size"]))
        base = params["base"]
        skewness = params["skewness"]
        
        distribution = self._generate_distribution(alphabet_size, skewness, rng)
        entropy = self._compute_entropy(distribution, base)
        
        # Format distribution
        symbols = [chr(65 + i) if i < 26 else f"X{i}" for i in range(alphabet_size)]
        dist_str = "\n".join(
            f"  P({sym}) = {p}" for sym, p in zip(symbols, distribution)
        )
        
        base_str = "bits (base 2)" if base == 2 else "nats (base e)"
        
        question = (
            f"Compute the Shannon entropy of the following discrete distribution "
            f"in {base_str}:\n\n"
            f"{dist_str}\n\n"
            f"Provide your answer rounded to 4 decimal places."
        )
        
        answer = round(entropy, 4)
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "distribution": [str(p) for p in distribution],
                "base": base,
                "exact_entropy": entropy,
            },
        )
    
    def grade(self, prediction: str, answer: float) -> bool:
        try:
            pred = prediction.strip()
            # Remove common prefixes
            for prefix in ["H =", "H=", "H(X) =", "H(X)="]:
                if pred.startswith(prefix):
                    pred = pred[len(prefix):].strip()
            
            pred_float = float(pred)
            return abs(pred_float - answer) < 0.0001
        except (ValueError, TypeError):
            return False
