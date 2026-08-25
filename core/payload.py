"""
Cryptonite Payload Packing & Unpacking Module.

Encapsulates binary framing, magic byte validation, versioning,
and capacity calculation.
"""

from typing import Tuple

MAGIC: bytes = b"STGC"
VERSION: int = 1


def pack(filename: str, payload: bytes, is_compressed: bool = False) -> bytes:
    """
    Pack payload with header:
    [magic: 4B "STGC"]
    [version: 1B] (bit 7: 1 if compressed, 0 if uncompressed; bits 0-6: version number)
    [filename_len: 2B (big-endian uint16)]
    [filename: NB (UTF-8)]
    [payload_size: 8B (big-endian uint64)]
    [payload_bytes: NB]
    """
    raise NotImplementedError("Phase 1 implementation pending")


def unpack(data: bytes) -> Tuple[str, bytes, bool]:
    """
    Unpack header, returning (filename, payload_bytes, is_compressed).
    Raises ValueError on invalid magic, unsupported version, or truncated data.
    """
    raise NotImplementedError("Phase 1 implementation pending")


def calculate_overhead(filename: str) -> int:
    """Return header overhead in bytes for a given filename (4 + 1 + 2 + len(filename_utf8) + 8)."""
    raise NotImplementedError("Phase 1 implementation pending")
