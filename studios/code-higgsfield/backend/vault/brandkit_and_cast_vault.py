#!/usr/bin/env python3
"""
Layer 6C: Persistent BrandKit DNA & Soul ID Character/Component Rig Vault
Adapted from higgsfield-ai/skills (higgsfield-brandkit & higgsfield-soul-id)
and Autom8AI/Open-Higgsfield-AI (src/lib/characters.js).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path("/workspace/studios/code-higgsfield")
BRANDKITS_DIR = STUDIO_ROOT / "brandkits"
CAST_DIR = STUDIO_ROOT / "cast"

DEFAULT_BRANDKITS: list[dict[str, Any]] = [
    {
        "id": "higgsfield_obsidian_lime",
        "name": "Higgsfield Obsidian & Acid Lime",
        "typography": {"heading": "Inter", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 210.0, "damping": 18.0, "primary_curve": "backOut"},
        "palette": {
            "bg_primary": "#09090B",
            "bg_secondary": "#121318",
            "accent_primary": "#D4FF00",
            "accent_secondary": "#00F5D4",
            "text_primary": "#F8FAFC",
            "texture": "brushed_metal",
        },
    },
    {
        "id": "cupertino_titanium",
        "name": "Cupertino Titanium & Cyan",
        "typography": {"heading": "Inter", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 185.0, "damping": 22.0, "primary_curve": "springDamper"},
        "palette": {
            "bg_primary": "#06080E",
            "bg_secondary": "#0F172A",
            "accent_primary": "#38BDF8",
            "accent_secondary": "#818CF8",
            "text_primary": "#FFFFFF",
            "texture": "frosted_glass",
        },
    },
    {
        "id": "cinema_noir_amber",
        "name": "Cinema Noir & Warm Amber",
        "typography": {"heading": "Inter", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 160.0, "damping": 16.0, "primary_curve": "ring"},
        "palette": {
            "bg_primary": "#0A0807",
            "bg_secondary": "#1A1412",
            "accent_primary": "#F59E0B",
            "accent_secondary": "#EF4444",
            "text_primary": "#FEF3C7",
            "texture": "paper_a",
        },
    },
    {
        "id": "felt_stopmotion_craft",
        "name": "Tactile Felt & Warm Daylight",
        "typography": {"heading": "Inter", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 240.0, "damping": 15.0, "primary_curve": "backOut"},
        "palette": {
            "bg_primary": "#141824",
            "bg_secondary": "#22293E",
            "accent_primary": "#FBBF24",
            "accent_secondary": "#34D399",
            "text_primary": "#FFFBEB",
            "texture": "felt_a",
        },
    },
]

DEFAULT_CAST_RIGS: list[dict[str, Any]] = [
    {
        "id": "soul_cyber_architect",
        "name": "Aegis // Cyber Director Rig",
        "kind": "character_rig",
        "blurb": "Articulated 2.5D studio director puppet with audio-reactive lip-sync, visor blink timer, and dual rim-light.",
        "accent_color": "#D4FF00",
        "default_stiffness": 220.0,
        "default_damping": 17.0,
    },
    {
        "id": "soul_felt_pip",
        "name": "Chik & Wool // Tactile Felt Rig",
        "kind": "character_rig",
        "blurb": "Stop-motion felt character rig with spring squash-and-stretch hops and damped ring oscillation.",
        "accent_color": "#FBBF24",
        "default_stiffness": 260.0,
        "default_damping": 14.0,
    },
    {
        "id": "rig_quantum_saas_card",
        "name": "Quantum // 3D Glass Telemetry Deck",
        "kind": "saas_3d_card",
        "blurb": "Glassmorphic 3D SaaS dashboard card with odometer counter, live sparkline spline, and frequency bars.",
        "accent_color": "#00F5D4",
        "default_stiffness": 210.0,
        "default_damping": 18.0,
    },
    {
        "id": "rig_fintech_terminal",
        "name": "Apex // Fintech Orderbook Rig",
        "kind": "saas_3d_card",
        "blurb": "High-contrast titanium trading & metrics rig with velocity-trailed cursor and click ripple.",
        "accent_color": "#38BDF8",
        "default_stiffness": 195.0,
        "default_damping": 20.0,
    },
]


def ensure_default_vault() -> dict[str, Any]:
    BRANDKITS_DIR.mkdir(parents=True, exist_ok=True)
    CAST_DIR.mkdir(parents=True, exist_ok=True)

    for bk in DEFAULT_BRANDKITS:
        p = BRANDKITS_DIR / f"{bk['id']}.json"
        if not p.exists():
            p.write_text(json.dumps(bk, indent=2) + "\n", encoding="utf-8")

    for cr in DEFAULT_CAST_RIGS:
        p = CAST_DIR / f"{cr['id']}.json"
        if not p.exists():
            p.write_text(json.dumps(cr, indent=2) + "\n", encoding="utf-8")

    return list_vault()


def list_vault() -> dict[str, Any]:
    BRANDKITS_DIR.mkdir(parents=True, exist_ok=True)
    CAST_DIR.mkdir(parents=True, exist_ok=True)
    brandkits = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(BRANDKITS_DIR.glob("*.json"))]
    cast_rigs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CAST_DIR.glob("*.json"))]
    return {"brandkits": brandkits, "cast_rigs": cast_rigs}


def upsert_vault_item(item_type: str, item_data: dict[str, Any]) -> dict[str, Any]:
    ensure_default_vault()
    item_id = str(item_data.get("id") or f"custom_{len(list(BRANDKITS_DIR.glob('*.json'))) + 1}")
    item_data["id"] = item_id
    target_dir = BRANDKITS_DIR if item_type == "brandkit" else CAST_DIR
    out_path = target_dir / f"{item_id}.json"
    out_path.write_text(json.dumps(item_data, indent=2) + "\n", encoding="utf-8")
    return {"status": "SAVED", "type": item_type, "id": item_id, "path": str(out_path), "item": item_data}


if __name__ == "__main__":
    data = ensure_default_vault()
    print(json.dumps({"brandkits_count": len(data["brandkits"]), "cast_rigs_count": len(data["cast_rigs"])}, indent=2))
