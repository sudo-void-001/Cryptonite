# Implementation Phases

---

### Phase 0 — Project Setup
Files: pyproject.toml, requirements.txt, requirements-dev.txt, Dockerfile, docker-compose.yml, .github/workflows/ci.yml, .env.example, .env, .gitignore
Acceptance criteria:
- [x] Project configuration (pyproject.toml, requirements.txt, requirements-dev.txt) created
- [x] Dockerfile and docker-compose.yml created
- [x] GitHub Actions CI pipeline (.github/workflows/ci.yml) created
- [x] Environment files (.env.example and .env with all placeholders) created
- [x] Git ignore rules (.gitignore) created
- [x] Project cleanly importable: `from core import crypto, prng, payload, compression, metadata, analysis`

### Phase 1 — Crypto Engine
Files: core/crypto.py, core/prng.py, core/payload.py, core/compression.py
Tests: tests/test_crypto.py, tests/test_prng.py, tests/test_payload.py, tests/test_compression.py
Acceptance criteria:
- [x] encrypt(decrypt(data)) == data for arbitrary byte strings
- [x] Two identical passphrases + same salt produce identical keys
- [x] Two different salts produce different keys
- [x] HMAC verification fails if ciphertext is modified by 1 bit
- [x] HMAC comparison is constant-time (uses hmac.compare_digest)
- [x] PRNG produces same permutation given same seed and length
- [x] PRNG produces different permutation given different seed
- [x] payload.pack(payload.unpack(data)) == data roundtrip
- [x] Compression reduces text payloads by >20%
- [x] compress(decompress(data)) == data roundtrip
- [x] Compression fallback: if compressed >= original, returns original with flag
- [x] All functions have type hints and docstrings

### Phase 2 — PNG Carrier
Files: core/carriers/base.py, core/carriers/png.py, core/metadata.py
Tests: tests/test_png.py, tests/test_metadata.py
Acceptance criteria:
- [x] embed(extract(cover, payload)) == payload roundtrip
- [x] Output PSNR > 40 dB vs cover
- [x] Output SSIM > 0.99 vs cover
- [x] Chi-squared detection score < 0.05 on output
- [x] capacity() returns correct byte count
- [x] Raises clear error if payload exceeds capacity
- [x] Adaptive bit depth: verifies 1-bit in flat regions, 3-bit in textured
- [x] PRNG scatter: bit-plane of stego looks like noise (no visible pattern)
- [x] Metadata stripped: no EXIF data in output PNG
- [x] base.py abstract class enforced (TypeError if embed/extract/capacity not implemented)

### Phase 3 — JPEG Carrier
Files: core/carriers/jpeg.py
Tests: tests/test_jpeg.py
Acceptance criteria:
- [x] embed(extract(cover, payload)) == payload roundtrip
- [x] DCT coefficient changes <= 1 per 100 total coefficients
- [x] No DC coefficients modified (only AC)
- [x] No re-encoding artifacts (file saved via jpegio, not PIL)
- [x] Sign-preserving LSB modification verified
- [x] capacity() returns correct byte count
- [x] EXIF metadata stripped from output
- [x] Raises error if payload exceeds capacity

