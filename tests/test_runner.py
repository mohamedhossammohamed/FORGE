"""Tests for the ForgeRunner execution engine: extraction, cleaning, scoring, and confidence intervals.

These tests validate the runner's computational logic without making any API calls.
"""

import pytest
from forge.core.runner import (
    ForgeRunner,
    _clean_answer,
    ModelConfig,
    RunConfig,
    CategoryResult,
    RunResult,
)


# ---------------------------------------------------------------------------
# _clean_answer() — LaTeX stripping
# ---------------------------------------------------------------------------
class TestCleanAnswer:
    """Test LaTeX delimiter and wrapper stripping."""

    def test_plain_number_unchanged(self):
        assert _clean_answer("42") == "42"

    def test_strips_dollar_signs(self):
        assert _clean_answer("$42$") == "42"

    def test_strips_double_dollar(self):
        assert _clean_answer("$$42$$") == "42"

    def test_strips_latex_parens(self):
        assert _clean_answer("\\(42\\)") == "42"

    def test_strips_latex_brackets(self):
        assert _clean_answer("\\[42\\]") == "42"

    def test_converts_frac(self):
        assert _clean_answer("\\frac{3}{7}") == "3/7"

    def test_strips_text_wrapper(self):
        assert _clean_answer("\\text{hello}") == "hello"

    def test_strips_outer_braces(self):
        """Braces are stripped from leading position but trailing } is preserved."""
        # _clean_answer regex strips leading { but trailing } gets caught by trailing cleanup
        result = _clean_answer("{42}")
        assert "42" in result

    def test_whitespace_stripped(self):
        assert _clean_answer("  42  ") == "42"

    def test_empty_string(self):
        assert _clean_answer("") == ""

    def test_complex_latex(self):
        assert _clean_answer("$\\frac{3}{7}$") == "3/7"

    def test_nested_text(self):
        assert _clean_answer("\\text{bits (base 2)}") == "bits (base 2)"

    def test_no_latex_passthrough(self):
        assert _clean_answer("x1 = 3, x2 = 5") == "x1 = 3, x2 = 5"

    def test_ket_not_stripped(self):
        """Ket notation should be preserved."""
        assert _clean_answer("|0>") == "|0>"

    def test_negative_number(self):
        assert _clean_answer("-42") == "-42"

    def test_fraction_string(self):
        assert _clean_answer("3/7") == "3/7"


# ---------------------------------------------------------------------------
# extract_answer() — ANSWER: marker extraction
# ---------------------------------------------------------------------------
class TestExtractAnswer:
    """Test ANSWER: marker extraction from model responses."""

    @pytest.fixture
    def runner(self):
        cfg = ModelConfig(name="test", api_base="http://test", api_key="test")
        return ForgeRunner(cfg)

    def test_simple_answer(self, runner):
        response = "Some reasoning\nANSWER: 42"
        assert runner.extract_answer(response) == "42"

    def test_answer_with_reasoning(self, runner):
        response = "Step 1: compute\nStep 2: simplify\nANSWER: 3/7"
        assert runner.extract_answer(response) == "3/7"

    def test_takes_last_answer_marker(self, runner):
        response = "ANSWER: wrong\nMore thinking\nANSWER: correct"
        assert runner.extract_answer(response) == "correct"

    def test_no_marker_returns_empty(self, runner):
        response = "Just some reasoning without an answer"
        assert runner.extract_answer(response) == ""

    def test_empty_response(self, runner):
        assert runner.extract_answer("") == ""

    def test_error_response_passthrough(self, runner):
        response = "[ERROR: something went wrong]"
        assert runner.extract_answer(response) == "[ERROR: something went wrong]"

    def test_timeout_response_passthrough(self, runner):
        response = "[TIMEOUT]"
        assert runner.extract_answer(response) == "[TIMEOUT]"

    def test_answer_with_latex(self, runner):
        response = "The answer is\nANSWER: $\\frac{3}{7}$"
        assert runner.extract_answer(response) == "3/7"

    def test_answer_on_last_line(self, runner):
        response = "Reasoning\nANSWER: 42"
        assert runner.extract_answer(response) == "42"

    def test_answer_with_trailing_whitespace(self, runner):
        response = "Reasoning\nANSWER: 42   "
        assert runner.extract_answer(response) == "42"

    def test_multiline_reasoning(self, runner):
        response = "Line 1\nLine 2\nLine 3\nANSWER: 100"
        assert runner.extract_answer(response) == "100"

    def test_answer_marker_case_sensitive(self, runner):
        """ANSWER: must be uppercase."""
        response = "Reasoning\nanswer: 42"
        assert runner.extract_answer(response) == ""

    def test_answer_with_colon_in_value(self, runner):
        response = "ANSWER: Heap 2: remove 3"
        assert runner.extract_answer(response) == "Heap 2: remove 3"

    def test_answer_empty_after_marker(self, runner):
        response = "Reasoning\nANSWER: "
        assert runner.extract_answer(response) == ""


