#  Product Requirements

## Problem
[1 paragraph: what problem does this solve, who has this problem]

## Users
- Security researchers
- CTF competitors
- Journalists / activists needing covert comms
- Photographers wanting invisible watermarks
- SOC analysts detecting hidden data

## Core features (must-have)
- Embed arbitrary payload into PNG, JPEG, MP3
- Extract payload given stego file + passphrase
- AES-256-CBC encryption of payload before embedding
- HMAC-SHA256 integrity verification
- PRNG-based position scatter (passphrase-seeded)
- Capacity estimation per file
- Steganalysis detection score

## Out of scope (explicitly)
- Video carriers (future version)
- BMP, WAV, GIF (future)
- Real-time streaming
- Mobile app

## Success metrics
- PSNR > 40dB for PNG output
- JPEG DCT changes ≤ 1 per 100 coefficients
- MP3 SNR > 60dB
- Chi-squared detection probability < 5% on output files
- API response time < 3s for files under 10MB

## Monetization tiers
[paste the tier structure]