#!/usr/bin/env python3
"""
Layer 1A: Deterministic Motion Script Validator & Pacing Gate
Adapted from higgsfield-ai/skills (higgsfield-faceless-video/scripts/validate_motion_script.py)
and extended for CODE-HIGGSFIELD 6-Layer Stateless Scene Graph (story.mjs + film.mjs).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

ARC_ROLES = {"hook", "build", "turn", "payoff"}
VALID_SHOT_SIZES = {"WIDE", "MEDIUM", "CU", "ECU", "DETAIL", "OTS", "TOP", "MACRO"}
REQUIRED_LAYERS = [
    "L0_Backdrop",
    "L1_Environment",
    "L2_HeroSubject",
    "L3_MotionProps",
    "L4_TypographyHUD",
    "L5_PostFX",
]
VALID_CURVES = {"smooth", "easeIn", "easeOut", "easeInOut", "backOut", "ring", "springDamper", "keys"}

FILLER_PATTERN = re.compile(
    r"\b(?:you\s+know|y'?know|i\s+mean|sort\s+of|kinda|basically|um+|uh+|erm)\b",
    re.IGNORECASE | re.UNICODE,
)


def compute_script_digest(script: dict[str, Any]) -> str:
    """Compute a canonical SHA-256 lock hash over narrative + shot structure."""
    canonical = {
        "title": script.get("title", ""),
        "genre": script.get("genre", ""),
        "fps": script.get("fps", 60),
        "duration_sec": script.get("duration_sec", 10.0),
        "through_line": script.get("through_line", {}),
        "cast": [c.get("id") for c in script.get("cast", []) if isinstance(c, dict)],
        "shots": [
            {
                "id": s.get("id"),
                "in_sec": round(float(s.get("in_sec", 0.0)), 3),
                "out_sec": round(float(s.get("out_sec", 0.0)), 3),
                "shot_size": s.get("shot_size"),
                "subject": s.get("subject"),
                "spoken_line": s.get("spoken_line", ""),
            }
            for s in script.get("shots", [])
            if isinstance(s, dict)
        ],
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_script(script: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    """
    Validate script.json against Higgsfield Code-Film & Faceless-Video discipline gates.
    Returns (passed, errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(script, dict):
        return False, ["Root of script.json must be a JSON object."], []

    # 1. Core metadata checks
    genre = script.get("genre")
    if not isinstance(genre, str) or not genre.strip():
        errors.append("Missing or empty 'genre' field.")

    fps = int(script.get("fps", 60))
    if fps not in (24, 30, 60):
        errors.append(f"Invalid 'fps': {fps}. Must be 24, 30, or 60.")

    duration_sec = float(script.get("duration_sec", 0))
    if duration_sec < 4.0 or duration_sec > 180.0:
        errors.append(f"Invalid 'duration_sec': {duration_sec}. Must be between 4.0 and 180.0 seconds.")

    # 2. Cast / Asset Roster Gate
    cast = script.get("cast")
    if not isinstance(cast, list) or len(cast) < 1:
        errors.append("'cast' must be a non-empty list of reusable character/UI component rigs.")
    else:
        seen_cast_ids = set()
        for idx, member in enumerate(cast):
            if not isinstance(member, dict) or not member.get("id") or not member.get("kind"):
                errors.append(f"cast[{idx}] must be an object with 'id' and 'kind'.")
            else:
                cid = str(member["id"])
                if cid in seen_cast_ids:
                    errors.append(f"Duplicate cast id '{cid}'.")
                seen_cast_ids.add(cid)

    # 3. Through-Line Progression Object Gate
    through_line = script.get("through_line")
    if not isinstance(through_line, dict) or not through_line.get("object_id") or not through_line.get("progression"):
        errors.append(
            "Missing 'through_line': must define {'object_id': ..., 'progression': [...]} "
            "that evolves across shots."
        )
    elif isinstance(through_line.get("progression"), list) and len(through_line["progression"]) < 3:
        errors.append("'through_line.progression' must contain at least 3 state transitions across the video.")

    # 4. Narrative Arc Gate
    arc = script.get("arc")
    if not isinstance(arc, dict):
        errors.append("Missing 'arc' object defining hook, build, turn, payoff.")
    else:
        missing_roles = ARC_ROLES - set(arc.keys())
        if missing_roles:
            errors.append(f"'arc' is missing required narrative roles: {sorted(missing_roles)}")

    # 5. Shots Density, Framing Contrast, and Layer Contract Gate
    shots = script.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("'shots' must be a non-empty array.")
        return False, errors, warnings

    min_shots_required = max(5, int(math.floor((duration_sec / 10.0) * 5)))
    if len(shots) < min_shots_required:
        errors.append(
            f"Shot density gate failed: found {len(shots)} shots for {duration_sec:.1f}s video, "
            f"but Higgsfield discipline requires at least {min_shots_required} shots (5 shots per 10s block)."
        )

    prev_size = None
    prev_subject = None
    prev_out = 0.0
    establishing_seen = False

    for idx, shot in enumerate(shots):
        if not isinstance(shot, dict):
            errors.append(f"shots[{idx}] must be an object.")
            continue

        sid = shot.get("id", f"S{idx+1}")
        in_sec = float(shot.get("in_sec", -1))
        out_sec = float(shot.get("out_sec", -1))
        shot_dur = out_sec - in_sec

        if in_sec < 0 or out_sec <= in_sec:
            errors.append(f"Shot '{sid}' has invalid timing: in_sec={in_sec}, out_sec={out_sec}.")
        if abs(in_sec - prev_out) > 0.05:
            errors.append(f"Shot '{sid}' timing gap/overlap: starts at {in_sec:.3f}s, previous ended at {prev_out:.3f}s.")
        prev_out = out_sec

        if shot_dur > 2.8 and not shot.get("allow_long_take"):
            errors.append(
                f"Shot '{sid}' duration is {shot_dur:.2f}s (> 2.8s max per cut without allow_long_take)."
            )
        if shot_dur < 0.6:
            errors.append(f"Shot '{sid}' duration is {shot_dur:.2f}s (< 0.6s minimum readable cut).")

        shot_size = str(shot.get("shot_size", "")).upper()
        if shot_size not in VALID_SHOT_SIZES:
            errors.append(f"Shot '{sid}' has invalid shot_size '{shot_size}'. Valid: {sorted(VALID_SHOT_SIZES)}.")
        else:
            if shot_size in {"WIDE", "TOP"}:
                establishing_seen = True
            if prev_size == shot_size:
                errors.append(
                    f"Shot contrast gate failed at '{sid}': consecutive shots cannot share shot_size '{shot_size}'."
                )
            prev_size = shot_size

        subject = str(shot.get("subject", "")).strip()
        if not subject:
            errors.append(f"Shot '{sid}' is missing 'subject'.")
        elif prev_subject and prev_subject.lower() == subject.lower() and not shot.get("allow_same_subject"):
            warnings.append(f"Shot '{sid}' repeats subject '{subject}' from previous shot; ensure camera angle shifts >= 35 deg.")
        prev_subject = subject

        # Check motion curve discipline (ban pure linear motion)
        curve = shot.get("primary_curve", "backOut")
        if curve not in VALID_CURVES:
            errors.append(f"Shot '{sid}' uses invalid primary_curve '{curve}'. Valid: {sorted(VALID_CURVES)}.")

        # Check 6-Layer Scene Graph presence
        layers = shot.get("layers")
        if not isinstance(layers, dict):
            errors.append(f"Shot '{sid}' is missing 'layers' object (must contain L0_Backdrop..L5_PostFX).")
        else:
            for req_layer in REQUIRED_LAYERS:
                if req_layer not in layers:
                    errors.append(f"Shot '{sid}' is missing required isolated layer '{req_layer}'.")

        # Check spoken line filler gate
        spoken = str(shot.get("spoken_line", "")).strip()
        if spoken and FILLER_PATTERN.search(spoken):
            errors.append(f"Shot '{sid}' spoken_line contains banned conversational filler words.")

    if not establishing_seen:
        errors.append("Framing gate failed: at least one shot must be 'WIDE' or 'TOP' to establish spatial geography.")

    if abs(prev_out - duration_sec) > 0.15:
        errors.append(f"Total shot timeline ends at {prev_out:.2f}s, which does not match duration_sec={duration_sec:.2f}s.")

    return len(errors) == 0, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Code-Higgsfield motion script.json and write script.lock")
    parser.add_argument("script_path", type=Path, help="Path to script.json")
    parser.add_argument("--write-lock", action="store_true", default=True, help="Write script.lock on success")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    if not args.script_path.exists():
        print(json.dumps({"passed": False, "errors": [f"File not found: {args.script_path}"]}), file=sys.stderr)
        return 1

    try:
        script = json.loads(args.script_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"passed": False, "errors": [f"Invalid JSON: {exc}"]}), file=sys.stderr)
        return 1

    passed, errors, warnings = validate_script(script)
    digest = compute_script_digest(script) if passed else None
    lock_path = args.script_path.parent / "script.lock"

    if passed and args.write_lock and digest:
        lock_payload = {
            "sha256": digest,
            "script_path": str(args.script_path.resolve()),
            "shot_count": len(script.get("shots", [])),
            "duration_sec": script.get("duration_sec", 10.0),
            "fps": script.get("fps", 60),
            "status": "LOCKED",
        }
        lock_path.write_text(json.dumps(lock_payload, indent=2) + "\n", encoding="utf-8")

    result = {
        "passed": passed,
        "sha256": digest,
        "lock_file": str(lock_path) if (passed and args.write_lock) else None,
        "shot_count": len(script.get("shots", [])) if isinstance(script, dict) else 0,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if passed:
            print(f"[PASS] script.json validated ({result['shot_count']} shots). Lock hash: {digest[:16]}...")
            for w in warnings:
                print(f"  [WARN] {w}")
        else:
            print("[FAIL] script.json failed validation:")
            for e in errors:
                print(f"  [ERROR] {e}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