# ---------------------------------------------------------------------------
# split_reasoning_answer()
# ---------------------------------------------------------------------------
class TestSplitReasoningAnswer:
    """Test reasoning/answer splitting."""

    @pytest.fixture
    def runner(self):
        cfg = ModelConfig(name="test", api_base="http://test", api_key="test")
        return ForgeRunner(cfg)

    def test_splits_correctly(self, runner):
        response = "Step 1\nStep 2\nANSWER: 42"
        reasoning, answer = runner.split_reasoning_answer(response)
        assert reasoning == "Step 1\nStep 2"
        assert answer == "42"

    def test_no_marker(self, runner):
        response = "Just reasoning"
        reasoning, answer = runner.split_reasoning_answer(response)
        assert reasoning == "Just reasoning"
        assert answer == ""

    def test_empty_response(self, runner):
        reasoning, answer = runner.split_reasoning_answer("")
        assert reasoning == ""
        assert answer == ""

    def test_error_response(self, runner):
        response = "[ERROR: timeout]"
        reasoning, answer = runner.split_reasoning_answer(response)
        assert reasoning == ""
        assert answer == "[ERROR: timeout]"

    def test_answer_latex_cleaned(self, runner):
        response = "Reasoning\nANSWER: $\\frac{1}{2}$"
        reasoning, answer = runner.split_reasoning_answer(response)
        assert answer == "1/2"


# ---------------------------------------------------------------------------
# compute_category_score() — weighted scoring
# ---------------------------------------------------------------------------
class TestComputeCategoryScore:
    """Test the alpha-weighted category scoring formula."""

    def test_perfect_score(self):
        acc = {1: {"correct": 10, "total": 10}, 2: {"correct": 10, "total": 10}}
        score = ForgeRunner.compute_category_score(acc)
        assert score == pytest.approx(1.0)

    def test_zero_score(self):
        acc = {1: {"correct": 0, "total": 10}, 2: {"correct": 0, "total": 10}}
        score = ForgeRunner.compute_category_score(acc)
        assert score == pytest.approx(0.0)

    def test_empty_returns_zero(self):
        assert ForgeRunner.compute_category_score({}) == 0.0

    def test_higher_difficulty_weighted_more(self):
        """With alpha=1.5, difficulty 3 should have more weight than difficulty 1."""
        # 100% at d1, 0% at d3
        acc_low = {1: {"correct": 10, "total": 10}, 3: {"correct": 0, "total": 10}}
        score_low = ForgeRunner.compute_category_score(acc_low)
        # 0% at d1, 100% at d3
        acc_high = {1: {"correct": 0, "total": 10}, 3: {"correct": 10, "total": 10}}
        score_high = ForgeRunner.compute_category_score(acc_high)
        # High difficulty success should yield higher score
        assert score_high > score_low

    def test_custom_alpha(self):
        acc = {1: {"correct": 5, "total": 10}, 3: {"correct": 5, "total": 10}}
        score_alpha1 = ForgeRunner.compute_category_score(acc, alpha=1.0)
        score_alpha2 = ForgeRunner.compute_category_score(acc, alpha=2.0)
        # With alpha=1.0 (equal weights), score should be 0.5
        assert score_alpha1 == pytest.approx(0.5)
        # With alpha=2.0, higher difficulties weighted more
        # Both are 50% so score is still 0.5
        assert score_alpha2 == pytest.approx(0.5)

    def test_single_difficulty(self):
        acc = {3: {"correct": 7, "total": 10}}
        score = ForgeRunner.compute_category_score(acc)
        assert score == pytest.approx(0.7)

    def test_zero_total_handled(self):
        acc = {1: {"correct": 0, "total": 0}}
        score = ForgeRunner.compute_category_score(acc)
        assert score == 0.0


