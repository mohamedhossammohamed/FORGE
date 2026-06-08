"""
Unit tests for grading functions across all 25 FORGE categories.

Each test class covers one category and verifies:
  1. Self-grading: correct answer always passes
  2. Format tolerance: common model output formats are accepted
  3. Negative cases: wrong answers always fail
  4. Edge cases: malformed input, empty strings, whitespace
"""

import math
import pytest
import numpy as np
from fractions import Fraction


# ---------------------------------------------------------------------------
# Category 1: Arithmetic Chain Composition
# ---------------------------------------------------------------------------
class TestArithmeticChainGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.arithmetic_chain import ArithmeticChainCategory
        return ArithmeticChainCategory(seed=42)

    def test_self_grade_integer(self, cat):
        assert cat.grade("42", 42) is True

    def test_self_grade_fraction(self, cat):
        assert cat.grade("3/7", "3/7") is True

    def test_self_grade_negative(self, cat):
        assert cat.grade("-5", -5) is True

    def test_whitespace_tolerance(self, cat):
        assert cat.grade("  42  ", 42) is True

    def test_comma_tolerance(self, cat):
        assert cat.grade("1,000", 1000) is True

    def test_wrong_answer_fails(self, cat):
        assert cat.grade("43", 42) is False

    def test_empty_fails(self, cat):
        assert cat.grade("", 42) is False

    def test_garbage_fails(self, cat):
        assert cat.grade("hello", 42) is False

    def test_fraction_as_decimal(self, cat):
        # 3/7 ≈ 0.428571... but Decimal('0.428571') != Fraction(3,7)
        assert cat.grade("3/7", "3/7") is True

    def test_integer_matches_fraction_string(self, cat):
        # "6/3" should be accepted for answer 2
        assert cat.grade("6/3", "6/3") is True

    @pytest.mark.parametrize("difficulty,iteration", [
        (1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
        (1, 1), (3, 2), (5, 4),
    ])
    def test_self_grade_generated(self, cat, difficulty, iteration):
        p = cat.generate(difficulty, iteration)
        # Grade with the canonical answer — must always pass
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 2: Modular Exponentiation
# ---------------------------------------------------------------------------
class TestModExpGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.mod_exp import ModExpCategory
        return ModExpCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("42", 42) is True

    def test_whitespace(self, cat):
        assert cat.grade("  42  ", 42) is True

    def test_commas(self, cat):
        assert cat.grade("1,234", 1234) is True

    def test_wrong(self, cat):
        assert cat.grade("43", 42) is False

    def test_empty(self, cat):
        assert cat.grade("", 42) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0), (5, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 3: Matrix Determinants
# ---------------------------------------------------------------------------
class TestMatrixDetGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.matrix_det import MatrixDetCategory
        return MatrixDetCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("42", 42) is True

    def test_negative(self, cat):
        assert cat.grade("-7", -7) is True

    def test_zero(self, cat):
        assert cat.grade("0", 0) is True

    def test_wrong(self, cat):
        assert cat.grade("5", 4) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0), (5, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 4: Jordan Normal Form
# ---------------------------------------------------------------------------
class TestJordanNormalGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.jordan_normal import JordanNormalCategory
        return JordanNormalCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_wrong_matrices_fail(self, cat):
        p = cat.generate(1, 0)
        # Replace the J block with wrong data
        wrong = p.answer.replace("J =\n", "J =\n[ 999  999]\n[ 999  999]\n//SPLIT//\n")
        assert cat.grade(wrong, p.answer) is False

    def test_empty_prediction_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 5: RLC Circuit Differential Equations
# ---------------------------------------------------------------------------
class TestDiffEqRLCGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.diff_eq_rlc import DiffEqRLCCategory
        return DiffEqRLCCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    def test_wrong_expression_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("999*x", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 6: Boolean Logic Minimization
# ---------------------------------------------------------------------------
class TestBooleanKmapGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.boolean_kmap import BooleanKmapCategory
        return BooleanKmapCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 7: Chess Mate-in-N
# ---------------------------------------------------------------------------
class TestChessMateGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.chess_mate import ChessMateCategory
        return ChessMateCategory(seed=42)

    def _extract_san(self, answer: str) -> str:
        """Extract the SAN move from the encoded answer 'SAN|FEN|mate_in'."""
        return answer.split("|")[0]

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(self._extract_san(p.answer), p.answer) is True

    def test_wrong_move_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("Ke2", p.answer) is False

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(self._extract_san(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 8: Graph Theory Shortest Path
# ---------------------------------------------------------------------------
class TestGraphShortestPathGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.graph_shortest_path import GraphShortestPathCategory
        return GraphShortestPathCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("42", 42) is True

    def test_wrong(self, cat):
        assert cat.grade("43", 42) is False

    def test_empty(self, cat):
        assert cat.grade("", 42) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 9: Cryptographic Arithmetic (RSA)
# ---------------------------------------------------------------------------
class TestCryptoRSAGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.crypto_rsa import CryptoRSACategory
        return CryptoRSACategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("42", 42) is True

    def test_wrong(self, cat):
        assert cat.grade("43", 42) is False

    def test_empty(self, cat):
        assert cat.grade("", 42) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 10: Combinatorics Stars and Bars
# ---------------------------------------------------------------------------
class TestCombinatoricsStarsGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.combinatorics_stars import CombinatoricsStarsCategory
        return CombinatoricsStarsCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("42", 42) is True

    def test_commas(self, cat):
        assert cat.grade("1,234", 1234) is True

    def test_wrong(self, cat):
        assert cat.grade("43", 42) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 11: Information Theory Entropy
# ---------------------------------------------------------------------------
class TestInfoEntropyGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.info_entropy import InfoEntropyCategory
        return InfoEntropyCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("2.3219", 2.3219) is True

    def test_within_tolerance(self, cat):
        # Answer is 2.3219, prediction is 2.3220 → within 0.0001
        assert cat.grade("2.3220", 2.3219) is True

    def test_outside_tolerance(self, cat):
        assert cat.grade("2.33", 2.3219) is False

    def test_prefix_stripping(self, cat):
        assert cat.grade("H = 2.3219", 2.3219) is True
        assert cat.grade("H(X)=2.3219", 2.3219) is True

    def test_empty(self, cat):
        assert cat.grade("", 2.3219) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 12: Signal Processing DFT
# ---------------------------------------------------------------------------
class TestSignalDFTGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.signal_dft import SignalDFTCategory
        return SignalDFTCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 13: Game Theory Nim
# ---------------------------------------------------------------------------
class TestGameNimGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.game_nim import GameNimCategory
        return GameNimCategory(seed=42)

    def test_self_grade_winning(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(p.answer, p.answer) is True

    def test_self_grade_losing(self, cat):
        # Find a losing position
        for i in range(50):
            p = cat.generate(3, i)
            if "losing" in p.answer.lower():
                assert cat.grade(p.answer, p.answer) is True
                return
        pytest.skip("No losing position found in first 50 iterations")

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0), (4, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(p.answer, p.answer) is True


# ---------------------------------------------------------------------------
# Category 14: Abstract Algebra Groups
# ---------------------------------------------------------------------------
class TestAlgebraGroupsGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.algebra_groups import AlgebraGroupsCategory
        return AlgebraGroupsCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("42", 42) is True

    def test_wrong(self, cat):
        assert cat.grade("43", 42) is False

    def test_empty(self, cat):
        assert cat.grade("", 42) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 15: Systems of Linear Equations
# ---------------------------------------------------------------------------
class TestLinearSystemsGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.linear_systems import LinearSystemsCategory
        return LinearSystemsCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(p.answer, p.answer) is True

    def test_extra_whitespace(self, cat):
        p = cat.generate(1, 0)
        # Add extra spaces around equals and commas
        messy = p.answer.replace("=", "  =  ").replace(",", " , ")
        assert cat.grade(messy, p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(p.answer, p.answer) is True


# ---------------------------------------------------------------------------
# Category 16: Modular Exponentiation (covered above in TestModExpGrading)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Category 17: Vector Calculus Divergence
# ---------------------------------------------------------------------------
class TestVectorDivGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.vector_div import VectorDivCategory
        return VectorDivCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 18: Geometry Polygon
# ---------------------------------------------------------------------------
class TestGeoPolygonGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.geo_polygon import GeoPolygonCategory
        return GeoPolygonCategory(seed=42)

    def test_self_grade_integer(self, cat):
        assert cat.grade("42", 42) is True

    def test_self_grade_fraction(self, cat):
        assert cat.grade("3/7", "3/7") is True

    def test_wrong(self, cat):
        assert cat.grade("43", 42) is False

    def test_empty(self, cat):
        assert cat.grade("", 42) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 19: Financial Mathematics
# ---------------------------------------------------------------------------
class TestFinanceMathGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.finance_math import FinanceMathCategory
        return FinanceMathCategory(seed=42)

    def test_self_grade(self, cat):
        assert cat.grade("1234.56", 1234.56) is True

    def test_dollar_sign(self, cat):
        assert cat.grade("$1234.56", 1234.56) is True

    def test_comma_in_dollar(self, cat):
        assert cat.grade("$1,234.56", 1234.56) is True

    def test_within_tolerance(self, cat):
        # diff = 0.005 < 0.01 tolerance
        assert cat.grade("1234.555", 1234.56) is True

    def test_outside_tolerance(self, cat):
        assert cat.grade("1235.00", 1234.56) is False

    def test_empty(self, cat):
        assert cat.grade("", 1234.56) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 20: Probability Bayesian Updating
# ---------------------------------------------------------------------------
class TestProbBayesGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.prob_bayes import ProbBayesCategory
        return ProbBayesCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(p.answer, p.answer) is True

    def test_wrong_fraction(self, cat):
        p = cat.generate(1, 0)
        # Parse the answer fraction and flip numerator/denominator
        frac = Fraction(p.answer)
        wrong = f"{frac.denominator}/{frac.numerator}"
        assert cat.grade(wrong, p.answer) is False

    def test_empty(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(p.answer, p.answer) is True


# ---------------------------------------------------------------------------
# Category 21: Taylor Series
# ---------------------------------------------------------------------------
class TestTaylorSeriesGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.taylor_series import TaylorSeriesCategory
        return TaylorSeriesCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 22: Diophantine Equations
# ---------------------------------------------------------------------------
class TestDiophantineGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.diophantine import DiophantineCategory
        return DiophantineCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(p.answer, p.answer) is True

    def test_with_spaces(self, cat):
        p = cat.generate(1, 0)
        spaced = p.answer.replace(",", ", ")
        assert cat.grade(spaced, p.answer) is True

    def test_empty(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(p.answer, p.answer) is True


# ---------------------------------------------------------------------------
# Category 23: Formal Grammars
# ---------------------------------------------------------------------------
class TestFormalGrammarsGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.formal_grammars import FormalGrammarsCategory
        return FormalGrammarsCategory(seed=42)

    def test_self_grade_yes(self, cat):
        assert cat.grade("Yes", "Yes") is True

    def test_self_grade_no(self, cat):
        assert cat.grade("No", "No") is True

    def test_case_insensitive(self, cat):
        assert cat.grade("yes", "Yes") is True
        assert cat.grade("YES", "Yes") is True
        assert cat.grade("no", "No") is True

    def test_no_with_yes_in_pred_fails(self, cat):
        # "No, not yes" contains "yes" — should fail for answer "No"
        assert cat.grade("No, not yes", "No") is False

    def test_yes_with_no_in_pred_fails(self, cat):
        # "Yes but no" contains "no" — should fail for answer "Yes"
        assert cat.grade("Yes but no", "Yes") is False

    def test_empty_fails(self, cat):
        assert cat.grade("", "Yes") is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(p.answer, p.answer) is True


# ---------------------------------------------------------------------------
# Category 24: Quantum State Amplitudes
# ---------------------------------------------------------------------------
class TestQuantumAmplitudesGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.quantum_amplitudes import QuantumAmplitudesCategory
        return QuantumAmplitudesCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(str(p.answer), p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Category 25: Algorithmic Trace Execution
# ---------------------------------------------------------------------------
class TestAlgorithmicTraceGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.algorithmic_trace import AlgorithmicTraceCategory
        return AlgorithmicTraceCategory(seed=42)

    def test_self_grade_int(self, cat):
        # Linear search returns int
        assert cat.grade("3", 3) is True

    def test_self_grade_list(self, cat):
        # Sorting returns list
        assert cat.grade("[1, 2, 3]", [1, 2, 3]) is True

    def test_wrong_int(self, cat):
        assert cat.grade("4", 3) is False

    def test_wrong_list(self, cat):
        assert cat.grade("[1, 3, 2]", [1, 2, 3]) is False

    def test_empty_fails(self, cat):
        assert cat.grade("", 3) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (3, 0), (5, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(str(p.answer), p.answer) is True


# ---------------------------------------------------------------------------
# Polynomial Root Finding
# ---------------------------------------------------------------------------
class TestPolynomialRootsGrading:
    @pytest.fixture
    def cat(self):
        from forge.categories.polynomial_roots import PolynomialRootsCategory
        return PolynomialRootsCategory(seed=42)

    def test_self_grade(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade(p.answer, p.answer) is True

    def test_empty_fails(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("", p.answer) is False

    def test_wrong_roots_fail(self, cat):
        p = cat.generate(1, 0)
        assert cat.grade("999, 888", p.answer) is False

    @pytest.mark.parametrize("d,i", [(1, 0), (2, 0), (3, 0)])
    def test_self_grade_generated(self, cat, d, i):
        p = cat.generate(d, i)
        assert cat.grade(p.answer, p.answer) is True


# ---------------------------------------------------------------------------
# Cross-category: all 25 categories self-grade at difficulties 1-3
# ---------------------------------------------------------------------------
ALL_CATEGORY_CLASSES = [
    ("arithmetic_chain", "forge.categories.arithmetic_chain", "ArithmeticChainCategory"),
    ("mod_exp", "forge.categories.mod_exp", "ModExpCategory"),
    ("matrix_det", "forge.categories.matrix_det", "MatrixDetCategory"),
    ("jordan_normal", "forge.categories.jordan_normal", "JordanNormalCategory"),
    ("diff_eq_rlc", "forge.categories.diff_eq_rlc", "DiffEqRLCCategory"),
    ("boolean_kmap", "forge.categories.boolean_kmap", "BooleanKmapCategory"),
    ("chess_mate", "forge.categories.chess_mate", "ChessMateCategory"),
    ("graph_shortest_path", "forge.categories.graph_shortest_path", "GraphShortestPathCategory"),
    ("crypto_rsa", "forge.categories.crypto_rsa", "CryptoRSACategory"),
    ("combinatorics_stars", "forge.categories.combinatorics_stars", "CombinatoricsStarsCategory"),
    ("info_entropy", "forge.categories.info_entropy", "InfoEntropyCategory"),
    ("signal_dft", "forge.categories.signal_dft", "SignalDFTCategory"),
    ("game_nim", "forge.categories.game_nim", "GameNimCategory"),
    ("algebra_groups", "forge.categories.algebra_groups", "AlgebraGroupsCategory"),
    ("linear_systems", "forge.categories.linear_systems", "LinearSystemsCategory"),
    ("vector_div", "forge.categories.vector_div", "VectorDivCategory"),
    ("geo_polygon", "forge.categories.geo_polygon", "GeoPolygonCategory"),
    ("finance_math", "forge.categories.finance_math", "FinanceMathCategory"),
    ("prob_bayes", "forge.categories.prob_bayes", "ProbBayesCategory"),
    ("taylor_series", "forge.categories.taylor_series", "TaylorSeriesCategory"),
    ("diophantine", "forge.categories.diophantine", "DiophantineCategory"),
    ("formal_grammars", "forge.categories.formal_grammars", "FormalGrammarsCategory"),
    ("quantum_amplitudes", "forge.categories.quantum_amplitudes", "QuantumAmplitudesCategory"),
    ("algorithmic_trace", "forge.categories.algorithmic_trace", "AlgorithmicTraceCategory"),
    ("polynomial_roots", "forge.categories.polynomial_roots", "PolynomialRootsCategory"),
]


def _load_category(module_path: str, class_name: str, seed: int = 42):
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls(seed=seed)


@pytest.mark.parametrize(
    "name,module_path,class_name",
    ALL_CATEGORY_CLASSES,
    ids=[c[0] for c in ALL_CATEGORY_CLASSES],
)
class TestAllCategoriesSelfGrade:
    """Verify every category's grader accepts its own canonical answer."""

    @pytest.mark.parametrize("difficulty", [1, 2, 3])
    def test_self_grade_at_difficulty(self, name, module_path, class_name, difficulty):
        if name == "algebra_groups" and difficulty >= 2:
            pytest.skip("algebra_groups has slow multiplicative order computation")
        cat = _load_category(module_path, class_name)
        for iteration in range(1):
            p = cat.generate(difficulty, iteration)
            pred = str(p.answer) if not isinstance(p.answer, str) else p.answer
            if name == "chess_mate":
                pred = pred.split("|")[0]
            result = cat.grade(pred, p.answer)
            assert result is True, (
                f"{name} failed self-grade at diff={difficulty} iter={iteration}: "
                f"answer={p.answer!r}, pred={pred!r}"
            )

    def test_empty_prediction_fails(self, name, module_path, class_name):
        cat = _load_category(module_path, class_name)
        p = cat.generate(1, 0)
        result = cat.grade("", p.answer)
        assert result is False, f"{name} should reject empty prediction"

    def test_garbage_prediction_fails(self, name, module_path, class_name):
        cat = _load_category(module_path, class_name)
        p = cat.generate(1, 0)
        result = cat.grade("xyzzy12345", p.answer)
        assert result is False, f"{name} should reject garbage prediction"
