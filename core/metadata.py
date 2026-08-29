"""
Cryptonite Lossless Metadata Sanitization Module.

Strips identifying EXIF/ID3/XMP tags without lossy re-encoding.
"""

import struct
import zlib
from pathlib import Path

PNG_SIGNATURE: bytes = b"\x89PNG\r\n\x1a\n"
CRITICAL_PNG_CHUNKS: frozenset[bytes] = frozenset(
    {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS"}
)

JPEG_SOI: bytes = b"\xff\xd8"
# Ancillary APP1-15 markers (EXIF, ICC, IPTC, Adobe, etc.) and COM (Comment)
JPEG_STRIP_MARKERS: frozenset[int] = frozenset(
    {
        0xE1,  # APP1 (EXIF / XMP)
        0xE2,  # APP2 (ICC Profile / FlashPix)
        0xE3,  # APP3
        0xE4,  # APP4
        0xE5,  # APP5
        0xE6,  # APP6
        0xE7,  # APP7
        0xE8,  # APP8
        0xE9,  # APP9
        0xEA,  # APP10
        0xEB,  # APP11
        0xEC,  # APP12 (Photoshop Ducky)
        0xED,  # APP13 (Photoshop IPTC)
        0xEE,  # APP14 (Adobe)
        0xEF,  # APP15
        0xFE,  # COM (Comment)
    }
)


def strip_png_metadata(image_input: str | Path | bytes | bytearray) -> bytes:
    """
    Remove all ancillary PNG chunks (tEXt, iTXt, zTXt, eXIf, tIME, pHYs, etc.)
    while strictly preserving critical chunks (IHDR, PLTE, IDAT, IEND) and
    transparency masks (tRNS).

    Args:
        image_input: File path (str or Path) or raw PNG bytes/bytearray.

    Returns:
        Sanitized PNG bytes containing only critical/transparency chunks.

    Raises:
        TypeError: If image_input is not a valid str, Path, bytes, or bytearray.
        FileNotFoundError: If a file path is passed but does not exist.
        ValueError: If data is not a valid PNG, has bad CRC, or is truncated.
    """
    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.is_file():
            raise FileNotFoundError(f"Carrier file not found: {image_input}")
        raw = path.read_bytes()
    elif isinstance(image_input, (bytes, bytearray)):
        raw = bytes(image_input)
    else:
        raise TypeError(
            f"image_input must be str, Path, bytes, or bytearray, got {type(image_input).__name__}"
        )

    if len(raw) < 8 or raw[:8] != PNG_SIGNATURE:
        raise ValueError("Invalid PNG file signature")

    output = bytearray(PNG_SIGNATURE)
    offset = 8
    raw_len = len(raw)
    raw_view = memoryview(raw)
    iend_found = False

    while offset < raw_len:
        if raw_len - offset < 12:
            raise ValueError("Truncated PNG chunk header")

        length = struct.unpack(">I", raw_view[offset : offset + 4])[0]
        chunk_type = bytes(raw_view[offset + 4 : offset + 8])
        chunk_total_len = 12 + length

        if offset + chunk_total_len > raw_len:
            type_str = chunk_type.decode("latin1", errors="replace")
            raise ValueError(f"Truncated PNG chunk data for {type_str}")

        chunk_data = raw_view[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(
            ">I", raw_view[offset + 8 + length : offset + chunk_total_len]
        )[0]
        computed_crc = zlib.crc32(chunk_data, zlib.crc32(chunk_type)) & 0xFFFFFFFF

        if stored_crc != computed_crc:
            type_str = chunk_type.decode("latin1", errors="replace")
            raise ValueError(f"CRC mismatch in PNG chunk {type_str}")

        if chunk_type in CRITICAL_PNG_CHUNKS:
            output.extend(raw_view[offset : offset + chunk_total_len])

        if chunk_type == b"IEND":
            iend_found = True
            break

        offset += chunk_total_len

    if not iend_found:
        raise ValueError("Missing IEND chunk in PNG stream")

    return bytes(output)


def strip_jpeg_metadata(image_input: str | Path | bytes | bytearray) -> bytes:
    """
    Losslessly remove all ancillary APP markers (APP1 EXIF, APP2 ICC, APP13 IPTC,
    APP14 Adobe) and COM comments from a JPEG byte stream.

    Operates purely at the binary stream level without re-encoding through PIL,
    preserving exact original DCT coefficients and image compression tables.

    Args:
        image_input: File path (str or Path) or raw JPEG bytes/bytearray.

    Returns:
        Sanitized JPEG bytes with all metadata stripped.

    Raises:
        TypeError: If image_input is not a valid str, Path, bytes, or bytearray.
        FileNotFoundError: If a file path is passed but does not exist.
        ValueError: If data is not a valid JPEG or is truncated.
    """
    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.is_file():
            raise FileNotFoundError(f"Carrier file not found: {image_input}")
        raw = path.read_bytes()
    elif isinstance(image_input, (bytes, bytearray)):
        raw = bytes(image_input)
    else:
        raise TypeError(
            f"image_input must be str, Path, bytes, or bytearray, got {type(image_input).__name__}"
        )

    if len(raw) < 4 or raw[:2] != JPEG_SOI:
        raise ValueError("Invalid JPEG file signature")

    raw_len = len(raw)
    raw_view = memoryview(raw)
    output = bytearray(JPEG_SOI)
    offset = 2
    eoi_found = False

    while offset < raw_len:
        if raw_view[offset] != 0xFF:
            offset += 1
            continue

        # Skip consecutive 0xFF fill bytes
        while offset < raw_len and raw_view[offset] == 0xFF:
            offset += 1

        if offset >= raw_len:
            break

        marker = raw_view[offset]
        offset += 1

        if marker == 0xD8:  # Embedded SOI
            continue

        if marker == 0xD9:  # EOI (End of Image)
            output.extend(b"\xff\xd9")
            eoi_found = True
            break

        if marker == 0xDA:  # SOS (Start of Scan)
            if offset + 2 > raw_len:
                raise ValueError("Truncated SOS marker in JPEG stream")
            output.extend(b"\xff\xda")
            output.extend(raw_view[offset:raw_len])
            eoi_found = True
            break

        # Standalone markers without payload (RST0-RST7, TEM)
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            output.extend(bytes([0xFF, marker]))
            continue

        # Variable-length markers with 2-byte big-endian length prefix
        if offset + 2 > raw_len:
            raise ValueError("Truncated marker length in JPEG stream")

        marker_length = struct.unpack(">H", raw_view[offset : offset + 2])[0]
        if offset + marker_length > raw_len:
            raise ValueError("Truncated marker payload in JPEG stream")

        if marker not in JPEG_STRIP_MARKERS:
            output.extend(bytes([0xFF, marker]))
            output.extend(raw_view[offset : offset + marker_length])

        offset += marker_length

    if not eoi_found:
        raise ValueError("Missing EOI marker in JPEG stream")

    return bytes(output)


def strip_mp3_metadata(audio_path: str) -> bytes:
    """
    Remove ID3v1, ID3v2, and APE tags from MP3 while preserving audio frame streams.
    """
    if not isinstance(audio_path, str):
        raise TypeError(f"audio_path must be str, got {type(audio_path).__name__}")
    raise NotImplementedError("Phase 4 implementation pending")
