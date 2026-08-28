# CRYPTONITE — Agent Instructions

## Project
Cryptonite: a production-grade steganography toolkit supporting PNG, JPEG, MP3.
Fully open source (MIT). CLI for power users. Web UI via Streamlit. REST API via FastAPI.
Repository: https://github.com/sudo-void-001/cryptonite

## Stack
- Python 3.11+ (currently using 3.12)
- cryptography (AES-256-CBC, PBKDF2, HMAC-SHA256)
- numpy, Pillow (PNG processing)
- jpegio (JPEG DCT access — NEVER use PIL for JPEG saving)
- pydub + ffmpeg (MP3 processing)
- scipy (chi-squared steganalysis)
- scikit-image (SSIM calculation)
- FastAPI + uvicorn (REST API)
- Streamlit (Web UI)
- typer + rich (CLI)

## Non-negotiables
- NEVER use MD5 for key derivation. Always PBKDF2-HMAC-SHA256, 600k iterations.
- ALWAYS encrypt-then-MAC. Never MAC-then-encrypt.
- NEVER re-encode JPEG through PIL — use jpegio to modify DCT coefficients directly.
- ALWAYS use ChaCha20 CSPRNG for position scatter — never Mersenne Twister.
- ALWAYS use hmac.compare_digest for constant-time HMAC comparison.
- ALWAYS strip metadata (EXIF/ID3) from carriers before embedding.
- ALWAYS compress payload with zlib before encryption.
- All functions must have type hints and docstrings.
- Every module must have a corresponding test file.
- No weak ciphers: AES-256 only, no DES/RC4/Blowfish options.

## File structure
```
core/
├── crypto.py          ← key derivation, AES-256-CBC, HMAC-SHA256
├── prng.py            ← ChaCha20-seeded position generation
├── payload.py         ← header pack/unpack, capacity calculation
├── compression.py     ← zlib payload compression/decompression
├── metadata.py        ← EXIF/ID3 stripping and sanitization
├── analysis.py        ← chi-squared, SSIM, RS analysis scoring
└── carriers/
    ├── base.py        ← abstract base carrier class
    ├── png.py         ← adaptive LSB embedding
    ├── jpeg.py        ← DCT coefficient embedding via jpegio
    └── mp3.py         ← echo hiding
cli/main.py            ← typer + rich CLI
api/routes.py          ← FastAPI HTTP endpoints
api/schemas.py         ← Pydantic models
ui/app.py              ← Streamlit web interface
ui/components.py       ← reusable UI components
```

## Current phase
Phase 2: PNG Carrier — Implement `core/carriers/base.py`, `core/carriers/png.py` (Sobel gradient adaptive LSB), and `core/metadata.py` (lossless PNG/JPEG/MP3 metadata sanitization) with 100% test coverage.

## What's done
- All documentation reviewed, reconciled, and updated:
  - Product_Requirements.md
  - Architecture.md
  - Algorithm_Specifications.md
  - Implementation_Phases.md (10 phases, 89 acceptance criteria)
  - File_structure.md
  - Design_Reference.md
  - Competitive_Research.md (14 tools analyzed)
  - Extras.md (all module stubs)
- **Phase 0 completed**:
  - `pyproject.toml`, `requirements.txt`, `requirements-dev.txt` created
  - `Dockerfile` & `docker-compose.yml` created
  - `.github/workflows/ci.yml` CI pipeline created
  - `.env` and `.env.example` created with all integration placeholders
  - `.gitignore` created
  - Complete project module tree created (`core/`, `cli/`, `api/`, `ui/`, `tests/`, `benchmarks/`, `samples/`)
- **Phase 1 completed (100.0% Test Coverage)**:
  - `core/crypto.py`: PBKDF2-HMAC-SHA256 (600k), AES-256-CBC, HMAC-SHA256 Encrypt-then-MAC, constant-time `hmac.compare_digest`, encrypted blob packaging (100% coverage).
  - `core/prng.py`: ChaCha20 CSPRNG vectorized bulk-unpacked Fisher-Yates permutation generator (100% coverage).
  - `core/payload.py`: Binary header framing with version bit 7 compression flag and bounds checking (100% coverage).
  - `core/compression.py`: Pre-encryption zlib compression with automated passthrough fallback (100% coverage).
  - Comprehensive test suite: 67 passing unit tests, 0 failures, 0 Ruff lint errors.

## Current Status: Phase 3 Ready

The user has explicitly mandated the **"Ponytail philosophy"** (zero bloat, rock-solid robustness, fail-safe defaults, high speed, 100% test coverage, strict typing, defensive validation). 

**What is completed:**
1. **Phase 0 & Infrastructure**: 100% complete (`pyproject.toml`, Docker, CI, requirements, `.env`, `docs/` organized).
2. **Phase 1 (Crypto Engine)**: 100% complete and compliant (`crypto.py`, `prng.py`, `payload.py`, `compression.py` with 100% coverage).
3. **Phase 2 (PNG Carrier & Lossless Metadata Sanitization)**: 100% complete and compliant:
   - `core/metadata.py`: Lossless binary-level PNG chunk sanitizer stripping all ancillary chunks while strictly preserving `IHDR`, `PLTE`, `IDAT`, `IEND`, and `tRNS` with CRC32 verification (100% coverage).
   - `core/carriers/base.py`: Robust abstract base class `BaseCarrier`.
   - `core/carriers/png.py`: Adaptive LSB PNG carrier using MSB-invariant Sobel edge gradient analysis and ChaCha20 scattering (100% coverage, PSNR > 40 dB, SSIM > 0.99, RGBA alpha preservation).
   - Complete test suite: **101 passing unit and end-to-end integration tests**, 0 failures, 0 Ruff lint errors.

## Next Steps for the Next Agent

Your immediate task is to begin implementing **Phase 3 (JPEG Carrier - Direct DCT Coefficient Embedding)**.
Read `docs/Algorithm_Specifications.md` and `docs/Implementation_Phases.md` for Phase 3 requirements (`jpegio` raw DCT manipulation without re-encoding, sign-preserving AC coefficient LSB modification, DC/abs<=1 skipping).

**Guidelines for Phase 3:**
1. Maintain the Ponytail philosophy: strict typing, defensive validation, 100% test coverage.
2. Note that on Windows, `jpegio` may require C++ build tools or fallback mock/conditional handling in CI.
3. Do not modify Phase 1 or Phase 2 modules (`core/crypto.py`, `core/prng.py`, `core/payload.py`, `core/compression.py`, `core/metadata.py`, `core/carriers/png.py`) — they are completed and fully tested.