import os, json, subprocess
from google import genai
from google.genai import types

proj = "/workspace/studios/story-shorts-v1/projects/casino-trap-01"
mp4 = os.path.join(proj, "master_60fps.mp4")
sheet = os.path.join(proj, "temporal_flow_sheet.png")

# Extract 6 keyframes across the 16.4s video (3x2 grid)
subprocess.run([
    "ffmpeg", "-y", "-v", "error",
    "-i", mp4,
    "-vf", "select='eq(n\,30)+eq(n\,180)+eq(n\,420)+eq(n\,620)+eq(n\,830)+eq(n\,940)',scale=360:640,tile=3x2",
    "-frames:v", "1",
    sheet
], check=True)

# Also extract 3 full-res 1080x1920 hero frames
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", "select='eq(n\,180)'", "-vframes", "1", os.path.join(proj, "scene_01_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", "select='eq(n\,620)'", "-vframes", "1", os.path.join(proj, "scene_02_1080p.png")], check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-vf", "select='eq(n\,940)'", "-vframes", "1", os.path.join(proj, "scene_03_1080p.png")], check=True)

with open(sheet, "rb") as f:
    img_bytes = f.read()

client = genai.Client(http_options=types.HttpOptions(timeout=25000))
resp = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[
        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
        "Audit this 6-frame contact sheet of our 'Why Casinos Have No Clocks or Windows' documentary short. Verify: 1) No text clipping at borders, 2) Visual storytelling metaphors (clock/window blocked + slot machine, 90-degree corner vs curved maze, $100 cash morphing into casino chips + insula brain meter), 3) Consistent host character presence. Return JSON with score (0-100), verdict (PASS/REJECT), and summary."
    ],
    config=types.GenerateContentConfig(response_mime_type="application/json")
)
print(resp.text)
