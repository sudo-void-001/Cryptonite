"""
Unit tests for Cryptonite lossless metadata sanitization module.
"""

import struct
import zlib
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from core.metadata import (
    CRITICAL_PNG_CHUNKS,
    PNG_SIGNATURE,
    strip_jpeg_metadata,
    strip_mp3_metadata,
    strip_png_metadata,
)


def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Helper to build a valid PNG chunk with CRC."""
    length = len(data)
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", length) + chunk_type + data + struct.pack(">I", crc)


def _make_minimal_png() -> bytes:
    """Create raw binary bytes for a valid minimal 1x1 RGB PNG."""
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_strip_png_metadata_preserves_critical_and_trns(tmp_path: Path):
    """
    Verify that critical chunks (IHDR, PLTE, IDAT, IEND) and tRNS are preserved
    while ancillary chunks are stripped.
    """
    # Create image with ancillary chunks using PngInfo
    img = Image.new("RGBA", (10, 10), color=(100, 150, 200, 128))
    png_info = PngImagePlugin.PngInfo()
    png_info.add_text("Author", "TestUser")
    png_info.add_text("Comment", "Confidential EXIF data")
    png_info.add_text("Software", "Cryptonite Security Suite")

    img_path = tmp_path / "carrier_with_meta.png"
    img.save(img_path, format="PNG", pnginfo=png_info)

    # Add custom tRNS and custom ancillary chunks (tIME, pHYs, eXIf) manually
    raw = img_path.read_bytes()
    idx_iend = raw.rfind(b"IEND") - 4
    custom_ancillary = (
        _make_chunk(b"tIME", b"\x07\xe8\x01\x01\x00\x00\x00")
        + _make_chunk(b"pHYs", b"\x00\x00\x0e\xc4\x00\x00\x0e\xc4\x01")
        + _make_chunk(b"eXIf", b"II*\x00\x08\x00\x00\x00")
        + _make_chunk(b"tRNS", b"\x00\x00\x00\x00\x00\x00")
    )
    raw_with_extra = raw[:idx_iend] + custom_ancillary + raw[idx_iend:]
    img_path.write_bytes(raw_with_extra)

    sanitized_bytes = strip_png_metadata(str(img_path))
    assert sanitized_bytes.startswith(PNG_SIGNATURE)
    assert sanitized_bytes.endswith(_make_chunk(b"IEND", b""))

    # Parse chunks in sanitized output
    offset = 8
    found_chunks = []
    while offset < len(sanitized_bytes):
        length = struct.unpack(">I", sanitized_bytes[offset : offset + 4])[0]
        ctype = sanitized_bytes[offset + 4 : offset + 8]
        found_chunks.append(ctype)
        offset += 12 + length

    for c in found_chunks:
        assert c in CRITICAL_PNG_CHUNKS

    assert b"tEXt" not in found_chunks
    assert b"tIME" not in found_chunks
    assert b"pHYs" not in found_chunks
    assert b"eXIf" not in found_chunks
    assert b"tRNS" in found_chunks

    # Valid PNG image verification
    reopened = Image.open(BytesIO(sanitized_bytes))
    assert reopened.size == (10, 10)


def test_strip_png_metadata_direct_bytes_and_path(tmp_path: Path):
    """Test passing Path objects, str paths, bytes, and bytearrays."""
    raw_png = _make_minimal_png()
    file_path = tmp_path / "test.png"
    file_path.write_bytes(raw_png)

    res_str = strip_png_metadata(str(file_path))
    res_path = strip_png_metadata(file_path)
    res_bytes = strip_png_metadata(raw_png)
    res_bytearray = strip_png_metadata(bytearray(raw_png))

    assert res_str == res_path == res_bytes == res_bytearray


def test_strip_png_metadata_type_errors():
    """Test invalid input parameter types."""
    with pytest.raises(TypeError):
        strip_png_metadata(123)  # type: ignore
    with pytest.raises(TypeError):
        strip_png_metadata(None)  # type: ignore
    with pytest.raises(TypeError):
        strip_png_metadata({"key": "val"})  # type: ignore


def test_strip_png_metadata_file_not_found():
    """Test non-existent file path."""
    with pytest.raises(FileNotFoundError):
        strip_png_metadata("non_existent_image_12345.png")


def test_strip_png_metadata_invalid_signature():
    """Test data without valid 8-byte PNG signature."""
    with pytest.raises(ValueError, match="Invalid PNG file signature"):
        strip_png_metadata(b"SHORT")
    with pytest.raises(ValueError, match="Invalid PNG file signature"):
        strip_png_metadata(b"GIF89a" + b"\x00" * 20)


def test_strip_png_metadata_truncated_chunk_header():
    """Test truncated chunk header (less than 12 bytes remaining)."""
    raw = PNG_SIGNATURE + b"\x00\x00\x00"
    with pytest.raises(ValueError, match="Truncated PNG chunk header"):
        strip_png_metadata(raw)


def test_strip_png_metadata_truncated_chunk_data():
    """Test chunk declaring length greater than remaining data."""
    raw = PNG_SIGNATURE + struct.pack(">I", 50) + b"tEXt" + b"short data"
    with pytest.raises(ValueError, match="Truncated PNG chunk data"):
        strip_png_metadata(raw)


def test_strip_png_metadata_crc_mismatch():
    """Test corrupted CRC in chunk."""
    chunk = struct.pack(">I", 4) + b"tEXt" + b"data" + struct.pack(">I", 0x12345678)
    raw = PNG_SIGNATURE + chunk + _make_chunk(b"IEND", b"")
    with pytest.raises(ValueError, match="CRC mismatch"):
        strip_png_metadata(raw)


def test_strip_png_metadata_missing_iend():
    """Test PNG stream without terminating IEND chunk."""
    raw = PNG_SIGNATURE + _make_chunk(b"IHDR", b"\x00" * 13)
    with pytest.raises(ValueError, match="Missing IEND chunk"):
        strip_png_metadata(raw)


def test_strip_jpeg_metadata_stub():
    """Test JPEG metadata stripping stub function and validation."""
    with pytest.raises(NotImplementedError):
        strip_jpeg_metadata("cover.jpg")
    with pytest.raises(TypeError):
        strip_jpeg_metadata(123)  # type: ignore


def test_strip_mp3_metadata_stub():
    """Test MP3 metadata stripping stub function and validation."""
    with pytest.raises(NotImplementedError):
        strip_mp3_metadata("cover.mp3")
    with pytest.raises(TypeError):
        strip_mp3_metadata(123)  # type: ignore
