# Product Requirements

## Problem
Every existing steganography tool forces users to choose between security, usability, and quality. Steghide (2003) has decent embedding but uses 128-bit AES and is abandoned. OpenStego has a GUI but uses flat LSB that's trivially detectable. OpenPuff offers multi-carrier chains but is closed-source and Windows-only. Academic tools require GPU training and lack encryption. Security researchers, CTF competitors, journalists, and SOC analysts need a unified tool that combines production-grade cryptography, adaptive embedding algorithms, built-in steganalysis scoring, and modern interfaces.

## Users
- Security researchers
- CTF competitors
- Journalists/activists needing covert comms
- Photographers wanting invisible watermarks
- SOC analysts detecting hidden data
- Developers integrating via API
- Privacy-conscious individuals

## Core Features (must-have)

### Embedding & Extraction
- Embed arbitrary payload into PNG/JPEG/MP3
- Extract with passphrase
- Capacity estimation

### Security
- AES-256-CBC
- HMAC-SHA256 Encrypt-then-MAC
- PBKDF2 600K iterations
- ChaCha20 CSPRNG position scatter
- Constant-time HMAC comparison
- 16-byte random salt

### Embedding Algorithms
- PNG adaptive LSB (1-3 bit Sobel gradient)
- JPEG direct DCT via jpegio (no re-encode)
- MP3 echo hiding

### Anti-Forensics
- Payload compression (zlib) before encryption
- Metadata sanitization (auto-strip EXIF/ID3)
- PRNG scatter makes bit-plane look natural

### Analysis & Quality
- Chi-squared steganalysis scoring
- SSIM perceptual quality scoring
- RS Analysis detection test
- Steganographic diff viewer (cover vs stego)

### Interfaces
- CLI (typer+rich)
- Web UI (Streamlit dark theme)
- REST API (FastAPI)
- Batch processing mode

## Differentiating Features

| Feature | Cryptonite | Closest Competitor |
| --- | --- | --- |
| Steganalysis scoring | Yes | None |
| Adaptive LSB | Yes | OpenStego (No) |
| JPEG DCT without re-encode | Yes | Steghide (Yes, but weak crypto) |
| Triple interface (CLI/Web/API) | Yes | None |
| Payload compression | Yes | OpenPuff (Yes) |
| Metadata sanitization | Yes | Varies |
| HMAC integrity | Yes | Rare |

## Out of Scope (v1)
*Planned for v2:*
- BMP, WAV, GIF, WebP audio/image carriers
- Video carriers (MP4 frame-level embedding)
- Real-time streaming steganography
- Mobile applications (iOS/Android)
- Deniable steganography (multi-password decoy payloads)
- Multi-carrier chains (splitting payloads across files)
- Deep learning steganalysis (SRNet/Aletheia integration)
- Network protocol steganography (ICMP/DNS)

## Success Metrics

| Metric | Target | Verification Method |
| --- | --- | --- |
| PSNR | >40dB | Image quality test |
| SSIM | >0.99 | Image quality test |
| JPEG DCT | ≤1/100 | Steganalysis |
| MP3 SNR | >60dB | Audio quality test |
| χ² detection | <5% | Steganalysis |
| RS score | <0.1 | RS Analysis test |
| API | <3s | Load testing |
| BER | 0% | Data integrity test |
| Compression | >20% on text | Payload test |

## Non-Functional Requirements

### Security
- No weak ciphers
- No plaintext keys in memory
- os.urandom only
- Zero MD5/SHA1

### Performance
- <3s for 10MB
- Batch 100 files <5min
- <500MB RAM

### Portability
- Cross-platform
- Python 3.11+
- Docker image

### Code Quality
- 100% type hints
- Docstrings
- >90% coverage
- Modular

## Open Source
- MIT license
- github.com/sudo-void-001/cryptonite
- No monetization
- Community PRs welcome