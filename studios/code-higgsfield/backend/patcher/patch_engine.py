#!/usr/bin/env python3
"""
Layer 5B: Surgical Layer & Shot Timeline Patcher ("Miracle Mode" + Vibe Motion Live Edit)
Modifies a single layer (L0_Backdrop..L5_PostFX) or shot in script.json / story.mjs,
re-renders ONLY the affected shot's frame window, writes patches.json, and runs assemble_partial_edit.sh
to splice the patched frames into master_60fps.mp4 without re-rendering the rest of the film.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO_ROOT / "backend" / "compiler"))
sys.path.insert(0, str(STUDIO_ROOT / "backend" / "renderer"))

from validate_motion_script import compute_script_digest, validate_script  # type: ignore
from scene_scaffold_generator import generate_3file_scene_graph  # type: ignore
from parallel_renderer import execute_render_pipeline  # type: ignore

ASSEMBLE_SH = STUDIO_ROOT / "backend" / "patcher" / "assemble_partial_edit.sh"


def apply_surgical_patch(
    job_dir: Path,
    shot_id: str,
    layer_id: str | None = None,
    layer_updates: dict[str, Any] | None = None,
    shot_updates: dict[str, Any] | None = None,
    instruction: str | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    script_path = job_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script.json in {job_dir}")

    script = json.loads(script_path.read_text(encoding="utf-8"))
    shots = script.get("shots", [])
    target_shot = next((s for s in shots if s.get("id") == shot_id), None)
    if not target_shot:
        raise ValueError(f"Shot '{shot_id}' not found in script.json")

    # Apply natural language instruction heuristics if provided
    if instruction:
        low = instruction.lower()
        if "neon" in low or "green" in low or "lime" in low:
            target_shot["layers"]["L2_HeroSubject"]["accent_color"] = "#00FF66"
            target_shot["layers"]["L4_TypographyHUD"]["accent_color"] = "#00FF66"
        elif "cyan" in low or "blue" in low:
            target_shot["layers"]["L2_HeroSubject"]["accent_color"] = "#00F5D4"
            target_shot["layers"]["L4_TypographyHUD"]["accent_color"] = "#00F5D4"
        elif "amber" in low or "gold" in low:
            target_shot["layers"]["L2_HeroSubject"]["accent_color"] = "#F59E0B"
            target_shot["layers"]["L4_TypographyHUD"]["accent_color"] = "#F59E0B"
        if "bounce" in low or "spring" in low or "faster" in low:
            target_shot["layers"]["L2_HeroSubject"]["stiffness"] = 310.0
            target_shot["layers"]["L2_HeroSubject"]["damping"] = 14.0
        if "character" in low or "puppet" in low:
            target_shot["layers"]["L2_HeroSubject"]["kind"] = "character_rig"

    # Apply explicit JSON property overrides
    if shot_updates:
        for k, v in shot_updates.items():
            if k != "layers":
                target_shot[k] = v

    if layer_id and layer_updates:
        if layer_id not in target_shot.get("layers", {}):
            target_shot.setdefault("layers", {})[layer_id] = {}
        target_shot["layers"][layer_id].update(layer_updates)

    # Validate updated script & re-lock
    passed, errors, _ = validate_script(script)
    if not passed:
        raise ValueError(f"Patched script violated Higgsfield discipline gate: {errors}")

    script_path.write_text(json.dumps(script, indent=2) + "\n", encoding="utf-8")
    digest = compute_script_digest(script)
    (job_dir / "script.lock").write_text(
        json.dumps({"sha256": digest, "status": "PATCH_LOCKED", "patched_shot": shot_id}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Regenerate story.mjs & film.mjs with updated layer props
    generate_3file_scene_graph(job_dir)

    fps = int(script.get("fps", 60))
    in_f = int(target_shot.get("in_frame", round(float(target_shot["in_sec"]) * fps)))
    out_f = int(target_shot.get("out_frame", round(float(target_shot["out_sec"]) * fps)))
    patch_mp4 = job_dir / f"patch_{shot_id}_{in_f}_{out_f}.mp4"

    # Render ONLY the patched shot frames [in_f .. out_f-1]
    render_res = asyncio.run(
        execute_render_pipeline(
            job_dir=job_dir,
            mode="master",
            shot_id=shot_id,
            workers=2,
            out_mp4=patch_mp4,
        )
    )

    # Build patches.json manifest across all shots (keeping untouched shots & splicing only target_shot)
    manifest: list[dict[str, Any]] = []
    for s in shots:
        sid = s.get("id")
        s_in = float(s["in_sec"])
        s_out = float(s["out_sec"])
        if sid == shot_id:
            manifest.append(
                {
                    "shot_id": sid,
                    "mode": "patch",
                    "start_sec": s_in,
                    "end_sec": s_out,
                    "patch_video": str(patch_mp4),
                }
            )
        else:
            manifest.append(
                {
                    "shot_id": sid,
                    "mode": "keep",
                    "start_sec": s_in,
                    "end_sec": s_out,
                }
            )

    manifest_path = job_dir / "patches.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    master_mp4 = job_dir / "master_60fps.mp4"
    if master_mp4.exists():
        ASSEMBLE_SH.chmod(0o755)
        subprocess.run(
            [
                "bash",
                str(ASSEMBLE_SH),
                "--source",
                str(master_mp4),
                "--manifest",
                str(manifest_path),
                "--out",
                str(master_mp4),
            ],
            check=True,
        )

    return {
        "status": "SURGICAL_PATCH_COMPLETED",
        "job_id": script.get("job_id"),
        "patched_shot": shot_id,
        "patched_layer": layer_id,
        "patched_frames": f"{in_f}-{out_f - 1}",
        "frames_rerendered": out_f - in_f,
        "total_film_frames": script.get("total_frames", 600),
        "patch_manifest": str(manifest_path),
        "master_mp4": str(master_mp4),
        "wall_sec": round(time.time() - t0, 2),
        "render_stats": render_res,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Surgical Layer & Shot Patcher for Code-Higgsfield")
    parser.add_argument("job_dir", type=Path)
    parser.add_argument("--shot", required=True, help="Target shot ID e.g. S2")
    parser.add_argument("--layer", default="L2_HeroSubject", help="Target layer ID e.g. L2_HeroSubject")
    parser.add_argument("--props-json", default="{}", help="JSON object of layer property updates")
    parser.add_argument("--instruction", default=None, help="Natural language edit instruction")
    args = parser.parse_args()

    props = json.loads(args.props_json)
    res = apply_surgical_patch(
        job_dir=args.job_dir,
        shot_id=args.shot,
        layer_id=args.layer,
        layer_updates=props,
        instruction=args.instruction,
    )
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
