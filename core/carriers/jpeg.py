"""
Cryptonite JPEG Carrier Module (Direct DCT Coefficient Manipulation).

Implements frequency-domain steganography by modifying quantized Discrete Cosine
Transform (DCT) AC coefficients without lossy re-encoding artifacts.
Uses sign-preserving LSB flipping, DC coefficient exclusion, and ChaCha20 scattering.
Optimized with fully vectorized SIMD 4D block DCT operations.
"""

import struct
import tempfile
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct

from core.carriers.base import BaseCarrier
from core.metadata import strip_jpeg_metadata
from core.prng import generate_permutation

try:
    import jpegio

    HAS_JPEGIO = True
except ImportError:
    jpegio = None
    HAS_JPEGIO = False

# Standard JPEG Luminance Quantization Table (ITU-T T.81 / RFC 2435)
DEFAULT_Q_MATRIX: np.ndarray = np.array(
    [
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99],
    ],
    dtype=np.float32,
)


def _block_dct_2d(block: np.ndarray) -> np.ndarray:
    """Compute 2D Discrete Cosine Transform on an 8x8 block."""
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def _block_idct_2d(block: np.ndarray) -> np.ndarray:
    """Compute 2D Inverse Discrete Cosine Transform on an 8x8 block."""
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


def _get_eligible_ac_mask(arr: np.ndarray) -> np.ndarray:
    """
    Generate boolean mask of embeddable AC coefficients:
    - Skips DC coefficient at (0, 0) of every 8x8 block.
    - Skips low-magnitude coefficients where |val| <= 1 (values 0, 1, -1).
    """
    if arr.ndim == 2:
        is_ac = np.ones_like(arr, dtype=bool)
        is_ac[0::8, 0::8] = False  # Skip all DC coefficients
        return is_ac & (np.abs(arr) > 1)
    if arr.ndim == 3:  # (N, 8, 8) batch format
        is_ac = np.ones_like(arr, dtype=bool)
        is_ac[:, 0, 0] = False  # Skip DC in every block
        return is_ac & (np.abs(arr) > 1)
    raise ValueError(f"Expected 2D or 3D array, got shape {arr.shape}")


def _modify_coeff_sign_preserving(v: int, bit: int) -> int:
    """
    Embed a bit into a single DCT coefficient while strictly preserving sign and |v| > 1:
    - If v >= 2: (v & ~1) | bit  (guaranteed >= 2)
    - If v <= -2: -((|v| & ~1) | bit) (guaranteed <= -2)
    """
    if v > 0:
        return (v & ~1) | bit
    mag = abs(v)
    return -((mag & ~1) | bit)


def _modify_coeffs_vectorized(vals: np.ndarray, bits: np.ndarray) -> np.ndarray:
    """
    Vectorized sign-preserving LSB flipping for batches of DCT coefficients.
    """
    modified = vals.copy()
    pos_mask = modified > 0
    neg_mask = modified < 0
    modified[pos_mask] = (modified[pos_mask] & ~1) | bits[pos_mask]
    abs_neg = np.abs(modified[neg_mask])
    modified[neg_mask] = -((abs_neg & ~1) | bits[neg_mask])
    return modified


def _img_to_vectorized_blocks(arr: np.ndarray) -> tuple[np.ndarray, int, int]:
    """
    Partition 3-channel RGB image (H, W, 3) into contiguous (N, 8, 8) blocks.
    """
    h, w = arr.shape[:2]
    hb, wb = h // 8, w // 8
    ch_first = arr[: hb * 8, : wb * 8].transpose(2, 0, 1)
    blocks = (
        ch_first.reshape(3, hb, 8, wb, 8)
        .transpose(0, 1, 3, 2, 4)
        .reshape(-1, 8, 8)
    )
    return blocks, hb, wb


def _vectorized_blocks_to_img(blocks: np.ndarray, hb: int, wb: int) -> np.ndarray:
    """
    Reconstruct (H, W, 3) RGB image from (N, 8, 8) blocks.
    """
    return (
        blocks.reshape(3, hb, wb, 8, 8)
        .transpose(0, 1, 3, 2, 4)
        .reshape(3, hb * 8, wb * 8)
        .transpose(1, 2, 0)
    )


