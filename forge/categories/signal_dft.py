"""
Category 12: Signal Processing - DFT

Generates discrete time-domain signals and computes DFT.
Difficulty scales from undergraduate (N=4, real) to frontier (N=16, complex).
"""

import numpy as np
from fractions import Fraction

from ..core.generator import ForgeCategory, Problem


class SignalDFTCategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "signal_dft"
    
    @property
    def display_name(self) -> str:
        return "Signal Processing: DFT"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"n": 4, "use_complex": False, "magnitude": 10},
            2: {"n": 8, "use_complex": False, "magnitude": 10},
            3: {"n": 8, "use_complex": True, "magnitude": 10},
            4: {"n": 16, "use_complex": True, "magnitude": 20},
            5: {"n": 16, "use_complex": True, "magnitude": 50},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        n = params["n"]
        use_complex = params["use_complex"]
        magnitude = params["magnitude"]
        
        # Generate time-domain signal
        if use_complex:
            signal = np.array([
                complex(rng.integers(-magnitude, magnitude + 1),
                       rng.integers(-magnitude, magnitude + 1))
                for _ in range(n)
            ])
        else:
            signal = np.array([
                complex(rng.integers(-magnitude, magnitude + 1), 0)
                for _ in range(n)
            ])
        
        # Compute DFT
        dft_result = np.fft.fft(signal)
        
        # Format signal
        if use_complex:
            signal_str = "[" + ", ".join(
                f"{s.real:+.0f}{s.imag:+.0f}j" for s in signal
            ) + "]"
        else:
            signal_str = "[" + ", ".join(f"{s.real:.0f}" for s in signal) + "]"
        
        # Format DFT result (rounded for display)
        dft_str = "[" + ", ".join(
            f"{d.real:.4f}{d.imag:+.4f}j" for d in dft_result
        ) + "]"
        
        question = (
            f"Compute the Discrete Fourier Transform (DFT) of the following signal:\n\n"
            f"x = {signal_str}\n\n"
            f"The DFT is defined as X[k] = Σ x[n] · e^(-j·2π·k·n/N)\n\n"
            f"Provide the DFT coefficients as complex numbers rounded to 4 decimal places."
        )
        
        answer = dft_str
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={
                "signal": signal.tolist(),
                "dft": dft_result.tolist(),
                "n": n,
            },
        )
    
    def grade(self, prediction: str, answer: str) -> bool:
        """Grade using numpy.allclose with strict tolerance."""
        try:
            pred_array = self._parse_complex_array(prediction)
            ans_array = self._parse_complex_array(answer)
            
            if len(pred_array) != len(ans_array):
                return False
            
            return np.allclose(pred_array, ans_array, atol=1e-4)
        except:
            return False
    
    def _parse_complex_array(self, text: str) -> np.ndarray:
        """Parse a string representation of a complex array."""
        import re
        # Remove brackets
        text = text.strip().strip('[]')
        
        # Find all complex numbers
        pattern = r'([+-]?\d+\.?\d*)([+-]\d+\.?\d*)j'
        matches = re.findall(pattern, text)
        
        result = []
        for real_str, imag_str in matches:
            result.append(complex(float(real_str), float(imag_str)))
        
        return np.array(result)
