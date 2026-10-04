/* THE GRAND EDITING MACHINE: a Monte Carlo tree search that directs a film from the archive, one piece at a time.
   1 Selection    from the timeline so far (the root), walk down the tree by UCT, Q + c·sqrt(ln N / n): promise balanced with curiosity.
   2 Expansion    at the edge of the tree, open one new branch: a next piece from the top-K the archive offers here (by CLIP embedding,
                  the judge's score, and the story: the beat it plays, the pictures that answer the card before it).
   3 Rollout      imagine the rest of the film from there, quickly and a little by chance, and hand the whole of it to the critic.
   4 Backprop     the critic's reward (the fixed critic of monte/sim.js) flows back up every branch that led to it.
   After `iters` searches the most-visited piece is committed, the tree is re-rooted there, and the search goes on until The End.
   Material: monte/material.json loaded by monte/sim.js. Runs in node (monte/mcts_run.js) and in the browser (mcts.html). */
(function (root) {
  const MC = root.MonteCinema || require('./sim.js');
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const BEAT = ['the want', 'the journey', 'the trouble', 'that night', 'the arrival'], PLOT = [0, 1, 2, 3, 4];
  // ---- what the search is allowed to reach for: the judged shots and the story's cards, with every pairwise likeness precomputed
  function prepare(M) {
    if (M._mcts) return M._mcts;
    const G = M.good, gi = new Map(G.map((k, j) => [k, j])), n = G.length, S = new Float32Array(n * n);
    for (let a = 0; a < n; a++) for (let b = a; b < n; b++) { const s = MC.dot(M.SE[G[a]], M.SE[G[b]]); S[a * n + b] = S[b * n + a] = s; }
    const hits = (A, B) => { let c = 0; for (const w of A) if (B.has(w)) c++; return c; };
    const ans = new Map(); for (const [k, A] of M.answer) ans.set(k, Float32Array.from(G, g => Math.min(2, hits(A, M.words[g]))));   // how far each shot answers each card
    const words = k => M.shots[k].text.split(/\s+/).length;
    return (M._mcts = { G, gi, n, S, ans, words });
  }
  const cos = (a, b) => { let s = 0, x = 0, y = 0; for (let k = 0; k < a.length; k++) { s += a[k] * b[k]; x += a[k] * a[k]; y += b[k] * b[k]; } return s / (Math.sqrt(x * y) || 1); };
  // ---- the state of a film being made: its pieces, where it is in the story, what it has used
  function start(opts) { return { ev: [], phase: 'open', act: 0, inAct: 0, card: null, prev: null, used: new Set(), thread: new Set(), films: new Map(), stopped: false, lines: new Set(), stage: null, routine: null }; }
  function clone(s) { return { ev: s.ev.slice(), phase: s.phase, act: s.act, inAct: s.inAct, card: s.card, prev: s.prev, used: new Set(s.used), thread: new Set(s.thread), films: new Map(s.films), stopped: s.stopped, lines: new Set(s.lines), stage: s.stage, routine: s.routine }; }
  // the moves open from a state, each with a prior (how good it looks before any search), best first, at most K
  function moves(M, X, s, P) {
    const out = [], free = k => !s.used.has(k) && !P.spent.has(k);
    if (s.phase === 'open') for (const k of M.opening) { if (free(k) && !P.avoid.has(k)) out.push({ kind: 'card', k, p: M.shots[k].score / 10 }); }
    else if (s.phase === 'card') for (const k of (P.routines ? [...new Set([...M.story[PLOT[s.act]], ...P.routines.keys()])] : M.story[PLOT[s.act]])) { if (free(k) && !(s.act === 0 && P.avoid.has(k)) && !(P.routines && P.routines.has(k) && !routinesFor(k, s, P).length))
      out.push({ kind: 'card', k, p: M.shots[k].score / 10 + (M.speaks.get(k) || 0) * .5 + (s.thread.has(M.shots[k].film) ? 1.2 : 0) - (P.told.has(M.shots[k].film) ? 1.4 : 0) + (P.routines && P.routines.has(k) ? 1.5 + routinesFor(k, s, P)[0].giggle / 10 : 0) }); }   // a story keeps to its own cards; a comedy reaches for its charges
    else if (s.phase === 'end') for (const k of M.ending) { if (free(k)) out.push({ kind: 'end', k, p: M.shots[k].score / 10 }); }
    else if (s.stage === 'punch') return routinesFor(s.card, s, P).slice(0, P.K).map(r => ({ kind: 'punch', k: r.shot, r, p: r.giggle / 10 }));   // [PAUSE], then the line that answers the charge
    else if (s.stage === 'exit') { const r = s.routine, ex = r.exit != null && free(r.exit) ? [{ kind: 'shot', k: r.exit, exit: true, p: 1 }] : [];   // [TONE SHIFT]: the solemn shot that resets the room
      return ex.length ? ex : moves(M, X, Object.assign(clone(s), { stage: 'plain' }), P).filter(m => m.kind === 'shot').slice(0, 3).map(m => Object.assign(m, { exit: true })); }
    else if (s.stage === 'after') return [{ kind: 'turn', k: -1, p: 1 }];
    else {
      const pj = s.prev != null ? X.gi.get(s.prev) : null, A = s.card != null ? X.ans.get(s.card) : null, ug = [];
      for (const u of s.used) { const j = X.gi.get(u); if (j != null) ug.push(j); }
      for (let j = 0; j < X.n; j++) { const k = X.G[j]; if (!free(k) || (s.ev.length < 3 && P.avoid.has(k))) continue;
        let twin = false; for (const u of ug) if (X.S[u * X.n + j] > .93) { twin = true; break; } if (twin) continue;   // never the same picture twice
        let p = M.shots[k].score / 10;
        if (pj != null) p -= Math.abs(X.S[pj * X.n + j] - .72) * 1.6;            // a cut that matches without repeating
        if (A && s.inAct < 3) p += A[j] * .9;                                   // the picture answers the card
        p -= (s.films.get(M.shots[k].film) || 0) * .5;
        out.push({ kind: 'shot', k, p });
        const jokes = !P.routines && P.comic && P.comic.get(k);   // a comedy: the same picture, with a line from another film over it
        if (jokes) for (const J of jokes) if (!s.lines.has(J.line) && !P.spentLines.has(J.line)) { out.push({ kind: 'shot', k, line: J.line, funny: J.funny, p: p + J.funny / 10 * P.wComic }); break; } }
      if (s.stopped === false && PLOT[s.act] === 2 && s.inAct >= 1 && M.stop.length && free(M.stop[0])) out.push({ kind: 'stop', k: M.stop[0], p: .9 });   // the film may stop itself, once
      if (s.inAct >= P.minShots) out.push({ kind: 'turn', k: -1, p: .55 + .1 * s.inAct });   // turn the page: the next chapter
    }
    out.sort((a, b) => b.p - a.p);
    const top = out.slice(0, P.K);
    if (s.phase === 'shot' && s.inAct >= P.maxShots) return out.filter(m => m.kind === 'turn');   // a chapter of four shots is full
    if (s.phase === 'shot' && s.inAct >= P.minShots && !top.some(m => m.kind === 'turn')) top[top.length - 1] = out.find(m => m.kind === 'turn');
    return top;
  }
  function apply(M, X, s0, m, P) {
    const s = clone(s0), sh = M.shots[m.k] || null;
    if (m.kind === 'card' && s.phase === 'open') { s.ev.push({ kind: 'card', k: m.k, dur: P.hold }); s.used.add(m.k); s.phase = 'card'; }
    else if (m.kind === 'card') { s.ev.push({ kind: 'card', k: m.k, dur: Math.max(P.hold, Math.min(4, 1.6 + X.words(m.k) * .22)), act: s.act, beat: PLOT[s.act] }); s.used.add(m.k); s.thread.add(sh.film); s.card = m.k; s.phase = 'shot'; s.inAct = 0; s.stage = P.routines && P.routines.has(m.k) ? 'momentum' : null; }
    else if (m.kind === 'stop') { s.ev.push({ kind: 'card', k: m.k, dur: 3.2, act: s.act, silent: true, stop: true }); s.used.add(m.k); s.stopped = true; }
    else if (m.kind === 'shot' && m.line != null) { const L = M.lines[m.line]; s.ev.push({ kind: 'shot', k: m.k, dur: Math.max(P.shotDur, L.t1 - L.t0 + .9), act: s.act, line: m.line, funny: m.funny }); s.lines.add(m.line); s.used.add(m.k); s.prev = m.k; s.inAct++; s.films.set(sh.film, (s.films.get(sh.film) || 0) + 1); }
    else if (m.kind === 'punch') { const r = m.r, L = M.lines[r.line]; s.ev.push({ kind: 'shot', k: r.shot, act: s.act, line: r.line, funny: r.giggle, punch: true, pause: r.pause, laugh: r.laugh, mechanism: r.mechanism, vice: r.vice, color: r.local_color,
        dur: Math.max(P.shotDur, r.pause / 1000 + (L.t1 - L.t0) + r.laugh / 1000) }); s.lines.add(r.line); s.used.add(r.shot); s.prev = r.shot; s.inAct++; s.stage = 'exit'; s.routine = r; }
    else if (m.kind === 'shot') { s.ev.push({ kind: 'shot', k: m.k, dur: P.shotDur + (m.exit ? .6 : 0), act: s.act, exit: !!m.exit }); s.used.add(m.k); s.prev = m.k; s.inAct++; s.films.set(sh.film, (s.films.get(sh.film) || 0) + 1);
      if (s.stage === 'momentum') s.stage = routinesFor(s.card, s, P).length ? 'punch' : null; else if (s.stage === 'exit') s.stage = 'after'; }
    else if (m.kind === 'turn') { s.act++; s.inAct = 0; s.stage = null; s.phase = s.act >= PLOT.length ? 'end' : 'card'; s.card = null; }
    else if (m.kind === 'end') { s.ev.push({ kind: 'card', k: m.k, dur: P.hold, end: true }); s.used.add(m.k); s.phase = 'done'; }
    if ((s.phase === 'card' && !moves(M, X, s, P).length) || (s.phase === 'end' && !moves(M, X, s, P).length)) s.phase = s.phase === 'card' ? 'shot' : 'done';   // a beat with no card left: play on
    return s;
  }
  // the routines still open for a charge: their picture, line and exit not yet used here or in an earlier print
  function routinesFor(k, s, P) { const rs = P.routines && P.routines.get(k); if (!rs) return [];
    return rs.filter(r => !s.used.has(r.shot) && !P.spent.has(r.shot) && !s.lines.has(r.line) && !P.spentLines.has(r.line)); }
  // the score: the music whose mood is nearest the cards' words, as monte/sim.js chooses it
  function score(M, s) { const cm = s.ev.filter(e => e.kind === 'card').map(e => M.cardMood[M.cardIx.get(e.k)]).filter(Boolean);
    const mood = cm.length ? cm[0].map((_, j) => cm.reduce((a, x) => a + x[j], 0) / cm.length) : M.moods.map(() => 0);
    let best = 0, bv = -9; M.music.forEach((x, k) => { const c = cos(x.mood, mood); if (c > bv) { bv = c; best = k; } }); return { ev: s.ev, music: best, mood }; }
  const reward = (M, s, W, P) => { const f = score(M, s); MC.critic(M, f, W);
    if (P && P.routines) {   // the tactical comedy: how hard each charge was answered (the giggle reflex), and at least three routines a film
      const pu = s.ev.filter(e => e.punch), tw = Object.values(W).reduce((a, b) => a + b, 0);
      f.parts.comedy = pu.length ? pu.reduce((a, e) => a + e.funny, 0) / pu.length / 10 * Math.min(1, pu.length / 3) : 0;
      f.score = (f.score * tw + P.wComedy * f.parts.comedy) / (tw + P.wComedy); }
    else if (P && P.comic) {   // the comedy: how funny its lines are, and enough of them (about every other shot), weighed in with the critic
      const sh = s.ev.filter(e => e.kind === 'shot'), jk = sh.filter(e => e.line != null), tw = Object.values(W).reduce((a, b) => a + b, 0);
      f.parts.comedy = jk.length ? jk.reduce((a, e) => a + e.funny, 0) / jk.length / 10 * Math.min(1, jk.length / Math.max(1, sh.length * .5)) : 0;
      f.score = (f.score * tw + P.wComedy * f.parts.comedy) / (tw + P.wComedy); }
    return f; };
  // ---- the machine
  function machine(M, opts = {}) {
    const X = prepare(M), P = Object.assign({ K: 8, iters: 128, c: .9, minShots: 2, maxShots: 4, shotDur: 2.6, hold: 2.6, seed: 1, spent: new Set(), avoid: new Set(), told: new Set(), comic: null, routines: null, spentLines: new Set(), wComic: 1.6, wComedy: .45, W: Object.assign({}, MC.CRITIC) }, opts);
    const R = rng(P.seed), node = (s, m, parent) => ({ s, m, parent, kids: [], untried: s.phase === 'done' ? [] : moves(M, X, s, P), n: 0, w: 0 });
    let rootN = node(start(), null, null), lo = 1, hi = 0, total = 0; const steps = [], recent = [];
    function rollout(s) { let t = s, first = [];   // imagine the rest of the film: each next piece from the best three, by chance
      for (let g = 0; g < 80 && t.phase !== 'done'; g++) { const ms = moves(M, X, t, P); if (!ms.length) break; const m = ms[Math.floor(R() * Math.min(3, ms.length))]; t = apply(M, X, t, m, P); if (m.kind !== 'turn' && first.length < 6) first.push(m.k); }
      return { f: reward(M, t, P.W, P), first }; }
    function iterate() {
      let v = rootN;
      while (!v.untried.length && v.kids.length) { const N = Math.log(v.n + 1); v = v.kids.reduce((b, c) => { const u = c.w / c.n + P.c * Math.sqrt(N / c.n); return u > b.u ? { c, u } : b; }, { c: null, u: -1e9 }).c; }   // 1 selection
      if (v.untried.length) { const m = v.untried.shift(); const c = node(apply(M, X, v.s, m, P), m, v); v.kids.push(c); v = c; }   // 2 expansion
      const { f, first } = rollout(v.s); total++;                                                                                     // 3 rollout
      lo = Math.min(lo, f.score); hi = Math.max(hi, f.score); const r = hi > lo ? (f.score - lo) / (hi - lo) : .5;
      recent.push({ first: v.s.ev.slice(rootN.s.ev.length).map(e => e.k).concat(first).slice(0, 6), score: f.score }); if (recent.length > 24) recent.shift();
      for (let u = v; u; u = u.parent) { u.n++; u.w += r; } }                                                                         // 4 backpropagation
    function commit() {   // the most visited branch becomes the film; the tree is re-rooted there, keeping what it learned
      const best = rootN.kids.reduce((b, c) => (!b || c.n > b.n ? c : b), null); if (!best) return null;
      steps.push({ at: rootN.s.ev.length, phase: rootN.s.phase, act: rootN.s.act, chosen: best.m, kids: rootN.kids.map(c => ({ kind: c.m.kind, k: c.m.k, n: c.n, q: c.n ? +(c.w / c.n).toFixed(3) : 0 })).sort((a, b) => b.n - a.n), rollouts: recent.slice(-8) });
      best.parent = null; rootN = best; return best.m; }
    function step(iters = P.iters) { if (rootN.s.phase === 'done') return null; for (let i = 0; i < iters; i++) iterate(); return commit(); }
    function run() { while (step()); return film(); }
    function film() { const f = reward(M, rootN.s, P.W, P); f.seed = P.seed; f.steps = steps; f.rollouts = total; return f; }
    return { step, run, film, iterate, commit, get root() { return rootN; }, get recent() { return recent; }, kids: () => rootN.kids.map(c => ({ kind: c.m.kind, k: c.m.k, n: c.n, q: c.n ? c.w / c.n : 0 })).sort((a, b) => b.n - a.n), get steps() { return steps; }, get total() { return total; }, get done() { return rootN.s.phase === 'done'; }, P, BEAT, PLOT };
  }
  const api = { machine, BEAT, PLOT };
  if (typeof module !== 'undefined') module.exports = api; else root.GrandEditingMachine = api;
})(this);
