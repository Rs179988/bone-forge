#!/usr/bin/env python3
"""
Layer 2E: Linear-Light Bloom, Warm Halation, Vignette & Kodak 2383 Grain Post-Processor
Ported from higgsfield-ai/higgsfield-video-engineer (examples/felt-good-morning/tools/glow.py)
Supports both:
  1. Frame directory mode: python3 glow.py <in_dir> <out_dir> [first last]
  2. Single PNG / NumPy array mode (importable by renderer & QA tools)
Uses pure NumPy separable Gaussian convolution (zero scipy/PIL required).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import numpy as np

from textures import read_png_rgb8, write_png_rgb8


def gaussian_kernel_1d(sigma: float) -> np.ndarray:
    radius = max(1, int(round(sigma * 2.5)))
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    k = np.exp(-0.5 * (x / max(0.1, sigma)) ** 2)
    return k / k.sum()


def blur_rgb_separable(img: np.ndarray, sigma: float) -> np.ndarray:
    """Fast 2D separable Gaussian blur on (H, W, 3) float32 array in pure NumPy."""
    k = gaussian_kernel_1d(sigma)
    r = len(k) // 2
    # Pad & convolve along width (axis 1)
    padded_x = np.pad(img, ((0, 0), (r, r), (0, 0)), mode="edge")
    out_x = np.zeros_like(img)
    for i, weight in enumerate(k):
        out_x += weight * padded_x[:, i : i + img.shape[1], :]
    # Pad & convolve along height (axis 0)
    padded_y = np.pad(out_x, ((r, r), (0, 0), (0, 0)), mode="edge")
    out_y = np.zeros_like(img)
    for i, weight in enumerate(k):
        out_y += weight * padded_y[i : i + img.shape[0], :, :]
    return out_y


def apply_linear_glow_and_halation(
    srgb: np.ndarray,
    bloom_strength: float = 0.42,
    vignette_strength: float = 0.18,
    grain_strength: float = 0.012,
    seed: int = 1,
) -> np.ndarray:
    """
    Execute Higgsfield's exact linear-light post-processing pass:
      1. sRGB -> Linear (gamma 2.2)
      2. Extract bright highlights (luminance > 0.68)
      3. Downsample 4x and run multi-scale Gaussian bloom (radii 3, 9, 22)
      4. Add warm halation tint [1.0, 0.94, 0.80]
      5. Apply optical radial vignette & subtle film grain
      6. Convert back to sRGB (gamma 1/2.2)
    """
    lin = np.power(np.clip(srgb[..., :3], 0.0, 1.0), 2.2).astype(np.float32)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    bright = np.clip((lum - 0.68) / 0.35, 0.0, 1.0)[..., None] * lin

    # 4x downsample for fast multi-octave bloom
    small = bright[::4, ::4, :]
    b1 = blur_rgb_separable(small, 2.0) * 0.50
    b2 = blur_rgb_separable(small, 6.0) * 0.35
    b3 = blur_rgb_separable(small, 14.0) * 0.25
    bloom_small = b1 + b2 + b3
    bloom = np.repeat(np.repeat(bloom_small, 4, axis=0), 4, axis=1)[: lin.shape[0], : lin.shape[1], :]

    tint = np.array([1.0, 0.95, 0.82], dtype=np.float32)
    out = lin + bloom_strength * bloom * tint

    # Radial vignette
    h, w = lum.shape
    yy = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    r = np.sqrt(xx**2 + yy**2)
    vig = (1.0 - vignette_strength * np.clip(r - 0.52, 0.0, 1.0) ** 1.5)[..., None]
    out = out * vig

    # Convert back to sRGB + subtle seeded film grain
    srgb_out = np.power(np.clip(out, 0.0, 1.0), 1.0 / 2.2)
    if grain_strength > 0:
        rng = np.random.default_rng(seed)
        noise = rng.normal(0.0, grain_strength, size=(h // 2, w // 2, 1)).astype(np.float32)
        noise_full = np.repeat(np.repeat(noise, 2, axis=0), 2, axis=1)[:h, :w, :]
        srgb_out = np.clip(srgb_out + noise_full, 0.0, 1.0)

    return srgb_out


def process_frame_range(src_dir: Path, dst_dir: Path, first_idx: int, last_idx: int) -> int:
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in range(first_idx, last_idx + 1):
        p_in = src_dir / f"f_{f:04d}.png"
        if not p_in.exists():
            continue
        arr = read_png_rgb8(p_in)
        graded = apply_linear_glow_and_halation(arr, seed=1000 + f)
        write_png_rgb8(dst_dir / f"f_{f:04d}.png", graded)
        count += 1
    return count


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 glow.py <in_dir> <out_dir> [first last]", file=sys.stderr)
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    a = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    b = int(sys.argv[4]) if len(sys.argv) > 4 else 599
    n = process_frame_range(src, dst, a, b)
    print(f"glow pass complete: {n} frames ({a}..{b}) -> {dst}")
