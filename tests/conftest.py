"""Shared fixtures and helper functions for the FORGE test suite."""

import json
import pytest
from pathlib import Path
from fractions import Fraction
from typing import Any

from forge.categories import CATEGORIES, get_all_categories
from forge.core.generator import Problem

REFERENCE_SEED = 42
QUICK_SEEDS = [1, 42, 12345, 999999, 2**31 - 1]
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


@pytest.fixture(params=CATEGORIES.keys(), ids=CATEGORIES.keys())
def forge_category(request):
    """Parametrized fixture yielding (name, cls, instance) for each category."""
    name = request.param
    cls = CATEGORIES[name]
    instance = cls(seed=REFERENCE_SEED)
    return name, cls, instance


@pytest.fixture
def all_category_instances():
    """Returns dict of {name: instance} for all 25 categories with seed=42."""
    return {name: cls(seed=REFERENCE_SEED) for name, cls in CATEGORIES.items()}


@pytest.fixture
def reference_seed():
    return REFERENCE_SEED


@pytest.fixture
def quick_seeds():
    return QUICK_SEEDS


@pytest.fixture(scope="session")
def snapshot_data():
    """Load the committed snapshot for version stability testing."""
    path = FIXTURES_DIR / "snapshot_seed42.json"
    if not path.exists():
        pytest.skip("Snapshot file not generated yet. Run: python tests/generate_snapshot.py")
    with open(path) as f:
        return json.load(f)


def generate_problem(
    category_name: str,
    difficulty: int = 3,
    iteration: int = 0,
    seed: int = REFERENCE_SEED,
) -> Problem:
    """Helper to generate a single problem from any category."""
    cls = CATEGORIES[category_name]
    instance = cls(seed=seed)
    return instance.generate(difficulty, iteration)


def make_prediction_from_answer(category_name: str, answer: Any) -> str:
    """Convert a Problem's canonical answer into the string format that
    the category's grade() method expects as a 'prediction'.

    Most categories: str(answer) works directly.
    Special cases:
    - chess_mate: answer is "SAN|FEN|mate_in" -> extract SAN part
    - game_nim: answer is "[heaps: x, y] winning | Heap X: remove Y" -> extract move part
    """
    if category_name == "chess_mate":
        return str(answer).split("|")[0]
    if category_name == "game_nim":
        # Extract the move part after " | " if present
        if " | " in str(answer):
            return str(answer).split(" | ", 1)[1]
        return str(answer)
    if category_name == "jordan_normal":
        # Answer format: "A = ...\nJ = ...\nP = ..." -> extract J and P parts
        lines = str(answer).split("\n")
        jp_lines = []
        capture = False
        for l in lines:
            if l.startswith("J ="):
                capture = True
            if capture:
                jp_lines.append(l)
        return "\n".join(jp_lines)
    return str(answer)


def make_wrong_answer(category_name: str, answer: Any) -> str:
    """Construct a deliberately wrong answer for a category."""
    if category_name == "formal_grammars":
        return "No" if str(answer).lower() == "yes" else "Yes"
    if category_name == "game_nim":
        if "losing" in str(answer).lower():
            return "Heap 1: remove 1"
        return "Losing position"
    if category_name == "diophantine":
        nums = str(answer).strip("()").split(",")
        return f"({int(nums[0].strip()) + 100}, {int(nums[1].strip()) + 100})"
    if category_name == "polynomial_roots":
        return "0, 0, 0, 0, 0, 0, 0"
    if category_name == "quantum_amplitudes":
        # Use a state with wrong basis - guaranteed to not match
        return "0.5|00> + 0.5|01> + 0.5|10> + 0.5|11>"
    if category_name == "chess_mate":
        # Use a clearly non-mating move: Na1 (knight to corner)
        return "Na1"
    if category_name == "algorithmic_trace":
        return "[-1]" if isinstance(answer, int) else "[]"
    if category_name == "linear_systems":
        return "x1 = 0, x2 = 0, x3 = 0, x4 = 0, x5 = 0, x6 = 0"
    if category_name == "jordan_normal":
        return "A = [[99]]\nJ = [[0]]\nP = [[1]]"
    if category_name == "signal_dft":
        return "[0.0000+0.0000j, 0.0000+0.0000j]"
    if category_name == "boolean_kmap":
        return "~A & ~B & ~C"
    if category_name == "arithmetic_chain":
        if isinstance(answer, int):
            return str(-abs(answer) - 999)
        return "999/1"
    if category_name == "geo_polygon":
        if isinstance(answer, int):
            return str(abs(answer) + 9999)
        return "9999/1"
    # Default for numeric categories
    if isinstance(answer, (int, float)):
        return str(-abs(int(answer)) - 999)
    if isinstance(answer, str) and "/" in str(answer):
        return "999/1"
    return "WRONG_ANSWER_XYZ_999"


def assert_grade_correct(category_name: str, prediction: str, answer: Any):
    """Assert that grading a prediction against the answer returns True."""
    cls = CATEGORIES[category_name]
    instance = cls(seed=REFERENCE_SEED)
    result = instance.grade(prediction, answer)
    assert result is True, (
        f"Grade should be correct for category '{category_name}'.\n"
        f"  prediction: {prediction!r}\n"
        f"  answer:     {answer!r}"
    )


def assert_grade_wrong(category_name: str, prediction: str, answer: Any):
    """Assert that grading a prediction against the answer returns False."""
    cls = CATEGORIES[category_name]
    instance = cls(seed=REFERENCE_SEED)
    result = instance.grade(prediction, answer)
    assert result is False, (
        f"Grade should reject wrong answer for category '{category_name}'.\n"
        f"  prediction: {prediction!r}\n"
        f"  answer:     {answer!r}"
    )
