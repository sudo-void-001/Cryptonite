# 🔐 CRYPTONITE

**Production-grade steganography toolkit — hide encrypted payloads inside PNG, JPEG, and MP3 files.**

Cryptonite combines AES-256 encryption, HMAC integrity verification, and carrier-specific embedding algorithms to make data invisible inside ordinary media files. Built for security researchers, CTF competitors, journalists, and anyone who needs covert communication channels.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Multi-carrier support** | Embed payloads into PNG, JPEG, and MP3 files |
| **AES-256-CBC encryption** | Military-grade encryption before embedding |
| **HMAC-SHA256 integrity** | Tamper detection on every extraction |
| **Adaptive LSB (PNG)** | Texture-aware bit depth — hides more in noisy regions, less in flat areas |
| **DCT coefficient embedding (JPEG)** | Direct coefficient manipulation via `jpegio` — no re-encoding artifacts |
| **Echo hiding (MP3)** | Imperceptible echo delays encode binary data into audio |
| **PRNG position scatter** | ChaCha20-seeded permutation makes payload positions unpredictable |
| **Steganalysis scoring** | Chi-squared detection test tells you how invisible your payload is |
| **Capacity estimation** | Know exactly how much data a carrier can hold before embedding |

---

## 🏗️ Architecture

```
EMBED PATH
──────────
passphrase + salt → PBKDF2 (600k iterations)
                  → enc_key | hmac_key | prng_seed

payload → header pack → AES-256-CBC encrypt → HMAC append
        → carrier-specific embedder → stego file


EXTRACT PATH
────────────
stego file → carrier-specific extractor → raw bytes
           → HMAC verify → AES decrypt → header unpack → payload
```

### Encrypted Blob Format
```
┌──────────┬──────────┬──────────┬─────────────────┐
│ salt:16B │  iv:16B  │ hmac:32B │ ciphertext:var  │
└──────────┴──────────┴──────────┴─────────────────┘
```

### Payload Header Format
```
┌────────────┬──────────┬───────────────┬────────────┬───────────────┬──────────────┐
│ magic:"STGC" │ ver:1B │ fname_len:2B │ fname:NB  │ payload_sz:8B │ payload:NB   │
└────────────┴──────────┴───────────────┴────────────┴───────────────┴──────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Cryptography | `cryptography` (AES-256-CBC, PBKDF2, HMAC-SHA256) |
| PNG processing | `numpy`, `Pillow` |
| JPEG processing | `jpegio` (raw DCT access) |
| MP3 processing | `pydub` + `ffmpeg` |
| CLI | `typer` + `rich` |
| Web UI | `Streamlit` |
| API | `FastAPI` + `uvicorn` |

---

## 📁 Project Structure

```
Cryptonite/
├── docs/
│   ├── PRD.md                 # Product requirements
│   ├── ARCHITECTURE.md        # System design & data flow
│   ├── PHASES.md              # Implementation plan & acceptance criteria
│   ├── DESIGN.md              # UI/visual reference
│   └── ALGORITHMS.md          # Math specs for each carrier
├── core/
│   ├── __init__.py
│   ├── crypto.py              # Key derivation, encryption, HMAC
│   ├── prng.py                # ChaCha20-seeded position generation
│   ├── payload.py             # Header pack/unpack, capacity calculation
│   └── carriers/
│       ├── __init__.py
│       ├── png.py             # Adaptive LSB embedding
│       ├── jpeg.py            # DCT coefficient embedding
│       └── mp3.py             # Echo hiding
├── cli/
│   └── main.py                # Typer CLI interface
├── api/
│   └── routes.py              # FastAPI HTTP layer
├── ui/
│   └── app.py                 # Streamlit web interface
├── tests/
│   ├── test_crypto.py
│   ├── test_png.py
│   ├── test_jpeg.py
│   └── test_mp3.py
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- `ffmpeg` installed and on PATH (for MP3 processing)

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/cryptonite.git
cd cryptonite

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Usage (planned)

**Embed a payload:**
```bash
cryptonite embed --carrier cover.png --payload secret.txt --passphrase "my-secret-phrase" --output stego.png
```

**Extract a payload:**
```bash
cryptonite extract --stego stego.png --passphrase "my-secret-phrase" --output recovered.txt
```

**Check capacity:**
```bash
cryptonite capacity --file cover.png
```

**Run steganalysis:**
```bash
cryptonite analyze --file suspicious.png
```

---

## 📋 Implementation Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Crypto engine — `crypto.py`, `prng.py`, `payload.py` + tests | 🔲 Not started |
| **Phase 2** | PNG carrier — adaptive LSB embedding + steganalysis | 🔲 Not started |
| **Phase 3** | JPEG carrier — DCT coefficient embedding via `jpegio` | 🔲 Not started |
| **Phase 4** | MP3 carrier — echo hiding | 🔲 Not started |
| **Phase 5** | CLI interface — `typer` + `rich` | 🔲 Not started |
| **Phase 6** | Web UI — `Streamlit` dark theme | 🔲 Not started |
| **Phase 7** | REST API — `FastAPI` | 🔲 Not started |

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| PNG output quality | PSNR > 40 dB |
| JPEG DCT impact | ≤ 1 change per 100 coefficients |
| MP3 audio quality | SNR > 60 dB |
| Steganalysis evasion | Chi-squared detection probability < 5% |
| API response time | < 3 seconds for files under 10 MB |

---

## 🔒 Security Design Principles

- **PBKDF2-HMAC-SHA256** with 600,000 iterations — no MD5, ever
- **Encrypt-then-MAC** — HMAC covers ciphertext, not plaintext
- **ChaCha20 PRNG** for position scatter — cryptographically secure, not Mersenne Twister
- **No JPEG re-encoding** — `jpegio` modifies DCT coefficients directly
- **Constant-time HMAC comparison** — prevents timing side-channel attacks

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/carrier-bmp`)
3. Commit your changes (`git commit -m 'Add BMP carrier support'`)
4. Push to the branch (`git push origin feature/carrier-bmp`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <strong>CRYPTONITE</strong> — What you see is never all there is.
</p>
