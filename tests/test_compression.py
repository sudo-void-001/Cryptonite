"""
Comprehensive test suite for core.compression module.

Tests payload compression, zlib decompression, automated fallback logic,
level boundaries, and corrupted payload exception handling.
"""

import os

import pytest

from core.compression import (
    MAX_COMPRESSION_LEVEL,
    MIN_COMPRESSION_LEVEL,
    compress,
    decompress,
)


def test_compress_text_success():
    text_data = b"Cryptonite production-grade steganography system. " * 50
    compressed, was_compressed = compress(text_data)

    assert was_compressed is True
    assert len(compressed) < len(text_data)
    # Check reduction is greater than 20%
    reduction_pct = (1.0 - (len(compressed) / len(text_data))) * 100.0
    assert reduction_pct > 20.0

    decompressed = decompress(compressed, is_compressed=True)
    assert decompressed == text_data


def test_compress_random_data_fallback():
    # Incompressible high-entropy payload
    random_data = os.urandom(2048)
    result, was_compressed = compress(random_data)

    # Automated fallback kicks in
    assert was_compressed is False
    assert result == random_data

    # Decompression with is_compressed=False returns data intact
    decompressed = decompress(result, is_compressed=False)
    assert decompressed == random_data


def test_compress_empty_data():
    comp, was_comp = compress(b"")
    assert comp == b""
    assert was_comp is False

    decomp = decompress(b"", is_compressed=True)
    assert decomp == b""

    decomp_uncomp = decompress(b"", is_compressed=False)
    assert decomp_uncomp == b""


def test_compress_bytearray_input():
    data = bytearray(b"repetitive byte pattern " * 20)
    compressed, was_compressed = compress(data)
    assert was_compressed is True

    decompressed = decompress(compressed, is_compressed=True)
    assert decompressed == bytes(data)


def test_compress_invalid_types():
    with pytest.raises(TypeError, match="Data must be bytes"):
        compress("string_data")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Compression level must be an integer"):
        compress(b"valid_data", level="6")  # type: ignore[arg-type]


def test_compress_invalid_level_boundaries():
    data = b"some data to compress"
    with pytest.raises(ValueError, match="1-9"):
        compress(data, level=0)
    with pytest.raises(ValueError, match="1-9"):
        compress(data, level=10)
    with pytest.raises(ValueError, match="1-9"):
        compress(data, level=-1)


def test_compress_all_valid_levels():
    text_data = b"Testing multiple zlib compression levels. " * 30
    for lvl in range(MIN_COMPRESSION_LEVEL, MAX_COMPRESSION_LEVEL + 1):
        comp, was_comp = compress(text_data, level=lvl)
        assert was_comp is True
        decomp = decompress(comp, is_compressed=True)
        assert decomp == text_data


def test_decompress_invalid_types():
    with pytest.raises(TypeError, match="Data must be bytes"):
        decompress("not_bytes", is_compressed=True)  # type: ignore[arg-type]


def test_decompress_corrupted_data():
    corrupted_data = b"\x78\x9c\x00\x00\x00\xff\xff_corrupted_stream"
    with pytest.raises(ValueError, match="Decompression error"):
        decompress(corrupted_data, is_compressed=True)


def test_decompress_passthrough_when_not_compressed():
    arbitrary_bytes = b"\xde\xad\xbe\xef\x00\x01\x02"
    result = decompress(arbitrary_bytes, is_compressed=False)
    assert result == arbitrary_bytes


def test_compress_zlib_error_fallback(monkeypatch: pytest.MonkeyPatch):
    import zlib

    def mock_compress(data: bytes, level: int = 6):
        raise zlib.error("Mocked compression fault")

    monkeypatch.setattr(zlib, "compress", mock_compress)
    data = b"sample uncompressible fallback test"
    res, was_comp = compress(data)
    assert res == data
    assert was_comp is False
