#!/usr/bin/env python3
"""
Layer 4A: 3-File Stateless Scene Graph Scaffold Generator
Generates:
  - jobs/<job_id>/shots/story.mjs
  - jobs/<job_id>/shots/film.mjs
  - jobs/<job_id>/shots/render_job.mjs
  - jobs/<job_id>/shots/stage.html
following higgsfield-ai/higgsfield-video-engineer's exact 3-file pure-function architecture.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def generate_3file_scene_graph(job_dir: Path) -> dict[str, str]:
    script_path = job_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script.json in {job_dir}")

    script = json.loads(script_path.read_text(encoding="utf-8"))
    beatmap_path = job_dir / "audio" / "beatmap.json"
    beatmap = json.loads(beatmap_path.read_text(encoding="utf-8")) if beatmap_path.exists() else {"bpm": 120.0, "drop": 4.0, "energy_envelope": [0.3] * 200}

    shots_dir = job_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    fps = int(script.get("fps", 60))
    total_frames = int(script.get("total_frames", round(float(script.get("duration_sec", 10.0)) * fps)))
    width = int(script.get("width", 1080))
    height = int(script.get("height", 1920))

    shots_json_str = json.dumps(script.get("shots", []), indent=2)
    palette_json_str = json.dumps(script.get("palette", {}), indent=2)
    envelope_json_str = json.dumps(beatmap.get("energy_envelope", [0.3] * 100))

    # 1. story.mjs — Pure functions of film time t returning world & 6-layer state
    story_mjs_code = f"""// Auto-generated & Agent-Editable Story Timeline (story.mjs)
// Job ID: {script.get("job_id")} | Genre: {script.get("genre")}
// Pure functions of time t (seconds) using Higgsfield pre-built curve primitives.

import {{ clamp, lerp, smooth, easeIn, easeOut, easeInOut, backOut, ring, springDamper, keys, evaluateCurve }} from '/backend/engine/core/curves.mjs';

export const JOB_ID = {json.dumps(script.get("job_id"))};
export const PALETTE = {palette_json_str};
export const ENERGY_ENVELOPE = {envelope_json_str};
export const DROP_SEC = {float(beatmap.get("drop", 4.0))};

export const SHOT_SPECS = {shots_json_str};

/**
 * Audio energy lookup at film time t (seconds) for reactive character lip-sync & UI telemetry
 */
export function audioEnergyAt(t) {{
  if (!ENERGY_ENVELOPE.length) return 0.25;
  const idx = clamp(Math.floor(t * 20), 0, ENERGY_ENVELOPE.length - 1);
  return ENERGY_ENVELOPE[idx] || 0.22;
}}

/**
 * Compute dynamic 6-Layer state for shot at global time tGlobal and shot-local time tLocal
 */
export function evaluateStoryLayers(shotSpec, tGlobal, tLocal) {{
  const shotDur = Math.max(0.1, shotSpec.out_sec - shotSpec.in_sec);
  const u = clamp(tLocal / shotDur);
  const baseLayers = shotSpec.layers || {{}};
  const curveVal = evaluateCurve(
    shotSpec.primary_curve || 'backOut',
    u,
    tLocal,
    baseLayers.L2_HeroSubject?.stiffness || 210,
    baseLayers.L2_HeroSubject?.damping || 18
  );

  return {{
    L0_Backdrop: {{
      ...baseLayers.L0_Backdrop,
      accent_color: PALETTE.accent_primary,
      ray_intensity: (baseLayers.L0_Backdrop?.ray_intensity ?? 0.42) * (0.85 + 0.25 * Math.sin(tGlobal * 1.8)),
    }},
    L1_Environment: {{
      ...baseLayers.L1_Environment,
      parallax_depth: (baseLayers.L1_Environment?.parallax_depth ?? 1.15) * (0.95 + 0.08 * curveVal),
    }},
    L2_HeroSubject: {{
      ...baseLayers.L2_HeroSubject,
      curve_progress: curveVal,
    }},
    L3_MotionProps: {{
      ...baseLayers.L3_MotionProps,
      orb_boost: tGlobal >= DROP_SEC ? 1.25 : 1.0,
    }},
    L4_TypographyHUD: {{
      ...baseLayers.L4_TypographyHUD,
    }},
    L5_PostFX: {{
      ...baseLayers.L5_PostFX,
      beat_flash: Boolean(baseLayers.L5_PostFX?.beat_flash) || Math.abs(tGlobal - DROP_SEC) < 0.14,
    }},
  }};
}}
"""

    # 2. film.mjs — Shot list (EDL), CameraRig evaluation, and stateless sceneFor(frameIndex)
    film_mjs_code = f"""// Auto-generated & Agent-Editable Film Shot List & Stateless Scene Factory (film.mjs)
// Job ID: {script.get("job_id")}
// Stateless contract: sceneFor(frameIndex) returns the exact scene descriptor for any frame i in isolation.

import {{ CameraRig }} from '/backend/engine/core/camera.mjs';
import {{ SHOT_SPECS, evaluateStoryLayers, audioEnergyAt }} from './story.mjs';

