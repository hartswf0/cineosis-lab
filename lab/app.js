/* CINEOSIS LAB — front end (plain JS, no build).
 *
 * Modules, in order:
 *   UTIL · DATA · FILTER · FACETS · TIP · VGRID · WALL · MAP · RING · STRATA · CUTS · REEL · INSPECTOR · LIVE · SHELL
 *
 * Every analysis field in lab-data.json (palette/hue/lum/sat/subjects/scale/xy/sim/strip/cutouts/audio) may be null;
 * each mode degrades to a sensible fallback and lights up when the field arrives (press ↻ to reload the data).
 */
'use strict';

/* ================================================================ UTIL */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
function el(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const fmt = n => Number(n).toLocaleString('en-US');
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const FPS = 24;
const ARCHIVE = 'https://www.movingimagearchive.com';

const DOMC = { perception: '#e9d9a8', affect: '#f0b9a4', action: '#e7a37c', reflection: '#b9cfa0', mental: '#a9c9c9', break: '#d9d3c7', time: '#b8b3d8', read: '#d9b8d2' };
const DOMN = { perception: 'Perception', affect: 'Affect', action: 'Action', reflection: 'Reflection', mental: 'Mental', break: 'Opsign · Sonsign', time: 'Time', read: 'Lectosign' };
const SCALES = ['extreme close-up', 'close-up', 'medium shot', 'long shot', 'extreme long shot'];
const SCALE_AB = { 'extreme close-up': 'ECU', 'close-up': 'CU', 'medium shot': 'MS', 'long shot': 'LS', 'extreme long shot': 'ELS' };
const AUDIO_KINDS = ['speech', 'music', 'sound', 'silence', 'none'];
const HUE_NAMES = ['red', 'orange', 'yellow', 'lime', 'green', 'jade', 'cyan', 'azure', 'blue', 'violet', 'magenta', 'rose'];
const hueBand = h => Math.floor(((h + 15) % 360) / 30);
const HB_GREY = 12, HB_NONE = 13;
const hbLabel = b => b === HB_GREY ? 'greyscale' : b === HB_NONE ? 'not analysed' : HUE_NAMES[b];

function tc(sec) {
  if (!isFinite(sec) || sec < 0) sec = 0;
  const f = Math.floor(sec * FPS + 1e-6), ff = f % FPS, s = Math.floor(f / FPS);
  return [Math.floor(s / 3600), Math.floor(s / 60) % 60, s % 60, ff].map(v => String(v).padStart(2, '0')).join(':');
}
const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
function hashf(str) { let h = 2166136261; for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return ((h >>> 0) % 100000) / 100000; }
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function rafThrottle(fn) { let q = false; return () => { if (q) return; q = true; requestAnimationFrame(() => { q = false; fn(); }); }; }
function typing(e) { const t = e.target; return t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable); }

let toastT;
function toast(msg, ms = 2600) {
  const t = $('#toast'); t.textContent = msg; t.hidden = false;
  clearTimeout(toastT); toastT = setTimeout(() => { t.hidden = true; }, ms);
}

/* ================================================================ DATA */
const L = {
  signs: [], S: {}, sidx: {}, shots: [], byId: new Map(), live: [], liveQ: '', showLive: true,
  assignments: [], has: {}, subjCounts: {}, loadedAt: 0,
};

function sign(n) { return L.S[n]; }
function signColor(n) { const s = L.S[n]; return s ? DOMC[s.dom] : '#888'; }
function chip(n, cls = '') {
  const s = L.S[n]; if (!s) return '';
  return `<span class="chip ${cls}" style="--c:${DOMC[s.dom]}" title="${esc(s.name)}">${esc(s.symbol)}</span>`;
}

function prep(s, i) {
  s._i = i;
  s._read = (s.signs || []).map(e => String(e.n));
  s._found = [...new Set((s.found || []).map(f => String(f.n)).filter(n => L.S[n]))];
  s._any = [...new Set([...s._read, ...s._found])];
  s._aff3 = (s.aff_top || []).slice(0, 3).map(x => String(x[0]));
  s._affMax = s.affinity ? Math.max(...Object.values(s.affinity)) : 0;
  s._conf = s.signs && s.signs.length ? Math.max(...s.signs.map(e => e.conf ?? 0)) : -1;
  s._text = [s.title, s.year, s.decade ? s.decade + 's' : '',
    ...(s.signs || []).map(e => (e.note || '') + ' ' + (e.flip || '')),
    ...(s.found || []).map(f => f.q), ...(s.subjects || []).map(x => x.label), s.scale, s.audio && s.audio.kind,
    ...(s.cutouts || []).map(c => c.label), ...s._any.map(n => L.S[n] ? L.S[n].name : '')]
    .filter(Boolean).join(' \u0001 ').toLowerCase();
  s._hb = s.hue != null ? hueBand(s.hue) : (s.palette ? HB_GREY : HB_NONE);
  s._dur = Math.max(0.1, (s.end || 0) - (s.start || 0));
  s._dot = dotColor(s);
  s._cuts = cutItems(s);
  s._col = s.collections && s.collections.length ? s.collections : ['cineosis'];
}
/** normalised cut-out list: SAM 2 tracked segments when present, else the older single-frame cut-outs */
function cutItems(s) {
  const g = s.segments;
  if (g && g.objects && g.objects.length) return g.objects.map(o => ({
    png: o.png, label: o.label || 'figure', desc: o.desc || o.label || 'figure', role: o.role || 'figure', src: o.src,
    bbox: o.sprite && o.union ? o.union : o.bbox, sprite: o.sprite || null, sw: o.sw, sh: o.sh, frames: g.frames, fps: g.fps, boxes: o.boxes }));
  return (s.cutouts || []).map(c => ({ png: c.png, label: c.label || 'figure', desc: c.label || 'figure', role: 'figure', bbox: c.bbox, sprite: null }));
}
function dotColor(s) {
  if (s.palette && s.palette[0]) return s.palette[0];
  if (s.hue != null) return `hsl(${s.hue},${Math.round((s.sat ?? .4) * 70)}%,${Math.round((s.lum ?? .5) * 70 + 15)}%)`;
  if (s.lum != null) { const v = Math.round(s.lum * 200 + 30); return `rgb(${v},${v},${v})`; }
  return s._read.length ? (s.bw ? '#9d9d9d' : '#b3aa9c') : (s.bw ? '#5a5a5a' : '#6d665e');
}

async function loadData(silent) {
  const r = await fetch('lab-data.json', { cache: 'no-store' });
  if (!r.ok) throw new Error('lab-data.json ' + r.status);
  const d = await r.json();
  L.signs = d.signs.map(s => ({ ...s, n: String(s.n) }));
  L.S = Object.fromEntries(L.signs.map(s => [s.n, s]));
  L.sidx = Object.fromEntries(L.signs.map((s, i) => [s.n, i]));
  L.shots = d.shots;
  L.byId = new Map();
  L.shots.forEach((s, i) => { prep(s, i); L.byId.set(s.id, s); });
  // re-attach live layer objects that are in the corpus
  L.live = L.live.map(s => { if (s._liveOnly) return s; const k = L.byId.get(s.id); if (k) { k._live = true; k._liveHit = true; return k; } return s; });
  const rows = await probeServer();
  L.server = !!rows;
  L.assignments = L.server ? rows : [...(d.assignments || []), ...Store.get()];
  L.wyg = d.wygwyl || null;
  L.wygCands = new Map();
  for (const s of L.shots) if (s.wygwyl && s.wygwyl.beats) for (const b of s.wygwyl.beats) { const k = String(b); if (!L.wygCands.has(k)) L.wygCands.set(k, []); if (!L.wygCands.get(k).includes(s)) L.wygCands.get(k).push(s); }
  const H = L.has = {};
  H.xy = L.shots.some(s => s.xy); H.hue = L.shots.some(s => s.hue != null); H.palette = L.shots.some(s => s.palette);
  H.strip = L.shots.some(s => s.strip); H.cut = L.shots.some(s => s._cuts.length); H.seg = L.shots.some(s => s.segments && s.segments.objects && s.segments.objects.length);
  H.subj = L.shots.some(s => s.subjects && s.subjects.length); H.scale = L.shots.some(s => s.scale);
  H.audio = L.shots.some(s => s.audio); H.sim = L.shots.some(s => s.sim != null); H.lum = L.shots.some(s => s.lum != null);
  const titles = [...new Set(L.shots.map(s => s.title || ''))].sort((a, b) => a.localeCompare(b));
  const tr = new Map(titles.map((t, i) => [t, i]));
  L.shots.forEach(s => { s._film = tr.get(s.title || '') * 1e5 + (s.start || 0); });
  L.loadedAt = Date.now();
  if (!silent) console.info(`[lab] ${L.shots.length} shots · ${L.signs.length} signs · analysis:`, H);
}

/* ---- server vs static (GitHub Pages) mode */
/** GET /api/assignments with a 2 s timeout: an array back means server.py is running; anything else → static mode */
async function probeServer() {
  if (location.protocol === 'file:' || /\.github\.io$/.test(location.hostname)) return null; // Pages: no API, skip the 404
  const ctl = new AbortController(), t = setTimeout(() => ctl.abort(), 2000);
  try {
    const r = await fetch('/api/assignments', { cache: 'no-store', signal: ctl.signal });
    if (!r.ok || !(r.headers.get('content-type') || '').includes('json')) return null;
    const rows = await r.json();
    return Array.isArray(rows) ? rows : null;
  } catch (e) { return null; } finally { clearTimeout(t); }
}
/** sub-shots saved in this browser when there is no server */
const Store = {
  key: 'lab.assignments',
  get() { try { const v = JSON.parse(localStorage.getItem(this.key) || '[]'); return Array.isArray(v) ? v : []; } catch (e) { return []; } },
  add(row) { const rows = this.get(); rows.push(row); try { localStorage.setItem(this.key, JSON.stringify(rows)); return true; } catch (e) { return false; } },
};
function exportAssignments() {
  const rows = L.server ? L.assignments : Store.get();
  if (!rows.length) { toast('no saved sub-shots yet'); return; }
  const url = URL.createObjectURL(new Blob([JSON.stringify(rows, null, 1)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = 'assignments.json';
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 5000);
  toast(`exported ${rows.length} sub-shot${rows.length > 1 ? 's' : ''}`);
}
const STATIC_NOTE = 'live archive search needs the local server — clone the repo and run python3 lab/server.py';

/* ================================================================ FILTER */
const F = {
  col: 'both', signs: new Set(), smode: 'corpus', dec: new Set(), color: 'all', hue: null, subj: new Set(), scale: new Set(),
  cut: false, audio: new Set(), q: '', terms: [], signTerms: [], decTerms: [],
};
const SORT = { key: 'sign', dir: 1 };
let GROUP = 'none';

function inHue(h, band) { const [a, b] = band; return a <= b ? h >= a && h <= b : h >= a || h <= b; }
const PRED = {
  signs: s => !F.signs.size || signList(s).some(n => F.signs.has(n)),
  read: s => F.smode !== 'read' || s._read.length > 0,
  dec: s => !F.dec.size || F.dec.has(s.decade ?? -1),
  color: s => F.color === 'all' || (F.color === 'bw' ? s.bw : !s.bw),
  hue: s => !F.hue || (s.hue != null && inHue(s.hue, F.hue)),
  subj: s => !F.subj.size || (s.subjects || []).some(x => F.subj.has(x.label)),
  scale: s => !F.scale.size || F.scale.has(s.scale),
  cut: s => !F.cut || s._cuts.length > 0,
  col: s => F.col === 'both' || s._col.includes(F.col),
  audio: s => !F.audio.size || (s.audio && F.audio.has(s.audio.kind)),
  q: s => {
    if (!F.terms.length && !F.signTerms.length && !F.decTerms.length) return true;
    for (const t of F.terms) if (!s._text.includes(t)) return false;
    for (const n of F.signTerms) if (!s._any.includes(n)) return false;
    for (const d of F.decTerms) if (s.decade !== d) return false;
    return true;
  },
};
const FKEYS = Object.keys(PRED);

function parseQuery(q) {
  F.q = q; F.terms = []; F.signTerms = []; F.decTerms = [];
  const bySym = {}; L.signs.forEach(s => { bySym[s.symbol.toLowerCase()] = s.n; bySym[s.n.toLowerCase()] = s.n; });
  for (const raw of q.toLowerCase().split(/\s+/).filter(Boolean)) {
    if (raw[0] === '#' && bySym[raw.slice(1)]) { F.signTerms.push(bySym[raw.slice(1)]); continue; }
    const m = raw.match(/^(1[89]\d0|20[0-2]0)s$/); if (m) { F.decTerms.push(+m[1]); continue; }
    F.terms.push(raw);
  }
}

/** which signs a shot counts for under the current sign mode */
function signList(s) { return F.smode === 'read' ? s._read : F.smode === 'machine' ? s._aff3 : s._any; }
function signOf(s) {
  if (F.signs.size) { const hit = signList(s).find(n => F.signs.has(n)); if (hit) return hit; }
  return s._read[0] || s._found[0] || null;
}
function entryOf(s, n) { return (s.signs || []).find(e => String(e.n) === n) || null; }

const SORTKEY = {
  sign: s => { const n = signOf(s); return n == null ? null : L.sidx[n] * 1000 + (s._read.includes(n) ? 100 - Math.max(0, (entryOf(s, n) || {}).conf || 0) : 500); },
  hue: s => s.hue != null ? s.hue + (s.lum ?? .5) * .01 : (s.palette || s.lum != null ? 400 + (s.lum ?? 0) : null),
  lum: s => s.lum,
  year: s => s.year,
  conf: s => s._conf >= 0 ? -s._conf : null,
  sim: s => s.sim,
  film: s => s._film,
  aff: s => { if (!s.affinity) return null; const n = F.signs.size ? [...F.signs][0] : null; return -(n ? (s.affinity[n] ?? 0) : s._affMax); },
};
function sortShots(arr) {
  const kf = SORTKEY[SORT.key] || SORTKEY.sign, d = SORT.dir;
  const keyed = arr.map(s => [kf(s), s]);
  keyed.sort((A, B) => {
    const a = A[0], b = B[0];
    if (a == null && b == null) return A[1]._i - B[1]._i;
    if (a == null) return 1; if (b == null) return -1;
    return (a - b) * d || A[1]._i - B[1]._i;
  });
  return keyed.map(k => k[1]);
}

const GROUPS = {
  sign: s => { const n = signOf(s); return n ? { k: 'S' + n, o: L.sidx[n], label: `${chip(n)} <b>${esc(L.S[n].name)}</b> <em>${esc(L.S[n].image)} · ${esc(n)}</em>` } : { k: 'S-', o: 999, label: '<b>no sign</b>' }; },
  decade: s => s.decade ? { k: 'D' + s.decade, o: s.decade, label: `<b>${s.decade}s</b>` } : { k: 'D-', o: 9999, label: '<b>undated</b>' },
  hue: s => ({ k: 'H' + s._hb, o: s._hb, label: `<i class="sw" style="background:${s._hb < 12 ? `hsl(${s._hb * 30},62%,55%)` : s._hb === HB_GREY ? '#888' : 'transparent'}"></i><b>${hbLabel(s._hb)}</b>` }),
  subject: s => { const l = s.subjects && s.subjects[0] && s.subjects[0].label; return l ? { k: 'U' + l, o: -(L.subjCounts[l] || 0), label: `<b>${esc(l)}</b>` } : { k: 'U-', o: 1e9, label: '<b>no subject yet</b>' }; },
  scale: s => { const i = SCALES.indexOf(s.scale); return i >= 0 ? { k: 'C' + i, o: i, label: `<b>${s.scale}</b> <em>${SCALE_AB[s.scale]}</em>` } : { k: 'C-', o: 99, label: '<b>scale not analysed</b>' }; },
};

let VIEW = [];          // filtered + sorted corpus shots
let GROUPED = null;     // [{k,label,items}] when grouping
let COUNTS = {};
let viewSeq = 0;

function liveView() { return L.showLive ? L.live : []; }
/** the list a mode shows, live layer first */
function viewList() { return [...liveView(), ...VIEW.filter(s => !s._liveHit || !L.showLive)]; }

function compute() {
  const P = FKEYS.map(k => PRED[k]), nF = P.length;
  const C = { signs: {}, dec: {}, color: { bw: 0, col: 0 }, hue: new Array(36).fill(0), grey: 0, subj: {}, scale: {}, cut: 0, audio: {}, read: 0, col: { cineosis: 0, wygwyl: 0, both: 0 } };
  const out = [];
  for (const s of L.shots) {
    let fails = 0, fk = -1;
    for (let k = 0; k < nF; k++) if (!P[k](s)) { fails++; fk = k; if (fails > 1) break; }
    s._in = fails === 0;
    if (fails > 1) continue;
    if (fails === 0) out.push(s);
    const only = fails === 1 ? FKEYS[fk] : null;
    if (!only || only === 'signs') for (const n of signList(s)) C.signs[n] = (C.signs[n] || 0) + 1;
    if (!only || only === 'dec') { const d = s.decade ?? -1; C.dec[d] = (C.dec[d] || 0) + 1; }
    if (!only || only === 'color') C.color[s.bw ? 'bw' : 'col']++;
    if (!only || only === 'hue') { if (s.hue != null) C.hue[Math.floor(s.hue / 10) % 36]++; else if (s.palette) C.grey++; }
    if (!only || only === 'subj') for (const x of s.subjects || []) C.subj[x.label] = (C.subj[x.label] || 0) + 1;
    if (!only || only === 'scale') if (s.scale) C.scale[s.scale] = (C.scale[s.scale] || 0) + 1;
    if (!only || only === 'cut') if (s._cuts.length) C.cut++;
    if (!only || only === 'col') { C.col.both++; for (const c of s._col) if (C.col[c] != null) C.col[c]++; }
    if (!only || only === 'audio') if (s.audio) C.audio[s.audio.kind] = (C.audio[s.audio.kind] || 0) + 1;
    if (!only || only === 'read') if (s._read.length) C.read++;
  }
  COUNTS = C;
  L.subjCounts = C.subj;
  VIEW = sortShots(out);
  GROUPED = null;
  if (GROUP !== 'none' && GROUPS[GROUP]) {
    const gf = GROUPS[GROUP], m = new Map();
    for (const s of VIEW) { const g = gf(s); let G = m.get(g.k); if (!G) { G = { ...g, items: [] }; m.set(g.k, G); } G.items.push(s); }
    GROUPED = [...m.values()].sort((a, b) => a.o - b.o);
    VIEW = GROUPED.flatMap(g => g.items);
  }
  viewSeq++;
}

let refreshQueued = false;
function refresh() {
  if (refreshQueued) return; refreshQueued = true;
  requestAnimationFrame(() => {
    refreshQueued = false;
    compute();
    Facets.update();
    Shell.updateCount();
    Shell.updateLiveBar();
    const m = MODES[Shell.mode]; if (m && m.update) m.update();
  });
}

/* ================================================================ FACETS */
const Facets = {
  root: null,
  build() {
    const R = this.root = $('#facets');
    R.innerHTML = `
      <div class="fx-head"><span>FILTER</span><em>click to narrow the shots</em></div>
      <section class="fx" id="fx-col"><h3>Collection</h3><div class="seg fx-scope" id="fxCol">
        <button data-v="both" title="every shot in the lab">both <i></i></button><button data-v="cineosis" title="the Cineosis 44 corpus: searched for the 45 signs">cineosis <i></i></button><button data-v="wygwyl" title="the WYGWYL Forage Suite: footage foraged for the film's 88 beats">wygwyl <i></i></button></div></section>
      <section class="fx" id="fx-signs">
        <h3>Sign</h3><div class="seg fx-scope" id="fxScope"><button data-v="corpus" title="read shots + everything each sign's searches surfaced">corpus</button><button data-v="read" title="only the shots the editor read">read only</button><button data-v="machine" title="machine-suggested: filter by the machine's top-3 sign affinity">machine top-3</button></div>
        <div class="ptable" id="ptable"></div>
        <div class="fx-note" id="signNote"></div>
      </section>
      <section class="fx"><h3>Decade <em id="decNote"></em></h3><div class="hist" id="dechist"></div><div class="hist-ax" id="decax"></div></section>
      <section class="fx"><h3>Colour <span class="seg" id="fxColor"><button data-v="all">all</button><button data-v="bw">B&amp;W</button><button data-v="col">colour</button></span></h3>
        <div class="huewrap"><canvas id="huecv" height="44"></canvas><div class="fx-note" id="hueNote"></div></div></section>
      <section class="fx"><h3>Subject</h3><div class="taglist" id="fxSubj"></div></section>
      <section class="fx"><h3>Shot scale</h3><div class="taglist" id="fxScale"></div></section>
      <section class="fx"><h3>Cut-outs · audio</h3><div class="taglist" id="fxCut"></div><div class="taglist" id="fxAudio"></div></section>
      <section class="fx fx-legend" id="fxLegend"></section>`;
    // periodic table of chips
    const T = $('#ptable', R);
    for (const s of L.signs) {
      const b = el('button', 'pt'); b.dataset.n = s.n;
      b.style.gridColumn = s.col + 1; b.style.gridRow = s.dom === 'read' ? '1 / span 3' : String(s.row + 1);
      b.style.setProperty('--c', DOMC[s.dom]);
      b.innerHTML = `<span>${esc(s.symbol)}</span><i></i>`;
      T.appendChild(b);
    }
    T.addEventListener('click', e => {
      const b = e.target.closest('.pt'); if (!b) return;
      const n = b.dataset.n;
      if (e.altKey) { Send.sendFamily(n, 'cut'); return; }
      if (e.shiftKey || e.metaKey) { F.signs = new Set(F.signs.size === 1 && F.signs.has(n) ? [] : [n]); }
      else F.signs.has(n) ? F.signs.delete(n) : F.signs.add(n);
      Guide.mark(1);
      refresh();
    });
    T.addEventListener('pointerover', e => { const b = e.target.closest('.pt'); if (b) Tip.sign(b.dataset.n, e); });
    T.addEventListener('pointerout', () => Tip.hide());
    $('#fxCol', R).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; F.col = b.dataset.v; refresh(); });
    $('#fxScope', R).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; F.smode = b.dataset.v; refresh(); });
    $('#fxColor', R).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; F.color = b.dataset.v; refresh(); });
    // decade histogram with click / drag range
    const DH = $('#dechist', R);
    this.decKeys = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, -1];
    DH.innerHTML = this.decKeys.map(d => `<div class="hb" data-d="${d}"><i></i></div>`).join('');
    $('#decax', R).innerHTML = this.decKeys.map(d => `<span>${d < 0 ? '?' : String(d).slice(2)}</span>`).join('');
    let drag = null;
    const decAt = e => { const b = document.elementFromPoint(e.clientX, e.clientY); const h = b && b.closest && b.closest('.hb'); return h ? +h.dataset.d : null; };
    DH.addEventListener('pointerdown', e => {
      const d = decAt(e); if (d == null) return;
      DH.setPointerCapture(e.pointerId);
      drag = { a: d, moved: false, was: new Set(F.dec) };
    });
    DH.addEventListener('pointermove', e => {
      if (!drag) return; const d = decAt(e); if (d == null) return;
      if (d !== drag.a) drag.moved = true;
      if (drag.moved) {
        const ia = this.decKeys.indexOf(drag.a), ib = this.decKeys.indexOf(d);
        F.dec = new Set(this.decKeys.slice(Math.min(ia, ib), Math.max(ia, ib) + 1)); refresh();
      }
    });
    DH.addEventListener('pointerup', () => {
      if (!drag) return;
      if (!drag.moved) { const d = drag.a; F.dec = drag.was.size === 1 && drag.was.has(d) ? new Set() : new Set([d]); refresh(); }
      drag = null;
    });
    DH.addEventListener('pointerover', e => { const h = e.target.closest('.hb'); if (!h) return; const d = +h.dataset.d; Tip.text(`${d < 0 ? 'undated' : d + 's'} · ${fmt(COUNTS.dec[d] || 0)} shots`, e); });
    DH.addEventListener('pointerout', () => Tip.hide());
    // hue strip
    const cv = $('#huecv', R);
    let hdrag = null;
    const hueAt = e => { const r = cv.getBoundingClientRect(); return clamp((e.clientX - r.left) / r.width, 0, 0.9999) * 360; };
    cv.addEventListener('pointerdown', e => { if (!L.has.hue) return; cv.setPointerCapture(e.pointerId); hdrag = { a: hueAt(e), moved: false }; });
    cv.addEventListener('pointermove', e => {
      if (!hdrag) { if (L.has.hue) Tip.text(`hue ${Math.round(hueAt(e))}° · ${HUE_NAMES[hueBand(hueAt(e))]}`, e); return; }
      const h = hueAt(e); if (Math.abs(h - hdrag.a) > 4) hdrag.moved = true;
      if (hdrag.moved) { F.hue = [Math.min(hdrag.a, h), Math.max(hdrag.a, h)]; refresh(); }
    });
    cv.addEventListener('pointerleave', () => Tip.hide());
    cv.addEventListener('pointerup', () => {
      if (!hdrag) return;
      if (!hdrag.moved) {
        const b = hueBand(hdrag.a), band = [((b * 30 - 15) + 360) % 360, (b * 30 + 15) % 360];
        F.hue = F.hue && F.hue[0] === band[0] && F.hue[1] === band[1] ? null : band;
        if (F.hue && F.color === 'bw') F.color = 'all';
        refresh();
      }
      hdrag = null;
    });
    new ResizeObserver(rafThrottle(() => this.drawHue())).observe(cv);
    const tagToggle = (sel, set) => $(sel, R).addEventListener('click', e => {
      const b = e.target.closest('button[data-v]'); if (!b) return; const v = b.dataset.v;
      set.has(v) ? set.delete(v) : set.add(v); refresh();
    });
    tagToggle('#fxSubj', F.subj); tagToggle('#fxScale', F.scale); tagToggle('#fxAudio', F.audio);
    $('#fxCut', R).addEventListener('click', e => { if (e.target.closest('button')) { F.cut = !F.cut; refresh(); } });
    $('#fxLegend', R).innerHTML = Object.entries(DOMN).map(([k, v]) => `<span><i style="background:${DOMC[k]}"></i>${v}</span>`).join('') +
      `<p>click a sign to toggle · shift-click to solo · ⌥/alt-click sends its family to CUT · drag across decades for a range · drag on the hue strip for a band</p>`;
  },
  reset() {
    SORT.key = 'sign'; SORT.dir = 1; GROUP = 'none'; $('#sort').value = 'sign'; $('#sortDir').textContent = '↓'; $('#group').value = 'none';
    F.col = 'both'; F.signs.clear(); F.smode = 'corpus'; F.dec.clear(); F.color = 'all'; F.hue = null; F.subj.clear(); F.scale.clear(); F.cut = false; F.audio.clear();
    $('#q').value = ''; parseQuery(''); refresh();
  },
  update() {
    const R = this.root, C = COUNTS;
    $$('.pt', R).forEach(b => {
      const n = b.dataset.n, c = C.signs[n] || 0;
      b.classList.toggle('on', F.signs.has(n)); b.classList.toggle('zero', !c);
      b.querySelector('i').style.width = Math.min(100, Math.sqrt(c) * 6) + '%';
    });
    $('#ptable', R).classList.toggle('sel', F.signs.size > 0);
    $$('#fxScope button', R).forEach(b => b.classList.toggle('on', b.dataset.v === F.smode));
    $$('#fxCol button', R).forEach(b => { b.classList.toggle('on', b.dataset.v === F.col); b.querySelector('i').textContent = fmt(C.col[b.dataset.v] || 0); });
    $('#signNote', R).innerHTML = F.signs.size
      ? `${[...F.signs].map(n => chip(n)).join('')} <button class="ghost" id="clrSigns">clear</button>`
      : `<span>${{ read: 'only the 253 shots the editor read', machine: 'shots whose machine top-3 affinity includes the sign — a pointer, not a reading', corpus: 'read shots + everything each sign’s searches surfaced' }[F.smode]}</span>`;
    const cs = $('#clrSigns', R); if (cs) cs.onclick = () => { F.signs.clear(); refresh(); };
    // decades
    const mx = Math.max(1, ...this.decKeys.map(d => C.dec[d] || 0));
    $$('.hb', R).forEach(h => {
      const d = +h.dataset.d, c = C.dec[d] || 0;
      h.firstChild.style.height = (c ? 6 + 94 * Math.sqrt(c / mx) : 0) + '%';
      h.classList.toggle('on', F.dec.has(d)); h.classList.toggle('zero', !c);
    });
    $('#dechist', R).classList.toggle('sel', F.dec.size > 0);
    $('#decNote', R).innerHTML = F.dec.size ? `${this.decRangeLabel()} <button class="ghost" id="clrDec">clear</button>` : '';
    const cd = $('#clrDec', R); if (cd) cd.onclick = () => { F.dec.clear(); refresh(); };
    // colour
    $$('#fxColor button', R).forEach(b => b.classList.toggle('on', b.dataset.v === F.color));
    $$('#fxColor button', R).forEach(b => { const v = b.dataset.v; b.title = v === 'all' ? '' : fmt(v === 'bw' ? C.color.bw : C.color.col) + ' shots'; });
    this.drawHue();
    // subjects
    const subj = Object.entries(C.subj).sort((a, b) => b[1] - a[1]).slice(0, 30);
    [...F.subj].forEach(l => { if (!subj.find(x => x[0] === l)) subj.push([l, 0]); });
    $('#fxSubj', R).innerHTML = subj.length ? subj.map(([l, c]) => `<button data-v="${esc(l)}" class="${F.subj.has(l) ? 'on' : ''}">${esc(l)}<i>${c}</i></button>`).join('')
      : `<span class="pending">${L.has.subj ? 'none in this selection' : 'pending · CLIP subjects are being computed'}</span>`;
    $('#fxScale', R).innerHTML = L.has.scale ? SCALES.map(sc => `<button data-v="${sc}" class="${F.scale.has(sc) ? 'on' : ''}" title="${sc}">${SCALE_AB[sc]}<i>${C.scale[sc] || 0}</i></button>`).join('')
      : `<span class="pending">pending · shot scale not analysed yet</span>`;
    $('#fxCut', R).innerHTML = `<button class="${F.cut ? 'on' : ''}" ${L.has.cut ? '' : 'disabled'}>has cut-outs<i>${C.cut}</i></button>` + (L.has.cut ? '' : `<span class="pending">SAM cut-outs being generated</span>`);
    $('#fxAudio', R).innerHTML = L.has.audio ? AUDIO_KINDS.map(k => `<button data-v="${k}" class="${F.audio.has(k) ? 'on' : ''}">${k}<i>${C.audio[k] || 0}</i></button>`).join('')
      : `<span class="pending">pending · audio not analysed yet</span>`;
  },
  decRangeLabel() {
    const ks = this.decKeys.filter(d => F.dec.has(d)); if (!ks.length) return '';
    const lab = d => d < 0 ? 'undated' : d + 's';
    return ks.length === 1 ? lab(ks[0]) : `${lab(ks[0])}–${lab(ks[ks.length - 1])}`;
  },
  drawHue() {
    const cv = $('#huecv', this.root); if (!cv) return;
    const W = cv.clientWidth || 260, H = 44, dpr = devicePixelRatio || 1;
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = H * dpr; }
    const g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    const has = L.has.hue, C = COUNTS;
    for (let x = 0; x < W; x++) { g.fillStyle = `hsl(${x / W * 360},${has ? 62 : 18}%,${has ? 52 : 30}%)`; g.fillRect(x, H - 8, 1, 8); }
    if (has) {
      const mx = Math.max(1, ...C.hue), bw = W / 36;
      for (let i = 0; i < 36; i++) {
        const h = (H - 12) * Math.sqrt(C.hue[i] / mx); g.fillStyle = `hsl(${i * 10 + 5},55%,58%)`;
        g.globalAlpha = F.hue && !inHue(i * 10 + 5, F.hue) ? .25 : .95; g.fillRect(i * bw + .5, H - 10 - h, bw - 1, h);
      }
      g.globalAlpha = 1;
      if (F.hue) {
        const [a, b] = F.hue; g.strokeStyle = '#fff'; g.lineWidth = 1;
        const seg = (x0, x1) => g.strokeRect(x0 + .5, .5, Math.max(2, x1 - x0) - 1, H - 1);
        if (a <= b) seg(a / 360 * W, b / 360 * W); else { seg(a / 360 * W, W); seg(0, b / 360 * W); }
      }
    }
    $('#hueNote', this.root).innerHTML = has
      ? (F.hue ? `${Math.round(F.hue[0])}°–${Math.round(F.hue[1])}° · ${fmt(C.grey)} greyscale excluded <button class="ghost" id="clrHue">clear</button>` : `click a band · drag a range · ${fmt(C.grey)} near-greyscale`)
      : `<span class="pending">pending · hue appears when palettes are analysed</span>`;
    const ch = $('#clrHue', this.root); if (ch) ch.onclick = () => { F.hue = null; refresh(); };
  },
};

