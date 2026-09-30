/* The Markov Poet's film surface: two layers of moving picture that interpolate into each other, and each shot's Cineosis DNA.
   The archive's CDN sends no CORS headers, so the pictures cannot be drawn to a canvas; the interpolation is the compositor's:
   the incoming shot rises through the outgoing one in screen blend (its light arrives first), out of blur and a slight scale,
   while the outgoing one blurs and falls away. At rest every shot drifts, very slowly.

   const F = MPFilm(el, { signs })   signs: kernel-data.json's {code: {symbol, name, dom}}
   F.show(shot, at, meta)            shot: a library shot; at: seconds into the clip; meta: {op, p} for the DNA
   F.play() F.pause() F.sound(on) F.calm(on) F.dna(shot, meta) -> html   */
(function () {
  const DOM = { perception: '#e9d9a8', affect: '#f0b9a4', action: '#e7a37c', reflection: '#b9cfa0', mental: '#a9c9c9', break: '#d9d3c7', time: '#b8b3d8', read: '#d9b8d2' };
  const EDIT = { OPEN: 'opens the scene', CONTINUE: 'stays in the world', HOLD: 'holds', REPEAT: 'returns again', RETURN: 'returns', ALTERNATE: 'meanwhile', SUSPEND: 'held back', COMPLETE: 'completes', ABSENCE: 'emptied', INSERT: 'insert', CUTAWAY: 'cuts away' };
  const css = `
  .mpf{ position:absolute; inset:0; overflow:hidden; background:#000; }
  .mpf .lay{ position:absolute; inset:0; opacity:0; will-change:opacity,filter,transform; }
  .mpf .lay video{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; animation:mpf-drift 40s ease-in-out infinite alternate; }
  .mpf .lay.cur{ opacity:1; }
  .mpf .lay.in{ opacity:1; mix-blend-mode:screen; animation:mpf-in var(--mpf-d,1.5s) cubic-bezier(.3,.6,.2,1) both; z-index:2; }
  .mpf .lay.out{ animation:mpf-out var(--mpf-d,1.5s) ease both; z-index:1; }
  @keyframes mpf-in{ 0%{ opacity:0; filter:blur(16px) brightness(1.7) saturate(.4); transform:scale(1.07); } 45%{ opacity:.9; filter:blur(5px) brightness(1.2) saturate(.8); } 100%{ opacity:1; filter:none; transform:scale(1); } }
  @keyframes mpf-out{ 0%{ opacity:1; filter:none; transform:scale(1); } 100%{ opacity:0; filter:blur(20px) brightness(.55); transform:scale(1.035); } }
  @keyframes mpf-drift{ from{ transform:scale(1) translate(0,0); } to{ transform:scale(1.045) translate(-.6%,.4%); } }
  .mpf.fit .lay video{ object-fit:contain; }
  .mpdna{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; font:10px/1.3 'IBM Plex Mono',ui-monospace,monospace; letter-spacing:.06em; color:#efe9ddaa; }
  .mpdna .el{ display:inline-grid; place-items:center; min-width:22px; height:22px; padding:0 4px; border-radius:3px; color:#15120d; font-weight:500; font-size:10.5px; letter-spacing:0; }
  .mpdna .els{ display:flex; gap:3px; } .mpdna .edit{ color:#e8c070; } .mpdna .conf{ display:inline-block; width:34px; height:2px; background:#ffffff26; vertical-align:middle; margin-left:4px; } .mpdna .conf b{ display:block; height:100%; background:#e8c070; }`;
  const st = document.createElement('style'); st.textContent = css; document.head.append(st);
  window.MPFilm = function (el, opts = {}) {
    const signs = opts.signs || {}, root = document.createElement('div'); root.className = 'mpf'; el.append(root);
    const lays = [0, 1].map(() => { const d = document.createElement('div'); d.className = 'lay'; const v = document.createElement('video'); v.playsInline = true; v.muted = true; v.preload = 'auto'; d.append(v); root.append(d); return d; });
    let on = 0, playing = false, sound = false, calm = false, dur = 1.5, fadeT = 0;
    const vid = i => lays[i].firstChild;
    function load(v, u, at) { if (v.dataset.u !== u) { v.dataset.u = u; v.src = u; } const set = () => { try { v.currentTime = Math.min(at, Math.max(0, (v.duration || 1e9) - .1)); } catch (e) { } }; if (v.readyState >= 1) set(); else v.addEventListener('loadedmetadata', set, { once: true }); }
    function volumes() {                                   // film sound crossfades with the picture
      clearInterval(fadeT); const a = vid(on), b = vid(1 - on); if (!sound) { a.muted = b.muted = true; return; }
      a.muted = false; b.muted = false; const t0 = performance.now();
      fadeT = setInterval(() => { const k = Math.min(1, (performance.now() - t0) / (dur * 1000)); a.volume = .85 * k; b.volume = .85 * (1 - k); if (k >= 1) { clearInterval(fadeT); b.muted = true; b.pause(); } }, 50);
    }
    const api = {
      show(shot, at, meta, instant) {
        const u = shot.video, cur = vid(on);
        if (cur.dataset.u === u && Math.abs(cur.currentTime - at) < 1.2 && !instant) return;       // the same shot carries on
        const n = 1 - on, nv = vid(n); load(nv, u, at); nv.playbackRate = calm ? .8 : 1; nv.loop = !!(meta && meta.loop);
        lays[n].style.setProperty('--mpf-d', (instant ? .01 : dur) + 's'); lays[on].style.setProperty('--mpf-d', (instant ? .01 : dur) + 's');
        lays[n].className = 'lay in'; lays[on].className = 'lay out';
        if (playing || (meta && meta.loop)) nv.play().catch(() => { });
        const was = on; on = n; volumes();
        setTimeout(() => { if (on !== n) return; lays[n].className = 'lay cur'; lays[was].className = 'lay'; if (!sound) vid(was).pause(); }, (instant ? 20 : dur * 1000 + 60));
      },
      preload(shot, at) { const b = vid(1 - on); if (lays[1 - on].className === 'lay') load(b, shot.video, at); },
      play() { playing = true; const v = vid(on); if (!(v.ended || (v.duration && v.currentTime >= v.duration - .12))) v.play().catch(() => { }); },
      pause() { playing = false; lays.forEach((l, i) => vid(i).pause()); },
      tick() { const v = vid(on); if (!playing) return; if (v.ended || (v.duration && v.currentTime >= v.duration - .12)) { if (!v.paused) v.pause(); } else if (v.paused && v.readyState >= 2) v.play().catch(() => { }); },
      sound(x) { sound = !!x; volumes(); return sound; }, calm(x) { calm = !!x; dur = calm ? 2.6 : 1.5; lays.forEach((l, i) => vid(i).playbackRate = calm ? .8 : 1); return calm; },
      get isSound() { return sound; }, get isCalm() { return calm; },
      dna(shot, meta = {}) {
        const els = (shot.signs || []).slice(0, 3).map(c => signs[c]).filter(Boolean)
          .map(g => `<span class="el" style="background:${DOM[g.dom] || '#ccc'}" title="${g.name}">${g.symbol}</span>`).join('');
        const bits = [shot.scale, shot.title && (shot.title.length > 38 ? shot.title.slice(0, 36) + '…' : shot.title), shot.year].filter(Boolean).join(' · ');
        return `<span class="els">${els}</span><span>${bits}</span>` + (meta.op ? `<span class="edit">${EDIT[meta.op] || meta.op.toLowerCase()}</span>` : '') +
          (meta.p != null ? `<span>${Math.round(meta.p * 100)}%<span class="conf"><b style="width:${Math.min(100, meta.p * 100)}%"></b></span></span>` : '');
      },
      el: root };
    return api;
  };
  window.MPFilm.DOM = DOM; window.MPFilm.EDIT = EDIT;
})();
