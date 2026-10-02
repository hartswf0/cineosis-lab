// offline evolution: node monte/run.js [generations] -> monte/evolution.json (history, the winning rules, the best films)
const fs = require('fs'), MC = require('./sim.js');
const M = MC.load(JSON.parse(fs.readFileSync(__dirname + '/material.json', 'utf8')));
const N = +(process.argv[2] || 40), E = MC.evolve(M, { seed: 2026, pop: 24, films: 6 });
const t0 = Date.now();
for (let k = 0; k < N; k++) { const h = E.step(); if (k % 5 === 0 || k === N - 1) console.log(`gen ${h.gen} · best rules ${h.best.toFixed(3)} · mean ${h.mean.toFixed(3)} · best film ${h.film.toFixed(3)}`); }
const b = E.best, rules = Object.fromEntries(MC.GENES.map(([n, lo, hi, say], k) => [n, { value: +MC.val(b.g, k).toFixed(2), say }]));
// the winning rules, run many times: the best films they make
const films = []; for (let s = 0; s < 400; s++) { const f = MC.generate(M, b.g, 9000 + s); MC.critic(M, f); films.push(f); }
films.sort((a, b) => b.score - a.score);
const show = f => ({ seed: f.seed, score: +f.score.toFixed(3), parts: Object.fromEntries(Object.entries(f.parts).map(([k, v]) => [k, +v.toFixed(2)])), seconds: +f.seconds.toFixed(1),
  music: M.music[f.music], ev: f.ev.map(e => ({ kind: e.kind, i: M.shots[e.k].i, film: M.shots[e.k].film, year: M.shots[e.k].year, text: M.shots[e.k].text || null, score: M.shots[e.k].score,
    dur: +e.dur.toFixed(2), act: e.act, silent: !!e.silent, ret: !!e.ret, end: !!e.end, line: e.line != null ? M.lines[e.line] : null })) });
fs.writeFileSync(__dirname + '/evolution.json', JSON.stringify({ generations: E.history.map(h => ({ gen: h.gen, best: +h.best.toFixed(4), mean: +h.mean.toFixed(4), film: +h.film.toFixed(4), g: h.g.map(x => +x.toFixed(3)) })),
  rules, genome: b.g, critic: MC.CRITIC, best: films.slice(0, 5).map(show), seconds: (Date.now() - t0) / 1000 }));
console.log(`done in ${((Date.now() - t0) / 1000).toFixed(1)} s · winning rules from gen ${b.gen}:`, Object.entries(rules).map(([k, r]) => `${k}=${r.value}`).join(' '));
console.log('best film', films[0].score.toFixed(3), JSON.stringify(show(films[0]).parts), films[0].seconds.toFixed(1) + ' s');