/* ================================================================ TIP */
const Tip = {
  node: null,
  show(html, e) {
    const t = this.node || (this.node = $('#tip'));
    t.innerHTML = html; t.hidden = false; this.move(e);
  },
  move(e) {
    const t = this.node; if (!t || t.hidden || !e) return;
    const W = innerWidth, H = innerHeight, r = t.getBoundingClientRect();
    let x = e.clientX + 16, y = e.clientY + 18;
    if (x + r.width > W - 8) x = e.clientX - r.width - 12;
    if (y + r.height > H - 8) y = e.clientY - r.height - 12;
    t.style.transform = `translate(${Math.max(4, x)}px,${Math.max(4, y)}px)`;
  },
  hide() { if (this.node) this.node.hidden = true; },
  text(s, e) { this.show(`<div class="t-l">${esc(s)}</div>`, e); },
  shot(s, e) {
    if (matchMedia('(hover: none)').matches) return;
    const n = signOf(s), en = n && entryOf(s, n);
    const badges = s._read.length ? `<span class="t-f">read as</span> ${s._read.map(x => chip(x)).join('')}` : machineChips(s, 2);
    this.show(`${s._live ? '<span class="livebadge">LIVE</span>' : ''}${colBadge(s)}
      <div class="t-t">${esc(s.title)}</div>
      <div class="t-m">${s.year ?? 'undated'} · ${mmss(s.start || 0)} · ${s._dur.toFixed(1)}s${s.bw ? ' · B&amp;W' : ''}${s.scale ? ' · ' + SCALE_AB[s.scale] : ''}</div>
      <div class="t-b">${badges}</div>
      ${en ? `<div class="t-n">${esc(en.note)}</div>` : ''}`, e);
  },
  sign(n, e) {
    const s = L.S[n]; if (!s) return;
    this.show(`<div class="t-s"><span class="chip big" style="--c:${DOMC[s.dom]}">${esc(s.symbol)}</span><div><div class="t-t">${esc(s.name)}</div><div class="t-m">${esc(s.image)} · ${esc(s.n)} · ${fmt(COUNTS.signs[n] || 0)} shots</div></div></div>
      <div class="t-n">${esc(s.difference || s.gloss || '')}</div>`, e);
  },
};

/** which collection(s) a shot belongs to */
function colBadge(s) {
  const c = s._col || ['cineosis'];
  return c.includes('wygwyl') ? `<span class="colbadge${c.includes('cineosis') ? ' both' : ''}" title="${c.join(' + ')}">${c.includes('cineosis') ? 'CINEOSIS + WYGWYL' : 'WYGWYL'}</span>` : '';
}
/** the machine's top sign(s) for an unread shot, labelled as such */
function machineChips(s, k) {
  const top = (s.aff_top || []).slice(0, k);
  if (!top.length) return s._found.length ? `<span class="t-f">found by</span> ${s._found.slice(0, 4).map(x => chip(x, 'ghostchip')).join('')}` : '';
  return `<span class="t-f">machine</span> ${top.map(([n, v]) => `${chip(String(n), 'ghostchip')}<span class="t-p">${Math.round(v)}%</span>`).join(' ')}`;
}

/* ================================================================ VGRID  (virtualised absolute grid with FLIP re-layout) */
class VGrid {
  constructor(host, opt) {
    this.host = host; this.opt = opt;
    this.sc = el('div', 'vg-scroll'); this.cv = el('div', 'vg-canvas'); this.sc.appendChild(this.cv); host.appendChild(this.sc);
    this.els = new Map(); this.heads = []; this.entries = []; this.X = []; this.Y = []; this.tw = 100; this.th = 75;
    this.dying = new Set();
    this.sc.addEventListener('scroll', rafThrottle(() => this.render(false)), { passive: true });
    this.ro = new ResizeObserver(rafThrottle(() => { if (!this.sc.clientWidth) return; this.layout(); this.render(false); }));
    this.ro.observe(this.sc);
    this.cv.addEventListener('pointerover', e => { const t = e.target.closest('[data-k]'); if (t) Tip.shot(t._shot, e); });
    this.cv.addEventListener('pointermove', e => Tip.move(e));
    this.cv.addEventListener('pointerout', e => { if (!e.relatedTarget || !e.relatedTarget.closest || !e.relatedTarget.closest('[data-k]')) Tip.hide(); });
    this.cv.addEventListener('click', e => {
      const t = e.target.closest('[data-k]'); if (!t) return;
      Tip.hide(); Inspector.open(t._shot, this.entries.map(x => x.s));
    });
  }
  /** entries: [{s,k}], groups: [{label, count, start, n}] | null */
  set(entries, groups, animate) {
    const old = new Map(); if (animate) for (const [k, e] of this.els) old.set(k, e);
    this.entries = entries; this.groups = groups;
    this.layout();
    const big = entries.length > 700 && this.lastN > 700;
    this.lastN = entries.length;
    this.render(animate && !big && !REDUCED);
  }
  layout() {
    const W = this.sc.clientWidth || innerWidth, o = this.opt;
    const pad = W < 640 ? 8 : 20, gap = o.gap, HEAD = 40;
    let tw = o.tileW(); if (W < 640) tw = Math.min(tw, (W - 2 * pad - 2 * gap) / 3);
    const cols = Math.max(1, Math.floor((W - 2 * pad + gap) / (tw + gap)));
    tw = (W - 2 * pad - (cols - 1) * gap) / cols;
    const th = tw * o.aspect + (o.caption || 0);
    this.tw = tw; this.th = th; this.cols = cols;
    const n = this.entries.length; this.X = new Float32Array(n); this.Y = new Float32Array(n);
    this.headPos = [];
    let y = pad + (o.top || 0);
    const place = (from, to) => {
      for (let i = from; i < to; i++) { const j = i - from; this.X[i] = pad + (j % cols) * (tw + gap); this.Y[i] = y + Math.floor(j / cols) * (th + gap); }
      y += Math.ceil((to - from) / cols) * (th + gap);
    };
    if (this.groups && this.groups.length) {
      for (const g of this.groups) { this.headPos.push({ g, y }); y += HEAD; place(g.start, g.start + g.n); y += 14; }
    } else place(0, n);
    this.H = y + pad;
    this.cv.style.height = this.H + 'px';
  }
  render(animate) {
    const st = this.sc.scrollTop, vh = this.sc.clientHeight || innerHeight, buf = this.th * 2;
    const y0 = st - buf, y1 = st + vh + buf, Y = this.Y, n = this.entries.length;
    let lo = 0, hi = n; while (lo < hi) { const m = (lo + hi) >> 1; if (Y[m] + this.th < y0) lo = m + 1; else hi = m; }
    const need = new Set();
    this.cv.classList.toggle('anim', !!animate);
    const tw = Math.round(this.tw * 10) / 10, ih = Math.round(this.tw * this.opt.aspect * 10) / 10;
    const fresh = [];
    for (let i = lo; i < n && Y[i] <= y1; i++) {
      const { s, k } = this.entries[i]; need.add(k);
      let e = this.els.get(k);
      if (!e) {
        e = this.opt.make(s, k); e.dataset.k = k; e._shot = s;
        this.els.set(k, e); this.cv.appendChild(e);
        if (animate) { e.classList.add('enter'); fresh.push(e); }
      } else if (this.dying.has(k)) { this.dying.delete(k); e.classList.remove('exit'); }
      e._shot = s;
      if (e._w !== tw) { e.style.width = tw + 'px'; e.style.setProperty('--ih', ih + 'px'); e._w = tw; }
      const tr = `translate3d(${Math.round(this.X[i])}px,${Math.round(Y[i])}px,0)`;
      if (e._tr !== tr) { e.style.transform = tr; e._tr = tr; }
    }
    // entries that still exist but are now off-window: during animation let them fly to their new place, then drop
    const idx = animate ? new Map(this.entries.map((x, i) => [x.k, i])) : null;
    for (const [k, e] of this.els) {
      if (need.has(k)) continue;
      if (animate && idx.has(k)) {
        const i = idx.get(k); const tr = `translate3d(${Math.round(this.X[i])}px,${Math.round(Y[i])}px,0)`;
        e.style.transform = tr; e._tr = tr; this.dying.add(k);
      } else if (animate && !e.classList.contains('exit')) { e.classList.add('exit'); this.dying.add(k); }
      else if (!animate) { e.remove(); this.els.delete(k); this.dying.delete(k); }
    }
    if (fresh.length) requestAnimationFrame(() => requestAnimationFrame(() => fresh.forEach(e => e.classList.remove('enter'))));
    if (animate) { clearTimeout(this.cleanT); this.cleanT = setTimeout(() => { this.cv.classList.remove('anim'); this.dying.forEach(k => { const e = this.els.get(k); if (e) e.remove(); this.els.delete(k); }); this.dying.clear(); this.render(false); }, 560); }
    // group headers
    if (this.headPos.length || this.heads.length) {
      this.heads.forEach(h => h.remove()); this.heads = [];
      for (const { g, y } of this.headPos) {
        if (y > y1 + 400 || y < y0 - 2000) continue;
        const h = el('div', 'ghead', `${g.label}<span class="gc">${fmt(g.n)}</span>`);
        h.style.transform = `translate3d(0,${y}px,0)`; this.cv.appendChild(h); this.heads.push(h);
      }
    }
  }
  scrollTop() { this.sc.scrollTop = 0; }
  destroy() { this.ro.disconnect(); this.host.innerHTML = ''; }
}

function entriesAndGroups() {
  const entries = [], groups = [];
  const lv = liveView();
  if (lv.length) { groups.push({ label: `<span class="livebadge">LIVE</span> <b>“${esc(L.liveQ)}”</b> <em>archive search</em>`, start: 0, n: lv.length }); lv.forEach(s => entries.push({ s, k: 'L' + s.id })); }
  const hideHits = L.showLive;
  if (GROUPED) {
    for (const g of GROUPED) {
      const start = entries.length;
      for (const s of g.items) if (!(hideHits && s._liveHit)) entries.push({ s, k: s.id });
      if (entries.length > start) groups.push({ label: g.label, start, n: entries.length - start });
    }
  } else {
    const start = entries.length;
    for (const s of VIEW) if (!(hideHits && s._liveHit)) entries.push({ s, k: s.id });
    if (lv.length) groups.push({ label: '<b>corpus</b>', start, n: entries.length - start });
  }
  return { entries, groups: groups.length ? groups : null };
}

/* ================================================================ WALL */
const Wall = {
  host: null, grid: null,
  mount(host) {
    if (this.grid) return;
    this.host = host;
    this.grid = new VGrid(host, {
      gap: 4, aspect: 0.75, tileW: () => Shell.size,
      make: (s) => {
        const d = el('div', 'tile' + (s._live ? ' live' : '') + (s._read.length ? ' read' : ''));
        d.appendChild(el('span', 'tcap', `<b>${esc(s.title || 'untitled')}</b><em>${s.year ?? 'undated'}</em>`));
        const img = new Image(); img.decoding = 'async'; img.loading = 'lazy'; img.alt = ''; img.draggable = false;
        img.onerror = () => d.classList.add('broken'); img.onload = () => d.classList.add('loaded');
        if (s.thumb) img.src = s.thumb; else d.classList.add('broken');
        d.appendChild(img);
        const b = el('div', 'badges');
        b.innerHTML = (s._live ? '<span class="livebadge">LIVE</span>' : '') + s._read.map(n => chip(n, 'sm')).join('') + (s._cuts.length ? '<span class="mk" title="has cut-outs">✂</span>' : '');
        d.appendChild(b);
        return d;
      },
    });
    this.seq = -1;
  },
  update() {
    const { entries, groups } = entriesAndGroups();
    const animate = this.seq >= 0;
    this.seq = viewSeq;
    this.grid.set(entries, groups, animate);
  },
  show() { this.update(); },
  resize() { if (this.grid) { this.grid.layout(); this.grid.render(false); } },
};

/* ================================================================ IMG cache (map/ring) */
const IMG = {
  cache: new Map(), queue: [], active: 0, max: 24, onload: null,
  get(url) {
    let r = this.cache.get(url);
    if (!r) { r = { img: null, ok: false, bad: false, queued: false }; this.cache.set(url, r); }
    return r;
  },
  want(url) {
    const r = this.get(url); if (r.ok || r.bad || r.queued) return r;
    r.queued = true; this.queue.push(url); this.pump(); return r;
  },
  pump() {
    while (this.active < this.max && this.queue.length) {
      const url = this.queue.pop(); const r = this.cache.get(url); this.active++;
      const im = new Image(); im.decoding = 'async';
      im.onload = () => { r.img = im; r.ok = true; this.active--; this.pump(); if (this.onload) this.onload(); };
      im.onerror = () => { r.bad = true; this.active--; this.pump(); };
      im.src = url;
    }
  },
  flush() { this.queue.forEach(u => { const r = this.cache.get(u); if (r) r.queued = false; }); this.queue = []; },
};

