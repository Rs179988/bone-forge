// Auto-generated & Agent-Editable Story Timeline (story.mjs)
// Job ID: hf_flagship_demo_v1 | Genre: vibe_motion_tech
// Pure functions of time t (seconds) using Higgsfield pre-built curve primitives.

import { clamp, lerp, smooth, easeIn, easeOut, easeInOut, backOut, ring, springDamper, keys, evaluateCurve } from '/backend/engine/core/curves.mjs';

export const JOB_ID = "hf_flagship_demo_v1";
export const PALETTE = {
  "name": "Higgsfield Obsidian & Acid Lime",
  "bg_primary": "#09090B",
  "bg_secondary": "#121318",
  "accent_primary": "#D4FF00",
  "accent_secondary": "#00F5D4",
  "alert_color": "#FF3366",
  "text_primary": "#F8FAFC",
  "text_muted": "#94A3B8",
  "surface_glass": "rgba(24, 26, 34, 0.78)",
  "texture": "brushed_metal"
};
export const ENERGY_ENVELOPE = [0.356, 0.414, 0.329, 0.148, 0.354, 0.233, 0.377, 0.253, 0.369, 0.147, 0.539, 0.349, 0.432, 0.129, 0.333, 0.142, 0.364, 0.201, 0.328, 0.166, 0.314, 0.497, 0.394, 0.325, 0.27, 0.256, 0.275, 0.331, 0.269, 0.283, 0.42, 0.263, 0.391, 0.251, 0.095, 0.077, 0.169, 0.168, 0.26, 0.117, 0.382, 0.501, 0.273, 0.32, 0.273, 0.202, 0.325, 0.276, 0.244, 0.314, 0.351, 0.524, 0.408, 0.255, 0.321, 0.238, 0.196, 0.349, 0.212, 0.195, 0.423, 0.502, 0.449, 0.317, 0.176, 0.321, 0.305, 0.214, 0.342, 0.245, 0.457, 0.619, 0.29, 0.146, 0.127, 0.083, 0.165, 0.163, 0.162, 0.058, 0.428, 0.578, 0.42, 0.285, 0.241, 0.314, 0.213, 0.275, 0.235, 0.141, 0.346, 0.609, 0.408, 0.315, 0.184, 0.286, 0.23, 0.233, 0.311, 0.134, 0.426, 0.59, 0.336, 0.394, 0.153, 0.244, 0.245, 0.177, 0.297, 0.201, 0.311, 0.426, 0.51, 0.344, 0.165, 0.109, 0.155, 0.154, 0.497, 0.413, 0.387, 0.694, 0.277, 0.444, 0.278, 0.277, 0.318, 0.28, 0.34, 0.189, 0.366, 0.659, 0.455, 0.27, 0.305, 0.169, 0.302, 0.174, 0.312, 0.177, 0.339, 0.398, 0.415, 0.228, 0.315, 0.154, 0.265, 0.146, 0.296, 0.164, 0.297, 0.504, 0.362, 0.191, 0.154, 0.088, 0.154, 0.154, 0.148, 0.066, 0.723, 0.605, 0.449, 0.222, 0.356, 0.255, 0.353, 0.291, 0.326, 0.237, 0.545, 0.494, 0.408, 0.298, 0.175, 0.3, 0.158, 0.277, 0.225, 0.251, 0.593, 0.593, 0.451, 0.27, 0.319, 0.131, 0.225, 0.18, 0.221, 0.235, 0.503, 0.412, 0.406, 0.362, 0.131, 0.113, 0.154, 0.153, 0.151, 0.05];
export const DROP_SEC = 8.0179;

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
    "spoken_line": "Look closely at Quantum. Every frame is engineered with zero latency.",
    "sfx_trigger": {
      "type": "whoosh",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "palette_bg": "#09090B",
        "palette_secondary": "#121318",
        "texture": "brushed_metal",
        "ray_intensity": 0.35
      },
      "L1_Environment": {
        "grid_mode": "perspective_vault",
        "parallax_depth": 1.0,
        "accent_color": "#00F5D4"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "pose_mode": "establish_rise",
        "metric_value": 128.4,
        "metric_unit": "MS",
        "stiffness": 220.0,
        "damping": 17.0,
        "accent_color": "#D4FF00"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 0,
        "cursor_active": false,
        "floating_badges": [
          "QUANTUM",
          "SHOT 01 // WIDE"
        ]
      },
      "L4_TypographyHUD": {
        "headline": "QUANTUM // ZERO SLOP",
        "sub_caption": "Look closely at Quantum. Every frame is engineered with zero latency.",
        "safe_margin_pct": 0.08,
        "text_color": "#F8FAFC",
        "accent_color": "#D4FF00",
        "badge_tag": "S1 \u2022 WIDE \u2022 DOLLY_IN"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.42,
        "vignette": 0.22,
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
    "spoken_line": "Inside the middle layer, deterministic curves lock motion to the exact millisecond.",
    "sfx_trigger": {
      "type": "ui_pop",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "palette_bg": "#09090B",
        "palette_secondary": "#121318",
        "texture": "brushed_metal",
        "ray_intensity": 0.47
      },
      "L1_Environment": {
        "grid_mode": "radial_matrix",
        "parallax_depth": 1.35,
        "accent_color": "#00F5D4"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "character_rig",
        "pose_mode": "close_inspect",
        "metric_value": 492.0,
        "metric_unit": "FPS",
        "stiffness": 310.0,
        "damping": 14.0,
        "accent_color": "#00FF66"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 1,
        "cursor_active": true,
        "floating_badges": [
          "FINTECH",
          "SHOT 02 // CU"
        ]
      },
      "L4_TypographyHUD": {
        "headline": "SPRING LOCKED: 220 N/m",
        "sub_caption": "Inside the middle layer, deterministic curves lock motion to the exact millisecond.",
        "safe_margin_pct": 0.08,
        "text_color": "#F8FAFC",
        "accent_color": "#00FF66",
        "badge_tag": "S2 \u2022 CU \u2022 ORBITAL_ARC"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.42,
        "vignette": 0.22,
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
    "spoken_line": "Watch the real-time telemetry spike past ninety-nine point eight percent precision.",
    "sfx_trigger": {
      "type": "mechanical_click",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "palette_bg": "#09090B",
        "palette_secondary": "#121318",
        "texture": "brushed_metal",
        "ray_intensity": 0.59
      },
      "L1_Environment": {
        "grid_mode": "perspective_vault",
        "parallax_depth": 1.7,
        "accent_color": "#00F5D4"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "pose_mode": "macro_pulse",
        "metric_value": 99.8,
        "metric_unit": "%",
        "stiffness": 220.0,
        "damping": 17.0,
        "accent_color": "#00F5D4"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 2,
        "cursor_active": true,
        "floating_badges": [
          "CYBER-DIRECTOR",
          "SHOT 03 // DETAIL"
        ]
      },
      "L4_TypographyHUD": {
        "headline": "99.8% FRAME ACCURACY",
        "sub_caption": "Watch the real-time telemetry spike past ninety-nine point eight percent precision.",
        "safe_margin_pct": 0.08,
        "text_color": "#F8FAFC",
        "accent_color": "#D4FF00",
        "badge_tag": "S3 \u2022 DETAIL \u2022 MACRO_RACK_FOCUS"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.42,
        "vignette": 0.22,
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
    "spoken_line": "Click any isolated layer to patch physics, lighting, or typography on the fly.",
    "sfx_trigger": {
      "type": "bass_sub_drop",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "palette_bg": "#09090B",
        "palette_secondary": "#121318",
        "texture": "brushed_metal",
        "ray_intensity": 0.35
      },
      "L1_Environment": {
        "grid_mode": "radial_matrix",
        "parallax_depth": 2.05,
        "accent_color": "#00F5D4"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "pose_mode": "action_turn",
        "metric_value": 1024.0,
        "metric_unit": "OPS",
        "stiffness": 220.0,
        "damping": 17.0,
        "accent_color": "#D4FF00"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 3,
        "cursor_active": true,
        "floating_badges": [
          "STUDIO",
          "SHOT 04 // MEDIUM"
        ]
      },
      "L4_TypographyHUD": {
        "headline": "6-LAYER SURGICAL AST",
        "sub_caption": "Click any isolated layer to patch physics, lighting, or typography on the fly.",
        "safe_margin_pct": 0.08,
        "text_color": "#F8FAFC",
        "accent_color": "#D4FF00",
        "badge_tag": "S4 \u2022 MEDIUM \u2022 WHIP_PAN"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.58,
        "vignette": 0.22,
        "chromatic_aberration": 0.0025,
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
    "spoken_line": "Code Higgsfield Studio. Pure procedural cinema at sixty frames per second.",
    "sfx_trigger": {
      "type": "tada",
      "offset_sec": 0.08
    },
    "layers": {
      "L0_Backdrop": {
        "palette_bg": "#09090B",
        "palette_secondary": "#121318",
        "texture": "brushed_metal",
        "ray_intensity": 0.47
      },
      "L1_Environment": {
        "grid_mode": "perspective_vault",
        "parallax_depth": 2.4,
        "accent_color": "#00F5D4"
      },
      "L2_HeroSubject": {
        "cast_id": "hero_primary",
        "kind": "saas_3d_card",
        "pose_mode": "hero_lock",
        "metric_value": 60.0,
        "metric_unit": "FPS",
        "stiffness": 220.0,
        "damping": 17.0,
        "accent_color": "#D4FF00"
      },
      "L3_MotionProps": {
        "through_line_id": "telemetry_orb",
        "through_line_state": 4,
        "cursor_active": false,
        "floating_badges": [
          "ENGINE",
          "SHOT 05 // OTS"
        ]
      },
      "L4_TypographyHUD": {
        "headline": "CODE-HIGGSFIELD // 9:16",
        "sub_caption": "Code Higgsfield Studio. Pure procedural cinema at sixty frames per second.",
        "safe_margin_pct": 0.08,
        "text_color": "#F8FAFC",
        "accent_color": "#D4FF00",
        "badge_tag": "S5 \u2022 OTS \u2022 DUTCH_TILT"
      },
      "L5_PostFX": {
        "bloom_intensity": 0.42,
        "vignette": 0.22,
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
