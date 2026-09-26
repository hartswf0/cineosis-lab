/* NARRATIVE LAB — the Cineosis Lab, driven by the poem.
 *
 * A branch of the lab (lab/narrative.html loads the same app.js). The poem drives it: her reading plays, the line
 * she is on decides what every view shows, and the chosen shot for that moment plays in the middle.
 *   <line>    the unit: every view (wall, map, ring, strata, cut-outs…) holds only this line's shots
 *   <shots>   for a line: what this lab kept, what the chosen source put there, the four cuts' shots, what the
 *             nine bets chose, then every ranked candidate of the line's beats, in that order
 *   <chosen>  the reference film: one of the four WYGWYL cuts, the house cut, a bet, or this lab's own film (NL)
 *   <now>     the shot playing at the voice's time, with its own sound ducked under her words: in the ring it
 *             plays in the middle of the cylinder, in the other views it sits docked in the corner
 * The same five verbs as the bets: A watch · B try · C keep · D flag · E on. Space plays, ← → move by line.
 * Clicking a shot tries it; double click keeps it; Alt-click opens the lab's inspector as before.
 * What this lab keeps is its own film, cineosis.film.NL.v1, in the same record format as every bet.
 */
(() => {
  'use strict';
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } } };
  const FILMKEY = c => `cineosis.film.${c}.v1`;
  const CUTS = ['suite', 'scenes', 'cineosis', 'drift'];
  const SOURCES = [['suite', 'Suite cut'], ['scenes', 'Scenes cut'], ['cineosis', 'Cineosis cut'], ['drift', 'Drift cut'], ['NL', 'this lab'], ['HOUSE', 'house cut'],
    ['P1', 'P1 Concordance'], ['P2', 'P2 Voice Clock'], ['P3', 'P3 Scale Ladder'], ['P4', 'P4 Audition'], ['P5', 'P5 Field'], ['P6', 'P6 Branches'], ['P7', 'P7 Loop Wheel'], ['P8', 'P8 Press'], ['P9', 'P9 Strata']];
  const HASH0 = location.hash;                                                     // the view asked for, before the lab picks its default
  const N = window.N = { on: true, li: 0, ids: null, role: {}, trying: null, loop: false, source: store.get('narrative.source', 'suite'), alt: false };
  const A = new Audio(); A.preload = 'auto';
  let KD, ND, LOOPS = new Set();
  const $ = s => document.querySelector(s), h = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const escH = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const fmtT = t => { t = Math.max(0, t || 0); const m = Math.floor(t / 60); return `${String(m).padStart(2, '0')}:${(t - m * 60).toFixed(1).padStart(4, '0')}`; };

  /* ---------- the poem ---------- */
  const lines = () => KD.lines;
  const line = () => KD.lines[N.li];
  const lineAt = t => KD.lines.find(l => t >= l.t0 && t < l.t1 + .25) || null;
  const wordAt = t => { const l = lineAt(t); return l ? l.words.find(w => t >= w.t0 && t < w.t1) || null : null; };
  const filmOf = n => KD.films.find(f => f.n === n);

  /* ---------- films: this lab's, the four cuts, the house, the bets ---------- */
  const film = code => {
    if (CUTS.includes(code)) return (ND.cuts[code] || []).map(([t0, t1, id]) => ({ t0, t1, id }));
    if (code === 'HOUSE') { const hs = store.get('cineosis.house.v1', {}), out = []; KD.films.forEach(f => { const c = hs[f.n]; if (c) store.get(FILMKEY(c), []).forEach(s => { if (s.t1 > f.t0 && s.t0 < f.t1) out.push({ t0: s.t0, t1: s.t1, id: s.clip.id }); }); }); return out; }
    return store.get(FILMKEY(code), []).map(s => ({ t0: s.t0, t1: s.t1, id: s.clip.id, flag: s.flag }));
  };
  const inSpan = (f, a, b) => f.filter(s => s.t1 > a + .01 && s.t0 < b - .01);
  const atT = (f, t) => f.find(s => t >= s.t0 && t < s.t1) || null;

  /* ---------- a line's shots, in the order that matters ---------- */
  function lineShots(l) {
    const a = l.t0, b = l.t1, ids = [], role = {};
    const add = (id, r) => { if (!id || role[id] || !L.byId.has(id)) return; role[id] = r; ids.push(id); };
    inSpan(film('NL'), a, b).forEach(s => add(s.id, 'kept'));
    if (N.source !== 'NL') inSpan(film(N.source), a, b).forEach(s => add(s.id, 'source'));
    CUTS.forEach(c => inSpan(film(c), a, b).forEach(s => add(s.id, 'cut')));
    ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'].forEach(c => inSpan(film(c), a, b).forEach(s => add(s.id, 'bet')));
    KD.beats.filter(x => x.t1 > a && x.t0 < b).forEach(x => (ND.ranked[x.id] || []).forEach(([id, v]) => add(id, v === 'K' ? 'keep' : v === 'M' ? 'maybe' : 'floor')));
    return { ids, role };
  }

  /* ---------- the hook: every view shows the line's shots ---------- */
  function hook() {
    const base = compute;
    compute = function () {                                                       // app.js calls compute() by name, so every view now follows the line
      base();
      if (!N.on || !N.ids) return;
      const inView = new Set(VIEW.map(s => s.id));                                // the lab's own filters still narrow the line's shots
      VIEW = N.ids.map(id => L.byId.get(id)).filter(s => s && inView.has(s.id)); GROUPED = null;
    };
    const open = Inspector.open.bind(Inspector);
    Inspector.open = (s, items) => { if (N.on && !N.alt) { tryShot(s); return; } open(s, items); };
    addEventListener('pointerdown', e => { N.alt = e.altKey || e.metaKey; }, true);
    addEventListener('dblclick', e => { const t = e.target.closest?.('.tile,.rc'); if (N.on && t && t._shot) { e.preventDefault(); keep(t._shot); } }, true);
    Ring.auto = false;
    const count = Shell.updateCount.bind(Shell);
    Shell.updateCount = () => {                                                   // the status speaks of the line, not the corpus
      count(); const st = document.getElementById('status'); if (!N.on || !st || !KD) return;
      const l = line(); st.innerHTML = `<b>${VIEW.length}</b> shots for line ${l.n} of poem ${l.film} · click to try · double click to keep · Alt-click to inspect`;
    };
    Guide.close?.(); try { localStorage.setItem(Guide.key, '1'); } catch (e) { /* ok */ }
  }

  /* ---------- the driver bar ---------- */
  function bar() {
    const d = $('#drive');
    d.innerHTML = `<button id="nPlay" title="Play or pause her voice (space)">▶</button>
      <div class="ncol"><div id="nPoems"></div><div id="nLine"><span id="nBrick" class="nbrick"></span><span id="nWords"></span></div></div>
      <div class="ncol r"><div class="nrow"><label>chosen <select id="nSrc">${SOURCES.map(([k, v]) => `<option value="${k}"${k === N.source ? ' selected' : ''}>${escH(v)}</option>`).join('')}</select></label><span id="nClock"></span></div>
        <div class="nrow" id="nVerbs">${[['A', 'watch'], ['B', 'try'], ['C', 'keep'], ['D', 'flag'], ['E', 'on']].map(([k, v]) => `<button data-v="${k}" title="${k}"><b>${k}</b>${v}</button>`).join('')}</div></div>
      <div id="nState"></div>`;
    $('#nPlay').onclick = () => A.paused ? play() : A.pause();
    $('#nSrc').onchange = e => { N.source = e.target.value; store.set('narrative.source', N.source); setLine(N.li); };
    d.querySelectorAll('#nVerbs button').forEach(b => b.onclick = () => verb(b.dataset.v));
    const P = $('#nPoems');
    KD.films.forEach(f => { const b = h('button', 'npoem'); b.dataset.n = f.n; b.innerHTML = `<b>${f.n}</b><i></i>`; b.title = f.title; b.onclick = () => { const i = KD.lines.findIndex(l => l.film === f.n); if (i >= 0) setLine(i, true); }; P.append(b); });
    A.addEventListener('play', () => $('#nPlay').textContent = '❚❚'); A.addEventListener('pause', () => $('#nPlay').textContent = '▶');
  }
  function drawBar() {
    const l = line(), f = filmOf(l.film), nl = film('NL');
    document.querySelectorAll('.npoem').forEach(b => {
      const g = filmOf(b.dataset.n), own = inSpan(nl, g.p0 ?? g.t0, g.p1 ?? g.t1), src = own[0] || inSpan(film(N.source), g.t0, g.t1)[0] || inSpan(film('suite'), g.t0, g.t1)[0], s = src && L.byId.get(src.id);
      if (s) b.style.backgroundImage = `url("${s.thumb}")`; b.classList.toggle('on', g.n === l.film); b.classList.toggle('made', !!own.length);
      const lsN = KD.lines.filter(x => x.film === g.n), made = lsN.filter(x => inSpan(nl, x.t0, x.t1).length).length; b.querySelector('i').style.width = (lsN.length ? 100 * made / lsN.length : 0) + '%';
    });
    const kept = inSpan(nl, l.t0, l.t1)[0], ks = kept && L.byId.get(kept.id), br = $('#nBrick');
    br.style.backgroundImage = ks ? `url("${ks.thumb}")` : ''; br.classList.toggle('full', !!ks); br.style.setProperty('--sg', ks ? colorOf(ks) : 'transparent');
    $('#nWords').dataset.li = ''; words(A.currentTime);
    const lf = KD.lines.filter(x => x.film === l.film), roles = Object.values(N.role);
    const cnt = r => roles.filter(x => x === r).length;
    $('#nState').innerHTML = `<i>poem</i><b>${l.film}</b><i>line</i><b>${l.n}/${lf.length}</b><i>shots</i><b>${VIEW.length}</b><i>kept</i><b>${cnt('kept') ? '●' : '○'}</b><i>cuts</i><b>${cnt('cut') + cnt('source')}</b><i>bets</i><b>${cnt('bet')}</b><i>ranked</i><b>${cnt('keep') + cnt('maybe') + cnt('floor')}</b><i>lab film</i><b>${Math.round(100 * KD.lines.filter(x => inSpan(nl, x.t0, x.t1).length).length / KD.lines.length)}%</b>`;
  }
  function words(t) {
    const l = line(), w = wordAt(t), k = N.li + ':' + (w ? w.t0 : -1), el = $('#nWords'); if (el.dataset.k === k) return; el.dataset.k = k;
    el.innerHTML = l.words.map(x => x === w ? `<b>${escH(x.w)}</b>` : escH(x.w)).join(' ');
  }
  const colorOf = s => { const n = (s._aff3 && s._aff3[0]) || (s._read && s._read[0]); return n ? signColor(n) : '#666'; };

  /* ---------- the now deck: the chosen shot, playing with its own sound ---------- */
  let nowKey = null, nowT = 0;
  function nowDeck() { const d = h('div', '', ''); d.id = 'nNow'; d.innerHTML = '<video playsinline preload="auto"></video><span class="nsrc"></span>'; $('#stage').append(d); d.onclick = () => N.trying && keep(N.trying); return d; }
  function nowShot(t) {
    if (N.trying) return [N.trying, 'try', null];
    const k = atT(film('NL'), t); if (k && L.byId.get(k.id)) return [L.byId.get(k.id), 'kept', k];
    const s = N.source !== 'NL' && atT(film(N.source), t); if (s && L.byId.get(s.id)) return [L.byId.get(s.id), N.source, s];
    const c = atT(film('suite'), t); return c && L.byId.get(c.id) ? [L.byId.get(c.id), 'suite', c] : [null, '', null];
  }
  function driveNow(t) {
    const d = $('#nNow'), v = d.querySelector('video'), [s, why, seat] = nowShot(t);
    const key = s ? s.id + why : '';
    if (key !== nowKey) {
      nowKey = key; nowT = t;
      if (s) { v.src = s.clip || s.video; v.poster = s.thumb || ''; d.style.setProperty('--sg', colorOf(s)); d.querySelector('.nsrc').textContent = why === 'try' ? 'trying · click or C to keep' : why === 'kept' ? 'kept' : why; d.classList.toggle('loose', why !== 'kept'); d.hidden = false; face(s.id); }
      else { v.removeAttribute('src'); d.hidden = true; }
    }
    if (!s || !v.src) return;
    const into = seat ? t - seat.t0 : t - nowT, base = s.read_t != null && !seat ? Math.max(0, s.read_t - .6) : 0, want = base + Math.max(0, into);
    if (v.readyState >= 1 && !v.seeking && Math.abs(v.currentTime - want) > (A.paused ? .15 : 1.2) && (!v.duration || want < v.duration)) try { v.currentTime = want; } catch (e) { /* not ready */ }
    if (!A.paused && v.paused) v.play().catch(() => {}); if (A.paused && !v.paused) v.pause();
    const speaking = !!wordAt(t); v.muted = !N.sound; v.volume = N.sound ? (speaking ? .22 : .7) : 0;   // her voice untouched; the shot steps back while she speaks
  }
  N.sound = store.get('cineosis.clipsound', true);

  /* ---------- the ring: the line's shots around, the chosen one faced; the front few play ---------- */
  function face(id) {
    if (Shell.mode !== 'ring' || !Ring.cards) return;
    const c = Ring.cards.find(x => x._shot && x._shot.id === id); if (!c) return;
    Ring.vel = 0; Ring.spin = -c._a; Ring.apply(true);
  }
  const ringLive = new Map();
  function ringPlay() {
    if (Shell.mode !== 'ring' || !Ring.cards) { ringLive.forEach(v => v.remove()); ringLive.clear(); return; }
    const front = Ring.cards.map(c => [c, Math.cos(((c._a + Ring.spin) % 360 + 360) % 360 * Math.PI / 180)]).filter(([, cs]) => cs > .55).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([c]) => c);
    ringLive.forEach((v, c) => { if (!front.includes(c)) { v.remove(); ringLive.delete(c); } });
    front.forEach(c => { if (ringLive.has(c)) return; const s = c._shot, src = LOOPS.has(s.id) ? `wygwyl/tempest/${s.id}.mp4` : (s.clip || s.video); if (!src) return;
      const v = h('video', 'rcv'); v.muted = true; v.loop = true; v.playsInline = true; v.src = src; v.addEventListener('loadedmetadata', () => { if (!LOOPS.has(s.id) && s.read_t != null) v.currentTime = Math.max(0, s.read_t - .6); }, { once: true });
      v.addEventListener('playing', () => v.classList.add('on'), { once: true }); v.play().catch(() => {}); c.append(v); ringLive.set(c, v); });
  }

  /* ---------- marks: what is kept, chosen, tried, in every view ---------- */
  function mark() {
    const t = A.currentTime, [cur] = nowShot(t);
    document.querySelectorAll('#stage .tile, #stage .rc').forEach(e => {
      const s = e._shot; if (!s) return; const r = N.role[s.id];
      e.classList.toggle('n-kept', r === 'kept'); e.classList.toggle('n-src', r === 'source' || r === 'cut'); e.classList.toggle('n-bet', r === 'bet');
      e.classList.toggle('n-try', !!N.trying && N.trying.id === s.id); e.classList.toggle('n-now', !!cur && cur.id === s.id);
    });
  }

  /* ---------- lines ---------- */
  function setLine(i, seek) {
    i = Math.max(0, Math.min(KD.lines.length - 1, i)); N.li = i; N.trying = null;
    const l = line(), r = lineShots(l); N.ids = r.ids; N.role = r.role;
    if (seek && A.paused) A.currentTime = l.t0;
    refresh();
    requestAnimationFrame(() => requestAnimationFrame(() => { drawBar(); mark(); nowKey = null; const [s] = nowShot(A.currentTime); if (s) face(s.id); }));
    try { const q = new URLSearchParams(location.search); q.set('line', l.id); history.replaceState(null, '', '?' + q + location.hash); } catch (e) { /* file: */ }
  }
  function play() { if (A.currentTime < line().t0 - .5 || A.currentTime > line().t1 + .5) A.currentTime = line().t0 - .15; A.play().catch(() => toast?.('tap once to allow sound')); }

  /* ---------- the five verbs ---------- */
  function tryShot(s) { N.trying = s; nowKey = null; mark(); face(s.id); if (A.paused) { N.loop = true; play(); } }
  function keep(s) {
    s = s || N.trying || nowShot(A.currentTime)[0]; if (!s) return;
    const l = line(), seats = store.get(FILMKEY('NL'), []).filter(x => !(x.t1 > l.t0 && x.t0 < l.t1));   // this lab keeps a line at a time
    const sg = (s._aff3 && s._aff3[0]) || (s._read && s._read[0]) || null;
    seats.push({ id: 's' + Date.now().toString(36), t0: l.t0, t1: l.t1, text: l.text, clip: { id: s.id, title: s.title, year: s.year, thumb: s.thumb, video: s.clip || s.video, loop: LOOPS.has(s.id), sg, in: s.read_t != null ? Math.max(0, s.read_t - .6) : 0, dur: null }, by: 'person', bet: 'NL', why: 'kept in the narrative lab', at: Date.now() });
    seats.sort((a, b) => a.t0 - b.t0); store.set(FILMKEY('NL'), seats);
    N.trying = null; const r = lineShots(l); N.ids = r.ids; N.role = r.role; refresh(); nowKey = null;
    celebrate(); requestAnimationFrame(() => { drawBar(); mark(); });
    toast?.(`kept · ${s.title} · line ${l.n}`);
  }
  function flag() {
    const [s] = nowShot(A.currentTime); if (!s) return;
    const bin = store.get('cineosis.bin.v1', {}); bin[s.id] = { id: s.id, title: s.title, year: s.year, thumb: s.thumb, video: s.clip || s.video, loop: LOOPS.has(s.id), sg: (s._aff3 && s._aff3[0]) || null, verdict: 'KEEP' };
    store.set('cineosis.bin.v1', bin); celebrate(); toast?.(`★ ${s.title} · noted for later, in every bet`);
  }
  function celebrate() { const d = $('#nNow'); d.classList.remove('cele'); void d.offsetWidth; d.classList.add('cele'); setTimeout(() => d.classList.remove('cele'), 1000); }
  function verb(k) {
    if (k === 'A') { if (!A.paused && N.loop) { A.pause(); return; } N.loop = true; play(); }
    else if (k === 'B') { const list = viewList(); if (!list.length) return; const i = N.trying ? list.findIndex(s => s.id === N.trying.id) : -1; tryShot(list[(i + 1) % list.length]); }
    else if (k === 'C') keep();
    else if (k === 'D') flag();
    else if (k === 'E') { setLine(N.li + 1, true); if (!A.paused) { A.currentTime = line().t0 - .15; } }
    const b = document.querySelector(`#nVerbs button[data-v="${k}"]`); if (b) { b.classList.add('fire'); setTimeout(() => b.classList.remove('fire'), 160); }
  }
  addEventListener('keydown', e => {
    if (!N.on || typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (!$('#inspector').hidden || Shell.mode === 'reel' || Shell.mode === 'wyg') return;   // those have their own keys
    const k = e.key.toUpperCase();
    if ('ABCDE'.includes(k) && e.key.length === 1) { e.preventDefault(); e.stopImmediatePropagation(); verb(k); }
    else if (e.key === ' ') { e.preventDefault(); e.stopImmediatePropagation(); N.loop = false; A.paused ? play() : A.pause(); }
    else if (e.key === 'ArrowRight' && Shell.mode !== 'map') { e.preventDefault(); setLine(N.li + 1, true); }
    else if (e.key === 'ArrowLeft' && Shell.mode !== 'map') { e.preventDefault(); setLine(N.li - 1, true); }
    else if (k === 'S' && e.key.length === 1) { N.sound = !N.sound; store.set('cineosis.clipsound', N.sound); toast?.(N.sound ? 'shot sound on, ducked under her words' : 'shot sound off'); }
  }, true);

  /* ---------- the clock ---------- */
  let lastMode = null, lastMark = 0;
  function tick() {
    const t = A.currentTime;
    if (!A.paused) {
      const l = line();
      if (N.loop && t >= l.t1 + .35) A.currentTime = l.t0 - .15;
      else if (!N.loop) { const at = lineAt(t); if (at && at !== l) setLine(KD.lines.indexOf(at)); }
    }
    driveNow(t); words(t); $('#nClock').textContent = fmtT(t);
    if (Shell.mode !== lastMode) { lastMode = Shell.mode; document.body.dataset.nmode = lastMode; nowKey = null; setTimeout(() => { mark(); const [s] = nowShot(A.currentTime); if (s) face(s.id); }, 120); }
    const now = performance.now(); if (now - lastMark > 450) { lastMark = now; mark(); ringPlay(); }
    requestAnimationFrame(tick);
  }

  async function start() {
    [KD, ND] = await Promise.all([fetch('bets/kernel-data.json').then(r => r.json()), fetch('narrative/narrative-data.json').then(r => r.json())]);
    KD.films.forEach(f => { const ls = KD.lines.filter(l => l.film === f.n); f.p0 = ls.length ? ls[0].t0 : f.t0; f.p1 = ls.length ? ls.at(-1).t1 : f.t1; });
    Object.values(KD.pool).forEach(v => v.forEach(c => { if (c.loop) LOOPS.add(c.id); }));
    A.src = 'wygwyl/WYGWYL_Suite_Audio.mp3';
    for (let k = 0; k < 400 && !(typeof L !== 'undefined' && L.shots && L.shots.length && typeof Shell !== 'undefined' && Shell.mode); k++) await sleep(100);
    document.body.classList.add('narrative');
    hook(); bar(); nowDeck();
    const q = new URLSearchParams(location.search), want = q.get('line'), i = want ? KD.lines.findIndex(l => l.id === want) : 0;
    setLine(Math.max(0, i), true);
    if (!HASH0) Shell.setMode?.('ring');                                          // the ring by default: the line's shots around, the chosen in the middle
    addEventListener('storage', e => { if (/^cineosis\.(film|house)/.test(e.key || '')) setLine(N.li); });
    requestAnimationFrame(tick);
  }
  start().catch(err => console.error('[narrative]', err));
})();
