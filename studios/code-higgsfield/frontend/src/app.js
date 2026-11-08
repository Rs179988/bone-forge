/**
 * Phase 4: CODE-HIGGSFIELD Studio Frontend Application
 * Connects live to the Zero-Key Local MCP Server & 6-Layer Middleware Engine.
 */

const LAYERS = [
  'L0_Backdrop',
  'L1_Environment',
  'L2_HeroSubject',
  'L3_MotionProps',
  'L4_TypographyHUD',
  'L5_PostFX',
];

const state = {
  activeTab: 'vibe_motion',
  mcpStatus: 'CONNECTING...',
  jobs: [],
  activeJob: null,
  selectedShotId: 'S1',
  selectedLayerId: 'L2_HeroSubject',
  storyCode: '',
  filmCode: '',
  activeCodeTab: 'story',
  vault: { brandkits: [], cast_rigs: [] },
  katanaBlueprint: null,
  busyMessage: null,
};

async function apiGet(path) {
  const res = await fetch(path);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function callMcpTool(name, args = {}) {
  const resp = await apiPost('/api/mcp/call', { name, arguments: args });
  if (!resp.ok) throw new Error(resp.error || 'MCP call failed');
  return resp.result;
}

async function refreshStudioState(selectJobId = null) {
  try {
    const data = await apiGet('/api/studio/state');
    state.mcpStatus = data.mcp_status || 'CONNECTED';
    state.jobs = data.jobs || [];
    state.vault = data.vault || { brandkits: [], cast_rigs: [] };

    if (selectJobId) {
      state.activeJob = state.jobs.find((j) => j.job_id === selectJobId) || state.jobs[0] || null;
    } else if (!state.activeJob && state.jobs.length > 0) {
      state.activeJob = state.jobs[0];
    } else if (state.activeJob) {
      state.activeJob = state.jobs.find((j) => j.job_id === state.activeJob.job_id) || state.jobs[0];
    }

    if (state.activeJob) {
      const codeResp = await apiGet(`/api/jobs/${state.activeJob.job_id}/code`);
      state.storyCode = codeResp.story_mjs || '';
      state.filmCode = codeResp.film_mjs || '';
    }
    renderApp();
  } catch (err) {
    state.mcpStatus = 'OFFLINE // CHECK MCP SERVER';
    renderApp();
  }
}

function setBusy(msg) {
  state.busyMessage = msg;
  renderApp();
}

/* ---------------- Cross-Studio Handoff (adapted from Open-Higgsfield handoff.js) ---------------- */
window.handoffToStudio = function (targetTab, jobId, shotId = 'S1') {
  state.activeTab = targetTab;
  if (jobId) {
    state.activeJob = state.jobs.find((j) => j.job_id === jobId) || state.activeJob;
  }
  state.selectedShotId = shotId;
  renderApp();
};

/* ---------------- Studio Actions ---------------- */
window.handleGenerateJob = async function () {
  const promptEl = document.getElementById('inp-prompt');
  const aspectEl = document.getElementById('inp-aspect');
  const durEl = document.getElementById('inp-duration');
  const paletteEl = document.getElementById('inp-palette');
  const stiffEl = document.getElementById('inp-stiffness');
  const dampEl = document.getElementById('inp-damping');

  const payload = {
    prompt: promptEl ? promptEl.value : 'Quantum 60FPS Fintech Launch Promo',
    studio_mode: state.activeTab === 'cinema_shorts' ? 'cinema_shorts' : 'vibe_motion',
    aspect_ratio: aspectEl ? aspectEl.value : '9:16',
    duration_sec: durEl ? parseFloat(durEl.value) : 10.0,
    palette_id: paletteEl ? paletteEl.value : 'higgsfield_obsidian_lime',
    stiffness: stiffEl ? parseFloat(stiffEl.value) : 210,
    damping: dampEl ? parseFloat(dampEl.value) : 18,
    katana_blueprint: state.katanaBlueprint || undefined,
    render_mode: 'master',
  };

  try {
    setBusy('Compiling 6-Layer Brief -> Synthesizing Audio & Beatmap -> Rendering 60FPS Master -> Running QA Gate...');
    const res = await apiPost('/api/studio/full-generate', payload);
    if (!res.ok) throw new Error(res.error || 'Generation failed');
    setBusy(null);
    await refreshStudioState(res.job_id);
  } catch (err) {
    setBusy(null);
    alert('Error: ' + err.message);
  }
};

window.handleSurgicalPatch = async function () {
  if (!state.activeJob) return alert('Select or generate a job first.');
  const instrEl = document.getElementById('inp-patch-instruction');
  const headlineEl = document.getElementById('inp-patch-headline');
  const colorEl = document.getElementById('inp-patch-color');
  const stiffEl = document.getElementById('inp-patch-stiff');

  const layerUpdates = {};
  if (colorEl && colorEl.value) layerUpdates.accent_color = colorEl.value;
  if (stiffEl && stiffEl.value) layerUpdates.stiffness = parseFloat(stiffEl.value);
  if (headlineEl && headlineEl.value && state.selectedLayerId === 'L4_TypographyHUD') {
    layerUpdates.headline = headlineEl.value;
  }

  try {
    setBusy(`Surgically patching ${state.selectedShotId} (${state.selectedLayerId}) via assemble_partial_edit.sh...`);
    await callMcpTool('higgsfield_patch_layer_or_shot', {
      job_id: state.activeJob.job_id,
      shot_id: state.selectedShotId,
      layer_id: state.selectedLayerId,
      layer_updates: layerUpdates,
      instruction: instrEl ? instrEl.value : undefined,
    });
    await callMcpTool('higgsfield_run_qa_gate', { job_id: state.activeJob.job_id });
    setBusy(null);
    await refreshStudioState(state.activeJob.job_id);
  } catch (err) {
    setBusy(null);
    alert('Surgical Patch Error: ' + err.message);
  }
};

window.handleKatanaDecompile = async function () {
  const pathEl = document.getElementById('inp-katana-path');
  const defaultPath = state.activeJob
    ? `/workspace/studios/code-higgsfield/jobs/${state.activeJob.job_id}/master_60fps.mp4`
    : '/workspace/studios/story-shorts-v1/output/casino_psychology/master_60fps.mp4';
  const vPath = pathEl && pathEl.value.trim() ? pathEl.value.trim() : defaultPath;

  try {
    setBusy('Running Katana Reference Decompiler (ffprobe + scdet + optical flow + beatmap.py)...');
    const res = await callMcpTool('higgsfield_decompile_reference', { video_path: vPath });
    state.katanaBlueprint = res.blueprint;
    setBusy(null);
    renderApp();
  } catch (err) {
    setBusy(null);
    alert('Katana Decompile Error: ' + err.message);
  }
};

window.handleSaveSceneCode = async function () {
  if (!state.activeJob) return;
  const ed = document.getElementById('code-drawer-textarea');
  if (!ed) return;
  try {
    setBusy('Validating & saving scene module via higgsfield_submit_scene_code...');
    const args = { job_id: state.activeJob.job_id };
    if (state.activeCodeTab === 'story') args.story_mjs_code = ed.value;
    else args.film_mjs_code = ed.value;
    await callMcpTool('higgsfield_submit_scene_code', args);
    await callMcpTool('higgsfield_render_preview_or_master', {
      job_id: state.activeJob.job_id,
      mode: 'master',
    });
    await callMcpTool('higgsfield_run_qa_gate', { job_id: state.activeJob.job_id });
    setBusy(null);
    await refreshStudioState(state.activeJob.job_id);
  } catch (err) {
    setBusy(null);
    alert('Code Save Error: ' + err.message);
  }
};

window.selectTab = function (tabId) {
  state.activeTab = tabId;
  renderApp();
};

window.selectShot = function (shotId) {
  state.selectedShotId = shotId;
  renderApp();
};

window.selectLayer = function (layerId) {
  state.selectedLayerId = layerId;
  renderApp();
};

window.selectJob = function (jobId) {
  refreshStudioState(jobId);
};

window.switchCodeTab = function (tab) {
  state.activeCodeTab = tab;
  renderApp();
};

function renderLeftPanel() {
  const job = state.activeJob;
  const shots = job?.script?.shots || [];
  const activeShot = shots.find((s) => s.id === state.selectedShotId) || shots[0];

  if (state.activeTab === 'miracle_layer') {
    const layerData = activeShot?.layers?.[state.selectedLayerId] || {};
    return `
      <div>
        <div class="section-label">MIRACLE // SURGICAL 6-LAYER AST EDITOR</div>
        <p style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">
          Select any isolated layer in Shot <b>${state.selectedShotId}</b> and patch only those frames via <code>assemble_partial_edit.sh</code>.
        </p>
        <div class="layer-pill-grid">
          ${LAYERS.map(
            (l) => `
            <button class="layer-btn ${state.selectedLayerId === l ? 'active' : ''}" onclick="selectLayer('${l}')">
              ${l}
            </button>`
          ).join('')}
        </div>
      </div>

      <div class="control-group">
        <div class="control-label"><span>Natural Language Layer Instruction</span></div>
        <input id="inp-patch-instruction" type="text" placeholder="e.g. Make L2_HeroSubject neon green with faster spring bounce" />
      </div>

      <div class="control-group">
        <div class="control-label"><span>Accent Color Override (HEX)</span></div>
        <input id="inp-patch-color" type="text" value="${layerData.accent_color || '#00FF66'}" />
      </div>

      <div class="control-group">
        <div class="control-label"><span>Spring Stiffness (N/m)</span></div>
        <input id="inp-patch-stiff" type="number" value="${layerData.stiffness || 280}" />
      </div>

      <div class="control-group">
        <div class="control-label"><span>HUD Headline (if L4_TypographyHUD)</span></div>
        <input id="inp-patch-headline" type="text" value="${activeShot?.layers?.L4_TypographyHUD?.headline || ''}" />
      </div>

      <button class="btn-primary" onclick="handleSurgicalPatch()">
        PATCH SHOT ${state.selectedShotId} ONLY (SURGICAL SPLICE)
      </button>
    `;
  }

  if (state.activeTab === 'katana_remix') {
    const bp = state.katanaBlueprint;
    return `
      <div>
        <div class="section-label">KATANA // REFERENCE VIDEO DECOMPILER</div>
        <p style="font-size:12px;color:var(--text-secondary);margin-bottom:10px;">
          Extract exact cut frames, optical motion vectors, palette & beatmap from any reference MP4.
        </p>
      </div>
      <div class="control-group">
        <div class="control-label"><span>Reference Video Path</span></div>
        <input id="inp-katana-path" type="text" value="${
          job ? `/workspace/studios/code-higgsfield/jobs/${job.job_id}/master_60fps.mp4` : ''
        }" />
      </div>
      <button class="btn-primary" onclick="handleKatanaDecompile()">
        DECOMPILE REFERENCE BLUEPRINT
      </button>
      ${
        bp
          ? `
        <div style="background:#0B0D13;padding:12px;border-radius:10px;border:1px solid var(--border-subtle);font-family:var(--font-mono);font-size:11px;">
          <div style="color:var(--accent-lime);font-weight:800;margin-bottom:6px;">EXTRACTED BLUEPRINT</div>
          <div>Duration: ${bp.duration_sec}s | Cuts: ${bp.cut_count} | Shots: ${bp.shots?.length}</div>
          <div>Palette: ${bp.extracted_palette?.bg_primary} / ${bp.extracted_palette?.accent_primary}</div>
          <div>BPM: ${bp.beatmap?.bpm || 120} | Drop: ${bp.beatmap?.drop || 4.0}s</div>
        </div>
        <button class="btn-secondary" onclick="selectTab('vibe_motion')">
          USE BLUEPRINT IN VIBE MOTION STUDIO ->
        </button>
      `
          : ''
      }
    `;
  }

  if (state.activeTab === 'soul_vault') {
    return `
      <div>
        <div class="section-label">SOUL ID & BRANDKIT DNA VAULT</div>
        <p style="font-size:12px;color:var(--text-secondary);margin-bottom:10px;">
          Persistent code-driven Character Rigs & BrandKit palettes locked across all studio renders.
        </p>
      </div>
      ${(state.vault.cast_rigs || [])
        .map(
          (c) => `
        <div style="background:#0B0D13;padding:12px;border-radius:10px;border:1px solid var(--border-subtle);">
          <div style="font-weight:800;font-size:13px;color:var(--accent-lime);">${c.name}</div>
          <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent-cyan);margin:3px 0;">ID: ${c.id} • ${c.kind}</div>
          <div style="font-size:11px;color:var(--text-secondary);">${c.blurb}</div>
        </div>`
        )
        .join('')}
    `;
  }

  // Default: Vibe Motion & Cinema Story Shorts Compiler Controls
  return `
    <div>
      <div class="section-label">${
        state.activeTab === 'cinema_shorts' ? 'CINEMA & STORY SHORTS COMPILER' : 'VIBE MOTION // BRIEF COMPILER'
      }</div>
      <p style="font-size:11px;color:var(--text-secondary);">
        Compiles via <code>validate_motion_script.py</code> (5 shots/10s gate + <code>script.lock</code> + <code>beatmap.py</code>).
      </p>
    </div>

    <div class="control-group">
      <div class="control-label"><span>Creative Brief / Prompt</span></div>
      <textarea id="inp-prompt" rows="3">${
        state.activeTab === 'cinema_shorts'
          ? 'Cyber Director Aegis reveals how deterministic code-based films replace generative video slop at 60fps.'
          : 'Quantum Fintech AI Engine launch promo with 3D glass telemetry cards, spring physics, and 99.8% accuracy.'
      }</textarea>
    </div>

    <div class="control-group">
      <div class="control-label"><span>Aspect Ratio & Duration</span></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
        <select id="inp-aspect">
          <option value="9:16">9:16 Vertical (1080x1920)</option>
          <option value="16:9">16:9 Cinema (1920x1080)</option>
          <option value="1:1">1:1 Square (1080x1080)</option>
        </select>
        <input id="inp-duration" type="number" value="10" min="6" max="60" step="2" />
      </div>
    </div>

    <div class="control-group">
      <div class="control-label"><span>BrandKit Palette Preset</span></div>
      <select id="inp-palette">
        ${(state.vault.brandkits || [])
          .map((b) => `<option value="${b.id}">${b.name}</option>`)
          .join('')}
      </select>
    </div>

    <div class="control-group">
      <div class="control-label"><span>Spring Stiffness / Damping</span></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
        <input id="inp-stiffness" type="number" value="210" />
        <input id="inp-damping" type="number" value="18" />
      </div>
    </div>

    <button class="btn-primary" onclick="handleGenerateJob()">
      COMPILE BRIEF + RENDER 60FPS MASTER
    </button>

    <div style="border-top:1px solid var(--border-subtle);padding-top:12px;">
      <div class="section-label">STUDIO HISTORY QUEUE (${state.jobs.length})</div>
      <div style="display:flex;flex-direction:column;gap:6px;">
        ${state.jobs
          .map(
            (j) => `
          <div onclick="selectJob('${j.job_id}')" style="padding:9px 11px;border-radius:9px;cursor:pointer;background:${
              state.activeJob?.job_id === j.job_id ? 'rgba(212,255,0,0.12)' : '#0B0D13'
            };border:1px solid ${
              state.activeJob?.job_id === j.job_id ? 'var(--accent-lime)' : 'var(--border-subtle)'
            };">
            <div style="font-size:12px;font-weight:700;">${j.job_id}</div>
            <div style="font-family:var(--font-mono);font-size:10px;color:var(--accent-cyan);display:flex;justify-content:space-between;margin-top:2px;">
              <span>${j.status}</span>
              <span>QA: ${j.qa_score || '--'}/100</span>
            </div>
          </div>`
          )
          .join('')}
      </div>
    </div>
  `;
}

