"""
Unit tests for Cryptonite MP3 Carrier (Acoustic Echo Hiding) and
strip_mp3_metadata (Lossless ID3/APE Tag Sanitization).
"""

import struct
from pathlib import Path

import numpy as np
import pytest
from pydub import AudioSegment

from core.carriers.base import BaseCarrier
from core.carriers.mp3 import (
    BASE_ALPHA,
    D0_SECONDS,
    D1_SECONDS,
    LPC_ORDER,
    SAMPLE_RATE,
    SEG_DURATION_S,
    Mp3Carrier,
    _audio_to_mono_f32,
    _compute_echo_params,
    _compute_lpc,
    _embed_bit_into_segment,
    _extract_bit_from_segment,
    _f32_to_audio,
)
from core.metadata import strip_mp3_metadata

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tone_wav(
    path: Path,
    duration_s: float = 5.0,
    sample_rate: int = SAMPLE_RATE,
    freqs: tuple[float, ...] = (330.0, 550.0, 1100.0),
) -> Path:
    """Generate a richly-textured polyphonic WAV file with noise for testing."""
    n = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    signal = sum(
        a * np.sin(2 * np.pi * f * t)
        for a, f in zip((0.40, 0.30, 0.20), freqs, strict=True)
    )
    signal += 0.10 * np.random.default_rng(42).standard_normal(n)
    signal = (signal / np.max(np.abs(signal)) * 0.9 * 32767).astype(np.int16)
    audio = AudioSegment(signal.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1)
    audio.export(str(path), format="wav")
    return path


def _make_id3v2_tag(size: int = 16, has_footer: bool = False) -> bytes:
    """Synthesize a minimal ID3v2 header + payload."""
    flags = 0x10 if has_footer else 0x00
    s = size
    synchsafe = bytes([
        (s >> 21) & 0x7F,
        (s >> 14) & 0x7F,
        (s >> 7) & 0x7F,
        s & 0x7F,
    ])
    header = b"ID3\x03\x00" + bytes([flags]) + synchsafe
    payload = b"\x00" * size
    footer = b"3DI\x03\x00" + bytes([flags]) + synchsafe if has_footer else b""
    return header + payload + footer


def _make_id3v1_tag() -> bytes:
    """Synthesize a fixed 128-byte ID3v1 tag."""
    return b"TAG" + b"A" * 30 + b"B" * 30 + b"C" * 30 + b"\x00" * 35


def _make_ape_footer(ape_payload_size: int = 0, has_header: bool = False) -> bytes:
    """Synthesize an APE footer (32 bytes) with optional header."""
    ape_version = struct.pack("<I", 2000)
    total_tag_size = ape_payload_size + 32 + (32 if has_header else 0)
    ape_size = struct.pack("<I", total_tag_size)
    item_count = struct.pack("<I", 0)
    flags_val = (1 << 31) if has_header else 0
    flags = struct.pack("<I", flags_val)
    reserved = b"\x00" * 8
    footer = b"APETAGEX" + ape_version + ape_size + item_count + flags + reserved
    header = footer if has_header else b""
    return header + (b"\x00" * ape_payload_size) + footer


# ---------------------------------------------------------------------------
# Module-level constant smoke tests
# ---------------------------------------------------------------------------

def test_constants_are_spec_compliant():
    """Verify echo hiding constants match Algorithm_Specifications.md."""
    assert D0_SECONDS == 0.0005
    assert D1_SECONDS == 0.0010
    assert BASE_ALPHA <= 0.05
    assert SEG_DURATION_S == 0.05
    assert SAMPLE_RATE == 44100


def test_compute_echo_params():
    """Verify computed delay samples match spec at standard sample rates."""
    seg, k0, k1 = _compute_echo_params(44100)
    assert seg == 2205
    assert k0 == 22   # 0.5 ms × 44100
    assert k1 == 44   # 1.0 ms × 44100

    seg8, k0_8, k1_8 = _compute_echo_params(8000)
    assert k0_8 == max(int(round(8000 * 0.0005)), 1)
    assert k1_8 == max(int(round(8000 * 0.0010)), 2)


# ---------------------------------------------------------------------------
# Internal helper unit tests
# ---------------------------------------------------------------------------

def test_compute_lpc_flat_signal():
    """LPC on a zero (or near-zero) segment returns zeros safely."""
    a = _compute_lpc(np.zeros(256, dtype=np.float32), order=LPC_ORDER)
    assert a.shape == (LPC_ORDER,)
    assert not np.any(np.isnan(a))
    assert not np.any(np.isinf(a))


