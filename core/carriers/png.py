"""
Cryptonite PNG Carrier Module (Adaptive LSB).

Implements texture-adaptive Least Significant Bit (LSB) embedding and extraction
using Sobel edge gradient analysis on Most Significant Bits (MSBs) to ensure
deterministic, side-channel-free cover-stego synchrony with ChaCha20 PRNG scattering.
"""

import struct
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.signal import convolve2d

from core.carriers.base import BaseCarrier
from core.metadata import strip_png_metadata
from core.prng import generate_permutation

SOBEL_X: np.ndarray = np.array(
    [[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]], dtype=np.float32
)
SOBEL_Y: np.ndarray = np.array(
    [[-1.0, -2.0, -1.0], [0.0, 0.0, 0.0], [1.0, 2.0, 1.0]], dtype=np.float32
)

# Texture thresholds for adaptive bit allocation
TEXTURE_T1: float = 20.0  # Smooth vs Medium boundary
TEXTURE_T2: float = 50.0  # Medium vs Textured boundary


def _compute_msb_gradient(img_arr: np.ndarray, embed_channels: int) -> np.ndarray:
    """
    Compute Sobel gradient magnitude on top 5 MSBs (pixel & 0xF8).
    Because embedding modifies at most the bottom 3 LSBs, the MSBs remain
    100% invariant between cover and stego images, guaranteeing deterministic
    extraction without transmitting side-channel allocation maps.
    """
    msb_arr = img_arr & 0xF8

    if embed_channels >= 3:
        # Luminance Y = 0.299*R + 0.587*G + 0.114*B computed in float32 directly
        gray = (
            0.299 * msb_arr[..., 0].astype(np.float32)
            + 0.587 * msb_arr[..., 1].astype(np.float32)
            + 0.114 * msb_arr[..., 2].astype(np.float32)
        )
    else:
        gray = msb_arr[..., 0].astype(np.float32)

    gx = convolve2d(gray, SOBEL_X, mode="same", boundary="symm")
    gy = convolve2d(gray, SOBEL_Y, mode="same", boundary="symm")
    grad = np.sqrt(gx**2 + gy**2)
    return grad


