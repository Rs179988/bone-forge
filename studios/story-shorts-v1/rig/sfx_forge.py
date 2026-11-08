#!/usr/bin/env python3
import os
import wave
import numpy as np

SR = 44100

def save_wav(path, audio):
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(np.column_stack((pcm, pcm)).tobytes())

def gen_sub_impact(dur=0.55):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Frequency drop from 135Hz -> 34Hz + crisp transient click
    freq = 34.0 + 101.0 * np.exp(-t * 18.0)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * np.exp(-t * 6.5)
    click = np.sin(2 * np.pi * 1600 * t) * np.exp(-t * 95.0) * 0.45
    punch = np.tanh((sub + click) * 1.6) * 0.88
    return punch

def gen_whoosh_fast(dur=0.28):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 1, n)
    # Dynamic resonant sweep via windowed tonal + filtered noise
    env = np.sin(np.pi * (t / dur)) ** 1.8
    sweep_f = 180 + 1400 * (t / dur) ** 1.4
    tonal = np.sin(2 * np.pi * np.cumsum(sweep_f) / SR) * 0.35
    # Simple moving-average lowpass on noise
    kernel = np.ones(18) / 18.0
    filt_noise = np.convolve(noise, kernel, mode='same')
    return (filt_noise * 0.65 + tonal) * env * 0.72

def gen_ui_tick(dur=0.045):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    tone = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 140.0)
    body = np.sin(2 * np.pi * 620 * t) * np.exp(-t * 85.0) * 0.5
    return (tone + body) * 0.55

def gen_riser_tension(dur=1.1):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    f1 = 90 + 520 * ((t / dur) ** 2.2)
    f2 = 135 + 780 * ((t / dur) ** 2.2)
    env = ((t / dur) ** 1.9) * (1.0 - np.exp(-(dur - t) * 35.0))
    sig = 0.5 * np.sin(2 * np.pi * np.cumsum(f1) / SR) + 0.35 * np.sin(2 * np.pi * np.cumsum(f2) / SR)
    return sig * env * 0.62

def gen_lock_chime(dur=0.42):
    t = np.linspace(0, dur, int(SR * dur), endpoint=False)
    # Two-note harmonic fifth (528Hz + 792Hz)
    c1 = np.sin(2 * np.pi * 528 * t) * np.exp(-t * 7.5)
    c2 = np.sin(2 * np.pi * 792 * np.maximum(0, t - 0.045)) * np.exp(-np.maximum(0, t - 0.045) * 6.0) * (t >= 0.045)
    return (c1 * 0.55 + c2 * 0.55) * 0.75

def build_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    bank = {
        "sub_impact.wav": gen_sub_impact(),
        "whoosh_fast.wav": gen_whoosh_fast(),
        "ui_tick.wav": gen_ui_tick(),
        "riser_tension.wav": gen_riser_tension(),
        "lock_chime.wav": gen_lock_chime(),
    }
    for name, data in bank.items():
        save_wav(os.path.join(out_dir, name), data)
    print(f"[SFX FORGE] Synthesized {len(bank)} coupled studio SFX assets in {out_dir}")

if __name__ == "__main__":
    build_all("/workspace/studios/story-shorts-v1/assets/sfx")