/* ================================================================ MAP */
const MapMode = {
  host: null, cv: null, g: null, P: [], cam: { x: .5, y: .5, z: 600 }, kind: null, hover: null, dirty: true,
  mount(host) {
    if (this.cv) return;
    this.host = host;
    host.innerHTML = `<canvas class="mapcv"></canvas>
      <div class="hud hud-tl"><div class="hud-title" id="mapTitle"></div><div class="seg" id="mapKind">
        <button data-v="xy">similarity</button><button data-v="hue">hue × decade</button><button data-v="sign">sign × decade</button></div>
        <div class="hud-note" id="mapNote"></div></div>
      <div class="hud hud-br"><button class="ghost" data-z="in">+</button><button class="ghost" data-z="out">−</button><button class="ghost" data-z="fit">fit</button></div>`;
    this.cv = $('canvas', host); this.g = this.cv.getContext('2d');
    IMG.onload = rafThrottle(() => { if (Shell.mode === 'map') this.draw(); });
    $('#mapKind', host).addEventListener('click', e => { const b = e.target.closest('button'); if (!b || b.disabled) return; this.kind = b.dataset.v; this.build(); this.fit(); });
    $('.hud-br', host).addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return; const z = b.dataset.z;
      if (z === 'fit') this.fit(); else this.zoomAt(this.W / 2, this.H / 2, z === 'in' ? 1.6 : 1 / 1.6);
    });
    const ptrs = new Map(); let drag = null, pinch = null;
    const cv = this.cv;
    cv.addEventListener('pointerdown', e => {
      cv.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, { x: e.offsetX, y: e.offsetY });
      if (ptrs.size === 1) drag = { x: e.offsetX, y: e.offsetY, cx: this.cam.x, cy: this.cam.y, moved: false };
      if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), z: this.cam.z }; drag = null; }
    });
    cv.addEventListener('pointermove', e => {
      if (ptrs.has(e.pointerId)) ptrs.set(e.pointerId, { x: e.offsetX, y: e.offsetY });
      if (pinch && ptrs.size === 2) {
        const [a, b] = [...ptrs.values()]; const d = Math.hypot(a.x - b.x, a.y - b.y);
        const f = (pinch.z * d / pinch.d) / this.cam.z; this.zoomAt((a.x + b.x) / 2, (a.y + b.y) / 2, f); return;
      }
      if (drag) {
        const dx = e.offsetX - drag.x, dy = e.offsetY - drag.y;
        if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
        if (drag.moved) { this.cam.x = drag.cx - dx / this.cam.z; this.cam.y = drag.cy - dy / this.cam.z; this.req(); Tip.hide(); return; }
      }
      const h = this.hit(e.offsetX, e.offsetY);
      if (h !== this.hover) { this.hover = h; this.req(); }
      if (h) Tip.shot(h.s, e); else Tip.hide();
      cv.style.cursor = h ? 'pointer' : 'grab';
    });
    const up = e => {
      ptrs.delete(e.pointerId);
      if (ptrs.size < 2) pinch = null;
      if (drag && !drag.moved && e.type === 'pointerup') { const h = this.hit(e.offsetX, e.offsetY); if (h) { Tip.hide(); Inspector.open(h.s, this.P.filter(p => p.s._in || p.s._live).map(p => p.s)); } }
      drag = null;
    };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
    cv.addEventListener('pointerleave', () => { Tip.hide(); if (this.hover) { this.hover = null; this.req(); } });
    cv.addEventListener('wheel', e => {
      e.preventDefault();
      const f = Math.exp(-(e.deltaMode ? e.deltaY * 16 : e.deltaY) * (e.ctrlKey ? 0.01 : 0.0022));
      this.zoomAt(e.offsetX, e.offsetY, f);
    }, { passive: false });
    cv.addEventListener('dblclick', e => this.zoomAt(e.offsetX, e.offsetY, 2.2));
    new ResizeObserver(() => { this.size(); this.draw(); }).observe(host);
  },
  size() {
    const r = this.host.getBoundingClientRect(), dpr = devicePixelRatio || 1;
    this.W = r.width; this.H = r.height; this.dpr = dpr;
    this.cv.width = Math.max(1, Math.round(r.width * dpr)); this.cv.height = Math.max(1, Math.round(r.height * dpr));
  },
  show() { this.size(); if (!this.kind || (this.kind === 'xy' && !L.has.xy) || (this.kind === 'hue' && !L.has.hue)) this.kind = L.has.xy ? 'xy' : L.has.hue ? 'hue' : 'sign'; this.build(); this.fit(); },
  update() { this.buildLive(); this.req(); this.hud(); },
  hud() {
    const H = this.host;
    $$('#mapKind button', H).forEach(b => { const v = b.dataset.v; b.disabled = (v === 'xy' && !L.has.xy) || (v === 'hue' && !L.has.hue); b.classList.toggle('on', v === this.kind); });
    const t = { xy: 'SIMILARITY MAP · CLIP embedding, t-SNE', hue: 'FALLBACK · hue band × decade', sign: 'FALLBACK · sign × decade' }[this.kind];
    $('#mapTitle', H).textContent = t;
    const shown = this.P.filter(p => p.s._in).length;
    $('#mapNote', H).innerHTML = `${fmt(shown)} lit · ${fmt(this.P.length - shown)} dimmed` +
      (this.kind !== 'xy' && !L.has.xy ? ' · similarity map appears when xy is computed' : '') + ' · wheel/pinch to zoom · drag to pan';
  },
  build() {
    const P = [], shots = L.shots;
    this.axes = null;
    const decs = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, -1];
    if (this.kind === 'xy') {
      const withXY = shots.filter(s => s.xy), without = shots.filter(s => !s.xy);
      const w = 1.05 / Math.sqrt(Math.max(1, withXY.length));
      for (const s of withXY) P.push({ s, x: s.xy[0], y: s.xy[1], w });
      if (without.length) { const band = []; packCell(without, 0, 1.06, 1, 0.12, band); P.push(...band); this.axes = { strip: { y: 1.05, label: `${without.length} not yet embedded` } }; }
      this.bounds = [0, 0, 1, without.length ? 1.2 : 1];
    } else {
      const rows = this.kind === 'hue' ? [...Array(14).keys()] : L.signs.map(s => s.n).concat(['-']);
      const rowOf = this.kind === 'hue' ? (s => s._hb) : (s => s._read[0] || s._found[0] || '-');
      const WW = 1.6, HH = 1, cw = WW / decs.length, ch = HH / rows.length;
      const cells = new Map();
      for (const s of shots) { const key = decs.indexOf(s.decade ?? -1) + '|' + rows.indexOf(rowOf(s)); let c = cells.get(key); if (!c) cells.set(key, c = []); c.push(s); }
      for (const [key, arr] of cells) {
        const [ci, ri] = key.split('|').map(Number); if (ri < 0) continue;
        arr.sort((a, b) => (a._read.length ? 0 : 1) - (b._read.length ? 0 : 1) || (a.hue ?? 999) - (b.hue ?? 999) || a._i - b._i);
        packCell(arr, ci * cw + cw * .04, ri * ch + ch * .06, cw * .92, ch * .88, P);
      }
      this.axes = { cols: decs.map((d, i) => ({ x: (i + .5) * cw, label: d < 0 ? 'undated' : d + 's' })), rows: rows.map((r, i) => ({ y: (i + .5) * ch, r })), cw, ch, WW, HH };
      this.bounds = [0, 0, WW, HH];
    }
    this.base = P; this.buildLive(); this.hud();
  },
  buildLive() {
    const lv = liveView().filter(s => !s._liveHit || !this.base.find(p => p.s === s));
    this.P = this.base.slice();
    if (lv.length) { const band = []; packCell(lv, this.bounds[0], this.bounds[1] - 0.14, this.bounds[2] - this.bounds[0], 0.11, band); this.P.push(...band); }
    this.liveRow = lv.length ? this.bounds[1] - 0.15 : null;
  },
  fit() {
    const [x0, y0, x1, y1] = this.bounds, top = this.liveRow != null ? this.liveRow : y0;
    const cells = this.axes && this.axes.cols, small = this.W < 640;
    const pad = { l: cells ? (small ? 44 : 120) : 24, r: 24, t: small ? 96 : cells ? 150 : 120, b: 24 };
    const z = this.cam.z = Math.max(20, Math.min((this.W - pad.l - pad.r) / (x1 - x0), (this.H - pad.t - pad.b) / (y1 - top)));
    const sx = (pad.l + this.W - pad.r) / 2, sy = (pad.t + this.H - pad.b) / 2;
    this.cam.x = (x0 + x1) / 2 - (sx - this.W / 2) / z; this.cam.y = (top + y1) / 2 - (sy - this.H / 2) / z; this.req();
  },
  zoomAt(sx, sy, f) {
    const c = this.cam, z2 = clamp(c.z * f, 40, 60000);
    const wx = (sx - this.W / 2) / c.z + c.x, wy = (sy - this.H / 2) / c.z + c.y;
    c.z = z2; c.x = wx - (sx - this.W / 2) / z2; c.y = wy - (sy - this.H / 2) / z2; this.req();
  },
  req() { if (this.rq) return; this.rq = true; requestAnimationFrame(() => { this.rq = false; this.draw(); }); },
  hit(mx, my) {
    const c = this.cam, W2 = this.W / 2, H2 = this.H / 2;
    for (let i = this.P.length - 1; i >= 0; i--) {
      const p = this.P[i], w = Math.max(5, p.w * c.z), h = w * .75;
      const sx = (p.x - c.x) * c.z + W2, sy = (p.y - c.y) * c.z + H2;
      if (Math.abs(mx - sx) <= w / 2 && Math.abs(my - sy) <= h / 2) return p;
    }
    return null;
  },
  draw() {
    if (!this.g || Shell.mode !== 'map') return;
    const g = this.g, c = this.cam, W = this.W, H = this.H, W2 = W / 2, H2 = H / 2;
    g.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    IMG.flush();
    const anyIn = F.signs.size || F.dec.size || F.color !== 'all' || F.hue || F.subj.size || F.scale.size || F.cut || F.audio.size || F.q || F.smode === 'read' || F.col !== 'both';
    // axes
    if (this.axes && this.axes.cols) {
      const A = this.axes;
      g.font = '11px "IBM Plex Mono", monospace'; g.textBaseline = 'middle';
      g.strokeStyle = '#161615'; g.lineWidth = 1;
      for (let i = 0; i <= A.cols.length; i++) { const x = Math.round((i * A.cw - c.x) * c.z + W2) + .5; g.beginPath(); g.moveTo(x, (0 - c.y) * c.z + H2); g.lineTo(x, (A.HH - c.y) * c.z + H2); g.stroke(); }
      const rowH = A.ch * c.z;
      for (let i = 0; i <= A.rows.length; i++) { if (rowH < 5 && i % 4) continue; const y = Math.round((i * A.ch - c.y) * c.z + H2) + .5; g.beginPath(); g.moveTo((0 - c.x) * c.z + W2, y); g.lineTo((A.WW - c.x) * c.z + W2, y); g.stroke(); }
      g.fillStyle = '#a8a196'; g.textAlign = 'center';
      const ty = Math.max(14, (0 - c.y) * c.z + H2 - 12);
      for (const col of A.cols) g.fillText(col.label, (col.x - c.x) * c.z + W2, ty);
      g.textAlign = 'right';
      const lx = Math.max(40, (0 - c.x) * c.z + W2 - 8);
      if (rowH >= 7) for (const r of A.rows) {
        const y = (r.y - c.y) * c.z + H2; if (y < -10 || y > H + 10) continue;
        if (this.kind === 'hue') { g.fillStyle = r.r < 12 ? `hsl(${r.r * 30},60%,60%)` : '#a8a196'; g.fillText(hbLabel(r.r), lx, y); }
        else { const s = L.S[r.r]; g.fillStyle = s ? DOMC[s.dom] : '#a8a196'; g.fillText(s ? s.symbol + (rowH > 16 ? ' ' + s.name : '') : 'no sign', lx, y); }
      }
    }
    if (this.axes && this.axes.strip) { g.fillStyle = '#a8a196'; g.font = '11px "IBM Plex Mono", monospace'; g.textAlign = 'left'; g.fillText(this.axes.strip.label, (0 - c.x) * c.z + W2, (this.axes.strip.y - c.y) * c.z + H2); }
    if (this.liveRow != null) { g.fillStyle = '#e8e4da'; g.font = '11px "IBM Plex Mono", monospace'; g.textAlign = 'left'; g.fillText('LIVE · “' + L.liveQ + '”', (this.bounds[0] - c.x) * c.z + W2, (this.liveRow - c.y) * c.z + H2); }
    let loads = 0;
    for (let pass = 0; pass < 2; pass++) {
      for (const p of this.P) {
        const lit = p.s._in || p.s._live;
        if (anyIn) { if (pass === 0 && lit) continue; if (pass === 1 && !lit) continue; } // dim first, lit on top
        else if (pass === 1) continue;
        const w = p.w * c.z, h = w * .75, sx = (p.x - c.x) * c.z + W2, sy = (p.y - c.y) * c.z + H2;
        if (sx + w < 0 || sx - w > W || sy + h < 0 || sy - h > H) continue;
        g.globalAlpha = lit || !anyIn ? 1 : .13;
        if (w < 18) {
          g.fillStyle = p.s._dot; g.fillRect(sx - w / 2, sy - h / 2, Math.max(1.2, w * .9), Math.max(1, h * .9));
        } else {
          const r = (lit || !anyIn || w > 60) ? (loads++ < 400 ? IMG.want(p.s.thumb) : IMG.get(p.s.thumb)) : IMG.get(p.s.thumb);
          if (r.ok) drawCover(g, r.img, sx - w / 2, sy - h / 2, w * .96, h * .96);
          else { g.fillStyle = p.s._dot; g.fillRect(sx - w / 2, sy - h / 2, w * .96, h * .96); }
          if (w > 60 && p.s._read.length && (lit || !anyIn)) {
            let bx = sx - w / 2 + 3;
            for (const n of p.s._read) { const S = L.S[n]; g.fillStyle = DOMC[S.dom]; g.fillRect(bx, sy + h / 2 - 16, 22, 12); g.fillStyle = '#1a1712'; g.font = '700 9px Fraunces, serif'; g.textAlign = 'center'; g.fillText(S.symbol, bx + 11, sy + h / 2 - 9.5); bx += 25; }
          }
        }
        if (p.s._live) { g.strokeStyle = '#e8e4da'; g.lineWidth = 1; g.strokeRect(sx - w / 2 - 1.5, sy - h / 2 - 1.5, w * .96 + 3, h * .96 + 3); }
      }
    }
    g.globalAlpha = 1;
    if (this.hover) {
      const p = this.hover, w = Math.max(5, p.w * c.z), h = w * .75, sx = (p.x - c.x) * c.z + W2, sy = (p.y - c.y) * c.z + H2;
      if (w < 70) {
        const bw = 150, bh = 112; const r = IMG.want(p.s.thumb);
        const bx = clamp(sx - bw / 2, 4, W - bw - 4), by = clamp(sy - bh - 14, 4, H - bh - 4);
        g.fillStyle = '#000'; g.fillRect(bx - 2, by - 2, bw + 4, bh + 4);
        if (r.ok) drawCover(g, r.img, bx, by, bw, bh); else { g.fillStyle = p.s._dot; g.fillRect(bx, by, bw, bh); }
        g.strokeStyle = '#e8e4da'; g.lineWidth = 1; g.strokeRect(bx - .5, by - .5, bw + 1, bh + 1);
      }
      g.strokeStyle = '#fff'; g.lineWidth = 1.5; g.strokeRect(sx - w / 2 - 1, sy - h / 2 - 1, w + 2, h + 2);
    }
  },
};
function packCell(items, x0, y0, cw, ch, out) {
  const k = items.length; if (!k) return;
  let best = 0, bc = 1;
  for (let nc = 1; nc <= k; nc++) { const nr = Math.ceil(k / nc); const s = Math.min(cw / nc, ch / (nr * .75)); if (s > best) { best = s; bc = nc; } if (cw / nc < best) break; }
  const w = best;
  items.forEach((s, i) => out.push({ s, x: x0 + (i % bc + .5) * w, y: y0 + (Math.floor(i / bc) + .5) * w * .75, w }));
}
function drawCover(g, img, x, y, w, h) {
  const ir = img.naturalWidth / img.naturalHeight, r = w / h;
  let sw = img.naturalWidth, sh = img.naturalHeight, sx = 0, sy = 0;
  if (ir > r) { sw = sh * r; sx = (img.naturalWidth - sw) / 2; } else { sh = sw / r; sy = (img.naturalHeight - sh) / 2; }
  g.drawImage(img, sx, sy, sw, sh, x, y, w, h);
}

/* ================================================================ RING */
const Ring = {
  host: null, rot: null, spin: 0, vel: 0, tilt: -6, items: [], auto: true, raf: 0,
  mount(host) {
    if (this.rot) return;
    this.host = host;
    host.innerHTML = `<div class="ring-stage"><div class="ring-rot"></div></div>
      <div class="hud hud-tl"><div class="hud-title" id="ringTitle"></div><div class="hud-note">drag or wheel to spin · click to inspect · first 240 of the current selection</div></div>
      <div class="hud hud-br"><button class="ghost" id="ringAuto">auto-spin</button></div>`;
    this.stage = $('.ring-stage', host); this.rot = $('.ring-rot', host);
    $('#ringAuto', host).addEventListener('click', () => { this.auto = !this.auto; $('#ringAuto', host).classList.toggle('on', this.auto); });
    $('#ringAuto', host).classList.add('on');
    let drag = null;
    this.stage.addEventListener('pointerdown', e => { this.stage.setPointerCapture(e.pointerId); drag = { x: e.clientX, y: e.clientY, s: this.spin, t: this.tilt, moved: false, lt: performance.now(), lx: e.clientX }; this.vel = 0; });
    this.stage.addEventListener('pointermove', e => {
      if (!drag) { const t = document.elementFromPoint(e.clientX, e.clientY); const c = t && t.closest && t.closest('.rc'); if (c) Tip.shot(c._shot, e); else Tip.hide(); return; }
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 5) drag.moved = true;
      this.spin = drag.s + dx * this.degPerPx; this.tilt = clamp(drag.t - dy * 0.08, -30, 24);
      const now = performance.now(); this.vel = (e.clientX - drag.lx) * this.degPerPx / Math.max(8, now - drag.lt) * 16; drag.lx = e.clientX; drag.lt = now;
      this.apply(); Tip.hide();
    });
    const up = e => {
      if (drag && !drag.moved) {
        this.stage.releasePointerCapture(e.pointerId);
        const t = document.elementFromPoint(e.clientX, e.clientY); const c = t && t.closest && t.closest('.rc');
        if (c) { Tip.hide(); Inspector.open(c._shot, this.items); }
      }
      drag = null;
    };
    this.stage.addEventListener('pointerup', up); this.stage.addEventListener('pointercancel', () => { drag = null; });
    this.stage.addEventListener('pointerleave', () => Tip.hide());
    this.stage.addEventListener('wheel', e => { e.preventDefault(); this.vel += (e.deltaX || e.deltaY) * 0.02; }, { passive: false });
  },
  show() { this.update(); this.loop(); },
  hide() { cancelAnimationFrame(this.raf); this.raf = 0; },
  update() {
    const list = viewList().slice(0, 240);
    const key = list.map(s => s.id).join(',');
    $('#ringTitle', this.host).textContent = `RING · ${list.length} of ${fmt(viewList().length)}`;
    if (key === this.key && this.lastW === this.host.clientWidth) return;
    this.key = key; this.lastW = this.host.clientWidth; this.items = list;
    const n = list.length, W = this.host.clientWidth || innerWidth, Hh = this.host.clientHeight || innerHeight;
    const rows = n > 180 ? 4 : n > 90 ? 3 : n > 40 ? 2 : 1, per = Math.max(1, Math.ceil(n / rows));
    const small = W < 700;
    const tw = small ? 96 : clamp(W / 11, 110, 190), th = tw * .75, gap = tw * .06;
    const R = Math.max(W * .32, per * (tw + gap) / (2 * Math.PI));
    this.R = R; this.degPerPx = 360 / (2 * Math.PI * R) * 1.1; this.per = per;
    this.rot.innerHTML = '';
    const frag = document.createDocumentFragment();
    this.cards = list.map((s, i) => {
      const row = Math.floor(i / per), j = i % per;
      const a = (j / per) * 360 + (row % 2 ? 180 / per : 0);
      const y = (row - (rows - 1) / 2) * (th + gap * 2);
      const c = el('div', 'rc' + (s._live ? ' live' : ''));
      c.style.width = tw + 'px'; c.style.height = th + 'px';
      c.style.transform = `translate(-50%,-50%) translateY(${y}px) rotateY(${a}deg) translateZ(${R}px)`;
      const img = new Image(); img.decoding = 'async'; img.alt = ''; img.draggable = false; img.src = s.thumb; img.onerror = () => c.classList.add('broken');
      c.appendChild(img); c._shot = s; c._a = a;
      if (s._read.length) c.insertAdjacentHTML('beforeend', `<div class="badges">${s._read.map(n => chip(n, 'sm')).join('')}</div>`);
      frag.appendChild(c); return c;
    });
    this.rot.appendChild(frag);
    this.stage.style.perspective = Math.max(900, R * 1.25) + 'px';
    this.zoff = -R - Math.min(Hh, W) * .15;
    this.apply(true);
  },
  apply(force) {
    this.rot.style.transform = `translateZ(${this.zoff}px) rotateX(${this.tilt}deg) rotateY(${this.spin}deg)`;
    const q = Math.round(this.spin * 2);
    if (!force && q === this._q) return; this._q = q;
    for (const c of this.cards || []) {
      const a = ((c._a + this.spin) % 360 + 360) % 360, cs = Math.cos(a * Math.PI / 180);
      c.style.opacity = (0.16 + 0.84 * Math.max(0, cs) ** 1.2).toFixed(2);
      c.style.zIndex = Math.round(cs * 100) + 100;
    }
  },
  loop() {
    cancelAnimationFrame(this.raf);
    const step = () => {
      if (Shell.mode !== 'ring') return;
      if (Math.abs(this.vel) > 0.01) { this.spin += this.vel; this.vel *= 0.94; this.apply(); }
      else if (this.auto && !REDUCED) { this.spin += 0.05; this.apply(); }
      this.raf = requestAnimationFrame(step);
    };
    this.raf = requestAnimationFrame(step);
  },
  resize() { this.key = null; if (Shell.mode === 'ring') this.update(); },
};

/* ================================================================ STRATA */
const Strata = {
  host: null, grid: null, timer: 0, hot: null,
  mount(host) {
    if (this.grid) return;
    this.host = host;
    this.grid = new VGrid(host, {
      gap: 10, aspect: 0.86, caption: 18, top: 34, tileW: () => Math.max(120, Shell.size * 1.3),
      make: s => this.cell(s),
    });
    host.insertAdjacentHTML('afterbegin', `<div class="hud hud-tl strata-hud"><div class="hud-title" id="strataTitle"></div><div class="hud-note" id="strataNote"></div></div>`);
    this.grid.cv.addEventListener('pointerover', e => this.heat(e.target.closest('.stc')));
    this.grid.cv.addEventListener('pointerleave', () => this.heat(null));
  },
  cell(s) {
    const d = el('div', 'stc' + (s._live ? ' live' : ''));
    const N = s.strip ? clamp(s.frames || 8, 2, 12) : 6;
    const tun = el('div', 'tun' + (s.strip ? ' strip' : ''));
    d._N = N; d._layers = [];
    for (let k = N - 1; k >= 0; k--) {
      const lay = el('div', 'lay');
      lay.style.setProperty('--k', k); lay.style.zIndex = N - k;
      if (s.strip) { lay.style.backgroundImage = `url("${s.strip}")`; lay.style.backgroundSize = `${N * 100}% 100%`; }
      else lay.style.backgroundImage = `url("${s.thumb}")`;
      d._layers[k] = lay; tun.appendChild(lay);
    }
    d.appendChild(tun);
    d.insertAdjacentHTML('beforeend', `<div class="cap">${s._live ? '<span class="livebadge">LIVE</span>' : ''}${s._read.map(n => chip(n, 'sm')).join('')}<span>${s.year ?? '—'} · ${esc(s.title)}</span></div>`);
    this.frame(d, s, 0);
    return d;
  },
  frame(d, s, phase) {
    const N = d._N;
    for (let k = 0; k < N; k++) {
      const lay = d._layers[k];
      if (s.strip) { const f = (k + phase) % N; lay.style.backgroundPosition = `${N > 1 ? f / (N - 1) * 100 : 0}% 0`; }
    }
  },
  heat(c) {
    if (this.hot === c) return;
    if (this.hot) { this.hot.classList.remove('hot'); this.frame(this.hot, this.hot._shot, 0); }
    clearInterval(this.timer); this.hot = c;
    if (!c) return;
    c.classList.add('hot');
    let ph = 0; const s = c._shot;
    if (s.strip) this.timer = setInterval(() => { ph = (ph + 1) % c._N; this.frame(c, s, ph); }, 150);
  },
  update() {
    const { entries, groups } = entriesAndGroups();
    const withStrip = entries.filter(e => e.s.strip).length;
    $('#strataTitle', this.host).textContent = `STRATA · ${fmt(entries.length)} shots · ${fmt(withStrip)} with frame strips`;
    $('#strataNote', this.host).textContent = withStrip ? 'each shot as a stack of its frames in time — front is the first frame; hover to run the stack'
      : 'frame strips are still being extracted — stacks show the thumbnail for now; hover to spread';
    const animate = this.seq >= 0; this.seq = viewSeq;
    this.grid.set(entries, groups, animate);
  },
  show() { this.update(); },
  hide() { this.heat(null); },
  resize() { if (this.grid) { this.grid.layout(); this.grid.render(false); } },
};

/* ================================================================ CUTS (cut-outs table) */
const Cuts = {
  host: null, pieces: [], sel: new Set(), labels: new Set(), uid: 1, z: 10, role: 'all',
  mount(host) {
    if (this.table) return;
    this.host = host;
    host.innerHTML = `<div class="cuts">
      <div class="tray"><div class="tray-head"><div class="hud-title">CUT-OUTS</div><div class="seg" id="cutRole"><button data-v="all">all figures</button><button data-v="reading">reading subjects only</button></div><div class="taglist" id="cutLabels"></div><div class="tray-note" id="cutNote"></div></div><div class="tray-list" id="trayList"></div></div>
      <div class="table" id="cutTable"><div class="table-empty" id="tableEmpty"></div>
        <div class="table-tools"><button class="ghost" id="cutPlus" title="join two selected cut-outs side by side">+ join</button><button class="ghost" id="cutDel">remove</button><button class="ghost" id="cutClear">clear table</button></div>
        <div class="table-hint">drag from the tray · drag to compose · shift-click duplicates · wheel scales · select two and press + · click the source tag to inspect</div>
      </div></div>`;
    this.table = $('#cutTable', host); this.tray = $('#trayList', host);
    $('#cutLabels', host).addEventListener('click', e => { const b = e.target.closest('button[data-v]'); if (!b) return; const v = b.dataset.v; this.labels.has(v) ? this.labels.delete(v) : this.labels.add(v); this.update(); });
    $('#cutRole', host).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; this.role = b.dataset.v; this.update(); });
    $('#cutClear', host).addEventListener('click', () => { this.pieces.forEach(p => p.el.remove()); this.pieces = []; this.sel.clear(); this.empty(); });
    $('#cutDel', host).addEventListener('click', () => this.removeSel());
    $('#cutPlus', host).addEventListener('click', () => this.join());
    this.tray.addEventListener('pointerdown', e => {
      const t = e.target.closest('.ti'); if (!t) return; e.preventDefault();
      const r = this.table.getBoundingClientRect();
      const p = this.add(t._cut, t._shot, e.clientX - r.left, e.clientY - r.top);
      this.startDrag(p, e);
    });
    this.tray.addEventListener('pointerover', e => { const t = e.target.closest('.ti'); if (t) Tip.shot(t._shot, e); });
    this.tray.addEventListener('pointerout', () => Tip.hide());
    this.table.addEventListener('pointerdown', e => {
      if (e.target === this.table || e.target.classList.contains('table-empty')) { this.sel.clear(); this.paintSel(); }
    });
  },
  show() { this.update(); this.empty(); this.pieces.forEach(p => this.place(p)); },
  update() {
    if (!this.host) return;
    const list = viewList();
    const cuts = [], lab = {};
    let nseg = 0;
    for (const s of list) for (const c of s._cuts) {
      if (this.role === 'reading' && c.role !== 'reading') continue;
      if (c.sprite) nseg++;
      lab[c.label] = (lab[c.label] || 0) + 1; if (!this.labels.size || this.labels.has(c.label)) cuts.push([c, s]);
    }
    $$('#cutRole button', this.host).forEach(b => b.classList.toggle('on', b.dataset.v === this.role));
    $('#cutNote', this.host).textContent = cuts.length ? `${fmt(cuts.length)} figures · ${fmt(nseg)} tracked over time (they move)` : '';
    $('#cutLabels', this.host).innerHTML = Object.entries(lab).sort((a, b) => b[1] - a[1]).slice(0, 24)
      .map(([l, c]) => `<button data-v="${esc(l)}" class="${this.labels.has(l) ? 'on' : ''}">${esc(l)}<i>${c}</i></button>`).join('');
    if (!L.has.cut) {
      this.tray.innerHTML = `<div class="empty"><b>No cut-outs yet.</b><p>SAM 2 (Segment Anything) is tracking the figures in the read shots; each becomes a moving transparent cut-out here. Press ↻ in the top bar to pick them up as they arrive.</p></div>`;
      return;
    }
    if (!cuts.length) { this.tray.innerHTML = `<div class="empty"><b>No cut-outs in this selection.</b><p>Widen the filters${this.role === 'reading' ? ', show all figures' : ''}, or tick “has cut-outs”.</p></div>`; return; }
    this.tray.innerHTML = '';
    const frag = document.createDocumentFragment();
    for (const [c, s] of cuts.slice(0, 600)) {
      const t = el('div', 'ti' + (c.role === 'reading' ? ' reading' : '')); t._cut = c; t._shot = s;
      t.innerHTML = `<div class="ti-im">${c.sprite ? cutSprite(c) : `<img src="${esc(c.png)}" alt="${esc(c.label)}" loading="lazy" draggable="false">`}</div><span title="${esc(c.desc)}">${esc(c.desc)}</span>`;
      frag.appendChild(t);
    }
    this.tray.appendChild(frag);
    $$('.spr', this.tray).forEach(e => Sprites.add(e));
    if (cuts.length > 600) this.tray.insertAdjacentHTML('beforeend', `<div class="empty">showing 600 of ${fmt(cuts.length)} · narrow the filter</div>`);
  },
  empty() {
    const e = $('#tableEmpty', this.host); if (!e) return;
    e.hidden = this.pieces.length > 0;
    e.innerHTML = `<div class="plusmark">+</div><p>the composing table</p>`;
  },
  add(c, s, x, y, w, kind) {
    const p = { id: this.uid++, c, s, x, y, kind: kind || 'cut' };
    const d = el('div', 'piece' + (p.kind === 'plus' ? ' plus' : ''));
    if (p.kind === 'plus') { d.textContent = '+'; p.w = w || 60; }
    else {
      const bb = c.bbox || [0, 0, .3, .5];
      p.w = w || clamp(bb[2] * 720, 40, 520);
      d.innerHTML = `${c.sprite ? cutSprite(c) : `<img src="${esc(c.png)}" alt="${esc(c.label)}" draggable="false">`}<button class="src">${s._read[0] ? esc(L.S[s._read[0]].symbol) + ' · ' : ''}${esc(c.desc.length > 40 ? c.desc.slice(0, 38) + '…' : c.desc)} · ${s.year ?? '—'} ↗</button>`;
      const sp = $('.spr', d); if (sp) Sprites.add(sp);
      $('.src', d).addEventListener('pointerdown', e => e.stopPropagation());
      $('.src', d).addEventListener('click', e => { e.stopPropagation(); Inspector.open(s, [s]); });
    }
    p.el = d; this.table.appendChild(d); this.pieces.push(p);
    d.addEventListener('pointerdown', e => {
      if (e.shiftKey) { e.preventDefault(); const q = this.add(p.c, p.s, p.x + 28, p.y + 18, p.w, p.kind); this.startDrag(q, e); return; }
      this.startDrag(p, e);
    });
    d.addEventListener('wheel', e => { e.preventDefault(); p.w = clamp(p.w * Math.exp(-e.deltaY * 0.0015), 24, 1600); this.place(p); }, { passive: false });
    this.place(p); this.empty();
    return p;
  },
  place(p) { p.el.style.width = p.w + 'px'; if (p.kind === 'plus') p.el.style.fontSize = p.w + 'px'; p.el.style.left = p.x + 'px'; p.el.style.top = p.y + 'px'; },
  startDrag(p, e) {
    const d = p.el; d.style.zIndex = ++this.z;
    const ox = e.clientX, oy = e.clientY, px = p.x, py = p.y; let moved = false;
    const mv = ev => { const dx = ev.clientX - ox, dy = ev.clientY - oy; if (Math.abs(dx) + Math.abs(dy) > 3) moved = true; p.x = px + dx; p.y = py + dy; this.place(p); };
    const upf = ev => {
      removeEventListener('pointermove', mv); removeEventListener('pointerup', upf); removeEventListener('pointercancel', upf);
      const W = this.table.clientWidth, H = this.table.clientHeight;
      if (p.x < 0 || p.x > W || p.y < 0 || p.y > H) { // dropped outside (or clicked in the tray): land somewhere on the table
        p.x = W * (.3 + .4 * Math.random()); p.y = H * (.35 + .3 * Math.random()); this.place(p); if (!moved) return;
      }
      if (!moved) { if (this.sel.has(p)) this.sel.delete(p); else { if (!ev.metaKey && !ev.ctrlKey && this.sel.size >= 2) this.sel.clear(); this.sel.add(p); } this.paintSel(); }
    };
    addEventListener('pointermove', mv); addEventListener('pointerup', upf); addEventListener('pointercancel', upf);
  },
  paintSel() { this.pieces.forEach(p => p.el.classList.toggle('sel', this.sel.has(p))); },
  removeSel() { this.pieces = this.pieces.filter(p => { if (this.sel.has(p)) { p.el.remove(); return false; } return true; }); this.sel.clear(); this.empty(); },
  join() {
    const ps = [...this.sel].filter(p => p.kind === 'cut');
    if (ps.length < 2) { toast('select two cut-outs (click each), then +'); return; }
    const [a, b] = ps.slice(-2).sort((u, v) => u.x - v.x);
    const ha = a.el.offsetHeight, hb = b.el.offsetHeight, base = a.y + ha / 2;
    const gap = 30;
    b.x = a.x + a.w / 2 + gap * 2 + 40 + b.w / 2; b.y = base - hb / 2;
    this.place(b);
    this.add(null, null, a.x + a.w / 2 + gap + 20, base - Math.max(ha, hb) * 0.4, 56, 'plus');
    this.sel.clear(); this.paintSel();
  },
  send(s) {
    if (!this.host) this.mount($('#m-cuts'));
    const r = this.table.getBoundingClientRect(); const W = r.width || innerWidth * .7, H = r.height || innerHeight * .7;
    s._cuts.forEach((c, i) => {
      const bb = c.bbox || [.3, .3, .3, .5];
      this.add(c, s, W * .15 + (bb[0] + bb[2] / 2) * W * .7 + i * 6, H * .15 + (bb[1] + bb[3] / 2) * H * .7);
    });
  },
};

