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
    iend_found = False

    while offset < raw_len:
        if raw_len - offset < 12:
            raise ValueError("Truncated PNG chunk header")

        length = struct.unpack(">I", raw[offset : offset + 4])[0]
        chunk_type = raw[offset + 4 : offset + 8]
        chunk_total_len = 12 + length

        if offset + chunk_total_len > raw_len:
            type_str = chunk_type.decode("latin1", errors="replace")
            raise ValueError(f"Truncated PNG chunk data for {type_str}")

        chunk_data = raw[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(
            ">I", raw[offset + 8 + length : offset + chunk_total_len]
        )[0]
        computed_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF

        if stored_crc != computed_crc:
            type_str = chunk_type.decode("latin1", errors="replace")
            raise ValueError(f"CRC mismatch in PNG chunk {type_str}")

        if chunk_type in CRITICAL_PNG_CHUNKS:
            output.extend(raw[offset : offset + chunk_total_len])

        if chunk_type == b"IEND":
            iend_found = True
            break

        offset += chunk_total_len

    if not iend_found:
        raise ValueError("Missing IEND chunk in PNG stream")

    return bytes(output)


def strip_jpeg_metadata(image_path: str) -> bytes:
    """
    Losslessly remove all APP markers (EXIF, IPTC, XMP) and COM comments from JPEG
    at the binary stream level. Never re-encodes through PIL.
    """
    if not isinstance(image_path, str):
        raise TypeError(f"image_path must be str, got {type(image_path).__name__}")
    raise NotImplementedError("Phase 3 implementation pending")


def strip_mp3_metadata(audio_path: str) -> bytes:
    """
    Remove ID3v1, ID3v2, and APE tags from MP3 while preserving audio frame streams.
    """
    if not isinstance(audio_path, str):
        raise TypeError(f"audio_path must be str, got {type(audio_path).__name__}")
    raise NotImplementedError("Phase 4 implementation pending")
