"""
Cryptonite Streamlit Web Application — Phase 7 Production Implementation.

Cyber-forensic steganography & steganalysis workbench.
Features 5 interactive operational modes:
1. 🔒 Embed: Hide encrypted payload inside PNG, JPEG, or MP3 carriers.
2. 🔓 Extract: Extract and decrypt hidden payload with HMAC integrity verification.
3. 🔍 Steganalysis Lab: Multi-vector forensic inspection (Chi-squared, SSIM, PSNR, RS).
4. 📦 Capacity Inspector: Carrier byte budget analysis and density calculations.
5. 👁️ Diff & Bit-Planes: Forensic side-by-side bit-plane slicing and 50x amplified diff.
"""

from __future__ import annotations

import hashlib
import io
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

from core.analysis import (
    chi_squared_test,
    full_analysis,
    rs_analysis,
)
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
from ui.components import (
    apply_custom_theme,
    render_capacity_card,
    render_diff_viewer,
    render_error_banner,
    render_header,
    render_metric_cards,
    render_terminal_log,
    render_verdict_banner,
)

# ---------------------------------------------------------------------------
# Constants & Interoperability
# ---------------------------------------------------------------------------

_PRNG_FIXED_SALT: bytes = b"cryptonite-cli-prng-v1\x00\x00\x00\x00\x00"[:16]
_PNG_EXTS = frozenset({".png"})
_JPEG_EXTS = frozenset({".jpg", ".jpeg"})
_MP3_EXTS = frozenset({".mp3", ".wav"})


def derive_prng_seed(passphrase: str) -> bytes:
    """Derive deterministic PRNG seed for carrier scattering (matches CLI)."""
    _enc_key, _hmac_key, prng_seed = derive_keys(passphrase, _PRNG_FIXED_SALT)
    return prng_seed


def encrypt_payload_bytes(passphrase: str, filename: str, raw_payload: bytes) -> bytes:
    """Run full compression + packing + AES-256-CBC + HMAC-SHA256 pipeline."""
    compressed, was_compressed = compress(raw_payload)
    packed = pack(filename, compressed, is_compressed=was_compressed)

    enc_salt = os.urandom(16)
    enc_key, hmac_key, _prng = derive_keys(passphrase, enc_salt)
    iv, ciphertext = encrypt(packed, enc_key)
    hmac_digest = compute_hmac(iv + ciphertext, hmac_key)
    return pack_encrypted_blob(enc_salt, iv, hmac_digest, ciphertext)


def decrypt_blob_bytes(passphrase: str, blob: bytes) -> tuple[str, bytes]:
    """Unpack blob + verify HMAC + decrypt AES-256-CBC + decompress."""
    enc_salt, iv, hmac_digest, ciphertext = unpack_encrypted_blob(blob)
    enc_key, hmac_key, _prng = derive_keys(passphrase, enc_salt)
    plaintext = verify_and_decrypt(iv, ciphertext, enc_key, hmac_key, hmac_digest)
    filename, data, is_compressed = unpack(plaintext)
    data = decompress(data, is_compressed)
    return filename, data