/* ================================================================ REEL  ("a film that shows each of these") */
const Reel = {
  root: null, Q: [], i: 0, playing: false, speed: 1, loop: false, src: 'table', t: 0, last: 0, raf: 0,
  build() {
    const R = this.root = $('#reel');
    R.innerHTML = `
      <div class="reel-stage">
        <video class="rv a" playsinline muted preload="auto"></video><video class="rv b" playsinline muted preload="auto"></video>
        <div class="card" id="reelCard"></div>
        <div class="lower" id="reelLower"></div>
      </div>
      <div class="film" id="reelFilmBox" hidden><video controls playsinline preload="none"></video><button class="ghost" id="reelFilmX">✕ back to the live reel</button><div class="film-msg" hidden>the rendered film isn’t there yet (reel/cineosis-reel.mp4 is being re-rendered) — try again in a few minutes</div></div>
      <div class="reel-top"><span class="hud-title">REEL</span><span id="reelPos"></span><button class="ghost" id="reelMute" title="sound">sound off</button><button class="ghost" id="reelFilm" title="the pre-rendered film, reel/cineosis-reel.mp4">watch the rendered film</button><button class="ghost" id="reelClose" title="close (Esc)">✕</button></div>
      <div class="reel-bar">
        <div class="rail" id="reelRail"><div class="rail-ph"></div></div>
        <div class="reel-ctl">
          <button class="ghost" data-a="prev" title="previous sign (←)">⏮</button>
          <button class="ghost big" data-a="play" title="play / pause (space)">▶</button>
          <button class="ghost" data-a="next" title="next sign (→)">⏭</button>
          <span class="seg" id="reelSpeed"><button data-v="0.5">0.5×</button><button data-v="1">1×</button><button data-v="2">2×</button></span>
          <button class="ghost" data-a="loop">loop</button>
          <span class="seg" id="reelSrc"><button data-v="table">table order</button><button data-v="sel">current selection</button></span>
          <span class="reel-note" id="reelNote"></span>
        </div>
      </div>`;
    this.va = $('.rv.a', R); this.vb = $('.rv.b', R); this.cur = this.va; this.nxt = this.vb;
    for (const v of [this.va, this.vb]) v.addEventListener('error', () => {
      if (remoteFallback(v, v._shot)) return;
      if (v === this.cur && this.item() && this.item().type === 'shot') this.skipSoon();
    });
    $('#reelClose', R).onclick = () => Shell.setMode(Shell.prevMode || 'wall');
    const fb = $('#reelFilmBox', R), fv = $('video', fb);
    fv.addEventListener('error', () => { $('.film-msg', fb).hidden = false; });
    $('#reelFilm', R).onclick = () => {
      this.pause(); fb.hidden = false; $('.film-msg', fb).hidden = true;
      fv.src = 'reel/cineosis-reel.mp4?v=' + Date.now(); fv.play().catch(() => {});
    };
    this.closeFilm = () => { fv.pause(); fv.removeAttribute('src'); fv.load(); fb.hidden = true; };
    $('#reelFilmX', R).onclick = () => this.closeFilm();
    $('#reelMute', R).onclick = () => { const m = !this.va.muted; this.va.muted = this.vb.muted = m; $('#reelMute', R).textContent = m ? 'sound off' : 'sound on'; };
    $('.reel-ctl', R).addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      const a = b.dataset.a;
      if (a === 'play') this.toggle(); else if (a === 'prev') this.jumpSign(-1); else if (a === 'next') this.jumpSign(1);
      else if (a === 'loop') { this.loop = !this.loop; b.classList.toggle('on', this.loop); }
    });
    $('#reelSpeed', R).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; this.speed = +b.dataset.v; this.va.playbackRate = this.vb.playbackRate = this.speed; this.paintCtl(); });
    $('#reelSrc', R).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; this.src = b.dataset.v; this.custom = null; this.start(); });
    $('#reelRail', R).addEventListener('click', e => { const r = e.currentTarget.getBoundingClientRect(); this.go(Math.floor(clamp((e.clientX - r.left) / r.width, 0, .9999) * this.Q.length)); });
    let idle; R.addEventListener('pointermove', () => { R.classList.remove('idle'); clearTimeout(idle); idle = setTimeout(() => { if (this.playing) R.classList.add('idle'); }, 2600); });
  },
  queue() {
    if (this.custom) return this.custom;
    const Q = [];
    if (this.src === 'table') {
      const signs = F.signs.size ? L.signs.filter(s => F.signs.has(s.n)) : L.signs;
      for (const sg of signs) {
        const shots = L.shots.filter(s => s._read.includes(sg.n)).sort((a, b) => ((entryOf(b, sg.n) || {}).conf || 0) - ((entryOf(a, sg.n) || {}).conf || 0));
        Q.push({ type: 'card', n: sg.n });
        for (const s of shots) Q.push({ type: 'shot', s, n: sg.n, e: entryOf(s, sg.n) });
      }
    } else {
      let last = null;
      for (const s of viewList().slice(0, 400)) {
        const n = signOf(s);
        if (n && n !== last) { Q.push({ type: 'card', n }); last = n; }
        Q.push({ type: 'shot', s, n, e: n ? entryOf(s, n) : null });
      }
    }
    return Q;
  },
  open() {
    if (!this.root) this.build();
    this.root.hidden = false; document.body.classList.add('reeling');
    this.start();
  },
  close() {
    if (!this.root) return;
    this.custom = null;
    this.pause(); if (this.closeFilm) this.closeFilm(); this.root.hidden = true; document.body.classList.remove('reeling');
    [this.va, this.vb].forEach(v => { v.removeAttribute('src'); v.dataset.key = ''; v.load(); });
  },
  start() {
    this.Q = this.queue(); this.i = 0;
    const R = this.root;
    $('#reelRail', R).innerHTML = '<div class="rail-ph"></div>' + this.Q.map((q, i) => q.type === 'card' ? `<i style="left:${i / Math.max(1, this.Q.length) * 100}%;background:${signColor(q.n)}"></i>` : '').join('');
    $$('#reelSrc button', R).forEach(b => b.classList.toggle('on', !this.custom && b.dataset.v === this.src));
    $('#reelNote', R).textContent = this.custom ? `montage · ${this.Q.filter(q => q.type === 'shot').length} clips in time order` : `${this.Q.filter(q => q.type === 'card').length} signs · ${this.Q.filter(q => q.type === 'shot').length} shots` + (this.src === 'table' && F.signs.size ? ' · limited to the selected signs' : '');
    if (!this.Q.length) { $('#reelCard', R).innerHTML = `<div class="c-name">Nothing to play in this selection.</div>`; $('#reelCard', R).hidden = false; return; }
    this.go(0); this.play();
  },
  item() { return this.Q[this.i]; },
  go(i) {
    if (!this.Q.length) return;
    if (i >= this.Q.length) { if (this.loop) i = 0; else { this.i = this.Q.length - 1; this.pause(); return; } }
    if (i < 0) i = 0;
    this.i = i; this.t = 0; this.stallT = 0; this.lastCT = -1;
    const q = this.item(), R = this.root, card = $('#reelCard', R), lower = $('#reelLower', R);
    clearTimeout(this.skipT);
    if (q.type === 'card' && !L.S[q.n]) {        // a montage title card
      card.style.setProperty('--c', '#ece6da');
      card.innerHTML = `<div class="c-name">${esc(q.title || 'montage')}</div><div class="c-img">${esc(q.sub || '')}</div>${q.why ? `<div class="c-diff">${esc(q.why)}</div>` : ''}`;
      card.hidden = false; card.classList.remove('in'); void card.offsetWidth; card.classList.add('in');
      lower.hidden = true; this.cur.classList.remove('on'); this.cur.pause(); this.preload();
    } else if (q.type === 'card') {
      const s = L.S[q.n];
      card.style.setProperty('--c', DOMC[s.dom]);
      card.innerHTML = `<div class="c-sym">${esc(s.symbol)}</div><div class="c-name">${esc(s.name)}</div><div class="c-img">${esc(s.image)} · ${esc(s.code)} · ${esc(s.n)}</div><div class="c-diff">${esc(s.difference || s.gloss || '')}</div>`;
      card.hidden = false; card.classList.remove('in'); void card.offsetWidth; card.classList.add('in');
      lower.hidden = true; this.cur.classList.remove('on'); this.cur.pause(); this.preload();
    } else {
      card.hidden = true;
      const s = q.s, key = s.id;
      let v = this.cur;
      if (this.nxt.dataset.key === key) { v = this.nxt; this.nxt = this.cur; this.cur = v; }
      else if (v.dataset.key !== key) this.assign(v, s, qStart(q));
      this.nxt.classList.remove('on'); this.nxt.pause();
      v.classList.add('on'); v.playbackRate = this.speed;
      const t0 = qStart(q);
      this.t0 = t0; this.limit = q.b != null ? Math.max(t0 + .2, q.b) : Math.min(s._dur || 5, t0 + 5);
      this.lastCT = -1;
      if (v.readyState >= 1) { try { v.currentTime = t0; } catch (e) { /* not ready */ } if (this.playing) v.play().catch(() => {}); }
      const e = q.e, sg = q.n && L.S[q.n];
      lower.innerHTML = `<div class="l-row">${q.n ? chip(q.n) : ''}<span class="l-sign">${sg ? esc(sg.name) : 'unread'}</span>${e ? `<span class="l-conf">${e.conf ?? '—'}%</span>` : ''}</div>
        <div class="l-note">${q.note ? esc(q.note) : e ? esc(e.note) : esc(((s.found || [])[0] || {}).q || '')}</div>
        <div class="l-meta">${esc(s.title)} · ${s.year ?? 'undated'} · ${tc(s.start || 0)}</div>
        ${e && e.conf != null ? readingBar(q.n, e) : ''}`;
      lower.hidden = false;
      this.preload();
    }
    this.paintCtl();
  },
  preload() {
    for (let j = this.i + 1; j < Math.min(this.Q.length, this.i + 4); j++) {
      const q = this.Q[j]; if (q.type !== 'shot') continue;
      if (this.nxt.dataset.key !== q.s.id) this.assign(this.nxt, q.s, qStart(q));
      break;
    }
  },
  /** load shot s into video v (local clips arrive as blobs so they can seek); seek to its start frame and play if current */
  assign(v, s, t0) {
    const key = s.id; v.dataset.key = key; v._shot = s; v.pause(); v.removeAttribute('src');
    playable(s).then(url => {
      if (v.dataset.key !== key) return;
      v.addEventListener('loadedmetadata', () => {
        if (v.dataset.key !== key) return;
        try { v.currentTime = t0 != null ? t0 : reelStart(s); } catch (e) { /* ignore */ }
        if (v === this.cur && this.playing) v.play().catch(() => {});
      }, { once: true });
      v.preload = 'auto'; v.src = url;
    });
  },
  skipSoon() { clearTimeout(this.skipT); this.skipT = setTimeout(() => this.go(this.i + 1), 700); },
  play() {
    this.playing = true; this.last = performance.now();
    const q = this.item(); if (q && q.type === 'shot') this.cur.play().catch(() => {});
    cancelAnimationFrame(this.raf); this.raf = requestAnimationFrame(() => this.tick()); this.paintCtl();
  },
  pause() { this.playing = false; this.cur && this.cur.pause(); cancelAnimationFrame(this.raf); this.paintCtl(); if (this.root) this.root.classList.remove('idle'); },
  toggle() { this.playing ? this.pause() : this.play(); },
  tick() {
    if (!this.playing) return;
    const now = performance.now(), dt = (now - this.last) / 1000; this.last = now;
    const q = this.item();
    if (q) {
      if (q.type === 'card') { this.t += dt * this.speed; if (this.t >= 2.5) this.go(this.i + 1); }
      else {
        const v = this.cur, ct = v.currentTime;
        if (ct === this.lastCT) { this.stallT += dt; if (this.stallT > 6) this.go(this.i + 1); } else { this.stallT = 0; this.lastCT = ct; }
        this.t = ct;
        if (ct >= this.limit || v.ended) this.go(this.i + 1);
      }
      this.paintRail();
    }
    this.raf = requestAnimationFrame(() => this.tick());
  },
  jumpSign(d) {
    if (!this.Q.length) return;
    let i = this.i;
    if (d < 0) { // to start of this sign, or previous if already near start
      let st = i; while (st > 0 && this.Q[st].type !== 'card') st--;
      if (i - st <= 1 && this.t < 1) { st--; while (st > 0 && this.Q[st].type !== 'card') st--; }
      i = Math.max(0, st);
    } else { i++; while (i < this.Q.length && this.Q[i].type !== 'card') i++; if (i >= this.Q.length) i = this.loop ? 0 : this.Q.length - 1; }
    this.go(i);
  },
  step(d) { this.go(clamp(this.i + d, 0, this.Q.length - 1)); },
  paintRail() {
    const ph = $('.rail-ph', this.root); if (!ph || !this.Q.length) return;
    const q = this.item(), frac = q.type === 'card' ? this.t / 2.5 : (this.t - (this.t0 || 0)) / Math.max(.1, (this.limit || 5) - (this.t0 || 0));
    ph.style.left = ((this.i + clamp(frac, 0, 1)) / this.Q.length * 100) + '%';
  },
  paintCtl() {
    const R = this.root; if (!R) return;
    $('[data-a="play"]', R).textContent = this.playing ? '❚❚' : '▶';
    $$('#reelSpeed button', R).forEach(b => b.classList.toggle('on', +b.dataset.v === this.speed));
    $$('#reelSrc button', R).forEach(b => b.classList.toggle('on', !this.custom && b.dataset.v === this.src));
    const q = this.item();
    const signsTotal = this.Q.filter(x => x.type === 'card').length;
    let si = 0; for (let j = 0; j <= this.i && j < this.Q.length; j++) if (this.Q[j].type === 'card') si++;
    $('#reelPos', R).innerHTML = q ? `${q.n ? chip(q.n) : ''} sign ${si} / ${signsTotal} · item ${this.i + 1} / ${this.Q.length}` : '';
    this.paintRail();
  },
  key(e) {
    if (!$('#reelFilmBox', this.root).hidden && e.key !== 'Escape') return false;
    if (e.key === ' ') { e.preventDefault(); this.toggle(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); this.jumpSign(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); this.jumpSign(-1); }
    else if (e.key === ']') this.step(1);
    else if (e.key === '[') this.step(-1);
    else if (e.key === 'Escape') { if (!$('#reelFilmBox', this.root).hidden) this.closeFilm(); else Shell.setMode(Shell.prevMode || 'wall'); }
    else return false;
    return true;
  },
};
const qStart = q => q.a != null ? Math.max(0, q.a) : reelStart(q.s);
const reelStart = s => s.read_t != null ? Math.max(0, s.read_t - 0.6) : 0;
/* server.py serves byte ranges, so local clips stream and seek directly; remote clips are range-capable too. */
/** a local clip that 404s (e.g. not published to Pages) falls back once to the archive's remote mp4 */
function remoteFallback(v, s) {
  const src = v.getAttribute('src') || '';
  if (!s || !s.clip || !s.video || !src || src === s.video || !src.includes(s.clip)) return false;
  v.src = s.video; if (v.play) v.play().catch(() => {}); return true;
}
function playable(s) { return Promise.resolve(s.clip || s.video); }
/** default still/seek position for a shot, seconds into its clip: the frame the editor read, else the matched frame */
function readT(s) { return s.read_t != null ? Math.max(0, s.read_t) : Math.max(0, (s.match || s.start || 0) - (s.start || 0)); }

function readingBar(n, e) {
  if (!e || e.conf == null) return '';
  const c = signColor(n), a = e.alt ? signColor(String(e.alt)) : '#555';
  const shot = clamp(e.shot ?? 0, 0, 100), hatch = Math.max(0, (e.conf ?? 0) - shot), alt = e.alt_conf || 0;
  const as = e.alt && L.S[String(e.alt)] ? L.S[String(e.alt)].symbol : '';
  return `<div class="rbar" title="${shot}% from the shot alone · ${e.conf}% in context${as ? ` · ${as} ${alt}%` : ''}"><span style="width:${shot}%;background:${c}"></span><span class="hatch" style="width:${hatch}%;--c:${c}"></span><span style="width:${alt}%;background:${a};opacity:.8"></span></div>`;
}

