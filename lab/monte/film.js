/* A Monte Carlo film, portable: the exact pieces it is made of (not the rules that made it), so a link plays the same film anywhere,
   and the words it already carries: a title found on its own opening card, and its chapters, in order.   Used by monte.html and monte-gallery.html. */
(function (root) {
  const CREDIT = /presents?|produced|production|copyright|picture|films?,? inc|organization|studios|haghe-film|pictoreels|technical|^a$|^an$|^the$/i;
  const b64 = s => btoa(unescape(encodeURIComponent(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const unb64 = s => decodeURIComponent(escape(atob(s.replace(/-/g, '+').replace(/_/g, '/'))));
  // [shot index, duration in centiseconds, spoken line or -1, flags (1 card · 2 silent · 4 return · 8 end), act or -1]
  function encode(M, f) { return b64(JSON.stringify({ v: 1, m: f.music, e: f.ev.map(e => [e.k, Math.round(e.dur * 100), e.line == null ? -1 : e.line, (e.kind === 'card' ? 1 : 0) | (e.silent ? 2 : 0) | (e.ret ? 4 : 0) | (e.end ? 8 : 0), e.act == null ? -1 : e.act]) })); }
  function decode(M, code) { const o = JSON.parse(unb64(code)); if (o.v !== 1) throw new Error('unknown film');
    const ev = o.e.map(([k, d, l, fl, a]) => { if (!M.shots[k]) throw new Error('missing piece'); const e = { kind: fl & 1 ? 'card' : 'shot', k, dur: d / 100 }; if (l >= 0) e.line = l; if (fl & 2) e.silent = true; if (fl & 4) e.ret = true; if (fl & 8) e.end = true; if (a >= 0) e.act = a; return e; });
    const cm = ev.filter(e => e.kind === 'card' && M.cardIx && M.cardIx.has(e.k)).map(e => M.cardMood[M.cardIx.get(e.k)]).filter(Boolean);
    const mood = cm.length ? cm[0].map((_, j) => cm.reduce((s, x) => s + x[j], 0) / cm.length) : M.moods.map(() => 0);
    return { seed: 'shared', ev, music: o.m, mood, code }; }
  const lines = (M, k) => M.shots[k].text.split(' / ').map(x => x.trim()).filter(Boolean);
  const clean = t => t.replace(/^["'“‘]+|["'”’]+$/g, '').replace(/\s+/g, ' ').trim();
  function chapters(M, f) { return f.ev.filter(e => e.kind === 'card' && !e.end && (!M.middle || M.middle.includes(e.k))).map(e => clean(lines(M, e.k).filter(x => !CREDIT.test(x) || x.split(' ').length > 4).join(' '))).filter(Boolean); }
  // the title: what an opening card announces after a bare PRESENTS ("CHEVROLET / PRESENTS / OVER / THE WAVES"); failing that, the film's last line
  function title(M, f) { const op = f.ev[0] && f.ev[0].kind === 'card' ? lines(M, f.ev[0].k) : [], j = op.findIndex(x => /^presents$/i.test(x));
    const named = j >= 0 ? op.slice(j + 1).filter(x => !CREDIT.test(x) && !/^in$/i.test(x)) : [];
    let t = named.length ? named.join(' ') : (chapters(M, f).slice(-1)[0] || '');
    t = clean(t.split(/(?<=[.!?])\s/)[0]); return t.length > 44 ? t.slice(0, 42).replace(/\s\S*$/, '') + '…' : t; }
  // a print, exactly as evolution.json records it (its pieces by id), as a film
  function fromPrint(M, b) { const ix = M._ix || (M._ix = new Map(M.shots.map((s, k) => [s.i, k])));
    const li = l => l ? M.lines.findIndex(x => x.i === l.i && Math.abs(x.t0 - l.t0) < .02) : -1, mi = M.music.findIndex(x => x.i === (b.music && b.music.i));
    const e = b.ev.map(x => [ix.get(x.i), Math.round(x.dur * 100), li(x.line), (x.kind === 'card' ? 1 : 0) | (x.silent ? 2 : 0) | (x.ret ? 4 : 0) | (x.end ? 8 : 0), x.act == null ? -1 : x.act]);
    if (e.some(x => x[0] == null)) throw new Error('missing piece'); return decode(M, b64(JSON.stringify({ v: 1, m: Math.max(0, mi), e }))); }
  const seconds = f => Math.round(f.ev.reduce((s, e) => s + e.dur, 0));
  const api = { fromPrint, encode, decode, chapters, title, seconds };
  if (typeof module !== 'undefined') module.exports = api; else root.MonteFilm = api;
})(this);
