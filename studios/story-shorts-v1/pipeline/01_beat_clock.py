#!/usr/bin/env python3
import os
import json
import wave
import numpy as np

SR = 44100
FPS = 60

def load_wav_mono(path):
    with wave.open(path, 'r') as wf:
        frames = wf.readframes(wf.getnframes())
        arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if wf.getnchannels() == 2:
            arr = arr.reshape(-1, 2)
        else:
            arr = np.column_stack((arr, arr))
        return arr

def synth_syllabic_cadence(duration_sec, syllables_per_sec=5.5, pitch_hz=125.0):
    """Synthesizes a warm editorial vocal-cadence pulse track + bass bed so audio envelope matches speech beats."""
    n = int(SR * duration_sec)
    t = np.linspace(0, duration_sec, n, endpoint=False)
    # Syllabic amplitude envelope
    syl_env = np.maximum(0, np.sin(2 * np.pi * syllables_per_sec * t)) ** 2.4
    # Formant-like warm harmonic pulse
    f0 = pitch_hz + 12.0 * np.sin(2 * np.pi * 1.3 * t)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    carrier = (
        0.55 * np.sin(phase) +
        0.30 * np.sin(2 * phase) +
        0.15 * np.sin(3 * phase)
    )
    # Subtle dark cinema sub-drone bed (55Hz A1)
    drone = 0.14 * np.sin(2 * np.pi * 55.0 * t) + 0.07 * np.sin(2 * np.pi * 110.0 * t)
    sig = carrier * syl_env * 0.22 + drone
    return np.column_stack((sig, sig))

