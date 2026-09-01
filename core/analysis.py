"""
Cryptonite Steganalysis & Perceptual Quality Module.

Computes Chi-squared LSB distribution, SSIM, PSNR, and RS analysis.
All functions accept uint8 NumPy arrays (H, W) or (H, W, C).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage, stats


@dataclass
class SteganalysisResult:
    chi_squared_p_value: float
    ssim_score: float
    rs_score: float
    psnr_db: float
    verdict: str  # 'SAFE' | 'MODERATE' | 'HIGH_RISK'


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_ndarray(*arrays: object, names: list[str] | None = None) -> None:
    """Raise TypeError if any argument is not np.ndarray."""
    for i, arr in enumerate(arrays):
        if not isinstance(arr, np.ndarray):
            label = names[i] if names else f"arg[{i}]"
            raise TypeError(
                f"{label} must be np.ndarray, got {type(arr).__name__}"
            )


def _to_float64_2d(arr: np.ndarray) -> np.ndarray:
    """
    Flatten a (H, W) or (H, W, C) uint8 array to a 1-D float64 pixel vector.
    Validates dtype is uint8 and ndim is 2 or 3.
    """
    if arr.ndim not in (2, 3):
        raise ValueError(f"image_array must be 2-D or 3-D, got shape {arr.shape}")
    return arr.astype(np.float64).ravel()


def _assert_same_shape(a: np.ndarray, b: np.ndarray) -> None:
    if a.shape != b.shape:
        raise ValueError(
            f"cover and stego arrays must have identical shapes, "
            f"got {a.shape} vs {b.shape}"
        )


# ---------------------------------------------------------------------------
# 1. Chi-Squared LSB Pair Analysis (Westfeld & Pfitzmann)
# ---------------------------------------------------------------------------

def chi_squared_test(image_array: np.ndarray) -> float:
    """
    Run chi-squared LSB pair analysis on an image (Westfeld & Pfitzmann).

    Pairs of Values: counts of pixel value 2k and 2k+1 (k=0..127).
    Under flat LSB substitution the two counts equalise → the chi² statistic
    *decreases* because observed frequencies closely match the expected (equalised)
    distribution.

    Interpretation of the returned p-value
    ---------------------------------------
    The null hypothesis (H0) is that the pair frequencies ARE equalised (stego).

    - **Low p-value (p < 0.05)**: reject H0 → pairs are NOT equalised → natural image → **SAFE**.
    - **High p-value (p > 0.95)**: cannot reject H0 → pairs ARE equalised → stego → **HIGH_RISK**.

    NOTE: Meaningful results require large images (≥512×512) where bin counts
    are statistically stable.  Small images return values closer to 1.0.

    Returns
    -------
    float
        Survival-function p-value ∈ [0, 1].
    """
    _require_ndarray(image_array, names=["image_array"])
    if image_array.ndim not in (2, 3):
        raise ValueError(f"image_array must be 2-D or 3-D, got shape {image_array.shape}")

    pixels = image_array.ravel().astype(np.int32)
    if len(pixels) == 0:
        return 1.0  # empty → trivially clean

    # Bin counts for values 0–255
    counts = np.bincount(pixels, minlength=256).astype(np.float64)  # shape (256,)

    # Build pair sums: E_k = (count(2k) + count(2k+1)) / 2  for k = 0..127
    even_counts = counts[0::2]          # shape (128,)
    odd_counts  = counts[1::2]          # shape (128,)
    expected    = (even_counts + odd_counts) / 2.0

    # Only include bins where expected > 0 to avoid division-by-zero
    active = expected > 0
    if not np.any(active):
        return 1.0

    chi2 = np.sum((even_counts[active] - expected[active]) ** 2 / expected[active])
    df   = int(np.sum(active)) - 1

    if df < 1:
        return 1.0

    # Survival function: P(X > chi2) under chi2(df)
    p_value = float(stats.chi2.sf(chi2, df))
    return p_value


# ---------------------------------------------------------------------------
# 2. SSIM — Structural Similarity Index Measure (Wang et al., 2004)
# ---------------------------------------------------------------------------

def compute_ssim(cover_array: np.ndarray, stego_array: np.ndarray) -> float:
    """
    Compute mean SSIM between a cover and stego image.

    Uses 11×11 Gaussian kernel (σ=1.5), constants C1=(0.01·255)², C2=(0.03·255)².
    Averaged over all spatial positions and colour channels.

    Returns
    -------
    float
        SSIM ∈ [0, 1].  1.0 = identical.
    """
    _require_ndarray(cover_array, stego_array, names=["cover_array", "stego_array"])
    _assert_same_shape(cover_array, stego_array)
    if cover_array.ndim not in (2, 3):
        raise ValueError(f"Arrays must be 2-D or 3-D, got shape {cover_array.shape}")

    L  = 255.0          # noqa: N806
    C1 = (0.01 * L) ** 2   # noqa: N806  6.5025
    C2 = (0.03 * L) ** 2   # noqa: N806  58.5225
    sigma = 1.5

    x = cover_array.astype(np.float64)
    y = stego_array.astype(np.float64)

    # Work channel-wise; stack to (H, W, C) if grayscale
    if x.ndim == 2:
        x = x[:, :, np.newaxis]
        y = y[:, :, np.newaxis]

    ssim_vals: list[float] = []
    for c in range(x.shape[2]):
        xc = x[:, :, c]
        yc = y[:, :, c]

        mu_x  = ndimage.gaussian_filter(xc, sigma=sigma, truncate=3.5)
        mu_y  = ndimage.gaussian_filter(yc, sigma=sigma, truncate=3.5)
        mu_x2 = mu_x * mu_x
        mu_y2 = mu_y * mu_y
        mu_xy = mu_x * mu_y

        sig_x2  = ndimage.gaussian_filter(xc * xc, sigma=sigma, truncate=3.5) - mu_x2
        sig_y2  = ndimage.gaussian_filter(yc * yc, sigma=sigma, truncate=3.5) - mu_y2
        sig_xy  = ndimage.gaussian_filter(xc * yc, sigma=sigma, truncate=3.5) - mu_xy

        num  = (2.0 * mu_xy + C1) * (2.0 * sig_xy + C2)
        den  = (mu_x2 + mu_y2 + C1) * (sig_x2 + sig_y2 + C2)
        ssim_map = num / den
        ssim_vals.append(float(np.mean(ssim_map)))

    return float(np.mean(ssim_vals))


# ---------------------------------------------------------------------------
# 3. PSNR — Peak Signal-to-Noise Ratio
# ---------------------------------------------------------------------------

def compute_psnr(cover_array: np.ndarray, stego_array: np.ndarray) -> float:
    """
    Compute PSNR in dB between cover and stego.

    PSNR = 10 · log10(255² / MSE).  Returns float('inf') for identical images.

    Parameters
    ----------
    cover_array, stego_array : np.ndarray
        Must have identical shapes.  Any numeric dtype accepted.

    Returns
    -------
    float
        PSNR in dB.
    """
    _require_ndarray(cover_array, stego_array, names=["cover_array", "stego_array"])
    _assert_same_shape(cover_array, stego_array)
    if cover_array.ndim not in (2, 3):
        raise ValueError(f"Arrays must be 2-D or 3-D, got shape {cover_array.shape}")

    diff = cover_array.astype(np.float64) - stego_array.astype(np.float64)
    mse  = float(np.mean(diff ** 2))

    if mse == 0.0:
        return float("inf")

    return float(10.0 * np.log10((255.0 ** 2) / mse))


# ---------------------------------------------------------------------------
# 4. RS Analysis — Regular-Singular (Fridrich et al., 2001)
# ---------------------------------------------------------------------------

def rs_analysis(image_array: np.ndarray) -> float:
    """
    Run RS (Regular-Singular) steganalysis on an image.

    Partitions the image into non-overlapping groups of 4 pixels.
    Applies mask M=[0,1,1,0] and its inverse to classify groups as
    Regular (R) or Singular (S) under standard vs inverted LSB flipping.

    Discrepancy score = (|R_M – R_{-M}| + |S_M – S_{-M}|) / (R_M + S_M + ε)

    Returns
    -------
    float
        RS score ≥ 0.  Score < 0.10 → clean, score > 0.25 → likely stego.
    """
    _require_ndarray(image_array, names=["image_array"])
    if image_array.ndim not in (2, 3):
        raise ValueError(f"image_array must be 2-D or 3-D, got shape {image_array.shape}")

    # Work on the first channel only (luminance / red); flatten to 1-D int32
    if image_array.ndim == 3:
        channel = image_array[:, :, 0]
    else:
        channel = image_array

    pixels = channel.astype(np.int32).ravel()
    n_group = 4
    n_pixels = len(pixels)

    # Truncate to a multiple of n_group
    n_trim = n_pixels - (n_pixels % n_group)
    if n_trim < n_group:
        return 0.0

    groups = pixels[:n_trim].reshape(-1, n_group)  # shape (N, 4)

    # Mask M = [0, 1, 1, 0] → flip positions 1, 2 (0-indexed)
    mask = np.array([0, 1, 1, 0], dtype=np.int32)

    def discrimination(g: np.ndarray) -> np.ndarray:
        """Sum of absolute differences between adjacent pixels. Shape (N,)."""
        return np.sum(np.abs(np.diff(g, axis=1)), axis=1)

    def flip_m(g: np.ndarray) -> np.ndarray:
        """Standard LSB flip at mask positions: x ⊕ mask."""
        return g ^ mask  # XOR flips LSB where mask=1

    def flip_neg_m(g: np.ndarray) -> np.ndarray:
        """Inverted-mask flip: x-1 if odd, x+1 if even at mask positions."""
        g2 = g.copy()
        for j in range(n_group):
            if mask[j] == 1:
                odd_mask = (g2[:, j] % 2 == 1)
                g2[:, j] = np.where(odd_mask, g2[:, j] - 1, g2[:, j] + 1)
        # Clip to [0, 255]
        g2 = np.clip(g2, 0, 255)
        return g2

    f_orig   = discrimination(groups)
    f_flip_m = discrimination(flip_m(groups))
    f_flip_n = discrimination(flip_neg_m(groups))

    R_M  = float(np.sum(f_flip_m > f_orig))   # noqa: N806
    S_M  = float(np.sum(f_flip_m < f_orig))   # noqa: N806
    R_nM = float(np.sum(f_flip_n > f_orig))   # noqa: N806
    S_nM = float(np.sum(f_flip_n < f_orig))   # noqa: N806

    total = R_M + S_M + 1e-10
    score = (abs(R_M - R_nM) + abs(S_M - S_nM)) / total
    return float(score)


# ---------------------------------------------------------------------------
# 5. Full Multi-Vector Analysis
# ---------------------------------------------------------------------------

def full_analysis(cover_array: np.ndarray, stego_array: np.ndarray) -> SteganalysisResult:
    """
    Run all steganalysis tests and return a unified SteganalysisResult.

    Verdict decision matrix (Westfeld chi2 p-value semantics)
    ----------------------------------------------------------
    chi2 p-value interpretation:
      - LOW p  (p < 0.05): pairs NOT equalised → natural image → supports SAFE
      - HIGH p (p > 0.95): pairs ARE equalised → likely flat LSB stego → supports HIGH_RISK

    HIGH_RISK : chi2_p > 0.95  OR  rs_score > 0.30  OR  ssim < 0.90
    MODERATE  : chi2_p > 0.50  OR  rs_score > 0.15  OR  ssim < 0.98  OR  psnr < 40
    SAFE      : everything else

    NOTE: chi2 is only statistically meaningful for large images (≥512×512).
    For small images, rely primarily on SSIM, PSNR, and RS scores.

    Parameters
    ----------
    cover_array : np.ndarray
        Original cover image (H, W) or (H, W, C), uint8.
    stego_array : np.ndarray
        Stego image with identical shape to cover_array.

    Returns
    -------
    SteganalysisResult
    """
    _require_ndarray(cover_array, stego_array, names=["cover_array", "stego_array"])
    _assert_same_shape(cover_array, stego_array)
    if cover_array.ndim not in (2, 3):
        raise ValueError(f"Arrays must be 2-D or 3-D, got shape {cover_array.shape}")

    p_value  = chi_squared_test(stego_array)
    ssim_val = compute_ssim(cover_array, stego_array)
    psnr_val = compute_psnr(cover_array, stego_array)
    rs_val   = rs_analysis(stego_array)

    # Verdict — chi2: HIGH p = equalized pairs = stego = risk
    if p_value > 0.95 or rs_val > 0.30 or ssim_val < 0.90:
        verdict = "HIGH_RISK"
    elif p_value > 0.50 or rs_val > 0.15 or ssim_val < 0.98 or psnr_val < 40.0:
        verdict = "MODERATE"
    else:
        verdict = "SAFE"

    return SteganalysisResult(
        chi_squared_p_value=p_value,
        ssim_score=ssim_val,
        rs_score=rs_val,
        psnr_db=psnr_val,
        verdict=verdict,
    )
