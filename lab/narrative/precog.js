/* PRECOG — the Narrative Lab's investigation room.
 *
 * A curved glass wall around you. The line she is speaking fills it with its shots as a cloud: around the curve by
 * hue, up and down by luminance, near or far by rank (greyscale shots gather at the two ends). The chosen shot plays
 * large in the middle with its sound; the line's words glow on the glass. Nothing but numbers and gestures:
 *   drag the glass sideways to turn it · drag up or down, or wheel, to move through the lines
 *   click a pane to try it (it comes forward) · double click to keep · the strip at the bottom is the whole poem
 *   filters as marks: drag across the hue band, tap ◐ (greyscale / colour), the eight sign colours, the five scales
 *   A watch · B try · C keep · D flag · E on · Esc back to the lab views · P returns here
 */
(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const h = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const DOMS = ['perception', 'affect', 'action', 'reflection', 'mental', 'break', 'time', 'read'];
  const SCL = [['extreme close-up', 'ECU'], ['close-up', 'CU'], ['medium shot', 'MS'], ['long shot', 'LS'], ['extreme long shot', 'ELS']];
  const PG = window.PG = { on: false, turn: 0, f: { hue: null, tone: null, dom: new Set(), scale: new Set() }, panes: new Map(), live: new Map() };
  let root, glass, api;

  const domOf = s => { const n = (s._aff3 && s._aff3[0]) || (s._read && s._read[0]); return n && L.S[n] ? L.S[n].dom : null; };
  const passes = s => {
    const f = PG.f;
    if (f.tone === 'bw' && !(s.bw || s.hue == null)) return false;
    if (f.tone === 'col' && (s.bw || s.hue == null)) return false;
    if (f.hue && !(s.hue != null && !s.bw && (f.hue[0] <= f.hue[1] ? s.hue >= f.hue[0] && s.hue <= f.hue[1] : s.hue >= f.hue[0] || s.hue <= f.hue[1]))) return false;
    if (f.dom.size && !f.dom.has(domOf(s))) return false;
    if (f.scale.size && !f.scale.has(s.scale)) return false;
    return true;
  };

  function build() {
    root = h('div', ''); root.id = 'precog';
    root.innerHTML = `
      <div class="pg-hud tl"><b id="pgLine"></b><span id="pgPoem"></span></div>
      <div class="pg-hud tc"><span id="pgFrame"></span> <b id="pgSec"></b></div>
      <div class="pg-hud tr"><b id="pgTC"></b><button id="pgOut" title="Back to the lab views (Esc)">⌗</button></div>
      <div class="pg-words" id="pgWords"></div>
      <div class="pg-space"><div class="pg-glass" id="pgGlass"></div></div>
      <div class="pg-center" id="pgCenter"></div>
      <div class="pg-hud bl" id="pgFilters">
        <div class="pg-hue" id="pgHue" title="Drag across to keep a range of hue · tap to clear"><i id="pgHueSel"></i></div>
        <button class="pg-tone" id="pgTone" title="All · greyscale · colour">◐</button>
        <span class="pg-doms" id="pgDoms">${DOMS.map(d => `<button data-d="${d}" style="--c:${DOMC[d]}" title="${esc(DOMN[d])}"></button>`).join('')}</span>
        <span class="pg-scl" id="pgScl">${SCL.map(([k, a]) => `<button data-s="${esc(k)}" title="${esc(k)}">${a}</button>`).join('')}</span>
      </div>
      <div class="pg-hud br" id="pgCount"></div>
      <div class="pg-poem" id="pgPoemStrip"></div>`;
    document.body.append(root);
    glass = $('#pgGlass');
    // turning the glass and moving through lines
    let drag = null;
    const space = $('.pg-space', root);
    space.addEventListener('pointerdown', e => { if (e.target.closest('.pg-pane')) return; space.setPointerCapture(e.pointerId); drag = { x: e.clientX, y: e.clientY, t: PG.turn, moved: false }; });
    space.addEventListener('pointermove', e => { if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y; if (Math.abs(dx) > 4) drag.moved = true; PG.turn = drag.t + dx * .12; place(); if (Math.abs(dy) > 90) { api.setLine(N.li + (dy < 0 ? 1 : -1), true); drag.y = e.clientY; } });
    space.addEventListener('pointerup', () => { drag = null; });
    let wheelAcc = 0;
    root.addEventListener('wheel', e => { e.preventDefault(); wheelAcc += e.deltaY; if (Math.abs(wheelAcc) > 120) { api.setLine(N.li + Math.sign(wheelAcc), true); wheelAcc = 0; } }, { passive: false });
    // filters
    const hue = $('#pgHue'); let hs = null;
    const hueAt = e => { const r = hue.getBoundingClientRect(); return Math.max(0, Math.min(359, 360 * (e.clientX - r.left) / r.width)); };
    hue.addEventListener('pointerdown', e => { hue.setPointerCapture(e.pointerId); hs = hueAt(e); PG.f.hue = null; });
    hue.addEventListener('pointermove', e => { if (hs == null) return; const b = hueAt(e); if (Math.abs(b - hs) > 6) { PG.f.hue = [Math.min(hs, b), Math.max(hs, b)]; filt(); } });
    hue.addEventListener('pointerup', () => { hs = null; filt(); });
    $('#pgTone').onclick = () => { PG.f.tone = PG.f.tone == null ? 'bw' : PG.f.tone === 'bw' ? 'col' : null; filt(); };
    root.querySelectorAll('#pgDoms button').forEach(b => b.onclick = () => { const d = b.dataset.d; PG.f.dom.has(d) ? PG.f.dom.delete(d) : PG.f.dom.add(d); filt(); });
    root.querySelectorAll('#pgScl button').forEach(b => b.onclick = () => { const d = b.dataset.s; PG.f.scale.has(d) ? PG.f.scale.delete(d) : PG.f.scale.add(d); filt(); });
    $('#pgOut').onclick = () => toggle(false);
  }

  /* the cloud: every shot of the line as a pane on the curve, kept by id so a new line is a glide, not a rebuild */
  function cloud() {
    const ids = N.ids || [], role = N.role || {};
    const shots = ids.map(id => L.byId.get(id)).filter(Boolean);
    const seen = new Set();
    shots.forEach((s, rank) => {
      seen.add(s.id);
      let p = PG.panes.get(s.id);
      if (!p) {
        p = h('div', 'pg-pane'); p._shot = s;
        const img = new Image(); img.src = s.thumb; img.alt = ''; img.draggable = false; p.append(img);
        p.style.setProperty('--sg', api.colorOf(s));
        p.onclick = () => { api.tryShot(s); mark(); };
        p.ondblclick = () => api.keep(s);
        p.title = `${s.title || ''}${s.year ? ' · ' + s.year : ''}`;
        glass.append(p); PG.panes.set(s.id, p);
      }
      p._rank = rank; p._role = role[s.id];
      const grey = s.bw || s.hue == null;
      p._a = grey ? (hashf(s.id) < .5 ? -78 : 78) + (hashf(s.id + 'x') - .5) * 10 : ((s.hue + 180) % 360 - 180) * .38;   // hue around the curve; greyscale at the ends
      let y = ((1 - (s.lum ?? .5)) - .5) * 70 + (hashf(s.id + 'y') - .5) * 12;                                                // bright up, dark down
      if (Math.abs(p._a) < 30 && Math.abs(y) < 24) y = (y < 0 ? -1 : 1) * (24 + Math.abs(y) * .6);                              // keep the middle clear for the chosen shot
      p._y = Math.max(-38, Math.min(38, y));
      p._z = Math.min(rank, 60) * 9;                                                                                           // the better, the nearer
    });
    PG.panes.forEach((p, id) => { if (!seen.has(id)) { p.classList.add('gone'); setTimeout(() => { if (!p.isConnected || !p.classList.contains('gone')) return; p.remove(); PG.panes.delete(id); PG.live.get(id)?.remove(); PG.live.delete(id); }, 900); } else p.classList.remove('gone'); });
    place(); filt(); mark(); poem();
  }
  function place() {
    const R = Math.max(480, innerWidth * .46);
    PG.panes.forEach(p => {
      if (p.classList.contains('gone')) { p.style.transform = `translate(-50%,-50%) rotateY(${(p._a || 0) + PG.turn}deg) translateZ(${-R - 900}px) translateY(${(p._y || 0) * 1.4}vh)`; return; }
      const off = p.classList.contains('off') ? 700 : 0, near = p.classList.contains('n-try') || p.classList.contains('n-now') ? -160 : 0;
      p.style.transform = `translate(-50%,-50%) rotateY(${p._a + PG.turn}deg) translateZ(${-(R + p._z + off + near)}px) translateY(${p._y}vh)`;
      p.style.zIndex = 1000 - p._rank;
    });
  }
  function filt() {
    PG.panes.forEach(p => p.classList.toggle('off', !passes(p._shot)));
    const f = PG.f, sel = $('#pgHueSel');
    if (f.hue) { sel.style.left = (100 * f.hue[0] / 360) + '%'; sel.style.width = (100 * (f.hue[1] - f.hue[0]) / 360) + '%'; sel.hidden = false; } else sel.hidden = true;
    $('#pgTone').dataset.v = f.tone || ''; $('#pgTone').textContent = f.tone === 'bw' ? '◑' : f.tone === 'col' ? '●' : '◐';
    root.querySelectorAll('#pgDoms button').forEach(b => b.classList.toggle('on', f.dom.has(b.dataset.d)));
    root.querySelectorAll('#pgScl button').forEach(b => b.classList.toggle('on', f.scale.has(b.dataset.s)));
    place(); count();
  }
  function mark() {
    const [cur] = api.nowShot(api.A.currentTime);
    PG.panes.forEach(p => {
      p.classList.toggle('n-kept', p._role === 'kept'); p.classList.toggle('n-src', p._role === 'source' || p._role === 'cut'); p.classList.toggle('n-bet', p._role === 'bet');
      p.classList.toggle('n-try', !!N.trying && N.trying.id === p._shot.id); p.classList.toggle('n-now', !!cur && cur.id === p._shot.id);
    });
    place();
  }
  /* the nearest panes play: the ones facing you, best ranked first */
  function live() {
    const cand = [...PG.panes.values()].filter(p => !p.classList.contains('off') && !p.classList.contains('gone')).map(p => [p, Math.cos(((p._a + PG.turn) % 360) * Math.PI / 180) - p._rank / 200]).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([p]) => p);
    PG.live.forEach((v, id) => { const p = PG.panes.get(id); if (!p || !cand.includes(p)) { v.remove(); PG.live.delete(id); } });
    cand.forEach(p => { const s = p._shot; if (PG.live.has(s.id)) return; const src = api.LOOPS.has(s.id) ? `wygwyl/tempest/${s.id}.mp4` : (s.clip || s.video); if (!src) return;
      const v = document.createElement('video'); v.muted = true; v.loop = true; v.playsInline = true; v.src = src;
      v.addEventListener('loadedmetadata', () => { if (!api.LOOPS.has(s.id) && s.read_t != null) try { v.currentTime = Math.max(0, s.read_t - .6); } catch (e) {} }, { once: true });
      v.addEventListener('playing', () => v.classList.add('on'), { once: true }); v.play().catch(() => {}); p.append(v); PG.live.set(s.id, v); });
  }
  function count() {
    const all = [...PG.panes.values()].filter(p => !p.classList.contains('gone')), on = all.filter(p => !p.classList.contains('off'));
    const r = k => all.filter(p => p._role === k).length;
    $('#pgCount').innerHTML = `<b>${on.length}</b>/${all.length} <i>kept</i> ${r('kept')} <i>cut</i> ${r('cut') + r('source')} <i>bet</i> ${r('bet')}`;
  }
  /* the whole poem at the bottom: every line as a tick, kept lines lit */
  function poem() {
    const box = $('#pgPoemStrip'), K = api.KD, nl = api.film('NL'), l = api.line();
    const lines = K.lines.filter(x => x.film === l.film), f = K.films.find(x => x.n === l.film), span = f.p1 - f.p0 || 1;
    box.innerHTML = lines.map(x => { const kept = api.inSpan(nl, x.t0, x.t1)[0], s = kept && L.byId.get(kept.id);
      return `<i class="${x === l ? 'on' : ''}${s ? ' k' : ''}" data-i="${K.lines.indexOf(x)}" style="left:${100 * (x.t0 - f.p0) / span}%;width:${Math.max(.6, 100 * (x.t1 - x.t0) / span)}%${s ? `;background-image:url('${s.thumb}')` : ''}"></i>`; }).join('') + '<b id="pgPh"></b>';
    box.onclick = e => { const i = e.target.dataset?.i; if (i != null) api.setLine(+i, true); };
  }
  function hud(t) {
    const l = api.line(), f = api.KD.films.find(x => x.n === l.film);
    $('#pgLine').textContent = `${l.film}·${String(l.n).padStart(2, '0')}`; $('#pgPoem').textContent = ` ${String(api.KD.lines.indexOf(l) + 1).padStart(3, '0')}`;
    $('#pgFrame').textContent = String(Math.floor(t * 25)).padStart(5, '0'); $('#pgSec').textContent = t.toFixed(2);
    const fr = Math.floor(t * 25), tc = [Math.floor(fr / 90000), Math.floor(fr / 1500) % 60, Math.floor(fr / 25) % 60].map(x => String(x).padStart(2, '0')).join(':') + ':' + String(fr % 25).padStart(2, '0');
    $('#pgTC').textContent = tc;
    const w = api.wordAt(t), k = N.li + ':' + (w ? w.t0 : -1), el = $('#pgWords');
    if (el.dataset.k !== k) { el.dataset.k = k; el.innerHTML = l.words.map(x => `<span class="${x === w ? 'on' : x.t1 < t ? 'past' : ''}">${esc(x.w)}</span>`).join(' '); }
    const ph = $('#pgPh'); if (ph && f) ph.style.left = (100 * (t - f.p0) / ((f.p1 - f.p0) || 1)) + '%';
  }

  function toggle(on) {
    PG.on = on ?? !PG.on; document.body.classList.toggle('precog', PG.on);
    const now = api.nowEl;
    if (PG.on) { $('#pgCenter').append(now); cloud(); } else { $('#stage').append(now); PG.live.forEach(v => v.remove()); PG.live.clear(); }
  }
  PG.toggle = toggle;

  let lastLi = -1, lastIds = '', lastLive = 0;
  function tick() {
    if (PG.on) {
      const t = api.A.currentTime;
      const key = (N.ids || []).join(',');
      if (N.li !== lastLi || key !== lastIds) { lastLi = N.li; lastIds = key; cloud(); }
      hud(t);
      const now = performance.now(); if (now - lastLive > 500) { lastLive = now; mark(); live(); }
    }
    requestAnimationFrame(tick);
  }
  addEventListener('keydown', e => {
    if (typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'Escape' && PG.on) { e.stopImmediatePropagation(); toggle(false); }
    else if ((e.key === 'p' || e.key === 'P') && !PG.on) { e.stopImmediatePropagation(); toggle(true); }
    else if (PG.on && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) { e.preventDefault(); e.stopImmediatePropagation(); api.setLine(N.li + (e.key === 'ArrowDown' ? 1 : -1), true); }
  }, true);
  addEventListener('resize', () => PG.on && place());

  (async function start() {
    for (let k = 0; k < 600 && !(window.N && N.api && N.ids && N.api.nowEl); k++) await new Promise(r => setTimeout(r, 100));
    api = N.api; build(); toggle(!/[#&?]lab\b/.test(location.hash + location.search)); requestAnimationFrame(tick);
    const d = document.getElementById('drive'); if (d) { const b = h('button', '', 'PRECOG'); b.id = 'nPrecog'; b.title = 'The investigation room (P)'; b.onclick = () => toggle(true); d.querySelector('#nVerbs')?.append(b); }
  })();
})();
