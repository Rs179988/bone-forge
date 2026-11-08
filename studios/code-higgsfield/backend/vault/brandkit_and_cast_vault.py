#!/usr/bin/env python3
"""
Layer 6C: Persistent BrandKit DNA & Soul ID Character/Component Rig Vault
Updated with Light Editorial (WizardZ / Positivus), Royal Violet Daylight, Warm Ivory Craft,
and Obsidian Cinema palettes so videos are never forced into generic dark-only slop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parents[2]
BRANDKITS_DIR = STUDIO_ROOT / "brandkits"
CAST_DIR = STUDIO_ROOT / "cast"

DEFAULT_BRANDKITS: list[dict[str, Any]] = [
    {
        "id": "wizardz_editorial_light",
        "name": "WizardZ Editorial Light & Acid Lime (Default)",
        "typography": {"heading": "Space Grotesk", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 220.0, "damping": 18.0, "primary_curve": "backOut"},
        "palette": {
            "theme_mode": "light",
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F3F3F3",
            "accent_primary": "#B9FF66",
            "accent_secondary": "#191A23",
            "alert_color": "#FF4D4D",
            "text_primary": "#191A23",
            "text_muted": "#595A66",
            "surface_card": "#FFFFFF",
            "surface_dark": "#191A23",
            "border_ink": "#191A23",
            "texture": "paper_a",
        },
    },
    {
        "id": "royal_violet_daylight",
        "name": "Royal Violet & Crisp Daylight",
        "typography": {"heading": "Space Grotesk", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 205.0, "damping": 19.0, "primary_curve": "springDamper"},
        "palette": {
            "theme_mode": "light",
            "bg_primary": "#FAF8FF",
            "bg_secondary": "#EDE9FE",
            "accent_primary": "#7C3AED",
            "accent_secondary": "#EC4899",
            "alert_color": "#F43F5E",
            "text_primary": "#1E1B4B",
            "text_muted": "#5B21B6",
            "surface_card": "#FFFFFF",
            "surface_dark": "#1E1B4B",
            "border_ink": "#1E1B4B",
            "texture": "frosted_glass",
        },
    },
    {
        "id": "warm_ivory_craft",
        "name": "Warm Ivory & Tactile Coral Craft",
        "typography": {"heading": "Space Grotesk", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 235.0, "damping": 16.0, "primary_curve": "ring"},
        "palette": {
            "theme_mode": "light",
            "bg_primary": "#FFFDF9",
            "bg_secondary": "#F5EFE6",
            "accent_primary": "#FF6B4A",
            "accent_secondary": "#10B981",
            "alert_color": "#EF4444",
            "text_primary": "#1C1917",
            "text_muted": "#57534E",
            "surface_card": "#FFFFFF",
            "surface_dark": "#1C1917",
            "border_ink": "#1C1917",
            "texture": "felt_a",
        },
    },
    {
        "id": "higgsfield_obsidian_lime",
        "name": "Obsidian Studio & Acid Lime (Dark)",
        "typography": {"heading": "Space Grotesk", "mono": "JetBrains Mono"},
        "motion_physics": {"stiffness": 210.0, "damping": 18.0, "primary_curve": "backOut"},
        "palette": {
            "theme_mode": "dark",
            "bg_primary": "#09090B",
            "bg_secondary": "#121318",
            "accent_primary": "#B9FF66",
            "accent_secondary": "#00F5D4",
            "alert_color": "#FF3366",
            "text_primary": "#F8FAFC",
            "text_muted": "#94A3B8",
            "surface_card": "#14161F",
            "surface_dark": "#09090B",
            "border_ink": "#B9FF00",
            "texture": "brushed_metal",
        },
    },
]

DEFAULT_CAST_RIGS: list[dict[str, Any]] = [
    {
        "id": "rig_wizardz_editorial_deck",
        "name": "WizardZ // Neo-Brutalist Editorial Deck",
        "kind": "saas_3d_card",
        "blurb": "Crisp white & charcoal neo-brutalist card rig with #B9FF66 lime highlight pills, live metric odometer, and vector megaphone/starburst geometry.",
        "accent_color": "#B9FF66",
        "default_stiffness": 220.0,
        "default_damping": 18.0,
    },
    {
        "id": "soul_editorial_director",
        "name": "Aegis // Studio Director Character Rig",
        "kind": "character_rig",
        "blurb": "Articulated 2.5D character rig with audio-reactive lip-sync, expressive eyes, and neo-brutalist ink outlines.",
        "accent_color": "#B9FF66",
        "default_stiffness": 225.0,
        "default_damping": 17.0,
    },
    {
        "id": "soul_felt_pip",
        "name": "Chik & Wool // Tactile Story Character Rig",
        "kind": "character_rig",
        "blurb": "Stop-motion tactile character rig with spring squash-and-stretch hops and damped ring oscillation.",
        "accent_color": "#FF6B4A",
        "default_stiffness": 250.0,
        "default_damping": 15.0,
    },
    {
        "id": "rig_violet_product_showcase",
        "name": "Prism // Daylight Product Showcase Card",
        "kind": "saas_3d_card",
        "blurb": "High-contrast daylight & royal violet interactive UI showcase rig with smooth cursor choreography.",
        "accent_color": "#7C3AED",
        "default_stiffness": 200.0,
        "default_damping": 20.0,
    },
]


def ensure_default_vault() -> dict[str, Any]:
    BRANDKITS_DIR.mkdir(parents=True, exist_ok=True)
    CAST_DIR.mkdir(parents=True, exist_ok=True)

    for bk in DEFAULT_BRANDKITS:
        p = BRANDKITS_DIR / f"{bk['id']}.json"
        p.write_text(json.dumps(bk, indent=2) + "\n", encoding="utf-8")

    for cr in DEFAULT_CAST_RIGS:
        p = CAST_DIR / f"{cr['id']}.json"
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
