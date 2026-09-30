// dump a composed film as rows (scene, op, shot thumb, line) for a contact sheet
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url'; import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const H = path.dirname(fileURLToPath(import.meta.url)), S = require(path.join(H, '../engine.js'));
const J = JSON.parse(fs.readFileSync(path.join(H, '../library.json'))), q = new Int8Array(fs.readFileSync(path.join(H, '../emb.bin')).buffer.slice(0));
const lib = new S.Library(J, q, JSON.parse(fs.readFileSync(path.join(H, '../events.json'))).events);
const cache = JSON.parse(fs.readFileSync(path.join(H, 'emb-cache.json')));
const out = {};
for (const id of process.argv.slice(2)) {
  const P = JSON.parse(fs.readFileSync(path.join(H, 'poems.json'))).poems.find(p => p.id === id);
  const ph = S.parse(P.text), sims = ph.map(p => lib.sims(cache[p.text])), A = S.run(lib, S.parse(P.text), sims, {});
  out[id] = A.cut.map(s => ({ scene: s.scene, op: s.op, thumb: J.shots[s.k].thumb, title: J.shots[s.k].title, home: s.src === s.home, line: ph[s.phrase].text }));
}
fs.writeFileSync('/private/tmp/claude-502/sheet.json', JSON.stringify(out));
