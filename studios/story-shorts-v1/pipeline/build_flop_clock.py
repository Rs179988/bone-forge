#!/usr/bin/env python3
import os
import json
import wave
import subprocess
import numpy as np
from google import genai
from google.genai import types

STUDIO_LOCK_PATH = "/workspace/studios/story-shorts-v1/studio_lock.json"
with open(STUDIO_LOCK_PATH, "r") as f:
    STUDIO_LOCK = json.load(f)

TECH = STUDIO_LOCK.get("1_tech_specs", {})
PERSONA = STUDIO_LOCK.get("2_channel_persona_and_pacing", {})

SR = TECH.get("audio_sample_rate", 44100)
FPS = TECH.get("fps", 60)
TTS_PROMPT = PERSONA.get("tts_voice_prompt", "Read in a sharp, confident, brisk female voice.")
ATEMPO = PERSONA.get("voice_speed_atempo", 1.26)

def load_wav_stereo(path):
    with wave.open(path, 'r') as wf:
        frames = wf.readframes(wf.getnframes())
        arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if wf.getnchannels() == 2:
            arr = arr.reshape(-1, 2)
        else:
            arr = np.column_stack((arr, arr))
        return arr

def trim_silence(audio_2ch, thresh=0.018, pad_samples=int(0.05 * SR)):
    env = np.max(np.abs(audio_2ch), axis=1)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return audio_2ch
    start = max(0, idx[0] - int(0.02 * SR))
    end = min(len(audio_2ch), idx[-1] + pad_samples)
    return audio_2ch[start:end]

