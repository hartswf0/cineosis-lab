/* The Shannon engine: language arrives, and a finite archive answers with the next edit.

   Shannon's discrete channel has a finite repertoire, symbols that take time, and states that decide which symbols may follow.
   Here the repertoire is the edit (OPEN, CONTINUE, HOLD, REPEAT, RETURN, ALTERNATE, SUSPEND, COMPLETE, ABSENCE, INSERT),
   the time is the phrase's duration, and the state is the film so far: its strands (who), their anchors (where), what is unresolved.
   The words do not pick a clip. They change the constraints; the state machine picks an operation; the operation and the words
   together give a distribution over the 16,260 shots; the cut takes the most probable one (or a person corrects it).

   Three readouts are kept apart on purpose:
     H         entropy (bits) of that distribution: how spread the engine's belief is among plausible shots
     surprisal −log2 p of the shot actually taken: high when a person overrides the engine
     coverage  the best raw text–image similarity: whether the archive holds anything for these words at all
   A flat distribution can mean several good readings or nothing suitable; only coverage separates the two.

   fidelity() is the distortion measure (Shannon 1959): which relations of the language must survive into the cut, and did they.
   The criterion is an editor's decision, not the engine's. */
(function (root) {
  const OPS = {
    OPEN: 'open a strand: establish who and where',
    CONTINUE: 'continue the strand: the next moment, same film forward when it can',
    HOLD: 'hold: the shot stays while the sentence changes what it means',
    REPEAT: 'repeat the composition: recurrence is the same place, again',
    RETURN: 'return to the strand\'s place',
    ALTERNATE: 'cut back to the other strand, still unresolved',
    SUSPEND: 'suspend: the lead-up to an action, held, never completed',
    COMPLETE: 'complete an action: a departure, an arrival',
    ABSENCE: 'the same place, emptied',
    INSERT: 'insert: a shot from another time, then back',
    CUTAWAY: 'cut away: the scene\'s world has nothing for these words, so the film leaves it for one shot and comes back' };
  // the lexicon: every rule a person can read and change
  const LEX = {
    // recurrence in time, not anaphora: "every evening" repeats, "every blow of his hand" does not
    recur: /\b(every|each)\s+(day|days|evening|night|morning|afternoon|week|year|time|summer|winter|spring|autumn|hour|sunday|dawn|dusk)\b|\b(always|again and again|used to|daily|nightly|evenings|mornings|whenever|over and over|kept (?:on )?\w+ing)\b/i,
    once: /\b(once|one day|one night|that day|that night)\b/i,
    simul: /\b(while|meanwhile|as|at the same time|across the|elsewhere|on the other side)\b/i,
    succ: /\b(after|then|later|already|by the time|afterwards|before|until|next|finally)\b/i,
    neg: /\b(not|never|no|cannot|can't|couldn't|don't|doesn't|didn't|won't|wouldn't|nobody|nothing|nowhere)\b/i,
    rev: /^\s*(but|yet|though|although|instead|still)\b|\b(but|yet|instead)\b/i,
    ret: /\b(return(ed|s|ing)?|came back|come back|back to|back home|again)\b/i,
    mem: /\b(remember(ed|s)?|recall(ed)?|imagin(e|ed|es)|dream(ed|s|t)?|memory|memories|used to be)\b/i,
    absent: /\b(gone|empty|nobody|no one|vanished|missing|absent|disappeared|nothing (?:was )?left|nothing remained)\b/i,
    text: /\b(word|words|letter|letters|sign|signs|read|reads|write|writes|written|name|names|book|page|pages|poem|poems|script)\b/i,
    still: /\b(nothing had moved|nothing moved|still there|unchanged|the same as|stayed|stood still|as it was)\b/i,
    wait: /\b(wait(ed|s|ing)?|stay(ed|s)?|stood|sat|linger(ed)?|hold(s)?|held|watch(ed|es)?)\b/i,
    depart: /\b(leav(e|es|ing)|left|depart(ed|s)?|go(es)?|went|walk(ed|s)? away|ran|run|fled|escape[ds]?|way out)\b/i,
    arrive: /\b(arriv(e|ed|es)|came|come|enter(ed|s)?|home|return(ed|s)?)\b/i };
  const SUBJ = /\b(I|he|she|they|we|you)\b/i;
  const KIN = { he: 'father brother son husband man boy grandfather uncle king priest poet', she: 'mother sister daughter wife woman girl grandmother aunt queen',
                they: 'family children people neighbors neighbours friends crowd lovers parents' };
  const GENDER = {}; Object.entries(KIN).forEach(([g, ws]) => ws.split(' ').forEach(w => GENDER[w] = g));
  const NOUNSUBJ = /^(?:but|and|then|yet|while|after|as|so)?\s*(?:my|his|her|our|their|the|a|an)\s+(\w+)/i;
  const PLACE = /\b(across|in|at|inside|outside|on|by|into|through|from|to)\s+(?:the|a|an|my|his|her|our|their|this|that)\s+([a-z]+(?:\s(?:of\s)?[a-z]+)?)/i;
  // visible events each operation wants (indices into events.json)
  const EVW = { establish: [14, 15, 16, 17, 27, 28, 31, 32, 44, 59], wait: [0, 1, 2, 3, 57], depart: [4, 6, 7, 8, 9, 55], arrive: [5, 10, 11],
    empty: [12, 13], door: [3, 50, 51], interior: [15, 25, 32] };
  // cards: intertitles, title cards, diagrams, black frames. CLIP reads printed words, so these match text too easily; they need the line to be about words
  const THIN = .258;   // OpenAI CLIP: the bottom tenth of best-shot similarities across the test library
  const CARD = [65, 66, 67, 68], ROOM = [15, 23, 53, 18, 21, 19, 24];
  // who the strand is: a pronoun asks for a figure the viewer can take as that person
  const WHO = { he: [60, 39, 40, 63], she: [61, 41, 38, 64], they: [18, 63, 64, 22], we: [18, 53, 63, 64], I: [], you: [23, 3] };
  const RELS = { recurrence: 'recurrence', separation: 'separation', order: 'simultaneity / succession', obstruction: 'completion / obstruction', reversal: 'reversal', rhythm: 'rhythm' };

  function splitPhrases(text) {
    const out = [];
    (String(text).replace(/\s+/g, ' ').match(/[^.!?;:]+[.!?;:]*/g) || []).map(x => x.trim()).filter(Boolean).forEach((sent, si) => {     // no lookbehind: older Safari cannot parse it
      if (!sent.trim()) return;
      // a comma, or a conjunction that opens a new clause, starts a phrase
      sent.split(/,\s+|\s+(?=(?:while|but|after|before|until|as soon as|meanwhile)\b)/i).forEach(p => { p = p.trim(); if (p.length > 1) out.push({ text: p, sent: si }); });
    });
    return out;
  }
  // an adverbial fragment ("Every evening", "Across the city") belongs to the clause that follows it
  function mergeFragments(ph) {
    const out = [];
    for (let i = 0; i < ph.length; i++) {
      const p = ph[i], nx = ph[i + 1];
      if (nx && nx.sent === p.sent && !SUBJ.test(p.text) && p.text.split(/\s+/).length <= 4 && !/[.!?;:]$/.test(p.text)) { nx.text = p.text + ', ' + nx.text; continue; }
      out.push(p);
    }
    return out;
  }
  function readPhrase(p) {
    const m = {}; for (const k in LEX) m[k] = LEX[k].test(p.text);
    if (m.succ && /\balready\b/i.test(p.text) && m.simul) m.succ = false;          // "across the city, already leaving": still simultaneous
    const s = p.text.match(SUBJ), pl = p.text.match(PLACE), ns = p.text.match(NOUNSUBJ);
    const noun = ns && GENDER[ns[1].toLowerCase()] ? ns[1].toLowerCase() : null;
    const pro = s ? s[1].toLowerCase() === 'i' ? 'I' : s[1].toLowerCase() : null;
    // a person named by a noun before any pronoun ("My father never came home") is a strand of their own
    const subj = noun && (!s || p.text.toLowerCase().indexOf(noun) < p.text.search(SUBJ)) ? noun : pro;
    return { ...p, marks: m, subj, place: pl ? pl[2].toLowerCase() : null,
             words: p.text.split(/\s+/).length };
  }
  // the text's own structure decides the scenes: a stanza (blank line) or a speaker's turn is a scene; a line is at least one phrase;
  // an unbroken block is divided every few sentences so no scene runs longer than the eye can hold one world
  function parse(text) {
    const raw = [], stanzas = String(text).replace(/\r/g, '').split(/\n\s*\n/).map(x => x.trim()).filter(Boolean);
    let scene = 0, sent = 0, lastSpk = null;
    stanzas.forEach(st => {
      const lines = st.split('\n').map(l => l.trim()).filter(Boolean);
      let inScene = 0;
      lines.forEach((line, li) => {
        let spk = null; const m = line.match(/^([A-Z][\w .'\u2019-]{0,28}):\s+(.+)$/); if (m) { spk = m[1].trim(); line = m[2]; }
        if (spk) lastSpk = spk;
        const ps = mergeFragments(splitPhrases(line));
        ps.forEach(p => { raw.push({ ...p, sent: sent + p.sent, scene, speaker: spk || lastSpk || null, line: li }); inScene++; });
        sent += 100;
        const endsSentence = /[.!?]["'\u201d\u2019)]*$/.test(line);
        if (inScene >= (lines.length > 1 ? 7 : 5) && endsSentence && li < lines.length - 1) { scene++; inScene = 0; }
      });
      if (inScene) scene++;
    });
    // a scene shorter than four phrases cannot hold a world: it joins the next. A conversation stays in its room: speakers are strands, not scenes
    const byScene = {}; raw.forEach(p => (byScene[p.scene] = byScene[p.scene] || []).push(p));
    const ks = Object.keys(byScene).map(Number).sort((a, b) => a - b); let cur = 0, run = 0, prevSpk;
    ks.forEach((k, j) => { const g = byScene[k], spk = g[0].speaker;
      if (j > 0 && run >= 4) { cur++; run = 0; }
      g.forEach(p => p.scene = cur); run += g.length; prevSpk = g[g.length - 1].speaker; });
    const ph = raw.map(readPhrase); let t = 0;
    ph.forEach(p => { if (p.speaker) p.subj = p.speaker; });
    // "A after B": the film tells B first; screen order follows story order (Metz's ordinary sequence), not sentence order
    for (let i = 1; i < ph.length; i++) if (/^after\b/i.test(ph[i].text) && ph[i - 1].sent === ph[i].sent) {
      const a = ph[i - 1]; ph[i - 1] = ph[i]; ph[i] = a; ph[i - 1].reordered = true;
    }
    ph.forEach((p, i) => {
      const d = Math.max(1.8, p.words * .42 + (ph[i + 1] && ph[i + 1].sent !== p.sent ? .6 : .2)); p.t0 = t; p.t1 = t + d;
      t = p.t1; p.i = i;
    });
    if (ph.length) ph[ph.length - 1].last = true;
    return ph;
  }

  // ---------------------------------------------------------------- the library
  function Library(json, emb, events) {
    this.shots = json.shots; this.n = json.n; this.q = emb; this.scale = json.scale; this.events = events;
    this.byPlace = {}; this.bySrc = {}; this.shots.forEach((s, i) => { s.k = i; (this.byPlace[s.place] = this.byPlace[s.place] || []).push(i); (this.bySrc[s.src] = this.bySrc[s.src] || []).push(i); });
  }
  Library.prototype.sims = function (v) {                       // cosine of a text embedding against every shot
    const n = this.n, d = 512, q = this.q, out = new Float32Array(n), sc = this.scale;
    for (let i = 0; i < n; i++) { let a = 0; const o = i * d; for (let j = 0; j < d; j++) a += q[o + j] * v[j]; out[i] = a * sc; }
    return out;
  };
  const evScore = (s, want) => s.ev.reduce((a, [e, z]) => a + (want.includes(e) ? Math.max(0, z) : 0), 0);

  // ---------------------------------------------------------------- the composer
  function Engine(lib, opts = {}) {
    this.lib = lib; this.o = Object.assign({ T: .018, wText: 1, wOp: 1, wHome: .09, gap: .045, close: true, prepared: null, poet: '', criterion: Object.keys(RELS), seed: 0 }, opts);
    this.strands = {}; this.order = []; this.cut = []; this.cur = null; this.used = new Map(); this.srcUsed = new Map(); this.structure = null; this.log = [];
  }
  Engine.prototype.strand = function (key) {
    if (!this.strands[key]) { this.strands[key] = { key, n: this.order.length, anchor: null, last: null, open: true, pending: false, poet: key === this.o.poet }; this.order.push(key); }
    return this.strands[key];
  };
  // before any cut: each scene gets a world, the film that can play the most of its lines (mean of each line's best shot in that film)
  Engine.prototype.plan = function (ph, sims) {
    const L = this.lib, n = L.n, sh = L.shots, o = this.o, groups = {}, used = new Map(); this.scenes = {};
    ph.forEach(p => (groups[p.scene] = groups[p.scene] || []).push(p));
    Object.keys(groups).map(Number).sort((a, b) => a - b).forEach(k => {
      const P = groups[k], poetScene = o.poet && P.some(p => p.subj === o.poet), tot = new Map();
      P.forEach(p => {
        const sim = sims[p.i], m = new Map(), who = p.subj && (WHO[p.subj] || WHO[GENDER[p.subj]]);
        for (let i = 0; i < n; i++) { const s = sh[i]; if (s.kind === 'poet' && !poetScene) continue;
          // a conversation's world is a room where people talk; what they talk about becomes cutaways
          const v = (p.speaker ? .4 * sim[i] + .02 * evScore(s, ROOM) : sim[i] + (who && who.length ? .01 * evScore(s, who) : 0)) - (p.marks.text ? 0 : .02 * evScore(s, CARD));
          const c = m.get(s.src); if (c === undefined || v > c) m.set(s.src, v); }
        m.forEach((v, src) => tot.set(src, (tot.get(src) || 0) + v));
      });
      const size = src => L.bySrc[src].length, fair = src => .012 * Math.min(1, size(src) / 10) - .003 * Math.log2(Math.max(1, size(src) / 12));
      const rank = [...tot].map(([src, v]) => [src, v / P.length + fair(src) - .03 * (used.get(src) || 0) + (poetScene && src.startsWith('cdmx:') ? .02 : 0)])
        .sort((a, b) => b[1] - a[1]);
      const home = rank[0][0]; used.set(home, (used.get(home) || 0) + 1);
      this.scenes[k] = { home, title: (sh[L.bySrc[home][0]] || {}).title, rank: rank.slice(0, 6), phrases: P.map(p => p.i) };
    });
    return this.scenes;
  };
  Engine.prototype.otherHome = function (sim, exclude) {       // a strand that opens inside a scene gets a world of its own
    const L = this.lib, sh = L.shots, best = new Map();
    for (let i = 0; i < L.n; i++) { const s = sh[i]; if (s.kind === 'poet' || exclude.has(s.src)) continue; const c = best.get(s.src); if (c === undefined || sim[i] > c) best.set(s.src, sim[i]); }
    let top = null, v = -9; best.forEach((x, src) => { const y = x + .012 * Math.min(1, L.bySrc[src].length / 10); if (y > v) { v = y; top = src; } }); return top;
  };
  // score every shot for one operation in one strand, given the words and the film so far
  Engine.prototype.distribution = function (op, S, sim, p, extra = {}) {
    const L = this.lib, sh = L.shots, n = L.n, sc = new Float32Array(n), o = this.o;
    const others = Object.values(this.strands).filter(x => x !== S && x.anchor);
    const want = extra.want || [];
    let best = -1;
    for (let i = 0; i < n; i++) {
      const s = sh[i]; let v = o.wText * sim[i]; best = Math.max(best, sim[i]);
      let f = 0;
      if (s.kind === 'poet') f += S.poet ? .07 : -.2;                       // the poet's own takes belong to his strand only
      else if (S.poet && o.poetOnly) f -= .05;
      if (want.length) f += (op === 'COMPLETE' || extra.act ? .045 : .02) * evScore(s, want);
      const who = WHO[S.key] || WHO[GENDER[S.key]];
      { const g = GENDER[S.key] || S.key; if (who && who.length && op !== 'ABSENCE' && op !== 'INSERT') f += (op === 'COMPLETE' ? .01 : .025) * evScore(s, who) - (g === 'he' ? .03 * evScore(s, [61, 41, 64]) : g === 'she' ? .03 * evScore(s, [60, 40, 39, 63]) : 0); }
      if (extra.avoid) f -= .025 * evScore(s, extra.avoid);
      const a = S.anchor, l = S.last;
      if (op === 'CONTINUE' || op === 'SUSPEND' || op === 'COMPLETE' || op === 'ALTERNATE') {
        if (l && s.src === l.src) f += (s.st != null && l.st != null && s.st > l.st && s.st - l.st < 240) ? .06 : .025;
        if (a && s.place === a.place) f += op === 'ALTERNATE' ? .06 : .02;
        if (op === 'ALTERNATE' && a && s.src === a.src) f += .08;       // back to the same strand: its film, its place
      }
      if (op === 'REPEAT' || op === 'RETURN' || op === 'ABSENCE') {
        if (a && s.place === a.place) f += .08; if (a && s.src === a.src) f += .03;
        if (op === 'REPEAT' && a && s.k === a.k) f += (this.used.get(s.k) || 0) < 2 ? .06 : -.1;   // the same composition once more, not a loop
        if (op === 'ABSENCE' && a && s.src === a.src) f += .06;         // emptied: the same film's own empty rooms first
      }
      if (op === 'OPEN') for (const x of others) { if (s.place === x.anchor.place) f -= .08; if (s.src === x.anchor.src) f -= .06; }   // separation
      if (op === 'INSERT' && l && s.year && l.year && Math.abs(s.year - l.year) > 15) f += .04;
      if (op !== 'REPEAT') { const u = this.used.get(s.k) || 0; f -= .12 * u; }
      f -= .004 * (this.srcUsed.get(s.src) || 0);
      if (o.prepared && p.pool && p.pool.has(s.id)) f += .05;
      if (!p.marks.text) f -= .03 * evScore(s, CARD);
      if (S.home && s.src === S.home && op !== 'CUTAWAY' && op !== 'INSERT' && op !== 'REPEAT' && op !== 'RETURN') f += op === 'OPEN' && !extra.act ? o.wHome * 1.6 : extra.act || op === 'COMPLETE' ? o.wHome * .5 : o.wHome;   // the scene's world (an action on screen outranks it)
      if (extra.close && a && s.src === a.src) f += .2;
      sc[i] = v + o.wOp * f;
    }
    return { sc, coverage: best };
  };
  Engine.prototype.choose = function (dist, lock) {
    const { sc } = dist, n = sc.length, T = this.o.T;
    // the distribution over the top 400 (the tail carries ~no mass at this temperature)
    const idx = Array.from({ length: n }, (_, i) => i).sort((a, b) => sc[b] - sc[a]).slice(0, 400);
    const mx = sc[idx[0]]; let Z = 0; const w = idx.map(i => { const e = Math.exp((sc[i] - mx) / T); Z += e; return e; });
    const P = w.map(e => e / Z); let H = 0; P.forEach(p => { if (p > 0) H -= p * Math.log2(p); });
    let pick = 0;
    if (lock != null) { pick = idx.indexOf(lock); if (pick < 0) { idx.push(lock); P.push(Math.exp((sc[lock] - mx) / T) / Z); pick = idx.length - 1; } }
    else if (this.o.seed) { let r = rand(this.o.seed + this.cut.length), c = 0; for (pick = 0; pick < P.length - 1; pick++) { c += P[pick]; if (c >= r) break; } }
    return { k: idx[pick], p: P[pick], H, perp: Math.pow(2, H), surprisal: -Math.log2(Math.max(P[pick], 1e-12)), alts: idx.slice(0, 24).map((k, j) => ({ k, p: P[j] })) };
  };
  Engine.prototype.emit = function (op, S, p, sim, dur, extra = {}) {
    if (op === 'ALTERNATE' && S.sim) sim = S.sim; else S.sim = sim;       // cutting back: the strand's own words, not the other strand's
    const d = this.distribution(op, S, sim, p, extra), c = this.choose(d, extra.lock != null ? extra.lock : (p.locks && p.locks[this.cut.length]));
    const s = this.lib.shots[c.k], t0 = this.cut.length ? this.cut[this.cut.length - 1].t1 : (p.t0 || 0);
    const off = op === 'REPEAT' && S.anchor && s.k === S.anchor.k ? 0 : (S.last && s.k === S.last.k ? S.lastOut : 0);
    const shot = { i: this.cut.length, op, strand: S.key, phrase: p.i, k: c.k, id: s.id, src: s.src, st: s.st, in: (s.in || 0) + off, t0, t1: t0 + dur,
                   H: c.H, perp: c.perp, surprisal: c.surprisal, p: c.p, coverage: d.coverage, alts: c.alts, why: extra.why || OPS[op], home: S.home || null, scene: p.scene };
    this.cut.push(shot); this.used.set(s.k, (this.used.get(s.k) || 0) + 1); this.srcUsed.set(s.src, (this.srcUsed.get(s.src) || 0) + 1);
    if (op !== 'CUTAWAY') { if (!S.anchor) S.anchor = s; S.last = s; S.lastOut = shot.in - (s.in || 0) + dur; }
    this.cur = S.key;
    return shot;
  };
  Engine.prototype.hold = function (p, dur, why) {                    // the shot already on screen stays; no cut
    const last = this.cut[this.cut.length - 1]; if (!last) return null;
    last.t1 += dur; last.held = (last.held || []).concat(p.i); last.why += ' · held through: ' + why;
    const S = this.strands[last.strand]; S.lastOut += dur; return last;
  };
  // one phrase in, the next edits out: this is the state machine
  Engine.prototype.feed = function (p, sim) {
    const m = p.marks, crit = new Set(this.o.criterion), prevKey = this.cur;
    let key = p.subj || prevKey || this.o.firstSubj || 'A';
    const isNew = !this.strands[key];
    const S = this.strand(key), prev = prevKey && this.strands[prevKey];
    let sceneNew = false;
    if (this.scenes && p.scene !== this.sceneK) {                     // a new scene: every strand needs a world here
      sceneNew = this.cut.length > 0; this.sceneK = p.scene; Object.values(this.strands).forEach(x => { x.home = null; });
    }
    if (this.scenes && !S.home) {
      const taken = new Set(Object.values(this.strands).filter(x => x.home).map(x => x.home));
      S.home = !taken.size || p.speaker ? this.scenes[p.scene].home : this.otherHome(sim, taken);     // people in one meeting share one room
    }
    if (prev && prev !== S) {
      if (m.succ && !m.simul) { this.structure = 'SEQ'; prev.open = false; }             // succession: the earlier strand closes
      else if (m.simul || isNew) this.structure = this.structure || 'ALT';
    }
    const ops = [], why = []; let dur = p.t1 - p.t0;
    const action = m.depart ? 'depart' : m.arrive ? 'arrive' : m.wait ? 'wait' : null;
    if (m.still && this.cut.length && !isNew) {
      ops.push(['HOLD']); why.push('persistence: the frame does not change');
    } else if (m.rev && crit.has('reversal') && this.cut.length && !(m.absent && !isNew) && !isNew && !m.recur && !m.depart && !m.arrive && !m.ret) {
      ops.push(['HOLD']); why.push('"' + (p.text.match(LEX.rev) || [''])[0].trim() + '": the image stays while the sentence turns it');
    } else if (isNew || sceneNew) {
      const act = action && { act: action !== 'wait', want: EVW[action] || [], avoid: m.neg ? EVW.depart.concat(EVW.arrive) : null };
      ops.push(['OPEN', p.speaker && !sceneNew ? { want: ROOM } : action && dur <= 3.4 && !m.neg ? act : { want: EVW.establish }]);   // a new voice in the room is seen in the room        // short: the action itself establishes the strand
      if (action && dur > 3.4) ops.push([m.neg ? 'SUSPEND' : action === 'wait' ? 'CONTINUE' : 'COMPLETE', { want: EVW[action] || [], avoid: m.neg ? EVW.depart.concat(EVW.arrive) : null }]);
    } else if (m.absent && S.anchor) ops.push(['ABSENCE', { want: EVW.empty, avoid: [0, 1, 18, 19] }]);
    else if (m.recur) ops.push(['REPEAT', { want: EVW.establish }]);
    else if (m.ret) ops.push(['RETURN', { want: EVW.arrive.concat(EVW.establish) }]);
    else if (m.mem) ops.push(['INSERT', {}]);
    else if (m.neg && action) ops.push(['SUSPEND', { want: action === 'depart' ? EVW.door.concat(EVW.wait) : EVW.wait, avoid: EVW.depart.concat(EVW.arrive) }]);
    else if (p.speaker && !action) ops.push(['CONTINUE', { want: ROOM }]);
    else if (action === 'wait') ops.push(['CONTINUE', { want: EVW.wait }]);
    else if (action) ops.push(['COMPLETE', { want: EVW[action] }]);
    else ops.push(['CONTINUE', {}]);
    if (m.recur && isNew && crit.has('recurrence')) ops.push(['REPEAT', { want: EVW.establish }]);     // "every evening": the place comes back within the phrase
    if (m.neg && action) S.pending = true; if (action === 'wait') S.pending = true; if (m.depart && !m.neg) S.pending = false;
    // the world has nothing for these words: leave it for one shot rather than force it
    if (S.home && ops.length === 1 && ops[0][0] === 'CONTINUE') {          // an action (COMPLETE) is never traded for a cutaway
      const hs = this.lib.bySrc[S.home] || []; let bh = -1, ba = -1; for (const i of hs) bh = Math.max(bh, sim[i]); for (let i = 0; i < sim.length; i++) ba = Math.max(ba, sim[i]);
      if (ba - bh > this.o.gap) { ops[0] = ['CUTAWAY', ops[0][1]]; why[0] = 'cut away: ' + ((this.lib.shots[hs[0]] || {}).title || 'this world') + ' has nothing for these words (' + bh.toFixed(2) + ' against ' + ba.toFixed(2) + ' elsewhere)'; }
    }
    // the last line: the film closes where it opened
    const first = this.strands[this.order[0]];
    const closing = p.last && this.o.close && this.scenes && Object.keys(this.scenes).length > 1 && first && first.anchor && !ops.some(o => o[0] === 'HOLD');
    const out = [];
    const willAlt = this.structure === 'ALT' && crit.has('order') && prev && prev !== S && prev.open && prev.pending && m.simul;
    if (!p.timed) {                  // typed language has no voice to keep time: give a structure the screen time it needs to be seen
      const base = this.cut.length ? this.cut[this.cut.length - 1].t1 : (p.t0 || 0), k = ops.filter(o => o[0] !== 'HOLD').length;
      dur = Math.max(dur * 1.3, 2.6, k * 2.4 + (willAlt ? 2.4 : 0)); p.t0 = base; p.t1 = base + dur;
    }
    if (closing && !p.timed) { dur += 2.4; p.t1 += 2.4; }
    const n = (ops.filter(o => o[0] !== 'HOLD').length || 1) + (closing ? 1 : 0), each = dur / n;
    ops.forEach(([op, ex]) => {
      if (op === 'HOLD') { const h = this.hold(p, dur, 'the sentence turns'); if (h) out.push(h); else out.push(this.emit('CONTINUE', S, p, sim, dur)); return; }
      out.push(this.emit(op, S, p, sim, op === 'SUSPEND' ? each : each, { ...ex, why: why[0] }));
    });
    if (closing) out.push(this.emit('RETURN', first, p, first.sim || sim, each, { want: EVW.establish, close: true, why: 'the film closes where it opened' }));
    // simultaneity must be seen: after the other strand speaks, cut back to the strand left waiting
    if (willAlt) {
      const back = Math.min(2.4, dur * .4); out[out.length - 1].t1 -= back;
      out.push(this.emit('ALTERNATE', prev, p, sim, back, { want: EVW.wait, why: 'meanwhile: back to ' + prev.key + ', still unresolved' }));
      this.cur = S.key;
    }
    this.log.push({ phrase: p.i, strand: S.key, structure: this.structure, ops: out.map(s => s.op) });
    return out;
  };
  function rand(s) { s = Math.sin(s * 9301 + 49297) * 233280; return s - Math.floor(s); }

  // ---------------------------------------------------------------- fidelity: what had to survive, and did it
  function fidelity(eng, ph) {
    const cut = eng.cut, crit = new Set(eng.o.criterion), L = eng.lib.shots, R = [];
    const of = i => cut.filter(s => s.phrase === i || (s.held || []).includes(i));
    const strands = eng.order;
    if (crit.has('recurrence')) ph.filter(p => p.marks.recur).forEach(p => {
      const sh = of(p.i), places = sh.map(s => L[s.k].place), rep = places.some((x, j) => places.indexOf(x) !== j) || sh.some((s, j) => sh.findIndex(t => t.k === s.k) !== j);
      const earlier = cut.filter(s => s.strand === (sh[0] && sh[0].strand) && s.phrase < p.i && !sh.includes(s)).some(s => places.includes(L[s.k].place));
      R.push({ rel: 'recurrence', at: p.text, ok: rep || earlier, why: rep || earlier ? 'the place comes back within the phrase' : 'no place repeats: it plays as a single occurrence' });
    });
    const speakers = new Set(ph.filter(p => p.speaker).map(p => p.speaker));
    if (crit.has('separation') && strands.filter(k => !speakers.has(k)).length > 1) {                 // people in one conversation share a room by design
      const a = {}; cut.filter(s => !speakers.has(s.strand)).forEach(s => { (a[s.strand] = a[s.strand] || new Set()).add(s.src); });
      const ks = Object.keys(a); let shared = 0; for (let i = 0; i < ks.length; i++) for (let j = i + 1; j < ks.length; j++) a[ks[i]].forEach(x => { if (a[ks[j]].has(x)) shared++; });
      R.push({ rel: 'separation', at: strands.join(' / '), ok: !shared, why: shared ? shared + ' film(s) shared between strands: they may read as one place' : 'each strand has its own films' });
    }
    if (crit.has('order')) ph.filter(p => p.marks.simul || p.marks.succ).forEach(p => {
      const mine = of(p.i), j = cut.indexOf(mine[0]); if (j < 1) return;
      const X = mine[0].strand, Y = cut.slice(0, j).reverse().map(s => s.strand).find(k => k !== X);
      const lastBefore = cut[j - 1].strand; if (!Y || lastBefore === X) return;       // one strand moving on: there is no second strand to order against
      const back = cut.slice(j + 1).some(s => s.strand === Y && s.scene === mine[0].scene);
      if (p.marks.simul && !p.marks.succ) R.push({ rel: 'simultaneity', at: p.text, ok: back, why: back ? 'the strands alternate: A … B … A' : 'no cut back: it reads as one after the other' });
      else R.push({ rel: 'succession', at: p.text, ok: !back, why: !back ? 'the earlier strand does not return' : 'the strands alternate: it reads as simultaneous' });
    });
    if (crit.has('obstruction')) ph.filter(p => p.marks.neg && (p.marks.depart || p.marks.arrive)).forEach(p => {
      const bad = of(p.i).filter(s => evScore(L[s.k], EVW.depart.concat(EVW.arrive)) > 1.2);
      R.push({ rel: 'obstruction', at: p.text, ok: !bad.length, why: bad.length ? 'a shot completes the action the sentence denies' : 'the action is held, never completed' });
    });
    if (crit.has('obstruction')) ph.filter(p => !p.marks.neg && p.marks.depart).forEach(p => {
      const good = of(p.i).some(s => evScore(L[s.k], EVW.depart) > .8);
      R.push({ rel: 'completion', at: p.text, ok: good, why: good ? 'a departure is on screen' : 'nothing on screen leaves' });
    });
    if (crit.has('reversal')) ph.filter(p => p.marks.rev).forEach(p => {
      const sh = of(p.i), prevShot = cut.filter(s => s.phrase < p.i && !(s.held || []).includes(p.i)).pop();
      const held = sh.some(s => (s.held || []).includes(p.i)), emptied = sh.some(s => s.op === 'ABSENCE');
      const reseen = !held && prevShot && sh.some(s => L[s.k].place === L[prevShot.k].place || s.src === prevShot.src || (eng.strands[s.strand].anchor && L[s.k].place === eng.strands[s.strand].anchor.place));
      R.push({ rel: 'reversal', at: p.text, ok: held || emptied || reseen, why: held ? 'the same shot carries both claims' : emptied ? 'the same place, emptied' : reseen ? 'the same place seen again, now otherwise' : 'a new image illustrates the second claim; the turn is lost' });
    });
    if (crit.has('rhythm')) {
      const heldOver = i => cut.some(s => (s.held || []).includes(i + 1));
      const b = ph.map(p => p.t1), cuts = cut.map(s => s.t1), near = b.filter((t, i) => heldOver(i) || cuts.some(c => Math.abs(c - t) < .35)).length;
      R.push({ rel: 'rhythm', at: 'phrase ends', ok: near / b.length > .6, why: Math.round(100 * near / b.length) + '% of phrase ends fall on a cut or a held join' });
    }
    const req = R.length, got = R.filter(r => r.ok).length;
    return { rows: R, required: req, realized: got, D: req ? 1 - got / req : 0 };
  }
  // what kind of film came out: worlds, continuity inside scenes, where the archive was thin
  function measure(eng, ph) {
    const cut = eng.cut; let same = 0, pairs = 0;
    for (let i = 1; i < cut.length; i++) { const a = cut[i - 1], b = cut[i]; if (a.scene !== b.scene || a.op === 'CUTAWAY' || b.op === 'CUTAWAY') continue; pairs++; if (a.src === b.src) same++; }
    const firstShot = i => cut.find(s => s.phrase === i || (s.held || []).includes(i));
    const cov = ph.map(p => (firstShot(p.i) || { coverage: 0 }).coverage);
    const ids = cut.map(s => s.k), meant = cut.filter(s => s.op === 'REPEAT' || s.op === 'RETURN').length;
    return { scenes: Object.keys(eng.scenes || {}).length || 1, shots: cut.length, phrases: ph.length,
      worlds: new Set(Object.values(eng.scenes || {}).map(s => s.home)).size, films: new Set(cut.map(s => s.src)).size,
      continuity: pairs ? same / pairs : 1, inWorld: cut.length ? cut.filter(s => s.home && s.src === s.home).length / cut.length : 0,
      cutaways: cut.filter(s => s.op === 'CUTAWAY').length, meanCoverage: cov.reduce((a, b) => a + b, 0) / (cov.length || 1),
      thin: ph.filter((p, i) => cov[i] < THIN).map(p => p.text), repeats: Math.max(0, ids.length - new Set(ids).size - meant) };
  }
  // search: which films can play these words, as a sequence, not a single clip
  function searchFilms(lib, sims, k = 8) {
    const sh = lib.shots, tot = new Map(), bestShot = new Map();
    sims.forEach((sim, q) => { const m = new Map(); for (let i = 0; i < lib.n; i++) { const s = sh[i]; const c = m.get(s.src); if (!c || sim[i] > c[0]) m.set(s.src, [sim[i], i]); }
      m.forEach(([v, i], src) => { tot.set(src, (tot.get(src) || 0) + v); (bestShot.get(src) || bestShot.set(src, []).get(src)).push(i); }); });
    return [...tot].map(([src, v]) => ({ src, score: v / sims.length + .012 * Math.min(1, lib.bySrc[src].length / 10), shots: [...new Set(bestShot.get(src))].sort((a, b) => (sh[a].st || 0) - (sh[b].st || 0)) }))
      .sort((a, b) => b.score - a.score).slice(0, k).map(r => ({ ...r, title: sh[r.shots[0]].title, year: sh[r.shots[0]].year }));
  }
  // plan the scenes, then feed every phrase (with any shots a person fixed: locks = {'phrase:j': shotIndex})
  function run(lib, ph, sims, opts = {}) {
    const f0 = ph.find(p => p.subj); const e = new Engine(lib, { firstSubj: f0 && f0.subj, ...opts }); e.plan(ph, sims); const locks = opts.locks || {};
    ph.forEach((p, i) => { const n0 = e.cut.length; p.locks = {}; Object.entries(locks).forEach(([key, k]) => { const [a, j] = key.split(':').map(Number); if (a === i) p.locks[n0 + j] = k; }); e.feed(p, sims[i]); });
    return { eng: e, cut: e.cut, fid: fidelity(e, ph), m: measure(e, ph) };
  }
  function compose(lib, ph, sims, opts) { return run(lib, ph, sims, opts); }
  const api = { OPS, LEX, EVW, RELS, parse, Library, Engine, compose, run, fidelity, measure, searchFilms };
  root.Shannon = api; if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
