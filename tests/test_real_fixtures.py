"""
Real-world media fixture test suite for Cryptonite.

Tests all carriers and metadata sanitizers against real photographic images,
RGBA transparency graphics, EXIF-tagged JPEGs, and acoustic audio recordings.
"""

import os
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pydub import AudioSegment

from core import compression, crypto, payload
from core.carriers import JpegCarrier, Mp3Carrier, PngCarrier
from core.metadata import strip_jpeg_metadata, strip_mp3_metadata, strip_png_metadata

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_path() -> Path:
    """Return path to tests/fixtures directory, ensuring it exists."""
    assert FIXTURES_DIR.is_dir(), f"Fixtures directory not found: {FIXTURES_DIR}"
    return FIXTURES_DIR


# ---------------------------------------------------------------------------
# Real PNG Fixture Tests
# ---------------------------------------------------------------------------

def test_real_png_photographic_embed_extract(tmp_path: Path):
    """Test full adaptive LSB embed/extract on real photographic PNG (Hopper)."""
    cover_file = FIXTURES_DIR / "pillow_hopper.png"
    if not cover_file.is_file():
        pytest.skip("pillow_hopper.png fixture not available")

    stego_file = tmp_path / "stego_hopper.png"
    carrier = PngCarrier()

    cap = carrier.capacity(str(cover_file))
    assert cap > 500, f"Expected photographic PNG capacity > 500 bytes, got {cap}"

    prng_seed = b"\x42" * 32
    secret = b"Real-world photographic PNG steganography payload test."

    stego_bytes = carrier.embed(str(cover_file), secret, prng_seed)
    stego_file.write_bytes(stego_bytes)

    # Verify stego image format & dimensions
    stego_img = Image.open(stego_file)
    cover_img = Image.open(cover_file)
    assert stego_img.size == cover_img.size
    assert stego_img.format == "PNG"

    # Extract and verify bit-for-bit exact recovery
    extracted = carrier.extract(str(stego_file), prng_seed)
    assert extracted == secret


def test_real_png_alpha_channel_preservation(tmp_path: Path):
    """Verify that RGBA PNG transparency (wiki_alpha.png) is 100% preserved."""
    cover_file = FIXTURES_DIR / "wiki_alpha.png"
    if not cover_file.is_file():
        pytest.skip("wiki_alpha.png fixture not available")

    stego_file = tmp_path / "stego_alpha.png"
    carrier = PngCarrier()

    cap = carrier.capacity(str(cover_file))
    assert cap > 100

    prng_seed = b"\x7A" * 32
    secret = b"Preserve Alpha Channel Exactly"

    stego_bytes = carrier.embed(str(cover_file), secret, prng_seed)
    stego_file.write_bytes(stego_bytes)

    cover_img = Image.open(cover_file).convert("RGBA")
    stego_img = Image.open(stego_file).convert("RGBA")

    cover_alpha = np.array(cover_img)[:, :, 3]
    stego_alpha = np.array(stego_img)[:, :, 3]

    # Alpha channel must be completely untouched
    assert np.array_equal(cover_alpha, stego_alpha)

    # Extracted secret must match
    extracted = carrier.extract(str(stego_file), prng_seed)
    assert extracted == secret


def test_real_png_metadata_sanitization():
    """Verify that real PNGs pass strip_png_metadata losslessly."""
    cover_file = FIXTURES_DIR / "test_card.png"
    if not cover_file.is_file():
        pytest.skip("test_card.png fixture not available")

    raw_bytes = cover_file.read_bytes()
    sanitized = strip_png_metadata(raw_bytes)

    assert sanitized.startswith(b"\x89PNG\r\n\x1a\n")
    assert sanitized.endswith(b"IEND\xaeB`\x82")

    img = Image.open(BytesIO(sanitized))
    assert img.format == "PNG"


# ---------------------------------------------------------------------------
# Real JPEG Fixture Tests
# ---------------------------------------------------------------------------

def test_real_jpeg_exif_metadata_sanitization():
    """Verify that EXIF metadata is completely stripped from real JPEG (exif_gps.jpg)."""
    exif_file = FIXTURES_DIR / "exif_gps.jpg"
    if not exif_file.is_file():
        pytest.skip("exif_gps.jpg fixture not available")

    raw_bytes = exif_file.read_bytes()
    # Confirm raw file contains EXIF marker APP1 (0xFFE1)
    assert b"\xff\xe1" in raw_bytes

    sanitized = strip_jpeg_metadata(raw_bytes)
    assert sanitized.startswith(b"\xff\xd8")
    assert sanitized.endswith(b"\xff\xd9")
    # APP1 marker must be gone
    assert b"\xff\xe1" not in sanitized

    # Valid JPEG image still decodes
    reopened = Image.open(BytesIO(sanitized))
    assert reopened.format == "JPEG"


