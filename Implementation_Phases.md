# Implementation Phases

## Phase 1 — Crypto Engine
**Files:** core/crypto.py, core/prng.py, core/payload.py
**Tests:** tests/test_crypto.py

Acceptance criteria:
- [ ] encrypt(decrypt(data)) == data for arbitrary byte strings
- [ ] Two identical passphrases + same salt produce identical keys
- [ ] Two different salts produce different keys
- [ ] HMAC verification fails if ciphertext is modified by 1 bit
- [ ] PRNG produces same permutation given same seed and length
- [ ] PRNG produces different permutation given different seed
- [ ] payload.pack(payload.unpack(data)) == data roundtrip
- [ ] All functions have type hints and docstrings

## Phase 2 — PNG Carrier
**Files:** core/carriers/png.py
**Tests:** tests/test_png.py

Acceptance criteria:
- [ ] embed(extract(cover, payload)) == payload for files up to capacity
- [ ] Output PSNR > 40dB vs cover
- [ ] Embedded file passes basic Chi-squared test (detection score < 0.05)
- [ ] capacity() returns correct byte count
- [ ] Raises clear error if payload exceeds capacity

[continue for each phase...]