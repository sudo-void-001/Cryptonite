# 🔒 CRYPTONITE
Production-grade steganography toolkit — hide encrypted payloads inside PNG, JPEG, and MP3 files.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg) ![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg) ![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)

Cryptonite combines AES-256 encryption, HMAC integrity verification, adaptive embedding algorithms, payload compression, metadata sanitization, and built-in steganalysis scoring to make data invisible inside ordinary media files. Built for security researchers, CTF competitors, journalists, and anyone who needs covert communication channels.

## Why Cryptonite?
We analyzed 14 steganography tools. None combines all of these.

| Feature | Cryptonite | Steghide | OpenStego | OpenPuff |
|---------|:---:|:---:|:---:|:---:|
| AES-256 encryption | ✅ | ❌ (128-bit) | ✅ | ✅ |
| HMAC-SHA256 integrity | ✅ | ❌ | ❌ | ❌ |
| Adaptive LSB | ✅ | Partial | ❌ | Partial |
| JPEG DCT (no re-encode) | ✅ | ❌ | ❌ | ❌ |
| MP3 support | ✅ | ❌ | ❌ | ✅ |
| PRNG scatter (ChaCha20) | ✅ | ❌ | ❌ | ✅ |
| Steganalysis scoring | ✅ | ❌ | ❌ | ❌ |
| Payload compression | ✅ | ✅ | ❌ | ❌ |
| Metadata sanitization | ✅ | ❌ | ❌ | ❌ |
| CLI + Web UI + REST API | ✅ | CLI only | GUI only | GUI only |
| Open source | ✅ | ✅ | ✅ | ❌ |
| Cross-platform | ✅ | Linux only | ✅ (Java) | ❌ (Windows) |
| Active development | ✅ | ❌ (2003) | ✅ | ❌ |

## Features
- **AES-256-CBC Encryption**: Military-grade encryption for all payloads.
- **HMAC-SHA256 Integrity**: Detects any tampering or corruption.
- **Adaptive LSB**: Smart embedding in PNG files minimizing visual distortion.
- **JPEG DCT**: Hides data in frequency domain without re-encoding.
- **MP3 Support**: Embeds data safely in audio files.
- **PRNG Scatter**: ChaCha20-based scattering to distribute payload uniformly.
- **Payload compression**: Pre-encryption zlib compression to maximize capacity.
- **Metadata sanitization**: Automatically strips identifying EXIF/ID3 tags from carriers.
- **SSIM quality scoring**: Measures visual fidelity of steganographic images.
- **RS Analysis detection**: Built-in test for common LSB detection methods.
- **Batch processing**: Embed or extract multiple files at once.
- **Steganographic diff viewer**: Visually compare cover and stego media.

## Architecture
```text
EMBED PATH
passphrase + salt -> PBKDF2 (600k) -> enc_key | hmac_key | prng_seed
carrier -> metadata sanitize (strip EXIF/ID3 without re-encoding)
payload -> zlib compress -> header pack -> AES-256-CBC encrypt -> HMAC append
        -> carrier-specific embedder -> stego file

EXTRACT PATH
stego file -> carrier-specific extractor -> raw bytes
           -> HMAC verify -> AES decrypt -> header unpack -> zlib decompress -> payload
```

## Tech Stack
| Component | Technology |
|---|---|
| Core Language | Python 3.11+ |
| Cryptography | `cryptography` |
| Image Processing | `Pillow`, `jpegio` |
| Audio Processing | `pydub`, `ffmpeg` |
| Steganalysis | `scipy`, `scikit-image` |
| CLI | `typer`, `rich` |
| Web UI | `Streamlit` |
| API | `FastAPI`, `uvicorn` |

