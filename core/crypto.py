"""
Cryptonite Cryptography Module.

Handles AES-256-CBC encryption, Encrypt-then-MAC verification with HMAC-SHA256,
and key derivation via PBKDF2-HMAC-SHA256 (600,000 iterations).
"""

from typing import Tuple


def derive_keys(passphrase: str, salt: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Derive (enc_key, hmac_key, prng_seed) — each 32 bytes.
    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations.
    """
    raise NotImplementedError("Phase 1 implementation pending")


def encrypt(plaintext: bytes, enc_key: bytes) -> Tuple[bytes, bytes]:
    """
    AES-256-CBC encrypt. Returns (iv: 16B, ciphertext).
    Raises ValueError if enc_key is not 32 bytes.
    """
    raise NotImplementedError("Phase 1 implementation pending")


def compute_hmac(data: bytes, hmac_key: bytes) -> bytes:
    """
    Compute HMAC-SHA256 over data. Returns 32-byte MAC.
    """
    raise NotImplementedError("Phase 1 implementation pending")


def verify_and_decrypt(
    iv: bytes,
    ciphertext: bytes,
    enc_key: bytes,
    hmac_key: bytes,
    stored_mac: bytes,
) -> bytes:
    """
    Verify HMAC then decrypt. Encrypt-then-MAC.
    Raises ValueError on MAC failure or bad key length.
    Uses hmac.compare_digest for constant-time comparison.
    """
    raise NotImplementedError("Phase 1 implementation pending")
