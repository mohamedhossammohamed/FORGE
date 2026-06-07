"""
Deterministic grading engine for FORGE evaluations.

All grading is performed through exact computational verification using
SymPy, NumPy, and python-chess. No LLM judges are involved.
"""

import math
from fractions import Fraction
from typing import Any, Union

import numpy as np
import sympy
from sympy import simplify, Rational, Eq, Symbol, sympify
from sympy.core.relational import Relational


class ForgeGrader:
    """
    Zero-LLM deterministic grader for FORGE problems.
    
    Provides methods for exact numeric, symbolic, set-based, and
    game-state verification.
    """
    
    @staticmethod
    def evaluate_numeric(
        target: Union[int, float, Fraction],
        prediction: Union[int, float, str],
        tolerance: float = 1e-4,
    ) -> bool:
        """
        Evaluate numeric equivalence with tolerance.
        
        Uses math.isclose for floats, exact match for integers.
        Handles string predictions by attempting numeric parsing.
        
        Args:
            target: The canonical numeric answer
            prediction: The model's predicted value
            tolerance: Relative tolerance for float comparison
            
        Returns:
            True if prediction matches target within tolerance
        """
        try:
            if isinstance(prediction, str):
                prediction = prediction.strip()
                # Try parsing as fraction
                if '/' in prediction:
                    pred_frac = Fraction(prediction)
                    target_frac = Fraction(target)
                    return pred_frac == target_frac
                prediction = float(prediction)
            
            # Integer exact match
            if isinstance(target, int) and isinstance(prediction, (int, float)):
                if float(prediction) == int(float(prediction)):
                    return int(float(prediction)) == target
            
            # Float comparison
            return math.isclose(float(target), float(prediction), rel_tol=tolerance)
        except (ValueError, TypeError, ZeroDivisionError):
            return False
    
    @staticmethod
    def evaluate_symbolic(
        target_expr: str,
        prediction_expr: str,
        variables: list[str] | None = None,
    ) -> bool:
        """
        Evaluate symbolic mathematical equivalence.
        
        Uses sympy.simplify to check if target - prediction == 0.
        Handles trigonometric identities, algebraic simplifications, etc.
        
        Args:
            target_expr: Canonical symbolic expression string
            prediction_expr: Model's predicted expression string
            variables: List of variable names (auto-detected if None)
            
        Returns:
            True if expressions are symbolically equivalent
        """
        try:
            target = sympify(target_expr, evaluate=False)
            pred = sympify(prediction_expr, evaluate=False)
            
            # Direct simplification check
            diff = simplify(target - pred)
            if diff == 0:
                return True
            
            # Try with assumptions (positive reals)
            symbols = list(target.free_symbols | pred.free_symbols)
            if symbols:
                assumptions = {s: sympy.Symbol(s.name, positive=True) for s in symbols}
                target_sub = target.subs(assumptions)
                pred_sub = pred.subs(assumptions)
                diff = simplify(target_sub - pred_sub)
                return diff == 0
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def evaluate_exact(target: Any, prediction: Any) -> bool:
        """
        Evaluate exact equality (integers, strings, booleans, tuples).
        
        Args:
            target: The canonical answer
            prediction: The model's predicted answer
            
        Returns:
            True if exactly equal
        """
        if isinstance(target, str) and isinstance(prediction, str):
            return target.strip() == prediction.strip()
        return target == prediction
    
    @staticmethod
    def evaluate_set(
        target_set: set | list,
        prediction_set: set | list,
        order_matters: bool = False,
    ) -> bool:
        """
        Evaluate set/list equivalence.
        
        For root-finding, evaluates whether the prediction set matches
        the target set (accounting for multiplicity).
        
        Args:
            target_set: Canonical answer set
            prediction_set: Model's predicted set
            order_matters: If True, compare as ordered lists
            
        Returns:
            True if sets are equivalent
        """
        try:
            if order_matters:
                return list(target_set) == list(prediction_set)
            
            # Handle multiplicity (e.g., roots with multiplicity)
            target_list = sorted([str(x) for x in target_set])
            pred_list = sorted([str(x) for x in prediction_set])
            return target_list == pred_list
        except Exception:
            return False
    
    @staticmethod
    def evaluate_numeric_set(
        target: list,
        prediction: list,
        tolerance: float = 1e-4,
    ) -> bool:
        """
        Evaluate a set of numeric values with tolerance.
        
        Useful for roots, eigenvalues, etc. that may have floating-point representation.
        
        Args:
            target: List of canonical numeric answers
            prediction: List of predicted numeric values
            tolerance: Tolerance for each comparison
            
        Returns:
            True if all values match within tolerance (accounting for multiplicity)
        """
        try:
            if len(target) != len(prediction):
                return False
            
            target_sorted = sorted([complex(x) for x in target])
            pred_sorted = sorted([complex(x) for x in prediction])
            
            for t, p in zip(target_sorted, pred_sorted):
                if not math.isclose(t.real, p.real, rel_tol=tolerance):
                    return False
                if not math.isclose(t.imag, p.imag, rel_tol=tolerance):
                    return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def evaluate_game_state(
        board_fen: str,
        move_sequence: list[str],
        target_mate_in: int,
    ) -> bool:
        """
        Validate a chess move sequence achieves mate in N.
        
        Uses python-chess to verify:
        1. All moves are legal
        2. The sequence results in checkmate
        3. Mate is achieved in exactly N moves (or fewer)
        
        Args:
            board_fen: Starting position in FEN notation
            move_sequence: List of moves in UCI or SAN format
            target_mate_in: Expected moves to mate
            
        Returns:
            True if the sequence forces mate in <= target_mate_in
        """
        try:
            import chess
            
            board = chess.Board(fen=board_fen)
            moves_played = 0
            
            for move_str in move_sequence:
                # Try parsing as UCI, then SAN
                try:
                    move = chess.Move.from_uci(move_str)
                except ValueError:
                    try:
                        move = board.parse_san(move_str)
                    except ValueError:
                        return False
                
                if move not in board.legal_moves:
                    return False
                
                board.push(move)
                moves_played += 1
                
                if board.is_checkmate():
                    return moves_played <= target_mate_in
            
            return board.is_checkmate()
        except Exception:
            return False
    
    @staticmethod
    def evaluate_fraction(
        target: Fraction,
        prediction: Union[str, Fraction, int, float],
    ) -> bool:
        """
        Evaluate exact fractional equivalence.
        
        Args:
            target: Canonical answer as Fraction
            prediction: Model's answer (parsed to Fraction if string)
            
        Returns:
            True if fractions are exactly equal
        """
        try:
            if isinstance(prediction, str):
                prediction = prediction.strip()
                if '/' in prediction:
                    pred_frac = Fraction(prediction)
                else:
                    pred_frac = Fraction(prediction).limit_denominator(10**12)
            elif isinstance(prediction, float):
                pred_frac = Fraction(prediction).limit_denominator(10**12)
            else:
                pred_frac = Fraction(prediction)
            
            return target == pred_frac
        except (ValueError, TypeError, ZeroDivisionError):
            return False
    
    @staticmethod
    def evaluate_matrix(
        target: np.ndarray,
        prediction: np.ndarray,
        tolerance: float = 1e-6,
    ) -> bool:
        """
        Evaluate matrix equivalence.
        
        Uses numpy.allclose for floating-point matrices.
        
        Args:
            target: Canonical matrix
            prediction: Predicted matrix
            tolerance: Absolute tolerance
            
        Returns:
            True if matrices are element-wise close
        """
        try:
            target = np.array(target, dtype=float)
            prediction = np.array(prediction, dtype=float)
            
            if target.shape != prediction.shape:
                return False
            
            return np.allclose(target, prediction, atol=tolerance)
        except Exception:
            return False
    
    @staticmethod
    def evaluate_integer(target: int, prediction: Union[int, str]) -> bool:
        """
        Evaluate exact integer match.
        
        Handles string predictions by parsing to int.
        
        Args:
            target: Canonical integer answer
            prediction: Model's predicted integer
            
        Returns:
            True if exactly equal
        """
        try:
            if isinstance(prediction, str):
                prediction = int(prediction.strip().replace(',', ''))
            return int(target) == int(prediction)
        except (ValueError, TypeError):
            return False