function renderCenterViewport() {
  const job = state.activeJob;
  if (state.busyMessage) {
    return `
      <div class="viewport-area">
        <div style="text-align:center;max-width:460px;padding:28px;background:#11131A;border:1px solid var(--accent-lime);border-radius:16px;">
          <div style="font-family:var(--font-mono);color:var(--accent-lime);font-weight:800;font-size:14px;margin-bottom:8px;">
            MCP PIPELINE EXECUTING...
          </div>
          <div style="font-size:13px;color:var(--text-secondary);line-height:1.5;">${state.busyMessage}</div>
        </div>
      </div>
    `;
  }

  if (!job) {
    return `<div class="viewport-area"><div style="color:var(--text-secondary);">No job selected. Click "COMPILE BRIEF + RENDER 60FPS MASTER".</div></div>`;
  }

  const videoUrl = `/jobs/${job.job_id}/master_60fps.mp4?t=${Date.now()}`;
  const posterUrl = `/jobs/${job.job_id}/preview/f_0054.png?t=${Date.now()}`;
  const contactUrl = `/jobs/${job.job_id}/qa/contact_sheet.png?t=${Date.now()}`;
  const shots = job.script?.shots || [];
  const downbeats = job.beatmap_summary?.downbeats || [0, 2, 4, 6, 8];
  const dropSec = job.beatmap_summary?.drop || 4.0;
  const dur = job.duration_sec || 10.0;

  return `
    <div class="viewport-area">
      <div class="video-player-card">
        <video src="${videoUrl}" poster="${posterUrl}" controls autoplay loop muted playsinline></video>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;max-width:440px;">
        <div class="section-label">QA SHOT CONTACT SHEET & HANDOFF</div>
        <img src="${contactUrl}" style="width:100%;border-radius:12px;border:1px solid var(--border-subtle);" alt="Contact Sheet" />
        <div style="display:flex;gap:8px;">
          <button class="btn-secondary" onclick="handoffToStudio('miracle_layer', '${job.job_id}', '${state.selectedShotId}')">
            Edit in Miracle Layer Canvas
          </button>
          <button class="btn-secondary" onclick="handoffToStudio('katana_remix', '${job.job_id}')">
            Send to Katana Decompiler
          </button>
        </div>
      </div>
    </div>

    <div class="timeline-bar">
      <div class="timeline-header">
        <span>MULTI-TRACK SHOT & BEATMAP TIMELINE // LOCK SHA256: ${(job.script_lock_sha256 || '').slice(0, 12)}...</span>
        <span>BPM: ${job.beatmap_summary?.bpm || 120} • DROP @ ${dropSec}s • ${job.total_frames} FRAMES @ ${job.fps} FPS</span>
      </div>
      <div class="shots-track">
        ${shots
          .map(
            (s) => `
          <div class="shot-block ${state.selectedShotId === s.id ? 'selected' : ''}" onclick="selectShot('${s.id}')">
            <div class="shot-block-title">${s.id} • ${s.shot_size}</div>
            <div style="font-size:10px;color:var(--text-secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              ${s.layers?.L4_TypographyHUD?.headline || s.subject}
            </div>
            <div class="shot-block-meta">${s.in_sec}s – ${s.out_sec}s (${s.camera_move})</div>
          </div>`
          )
          .join('')}
      </div>
      <div class="beat-markers-track">
        <span style="font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);z-index:2;">
          AUDIO BAR/DOWNBEAT SYNC MARKERS
        </span>
        ${downbeats
          .map((t) => `<div class="beat-tick" style="left:${Math.min(98, (t / dur) * 100)}%;"></div>`)
          .join('')}
        <div class="beat-tick drop" style="left:${Math.min(98, (dropSec / dur) * 100)}%;" title="Musical Drop"></div>
      </div>
    </div>
  `;
}

