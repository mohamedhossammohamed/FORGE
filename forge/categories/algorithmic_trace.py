"""
Category 25: Algorithmic Trace Execution

Generates pseudocode and asks for execution trace results.
Difficulty scales from middle school (linear search) to frontier (quicksort).
"""

import random

from ..core.generator import ForgeCategory, Problem


class AlgorithmicTraceCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "algorithmic_trace"
    
    @property
    def display_name(self) -> str:
        return "Algorithmic Trace Execution"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"algorithm": "linear_search", "array_size": 5},
            2: {"algorithm": "binary_search", "array_size": 7},
            3: {"algorithm": "bubble_sort", "array_size": 5},
            4: {"algorithm": "merge_sort", "array_size": 8},
            5: {"algorithm": "quicksort", "array_size": 10},
        }
        return params.get(difficulty, params[3])
    
    def _generate_array(self, rng, size, max_val=100):
        """Generate a random array of integers."""
        return [int(rng.integers(1, max_val + 1)) for _ in range(size)]
    
    def _trace_linear_search(self, array, target):
        """Trace linear search and return the index."""
        for i, val in enumerate(array):
            if val == target:
                return i
        return -1
    
    def _trace_binary_search(self, sorted_array, target):
        """Trace binary search and return the index."""
        left, right = 0, len(sorted_array) - 1
        while left <= right:
            mid = (left + right) // 2
            if sorted_array[mid] == target:
                return mid
            elif sorted_array[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1
    
    def _trace_bubble_sort(self, array):
        """Trace bubble sort and return the sorted array."""
        arr = array.copy()
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr
    
    def _trace_merge_sort(self, array):
        """Trace merge sort and return the sorted array."""
        if len(array) <= 1:
            return array
        
        mid = len(array) // 2
        left = self._trace_merge_sort(array[:mid])
        right = self._trace_merge_sort(array[mid:])
        
        return self._merge(left, right)
    
    def _merge(self, left, right):
        """Merge two sorted arrays."""
        result = []
        i = j = 0
        
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        
        result.extend(left[i:])
        result.extend(right[j:])
        return result
    
    def _trace_quicksort(self, array):
        """Trace quicksort and return the sorted array."""
        if len(array) <= 1:
            return array
        
        pivot = array[0]
        less = [x for x in array[1:] if x <= pivot]
        greater = [x for x in array[1:] if x > pivot]
        
        return self._trace_quicksort(less) + [pivot] + self._trace_quicksort(greater)
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        algorithm = params["algorithm"]
        array_size = params["array_size"]
        
        array = self._generate_array(rng, array_size)
        
        if algorithm == "linear_search":
            target = array[int(rng.integers(0, len(array)))]
            answer = self._trace_linear_search(array, target)
            
            code = f"""function linear_search(arr, target):
    for i = 0 to length(arr) - 1:
        if arr[i] == target:
            return i
    return -1

arr = {array}
target = {target}
result = linear_search(arr, target)"""
            
            question = (
                f"Trace the following pseudocode execution and provide the final value "
                f"of 'result':\n\n{code}\n\nWhat is the value of 'result'?"
            )
            
        elif algorithm == "binary_search":
            sorted_array = sorted(array)
            target = sorted_array[int(rng.integers(0, len(sorted_array)))]
            answer = self._trace_binary_search(sorted_array, target)
            
            code = f"""function binary_search(arr, target):
    left = 0
    right = length(arr) - 1
    while left <= right:
        mid = (left + right) / 2  // integer division
        if arr[mid] == target:
            return mid
        else if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

arr = {sorted_array}
target = {target}
result = binary_search(arr, target)"""
            
            question = (
                f"Trace the following pseudocode execution and provide the final value "
                f"of 'result':\n\n{code}\n\nWhat is the value of 'result'?"
            )
            
        elif algorithm == "bubble_sort":
            answer = self._trace_bubble_sort(array)
            
            code = f"""function bubble_sort(arr):
    n = length(arr)
    for i = 0 to n - 1:
        for j = 0 to n - i - 2:
            if arr[j] > arr[j + 1]:
                swap(arr[j], arr[j + 1])
    return arr

arr = {array}
result = bubble_sort(arr)"""
            
            question = (
                f"Trace the following pseudocode execution and provide the final value "
                f"of 'result':\n\n{code}\n\nWhat is the final sorted array?"
            )
            
        elif algorithm == "merge_sort":
            answer = self._trace_merge_sort(array)
            
            code = f"""function merge_sort(arr):
    if length(arr) <= 1:
        return arr
    mid = length(arr) / 2  // integer division
    left = merge_sort(arr[0..mid-1])
    right = merge_sort(arr[mid..end])
    return merge(left, right)

arr = {array}
result = merge_sort(arr)"""
            
            question = (
                f"Trace the following pseudocode execution and provide the final value "
                f"of 'result':\n\n{code}\n\nWhat is the final sorted array?"
            )
            
        else:  # quicksort
            answer = self._trace_quicksort(array)
            
            code = f"""function quicksort(arr):
    if length(arr) <= 1:
        return arr
    pivot = arr[0]
    less = [x for x in arr[1:] if x <= pivot]
    greater = [x for x in arr[1:] if x > pivot]
    return quicksort(less) + [pivot] + quicksort(greater)

arr = {array}
result = quicksort(arr)"""
            
            question = (
                f"Trace the following pseudocode execution and provide the final value "
                f"of 'result':\n\n{code}\n\nWhat is the final sorted array?"
            )
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "algorithm": algorithm,
                "input_array": array,
                "answer": answer,
            },
        )
    
    def grade(self, prediction: str, answer) -> bool:
        try:
            import ast
            
            # Try to parse prediction as Python literal
            pred_clean = prediction.strip()
            
            # Handle array format
            if pred_clean.startswith('[') and pred_clean.endswith(']'):
                pred_value = ast.literal_eval(pred_clean)
            else:
                # Try as single integer
                pred_value = int(pred_clean)
            
            return pred_value == answer
        except:
            return False
