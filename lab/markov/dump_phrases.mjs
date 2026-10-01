// every phrase the page can show without the server: the presets, the pairs, and the suite's lines
import fs from 'fs'; import { createRequire } from 'module'; const require = createRequire(import.meta.url);
const S = require('./engine.js'); const P = JSON.parse(fs.readFileSync('presets.json')); const K = JSON.parse(fs.readFileSync('../bets/kernel-data.json'));
const out = new Set();
const T = JSON.parse(fs.readFileSync('tests/poems.json')).poems.filter(p => p.text).map(p => p.text);
[...P.texts.map(t => t.text), ...P.pairs.flatMap(p => [p.a, p.b]), ...T].forEach(t => S.parse(t).forEach(p => out.add(p.text)));
K.films.forEach(f => S.parse(K.lines.filter(l => l.film === f.n).map(l => l.text).join('\n')).forEach(p => out.add(p.text)));
K.lines.forEach(l => S.parse(l.text).forEach(p => out.add(p.text)));
fs.writeFileSync('phrases.json', JSON.stringify([...out])); console.log(out.size, 'phrases');
