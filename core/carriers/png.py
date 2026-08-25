"""
Cryptonite PNG Carrier Module (Adaptive LSB).
"""

from core.carriers.base import BaseCarrier


class PngCarrier(BaseCarrier):
    """Adaptive LSB carrier using Sobel gradient texture analysis."""

    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        raise NotImplementedError("Phase 2 implementation pending")

    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        raise NotImplementedError("Phase 2 implementation pending")

    def capacity(self, carrier_path: str) -> int:
        raise NotImplementedError("Phase 2 implementation pending")
