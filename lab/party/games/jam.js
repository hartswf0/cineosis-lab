/* THE JAM: the archive as a playground, and every move changes what can happen next.
   A card asks an open question (WHO IS THE HERO?). Every phone forages the archive and casts a shot: talk to search, point to pick,
   go farther to wander. Then each shot is PASSED: the next phone gives it a sound (the archive's own sounds, music, people
   speaking, people saying what you said); the next one SPOILS it with one cut (hold, repeat, reverse, enter early, cut too
   soon, silence, interrupt). Each thing ends with three authors, and their fingerprints stay on it. The round plays; tomatoes and
   roses fly; everyone keeps one piece. Then the world remembers:
     the card's MOVE casts the room's favourite (the hero now stands at the centre of the next deals until someone recasts it),
     a sound that survived on an image becomes a MOTIF (that sound is offered whenever the image's like returns, and summons it),
     CUT TOO SOON leaves a DEBT (something we didn't see, which a later card can reveal),
     a KEEP is spendable (it comes back gold in its keeper's hand), the cuts people use become the room's STYLE,
     and every pick pulls the search toward where the room has been going, fading over a few rounds unless renewed.
   The film is every round in order; it plays on the stand, goes to The Cut, and leaves as a link.
   Reuses: markov/shared.js (16,153 shots + CLIP vectors), party/lexicon (words to pictures), tools/sound-kinds.json (which clips
   have voices, music, noise), pictures/rushes.json (spoken lines, music), odyssey/transcripts.json (who said which word), party/ears.js. */
