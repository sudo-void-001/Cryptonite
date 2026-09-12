"""
Cryptonite Quality Benchmark — PSNR and SSIM validation across diverse images.

Run with:
    python benchmarks/bench_quality.py
or:
    python -m pytest benchmarks/bench_quality.py -v -s
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

from core.analysis import compute_psnr, compute_ssim
from core.carriers.jpeg import JpegCarrier
from core.carriers.png import PngCarrier
from core.compression import compress
from core.crypto import compute_hmac, derive_keys, encrypt, pack_encrypted_blob
from core.payload import pack

_PRNG_FIXED_SALT: bytes = b"cryptonite-cli-prng-v1\x00\x00\x00\x00\x00"[:16]
_PASSPHRASE = "benchmark-quality-2024"

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
    """Generate some synthetic images to ensure we have a diverse set of 10+ images."""
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
        if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            images.append(str(f))
    images.extend(_generate_synthetic_images())
    return images

def _run_quality_benchmark() -> list[dict]:
    images = get_test_images()
    png_carrier = PngCarrier()
    jpeg_carrier = JpegCarrier()
    prng_seed = _derive_prng_seed(_PASSPHRASE)
    
    results = []
    
    for img_path in images:
        is_jpeg = img_path.lower().endswith((".jpg", ".jpeg"))
        carrier = jpeg_carrier if is_jpeg else png_carrier
        
        try:
            capacity = carrier.capacity(img_path)
            if capacity < 1024:
                continue
                
            # Test at 25% capacity
            target_size = max(1, int(capacity * 0.25))
            payload = _encrypt_payload(target_size)
            
            # Embed
            stego_bytes = carrier.embed(img_path, payload, prng_seed)
            stego_path = tempfile.mktemp(suffix=".jpg" if is_jpeg else ".png")
            with open(stego_path, "wb") as f:
                f.write(stego_bytes)
                
            # Compute metrics
            cover_arr = np.array(Image.open(img_path).convert("RGB"))
            stego_arr = np.array(Image.open(stego_path).convert("RGB"))
            
            # Ensure same shape for metrics by cropping to minimum dimensions
            if cover_arr.shape != stego_arr.shape:
                min_h = min(cover_arr.shape[0], stego_arr.shape[0])
                min_w = min(cover_arr.shape[1], stego_arr.shape[1])
                cover_arr = cover_arr[:min_h, :min_w]
                stego_arr = stego_arr[:min_h, :min_w]
                
            psnr = compute_psnr(cover_arr, stego_arr)
            ssim = compute_ssim(cover_arr, stego_arr)
            
            results.append({
                "image": Path(img_path).name,
                "type": "JPEG" if is_jpeg else "PNG",
                "capacity_bytes": capacity,
                "payload_bytes": len(payload),
                "psnr": psnr,
                "ssim": ssim,
            })
            
        finally:
            if 'stego_path' in locals() and os.path.exists(stego_path):
                os.unlink(stego_path)
            # Cleanup synthetic images
            if Path(img_path).parent != FIXTURES_DIR and os.path.exists(img_path):
                os.unlink(img_path)
                
    return results

def test_psnr_ssim_quality() -> None:
    """Ensure all test images maintain PSNR > 30 dB and SSIM > 0.95."""
    results = _run_quality_benchmark()
    assert len(results) >= 10, f"Expected 10+ test images, got {len(results)}"
    for r in results:
        # NOTE: Flat images might have slightly different SSIM behaviors or infinite PSNR,
        # but Cryptonite is designed to meet these metrics on standard images.
        if r["psnr"] != float('inf'):
            assert r["psnr"] >= 30.0, f"PSNR too low on {r['image']}: {r['psnr']}"
        assert r["ssim"] >= 0.95, f"SSIM too low on {r['image']}: {r['ssim']}"

if __name__ == "__main__":
    print("=" * 80)
    print("  Cryptonite - Quality Benchmark (PSNR & SSIM)")
    print("=" * 80)
    results = _run_quality_benchmark()
    print(f"  {'Image Name':<25}  {'Type':<5}  {'Load':>6}  {'PSNR (dB)':>10}  {'SSIM':>8}")
    print("  " + "-" * 65)
    
    psnrs = []
    ssims = []
    for r in results:
        load = (r["payload_bytes"] / r["capacity_bytes"]) * 100
        psnrs.append(r["psnr"] if r["psnr"] != float('inf') else 100.0)
        ssims.append(r["ssim"])
        psnr_str = "inf" if r["psnr"] == float('inf') else f"{r['psnr']:>10.2f}"
        print(f"  {r['image']:<25}  {r['type']:<5}  {load:>5.1f}%  {psnr_str:>10}  {r['ssim']:>8.4f}")
        
    print("=" * 80)
    print(f"  Average PSNR: {np.mean([p for p in psnrs if p < 100]):.2f} dB")
    print(f"  Average SSIM: {np.mean(ssims):.4f}")
    print("=" * 80)
