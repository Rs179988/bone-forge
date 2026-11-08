/**
 * Layer 2A: Pre-Built Procedural Motion Curves & Spring Physics Engine
 * Ported & extended from higgsfield-ai/higgsfield-video-engineer (skills/code-based-films/shots/story.mjs)
 */

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (x) => {
  x = clamp(x);
  return x * x * (3 - 2 * x);
};
export const smoother = (x) => {
  x = clamp(x);
  return x * x * x * (x * (x * 6 - 15) + 10);
};
export const easeOut = (x) => 1 - (1 - clamp(x)) ** 3;
export const easeIn = (x) => clamp(x) ** 3;
export const easeInOut = (x) => {
  x = clamp(x);
  return x < 0.5 ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2;
};

/**
 * Overshoot settle: 0 -> 1 with a springy overshoot (Higgsfield standard k=1.9)
 */
export const backOut = (x, k = 1.9) => {
  x = clamp(x);
  const c3 = k + 1;
  return 1 + c3 * (x - 1) ** 3 + k * (x - 1) ** 2;
};

/**
 * Damped oscillation after t0: amp * e^(-d * (t - t0)) * sin(w * (t - t0))
 */
export const ring = (t, t0, amp = 0.15, w = 22, d = 6) =>
  t < t0 ? 0 : amp * Math.exp(-d * (t - t0)) * Math.sin(w * (t - t0));

/**
 * Analytical Under-Damped Harmonic Oscillator (Spring-Damper response 0 -> 1)
 * stiffness (N/m): 120..350, damping: 10..30
 */
export function springDamper(t, stiffness = 210, damping = 18) {
  if (t <= 0) return 0;
  const wn = Math.sqrt(Math.max(10, stiffness));
  const zeta = damping / (2 * wn);
  if (zeta < 1) {
    const wd = wn * Math.sqrt(1 - zeta * zeta);
    const env = Math.exp(-zeta * wn * t);
    return 1 - env * (Math.cos(wd * t) + (zeta / Math.sqrt(1 - zeta * zeta)) * Math.sin(wd * t));
  }
  return 1 - (1 + wn * t) * Math.exp(-wn * t);
}

/**
 * Piecewise keyframes [[t0, v0], [t1, v1, easeFn], ...]
 */
export function keys(t, K) {
  if (!K || !K.length) return 0;
  if (t <= K[0][0]) return K[0][1];
  for (let i = 1; i < K.length; i++) {
    if (t <= K[i][0]) {
      const [t0, v0] = K[i - 1];
      const [t1, v1, easeFn] = K[i];
      const span = Math.max(1e-6, t1 - t0);
      const u = (t - t0) / span;
      const fn = easeFn || smooth;
      return lerp(v0, v1, fn(u));
    }
  }
  return K[K.length - 1][1];
}

/**
 * Resolve named curve from string identifier
 */
export function evaluateCurve(name, u, tLocal = 0, stiffness = 210, damping = 18) {
  switch (name) {
    case 'backOut':
      return backOut(u, 1.95);
    case 'ring':
      return backOut(u, 1.7) + ring(tLocal, 0.18, 0.08, 24, 5.5);
    case 'springDamper':
      return springDamper(tLocal * 1.15, stiffness, damping);
    case 'easeIn':
      return easeIn(u);
    case 'easeOut':
      return easeOut(u);
    case 'easeInOut':
      return easeInOut(u);
    default:
      return smooth(u);
  }
}
