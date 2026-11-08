#!/usr/bin/env python3
"""
Phase 3: CODE-HIGGSFIELD Zero-API-Key MCP Server & Studio HTTP/SSE Bridge
Supports:
  1. MCP JSON-RPC 2.0 over stdio:   python3 mcp_server.py --stdio
  2. Direct Tool CLI Invocation:    python3 mcp_server.py --call <tool_name> --args '<json>'
  3. Studio HTTP API + SSE Bridge:  python3 mcp_server.py --http --port 8765

Exposes all 8 deterministic Higgsfield Studio MCP Tools:
  1. higgsfield_compile_brief
  2. higgsfield_decompile_reference
  3. higgsfield_submit_scene_code
  4. higgsfield_render_preview_or_master
  5. higgsfield_patch_layer_or_shot
  6. higgsfield_run_qa_gate
  7. higgsfield_manage_brandkit_and_cast
  8. higgsfield_poll_studio_queue
"""

from __future__ import annotations

import argparse
import asyncio
import http.server
import json
import mimetypes
import os
import socketserver
import sys
import time
import traceback
import urllib.parse
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = STUDIO_ROOT / "backend"
JOBS_DIR = STUDIO_ROOT / "jobs"
FRONTEND_DIR = STUDIO_ROOT / "frontend"

for sub in ["compiler", "engine/tools", "audio", "renderer", "patcher", "qa", "vault"]:
    sys.path.insert(0, str(BACKEND_DIR / sub))

from brief_to_spec_compiler import compile_brief_to_job  # type: ignore
from validate_motion_script import validate_script  # type: ignore
from narration_engine import build_job_audio_pipeline  # type: ignore
from scene_scaffold_generator import generate_3file_scene_graph  # type: ignore
from parallel_renderer import execute_render_pipeline  # type: ignore
from patch_engine import apply_surgical_patch  # type: ignore
from katana_decompiler import decompile_reference_video  # type: ignore
from qa_gate import run_qa_gate  # type: ignore
from brandkit_and_cast_vault import ensure_default_vault, list_vault, upsert_vault_item  # type: ignore


MCP_TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "name": "higgsfield_compile_brief",
        "description": "Compile a Studio UI brief into a locked job_spec.json, script.json, script.lock, beatmap.json, master_mix.wav, and 3-file scene graph (story.mjs + film.mjs + render_job.mjs).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Creative brief or prompt"},
                "studio_mode": {"type": "string", "enum": ["vibe_motion", "cinema_shorts", "katana_remix", "miracle_layer"], "default": "vibe_motion"},
                "aspect_ratio": {"type": "string", "enum": ["9:16", "16:9", "1:1", "4:5"], "default": "9:16"},
                "duration_sec": {"type": "number", "default": 10.0},
                "fps": {"type": "integer", "default": 60},
                "palette_id": {"type": "string", "default": "higgsfield_obsidian_lime"},
                "camera_preset": {"type": "string", "default": "dynamic_cinema"},
                "stiffness": {"type": "number", "default": 210.0},
                "damping": {"type": "number", "default": 18.0},
                "brandkit_id": {"type": "string"},
                "cast_ids": {"type": "array", "items": {"type": "string"}},
                "katana_blueprint": {"type": "object"},
                "job_id": {"type": "string"},
                "use_cloud_tts": {"type": "boolean", "default": False},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "higgsfield_decompile_reference",
        "description": "Katana Mode: Decompile any reference .mp4 or .gif into katana_blueprint.json with exact cut timestamps, optical motion vectors, palette, and audio beatmap.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video_path": {"type": "string", "description": "Path to reference video file"},
                "out_json": {"type": "string", "description": "Optional output JSON path"},
            },
            "required": ["video_path"],
        },
    },
    {
        "name": "higgsfield_submit_scene_code",
        "description": "Validate and save custom or Coding-Agent-authored story.mjs and/or film.mjs modules into jobs/<job_id>/shots/.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "story_mjs_code": {"type": "string"},
                "film_mjs_code": {"type": "string"},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "higgsfield_render_preview_or_master",
        "description": "Execute parallel headless Chromium renderer + linear glow.py post-pass + FFmpeg 60fps muxing in 'preview' (5 keyframes) or 'master' (full 60fps MP4) mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "mode": {"type": "string", "enum": ["preview", "master"], "default": "master"},
                "frames": {"type": "string", "description": "Optional frame range e.g. 0-119"},
                "shot_id": {"type": "string", "description": "Optional shot ID e.g. S2"},
                "layer_id": {"type": "string", "description": "Optional isolated layer ID"},
                "workers": {"type": "integer", "default": 4},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "higgsfield_patch_layer_or_shot",
        "description": "Miracle / Vibe Motion Surgical Edit: Modify a single layer (L0_Backdrop..L5_PostFX) or shot (S1..S5), re-render ONLY those frames, and splice into master_60fps.mp4 via assemble_partial_edit.sh.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "shot_id": {"type": "string", "description": "Target shot ID e.g. S2"},
                "layer_id": {"type": "string", "description": "Target layer ID e.g. L2_HeroSubject"},
                "layer_updates": {"type": "object", "description": "Key-value overrides for the target layer"},
                "shot_updates": {"type": "object", "description": "Key-value overrides for the shot"},
                "instruction": {"type": "string", "description": "Natural language surgical edit instruction"},
            },
            "required": ["job_id", "shot_id"],
        },
    },
    {
        "name": "higgsfield_run_qa_gate",
        "description": "Run the 2-Stage Machine + Visual QA Protocol (ffprobe, freezedetect, blackdetect, scdet, ebur128 loudness, WCAG contrast, and contact_sheet.png generation).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "higgsfield_manage_brandkit_and_cast",
        "description": "List or upsert persistent BrandKit DNA tokens and SoulID Character/UI Component Rigs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "upsert_brandkit", "upsert_cast"], "default": "list"},
                "item": {"type": "object"},
            },
        },
    },
    {
        "name": "higgsfield_poll_studio_queue",
        "description": "List all jobs in the Studio Queue with their current status, locks, QA telemetry, and code paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {"type": "string"},
            },
        },
    },
]


