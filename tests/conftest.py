"""
Shared Pytest Fixtures.
"""

import pytest


@pytest.fixture
def sample_passphrase() -> str:
    return "correct-horse-battery-staple-secure-passphrase-2026"


@pytest.fixture
def sample_payload() -> bytes:
    return b"TOP SECRET: Operation Cryptonite steganography payload verification data."
