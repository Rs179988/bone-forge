// Auto-generated & Agent-Editable Film Shot List & Stateless Scene Factory (film.mjs)
// Job ID: hf_flagship_demo_v1
// Stateless contract: sceneFor(frameIndex) returns the exact scene descriptor for any frame i in isolation.

import { CameraRig } from '/backend/engine/core/camera.mjs';
import { SHOT_SPECS, evaluateStoryLayers, audioEnergyAt } from './story.mjs';

export const FPS = 60;
export const FRAMES = 600;
export const WIDTH = 1080;
export const HEIGHT = 1920;

export const SHOTS = SHOT_SPECS;

export function shotFor(frameIndex) {
  const t = frameIndex / FPS;
  for (let i = 0; i < SHOTS.length; i++) {
    const s = SHOTS[i];
    if (t >= s.in_sec - 1e-6 && t < s.out_sec - 1e-6) return s;
  }
  return SHOTS[SHOTS.length - 1];
}

/**
 * Pure stateless scene factory for frame i (0 <= i < FRAMES)
 */
export function sceneFor(frameIndex, opts = {}) {
  const W = opts.width || WIDTH;
  const H = opts.height || HEIGHT;
  const tGlobal = frameIndex / FPS;
  const shot = shotFor(frameIndex);
  const tLocal = Math.max(0, tGlobal - shot.in_sec);
  const shotDur = Math.max(0.1, shot.out_sec - shot.in_sec);

  const cam = CameraRig.evaluate({
    move: shot.camera_move || 'dolly_in',
    shotSize: shot.shot_size || 'MEDIUM',
    tLocal,
    shotDur,
    seed: (shot.index || 0) * 17 + 1,
    shakeIntensity: 0.55,
  });

  const layers = evaluateStoryLayers(shot, tGlobal, tLocal);
  const audioAmp = audioEnergyAt(tGlobal);

  return {
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
  };
}
