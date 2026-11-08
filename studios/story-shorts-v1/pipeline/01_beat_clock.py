#!/usr/bin/env python3
import os
import json
import wave
import subprocess
import numpy as np
from google import genai
from google.genai import types

SR = 44100
FPS = 60

def load_wav_stereo(path):
    with wave.open(path, 'r') as wf:
        frames = wf.readframes(wf.getnframes())
        arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if wf.getnchannels() == 2:
            arr = arr.reshape(-1, 2)
        else:
            arr = np.column_stack((arr, arr))
        return arr

def trim_silence(audio_2ch, thresh=0.015, pad_samples=int(0.08 * SR)):
    env = np.max(np.abs(audio_2ch), axis=1)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return audio_2ch
    start = max(0, idx[0] - int(0.03 * SR))
    end = min(len(audio_2ch), idx[-1] + pad_samples)
    return audio_2ch[start:end]

def generate_tts_segment(client, text, out_wav_44k):
    raw_24k = out_wav_44k + ".24k.wav"
    resp = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"Read in a gripping, brisk, cinematic documentary storyteller voice: {text}",
        config={"response_modalities": ["AUDIO"]}
    )
    pcm_bytes = resp.candidates[0].content.parts[0].inline_data.data
    with wave.open(raw_24k, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_bytes)

    # Resample to 44.1kHz stereo via FFmpeg
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-i", raw_24k,
        "-ar", str(SR),
        "-ac", "2",
        out_wav_44k
    ], check=True)
    os.remove(raw_24k)
    audio = load_wav_stereo(out_wav_44k)
    audio = trim_silence(audio)
    # Save trimmed
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(out_wav_44k, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return audio

def build_casino_master_clock(project_dir, sfx_dir):
    os.makedirs(project_dir, exist_ok=True)
    client = genai.Client(http_options=types.HttpOptions(api_version='v1alpha', timeout=30000))

    raw_beats = [
        {
            "beat_id": "scene_01_time_trap",
            "scene_fn": "Scene_01_TimeTrap",
            "camera_mode": "punch_in",
            "spoken_line": "Walk into any Vegas casino and look at the walls. No clocks. No windows.",
            "headline": "NO CLOCKS. NO WINDOWS.",
            "sub_caption": "SENSORY DEPRIVATION TRAP"
        },
        {
            "beat_id": "scene_02_curved_maze",
            "scene_fn": "Scene_02_CurvedMaze",
            "camera_mode": "tilt_left",
            "spoken_line": "Architects banned ninety degree corners, curving every walkway so your brain never hits a decision point to leave.",
            "headline": "ZERO 90° CORNERS",
            "sub_caption": "FRIEDMAN'S LABYRINTH DESIGN"
        },
        {
            "beat_id": "scene_03_plastic_illusion",
            "scene_fn": "Scene_03_ChipIllusion",
            "camera_mode": "zoom_node",
            "spoken_line": "Even your cash is swapped for weightless plastic chips, numbing the neural pain of losing real money.",
            "headline": "CASH TO PLASTIC",
            "sub_caption": "NUMBING THE PAIN OF PAYING"
        }
    ]

    voice_segments = []
    beats_locked = []
    curr_frame = 0

    for idx, b in enumerate(raw_beats):
        seg_wav = os.path.join(project_dir, f"vo_beat_{idx+1}.wav")
        print(f"[TTS] Generating real human voiceover for {b['beat_id']}...")
        seg_audio = generate_tts_segment(client, b["spoken_line"], seg_wav)
        seg_dur = len(seg_audio) / SR
        seg_frames = int(np.ceil(seg_dur * FPS))
        # Pad audio to exact frame multiple
        target_samples = int((seg_frames / FPS) * SR)
        if len(seg_audio) < target_samples:
            pad = np.zeros((target_samples - len(seg_audio), 2), dtype=np.float32)
            seg_audio = np.vstack((seg_audio, pad))
        else:
            seg_audio = seg_audio[:target_samples]

        start_f = curr_frame
        end_f = curr_frame + seg_frames
        curr_frame = end_f

        sfx_cues = [
            {"frame": start_f, "sfx": "sub_impact.wav", "gain": 0.48},
            {"frame": start_f + 14, "sfx": "ui_tick.wav", "gain": 0.38},
            {"frame": max(start_f, end_f - 10), "sfx": "whoosh_fast.wav", "gain": 0.45}
        ]
        if idx == 2:
            sfx_cues.append({"frame": start_f + int(seg_frames * 0.45), "sfx": "lock_chime.wav", "gain": 0.45})

        beats_locked.append({
            **b,
            "start_frame": start_f,
            "end_frame": end_f,
            "duration_frames": seg_frames,
            "start_sec": round(start_f / FPS, 3),
            "end_sec": round(end_f / FPS, 3),
            "sfx_cues": sfx_cues
        })
        voice_segments.append(seg_audio)

    full_voice = np.vstack(voice_segments)
    total_samples = len(full_voice)
    total_sec = total_samples / SR
    total_frames = curr_frame

    # Normalize voiceover cleanly
    v_peak = np.max(np.abs(full_voice))
    if v_peak > 0:
        full_voice = (full_voice / v_peak) * 0.82

    # Subtle dark tension sub-bass drone under the voiceover
    t = np.linspace(0, total_sec, total_samples, endpoint=False)
    drone = (0.045 * np.sin(2 * np.pi * 52.0 * t) + 0.025 * np.sin(2 * np.pi * 104.0 * t))
    master_mix = full_voice + np.column_stack((drone, drone))

    # Mix coupled SFX cues under the voiceover
    for b in beats_locked:
        for cue in b["sfx_cues"]:
            sfx_path = os.path.join(sfx_dir, cue["sfx"])
            if os.path.exists(sfx_path):
                sfx_data = load_wav_stereo(sfx_path) * cue.get("gain", 0.4)
                s_idx = int((cue["frame"] / FPS) * SR)
                e_idx = min(len(master_mix), s_idx + len(sfx_data))
                if e_idx > s_idx:
                    master_mix[s_idx:e_idx] += sfx_data[:e_idx - s_idx]

    # Final soft limiter
    peak = np.max(np.abs(master_mix))
    if peak > 0.94:
        master_mix = (master_mix / peak) * 0.94

    master_wav = os.path.join(project_dir, "master_audio.wav")
    pcm = (np.clip(master_mix, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(master_wav, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    clock_data = {
        "project_id": "casino-trap-01",
        "topic": "Why Vegas Casinos Have No Clocks, Windows, or 90-Degree Corners",
        "fps": FPS,
        "width": 1080,
        "height": 1920,
        "total_frames": total_frames,
        "total_duration_sec": round(total_sec, 3),
        "audio_file": master_wav,
        "beats": beats_locked
    }
    clock_path = os.path.join(project_dir, "beat_clock.json")
    with open(clock_path, "w") as f:
        json.dump(clock_data, f, indent=2)

    print(f"[MASTER CLOCK LOCKED] {total_frames} frames ({total_sec:.2f}s) with REAL HUMAN VOICEOVER -> {clock_path}")

if __name__ == "__main__":
    build_casino_master_clock(
        "/workspace/studios/story-shorts-v1/projects/casino-trap-01",
        "/workspace/studios/story-shorts-v1/assets/sfx"
    )
