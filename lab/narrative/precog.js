/* PRECOG — the Narrative Lab's investigation room: every shot visible, every shot studiable, everything exportable.
 *
 *   THE WALL   every shot of the line (or its beat, or the whole poem) fills the screen at the largest size that fits:
 *              columns run through hue (greyscale first, then red → violet), each column runs light → dark. Filters
 *              remove shots and the rest grow into the room. Tiles glide when the line or the filter changes.
 *   THE SIDE   NOW: the chosen shot at the voice's time, with its sound. STUDY: the shot you point at or click,
 *              playing large, with everything known about it — title, year, signs and their readings, rank and fit
 *              for this line, which cuts and bets used it, subjects, scale, sound, palette, frame strip.
 *   EXPORT     this lab's film as a cineosis EDL (JSON) or CMX3600; the wall's shots as a CSV to study elsewhere.
 * point: study · click: try it under the voice · double click: keep · A–E as everywhere · ↑↓ lines · Esc lab views
 */
(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const h = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const DOMS = ['perception', 'affect', 'action', 'reflection', 'mental', 'break', 'time', 'read'];
  const SCL = [['extreme close-up', 'ECU'], ['close-up', 'CU'], ['medium shot', 'MS'], ['long shot', 'LS'], ['extreme long shot', 'ELS']];
  const PG = window.PG = { on: false, scope: 'line', f: { hue: null, tone: null, dom: new Set(), scale: new Set() }, tiles: new Map(), live: new Map(), study: null, pinned: false, list: [] };
  let root, wall, api;

  const domOf = s => { const n = (s._aff3 && s._aff3[0]) || (s._read && s._read[0]); return n && L.S[n] ? L.S[n].dom : null; };
  const grey = s => s.bw || s.hue == null;
  const passes = s => {
    const f = PG.f;
    if (f.tone === 'bw' && !grey(s)) return false;
    if (f.tone === 'col' && grey(s)) return false;
    if (f.hue && !(!grey(s) && (f.hue[0] <= f.hue[1] ? s.hue >= f.hue[0] && s.hue <= f.hue[1] : s.hue >= f.hue[0] || s.hue <= f.hue[1]))) return false;
    if (f.dom.size && !f.dom.has(domOf(s))) return false;
    if (f.scale.size && !f.scale.has(s.scale)) return false;
    return true;
  };

  /* ---------- the shots in scope, with what we know about each for this moment ---------- */
  function scoped() {
    const l = api.line(), K = api.KD;
    const lines = PG.scope === 'line' ? [l] : PG.scope === 'beat' ? K.lines.filter(x => { const b = K.beats.find(b => (l.t0 + l.t1) / 2 >= b.t0 && (l.t0 + l.t1) / 2 < b.t1); return b && x.t1 > b.t0 && x.t0 < b.t1; }) : K.lines.filter(x => x.film === l.film);
    const ids = [], role = {};
    lines.forEach(x => { const r = x === l ? { ids: N.ids, role: N.role } : api.lineShots(x); r.ids.forEach(id => { if (!role[id]) { role[id] = r.role[id]; ids.push(id); } }); });
    PG.role = role;
    return ids.map(id => L.byId.get(id)).filter(Boolean);
  }
  function rankInfo(id) {                                                        // rank, verdict and fit for the line's beats
    const l = api.line(), K = api.KD; let best = null;
    K.beats.filter(b => b.t1 > l.t0 && b.t0 < l.t1).forEach(b => (api.ND.ranked[b.id] || []).forEach(([x, v, fit], i) => { if (x === id && (!best || i < best.rank)) best = { rank: i + 1, of: api.ND.ranked[b.id].length, v, fit, beat: b.id }; }));
    return best;
  }
  function usedBy(id) {
    const l = api.line(), out = [];
    api.CUTS.forEach(c => { if (api.inSpan(api.film(c), l.t0, l.t1).some(s => s.id === id)) out.push(c); });
    ['NL', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'].forEach(c => { if (api.film(c).some(s => s.id === id)) out.push(c === 'NL' ? 'this lab' : c); });
    return out;
  }

  /* ---------- the room ---------- */
  function build() {
    root = h('div', ''); root.id = 'precog';
    root.innerHTML = `
      <div class="pg-top">
        <span class="pg-n"><b id="pgLine"></b> <span id="pgIdx"></span></span>
        <span class="pg-words" id="pgWords"></span>
        <span class="pg-n"><span id="pgFrame"></span> <b id="pgSec"></b></span>
        <span class="pg-n"><b id="pgTC"></b></span>
        <button id="pgOut" title="Back to the lab views (Esc)">⌗</button>
      </div>
      <div class="pg-main">
        <div class="pg-wall" id="pgWall"></div>
        <div class="pg-side">
          <div class="pg-now" id="pgNow"><span class="pg-tag">now</span></div>
          <div class="pg-study" id="pgStudy"></div>
        </div>
      </div>
      <div class="pg-bot">
        <span class="pg-scope" id="pgScope">${['line', 'beat', 'poem'].map(k => `<button data-k="${k}" title="Show every shot of the ${k}">${k}</button>`).join('')}</span>
        <div class="pg-hue" id="pgHue" title="Drag across to keep a range of hue · tap to clear"><i id="pgHueSel" hidden></i></div>
        <button class="pg-tone" id="pgTone" title="All · greyscale · colour">◐</button>
        <span class="pg-doms" id="pgDoms">${DOMS.map(d => `<button data-d="${d}" style="--c:${DOMC[d]}" title="${esc(DOMN[d])}"></button>`).join('')}</span>
        <span class="pg-scl" id="pgScl">${SCL.map(([k, a]) => `<button data-s="${esc(k)}" title="${esc(k)}">${a}</button>`).join('')}</span>
        <div class="pg-poem" id="pgPoemStrip"></div>
        <span class="pg-n" id="pgCount"></span>
        <span class="pg-exp"><button id="pgEDL" title="This lab's film as a cineosis EDL (JSON)">EDL</button><button id="pgCMX" title="This lab's film as CMX3600 for an editor">CMX</button><button id="pgCSV" title="Every shot on the wall, with what is known, as CSV">LIST</button></span>
      </div>`;
    document.body.append(root);
    wall = $('#pgWall');
    const hue = $('#pgHue'); let hs = null, moved = false;
    const hueAt = e => { const r = hue.getBoundingClientRect(); return Math.max(0, Math.min(359, 360 * (e.clientX - r.left) / r.width)); };
    hue.addEventListener('pointerdown', e => { hue.setPointerCapture(e.pointerId); hs = hueAt(e); moved = false; });
    hue.addEventListener('pointermove', e => { if (hs == null) return; const b = hueAt(e); if (Math.abs(b - hs) > 6) { moved = true; PG.f.hue = [Math.min(hs, b), Math.max(hs, b)]; filt(); } });
    hue.addEventListener('pointerup', () => { if (!moved) PG.f.hue = null; hs = null; filt(); });
    $('#pgTone').onclick = () => { PG.f.tone = PG.f.tone == null ? 'bw' : PG.f.tone === 'bw' ? 'col' : null; filt(); };
    root.querySelectorAll('#pgDoms button').forEach(b => b.onclick = () => { const d = b.dataset.d; PG.f.dom.has(d) ? PG.f.dom.delete(d) : PG.f.dom.add(d); filt(); });
    root.querySelectorAll('#pgScl button').forEach(b => b.onclick = () => { const d = b.dataset.s; PG.f.scale.has(d) ? PG.f.scale.delete(d) : PG.f.scale.add(d); filt(); });
    root.querySelectorAll('#pgScope button').forEach(b => b.onclick = () => { PG.scope = b.dataset.k; fill(); });
    $('#pgOut').onclick = () => toggle(false);
    $('#pgEDL').onclick = () => download('wygwyl-NL.cineosis-edl.json', edlJSON(), 'application/json');
    $('#pgCMX').onclick = () => download('wygwyl-NL.edl', edlCMX(), 'text/plain');
    $('#pgCSV').onclick = () => download(`wygwyl-${api.line().id}-${PG.scope}-shots.csv`, csv(), 'text/csv');
    new ResizeObserver(() => PG.on && layout()).observe(wall);
    let wheelAcc = 0;
    wall.addEventListener('wheel', e => { if (e.ctrlKey) return; e.preventDefault(); wheelAcc += e.deltaY; if (Math.abs(wheelAcc) > 120) { api.setLine(N.li + Math.sign(wheelAcc), true); wheelAcc = 0; } }, { passive: false });
  }

  /* ---------- the wall ---------- */
  function fill() {
    const shots = scoped(), seen = new Set();
    shots.forEach(s => {
      seen.add(s.id); let t = PG.tiles.get(s.id);
      if (!t) {
        t = h('div', 'pg-t'); t._shot = s; const img = new Image(); img.src = s.thumb; img.alt = ''; img.draggable = false; img.loading = 'lazy'; t.append(img);
        t.style.setProperty('--sg', api.colorOf(s));
        t.onmouseenter = () => { if (!PG.pinned) study(s); live([s]); };
        t.onclick = () => { PG.pinned = true; study(s); api.tryShot(s); marks(); };
        t.ondblclick = () => api.keep(s);
        wall.append(t); PG.tiles.set(s.id, t);
      }
      t._role = PG.role[s.id];
    });
    PG.tiles.forEach((t, id) => { if (!seen.has(id)) { t.remove(); PG.tiles.delete(id); PG.live.get(id)?.remove(); PG.live.delete(id); } });
    root.querySelectorAll('#pgScope button').forEach(b => b.classList.toggle('on', b.dataset.k === PG.scope));
    filt(); poem();
  }
  function filt() {
    const on = [...PG.tiles.values()].filter(t => passes(t._shot));
    PG.tiles.forEach(t => t.classList.toggle('off', !on.includes(t)));
    // columns through hue (greyscale first), each column light → dark
    on.sort((a, b) => { const A = a._shot, B = b._shot, ka = grey(A) ? -1 : A.hue, kb = grey(B) ? -1 : B.hue; return ka - kb || (A.lum ?? .5) - (B.lum ?? .5); });
    PG.list = on;
    const f = PG.f, sel = $('#pgHueSel');
    if (f.hue) { sel.style.left = (100 * f.hue[0] / 360) + '%'; sel.style.width = (100 * (f.hue[1] - f.hue[0]) / 360) + '%'; sel.hidden = false; } else sel.hidden = true;
    $('#pgTone').textContent = f.tone === 'bw' ? '◑' : f.tone === 'col' ? '●' : '◐';
    root.querySelectorAll('#pgDoms button').forEach(b => b.classList.toggle('on', f.dom.has(b.dataset.d)));
    root.querySelectorAll('#pgScl button').forEach(b => b.classList.toggle('on', f.scale.has(b.dataset.s)));
    layout(); marks(); count();
  }
  function layout() {                                                             // the largest 4:3 tile at which every shot fits: no scrolling, no margin
    const W = wall.clientWidth, H = wall.clientHeight, n = PG.list.length, g = 2; if (!W || !H) return;
    let best = { rows: 1, cols: n || 1, tw: 0, th: 0 };
    for (let rows = 1; rows <= Math.max(1, n); rows++) {
      const cols = Math.ceil(n / rows), th = Math.min((H - g * (rows - 1)) / rows, ((W - g * (cols - 1)) / cols) * .75), tw = th / .75;
      if (th > best.th) best = { rows, cols, tw, th };
      if (rows * 20 > H) break;
    }
    const { rows, cols, tw, th } = best, ox = (W - (cols * tw + (cols - 1) * g)) / 2, oy = (H - (rows * th + (rows - 1) * g)) / 2;
    PG.list.forEach((t, i) => { const c = Math.floor(i / rows), r = i % rows; Object.assign(t.style, { left: ox + c * (tw + g) + 'px', top: oy + r * (th + g) + 'px', width: tw + 'px', height: th + 'px' }); });
    wall.style.setProperty('--tw', tw + 'px');
  }
  function marks() {
    const [cur] = api.nowShot(api.A.currentTime);
    PG.tiles.forEach(t => {
      const id = t._shot.id;
      t.classList.toggle('n-kept', t._role === 'kept'); t.classList.toggle('n-src', t._role === 'source' || t._role === 'cut'); t.classList.toggle('n-bet', t._role === 'bet');
      t.classList.toggle('n-try', !!N.trying && N.trying.id === id); t.classList.toggle('n-now', !!cur && cur.id === id); t.classList.toggle('n-study', PG.study === t._shot);
    });
  }
  /* the best-ranked visible tiles play, and whatever you point at */
  function live(extra = []) {
    const want = [...extra, ...PG.list.slice().sort((a, b) => rankOf(a) - rankOf(b)).slice(0, 12).map(t => t._shot)];
    const ids = new Set(want.map(s => s.id));
    PG.live.forEach((v, id) => { if (!ids.has(id)) { v.remove(); PG.live.delete(id); } });
    want.forEach(s => { if (PG.live.has(s.id)) return; const t = PG.tiles.get(s.id); if (!t || t.classList.contains('off')) return; const src = api.LOOPS.has(s.id) ? `wygwyl/tempest/${s.id}.mp4` : (s.clip || s.video); if (!src) return;
      const v = document.createElement('video'); v.muted = true; v.loop = true; v.playsInline = true; v.src = src;
      v.addEventListener('loadedmetadata', () => { if (!api.LOOPS.has(s.id) && s.read_t != null) try { v.currentTime = Math.max(0, s.read_t - .6); } catch (e) {} }, { once: true });
      v.addEventListener('playing', () => v.classList.add('on'), { once: true }); v.play().catch(() => {}); t.append(v); PG.live.set(s.id, v); });
  }
  const ROLEORDER = { kept: 0, source: 1, cut: 2, bet: 3, keep: 4, maybe: 5, floor: 6 };
  const rankOf = t => (ROLEORDER[t._role] ?? 7) * 1000 + (N.ids ? Math.max(0, N.ids.indexOf(t._shot.id)) : 0);

  /* ---------- study: everything known about one shot ---------- */
  function study(s) {
    PG.study = s; const box = $('#pgStudy'), r = rankInfo(s.id), used = usedBy(s.id), role = PG.role[s.id];
    const signs = (s.signs || []).slice(0, 3), dom = domOf(s);
    box.innerHTML = `<div class="pg-sv" style="--sg:${api.colorOf(s)}"><video muted playsinline loop preload="auto"></video><span class="pg-tag">study</span><button class="pg-snd" title="Hear this shot">♪</button></div>
      <div class="pg-facts">
        <div class="pg-ti"><b>${esc(s.title || 'untitled')}</b> ${s.year ?? ''}</div>
        <div class="pg-kv">
          <i>role</i><span>${esc(role || '—')}${r ? ` · rank ${r.rank}/${r.of} · fit ${r.fit} · ${r.v === 'K' ? 'KEEP' : r.v === 'M' ? 'MAYBE' : 'FLOOR'} · beat ${r.beat}` : ''}</span>
          <i>used by</i><span>${used.length ? esc(used.join(' · ')) : 'nobody yet'}</span>
          <i>sign</i><span>${(s._aff3 || []).slice(0, 3).map(n => chip(n, 'sm')).join('')} ${dom ? esc(DOMN[dom]) : ''}</span>
          <i>scale</i><span>${esc(s.scale || '—')}${s.audio ? ` · sound: ${esc(s.audio.kind)}` : ''}${s.bw ? ' · b/w' : ''}</span>
          <i>subjects</i><span>${(s.subjects || []).slice(0, 4).map(x => esc(x.label)).join(' · ') || '—'}</span>
          <i>colour</i><span class="pg-pal">${(s.palette || []).map(c => `<b style="background:${esc(c)}" title="${esc(c)}"></b>`).join('')}</span>
        </div>
        ${signs.length ? `<div class="pg-read">${signs.map(x => `${chip(String(x.n), 'sm')} ${esc((x.note || '').slice(0, 150))}`).join('<br>')}</div>` : ''}
        ${s.strip ? `<div class="pg-strip" style="background-image:url('${esc(s.strip)}')" title="the shot's frames"></div>` : ''}
        <div class="pg-acts"><button data-a="try">B try</button><button data-a="keep">C keep</button><button data-a="flag">D flag</button><button data-a="ins">inspect</button>${s.page || s.video ? `<a href="${esc(s.page || s.video)}" target="_blank" rel="noopener">source ↗</a>` : ''}</div>
      </div>`;
    const v = box.querySelector('video'); v.src = s.clip || s.video; v.addEventListener('loadedmetadata', () => { if (s.read_t != null) try { v.currentTime = Math.max(0, s.read_t - .6); } catch (e) {} }, { once: true }); v.play().catch(() => {});
    box.querySelector('.pg-snd').onclick = e => { v.muted = !v.muted; e.currentTarget.classList.toggle('on', !v.muted); };
    box.querySelectorAll('.pg-acts button').forEach(b => b.onclick = () => { const a = b.dataset.a; if (a === 'try') api.tryShot(s); else if (a === 'keep') api.keep(s); else if (a === 'flag') { api.tryShot(s); api.verb('D'); } else if (a === 'ins') { N.alt = true; Inspector.open(s, PG.list.map(t => t._shot)); N.alt = false; toggle(false); } marks(); });
    marks();
  }

  /* ---------- export ---------- */
  const FPS = 25, tc = t => { const f = Math.round(Math.max(0, t) * FPS); return [Math.floor(f / 90000), Math.floor(f / 1500) % 60, Math.floor(f / FPS) % 60, f % FPS].map(x => String(x).padStart(2, '0')).join(':'); };
  const nlSeats = () => { try { return JSON.parse(localStorage.getItem(api.FILMKEY('NL'))) || []; } catch (e) { return []; } };
  function edlJSON() { const seats = nlSeats(); return JSON.stringify({ format: 'cineosis-edl/1', title: 'WYGWYL', bet: 'NL', made: new Date().toISOString(), clock: { audio: 'WYGWYL_Suite_Audio.mp3', duration: api.KD.duration, fps: FPS },
    events: seats.map((s, i) => ({ n: i + 1, rec: [s.t0, s.t1], words: s.text, clip: s.clip, src: [s.clip.in || 0, (s.clip.in || 0) + s.t1 - s.t0], by: s.by, bet: 'NL', why: s.why, flag: !!s.flag })) }, null, 1); }
  function edlCMX() { const o = ['TITLE: WYGWYL NARRATIVE LAB', 'FCM: NON-DROP FRAME', ''];
    nlSeats().forEach((s, i) => { const a = s.clip.in || 0; o.push(`${String(i + 1).padStart(3, '0')}  AX       V     C        ${tc(a)} ${tc(a + s.t1 - s.t0)} ${tc(s.t0)} ${tc(s.t1)}`, `* FROM CLIP NAME: ${s.clip.title}${s.clip.year ? ' (' + s.clip.year + ')' : ''}`, `* SOURCE FILE: ${s.clip.video || ''}`, `* WORDS: ${s.text}`, ''); });
    return o.join('\n'); }
  function csv() {
    const q = v => `"${String(v ?? '').replace(/"/g, '""')}"`, rows = [['id', 'title', 'year', 'role', 'rank', 'verdict', 'fit', 'beat', 'hue', 'lum', 'bw', 'scale', 'sign', 'domain', 'subjects', 'used_by', 'video', 'thumb']];
    PG.list.forEach(t => { const s = t._shot, r = rankInfo(s.id) || {}; rows.push([s.id, s.title, s.year, PG.role[s.id], r.rank, r.v, r.fit, r.beat, s.hue, s.lum, s.bw ? 1 : 0, s.scale, (s._aff3 || [])[0], domOf(s), (s.subjects || []).map(x => x.label).join('|'), usedBy(s.id).join('|'), s.video, s.thumb]); });
    return rows.map(r => r.map(q).join(',')).join('\n');
  }
  function download(name, text, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); toast?.(`exported ${name}`); }

  /* ---------- HUD, counts, the poem ---------- */
  function count() {
    const all = [...PG.tiles.values()], r = k => all.filter(t => t._role === k).length;
    $('#pgCount').innerHTML = `<b>${PG.list.length}</b>/${all.length} <i>kept</i>${r('kept')} <i>cut</i>${r('cut') + r('source')} <i>bet</i>${r('bet')}`;
  }
  function poem() {
    const box = $('#pgPoemStrip'), K = api.KD, nl = api.film('NL'), l = api.line();
    const lines = K.lines.filter(x => x.film === l.film), f = K.films.find(x => x.n === l.film), span = (f.p1 - f.p0) || 1;
    box.innerHTML = lines.map(x => { const kept = api.inSpan(nl, x.t0, x.t1)[0], s = kept && L.byId.get(kept.id);
      return `<i class="${x === l ? 'on' : ''}${s ? ' k' : ''}" data-i="${K.lines.indexOf(x)}" title="line ${x.n}" style="left:${100 * (x.t0 - f.p0) / span}%;width:${Math.max(.6, 100 * (x.t1 - x.t0) / span)}%${s ? `;background-image:url('${s.thumb}')` : ''}"></i>`; }).join('') + '<b id="pgPh"></b>';
    box.onclick = e => { const i = e.target.dataset?.i; if (i != null) api.setLine(+i, true); };
  }
  function hud(t) {
    const l = api.line(), f = api.KD.films.find(x => x.n === l.film);
    $('#pgLine').textContent = `${l.film}·${String(l.n).padStart(2, '0')}`; $('#pgIdx').textContent = String(api.KD.lines.indexOf(l) + 1).padStart(3, '0');
    const fr = Math.floor(t * 25); $('#pgFrame').textContent = String(fr).padStart(5, '0'); $('#pgSec').textContent = t.toFixed(2);
    $('#pgTC').textContent = [Math.floor(fr / 90000), Math.floor(fr / 1500) % 60, Math.floor(fr / 25) % 60].map(x => String(x).padStart(2, '0')).join(':') + ':' + String(fr % 25).padStart(2, '0');
    const w = api.wordAt(t), k = N.li + ':' + (w ? w.t0 : -1), el = $('#pgWords');
    if (el.dataset.k !== k) { el.dataset.k = k; el.innerHTML = l.words.map(x => `<span class="${x === w ? 'on' : x.t1 < t ? 'past' : ''}">${esc(x.w)}</span>`).join(' '); }
    const ph = $('#pgPh'); if (ph && f) ph.style.left = (100 * (t - f.p0) / ((f.p1 - f.p0) || 1)) + '%';
  }

  function toggle(on) {
    PG.on = on ?? !PG.on; document.body.classList.toggle('precog', PG.on);
    const now = api.nowEl;
    if (PG.on) { $('#pgNow').append(now); fill(); if (!PG.study) { const [c] = api.nowShot(api.A.currentTime); if (c) study(c); } }
    else { $('#stage').append(now); PG.live.forEach(v => v.remove()); PG.live.clear(); }
  }
  PG.toggle = toggle;

  let lastLi = -1, lastIds = '', lastLive = 0;
  function tick() {
    if (PG.on) {
      const t = api.A.currentTime, key = (N.ids || []).join(',');
      if (N.li !== lastLi || key !== lastIds) { const moved = N.li !== lastLi; lastLi = N.li; lastIds = key; if (moved) PG.pinned = false; fill(); if (!PG.pinned) { const [c] = api.nowShot(t); if (c) study(c); } }
      hud(t);
      const now = performance.now(); if (now - lastLive > 600) { lastLive = now; marks(); live(PG.study ? [PG.study] : []); }
    }
    requestAnimationFrame(tick);
  }
  addEventListener('keydown', e => {
    if (typing(e) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'Escape' && PG.on) { e.stopImmediatePropagation(); toggle(false); }
    else if ((e.key === 'p' || e.key === 'P') && !PG.on) { e.stopImmediatePropagation(); toggle(true); }
    else if (PG.on && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) { e.preventDefault(); e.stopImmediatePropagation(); api.setLine(N.li + (e.key === 'ArrowDown' ? 1 : -1), true); }
  }, true);

  (async function start() {
    for (let k = 0; k < 600 && !(window.N && N.api && N.ids && N.api.nowEl); k++) await new Promise(r => setTimeout(r, 100));
    api = N.api; build(); toggle(!/[#&?]lab\b/.test(location.hash + location.search)); requestAnimationFrame(tick);
    const d = document.getElementById('drive'); if (d) { const b = h('button', '', 'PRECOG'); b.id = 'nPrecog'; b.title = 'The investigation room (P)'; b.onclick = () => toggle(true); d.querySelector('#nVerbs')?.append(b); }
  })();
})();
