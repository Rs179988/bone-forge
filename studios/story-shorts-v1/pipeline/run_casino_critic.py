import os, json, subprocess
from google import genai
from google.genai import types

proj = "/workspace/studios/story-shorts-v1/projects/casino-trap-01"
lock_path = "/workspace/studios/story-shorts-v1/studio_lock.json"
mp4 = os.path.join(proj, "master_60fps.mp4")
sheet = os.path.join(proj, "temporal_flow_sheet.png")

with open(lock_path, "r") as f:
    studio_lock = json.load(f)

# Extract 6 true story keyframes across the 4 shots (3x2 grid):
# 1) f=45 (Clock intact), 2) f=115 (Clock shattering 00:00:00), 3) f=235 (Neon Vault 777),
# 4) f=480 (3D Curved Labyrinth), 5) f=672 ($100 Bill + 92% Pain), 6) f=900 (3D Casino Chips + 8% Pain)
subprocess.run([
    "ffmpeg", "-y", "-v", "error",
    "-i", mp4,
    "-vf", r"select='eq(n\,45)+eq(n\,115)+eq(n\,235)+eq(n\,480)+eq(n\,672)+eq(n\,900)',scale=360:640,tile=3x2",
    "-frames:v", "1",
    sheet
], check=True)

# Extract 3 full-res 1080x1920 hero frames
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,115)'", "-vframes", "1", os.path.join(proj, "scene_01_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,480)'", "-vframes", "1", os.path.join(proj, "scene_02_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", r"select='eq(n\,900)'", "-vframes", "1", os.path.join(proj, "scene_03_1080p.png")], check=True)

with open(sheet, "rb") as f:
    img_bytes = f.read()

palette_info = json.dumps(studio_lock.get("3_design_system", {}).get("palette", {}))
custom_rules = json.dumps(studio_lock.get("5_custom_user_rules", []))

client = genai.Client(http_options=types.HttpOptions(timeout=25000))
resp = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
        f"Audit this 6-keyframe contact sheet against studio_lock.json palette {palette_info} and custom rules {custom_rules}. Verify: 1) Zero text clipping at borders, 2) All 4 visual storytelling metaphors clearly visible (Clock intact -> Clock shattering 00:00:00 -> Neon Vault 777 -> 3D Curved Labyrinth -> $100 Cash Bill at 92% Pain -> 3D Casino Chips at 8% Pain), 3) Exact 6-swatch Rooster palette applied (#3B2336 Aubergine, #009E83 Jade Teal, #F24414 Vermilion, #F38BA8 Flamingo Pink, #FBA40D Marigold, #E7E4DD Bone Cream). Return JSON with score (0-100), verdict (PASS/REJECT), and summary."
    ],
    config=types.GenerateContentConfig(response_mime_type="application/json")
)
print(resp.text)
