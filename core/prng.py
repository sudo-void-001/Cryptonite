"""
Pseudorandom number generator (PRNG) module for Cryptonite.

Provides cryptographically secure, deterministic index permutations
using ChaCha20 as a CSPRNG for steganographic position scattering.
"""

import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms


def generate_permutation(seed: bytes, length: int) -> list[int]:
    """
    Generate a cryptographically secure deterministic permutation of indices [0, length).

    Uses a ChaCha20 CSPRNG keystream to drive a Fisher-Yates (Knuth) shuffle,
    guaranteeing uniform random distribution without modulo bias or external dependencies.

    Args:
        seed: Exactly 32 bytes of cryptographically derived seed.
        length: Number of indices to permute (must be positive integer).

    Returns:
        A list of integers from 0 to length - 1 in pseudo-randomly permuted order.

    Raises:
        ValueError: If seed length is not 32 bytes or length is <= 0.
        TypeError: If seed is not bytes-like or length is not an int.
    """
    if not isinstance(seed, (bytes, bytearray)):
        raise TypeError("Seed must be bytes or bytearray.")
    if len(seed) != 32:
        raise ValueError(f"Seed must be exactly 32 bytes, got {len(seed)}.")
    if not isinstance(length, int):
        raise TypeError("Length must be an integer.")
    if length <= 0:
        raise ValueError(f"Length must be a positive integer, got {length}.")

    if length == 1:
        return [0]

    # Initialize ChaCha20 with the 32-byte seed and a fixed 16-byte zero nonce.
    # The nonce is fixed because each seed is unique per (passphrase + random salt).
    nonce = b"\x00" * 16
    algorithm = algorithms.ChaCha20(bytes(seed), nonce)
    cipher = Cipher(algorithm, mode=None)
    encryptor = cipher.encryptor()

    steps = length - 1
    bytes_needed = steps * 4

    # Generate the pseudorandom stream via keystream encryption of zeros
    zero_stream = b"\x00" * bytes_needed
    prng_stream = encryptor.update(zero_stream)

    # Bulk unpack 32-bit big-endian integers in a single native C-call
    values = struct.unpack(f">{steps}I", prng_stream)

    # In-place Fisher-Yates shuffle
    positions = list(range(length))
    for i, val in zip(range(length - 1, 0, -1), values, strict=True):
        j = val % (i + 1)
        positions[i], positions[j] = positions[j], positions[i]

    return positions
