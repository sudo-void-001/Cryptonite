# Architecture

## Data Flow — Embed Path
```
passphrase + salt → PBKDF2 (600K iterations) → (enc_key, hmac_key, prng_seed)
carrier file → metadata sanitization (losslessly strip EXIF/ID3)
payload → zlib compress → header pack (with compression flag) → AES-256-CBC encrypt → HMAC append
→ carrier-specific embedder (using PRNG permutation) → stego file
```

## Data Flow — Extract Path
```
stego file → carrier-specific extractor → raw bytes
→ HMAC verify → AES decrypt → header unpack → zlib decompress (if flagged) → payload file
```

## Payload Header Format
[magic:4B "STGC"][version:1B (bit 7: compressed)][filename_len:2B][filename:NB][payload_size:8B][payload_bytes:NB]

## Key Derivation
PBKDF2-HMAC-SHA256, 600K iterations, 16B salt, 96B output split into enc_key[0:32], hmac_key[32:64], prng_seed[64:96]

## Encrypted Blob Format
[salt:16B][iv:16B][hmac:32B][ciphertext:variable]

## PNG Embedding Strategy
Adaptive LSB: 1-bit low-texture, 2-bit medium, 3-bit high-texture. Texture via Sobel edge filter. ChaCha20 PRNG permutation. Euler graph matching to minimize pixel changes.

## JPEG Embedding Strategy
jpegio raw DCT access (no re-encode). Skip DC coefficients and abs(val)<=1. Embed LSB of AC coefficients, sign-preserving. PRNG permutation of coefficient indices.

## MP3 Embedding Strategy
Primary: echo hiding (d0=0.5ms bit 0, d1=1.0ms bit 1, amplitude=0.05). Extraction: autocorrelation per segment.

## Steganalysis Module
- Chi-squared test: statistical analysis of LSB pair distributions
- SSIM scoring: perceptual quality comparison cover vs stego
- RS Analysis: Regular-Singular group statistical detection
- Output: detection_score (0.0-1.0), quality metrics (PSNR, SSIM), risk verdict (SAFE/MODERATE/HIGH)

## Metadata Sanitization
- PNG: strip all ancillary chunks (tEXt, iTXt, zTXt, eXIf, etc.) except critical (IHDR, PLTE, IDAT, IEND, tRNS)
- JPEG: losslessly strip EXIF, IPTC, XMP APP markers directly at byte/stream level (NEVER save via PIL)
- MP3: strip ID3v1, ID3v2, APE tags while preserving audio frame streams

## Compression Pipeline
- Algorithm: zlib (level 6 default, configurable)
- Applied BEFORE header packing, so header flag accurately encodes compression status
- Fallback: if compressed size >= original, store raw payload and set header compression flag to 0
- Header version byte (bit 7) records compression state

## Batch Processing
- Input: directory path + glob pattern + passphrase
- Output: parallel embed/extract across matched files
- Concurrency: ThreadPoolExecutor (I/O bound) with configurable workers
- Progress: callback-based reporting for CLI/UI progress bars

## Module Boundaries
- crypto.py: ONLY key derivation, encryption, HMAC. No file I/O.
- prng.py: ONLY position generation. Takes seed + capacity, returns permutation.
- payload.py: ONLY header pack/unpack, capacity calculation.
- compression.py: ONLY zlib compress/decompress. Takes bytes, returns bytes.
- metadata.py: ONLY lossless metadata stripping. Takes file path, returns sanitized bytes.
- analysis.py: ONLY steganalysis scoring. Takes cover + stego arrays, returns metrics dict.
- carriers/base.py: Abstract base class with embed(), extract(), capacity() interface.
- carriers/*.py: ONLY file I/O and bit embedding/extraction. Implements base.py.
- cli/main.py: ONLY user interface. No business logic.
- api/routes.py: ONLY HTTP layer. Calls core modules.
- ui/app.py: ONLY Streamlit UI. Calls core modules.

## Key Decisions and Reasons
- PBKDF2 over scrypt: broader library support, deterministic on all platforms
- jpegio over PIL: PIL re-encodes JPEG on save, destroying DCT-level edits
- ChaCha20 PRNG over Mersenne Twister: cryptographically secure, unpredictable positions
- Encrypt-then-MAC over GCM: explicit HMAC easier to audit
- zlib over brotli: universal standard library availability, zero external binary dependency
- Lossless metadata stripping: eliminates forensic metadata signatures without altering media streams
- SSIM over PSNR alone: SSIM correlates better with human visual perception
- Abstract base carrier: enables easy addition of new carrier formats (BMP, WAV, GIF, WebP, Video in v2)