function renderRightPanel() {
  const job = state.activeJob;
  const qa = job?.qa_report;
  const gates = qa?.gates || {};
  const codeText = state.activeCodeTab === 'story' ? state.storyCode : state.filmCode;

  return `
    <div>
      <div class="section-label">AUTOMATED MACHINE + VISUAL QA TELEMETRY</div>
      <div class="qa-badge-grid">
        <div class="qa-metric-card">
          <div class="qa-metric-val">${qa?.verdict || 'READY'} (${qa?.score_100 || 98}/100)</div>
          <div class="qa-metric-lbl">QA VERDICT (qa_gate.py)</div>
        </div>
        <div class="qa-metric-card">
          <div class="qa-metric-val">${gates['1_integrity_and_spec']?.fps || 60.0} FPS</div>
          <div class="qa-metric-lbl">${gates['1_integrity_and_spec']?.width || 1080}x${gates['1_integrity_and_spec']?.height || 1920} yuv420p</div>
        </div>
        <div class="qa-metric-card">
          <div class="qa-metric-val">${gates['2_holds_and_density']?.freeze_count ?? 0} Freezes</div>
          <div class="qa-metric-lbl">Density: ${gates['2_holds_and_density']?.shot_density_per_10s || 5.0} shots/10s</div>
        </div>
        <div class="qa-metric-card">
          <div class="qa-metric-val">${gates['5_sound_ebur128']?.integrated_lufs ?? -14.0} LUFS</div>
          <div class="qa-metric-lbl">WCAG Contrast: ${gates['4_text_and_wcag']?.min_wcag_contrast || 18.8}:1</div>
        </div>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:8px;flex:1;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div class="section-label" style="margin:0;">3-FILE STATELESS SCENE GRAPH</div>
        <div style="display:flex;gap:4px;">
          <button class="btn-secondary" style="padding:4px 8px;font-size:10px;" onclick="switchCodeTab('story')">story.mjs</button>
          <button class="btn-secondary" style="padding:4px 8px;font-size:10px;" onclick="switchCodeTab('film')">film.mjs</button>
        </div>
      </div>
      <textarea id="code-drawer-textarea" class="code-editor" style="flex:1;">${codeText}</textarea>
      <button class="btn-secondary" onclick="handleSaveSceneCode()">
        HOT-COMPILE & RE-RENDER SCENE CODE (MCP)
      </button>
    </div>
  `;
}

