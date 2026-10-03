/* The Monte Carlo cinema. A rule set (a genome of 18 numbers) generates films from the archive by chance; a fixed critic scores
   each film from its embeddings (CLIP for pictures and words, CLAP for music); rule sets that make good films survive, cross and
   mutate. The same file runs offline (node) and in the browser.   Material: monte/material.json (monte/pack.py). */
(function (root) {
  // ---- the material
  function dec(b64, n) { const bin = typeof atob === 'function' ? atob(b64) : Buffer.from(b64, 'base64').toString('binary'); const a = new Int8Array(bin.length);
    for (let k = 0; k < bin.length; k++) a[k] = bin.charCodeAt(k) << 24 >> 24; const d = a.length / n, out = [];
    for (let r = 0; r < n; r++) { const v = new Float32Array(d); let s = 0; for (let k = 0; k < d; k++) { v[k] = a[r * d + k]; s += v[k] * v[k]; } s = Math.sqrt(s) || 1; for (let k = 0; k < d; k++) v[k] /= s; out.push(v); } return out; }
  const dot = (a, b) => { let s = 0; for (let k = 0; k < a.length; k++) s += a[k] * b[k]; return s; };
  function load(M) { M.SE = dec(M.shotEmb, M.shots.length); M.CT = dec(M.cardText, M.cards.length); M.LT = dec(M.lineEmb, M.lines.length);
    M.cardIx = new Map(M.cards.map((s, k) => [s, k])); M.plain = M.shots.map((s, k) => k).filter(k => !M.shots[k].title);
    const said = k => M.shots[k].text.split(' / ').some(x => !CREDIT.test(x) && (/^["'“]/.test(x) || /[a-z][.!?]["']?$/.test(x.trim())));   // a line someone says, even with a studio credit under it
    M.opening = M.cards.filter(k => /present|produced|picture|productions?|films?\b/i.test(M.shots[k].text) && !/\bend\b|einde|stop projector/i.test(M.shots[k].text) && !said(k));
    M.ending = M.cards.filter(k => /\bthe end\b|^end\b|einde/i.test(M.shots[k].text));
    M.middle = M.cards.filter(k => !M.opening.includes(k) && !M.ending.includes(k) && M.shots[k].score >= 5);
    M.opening = M.opening.filter(k => M.shots[k].score >= 7 && M.shots[k].text.split(' / ').length <= 6 && !/credits|cast of|direction|screenplay|photography|edited|narrated/i.test(M.shots[k].text));   // an opening, not a credit roll M.ending = M.ending.filter(k => M.shots[k].score >= 6 && /\bthe end\b/i.test(M.shots[k].text));   // Precisely So's floor: nothing the judge did not rate
    M.good = M.plain.filter(k => M.shots[k].score >= 7);
    // the story grammar. Precisely So worked because its cards, in order, told one: an invitation, a voyage, a door that will not open,
    // "That night.", the King. Each middle card is read for the beat it can play and for how much it speaks (dialogue, I/you/we, a sentence)
    M.beat = new Map(); M.speaks = new Map(); M.story = BEATS.map(() => []);
    for (const k of M.middle) { const segs = M.shots[k].text.split(' / '), keep = segs.filter(x => !CREDIT.test(x)), t = keep.join(' ');   // a credit line under a title does not silence it
      if (!keep.length || keep.length < segs.length / 2 || (t.match(FOREIGN) || []).length >= 2) continue;
      const b = [2, 3, 0, 1, 4].find(j => BEATS[j].re.test(t)) ?? -1; let sp = (/^["'“]/.test(t) ? .45 : 0) + (/\b(I|I'm|you|your|we|my|our|me)\b/i.test(t) ? .25 : 0) + (/[.!?"'-]$/.test(t.trim()) ? .15 : 0) + (b >= 0 ? .15 : 0);
      if (t === t.toUpperCase() && t.split(' ').length < 5) sp -= .15;
      M.speaks.set(k, Math.max(0, Math.min(1, sp))); if (b >= 0) { M.beat.set(k, b); M.story[b].push(k); } }
    M.middle = M.middle.filter(k => M.shots[k].score >= 6 || M.beat.has(k));   // a 5 only if it tells the story
    // the lexicon: every chapter card read by hand for the beat it plays and the pictures that answer it (monte/story.json). When it is
    // there, it replaces the guesses: only cards that tell a story are chapters, and the shots after a card are the ones that bear it out
    const word = w => w.toLowerCase().replace(/[^a-z-]/g, '').replace(/(es|s)$/, '');
    M.words = M.shots.map(x => new Set((x.sees && x.sees.length ? x.sees : (x.why || '').split(/[\s,;]+/)).map(word).filter(w => w.length > 2)));
    M.answer = new Map(); M.stop = [];
    if (M.lexicon) { const byId = new Map(M.shots.map((x, k) => [x.i, k])); M.beat = new Map(); M.story = BEATS.map(() => []); M.middle = [];
      for (const [i, L] of Object.entries(M.lexicon)) { const k = byId.get(i); if (k == null || !M.cardIx.has(k)) continue;
        if (L.beat === 'stop') { M.stop.push(k); continue; }
        const b = BEATS.findIndex(x => x.key === L.beat); if (b < 0) continue;
        M.beat.set(k, b); M.story[b].push(k); M.middle.push(k); M.answer.set(k, new Set(L.answer.map(word))); if (!M.speaks.has(k)) M.speaks.set(k, .5); } }
    const d = M.SE[0].length; M.mu = new Float32Array(d); M.SE.forEach(v => { for (let j = 0; j < d; j++) M.mu[j] += v[j] / M.SE.length; }); M.taste = null; return M; }
  // ---- the viewer's taste: shots marked yes (+) and no (-), and the films chosen, as one direction in CLIP space
  function taste(M, marks) { const d = M.mu.length, T = new Float32Array(d); let n = 0; const ix = new Map(M.shots.map((s, k) => [s.i, k]));
    for (const [i, w] of Object.entries(marks)) { const k = ix.get(i); if (k == null || !w) continue; for (let j = 0; j < d; j++) T[j] += w * (M.SE[k][j] - M.mu[j]); n++; }
    let s = 0; for (let j = 0; j < d; j++) s += T[j] * T[j]; s = Math.sqrt(s); if (!n || !s) return (M.taste = null); for (let j = 0; j < d; j++) T[j] /= s; return (M.taste = T); }
  const lean = (M, k) => { let s = 0; for (let j = 0; j < M.mu.length; j++) s += (M.SE[k][j] - M.mu[j]) * M.taste[j]; return s; };
  const BEATS = [{ key: 'want', name: 'the want', re: /\bparty|come to|bring a friend|introduc|partners|i'm going|going to|ready to launch|\bwant|\bwish|invit|\bmust\b|let's|how do you|qualifications/i },
    { key: 'journey', name: 'the journey', re: /\bsail|voyage|aboard|abroad|europe|pass the|\broad\b|highway|\btrain\b|flight|anchored|journey|\btrip|travel|out on|across|we saw|streets|vistas/i },
    { key: 'trouble', name: 'the trouble', re: /can't|cannot|wrong|mutiny|cyclone|\bburn|fire|flames|threat|darkness|stumbled|\bfell\b|\brent\b|chance|too close|danger|disaster|\bno,|ruins|earthquake|not want|axe|suspense/i },
    { key: 'night', name: 'that night', re: /\bnight\b|evening|that day|later|next morning|meanwhile|zeideravond|nacht|\bdusk|\bdawn|day and night/i },
    { key: 'arrival', name: 'the arrival', re: /\bking\b|coming|\bmeet\b|farewell|finished|ready for|arriv|at last|\bhome\b|welcome|races|graduat|saved|\\bhorses\\b|sight of a ship|highspot/i }];
  const CREDIT = /collaborator|produced|production|presents|copyright|music|narrated|commentary|cooperation|appreciation|consultant|supervisor|directed|manufactured|technical|investigator|official film|encyclop|erpi|correlated|\bpicture\b|films? inc|studios|acknowledged|haghe-film|pictoreels/i;
  const FOREIGN = /\b(de|het|een|van|werd|den|zocht|der|die|und|waren|naar|hun|men|op|ter)\b/gi;
  // the order a story's beats take, for a film of n acts
  const PLOT = { 3: [0, 2, 4], 4: [0, 1, 2, 4], 5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 2, 4], 7: [0, 1, 2, 1, 2, 3, 4] };
  // ---- the rules: each gene in [0,1], read through its range
  const GENES = [['acts', 3, 7, 'acts'], ['shots', 2, 5, 'shots per act'], ['card', 0, 1, 'a card opens an act'], ['voice', 0, 2.5, 'spoken lines per act'],
    ['wJudge', 0, 3, 'trust the judge'], ['wMatch', 0, 3, 'match cuts'], ['target', .55, .9, 'how alike a cut'], ['wText', 0, 3, 'cards borne out'], ['wVoice', 0, 3, 'words fit pictures'],
    ['ret', 0, 1, 'return to the first image'], ['exc', 0, 1, 'the last act breaks'], ['dur', 2.2, 3.0, 'seconds a shot'], ['silence', 0, .6, 'silent acts'],
    ['wRole', 0, 2, 'rule of three'], ['bw', 0, 1, 'black and white allowed'], ['temp', .05, .6, 'chance'], ['wColour', 0, 2, 'colour holds'], ['hold', 2.2, 3.2, 'seconds a card'], ['story', 0, 1, 'tell a story'], ['wSpeak', 0, 3, 'cards that speak']];
  const val = (g, k) => { const [, lo, hi] = GENES[k]; return lo + (hi - lo) * (g[k] == null ? .5 : g[k]); };
  const G = name => GENES.findIndex(x => x[0] === name);
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function pick(R, xs, score, temp) { const s = xs.map(score), mx = Math.max(...s), w = s.map(v => Math.exp((v - mx) / Math.max(.02, temp))), t = w.reduce((a, b) => a + b, 0); let r = R() * t;
    for (let k = 0; k < xs.length; k++) { r -= w[k]; if (r <= 0) return xs[k]; } return xs[xs.length - 1]; }
  const sample = (R, xs, n) => { const out = []; for (let k = 0; k < n; k++) out.push(xs[Math.floor(R() * xs.length)]); return [...new Set(out)]; };
  // ---- a film, generated by the rules (events: card | shot, with an optional spoken line on a shot)
  function generate(M, g, seed, avoid, spent) {   // spent: chapter cards its companions already tell   // avoid: a Set of shots this film may not begin with (its opening, first chapter, first shot)
    const A = avoid || new Set(), S = spent || new Set();
    const R = rng(seed), v = n => val(g, G(n)), temp = v('temp'), ev = [], used = new Set(), films = new Map();
    const thread = new Set();
    const seenAlike = k => { for (const u of used) if (!M.shots[u].title && dot(M.SE[u], M.SE[k]) > .93) return true; return false; };
    const acts = Math.round(v('acts')), story = M.lexicon ? true : R() < v('story'), plot = PLOT[acts] || [];   // with the lexicon every film tells one
    const opens = M.opening.filter(k => !A.has(k)), op = opens.length ? pick(R, sample(R, opens, 30), k => M.shots[k].score / 10 * v('wJudge'), temp) : null;
    if (op != null) { ev.push({ kind: 'card', k: op, dur: v('hold') }); used.add(op); }
    let prev = null, roleRun = [], first = null;
    for (let a = 0; a < acts; a++) {
      let card = null;
      const told = story && plot[a] != null ? M.story[plot[a]].filter(k => !used.has(k) && !S.has(k) && !(a === 0 && A.has(k))) : [];
      const cardScore = k => M.shots[k].score / 10 * v('wJudge') + (M.speaks.get(k) || 0) * v('wSpeak') + (thread.has(M.shots[k].film) ? 1.6 : 0) + (prev != null ? .5 * dot(M.CT[M.cardIx.get(k)], M.SE[prev]) * v('wText') : 0);
      if (told.length) card = pick(R, told, cardScore, temp);
      else if (M.middle.length && (a === 0 || R() < v('card'))) card = pick(R, sample(R, M.middle, 40).filter(k => !used.has(k) && !S.has(k) && !(a === 0 && A.has(k))), cardScore, temp);
      if (card != null && M.beat.has(card)) thread.add(M.shots[card].film);   // a story, once begun, keeps to its own cards where it can
      if (card != null) { const words = M.shots[card].text.split(/\s+/).length; ev.push({ kind: 'card', k: card, dur: Math.max(v('hold'), Math.min(4, 1.6 + words * .22)), act: a, beat: M.beat.get(card) }); used.add(card); }
      if (M.stop.length && story && plot[a] === 2 && R() < .5) { const st = M.stop.find(k => !used.has(k) && !S.has(k)); if (st != null) { ev.push({ kind: 'card', k: st, dur: 3.2, act: a, silent: true, stop: true }); used.add(st); } }   // the film stops itself, in silence
      const silent = R() < v('silence'), n = Math.max(1, Math.round(v('shots') + (R() - .5) * 2));
      const actShots = [];
      for (let s = 0; s < n; s++) {
        const last = a === acts - 1 && s === n - 1;
        if (false) { ev.push({ kind: 'shot', k: first, dur: v('dur') + .6, act: a, silent, ret: true }); actShots.push(first); continue; }   // Precisely So never shows a shot twice: no return to the first image
        const cand = sample(R, M.good, 220).filter(k => !used.has(k) && !S.has(k) && !(first == null && A.has(k)) && !seenAlike(k));   // S: what the other prints already show
        const cen = actShots.length ? actShots.map(k => M.SE[k]) : null;
        const k = pick(R, cand, c => { const S = M.shots[c]; let sc = S.score / 10 * v('wJudge');
          if (prev != null) { const sim = dot(M.SE[prev], M.SE[c]); sc -= Math.abs(sim - v('target')) * 3 * v('wMatch') / 3; sc -= Math.abs(S.colour - M.shots[prev].colour) * v('wColour') * .5; }
          if (card != null && s < 2) sc += dot(M.CT[M.cardIx.get(card)], M.SE[c]) * 4 * v('wText');
          if (card != null && s < 3 && M.answer.has(card)) sc += Math.min(2, hits(M.answer.get(card), M.words[c])) * 1.4 * v('wText');   // the picture answers the card
          if (roleRun.length >= 1 && roleRun[roleRun.length - 1] === S.role) sc += .35 * v('wRole');
          if (S.colour < .12) sc -= (1 - v('bw')) * 1.2;
          if (films.get(S.film)) sc -= .8 * films.get(S.film);
          if (last && cen && v('exc') > .5) sc += (1 - Math.max(...cen.map(e => dot(e, M.SE[c])))) * 2 * v('exc');   // the exception: unlike the act
          return sc; }, temp);
        if (k == null) continue;
        const e = { kind: 'shot', k, dur: v('dur') * (.85 + R() * .3), act: a, silent }; ev.push(e); used.add(k); actShots.push(k);
        if (first == null) first = k; films.set(M.shots[k].film, (films.get(M.shots[k].film) || 0) + 1);
        roleRun.push(M.shots[k].role); if (roleRun.length > 3) roleRun.shift(); prev = k;
      }
      // spoken lines this act, each laid on a shot it suits
      const lines = 0, shotsHere = ev.filter(e => e.kind === 'shot' && e.act === a && !e.line);
      for (let l = 0; l < lines && shotsHere.length; l++) {
        const e = shotsHere[Math.floor(R() * shotsHere.length)]; if (e.line != null) continue;
        e.line = pick(R, sample(R, M.lines.map((_, k) => k), 220), L => dot(M.LT[L], M.SE[e.k]) * 4 * v('wVoice'), temp);
        const ln = M.lines[e.line]; e.dur = Math.max(e.dur, ln.t1 - ln.t0 + .6);
      }
    }
    const endings = M.ending.filter(k => !S.has(k));   // each print its own last card
    if (endings.length) { const end = pick(R, sample(R, endings, 20), k => M.shots[k].score / 10, temp); ev.push({ kind: 'card', k: end, dur: v('hold'), end: true }); }
    // the score: the music whose mood is nearest the cards' words
    const cm = ev.filter(e => e.kind === 'card').map(e => M.cardMood[M.cardIx.get(e.k)]).filter(Boolean);
    const mood = cm.length ? cm[0].map((_, j) => cm.reduce((s, x) => s + x[j], 0) / cm.length) : M.moods.map(() => 0);
    const music = pick(R, M.music.map((_, k) => k), k => { const x = M.music[k].mood; return cos(x, mood) * 3; }, .3);
    return { seed, ev, music, mood };
  }
  const hits = (A, B) => { let n = 0; for (const w of A) if (B.has(w)) n++; return n; };
  const cos = (a, b) => { let s = 0, x = 0, y = 0; for (let k = 0; k < a.length; k++) { s += a[k] * b[k]; x += a[k] * a[k]; y += b[k] * b[k]; } return s / (Math.sqrt(x * y) || 1); };
  // ---- the critic: fixed, from the embeddings; each part in [0,1]
  const CRITIC = { anderson: .26, story: .18, cuts: .12, cards: .12, voice: 0, structure: .12, variety: .06, pace: .05, music: .05 };
  function critic(M, f, W = CRITIC) {
    const ev = f.ev, shots = ev.filter(e => e.kind === 'shot'), cards = ev.filter(e => e.kind === 'card'), P = {};
    P.anderson = ev.length ? ev.reduce((s, e) => s + M.shots[e.k].score, 0) / ev.length / 10 : 0;
    let c = [], cl = [], vl = [];
    for (let k = 1; k < ev.length; k++) if (ev[k].kind === 'shot' && ev[k - 1].kind === 'shot') { const s = dot(M.SE[ev[k - 1].k], M.SE[ev[k].k]); c.push(Math.exp(-(((s - .72) / .12) ** 2))); }
    P.cuts = c.length ? c.reduce((a, b) => a + b, 0) / c.length : 0;
    for (let k = 0; k < ev.length; k++) if (ev[k].kind === 'card' && !ev[k].end && M.cardIx.has(ev[k].k)) {
      const nx = ev.slice(k + 1, k + 3).filter(e => e.kind === 'shot'); if (!nx.length) continue;
      cl.push(Math.min(1, Math.max(0, (Math.max(...nx.map(e => dot(M.CT[M.cardIx.get(ev[k].k)], M.SE[e.k]))) - .17) / .12))); }
    P.cards = cl.length ? cl.reduce((a, b) => a + b, 0) / cl.length : 0;
    const asked = ev.map((e, k) => [e, k]).filter(([e]) => e.kind === 'card' && M.answer.has(e.k));
    if (asked.length) P.cards = .4 * P.cards + .6 * asked.filter(([e, k]) => ev.slice(k + 1, k + 3).some(x => x.kind === 'shot' && hits(M.answer.get(e.k), M.words[x.k]) > 0)).length / asked.length;
    for (const e of shots) if (e.line != null) vl.push(Math.min(1, Math.max(0, (dot(M.LT[e.line], M.SE[e.k]) - .17) / .12)));
    P.voice = vl.length ? (vl.reduce((a, b) => a + b, 0) / vl.length) * Math.min(1, vl.length / 3) : 0;
    let three = 0; for (let k = 2; k < shots.length; k++) if (M.shots[shots[k].k].role === M.shots[shots[k - 1].k].role && M.shots[shots[k].k].role === M.shots[shots[k - 2].k].role) three = 1;
    const chapters = ev.filter(e => e.kind === 'card' && !e.end && !M.opening.includes(e.k)).length;   // the film is told in chapters, in the archive's own cards
    P.structure = (cards.length && M.opening.includes(ev[0].k) ? .2 : 0) + (ev.length && ev[ev.length - 1].end ? .2 : 0) + (new Set(shots.map(e => e.k)).size === shots.length ? .2 : 0) + .2 * three + .2 * Math.min(1, chapters / 2);
    // the story: chapters that speak, in the order a story goes (want, journey, trouble, night, arrival), enough of them to be one
    const ch = ev.filter(e => e.kind === 'card' && !e.end && M.middle.includes(e.k)), bs = ch.map(e => M.beat.get(e.k)).filter(b => b != null);
    const speak = ch.length ? ch.reduce((a, e) => a + (M.speaks.get(e.k) || 0), 0) / ch.length : 0;
    let ord = 0; for (let k = 1; k < bs.length; k++) ord += bs[k] >= bs[k - 1] ? 1 : 0; const order = bs.length > 1 ? ord / (bs.length - 1) : 0;
    P.story = Math.min(1, Math.min(1, bs.length / 3) * (.45 * speak + .35 * order + .2 * new Set(bs).size / 5) / .85);
    P.variety = shots.length ? new Set(shots.map(e => M.shots[e.k].film)).size / shots.length : 0;
    const T = ev.reduce((s, e) => s + e.dur, 0); f.seconds = T; P.pace = T < 60 ? T / 60 : T > 95 ? Math.max(0, 1 - (T - 95) / 30) : 1;   // Precisely So's length: about seventy seconds, every one held
    P.yours = M.taste && shots.length ? Math.min(1, Math.max(0, .5 + 3 * shots.reduce((a, e) => a + lean(M, e.k), 0) / shots.length)) : 0;
    P.music = f.music != null ? Math.max(0, cos(M.music[f.music].mood, f.mood)) : 0;
    const tw = Object.values(W).reduce((a, b) => a + b, 0) || 1; f.parts = P; f.score = Object.entries(W).reduce((s, [k, w]) => s + w * (P[k] || 0), 0) / tw; return f.score;
  }
  // ---- evolution: rule sets that make good films survive, cross and mutate
  function evolve(M, opts = {}) {
    const R = rng(opts.seed || 1), P = opts.pop || 24, K = opts.films || 6, ELITE = opts.elite || 6, W = opts.critic || CRITIC;
    let pop = opts.start || Array.from({ length: P }, () => GENES.map(() => R())), gen = 0, history = [], best = null;
    function rate(g) { const fs = []; for (let k = 0; k < K; k++) { const f = generate(M, g, Math.floor(R() * 1e9)); critic(M, f, W); fs.push(f); } fs.sort((a, b) => b.score - a.score);
      return { g, fit: (fs[0].score + fs[1].score + fs[2].score) / 3, film: fs[0] }; }
    function step() { const rated = pop.map(rate).sort((a, b) => b.fit - a.fit);
      if (!best || rated[0].film.score > best.film.score) best = { g: rated[0].g, film: rated[0].film, gen };
      history.push({ gen, best: rated[0].fit, mean: rated.reduce((s, r) => s + r.fit, 0) / rated.length, g: rated[0].g.slice(), film: rated[0].film.score });
      const elite = rated.slice(0, ELITE).map(r => r.g), sigma = .14 * Math.pow(.97, gen); const next = elite.map(g => g.slice());
      while (next.length < P) { const a = elite[Math.floor(R() * elite.length)], b = elite[Math.floor(R() * elite.length)];
        next.push(a.map((x, k) => { let y = R() < .5 ? x : b[k]; if (R() < .35) { y += (R() + R() + R() - 1.5) * sigma * 2; } return Math.min(1, Math.max(0, y)); })); }
      pop = next; gen++; return history[history.length - 1]; }
    return { step, get best() { return best; }, get history() { return history; }, get pop() { return pop; } };
  }
    // what a film begins with: its opening card, its first chapter card, its first shot
  const starts = f => { const out = []; const c = f.ev.filter(e => e.kind === 'card' && !e.end).slice(0, 2), sh = f.ev.find(e => e.kind === 'shot'); c.forEach(e => out.push(e.k)); if (sh) out.push(sh.k); return out; };
  const api = { BEATS, starts, load, generate, critic, evolve, taste, lean, GENES, CRITIC, val, dot };
  if (typeof module !== 'undefined') module.exports = api; else root.MonteCinema = api;
})(this);
