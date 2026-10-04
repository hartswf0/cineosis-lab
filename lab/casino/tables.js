/* THE MONTE CARLO CASINO: twelve tables, one house.
   Every table plays the same round — the film plays, a gap opens (in the picture, in the sound, or both), each player is dealt a hand,
   chips are bet, the house rolls, the visions play, a gold chip is laid, and the winner is cut into the film — but each table opens a
   different gap and deals a different hand. The house is the Monte Carlo dealer: every chip on a card buys imagined continuations of it
   (rollouts through the archive's judged shots), the continuation it keeps finding is that card's vision, and the house lays one secret
   chip of its own where nobody looked.
   Material: monte/material.json (via monte/sim.js), casino/deck.json (casino/build_deck.py). */
(function (root) {
  const MC = root.MonteCinema;
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const pick = (R, xs) => xs[Math.floor(R() * xs.length)], shuffle = (R, xs) => { xs = xs.slice(); for (let k = xs.length - 1; k > 0; k--) { const j = Math.floor(R() * (k + 1)); [xs[k], xs[j]] = [xs[j], xs[k]]; } return xs; };
  const KEYS = ['A', 'B', 'C'];
  // ---- the house: where a card could lead, rolled again and again; the future it keeps finding is the vision
  function House(M, D) {
    const good = M.good, used = new Set(), ix = new Map(M.shots.map((s, k) => [s.i, k]));
    const near = (a, b) => MC.dot(M.SE[a], M.SE[b]);
    function rollout(R, from, len, pool = good) { const seq = []; let prev = from;
      for (let s = 0; s < len; s++) { let best = null, bv = -9;
        for (let t = 0; t < 70; t++) { const c = pick(R, pool); if (c === prev || seq.includes(c) || used.has(c)) continue;
          const v = M.shots[c].score / 10 - (prev != null ? Math.abs(near(prev, c) - .72) * 1.6 : 0) + R() * .45; if (v > bv) { bv = v; best = c; } }
        if (best == null) break; seq.push(best); prev = best; }
      const sc = seq.reduce((a, k) => a + M.shots[k].score / 10, 0) / Math.max(1, seq.length); return { seq, score: sc }; }
    // chips become rollouts: n futures for a card, counted by the spine (the two shots after it) they keep returning to
    function roll(R, from, chips, len = 3) { const n = 2 + chips * 4, spines = new Map(); let all = [];
      for (let k = 0; k < n; k++) { const r = rollout(R, from, len); all.push(r); const key = r.seq.slice(0, 2).join('>'); const e = spines.get(key) || { n: 0, best: r }; e.n++; if (r.score > e.best.score) e.best = r; spines.set(key, e); }
      const top = [...spines.values()].sort((a, b) => b.n - a.n || b.best.score - a.best.score)[0];
      return { n, spines: [...spines.entries()].map(([k, v]) => ({ spine: k.split('>').map(Number), n: v.n })).sort((a, b) => b.n - a.n), best: top ? top.best : { seq: [], score: 0 }, all }; }
    return { roll, rollout, used, ix, near };
  }
  // ---- what a piece is: a shot (k, from the material), a clip (id, from the deck), a frozen card, black, a line heard, the music bed
  const shot = (k, dur = 2.6, x = {}) => Object.assign({ k, dur }, x), clip = (id, dur = 2.6, x = {}) => Object.assign({ id, dur }, x);
  const lineOf = (M, j) => ({ i: M.lines[j].i, t0: M.lines[j].t0, t1: M.lines[j].t1, text: M.lines[j].text, film: M.lines[j].film, year: M.lines[j].year });
  const lineDur = L => Math.max(2.4, L.t1 - L.t0 + .8);
  const shotCard = (M, key, k, x = {}) => Object.assign({ key, kind: 'shot', k, label: M.shots[k].film || '', thumbK: k }, x);
  const goodShots = (M, R, n, avoid) => shuffle(R, M.good.filter(k => !avoid.has(k))).slice(0, n);
  // every table: deal(ctx) -> { setup: pieces the TV plays to open the gap, prompt, cards[3] }; vision(ctx, card, roll) -> { pieces, note }
  // optional: truth(ctx) -> the card that was really so (a quiz table), houseBets(ctx) -> the house's visible chips (THE HOUSE)
  const TABLES = [
    { id: 'seam', name: 'The Seam', n: 'I', gap: 'SOUND LEADS', rule: 'Rounds open only where one piece of music fades into the next. The picture goes dark; the new music has not said what it is for. Bet on the image it summons.',
      deal(c) { const m0 = c.music, m1 = (m0 + 1 + Math.floor(c.R() * (c.M.music.length - 1))) % c.M.music.length; c.nextMusic = m1;
        return { setup: [{ black: true, dur: 3.2, musicTo: m1, note: 'THE SEAM' }], prompt: 'WHAT SHOULD THIS MUSIC BECOME?', cards: goodShots(c.M, c.R, 3, c.used).map((k, n) => shotCard(c.M, KEYS[n], k)) }; },
      vision(c, card, r) { return { pieces: [shot(card.k, 3.2, { musicTo: c.nextMusic }), ...r.best.seq.map(k => shot(k))] }; } },
    { id: 'stop', name: 'Stop Projector', n: 'II', gap: 'THE FILM STOPS ITSELF', rule: 'A 1970s classroom card stops the film: STOP PROJECTOR — DISCUSS FILM. Discuss. Then bet on the card the story says next.',
      deal(c) { const M = c.M, stop = M.stop[0], beat = c.beat = (c.beat ?? -1) + 1, b = beat % 5, pool = shuffle(c.R, (M.story[b] || M.middle).filter(k => !c.used.has(k)));
        return { setup: stop != null ? [shot(stop, 3.4, { card: true, mute: true, note: 'DISCUSS FILM' })] : [], prompt: 'WHAT DOES THE FILM SAY NEXT?',
          cards: pool.slice(0, 3).map((k, n) => ({ key: KEYS[n], kind: 'card', k, label: M.shots[k].text.replace(/ \/ /g, ' ').replace(/"?ALICE IN WONDERLAND"?|V\.H\. Productions Co\./g, '').trim(), thumbK: k })) }; },
      vision(c, card, r) { const M = c.M, A = M.answer.get(card.k), words = A ? [...A] : [];
        const answer = words.length ? M.good.filter(k => words.some(w => M.words[k].has(w)) && !c.used.has(k)) : []; const first = answer.length ? pick(c.R, answer) : r.best.seq[0];
        return { pieces: [shot(card.k, 3.2, { card: true }), ...(first != null ? [shot(first)] : []), ...r.best.seq.filter(k => k !== first).slice(0, 2).map(k => shot(k))] }; },
      from(c, card) { return null; } },
    { id: 'wrong', name: 'The Wrong Card', n: 'III', gap: 'THE ARCHIVE DEALS THE NEIGHBOUR', rule: 'You bet on a shot; the archive plays the clip that came next in its own film. Story by adjacency: you can lean on it, never steer it.',
      deal(c) { const M = c.M, have = shuffle(c.R, M.good.filter(k => c.D.next[M.shots[k].i] && c.D.next[M.shots[k].i][1] && !c.used.has(k))).slice(0, 3);
        return { setup: [], prompt: 'WHICH SHOT? (THE ARCHIVE WILL PLAY ITS NEIGHBOUR)', cards: have.map((k, n) => shotCard(c.M, KEYS[n], k)) }; },
      vision(c, card, r) { const nb = c.D.next[c.M.shots[card.k].i][1]; return { pieces: [clip(nb[0], Math.min(3.4, nb[1] || 3), { note: 'WHAT CAME NEXT' }), ...r.best.seq.slice(0, 2).map(k => shot(k))], note: 'you bet on one shot; the archive played the one after it' }; } },
    { id: 'wing', name: 'Wing Nuts', n: 'IV', gap: 'BLIND HANDOFF', rule: 'A voice from one film plays over black. You only get the strict judge’s description of three pictures, not the pictures. Bet on which one the joke survives.',
      deal(c) { const J = c.D.jokes || [], j = pick(c.R, J.filter(x => c.M.shots[c.ix.get(x[0])] && !c.used.has(c.ix.get(x[0])))); c.joke = j; const L = lineOf(c.M, j[1]);
        const right = c.ix.get(j[0]), others = goodShots(c.M, c.R, 2, new Set([...c.used, right]));
        return { setup: [{ black: true, dur: lineDur(L), line: L, mute: true, note: '“' + L.text + '”' }], prompt: 'WHICH PICTURE IS THIS VOICE ABOUT?',
          cards: shuffle(c.R, [right, ...others]).map((k, n) => ({ key: KEYS[n], kind: 'blind', k, label: c.M.shots[k].why || 'a picture', thumbK: null })) }; },
      vision(c, card, r) { const L = lineOf(c.M, c.joke[1]); return { pieces: [shot(card.k, lineDur(L) + 1, { line: L, mute: true }), ...r.best.seq.slice(0, 2).map(k => shot(k))] }; },
      truth(c) { return c.ix.get(c.joke[0]); } },
    { id: 'reject', name: 'The Reject Bin', n: 'V', gap: 'ONLY THE REFUSED', rule: 'Every card here was rejected by the strict judge, with its reason printed on it. Make something precise out of what was refused. The judge jeers.',
      deal(c) { const R = shuffle(c.R, c.D.rejects).slice(0, 3); c.rej = R;
        return { setup: [], prompt: 'BET ON A REJECT', cards: R.map((x, n) => ({ key: KEYS[n], kind: 'clip', id: x.i, label: 'REJECTED: ' + x.why, sub: (x.film || '') + (x.year ? ' · ' + x.year : ''), thumbId: x.i })) }; },
      vision(c, card) { const me = c.D.rejects.find(x => x.i === card.id), kin = shuffle(c.R, c.D.rejects.filter(x => x !== me && x.sees.some(w => me.sees.includes(w)))).slice(0, 2);
        const more = kin.length < 2 ? shuffle(c.R, c.D.rejects.filter(x => x !== me)).slice(0, 2 - kin.length) : [];
        return { pieces: [me, ...kin, ...more].map(x => clip(x.i, 2.6, { note: 'REJECTED: ' + x.why })), note: 'the judge: “' + me.why + '”' }; } },
    { id: 'century', name: 'Same Title, Wrong Century', n: 'VI', gap: 'ONE WORD, A HUNDRED YEARS', rule: 'A word that titles films across the century. Three clips, three decades. Bet on the decade that answers it best; the vision cuts the century together from there.',
      deal(c) { const w = pick(c.R, c.D.decades); c.word = w; const ds = shuffle(c.R, Object.keys(w.decades)).slice(0, 3);
        return { setup: [{ black: true, dur: 2.6, title: w.word.toUpperCase(), note: 'THE WORD' }], prompt: `“${w.word.toUpperCase()}”: WHICH DECADE?`,
          cards: ds.map((d, n) => { const x = w.decades[d][0]; return { key: KEYS[n], kind: 'clip', id: x[0], label: d + 's', sub: x[1], thumbId: x[0], decade: +d }; }) }; },
      vision(c, card) { const w = c.word, ds = Object.keys(w.decades).map(Number).sort((a, b) => Math.abs(a - card.decade) - Math.abs(b - card.decade)).slice(0, 4);
        return { pieces: ds.map(d => clip(w.decades[d][0][0], 2.4, { note: d + 's · ' + w.decades[d][0][1] })), note: 'a century of “' + w.word + '”' }; } },
    { id: 'mishear', name: 'The Mishearing', n: 'VII', gap: 'WHAT WAS SAID?', rule: 'The archive’s speech-to-text mishears. Three versions of a line: one is what was said, two are what a machine could have heard. Bet; then the archive speaks.',
      deal(c) { const m = pick(c.R, c.D.mishear), L = lineOf(c.M, m.line); c.mis = { m, L };
        const vs = shuffle(c.R, [{ t: L.text, real: true }, ...m.fakes.map(t => ({ t }))]); c.mis.real = KEYS[vs.findIndex(v => v.real)];
        return { setup: [], prompt: 'WHICH DID THEY REALLY SAY?', cards: vs.map((v, n) => ({ key: KEYS[n], kind: 'text', label: '“' + v.t + '”', sub: L.film || '' })) }; },
      vision(c, card) { const L = c.mis.L; return { pieces: [clip(L.i, lineDur(L), { at: L.t0, own: true, line: L, mute: true, note: '“' + L.text + '”' })], note: card.key === c.mis.real ? 'that is what was said' : 'they said: “' + L.text + '”', once: true }; },
      truth(c) { return c.mis.real; } },
    { id: 'refusal', name: 'The Refusal', n: 'VIII', gap: 'A CHARGE YOU CANNOT ARGUE', rule: 'An archival card makes an accusation. Answer it with a routine (a pause, a line from another film, room for the laugh, a solemn exit) or with silence. Some charges the house refuses to joke about.',
      deal(c) { const pool = [...c.D.routines, ...c.D.refused], ch = pick(c.R, pool); c.charge = ch; const chK = c.ix.get(ch.charge);
        const rs = (ch.routines || []).slice().sort((a, b) => b.giggle - a.giggle).slice(0, 2);
        const cards = rs.map((r, n) => ({ key: KEYS[n], kind: 'routine', k: c.ix.get(r.shot), r, label: '“' + c.M.lines[r.line].text + '”', sub: (c.M.shots[c.ix.get(r.shot)] || {}).why || '', thumbK: c.ix.get(r.shot) }));
        const quiet = [{ kind: 'silence', secs: 3, label: 'SILENCE', sub: 'say nothing; hold the room' }, { kind: 'silence', secs: 6, label: 'A LONG SILENCE', sub: 'hold it until it hurts' }, { kind: 'silence', secs: 0, label: 'CUT AWAY', sub: 'straight to a solemn shot' }];
        if (!rs.length) c.refusedNow = true;   // a charge the house refused to joke about: only silences are legal
        for (const q of quiet) if (cards.length < 3) cards.push(Object.assign({ key: KEYS[cards.length] }, q));
        return { setup: chK != null ? [shot(chK, 3.6, { card: true, note: 'THE CHARGE' })] : [], prompt: 'HOW DO WE ANSWER?', cards }; },
      vision(c, card) { const chK = c.ix.get(c.charge.charge); if (card.kind === 'silence') { const ex = pick(c.R, c.M.good);
          return { pieces: [shot(chK, 3, { card: true }), ...(card.secs ? [{ black: true, dur: card.secs, mute: true, note: '…' }] : []), shot(ex, 3)], note: c.refusedNow ? 'the house refuses to joke about this' : card.label.toLowerCase() }; }
        const r = card.r, L = lineOf(c.M, r.line), ex = c.ix.get(r.exit);
        return { pieces: [shot(chK, 3, { card: true }), shot(card.k, r.pause / 1000 + lineDur(L) + r.laugh / 1000, { line: L, lineAt: r.pause / 1000, mute: true, note: '[' + (r.mech || '').toUpperCase() + ']' }), ...(ex != null ? [shot(ex, 3.2, { note: 'EXIT' })] : [])] }; } },
    { id: 'missing', name: 'The Missing Reel', n: 'IX', gap: 'THE PICTURE IS LOST', rule: 'A voice survives; its picture is lost. Bet on what the lost reel showed. The house knows: the voice’s own film is one of the cards.',
      deal(c) { const J = c.D.jokes || []; const j = pick(c.R, J), L = lineOf(c.M, j[1]); c.lost = L;
        const others = goodShots(c.M, c.R, 2, c.used);
        const cards = shuffle(c.R, [{ kind: 'clip', id: L.i, own: true, thumbId: L.i }, ...others.map(k => ({ kind: 'shot', k, thumbK: k }))]).map((x, n) => Object.assign(x, { key: KEYS[n], label: 'reel ' + KEYS[n] + '?' }));
        c.lostKey = cards.find(x => x.own).key;
        return { setup: [{ black: true, dur: lineDur(L), line: L, mute: true, title: 'REEL MISSING', note: '“' + L.text + '”' }], prompt: 'WHAT DID THE LOST REEL SHOW?', cards }; },
      vision(c, card) { const L = c.lost; return { pieces: [card.own ? clip(L.i, lineDur(L) + .6, { at: L.t0, own: true, line: L, mute: true }) : shot(card.k, lineDur(L) + .6, { line: L, mute: true })], note: card.own ? 'the reel itself' : 'a reel that never was' }; },
      truth(c) { return c.lostKey; } },
    { id: 'madness', name: 'Rain of Madness', n: 'X', gap: 'THE STUDIO HAS NOTES', rule: 'Every round the studio hands down a mandate. Toy sales want horses; the brick rule allows only the strictest frames. Make the film anyway. The commentary track is read from the house’s own numbers.',
      deal(c) { const M = c.M, md = pick(c.R, MANDATES); c.mandate = md; const pool = M.good.filter(k => md.ok(M, k) && !c.used.has(k)), hand = shuffle(c.R, pool.length >= 3 ? pool : M.good).slice(0, 3);
        return { setup: [{ black: true, dur: 3, title: md.name, note: 'MANDATE: ' + md.say }], prompt: 'MANDATE: ' + md.name, cards: hand.map((k, n) => shotCard(M, KEYS[n], k)) }; },
      vision(c, card, r) { const md = c.mandate, fits = r.all.filter(x => x.seq.every(k => md.ok(c.M, k))).length;
        return { pieces: [shot(card.k), ...r.best.seq.map(k => shot(k))], note: `COMMENTARY: we shot ${r.n} versions. ${fits} obeyed the studio. You are watching ${md.ok(c.M, r.best.seq[0] ?? card.k) ? 'one that did' : 'one that did not'}.` }; } },
    { id: 'spine', name: 'The Spine', n: 'XI', gap: 'SEE THE PATTERN', rule: 'The house flashes twelve imagined futures. Bet on the two-shot spine that kept coming back. No percentages: the repetition is the evidence.',
      deal(c) { const M = c.M, from = c.lastK ?? pick(c.R, M.good), r = c.H.roll(c.R, from, 2, 3); c.spineRoll = r;
        const top = r.spines.slice(0, 3); while (top.length < 3) top.push({ spine: c.H.rollout(c.R, from, 2).seq, n: 0 });
        const flash = r.all.slice(0, 12).map(x => x.seq.slice(0, 2)).flat().map(k => shot(k, .42, { card: true }));   // twelve futures, flashed as stills: too fast for video
        const cards = shuffle(c.R, top).map((s, n) => ({ key: KEYS[n], kind: 'spine', spine: s.spine, n: s.n, label: s.spine.map(k => (M.shots[k] || {}).why || '').join(' → '), thumbK: s.spine[0], thumbK2: s.spine[1] }));
        c.spineTruth = cards.slice().sort((a, b) => b.n - a.n)[0].key;
        return { setup: flash, prompt: 'WHICH SPINE KEPT COMING BACK?', cards }; },
      vision(c, card) { return { pieces: card.spine.map(k => shot(k, 2.8)), note: `this spine came back ${card.n} time${card.n === 1 ? '' : 's'} in ${c.spineRoll.n} futures` }; },
      truth(c) { return c.spineTruth; } },
    { id: 'house', name: 'The House Plays Against You', n: 'XII', gap: 'THE CRITIC BETS TOO', rule: 'The house critic lays its chips in the open, on the shot its taste prefers. Then the gold chips decide whose vision is cut: the room’s or the house’s. A running score: ROOM against HOUSE.',
      deal(c) { const hand = goodShots(c.M, c.R, 3, c.used); return { setup: [], prompt: 'BEAT THE HOUSE', cards: hand.map((k, n) => shotCard(c.M, KEYS[n], k)) }; },
      vision(c, card, r) { return { pieces: [shot(card.k), ...r.best.seq.map(k => shot(k))] }; },
      houseBets(c, cards) { const M = c.M; const best = cards.slice().sort((a, b) => M.shots[b.k].score - M.shots[a.k].score || MC.dot(M.SE[b.k], M.mu) - MC.dot(M.SE[a.k], M.mu))[0]; return { [best.key]: 4 }; } },
  ];
  // the studio's mandates (Rain of Madness): each a constraint on what may be shot
  const MANDATES = [
    { name: 'MORE HORSES', say: 'toy sales want horses', ok: (M, k) => /horse|cavalr|carousel/i.test((M.shots[k].why || '') + (M.shots[k].sees || []).join(' ')) },
    { name: 'THE BRICK RULE', say: 'only frames the judge scored 9 or 10', ok: (M, k) => M.shots[k].score >= 9 },
    { name: 'NO COLOUR', say: 'the studio has run out of colour', ok: (M, k) => M.shots[k].colour < .15 },
    { name: 'FACES ONLY', say: 'test audiences want faces', ok: (M, k) => /face|man|woman|men|girl|boy|people|row/i.test(M.shots[k].why || '') },
    { name: 'NO PEOPLE', say: 'the cast is on strike', ok: (M, k) => !/man|woman|men|girl|boy|people|figure|crowd|dancer|guard/i.test(M.shots[k].why || '') },
    { name: 'PINK', say: 'the merchandise is pink', ok: (M, k) => /pink|pastel|rose/i.test(M.shots[k].why || '') },
    { name: 'DEAD CENTRE', say: 'the director insists on symmetry', ok: (M, k) => /centre|center|symmetr/i.test(M.shots[k].why || '') },
  ];
  root.Casino = { TABLES, MANDATES, House, rng, shuffle, pick, KEYS };
})(typeof window !== "undefined" ? window : globalThis);