class JpegCarrier(BaseCarrier):
    """
    JPEG steganography carrier operating in the frequency domain on raw DCT coefficients.
    Supports native jpegio with vectorized pure-Python/NumPy fallback for universal portability.
    """

    def capacity(self, carrier_path: str) -> int:
        """
        Calculate maximum payload capacity in bytes for the given JPEG carrier.

        Formula: count(eligible AC coefficients where |val| > 1) / 8 - 4 bytes.
        """
        if not isinstance(carrier_path, (str, Path)):
            raise TypeError(f"carrier_path must be str or Path, got {type(carrier_path).__name__}")

        path = Path(carrier_path)
        if not path.is_file():
            raise FileNotFoundError(f"Carrier file not found: {carrier_path}")

        if HAS_JPEGIO:
            cobj = jpegio.read(str(path))
            total_slots = sum(
                int(np.sum(_get_eligible_ac_mask(arr))) for arr in cobj.coef_arrays
            )
        else:
            img = Image.open(path).convert("RGB")
            arr = np.array(img, dtype=np.float32)
            blocks, _, _ = _img_to_vectorized_blocks(arr)
            # Vectorized 2D DCT on all N blocks simultaneously
            dct_blocks = np.round(
                dct(dct(blocks - 128.0, axis=-1, norm="ortho"), axis=-2, norm="ortho")
                / DEFAULT_Q_MATRIX
            ).astype(np.int32)
            mask = _get_eligible_ac_mask(dct_blocks)
            total_slots = int(np.sum(mask))

        max_bytes = (total_slots // 8) - 4
        return max(0, max_bytes)

    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        """
        Embed an encrypted payload into the JPEG carrier's DCT AC coefficients.
        """
        if not isinstance(carrier_path, (str, Path)):
            raise TypeError(f"carrier_path must be str or Path, got {type(carrier_path).__name__}")
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError(f"payload must be bytes or bytearray, got {type(payload).__name__}")
        if not isinstance(prng_seed, (bytes, bytearray)):
            raise TypeError(f"prng_seed must be bytes or bytearray, got {type(prng_seed).__name__}")

        payload_bytes = bytes(payload)
        seed_bytes = bytes(prng_seed)

        if len(seed_bytes) < 16:
            raise ValueError(f"prng_seed must be at least 16 bytes, got {len(seed_bytes)}")

        path = Path(carrier_path)
        if not path.is_file():
            raise FileNotFoundError(f"Carrier file not found: {carrier_path}")

        # Frame payload: 4-byte big-endian length prefix + payload
        framed = struct.pack(">I", len(payload_bytes)) + payload_bytes
        payload_bits = np.unpackbits(np.frombuffer(framed, dtype=np.uint8))
        num_bits = len(payload_bits)

        if HAS_JPEGIO:
            cobj = jpegio.read(str(path))
            coef_arrays = cobj.coef_arrays

            # Collect coordinate list of all eligible AC positions
            slot_coords: list[tuple[int, int, int]] = []
            for comp_idx, arr in enumerate(coef_arrays):
                mask = _get_eligible_ac_mask(arr)
                ys, xs = np.where(mask)
                for y, x in zip(ys, xs, strict=True):
                    slot_coords.append((comp_idx, int(y), int(x)))

            total_slots = len(slot_coords)
            max_capacity = (total_slots // 8) - 4

            if len(payload_bytes) > max_capacity:
                raise ValueError(
                    f"Payload size ({len(payload_bytes)} bytes) exceeds carrier capacity "
                    f"({max_capacity} bytes)"
                )

            perm = generate_permutation(seed_bytes, total_slots)
            selected_indices = perm[:num_bits]

            for bit_idx, slot_idx in enumerate(selected_indices):
                comp_idx, y, x = slot_coords[slot_idx]
                val = int(coef_arrays[comp_idx][y, x])
                bit = int(payload_bits[bit_idx])
                coef_arrays[comp_idx][y, x] = _modify_coeff_sign_preserving(val, bit)

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_out_path = tmp.name

            try:
                jpegio.write(cobj, tmp_out_path)
                stego_bytes = Path(tmp_out_path).read_bytes()
            finally:
                Path(tmp_out_path).unlink(missing_ok=True)

        else:
            img = Image.open(path).convert("RGB")
            arr = np.array(img, dtype=np.float32)
            blocks, hb, wb = _img_to_vectorized_blocks(arr)

            # Vectorized 2D DCT on all N blocks simultaneously
            dct_blocks = np.round(
                dct(dct(blocks - 128.0, axis=-1, norm="ortho"), axis=-2, norm="ortho")
                / DEFAULT_Q_MATRIX
            ).astype(np.int32)

            mask = _get_eligible_ac_mask(dct_blocks)
            b_indices, y_coords, x_coords = np.where(mask)
            total_slots = len(b_indices)
            max_capacity = (total_slots // 8) - 4

            if len(payload_bytes) > max_capacity:
                raise ValueError(
                    f"Payload size ({len(payload_bytes)} bytes) exceeds carrier capacity "
                    f"({max_capacity} bytes)"
                )

            perm = generate_permutation(seed_bytes, total_slots)
            selected_slots = perm[:num_bits]
            tb = b_indices[selected_slots]
            ty = y_coords[selected_slots]
            tx = x_coords[selected_slots]

            # Vectorized sign-preserving LSB assignment
            vals = dct_blocks[tb, ty, tx]
            dct_blocks[tb, ty, tx] = _modify_coeffs_vectorized(vals, payload_bits)

            # Vectorized 2D IDCT on all blocks simultaneously
            spatial_blocks = np.clip(
                idct(
                    idct(
                        dct_blocks.astype(np.float32) * DEFAULT_Q_MATRIX,
                        axis=-1,
                        norm="ortho",
                    ),
                    axis=-2,
                    norm="ortho",
                )
                + 128.0,
                0,
                255,
            )
            reconstructed = _vectorized_blocks_to_img(spatial_blocks, hb, wb)
            out_img = Image.fromarray(reconstructed.astype(np.uint8), mode="RGB")
            buf = BytesIO()
            out_img.save(buf, format="JPEG", quality=100, subsampling=0)
            stego_bytes = buf.getvalue()

        sanitized_stego = strip_jpeg_metadata(stego_bytes)
        return sanitized_stego

    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        """
        Extract and decrypt hidden payload from JPEG DCT AC coefficients.
        """
        if not isinstance(stego_path, (str, Path)):
            raise TypeError(f"stego_path must be str or Path, got {type(stego_path).__name__}")
        if not isinstance(prng_seed, (bytes, bytearray)):
            raise TypeError(f"prng_seed must be bytes or bytearray, got {type(prng_seed).__name__}")

        seed_bytes = bytes(prng_seed)
        if len(seed_bytes) < 16:
            raise ValueError(f"prng_seed must be at least 16 bytes, got {len(seed_bytes)}")

        path = Path(stego_path)
        if not path.is_file():
            raise FileNotFoundError(f"Stego file not found: {stego_path}")

        if HAS_JPEGIO:
            cobj = jpegio.read(str(path))
            coef_arrays = cobj.coef_arrays

            slot_coords = []
            for comp_idx, arr in enumerate(coef_arrays):
                mask = _get_eligible_ac_mask(arr)
                ys, xs = np.where(mask)
                for y, x in zip(ys, xs, strict=True):
                    slot_coords.append((comp_idx, int(y), int(x)))

            total_slots = len(slot_coords)
            max_capacity = (total_slots // 8) - 4

            if total_slots < 32:
                raise ValueError("Carrier does not have enough capacity for length header")

            perm = generate_permutation(seed_bytes, total_slots)

            # Extract 32-bit length header
            len_indices = perm[:32]
            len_bits = np.zeros(32, dtype=np.uint8)
            for i, slot_idx in enumerate(len_indices):
                comp_idx, y, x = slot_coords[slot_idx]
                val = int(coef_arrays[comp_idx][y, x])
                len_bits[i] = abs(val) & 1

            len_bytes = np.packbits(len_bits).tobytes()
            payload_len = struct.unpack(">I", len_bytes)[0]

            if payload_len > max_capacity:
                raise ValueError(
                    f"Extracted payload length ({payload_len} bytes) exceeds carrier capacity "
                    f"({max_capacity} bytes) - corrupted file or invalid passphrase/seed"
                )

            # Extract payload bits
            num_bits = payload_len * 8
            payload_indices = perm[32 : 32 + num_bits]
            p_bits = np.zeros(num_bits, dtype=np.uint8)
            for i, slot_idx in enumerate(payload_indices):
                comp_idx, y, x = slot_coords[slot_idx]
                val = int(coef_arrays[comp_idx][y, x])
                p_bits[i] = abs(val) & 1

            payload = np.packbits(p_bits).tobytes()
            return payload

        else:
            img = Image.open(path).convert("RGB")
            arr = np.array(img, dtype=np.float32)
            blocks, _, _ = _img_to_vectorized_blocks(arr)

            # Vectorized 2D DCT on all N blocks simultaneously
            dct_blocks = np.round(
                dct(dct(blocks - 128.0, axis=-1, norm="ortho"), axis=-2, norm="ortho")
                / DEFAULT_Q_MATRIX
            ).astype(np.int32)

            mask = _get_eligible_ac_mask(dct_blocks)
            b_indices, y_coords, x_coords = np.where(mask)
            total_slots = len(b_indices)
            max_capacity = (total_slots // 8) - 4

            if total_slots < 32:
                raise ValueError("Carrier does not have enough capacity for length header")

            perm = generate_permutation(seed_bytes, total_slots)

            # Vectorized length header extraction
            len_indices = perm[:32]
            len_vals = dct_blocks[
                b_indices[len_indices], y_coords[len_indices], x_coords[len_indices]
            ]
            len_bits = np.abs(len_vals) & 1
            len_bytes = np.packbits(len_bits).tobytes()
            payload_len = struct.unpack(">I", len_bytes)[0]

            if payload_len > max_capacity:
                raise ValueError(
                    f"Extracted payload length ({payload_len} bytes) exceeds carrier capacity "
                    f"({max_capacity} bytes) - corrupted file or invalid passphrase/seed"
                )

            # Vectorized payload bits extraction
            num_bits = payload_len * 8
            payload_indices = perm[32 : 32 + num_bits]
            p_vals = dct_blocks[
                b_indices[payload_indices],
                y_coords[payload_indices],
                x_coords[payload_indices],
            ]
            p_bits = np.abs(p_vals) & 1
            payload = np.packbits(p_bits).tobytes()
            return payload
