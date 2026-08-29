"""
Unit tests for Cryptonite JPEG Carrier module (Direct DCT Coefficient Manipulation).
"""

from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from core.carriers.base import BaseCarrier
from core.carriers.jpeg import (
    JpegCarrier,
    _block_dct_2d,
    _block_idct_2d,
    _get_eligible_ac_mask,
    _img_to_vectorized_blocks,
    _modify_coeff_sign_preserving,
    _modify_coeffs_vectorized,
    _vectorized_blocks_to_img,
)


def _create_test_jpeg(
    path: Path, size: tuple[int, int] = (64, 64), comment: str | None = None
) -> Path:
    """Helper to generate and save synthetic JPEG test images with high texture."""
    w, h = size
    # High entropy gradient texture to produce abundant non-zero AC coefficients
    x = np.linspace(0, 10 * np.pi, w)
    y = np.linspace(0, 10 * np.pi, h)
    xx, yy = np.meshgrid(x, y)
    r = (128 + 100 * np.sin(xx) * np.cos(yy)).astype(np.uint8)
    g = (128 + 100 * np.cos(xx) * np.sin(yy)).astype(np.uint8)
    b = (128 + 100 * np.sin(xx + yy)).astype(np.uint8)
    arr = np.stack([r, g, b], axis=-1)

    img = Image.fromarray(arr, mode="RGB")
    if comment:
        img.save(path, format="JPEG", quality=95, comment=comment)
    else:
        img.save(path, format="JPEG", quality=95)
    return path


@pytest.fixture
def jpeg_carrier() -> JpegCarrier:
    return JpegCarrier()


def test_jpeg_carrier_inheritance(jpeg_carrier: JpegCarrier):
    """Verify JpegCarrier subclasses BaseCarrier."""
    assert issubclass(JpegCarrier, BaseCarrier)
    assert isinstance(jpeg_carrier, BaseCarrier)


def test_dct_block_math_helpers():
    """Verify 2D DCT / IDCT roundtrip and coefficient modification properties."""
    block = np.random.uniform(-100, 100, (8, 8)).astype(np.float32)
    dct_b = _block_dct_2d(block)
    rec_b = _block_idct_2d(dct_b)
    assert np.allclose(block, rec_b, atol=1e-3)

    # Test mask excludes DC at (0, 0)
    arr = np.zeros((16, 16), dtype=np.int32)
    arr[0, 0] = 50  # DC block 0,0
    arr[0, 8] = 50  # DC block 0,1
    arr[0, 1] = 5  # AC block 0,0
    arr[1, 1] = -3  # AC block 0,0
    arr[2, 2] = 1  # AC low magnitude (<=1)
    arr[3, 3] = -1  # AC low magnitude (<=1)
    arr[4, 4] = 0  # AC zero

    mask = _get_eligible_ac_mask(arr)
    assert not mask[0, 0]
    assert not mask[0, 8]
    assert mask[0, 1]
    assert mask[1, 1]
    assert not mask[2, 2]
    assert not mask[3, 3]
    assert not mask[4, 4]

    # Test 3D batch mask
    arr_3d = np.zeros((4, 8, 8), dtype=np.int32)
    arr_3d[:, 0, 0] = 50  # DC
    arr_3d[:, 0, 1] = 5  # AC
    mask_3d = _get_eligible_ac_mask(arr_3d)
    assert not np.any(mask_3d[:, 0, 0])
    assert np.all(mask_3d[:, 0, 1])

    # Test invalid dimensions on mask
    with pytest.raises(ValueError, match="Expected 2D or 3D array"):
        _get_eligible_ac_mask(np.zeros(10))

    # Test scalar sign-preserving LSB flipping
    # Positive values:
    assert _modify_coeff_sign_preserving(2, 0) == 2
    assert _modify_coeff_sign_preserving(2, 1) == 3
    assert _modify_coeff_sign_preserving(3, 0) == 2
    assert _modify_coeff_sign_preserving(3, 1) == 3
    # Negative values:
    assert _modify_coeff_sign_preserving(-2, 0) == -2
    assert _modify_coeff_sign_preserving(-2, 1) == -3
    assert _modify_coeff_sign_preserving(-3, 0) == -2
    assert _modify_coeff_sign_preserving(-3, 1) == -3

    # Test vectorized sign-preserving LSB modification
    vals = np.array([2, 3, 5, 8, -2, -3, -5, -8], dtype=np.int32)
    bits = np.array([0, 1, 0, 1, 0, 1, 0, 1], dtype=np.uint8)
    mod_vals = _modify_coeffs_vectorized(vals, bits)
    assert np.array_equal(np.abs(mod_vals) & 1, bits)
    assert np.all(mod_vals[:4] > 0)
    assert np.all(mod_vals[4:] < 0)

    # Test vectorized block partition and reconstruction
    test_img = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8).astype(np.float32)
    blocks, hb, wb = _img_to_vectorized_blocks(test_img)
    assert blocks.shape == (3 * 4 * 4, 8, 8)
    rec_img = _vectorized_blocks_to_img(blocks, hb, wb)
    assert np.allclose(test_img, rec_img)


