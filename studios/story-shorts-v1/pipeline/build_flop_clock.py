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
    if os.path.exists(out_wav_44k) and os.path.getsize(out_wav_44k) > 10000:
        return load_wav_stereo(out_wav_44k)

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
            "spoken_line": "Tumne apni pichli video ke 3-second ke transition par 4 ghante lagaye... aur viewer ne use 0.5 second mein swipe kar diya. Bura laga? Good. Ab sach suno."
        },
        {
            "beat_id": "beat_02_reality_check_agitation",
            "spoken_line": "90 percent naye creators ko lagta hai ki unhe ek viral editing pack ya naye AI plugin ki zaroorat hai. Nahi. Tumhara color grade cinematic hai, sound design crispy hai—par tumhari video boring hai. Kyunki tum apne liye edit kar rahe ho, dusre editors ko flex dikhane ke liye. Audience ko tumhare keyframes se ghanta farak nahi padta."
        },
        {
            "beat_id": "beat_03_the_fix_three_questions",
            "spoken_line": "Agli video render karne se pehle apne timeline ko mute karo, saare effects band karo, aur khud se yeh teen sawaal poocho. Pehla, 3-Second Hook: Kya mera pehla sentence kisi ke dimaag mein khujli paida kar raha hai? Agar tum Hey guys welcome back bol rahe ho, toh wahin khel khatam hai. Doosra, 15-Second Rule: Kya har 15 second mein story ki direction badal rahi hai? Teesra, The Cut Test: Agar main is clip ko hata doon, toh kya story tootegi? Agar nahi, toh delete maaro."
        },
        {
            "beat_id": "beat_04_mic_drop_outro",
            "spoken_line": "Editing ka kaam story ko chhupana nahi, story ko raste se bhatakne se rokna hai. Agli video mein 50 percent kam effects lagao, aur 200 percent zyada dimaag apne hook aur script par lagao. Ab yeh Reel save karke mat chhod dena—apna timeline kholo aur sabse pehle woh fancy intro udao."
        }
    ]

    voice_segments = []
    beats_locked = []
    curr_frame = 0

    for idx, b in enumerate(raw_beats):
        seg_wav = os.path.join(project_dir, f"vo_beat_{idx+1}.wav")
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

        beats_locked.append({
            **b,
            "start_frame": start_f,
            "end_frame": end_f,
            "duration_frames": seg_frames,
            "start_sec": round(start_f / FPS, 3),
            "end_sec": round(end_f / FPS, 3)
        })
        voice_segments.append(seg_audio)

    # 14 Dynamic Story Scenes synced to exact voiceover speech pauses (0..3685)
    scenes = [
        {"scene_id": "s01_hook_card",       "start_frame": 0,    "end_frame": 90,   "camera": "snap_zoom",  "spoken_focus": "Tumne apni pichli video ke 3-second ke transition..."},
        {"scene_id": "s02_four_hours_nle",  "start_frame": 90,   "end_frame": 258,  "camera": "push_in",    "spoken_focus": "...par 4 ghante lagaye..."},
        {"scene_id": "s03_half_sec_swipe",  "start_frame": 258,  "end_frame": 449,  "camera": "pan_up",     "spoken_focus": "...aur viewer ne use 0.5 second mein swipe kar diya."},
        {"scene_id": "s04_bura_laga_truth", "start_frame": 449,  "end_frame": 590,  "camera": "snap_zoom",  "spoken_focus": "Bura laga? Good. Ab sach suno."},
        {"scene_id": "s05_ninety_pct_trap", "start_frame": 590,  "end_frame": 906,  "camera": "push_in",    "spoken_focus": "90% naye creators ko lagta hai viral pack ya AI plugin chahiye. Nahi."},
        {"scene_id": "s06_grade_vs_boring", "start_frame": 906,  "end_frame": 1179, "camera": "tilt_focus", "spoken_focus": "Color grade cinematic hai, sound crispy hai—par video boring hai."},
        {"scene_id": "s07_editor_ego_bars", "start_frame": 1179, "end_frame": 1535, "camera": "pan_up",     "spoken_focus": "Dusre editors ko flex dikhane ke liye. Audience ko keyframes se farak nahi padta."},
        {"scene_id": "s08_mute_three_q",    "start_frame": 1535, "end_frame": 1812, "camera": "snap_zoom",  "spoken_focus": "Timeline mute karo, effects band karo, aur yeh 3 sawaal poocho."},
        {"scene_id": "s09_q1_curiosity",    "start_frame": 1812, "end_frame": 2156, "camera": "push_in",    "spoken_focus": "Pehle 3 second: Curiosity gap vs Hey guys welcome back drop-off."},
        {"scene_id": "s10_q2_15sec_twist",  "start_frame": 2156, "end_frame": 2549, "camera": "tilt_focus", "spoken_focus": "The 15-Second Rule: Har 15 second mein story direction shift."},
        {"scene_id": "s11_q3_cut_test",     "start_frame": 2549, "end_frame": 2858, "camera": "snap_zoom",  "spoken_focus": "The Cut Test: Clip hatane se story na toote toh delete maaro."},
        {"scene_id": "s12_story_compass",   "start_frame": 2858, "end_frame": 3158, "camera": "push_in",    "spoken_focus": "Editing ka kaam story ko chhupana nahi, bhatakne se rokna hai."},
        {"scene_id": "s13_fx_vs_script",    "start_frame": 3158, "end_frame": 3409, "camera": "pan_up",     "spoken_focus": "50% kam effects lagao, aur 200% zyada dimaag hook aur script par."},
        {"scene_id": "s14_delete_intro",    "start_frame": 3409, "end_frame": 3685, "camera": "snap_zoom",  "spoken_focus": "Timeline kholo aur sabse pehle woh fancy intro udao."}
    ]

    # Build frame-accurate SFX cues across all 14 dynamic scene cuts
    all_sfx_cues = []
    for idx, sc in enumerate(scenes):
        sf = sc["start_frame"]
        ef = sc["end_frame"]
        all_sfx_cues.append({"frame": sf, "sfx": "sub_impact.wav" if idx in (0, 1, 3, 4, 7, 13) else "whoosh_fast.wav", "gain": 0.46})
        all_sfx_cues.append({"frame": sf + 12, "sfx": "ui_tick.wav", "gain": 0.38})
        if (ef - sf) > 180:
            all_sfx_cues.append({"frame": sf + (ef - sf) // 2, "sfx": "ui_tick.wav", "gain": 0.36})

    # Special action SFX cues:
    # 1) "Nahi." stamp in Scene 5 at f=865
    all_sfx_cues.append({"frame": 865, "sfx": "sub_impact.wav", "gain": 0.50})
    # 2) Scissor snip in Scene 11 at f=2680
    all_sfx_cues.append({"frame": 2680, "sfx": "lock_chime.wav", "gain": 0.46})
    # 3) Giant 3D [DELETE] keycap slam in Scene 14 at f=3503
    all_sfx_cues.append({"frame": 3503, "sfx": "sub_impact.wav", "gain": 0.62})
    all_sfx_cues.append({"frame": 3507, "sfx": "lock_chime.wav", "gain": 0.48})

    full_voice = np.vstack(voice_segments)
    total_samples = len(full_voice)
    total_sec = total_samples / SR
    total_frames = curr_frame

    v_peak = np.max(np.abs(full_voice))
    if v_peak > 0:
        full_voice = (full_voice / v_peak) * 0.86

    t = np.linspace(0, total_sec, total_samples, endpoint=False)
    bed = 0.016 * np.sin(2 * np.pi * 65.0 * t)
    master_mix = full_voice + np.column_stack((bed, bed))

    for cue in all_sfx_cues:
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
        "beats": beats_locked,
        "scenes": scenes,
        "sfx_cues": all_sfx_cues
    }
    clock_path = os.path.join(project_dir, "beat_clock.json")
    with open(clock_path, "w") as f:
        json.dump(clock_data, f, indent=2)

    print(f"[IRAA DYNAMIC 14-SCENE CLOCK LOCKED] {total_frames} frames ({total_sec:.2f}s @ {FPS}fps) -> {clock_path}")

if __name__ == "__main__":
    build_flop_master_clock(
        "/workspace/studios/story-shorts-v1/projects/high-effort-flop-01",
        "/workspace/studios/story-shorts-v1/assets/sfx"
    )
