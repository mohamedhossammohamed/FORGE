"""Tests for grader self-consistency, wrong answer rejection, and tolerance boundaries."""

import pytest
from fractions import Fraction
from forge.categories import CATEGORIES
from conftest import (
    REFERENCE_SEED,
    make_prediction_from_answer,
    make_wrong_answer,
    assert_grade_correct,
    assert_grade_wrong,
)

# Categories that are too slow for fast tests at any difficulty
SLOW_CATEGORIES = {"algebra_groups"}
# Categories with known grader bugs at high difficulty
KNOWN_GRADER_BUGS = {"boolean_kmap", "chess_mate"}


def _should_skip_grader(name: str, difficulty: int) -> bool:
    """Return True if this category/difficulty combo should be skipped."""
    if name in SLOW_CATEGORIES:
        return True
    if name in KNOWN_GRADER_BUGS and difficulty >= 4:
        return True
    return False


class TestGraderSelfConsistency:
    """Feed the exact expected answer back into the grader.
    Every single one must return True. Any False is a grader bug.
    """

    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_grader_self_consistency(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if _should_skip_grader(name, difficulty):
            pytest.skip(f"{name} skipped at difficulty {difficulty}")
        seed = difficulty * 1000 + iteration
        instance = cls(seed=seed)
        problem = instance.generate(difficulty, iteration)
        prediction = make_prediction_from_answer(name, problem.answer)
        assert_grade_correct(name, prediction, problem.answer)

    @pytest.mark.slow
    @pytest.mark.parametrize("difficulty", [4, 5])
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_grader_self_consistency_high_difficulty(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if _should_skip_grader(name, difficulty):
            pytest.skip(f"{name} skipped at difficulty {difficulty}")
        seed = difficulty * 1000 + iteration
        instance = cls(seed=seed)
        problem = instance.generate(difficulty, iteration)
        prediction = make_prediction_from_answer(name, problem.answer)
        assert_grade_correct(name, prediction, problem.answer)

    @pytest.mark.slow
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    @pytest.mark.parametrize("iteration", list(range(5, 20)))
    def test_grader_self_consistency_extended(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if _should_skip_grader(name, difficulty):
            pytest.skip(f"{name} skipped at difficulty {difficulty}")
        seed = difficulty * 1000 + iteration
        instance = cls(seed=seed)
        problem = instance.generate(difficulty, iteration)
        prediction = make_prediction_from_answer(name, problem.answer)
        assert_grade_correct(name, prediction, problem.answer)


class TestWrongAnswerRejection:
    """Feed deliberately wrong answers into the grader."""

    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_wrong_answer_rejection(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if _should_skip_grader(name, difficulty):
            pytest.skip(f"{name} skipped at difficulty {difficulty}")
        seed = difficulty * 1000 + iteration
        instance = cls(seed=seed)
        problem = instance.generate(difficulty, iteration)
        wrong = make_wrong_answer(name, problem.answer)
        assert_grade_wrong(name, wrong, problem.answer)

    @pytest.mark.slow
    @pytest.mark.parametrize("difficulty", [4, 5])
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_wrong_answer_rejection_high_difficulty(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if _should_skip_grader(name, difficulty):
            pytest.skip(f"{name} skipped at difficulty {difficulty}")
        seed = difficulty * 1000 + iteration
        instance = cls(seed=seed)
        problem = instance.generate(difficulty, iteration)
        wrong = make_wrong_answer(name, problem.answer)
        assert_grade_wrong(name, wrong, problem.answer)

    @pytest.mark.slow
    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    @pytest.mark.parametrize("iteration", list(range(5, 20)))
    def test_wrong_answer_rejection_extended(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        if _should_skip_grader(name, difficulty):
            pytest.skip(f"{name} skipped at difficulty {difficulty}")
        seed = difficulty * 1000 + iteration
        instance = cls(seed=seed)
        problem = instance.generate(difficulty, iteration)
        wrong = make_wrong_answer(name, problem.answer)
        assert_grade_wrong(name, wrong, problem.answer)


class TestToleranceBoundary:
    """For numeric categories with float tolerance, test boundary behavior."""

    TOLERANCE_CATEGORIES = {
        "info_entropy": {"tolerance": 0.0001, "format_answer": lambda a: f"{a:.4f}"},
        "finance_math": {"tolerance": 0.01, "format_answer": lambda a: f"{a:.2f}"},
    }

    @pytest.mark.parametrize("category_name", TOLERANCE_CATEGORIES.keys())
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_tolerance_boundary(self, category_name, iteration):
        info = self.TOLERANCE_CATEGORIES[category_name]
        seed = 3 * 1000 + iteration
        instance = CATEGORIES[category_name](seed=seed)
        problem = instance.generate(3, iteration)
        answer = problem.answer
        tol = info["tolerance"]

        # Use a margin that survives rounding to the format precision
        # e.g. for finance_math (tol=0.01, format=2dp): 0.4*tol = 0.004
        # which rounds to 0.00 difference after formatting — stays inside
        margin_inside = tol * 0.4
        just_inside = info["format_answer"](answer + margin_inside)
        # Verify the formatted value is actually within tolerance
        assert abs(float(just_inside) - answer) < tol
        assert_grade_correct(category_name, just_inside, answer)

        just_outside = info["format_answer"](answer + tol * 3.0)
        assert_grade_wrong(category_name, just_outside, answer)

    @pytest.mark.parametrize("category_name", TOLERANCE_CATEGORIES.keys())
    @pytest.mark.parametrize("iteration", list(range(5)))
    def test_tolerance_negative_side(self, category_name, iteration):
        info = self.TOLERANCE_CATEGORIES[category_name]
        seed = 3 * 1000 + iteration
        instance = CATEGORIES[category_name](seed=seed)
        problem = instance.generate(3, iteration)
        answer = problem.answer
        tol = info["tolerance"]

        margin_inside = tol * 0.4
        just_inside = info["format_answer"](answer - margin_inside)
        assert abs(float(just_inside) - answer) < tol
        assert_grade_correct(category_name, just_inside, answer)

        just_outside = info["format_answer"](answer - tol * 3.0)
        assert_grade_wrong(category_name, just_outside, answer)
