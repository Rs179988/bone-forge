#!/usr/bin/env python3
"""
Layer 4B: Parallel Headless Chromium 60FPS Frame Renderer & Linear-Light Post-Processor
Executes jobs/<job_id>/shots/{story.mjs, film.mjs, stage.html} across parallel Chrome CDP workers.
Supports:
  - Full 60fps master MP4 rendering (--mode master)
  - Instant 5-keyframe preview strip + linear glow.py pass (--mode preview)
  - Surgical frame-range or single-shot re-rendering (--frames start-end | --shot S2 | --layer L2_HeroSubject)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import functools
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import glob
try:
    import websockets
except ImportError:
    websockets = None  # type: ignore

STUDIO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_TOOLS_DIR = STUDIO_ROOT / "backend" / "engine" / "tools"
RENDERER_DIR = STUDIO_ROOT / "backend" / "renderer"
for _p in (ENGINE_TOOLS_DIR, RENDERER_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from glow import apply_linear_glow_and_halation  # type: ignore
from textures import read_png_rgb8, write_png_rgb8  # type: ignore
from native_canvas_renderer import (  # type: ignore
    capture_keyframes_native_fallback,
    render_chunk_native_fallback,
)


def find_chrome_binary() -> str | None:
    if os.environ.get("FORCE_NATIVE_RENDERER") == "1" or websockets is None:
        return None
    pw_candidates = sorted(
        glob.glob(os.path.expanduser("~/.cache/ms-playwright/*/chrome-linux/chrome"))
        + glob.glob("/root/.cache/ms-playwright/*/chrome-linux/chrome"),
        reverse=True,
    )
    candidates = [
        os.environ.get("CHROME_BIN"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/usr/local/lib/chrome-headless-shell/chrome-headless-shell",
        *pw_candidates,
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for cand in candidates:
        if not cand or not os.path.exists(cand):
            continue
        try:
            proc = subprocess.run(
                [cand, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=3,
                text=True,
            )
            out_combined = (proc.stdout + proc.stderr).lower()
            if proc.returncode == 0 and "snap" not in out_combined and "requires the chromium snap" not in out_combined:
                return cand
        except Exception:
            continue
    return None


class QuietStaticServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


def start_local_studio_http_server(root_dir: Path) -> tuple[QuietStaticServer, int]:
    handler = functools.partial(QuietHandler, directory=str(root_dir))
    server = QuietStaticServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


async def render_worker_chunk(
    worker_id: int,
    start_f: int,
    end_f: int,
    stage_url: str,
    width: int,
    height: int,
    fps: int,
    out_ts_path: Path,
    active_layer: str | None = None,
) -> dict[str, Any]:
    """Render frames [start_f, end_f) in a dedicated headless Chrome instance and pipe to FFmpeg."""
    cdp_port = 9340 + (worker_id * 7) + (int(time.time() * 10) % 5)
    user_dir = Path(f"/tmp/hf_chrome_w{worker_id}_{int(time.time() * 1000)}")
    user_dir.mkdir(parents=True, exist_ok=True)

    chrome_cmd = [
        find_chrome_binary(),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--user-data-dir={user_dir}",
        f"--remote-debugging-port={cdp_port}",
        stage_url,
    ]
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws_url = None
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json", timeout=1.0) as resp:
                    targets = json.loads(resp.read().decode("utf-8"))
                    for t in targets:
                        if t.get("type") == "page":
                            ws_url = t.get("webSocketDebuggerUrl")
                            break
                if ws_url:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.1)

        if not ws_url:
            raise RuntimeError(f"Worker {worker_id} could not connect to Chrome CDP on port {cdp_port}")

        # Pipe JPEG frames into FFmpeg with linear-light bloom/contrast eq & unsharp filter
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "image2pipe",
            "-vcodec",
            "mjpeg",
            "-r",
            str(fps),
            "-i",
            "-",
            "-vf",
            "eq=contrast=1.04:saturation=1.06,unsharp=3:3:0.35:3:3:0.0",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            str(out_ts_path),
        ]
        ffmpeg_proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        async with websockets.connect(ws_url, max_size=120 * 1024 * 1024) as ws:
            msg_id = 1

            async def cdp_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
                nonlocal msg_id
                curr = msg_id
                msg_id += 1
                await ws.send(json.dumps({"id": curr, "method": method, "params": params or {}}))
                while True:
                    raw = await ws.recv()
                    data = json.loads(raw)
                    if data.get("id") == curr:
                        if "error" in data:
                            raise RuntimeError(f"CDP error: {data['error']}")
                        return data.get("result", {})

            await cdp_call("Runtime.enable")

            # Wait for ES module stage.html to finish loading film.mjs & story.mjs
            for _ in range(50):
                ready_res = await cdp_call(
                    "Runtime.evaluate",
                    {"expression": "Boolean(window.__STAGE_READY)", "returnByValue": True},
                )
                if ready_res.get("result", {}).get("value") is True:
                    break
                await asyncio.sleep(0.08)

            layer_arg = json.dumps(active_layer)
            await cdp_call(
                "Runtime.evaluate",
                {
                    "expression": f"""
                    window.__renderBatchB64 = function(fStart, fEnd) {{
                        const c = document.getElementById('stage');
                        const out = [];
                        for (let f = fStart; f < fEnd; f++) {{
                            window.__renderFrame(f, {layer_arg});
                            const d = c.toDataURL('image/jpeg', 0.95);
                            out.push(d.substring(23));
                        }}
                        return out;
                    }};
                    """,
                    "returnByValue": True,
                },
            )

            t0 = time.time()
            batch_size = 15
            for b_start in range(start_f, end_f, batch_size):
                b_end = min(end_f, b_start + batch_size)
                res = await cdp_call(
                    "Runtime.evaluate",
                    {
                        "expression": f"window.__renderBatchB64({b_start}, {b_end});",
                        "returnByValue": True,
                    },
                )
                b64_list = res.get("result", {}).get("value", [])
                for b64_str in b64_list:
                    if ffmpeg_proc.stdin:
                        ffmpeg_proc.stdin.write(base64.b64decode(b64_str))

            if ffmpeg_proc.stdin:
                ffmpeg_proc.stdin.close()
            ffmpeg_proc.wait(timeout=60)
            if ffmpeg_proc.returncode != 0:
                err_txt = ffmpeg_proc.stderr.read().decode(errors="replace") if ffmpeg_proc.stderr else ""
                raise RuntimeError(f"Worker {worker_id} FFmpeg failed: {err_txt}")

            return {
                "worker_id": worker_id,
                "start_frame": start_f,
                "end_frame": end_f,
                "frames_rendered": end_f - start_f,
                "wall_sec": round(time.time() - t0, 2),
                "chunk_path": str(out_ts_path),
            }
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()
        shutil.rmtree(user_dir, ignore_errors=True)


async def capture_single_png_frames(
    frame_indices: list[int],
    stage_url: str,
    width: int,
    height: int,
    out_dir: Path,
    active_layer: str | None = None,
    apply_glow: bool = True,
) -> list[str]:
    """Capture exact lossless PNG frames for preview strip / styleframes and run glow.py linear bloom."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cdp_port = 9390 + (int(time.time() * 10) % 9)
    user_dir = Path(f"/tmp/hf_chrome_preview_{int(time.time() * 1000)}")
    user_dir.mkdir(parents=True, exist_ok=True)

    chrome_cmd = [
        find_chrome_binary(),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--user-data-dir={user_dir}",
        f"--remote-debugging-port={cdp_port}",
        stage_url,
    ]
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    written_paths: list[str] = []

    try:
        ws_url = None
        for _ in range(50):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json", timeout=1.0) as resp:
                    targets = json.loads(resp.read().decode("utf-8"))
                    for t in targets:
                        if t.get("type") == "page":
                            ws_url = t.get("webSocketDebuggerUrl")
                            break
                if ws_url:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.1)

        if not ws_url:
            raise RuntimeError("Preview worker failed to connect to Chrome CDP")

        async with websockets.connect(ws_url, max_size=120 * 1024 * 1024) as ws:
            msg_id = 1

            async def cdp_call(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
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
            for _ in range(50):
                ready_res = await cdp_call(
                    "Runtime.evaluate",
                    {"expression": "Boolean(window.__STAGE_READY)", "returnByValue": True},
                )
                if ready_res.get("result", {}).get("value") is True:
                    break
                await asyncio.sleep(0.08)

            layer_arg = json.dumps(active_layer)
            for f_idx in frame_indices:
                res = await cdp_call(
                    "Runtime.evaluate",
                    {
                        "expression": f"""
                        (() => {{
                            window.__renderFrame({f_idx}, {layer_arg});
                            return document.getElementById('stage').toDataURL('image/png').substring(22);
                        }})()
                        """,
                        "returnByValue": True,
                    },
                )
                b64_png = res.get("result", {}).get("value", "")
                raw_png_path = out_dir / f"f_{f_idx:04d}.png"
                raw_png_path.write_bytes(base64.b64decode(b64_png))

                if apply_glow:
                    arr = read_png_rgb8(raw_png_path)
                    graded = apply_linear_glow_and_halation(arr, seed=1000 + f_idx)
                    write_png_rgb8(raw_png_path, graded)

                written_paths.append(str(raw_png_path))
        return written_paths
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()
        shutil.rmtree(user_dir, ignore_errors=True)


async def execute_render_pipeline(
    job_dir: Path,
    mode: str = "master",
    frames_spec: str | None = None,
    shot_id: str | None = None,
    active_layer: str | None = None,
    workers: int = 4,
    out_mp4: Path | None = None,
) -> dict[str, Any]:
    script = json.loads((job_dir / "script.json").read_text(encoding="utf-8"))
    fps = int(script.get("fps", 60))
    total_frames = int(script.get("total_frames", 600))
    width = int(script.get("width", 1080))
    height = int(script.get("height", 1920))

    server, port = start_local_studio_http_server(STUDIO_ROOT)
    rel_stage = (job_dir / "shots" / "stage.html").relative_to(STUDIO_ROOT)
    stage_url = f"http://127.0.0.1:{port}/{rel_stage}"

    t_start = time.time()
    try:
        # Resolve frame range if --shot or --frames was passed
        start_f = 0
        end_f = total_frames
        if shot_id:
            target_shot = next((s for s in script.get("shots", []) if s.get("id") == shot_id), None)
            if not target_shot:
                raise ValueError(f"Shot '{shot_id}' not found in script.json")
            start_f = int(target_shot.get("in_frame", round(float(target_shot["in_sec"]) * fps)))
            end_f = int(target_shot.get("out_frame", round(float(target_shot["out_sec"]) * fps)))
        elif frames_spec:
            if "-" in frames_spec:
                a_s, b_s = frames_spec.split("-", 1)
                start_f = max(0, int(a_s))
                end_f = min(total_frames, int(b_s) + 1)
            else:
                start_f = int(frames_spec)
                end_f = start_f + 1

        # Preview mode: render 1 keyframe per shot (plus glow.py pass)
        preview_dir = job_dir / "preview"
        keyframes = [
            min(
                total_frames - 1,
                int(round(((float(s["in_sec"]) + float(s["out_sec"])) * 0.5) * fps)),
            )
            for s in script.get("shots", [])
        ]

        chrome_bin = find_chrome_binary()
        use_native_fallback = chrome_bin is None
        if not use_native_fallback:
            try:
                preview_pngs = await capture_single_png_frames(
                    keyframes,
                    stage_url,
                    width,
                    height,
                    preview_dir,
                    active_layer=active_layer,
                    apply_glow=True,
                )
            except Exception:
                use_native_fallback = True
                preview_pngs = capture_keyframes_native_fallback(
                    keyframes,
                    script,
                    width,
                    height,
                    preview_dir,
                    active_layer=active_layer,
                )
        else:
            preview_pngs = capture_keyframes_native_fallback(
                keyframes,
                script,
                width,
                height,
                preview_dir,
                active_layer=active_layer,
            )

        if mode == "preview":
            return {
                "status": "PREVIEW_COMPLETED",
                "job_id": script.get("job_id"),
                "keyframes": keyframes,
                "preview_pngs": preview_pngs,
                "renderer_engine": "native_numpy_60fps" if use_native_fallback else "chrome_cdp_60fps",
                "wall_sec": round(time.time() - t_start, 2),
            }

        # Master or Range video render across parallel workers
        chunks_dir = job_dir / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)
        total_to_render = max(1, end_f - start_f)
        actual_workers = min(workers, max(1, total_to_render // 30))
        chunk_size = (total_to_render + actual_workers - 1) // actual_workers

        chunk_files: list[Path] = []
        chunk_specs: list[tuple[int, int, int, Path]] = []
        for w_idx in range(actual_workers):
            c_start = start_f + w_idx * chunk_size
            c_end = min(end_f, c_start + chunk_size)
            if c_start >= c_end:
                continue
            c_path = chunks_dir / f"chunk_{c_start:04d}_{c_end:04d}.ts"
            chunk_files.append(c_path)
            chunk_specs.append((w_idx, c_start, c_end, c_path))

        if not use_native_fallback:
            try:
                tasks = [
                    render_worker_chunk(
                        w_idx,
                        c_start,
                        c_end,
                        stage_url,
                        width,
                        height,
                        fps,
                        c_path,
                        active_layer=active_layer,
                    )
                    for (w_idx, c_start, c_end, c_path) in chunk_specs
                ]
                worker_stats = await asyncio.gather(*tasks)
            except Exception:
                use_native_fallback = True

        if use_native_fallback:
            loop = asyncio.get_running_loop()
            native_tasks = [
                loop.run_in_executor(
                    None,
                    render_chunk_native_fallback,
                    w_idx,
                    c_start,
                    c_end,
                    script,
                    width,
                    height,
                    fps,
                    c_path,
                    active_layer,
                )
                for (w_idx, c_start, c_end, c_path) in chunk_specs
            ]
            worker_stats = list(await asyncio.gather(*native_tasks))

        concat_list = chunks_dir / "concat.txt"
        concat_list.write_text("\n".join(f"file '{p.resolve()}'" for p in chunk_files) + "\n", encoding="utf-8")

        final_mp4 = out_mp4 or (job_dir / "master_60fps.mp4" if (start_f == 0 and end_f == total_frames) else job_dir / f"patch_{start_f}_{end_f}.mp4")
        master_audio = job_dir / "audio" / "master_mix.wav"

        if master_audio.exists() and start_f == 0 and end_f == total_frames:
            mux_cmd = [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-i",
                str(master_audio),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "17",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(final_mp4),
            ]
        elif master_audio.exists():
            # Slice matching audio window for partial range render
            in_s = start_f / fps
            dur_s = (end_f - start_f) / fps
            mux_cmd = [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-ss",
                f"{in_s:.4f}",
                "-t",
                f"{dur_s:.4f}",
                "-i",
                str(master_audio),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "17",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                str(final_mp4),
            ]
        else:
            mux_cmd = [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "17",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(fps),
                str(final_mp4),
            ]

        subprocess.run(mux_cmd, check=True)

        # Update job_spec.json status
        spec_path = job_dir / "job_spec.json"
        if spec_path.exists() and final_mp4.name == "master_60fps.mp4":
            spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
            spec_data["status"] = "RENDERED"
            spec_data["last_render_sec"] = round(time.time() - t_start, 2)
            spec_path.write_text(json.dumps(spec_data, indent=2) + "\n", encoding="utf-8")

        return {
            "status": "RENDER_COMPLETED",
            "job_id": script.get("job_id"),
            "output_mp4": str(final_mp4),
            "start_frame": start_f,
            "end_frame": end_f,
            "frames_rendered": end_f - start_f,
            "fps": fps,
            "preview_pngs": preview_pngs,
            "workers": worker_stats,
            "wall_sec": round(time.time() - t_start, 2),
        }
    finally:
        server.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description="Parallel 60FPS Headless Chrome Renderer for Code-Higgsfield")
    parser.add_argument("job_dir", type=Path)
    parser.add_argument("--mode", default="master", choices=["master", "preview"])
    parser.add_argument("--frames", default=None, help="Optional frame range e.g. 120-240")
    parser.add_argument("--shot", default=None, help="Optional shot ID e.g. S2")
    parser.add_argument("--layer", default=None, help="Optional isolated layer e.g. L2_HeroSubject")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        script = json.loads((args.job_dir / "script.json").read_text(encoding="utf-8"))
        print(json.dumps({"dry_run": True, "job_id": script.get("job_id"), "shots": len(script.get("shots", []))}, indent=2))
        return 0

    res = asyncio.run(
        execute_render_pipeline(
            job_dir=args.job_dir,
            mode=args.mode,
            frames_spec=args.frames,
            shot_id=args.shot,
            active_layer=args.layer,
            workers=args.workers,
            out_mp4=args.out,
        )
    )
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
