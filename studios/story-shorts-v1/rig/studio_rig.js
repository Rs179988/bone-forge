// Deterministic 60fps Spring Solver & Camera Choreography Rig
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

  // Camera shake & subtle organic handheld drift so ZERO frames are ever dead-static
  function computeCameraTransform(frame, beatStart, beatEnd, mode = "punch_in") {
    const localF = frame - beatStart;
    const dur = Math.max(1, beatEnd - beatStart);
    const progress = clamp(localF / dur, 0, 1);

    // Continuous subtle organic breathing (prevents static dead frames)
    const driftX = Math.sin(frame * 0.055) * 4.5 + Math.cos(frame * 0.028) * 2.5;
    const driftY = Math.cos(frame * 0.048) * 5.0 + Math.sin(frame * 0.031) * 2.5;
    const driftRot = Math.sin(frame * 0.035) * 0.28;

    // Entry impact punch on beat boundary
    const entrySpring = spring(frame, beatStart, { stiffness: 260, damping: 16, mass: 0.9 });
    let scale = 1.0 + progress * 0.045;
    let tx = driftX;
    let ty = driftY;
    let rot = driftRot;

    if (mode === "punch_in") {
      scale = (0.91 + 0.09 * entrySpring) + progress * 0.04;
    } else if (mode === "tilt_left") {
      scale = (0.94 + 0.06 * entrySpring) + progress * 0.035;
      rot = driftRot - 1.15 * (1 - progress * 0.5);
    } else if (mode === "zoom_node") {
      scale = (0.88 + 0.12 * entrySpring) + easeInOutCubic(progress) * 0.06;
    } else if (mode === "payoff_lock") {
      scale = (0.92 + 0.08 * entrySpring) + progress * 0.03;
    }

    // Whip-bridge transition in the final 10 frames of a beat
    const framesLeft = beatEnd - frame;
    let bridgeBlur = 0;
    if (framesLeft <= 8 && framesLeft >= 0) {
      const whip = easeInOutCubic((8 - framesLeft) / 8);
      scale += whip * 0.14;
      bridgeBlur = whip * 6;
    } else if (localF <= 6 && beatStart > 0) {
      const whipIn = 1 - easeOutExpo(localF / 6);
      scale -= whipIn * 0.10;
      bridgeBlur = whipIn * 5;
    }

    return {
      transform: `translate3d(${tx.toFixed(2)}px, ${ty.toFixed(2)}px, 0) scale(${scale.toFixed(4)}) rotate(${rot.toFixed(3)}deg)`,
      filter: bridgeBlur > 0.2 ? `blur(${bridgeBlur.toFixed(2)}px)` : "none"
    };
  }

  return { spring, easeOutExpo, easeInOutCubic, interpolate, computeCameraTransform, clamp };
})();
