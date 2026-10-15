/* Shared Studio Set Bar & Beat Selector for the 6-Page Found WarGames Studio Set
   Pages:
     01 / SCREEN STATES (wg-studio-screens.html)
     02 / JOHN WHITNEY  (wg-studio-whitney.html)  — Harmonic Differential Slit-Scan
     03 / KEN KNOWLTON  (wg-studio-knowlton.html) — Film Made of Stills / Multi-Scale Mosaic
     05 / FRIEDER NAKE  (wg-studio-nake.html)     — 5-Column Vertical 35mm Plotter Matrix
     06 / MANFRED MOHR  (wg-studio-mohr.html)     — 4D Hypercube Facet Lattice
     10 / CASEY REAS    (wg-studio-reas.html)     — Vector Flow-Field Tissue Assembly
   Zero emojis. Pure SVG & tracked monospace/serif museum typography.
*/
(() => {
  'use strict';

  const STUDIO_PAGES = [
    { num: '01', name: 'SCREEN STATES', sub: 'Infer Program from All Screens', href: 'wg-studio-screens.html' },
    { num: '02', name: 'JOHN WHITNEY',  sub: 'Harmonic Slit-Scan Orbits',      href: 'wg-studio-whitney.html' },
    { num: '03', name: 'KEN KNOWLTON',  sub: 'A Film Made of Stills',          href: 'wg-studio-knowlton.html' },
    { num: '05', name: 'FRIEDER NAKE',  sub: 'Vertical 35mm Plotter Matrix',   href: 'wg-studio-nake.html' },
    { num: '06', name: 'MANFRED MOHR',  sub: '4D Hypercube Cut Lattice',       href: 'wg-studio-mohr.html' },
    { num: '10', name: 'CASEY REAS',    sub: 'Flow-Field Tissue Assembly',     href: 'wg-studio-reas.html' },
  ];

  const EXTRA_LINKS = [
    { num: 'ST', name: '6-LENS STUDIO', sub: 'ASAL & 8 Cybernetic Species', href: 'found-wargames.html' },
    { num: 'MU', name: 'MUSEUM STAGE',  sub: 'Traveling Mask & Cast Grid',  href: 'found-wargames-museum.html' },
    { num: 'SB', name: 'SOUND BENCH',   sub: 'Bumblebee Spectrogram Lab',   href: 'bumblebee-dilemma.html' },
  ];

  const ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI'];

  function mount(opts = {}) {
    const theme = opts.theme || 'dark'; // 'dark' (#050505) or 'paper' (#f2ede2)
    const currentNum = opts.num || '02';
    const titleLeft = opts.titleLeft || '02 / JOHN WHITNEY';
    const promptCenter = opts.promptCenter || 'DRAG THE ORBIT TO CHANGE PHASE';

    const style = document.createElement('style');
    style.textContent = `
      .wgs-top{
        position:fixed;top:0;left:0;right:0;height:40px;z-index:80;
        display:flex;align-items:center;justify-content:space-between;
        padding:0 22px;
        font:400 10px/1 'IBM Plex Mono',ui-monospace,monospace;
        letter-spacing:.18em;text-transform:uppercase;
        pointer-events:none;
        transition:opacity .35s;
      }
      .wgs-top > *{pointer-events:auto}
      .wgs-top.theme-dark{
        color:rgba(239,233,221,.72);
        background:linear-gradient(180deg,rgba(5,5,5,.86) 0%,rgba(5,5,5,0) 100%);
      }
      .wgs-top.theme-paper{
        color:rgba(24,22,19,.75);
        background:linear-gradient(180deg,rgba(242,237,226,.92) 0%,rgba(242,237,226,0) 100%);
      }
      .wgs-pills{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
      .wgs-pill{
        text-decoration:none;padding:5px 9px;border:1px solid transparent;
        font:500 9.5px/1 'IBM Plex Mono',monospace;letter-spacing:.16em;
        transition:all .16s;cursor:pointer;background:none;
      }
      .theme-dark .wgs-pill{color:rgba(239,233,221,.58);border-color:rgba(239,233,221,.12);background:rgba(10,10,10,.55)}
      .theme-dark .wgs-pill:hover{color:#efe9dd;border-color:rgba(239,233,221,.4)}
      .theme-dark .wgs-pill.on{color:#050505;background:#e8c070;border-color:#e8c070}
      .theme-paper .wgs-pill{color:rgba(24,22,19,.62);border-color:rgba(24,22,19,.15);background:rgba(242,237,226,.75)}
      .theme-paper .wgs-pill:hover{color:#111;border-color:rgba(24,22,19,.45)}
      .theme-paper .wgs-pill.on{color:#f4f0e6;background:#181613;border-color:#181613}

      .wgs-beatbar{display:flex;align-items:center;gap:8px}
      .wgs-beat-lbl{
        font:italic 300 13px/1 'Fraunces',Georgia,serif;letter-spacing:.01em;text-transform:none;
        max-width:340px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
      }
      .theme-dark .wgs-beat-lbl{color:#efe9dd}
      .theme-paper .wgs-beat-lbl{color:#181613}

      .wgs-foot{
        position:fixed;bottom:0;left:0;right:0;height:48px;z-index:80;
        display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
        padding:0 28px;
        font:400 10.5px/1 'IBM Plex Mono',ui-monospace,monospace;
        letter-spacing:.22em;text-transform:uppercase;
        user-select:none;
      }
      .wgs-foot.theme-dark{
        color:rgba(239,233,221,.78);
        background:linear-gradient(0deg,rgba(5,5,5,.92) 0%,rgba(5,5,5,0) 100%);
      }
      .wgs-foot.theme-paper{
        color:rgba(24,22,19,.78);
        border-top:1px solid rgba(24,22,19,.12);
        background:rgba(242,237,226,.92);
      }
      .wgs-foot-left{display:flex;align-items:center;gap:14px}
      .wgs-foot-center{
        justify-self:center;opacity:.72;font-size:10px;letter-spacing:.24em;
        text-align:center;white-space:nowrap;
      }
      .wgs-foot-right{
        justify-self:end;display:flex;align-items:center;gap:14px;
      }
      .wgs-ico-btn{
        background:none;border:0;cursor:pointer;padding:6px;
        display:inline-flex;align-items:center;justify-content:center;
        color:inherit;opacity:.78;transition:opacity .15s,transform .15s;
      }
      .wgs-ico-btn:hover{opacity:1;transform:scale(1.08)}
      .wgs-cut-strip{
        display:inline-flex;align-items:center;gap:6px;
        font-size:9px;letter-spacing:.15em;opacity:.82;
      }
      @media (max-width:860px){
        .wgs-beat-lbl{display:none}
        .wgs-foot{grid-template-columns:auto 1fr auto;padding:0 14px;gap:8px}
        .wgs-foot-center{font-size:8.5px;letter-spacing:.14em;overflow:hidden;text-overflow:ellipsis}
      }
    `;
    document.head.appendChild(style);

    // Top Studio Set Bar
    const top = document.createElement('header');
    top.className = `wgs-top theme-${theme}`;
    top.innerHTML = `
      <nav class="wgs-pills" aria-label="Studio Set Pages">
        ${STUDIO_PAGES.map(p => `
          <a class="wgs-pill${p.num === currentNum ? ' on' : ''}" href="${p.href}" title="${p.num} / ${p.name} — ${p.sub}">
            ${p.num} · ${p.name}
          </a>
        `).join('')}
        <span style="opacity:.25;padding:0 3px">|</span>
        ${EXTRA_LINKS.map(p => `
          <a class="wgs-pill" href="${p.href}" title="${p.sub}">${p.name}</a>
        `).join('')}
      </nav>
      <div class="wgs-beatbar">
        <button class="wgs-pill" id="wgsPrevBeat" title="Previous Scene Beat (Left Arrow)">PREV</button>
        <span class="wgs-beat-lbl" id="wgsBeatLabel">Book I · Silo Refusal</span>
        <button class="wgs-pill" id="wgsNextBeat" title="Next Scene Beat (Right Arrow)">NEXT</button>
        <button class="wgs-pill" id="wgsSoundToggle" title="Toggle 1983 / Archive Voice Audio">SOUND: ON</button>
      </div>
    `;
    document.body.appendChild(top);

    // Bottom Museum Footer (matching the 5 reference images)
    const foot = document.createElement('footer');
    foot.className = `wgs-foot theme-${theme}`;
    foot.innerHTML = `
      <div class="wgs-foot-left">
        <span id="wgsTitleLeft">${titleLeft}</span>
      </div>
      <div class="wgs-foot-center" id="wgsPromptCenter">${promptCenter}</div>
      <div class="wgs-foot-right">
        <span class="wgs-cut-strip" id="wgsStatusRight">8 CUTS SIMULTANEOUS</span>
        <button class="wgs-ico-btn" id="wgsPlayPauseBtn" title="Pause / Resume (Space)">
          <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" id="wgsPlayPauseSvg">
            <rect x="3" y="2" width="3.2" height="12"/>
            <rect x="9.8" y="2" width="3.2" height="12"/>
          </svg>
        </button>
        <button class="wgs-ico-btn" id="wgsResetBtn" title="Reset View / Phase (R)">
          <svg width="16" height="16" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3.5 9a5.5 5.5 0 1 0 1.4-3.7"/>
            <polyline points="3.2 2.4 3.4 5.6 6.6 5.4"/>
          </svg>
        </button>
      </div>
    `;
    document.body.appendChild(foot);

    let playing = true;
    let soundOn = true;
    const playPauseBtn = document.getElementById('wgsPlayPauseBtn');
    const playPauseSvg = document.getElementById('wgsPlayPauseSvg');
    const resetBtn = document.getElementById('wgsResetBtn');
    const soundBtn = document.getElementById('wgsSoundToggle');

    function setPlayingUI(p) {
      playing = p;
      if (playPauseSvg) {
        playPauseSvg.innerHTML = playing
          ? '<rect x="3" y="2" width="3.2" height="12"/><rect x="9.8" y="2" width="3.2" height="12"/>'
          : '<polygon points="4,2 14,8 4,14"/>';
      }
    }

    playPauseBtn.onclick = () => {
      setPlayingUI(!playing);
      if (opts.onTogglePlay) opts.onTogglePlay(playing);
    };
    resetBtn.onclick = () => {
      if (opts.onReset) opts.onReset();
    };
    soundBtn.onclick = () => {
      soundOn = !soundOn;
      soundBtn.textContent = soundOn ? 'SOUND: ON' : 'SOUND: MUTE';
      if (opts.onToggleSound) opts.onToggleSound(soundOn);
    };
    document.getElementById('wgsPrevBeat').onclick = () => {
      if (opts.onPrevBeat) opts.onPrevBeat();
    };
    document.getElementById('wgsNextBeat').onclick = () => {
      if (opts.onNextBeat) opts.onNextBeat();
    };

    window.addEventListener('keydown', e => {
      if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA')) return;
      if (e.key === ' ') {
        e.preventDefault();
        playPauseBtn.click();
      } else if (e.key === 'ArrowRight') {
        if (opts.onNextBeat) opts.onNextBeat();
      } else if (e.key === 'ArrowLeft') {
        if (opts.onPrevBeat) opts.onPrevBeat();
      } else if (e.key === 'r' || e.key === 'R') {
        resetBtn.click();
      }
    });

    return {
      setBeatLabel(txt) {
        const el = document.getElementById('wgsBeatLabel');
        if (el) el.textContent = txt;
      },
      setPrompt(txt) {
        const el = document.getElementById('wgsPromptCenter');
        if (el) el.textContent = txt;
      },
      setStatus(txt) {
        const el = document.getElementById('wgsStatusRight');
        if (el) el.textContent = txt;
      },
      setPlaying: setPlayingUI,
      ROMAN,
    };
  }

  window.WGStudioNav = { mount, STUDIO_PAGES, ROMAN };
})();
