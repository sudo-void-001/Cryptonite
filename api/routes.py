"""
Cryptonite FastAPI REST Endpoints.
"""

from __future__ import annotations

import hashlib
import io
import os
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

from api.schemas import (
    BatchEmbedSummary,
    CapacityResponse,
    EmbedMetadata,
    ErrorResponse,
    ExtractMetadata,
    SteganalysisResponse,
)
from core.analysis import full_analysis
from core.carriers.jpeg import JpegCarrier
from core.carriers.mp3 import Mp3Carrier
from core.carriers.png import PngCarrier
from core.compression import compress, decompress
from core.crypto import (
    compute_hmac,
    derive_keys,
    encrypt,
    pack_encrypted_blob,
    unpack_encrypted_blob,
    verify_and_decrypt,
)
from core.payload import pack, unpack

# --- Config ---
CORS_ORIGINS = os.getenv("CRYPTONITE_CORS_ORIGINS", "*").split(",")
MAX_UPLOAD_MB = int(os.getenv("CRYPTONITE_MAX_UPLOAD_MB", "50"))

app = FastAPI(
    title="Cryptonite REST API",
    description="Production-grade steganography toolkit API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helpers ---
_PRNG_FIXED_SALT: bytes = b"cryptonite-cli-prng-v1\x00\x00\x00\x00\x00"[:16]
_PNG_EXTS = frozenset({".png"})
_JPEG_EXTS = frozenset({".jpg", ".jpeg"})
_MP3_EXTS = frozenset({".mp3", ".wav"})


def _get_carrier(filename: str) -> Any:
    ext = Path(filename).suffix.lower()
    if ext in _PNG_EXTS:
        return PngCarrier()
    if ext in _JPEG_EXTS:
        return JpegCarrier()
    if ext in _MP3_EXTS:
        return Mp3Carrier()
    return None


def _derive_prng_seed(passphrase: str) -> bytes:
    _, _, prng_seed = derive_keys(passphrase, _PRNG_FIXED_SALT)
    return prng_seed


def _encrypt_payload_bytes(passphrase: str, filename: str, raw_payload: bytes) -> bytes:
    compressed, was_compressed = compress(raw_payload)
    packed = pack(filename, compressed, is_compressed=was_compressed)

    enc_salt = os.urandom(16)
    enc_key, hmac_key, _ = derive_keys(passphrase, enc_salt)
    iv, ciphertext = encrypt(packed, enc_key)
    hmac_digest = compute_hmac(iv + ciphertext, hmac_key)
    return pack_encrypted_blob(enc_salt, iv, hmac_digest, ciphertext)


def _decrypt_blob_bytes(passphrase: str, blob: bytes) -> tuple[str, bytes]:
    enc_salt, iv, hmac_digest, ciphertext = unpack_encrypted_blob(blob)
    enc_key, hmac_key, _ = derive_keys(passphrase, enc_salt)
    plaintext = verify_and_decrypt(iv, ciphertext, enc_key, hmac_key, hmac_digest)
    filename, data, is_compressed = unpack(plaintext)
    data = decompress(data, is_compressed)
    return filename, data


def _human_bytes(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024.0:
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"


def _check_size(content: bytes) -> None:
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_MB}MB",
        )


# --- Exception Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail, error_code=str(exc.status_code)
        ).model_dump(),
    )


# --- Endpoints ---
@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "cryptonite"}