@pytest.mark.parametrize("payload_size", [0, 1, 8, 16, 32, 64])
def test_jpeg_embed_extract_roundtrip(
    tmp_path: Path, jpeg_carrier: JpegCarrier, payload_size: int
):
    """Test embed/extract roundtrip across multiple payload lengths."""
    cover_path = tmp_path / f"cover_{payload_size}.jpg"
    stego_path = tmp_path / f"stego_{payload_size}.jpg"
    _create_test_jpeg(cover_path, size=(64, 64))

    prng_seed = b"\x55" * 32
    payload = np.random.bytes(payload_size)

    stego_bytes = jpeg_carrier.embed(str(cover_path), payload, prng_seed)
    stego_path.write_bytes(stego_bytes)

    # Verify stego is valid JPEG
    reopened = Image.open(BytesIO(stego_bytes))
    assert reopened.format == "JPEG"

    extracted_payload = jpeg_carrier.extract(str(stego_path), prng_seed)
    assert extracted_payload == payload


def test_jpeg_capacity_and_overflow(tmp_path: Path, jpeg_carrier: JpegCarrier):
    """Verify capacity bounds and overflow exception."""
    cover_path = tmp_path / "cover_cap.jpg"
    _create_test_jpeg(cover_path, size=(64, 64))

    cap = jpeg_carrier.capacity(str(cover_path))
    assert cap > 0

    prng_seed = b"\x77" * 32
    # Exact fit payload
    stego_bytes = jpeg_carrier.embed(str(cover_path), b"\x00" * cap, prng_seed)
    assert len(stego_bytes) > 0

    # Overflow by 1 byte
    with pytest.raises(ValueError, match="exceeds carrier capacity"):
        jpeg_carrier.embed(str(cover_path), b"\x00" * (cap + 1), prng_seed)


def test_jpeg_wrong_seed_handling(tmp_path: Path, jpeg_carrier: JpegCarrier):
    """Verify wrong PRNG seed raises error or returns mismatched payload."""
    cover_path = tmp_path / "cover_wrong_seed.jpg"
    stego_path = tmp_path / "stego_wrong_seed.jpg"
    _create_test_jpeg(cover_path, size=(64, 64))

    correct_seed = b"\x11" * 32
    wrong_seed = b"\x22" * 32
    payload = b"Top secret DCT payload"

    stego_bytes = jpeg_carrier.embed(str(cover_path), payload, correct_seed)
    stego_path.write_bytes(stego_bytes)

    try:
        extracted = jpeg_carrier.extract(str(stego_path), wrong_seed)
        assert extracted != payload
    except ValueError:
        pass


def test_jpeg_error_handling(tmp_path: Path, jpeg_carrier: JpegCarrier):
    """Verify defensive input validation and exception types."""
    valid_path = tmp_path / "valid.jpg"
    _create_test_jpeg(valid_path, size=(32, 32))

    # File not found
    with pytest.raises(FileNotFoundError):
        jpeg_carrier.capacity("missing_carrier.jpg")
    with pytest.raises(FileNotFoundError):
        jpeg_carrier.embed("missing_carrier.jpg", b"data", b"seed" * 8)
    with pytest.raises(FileNotFoundError):
        jpeg_carrier.extract("missing_carrier.jpg", b"seed" * 8)

    # Invalid types
    with pytest.raises(TypeError):
        jpeg_carrier.capacity(12345)  # type: ignore
    with pytest.raises(TypeError):
        jpeg_carrier.embed(12345, b"data", b"seed" * 8)  # type: ignore
    with pytest.raises(TypeError):
        jpeg_carrier.embed(str(valid_path), "not_bytes", b"seed" * 8)  # type: ignore
    with pytest.raises(TypeError):
        jpeg_carrier.embed(str(valid_path), b"data", "not_bytes")  # type: ignore
    with pytest.raises(TypeError):
        jpeg_carrier.extract(12345, b"seed" * 8)  # type: ignore
    with pytest.raises(TypeError):
        jpeg_carrier.extract(str(valid_path), "not_bytes")  # type: ignore

    # Short seed
    with pytest.raises(ValueError, match="at least 16 bytes"):
        jpeg_carrier.embed(str(valid_path), b"data", b"short_seed")
    with pytest.raises(ValueError, match="at least 16 bytes"):
        jpeg_carrier.extract(str(valid_path), b"short_seed")