def test_compute_lpc_sinusoid():
    """LPC coefficients should be non-trivial on a rich sinusoid."""
    t = np.linspace(0, 0.05, 2205, endpoint=False)
    seg = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    a = _compute_lpc(seg, order=LPC_ORDER)
    assert a.shape == (LPC_ORDER,)
    assert np.any(a != 0.0)


def test_embed_and_extract_all_bits():
    """Single-segment embed/extract must be 100% correct for all bit values."""
    t = np.linspace(0, SEG_DURATION_S, int(SAMPLE_RATE * SEG_DURATION_S), endpoint=False)
    seg = (
        0.4 * np.sin(2 * np.pi * 330 * t) +
        0.3 * np.sin(2 * np.pi * 550 * t) +
        0.2 * np.sin(2 * np.pi * 1100 * t) +
        0.1 * np.random.default_rng(7).standard_normal(len(t))
    ).astype(np.float32)

    seg_len, k0, k1 = _compute_echo_params(SAMPLE_RATE)

    for bit in (0, 1):
        stego_seg = _embed_bit_into_segment(seg[:seg_len], bit, k0, k1)
        extracted = _extract_bit_from_segment(stego_seg, k0, k1)
        assert extracted == bit, f"Expected bit {bit}, got {extracted}"


def test_audio_f32_conversion_roundtrip():
    """Audio → float32 → AudioSegment conversion preserves dimensions."""
    t = np.linspace(0, 1.0, SAMPLE_RATE, endpoint=False)
    samples = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    audio = AudioSegment(samples.tobytes(), frame_rate=SAMPLE_RATE, sample_width=2, channels=1)

    f32 = _audio_to_mono_f32(audio)
    assert f32.dtype == np.float32
    assert len(f32) == SAMPLE_RATE
    assert np.all(np.abs(f32) <= 1.0)

    reconstructed = _f32_to_audio(f32, SAMPLE_RATE, 2)
    assert reconstructed.frame_rate == SAMPLE_RATE
    assert reconstructed.channels == 1
    assert reconstructed.sample_width == 2


# ---------------------------------------------------------------------------
# Mp3Carrier interface tests
# ---------------------------------------------------------------------------

def test_mp3_carrier_inheritance():
    """Mp3Carrier must subclass BaseCarrier."""
    assert issubclass(Mp3Carrier, BaseCarrier)
    assert isinstance(Mp3Carrier(), BaseCarrier)


@pytest.mark.parametrize("payload_size", [0, 1, 8, 16, 32])
def test_mp3_embed_extract_roundtrip(tmp_path: Path, payload_size: int):
    """Embed/extract roundtrip must recover the exact payload for any size."""
    cover_path = tmp_path / f"cover_{payload_size}.wav"
    stego_path = tmp_path / f"stego_{payload_size}.wav"
    # 18s gives ~400 segments → capacity = (400//8)-4 = 46 bytes ≥ 32 bytes needed
    _make_tone_wav(cover_path, duration_s=18.0)

    carrier = Mp3Carrier()
    prng_seed = b"\xAB" * 32
    payload = np.random.default_rng(payload_size).bytes(payload_size)

    stego_bytes = carrier.embed(str(cover_path), payload, prng_seed)
    stego_path.write_bytes(stego_bytes)

    extracted = carrier.extract(str(stego_path), prng_seed)
    assert extracted == payload


def test_mp3_capacity_and_overflow(tmp_path: Path):
    """capacity() must match bounds and overflow must raise ValueError."""
    cover_path = tmp_path / "cover_cap.wav"
    _make_tone_wav(cover_path, duration_s=10.0)

    carrier = Mp3Carrier()
    cap = carrier.capacity(str(cover_path))
    assert cap > 0

    prng_seed = b"\x77" * 32

    # Embed exactly at capacity (no error)
    stego_bytes = carrier.embed(str(cover_path), b"\x00" * cap, prng_seed)
    assert len(stego_bytes) > 0

    # Overflow by 1 byte
    with pytest.raises(ValueError, match="exceeds carrier capacity"):
        carrier.embed(str(cover_path), b"\x00" * (cap + 1), prng_seed)


