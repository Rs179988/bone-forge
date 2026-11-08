#!/usr/bin/env python3
import os, json, subprocess
from google import genai
from google.genai import types

proj = "/workspace/studios/story-shorts-v1/projects/high-effort-flop-01"
lock_path = "/workspace/studios/story-shorts-v1/studio_lock.json"
mp4 = os.path.join(proj, "master_60fps.mp4")
sheet = os.path.join(proj, "temporal_flow_sheet.png")

with open(lock_path, "r") as f:
    studio_lock = json.load(f)

# Extract 6 story keyframes across the 3685-frame (61.4s) video:
# 1) f=45 (90-frame Cobalt/Lime Color-Block Hook Card)
# 2) f=380 (Light Graph Grid + 3D Target Cutout in Dashed Circle + 4.0 HRS vs 0.5 SEC Odometer)
# 3) f=1100 (Beat 2: 90% & 35,000 Amber Odometers + Dashed Boxes + 4-Bar Chart with Arrows)
# 4) f=1720 (Beat 3 Q1: [Faster, Sharper, Effective] Dashed Anchor-Dot Boxes + 3D Brain & Puzzle Piece)
# 5) f=2650 (Beat 3 Q3: The Cut Test + 3 Stacked Audit Rules)
# 6) f=3525 (Beat 4 Mic-Drop: -50% FX / +200% SCRIPT + 3D [INTRO DELETED] Keycap Slam)
subprocess.run([
    "ffmpeg", "-y", "-v", "error",
    "-i", mp4,
    "-vf", r"select='eq(n\,45)+eq(n\,380)+eq(n\,1100)+eq(n\,1720)+eq(n\,2650)+eq(n\,3525)',scale=360:640,tile=3x2",
    "-frames:v", "1",
    sheet
], check=True)

# Extract 4 full-res 1080x1920 hero frames
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,380)'", "-vframes", "1", os.path.join(proj, "scene_01_hook_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,1100)'", "-vframes", "1", os.path.join(proj, "scene_02_reality_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,1720)'", "-vframes", "1", os.path.join(proj, "scene_03_fix_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,3525)'", "-vframes", "1", os.path.join(proj, "scene_04_micdrop_1080p.png")], check=True)

with open(sheet, "rb") as f:
    img_bytes = f.read()

custom_rules = json.dumps(studio_lock.get("5_custom_user_rules", []), indent=2)
palette = json.dumps(studio_lock.get("3_design_system", {}).get("palette", {}), indent=2)

client = genai.Client(http_options=types.HttpOptions(timeout=30000))
resp = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
        f"""Audit this 6-keyframe contact sheet for our 60-second YouTube Short 'Why Your High-Effort Videos Flop' hosted by Iraa (The Brutally Honest Critic) against the user's studio_lock.json rules:
Palette: {palette}
Custom User Rules: {custom_rules}

Verify strictly:
1) Keyframe 1 opens with a bold Cobalt/Lime color-block reality check card before snapping into the light off-white (#EAEAE6) square graph-paper grid in Keyframes 2-6.
2) Typography pairs Italic Editorial Serif lead lines with heavy Bold Sans punch words.
3) Key list words ('Faster', 'Sharper', 'Effective' and rule cards) are inside dashed vector selection boxes with 4 corner anchor dots.
4) Visual metaphors are clearly rendered: 3D Bullseye & 3D Brain + Puzzle Piece inside dashed circular frames, 4-bar telemetry chart with curved arrow, and 3D [INTRO DELETED] mechanical keycap slam.
5) Numbers ('4.0 HRS', '0.5 SEC', '90%', '35,000', '-50%', '+200%') use odometer counters with glowing Amber (#FF9500) outer glow.
6) Zero text clipping or overlapping.

Return JSON with score (0-100), verdict (PASS/REJECT), and summary."""
    ],
    config=types.GenerateContentConfig(response_mime_type="application/json")
)
print(resp.text)
with open(os.path.join(proj, "critic_audit_report.json"), "w") as out_f:
    out_f.write(resp.text)
