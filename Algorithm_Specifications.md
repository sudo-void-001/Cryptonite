# Algorithm Specifications

## PBKDF2 Key Derivation
Input: passphrase (str), salt (16 random bytes)
Output: 96-byte key material
  enc_key = material[0:32]
  hmac_key = material[32:64]
  prng_seed = material[64:96]
Parameters: SHA-256, 600,000 iterations

## Adaptive LSB (PNG)
1. Load image as numpy array shape (H, W, C)
2. Compute Sobel gradient magnitude per pixel
3. Classify pixels: low (<20), medium (20-100), high (>100)
4. Assign bit depth: low=1, medium=2, high=3
5. Generate PRNG permutation of all pixel-channel indices
6. For each payload bit, take next index from permutation
7. Clear bottom N bits of that channel value (N = pixel's bit depth)
8. OR in N bits of payload

## Chi-squared Test (Steganalysis)
For each pair of values (2k, 2k+1) in the LSB plane:
  expected = (count(2k) + count(2k+1)) / 2
  chi_sq += (count(2k) - expected)^2 / expected
p_value = chi2.sf(chi_sq, degrees_of_freedom)
p < 0.05 = likely contains LSB stego data

## Echo Hiding (MP3)
Segment audio into N equal frames (N = payload bit count)
For each frame i:
  if bit == 0: add echo at delay d0 = 0.0005 * sample_rate
  if bit == 1: add echo at delay d1 = 0.001 * sample_rate
  echo amplitude = 0.05 (5% of original)
  frame[delay:] += original_frame[:-delay] * amplitude

Extraction:
For each frame:
  compute autocorrelation
  peak at d0 → bit 0, peak at d1 → bit 1