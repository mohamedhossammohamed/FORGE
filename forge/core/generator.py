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


# ---------------------------------------------------------------------------
# Adversarially hardened, category-aware system prompts
# ---------------------------------------------------------------------------

_BASE_INSTRUCTIONS = (
    "You are a precise mathematical reasoning engine. "
    "You are being evaluated on accuracy, not verbosity.\n\n"
    "RULES:\n"
    "1. Solve the problem step by step. Show your reasoning.\n"
    "2. When you are done, output EXACTLY one line in the format:\n"
    "   ANSWER: <your answer>\n"
    "3. The ANSWER line must be the LAST line of your response.\n"
    "4. Do NOT output more than one ANSWER line.\n"
    "5. Do NOT include any text after the ANSWER line.\n"
    "6. Do NOT use LaTeX, dollar signs, \\frac, braces, or any formatting "
    "in the ANSWER line — plain text only.\n"
    "7. Do NOT say 'I think', 'approximately', 'maybe', or hedge. "
    "Give a single definitive answer.\n"
    "8. Do NOT repeat the question or restate the problem in your answer.\n"
)

_CATEGORY_ANSWER_FORMATS: dict[str, str] = {
    "arithmetic_chain": (
        "Answer format: an integer (e.g. 42) or an exact fraction like 3/7. "
        "Do NOT use decimals unless the problem specifies rounding."
    ),
    "polynomial_roots": (
        "Answer format: comma-separated list of roots. "
        "Use 'i' for the imaginary unit. Example: 2, -1/2, 3+2i, 3-2i"
    ),
    "matrix_det": ("Answer format: a single integer (the determinant)."),
    "jordan_normal": (
        "Answer format: two matrices labeled exactly as:\n"
        "J = [[row1], [row2], ...]\nP = [[row1], [row2], ...]"
    ),
    "diff_eq_rlc": (
        "Answer format: a symbolic expression for y(t) using ^ for exponentiation. "
        "Example: 5*exp(-t/3) + 2*sin(4*t)"
    ),
    "boolean_kmap": (
        "Answer format: a Boolean expression in SOP form using & for AND, "
        "| for OR, ~ for NOT. Example: A & B | ~C & D"
    ),
    "chess_mate": (
        "Answer format: a single move in standard algebraic notation (SAN). Example: Qf7#, Nf3, Rh8"
    ),
    "graph_shortest_path": (
        "Answer format: a single integer (the total weight of the shortest path)."
    ),
    "crypto_rsa": ("Answer format: a single integer (the private key d)."),
    "combinatorics_stars": ("Answer format: a single integer (the count of distributions)."),
    "info_entropy": (
        "Answer format: a decimal number rounded to exactly 4 decimal places. Example: 2.3219"
    ),
    "signal_dft": (
        "Answer format: a bracketed list of complex numbers rounded to 4 decimals. "
        "Example: [12.0000+0.0000j, -4.0000+8.0000j]"
    ),
    "game_nim": (
        "Answer format: either 'Losing position' (exact text) or "
        "'Heap X: remove Y' where X is the heap number and Y is the count. "
        "Example: Heap 2: remove 3"
    ),
    "algebra_groups": ("Answer format: a single integer (the multiplicative order)."),
    "linear_systems": ("Answer format: comma-separated assignments like x1 = 2, x2 = -1/3, x3 = 5"),
    "mod_exp": ("Answer format: a single integer (the result of a^b mod c)."),
    "vector_div": ("Answer format: a simplified symbolic expression. Example: 2*x + cos(y) + 3"),
    "geo_polygon": ("Answer format: an integer or exact fraction like 45/2."),
    "finance_math": (
        "Answer format: a decimal number rounded to exactly 2 decimal places. Example: 1234.56"
    ),
    "prob_bayes": ("Answer format: an exact fraction like 123/4567."),
    "taylor_series": ("Answer format: an exact symbolic fraction like -1/6 or 1/24."),
    "diophantine": ("Answer format: a tuple of two integers like (3, 7)."),
    "formal_grammars": ("Answer format: exactly 'Yes' or 'No' (capitalized, no period)."),
    "quantum_amplitudes": ("Answer format: ket notation like (1/sqrt(2))|00> + (1/sqrt(2))|11>."),
    "algorithmic_trace": (
        "Answer format: either a single integer (for search) or a Python list "
        "like [3, 5, 7, 12] (for sorting)."
    ),
}


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

    def system_prompt(self) -> str:
        """
        Return the category-specific system prompt.

        Uses the centralized registry to build a hardened prompt with
        category-specific answer format instructions.
        """
        fmt = _CATEGORY_ANSWER_FORMATS.get(self.name, "")
        format_block = f"\nANSWER FORMAT:\n{fmt}\n" if fmt else ""
        return _BASE_INSTRUCTIONS + format_block

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

    def generate_batch(self, difficulty: int, count: int) -> list[Problem]:
        """
        Generate multiple problems at the same difficulty level.

        Args:
            difficulty: Difficulty level 1-5
            count: Number of problems to generate

        Returns:
            List of Problem instances
        """
        return [self.generate(difficulty, iteration) for iteration in range(count)]