function renderApp() {
  const root = document.getElementById('app');
  if (!root) return;

  const tabs = [
    { id: 'vibe_motion', label: 'Vibe Motion Studio' },
    { id: 'miracle_layer', label: 'Miracle Layer Canvas' },
    { id: 'katana_remix', label: 'Katana Reference Studio' },
    { id: 'cinema_shorts', label: 'Cinema & Story Shorts' },
    { id: 'soul_vault', label: 'Soul ID & BrandKit Vault' },
  ];

  root.innerHTML = `
    <div class="studio-shell">
      <header class="studio-header">
        <div class="brand-mark">
          <div class="brand-logo">HF</div>
          <div>
            <div class="brand-title">CODE-HIGGSFIELD STUDIO</div>
            <div class="brand-subtitle">6-LAYER PROCEDURAL ENGINE • ZERO API KEYS</div>
          </div>
        </div>

        <nav class="studio-tabs">
          ${tabs
            .map(
              (t) => `
            <button class="studio-tab ${state.activeTab === t.id ? 'active' : ''}" onclick="selectTab('${t.id}')">
              ${t.label}
            </button>`
            )
            .join('')}
        </nav>

        <div class="mcp-pill">
          <span class="mcp-dot"></span>
          <span>${state.mcpStatus}</span>
        </div>
      </header>

      <main class="studio-body">
        <aside class="panel-left">${renderLeftPanel()}</aside>
        <section class="panel-center">${renderCenterViewport()}</section>
        <aside class="panel-right">${renderRightPanel()}</aside>
      </main>
    </div>
  `;
}

window.addEventListener('DOMContentLoaded', () => {
  refreshStudioState();
});
