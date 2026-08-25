# Extras!          
The Stubs (core/crypto.py etc.)

Every module starts as a stub — function signatures, type hints, docstrings, but no implementation. This stops the AI from going off-spec on the interface design.

python
# core/crypto.py

from typing import tuple

def derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes, bytes]:
    """
    Derive three 32-byte keys from a passphrase and salt.
    
    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations.
    
    Returns:
        (enc_key, hmac_key, prng_seed) — each 32 bytes
    """
    raise NotImplementedError

def encrypt(plaintext: bytes, enc_key: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext with AES-256-CBC.
    
    Returns:
        (iv: 16 bytes, ciphertext: bytes)
    Raises:
        ValueError if enc_key is not 32 bytes
    """
    raise NotImplementedError

def verify_and_decrypt(iv: bytes, ciphertext: bytes, 
                       enc_key: bytes, hmac_key: bytes,
                       stored_mac: bytes) -> bytes:
    """
    Verify HMAC then decrypt. Raises ValueError on MAC failure.
    Encrypt-then-MAC: MAC covers the ciphertext, not plaintext.
    """
    raise NotImplementedError

Same pattern for every module. The AI fills in the raise NotImplementedError bodies. The interface never changes mid-project.