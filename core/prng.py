"""
Cryptonite CSPRNG Position Generation.

Generates cryptographically unpredictable index permutations using ChaCha20.
"""

from typing import List


def generate_permutation(seed: bytes, length: int) -> List[int]:
    """
    Generate a cryptographic permutation of indices [0, length).
    Uses ChaCha20 CSPRNG seeded with the given 32-byte seed.
    """
    raise NotImplementedError("Phase 1 implementation pending")
