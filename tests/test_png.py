"""
Unit tests for Cryptonite PNG Carrier module (Adaptive LSB).
"""

from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as compute_psnr
from skimage.metrics import structural_similarity as compute_ssim

from core.carriers.base import BaseCarrier
from core.carriers.png import (
    PngCarrier,
    _build_embedding_slots,
    _compute_msb_gradient,
)


def _create_test_image(
    path: Path, size: tuple[int, int] = (64, 64), mode: str = "RGB"
) -> Path:
    """Helper to generate and save synthetic test images."""
    w, h = size
    if mode == "RGB":
        arr = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGB")
    elif mode == "RGBA":
        arr = np.random.randint(0, 256, (h, w, 4), dtype=np.uint8)
        # Set varied alpha channel
        arr[:, :, 3] = np.linspace(50, 255, w, dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
    elif mode == "L":
        arr = np.random.randint(0, 256, (h, w), dtype=np.uint8)
        img = Image.fromarray(arr, mode="L")
    elif mode == "LA":
        arr = np.random.randint(0, 256, (h, w, 2), dtype=np.uint8)
        img = Image.fromarray(arr, mode="LA")
    elif mode == "1":
        arr = np.random.choice([0, 255], size=(h, w)).astype(np.uint8)
        img = Image.fromarray(arr, mode="L").convert("1")
    elif mode == "P":
        arr = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGB").quantize(colors=64)
    else:
        raise ValueError(f"Unsupported test mode: {mode}")

    img.save(path, format="PNG")
    return path


@pytest.fixture
def png_carrier() -> PngCarrier:
    return PngCarrier()


def test_png_carrier_inheritance(png_carrier: PngCarrier):
    """Verify that PngCarrier correctly subclasses BaseCarrier."""
    assert issubclass(PngCarrier, BaseCarrier)
    assert isinstance(png_carrier, BaseCarrier)


@pytest.mark.parametrize("payload_size", [0, 1, 15, 16, 17, 128, 512, 1024])
def test_png_embed_extract_roundtrip_rgb(
    tmp_path: Path, png_carrier: PngCarrier, payload_size: int
):
    """Test full embed and extract roundtrip across various payload lengths in RGB mode."""
    cover_path = tmp_path / f"cover_rgb_{payload_size}.png"
    stego_path = tmp_path / f"stego_rgb_{payload_size}.png"
    _create_test_image(cover_path, size=(64, 64), mode="RGB")

    prng_seed = b"\x01" * 32
    payload = np.random.bytes(payload_size)

    stego_bytes = png_carrier.embed(str(cover_path), payload, prng_seed)
    stego_path.write_bytes(stego_bytes)

    extracted_payload = png_carrier.extract(str(stego_path), prng_seed)
    assert extracted_payload == payload


def test_png_embed_extract_rgba_preserves_alpha(
    tmp_path: Path, png_carrier: PngCarrier
):
    """Verify RGBA stego extraction and verify Alpha channel is 100% unaltered."""
    cover_path = tmp_path / "cover_rgba.png"
    stego_path = tmp_path / "stego_rgba.png"
    _create_test_image(cover_path, size=(50, 50), mode="RGBA")

    cover_img = Image.open(cover_path)
    cover_alpha = np.array(cover_img)[:, :, 3]

    prng_seed = b"\xa5" * 32
    payload = b"Top secret payload inside transparent PNG!"

    stego_bytes = png_carrier.embed(str(cover_path), payload, prng_seed)
    stego_path.write_bytes(stego_bytes)

    extracted = png_carrier.extract(str(stego_path), prng_seed)
    assert extracted == payload

    stego_img = Image.open(stego_path)
    stego_alpha = np.array(stego_img)[:, :, 3]
    assert np.array_equal(cover_alpha, stego_alpha)


def test_png_embed_extract_grayscale_and_la(
    tmp_path: Path, png_carrier: PngCarrier
):
    """Test Grayscale (L) and Grayscale+Alpha (LA) image carriers."""
    for mode in ["L", "LA", "1"]:
        cover_path = tmp_path / f"cover_{mode}.png"
        stego_path = tmp_path / f"stego_{mode}.png"
        _create_test_image(cover_path, size=(40, 40), mode=mode)

        prng_seed = b"\x42" * 32
        payload = f"Payload for {mode} image".encode()

        stego_bytes = png_carrier.embed(str(cover_path), payload, prng_seed)
        stego_path.write_bytes(stego_bytes)

        extracted = png_carrier.extract(str(stego_path), prng_seed)
        assert extracted == payload


def test_png_embed_extract_palette_mode(
    tmp_path: Path, png_carrier: PngCarrier
):
    """Test Palette (P) mode images convert and embed safely."""
    cover_path = tmp_path / "cover_p.png"
    stego_path = tmp_path / "stego_p.png"
    _create_test_image(cover_path, size=(48, 48), mode="P")

    prng_seed = b"\x77" * 32
    payload = b"Palette mode payload data test"

    stego_bytes = png_carrier.embed(str(cover_path), payload, prng_seed)
    stego_path.write_bytes(stego_bytes)

    extracted = png_carrier.extract(str(stego_path), prng_seed)
    assert extracted == payload


def test_png_capacity_and_overflow(tmp_path: Path, png_carrier: PngCarrier):
    """Verify capacity bounds checking."""
    cover_path = tmp_path / "cover_cap.png"
    _create_test_image(cover_path, size=(32, 32), mode="RGB")

    cap = png_carrier.capacity(str(cover_path))
    assert cap > 0

    prng_seed = b"\x99" * 32
    # Exact capacity payload
    fit_payload = b"\x00" * cap
    stego_bytes = png_carrier.embed(str(cover_path), fit_payload, prng_seed)
    assert len(stego_bytes) > 0

    # Overflow by 1 byte
    overflow_payload = b"\x00" * (cap + 1)
    with pytest.raises(ValueError, match="exceeds carrier capacity"):
        png_carrier.embed(str(cover_path), overflow_payload, prng_seed)


def test_png_perceptual_quality_psnr_and_ssim(
    tmp_path: Path, png_carrier: PngCarrier
):
    """Verify stego image achieves PSNR > 40 dB and SSIM > 0.99."""
    cover_path = tmp_path / "cover_quality.png"
    stego_path = tmp_path / "stego_quality.png"
    _create_test_image(cover_path, size=(100, 100), mode="RGB")

    cover_arr = np.array(Image.open(cover_path))
    payload = np.random.bytes(1000)
    prng_seed = b"\xee" * 32

    stego_bytes = png_carrier.embed(str(cover_path), payload, prng_seed)
    stego_path.write_bytes(stego_bytes)

    stego_arr = np.array(Image.open(stego_path))

    psnr_val = compute_psnr(cover_arr, stego_arr)
    ssim_val = compute_ssim(cover_arr, stego_arr, channel_axis=2)

    assert psnr_val >= 40.0, f"PSNR too low: {psnr_val} dB"
    assert ssim_val >= 0.99, f"SSIM too low: {ssim_val}"


def test_png_wrong_seed_or_corrupted_data(
    tmp_path: Path, png_carrier: PngCarrier
):
    """Verify wrong extraction seed raises ValueError or returns mismatched data."""
    cover_path = tmp_path / "cover_seed.png"
    stego_path = tmp_path / "stego_seed.png"
    _create_test_image(cover_path, size=(64, 64), mode="RGB")

    correct_seed = b"\x11" * 32
    wrong_seed = b"\x22" * 32
    payload = b"Secret data to protect"

    stego_bytes = png_carrier.embed(str(cover_path), payload, correct_seed)
    stego_path.write_bytes(stego_bytes)

    try:
        extracted = png_carrier.extract(str(stego_path), wrong_seed)
        assert extracted != payload
    except ValueError:
        # Length header mismatch check caught corruption
        pass


def test_png_error_handling(tmp_path: Path, png_carrier: PngCarrier):
    """Test input validation and error raises for invalid arguments."""
    valid_img = tmp_path / "valid.png"
    _create_test_image(valid_img, size=(16, 16), mode="RGB")

    # File not found
    with pytest.raises(FileNotFoundError):
        png_carrier.capacity("non_existent_image.png")
    with pytest.raises(FileNotFoundError):
        png_carrier.embed("non_existent_image.png", b"data", b"seed" * 8)
    with pytest.raises(FileNotFoundError):
        png_carrier.extract("non_existent_image.png", b"seed" * 8)

    # Invalid argument types
    with pytest.raises(TypeError):
        png_carrier.capacity(123)  # type: ignore
    with pytest.raises(TypeError):
        png_carrier.embed(123, b"data", b"seed" * 8)  # type: ignore
    with pytest.raises(TypeError):
        png_carrier.embed(str(valid_img), "not_bytes", b"seed" * 8)  # type: ignore
    with pytest.raises(TypeError):
        png_carrier.embed(str(valid_img), b"data", "not_bytes")  # type: ignore
    with pytest.raises(TypeError):
        png_carrier.extract(123, b"seed" * 8)  # type: ignore
    with pytest.raises(TypeError):
        png_carrier.extract(str(valid_img), "not_bytes")  # type: ignore

    # Short seed
    with pytest.raises(ValueError, match="at least 16 bytes"):
        png_carrier.embed(str(valid_img), b"data", b"short_seed")
    with pytest.raises(ValueError, match="at least 16 bytes"):
        png_carrier.extract(str(valid_img), b"short_seed")


def test_png_texture_adaptation():
    """Verify that textured regions allocate more bits than smooth regions."""
    # Create image with smooth left half and edge/textured right half
    h, w = 32, 32
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    # Right half checkerboard edges
    arr[:, w // 2 :, :] = (
        np.indices((h, w // 2)).sum(axis=0)[:, :, np.newaxis] % 2
    ) * 255

    grad = _compute_msb_gradient(arr, embed_channels=3)
    flat_indices, bit_offsets, total_bits = _build_embedding_slots(
        arr.shape, 3, grad
    )

    # Gradient in textured area should be much higher than in smooth area
    assert np.mean(grad[:, w // 2 :]) > np.mean(grad[:, : w // 2])
    assert total_bits > h * w * 3  # More than 1 bit/channel in total


def test_png_load_image_array_modes_and_types(tmp_path: Path):
    """Test _load_image_array with bytes, bytearray, CMYK mode fallback, and invalid types."""
    from core.carriers.png import _load_image_array

    # Test with bytes and bytearray
    raw_png = (tmp_path / "sample.png")
    _create_test_image(raw_png, size=(10, 10), mode="RGB")
    bytes_data = raw_png.read_bytes()

    _, arr_bytes, ch_bytes = _load_image_array(bytes_data)
    _, arr_ba, ch_ba = _load_image_array(bytearray(bytes_data))
    assert ch_bytes == 3 and ch_ba == 3
    assert np.array_equal(arr_bytes, arr_ba)

    # Test invalid type
    with pytest.raises(TypeError):
        _load_image_array(12345)  # type: ignore

    # Test CMYK fallback to RGB
    cmyk_img = Image.new("CMYK", (10, 10), color=(10, 20, 30, 40))
    cmyk_buf = BytesIO()
    cmyk_img.save(cmyk_buf, format="JPEG")
    _, arr_cmyk, ch_cmyk = _load_image_array(cmyk_buf.getvalue())
    assert ch_cmyk == 3
    assert arr_cmyk.shape == (10, 10, 3)


def test_png_extract_tiny_image_insufficient_capacity(
    tmp_path: Path, png_carrier: PngCarrier
):
    """Test extract on an image with less than 32 total embeddable bits raises ValueError."""
    tiny_path = tmp_path / "tiny.png"
    # 2x2 grayscale image = 4 pixels * 1 bit = 4 bits < 32 bits
    img = Image.new("L", (2, 2), color=128)
    img.save(tiny_path, format="PNG")

    with pytest.raises(
        ValueError, match="does not have enough capacity for length header"
    ):
        png_carrier.extract(str(tiny_path), b"\x00" * 32)


def test_png_full_end_to_end_pipeline(tmp_path: Path, png_carrier: PngCarrier):
    """
    Test complete end-to-end pipeline:
    Payload -> Compress -> Pack -> Encrypt -> HMAC -> Embed in PNG ->
    Extract from PNG -> Verify HMAC -> Decrypt -> Unpack -> Decompress -> Original
    """
    import os

    from core import compression, crypto, payload

    # 1. Setup cover carrier
    cover_path = tmp_path / "e2e_cover.png"
    stego_path = tmp_path / "e2e_stego.png"
    _create_test_image(cover_path, size=(128, 128), mode="RGB")

    # 2. Secret file data and passphrase
    secret_filename = "classified_report.txt"
    secret_data = (
        b"Top Secret Intelligence Report:\n"
        + b"Target coordinates confirmed at 37.7749N, 122.4194W.\n" * 20
    )
    passphrase = "UltraSecurePassphrase!2026#Cryptonite"
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

    # 9. Embed into PNG carrier
    stego_bytes = png_carrier.embed(str(cover_path), encrypted_blob, prng_seed)
    stego_path.write_bytes(stego_bytes)

    # === EXTRACTION PATH ===

    # 10. Extract blob from stego PNG
    extracted_blob = png_carrier.extract(str(stego_path), prng_seed)
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


