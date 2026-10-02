/* The workshop's engine: the evolving population, kept off the page's thread (a generation is 144 films, about a second and a half).
   Runs as a Web Worker (new Worker('monte/engine.js')) or, where workers fail, as a plain script that defines MonteEngine.
   Messages in:  init {material, g0, W, marks} · step · critic {W, marks} · keep {g, id} · undo
   Messages out: ready | gen | pop, each with the register (every rule set: id, rules, birth, latest measured fitness). */
(function (root) {
  const POP = 24, FILMS = 6, ELITE = 6, TRIALS = 4, SHOWN = 3, VARIANTS = 7;
  function Engine(MC) {
    let M = null, E = null, W = null, undo = null;
    const mutate = (g, s) => g.map(x => Math.min(1, Math.max(0, x + (Math.random() - .5) * s)));
    const diff = (a, b) => b.map((y, k) => ({ k, from: a[k], to: y })).filter(d => Math.abs(d.to - d.from) > 1e-9);
    const register = () => E.pop.map((g, k) => { const id = E.ids[k]; return { id, g, birth: E.births[id], fit: E.fits[id] || null }; });
    // the films shown: from each of the top rule sets, the best of a few fresh samples (each sample a different random seed)
    function shown() { const out = [];
      for (let c = 0; c < SHOWN; c++) { const g = E.pop[c]; let best = null, tried = [];
        for (let t = 0; t < TRIALS; t++) { const f = MC.generate(M, g, Math.floor(Math.random() * 1e9)); MC.critic(M, f, W); tried.push(+f.score.toFixed(4)); if (!best || f.score > best.score) best = f; }
        out.push({ id: E.ids[c], g: g.slice(), seed: best.seed, ev: best.ev, music: best.music, mood: best.mood, score: best.score, parts: best.parts, seconds: best.seconds, trials: tried }); }
      return out; }
    function setCritic(w, marks) { Object.keys(W).forEach(k => delete W[k]); Object.assign(W, w); MC.taste(M, marks || {}); }
    const handle = function (m) {
      if (m.type === 'init') { M = MC.load(m.material); W = Object.assign({}, m.W); MC.taste(M, m.marks || {});
        const g0 = m.g0, start = g0 ? Array.from({ length: POP }, (_, k) => k ? mutate(g0, .2) : g0.slice()) : undefined;
        E = MC.evolve(M, { seed: Math.floor(Math.random() * 1e9), pop: POP, films: FILMS, elite: ELITE, critic: W, start,
          origin: k => g0 ? (k ? { kind: 'variant', gen: 0, of: 'saved', mut: diff(g0, start[k]) } : { kind: 'saved', gen: 0 }) : null });
        return { type: 'ready', reg: register(), sizes: { POP, FILMS, ELITE, TRIALS, SHOWN, VARIANTS } }; }
      if (m.type === 'step') { const h = E.step();
        return { type: 'gen', hist: { gen: h.gen, best: h.best, mean: h.mean }, reg: register(), three: shown() }; }
      if (m.type === 'critic') { setCritic(m.W, m.marks); return { type: 'pop', reg: register() }; }
      if (m.type === 'keep') { undo = E.snapshot(); const id = E.adopt(0, m.g, { kind: 'kept', from: m.id });
        for (let j = 1; j <= VARIANTS; j++) { const v = mutate(m.g, .12); E.adopt(POP - j, v, { kind: 'variant', of: id, mut: diff(m.g, v) }); }
        return { type: 'pop', reg: register() }; }
      if (m.type === 'undo') { if (undo) E.restore(undo); undo = null; return { type: 'pop', reg: register() }; }
    };
    return m => { const r = handle(m); if (r) r.gen = E ? E.gen : 0; return r; };
  }
  if (typeof WorkerGlobalScope !== 'undefined' && root instanceof WorkerGlobalScope) {
    importScripts('sim.js'); const handle = Engine(root.MonteCinema);
    root.onmessage = e => { try { const r = handle(e.data); if (r) root.postMessage(Object.assign(r, { req: e.data.req })); } catch (x) { root.postMessage({ type: 'error', req: e.data.req, message: String(x && x.message || x) }); } };
  } else root.MonteEngine = Engine;
})(this);
