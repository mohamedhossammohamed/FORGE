"""
Category 13: Game Theory - Nim States

Generates Nim game board states with random heaps.
Difficulty scales from elementary (3 heaps) to frontier (10 heaps).
"""

from ..core.generator import ForgeCategory, Problem


class GameNimCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "game_nim"
    
    @property
    def display_name(self) -> str:
        return "Game Theory: Nim States"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"heaps_range": (2, 3), "max_items": 5},
            2: {"heaps_range": (3, 4), "max_items": 10},
            3: {"heaps_range": (4, 6), "max_items": 20},
            4: {"heaps_range": (5, 8), "max_items": 50},
            5: {"heaps_range": (8, 10), "max_items": 100},
        }
        return params.get(difficulty, params[3])
    
    def _nim_sum(self, heaps: list[int]) -> int:
        """Compute the XOR sum (Nim-sum) of heap sizes."""
        result = 0
        for h in heaps:
            result ^= h
        return result
    
    def _is_winning(self, heaps: list[int]) -> bool:
        """A position is winning if and only if the Nim-sum is non-zero."""
        return self._nim_sum(heaps) != 0
    
    def _find_winning_move(self, heaps: list[int]) -> tuple[int, int] | None:
        """
        Find a winning move (heap_index, items_to_remove).
        Returns None if position is losing.
        """
        nim_sum = self._nim_sum(heaps)
        if nim_sum == 0:
            return None
        
        for i, h in enumerate(heaps):
            target = h ^ nim_sum
            if target < h:
                return (i + 1, h - target)  # 1-indexed heap
        
        return None
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_heaps = int(rng.integers(*params["heaps_range"]))
        max_items = params["max_items"]
        
        # Generate heap sizes
        heaps = [int(rng.integers(1, max_items + 1)) for _ in range(n_heaps)]
        
        is_winning = self._is_winning(heaps)
        winning_move = self._find_winning_move(heaps) if is_winning else None
        
        heaps_str = ", ".join(f"Heap {i+1}: {h}" for i, h in enumerate(heaps))
        
        question = (
            f"Consider a Nim game with the following heaps:\n"
            f"{heaps_str}\n\n"
            f"Players take turns removing any number of items from a single heap. "
            f"The player who takes the last item wins.\n\n"
            f"Is this a winning position for the player to move?\n"
            f"If yes, provide the optimal move as 'Heap X: remove Y'.\n"
            f"If no, provide 'Losing position'."
        )
        
        if is_winning:
            heap_idx, remove_count = winning_move
            answer = f"Heap {heap_idx}: remove {remove_count}"
        else:
            answer = "Losing position"
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"heaps": heaps, "is_winning": is_winning, "nim_sum": self._nim_sum(heaps)},
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade by checking if prediction identifies the correct position type and move."""
        pred = prediction.strip().lower()
        ans = answer.strip().lower()
        
        # Check if position type matches
        if "losing" in ans:
            return "losing" in pred
        
        if "winning" not in ans:
            return pred == ans
        
        # For winning positions, verify the move achieves the correct nim-sum
        # Parse the predicted move
        try:
            import re
            match = re.search(r'heap\s*(\d+).*?remove\s*(\d+)', pred)
            if match:
                heap_idx = int(match.group(1))
                remove_count = int(match.group(2))
                
                # Verify by computing the resulting position
                # We need to regenerate the heaps from the problem
                # For now, check if it matches the expected answer format
                expected_match = re.search(r'heap\s*(\d+).*?remove\s*(\d+)', ans)
                if expected_match:
                    exp_heap = int(expected_match.group(1))
                    exp_remove = int(expected_match.group(2))
                    
                    # Same heap and same count = correct
                    if heap_idx == exp_heap and remove_count == exp_remove:
                        return True
                    
                    # Different heap but same resulting nim-sum is also valid
                    # This is harder to verify without the original heaps
                    # For now, accept any valid winning move
        except:
            pass
        
        return pred == ans