### Phase 4 — MP3 Carrier ✅ Complete
Files: core/carriers/mp3.py, core/metadata.py (strip_mp3_metadata)
Tests: tests/test_mp3.py (26 tests, 99% coverage)
- [x] embed(extract(cover, payload)) == payload roundtrip
- [x] LPC-whitened autocorrelation extraction — 100% accuracy on random payloads
- [x] Echo delays placed at d0=0.5ms (22 samples) and d1=1.0ms (44 samples) @ 44100Hz
- [x] Echo amplitude ≤ 5% of original (BASE_ALPHA=0.04); SNR > 20 dB verified
- [x] Closed-loop analysis-by-synthesis guarantees per-bit accuracy
- [x] capacity() = max(0, (n_segments // 8) - 4) bytes
- [x] ID3v2/v1 and APE tags losslessly stripped from output (RIFF WAV pass-through)
- [x] Raises ValueError if payload exceeds capacity
- [x] ChaCha20 CSPRNG segment scattering for position security
- [x] Full end-to-end pipeline: compress → pack → encrypt → embed → extract → decrypt

### Phase 5 — Steganalysis Module
Files: core/analysis.py
Tests: tests/test_analysis.py
Acceptance criteria:
- [ ] Chi-squared test returns p-value for given image
- [ ] Chi-squared correctly detects flat LSB stego (p < 0.05)
- [ ] Chi-squared passes clean images (p > 0.05)
- [ ] SSIM calculation matches scikit-image reference implementation (tolerance 0.001)
- [ ] PSNR calculation matches known test values
- [ ] RS Analysis returns score < 0.1 for clean images
- [ ] RS Analysis returns score > 0.3 for sequential LSB stego
- [ ] Combined verdict: SAFE / MODERATE / HIGH RISK
- [ ] Works on PNG and JPEG carriers

### Phase 6 — CLI Interface
Files: cli/main.py
Tests: manual testing + snapshot tests
Acceptance criteria:
- [x] `cryptonite embed` works with --carrier, --payload, --passphrase, --output flags
- [x] `cryptonite extract` works with --stego, --passphrase, --output flags
- [x] `cryptonite capacity` shows carrier capacity in human-readable format
- [x] `cryptonite analyze` runs steganalysis and shows chi-squared, SSIM, RS, verdict
- [x] `cryptonite batch embed` processes directory of files
- [x] `cryptonite batch extract` processes directory of stego files
- [x] Rich panels: green for success, red for failure, yellow for warnings
- [x] Progress bars for batch operations
- [x] `--help` shows clear usage for all commands
- [x] Passphrase can be provided via --passphrase flag or interactive prompt (hidden input)

### Phase 7 — Web UI (Streamlit)
Files: ui/app.py, ui/components.py
Acceptance criteria:
- [ ] Dark theme applied (background #0d0d0d, gold #c9a84c accents)
- [ ] Left panel: file upload, passphrase input, action buttons
- [ ] Right panel: output preview, PSNR, SSIM, chi-squared score, detection verdict, download button
- [ ] Embed mode: upload carrier + payload, enter passphrase, download stego file
- [ ] Extract mode: upload stego file, enter passphrase, download payload
- [ ] Analyze mode: upload file, show steganalysis results with color-coded verdict badge
- [ ] Capacity mode: upload file, show capacity breakdown
- [ ] Steganographic diff viewer: side-by-side cover vs stego with bit-plane overlay toggle
- [ ] Error states: clear error messages for wrong passphrase, capacity exceeded, unsupported format
- [ ] Loading spinner during embed/extract operations

### Phase 8 — REST API (FastAPI)
Files: api/routes.py, api/schemas.py
Tests: tests/test_api.py
Acceptance criteria:
- [ ] POST /embed accepts multipart form (carrier file, payload file, passphrase) returns stego file
- [ ] POST /extract accepts multipart form (stego file, passphrase) returns payload file
- [ ] GET /capacity accepts file upload, returns JSON with capacity bytes and human-readable
- [ ] POST /analyze accepts file upload, returns JSON with chi-squared, SSIM, RS, verdict
- [ ] POST /batch/embed accepts zip of carriers + payload + passphrase, returns zip of stego files
- [ ] All endpoints return proper HTTP status codes (200, 400, 413, 422, 500)
- [ ] Swagger UI available at /docs
- [ ] Response time < 3 seconds for files under 10MB
- [ ] File size limit configurable via environment variable
- [ ] CORS headers configurable

### Phase 9 — Polish and Benchmarks
Files: benchmarks/bench_*.py, README.md updates
Acceptance criteria:
- [ ] PSNR/SSIM benchmark suite runs across 10+ test images
- [ ] Steganalysis evasion benchmark validates < 5% detection rate
- [ ] Performance benchmark: embed/extract speed for 1MB, 5MB, 10MB files
- [ ] Docker image builds and runs all three interfaces
- [ ] README updated with actual benchmark results
- [ ] All tests pass in CI
- [ ] Test coverage > 90%
- [ ] No security warnings from `bandit` static analysis