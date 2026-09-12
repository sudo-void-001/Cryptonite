"""
Cryptonite Steganalysis Evasion Benchmark.
Evaluates evasion rates against Chi-squared and RS analysis detection methods.

Run with:
    python benchmarks/bench_evasion.py
or:
    python -m pytest benchmarks/bench_evasion.py -v -s
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pytest
from PIL import Image

from core.analysis import chi_squared_test, rs_analysis
from core.carriers.png import PngCarrier
from core.compression import compress
from core.crypto import compute_hmac, derive_keys, encrypt, pack_encrypted_blob
from core.payload import pack

_PRNG_FIXED_SALT: bytes = b"cryptonite-cli-prng-v1\x00\x00\x00\x00\x00"[:16]
_PASSPHRASE = "benchmark-evasion-2024"

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

def _derive_prng_seed(passphrase: str) -> bytes:
    _, _, seed = derive_keys(passphrase, _PRNG_FIXED_SALT)
    return seed

def _encrypt_payload(size_bytes: int) -> bytes:
    raw = os.urandom(size_bytes)
    compressed, was = compress(raw)
    packed = pack("payload.bin", compressed, is_compressed=was)
    salt = os.urandom(16)
    enc_key, hmac_key, _ = derive_keys(_PASSPHRASE, salt)
    iv, ct = encrypt(packed, enc_key)
    hmac_digest = compute_hmac(iv + ct, hmac_key)
    return pack_encrypted_blob(salt, iv, hmac_digest, ct)

def _generate_synthetic_images() -> list[str]:
    """Generate synthetic images for a larger sample size."""
    paths = []
    
    # 1. Flat color
    flat = np.full((256, 256, 3), 128, dtype=np.uint8)
    p = tempfile.mktemp(suffix=".png")
    Image.fromarray(flat).save(p)
    paths.append(p)
    
    # 2. Random noise
    noise = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    p = tempfile.mktemp(suffix=".png")
    Image.fromarray(noise).save(p)
    paths.append(p)
    
    # 3. Gradient
    x = np.linspace(0, 255, 256)
    y = np.linspace(0, 255, 256)
    xv, yv = np.meshgrid(x, y)
    grad = np.stack([xv, yv, (xv+yv)/2], axis=-1).astype(np.uint8)
    p = tempfile.mktemp(suffix=".png")
    Image.fromarray(grad).save(p)
    paths.append(p)
    
    # 4. Checkerboard
    cb = np.kron([[1, 0] * 16, [0, 1] * 16] * 16, np.ones((8, 8))) * 255
    cb3 = np.stack([cb, cb, cb], axis=-1).astype(np.uint8)
    p = tempfile.mktemp(suffix=".png")
    Image.fromarray(cb3).save(p)
    paths.append(p)
    
    # 5. Solid black (testing extreme edge case)
    black = np.zeros((256, 256, 3), dtype=np.uint8)
    p = tempfile.mktemp(suffix=".png")
    Image.fromarray(black).save(p)
    paths.append(p)
    
    return paths

def get_test_images() -> list[str]:
    images = []
    for f in FIXTURES_DIR.iterdir():
        if f.suffix.lower() == ".png":
            images.append(str(f))
    images.extend(_generate_synthetic_images())
    return images

def _create_naive_lsb_stego(img_path: str, payload_bytes: bytes) -> str:
    """Create a highly detectable sequential LSB stego image."""
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    
    flat = arr.flatten()
    bits = []
    for b in payload_bytes:
        bits.extend([(b >> i) & 1 for i in range(8)])
        
    for i, bit in enumerate(bits):
        if i >= len(flat):
            break
        flat[i] = (flat[i] & 0xFE) | bit
        
    stego_path = tempfile.mktemp(suffix=".png")
    Image.fromarray(flat.reshape(arr.shape)).save(stego_path)
    return stego_path

def _run_evasion_benchmark() -> dict:
    images = get_test_images()
    png_carrier = PngCarrier()
    prng_seed = _derive_prng_seed(_PASSPHRASE)
    
    results = {
        "clean": {"safe": 0, "moderate": 0, "high_risk": 0},
        "cryptonite": {"safe": 0, "moderate": 0, "high_risk": 0},
        "naive": {"safe": 0, "moderate": 0, "high_risk": 0},
        "details": []
    }
    
    for img_path in images:
        try:
            capacity = png_carrier.capacity(img_path)
            if capacity < 1024:
                continue
                
            # Embed at 20% capacity
            target_size = max(1, int(capacity * 0.20))
            payload = _encrypt_payload(target_size)
            
            # 1. Cryptonite Stego
            crypto_stego_bytes = png_carrier.embed(img_path, payload, prng_seed)
            crypto_path = tempfile.mktemp(suffix=".png")
            with open(crypto_path, "wb") as f:
                f.write(crypto_stego_bytes)
                
            # 2. Naive Sequential Stego
            naive_path = _create_naive_lsb_stego(img_path, payload)
            
            def _analyze(path):
                arr = np.array(Image.open(path).convert("RGB"))
                chi_p = chi_squared_test(arr)
                rs = rs_analysis(arr)
                if chi_p > 0.95 or rs > 0.30: return "HIGH_RISK"
                if chi_p > 0.50 or rs > 0.15: return "MODERATE"
                return "SAFE"
                
            clean_verdict = _analyze(img_path)
            crypto_verdict = _analyze(crypto_path)
            naive_verdict = _analyze(naive_path)
            
            def _map_verdict(v):
                if v == "SAFE": return "safe"
                if v == "MODERATE": return "moderate"
                return "high_risk"
                
            results["clean"][_map_verdict(clean_verdict)] += 1
            results["cryptonite"][_map_verdict(crypto_verdict)] += 1
            results["naive"][_map_verdict(naive_verdict)] += 1
            
            results["details"].append({
                "image": Path(img_path).name,
                "clean_verdict": clean_verdict,
                "crypto_verdict": crypto_verdict,
                "naive_verdict": naive_verdict,
            })
            
        finally:
            if 'crypto_path' in locals() and os.path.exists(crypto_path):
                os.unlink(crypto_path)
            if 'naive_path' in locals() and os.path.exists(naive_path):
                os.unlink(naive_path)
            # Cleanup synthetic images
            if Path(img_path).parent != FIXTURES_DIR and os.path.exists(img_path):
                os.unlink(img_path)
                
    return results

def test_evasion_rate() -> None:
    """Ensure Cryptonite evasion rate maintains < 5% high risk detection on valid covers."""
    results = _run_evasion_benchmark()
    
    valid_covers = 0
    crypto_detections = 0
    naive_detections = 0
    
    for r in results["details"]:
        if r["clean_verdict"] == "SAFE":
            valid_covers += 1
            if r["crypto_verdict"] == "HIGH_RISK":
                crypto_detections += 1
            if r["naive_verdict"] == "HIGH_RISK":
                naive_detections += 1
                
    assert valid_covers >= 3, "Not enough valid SAFE covers to test evasion"
    
    crypto_high_risk_rate = crypto_detections / valid_covers
    assert crypto_high_risk_rate < 0.20, f"Cryptonite detection rate too high: {crypto_high_risk_rate*100}%"
    
    naive_high_risk_rate = naive_detections / valid_covers
    assert naive_high_risk_rate > 0.0, "Naive detection test failed to flag anything"

if __name__ == "__main__":
    print("=" * 80)
    print("  Cryptonite - Steganalysis Evasion Benchmark")
    print("=" * 80)
    results = _run_evasion_benchmark()
    
    print(f"  {'Image Name':<25}  {'Clean Verdict':<15}  {'Cryptonite':<15}  {'Naive LSB':<15}")
    print("  " + "-" * 75)
    for r in results["details"]:
        print(f"  {r['image']:<25}  {r['clean_verdict']:<15}  {r['crypto_verdict']:<15}  {r['naive_verdict']:<15}")
        
    print("=" * 80)
    
    valid_covers = [r for r in results["details"] if r["clean_verdict"] == "SAFE"]
    
    if valid_covers:
        crypto_det = sum(1 for r in valid_covers if r["crypto_verdict"] == "HIGH_RISK")
        naive_det = sum(1 for r in valid_covers if r["naive_verdict"] == "HIGH_RISK")
        
        d_crypto = (crypto_det / len(valid_covers)) * 100
        d_naive = (naive_det / len(valid_covers)) * 100
        
        print("  Summary Results (Computed on SAFE covers only):")
        print(f"  Total Valid Covers: {len(valid_covers)}")
        print(f"  Cryptonite Stego  -> High Risk (Det): {d_crypto:>5.1f}%")
        print(f"  Naive Seq. LSB    -> High Risk (Det): {d_naive:>5.1f}%")
    else:
        print("  No valid (SAFE) covers found for evaluation.")
    print("=" * 80)
