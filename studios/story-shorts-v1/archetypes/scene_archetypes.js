window.StudioArchetypes = (function() {
  const { spring, easeOutExpo, clamp } = window.StudioRig;

  function renderHeaderHUD(frame, beatIndex, beat) {
    const pulse = 0.55 + 0.45 * Math.sin(frame * 0.18);
    const timeSec = (frame / 60).toFixed(2);
    return `
      <div class="hud-top">
        <div class="hud-left">
          <span class="rec-dot" style="opacity:${pulse.toFixed(2)}"></span>
          <span class="hud-tag">KINETIC ARCHITECT // CH-01</span>
        </div>
        <div class="hud-right">
          <span class="hud-frame">BEAT 0${beatIndex + 1}/04</span>
          <span class="hud-tc">${timeSec}s [F:${String(frame).padStart(3, '0')}]</span>
        </div>
      </div>
    `;
  }

  function renderHostDock(frame, beat) {
    const dockIn = spring(frame, beat.start_frame, { stiffness: 200, damping: 20 });
    const wave1 = 14 + Math.abs(Math.sin(frame * 0.35)) * 28;
    const wave2 = 14 + Math.abs(Math.cos(frame * 0.42)) * 36;
    const wave3 = 14 + Math.abs(Math.sin(frame * 0.28 + 1.2)) * 24;
    return `
      <div class="host-dock" style="transform: translateY(${(1 - dockIn) * 40}px); opacity: ${clamp(dockIn, 0, 1)}">
        <div class="host-avatar">
          <span class="avatar-initial">K</span>
        </div>
        <div class="host-meta">
          <div class="host-name">KAEL // SYSTEMS DISSECTOR</div>
          <div class="host-sub">${beat.archetype.replace('Archetype_', '')}</div>
        </div>
        <div class="voice-meter">
          <span style="height:${wave1.toFixed(0)}px"></span>
          <span style="height:${wave2.toFixed(0)}px"></span>
          <span style="height:${wave3.toFixed(0)}px"></span>
          <span style="height:${wave1.toFixed(0)}px"></span>
        </div>
      </div>
    `;
  }

  // ARCHETYPE 01: HOOK TENSION (Expanded 500x500 Radial Gauge so text never clips ring)
  function Archetype_01_HookTension(frame, beat) {
    const f0 = beat.start_frame;
    const s1 = spring(frame, f0 + 2, { stiffness: 240, damping: 16 });
    const s2 = spring(frame, f0 + 14, { stiffness: 210, damping: 17 });
    const countProg = easeOutExpo(clamp((frame - (f0 + 4)) / 48, 0, 1));
    const currentVal = Math.round(beat.sub_metric.value * countProg);

    const radius = 205;
    const circum = 2 * Math.PI * radius;
    const dashOffset = circum * (1 - (currentVal / 100) * 0.97);

    return `
      <div class="archetype-stage">
        <div class="kinetic-header" style="transform: translateY(${(1 - s1) * 55}px) scale(${0.92 + 0.08 * s1}); opacity: ${clamp(s1, 0, 1)}">
          <div class="eyebrow-pill">RETENTION AUTOPSY // 0-3s WINDOW</div>
          <div class="punch-line-1">${beat.punch_words[0]}</div>
          <div class="punch-line-2 accent-red">${beat.punch_words[1]}</div>
        </div>

        <div class="focal-card gauge-card" style="transform: translateY(${(1 - s2) * 65}px) scale(${0.88 + 0.12 * s2}); opacity: ${clamp(s2, 0, 1)}">
          <div class="gauge-ring-wrap">
            <svg width="480" height="480" viewBox="0 0 480 480" class="gauge-svg">
              <circle cx="240" cy="240" r="${radius}" stroke="rgba(244,241,234,0.10)" stroke-width="26" fill="none"/>
              <circle cx="240" cy="240" r="${radius}" stroke="#FF3B30" stroke-width="26" fill="none"
                stroke-linecap="round"
                stroke-dasharray="${circum.toFixed(1)}"
                stroke-dashoffset="${dashOffset.toFixed(1)}"
                transform="rotate(-90 240 240)"/>
            </svg>
            <div class="gauge-center">
              <div class="gauge-num">${currentVal}<span class="gauge-unit">%</span></div>
            </div>
          </div>
          <div class="gauge-footer-badge">${beat.sub_metric.label}</div>
        </div>
      </div>
    `;
  }

  // ARCHETYPE 02: SPLIT COMPARE
  function Archetype_02_SplitCompare(frame, beat) {
    const f0 = beat.start_frame;
    const sHead = spring(frame, f0 + 2, { stiffness: 230, damping: 18 });
    const sBad = spring(frame, f0 + 8, { stiffness: 210, damping: 16 });
    const sGood = spring(frame, f0 + 22, { stiffness: 230, damping: 15 });

    return `
      <div class="archetype-stage">
        <div class="kinetic-header" style="transform: translateY(${(1 - sHead) * 45}px); opacity: ${clamp(sHead, 0, 1)}">
          <div class="eyebrow-pill">ARCHITECTURE DELTA</div>
          <div class="punch-line-1">${beat.punch_words[0]}</div>
          <div class="punch-line-2 accent-gold">${beat.punch_words[1]}</div>
        </div>

        <div class="compare-stack">
          <div class="compare-card card-bad" style="transform: translateX(${(1 - sBad) * -80}px) scale(${0.92 + 0.08 * sBad}); opacity: ${clamp(sBad, 0, 1)}">
            <div class="card-badge badge-red">REJECTED // ${beat.compare_cards.bad.tag}</div>
            <div class="card-stat">${beat.compare_cards.bad.stat}</div>
            <div class="card-desc">${beat.compare_cards.bad.flaw}</div>
          </div>

          <div class="compare-card card-good" style="transform: translateX(${(1 - sGood) * 80}px) scale(${0.92 + 0.08 * sGood}); opacity: ${clamp(sGood, 0, 1)}">
            <div class="card-badge badge-green">LOCKED // ${beat.compare_cards.good.tag}</div>
            <div class="card-stat accent-emerald">${beat.compare_cards.good.stat}</div>
            <div class="card-desc">${beat.compare_cards.good.edge}</div>
          </div>
        </div>
      </div>
    `;
  }

  // ARCHETYPE 03: NODE ARCHITECTURE
  function Archetype_03_NodeArchitecture(frame, beat) {
    const f0 = beat.start_frame;
    const sHead = spring(frame, f0 + 2, { stiffness: 230, damping: 18 });

    const nodesHtml = beat.nodes.map((n, idx) => {
      const nodeSpring = spring(frame, f0 + 8 + idx * 16, { stiffness: 220, damping: 16 });
      const activeGlow = frame >= (f0 + 10 + idx * 16) ? "node-active" : "";
      return `
        <div class="arch-node ${activeGlow}" style="transform: translateY(${(1 - nodeSpring) * 48}px) scale(${0.92 + 0.08 * nodeSpring}); opacity: ${clamp(nodeSpring, 0, 1)}">
          <div class="node-step">${n.step}</div>
          <div class="node-body">
            <div class="node-title">${n.title}</div>
            <div class="node-ms">${n.ms}</div>
          </div>
          <div class="node-status-dot"></div>
        </div>
      `;
    }).join('');

    return `
      <div class="archetype-stage">
        <div class="kinetic-header" style="transform: translateY(${(1 - sHead) * 45}px); opacity: ${clamp(sHead, 0, 1)}">
          <div class="eyebrow-pill">SYNCHRONIZED PIPELINE</div>
          <div class="punch-line-1">${beat.punch_words[0]}</div>
          <div class="punch-line-2 accent-emerald">${beat.punch_words[1]}</div>
        </div>
        <div class="nodes-container">
          ${nodesHtml}
        </div>
      </div>
    `;
  }

  // ARCHETYPE 04: METRIC PAYOFF
  function Archetype_04_MetricPayoff(frame, beat) {
    const f0 = beat.start_frame;
    const sHead = spring(frame, f0 + 2, { stiffness: 240, damping: 17 });

    const barsHtml = beat.chart_bars.map((b, idx) => {
      const bSpring = spring(frame, f0 + 8 + idx * 14, { stiffness: 200, damping: 16 });
      const widthPct = clamp(b.pct * bSpring, 0, 100);
      const valNum = Math.round(b.pct * clamp(bSpring, 0, 1));
      return `
        <div class="bar-row" style="opacity: ${clamp(bSpring * 1.5, 0, 1)}">
          <div class="bar-meta">
            <span class="bar-label">${b.label}</span>
            <span class="bar-val" style="color:${b.color}">${valNum}%</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width:${widthPct.toFixed(1)}%; background:${b.color}"></div>
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="archetype-stage">
        <div class="kinetic-header" style="transform: translateY(${(1 - sHead) * 45}px); opacity: ${clamp(sHead, 0, 1)}">
          <div class="eyebrow-pill">VERIFIED OUTPUT BENCHMARK</div>
          <div class="punch-line-1">${beat.punch_words[0]}</div>
          <div class="punch-line-2 accent-emerald">${beat.punch_words[1]}</div>
        </div>
        <div class="focal-card payoff-card">
          ${barsHtml}
        </div>
      </div>
    `;
  }

  return {
    renderHeaderHUD,
    renderHostDock,
    Archetype_01_HookTension,
    Archetype_02_SplitCompare,
    Archetype_03_NodeArchitecture,
    Archetype_04_MetricPayoff
  };
})();
