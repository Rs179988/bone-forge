#!/usr/bin/env python3
"""
Layer 2D: Deterministic Procedural Material & Texture Generator
Ported from higgsfield-ai/higgsfield-video-engineer (examples/felt-good-morning/tools/textures.py)
Uses pure NumPy FFT + stdlib zlib/struct PNG writer (zero external PIL/scipy dependency).
Generates tileable studio textures in /workspace/studios/code-higgsfield/assets/tex/:
  - felt_a.png, felt_n.png
  - paper_a.png, paper_n.png
  - brushed_metal.png
  - frosted_glass.png
  - clay_a.png
  - volumetric_fog.png
  - kodak_2383_grain.png
"""

from __future__ import annotations

import os
import struct
import sys
import zlib
from pathlib import Path
import numpy as np

DEFAULT_OUT = Path("/workspace/studios/code-higgsfield/assets/tex")


def write_png_rgb8(path: Path, arr_float: np.ndarray) -> None:
    """Write an (H, W) or (H, W, 3) float [0..1] array to an 8-bit RGB PNG using stdlib zlib."""
    a = np.clip(arr_float, 0.0, 1.0)
    if a.ndim == 2:
        a = np.stack([a, a, a], axis=-1)
    rgb = (a * 255.0 + 0.5).astype(np.uint8)
    h, w, _ = rgb.shape

    # Filter byte 0 (None) at the start of each scanline
    scanlines = np.concatenate([np.zeros((h, 1), dtype=np.uint8), rgb.reshape(h, w * 3)], axis=1)
    raw_bytes = scanlines.tobytes()

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + make_chunk(b"IHDR", ihdr)
        + make_chunk(b"IDAT", zlib.compress(raw_bytes, level=6))
        + make_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def read_png_rgb8(path: Path) -> np.ndarray:
    """Read an 8-bit RGB/RGBA PNG written by write_png_rgb8 or FFmpeg back into float32 [0..1]."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a valid PNG file: {path}")
    pos = 8
    w = h = bit_depth = color_type = 0
    idat_chunks: list[bytes] = []
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            w, h, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", chunk_data)
        elif ctype == b"IDAT":
            idat_chunks.append(chunk_data)
        elif ctype == b"IEND":
            break

    raw = zlib.decompress(b"".join(idat_chunks))
    channels = 3 if color_type == 2 else (4 if color_type == 6 else 1)
    stride = w * channels + 1
    buf = np.frombuffer(raw, dtype=np.uint8).reshape(h, stride)
    out = np.zeros((h, w * channels), dtype=np.uint8)
    bpp = channels

    for y in range(h):
        flt = int(buf[y, 0])
        row = buf[y, 1:].astype(np.int32)
        if flt == 0:
            out[y] = row
        elif flt == 1:  # Sub
            for x in range(len(row)):
                left = int(out[y, x - bpp]) if x >= bpp else 0
                out[y, x] = (row[x] + left) & 0xFF
        elif flt == 2:  # Up
            up = out[y - 1] if y > 0 else np.zeros_like(out[y])
            out[y] = (row + up) & 0xFF
        elif flt == 3:  # Average
            for x in range(len(row)):
                left = int(out[y, x - bpp]) if x >= bpp else 0
                up = int(out[y - 1, x]) if y > 0 else 0
                out[y, x] = (row[x] + ((left + up) >> 1)) & 0xFF
        elif flt == 4:  # Paeth
            for x in range(len(row)):
                a = int(out[y, x - bpp]) if x >= bpp else 0
                b = int(out[y - 1, x]) if y > 0 else 0
                c = int(out[y - 1, x - bpp]) if (y > 0 and x >= bpp) else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                out[y, x] = (row[x] + pr) & 0xFF

    img = out.reshape(h, w, channels)[..., :3]
    return img.astype(np.float32) / 255.0


def blur_wrap(h: np.ndarray, sigma: float) -> np.ndarray:
    f = np.fft.fft2(h)
    ky = np.fft.fftfreq(h.shape[0])[:, None]
    kx = np.fft.fftfreq(h.shape[1])[None, :]
    return np.real(np.fft.ifft2(f * np.exp(-2.0 * (np.pi * sigma) ** 2 * (kx**2 + ky**2)))).astype(np.float32)


def noise_wrap(rng: np.random.Generator, n: int, beta: float) -> np.ndarray:
    """Tileable 1/f^beta spectral noise normalized to [0..1]."""
    w = rng.standard_normal((n, n))
    f = np.fft.fft2(w)
    ky = np.fft.fftfreq(n)[:, None]
    kx = np.fft.fftfreq(n)[None, :]
    k = np.sqrt(kx**2 + ky**2)
    k[0, 0] = 1.0
    a = np.real(np.fft.ifft2(f / (k**beta)))
    a -= a.min()
    mx = a.max() or 1.0
    return (a / mx).astype(np.float32)


def normal_from_height(h: np.ndarray, strength: float) -> np.ndarray:
    gx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 * strength
    gy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 * strength
    n = np.stack([-gx, gy, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-8
    return n * 0.5 + 0.5


def fibers(n: int, count: int, length: int, curl: float, seed: int = 0) -> np.ndarray:
    r = np.random.default_rng(seed)
    h = np.zeros((n, n), dtype=np.float32)
    for _ in range(count):
        x, y = r.uniform(0, n, 2)
        a = r.uniform(0, 2 * np.pi)
        da = r.normal(0, curl)
        hgt = r.uniform(0.4, 1.0)
        xs = np.empty(length, dtype=np.int32)
        ys = np.empty(length, dtype=np.int32)
        for s in range(length):
            xs[s] = int(x) % n
            ys[s] = int(y) % n
            x += np.cos(a)
            y += np.sin(a)
            a += da + r.normal(0, curl * 0.5)
        np.maximum.at(h, (ys, xs), hgt)
    return h


def generate_all_textures(out_dir: Path = DEFAULT_OUT, size: int = 512) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(13)
    written: list[str] = []

    # 1. Felt (tactile wool fibres + soft fbm lump)
    fb = blur_wrap(fibers(size, 6500, 28, 0.08, seed=1), 0.8)
    lump = noise_wrap(rng, size, 1.6)
    h_felt = 0.7 * (fb / (fb.max() or 1.0)) + 0.6 * lump
    write_png_rgb8(out_dir / "felt_n.png", normal_from_height(h_felt, 9.0))
    alb_felt = np.clip((0.86 + 0.2 * (lump - 0.5)) * (0.93 + 0.12 * noise_wrap(rng, size, 2.2)), 0, 1)
    write_png_rgb8(out_dir / "felt_a.png", alb_felt)
    written.extend(["felt_n.png", "felt_a.png"])

    # 2. Cold-press Paper grain
    g1 = noise_wrap(rng, size, 0.9)
    g2 = noise_wrap(rng, size, 1.4)
    pf = blur_wrap(fibers(size, 1500, 32, 0.04, seed=3), 0.7)
    ph = 0.6 * g2 + 0.25 * g1 + 0.25 * (pf / (pf.max() or 1.0))
    write_png_rgb8(out_dir / "paper_n.png", normal_from_height(ph, 5.0))
    pa = np.clip(0.88 + 0.14 * (noise_wrap(rng, size, 2.2) - 0.5) - 0.05 * (g1 - 0.5), 0, 1)
    write_png_rgb8(out_dir / "paper_a.png", pa)
    written.extend(["paper_n.png", "paper_a.png"])

    # 3. Brushed Anodized Titanium / Metal
    streak = rng.standard_normal((size, size)).astype(np.float32)
    f = np.fft.fft2(streak)
    ky = np.fft.fftfreq(size)[:, None]
    kx = np.fft.fftfreq(size)[None, :]
    aniso = np.real(np.fft.ifft2(f * np.exp(-2 * np.pi**2 * ((kx * 28.0) ** 2 + (ky * 0.8) ** 2))))
    aniso = (aniso - aniso.min()) / ((aniso.max() - aniso.min()) or 1.0)
    metal = np.stack([0.16 + 0.12 * aniso, 0.18 + 0.13 * aniso, 0.22 + 0.15 * aniso], axis=-1)
    write_png_rgb8(out_dir / "brushed_metal.png", metal)
    written.append("brushed_metal.png")

    # 4. Frosted Glass Micro-Etch
    frost = 0.78 + 0.18 * noise_wrap(rng, size, 1.1) + 0.04 * rng.uniform(-1, 1, (size, size))
    write_png_rgb8(out_dir / "frosted_glass.png", frost)
    written.append("frosted_glass.png")

    # 5. Stop-Motion Sculpted Clay
    clay_h = noise_wrap(rng, size, 1.9) * 0.75 + noise_wrap(rng, size, 1.1) * 0.25
    clay_rgb = np.stack([0.78 * clay_h + 0.15, 0.52 * clay_h + 0.12, 0.38 * clay_h + 0.10], axis=-1)
    write_png_rgb8(out_dir / "clay_a.png", clay_rgb)
    written.append("clay_a.png")

    # 6. Volumetric Fog & Kodak 2383 Film Grain
    fog = noise_wrap(rng, size, 2.5)
    write_png_rgb8(out_dir / "volumetric_fog.png", fog)
    grain = np.clip(0.5 + 0.16 * rng.standard_normal((size, size)), 0, 1)
    write_png_rgb8(out_dir / "kodak_2383_grain.png", grain)
    written.extend(["volumetric_fog.png", "kodak_2383_grain.png"])

    return [str(out_dir / name) for name in written]


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    files = generate_all_textures(target)
    print(json.dumps({"status": "ok", "count": len(files), "textures": files}, indent=2) if "--json" in sys.argv else f"Generated {len(files)} procedural textures in {target}")
