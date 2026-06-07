"""
Category 10: Combinatorics - Stars and Bars

Generates problems mapping to indistinguishable objects in distinguishable bins.
Difficulty scales from high school (unconstrained) to frontier (complex constraints).
"""

import math
from ..core.generator import ForgeCategory, Problem


class CombinatoricsStarsCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "combinatorics_stars"
    
    @property
    def display_name(self) -> str:
        return "Combinatorics: Stars and Bars"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"objects_range": (2, 10), "bins_range": (2, 3), "min_capacity": 0, "max_capacity": None},
            2: {"objects_range": (5, 20), "bins_range": (2, 4), "min_capacity": 0, "max_capacity": None},
            3: {"objects_range": (10, 30), "bins_range": (3, 5), "min_capacity": 1, "max_capacity": None},
            4: {"objects_range": (20, 50), "bins_range": (3, 6), "min_capacity": 0, "max_capacity": 10},
            5: {"objects_range": (30, 100), "bins_range": (4, 8), "min_capacity": 2, "max_capacity": 15},
        }
        return params.get(difficulty, params[3])
    
    def _stars_and_bars(self, n_objects: int, n_bins: int) -> int:
        """Unconstrained: C(n + k - 1, k - 1)"""
        return math.comb(n_objects + n_bins - 1, n_bins - 1)
    
    def _constrained_distribution(self, n_objects: int, bins: list[tuple[int, int]]) -> int:
        """
        Count distributions with min/max capacity constraints per bin.
        Uses inclusion-exclusion principle.
        """
        n_bins = len(bins)
        
        # First handle minimum constraints via substitution
        total_min = sum(b[0] for b in bins)
        if total_min > n_objects:
            return 0
        
        remaining = n_objects - total_min
        max_caps = [b[1] - b[0] if b[1] is not None else None for b in bins]
        
        # If no max constraints, use stars and bars
        if all(cap is None for cap in max_caps):
            return math.comb(remaining + n_bins - 1, n_bins - 1)
        
        # Inclusion-exclusion for max constraints
        result = 0
        for mask in range(1 << n_bins):
            sign = (-1) ** bin(mask).count('1')
            adjusted = remaining
            valid = True
            
            for i in range(n_bins):
                if mask & (1 << i):
                    if max_caps[i] is not None:
                        adjusted -= (max_caps[i] + 1)
                    else:
                        valid = False
                        break
            
            if valid and adjusted >= 0:
                result += sign * math.comb(adjusted + n_bins - 1, n_bins - 1)
        
        return max(0, result)
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_objects = int(rng.integers(*params["objects_range"]))
        n_bins = int(rng.integers(*params["bins_range"]))
        
        # Generate constraints
        if params["max_capacity"] is not None and difficulty >= 4:
            bins = []
            for _ in range(n_bins):
                min_cap = params["min_capacity"]
                max_cap = int(rng.integers(min_cap + 2, params["max_capacity"]))
                bins.append((min_cap, max_cap))
            answer = self._constrained_distribution(n_objects, bins)
            
            constraints_str = ", ".join(
                f"Bin {i+1}: [{b[0]}, {b[1]}]" for i, b in enumerate(bins)
            )
            question = (
                f"Distribute {n_objects} indistinguishable objects into {n_bins} "
                f"distinguishable bins with capacity constraints.\n\n"
                f"Constraints: {constraints_str}\n\n"
                f"How many distinct distributions are possible? "
                f"Provide the exact integer count."
            )
        else:
            # Simple stars and bars with minimum capacity
            min_cap = params["min_capacity"]
            if min_cap > 0:
                adjusted_objects = n_objects - min_cap * n_bins
                if adjusted_objects < 0:
                    adjusted_objects = n_objects
                    min_cap = 0
                answer = math.comb(adjusted_objects + n_bins - 1, n_bins - 1)
                question = (
                    f"Distribute {n_objects} indistinguishable objects into {n_bins} "
                    f"distinguishable bins, where each bin must contain at least "
                    f"{min_cap} object{'s' if min_cap > 1 else ''}.\n\n"
                    f"How many distinct distributions are possible? "
                    f"Provide the exact integer count."
                )
            else:
                answer = self._stars_and_bars(n_objects, n_bins)
                question = (
                    f"Distribute {n_objects} indistinguishable objects into {n_bins} "
                    f"distinguishable bins.\n\n"
                    f"How many distinct distributions are possible? "
                    f"Provide the exact integer count."
                )
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"n_objects": n_objects, "n_bins": n_bins},
        )
    
    def grade(self, prediction: str, answer: int) -> bool:
        try:
            pred = prediction.strip().replace(',', '').replace(' ', '')
            return int(pred) == int(answer)
        except (ValueError, TypeError):
            return False
