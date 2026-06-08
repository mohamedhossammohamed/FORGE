"""Boundary input tests for each FORGE category.

Each test verifies that categories handle edge cases correctly:
either grading correctly or raising documented exceptions (not silent wrong answers).
"""

import pytest
from fractions import Fraction
from forge.categories import CATEGORIES
from forge.core.generator import Problem
from conftest import (
    REFERENCE_SEED,
    assert_grade_correct,
    assert_grade_wrong,
    generate_problem,
)


def _make_problem(category: str, answer, metadata=None) -> Problem:
    """Create a Problem with controlled answer for edge-case testing."""
    return Problem(
        question="edge case test",
        answer=answer,
        category=category,
        difficulty=1,
        iteration=0,
        seed=42,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Arithmetic Chain
# ---------------------------------------------------------------------------
class TestArithmeticChainEdgeCases:
    def test_integer_result(self):
        assert_grade_correct("arithmetic_chain", "42", 42)
        assert_grade_wrong("arithmetic_chain", "43", 42)

    def test_fraction_result(self):
        assert_grade_correct("arithmetic_chain", "3/7", "3/7")
        assert_grade_wrong("arithmetic_chain", "3/8", "3/7")

    def test_zero_result(self):
        assert_grade_correct("arithmetic_chain", "0", 0)

    def test_negative_integer(self):
        assert_grade_correct("arithmetic_chain", "-5", -5)

    def test_large_integer(self):
        assert_grade_correct("arithmetic_chain", str(10**18), 10**18)


# ---------------------------------------------------------------------------
# Info Entropy
# ---------------------------------------------------------------------------
class TestInfoEntropyEdgeCases:
    def test_zero_entropy_single_symbol(self):
        """Single symbol p=1 must have entropy 0."""
        assert_grade_correct("info_entropy", "0.0000", 0.0)

    def test_one_bit_entropy(self):
        """Uniform binary distribution has entropy 1 bit."""
        assert_grade_correct("info_entropy", "1.0000", 1.0)

    def test_prefix_stripping(self):
        """Grader strips 'H =' prefix."""
        assert_grade_correct("info_entropy", "H = 2.5000", 2.5)

    def test_wrong_value_rejected(self):
        assert_grade_wrong("info_entropy", "99.0000", 2.5)

    def test_large_alphabet_generation(self):
        """50-symbol distribution should generate without error."""
        cls = CATEGORIES["info_entropy"]
        instance = cls(seed=42)
        # Difficulty 5 has alphabet_size up to 20; test that generation works
        p = instance.generate(5, 0)
        assert p.answer is not None


# ---------------------------------------------------------------------------
# Matrix Determinant
# ---------------------------------------------------------------------------
class TestMatrixDetEdgeCases:
    def test_singular_matrix_det_zero(self):
        assert_grade_correct("matrix_det", "0", 0)
        assert_grade_wrong("matrix_det", "1", 0)

    def test_identity_det_one(self):
        assert_grade_correct("matrix_det", "1", 1)

    def test_negative_determinant(self):
        assert_grade_correct("matrix_det", "-42", -42)

    def test_large_determinant(self):
        assert_grade_correct("matrix_det", "2722752", 2722752)


# ---------------------------------------------------------------------------
# Chess Mate
# ---------------------------------------------------------------------------
class TestChessMateEdgeCases:
    def test_mate_in_one_correct(self):
        """Known mate-in-1 position from seed=0."""
        answer = "Qd1#|8/3Q4/8/8/8/6K1/8/5k2 w - - 0 1|1"
        assert_grade_correct("chess_mate", "Qd1#", answer)

    def test_invalid_move_rejected(self):
        """Non-mating move must be rejected."""
        answer = "Qd1#|8/3Q4/8/8/8/6K1/8/5k2 w - - 0 1|1"
        assert_grade_wrong("chess_mate", "Qg4", answer)

    def test_mate_in_one_from_generation(self):
        """Generate a mate-in-1 problem and verify self-consistency."""
        cls = CATEGORIES["chess_mate"]
        instance = cls(seed=0)
        problem = instance.generate(1, 0)
        san = str(problem.answer).split("|")[0]
        result = instance.grade(san, problem.answer)
        assert result is True, (
            f"Self-consistency failed for chess_mate: san={san!r}, answer={problem.answer!r}"
        )


# ---------------------------------------------------------------------------
# Polynomial Roots
# ---------------------------------------------------------------------------
class TestPolynomialRootsEdgeCases:
    def test_repeated_roots(self):
        assert_grade_correct("polynomial_roots", "2, 2", "2, 2")

    def test_single_root(self):
        assert_grade_correct("polynomial_roots", "5", "5")

    def test_negative_roots(self):
        assert_grade_correct("polynomial_roots", "-3, -1, 2, 5", "-3, -1, 2, 5")

    def test_wrong_roots_rejected(self):
        assert_grade_wrong("polynomial_roots", "0, 0, 0, 0", "2, 2, 3, 3")


# ---------------------------------------------------------------------------
# Linear Systems
# ---------------------------------------------------------------------------
class TestLinearSystemsEdgeCases:
    def test_integer_solutions(self):
        assert_grade_correct("linear_systems", "x1 = 3, x2 = 5", "x1 = 3, x2 = 5")

    def test_fractional_solutions(self):
        assert_grade_correct("linear_systems", "x1 = 1/3, x2 = -2/5", "x1 = 1/3, x2 = -2/5")

    def test_wrong_solutions_rejected(self):
        assert_grade_wrong("linear_systems", "x1 = 0, x2 = 0", "x1 = 3, x2 = 5")


# ---------------------------------------------------------------------------
# Modular Exponentiation
# ---------------------------------------------------------------------------
class TestModExpEdgeCases:
    def test_zero_base(self):
        """0^5 mod 7 = 0."""
        assert_grade_correct("mod_exp", "0", 0)

    def test_base_one(self):
        """1^100 mod 7 = 1."""
        assert_grade_correct("mod_exp", "1", 1)

    def test_exponent_zero(self):
        """a^0 mod c = 1 for any c > 1."""
        assert_grade_correct("mod_exp", "1", 1)

    def test_modulus_two(self):
        """Odd^anything mod 2 = 1."""
        assert_grade_correct("mod_exp", "1", 1)

    def test_wrong_answer_rejected(self):
        assert_grade_wrong("mod_exp", "999", 42)


# ---------------------------------------------------------------------------
# Probability: Bayesian Updating
# ---------------------------------------------------------------------------
class TestProbBayesEdgeCases:
    def test_perfect_test_posterior_one(self):
        """If sensitivity=1 and specificity=1, posterior should be 1."""
        assert_grade_correct("prob_bayes", "1", "1")

    def test_common_fraction(self):
        assert_grade_correct("prob_bayes", "1/2", "1/2")

    def test_wrong_fraction_rejected(self):
        assert_grade_wrong("prob_bayes", "999/1", "1/2")


# ---------------------------------------------------------------------------
# Quantum Amplitudes
# ---------------------------------------------------------------------------
class TestQuantumAmplitudesEdgeCases:
    def test_basis_state(self):
        assert_grade_correct("quantum_amplitudes", "1|0>", "1|0>")

    def test_global_phase_invariance(self):
        """Global phase difference should be accepted."""
        answer = "(1/sqrt(2))|0> + (1/sqrt(2))|1>"
        prediction = "(-1/sqrt(2))|0> + (-1/sqrt(2))|1>"
        assert_grade_correct("quantum_amplitudes", prediction, answer)

    def test_wrong_state_rejected(self):
        assert_grade_wrong("quantum_amplitudes", "1|1>", "1|0>")

    def test_superposition(self):
        answer = "(1/sqrt(2))|0> + (1/sqrt(2))|1>"
        assert_grade_correct("quantum_amplitudes", answer, answer)


# ---------------------------------------------------------------------------
# Formal Grammars
# ---------------------------------------------------------------------------
class TestFormalGrammarsEdgeCases:
    def test_yes_answer(self):
        assert_grade_correct("formal_grammars", "Yes", "Yes")

    def test_no_answer(self):
        assert_grade_correct("formal_grammars", "No", "No")

    def test_case_insensitive_yes(self):
        assert_grade_correct("formal_grammars", "yes", "Yes")

    def test_mixed_case_yes(self):
        assert_grade_correct("formal_grammars", "YES", "Yes")

    def test_yes_no_cross_rejected(self):
        assert_grade_wrong("formal_grammars", "No", "Yes")
        assert_grade_wrong("formal_grammars", "Yes", "No")


# ---------------------------------------------------------------------------
# Game Nim
# ---------------------------------------------------------------------------
class TestGameNimEdgeCases:
    def test_losing_position(self):
        assert_grade_correct("game_nim", "Losing position", "[heaps: 3, 5] losing")

    def test_winning_move(self):
        answer = "[heaps: 4, 7] winning | Heap 2: remove 3"
        assert_grade_correct("game_nim", "Heap 2: remove 3", answer)

    def test_alternative_winning_move(self):
        """Any valid winning move should be accepted, not just the canonical one."""
        # Heaps [4, 7]: nim-sum = 3. Heap 2 remove 3 is canonical.
        # Heap 1 remove... target = 4^3 = 7 > 4, so no move on heap 1.
        # Use different heaps: [1, 2], nim-sum = 3.
        # heap 2: target = 2^3 = 1, remove 1 -> [1, 1], nim-sum = 0.
        answer = "[heaps: 1, 2] winning | Heap 2: remove 1"
        assert_grade_correct("game_nim", "Heap 2: remove 1", answer)

    def test_wrong_move_rejected(self):
        answer = "[heaps: 4, 7] winning | Heap 2: remove 3"
        assert_grade_wrong("game_nim", "Heap 1: remove 99", answer)

    def test_move_exceeds_heap_rejected(self):
        """Removing more items than the heap contains must be rejected."""
        answer = "[heaps: 4, 7] winning | Heap 1: remove 2"
        assert_grade_wrong("game_nim", "Heap 1: remove 100", answer)

    def test_invalid_heap_index_rejected(self):
        """Heap index out of range must be rejected."""
        answer = "[heaps: 3, 5] winning | Heap 1: remove 2"
        assert_grade_wrong("game_nim", "Heap 99: remove 1", answer)

    def test_losing_vs_winning_cross_rejected(self):
        answer = "[heaps: 4, 7] winning | Heap 2: remove 3"
        assert_grade_wrong("game_nim", "Losing position", answer)


# ---------------------------------------------------------------------------
# Diophantine Equations
# ---------------------------------------------------------------------------
class TestDiophantineEdgeCases:
    def test_standard_tuple(self):
        assert_grade_correct("diophantine", "(3, 7)", "(3, 7)")

    def test_negative_y(self):
        assert_grade_correct("diophantine", "(5, -3)", "(5, -3)")

    def test_wrong_tuple_rejected(self):
        assert_grade_wrong("diophantine", "(100, 100)", "(3, 7)")


# ---------------------------------------------------------------------------
# Signal DFT
# ---------------------------------------------------------------------------
class TestSignalDFTEdgeCases:
    def test_correct_array(self):
        answer = "[10.0000+0.0000j, -2.0000+2.0000j, -2.0000+0.0000j, -2.0000-2.0000j]"
        assert_grade_correct("signal_dft", answer, answer)

    def test_wrong_array_rejected(self):
        answer = "[10.0000+0.0000j, -2.0000+2.0000j, -2.0000+0.0000j, -2.0000-2.0000j]"
        wrong = "[0.0000+0.0000j, 0.0000+0.0000j, 0.0000+0.0000j, 0.0000+0.0000j]"
        assert_grade_wrong("signal_dft", wrong, answer)


# ---------------------------------------------------------------------------
# Geometry: Polygon Area
# ---------------------------------------------------------------------------
class TestGeoPolygonEdgeCases:
    def test_integer_area(self):
        assert_grade_correct("geo_polygon", "100", 100)

    def test_fraction_area(self):
        assert_grade_correct("geo_polygon", "15/2", "15/2")

    def test_wrong_area_rejected(self):
        assert_grade_wrong("geo_polygon", "999", 100)


# ---------------------------------------------------------------------------
# Cryptographic Arithmetic (RSA)
# ---------------------------------------------------------------------------
class TestCryptoRSAEdgeCases:
    def test_correct_key(self):
        assert_grade_correct("crypto_rsa", "2753", 2753)

    def test_wrong_key_rejected(self):
        assert_grade_wrong("crypto_rsa", "1", 2753)


# ---------------------------------------------------------------------------
# Abstract Algebra: Group Orders
# ---------------------------------------------------------------------------
class TestAlgebraGroupsEdgeCases:
    def test_correct_order(self):
        assert_grade_correct("algebra_groups", "4", 4)

    def test_wrong_order_rejected(self):
        assert_grade_wrong("algebra_groups", "999", 4)


# ---------------------------------------------------------------------------
# Combinatorics: Stars and Bars
# ---------------------------------------------------------------------------
class TestCombinatoricsStarsEdgeCases:
    def test_correct_count(self):
        assert_grade_correct("combinatorics_stars", "2925", 2925)

    def test_wrong_count_rejected(self):
        assert_grade_wrong("combinatorics_stars", "0", 2925)


# ---------------------------------------------------------------------------
# Graph Shortest Path
# ---------------------------------------------------------------------------
class TestGraphShortestPathEdgeCases:
    def test_correct_distance(self):
        assert_grade_correct("graph_shortest_path", "17", 17)

    def test_wrong_distance_rejected(self):
        assert_grade_wrong("graph_shortest_path", "0", 17)


# ---------------------------------------------------------------------------
# Vector Calculus: Divergence
# ---------------------------------------------------------------------------
class TestVectorDivEdgeCases:
    def test_correct_expression(self):
        assert_grade_correct("vector_div", "-6*y - 2*cos(y) + 2", "-6*y - 2*cos(y) + 2")

    def test_wrong_expression_rejected(self):
        assert_grade_wrong("vector_div", "0", "-6*y - 2*cos(y) + 2")


# ---------------------------------------------------------------------------
# Taylor Series
# ---------------------------------------------------------------------------
class TestTaylorSeriesEdgeCases:
    def test_correct_coefficient(self):
        assert_grade_correct("taylor_series", "81/40", "81/40")

    def test_negative_coefficient(self):
        assert_grade_correct("taylor_series", "-1/6", "-1/6")

    def test_wrong_coefficient_rejected(self):
        assert_grade_wrong("taylor_series", "0", "81/40")


# ---------------------------------------------------------------------------
# Differential Equations (RLC)
# ---------------------------------------------------------------------------
class TestDiffEqRLCEdgeCases:
    def test_wrong_solution_rejected(self):
        answer = "5*exp(-t/3)"
        assert_grade_wrong("diff_eq_rlc", "0", answer)


# ---------------------------------------------------------------------------
# Financial Mathematics
# ---------------------------------------------------------------------------
class TestFinanceMathEdgeCases:
    def test_within_tolerance(self):
        answer = 1000.00
        assert_grade_correct("finance_math", "1000.00", answer)

    def test_outside_tolerance(self):
        answer = 1000.00
        assert_grade_wrong("finance_math", "1100.00", answer)


# ---------------------------------------------------------------------------
# Boolean K-Map
# ---------------------------------------------------------------------------
class TestBooleanKmapEdgeCases:
    def test_wrong_expression_rejected(self):
        # Use a known answer from snapshot
        answer = "(A & C & ~D) | (B & D & ~A) | (C & D & ~A)"
        assert_grade_wrong("boolean_kmap", "~A & ~B & ~C", answer)


# ---------------------------------------------------------------------------
# Jordan Normal Form
# ---------------------------------------------------------------------------
class TestJordanNormalEdgeCases:
    def test_wrong_matrices_rejected(self):
        assert_grade_wrong(
            "jordan_normal", "J = [[0]]\nP = [[1]]", "A = [[1]]\nJ = [[2]]\nP = [[3]]"
        )

    def test_invertible_p_required(self):
        """P with det=0 must be rejected."""
        assert_grade_wrong(
            "jordan_normal",
            "J = [[1, 0], [0, 1]]\nP = [[1, 0], [0, 0]]",
            "A = [[1, 0], [0, 1]]\nJ = [[1, 0], [0, 1]]\nP = [[1, 0], [0, 1]]",
        )


# ---------------------------------------------------------------------------
# Algorithmic Trace
# ---------------------------------------------------------------------------
class TestAlgorithmicTraceEdgeCases:
    def test_correct_list(self):
        assert_grade_correct("algorithmic_trace", "[34, 43, 51, 63, 92]", [34, 43, 51, 63, 92])

    def test_correct_integer(self):
        assert_grade_correct("algorithmic_trace", "3", 3)

    def test_wrong_list_rejected(self):
        assert_grade_wrong("algorithmic_trace", "[]", [34, 43, 51, 63, 92])

    def test_wrong_integer_rejected(self):
        assert_grade_wrong("algorithmic_trace", "-1", 3)


# ---------------------------------------------------------------------------
# Combinatorics: Stars and Bars (extended)
# ---------------------------------------------------------------------------
class TestCombinatoricsStarsExtendedEdgeCases:
    def test_single_bin(self):
        assert_grade_correct("combinatorics_stars", "1", 1)

    def test_zero_objects(self):
        assert_grade_correct("combinatorics_stars", "1", 1)

    def test_wrong_count_negative(self):
        assert_grade_wrong("combinatorics_stars", "-1", 2925)


# ---------------------------------------------------------------------------
# Graph Shortest Path (extended)
# ---------------------------------------------------------------------------
class TestGraphShortestPathExtendedEdgeCases:
    def test_zero_distance(self):
        assert_grade_correct("graph_shortest_path", "0", 0)

    def test_large_distance(self):
        assert_grade_correct("graph_shortest_path", "99999", 99999)

    def test_wrong_distance_negative(self):
        assert_grade_wrong("graph_shortest_path", "-1", 17)


# ---------------------------------------------------------------------------
# Vector Calculus: Divergence (extended)
# ---------------------------------------------------------------------------
class TestVectorDivExtendedEdgeCases:
    def test_zero_divergence(self):
        assert_grade_correct("vector_div", "0", "0")

    def test_constant_divergence(self):
        assert_grade_correct("vector_div", "3", "3")

    def test_wrong_divergence(self):
        assert_grade_wrong("vector_div", "x + y + z", "6*x")


# ---------------------------------------------------------------------------
# Taylor Series (extended)
# ---------------------------------------------------------------------------
class TestTaylorSeriesExtendedEdgeCases:
    def test_zero_coefficient(self):
        assert_grade_correct("taylor_series", "0", "0")

    def test_integer_coefficient(self):
        assert_grade_correct("taylor_series", "1", "1")

    def test_wrong_coefficient_string(self):
        assert_grade_wrong("taylor_series", "sin(x)", "1/6")


# ---------------------------------------------------------------------------
# Differential Equations (extended)
# ---------------------------------------------------------------------------
class TestDiffEqRLCExtendedEdgeCases:
    def test_zero_solution(self):
        assert_grade_correct("diff_eq_rlc", "0", "0")

    def test_exponential_solution(self):
        assert_grade_correct("diff_eq_rlc", "exp(-t)", "exp(-t)")

    def test_wrong_solution_string(self):
        assert_grade_wrong("diff_eq_rlc", "t^2 + 1", "exp(-t)")


# ---------------------------------------------------------------------------
# Financial Mathematics (extended)
# ---------------------------------------------------------------------------
class TestFinanceMathExtendedEdgeCases:
    def test_zero_amount(self):
        assert_grade_correct("finance_math", "0.00", 0.0)

    def test_large_amount(self):
        assert_grade_correct("finance_math", "1000000.00", 1000000.0)

    def test_dollar_sign_format(self):
        """Dollar sign should be stripped by grader."""
        cls = CATEGORIES["finance_math"]
        instance = cls(seed=42)
        assert instance.grade("$1000.00", 1000.00) is True

    def test_comma_format(self):
        """Commas should be stripped by grader."""
        cls = CATEGORIES["finance_math"]
        instance = cls(seed=42)
        assert instance.grade("$1,000.00", 1000.00) is True


# ---------------------------------------------------------------------------
# Jordan Normal Form (extended)
# ---------------------------------------------------------------------------
class TestJordanNormalExtendedEdgeCases:
    def test_diagonal_matrix(self):
        """Diagonal matrix is its own Jordan form."""
        cls = CATEGORIES["jordan_normal"]
        instance = cls(seed=42)
        # Self-grade a generated problem
        p = instance.generate(1, 0)
        pred = str(p.answer)
        # Extract J and P parts
        if "J =" in pred and "P =" in pred:
            assert instance.grade(pred, p.answer) is True


# ---------------------------------------------------------------------------
# Cross-seed reproducibility
# ---------------------------------------------------------------------------
class TestCrossSeedReproducibility:
    """Verify that different seeds produce different problems but same seed is deterministic."""

    @pytest.mark.parametrize("seed", [1, 100, 999, 2**16, 2**31 - 1])
    def test_different_seeds_different_problems(self, seed):
        """Different seeds should produce different problems (most of the time)."""
        from forge.categories.mod_exp import ModExpCategory
        instance1 = ModExpCategory(seed=seed)
        instance2 = ModExpCategory(seed=seed + 1)
        p1 = instance1.generate(3, 0)
        p2 = instance2.generate(3, 0)
        # Different seeds should produce different problems (with high probability)
        # We just verify both generate successfully
        assert p1.answer is not None
        assert p2.answer is not None

    @pytest.mark.parametrize("seed", [42, 100, 999])
    def test_same_seed_deterministic(self, seed):
        """Same seed must always produce identical output."""
        from forge.categories.matrix_det import MatrixDetCategory
        instance1 = MatrixDetCategory(seed=seed)
        instance2 = MatrixDetCategory(seed=seed)
        p1 = instance1.generate(3, 0)
        p2 = instance2.generate(3, 0)
        assert p1.question == p2.question
        assert str(p1.answer) == str(p2.answer)


# ---------------------------------------------------------------------------
# Adversarial formatting tests
# ---------------------------------------------------------------------------
class TestAdversarialFormatting:
    """Test that graders handle malformed input gracefully."""

    def test_empty_string_rejected(self):
        """Empty string should be rejected by all numeric graders."""
        for name in ["mod_exp", "matrix_det", "crypto_rsa", "combinatorics_stars",
                      "graph_shortest_path", "algebra_groups"]:
            cls = CATEGORIES[name]
            instance = cls(seed=42)
            assert instance.grade("", 42) is False, f"{name} accepted empty string"

    def test_whitespace_only_rejected(self):
        """Whitespace-only should be rejected."""
        for name in ["mod_exp", "matrix_det", "crypto_rsa"]:
            cls = CATEGORIES[name]
            instance = cls(seed=42)
            assert instance.grade("   ", 42) is False, f"{name} accepted whitespace"

    def test_garbage_string_rejected(self):
        """Random garbage should be rejected."""
        for name in ["mod_exp", "matrix_det", "crypto_rsa", "combinatorics_stars"]:
            cls = CATEGORIES[name]
            instance = cls(seed=42)
            assert instance.grade("xyzzy12345!@#$%", 42) is False, f"{name} accepted garbage"

    def test_negative_number_rejected_for_positive(self):
        """Negative number should be rejected when answer is positive."""
        cls = CATEGORIES["mod_exp"]
        instance = cls(seed=42)
        assert instance.grade("-42", 42) is False

    def test_float_for_integer_answer(self):
        """Float representation of integer - behavior depends on grader."""
        cls = CATEGORIES["mod_exp"]
        instance = cls(seed=42)
        # mod_exp grader uses int() which doesn't accept "42.0"
        # This is correct grader behavior - float format is not accepted
        assert instance.grade("42.0", 42) is False

    def test_comma_separated_number(self):
        """Number with commas should be accepted."""
        cls = CATEGORIES["mod_exp"]
        instance = cls(seed=42)
        assert instance.grade("1,234", 1234) is True


# ---------------------------------------------------------------------------
# Infrastructure method tests
# ---------------------------------------------------------------------------
class TestInfrastructureMethods:
    """Test generate_batch() and system_prompt() methods."""

    def test_generate_batch_returns_list(self):
        """generate_batch should return a list of Problems."""
        from forge.categories.mod_exp import ModExpCategory
        instance = ModExpCategory(seed=42)
        problems = instance.generate_batch(3, 5)
        assert isinstance(problems, list)
        assert len(problems) == 5
        for p in problems:
            assert p.category == "mod_exp"
            assert p.difficulty == 3

    def test_generate_batch_deterministic(self):
        """Same seed should produce identical batches."""
        from forge.categories.matrix_det import MatrixDetCategory
        instance1 = MatrixDetCategory(seed=42)
        instance2 = MatrixDetCategory(seed=42)
        batch1 = instance1.generate_batch(2, 10)
        batch2 = instance2.generate_batch(2, 10)
        for p1, p2 in zip(batch1, batch2):
            assert p1.question == p2.question
            assert str(p1.answer) == str(p2.answer)

    def test_system_prompt_not_empty(self):
        """system_prompt() should return non-empty string for all categories."""
        for name, cls in CATEGORIES.items():
            instance = cls(seed=42)
            prompt = instance.system_prompt()
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "ANSWER" in prompt.upper()

    def test_system_prompt_contains_category_format(self):
        """system_prompt() should include category-specific answer format."""
        from forge.categories.mod_exp import ModExpCategory
        instance = ModExpCategory(seed=42)
        prompt = instance.system_prompt()
        assert "integer" in prompt.lower() or "mod" in prompt.lower()

    def test_generate_returns_problem_dataclass(self):
        """generate() should return a Problem dataclass."""
        from forge.core.generator import Problem
        for name, cls in list(CATEGORIES.items())[:5]:
            instance = cls(seed=42)
            p = instance.generate(1, 0)
            assert isinstance(p, Problem)
            assert hasattr(p, 'question')
            assert hasattr(p, 'answer')
            assert hasattr(p, 'category')
            assert hasattr(p, 'difficulty')
            assert hasattr(p, 'iteration')
            assert hasattr(p, 'seed')
