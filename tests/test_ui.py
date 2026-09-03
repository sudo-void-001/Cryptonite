"""
Automated Test Suite for Cryptonite Web UI (Phase 7 Streamlit).

Covers:
- Streamlit headless AppTest initialization and mode navigation.
- Component rendering tests for Obsidian Protocol design elements.
- Bit-plane slicing and enhanced difference mathematical fidelity.
- End-to-end cryptographic and carrier interoperability between UI and CLI.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

from cli.main import _derive_prng_seed as cli_derive_prng_seed
from core.carriers.jpeg import JpegCarrier
from core.carriers.mp3 import Mp3Carrier
from core.carriers.png import PngCarrier
from ui.app import (
    decrypt_blob_bytes,
    derive_prng_seed,
    encrypt_payload_bytes,
    get_carrier_for_filename,
)
from ui.components import (
    compute_bitplane,
    compute_enhanced_diff,
    render_capacity_card,
    render_diff_viewer,
    render_error_banner,
    render_header,
    render_metric_cards,
    render_terminal_log,
    render_verdict_banner,
)

# ===========================================================================
# 1. Streamlit Headless AppTest
# ===========================================================================

class TestUIApp:
    def test_app_init(self) -> None:
        """Streamlit application initializes without any unhandled exceptions."""
        at = AppTest.from_file("ui/app.py")
        at.run(timeout=30)
        assert len(at.exception) == 0, f"App crashed on startup: {at.exception}"

    def test_sidebar_navigation_options(self) -> None:
        """Verify the sidebar navigation radio renders with all 5 operational modes."""
        at = AppTest.from_file("ui/app.py")
        at.run(timeout=30)
        assert len(at.sidebar.radio) >= 1
        radio = at.sidebar.radio[0]
        expected_options = [
            "🔒 Embed Carrier",
            "🔓 Extract Secret",
            "🔍 Steganalysis Lab",
            "📦 Capacity Inspector",
            "👁️ Diff & Bit-Planes",
        ]
        assert radio.options == expected_options

    @pytest.mark.parametrize(
        "mode_name",
        [
            "🔒 Embed Carrier",
            "🔓 Extract Secret",
            "🔍 Steganalysis Lab",
            "📦 Capacity Inspector",
            "👁️ Diff & Bit-Planes",
        ],
    )
    def test_switch_modes_cleanly(self, mode_name: str) -> None:
        """Verify each operational mode loads and renders without exceptions."""
        at = AppTest.from_file("ui/app.py")
        at.run(timeout=30)
        at.sidebar.radio[0].set_value(mode_name).run(timeout=30)
        assert len(at.exception) == 0, f"Exception in mode {mode_name}: {at.exception}"


# ===========================================================================
# 2. Reusable Component Tests
# ===========================================================================

class TestUIComponents:
    def test_compute_bitplane(self) -> None:
        """Verify LSB plane extraction isolates the 0th bit and scales to 0/255."""
        arr = np.array([[0, 1], [2, 3]], dtype=np.uint8)
        plane0 = compute_bitplane(arr, bit_index=0)
        expected0 = np.array([[0, 255], [0, 255]], dtype=np.uint8)
        np.testing.assert_array_equal(plane0, expected0)

        plane1 = compute_bitplane(arr, bit_index=1)
        expected1 = np.array([[0, 0], [255, 255]], dtype=np.uint8)
        np.testing.assert_array_equal(plane1, expected1)

    def test_compute_enhanced_diff(self) -> None:
        """Verify difference calculation amplifies differences by the specified gain."""
        cover = np.array([[[100, 100, 100]]], dtype=np.uint8)
        stego = np.array([[[101, 100, 98]]], dtype=np.uint8)
        diff = compute_enhanced_diff(cover, stego, gain=50)

        # Delta is: R=1*50=50, G=0, B=2*50=100
        assert diff[0, 0, 0] == 50
        assert diff[0, 0, 1] == 0
        assert diff[0, 0, 2] == 100

    def test_render_diff_viewer_shapes(self) -> None:
        """Verify render_diff_viewer works across all visual inspection modes."""
        rng = np.random.default_rng(42)
        c_arr = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
        s_arr = c_arr.copy()
        s_arr[0, 0, 0] = (s_arr[0, 0, 0] ^ 1)  # 1 bit modification

        c_img = Image.fromarray(c_arr)
        s_img = Image.fromarray(s_arr)

        for mode in ["Normal View", "Bit-Plane 0 (LSB)", "Bit-Plane 1", "Enhanced Diff (50x Gain)"]:
            render_diff_viewer(c_img, s_img, mode=mode)

    def test_render_diff_viewer_mismatch(self) -> None:
        """Verify dimension mismatch is safely handled."""
        c_img = Image.new("RGB", (32, 32))
        s_img = Image.new("RGB", (64, 64))
        render_diff_viewer(c_img, s_img, mode="Normal View")

    def test_render_verdict_banners(self) -> None:
        """Verify verdict banners execute cleanly for SAFE, MODERATE, and HIGH_RISK."""
        for v in ["SAFE", "MODERATE", "HIGH_RISK", "UNKNOWN"]:
            render_verdict_banner(v, analysis_id="TEST-01")

    def test_render_metric_cards(self) -> None:
        """Verify metric card grid renders standard numerical values and infinity PSNR."""
        render_metric_cards(chi2_p=0.012, ssim=0.9995, psnr=float("inf"), rs=0.035)
        render_metric_cards(chi2_p=0.985, ssim=0.8800, psnr=28.4, rs=0.340)

    def test_render_terminal_log(self) -> None:
        """Verify terminal logger renders status rows and tags."""
        logs = [
            "[OK] Subsystem initialized",
            "[WARN] Marginal texture detected",
            "[FAIL] Packet dropped",
            "General diagnostic message",
        ]
        render_terminal_log(logs, command="./cryptonite --test")

    def test_render_capacity_card(self) -> None:
        """Verify capacity card calculation and display."""
        render_capacity_card("sample.png", capacity_bytes=16384, file_size_bytes=65536)

    def test_render_error_banners(self) -> None:
        """Verify error banners execute for all specialized error types."""
        for err_type in ["wrong_passphrase", "capacity_exceeded", "unsupported_format", "general"]:
            render_error_banner("Sample error description", error_type=err_type)

    def test_render_header(self) -> None:
        """Verify top header renders cleanly."""
        render_header()


# ===========================================================================
# 3. Interoperability & Crypto Tests
# ===========================================================================

class TestUIInteroperability:
    def test_derive_prng_seed_matches_cli(self) -> None:
        """Verify PRNG seed derivation in UI is identical to CLI for scatter synchrony."""
        passphrase = "test-synchronization-passphrase"
        ui_seed = derive_prng_seed(passphrase)
        cli_seed = cli_derive_prng_seed(passphrase)
        assert ui_seed == cli_seed
        assert len(ui_seed) == 32

    def test_encrypt_decrypt_payload_bytes_roundtrip(self) -> None:
        """Verify in-memory payload encryption, packing, and decryption roundtrip."""
        passphrase = "alpha-bravo-charlie"
        raw_data = b"Secret payload content to test UI in-memory cryptographic pipeline."
        orig_name = "classified_intel.txt"

        blob = encrypt_payload_bytes(passphrase, orig_name, raw_data)
        assert isinstance(blob, bytes)
        assert len(blob) > len(raw_data)

        rec_name, rec_data = decrypt_blob_bytes(passphrase, blob)
        assert rec_name == orig_name
        assert rec_data == raw_data

    def test_decrypt_wrong_passphrase_raises(self) -> None:
        """Verify wrong passphrase in UI decrypt triggers HMAC verification failure."""
        passphrase = "correct-passphrase"
        blob = encrypt_payload_bytes(passphrase, "file.bin", b"Some confidential data")

        with pytest.raises(ValueError, match="HMAC verification failed"):
            decrypt_blob_bytes("incorrect-passphrase", blob)

    def test_get_carrier_for_filename(self) -> None:
        """Verify carrier selection correctly routes file extensions."""
        assert isinstance(get_carrier_for_filename("photo.png"), PngCarrier)
        assert isinstance(get_carrier_for_filename("image.jpg"), JpegCarrier)
        assert isinstance(get_carrier_for_filename("image.jpeg"), JpegCarrier)
        assert isinstance(get_carrier_for_filename("audio.mp3"), Mp3Carrier)
        assert isinstance(get_carrier_for_filename("sound.wav"), Mp3Carrier)
        assert get_carrier_for_filename("document.pdf") is None
        assert get_carrier_for_filename("archive.zip") is None