def test_real_jpeg_photographic_embed_extract(tmp_path: Path):
    """Test DCT coefficient steganography on real photographic JPEG (Hopper)."""
    cover_file = FIXTURES_DIR / "pillow_hopper.jpg"
    if not cover_file.is_file():
        pytest.skip("pillow_hopper.jpg fixture not available")

    stego_file = tmp_path / "stego_hopper.jpg"
    carrier = JpegCarrier()

    cap = carrier.capacity(str(cover_file))
    assert cap > 50, f"Expected JPEG capacity > 50 bytes, got {cap}"

    from core.carriers.jpeg import HAS_JPEGIO

    if HAS_JPEGIO:
        prng_seed = b"\x33" * 32
        secret = b"Real JPEG DCT Steganography"
        stego_bytes = carrier.embed(str(cover_file), secret, prng_seed)
        stego_file.write_bytes(stego_bytes)

        extracted = carrier.extract(str(stego_file), prng_seed)
        assert extracted == secret


# ---------------------------------------------------------------------------
# Real Audio WAV Fixture Tests
# ---------------------------------------------------------------------------

def test_real_audio_wav_embed_extract(tmp_path: Path):
    """Test acoustic echo hiding on real acoustic recording (acoustic_sample.wav)."""
    cover_file = FIXTURES_DIR / "acoustic_sample.wav"
    if not cover_file.is_file():
        pytest.skip("acoustic_sample.wav fixture not available")

    stego_file = tmp_path / "stego_acoustic.wav"
    carrier = Mp3Carrier()

    cap = carrier.capacity(str(cover_file))
    assert cap >= 10, f"Expected audio capacity >= 10 bytes, got {cap}"

    prng_seed = b"\x88" * 32
    secret = b"Acoustic Audio"

    assert len(secret) <= cap, f"Secret ({len(secret)}B) > cap ({cap}B)"

    stego_bytes = carrier.embed(str(cover_file), secret, prng_seed)
    stego_file.write_bytes(stego_bytes)

    # Audio format check
    audio = AudioSegment.from_file(str(stego_file))
    assert audio.frame_rate > 0
    assert audio.channels >= 1

    extracted = carrier.extract(str(stego_file), prng_seed)
    assert extracted == secret


def test_real_audio_metadata_sanitization():
    """Verify strip_mp3_metadata passes real WAV files cleanly."""
    cover_file = FIXTURES_DIR / "piano.wav"
    if not cover_file.is_file():
        pytest.skip("piano.wav fixture not available")

    raw_bytes = cover_file.read_bytes()
    sanitized = strip_mp3_metadata(raw_bytes)
    assert sanitized == raw_bytes
    assert sanitized.startswith(b"RIFF")


# ---------------------------------------------------------------------------
# Full End-to-End Cryptographic Integration with Real Fixtures
# ---------------------------------------------------------------------------

def test_full_pipeline_with_real_png_fixture(tmp_path: Path):
    """
    Complete real-world workflow:
    Raw document -> zlib compress -> binary pack -> AES-256-CBC encrypt ->
    HMAC-SHA256 authenticate -> Adaptive LSB embed in real PNG ->
    Extract from stego PNG -> Verify HMAC -> Decrypt -> Decompress -> Validate.
    """
    cover_file = FIXTURES_DIR / "sample_color.png"
    if not cover_file.is_file():
        pytest.skip("sample_color.png fixture not available")

    stego_file = tmp_path / "pipeline_stego.png"

    secret_data = (
        b"CONFIDENTIAL FORENSIC REPORT\n"
        b"Case: #CYBER-2026-X99\n"
        b"Evidence verified: PNG LSB Adaptive Scatter with ChaCha20 PRNG.\n"
    )
    secret_filename = "forensic_report.txt"
    passphrase = "RealWorldObsidianProtocol!2026"
    salt = os.urandom(16)

    # 1. Key Derivation (PBKDF2 600,000 iterations)
    enc_key, hmac_key, prng_seed = crypto.derive_keys(passphrase, salt)

    # 2. Compress & Pack
    compressed, is_comp = compression.compress(secret_data, level=6)
    packed = payload.pack(secret_filename, compressed, is_compressed=is_comp)

    # 3. Encrypt & Authenticate
    iv, ciphertext = crypto.encrypt(packed, enc_key)
    hmac_digest = crypto.compute_hmac(iv + ciphertext, hmac_key)
    encrypted_blob = crypto.pack_encrypted_blob(salt, iv, hmac_digest, ciphertext)

    # 4. Embed into real PNG
    carrier = PngCarrier()
    cap = carrier.capacity(str(cover_file))
    assert len(encrypted_blob) <= cap

    stego_bytes = carrier.embed(str(cover_file), encrypted_blob, prng_seed)
    stego_file.write_bytes(stego_bytes)

    # 5. Extract from stego PNG
    extracted_blob = carrier.extract(str(stego_file), prng_seed)
    assert extracted_blob == encrypted_blob

    # 6. Authenticate & Decrypt
    ext_salt, ext_iv, ext_hmac, ext_cipher = crypto.unpack_encrypted_blob(extracted_blob)
    d_enc, d_hmac, _ = crypto.derive_keys(passphrase, ext_salt)
    decrypted_packed = crypto.verify_and_decrypt(ext_iv, ext_cipher, d_enc, d_hmac, ext_hmac)

    # 7. Unpack & Decompress
    ext_fn, ext_comp, ext_is_comp = payload.unpack(decrypted_packed)
    recovered = compression.decompress(ext_comp, ext_is_comp)

    assert recovered == secret_data
    assert ext_fn == secret_filename
