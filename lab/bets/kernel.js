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
  K.now = () => A.currentTime || 0;
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
      clip: { id: c.id, title: c.title, year: c.year, thumb: c.thumb, video: c.video, loop: !!c.loop, verdict: c.verdict, score: c.score, fit: c.fit, cat: c.cat },
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
    load() { L.key = FILMKEY(K.code); L.seats = store.get(L.key, null) ?? L.split(); L.seats.sort((a, b) => a.t0 - b.t0); },
    split() {                                                                     // the first version kept one shared ledger: each bet takes back what it made
      const mine = store.get('cineosis.ledger.v1', []).filter(s => s.bet === K.code); store.set(L.key, mine); return mine;
    },
    save(why) { if (L.quiet) { L.dirty = true; return; } L.seats.sort((a, b) => a.t0 - b.t0); store.set(L.key, L.seats); K.stake.decide(why); K.emit('ledger', why); },
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
  addEventListener('storage', e => { if (e.key === L.key) { L.seats = store.get(L.key, []); K.emit('ledger', 'elsewhere'); K.log('film', 'changed in another tab of this bet'); } });

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
  function stakeUI() { const e = document.getElementById('stake'); if (!e || !K.stake.s || !K.data) return; const m = Math.floor(K.stake.s.ms / 60000); e.innerHTML = `<b>${Math.round(100 * L.whole())}%</b> made · ${m} min · ${K.stake.s.decisions} decisions`; }

  /* ---------- clips ---------- */
  const LIVE = new Set(); K.CAP = 8;
  K.loopURL = c => U(`../wygwyl/tempest/${c.id}.mp4`);
  K.media = (c, live) => {
    if (live && c.loop) {
      [...LIVE].forEach(v => { if (!v.isConnected) LIVE.delete(v); });
      if (LIVE.size >= K.CAP) { const old = LIVE.values().next().value; LIVE.delete(old); if (old.isConnected) old.replaceWith(h('img', { src: old.poster, alt: '' })); }
      const v = h('video', { src: K.loopURL(c), poster: c.thumb, muted: true, loop: true, playsinline: true, autoplay: true, preload: 'auto' }); v.muted = true; v.play().catch(() => {}); LIVE.add(v); return v;
    }
    return h('img', { src: c.thumb, alt: '', loading: 'lazy' });
  };
  K.tile = (c, o = {}) => h('div', { class: 'tile' + (o.on ? ' on' : '') + (o.seated ? ' seated' : ''), title: `${c.title}${c.year ? ' · ' + c.year : ''}\n${c.verdict} · score ${c.score} · fit ${c.fit} · ${c.cat}`, onclick: o.onclick, style: o.style },
    K.media(c, o.live), h('span', { class: 'v ' + c.verdict }, o.badge ?? c.verdict[0] + ' ' + c.fit), o.name === false ? null : h('span', { class: 'nm' }, `${c.title}${c.year ? ' ' + c.year : ''}`));

  /* the monitor: the film as the ledger has it, at the playhead */
  K.monitor = (host, o = {}) => {
    const mon = h('div', { class: 'mon' }), cap = h('div', { class: 'cap' }); host.append(mon); let cur;
    const show = t => {
      const s = L.at(t), key = s ? s.id : 'none';
      if (key !== cur) {
        cur = key; mon.replaceChildren();
        if (s) mon.append(K.media(s.clip, true)); else mon.append(h('span', { class: 'none' }, o.empty || 'unmade in this bet'));
        mon.append(cap);
      }
      const w = K.wordAt(t);
      cap.textContent = (s ? (s.by === 'machine' ? '▒ ' : '') + s.clip.title + ' · ' : '') + (w ? w.line.text : '');
    };
    K.on('tick', show); K.on('ledger', () => { cur = null; show(K.now()); }); show(K.now());
    return mon;
  };

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
  K.fire = l => { const b = document.querySelector(`#verbs button[data-l="${l}"]`); if (!b || b.disabled) return; b.classList.add('fire'); setTimeout(() => b.classList.remove('fire'), 160); K.verbs[l]?.do?.(); };

  K.film = null;
  K.setFilm = (n, silent) => {
    K.film = K.filmOf(n) || K.data.films[0];
    document.querySelectorAll('#strip button').forEach(b => b.classList.toggle('on', b.dataset.n === K.film.n));
    document.querySelector(`#strip button[data-n="${K.film.n}"]`)?.scrollIntoView({ inline: 'nearest', block: 'nearest' });
    try { const q = new URLSearchParams(location.search); q.set('film', K.film.n); history.replaceState(null, '', '?' + q); } catch (e) { /* file: */ }
    if (!silent) K.emit('film', K.film);
  };
  function coverage() { document.querySelectorAll('#strip button').forEach(b => { const f = K.filmOf(b.dataset.n); b.querySelector('.cov i').style.width = Math.round(100 * L.cover(f.p0, f.p1)) + '%'; }); reel(document.getElementById('reel')); if (screenOn) reel(document.querySelector('#screen .reel')); stakeUI(); }

  /* the reel: this bet's whole film on one line, the way back to anywhere in it */
  function reel(box) {
    if (!box || !K.data) return; const D = K.duration;
    box.replaceChildren(...K.data.films.map(f => h('span', { class: 'fb', style: `left:${100 * f.t0 / D}%;width:${100 * (f.t1 - f.t0) / D}%` }, f.n)),
      ...L.seats.map(s => h('span', { class: 'rs' + (s.by === 'machine' ? ' m' : ''), style: `left:${100 * s.t0 / D}%;width:${Math.max(.08, 100 * (s.t1 - s.t0) / D)}%;background-image:url("${s.clip.thumb}")` })),
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
        h('div', { class: 'scr' }), h('div', { class: 'reel', onclick: e => { const r = e.currentTarget.getBoundingClientRect(); K.screen(K.duration * (e.clientX - r.left) / r.width); } }));
      document.body.append(sc); K.monitor(sc.querySelector('.scr'), { empty: 'unmade' });
      K.on('tick', t => { if (!screenOn) return; sc.querySelector('.ck').textContent = K.fmt(t); const f = K.filmAt(t); sc.querySelector('.ti').textContent = `${f.n} ${f.title}`; sc.querySelector('.reel .rph').style.left = (100 * t / K.duration) + '%'; });
      A.addEventListener('play', () => sc.querySelector('.pp').innerHTML = K.icon('pause')); A.addEventListener('pause', () => sc.querySelector('.pp').innerHTML = K.icon('play'));
    }
    screenOn = true; sc.classList.remove('hidden'); reel(sc.querySelector('.reel'));
    K.stopRange(); A.currentTime = from ?? K.film.t0; K.play();
    { const f = K.filmAt(A.currentTime); sc.querySelector('.ti').textContent = `${f.n} ${f.title}`; sc.querySelector('.ck').textContent = K.fmt(A.currentTime); }
    K.log('screen', `${K.code} from ${K.fmt(A.currentTime)}`);
  };
  K.unscreen = () => { screenOn = false; K.pause(); document.getElementById('screen')?.classList.add('hidden'); };

  K.boot = async (o) => {
    K.code = o.code; K.verbs = {};
    document.title = `${o.code} ${o.name} · bet studio`;
    document.body.prepend(
      h('div', { id: 'bar' }, h('span', { class: 'ind' }), h('span', { class: 'bet', html: `<b>${K.esc(o.code)}</b>${K.esc(o.name)}` }), h('span', { class: 'claim' }, o.claim), h('span', { class: 'sp' }),
        h('span', { class: 'stake', id: 'stake', title: 'The stake: how much of the film this bet has made, the time you have spent in it, and the decisions you made' }),
        h('span', { class: 'clock', id: 'clock' }, '00:00.0'),
        h('button', { class: 'ic', id: 'playbtn', type: 'button', title: 'Play or pause the voice (space)', 'aria-label': 'Play or pause', html: K.icon('play'), onclick: () => K.toggle() }),
        h('button', { class: 'ic', type: 'button', title: 'Next unmade line (N)', 'aria-label': 'Next unmade line', html: '<svg viewBox="0 0 18 18" width="18" height="18"><path d="M3 4l6 5-6 5M10 4v10M14 4v10" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>', onclick: () => K.nextGap() }),
        h('button', { class: 'ic', type: 'button', title: 'Screen this bet’s film (F)', 'aria-label': 'Screen the film', html: '<svg viewBox="0 0 18 18" width="18" height="18"><path d="M2 3.5h14v9H2zM6 15.5h6" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M7.5 6l4 2-4 2z" fill="currentColor"/></svg>', onclick: () => K.screen() }),
        h('button', { class: 'ic', type: 'button', title: 'The theory of this studio (?)', 'aria-label': 'Theory', html: K.icon('help'), onclick: () => document.getElementById('help').classList.toggle('hidden') }),
        h('a', { class: 'ic', href: './', title: 'All nine bets', 'aria-label': 'All nine bets', html: K.icon('grid') })),
      h('div', { id: 'strip', role: 'tablist', 'aria-label': 'Poems' }),
      h('div', { id: 'reel', title: 'This bet’s whole film. Click to go there.', onclick: reelClick }));
    const stage = document.getElementById('stage') || document.body.appendChild(h('div', { id: 'stage' }));
    document.body.append(stage, h('div', { id: 'tools' }, h('div', { id: 'log' }, 'loading the poem…')), h('div', { id: 'verbs' }));
    o.verbs.forEach(v => { K.verbs[v.l] = v; document.getElementById('verbs').append(h('button', { type: 'button', 'data-l': v.l, title: `${v.l} · ${v.tip || v.v}`, onclick: () => K.fire(v.l) }, h('span', { class: 'L' }, v.l), h('span', { class: 'V' }, v.v))); });
    const hp = o.help || {};
    document.body.append(h('div', { id: 'help', class: 'hidden', role: 'dialog', 'aria-label': 'Theory' },
      h('h3', {}, `${o.code} · ${o.name}`), h('p', {}, hp.bet || o.claim),
      h('dl', {}, o.verbs.map(v => [h('dt', {}, `${v.l}  ${v.v}`), h('dd', {}, v.tip || '')]), (hp.keys || []).map(([k, d]) => [h('dt', {}, k), h('dd', {}, d)])),
      hp.inv ? h('p', { class: 'inv' }, h('b', {}, 'Invariant. '), hp.inv) : null,
      h('p', { class: 'inv mini' }, 'This bet makes its own film, start to finish; no other studio touches it. N jumps to the next unmade line, F screens the film. Her voice is never edited. Seats snap to word edges. One clip per instant. The ranking only advises.')));
    A.addEventListener('play', () => document.getElementById('playbtn').innerHTML = K.icon('pause'));
    A.addEventListener('pause', () => document.getElementById('playbtn').innerHTML = K.icon('play'));
    addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey || e.target.closest?.('input,textarea,select')) return;
      const k = e.key.toUpperCase();
      if (screenOn) {                                                             // while screening, the keys belong to the screening
        if (e.key === ' ') { e.preventDefault(); K.toggle(); }
        else if (e.key === 'Escape' || k === 'F') K.unscreen();
        else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); const i = K.data.films.indexOf(K.filmAt(K.now())) + (e.key === 'ArrowRight' ? 1 : -1); K.screen(K.data.films[Math.max(0, Math.min(K.data.films.length - 1, i))].t0); }
        return;
      }
      if ('ABCDE'.includes(k) && k.length === 1 && K.verbs[k]) { e.preventDefault(); K.fire(k); }
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
    D.films.forEach(f => strip.append(h('button', { type: 'button', role: 'tab', 'data-n': f.n, title: f.title, onclick: () => K.setFilm(f.n) }, h('span', { class: 'n' }, f.n), h('span', { class: 't' }, f.title), h('span', { class: 'cov' }, h('i')))));
    K.on('ledger', coverage); coverage();
    const q = new URLSearchParams(location.search);
    K.setFilm(q.get('film') || '01', true);
    K.log(o.code, `${o.claim} · ${Math.round(100 * L.whole())}% of this bet’s film is made · N next unmade line · F screen it`);
    if (q.get('screen')) setTimeout(() => K.screen(K.film.t0), 50);
    K.on('tick', t => { const p = document.querySelector('#reel .rph'); if (p) p.style.left = (100 * t / K.duration) + '%'; });
    requestAnimationFrame(tick);
    return K;
  };
})();
