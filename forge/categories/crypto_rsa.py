"""
Category 9: Cryptographic Arithmetic (RSA)

Generates prime pairs and computes RSA keys.
Difficulty scales from undergraduate (8-bit) to frontier (32-bit primes).
"""

import sympy
from sympy import gcd, mod_inverse, isprime

from ..core.generator import ForgeCategory, Problem


class CryptoRSACategory(ForgeCategory):
    
    @property
    def name(self) -> str:
        return "crypto_rsa"
    
    @property
    def display_name(self) -> str:
        return "Cryptographic Arithmetic (RSA)"
    
    def get_difficulty_params(self, difficulty: int) -> dict:
        params = {
            1: {"bit_length": 4, "e": 3},
            2: {"bit_length": 8, "e": 17},
            3: {"bit_length": 16, "e": 65537},
            4: {"bit_length": 24, "e": 65537},
            5: {"bit_length": 32, "e": 65537},
        }
        return params.get(difficulty, params[3])
    
    def generate(self, difficulty: int, iteration: int) -> Problem:
        rng = self.get_rng(difficulty, iteration)
        params = self.get_difficulty_params(difficulty)
        
        bit_length = params["bit_length"]
        e = params["e"]
        
        # Generate two distinct primes
        low = 2 ** (bit_length - 1)
        high = 2 ** bit_length
        
        p = int(rng.integers(low, high))
        while not isprime(p):
            p += 1
        
        q = int(rng.integers(low, high))
        while not isprime(q) or q == p:
            q += 1
        
        # RSA computation
        n = p * q
        phi_n = (p - 1) * (q - 1)
        
        # Ensure e is coprime to phi_n
        while gcd(e, phi_n) != 1:
            e += 2
        
        # Compute private key d
        d = mod_inverse(e, phi_n)
        
        # Verify
        assert (e * d) % phi_n == 1
        
        question = (
            f"In RSA cryptography, given:\n\n"
            f"  p = {p}\n"
            f"  q = {q}\n"
            f"  e = {e}\n\n"
            f"Compute the private key d such that e·d ≡ 1 (mod φ(n)) "
            f"where n = p·q and φ(n) = (p-1)(q-1).\n\n"
            f"Provide the exact integer value of d."
        )
        
        answer = d
        
        return Problem(
            question=question,
            answer=answer,
            category=self.name,
            difficulty=difficulty,
            iteration=iteration,
            seed=self.base_seed,
            metadata={"p": p, "q": q, "n": n, "e": e, "d": d, "phi_n": phi_n},
        )
    
    def grade(self, prediction: str, answer: int) -> bool:
        """Grade by checking if d satisfies e*d ≡ 1 (mod phi_n)."""
        try:
            d_pred = int(prediction.strip().replace(',', '').replace(' ', ''))
            
            # We need to verify against the metadata
            # For now, check exact match
            return d_pred == int(answer)
        except (ValueError, TypeError):
            return False
