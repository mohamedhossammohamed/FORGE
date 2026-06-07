"""
Category 19: Financial Mathematics

Generates continuous compound interest and option pricing problems.
Difficulty scales from high school (static rate) to frontier (Black-Scholes).
"""

import math
from fractions import Fraction

from ..core.generator import ForgeCategory, Problem


class FinanceMathCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "finance_math"
    
    @property
    def display_name(self) -> str:
        return "Financial Mathematics"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"compound_type": "simple", "time_range": (1, 10), "rate_range": (0.01, 0.10)},
            2: {"compound_type": "continuous", "time_range": (1, 10), "rate_range": (0.01, 0.10)},
            3: {"compound_type": "continuous", "time_range": (1, 20), "rate_range": (0.01, 0.15)},
            4: {"compound_type": "varying_rate", "time_range": (1, 10), "rate_range": (0.01, 0.20)},
            5: {"compound_type": "black_scholes", "time_range": (1, 5), "rate_range": (0.01, 0.30)},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        compound_type = params["compound_type"]
        
        if compound_type == "simple":
            # Simple compound interest: A = P(1 + r)^t
            P = int(rng.integers(1000, 100000))
            r = round(rng.uniform(*params["rate_range"]), 4)
            t = int(rng.integers(*params["time_range"]))
            
            A = P * (1 + r) ** t
            answer = round(A, 2)
            
            question = (
                f"Compute the future value of an investment with:\n\n"
                f"  Principal: ${P:,.2f}\n"
                f"  Annual interest rate: {r*100:.2f}%\n"
                f"  Time: {t} years\n"
                f"  Compounding: Annual\n\n"
                f"Provide your answer rounded to 2 decimal places."
            )
            
        elif compound_type == "continuous":
            # Continuous compounding: A = P * e^(rt)
            P = int(rng.integers(1000, 100000))
            r = round(rng.uniform(*params["rate_range"]), 4)
            t = int(rng.integers(*params["time_range"]))
            
            A = P * math.exp(r * t)
            answer = round(A, 2)
            
            question = (
                f"Compute the future value of an investment with:\n\n"
                f"  Principal: ${P:,.2f}\n"
                f"  Annual interest rate: {r*100:.2f}%\n"
                f"  Time: {t} years\n"
                f"  Compounding: Continuous\n\n"
                f"Formula: A = P · e^(rt)\n"
                f"Provide your answer rounded to 2 decimal places."
            )
            
        elif compound_type == "varying_rate":
            # Varying rate over time
            P = int(rng.integers(1000, 50000))
            n_periods = int(rng.integers(2, 5))
            rates = [round(rng.uniform(0.01, 0.15), 4) for _ in range(n_periods)]
            times = [int(rng.integers(1, 4)) for _ in range(n_periods)]
            
            A = P
            for r, t in zip(rates, times):
                A *= math.exp(r * t)
            
            answer = round(A, 2)
            
            rates_str = "\n".join(
                f"  Period {i+1}: {r*100:.2f}% for {t} years"
                for i, (r, t) in enumerate(zip(rates, times))
            )
            
            question = (
                f"Compute the future value of an investment with:\n\n"
                f"  Principal: ${P:,.2f}\n"
                f"  Continuous compounding with varying rates:\n"
                f"{rates_str}\n\n"
                f"Provide your answer rounded to 2 decimal places."
            )
            
        else:  # black_scholes
            # Simplified Black-Scholes call option price
            S = int(rng.integers(50, 200))  # Current stock price
            K = int(rng.integers(50, 200))  # Strike price
            T = round(rng.uniform(0.1, 2.0), 2)  # Time to expiration
            r = round(rng.uniform(0.01, 0.10), 4)  # Risk-free rate
            sigma = round(rng.uniform(0.10, 0.50), 4)  # Volatility
            
            # Black-Scholes formula
            d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            # Cumulative normal distribution
            from scipy.stats import norm
            N_d1 = norm.cdf(d1)
            N_d2 = norm.cdf(d2)
            
            C = S * N_d1 - K * math.exp(-r * T) * N_d2
            answer = round(C, 2)
            
            question = (
                f"Using the Black-Scholes model, compute the price of a European "
                f"call option with:\n\n"
                f"  Current stock price (S): ${S}\n"
                f"  Strike price (K): ${K}\n"
                f"  Time to expiration (T): {T} years\n"
                f"  Risk-free rate (r): {r*100:.2f}%\n"
                f"  Volatility (σ): {sigma*100:.2f}%\n\n"
                f"Formula: C = S·N(d₁) - K·e^(-rT)·N(d₂)\n"
                f"where d₁ = [ln(S/K) + (r + σ²/2)·T] / (σ·√T), d₂ = d₁ - σ·√T\n\n"
                f"Provide your answer rounded to 2 decimal places."
            )
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"compound_type": compound_type},
        )
    
    def grade(self, prediction: str, answer: float) -> bool:
        try:
            pred = prediction.strip().replace('$', '').replace(',', '')
            pred_float = float(pred)
            return abs(pred_float - answer) < 0.01
        except (ValueError, TypeError):
            return False