def generate_female_tts_segment(client, text, out_wav_44k):
    raw_24k = out_wav_44k + ".24k.wav"
    untight_44k = out_wav_44k + ".raw44k.wav"

    resp = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"{TTS_PROMPT}: {text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                )
            )
        )
    )
    pcm_bytes = resp.candidates[0].content.parts[0].inline_data.data
    with wave.open(raw_24k, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_bytes)

    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-i", raw_24k,
        "-filter:a", f"atempo={ATEMPO}",
        "-ar", str(SR),
        "-ac", "2",
        untight_44k
    ], check=True)
    os.remove(raw_24k)

    audio = load_wav_stereo(untight_44k)
    os.remove(untight_44k)
    audio = trim_silence(audio)

    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(out_wav_44k, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return audio

def build_flop_master_clock(project_dir, sfx_dir):
    os.makedirs(project_dir, exist_ok=True)
    client = genai.Client(http_options=types.HttpOptions(api_version='v1alpha', timeout=45000))

    raw_beats = [
        {
            "beat_id": "beat_01_hook_pattern_interrupt",
            "act_title": "THE HOOK // PATTERN INTERRUPT",
            "spoken_line": "Tumne apni pichli video ke 3-second ke transition par 4 ghante lagaye... aur viewer ne use 0.5 second mein swipe kar diya. Bura laga? Good. Ab sach suno.",
            "headline": "4 HRS WORK -> 0.5s SWIPE",
            "sub_caption": "BRUTAL REALITY CHECK"
        },
        {
            "beat_id": "beat_02_reality_check_agitation",
            "act_title": "THE REALITY CHECK // EDITOR FLEX",
            "spoken_line": "90 percent naye creators ko lagta hai ki unhe ek viral editing pack ya naye AI plugin ki zaroorat hai. Nahi. Tumhara color grade cinematic hai, sound design crispy hai—par tumhari video boring hai. Kyunki tum apne liye edit kar rahe ho, dusre editors ko flex dikhane ke liye. Audience ko tumhare keyframes se ghanta farak nahi padta.",
            "headline": "90% CHASE PLUGINS",
            "sub_caption": "AUDIENCE DOESN'T CARE ABOUT KEYFRAMES"
        },
        {
            "beat_id": "beat_03_the_fix_three_questions",
            "act_title": "THE FIX // 3 BRUTAL QUESTIONS",
            "spoken_line": "Agli video render karne se pehle apne timeline ko mute karo, saare effects band karo, aur khud se yeh teen sawaal poocho. Pehla, 3-Second Hook: Kya mera pehla sentence kisi ke dimaag mein khujli paida kar raha hai? Agar tum Hey guys welcome back bol rahe ho, toh wahin khel khatam hai. Doosra, 15-Second Rule: Kya har 15 second mein story ki direction badal rahi hai? Teesra, The Cut Test: Agar main is clip ko hata doon, toh kya story tootegi? Agar nahi, toh delete maaro.",
            "headline": "FASTER. SHARPER. EFFECTIVE.",
            "sub_caption": "3-SEC HOOK // 15-SEC SHIFT // CUT TEST"
        },
        {
            "beat_id": "beat_04_mic_drop_outro",
            "act_title": "MIC-DROP // DELETE THE FLUFF",
            "spoken_line": "Editing ka kaam story ko chhupana nahi, story ko raste se bhatakne se rokna hai. Agli video mein 50 percent kam effects lagao, aur 200 percent zyada dimaag apne hook aur script par lagao. Ab yeh Reel save karke mat chhod dena—apna timeline kholo aur sabse pehle woh fancy intro udao.",
            "headline": "-50% FX // +200% SCRIPT",
            "sub_caption": "DELETE THAT FANCY INTRO NOW"
        }
    ]

    voice_segments = []
    beats_locked = []
    curr_frame = 0

    for idx, b in enumerate(raw_beats):
        seg_wav = os.path.join(project_dir, f"vo_beat_{idx+1}.wav")
        print(f"[TTS-IRAA] Generating female voiceover for {b['beat_id']}...")
        seg_audio = generate_female_tts_segment(client, b["spoken_line"], seg_wav)
        seg_dur = len(seg_audio) / SR
        seg_frames = int(np.ceil(seg_dur * FPS))
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
            {"frame": start_f, "sfx": "sub_impact.wav", "gain": 0.46},
            {"frame": start_f + 16, "sfx": "ui_tick.wav", "gain": 0.40},
            {"frame": start_f + int(seg_frames * 0.42), "sfx": "ui_tick.wav", "gain": 0.40},
            {"frame": start_f + int(seg_frames * 0.72), "sfx": "ui_tick.wav", "gain": 0.40},
            {"frame": max(start_f, end_f - 9), "sfx": "whoosh_fast.wav", "gain": 0.44}
        ]
        if idx == 0:
            # Snap from 90-frame bold color-block card into Light Graph Grid at frame 90
            sfx_cues.append({"frame": min(end_f - 5, 90), "sfx": "sub_impact.wav", "gain": 0.48})
        if idx == 3:
            # Loud THUD when pressing DELETE key on the bloated timeline chunk
            del_frame = start_f + int(seg_frames * 0.78)
            sfx_cues.append({"frame": del_frame, "sfx": "sub_impact.wav", "gain": 0.58})
            sfx_cues.append({"frame": del_frame + 4, "sfx": "lock_chime.wav", "gain": 0.45})

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

    v_peak = np.max(np.abs(full_voice))
    if v_peak > 0:
        full_voice = (full_voice / v_peak) * 0.86

    # Subtle tactile rhythmic pulse under voiceover
    t = np.linspace(0, total_sec, total_samples, endpoint=False)
    bed = 0.018 * np.sin(2 * np.pi * 65.0 * t)
    master_mix = full_voice + np.column_stack((bed, bed))

    for b in beats_locked:
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

    master_wav = os.path.join(project_dir, "master_audio.wav")
    pcm = (np.clip(master_mix, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(master_wav, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

    clock_data = {
        "project_id": "high-effort-flop-01",
        "topic": "Tumhare 'High-Effort' Videos Flop Kyun Ho Rahe Hain?",
        "host": PERSONA.get("host_name", "Iraa"),
        "persona": PERSONA.get("host_persona", "The Brutally Honest Critic"),
        "fps": FPS,
        "width": TECH.get("width", 1080),
        "height": TECH.get("height", 1920),
        "total_frames": total_frames,
        "total_duration_sec": round(total_sec, 3),
        "audio_file": master_wav,
        "beats": beats_locked
    }
    clock_path = os.path.join(project_dir, "beat_clock.json")
    with open(clock_path, "w") as f:
        json.dump(clock_data, f, indent=2)

    print(f"[IRAA MASTER CLOCK LOCKED] {total_frames} frames ({total_sec:.2f}s @ {FPS}fps) -> {clock_path}")

if __name__ == "__main__":
    build_flop_master_clock(
        "/workspace/studios/story-shorts-v1/projects/high-effort-flop-01",
        "/workspace/studios/story-shorts-v1/assets/sfx"
    )
