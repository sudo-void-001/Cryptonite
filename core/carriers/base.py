"""
Cryptonite Abstract Base Carrier.
"""

from abc import ABC, abstractmethod


class BaseCarrier(ABC):
    """Abstract interface that all carrier plugins must implement."""

    @abstractmethod
    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        """Embed payload into carrier. Returns stego file bytes."""
        raise NotImplementedError

    @abstractmethod
    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        """Extract payload from stego file. Returns raw payload bytes."""
        raise NotImplementedError

    @abstractmethod
    def capacity(self, carrier_path: str) -> int:
        """Return maximum payload capacity in bytes."""
        raise NotImplementedError