def test_mp3_wrong_seed(tmp_path: Path):
    """Wrong PRNG seed must produce garbled output or ValueError on length."""
    cover_path = tmp_path / "cover_seed.wav"
    stego_path = tmp_path / "stego_seed.wav"
    # 18s → capacity ~46 bytes ≥ 27-byte test payload
    _make_tone_wav(cover_path, duration_s=18.0)

    carrier = Mp3Carrier()
    correct_seed = b"\x11" * 32
    wrong_seed = b"\x22" * 32
    payload = b"Ponytail echo stego secret!"

    stego_bytes = carrier.embed(str(cover_path), payload, correct_seed)
    stego_path.write_bytes(stego_bytes)

    try:
        extracted = carrier.extract(str(stego_path), wrong_seed)
        assert extracted != payload
    except ValueError:
        pass  # Corrupt length header detected — acceptable


def test_mp3_error_handling(tmp_path: Path):
    """Defensive validation must raise correct exception types."""
    valid_path = tmp_path / "valid.wav"
    _make_tone_wav(valid_path, duration_s=3.0)

    carrier = Mp3Carrier()
    seed = b"\x99" * 32

    # FileNotFoundError
    with pytest.raises(FileNotFoundError):
        carrier.capacity("missing_carrier.wav")
    with pytest.raises(FileNotFoundError):
        carrier.embed("missing_carrier.wav", b"data", seed)
    with pytest.raises(FileNotFoundError):
        carrier.extract("missing_carrier.wav", seed)

    # TypeError — wrong carrier_path type
    with pytest.raises(TypeError):
        carrier.capacity(12345)  # type: ignore
    with pytest.raises(TypeError):
        carrier.embed(12345, b"data", seed)  # type: ignore
    with pytest.raises(TypeError):
        carrier.extract(12345, seed)  # type: ignore

    # TypeError — wrong payload type
    with pytest.raises(TypeError):
        carrier.embed(str(valid_path), "not_bytes", seed)  # type: ignore

    # TypeError — wrong prng_seed type
    with pytest.raises(TypeError):
        carrier.embed(str(valid_path), b"data", "not_bytes")  # type: ignore
    with pytest.raises(TypeError):
        carrier.extract(str(valid_path), "not_bytes")  # type: ignore

    # ValueError — seed not 32 bytes
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        carrier.embed(str(valid_path), b"data", b"short")
    with pytest.raises(ValueError, match="exactly 32 bytes"):
        carrier.extract(str(valid_path), b"short")


def test_mp3_tiny_audio_extract_insufficient_capacity(tmp_path: Path):
    """Extract on audio too short for even length header raises ValueError."""
    tiny_path = tmp_path / "tiny.wav"
    # 1-second audio → ~20 segments → fewer than 32 needed for header
    _make_tone_wav(tiny_path, duration_s=0.5)

    carrier = Mp3Carrier()
    with pytest.raises(ValueError, match="enough segments for length header"):
        carrier.extract(str(tiny_path), b"\x00" * 32)


# ---------------------------------------------------------------------------
# strip_mp3_metadata tests
# ---------------------------------------------------------------------------

def test_strip_mp3_metadata_id3v2(tmp_path: Path):
    """ID3v2 header must be stripped while preserving audio payload."""
    audio_frames = b"\xff\xfb\x90\x00" + b"\x55" * 200
    id3 = _make_id3v2_tag(size=32)
    raw = id3 + audio_frames

    sanitized = strip_mp3_metadata(raw)
    assert sanitized == audio_frames
    assert not sanitized.startswith(b"ID3")


def test_strip_mp3_metadata_id3v2_with_footer():
    """ID3v2 tag with footer flag must skip footer bytes correctly."""
    audio_frames = b"\xff\xfb\x90\x00" + b"\xBB" * 100
    id3 = _make_id3v2_tag(size=8, has_footer=True)
    raw = id3 + audio_frames

    sanitized = strip_mp3_metadata(raw)
    assert sanitized == audio_frames


def test_strip_mp3_metadata_id3v1():
    """Trailing 128-byte ID3v1 TAG must be stripped."""
    audio_frames = b"\xff\xfb\x90\x00" + b"\xCC" * 300
    tag_v1 = _make_id3v1_tag()
    raw = audio_frames + tag_v1

    sanitized = strip_mp3_metadata(raw)
    assert sanitized == audio_frames
    assert b"TAG" not in sanitized


