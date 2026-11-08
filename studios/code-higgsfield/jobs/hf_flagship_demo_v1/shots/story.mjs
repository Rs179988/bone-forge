// Auto-generated & Agent-Editable Story Timeline (story.mjs)
// Job ID: hf_flagship_demo_v1 | Genre: editorial_motion
// Pure functions of time t (seconds) using Higgsfield pre-built curve primitives.

import { clamp, lerp, smooth, easeIn, easeOut, easeInOut, backOut, ring, springDamper, keys, evaluateCurve } from '/backend/engine/core/curves.mjs';

export const JOB_ID = "hf_flagship_demo_v1";
export const PALETTE = {
  "name": "WizardZ Editorial Light & Acid Lime",
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
  "texture": "paper_a"
};
export const ENERGY_ENVELOPE = [0.257, 0.299, 0.276, 0.107, 0.141, 0.16, 0.268, 0.36, 0.296, 0.265, 0.388, 0.353, 0.218, 0.268, 0.101, 0.505, 0.365, 0.239, 0.327, 0.221, 0.359, 0.525, 0.229, 0.21, 0.15, 0.322, 0.104, 0.198, 0.117, 0.425, 0.282, 0.278, 0.257, 0.222, 0.161, 0.055, 0.122, 0.122, 0.207, 0.062, 0.315, 0.441, 0.218, 0.221, 0.34, 0.353, 0.475, 0.335, 0.219, 0.079, 0.257, 0.403, 0.311, 0.214, 0.191, 0.361, 0.468, 0.301, 0.164, 0.371, 0.336, 0.444, 0.284, 0.102, 0.13, 0.172, 0.376, 0.117, 0.116, 0.257, 0.464, 0.493, 0.306, 0.254, 0.409, 0.151, 0.123, 0.12, 0.12, 0.043, 0.375, 0.561, 0.353, 0.109, 0.132, 0.098, 0.134, 0.308, 0.385, 0.35, 0.305, 0.523, 0.35, 0.16, 0.341, 0.109, 0.123, 0.125, 0.114, 0.126, 0.45, 0.505, 0.358, 0.271, 0.119, 0.207, 0.169, 0.163, 0.118, 0.136, 0.248, 0.36, 0.372, 0.257, 0.15, 0.084, 0.12, 0.119, 0.481, 0.398, 0.365, 0.801, 0.212, 0.38, 0.353, 0.368, 0.361, 0.18, 0.167, 0.35, 0.31, 0.476, 0.386, 0.289, 0.192, 0.097, 0.218, 0.282, 0.283, 0.18, 0.203, 0.402, 0.373, 0.186, 0.129, 0.149, 0.13, 0.123, 0.111, 0.052, 0.169, 0.559, 0.275, 0.117, 0.093, 0.072, 0.122, 0.122, 0.117, 0.052, 0.573, 0.481, 0.419, 0.206, 0.222, 0.246, 0.385, 0.281, 0.262, 0.143, 0.469, 0.363, 0.331, 0.172, 0.289, 0.253, 0.113, 0.121, 0.344, 0.236, 0.38, 0.494, 0.351, 0.264, 0.237, 0.073, 0.162, 0.187, 0.2, 0.092, 0.464, 0.414, 0.323, 0.205, 0.107, 0.297, 0.203, 0.202, 0.184, 0.04];
export const DROP_SEC = 4.0166;

