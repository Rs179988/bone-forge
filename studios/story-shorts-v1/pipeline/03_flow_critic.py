#!/usr/bin/env python3
import os
import json
import wave
import subprocess
import numpy as np
from google import genai
from google.genai import types

def analyze_frame_physics(mp4_path, clock_path):
    with open(clock_path, "r") as f:
        clock = json.load(f)

    # Extract scaled down RGB frames (180x320) via FFmpeg rawvideo pipe for fast NumPy motion & whitespace analysis
    W, H = 180, 320
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", mp4_path,
        "-vf", f"scale={W}:{H}",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-"
    ]
    raw = subprocess.check_output(cmd)
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W, 3).astype(np.float32)
    n_frames = len(frames)

    # 1. Frame-to-frame motion delta (mean absolute pixel difference)
    diffs = np.mean(np.abs(frames[1:] - frames[:-1]), axis=(1, 2, 3))
    dead_streak = 0
    max_dead_streak = 0
    for d in diffs:
        if d < 0.08:
            dead_streak += 1
            max_dead_streak = max(max_dead_streak, dead_streak)
        else:
            dead_streak = 0

    # 2. Whitespace / negative space ratio (pixels close to dark obsidian background #08090D -> RGB < 26)
    bg_mask = (frames[:, :, :, 0] < 28) & (frames[:, :, :, 1] < 30) & (frames[:, :, :, 2] < 38)
    whitespace_ratios = np.mean(bg_mask, axis=(1, 2))
    min_whitespace = float(np.min(whitespace_ratios))
    avg_whitespace = float(np.mean(whitespace_ratios))

    # 3. Audio-Visual Beat Alignment Check
    wav_path = clock["audio_file"]
    with wave.open(wav_path, "r") as wf:
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        pcm = pcm.reshape(-1, wf.getnchannels())
        sr = wf.getframerate()

    beat_sync_results = []
    for b in clock["beats"]:
        bf = b["start_frame"]
        sample_idx = int((bf / clock["fps"]) * sr)
        window = pcm[max(0, sample_idx):min(len(pcm), sample_idx + int(0.12 * sr))]
        peak_amp = float(np.max(np.abs(window))) if len(window) > 0 else 0.0
        beat_sync_results.append({
            "beat_id": b["beat_id"],
            "frame": bf,
            "audio_transient_peak": round(peak_amp, 3),
            "synced": peak_amp > 0.35
        })

    return {
        "total_frames_analyzed": n_frames,
        "max_dead_frame_streak": int(max_dead_streak),
        "motion_pass": max_dead_streak < 15,
        "avg_whitespace_ratio": round(avg_whitespace, 3),
        "min_whitespace_ratio": round(min_whitespace, 3),
        "whitespace_pass": min_whitespace >= 0.40,
        "beat_sync": beat_sync_results,
        "audio_sync_pass": all(x["synced"] for x in beat_sync_results)
    }

def build_temporal_sheet(mp4_path, sheet_png):
    # Extract 8 keyframes (2 per beat: entry spring + settled state) into a 4x2 temporal contact sheet
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", mp4_path,
        "-vf", "fps=1,scale=360:640,drawtext=text='T=%{pts\\:hms}':x=18:y=595:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6,tile=4x2",
        "-frames:v", "1",
        sheet_png
    ]
    subprocess.run(cmd, check=True)

def run_gemini_vision_critic(sheet_png, physics_report):
    with open(sheet_png, "rb") as f:
        img_bytes = f.read()

    client = genai.Client(http_options=types.HttpOptions(timeout=20000))
    prompt = f"""You are a ruthless 3rd-Person Editorial Video Critic auditing a 60fps programmatic short video.
Inspect the attached 8-frame temporal flow sheet (1 frame per second across 4 beats) and the deterministic physics telemetry:
{json.dumps(physics_report, indent=2)}

Evaluate strictly on 4 criteria:
1. Typography & Hierarchy (Are punch words readable, bold, max 4 words, zero full-sentence subtitle clutter?)
2. Spatial Balance & Whitespace (Are cards cleanly aligned with zero text overlapping/clipping?)
3. Archetype Progression (Do the 4 beats visually progress from Radial Hook -> Split Compare -> 3-Node Pipeline -> Benchmark Bar Payoff?)
4. Overall Studio Readiness Score (0-100) and Verdict (PASS or REJECT).

Return concise JSON only with keys: score, verdict, strengths, issues."""

    resp = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return json.loads(resp.text)

if __name__ == "__main__":
    proj = "/workspace/studios/story-shorts-v1/projects/test-01-retention"
    mp4 = os.path.join(proj, "master_60fps.mp4")
    clock = os.path.join(proj, "beat_clock.json")
    sheet = os.path.join(proj, "temporal_flow_sheet.png")
    report_out = os.path.join(proj, "critic_audit_report.json")

    print("[FLOW CRITIC] Running frame-by-frame motion, whitespace, and audio transient sync audit...")
    physics = analyze_frame_physics(mp4, clock)
    build_temporal_sheet(mp4, sheet)
    print("[FLOW CRITIC] Running Gemini 3.6 Flash Multimodal Vision Critic on temporal flow sheet...")
    ai_review = run_gemini_vision_critic(sheet, physics)

    full_report = {
        "physics_telemetry": physics,
        "multimodal_critic": ai_review
    }
    with open(report_out, "w") as f:
        json.dump(full_report, f, indent=2)

    print(json.dumps(full_report, indent=2))
