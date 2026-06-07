"""
Category 1: Arithmetic Chain Composition

Generates N-step sequential arithmetic operations.
Difficulty scales from kindergarten (N=1, addition) to frontier (N=25, mixed fractional/exponent).
"""

import random
from fractions import Fraction

from ..core.generator import ForgeCategory, Problem


class ArithmeticChainCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "arithmetic_chain"
    
    @property
    def display_name(self) -> str:
        return "Arithmetic Chain Composition"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        """Return parameters for each difficulty level."""
        params = {
            1: {"n_steps": 1, "operations": ["+", "-"], "magnitude": 10, "use_fractions": False},
            2: {"n_steps": 3, "operations": ["+", "-", "*"], "magnitude": 50, "use_fractions": False},
            3: {"n_steps": 5, "operations": ["+", "-", "*", "//"], "magnitude": 100, "use_fractions": True},
            4: {"n_steps": 10, "operations": ["+", "-", "*", "//", "**"], "magnitude": 500, "use_fractions": True},
            5: {"n_steps": 25, "operations": ["+", "-", "*", "//", "**", "%"], "magnitude": 1000, "use_fractions": True},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n_steps = params["n_steps"]
        operations = params["operations"]
        magnitude = params["magnitude"]
        use_fractions = params["use_fractions"]
        
        # Generate initial value
        if use_fractions and rng.random() < 0.3:
            num = rng.integers(1, magnitude + 1)
            den = rng.integers(1, 10)
            value = Fraction(num, den)
        else:
            value = Fraction(rng.integers(1, magnitude + 1))
        
        # Generate chain
        steps = [(value, None)]
        
        for i in range(n_steps):
            op = operations[rng.integers(0, len(operations))]
            
            if use_fractions and rng.random() < 0.3:
                num = rng.integers(1, magnitude // 10 + 1)
                den = rng.integers(1, 10)
                operand = Fraction(num, den)
            else:
                operand = Fraction(rng.integers(1, magnitude // 5 + 1))
            
            # Avoid division by zero and problematic exponents
            if op == "//" or op == "/":
                while operand == 0:
                    operand = Fraction(rng.integers(1, 10))
            elif op == "**":
                operand = Fraction(rng.integers(2, 4))  # Keep exponents small
            
            steps.append((operand, op))
        
        # Format question with standard math notation
        op_symbols = {
            "+": "+", "-": "-", "*": "*", "//": "÷", "/": "/", "**": "^", "%": "mod"
        }
        
        parts = []
        for val, op in steps:
            if op is None:
                if val.denominator == 1:
                    parts.append(str(int(val)))
                else:
                    parts.append(f"({val})")
            else:
                sym = op_symbols.get(op, op)
                if val.denominator == 1:
                    parts.append(f" {sym} {int(val)}")
                else:
                    parts.append(f" {sym} ({val})")
        
        expression = "".join(parts)
        
        # Evaluate expression with standard operator precedence (PEMDAS)
        # Build a Python-evaluable expression
        py_ops = {"+": "+", "-": "-", "*": "*", "//": "//", "/": "/", "**": "**", "%": "%"}
        py_parts = []
        for val, op in steps:
            if op is None:
                py_parts.append(f"Fraction({val.numerator},{val.denominator})")
            else:
                py_sym = py_ops.get(op, op)
                py_parts.append(f" {py_sym} Fraction({val.numerator},{val.denominator})")
        py_expr = "".join(py_parts)
        
        answer = eval(py_expr, {"Fraction": Fraction})
        
        question = (
            f"Compute the following arithmetic expression. "
            f"Provide your answer as an exact fraction if it's not an integer.\n\n"
            f"{expression}"
        )
        
        # Format answer
        if answer.denominator == 1:
            answer = int(answer)
        else:
            answer = str(answer)
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"expression": expression, "n_steps": n_steps},
        )
    
    def grade(self, prediction: str, answer) -> bool:
        """Grade using exact fraction comparison."""
        try:
            if isinstance(answer, int):
                # Integer answer
                pred = prediction.strip().replace(',', '')
                if '/' in pred:
                    frac = Fraction(pred)
                    return frac.denominator == 1 and frac.numerator == answer
                return int(float(pred)) == answer
            else:
                # Fraction answer (as string)
                target = Fraction(answer)
                pred = prediction.strip()
                if '/' in pred:
                    return Fraction(pred) == target
                try:
                    # Try as decimal
                    from decimal import Decimal
                    d = Decimal(pred)
                    return Fraction(d) == target
                except:
                    return float(pred) == float(target)
        except (ValueError, TypeError, ZeroDivisionError):
            return False