(function () {
  const { esc, rnd, pick, shuffle, mini, KINDS } = Party;
  const col = av => (KINDS[av] || KINDS[0]).c, HOUSE = '#8b8a86';
  const STOP = new Set('a an the and or of to in on at by for with from into onto over under is are was were be been it its this that these those as his her their our your my he she they we you i me him them us one two not no but so if then than there here what which who whom whose when where while out up down off about after before again all any both each few more most other some such only own same very can will just do does did has have had am also yet too nor like said say get got go going want know think yeah okay well really thing things find something make give'.split(' '));
  const stem = w => { for (const x of ['ing', 'ed', 'es', 's']) if (w.length > x.length + 3 && w.endsWith(x)) return w.slice(0, -x.length); return w; };
  const words = t => ((t || '').toLowerCase().match(/[a-z']+/g) || []).map(w => w.replace(/'/g, '')).filter(w => w.length > 2 && !STOP.has(w));
  const thumbOf = u => u ? u.replace('/clips/', '/thumbnails/').replace(/\.mp4.*$/, '.jpg') : '';
  // the cards: each asks for a way of seeing, and each is a MOVE the world obeys afterwards
  const CARDS = [
    { id: 'hero', q: 'Who is the hero?', move: 'CAST', role: 'hero', w: 'person face man woman child', snd: 'right' },
    { id: 'where', q: 'Where are we?', move: 'PLACE', role: 'place', w: 'landscape street room city field house', snd: 'right' },
    { id: 'stranger', q: 'Who doesn’t belong here?', move: 'INTRUDE', role: 'stranger', anti: true, snd: 'wrong' },
    { id: 'guilty', q: 'Find something that looks guilty.', move: 'SUSPECT', role: 'suspect', w: 'hand hide night window shadow', snd: 'right' },
    { id: 'watch', q: 'Who is watching the hero?', move: 'WATCH', role: 'watcher', w: 'face eye look window', near: 'hero', need: 'hero', snd: 'right' },
    { id: 'small', q: 'Make something small feel enormous.', move: 'SCALE', w: 'close hand insect object small', snd: 'wrong' },
    { id: 'lie', q: 'Make this shot lie.', move: 'MISDIRECT', snd: 'wrong' },
    { id: 'back', q: 'Bring back something we forgot.', move: 'RETURN', pool: 'reel', need: 'reel', snd: 'right' },
    { id: 'unseen', q: 'What didn’t we see?', move: 'REVEAL', pool: 'debt', need: 'debt', snd: 'right' },
    { id: 'meet', q: 'Make two strangers remember each other.', move: 'MEET', near: 'two', need: 'two', snd: 'right' },
    { id: 'end', q: 'Find the ending in the middle.', move: 'END', role: 'ending', w: 'door leave road sea night sunset', need: 'late', snd: 'right' }];
  const OPS = ['hold', 'repeat', 'reverse', 'early', 'soon', 'silence', 'interrupt'];
  const OPN = { hold: 'HOLD', repeat: 'REPEAT', reverse: 'REVERSE', early: 'ENTER EARLY', soon: 'CUT TOO SOON', silence: 'SILENCE', interrupt: 'INTERRUPT' };
  const FAM = { voice: '#ff5a1f', music: '#1d6bff', field: '#1f9d57' };
  const I = {
    eye: '<svg viewBox="0 0 40 40"><path d="M3 20 Q20 4 37 20 Q20 36 3 20Z" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="20" cy="20" r="6" fill="currentColor"/></svg>',
    ear: '<svg viewBox="0 0 40 40"><path d="M13 16 Q13 5 22 5 Q31 5 31 15 Q31 21 26 25 Q23 28 23 32 Q23 37 18 37 Q14 37 13 33" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/><path d="M19 17 Q19 11 23 11 Q26 11 26 15" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    cut: '<svg viewBox="0 0 40 40"><circle cx="11" cy="30" r="5" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="29" cy="30" r="5" fill="none" stroke="currentColor" stroke-width="3"/><path d="M14 26 L30 5 M26 26 L10 5" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    keep: '<svg viewBox="0 0 40 40"><path d="M20 35 L6 21 Q1 15 6 9 Q12 4 20 12 Q28 4 34 9 Q39 15 34 21Z" fill="currentColor"/></svg>',
    play: '<svg viewBox="0 0 40 40"><path d="M12 7 L33 20 L12 33Z" fill="currentColor"/></svg>',
    mic: '<svg viewBox="0 0 40 40"><rect x="14" y="4" width="12" height="20" rx="6" fill="currentColor"/><path d="M9 18 Q9 30 20 30 Q31 30 31 18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M20 30 V36 M13 36 H27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    far: '<svg viewBox="0 0 40 40"><path d="M6 20 H30 M22 11 L31 20 L22 29" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M6 12 V28" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity=".5"/></svg>',
    note: '<svg viewBox="0 0 40 40"><path d="M15 29 V8 L33 4 V25" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="11" cy="29" r="5" fill="currentColor"/><circle cx="29" cy="25" r="5" fill="currentColor"/></svg>',
    mouth: '<svg viewBox="0 0 40 40"><path d="M4 20 Q20 6 36 20 Q20 34 4 20Z" fill="currentColor"/><path d="M8 20 Q20 25 32 20" stroke="#fff" stroke-width="2.5" fill="none"/></svg>',
    wave: '<svg viewBox="0 0 40 40"><path d="M3 20 Q8 8 13 20 T23 20 T33 20 T40 20" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/></svg>',
    hold: '<svg viewBox="0 0 40 40"><rect x="10" y="8" width="7" height="24" rx="2" fill="currentColor"/><rect x="23" y="8" width="7" height="24" rx="2" fill="currentColor"/></svg>',
    repeat: '<svg viewBox="0 0 40 40"><path d="M8 18 Q8 9 18 9 H30 L26 5 M30 9 L26 13 M32 22 Q32 31 22 31 H10 L14 35 M10 31 L14 27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    reverse: '<svg viewBox="0 0 40 40"><path d="M30 8 L12 20 L30 32Z" fill="currentColor"/><path d="M10 8 V32" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/></svg>',
    early: '<svg viewBox="0 0 40 40"><path d="M3 20 Q6 12 9 20 T15 20" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><rect x="19" y="10" width="18" height="20" rx="2" fill="currentColor"/></svg>',
    soon: '<svg viewBox="0 0 40 40"><rect x="4" y="10" width="14" height="20" rx="2" fill="currentColor"/><path d="M22 6 V34" stroke="currentColor" stroke-width="3.5" stroke-dasharray="4 3"/><rect x="26" y="10" width="10" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="2" opacity=".4"/></svg>',
    silence: '<svg viewBox="0 0 40 40"><path d="M6 15 H12 L20 8 V32 L12 25 H6Z" fill="currentColor"/><path d="M26 14 L36 26 M36 14 L26 26" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/></svg>',
    interrupt: '<svg viewBox="0 0 40 40"><rect x="3" y="10" width="13" height="20" rx="2" fill="currentColor"/><rect x="24" y="10" width="13" height="20" rx="2" fill="currentColor"/><rect x="16" y="6" width="8" height="28" rx="1" fill="#c8553d"/></svg>'
  };
  const PASS = { find: 'eye', sound: 'ear', spoil: 'cut', keep: 'keep', play: 'play' };
  const famIcon = f => f === 'music' ? I.note : f === 'voice' ? I.mouth : I.wave;

  // ---- an object on any screen: its picture, a sound under it, a cut through it; time-shaped by the cut
  // run(o, el, hooks): plays one object into {V: video, A: audio, X: flash img, B: black div}; returns stop()
  function run(o, el, h = {}) {
    let dead = false; const tm = [], later = (f, s) => tm.push(setTimeout(() => { if (!dead) f(); }, s * 1000));
    const { V, A, X, B } = el, S = o.snd, op = o.op && o.op.o, base = 4.2;
    const vin = o.vin || 0, sin = S ? S.t0 || 0 : 0, slen = S ? Math.max(.6, Math.min(6, (S.t1 || sin + base) - sin)) : 0;
    const vgo = (t, play = true) => { try { V.currentTime = vin + t; } catch (e) { } if (play) V.play().catch(() => { }); };
    const ago = t => { if (!S) return; try { A.currentTime = sin + t; } catch (e) { } A.play().catch(() => { }); };
    if (V.dataset.u !== o.v) { V.dataset.u = o.v; V.src = o.v; } V.muted = !!S; V.volume = .6; V.playbackRate = 1;
    if (S) { if (A.dataset.u !== S.u) { A.dataset.u = S.u; A.src = S.u; } A.volume = .9; }
    X.style.opacity = 0; B.style.opacity = 0; let T = base;
    const start = () => { V.style.opacity = 1;
      if (op === 'hold') { vgo(0); ago(0); later(() => V.pause(), 1.1); }
      else if (op === 'repeat') { [0, 1.15, 2.3].forEach(t => later(() => { vgo(0); ago(0); }, t)); T = 3.5; }
      else if (op === 'reverse') { vgo(3, false); V.pause(); ago(0); let x = 3; const iv = setInterval(() => { if (dead || x <= 0) return clearInterval(iv); x -= .05; try { V.currentTime = vin + Math.max(0, x); } catch (e) { } }, 50); tm.push(iv); }
      else if (op === 'soon') { vgo(0); ago(0); T = 1.3; }
      else if (op === 'silence') { vgo(0); ago(0); later(() => A.pause(), 1.6); }
      else if (op === 'interrupt') { vgo(0); ago(0); later(() => { X.src = o.flash || ''; X.style.opacity = 1; A.pause(); V.pause(); }, 1.8); later(() => { X.style.opacity = 0; vgo(2.4); ago(2.4); }, 2.4); T = base + .6; }
      else { vgo(0); ago(0); }
      if (S && !op) later(() => { }, 0);
      later(() => { stop(); h.done && h.done(); }, T); };
    if (op === 'early') { B.style.opacity = 1; V.style.opacity = 0; ago(0); later(() => { B.style.opacity = 0; start(); }, 1.4); } else start();
    function stop() { dead = true; tm.forEach(t => { clearTimeout(t); clearInterval(t); }); try { A.pause(); } catch (e) { } try { V.pause(); } catch (e) { } X.style.opacity = 0; B.style.opacity = 0; }
    return stop;
  }

  function host(H) {
    const $ = s => document.querySelector(s), P = H.P, ARC = window.SH;
    H.show(null); H.slate(''); H.cap('');
    let root$ = $('#jamv'); if (!root$) { root$ = document.createElement('div'); root$.id = 'jamv'; $('#vids').after(root$); } root$.hidden = false;
    root$.innerHTML = `<div class="jcard" id="jCard"></div><div class="jtiles" id="jTiles"></div><div class="jsolo" id="jSolo" hidden><video playsinline preload="auto"></video><div class="jb"></div><img class="jx" alt=""><div class="jauth" id="jAuth"></div></div>`;
    const solo = { V: root$.querySelector('.jsolo video'), A: H.AP[0], X: root$.querySelector('.jsolo .jx'), B: root$.querySelector('.jsolo .jb') };
    const J = { ready: false, why: 'opening the archive', round: 0, phase: 'find', card: null, order: [], objs: [], reel: [], playing: null, at: -1, said: {}, heard: {} };
    const ST = { att: [], cast: {}, motifs: [], debts: [], keeps: [], style: {}, log: [], seen: new Set() };
    const hands = {}; let LIB = null, X = null, XV = null, XI = null, R = null, SK = null, SND = [], TR = null, TW = null, nid = 1, stopPlay = null, spot = null, spotQ = [];
    const players = () => H.players.filter(p => !p.house);
    window.__jam = { J, ST, hands };
    Promise.all([ARC.load({ light: true }), fetch('party/lexicon.json').then(r => r.json()), fetch('party/lexicon.bin').then(r => r.arrayBuffer()), fetch('pictures/rushes.json').then(r => r.json()), fetch('tools/sound-kinds.json').then(r => r.json())])
      .then(([d, xj, xb, rj, sk]) => { LIB = d.LIB; X = xj; XV = new Int8Array(xb); XI = new Map(X.words.map((w, i) => [w, i])); R = rj; SK = sk.clips;
        const byId = new Map(LIB.shots.map((s, i) => [s.id, i])); for (const id in SK) { const k = byId.get(id), kind = SK[id][0]; if (k != null && /mixed|speech|music|noise/.test(kind)) SND.push(k); }
        J.ready = true; J.why = ''; newRound(); })
      .catch(e => { J.why = 'the archive did not load: ' + e.message; draw(); });
    fetch('odyssey/transcripts.json').then(r => r.json()).then(t => TR = t).catch(() => { });
    // ---- vectors: shots, words, and the room's steering
    const norm = v => { let n = 0; for (let j = 0; j < v.length; j++) n += v[j] * v[j]; n = Math.sqrt(n) || 1; for (let j = 0; j < v.length; j++) v[j] /= n; return v; };
    const vecK = k => { const d = 512, o = new Float32Array(d), r = k * d; for (let j = 0; j < d; j++) o[j] = LIB.q[r + j]; return norm(o); };
    const vecW = t => { const ws = words(t).map(stem).filter(w => XI.has(w)); if (!ws.length) return null; const v = new Float32Array(512); ws.forEach(w => { const i = XI.get(w), f = X.idf[i]; for (let j = 0; j < 512; j++) v[j] += XV[i * 512 + j] * f; }); return norm(v); };
    const add = (o, v, w) => { if (v) for (let j = 0; j < 512; j++) o[j] += v[j] * w; return o; };
    const dotK = (v, k) => { let a = 0; const r = k * 512; for (let j = 0; j < 512; j++) a += v[j] * LIB.q[r + j]; return a; };
    const steer = () => { const v = new Float32Array(512); ST.att.forEach(a => add(v, a.v, a.w)); return v; };
    const empty = v => !v || !v.some(x => x);
    const isArc = k => LIB.shots[k].kind !== 'presence';
    const shot = k => LIB.shots[k], nameOf = id => (P(id) || {}).name || 'the archive', colOf = id => P(id) ? col(P(id).av) : HOUSE;
    const label = k => { const s = shot(k); return s ? (s.title || '').replace(/\s*\(.*$/, '').slice(0, 34) + (s.year ? ' · ' + s.year : '') : ''; };
    const softPick = (arr, n, T = 12) => { const out = [], pool = arr.slice(); while (out.length < n && pool.length) { let r = rnd() * pool.reduce((a, _, i) => a + Math.exp(-i / T), 0), i = 0; for (; i < pool.length; i++) { r -= Math.exp(-i / T); if (r <= 0) break; } out.push(pool.splice(Math.min(i, pool.length - 1), 1)[0]); } return out; };
    // ---- the round: a card, then passes
    function chooseCard() { const used = J.card ? J.card.id : '', inReel = J.reel.length, can = c => !c.need || (c.need === 'hero' && ST.cast.hero) || (c.need === 'reel' && inReel >= 6) || (c.need === 'debt' && ST.debts.length) || (c.need === 'two' && ST.att.length >= 2) || (c.need === 'late' && J.round >= 4);
      if (J.round === 1) return CARDS[0]; const pool = CARDS.filter(c => c.id !== used && can(c)); const w = pool.map(c => (c.need === 'debt' ? 3 : c.need === 'reel' ? 1.5 : 1)); let r = rnd() * w.reduce((a, b) => a + b, 0); for (let i = 0; i < pool.length; i++) { r -= w[i]; if (r <= 0) return pool[i]; } return pool[0]; }
    function newRound() { J.round++; J.card = chooseCard(); J.phase = 'find'; J.order = players().map(p => p.id); if (!J.order.length) J.order = ['__house'];
      J.objs = J.order.map((id, i) => ({ id: nid++, round: J.round, slot: i, card: J.card.id, img: null, snd: null, op: null, r: {}, keeps: [] }));
      J.order.forEach(id => { hands[id] = { depth: 0, q: null, heard: '' }; deal(id); }); H.crowdShow && H.crowdShow(null); speak(J.card.q); H.ungate && H.ungate(); draw(); }
    const n = () => J.order.length, slotOf = (id, ph) => { const i = J.order.indexOf(id); if (i < 0) return null; const N = n(); return J.objs[(i - (ph === 'sound' ? 1 : ph === 'spoil' ? 2 : 0) + 2 * N) % N]; };
    const whoOn = (o, ph) => J.order[(o.slot + (ph === 'sound' ? 1 : ph === 'spoil' ? 2 : 0)) % n()];
    // ---- deals: what each phone is handed now, from where the room has been going
    function deal(id) { if (!J.ready) return; const h = hands[id] = hands[id] || { depth: 0 }, c = J.card, o = slotOf(id, J.phase);
      if (J.phase === 'find') h.cands = dealFind(id, h); else if (J.phase === 'sound' && o) h.discs = dealSound(id, o, h); else if (J.phase === 'spoil' && o) h.ops = dealOps(id); }
    function dealFind(id, h) { const c = J.card, used = new Set(J.reel.map(o => o.img.k).concat(J.objs.filter(o => o.img).map(o => o.img.k))); let idx;
      const gold = ST.keeps.filter(x => x.owner === id && x.layer === 'img' && !x.spent).map(x => x.item.k);
      if (c.pool === 'reel' || c.pool === 'debt') { const base = c.pool === 'reel' ? [...new Set(J.reel.map(o => o.img.k))] : ST.debts.map(d => d.k); const out = new Set();
        base.forEach(k => { out.add(k); (LIB.bySrc[shot(k).src] || []).slice(0, 12).forEach(x => out.add(x)); }); const v = steer(); idx = [...out].filter(k => c.pool === 'reel' || !used.has(k)).sort((a, b) => dotK(v, b) - dotK(v, a)); }
      else { let v = steer(); add(v, vecW(c.w || ''), .6); if (h.q) add(v, h.q, 2.4); if (c.near === 'hero' && ST.cast.hero) add(v, vecK(ST.cast.hero.k), 1.5);
        if (c.near === 'two' && ST.att.length >= 2) { add(v, ST.att[0].v, 1); add(v, ST.att[1].v, 1); }
        if (empty(v)) idx = shuffle(Array.from({ length: 300 }, () => Math.floor(rnd() * LIB.n))).filter(k => isArc(k) && !used.has(k));
        else { const s = LIB.sims(v); if (c.anti && !h.q) for (let i = 0; i < s.length; i++) s[i] = -s[i]; idx = []; for (let i = 0; i < s.length; i++) if (isArc(i) && !used.has(i)) idx.push(i); idx.sort((a, b) => s[b] - s[a]); idx = idx.slice(0, 600); } }
      const d = h.depth || 0, win = idx.slice(d * 36, d * 36 + 90), wild = Array.from({ length: 8 }, () => Math.floor(rnd() * LIB.n)).filter(k => isArc(k) && !used.has(k)).slice(0, 2);
      return [...new Set([...gold, ...softPick(win.length ? win : idx, 6), ...wild])].slice(0, 9); }
    function sndOf(kind, a) { if (kind === 'clip') { const s = shot(a), K = SK[s.id] || ['noise']; return { kind, ref: a, u: s.video, t0: 0, t1: Math.min(5, s.dur || 5), th: thumbOf(s.video), fam: /music/.test(K[0]) ? 'music' : /speech|mixed/.test(K[0]) ? 'voice' : 'field', label: label(a) }; }
      if (kind === 'line' || kind === 'funny') { const l = R[kind === 'line' ? 'lines' : 'funny'][a], u = R.r2 + R.P[l.v[0]] + '/clips/' + l.v[1] + '.mp4'; return { kind, ref: a, u, t0: l.t0, t1: l.t1, th: thumbOf(u), fam: 'voice', x: l.x, label: l.f }; }
      if (kind === 'music') { const m = R.music[a], u = R.r2 + R.P[m.v[0]] + '/clips/' + m.v[1] + '.mp4'; return { kind, ref: a, u, t0: Math.min(4, Math.max(0, (m.d || 20) - 30)), t1: Math.min(4, Math.max(0, (m.d || 20) - 30)) + 6, th: thumbOf(u), fam: 'music', label: m.f }; }
      if (kind === 'found') { const t = TR[a.c]; return { kind, ref: a, u: t.video, t0: a.t0, t1: a.t1, th: /^http/.test(t.thumb || '') ? t.thumb : thumbOf(t.video), fam: 'voice', x: a.x, label: t.title }; } }
    const keyOf = s => s.kind + ':' + (typeof s.ref === 'object' ? s.ref.c + '@' + s.ref.t0 : s.ref);
    function found(text) { if (!TR) return []; if (!TW) { TW = new Map(); for (const id in TR) { const w = TR[id].words; for (let i = 0; i < w.length; i++) { const k = stem(String(w[i][0]).toLowerCase().replace(/[^a-z]/g, '')); if (k.length < 4 || STOP.has(k)) continue; let l = TW.get(k); if (!l) TW.set(k, l = []); if (l.length < 30) l.push([id, i]); } } }
      const out = []; words(text).map(stem).forEach(k => (TW.get(k) || []).forEach(([id, i]) => { const w = TR[id].words, a = Math.max(0, i - 1), b = Math.min(w.length - 1, i + 2), t1 = w[b + 1] ? w[b + 1][1] : w[b][1] + .5; if (t1 - w[a][1] < 4) out.push({ c: id, t0: Math.max(0, w[a][1] - .05), t1: t1 + .05, x: w.slice(a, b + 1).map(x => x[0]).join(' ') }); }));
      return shuffle(out).slice(0, 3); }
    function dealSound(id, o, h) { const c = J.card, vi = vecK(o.img.k), v = add(new Float32Array(vi), steer(), .3), out = [];
      // motifs first: a sound that survived on an image like this one comes back with it
      ST.motifs.forEach(m => { let a = 0; const mv = vecK(m.k); for (let j = 0; j < 512; j++) a += mv[j] * vi[j]; if (a > .8 || shot(m.k).src === shot(o.img.k).src) out.push({ ...m.snd, motif: 1 }); });
      ST.keeps.filter(x => x.owner === id && x.layer === 'snd' && !x.spent).forEach(x => out.push({ ...x.item, gold: 1 }));
      if (h.text) { const ws = words(h.text); const L = []; ['lines', 'funny'].forEach(kind => R[kind].forEach((l, i) => { const lw = l.x.toLowerCase(); const sc = ws.filter(w => lw.includes(w)).length; if (sc) L.push([sc, kind === 'lines' ? 'line' : 'funny', i]); }));
        L.sort((a, b) => b[0] - a[0]).slice(0, 3).forEach(([, k, i]) => out.push(sndOf(k, i))); found(h.text).forEach(f => out.push(sndOf('found', f))); }
      const qv = h.q ? add(new Float32Array(v), h.q, 2) : v, ranked = SND.slice().sort((a, b) => dotK(qv, b) - dotK(qv, a)), d = h.depth || 0;
      const want = c.snd === 'wrong' && !h.q ? ranked.slice().reverse() : ranked; softPick(want.slice(d * 30, d * 30 + 80), 4, 10).forEach(k => out.push(sndOf('clip', k)));
      out.push(sndOf('line', Math.floor(rnd() * R.lines.length))); out.push(sndOf('music', Math.floor(rnd() * R.music.length)));
      const seen = new Set(); return out.filter(s => { const k = keyOf(s); if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 9); }
    function dealOps(id) { const w = OPS.map(o => 1 + (ST.style[o] || 0) * .6), pool = OPS.slice(), out = []; while (out.length < 3) { let r = rnd() * pool.reduce((a, o) => a + w[OPS.indexOf(o)], 0), i = 0; for (; i < pool.length; i++) { r -= w[OPS.indexOf(pool[i])]; if (r <= 0) break; } out.push(pool.splice(Math.min(i, pool.length - 1), 1)[0]); }
      ST.keeps.filter(x => x.owner === id && x.layer === 'op' && !x.spent).forEach(x => { if (!out.includes(x.item.o)) out.unshift(x.item.o); }); return out; }
    // ---- moves from the phones
    function onMsg(p, m) { if (!J.ready) return; const h = hands[p.id];
      if (m.t === 'heard') { const t = String(m.part || '').slice(-80); if (t) H.say(p.id, t, 2200); return; }
      if (m.t === 'say' && h) { (async () => { let text = String(m.text || '').trim(); if (!text && m.a && H.ears) text = await H.ears.read(m.a, m.mime).catch(() => ''); h.text = text; h.heard = text.slice(0, 60); h.q = vecW(text); h.depth = 0; if (text) H.say(p.id, text.slice(0, 60), 2600); deal(p.id); H.broadcast(); drawSide(); })(); return; }
      if (m.t === 'far' && h) { h.depth = (h.depth || 0) + 1; deal(p.id); H.broadcast(); return; }
      if (m.t === 'near' && h) { h.depth = 0; h.q = null; h.text = ''; h.heard = ''; deal(p.id); H.broadcast(); return; }
      if (m.t === 'pick') { const o = slotOf(p.id, J.phase); if (!o || !h) return;
        if (J.phase === 'find') { const k = +m.key; if (!h.cands.includes(k)) return; o.img = { k, by: p.id }; spend(p.id, 'img', x => x.item.k === k); }
        else if (J.phase === 'sound') { const s = (h.discs || []).find(s => keyOf(s) === m.key); if (!s) return; o.snd = { ...s, by: p.id }; delete o.snd.motif; delete o.snd.gold; spend(p.id, 'snd', x => keyOf(x.item) === m.key); spotlight(o); }
        else if (J.phase === 'spoil') { if (!(h.ops || []).includes(m.key)) return; o.op = { o: m.key, by: p.id }; spend(p.id, 'op', x => x.item.o === m.key); spotlight(o); }
        H.act(p.id, 'hop', 820); checkDone(); draw(); return; }
      if (m.t === 'keep' && J.phase === 'keep') { const o = J.objs.find(o => o.id === m.obj); if (!o || !['img', 'snd', 'op', 'all'].includes(m.layer) || (m.layer !== 'all' && !o[m.layer])) return;
        J.objs.forEach(x => x.keeps = x.keeps.filter(k => k.by !== p.id)); o.keeps.push({ by: p.id, layer: m.layer }); H.act(p.id, 'cheer', 1600); checkDone(); draw(); return; }
      if (m.t === 'play') { if (J.playing) stopIt(); else playList(m.what === 'film' ? filmList() : J.objs.filter(o => o.img)); return; } }
    function spend(id, layer, f) { ST.keeps.forEach(x => { if (x.owner === id && x.layer === layer && !x.spent && f(x)) x.spent = J.round; }); }
    function checkDone() { const ph = J.phase, all = J.phase === 'keep' ? J.order.every(id => J.objs.some(o => o.keeps.some(k => k.by === id))) : J.objs.every(o => ph === 'find' ? o.img : ph === 'sound' ? o.snd : o.op);
      if (all) H.gate(ph === 'keep' ? 'Next card ▸' : ph === 'spoil' ? 'Play it ▸' : 'Pass ▸', 'any', advance); }
    // the house fills what nobody did, in plain sight: the archive is an author too
    function fill() { J.objs.forEach(o => { if (J.phase === 'find' && !o.img) { const c = (hands[J.order[o.slot]] || {}).cands || dealFind(J.order[o.slot], { depth: 0 }); o.img = { k: c[0], by: null }; }
        if (J.phase === 'sound' && !o.snd) { const d = dealSound(null, o, { depth: 0 }); o.snd = { ...d[0], by: null }; } if (J.phase === 'spoil' && !o.op && rnd() < .5) o.op = { o: pick(OPS), by: null }; }); }
    function advance() { stopIt(); fill();
      if (J.phase === 'find') { J.phase = 'sound'; J.order.forEach(id => { hands[id].depth = 0; hands[id].q = null; hands[id].text = ''; hands[id].heard = ''; deal(id); }); speak(J.card.snd === 'wrong' ? 'Give it the wrong sound.' : 'Give it a sound.'); }
      else if (J.phase === 'sound') { J.phase = 'spoil'; J.order.forEach(id => deal(id)); speak('Spoil it.'); }
      else if (J.phase === 'spoil') { J.phase = 'play'; J.objs.forEach((o, i) => { const nx = J.objs[(i + 1) % J.objs.length]; o.flash = thumbOf(shot(nx.img.k).video); }); playList(J.objs, () => { J.phase = 'keep'; speak('What do we keep?'); draw(); }); }
      else if (J.phase === 'keep') { remember(); J.reel.push(...J.objs); newRound(); return; }
      draw(); }
    // ---- the world remembers what the room did
    function remember() { const c = J.card, sc = o => (o.r.rose || 0) + 2 * (o.r.bravo || 0) - (o.r.tomato || 0) - (o.r.cut || 0) + 2 * o.keeps.length;
      ST.att.forEach(a => a.w *= a.decay); ST.att = ST.att.filter(a => a.w > .08);
      J.objs.forEach(o => ST.att.push({ v: vecK(o.img.k), w: .45, decay: .55, k: o.img.k, by: o.img.by }));
      const best = J.objs.slice().sort((a, b) => sc(b) - sc(a))[0];
      if (c.role && best) { ST.cast[c.role] = { k: best.img.k, by: best.img.by, round: J.round }; ST.att.unshift({ v: vecK(best.img.k), w: c.role === 'hero' ? 1.6 : 1, decay: c.role === 'hero' ? .88 : .7, k: best.img.k, by: best.img.by, role: c.role });
        ST.log.unshift({ r: J.round, html: `${chip(best.img.by)} ${esc(c.move)}: <b>${esc(label(best.img.k))}</b> is the ${esc(c.role)}` }); }
      if (c.move === 'END' && best) best.ending = true;
      J.objs.forEach(o => { const combo = o.keeps.some(k => k.layer === 'all' || k.layer === 'snd') || (o === best && sc(o) > 0); if (combo && o.snd) { ST.motifs.unshift({ k: o.img.k, snd: o.snd, by: [o.img.by, o.snd.by] }); ST.motifs = ST.motifs.slice(0, 6); ST.log.unshift({ r: J.round, html: `${chip(o.img.by)}${chip(o.snd.by)} MOTIF: <b>${esc(label(o.img.k))}</b> with <b>${esc(o.snd.x || o.snd.label || o.snd.fam)}</b>` }); }
        if (o.op && o.op.o === 'soon') { ST.debts.unshift({ k: o.img.k, by: o.op.by }); ST.log.unshift({ r: J.round, html: `${chip(o.op.by)} DEBT: we never saw the rest of <b>${esc(label(o.img.k))}</b>` }); }
        if (o.op) ST.style[o.op.o] = (ST.style[o.op.o] || 0) + 1;
        o.keeps.forEach(k => { const item = k.layer === 'img' ? o.img : k.layer === 'snd' ? o.snd : k.layer === 'op' ? o.op : o.img; if (!item) return; ST.keeps.push({ owner: k.by, layer: k.layer === 'all' ? 'img' : k.layer, item, round: J.round }); if (k.layer === 'img' || k.layer === 'all') ST.att.push({ v: vecK(o.img.k), w: .7, decay: .75, k: o.img.k, by: k.by }); }); });
      if (c.pool === 'debt') ST.debts = ST.debts.filter(d => !J.objs.some(o => shot(o.img.k).src === shot(d.k).src));
      ST.att.sort((a, b) => b.w - a.w); ST.att = ST.att.slice(0, 10); ST.log = ST.log.slice(0, 12); }
    // ---- the stand: tiles while the passes happen, one object at a time when it plays
    function spotlight(o) { if (J.playing) return; spotQ = spotQ.filter(x => x !== o); spotQ.push(o); if (!spot) nextSpot(); }
    function nextSpot() { const o = spotQ.shift(); if (!o) { spot = null; drawTiles(); return; } const t = root$.querySelector(`.jt[data-o="${o.id}"]`); if (!t) return nextSpot();
      t.classList.add('spot'); spot = run(res(o), { V: t.querySelector('video'), A: H.AP[1], X: t.querySelector('.jx'), B: t.querySelector('.jb') }, { done: () => { t.classList.remove('spot'); const v = t.querySelector('video'); v.muted = true; v.loop = true; v.play().catch(() => { }); spot = null; setTimeout(nextSpot, 250); } }); }
    function res(o) { const s = shot(o.img.k); return { v: s.video, vin: 0, snd: o.snd ? { u: o.snd.u, t0: o.snd.t0, t1: o.snd.t1 } : null, op: o.op, flash: o.flash || '' }; }
    function filmList() { const all = J.reel.concat(J.phase === 'keep' || J.phase === 'play' ? J.objs : []).filter(o => o.img); return all.filter(o => !o.ending).concat(all.filter(o => o.ending)); }
    function playList(list, done) { stopIt(); if (!list.length) return; if (spot) { spot(); spot = null; } J.playing = list; J.at = 0; root$.querySelector('#jSolo').hidden = false; root$.querySelector('#jTiles').hidden = true;
      const step = () => { if (J.playing !== list) return; const o = list[J.at]; if (!o) { J.playing = null; J.at = -1; root$.querySelector('#jSolo').hidden = true; root$.querySelector('#jTiles').hidden = false; done && done(); draw(); return; }
        const nx = list[J.at + 1] || list[0]; o.flash = o.flash || thumbOf(shot(nx.img.k).video);
        $('#jAuth').innerHTML = authHTML(o); H.act(o.img.by || J.order[0], 'hop', 820); stopPlay = run(res(o), solo, { done: () => { J.at++; step(); } }); drawSide(); H.broadcast(); };
      step(); draw(); }
    function stopIt() { if (stopPlay) { stopPlay(); stopPlay = null; } if (J.playing) { J.playing = null; J.at = -1; root$.querySelector('#jSolo').hidden = true; root$.querySelector('#jTiles').hidden = false; } }
    const chip = id => `<i class="jchip" style="--c:${colOf(id)}">${id && P(id) ? esc(P(id).name[0]) : '◆'}</i>`;
    const authHTML = o => `<span>${chip(o.img.by)}${I.eye}<em>${esc(nameOf(o.img.by))}</em></span>${o.snd ? `<span>${chip(o.snd.by)}${famIcon(o.snd.fam)}<em>${esc(nameOf(o.snd.by))}</em></span>` : ''}${o.op ? `<span>${chip(o.op.by)}${I[o.op.o]}<em>${OPN[o.op.o]}</em></span>` : ''}`;
    function drawTiles() { const T = root$.querySelector('#jTiles'); T.style.setProperty('--n', Math.min(4, Math.max(1, J.objs.length))); T.style.setProperty('--rows', Math.ceil(J.objs.length / 4) || 1);
      const have = new Map([...T.children].map(d => [d.dataset.o, d]));
      J.objs.forEach(o => { let t = have.get(String(o.id)); have.delete(String(o.id)); if (!t) { t = document.createElement('div'); t.className = 'jt'; t.dataset.o = o.id; t.innerHTML = '<video muted loop playsinline preload="auto"></video><div class="jb"></div><img class="jx" alt=""><div class="jl"></div><div class="jw"></div>'; T.append(t); }
        const v = t.querySelector('video'), u = o.img ? shot(o.img.k).video : ''; if (v.dataset.u !== u && !t.classList.contains('spot')) { v.dataset.u = u; if (u) { v.src = u; v.play().catch(() => { }); } else v.removeAttribute('src'); }
        const who = whoOn(o, J.phase), working = ['find', 'sound', 'spoil'].includes(J.phase) && !(J.phase === 'find' ? o.img : J.phase === 'sound' ? o.snd : o.op);
        t.querySelector('.jw').innerHTML = working && P(who) ? `${mini(P(who).av)}<b>${I[PASS[J.phase]]}</b>` : '';
        t.querySelector('.jl').innerHTML = `<span class="${o.img ? '' : 'no'}">${chip(o.img && o.img.by !== undefined ? o.img.by : J.order[o.slot])}${I.eye}</span><span class="${o.snd ? '' : 'no'}" style="${o.snd ? '--f:' + FAM[o.snd.fam] : ''}">${chip(o.snd ? o.snd.by : whoOn(o, 'sound'))}${o.snd ? famIcon(o.snd.fam) : I.ear}</span><span class="${o.op ? '' : 'no'}">${chip(o.op ? o.op.by : whoOn(o, 'spoil'))}${o.op ? I[o.op.o] : I.cut}</span>${o.keeps.length ? `<span class="kp">${o.keeps.map(k => chip(k.by)).join('')}${I.keep}</span>` : ''}`; });
      have.forEach(d => d.remove()); }
    function drawCard() { const c = J.card; root$.querySelector('#jCard').innerHTML = c ? `<small>${esc(c.move)} · round ${J.round}</small>${esc(J.phase === 'find' ? c.q : J.phase === 'sound' ? (c.snd === 'wrong' ? 'Give it the wrong sound.' : 'Give it a sound.') : J.phase === 'spoil' ? 'Spoil it.' : J.phase === 'keep' ? 'What do we keep?' : c.q)}` : ''; }
    function drawSide() { const ph = J.phase, rows = J.order.filter(id => P(id)).map(id => { const o = ph === 'keep' ? null : slotOf(id, ph), done = ph === 'keep' ? J.objs.some(x => x.keeps.some(k => k.by === id)) : o && (ph === 'find' ? o.img : ph === 'sound' ? o.snd : ph === 'spoil' ? o.op : 1);
        return `<div class="jp"><span class="m">${mini(P(id).av)}</span><b>${esc(P(id).name)}</b><span class="i">${I[PASS[ph]] || ''}</span>${o && o.img && ph !== 'find' ? `<img src="${esc(thumbOf(shot(o.img.k).video))}" alt=""><small>${esc(nameOf(o.img.by))}’s</small>` : ''}<span class="ok">${done ? '✓' : (hands[id] && hands[id].heard ? '“' + esc(hands[id].heard) + '”' : '')}</span></div>`; }).join('');
      const world = [ST.cast.hero && ['hero', ST.cast.hero], ST.cast.place && ['place', ST.cast.place], ST.cast.stranger && ['stranger', ST.cast.stranger], ST.cast.suspect && ['suspect', ST.cast.suspect], ST.cast.watcher && ['watcher', ST.cast.watcher], ST.cast.ending && ['ending', ST.cast.ending]].filter(Boolean)
        .map(([r, x]) => `<span class="jw1"><img src="${esc(thumbOf(shot(x.k).video))}" alt="">${chip(x.by)}<em>${r}</em></span>`).join('')
        + ST.motifs.slice(0, 3).map(m => `<span class="jw1"><img src="${esc(thumbOf(shot(m.k).video))}" alt=""><b style="color:${FAM[m.snd.fam]}">${famIcon(m.snd.fam)}</b><em>motif</em></span>`).join('')
        + ST.debts.slice(0, 2).map(d => `<span class="jw1 debt"><img src="${esc(thumbOf(shot(d.k).video))}" alt=""><em>unseen</em></span>`).join('');
      H.side(`<div class="ph">The Jam <small>round ${J.round} · ${J.reel.length} in the film</small></div>
        <div class="row" style="margin-bottom:6px"><button class="btn chip" id="jRound" ${J.objs.some(o => o.img) ? '' : 'disabled'}>${J.playing ? '■ stop' : '▶ this round'}</button><button class="btn chip" id="jFilm" ${J.reel.length ? '' : 'disabled'}>▶ the film</button><button class="btn chip" id="jCut" ${J.reel.length ? '' : 'disabled'}>edit the film</button>${['find', 'sound', 'spoil'].includes(ph) ? '<button class="btn chip" id="jFill">fill the rest</button>' : ''}</div>
        ${J.ready ? '' : `<div class="hint">${esc(J.why)}</div>`}<div class="jps">${rows}</div>
        ${world ? `<div class="ph" style="margin-top:6px">The world <small>what the room has made true</small></div><div class="jworld">${world}</div>` : ''}
        ${ST.log.length ? `<div class="jlog">${ST.log.slice(0, 5).map(l => `<div>${l.html}</div>`).join('')}</div>` : ''}`, 'jam');
      $('#jRound').onclick = () => J.playing ? stopIt() || draw() : playList(J.objs.filter(o => o.img)); $('#jFilm').onclick = () => playList(filmList()); $('#jCut').onclick = () => { stopIt(); H.seed = toFilm(); H.playGame('cut'); };
      const f = $('#jFill'); if (f) f.onclick = () => { fill(); checkDone(); draw(); }; }
    function draw() { if (!J.ready) { H.slate(H.card(`<div class="big">The Jam<small>${esc(J.why)}</small></div>`, 'night')); drawSide(); H.broadcast(); return; } H.slate(''); drawCard(); drawTiles(); drawSide(); H.syncCrew(); H.broadcast(); }
    const speak = t => { try { const u = new SpeechSynthesisUtterance(t); u.rate = .95; speechSynthesis.cancel(); speechSynthesis.speak(u); } catch (e) { } };
    // the film for The Cut: every object as a clip with its sound laid on it, the cuts done as well as an edit list can
    function toFilm() { const F = Cut.blank('The Jam'); filmList().forEach(o => { const s = shot(o.img.k), op = o.op && o.op.o, len = op === 'soon' ? 1.3 : op === 'hold' ? 4.2 : 4.2;
        const add1 = (t0, t1) => { const c = Cut.shot(s.video, t0, t1, { d: s.dur || null, label: label(o.img.k), by: o.img.by }); F.clips.push(c); return c; };
        let c; if (op === 'repeat') { c = add1(0, 1.15); add1(0, 1.15); add1(0, 1.15); } else c = add1(0, Math.min(s.dur || 6, len));
        if (o.snd) { const sl = op === 'silence' ? 1.6 : Math.min(6, (o.snd.t1 || o.snd.t0 + 4.2) - o.snd.t0); F.sounds.push(o.snd.fam === 'music' ? Cut.music(c.id, o.snd.u, o.snd.t0, o.snd.t0 + sl, { vol: .8 }) : Cut.voice(c.id, o.snd.u, o.snd.t0, o.snd.t0 + sl, { text: o.snd.x || null, off: 0 })); } }); return F; }
    function stateFor(p) { const h = hands[p.id] || {}, ph = J.phase, o = ph === 'keep' || ph === 'play' ? null : slotOf(p.id, ph);
      const ob = x => x && ({ id: x.id, th: thumbOf(shot(x.img.k).video), v: shot(x.img.k).video, img: { c: colOf(x.img.by), n: nameOf(x.img.by) }, snd: x.snd ? { c: colOf(x.snd.by), n: nameOf(x.snd.by), fam: x.snd.fam, u: x.snd.u, t0: x.snd.t0, t1: x.snd.t1, th: x.snd.th } : null, op: x.op ? { o: x.op.o, c: colOf(x.op.by), n: nameOf(x.op.by) } : null, kept: x.keeps.filter(k => k.by === p.id).map(k => k.layer) });
      const cur = J.playing ? J.playing[J.at] : null;
      return { phase: 'jam', noScore: true, me: p.id, ready: J.ready, round: J.round, pass: ph, card: J.card ? { q: J.card.q, move: J.card.move, snd: J.card.snd } : null, playing: !!J.playing, now: cur ? ob(cur) : null, heard: h.heard || '',
        mine: o ? ob(o.img ? o : null) : null, from: o && o.img ? nameOf(o.img.by) : '', crew: J.order.filter(id => P(id)).map(id => ({ id, av: P(id).av, c: col(P(id).av), done: ph === 'keep' ? J.objs.some(x => x.keeps.some(k => k.by === id)) : !!(slotOf(id, ph) && (ph === 'find' ? slotOf(id, ph).img : ph === 'sound' ? slotOf(id, ph).snd : slotOf(id, ph).op)) })),
        pickd: o ? (ph === 'find' ? (o.img && o.img.by === p.id ? String(o.img.k) : '') : ph === 'sound' ? (o.snd && o.snd.by === p.id ? keyOf(o.snd) : '') : ph === 'spoil' ? (o.op && o.op.by === p.id ? o.op.o : '') : '') : '',
        cands: ph === 'find' && h.cands ? h.cands.map(k => ({ key: String(k), th: thumbOf(shot(k).video), v: shot(k).video, gold: ST.keeps.some(x => x.owner === p.id && x.layer === 'img' && !x.spent && x.item.k === k) })) : null,
        discs: ph === 'sound' && h.discs ? h.discs.map(s => ({ key: keyOf(s), th: s.th, u: s.u, t0: s.t0, t1: s.t1, fam: s.fam, x: s.x || '', gold: !!s.gold, motif: !!s.motif })) : null,
        ops: ph === 'spoil' && h.ops ? h.ops.map(o2 => ({ key: o2, n: OPN[o2] })) : null,
        objs: ph === 'keep' ? J.objs.filter(x => x.img).map(ob) : null }; }
    draw();
    return { stateFor, draw, onMsg, onJoin: p => { if (J.ready && !J.order.includes(p.id) && J.phase === 'find') { J.order.push(p.id); J.objs.push({ id: nid++, round: J.round, slot: J.order.length - 1, card: J.card.id, img: null, snd: null, op: null, r: {}, keeps: [] }); hands[p.id] = { depth: 0 }; deal(p.id); } draw(); },
      crowdTarget: () => { const o = J.playing ? J.playing[J.at] : null; if (o) { o.by = o.img.by; return o; } return null; }, performer: () => { const o = J.playing ? J.playing[J.at] : null; return o ? o.img.by : null; },
      stop() { stopIt(); if (spot) spot(); root$.hidden = true; root$.innerHTML = ''; try { speechSynthesis.cancel(); } catch (e) { } } };
  }

  // ======================================================================= the phone: point at things, talk to the archive
  const L = { prev: null, talk: null, sending: false, sel: '' };
  function phone(S, api) {
    if (S.phase !== 'jam') return null; L.S = S;
    const ph = S.pass, mk = () => [ph, S.round, S.playing].join('|');
    const take = {
      key: 'jam' + mk(),
      render(el) { el.innerHTML = `<div class="jm"><div class="jhd"><span class="jpi">${I[PASS[ph]] || I.play}</span><span class="jq" id="jQ"></span><span class="jcrew" id="jCrew"></span></div><div class="jbd"><div class="jlf" id="jLf"></div><div class="jrt" id="jRt"></div></div></div>`; L.take = take; take.patch(el, api, true); },
      patch(el, api, force) { const S = L.S;
        el.querySelector('#jQ').textContent = !S.card ? '' : ph === 'find' ? S.card.q : ph === 'sound' ? (S.card.snd === 'wrong' ? 'Give it the wrong sound.' : 'Give it a sound.') : ph === 'spoil' ? 'Spoil it.' : ph === 'keep' ? 'What do we keep?' : S.card.q;
        el.querySelector('#jCrew').innerHTML = S.crew.map(c => `<i class="${c.done ? 'ok' : ''}" style="--c:${c.c}">${mini(c.av)}</i>`).join('');
        const lf = el.querySelector('#jLf'), rt = el.querySelector('#jRt');
        if (S.playing || ph === 'play') { const n = S.now; const k = 'p' + (n ? n.id : ''); if (lf.dataset.k !== k) { lf.dataset.k = k; lf.innerHTML = n ? `<div class="jprev"><img src="${esc(n.th)}" alt=""></div><div class="jby">${who3(n)}</div>` : ''; } if (rt.dataset.k !== 'p') { rt.dataset.k = 'p'; rt.innerHTML = `<div class="jbig">${I.play}</div>`; } return; }
        if (ph === 'keep') { const k = JSON.stringify(S.objs); if (rt.dataset.k !== k) { rt.dataset.k = k; lf.dataset.k = ''; lf.innerHTML = `<div class="jbig">${I.keep}</div>`;
            rt.innerHTML = `<div class="jkeeps">${(S.objs || []).map(o => `<div class="jko"><button data-keep="${o.id}" data-l="img" class="${o.kept.includes('img') ? 'on' : ''}"><img src="${esc(o.th)}" alt=""><i style="--c:${o.img.c}"></i></button>${o.snd ? `<button data-keep="${o.id}" data-l="snd" class="snd ${o.kept.includes('snd') ? 'on' : ''}" style="--f:${FAM[o.snd.fam]}">${famIcon(o.snd.fam)}<i style="--c:${o.snd.c}"></i></button>` : ''}${o.op ? `<button data-keep="${o.id}" data-l="op" class="op ${o.kept.includes('op') ? 'on' : ''}">${I[o.op.o]}<i style="--c:${o.op.c}"></i></button>` : ''}<button data-keep="${o.id}" data-l="all" class="all ${o.kept.includes('all') ? 'on' : ''}">${I.keep}</button></div>`).join('')}</div>`;
            rt.querySelectorAll('[data-keep]').forEach(b => b.onclick = () => { api.buzz(16); api.send({ t: 'keep', obj: +b.dataset.keep, layer: b.dataset.l }); }); } return; }
        // the thing in your hands: your find, or the one passed to you
        const lk = JSON.stringify([ph, S.mine && S.mine.id, S.mine && S.mine.snd && S.mine.snd.u, S.mine && S.mine.op && S.mine.op.o, S.pickd, S.from]);
        if (lf.dataset.k !== lk) { lf.dataset.k = lk; const m = S.mine;
          if (ph === 'find') { const c = (S.cands || []).find(c => c.key === S.pickd); lf.innerHTML = `<div class="jprev">${c ? `<video src="${esc(c.v)}" muted loop playsinline autoplay></video>` : `<div class="jbig dim">${I.eye}</div>`}</div>`; }
          else if (m) { lf.innerHTML = `<div class="jprev"><video src="${esc(m.v)}" muted loop playsinline autoplay></video>${m.op ? `<b class="jop">${I[m.op.o]}</b>` : ''}</div><div class="jby">${who3(m)}</div>`; }
          else lf.innerHTML = '<div class="jbig dim">…</div>'; }
        const rk = JSON.stringify([ph, S.cands, S.discs, S.ops, S.pickd, S.heard]);
        if (force || rt.dataset.k !== rk) { if (L.talk && !force) return; rt.dataset.k = rk;
          const grid = ph === 'find' ? (S.cands || []).map(c => `<button class="jc ${c.key === S.pickd ? 'on' : ''} ${c.gold ? 'gold' : ''}" data-pick="${c.key}"><img src="${esc(c.th)}" alt="" draggable="false"></button>`).join('')
            : ph === 'sound' ? (S.discs || []).map(d => `<button class="jc jd ${d.key === S.pickd ? 'on' : ''} ${d.gold ? 'gold' : ''} ${d.motif ? 'motif' : ''}" data-pick="${esc(d.key)}" data-u="${esc(d.u)}" data-t0="${d.t0}" data-t1="${d.t1}" style="--f:${FAM[d.fam]}"><img src="${esc(d.th)}" alt="" draggable="false"><b>${famIcon(d.fam)}</b></button>`).join('')
            : ph === 'spoil' ? (S.ops || []).map(o => `<button class="jc jo ${o.key === S.pickd ? 'on' : ''}" data-pick="${o.key}">${I[o.key]}<small>${o.n}</small></button>`).join('') : '';
          rt.innerHTML = `<div class="jgrid ${ph}">${grid}</div>${ph === 'spoil' ? '' : `<div class="jtools"><button class="jmic" id="jTalk" aria-label="talk">${I.mic}<i id="jLv"></i></button><span class="jheard">${S.heard ? '“' + esc(S.heard) + '”' : ''}</span><button class="jfar" id="jFar" aria-label="farther">${I.far}</button></div>`}`;
          rt.querySelectorAll('[data-pick]').forEach(b => b.onclick = () => { api.buzz(14); api.send({ t: 'pick', key: b.dataset.pick }); if (b.dataset.u) hear(b); });
          const f = rt.querySelector('#jFar'); if (f) f.onclick = () => { api.buzz(8); api.send({ t: 'far' }); };
          const t = rt.querySelector('#jTalk'); if (t) talk(t, api); } }
    };
    function who3(o) { return `<span style="--c:${o.img.c}">${I.eye}${esc(o.img.n)}</span>${o.snd ? `<span style="--c:${o.snd.c}">${famIcon(o.snd.fam)}${esc(o.snd.n)}</span>` : ''}${o.op ? `<span style="--c:${o.op.c}">${I[o.op.o]}${esc(o.op.n)}</span>` : ''}`; }
    function hear(b) { const a = L.prev || (L.prev = new Audio()); a.src = b.dataset.u; const t0 = +b.dataset.t0 || 0, t1 = +b.dataset.t1 || t0 + 5; a.addEventListener('loadedmetadata', () => { try { a.currentTime = t0; } catch (e) { } a.play().catch(() => { }); }, { once: true }); clearTimeout(a._t); a._t = setTimeout(() => a.pause(), Math.min(6, t1 - t0) * 1000 + 200);
      const v = document.querySelector('#jLf video'); if (v) { try { v.currentTime = 0; } catch (e) { } v.play().catch(() => { }); } }
    // talk to the archive: hold, say what you're looking for, let go
    function talk(b, api) {
      b.onpointerdown = e => { e.preventDefault(); if (L.talk || L.sending) return; api.buzz(16); try { b.setPointerCapture(e.pointerId); } catch (x) { } b.classList.add('on'); let last = 0;
        L.talk = window.Ears ? Ears.hold(api, { onLevel: v => { const i = document.getElementById('jLv'); if (i) i.style.transform = `scale(${1 + Math.min(1, v * 3)})`; }, onPartial: t => { const now = performance.now(); if (now - last > 200) { last = now; api.send({ t: 'heard', part: t }); } const h = document.querySelector('.jheard'); if (h) h.textContent = t; } }) : null;
        if (L.talk) L.talk.ready.catch(() => { L.talk = null; b.classList.remove('on'); }); };
      const up = async e => { const h = L.talk; if (!h) return; L.talk = null; b.classList.remove('on'); L.sending = true; const r = await h.stop().catch(() => null); L.sending = false; if (r) api.send({ t: 'say', a: r.a, mime: r.mime, dur: r.dur, text: r.text }); };
      b.onpointerup = up; b.onpointercancel = up; b.oncontextmenu = e => e.preventDefault(); }
    return { key: take.key, status: null, cls: 'jamp', throws: true, takeover: take };
  }
  Party.games.jam = { title: 'The Jam', blurb: 'a card asks a question; everyone forages the archive by talking and pointing; each find is passed on to be given a sound, then spoiled with one cut. Every move changes what the archive deals next.', options: [], host, phone };
})();