def build_beat_clock(project_dir, sfx_dir):
    os.makedirs(project_dir, exist_ok=True)
    # 4 Tight Editorial Beats = 8.0 seconds total (480 frames @ 60fps)
    beats = [
      {
        "beat_id": "beat_01_hook",
        "archetype": "Archetype_01_HookTension",
        "camera_mode": "punch_in",
        "start_sec": 0.0,
        "end_sec": 2.0,
        "start_frame": 0,
        "end_frame": 120,
        "spoken_line": "Ninety-seven percent of AI videos fail in the first ninety frames.",
        "punch_words": ["97% FAIL", "IN 90 FRAMES"],
        "sub_metric": {"value": 97, "unit": "%", "label": "DROP-OFF BEFORE 1.5s"},
        "sfx_cues": [
          {"frame": 0, "sfx": "sub_impact.wav", "gain": 0.95},
          {"frame": 18, "sfx": "ui_tick.wav", "gain": 0.70},
          {"frame": 42, "sfx": "ui_tick.wav", "gain": 0.70},
          {"frame": 112, "sfx": "whoosh_fast.wav", "gain": 0.85}
        ]
      },
      {
        "beat_id": "beat_02_contrast",
        "archetype": "Archetype_02_SplitCompare",
        "camera_mode": "tilt_left",
        "start_sec": 2.0,
        "end_sec": 4.0,
        "start_frame": 120,
        "end_frame": 240,
        "spoken_line": "Why? Because raw prompts dump walls of text instead of visual physics.",
        "punch_words": ["WALL OF TEXT", "VS VISUAL RIG"],
        "compare_cards": {
          "bad": {"tag": "RAW PROMPT SLOP", "stat": "12% RETENTION", "flaw": "Static captions + linear boxes"},
          "good": {"tag": "STUDIO ARCHETYPE", "stat": "84% RETENTION", "edge": "Audio-locked spring choreography"}
        },
        "sfx_cues": [
          {"frame": 120, "sfx": "sub_impact.wav", "gain": 0.85},
          {"frame": 152, "sfx": "ui_tick.wav", "gain": 0.80},
          {"frame": 232, "sfx": "whoosh_fast.wav", "gain": 0.85}
        ]
      },
      {
        "beat_id": "beat_03_pipeline",
        "archetype": "Archetype_03_NodeArchitecture",
        "camera_mode": "zoom_node",
        "start_sec": 4.0,
        "end_sec": 6.0,
        "start_frame": 240,
        "end_frame": 360,
        "spoken_line": "A real editor locks the audio master-clock before a single pixel moves.",
        "punch_words": ["AUDIO CLOCK", "DRIVES PIXELS"],
        "nodes": [
          {"step": "01", "title": "BEAT SCRIPT", "ms": "0ms DRIFT"},
          {"step": "02", "title": "60FPS CLOCK", "ms": "FRAME LOCKED"},
          {"step": "03", "title": "FLOW CRITIC", "ms": "AUTO-VERIFIED"}
        ],
        "sfx_cues": [
          {"frame": 240, "sfx": "sub_impact.wav", "gain": 0.80},
          {"frame": 265, "sfx": "ui_tick.wav", "gain": 0.75},
          {"frame": 295, "sfx": "ui_tick.wav", "gain": 0.75},
          {"frame": 300, "sfx": "riser_tension.wav", "gain": 0.70},
          {"frame": 352, "sfx": "whoosh_fast.wav", "gain": 0.90}
        ]
      },
      {
        "beat_id": "beat_04_payoff",
        "archetype": "Archetype_04_MetricPayoff",
        "camera_mode": "payoff_lock",
        "start_sec": 6.0,
        "end_sec": 8.0,
        "start_frame": 360,
        "end_frame": 480,
        "spoken_line": "Zero random code. Deterministic sixty frames per second studio output.",
        "punch_words": ["60 FPS LOCKED", "STUDIO GRADE"],
        "chart_bars": [
          {"label": "GENERIC AI", "pct": 18, "color": "#8E95A8"},
          {"label": "TEMPLATE", "pct": 46, "color": "#FFB800"},
          {"label": "STUDIO ENGINE", "pct": 94, "color": "#10B981"}
        ],
        "sfx_cues": [
          {"frame": 360, "sfx": "sub_impact.wav", "gain": 0.95},
          {"frame": 385, "sfx": "lock_chime.wav", "gain": 0.90},
          {"frame": 415, "sfx": "ui_tick.wav", "gain": 0.70}
        ]
      }
    ]

    total_sec = 8.0
    total_frames = int(total_sec * FPS)
    master_audio = synth_syllabic_cadence(total_sec)

    # Mix coupled SFX cues at exact frame sample offsets
    for b in beats:
        for cue in b["sfx_cues"]:
            sfx_path = os.path.join(sfx_dir, cue["sfx"])
            if os.path.exists(sfx_path):
                sfx_data = load_wav_mono(sfx_path) * cue.get("gain", 0.8)
                start_sample = int((cue["frame"] / FPS) * SR)
                end_sample = min(len(master_audio), start_sample + len(sfx_data))
                if end_sample > start_sample:
                    master_audio[start_sample:end_sample] += sfx_data[:end_sample - start_sample]

    # Peak limiter / normalization to -1.5 dBFS
    peak = np.max(np.abs(master_audio))
    if peak > 0:
        master_audio = (master_audio / peak) * 0.84

    wav_out = os.path.join(project_dir, "master_audio.wav")
    pcm = (np.clip(master_audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(wav_out, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    clock_payload = {
        "project_id": "test-01-retention",
        "fps": FPS,
        "width": 1080,
        "height": 1920,
        "total_frames": total_frames,
        "total_duration_sec": total_sec,
        "audio_file": wav_out,
        "beats": beats
    }
    clock_path = os.path.join(project_dir, "beat_clock.json")
    with open(clock_path, "w") as f:
        json.dump(clock_payload, f, indent=2)

    print(f"[MASTER CLOCK] Locked {total_frames} frames ({total_sec}s @ {FPS}fps) + mixed audio -> {clock_path}")

if __name__ == "__main__":
    build_beat_clock(
        "/workspace/studios/story-shorts-v1/projects/test-01-retention",
        "/workspace/studios/story-shorts-v1/assets/sfx"
    )