export const FPS = {fps};
export const FRAMES = {total_frames};
export const WIDTH = {width};
export const HEIGHT = {height};

export const SHOTS = SHOT_SPECS;

export function shotFor(frameIndex) {{
  const t = frameIndex / FPS;
  for (let i = 0; i < SHOTS.length; i++) {{
    const s = SHOTS[i];
    if (t >= s.in_sec - 1e-6 && t < s.out_sec - 1e-6) return s;
  }}
  return SHOTS[SHOTS.length - 1];
}}

/**
 * Pure stateless scene factory for frame i (0 <= i < FRAMES)
 */
export function sceneFor(frameIndex, opts = {{}}) {{
  const W = opts.width || WIDTH;
  const H = opts.height || HEIGHT;
  const tGlobal = frameIndex / FPS;
  const shot = shotFor(frameIndex);
  const tLocal = Math.max(0, tGlobal - shot.in_sec);
  const shotDur = Math.max(0.1, shot.out_sec - shot.in_sec);

  const cam = CameraRig.evaluate({{
    move: shot.camera_move || 'dolly_in',
    shotSize: shot.shot_size || 'MEDIUM',
    tLocal,
    shotDur,
    seed: (shot.index || 0) * 17 + 1,
    shakeIntensity: 0.55,
  }});

  const layers = evaluateStoryLayers(shot, tGlobal, tLocal);
  const audioAmp = audioEnergyAt(tGlobal);

  return {{
    frameIndex,
    width: W,
    height: H,
    fps: FPS,
    shotId: shot.id,
    shotSize: shot.shot_size,
    tGlobal,
    tLocal,
    shotDur,
    cam,
    layers,
    audioAmp,
  }};
}}
"""

    # 3. render_job.mjs — Node CLI entrypoint supporting --frames a-b, --shot Sx, --layer Lx, --dry-run
    render_job_mjs_code = f"""#!/usr/bin/env node
// Stateless Render Job Runner (render_job.mjs)
// Usage: node shots/render_job.mjs [--frames 0-{total_frames - 1}] [--shot S1] [--layer L2_HeroSubject] [--mode master|preview] [--dry-run]
import {{ spawnSync }} from 'node:child_process';
import path from 'node:path';
import {{ fileURLToPath }} from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const JOB_DIR = path.resolve(HERE, '..');
const PARALLEL_RENDERER = '/workspace/studios/code-higgsfield/backend/renderer/parallel_renderer.py';

const args = process.argv.slice(2);
const res = spawnSync('python3', [PARALLEL_RENDERER, JOB_DIR, ...args], {{ stdio: 'inherit' }});
process.exit(res.status ?? 0);
"""

    # 4. stage.html — Deterministic HTML5 Canvas Host loaded by Parallel Headless Chrome Workers & Frontend Live Preview
    stage_html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Code-Higgsfield Stage // {script.get("job_id")}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ width: {width}px; height: {height}px; overflow: hidden; background: #09090B; }}
    canvas {{ display: block; width: {width}px; height: {height}px; }}
  </style>
</head>
<body>
  <canvas id="stage" width="{width}" height="{height}"></canvas>
  <script type="module">
    import {{ sceneFor, FPS, FRAMES, WIDTH, HEIGHT, SHOTS }} from './film.mjs';
    import {{ renderSceneLayers }} from '/backend/engine/lib/geo_and_rigs.mjs';

    const canvas = document.getElementById('stage');
    const ctx = canvas.getContext('2d', {{ alpha: false }});

    window.__STUDIO_META = {{ FPS, FRAMES, WIDTH, HEIGHT, SHOTS }};

    window.__renderFrame = function(frameIndex, activeLayerFilter = null) {{
      const desc = sceneFor(frameIndex, {{ width: WIDTH, height: HEIGHT }});
      renderSceneLayers(ctx, desc, activeLayerFilter);
      return desc;
    }};

    // Render frame 0 immediately on boot
    window.__renderFrame(0, null);
    window.__STAGE_READY = true;
  </script>
</body>
</html>
"""

    story_path = shots_dir / "story.mjs"
    film_path = shots_dir / "film.mjs"
    render_job_path = shots_dir / "render_job.mjs"
    stage_path = shots_dir / "stage.html"

    story_path.write_text(story_mjs_code, encoding="utf-8")
    film_path.write_text(film_mjs_code, encoding="utf-8")
    render_job_path.write_text(render_job_mjs_code, encoding="utf-8")
    render_job_path.chmod(0o755)
    stage_path.write_text(stage_html_code, encoding="utf-8")

    return {
        "story_mjs": str(story_path),
        "film_mjs": str(film_path),
        "render_job_mjs": str(render_job_path),
        "stage_html": str(stage_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate 3-file stateless scene graph (story.mjs, film.mjs, render_job.mjs)")
    parser.add_argument("job_dir", type=Path)
    args = parser.parse_args()
    out = generate_3file_scene_graph(args.job_dir)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