/* ================================================================ INSPECTOR */
const Inspector = {
  root: null, s: null, list: [], A: null, B: null, loopAB: false, speed: 1, showCuts: false,
  build() {
    const R = this.root = $('#inspector');
    R.innerHTML = `
      <div class="ins-top">
        <button class="ghost" id="insPrev" title="previous (↑)">↑</button><button class="ghost" id="insNext" title="next (↓)">↓</button>
        <div class="ins-title" id="insTitle"></div>
        <button class="ghost" id="insClose" title="close (Esc)">✕</button>
      </div>
      <div class="ins-body">
        <div class="ins-stage" id="insStage">
          <div class="frame" id="insFrame">
            <video id="insVid" playsinline preload="auto"></video>
            <div class="seglayer" id="insSegs"></div>
            <div class="cutlayer" id="insCuts"></div>
            <div class="mline" id="insMline"></div>
          </div>
          <div class="ins-msg" id="insMsg" hidden></div>
        </div>
        <aside class="ins-side" id="insSide"></aside>
        <div class="scrub">
          <div class="scrub-read">
            <div class="tcbig" id="insTC">00:00:00:00</div>
            <div class="spd"><span id="insSpd">1.0</span><small>x</small></div>
            <div class="scrub-btns">
              <button class="ghost" data-a="back" title="−1 frame (,)">‹</button>
              <button class="ghost big" data-a="play" title="play / pause (space)">▶</button>
              <button class="ghost" data-a="fwd" title="+1 frame (.)">›</button>
              <span class="seg" id="insSpeeds"><button data-v="0">0.0</button><button data-v="0.25">.25</button><button data-v="0.5">.5</button><button data-v="1">1</button><button data-v="2">2</button></span>
              <button class="ghost" data-a="A" title="set in point (A)">A</button><button class="ghost" data-a="B" title="set out point (B)">B</button>
              <button class="ghost" data-a="loop" title="loop A–B (L)">loop</button>
              <button class="ghost" data-a="R" title="jump to the frame the editor read (R)">R</button>
              <button class="ghost" data-a="M" title="jump to matched frame (M)">M</button>
              <button class="ghost" data-a="clr" title="clear A/B">clear</button>
            </div>
          </div>
          <div class="tl" id="insTL"><div class="tl-strip" id="insStrip"></div><div class="tl-ab" id="insAB"></div><div class="tl-seg" id="insSegWin" title="SAM 2 tracking window" hidden></div><div class="tl-ticks" id="insTicks"></div><div class="tl-marks" id="insMarks"></div><div class="tl-ph" id="insPH"></div></div>
          <div class="save">
            <select id="insSign" aria-label="sign"></select>
            <input id="insNote" placeholder="note — why this sub-shot is this sign" spellcheck="false">
            <span class="ab-read" id="insABread"></span>
            <button id="insSave">save sub-shot</button>
            <span class="ins-send" id="insSend"></span>
            <span id="insSaved"></span>
          </div>
        </div>
      </div>`;
    const v = this.v = $('#insVid', R);
    $('#insClose', R).onclick = () => this.close();
    $('#insPrev', R).onclick = () => this.nav(-1);
    $('#insNext', R).onclick = () => this.nav(1);
    $('#insSign', R).innerHTML = L.signs.map(s => `<option value="${esc(s.n)}">${esc(s.symbol)} · ${esc(s.name)}</option>`).join('');
    $('.scrub-btns', R).addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.v != null) this.setSpeed(+b.dataset.v); else this.act(b.dataset.a); });
    $('#insSave', R).onclick = () => this.save();
    $('#insSend', R).addEventListener('click', e => {
      const b = e.target.closest('[data-send]'); if (!b) return; const s = this.s;
      const ab = this.A != null && this.B != null;
      const n = s._read[0] || null;
      Send.go(b.dataset.send, `${s.title}${ab ? ` · ${this.A.toFixed(1)}–${this.B.toFixed(1)}s` : ''}`, 'sequence',
        [ab ? { s, n, a: +this.A.toFixed(3), b: +this.B.toFixed(3) } : { s, n }]);
    });
    v.addEventListener('loadedmetadata', () => { this.fitFrame(); this.ticks(); this.marks(); if (this.pendingSeek != null) { v.currentTime = this.pendingSeek; this.pendingSeek = null; } });
    v.addEventListener('error', () => !remoteFallback(v, this.s) && v.getAttribute('src') && this.msg('video could not be loaded — ' + (this.s && this.s.clip ? 'local clip missing' : 'remote source unavailable')));
    v.addEventListener('play', () => this.paintPlay()); v.addEventListener('pause', () => this.paintPlay());
    const TL = $('#insTL', R); let sd = false;
    const seek = e => { const r = TL.getBoundingClientRect(); const d = this.dur(); v.currentTime = clamp((e.clientX - r.left) / r.width, 0, 1) * d; this.paint(); };
    TL.addEventListener('pointerdown', e => { if (e.target.closest('.mk')) return; TL.setPointerCapture(e.pointerId); sd = true; v.pause(); seek(e); });
    TL.addEventListener('pointermove', e => { if (sd) seek(e); });
    TL.addEventListener('pointerup', () => { sd = false; });
    $('#insMarks', R).addEventListener('click', e => { const m = e.target.closest('.mk'); if (m) { v.currentTime = +m.dataset.t; this.paint(); } });
    $('#insMline', R).addEventListener('click', e => { const m = e.target.closest('[data-t]'); if (m) { v.pause(); v.currentTime = +m.dataset.t; this.paint(); } });
    $('#insFrame', R).addEventListener('wheel', e => { if (e.target.closest('.cutp')) return; e.preventDefault(); v.pause(); this.stepF(e.deltaY > 0 ? 1 : -1); }, { passive: false });
    $('#insFrame', R).addEventListener('click', e => { if (e.target === v) this.act('play'); });
    this.ro = new ResizeObserver(() => this.fitFrame()); this.ro.observe($('#insStage', R));
  },
  open(s, list) {
    if (!s) return;
    if (!this.root) this.build();
    this.list = list && list.length ? list : [s];
    this.root.hidden = false; document.body.classList.add('inspecting');
    Guide.mark(2);
    if (Shell.mode === 'reel') Reel.pause();
    this.load(s);
  },
  close() {
    if (!this.root || this.root.hidden) return;
    this.tok = (this.tok || 0) + 1;
    this.v.pause(); this.v.removeAttribute('src'); this.v.load();
    this.root.hidden = true; document.body.classList.remove('inspecting');
    cancelAnimationFrame(this.raf);
  },
  nav(d) { const i = this.list.indexOf(this.s); if (i < 0) return; const j = i + d; if (j >= 0 && j < this.list.length) this.load(this.list[j]); },
  load(s) {
    this.s = s; this.A = null; this.B = null; this.loopAB = false; this.showCuts = false;
    this.showSegs = true; this.lift = new Set(); this.hlk = null; this._segF = null; Sprites.prune();
    const R = this.root, v = this.v;
    $('#insMsg', R).hidden = true;
    const tok = this.tok = (this.tok || 0) + 1;
    v.pause(); v.removeAttribute('src'); v.load();
    v.poster = s.thumb; this.pendingSeek = readT(s);
    playable(s).then(url => {
      if (tok !== this.tok || this.root.hidden) return;
      v.src = url; v.playbackRate = this.speed || 1; v.muted = false;
      v.play().catch(() => { v.muted = true; v.play().catch(() => {}); });
    });
    const i = this.list.indexOf(s);
    $('#insTitle', R).innerHTML = `${s._live ? '<span class="livebadge">LIVE</span>' : ''}${colBadge(s) || '<span class="colbadge c">CINEOSIS</span>'}<b>${esc(s.title)}</b> <span>${s.year ?? 'undated'} · ${tc(s.start || 0)} – ${tc(s.end || 0)} · ${s.clip ? 'local clip' : 'remote'}</span>${this.list.length > 1 ? `<em>${i + 1} / ${fmt(this.list.length)}</em>` : ''}`;
    $('#insStrip', R).style.backgroundImage = s.strip ? `url("${s.strip}")` : `url("${s.thumb}")`;
    $('#insStrip', R).classList.toggle('thumbonly', !s.strip);
    const def = s._read[0] || s._found[0] || '1';
    $('#insSign', R).value = def;
    $('#insNote', R).value = ''; $('#insSaved', R).textContent = '';
    $('#insSend', R).innerHTML = sendButtons();
    this.side(); this.cutLayer(); this.segLayer(); this.marks(); this.ticks(); this.paintSpeeds();
    cancelAnimationFrame(this.raf);
    const loop = () => { this.paint(); this.raf = requestAnimationFrame(loop); };
    this.raf = requestAnimationFrame(loop);
  },
  dur() { const d = this.v.duration; return isFinite(d) && d > 0 ? d : (this.s ? this.s._dur : 1); },
  msg(t) { const m = $('#insMsg', this.root); m.textContent = t; m.hidden = false; },
  fitFrame() {
    if (!this.root || this.root.hidden) return;
    const st = $('#insStage', this.root), fr = $('#insFrame', this.root);
    const W = st.clientWidth - 8, H = st.clientHeight - 8;
    const ar = (this.v.videoWidth && this.v.videoHeight) ? this.v.videoWidth / this.v.videoHeight : 4 / 3;
    let w = W, h = w / ar; if (h > H) { h = H; w = h * ar; }
    fr.style.width = Math.max(10, w) + 'px'; fr.style.height = Math.max(10, h) + 'px';
  },
  setSpeed(x) {
    this.speed = x;
    if (x === 0) this.v.pause(); else { this.v.playbackRate = x; if (this.v.paused) this.v.play().catch(() => {}); }
    this.paintSpeeds();
  },
  paintSpeeds() {
    const R = this.root, sp = this.v.paused ? 0 : this.speed;
    $('#insSpd', R).textContent = sp.toFixed(sp && sp < 1 ? 2 : 1);
    $$('#insSpeeds button', R).forEach(b => b.classList.toggle('on', +b.dataset.v === sp));
  },
  paintPlay() { const b = $('[data-a="play"]', this.root); if (b) b.textContent = this.v.paused ? '▶' : '❚❚'; this.paintSpeeds(); },
  stepF(n) { const v = this.v; v.pause(); v.currentTime = clamp(v.currentTime + n / FPS, 0, this.dur()); this.paint(); },
  act(a) {
    const v = this.v, s = this.s;
    if (a === 'play') { if (v.paused) { if (!this.speed) this.speed = 1; v.playbackRate = this.speed; v.play().catch(() => {}); } else v.pause(); }
    else if (a === 'back') this.stepF(-1);
    else if (a === 'fwd') this.stepF(1);
    else if (a === 'A') { this.A = v.currentTime; if (this.B != null && this.B < this.A) this.B = null; this.marks(); }
    else if (a === 'B') { this.B = v.currentTime; if (this.A != null && this.A > this.B) { const t = this.A; this.A = this.B; this.B = t; } this.marks(); }
    else if (a === 'M') { v.pause(); v.currentTime = Math.max(0, s.match - s.start); }
    else if (a === 'R') { v.pause(); v.currentTime = readT(s); }
    else if (a === 'clr') { this.A = this.B = null; this.loopAB = false; this.marks(); }
    else if (a === 'loop') { this.loopAB = !this.loopAB; this.marks(); if (this.loopAB && this.A != null) v.currentTime = this.A; }
    else if (a === 'jA' && this.A != null) v.currentTime = this.A;
    else if (a === 'jB' && this.B != null) v.currentTime = this.B;
    this.paint();
  },
  paint() {
    const v = this.v, s = this.s; if (!s) return;
    const d = this.dur(), t = v.currentTime || 0;
    if (this.loopAB && this.A != null && this.B != null && t >= this.B && !v.paused) v.currentTime = this.A;
    const R = this.root;
    const tcs = tc((s.start || 0) + t);
    if (tcs !== this._tc) { $('#insTC', R).textContent = tcs; this._tc = tcs; }
    $('#insPH', R).style.left = (t / d * 100) + '%';
    this.segPaint();
  },
  ticks() {
    const d = this.dur(), T = $('#insTicks', this.root); let h = '';
    const step = d > 40 ? 5 : d > 12 ? 1 : 0.5;
    for (let x = 0; x <= d + 1e-6; x += step) h += `<i style="left:${x / d * 100}%" class="${Math.abs(x % 5) < 1e-6 ? 'maj' : ''}"></i>`;
    T.innerHTML = h;
  },
  marks() {
    const R = this.root, s = this.s; if (!s) return;
    const d = this.dur(), M = Math.max(0, (s.match || s.start) - s.start);
    const list = [];
    if (s.read_t != null) list.push(['R', s.read_t, 'read frame']);
    list.push(['M', M, 'match']); if (this.A != null) list.push(['A', this.A, 'in']); if (this.B != null) list.push(['B', this.B, 'out']);
    $('#insMarks', R).innerHTML = list.map(([k, t]) => `<div class="mk mk-${k}" data-t="${t}" style="left:${clamp(t / d, 0, 1) * 100}%"><b>${k}</b></div>`).join('');
    const ab = $('#insAB', R);
    if (this.A != null && this.B != null) { ab.hidden = false; ab.style.left = this.A / d * 100 + '%'; ab.style.width = (this.B - this.A) / d * 100 + '%'; ab.classList.toggle('loop', this.loopAB); } else ab.hidden = true;
    const g = this.segs(), sw = $('#insSegWin', R);
    if (g) { sw.hidden = false; sw.style.left = clamp(g.t0 / d, 0, 1) * 100 + '%'; sw.style.width = clamp(g.frames / g.fps / d, 0, 1) * 100 + '%'; } else sw.hidden = true;
    $('#insMline', R).innerHTML = list.map(([k, t, w]) => `<div class="ml" data-t="${t}"><b>${k}</b><span>${tc(s.start + t)}</span><em>${w}</em></div>`).join('');
    $('#insABread', R).textContent = this.A != null || this.B != null ? `A ${this.A != null ? this.A.toFixed(2) + 's' : '—'} · B ${this.B != null ? this.B.toFixed(2) + 's' : '—'}` : 'set A / B for a sub-shot';
    $$('[data-a="loop"]', R).forEach(b => b.classList.toggle('on', this.loopAB));
  },
  side() {
    const s = this.s, R = this.root;
    const pend = t => `<span class="pending">${t}</span>`;
    const pal = s.palette ? `<div class="pal">${s.palette.map(c => `<i style="background:${esc(c)}" title="${esc(c)}"></i>`).join('')}</div>` : pend('palette pending');
    const subj = s.subjects && s.subjects.length ? s.subjects.map(x => `<div class="sbar"><span>${esc(x.label)}</span><i><b style="width:${Math.round((x.p || 0) * 100)}%"></b></i><em>${Math.round((x.p || 0) * 100)}%</em></div>`).join('') : pend('subjects pending');
    const au = s.audio ? `${esc(s.audio.kind)}${s.audio.has_audio === false ? ' · no track' : ''} · ${s.audio.rms_db != null ? s.audio.rms_db.toFixed(1) + ' dB' : ''} · silence ${Math.round((s.audio.silence || 0) * 100)}% · flatness ${(s.audio.flatness ?? 0).toFixed(2)}` : pend('audio pending');
    const reads = (s.signs || []).map(e => {
      const n = String(e.n), sg = L.S[n], alt = e.alt != null ? String(e.alt) : null;
      return `<div class="rd"><div class="rd-h">${chip(n, 'big')}<div><b>${esc(sg ? sg.name : n)}</b><span>${e.conf != null ? e.conf + '% in context' : ''}${e.shot != null ? ` · ${e.shot}% from the shot alone` : ''}</span></div></div>
        ${readingBar(n, e)}
        <p class="rd-n">${esc(e.note || '')}</p>
        ${alt && L.S[alt] ? `<p class="rd-f">else ${chip(alt, 'sm')} ${esc(L.S[alt].name)} ${e.alt_conf ?? ''}% — <i>${esc(e.flip || '')}</i></p>` : ''}</div>`;
    }).join('');
    const found = (s.found || []).slice(0, 12).map(f => `<div class="fd">${chip(String(f.n), 'sm')}<span>“${esc(f.q)}”</span><em>#${f.rank + 1}</em></div>`).join('');
    const mine = L.assignments.filter(a => a.id === s.id).map(a => `<div class="fd">${chip(String(a.n), 'sm')}<span>${esc(a.note || '')}</span><em>${a.a != null ? (+a.a).toFixed(1) : '—'}–${a.b != null ? (+a.b).toFixed(1) : '—'}s</em></div>`).join('');
    const seg = this.segs(), cuts = !seg && s.cutouts && s.cutouts.length;
    R.querySelector('#insSide').innerHTML = `
      ${wygBlock(s)}
      ${affinityBlock(s)}
      ${seg ? this.segBlock(seg) : (s._read.length ? `<div class="sd-block"><h4>segments over time</h4>${pend('SAM 2 tracking for this shot is still running — press ↻ later')}</div>` : '')}
      <div class="sd-block"><h4>editor’s reading</h4>${reads || pend(s._live ? 'live result — not read yet; assign it below' : 'not read — surfaced by search only')}</div>
      <div class="sd-block"><h4>shot</h4><a class="arch" href="${esc(s.page)}" target="_blank" rel="noopener">open in the archive ↗</a>
        <div class="kv"><span>year</span><b>${s.year ?? '—'}</b><span>source</span><b>${tc(s.start || 0)} → ${tc(s.end || 0)}</b><span>length</span><b>${s._dur.toFixed(2)} s</b>
        ${s.read_t != null ? `<span>read</span><b>${tc((s.start || 0) + s.read_t)}</b>` : ''}
        <span>matched</span><b>${tc(s.match || 0)}</b><span>colour</span><b>${s.bw ? 'black &amp; white' : 'colour'}</b><span>scale</span><b>${s.scale ? esc(s.scale) : '<span class="pending">pending</span>'}</b>
        ${s.hue != null ? `<span>hue</span><b>${Math.round(s.hue)}° ${hbLabel(s._hb)} · lum ${(s.lum ?? 0).toFixed(2)} · sat ${(s.sat ?? 0).toFixed(2)}</b>` : ''}
        ${s.sim != null ? `<span>sim</span><b>#${s.sim}</b>` : ''}</div></div>
      <div class="sd-block"><h4>palette</h4>${pal}</div>
      <div class="sd-block"><h4>subjects <small>CLIP zero-shot</small></h4>${subj}</div>
      <div class="sd-block"><h4>audio</h4><div class="au">${au}</div></div>
      ${cuts ? `<div class="sd-block"><h4>single-frame cut-outs · ${s.cutouts.length}</h4><div class="cutbtns"><button class="ghost" id="insCutT">${this.showCuts ? 'hide' : 'show'} on frame (C)</button><button class="ghost" id="insCutSend">send to table</button></div>
        <div class="cutthumbs">${s.cutouts.map(c => `<span><img src="${esc(c.png)}" alt=""><em>${esc(c.label)}</em></span>`).join('')}</div></div>` : ''}
      ${found ? `<div class="sd-block"><h4>found by these searches</h4>${found}</div>` : ''}
      ${mine ? `<div class="sd-block"><h4>your sub-shots <small>${L.server ? 'saved to assignments.json' : 'saved in this browser'}</small></h4>${mine}<div class="cutbtns" style="margin-top:10px"><button class="ghost" id="insExport">export assignments.json</button></div></div>` : ''}`;
    const ex = $('#insExport', R); if (ex) ex.onclick = exportAssignments;
    const ct = $('#insCutT', R); if (ct) ct.onclick = () => this.toggleCuts();
    const cs = $('#insCutSend', R); if (cs) cs.onclick = () => { Cuts.send(s); toast(`${s.cutouts.length} cut-out${s.cutouts.length > 1 ? 's' : ''} sent to the table`); };
    // affinity table: hover readout, click filters the wall
    $$('.wy-go', R).forEach(b => { b.onclick = () => Wyg.goBeat(b.dataset.beat); });
    const at = $('.aff', R);
    if (at) {
      const out = $('.aff-read', R), def = out.innerHTML;
      at.addEventListener('pointerover', e => { const c = e.target.closest('.ac'); if (c) out.innerHTML = affReadout(s, c.dataset.n); });
      at.addEventListener('pointerleave', () => { out.innerHTML = def; });
      at.addEventListener('click', e => {
        const c = e.target.closest('.ac'); if (!c) return;
        if (e.altKey) { Send.sendFamily(c.dataset.n, 'cut'); return; }
        F.signs = new Set([c.dataset.n]); this.close(); if (Shell.mode !== 'wall') Shell.setMode('wall'); refresh();
        toast(`wall filtered to ${L.S[c.dataset.n].symbol} · ${L.S[c.dataset.n].name}`);
      });
    }
    // segment list
    const sl = $('.seglist', R);
    if (sl) {
      sl.addEventListener('pointerover', e => { const r = e.target.closest('.sg'); this.hl(r ? +r.dataset.k : null); });
      sl.addEventListener('pointerleave', () => this.hl(null));
      sl.addEventListener('click', e => {
        const r = e.target.closest('.sg'); if (!r) return;
        const k = +r.dataset.k; this.lift.has(k) ? this.lift.delete(k) : this.lift.add(k);
        r.classList.toggle('lifted', this.lift.has(k)); this.segLayer();
      });
      $('#segT', R).onclick = () => this.toggleSegs();
      $('#segSend', R).onclick = () => { Cuts.send(s); toast('tracked segments sent to the cut-outs table'); };
      $$('.spr', sl).forEach(el => Sprites.add(el));
    }
  },
  segs() { const g = this.s && this.s.segments; return g && g.objects && g.objects.length ? g : null; },
  segBlock(g) {
    const rows = g.objects.map((o, i) => `
      <div class="sg${this.lift.has(o.k) ? ' lifted' : ''}${o.role === 'reading' ? ' reading' : ''}" data-k="${o.k}" style="--sc:${segColor(o, i)}">
        ${sprHTML(o, g)}
        <div class="sg-t"><b>${esc(o.desc || o.label)}</b>
          <span>${o.role === 'reading' ? 'reading subject · ' : ''}${esc(o.label || '')} · ${esc(o.src || '')}</span>
          <span>match ${o.match != null ? Math.round(o.match * 100) + '%' : '—'} · present ${Math.round((o.present || 0) * 100)}%</span></div>
      </div>`).join('');
    return `<div class="sd-block"><h4>segments over time <small>SAM 2 · ${g.frames} frames @ ${g.fps} fps · ${(g.frames / g.fps).toFixed(1)} s</small></h4>
      <div class="cutbtns"><button class="ghost${this.showSegs ? ' on' : ''}" id="segT">segments: ${this.showSegs ? 'on' : 'off'} (S)</button><button class="ghost" id="segSend">send to table</button></div>
      <p class="hint">hover a row to find its box · click to lift the tracked cut-out over the video</p>
      <div class="seglist">${rows}</div></div>`;
  },
  toggleSegs() {
    this.showSegs = !this.showSegs; this.segLayer();
    const b = $('#segT', this.root); if (b) { b.textContent = `segments: ${this.showSegs ? 'on' : 'off'} (S)`; b.classList.toggle('on', this.showSegs); }
  },
  hl(k) { this.hlk = k; $$('.segbox', this.root).forEach(b => b.classList.toggle('hl', +b.dataset.k === k)); },
  /** (re)build the per-object box + lift elements over the frame */
  segLayer() {
    const layer = $('#insSegs', this.root), g = this.segs();
    layer.innerHTML = ''; this.segEls = [];
    if (!g || !this.showSegs) return;
    g.objects.forEach((o, i) => {
      const box = el('div', 'segbox' + (o.role === 'reading' ? ' reading' : ''), o.role === 'reading' || o.desc ? `<span>${esc(o.role === 'reading' ? o.desc : (o.desc || o.label))}</span>` : '');
      box.dataset.k = o.k; box.style.setProperty('--sc', segColor(o, i));
      let lift = null;
      if (this.lift.has(o.k) && o.sprite && o.union) {
        lift = el('div', 'seglift');
        const [x, y, w, h] = o.union;
        Object.assign(lift.style, { left: x * 100 + '%', top: y * 100 + '%', width: w * 100 + '%', height: h * 100 + '%',
          backgroundImage: `url("${o.sprite}")`, backgroundSize: `${g.frames * 100}% 100%` });
        layer.appendChild(lift);
      }
      layer.appendChild(box);
      this.segEls.push({ o, box, lift });
    });
    this.hl(this.hlk);
    this.segPaint(true);
  },
  segPaint(force) {
    const g = this.segs(); if (!g || !this.segEls || !this.segEls.length) return;
    const t = this.v.currentTime || 0, f = Math.floor((t - g.t0) * g.fps + 1e-6);
    if (!force && f === this._segF) return; this._segF = f;
    const inWin = f >= 0 && f < g.frames;
    for (const { o, box, lift } of this.segEls) {
      const b = inWin && o.boxes ? o.boxes[f] : null;
      if (!b) { box.style.display = 'none'; if (lift) lift.style.display = 'none'; continue; }
      box.style.display = ''; box.style.left = b[0] * 100 + '%'; box.style.top = b[1] * 100 + '%'; box.style.width = b[2] * 100 + '%'; box.style.height = b[3] * 100 + '%';
      if (lift) { lift.style.display = ''; lift.style.backgroundPosition = `${g.frames > 1 ? f / (g.frames - 1) * 100 : 0}% 0`; }
    }
  },
  toggleCuts() {
    this.showCuts = !this.showCuts;
    if (this.showCuts) { this.v.pause(); this.v.currentTime = readT(this.s); }
    this.cutLayer(); const b = $('#insCutT', this.root); if (b) b.textContent = `${this.showCuts ? 'hide' : 'show'} on frame (C)`; },
  cutLayer() {
    const layer = $('#insCuts', this.root), s = this.s;
    layer.innerHTML = ''; layer.classList.toggle('on', this.showCuts);
    if (!this.showCuts || !s.cutouts || !s.cutouts.length) return;
    s.cutouts.forEach(c => this.cutPiece(layer, c));
  },
  cutPiece(layer, c, off) {
    const [x, y, w, h] = c.bbox || [0, 0, 1, 1];
    const p = el('div', 'cutp'); p.innerHTML = `<img src="${esc(c.png)}" alt="${esc(c.label)}" draggable="false"><span>${esc(c.label)}</span>`;
    let px = x * 100 + (off || 0), py = y * 100;
    const put = () => { p.style.left = px + '%'; p.style.top = py + '%'; };
    p.style.width = w * 100 + '%'; p.style.height = h * 100 + '%'; put();
    p.addEventListener('pointerdown', e => {
      e.preventDefault(); e.stopPropagation();
      if (e.shiftKey) { this.cutPiece(layer, { ...c, bbox: [px / 100, py / 100, w, h] }, 4); }
      const r = layer.getBoundingClientRect(), ox = e.clientX, oy = e.clientY, sx = px, sy = py;
      const mv = ev => { px = sx + (ev.clientX - ox) / r.width * 100; py = sy + (ev.clientY - oy) / r.height * 100; put(); };
      const up = () => { removeEventListener('pointermove', mv); removeEventListener('pointerup', up); };
      addEventListener('pointermove', mv); addEventListener('pointerup', up);
    });
    layer.appendChild(p);
  },
  async save() {
    const s = this.s, R = this.root, out = $('#insSaved', R);
    const n = $('#insSign', R).value, note = $('#insNote', R).value.trim();
    const body = { id: s.id, n, note, a: this.A != null ? +this.A.toFixed(3) : null, b: this.B != null ? +this.B.toFixed(3) : null };
    if (s._live && s._raw) body.clip = s._raw;
    out.textContent = 'saving…'; out.className = '';
    if (!L.server) {
      const row = { ...body, ts: new Date().toISOString().slice(0, 19) };
      if (!Store.add(row)) { out.textContent = 'not saved — this browser blocks local storage'; out.className = 'err'; return; }
      L.assignments.push(row); out.textContent = `saved in this browser · ${L.S[n].symbol} — export from “your sub-shots”`; out.className = 'ok';
      this.side(); return;
    }
    try {
      const r = await fetch('/api/assign', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error || 'HTTP ' + r.status);
      L.assignments.push(j); out.textContent = `saved · ${L.S[n].symbol}${body.a != null ? ` ${body.a}–${body.b ?? '…'}s` : ''}`; out.className = 'ok';
      this.side();
    } catch (e) { out.textContent = 'not saved — ' + e.message + ' (is server.py running?)'; out.className = 'err'; }
  },
  key(e) {
    const k = e.key;
    if (k === 'Escape') this.close();
    else if (k === ' ') { e.preventDefault(); this.act('play'); }
    else if (k === ',') this.stepF(-1);
    else if (k === '.') this.stepF(1);
    else if (k === 'a' || k === 'A') this.act('A');
    else if (k === 'b' || k === 'B') this.act('B');
    else if (k === 'm' || k === 'M') this.act('M');
    else if (k === 'r' || k === 'R') this.act('R');
    else if (k === 'l' || k === 'L') this.act('loop');
    else if (k === '[') this.act('jA');
    else if (k === ']') this.act('jB');
    else if (k === 's' || k === 'S') { if (this.segs()) this.toggleSegs(); }
    else if (k === 'c' || k === 'C') { if (this.s.cutouts && this.s.cutouts.length) this.toggleCuts(); }
    else if (k === 'ArrowUp') { e.preventDefault(); this.nav(-1); }
    else if (k === 'ArrowDown') { e.preventDefault(); this.nav(1); }
    else if (k === 'ArrowLeft') { e.preventDefault(); this.stepF(e.shiftKey ? -FPS : -1); }
    else if (k === 'ArrowRight') { e.preventDefault(); this.stepF(e.shiftKey ? FPS : 1); }
    else if (k === '0') this.setSpeed(0);
    else if (k === '1') this.setSpeed(1);
    else if (k === '2') this.setSpeed(2);
    else if (k === '9') this.setSpeed(0.5);
    else if (k === '8') this.setSpeed(0.25);
    else return false;
    return true;
  },
};

/* ---- inspector helpers: WYGWYL block, affinity table, segment colours, animated sprites */
function wygBlock(s) {
  const w = s.wygwyl; if (!w) return '';
  const B = (L.wyg && L.wyg.beats) || [], byId = id => B.find(b => String(b.id) === String(id));
  const beats = (w.beats || []).map(id => { const b = byId(id); return `<button class="ghost wy-go" data-beat="${esc(String(id))}" title="${b ? esc(b.title) : ''}">#${esc(String(id))}${b ? ' · ' + esc(b.title) : ''}</button>`; }).join('');
  const ch = w.chosen != null ? byId(w.chosen) : null;
  return `<div class="sd-block wyblock"><h4>WYGWYL <small>Forage Suite review</small></h4>
    <div class="kv"><span>grade</span><b><span class="gr g-${esc(w.grade || 'U')}">${esc(w.grade || 'U')}</span> ${w.grade === 'U' || !w.grade ? 'unreviewed' : 'reviewed'}</b></div>
    ${w.chosen != null ? `<p class="wy-chosen">chosen for beat <button class="ghost wy-go" data-beat="${esc(String(w.chosen))}">#${esc(String(w.chosen))}${ch ? ' · ' + esc(ch.title) : ''}</button></p>` : ''}
    ${w.observed ? `<h5>observed</h5><p class="wy-p">${esc(w.observed)}</p>` : ''}
    ${w.use ? `<h5>use</h5><p class="wy-p">${esc(w.use)}</p>` : ''}
    ${beats ? `<h5>candidate for</h5><div class="wy-beatlinks">${beats}</div>` : ''}
    ${(w.queries || []).filter(Boolean).length ? `<p class="hint">foraged with: ${w.queries.filter(Boolean).slice(0, 4).map(q => '“' + esc(q) + '”').join(' · ')}</p>` : ''}</div>`;
}
const SEGC = ['#ffd166', '#7fd1ff', '#9ef01a', '#f78cff', '#5ef2c9', '#ffa94d', '#c3b5ff'];
function segColor(o, i) { return o.role === 'reading' ? '#ffffff' : SEGC[i % SEGC.length]; }
function affinityBlock(s) {
  const A = s.affinity || null, mx = s._affMax || 1, mn = A ? Math.min(...Object.values(A)) : 0;
  const read = new Map((s.signs || []).map(e => [String(e.n), e]));
  const alts = new Set((s.signs || []).map(e => e.alt != null ? String(e.alt) : null).filter(Boolean));
  const found = new Set(s._found);
  const cells = L.signs.map(sg => {
    const n = sg.n, a = A ? (A[n] ?? 0) : 0, r = read.get(n);
    const op = A ? 0.04 + 0.96 * Math.pow(clamp((a - mn) / Math.max(1e-6, mx - mn), 0, 1), 1.4) : 0;
    const cls = ['ac', r ? 'rd' : '', alts.has(n) && !r ? 'alt' : '', op > .55 ? 'lit' : ''].join(' ');
    return `<button class="${cls}" data-n="${esc(n)}" style="grid-column:${sg.col + 1};grid-row:${sg.dom === 'read' ? '1 / span 3' : sg.row + 1};--c:${DOMC[sg.dom]};--op:${op.toFixed(3)}" aria-label="${esc(sg.name)} ${a.toFixed(1)}%">
      <i></i><span>${esc(sg.symbol)}</span>${r && r.conf != null ? `<em>${r.conf}</em>` : ''}${found.has(n) ? '<u></u>' : ''}</button>`;
  }).join('');
  const top = (s.aff_top || []).slice(0, 3).map(([n, v], i) => { const sg = L.S[String(n)]; if (!sg) return ''; return `
    <div class="sug"><div class="sug-h"><span class="sug-i">${i + 1}</span>${chip(sg.n)}<b>${esc(sg.name)}</b><em>${(+v).toFixed(1)}%</em></div>
      <p>${esc(sg.difference || sg.gloss || '')}</p></div>`; }).join('');
  const def = A ? `hover a sign for its affinity · click to filter the wall · ⌥-click sends its family to CUT` : 'affinity not computed for this shot';
  return `<div class="sd-block affblock"><h4>the 45 signs</h4>
    <div class="aff">${cells}</div>
    <div class="aff-key"><span><i class="k-rd"></i>editor’s reading + conf %</span><span><i class="k-alt"></i>rival</span><span><i class="k-dot"></i>found by its search</span><span><i class="k-heat"></i>machine affinity</span></div>
    <div class="aff-read">${def}</div>
    ${top ? `<h5>machine suggestions</h5>${top}` : ''}
    <p class="honest">Machine affinity (CLIP vs sign descriptions + exemplars) — a pointer, not a reading.</p></div>`;
}
function affReadout(s, n) {
  const sg = L.S[n], a = s.affinity ? s.affinity[n] ?? 0 : null;
  const rank = s.affinity ? Object.values(s.affinity).filter(v => v > a).length + 1 : null;
  const r = (s.signs || []).find(e => String(e.n) === n);
  const alt = (s.signs || []).find(e => String(e.alt) === n);
  return `${chip(n)} <b>${esc(sg.name)}</b> · ${a != null ? `affinity <b>${a.toFixed(1)}%</b> (rank ${rank}/45)` : 'no affinity'}` +
    (r ? ` · editor <b>${r.conf ?? '—'}%</b>` : '') + (alt ? ` · rival ${alt.alt_conf ?? ''}%` : '') + (s._found.includes(n) ? ' · found by its search' : '');
}
function cutSprite(c) { return sprHTML({ sprite: c.sprite, sw: c.sw, sh: c.sh, boxes: c.boxes, png: c.png }, { frames: c.frames, fps: c.fps }); }
/** sprite cell HTML for a tracked object (animated by Sprites) */
function sprHTML(o, g) {
  if (!o.sprite) return `<span class="spr still"><img src="${esc(o.png)}" alt=""></span>`;
  const cells = (o.boxes || []).map((b, i) => b ? i : -1).filter(i => i >= 0).join(',');
  return `<span class="spr" data-n="${g.frames}" data-fps="${g.fps}" data-cells="${cells}" style="aspect-ratio:${o.sw || 4}/${o.sh || 3};background-image:url('${esc(o.sprite)}');background-size:${g.frames * 100}% 100%"></span>`;
}
/** one clock for every animated sprite (inspector list, cut-outs tray + table) */
const Sprites = {
  set: new Set(), raf: 0,
  add(e) {
    e._n = +e.dataset.n || 1; e._fps = +e.dataset.fps || 6;
    e._cells = (e.dataset.cells || '').split(',').filter(x => x !== '').map(Number); if (!e._cells.length) e._cells = [0];
    this.set.add(e); if (!this.raf) this.raf = requestAnimationFrame(t => this.tick(t));
  },
  prune() { for (const e of this.set) if (!e.isConnected) this.set.delete(e); },
  tick(t) {
    let live = 0;
    for (const e of this.set) {
      if (!e.isConnected) { this.set.delete(e); continue; }
      live++;
      const i = e._cells[Math.floor(t / 1000 * e._fps) % e._cells.length];
      if (i !== e._i) { e._i = i; e.style.backgroundPosition = `${e._n > 1 ? i / (e._n - 1) * 100 : 0}% 0`; }
    }
    this.raf = live || this.set.size ? requestAnimationFrame(tt => this.tick(tt)) : 0;
  },
};

/* ================================================================ LIVE (archive search through server.py) */
const Live = {
  busy: false,
  async search(q) {
    q = q.trim(); if (!q || this.busy) return;
    this.busy = true; Shell.qstat('searching the archive…');
    try {
      if (!L.server) { Shell.qstat(STATIC_NOTE, 'warn'); return; }
      const r = await fetch('/api/search', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ query: q }) });
      const j = await r.json().catch(() => ({}));
      if (r.status === 429) { Shell.qstat('the archive asks us to wait — try again in a few seconds', 'warn'); return; }
      if (!r.ok) { Shell.qstat((j.error || 'search failed ' + r.status), 'warn'); return; }
      const clips = j.clips || j.results || [];
      L.live.forEach(s => { if (!s._liveOnly) s._live = false; });
      L.shots.forEach(s => { s._liveHit = false; });
      let hits = 0;
      L.live = clips.map((c, i) => {
        const known = L.byId.get(c.id);
        if (known) { known._liveHit = true; hits++; return known; }
        const s = fromClip(c); prep(s, 1e6 + i); s._live = true; s._liveOnly = true; return s;
      });
      L.live.forEach(s => { s._live = true; });
      L.liveQ = q; L.showLive = true;
      Shell.qstat(`${clips.length} live · ${hits} already in corpus`);
      refresh();
    } catch (e) {
      Shell.qstat(STATIC_NOTE, 'warn');
    } finally { this.busy = false; }
  },
  clear() {
    L.live.forEach(s => { if (!s._liveOnly) s._live = false; s._liveHit = false; });
    L.live = []; L.liveQ = ''; refresh();
  },
};
function fromClip(c) {
  const year = c.sourceYear ?? null;
  return {
    id: c.id, title: c.sourceTitle || 'untitled', year, decade: year ? Math.floor(year / 10) * 10 : null,
    slug: c.sourceSlug, page: `${ARCHIVE}/sources/${c.sourceSlug}?clip=${c.id}`, video: c.videoUrl, clip: null, thumb: c.thumbnailUrl,
    start: c.startSeconds ?? 0, end: c.endSeconds ?? ((c.startSeconds ?? 0) + 5), match: c.matchTimestampSeconds ?? c.startSeconds ?? 0,
    bw: c.colorMode === 'black_and_white', palette: null, hue: null, lum: null, sat: null, subjects: null, scale: null, xy: null, sim: null,
    signs: [], found: [], strip: null, frames: null, cutouts: [], audio: null, _raw: c,
  };
}

/* ================================================================ SEND (lab → editors, contract: tools/bridge.js) */
const TOOLS = {
  cut: { url: 'tools/cut.html', win: 'cineosis-cut', name: 'CUT' },
  room: { url: 'tools/hand-butter.html', win: 'cineosis-room', name: 'the Cutting Room' },
};
const LAYOUTS = ['sequence', 'grid', 'cascade', 'split'];
const BUS = 'BroadcastChannel' in window ? new BroadcastChannel('cineosis') : null;
const Send = {
  /** default in/out for a shot: a window round the read frame for read shots, the whole clip otherwise */
  win(s) {
    if (s.read_t == null || !s._read.length) return [null, null];
    return [+Math.max(0, s.read_t - 1.5).toFixed(3), +Math.min(s._dur, s.read_t + 2.5).toFixed(3)];
  },
  media(s) {
    if (L.server) return new URL('/media/' + s.id + '.mp4', location).href;
    return s.clip ? new URL(s.clip, location).href : null;
  },
  /** one bin item, or null when the media can't be served same-origin (static site, unread shot) */
  item(s, n, a, b, place, note) {
    const media = this.media(s); if (!media) return null;
    n = n || s._read[0] || null;
    const e = n ? entryOf(s, n) : null, sg = n ? L.S[n] : null;
    if (a === undefined) [a, b] = this.win(s);
    const it = { shot: s.id, title: s.title, year: s.year ?? null, n, symbol: sg ? sg.symbol : null, note: note || (e ? e.note : ''), a: a ?? null, b: b ?? null, media };
    if (place) it.place = place;
    return it;
  },
  /** entries: [{s, n?, a?, b?, place?, note?}] */
  go(tool, title, layout, entries) {
    const T = TOOLS[tool];
    if (tool === 'room' && !L.server) { toast('the Cutting Room is local-only — run python3 lab/server.py'); return; }
    const items = [], total = entries.length;
    for (const x of entries) { const it = this.item(x.s, x.n, x.a, x.b, x.place, x.note); if (it) items.push(it); }
    const skipped = total - items.length;
    if (!items.length) { toast(skipped ? `nothing to send: none of these ${skipped} shots has a clip on this static site` : 'nothing to send'); return; }
    const bin = { id: 'lab-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7), title, layout: tool === 'room' ? 'sequence' : (layout || 'sequence'), items };
    try { localStorage.setItem('cineosis.bin', JSON.stringify(bin)); } catch (e) { /* storage blocked: the channel still carries it */ }
    const w = window.open(T.url, T.win);
    if (BUS) BUS.postMessage({ type: 'bin', bin });
    toast(`${items.length} shot${items.length > 1 ? 's' : ''} → ${T.name} · ${bin.layout}${skipped ? ` · ${skipped} skipped (no clip on the static site)` : ''}${w ? '' : ' · allow pop-ups for this page'}`, 4200);
  },
  /** a sign's read shots, best conf first, with read windows */
  family(n) {
    return L.shots.filter(s => s._read.includes(n))
      .sort((a, b) => ((entryOf(b, n) || {}).conf || 0) - ((entryOf(a, n) || {}).conf || 0)).map(s => ({ s, n }));
  },
  sendFamily(n, tool = 'cut') {
    const sg = L.S[n], fam = this.family(n);
    if (!fam.length) { toast(`${sg.symbol} has no read shots yet`); return; }
    this.go(tool, `${sg.symbol} · ${sg.name} — the family`, 'sequence', fam);
  },
  sendView(tool, layout) {
    const list = viewList(), ent = list.slice(0, 24).map(s => ({ s, n: signOf(s) }));
    if (!ent.length) { toast('the view is empty'); return; }
    if (list.length > 24) toast(`sending the first 24 of ${fmt(list.length)} shots in the view`, 3000);
    this.go(tool, `view · ${fmt(list.length)} shots${F.signs.size ? ' · ' + [...F.signs].map(n => L.S[n].symbol).join(' ') : ''}`, layout, ent);
  },
};
function sendButtons(extra = '') {
  return `<button class="ghost send" data-send="cut" title="send to CUT — the frame, depth as time">→ CUT</button>` +
    (L.server ? `<button class="ghost send" data-send="room" title="send to the WAG Cutting Room (local only)">→ Cutting Room</button>` : '') + extra;
}

/* ================================================================ MONTAGE (recipes for relational signs + saved edits) */
const RECIPES = [
  { id: 'markdemark', title: 'Mark → Demark', signs: ['31', '32'], layout: 'sequence', why: 'a series, then the term that breaks it',
    build: () => [...Send.family('31').slice(0, 3), ...Send.family('32').slice(0, 1)] },
  { id: 'peaks', title: 'Peaks of the present', signs: ['38'], layout: 'grid', why: 'several presents, simultaneously valid',
    build: () => Send.family('38').slice(0, 4) },
  { id: 'sheets', title: 'Sheets of the past', signs: ['39'], layout: 'cascade', why: 'layers of the past coexisting',
    build: () => Send.family('39') },
  { id: 'forking', title: 'Forking paths', signs: ['30'], layout: 'split', why: 'incompatible pasts, both running — two at a time, side by side',
    build: () => Send.family('30') },
  { id: 'binomial', title: 'Binomial', signs: ['14'], layout: 'split', why: 'two sides of a duel',
    build: () => Send.family('14').slice(0, 2) },
  { id: 'destiny', title: 'Strong destiny → what it determines', signs: ['28'], layout: 'sequence', why: 'a destiny, then the shot it determines (next in your current selection — swap it for your pick)',
    build: () => { const d = Send.family('28').slice(0, 1); const nx = viewList().find(s => !s._read.includes('28')); return nx ? [...d, { s: nx, n: signOf(nx) }] : d; } },
  { id: 'any', title: 'Any sign, any layout', signs: [], layout: 'sequence', why: 'pick a sign (its family) or take the current selection', any: true,
    build: () => Montage.anySrc === 'view' ? viewList().slice(0, 24).map(s => ({ s, n: signOf(s) })) : Send.family(Montage.anySign) },
  { id: 'wychapter', title: 'WYGWYL chapter', signs: [], layout: 'sequence', wyg: true, why: 'a chapter of the Forage Suite: its beats’ A clips in cut order, trimmed as the cut trims them',
    build: () => Wyg.beats().filter(b => b.chapter === Montage.wyCh && b.a && L.byId.get(b.a.id)).map(b => {
      const len = (b.end - b.start) * (b.rate || 1), a = +(b.trim || 0);
      return { s: L.byId.get(b.a.id), n: b.codes && b.codes[0] != null ? String(b.codes[0]) : null, a, b: +(a + len).toFixed(3), note: `#${b.id} ${b.title}` };
    }) },
  { id: 'wycands', title: 'WYGWYL beat’s candidates', signs: [], layout: 'grid', wyg: true, why: 'every shot the forage found for one beat, reviewed first — to choose between them in the frame',
    build: () => { const b = Wyg.beats().find(x => String(x.id) === String(Montage.wyBeat)); return b ? Wyg.candidates(b).slice(0, 24).map(s => ({ s, n: signOf(s) })) : []; } },
];
const Montage = {
  host: null, state: {}, edits: [], anySign: '32', anySrc: 'sign', wyCh: 0, wyBeat: null,
  mount(host) {
    if (this.host) return;
    this.host = host;
    host.innerHTML = `<div class="mont">
      <section class="mont-col"><div class="mont-h"><h2>Montage recipes</h2><p>Some signs are relations between shots — a series and its break, presents side by side, pasts that fork. One shot can’t carry them; a cut can. Each recipe builds a bin for the editors: check the shots, drag to reorder, × to drop, ⇄ to swap in the next shot from your current view.</p></div>
        <div id="recipes"></div></section>
      <section class="mont-col"><div class="mont-h"><h2>Edits</h2><p>Montages saved back from CUT or the Cutting Room (“↩ lab”). They are the corpus’s new material: sequences where relational signs can actually happen. <span id="editsSrc"></span></p>
        <div class="cutbtns"><button class="ghost" id="editsRefresh">refresh</button></div></div>
        <div id="edits"></div></section></div>`;
    $('#editsRefresh', host).onclick = () => this.loadEdits();
    $('#recipes', host).addEventListener('click', e => this.onRecipe(e));
    $('#recipes', host).addEventListener('change', e => {
      const card = e.target.closest('.rc-card'); if (!card) return; const id = card.dataset.id;
      if (e.target.matches('.rc-layout')) this.state[id].layout = e.target.value;
      if (e.target.matches('.rc-sign')) { this.anySign = e.target.value; this.anySrc = 'sign'; this.reset(id); }
      if (e.target.matches('.rc-src')) { this.anySrc = e.target.value; this.reset(id); }
      if (e.target.matches('.rc-wych')) { this.wyCh = +e.target.value; this.reset(id); }
      if (e.target.matches('.rc-wybeat')) { this.wyBeat = e.target.value; this.reset(id); }
    });
    // drag to reorder thumbnails inside a recipe
    let drag = null;
    $('#recipes', host).addEventListener('dragstart', e => { const t = e.target.closest('.rt'); if (!t) return; drag = t; e.dataTransfer.effectAllowed = 'move'; try { e.dataTransfer.setData('text/plain', t.dataset.i); } catch (er) { /* ignore */ } });
    $('#recipes', host).addEventListener('dragover', e => { if (drag && e.target.closest('.rthumbs') === drag.parentNode) e.preventDefault(); });
    $('#recipes', host).addEventListener('drop', e => {
      const t = e.target.closest('.rt'); if (!drag || !t || t.parentNode !== drag.parentNode) return; e.preventDefault();
      const id = t.closest('.rc-card').dataset.id, L2 = this.state[id].list, from = +drag.dataset.i, to = +t.dataset.i;
      const [x] = L2.splice(from, 1); L2.splice(to, 0, x); drag = null; this.renderRecipe(id);
    });
    $('#recipes', host).addEventListener('dragend', () => { drag = null; });
    $('#edits', host).addEventListener('click', e => this.onEdit(e));
    if (BUS) BUS.addEventListener('message', e => { if (e.data && e.data.type === 'edit') { this.loadEdits(); toast('a montage came back from the editor'); } });
  },
  show() { this.renderRecipes(); this.loadEdits(); },
  update() { /* recipes keep their picks; the view only feeds ⇄ and “current selection” */ },
  reset(id) { const r = RECIPES.find(x => x.id === id); this.state[id] = { list: r.build(), layout: this.state[id] ? this.state[id].layout : r.layout }; this.renderRecipe(id); },
  renderRecipes() {
    const box = $('#recipes', this.host);
    const list = RECIPES.filter(r => !r.wyg || (L.wyg && Wyg.beats().length));
    if (this.wyBeat == null && Wyg.beats().length) this.wyBeat = String(Wyg.beats()[0].id);
    box.innerHTML = list.map(r => `<div class="rc-card" data-id="${r.id}"></div>`).join('');
    list.forEach(r => { if (!this.state[r.id]) this.state[r.id] = { list: r.build(), layout: r.layout }; this.renderRecipe(r.id); });
  },
  renderRecipe(id) {
    const r = RECIPES.find(x => x.id === id), st = this.state[id], card = $(`.rc-card[data-id="${id}"]`, this.host); if (!card) return;
    const signs = r.any ? (this.anySrc === 'sign' ? [this.anySign] : []) : r.signs;
    const thumbs = st.list.map((x, i) => `<div class="rt" draggable="true" data-i="${i}" title="${esc(x.s.title)} · ${x.s.year ?? '—'}">
        <img src="${esc(x.s.thumb)}" alt="" draggable="false" onerror="this.style.visibility='hidden'">${x.n && L.S[x.n] ? chip(x.n, 'sm') : ''}
        <button class="rt-x" data-act="drop" data-i="${i}" title="drop">×</button><button class="rt-s" data-act="swap" data-i="${i}" title="swap for the next shot in your view">⇄</button></div>`).join('');
    const anyCtl = r.any ? `<div class="rc-any"><select class="rc-src"><option value="sign"${this.anySrc === 'sign' ? ' selected' : ''}>a sign’s family</option><option value="view"${this.anySrc === 'view' ? ' selected' : ''}>current selection (24)</option></select>
        <select class="rc-sign"${this.anySrc === 'view' ? ' disabled' : ''}>${L.signs.map(s => `<option value="${s.n}"${s.n === this.anySign ? ' selected' : ''}>${esc(s.symbol)} · ${esc(s.name)}</option>`).join('')}</select></div>` : '';
    const wyCtl = r.id === 'wychapter' ? `<div class="rc-any"><select class="rc-wych">${Wyg.films().map((f, i) => `<option value="${i}"${i === this.wyCh ? ' selected' : ''}>${esc(f.n)} · ${esc(f.title)}</option>`).join('')}</select></div>`
      : r.id === 'wycands' ? `<div class="rc-any"><select class="rc-wybeat">${Wyg.beats().map(b => `<option value="${esc(String(b.id))}"${String(b.id) === String(this.wyBeat) ? ' selected' : ''}>#${esc(String(b.id))} · ${esc(b.title)}</option>`).join('')}</select></div>` : '';
    card.innerHTML = `<div class="rc-h">${r.wyg ? '<span class="colbadge">WYGWYL</span>' : ''}${signs.map(n => chip(n)).join('<span class="arr">→</span>')}<b>${esc(r.title)}</b></div>
      <p class="rc-why">${esc(r.why)}</p>${anyCtl}${wyCtl}
      <div class="rthumbs">${thumbs || '<span class="pending">no read shots for this recipe yet</span>'}</div>
      <div class="rc-foot"><label>layout <select class="rc-layout">${LAYOUTS.map(l => `<option${l === st.layout ? ' selected' : ''}>${l}</option>`).join('')}</select></label>
        <button class="ghost" data-act="add" title="add the next shot from your current view">+ from view</button><button class="ghost" data-act="reset">reset</button>
        <button class="ghost" data-act="play" title="play it here, in the reel">play here</button>${sendButtons()}</div>`;
  },
  onRecipe(e) {
    const b = e.target.closest('button'); if (!b) return;
    const card = b.closest('.rc-card'), id = card.dataset.id, r = RECIPES.find(x => x.id === id), st = this.state[id];
    const nextFromView = () => { const used = new Set(st.list.map(x => x.s.id)); const s = viewList().find(v => !used.has(v.id)); return s ? { s, n: signOf(s) } : null; };
    const act = b.dataset.act, i = +b.dataset.i;
    if (act === 'drop') st.list.splice(i, 1);
    else if (act === 'swap') { const nx = nextFromView(); if (nx) st.list[i] = nx; else toast('no unused shot in the current view'); }
    else if (act === 'add') { const nx = nextFromView(); if (nx) st.list.push(nx); else toast('no unused shot in the current view'); }
    else if (act === 'reset') return this.reset(id);
    else if (act === 'play') return this.play(r.title, r.why, st.list.map(x => { const [a, bb] = x.a !== undefined ? [x.a, x.b] : Send.win(x.s); return { s: x.s, n: x.n, a, b: bb, note: x.note }; }));
    else if (b.dataset.send) return Send.go(b.dataset.send, `${r.title}${r.any && this.anySrc === 'sign' ? ' · ' + L.S[this.anySign].name : ''}`, st.layout, st.list);
    else return;
    this.renderRecipe(id);
  },
  /** play a list of {s,n,a,b,note} in the reel */
  play(title, why, list) {
    const Q = [{ type: 'card', n: null, title, sub: `${list.length} clips`, why }];
    for (const x of list) { if (!x.s) continue; const n = x.n && L.S[x.n] ? x.n : null; Q.push({ type: 'shot', s: x.s, n, e: n ? entryOf(x.s, n) : null, a: x.a, b: x.b, note: x.note }); }
    if (Q.length < 2) { toast('none of these clips are in the corpus'); return; }
    Reel.custom = Q;
    if (Shell.mode === 'reel') Reel.start(); else Shell.setMode('reel');
  },
  async loadEdits() {
    let rows = [];
    if (L.server) {
      try { const r = await fetch('/api/edits', { cache: 'no-store' }); if (r.ok) rows = await r.json(); } catch (e) { rows = []; }
    } else { try { rows = JSON.parse(localStorage.getItem('cineosis.edits') || '[]'); } catch (e) { rows = []; } }
    this.edits = (Array.isArray(rows) ? rows : []).slice().sort((a, b) => String(b.ts || '').localeCompare(String(a.ts || '')));
    if (this.host) this.renderEdits();
  },
  renderEdits() {
    $('#editsSrc', this.host).textContent = L.server ? 'Listed from lab/edits/ on the local server.' : 'Static site: listed from this browser (the editors keep them here and download a JSON).';
    const box = $('#edits', this.host);
    if (!this.edits.length) { box.innerHTML = `<div class="empty"><b>No montages yet.</b><p>Send a recipe to CUT, cut it, and press “↩ lab” in the editor. It will appear here.</p></div>`; return; }
    box.innerHTML = this.edits.map((ed, i) => {
      const clips = ed.clips || [], signs = [...new Set((ed.signs && ed.signs.length ? ed.signs : clips.map(c => c.n)).filter(Boolean).map(String))];
      const strip = clips.slice(0, 16).map(c => { const s = c.shot && L.byId.get(c.shot); return s ? `<img src="${esc(s.thumb)}" alt="" title="${esc(s.title)}" onerror="this.style.visibility='hidden'">` : '<i></i>'; }).join('');
      return `<div class="ed" data-i="${i}"><div class="ed-h"><b>${esc(ed.title || 'untitled montage')}</b><span>${esc(ed.tool || 'edit')} · ${esc(String(ed.ts || '').replace('T', ' '))} · ${clips.length} clip${clips.length === 1 ? '' : 's'}</span></div>
        <div class="ed-signs">${signs.map(n => chip(n)).join('')}</div>
        <div class="ed-strip">${strip}</div>
        <div class="cutbtns"><button class="ghost" data-act="play">play here</button><button class="ghost" data-act="cut">reopen in CUT</button><button class="ghost" data-act="json">export JSON</button></div></div>`;
    }).join('');
  },
  onEdit(e) {
    const b = e.target.closest('button[data-act]'); if (!b) return;
    const ed = this.edits[+b.closest('.ed').dataset.i]; if (!ed) return;
    const clips = (ed.clips || []).slice().sort((a, c) => (a.t || 0) - (c.t || 0));
    const known = clips.filter(c => c.shot && L.byId.get(c.shot));
    if (b.dataset.act === 'json') {
      const url = URL.createObjectURL(new Blob([JSON.stringify(ed, null, 1)], { type: 'application/json' }));
      const a = document.createElement('a'); a.href = url; a.download = `montage-${(ed.title || 'untitled').replace(/[^\w-]+/g, '-').slice(0, 40)}.json`;
      document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 5000); return;
    }
    if (!known.length) { toast('none of this montage’s clips are corpus shots'); return; }
    const miss = clips.length - known.length;
    if (b.dataset.act === 'play') {
      this.play(ed.title || 'montage', `${ed.tool || 'edit'}${miss ? ` · ${miss} clip(s) not in the corpus skipped` : ''}`,
        known.map(c => ({ s: L.byId.get(c.shot), n: c.n != null ? String(c.n) : null, a: c.in, b: c.out, note: c.note })));
    } else if (b.dataset.act === 'cut') {
      Send.go('cut', ed.title || 'reopened montage', 'sequence', known.map(c => ({ s: L.byId.get(c.shot), n: c.n != null ? String(c.n) : null, a: c.in ?? null, b: c.out ?? null, note: c.note,
        place: c.x != null && c.w != null ? { t: c.t || 0, x: c.x, y: c.y, w: c.w, h: c.h } : { t: c.t || 0, x: 0, y: 0, w: 1, h: 1 } })));
    }
  },
};