def test_strip_mp3_metadata_ape_footer():
    """Trailing APE APETAGEX footer must be stripped."""
    audio_frames = b"\xff\xfb\x90\x00" + b"\xDD" * 200
    ape = _make_ape_footer(ape_payload_size=0)
    raw = audio_frames + ape

    sanitized = strip_mp3_metadata(raw)
    assert sanitized == audio_frames
    assert b"APETAGEX" not in sanitized


def test_strip_mp3_metadata_ape_with_header():
    """APE tag with header and payload must be completely stripped."""
    audio_frames = b"\xff\xfb\x90\x00" + b"\xCC" * 200
    ape = _make_ape_footer(ape_payload_size=64, has_header=True)
    raw = audio_frames + ape

    sanitized = strip_mp3_metadata(raw)
    assert sanitized == audio_frames
    assert b"APETAGEX" not in sanitized


def test_strip_mp3_metadata_truncated_id3v2():
    """Truncated ID3v2 tag (declared size > actual length) handled gracefully."""
    # Tag declares 100 bytes but only 10 bytes follow
    truncated_tag = b"ID3\x03\x00\x00\x00\x00\x00\x64" + b"\x00" * 10
    audio_frames = b"\xff\xfb\x90\x00" + b"\xAA" * 100
    raw = truncated_tag + audio_frames
    sanitized = strip_mp3_metadata(raw)
    # Header stripped, remaining bytes returned
    assert len(sanitized) > 0


def test_strip_mp3_metadata_all_tags_combined():
    """Stripping ID3v2 + audio + ID3v1 + APE all at once."""
    audio_frames = b"\xff\xfb\x90\x00" + b"\xEE" * 400
    id3v2 = _make_id3v2_tag(size=20)
    id3v1 = _make_id3v1_tag()
    ape = _make_ape_footer(ape_payload_size=0)

    raw = id3v2 + audio_frames + id3v1 + ape
    sanitized = strip_mp3_metadata(raw)

    assert not sanitized.startswith(b"ID3")
    assert b"TAG" not in sanitized
    assert b"APETAGEX" not in sanitized
    assert audio_frames in sanitized


def test_strip_mp3_metadata_wav_passthrough(tmp_path: Path):
    """WAV/RIFF files must pass through strip_mp3_metadata unchanged."""
    wav_path = tmp_path / "pass.wav"
    _make_tone_wav(wav_path, duration_s=1.0)
    raw = wav_path.read_bytes()

    sanitized = strip_mp3_metadata(raw)
    assert sanitized == raw
    assert sanitized.startswith(b"RIFF")


def test_strip_mp3_metadata_input_types(tmp_path: Path):
    """str, Path, bytes, and bytearray must all work identically."""
    wav_path = tmp_path / "type_test.wav"
    _make_tone_wav(wav_path, duration_s=1.0)
    raw = wav_path.read_bytes()

    r_str = strip_mp3_metadata(str(wav_path))
    r_path = strip_mp3_metadata(wav_path)
    r_bytes = strip_mp3_metadata(raw)
    r_ba = strip_mp3_metadata(bytearray(raw))
    assert r_str == r_path == r_bytes == r_ba


def test_strip_mp3_metadata_errors():
    """Invalid inputs must raise correct exception types."""
    # TypeError
    with pytest.raises(TypeError):
        strip_mp3_metadata(12345)  # type: ignore
    with pytest.raises(TypeError):
        strip_mp3_metadata(None)  # type: ignore

    # FileNotFoundError
    with pytest.raises(FileNotFoundError):
        strip_mp3_metadata("missing_audio_xyz.mp3")

    # ValueError — empty data
    with pytest.raises(ValueError, match="empty"):
        strip_mp3_metadata(b"")

    # ValueError — corrupted synchsafe integer (byte >= 128)
    bad_id3 = b"ID3\x03\x00\x00\xFF\x00\x00\x00" + b"\xAA" * 20
    with pytest.raises(ValueError, match="synchsafe"):
        strip_mp3_metadata(bad_id3)

    # ValueError — all content stripped (nothing remains)
    only_id3 = _make_id3v2_tag(size=0)
    with pytest.raises(ValueError, match="No audio data remains"):
        strip_mp3_metadata(only_id3)


# ---------------------------------------------------------------------------
# Full end-to-end cryptographic integration pipeline
# ---------------------------------------------------------------------------

