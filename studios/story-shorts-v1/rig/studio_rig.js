// Deterministic 60fps Spring Solver & 2D Canvas Living Camera Rig
window.StudioRig = (function() {
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

  // Exact analytical damped harmonic oscillator spring (0 -> 1)
  function spring(frame, startFrame, config = {}) {
    const f = frame - startFrame;
    if (f <= 0) return 0;
    const stiffness = config.stiffness || 220;
    const damping = config.damping || 18;
    const mass = config.mass || 1.0;
    const fps = config.fps || 60;
    const t = f / fps;

    const omega0 = Math.sqrt(stiffness / mass);
    const zeta = damping / (2 * Math.sqrt(stiffness * mass));

    if (zeta < 1) {
      const omegaD = omega0 * Math.sqrt(1 - zeta * zeta);
      const env = Math.exp(-zeta * omega0 * t);
      const val = 1 - env * (Math.cos(omegaD * t) + (zeta * omega0 / omegaD) * Math.sin(omegaD * t));
      return Math.abs(1 - val) < 0.0005 && t > 0.25 ? 1 : val;
    } else {
      const env = Math.exp(-omega0 * t);
      return 1 - env * (1 + omega0 * t);
    }
  }

  function easeOutExpo(x) {
    return x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(2, -10 * x);
  }

  function easeInOutCubic(x) {
    return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  }

  function interpolate(frame, inputRange, outputRange, easingFn = (x) => x) {
    const [inMin, inMax] = inputRange;
    const [outMin, outMax] = outputRange;
    const raw = clamp((frame - inMin) / Math.max(0.0001, inMax - inMin), 0, 1);
    const eased = easingFn(raw);
    return outMin + (outMax - outMin) * eased;
  }

  // Applies Living Camera directly onto a 1080x1920 2D Canvas Context:
  // - Subtle handheld breathing so zero frames are ever dead-static
  // - Dynamic push-in / pull-out / pan per scene
  // - Crisp whip-zoom transition on scene boundaries
  function applyCanvasCamera(ctx, frame, sceneStart, sceneEnd, mode = "push_in", focusX = 540, focusY = 960) {
    const localF = frame - sceneStart;
    const dur = Math.max(1, sceneEnd - sceneStart);
    const progress = clamp(localF / dur, 0, 1);

    const driftX = Math.sin(frame * 0.052) * 5.0 + Math.cos(frame * 0.027) * 3.0;
    const driftY = Math.cos(frame * 0.046) * 5.5 + Math.sin(frame * 0.033) * 3.0;
    const driftRot = Math.sin(frame * 0.032) * 0.0035;

    const entryS = spring(frame, sceneStart, { stiffness: 240, damping: 17 });
    let scale = 1.0;
    let panX = 0;
    let panY = 0;
    let rot = driftRot;

    if (mode === "push_in") {
      scale = (0.94 + 0.06 * entryS) + progress * 0.065;
    } else if (mode === "snap_zoom") {
      scale = (0.88 + 0.12 * entryS) + easeInOutCubic(progress) * 0.08;
    } else if (mode === "pan_up") {
      scale = (0.96 + 0.04 * entryS) + progress * 0.04;
      panY = (1 - easeOutExpo(clamp(localF / 35, 0, 1))) * 70 - progress * 24;
    } else if (mode === "tilt_focus") {
      scale = (0.95 + 0.05 * entryS) + progress * 0.05;
      rot = driftRot - 0.012 * (1 - progress);
    }

    // Subtle whip-push in final 6 frames of a scene
    const rem = sceneEnd - frame;
    if (rem <= 6 && rem >= 0) {
      const w = easeInOutCubic((6 - rem) / 6);
      scale += w * 0.09;
    }

    ctx.translate(540 + driftX + panX, 960 + driftY + panY);
    ctx.rotate(rot);
    ctx.scale(scale, scale);
    ctx.translate(-focusX, -focusY);
  }

  return { spring, easeOutExpo, easeInOutCubic, interpolate, applyCanvasCamera, clamp };
})();