/* ================================================================ WYGWYL (the Forage Suite cut as an inspectable archive) */
function setVT(v, t) {
  if (v.readyState >= 1) { try { v.currentTime = t; } catch (e) { /* ignore */ } return; }
  v._wantT = t;
  if (!v._wantL) { v._wantL = true; v.addEventListener('loadedmetadata', () => { v._wantL = false; try { v.currentTime = v._wantT; } catch (e) { /* ignore */ } }, { once: true }); }
}
/** is there a pre-rendered wygwyl/cuts/grid.mp4? The local server lists the folder (no 404 noise); elsewhere ask with HEAD */
async function probeGrid() {
  const url = 'wygwyl/cuts/grid.mp4';
  try {
    if (L.server) { const r = await fetch('wygwyl/cuts/', { cache: 'no-store' }); return r.ok && /href="grid\.mp4"/.test(await r.text()) ? url : null; }
    const r = await fetch(url, { method: 'HEAD', cache: 'no-store' }); return r.ok ? url : null;
  } catch (e) { return null; }
}
const MODE_GLYPH = { hold: '▮', split: '◧', inset: '▣', dissolve: '◐', montage: '▦', black: '■' };
const GRADE_ORDER = g => g && g !== 'U' ? g.charCodeAt(0) : 999;
const Wyg = {
  host: null, cur: -1, playing: false, useFilm: false, raf: 0, cuts: [], ci: 0, patches: null, cutsLoaded: false,
  grid: false, gridFile: false, gridURL: null, gv: [], gcuts: [], focus: 0, syncT: 0,
  beats() { return (L.wyg && L.wyg.beats) || []; },
  films() { return (L.wyg && L.wyg.films) || []; },
  cut() { return this.cuts[this.ci] || null; },
  /** the ribbon's cells: the selected cut's patches when it has them, else the original cut's beats */
  cells() { return this.patches || this.beats(); },
  dur() { const c = this.cut(); return (c && c.duration) || (L.wyg && L.wyg.cut && L.wyg.cut.duration) || 1440; },
  mount(host) {
    if (this.host) return;
    this.host = host;
    host.innerHTML = `<div class="wyg">
      <div class="wy-top"><div class="wy-cuts" id="wyCuts"></div><div class="wy-ribbon" id="wyRibbon"><div class="wy-ph" id="wyPH"></div></div></div>
      <div class="wy-main">
        <div class="wy-stage">
          <div class="wy-view" id="wyView"><video id="wyFilm" playsinline preload="auto"></video>
            <div class="wy-grid" id="wyGrid" hidden>${[0, 1, 2, 3].map(i => `<div class="wg-cell" data-q="${i}"><video playsinline muted preload="auto"></video><span class="wg-l"></span></div>`).join('')}</div><div class="wy-mock" id="wyMock" hidden></div><div class="wy-fallback" id="wyFallback" hidden></div></div>
          <div class="wy-ctl">
            <button class="ghost" data-a="prev" title="previous (←)">⏮</button><button class="ghost big" data-a="play" title="play / pause (space)">▶</button><button class="ghost" data-a="next" title="next (→)">⏭</button>
            <span class="wy-tc" id="wyTC">00:00</span>
            <span class="wy-src" id="wySrc"></span>
            <span class="wy-links">
              <button class="ghost send" data-a="cut">open in CUT</button>
              <button class="ghost send" data-a="wag" id="wyWag">open in WAG</button>
              <a class="ghost" href="wygwyl/player.html" target="_blank" rel="noopener">original Forage player ↗</a>
              <button class="ghost" data-a="json">cut JSON</button>
              <a class="ghost" href="wygwyl/WYGWYL_Forage_Catalogue.json" download>catalogue JSON</a>
            </span>
          </div>
        </div>
        <aside class="wy-card" id="wyCard"></aside>
      </div>
      <audio id="wyAudio" preload="metadata"></audio></div>`;
    this.audio = $('#wyAudio', host); this.film = $('#wyFilm', host);
    $('.wy-ctl', host).addEventListener('click', e => { const b = e.target.closest('button[data-a]'); if (b) this.act(b.dataset.a); });
    $('#wyCuts', host).addEventListener('click', e => {
      if (e.target.closest('[data-grid]')) { this.toggleGrid(); return; }
      if (e.target.closest('[data-gridfile]')) { this.toggleGridFile(); return; }
      const b = e.target.closest('[data-ci]'); if (b) { if (this.grid) this.leaveGrid(+b.dataset.ci); else this.setCut(+b.dataset.ci); }
    });
    this.gv = $$('#wyGrid video', host);
    const G = $('#wyGrid', host);
    G.addEventListener('click', e => { const c = e.target.closest('.wg-cell'); if (c) this.setFocus(+c.dataset.q); });
    G.addEventListener('dblclick', e => { const c = e.target.closest('.wg-cell'); if (!c) return; const k = this.cuts.indexOf(this.gcuts[+c.dataset.q]); if (k >= 0) this.leaveGrid(k); });
    // the three followers mirror the master at once on play / pause / seek
    const M = this.gv[0];
    M.addEventListener('play', () => { if (this.grid && !this.gridFile) this.gv.slice(1).forEach(v => { if (v.getAttribute('src')) { v.currentTime = M.currentTime; v.play().catch(() => {}); } }); this.paintPlay(); });
    M.addEventListener('pause', () => { if (this.grid && !this.gridFile) this.gv.slice(1).forEach(v => v.pause()); this.paintPlay(); });
    M.addEventListener('seeking', () => { if (this.grid && !this.gridFile) this.gv.slice(1).forEach(v => { if (v.readyState >= 1) v.currentTime = M.currentTime; }); });
    this.syncT = setInterval(() => this.drift(), 500);
    const rib = $('#wyRibbon', host); let drag = false;
    const seekAt = e => { const r = rib.getBoundingClientRect(); this.seek(clamp((e.clientX - r.left) / r.width, 0, 1) * this.dur()); };
    rib.addEventListener('pointerdown', e => { rib.setPointerCapture(e.pointerId); drag = true; seekAt(e); });
    rib.addEventListener('pointermove', e => { if (drag) seekAt(e); else { const c = e.target.closest('.wy-beat'); if (c) Tip.text(this.cellLabel(this.cells()[+c.dataset.i]), e); else Tip.hide(); } });
    rib.addEventListener('pointerup', () => { drag = false; });
    rib.addEventListener('pointerleave', () => Tip.hide());
    $('#wyCard', host).addEventListener('click', e => this.onCard(e));
    for (const m of [this.audio, this.film]) { m.addEventListener('play', () => this.paintPlay()); m.addEventListener('pause', () => this.paintPlay()); }
    this.film.addEventListener('error', () => {
      if (this.grid && this.gridFile) { this.gridFile = false; toast('the rendered grid could not be loaded — back to the four synced videos'); this.enterGrid(this._pendingT || 0, this.playing); return; }
      if (!this.useFilm || !this.film.getAttribute('src')) return;
      const t = this._pendingT || 0; this.useFilm = false; this.film.removeAttribute('src');
      toast(`${this.cut() ? this.cut().title : 'this cut'}: the film could not be loaded — falling back to the stills mock-up`, 4000);
      this.applyMaster(t, this.playing);
    });
  },
  async show() {
    if (!L.wyg) { $('#wyCard', this.host).innerHTML = `<div class="empty"><b>WYGWYL isn’t in lab-data.json yet.</b><p>The Forage Suite collection is being merged into the lab data — press ↻ in a few minutes.</p></div>`; return; }
    $('#wyWag', this.host).hidden = !L.server;
    if (!this.cutsLoaded) await this.loadCuts();
    this.renderCuts();
    this.ribbon();
    if (this.cur < 0) this.select(0, false, true); else this.select(this.cur, false, true);
    this.loop();
  },
  hide() { this.pause(); cancelAnimationFrame(this.raf); this.raf = 0; Tip.hide(); },
  update() { /* the collection facet doesn't change the cut */ },
  /* ---- the cuts: the original forage render + whatever lab/wygwyl/cuts/index.json lists */
  async loadCuts() {
    const orig = L.wyg.cut || {};
    const list = [{ slug: 'forage', title: 'Forage cut (A/B compositions)', idea: 'The original forage: each of the 88 beats composed from its A and B shots (hold, split, inset, dissolve, montage).', film: orig.film || null, duration: orig.duration, patches: null }];
    try {
      const r = await fetch('wygwyl/cuts/index.json', { cache: 'no-store' });
      if (r.ok) {
        const j = await r.json(), arr = Array.isArray(j) ? j : (j.cuts || []);
        for (const c of arr) { if (!c || !c.slug || c.slug === 'forage') continue; if (c.slug === 'grid') { this.gridURL = c.film || null; continue; } list.push(c); }
        if (!Array.isArray(j) && j.grid) this.gridURL = typeof j.grid === 'string' ? j.grid : j.grid.film;
      }
    } catch (e) { /* no extra cuts yet */ }
    this.cuts = list; this.cutsLoaded = true;
    let slug = null; try { slug = localStorage.getItem('lab.wygwyl.cut'); } catch (e) { /* storage blocked */ }
    const i = Math.max(0, list.findIndex(c => c.slug === slug));
    await this.setCut(i, true);
    this.gcuts = list.filter(c => c.slug !== 'forage' && c.film).slice(0, 4);
    if (!this.gridURL && this.gcuts.length) this.gridURL = await probeGrid();
    let g = false; try { g = localStorage.getItem('lab.wygwyl.grid') === '1'; } catch (e) { /* storage blocked */ }
    if (g && this.gcuts.length > 1) await this.enterGrid(0, false);
  },
  renderCuts() {
    const box = $('#wyCuts', this.host);
    const gridBtn = this.gcuts.length > 1 ? `<button class="wy-cutb wy-gridb${this.grid ? ' on' : ''}" data-grid title="all ${this.gcuts.length} new cuts at once, in sync (G)">▦ grid</button>` +
      (this.grid && this.gridURL ? `<button class="wy-cutb${this.gridFile ? ' on' : ''}" data-gridfile title="play the pre-rendered grid.mp4 instead of four synced videos">rendered grid</button>` : '') : '';
    box.innerHTML = `<span class="wy-cuts-l">cut</span>` + this.cuts.map((c, i) => `<button class="wy-cutb${i === this.ci && !this.grid ? ' on' : ''}${this.grid && this.gcuts[this.focus] === c ? ' focus' : ''}" data-ci="${i}" title="${esc(c.idea || '')}">${esc(c.title || c.slug)}${c.film ? '' : ' <em>no film yet</em>'}</button>`).join('') + gridBtn +
      (this.grid ? `<span class="wy-idea">${this.gridFile ? 'the rendered grid (one file)' : `four cuts in sync — the focused quadrant (<b>${esc(this.cut().title)}</b>) is the one you hear and read; double-click a quadrant to open it alone`}</span>`
        : this.cut() && this.cut().idea ? `<span class="wy-idea">${esc(this.cut().idea)}</span>` : '') + `<span class="wy-keys">[ ] cut · G grid</span><a class="wy-cutb wy-page" href="./wygwyl.html" target="_blank" rel="noopener" title="Open the WYGWYL page in a new tab">Open WYGWYL page ↗</a>`;
  },
  async loadPatches(c) {
    if (!c || !c.patches) return null;
    if (c._patches !== undefined) return c._patches;
    try {
      const r = await fetch(c.patches, { cache: 'no-store' }); if (!r.ok) throw new Error(r.status);
      const j = await r.json(), P = Array.isArray(j) ? j : (j.patches || []);
      const out = P.map(p => ({ ...p, start: +p.t0, end: +p.t1 })).filter(p => isFinite(p.start) && isFinite(p.end)).sort((a, b) => a.start - b.start);
      c._patches = out.length ? out : null;
    } catch (e) { c._patches = null; }
    return c._patches;
  },
  async setCut(i, quiet, tOver, playOver) {
    if (!this.cuts.length) return;
    i = (i + this.cuts.length) % this.cuts.length;
    const t = tOver != null ? tOver : this.cutsLoaded && this.master() ? this.now() : 0, was = playOver != null ? playOver : this.playing;
    this.pause();
    this.ci = i; const c = this.cut();
    try { localStorage.setItem('lab.wygwyl.cut', c.slug); } catch (e) { /* storage blocked */ }
    this.patches = await this.loadPatches(c);
    if (c.patches && !this.patches && !quiet) toast(`${c.title}: patches.json not readable — showing the original beats`);
    this.useFilm = !!c.film;
    this.cur = -1;
    if (this.host) { this.renderCuts(); this.ribbon(); }
    this.applyMaster(t, was);
    const k = this.indexAt(t); this.select(k >= 0 ? k : 0, false, true);
    if (!quiet) toast(`cut · ${c.title}`);
  },
  /** point the clock at the film (its own soundtrack is the suite audio) or, with no film, the suite audio + stills */
  applyMaster(t, play) {
    const c = this.cut() || {}, f = this.film, a = this.audio;
    if (this.useFilm && c.film) {
      a.pause(); a.removeAttribute('src'); a.load();
      if (f.getAttribute('src') !== c.film) f.src = c.film;
    } else {
      this.useFilm = false;
      f.pause(); f.removeAttribute('src'); f.load();
      const au = (L.wyg.cut && L.wyg.cut.audio) || 'wygwyl/WYGWYL_Suite_Audio.mp3';
      if (a.getAttribute('src') !== au) a.src = au;
    }
    f.hidden = !this.useFilm; $('#wyMock', this.host).hidden = this.useFilm || !!this.patches; $('#wyFallback', this.host).hidden = this.useFilm || !this.patches;
    this.setTime(t || 0);
    if (play) this.play();
    this.paintSrc();
  },
  ribbon() {
    const D = this.dur(), R = $('#wyRibbon', this.host);
    const films = this.films().map(f => `<div class="wy-ch" style="left:${f.container[0] / D * 100}%;width:${(f.container[1] - f.container[0]) / D * 100}%" title="${esc(f.n)} · ${esc(f.title)}"><span>${esc(f.n)} ${esc(f.title)}</span></div>`).join('');
    const cells = this.patches
      ? this.patches.map((p, i) => { const th = p.clip && p.clip.thumb; return `<div class="wy-beat wy-patch${th ? '' : ' empty'}" data-i="${i}" style="left:${p.start / D * 100}%;width:${Math.max(.04, (p.end - p.start) / D * 100)}%;${th ? `background-image:url('${esc(th)}')` : ''}"></div>`; }).join('')
      : this.beats().map((b, i) => `<div class="wy-beat m-${esc(b.mode)}" data-i="${i}" style="left:${b.start / D * 100}%;width:${Math.max(.05, (b.end - b.start) / D * 100)}%;${b.a && b.a.thumb ? `background-image:url('${esc(b.a.thumb)}')` : ''}"><i>${MODE_GLYPH[b.mode] || '·'}</i></div>`).join('');
    R.innerHTML = `<div class="wy-chs">${films}</div><div class="wy-beats">${cells}</div><div class="wy-ph" id="wyPH"></div>`;
  },
  /** set the master clock; before its metadata has loaded, remember the time and apply it on load */
  setTime(t) {
    if (this.grid && !this.gridFile) { this.gv.forEach(v => { if (v.getAttribute('src')) setVT(v, t); }); this._pendingT = t; return; }
    const m = this.master();
    if (m.readyState >= 1) { try { m.currentTime = t; } catch (e) { /* ignore */ } }
    else { m.preload = 'auto'; m.addEventListener('loadedmetadata', () => { try { m.currentTime = this._pendingT ?? t; } catch (e) { /* ignore */ } }, { once: true }); }
    this._pendingT = t;
  },
  cellLabel(c) {
    if (!c) return '';
    if (this.patches) return `${c.id || ''} · ${c.clip ? c.clip.title : c.beat_title || 'patch'} · ${mmss(c.start)}–${mmss(c.end)}${c.line ? ' · “' + c.line + '”' : ''}`;
    return `#${c.id} · ${c.title} · ${c.mode} · ${mmss(c.start)}–${mmss(c.end)}`;
  },
  now() { const m = this.master(); return m && m.readyState >= 1 ? (m.currentTime || 0) : (this._pendingT || 0); },
  master() { if (this.grid) return this.gridFile ? this.film : this.gv[0]; return this.useFilm ? this.film : this.audio; },
  indexAt(t) { const B = this.cells(); for (let i = 0; i < B.length; i++) if (t >= B[i].start && t < B[i].end) return i; return t >= this.dur() - .05 ? B.length - 1 : -1; },
  seek(t) {
    this.setTime(clamp(t, 0, this.dur() - .01));
    const i = this.indexAt(t); if (i >= 0 && i !== this.cur) this.select(i, false);
    this.paintHead(t);
  },
  select(i, seekTo = true, force = false) {
    const B = this.cells(); if (!B.length) return;
    i = clamp(i, 0, B.length - 1);
    const changed = i !== this.cur; this.cur = i;
    if (seekTo) this.setTime(B[i].start + .001);
    if (changed || force) { this.card(); if (!this.useFilm) this.mock(); }
    $$('.wy-beat', this.host).forEach(c => c.classList.toggle('on', +c.dataset.i === i));
    this.paintHead(seekTo ? B[i].start : this.now());
  },
  async goBeat(id) {
    Inspector.close();
    Shell.setMode('wyg');
    const fk = this.cuts.findIndex(c => c.slug === 'forage');               // beats belong to the original cut
    if (this.grid) await this.leaveGrid(fk); else if (this.patches) await this.setCut(fk, true);
    const i = this.beats().findIndex(b => String(b.id) === String(id));
    if (i >= 0) this.select(i, true);
  },
  act(a) {
    if (a === 'play') this.playing ? this.pause() : this.play();
    else if (a === 'prev') this.select(this.cur - 1);
    else if (a === 'next') this.select(this.cur + 1);
    else if (a === 'cut') window.open('tools/cut.html?load=wygwyl', 'cineosis-cut');
    else if (a === 'wag') { if (L.server) window.open('tools/hand-butter.html?load=wygwyl', 'cineosis-room'); }
    else if (a === 'json') this.exportCut();
  },
  play() { this.playing = true; this.master().play().catch(() => { this.playing = false; this.paintPlay(); }); this.paintPlay(); },
  pause() { this.playing = false; if (this.audio) this.audio.pause(); if (this.film) this.film.pause(); this.gv.forEach(v => v.pause()); this.paintPlay(); },
  paintPlay() { const b = $('.wy-ctl [data-a="play"]', this.host); if (b) b.textContent = this.playing && !this.master().paused ? '❚❚' : '▶'; },
  paintSrc() {
    const c = this.cut() || {};
    if (this.grid) { $('#wySrc', this.host).innerHTML = this.gridFile ? '<b>rendered grid</b> · one file' : `<b>grid</b> · ${this.gcuts.length} cuts in sync · hearing <b>${esc(c.title || '')}</b>`; return; }
    $('#wySrc', this.host).innerHTML = this.useFilm ? `<b>${esc(c.title || 'cut')}</b> · moving footage` :
      `<b class="warn">no rendered film for this cut yet</b> · suite audio over a stills mock-up`;
  },
  paintHead(t) {
    const ph = $('#wyPH', this.host); if (ph) ph.style.left = (t / this.dur() * 100) + '%';
    const tcs = `${mmss(t)} / ${mmss(this.dur())}`; if (tcs !== this._tc) { $('#wyTC', this.host).textContent = tcs; this._tc = tcs; }
  },
  loop() {
    cancelAnimationFrame(this.raf); this.paintSrc();
    const step = () => {
      if (Shell.mode !== 'wyg') return;
      const t = this.now();
      if (this.playing) { const i = this.indexAt(t); if (i >= 0 && i !== this.cur) this.select(i, false); }   // the clock leads only while playing
      if (this.playing || t !== this._lastT) this.paintHead(t);
      this._lastT = t; if (!this.useFilm) this.animMock(t);
      this.raf = requestAnimationFrame(step);
    };
    this.raf = requestAnimationFrame(step);
  },
  /** fallback only (no rendered film): the beat's composition from its A/B stills, or the patch's clip still */
  mock() {
    if (this.patches) {
      const p = this.patches[this.cur], F2 = $('#wyFallback', this.host); if (!F2) return;
      F2.innerHTML = `<div class="wm wm-full wm-hold" style="${p && p.clip && p.clip.thumb ? `background-image:url('${esc(p.clip.thumb)}')` : ''}"></div><div class="wm-cap"><span class="wm-mode">stills mock-up · no film</span> ${esc(p ? (p.clip ? p.clip.title : p.beat_title || '') : '')}</div>`;
      return;
    }
    const b = this.beats()[this.cur], M = $('#wyMock', this.host); if (!b || !M) return;
    const img = (x, cls) => x && x.thumb ? `<div class="wm ${cls}" style="background-image:url('${esc(x.thumb)}')"></div>` : `<div class="wm ${cls} none"></div>`;
    let h = '';
    if (b.mode === 'black') h = `<div class="wm-black"><span>${esc(b.title)}</span></div>`;
    else if (b.mode === 'split') h = img(b.a, 'wm-l') + img(b.b, 'wm-r');
    else if (b.mode === 'inset') h = img(b.a, 'wm-full') + img(b.b, 'wm-inset');
    else if (b.mode === 'dissolve') h = img(b.a, 'wm-full') + img(b.b, 'wm-full wm-over');
    else if (b.mode === 'montage') h = img(b.a, 'wm-full wm-mA') + img(b.b, 'wm-full wm-mB');
    else h = img(b.a, 'wm-full wm-hold');
    M.className = 'wy-mock mode-' + b.mode;
    M.innerHTML = h + `<div class="wm-cap"><span class="wm-mode">stills mock-up · no film · ${MODE_GLYPH[b.mode] || ''} ${esc(b.mode)}</span> ${esc(b.title)}</div>`;
  },
  animMock(t) {
    const b = this.cells()[this.cur]; if (!b) return;
    const p = clamp((t - b.start) / Math.max(.1, b.end - b.start), 0, 1), M = this.patches ? $('#wyFallback', this.host) : $('#wyMock', this.host);
    if (!this.patches && b.mode === 'dissolve') { const o = $('.wm-over', M); if (o) o.style.opacity = p.toFixed(3); }
    else if (!this.patches && b.mode === 'montage') { const on = Math.floor(t / .7) % 2 === 0, a = $('.wm-mA', M), bb = $('.wm-mB', M); if (a && bb) { a.style.opacity = on ? 1 : 0; bb.style.opacity = on ? 0 : 1; } }
    const k = $('.wm-hold', M) || $('.wm-full', M); if (k) k.style.transform = `scale(${(1 + p * .05).toFixed(4)})`;
  },
  /* ---- grid: the new cuts side by side, one clock ---- */
  async toggleGrid() {
    if (this.grid) { const k = this.cuts.indexOf(this.gcuts[this.focus]); return this.leaveGrid(k >= 0 ? k : this.ci); }
    if (this.gcuts.length < 2) { toast('the grid needs at least two rendered cuts in wygwyl/cuts/'); return; }
    const k = this.gcuts.indexOf(this.cut()); if (k >= 0) this.focus = k;
    await this.enterGrid(this.now(), this.playing);
  },
  async enterGrid(t, play) {
    this.pause();
    const a = this.audio, f = this.film;
    a.removeAttribute('src'); a.load();
    this.grid = true; this.useFilm = false;
    try { localStorage.setItem('lab.wygwyl.grid', '1'); } catch (e) { /* storage blocked */ }
    if (this.gridFile && this.gridURL) { if (f.getAttribute('src') !== this.gridURL) f.src = this.gridURL; f.muted = false; }
    else { f.pause(); f.removeAttribute('src'); f.load(); }
    this.gcuts.forEach((c, i) => { const v = this.gv[i]; if (this.gridFile) { v.pause(); v.removeAttribute('src'); v.load(); return; } if (v.getAttribute('src') !== c.film) v.src = c.film; v.playbackRate = 1; });
    this.gv.forEach((v, i) => { v.parentNode.hidden = i >= this.gcuts.length; v.nextElementSibling.textContent = this.gcuts[i] ? this.gcuts[i].title : ''; });
    await Promise.all(this.gcuts.map(c => this.loadPatches(c)));
    $('#wyGrid', this.host).hidden = this.gridFile; f.hidden = !this.gridFile;
    $('#wyMock', this.host).hidden = true; $('#wyFallback', this.host).hidden = true;
    $('#wyGrid', this.host).dataset.n = this.gcuts.length;
    this.setFocus(this.focus, true);
    this.setTime(t || 0);
    if (play) this.play();
  },
  /** the focused quadrant is the one heard and read; timing never changes (all four carry the same suite audio) */
  setFocus(q, quiet) {
    if (!this.grid || !this.gcuts[q]) return;
    this.focus = q;
    if (!this.gridFile) this.gv.forEach((v, i) => { v.muted = i !== q; });
    $$('.wg-cell', this.host).forEach(c => c.classList.toggle('focus', +c.dataset.q === q));
    this.ci = Math.max(0, this.cuts.indexOf(this.gcuts[q]));
    this.patches = this.gcuts[q]._patches || null;
    this.cur = -1; this.renderCuts(); this.ribbon();
    const k = this.indexAt(this.now()); this.select(k >= 0 ? k : 0, false, true);
    this.paintSrc();
    if (!quiet) toast(`hearing ${this.gcuts[q].title}`);
  },
  async leaveGrid(k) {
    const t = this.now(), was = this.playing;
    this.pause(); this.grid = false;
    try { localStorage.setItem('lab.wygwyl.grid', '0'); } catch (e) { /* storage blocked */ }
    this.gv.forEach(v => { v.removeAttribute('src'); v.load(); v.playbackRate = 1; });
    $('#wyGrid', this.host).hidden = true;
    await this.setCut(k, true, t, was);
  },
  toggleGridFile() {
    if (!this.gridURL) return;
    const t = this.now(), was = this.playing; this.gridFile = !this.gridFile;
    this.enterGrid(t, was); this.renderCuts();
  },
  /** every ~500 ms: followers drifting more than 0.12 s get nudged (±3 % rate under 0.4 s) or re-seated */
  drift() {
    if (!this.grid || this.gridFile || !this.playing) return;
    const M = this.gv[0]; if (M.paused || M.readyState < 2) return;
    for (const v of this.gv.slice(1)) {
      if (!v.getAttribute('src') || v.readyState < 1) continue;
      if (v.paused && !M.paused) v.play().catch(() => {});
      const d = v.currentTime - M.currentTime, ad = Math.abs(d);
      if (ad > 0.4) { v.currentTime = M.currentTime; v.playbackRate = 1; }
      else if (ad > 0.12) v.playbackRate = d > 0 ? 0.97 : 1.03;
      else if (ad < 0.04 && v.playbackRate !== 1) v.playbackRate = 1;
    }
  },
  patchCard() {
    const p = this.patches[this.cur], C = $('#wyCard', this.host); if (!p || !C) return;
    const cl = p.clip, s = cl && L.byId.get(cl.id), c = this.cut();
    C.innerHTML = `<div class="sd-block">
      <div class="wy-h"><span class="wy-n">${esc(p.id || '')}</span><b>${esc(cl ? cl.title : (p.beat_title || 'patch'))}</b></div>
      <div class="kv"><span>cut</span><b>${esc(c.title)}</b><span>chapter</span><b>${esc(p.chapter || '')}${p.film ? ' · ' + esc(p.film) : ''}</b>
        <span>time</span><b>${mmss(p.start)} – ${mmss(p.end)} · ${(p.end - p.start).toFixed(1)} s</b>
        ${p.beat ? `<span>beat</span><b>#${esc(String(p.beat))}${p.beat_title ? ' · ' + esc(p.beat_title) : ''}</b>` : ''}</div>
      ${(p.codes || []).length ? `<div class="wy-codes"><span>cineosis signs</span>${p.codes.map(n => `<button class="wy-code" data-n="${esc(String(n))}">${chip(String(n))}${esc(L.S[String(n)] ? L.S[String(n)].name : n)}</button>`).join('')}</div>` : ''}
      ${p.line ? `<h4>the line</h4><p class="wy-line">“${esc(p.line)}”</p>` : ''}
      ${p.why ? `<h4>why this clip</h4><p class="wy-p">${esc(p.why)}</p>` : ''}</div>
      <div class="sd-block"><h4>clip</h4>${cl ? `<div class="wy-ab" data-id="${esc(cl.id)}"><em></em><img src="${esc(cl.thumb || (s && s.thumb) || '')}" alt="" onerror="this.style.visibility='hidden'">
        <div><b>${esc(cl.title)}</b><span>${cl.year ?? '—'}${cl.in != null ? ` · in ${(+cl.in).toFixed(1)} s` : ''}${cl.out != null ? ` · out ${(+cl.out).toFixed(1)} s` : ''}</span>
        <p>${s ? 'click to inspect' : 'not in the lab corpus'}</p></div></div>` : '<span class="pending">no clip chosen for this patch yet</span>'}</div>`;
  },
  candidates(b) { return (L.wygCands.get(String(b.id)) || []).slice().sort((x, y) => GRADE_ORDER(x.wygwyl.grade) - GRADE_ORDER(y.wygwyl.grade) || (y._read.length - x._read.length)); },
  card() {
    if (this.patches) return this.patchCard();
    const b = this.beats()[this.cur], C = $('#wyCard', this.host); if (!b || !C) return;
    const f = this.films()[b.chapter] || {}, ch = this.choices()[b.id] || {};
    const side = (x, k) => {
      if (!x) return `<div class="wy-ab"><em>${k}</em><span class="pending">none</span></div>`;
      const pick = ch[k] && ch[k] !== x.id ? L.byId.get(ch[k]) : null;
      return `<div class="wy-ab" data-id="${esc(x.id)}"><em>${k}</em><img src="${esc(x.thumb || '')}" alt="" onerror="this.style.visibility='hidden'">
        <div><b>${esc(x.title)}</b><span>${x.year ?? '—'} · ${x.dur ? x.dur.toFixed(1) + ' s' : ''} · grade ${esc(x.grade || 'U')}</span><p>${esc(x.observed || '')}</p>
        ${pick ? `<p class="wy-pick">your choice: <b>${esc(pick.title)}</b> (${pick.year ?? '—'})</p>` : ''}</div></div>`;
    };
    const cands = this.candidates(b);
    C.innerHTML = `<div class="sd-block">
      <div class="wy-h"><span class="wy-n">#${esc(b.id)}</span><b>${esc(b.title)}</b></div>
      <div class="kv"><span>chapter</span><b>${esc(f.n || '')} · ${esc(f.title || b.sequence || '')}</b><span>time</span><b>${mmss(b.start)} – ${mmss(b.end)} · ${(b.end - b.start).toFixed(1)} s</b>
        <span>mode</span><b>${MODE_GLYPH[b.mode] || ''} ${esc(b.mode)}${b.partner ? ` · partner #${esc(b.partner)}` : ''}</b>${b.rate && b.rate !== 1 ? `<span>rate</span><b>${b.rate}×</b>` : ''}</div>
      ${(b.codes || []).length ? `<div class="wy-codes"><span>cineosis signs</span>${b.codes.map(n => `<button class="wy-code" data-n="${esc(String(n))}" title="open ${esc(L.S[String(n)] ? L.S[String(n)].name : n)} in the periodic table">${chip(String(n))}${esc(L.S[String(n)] ? L.S[String(n)].name : n)}</button>`).join('')}</div>` : ''}
      ${b.edit ? `<h4>edit</h4><p class="wy-p">${esc(b.edit)}</p>` : ''}
      ${b.operation ? `<h4>operation</h4><p class="wy-p">${esc(b.operation)}</p>` : ''}
      ${b.gap ? `<h4>gap — needs original material</h4><p class="wy-p wy-gap">${esc(b.gap)}</p>` : ''}
      ${b.query ? `<p class="hint">search: “${esc(b.query)}”</p>` : ''}</div>
      <div class="sd-block"><h4>A · B</h4>${side(b.a, 'A')}${side(b.b, 'B')}</div>
      <div class="sd-block"><h4>candidates <small>${cands.length} corpus shot${cands.length === 1 ? '' : 's'} forage found for this beat · reviewed first</small></h4>
        <div class="wy-cands">${cands.map(s => `<div class="wy-cand${ch.A === s.id ? ' isA' : ''}${ch.B === s.id ? ' isB' : ''}" data-id="${esc(s.id)}">
          <img src="${esc(s.thumb)}" alt="" onerror="this.style.visibility='hidden'"><span class="gr g-${esc(s.wygwyl.grade || 'U')}">${esc(s.wygwyl.grade || 'U')}</span>
          <p>${esc(s.wygwyl.observed || s.title)}</p>
          <div class="wy-use"><button class="ghost" data-use="A">use as A</button><button class="ghost" data-use="B">use as B</button></div></div>`).join('') || '<span class="pending">no candidates recorded</span>'}</div></div>`;
  },
  onCard(e) {
    const code = e.target.closest('.wy-code');
    if (code) { window.open('../periodic-table.html#' + encodeURIComponent(code.dataset.n), '_blank', 'noopener'); return; }
    const use = e.target.closest('[data-use]');
    if (use) { this.choose(use.closest('.wy-cand').dataset.id, use.dataset.use); return; }
    const t = e.target.closest('.wy-ab[data-id], .wy-cand');
    if (t) { const s = L.byId.get(t.dataset.id); if (s) { this.pause(); Inspector.open(s, this.patches ? [s] : this.candidates(this.beats()[this.cur])); } else toast('that shot isn’t in the lab corpus'); }
  },
  /** {beatId: {A: shotId, B: shotId}} from the saved assignment rows (last one wins) */
  choices() {
    const out = {};
    for (const r of L.assignments) { const m = /^wygwyl beat (\S+) (A|B)$/.exec(r.note || ''); if (m) (out[m[1]] = out[m[1]] || {})[m[2]] = r.id; }
    return out;
  },
  async choose(id, k) {
    if (this.patches) return;
    const b = this.beats()[this.cur]; if (!b) return;
    const note = `wygwyl beat ${b.id} ${k}`;
    if (!L.server) { const row = { id, n: null, note, a: null, b: null, ts: new Date().toISOString().slice(0, 19) }; if (!Store.add(row)) { toast('this browser blocks local storage'); return; } L.assignments.push(row); }
    else {
      try {  // server.py requires a truthy n, so the collection name stands in for “no sign”
        const r = await fetch('/api/assign', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id, n: 'wygwyl', note, a: null, b: null }) });
        const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.error || 'HTTP ' + r.status); L.assignments.push(j);
      } catch (er) { toast('not saved — ' + er.message); return; }
    }
    toast(`beat #${b.id}: ${k} = ${(L.byId.get(id) || {}).title || id}`); this.card();
  },
  async exportCut() {
    let cut;
    try { const r = await fetch('wygwyl/WYGWYL_Forage_Cut.json'); if (!r.ok) throw new Error(r.status); cut = await r.json(); }
    catch (e) { toast('could not read wygwyl/WYGWYL_Forage_Cut.json'); return; }
    const ch = this.choices(), applied = [];
    for (const sh of cut.shots || []) {
      const c = ch[sh.id]; if (!c) continue;
      if (c.A) { sh.selected = c.A; applied.push({ beat: sh.id, A: c.A }); }
      if (c.B) { sh.layer = c.B; applied.push({ beat: sh.id, B: c.B }); }   // B normally comes from the partner beat; an explicit pick rides on `layer`
    }
    cut.lab_choices = applied; cut.lab_note = 'A picks replace `selected`; B picks are recorded in `layer` (the counter-image), since B otherwise comes from the partner beat.';
    const url = URL.createObjectURL(new Blob([JSON.stringify(cut, null, 1)], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = 'WYGWYL_Forage_Cut.lab.json'; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 5000);
    toast(`cut JSON exported · ${applied.length} choice${applied.length === 1 ? '' : 's'} applied`);
  },
  key(e) {
    if (e.key === 'g' || e.key === 'G') { this.toggleGrid(); return true; }
    if (e.key === '[') { this.setCut(this.ci - 1); return true; }
    if (e.key === ']') { this.setCut(this.ci + 1); return true; }
    if (e.key === ' ') { e.preventDefault(); this.act('play'); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); this.select(this.cur + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); this.select(this.cur - 1); }
    else return false;
    return true;
  },
};

