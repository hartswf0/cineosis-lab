// The Grand Editing Machine, offline: node monte/mcts_run.js [iters] -> monte/mcts.json (the prints it directed, each with its search:
// at every step, the branches it weighed, how often it visited each, what they promised, and the futures it imagined)
const fs = require('fs'), MC = require('./sim.js'), GM = require('./mcts.js');
const M = MC.load(JSON.parse(fs.readFileSync(__dirname + '/material.json', 'utf8')));
const TACT = process.argv[3] === 'tactical', COMIC = process.argv[3] === 'comic' || TACT, IT = +(process.argv[2] || 256), t0 = Date.now(), prints = [], spent = new Set(), avoid = new Set(), told = new Set();   // told: the films whose story a print already told
// the comedies: lines from one film over pictures from another, as the comedy judges scored them (monte/comic/funny_*.json)
let comic = null; const spentLines = new Set();
if (COMIC) { const pairs = JSON.parse(fs.readFileSync(__dirname + '/comic/pairs.json', 'utf8')), byN = new Map(pairs.map(p => [p.n, p])), ix = new Map(M.shots.map((x, k) => [x.i, k])); comic = new Map();
  for (const f of fs.readdirSync(__dirname + '/comic').filter(f => /^funny_\d+\.json$/.test(f))) for (const v of JSON.parse(fs.readFileSync(__dirname + '/comic/' + f, 'utf8'))) {
    const p = byN.get(v.n); if (!p || v.funny < 6) continue; const k = ix.get(p.shot); if (k == null) continue;
    if (!comic.has(k)) comic.set(k, []); comic.get(k).push({ line: p.line, funny: v.funny, why: v.why }); }
  for (const a of comic.values()) a.sort((x, y) => y.funny - x.funny); console.log('comedy: funny pairings for', comic.size, 'pictures'); }
// the tactical comedies: for each charge (an attacking card), the routines the Tactical Charisma judges built (monte/comic/routines_*.json):
// a picture and a line that answer it, the pause before the line, the room left for the laugh, and the solemn shot that resets the room
let routines = null;
if (TACT) { const tin = JSON.parse(fs.readFileSync(__dirname + '/comic/tactical_input.json', 'utf8')), ix = new Map(M.shots.map((x, k) => [x.i, k])), pairs = JSON.parse(fs.readFileSync(__dirname + '/comic/pairs.json', 'utf8')), byN = new Map(pairs.map(p => [p.n, p]));
  const chargeK = new Map(tin.charges.map(c => [c.id, ix.get(c.i)])), shotK = s => (tin.shots[s - 1] ? ix.get(tin.shots[s - 1].i) : null); routines = new Map();
  for (const f of fs.readdirSync(__dirname + '/comic').filter(f => /^routines_\d+\.json$/.test(f))) for (const c of JSON.parse(fs.readFileSync(__dirname + '/comic/' + f, 'utf8'))) {
    const k = chargeK.get(c.charge); if (k == null) continue;
    const rs = (c.routines || []).map(r => { const p = byN.get(r.pair); return p && r.giggle >= 6 ? Object.assign({}, r, { shot: ix.get(p.shot), line: p.line, exit: shotK(r.exit), pause: Math.max(300, Math.min(1500, r.pause_ms || 700)), laugh: Math.max(600, Math.min(2200, r.laugh_ms || 1200)) }) : null; }).filter(r => r && r.shot != null);
    if (rs.length) routines.set(k, rs.sort((a, b) => b.giggle - a.giggle)); }
  console.log('tactical: routines for', routines.size, 'charges,', [...routines.values()].reduce((a, r) => a + r.length, 0), 'in all'); }
const same = k => M.cards.filter(c => M.shots[c].text && M.shots[c].text === M.shots[k].text);   // the same card from another reel is the same card
for (let p = 0; p < 6; p++) {   // each print directed from scratch, forbidden what the prints before it used; three at least, then while they stay good
  let best = null;
  for (const seed of [1, 2, 3]) { const f = GM.machine(M, { seed: 100 * p + seed, iters: IT, spent: new Set(spent), avoid: new Set(avoid), told: new Set(told), comic: TACT ? null : comic, routines, spentLines: new Set(spentLines) }).run(); if (!best || f.score > best.score) best = f; }
  if (prints.length >= 3 && best.score < (COMIC ? .8 : .85)) break;
  prints.push(best); console.log(`print ${p + 1} · ${best.score.toFixed(3)} · ${best.seconds.toFixed(1)} s · ${best.ev.length} pieces · ${best.rollouts} futures imagined`);
  for (const e of best.ev) { if (e.line != null) spentLines.add(e.line); spent.add(e.k); if (e.kind === 'card') same(e.k).forEach(c => spent.add(c)); }
  const ch = new Map(); best.ev.filter(e => e.kind === 'card' && M.beat.has(e.k)).forEach(e => ch.set(M.shots[e.k].film, (ch.get(M.shots[e.k].film) || 0) + 1));
  for (const [film, n] of ch) if (n >= 2) told.add(film);
  MC.starts(best).forEach(k => { avoid.add(k); same(k).forEach(c => avoid.add(c)); });
}
const id = k => (k >= 0 ? M.shots[k].i : null);
const show = f => ({ seed: f.seed, score: +f.score.toFixed(3), parts: Object.fromEntries(Object.entries(f.parts).map(([k, v]) => [k, +v.toFixed(2)])), seconds: +f.seconds.toFixed(1), music: M.music[f.music], rollouts: f.rollouts,
  ev: f.ev.map(e => ({ kind: e.kind, i: M.shots[e.k].i, film: M.shots[e.k].film, year: M.shots[e.k].year, text: M.shots[e.k].text || null, score: M.shots[e.k].score, dur: +e.dur.toFixed(2), act: e.act, beat: e.beat, silent: !!e.silent, stop: !!e.stop, end: !!e.end, line: e.line != null ? M.lines[e.line] : null, funny: e.funny, punch: !!e.punch, pause: e.pause, laugh: e.laugh, exit: !!e.exit, mechanism: e.mechanism, vice: e.vice, color: e.color })),
  steps: f.steps.map(s => ({ at: s.at, phase: s.phase, act: s.act, chosen: { kind: s.chosen.kind, i: id(s.chosen.k) }, kids: s.kids.map(c => ({ kind: c.kind, i: id(c.k), n: c.n, q: c.q })), rollouts: s.rollouts.map(r => ({ score: +r.score.toFixed(3), first: r.first.map(id) })) })) });
fs.writeFileSync(__dirname + (TACT ? '/tactical.json' : COMIC ? '/comic.json' : '/mcts.json'), JSON.stringify({ engine: 'The Grand Editing Machine: Monte Carlo tree search (UCT selection, top-K expansion, rollout, critic backpropagation)', iters: IT, best: prints.map(show), seconds: (Date.now() - t0) / 1000 }));
if (COMIC && !TACT) fs.writeFileSync(__dirname + '/comic-jokes.json', JSON.stringify([...comic].flatMap(([k, a]) => a.map(J => [M.shots[k].i, J.line, J.funny]))));   // the pairings, for the page's live comedies
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(1)} s · ${prints.length} prints · ${(fs.statSync(__dirname + (TACT ? '/tactical.json' : COMIC ? '/comic.json' : '/mcts.json')).size / 1e6).toFixed(2)} MB`);
