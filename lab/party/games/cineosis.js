/* CINEOSIS: a multiplayer game for getting lost together in a moving-image archive. One game, one living film; the round card
   changes only what kind of move you may make to somebody else's material. FIND → PASS → CHANGE → PLAY.
     PASS THE CUT     find a shot · pass · someone gives it sound · someone changes its time · someone finds what follows
     SPOIL IT         find something beautiful · someone spoils it with the wrong sound · someone makes it work · someone spoils that
     CHANNEL SURF     everyone wanders the archive; where you go grows the map; REC makes your path a strip of the film
     BACKLOT          rescue a rejected take · someone decides where it goes · someone gives it a sound
     AUDITION         cast a hero · someone gives them an entrance · a voice · somebody to look at them · the room casts one
     TELEPHONE        find a shot · the next hears only its sound and finds what they imagine · the next sees only that and sounds it
     CHEMISTRY JAM    find a shot · someone joins another to it · someone decides how they meet (cut, rhyme, contrast, merge, overlay, transform) · a sound
     BREAKAWAY        pick something small out of a shot · its neighbour · keep going · it becomes a film of its own
   Tomatoes reject: a take the room pelts leaves the film for the backlot, where anyone can keep it (it comes back gold, with its
   provenance) or the Backlot card can rescue it. The hero stays cast, sounds that survive become motifs, a cut too soon leaves
   something unseen, and every move steers what the archive deals next (Monte Carlo is the weather, not the dealer).
   Built on the lab: markov/shared.js (16,153 shots, CLIP vectors), markov/sam.json (806 cut-outs), tools/sound-kinds.json,
   pictures/rushes.json, odyssey/transcripts.json, party/lexicon, party/ears.js (one key on the stand; talk or type on phones). */
