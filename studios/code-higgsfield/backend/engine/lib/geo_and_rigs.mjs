/**
 * Layer 2C: Pre-Built Procedural Component Kit, 3D UI Cards & 2.5D Character Rigs
 * Implements the 6 Isolated Studio Layers:
 *   L0_Backdrop, L1_Environment, L2_HeroSubject, L3_MotionProps, L4_TypographyHUD, L5_PostFX
 */

import { clamp, lerp, smooth, easeOut, easeInOut, backOut, ring, springDamper, evaluateCurve } from '../core/curves.mjs';
import { CameraRig } from '../core/camera.mjs';

function hexToRgba(hex, alpha = 1.0) {
  if (!hex || typeof hex !== 'string') return `rgba(212, 255, 0, ${alpha})`;
  if (hex.startsWith('rgba') || hex.startsWith('rgb')) return hex;
  const clean = hex.replace('#', '');
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean;
  const num = parseInt(full, 16) || 0xd4ff00;
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function roundRectPath(ctx, x, y, w, h, r) {
  const rad = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rad, y);
  ctx.arcTo(x + w, y, x + w, y + h, rad);
  ctx.arcTo(x + w, y + h, x, y + h, rad);
  ctx.arcTo(x, y + h, x, y, rad);
  ctx.arcTo(x, y, x + w, y, rad);
  ctx.closePath();
}

/**
 * L0_Backdrop: Deep obsidian/studio atmosphere, volumetric god-rays & procedural surface grain
 */
export function renderL0Backdrop(ctx, W, H, layerProps = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  const bg1 = layerProps.palette_bg || '#09090B';
  const bg2 = layerProps.palette_secondary || '#121318';
  const accent = layerProps.accent_color || '#D4FF00';
  const rayIntensity = layerProps.ray_intensity ?? 0.42;

  const grad = ctx.createLinearGradient(0, 0, W * 0.35, H);
  grad.addColorStop(0, bg1);
  grad.addColorStop(0.55, bg2);
  grad.addColorStop(1, bg1);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // Volumetric atmospheric glow core
  const cx = W * (0.5 + 0.08 * Math.sin(tGlobal * 0.9));
  const cy = H * (0.42 + 0.05 * Math.cos(tGlobal * 0.7));
  const radGrad = ctx.createRadialGradient(cx, cy, W * 0.04, cx, cy, W * 0.85);
  radGrad.addColorStop(0, hexToRgba(accent, 0.22 * rayIntensity));
  radGrad.addColorStop(0.45, hexToRgba('#38BDF8', 0.09 * rayIntensity));
  radGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = radGrad;
  ctx.fillRect(0, 0, W, H);

  // Volumetric diagonal studio light shafts
  ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < 4; i++) {
    const beamX = W * (0.18 + i * 0.24) + Math.sin(tGlobal * 0.6 + i) * 35;
    const beamGrad = ctx.createLinearGradient(beamX - 90, 0, beamX + 140, H * 0.85);
    beamGrad.addColorStop(0, hexToRgba(accent, 0.07 * rayIntensity));
    beamGrad.addColorStop(0.6, hexToRgba('#FFFFFF', 0.02 * rayIntensity));
    beamGrad.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = beamGrad;
    ctx.beginPath();
    ctx.moveTo(beamX - 70, 0);
    ctx.lineTo(beamX + 70, 0);
    ctx.lineTo(beamX + 260, H);
    ctx.lineTo(beamX - 180, H);
    ctx.closePath();
    ctx.fill();
  }

  // Procedural micro-texture weave (felt / brushed-metal / paper lines)
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.024)';
  ctx.lineWidth = 1;
  const step = 24;
  const offset = (tGlobal * 18) % step;
  for (let y = offset; y < H; y += step) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  ctx.restore();
}

/**
 * L1_Environment: 3D Perspective Horizon Grid, Radial Telemetry Matrix & Depth Parallax Nodes
 */
