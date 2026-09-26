/* The kernel every bet studio shares.
 *   <clock>  the suite's 1440.1 s: her voice, never edited (I1)
 *   <word>   2,799 words on that clock, from the readings' word timings
 *   <beat>   88 beats, each with a ranked pool of clips
 *   <seat>   {t0, t1, clip, by, bet, why}: a span of the clock holds a clip
 *   <film>   each bet's own list of seats: a wager is a whole film made one way (I2). Films never mix; the wager
 *            board screens them side by side and the house cut takes the winner of each poem
 *   <stake>  what a bet has cost: active time in its studio and the decisions made
 * Invariants the kernel enforces: every seat traces to words (I3: its span is snapped to word edges), one clip at
 * any instant (I4: a new seat trims what it overlaps), and the ranking only advises (I5: machine seats are marked
 * until a person accepts them).
 *   K.boot({code, name, claim, verbs:[{l,v,do,tip}], tools, help}) → Promise<K>
 */
(() => {
  'use strict';
  const HERE = document.currentScript?.src || location.href;
  const U = p => new URL(p, HERE).href;
  const FILMKEY = c => `cineosis.film.${c}.v1`, STAKEKEY = c => `cineosis.stake.${c}.v1`;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } } };
  const ev = {};
  const K = window.K = {
    on(n, f) { (ev[n] = ev[n] || []).push(f); return K; },
    emit(n, ...a) { (ev[n] || []).forEach(f => { try { f(...a); } catch (e) { console.error(e); } }); },
    fmt(t) { t = Math.max(0, t || 0); const m = Math.floor(t / 60), s = t - m * 60; return `${String(m).padStart(2, '0')}:${s.toFixed(1).padStart(4, '0')}`; },
    esc: s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]),
    h(tag, attrs = {}, ...kids) {
      const e = document.createElement(tag);
      for (const [k, v] of Object.entries(attrs || {})) { if (v == null || v === false) continue; if (k === 'class') e.className = v; else if (k === 'style') e.style.cssText = v; else if (k === 'html') e.innerHTML = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v === true ? '' : v); }
      kids.flat(9).forEach(c => c != null && c !== false && e.append(c.nodeType ? c : document.createTextNode(c))); return e;
    },
  };
  const h = K.h;

  /* ---------- data ---------- */
  K.norm = w => w.toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9']/g, '');
  function index(D) {
    K.data = D; K.duration = D.duration;
    D.words = [];
    D.lines.forEach((l, li) => { l.i = li; l.words.forEach((w, wi) => { w.line = l; w.wi = wi; w.i = D.words.length; w.k = K.norm(w.w); D.words.push(w); }); });
    D.films.forEach(f => { f.lines = D.lines.filter(l => l.film === f.n); f.beats = D.beats.filter(b => b.film === f.n); if (f.lines.length) { f.p0 = f.lines[0].t0; f.p1 = f.lines.at(-1).t1; } else { f.p0 = f.t0; f.p1 = f.t1; } });
    D.byBeat = Object.fromEntries(D.beats.map(b => [b.id, b]));
  }
  const find = (arr, t) => { let lo = 0, hi = arr.length - 1, best = null; while (lo <= hi) { const m = (lo + hi) >> 1; if (arr[m].t0 <= t) { best = arr[m]; lo = m + 1; } else hi = m - 1; } return best && t < best.t1 ? best : null; };
  K.lineAt = t => find(K.data.lines, t);
  K.wordAt = t => find(K.data.words, t);
  K.beatAt = t => K.data.beats.find(b => t >= b.t0 && t < b.t1) || null;
  K.filmAt = t => K.data.films.find(f => t >= f.t0 && t < f.t1) || K.data.films[0];
  K.filmOf = n => K.data.films.find(f => f.n === n);
  K.wordsIn = (t0, t1) => K.data.words.filter(w => w.t1 > t0 + 1e-3 && w.t0 < t1 - 1e-3);
  K.cands = beatId => K.data.pool[beatId] || [];
  K.candsAt = t => { const b = K.beatAt(t); return b ? K.cands(b.id) : []; };
  K.snap = (t0, t1) => { const ws = K.wordsIn(t0, t1); return ws.length ? [ws[0].t0, ws.at(-1).t1] : [t0, t1]; };   // I3
  K.textOf = (t0, t1) => K.wordsIn(t0, t1).map(w => w.w).join(' ');

  /* ---------- the voice ---------- */
  const A = K.audio = new Audio(); A.preload = 'auto';
  let range = null, passes = 0;
  // the voice's own time updates are coarse on some browsers; between them the clock runs on
  let lastA = -1, lastP = 0;
  K.now = () => { const a = A.currentTime || 0, p = performance.now(); if (a !== lastA) { lastA = a; lastP = p; return a; } return A.paused || A.readyState < 3 ? a : a + Math.min(.3, (p - lastP) / 1000 * (A.playbackRate || 1)); };
  K.playing = () => !A.paused;
  K.seek = t => { A.currentTime = Math.max(0, Math.min(K.duration - .05, t)); K.emit('tick', K.now()); };
  K.play = (t0, t1, o = {}) => {
    if (t0 != null) { A.currentTime = Math.max(0, t0); range = t1 != null ? { t0, t1, loop: !!o.loop } : null; passes = 0; }
    A.play().catch(() => K.log('voice', 'tap once to allow sound'));
  };
  K.pause = () => { A.pause(); };
  K.toggle = () => K.playing() ? K.pause() : K.play();
  K.stopRange = () => { range = null; };
  K.range = () => range;
  function tick() {
    const t = K.now();
    if (range && !A.paused && t >= range.t1) {
      if (range.loop) { passes++; A.currentTime = range.t0; K.emit('loop', passes, range); } else { A.pause(); range = null; K.emit('end'); }
    }
    if (!A.paused || tick.last !== t) { tick.last = t; K.emit('tick', t); }
    const bar = document.getElementById('bar'); if (bar) bar.classList.toggle('live', !A.paused);
    const c = document.getElementById('clock'); if (c) c.textContent = `${K.fmt(t)} / ${K.fmt(K.duration)}`;
    requestAnimationFrame(tick);
  }

  /* place a seat into any list of seats (the ledger, or a branch): snap to words (I3), trim overlaps (I4) */
  K.place = (list, o) => {
    let [t0, t1] = o.snap === false ? [o.t0, o.t1] : K.snap(o.t0, o.t1);
    if (!(t1 > t0)) return null;
    const keep = [];
    for (const s of list) {
      if (s.t1 <= t0 || s.t0 >= t1) { keep.push(s); continue; }
      if (s.t0 < t0) keep.push({ ...s, id: s.id + 'a', t1: t0 });
      if (s.t1 > t1) keep.push({ ...s, id: s.id + 'b', t0: t1 });
    }
    const c = o.clip, seat = { id: 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5), t0, t1, text: K.textOf(t0, t1),
      clip: { id: c.id, title: c.title, year: c.year, thumb: c.thumb, video: c.video, loop: !!c.loop, verdict: c.verdict, score: c.score, fit: c.fit, cat: c.cat, sg: c.sg ?? K.clips.get(c.id)?.sg ?? null, in: c.in || 0, dur: c.dur ?? null },
      by: o.by || 'person', bet: o.bet || K.code, why: o.why || '', at: Date.now() };
    return [keep.concat(seat).sort((a, b) => a.t0 - b.t0), seat];
  };
  /* breath points: the pauses inside and between lines where a cut can fall */
  K.breaths = (t0, t1, min = .18) => { const ws = K.wordsIn(t0 - 3, t1 + 3), out = []; for (let i = 1; i < ws.length; i++) { const a = ws[i - 1].t1, b = ws[i].t0; if (b - a >= min && (a + b) / 2 > t0 && (a + b) / 2 < t1) out.push({ t: (a + b) / 2, a, b, len: b - a }); } return out; };
  /* from a word to the end of its phrase: punctuation or a breath */
  K.phraseEnd = w => { const ws = w.line.words; for (let i = w.wi; i < ws.length; i++) { if (/[,.;:!?—]$/.test(ws[i].w) || (ws[i + 1] && ws[i + 1].t0 - ws[i].t1 > .25)) return ws[i].t1; } return ws.at(-1).t1; };

  /* ---------- this bet's film ---------- */
  K.filmKey = FILMKEY;
  K.readFilm = code => store.get(FILMKEY(code), []);
  const L = K.ledger = {
    seats: [], key: null,
    hist: [], prev: '[]',
    load() {
      L.key = FILMKEY(K.code); L.seats = store.get(L.key, null) ?? L.split(); L.seats.sort((a, b) => a.t0 - b.t0);
      const byId = new Map(); Object.values(K.data.pool).forEach(v => v.forEach(c => byId.set(c.id, c)));
      L.seats.forEach(s => { const c = byId.get(s.clip.id); if (c && s.clip.sg == null) Object.assign(s.clip, { sg: c.sg, in: c.in || 0, dur: c.dur }); });   // older seats learn their sign
      L.prev = JSON.stringify(L.seats);
    },
    split() {                                                                     // the first version kept one shared ledger: each bet takes back what it made
      const mine = store.get('cineosis.ledger.v1', []).filter(s => s.bet === K.code); store.set(L.key, mine); return mine;
    },
    save(why) { if (L.quiet) { L.dirty = true; return; } L.seats.sort((a, b) => a.t0 - b.t0); L.hist.push(L.prev); if (L.hist.length > 60) L.hist.shift(); L.prev = JSON.stringify(L.seats); store.set(L.key, L.seats); K.stake.decide(why); K.emit('ledger', why); },
    batch(fn, why = 'batch') { L.quiet = true; try { fn(); } finally { L.quiet = false; if (L.dirty) { L.dirty = false; L.save(why); } } },   // many seats, one save, one decision
    all: () => L.seats,
    at: t => L.seats.find(s => t >= s.t0 && t < s.t1) || null,
    in: (t0, t1) => L.seats.filter(s => s.t1 > t0 && s.t0 < t1),
    cover(t0, t1) { let c = 0; L.in(t0, t1).forEach(s => c += Math.min(t1, s.t1) - Math.max(t0, s.t0)); return t1 > t0 ? Math.min(1, c / (t1 - t0)) : 0; },
    whole() { let c = 0, n = 0; K.data.films.forEach(f => { c += L.cover(f.p0, f.p1) * (f.p1 - f.p0); n += f.p1 - f.p0; }); return n ? c / n : 0; },
    seat(o) { const r = K.place(L.seats, o); if (!r) return null; L.seats = r[0]; L.save('seat'); return r[1]; },
    unseat(id) { L.seats = L.seats.filter(s => s.id !== id); L.save('unseat'); },
    clear(t0, t1, pred = () => true) { L.seats = L.seats.filter(s => !(s.t1 > t0 && s.t0 < t1 && pred(s))); L.save('clear'); },
    accept(id) { const s = L.seats.find(x => x.id === id); if (s) { s.by = 'person'; L.save('accept'); } },
  };
  addEventListener('storage', e => { if (e.key === 'cineosis.bin.v1') { K.bin = new Map(Object.entries(store.get('cineosis.bin.v1', {}))); K.emit('bin'); } if (e.key === L.key) { L.seats = store.get(L.key, []); L.prev = JSON.stringify(L.seats); K.emit('ledger', 'elsewhere'); K.log('film', 'changed in another tab of this bet'); } });

  /* ---------- the stake: what this wager has cost ---------- */
  K.stake = {
    s: null,
    load() { this.s = store.get(STAKEKEY(K.code), { ms: 0, decisions: 0, sessions: 0, started: Date.now() }); this.s.sessions++; this.save(); },
    decide(why) { if (this.s && why && why !== 'elsewhere') { this.s.decisions++; this.save(); } },
    save() { store.set(STAKEKEY(K.code), this.s); stakeUI(); },
  };
  let lastAct = performance.now(), beats = 0;
  ['pointerdown', 'keydown'].forEach(n => addEventListener(n, () => { lastAct = performance.now(); }, true));
  setInterval(() => { const st = K.stake.s; if (!st || document.visibilityState !== 'visible') return; if (performance.now() - lastAct < 60000 || K.playing()) { st.ms += 1000; if (++beats % 10 === 0) K.stake.save(); else stakeUI(); } }, 1000);
  let stT = 0;
  K.stateUI = () => {                                                              // the state of things, in one dense line
    const e = document.getElementById('state'); if (!e || !K.data || !K.film) return;
    const t = K.now(), [a, b] = K.span(), l = K.lineAt((a + b) / 2) || K.lineAt(t), be = K.beatAt((a + b) / 2), kept = L.in(K.film.p0, K.film.p1).length;
    const oth = Object.entries(K.others()).filter(([, ss]) => ss.some(s => s.t1 > a && s.t0 < b)).map(([c]) => c);
    const cell = (k, v) => `<i>${k}</i><b>${v}</b>`;
    e.innerHTML = [cell('poem', `${K.film.n}`), cell('line', l ? `${l.n}/${K.film.lines.length}` : '–'), cell('beat', be ? be.id : '–'), cell('here', L.cover(a, b) > .5 ? 'kept' : K.trying ? 'trying' : 'open'),
      cell('poem made', Math.round(100 * L.cover(K.film.p0, K.film.p1)) + '%'), cell('film made', Math.round(100 * L.whole()) + '%'), cell('seats', kept), cell('★', K.bin.size),
      cell('others here', oth.length ? oth.join(' ') : '–'), cell('min', Math.floor((K.stake.s?.ms || 0) / 60000)), cell('moves', K.stake.s?.decisions || 0)].join('');
  };
  K.on('ledger', () => K.stateUI()); K.on('focus', () => K.stateUI()); K.on('try', () => K.stateUI()); K.on('bin', () => K.stateUI()); K.on('others', () => K.stateUI());
  K.on('tick', () => { const n = performance.now(); if (n - stT > 400) { stT = n; K.stateUI(); } });
  function stakeUI() { K.stateUI?.(); const e = document.getElementById('stake'); if (!e || !K.stake.s || !K.data) return; const m = Math.floor(K.stake.s.ms / 60000); e.innerHTML = `<b>${Math.round(100 * L.whole())}%</b> made · ${m} min · ${K.stake.s.decisions} decisions`; }

  /* ---------- clips ---------- */
  const LIVE = new Set(); K.CAP = 14;
  K.loopURL = c => U(`../wygwyl/tempest/${c.id}.mp4`);
  K.media = (c, live) => {                                                        // the still is always there; a live loop fades in over it once it truly plays
    const img = h('img', { src: c.thumb, alt: '', loading: 'lazy' });
    if (!(live && c.loop)) return img;
    [...LIVE].forEach(v => { if (!v.isConnected) LIVE.delete(v); });
    if (LIVE.size >= K.CAP) { const old = LIVE.values().next().value; LIVE.delete(old); old.remove(); }
    const v = h('video', { src: K.loopURL(c), muted: true, loop: true, playsinline: true, autoplay: true, preload: 'auto' }); v.muted = true;
    v.addEventListener('playing', () => v.classList.add('on'), { once: true }); v.play().catch(() => {}); LIVE.add(v);
    return h('span', { class: 'mw' }, img, v);
  };

  /* ---------- the periodic table's colours: every clip wears its strongest sign's domain ---------- */
  K.DOM = { perception: '#e9d9a8', affect: '#f0b9a4', action: '#e7a37c', reflection: '#b9cfa0', mental: '#a9c9c9', break: '#d9d3c7', time: '#b8b3d8', read: '#d9b8d2' };
  K.signOf = c => { const n = c?.sg, g = n && K.data?.signs[n]; return g ? { n, symbol: g.symbol, name: g.name, dom: g.dom, col: K.DOM[g.dom] || '#ddd' } : { n: null, symbol: '·', name: 'no sign read', dom: null, col: '#ddd' }; };
  K.sa = s => ({ 'data-seat': s.id, 'data-flag': s.flag ? '1' : null, 'data-mute': s.mute ? '1' : null });   // seat attributes: right click, highlight, mute
  K.clips = new Map();
  /* a tile is the clip and nothing else: its sign's colour for a frame, a star if flagged, a dot for each other bet
     that chose it here. Everything else is in the hover title. */
  K.tile = (c, o = {}) => {
    K.clips.set(c.id, c); const g = K.signOf(c);
    const e = h('div', { class: 'tile' + (o.on ? ' on' : '') + (o.seated ? ' seated' : '') + (K.bin.has(c.id) ? ' saved' : ''), 'data-clip': c.id, draggable: 'true', style: `--sg:${g.col};` + (o.style || ''),
      title: `${c.title}${c.year ? ' · ' + c.year : ''}\n${g.symbol} ${g.name}\nclick to try · double click to keep · drag anywhere · right click for more`, onclick: o.onclick, ondblclick: o.ondblclick },
      K.media(c, o.live), h('span', { class: 'pips' }));
    if (o.pips) K.pips(e, o.pips);
    return e;
  };
  K.pips = (e, codes) => { const p = e.querySelector('.pips'); if (p) p.replaceChildren(...(codes || []).map(x => h('i', { title: `${x} chose this here` }, x.replace('P', '')))); };
  K.celebrate = (el, col) => { if (!el) return; el.style.setProperty('--cele', col || 'var(--aB)'); el.classList.remove('cele'); void el.offsetWidth; el.classList.add('cele'); setTimeout(() => el.classList.remove('cele'), 1000); };

  /* a brick: the clip seated on a span, or an empty dashed brick. Drop on it, right click it, click it to go there. */
  K.brick = (t0, t1, o = {}) => { const e = h('span', { class: 'brick', 'data-span': `${t0},${t1}`, title: o.title || '', onclick: o.onclick }); fillBrick(e); return e; };
  function fillBrick(e) {
    const [a, b] = e.dataset.span.split(',').map(Number), s = L.at((a + b) / 2) || L.in(a, b)[0];
    const key = s ? s.id + (s.flag ? 'f' : '') : ''; if (e.dataset.k === key) return; e.dataset.k = key;
    e.replaceChildren(); ['data-seat', 'data-flag', 'data-mute', 'data-clip'].forEach(k => e.removeAttribute(k));
    e.classList.toggle('full', !!s); e.style.setProperty('--sg', s ? K.signOf(s.clip).col : 'transparent');
    if (s) { e.append(h('img', { src: s.clip.thumb, alt: '' })); Object.entries(K.sa(s)).forEach(([k, x]) => x != null && e.setAttribute(k, x)); e.dataset.clip = s.clip.id; K.clips.set(s.clip.id, s.clip); }
  }
  K.on('ledger', () => document.querySelectorAll('.brick[data-span]').forEach(fillBrick));

  /* the other bets' films, read for comparison: what did each of them put here? */
  const OTHERS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'];
  let otherCache = null;
  K.others = () => { if (!otherCache) { otherCache = {}; OTHERS.filter(c => c !== K.code).forEach(c => otherCache[c] = store.get(FILMKEY(c), [])); } return otherCache; };
  K.othersAt = t => { const out = {}; Object.entries(K.others()).forEach(([c, seats]) => { const s = seats.find(x => t >= x.t0 && t < x.t1); if (s) (out[s.clip.id] = out[s.clip.id] || []).push(c); }); return out; };
  addEventListener('storage', e => { if (/^cineosis\.film\./.test(e.key || '')) { otherCache = null; K.emit('others'); } });
  addEventListener('focus', () => { otherCache = null; K.emit('others'); });

  /* layout words placed by time without collisions: a word that would overlap drops to the next row */
  K.layWords = (box, words, X, o = {}) => {
    const rows = []; const rh = o.rowH || 18, max = o.rows || 3;
    words.forEach(w => {
      const e = h('span', { class: o.cls || 'wd2', 'data-i': w.i, style: `left:${X(w.t0)}%`, ...(o.attrs ? o.attrs(w) : {}) }, w.w); box.append(e);
      const L0 = e.offsetLeft, R0 = L0 + e.offsetWidth + 3; let r = rows.findIndex(end => end <= L0); if (r < 0) r = rows.length < max ? rows.length : rows.indexOf(Math.min(...rows));
      rows[r] = R0; e.style.top = (o.top || 0) + r * rh + 'px';
    });
  };

  /* ---------- the saved bin, shared by every bet: clips worth keeping ---------- */
  K.bin = new Map(Object.entries(store.get('cineosis.bin.v1', {})));
  K.save2bin = c => { if (K.bin.has(c.id)) K.bin.delete(c.id); else K.bin.set(c.id, { id: c.id, title: c.title, year: c.year, thumb: c.thumb, video: c.video, loop: c.loop, sg: c.sg, verdict: c.verdict || 'KEEP', score: c.score, fit: c.fit, cat: c.cat, in: c.in, dur: c.dur }); store.set('cineosis.bin.v1', Object.fromEntries(K.bin)); K.emit('bin'); return K.bin.has(c.id); };

  /* ---------- clip sound: the real clip's audio, ducked under her words, mutable per seat ---------- */
  K.clipSound = store.get('cineosis.clipsound', true);
  K.setClipSound = on => { K.clipSound = on; store.set('cineosis.clipsound', on); K.emit('clipsound', on); };
  function clipVideo(c) {
    const v = h('video', { src: c.video || K.loopURL(c), poster: c.thumb, playsinline: true, preload: 'auto' });
    v.addEventListener('error', () => { if (c.loop && !v.dataset.fell) { v.dataset.fell = 1; v.src = K.loopURL(c); v.loop = true; } }, { once: false });
    return v;
  }
  function drive(v, c, s, t, preview) {                                          // keep a real clip near the voice, without fighting it
    if (!v || !c) return;
    const dur = c.dur || v.duration || 10, into = preview != null ? preview : t - s.t0, want = (c.in || 0) + (((into % Math.max(.5, dur)) + dur) % dur);
    const play = K.playing();
    if (!v.dataset.fell && v.readyState >= 1 && !v.seeking) {
      // small drift is taken up by running the clip a touch faster or slower; only a big one jumps
      const d = (v.currentTime || 0) - want, drift = Math.abs(d), rate = A.playbackRate || 1;
      if (drift > (play ? .5 : .15)) { try { v.currentTime = want; } catch (e) { /* not seekable yet */ } v.playbackRate = rate; }
      else if (play && drift > .05) v.playbackRate = rate * Math.max(.9, Math.min(1.1, 1 - d * .5));
      else if (v.playbackRate !== rate) v.playbackRate = rate;
    }
    if (play && v.paused && !v._starting) { v._starting = true; v.play().catch(() => {}).finally(() => { v._starting = false; }); }
    if (!play && !v.paused) v.pause();
    const speaking = !!K.wordAt(t), on = K.clipSound && !(s && s.mute);
    v.muted = !on; v.volume = on ? (speaking ? .22 : .7) : 0;                     // her voice untouched; the clip steps back while she speaks
  }

  K.clipVideo = clipVideo; K.drive = drive;

  /* ---------- the span, the pool, and what is being tried ---------- */
  K.focusSpan = null; K.pickIdx = 0; K.trying = null; K.deckPool = null;
  K.span = () => { if (K.focusSpan) return K.focusSpan; const t = K.now(), l = K.lineAt(t) || K.data.lines.find(x => x.t0 > t) || K.data.lines.at(-1); return [l.t0, l.t1]; };
  K.pool = () => { if (K.deckPool) return K.deckPool; const [a, b] = K.span(), be = K.beatAt((a + b) / 2) || K.beatAt(a); return be ? K.cands(be.id) : []; };
  K.picked = () => K.pool()[K.pickIdx];
  K.focus = (t0, t1) => { const n = t0 == null ? null : [t0, t1]; if (JSON.stringify(n) !== JSON.stringify(K.focusSpan)) { K.focusSpan = n; K.trying = null; K.deckPool = null; K.pickIdx = 0; } K.emit('focus'); };
  K.pick = i => { const p = K.pool(); if (i >= 0 && i < p.length) { K.pickIdx = i; K.trying = p[i]; K.emit('pick', p[i], i); K.emit('try', p[i], i); } };
  K.seatSpanFor = t => { const s = L.at(t); if (s) return [s.t0, s.t1, s]; const w = K.wordAt(t) || K.data.words.find(x => x.t0 > t); return w ? [w.t0, K.phraseEnd(w), null] : null; };
  K.swap = c => {                                                                 // put a clip into the span in focus, or the seat under the playhead
    const [a, b] = K.span(), s = L.at((a + b) / 2);
    if (K.hooks.keep && K.hooks.keep(c, [a, b])) return;
    if (s && !K.focusSpan) { K.ledger.seat({ t0: s.t0, t1: s.t1, clip: c, snap: false, why: `swapped in for ${s.clip.title}` }); K.log('keep', `${c.title} replaces ${s.clip.title}`); }
    else { K.ledger.seat({ t0: a, t1: b, clip: c, why: K.trying === c ? 'kept under the loop' : 'kept' }); K.log('keep', `${c.title} · “${K.textOf(a, b).slice(0, 60)}”`); }
    K.trying = null; K.celebrate(document.querySelector('.dmain'), K.signOf(c).col);
  };
  K.hooks = {};

  /* ---------- the five verbs, the same in every bet: watch, try, keep, flag, on ---------- */
  K.UNI = [
    { l: 'A', v: 'watch', tip: 'Loop the span you are on; press again to pause', do: () => { if (K.playing() && K.range()?.loop) { K.pause(); return; } const [a, b] = K.span(); K.play(a - .15, b + .35, { loop: true }); K.log('watch', `“${K.textOf(a, b).slice(0, 70)}” on repeat`); } },
    { l: 'B', v: 'try', tip: 'The next candidate under the loop', do: () => { const p = K.pool(); if (!p.length) return; const i = K.trying ? (p.indexOf(K.trying) + 1) % p.length : (K.pickIdx + 1) % p.length; K.pick(i); if (!K.playing()) K.UNI[0].do(); K.log('try', `${i + 1}/${p.length} · ${p[i].title}`); } },
    { l: 'C', v: 'keep', tip: 'Seat what is playing on the span', do: () => { const c = K.hooks.pick?.() || K.trying || K.picked(); if (c) K.swap(c); } },
    { l: 'D', v: 'flag', tip: 'Celebrate this clip: noted for later, in every bet', do: () => {
      const [a, b] = K.span(), s = L.at((a + b) / 2), c = K.trying || s?.clip || K.picked(); if (!c) return;
      if (!K.bin.has(c.id)) K.save2bin(c); if (s && s.clip.id === c.id && !s.flag) { s.flag = true; L.save('flag'); }
      K.celebrate(document.querySelector('.dmain'), K.signOf(c).col); K.log('flag', `★ ${c.title} · noted for later · ${K.bin.size} flagged`); } },
    { l: 'E', v: 'on', tip: 'On to the next line (N: the next unmade one)', do: () => {
      const [, b] = K.span(), l = K.data.lines.find(x => x.t0 >= b - .05) || K.data.lines[0], was = K.playing() && K.range()?.loop;
      K.goto(l.t0 + .01); if (was) setTimeout(() => K.UNI[0].do(), 60); } },
  ];

  /* ---------- the deck: the words on top, the clips are the page ---------- */
  K.deck = (host, o = {}) => {
    const strip = o.strip !== false;
    const grid = h('div', { class: 'dgrid' });
    const snd = h('button', { type: 'button', class: 'dic', title: 'Clip sound on or off (S)' }), sav = h('button', { type: 'button', class: 'dic', title: 'Flagged clips, shared by every bet' });
    const deck = h('div', { class: 'deck' + (strip ? '' : ' nostrip') }, grid, h('div', { class: 'dctl' }, strip ? sav : null, snd));   // clips only: nothing above them to wrap and push them around
    host.replaceChildren(deck);
    const main = h('div', { class: 'dmain', draggable: 'true' });
    let cur = null, v = null, shelf = 'beat', tiles = [], poolKey = '', startT = 0, lastWord = null;
    const sndUI = () => { snd.innerHTML = K.clipSound ? '<svg viewBox="0 0 18 18" width="16" height="16"><path d="M3 7h3l4-3v10l-4-3H3z" fill="currentColor"/><path d="M12.5 6.5a3.5 3.5 0 0 1 0 5M14.5 4.5a6 6 0 0 1 0 9" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>' : '<svg viewBox="0 0 18 18" width="16" height="16"><path d="M3 7h3l4-3v10l-4-3H3z" fill="currentColor"/><path d="M12 7l4 4M16 7l-4 4" stroke="currentColor" stroke-width="1.5"/></svg>'; snd.classList.toggle('off', !K.clipSound); };
    snd.onclick = () => K.setClipSound(!K.clipSound); K.on('clipsound', sndUI); sndUI();
    const savUI = () => { sav.textContent = `★${K.bin.size}`; sav.classList.toggle('on', shelf === 'saved'); };
    sav.onclick = () => { shelf = shelf === 'saved' ? 'beat' : 'saved'; savUI(); fill(true); };
    const show = t => {
      const [a, b] = K.span(), s = L.at(t) || (K.focusSpan ? L.at((a + b) / 2) : null), tr = K.trying;
      const c = tr || s?.clip || K.picked();                                       // always footage: what you try, else what is kept, else the first candidate
      const key = c ? (tr ? 't:' : s ? 's:' : 'p:') + c.id + (s?.mute ? 'm' : '') : 'none';
      if (key !== cur) {
        cur = key; startT = t; main.replaceChildren(); v = null;
        main.className = 'dmain' + (s && !tr ? '' : ' loose');                     // loose: playing but not kept (dashed frame, no words about it)
        if (c) { v = clipVideo(c); v.addEventListener('playing', () => v.classList.add('on'), { once: true }); main.append(h('img', { src: c.thumb, alt: '', class: 'still' }), v); main.style.setProperty('--sg', K.signOf(c).col); main.dataset.clip = c.id; K.clips.set(c.id, c); main.title = `${c.title}${c.year ? ' · ' + c.year : ''} · ${K.signOf(c).symbol} ${K.signOf(c).name}${s && !tr ? ' · kept' : ' · not kept yet: C keeps it'}`; if (K.bin.has(c.id)) main.append(h('span', { class: 'star' }, '★')); }
        if (s && !tr) Object.entries(K.sa(s)).forEach(([k, x]) => x == null ? main.removeAttribute(k) : main.setAttribute(k, x)); else ['data-seat', 'data-flag', 'data-mute'].forEach(k => main.removeAttribute(k));
      }
      if (v && c) drive(v, c, s && !tr ? s : { t0: startT }, t, s && !tr ? null : t - startT);
    };
    main.ondblclick = () => { if (K.trying) K.swap(K.trying); };
    const layout = () => {
      const W = grid.clientWidth, H = grid.clientHeight, n = strip ? tiles.length : 0; if (!W || !H) return;
      if (!n) { grid.style.gridTemplateColumns = '1fr'; grid.style.gridAutoRows = (H - 6) + 'px'; main.style.gridColumn = main.style.gridRow = 'auto'; return; }
      let best = null;
      for (let cols = 2; cols <= 8; cols++) for (let m = Math.min(n, 15); m >= 1; m--) {
        const rows = Math.ceil((m + 4) / cols), tw = (W - 6 - 3 * (cols - 1)) / cols, th = Math.min(tw * .75, (H - 6 - 3 * (rows - 1)) / rows);
        if (rows * th + 3 * (rows - 1) + 6 <= H + 1) { const score = th * (m + 6.4); if (!best || score > best.score) best = { cols, m, th, score }; break; }
      }
      grid.style.gridTemplateColumns = `repeat(${best.cols},1fr)`; grid.style.gridAutoRows = Math.floor(best.th) + 'px';
      main.style.gridColumn = 'span 2'; main.style.gridRow = 'span 2';
      tiles.forEach((e, i) => e.hidden = i >= best.m);
    };
    const marks = () => {                                                           // update the tiles in place: no reloading, no flicker
      const [a, b] = K.span(), seated = L.at((a + b) / 2)?.clip.id, oth = K.othersAt((a + b) / 2);
      tiles.forEach((e, i) => { const c = K.deckPool[i]; e.classList.toggle('on', c === K.trying); e.classList.toggle('seated', c.id === seated); e.classList.toggle('saved', K.bin.has(c.id)); K.pips(e, oth[c.id]); });
    };
    const fill = force => {
      const [a, b] = K.span(), be = K.beatAt((a + b) / 2) || K.beatAt(a);
      const pool = shelf === 'saved' ? [...K.bin.values()] : (be ? K.cands(be.id) : []);
      const key = shelf + ':' + pool.map(c => c.id).join(',');
      K.deckPool = pool; if (K.pickIdx >= pool.length) K.pickIdx = 0;
      if (key !== poolKey || force) {
        poolKey = key;
        tiles = strip ? pool.slice(0, 15).map((c, i) => K.tile(c, { live: i < 11, onclick: () => K.pick(i), ondblclick: () => { K.pick(i); K.swap(c); } })) : [];
        grid.replaceChildren(main, ...tiles); layout();
      }
      marks(); savUI(); cur = null; show(K.now());
    };
    new ResizeObserver(layout).observe(grid);
    let lastSpan = '';
    K.on('tick', t => { show(t); if (!K.focusSpan) { const sp = K.span().join(); if (sp !== lastSpan) { lastSpan = sp; K.trying = null; fill(); } } });
    K.on('ledger', () => fill()); K.on('focus', () => fill()); K.on('others', marks); K.on('bin', () => { savUI(); if (shelf === 'saved') fill(true); else marks(); });
    K.on('try', () => { marks(); cur = null; show(K.now()); });
    K.on('clipsound', () => { cur = null; show(K.now()); });
    K.preview = c => { K.trying = c; cur = null; show(K.now()); marks(); };
    if (strip) K.deckStrip = true;
    fill(true);
    return deck;
  };
  K.monitor = (host, o = {}) => K.deck(host, { ...o, strip: false });

  /* ---------- right click: highlight, save, mute, delete, undo ---------- */
  function menu(e) {
    const seatEl = e.target.closest?.('[data-seat]'), clipEl = e.target.closest?.('[data-clip]');
    const s = seatEl && L.seats.find(x => x.id === seatEl.dataset.seat), c = clipEl && (K.clips.get(clipEl.dataset.clip) || K.bin.get(clipEl.dataset.clip));
    const items = [];
    if (s) {
      items.push([s.flag ? 'Unhighlight' : 'Highlight', 'H', () => { s.flag = !s.flag; L.save('highlight'); K.log('highlight', `${s.clip.title} ${s.flag ? 'marked' : 'unmarked'}`); }]);
      items.push([K.bin.has(s.clip.id) ? 'Unsave clip' : 'Save clip', 'S', () => K.log('save', `${s.clip.title} ${K.save2bin({ ...s.clip }) ? 'saved' : 'removed from saved'}`)]);
      items.push([s.mute ? 'Unmute its sound' : 'Mute its sound', 'M', () => { s.mute = !s.mute; L.save('mute'); K.log('sound', `${s.clip.title} ${s.mute ? 'muted' : 'audible'}`); }]);
      items.push(['Delete seat', 'Del', () => { L.unseat(s.id); K.log('delete', `${s.clip.title} removed · Ctrl Z to undo`); }]);
    } else if (c) {
      items.push([K.bin.has(c.id) ? 'Unsave clip' : 'Save clip', 'S', () => K.log('save', `${c.title} ${K.save2bin(c) ? 'saved' : 'removed from saved'}`)]);
      items.push(['Swap in here', '⇄', () => K.swap(c)]);
    }
    items.push(['Undo', 'Ctrl Z', () => K.undo()]);
    e.preventDefault(); closeMenu();
    const m = h('div', { id: 'ctx', role: 'menu' }, (s || c) ? h('div', { class: 'ch' }, (s ? s.clip : c).title.slice(0, 40)) : null,
      items.map(([t, k, f]) => h('button', { type: 'button', role: 'menuitem', onclick: () => { closeMenu(); f(); } }, h('span', {}, t), h('small', {}, k))));
    document.body.append(m); const r = m.getBoundingClientRect();
    m.style.left = Math.min(e.clientX, innerWidth - r.width - 6) + 'px'; m.style.top = Math.min(e.clientY, innerHeight - r.height - 6) + 'px';
  }
  function closeMenu() { document.getElementById('ctx')?.remove(); }
  addEventListener('contextmenu', menu); addEventListener('pointerdown', e => { if (!e.target.closest?.('#ctx')) closeMenu(); }, true);

  /* ---------- drag a clip anywhere: onto a word, a seat, a span, a timeline, the deck ---------- */
  const DROP = '[data-seat],[data-span],[data-tl0],.wd[data-i],.wd2[data-i],.tw[data-i],.dmain';
  addEventListener('mousedown', e => { const c = e.target.closest?.('[data-clip]'); if (c && !c.draggable) c.draggable = true; }, true);
  addEventListener('dragstart', e => { const c = e.target.closest?.('[data-clip]'); if (!c) return; e.dataTransfer.setData('text/plain', 'clip:' + c.dataset.clip); e.dataTransfer.effectAllowed = 'copy'; document.body.classList.add('dragging'); });
  addEventListener('dragend', () => { document.body.classList.remove('dragging'); document.querySelectorAll('.dropok').forEach(x => x.classList.remove('dropok')); });
  addEventListener('dragover', e => { const t = e.target.closest?.(DROP); document.querySelectorAll('.dropok').forEach(x => x !== t && x.classList.remove('dropok')); if (!t) return; e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; t.classList.add('dropok'); });
  addEventListener('drop', e => {
    const t = e.target.closest?.(DROP), d = e.dataTransfer.getData('text/plain'); document.body.classList.remove('dragging'); document.querySelectorAll('.dropok').forEach(x => x.classList.remove('dropok'));
    if (!t || !d.startsWith('clip:')) return; e.preventDefault();
    const id = d.slice(5), c = K.clips.get(id) || K.bin.get(id) || Object.values(K.data.pool).flat().find(x => x.id === id); if (!c) return;
    let span = null;
    if (t.dataset.seat) { const s = L.seats.find(x => x.id === t.dataset.seat); if (s) span = [s.t0, s.t1, false]; }
    else if (t.dataset.span) { const [a, b] = t.dataset.span.split(',').map(Number); span = [a, b, true]; }
    else if (t.dataset.tl0 != null) { const r = t.getBoundingClientRect(), tt = +t.dataset.tl0 + (+t.dataset.tl1 - +t.dataset.tl0) * (e.clientX - r.left) / r.width, x = K.seatSpanFor(tt); if (x) span = [x[0], x[1], !x[2]]; }
    else if (t.dataset.i != null) { const w = K.data.words[+t.dataset.i]; if (w) span = [w.t0, K.phraseEnd(w), true]; }
    else if (t.classList.contains('dmain')) { K.swap(c); return; }
    if (!span) return;
    if (K.hooks.keep && K.hooks.keep(c, span)) return;
    K.ledger.seat({ t0: span[0], t1: span[1], clip: c, snap: span[2], why: 'dropped here' });
    K.log('drop', `${c.title} · “${K.textOf(span[0], span[1]).slice(0, 60)}”`); K.celebrate(t, K.signOf(c).col);
  });

  /* ---------- undo ---------- */
  K.undo = () => { const snap = L.hist.pop(); if (!snap) return K.log('undo', 'nothing to undo'); L.seats = JSON.parse(snap); L.prev = snap; store.set(L.key, L.seats); K.emit('ledger', 'undo'); K.log('undo', `back one step · ${L.hist.length} more`); };

  /* ---------- the shared record: every bet's film as one EDL format ---------- */
  const FPS = 25, tc = t => { const f = Math.round(Math.max(0, t) * FPS), hh = Math.floor(f / (3600 * FPS)), mm = Math.floor(f / (60 * FPS)) % 60, ss = Math.floor(f / FPS) % 60, ff = f % FPS; return [hh, mm, ss, ff].map(x => String(x).padStart(2, '0')).join(':'); };
  K.edl = {
    json(seats, bet) {
      return { format: 'cineosis-edl/1', title: 'WYGWYL', bet, made: new Date().toISOString(), clock: { audio: 'WYGWYL_Suite_Audio.mp3', duration: K.duration, fps: FPS },
        events: seats.map((s, i) => ({ n: i + 1, rec: [+s.t0.toFixed(3), +s.t1.toFixed(3)], words: s.text, clip: { id: s.clip.id, title: s.clip.title, year: s.clip.year, video: s.clip.video, thumb: s.clip.thumb, sg: s.clip.sg, loop: s.clip.loop },
          src: [+(s.clip.in || 0).toFixed(3), +((s.clip.in || 0) + s.t1 - s.t0).toFixed(3)], by: s.by, bet: s.bet, why: s.why, flag: !!s.flag, mute: !!s.mute })) };
    },
    cmx(seats, bet) {
      const out = [`TITLE: WYGWYL ${bet}`, 'FCM: NON-DROP FRAME', ''];
      seats.forEach((s, i) => { const a = s.clip.in || 0, g = K.signOf(s.clip);
        out.push(`${String(i + 1).padStart(3, '0')}  AX       V     C        ${tc(a)} ${tc(a + s.t1 - s.t0)} ${tc(s.t0)} ${tc(s.t1)}`,
          `* FROM CLIP NAME: ${s.clip.title}${s.clip.year ? ' (' + s.clip.year + ')' : ''}`, `* SOURCE FILE: ${s.clip.video || ''}`,
          `* WORDS: ${s.text}`, `* SIGN: ${g.symbol} ${g.name}${s.mute ? ' · CLIP SOUND MUTED' : ''}`, ''); });
      return out.join('\n');
    },
    seatsOf(src) {                                                                 // another bet's film, or the house cut
      if (src !== 'HOUSE') return store.get(FILMKEY(src), []);
      const house = store.get('cineosis.house.v1', {}), out = [];
      K.data.films.forEach(f => { const c = house[f.n]; if (c) store.get(FILMKEY(c), []).forEach(s => { if (s.t1 > f.t0 && s.t0 < f.t1) out.push(s); }); });
      return out;
    },
    take(seats, t0, t1, from) { let n = 0; L.batch(() => seats.filter(s => s.t1 > t0 && s.t0 < t1).forEach(s => { K.ledger.seat({ t0: Math.max(t0, s.t0), t1: Math.min(t1, s.t1), clip: s.clip, snap: false, by: s.by, why: `from ${from} · ${s.why || ''}` }); n++; }), 'take'); return n; },
    download(name, text, type) { const a = h('a', { href: URL.createObjectURL(new Blob([text], { type })), download: name }); document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); },
  };
  function edlPanel() {
    let p = document.getElementById('edlp'); if (p) { p.remove(); return; }
    const bets = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'HOUSE'].filter(b => b !== K.code);
    const from = h('select', { id: 'edlFrom', 'aria-label': 'Take from' }, bets.map(b => h('option', { value: b }, `${b} · ${Math.round(100 * coverOf(K.edl.seatsOf(b)))}% made`)));
    const scope = h('select', { id: 'edlScope', 'aria-label': 'How much' }, h('option', { value: 'poem' }, `this poem (${K.film.n})`), h('option', { value: 'film' }, 'the whole film'));
    const file = h('input', { type: 'file', accept: '.json,application/json', id: 'edlFile', class: 'hidden', onchange: e => { const f = e.target.files[0]; if (!f) return; f.text().then(txt => { try { const j = JSON.parse(txt); if (j.format !== 'cineosis-edl/1') throw new Error('not a cineosis EDL'); const seats = j.events.map(ev => ({ t0: ev.rec[0], t1: ev.rec[1], clip: ev.clip, by: ev.by, why: ev.why })); const n = K.edl.take(seats, 0, K.duration, `${j.bet} EDL`); K.log('import', `${n} events from ${f.name}`); } catch (err) { K.log('import', `could not read ${f.name}: ${err.message}`); } }); } });
    p = h('div', { id: 'edlp', role: 'dialog', 'aria-label': 'Edit decision list' },
      h('h3', {}, `${K.code} · edit decision list`), h('p', {}, `${L.seats.length} events · ${Math.round(100 * L.whole())}% of the film. One record format for every bet, so any film can be shared, compared, or finished in an editor.`),
      h('div', { class: 'erow' }, h('button', { type: 'button', onclick: () => K.edl.download(`wygwyl-${K.code}.cineosis-edl.json`, JSON.stringify(K.edl.json(L.seats, K.code), null, 1), 'application/json') }, 'Export EDL · JSON'),
        h('button', { type: 'button', onclick: () => K.edl.download(`wygwyl-${K.code}.edl`, K.edl.cmx(L.seats, K.code), 'text/plain') }, 'Export CMX3600 .edl'),
        h('button', { type: 'button', onclick: () => file.click() }, 'Import EDL'), file),
      h('div', { class: 'erow' }, h('span', {}, 'Take from'), from, scope, h('button', { type: 'button', onclick: () => {
        const src = from.value, seats = K.edl.seatsOf(src), [t0, t1] = scope.value === 'poem' ? [K.film.t0, K.film.t1] : [0, K.duration];
        const n = K.edl.take(seats, t0, t1, src); K.log('take', `${n} events from ${src} into ${K.code} · Ctrl Z to undo`); p.remove(); } }, 'Take')),
      h('p', { class: 'mini' }, 'Taking overwrites this bet’s seats where they overlap. Ctrl Z undoes it.'));
    document.body.append(p);
  }
  function coverOf(seats) { let c = 0, n = 0; K.data.films.forEach(f => { let x = 0; seats.forEach(s => { if (s.t1 > f.p0 && s.t0 < f.p1) x += Math.min(f.p1, s.t1) - Math.max(f.p0, s.t0); }); c += Math.min(x, f.p1 - f.p0); n += f.p1 - f.p0; }); return n ? c / n : 0; }
  K.edlPanel = edlPanel;

  /* ---------- chrome ---------- */
  const IC = {
    play: '<path d="M5 3.5l9 5.5-9 5.5z" fill="currentColor"/>',
    pause: '<path d="M5 3.5h3v11H5zM10 3.5h3v11h-3z" fill="currentColor"/>',
    help: '<circle cx="9" cy="9" r="7" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M6.6 6.8a2.4 2.4 0 1 1 3.2 2.3c-.5.2-.8.6-.8 1.2v.4" fill="none" stroke="currentColor" stroke-width="1.5"/><circle cx="9" cy="13.4" r=".9" fill="currentColor"/>',
    grid: '<path d="M3 3h5v5H3zM10 3h5v5h-5zM3 10h5v5H3zM10 10h5v5h-5z" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    prev: '<path d="M12 4L6 9l6 5" fill="none" stroke="currentColor" stroke-width="1.8"/>',
    next: '<path d="M6 4l6 5-6 5" fill="none" stroke="currentColor" stroke-width="1.8"/>',
    loop: '<path d="M4 7a4 4 0 0 1 4-3h4l-2-2M14 11a4 4 0 0 1-4 3H6l2 2" fill="none" stroke="currentColor" stroke-width="1.6"/>',
    undo: '<path d="M6 5L3 8l3 3M3 8h8a4 4 0 0 1 0 8H8" fill="none" stroke="currentColor" stroke-width="1.6"/>',
  };
  K.icon = (n, s = 18) => `<svg viewBox="0 0 18 18" width="${s}" height="${s}">${IC[n] || n}</svg>`;
  K.log = (verb, text) => { const l = document.getElementById('log'); if (l) l.innerHTML = `<b>${K.esc(verb)}</b> · ${K.esc(text)}`; };
  K.tools = (...groups) => { const t = document.getElementById('tools'); groups.forEach(g => t.insertBefore(h('div', { class: 'tool-grp' }, g.map(b => h('button', { type: 'button', title: b.tip || b.t, 'aria-label': b.tip || b.t, class: b.on ? 'on' : '', id: b.id, onclick: b.do, html: (b.icon ? K.icon(b.icon, 16) : '') + (b.t ? `<span>${K.esc(b.t)}</span>` : '') }))), document.getElementById('log'))); };
  K.fire = l => { const b = document.querySelector(`#verbs button[data-l="${l}"]`); if (b) { b.classList.add('fire'); setTimeout(() => b.classList.remove('fire'), 160); } K.verbs[l]?.do?.(); };
  K.fireOwn = l => { const b = document.querySelector(`#own button[data-l="${l}"]`); if (b) { b.classList.add('on'); setTimeout(() => b.classList.remove('on'), 160); } K.own[l]?.do?.(); };

  K.film = null;
  K.setFilm = (n, silent) => {
    K.film = K.filmOf(n) || K.data.films[0];
    document.querySelectorAll('#strip button').forEach(b => b.classList.toggle('on', b.dataset.n === K.film.n));
    document.querySelector(`#strip button[data-n="${K.film.n}"]`)?.scrollIntoView({ inline: 'nearest', block: 'nearest' });
    try { const q = new URLSearchParams(location.search); q.set('film', K.film.n); history.replaceState(null, '', '?' + q); } catch (e) { /* file: */ }
    if (!silent) K.emit('film', K.film);
  };
  function coverage() {
    document.querySelectorAll('#strip button').forEach(b => {                     // each poem tab carries its own little film
      const f = K.filmOf(b.dataset.n), mr = b.querySelector('.mr'), X = t => 100 * (t - f.t0) / (f.t1 - f.t0);
      const own = L.in(f.p0, f.p1), rep = own[0]?.clip || K.cands(f.beats.find(x => x.t1 > f.p0)?.id)[0];   // the poem as a clip: its first kept clip, else its best candidate
      if (rep) { b.style.backgroundImage = `url("${rep.thumb}")`; b.style.setProperty('--sg', K.signOf(rep).col); b.classList.toggle('made', !!own.length); }
      b.title = `${f.n} ${f.title} · ${Math.round(100 * L.cover(f.p0, f.p1))}% made`;
      mr.replaceChildren(...own.map(s => h('span', { style: `left:${X(Math.max(f.t0, s.t0))}%;width:${Math.max(.6, X(Math.min(f.t1, s.t1)) - X(Math.max(f.t0, s.t0)))}%;background:${K.signOf(s.clip).col}` })), h('b', { class: 'mph' }));
    }); if (screenOn) reel(document.querySelector('#screen .reel')); stakeUI(); }

  /* the reel: this bet's whole film on one line, the way back to anywhere in it */
  function reel(box) {
    if (!box || !K.data) return; const D = K.duration;
    box.replaceChildren(...K.data.films.map(f => h('span', { class: 'fb', style: `left:${100 * f.t0 / D}%;width:${100 * (f.t1 - f.t0) / D}%` }, f.n)),
      ...L.seats.map(s => h('span', { class: 'rs' + (s.by === 'machine' ? ' m' : ''), ...K.sa(s), style: `left:${100 * s.t0 / D}%;width:${Math.max(.08, 100 * (s.t1 - s.t0) / D)}%;background-image:url("${s.clip.thumb}");--sg:${K.signOf(s.clip).col}`, title: `${s.clip.title} · ${s.text}` })),
      h('span', { class: 'rph' }));
  }
  function reelClick(e) { const r = e.currentTarget.getBoundingClientRect(); K.goto(K.duration * (e.clientX - r.left) / r.width); }

  /* go anywhere: change poem if needed, move the voice, and let the studio select that line */
  K.goto = t => {
    const f = K.filmAt(t); if (f.n !== K.film.n) K.setFilm(f.n);
    const l = K.lineAt(t) || K.data.lines.find(x => x.t0 >= t && x.film === f.n) || f.lines.at(-1);
    K.seek(t); if (l) K.emit('goto', l, t);
  };
  K.nextGap = () => {
    const t = K.now(), open = x => L.cover(x.t0, x.t1) < .5;
    const l = K.data.lines.find(x => x.t0 > t + .05 && open(x)) || K.data.lines.find(open);
    if (!l) return K.log('gap', 'this bet has made the whole film. Screen it (F).');
    K.goto(l.t0); K.log('gap', `${l.film} · L${l.n} is the next unmade line · ${Math.round(100 * L.whole())}% of the film made`);
  };
  /* moving past the last line of a poem goes on to the next poem */
  K.advance = () => { const i = K.data.films.indexOf(K.film); if (i < K.data.films.length - 1) { K.setFilm(K.data.films[i + 1].n); K.log('next poem', `${K.film.n} ${K.film.title}`); return true; } return false; };

  /* the screening: this bet's film, full screen, from the start of the poem */
  let screenOn = false;
  K.screen = from => {
    let sc = document.getElementById('screen');
    if (!sc) {
      sc = h('div', { id: 'screen', role: 'dialog', 'aria-label': 'Screening' },
        h('div', { class: 'top' }, h('b', {}, K.code), h('span', { class: 'ti' }), h('span', { class: 'sp2' }), h('span', { class: 'ck' }),
          h('button', { type: 'button', title: 'Previous poem', html: K.icon('prev'), onclick: () => K.screen(K.data.films[Math.max(0, K.data.films.indexOf(K.filmAt(K.now())) - 1)].t0) }),
          h('button', { type: 'button', title: 'Play or pause', class: 'pp', html: K.icon('pause'), onclick: () => K.toggle() }),
          h('button', { type: 'button', title: 'Next poem', html: K.icon('next'), onclick: () => K.screen(K.data.films[Math.min(K.data.films.length - 1, K.data.films.indexOf(K.filmAt(K.now())) + 1)].t0) }),
          h('button', { type: 'button', title: 'Back to the studio (Esc)', class: 'x', html: '<svg viewBox="0 0 18 18" width="18" height="18"><path d="M4 4l10 10M14 4L4 14" stroke="currentColor" stroke-width="2"/></svg>', onclick: () => K.unscreen() })),
        h('div', { class: 'scr' }), h('div', { class: 'scap' }), h('div', { class: 'reel', onclick: e => { const r = e.currentTarget.getBoundingClientRect(); K.screen(K.duration * (e.clientX - r.left) / r.width); } }));
      document.body.append(sc); K.monitor(sc.querySelector('.scr'), { empty: 'unmade' });
      K.on('tick', t => { if (!screenOn) return; sc.querySelector('.ck').textContent = K.fmt(t); const w = K.wordAt(t) || K.wordAt(t + .3), cp = sc.querySelector('.scap'), k = w ? w.i : -1; if (cp.dataset.k != k) { cp.dataset.k = k; cp.innerHTML = w ? w.line.words.map(x => x === w ? `<b>${K.esc(x.w)}</b>` : K.esc(x.w)).join(' ') : ''; } const f = K.filmAt(t); sc.querySelector('.ti').textContent = `${f.n} ${f.title}`; sc.querySelector('.reel .rph').style.left = (100 * t / K.duration) + '%'; });
      A.addEventListener('play', () => sc.querySelector('.pp').innerHTML = K.icon('pause')); A.addEventListener('pause', () => sc.querySelector('.pp').innerHTML = K.icon('play'));
    }
    screenOn = true; sc.classList.remove('hidden'); reel(sc.querySelector('.reel'));
    K.stopRange(); A.currentTime = from ?? K.film.t0; K.play();
    { const f = K.filmAt(A.currentTime); sc.querySelector('.ti').textContent = `${f.n} ${f.title}`; sc.querySelector('.ck').textContent = K.fmt(A.currentTime); }
    K.log('screen', `${K.code} from ${K.fmt(A.currentTime)}`);
  };
  K.unscreen = () => { screenOn = false; K.pause(); document.getElementById('screen')?.classList.add('hidden'); };

  /* the panes are windows you size: drag a divider, double click it to share evenly; each studio remembers */
  function splitters() {
    const stage = document.getElementById('stage'), panes = [...stage.children].filter(e => e.classList.contains('pane')); if (panes.length < 2) return;
    const key = `bets.layout.${K.code}`, saved = store.get(key, null);
    panes.forEach((p, i) => { if (i < panes.length - 1) p.after(h('div', { class: 'gut', role: 'separator', 'aria-orientation': 'vertical', title: 'Drag to resize · double click to reset' })); });
    const apply = ws => panes.forEach((p, i) => { p.style.flex = ws && ws[i] != null ? `0 0 ${ws[i]}%` : ''; });
    if (saved && saved.length === panes.length) apply(saved);
    else { const d = panes.findIndex(p => p.querySelector('.body#monHost,.body#monHost2')); if (d >= 0) { const ws = panes.map(() => null); ws[d] = 44; apply(ws.map((w, i) => w ?? (56 / (panes.length - 1)))); } }   // the videos get the room by default
    stage.querySelectorAll('.gut').forEach((g, i) => {
      g.addEventListener('pointerdown', e => {
        e.preventDefault(); g.setPointerCapture(e.pointerId); const W = stage.clientWidth, a = panes[i], b = panes[i + 1], wa = a.offsetWidth, wb = b.offsetWidth, x0 = e.clientX;
        const move = ev => { const d = ev.clientX - x0, na = Math.max(160, Math.min(wa + wb - 160, wa + d)); a.style.flex = `0 0 ${100 * na / W}%`; b.style.flex = `0 0 ${100 * (wa + wb - na) / W}%`; };
        const up = () => { g.removeEventListener('pointermove', move); g.removeEventListener('pointerup', up); store.set(key, panes.map(p => 100 * p.offsetWidth / W)); };
        g.addEventListener('pointermove', move); g.addEventListener('pointerup', up);
      });
      g.addEventListener('dblclick', () => { store.set(key, null); panes.forEach(p => p.style.flex = `1 1 0`); });
    });
  }

  K.boot = async (o) => {
    K.code = o.code; K.verbs = {};
    document.title = `${o.code} ${o.name} · bet studio`;
    document.body.prepend(
      h('div', { id: 'bar' }, h('span', { class: 'ind' }), h('span', { class: 'bet', title: o.claim, html: `<b>${K.esc(o.code)}</b>${K.esc(o.name)}` }), h('span', { class: 'state', id: 'state' }), h('span', { class: 'sp' }),
        h('span', { class: 'clock', id: 'clock' }, '00:00.0'),
        h('button', { class: 'ic', id: 'playbtn', type: 'button', title: 'Play or pause the voice (space)', 'aria-label': 'Play or pause', html: K.icon('play'), onclick: () => K.toggle() }),
        h('button', { class: 'ic wide', type: 'button', title: 'Edit decision list: export, import, take from another bet (E is a verb, so this is the L key)', 'aria-label': 'Edit decision list', onclick: () => edlPanel() }, 'EDL'),
        h('button', { class: 'ic', type: 'button', title: 'Next unmade line (N)', 'aria-label': 'Next unmade line', html: '<svg viewBox="0 0 18 18" width="18" height="18"><path d="M3 4l6 5-6 5M10 4v10M14 4v10" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>', onclick: () => K.nextGap() }),
        h('button', { class: 'ic', type: 'button', title: 'Screen this bet’s film (F)', 'aria-label': 'Screen the film', html: '<svg viewBox="0 0 18 18" width="18" height="18"><path d="M2 3.5h14v9H2zM6 15.5h6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M7.5 6l4 2-4 2z" fill="currentColor"/></svg>', onclick: () => K.screen() }),
        h('button', { class: 'ic', type: 'button', title: 'The theory of this studio (?)', 'aria-label': 'Theory', html: K.icon('help'), onclick: () => document.getElementById('help').classList.toggle('hidden') }),
        h('a', { class: 'ic', href: './', title: 'All nine bets', 'aria-label': 'All nine bets', html: K.icon('grid') })),
      h('div', { id: 'strip', role: 'tablist', 'aria-label': 'Poems' }));
    const stage = document.getElementById('stage') || document.body.appendChild(h('div', { id: 'stage' }));
    document.body.append(stage, h('div', { id: 'tools' }, h('div', { id: 'log' }, 'loading the poem…')), h('div', { id: 'verbs' }));
    K.UNI.forEach(v => { K.verbs[v.l] = v; document.getElementById('verbs').append(h('button', { type: 'button', 'data-l': v.l, title: `${v.l} · ${v.tip}`, onclick: () => K.fire(v.l) }, h('span', { class: 'L' }, v.l), h('span', { class: 'V' }, v.v))); });
    K.own = {}; const own = h('div', { class: 'tool-grp', id: 'own', title: `${o.name}’s own moves: Shift + letter` });
    o.verbs.forEach(v => { K.own[v.l] = v; own.append(h('button', { type: 'button', 'data-l': v.l, title: `Shift ${v.l} · ${v.tip || v.v}`, onclick: () => K.fireOwn(v.l) }, h('b', {}, v.l), ' ', v.v)); });
    document.getElementById('tools').prepend(own);
    const hp = o.help || {};
    document.body.append(h('div', { id: 'help', class: 'hidden', role: 'dialog', 'aria-label': 'Theory' },
      h('h3', {}, `${o.code} · ${o.name}`), h('p', {}, hp.bet || o.claim),
      h('dl', {}, K.UNI.map(v => [h('dt', {}, `${v.l}  ${v.v}`), h('dd', {}, v.tip)]), o.verbs.map(v => [h('dt', {}, `⇧${v.l}  ${v.v}`), h('dd', {}, v.tip || '')]), (hp.keys || []).map(([k, d]) => [h('dt', {}, k), h('dd', {}, d)])),
      hp.inv ? h('p', { class: 'inv' }, h('b', {}, 'Invariant. '), hp.inv) : null,
      h('p', { class: 'inv mini' }, 'This bet makes its own film, start to finish; no other studio touches it. N next unmade line · F screen the film · S clip sound on or off · L the EDL: export JSON or CMX3600, import, or take a poem from another bet · right click a clip or seat: highlight, save, mute, delete, undo · Ctrl Z undo · 1–9 pick from the deck, double click to swap it in. Clips wear their strongest sign’s colour from the periodic table. Her voice is never edited; clip sound steps back while she speaks.')));
    A.addEventListener('play', () => document.getElementById('playbtn').innerHTML = K.icon('pause'));
    A.addEventListener('pause', () => document.getElementById('playbtn').innerHTML = K.icon('play'));
    addEventListener('keydown', e => {
      const k = e.key.toUpperCase();
      if ((e.metaKey || e.ctrlKey) && k === 'Z' && !e.target.closest?.('input,textarea')) { e.preventDefault(); K.undo(); return; }
      if (e.metaKey || e.ctrlKey || e.altKey || e.target.closest?.('input,textarea,select')) return;
      if (screenOn) {                                                             // while screening, the keys belong to the screening
        if (e.key === ' ') { e.preventDefault(); K.toggle(); }
        else if (e.key === 'Escape' || k === 'F') K.unscreen();
        else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); const i = K.data.films.indexOf(K.filmAt(K.now())) + (e.key === 'ArrowRight' ? 1 : -1); K.screen(K.data.films[Math.max(0, Math.min(K.data.films.length - 1, i))].t0); }
        return;
      }
      if ((e.metaKey || e.ctrlKey) && k === 'Z') { e.preventDefault(); K.undo(); return; }
      if ('ABCDE'.includes(k) && e.key.length === 1 && e.shiftKey && K.own[k]) { e.preventDefault(); K.fireOwn(k); }
      else if ('ABCDE'.includes(k) && e.key.length === 1 && K.verbs[k]) { e.preventDefault(); K.fire(k); }
      else if (/^[1-9]$/.test(e.key) && !o.keys?.[e.key]) { e.preventDefault(); K.pick(+e.key - 1); }
      else if (k === 'S' && e.key.length === 1) { e.preventDefault(); K.setClipSound(!K.clipSound); K.log('clip sound', K.clipSound ? 'on, ducked under her words' : 'off'); }
      else if (k === 'L' && e.key.length === 1) { e.preventDefault(); edlPanel(); }
      else if (e.key === ' ') { e.preventDefault(); (o.space || K.toggle)(); }
      else if (e.key === '?') document.getElementById('help').classList.toggle('hidden');
      else if (e.key === 'Escape') document.getElementById('help').classList.add('hidden');
      else if (e.key === 'n' || e.key === 'N') { e.preventDefault(); K.nextGap(); }
      else if (e.key === 'f' || e.key === 'F') { e.preventDefault(); K.screen(); }
      else if (o.keys?.[e.key]) { e.preventDefault(); o.keys[e.key](e); }
    });
    const D = await fetch(U('kernel-data.json')).then(r => r.json());
    index(D); A.src = U(D.audio); L.load(); K.stake.load();
    const strip = document.getElementById('strip');
    D.films.forEach(f => strip.append(h('button', { type: 'button', role: 'tab', 'data-n': f.n, title: f.title, onclick: () => K.setFilm(f.n) }, h('span', { class: 'n' }, f.n), h('span', { class: 't' }, f.title), h('span', { class: 'mr', 'data-tl0': f.t0, 'data-tl1': f.t1 }))));
    K.on('ledger', coverage); coverage();
    const q = new URLSearchParams(location.search);
    K.setFilm(q.get('film') || '01', true);
    K.log(o.code, `${o.claim} · ${Math.round(100 * L.whole())}% of this bet’s film is made · N next unmade line · F screen it`);
    splitters();
    if (q.get('screen')) setTimeout(() => K.screen(K.film.t0), 50);
    // one clock for the lab: arrive from another tool mid-film and carry on; open side by side and follow the one playing
    else { const cs = document.createElement('script'); cs.src = U('../clock.js?v=2'); cs.onload = () => window.LabClock && LabClock.attach({ name: o.code + ' ' + o.name, audio: A, play: () => K.play(), pause: () => K.pause(), seek: t => K.goto(t) }); document.head.append(cs); }
    K.on('tick', t => { const f = K.film, p = document.querySelector(`#strip button[data-n="${f.n}"] .mph`); if (p) p.style.left = (100 * (t - f.t0) / (f.t1 - f.t0)) + '%'; });
    requestAnimationFrame(tick);
    return K;
  };
})();
