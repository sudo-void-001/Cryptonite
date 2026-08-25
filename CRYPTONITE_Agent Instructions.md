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
Phase 0: Project setup. Documentation complete. No code implemented yet.

## What's done
- All documentation written and reviewed:
  - Product_Requirements.md
  - Architecture.md
  - Algorithm_Specifications.md
  - Implementation_Phases.md (10 phases, 89 acceptance criteria)
  - File_structure.md
  - Design_Reference.md
  - Competitive_Research.md (14 tools analyzed)
  - Extras.md (all module stubs)

## What's next
- Phase 0: Create pyproject.toml, requirements.txt, Dockerfile, CI pipeline, .gitignore
- Then Phase 1: Implement crypto.py, prng.py, payload.py, compression.py + tests