def get_carrier_for_filename(filename: str):  # type: ignore[return]
    """Return appropriate carrier instance based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext in _PNG_EXTS:
        return PngCarrier()
    if ext in _JPEG_EXTS:
        return JpegCarrier()
    if ext in _MP3_EXTS:
        return Mp3Carrier()
    return None


# ---------------------------------------------------------------------------
# Streamlit App Execution
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cryptonite | Steganography & Steganalysis Studio",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_theme()
render_header()

# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #86948a; letter-spacing: 0.1em; margin-bottom: 8px;">
            OPERATIONAL MODE
        </div>
        """,
        unsafe_allow_html=True,
    )
    mode = st.radio(
        label="Mode Selection",
        options=[
            "🔒 Embed Carrier",
            "🔓 Extract Secret",
            "🔍 Steganalysis Lab",
            "📦 Capacity Inspector",
            "👁️ Diff & Bit-Planes",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        """
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #86948a; line-height: 1.8;">
            <div><b>ENGINE:</b> Cryptonite v0.1.0</div>
            <div><b>CIPHER:</b> AES-256-CBC</div>
            <div><b>MAC:</b> HMAC-SHA256</div>
            <div><b>KDF:</b> PBKDF2 (600k iter)</div>
            <div><b>PRNG:</b> ChaCha20 Scatter</div>
            <div><b>AUDIO:</b> LPC Echo Hiding</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# 1. EMBED CARRIER MODE
# ===========================================================================

if mode == "🔒 Embed Carrier":
    col_left, col_right = st.columns([4, 6], gap="large")

    with col_left:
        st.markdown(
            """
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #4edea3; margin-bottom: 12px;">
                » CARRIER & PAYLOAD SELECTION
            </div>
            """,
            unsafe_allow_html=True,
        )

        carrier_file = st.file_uploader(
            "Upload Cover Carrier (PNG, JPG, JPEG, MP3, WAV)",
            type=["png", "jpg", "jpeg", "mp3", "wav"],
            key="embed_carrier",
        )

        payload_file = st.file_uploader(
            "Upload Secret Payload (Any file)",
            key="embed_payload",
        )

        passphrase = st.text_input(
            "Secret Cryptographic Passphrase",
            type="password",
            placeholder="Enter high-entropy passphrase...",
            key="embed_passphrase",
            help="Derives 256-bit AES key, 256-bit HMAC key, and ChaCha20 scatter seed via PBKDF2-HMAC-SHA256.",
        )

        embed_btn = st.button("EXECUTE EMBED & ENCRYPT", use_container_width=True)

    with col_right:
        if not carrier_file:
            st.info("Upload a cover carrier image or audio file to begin.")
        else:
            carrier_obj = get_carrier_for_filename(carrier_file.name)
            if carrier_obj is None:
                render_error_banner(f"Unsupported file format: {carrier_file.name}", "unsupported_format")
            else:
                # Calculate carrier capacity using a temporary file
                carrier_bytes = carrier_file.getvalue()
                with tempfile.NamedTemporaryFile(suffix=Path(carrier_file.name).suffix, delete=False) as tmp_c:
                    tmp_c.write(carrier_bytes)
                    tmp_c_path = tmp_c.name

                try:
                    cap = carrier_obj.capacity(tmp_c_path)
                finally:
                    if os.path.exists(tmp_c_path):
                        os.unlink(tmp_c_path)

                render_capacity_card(carrier_file.name, cap, len(carrier_bytes))

                if embed_btn:
                    if not payload_file:
                        st.warning("Please upload a payload file to embed.")
                    elif not passphrase:
                        st.warning("Please enter a secret passphrase.")
                    else:
                        payload_bytes = payload_file.getvalue()
                        with st.spinner("Deriving keys and encrypting payload..."):
                            t0 = time.time()
                            try:
                                blob = encrypt_payload_bytes(passphrase, payload_file.name, payload_bytes)
                            except Exception as err:
                                render_error_banner(f"Encryption failed: {err}", "general")
                                blob = None

                        if blob is not None:
                            if len(blob) > cap:
                                render_error_banner(
                                    f"Encrypted blob is {len(blob):,} bytes, but carrier only holds {cap:,} bytes.",
                                    "capacity_exceeded",
                                )
                            else:
                                with st.spinner("Embedding into carrier with ChaCha20 scattering..."):
                                    prng_seed = derive_prng_seed(passphrase)
                                    with tempfile.NamedTemporaryFile(suffix=Path(carrier_file.name).suffix, delete=False) as tmp_in:
                                        tmp_in.write(carrier_bytes)
                                        tmp_in_path = tmp_in.name

                                    try:
                                        stego_bytes = carrier_obj.embed(tmp_in_path, blob, prng_seed)
                                        success = True
                                    except Exception as e:
                                        render_error_banner(f"Embedding error: {e}", "general")
                                        success = False
                                    finally:
                                        if os.path.exists(tmp_in_path):
                                            os.unlink(tmp_in_path)

                                if success:
                                    elapsed = time.time() - t0
                                    st.success(f"Payload embedded successfully in {elapsed:.2f}s!")

                                    # Stego Download Button
                                    out_name = f"stego_{carrier_file.name}"
                                    mime = "image/png" if carrier_file.name.lower().endswith(".png") else (
                                        "image/jpeg" if carrier_file.name.lower().endswith((".jpg", ".jpeg")) else "audio/wav"
                                    )
                                    st.download_button(
                                        label=f"💾 DOWNLOAD STEGO FILE ({len(stego_bytes):,} B)",
                                        data=stego_bytes,
                                        file_name=out_name,
                                        mime=mime,
                                        use_container_width=True,
                                    )

                                    # For image carriers, calculate perceptual quality metrics
                                    ext = Path(carrier_file.name).suffix.lower()
                                    if ext in _PNG_EXTS | _JPEG_EXTS:
                                        try:
                                            cover_img = Image.open(io.BytesIO(carrier_bytes)).convert("RGB")
                                            stego_img = Image.open(io.BytesIO(stego_bytes)).convert("RGB")
                                            cover_arr = np.array(cover_img)
                                            stego_arr = np.array(stego_img)

                                            result = full_analysis(cover_arr, stego_arr)
                                            st.markdown("---")
                                            render_verdict_banner(result.verdict)
                                            render_metric_cards(
                                                result.chi_squared_p_value,
                                                result.ssim_score,
                                                result.psnr_db,
                                                result.rs_score,
                                            )
                                        except Exception as analysis_err:
                                            st.caption(f"Forensic metrics calculation skipped: {analysis_err}")

                                    # Execution Terminal
                                    render_terminal_log(
                                        [
                                            f"[OK] Payload '{payload_file.name}' compressed and packed",
                                            "[OK] PBKDF2 600,000 rounds derived key material for AES-256-CBC",
                                            f"[OK] Encrypted blob created: {len(blob):,} bytes with HMAC-SHA256 tag",
                                            f"[OK] ChaCha20 scattering completed into {carrier_file.name}",
                                            f"[OK] Output stego generated: {len(stego_bytes):,} bytes in {elapsed:.2f}s",
                                        ],
                                        command=f"./cryptonite embed --carrier {carrier_file.name} --payload {payload_file.name}",
                                    )


# ===========================================================================
# 2. EXTRACT SECRET MODE
# ===========================================================================

elif mode == "🔓 Extract Secret":
    col_left, col_right = st.columns([4, 6], gap="large")

    with col_left:
        st.markdown(
            """
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #4edea3; margin-bottom: 12px;">
                » STEGO CARRIER EXTRACTION
            </div>
            """,
            unsafe_allow_html=True,
        )

        stego_file = st.file_uploader(
            "Upload Stego Carrier File",
            type=["png", "jpg", "jpeg", "mp3", "wav"],
            key="extract_stego",
        )

        extract_passphrase = st.text_input(
            "Secret Passphrase",
            type="password",
            placeholder="Enter passphrase used during embedding...",
            key="extract_passphrase",
        )

        extract_btn = st.button("EXTRACT & DECRYPT PAYLOAD", use_container_width=True)

    with col_right:
        if not stego_file:
            st.info("Upload an encoded stego carrier file and provide the secret passphrase.")
        elif extract_btn:
            if not extract_passphrase:
                st.warning("Please enter the passphrase.")
            else:
                c_obj = get_carrier_for_filename(stego_file.name)
                if c_obj is None:
                    render_error_banner(f"Unsupported format: {stego_file.name}", "unsupported_format")
                else:
                    with st.spinner("Extracting hidden data and verifying cryptographic integrity..."):
                        t0 = time.time()
                        prng_seed = derive_prng_seed(extract_passphrase)
                        stego_bytes = stego_file.getvalue()

                        with tempfile.NamedTemporaryFile(suffix=Path(stego_file.name).suffix, delete=False) as tmp_stego:
                            tmp_stego.write(stego_bytes)
                            tmp_stego_path = tmp_stego.name

                        try:
                            blob = c_obj.extract(tmp_stego_path, prng_seed)
                            extract_err = None
                        except Exception as e:
                            blob = None
                            extract_err = e
                        finally:
                            if os.path.exists(tmp_stego_path):
                                os.unlink(tmp_stego_path)

                        if blob is None:
                            render_error_banner(f"Extraction failed: {extract_err}", "general")
                        else:
                            try:
                                orig_filename, recovered_bytes = decrypt_blob_bytes(extract_passphrase, blob)
                                decrypt_err = None
                            except ValueError as ve:
                                orig_filename, recovered_bytes = "", b""
                                decrypt_err = ve
                            except Exception as e:
                                orig_filename, recovered_bytes = "", b""
                                decrypt_err = e

                            elapsed = time.time() - t0
                            if decrypt_err is not None:
                                render_error_banner(str(decrypt_err), "wrong_passphrase")
                                render_terminal_log(
                                    [
                                        f"Extracting carrier from {stego_file.name}...",
                                        "[FAIL] HMAC-SHA256 verification failed",
                                        "Integrity check rejected: Passphrase incorrect or file corrupted",
                                    ],
                                    command=f"./cryptonite extract --stego {stego_file.name}",
                                )
                            else:
                                st.success(f"Payload successfully decrypted in {elapsed:.2f}s!")
                                sha = hashlib.sha256(recovered_bytes).hexdigest()

                                st.markdown(
                                    f"""
                                    <div class="obsidian-card">
                                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #4edea3; margin-bottom: 8px;">
                                            ✓ PAYLOAD INTEGRITY VERIFIED
                                        </div>
                                        <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #dfe2eb; line-height: 1.8;">
                                            <div>• Recovered Filename: <b>{orig_filename}</b></div>
                                            <div>• Extracted Size: <b>{len(recovered_bytes):,} bytes</b></div>
                                            <div>• SHA-256 Checksum: <span style="color: #4cd7f6;">{sha[:32]}...</span></div>
                                            <div>• Authentication: <span style="color: #10b981;">HMAC-SHA256 Validated</span></div>
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.download_button(
                                    label=f"💾 DOWNLOAD RECOVERED FILE ({orig_filename})",
                                    data=recovered_bytes,
                                    file_name=orig_filename,
                                    use_container_width=True,
                                )

                                render_terminal_log(
                                    [
                                        f"[OK] Raw encrypted blob extracted: {len(blob):,} bytes",
                                        "[OK] HMAC-SHA256 signature verified against ciphertext",
                                        "[OK] AES-256-CBC plaintext decrypted and unpadded",
                                        f"[OK] Payload decompressed: '{orig_filename}' ({len(recovered_bytes):,} B)",
                                    ],
                                    command=f"./cryptonite extract --stego {stego_file.name}",
                                )


# ===========================================================================
# 3. STEGANALYSIS LAB MODE
# ===========================================================================

elif mode == "🔍 Steganalysis Lab":
    st.markdown(
        """
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #4edea3; margin-bottom: 14px;">
            » MULTI-VECTOR STEGANOGRAPHY INSPECTOR
        </div>
        """,
        unsafe_allow_html=True,
    )

    scan_type = st.radio(
        "Analysis Type",
        ["Differential (Cover vs Stego) — Full Forensic Suite", "Blind Inspection (Single Image) — Chi-Squared & RS"],
        horizontal=True,
    )

    if "Differential" in scan_type:
        c1, c2 = st.columns(2)
        with c1:
            cover_upload = st.file_uploader("Original Cover Image (PNG / JPEG)", type=["png", "jpg", "jpeg"], key="lab_cover")
        with c2:
            stego_upload = st.file_uploader("Suspect Stego Image (PNG / JPEG)", type=["png", "jpg", "jpeg"], key="lab_stego")

        if cover_upload and stego_upload:
            if st.button("RUN FULL FORENSIC EVALUATION", use_container_width=True):
                with st.spinner("Computing Westfeld Chi-Squared, Wang SSIM, PSNR, and Fridrich RS analysis..."):
                    c_img = Image.open(cover_upload).convert("RGB")
                    s_img = Image.open(stego_upload).convert("RGB")
                    c_arr = np.array(c_img)
                    s_arr = np.array(s_img)

                    if c_arr.shape != s_arr.shape:
                        st.error(f"Image dimension mismatch: Cover {c_arr.shape} vs Stego {s_arr.shape}")
                    else:
                        result = full_analysis(c_arr, s_arr)
                        render_verdict_banner(result.verdict)
                        render_metric_cards(
                            result.chi_squared_p_value,
                            result.ssim_score,
                            result.psnr_db,
                            result.rs_score,
                        )

                        with st.expander("🔬 Theoretical Metric Thresholds & Details", expanded=False):
                            st.markdown(
                                """
                                - **Westfeld & Pfitzmann Chi-Squared**: Evaluates Pair of Values (PoV) distribution equalisation.
                                  Natural images maintain unequal frequencies (*p* < 0.05). Stego replacement equalises pairs (*p* > 0.95).
                                - **Wang et al. SSIM (2004)**: Measures structural degradation using an 11×11 Gaussian window.
                                  Values > 0.99 indicate near-flawless perceptual preservation.
                                - **Peak Signal-to-Noise Ratio (PSNR)**: Logarithmic MSE metric in dB. Values > 40 dB are imperceptible to the human eye.
                                - **Fridrich et al. RS Analysis**: Dual-mask spatial correlation test. Clean images score < 0.10; modified LSB planes elevate > 0.25.
                                """
                            )

                        render_terminal_log(
                            [
                                f"[OK] Dimensions verified: {c_arr.shape[1]}x{c_arr.shape[0]} RGB pixels",
                                f"[OK] Wang SSIM 11x11 Gaussian kernel score: {result.ssim_score:.6f}",
                                f"[OK] Peak SNR computed: {result.psnr_db:.2f} dB",
                                f"[OK] Westfeld chi2 survival p-value: {result.chi_squared_p_value:.6f}",
                                f"[OK] Fridrich RS discrepancy: {result.rs_score:.6f}",
                                f"[OK] Final automated verdict: {result.verdict}",
                            ],
                            command="./cryptonite analyze --cover original.png --stego test.png",
                        )

    else:
        single_upload = st.file_uploader("Upload Image for Blind Analysis", type=["png", "jpg", "jpeg"], key="blind_upload")
        if single_upload:
            if st.button("RUN BLIND FORENSIC PROBE", use_container_width=True):
                with st.spinner("Analyzing bit-plane distributions..."):
                    img = Image.open(single_upload).convert("RGB")
                    arr = np.array(img)
                    p_val = chi_squared_test(arr)
                    rs_val = rs_analysis(arr)

                    blind_verdict = "HIGH_RISK" if (p_val > 0.95 or rs_val > 0.30) else (
                        "MODERATE" if (p_val > 0.50 or rs_val > 0.15) else "SAFE"
                    )

                    render_verdict_banner(blind_verdict)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Chi-Squared p-value", f"{p_val:.4f}", help="Low p (<0.05) is clean. High p (>0.95) indicates equalized stego.")
                    with col_b:
                        st.metric("RS Analysis Discrepancy", f"{rs_val:.4f}", help="Score < 0.10 is clean. Score > 0.25 indicates LSB tampering.")


# ===========================================================================
# 4. CAPACITY INSPECTOR MODE
# ===========================================================================

elif mode == "📦 Capacity Inspector":
    st.markdown(
        """
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #4edea3; margin-bottom: 14px;">
            » CARRIER CAPACITY & OVERHEAD ANALYZER
        </div>
        """,
        unsafe_allow_html=True,
    )

    cap_file = st.file_uploader(
        "Upload Media Carrier (PNG, JPG, JPEG, MP3, WAV)",
        type=["png", "jpg", "jpeg", "mp3", "wav"],
        key="capacity_uploader",
    )

    if cap_file:
        c_inst = get_carrier_for_filename(cap_file.name)
        if c_inst is None:
            render_error_banner(f"Unsupported format: {cap_file.name}", "unsupported_format")
        else:
            raw_data = cap_file.getvalue()
            with tempfile.NamedTemporaryFile(suffix=Path(cap_file.name).suffix, delete=False) as tmp_f:
                tmp_f.write(raw_data)
                tmp_f_path = tmp_f.name

            try:
                max_cap = c_inst.capacity(tmp_f_path)
            finally:
                if os.path.exists(tmp_f_path):
                    os.unlink(tmp_f_path)

            render_capacity_card(cap_file.name, max_cap, len(raw_data))

            st.markdown(
                """
                <div class="obsidian-card">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #4cd7f6; margin-bottom: 8px;">
                        ALGORITHM TECHNICAL SPECS
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #dfe2eb; line-height: 1.8;">
                        <div>• <b>PNG (Adaptive LSB)</b>: Sobel gradient analysis on MSBs dynamically assigns 1 to 3 bits per channel.</div>
                        <div>• <b>JPEG (Quantized DCT)</b>: Zero-DC preservation; modifies non-zero high-frequency AC coefficients only.</div>
                        <div>• <b>MP3/WAV (Echo Hiding)</b>: 50ms dual-delay echo kernels (d0=0.5ms, d1=1.0ms) with LPC whitening.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ===========================================================================
# 5. DIFF & BIT-PLANES MODE
# ===========================================================================

elif mode == "👁️ Diff & Bit-Planes":
    st.markdown(
        """
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #4edea3; margin-bottom: 14px;">
            » STEGANOGRAPHIC DIFF & BIT-PLANE INSPECTION
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        diff_cover = st.file_uploader("Original Cover Image", type=["png", "jpg", "jpeg"], key="diff_cover_up")
    with col2:
        diff_stego = st.file_uploader("Stego Output Image", type=["png", "jpg", "jpeg"], key="diff_stego_up")

    if diff_cover and diff_stego:
        view_mode = st.radio(
            "Visualization Inspection Filter",
            ["Normal View", "Bit-Plane 0 (LSB)", "Bit-Plane 1", "Enhanced Diff (50x Gain)"],
            horizontal=True,
        )

        c_img = Image.open(diff_cover)
        s_img = Image.open(diff_stego)
        render_diff_viewer(c_img, s_img, mode=view_mode)
    else:
        st.info("Upload both cover and stego images to explore side-by-side bit-plane slices.")
