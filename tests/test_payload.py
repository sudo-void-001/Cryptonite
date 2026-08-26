"""
Comprehensive test suite for core.payload module.

Tests payload framing, binary header parsing, versioning & bit 7 flags,
overhead calculations, and defensive boundary validations.
"""

import os
import struct

import pytest

from core.payload import (
    MAGIC,
    MAX_FILENAME_BYTES,
    VERSION,
    calculate_overhead,
    pack,
    unpack,
)


def test_pack_unpack_roundtrip_uncompressed():
    filename = "document.pdf"
    payload = b"Secret payload content with binary \x00\xff\xfe\x01 bytes."
    packed = pack(filename, payload, is_compressed=False)

    rec_fname, rec_payload, rec_compressed = unpack(packed)
    assert rec_fname == filename
    assert rec_payload == payload
    assert rec_compressed is False


def test_pack_unpack_roundtrip_compressed():
    filename = "archive.tar"
    payload = b"Compressed stream bytes simulation"
    packed = pack(filename, payload, is_compressed=True)

    rec_fname, rec_payload, rec_compressed = unpack(packed)
    assert rec_fname == filename
    assert rec_payload == payload
    assert rec_compressed is True


def test_pack_invalid_inputs():
    with pytest.raises(ValueError, match="Filename cannot be empty"):
        pack("", b"payload")
    with pytest.raises(TypeError, match="Filename must be a string"):
        pack(12345, b"payload")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Payload must be bytes"):
        pack("valid.txt", "not_bytes")  # type: ignore[arg-type]


def test_pack_filename_too_long():
    long_filename = "a" * (MAX_FILENAME_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds maximum"):
        pack(long_filename, b"data")


def test_unpack_invalid_types_and_lengths():
    with pytest.raises(TypeError, match="Data must be bytes"):
        unpack("not_bytes")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="too short"):
        unpack(b"short")


def test_unpack_invalid_magic():
    packed = pack("file.txt", b"payload")
    tampered_magic = b"XXXX" + packed[4:]
    with pytest.raises(ValueError, match="Invalid magic bytes"):
        unpack(tampered_magic)


def test_unpack_unsupported_version():
    packed = pack("file.txt", b"payload")
    # Modify version number to 5
    tampered_version = packed[:4] + bytes([5]) + packed[5:]
    with pytest.raises(ValueError, match="Unsupported Cryptonite version"):
        unpack(tampered_version)


def test_unpack_truncated_header_short_data():
    packed = pack("file.txt", b"payload")
    with pytest.raises(ValueError, match="too short"):
        unpack(packed[:10])


def test_unpack_truncated_header_mid_stream():
    # Length >= 15 but shorter than filename + payload size header
    long_name = "a" * 20
    packed = pack(long_name, b"payload")
    with pytest.raises(ValueError, match="Data truncated: header requires"):
        unpack(packed[:20])


def test_unpack_truncated_payload():
    packed = pack("file.txt", b"payload_bytes_here")
    with pytest.raises(ValueError, match="Data truncated: payload requires"):
        unpack(packed[:-4])


def test_unpack_invalid_utf8_filename():
    # Build raw frame with invalid UTF-8 bytes in filename
    invalid_utf8 = b"\xff\xfe\xfd"
    header = struct.pack(
        f">4sBH{len(invalid_utf8)}sQ",
        MAGIC,
        VERSION,
        len(invalid_utf8),
        invalid_utf8,
        10,
    )
    raw_data = header + b"1234567890"

    with pytest.raises(ValueError, match="not valid UTF-8"):
        unpack(raw_data)


def test_calculate_overhead():
    assert calculate_overhead("a.txt") == 4 + 1 + 2 + 5 + 8
    expected = 4 + 1 + 2 + len("longer_filename.tar.gz") + 8
    assert calculate_overhead("longer_filename.tar.gz") == expected
    with pytest.raises(TypeError, match="Filename must be a string"):
        calculate_overhead(123)  # type: ignore[arg-type]


def test_unicode_filenames_and_large_payloads():
    unicode_names = ["秘密_secret.txt", "données_sécurisées.dat", "🔐_crypto.key"]
    large_payload = os.urandom(1024 * 512)  # 512 KB

    for name in unicode_names:
        packed = pack(name, large_payload, is_compressed=True)
        rec_name, rec_payload, rec_comp = unpack(packed)
        assert rec_name == name
        assert rec_payload == large_payload
        assert rec_comp is True
