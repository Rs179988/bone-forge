/**
 * Layer 2B: Pre-Built Cinematography & Camera Rig Engine
 * Supports: dolly_in, whip_pan, orbital_arc, dutch_tilt, handheld_shake, macro_rack_focus,
 * and depth-of-field blur radius calculation per Z-plane.
 */

import { clamp, lerp, smooth, easeInOut, backOut, ring } from './curves.mjs';

export function handheldShake(t, intensity = 1.0, seed = 1) {
  const f1 = 2.1, f2 = 3.7, f3 = 5.3;
  const dx =
    intensity *
    (6.0 * Math.sin(t * f1 * 6.28 + seed) + 2.5 * Math.cos(t * f2 * 6.28 + seed * 1.7));
  const dy =
    intensity *
    (5.0 * Math.cos(t * f1 * 5.1 + seed * 2.3) + 2.2 * Math.sin(t * f3 * 6.28 + seed * 3.1));
  const rotDeg = intensity * 0.45 * Math.sin(t * 2.8 * 6.28 + seed * 0.9);
  return { dx, dy, rotDeg };
}

export class CameraRig {
  static evaluate({
    move = 'dolly_in',
    shotSize = 'MEDIUM',
    tLocal = 0,
    shotDur = 2.0,
    seed = 1,
    shakeIntensity = 0.65,
  }) {
    const u = clamp(tLocal / Math.max(0.01, shotDur));
    const shake = handheldShake(tLocal, shakeIntensity, seed);

    // Base scale by shot framing size (calibrated to keep hero subject strictly inside safe margins)
    const baseScaleMap = {
      TOP: 0.88,
      WIDE: 0.92,
      OTS: 0.98,
      MEDIUM: 1.02,
      CU: 1.08,
      DETAIL: 1.14,
      MACRO: 1.18,
      ECU: 1.22,
    };
    const baseScale = baseScaleMap[shotSize] || 1.0;

    let zoom = baseScale;
    let panX = 0;
    let panY = 0;
    let tiltDeg = 0;
    let focusZ = 0; // Hero subject sits at Z = 0
    let apertureDof = 1.0;

    switch (move) {
      case 'dolly_in': {
        const k = easeInOut(u);
        zoom = baseScale * lerp(0.95, 1.12, k);
        panY = lerp(18, -10, k);
        apertureDof = 1.2;
        break;
      }
      case 'whip_pan': {
        // Fast entry whip settle + subtle drift
        const entry = backOut(clamp(tLocal / 0.38), 2.1);
        panX = lerp(-180, 0, entry) + lerp(0, 16, u);
        tiltDeg = ring(tLocal, 0.05, 3.2, 20, 6);
        zoom = baseScale * (0.98 + 0.06 * smooth(u));
        apertureDof = 1.5;
        break;
      }
      case 'orbital_arc': {
        const k = smooth(u);
        panX = lerp(-42, 42, k);
        panY = -14 * Math.sin(k * Math.PI);
        tiltDeg = lerp(-1.8, 1.8, k);
        zoom = baseScale * (1.0 + 0.07 * Math.sin(k * Math.PI));
        apertureDof = 1.4;
        break;
      }
      case 'dutch_tilt': {
        const k = backOut(clamp(tLocal / 0.45), 1.8);
        tiltDeg = lerp(0, -4.2, k) + 1.2 * Math.sin(u * Math.PI);
        zoom = baseScale * lerp(0.96, 1.1, smooth(u));
        apertureDof = 1.3;
        break;
      }
      case 'macro_rack_focus': {
        const rack = smooth(clamp(tLocal / 0.55));
        focusZ = lerp(-3.5, 0.0, rack);
        zoom = baseScale * lerp(1.04, 1.18, easeInOut(u));
        panX = lerp(24, -12, easeInOut(u));
        apertureDof = 2.6;
        break;
      }
      default: {
        zoom = baseScale * lerp(0.98, 1.06, smooth(u));
        break;
      }
    }

    return {
      zoom,
      panX: panX + shake.dx,
      panY: panY + shake.dy,
      tiltDeg: tiltDeg + shake.rotDeg,
      focusZ,
      apertureDof,
      shotSize,
      move,
      u,
    };
  }

  /**
   * Compute depth-of-field blur in px for a layer at depth Z (Hero is Z=0, Backdrop Z=-8, Foreground Z=+3)
   */
  static dofBlurPx(layerZ, camState) {
    const dist = Math.abs(layerZ - (camState.focusZ || 0));
    if (dist < 0.5) return 0;
    return Math.min(14, dist * 0.85 * (camState.apertureDof || 1.0));
  }
}
