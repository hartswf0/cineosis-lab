/* Shared Studio Set Bar, Beat Selector, Multi-Deck Video/Audio Preloader,
   and Line-by-Line Spoken Dialogue Sequencer (`WGStudioNav` + `WGStudioEngine`)
   Pages:
     00 / STUDIO INDEX  (wargames-studio.html)
     01 / SCREEN STATES (wg-studio-screens.html)  — Reverse-Engineered WOPR/IMSAI Program
     02 / JOHN WHITNEY  (wg-studio-whitney.html)  — Harmonic Differential Slit-Scan
     03 / KEN KNOWLTON  (wg-studio-knowlton.html) — Film Made of Stills / Multi-Scale Mosaic
     05 / FRIEDER NAKE  (wg-studio-nake.html)     — 5-Column Vertical 35mm Plotter Matrix
     06 / MANFRED MOHR  (wg-studio-mohr.html)     — 6-Critic Hypercube Dialectical Resolver
     10 / CASEY REAS    (wg-studio-reas.html)     — Conversational Attractor Tissue
   Zero emojis. Pure SVG & tracked monospace/serif museum typography.
*/
(() => {
  'use strict';

  const STUDIO_PAGES = [
    { num: '00', name: 'STUDIO INDEX',  sub: 'All 12 Studios Together',        href: 'wargames-studio.html' },
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
    { num: 'VJ', name: 'VJ COUCH',      sub: 'Dual-Deck TV + Phone Rig',    href: 'vj-wargames.html' },
  ];

  const ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI'];
  const IS_PAGES = typeof location !== 'undefined' && (location.hostname.endsWith('github.io') || location.protocol === 'file:');

  function escHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderHighlightedText(text, hlIndices, cls) {
    const words = String(text || '').trim().split(/\s+/).filter(Boolean);
    if (!words.length) return '';
    const hlSet = new Set(Array.isArray(hlIndices) ? hlIndices : []);
    return words.map((w, i) => hlSet.has(i) ? `<span class="${cls}">${escHtml(w)}</span>` : escHtml(w)).join(' ');
  }

  function resolveVideoUrl(u) {
    if (!u) return '';
    if (typeof u === 'string') {
      if (IS_PAGES && u.startsWith('/api/')) return '';
      if (IS_PAGES && u.startsWith('/media/')) return '';
      return u;
    }
    if (!IS_PAGES) {
      return u.media_url || u.static_clip || u.video || '';
    }
    // On GitHub Pages, prefer local clips/wg_XXX.mp4 or direct R2/HTTPS video URL
    if (u.static_clip) return u.static_clip;
    if (u.video && !String(u.video).startsWith('/api/') && !String(u.video).startsWith('/media/')) {
      return u.video;
    }
    if (u.id && /^wg_\d+$/.test(u.id)) return `clips/${u.id}.mp4`;
    return '';
  }

  function resolveAudioUrl(url) {
    if (!url) return '';
    if (IS_PAGES && String(url).startsWith('/api/')) return '';
    return url;
  }

  let currentNavInstance = null;

  function mount(opts = {}) {
    const theme = opts.theme || 'dark';
    const currentNum = opts.num || '02';
    const titleLeft = opts.titleLeft || '02 / JOHN WHITNEY';
    const promptCenter = opts.promptCenter || 'DRAG THE ORBIT TO CHANGE PHASE';

    if (!document.getElementById('wgs-shared-styles')) {
      const style = document.createElement('style');
      style.id = 'wgs-shared-styles';
      style.textContent = `
        .wgs-top{
          position:fixed;top:0;left:0;right:0;height:40px;z-index:90;
          display:flex;align-items:center;justify-content:space-between;
          padding:0 18px;
          font:400 10px/1 'IBM Plex Mono',ui-monospace,monospace;
          letter-spacing:.15em;text-transform:uppercase;
          pointer-events:none;
          transition:opacity .35s;
        }
        .wgs-top > *{pointer-events:auto}
        .wgs-top.theme-dark{
          color:rgba(239,233,221,.78);
          background:linear-gradient(180deg,rgba(5,5,5,.92) 0%,rgba(5,5,5,.65) 75%,rgba(5,5,5,0) 100%);
        }
        .wgs-top.theme-paper{
          color:rgba(24,22,19,.82);
          background:linear-gradient(180deg,rgba(242,237,226,.95) 0%,rgba(242,237,226,.75) 75%,rgba(242,237,226,0) 100%);
        }
        .wgs-pills{display:flex;align-items:center;gap:3px;flex-wrap:wrap}
        .wgs-pill{
          text-decoration:none;padding:4px 8px;border:1px solid transparent;
          font:500 9px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;
          transition:all .15s;cursor:pointer;background:none;text-transform:uppercase;
        }
        .theme-dark .wgs-pill{color:rgba(239,233,221,.62);border-color:rgba(239,233,221,.14);background:rgba(10,10,10,.65)}
        .theme-dark .wgs-pill:hover{color:#efe9dd;border-color:rgba(239,233,221,.45)}
        .theme-dark .wgs-pill.on{color:#050505;background:#e8c070;border-color:#e8c070;font-weight:600}
        .theme-dark .wgs-pill.mode-on{color:#050505;background:#45b1ff;border-color:#45b1ff;font-weight:600}
        .theme-paper .wgs-pill{color:rgba(24,22,19,.66);border-color:rgba(24,22,19,.16);background:rgba(242,237,226,.82)}
        .theme-paper .wgs-pill:hover{color:#111;border-color:rgba(24,22,19,.48)}
        .theme-paper .wgs-pill.on{color:#f4f0e6;background:#181613;border-color:#181613;font-weight:600}
        .theme-paper .wgs-pill.mode-on{color:#fff;background:#d8341b;border-color:#d8341b;font-weight:600}

        .wgs-beatbar{display:flex;align-items:center;gap:5px}
        .wgs-beat-lbl{
          font:italic 400 12.5px/1 'Fraunces',Georgia,serif;letter-spacing:.01em;text-transform:none;
          max-width:250px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
          padding:0 4px;
        }
        .theme-dark .wgs-beat-lbl{color:#efe9dd}
        .theme-paper .wgs-beat-lbl{color:#181613}

        /* SPOKEN LINE & TAKE SEQUENCER DOCK */
        .wgs-linedock{
          position:fixed;left:0;right:0;bottom:44px;z-index:85;
          padding:7px 18px 8px;
          transition:transform .24s cubic-bezier(.22,1,.36,1), opacity .22s;
          font-family:'IBM Plex Mono',ui-monospace,monospace;
        }
        .wgs-linedock.collapsed{
          transform:translateY(calc(100% + 4px));
          opacity:0;
          pointer-events:none;
        }
        .wgs-linedock.theme-dark{
          background:rgba(7,8,11,.92);
          border-top:1px solid rgba(232,192,112,.22);
          backdrop-filter:blur(10px);
          color:#efe9dd;
        }
        .wgs-linedock.theme-paper{
          background:rgba(244,239,229,.94);
          border-top:1px solid rgba(24,22,19,.18);
          backdrop-filter:blur(10px);
          color:#181613;
        }
        .wgs-ld-head{
          display:flex;align-items:center;justify-content:space-between;gap:12px;
          margin-bottom:6px;font-size:9px;letter-spacing:.14em;text-transform:uppercase;
        }
        .wgs-ld-modes{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
        .wgs-ld-status{display:flex;align-items:center;gap:10px;opacity:.85}
        .wgs-ld-strip{
          display:grid;
          grid-auto-flow:column;
          grid-auto-columns:minmax(255px, 1fr);
          gap:7px;
          overflow-x:auto;
          padding-bottom:2px;
          scrollbar-width:thin;
        }
        .wgs-turn-card{
          position:relative;
          padding:6px 9px 7px;
          border:1px solid rgba(150,150,150,.22);
          cursor:pointer;
          transition:border-color .15s, background .15s, transform .15s;
          display:flex;flex-direction:column;gap:4px;
          overflow:hidden;
        }
        .theme-dark .wgs-turn-card{background:rgba(15,17,22,.82);border-color:rgba(239,233,221,.13)}
        .theme-dark .wgs-turn-card:hover{border-color:rgba(232,192,112,.45)}
        .theme-dark .wgs-turn-card.active{border-color:#e8c070;background:rgba(232,192,112,.09);box-shadow:0 0 18px rgba(232,192,112,.12)}
        .theme-paper .wgs-turn-card{background:rgba(255,252,245,.86);border-color:rgba(24,22,19,.15)}
        .theme-paper .wgs-turn-card:hover{border-color:rgba(24,22,19,.45)}
        .theme-paper .wgs-turn-card.active{border-color:#d8341b;background:rgba(216,52,27,.06);box-shadow:0 2px 12px rgba(216,52,27,.1)}

        .wgs-tc-top{
          display:flex;align-items:center;justify-content:space-between;gap:6px;
          font-size:8.5px;letter-spacing:.12em;text-transform:uppercase;
        }
        .wgs-tc-who{display:flex;align-items:center;gap:5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .wgs-tc-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
        .wgs-tc-fulc{
          padding:1px 4px;font-size:7.5px;letter-spacing:.1em;
          background:rgba(232,192,112,.2);color:#e8c070;border:1px solid rgba(232,192,112,.45);
        }
        .theme-paper .wgs-tc-fulc{background:rgba(216,52,27,.12);color:#d8341b;border-color:rgba(216,52,27,.4)}
        .wgs-tc-1983{
          font:400 10.5px/1.3 'IBM Plex Sans',system-ui,sans-serif;
          display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;
        }
        .wgs-tc-arch{
          font:italic 400 10.5px/1.3 'Fraunces',Georgia,serif;
          opacity:.92;
          display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;
        }
        .theme-dark .wgs-tc-arch{color:#77e4b6}
        .theme-paper .wgs-tc-arch{color:#0b6b45}
        .wgs-hl{
          padding:0 3px;border-radius:2px;font-weight:600;
          background:rgba(69,177,255,.22);color:#6bc5ff;
        }
        .theme-paper .wgs-hl{background:rgba(20,108,180,.15);color:#0d528a}
        .wgs-ha{
          padding:0 3px;border-radius:2px;font-weight:600;font-style:normal;
          background:rgba(232,192,112,.24);color:#ffd678;
        }
        .theme-paper .wgs-ha{background:rgba(216,52,27,.15);color:#b0230d}
        .wgs-tc-foot{
          display:flex;align-items:center;justify-content:space-between;gap:6px;
          font-size:8px;letter-spacing:.1em;text-transform:uppercase;opacity:.85;
          margin-top:1px;
        }
        .wgs-tc-film{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:145px}
        .wgs-tc-takes{display:flex;align-items:center;gap:2px;flex-shrink:0}
        .wgs-tk-btn{
          border:1px solid rgba(150,150,150,.3);background:none;color:inherit;
          font:600 7.5px/1 'IBM Plex Mono',monospace;padding:2px 4px;cursor:pointer;
          letter-spacing:.06em;transition:all .12s;
        }
        .wgs-tk-btn:hover{border-color:currentColor}
        .theme-dark .wgs-tk-btn.on{background:#e8c070;color:#050505;border-color:#e8c070}
        .theme-paper .wgs-tk-btn.on{background:#181613;color:#f4f0e6;border-color:#181613}
        .wgs-tc-prog{
          position:absolute;left:0;bottom:0;height:2px;width:0%;
          transition:width .08s linear;
        }
        .wgs-tc-prog.phase-1983{background:#45b1ff}
        .wgs-tc-prog.phase-arch{background:#e8c070}

        .wgs-foot{
          position:fixed;bottom:0;left:0;right:0;height:44px;z-index:90;
          display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
          padding:0 22px;
          font:400 10px/1 'IBM Plex Mono',ui-monospace,monospace;
          letter-spacing:.2em;text-transform:uppercase;
          user-select:none;
        }
        .wgs-foot.theme-dark{
          color:rgba(239,233,221,.82);
          background:rgba(5,5,5,.94);
          border-top:1px solid rgba(239,233,221,.08);
        }
        .wgs-foot.theme-paper{
          color:rgba(24,22,19,.82);
          border-top:1px solid rgba(24,22,19,.14);
          background:rgba(242,237,226,.95);
        }
        .wgs-foot-left{display:flex;align-items:center;gap:12px}
        .wgs-foot-center{
          justify-self:center;opacity:.82;font-size:9.5px;letter-spacing:.2em;
          text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:46vw;
        }
        .wgs-foot-right{
          justify-self:end;display:flex;align-items:center;gap:10px;
        }
        .wgs-ico-btn{
          background:none;border:0;cursor:pointer;padding:5px;
          display:inline-flex;align-items:center;justify-content:center;
          color:inherit;opacity:.8;transition:opacity .15s,transform .15s;
        }
        .wgs-ico-btn:hover{opacity:1;transform:scale(1.08)}
        .wgs-cut-strip{
          display:inline-flex;align-items:center;gap:6px;
          font-size:8.5px;letter-spacing:.14em;opacity:.85;
        }
        @media (max-width:920px){
          .wgs-beat-lbl{display:none}
          .wgs-foot{grid-template-columns:auto 1fr auto;padding:0 12px;gap:6px}
          .wgs-foot-center{font-size:8px;letter-spacing:.12em}
        }
      `;
      document.head.appendChild(style);
    }

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
        <span style="opacity:.25;padding:0 2px">|</span>
        ${EXTRA_LINKS.map(p => `
          <a class="wgs-pill" href="${p.href}" title="${p.sub}">${p.name}</a>
        `).join('')}
      </nav>
      <div class="wgs-beatbar">
        <button class="wgs-pill" id="wgsPrevBeat" title="Previous Scene Beat (Left Arrow)">PREV</button>
        <span class="wgs-beat-lbl" id="wgsBeatLabel">Book I · Silo Refusal</span>
        <button class="wgs-pill" id="wgsNextBeat" title="Next Scene Beat (Right Arrow)">NEXT</button>
        <button class="wgs-pill on" id="wgsLinesToggle" title="Toggle Line-by-Line Spoken Dialogue & 3-Take Sequencer (L)">LINES: OPEN</button>
        <button class="wgs-pill on" id="wgsSoundToggle" title="Toggle 1983 / Archive Spoken Audio (M)">SOUND: ON</button>
      </div>
    `;
    document.body.appendChild(top);

    // Line-by-Line Spoken Dialogue & Take Sequencer Dock
    const lineDock = document.createElement('section');
    lineDock.className = `wgs-linedock theme-${theme}${opts.linesCollapsed ? ' collapsed' : ''}`;
    lineDock.id = 'wgsLineDock';
    lineDock.innerHTML = `
      <div class="wgs-ld-head">
        <div class="wgs-ld-modes">
          <span style="opacity:.65;margin-right:4px">LINE PACING:</span>
          <button class="wgs-pill mode-on" data-wgs-mode="duet" title="For each spoken line in the beat: 1983 character speaks -> answered immediately by that line's chosen Archival Spoken Take">CALL &amp; ANSWER (LINE DUET)</button>
          <button class="wgs-pill" data-wgs-mode="archive" title="Every spoken line in the scene is spoken back-to-back by its assigned Archival Speaker Take">ARCHIVE CAST (ALL LINES)</button>
          <button class="wgs-pill" data-wgs-mode="1983" title="Continuous 1983 scene audio while all visual cuts pace through f1-f8">1983 SCENE VOICE</button>
          <button class="wgs-pill" data-wgs-mode="overlay" title="Simultaneous 1983 + Archival Line Voice">DUAL OVERLAY</button>
          <span style="opacity:.25;padding:0 3px">|</span>
          <button class="wgs-pill on" id="wgsAutoNextBtn" title="Automatically advance to the next beat when all spoken lines in the current beat complete">AUTO-CHAIN: ON</button>
        </div>
        <div class="wgs-ld-status">
          <span id="wgsPreloadBadge">PRELOAD: WARMING DECKS</span>
          <span id="wgsActiveVoiceBadge">VOICE: READY</span>
        </div>
      </div>
      <div class="wgs-ld-strip" id="wgsLineStrip"></div>
    `;
    document.body.appendChild(lineDock);

    // Bottom Museum Footer
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
    let linesOpen = !opts.linesCollapsed;
    const playPauseBtn = document.getElementById('wgsPlayPauseBtn');
    const playPauseSvg = document.getElementById('wgsPlayPauseSvg');
    const resetBtn = document.getElementById('wgsResetBtn');
    const soundBtn = document.getElementById('wgsSoundToggle');
    const linesBtn = document.getElementById('wgsLinesToggle');

    function setPlayingUI(p) {
      playing = p;
      if (playPauseSvg) {
        playPauseSvg.innerHTML = playing
          ? '<rect x="3" y="2" width="3.2" height="12"/><rect x="9.8" y="2" width="3.2" height="12"/>'
          : '<polygon points="4,2 14,8 4,14"/>';
      }
    }

    function setLinesOpen(open) {
      linesOpen = open;
      lineDock.classList.toggle('collapsed', !linesOpen);
      linesBtn.classList.toggle('on', linesOpen);
      linesBtn.textContent = linesOpen ? 'LINES: OPEN' : 'LINES: HIDE';
    }

    linesBtn.onclick = () => setLinesOpen(!linesOpen);

    playPauseBtn.onclick = () => {
      setPlayingUI(!playing);
      if (opts.onTogglePlay) opts.onTogglePlay(playing);
      if (currentNavInstance && currentNavInstance._engine) {
        currentNavInstance._engine.setPlaying(playing);
      }
    };
    resetBtn.onclick = () => {
      if (opts.onReset) opts.onReset();
    };
    soundBtn.onclick = () => {
      soundOn = !soundOn;
      soundBtn.textContent = soundOn ? 'SOUND: ON' : 'SOUND: MUTE';
      soundBtn.classList.toggle('on', soundOn);
      if (opts.onToggleSound) opts.onToggleSound(soundOn);
      if (currentNavInstance && currentNavInstance._engine) {
        currentNavInstance._engine.setSound(soundOn);
      }
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
      } else if (e.key === 'l' || e.key === 'L') {
        linesBtn.click();
      } else if (e.key === 'm' || e.key === 'M') {
        soundBtn.click();
      } else if (e.key === '1' || e.key === '2' || e.key === '3') {
        if (currentNavInstance && currentNavInstance._engine) {
          currentNavInstance._engine.setActiveTurnTake(parseInt(e.key, 10) - 1);
        }
      }
    });

    const api = {
      _engine: null,
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
      setLinesOpen,
      ROMAN,
    };
    currentNavInstance = api;
    return api;
  }

  /* ==========================================================================
     WGStudioEngine — Shared Multi-Deck Video/Audio Preloader & Line Sequencer
     ========================================================================== */
  function createEngine(cfg = {}) {
    const cutKeys = cfg.cutKeys || ['1983', 'synthesis', 'clip', 'vjepa', 'blip', 'cineosis', 'trurl', 'klapaucius', 'murch', 'novelty'];
    const nav = cfg.nav || currentNavInstance;

    // Hidden container for preloaded <video> and <audio> decks
    let poolEl = document.getElementById('wgs-media-pool');
    if (!poolEl) {
      poolEl = document.createElement('div');
      poolEl.id = 'wgs-media-pool';
      poolEl.style.cssText = 'position:fixed;left:-9999px;top:-9999px;width:320px;height:180px;overflow:hidden;pointer-events:none;opacity:0;';
      document.body.appendChild(poolEl);
    }

    // Double-buffered video deck per cutKey + 'take_video' for the currently speaking archival take
    const allDeckKeys = [...new Set([...cutKeys, 'take_video'])];
    const videoDecks = {};
    allDeckKeys.forEach(k => {
      const makeVid = () => {
        const v = document.createElement('video');
        v.muted = true;
        v.playsInline = true;
        v.preload = 'auto';
        v.width = 320;
        v.height = 180;
        if (!IS_PAGES) v.crossOrigin = 'anonymous';
        poolEl.appendChild(v);
        return v;
      };
      videoDecks[k] = {
        slots: [makeVid(), makeVid()],
        activeSlot: 0,
        activeUnitKey: '',
        standbyUnitKey: '',
        currentUnit: null,
      };
    });

    // Warm Audio Preload Cache + WebAudio Gain Normalizer
    const audioCache = new Map(); // url -> HTMLAudioElement
    let audioCtx = null;
    const gainNodes = new WeakMap();

    function ensureAudioCtx() {
      if (!audioCtx && typeof (window.AudioContext || window.webkitAudioContext) !== 'undefined') {
        try {
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch (_) {}
      }
      if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume().catch(() => {});
      }
    }

    function getPreloadedAudio(rawUrl) {
      const url = resolveAudioUrl(rawUrl);
      if (!url) return null;
      if (audioCache.has(url)) return audioCache.get(url);
      // Cap cache at 48 audio elements
      if (audioCache.size > 48) {
        const oldestKey = audioCache.keys().next().value;
        const oldEl = audioCache.get(oldestKey);
        if (oldEl && oldEl !== active1983Audio && oldEl !== activeArchAudio) {
          try { oldEl.pause(); oldEl.src = ''; } catch (_) {}
          audioCache.delete(oldestKey);
        }
      }
      const a = new Audio();
      a.preload = 'auto';
      a.src = url;
      try { a.load(); } catch (_) {}
      audioCache.set(url, a);
      return a;
    }

    function applyGainDb(audioEl, gainDb, baseScale = 1.0) {
      if (!audioEl) return;
      const db = Math.max(-12, Math.min(12, Number(gainDb || 0)));
      const linear = Math.pow(10, db / 20) * baseScale;
      audioEl.volume = Math.max(0.05, Math.min(1.0, linear));
    }

    // Engine State
    let beats = [];
    let beatIdx = 0;
    let playing = true;
    let soundOn = true;
    let autoAdvance = true;
    let pacingMode = cfg.defaultMode || 'duet'; // 'duet' | 'archive' | '1983' | 'overlay'
    const takeChoices = {}; // `${beatId}:${turnIdx}` -> 0 | 1 | 2

    // Current Beat & Turn Pacing State
    let turnIdx = 0;
    let turnPhase = '1983'; // '1983' | 'arch'
    let phaseElapsed = 0;
    let phaseDuration = 2.5;
    let beatClock = 0;
    let beatDuration = 5.0;
    let lastTickMs = performance.now();

    let active1983Audio = null;
    let activeArchAudio = null;
    let audioUnlocked = false;

    function stopActiveAudio() {
      if (active1983Audio) {
        try { active1983Audio.pause(); } catch (_) {}
        active1983Audio = null;
      }
      if (activeArchAudio) {
        try { activeArchAudio.pause(); } catch (_) {}
        activeArchAudio = null;
      }
    }

    function getTurnTakeIndex(bt, tIdx) {
      if (!bt) return 0;
      const k = `${bt.id}:${tIdx}`;
      return takeChoices[k] != null ? takeChoices[k] : 0;
    }

    function getTurnActiveTake(bt, tIdx) {
      if (!bt) return null;
      const turns = bt.turns_1983 || [];
      const tr = turns[tIdx] || turns[0];
      if (!tr) return (bt.takes && bt.takes[0]) || null;
      const takes = tr.takes && tr.takes.length ? tr.takes : (tr.arch_take ? [tr.arch_take] : (bt.takes || []));
      const choice = getTurnTakeIndex(bt, tIdx);
      return takes[Math.min(choice, Math.max(0, takes.length - 1))] || null;
    }

    // Prime a <video> element to a specific unit and clip_t0
    function primeVideoSlot(vid, unit) {
      if (!vid || !unit) return '';
      const url = resolveVideoUrl(unit);
      if (!url) return '';
      const t0 = Math.max(0, Number(unit.clip_t0 != null ? unit.clip_t0 : (unit.t0 || 0)));
      const key = `${url}@${t0.toFixed(2)}`;
      if (vid._wgsKey !== key) {
        vid._wgsKey = key;
        vid._wgsTargetT0 = t0;
        if (vid.getAttribute('src') !== url) {
          if (!IS_PAGES) vid.crossOrigin = 'anonymous';
          vid.src = url;
          vid.onerror = () => {
            // If CORS blocks remote R2 video on crossOrigin='anonymous', retry without crossOrigin
            if (vid.crossOrigin) {
              vid.removeAttribute('crossorigin');
              vid.crossOrigin = null;
              vid.src = url;
            }
          };
        }
        const seekToT0 = () => {
          try {
            if (Math.abs(vid.currentTime - t0) > 0.25) {
              vid.currentTime = t0;
            }
          } catch (_) {}
        };
        if (vid.readyState >= 1) {
          seekToT0();
        } else {
          vid.addEventListener('loadedmetadata', seekToT0, { once: true });
        }
      }
      return key;
    }

    // Preload all audio & initial sub-shots for beat `bIndex` and `bIndex + 1`
    function warmBeatResources(bIndex) {
      let warmedCount = 0;
      for (let offset = 0; offset <= 1; offset++) {
        const b = beats[(bIndex + offset) % Math.max(1, beats.length)];
        if (!b) continue;
        if (b.orig_file) { getPreloadedAudio(b.orig_file); warmedCount++; }
        if (b.aligned_file) { getPreloadedAudio(b.aligned_file); warmedCount++; }
        const turns = b.turns_1983 || [];
        turns.forEach((tr, ti) => {
          const takes = tr.takes || (tr.arch_take ? [tr.arch_take] : []);
          takes.forEach((tk, kIdx) => {
            if (offset === 0 || kIdx === getTurnTakeIndex(b, ti)) {
              if (tk && tk.audio_url) {
                const a = getPreloadedAudio(tk.audio_url);
                if (a && a.readyState >= 1 && a.paused) {
                  try { a.currentTime = Number(tk.audio_t0 || tk.t0 || 0); } catch (_) {}
                }
                warmedCount++;
              }
            }
          });
        });
      }
      const badge = document.getElementById('wgsPreloadBadge');
      if (badge) {
        badge.textContent = `PRELOAD: ${warmedCount} AUDIO/VIDEO STREAMS WARM`;
      }
    }

    // Sync all cut video decks to the current `beatClock`
    function syncVideoDecksToClock(bt, clockSec) {
      if (!bt || !bt.cuts) return;
      const dur = Math.max(1.5, Number(bt.wg_shot?.dur || 5.0));
      const localClock = Math.max(0, Math.min(dur - 0.02, clockSec % dur));

      cutKeys.forEach(cKey => {
        const deck = videoDecks[cKey];
        const units = bt.cuts[cKey] || bt.cuts.synthesis || bt.cuts['1983'] || [];
        if (!deck || !units.length) return;

        // Find active sub-shot unit at `localClock`
        let uIdx = 0;
        for (let i = 0; i < units.length; i++) {
          const st0 = Number(units[i].slot_t0 || 0);
          const sd = Number(units[i].slot_dur || units[i].dur || (dur / units.length));
          if (localClock >= st0 && localClock < st0 + sd + 0.05) {
            uIdx = i;
            break;
          }
          if (localClock >= st0) uIdx = i;
        }
        const unit = units[uIdx];
        const nextUnit = units[(uIdx + 1) % units.length];
        deck.currentUnit = unit;
        deck.currentUnitIndex = uIdx;

        const t0 = Number(unit.clip_t0 != null ? unit.clip_t0 : (unit.t0 || 0));
        const t1 = Number(unit.clip_t1 != null ? unit.clip_t1 : (unit.t1 || (t0 + 2.5)));
        const rate = Math.max(0.5, Math.min(1.5, Number(unit.rate || 1.0)));
        const url = resolveVideoUrl(unit);
        const unitKey = `${url}@${t0.toFixed(2)}`;

        let activeVid = deck.slots[deck.activeSlot];
        let standbyVid = deck.slots[1 - deck.activeSlot];

        // If standby slot already preloaded this exact unit, swap slots!
        if (deck.activeUnitKey !== unitKey) {
          if (standbyVid._wgsKey === unitKey) {
            try { activeVid.pause(); } catch (_) {}
            deck.activeSlot = 1 - deck.activeSlot;
            activeVid = deck.slots[deck.activeSlot];
            standbyVid = deck.slots[1 - deck.activeSlot];
          } else {
            primeVideoSlot(activeVid, unit);
          }
          deck.activeUnitKey = unitKey;
        }

        // Keep active video playing within [t0, t1]
        activeVid.playbackRate = rate;
        if (activeVid.readyState >= 1) {
          const offsetInSlot = Math.max(0, localClock - Number(unit.slot_t0 || 0));
          const clipSpan = Math.max(0.6, t1 - t0);
          const expectedTime = t0 + ((offsetInSlot * rate) % clipSpan);
          if (activeVid.currentTime < t0 - 0.15 || activeVid.currentTime > t1 + 0.25) {
            try { activeVid.currentTime = expectedTime; } catch (_) {}
          }
        }
        if (playing && activeVid.paused && activeVid.readyState >= 2) {
          activeVid.play().catch(() => {});
        } else if (!playing && !activeVid.paused) {
          try { activeVid.pause(); } catch (_) {}
        }

        // Preload `nextUnit` into `standbyVid`!
        if (nextUnit && nextUnit !== unit) {
          try { standbyVid.pause(); } catch (_) {}
          primeVideoSlot(standbyVid, nextUnit);
        }
      });

      // Also sync the active spoken line's archival take video (`take_video` deck)
      const takeDeck = videoDecks.take_video;
      const activeTake = getTurnActiveTake(bt, turnIdx);
      if (takeDeck && activeTake) {
        takeDeck.currentUnit = activeTake;
        const tVid = takeDeck.slots[0];
        primeVideoSlot(tVid, activeTake);
        const tkT0 = Number(activeTake.clip_t0 != null ? activeTake.clip_t0 : (activeTake.t0 || 0));
        const tkT1 = Number(activeTake.clip_t1 != null ? activeTake.clip_t1 : (tkT0 + Number(activeTake.dur || 2.5)));
        if (tVid.readyState >= 1 && (tVid.currentTime < tkT0 - 0.15 || tVid.currentTime > tkT1 + 0.25)) {
          try { tVid.currentTime = tkT0; } catch (_) {}
        }
        if (playing && tVid.paused && tVid.readyState >= 2) {
          tVid.play().catch(() => {});
        } else if (!playing && !tVid.paused) {
          try { tVid.pause(); } catch (_) {}
        }
      }
    }

    // Start audio for a specific turn & phase
    function startTurnPhaseAudio(bt, tIdx, phase) {
      stopActiveAudio();
      const turns = bt.turns_1983 || [];
      const tr = turns[tIdx] || turns[0];
      const take = getTurnActiveTake(bt, tIdx);
      const voiceBadge = document.getElementById('wgsActiveVoiceBadge');

      if (!tr) {
        phaseDuration = beatDuration;
        phaseElapsed = 0;
        return;
      }

      if (pacingMode === 'duet') {
        if (phase === '1983') {
          const s = Math.max(0, Number(tr.s || 0));
          const e = Math.max(s + 0.65, Number(tr.e || (s + 2.2)));
          phaseDuration = Math.max(0.75, Math.min(6.5, e - s));
          phaseElapsed = 0;
          if (voiceBadge) {
            voiceBadge.textContent = `1983 LINE ${tIdx + 1}/${turns.length}: ${String(tr.speaker || bt.who).toUpperCase()} (${tr.f0 || 125} Hz)`;
          }
          if (soundOn && bt.orig_file) {
            const a = getPreloadedAudio(bt.orig_file);
            if (a) {
              active1983Audio = a;
              applyGainDb(a, 0, 0.95);
              try { a.currentTime = s; } catch (_) {}
              if (playing) {
                a.play().then(() => { audioUnlocked = true; }).catch(() => {});
              }
            }
          }
        } else {
          // 'arch' answer phase for THIS specific spoken line
          const a0 = Number(take?.audio_t0 != null ? take.audio_t0 : (take?.t0 || 0));
          const a1 = Number(take?.audio_t1 != null ? take.audio_t1 : (take?.t1 || (a0 + (take?.dur || 2.4))));
          phaseDuration = Math.max(0.85, Math.min(6.5, a1 - a0));
          phaseElapsed = 0;
          if (voiceBadge) {
            voiceBadge.textContent = `ARCHIVE TAKE ${getTurnTakeIndex(bt, tIdx) + 1} (LINE ${tIdx + 1}/${turns.length}): ${String(take?.title || 'ARCHIVE').toUpperCase()}`;
          }
          if (soundOn && take?.audio_url) {
            const a = getPreloadedAudio(take.audio_url);
            if (a) {
              activeArchAudio = a;
              applyGainDb(a, take.gain_db || 0, 1.0);
              try { a.currentTime = a0; } catch (_) {}
              if (playing) {
                a.play().then(() => { audioUnlocked = true; }).catch(() => {});
              }
            }
          }
        }
      } else if (pacingMode === 'archive') {
        // Every spoken line in the scene is spoken back-to-back by its assigned Archival Speaker Take
        turnPhase = 'arch';
        const a0 = Number(take?.audio_t0 != null ? take.audio_t0 : (take?.t0 || 0));
        const a1 = Number(take?.audio_t1 != null ? take.audio_t1 : (take?.t1 || (a0 + (take?.dur || 2.4))));
        phaseDuration = Math.max(0.85, Math.min(6.5, a1 - a0));
        phaseElapsed = 0;
        if (voiceBadge) {
          voiceBadge.textContent = `ARCHIVE CAST LINE ${tIdx + 1}/${turns.length}: ${String(take?.title || 'ARCHIVE').toUpperCase()}`;
        }
        if (soundOn && take?.audio_url) {
          const a = getPreloadedAudio(take.audio_url);
          if (a) {
            activeArchAudio = a;
            applyGainDb(a, take.gain_db || 0, 1.0);
            try { a.currentTime = a0; } catch (_) {}
            if (playing) {
              a.play().then(() => { audioUnlocked = true; }).catch(() => {});
            }
          }
        }
      } else if (pacingMode === '1983') {
        // 1983 continuous scene master, stepping turn highlight by tr.s .. tr.e
        turnPhase = '1983';
        const s = Math.max(0, Number(tr.s || 0));
        const e = Math.max(s + 0.65, Number(tr.e || (s + 2.2)));
        phaseDuration = Math.max(0.75, e - s);
        phaseElapsed = 0;
        if (voiceBadge) {
          voiceBadge.textContent = `1983 MASTER LINE ${tIdx + 1}/${turns.length}: ${String(tr.speaker || bt.who).toUpperCase()}`;
        }
        if (soundOn && bt.orig_file) {
          const a = getPreloadedAudio(bt.orig_file);
          if (a) {
            active1983Audio = a;
            applyGainDb(a, 0, 0.95);
            try {
              if (Math.abs(a.currentTime - s) > 0.35) a.currentTime = s;
            } catch (_) {}
            if (playing && a.paused) {
              a.play().then(() => { audioUnlocked = true; }).catch(() => {});
            }
          }
        }
      } else if (pacingMode === 'overlay') {
        // Simultaneous 1983 + Archival Line Take
        turnPhase = 'arch';
        const s = Math.max(0, Number(tr.s || 0));
        const e = Math.max(s + 0.65, Number(tr.e || (s + 2.2)));
        const a0 = Number(take?.audio_t0 != null ? take.audio_t0 : (take?.t0 || 0));
        const a1 = Number(take?.audio_t1 != null ? take.audio_t1 : (take?.t1 || (a0 + (take?.dur || 2.4))));
        phaseDuration = Math.max(0.9, Math.max(e - s, a1 - a0));
        phaseElapsed = 0;
        if (voiceBadge) {
          voiceBadge.textContent = `OVERLAY LINE ${tIdx + 1}/${turns.length}: ${String(tr.speaker).toUpperCase()} + ${String(take?.title || 'ARCHIVE').toUpperCase()}`;
        }
        if (soundOn) {
          if (bt.orig_file) {
            const a83 = getPreloadedAudio(bt.orig_file);
            if (a83) {
              active1983Audio = a83;
              applyGainDb(a83, -5, 0.65);
              try { a83.currentTime = s; } catch (_) {}
              if (playing) a83.play().catch(() => {});
            }
          }
          if (take?.audio_url) {
            const aAr = getPreloadedAudio(take.audio_url);
            if (aAr) {
              activeArchAudio = aAr;
              applyGainDb(aAr, take.gain_db || 0, 0.95);
              try { aAr.currentTime = a0; } catch (_) {}
              if (playing) aAr.play().catch(() => {});
            }
          }
        }
      }
    }

    // Render the Spoken Line & 3-Take Sequencer Strip for the current beat
    function renderLineStrip() {
      const strip = document.getElementById('wgsLineStrip');
      if (!strip) return;
      const bt = beats[beatIdx];
      if (!bt) return;
      const turns = bt.turns_1983 || [];

      strip.innerHTML = turns.map((tr, i) => {
        const isAct = i === turnIdx;
        const choice = getTurnTakeIndex(bt, i);
        const takes = tr.takes && tr.takes.length ? tr.takes : (tr.arch_take ? [tr.arch_take] : []);
        const tk = takes[Math.min(choice, Math.max(0, takes.length - 1))] || {};
        const hlHtml = renderHighlightedText(tr.text, tk.hl, 'wgs-hl');
        const haHtml = renderHighlightedText(tk.spoken || '', tk.ha, 'wgs-ha');

        return `
          <div class="wgs-turn-card${isAct ? ' active' : ''}" data-turn-idx="${i}">
            <div class="wgs-tc-top">
              <span class="wgs-tc-who">
                <span class="wgs-tc-dot" style="background:${escHtml(tr.speaker_color || '#45b1ff')}"></span>
                <span>L${i + 1} · ${escHtml(tr.speaker || bt.who)}</span>
              </span>
              <span style="display:flex;align-items:center;gap:4px">
                ${tr.is_fulcrum ? '<span class="wgs-tc-fulc">THE LINE</span>' : ''}
                <span style="opacity:.65">${Number(tr.s || 0).toFixed(1)}–${Number(tr.e || 0).toFixed(1)}s · ${Math.round(Number(tr.f0 || 125))}Hz</span>
              </span>
            </div>
            <div class="wgs-tc-1983" title="${escHtml(tr.text)}">${hlHtml}</div>
            <div class="wgs-tc-arch" title="${escHtml(tk.spoken || '')}">"${haHtml}"</div>
            <div class="wgs-tc-foot">
              <span class="wgs-tc-film" title="${escHtml(tk.title || '')} (${tk.year || ''})">${escHtml(tk.title || 'Archive')} (${tk.year || '—'})</span>
              <div class="wgs-tc-takes">
                <button class="wgs-tk-btn" data-audition-1983="${i}" title="Hear 1983 Character Speak This Line">83</button>
                ${takes.map((tItem, tkIdx) => `
                  <button class="wgs-tk-btn${tkIdx === choice ? ' on' : ''}" data-take-turn="${i}" data-take-idx="${tkIdx}" title="${escHtml(tItem.role || ('Take ' + (tkIdx + 1)))}: &quot;${escHtml(tItem.spoken || '')}&quot; — ${escHtml(tItem.title || '')}">
                    T${tkIdx + 1}
                  </button>
                `).join('')}
              </div>
            </div>
            <div class="wgs-tc-prog ${isAct ? 'phase-' + turnPhase : ''}" id="wgsTurnProg_${i}" style="width:${isAct ? Math.min(100, (phaseElapsed / Math.max(0.2, phaseDuration)) * 100).toFixed(1) : 0}%"></div>
          </div>
        `;
      }).join('');

      // Bind clicks on turn cards & T1/T2/T3 take buttons
      strip.querySelectorAll('.wgs-turn-card').forEach(card => {
        card.addEventListener('click', e => {
          const tBtn = e.target.closest('[data-take-turn]');
          if (tBtn) {
            e.stopPropagation();
            const ti = parseInt(tBtn.getAttribute('data-take-turn'), 10);
            const tkIdx = parseInt(tBtn.getAttribute('data-take-idx'), 10);
            selectTurnTake(ti, tkIdx, true);
            return;
          }
          const a83Btn = e.target.closest('[data-audition-1983]');
          if (a83Btn) {
            e.stopPropagation();
            const ti = parseInt(a83Btn.getAttribute('data-audition-1983'), 10);
            jumpToTurn(ti, '1983');
            return;
          }
          const ti = parseInt(card.getAttribute('data-turn-idx'), 10);
          jumpToTurn(ti, pacingMode === 'archive' ? 'arch' : '1983');
        });
      });

      // Scroll active turn into view smoothly
      const activeCard = strip.querySelector('.wgs-turn-card.active');
      if (activeCard && strip.scrollWidth > strip.clientWidth) {
        activeCard.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
      }
    }

    function selectTurnTake(tIdx, tkIdx, auditionNow = true) {
      const bt = beats[beatIdx];
      if (!bt) return;
      takeChoices[`${bt.id}:${tIdx}`] = tkIdx;
      turnIdx = tIdx;
      if (auditionNow) {
        turnPhase = 'arch';
        startTurnPhaseAudio(bt, turnIdx, 'arch');
      }
      renderLineStrip();
      if (cfg.onTurnChange) cfg.onTurnChange(getCurrentState());
    }

    function jumpToTurn(tIdx, phase = '1983') {
      const bt = beats[beatIdx];
      if (!bt) return;
      const turns = bt.turns_1983 || [];
      turnIdx = Math.max(0, Math.min(turns.length - 1, tIdx));
      turnPhase = phase;
      const tr = turns[turnIdx];
      if (tr) {
        beatClock = Number(tr.s || 0);
      }
      startTurnPhaseAudio(bt, turnIdx, turnPhase);
      syncVideoDecksToClock(bt, beatClock);
      renderLineStrip();
      if (cfg.onTurnChange) cfg.onTurnChange(getCurrentState());
    }

    function loadBeat(index, opts = {}) {
      if (!beats.length) return;
      beatIdx = (index + beats.length) % beats.length;
      const bt = beats[beatIdx];
      beatDuration = Math.max(2.4, Number(bt.wg_shot?.dur || 5.0));
      beatClock = 0;
      turnIdx = 0;
      turnPhase = pacingMode === 'archive' ? 'arch' : '1983';

      if (nav) {
        nav.setBeatLabel(`Book ${ROMAN[bt.book_idx] || (bt.book_idx + 1)} · ${bt.book_title} · #${bt.index + 1}`);
      }

      warmBeatResources(beatIdx);
      syncVideoDecksToClock(bt, 0);
      startTurnPhaseAudio(bt, 0, turnPhase);
      renderLineStrip();

      if (cfg.onBeatChange) cfg.onBeatChange(bt, beatIdx, getCurrentState());
    }

    function advancePhaseOrTurn() {
      const bt = beats[beatIdx];
      if (!bt) return;
      const turns = bt.turns_1983 || [];
      if (!turns.length) {
        if (autoAdvance) loadBeat(beatIdx + 1);
        else loadBeat(beatIdx);
        return;
      }

      if (pacingMode === 'duet') {
        if (turnPhase === '1983') {
          turnPhase = 'arch';
          startTurnPhaseAudio(bt, turnIdx, 'arch');
          renderLineStrip();
          if (cfg.onTurnChange) cfg.onTurnChange(getCurrentState());
          return;
        }
        // Finished 'arch' answer for turnIdx -> advance to next spoken line!
        if (turnIdx + 1 < turns.length) {
          turnIdx++;
          turnPhase = '1983';
          startTurnPhaseAudio(bt, turnIdx, '1983');
          renderLineStrip();
          if (cfg.onTurnChange) cfg.onTurnChange(getCurrentState());
          return;
        }
      } else {
        // 'archive', '1983', or 'overlay' mode: step directly through turnIdx 0..N-1
        if (turnIdx + 1 < turns.length) {
          turnIdx++;
          startTurnPhaseAudio(bt, turnIdx, turnPhase);
          renderLineStrip();
          if (cfg.onTurnChange) cfg.onTurnChange(getCurrentState());
          return;
        }
      }

      // Completed all spoken lines in the beat!
      if (autoAdvance && beats.length > 1) {
        loadBeat(beatIdx + 1);
      } else {
        turnIdx = 0;
        turnPhase = pacingMode === 'archive' ? 'arch' : '1983';
        beatClock = 0;
        startTurnPhaseAudio(bt, 0, turnPhase);
        renderLineStrip();
      }
    }

    // Bind mode pills in the Line Dock
    document.querySelectorAll('[data-wgs-mode]').forEach(btn => {
      btn.addEventListener('click', () => {
        pacingMode = btn.getAttribute('data-wgs-mode') || 'duet';
        document.querySelectorAll('[data-wgs-mode]').forEach(b => {
          b.classList.toggle('mode-on', b.getAttribute('data-wgs-mode') === pacingMode);
        });
        const bt = beats[beatIdx];
        if (bt) {
          turnPhase = pacingMode === 'archive' ? 'arch' : '1983';
          startTurnPhaseAudio(bt, turnIdx, turnPhase);
          renderLineStrip();
        }
      });
    });

    const autoBtn = document.getElementById('wgsAutoNextBtn');
    if (autoBtn) {
      autoBtn.addEventListener('click', () => {
        autoAdvance = !autoAdvance;
        autoBtn.classList.toggle('on', autoAdvance);
        autoBtn.textContent = autoAdvance ? 'AUTO-CHAIN: ON' : 'AUTO-CHAIN: LOOP BEAT';
      });
    }

    // Unlock audio on first user pointer interaction anywhere
    const unlockOnce = () => {
      ensureAudioCtx();
      if (!audioUnlocked && soundOn && playing && beats[beatIdx]) {
        startTurnPhaseAudio(beats[beatIdx], turnIdx, turnPhase);
      }
    };
    window.addEventListener('pointerdown', unlockOnce, { passive: true });

    // Main RAF Pacing Loop
    function tick(now) {
      const dt = Math.min(0.1, Math.max(0.001, (now - lastTickMs) / 1000));
      lastTickMs = now;

      const bt = beats[beatIdx];
      if (bt && playing) {
        phaseElapsed += dt;

        // Map turn + phase progress onto the beat's visual timeline `beatClock` (`0 .. beatDuration`)
        const turns = bt.turns_1983 || [];
        const tr = turns[turnIdx];
        if (tr) {
          const s = Math.max(0, Number(tr.s || 0));
          const e = Math.min(beatDuration, Math.max(s + 0.5, Number(tr.e || beatDuration)));
          const frac = Math.min(1, phaseElapsed / Math.max(0.25, phaseDuration));
          if (pacingMode === 'duet') {
            // During 1983 call, advance first half of turn window; during archive answer, second half
            const halfSpan = (e - s) * 0.5;
            beatClock = turnPhase === '1983' ? (s + frac * halfSpan) : (s + halfSpan + frac * halfSpan);
          } else {
            beatClock = s + frac * (e - s);
          }
        } else {
          beatClock = (beatClock + dt) % beatDuration;
        }

        // Update progress bar inside active turn card
        const progEl = document.getElementById(`wgsTurnProg_${turnIdx}`);
        if (progEl) {
          progEl.style.width = `${Math.min(100, (phaseElapsed / Math.max(0.2, phaseDuration)) * 100).toFixed(1)}%`;
        }

        syncVideoDecksToClock(bt, beatClock);

        if (phaseElapsed >= phaseDuration) {
          advancePhaseOrTurn();
        }
      }

      if (bt && cfg.onTick) {
        cfg.onTick(getCurrentState(), dt, now);
      }
      requestAnimationFrame(tick);
    }

    function getCurrentState() {
      const bt = beats[beatIdx] || null;
      const turns = bt ? (bt.turns_1983 || []) : [];
      const activeTurn = turns[turnIdx] || turns[0] || null;
      const activeTake = getTurnActiveTake(bt, turnIdx);
      return {
        beat: bt,
        beatIdx,
        beats,
        beatClock,
        beatDuration,
        turnIdx,
        turnCount: turns.length,
        activeTurn,
        activeTake,
        turnPhase,
        phaseElapsed,
        phaseDuration,
        phaseProgress: Math.min(1, phaseElapsed / Math.max(0.2, phaseDuration)),
        pacingMode,
        playing,
        soundOn,
        getCutVideo(cutKey) {
          const d = videoDecks[cutKey];
          return d ? d.slots[d.activeSlot] : null;
        },
        getCutUnit(cutKey) {
          const d = videoDecks[cutKey];
          return d ? d.currentUnit : null;
        },
        getTakeVideo() {
          const d = videoDecks.take_video;
          return d ? d.slots[0] : null;
        },
      };
    }

    const engineApi = {
      setBeats(beatsList, initialIdx = 0) {
        beats = beatsList || [];
        loadBeat(initialIdx);
        lastTickMs = performance.now();
        requestAnimationFrame(tick);
      },
      loadBeat,
      nextBeat() { loadBeat(beatIdx + 1); },
      prevBeat() { loadBeat(beatIdx - 1); },
      jumpToTurn,
      selectTurnTake,
      setActiveTurnTake(tkIdx) {
        selectTurnTake(turnIdx, tkIdx, true);
      },
      setPlaying(p) {
        playing = p;
        if (!playing) {
          stopActiveAudio();
          allDeckKeys.forEach(k => {
            videoDecks[k].slots.forEach(v => { try { v.pause(); } catch (_) {} });
          });
        } else if (beats[beatIdx]) {
          startTurnPhaseAudio(beats[beatIdx], turnIdx, turnPhase);
          syncVideoDecksToClock(beats[beatIdx], beatClock);
        }
      },
      setSound(s) {
        soundOn = s;
        if (!soundOn) stopActiveAudio();
        else if (playing && beats[beatIdx]) startTurnPhaseAudio(beats[beatIdx], turnIdx, turnPhase);
      },
      getState: getCurrentState,
      resolveVideoUrl,
    };

    if (nav) nav._engine = engineApi;
    return engineApi;
  }

  window.WGStudioNav = { mount, STUDIO_PAGES, ROMAN, resolveVideoUrl, resolveAudioUrl };
  window.WGStudioEngine = { create: createEngine, resolveVideoUrl, resolveAudioUrl };
})();
