This file contains the initial function stubs for the core modules.

## core/crypto.py
```python
def derive_keys(passphrase: str, salt: bytes) -> tuple[bytes, bytes, bytes]:
    """Derive (enc_key, hmac_key, prng_seed) — each 32 bytes. PBKDF2-HMAC-SHA256, 600K iterations."""
    raise NotImplementedError

def encrypt(plaintext: bytes, enc_key: bytes) -> tuple[bytes, bytes]:
    """AES-256-CBC encrypt. Returns (iv: 16B, ciphertext). Raises ValueError if key not 32B."""
    raise NotImplementedError

def compute_hmac(data: bytes, hmac_key: bytes) -> bytes:
    """Compute HMAC-SHA256 over data. Returns 32-byte MAC."""
    raise NotImplementedError

def verify_and_decrypt(iv: bytes, ciphertext: bytes, enc_key: bytes, hmac_key: bytes, stored_mac: bytes) -> bytes:
    """Verify HMAC then decrypt. Encrypt-then-MAC. Raises ValueError on MAC failure. Uses hmac.compare_digest for constant-time comparison."""
    raise NotImplementedError
```

## core/prng.py
```python
def generate_permutation(seed: bytes, length: int) -> list[int]:
    """Generate a cryptographic permutation of indices [0, length). Uses ChaCha20 CSPRNG seeded with the given 32-byte seed."""
    raise NotImplementedError
```

## core/payload.py
```python
MAGIC = b"STGC"
VERSION = 1

def pack(filename: str, payload: bytes, is_compressed: bool = False) -> bytes:
    """
    Pack payload with header:
    [magic: 4B "STGC"]
    [version: 1B] (bit 7: 1 if compressed, 0 if uncompressed; bits 0-6: version number)
    [filename_len: 2B (big-endian uint16)]
    [filename: NB (UTF-8)]
    [payload_size: 8B (big-endian uint64)]
    [payload_bytes: NB]
    """
    raise NotImplementedError

def unpack(data: bytes) -> tuple[str, bytes, bool]:
    """
    Unpack header, returning (filename, payload_bytes, is_compressed).
    Raises ValueError on invalid magic, unsupported version, or truncated data.
    """
    raise NotImplementedError

def calculate_overhead(filename: str) -> int:
    """Return header overhead in bytes for a given filename (4 + 1 + 2 + len(filename_utf8) + 8)."""
    raise NotImplementedError
```

## core/compression.py
```python
def compress(data: bytes, level: int = 6) -> tuple[bytes, bool]:
    """zlib compress data. Returns (result_bytes, was_compressed). If compressed >= original, returns (original, False)."""
    raise NotImplementedError

def decompress(data: bytes, is_compressed: bool) -> bytes:
    """zlib decompress if is_compressed flag is True, else return data unchanged."""
    raise NotImplementedError
```

## core/metadata.py
```python
def strip_png_metadata(image_path: str) -> bytes:
    """Remove all ancillary PNG chunks (tEXt, iTXt, zTXt, eXIf, tIME, etc.). Keep critical chunks only."""
    raise NotImplementedError

def strip_jpeg_metadata(image_path: str) -> bytes:
    """Remove all EXIF, IPTC, XMP metadata from JPEG. Preserve image data."""
    raise NotImplementedError

def strip_mp3_metadata(audio_path: str) -> bytes:
    """Remove ID3v1, ID3v2, APE tags from MP3. Preserve audio frames."""
    raise NotImplementedError
```

## core/analysis.py
```python
from dataclasses import dataclass

@dataclass
class SteganalysisResult:
    chi_squared_p_value: float
    ssim_score: float
    rs_score: float
    psnr_db: float
    verdict: str  # 'SAFE' | 'MODERATE' | 'HIGH_RISK'

def chi_squared_test(image_array) -> float:
    """Run chi-squared LSB pair analysis. Returns p-value (higher = less detectable)."""
    raise NotImplementedError

def compute_ssim(cover_array, stego_array) -> float:
    """Compute SSIM between cover and stego images. Returns value in [0, 1]."""
    raise NotImplementedError

def compute_psnr(cover_array, stego_array) -> float:
    """Compute PSNR in dB between cover and stego. Returns float."""
    raise NotImplementedError

def rs_analysis(image_array) -> float:
    """Run RS analysis. Returns RS ratio (lower = less detectable)."""
    raise NotImplementedError

def full_analysis(cover_array, stego_array) -> SteganalysisResult:
    """Run all steganalysis tests. Returns comprehensive result with verdict."""
    raise NotImplementedError
```

## core/carriers/base.py
```python
from abc import ABC, abstractmethod

class BaseCarrier(ABC):
    @abstractmethod
    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        """Embed payload into carrier. Returns stego file bytes."""
        ...

    @abstractmethod
    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        """Extract payload from stego file. Returns raw payload bytes."""
        ...

    @abstractmethod
    def capacity(self, carrier_path: str) -> int:
        """Return maximum payload capacity in bytes."""
        ...
```

Same pattern for every module!. The AI fills in the raise NotImplementedError bodies. The interface never changes mid-project.