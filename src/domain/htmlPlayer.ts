import { SkeletonData } from './types.js';

/**
 * Standalone HTML5 Canvas Interactive Preview Player
 * Generates a self-contained zero-dependency HTML file with 60 FPS animation loop,
 * bone vector rendering, and real-time playback controls.
 */

export function generateHtmlPreview(data: SkeletonData): string {
  const skeletonJson = JSON.stringify(data);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bone-Forge 2D Skeleton Preview - ${data.name}</title>
  <style>
    body {
      margin: 0;
      background: #121316;
      color: #e0e0e0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
    }
    h1 { margin-bottom: 8px; font-size: 20px; color: #4ade80; }
    p { margin-top: 0; color: #94a3b8; font-size: 13px; }
    canvas {
      background: #1e2025;
      border: 1px solid #334155;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    }
    .controls {
      margin-top: 15px;
      display: flex;
      gap: 12px;
      align-items: center;
    }
    button {
      background: #2563eb;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
    }
    button:hover { background: #1d4ed8; }
    .badge {
      background: #334155;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <h1>Bone-Forge Interactive 2D Preview</h1>
  <p>Skeleton: <strong>${data.name}</strong> | Bones: ${data.bones.length} | Slots: ${data.slots.length}</p>
  <canvas id="stage" width="600" height="600"></canvas>
  <div class="controls">
    <button id="togglePlay">Pause</button>
    <button id="resetView">Reset View</button>
    <span class="badge">FPS: <span id="fps">60</span></span>
  </div>

  <script>
    const skeleton = ${skeletonJson};
    const canvas = document.getElementById('stage');
    const ctx = canvas.getContext('2d');
    let playing = true;
    let time = 0;

    function drawBone(bone, parentX, parentY, parentRot) {
      const rad = ((bone.rotation + parentRot) * Math.PI) / 180;
      const bx = parentX + bone.x;
      const by = parentY + bone.y;
      const length = bone.length || 40;

      const endX = bx + Math.cos(rad) * length;
      const endY = by + Math.sin(rad) * length;

      // Draw bone line
      ctx.beginPath();
      ctx.moveTo(bx, by);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Joint circle
      ctx.beginPath();
      ctx.arc(bx, by, 6, 0, Math.PI * 2);
      ctx.fillStyle = '#f43f5e';
      ctx.fill();

      // Bone tip circle
      ctx.beginPath();
      ctx.arc(endX, endY, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#fbbf24';
      ctx.fill();

      // Label
      ctx.fillStyle = '#94a3b8';
      ctx.font = '10px monospace';
      ctx.fillText(bone.name, bx + 8, by - 6);

      // Draw children
      const children = skeleton.bones.filter(b => b.parentId === bone.id);
      for (const child of children) {
        drawBone(child, bx, by, bone.rotation + parentRot);
      }
    }

    function render() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Coordinate center
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2 + 50;

      // Draw grid
      ctx.strokeStyle = '#272a30';
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }

      // Root bones (no parent)
      const roots = skeleton.bones.filter(b => !b.parentId);
      for (const root of roots) {
        drawBone(root, centerX, centerY, 0);
      }

      if (playing) {
        time += 0.016;
      }
      requestAnimationFrame(render);
    }

    document.getElementById('togglePlay').addEventListener('click', (e) => {
      playing = !playing;
      e.target.textContent = playing ? 'Pause' : 'Play';
    });

    render();
  </script>
</body>
</html>`;
}
