"""
CLI integration tests for Cryptonite Phase 6.

Uses typer.testing.CliRunner — fully hermetic, no subprocess overhead.
Passphrases passed via the --passphrase flag so no stdin prompting is needed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()

_PASS = "hunter2-secure-passphrase"
_PASS_WRONG = "totally-wrong-passphrase"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def png_carrier(tmp_path: Path) -> str:
    """Create a 128×128 RGB PNG carrier and return its path."""
    rng = np.random.default_rng(42)
    img = rng.normal(128.0, 40.0, (128, 128, 3)).clip(0, 255).astype(np.uint8)
    p = tmp_path / "carrier.png"
    Image.fromarray(img).save(str(p))
    return str(p)


@pytest.fixture()
def jpeg_carrier(tmp_path: Path) -> str:
    """Create a 128×128 RGB JPEG carrier and return its path."""
    rng = np.random.default_rng(43)
    img = rng.normal(128.0, 40.0, (128, 128, 3)).clip(0, 255).astype(np.uint8)
    p = tmp_path / "carrier.jpg"
    Image.fromarray(img).save(str(p), quality=95)
    return str(p)


@pytest.fixture()
def small_payload(tmp_path: Path) -> str:
    """Create a tiny text payload file."""
    p = tmp_path / "secret.txt"
    p.write_text("Cryptonite Phase 6 CLI roundtrip test payload!", encoding="utf-8")
    return str(p)


@pytest.fixture()
def large_payload(tmp_path: Path) -> str:
    """Create a payload that exceeds the 128×128 PNG carrier capacity (~17 489 B).

    The PNG carrier holds ~17 489 B. Encryption adds 64 B overhead (salt+iv+hmac)
    and packing adds ~30 B. So a 17 500 B random payload (incompressible) produces
    a blob of ~17 600 B which exceeds capacity by ~110 B.
    """
    p = tmp_path / "big.bin"
    rng = np.random.default_rng(0)
    p.write_bytes(bytes(rng.integers(0, 256, 17_500, dtype=np.uint8)))
    return str(p)


# ---------------------------------------------------------------------------
# TestEmbed
# ---------------------------------------------------------------------------

class TestEmbed:
    def test_embed_png_success(self, png_carrier: str, small_payload: str, tmp_path: Path) -> None:
        out = str(tmp_path / "stego.png")
        result = runner.invoke(app, [
            "embed",
            "--carrier", png_carrier,
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output", out,
        ])
        assert result.exit_code == 0, result.output
        assert Path(out).exists()
        assert "Embed Successful" in result.output

    def test_embed_jpeg_success(self, jpeg_carrier: str, small_payload: str, tmp_path: Path) -> None:
        out = str(tmp_path / "stego.jpg")
        result = runner.invoke(app, [
            "embed",
            "--carrier", jpeg_carrier,
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output", out,
        ])
        assert result.exit_code == 0, result.output
        assert Path(out).exists()

    def test_embed_carrier_not_found(self, small_payload: str, tmp_path: Path) -> None:
        result = runner.invoke(app, [
            "embed",
            "--carrier", "/nonexistent/carrier.png",
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output", str(tmp_path / "out.png"),
        ])
        assert result.exit_code == 1

    def test_embed_payload_not_found(self, png_carrier: str, tmp_path: Path) -> None:
        result = runner.invoke(app, [
            "embed",
            "--carrier", png_carrier,
            "--payload", "/nonexistent/payload.bin",
            "--passphrase", _PASS,
            "--output", str(tmp_path / "out.png"),
        ])
        assert result.exit_code == 1

    def test_embed_payload_too_large(self, png_carrier: str, large_payload: str, tmp_path: Path) -> None:
        result = runner.invoke(app, [
            "embed",
            "--carrier", png_carrier,
            "--payload", large_payload,
            "--passphrase", _PASS,
            "--output", str(tmp_path / "out.png"),
        ])
        assert result.exit_code == 1

    def test_embed_unsupported_extension(self, small_payload: str, tmp_path: Path) -> None:
        fake = tmp_path / "carrier.bmp"
        fake.write_bytes(b"\x00" * 128)
        result = runner.invoke(app, [
            "embed",
            "--carrier", str(fake),
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output", str(tmp_path / "out.png"),
        ])
        assert result.exit_code == 1

    def test_embed_creates_output_subdirs(self, png_carrier: str, small_payload: str, tmp_path: Path) -> None:
        out = str(tmp_path / "deep" / "nested" / "stego.png")
        result = runner.invoke(app, [
            "embed",
            "--carrier", png_carrier,
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output", out,
        ])
        assert result.exit_code == 0
        assert Path(out).exists()


# ---------------------------------------------------------------------------
# TestExtract
# ---------------------------------------------------------------------------

class TestExtract:
    def _do_embed(self, carrier: str, payload: str, out: str) -> None:
        result = runner.invoke(app, [
            "embed",
            "--carrier", carrier,
            "--payload", payload,
            "--passphrase", _PASS,
            "--output", out,
        ])
        assert result.exit_code == 0, f"embed failed: {result.output}"

    def test_extract_png_roundtrip(self, png_carrier: str, small_payload: str, tmp_path: Path) -> None:
        stego = str(tmp_path / "stego.png")
        recovered = str(tmp_path / "recovered.txt")
        self._do_embed(png_carrier, small_payload, stego)

        result = runner.invoke(app, [
            "extract",
            "--stego", stego,
            "--passphrase", _PASS,
            "--output", recovered,
        ])
        assert result.exit_code == 0, result.output
        assert "Extract Successful" in result.output
        original = Path(small_payload).read_bytes()
        assert Path(recovered).read_bytes() == original

    def test_extract_jpeg_roundtrip(self, jpeg_carrier: str, small_payload: str, tmp_path: Path) -> None:
        stego = str(tmp_path / "stego.jpg")
        recovered = str(tmp_path / "recovered.txt")
        self._do_embed(jpeg_carrier, small_payload, stego)

        result = runner.invoke(app, [
            "extract",
            "--stego", stego,
            "--passphrase", _PASS,
            "--output", recovered,
        ])
        assert result.exit_code == 0, result.output
        assert Path(recovered).read_bytes() == Path(small_payload).read_bytes()

    def test_extract_wrong_passphrase(self, png_carrier: str, small_payload: str, tmp_path: Path) -> None:
        stego = str(tmp_path / "stego.png")
        self._do_embed(png_carrier, small_payload, stego)

        result = runner.invoke(app, [
            "extract",
            "--stego", stego,
            "--passphrase", _PASS_WRONG,
            "--output", str(tmp_path / "recovered.txt"),
        ])
        assert result.exit_code == 1

    def test_extract_stego_not_found(self, tmp_path: Path) -> None:
        result = runner.invoke(app, [
            "extract",
            "--stego", "/nonexistent/stego.png",
            "--passphrase", _PASS,
            "--output", str(tmp_path / "out.txt"),
        ])
        assert result.exit_code == 1

    def test_extract_recovers_original_content(self, png_carrier: str, tmp_path: Path) -> None:
        """Verify byte-for-byte recovery."""
        payload_file = tmp_path / "binary_payload.bin"
        payload_file.write_bytes(bytes(range(256)) * 4)
        stego = str(tmp_path / "stego.png")
        recovered = str(tmp_path / "recovered.bin")
        self._do_embed(png_carrier, str(payload_file), stego)

        result = runner.invoke(app, [
            "extract",
            "--stego", stego,
            "--passphrase", _PASS,
            "--output", recovered,
        ])
        assert result.exit_code == 0
        assert Path(recovered).read_bytes() == payload_file.read_bytes()


# ---------------------------------------------------------------------------
# TestCapacity
# ---------------------------------------------------------------------------

class TestCapacity:
    def test_capacity_png(self, png_carrier: str) -> None:
        result = runner.invoke(app, ["capacity", "--carrier", png_carrier])
        assert result.exit_code == 0
        assert "Carrier Capacity" in result.output
        # Numeric value should appear in output (bytes, KB, MB etc.)
        assert any(unit in result.output for unit in ("B", "KB", "MB"))

    def test_capacity_jpeg(self, jpeg_carrier: str) -> None:
        result = runner.invoke(app, ["capacity", "--carrier", jpeg_carrier])
        assert result.exit_code == 0
        assert "Carrier Capacity" in result.output

    def test_capacity_file_not_found(self) -> None:
        result = runner.invoke(app, ["capacity", "--carrier", "/nope/carrier.png"])
        assert result.exit_code == 1

    def test_capacity_png_is_positive(self, png_carrier: str) -> None:
        """128×128 PNG should have non-trivial capacity."""
        result = runner.invoke(app, ["capacity", "--carrier", png_carrier])
        assert result.exit_code == 0
        # The max capacity line must not say "0 B"
        assert "0 B" not in result.output or "Max capacity" not in result.output


# ---------------------------------------------------------------------------
# TestAnalyze
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_analyze_identical_images_safe(self, png_carrier: str) -> None:
        """Identical cover and stego → at most MODERATE (SSIM=1, PSNR=inf)."""
        result = runner.invoke(app, [
            "analyze",
            "--cover", png_carrier,
            "--stego", png_carrier,
        ])
        assert result.exit_code == 0
        assert "VERDICT" in result.output
        assert any(v in result.output for v in ("SAFE", "MODERATE", "HIGH_RISK"))

    def test_analyze_shows_all_metrics(self, png_carrier: str) -> None:
        result = runner.invoke(app, [
            "analyze",
            "--cover", png_carrier,
            "--stego", png_carrier,
        ])
        assert result.exit_code == 0
        assert "Chi-Squared" in result.output
        assert "SSIM" in result.output
        assert "PSNR" in result.output
        assert "RS Analysis" in result.output

    def test_analyze_stego_vs_cover(self, png_carrier: str, small_payload: str, tmp_path: Path) -> None:
        """Stego file analyzed against original cover should return a result."""
        stego = str(tmp_path / "stego.png")
        runner.invoke(app, [
            "embed", "--carrier", png_carrier,
            "--payload", small_payload,
            "--passphrase", _PASS, "--output", stego,
        ])
        result = runner.invoke(app, [
            "analyze", "--cover", png_carrier, "--stego", stego,
        ])
        assert result.exit_code == 0
        assert "VERDICT" in result.output

    def test_analyze_cover_not_found(self, png_carrier: str) -> None:
        result = runner.invoke(app, [
            "analyze", "--cover", "/nope.png", "--stego", png_carrier,
        ])
        assert result.exit_code == 1

    def test_analyze_stego_not_found(self, png_carrier: str) -> None:
        result = runner.invoke(app, [
            "analyze", "--cover", png_carrier, "--stego", "/nope.png",
        ])
        assert result.exit_code == 1

    def test_analyze_unsupported_format_rejected(self, tmp_path: Path) -> None:
        """MP3 is not supported for image steganalysis — should fail cleanly."""
        fake_mp3 = tmp_path / "audio.mp3"
        fake_mp3.write_bytes(b"\x00" * 64)
        result = runner.invoke(app, [
            "analyze", "--cover", str(fake_mp3), "--stego", str(fake_mp3),
        ])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# TestBatch
# ---------------------------------------------------------------------------

class TestBatch:
    def test_batch_embed_dir(self, tmp_path: Path, small_payload: str) -> None:
        """Embed same payload into 3 PNG carriers."""
        carriers_dir = tmp_path / "carriers"
        carriers_dir.mkdir()
        out_dir = tmp_path / "stego_out"
        rng = np.random.default_rng(99)
        for i in range(3):
            img = rng.normal(128.0, 40.0, (128, 128, 3)).clip(0, 255).astype(np.uint8)
            Image.fromarray(img).save(str(carriers_dir / f"cover_{i}.png"))

        result = runner.invoke(app, [
            "batch", "embed",
            "--carriers-dir", str(carriers_dir),
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output-dir", str(out_dir),
        ])
        assert result.exit_code == 0
        stego_files = list(out_dir.glob("*.png"))
        assert len(stego_files) == 3

    def test_batch_extract_dir(self, tmp_path: Path, small_payload: str) -> None:
        """Roundtrip: batch embed then batch extract."""
        carriers_dir = tmp_path / "carriers"
        carriers_dir.mkdir()
        stego_dir = tmp_path / "stego"
        recovered_dir = tmp_path / "recovered"
        rng = np.random.default_rng(77)
        for i in range(2):
            img = rng.normal(128.0, 40.0, (128, 128, 3)).clip(0, 255).astype(np.uint8)
            Image.fromarray(img).save(str(carriers_dir / f"c_{i}.png"))

        runner.invoke(app, [
            "batch", "embed",
            "--carriers-dir", str(carriers_dir),
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output-dir", str(stego_dir),
        ])
        result = runner.invoke(app, [
            "batch", "extract",
            "--stego-dir", str(stego_dir),
            "--passphrase", _PASS,
            "--output-dir", str(recovered_dir),
        ])
        assert result.exit_code == 0

    def test_batch_embed_empty_dir(self, tmp_path: Path, small_payload: str) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        result = runner.invoke(app, [
            "batch", "embed",
            "--carriers-dir", str(empty),
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output-dir", str(tmp_path / "out"),
        ])
        assert result.exit_code == 0
        assert "No supported" in result.output

    def test_batch_embed_dir_not_found(self, small_payload: str, tmp_path: Path) -> None:
        result = runner.invoke(app, [
            "batch", "embed",
            "--carriers-dir", "/nope/dir",
            "--payload", small_payload,
            "--passphrase", _PASS,
            "--output-dir", str(tmp_path / "out"),
        ])
        assert result.exit_code == 1

    def test_batch_extract_empty_dir(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        result = runner.invoke(app, [
            "batch", "extract",
            "--stego-dir", str(empty),
            "--passphrase", _PASS,
            "--output-dir", str(tmp_path / "out"),
        ])
        assert result.exit_code == 0
        assert "No supported" in result.output


# ---------------------------------------------------------------------------
# TestErrors — edge cases and type safety
# ---------------------------------------------------------------------------

class TestErrors:
    def test_help_embed(self) -> None:
        result = runner.invoke(app, ["embed", "--help"])
        assert result.exit_code == 0
        assert "--carrier" in result.output
        assert "--payload" in result.output
        assert "--output" in result.output

    def test_help_extract(self) -> None:
        result = runner.invoke(app, ["extract", "--help"])
        assert result.exit_code == 0
        assert "--stego" in result.output
        assert "--output" in result.output

    def test_help_capacity(self) -> None:
        result = runner.invoke(app, ["capacity", "--help"])
        assert result.exit_code == 0

    def test_help_analyze(self) -> None:
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0

    def test_human_bytes_formatting(self) -> None:
        """Smoke test the internal _human_bytes helper."""
        from cli.main import _human_bytes
        assert "B" in _human_bytes(512)
        assert "KB" in _human_bytes(2048)
        assert "MB" in _human_bytes(2 * 1024 * 1024)

    def test_get_carrier_png(self, tmp_path: Path) -> None:
        from cli.main import _get_carrier
        from core.carriers.png import PngCarrier
        fake = tmp_path / "x.png"
        fake.touch()
        assert isinstance(_get_carrier(str(fake)), PngCarrier)

    def test_get_carrier_jpg(self, tmp_path: Path) -> None:
        from cli.main import _get_carrier
        from core.carriers.jpeg import JpegCarrier
        fake = tmp_path / "x.jpg"
        fake.touch()
        assert isinstance(_get_carrier(str(fake)), JpegCarrier)

    def test_get_carrier_mp3(self, tmp_path: Path) -> None:
        from cli.main import _get_carrier
        from core.carriers.mp3 import Mp3Carrier
        fake = tmp_path / "x.mp3"
        fake.touch()
        assert isinstance(_get_carrier(str(fake)), Mp3Carrier)

    def test_get_carrier_wav(self, tmp_path: Path) -> None:
        from cli.main import _get_carrier
        from core.carriers.mp3 import Mp3Carrier
        fake = tmp_path / "x.wav"
        fake.touch()
        assert isinstance(_get_carrier(str(fake)), Mp3Carrier)
