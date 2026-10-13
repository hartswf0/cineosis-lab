// Every beat of every WYGWYL take through the Grand Syntagmatique's own classifier (syntagma/metz.js): the count of each of Metz's
// eight kinds per take, and for each kind its clearest example (2-4 shots, no doubt). Writes explain/ep/metz.json.
// usage: node lab/explain/ep_metz.js
const fs = require('fs'), path = require('path'), L = path.join(__dirname, '..');
const M = require(path.join(L, 'syntagma/metz.js')), D = JSON.parse(fs.readFileSync(path.join(L, 'syntagma/syntagma-data.json')));
const out = { types: M.TYPES, path: M.PATH, versions: {}, ex: {}, cdn: D.cdn };
for (const v of D.versions) {
  const shots = v.shots.map(s => ({ t0: s[0], t1: s[1], id: s[2], title: s[3], year: s[4], src: s[5], thumb: s[6], in: s[7], st: s[8], sg: s[9] }));
  const count = {};
  for (const b of D.beats) {
    const sh = M.members(shots, b[2], b[3]), c = M.classify(sh); count[c.t] = (count[c.t] || 0) + 1;
    const ok = !sh.some(s => s.src === 'all-my-babies' || /jfk/i.test(s.src + s.title)) && !c.doubt && !c.insert && sh.length >= (c.t === 1 ? 1 : 2) && sh.length <= 4 && b[3] - b[2] >= 7;
    if (ok) { const prev = out.ex[c.t], score = (c.t === 1 ? 1 : sh.length) + (v.slug === 'scenes' && c.t >= 6 ? 1 : 0);
      if (!prev || score > prev.score) out.ex[c.t] = { score, version: v.slug, beat: b[4], t0: b[2], t1: b[3], why: c.why, shots: sh.map(s => ({ t0: s.t0, t1: s.t1, title: s.title, year: s.year, src: s.src, thumb: D.cdn + s.thumb, st: s.st })) }; }
  }
  out.versions[v.slug] = count;
}
fs.writeFileSync(path.join(L, 'explain/ep/metz.json'), JSON.stringify(out));
console.log(out.versions); for (const t of Object.keys(M.TYPES)) { const e = out.ex[t]; console.log(t, M.TYPES[t].n, e ? `${e.version} ${e.t0}-${e.t1} ${e.why} | ${e.shots.map(s => s.title.slice(0, 18)).join(' / ')}` : 'NONE'); }
