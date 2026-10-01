// the decisive experiment: hold the footage constant, change one relation in the sentence, and see whether the cut changes as it should.
// Also the ablation: does the relation survive when the engine ignores the sentence's structure (text retrieval only)?
import fs from 'fs'; import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const S = require('./engine.js');
const J = JSON.parse(fs.readFileSync('library.json')); const q = new Int8Array(fs.readFileSync('emb.bin').buffer.slice(0));
const lib = new S.Library(J, q, JSON.parse(fs.readFileSync('events.json')).events);
const TX = JSON.parse(fs.readFileSync('texts.json')); const P = JSON.parse(fs.readFileSync('presets.json'));
const run = (text, opts = {}) => { const ph = S.parse(text); const sims = ph.map(p => lib.sims(TX[p.text])); return { ph, ...S.compose(lib, ph, sims, opts) }; };
const flat = (text) => {  // retrieval only: one best shot per phrase by text similarity, no state, no operations
  const ph = S.parse(text); const e = new S.Engine(lib, { wOp: 0 }); ph.forEach(p => { const sim = lib.sims(TX[p.text]); const S0 = e.strand(p.subj || e.cur || 'A'); e.emit('CONTINUE', S0, p, sim, p.t1 - p.t0); });
  return { cut: e.cut, fid: S.fidelity(e, ph) };
};
const show = r => r.cut.map(s => `${s.strand}:${s.op}${s.held ? '+held' : ''}`).join(' ');
const report = [];
for (const pr of P.pairs) {
  const A = run(pr.a), B = run(pr.b), FA = flat(pr.a), FB = flat(pr.b);
  const row = { rel: pr.rel, a: pr.a, b: pr.b, expect: pr.expect, opsA: show(A), opsB: show(B), fidA: A.fid, fidB: B.fid,
    flatA: FA.fid, flatB: FB.fid, differ: show(A) !== show(B), shotsA: A.cut.map(s => s.id), shotsB: B.cut.map(s => s.id) };
  report.push(row);
  console.log(`\n■ ${pr.rel}\n  A ${pr.a}\n    ${row.opsA}   D=${A.fid.D.toFixed(2)} (${A.fid.realized}/${A.fid.required})   flat D=${FA.fid.D.toFixed(2)}\n  B ${pr.b}\n    ${row.opsB}   D=${B.fid.D.toFixed(2)} (${B.fid.realized}/${B.fid.required})   flat D=${FB.fid.D.toFixed(2)}`);
  [...A.fid.rows.map(r => ['A', r]), ...B.fid.rows.map(r => ['B', r])].filter(([, r]) => r.rel !== 'rhythm').forEach(([w, r]) => console.log(`    ${w} ${r.ok ? '✓' : '✗'} ${r.rel}: ${r.why}`));
}
fs.writeFileSync('pairs-report.json', JSON.stringify(report, null, 1));
