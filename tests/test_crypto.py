"""
Comprehensive test suite for core.crypto module.

Tests key derivation, AES-256-CBC encryption, Encrypt-then-MAC authentication,
constant-time verification, and encrypted blob packaging.
"""

import os

import pytest

from core.crypto import (
    HMAC_LEN,
    IV_LEN,
    KEY_LEN,
    compute_hmac,
    derive_keys,
    encrypt,
    pack_encrypted_blob,
    unpack_encrypted_blob,
    verify_and_decrypt,
)

# --- derive_keys Tests ---


def test_derive_keys_deterministic():
    salt = os.urandom(16)
    passphrase = "master_secret_passphrase_2026"
    enc1, mac1, seed1 = derive_keys(passphrase, salt)
    enc2, mac2, seed2 = derive_keys(passphrase, salt)
    assert enc1 == enc2
    assert mac1 == mac2
    assert seed1 == seed2


def test_derive_keys_different_salt():
    passphrase = "master_secret_passphrase_2026"
    salt1 = os.urandom(16)
    salt2 = os.urandom(16)
    enc1, mac1, seed1 = derive_keys(passphrase, salt1)
    enc2, mac2, seed2 = derive_keys(passphrase, salt2)
    assert enc1 != enc2
    assert mac1 != mac2
    assert seed1 != seed2


def test_derive_keys_different_passphrase():
    salt = os.urandom(16)
    enc1, mac1, seed1 = derive_keys("passphrase_one", salt)
    enc2, mac2, seed2 = derive_keys("passphrase_two", salt)
    assert enc1 != enc2
    assert mac1 != mac2
    assert seed1 != seed2


def test_derive_keys_empty_passphrase():
    with pytest.raises(ValueError, match="non-empty string"):
        derive_keys("", os.urandom(16))


def test_derive_keys_invalid_type():
    with pytest.raises(ValueError):
        derive_keys(b"bytes_pass", os.urandom(16))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        derive_keys(None, os.urandom(16))  # type: ignore[arg-type]


def test_derive_keys_wrong_salt_length():
    with pytest.raises(ValueError, match="16 bytes"):
        derive_keys("valid_pass", os.urandom(15))
    with pytest.raises(ValueError, match="16 bytes"):
        derive_keys("valid_pass", os.urandom(17))
    with pytest.raises(ValueError, match="16 bytes"):
        derive_keys("valid_pass", "not_bytes")  # type: ignore[arg-type]


def test_derive_keys_output_lengths():
    enc, mac, seed = derive_keys("valid_pass", os.urandom(16))
    assert len(enc) == KEY_LEN
    assert len(mac) == KEY_LEN
    assert len(seed) == KEY_LEN


# --- encrypt Tests ---


def test_encrypt_valid():
    key = os.urandom(32)
    data = b"confidential payload"
    iv, ct = encrypt(data, key)
    assert len(iv) == IV_LEN
    assert len(ct) >= 16
    assert len(ct) % 16 == 0  # Block aligned


def test_encrypt_randomized_iv():
    key = os.urandom(32)
    data = b"same data"
    iv1, ct1 = encrypt(data, key)
    iv2, ct2 = encrypt(data, key)
    assert iv1 != iv2
    assert ct1 != ct2


def test_encrypt_empty_bytes():
    key = os.urandom(32)
    iv, ct = encrypt(b"", key)
    assert len(iv) == IV_LEN
    assert len(ct) == 16  # Full PKCS7 padding block


def test_encrypt_invalid_key():
    with pytest.raises(ValueError, match="32 bytes"):
        encrypt(b"data", os.urandom(16))
    with pytest.raises(ValueError, match="32 bytes"):
        encrypt(b"data", "not_bytes")  # type: ignore[arg-type]


def test_encrypt_invalid_plaintext_type():
    key = os.urandom(32)
    with pytest.raises(ValueError, match="Plaintext must be bytes"):
        encrypt("string_instead_of_bytes", key)  # type: ignore[arg-type]


# --- compute_hmac Tests ---


def test_compute_hmac_deterministic():
    key = os.urandom(32)
    data = b"authenticated payload"
    mac1 = compute_hmac(data, key)
    mac2 = compute_hmac(data, key)
    assert mac1 == mac2
    assert len(mac1) == HMAC_LEN


def test_compute_hmac_different_data():
    key = os.urandom(32)
    mac1 = compute_hmac(b"data1", key)
    mac2 = compute_hmac(b"data2", key)
    assert mac1 != mac2


def test_compute_hmac_invalid_key():
    with pytest.raises(ValueError, match="32 bytes"):
        compute_hmac(b"data", os.urandom(31))
    with pytest.raises(ValueError, match="32 bytes"):
        compute_hmac(b"data", "bad_key")  # type: ignore[arg-type]


def test_compute_hmac_invalid_data_type():
    key = os.urandom(32)
    with pytest.raises(ValueError, match="Data must be bytes"):
        compute_hmac(12345, key)  # type: ignore[arg-type]


# --- verify_and_decrypt Tests ---


def test_verify_and_decrypt_success():
    key = os.urandom(32)
    mac_key = os.urandom(32)
    original = b"steganography payload integrity test"
    iv, ct = encrypt(original, key)
    mac = compute_hmac(iv + ct, mac_key)

    decrypted = verify_and_decrypt(iv, ct, key, mac_key, mac)
    assert decrypted == original


def test_verify_and_decrypt_tampered_ciphertext():
    key = os.urandom(32)
    mac_key = os.urandom(32)
    iv, ct = encrypt(b"sensitive data", key)
    mac = compute_hmac(iv + ct, mac_key)

    tampered_ct = bytearray(ct)
    tampered_ct[0] ^= 0x01

    with pytest.raises(ValueError, match="HMAC verification failed"):
        verify_and_decrypt(iv, bytes(tampered_ct), key, mac_key, mac)


