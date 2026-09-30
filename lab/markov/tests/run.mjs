// The test: every text in the library becomes a film twice, composed (scenes, worlds, operations) and flat (best shot per line, the search baseline).
// Needs the lab server for embeddings (python3 CINEOSIS_44/lab/server.py). Writes tests/report.json.
import fs from 'fs'; import path from 'path'; import { createRequire } from 'module'; const require = createRequire(import.meta.url);
import { fileURLToPath } from 'url'; const H = path.dirname(fileURLToPath(import.meta.url)), S = require(path.join(H, '../engine.js'));
const J = JSON.parse(fs.readFileSync(path.join(H, '../library.json'))), q = new Int8Array(fs.readFileSync(path.join(H, '../emb.bin')).buffer.slice(0));
const lib = new S.Library(J, q, JSON.parse(fs.readFileSync(path.join(H, '../events.json'))).events);
const cacheF = path.join(H, 'emb-cache.json'), cache = fs.existsSync(cacheF) ? JSON.parse(fs.readFileSync(cacheF)) : {};
const off = JSON.parse(fs.readFileSync(path.join(H, '../texts.json'))); Object.assign(cache, off);
async function embed(texts) {
  const miss = [...new Set(texts.filter(t => !cache[t]))];
  for (let i = 0; i < miss.length; i += 48) {
    const r = await fetch('http://127.0.0.1:8765/api/embed', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ texts: miss.slice(i, i + 48) }) });
    if (!r.ok) throw new Error('embed ' + r.status); const j = await r.json(); miss.slice(i, i + 48).forEach((t, k) => cache[t] = j.emb[k]);
  }
  return texts.map(t => cache[t]);
}
const P = JSON.parse(fs.readFileSync(path.join(H, 'poems.json'))).poems;
const K = JSON.parse(fs.readFileSync(path.join(H, '../../bets/kernel-data.json')));
const tests = P.filter(p => p.text).map(p => ({ id: p.id, title: p.title, text: p.text }));
['01', '03'].forEach(n => tests.unshift({ id: 'wygwyl-' + n, title: 'WYGWYL ' + n + ' · ' + K.films.find(f => f.n === n).title, text: K.lines.filter(l => l.film === n).map(l => l.text).join('\n') }));
const pct = x => Math.round(x * 100) + '%', f2 = x => x.toFixed(2);
const rows = [];
for (const t of tests) {
  const ph = S.parse(t.text), E = await embed(ph.map(p => p.text)), sims = E.map(e => lib.sims(e));
  const A = S.run(lib, S.parse(t.text), sims, {}), F = S.run(lib, S.parse(t.text), sims, { wOp: 0, wHome: 0, close: false, gap: 9 });
  const row = { id: t.id, title: t.title, phrases: ph.length, composed: { ...A.m, kept: A.fid.realized, required: A.fid.required, thin: A.m.thin.length }, flat: { ...F.m, kept: F.fid.realized, required: F.fid.required, thin: F.m.thin.length },
    scenes: Object.values(A.eng.scenes).map(s => s.title), thinLines: A.m.thin.slice(0, 6) };
  rows.push(row);
  console.log(`${t.title.slice(0, 38).padEnd(38)} ${String(ph.length).padStart(3)} lines  scenes ${String(A.m.scenes).padStart(2)}  worlds ${String(A.m.worlds).padStart(2)}  continuity ${pct(A.m.continuity).padStart(4)} (flat ${pct(F.m.continuity).padStart(4)})  in-world ${pct(A.m.inWorld).padStart(4)}  cutaways ${String(A.m.cutaways).padStart(2)}  coverage ${f2(A.m.meanCoverage)}  thin ${String(A.m.thin.length).padStart(2)}  relations ${A.fid.realized}/${A.fid.required} (flat ${F.fid.realized}/${F.fid.required})  films ${A.m.films} (flat ${F.m.films})`);
}
fs.writeFileSync(cacheF, JSON.stringify(cache)); fs.writeFileSync(path.join(H, 'report.json'), JSON.stringify({ at: new Date().toISOString(), rows }, null, 1));
