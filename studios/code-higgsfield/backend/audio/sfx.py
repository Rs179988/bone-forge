#!/usr/bin/env python3
"""
Layer 3B: Frame-Accurate Procedural SFX & Cinematic Score Synthesizer
Ported & extended from higgsfield-ai/higgsfield-video-engineer (examples/felt-good-morning/tools/sfx.py)
Uses pure NumPy FFT filtering + stdlib wave module (zero scipy dependency).
Synthesizes stereo 48kHz stems for:
  whoosh, ui_pop, mechanical_click, bass_sub_drop, riser, camera_shutter, glitch_burst, boing, ding, tada
plus a rhythmic 120 BPM studio score bed with downbeat kicks and bass drop.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import wave
from pathlib import Path
from typing import Any
import numpy as np

SR = 48000


def t_vec(dur: float) -> np.ndarray:
    return np.arange(max(1, int(round(SR * dur))), dtype=np.float32) / SR


def env_ad(n: int, attack_s: float, decay_s: float) -> np.ndarray:
    e = np.ones(n, dtype=np.float32)
    na = min(n, max(1, int(SR * attack_s)))
    nd = min(n, max(1, int(SR * decay_s)))
    e[:na] = np.linspace(0.0, 1.0, na, dtype=np.float32)
    e[-nd:] *= np.linspace(1.0, 0.0, nd, dtype=np.float32)
    return e


def fft_bandpass(x: np.ndarray, f_lo: float, f_hi: float) -> np.ndarray:
    f = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / SR)
    mask = np.exp(-0.5 * (np.maximum(0.0, f_lo - freqs) / max(20.0, f_lo * 0.25)) ** 2) * np.exp(
        -0.5 * (np.maximum(0.0, freqs - f_hi) / max(40.0, f_hi * 0.2)) ** 2
    )
    return np.fft.irfft(f * mask, n=len(x)).astype(np.float32)


def fft_lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    return fft_bandpass(x, 0.0, cutoff)


def fft_highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    return fft_bandpass(x, cutoff, SR * 0.48)


def osc(freq_arr: np.ndarray, kind: str = "sine") -> np.ndarray:
    ph = 2.0 * np.pi * np.cumsum(freq_arr) / SR
    if kind == "saw":
        return (2.0 * ((ph / (2.0 * np.pi)) % 1.0) - 1.0).astype(np.float32)
    if kind == "square":
        return np.sign(np.sin(ph)).astype(np.float32)
    return np.sin(ph).astype(np.float32)


def norm(x: np.ndarray, peak: float = 0.8) -> np.ndarray:
    m = float(np.max(np.abs(x))) or 1.0
    return (x / m * peak).astype(np.float32)


# ---------------- Procedural Studio SFX Primitives ---------------- #

def sfx_whoosh(dur: float = 0.42, up: bool = True, rng: np.random.Generator | None = None) -> np.ndarray:
    r = rng or np.random.default_rng(42)
    t = t_vec(dur)
    n = r.standard_normal(len(t)).astype(np.float32)
    out = np.zeros_like(t)
    step = max(1, int(SR * 0.015))
    for i in range(0, len(t), step):
        u = i / len(t)
        fc = (280.0 + 2600.0 * u) if up else (2800.0 - 2300.0 * u)
        seg = n[i : i + step]
        out[i : i + len(seg)] = fft_bandpass(seg, fc * 0.65, fc * 1.35)
    sweep_tone = osc(np.linspace(110.0, 340.0 if up else 90.0, len(t))) * 0.25
    return norm((out + sweep_tone) * (np.sin(np.pi * t / dur) ** 1.4), 0.65)


def sfx_ui_pop(bright: float = 1.1, rng: np.random.Generator | None = None) -> np.ndarray:
    r = rng or np.random.default_rng(43)
    t = t_vec(0.11)
    n = r.standard_normal(len(t)).astype(np.float32)
    f_sweep = np.linspace(260.0 * bright, 680.0 * bright, len(t))
    body = osc(f_sweep) * np.exp(-t * 42.0) * 0.75
    snap = fft_highpass(n, 1600.0 * bright) * np.exp(-t * 85.0) * 0.45
    return norm(body + snap, 0.72)


def sfx_mechanical_click(rng: np.random.Generator | None = None) -> np.ndarray:
    r = rng or np.random.default_rng(44)
    t = t_vec(0.065)
    n = r.standard_normal(len(t)).astype(np.float32)
    click1 = fft_bandpass(n, 1800.0, 5400.0) * np.exp(-t * 140.0)
    click2 = np.roll(click1 * 0.55, int(SR * 0.018))
    res = osc(np.full(len(t), 1150.0)) * np.exp(-t * 95.0) * 0.35
    return norm(click1 + click2 + res, 0.68)


def sfx_bass_sub_drop(dur: float = 0.85, rng: np.random.Generator | None = None) -> np.ndarray:
    r = rng or np.random.default_rng(45)
    t = t_vec(dur)
    f = 42.0 + 135.0 * np.exp(-t * 7.5)
    sub = osc(f) + 0.35 * np.tanh(2.5 * osc(f * 2.0))
    punch = fft_lowpass(r.standard_normal(len(t)).astype(np.float32), 450.0) * np.exp(-t * 28.0) * 0.4
    return norm((sub * np.exp(-t * 2.6) + punch) * env_ad(len(t), 0.005, 0.12), 0.85)


def sfx_riser(dur: float = 0.75, rng: np.random.Generator | None = None) -> np.ndarray:
    r = rng or np.random.default_rng(46)
    t = t_vec(dur)
    f = np.geomspace(160.0, 1450.0, len(t))
    tone = osc(f, "saw") * 0.4 + osc(f * 1.5, "sine") * 0.35
    shimmer = fft_bandpass(r.standard_normal(len(t)).astype(np.float32), 900.0, 4800.0) * 0.35
    env = (t / dur) ** 1.8 * env_ad(len(t), 0.02, 0.04)
    return norm((tone + shimmer) * env, 0.60)


def sfx_boing(dur: float = 0.65) -> np.ndarray:
    t = t_vec(dur)
    f = 175.0 + 250.0 * (1.0 - np.exp(-t * 9.0)) + 38.0 * np.sin(2.0 * np.pi * 13.0 * t) * np.exp(-t * 3.0)
    x = osc(f) + 0.25 * osc(f * 2.01) + 0.08 * osc(f * 3.0)
    return norm(x * np.exp(-t * 4.2) * env_ad(len(t), 0.004, 0.05), 0.72)


def sfx_tada() -> np.ndarray:
    out = np.zeros(int(SR * 0.85), dtype=np.float32)
    for k, freq in enumerate([587.33, 783.99, 987.77, 1174.66]):
        t = t_vec(0.52)
        note = (osc(np.full(len(t), freq)) + 0.35 * osc(np.full(len(t), freq * 2.0))) * np.exp(-t * 5.2)
        start = int(k * SR * 0.075)
        end = min(len(out), start + len(note))
        out[start:end] += note[: end - start]
    return norm(out * env_ad(len(out), 0.005, 0.08), 0.62)


def synthesize_event_sound(kind: str, rng: np.random.Generator) -> np.ndarray:
    k = kind.lower()
    if k == "whoosh":
        return sfx_whoosh(0.40, True, rng)
    if k in ("ui_pop", "pop"):
        return sfx_ui_pop(1.15, rng)
    if k in ("mechanical_click", "click", "camera_shutter"):
        return sfx_mechanical_click(rng)
    if k in ("bass_sub_drop", "drop", "thud"):
        return sfx_bass_sub_drop(0.82, rng)
    if k in ("riser", "glitch_burst"):
        return sfx_riser(0.65, rng)
    if k == "boing":
        return sfx_boing(0.60)
    if k in ("tada", "ding"):
        return sfx_tada()
    return sfx_ui_pop(1.0, rng)


def synthesize_backing_score(duration_sec: float, bpm: float = 120.0, seed: int = 13) -> np.ndarray:
    """
    Synthesize a clean, rhythmic 120 BPM stereo studio backing track (N, 2)
    with four-on-the-floor kick, off-beat hi-hat, warm bass arpeggio, and a mid-film drop.
    """
    rng = np.random.default_rng(seed)
    total_samples = int(round(duration_sec * SR))
    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    beat_s = 60.0 / bpm
    beat_n = int(round(beat_s * SR))
    num_beats = int(math.ceil(duration_sec / beat_s))

    # Pre-build kick & hat samples
    tk = t_vec(0.24)
    kick = osc(46.0 + 110.0 * np.exp(-tk * 28.0)) * np.exp(-tk * 11.0) * 0.55
    th = t_vec(0.055)
    hat = fft_highpass(rng.standard_normal(len(th)).astype(np.float32), 5500.0) * np.exp(-th * 75.0) * 0.16

    bass_notes = [55.0, 55.0, 65.41, 73.42, 82.41, 65.41, 55.0, 49.0]  # A1 minor tech progression

    for b in range(num_beats):
        pos = b * beat_n
        if pos >= total_samples:
            break
        # Kick on every beat (stronger after beat 6 for drop contrast)
        gain = 1.18 if b >= 6 else 0.78
        end_k = min(total_samples, pos + len(kick))
        left[pos:end_k] += kick[: end_k - pos] * gain
        right[pos:end_k] += kick[: end_k - pos] * gain

        # Off-beat hat
        h_pos = pos + beat_n // 2
        if h_pos < total_samples:
            end_h = min(total_samples, h_pos + len(hat))
            left[h_pos:end_h] += hat[: end_h - h_pos] * 0.85
            right[h_pos:end_h] += hat[: end_h - h_pos] * 1.15

        # Bass pulse on 8th notes
        for sub_idx in range(2):
            s_pos = pos + sub_idx * (beat_n // 2)
            if s_pos >= total_samples:
                break
            tb = t_vec(beat_s * 0.45)
            f_bass = bass_notes[(b + sub_idx) % len(bass_notes)]
            bass_wave = (osc(np.full(len(tb), f_bass), "saw") * 0.25 + osc(np.full(len(tb), f_bass), "sine") * 0.45)
            bass_wave = fft_lowpass(bass_wave, 480.0 if b < 6 else 920.0) * env_ad(len(tb), 0.01, 0.08) * 0.28
            end_b = min(total_samples, s_pos + len(bass_wave))
            left[s_pos:end_b] += bass_wave[: end_b - s_pos] * 0.95
            right[s_pos:end_b] += bass_wave[: end_b - s_pos] * 1.05

    return np.column_stack([left, right])


def save_wav_stereo(path: Path, audio_2ch: np.ndarray, sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(audio_2ch, -0.98, 0.98)
    pcm16 = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())


def generate_sfx_and_score_for_script(script: dict[str, Any], out_wav: Path, include_score: bool = True) -> dict[str, Any]:
    duration_sec = float(script.get("duration_sec", 10.0))
    total_samples = int(round(duration_sec * SR))
    rng = np.random.default_rng(13)

    mix = synthesize_backing_score(duration_sec, bpm=120.0, seed=13) if include_score else np.zeros((total_samples, 2), dtype=np.float32)

    events_placed: list[dict[str, Any]] = []
    for idx, shot in enumerate(script.get("shots", [])):
        in_s = float(shot.get("in_sec", 0.0))
        trig = shot.get("sfx_trigger") or {"type": "whoosh", "offset_sec": 0.05}
        ev_type = str(trig.get("type", "whoosh"))
        ev_time = max(0.0, min(duration_sec - 0.1, in_s + float(trig.get("offset_sec", 0.05))))

        mono_sfx = synthesize_event_sound(ev_type, rng)
        pan = 0.5 + 0.25 * math.sin(idx * 1.7)
        stereo_sfx = np.column_stack([mono_sfx * math.sqrt(1.0 - pan), mono_sfx * math.sqrt(pan)])

        start_i = int(round(ev_time * SR))
        end_i = min(total_samples, start_i + len(stereo_sfx))
        if end_i > start_i:
            mix[start_i:end_i] += stereo_sfx[: end_i - start_i] * 0.72
            events_placed.append({"shot_id": shot.get("id", f"S{idx+1}"), "type": ev_type, "time_sec": round(ev_time, 3)})

    save_wav_stereo(out_wav, mix, sr=SR)
    return {"out_wav": str(out_wav), "duration_sec": duration_sec, "events": events_placed}


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthesize procedural SFX & studio backing score")
    parser.add_argument("out_wav", type=Path, help="Output WAV path")
    parser.add_argument("--script", type=Path, default=None, help="Optional script.json path")
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--no-music", action="store_true")
    args = parser.parse_args()

    if args.script and args.script.exists():
        script = json.loads(args.script.read_text(encoding="utf-8"))
    else:
        script = {"duration_sec": args.duration, "shots": [{"id": f"S{i+1}", "in_sec": i * 2.0, "sfx_trigger": {"type": "whoosh", "offset_sec": 0.05}} for i in range(5)]}

    info = generate_sfx_and_score_for_script(script, args.out_wav, include_score=not args.no_music)
    print(f"[sfx] synthesized {len(info['events'])} SFX events -> {args.out_wav}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
