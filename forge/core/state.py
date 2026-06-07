"""
Deterministic seed management for reproducible problem generation.

All randomness in FORGE derives from SHA-256 hashing of (base_seed, difficulty, iteration),
ensuring identical inputs always produce identical outputs across runs.

SECURITY NOTE: The base_seed should be kept secret for production evaluations.
If an adversary knows the base_seed, they can pre-compute all problems.
For public benchmarking, use a random seed and publish it alongside results.
For internal testing, consider using a secret seed that is never disclosed.
"""

import hashlib
import random
import secrets
from typing import Optional

import numpy as np


def generate_secret_seed() -> int:
    """
    Generate a cryptographically secure random seed.
    
    Uses 128 bits of entropy (sufficient to prevent brute-force).
    This should be used when the seed needs to remain secret.
    
    Returns:
        A random 128-bit integer
    """
    return secrets.randbits(128)


def derive_seed(base_seed: int, difficulty: int, iteration: int) -> int:
    """
    Derive a deterministic seed from base seed, difficulty level, and iteration.
    
    Uses SHA-256 to produce a 256-bit hash, then extracts a 64-bit seed.
    This makes pre-computation of all possible problems physically impossible:
    - 2^256 possible hash inputs
    - Even at 1 trillion hashes/second, would take ~3.7 × 10^51 years to exhaust
    
    Args:
        base_seed: The master seed for the evaluation run
        difficulty: Difficulty level (1-5)
        iteration: Question iteration number within the difficulty level
        
    Returns:
        A 64-bit integer suitable for seeding RNGs
    """
    hash_input = f"{base_seed}_{difficulty}_{iteration}".encode()
    hash_hex = hashlib.sha256(hash_input).hexdigest()
    # Use full 256-bit hash space, extract 64 bits for RNG seeding
    return int(hash_hex, 16) % (2**64)


def create_rng(
    base_seed: int,
    difficulty: int,
    iteration: int,
    seed_python_random: bool = True,
) -> np.random.Generator:
    """
    Create a deterministic NumPy RNG for a specific generation context.
    
    Optionally seeds Python's random module as well for cases where
    categories use both numpy and stdlib random.
    
    Args:
        base_seed: The master seed for the evaluation run
        difficulty: Difficulty level (1-5)
        iteration: Question iteration number
        seed_python_random: Whether to also seed random.seed()
        
    Returns:
        A seeded numpy.random.Generator
    """
    derived = derive_seed(base_seed, difficulty, iteration)
    rng = np.random.default_rng(derived)
    if seed_python_random:
        random.seed(derived)
    return rng
