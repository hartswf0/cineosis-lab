// every text the published pages can play gets a Piper reading: the test poems read at their own pace (the voice is the clock),
// and the fourteen suite poems read in step with the recorded voice (each phrase placed where the poet says it), for mixing.
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url'; import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const H = path.dirname(fileURLToPath(import.meta.url)), S = require(path.join(H, 'engine.js'));
const P = JSON.parse(fs.readFileSync(path.join(H, 'tests/poems.json'))).poems, K = JSON.parse(fs.readFileSync(path.join(H, '../bets/kernel-data.json')));
const gaps = ph => ph.map((p, i) => { const n = ph[i + 1]; return !n ? 1.2 : n.scene !== p.scene ? 1.3 : n.sent !== p.sent ? .75 : .3; });
const jobs = [], index = { poems: {}, wygwyl: {} }, voices = ['en_US-ryan-high', 'en_US-lessac-medium'];
for (const p of P.filter(p => p.text)) for (const v of voices) {
  const ph = S.parse(p.text), out = `markov/voice/${p.id}.${v}`;
  jobs.push({ phrases: ph.map(x => x.text), gaps: gaps(ph), voice: v, out }); (index.poems[p.id] = index.poems[p.id] || {})[v] = out;
}
for (const f of K.films) {
  const lines = K.lines.filter(l => l.film === f.n), ph = S.parse(lines.map(l => l.text).join('\n')), W = [];
  lines.forEach(l => l.text.split(/\s+/).filter(Boolean).forEach((_, k) => { const w = l.words[Math.min(k, l.words.length - 1)]; W.push([w.t0, w.t1]); }));
  let w = 0; const at = ph.map(p => { const n = p.text.split(/\s+/).filter(Boolean).length, a = W[Math.min(w, W.length - 1)]; w += n; return Math.max(0, a[0] - f.t0); });
  const out = `markov/voice/wygwyl-${f.n}.en_US-ryan-high.aligned`;
  jobs.push({ phrases: ph.map(x => x.text), at, duration: f.t1 - f.t0, voice: 'en_US-ryan-high', out }); index.wygwyl[f.n] = { 'en_US-ryan-high': out };
}
fs.mkdirSync(path.join(H, 'voice'), { recursive: true });
fs.writeFileSync(path.join(H, 'voice/jobs.json'), JSON.stringify(jobs)); fs.writeFileSync(path.join(H, 'voice/index.json'), JSON.stringify(index, null, 1));
console.log(jobs.length, 'readings to render');
