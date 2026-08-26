"""
Payload Framing and Serialization Module for Cryptonite Steganography.

Encapsulates binary framing, magic byte verification, version flags,
and payload header packing/unpacking with strict bounds checking.
"""

import struct

# Binary header protocol constants
MAGIC: bytes = b"STGC"
VERSION: int = 1
MIN_HEADER_LEN: int = 15  # 4 (magic) + 1 (version) + 2 (fname_len) + 0 (fname) + 8 (size)
MAX_FILENAME_BYTES: int = 0xFFFF  # 65535 bytes (uint16)


def pack(filename: str, payload: bytes, is_compressed: bool = False) -> bytes:
    """
    Pack a filename and payload into the standard Cryptonite binary format:
    [magic: 4B "STGC"]
    [version: 1B] (bit 7: 1 if compressed, 0 if uncompressed; bits 0-6: version number)
    [filename_len: 2B big-endian uint16]
    [filename: NB UTF-8 encoded]
    [payload_size: 8B big-endian uint64]
    [payload_bytes: NB]

    Args:
        filename: Original filename to store in metadata.
        payload: Binary payload data.
        is_compressed: True if payload was compressed prior to packing.

    Returns:
        Framed bytes ready for encryption.

    Raises:
        ValueError: If filename is empty, payload is None, or filename exceeds 65535 bytes.
        TypeError: If types are invalid.
    """
    if not isinstance(filename, str):
        raise TypeError("Filename must be a string.")
    if not filename:
        raise ValueError("Filename cannot be empty.")
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError("Payload must be bytes or bytearray.")

    encoded_filename = filename.encode("utf-8")
    if len(encoded_filename) > MAX_FILENAME_BYTES:
        raise ValueError(
            f"Filename length ({len(encoded_filename)} bytes) exceeds maximum "
            f"supported header length ({MAX_FILENAME_BYTES} bytes)."
        )

    # Encode version byte: Bit 7 = compression flag, Bits 0-6 = version number (1)
    version_byte = (VERSION & 0x7F) | (0x80 if is_compressed else 0x00)

    header = struct.pack(
        f">4sBH{len(encoded_filename)}sQ",
        MAGIC,
        version_byte,
        len(encoded_filename),
        encoded_filename,
        len(payload),
    )

    return header + bytes(payload)


def unpack(data: bytes) -> tuple[str, bytes, bool]:
    """
    Unpack a Cryptonite binary framed structure into filename, payload, and compression flag.

    Args:
        data: Binary payload data to parse.

    Returns:
        Tuple of (filename: str, payload: bytes, is_compressed: bool).

    Raises:
        ValueError: If data is corrupted, truncated, invalid magic, or unsupported version.
        TypeError: If data is not bytes-like.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Data must be bytes or bytearray.")

    if len(data) < MIN_HEADER_LEN:
        msg = f"Data is too short ({len(data)}B) to contain a valid Cryptonite header"
        raise ValueError(f"{msg} (min {MIN_HEADER_LEN}B).")

    magic = bytes(data[0:4])
    if magic != MAGIC:
        raise ValueError(f"Invalid magic bytes in header: expected {MAGIC!r}, got {magic!r}.")

    version_byte = data[4]
    version_number = version_byte & 0x7F
    is_compressed = bool(version_byte & 0x80)

    if version_number != VERSION:
        raise ValueError(f"Unsupported Cryptonite version: {version_number} (expected {VERSION}).")

    filename_len = struct.unpack(">H", data[5:7])[0]

    header_required_len = 7 + filename_len + 8
    if len(data) < header_required_len:
        raise ValueError(
            f"Data truncated: header requires {header_required_len} bytes for filename and size, "
            f"but only {len(data)} bytes available."
        )

    filename_bytes = data[7 : 7 + filename_len]
    try:
        filename = filename_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"Filename in header is not valid UTF-8: {e}") from e

    payload_size_offset = 7 + filename_len
    payload_size = struct.unpack(">Q", data[payload_size_offset : payload_size_offset + 8])[0]

    payload_offset = payload_size_offset + 8
    if len(data) < payload_offset + payload_size:
        raise ValueError(
            f"Data truncated: payload requires {payload_size} bytes, "
            f"but only {len(data) - payload_offset} bytes remain."
        )

    payload = bytes(data[payload_offset : payload_offset + payload_size])

    return filename, payload, is_compressed


def calculate_overhead(filename: str) -> int:
    """
    Calculate the exact byte overhead added by the frame header for a given filename.

    Formula: 4 (magic) + 1 (version) + 2 (fname_len uint16) + len(fname_utf8) + 8 (size uint64)

    Args:
        filename: Filename string.

    Returns:
        Overhead size in bytes.
    """
    if not isinstance(filename, str):
        raise TypeError("Filename must be a string.")
    return 4 + 1 + 2 + len(filename.encode("utf-8")) + 8
