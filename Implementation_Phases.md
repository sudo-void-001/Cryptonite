# Implementation Phases

---

### Phase 0 — Project Setup
Files: pyproject.toml, requirements.txt, requirements-dev.txt, Dockerfile, .github/workflows/ci.yml, .env.example, .gitignore
Acceptance criteria:
- [ ] Virtual environment creates and activates
- [ ] All dependencies install without errors
- [ ] Docker image builds successfully
- [ ] CI pipeline runs (even if no tests yet)
- [ ] Project importable: `from core import crypto, prng, payload`

### Phase 1 — Crypto Engine
Files: core/crypto.py, core/prng.py, core/payload.py, core/compression.py
Tests: tests/test_crypto.py, tests/test_payload.py
Acceptance criteria:
- [ ] encrypt(decrypt(data)) == data for arbitrary byte strings
- [ ] Two identical passphrases + same salt produce identical keys
- [ ] Two different salts produce different keys
- [ ] HMAC verification fails if ciphertext is modified by 1 bit
- [ ] HMAC comparison is constant-time (uses hmac.compare_digest)
- [ ] PRNG produces same permutation given same seed and length
- [ ] PRNG produces different permutation given different seed
- [ ] payload.pack(payload.unpack(data)) == data roundtrip
- [ ] Compression reduces text payloads by >20%
- [ ] compress(decompress(data)) == data roundtrip
- [ ] Compression fallback: if compressed >= original, returns original with flag
- [ ] All functions have type hints and docstrings

### Phase 2 — PNG Carrier
Files: core/carriers/base.py, core/carriers/png.py, core/metadata.py
Tests: tests/test_png.py, tests/test_metadata.py
Acceptance criteria:
- [ ] embed(extract(cover, payload)) == payload roundtrip
- [ ] Output PSNR > 40 dB vs cover
- [ ] Output SSIM > 0.99 vs cover
- [ ] Chi-squared detection score < 0.05 on output
- [ ] capacity() returns correct byte count
- [ ] Raises clear error if payload exceeds capacity
- [ ] Adaptive bit depth: verifies 1-bit in flat regions, 3-bit in textured
- [ ] PRNG scatter: bit-plane of stego looks like noise (no visible pattern)
- [ ] Metadata stripped: no EXIF data in output PNG
- [ ] base.py abstract class enforced (TypeError if embed/extract/capacity not implemented)

### Phase 3 — JPEG Carrier
Files: core/carriers/jpeg.py
Tests: tests/test_jpeg.py
Acceptance criteria:
- [ ] embed(extract(cover, payload)) == payload roundtrip
- [ ] DCT coefficient changes <= 1 per 100 total coefficients
- [ ] No DC coefficients modified (only AC)
- [ ] No re-encoding artifacts (file saved via jpegio, not PIL)
- [ ] Sign-preserving LSB modification verified
- [ ] capacity() returns correct byte count
- [ ] EXIF metadata stripped from output
- [ ] Raises error if payload exceeds capacity

### Phase 4 — MP3 Carrier
Files: core/carriers/mp3.py
Tests: tests/test_mp3.py
Acceptance criteria:
- [ ] embed(extract(cover, payload)) == payload roundtrip
- [ ] Output SNR > 60 dB vs cover audio
- [ ] Echo delays correctly placed at d0 (0.5ms) and d1 (1.0ms)
- [ ] Echo amplitude <= 5% of original signal
- [ ] Autocorrelation extraction correctly identifies d0 vs d1 peaks
- [ ] capacity() returns correct byte count
- [ ] ID3 tags stripped from output (except embedded payload tag if used)
- [ ] Raises error if payload exceeds capacity

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
- [ ] `cryptonite embed` works with --carrier, --payload, --passphrase, --output flags
- [ ] `cryptonite extract` works with --stego, --passphrase, --output flags
- [ ] `cryptonite capacity` shows carrier capacity in human-readable format
- [ ] `cryptonite analyze` runs steganalysis and shows chi-squared, SSIM, RS, verdict
- [ ] `cryptonite batch embed` processes directory of files
- [ ] `cryptonite batch extract` processes directory of stego files
- [ ] Rich panels: green for success, red for failure, yellow for warnings
- [ ] Progress bars for batch operations
- [ ] `--help` shows clear usage for all commands
- [ ] Passphrase can be provided via --passphrase flag or interactive prompt (hidden input)

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