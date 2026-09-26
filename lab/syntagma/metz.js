/* Metz's large syntagmatic category, applied to the image track of a found-footage cut.
   A cut is a list of shots; each shot = {t0, t1, id, src, st, dur, sg}. The slots are the
   suite's beats (units of the scenario), so every cut is divided on the same frame and one
   slot can be commuted against the same slot in another cut.
   Only the image track is read, as in Metz's table; the voice is used for punctuation. */
(function (root) {
  const TYPES = {
    1: { n: 'autonomous shot', k: 'AS' }, 2: { n: 'parallel syntagma', k: 'PAR' }, 3: { n: 'bracket syntagma', k: 'BR' },
    4: { n: 'descriptive syntagma', k: 'DESC' }, 5: { n: 'alternate syntagma', k: 'ALT' }, 6: { n: 'scene', k: 'SC' },
    7: { n: 'episodic sequence', k: 'EP' }, 8: { n: 'ordinary sequence', k: 'SEQ' } };
  // the dichotomies, top to bottom; each type's path through them
  const PATH = { 1: ['one'], 2: ['many', 'achron', 'alt'], 3: ['many', 'achron', 'noalt'], 4: ['many', 'chron', 'desc'],
    5: ['many', 'chron', 'narr', 'altn'], 6: ['many', 'chron', 'narr', 'lin', 'cont'], 7: ['many', 'chron', 'narr', 'lin', 'disc', 'org'], 8: ['many', 'chron', 'narr', 'lin', 'disc', 'scat'] };
  const MIN = 1;   // a shot belongs to a slot it overlaps by at least this many seconds (or its whole length)

  function members(shots, a, b) {
    return shots.filter(s => { const o = Math.min(s.t1, b) - Math.max(s.t0, a); return o >= Math.min(MIN, (s.t1 - s.t0) * .5, (b - a) * .5); });
  }
  function runs(list) { const r = []; list.forEach(s => { const last = r[r.length - 1]; if (last && last.src === s.src) last.shots.push(s); else r.push({ src: s.src, shots: [s] }); }); return r; }
  // gap in source time between consecutive shots of one source: null when unknown
  function gaps(sh) {
    const g = [];
    for (let i = 1; i < sh.length; i++) {
      const a = sh[i - 1], b = sh[i];
      if (a.id === b.id) g.push(b.in - (a.in + (a.t1 - a.t0)));
      else if (a.st != null && b.st != null) g.push(b.st - (a.st + (a.t1 - a.t0)));
      else g.push(null);
    }
    return g;
  }
  function linear(sh) {   // one source: scene / episodic / ordinary / descriptive
    const g = gaps(sh), known = g.filter(x => x != null);
    const doubt = known.length < g.length;
    if (known.some(x => x < -2)) return { t: 4, doubt, why: 'screen order runs against source order' };
    if (!known.length) return { t: 8, doubt: true, why: 'one film, source order unknown' };
    if (known.every(x => x <= 2)) return { t: 6, doubt, why: 'one film, no time skipped' };
    if (known.every(x => x > 45)) return { t: 7, doubt, why: 'one film, long organised leaps' };
    return { t: 8, doubt, why: 'one film, moments skipped' };
  }
  function classify(sh) {
    if (!sh.length) return { t: 0, why: 'no shot' };
    if (sh.length === 1) return { t: 1, sub: 'sequence shot', why: 'one shot holds the whole slot' };
    const r = runs(sh), srcs = [...new Set(sh.map(s => s.src))];
    if (srcs.length === 1) return linear(sh);
    // a source that returns after another has intervened: images alternate in series
    const seen = new Set(); let alt = false; r.forEach(x => { if (seen.has(x.src)) alt = true; seen.add(x.src); });
    if (alt) {
      const series = srcs.map(s => sh.filter(x => x.src === s)).filter(x => x.length > 1);
      const ok = series.length >= 1 && series.every(x => { const g = gaps(x); return g.every(v => v == null || v > -2); });
      const known = series.every(x => gaps(x).every(v => v != null));
      return ok ? { t: 5, doubt: !known, why: 'two films alternate, each moving forward' } : { t: 2, why: 'motifs alternate with no time between them' };
    }
    // one film carries the slot, one short shot of another cuts in: that film's treatment, with an insert
    const dur = s => s.t1 - s.t0, tot = sh.reduce((a, s) => a + dur(s), 0);
    const big = r.filter(x => x.shots.length > 1).sort((a, b) => b.shots.length - a.shots.length)[0];
    if (big && big.shots.reduce((a, s) => a + dur(s), 0) / tot >= .6) {
      const c = linear(big.shots); return { ...c, insert: true, why: c.why + ', with an insert' };
    }
    return { t: 3, why: 'shots from ' + srcs.length + ' films, no time between them: a category' };
  }
  // punctuation at a join: ⌒ a shot runs across it; ■ poem ends; ‖ the voice breathes; ! no breath but the image jumps regime; o plain cut
  function punct(prevShots, nextShots, joinT, poemEnds, pause, regimeOf) {
    if (poemEnds) return '■';
    const a = prevShots[prevShots.length - 1], b = nextShots[0];
    if (a && b && a === b) return '⌒';
    if (pause > 1.2) return '‖';
    if (a && b && regimeOf(a.sg) !== regimeOf(b.sg)) return '!';
    return 'o';
  }
  const PUNCT = { 'o': 'plain cut', '⌒': 'overlap: one shot ends a segment and begins the next', '■': 'the poem ends', '‖': 'the voice breathes at the join', '!': 'montage with effect: no breath, the image jumps regime' };
  root.Metz = { TYPES, PATH, PUNCT, members, classify, punct, runs };
  if (typeof module !== 'undefined') module.exports = root.Metz;
})(typeof window !== 'undefined' ? window : globalThis);
