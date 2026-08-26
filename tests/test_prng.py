"""
Comprehensive test suite for core.prng module.

Tests ChaCha20 CSPRNG deterministic permutation generation, bounds checking,
and distribution properties.
"""

import os

import pytest

from core.prng import generate_permutation


def test_permutation_deterministic():
    seed = os.urandom(32)
    length = 500
    p1 = generate_permutation(seed, length)
    p2 = generate_permutation(seed, length)
    assert p1 == p2


def test_permutation_different_seeds():
    length = 200
    p1 = generate_permutation(os.urandom(32), length)
    p2 = generate_permutation(os.urandom(32), length)
    assert p1 != p2


def test_permutation_valid_set():
    length = 100
    p = generate_permutation(os.urandom(32), length)
    assert sorted(p) == list(range(length))
    assert len(set(p)) == length


def test_permutation_single_element():
    p = generate_permutation(os.urandom(32), 1)
    assert p == [0]


def test_permutation_small_lengths():
    seed = os.urandom(32)
    for n in [2, 3, 5, 10, 50]:
        p = generate_permutation(seed, n)
        assert len(p) == n
        assert sorted(p) == list(range(n))


def test_permutation_large():
    length = 50_000
    seed = os.urandom(32)
    p = generate_permutation(seed, length)
    assert len(p) == length
    assert min(p) == 0
    assert max(p) == length - 1


def test_permutation_invalid_seed_types_and_lengths():
    with pytest.raises(TypeError, match="Seed must be bytes"):
        generate_permutation("not_bytes", 10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        generate_permutation(os.urandom(31), 10)
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        generate_permutation(os.urandom(33), 10)


def test_permutation_invalid_length_types_and_values():
    seed = os.urandom(32)
    with pytest.raises(TypeError, match="Length must be an integer"):
        generate_permutation(seed, "10")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive integer"):
        generate_permutation(seed, 0)
    with pytest.raises(ValueError, match="positive integer"):
        generate_permutation(seed, -10)


def test_permutation_bytearray_seed():
    seed = bytearray(os.urandom(32))
    p = generate_permutation(seed, 20)
    assert len(p) == 20
    assert sorted(p) == list(range(20))