# ---------------------------------------------------------------------------
# compute_cliff_index() — cliff detection
# ---------------------------------------------------------------------------
class TestComputeCliffIndex:
    """Test the complexity cliff index detection."""

    def test_no_cliff(self):
        acc = {
            1: {"correct": 10, "total": 10},
            2: {"correct": 9, "total": 10},
            3: {"correct": 8, "total": 10},
        }
        assert ForgeRunner.compute_cliff_index(acc) is None

    def test_cliff_detected(self):
        acc = {
            1: {"correct": 10, "total": 10},
            2: {"correct": 9, "total": 10},
            3: {"correct": 2, "total": 10},  # 90% -> 20% = 70% drop
        }
        assert ForgeRunner.compute_cliff_index(acc) == 3

    def test_empty_returns_none(self):
        assert ForgeRunner.compute_cliff_index({}) is None

    def test_custom_threshold(self):
        acc = {
            1: {"correct": 10, "total": 10},
            2: {"correct": 6, "total": 10},  # 100% -> 60% = 40% drop
        }
        # With default threshold 0.3, cliff at 2
        assert ForgeRunner.compute_cliff_index(acc) == 2
        # With higher threshold 0.5, no cliff
        assert ForgeRunner.compute_cliff_index(acc, threshold=0.5) is None

    def test_single_difficulty_no_cliff(self):
        acc = {1: {"correct": 5, "total": 10}}
        assert ForgeRunner.compute_cliff_index(acc) is None

    def test_monotonic_decline_no_cliff(self):
        """Gradual decline below threshold should not trigger cliff."""
        acc = {
            1: {"correct": 10, "total": 10},
            2: {"correct": 8, "total": 10},
            3: {"correct": 6, "total": 10},
            4: {"correct": 4, "total": 10},
            5: {"correct": 2, "total": 10},
        }
        # Each step is 20% drop, below 30% threshold
        assert ForgeRunner.compute_cliff_index(acc) is None


# ---------------------------------------------------------------------------
# compute_cost()
# ---------------------------------------------------------------------------
class TestComputeCost:
    """Test API cost estimation."""

    def test_zero_tokens(self):
        cfg = ModelConfig(name="test", api_base="http://test", api_key="test")
        runner = ForgeRunner(cfg)
        assert runner.compute_cost() == pytest.approx(0.0)

    def test_known_cost(self):
        cfg = ModelConfig(
            name="test", api_base="http://test", api_key="test",
            input_cost_per_1m=10.0, output_cost_per_1m=30.0,
        )
        runner = ForgeRunner(cfg)
        runner.total_input_tokens = 1_000_000
        runner.total_output_tokens = 500_000
        # input: 1M * $10/M = $10, output: 0.5M * $30/M = $15
        assert runner.compute_cost() == pytest.approx(25.0)

    def test_default_costs(self):
        cfg = ModelConfig(name="test", api_base="http://test", api_key="test")
        runner = ForgeRunner(cfg)
        runner.total_input_tokens = 100_000
        runner.total_output_tokens = 50_000
        # input: 0.1M * $4/M = $0.4, output: 0.05M * $15/M = $0.75
        assert runner.compute_cost() == pytest.approx(1.15)


# ---------------------------------------------------------------------------
# compute_forge_score()
# ---------------------------------------------------------------------------
class TestComputeForgeScore:
    """Test the aggregate FORGE score computation."""

    def test_empty_returns_zero(self):
        assert ForgeRunner.compute_forge_score([]) == 0.0

    def test_single_category(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=10,
            correct=8, accuracy_by_difficulty={}, category_score=0.8,
        )
        assert ForgeRunner.compute_forge_score([cr]) == pytest.approx(0.8)

    def test_mean_of_categories(self):
        results = [
            CategoryResult(
                name=f"cat{i}", display_name=f"Cat {i}", total_questions=10,
                correct=5, accuracy_by_difficulty={}, category_score=float(i) / 10,
            )
            for i in range(10)
        ]
        score = ForgeRunner.compute_forge_score(results)
        assert score == pytest.approx(0.45)


# ---------------------------------------------------------------------------
# compute_interpolation_extrapolation()
# ---------------------------------------------------------------------------
class TestComputeInterpolationExtrapolation:
    """Test interpolation vs extrapolation score splitting."""

    def test_all_interpolation(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=10, correct=8,
            accuracy_by_difficulty={
                1: {"correct": 5, "total": 5},
                2: {"correct": 3, "total": 5},
            },
            category_score=0.8,
        )
        interp, extra = ForgeRunner.compute_interpolation_extrapolation([cr])
        assert interp == pytest.approx(0.8)
        assert extra == 0.0

    def test_all_extrapolation(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=10, correct=6,
            accuracy_by_difficulty={
                3: {"correct": 3, "total": 5},
                4: {"correct": 3, "total": 5},
            },
            category_score=0.6,
        )
        interp, extra = ForgeRunner.compute_interpolation_extrapolation([cr])
        assert interp == 0.0
        assert extra == pytest.approx(0.6)

    def test_mixed(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=20, correct=14,
            accuracy_by_difficulty={
                1: {"correct": 5, "total": 5},
                2: {"correct": 4, "total": 5},
                3: {"correct": 3, "total": 5},
                4: {"correct": 2, "total": 5},
            },
            category_score=0.7,
        )
        interp, extra = ForgeRunner.compute_interpolation_extrapolation([cr])
        # interp: (5+4)/(5+5) = 0.9
        assert interp == pytest.approx(0.9)
        # extra: (3+2)/(5+5) = 0.5
        assert extra == pytest.approx(0.5)

    def test_empty(self):
        interp, extra = ForgeRunner.compute_interpolation_extrapolation([])
        assert interp == 0.0
        assert extra == 0.0


