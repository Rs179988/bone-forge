/**
 * Layer 2C: Pre-Built Procedural Component Kit, Neo-Brutalist Editorial Cards & 2.5D Character Rigs
 * Implements the 6 Isolated Studio Layers:
 *   L0_Backdrop, L1_Environment, L2_HeroSubject, L3_MotionProps, L4_TypographyHUD, L5_PostFX
 * First-class support for WizardZ Editorial Light (#FFFFFF, #F3F3F3, #191A23, #B9FF66),
 * Royal Violet Daylight, Warm Ivory Craft, and Obsidian Dark themes.
 */

import { clamp, lerp, smooth, easeOut, easeInOut, backOut, ring, springDamper } from '../core/curves.mjs';

function hexToRgba(hex, alpha = 1.0) {
  if (!hex || typeof hex !== 'string') return `rgba(185, 255, 102, ${alpha})`;
  if (hex.startsWith('rgba') || hex.startsWith('rgb')) return hex;
  const clean = hex.replace('#', '');
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean;
  const num = parseInt(full, 16) || 0xb9ff66;
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function isLightHex(hex) {
  if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) return true;
  const clean = hex.replace('#', '');
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean;
  const num = parseInt(full, 16) || 0xffffff;
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return (0.299 * r + 0.587 * g + 0.114 * b) > 150;
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

function drawFourPointStar(ctx, cx, cy, outerR, innerR, fillStyle, strokeStyle = null, rot = 0) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(rot);
  ctx.beginPath();
  for (let i = 0; i < 8; i++) {
    const r = i % 2 === 0 ? outerR : innerR;
    const ang = (i * Math.PI) / 4;
    const px = Math.cos(ang) * r;
    const py = Math.sin(ang) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fillStyle = fillStyle;
  ctx.fill();
  if (strokeStyle) {
    ctx.strokeStyle = strokeStyle;
    ctx.lineWidth = 2.5;
    ctx.stroke();
  }
  ctx.restore();
}

/**
 * L0_Backdrop: Editorial Light Paper / Pastel Daylight OR Obsidian Studio Atmosphere
 */
export function renderL0Backdrop(ctx, W, H, layerProps = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  const bg1 = layerProps.palette_bg || '#FFFFFF';
  const bg2 = layerProps.palette_secondary || '#F3F3F3';
  const accent = layerProps.accent_color || '#B9FF66';
  const ink = layerProps.ink_color || '#191A23';
  const isLight = isLightHex(bg1);

  const grad = ctx.createLinearGradient(0, 0, W, H);
  grad.addColorStop(0, bg1);
  grad.addColorStop(0.55, bg2);
  grad.addColorStop(1, bg1);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  if (isLight) {
    // Soft editorial lime/violet ambient wash + clean diagonal geometric rings (like WizardZ reference)
    const cx = W * (0.68 + 0.05 * Math.sin(tGlobal * 0.9));
    const cy = H * (0.34 + 0.04 * Math.cos(tGlobal * 0.7));
    const radGrad = ctx.createRadialGradient(cx, cy, W * 0.02, cx, cy, W * 0.55);
    radGrad.addColorStop(0, hexToRgba(accent, 0.32));
    radGrad.addColorStop(0.6, hexToRgba(accent, 0.08));
    radGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
    ctx.fillStyle = radGrad;
    ctx.fillRect(0, 0, W, H);

    // Subtle editorial architectural grid lines
    ctx.strokeStyle = hexToRgba(ink, 0.05);
    ctx.lineWidth = 1;
    const step = 64;
    for (let x = step; x < W; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = step; y < H; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.stroke();
    }
  } else {
    // Dark cinema mode
    const cx = W * (0.5 + 0.08 * Math.sin(tGlobal * 0.9));
    const cy = H * (0.42 + 0.05 * Math.cos(tGlobal * 0.7));
    const radGrad = ctx.createRadialGradient(cx, cy, W * 0.04, cx, cy, W * 0.85);
    radGrad.addColorStop(0, hexToRgba(accent, 0.20));
    radGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = radGrad;
    ctx.fillRect(0, 0, W, H);
  }

  ctx.restore();
}

/**
 * L1_Environment: Orbital Ellipses, Editorial Dot Matrix & Floating Starbursts (WizardZ Style)
 */
export function renderL1Environment(ctx, W, H, layerProps = {}, cam = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  const accent = layerProps.accent_color || '#191A23';
  const highlight = layerProps.highlight_color || '#B9FF66';
  const depthScale = layerProps.parallax_depth || 1.1;

  const panX = (cam.panX || 0) * 0.4 * depthScale;
  const panY = (cam.panY || 0) * 0.4 * depthScale;
  ctx.translate(W / 2 + panX, H / 2 + panY);
  ctx.scale(cam.zoom ? 1 + (cam.zoom - 1) * 0.35 : 1, cam.zoom ? 1 + (cam.zoom - 1) * 0.35 : 1);
  ctx.translate(-W / 2, -H / 2);

  // Tilted orbital rings (matching the megaphone orbital rings in the WizardZ hero illustration)
  const cx = W * 0.5;
  const cy = H * 0.47;
  for (let r = 0; r < 3; r++) {
    ctx.save();
    ctx.translate(cx, cy + (r - 1) * 26);
    ctx.rotate(-0.22 + 0.04 * Math.sin(tGlobal * 1.3 + r));
    ctx.strokeStyle = hexToRgba(accent, 0.22 - r * 0.04);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(0, 0, W * (0.40 + r * 0.03), H * (0.08 + r * 0.015), 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  // Editorial 4-point starbursts (black & acid lime stars from WizardZ reference)
  drawFourPointStar(ctx, W * 0.14, H * 0.30, 26, 9, accent, null, tGlobal * 0.6);
  drawFourPointStar(ctx, W * 0.85, H * 0.62, 32, 11, highlight, accent, -tGlobal * 0.5);
  drawFourPointStar(ctx, W * 0.20, H * 0.72, 18, 6, highlight, accent, tGlobal * 0.8);

  ctx.restore();
}

/**
 * L2_HeroSubject: Neo-Brutalist Positivus/WizardZ Hero Card OR Articulated 2.5D Character Rig
 */
export function renderL2HeroSubject(ctx, W, H, layerProps = {}, cam = {}, tGlobal = 0, tLocal = 0, audioAmp = 0.2) {
  ctx.save();
  const kind = layerProps.kind || 'saas_3d_card';
  const accent = layerProps.accent_color || '#B9FF66';
  const ink = layerProps.ink_color || '#191A23';
  const stiffness = layerProps.stiffness || 220;
  const damping = layerProps.damping || 18;
  const entrySpring = clamp(springDamper(tLocal + 0.08, stiffness, damping), 0, 1.3);
  const settleRing = ring(tLocal, 0.10, 0.03, 20, 5.5);

  const cx = W * 0.5 + (cam.panX || 0);
  const cy = H * 0.47 + (cam.panY || 0);
  const scale = (cam.zoom || 1.0) * (0.85 + 0.15 * entrySpring + settleRing);

  ctx.translate(cx, cy);
  ctx.rotate(((cam.tiltDeg || 0) * Math.PI) / 180);
  ctx.scale(scale, scale);

  if (kind === 'character_rig') {
    _drawArticulatedCharacterRig(ctx, W, H, layerProps, tGlobal, tLocal, audioAmp, accent, ink);
  } else {
    _drawWizardZEditorialCard(ctx, W, H, layerProps, tGlobal, tLocal, entrySpring, accent, ink);
  }

  ctx.restore();
}

function _drawWizardZEditorialCard(ctx, W, H, props, tGlobal, tLocal, springVal, accent, ink) {
  const cardW = Math.min(W * 0.82, 820);
  const cardH = Math.min(H * 0.37, 570);
  const x = -cardW / 2;
  const y = -cardH / 2;

  const variant = props.card_variant || 'white';
  const cardBg = variant === 'dark' ? '#191A23' : variant === 'lime' ? accent : '#FFFFFF';
  const mainText = variant === 'dark' ? '#FFFFFF' : '#191A23';
  const pillBg = variant === 'lime' ? '#FFFFFF' : accent;
  const pillText = '#191A23';

  // Signature Neo-Brutalist Hard Offset Shadow (0 10px 0 #191A23)
  ctx.fillStyle = ink;
  roundRectPath(ctx, x + 4, y + 12, cardW, cardH, 38);
  ctx.fill();

  // Main Card Body
  ctx.fillStyle = cardBg;
  ctx.strokeStyle = ink;
  ctx.lineWidth = 3.5;
  roundRectPath(ctx, x, y, cardW, cardH, 38);
  ctx.fill();
  ctx.stroke();

  // Top Lime Highlight Label Pill inside Card (exact Positivus service card style)
  const cardTitle = String(props.card_title || props.metric_label || 'DIGITAL GROWTH').toUpperCase();
  ctx.font = '800 26px "Space Grotesk", "Inter", sans-serif';
  const pillW = Math.min(cardW - 96, Math.max(220, ctx.measureText(cardTitle).width + 44));
  ctx.fillStyle = pillBg;
  roundRectPath(ctx, x + 44, y + 42, pillW, 52, 12);
  ctx.fill();

  ctx.fillStyle = pillText;
  ctx.textAlign = 'left';
  ctx.fillText(cardTitle, x + 64, y + 77, pillW - 36);

  // Animated Metric Counter on Left Side
  const targetVal = Number(props.metric_value ?? 240);
  const unit = String(props.metric_unit || '%');
  const animatedVal = (targetVal * clamp(backOut(clamp(tLocal / 0.6), 1.5), 0, 1.1)).toFixed(
    targetVal % 1 === 0 ? 0 : 1
  );

  ctx.font = '800 84px "Space Grotesk", "Inter", sans-serif';
  ctx.fillStyle = mainText;
  ctx.fillText(`${animatedVal}${unit}`, x + 44, y + 195);

  ctx.font = '600 21px "Plus Jakarta Sans", "Inter", sans-serif';
  ctx.fillStyle = variant === 'dark' ? '#CBD5E1' : '#595A66';
  ctx.fillText(String(props.metric_label || 'VERIFIED CAMPAIGN IMPACT'), x + 46, y + 234);

  // Right Side Vector Illustration (Megaphone / Geometric Growth Node like WizardZ)
  const illX = x + cardW * 0.72;
  const illY = y + cardH * 0.44;
  ctx.save();
  ctx.translate(illX, illY);
  const floatY = Math.sin(tGlobal * 3.2) * 8;
  ctx.translate(0, floatY);

  // Orbit ellipse
  ctx.strokeStyle = variant === 'dark' ? '#FFFFFF' : ink;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.ellipse(0, 22, 92, 28, -0.25, 0, Math.PI * 2);
  ctx.stroke();

  // Megaphone cone (Lime + Ink outline)
  ctx.rotate(-0.28 + 0.06 * Math.sin(tGlobal * 4));
  ctx.fillStyle = accent;
  ctx.strokeStyle = ink;
  ctx.lineWidth = 3.2;
  ctx.beginPath();
  ctx.moveTo(-48, -14);
  ctx.lineTo(38, -46);
  ctx.lineTo(38, 46);
  ctx.lineTo(-48, 14);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Megaphone bell
  ctx.fillStyle = '#FFFFFF';
  ctx.beginPath();
  ctx.ellipse(38, 0, 16, 46, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.restore();

  // Bottom Section: Clean Progress Bar + "Learn more ↗" Circle Arrow Button
  const bottomY = y + cardH - 86;
  ctx.fillStyle = variant === 'dark' ? '#FFFFFF' : ink;
  ctx.beginPath();
  ctx.arc(x + 68, bottomY + 22, 24, 0, Math.PI * 2);
  ctx.fill();

  // Arrow inside circle
  ctx.strokeStyle = variant === 'dark' ? ink : accent;
  ctx.lineWidth = 3.5;
  ctx.beginPath();
  ctx.moveTo(x + 60, bottomY + 30);
  ctx.lineTo(x + 76, bottomY + 14);
  ctx.moveTo(x + 64, bottomY + 14);
  ctx.lineTo(x + 76, bottomY + 14);
  ctx.lineTo(x + 76, bottomY + 26);
  ctx.stroke();

  ctx.font = '700 22px "Space Grotesk", "Inter", sans-serif';
  ctx.fillStyle = mainText;
  ctx.fillText('Active Stage', x + 108, bottomY + 30);

  // Animated Bars on bottom right
  const barStartX = x + cardW * 0.48;
  const barCount = 10;
  for (let b = 0; b < barCount; b++) {
    const wave = 0.35 + 0.65 * Math.abs(Math.sin(tGlobal * 3.6 + b * 0.5));
    const bh = 18 + 56 * wave;
    const bx = barStartX + b * 34;
    const by = bottomY + 44 - bh;
    ctx.fillStyle = b % 2 === 0 ? accent : (variant === 'dark' ? '#FFFFFF' : ink);
    roundRectPath(ctx, bx, by, 20, bh, 6);
    ctx.fill();
  }
}

function _drawArticulatedCharacterRig(ctx, W, H, props, tGlobal, tLocal, audioAmp, accent, ink) {
  const breathe = 1 + 0.025 * Math.sin(tGlobal * 3.4);
  const hop = ring(tLocal, 0.05, 18, 20, 5);
  const squash = 1 + ring(tLocal, 0.05, 0.07, 22, 6);

  ctx.save();
  ctx.translate(0, -hop);
  ctx.scale(squash, (2 - squash) * breathe);

  // Neo-brutalist backdrop badge behind character
  ctx.fillStyle = accent;
  ctx.strokeStyle = ink;
  ctx.lineWidth = 3.5;
  ctx.beginPath();
  ctx.arc(0, -20, 210, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Torso
  ctx.fillStyle = '#191A23';
  ctx.strokeStyle = ink;
  ctx.lineWidth = 4;
  roundRectPath(ctx, -110, 25, 220, 195, 46);
  ctx.fill();
  ctx.stroke();

  // Chest Star Emblem
  drawFourPointStar(ctx, 0, 110, 32, 12, accent, '#FFFFFF', tGlobal * 0.8);

  // Arms
  for (const dir of [-1, 1]) {
    ctx.save();
    ctx.translate(dir * 118, 55);
    ctx.rotate(dir * (0.22 + 0.16 * Math.sin(tGlobal * 4.0 + dir)));
    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = ink;
    ctx.lineWidth = 3.5;
    roundRectPath(ctx, -22, 0, 44, 130, 20);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  // Head
  ctx.save();
  ctx.translate(0, -82);
  ctx.rotate(0.06 * Math.sin(tGlobal * 2.5));
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = ink;
  ctx.lineWidth = 4;
  roundRectPath(ctx, -92, -92, 184, 170, 50);
  ctx.fill();
  ctx.stroke();

  // Expressive Eyes
  const blinkPhase = tGlobal % 2.8;
  const eyeOpen = blinkPhase > 2.66 ? 0.15 : 1.0;
  for (const ex of [-36, 36]) {
    ctx.fillStyle = ink;
    roundRectPath(ctx, ex - 14, -28, 28, Math.max(4, 34 * eyeOpen), 14);
    ctx.fill();
  }

  // Lip-sync mouth
  const jawOpen = 8 + 30 * clamp(audioAmp * 1.8 + 0.25 * Math.abs(Math.sin(tGlobal * 18)), 0.05, 1.0);
  ctx.fillStyle = accent;
  ctx.strokeStyle = ink;
  ctx.lineWidth = 3;
  roundRectPath(ctx, -34, 24, 68, jawOpen, 12);
  ctx.fill();
  ctx.stroke();

  ctx.restore();
  ctx.restore();
}

/**
 * L3_MotionProps: Floating Neo-Brutalist Badges + Interactive Studio Cursor
 */
export function renderL3MotionProps(ctx, W, H, layerProps = {}, cam = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  const accent = layerProps.accent_color || '#B9FF66';
  const ink = layerProps.ink_color || '#191A23';

  // Floating Callout Badges with crisp ink borders & offset shadows
  const badges = Array.isArray(layerProps.floating_badges) ? layerProps.floating_badges : ['GROWTH', '01 // FOCUS'];
  badges.forEach((label, idx) => {
    const enter = backOut(clamp((tLocal - idx * 0.10) / 0.40), 1.7);
    const bx = idx === 0 ? W * 0.10 : W * 0.60;
    const by = (idx === 0 ? H * 0.23 : H * 0.69) + (1 - enter) * 32;

    ctx.save();
    ctx.globalAlpha = clamp(enter, 0, 1);
    // Offset shadow
    ctx.fillStyle = ink;
    roundRectPath(ctx, bx + 3, by + 6, 290, 54, 27);
    ctx.fill();

    ctx.fillStyle = idx === 0 ? accent : '#FFFFFF';
    ctx.strokeStyle = ink;
    ctx.lineWidth = 2.5;
    roundRectPath(ctx, bx, by, 290, 54, 27);
    ctx.fill();
    ctx.stroke();

    ctx.font = '800 19px "Space Grotesk", "Inter", sans-serif';
    ctx.fillStyle = ink;
    ctx.textAlign = 'center';
    ctx.fillText(String(label), bx + 145, by + 34);
    ctx.restore();
  });

  // Interactive Cursor
  if (layerProps.cursor_active) {
    const u = easeInOut(clamp(tLocal / 1.05));
    const curX = lerp(W * 0.78, W * 0.54, u);
    const curY = lerp(H * 0.66, H * 0.48, u);

    if (tLocal > 0.82) {
      const rU = clamp((tLocal - 0.82) / 0.45);
      ctx.strokeStyle = hexToRgba(ink, 1 - rU);
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(curX, curY, 14 + rU * 58, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.fillStyle = accent;
    ctx.strokeStyle = ink;
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
 * L4_TypographyHUD: WizardZ Highlight Headline + Word-Synced Subtitle Card inside >=8% Safe Margins
 */
export function renderL4TypographyHUD(ctx, W, H, layerProps = {}, tGlobal = 0, tLocal = 0, shotDur = 2.0) {
  ctx.save();
  const marginX = Math.round(W * Math.max(0.08, layerProps.safe_margin_pct || 0.08));
  const marginY = Math.round(H * 0.07);
  const safeW = W - marginX * 2;
  const accent = layerProps.accent_color || '#B9FF66';
  const ink = layerProps.ink_color || '#191A23';

  // 1. Top Pill Tag
  const badgeTag = String(layerProps.badge_tag || '01 • STUDIO');
  ctx.fillStyle = '#FFFFFF';
  ctx.strokeStyle = ink;
  ctx.lineWidth = 2.5;
  roundRectPath(ctx, marginX, marginY, Math.min(safeW, 340), 48, 24);
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = accent;
  ctx.strokeStyle = ink;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(marginX + 26, marginY + 24, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  ctx.font = '800 18px "Space Grotesk", monospace';
  ctx.fillStyle = ink;
  ctx.textAlign = 'left';
  ctx.fillText(badgeTag, marginX + 46, marginY + 30);

  // 2. Signature Lime Highlight Headline Bar (WizardZ "Services" / "Case study" highlight style)
  const headline = String(layerProps.headline || 'DIGITAL LANDSCAPE');
  const headEnter = backOut(clamp(tLocal / 0.35), 1.7);
  const headY = marginY + 115 + (1 - headEnter) * 24;

  ctx.save();
  ctx.translate(W / 2, headY);
  ctx.scale(0.9 + 0.1 * headEnter, 0.9 + 0.1 * headEnter);

  // Offset shadow
  ctx.fillStyle = ink;
  roundRectPath(ctx, -safeW / 2 + 4, -44, safeW, 84, 18);
  ctx.fill();

  // Lime highlight bar with ink border
  ctx.fillStyle = accent;
  ctx.strokeStyle = ink;
  ctx.lineWidth = 3;
  roundRectPath(ctx, -safeW / 2, -50, safeW, 84, 18);
  ctx.fill();
  ctx.stroke();

  ctx.font = '900 42px "Space Grotesk", "Inter", sans-serif';
  ctx.fillStyle = '#191A23';
  ctx.textAlign = 'center';
  ctx.fillText(headline, 0, 6, safeW - 36);
  ctx.restore();

  // 3. Bottom Word-Synced Subtitle Card (#191A23 Charcoal Card with #B9FF66 active word pill -> 18:1 WCAG contrast)
  const caption = String(layerProps.sub_caption || '');
  if (caption) {
    const words = caption.split(/\s+/).filter(Boolean);
    const activeWordIdx = Math.min(
      words.length - 1,
      Math.floor(clamp(tLocal / Math.max(0.2, shotDur * 0.88)) * words.length)
    );

    const boxH = 148;
    const boxY = H - marginY - boxH;
    ctx.fillStyle = '#191A23';
    ctx.strokeStyle = ink;
    ctx.lineWidth = 3;
    roundRectPath(ctx, marginX, boxY, safeW, boxH, 26);
    ctx.fill();
    ctx.stroke();

    const progW = (safeW - 32) * clamp(tLocal / Math.max(0.1, shotDur));
    ctx.fillStyle = accent;
    roundRectPath(ctx, marginX + 16, boxY + boxH - 12, Math.max(8, progW), 5, 3);
    ctx.fill();

    ctx.font = '700 27px "Plus Jakarta Sans", "Inter", sans-serif';
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
          ctx.fillStyle = '#191A23';
        } else if (isPast) {
          ctx.fillStyle = '#FFFFFF';
        } else {
          ctx.fillStyle = '#CBD5E1';
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
 * L5_PostFX: Subtle Editorial Frame Polish
 */
export function renderL5PostFX(ctx, W, H, layerProps = {}, tGlobal = 0, tLocal = 0) {
  ctx.save();
  if (layerProps.beat_flash && tLocal < 0.18) {
    const flashAlpha = (1 - tLocal / 0.18) ** 2 * 0.14;
    ctx.fillStyle = `rgba(185, 255, 102, ${flashAlpha})`;
    ctx.fillRect(0, 0, W, H);
  }
  ctx.restore();
}

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
