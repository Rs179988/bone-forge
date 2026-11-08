#!/usr/bin/env python3
"""
Layer 3A: Pure-NumPy Music & Audio Bar-Map / Beatmap Analyzer
Adapted from higgsfield-ai/higgsfield-video-engineer (skills/code-based-films/tools/beatmap.py)
Replaced scipy with pure numpy.fft + numpy stride tricks so it runs with zero external C-extensions.
Outputs beatmap.json with:
  bpm, beat, bar, fps, duration, beats[], downbeats[], hits[], drops[], energy_envelope[], frames: {...}
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

SR = 22050
HOP = 256  # ~11.6 ms hop


def decode_audio_mono(path: Path, start: float = 0.0, dur: float | None = None, sr: int = SR) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if start > 0:
        cmd += ["-ss", f"{start:.4f}"]
    cmd += ["-i", str(path)]
    if dur:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or not res.stdout:
        raise RuntimeError(f"beatmap: ffmpeg failed to decode {path}: {res.stderr.decode(errors='replace')[:300]}")
    return np.frombuffer(res.stdout, dtype="<f4").astype(np.float32)


def analyze_beatmap(
    audio_path: Path,
    fps: int = 60,
    start: float = 0.0,
    dur: float | None = None,
) -> dict[str, Any]:
    y = decode_audio_mono(audio_path, start=start, dur=dur, sr=SR)
    duration = float(len(y)) / SR
    if duration < 0.5:
        raise ValueError(f"Audio track too short ({duration:.2f}s)")

    n_fft = 1024
    padded = np.pad(y, n_fft // 2)
    frames = sliding_window_view(padded, n_fft)[::HOP]
    hann = (0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(n_fft, dtype=np.float32) / n_fft))[None, :]
    spec = np.abs(np.fft.rfft(frames * hann, axis=1))  # shape: (n_frames, n_fft//2 + 1)

    freqs = np.fft.rfftfreq(n_fft, 1.0 / SR)
    low_mask = freqs <= 150.0

    # Log-power spectrogram & spectral flux onset envelope
    spec_db = 20.0 * np.log10(np.maximum(spec, 1e-7))
    flux = np.maximum(0.0, spec_db[1:, :] - spec_db[:-1, :]).mean(axis=1)
    flux = np.concatenate([[0.0], flux])
    flux_norm = flux / (np.max(flux) or 1.0)

    low_energy = np.sqrt(np.mean(spec[:, low_mask] ** 2, axis=1))
    low_norm = low_energy / (np.max(low_energy) or 1.0)

    rms = np.sqrt(np.mean(spec**2, axis=1))
    rms_norm = rms / (np.max(rms) or 1.0)

    # Autocorrelation tempogram over 75..165 BPM
    ac_full = np.correlate(flux_norm - flux_norm.mean(), flux_norm - flux_norm.mean(), mode="full")
    ac = ac_full[len(ac_full) // 2 :]
    min_lag = max(1, int(round((60.0 / 165.0) * SR / HOP)))
    max_lag = min(len(ac) - 1, int(round((60.0 / 75.0) * SR / HOP)))

    if max_lag > min_lag:
        best_lag = min_lag + int(np.argmax(ac[min_lag : max_lag + 1]))
        bpm = round(float(60.0 * SR / (best_lag * HOP)), 1)
    else:
        bpm = 120.0

    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0

    # Find best beat phase alignment using low-band kick energy
    phase_steps = 16
    best_phase = 0.0
    best_score = -1.0
    for p_idx in range(phase_steps):
        cand_phase = (p_idx / phase_steps) * beat_sec
        beat_times = np.arange(cand_phase, duration, beat_sec)
        beat_hops = np.clip((beat_times * SR / HOP).astype(int), 0, len(low_norm) - 1)
        score = float(np.mean(low_norm[beat_hops] + 0.6 * flux_norm[beat_hops]))
        if score > best_score:
            best_score = score
            best_phase = cand_phase

    beats = [round(float(t), 4) for t in np.arange(best_phase, duration, beat_sec)]

    # Choose bar downbeat phase (0, 1, 2, or 3) with strongest low-band kick energy
    best_bar_offset = 0
    best_bar_energy = -1.0
    for off in range(min(4, len(beats))):
        bar_beats = beats[off::4]
        hops = np.clip([int(round(t * SR / HOP)) for t in bar_beats], 0, len(low_norm) - 1)
        e = float(np.mean(low_norm[hops])) if len(hops) else 0.0
        if e > best_bar_energy:
            best_bar_energy = e
            best_bar_offset = off

    downbeats = beats[best_bar_offset::4]
    if not downbeats and beats:
        downbeats = [beats[0]]

    # Top transient hits (de-duplicated >= 0.18s apart)
    hit_indices = np.argsort(flux_norm)[::-1]
    hits: list[float] = []
    for idx in hit_indices:
        if flux_norm[idx] < 0.25:
            break
        t_hit = round(float(idx * HOP / SR), 4)
        if all(abs(t_hit - existing) >= 0.18 for existing in hits):
            hits.append(t_hit)
        if len(hits) >= 12:
            break
    hits.sort()

    # Detect main drop (largest bar-to-bar RMS jump or strongest downbeat transient in middle 25%-85% of track)
    drop_sec = downbeats[min(2, len(downbeats) - 1)] if downbeats else round(duration * 0.55, 3)
    best_jump = -1.0
    for d_t in downbeats:
        if duration * 0.2 <= d_t <= duration * 0.85:
            h_idx = int(round(d_t * SR / HOP))
            pre = float(np.mean(rms_norm[max(0, h_idx - 25) : max(1, h_idx)]))
            post = float(np.mean(rms_norm[h_idx : min(len(rms_norm), h_idx + 25)]))
            jump = post - pre + 0.3 * float(low_norm[min(h_idx, len(low_norm) - 1)])
            if jump > best_jump:
                best_jump = jump
                drop_sec = round(d_t, 4)

    # Sample energy envelope at 20Hz for UI waveform & character lip/pulse sync
    env_times = np.linspace(0, duration, max(10, int(duration * 20)), endpoint=False)
    env_hops = np.clip((env_times * SR / HOP).astype(int), 0, len(rms_norm) - 1)
    energy_envelope = [round(float(rms_norm[h]), 3) for h in env_hops]

    return {
        "bpm": bpm,
        "beat": round(beat_sec, 4),
        "bar": round(bar_sec, 4),
        "fps": fps,
        "start": start,
        "duration": round(duration, 4),
        "source": str(audio_path),
        "beats": beats,
        "downbeats": downbeats,
        "hits": hits,
        "drop": drop_sec,
        "frames": {
            "beats": [int(round(t * fps)) for t in beats],
            "downbeats": [int(round(t * fps)) for t in downbeats],
            "hits": [int(round(t * fps)) for t in hits],
            "drop": int(round(drop_sec * fps)),
        },
        "energy_envelope": energy_envelope,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze audio/video track into Higgsfield beatmap.json")
    parser.add_argument("input_path", type=Path, help="Audio or video file path")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--dur", type=float, default=None)
    parser.add_argument("--out", type=Path, required=True, help="Output beatmap.json path")
    args = parser.parse_args()

    data = analyze_beatmap(args.input_path, fps=args.fps, start=args.start, dur=args.dur)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"[beatmap] {data['bpm']} BPM, {len(data['downbeats'])} bars, drop @ {data['drop']}s -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
