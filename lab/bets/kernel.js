/* The kernel every bet studio shares.
 *   <clock>  the suite's 1440.1 s: her voice, never edited (I1)
 *   <word>   2,799 words on that clock, from the readings' word timings
 *   <beat>   88 beats, each with a ranked pool of clips
 *   <seat>   {t0, t1, clip, by, bet, why}: a span of the clock holds a clip
 *   <ledger> the one list of seats every studio reads and writes (I2), live across tabs, mirrored into the
 *            cutting room floor's beat seats so the floor, Tempest, CUT and WAG see the same decisions
 * Invariants the kernel enforces: every seat traces to words (I3: its span is snapped to word edges), one clip at
 * any instant (I4: a new seat trims what it overlaps), and the ranking only advises (I5: machine seats are marked
 * until a person accepts them).
 *   K.boot({code, name, claim, verbs:[{l,v,do,tip}], tools, help}) → Promise<K>
 */
(() => {
  'use strict';
  const HERE = document.currentScript?.src || location.href;
  const U = p => new URL(p, HERE).href;
  const LKEY = 'cineosis.ledger.v1', FKEY = 'floor.seats';
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

  /* ---------- the ledger ---------- */
  const L = K.ledger = {
    seats: [],
    load() { L.seats = store.get(LKEY, []); if (!L.seats.length) L.importFloor(); L.seats.sort((a, b) => a.t0 - b.t0); },
    save(why) { L.seats.sort((a, b) => a.t0 - b.t0); store.set(LKEY, L.seats); L.mirror(); K.emit('ledger', why); },
    all: () => L.seats,
    at: t => L.seats.find(s => t >= s.t0 && t < s.t1) || null,
    in: (t0, t1) => L.seats.filter(s => s.t1 > t0 && s.t0 < t1),
    cover(t0, t1) { let c = 0; L.in(t0, t1).forEach(s => c += Math.min(t1, s.t1) - Math.max(t0, s.t0)); return t1 > t0 ? Math.min(1, c / (t1 - t0)) : 0; },
    seat(o) { const r = K.place(L.seats, o); if (!r) return null; L.seats = r[0]; L.save('seat'); return r[1]; },
    unseat(id) { L.seats = L.seats.filter(s => s.id !== id); L.save('unseat'); },
    clear(t0, t1, pred = () => true) { L.seats = L.seats.filter(s => !(s.t1 > t0 && s.t0 < t1 && pred(s))); L.save('clear'); },
    accept(id) { const s = L.seats.find(x => x.id === id); if (s) { s.by = 'person'; L.save('accept'); } },
    importFloor() {
      const F = store.get(FKEY, {}); if (!K.data) return;
      Object.entries(F).forEach(([bid, c]) => { const b = K.data.byBeat[bid]; if (b && c?.id) L.seats.push({ id: 'f' + bid, t0: b.t0, t1: b.t1, text: K.textOf(b.t0, b.t1), clip: { ...c, loop: K.cands(b.id).some(x => x.id === c.id && x.loop) }, by: 'person', bet: 'floor', why: 'seated on the cutting room floor', at: 0 }); });
      if (L.seats.length) store.set(LKEY, L.seats);
    },
    mirror() {                                                                    // the floor's beat seats follow the ledger
      const F = store.get(FKEY, {});
      K.data.beats.forEach(b => {
        let best = null, ov = 0;
        L.in(b.t0, b.t1).filter(s => s.by === 'person').forEach(s => { const o = Math.min(b.t1, s.t1) - Math.max(b.t0, s.t0); if (o > ov) { ov = o; best = s; } });
        if (best) F[b.id] = { id: best.clip.id, title: best.clip.title, year: best.clip.year, thumb: best.clip.thumb, video: best.clip.video, in: 0, score: best.clip.score, fit: best.clip.fit };
      });
      store.set(FKEY, F);
    },
  };
  addEventListener('storage', e => { if (e.key === LKEY) { L.seats = store.get(LKEY, []); K.emit('ledger', 'elsewhere'); K.log('ledger', 'changed in another studio'); } });

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
        if (s) mon.append(K.media(s.clip, true)); else mon.append(h('span', { class: 'none' }, o.empty || 'unseated'));
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
  function coverage() { document.querySelectorAll('#strip button').forEach(b => { const f = K.filmOf(b.dataset.n); b.querySelector('.cov i').style.width = Math.round(100 * L.cover(f.p0, f.p1)) + '%'; }); }

  K.boot = async (o) => {
    K.code = o.code; K.verbs = {};
    document.title = `${o.code} ${o.name} · bet studio`;
    document.body.prepend(
      h('div', { id: 'bar' }, h('span', { class: 'ind' }), h('span', { class: 'bet', html: `<b>${K.esc(o.code)}</b>${K.esc(o.name)}` }), h('span', { class: 'claim' }, o.claim), h('span', { class: 'sp' }),
        h('span', { class: 'clock', id: 'clock' }, '00:00.0'),
        h('button', { class: 'ic', id: 'playbtn', type: 'button', title: 'Play or pause the voice (space)', 'aria-label': 'Play or pause', html: K.icon('play'), onclick: () => K.toggle() }),
        h('button', { class: 'ic', type: 'button', title: 'The theory of this studio (?)', 'aria-label': 'Theory', html: K.icon('help'), onclick: () => document.getElementById('help').classList.toggle('hidden') }),
        h('a', { class: 'ic', href: './', title: 'All nine bets', 'aria-label': 'All nine bets', html: K.icon('grid') })),
      h('div', { id: 'strip', role: 'tablist', 'aria-label': 'Poems' }));
    const stage = document.getElementById('stage') || document.body.appendChild(h('div', { id: 'stage' }));
    document.body.append(stage, h('div', { id: 'tools' }, h('div', { id: 'log' }, 'loading the poem…')), h('div', { id: 'verbs' }));
    o.verbs.forEach(v => { K.verbs[v.l] = v; document.getElementById('verbs').append(h('button', { type: 'button', 'data-l': v.l, title: `${v.l} · ${v.tip || v.v}`, onclick: () => K.fire(v.l) }, h('span', { class: 'L' }, v.l), h('span', { class: 'V' }, v.v))); });
    const hp = o.help || {};
    document.body.append(h('div', { id: 'help', class: 'hidden', role: 'dialog', 'aria-label': 'Theory' },
      h('h3', {}, `${o.code} · ${o.name}`), h('p', {}, hp.bet || o.claim),
      h('dl', {}, o.verbs.map(v => [h('dt', {}, `${v.l}  ${v.v}`), h('dd', {}, v.tip || '')]), (hp.keys || []).map(([k, d]) => [h('dt', {}, k), h('dd', {}, d)])),
      hp.inv ? h('p', { class: 'inv' }, h('b', {}, 'Invariant. '), hp.inv) : null,
      h('p', { class: 'inv mini' }, 'Every studio writes one ledger. Her voice is never edited. Seats snap to word edges. One clip per instant. The ranking only advises.')));
    A.addEventListener('play', () => document.getElementById('playbtn').innerHTML = K.icon('pause'));
    A.addEventListener('pause', () => document.getElementById('playbtn').innerHTML = K.icon('play'));
    addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey || e.target.closest?.('input,textarea,select')) return;
      const k = e.key.toUpperCase();
      if ('ABCDE'.includes(k) && k.length === 1 && K.verbs[k]) { e.preventDefault(); K.fire(k); }
      else if (e.key === ' ') { e.preventDefault(); (o.space || K.toggle)(); }
      else if (e.key === '?') document.getElementById('help').classList.toggle('hidden');
      else if (e.key === 'Escape') document.getElementById('help').classList.add('hidden');
      else if (o.keys?.[e.key]) { e.preventDefault(); o.keys[e.key](e); }
    });
    const D = await fetch(U('kernel-data.json')).then(r => r.json());
    index(D); A.src = U(D.audio); L.load();
    const strip = document.getElementById('strip');
    D.films.forEach(f => strip.append(h('button', { type: 'button', role: 'tab', 'data-n': f.n, title: f.title, onclick: () => K.setFilm(f.n) }, h('span', { class: 'n' }, f.n), h('span', { class: 't' }, f.title), h('span', { class: 'cov' }, h('i')))));
    K.on('ledger', coverage); coverage();
    const q = new URLSearchParams(location.search);
    K.setFilm(q.get('film') || '01', true);
    K.log(o.code, o.claim);
    requestAnimationFrame(tick);
    return K;
  };
})();
