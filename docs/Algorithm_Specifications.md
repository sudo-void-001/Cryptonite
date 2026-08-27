# Algorithm Specifications

## PBKDF2 Key Derivation
- Input: passphrase (str), salt (16 random bytes)
- Output: 96-byte key material → enc_key[0:32], hmac_key[32:64], prng_seed[64:96]
- Parameters: SHA-256, 600,000 iterations

## Payload Compression
- Algorithm: zlib (RFC 1950)
- Level: 6 (default), configurable 1-9
- Applied BEFORE header packing so the header version byte accurately reflects compression status
- Header version byte bit 7: 0 = uncompressed, 1 = compressed
- Fallback: if `len(compressed_data) >= len(raw_data)`, store raw payload and set bit 7 = 0
- Decompression: header unpack checks bit 7; if set (1), `zlib.decompress()` payload after AES decryption

## Adaptive LSB (PNG)
- Step 1: Convert image to grayscale for texture analysis
- Step 2: Apply Sobel edge filter to find texture gradients
- Step 3: Classify pixels: 1-bit low-texture, 2-bit medium, 3-bit high-texture
- Step 4: Generate ChaCha20 PRNG permutation of pixel positions
- Step 5: Read payload bits according to pixel capacity
- Step 6: Perform LSB replacement
- Step 7: Apply Euler graph matching to minimize pixel changes
- Step 8: Write back modified pixels
- Step 9: After embedding, run SSIM check: if SSIM < 0.99, reduce bit depth by 1 level and re-embed
- Capacity formula: sum over all pixels of (bit_depth[pixel] * num_channels) / 8 bytes

## JPEG DCT Coefficient Embedding
- Step 1: Load JPEG via jpegio.read() → access raw DCT coefficient arrays
- Step 2: For each 8x8 block, identify embeddable coefficients: AC only (skip [0,0] DC), abs(value) > 1
- Step 3: Generate PRNG permutation of all embeddable coefficient indices
- Step 4: For each payload bit, take next coefficient from permutation
- Step 5: Modify LSB of coefficient value, preserving sign: if coeff > 0: coeff = (coeff & ~1) | bit; if coeff < 0: coeff = -(abs(coeff) & ~1) | bit)
- Step 6: Write modified coefficients back via jpegio.write() — no re-encoding
- Capacity formula: count of coefficients where abs(val) > 1 and position != [0,0], divided by 8 bytes
- Quality constraint: modify at most 1 coefficient per 100 total coefficients

## Echo Hiding (MP3)
- Segment, delays d0=0.5ms bit 0, d1=1.0ms bit 1, amplitude 0.05, autocorrelation extraction
- Add capacity formula: floor(total_samples / segment_size) bits, where segment_size = sample_rate * 0.05 (50ms segments)

## Chi-Squared Test (Steganalysis)
- Current formula for LSB pair analysis
- Add interpretation: p > 0.05 → SAFE (no detectable stego), p 0.01-0.05 → MODERATE, p < 0.01 → HIGH RISK

## RS Analysis
- Divide image into groups of n consecutive pixels (n=4 default)
- Define flipping function F: flip LSB of each pixel in group
- Compute discrimination function f: variation across group (sum of absolute differences)
- Classify groups: Regular (f increases after flip), Singular (f decreases), Unusable (no change)
- Metric: RS_ratio = |R_m - R_-m| / (R_m + R_-m) where R_m = regular groups under mask m, R_-m = regular under inverse mask
- Score < 0.1 → clean, Score > 0.3 → likely contains stego data

## SSIM Calculation
- Formula: SSIM(x,y) = ((2*mu_x*mu_y + C1) * (2*sigma_xy + C2)) / ((mu_x^2 + mu_y^2 + C1) * (sigma_x^2 + sigma_y^2 + C2))
- C1 = (K1*L)^2 where K1=0.01, L=255
- C2 = (K2*L)^2 where K2=0.03, L=255
- Computed per-channel, averaged across 11x11 Gaussian-weighted windows
- Target: SSIM > 0.99 for all carrier types

## PSNR Calculation
- MSE = (1/MN) * sum((cover[i,j] - stego[i,j])^2)
- PSNR = 10 * log10(MAX^2 / MSE) where MAX=255 for 8-bit images
- Target: PSNR > 40 dB

## Metadata Sanitization
- PNG: Remove ancillary chunks (tEXt, iTXt, zTXt, eXIf, tIME, gAMA, cHRM, sRGB, iCCP, sBIT, bKGD, hIST, pHYs, sPLT) while preserving critical chunks (IHDR, PLTE, IDAT, IEND, tRNS)
- JPEG: Losslessly strip APP markers (APP1 EXIF, APP2 ICC/FlashPix, APP13 IPTC, APP14 Adobe) and COM comments at the binary/stream level — NEVER re-encode via PIL
- MP3: Strip ID3v1 (last 128 bytes starting with 'TAG'), ID3v2 (header at file start), and APE tags while preserving audio frame integrity

## Capacity Calculation Summary
- Table: Carrier | Formula | Example (1920x1080 image / 5min audio)
- PNG: sum(bit_depth_per_pixel * channels) / 8. Example: ~700KB for 1920x1080 RGB
- JPEG: count(AC coefficients where abs > 1) / 8. Example: ~50KB for typical 1920x1080 JPEG
- MP3: floor(total_samples / segment_size) / 8. Example: ~3KB for 5-min 44.1KHz audio