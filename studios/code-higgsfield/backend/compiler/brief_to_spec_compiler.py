#!/usr/bin/env python3
"""
Layer 1B: Studio Brief-to-Spec Compiler
Translates raw Studio UI controls & user prompts into a validated Studio Execution Contract:
  - jobs/<job_id>/job_spec.json
  - jobs/<job_id>/script.json
  - jobs/<job_id>/script.lock
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

from validate_motion_script import compute_script_digest, validate_script

STUDIO_ROOT = Path("/workspace/studios/code-higgsfield")
JOBS_DIR = STUDIO_ROOT / "jobs"
BRANDKITS_DIR = STUDIO_ROOT / "brandkits"
CAST_DIR = STUDIO_ROOT / "cast"

PALETTE_PRESETS: dict[str, dict[str, Any]] = {
    "higgsfield_obsidian_lime": {
        "name": "Higgsfield Obsidian & Acid Lime",
        "bg_primary": "#09090B",
        "bg_secondary": "#121318",
        "accent_primary": "#D4FF00",
        "accent_secondary": "#00F5D4",
        "alert_color": "#FF3366",
        "text_primary": "#F8FAFC",
        "text_muted": "#94A3B8",
        "surface_glass": "rgba(24, 26, 34, 0.78)",
        "texture": "brushed_metal",
    },
    "cupertino_titanium": {
        "name": "Cupertino Titanium & Cyan",
        "bg_primary": "#06080E",
        "bg_secondary": "#0F172A",
        "accent_primary": "#38BDF8",
        "accent_secondary": "#818CF8",
        "alert_color": "#F43F5E",
        "text_primary": "#FFFFFF",
        "text_muted": "#94A3B8",
        "surface_glass": "rgba(15, 23, 42, 0.80)",
        "texture": "frosted_glass",
    },
    "cinema_noir_amber": {
        "name": "Cinema Noir & Warm Amber",
        "bg_primary": "#0A0807",
        "bg_secondary": "#1A1412",
        "accent_primary": "#F59E0B",
        "accent_secondary": "#EF4444",
        "alert_color": "#DC2626",
        "text_primary": "#FEF3C7",
        "text_muted": "#D6D3D1",
        "surface_glass": "rgba(28, 22, 19, 0.82)",
        "texture": "paper_a",
    },
    "felt_stopmotion_craft": {
        "name": "Tactile Felt & Warm Daylight",
        "bg_primary": "#141824",
        "bg_secondary": "#22293E",
        "accent_primary": "#FBBF24",
        "accent_secondary": "#34D399",
        "alert_color": "#FB7185",
        "text_primary": "#FFFBEB",
        "text_muted": "#CBD5E1",
        "surface_glass": "rgba(34, 41, 62, 0.82)",
        "texture": "felt_a",
    },
}

ASPECT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def _extract_topic_keywords(prompt: str) -> dict[str, Any]:
    """Extract clean semantic tokens and domain intent from user prompt."""
    clean = prompt.strip()
    lower = clean.lower()

    is_story_or_cinema = any(
        w in lower
        for w in ["story", "character", "cinema", "short", "horror", "detective", "casino", "history", "narrative", "felt", "puppet"]
    )
    is_fintech_or_saas = any(
        w in lower
        for w in ["saas", "fintech", "dashboard", "ui", "app", "promo", "launch", "metric", "revenue", "ai", "crypto", "card", "vibe"]
    )

    words = [w.upper() for w in re.findall(r"[A-Za-z0-9$%+.-]+", clean) if len(w) > 2]
    stop = {"THE", "AND", "FOR", "WITH", "MAKE", "CREATE", "VIDEO", "SHORT", "ABOUT", "STYLE", "INTO", "FROM", "THAT", "THIS"}
    keywords = [w for w in words if w not in stop][:12]
    if not keywords:
        keywords = ["QUANTUM", "ENGINE", "60FPS", "PRECISION", "LAUNCH"]

    return {
        "is_story": is_story_or_cinema and not is_fintech_or_saas,
        "is_saas": is_fintech_or_saas or not is_story_or_cinema,
        "keywords": keywords,
        "raw": clean,
    }


def compile_brief_to_job(
    prompt: str,
    studio_mode: str = "vibe_motion",
    aspect_ratio: str = "9:16",
    duration_sec: float = 10.0,
    fps: int = 60,
    palette_id: str = "higgsfield_obsidian_lime",
    camera_preset: str = "dynamic_cinema",
    stiffness: float = 210.0,
    damping: float = 18.0,
    brandkit_id: str | None = None,
    cast_ids: list[str] | None = None,
    katana_blueprint: dict[str, Any] | None = None,
    job_id: str | None = None,
    custom_shots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Deterministically compile UI controls + prompt into a validated Studio job directory
    with job_spec.json, script.json, and script.lock.
    """
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    BRANDKITS_DIR.mkdir(parents=True, exist_ok=True)
    CAST_DIR.mkdir(parents=True, exist_ok=True)

    if not job_id:
        ts = time.strftime("%Y%m%d_%H%M%S")
        short_uid = uuid.uuid4().hex[:6]
        job_id = f"hf_{studio_mode}_{ts}_{short_uid}"

    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "shots").mkdir(exist_ok=True)
    (job_dir / "audio").mkdir(exist_ok=True)
    (job_dir / "qa").mkdir(exist_ok=True)

    width, height = ASPECT_DIMENSIONS.get(aspect_ratio, (1080, 1920))
    palette = dict(PALETTE_PRESETS.get(palette_id, PALETTE_PRESETS["higgsfield_obsidian_lime"]))

    # Load custom BrandKit override if specified
    if brandkit_id and (BRANDKITS_DIR / f"{brandkit_id}.json").exists():
        bk = json.loads((BRANDKITS_DIR / f"{brandkit_id}.json").read_text(encoding="utf-8"))
        palette.update(bk.get("palette", {}))

    sem = _extract_topic_keywords(prompt)
    kw = sem["keywords"]
    hero_kind = "character_rig" if studio_mode == "cinema_shorts" or sem["is_story"] else "saas_3d_card"

    # Determine shot count and cut timings (from Katana blueprint if provided, else 5 shots per 10s block)
    num_shots = max(5, int(round((duration_sec / 10.0) * 5)))
    cut_boundaries: list[tuple[float, float]] = []

    if katana_blueprint and isinstance(katana_blueprint.get("shots"), list) and len(katana_blueprint["shots"]) >= 5:
        raw_kshots = katana_blueprint["shots"][:num_shots]
        scale = duration_sec / max(0.1, float(raw_kshots[-1]["out_sec"]))
        cur = 0.0
        for idx, ks in enumerate(raw_kshots):
            out_t = duration_sec if idx == len(raw_kshots) - 1 else round(float(ks["out_sec"]) * scale, 3)
            if out_t - cur < 0.7:
                out_t = min(duration_sec, cur + 1.2)
            cut_boundaries.append((round(cur, 3), round(out_t, 3)))
            cur = out_t
    else:
        # Rhythmic golden-ratio / beat-aligned shot durations summing to duration_sec
        base_weights = [1.8, 2.1, 1.9, 2.2, 2.0]
        weights = [base_weights[i % len(base_weights)] for i in range(num_shots)]
        w_sum = sum(weights)
        cur = 0.0
        for i, w in enumerate(weights):
            nxt = duration_sec if i == num_shots - 1 else round(cur + (w / w_sum) * duration_sec, 3)
            cut_boundaries.append((round(cur, 3), round(nxt, 3)))
            cur = nxt

    shot_sizes_cycle = ["WIDE", "CU", "DETAIL", "MEDIUM", "OTS", "TOP"]
    camera_moves_cycle = ["dolly_in", "orbital_arc", "macro_rack_focus", "whip_pan", "dutch_tilt", "dolly_in"]
    curves_cycle = ["backOut", "ring", "springDamper", "backOut", "easeInOut"]
    sfx_cycle = ["whoosh", "ui_pop", "mechanical_click", "bass_sub_drop", "tada"]

    cast_roster = [
        {
            "id": "hero_primary",
            "kind": hero_kind,
            "name": f"{kw[0]} Core Rig",
            "soul_id": (cast_ids[0] if cast_ids else "soul_cyber_architect"),
            "accent_color": palette["accent_primary"],
        },
        {
            "id": "telemetry_orb",
            "kind": "through_line_prop",
            "name": "Pulse Chrono-Core",
            "accent_color": palette["accent_secondary"],
        },
    ]

    through_line = {
        "object_id": "telemetry_orb",
        "name": "Quantum Pulse Core",
        "progression": [
            "S1: Ignites at center of wide architectural grid at t=0.15s",
            "S2: Locks into Hero Subject interface socket with spring ring oscillation",
            "S3: Expands into macro internal waveform & metric counter array",
            "S4: Synchronizes multi-node kinetic beam across secondary props",
            "S5: Stabilizes into final Brand Seal & high-contrast CTA emblem",
        ],
    }

    default_narrations = [
        f"Look closely at {kw[0].title()}. Every frame is engineered with zero latency.",
        f"Inside the middle layer, deterministic curves lock motion to the exact millisecond.",
        f"Watch the real-time telemetry spike past ninety-nine point eight percent precision.",
        f"Click any isolated layer to patch physics, lighting, or typography on the fly.",
        f"Code Higgsfield Studio. Pure procedural cinema at sixty frames per second.",
    ]

    default_headlines = [
        f"{kw[0]} // ZERO SLOP",
        f"SPRING LOCKED: {int(stiffness)} N/m",
        "99.8% FRAME ACCURACY",
        "6-LAYER SURGICAL AST",
        f"CODE-HIGGSFIELD // {aspect_ratio}",
    ]

    shots: list[dict[str, Any]] = []
    if custom_shots and len(custom_shots) >= min(5, num_shots):
        shots = custom_shots
    else:
        for i, (in_s, out_s) in enumerate(cut_boundaries):
            s_size = shot_sizes_cycle[i % len(shot_sizes_cycle)]
            cam_move = camera_moves_cycle[i % len(camera_moves_cycle)]
            curve = curves_cycle[i % len(curves_cycle)]
            sfx_ev = sfx_cycle[i % len(sfx_cycle)]
            headline = default_headlines[i % len(default_headlines)]
            narration = default_narrations[i % len(default_narrations)]

            shots.append(
                {
                    "id": f"S{i+1}",
                    "index": i,
                    "in_sec": in_s,
                    "out_sec": out_s,
                    "in_frame": int(round(in_s * fps)),
                    "out_frame": int(round(out_s * fps)),
                    "shot_size": s_size,
                    "subject": f"{cast_roster[0]['id']}_angle_{i+1}",
                    "camera_move": cam_move,
                    "primary_curve": curve,
                    "spoken_line": narration,
                    "sfx_trigger": {"type": sfx_ev, "offset_sec": 0.08},
                    "layers": {
                        "L0_Backdrop": {
                            "palette_bg": palette["bg_primary"],
                            "palette_secondary": palette["bg_secondary"],
                            "texture": palette["texture"],
                            "ray_intensity": round(0.35 + 0.12 * (i % 3), 2),
                        },
                        "L1_Environment": {
                            "grid_mode": "perspective_vault" if i % 2 == 0 else "radial_matrix",
                            "parallax_depth": round(1.0 + 0.35 * i, 2),
                            "accent_color": palette["accent_secondary"],
                        },
                        "L2_HeroSubject": {
                            "cast_id": "hero_primary",
                            "kind": hero_kind,
                            "pose_mode": ["establish_rise", "close_inspect", "macro_pulse", "action_turn", "hero_lock"][i % 5],
                            "metric_value": [128.4, 492.0, 99.8, 1024.0, 60.0][i % 5],
                            "metric_unit": ["MS", "FPS", "%", "OPS", "FPS"][i % 5],
                            "stiffness": stiffness,
                            "damping": damping,
                            "accent_color": palette["accent_primary"],
                        },
                        "L3_MotionProps": {
                            "through_line_id": "telemetry_orb",
                            "through_line_state": i,
                            "cursor_active": (i in (1, 2, 3)),
                            "floating_badges": [kw[i % len(kw)], f"SHOT 0{i+1} // {s_size}"],
                        },
                        "L4_TypographyHUD": {
                            "headline": headline,
                            "sub_caption": narration,
                            "safe_margin_pct": 0.08,
                            "text_color": palette["text_primary"],
                            "accent_color": palette["accent_primary"],
                            "badge_tag": f"S{i+1} • {s_size} • {cam_move.upper()}",
                        },
                        "L5_PostFX": {
                            "bloom_intensity": 0.42 if i != 3 else 0.58,
                            "vignette": 0.22,
                            "chromatic_aberration": 0.0025 if cam_move == "whip_pan" else 0.001,
                            "beat_flash": (i in (0, 3)),
                        },
                    },
                }
            )

    script_payload: dict[str, Any] = {
        "job_id": job_id,
        "title": f"Code-Higgsfield // {' '.join(kw[:3])}",
        "prompt": prompt,
        "studio_mode": studio_mode,
        "genre": "cinema_story" if hero_kind == "character_rig" else "vibe_motion_tech",
        "aspect_ratio": aspect_ratio,
        "width": width,
        "height": height,
        "fps": fps,
        "duration_sec": duration_sec,
        "total_frames": int(round(duration_sec * fps)),
        "brand_kit": brandkit_id or palette_id,
        "palette": palette,
        "physics": {"stiffness": stiffness, "damping": damping, "overshoot_k": 1.9},
        "cast": cast_roster,
        "through_line": through_line,
        "arc": {
            "hook": f"S1 ({shots[0]['in_sec']}s-{shots[0]['out_sec']}s): Immediate {shots[0]['shot_size']} kinetic ignition of {kw[0]}.",
            "build": f"S2-S3: Escalating CU & DETAIL inspection with synced spring physics and telemetry proof.",
            "turn": f"S4: High-energy {shots[min(3, len(shots)-1)]['camera_move']} cut on musical drop.",
            "payoff": f"S{len(shots)}: Resolved Establishing Lock with persistent through-line seal.",
        },
        "shots": shots,
    }

    passed, errors, warnings = validate_script(script_payload)
    if not passed:
        raise ValueError(f"Compiled script failed validation gate: {errors}")

    digest = compute_script_digest(script_payload)
    script_path = job_dir / "script.json"
    lock_path = job_dir / "script.lock"
    spec_path = job_dir / "job_spec.json"

    script_path.write_text(json.dumps(script_payload, indent=2) + "\n", encoding="utf-8")

    lock_payload = {
        "sha256": digest,
        "job_id": job_id,
        "script_path": str(script_path),
        "shot_count": len(shots),
        "duration_sec": duration_sec,
        "fps": fps,
        "status": "LOCKED",
        "locked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    lock_path.write_text(json.dumps(lock_payload, indent=2) + "\n", encoding="utf-8")

    job_spec = {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "status": "COMPILED_AND_LOCKED",
        "created_at": lock_payload["locked_at"],
        "studio_mode": studio_mode,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "width": width,
        "height": height,
        "fps": fps,
        "duration_sec": duration_sec,
        "total_frames": int(round(duration_sec * fps)),
        "palette_id": palette_id,
        "camera_preset": camera_preset,
        "physics": {"stiffness": stiffness, "damping": damping},
        "script_lock_sha256": digest,
        "artifacts": {
            "script_json": str(script_path),
            "script_lock": str(lock_path),
            "story_mjs": str(job_dir / "shots" / "story.mjs"),
            "film_mjs": str(job_dir / "shots" / "film.mjs"),
            "render_job_mjs": str(job_dir / "shots" / "render_job.mjs"),
            "beatmap_json": str(job_dir / "audio" / "beatmap.json"),
            "narration_json": str(job_dir / "audio" / "narration_timing.json"),
            "master_audio_wav": str(job_dir / "audio" / "master_mix.wav"),
            "master_mp4": str(job_dir / "master_60fps.mp4"),
            "contact_sheet_png": str(job_dir / "qa" / "contact_sheet.png"),
            "qa_report_json": str(job_dir / "qa" / "qa_report.json"),
        },
        "warnings": warnings,
    }
    spec_path.write_text(json.dumps(job_spec, indent=2) + "\n", encoding="utf-8")
    return job_spec


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile raw Studio brief into locked job_spec.json + script.json")
    parser.add_argument("--prompt", required=True, help="User creative brief or prompt")
    parser.add_argument("--mode", default="vibe_motion", choices=["vibe_motion", "cinema_shorts", "katana_remix", "miracle_layer"])
    parser.add_argument("--aspect", default="9:16", choices=["9:16", "16:9", "1:1", "4:5"])
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--palette", default="higgsfield_obsidian_lime")
    parser.add_argument("--camera", default="dynamic_cinema")
    parser.add_argument("--stiffness", type=float, default=210.0)
    parser.add_argument("--damping", type=float, default=18.0)
    parser.add_argument("--job-id", default=None)
    args = parser.parse_args()

    spec = compile_brief_to_job(
        prompt=args.prompt,
        studio_mode=args.mode,
        aspect_ratio=args.aspect,
        duration_sec=args.duration,
        fps=args.fps,
        palette_id=args.palette,
        camera_preset=args.camera,
        stiffness=args.stiffness,
        damping=args.damping,
        job_id=args.job_id,
    )
    print(json.dumps(spec, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
