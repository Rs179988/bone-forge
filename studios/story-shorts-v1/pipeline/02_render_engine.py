#!/usr/bin/env python3
import os
import sys
import json
import time
import base64
import shutil
import asyncio
import subprocess
import urllib.request
import websockets

async def render_worker_chunk(worker_id, start_f, end_f, html_path, clock, studio_lock, fps, out_ts):
    port = 9230 + worker_id
    user_dir = f"/tmp/chrome_worker_{worker_id}_{int(time.time()*1000)}"
    os.makedirs(user_dir, exist_ok=True)

    chrome_cmd = [
        "/usr/bin/google-chrome",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--window-size=1080,1920",
        f"--user-data-dir={user_dir}",
        f"--remote-debugging-port={port}",
        f"file://{os.path.abspath(html_path)}"
    ]
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws_url = None
        for _ in range(50):
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
            await asyncio.sleep(0.12)

        if not ws_url:
            raise RuntimeError(f"Worker {worker_id}: Failed to connect to Chrome CDP on port {port}")

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "16",
            "-pix_fmt", "yuv420p",
            out_ts
        ]
        ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        async with websockets.connect(ws_url, max_size=100 * 1024 * 1024) as ws:
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

            await cdp_call("Runtime.enable")
            await asyncio.sleep(0.15)

            clock_json_str = json.dumps(clock)
            lock_json_str = json.dumps(studio_lock)
            await cdp_call("Runtime.evaluate", {
                "expression": f"""
                window.initClock({clock_json_str}, {lock_json_str});
                window.renderBatchB64 = function(fStart, fEnd) {{
                    const c = document.getElementById('stage');
                    const out = [];
                    for (let f = fStart; f < fEnd; f++) {{
                        window.seekToFrame(f);
                        const d = c.toDataURL('image/jpeg', 0.94);
                        out.push(d.substring(23));
                    }}
                    return out;
                }};
                true;
                """,
                "returnByValue": True
            })

            t0 = time.time()
            count = end_f - start_f
            batch_sz = 20
            for b_start in range(start_f, end_f, batch_sz):
                b_end = min(end_f, b_start + batch_sz)
                res = await cdp_call("Runtime.evaluate", {
                    "expression": f"window.renderBatchB64({b_start}, {b_end});",
                    "returnByValue": True
                })
                b64_list = res.get("result", {}).get("value", [])
                for b64_str in b64_list:
                    ffmpeg_proc.stdin.write(base64.b64decode(b64_str))

                done = b_end - start_f
                if done % 200 == 0 or b_end == end_f:
                    el = max(0.001, time.time() - t0)
                    print(f"  [WORKER {worker_id}] {done}/{count} frames (f:{b_end-1}) @ {done/el:.1f} fps", flush=True)

        ffmpeg_proc.stdin.flush()
        ffmpeg_proc.stdin.close()
        ffmpeg_proc.stdin = None
        ff_err = ffmpeg_proc.stderr.read()
        ret = ffmpeg_proc.wait()
        if ret != 0:
            raise RuntimeError(f"Worker {worker_id} FFmpeg failed: {ff_err.decode()[-300:]}")

    finally:
        chrome_proc.terminate()
        chrome_proc.wait()
        shutil.rmtree(user_dir, ignore_errors=True)

async def render_frames_via_cdp(html_path, clock_path, out_mp4):
    with open(clock_path, "r") as f:
        clock = json.load(f)

    studio_lock_path = os.path.abspath(os.path.join(os.path.dirname(clock_path), "../../studio_lock.json"))
    studio_lock = {}
    if os.path.exists(studio_lock_path):
        with open(studio_lock_path, "r") as f:
            studio_lock = json.load(f)

    total_frames = clock["total_frames"]
    fps = clock["fps"]
    audio_file = clock["audio_file"]

    num_workers = 5
    chunk_size = (total_frames + num_workers - 1) // num_workers
    chunk_files = []
    tasks = []

    t_start = time.time()
    print(f"[DIRECT CANVAS ENGINE] Launching {num_workers} parallel workers for {total_frames} frames...", flush=True)

    for w in range(num_workers):
        sf = w * chunk_size
        ef = min(total_frames, (w + 1) * chunk_size)
        if sf >= ef:
            break
        c_mp4 = f"/tmp/render_chunk_{w}.mp4"
        chunk_files.append(c_mp4)
        tasks.append(render_worker_chunk(w, sf, ef, html_path, clock, studio_lock, fps, c_mp4))

    await asyncio.gather(*tasks)

    concat_list = "/tmp/render_concat_list.txt"
    with open(concat_list, "w") as f:
        for cf in chunk_files:
            f.write(f"file '{cf}'\n")

    mux_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
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
    subprocess.run(mux_cmd, check=True)

    for cf in chunk_files:
        if os.path.exists(cf):
            os.remove(cf)
    if os.path.exists(concat_list):
        os.remove(concat_list)

    total_elapsed = time.time() - t_start
    print(f"[RENDER SUCCESS] {total_frames} frames rendered in {total_elapsed:.1f}s ({total_frames/total_elapsed:.1f} effective fps) -> {out_mp4}", flush=True)

if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "/workspace/studios/story-shorts-v1/projects/high-effort-flop-01"
    asyncio.run(render_frames_via_cdp(
        os.path.join(proj, "stage.html"),
        os.path.join(proj, "beat_clock.json"),
        os.path.join(proj, "master_60fps.mp4")
    ))
