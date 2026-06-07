"""
FORGE category registry with auto-discovery.

All category modules are imported here and registered in CATEGORIES dict
for automatic discovery by the runner and CLI.
"""

from typing import Type

from ..core.generator import ForgeCategory

# Import all category implementations
from .arithmetic_chain import ArithmeticChainCategory
from .mod_exp import ModExpCategory
from .combinatorics_stars import CombinatoricsStarsCategory
from .game_nim import GameNimCategory
from .info_entropy import InfoEntropyCategory
from .matrix_det import MatrixDetCategory
from .linear_systems import LinearSystemsCategory
from .jordan_normal import JordanNormalCategory
from .vector_div import VectorDivCategory
from .polynomial_roots import PolynomialRootsCategory
from .algebra_groups import AlgebraGroupsCategory
from .diophantine import DiophantineCategory
from .crypto_rsa import CryptoRSACategory
from .taylor_series import TaylorSeriesCategory
from .diff_eq_rlc import DiffEqRLCCategory
from .finance_math import FinanceMathCategory
from .prob_bayes import ProbBayesCategory
from .boolean_kmap import BooleanKmapCategory
from .signal_dft import SignalDFTCategory
from .geo_polygon import GeoPolygonCategory
from .graph_shortest_path import GraphShortestPathCategory
from .formal_grammars import FormalGrammarsCategory
from .quantum_amplitudes import QuantumAmplitudesCategory
from .chess_mate import ChessMateCategory
from .algorithmic_trace import AlgorithmicTraceCategory

# Registry mapping category name to class
CATEGORIES: dict[str, Type[ForgeCategory]] = {
    "arithmetic_chain": ArithmeticChainCategory,
    "mod_exp": ModExpCategory,
    "combinatorics_stars": CombinatoricsStarsCategory,
    "game_nim": GameNimCategory,
    "info_entropy": InfoEntropyCategory,
    "matrix_det": MatrixDetCategory,
    "linear_systems": LinearSystemsCategory,
    "jordan_normal": JordanNormalCategory,
    "vector_div": VectorDivCategory,
    "polynomial_roots": PolynomialRootsCategory,
    "algebra_groups": AlgebraGroupsCategory,
    "diophantine": DiophantineCategory,
    "crypto_rsa": CryptoRSACategory,
    "taylor_series": TaylorSeriesCategory,
    "diff_eq_rlc": DiffEqRLCCategory,
    "finance_math": FinanceMathCategory,
    "prob_bayes": ProbBayesCategory,
    "boolean_kmap": BooleanKmapCategory,
    "signal_dft": SignalDFTCategory,
    "geo_polygon": GeoPolygonCategory,
    "graph_shortest_path": GraphShortestPathCategory,
    "formal_grammars": FormalGrammarsCategory,
    "quantum_amplitudes": QuantumAmplitudesCategory,
    "chess_mate": ChessMateCategory,
    "algorithmic_trace": AlgorithmicTraceCategory,
}

# Ordered list for display
CATEGORY_NAMES = list(CATEGORIES.keys())

def get_category(name: str) -> Type[ForgeCategory]:
    """Get a category class by name."""
    if name not in CATEGORIES:
        raise ValueError(
            f"Unknown category: {name}. "
            f"Available: {', '.join(CATEGORY_NAMES)}"
        )
    return CATEGORIES[name]

def get_all_categories() -> list[Type[ForgeCategory]]:
    """Get all registered category classes."""
    return list(CATEGORIES.values())
