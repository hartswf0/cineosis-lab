/* SEA CORE — the lattice of takes as something to reason with, shared by slopfeeder-takes.html and party/games/sea.js.
   The critic is the lab's: a cut scores as monte/sim.js scores one (a Gaussian of CLIP cosine around .72); a take scores by likeness
   to the shot it would replace, symmetry (after wes/score.py) and poison; shots that carry a line or a poison turn are riverbed (held).
   BEST PATH is the Found Odyssey's joint choice (Viterbi, build_cuts.py); ROLL is Monte Carlo films; the MACHINE is monte/mcts.js's loop
   (selection by UCT c=.9, expansion, a rollout from the best three by chance, backpropagation of a min-max-normalised reward; commit the
   most-visited piece and re-root, keeping what it learned) over the next shots of the lattice. */
(function (root) {
  function Sea(M) {
    const cols = M.cols, cal = M.cal;
    const sid = x => x.kind === 'ai' ? x.clip : x.v;
    const USED = {}; cols.forEach((c, i) => { const x = c.cands[0]; (USED[sid(x)] = USED[sid(x)] || []).push(i); });
    const cosE = (a, b) => { let s = 0; for (let i = 0; i < 32; i++) s += a.e[i] * b.e[i]; return cal[0] * s / 16129 + cal[1]; };
    const join = (a, b) => (a.kind === 'ai' && b.kind === 'ai' && a.clip === b.clip) ? -1 : Math.exp(-(((cosE(a, b) - .72) / .12) ** 2) / 2);
    const node = (c, k) => { const C = cols[c], x = C.cands[k]; return 2.2 * x.same + .25 * x.sym - (C.poison ? 0 : .5 * x.poison) + (k === 0 ? .15 + (C.hold ? 3 : 0) : 0) - (k && (USED[sid(x)] || []).some(o => o !== c) ? 1.2 : 0); };
    /* everything below works over `vis`, the columns in view (all, or AI only) */
    function total(path, vis) { let n = 0, j = 0, weak = 0, lk = 0; vis.forEach((c, i) => { n += node(c, path[c]); lk += cols[c].cands[path[c]].same; if (i) { const v = join(cols[vis[i - 1]].cands[path[vis[i - 1]]], cols[c].cands[path[c]]); j += v; if (v < .35) weak++; } }); return { like: lk / vis.length, seams: j / Math.max(1, vis.length - 1), weak, all: n + 1.2 * j }; }
    function seam(path, a, b) { return join(cols[a].cands[path[a]], cols[b].cands[path[b]]); }
    function viterbi(path, lock, vis) {
      const out = path.slice(), sc = [], bp = [];
      vis.forEach((c, i) => {
        const K = cols[c].cands.length; sc[i] = new Array(K).fill(-1e9); bp[i] = new Array(K).fill(0);
        for (let k = 0; k < K; k++) {
          if (lock[c] && path[c] !== k) continue; const nd = node(c, k);
          if (!i) { sc[i][k] = nd; continue; } const pc = vis[i - 1];
          for (let p = 0; p < cols[pc].cands.length; p++) { if (sc[i - 1][p] < -1e8) continue; const v = sc[i - 1][p] + nd + 1.2 * join(cols[pc].cands[p], cols[c].cands[k]); if (v > sc[i][k]) { sc[i][k] = v; bp[i][k] = p; } }
        }
      });
      let k = sc[vis.length - 1].indexOf(Math.max(...sc[vis.length - 1])); for (let i = vis.length - 1; i >= 0; i--) { out[vis[i]] = k; k = bp[i][k]; } return out;
    }
    function rollout(path, lock, vis, n = 400) {
      const runs = [];
      for (let r = 0; r < n; r++) {
        const p = path.slice();
        vis.forEach((c, i) => { if (lock[c]) return; const pc = i ? vis[i - 1] : null; const w = cols[c].cands.map((x, k) => Math.exp((node(c, k) + (pc != null ? 1.2 * join(cols[pc].cands[p[pc]], x) : 0)) / .35)); let u = Math.random() * w.reduce((a, b) => a + b, 0), k = 0; while (k < w.length - 1 && (u -= w[k]) > 0) k++; p[c] = k; });
        runs.push([total(p, vis).all, p]);
      }
      runs.sort((a, b) => b[0] - a[0]); const keep = runs.slice(0, Math.max(1, Math.round(n * .15)));
      const heat = cols.map(c => new Array(c.cands.length).fill(0)); keep.forEach(([, p]) => vis.forEach(c => heat[c][p[c]]++)); return heat.map(h => h.map(v => v / keep.length));
    }
    /* the machine: decide column vis[at] (given the take before it), looking H shots ahead */
    function machine(path, lock, vis, at, opts = {}) {
      const H = opts.horizon || 10, K = opts.K || 6, c0 = opts.c || .9; let lo = 1e9, hi = -1e9, total_ = 0;
      const prior = (i, prevTake) => { const c = vis[i]; return cols[c].cands.map((x, k) => ({ k, p: node(c, k) + (prevTake ? 1.2 * join(prevTake, x) : 0) })).filter(m => !lock[c] || m.k === path[c]).sort((a, b) => b.p - a.p).slice(0, K); };
      const take = (i, k) => cols[vis[i]].cands[k];
      const mk = (i, k, parent) => ({ i, k, parent, kids: [], untried: i + 1 < Math.min(vis.length, at + H) ? prior(i + 1, take(i, k)) : [], n: 0, w: 0 });
      const prevK = at > 0 ? path[vis[at - 1]] : null;
      let root = { i: at - 1, k: prevK, parent: null, kids: [], untried: prior(at, at > 0 ? take(at - 1, prevK) : null), n: 0, w: 0 };
      function score(i, k, seq) { let s = 0, prev = take(i, k); for (const [j, kk] of seq) { s += node(vis[j], kk) + 1.2 * join(prev, take(j, kk)); prev = take(j, kk); } return s; }
      function iterate() {
        let v = root, chain = [];
        while (!v.untried.length && v.kids.length) { const N = Math.log(v.n + 1); v = v.kids.reduce((b, c) => { const u = c.w / c.n + c0 * Math.sqrt(N / c.n); return u > b.u ? { c, u } : b; }, { c: null, u: -1e9 }).c; }
        if (v.untried.length) { const m = v.untried.shift(); const ch = mk(v.i + 1, m.k, v); v.kids.push(ch); v = ch; }
        for (let u = v; u && u !== root; u = u.parent) chain.unshift([u.i, u.k]);
        let i = v.i, k = v.k; const seq = [];
        while (i + 1 < Math.min(vis.length, at + H)) { const ms = prior(i + 1, take(i, k)); const m = ms[Math.floor(Math.random() * Math.min(3, ms.length))]; i++; k = m.k; seq.push([i, k]); }   // a rollout: each next take from the best three, by chance
        const first = chain[0]; const r0 = (at > 0 ? 1.2 * join(take(at - 1, prevK), take(first[0], first[1])) : 0) + node(vis[first[0]], first[1]) + score(first[0], first[1], chain.slice(1).concat(seq));
        lo = Math.min(lo, r0); hi = Math.max(hi, r0); const r = hi > lo ? (r0 - lo) / (hi - lo) : .5; total_++;
        for (let u = v; u; u = u.parent) { u.n++; u.w += r; }
      }
      const kids = () => { const t = root.kids.reduce((a, c) => a + c.n, 0) || 1; return root.kids.map(c => ({ k: c.k, n: c.n, share: c.n / t, q: c.n ? c.w / c.n : 0 })).sort((a, b) => b.n - a.n); };
      return { iterate, kids, get total() { return total_; }, at };
    }
    return { cols, join, node, total, seam, viterbi, rollout, machine, sid };
  }
  const api = { Sea };
  if (typeof module !== 'undefined') module.exports = api; else root.SeaCore = api;
})(this);
