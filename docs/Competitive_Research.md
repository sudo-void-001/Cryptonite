# 🔍 Competitive Research — Steganography Tools Landscape

> **Purpose**: Deep analysis of the top steganography tools in the market, their strengths, weaknesses, and the gaps Cryptonite can exploit to build a superior product.
>
> **Last Updated**: August 2026

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Tool-by-Tool Deep Dive](#tool-by-tool-deep-dive)
   - [Tier 1 — Classic CLI / GUI Tools](#tier-1--classic-cli--gui-tools)
   - [Tier 2 — Advanced / Professional Tools](#tier-2--advanced--professional-tools)
   - [Tier 3 — Modern Python Libraries](#tier-3--modern-python-libraries)
   - [Tier 4 — Deep Learning Approaches](#tier-4--deep-learning-approaches)
3. [Steganalysis / Detection Tools](#steganalysis--detection-tools)
4. [Master Comparison Matrix](#master-comparison-matrix)
5. [Common Weaknesses Across All Tools](#common-weaknesses-across-all-tools)
6. [Where Cryptonite Wins](#where-cryptonite-wins)
7. [Cryptonite Competitive Advantages — Detailed Breakdown](#cryptonite-competitive-advantages--detailed-breakdown)
8. [Quality Metrics and Benchmarks](#quality-metrics-and-benchmarks)
9. [Threat Model: What Steganalysis Can Detect](#threat-model-what-steganalysis-can-detect)
10. [Recommendations for Cryptonite Roadmap](#recommendations-for-cryptonite-roadmap)

---

## Executive Summary

The steganography tools market is fragmented across **four tiers**: legacy CLI tools (Steghide, OutGuess), GUI-based consumer tools (OpenStego, SilentEye, QuickStego), advanced professional tools (OpenPuff, Invisible Secrets), and modern deep-learning approaches (SteganoGAN, HiDDeN, StegaStamp). Despite decades of development, **no single tool** combines:

- Multi-carrier support (PNG + JPEG + Audio)
- Production-grade encryption (AES-256 + HMAC)
- Adaptive embedding algorithms (texture-aware, not flat LSB)
- Built-in steganalysis scoring
- PRNG position scatter (cryptographically secure)
- Triple interface (CLI + Web UI + REST API)
- Modern Python ecosystem with clean architecture

**Cryptonite fills every gap above.** This document proves it.

---

## Tool-by-Tool Deep Dive

### Tier 1 — Classic CLI / GUI Tools

---

#### 1. Steghide

| Attribute | Details |
|-----------|---------|
| **Type** | CLI (command-line only) |
| **Language** | C++ |
| **License** | GPL |
| **Carriers** | JPEG, BMP, WAV, AU |
| **Encryption** | 128-bit AES (default), Blowfish, Rijndael, others |
| **Embedding** | LSB + graph-matching (optimized pixel pairing) |
| **Last Update** | ~2003 (abandoned) |

**Strengths:**
- Graph-theoretic embedding minimizes visual artifacts
- Built-in integrity checking with checksums
- Compresses data before embedding (maximizes capacity)
- Lightweight, no dependencies

**Weaknesses:**
- **128-bit AES only** — no AES-256 option
- **No PNG support** — the most common lossless format is excluded
- **No MP3 support** — audio limited to WAV/AU
- **Abandoned since 2003** — no security patches, no modern OS support
- **Well-known signatures** — tools like `StegSeek` can brute-force weak passphrases
- **No steganalysis scoring** — you can't check how detectable your output is
- **No API or Web UI** — CLI only
- **No HMAC verification** — integrity checking uses basic checksums, not cryptographic MACs

**What Cryptonite does better:**
AES-256-CBC with HMAC-SHA256 (not 128-bit AES with checksums). PNG + JPEG + MP3 support. ChaCha20 PRNG scatter instead of deterministic positions. Built-in chi-squared steganalysis scoring.

---

#### 2. OpenStego

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Java-based) |
| **Language** | Java |
| **License** | GPL v2 |
| **Carriers** | BMP, PNG, JPEG, GIF |
| **Encryption** | DES, AES (configurable) |
| **Embedding** | Standard LSB |
| **Last Update** | Active (maintained) |

**Strengths:**
- User-friendly GUI with drag-and-drop
- Invisible watermarking feature (unique differentiator)
- Supports multiple image formats
- Active development

**Weaknesses:**
- **Flat LSB only** — no adaptive/texture-aware embedding
- **Requires Java Runtime** — heavy dependency, poor portability
- **No audio support** — images only
- **No PRNG position scatter** — sequential embedding = easy to detect
- **No steganalysis scoring** — no way to assess output quality
- **DES as an option** — DES is broken, shouldn't exist as an option in 2026
- **No CLI or API** — GUI only, can't automate or script
- **No HMAC integrity** — no tamper detection

**What Cryptonite does better:**
Adaptive LSB (1-3 bits based on Sobel texture detection) vs flat 1-bit LSB. ChaCha20 PRNG for position randomization. No Java dependency — pure Python. CLI + Streamlit Web UI + FastAPI REST API.

---

#### 3. SilentEye

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Qt-based) |
| **Language** | C++ |
| **License** | GPL v3 |
| **Carriers** | BMP, JPEG, WAV (via plugins) |
| **Encryption** | AES-128 (via plugins) |
| **Embedding** | LSB / plugin-extensible |
| **Last Update** | ~2013 (stale) |

**Strengths:**
- Plugin architecture for extensibility
- Clean Qt GUI
- Supports both images and audio
- Good balance of capacity and imperceptibility

**Weaknesses:**
- **Effectively abandoned** — last meaningful update ~2013
- **AES-128 only** — no AES-256
- **No PNG support** — BMP/JPEG only for images
- **Plugin dependency** — core functionality requires plugins that may not exist
- **No modern build system** — difficult to compile on modern systems
- **No steganalysis** — no detection scoring
- **No CLI or API** — GUI only
- **No HMAC or integrity checking**

**What Cryptonite does better:**
PNG + JPEG + MP3 out of the box (no plugins needed). AES-256-CBC. HMAC-SHA256 integrity. Modern Python ecosystem that actually builds in 2026.

---

#### 4. QuickStego

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Windows) |
| **Language** | C# |
| **Carriers** | BMP (primarily) |
| **Encryption** | None |
| **Embedding** | Basic LSB |

**Strengths:**
- Extremely simple, zero learning curve
- Instant text-to-image hiding

**Weaknesses:**
- **No encryption at all** — anyone who knows to look can read the data
- **Text only** — can't hide files, binaries, or archives
- **BMP only** — nobody uses BMP in 2026
- **Windows only** — no cross-platform support
- **Toy-level security** — security through obscurity alone

**What Cryptonite does better:**
Everything. Cryptonite is a production-grade toolkit; QuickStego is a toy.

---

#### 5. Xiao Steganography

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Windows) |
| **Carriers** | BMP, WAV |
| **Encryption** | RC4, DES, Triple DES, MD5/SHA hashing |
| **Embedding** | Basic LSB |

**Strengths:**
- Multiple encryption/hash algorithm choices
- Step-by-step guided workflow
- Free and lightweight

**Weaknesses:**
- **RC4 and DES are broken** — insecure by modern standards
- **BMP + WAV only** — no JPEG, PNG, or MP3
- **Windows only** — no portability
- **Flat LSB** — trivially detectable by chi-squared analysis
- **No position randomization** — sequential embedding
- **No integrity verification** — no HMAC or tamper detection

**What Cryptonite does better:**
AES-256 (not RC4/DES). HMAC-SHA256 (not basic hashing). PNG + JPEG + MP3 carriers. Cross-platform Python.

---

### Tier 2 — Advanced / Professional Tools

---

#### 6. OpenPuff

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Windows) |
| **Language** | C/C++ |
| **License** | Freeware (closed source) |
| **Carriers** | BMP, JPG, PNG, PCX, TGA, AIFF, MP3, WAV, 3GP, MP4, MPG, VOB, FLV, SWF, PDF |
| **Encryption** | 16 x 256-bit symmetric algorithms (multi-password) |
| **Embedding** | Adaptive non-linear carrier bit encoding |
| **Special Features** | Multi-carrier chains, deniable steganography, CSPRNG scrambling |

**Strengths:**
- **Multi-carrier chains** — split payloads across multiple files (up to 256MB)
- **Deniable steganography** — real + decoy payloads with separate passwords
- **Multi-layer obfuscation** — crypto, scramble, whiten, encode
- **Massive format support** — 16+ carrier types including video and PDF
- **No installation required** — portable executable

**Weaknesses:**
- **Closed source** — impossible to audit security claims
- **Windows only** — no Linux/macOS support
- **GUI only** — no CLI, no API, no automation
- **No steganalysis scoring** — can't assess output imperceptibility
- **Proprietary algorithms** — "trust us" security model
- **No developer ecosystem** — can't integrate into applications
- **Freeware is not open source** — could be abandoned or contain backdoors

**What Cryptonite does better:**
Fully open source (auditable). CLI + Web UI + REST API. Built-in steganalysis scoring (chi-squared). Cross-platform Python. Clean, documented architecture.

**What OpenPuff does better than Cryptonite (acknowledge the gap):**
Multi-carrier chains, deniable steganography, video/PDF carriers, 16+ format support. These are potential Cryptonite v2 features.

---

#### 7. Invisible Secrets

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Windows) — commercial |
| **Carriers** | JPEG, PNG, BMP, HTML, WAV |
| **Encryption** | Military-grade (AES, Blowfish, etc.) |
| **Special Features** | Password manager, file shredder, app locker |

**Strengths:**
- Full privacy suite (stego + shredder + password vault)
- "Diversion" decoy methods
- 5 carrier formats

**Weaknesses:**
- **Commercial / paid** — not open source
- **Windows only**
- **Bloated** — password manager and app locker are irrelevant to steganography
- **No MP3/audio embedding** — WAV only
- **No API or CLI**
- **No steganalysis scoring**

---

#### 8. SSuite Picsel

| Attribute | Details |
|-----------|---------|
| **Type** | GUI (Windows) — portable |
| **Carriers** | BMP, JPG, WMF |
| **Encryption** | Image-as-key (proprietary) |
| **Embedding** | Proprietary |

**Strengths:**
- Unique "image as encryption key" concept
- Zero installation, portable
- No password to remember (the image IS the key)

**Weaknesses:**
- **Proprietary/unauditable algorithm** — "image-as-key" security is unproven
- **Text only** — can't hide files
- **Limited formats** — BMP, JPG, WMF (nobody uses WMF)
- **Windows only**
- **No standard encryption** — not AES, not anything auditable

---

### Tier 3 — Modern Python Libraries

---

#### 9. SecretPixel

| Attribute | Details |
|-----------|---------|
| **Type** | Python CLI library |
| **Carriers** | PNG (primarily) |
| **Encryption** | AES-256 |
| **Embedding** | Seeded LSB |

**Strengths:**
- Modern Python, AES-256
- Seeded position selection (similar to Cryptonite's approach)
- Clean code, well-documented

**Weaknesses:**
- **PNG only** — no JPEG or audio
- **No adaptive embedding** — seeded but still flat 1-bit LSB
- **No steganalysis scoring**
- **No HMAC integrity verification**
- **No Web UI or REST API**
- **No JPEG DCT-level access** — would re-encode if JPEG support added

**What Cryptonite does better:**
Adaptive LSB (texture-aware, 1-3 bits). HMAC-SHA256 integrity. Three carrier types. Triple interface (CLI + UI + API). jpegio for lossless DCT coefficient access.

---

#### 10. stegano (Python)

| Attribute | Details |
|-----------|---------|
| **Type** | Python library |
| **Carriers** | PNG |
| **Encryption** | None built-in |
| **Embedding** | LSB (multiple strategies) |

**Strengths:**
- Pure Python, easy to pip install
- Multiple LSB strategies (basic, edge-detection based)
- Good documentation, active maintenance

**Weaknesses:**
- **No encryption** — must BYO encryption
- **PNG only**
- **No integrity verification**
- **Library only** — no CLI, no UI, no API
- **No steganalysis**

---

#### 11. cryptosteganography (Python)

| Attribute | Details |
|-----------|---------|
| **Type** | Python library |
| **Carriers** | PNG |
| **Encryption** | AES-256 |
| **Embedding** | LSB |

**Strengths:**
- Integrates AES-256 with LSB embedding
- Simple API

**Weaknesses:**
- **PNG only**
- **Flat LSB** — no adaptive embedding
- **No HMAC** — encryption without integrity verification
- **No position scatter** — sequential embedding
- **No steganalysis**
- **No JPEG DCT or audio support**

---

### Tier 4 — Deep Learning Approaches

---

#### 12. SteganoGAN

| Attribute | Details |
|-----------|---------|
| **Type** | Research framework (Python / PyTorch) |
| **Mechanism** | GAN adversarial training — encoder hides, discriminator detects |
| **Capacity** | High (configurable via architecture selection) |

**Strengths:**
- Adversarially trained — explicitly optimized to fool detection models
- High capacity with good imperceptibility
- Flexible architectures (basic, dense encoders)

**Weaknesses:**
- **Research prototype** — not production-ready
- **Requires GPU + training** — impractical for end users
- **No encryption layer** — hides data but doesn't encrypt it
- **No integrity verification**
- **Images only** — no audio
- **No CLI/API** — research notebook interface
- **Model must be shared** — both parties need the same trained model

---

#### 13. HiDDeN

| Attribute | Details |
|-----------|---------|
| **Type** | Research framework (Python / PyTorch) |
| **Mechanism** | Encoder-decoder with "noise layer" for robustness |
| **Focus** | Surviving JPEG compression, resizing, cropping |

**Strengths:**
- Trained to survive real-world distortions (JPEG compression, social media re-encoding)
- Highly robust hidden watermarks

**Weaknesses:**
- **Research-only** — not a usable tool
- **No encryption**
- **Requires GPU**
- **Low capacity** — optimized for short messages / watermarks
- **No audio support**

---

#### 14. StegaStamp

| Attribute | Details |
|-----------|---------|
| **Type** | Research framework |
| **Mechanism** | DNN trained to survive print, photograph, scan pipeline |
| **Focus** | Physical-world steganography ("invisible QR codes") |

**Strengths:**
- Survives physical printing + camera capture
- Practical for invisible barcodes and document tracking

**Weaknesses:**
- **56-bit capacity max** — only enough for a short URL
- **Research prototype**
- **No encryption or integrity**
- **Extremely specialized use case**

---

## Steganalysis / Detection Tools

Understanding the adversary is critical. These are the tools that will try to detect Cryptonite's output.

| Tool | Focus | Method | Strengths | Limitations |
|------|-------|--------|-----------|-------------|
| **Stegdetect** | JPEG signatures | Signature matching (JSteg, OutGuess, F5) | Fast triage of known tools | High false positives; JPEG only; outdated |
| **StegExpose** | LSB detection (PNG/BMP) | Chi-square + RS Analysis + Sample Pairs | Batch processing; quantitative scoring | LSB-only; poor on adaptive methods |
| **Aletheia** | Universal (modern) | Deep learning (SRNet, EfficientNet) | Detects adaptive steganography (WOW, HUGO, J-UNIWARD) | GPU required; data-dependent accuracy |
| **Stegsolve** | Visual inspection | Color plane separation, bit-plane analysis | Reveals flat LSB visually | Manual; useless against PRNG scatter |
| **Zsteg** | PNG/BMP | Multi-strategy LSB extraction | Quick; reveals sequential LSB payloads | Defeated by position randomization |
| **Binwalk** | File carving | Magic byte signatures | Finds appended/embedded files | Not true steganalysis; only finds appended data |

### Key Insight for Cryptonite

**Cryptonite's PRNG position scatter (ChaCha20) defeats:** Zsteg, Stegsolve bit-plane analysis, basic StegExpose scans.

**Cryptonite's adaptive LSB defeats:** Chi-squared analysis (by concentrating changes in high-texture regions where statistical anomalies blend into natural noise).

**What still detects Cryptonite (future threat):** Deep learning models like Aletheia's SRNet, if trained on Cryptonite's specific embedding pattern. This is the arms-race frontier.

---

## Master Comparison Matrix

| Feature | Steghide | OpenStego | SilentEye | OpenPuff | SecretPixel | stegano | SteganoGAN | **CRYPTONITE** |
|---------|----------|-----------|-----------|----------|-------------|---------|------------|----------------|
| **PNG support** | No | Yes | No | Yes | Yes | Yes | Yes | **Yes** |
| **JPEG support** | Yes | Yes | Yes | Yes | No | No | No | **Yes** |
| **MP3/Audio support** | WAV only | No | WAV only | Yes | No | No | No | **Yes** |
| **AES-256 encryption** | No (128) | Yes | No (128) | Yes | Yes | No | No | **Yes** |
| **HMAC integrity** | No | No | No | Unknown | No | No | No | **Yes** |
| **Adaptive LSB** | Partial | No | No | Partial | No | Partial | N/A | **Yes** |
| **PRNG scatter** | No | No | No | Yes | Yes | No | N/A | **Yes (ChaCha20)** |
| **DCT direct access (JPEG)** | No | No | No | Unknown | No | No | N/A | **Yes (jpegio)** |
| **Steganalysis scoring** | No | No | No | No | No | No | No | **Yes** |
| **CLI** | Yes | No | No | No | Yes | No | No | **Yes** |
| **Web UI** | No | Yes | Yes | Yes | No | No | No | **Yes (Streamlit)** |
| **REST API** | No | No | No | No | No | No | No | **Yes (FastAPI)** |
| **Open source** | Yes | Yes | Yes | No | Yes | Yes | Yes | **Yes** |
| **Cross-platform** | Linux | Yes (Java) | No | No | Yes | Yes | Yes | **Yes (Python)** |
| **Active (2024+)** | No | Yes | No | No | Yes | Yes | No | **Yes** |
| **Deniable stego** | No | No | No | Yes | No | No | No | No (future) |
| **Multi-carrier chain** | No | No | No | Yes | No | No | No | No (future) |

---

## Common Weaknesses Across All Tools

After analyzing 14 tools, these problems are **universal** or **near-universal**:

### 1. No Built-in Steganalysis Scoring
**Zero tools** offer "here's how detectable your output is" as a feature. Users embed data blindly and hope for the best. Cryptonite's chi-squared detection scoring is **unique in the market**.

### 2. Weak or Missing Integrity Verification
Most tools either skip integrity checking entirely or use basic checksums. Only Cryptonite uses HMAC-SHA256 with Encrypt-then-MAC — the gold standard for authenticated encryption.

### 3. Flat LSB Embedding
Almost every tool uses basic 1-bit LSB substitution across all pixels uniformly. This creates trivially detectable statistical anomalies. Cryptonite's Sobel-gradient adaptive bit depth (1-3 bits based on texture) is a significant advancement.

### 4. Sequential Position Selection
Most tools embed data in predictable sequential order. One pass of Zsteg or Stegsolve reveals the payload. Cryptonite's ChaCha20-seeded PRNG permutation makes positions cryptographically unpredictable.

### 5. Single Interface
Nearly all tools offer exactly one interface (CLI OR GUI, never both). None offer a REST API. Cryptonite provides all three: Typer CLI, Streamlit Web UI, FastAPI REST API.

### 6. JPEG Re-encoding Problem
Most tools that claim JPEG support actually re-encode the image on save (via PIL/Pillow), which introduces compression artifacts and destroys careful DCT modifications. Cryptonite uses `jpegio` for raw DCT coefficient access — no re-encoding.

### 7. Abandoned or Unmaintained
Steghide (2003), SilentEye (2013), and many others haven't received updates in over a decade. Known vulnerabilities go unpatched. Cryptonite is being built with modern Python 3.11+ and actively maintained.

### 8. No Audio Steganography Beyond Basic WAV
Very few tools support any audio format. Those that do are limited to WAV. Cryptonite supports MP3 via echo hiding — a more practical carrier since nobody shares WAV files casually.

---

## Where Cryptonite Wins

### The "Only Tool That" List

Cryptonite is the **only tool** that simultaneously offers:

| Capability | Why It Matters |
|------------|---------------|
| **Adaptive LSB with Sobel texture detection** | Hides more data in noisy regions, less in flat regions — evades chi-squared detection |
| **JPEG DCT access via jpegio (no re-encode)** | Modifies coefficients without introducing compression artifacts |
| **Echo hiding for MP3** | Practical audio carrier (MP3 is ubiquitous; WAV/AU are not) |
| **PBKDF2 with 600K iterations** | Brute-force resistant key derivation (Steghide uses simple hashing) |
| **HMAC-SHA256 Encrypt-then-MAC** | Tamper detection that no competitor offers |
| **ChaCha20 PRNG position scatter** | Cryptographically secure, not Mersenne Twister (Python default) |
| **Chi-squared steganalysis scoring** | Know your detection risk before sending |
| **Triple interface (CLI + Web + API)** | No other tool offers all three |
| **Capacity estimation** | Know exactly how much data fits before embedding |

---

## Cryptonite Competitive Advantages — Detailed Breakdown

### Security Layer (vs. Steghide, OpenStego, SilentEye)

| Aspect | Competitors | Cryptonite |
|--------|------------|------------|
| **Encryption** | AES-128, DES, RC4, Blowfish (mixed, often weak) | AES-256-CBC only — no weak options |
| **Key Derivation** | Simple hashing or low-iteration PBKDF2 | PBKDF2-HMAC-SHA256, 600,000 iterations |
| **Integrity** | Checksums or nothing | HMAC-SHA256 (Encrypt-then-MAC) |
| **PRNG** | Mersenne Twister or none | ChaCha20 CSPRNG |
| **Timing Attacks** | Not considered | Constant-time HMAC comparison |
| **Salt** | Often reused or predictable | 16-byte random salt per operation |

### Embedding Quality (vs. All Competitors)

| Aspect | Competitors | Cryptonite |
|--------|------------|------------|
| **PNG Strategy** | Flat 1-bit LSB | Adaptive 1-3 bit LSB (Sobel gradient) |
| **JPEG Strategy** | Re-encode via PIL (destroys quality) | Direct DCT coefficient modification (jpegio) |
| **MP3 Strategy** | Not supported or WAV-only LSB | Echo hiding (imperceptible delay encoding) |
| **Position Selection** | Sequential or basic random | ChaCha20 PRNG permutation |
| **Quality Target** | Not measured | PSNR > 40dB, SNR > 60dB |

### Steganalysis Resistance (vs. All Competitors)

| Attack | How Competitors Fail | How Cryptonite Resists |
|--------|---------------------|----------------------|
| **Chi-squared** | Flat LSB creates detectable statistical anomalies | Adaptive bit depth concentrates changes in high-texture regions |
| **RS Analysis** | Sequential embedding detected via Regular-Singular pairs | PRNG scatter distributes changes randomly across image |
| **Visual bit-plane analysis** | Stegsolve reveals patterns in LSB planes | PRNG permutation makes LSB plane look like natural noise |
| **Zsteg extraction** | Sequential LSB extracted trivially | PRNG-ordered positions can't be reconstructed without key |
| **Signature detection** | Known tool signatures (Steghide, F5) detected by Stegdetect | Custom format with no public signature database |
| **File size anomaly** | Some tools increase file size noticeably | In-place modification preserves carrier size |

### Architecture (vs. All Competitors)

| Aspect | Competitors | Cryptonite |
|--------|------------|------------|
| **Modularity** | Monolithic codebases | Clean separation: crypto / prng / payload / carriers / interfaces |
| **Interfaces** | 1 (usually GUI or CLI) | 3 (Typer CLI + Streamlit UI + FastAPI API) |
| **Language** | C++, Java, C# (hard to extend) | Python 3.11+ (accessible, large ecosystem) |
| **Testing** | Rarely tested | Dedicated test suite per module |
| **Documentation** | Minimal | PRD, Architecture, Algorithm Specs, Phase plans |

---

## Quality Metrics and Benchmarks

### Industry Standard Metrics

| Metric | What It Measures | Good Stego Target |
|--------|-----------------|-------------------|
| **PSNR** | Pixel-level fidelity (dB) | > 40 dB |
| **SSIM** | Perceptual similarity (HVS-aware) | > 0.99 |
| **MSE** | Raw distortion magnitude | < 1.0 |
| **Chi-squared p-value** | Steganographic detectability | > 0.05 (undetectable) |
| **BER** | Bit Error Rate after extraction | 0.0 (perfect recovery) |

### Cryptonite Targets vs. Competition

| Metric | Steghide | OpenStego | OpenPuff | **Cryptonite Target** |
|--------|----------|-----------|----------|----------------------|
| **PSNR** | ~38-42 dB | ~35-40 dB | Unknown | **> 40 dB** |
| **SSIM** | Unknown | Unknown | Unknown | **> 0.99** |
| **Chi-squared detection** | ~15-30% | ~40-60% | Unknown | **< 5%** |
| **JPEG DCT impact** | N/A (no JPEG) | Re-encoded | Unknown | **<= 1 per 100 coefficients** |
| **MP3 SNR** | N/A | N/A | Unknown | **> 60 dB** |

---

## Threat Model: What Steganalysis Can Detect

### Detection Tiers (hardest to easiest to detect)

```
TIER 1 — Hardest to detect
  - Adaptive LSB + PRNG scatter + small payload
  - DCT coefficient LSB with AC-only targeting
  - Echo hiding in MP3 with 5% amplitude
  Requires: Trained deep learning model (Aletheia + SRNet)

TIER 2 — Moderate difficulty
  - Flat LSB with PRNG scatter
  - JPEG re-encoded with embedded data
  - Large payload (>50% capacity)
  Detected by: Chi-squared, RS Analysis

TIER 3 — Easily detected
  - Sequential flat LSB (OpenStego, QuickStego)
  - Known tool signatures (Steghide, F5)
  - Metadata anomalies, file size increases
  Detected by: Zsteg, Stegdetect, Stegsolve, Binwalk
```

**Cryptonite operates at Tier 1** — the most resistant tier. Its combination of adaptive embedding + PRNG scatter + proper encryption makes it detectable only by purpose-trained deep learning models.

---

## Recommendations for Cryptonite Roadmap

Based on competitive gaps identified in this research:

### Phase 1 / v1 — Core Toolkit (Current Scope)
These are the features that differentiate Cryptonite from day one:
- **Military-grade Cryptography**: AES-256-CBC + HMAC-SHA256 (Encrypt-then-MAC) + PBKDF2 (600K iterations)
- **High-Entropy Position Scatter**: ChaCha20 CSPRNG permutation
- **Adaptive PNG Carrier**: Texture-aware 1-3 bit LSB allocation with Sobel gradient
- **Lossless JPEG Carrier**: Direct DCT AC-coefficient embedding via `jpegio` (no re-encoding)
- **Acoustic MP3 Carrier**: Echo hiding with autocorrelation extraction
- **Payload Compression**: Automated pre-encryption `zlib` compression with bypass fallback
- **Lossless Metadata Sanitization**: Byte-level EXIF/ID3/XMP marker stripping
- **Steganalysis Scoring Suite**: Chi-squared distribution test, SSIM fidelity scoring, and RS analysis
- **Steganographic Diff Viewer**: Visual cover vs stego comparison with bit-plane overlay & amplifications
- **Batch Processing**: Multi-file parallel embedding & extraction
- **Triple Interface**: Typer+Rich CLI, Streamlit dark-theme Web UI, and FastAPI REST API

### Phase 2 / v2 — Expanded Carriers & Deniability
- **Additional Carrier Formats**: BMP, WAV, GIF, WebP, and MP4 video carriers
- **Multi-carrier Chains**: Split large payloads across an array of independent cover files
- **Deniable Steganography**: Plausible deniability with decoy and real payloads behind distinct passphrases

### Phase 3 / v3 — Deep Learning & Anti-Forensics Research
- **Deep Learning Steganalysis**: Pre-trained SRNet / Aletheia CNN model integration for advanced detection evaluation
- **Adversarial Embedding**: GAN-assisted perturbation optimization to evade machine learning classifiers
- **Network Protocol Steganography**: Covert channels in ICMP/DNS/TCP header options
- **Physical-World Resilience**: Print/photo/scan survivable watermarking (StegaStamp-inspired)

---

## Summary

Cryptonite's position in the market can be summarized as:

> **"The tool that takes the best ideas from Steghide's graph-theory embedding, OpenPuff's multi-layer security, and modern research's adaptive algorithms — then wraps them in production-grade Python with proper cryptography, built-in steganalysis, and three interfaces. All open source."**

No existing tool combines all of Cryptonite's planned features. The closest competitor (OpenPuff) is closed-source, Windows-only, GUI-only, and offers no steganalysis scoring. The academic tools (SteganoGAN, HiDDeN) are research prototypes that lack encryption, integrity checking, and usable interfaces.

**Cryptonite fills the gap between toy tools and academic research. That's the opportunity.**
