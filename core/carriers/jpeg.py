"""
Cryptonite JPEG Carrier Module (Direct DCT Coefficient Embedding).
"""

from core.carriers.base import BaseCarrier


class JpegCarrier(BaseCarrier):
    """Direct DCT coefficient manipulation via jpegio without re-encoding."""

    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        raise NotImplementedError("Phase 3 implementation pending")

    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        raise NotImplementedError("Phase 3 implementation pending")

    def capacity(self, carrier_path: str) -> int:
        raise NotImplementedError("Phase 3 implementation pending")