@app.post("/capacity", response_model=CapacityResponse)
async def get_capacity(file: UploadFile = File(...)) -> CapacityResponse:
    content = await file.read()
    _check_size(content)

    c_obj = _get_carrier(file.filename or "")
    if not c_obj:
        raise HTTPException(status_code=400, detail="Unsupported carrier format")

    ext = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cap = c_obj.capacity(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    usable = max(0, cap - 100)
    return CapacityResponse(
        carrier_filename=file.filename or "unknown",
        carrier_type=type(c_obj).__name__,
        capacity_bytes=cap,
        capacity_human=_human_bytes(cap),
        usable_bytes=usable,
        file_size_bytes=len(content),
    )


@app.post("/embed")
async def embed(
    carrier: UploadFile = File(...),
    payload: UploadFile = File(...),
    passphrase: str = Form(...),
) -> Response:
    t0 = time.time()
    carrier_bytes = await carrier.read()
    payload_bytes = await payload.read()
    _check_size(carrier_bytes)

    c_obj = _get_carrier(carrier.filename or "")
    if not c_obj:
        raise HTTPException(status_code=400, detail="Unsupported carrier format")

    try:
        blob = _encrypt_payload_bytes(passphrase, payload.filename or "payload.bin", payload_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {e}") from e

    ext = Path(carrier.filename or "").suffix
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(carrier_bytes)
        tmp_path = tmp.name

    try:
        cap = c_obj.capacity(tmp_path)
        if len(blob) > cap:
            raise HTTPException(status_code=413, detail=f"Payload encrypted size ({len(blob)}B) exceeds capacity ({cap}B)")

        prng_seed = _derive_prng_seed(passphrase)
        stego_bytes = c_obj.embed(tmp_path, blob, prng_seed)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}") from e
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    elapsed = time.time() - t0
    meta = EmbedMetadata(
        carrier_filename=carrier.filename or "unknown",
        payload_filename=payload.filename or "unknown",
        blob_bytes=len(blob),
        capacity_bytes=cap,
        capacity_used_pct=(len(blob) / cap * 100) if cap > 0 else 0.0,
        elapsed_s=elapsed,
    )

    mime = "image/png" if ext in _PNG_EXTS else ("image/jpeg" if ext in _JPEG_EXTS else "audio/wav")

    headers = {
        "X-Embed-Metadata": meta.model_dump_json(),
        "Content-Disposition": f'attachment; filename="stego_{carrier.filename}"',
    }
    return Response(content=stego_bytes, media_type=mime, headers=headers)


@app.post("/extract")
async def extract(
    stego: UploadFile = File(...),
    passphrase: str = Form(...),
) -> Response:
    t0 = time.time()
    stego_bytes = await stego.read()
    _check_size(stego_bytes)

    c_obj = _get_carrier(stego.filename or "")
    if not c_obj:
        raise HTTPException(status_code=400, detail="Unsupported carrier format")

    ext = Path(stego.filename or "").suffix
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(stego_bytes)
        tmp_path = tmp.name

    try:
        prng_seed = _derive_prng_seed(passphrase)
        blob = c_obj.extract(tmp_path, prng_seed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    try:
        orig_filename, recovered_bytes = _decrypt_blob_bytes(passphrase, blob)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {e}")

    elapsed = time.time() - t0
    meta = ExtractMetadata(
        recovered_filename=orig_filename,
        recovered_bytes=len(recovered_bytes),
        sha256=hashlib.sha256(recovered_bytes).hexdigest(),
        elapsed_s=elapsed,
    )

    headers = {
        "X-Extract-Metadata": meta.model_dump_json(),
        "Content-Disposition": f'attachment; filename="{orig_filename}"',
    }
    return Response(content=recovered_bytes, media_type="application/octet-stream", headers=headers)


@app.post("/analyze", response_model=SteganalysisResponse)
async def analyze(
    cover: UploadFile = File(...),
    stego: UploadFile = File(...),
) -> SteganalysisResponse:
    cover_bytes = await cover.read()
    stego_bytes = await stego.read()
    _check_size(cover_bytes)
    _check_size(stego_bytes)

    try:
        c_img = Image.open(io.BytesIO(cover_bytes)).convert("RGB")
        s_img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {e}")

    c_arr = np.array(c_img)
    s_arr = np.array(s_img)

    if c_arr.shape != s_arr.shape:
        raise HTTPException(
            status_code=400,
            detail=f"Image dimension mismatch: Cover {c_arr.shape} vs Stego {s_arr.shape}",
        )

    res = full_analysis(c_arr, s_arr)
    return SteganalysisResponse(
        chi_squared_p_value=res.chi_squared_p_value,
        ssim_score=res.ssim_score,
        rs_score=res.rs_score,
        psnr_db=res.psnr_db,
        verdict=res.verdict,
        is_suspicious=(res.verdict != "SAFE"),
    )


@app.post("/batch/embed")
async def batch_embed(
    archive: UploadFile = File(...),
    payload: UploadFile = File(...),
    passphrase: str = Form(...),
) -> Response:
    archive_bytes = await archive.read()
    payload_bytes = await payload.read()
    _check_size(archive_bytes)
    _check_size(payload_bytes)

    try:
        blob = _encrypt_payload_bytes(passphrase, payload.filename or "payload.bin", payload_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {e}") from e

    prng_seed = _derive_prng_seed(passphrase)

    in_zip = io.BytesIO(archive_bytes)
    out_zip = io.BytesIO()

    total = 0
    succeeded = 0
    failed = 0
    failed_files = []

    try:
        with zipfile.ZipFile(in_zip, "r") as z_in, zipfile.ZipFile(out_zip, "w") as z_out:
            for item in z_in.infolist():
                if item.is_dir():
                    continue

                total += 1
                c_obj = _get_carrier(item.filename)
                if not c_obj:
                    failed += 1
                    failed_files.append(f"{item.filename} (unsupported)")
                    continue

                carrier_bytes = z_in.read(item.filename)
                ext = Path(item.filename).suffix
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(carrier_bytes)
                    tmp_path = tmp.name

                try:
                    cap = c_obj.capacity(tmp_path)
                    if len(blob) > cap:
                        failed += 1
                        failed_files.append(f"{item.filename} (capacity)")
                    else:
                        stego_bytes = c_obj.embed(tmp_path, blob, prng_seed)
                        out_name = f"stego_{Path(item.filename).name}"
                        z_out.writestr(out_name, stego_bytes)
                        succeeded += 1
                except Exception as e:
                    failed += 1
                    failed_files.append(f"{item.filename} ({e})")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip archive")

    meta = BatchEmbedSummary(
        total=total,
        succeeded=succeeded,
        failed=failed,
        failed_files=failed_files,
    )

    headers = {
        "X-Batch-Metadata": meta.model_dump_json(),
        "Content-Disposition": 'attachment; filename="stego_batch.zip"',
    }

    return Response(content=out_zip.getvalue(), media_type="application/zip", headers=headers)