export const SHOT_SPECS = [
  {
    "id": "S1",
    "index": 0,
    "in_sec": 0.0,
    "out_sec": 1.8,
    "in_frame": 0,
    "out_frame": 108,
    "shot_size": "WIDE",
    "subject": "hero_primary_angle_1",
    "camera_move": "dolly_in",
    "primary_curve": "backOut",
    "spoken_line": "Navigating the digital landscape for success.",
    "sfx_trigger": {
      "type": "whoosh",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "theme_mode": "light",
        "palette_bg": "#FFFFFF",
        "palette_secondary": "#F3F3F3",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "texture": "paper_a",
        "ray_intensity": 0.28
      },
      "L1_Environment": {
        "grid_mode": "editorial_dots",
        "parallax_depth": 1.0,
        "accent_color": "#191A23",
        "highlight_color": "#B9FF66"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "card_variant": "white",
        "pose_mode": "establish_rise",
        "card_title": "NAVIGATING DIGITAL LANDSCAPE SUCCE",
        "metric_value": 240.0,
        "metric_unit": "%",
        "metric_label": "NAVIGATING DIGITAL IMPACT",
        "stiffness": 220.0,
        "damping": 18.0,
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 0,
        "cursor_active": false,
        "floating_badges": [
          "NAVIGATING",
          "01 // DIGITAL"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "NAVIGATING DIGITAL LANDSCAPE SUCCE",
        "sub_caption": "Navigating the digital landscape for success.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "01 \u2022 NAVIGATING"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.18,
        "vignette": 0.06,
        "chromatic_aberration": 0.001,
        "beat_flash": true
      }
    }
  },
  {
    "id": "S2",
    "index": 1,
    "in_sec": 1.8,
    "out_sec": 3.9,
    "in_frame": 108,
    "out_frame": 234,
    "shot_size": "CU",
    "subject": "hero_primary_angle_2",
    "camera_move": "orbital_arc",
    "primary_curve": "ring",
    "spoken_line": "search engine optimization.",
    "sfx_trigger": {
      "type": "ui_pop",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "theme_mode": "light",
        "palette_bg": "#FFFFFF",
        "palette_secondary": "#F3F3F3",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "texture": "paper_a",
        "ray_intensity": 0.36
      },
      "L1_Environment": {
        "grid_mode": "editorial_dots",
        "parallax_depth": 1.28,
        "accent_color": "#191A23",
        "highlight_color": "#B9FF66"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "card_variant": "dark",
        "pose_mode": "close_inspect",
        "card_title": "SEARCH ENGINE OPTIMIZATION",
        "metric_value": 240.0,
        "metric_unit": "%",
        "metric_label": "LANDSCAPE SUCCESS IMPACT",
        "stiffness": 220.0,
        "damping": 18.0,
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 1,
        "cursor_active": true,
        "floating_badges": [
          "LANDSCAPE",
          "02 // SUCCESS"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "SEARCH ENGINE OPTIMIZATION",
        "sub_caption": "search engine optimization.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "02 \u2022 DIGITAL"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.18,
        "vignette": 0.06,
        "chromatic_aberration": 0.001,
        "beat_flash": false
      }
    }
  },
  {
    "id": "S3",
    "index": 2,
    "in_sec": 3.9,
    "out_sec": 5.8,
    "in_frame": 234,
    "out_frame": 348,
    "shot_size": "DETAIL",
    "subject": "hero_primary_angle_3",
    "camera_move": "macro_rack_focus",
    "primary_curve": "springDamper",
    "spoken_line": "pay per click campaigns.",
    "sfx_trigger": {
      "type": "mechanical_click",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "theme_mode": "light",
        "palette_bg": "#FFFFFF",
        "palette_secondary": "#F3F3F3",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "texture": "paper_a",
        "ray_intensity": 0.44
      },
      "L1_Environment": {
        "grid_mode": "editorial_dots",
        "parallax_depth": 1.56,
        "accent_color": "#191A23",
        "highlight_color": "#B9FF66"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "card_variant": "lime",
        "pose_mode": "macro_pulse",
        "card_title": "PAY PER CLICK",
        "metric_value": 99.4,
        "metric_unit": "%",
        "metric_label": "SEARCH ENGINE IMPACT",
        "stiffness": 220.0,
        "damping": 18.0,
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 2,
        "cursor_active": true,
        "floating_badges": [
          "SEARCH",
          "03 // ENGINE"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "PAY PER CLICK",
        "sub_caption": "pay per click campaigns.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "03 \u2022 LANDSCAPE"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.18,
        "vignette": 0.06,
        "chromatic_aberration": 0.001,
        "beat_flash": false
      }
    }
  },
  {
    "id": "S4",
    "index": 3,
    "in_sec": 5.8,
    "out_sec": 8.0,
    "in_frame": 348,
    "out_frame": 480,
    "shot_size": "MEDIUM",
    "subject": "hero_primary_angle_4",
    "camera_move": "whip_pan",
    "primary_curve": "backOut",
    "spoken_line": "social media marketing.",
    "sfx_trigger": {
      "type": "bass_sub_drop",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "theme_mode": "light",
        "palette_bg": "#FFFFFF",
        "palette_secondary": "#F3F3F3",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "texture": "paper_a",
        "ray_intensity": 0.28
      },
      "L1_Environment": {
        "grid_mode": "editorial_dots",
        "parallax_depth": 1.84,
        "accent_color": "#191A23",
        "highlight_color": "#B9FF66"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "card_variant": "white",
        "pose_mode": "action_turn",
        "card_title": "SOCIAL MEDIA MARKETING",
        "metric_value": 50.0,
        "metric_unit": "+",
        "metric_label": "OPTIMIZATION PAY IMPACT",
        "stiffness": 220.0,
        "damping": 18.0,
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 3,
        "cursor_active": true,
        "floating_badges": [
          "OPTIMIZATION",
          "04 // PAY"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "SOCIAL MEDIA MARKETING",
        "sub_caption": "social media marketing.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "04 \u2022 SUCCESS"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.18,
        "vignette": 0.06,
        "chromatic_aberration": 0.001,
        "beat_flash": true
      }
    }
  },
  {
    "id": "S5",
    "index": 4,
    "in_sec": 8.0,
    "out_sec": 10.0,
    "in_frame": 480,
    "out_frame": 600,
    "shot_size": "OTS",
    "subject": "hero_primary_angle_5",
    "camera_move": "dutch_tilt",
    "primary_curve": "easeInOut",
    "spoken_line": "240% organic traffic growth.",
    "sfx_trigger": {
      "type": "tada",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "theme_mode": "light",
        "palette_bg": "#FFFFFF",
        "palette_secondary": "#F3F3F3",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "texture": "paper_a",
        "ray_intensity": 0.36
      },
      "L1_Environment": {
        "grid_mode": "editorial_dots",
        "parallax_depth": 2.12,
        "accent_color": "#191A23",
        "highlight_color": "#B9FF66"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "card_variant": "dark",
        "pose_mode": "hero_lock",
        "card_title": "NAVIGATING DIGITAL // NEXT LEVEL",
        "metric_value": 100.0,
        "metric_unit": "%",
        "metric_label": "PER CLICK IMPACT",
        "stiffness": 220.0,
        "damping": 18.0,
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 4,
        "cursor_active": false,
        "floating_badges": [
          "PER",
          "05 // CLICK"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "NAVIGATING DIGITAL // NEXT LEVEL",
        "sub_caption": "240% organic traffic growth.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "05 \u2022 SEARCH"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.18,
        "vignette": 0.06,
        "chromatic_aberration": 0.001,
        "beat_flash": false
      }
    }
  }
];