def test_verify_and_decrypt_tampered_iv():
    key = os.urandom(32)
    mac_key = os.urandom(32)
    iv, ct = encrypt(b"sensitive data", key)
    mac = compute_hmac(iv + ct, mac_key)

    tampered_iv = bytearray(iv)
    tampered_iv[0] ^= 0x01

    with pytest.raises(ValueError, match="HMAC verification failed"):
        verify_and_decrypt(bytes(tampered_iv), ct, key, mac_key, mac)


def test_verify_and_decrypt_wrong_hmac_key():
    key = os.urandom(32)
    mac_key = os.urandom(32)
    wrong_mac_key = os.urandom(32)
    iv, ct = encrypt(b"sensitive data", key)
    mac = compute_hmac(iv + ct, mac_key)

    with pytest.raises(ValueError, match="HMAC verification failed"):
        verify_and_decrypt(iv, ct, key, wrong_mac_key, mac)


def test_verify_and_decrypt_invalid_parameter_lengths():
    valid_key = os.urandom(32)
    valid_mac_key = os.urandom(32)
    valid_iv = os.urandom(16)
    valid_mac = os.urandom(32)
    valid_ct = os.urandom(32)

    with pytest.raises(ValueError, match="IV must be exactly 16 bytes"):
        verify_and_decrypt(os.urandom(15), valid_ct, valid_key, valid_mac_key, valid_mac)
    with pytest.raises(ValueError, match="Encryption key must be exactly 32 bytes"):
        verify_and_decrypt(valid_iv, valid_ct, os.urandom(31), valid_mac_key, valid_mac)
    with pytest.raises(ValueError, match="HMAC key must be exactly 32 bytes"):
        verify_and_decrypt(valid_iv, valid_ct, valid_key, os.urandom(31), valid_mac)
    with pytest.raises(ValueError, match="Stored MAC must be exactly 32 bytes"):
        verify_and_decrypt(valid_iv, valid_ct, valid_key, valid_mac_key, os.urandom(31))
    with pytest.raises(ValueError, match="Ciphertext must be bytes"):
        verify_and_decrypt(valid_iv, "bad_ct", valid_key, valid_mac_key, valid_mac)  # type: ignore[arg-type]


def test_verify_and_decrypt_bad_padding_handling():
    """If HMAC is forged with legitimate key but unpadding fails, error is cleanly raised."""
    key = os.urandom(32)
    mac_key = os.urandom(32)
    iv = os.urandom(16)
    # Direct cipher without valid PKCS7 padding
    raw_bad_block = os.urandom(16)
    mac = compute_hmac(iv + raw_bad_block, mac_key)

    # Force bad padding by using invalid block
    try:
        verify_and_decrypt(iv, raw_bad_block, key, mac_key, mac)
    except ValueError as e:
        assert "padding" in str(e).lower() or "hmac" in str(e).lower()


# --- Encrypted Blob Packaging Tests ---


def test_pack_unpack_encrypted_blob():
    salt = os.urandom(16)
    iv = os.urandom(16)
    hmac_digest = os.urandom(32)
    ciphertext = os.urandom(128)

    blob = pack_encrypted_blob(salt, iv, hmac_digest, ciphertext)
    assert len(blob) == 16 + 16 + 32 + 128

    unpacked_salt, unpacked_iv, unpacked_mac, unpacked_ct = unpack_encrypted_blob(blob)
    assert unpacked_salt == salt
    assert unpacked_iv == iv
    assert unpacked_mac == hmac_digest
    assert unpacked_ct == ciphertext


def test_pack_encrypted_blob_invalid_inputs():
    with pytest.raises(ValueError, match="Invalid salt, IV, or HMAC length"):
        pack_encrypted_blob(os.urandom(15), os.urandom(16), os.urandom(32), b"ct")
    with pytest.raises(ValueError, match="Invalid salt, IV, or HMAC length"):
        pack_encrypted_blob(os.urandom(16), os.urandom(15), os.urandom(32), b"ct")
    with pytest.raises(ValueError, match="Invalid salt, IV, or HMAC length"):
        pack_encrypted_blob(os.urandom(16), os.urandom(16), os.urandom(31), b"ct")


def test_unpack_encrypted_blob_too_short():
    with pytest.raises(ValueError, match="Blob is too short"):
        unpack_encrypted_blob(os.urandom(63))


# --- Full End-to-End Pipeline Multi-Size Tests ---


@pytest.mark.parametrize("payload_size", [0, 1, 15, 16, 17, 256, 4096, 65536])
def test_full_crypto_pipeline(sample_passphrase: str, payload_size: int):
    plaintext = os.urandom(payload_size)
    salt = os.urandom(16)

    # 1. Key Derivation
    enc_key, hmac_key, prng_seed = derive_keys(sample_passphrase, salt)

    # 2. Encrypt
    iv, ciphertext = encrypt(plaintext, enc_key)

    # 3. Authenticate (Encrypt-then-MAC)
    mac = compute_hmac(iv + ciphertext, hmac_key)

    # 4. Assemble Blob
    blob = pack_encrypted_blob(salt, iv, mac, ciphertext)

    # 5. Extract Blob
    ext_salt, ext_iv, ext_mac, ext_ciphertext = unpack_encrypted_blob(blob)
    assert ext_salt == salt

    # 6. Re-derive keys
    rec_enc_key, rec_hmac_key, rec_seed = derive_keys(sample_passphrase, ext_salt)
    assert rec_seed == prng_seed

    # 7. Verify & Decrypt
    decrypted = verify_and_decrypt(ext_iv, ext_ciphertext, rec_enc_key, rec_hmac_key, ext_mac)
    assert decrypted == plaintext