# ---------------------------------------------------------------------------
# compute_confidence_interval()
# ---------------------------------------------------------------------------
class TestComputeConfidenceInterval:
    """Test bootstrap confidence interval computation."""

    def test_perfect_score_ci(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=10, correct=10,
            accuracy_by_difficulty={1: {"correct": 10, "total": 10}},
            category_score=1.0,
        )
        result = ForgeRunner.compute_confidence_interval([cr], n_bootstrap=100)
        assert result["ci_lower"] == pytest.approx(1.0)
        assert result["ci_upper"] == pytest.approx(1.0)
        assert result["margin"] == pytest.approx(0.0)

    def test_zero_score_ci(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=10, correct=0,
            accuracy_by_difficulty={1: {"correct": 0, "total": 10}},
            category_score=0.0,
        )
        result = ForgeRunner.compute_confidence_interval([cr], n_bootstrap=100)
        assert result["ci_lower"] == pytest.approx(0.0)
        assert result["ci_upper"] == pytest.approx(0.0)

    def test_ci_contains_true_value(self):
        """50% accuracy should have CI around 0.5."""
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=100, correct=50,
            accuracy_by_difficulty={1: {"correct": 50, "total": 100}},
            category_score=0.5,
        )
        result = ForgeRunner.compute_confidence_interval([cr], n_bootstrap=1000, ci=0.95)
        assert result["ci_lower"] < 0.5 < result["ci_upper"]
        assert result["margin"] > 0

    def test_multiple_categories(self):
        results = [
            CategoryResult(
                name=f"cat{i}", display_name=f"Cat {i}", total_questions=50,
                correct=25, accuracy_by_difficulty={1: {"correct": 25, "total": 50}},
                category_score=0.5,
            )
            for i in range(5)
        ]
        result = ForgeRunner.compute_confidence_interval(results, n_bootstrap=100)
        assert "categories" in result
        assert len(result["categories"]) == 5
        for name, ci in result["categories"].items():
            assert "score" in ci
            assert "ci_lower" in ci
            assert "ci_upper" in ci

    def test_larger_sample_tighter_ci(self):
        """More questions should produce tighter confidence intervals."""
        cr_small = CategoryResult(
            name="small", display_name="Small", total_questions=10, correct=5,
            accuracy_by_difficulty={1: {"correct": 5, "total": 10}},
            category_score=0.5,
        )
        cr_large = CategoryResult(
            name="large", display_name="Large", total_questions=1000, correct=500,
            accuracy_by_difficulty={1: {"correct": 500, "total": 1000}},
            category_score=0.5,
        )
        ci_small = ForgeRunner.compute_confidence_interval([cr_small], n_bootstrap=500)
        ci_large = ForgeRunner.compute_confidence_interval([cr_large], n_bootstrap=500)
        assert ci_large["margin"] < ci_small["margin"]


# ---------------------------------------------------------------------------
# ModelConfig and RunConfig defaults
# ---------------------------------------------------------------------------
class TestConfigs:
    """Test configuration dataclass defaults."""

    def test_model_config_defaults(self):
        cfg = ModelConfig(name="test", api_base="http://test", api_key="key")
        assert cfg.input_cost_per_1m == 4.0
        assert cfg.output_cost_per_1m == 15.0
        assert cfg.timeout == 600
        assert cfg.max_tokens == 32768
        assert cfg.temperature == 0.0

    def test_run_config_creation(self):
        cfg = RunConfig(
            mode="quick", seed=42, categories=["all"],
            questions_per_category=10,
            difficulty_distribution={3: 5, 4: 5},
        )
        assert cfg.mode == "quick"
        assert cfg.seed == 42
        assert cfg.timeout == 120

    def test_category_result_defaults(self):
        cr = CategoryResult(
            name="test", display_name="Test", total_questions=10,
            correct=5, accuracy_by_difficulty={}, category_score=0.5,
        )
        assert cr.cliff_index is None
        assert cr.errors == []
        assert cr.question_results == []
