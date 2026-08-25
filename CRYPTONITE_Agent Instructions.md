# CRYPTONITE — Agent Instructions

## Project
Cryptonite: a production-grade steganography tool supporting PNG, JPEG, MP3.
Monetized via SaaS API. CLI for power users. Web UI via Streamlit.

## Stack
- Python 3.11+
- cryptography (AES-256-CBC, PBKDF2, HMAC)
- numpy, Pillow (PNG)
- jpegio (JPEG DCT access — NOT PIL for JPEG)
- pydub + ffmpeg (MP3)
- FastAPI, Streamlit, typer, rich

## Non-negotiables
- NEVER use MD5 for key derivation. Always PBKDF2-HMAC-SHA256, 600k iterations.
- ALWAYS encrypt-then-MAC. Never MAC-then-encrypt.
- NEVER re-encode JPEG through PIL — use jpegio to modify DCT coefficients directly.
- All functions must have type hints and docstrings.
- Every module must have a corresponding test file.

## File structure
[paste the directory tree here]

## Current phase
[UPDATE THIS every session — e.g. "Phase 2: PNG carrier. crypto.py is complete and tested."]

## What's done
[UPDATE THIS — bullet list of completed + tested modules]

## What's next
[UPDATE THIS — the specific deliverable for this session]