/* ================================================================ GUIDE (first-visit card) + STATUS (what is filtered, and the undo) */
const Guide = {
  key: 'cineosis.seen',
  seen() { try { return !!localStorage.getItem(this.key); } catch (e) { return true; } },
  open() { const g = $('#guide'); return !!g && !g.hidden; },
  show() {
    const g = $('#guide'); if (!g) return;
    g.setAttribute('role', 'dialog'); g.setAttribute('aria-labelledby', 'guideH');
    g.innerHTML = `<div class="gd-h" id="guideH">Start here <em>3 steps</em></div>
      <ol>
        <li data-g="1"><b>Click a sign</b> in the table at left: the wall keeps only that sign’s shots. <span>No table? Press <kbd>F</kbd> or the ≡ button at top left.</span></li>
        <li data-g="2"><b>Click any shot:</b> the inspector plays it from the frame the reading was made from. <span><kbd>Esc</kbd> closes it.</span></li>
        <li data-g="3"><b>Press <kbd>1</kbd>–<kbd>8</kbd></b> to switch views. <span><kbd>?</kbd> lists every key.</span></li>
      </ol>
      <div class="gd-f"><button class="gd-go" id="guideGo">Start</button><span><kbd>Esc</kbd> closes · <kbd>?</kbd> reopens</span></div>`;
    g.hidden = false;
    $('#guideGo', g).onclick = e => { e.stopPropagation(); this.close(); };
    if (F.signs.size) this.mark(1);
    try { $('#guideGo', g).focus({ preventScroll: true }); } catch (e) { /* old browser */ }
  },
  close() {
    const g = $('#guide'); if (g) g.hidden = true;
    try { localStorage.setItem(this.key, '1'); } catch (e) { /* storage blocked: the card returns next visit */ }
  },
  mark(i) { const li = this.open() && $(`#guide [data-g="${i}"]`); if (li) li.classList.add('done'); },
};

