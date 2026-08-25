# Architecture

## Data flow — embed path
passphrase + salt → PBKDF2 → (enc_key, hmac_key, prng_seed)
payload → header pack → AES-256-CBC encrypt → HMAC append
→ carrier-specific embedder → stego file

## Data flow — extract path
stego file → carrier-specific extractor → raw bytes
→ HMAC verify → AES decrypt → header unpack → payload file

## Payload header format
[magic: 4B "STGC"][version: 1B][filename_len: 2B]
[filename: NB][payload_size: 8B][payload_bytes: NB]

## Key derivation
- Algorithm: PBKDF2-HMAC-SHA256
- Iterations: 600,000
- Salt: 16 bytes random, stored in stego file header
- Output: 96 bytes split as enc_key[0:32], hmac_key[32:64], prng_seed[64:96]

## Encrypted blob format (written to stego file)
[salt: 16B][iv: 16B][hmac: 32B][ciphertext: variable]

## PNG embedding strategy
- Adaptive LSB: 1-bit in low-texture regions, up to 3-bit in high-texture
- Texture detection: Sobel edge filter via numpy
- Position selection: ChaCha20 PRNG permutation of pixel coordinates
- Graph pairing: Euler matching to minimise total pixel changes

## JPEG embedding strategy
- Access layer: jpegio (raw DCT coefficient access, no re-encode)
- Skip: coefficients where abs(val) <= 1 and DC coefficients (position [0,0] of each block)
- Embed: LSB of AC coefficients, sign-preserving
- Position order: PRNG permutation of embeddable coefficient indices

## MP3 embedding strategy
- Primary: echo hiding (d0=0.5ms for bit 0, d1=1.0ms for bit 1, amplitude=0.05)
- Secondary: ID3 custom tag for small payloads (< 1KB)
- Extraction: autocorrelation per segment, peak at d0 vs d1

## Module boundaries (what each file owns)
- crypto.py: ONLY key derivation, encryption, HMAC. No file I/O.
- prng.py: ONLY position generation. Takes seed + capacity, returns permutation.
- payload.py: ONLY header pack/unpack, capacity calculation.
- carriers/*.py: ONLY file I/O and bit embedding/extraction. Calls crypto and prng.
- cli/main.py: ONLY user interface. No business logic.
- api/routes.py: ONLY HTTP layer. No business logic.

## Key decisions and reasons
- PBKDF2 over scrypt: broader library support, deterministic on all platforms
- jpegio over PIL: PIL re-encodes JPEG on save, destroying DCT-level edits
- ChaCha20 PRNG over Mersenne Twister: cryptographically secure, unpredictable positions
- Encrypt-then-MAC over authenticated encryption (GCM): explicit HMAC easier to audit