def dispatch_mcp_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Execute one of the 8 deterministic MCP tools and return a structured JSON result."""
    ensure_default_vault()
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    if name == "higgsfield_compile_brief":
        spec = compile_brief_to_job(
            prompt=str(args.get("prompt", "Navigating the digital landscape for growth with clean editorial design and real results")),
            studio_mode=str(args.get("studio_mode", "vibe_motion")),
            aspect_ratio=str(args.get("aspect_ratio", "9:16")),
            duration_sec=float(args.get("duration_sec", 10.0)),
            fps=int(args.get("fps", 60)),
            palette_id=str(args.get("palette_id", "wizardz_editorial_light")),
            camera_preset=str(args.get("camera_preset", "dynamic_cinema")),
            stiffness=float(args.get("stiffness", 220.0)),
            damping=float(args.get("damping", 18.0)),
            brandkit_id=args.get("brandkit_id"),
            cast_ids=args.get("cast_ids"),
            katana_blueprint=args.get("katana_blueprint"),
            job_id=args.get("job_id"),
            custom_shots=args.get("custom_shots"),
        )
        job_dir = Path(spec["job_dir"])
        audio_info = build_job_audio_pipeline(job_dir, use_cloud_tts=bool(args.get("use_cloud_tts", True)))
        scene_files = generate_3file_scene_graph(job_dir)
        return {
            "tool": name,
            "status": "COMPILED_AND_SCAFFOLDED",
            "job_id": spec["job_id"],
            "job_spec": spec,
            "audio_pipeline": audio_info,
            "scene_graph_files": scene_files,
        }

    if name == "higgsfield_decompile_reference":
        v_path = Path(str(args["video_path"]))
        out_p = Path(str(args["out_json"])) if args.get("out_json") else (v_path.parent / "katana_blueprint.json")
        bp = decompile_reference_video(v_path, out_json=out_p)
        return {"tool": name, "status": "DECOMPILED", "blueprint_path": str(out_p), "blueprint": bp}

    if name == "higgsfield_submit_scene_code":
        job_id = str(args["job_id"])
        job_dir = JOBS_DIR / job_id
        if not job_dir.exists():
            raise FileNotFoundError(f"Job '{job_id}' not found")
        shots_dir = job_dir / "shots"
        shots_dir.mkdir(parents=True, exist_ok=True)

        updated_files: list[str] = []
        if args.get("story_mjs_code"):
            code = str(args["story_mjs_code"])
            if "evaluateStoryLayers" not in code:
                raise ValueError("story.mjs must export function evaluateStoryLayers(shotSpec, tGlobal, tLocal)")
            p = shots_dir / "story.mjs"
            p.write_text(code, encoding="utf-8")
            updated_files.append(str(p))

        if args.get("film_mjs_code"):
            code = str(args["film_mjs_code"])
            if "sceneFor" not in code:
                raise ValueError("film.mjs must export stateless function sceneFor(frameIndex, opts)")
            p = shots_dir / "film.mjs"
            p.write_text(code, encoding="utf-8")
            updated_files.append(str(p))

        return {"tool": name, "status": "SCENE_CODE_ACCEPTED", "job_id": job_id, "updated_files": updated_files}

    if name == "higgsfield_render_preview_or_master":
        job_id = str(args["job_id"])
        job_dir = JOBS_DIR / job_id
        if not job_dir.exists():
            raise FileNotFoundError(f"Job '{job_id}' not found")
        res = asyncio.run(
            execute_render_pipeline(
                job_dir=job_dir,
                mode=str(args.get("mode", "master")),
                frames_spec=args.get("frames"),
                shot_id=args.get("shot_id"),
                active_layer=args.get("layer_id"),
                workers=int(args.get("workers", 4)),
            )
        )
        return {"tool": name, **res}

    if name == "higgsfield_patch_layer_or_shot":
        job_id = str(args["job_id"])
        job_dir = JOBS_DIR / job_id
        if not job_dir.exists():
            raise FileNotFoundError(f"Job '{job_id}' not found")
        res = apply_surgical_patch(
            job_dir=job_dir,
            shot_id=str(args["shot_id"]),
            layer_id=args.get("layer_id", "L2_HeroSubject"),
            layer_updates=args.get("layer_updates"),
            shot_updates=args.get("shot_updates"),
            instruction=args.get("instruction"),
        )
        return {"tool": name, **res}

    if name == "higgsfield_run_qa_gate":
        job_id = str(args["job_id"])
        job_dir = JOBS_DIR / job_id
        if not job_dir.exists():
            raise FileNotFoundError(f"Job '{job_id}' not found")
        rep = run_qa_gate(job_dir)
        return {"tool": name, **rep}

    if name == "higgsfield_manage_brandkit_and_cast":
        action = str(args.get("action", "list"))
        if action == "list":
            return {"tool": name, **list_vault()}
        if action == "upsert_brandkit":
            return {"tool": name, **upsert_vault_item("brandkit", dict(args.get("item") or {}))}
        if action == "upsert_cast":
            return {"tool": name, **upsert_vault_item("cast", dict(args.get("item") or {}))}
        raise ValueError(f"Unknown vault action: {action}")

    if name == "higgsfield_poll_studio_queue":
        status_filter = args.get("status_filter")
        jobs_list: list[dict[str, Any]] = []
        for j_dir in sorted(JOBS_DIR.iterdir(), reverse=True):
            if not j_dir.is_dir():
                continue
            spec_p = j_dir / "job_spec.json"
            if not spec_p.exists():
                continue
            spec = json.loads(spec_p.read_text(encoding="utf-8"))
            if status_filter and spec.get("status") != status_filter:
                continue
            qa_p = j_dir / "qa" / "qa_report.json"
            if qa_p.exists():
                spec["qa_report"] = json.loads(qa_p.read_text(encoding="utf-8"))
            bm_p = j_dir / "audio" / "beatmap.json"
            if bm_p.exists():
                bm = json.loads(bm_p.read_text(encoding="utf-8"))
                spec["beatmap_summary"] = {"bpm": bm.get("bpm"), "drop": bm.get("drop"), "downbeats": bm.get("downbeats", [])}
            sc_p = j_dir / "script.json"
            if sc_p.exists():
                spec["script"] = json.loads(sc_p.read_text(encoding="utf-8"))
            jobs_list.append(spec)
        return {"tool": name, "count": len(jobs_list), "jobs": jobs_list}

    raise ValueError(f"Unknown MCP tool: {name}")


# ---------------- 1. Standard MCP JSON-RPC 2.0 over stdio ---------------- #

def run_stdio_mcp_loop() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "serverInfo": {"name": "code-higgsfield-mcp", "version": "2.0.0"},
                    "capabilities": {"tools": {"listChanged": False}},
                },
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS_SCHEMA}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            t_name = params.get("name", "")
            t_args = params.get("arguments") or {}
            try:
                out = dispatch_mcp_tool(t_name, t_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
                        "isError": False,
                    },
                }
            except Exception as exc:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps({"error": str(exc), "trace": traceback.format_exc()})}],
                        "isError": True,
                    },
                }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        elif req_id is not None:
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


# ---------------- 2. Studio HTTP REST + SSE + Static UI Server ---------------- #

class StudioHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True


class StudioHTTPHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path

        if route == "/api/mcp/tools":
            return self._send_json(200, {"server": "code-higgsfield-mcp", "version": "2.0.0", "tools": MCP_TOOLS_SCHEMA})

        if route == "/api/studio/state":
            queue_data = dispatch_mcp_tool("higgsfield_poll_studio_queue", {})
            vault_data = dispatch_mcp_tool("higgsfield_manage_brandkit_and_cast", {"action": "list"})
            return self._send_json(
                200,
                {
                    "mcp_status": "CONNECTED // ZERO-KEY LOCAL AGENT",
                    "tools_count": len(MCP_TOOLS_SCHEMA),
                    "jobs": queue_data["jobs"],
                    "vault": vault_data,
                },
            )

        if route.startswith("/api/jobs/") and route.endswith("/code"):
            parts = route.strip("/").split("/")
            job_id = parts[2]
            job_dir = JOBS_DIR / job_id
            if not job_dir.exists():
                return self._send_json(404, {"error": "Job not found"})
            story_p = job_dir / "shots" / "story.mjs"
            film_p = job_dir / "shots" / "film.mjs"
            script_p = job_dir / "script.json"
            return self._send_json(
                200,
                {
                    "job_id": job_id,
                    "story_mjs": story_p.read_text(encoding="utf-8") if story_p.exists() else "",
                    "film_mjs": film_p.read_text(encoding="utf-8") if film_p.exists() else "",
                    "script_json": json.loads(script_p.read_text(encoding="utf-8")) if script_p.exists() else {},
                },
            )

        # Serve static files from /jobs/, /backend/, /assets/, or /frontend/public/
        if route.startswith(("/jobs/", "/backend/", "/assets/")):
            file_path = (STUDIO_ROOT / route.lstrip("/")).resolve()
            if not str(file_path).startswith(str(STUDIO_ROOT.resolve())) or not file_path.is_file():
                self.send_error(404, "File not found")
                return
            return self._serve_file(file_path)

        # Default to Frontend Studio UI
        rel = "index.html" if route in ("/", "") else route.lstrip("/")
        ui_file = (FRONTEND_DIR / rel).resolve()
        if not ui_file.is_file():
            ui_file = (FRONTEND_DIR / "index.html").resolve()
        if ui_file.is_file():
            return self._serve_file(ui_file)

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body) if raw_body else {}
        except Exception as exc:
            return self._send_json(400, {"error": f"Invalid JSON: {exc}"})

        if route == "/api/mcp/call":
            tool_name = str(body.get("name", ""))
            tool_args = dict(body.get("arguments") or {})
            try:
                res = dispatch_mcp_tool(tool_name, tool_args)
                return self._send_json(200, {"ok": True, "result": res})
            except Exception as exc:
                return self._send_json(500, {"ok": False, "error": str(exc), "trace": traceback.format_exc()})

        if route == "/api/studio/full-generate":
            # Full 1-click Studio Pipeline: Compile Brief + Audio/Beatmap + Scene Graph + Render + QA Gate
            try:
                comp = dispatch_mcp_tool("higgsfield_compile_brief", body)
                job_id = comp["job_id"]
                mode = str(body.get("render_mode", "master"))
                rend = dispatch_mcp_tool("higgsfield_render_preview_or_master", {"job_id": job_id, "mode": mode})
                qa = dispatch_mcp_tool("higgsfield_run_qa_gate", {"job_id": job_id}) if mode == "master" else None
                return self._send_json(
                    200,
                    {
                        "ok": True,
                        "job_id": job_id,
                        "compile": comp,
                        "render": rend,
                        "qa": qa,
                    },
                )
            except Exception as exc:
                return self._send_json(500, {"ok": False, "error": str(exc), "trace": traceback.format_exc()})

        self._send_json(404, {"error": f"Unknown endpoint {route}"})

    def _serve_file(self, file_path: Path) -> None:
        ctype, _ = mimetypes.guess_type(str(file_path))
        if file_path.suffix == ".mjs":
            ctype = "text/javascript; charset=utf-8"
        elif not ctype:
            ctype = "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Code-Higgsfield Zero-Key MCP Server & HTTP Bridge")
    parser.add_argument("--stdio", action="store_true", help="Run JSON-RPC 2.0 MCP server over stdio")
    parser.add_argument("--http", action="store_true", help="Run Studio HTTP + MCP Bridge server")
    parser.add_argument("--port", type=int, default=8765, help="HTTP port (default: 8765)")
    parser.add_argument("--call", default=None, help="Directly invoke an MCP tool by name")
    parser.add_argument("--args", default="{}", help="JSON arguments for --call")
    args = parser.parse_args()

    ensure_default_vault()

    if args.call:
        tool_args = json.loads(args.args)
        out = dispatch_mcp_tool(args.call, tool_args)
        print(json.dumps(out, indent=2))
        return 0

    if args.http:
        server = StudioHTTPServer(("0.0.0.0", args.port), StudioHTTPHandler)
        print(f"[code-higgsfield-mcp] Studio HTTP & MCP Bridge listening on http://0.0.0.0:{args.port} (Local: http://127.0.0.1:{args.port})", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0

    # Default to MCP stdio server
    run_stdio_mcp_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