def test_mp3_full_end_to_end_pipeline(tmp_path: Path):
    """
    Test complete MP3 carrier end-to-end pipeline:
    Payload -> Compress -> Pack -> Encrypt -> HMAC ->
    Embed via Acoustic Echo Hiding ->
    Extract -> Verify HMAC -> Decrypt -> Unpack -> Decompress -> Original
    """
    import os

    from core import compression, crypto, payload

    cover_path = tmp_path / "e2e_cover.wav"
    stego_path = tmp_path / "e2e_stego.wav"

    # Use a compact payload to keep audio duration manageable for CI.
    # Encrypted blob overhead: salt(16)+iv(16)+hmac(32)+cipher(≥16) = ~80+ bytes.
    # 60s audio → 1322 segments → capacity = (1322//8)-4 = 161 bytes — enough.
    _make_tone_wav(cover_path, duration_s=60.0)

    secret_data = b"Ponytail Phase 4 E2E OK"
    secret_filename = "p4.txt"
    passphrase = "AcousticPonytailPhase4!2026"
    salt = os.urandom(16)

    # Derive keys
    enc_key, hmac_key, prng_seed = crypto.derive_keys(passphrase, salt)

    # Compress and pack
    compressed, is_comp = compression.compress(secret_data, level=6)
    packed = payload.pack(secret_filename, compressed, is_compressed=is_comp)

    # Encrypt + HMAC
    iv, ciphertext = crypto.encrypt(packed, enc_key)
    hmac_digest = crypto.compute_hmac(iv + ciphertext, hmac_key)
    encrypted_blob = crypto.pack_encrypted_blob(salt, iv, hmac_digest, ciphertext)

    # Verify it fits before embedding
    carrier = Mp3Carrier()
    cap = carrier.capacity(str(cover_path))
    assert len(encrypted_blob) <= cap, (
        f"Test blob ({len(encrypted_blob)} B) exceeds capacity ({cap} B)"
    )

    # Embed into WAV via echo hiding
    stego_bytes = carrier.embed(str(cover_path), encrypted_blob, prng_seed)
    stego_path.write_bytes(stego_bytes)

    # Extract
    extracted_blob = carrier.extract(str(stego_path), prng_seed)
    assert extracted_blob == encrypted_blob

    # Decrypt and verify
    ext_salt, ext_iv, ext_hmac, ext_cipher = crypto.unpack_encrypted_blob(extracted_blob)
    d_enc, d_hmac, _ = crypto.derive_keys(passphrase, ext_salt)
    decrypted_packed = crypto.verify_and_decrypt(ext_iv, ext_cipher, d_enc, d_hmac, ext_hmac)

    # Unpack and decompress
    ext_fn, ext_compressed, ext_is_comp = payload.unpack(decrypted_packed)
    recovered = compression.decompress(ext_compressed, ext_is_comp)

    assert recovered == secret_data
    assert ext_fn == secret_filename



# ---------------------------------------------------------------------------
# Imperceptibility validation
# ---------------------------------------------------------------------------

def test_mp3_imperceptibility_snr(tmp_path: Path):
    """Stego audio SNR must remain above 20 dB at spec-compliant alpha."""
    cover_path = tmp_path / "cover_snr.wav"
    stego_path = tmp_path / "stego_snr.wav"
    # 25s → ~565 segments → capacity = (565//8)-4 = 66 bytes ≥ 50-byte payload
    _make_tone_wav(cover_path, duration_s=25.0)

    carrier = Mp3Carrier()
    prng_seed = b"\xF0" * 32
    payload_data = b"\xAA" * 50

    stego_bytes = carrier.embed(str(cover_path), payload_data, prng_seed)
    stego_path.write_bytes(stego_bytes)

    cover_audio = AudioSegment.from_file(str(cover_path))
    stego_audio = AudioSegment.from_file(str(stego_path))

    cover_f32 = _audio_to_mono_f32(cover_audio)
    stego_f32 = _audio_to_mono_f32(stego_audio)

    # Trim to same length
    min_len = min(len(cover_f32), len(stego_f32))
    cover_f32 = cover_f32[:min_len]
    stego_f32 = stego_f32[:min_len]

    noise = stego_f32 - cover_f32
    p_signal = float(np.mean(cover_f32**2))
    p_noise = float(np.mean(noise**2))
    if p_noise < 1e-12:
        snr_db = 120.0
    else:
        snr_db = 10.0 * np.log10(p_signal / p_noise)

    assert snr_db >= 20.0, f"SNR {snr_db:.1f} dB below 20 dB minimum"