def test_jpeg_tiny_image_extract_insufficient_capacity(
    tmp_path: Path, jpeg_carrier: JpegCarrier
):
    """Test extract on image with insufficient DCT capacity raises ValueError."""
    tiny_path = tmp_path / "tiny.jpg"
    # Flat 8x8 image has almost zero AC coefficients
    img = Image.new("RGB", (8, 8), color=(128, 128, 128))
    img.save(tiny_path, format="JPEG")

    with pytest.raises(
        ValueError, match="does not have enough capacity for length header"
    ):
        jpeg_carrier.extract(str(tiny_path), b"\x00" * 32)


def test_jpegio_native_pathways_mocked(tmp_path: Path, monkeypatch):
    """Test the HAS_JPEGIO native C-extension execution pathways via mocking."""
    import core.carriers.jpeg as jpeg_mod

    class MockJpegObject:
        def __init__(self, coef_arrays):
            self.coef_arrays = coef_arrays

    # Build 16x16 block arrays with abundant AC coefficients
    base_arr = np.zeros((16, 16), dtype=np.int16)
    for r in range(16):
        for c in range(16):
            if not (r % 8 == 0 and c % 8 == 0):
                base_arr[r, c] = int(2 + ((r * 16 + c) % 5))

    class MockJpegio:
        @staticmethod
        def read(filepath):
            return MockJpegObject([base_arr.copy(), base_arr.copy(), base_arr.copy()])

        @staticmethod
        def write(cobj, filepath):
            img = Image.new("RGB", (16, 16), color=(100, 100, 100))
            img.save(filepath, format="JPEG")

    monkeypatch.setattr(jpeg_mod, "HAS_JPEGIO", True)
    monkeypatch.setattr(jpeg_mod, "jpegio", MockJpegio)

    carrier = jpeg_mod.JpegCarrier()
    carrier_file = tmp_path / "mock_carrier.jpg"
    _create_test_jpeg(carrier_file, size=(16, 16))

    # Test capacity calculation with HAS_JPEGIO
    cap = carrier.capacity(str(carrier_file))
    assert cap > 0

    # Test embed and overflow with HAS_JPEGIO
    prng_seed = b"\x33" * 32
    stego_bytes = carrier.embed(str(carrier_file), b"Hello", prng_seed)
    assert len(stego_bytes) > 0

    # Test overflow
    with pytest.raises(ValueError, match="exceeds carrier capacity"):
        carrier.embed(str(carrier_file), b"\x00" * (cap + 1), prng_seed)

    # Test extract with HAS_JPEGIO
    stego_file = tmp_path / "mock_stego.jpg"
    stego_file.write_bytes(stego_bytes)

    # State holding coefficients after embed
    saved_coefs = []

    class MockStegoJpegio:
        @staticmethod
        def read(filepath):
            if not saved_coefs:
                return MockJpegObject([base_arr.copy(), base_arr.copy(), base_arr.copy()])
            return MockJpegObject([c.copy() for c in saved_coefs])

        @staticmethod
        def write(cobj, filepath):
            nonlocal saved_coefs
            saved_coefs = [c.copy() for c in cobj.coef_arrays]
            img = Image.new("RGB", (16, 16), color=(100, 100, 100))
            img.save(filepath, format="JPEG")

    monkeypatch.setattr(jpeg_mod, "jpegio", MockStegoJpegio)
    carrier.embed(str(carrier_file), b"Hello Mocked Jpegio!", prng_seed)
    extracted = carrier.extract(str(stego_file), prng_seed)
    assert extracted == b"Hello Mocked Jpegio!"

    # Test extract with corrupted length header (> max_capacity)
    corrupted_coefs = [c.copy() for c in saved_coefs]
    # Invert bits to produce massive payload length
    corrupted_coefs[0][0, 1] = 3
    corrupted_coefs[0][0, 2] = 3

    class MockCorruptJpegio:
        @staticmethod
        def read(filepath):
            # Set all AC to 3 (LSB=1) so length = 0xFFFFFFFF > cap
            all_ones = base_arr.copy()
            all_ones[all_ones > 0] = 3
            all_ones[all_ones < 0] = -3
            return MockJpegObject([all_ones.copy(), all_ones.copy(), all_ones.copy()])

    monkeypatch.setattr(jpeg_mod, "jpegio", MockCorruptJpegio)
    with pytest.raises(ValueError, match="exceeds carrier capacity"):
        carrier.extract(str(stego_file), prng_seed)

    # Test extract insufficient capacity error with HAS_JPEGIO
    class MockTinyJpegio:
        @staticmethod
        def read(filepath):
            # All zeros -> 0 AC slots < 32
            return MockJpegObject([np.zeros((8, 8), dtype=np.int16)])

    monkeypatch.setattr(jpeg_mod, "jpegio", MockTinyJpegio)
    with pytest.raises(
        ValueError, match="does not have enough capacity for length header"
    ):
        carrier.extract(str(stego_file), prng_seed)