def _build_embedding_slots(
    img_shape: tuple[int, ...], embed_channels: int, grad: np.ndarray
) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Build arrays of (flat_pixel_index, bit_offset) for all available bit slots.

    Allocation rules:
      - Gradient < T1: 1 bit per channel (bit 0)
      - T1 <= Gradient < T2: 2 bits per channel (bits 0, 1)
      - Gradient >= T2: 3 bits per channel (bits 0, 1, 2)

    Returns:
        flat_indices: 1D array of flat pixel-channel indices.
        bit_offsets: 1D array of bit positions (0, 1, or 2).
        total_bits: Total count of embeddable bit slots.
    """
    h, w = img_shape[:2]
    total_pixels = h * w
    num_channels = img_shape[2] if len(img_shape) > 2 else 1

    # Classify bit depth per pixel
    depth_map = np.ones((h, w), dtype=np.uint8)
    depth_map[grad >= TEXTURE_T1] = 2
    depth_map[grad >= TEXTURE_T2] = 3

    flat_depth = depth_map.reshape(-1)
    indices_list: list[np.ndarray] = []
    offsets_list: list[np.ndarray] = []

    # Calculate pixel offsets for each embeddable channel
    for c in range(embed_channels):
        channel_base = np.arange(total_pixels, dtype=np.int64) * num_channels + c

        # Bit plane 0: available for all pixels
        indices_list.append(channel_base)
        offsets_list.append(np.zeros(total_pixels, dtype=np.uint8))

        # Bit plane 1: available where depth >= 2
        mask_2 = flat_depth >= 2
        if np.any(mask_2):
            indices_list.append(channel_base[mask_2])
            offsets_list.append(np.ones(np.sum(mask_2), dtype=np.uint8))

        # Bit plane 2: available where depth >= 3
        mask_3 = flat_depth >= 3
        if np.any(mask_3):
            indices_list.append(channel_base[mask_3])
            offsets_list.append(np.full(np.sum(mask_3), 2, dtype=np.uint8))

    flat_indices = np.concatenate(indices_list)
    bit_offsets = np.concatenate(offsets_list)
    return flat_indices, bit_offsets, len(flat_indices)


def _load_image_array(
    carrier_input: str | Path | bytes | bytearray,
) -> tuple[Image.Image, np.ndarray, int]:
    """
    Load image and return PIL Image, NumPy uint8 array, and count of embeddable channels.
    """
    if isinstance(carrier_input, (str, Path)):
        path = Path(carrier_input)
        if not path.is_file():
            raise FileNotFoundError(f"Carrier file not found: {carrier_input}")
        img = Image.open(path)
    elif isinstance(carrier_input, (bytes, bytearray)):
        img = Image.open(BytesIO(carrier_input))
    else:
        raise TypeError(
            "Carrier input must be str, Path, bytes, or bytearray, "
            f"got {type(carrier_input).__name__}"
        )

    # Standardize image modes for steganography
    if img.mode == "P":
        # Palette image: convert to RGBA if transparency is present, else RGB
        img = img.convert("RGBA" if "transparency" in img.info else "RGB")
    elif img.mode == "1":
        img = img.convert("L")

    arr = np.array(img, dtype=np.uint8)

    if img.mode == "RGBA":
        embed_channels = 3  # Keep Alpha channel 3 intact to preserve transparency masks
    elif img.mode == "RGB":
        embed_channels = 3
    elif img.mode == "LA":
        embed_channels = 1  # Keep Alpha channel 1 intact
    elif img.mode == "L":
        embed_channels = 1
    else:
        # Fallback convert to RGB
        img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        embed_channels = 3

    if arr.ndim == 2:
        arr = arr[:, :, np.newaxis]

    return img, arr, embed_channels


class PngCarrier(BaseCarrier):
    """
    Adaptive LSB carrier using Sobel gradient texture analysis on MSBs with
    ChaCha20 PRNG position scattering and lossless metadata sanitization.
    """

    def capacity(self, carrier_path: str) -> int:
        """
        Calculate maximum payload capacity in bytes for the given PNG carrier.

        Args:
            carrier_path: Path to PNG carrier image file.

        Returns:
            Maximum payload capacity in bytes (excluding 4-byte length prefix).

        Raises:
            TypeError: If carrier_path is not a string.
            FileNotFoundError: If carrier_path file does not exist.
            ValueError: If file is not a valid image.
        """
        if not isinstance(carrier_path, (str, Path)):
            raise TypeError(f"carrier_path must be str or Path, got {type(carrier_path).__name__}")

        _, arr, embed_channels = _load_image_array(carrier_path)
        grad = _compute_msb_gradient(arr, embed_channels)

        # O(1) memory vectorized bit count directly from depth classification
        h, w = arr.shape[:2]
        depth_map = np.ones((h, w), dtype=np.uint8)
        depth_map[grad >= TEXTURE_T1] = 2
        depth_map[grad >= TEXTURE_T2] = 3

        total_bits = int(np.sum(depth_map)) * embed_channels

        # 4 bytes (32 bits) reserved for framed payload length header
        max_bytes = (total_bits // 8) - 4
        return max(0, max_bytes)

    def embed(self, carrier_path: str, payload: bytes, prng_seed: bytes) -> bytes:
        """
        Embed an encrypted binary payload into a PNG carrier using adaptive LSB
        and ChaCha20 PRNG scattering.

        Args:
            carrier_path: Path to PNG carrier image file.
            payload: Binary payload bytes to embed.
            prng_seed: 32-byte cryptographic seed for ChaCha20 scattering.

        Returns:
            Sanitized stego PNG image as bytes.

        Raises:
            TypeError: If parameters have invalid types.
            FileNotFoundError: If carrier_path does not exist.
            ValueError: If payload exceeds capacity or parameters are malformed.
        """
        if not isinstance(carrier_path, (str, Path)):
            raise TypeError(f"carrier_path must be str or Path, got {type(carrier_path).__name__}")
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError(f"payload must be bytes or bytearray, got {type(payload).__name__}")
        if not isinstance(prng_seed, (bytes, bytearray)):
            raise TypeError(f"prng_seed must be bytes or bytearray, got {type(prng_seed).__name__}")

        payload_bytes = bytes(payload)
        seed_bytes = bytes(prng_seed)

        if len(seed_bytes) != 32:
            raise ValueError(f"prng_seed must be exactly 32 bytes, got {len(seed_bytes)}")

        img, arr, embed_channels = _load_image_array(carrier_path)
        grad = _compute_msb_gradient(arr, embed_channels)
        flat_indices, bit_offsets, total_bits = _build_embedding_slots(
            arr.shape, embed_channels, grad
        )

        max_capacity = (total_bits // 8) - 4
        if len(payload_bytes) > max_capacity:
            raise ValueError(
                f"Payload size ({len(payload_bytes)} bytes) exceeds carrier capacity "
                f"({max_capacity} bytes)"
            )

        # Frame payload with 4-byte big-endian length prefix
        framed = struct.pack(">I", len(payload_bytes)) + payload_bytes
        payload_bits = np.unpackbits(np.frombuffer(framed, dtype=np.uint8))
        num_payload_bits = len(payload_bits)

        # Generate PRNG permutation of all embedding slots
        perm = generate_permutation(seed_bytes, total_bits)
        selected_slots = perm[:num_payload_bits]

        target_flat_indices = flat_indices[selected_slots]
        target_bit_offsets = bit_offsets[selected_slots]

        # Flatten working array for assignment
        flat_arr = arr.reshape(-1)

        # Separate by bit offset (0, 1, 2) to eliminate write collisions
        for b in range(3):
            mask_b = target_bit_offsets == b
            if np.any(mask_b):
                idx_b = target_flat_indices[mask_b]
                bits_b = payload_bits[mask_b].astype(np.uint8)
                clear_mask = np.uint8(0xFF ^ (1 << b))
                flat_arr[idx_b] = (flat_arr[idx_b] & clear_mask) | (bits_b << b)

        stego_arr = flat_arr.reshape(arr.shape)
        if stego_arr.shape[2] == 1:
            stego_arr = stego_arr[:, :, 0]

        # Save stego image losslessly — do NOT use optimize=True as it triggers
        # Pillow's two-pass encoder which can alter filter bytes and pixel
        # representation for palette/grayscale modes, breaking extraction.
        out_img = Image.fromarray(stego_arr, mode=img.mode)
        buf = BytesIO()
        out_img.save(buf, format="PNG", optimize=False, compress_level=6)
        raw_png = buf.getvalue()

        # Sanitize metadata chunks
        sanitized_png = strip_png_metadata(raw_png)
        return sanitized_png

    def extract(self, stego_path: str, prng_seed: bytes) -> bytes:
        """
        Extract and recover a hidden binary payload from a stego PNG image.

        Args:
            stego_path: Path to stego PNG image file.
            prng_seed: 32-byte cryptographic seed for ChaCha20 permutation reconstruction.

        Returns:
            Recovered payload bytes.

        Raises:
            TypeError: If parameters have invalid types.
            FileNotFoundError: If stego_path does not exist.
            ValueError: If payload length is corrupt or exceeds capacity.
        """
        if not isinstance(stego_path, (str, Path)):
            raise TypeError(f"stego_path must be str or Path, got {type(stego_path).__name__}")
        if not isinstance(prng_seed, (bytes, bytearray)):
            raise TypeError(f"prng_seed must be bytes or bytearray, got {type(prng_seed).__name__}")

        seed_bytes = bytes(prng_seed)
        if len(seed_bytes) != 32:
            raise ValueError(f"prng_seed must be exactly 32 bytes, got {len(seed_bytes)}")

        _, arr, embed_channels = _load_image_array(stego_path)
        grad = _compute_msb_gradient(arr, embed_channels)
        flat_indices, bit_offsets, total_bits = _build_embedding_slots(
            arr.shape, embed_channels, grad
        )

        max_capacity = (total_bits // 8) - 4
        if total_bits < 32:
            raise ValueError("Carrier does not have enough capacity for length header")

        perm = generate_permutation(seed_bytes, total_bits)
        flat_arr = arr.reshape(-1)

        # Extract first 32 bits (length prefix)
        len_slots = perm[:32]
        len_flat_idx = flat_indices[len_slots]
        len_bit_offsets = bit_offsets[len_slots]
        len_bits = (flat_arr[len_flat_idx] >> len_bit_offsets) & 1

        len_bytes = np.packbits(len_bits).tobytes()
        payload_len = struct.unpack(">I", len_bytes)[0]

        if payload_len > max_capacity:
            raise ValueError(
                f"Extracted payload length ({payload_len} bytes) exceeds carrier capacity "
                f"({max_capacity} bytes) - corrupted file or invalid passphrase/seed"
            )

        # Extract remaining payload bits
        num_payload_bits = payload_len * 8
        payload_slots = perm[32 : 32 + num_payload_bits]
        p_flat_idx = flat_indices[payload_slots]
        p_bit_offsets = bit_offsets[payload_slots]
        p_bits = (flat_arr[p_flat_idx] >> p_bit_offsets) & 1

        payload = np.packbits(p_bits).tobytes()
        return payload
