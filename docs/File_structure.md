```text
Cryptonite/
├── docs/
│   ├── Algorithm_Specifications.md
│   ├── Architecture.md
│   ├── Competitive_Research.md
│   ├── CRYPTONITE_Agent Instructions.md
│   ├── Design_Reference.md
│   ├── Extras.md
│   ├── File_structure.md
│   ├── Implementation_Phases.md
│   └── Product_Requirements.md
├── core/
│   ├── __init__.py
│   ├── crypto.py              ← key derivation, AES-256-CBC, HMAC-SHA256
│   ├── prng.py                ← ChaCha20-seeded position generation
│   ├── payload.py             ← header pack/unpack, capacity calculation
│   ├── compression.py         ← zlib payload compression/decompression
│   ├── metadata.py            ← EXIF/ID3 stripping and sanitization
│   ├── analysis.py            ← chi-squared, SSIM, RS analysis scoring
│   └── carriers/
│       ├── __init__.py
│       ├── base.py            ← abstract base carrier class
│       ├── png.py             ← adaptive LSB embedding
│       ├── jpeg.py            ← DCT coefficient embedding via jpegio
│       └── mp3.py             ← echo hiding
├── cli/
│   └── main.py                ← typer + rich CLI interface
├── api/
│   ├── __init__.py
│   ├── routes.py              ← FastAPI HTTP endpoints
│   └── schemas.py             ← Pydantic request/response models
├── ui/
│   ├── app.py                 ← Streamlit web interface
│   └── components.py          ← reusable Streamlit UI components
├── tests/
│   ├── __init__.py
│   ├── conftest.py            ← shared fixtures (sample images, audio)
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
│   ├── bench_psnr.py          ← PSNR/SSIM quality benchmarks
│   ├── bench_detection.py     ← steganalysis evasion benchmarks
│   └── bench_performance.py   ← speed and memory benchmarks
├── samples/                   ← sample carrier files for testing
│   ├── cover.png
│   ├── cover.jpg
│   └── cover.mp3
├── .github/
│   └── workflows/
│       └── ci.yml             ← GitHub Actions CI pipeline
├── Dockerfile                 ← containerized deployment
├── docker-compose.yml         ← full stack (API + UI)
├── requirements.txt           ← pinned dependencies
├── requirements-dev.txt       ← dev/test dependencies
├── pyproject.toml             ← project metadata + tool config
├── .env.example               ← environment variables template
├── .gitignore
├── LICENSE                    ← MIT
└── README.md
```

## Module Responsibilities
- `crypto.py`: Handles all cryptography including AES-256-CBC, HMAC-SHA256, and PBKDF2 key derivation.
- `prng.py`: Generates scattered embedding positions using a ChaCha20-based PRNG.
- `payload.py`: Manages packing, unpacking, and capacity calculation of the payload headers and data.
- `compression.py`: Handles payload compression and decompression using zlib to save space and add entropy.
- `metadata.py`: Responsible for stripping EXIF/ID3 metadata to sanitize carriers.
- `analysis.py`: Calculates steganalysis metrics like chi-squared, SSIM, and RS analysis to score stego quality.
- `carriers/base.py`: Defines the abstract interface that all carrier types must implement.
- `carriers/png.py`: Implements adaptive LSB embedding for PNG images.
- `carriers/jpeg.py`: Implements direct DCT coefficient embedding for JPEG images.
- `carriers/mp3.py`: Implements echo hiding for MP3 audio files.

## Key Principles
- **Single Responsibility**: Each module owns one thing and performs one distinct task.
- **No Business Logic in Interfaces**: The CLI, API, and UI are thin wrappers around the core logic.
- **Carrier Abstraction**: All carriers implement a unified interface defined in `base.py`.
- **Security by Default**: No weak encryption options, no opting out of secure defaults.