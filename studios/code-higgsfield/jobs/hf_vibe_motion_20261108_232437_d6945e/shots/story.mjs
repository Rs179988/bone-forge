// Auto-generated & Agent-Editable Story Timeline (story.mjs)
// Job ID: hf_vibe_motion_20261108_232437_d6945e | Genre: editorial_motion
// Pure functions of time t (seconds) using Higgsfield pre-built curve primitives.

import { clamp, lerp, smooth, easeIn, easeOut, easeInOut, backOut, ring, springDamper, keys, evaluateCurve } from '/backend/engine/core/curves.mjs';

export const JOB_ID = "hf_vibe_motion_20261108_232437_d6945e";
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
export const ENERGY_ENVELOPE = [0.279, 0.324, 0.299, 0.116, 0.152, 0.174, 0.227, 0.566, 0.455, 0.436, 0.425, 0.373, 0.245, 0.101, 0.293, 0.335, 0.282, 0.165, 0.394, 0.279, 0.348, 0.415, 0.355, 0.275, 0.131, 0.241, 0.286, 0.245, 0.181, 0.208, 0.334, 0.274, 0.349, 0.191, 0.093, 0.06, 0.132, 0.132, 0.224, 0.067, 0.342, 0.479, 0.233, 0.371, 0.411, 0.257, 0.131, 0.5, 0.412, 0.066, 0.436, 0.384, 0.465, 0.3, 0.225, 0.087, 0.13, 0.186, 0.236, 0.306, 0.419, 0.48, 0.378, 0.113, 0.146, 0.12, 0.179, 0.176, 0.131, 0.047, 0.4, 0.601, 0.245, 0.179, 0.135, 0.091, 0.135, 0.133, 0.132, 0.047, 0.411, 0.614, 0.386, 0.119, 0.356, 0.51, 0.265, 0.14, 0.264, 0.332, 0.438, 0.443, 0.337, 0.289, 0.229, 0.113, 0.13, 0.331, 0.314, 0.29, 0.341, 0.524, 0.369, 0.268, 0.298, 0.306, 0.297, 0.172, 0.121, 0.058, 0.298, 0.348, 0.392, 0.352, 0.398, 0.088, 0.125, 0.124, 0.501, 0.414, 0.38, 0.812, 0.293, 0.32, 0.352, 0.478, 0.447, 0.223, 0.258, 0.131, 0.19, 0.643, 0.434, 0.218, 0.122, 0.078, 0.325, 0.385, 0.338, 0.304, 0.211, 0.362, 0.3, 0.131, 0.128, 0.17, 0.294, 0.369, 0.32, 0.148, 0.2, 0.487, 0.311, 0.206, 0.207, 0.266, 0.33, 0.12, 0.117, 0.053, 0.578, 0.485, 0.422, 0.208, 0.236, 0.25, 0.269, 0.555, 0.196, 0.211, 0.629, 0.521, 0.377, 0.104, 0.233, 0.445, 0.498, 0.407, 0.153, 0.161, 0.478, 0.527, 0.422, 0.414, 0.499, 0.361, 0.115, 0.212, 0.214, 0.055, 0.391, 0.432, 0.444, 0.372, 0.101, 0.065, 0.335, 0.314, 0.139, 0.04];
export const DROP_SEC = 6.0212;

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
    "spoken_line": "Here is how Launching Matcha Craft transforms the entire landscape.",
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
        "card_title": "LAUNCHING MATCHA CRAFT COLD",
        "metric_value": 320.0,
        "metric_unit": "%",
        "metric_label": "LAUNCHING MATCHA IMPACT",
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
          "LAUNCHING",
          "01 // MATCHA"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "LAUNCHING MATCHA CRAFT COLD",
        "sub_caption": "Here is how Launching Matcha Craft transforms the entire landscape.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "01 \u2022 LAUNCHING"
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
    "spoken_line": "We focus on craft and cold with clean, unmistakable clarity.",
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
        "card_title": "320% MORNING ENERGY",
        "metric_value": 240.0,
        "metric_unit": "%",
        "metric_label": "CRAFT COLD IMPACT",
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
          "CRAFT",
          "02 // COLD"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "320% MORNING ENERGY",
        "sub_caption": "We focus on craft and cold with clean, unmistakable clarity.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "02 \u2022 MATCHA"
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
    "spoken_line": "Every detail of craft is built for real measurable growth.",
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
        "card_title": "ZERO SUGAR",
        "metric_value": 99.4,
        "metric_unit": "%",
        "metric_label": "BREW 320% IMPACT",
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
          "BREW",
          "03 // 320%"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "ZERO SUGAR",
        "sub_caption": "Every detail of craft is built for real measurable growth.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "03 \u2022 CRAFT"
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
    "spoken_line": "Watch how fast Launching Matcha Craft scales from concept to execution.",
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
        "card_title": "ORGANIC KYOTO LEAVES",
        "metric_value": 50.0,
        "metric_unit": "+",
        "metric_label": "MORNING ENERGY IMPACT",
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
          "MORNING",
          "04 // ENERGY"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "ORGANIC KYOTO LEAVES",
        "sub_caption": "Watch how fast Launching Matcha Craft scales from concept to execution.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "04 \u2022 COLD"
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
    "spoken_line": "Let's make Launching Matcha Craft happen today with zero compromise.",
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
        "card_title": "LAUNCHING MATCHA // NEXT LEVEL",
        "metric_value": 100.0,
        "metric_unit": "%",
        "metric_label": "BOOST ZERO IMPACT",
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
          "BOOST",
          "05 // ZERO"
        ],
        "accent_color": "#B9FF66",
        "ink_color": "#191A23"
      },
      "L4_TypographyHUD": {
        "headline": "LAUNCHING MATCHA // NEXT LEVEL",
        "sub_caption": "Let's make Launching Matcha Craft happen today with zero compromise.",
        "safe_margin_pct": 0.08,
        "theme_mode": "light",
        "text_color": "#191A23",
        "accent_color": "#B9FF66",
        "ink_color": "#191A23",
        "badge_tag": "05 \u2022 BREW"
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