/**
 * Audio energy lookup at film time t (seconds) for reactive character lip-sync & UI telemetry
 */
export function audioEnergyAt(t) {
  if (!ENERGY_ENVELOPE.length) return 0.25;
  const idx = clamp(Math.floor(t * 20), 0, ENERGY_ENVELOPE.length - 1);
  return ENERGY_ENVELOPE[idx] || 0.22;
}

/**
 * Compute dynamic 6-Layer state for shot at global time tGlobal and shot-local time tLocal
 */
export function evaluateStoryLayers(shotSpec, tGlobal, tLocal) {
  const shotDur = Math.max(0.1, shotSpec.out_sec - shotSpec.in_sec);
  const u = clamp(tLocal / shotDur);
  const baseLayers = shotSpec.layers || {};
  const curveVal = evaluateCurve(
    shotSpec.primary_curve || 'backOut',
    u,
    tLocal,
    baseLayers.L2_HeroSubject?.stiffness || 210,
    baseLayers.L2_HeroSubject?.damping || 18
  );

  return {
    L0_Backdrop: {
      ...baseLayers.L0_Backdrop,
      accent_color: PALETTE.accent_primary,
      ray_intensity: (baseLayers.L0_Backdrop?.ray_intensity ?? 0.42) * (0.85 + 0.25 * Math.sin(tGlobal * 1.8)),
    },
    L1_Environment: {
      ...baseLayers.L1_Environment,
      parallax_depth: (baseLayers.L1_Environment?.parallax_depth ?? 1.15) * (0.95 + 0.08 * curveVal),
    },
    L2_HeroSubject: {
      ...baseLayers.L2_HeroSubject,
      curve_progress: curveVal,
    },
    L3_MotionProps: {
      ...baseLayers.L3_MotionProps,
      orb_boost: tGlobal >= DROP_SEC ? 1.25 : 1.0,
    },
    L4_TypographyHUD: {
      ...baseLayers.L4_TypographyHUD,
    },
    L5_PostFX: {
      ...baseLayers.L5_PostFX,
      beat_flash: Boolean(baseLayers.L5_PostFX?.beat_flash) || Math.abs(tGlobal - DROP_SEC) < 0.14,
    },
  };
}
