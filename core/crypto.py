"""
Cryptonite Cryptography Module.

Handles AES-256-CBC encryption, Encrypt-then-MAC verification with HMAC-SHA256,
and key derivation via PBKDF2-HMAC-SHA256 (600,000 iterations).
"""

import hmac
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Constants
KEY_LEN = 32
SALT_LEN = 16
IV_LEN = 16
HMAC_LEN = 32
PBKDF2_ITERATIONS = 600_000
TOTAL_KDF_LEN = 96  # 32 (enc_key) + 32 (hmac_key) + 32 (prng_seed)


def derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes, bytes]:
    """
    Derive (enc_key, hmac_key, prng_seed) — each 32 bytes.
    Uses PBKDF2-HMAC-SHA256 with 600,000 iterations.

    Args:
        passphrase: The secret passphrase string.
        salt: A 16-byte random cryptographic salt.

    Returns:
        Tuple of (enc_key, hmac_key, prng_seed) each of length 32 bytes.

    Raises:
        ValueError: If passphrase is empty or salt is not 16 bytes.
    """
    if not isinstance(passphrase, str) or not passphrase:
        raise ValueError("Passphrase must be a non-empty string.")
    if not isinstance(salt, (bytes, bytearray)) or len(salt) != SALT_LEN:
        raise ValueError(f"Salt must be exactly {SALT_LEN} bytes.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=TOTAL_KDF_LEN,
        salt=bytes(salt),
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    key_material = kdf.derive(passphrase.encode("utf-8"))

    enc_key = key_material[0:32]
    hmac_key = key_material[32:64]
    prng_seed = key_material[64:96]

    return enc_key, hmac_key, prng_seed


def encrypt(plaintext: bytes, enc_key: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext with AES-256-CBC using PKCS7 padding.

    Args:
        plaintext: Raw data bytes to encrypt.
        enc_key: 32-byte AES-256 encryption key.

    Returns:
        Tuple of (iv: 16 bytes, ciphertext: bytes).

    Raises:
        ValueError: If enc_key is not 32 bytes or plaintext is invalid.
    """
    if not isinstance(enc_key, (bytes, bytearray)) or len(enc_key) != KEY_LEN:
        raise ValueError(f"Encryption key must be exactly {KEY_LEN} bytes.")
    if not isinstance(plaintext, (bytes, bytearray)):
        raise ValueError("Plaintext must be bytes.")

    iv = os.urandom(IV_LEN)

    # Apply PKCS7 padding (128-bit block size for AES)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    # AES-256-CBC encryption
    cipher = Cipher(algorithms.AES(bytes(enc_key)), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return iv, ciphertext


def compute_hmac(data: bytes, hmac_key: bytes) -> bytes:
    """
    Compute HMAC-SHA256 over data.

    Args:
        data: Arbitrary binary data to authenticate.
        hmac_key: 32-byte HMAC key.

    Returns:
        32-byte HMAC digest.

    Raises:
        ValueError: If hmac_key is not 32 bytes or data is invalid.
    """
    if not isinstance(hmac_key, (bytes, bytearray)) or len(hmac_key) != KEY_LEN:
        raise ValueError(f"HMAC key must be exactly {KEY_LEN} bytes.")
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("Data must be bytes.")

    return hmac.new(bytes(hmac_key), bytes(data), "sha256").digest()


def verify_and_decrypt(
    iv: bytes,
    ciphertext: bytes,
    enc_key: bytes,
    hmac_key: bytes,
    stored_mac: bytes,
) -> bytes:
    """
    Verify HMAC then decrypt ciphertext using AES-256-CBC (Encrypt-then-MAC).

    The HMAC covers iv + ciphertext to ensure complete ciphertext & IV integrity.

    Args:
        iv: 16-byte initialization vector.
        ciphertext: Encrypted ciphertext bytes.
        enc_key: 32-byte AES-256 encryption key.
        hmac_key: 32-byte HMAC key.
        stored_mac: 32-byte expected HMAC-SHA256 digest.

    Returns:
        Decrypted and unpadded plaintext bytes.

    Raises:
        ValueError: If MAC verification fails, parameters are malformed,
                    or padding is invalid.
    """
    if not isinstance(iv, (bytes, bytearray)) or len(iv) != IV_LEN:
        raise ValueError(f"IV must be exactly {IV_LEN} bytes.")
    if not isinstance(enc_key, (bytes, bytearray)) or len(enc_key) != KEY_LEN:
        raise ValueError(f"Encryption key must be exactly {KEY_LEN} bytes.")
    if not isinstance(hmac_key, (bytes, bytearray)) or len(hmac_key) != KEY_LEN:
        raise ValueError(f"HMAC key must be exactly {KEY_LEN} bytes.")
    if not isinstance(stored_mac, (bytes, bytearray)) or len(stored_mac) != HMAC_LEN:
        raise ValueError(f"Stored MAC must be exactly {HMAC_LEN} bytes.")
    if not isinstance(ciphertext, (bytes, bytearray)):
        raise ValueError("Ciphertext must be bytes.")

    # Encrypt-then-MAC verification over (iv + ciphertext)
    data_to_verify = bytes(iv) + bytes(ciphertext)
    calculated_mac = compute_hmac(data_to_verify, hmac_key)

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(calculated_mac, bytes(stored_mac)):
        raise ValueError("HMAC verification failed: ciphertext modified or invalid passphrase.")

    # AES-256-CBC decryption
    cipher = Cipher(algorithms.AES(bytes(enc_key)), modes.CBC(bytes(iv)), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(bytes(ciphertext)) + decryptor.finalize()

    # Remove PKCS7 padding
    try:
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
    except Exception as e:
        raise ValueError(f"Decryption padding error: {e}") from e

    return plaintext


def pack_encrypted_blob(
    salt: bytes,
    iv: bytes,
    hmac_digest: bytes,
    ciphertext: bytes,
) -> bytes:
    """
    Assemble encrypted blob format:
    [salt: 16B][iv: 16B][hmac: 32B][ciphertext: variable]
    """
    if len(salt) != SALT_LEN or len(iv) != IV_LEN or len(hmac_digest) != HMAC_LEN:
        raise ValueError("Invalid salt, IV, or HMAC length for encrypted blob packaging.")
    return bytes(salt) + bytes(iv) + bytes(hmac_digest) + bytes(ciphertext)


def unpack_encrypted_blob(blob: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    """
    Extract components from encrypted blob:
    [salt: 16B][iv: 16B][hmac: 32B][ciphertext: variable]
    """
    min_len = SALT_LEN + IV_LEN + HMAC_LEN
    if len(blob) < min_len:
        raise ValueError(f"Blob is too short ({len(blob)}B). Minimum required is {min_len}B.")

    salt = blob[0:SALT_LEN]
    iv = blob[SALT_LEN : SALT_LEN + IV_LEN]
    hmac_digest = blob[SALT_LEN + IV_LEN : SALT_LEN + IV_LEN + HMAC_LEN]
    ciphertext = blob[SALT_LEN + IV_LEN + HMAC_LEN :]

    return salt, iv, hmac_digest, ciphertext