(function () {
  const { esc, rnd, pick, shuffle, mini, KINDS } = Party;
  const NEON = ['#ff4fa3', '#3aa0ff', '#32d17c', '#ffc93c', '#b06bff', '#ff7a3d', '#2fe0d6', '#ff5e5e', '#9bdc3a', '#ff9de1', '#7ea8ff', '#e8e8e8'];
  const col = av => NEON[av % NEON.length], HOUSE = '#6f7a8a';
  const STOP = new Set('a an the and or of to in on at by for with from into onto over under is are was were be been it its this that these those as his her their our your my he she they we you i me him them us one two not no but so if then than there here what which who whom whose when where while out up down off about after before again all any both each few more most other some such only own same very can will just do does did has have had am also yet too nor like said say get got go going want know think yeah okay well really thing things find something make give'.split(' '));
  const stem = w => { for (const x of ['ing', 'ed', 'es', 's']) if (w.length > x.length + 3 && w.endsWith(x)) return w.slice(0, -x.length); return w; };
  const words = t => ((t || '').toLowerCase().match(/[a-z']+/g) || []).map(w => w.replace(/'/g, '')).filter(w => w.length > 2 && !STOP.has(w));
  const thumbOf = u => u ? u.replace('/clips/', '/thumbnails/').replace(/\.mp4.*$/, '.jpg') : '';
  // ---- the cards
  const MODES = {
    pass: { name: 'Pass the Cut', sub: 'find → pass → alter → one film', kind: 'chain', steps: ['find', 'sound', 'time', 'follow'] },
    spoil: { name: 'Spoil It', sub: 'sabotage → repair → new meaning', kind: 'chain', steps: ['beauty', 'spoil', 'repair', 'worse'] },
    surf: { name: 'Channel Surf', sub: 'explore → record → expand', kind: 'surf' },
    backlot: { name: 'Backlot', sub: 'nothing is really gone', kind: 'chain', steps: ['rescue', 'place', 'sound'], need: 'backlot' },
    audition: { name: 'Audition', sub: 'anything can be a hero', kind: 'chain', steps: ['cast', 'entrance', 'voice', 'reaction'], vote: true },
    phone: { name: 'Cutting-Room Telephone', sub: 'mishear → missee → new story', kind: 'chain', steps: ['find', 'listen', 'look'], hide: true },
    chem: { name: 'Chemistry Jam', sub: 'combine → react → transmute', kind: 'chain', steps: ['find', 'attach', 'bond', 'sound'] },
    away: { name: 'Breakaway', sub: 'follow the irrelevant', kind: 'chain', steps: ['detail', 'neighbor', 'carry'], branch: true } };
  const STEP = {
    find: { say: 'Find a shot.', verb: 'finds', deal: 'shots', act: 'Pass it' },
    beauty: { say: 'Find something beautiful.', verb: 'finds beauty', deal: 'shots', w: 'sunset light sea flower beautiful sky dance', act: 'Pass it' },
    cast: { say: 'Who is the hero? Anything can be.', verb: 'casts', deal: 'shots', w: 'person face man woman child dog', act: 'Cast it' },
    rescue: { say: 'Rescue something from the backlot.', verb: 'rescues', deal: 'backlot', act: 'Rescue it' },
    detail: { say: 'Pick something small. Take it somewhere.', verb: 'picks a detail', deal: 'figs', act: 'Follow this' },
    sound: { say: 'Give it a sound.', verb: 'adds sound', deal: 'sounds', act: 'Pass it' },
    spoil: { say: 'It looks serious. Now spoil it.', verb: 'spoils it', deal: 'sounds', wrong: true, act: 'Spoil it' },
    voice: { say: 'Give them a voice.', verb: 'gives a voice', deal: 'sounds', voice: true, act: 'Pass it' },
    look: { say: 'You only see this. What does it sound like?', verb: 'hears it', deal: 'sounds', act: 'Pass it' },
    time: { say: 'Change its time.', verb: 'changes time', deal: 'ops', act: 'Pass it' },
    worse: { say: 'Spoil that. Or save it.', verb: 'spoils that', deal: 'ops', act: 'Pass it' },
    follow: { say: 'Find what follows.', verb: 'finds next', deal: 'shots', near: 1, act: 'Pass it' },
    repair: { say: 'Make it work: find one shot to go between.', verb: 'repairs it', deal: 'shots', near: 1, act: 'Pass it' },
    entrance: { say: 'Give them an entrance: what comes just before?', verb: 'gives an entrance', deal: 'shots', near: 1, act: 'Pass it' },
    reaction: { say: 'Who is looking at them?', verb: 'adds a reaction', deal: 'shots', near: 1, w: 'face look eye watch', act: 'Pass it' },
    listen: { say: 'You only hear it. What do you see?', verb: 'imagines it', deal: 'shots', act: 'Pass it' },
    neighbor: { say: 'Find its neighbour.', verb: 'finds a neighbour', deal: 'shots', near: 1, act: 'Pass it' },
    carry: { say: 'Keep going.', verb: 'carries on', deal: 'shots', near: 1, act: 'Pass it' },
    place: { say: 'Where does it go in the film?', verb: 'places it', deal: 'place', act: 'Put it here' },
    attach: { say: 'Find a shot to join it.', verb: 'joins one', deal: 'shots', near: 1, act: 'Pass it' },
    bond: { say: 'How do they meet?', verb: 'bonds them', deal: 'bonds', act: 'Pass it' } };
  const OPS = ['hold', 'repeat', 'reverse', 'early', 'soon', 'silence', 'interrupt'];
  const OPN = { hold: 'HOLD', repeat: 'REPEAT', reverse: 'REVERSE', early: 'ENTER EARLY', soon: 'CUT TOO SOON', silence: 'SILENCE', interrupt: 'INTERRUPT' };
  const BONDS = ['cut', 'rhyme', 'contrast', 'merge', 'overlay', 'transform'], BCOL = { cut: '#e8e8e8', rhyme: '#ffc93c', contrast: '#ff5e5e', merge: '#3aa0ff', overlay: '#b06bff', transform: '#32d17c' };
  const FAM = { voice: '#ff7a3d', music: '#3aa0ff', field: '#32d17c' };
  const I = {
    eye: '<svg viewBox="0 0 40 40"><path d="M3 20 Q20 4 37 20 Q20 36 3 20Z" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="20" cy="20" r="6" fill="currentColor"/></svg>',
    ear: '<svg viewBox="0 0 40 40"><path d="M13 16 Q13 5 22 5 Q31 5 31 15 Q31 21 26 25 Q23 28 23 32 Q23 37 18 37 Q14 37 13 33" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/><path d="M19 17 Q19 11 23 11 Q26 11 26 15" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    wave: '<svg viewBox="0 0 40 40"><path d="M4 20 H8 M10 14 V26 M14 9 V31 M18 15 V25 M22 6 V34 M26 12 V28 M30 16 V24 M34 19 V21" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>',
    time: '<svg viewBox="0 0 40 40"><circle cx="20" cy="21" r="14" fill="none" stroke="currentColor" stroke-width="3"/><path d="M20 12 V21 L27 25" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    pass: '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" fill="none" stroke="currentColor" stroke-width="3"/><path d="M11 20 H28 M22 13 L29 20 L22 27" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    star: '<svg viewBox="0 0 40 40"><path d="M20 3 L24.5 14.5 L37 15 L27 23 L30.5 35.5 L20 28.5 L9.5 35.5 L13 23 L3 15 L15.5 14.5Z" fill="currentColor"/></svg>',
    mic: '<svg viewBox="0 0 40 40"><rect x="14" y="4" width="12" height="20" rx="6" fill="currentColor"/><path d="M9 18 Q9 30 20 30 Q31 30 31 18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M20 30 V36 M13 36 H27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    far: '<svg viewBox="0 0 40 40"><path d="M6 20 H30 M22 11 L31 20 L22 29" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    play: '<svg viewBox="0 0 40 40"><path d="M12 7 L33 20 L12 33Z" fill="currentColor"/></svg>',
    combine: '<svg viewBox="0 0 40 40"><circle cx="9" cy="20" r="5" fill="#3aa0ff"/><circle cx="31" cy="20" r="5" fill="#32d17c"/><circle cx="20" cy="8" r="5" fill="#ff4fa3"/><circle cx="20" cy="32" r="5" fill="#ffc93c"/><path d="M14 20 H26 M20 13 V27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    rec: '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="11" fill="#ff3b3b"/></svg>',
    branch: '<svg viewBox="0 0 40 40"><path d="M12 6 V34 M12 22 Q12 14 28 12" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/><circle cx="28" cy="12" r="4" fill="currentColor"/></svg>',
    left: '<svg viewBox="0 0 40 40"><path d="M25 7 L12 20 L25 33" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    right: '<svg viewBox="0 0 40 40"><path d="M15 7 L28 20 L15 33" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    note: '<svg viewBox="0 0 40 40"><path d="M15 29 V8 L33 4 V25" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="11" cy="29" r="5" fill="currentColor"/><circle cx="29" cy="25" r="5" fill="currentColor"/></svg>',
    mouth: '<svg viewBox="0 0 40 40"><path d="M4 20 Q20 6 36 20 Q20 34 4 20Z" fill="currentColor"/><path d="M8 20 Q20 25 32 20" stroke="#111" stroke-width="2.5" fill="none"/></svg>',
    hold: '<svg viewBox="0 0 40 40"><rect x="10" y="8" width="7" height="24" rx="2" fill="currentColor"/><rect x="23" y="8" width="7" height="24" rx="2" fill="currentColor"/></svg>',
    repeat: '<svg viewBox="0 0 40 40"><path d="M8 18 Q8 9 18 9 H30 L26 5 M30 9 L26 13 M32 22 Q32 31 22 31 H10 L14 35 M10 31 L14 27" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    reverse: '<svg viewBox="0 0 40 40"><path d="M30 8 L12 20 L30 32Z" fill="currentColor"/><path d="M10 8 V32" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/></svg>',
    early: '<svg viewBox="0 0 40 40"><path d="M3 20 Q6 12 9 20 T15 20" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><rect x="19" y="10" width="18" height="20" rx="2" fill="currentColor"/></svg>',
    soon: '<svg viewBox="0 0 40 40"><rect x="4" y="10" width="14" height="20" rx="2" fill="currentColor"/><path d="M22 6 V34" stroke="currentColor" stroke-width="3.5" stroke-dasharray="4 3"/></svg>',
    silence: '<svg viewBox="0 0 40 40"><path d="M6 15 H12 L20 8 V32 L12 25 H6Z" fill="currentColor"/><path d="M26 14 L36 26 M36 14 L26 26" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/></svg>',
    interrupt: '<svg viewBox="0 0 40 40"><rect x="3" y="10" width="13" height="20" rx="2" fill="currentColor"/><rect x="24" y="10" width="13" height="20" rx="2" fill="currentColor"/><rect x="16" y="6" width="8" height="28" rx="1" fill="#ff4fa3"/></svg>' };
  const famIcon = f => f === 'music' ? I.note : f === 'voice' ? I.mouth : I.wave;
  const stepIcon = s => { const d = (STEP[s] || {}).deal; return d === 'sounds' ? I.wave : d === 'ops' ? I.time : d === 'bonds' ? I.combine : d === 'place' ? I.pass : d === 'figs' ? I.branch : d === 'backlot' ? I.star : I.eye; };

  // ---- one piece of film on a layer: its picture (or a detail of it), a sound, a change of time
  function run(o, L, h = {}) {
    let dead = false; const tm = [], later = (f, s) => tm.push(setTimeout(() => { if (!dead) f(); }, s * 1000));
    const { V, A, X, B } = L, S = o.snd, op = o.op, base = o.len || 4.2;
    const sin = S ? S.t0 || 0 : 0;
    const vgo = (t, play = true) => { try { V.currentTime = t; } catch (e) { } if (play) V.play().catch(() => { }); };
    const ago = t => { if (!S) return; try { A.currentTime = sin + t; } catch (e) { } A.play().catch(() => { }); };
    if (V.dataset.u !== o.v) { V.dataset.u = o.v; V.src = o.v; } V.muted = !!S || !!o.mute; V.volume = .6;
    if (o.box) { const [x, y, w, hh] = o.box, s = Math.max(1, Math.min(3.2, .85 / Math.max(w, hh, .05))); V.style.transformOrigin = `${(x + w / 2) * 100}% ${(y + hh / 2) * 100}%`; V.style.transform = `scale(${s})`; } else V.style.transform = '';
    if (S) { if (A.dataset.u !== S.u) { A.dataset.u = S.u; A.src = S.u; } A.volume = .9; }
    X.style.opacity = 0; B.style.opacity = 0; let T = base;
    const start = () => {
      if (op === 'hold') { vgo(0); ago(0); later(() => V.pause(), 1.1); }
      else if (op === 'repeat') { [0, 1.15, 2.3].forEach(t => later(() => { vgo(0); ago(0); }, t)); T = 3.5; }
      else if (op === 'reverse') { vgo(3, false); V.pause(); ago(0); let x = 3; const iv = setInterval(() => { if (dead || x <= 0) return clearInterval(iv); x -= .05; try { V.currentTime = Math.max(0, x); } catch (e) { } }, 50); tm.push(iv); }
      else if (op === 'soon') { vgo(0); ago(0); T = 1.3; }
      else if (op === 'silence') { vgo(0); ago(0); later(() => A.pause(), 1.6); }
      else if (op === 'interrupt') { vgo(0); ago(0); later(() => { X.src = o.flash || ''; X.style.opacity = 1; A.pause(); V.pause(); }, 1.8); later(() => { X.style.opacity = 0; vgo(2.4); ago(2.4); }, 2.4); T = base + .6; }
      else { vgo(0); ago(0); }
      later(() => { h.done && h.done(); }, T); later(() => stop(), T + 2.5); };
    if (op === 'early') { B.style.opacity = 1; ago(0); later(() => { B.style.opacity = 0; start(); }, 1.4); } else start();
    function stop() { dead = true; tm.forEach(t => { clearTimeout(t); clearInterval(t); }); try { A.pause(); } catch (e) { } try { V.pause(); } catch (e) { } X.style.opacity = 0; B.style.opacity = 0; }
    return stop;
  }

  function host(H) {
    const $ = s => document.querySelector(s), P = H.P, ARC = window.SH;
    H.show(null); H.slate(''); H.cap(''); $('#host').classList.add('cin');
    let root$ = $('#cinv'); if (!root$) { root$ = document.createElement('div'); root$.id = 'cinv'; $('#vids').after(root$); } root$.hidden = false;
    root$.innerHTML = `<div class="chead" id="cHead"></div><div class="cboard" id="cBoard"></div><div class="csolo" id="cSolo" hidden>${[0, 1].map(i => `<div class="cly" data-l="${i}"><video playsinline preload="auto"></video><div class="cb"></div><img class="cx" alt=""></div>`).join('')}<div class="cflash" id="cFlash"></div><div class="cauth" id="cAuth"></div></div><div class="cfoot" id="cFoot"></div>`;
    const lays = [...root$.querySelectorAll('.cly')].map((el, i) => ({ el, V: el.querySelector('video'), A: H.AP[i], X: el.querySelector('.cx'), B: el.querySelector('.cb') }));
    const C = { ready: false, why: 'opening the archive', round: 0, mode: null, phase: 'load', step: 0, order: [], chains: [], films: [{ id: 0, name: 'The film', pieces: [] }], cur: 0, playing: null, at: -1, votes: {}, keeps: {}, t0: performance.now(), molecule: null, surf: {} };
    const ST = { att: [], cast: {}, motifs: [], debts: [], backlot: [], mine: {}, style: {}, log: [] };
    const hands = {}; let LIB = null, X = null, XV = null, XI = null, R = null, SK = null, SND = [], TR = null, TW = null, SAM = null, FE = null, EXT = '.webp', byId = null, nid = 1, stopPlay = [], advT = 0;
    window.__cin = { C, ST, hands, begin: m => begin(m) };
    const players = () => H.players.filter(p => !p.house && (p.conn || p.local));
    Promise.all([ARC.load({ light: true }), fetch('party/lexicon.json').then(r => r.json()), fetch('party/lexicon.bin').then(r => r.arrayBuffer()), fetch('pictures/rushes.json').then(r => r.json()), fetch('tools/sound-kinds.json').then(r => r.json()),
      fetch('markov/sam.json').then(r => r.json()), fetch('markov/sam-emb.bin').then(r => r.arrayBuffer()), new Promise(r => { const i = new Image(); i.onload = () => r('.webp'); i.onerror = () => r('.png'); i.src = 'seg/0046aa70-365f-5128-88eb-90cfe9e075e4/0.webp'; })])
      .then(([d, xj, xb, rj, sk, sj, sb, ext]) => { LIB = d.LIB; X = xj; XV = new Int8Array(xb); XI = new Map(X.words.map((w, i) => [w, i])); R = rj; SK = sk.clips; SAM = sj; FE = new Int8Array(sb); EXT = ext;
        byId = new Map(LIB.shots.map((s, i) => [s.id, i])); for (const id in SK) { const k = byId.get(id), kind = SK[id][0]; if (k != null && /mixed|speech|music|noise/.test(kind)) SND.push(k); }
        C.ready = true; C.why = ''; begin((H.opt && MODES[H.opt.start] && H.opt.start) || 'pass'); })
      .catch(e => { C.why = 'the archive did not load: ' + e.message; draw(); });
    fetch('odyssey/transcripts.json').then(r => r.json()).then(t => TR = t).catch(() => { });
    // ---- vectors and the steering
    const norm = v => { let n = 0; for (let j = 0; j < v.length; j++) n += v[j] * v[j]; n = Math.sqrt(n) || 1; for (let j = 0; j < v.length; j++) v[j] /= n; return v; };
    const vecK = k => { const o = new Float32Array(512), r = k * 512; for (let j = 0; j < 512; j++) o[j] = LIB.q[r + j]; return norm(o); };
    const vecF = f => { const o = new Float32Array(512), r = f * 512; for (let j = 0; j < 512; j++) o[j] = FE[r + j]; return norm(o); };
    const vecW = t => { const ws = words(t).map(stem).filter(w => XI.has(w)); if (!ws.length) return null; const v = new Float32Array(512); ws.forEach(w => { const i = XI.get(w), f = X.idf[i]; for (let j = 0; j < 512; j++) v[j] += XV[i * 512 + j] * f; }); return norm(v); };
    const add = (o, v, w) => { if (v) for (let j = 0; j < 512; j++) o[j] += v[j] * w; return o; };
    const dotK = (v, k) => { let a = 0; const r = k * 512; for (let j = 0; j < 512; j++) a += v[j] * LIB.q[r + j]; return a; };
    const steer = () => { const v = new Float32Array(512); ST.att.forEach(a => add(v, a.v, a.w)); return v; };
    const empty = v => !v || !v.some(x => x);
    const isArc = k => LIB.shots[k] && LIB.shots[k].kind !== 'presence';
    const shot = k => LIB.shots[k], nameOf = id => (P(id) || {}).name || 'the archive', colOf = id => P(id) ? col(P(id).av) : HOUSE;
    const label = k => { const s = shot(k); return s ? (s.title || '').replace(/\s*\(.*$/, '').slice(0, 34) + (s.year ? ' · ' + s.year : '') : ''; };
    const softPick = (arr, n, T = 12) => { const out = [], pool = arr.slice(); while (out.length < n && pool.length) { let r = rnd() * pool.reduce((a, _, i) => a + Math.exp(-i / T), 0), i = 0; for (; i < pool.length; i++) { r -= Math.exp(-i / T); if (r <= 0) break; } out.push(pool.splice(Math.min(i, pool.length - 1), 1)[0]); } return out; };
    const film = () => C.films.find(f => f.id === C.cur) || C.films[0];
    const allPieces = () => C.films.flatMap(f => f.pieces);
    // ---- a round begins: the card, the chains, the hands
    function begin(mode) { stopIt(); H.crowdShow && H.crowdShow(null); C.round++; C.mode = mode; C.step = 0; C.votes = {}; C.keeps = {}; C.t0 = performance.now(); C.order = players().map(p => p.id); if (!C.order.length) C.order = ['__house'];
      const M = MODES[mode]; C.order.forEach(id => { hands[id] = { depth: 0, n: 0 }; }); C.keeps = {}; C.pending = [];
      if (M.kind === 'chain') { C.phase = 'steps'; C.chains = C.order.map((id, i) => ({ id: nid++, slot: i, shots: [], pos: null, done: {}, who: M.steps.map((_, s) => C.order[(i + s) % C.order.length]) })); C.order.forEach(id => deal(id)); }
      else if (M.kind === 'surf') { C.phase = 'surf'; C.chains = []; C.surf = {}; C.order.forEach((id, i) => { const k = seedShot(i); C.surf[id] = { at: k, trail: [{ k, t: performance.now() }], rec: null, mom: vecK(k) }; ring(id); }); }
      speak(M.name + '. ' + (M.kind === 'chain' ? STEP[M.steps[0]].say : 'Wander the archive. Record somewhere strange.')); draw(); }
    function seedShot(i) { const v = steer(); if (empty(v)) { let k; do { k = Math.floor(rnd() * LIB.n); } while (!isArc(k)); return k; } const s = LIB.sims(v), idx = []; for (let j = 0; j < s.length; j++) if (isArc(j)) idx.push(j); idx.sort((a, b) => s[b] - s[a]); return idx[i * 7 + Math.floor(rnd() * 20)]; }
    const N = () => C.order.length, chainOf = (id, s = C.step) => { const i = C.order.indexOf(id); if (i < 0) return null; return C.chains[((i - s) % N() + N()) % N()]; };
    const stepName = () => MODES[C.mode].steps[C.step];
    const last = c => c.shots[c.shots.length - 1];
    // ---- what a hand holds
    function deal(id) { if (!C.ready) return; const h = hands[id] = hands[id] || { depth: 0, n: 0 }, M = MODES[C.mode];
      if (C.phase !== 'steps') return; const c = chainOf(id), st = STEP[stepName()]; if (!c) return; h.kind = st.deal;
      if (st.deal === 'shots') { const near = st.near && c.shots.length ? (stepName() === 'neighbor' && c.shots[0].fig != null ? { fig: c.shots[0].fig } : { near: stepName() === 'entrance' ? c.shots[0].k : last(c).k }) : {}; h.items = dealShots(id, { ...near, w: st.w }, h); }
      else if (st.deal === 'sounds') h.discs = dealSounds(id, last(c).k, h, st);
      else if (st.deal === 'ops') h.ops = dealOps(id);
      else if (st.deal === 'figs') h.figs = dealFigs(id, h);
      else if (st.deal === 'backlot') h.items = dealBacklot(id);
      else if (st.deal === 'bonds') h.bonds = BONDS.slice();
      else if (st.deal === 'place') h.items = null; }
    function dealShots(id, o, h) { const used = new Set(allPieces().map(p => p.k).concat(C.chains.flatMap(c => c.shots.map(s => s.k))));
      const gold = (ST.mine[id] || []).filter(x => !x.spent).map(x => x.p.k).filter(k => !used.has(k)).slice(0, 2);
      let v = steer(); add(v, vecW(o.w || ''), .6); if (h.q) add(v, h.q, 2.4); if (o.near != null) add(v, vecK(o.near), 1.4); if (o.fig != null) add(v, vecF(o.fig), 2);
      let idx; if (empty(v)) idx = Array.from({ length: 300 }, () => Math.floor(rnd() * LIB.n)).filter(k => isArc(k) && !used.has(k));
      else { const s = LIB.sims(v); idx = []; for (let i = 0; i < s.length; i++) if (isArc(i) && !used.has(i)) idx.push(i); idx.sort((a, b) => s[b] - s[a]); idx = idx.slice(0, 700); }
      const d = h.depth || 0, win = idx.slice(d * 36, d * 36 + 90), wild = Array.from({ length: 8 }, () => Math.floor(rnd() * LIB.n)).filter(k => isArc(k) && !used.has(k)).slice(0, 2);
      return [...new Set([...gold, ...softPick(win.length ? win : idx, 7), ...wild])].slice(0, 9).map(k => ({ k, gold: gold.includes(k) })); }
    function dealBacklot(id) { const mine = (ST.mine[id] || []).filter(x => !x.spent).map(x => ({ k: x.p.k, gold: true, from: x.p, prov: 'saved by ' + nameOf(id) + ' · round ' + x.round }));
      const room = ST.backlot.filter(x => !x.spent).map(x => ({ k: x.p.k, from: x.p, prov: (x.rej ? 'rejected' : 'lost') + ' · round ' + x.round }));
      const others = Object.entries(ST.mine).filter(([o]) => o !== id).flatMap(([o, l]) => l.filter(x => !x.spent).map(x => ({ k: x.p.k, from: x.p, prov: 'saved by ' + nameOf(o) + ' · round ' + x.round })));
      const out = [...mine, ...room, ...others]; return out.length ? out.slice(0, 9) : dealShots(id, {}, hands[id]); }
    function dealFigs(id, h) { let v = steer(); if (h.q) add(v, h.q, 2.4); film().pieces.slice(-4).forEach(p => add(v, vecK(p.k), .5));
      const n = SAM.figs.length, s = new Float32Array(n); const zero = empty(v); for (let i = 0; i < n; i++) { if (zero) { s[i] = rnd(); continue; } let a = 0; const r = i * 512; for (let j = 0; j < 512; j++) a += v[j] * FE[r + j]; s[i] = a; }
      const idx = Array.from(s.keys()).filter(i => byId.has(SAM.figs[i].shot)).sort((a, b) => s[b] - s[a]), d = h.depth || 0, seen = new Set(), out = [];
      for (const f of softPick(idx.slice(d * 30, d * 30 + 120), 40, 20)) { if (seen.has(SAM.figs[f].shot)) continue; seen.add(SAM.figs[f].shot); out.push(f); if (out.length >= 9) break; } return out; }
    function sndOf(kind, a) { if (kind === 'clip') { const s = shot(a), K = SK[s.id] || ['noise']; return { kind, ref: a, u: s.video, t0: 0, t1: Math.min(5, s.dur || 5), th: thumbOf(s.video), fam: /music/.test(K[0]) ? 'music' : /speech|mixed/.test(K[0]) ? 'voice' : 'field', label: label(a) }; }
      if (kind === 'line' || kind === 'funny') { const l = R[kind === 'line' ? 'lines' : 'funny'][a], u = R.r2 + R.P[l.v[0]] + '/clips/' + l.v[1] + '.mp4'; return { kind, ref: a, u, t0: l.t0, t1: l.t1, th: thumbOf(u), fam: 'voice', x: l.x, label: l.f }; }
      if (kind === 'music') { const m = R.music[a], u = R.r2 + R.P[m.v[0]] + '/clips/' + m.v[1] + '.mp4', t0 = Math.min(4, Math.max(0, (m.d || 20) - 30)); return { kind, ref: a, u, t0, t1: t0 + 6, th: thumbOf(u), fam: 'music', label: m.f }; }
      if (kind === 'found') { const t = TR[a.c]; return { kind, ref: a, u: t.video, t0: a.t0, t1: a.t1, th: thumbOf(t.video), fam: 'voice', x: a.x, label: t.title }; } }
    const keyOf = s => s.kind + ':' + (typeof s.ref === 'object' ? s.ref.c + '@' + s.ref.t0 : s.ref);
    function found(text) { if (!TR) return []; if (!TW) { TW = new Map(); for (const id in TR) { const w = TR[id].words; for (let i = 0; i < w.length; i++) { const k = stem(String(w[i][0]).toLowerCase().replace(/[^a-z]/g, '')); if (k.length < 4 || STOP.has(k)) continue; let l = TW.get(k); if (!l) TW.set(k, l = []); if (l.length < 30) l.push([id, i]); } } }
      const out = []; words(text).map(stem).forEach(k => (TW.get(k) || []).forEach(([id, i]) => { const w = TR[id].words, a = Math.max(0, i - 1), b = Math.min(w.length - 1, i + 2), t1 = w[b + 1] ? w[b + 1][1] : w[b][1] + .5; if (t1 - w[a][1] < 4) out.push({ c: id, t0: Math.max(0, w[a][1] - .05), t1: t1 + .05, x: w.slice(a, b + 1).map(x => x[0]).join(' ') }); }));
      return shuffle(out).slice(0, 3); }
    function dealSounds(id, k, h, st) { const vi = vecK(k), v = add(new Float32Array(vi), steer(), .3), out = [];
      ST.motifs.forEach(m => { let a = 0; const mv = vecK(m.k); for (let j = 0; j < 512; j++) a += mv[j] * vi[j]; if (a > .8 || shot(m.k).src === shot(k).src) out.push({ ...m.snd, motif: 1 }); });
      (ST.mine[id] || []).filter(x => !x.spent && x.p.snd).slice(0, 1).forEach(x => out.push({ ...x.p.snd, gold: 1 }));
      if (h.text) { const ws = words(h.text), L = []; ['lines', 'funny'].forEach(kind => R[kind].forEach((l, i) => { const lw = l.x.toLowerCase(), sc = ws.filter(w => lw.includes(w)).length; if (sc) L.push([sc, kind === 'lines' ? 'line' : 'funny', i]); }));
        L.sort((a, b) => b[0] - a[0]).slice(0, 3).forEach(([, kk, i]) => out.push(sndOf(kk, i))); found(h.text).forEach(f => out.push(sndOf('found', f))); }
      if (st.voice) { shuffle(R.lines.map((_, i) => i)).slice(0, 3).forEach(i => out.push(sndOf('line', i))); }
      const qv = h.q ? add(new Float32Array(v), h.q, 2) : v, ranked = SND.slice().sort((a, b) => dotK(qv, b) - dotK(qv, a)), d = h.depth || 0, want = st.wrong && !h.q ? ranked.slice().reverse() : ranked;
      softPick(want.slice(d * 30, d * 30 + 80), st.voice ? 2 : 4, 10).forEach(kk => out.push(sndOf('clip', kk)));
      out.push(sndOf('line', Math.floor(rnd() * R.lines.length))); out.push(sndOf('music', Math.floor(rnd() * R.music.length)));
      const seen = new Set(); return out.filter(s => { const kk = keyOf(s); if (seen.has(kk)) return false; seen.add(kk); return true; }).slice(0, 9); }
    function dealOps(id) { const w = OPS.map(o => 1 + (ST.style[o] || 0) * .6), pool = OPS.slice(), out = []; while (out.length < 4) { let r = rnd() * pool.reduce((a, o) => a + w[OPS.indexOf(o)], 0), i = 0; for (; i < pool.length; i++) { r -= w[OPS.indexOf(pool[i])]; if (r <= 0) break; } out.push(pool.splice(Math.min(i, pool.length - 1), 1)[0]); } return out; }
    // ---- surfing: every move changes your next neighbourhood
    function ring(id) { const s = C.surf[id], h = hands[id]; const v = add(add(new Float32Array(vecK(s.at)), s.mom, .7), steer(), .25); if (h.q) add(v, h.q, 2.2); const sims = LIB.sims(v), seen = new Set([shot(s.at).src]), idx = []; for (let i = 0; i < sims.length; i++) if (isArc(i)) idx.push(i); idx.sort((a, b) => sims[b] - sims[a]);
      const d = h.depth || 0, out = []; for (const k of softPick(idx.slice(1 + d * 50, 1 + d * 50 + 150), 60, 18)) { if (seen.has(shot(k).src)) continue; seen.add(shot(k).src); out.push(k); if (out.length >= 6) break; }
      let w; do { w = Math.floor(rnd() * LIB.n); } while (!isArc(w)); out.push(w); s.ring = out; }
    function surf(p, k) { const s = C.surf[p.id]; if (!s || !s.ring.includes(k)) return; s.trail.push({ k, t: performance.now() }); if (s.trail.length > 12) s.trail.shift(); s.at = k; for (let j = 0; j < 512; j++) s.mom[j] = s.mom[j] * .6 + vecK(k)[j] * .4; hands[p.id].depth = 0; hands[p.id].q = null; ring(p.id); }
    function rec(p) { const s = C.surf[p.id]; if (!s) return; const tr = s.trail.slice(-4); s.rec = tr.map((x, i) => ({ k: x.k, len: Math.max(1.2, Math.min(3, ((tr[i + 1] ? tr[i + 1].t : performance.now()) - x.t) / 1000)) })); H.act(p.id, 'cheer', 1600); }
    // ---- moves
    const piece = o => ({ id: nid++, round: C.round, mode: C.mode, r: {}, ...o });
    function onMsg(p, m) { if (!C.ready) return; const h = hands[p.id] = hands[p.id] || { depth: 0, n: 0 };
      if (m.t === 'heard') { const t = String(m.part || '').slice(-80); if (t) H.say(p.id, t, 2200); return; }
      if (m.t === 'say') { (async () => { let text = String(m.text || '').trim(); if (!text && m.a && H.ears) text = await H.ears.read(m.a, m.mime).catch(() => ''); h.text = text; h.heard = text.slice(0, 60); h.miss = !text; h.n++; h.q = vecW(text); h.depth = 0; if (text) H.say(p.id, text.slice(0, 60), 2600); if (C.phase === 'surf') ring(p.id); else deal(p.id); H.broadcast(); drawBoard(); })(); return; }
      if (m.t === 'far') { h.depth = (h.depth || 0) + 1; h.n++; if (C.phase === 'surf') ring(p.id); else deal(p.id); H.broadcast(); return; }
      if (m.t === 'surf' && C.phase === 'surf') { surf(p, +m.k); drawBoard(); H.broadcast(); return; }
      if (m.t === 'rec' && C.phase === 'surf') { rec(p); if (C.order.every(id => C.surf[id] && C.surf[id].rec)) later(endSurf, 900); draw(); return; }
      if (m.t === 'back' && C.phase === 'surf') { const s = C.surf[p.id]; if (s && s.trail.length > 1) { s.trail.pop(); s.at = s.trail[s.trail.length - 1].k; ring(p.id); } H.broadcast(); drawBoard(); return; }
      if (m.t === 'pass' && C.phase === 'steps') return pass(p, m);
      if (m.t === 'next' && C.phase === 'between') { begin(C.nextMode); return; }
      if (m.t === 'vote' && C.phase === 'vote') { C.votes[p.id] = m.v; H.act(p.id, 'hop', 820); if (C.order.filter(id => P(id)).every(id => C.votes[id] != null)) later(endVote, 900); draw(); return; }
      if (m.t === 'keep') { const cur = C.playing ? C.playing[C.at] : null; if (!cur) return; C.keeps[p.id] = cur.id; H.act(p.id, 'cheer', 1600); H.logLine(chip(p.id) + ' kept this one'); H.broadcast(); return; }
      if (m.t === 'play') { if (C.playing) { stopIt(); draw(); } else playList(film().pieces); return; } }
    function pass(p, m) { const c = chainOf(p.id), sn = stepName(), st = STEP[sn], h = hands[p.id]; if (!c || c.done[C.step]) return;
      if (st.deal === 'shots' || st.deal === 'backlot') { const it = (h.items || []).find(x => x.k === +m.key); if (!it) return; const s = { k: it.k, by: p.id }; if (it.from && it.from.snd && sn === 'rescue') s.snd = it.from.snd;
        if (it.gold || it.from) spend(it.k);
        if (sn === 'entrance') c.shots.unshift(s); else if (sn === 'repair') { s.snd = c.shots[0].snd; c.shots[0].snd = null; c.shots.splice(1, 0, s); } else c.shots.push(s); }
      else if (st.deal === 'sounds') { const s = (h.discs || []).find(d => keyOf(d) === m.key); if (!s) return; const t = last(c); t.snd = { ...s, by: p.id }; delete t.snd.motif; delete t.snd.gold; }
      else if (st.deal === 'ops') { if (!(h.ops || []).includes(m.key)) return; const t = last(c); t.op = m.key; t.opBy = p.id; t.len = Math.max(1, Math.min(6, +m.len || 4.2)); }
      else if (st.deal === 'figs') { const f = +m.key, F = SAM.figs[f]; if (!F || !(h.figs || []).includes(f)) return; c.shots.push({ k: byId.get(F.shot), by: p.id, fig: f, box: F.box, desc: F.desc }); }
      else if (st.deal === 'bonds') { if (!BONDS.includes(m.key)) return; const t = last(c); t.tr = m.key; t.trBy = p.id; }
      else if (st.deal === 'place') { const n = film().pieces.length; c.pos = Math.max(0, Math.min(n, +m.key)); c.posBy = p.id; }
      c.done[C.step] = p.id; H.act(p.id, 'hop', 820);
      if (C.chains.every(x => x.done[C.step])) { clearTimeout(advT); advT = setTimeout(nextStep, 1200); } draw(); }
    function spend(k) { Object.values(ST.mine).forEach(l => l.forEach(x => { if (x.p.k === k) x.spent = C.round; })); ST.backlot.forEach(x => { if (x.p.k === k) x.spent = C.round; }); }
    // the house does what nobody did, in plain sight
    function fill() { if (C.phase === 'steps') { C.chains.forEach(c => { if (c.done[C.step]) return; const id = c.who[C.step], h = hands[id] || (hands[id] = { depth: 0, n: 0 }); const sn = stepName(), st = STEP[sn];
          if (st.deal === 'shots' || st.deal === 'backlot') { const k = (h.items || dealShots(id, {}, h))[0].k; if (sn === 'entrance') c.shots.unshift({ k, by: null }); else c.shots.push({ k, by: null }); }
          else if (st.deal === 'sounds' && c.shots.length) { last(c).snd = { ...dealSounds(id, last(c).k, h, st)[0], by: null }; }
          else if (st.deal === 'ops' && c.shots.length && rnd() < .6) { last(c).op = pick(OPS); last(c).opBy = null; }
          else if (st.deal === 'bonds' && c.shots.length) last(c).tr = pick(BONDS);
          else if (st.deal === 'figs') { const f = (h.figs || dealFigs(id, h))[0], F = SAM.figs[f]; c.shots.push({ k: byId.get(F.shot), by: null, fig: f, box: F.box, desc: F.desc }); }
          c.done[C.step] = c.done[C.step] || '__house'; }); nextStep(); }
      else if (C.phase === 'surf') { C.order.forEach(id => { if (C.surf[id] && !C.surf[id].rec) rec({ id }); }); endSurf(); }
      else if (C.phase === 'vote') endVote(); else if (C.phase === 'between') begin(C.nextMode); }
    function nextStep() { if (C.phase !== 'steps') return; const M = MODES[C.mode]; C.step++;
      if (C.step >= M.steps.length) { const out = []; C.chains.forEach(c => { if (!c.shots.length) return;
          if (M.branch) { const head = c.shots[0], f = { id: nid++, name: (head.desc && head.desc.split(' ').length > 1 ? head.desc : 'the ' + (head.desc || 'detail') + ' from ' + label(head.k)).slice(0, 60), pieces: [], from: C.cur, by: head.by }; c.shots.forEach(s => f.pieces.push(piece({ ...s }))); C.films.push(f); ST.log.unshift({ html: `${chip(head.by)} BREAKAWAY: <b>${esc(f.name)}</b> became a film of its own` }); out.push(...f.pieces); }
          else if (C.mode === 'backlot' && c.pos != null) { const ps = c.shots.map(s => piece({ ...s, placed: c.pos })); out.push(...ps); }
          else c.shots.forEach(s => out.push(piece({ ...s, chain: c.id }))); });
        if (M.vote) { C.phase = 'play'; C.pending = out; playList(out, () => { C.phase = 'vote'; speak('Who is the hero?'); draw(); }); draw(); return; }
        finishRound(out); return; }
      C.order.forEach(id => { hands[id].depth = 0; hands[id].q = null; hands[id].text = ''; hands[id].heard = ''; deal(id); }); speak(STEP[stepName()].say); draw(); }
    function endSurf() { if (C.phase !== 'surf') return; const strips = C.order.map(id => (C.surf[id] && C.surf[id].rec || []).map(x => piece({ k: x.k, len: x.len, by: id, tr: 'cut' }))), out = [];
      for (let i = 0; strips.some(s => s[i]); i++) strips.forEach(s => s[i] && out.push(s[i]));
      C.order.forEach(id => (C.surf[id] ? C.surf[id].trail : []).forEach(x => ST.att.push({ v: vecK(x.k), w: .18, decay: .6, k: x.k, by: id })));
      finishRound(out); }
    // ---- a round's pieces join the film, play, and the room keeps or rejects
    function finishRound(out) { stopIt(); const F = film();
      out.forEach(p => { if (p.placed != null) { F.pieces.splice(Math.min(p.placed, F.pieces.length), 0, p); p.placed = null; } else if (!C.films.some(f => f !== F && f.pieces.includes(p))) F.pieces.push(p); });
      C.pending = out; C.phase = 'play'; playList(out, () => settle()); draw(); }
    function endVote() { if (C.phase !== 'vote') return; const t = {}; Object.values(C.votes).forEach(v => t[v] = (t[v] || 0) + 1); const best = C.chains.slice().sort((a, b) => (t[b.id] || 0) - (t[a.id] || 0))[0];
      const hero = best && best.shots.find(s => s.by === best.who[0]) || (best && best.shots[0]); if (hero) { ST.cast.hero = { k: hero.k, by: hero.by, round: C.round }; ST.att = ST.att.filter(a => a.role !== 'hero'); ST.att.unshift({ v: vecK(hero.k), w: 1.6, decay: .88, k: hero.k, by: hero.by, role: 'hero' }); ST.log.unshift({ html: `${chip(hero.by)} CAST: <b>${esc(label(hero.k))}</b> is the hero` }); }
      const F = film(); (C.pending || []).forEach(p => F.pieces.push(p)); C.votes = {}; settle(); }
    function settle() { const sc = p => (p.r.rose || 0) + 2 * (p.r.bravo || 0) - (p.r.tomato || 0) - (p.r.cut || 0);
      const out = C.pending || []; out.forEach(p => { if ((p.r.tomato || 0) + (p.r.cut || 0) > (p.r.rose || 0) + (p.r.bravo || 0) && (p.r.tomato || 0) > 0) p.rej = true; });
      Object.entries(C.keeps).forEach(([id, v]) => { const p = out.find(x => x.id === v); if (!p) return; (ST.mine[id] = ST.mine[id] || []).push({ p, round: C.round }); ST.att.push({ v: vecK(p.k), w: .7, decay: .75, k: p.k, by: id }); ST.log.unshift({ html: `${chip(id)} BACKLOT: kept <b>${esc(label(p.k))}</b>${p.rej ? ' (rejected)' : ''}` }); });
      out.filter(p => p.rej).forEach(p => { C.films.forEach(f => f.pieces = f.pieces.filter(x => x !== p)); if (!Object.values(C.keeps).includes(p.id)) ST.backlot.push({ p, round: C.round, rej: true }); ST.log.unshift({ html: `${chip(p.by)} REJECTED: <b>${esc(label(p.k))}</b> went to the backlot` }); });
      // the world remembers: the room's favourite pulls the search; surviving sounds become motifs; a cut too soon leaves a debt; cuts become style
      ST.att.forEach(a => a.w *= a.decay); ST.att = ST.att.filter(a => a.w > .06);
      out.filter(p => !p.rej).forEach(p => ST.att.push({ v: vecK(p.k), w: .4, decay: .55, k: p.k, by: p.by }));
      const best = out.filter(p => !p.rej).sort((a, b) => sc(b) - sc(a))[0]; if (best && best.snd && sc(best) > 0) { ST.motifs.unshift({ k: best.k, snd: best.snd, by: [best.by, best.snd.by] }); ST.motifs = ST.motifs.slice(0, 6); ST.log.unshift({ html: `${chip(best.by)}${chip(best.snd.by)} MOTIF: <b>${esc(label(best.k))}</b> with <b>${esc(best.snd.x || best.snd.label || best.snd.fam)}</b>` }); }
      out.forEach(p => { if (p.op === 'soon' && !p.rej) ST.debts.unshift({ k: p.k, by: p.opBy }); if (p.op) ST.style[p.op] = (ST.style[p.op] || 0) + 1; });
      ST.att.sort((a, b) => b.w - a.w); ST.att = ST.att.slice(0, 12); ST.log = ST.log.slice(0, 14);
      C.phase = 'between'; C.votes = {}; C.nextMode = nextCard(); speak('Next: ' + MODES[C.nextMode].name); draw(); }
    const ROT = ['pass', 'spoil', 'surf', 'audition', 'phone', 'backlot', 'chem', 'away'];
    function nextCard() { const ok = m => MODES[m].need !== 'backlot' || ST.backlot.some(x => !x.spent) || Object.values(ST.mine).some(l => l.some(x => !x.spent)); let i = ROT.indexOf(C.mode); for (let n = 0; n < ROT.length; n++) { i = (i + 1) % ROT.length; if (ok(ROT[i])) return ROT[i]; } return 'pass'; }
    const later = (f, ms) => setTimeout(f, ms);
    // ---- the stand plays pieces with their transitions: cut, rhyme, contrast, merge, overlay, transform
    function res(p, list, i) { const s = shot(p.k), nx = list[i + 1] || list[0]; return { v: s.video, snd: p.snd ? { u: p.snd.u, t0: p.snd.t0, t1: p.snd.t1 } : null, op: p.op, len: p.len, box: p.box, flash: nx ? thumbOf(shot(nx.k).video) : '' }; }
    function playList(list, done) { stopIt(); if (!list.length) { done && done(); return; } const my = C.playing = list; C.at = 0; let side = 0; root$.querySelector('#cSolo').hidden = false; root$.querySelector('#cBoard').hidden = true;
      lays.forEach(l => { l.el.style.opacity = 0; l.el.style.transition = 'none'; l.el.classList.remove('ovl'); });
      const step = () => { if (C.playing !== my) return; const p = list[C.at]; if (!p) { C.playing = null; C.at = -1; stopIt(); done && done(); draw(); return; }
        const L = lays[side], O = lays[1 - side], tr = C.at ? (p.tr || 'cut') : 'cut', fl = root$.querySelector('#cFlash');
        const dur = { merge: .8, transform: 1.6, overlay: .5 }[tr] || 0; L.el.style.transition = dur ? `opacity ${dur}s, transform ${dur}s` : 'none'; L.el.style.zIndex = 2; O.el.style.zIndex = 1; L.el.classList.toggle('tf', tr === 'transform');
        if (tr === 'contrast' || tr === 'rhyme') { fl.className = 'cflash ' + tr; void fl.offsetWidth; fl.classList.add('go'); }
        stopPlay.push(run(res(p, list, C.at), L, { done: () => { C.at++; step(); } }));
        requestAnimationFrame(() => { L.el.style.opacity = tr === 'overlay' ? .55 : 1; L.el.classList.remove('tf'); if (tr !== 'overlay') { O.el.style.transition = dur ? `opacity ${dur}s` : 'none'; O.el.style.opacity = 0; } });
        side = 1 - side; root$.querySelector('#cAuth').innerHTML = authHTML(p); if (p.by) H.act(p.by, 'hop', 820); drawFoot(); H.broadcast(); };
      step(); draw(); }
    function stopIt() { stopPlay.forEach(f => f()); stopPlay = []; if (C.playing) { C.playing = null; C.at = -1; } root$.querySelector('#cSolo').hidden = true; root$.querySelector('#cBoard').hidden = false; }
    // ---- the stand
    const chip = id => `<i class="cchip" style="--c:${colOf(id)}">${id && P(id) ? esc(P(id).name[0]) : '◆'}</i>`;
    const authHTML = p => `<span style="--c:${colOf(p.by)}">${I.eye}${esc(nameOf(p.by))}</span>${p.snd ? `<span style="--c:${colOf(p.snd.by)}">${famIcon(p.snd.fam)}${esc(nameOf(p.snd.by))}</span>` : ''}${p.op ? `<span style="--c:${colOf(p.opBy)}">${I[p.op]}${OPN[p.op]}</span>` : ''}${p.tr && p.tr !== 'cut' ? `<span style="--c:${BCOL[p.tr]}">${I.combine}${p.tr.toUpperCase()}</span>` : ''}<em>${esc(MODES[p.mode] ? MODES[p.mode].name : '')} · round ${p.round}</em>`;
    const mmss = t => Math.floor(t / 60) + ':' + String(Math.floor(t % 60)).padStart(2, '0');
    function drawHead() { const M = MODES[C.mode] || { name: 'Cineosis', sub: '' }, ph = C.phase, sn = ph === 'steps' ? stepName() : '';
      root$.querySelector('#cHead').innerHTML = `<b>CINEOSIS</b><span class="m">${esc(M.name)}</span><span class="s">${ph === 'steps' ? esc(STEP[sn].say) : ph === 'surf' ? 'Wander. Press REC somewhere strange.' : ph === 'vote' ? 'Who is the hero?' : ph === 'between' ? 'Next: ' + esc(MODES[C.nextMode].name) : ph === 'play' ? 'Throw things. Tap ★ to keep one.' : esc(M.sub)}</span><span class="r">round ${C.round} · ${mmss((performance.now() - C.t0) / 1000)}</span>`; }
    function drawFoot() { const F = film(), cur = C.playing ? C.playing[C.at] : null;
      root$.querySelector('#cFoot').innerHTML = `<div class="cstrip">${F.pieces.slice(-14).map(p => `<span class="${cur === p ? 'now' : ''}" style="--c:${colOf(p.by)}"><img src="${esc(thumbOf(shot(p.k).video))}" alt=""></span>`).join('') || '<em>the film we make together starts here</em>'}</div><div class="cdots">${C.order.filter(id => P(id)).map(id => `<i style="--c:${colOf(id)}"></i>`).join('')}<small>${esc(F.name)} · ${F.pieces.length} shots</small></div>`; }
    function drawBoard() { const B = root$.querySelector('#cBoard'), ph = C.phase, M = MODES[C.mode] || {};
      if (ph === 'steps') { const hide = M.hide && C.step < M.steps.length;
        B.innerHTML = `<div class="cchains">${C.chains.map(c => { const cells = M.steps.map((s, i) => { const who = c.who[i], d = c.done[i] != null, cur = i === C.step; const sh = i === 0 || STEP[s].deal === 'shots' ? null : null;
            return `<div class="ccell ${d ? 'd' : ''} ${cur ? 'cur' : ''}" style="--c:${colOf(d && c.done[i] !== '__house' ? c.done[i] : who)}"><span class="who">${P(who) ? mini(P(who).av) : '◆'}</span><b>${stepIcon(s)}</b><small>${esc(nameOf(who))} ${esc(STEP[s].verb)}</small></div>`; }).join('<i class="arr">→</i>');
          const thumbs = c.shots.map(s => `<span style="--c:${colOf(s.by)}">${hide ? `<em>?</em>` : `<img src="${esc(thumbOf(shot(s.k).video))}" alt="" ${s.box ? `style="object-position:${(s.box[0] + s.box[2] / 2) * 100}% ${(s.box[1] + s.box[3] / 2) * 100}%;transform:scale(1.6)"` : ''}>`}${s.snd ? `<b class="sn" style="color:${FAM[s.snd.fam]}">${famIcon(s.snd.fam)}</b>` : ''}${s.op ? `<b class="op">${I[s.op]}</b>` : ''}</span>`).join('');
          return `<div class="cchain"><div class="ccells">${cells}</div><div class="cthumbs">${thumbs}${c.pos != null ? `<span class="pos">${I.pass}<small>at ${c.pos + 1}</small></span>` : ''}</div></div>`; }).join('')}</div>`; }
      else if (ph === 'surf') { const cells = []; C.order.forEach(id => { const s = C.surf[id]; if (!s) return; cells.push({ k: s.at, who: id, at: 1, rec: !!s.rec }); s.ring.forEach(k => cells.push({ k, who: id })); s.trail.slice(-5, -1).forEach(x => cells.push({ k: x.k, who: id, past: 1 })); });
        B.innerHTML = `<div class="cwall">${cells.slice(0, 32).map(c => `<span class="${c.at ? 'at' : ''} ${c.past ? 'past' : ''}" style="--c:${colOf(c.who)}"><img src="${esc(thumbOf(shot(c.k).video))}" alt="">${c.at ? `<b class="pin">${P(c.who) ? mini(P(c.who).av) : ''}</b>${c.rec ? '<i class="recd">REC</i>' : ''}` : ''}</span>`).join('')}</div>`; }
      else if (ph === 'vote') { const t = {}; Object.values(C.votes).forEach(v => t[v] = (t[v] || 0) + 1);
        B.innerHTML = `<div class="cvote">${C.chains.filter(c => c.shots.length).map(c => { const h = c.shots.find(s => s.by === c.who[0]) || c.shots[0]; return `<span style="--c:${colOf(c.who[0])}"><img src="${esc(thumbOf(shot(h.k).video))}" alt=""><b>${t[c.id] || 0}</b><small>${esc(nameOf(c.who[0]))}’s</small></span>`; }).join('')}</div>`; }
      else if (ph === 'between') { const F = film();
        B.innerHTML = `<div class="cbetween"><div class="cbs">${F.pieces.slice(-12).map(p => `<span style="--c:${colOf(p.by)}"><img src="${esc(thumbOf(shot(p.k).video))}" alt=""></span>`).join('')}</div><b>${esc(F.name)} · ${F.pieces.length} shots</b><em>next: ${esc(MODES[C.nextMode].name)}</em></div>`; }
      else B.innerHTML = C.ready ? '' : `<div class="cwait">${esc(C.why)}</div>`; }
    function drawSide() { const ph = C.phase;
      const rows = C.order.filter(id => P(id)).map(id => { let what = '', done = false;
        if (ph === 'steps') { const c = chainOf(id), s = stepName(); done = !!(c && c.done[C.step]); const from = c && c.who[(C.step + c.who.length - 1) % c.who.length]; what = `${stepIcon(s)}<small>${esc(STEP[s].verb)}${C.step ? ' · ' + esc(nameOf(from)) + '’s' : ''}</small>`; }
        else if (ph === 'surf') { const s = C.surf[id]; done = !!(s && s.rec); what = `${I.eye}<small>${s ? s.trail.length + ' channels' : ''}</small>`; }
        else if (ph === 'vote') { done = C.votes[id] != null; what = `<small>${done ? 'voted' : 'choosing'}</small>`; }
        return `<div class="cp" style="--c:${colOf(id)}"><span class="m">${mini(P(id).av)}</span><b>${esc(P(id).name)}</b><span class="i">${what}</span><span class="ok">${done ? '✓' : (hands[id] && hands[id].heard ? '“' + esc(hands[id].heard) + '”' : '')}</span></div>`; }).join('');
      const world = [ST.cast.hero && `<span class="cw"><img src="${esc(thumbOf(shot(ST.cast.hero.k).video))}" alt="">${chip(ST.cast.hero.by)}<em>hero</em></span>`].concat(ST.motifs.slice(0, 2).map(m => `<span class="cw"><img src="${esc(thumbOf(shot(m.k).video))}" alt=""><b style="color:${FAM[m.snd.fam]}">${famIcon(m.snd.fam)}</b><em>motif</em></span>`))
        .concat(ST.debts.slice(0, 1).map(d => `<span class="cw debt"><img src="${esc(thumbOf(shot(d.k).video))}" alt=""><em>unseen</em></span>`)).concat(ST.backlot.filter(x => !x.spent).slice(0, 2).map(x => `<span class="cw lost"><img src="${esc(thumbOf(shot(x.p.k).video))}" alt=""><em>backlot</em></span>`)).filter(Boolean).join('');
      const films = C.films.length > 1 ? `<div class="ph" style="margin-top:6px">Films <small>a new film can emerge anywhere</small></div><div class="cfilms">${C.films.map(f => `<div class="${f.id === C.cur ? 'on' : ''}"><b>${esc(f.name)}</b><small>${f.pieces.length}</small><button class="btn chip" data-fplay="${f.id}">▶</button>${f.id === C.cur ? '' : `<button class="btn chip" data-follow="${f.id}">follow</button>`}</div>`).join('')}</div>` : '';
      H.side(`<div class="ph">Cineosis <small>${esc(film().name)} · ${film().pieces.length} shots</small></div>
        <div class="row" style="margin-bottom:6px"><button class="btn chip" id="cPlay" ${film().pieces.length ? '' : 'disabled'}>${C.playing ? '■ stop' : '▶ play together'}</button><button class="btn chip" id="cCut" ${film().pieces.length ? '' : 'disabled'}>edit the film</button><button class="btn chip" id="cFill">${ph === 'between' ? 'next card ▸' : 'fill the rest ▸'}</button></div>
        ${C.ready ? '' : `<div class="hint">${esc(C.why)}</div>`}<div class="cps">${rows}</div>
        ${world ? `<div class="ph" style="margin-top:6px">The world <small>what the room made true</small></div><div class="cworld">${world}</div>` : ''}${films}
        ${ST.log.length ? `<div class="clog">${ST.log.slice(0, 5).map(l => `<div>${l.html}</div>`).join('')}</div>` : ''}`, 'cin');
      $('#cPlay').onclick = () => { if (C.playing) { stopIt(); draw(); } else playList(film().pieces); }; $('#cCut').onclick = () => { stopIt(); H.seed = toFilm(); H.playGame('cut'); }; $('#cFill').onclick = () => fill();
      document.querySelectorAll('[data-fplay]').forEach(b => b.onclick = () => { const f = C.films.find(x => x.id === +b.dataset.fplay); if (f) playList(f.pieces); });
      document.querySelectorAll('[data-follow]').forEach(b => b.onclick = () => { C.cur = +b.dataset.follow; ST.log.unshift({ html: `the room follows <b>${esc(film().name)}</b>` }); draw(); }); }
    function draw() { if (!C.ready) { H.slate(H.card(`<div class="big">Cineosis<small>${esc(C.why)}</small></div>`, 'night')); drawSide(); H.broadcast(); return; } H.slate(''); drawHead(); drawBoard(); drawFoot(); drawSide(); H.syncCrew(); H.broadcast(); }
    const clock = setInterval(() => { if (C.ready && root$.isConnected) drawHead(); }, 1000);
    const speak = t => { try { const u = new SpeechSynthesisUtterance(t); u.rate = .95; speechSynthesis.cancel(); speechSynthesis.speak(u); } catch (e) { } };
    function toFilm() { const F = Cut.blank('Cineosis · ' + film().name); film().pieces.forEach(p => { const s = shot(p.k), len = p.op === 'soon' ? 1.3 : p.len || 4.2;
        const c = Cut.shot(s.video, 0, Math.min(s.dur || 6, len), { d: s.dur || null, label: label(p.k), by: p.by }); if (p.tr === 'merge' || p.tr === 'transform') c.tr = 'dissolve'; if (p.tr === 'contrast') c.tr = 'dip'; F.clips.push(c);
        if (p.snd) { const sl = p.op === 'silence' ? 1.6 : Math.min(6, (p.snd.t1 || p.snd.t0 + 4.2) - p.snd.t0); F.sounds.push(p.snd.fam === 'music' ? Cut.music(c.id, p.snd.u, p.snd.t0, p.snd.t0 + sl, { vol: .8 }) : Cut.voice(c.id, p.snd.u, p.snd.t0, p.snd.t0 + sl, { text: p.snd.x || null, off: 0 })); } }); return F; }
    // ---- what a phone sees
    function stateFor(p) { const h = hands[p.id] || {}, ph = C.phase, M = MODES[C.mode] || {}, base = { phase: 'cin', noScore: true, me: p.id, ready: C.ready, round: C.round, mode: C.mode, modeName: M.name || '', modeSub: M.sub || '', ph, heard: h.heard || '', heardN: h.n || 0, miss: !!h.miss,
        crew: C.order.filter(id => P(id)).map(id => ({ id, av: P(id).av, c: colOf(id), name: P(id).name })), playing: !!C.playing };
      const sv = k => ({ k, th: thumbOf(shot(k).video), v: shot(k).video });
      if (C.playing) { const cur = C.playing[C.at]; return { ...base, kept: !!cur && C.keeps[p.id] === cur.id, now: cur ? { ...sv(cur.k), by: nameOf(cur.by), c: colOf(cur.by), snd: cur.snd ? { fam: cur.snd.fam, by: nameOf(cur.snd.by), c: colOf(cur.snd.by) } : null, op: cur.op || null } : null }; }
      if (ph === 'steps') { const c = chainOf(p.id), sn = stepName(), st = STEP[sn], hide = M.hide; if (!c) return base;
        const prev = c.who[(C.step + c.who.length - 1) % c.who.length], next = c.who[(C.step + 1) % c.who.length], t = c.shots.length ? (sn === 'entrance' ? c.shots[0] : last(c)) : null;
        const hand = t ? { ...sv(t.k), box: t.box || null, snd: t.snd ? { fam: t.snd.fam, u: t.snd.u, t0: t.snd.t0, t1: t.snd.t1, by: nameOf(t.snd.by), c: colOf(t.snd.by) } : null, op: t.op || null, by: nameOf(t.by), c: colOf(t.by), listen: hide && sn === 'listen', look: hide && sn === 'look' } : null;
        return { ...base, step: sn, say: st.say, act: st.act, kind: st.deal, from: C.step ? nameOf(prev) : '', to: C.step < M.steps.length - 1 ? nameOf(next) : '', passed: !!c.done[C.step], hand,
          items: (st.deal === 'shots' || st.deal === 'backlot') ? (h.items || []).map(x => ({ key: String(x.k), ...sv(x.k), gold: !!x.gold, prov: x.prov || '' })) : null,
          discs: st.deal === 'sounds' ? (h.discs || []).map(d => ({ key: keyOf(d), th: d.th, u: d.u, t0: d.t0, t1: d.t1, fam: d.fam, x: d.x || '', gold: !!d.gold, motif: !!d.motif })) : null,
          ops: st.deal === 'ops' ? (h.ops || []).map(o => ({ key: o, n: OPN[o] })) : null,
          figs: st.deal === 'figs' ? (h.figs || []).map(f => ({ key: String(f), png: SAM.figs[f].png.replace(/\.png$/, EXT), desc: SAM.figs[f].desc })) : null,
          bonds: st.deal === 'bonds' ? BONDS : null, pair: st.deal === 'bonds' && c.shots.length > 1 ? c.shots.slice(-2).map(x => sv(x.k)) : null,
          slots: st.deal === 'place' ? film().pieces.map(x => ({ th: thumbOf(shot(x.k).video), c: colOf(x.by) })) : null }; }
      if (ph === 'surf') { const s = C.surf[p.id]; if (!s) return base; return { ...base, at: sv(s.at), ring: s.ring.map(sv), rec: !!s.rec, trail: s.trail.slice(-6).map(x => thumbOf(shot(x.k).video)) }; }
      if (ph === 'vote') return { ...base, options: C.chains.filter(c => c.shots.length).map(c => { const hh = c.shots.find(s => s.by === c.who[0]) || c.shots[0]; return { key: c.id, ...sv(hh.k), by: nameOf(c.who[0]), c: colOf(c.who[0]) }; }), voted: C.votes[p.id] };
      if (ph === 'between') return { ...base, next: MODES[C.nextMode].name, nextSub: MODES[C.nextMode].sub, filmN: film().pieces.length, kept: Object.values(ST.mine[p.id] || []).length };
      return base; }
    draw();
    return { stateFor, draw, onMsg, onJoin: p => { draw(); },
      crowdTarget: () => { const o = C.playing ? C.playing[C.at] : null; return o || null; }, performer: () => { const o = C.playing ? C.playing[C.at] : null; return o ? o.by : null; },
      stop() { stopIt(); clearInterval(clock); clearTimeout(advT); root$.hidden = true; root$.innerHTML = ''; $('#host').classList.remove('cin'); try { speechSynthesis.cancel(); } catch (e) { } } };
  }

  // ======================================================================= a phone: one thing on screen, ‹ › to browse, one big button
  const L = { i: 0, key: '', sig: '', prev: null, talk: null, sending: false, note: '', asked: 0, heardWas: 0, stop: null, shown: '' };
  const SEARCH = '<svg viewBox="0 0 40 40"><circle cx="17" cy="17" r="10" fill="none" stroke="currentColor" stroke-width="3.4"/><path d="M25 25 L35 35" stroke="currentColor" stroke-width="3.6" stroke-linecap="round"/></svg>';
  function phone(S, api) {
    if (S.phase !== 'cin') return null; L.S = S;
    const ph = S.ph, sk = [ph, S.round, S.step || '', S.playing].join('|');
    if (L.key !== sk) { L.key = sk; L.i = 0; L.note = ''; L.heardOnce = 0; L.shown = ''; }
    const take = {
      key: 'cin' + sk,
      render(el) { el.innerHTML = `<div class="cm"><div class="chd"><span class="cmode">${esc(S.modeName)}</span><span class="csay" id="cSay"></span><button class="cmag" id="cMag" aria-label="search" hidden>${SEARCH}</button></div>
          <div class="cstage" id="cStage"><div class="cmedia" id="cMedia"></div><button class="cnav l" id="cPrev" aria-label="back">${I.left}</button><button class="cnav r" id="cNext" aria-label="next">${I.right}</button><div class="cdots2" id="cDots"></div></div>
          <div class="cmeta" id="cMeta"></div><button class="cbig" id="cBig"></button>
          <div class="csheet" id="cSheet" hidden><div class="cfind"><button class="cmic" id="cTalk" aria-label="hold to talk">${I.mic}<i id="cLv"></i></button><form class="ctype" id="cForm"><input id="cType" type="text" enterkeyhint="search" autocomplete="off" maxlength="80" placeholder="say or type what you want"><button type="submit">find</button></form><button class="cx2" id="cClose" aria-label="close">✕</button></div><div class="cnote" id="cNote"></div></div></div>`;
        wire(el, api); take.patch(el, api, true); },
      patch(el, api, force) { const S = L.S, list = items();
        el.querySelector('#cSay').textContent = S.playing ? 'Throw things. Keep one.' : ph === 'steps' ? (S.passed ? 'Passed.' : S.say) : ph === 'surf' ? 'Wander. Record somewhere strange.' : ph === 'vote' ? 'Who is the hero?' : ph === 'between' ? 'That’s in the film.' : S.ready ? '' : 'Opening the archive…';
        const sig = JSON.stringify(list.map(x => x.key)); if (sig !== L.sig) { L.sig = sig; if (!L.keepI) L.i = 0; L.keepI = 0; }
        if (L.i >= list.length) L.i = Math.max(0, list.length - 1);
        const mag = el.querySelector('#cMag'); mag.hidden = !(ph === 'surf' || (ph === 'steps' && !S.passed && ['shots', 'sounds', 'figs'].includes(S.kind)));
        const browse = list.length > 1 || ph === 'surf' || (ph === 'steps' && ['shots', 'sounds', 'figs'].includes(S.kind));
        el.querySelector('#cPrev').hidden = !browse || (ph !== 'surf' && L.i === 0); el.querySelector('#cNext').hidden = !browse;
        el.querySelector('#cDots').innerHTML = browse && ph !== 'surf' ? list.map((_, i) => `<i class="${i === L.i ? 'on' : ''}"></i>`).join('') : '';
        show(el, api, list[L.i], force); big(el, api, list[L.i]); note(); }
    };
    // what can be browsed right now
    function items() { const S = L.S;
      if (S.playing) return S.now ? [{ key: 'now', show: 'img', th: S.now.th }] : [];
      if (ph === 'steps') { if (S.passed) return [];
        if (S.kind === 'shots' || S.kind === 'backlot') return (S.items || []).map(x => ({ key: x.key, show: 'video', v: x.v, th: x.th, prov: x.prov, gold: x.gold }));
        if (S.kind === 'sounds') return (S.discs || []).map(d => ({ key: d.key, show: 'sound', d }));
        if (S.kind === 'ops') return (S.ops || []).map(o => ({ key: o.key, show: 'op', o }));
        if (S.kind === 'figs') return (S.figs || []).map(f => ({ key: f.key, show: 'fig', png: f.png }));
        if (S.kind === 'bonds') return (S.bonds || []).map(b => ({ key: b, show: 'bond', b }));
        if (S.kind === 'place') { const sl = S.slots || []; return Array.from({ length: sl.length + 1 }, (_, i) => ({ key: String(sl.length - i), show: 'place', a: sl[sl.length - i - 1], b: sl[sl.length - i] })); } }
      if (ph === 'surf') return S.at ? [{ key: String(S.at.k), show: 'video', v: S.at.v, th: S.at.th }] : [];
      if (ph === 'vote') return (S.options || []).map(o => ({ key: String(o.key), show: 'img', th: o.th, by: o.by, c: o.c }));
      return []; }
    // the thing on screen; sounds play on the phone, cuts happen on the phone
    function show(el, api, it, force) { const S = L.S, m = el.querySelector('#cMedia'), meta = el.querySelector('#cMeta'), id = it ? it.key + '|' + it.show : (S.passed ? 'passed' : ph);
      if (!force && L.shown === id + S.heardN) return; L.shown = id + S.heardN; if (L.stop) { L.stop(); L.stop = null; } const a = L.prev || (L.prev = new Audio()); a.pause();
      const h = S.hand;
      if (S.passed) { m.innerHTML = `<div class="cdone">${I.pass}<b>${S.to ? 'Passed to ' + esc(S.to) : 'In the film'}</b><small>waiting for the others</small></div>`; meta.innerHTML = ''; return; }
      if (ph === 'between') { m.innerHTML = `<div class="cdone">${I.star}<b>${S.filmN} shots in the film</b><small>next: ${esc(S.next)} · ${esc(S.nextSub)}</small></div>`; meta.innerHTML = ''; return; }
      if (!it) { m.innerHTML = `<div class="cdone"><small>${S.ready ? '…' : 'opening the archive…'}</small></div>`; meta.innerHTML = ''; return; }
      const vid = (v, box, th) => `<video src="${esc(v)}" ${th ? `poster="${esc(th)}"` : ''} muted loop playsinline autoplay ${box ? `style="transform-origin:${(box[0] + box[2] / 2) * 100}% ${(box[1] + box[3] / 2) * 100}%;transform:scale(${Math.min(3.2, .85 / Math.max(box[2], box[3]))})"` : ''}></video>`;
      if (it.show === 'video') m.innerHTML = vid(it.v, null, it.th) + (it.prov ? `<i class="prov">${I.star}${esc(it.prov)}</i>` : '');
      else if (it.show === 'img') m.innerHTML = `<img src="${esc(it.th)}" alt="">`;
      else if (it.show === 'fig') m.innerHTML = `<img class="fig" src="${esc(it.png)}" alt="">`;
      else if (it.show === 'sound') { m.innerHTML = (h ? vid(h.v, h.box, h.th) : '') + `<b class="csd2" style="--f:${FAM[it.d.fam]}">${famIcon(it.d.fam)}</b>${it.d.x ? `<i class="cline">“${esc(it.d.x)}”</i>` : ''}`; a.src = it.d.u; a.addEventListener('loadedmetadata', () => { try { a.currentTime = it.d.t0 || 0; } catch (e) { } a.play().catch(() => { }); }, { once: true }); clearTimeout(a._t); a._t = setTimeout(() => a.pause(), Math.min(6, (it.d.t1 || 5) - (it.d.t0 || 0)) * 1000 + 200); }
      else if (it.show === 'op' && h) { m.innerHTML = `<video playsinline muted></video><div class="cb"></div><img class="cx" alt=""><b class="copw">${I[it.o.key]}<span>${it.o.n}</span></b>`; const V = m.querySelector('video'); L.stop = run({ v: h.v, snd: h.snd ? { u: h.snd.u, t0: h.snd.t0, t1: h.snd.t1 } : null, op: it.o.key, len: 4.2, box: h.box, flash: h.th }, { V, A: a, X: m.querySelector('.cx'), B: m.querySelector('.cb') }, { done: () => { if (L.shown.startsWith(id)) { L.shown = ''; show(el, api, it, true); } } }); }
      else if (it.show === 'bond') { const pr = S.pair || []; m.innerHTML = `<div class="cpair">${pr[0] ? `<img src="${esc(pr[0].th)}" alt="">` : ''}<b style="--c:${BCOL[it.b]}">${I.combine}<span>${it.b}</span></b>${pr[1] ? `<img src="${esc(pr[1].th)}" alt="">` : ''}</div>`; }
      else if (it.show === 'place') m.innerHTML = `<div class="cpair">${it.a ? `<img src="${esc(it.a.th)}" alt="">` : '<em>start</em>'}<b class="slot">${I.star}</b>${it.b ? `<img src="${esc(it.b.th)}" alt="">` : '<em>end</em>'}</div>`;
      // the line under it: whose it is, what you are adding
      if (S.playing && S.now) meta.innerHTML = `<span style="--c:${S.now.c}">${I.eye}${esc(S.now.by)}</span>${S.now.snd ? `<span style="--c:${S.now.snd.c}">${famIcon(S.now.snd.fam)}${esc(S.now.snd.by)}</span>` : ''}${S.now.op ? `<span>${I[S.now.op]}${OPN[S.now.op]}</span>` : ''}`;
      else if (ph === 'steps' && h && S.from) meta.innerHTML = `<span style="--c:${h.c}">${esc(S.from)}’s shot</span>${h.listen ? `<button class="chear" id="cHear">${I.ear}hear it</button>` : ''}`;
      else if (ph === 'steps' && h && h.listen) meta.innerHTML = `<button class="chear" id="cHear">${I.ear}hear it</button>`;
      else if (ph === 'vote') meta.innerHTML = `<span style="--c:${it.c}">${esc(it.by)}’s</span>`;
      else meta.innerHTML = '';
      const hb = meta.querySelector('#cHear'); if (hb && h) { const go = () => { a.src = h.v; a.currentTime = 0; a.play().catch(() => { }); clearTimeout(a._t); a._t = setTimeout(() => a.pause(), 5000); }; hb.onclick = go; if (!L.heardOnce) { L.heardOnce = 1; go(); } } }
    // the one big button
    function big(el, api, it) { const S = L.S, b = el.querySelector('#cBig'); let label = '', on = !!it, cls = '';
      if (S.playing) { label = S.kept ? '★ Kept' : '★ Keep this one'; cls = S.kept ? 'gold' : 'gold-o'; on = !S.kept; }
      else if (ph === 'steps') { if (S.passed) { label = 'Passed ✓'; on = false; } else label = (S.act || 'Pass it') + ' ▸ ' + (S.to || 'the film'); }
      else if (ph === 'surf') { label = S.rec ? '● Recorded · again' : '● REC'; cls = 'rec'; on = true; }
      else if (ph === 'vote') { label = S.voted != null && it && String(S.voted) === it.key ? 'Voted ✓' : 'Vote'; cls = 'pink'; }
      else if (ph === 'between') { label = '▶ Next: ' + S.next; on = true; }
      else { label = '…'; on = false; }
      b.textContent = label; b.className = 'cbig ' + cls; b.disabled = !on; }
    function wire(el, api) {
      const go = d => { const S = L.S, list = items(); api.buzz(6);
        if (ph === 'surf') { if (d < 0) api.send({ t: 'back' }); else { const r = S.ring || []; const k = r[Math.min(r.length - 1, Math.floor(Math.random() * 3))]; if (k) api.send({ t: 'surf', k: k.k }); } return; }
        if (d > 0 && L.i >= list.length - 1) { if (ph === 'steps' && ['shots', 'sounds', 'figs'].includes(S.kind)) { ask(api, { far: 1 }, 'more…'); } return; }
        L.i = Math.max(0, Math.min(list.length - 1, L.i + d)); take.patch(el, api); };
      el.querySelector('#cPrev').onclick = () => go(-1); el.querySelector('#cNext').onclick = () => go(1);
      const st = el.querySelector('#cStage'); let x0 = null; st.addEventListener('pointerdown', e => { x0 = e.clientX; }); st.addEventListener('pointerup', e => { if (x0 == null) return; const dx = e.clientX - x0; x0 = null; if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1); });
      el.querySelector('#cBig').onclick = () => { const S = L.S, it = items()[L.i]; api.buzz(26);
        if (S.playing) api.send({ t: 'keep' });
        else if (ph === 'steps' && it) { api.send({ t: 'pass', key: it.key }); const b = el.querySelector('#cBig'); b.disabled = true; b.textContent = 'passing…'; }
        else if (ph === 'surf') api.send({ t: 'rec' });
        else if (ph === 'vote' && it) api.send({ t: 'vote', v: +it.key });
        else if (ph === 'between') api.send({ t: 'next' }); };
      const sh = el.querySelector('#cSheet'); el.querySelector('#cMag').onclick = () => { sh.hidden = false; L.note = ''; note(); }; el.querySelector('#cClose').onclick = () => { sh.hidden = true; };
      const ti = el.querySelector('#cType'); el.querySelector('#cForm').onsubmit = e => { e.preventDefault(); const q = ti.value.trim(); if (!q) return; ti.blur(); ask(api, { text: q }, 'looking for “' + q + '”…'); };
      talk(el.querySelector('#cTalk'), api); }
    function note() { const S = L.S, nt = document.getElementById('cNote'); if (!nt) return;
      if (L.asked && S.heardN !== L.heardWas) { L.asked = 0; L.note = L.far ? '' : S.miss ? 'nothing heard: type it instead' : S.heard ? 'found things for “' + S.heard + '”' : ''; const sh = document.getElementById('cSheet'); if (sh && !S.miss) sh.hidden = true; }
      else if (L.asked && performance.now() - L.asked > 15000) { L.asked = 0; L.note = 'no answer: try again or type'; }
      nt.textContent = L.note; nt.classList.toggle('busy', !!L.asked); }
    function ask(api, m, n) { L.far = !!m.far; L.asked = performance.now(); L.heardWas = L.S.heardN; L.note = n; if (m.far) L.keepI = 0; note(); api.send(m.far ? { t: 'far' } : { t: 'say', ...m }); }
    function talk(b, api) {
      const say = t => { L.note = t; const n = document.getElementById('cNote'); if (n) { n.textContent = t; n.classList.add('busy'); } };
      b.onpointerdown = e => { e.preventDefault(); if (L.talk || L.sending) return; api.buzz(16); try { b.setPointerCapture(e.pointerId); } catch (x) { } b.classList.add('on'); let last = 0; say('listening… let go to send');
        L.talk = window.Ears ? Ears.hold(api, { onLevel: v => { const i = document.getElementById('cLv'); if (i) i.style.transform = `scale(${1 + Math.min(1, v * 3)})`; }, onPartial: t => { const now = performance.now(); if (now - last > 200) { last = now; api.send({ t: 'heard', part: t }); } if (t) say('“' + t + '”'); } }) : null;
        if (L.talk) L.talk.ready.catch(() => { L.talk = null; b.classList.remove('on'); say('no microphone: type it instead'); }); else say('no microphone: type it instead'); };
      const up = async () => { const h = L.talk; if (!h) return; L.talk = null; b.classList.remove('on'); L.sending = true; say('sending…'); const r = await h.stop().catch(() => null); L.sending = false;
        if (r) ask(api, { a: r.a, mime: r.mime, dur: r.dur, text: r.text }, r.text ? 'looking for “' + r.text + '”…' : 'listening to it…'); else say('too short: hold it while you talk'); };
      b.onpointerup = up; b.onpointercancel = up; b.oncontextmenu = e => e.preventDefault(); }
    L.take = take;
    return { key: take.key, status: null, cls: 'cinp', throws: true, takeover: take };
  }
  Party.games.cineosis = { title: 'Cineosis', blurb: 'a multiplayer game for getting lost together in a moving-image archive. Find a shot, pass it, someone changes it: eight cards (Pass the Cut, Spoil It, Channel Surf, Backlot, Audition, Telephone, Chemistry Jam, Breakaway), one living film.',
    options: [{ k: 'start', name: 'first card', values: ['pass', 'spoil', 'surf', 'audition', 'phone', 'chem', 'away'], def: 'pass' }], host, phone };
})();