## Project Structure
```text
cryptonite/
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── PHASES.md
│   ├── DESIGN.md
│   ├── ALGORITHMS.md
│   └── COMPETITIVE_RESEARCH.md
├── core/
│   ├── __init__.py
│   ├── crypto.py              # AES-256-CBC, PBKDF2, HMAC-SHA256
│   ├── prng.py                # ChaCha20-seeded position generation
│   ├── payload.py             # Header pack/unpack, capacity calculation
│   ├── compression.py         # zlib payload compression/decompression
│   ├── metadata.py            # Lossless EXIF/ID3 stripping and sanitization
│   ├── analysis.py            # Chi-squared, SSIM, RS analysis scoring
│   └── carriers/
│       ├── __init__.py
│       ├── base.py            # Abstract base carrier class
│       ├── png.py             # Adaptive LSB embedding
│       ├── jpeg.py            # Direct DCT coefficient embedding via jpegio
│       └── mp3.py             # Echo hiding
├── api/
│   ├── __init__.py
│   ├── routes.py              # FastAPI HTTP endpoints
│   └── schemas.py             # Pydantic request/response models
├── cli/
│   └── main.py                # Typer + Rich CLI interface
├── ui/
│   ├── app.py                 # Streamlit web interface
│   └── components.py          # Reusable Streamlit UI components
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures (sample images, audio)
│   ├── test_crypto.py
│   ├── test_prng.py
│   ├── test_payload.py
│   ├── test_compression.py
│   ├── test_metadata.py
│   ├── test_analysis.py
│   ├── test_png.py
│   ├── test_jpeg.py
│   ├── test_mp3.py
│   └── test_api.py
├── benchmarks/
│   ├── bench_psnr.py          # PSNR/SSIM quality benchmarks
│   ├── bench_detection.py     # Steganalysis evasion benchmarks
│   └── bench_performance.py   # Speed and memory benchmarks
├── samples/                   # Sample carrier files for testing
│   ├── cover.png
│   ├── cover.jpg
│   └── cover.mp3
├── Dockerfile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

## Quick Start
**Prerequisites**: Python 3.11+, ffmpeg

**Installation**:
```bash
git clone https://github.com/sudo-void-001/cryptonite.git
cd cryptonite
pip install -e .
```

**Docker Quickstart**:
```bash
docker-compose up
```
Then visit http://localhost:8501 for the Web UI or http://localhost:8000/docs for the API.

## Usage
**Embed**:
```bash
cryptonite embed --carrier image.png --payload secret.txt --passphrase "my_secure_pass" --output stego.png
```

**Extract**:
```bash
cryptonite extract --stego stego.png --passphrase "my_secure_pass" --output recovered.txt
```

**Capacity**:
```bash
cryptonite capacity --carrier image.png
```

**Analyze**:
```bash
cryptonite analyze --cover image.png --stego stego.png
```

**Batch Embed**:
```bash
cryptonite batch embed --dir ./images --payload secret.txt --passphrase "pass"
```

**Batch Extract**:
```bash
cryptonite batch extract --dir ./stego_images --passphrase "pass" --output ./recovered/
```

## API Usage
**Embed via API**:
```bash
curl -X POST "http://localhost:8000/embed" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "carrier=@image.png" \
  -F "payload=@secret.txt" \
  -F "passphrase=my_secure_pass"
```

**Extract via API**:
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "stego=@stego.png" \
  -F "passphrase=my_secure_pass"
```

**Python Requests Example**:
```python
import requests

url = "http://localhost:8000/capacity"
files = {"carrier": open("image.png", "rb")}
response = requests.get(url, files=files)
print(response.json())
```

## Implementation Phases
| Phase | Description |
|-------|-------------|
| 0 | Project setup, dependencies, CI/CD, Docker |
| 1 | Crypto engine, PRNG, payload packing & compression |
| 2 | PNG carrier & lossless metadata sanitization |
| 3 | JPEG carrier (direct DCT manipulation via jpegio) |
| 4 | MP3 carrier (echo hiding) |
| 5 | Steganalysis module (Chi-squared, SSIM, RS analysis) |
| 6 | CLI interface (Typer + Rich, batch processing) |
| 7 | Web UI (Streamlit dark theme, diff viewer) |
| 8 | REST API (FastAPI + Swagger docs) |
| 9 | Polish, benchmarks, and security audits |

## Success Metrics
- 100% test coverage on crypto modules
- Zero data corruption across 1000 randomized payload tests
- Steganographic integrity: SSIM > 0.99, PSNR > 40 dB
- Stealth: Chi-squared p > 0.05, RS score < 0.1
- Processing speed: < 3 seconds for 10MB payload

## Security Design Principles
- **Encrypt-then-MAC**: Prevents chosen-ciphertext attacks.
- **PBKDF2 Key Derivation**: High iteration count resists brute force.
- **CSPRNG Scattering**: Avoids contiguous modifications to defeat simple statistical analysis.
- **Payload Compression**: Minimizes required modifications to the carrier, increasing stealth.
- **Metadata Sanitization**: Removes identifiable fingerprints and trailing data.
- **No Weak Cipher Fallbacks**: Enforces AES-256 for all operations.
- **Abstract Carrier**: Interface enforces safe extensibility.

## Benchmarks
| Carrier | File Size | Embed Time | PSNR | SSIM | Chi-squared | Verdict |
|---------|-----------|------------|------|------|-------------|---------|
| - | - | - | - | - | - | - |

Results will be populated after Phase 9.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss proposed changes. Ensure all tests pass before submitting.

## License
MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments
Built with `jpegio`, `Pillow`, `numpy`, `pydub`, `cryptography`, `typer`, `rich`, `Streamlit`, and `FastAPI`.

---
CRYPTONITE — What you see is never all there is.
