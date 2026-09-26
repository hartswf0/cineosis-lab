// Metz's reading of every beat in every WYGWYL cut, with the Grand Syntagmatique's own classifier (lab/syntagma/metz.js).
// node lab/matrix/metz_read.js  → prints JSON {cut: [{beat, type, key, name, why, doubt, insert}]} on stdout
const path = require('path'), fs = require('fs');
const LAB = path.dirname(__dirname);
const Metz = require(path.join(LAB, 'syntagma', 'metz.js'));
const D = JSON.parse(fs.readFileSync(path.join(LAB, 'syntagma', 'syntagma-data.json'), 'utf8'));
const out = {};
for (const v of D.versions) {
  const shots = v.shots.map(s => ({ t0: s[0], t1: s[1], id: s[2], title: s[3], year: s[4], src: s[5], thumb: s[6], in: s[7], st: s[8], sg: s[9] }));
  out[v.slug] = D.beats.map(b => {
    const m = Metz.members(shots, b[2], b[3]), r = Metz.classify(m), T = Metz.TYPES[r.t] || { n: 'none', k: '—' };
    return { beat: b[0], type: r.t, key: T.k, name: T.n, why: r.why, doubt: !!r.doubt, insert: !!r.insert,
             shots: m.map(s => ({ id: s.id, title: s.title, year: s.year, src: s.src, t0: s.t0, t1: s.t1, in: s.in, sg: s.sg, thumb: s.thumb })) };
  });
}
process.stdout.write(JSON.stringify(out));
