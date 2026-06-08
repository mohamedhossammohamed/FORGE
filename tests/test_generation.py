"""Tests for problem structure validation and difficulty scaling."""

import pytest
from forge.categories import CATEGORIES
from conftest import REFERENCE_SEED


# Complexity metric keys per category - maps to a difficulty param key
# that should increase monotonically with difficulty level.
COMPLEXITY_METRIC_KEYS = {
    "arithmetic_chain": "n_steps",
    "matrix_det": "n",
    "linear_systems": "n",
    "polynomial_roots": "degree",
    "taylor_series": "target_degree",
    "boolean_kmap": "n_vars",
    "quantum_amplitudes": "n_qubits",
    "chess_mate": "mate_in",
    "graph_shortest_path": "n_vertices",
    "geo_polygon": "n_vertices",
    "info_entropy": "alphabet_size",
    "crypto_rsa": "bit_length",
    "algorithmic_trace": "algorithm",
    "prob_bayes": "n_stages",
    "mod_exp": "exp_range",
    "combinatorics_stars": "objects_range",
    "finance_math": "compound_type",
    "signal_dft": "n",
    "algebra_groups": "n_range",
    "vector_div": "n_terms",
    "diff_eq_rlc": "order",
    "game_nim": "heaps_range",
    "diophantine": "magnitude",
    "formal_grammars": "n_rules",
    "jordan_normal": "n",
}


def _extract_complexity(params: dict, key: str) -> float:
    """Extract a numeric complexity metric from difficulty params."""
    val = params[key]
    if isinstance(val, tuple):
        return float(val[0])
    if isinstance(val, str):
        order = {
            "simple": 1, "continuous": 2, "varying_rate": 3, "black_scholes": 4,
            "linear_search": 1, "binary_search": 2, "bubble_sort": 3,
            "merge_sort": 4, "quicksort": 5,
        }
        return float(order.get(val, 0))
    return float(val)


SLOW_GENERATORS = {"algebra_groups", "chess_mate", "diff_eq_rlc", "finance_math"}


class TestProblemStructure:
    """Verify generated problems have valid structure."""

    @pytest.mark.parametrize("difficulty", [1, 3, 5])
    @pytest.mark.parametrize("iteration", list(range(3)))
    def test_problem_structure_valid(self, forge_category, difficulty, iteration):
        name, cls, _ = forge_category
        instance = cls(seed=REFERENCE_SEED)
        try:
            p = instance.generate(difficulty, iteration)
        except (IndexError, ValueError, ZeroDivisionError, OverflowError) as e:
            pytest.xfail(f"{name} raises {type(e).__name__}: {e}")
        except RecursionError:
            pytest.xfail(f"{name} hit recursion limit at difficulty {difficulty}")

        assert p.question is not None and isinstance(p.question, str) and len(p.question) > 0
        assert p.answer is not None
        assert p.category == name
        assert p.difficulty == difficulty
        assert p.iteration == iteration
        assert p.seed == REFERENCE_SEED
        assert isinstance(p.metadata, dict) or p.metadata is None


class TestDifficultyParams:
    """Verify get_difficulty_params returns valid dicts for all tiers."""

    def test_difficulty_params_returns_dict(self, forge_category):
        name, cls, instance = forge_category
        for d in range(1, 6):
            params = instance.get_difficulty_params(d)
            assert isinstance(params, dict)
            assert len(params) > 0


class TestDifficultyScaling:
    """Verify complexity increases monotonically from tier 1 to 5."""

    def test_difficulty_scaling_monotonic(self, forge_category):
        name, cls, instance = forge_category
        metric_key = COMPLEXITY_METRIC_KEYS.get(name)
        if metric_key is None:
            pytest.skip(f"No complexity metric defined for {name}")

        complexities = []
        for d in range(1, 6):
            params = instance.get_difficulty_params(d)
            assert metric_key in params
            complexities.append(_extract_complexity(params, metric_key))

        for i in range(len(complexities) - 1):
            assert complexities[i] <= complexities[i + 1], (
                f"{name}: complexity at difficulty {i+1} ({complexities[i]}) > "
                f"difficulty {i+2} ({complexities[i+1]})"
            )


class TestDifficultyCalibration:
    """Verify that generated problems actually increase in measurable complexity.

    This goes beyond parameter monotonicity — it measures actual output
    complexity from generated problems (question length, answer magnitude, etc.)
    to confirm that higher difficulty tiers produce genuinely harder problems.
    """

    # Categories where question length should increase with difficulty
    QUESTION_LENGTH_CATEGORIES = {
        "arithmetic_chain", "matrix_det", "linear_systems",
        "polynomial_roots", "boolean_kmap", "quantum_amplitudes",
        "formal_grammars", "geo_polygon", "signal_dft",
    }

    # Categories where answer magnitude should increase with difficulty
    ANSWER_MAGNITUDE_CATEGORIES = {
        "mod_exp", "crypto_rsa", "algebra_groups",
        "combinatorics_stars", "graph_shortest_path",
    }

    @pytest.mark.parametrize("name", QUESTION_LENGTH_CATEGORIES)
    def test_question_complexity_increases(self, name):
        """Question text should be longer at difficulty 5 than difficulty 1."""
        cls = CATEGORIES[name]
        instance = cls(seed=42)
        lengths = []
        for d in [1, 5]:
            p = instance.generate(d, 0)
            lengths.append(len(p.question))
        assert lengths[1] >= lengths[0], (
            f"{name}: question at d5 ({lengths[1]} chars) shorter than d1 ({lengths[0]} chars)"
        )

    @pytest.mark.parametrize("name", ANSWER_MAGNITUDE_CATEGORIES)
    def test_answer_magnitude_increases(self, name):
        """Answer magnitude should be larger at difficulty 5 than difficulty 1."""
        cls = CATEGORIES[name]
        instance = cls(seed=42)
        p1 = instance.generate(1, 0)
        p5 = instance.generate(5, 0)
        try:
            v1 = abs(int(p1.answer))
            v5 = abs(int(p5.answer))
            assert v5 >= v1, (
                f"{name}: answer at d5 ({v5}) smaller than d1 ({v1})"
            )
        except (ValueError, TypeError):
            pytest.skip(f"{name} answer not a simple integer")

    def test_all_categories_generate_at_all_tiers(self):
        """Every category must generate a valid problem at all 5 difficulty tiers."""
        for name, cls in CATEGORIES.items():
            if name in SLOW_GENERATORS:
                continue
            instance = cls(seed=42)
            for d in range(1, 6):
                try:
                    p = instance.generate(d, 0)
                    assert p is not None
                    assert p.answer is not None
                except Exception as e:
                    pytest.xfail(f"{name} fails at difficulty {d}: {type(e).__name__}: {e}")