def test_jpeg_full_end_to_end_pipeline(tmp_path: Path, jpeg_carrier: JpegCarrier):
    """
    Test complete JPEG end-to-end pipeline:
    Payload -> Compress -> Pack -> Encrypt -> HMAC -> Embed in JPEG DCT ->
    Extract from JPEG -> Verify HMAC -> Decrypt -> Unpack -> Decompress -> Original
    """
    import os

    from core import compression, crypto, payload

    # 1. Setup cover carrier
    cover_path = tmp_path / "e2e_cover.jpg"
    stego_path = tmp_path / "e2e_stego.jpg"
    _create_test_jpeg(cover_path, size=(128, 128))

    # 2. Secret file data and passphrase
    secret_filename = "classified_jpeg_intel.txt"
    secret_data = (
        b"CONFIDENTIAL INTELLIGENCE TRANSMISSION:\n"
        + b"Surveillance drone payload secured at grid 48.8584N, 2.2945E.\n"
    )
    passphrase = "UltraSecureJpegPassphrase!2026#DCT"
    salt = os.urandom(16)

    # 3. Derive keys
    enc_key, hmac_key, prng_seed = crypto.derive_keys(passphrase, salt)

    # 4. Compress payload
    compressed_bytes, is_comp = compression.compress(secret_data, level=6)

    # 5. Pack framed binary header
    packed_payload = payload.pack(
        secret_filename, compressed_bytes, is_compressed=is_comp
    )

    # 6. Encrypt plaintext
    iv, ciphertext = crypto.encrypt(packed_payload, enc_key)

    # 7. Compute HMAC
    hmac_digest = crypto.compute_hmac(iv + ciphertext, hmac_key)

    # 8. Pack encrypted blob
    encrypted_blob = crypto.pack_encrypted_blob(
        salt, iv, hmac_digest, ciphertext
    )

    # 9. Embed into JPEG carrier
    stego_bytes = jpeg_carrier.embed(str(cover_path), encrypted_blob, prng_seed)
    stego_path.write_bytes(stego_bytes)

    # === EXTRACTION PATH ===

    # 10. Extract blob from stego JPEG
    extracted_blob = jpeg_carrier.extract(str(stego_path), prng_seed)
    assert extracted_blob == encrypted_blob

    # 11. Unpack blob
    ext_salt, ext_iv, ext_hmac, ext_ciphertext = crypto.unpack_encrypted_blob(
        extracted_blob
    )
    assert ext_salt == salt

    # 12. Re-derive keys and verify/decrypt
    d_enc, d_hmac, _ = crypto.derive_keys(passphrase, ext_salt)
    decrypted_packed = crypto.verify_and_decrypt(
        ext_iv, ext_ciphertext, d_enc, d_hmac, ext_hmac
    )

    # 13. Unpack payload header
    ext_filename, ext_compressed, ext_is_comp = payload.unpack(decrypted_packed)
    assert ext_filename == secret_filename
    assert ext_is_comp == is_comp

    # 14. Decompress payload
    recovered_data = compression.decompress(ext_compressed, ext_is_comp)
    assert recovered_data == secret_data



