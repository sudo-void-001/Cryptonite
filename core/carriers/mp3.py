"""
Cryptonite MP3 Carrier Module (Echo Hiding).
"""

from core.carriers.base import BaseCarrier


class Mp3Carrier(BaseCarrier):
    """Acoustic echo hiding carrier."""

    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        raise NotImplementedError("Phase 4 implementation pending")

    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        raise NotImplementedError("Phase 4 implementation pending")

    def capacity(self, carrier_path: str) -> int:
        raise NotImplementedError("Phase 4 implementation pending")
