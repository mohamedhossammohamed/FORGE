"""
Abstract base class for FORGE problem generators.

Every category must subclass ForgeCategory and implement:
- generate(): produce a question and canonical answer
- get_difficulty_params(): return parameter ranges for each difficulty level
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from .state import create_rng


@dataclass
class Problem:
    """A single generated problem with its canonical answer."""
    
    question: str
    answer: Any
    category: str
    difficulty: int
    iteration: int
    seed: int
    metadata: Optional[dict] = None


class ForgeCategory(ABC):
    """
    Base class for all FORGE problem categories.
    
    Subclasses must implement:
    - name: str property identifying the category
    - generate(): creates a Problem instance
    - get_difficulty_params(): returns dict of parameters for each difficulty level
    - grade(prediction, answer): evaluates a model's response against canonical answer
    """
    
    def __init__(self, seed: int):
        """
        Initialize category with a master seed.
        
        Args:
            seed: The master seed for deterministic generation
        """
        self.base_seed = seed
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this category (e.g., 'arithmetic_chain')."""
        ...
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'Arithmetic Chain Composition')."""
        ...
    
    @abstractmethod
    def generate(self, difficulty: int, iteration: int) -> Problem:
        """
        Generate a single problem at the specified difficulty.
        
        Args:
            difficulty: Difficulty level 1-5
            iteration: Question number within this difficulty level
            
        Returns:
            Problem instance with question text, canonical answer, and metadata
        """
        ...
    
    @abstractmethod
    def get_difficulty_params(self, difficulty: int) -> dict:
        """
        Return the parameter configuration for a given difficulty level.
        
        Args:
            difficulty: Difficulty level 1-5
            
        Returns:
            Dict of parameter names to values that define this difficulty
        """
        ...
    
    @abstractmethod
    def grade(self, prediction: Any, answer: Any) -> bool:
        """
        Evaluate whether a model's prediction matches the canonical answer.
        
        Args:
            prediction: The model's extracted answer
            answer: The canonical answer from generate()
            
        Returns:
            True if the prediction is correct
        """
        ...
    
    def get_rng(self, difficulty: int, iteration: int) -> np.random.Generator:
        """
        Get a deterministic RNG for this specific generation context.
        
        Args:
            difficulty: Difficulty level
            iteration: Iteration number
            
        Returns:
            Seeded numpy.random.Generator
        """
        return create_rng(self.base_seed, difficulty, iteration)
    
    def generate_batch(
        self, difficulty: int, count: int
    ) -> list[Problem]:
        """
        Generate multiple problems at the same difficulty level.
        
        Args:
            difficulty: Difficulty level 1-5
            count: Number of problems to generate
            
        Returns:
            List of Problem instances
        """
        return [
            self.generate(difficulty, iteration)
            for iteration in range(count)
        ]
