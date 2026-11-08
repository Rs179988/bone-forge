import os, json, wave, subprocess
import numpy as np

SR = 44100
FPS = 60
proj_dir = "/workspace/studios/story-shorts-v1/projects/casino-trap-01"
sfx_dir = "/workspace/studios/story-shorts-v1/assets/sfx"

with open(os.path.join(proj_dir, "beat_clock.json")) as f:
    clock = json.load(f)

def load_wav_stereo(path):
    with wave.open(path, 'r') as wf:
        arr = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        return arr.reshape(-1, 2) if wf.getnchannels() == 2 else np.column_stack((arr, arr))

voice_segments = []
curr_frame = 0

for idx, b in enumerate(clock["beats"]):
    in_wav = os.path.join(proj_dir, f"vo_beat_{idx+1}.wav")
    fast_wav = os.path.join(proj_dir, f"vo_beat_{idx+1}_fast.wav")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-i", in_wav,
        "-filter:a", "atempo=1.26",
        "-ar", str(SR), "-ac", "2",
        fast_wav
    ], check=True)
    seg = load_wav_stereo(fast_wav)
    # Trim any trailing silence > 0.02
    env = np.max(np.abs(seg), axis=1)
    nz = np.where(env > 0.018)[0]
    if len(nz) > 0:
        seg = seg[max(0, nz[0]-int(0.02*SR)):min(len(seg), nz[-1]+int(0.06*SR))]

    seg_frames = int(np.ceil((len(seg) / SR) * FPS))
    target_samples = int((seg_frames / FPS) * SR)
    if len(seg) < target_samples:
        seg = np.vstack((seg, np.zeros((target_samples - len(seg), 2), dtype=np.float32)))
    else:
        seg = seg[:target_samples]

    start_f = curr_frame
    end_f = curr_frame + seg_frames
    curr_frame = end_f

    b["start_frame"] = start_f
    b["end_frame"] = end_f
    b["duration_frames"] = seg_frames
    b["start_sec"] = round(start_f / FPS, 3)
    b["end_sec"] = round(end_f / FPS, 3)
    b["sfx_cues"] = [
        {"frame": start_f, "sfx": "sub_impact.wav", "gain": 0.45},
        {"frame": start_f + int(seg_frames * 0.32), "sfx": "ui_tick.wav", "gain": 0.35},
        {"frame": start_f + int(seg_frames * 0.62), "sfx": "lock_chime.wav" if idx == 2 else "ui_tick.wav", "gain": 0.42},
        {"frame": max(start_f, end_f - 9), "sfx": "whoosh_fast.wav", "gain": 0.44}
    ]
    voice_segments.append(seg)

full_voice = np.vstack(voice_segments)
v_peak = np.max(np.abs(full_voice))
if v_peak > 0:
    full_voice = (full_voice / v_peak) * 0.85

total_samples = len(full_voice)
total_sec = total_samples / SR
t = np.linspace(0, total_sec, total_samples, endpoint=False)
drone = 0.04 * np.sin(2 * np.pi * 52.0 * t) + 0.02 * np.sin(2 * np.pi * 104.0 * t)
master_mix = full_voice + np.column_stack((drone, drone))

for b in clock["beats"]:
    for cue in b["sfx_cues"]:
        sfx_path = os.path.join(sfx_dir, cue["sfx"])
        if os.path.exists(sfx_path):
            sfx_data = load_wav_stereo(sfx_path) * cue.get("gain", 0.4)
            s_idx = int((cue["frame"] / FPS) * SR)
            e_idx = min(len(master_mix), s_idx + len(sfx_data))
            if e_idx > s_idx:
                master_mix[s_idx:e_idx] += sfx_data[:e_idx - s_idx]

peak = np.max(np.abs(master_mix))
if peak > 0.95:
    master_mix = (master_mix / peak) * 0.95

master_wav = os.path.join(proj_dir, "master_audio.wav")
pcm = (np.clip(master_mix, -1.0, 1.0) * 32767).astype(np.int16)
with wave.open(master_wav, "w") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())

clock["total_frames"] = curr_frame
clock["total_duration_sec"] = round(total_sec, 3)
with open(os.path.join(proj_dir, "beat_clock.json"), "w") as f:
    json.dump(clock, f, indent=2)

print(f"[TIGHTENED MASTER CLOCK] {curr_frame} frames ({total_sec:.2f}s @ 60fps)")