const Status = {
  items: [],
  /** every change from the default view, each with its own undo */
  active() {
    const out = [], add = (label, title, clear) => out.push({ label, title, clear });
    const scopeN = { read: 'read only', machine: 'machine top-3' };
    if (F.col !== 'both') add(`collection ${F.col}`, 'show both collections', () => { F.col = 'both'; });
    if (F.smode !== 'corpus') add(`signs: ${scopeN[F.smode]}`, 'count every shot a sign’s searches surfaced', () => { F.smode = 'corpus'; });
    for (const n of F.signs) { const g = L.S[n]; add(`sign ${chip(n, 'sm')}${g ? esc(n) : ''}`, g ? `remove ${g.name}` : 'remove', () => { F.signs.delete(n); }); }
    if (F.dec.size) add(`decade ${esc(Facets.decRangeLabel())}`, 'show every decade', () => { F.dec.clear(); });
    if (F.color !== 'all') add(F.color === 'bw' ? 'B&amp;W' : 'colour', 'show colour and B&W', () => { F.color = 'all'; });
    if (F.hue) add(`hue ${Math.round(F.hue[0])}°–${Math.round(F.hue[1])}°`, 'show every hue', () => { F.hue = null; });
    for (const l of F.subj) add(`subject ${esc(l)}`, 'remove this subject', () => { F.subj.delete(l); });
    for (const c of F.scale) add(`scale ${SCALE_AB[c] || esc(c)}`, 'remove this scale', () => { F.scale.delete(c); });
    if (F.cut) add('has cut-outs', 'show shots without cut-outs too', () => { F.cut = false; });
    for (const k of F.audio) add(`audio ${esc(k)}`, 'remove this audio kind', () => { F.audio.delete(k); });
    if (F.q && Shell.scope === 'corpus') add(`search “${esc(F.q)}”`, 'clear the search', () => { $('#q').value = ''; parseQuery(''); });
    if (GROUP !== 'none') add(`grouped by ${esc(GROUP)}`, 'stop grouping', () => { GROUP = 'none'; $('#group').value = 'none'; });
    if (SORT.key !== 'sign' || SORT.dir < 0) add(`sorted by ${esc(($('#sort').selectedOptions[0] || {}).textContent || SORT.key)} ${SORT.dir < 0 ? '↑' : '↓'}`, 'back to sign order', () => { SORT.key = 'sign'; SORT.dir = 1; $('#sort').value = 'sign'; $('#sortDir').textContent = '↓'; });
    return out;
  },
  render(lv) {
    const b = $('#status'); if (!b) return;
    if (!b._wired) {
      b._wired = true;
      b.addEventListener('click', e => {
        const x = e.target.closest('[data-x]');
        if (x) { const it = this.items[+x.dataset.x]; if (it) { it.clear(); refresh(); } return; }
        if (e.target.closest('#stReset')) { Facets.reset(); return; }
        if (e.target.closest('#stPanel')) { document.body.classList.remove('nofacets'); Shell.updateCount(); setTimeout(() => { Wall.resize(); Strata.resize(); }, 260); }
      });
    }
    const it = this.items = this.active(), n = VIEW.length, N = L.shots.length;
    const live = lv ? ` <span class="livebadge">+${lv} LIVE</span>` : '';
    const count = !it.length ? `Showing all <b>${fmt(N)}</b> shots${live}`
      : n ? `Showing <b>${fmt(n)}</b> of ${fmt(N)} shots${live}` : `<b>No shots match</b>${live} · remove a filter (✕) or reset all`;
    const panelHidden = document.body.classList.contains('nofacets');
    const hint = panelHidden ? ` · <button class="st-lnk" id="stPanel">open filters</button> and click a sign to narrow` : ' · click a sign in the table at left to narrow';
    b.innerHTML = `<span class="st-n">${count}</span>` + (it.length
      ? `<span class="st-f"><span class="st-l">filters:</span>${it.map((x, i) => `<button class="st-x" data-x="${i}" title="${esc(x.title)} (click ✕)" aria-label="remove filter ${x.label.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()}">${x.label}<i aria-hidden="true">✕</i></button>`).join('')}</span><button class="st-lnk st-reset" id="stReset" title="clear every filter, the search, sort and grouping">reset all</button>`
      : `<span class="st-h">${hint}</span>`);
  },
};

/* ================================================================ SHELL */
const MODES = { wall: Wall, map: MapMode, ring: Ring, strata: Strata, cuts: Cuts, reel: Reel, montage: Montage, wyg: Wyg };
const Shell = {
  mode: null, prevMode: null, size: 132, scope: 'corpus',
  init() {
    this.size = innerWidth < 640 ? 100 : innerWidth > 2000 ? 150 : 132;
    try { const v = +localStorage.getItem('lab.size'); if (v) this.size = v; } catch (e) { /* storage blocked */ }
    $('#size').value = this.size;
    $('#modes').addEventListener('click', e => { const b = e.target.closest('button[data-mode]'); if (b) this.setMode(b.dataset.mode); });
    $('#sort').addEventListener('change', e => { SORT.key = e.target.value; refresh(); });
    $('#sortDir').addEventListener('click', () => { SORT.dir *= -1; $('#sortDir').textContent = SORT.dir > 0 ? '↓' : '↑'; refresh(); });
    $('#group').addEventListener('change', e => { GROUP = e.target.value; refresh(); });
    $('#size').addEventListener('input', e => {
      this.size = +e.target.value; try { localStorage.setItem('lab.size', this.size); } catch (er) { /* ignore */ }
      if (this.mode === 'wall') Wall.resize(); else if (this.mode === 'strata') Strata.resize();
    });
    const q = $('#q');
    const onInput = debounce(() => { if (this.scope === 'corpus') { parseQuery(q.value); refresh(); } }, 90);
    q.addEventListener('input', onInput);
    $('#search').addEventListener('submit', e => { e.preventDefault(); if (this.scope === 'archive') Live.search(q.value); });
    $('.scope').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.scope === 'archive' && !L.server) { this.qstat(STATIC_NOTE, 'warn'); toast(STATIC_NOTE, 4200); return; }
      this.scope = b.dataset.scope;
      $$('.scope button').forEach(x => x.classList.toggle('on', x === b));
      q.placeholder = this.scope === 'corpus' ? 'search titles, readings, queries, subjects · #Dm · 1940s' : 'describe a shot, press Enter to search the whole archive';
      if (this.scope === 'archive' && F.q) { parseQuery(''); refresh(); }
      if (this.scope === 'corpus') { parseQuery(q.value); refresh(); }
      this.qstat(''); q.focus();
    });
    $('#facetBtn').addEventListener('click', () => { document.body.classList.toggle('nofacets'); Shell.updateCount(); });
    $('#aboutBtn').addEventListener('click', e => { e.stopPropagation(); this.help(); });
    $('#reload').addEventListener('click', () => this.reload());
    const pop = $('#sendPop');
    $('#sendBtn').addEventListener('click', e => {
      e.stopPropagation();
      if (!pop.hidden) { pop.hidden = true; return; }
      const n = viewList().length;
      pop.innerHTML = `<div class="sp-h">send the view to an editor</div>
        <p>${n > 24 ? `the first 24 of ${fmt(n)} shots, in the current order` : `${fmt(n)} shot${n === 1 ? '' : 's'}, in the current order`}${L.server ? '' : ' · static site: only shots with a local clip travel'}</p>
        <label>layout <select id="spLayout">${LAYOUTS.map(l => `<option>${l}</option>`).join('')}</select></label>
        <div class="cutbtns">${sendButtons()}</div>`;
      pop.hidden = false;
    });
    pop.addEventListener('click', e => { e.stopPropagation(); const b = e.target.closest('[data-send]'); if (!b) return; Send.sendView(b.dataset.send, $('#spLayout').value); pop.hidden = true; });
    document.addEventListener('click', () => { pop.hidden = true; });
    if (innerWidth < 900) document.body.classList.add('nofacets');
    addEventListener('keydown', e => this.key(e));
    addEventListener('resize', debounce(() => { if (this.mode === 'ring') Ring.resize(); Facets.drawHue(); }, 150));
    addEventListener('hashchange', () => { const m = ({ wygwyl: 'wyg' })[location.hash.slice(1)] || location.hash.slice(1); if (MODES[m] && m !== this.mode) this.setMode(m); });
    addEventListener('focus', () => { if (Date.now() - L.loadedAt > 5 * 60e3) this.reload(true); });
  },
  setMode(m) {
    if (!MODES[m]) m = 'wall';
    if (m === this.mode) return;
    const old = this.mode;
    if (old && MODES[old].hide) MODES[old].hide();
    if (old === 'reel') Reel.close();
    if (m === 'reel') { this.prevMode = old && old !== 'reel' ? old : this.prevMode || 'wall'; }
    if (old) Guide.mark(3);
    this.mode = m;
    $$('#modes button').forEach(b => b.classList.toggle('on', b.dataset.mode === m));
    if (m === 'reel') { Reel.open(); } else {
      $$('.mode').forEach(s => { s.hidden = s.id !== 'm-' + m; });
      const host = $('#m-' + m), M = MODES[m];
      if (M.mount) M.mount(host);
      if (M.show) M.show();
    }
    document.body.dataset.mode = m;
    if (location.hash.slice(1) !== m) history.replaceState(null, '', '#' + m);
    Tip.hide();
  },
  badge() {
    const b = $('#srvBadge'); if (!b) return;
    b.innerHTML = L.server ? '<b>local</b><span> server</span>' : '<b>static</b><span> · archive search needs local server</span>';
    b.title = L.server ? 'server.py is running: archive search and saving to assignments.json are on' : STATIC_NOTE;
    const ar = $('.scope [data-scope="archive"]');
    ar.title = 'switch to archive, type, press Enter: the whole archive is searched';
    $('.scope').hidden = !L.server;
    if (!L.server && this.scope === 'archive') { this.scope = 'corpus'; $$('.scope button').forEach(x => x.classList.toggle('on', x.dataset.scope === 'corpus')); }
  },
  updateCount() {
    Status.render(liveView().length);
  },
  updateLiveBar() {
    const b = $('#livebar');
    if (!L.live.length) { b.hidden = true; document.body.classList.remove('haslive'); return; }
    b.hidden = false; document.body.classList.add('haslive');
    const hits = L.live.filter(s => !s._liveOnly).length;
    b.innerHTML = `<span class="livebadge">LIVE</span> <b>“${esc(L.liveQ)}”</b> <span>${L.live.length} clips from the archive · ${hits} already in the corpus · click any to inspect and assign a sign</span>
      <button class="ghost" id="liveHide">${L.showLive ? 'hide layer' : 'show layer'}</button><button class="ghost" id="liveClear">clear</button>`;
    $('#liveHide').onclick = () => { L.showLive = !L.showLive; refresh(); };
    $('#liveClear').onclick = () => Live.clear();
  },
  qstat(t, cls) { const s = $('#qstat'); s.textContent = t; s.className = cls || ''; },
  async reload(silent) {
    const b = $('#reload'); b.classList.add('spin');
    try {
      await loadData(true); Shell.badge(); Facets.update(); MapMode.kind = null; Ring.key = null;
      if (this.mode === 'map') MapMode.show();
      Wyg.cutsLoaded = false;
      if (this.mode === 'wyg') Wyg.show();
      if (this.mode === 'montage') Montage.renderRecipes();
      if (Cuts.host) Cuts.update();
      refresh();
      if (!silent) toast(`reloaded · ${fmt(L.shots.length)} shots · ${['palette', 'xy', 'strip', 'cut', 'subj', 'audio'].filter(k => L.has[k]).join(' · ') || 'no analysis yet'}`);
    } catch (e) { if (!silent) toast('reload failed — ' + e.message); }
    b.classList.remove('spin');
  },
  help() {
    const A = $('#about');
    if (!A.hidden) { A.hidden = true; return; }
    if (Guide.open()) { Guide.close(); this.about(); return; }
    Guide.show();
  },
  about() {
    const A = $('#about');
    if (!A.hidden) { A.hidden = true; return; }
    A.innerHTML = `<div class="about-in"><button class="ghost about-x" title="close">✕</button>
      <h2>Cineosis Lab</h2>
      <p class="lede">${fmt(L.shots.length)} shots from the Moving Image Archive, ${fmt(L.shots.filter(s => s._read.length).length)} of them read by the editor for one of the 45 signs. Click controls on the left to narrow them; every view below shows that same selection, in the same order. The line above the shots lists each filter: click its ✕ to remove it, or “reset all”.</p>
      <h3>First steps</h3>
      <ol class="about-steps">
        <li>Click a sign in the table at left: the shots narrow to that sign. Shift-click keeps only that sign.</li>
        <li>Click any shot: the inspector plays it from the frame the reading was made from. <kbd>Esc</kbd> closes it.</li>
        <li>Press <kbd>1</kbd>–<kbd>8</kbd> to switch views.</li>
      </ol>
      <h3>Views</h3>
      <dl>
        <dt>Wall <kbd>1</kbd></dt><dd>Every shot in the selection as a grid. Pick sort and group in the top bar: tiles slide to their new places. Drag the size slider to resize tiles.</dd>
        <dt>Map <kbd>2</kbd></dt><dd>Shots placed by visual likeness. Drag to pan, wheel or pinch to zoom, <kbd>0</kbd> to fit. Shots outside the filter stay dimmed in place.</dd>
        <dt>Ring <kbd>3</kbd></dt><dd>The first 240 shots of the selection on a cylinder. Drag or wheel to spin; click a shot to inspect it.</dd>
        <dt>Strata <kbd>4</kbd></dt><dd>Each shot as a stack of its own frames, time running into depth. Hover a stack to run it.</dd>
        <dt>Cut-outs <kbd>5</kbd></dt><dd>Figures lifted out of the shots. Drag one onto the table; shift-click duplicates it; select two and press <kbd>+</kbd> to join; <kbd>Delete</kbd> removes it.</dd>
        <dt>Reel <kbd>6</kbd></dt><dd>Plays the table: each sign’s title card, then the shots read for it. <kbd>space</kbd> plays, <kbd>←</kbd><kbd>→</kbd> changes sign, <kbd>[</kbd> <kbd>]</kbd> changes shot, <kbd>Esc</kbd> exits.</dd>
        <dt>Montage <kbd>7</kbd></dt><dd>Recipes for signs that need two or more shots (mark → demark, sheets of the past, forking paths…). Click × to drop a shot or ⇄ to swap it, then “→ CUT” to send the recipe to the editor; montages sent back appear under Edits.</dd>
        <dt>WYGWYL <kbd>8</kbd></dt><dd>The WYGWYL Forage Suite, a 24-minute film in 88 beats. Click the ribbon to jump to a beat; <kbd>space</kbd> plays, <kbd>←</kbd><kbd>→</kbd> steps beats, <kbd>[</kbd> <kbd>]</kbd> changes cut, <kbd>G</kbd> shows the cuts side by side. “Open WYGWYL page ↗” opens the film’s own page.</dd>
        <dt>Inspector</dt><dd>Click any shot. <kbd>space</kbd> plays, <kbd>,</kbd> <kbd>.</kbd> step one frame, <kbd>A</kbd> <kbd>B</kbd> set in/out, <kbd>M</kbd> jumps to the matched frame; pick a sign and click “save sub-shot” to record your reading.</dd>
        ${L.server ? `<dt>Archive search</dt><dd>Click <i>archive</i> beside the search box, type, press Enter: results from the whole archive appear as a LIVE layer above the shots. Click “clear” on that bar to remove it.</dd>` : ''}
      </dl>
      <h3>Your sub-shots</h3>
      <p class="about-p">${L.server ? 'Running on the local server: “save sub-shot” appends to lab/assignments.json.' : 'Static copy (no server): “save sub-shot” keeps rows in this browser only. Archive search needs the local server — clone the repo and run <code>python3 lab/server.py</code>.'}
        <button class="ghost" id="aboutExport">export assignments.json</button></p>
      <h3>Keys</h3>
      <div class="keys">
        <span><kbd>1</kbd>–<kbd>8</kbd> views</span><span><kbd>/</kbd> search</span><span><kbd>F</kbd> show/hide filters</span><span><kbd>?</kbd> first steps, then this list</span><span><kbd>Esc</kbd> close</span>
        <span>inspector: <kbd>space</kbd> play · <kbd>,</kbd> <kbd>.</kbd> ±1 frame · <kbd>←</kbd><kbd>→</kbd> ±1 frame (shift: ±1 s) · <kbd>A</kbd> <kbd>B</kbd> in/out · <kbd>[</kbd> <kbd>]</kbd> jump to A/B · <kbd>L</kbd> loop A–B · <kbd>M</kbd> matched frame · <kbd>0</kbd> <kbd>8</kbd> <kbd>9</kbd> <kbd>1</kbd> <kbd>2</kbd> speed 0/.25/.5/1/2 · <kbd>C</kbd> cut-outs · <kbd>↑</kbd><kbd>↓</kbd> prev/next shot</span>
        <span>reel: <kbd>space</kbd> play · <kbd>←</kbd><kbd>→</kbd> sign · <kbd>[</kbd> <kbd>]</kbd> shot</span>
      </div>
      <h3>Editors</h3>
      <p class="about-p">Two editors take shots from the lab. <b>CUT</b> treats the frame as a space and depth as time: each clip is a box placed in the frame and a moment in time, to chop, push and stretch, and it records the cut to video. <b>The Cutting Room</b> (WAG · Hand Butter 13) is a 3-D plate volume where time is depth. Send with “→ CUT” / “→ Cutting Room” from the Inspector, the top bar (“send view”), a sign chip (⌥-click: its family) or a Montage recipe. In the editor, “↩ lab” brings the montage back as data — which shots, which signs, in/out, when and where — and it appears under Montage → Edits, where you can play it here or reopen it in CUT. The Cutting Room is local-only (it needs <code>python3 lab/server.py</code>); CUT also works on the static site with the read shots’ clips.</p>
      <h3>Source &amp; credits</h3>
      <ul class="credits">
        <li>The signs follow David Deamer, <i>Deleuze’s Cinema Books: Three Introductions to the Taxonomy of Images</i> (Edinburgh University Press, 2016).</li>
        <li>Shots from <a href="https://www.movingimagearchive.com" target="_blank" rel="noopener">movingimagearchive.com</a> — public-domain collections; rights remain with their holders.</li>
        <li>Segmentation: SAM 2.1 (Meta, Apache-2.0). Embeddings and affinity: OpenCLIP ViT-B/32 (LAION).</li>
        <li>Readings are an editor’s judgements. Machine affinity is a pointer, not a reading.</li>
      </ul>
      <p class="foot"><a href="../periodic-table.html" target="_blank" rel="noopener">the periodic table ↗</a></p></div>`;
    A.hidden = false;
    $('.about-x', A).onclick = () => { A.hidden = true; };
    $('#aboutExport', A).onclick = exportAssignments;
    A.onclick = e => { if (e.target === A) A.hidden = true; };
  },
  key(e) {
    if (e.metaKey || e.ctrlKey) return;
    if (typing(e)) { if (e.key === 'Escape') e.target.blur(); return; }
    if (Inspector.root && !Inspector.root.hidden) { if (Inspector.key(e)) return; return; }
    if (!$('#about').hidden && e.key === 'Escape') { $('#about').hidden = true; return; }
    if (Guide.open() && e.key === 'Escape') { Guide.close(); return; }
    if (this.mode === 'reel' && Reel.key(e)) return;
    if (this.mode === 'wyg' && Wyg.key(e)) return;
    if (e.key === '/') { e.preventDefault(); $('#q').focus(); return; }
    if (e.key === '?') { this.help(); return; }
    if (e.key === 'f' || e.key === 'F') { document.body.classList.toggle('nofacets'); this.updateCount(); setTimeout(() => { Wall.resize(); Strata.resize(); }, 260); return; }
    const m = ['wall', 'map', 'ring', 'strata', 'cuts', 'reel', 'montage', 'wyg'][+e.key - 1];
    if (m && /^[1-8]$/.test(e.key)) { this.setMode(m); return; }
    if (this.mode === 'cuts' && (e.key === 'Delete' || e.key === 'Backspace')) { Cuts.removeSel(); return; }
    if (this.mode === 'cuts' && e.key === '+') { Cuts.join(); return; }
    if (this.mode === 'map' && (e.key === '0')) MapMode.fit();
  },
};

/* ================================================================ BOOT */
(async function boot() {
  try {
    await loadData();
  } catch (e) {
    $('#boot').innerHTML = `could not load lab-data.json — run <code>python3 server.py 8765</code> in <code>lab/</code> and open http://localhost:8765/<br><small>${esc(e.message)}</small>`;
    return;
  }
  $('#boot').remove();
  Shell.init(); Shell.badge();
  Facets.build();
  parseQuery('');
  compute(); Facets.update(); Shell.updateCount(); Shell.updateLiveBar();
  const m = ({ wygwyl: 'wyg' })[location.hash.slice(1)] || location.hash.slice(1);
  Shell.setMode(MODES[m] ? m : 'wall');
  if (!Guide.seen()) Guide.show();
  // facet panel slides: re-layout grids once the transition ends
  $('#facets').addEventListener('transitionend', () => { Wall.resize(); Strata.resize(); Facets.drawHue(); });
})();