export function renderL1Environment(ctx, W, H, layerProps = {}, cam = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  const accent = layerProps.accent_color || '#00F5D4';
  const gridMode = layerProps.grid_mode || 'perspective_vault';
  const depthScale = layerProps.parallax_depth || 1.15;

  const panX = (cam.panX || 0) * 0.45 * depthScale;
  const panY = (cam.panY || 0) * 0.45 * depthScale;
  ctx.translate(W / 2 + panX, H / 2 + panY);
  ctx.scale(cam.zoom ? 1 + (cam.zoom - 1) * 0.4 : 1, cam.zoom ? 1 + (cam.zoom - 1) * 0.4 : 1);
  ctx.translate(-W / 2, -H / 2);

  const horizonY = H * 0.56;

  if (gridMode === 'perspective_vault') {
    // Perspective floor & ceiling grid
    ctx.strokeStyle = hexToRgba(accent, 0.16);
    ctx.lineWidth = 1.5;
    const vanishX = W * 0.5;
    for (let i = -10; i <= 10; i++) {
      ctx.beginPath();
      ctx.moveTo(vanishX + i * 28, horizonY);
      ctx.lineTo(vanishX + i * 210, H * 1.05);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(vanishX + i * 28, horizonY - 120);
      ctx.lineTo(vanishX + i * 190, -H * 0.05);
      ctx.stroke();
    }

    // Moving depth Z-bars
    const zPhase = (tGlobal * 0.85) % 1;
    for (let j = 0; j < 9; j++) {
      const u = ((j + zPhase) / 9) ** 1.85;
      const y = lerp(horizonY, H * 0.98, u);
      ctx.strokeStyle = hexToRgba(accent, 0.06 + 0.22 * u);
      ctx.beginPath();
      ctx.moveTo(W * 0.04, y);
      ctx.lineTo(W * 0.96, y);
      ctx.stroke();
    }
  } else {
    // Radial sonar / orbital studio rings
    const cx = W * 0.5;
    const cy = H * 0.46;
    for (let r = 1; r <= 6; r++) {
      const radius = r * (Math.min(W, H) * 0.085) + 8 * Math.sin(tGlobal * 2 + r);
      ctx.strokeStyle = hexToRgba(accent, 0.22 - r * 0.025);
      ctx.lineWidth = r === 3 ? 2.2 : 1.2;
      ctx.setLineDash(r % 2 === 0 ? [10, 8] : []);
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.setLineDash([]);
  }

  // Parallax floating architectural nodes
  for (let k = 0; k < 14; k++) {
    const px = ((k * 197 + Math.sin(tGlobal * 0.8 + k) * 45) % (W * 0.88)) + W * 0.06;
    const py = ((k * 311 + tGlobal * 38 * (1 + (k % 3) * 0.3)) % (H * 0.78)) + H * 0.1;
    const sz = 2.5 + (k % 4) * 1.6;
    ctx.fillStyle = hexToRgba(accent, 0.28);
    ctx.beginPath();
    ctx.arc(px, py, sz, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
}

/**
 * L2_HeroSubject: Supports both High-Craft 3D SaaS/Fintech Cards AND Articulated 2.5D Character Rigs
 */
export function renderL2HeroSubject(ctx, W, H, layerProps = {}, cam = {}, tGlobal = 0, tLocal = 0, audioAmp = 0.2) {
  ctx.save();
  const kind = layerProps.kind || 'saas_3d_card';
  const accent = layerProps.accent_color || '#D4FF00';
  const stiffness = layerProps.stiffness || 210;
  const damping = layerProps.damping || 18;
  const entrySpring = clamp(springDamper(tLocal + 0.08, stiffness, damping), 0, 1.35);
  const settleRing = ring(tLocal, 0.12, 0.035, 22, 5.5);

  const cx = W * 0.5 + (cam.panX || 0);
  const cy = H * 0.45 + (cam.panY || 0);
  const scale = (cam.zoom || 1.0) * (0.82 + 0.18 * entrySpring + settleRing);

  ctx.translate(cx, cy);
  ctx.rotate(((cam.tiltDeg || 0) * Math.PI) / 180);
  ctx.scale(scale, scale);

  if (kind === 'character_rig') {
    _drawArticulatedCharacterRig(ctx, W, H, layerProps, tGlobal, tLocal, audioAmp, accent);
  } else {
    _drawSaaS3DHeroCard(ctx, W, H, layerProps, tGlobal, tLocal, entrySpring, accent);
  }

  ctx.restore();
}

function _drawSaaS3DHeroCard(ctx, W, H, props, tGlobal, tLocal, springVal, accent) {
  const cardW = Math.min(W * 0.78, 760);
  const cardH = Math.min(H * 0.36, 560);
  const x = -cardW / 2;
  const y = -cardH / 2;

  // Drop shadow + ambient neon aura
  ctx.shadowColor = hexToRgba(accent, 0.35);
  ctx.shadowBlur = 42;
  ctx.shadowOffsetY = 18;

  // Main glassmorphic chassis
  const bgGrad = ctx.createLinearGradient(x, y, x + cardW, y + cardH);
  bgGrad.addColorStop(0, 'rgba(18, 21, 30, 0.94)');
  bgGrad.addColorStop(0.6, 'rgba(11, 13, 20, 0.96)');
  bgGrad.addColorStop(1, 'rgba(22, 27, 38, 0.94)');
  ctx.fillStyle = bgGrad;
  roundRectPath(ctx, x, y, cardW, cardH, 28);
  ctx.fill();

  ctx.shadowBlur = 0;
  ctx.shadowOffsetY = 0;

  // Specular border highlight
  const borderGrad = ctx.createLinearGradient(x, y, x + cardW, y + cardH);
  borderGrad.addColorStop(0, hexToRgba(accent, 0.85));
  borderGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.18)');
  borderGrad.addColorStop(1, hexToRgba('#00F5D4', 0.65));
  ctx.strokeStyle = borderGrad;
  ctx.lineWidth = 2.8;
  roundRectPath(ctx, x, y, cardW, cardH, 28);
  ctx.stroke();

  // Top studio header bar inside card
  ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
  roundRectPath(ctx, x + 20, y + 20, cardW - 40, 54, 14);
  ctx.fill();

  // Traffic light dots + live status pill
  const dotColors = ['#FF3366', '#F59E0B', accent];
  for (let i = 0; i < 3; i++) {
    ctx.fillStyle = dotColors[i];
    ctx.beginPath();
    ctx.arc(x + 48 + i * 22, y + 47, 6.5, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.font = '700 18px "JetBrains Mono", monospace';
  ctx.fillStyle = accent;
  ctx.textAlign = 'right';
  ctx.fillText(`ENGINE // ${String(props.pose_mode || 'ACTIVE').toUpperCase()}`, x + cardW - 42, y + 53);

  // Animated Metric Odometer Counter
  const targetVal = Number(props.metric_value ?? 99.8);
  const unit = String(props.metric_unit || 'FPS');
  const animatedVal = (targetVal * clamp(backOut(clamp(tLocal / 0.65), 1.6), 0, 1.15)).toFixed(
    targetVal % 1 === 0 ? 0 : 1
  );

  ctx.textAlign = 'left';
  ctx.font = '800 76px "Inter", "Geist", sans-serif';
  ctx.fillStyle = '#FFFFFF';
  ctx.fillText(`${animatedVal}${unit}`, x + 38, y + 168);

  ctx.font = '600 20px "JetBrains Mono", monospace';
  ctx.fillStyle = '#94A3B8';
  ctx.fillText('DETERMINISTIC MIDDLEWARE THROUGHPUT', x + 40, y + 204);

  // Live Animated Telemetry Sparkline + Bars
  const chartX = x + 38;
  const chartY = y + 235;
  const chartW = cardW - 76;
  const chartH = cardH - 275;

  ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
  roundRectPath(ctx, chartX, chartY, chartW, chartH, 16);
  ctx.fill();

  // Animated frequency/telemetry bars
  const barCount = 18;
  const barGap = 8;
  const barW = (chartW - 32 - (barCount - 1) * barGap) / barCount;
  for (let b = 0; b < barCount; b++) {
    const wave = 0.35 + 0.6 * Math.abs(Math.sin(tGlobal * 3.8 + b * 0.45));
    const bh = Math.max(12, (chartH - 36) * wave * clamp(tLocal * 2.2, 0.2, 1));
    const bx = chartX + 16 + b * (barW + barGap);
    const by = chartY + chartH - 16 - bh;
    ctx.fillStyle = b % 4 === 0 ? accent : 'rgba(56, 189, 248, 0.55)';
    roundRectPath(ctx, bx, by, barW, bh, 5);
    ctx.fill();
  }

  // Smooth glowing spline curve over bars
  ctx.strokeStyle = accent;
  ctx.lineWidth = 4;
  ctx.beginPath();
  for (let s = 0; s <= 32; s++) {
    const u = s / 32;
    const px = chartX + 16 + u * (chartW - 32);
    const py =
      chartY +
      chartH * 0.55 -
      Math.sin(u * Math.PI * 2.5 + tGlobal * 4.2) * (chartH * 0.26) -
      u * (chartH * 0.15);
    if (s === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.stroke();
}

function _drawArticulatedCharacterRig(ctx, W, H, props, tGlobal, tLocal, audioAmp, accent) {
  // Multi-joint 2.5D Cyber-Director / Felt-Craft Character Rig with squash, stretch, blink, and lip-sync
  const breathe = 1 + 0.025 * Math.sin(tGlobal * 3.4);
  const hop = ring(tLocal, 0.05, 18, 20, 5);
  const squash = 1 + ring(tLocal, 0.05, 0.08, 22, 6);

  ctx.save();
  ctx.translate(0, -hop);
  ctx.scale(squash, (2 - squash) * breathe);

  // Rim light aura behind character
  const rimGrad = ctx.createRadialGradient(0, -40, 20, 0, -40, 280);
  rimGrad.addColorStop(0, hexToRgba(accent, 0.42));
  rimGrad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = rimGrad;
  ctx.beginPath();
  ctx.arc(0, -40, 280, 0, Math.PI * 2);
  ctx.fill();

  // Torso / Jacket chassis
  ctx.fillStyle = '#161925';
  ctx.strokeStyle = accent;
  ctx.lineWidth = 3.5;
  roundRectPath(ctx, -115, 20, 230, 210, 48);
  ctx.fill();
  ctx.stroke();

  // Chest core emblem
  ctx.fillStyle = hexToRgba(accent, 0.9);
  ctx.beginPath();
  ctx.arc(0, 105, 28 + 5 * Math.sin(tGlobal * 6), 0, Math.PI * 2);
  ctx.fill();

  // Articulated Left & Right Arms
  for (const dir of [-1, 1]) {
    ctx.save();
    ctx.translate(dir * 122, 55);
    const armAngle = dir * (0.25 + 0.18 * Math.sin(tGlobal * 4.2 + dir));
    ctx.rotate(armAngle);
    ctx.fillStyle = '#1E2436';
    ctx.strokeStyle = hexToRgba(accent, 0.7);
    ctx.lineWidth = 3;
    roundRectPath(ctx, -24, 0, 48, 135, 22);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  // Head with subtle tilt
  ctx.save();
  const headTilt = 0.08 * Math.sin(tGlobal * 2.7);
  ctx.translate(0, -85);
  ctx.rotate(headTilt);

  ctx.fillStyle = '#1E2330';
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 3.5;
  roundRectPath(ctx, -95, -95, 190, 175, 52);
  ctx.fill();
  ctx.stroke();

  // Visor / Eyes with deterministic blink every 2.8 seconds
  const blinkPhase = tGlobal % 2.8;
  const eyeOpen = blinkPhase > 2.66 ? 0.12 : 1.0;
  for (const ex of [-40, 40]) {
    ctx.fillStyle = accent;
    roundRectPath(ctx, ex - 20, -32, 40, Math.max(4, 26 * eyeOpen), 10);
    ctx.fill();
  }

  // Audio-reactive Lip-Sync Mouth Waveform
  const jawOpen = 6 + 34 * clamp(audioAmp * 1.8 + 0.25 * Math.abs(Math.sin(tGlobal * 18)), 0.05, 1.0);
  ctx.fillStyle = '#09090B';
  ctx.strokeStyle = accent;
  ctx.lineWidth = 2.5;
  roundRectPath(ctx, -38, 22, 76, jawOpen, 12);
  ctx.fill();
  ctx.stroke();

  ctx.restore();
  ctx.restore();
}

/**
 * L3_MotionProps: Persistent Through-Line Object + Velocity-Trailed Cursor + Floating Callout Badges
 */
export function renderL3MotionProps(ctx, W, H, layerProps = {}, cam = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  const stateIdx = Number(layerProps.through_line_state || 0);
  const accent = '#00F5D4';

  // 1. Through-Line Object ("telemetry_orb" / Quantum Pulse Core) that progresses across shots S1..S5
  const orbPositions = [
    [W * 0.5, H * 0.19],
    [W * 0.82, H * 0.25],
    [W * 0.82, H * 0.22],
    [W * 0.80, H * 0.68],
    [W * 0.5, H * 0.19],
  ];
  const [ox, oy] = orbPositions[stateIdx % orbPositions.length];
  const pulse = 1 + 0.14 * Math.sin(tGlobal * 6.5) + ring(tLocal, 0.05, 0.25, 24, 5);
  const orbR = 34 * pulse;

  ctx.save();
  ctx.translate(ox + (cam.panX || 0) * 0.6, oy + (cam.panY || 0) * 0.6);
  const orbGrad = ctx.createRadialGradient(0, 0, 4, 0, 0, orbR * 1.8);
  orbGrad.addColorStop(0, '#FFFFFF');
  orbGrad.addColorStop(0.35, accent);
  orbGrad.addColorStop(1, 'rgba(0, 245, 212, 0)');
  ctx.fillStyle = orbGrad;
  ctx.beginPath();
  ctx.arc(0, 0, orbR * 1.8, 0, Math.PI * 2);
  ctx.fill();

  // Rotating orbital ring around through-line core
  ctx.rotate(tGlobal * 2.4 + stateIdx);
  ctx.strokeStyle = '#D4FF00';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.ellipse(0, 0, orbR * 1.35, orbR * 0.55, 0.4, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  // 2. Floating Callout Badges
  const badges = Array.isArray(layerProps.floating_badges) ? layerProps.floating_badges : ['60FPS LOCK', 'PURE AST'];
  badges.forEach((label, idx) => {
    const enter = backOut(clamp((tLocal - idx * 0.12) / 0.42), 1.85);
    const bx = idx === 0 ? W * 0.12 : W * 0.62;
    const by = (idx === 0 ? H * 0.24 : H * 0.66) + (1 - enter) * 40;

    ctx.save();
    ctx.globalAlpha = clamp(enter, 0, 1);
    ctx.fillStyle = 'rgba(12, 15, 24, 0.90)';
    ctx.strokeStyle = idx === 0 ? '#D4FF00' : '#00F5D4';
    ctx.lineWidth = 2;
    roundRectPath(ctx, bx, by, 280, 52, 26);
    ctx.fill();
    ctx.stroke();

    ctx.font = '700 18px "JetBrains Mono", monospace';
    ctx.fillStyle = '#F8FAFC';
    ctx.textAlign = 'center';
    ctx.fillText(String(label), bx + 140, by + 32);
    ctx.restore();
  });

  // 3. Velocity-Trailed Interactive Studio Cursor (when active)
  if (layerProps.cursor_active) {
    const u = easeInOut(clamp(tLocal / 1.1));
    const curX = lerp(W * 0.78, W * 0.52, u);
    const curY = lerp(H * 0.68, H * 0.46, u);

    // Motion trail ghosts
    for (let g = 3; g >= 1; g--) {
      const ug = easeInOut(clamp((tLocal - g * 0.03) / 1.1));
      const gx = lerp(W * 0.78, W * 0.52, ug);
      const gy = lerp(H * 0.68, H * 0.46, ug);
      ctx.fillStyle = `rgba(212, 255, 0, ${0.15 / g})`;
      ctx.beginPath();
      ctx.arc(gx, gy, 14, 0, Math.PI * 2);
      ctx.fill();
    }

    // Click ripple after tLocal > 0.9s
    if (tLocal > 0.85) {
      const rU = clamp((tLocal - 0.85) / 0.45);
      ctx.strokeStyle = `rgba(212, 255, 0, ${1 - rU})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(curX, curY, 16 + rU * 68, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cursor pointer triangle
    ctx.fillStyle = '#D4FF00';
    ctx.strokeStyle = '#09090B';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(curX, curY);
    ctx.lineTo(curX + 28, curY + 12);
    ctx.lineTo(curX + 16, curY + 18);
    ctx.lineTo(curX + 24, curY + 32);
    ctx.lineTo(curX + 16, curY + 36);
    ctx.lineTo(curX + 8, curY + 22);
    ctx.lineTo(curX, curY + 30);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  ctx.restore();
}

/**
 * L4_TypographyHUD: Staggered Kinetic Headline + Word-Synced Narration Box inside >=8% Safe Margins
 */
export function renderL4TypographyHUD(ctx, W, H, layerProps = {}, tGlobal = 0, tLocal = 0, shotDur = 2.0) {
  ctx.save();
  const marginX = Math.round(W * Math.max(0.08, layerProps.safe_margin_pct || 0.08));
  const marginY = Math.round(H * 0.075);
  const safeW = W - marginX * 2;
  const accent = layerProps.accent_color || '#D4FF00';
  const textColor = layerProps.text_color || '#F8FAFC';

  // 1. Top Studio Telemetry Pill (strictly inside safe zone)
  const badgeTag = String(layerProps.badge_tag || 'CODE-HIGGSFIELD // 60FPS');
  ctx.fillStyle = 'rgba(9, 9, 11, 0.86)';
  ctx.strokeStyle = hexToRgba(accent, 0.75);
  ctx.lineWidth = 2;
  roundRectPath(ctx, marginX, marginY, Math.min(safeW, 440), 48, 24);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = accent;
  ctx.beginPath();
  ctx.arc(marginX + 26, marginY + 24, 6, 0, Math.PI * 2);
  ctx.fill();

  ctx.font = '700 17px "JetBrains Mono", monospace';
  ctx.fillStyle = textColor;
  ctx.textAlign = 'left';
  ctx.fillText(badgeTag, marginX + 44, marginY + 30);

  // 2. Kinetic Overshoot Headline
  const headline = String(layerProps.headline || 'CODE-HIGGSFIELD STUDIO');
  const headEnter = backOut(clamp(tLocal / 0.36), 1.9);
  const headY = marginY + 118 + (1 - headEnter) * 28;

  ctx.save();
  ctx.translate(W / 2, headY);
  ctx.scale(0.88 + 0.12 * headEnter, 0.88 + 0.12 * headEnter);

  // High-contrast backdrop plate behind headline for guaranteed WCAG > 7:1 readability
  ctx.fillStyle = 'rgba(9, 9, 11, 0.82)';
  roundRectPath(ctx, -safeW / 2, -52, safeW, 84, 18);
  ctx.fill();

  ctx.font = '900 44px "Inter", "Geist", sans-serif';
  ctx.fillStyle = textColor;
  ctx.textAlign = 'center';
  ctx.fillText(headline, 0, 6, safeW - 36);
  ctx.restore();

  // 3. Bottom Word-Synced Narration Subtitle Box (strictly inside safe margins)
  const caption = String(layerProps.sub_caption || '');
  if (caption) {
    const words = caption.split(/\s+/).filter(Boolean);
    const activeWordIdx = Math.min(
      words.length - 1,
      Math.floor(clamp(tLocal / Math.max(0.2, shotDur * 0.88)) * words.length)
    );

    const boxH = 148;
    const boxY = H - marginY - boxH;
    ctx.fillStyle = 'rgba(9, 9, 11, 0.92)';
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.18)';
    ctx.lineWidth = 2;
    roundRectPath(ctx, marginX, boxY, safeW, boxH, 22);
    ctx.fill();
    ctx.stroke();

    // Accent progress bar along bottom of caption card
    const progW = (safeW - 24) * clamp(tLocal / Math.max(0.1, shotDur));
    ctx.fillStyle = accent;
    roundRectPath(ctx, marginX + 12, boxY + boxH - 10, Math.max(8, progW), 4, 2);
    ctx.fill();

    // Wrap words into 2 clean lines inside safeW - 48
    ctx.font = '700 28px "Inter", sans-serif';
    const maxLineW = safeW - 56;
    const lines = [];
    let currentLine = [];
    let currentW = 0;

    words.forEach((w, idx) => {
      const ww = ctx.measureText(w + ' ').width;
      if (currentW + ww > maxLineW && currentLine.length > 0) {
        lines.push(currentLine);
        currentLine = [{ w, idx }];
        currentW = ww;
      } else {
        currentLine.push({ w, idx });
        currentW += ww;
      }
    });
    if (currentLine.length > 0) lines.push(currentLine);

    const displayLines = lines.slice(0, 2);
    displayLines.forEach((lineObj, lineIdx) => {
      const lineStr = lineObj.map((item) => item.w).join(' ');
      const totalLineW = ctx.measureText(lineStr).width;
      let cursorX = W / 2 - totalLineW / 2;
      const lineY = boxY + 56 + lineIdx * 42;

      lineObj.forEach((item) => {
        const isCurrent = item.idx === activeWordIdx;
        const isPast = item.idx < activeWordIdx;
        const wordW = ctx.measureText(item.w + ' ').width;

        if (isCurrent) {
          ctx.fillStyle = accent;
          roundRectPath(ctx, cursorX - 6, lineY - 28, wordW + 4, 36, 8);
          ctx.fill();
          ctx.fillStyle = '#09090B';
        } else if (isPast) {
          ctx.fillStyle = '#FFFFFF';
        } else {
          ctx.fillStyle = '#94A3B8';
        }

        ctx.textAlign = 'left';
        ctx.fillText(item.w, cursorX, lineY);
        cursorX += wordW;
      });
    });
  }

  ctx.restore();
}

/**
 * L5_PostFX: Beat-Drop Impact Flash, Anamorphic Streak & Radial Vignette
 */
export function renderL5PostFX(ctx, W, H, layerProps = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();

  // 1. Cut/Beat entry flash decay (subtle cinematic lens flare on downbeat cuts)
  if (layerProps.beat_flash && tLocal < 0.22) {
    const flashAlpha = (1 - tLocal / 0.22) ** 2 * 0.22;
    ctx.fillStyle = `rgba(212, 255, 0, ${flashAlpha})`;
    ctx.fillRect(0, 0, W, H);
  }

  // 2. Anamorphic horizontal streak across hero center
  const streakY = H * 0.45;
  const streakGrad = ctx.createLinearGradient(0, streakY, W, streakY);
  streakGrad.addColorStop(0, 'rgba(0, 245, 212, 0)');
  streakGrad.addColorStop(0.5, 'rgba(212, 255, 0, 0.08)');
  streakGrad.addColorStop(1, 'rgba(0, 245, 212, 0)');
  ctx.fillStyle = streakGrad;
  ctx.fillRect(0, streakY - 3, W, 6);

  // 3. Optical Vignette
  const vigStrength = layerProps.vignette ?? 0.22;
  const rad = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.max(W, H) * 0.72);
  rad.addColorStop(0, 'rgba(0,0,0,0)');
  rad.addColorStop(1, `rgba(0,0,0,${vigStrength})`);
  ctx.fillStyle = rad;
  ctx.fillRect(0, 0, W, H);

  ctx.restore();
}

/**
 * Render complete 6-Layer Scene Graph for frame i (or isolated single layer if activeLayerFilter is set)
 */
export function renderSceneLayers(ctx, sceneDescriptor, activeLayerFilter = null) {
  const { width: W, height: H, tGlobal, tLocal, shotDur, cam, layers, audioAmp = 0.25 } = sceneDescriptor;
  ctx.clearRect(0, 0, W, H);

  const shouldDraw = (layerName) => !activeLayerFilter || activeLayerFilter === layerName;

  if (shouldDraw('L0_Backdrop')) {
    renderL0Backdrop(ctx, W, H, layers.L0_Backdrop, tGlobal, tLocal);
  }
  if (shouldDraw('L1_Environment')) {
    renderL1Environment(ctx, W, H, layers.L1_Environment, cam, tGlobal, tLocal);
  }
  if (shouldDraw('L2_HeroSubject')) {
    renderL2HeroSubject(ctx, W, H, layers.L2_HeroSubject, cam, tGlobal, tLocal, audioAmp);
  }
  if (shouldDraw('L3_MotionProps')) {
    renderL3MotionProps(ctx, W, H, layers.L3_MotionProps, cam, tGlobal, tLocal);
  }
  if (shouldDraw('L4_TypographyHUD')) {
    renderL4TypographyHUD(ctx, W, H, layers.L4_TypographyHUD, tGlobal, tLocal, shotDur);
  }
  if (shouldDraw('L5_PostFX')) {
    renderL5PostFX(ctx, W, H, layers.L5_PostFX, tGlobal, tLocal);
  }
}
