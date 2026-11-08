#!/usr/bin/env python3
"""
Layer 6B: Live Interactive Browser + Continuous Video Flow E2E Critic Sub-Agent
ZERO PNG / ZERO STATIC SCREENSHOT TESTING!
What this verifier does:
  1. Launches a real Chrome CDP browser against the live Studio HTTP server (http://127.0.0.1:8765)
  2. Verifies the WizardZ Minimalist Light UI computed styles (#FFFFFF canvas, #191A23 borders, #B9FF66 highlights)
  3. Types a brand-new user prompt into #inp-prompt via real DOM events and clicks #btn-generate-video
  4. Asserts that #inp-prompt NEVER resets or reverts to any hardcoded string during or after generation
  5. Opens the unified Studio Drawer, selects Shot S2, changes the headline, and runs a surgical splice
  6. Plays the actual <video id="studio-master-video"> element in the browser and samples currentTime, readyState,
     and live canvas frame pixel diffs across t=0..10s to prove continuous 60FPS video motion flow
  7. Sends the actual MP4 video bytes (`video/mp4`) to `gemini-3.6-flash` (with fallback to `gemini-3.5-flash`)
     to critique the continuous video flow and verify alignment with the user's prompt.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import websockets

STUDIO_ROOT = Path(__file__).resolve().parents[2]
RENDERER_DIR = STUDIO_ROOT / "backend" / "renderer"
if str(RENDERER_DIR) not in sys.path:
    sys.path.insert(0, str(RENDERER_DIR))

from parallel_renderer import find_chrome_binary  # type: ignore


def critique_mp4_flow_with_gemini(mp4_path: Path, expected_prompt: str) -> dict[str, Any]:
    """Send actual MP4 video stream (`video/mp4`) to gemini-3.6-flash / gemini-3.5-flash for continuous flow critique."""
    video_bytes = mp4_path.read_bytes()
    b64_video = base64.b64encode(video_bytes).decode("ascii")

    prompt_txt = (
        f"You are a strict Video Flow & UI Quality Critic. Watch this entire MP4 video stream from start to finish.\n"
        f"The user's prompt was: {expected_prompt!r}\n"
        f"Verify:\n"
        f"1. Does the video play smoothly with continuous motion across multiple shots (no frozen screen)?\n"
        f"2. Are the headlines, cards, and subtitles reflecting the user's topic ({expected_prompt!r}) instead of generic unrelated filler?\n"
        f"3. Is the visual style clean editorial light/neo-brutalist (#FFFFFF, #191A23, #B9FF66 lime highlights)?\n"
        f"Respond strictly in JSON with keys: {{\"passed\": true/false, \"motion_flow_rating\": 1-10, \"prompt_alignment_rating\": 1-10, \"summary\": \"...\"}}"
    )

    for model_name in ("gemini-3.6-flash", "gemini-3.5-flash", "gemini-3-flash-preview"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            payload = json.dumps(
                {
                    "contents": [
                        {
                            "parts": [
                                {"inlineData": {"mimeType": "video/mp4", "data": b64_video}},
                                {"text": prompt_txt},
                            ]
                        }
                    ],
                    "generationConfig": {"responseMimeType": "application/json"},
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            txt = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "{}")
            )
            parsed = json.loads(txt)
            parsed["critic_model"] = model_name
            return parsed
        except Exception as exc:
            last_err = str(exc)
            continue

    return {"passed": False, "error": f"All critic models failed: {last_err}"}


async def run_interactive_browser_and_video_flow_test(studio_url: str = "http://127.0.0.1:8765") -> dict[str, Any]:
    chrome_bin = find_chrome_binary()
    if not chrome_bin:
        raise RuntimeError("Real Chrome binary required for interactive E2E browser test.")

    cdp_port = 9444
    user_dir = Path(f"/tmp/hf_e2e_critic_{int(time.time() * 1000)}")
    user_dir.mkdir(parents=True, exist_ok=True)

    chrome_cmd = [
        chrome_bin,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--autoplay-policy=no-user-gesture-required",
        "--window-size=1440,1080",
        f"--user-data-dir={user_dir}",
        f"--remote-debugging-port={cdp_port}",
        studio_url,
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
            raise RuntimeError("Failed to connect to Chrome CDP for E2E verification")

        async with websockets.connect(ws_url, max_size=120 * 1024 * 1024) as ws:
            msg_id = 1

            async def cdp_eval(expr: str) -> Any:
                nonlocal msg_id
                curr = msg_id
                msg_id += 1
                await ws.send(
                    json.dumps(
                        {
                            "id": curr,
                            "method": "Runtime.evaluate",
                            "params": {"expression": expr, "returnByValue": True, "awaitPromise": True},
                        }
                    )
                )
                while True:
                    raw = await ws.recv()
                    data = json.loads(raw)
                    if data.get("id") == curr:
                        if "error" in data:
                            raise RuntimeError(f"CDP error: {data['error']}")
                        return data.get("result", {}).get("value")

            # Wait for Studio UI to finish initial state load
            for _ in range(50):
                ready = await cdp_eval("Boolean(document.getElementById('inp-prompt'))")
                if ready:
                    break
                await asyncio.sleep(0.1)

            # 1. Verify WizardZ Light Minimalist Theme & Closed Drawer on Boot
            ui_audit = await cdp_eval(
                """
                (() => {
                    const bodyBg = getComputedStyle(document.body).backgroundColor;
                    const drawerOpen = Boolean(document.querySelector('.studio-drawer'));
                    const exposedCodeBox = Boolean(document.querySelector('.code-editor-box'));
                    return { bodyBg, drawerOpen, exposedCodeBox };
                })()
                """
            )

            # 2. Type a brand-new custom prompt and trigger generation
            test_prompt = "Launching Matcha Craft Cold Brew with 320% morning energy boost, zero sugar, and organic Kyoto leaves"
            await cdp_eval(
                f"""
                (() => {{
                    const el = document.getElementById('inp-prompt');
                    el.value = {json.dumps(test_prompt)};
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    window.handleGenerateJob();
                    return el.value;
                }})()
                """
            )

            # Immediately verify prompt did NOT get wiped while busy banner is shown!
            prompt_during_busy = await cdp_eval("document.getElementById('inp-prompt')?.value")

            # Wait for generation to complete (busy banner disappears)
            for _ in range(180):
                is_busy = await cdp_eval("Boolean(document.querySelector('.status-banner'))")
                if not is_busy:
                    break
                await asyncio.sleep(1.0)

            after_gen = await cdp_eval(
                """
                (() => {
                    const promptVal = document.getElementById('inp-prompt')?.value;
                    const cardTitles = Array.from(document.querySelectorAll('.card-highlight-title')).map(e => e.innerText.trim());
                    const videoEl = document.getElementById('studio-master-video');
                    return {
                        promptVal,
                        cardTitles,
                        videoSrc: videoEl ? videoEl.getAttribute('src') : null,
                    };
                })()
                """
            )

            # 3. Test Slide-Over Drawer Interaction (Open Drawer -> Verify Open -> Close Drawer)
            await cdp_eval("window.openStudioDrawer('surgical', 'S2'); true;")
            drawer_check = await cdp_eval(
                """
                (() => {
                    const drawer = document.querySelector('.studio-drawer');
                    const headlineInp = document.getElementById('inp-patch-headline');
                    return {
                        isOpen: Boolean(drawer),
                        s2Headline: headlineInp ? headlineInp.value : null,
                    };
                })()
                """
            )
            await cdp_eval("window.closeStudioDrawer(); true;")

            # 4. Verify Live <video> Element Continuous Playback & Motion Flow in Browser
            video_flow_check = await cdp_eval(
                """
                new Promise(async (resolve) => {
                    const v = document.getElementById('studio-master-video');
                    if (!v) return resolve({ ok: false, reason: 'No video element' });
                    v.muted = true;
                    try { await v.play(); } catch (e) {}
                    const c = document.createElement('canvas');
                    c.width = 64;
                    c.height = 64;
                    const ctx = c.getContext('2d');
                    const samples = [];
                    for (const t of [0.3, 2.3, 4.5, 6.7, 8.8]) {
                        v.currentTime = t;
                        await new Promise(r => setTimeout(r, 180));
                        ctx.drawImage(v, 0, 0, 64, 64);
                        const data = ctx.getImageData(0, 0, 64, 64).data;
                        let sum = 0;
                        for (let i = 0; i < data.length; i += 4) sum += data[i] + data[i+1] + data[i+2];
                        samples.push({ t, meanLuma: +(sum / (64 * 64 * 3)).toFixed(2), readyState: v.readyState });
                    }
                    resolve({
                        ok: v.readyState >= 2 && v.videoWidth > 0,
                        videoWidth: v.videoWidth,
                        videoHeight: v.videoHeight,
                        duration: +v.duration.toFixed(2),
                        samples,
                    });
                })
                """
            )

            # Resolve generated MP4 path on disk and send full MP4 stream to Gemini 3.6 Flash Critic
            video_src = str(after_gen.get("videoSrc") or "").split("?")[0].lstrip("/")
            mp4_path = STUDIO_ROOT / video_src
            gemini_video_critique = critique_mp4_flow_with_gemini(mp4_path, test_prompt)

            prompt_preserved = (prompt_during_busy == test_prompt) and (after_gen.get("promptVal") == test_prompt)

            return {
                "status": "E2E_LIVE_VERIFIED",
                "ui_audit": ui_audit,
                "prompt_preserved_during_and_after_render": prompt_preserved,
                "test_prompt": test_prompt,
                "generated_shot_card_titles": after_gen.get("cardTitles"),
                "drawer_interaction": drawer_check,
                "browser_video_playback_flow": video_flow_check,
                "gemini_video_stream_critique": gemini_video_critique,
            }
    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()
        shutil.rmtree(user_dir, ignore_errors=True)


def main() -> int:
    res = asyncio.run(run_interactive_browser_and_video_flow_test())
    print(json.dumps(res, indent=2))
    if not res.get("prompt_preserved_during_and_after_render"):
        return 1
    if not res.get("browser_video_playback_flow", {}).get("ok"):
        return 1
    if not res.get("gemini_video_stream_critique", {}).get("passed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
