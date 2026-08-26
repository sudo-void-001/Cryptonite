"""
Payload Compression Module for Cryptonite Steganography.

Provides pre-encryption zlib compression with automated bypass fallback
when compressed payload size exceeds raw size.
"""

import zlib

DEFAULT_COMPRESSION_LEVEL = 6
MIN_COMPRESSION_LEVEL = 1
MAX_COMPRESSION_LEVEL = 9


def compress(data: bytes, level: int = DEFAULT_COMPRESSION_LEVEL) -> tuple[bytes, bool]:
    """
    Compress binary payload using standard zlib.

    If compression does not reduce payload size (e.g., already compressed or random data),
    it automatically falls back to raw data to save processing time and avoid unnecessary overhead.

    Args:
        data: Raw binary payload to compress.
        level: Compression level from 1 (fastest) to 9 (highest compression). Default is 6.

    Returns:
        Tuple of (result_bytes, was_compressed).
        - (compressed_bytes, True) if compression was beneficial.
        - (original_bytes, False) if compression was skipped or ineffective.

    Raises:
        TypeError: If data is not bytes-like or level is not an integer.
        ValueError: If level is outside the range [1, 9].
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Data must be bytes or bytearray.")
    if not isinstance(level, int):
        raise TypeError("Compression level must be an integer.")
    if not MIN_COMPRESSION_LEVEL <= level <= MAX_COMPRESSION_LEVEL:
        raise ValueError(
            f"Compression level must be {MIN_COMPRESSION_LEVEL}-{MAX_COMPRESSION_LEVEL}, "
            f"got {level}."
        )

    if not data:
        return b"", False

    try:
        compressed = zlib.compress(bytes(data), level=level)
    except zlib.error:
        return bytes(data), False

    # Fallback to uncompressed if compressed payload is larger than original
    if len(compressed) >= len(data):
        return bytes(data), False

    return compressed, True


def decompress(data: bytes, is_compressed: bool) -> bytes:
    """
    Decompress payload data if flagged as compressed.

    Args:
        data: Binary payload bytes.
        is_compressed: Boolean flag indicating if decompression is required.

    Returns:
        Decompressed original bytes.

    Raises:
        TypeError: If data is not bytes-like.
        ValueError: If decompressing corrupted data fails.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("Data must be bytes or bytearray.")

    if not is_compressed:
        return bytes(data)

    if not data:
        return b""

    try:
        return zlib.decompress(bytes(data))
    except zlib.error as e:
        raise ValueError(f"Decompression error: corrupted or invalid compressed stream: {e}") from e
