#!/usr/bin/env python3
import os
import sys
import json
import time
import base64
import asyncio
import subprocess
import urllib.request
import websockets

async def render_frames_via_cdp(html_path, clock_path, out_mp4):
    with open(clock_path, "r") as f:
        clock = json.load(f)

    total_frames = clock["total_frames"]
    fps = clock["fps"]
    audio_file = clock["audio_file"]

    port = 9229
    chrome_cmd = [
        "/usr/bin/google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--window-size=1080,1920",
        f"--remote-debugging-port={port}",
        f"file://{os.path.abspath(html_path)}"
    ]
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws_url = None
        for _ in range(40):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    targets = json.loads(resp.read().decode())
                    for t in targets:
                        if t.get("type") == "page":
                            ws_url = t["webSocketDebuggerUrl"]
                            break
                if ws_url:
                    break
            except Exception:
                pass
            time.sleep(0.15)

        if not ws_url:
            raise RuntimeError("Failed to connect to Headless Chrome CDP WebSocket.")

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-r", str(fps),
            "-i", "-",
            "-i", audio_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "17",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            out_mp4
        ]
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            msg_id = 1
            async def cdp_call(method, params=None):
                nonlocal msg_id
                curr = msg_id
                msg_id += 1
                await ws.send(json.dumps({"id": curr, "method": method, "params": params or {}}))
                while True:
                    raw = await ws.recv()
                    data = json.loads(raw)
                    if data.get("id") == curr:
                        return data.get("result", {})

            await cdp_call("Page.enable")
            await cdp_call("Runtime.enable")
            await cdp_call("Emulation.setDeviceMetricsOverride", {
                "width": 1080,
                "height": 1920,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            await asyncio.sleep(0.25)
            clock_json_str = json.dumps(clock)
            await cdp_call("Runtime.evaluate", {
                "expression": f"window.initClock({clock_json_str});",
                "returnByValue": True
            })

            t0 = time.time()
            for frame in range(total_frames):
                await cdp_call("Runtime.evaluate", {
                    "expression": f"window.seekToFrame({frame});",
                    "returnByValue": True
                })
                shot = await cdp_call("Page.captureScreenshot", {
                    "format": "jpeg",
                    "quality": 96,
                    "fromSurface": True
                })
                img_bytes = base64.b64decode(shot["data"])
                ffmpeg_proc.stdin.write(img_bytes)
                if (frame + 1) % 120 == 0 or frame == total_frames - 1:
                    elapsed = time.time() - t0
                    print(f"  [RENDER] Frame {frame + 1}/{total_frames} ({(frame + 1) / elapsed:.1f} fps capture speed)")

        ffmpeg_proc.stdin.flush()
        ffmpeg_proc.stdin.close()
        ffmpeg_proc.stdin = None
        ff_err = ffmpeg_proc.stderr.read()
        ret = ffmpeg_proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg failed: {ff_err.decode()[-400:]}")

        print(f"[RENDER SUCCESS] Master 60fps MP4 written -> {out_mp4}")
    finally:
        chrome_proc.terminate()
        chrome_proc.wait()

if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "/workspace/studios/story-shorts-v1/projects/casino-trap-01"
    asyncio.run(render_frames_via_cdp(
        os.path.join(proj, "stage.html"),
        os.path.join(proj, "beat_clock.json"),
        os.path.join(proj, "master_60fps.mp4")
    ))
