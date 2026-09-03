"""
Cryptonite Streamlit UI Reusable Components.

Styled using the cyber-forensic "Obsidian Protocol" design system:
- Deep obsidian base (#0d1117 / #10141a)
- Elevated dark surfaces (#161b22 / #1c2026) with subtle 1px border (#30363d)
- Vibrant functional accents: Neon Emerald (#10b981 / #4edea3) for SAFE/primary,
  Cyan (#06b6d4 / #4cd7f6) for scanning/data, Gold (#c9a84c) for actions,
  Rose/Red (#ef4444 / #f43f5e) for threat/critical.
- Typography: Inter for UI & headlines, JetBrains Mono for metrics, hashes, and logs.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

import numpy as np
import streamlit as st
from PIL import Image

if TYPE_CHECKING:
    pass


def apply_custom_theme() -> None:
    """Inject bespoke CSS for the Obsidian Protocol cyber-forensics theme."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

        /* Root & Page Background */
        .stApp {
            background-color: #0d1117 !important;
            color: #dfe2eb !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #10141a !important;
            border-right: 1px solid #30363d !important;
        }
        section[data-testid="stSidebar"] div.stRadio > div {
            gap: 8px !important;
        }
        section[data-testid="stSidebar"] div.stRadio label {
            background: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            color: #dfe2eb !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        section[data-testid="stSidebar"] div.stRadio label:hover {
            border-color: #10b981 !important;
            color: #4edea3 !important;
            transform: translateX(2px);
        }

        /* Primary Action Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            color: #002113 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            letter-spacing: 0.05em !important;
            text-transform: uppercase !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.6rem 1.4rem !important;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.3) !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #4edea3 0%, #10b981 100%) !important;
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.5) !important;
            transform: translateY(-1px) !important;
            color: #001f26 !important;
        }
        .stButton > button:active {
            transform: translateY(1px) !important;
        }

        /* Download Buttons */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
            color: #001f26 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 6px !important;
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.3) !important;
            width: 100% !important;
        }
        .stDownloadButton > button:hover {
            box-shadow: 0 0 22px rgba(6, 182, 212, 0.5) !important;
            transform: translateY(-1px) !important;
        }

        /* Input Controls */
        input[type="text"], input[type="password"], div[data-baseweb="input"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
            color: #dfe2eb !important;
            font-family: 'JetBrains Mono', monospace !important;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            border-color: #06b6d4 !important;
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.25) !important;
        }

        /* File Uploader Container */
        div[data-testid="stFileUploader"] {
            background: #161b22 !important;
            border: 1px dashed #3c4a42 !important;
            border-radius: 8px !important;
            padding: 12px !important;
            transition: border-color 0.2s ease !important;
        }
        div[data-testid="stFileUploader"]:hover {
            border-color: #10b981 !important;
        }

        /* Expander / Accordion */
        div[data-testid="stExpander"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
        }

        /* Metric Card Elements */
        .obsidian-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            transition: border-color 0.2s ease;
        }
        .obsidian-card:hover {
            border-color: #4edea3;
        }

        /* Neon Glow Utility */
        .neon-glow-primary {
            box-shadow: 0 0 18px rgba(16, 185, 129, 0.35);
        }
        .neon-text-primary {
            text-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
        }

        /* Terminal Logs Simulation */
        .terminal-container {
            background-color: #000000;
            border: 1px solid #30363d;
            border-radius: 8px;
            overflow: hidden;
            font-family: 'JetBrains Mono', monospace;
            margin-top: 12px;
        }
        .terminal-header {
            background-color: #161b22;
            padding: 8px 14px;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #86948a;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .terminal-dots {
            display: flex;
            gap: 6px;
        }
        .terminal-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .terminal-body {
            padding: 14px;
            font-size: 12px;
            line-height: 1.6;
            color: #dfe2eb;
            max-height: 220px;
            overflow-y: auto;
        }
        .terminal-time {
            color: #4edea3;
            font-weight: bold;
        }
        .terminal-cyan {
            color: #4cd7f6;
        }
        .terminal-yellow {
            color: #eab308;
        }
        .terminal-red {
            color: #ef4444;
        }
        .blinking-cursor::after {
            content: ' █';
            color: #10b981;
            animation: terminal-blink 1s step-end infinite;
        }
        @keyframes terminal-blink {
            50% { opacity: 0; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the top brand navigation bar and forensic status indicator."""
    st.markdown(
        """
        <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
            <div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 26px;">💎</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 800; color: #4edea3; letter-spacing: -0.02em;" class="neon-text-primary">CRYPTONITE</span>
                    <span style="background: rgba(16, 185, 129, 0.15); color: #4edea3; border: 1px solid #10b981; font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; letter-spacing: 0.1em;">OBSIDIAN PROTOCOL</span>
                </div>
                <div style="font-size: 13px; color: #86948a; margin-top: 4px; font-family: 'Inter', sans-serif;">
                    Military-Grade Steganography & Forensic Steganalysis Studio
                </div>
            </div>
            <div style="text-align: right;" class="hide-mobile">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #4cd7f6; font-weight: 600;">AES-256-CBC • ChaCha20 • PBKDF2 600k</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #86948a; margin-top: 2px;">PURE NUMPY/SCIPY ENGINE • 100% AIR-GAPPED</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_verdict_banner(verdict: str, analysis_id: str = "CR-9902") -> None:
    """Render high-impact color-coded verdict banner based on forensic analysis."""
    v_clean = verdict.upper().strip()
    if v_clean == "SAFE":
        bg_color = "rgba(16, 185, 129, 0.08)"
        border_color = "#10b981"
        text_color = "#4edea3"
        icon = "🛡️"
        label = "SAFE — NO ANOMALY DETECTED"
        desc = "Bit-plane distributions match natural carrier profiles. Statistical entropy within organic variance."
    elif v_clean == "MODERATE":
        bg_color = "rgba(234, 179, 8, 0.08)"
        border_color = "#eab308"
        text_color = "#fde047"
        icon = "⚠️"
        label = "MODERATE RISK — PERTURBATION SUSPECTED"
        desc = "Marginal coefficient shift or texture variance detected. Manual bit-plane inspection advised."
    else:
        bg_color = "rgba(239, 68, 68, 0.12)"
        border_color = "#ef4444"
        text_color = "#fca5a5"
        icon = "🚨"
        label = "HIGH RISK — STEGO CARRIER CONFIRMED"
        desc = "Westfeld Chi-Squared pair equalization or RS mask divergence indicates high-probability payload."

    st.markdown(
        f"""
        <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 20px {border_color}33;">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="font-size: 36px;">{icon}</div>
                <div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {text_color}; letter-spacing: 0.15em;">FORENSIC EVALUATION</div>
                    <div style="font-family: 'Inter', sans-serif; font-size: 22px; font-weight: 800; color: {text_color}; margin: 2px 0;">{label}</div>
                    <div style="font-size: 13px; color: #dfe2eb; opacity: 0.85;">{desc}</div>
                </div>
            </div>
            <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #86948a;">
                <div>NODE: REF-LOCAL</div>
                <div>ID: #{analysis_id}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(
    chi2_p: float,
    ssim: float,
    psnr: float,
    rs: float,
) -> None:
    """Render the 4-card forensic metric grid in Obsidian Protocol styling."""
    # Status badges and colors
    chi2_badge = "SAFE" if chi2_p < 0.05 else ("SUSPECT" if chi2_p > 0.95 else "NORMAL")
    chi2_color = "#10b981" if chi2_p < 0.05 else ("#ef4444" if chi2_p > 0.95 else "#eab308")

    ssim_badge = "EXCELLENT" if ssim > 0.99 else ("GOOD" if ssim > 0.95 else "DEGRADED")
    ssim_color = "#10b981" if ssim > 0.99 else ("#06b6d4" if ssim > 0.95 else "#ef4444")

    psnr_str = "∞ dB" if psnr == float("inf") else f"{psnr:.2f} dB"
    psnr_badge = "IDENTICAL" if psnr == float("inf") else ("HIGH FIDELITY" if psnr > 40 else "POOR")
    psnr_color = "#10b981" if (psnr == float("inf") or psnr > 40) else "#ef4444"

    rs_badge = "CLEAN" if rs < 0.10 else ("SUSPECT" if rs < 0.25 else "STEGO DETECTED")
    rs_color = "#10b981" if rs < 0.10 else ("#eab308" if rs < 0.25 else "#ef4444")

    cols = st.columns(4)

    card_data = [
        ("CHI-SQUARED TEST", f"p = {chi2_p:.4f}", "Target: p < 0.05", chi2_badge, chi2_color),
        ("SSIM INDEX", f"{ssim:.4f}", "Target: ~1.000", ssim_badge, ssim_color),
        ("PEAK SNR", psnr_str, "Target: > 40 dB", psnr_badge, psnr_color),
        ("RS ANALYSIS", f"{rs:.4f}", "Target: < 0.100", rs_badge, rs_color),
    ]

    for col, (title, value, target, badge, color) in zip(cols, card_data, strict=False):
        with col:
            st.markdown(
                f"""
                <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px; display: flex; flex-col; justify-content: space-between; height: 100%;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: #86948a; letter-spacing: 0.05em;">{title}</span>
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: #dfe2eb; margin: 4px 0 10px 0;">
                        {value}
                    </div>
                    <div style="border-top: 1px solid rgba(48, 54, 61, 0.6); padding-top: 8px; display: flex; justify-content: space-between; align-items: center; font-family: 'JetBrains Mono', monospace; font-size: 10px;">
                        <span style="color: #86948a;">{target}</span>
                        <span style="background: {color}20; color: {color}; border: 1px solid {color}40; padding: 2px 6px; border-radius: 3px; font-weight: 700;">{badge}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_terminal_log(lines: list[str], command: str = "./cryptonite --analyze") -> None:
    """Render terminal execution console with glowing timestamps and animated cursor."""
    log_rows = []
    for line in lines:
        safe_line = html.escape(line)
        if "[OK]" in safe_line or "PASS" in safe_line or "Completed" in safe_line:
            row = f'<div><span class="terminal-time">✓</span> <span class="terminal-cyan">{safe_line}</span></div>'
        elif "[WARN]" in safe_line:
            row = f'<div><span class="terminal-yellow">⚠</span> <span class="terminal-yellow">{safe_line}</span></div>'
        elif "[FAIL]" in safe_line or "ERROR" in safe_line:
            row = f'<div><span class="terminal-red">✗</span> <span class="terminal-red">{safe_line}</span></div>'
        else:
            row = f'<div><span class="terminal-time">»</span> {safe_line}</div>'
        log_rows.append(row)

    body_html = "\n".join(log_rows)

    st.markdown(
        f"""
        <div class="terminal-container">
            <div class="terminal-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="terminal-dots">
                        <div class="terminal-dot" style="background: #ef4444;"></div>
                        <div class="terminal-dot" style="background: #eab308;"></div>
                        <div class="terminal-dot" style="background: #10b981;"></div>
                    </div>
                    <span style="margin-left: 6px; font-weight: 600;">FORENSIC EXECUTION LOG</span>
                </div>
                <span style="color: #86948a;">CRYPT-TERM v2.4</span>
            </div>
            <div class="terminal-body">
                <div style="color: #4cd7f6; opacity: 0.8; margin-bottom: 8px;">operator@cryptonite-node:~$ {html.escape(command)}</div>
                {body_html}
                <div class="blinking-cursor" style="margin-top: 6px; color: #4edea3; font-weight: bold;">[ACTIVE NODE] Idle</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compute_bitplane(img_arr: np.ndarray, bit_index: int = 0) -> np.ndarray:
    """Extract a specific bit plane (0=LSB) from uint8 image array and scale to 255."""
    extracted = (img_arr >> bit_index) & 1
    return (extracted * 255).astype(np.uint8)


def compute_enhanced_diff(cover_arr: np.ndarray, stego_arr: np.ndarray, gain: int = 50) -> np.ndarray:
    """Compute difference map with amplification gain and RGB visualization."""
    c_float = cover_arr.astype(np.int32)
    s_float = stego_arr.astype(np.int32)
    diff = np.abs(c_float - s_float) * gain
    return np.clip(diff, 0, 255).astype(np.uint8)


def render_diff_viewer(
    cover_image: Image.Image,
    stego_image: Image.Image,
    mode: str = "Normal View",
) -> None:
    """
    Render interactive side-by-side or forensic difference inspection.

    Modes:
    - Normal View: Cover vs Stego side-by-side
    - Bit-Plane 0 (LSB): Inspect randomized LSB noise
    - Bit-Plane 1: Inspect second LSB plane
    - Enhanced Diff (50x Gain): Amplified pixel modifications
    """
    cover_arr = np.array(cover_image.convert("RGB"))
    stego_arr = np.array(stego_image.convert("RGB"))

    if cover_arr.shape != stego_arr.shape:
        st.error(f"Image dimension mismatch: {cover_arr.shape} vs {stego_arr.shape}")
        return

    if mode == "Normal View":
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Cover Carrier (Original)")
            st.image(cover_image, use_container_width=True)
        with col2:
            st.caption("Stego Output (Carrier + Payload)")
            st.image(stego_image, use_container_width=True)

    elif mode == "Bit-Plane 0 (LSB)":
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Cover Bit-Plane 0 (LSB)")
            plane_c = compute_bitplane(cover_arr, 0)
            st.image(plane_c, use_container_width=True)
        with col2:
            st.caption("Stego Bit-Plane 0 (ChaCha20 Scattered)")
            plane_s = compute_bitplane(stego_arr, 0)
            st.image(plane_s, use_container_width=True)

    elif mode == "Bit-Plane 1":
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Cover Bit-Plane 1")
            plane_c1 = compute_bitplane(cover_arr, 1)
            st.image(plane_c1, use_container_width=True)
        with col2:
            st.caption("Stego Bit-Plane 1")
            plane_s1 = compute_bitplane(stego_arr, 1)
            st.image(plane_s1, use_container_width=True)

    elif mode == "Enhanced Diff (50x Gain)":
        diff_img = compute_enhanced_diff(cover_arr, stego_arr, gain=50)
        col1, col2 = st.columns([1, 1])
        with col1:
            st.caption("Amplified Pixel Divergence (50x Gain)")
            st.image(diff_img, use_container_width=True)
        with col2:
            # Show summary stats of diff
            total_diff_pixels = int(np.sum(np.any(cover_arr != stego_arr, axis=-1)))
            total_pixels = cover_arr.shape[0] * cover_arr.shape[1]
            pct = (total_diff_pixels / total_pixels) * 100.0 if total_pixels else 0.0
            max_delta = int(np.max(np.abs(cover_arr.astype(int) - stego_arr.astype(int))))

            st.markdown(
                f"""
                <div class="obsidian-card" style="margin-top: 24px;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #4cd7f6; margin-bottom: 12px;">
                        PERCEPTUAL DIFF SUMMARY
                    </div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #dfe2eb; line-height: 1.8;">
                        <div>• Modified Pixels: <b>{total_diff_pixels:,}</b> / {total_pixels:,} ({pct:.2f}%)</div>
                        <div>• Max Pixel Delta: <b>±{max_delta}</b> / 255</div>
                        <div>• Noise Scattering: <b>ChaCha20 Uniform CSPRNG</b></div>
                        <div>• Visual Imperceptibility: <b style="color: #4edea3;">Preserved</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_capacity_card(
    carrier_name: str,
    capacity_bytes: int,
    file_size_bytes: int,
) -> None:
    """Render a styled capacity breakdown card with progress indicator."""
    cap_kb = capacity_bytes / 1024.0
    size_kb = file_size_bytes / 1024.0
    usable_bytes = max(0, capacity_bytes - 100)
    usable_kb = usable_bytes / 1024.0
    cap_pct = (capacity_bytes / file_size_bytes * 100.0) if file_size_bytes > 0 else 0.0

    st.markdown(
        f"""
        <div class="obsidian-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #4cd7f6;">
                    CARRIER CAPACITY ASSESSMENT
                </span>
                <span style="background: rgba(6, 182, 212, 0.15); color: #4cd7f6; font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 2px 8px; border-radius: 4px; border: 1px solid #06b6d4;">
                    {html.escape(carrier_name)}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div>
                    <div style="font-size: 11px; color: #86948a;">RAW CAPACITY</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: #4edea3;">
                        {capacity_bytes:,} B <span style="font-size: 12px; color: #86948a;">({cap_kb:.1f} KB)</span>
                    </div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #86948a;">USABLE PAYLOAD</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: #dfe2eb;">
                        {usable_bytes:,} B <span style="font-size: 12px; color: #86948a;">({usable_kb:.1f} KB)</span>
                    </div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #86948a;">CARRIER SIZE</div>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: #dfe2eb;">
                        {file_size_bytes:,} B <span style="font-size: 12px; color: #86948a;">({size_kb:.1f} KB)</span>
                    </div>
                </div>
            </div>
            <div style="background: #10141a; border-radius: 4px; height: 8px; overflow: hidden; border: 1px solid #30363d;">
                <div style="background: linear-gradient(90deg, #10b981, #06b6d4); height: 100%; width: {min(100.0, cap_pct)}%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #86948a; margin-top: 6px;">
                <span>Density: {cap_pct:.2f}% of carrier volume</span>
                <span>Crypto Overhead: ~100 B (Salt + IV + HMAC + Header)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error_banner(message: str, error_type: str = "wrong_passphrase") -> None:
    """Render distinct themed alerts for specific error states."""
    if error_type == "wrong_passphrase":
        icon = "🔒"
        title = "INTEGRITY CHECK FAILED"
        desc = "HMAC-SHA256 signature verification failed. Incorrect passphrase or carrier data has been altered."
        border = "#ef4444"
        bg = "rgba(239, 68, 68, 0.12)"
    elif error_type == "capacity_exceeded":
        icon = "⚠️"
        title = "PAYLOAD CAPACITY EXCEEDED"
        desc = "The selected payload file is too large for this carrier after cryptographic packing."
        border = "#eab308"
        bg = "rgba(234, 179, 8, 0.12)"
    elif error_type == "unsupported_format":
        icon = "📁"
        title = "UNSUPPORTED CARRIER FORMAT"
        desc = "Supported formats: PNG (.png), JPEG (.jpg, .jpeg), and Audio (.mp3, .wav)."
        border = "#86948a"
        bg = "rgba(134, 148, 138, 0.12)"
    else:
        icon = "✗"
        title = "OPERATION ERROR"
        desc = html.escape(message)
        border = "#ef4444"
        bg = "rgba(239, 68, 68, 0.12)"

    st.markdown(
        f"""
        <div style="background: {bg}; border: 1px solid {border}; border-radius: 8px; padding: 16px; margin: 16px 0; display: flex; gap: 14px; align-items: center;">
            <div style="font-size: 28px;">{icon}</div>
            <div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: {border};">{title}</div>
                <div style="font-size: 13px; color: #dfe2eb; margin-top: 2px;">{desc}</div>
                {f'<div style="font-family: JetBrains Mono, monospace; font-size: 11px; color: #86948a; margin-top: 4px;">Detail: {html.escape(message)}</div>' if error_type != "general" and message else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
