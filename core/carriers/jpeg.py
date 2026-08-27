"""
Cryptonite JPEG Carrier Module (Direct DCT Coefficient Embedding).
"""

from core.carriers.base import BaseCarrier


class JpegCarrier(BaseCarrier):
    """Direct DCT coefficient manipulation via jpegio without re-encoding."""

    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        if not isinstance(carrier_path, str):
            raise TypeError("carrier_path must be a string")
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")
        if not isinstance(prng_seed, bytes):
            raise TypeError("prng_seed must be bytes")
        raise NotImplementedError("Phase 3 implementation pending")

    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        if not isinstance(stego_path, str):
            raise TypeError("stego_path must be a string")
        if not isinstance(prng_seed, bytes):
            raise TypeError("prng_seed must be bytes")
        raise NotImplementedError("Phase 3 implementation pending")

    def capacity(self, carrier_path: str) -> int:
        if not isinstance(carrier_path, str):
            raise TypeError("carrier_path must be a string")
        raise NotImplementedError("Phase 3 implementation pending")
