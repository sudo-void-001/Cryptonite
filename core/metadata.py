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


def strip_mp3_metadata(audio_input: str | Path | bytes | bytearray) -> bytes:
    """
    Losslessly remove ID3v2 header tags, ID3v1 trailer tags, and APE footer tags
    from an MP3 or WAV audio byte stream. Preserves all raw MPEG audio frames intact.

    Supports WAV RIFF streams transparently (pass-through; WAV has no ID3 tags).

    Args:
        audio_input: File path (str or Path) or raw audio bytes/bytearray.

    Returns:
        Sanitized audio bytes with all metadata tags removed.

    Raises:
        TypeError: If audio_input is not a valid str, Path, bytes, or bytearray.
        FileNotFoundError: If a file path is passed but does not exist.
        ValueError: If the data is empty, or has a corrupted ID3v2 synchsafe header.
    """
    if isinstance(audio_input, (str, Path)):
        path = Path(audio_input)
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_input}")
        raw = path.read_bytes()
    elif isinstance(audio_input, (bytes, bytearray)):
        raw = bytes(audio_input)
    else:
        raise TypeError(
            f"audio_input must be str, Path, bytes, or bytearray, "
            f"got {type(audio_input).__name__}"
        )

    if len(raw) == 0:
        raise ValueError("Audio data is empty")

    raw_view = memoryview(raw)
    offset = 0
    raw_len = len(raw)

    # WAV / RIFF pass-through: WAV files have no ID3 tags; return as-is
    if raw_len >= 4 and raw[:4] == b"RIFF":
        return bytes(raw)

    # --- Strip leading ID3v2 tag(s) ---
    # ID3v2 structure: b"ID3" [major] [minor] [flags] [s0 s1 s2 s3] <payload>
    # Size is a 28-bit synchsafe big-endian integer (each byte uses only 7 bits).
    while offset + 10 <= raw_len and raw_view[offset : offset + 3] == b"ID3":
        flags = raw_view[offset + 5]
        s0 = raw_view[offset + 6]
        s1 = raw_view[offset + 7]
        s2 = raw_view[offset + 8]
        s3 = raw_view[offset + 9]

        # Validate synchsafe integers (each byte must be < 128)
        if any(b > 127 for b in (s0, s1, s2, s3)):
            raise ValueError(
                "Corrupted ID3v2 tag: invalid synchsafe integer (byte >= 128)"
            )

        tag_size = (s0 << 21) | (s1 << 14) | (s2 << 7) | s3
        # 0x10 flag = footer present (10-byte echo of header at end of tag)
        has_footer = bool(flags & 0x10)
        total_tag_len = 10 + tag_size + (10 if has_footer else 0)

        if offset + total_tag_len > raw_len:
            # Truncated ID3v2 tag — strip whatever we can and stop
            offset = raw_len
            break

        offset += total_tag_len

    # Audio frames begin here
    audio_data = bytearray(raw_view[offset:raw_len])

    # Strip trailing tags iteratively — APE first (it wraps ID3v1), then ID3v1.
    # Loop handles any combination of APE + ID3v1 trailing tags.
    prev_len = -1
    while len(audio_data) != prev_len:
        prev_len = len(audio_data)

        # --- Strip trailing APE tag (32-byte footer starting with "APETAGEX") ---
        if len(audio_data) >= 32 and audio_data[-32:-24] == b"APETAGEX":
            # APE footer: preamble(8)+version(4)+size(4)+count(4)+flags(4)+reserved(8)
            ape_size = struct.unpack_from("<I", audio_data, len(audio_data) - 32 + 12)[0]
            total_ape = ape_size + 32
            if total_ape <= len(audio_data):
                audio_data = audio_data[: len(audio_data) - total_ape]

        # --- Strip trailing ID3v1 tag (fixed 128 bytes starting with "TAG") ---
        if len(audio_data) >= 128 and audio_data[-128:-125] == b"TAG":
            audio_data = audio_data[:-128]

    if len(audio_data) == 0:
        raise ValueError("No audio data remains after stripping all metadata tags")

    return bytes(audio_data)
