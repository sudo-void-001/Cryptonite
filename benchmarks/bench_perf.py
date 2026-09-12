"""
Cryptonite Performance Benchmark — embed/extract throughput for 1 MB, 5 MB, 10 MB payloads.

Run with:
    python benchmarks/bench_perf.py
or:
    python -m pytest benchmarks/bench_perf.py -v -s
"""

from __future__ import annotations

import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pytest
from PIL import Image

from core.carriers.png import PngCarrier
from core.compression import compress, decompress
from core.crypto import (
    compute_hmac,
    derive_keys,
    encrypt,
    pack_encrypted_blob,
    unpack_encrypted_blob,
    verify_and_decrypt,
)
from core.payload import pack, unpack

# ── crypto constants (must match CLI/UI/API) ────────────────────────────────
_PRNG_FIXED_SALT: bytes = b"cryptonite-cli-prng-v1\x00\x00\x00\x00\x00"[:16]
_PASSPHRASE = "benchmark-passphrase-2024"
_ITERATIONS = 3  # per payload size — enough for stable timing


def _derive_prng_seed(passphrase: str) -> bytes:
    _, _, seed = derive_keys(passphrase, _PRNG_FIXED_SALT)
    return seed


def _encrypt(passphrase: str, filename: str, raw: bytes) -> bytes:
    compressed, was = compress(raw)
    packed = pack(filename, compressed, is_compressed=was)
    salt = os.urandom(16)
    enc_key, hmac_key, _ = derive_keys(passphrase, salt)
    iv, ct = encrypt(packed, enc_key)
    hmac_digest = compute_hmac(iv + ct, hmac_key)
    return pack_encrypted_blob(salt, iv, hmac_digest, ct)


def _decrypt(passphrase: str, blob: bytes) -> bytes:
    salt, iv, hmac_digest, ct = unpack_encrypted_blob(blob)
    enc_key, hmac_key, _ = derive_keys(passphrase, salt)
    pt = verify_and_decrypt(iv, ct, enc_key, hmac_key, hmac_digest)
    _, data, is_compressed = unpack(pt)
    return decompress(data, is_compressed)


def _make_carrier_image(min_capacity_bytes: int) -> tuple[str, str]:
    """
    Create a random-noise PNG large enough to hold `min_capacity_bytes` of payload.
    PNG LSB capacity ≈ 3 bytes per pixel for an RGB image (1 bit per channel × 3 channels = 3 bits → ~0.375 B/px).
    Rough formula: pixels needed = min_capacity_bytes / 0.375.
    We add 50% headroom and snap to a square.
    """
    pixels_needed = int(min_capacity_bytes / 0.375 * 1.5)
    side = max(512, int(pixels_needed**0.5) + 1)
    arr = np.random.randint(0, 256, (side, side, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, format="PNG")
    tmp.close()
    return tmp.name, "png"


def _run_benchmark(size_mb: int) -> dict:
    payload_bytes = os.urandom(size_mb * 1024 * 1024)
    carrier_path, _ = _make_carrier_image(len(payload_bytes) * 2)  # 2× headroom

    carrier = PngCarrier()
    prng_seed = _derive_prng_seed(_PASSPHRASE)

    embed_times: list[float] = []
    extract_times: list[float] = []

    try:
        # Pre-encrypt blob once (crypto cost is NOT part of the "carrier throughput" metric,
        # but we time the full pipeline for a real-world number)
        t0 = time.perf_counter()
        blob = _encrypt(_PASSPHRASE, f"payload_{size_mb}mb.bin", payload_bytes)
        encrypt_time = time.perf_counter() - t0

        for _ in range(_ITERATIONS):
            # ── EMBED ─────────────────────────────────────────────────────────
            t0 = time.perf_counter()
            stego_bytes = carrier.embed(carrier_path, blob, prng_seed)
            embed_times.append(time.perf_counter() - t0)

            # Write stego to temp file for extract
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as stf:
                stf.write(stego_bytes)
                stego_path = stf.name

            try:
                # ── EXTRACT ───────────────────────────────────────────────────
                t0 = time.perf_counter()
                raw_blob = carrier.extract(stego_path, prng_seed)
                recovered = _decrypt(_PASSPHRASE, raw_blob)
                extract_times.append(time.perf_counter() - t0)
            finally:
                if os.path.exists(stego_path):
                    os.unlink(stego_path)

            assert recovered == payload_bytes, "Payload round-trip mismatch!"

    finally:
        if os.path.exists(carrier_path):
            os.unlink(carrier_path)

    avg_embed = statistics.mean(embed_times)
    avg_extract = statistics.mean(extract_times)
    throughput_embed = size_mb / avg_embed
    throughput_extract = size_mb / avg_extract

    return {
        "size_mb": size_mb,
        "blob_bytes": len(blob),
        "encrypt_s": round(encrypt_time, 3),
        "avg_embed_s": round(avg_embed, 3),
        "avg_extract_s": round(avg_extract, 3),
        "embed_mb_s": round(throughput_embed, 2),
        "extract_mb_s": round(throughput_extract, 2),
    }


def run_all() -> list[dict]:
    results = []
    for size_mb in (1, 5, 10):
        print(f"\n  > {size_mb} MB payload...", flush=True)
        r = _run_benchmark(size_mb)
        results.append(r)
        print(
            f"    encrypt:  {r['encrypt_s']:.3f}s\n"
            f"    embed:    {r['avg_embed_s']:.3f}s  ({r['embed_mb_s']:.2f} MB/s)\n"
            f"    extract:  {r['avg_extract_s']:.3f}s  ({r['extract_mb_s']:.2f} MB/s)"
        )
    return results


# ── pytest harness ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("size_mb", [1, 5, 10])
def test_perf_embed_extract(size_mb: int) -> None:
    """Ensure embed+extract round-trips are correct and complete within reason."""
    r = _run_benchmark(size_mb)
    # Correctness already asserted inside _run_benchmark (assert recovered == payload)
    # Performance guard: whole round-trip should finish within 60s per MB
    assert r["avg_embed_s"] < 60, f"Embed too slow: {r['avg_embed_s']:.2f}s"
    assert r["avg_extract_s"] < 60, f"Extract too slow: {r['avg_extract_s']:.2f}s"
    print(
        f"\n  {size_mb} MB | embed {r['avg_embed_s']:.2f}s "
        f"({r['embed_mb_s']:.2f} MB/s) | extract {r['avg_extract_s']:.2f}s "
        f"({r['extract_mb_s']:.2f} MB/s)"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("  Cryptonite - Performance Benchmark")
    print("=" * 60)
    results = run_all()
    print("\n" + "=" * 60)
    print(f"  {'Size':>8}  {'Encrypt':>9}  {'Embed':>9}  {'Extract':>10}")
    print(f"  {'':>8}  {'(s)':>9}  {'(MB/s)':>9}  {'(MB/s)':>10}")
    print("  " + "-" * 44)
    for r in results:
        print(
            f"  {r['size_mb']:>5} MB  "
            f"{r['encrypt_s']:>9.3f}  "
            f"{r['embed_mb_s']:>8.2f}  "
            f"{r['extract_mb_s']:>9.2f}"
        )
    print("=" * 60)
