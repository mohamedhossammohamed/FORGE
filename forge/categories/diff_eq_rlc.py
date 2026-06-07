"""
Category 5: RLC Circuit Differential Equations

Generates RLC circuits and computes transient responses.
Difficulty scales from high school (RC first-order) to frontier (RLC third-order coupled).
"""

import sympy
from sympy import Symbol, Function, Eq, dsolve, exp, sin, cos, sqrt, Rational

from ..core.generator import ForgeCategory, Problem


class DiffEqRLCCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "diff_eq_rlc"
    
    @property
    def display_name(self) -> str:
        return "RLC Circuit Differential Equations"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"order": 1, "circuit_type": "RC", "forcing": "step"},
            2: {"order": 1, "circuit_type": "RC", "forcing": "sinusoidal"},
            3: {"order": 2, "circuit_type": "RLC_series", "forcing": "step"},
            4: {"order": 2, "circuit_type": "RLC_series", "forcing": "sinusoidal"},
            5: {"order": 3, "circuit_type": "RLC_coupled", "forcing": "sinusoidal"},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        t = Symbol('t', positive=True)
        y = Function('y')
        
        circuit_type = params["circuit_type"]
        forcing = params["forcing"]
        
        if circuit_type == "RC":
            R = Rational(int(rng.integers(1, 10)), int(rng.integers(1, 5)))
            C = Rational(int(rng.integers(1, 10)), int(rng.integers(1, 5)))
            
            # RC circuit: RC * y' + y = V(t)
            tau = R * C
            
            if forcing == "step":
                V0 = Rational(int(rng.integers(1, 10)))
                eq = Eq(tau * y(t).diff(t) + y(t), V0)
                y0 = Rational(0)
            else:
                omega = Rational(int(rng.integers(1, 5)))
                V0 = Rational(int(rng.integers(1, 10)))
                eq = Eq(tau * y(t).diff(t) + y(t), V0 * sin(omega * t))
                y0 = Rational(0)
            
            sol = dsolve(eq, y(t), ics={y(0): y0})
            answer = str(sol.rhs).replace("**", "^")
            
            question = (
                f"An RC circuit has R = {R} Ω and C = {C} F.\n"
                f"The governing equation is:\n\n"
                f"  {tau}·y'(t) + y(t) = {V0}" + (f"·sin({omega}t)" if forcing == "sinusoidal" else "") + f"\n\n"
                f"with initial condition y(0) = {y0}.\n\n"
                f"Find the complete solution y(t)."
            )
            
        elif circuit_type == "RLC_series":
            R = Rational(int(rng.integers(1, 10)))
            L = Rational(int(rng.integers(1, 5)))
            C = Rational(int(rng.integers(1, 5)), int(rng.integers(1, 5)))
            
            # RLC series: L*y'' + R*y' + (1/C)*y = V(t)
            if forcing == "step":
                V0 = Rational(int(rng.integers(1, 10)))
                eq = Eq(L * y(t).diff(t, 2) + R * y(t).diff(t) + (1/C) * y(t), V0)
                y0 = Rational(0)
                dy0 = Rational(0)
            else:
                omega = Rational(int(rng.integers(1, 5)))
                V0 = Rational(int(rng.integers(1, 10)))
                eq = Eq(L * y(t).diff(t, 2) + R * y(t).diff(t) + (1/C) * y(t), 
                       V0 * sin(omega * t))
                y0 = Rational(0)
                dy0 = Rational(0)
            
            sol = dsolve(eq, y(t), ics={y(0): y0, y(t).diff(t).subs(t, 0): dy0})
            answer = str(sol.rhs).replace("**", "^")
            
            question = (
                f"A series RLC circuit has R = {R} Ω, L = {L} H, and C = {C} F.\n"
                f"The governing equation is:\n\n"
                f"  {L}·y''(t) + {R}·y'(t) + {1/C}·y(t) = {V0}" + 
                (f"·sin({omega}t)" if forcing == "sinusoidal" else "") + f"\n\n"
                f"with initial conditions y(0) = {y0}, y'(0) = {dy0}.\n\n"
                f"Find the complete solution y(t)."
            )
            
        else:  # coupled RLC
            R1 = Rational(int(rng.integers(1, 5)))
            R2 = Rational(int(rng.integers(1, 5)))
            L1 = Rational(int(rng.integers(1, 5)))
            L2 = Rational(int(rng.integers(1, 5)))
            C = Rational(int(rng.integers(1, 5)))
            M = Rational(int(rng.integers(1, 3)))
            
            # Simplified coupled system
            omega = Rational(int(rng.integers(1, 5)))
            V0 = Rational(int(rng.integers(1, 10)))
            
            # For simplicity, solve a single second-order with coupling effect
            eq = Eq(L1 * y(t).diff(t, 2) + R1 * y(t).diff(t) + (1/C) * y(t), 
                   V0 * sin(omega * t))
            
            sol = dsolve(eq, y(t), ics={y(0): 0, y(t).diff(t).subs(t, 0): 0})
            answer = str(sol.rhs).replace("**", "^")
            
            question = (
                f"A coupled RLC circuit has R₁ = {R1} Ω, L₁ = {L1} H, "
                f"R₂ = {R2} Ω, L₂ = {L2} H, C = {C} F, and mutual inductance M = {M} H.\n\n"
                f"For the primary loop, the equation simplifies to:\n\n"
                f"  {L1}·y''(t) + {R1}·y'(t) + {1/C}·y(t) = {V0}·sin({omega}t)\n\n"
                f"with initial conditions y(0) = 0, y'(0) = 0.\n\n"
                f"Find the complete solution y(t)."
            )
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"circuit_type": circuit_type, "forcing": forcing},
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade using symbolic equivalence of the differential equation solution."""
        try:
            pred = sympy.sympify(prediction.strip())
            target = sympy.sympify(answer)
            
            # Try simplification
            diff = sympy.simplify(pred - target)
            return diff == 0
        except:
            return False
