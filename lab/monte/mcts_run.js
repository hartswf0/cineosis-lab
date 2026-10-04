// The Grand Editing Machine, offline: node monte/mcts_run.js [iters] -> monte/mcts.json (the prints it directed, each with its search:
// at every step, the branches it weighed, how often it visited each, what they promised, and the futures it imagined)
const fs = require('fs'), MC = require('./sim.js'), GM = require('./mcts.js');
const M = MC.load(JSON.parse(fs.readFileSync(__dirname + '/material.json', 'utf8')));
const COMIC = process.argv[3] === 'comic', IT = +(process.argv[2] || 256), t0 = Date.now(), prints = [], spent = new Set(), avoid = new Set(), told = new Set();   // told: the films whose story a print already told
// the comedies: lines from one film over pictures from another, as the comedy judges scored them (monte/comic/funny_*.json)
let comic = null; const spentLines = new Set();
if (COMIC) { const pairs = JSON.parse(fs.readFileSync(__dirname + '/comic/pairs.json', 'utf8')), byN = new Map(pairs.map(p => [p.n, p])), ix = new Map(M.shots.map((x, k) => [x.i, k])); comic = new Map();
  for (const f of fs.readdirSync(__dirname + '/comic').filter(f => /^funny_\d+\.json$/.test(f))) for (const v of JSON.parse(fs.readFileSync(__dirname + '/comic/' + f, 'utf8'))) {
    const p = byN.get(v.n); if (!p || v.funny < 6) continue; const k = ix.get(p.shot); if (k == null) continue;
    if (!comic.has(k)) comic.set(k, []); comic.get(k).push({ line: p.line, funny: v.funny, why: v.why }); }
  for (const a of comic.values()) a.sort((x, y) => y.funny - x.funny); console.log('comedy: funny pairings for', comic.size, 'pictures'); }
const same = k => M.cards.filter(c => M.shots[c].text && M.shots[c].text === M.shots[k].text);   // the same card from another reel is the same card
for (let p = 0; p < 6; p++) {   // each print directed from scratch, forbidden what the prints before it used; three at least, then while they stay good
  let best = null;
  for (const seed of [1, 2, 3]) { const f = GM.machine(M, { seed: 100 * p + seed, iters: IT, spent: new Set(spent), avoid: new Set(avoid), told: new Set(told), comic, spentLines: new Set(spentLines) }).run(); if (!best || f.score > best.score) best = f; }
  if (prints.length >= 3 && best.score < (COMIC ? .8 : .85)) break;
  prints.push(best); console.log(`print ${p + 1} · ${best.score.toFixed(3)} · ${best.seconds.toFixed(1)} s · ${best.ev.length} pieces · ${best.rollouts} futures imagined`);
  for (const e of best.ev) { if (e.line != null) spentLines.add(e.line); spent.add(e.k); if (e.kind === 'card') same(e.k).forEach(c => spent.add(c)); }
  const ch = new Map(); best.ev.filter(e => e.kind === 'card' && M.beat.has(e.k)).forEach(e => ch.set(M.shots[e.k].film, (ch.get(M.shots[e.k].film) || 0) + 1));
  for (const [film, n] of ch) if (n >= 2) told.add(film);
  MC.starts(best).forEach(k => { avoid.add(k); same(k).forEach(c => avoid.add(c)); });
}
const id = k => (k >= 0 ? M.shots[k].i : null);
const show = f => ({ seed: f.seed, score: +f.score.toFixed(3), parts: Object.fromEntries(Object.entries(f.parts).map(([k, v]) => [k, +v.toFixed(2)])), seconds: +f.seconds.toFixed(1), music: M.music[f.music], rollouts: f.rollouts,
  ev: f.ev.map(e => ({ kind: e.kind, i: M.shots[e.k].i, film: M.shots[e.k].film, year: M.shots[e.k].year, text: M.shots[e.k].text || null, score: M.shots[e.k].score, dur: +e.dur.toFixed(2), act: e.act, beat: e.beat, silent: !!e.silent, stop: !!e.stop, end: !!e.end, line: e.line != null ? M.lines[e.line] : null, funny: e.funny })),
  steps: f.steps.map(s => ({ at: s.at, phase: s.phase, act: s.act, chosen: { kind: s.chosen.kind, i: id(s.chosen.k) }, kids: s.kids.map(c => ({ kind: c.kind, i: id(c.k), n: c.n, q: c.q })), rollouts: s.rollouts.map(r => ({ score: +r.score.toFixed(3), first: r.first.map(id) })) })) });
fs.writeFileSync(__dirname + (COMIC ? '/comic.json' : '/mcts.json'), JSON.stringify({ engine: 'The Grand Editing Machine: Monte Carlo tree search (UCT selection, top-K expansion, rollout, critic backpropagation)', iters: IT, best: prints.map(show), seconds: (Date.now() - t0) / 1000 }));
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(1)} s · ${prints.length} prints · ${(fs.statSync(__dirname + (COMIC ? '/comic.json' : '/mcts.json')).size / 1e6).toFixed(2)} MB`);
