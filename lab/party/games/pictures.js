/* MONTE CARLO PICTURES on the Party platform: make the movie with what you've got.
   Each reel deals a production problem to the whole crew; every phone holds its own hand (three shots, three sounds, three
   cuts, under the problem's rules) and sends one of each; studio notes land after the hands are in; the house rolls twelve
   takes from every hand and keeps the critic's best, and rolls one of its own from anything in the rushes; dailies unlabelled;
   every phone circles one; the circled take is printed. At the wrap: the film and the making of. Nothing moves until a
   person says so. */
(function () {
  const { esc, pad, UP, rnd, pick, shuffle, mini } = Party;
  const NOTE_REELS = [2, 4];
  const SKIP = /^(and|the|for|its|two|row|off|top|set|one|three|four|five|many|pink|golden|green|blue|yellow|orange|pastel|dead|retro|overhead|single|tidy|grid|array|pair|group|with|from|over|under|into|onto|through|frame|shot|wide|close|frontal|distant|empty|small|large|black|white|colour|color|light|dark|washed|centre|center|left|right|half|low|high|soft|flat|deep|pale|tight|loose|b&w)$|(y|ed|al|ive|ous|ful|ic|ish|less|ing|ly)$/i;
  const EDITS = [
    { id: 'hold', n: 'Hold', x: 'stay on it' }, { id: 'early', n: 'Cut early', x: 'get out fast' }, { id: 'repeat', n: 'Repeat', x: 'say it twice' },
    { id: 'interrupt', n: 'Interrupt', x: 'break in, come back' }, { id: 'withhold', n: 'Withhold', x: 'sound first, picture later' },
    { id: 'away', n: 'Cut away', x: 'look elsewhere, return' }, { id: 'bridge', n: 'Bridge', x: 'sound starts on the last shot' }, { id: 'late', n: 'Enter late', x: 'start at the end' }];
  const E = id => EDITS.find(e => e.id === id);

  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    let R = null, SH = [], url, thumb;
    const has = (s, t) => s.t.includes(t), words = s => new Set(((s.w || '') + ' ' + (s.s || []).join(' ') + ' ' + (s.x || '')).toLowerCase().match(/[a-z]{4,}/g) || []);
    const jac = (a, b) => { let n = 0; a.forEach(w => b.has(w) && n++); return n / Math.max(1, Math.min(a.size, b.size)); };
    const noun = s => (s.s && s.s[0]) || ((s.w || '').toLowerCase().match(/[a-z]{3,}/g) || []).find(w => !SKIP.test(w)) || 'shot';
    const voiceCard = l => ({ kind: 'voice', v: l.v, t0: l.t0, t1: l.t1, x: l.x, f: l.f }), musicCard = m => ({ kind: 'music', v: m.v, f: m.f, d: m.d });
    const SILENCE = { kind: 'silence' }, ROOM = { kind: 'room' };
    const total = P => P.reduce((a, p) => a + p.len, 0);
    function cap(t, T) { let a = 0; t.pieces = t.pieces.filter(p => { if (a >= T - .05) return false; p.len = Math.min(p.len, T - a); a += p.len; return true; }); }
    function cover(t) { const end = Math.max(0, ...t.sounds.filter(s => s.kind === 'voice').map(s => s.at + s.len + .4)), T = total(t.pieces); if (end > T) t.pieces[t.pieces.length - 1].len += end - T; }
    const PROBLEMS = [
      { id: 'nocu', n: 'No close-up', x: 'Every take we have is wide.', foot: s => !has(s, 'close') && !has(s, 'people') },
      { id: 'dialogue', n: 'We lost the dialogue', x: 'The production sound is gone. Find another.', noRoom: true },
      { id: 'dog', n: 'Keep the dog', x: 'The animal is in the contract.', foot: s => has(s, 'animal') },
      { id: 'shorter', n: 'The studio wants it shorter', x: 'Under two and a half seconds.', edits: ['early', 'interrupt', 'late'], apply: t => cap(t, 2.4) },
      { id: 'longer', n: 'The studio now wants it longer', x: 'Fill eight seconds.', edits: ['hold', 'repeat', 'withhold'], apply: t => { while (total(t.pieces) < 8) t.pieces.push(Object.assign({}, t.pieces.find(p => p.main) || t.pieces[0], { len: 2.2 })); } },
      { id: 'soft', n: 'The best take is out of focus', x: 'It is still the best take.' },
      { id: 'early', n: 'The sound arrives two seconds early', x: 'Sync is off. It stays off.', apply: t => t.pieces.unshift({ black: true, len: 2 }) },
      { id: 'bw', n: 'No colour', x: 'The colour stock was lost in the post.', foot: s => has(s, 'bw') },
      { id: 'back', n: 'The star won’t turn around', x: 'Every take is from behind.', foot: s => has(s, 'back') },
      { id: 'gone', n: 'The location is gone in four seconds', x: 'Then the permit runs out.', apply: t => { cap(t, 4); t.pieces.push({ black: true, len: 1.4, slate: 'Permit expired' }); } },
      { id: 'prop', n: 'That prop cannot be shown', x: 'Legal has not cleared it.' },
      { id: 'nocov', n: 'No coverage', x: 'One shot. That is all there is.' }];
    const NOTES = [
      { id: 'dog', n: 'We need the dog.', apply: t => { const a = pick(SH.filter(s => has(s, 'animal'))); t.pieces.push({ v: a.v, t0: 0, len: 1.8, shot: a }); } },
      { id: 'funnier', n: 'Make it funnier. Without changing the tone.', apply: t => { const l = pick(R.funny); t.sounds = t.sounds.filter(s => s.kind === 'music'); t.pieces.forEach(p => p.own = false); t.sounds.push({ kind: 'voice', v: l.v, t0: l.t0, len: l.t1 - l.t0 + .2, at: .4, x: l.x }); cover(t); } },
      { id: 'lost8', n: 'We’ve lost eight seconds.', apply: t => cap(t, 1.8) },
      { id: 'legal', n: 'Legal has concerns about the last shot.', apply: t => { const k = t.pieces.length - 1; t.pieces[k] = { black: true, len: t.pieces[k].len || 1.8, slate: 'This shot has been removed' }; } },
      { id: 'music', n: 'Add music. Any music.', apply: t => { const m = pick(R.music); t.sounds = t.sounds.filter(s => s.kind !== 'music'); t.sounds.push({ kind: 'music', v: m.v, t0: Math.min(4, Math.max(0, (m.d || 20) - 12)), len: 99, at: 0, vol: .7 }); } },
      { id: 'face', n: 'Can it end on a face?', apply: t => { const a = pick(SH.filter(s => has(s, 'close'))); t.pieces.push({ v: a.v, t0: 0, len: 1.8, shot: a }); } }];
    const G = { phase: 'loading', reel: 0, reels: H.opt.reels, film: [], all: [], hands: {}, picks: {}, sent: {}, takes: [], votes: {} };
    H.houseScore = 0;

    // ---- a take: the hand played through its cut, the house's continuation after it; then the problem and the note
    function build(h, o, prob, note) {
      const F = h.F, S = h.S, d = Math.max(1.5, F.d || 4), Pc = [];
      const at = len => Math.max(0, (d - len) * o.j);
      const fp = (len, t0) => ({ v: F.v, t0, len, own: S.kind === 'room', blur: !!F.soft, shot: F, main: true });
      const tp = len => ({ v: o.tail.v, t0: Math.max(0, Math.min(1, (o.tail.d || 3) - len)), len, shot: o.tail });
      const prev = o.prev ? { v: o.prev.v, t0: 0, len: 1.5, shot: o.prev } : { black: true, len: 1.5 };
      if (h.E.id === 'hold') Pc.push(fp(Math.max(4, Math.min(6.5, d)), 0));
      if (h.E.id === 'early') Pc.push(fp(1.6, at(1.6)));
      if (h.E.id === 'repeat') { const a = at(2); Pc.push(fp(2, a), fp(2, a)); }
      if (h.E.id === 'interrupt') { const a = at(3.4); Pc.push(fp(1.8, a), Object.assign({}, prev, { len: .5 }), fp(1.6, a + 1.8)); }
      if (h.E.id === 'withhold') Pc.push({ black: true, len: 1.6 }, fp(3, at(3)));
      if (h.E.id === 'away') { const a = at(3.5); Pc.push(fp(2, a), tp(2), fp(1.5, a + 2)); }
      if (h.E.id === 'bridge') Pc.push(prev, fp(3, at(3)));
      if (h.E.id === 'late') Pc.push(fp(2.5, Math.max(0, d - 2.5)));
      if (h.E.id !== 'away') Pc.push(tp(1.8));
      const t = { pieces: Pc, sounds: [], F, S, E: h.E, tail: o.tail };
      if (S.kind === 'voice') t.sounds.push({ kind: 'voice', v: S.v, t0: S.t0, len: S.t1 - S.t0 + .2, at: h.E.id === 'bridge' ? 0 : h.E.id === 'withhold' ? .2 : o.delay, x: S.x });
      if (S.kind === 'music') t.sounds.push({ kind: 'music', v: S.v, t0: o.mo * Math.max(0, (S.d || 20) - 12), len: 99, at: 0, vol: .8 });
      cover(t); if (prob.apply) prob.apply(t); if (note) note.apply(t);
      return t; }
    function critic(t) { const a = words(t.F), b = words(t.tail), sfit = t.S.kind === 'voice' ? (jac(words({ x: t.S.x }), a) > 0 ? 1 : .45) : t.S.kind === 'music' ? .62 : t.S.kind === 'silence' ? .5 : .38;
      const v = .3 * t.F.sc / 10 + .2 * t.tail.sc / 10 + .18 * jac(a, b) + .2 * sfit + .12 * rnd(); return Math.max(4, Math.min(97, Math.round((v - .28) / .5 * 100))); }
    function tailFor(F) { const a = words(F); let best = null, bv = -1; for (let k = 0; k < 40; k++) { const c = pick(SH); if (c === F || c.v === F.v || c.d < 1.5) continue; const v = .55 * c.sc / 10 + .45 * jac(a, words(c)) + rnd() * .35; if (v > bv) { bv = v; best = c; } } return best; }
    function roll(h, n) { const out = []; for (let k = 0; k < n; k++) { const t = build(h, { tail: tailFor(h.F), j: rnd(), delay: .2 + rnd() * .9, mo: rnd(), prev: G.film.length ? G.film[G.film.length - 1].take.tail : null }, G.prob, G.note); t.pct = critic(t); out.push(t); } return out.sort((a, b) => b.pct - a.pct)[0]; }
    function deal(prob) {
      const printed = new Set(G.film.map(f => String(f.take.F.v))), ok = s => s.d >= 2 && !printed.has(String(s.v)) && (!prob.foot || prob.foot(s));
      let pool = SH.filter(ok); if (pool.length < 6) pool = SH.filter(s => s.d >= 2);
      const films = new Set(), F = [];
      for (const band of [s => s.sc >= 6, s => s.sc >= 3 && s.sc <= 5, () => true]) { const c = shuffle(pool.filter(band)).find(s => !films.has(s.f)) || pick(pool); films.add(c.f); F.push(Object.assign({}, c)); }
      if (prob.id === 'soft') { const b = F.reduce((a, c) => c.sc > a.sc ? c : a); b.soft = true; b.stamp = 'soft'; }
      if (prob.id === 'prop') { const c = F.find(s => s.s && s.s[0]) || F[0]; c.stamp = 'not cleared'; c.off = true; }
      if (prob.id === 'nocov') { F[1] = { stub: true, stamp: 'not shot', off: true }; F[2] = { stub: true, stamp: 'not shot', off: true }; }
      const S = shuffle([voiceCard(pick(R.lines)), musicCard(pick(R.music)), prob.noRoom ? (rnd() < .5 ? SILENCE : voiceCard(pick(R.lines))) : pick([SILENCE, ROOM, ROOM])]);
      return { F: shuffle(F), S, E: prob.edits ? prob.edits.map(E) : shuffle(EDITS).slice(0, 3) }; }

    // ---- the projector: two pictures that swap at the cut, stills, slates, voices and beds
    const vids = [H.VP[0], H.VP[1]], auds = H.AP.slice(0, 4); let still = $('#vids img.still'); if (!still) { still = document.createElement('img'); still.className = 'still'; still.alt = ''; $('#vids').append(still); }
    let ptok = 0, timers = []; const later = (ms, f) => timers.push(setTimeout(f, ms));
    function load(el, p) { const u = url(p.v); el.dataset.t0 = p.t0 || 0; if (el.dataset.u !== u) { el.dataset.u = u; el.src = u; el.addEventListener('loadedmetadata', () => { try { el.currentTime = +el.dataset.t0; } catch (e) { } }, { once: true }); } else { try { el.currentTime = p.t0 || 0; } catch (e) { } } }
    function hush() { ptok++; timers.forEach(clearTimeout); timers = []; vids.forEach(v => { v.pause(); v.style.filter = ''; }); auds.forEach(a => { a.pause(); a.dataset.busy = ''; }); H.cap(''); H.bug(''); }
    function project(pieces, sounds, onEnd) {
      hush(); const my = ptok; let n = 0, side = 0; const loaded = new Map(); H.show(null);
      const nextV = from => { for (let k = from; k < pieces.length; k++) if (pieces[k].v) return k; return -1; };
      const first = nextV(0); if (first >= 0) { load(vids[0], pieces[first]); loaded.set(first, 0); }
      const step = () => { if (my !== ptok) return; const p = pieces[n]; if (!p) { hush(); onEnd && onEnd(); return; }
        H.bug(p.tag ? `<span>${esc(p.tag)}</span>` : '');
        if (p.slate || p.black) { H.slate(p.slate ? `<div class="card"><div class="txt"><div class="big" style="font-size:9cqh">${esc(p.slate).replace(/\n/g, '<br>')}</div></div></div>` : ''); still.classList.remove('on'); }
        else if (p.still) { H.show(null); vids.forEach(v => v.classList.remove('on')); still.src = p.still; still.classList.add('on'); }
        else { H.show(null); still.classList.remove('on');
          let k = loaded.has(n) ? loaded.get(n) : side; if (!loaded.has(n)) load(vids[k], p);
          const el = vids[k], other = vids[1 - k]; el.muted = !p.own; el.style.filter = p.blur ? 'blur(7px)' : ''; el.classList.add('on'); other.classList.remove('on'); other.pause(); el.play().catch(() => { });
          side = 1 - k; const nv = nextV(n + 1); if (nv >= 0 && !loaded.has(nv)) { load(other, pieces[nv]); loaded.set(nv, 1 - k); } }
        n++; later(p.len * 1000, step); };
      (sounds || []).forEach(s => later(Math.max(0, s.at) * 1000, () => { if (my !== ptok) return;
        const a = auds.find(x => !x.dataset.busy) || auds[0]; a.dataset.busy = '1'; const u = url(s.v);
        if (a.dataset.u !== u) { a.dataset.u = u; a.src = u; a.addEventListener('loadedmetadata', () => { try { a.currentTime = s.t0 || 0; } catch (e) { } }, { once: true }); } else { try { a.currentTime = s.t0 || 0; } catch (e) { } }
        a.volume = s.vol || 1; a.play().catch(() => { }); if (s.x) H.cap('“' + s.x + '”');
        if (s.len < 90) later(s.len * 1000, () => { if (my !== ptok) return; a.pause(); a.dataset.busy = ''; H.cap(''); }); }));
      step(); }
    const playTake = (t, done, x = {}) => project(x.slate ? [{ black: true, len: 1.2, slate: x.slate }, ...t.pieces] : t.pieces, (t.sounds || []).map(s => Object.assign({}, s, { at: s.at + (x.slate ? 1.2 : 0) })), done);
    const stripOf = t => t.pieces.slice(0, 6).map(p => p.v ? `<i style="background-image:url('${esc(thumb(p.v))}')${p.blur ? ';filter:blur(2px)' : ''}"></i>` : `<i style="background:#000"></i>`).join('');

    fetch('pictures/rushes.json').then(r => r.json()).then(d => { R = d; SH = R.shots;
      url = v => Array.isArray(v) ? R.r2 + R.P[v[0]] + '/clips/' + v[1] + '.mp4' : R.r2 + v; thumb = v => url(v).replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg'); reel(); });
    H.slate(H.card(`<div class="big">Monte Carlo Pictures<small>make the movie with what you’ve got · loading the rushes…</small></div>`, 'rose'));

    // ---- a reel: the problem, a hand for everyone, the note, the roll, the dailies, the circle, the print
    function reel() {
      G.reel++; hush(); const used = new Set(G.film.map(f => f.prob.id)); G.prob = pick(PROBLEMS.filter(p => !used.has(p.id)));
      G.note = NOTE_REELS.includes(G.reel) ? pick(NOTES.filter(n => !G.film.some(f => f.note && f.note.id === n.id))) : null; G.noteShown = false;
      G.hands = {}; G.picks = {}; G.sent = {}; G.takes = []; G.votes = {}; H.sign = {}; G.phase = 'deal';
      H.players.forEach(p => { G.hands[p.id] = deal(G.prob); G.picks[p.id] = {}; });
      H.slate(H.card(`<div class="big">Reel ${G.reel}<br>${esc(G.prob.n)}<small>${esc(G.prob.x)} · pick a shot, a sound and a cut on your phone</small></div>`, 'rose'));
      draw(); }
    const handOf = id => { if (!G.hands[id]) { G.hands[id] = deal(G.prob); G.picks[id] = {}; } return G.hands[id]; };
    const voters = () => H.players.filter(p => p.local || p.conn);
    function pickCard(pid, row, k) { if (G.phase !== 'deal') return; const h = handOf(pid), c = h[row][k]; if (!c || c.off || c.stub) return; G.picks[pid][row] = k; if (G.sent[pid]) { G.sent[pid] = false; delete H.sign[pid]; if (H._gate) H.ungate(); } draw(); }
    function send(pid) { if (G.phase !== 'deal') return; const pk = G.picks[pid] || {}; if (pk.F == null || pk.S == null || pk.E == null) return; G.sent[pid] = true; H.sign[pid] = 'ready'; H.act(pid, 'hop', 820);       if (voters().every(p => G.sent[p.id])) H.gate(G.note ? 'Studio note ▸' : 'Roll the takes ▸', 'any', G.note ? studioNote : rollAll); draw(); }
    function studioNote() { G.phase = 'note'; H.paper(`<div class="ledger" style="font-size:7cqh;line-height:1.3"><div class="hd">STUDIO NOTE · REEL ${G.reel}</div><div style="border:0;padding-top:2cqh">${esc(G.note.n)}</div><div style="border:0;font-size:3.6cqh;color:#7a6a58">Your hands stay. The note goes into every take.</div></div>`); H.gate('Fine. Roll the takes ▸', 'any', rollAll); draw(); }
    function rollAll() {
      G.phase = 'rolled'; H.sign = {};
      H.players.forEach(p => { if (!G.sent[p.id]) return; const h = handOf(p.id), pk = G.picks[p.id]; G.takes.push({ by: p.id, take: roll({ F: h.F[pk.F], S: h.S[pk.S], E: h.E[pk.E] }, 12), r: {} }); });
      const wildPool = G.prob.foot ? SH.filter(s => G.prob.foot(s) && s.d >= 2) : SH.filter(s => s.d >= 2 && (has(s, 'animal') || s.sc <= 3 || rnd() < .05));
      const wild = { F: Object.assign({}, pick(wildPool.length ? wildPool : SH)), S: pick([voiceCard(pick(R.lines)), voiceCard(pick(R.lines)), musicCard(pick(R.music)), SILENCE, ...(G.prob.noRoom ? [] : [ROOM])]), E: pick(G.prob.edits ? G.prob.edits.map(E) : EDITS) };
      G.takes.push({ by: 'house', take: roll(wild, 12), r: {} }); G.takes = shuffle(G.takes);
      H.slate(H.card(`<div class="big">${G.takes.length * 12} futures rolled<small>the critic kept one take per hand · the house rolled one of its own</small></div>`, 'house')); H.act('house', 'hop', 820); H.say('house', 'I made one too', 1800);
      H.gate('Screen the dailies ▸', 'any', () => { G.phase = 'dailies'; G.daily = 0; daily(); }); draw(); }
    function daily() { const k = G.daily, d = G.takes[k]; G.watching = true; H.crowdShow(d); draw();
      playTake(d.take, () => { G.watching = false; H.slate(H.card(`<div class="big">Take ${k + 1}<small>${k + 1 < G.takes.length ? 'next take when you’re ready' : 'that’s all of them'}</small></div>`, 'night'));
        H.gate(k + 1 < G.takes.length ? 'Next take ▸' : 'Circle one ▸', 'any', () => { if (k + 1 < G.takes.length) { G.daily++; daily(); } else { G.phase = 'circle'; H.crowdShow(null); H.slate(H.card(`<div class="big">Circle one<small>every phone · not your own take</small></div>`, 'night')); draw(); } }); draw(); }, { slate: 'Take ' + (k + 1) }); }
    function vote(pid, k) { if (G.phase !== 'circle' || k < 0 || k >= G.takes.length || G.takes[k].by === pid) return; const first = G.votes[pid] == null; G.votes[pid] = k; H.sign[pid] = 'circled'; if (first) H.act(pid, 'hit', 280);
      if (voters().every(p => G.votes[p.id] != null)) H.gate('Print it ▸', 'any', print); draw(); }
    function print() {
      const n = G.takes.map(() => 0); Object.values(G.votes).forEach(k => n[k]++); const max = Math.max(...n); let win = n.indexOf(max); const tied = n.map((v, k) => v === max ? k : -1).filter(k => k >= 0); if (tied.length > 1) win = pick(tied);
      G.win = win; G.n = n; G.gain = {}; H.sign = {};
      G.takes.forEach((d, k) => { const g = n[k] + (k === win ? 2 : 0); if (!g) return; if (d.by === 'house') H.houseScore += g; else { const p = P(d.by); if (p) { p.score += g; G.gain[p.id] = g; } } });
      const d = G.takes[win], wp = P(d.by), head = wp ? (n[win] ? UP(wp.name) + '’S TAKE IS PRINTED.' : 'PRINTED BY A COIN TOSS.') : 'NOBODY BET ON THE ' + UP(noun(d.take.F)) + '.';
      G.film.push({ reel: G.reel, prob: G.prob, note: G.note, take: d.take, by: d.by, takes: G.takes, printed: win, head, hands: H.players.map(p => G.hands[p.id] && G.hands[p.id].F[(G.picks[p.id] || {}).F]).filter(Boolean).map(c => c.v) }); G.all = G.all.concat(G.takes);
      G.phase = 'printed'; H.slate(H.card(`<div class="big">${esc(head)}<small>take ${win + 1} · ${wp ? esc(wp.name) : 'the house'} · ${n[win]} circled</small></div>`, 'gold'));
      H.act(d.by, 'cheer', 2200); G.takes.forEach((t, k) => { if (k !== win && !n[k]) setTimeout(() => H.act(t.by, 'slump', 2000), 400); });
      setTimeout(() => { if (G.phase === 'printed') playTake(d.take, null, { slate: 'Print' }); }, 2400);
      H.gate(G.reel < G.reels ? 'Next reel ▸' : 'That’s a wrap ▸', 'any', () => { if (G.reel < G.reels) reel(); else wrap(); }); draw(); }
    function toFilm() { const F = Cut.blank(title());
      G.film.forEach(f => { F.clips.push(Cut.card('Reel ' + f.reel + '\n' + f.prob.n, 1.8)); const firstIx = F.clips.length, at = [];
        let t = 0; f.take.pieces.forEach(p => { const c = p.v ? Cut.shot(url(p.v), +(p.t0 || 0), +(p.t0 || 0) + p.len, { d: p.shot && p.shot.d, own: !!p.own, label: p.shot && p.shot.w }) : Cut.card(p.slate || '', p.len); at.push([t, c]); t += p.len; F.clips.push(c); });
        const T = t; f.take.sounds.forEach(s => { const hit = at.filter(([a]) => a <= s.at + .001).pop() || at[0]; if (!hit) return; const off = s.at - hit[0];
          if (s.kind === 'voice') F.sounds.push(Cut.voice(hit[1].id, url(s.v), s.t0, s.t0 + s.len - .2, { off, text: s.x }));
          if (s.kind === 'music') F.sounds.push(Cut.music(hit[1].id, url(s.v), s.t0, Math.max(1, T - s.at), { off, vol: s.vol || .7 })); }); });
      return F; }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function title() { const c = {}; G.film.forEach(f => (f.take.F.s && f.take.F.s.length ? f.take.F.s.map(x => x.toLowerCase()) : [...words(f.take.F)]).forEach(w => c[w] = (c[w] || 0) + 1)); const w = Object.entries(c).filter(([w]) => !SKIP.test(w)).sort((a, b) => b[1] - a[1])[0]; return w ? 'The ' + w[0] : 'Untitled'; }
    function seq(list) { const pieces = [], sounds = []; let t = 0; list.forEach(x => { if (x.take) { x.take.sounds.forEach(s => sounds.push(Object.assign({}, s, { at: s.at + t, len: Math.min(s.len, total(x.take.pieces) - s.at + .2) }))); x.take.pieces.forEach(p => { pieces.push(Object.assign({}, p, x.tag ? { tag: x.tag } : {})); t += p.len; }); } else { pieces.push(x); t += x.len; } }); return { pieces, sounds, t }; }
    const whoName = id => id === 'house' ? 'the house' : (P(id) || {}).name || '';
    function filmA() { const T = title(), films = [...new Set(G.film.flatMap(f => [f.take.F.f, f.take.tail.f]).filter(Boolean))];
      const s = seq([{ black: true, len: 2.2, slate: 'A Monte Carlo Picture' }, { black: true, len: 2.4, slate: T }, ...G.film.map(f => ({ take: f.take })), { black: true, len: 2.6, slate: 'Made with what we had' }, ...Array.from({ length: Math.ceil(films.length / 4) }, (_, k) => ({ black: true, len: 2.6, slate: 'Footage from\n' + films.slice(k * 4, k * 4 + 4).join('\n') }))]);
      project(s.pieces, s.sounds); }
    function filmB() { const L = [{ black: true, len: 2.4, slate: 'The making of\n' + title() }];
      G.film.forEach(f => { L.push({ black: true, len: 2.2, slate: 'Reel ' + f.reel + '\n“' + f.prob.n + '”' }); f.hands.forEach(v => L.push({ still: thumb(v), len: .55, tag: 'the rushes' }));
        if (f.note) L.push({ black: true, len: 2, slate: 'Studio note:\n' + f.note.n });
        f.takes.forEach((d, k) => { if (k !== f.printed) { const p = d.take.pieces.find(p => p.v); if (p) L.push(Object.assign({}, p, { len: Math.min(1.8, p.len + 1), own: false, tag: 'take ' + (k + 1) + ' · ' + whoName(d.by) + ' · outtake' })); } });
        f.take.pieces.filter(p => p.v).slice(0, 2).forEach(p => L.push(Object.assign({}, p, { tag: 'printed · ' + whoName(f.by) }))); L.push({ black: true, len: 1.9, slate: f.head }); });
      const s = seq(L), m = pick(R.music); s.sounds.push({ kind: 'music', v: m.v, t0: 2, len: s.t, at: 0, vol: .55 }); project(s.pieces, s.sounds); }
    function wrap() { hush(); G.phase = 'wrap'; const r = rank(), top = r[0], houseWins = H.houseScore > (top ? top.score : 0); G.awards = H.awards(G.all);
      H.slate(H.card(houseWins ? `<div class="big">The house directed<br>this picture<small>${H.houseScore} ★</small></div>` : `<div class="big">Best director<br>${H.who(top.id)}<small>${top.score} ★ · the house ${H.houseScore} ★</small></div>`, 'gold'));
      const champ = houseWins ? 'house' : top.id; H.act(champ, 'cheer', 2200); [...H.players.map(p => p.id), 'house'].filter(id => id !== champ).forEach((id, i) => setTimeout(() => H.act(id, 'bow', 1300), 500 + i * 160));
      H.gate('Edit the film ▸', 'any', () => { H.seed = toFilm(); H.playGame('cut'); }); draw(); }

    // ---- the exposure sheet
    function handRows(p) { const h = handOf(p.id), pk = G.picks[p.id] || {};
      return `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${['F', 'S', 'E'].map(row => h[row].map((c, k) => `<button class="btn chip ${pk[row] === k ? 'on' : ''}" data-p="${p.id}" data-row="${row}" data-k="${k}" ${c.off || c.stub ? 'disabled' : ''}>${row === 'F' ? 'shot' : row === 'S' ? 'snd' : 'cut'} ${k + 1}</button>`).join('')).join('')}<button class="btn chip" data-send="${p.id}">${G.sent[p.id] ? 'sent ✓' : 'send'}</button></div>`; }
    function drawSide() { const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">Monte Carlo Pictures <small>loading</small></div>`, ph);
      if (ph === 'deal' || ph === 'note') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Reel ${G.reel} of ${G.reels} <small>${Object.values(G.sent).filter(Boolean).length} of ${voters().length} hands in</small></div><div class="problem"><b>${esc(G.prob.n)}</b>${esc(G.prob.x)}</div>
          ${locals.map(handRows).join('')}${G.note && ph === 'note' ? `<div class="problem"><b>Studio note</b>${esc(G.note.n)}</div>` : ''}
          ${!H._gate && ph === 'deal' && Object.values(G.sent).some(Boolean) ? `<button class="btn chip" id="force" style="margin-top:8px">roll now (skip the stragglers)</button>` : ''}`, ph + G.reel);
        S.querySelectorAll('[data-row]').forEach(b => b.onclick = () => pickCard(b.dataset.p, b.dataset.row, +b.dataset.k)); S.querySelectorAll('[data-send]').forEach(b => b.onclick = () => send(b.dataset.send));
        const f = $('#force'); if (f) f.onclick = () => (G.note ? studioNote : rollAll)(); return; }
      if (ph === 'rolled' || ph === 'dailies' || ph === 'circle') { const locals = ph === 'circle' ? H.players.filter(p => p.local) : [];
        const S = H.side(`<div class="ph">${ph === 'circle' ? 'Circle take' : 'Dailies'} <small>${ph === 'circle' ? Object.keys(G.votes).length + ' of ' + voters().length + ' circled' : 'nobody knows whose is whose'}</small></div><div class="takes">${G.takes.map((d, k) => `<div class="tk ${ph === 'dailies' && k === G.daily ? 'now' : ''}"><span class="n">${k + 1}</span><span class="strip">${ph === 'circle' || (ph === 'dailies' && (k < G.daily || (k === G.daily && !G.watching))) ? stripOf(d.take) : ''}</span><span class="by hint" style="margin:0">${esc(H.crowdText(d))}</span></div>`).join('')}</div>
          ${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.takes.map((d, k) => `<button class="btn chip ${G.votes[p.id] === k ? 'on' : ''}" data-v="${p.id}" data-k="${k}" ${d.by === p.id ? 'disabled' : ''}>${k + 1}</button>`).join('')}</div>`).join('')}
          ${ph === 'circle' && !H._gate ? `<button class="btn chip" id="force" style="margin-top:8px">print now (skip the stragglers)</button>` : ''}`, ph + (G.daily || 0));
        S.querySelectorAll('[data-v]').forEach(b => b.onclick = () => vote(b.dataset.v, +b.dataset.k)); const f = $('#force'); if (f) f.onclick = print; return; }
      if (ph === 'printed') return H.side(`<div class="ph">Printed <small>who made what · who circled it</small></div><div class="takes">${G.takes.map((d, k) => `<div class="tk ${k === G.win ? 'win' : ''}"><span class="n">${k + 1}</span><span class="strip">${stripOf(d.take)}</span><span class="by">${H.who(d.by)} <span class="hint" style="margin:0">♣ ${d.take.pct}%</span><br><span class="vs">${Object.entries(G.votes).filter(([, v]) => v === k).map(([id]) => P(id) ? mini(P(id).av) : '').join('') || '·'}</span>${H.crowdText(d) ? `<br><span class="hint" style="margin:0">${esc(H.crowdText(d))}</span>` : ''}</span></div>`).join('')}</div>`, ph + G.reel);
      if (ph === 'wrap') { const S = H.side(`<div class="ph">That’s a wrap <small>circles · printed</small></div>${rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}<b>${p.score}</b></div>`).join('')}<div class="rk">· ${mini('house')} the house<b>${H.houseScore}</b></div>${H.awardsHTML(G.awards)}
          <div class="row" style="margin-top:8px"><button class="btn chip" id="fa">▶ the film</button><button class="btn chip" id="fb">▶ the making of</button></div>`, ph); $('#fa').onclick = filmA; $('#fb').onclick = filmB; return S; }
    }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, reel: G.reel, reels: G.reels };
      if (G.prob) { s.prob = { n: G.prob.n, x: G.prob.x }; }
      if (G.phase === 'deal' || G.phase === 'note') { const h = handOf(p.id); s.hand = { F: h.F.map(c => c.stub ? { stub: true, stamp: c.stamp } : { th: thumb(c.v), w: c.w, stamp: c.stamp, off: !!c.off, soft: !!c.soft }), S: h.S.map(c => ({ kind: c.kind, x: c.x, f: c.f })), E: h.E.map(c => ({ n: c.n, x: c.x })) }; s.picks = G.picks[p.id] || {}; s.sent = !!G.sent[p.id]; s.in = Object.values(G.sent).filter(Boolean).length; s.of = voters().length; }
      if (G.phase === 'note') s.note = G.note.n;
      if (G.phase === 'dailies') { s.daily = G.daily + 1; s.nTakes = G.takes.length; }
      if (G.phase === 'circle') { s.nTakes = G.takes.length; s.own = G.takes.findIndex(d => d.by === p.id); s.mine = G.votes[p.id]; s.crowd = G.takes.map(d => H.crowdText(d)); }
      if (G.phase === 'printed') { const d = G.takes[G.win]; s.win = G.win; s.head = G.film[G.film.length - 1].head; s.gain = G.gain[p.id] || 0; s.pct = (G.takes.find(x => x.by === p.id) || {}).take; s.pct = s.pct ? s.pct.pct : null; }
      if (G.phase === 'wrap') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; s.awards = (G.awards || []).filter(a => a.id === p.id).map(a => a.name); }
      return s; }
    return { stateFor, draw, onMsg(p, m) { if (m.t === 'pick') pickCard(p.id, m.row, m.k); if (m.t === 'send') send(p.id); if (m.t === 'vote') vote(p.id, m.k); },
      crowdTarget: () => G.phase === 'dailies' ? G.takes[G.daily] : null, performer: () => null, stop() { hush(); } };
  }

  function phone(S, api) {
    const P = S.phase;
    if (P === 'loading') return { key: 'loading', status: 'loading the rushes…', tabs: ['me', 'throw'] };
    if (P === 'deal' || P === 'note') return { key: 'deal' + S.reel, status: 'Reel ' + S.reel + ' of ' + S.reels + ' · ' + S.in + ' of ' + S.of + ' hands in' + (S.note ? ' · studio note: ' + esc(S.note) : ''), takeover: { key: 'deal' + S.reel + JSON.stringify(S.picks) + S.sent, render(el) {
      const h = S.hand, pk = S.picks, ready = pk.F != null && pk.S != null && pk.E != null;
      el.innerHTML = `<div class="problem"><b>${esc(S.prob.n)}</b>${esc(S.prob.x)}</div>
        <div class="lbl">footage</div><div class="hand">${h.F.map((c, k) => c.stub ? `<button class="cd" disabled><div style="aspect-ratio:4/3;background:#2a2220;border-radius:3px"></div><span class="stamp">${esc(c.stamp)}</span></button>` : `<button class="cd ${pk.F === k ? 'on' : ''}" data-row="F" data-k="${k}" ${c.off ? 'disabled' : ''}><img alt="" src="${esc(c.th)}" style="${c.soft ? 'filter:blur(3px)' : ''}">${esc(c.w)}${c.stamp ? `<span class="stamp">${esc(c.stamp)}</span>` : ''}</button>`).join('')}</div>
        <div class="lbl">sound</div><div class="hand">${h.S.map((c, k) => `<button class="cd ${pk.S === k ? 'on' : ''}" data-row="S" data-k="${k}">${c.kind === 'voice' ? `<b>a voice</b>“${esc(c.x)}”` : c.kind === 'music' ? `<b>♪ music</b>${esc(c.f)}` : c.kind === 'silence' ? '<b>silence</b>nothing at all' : '<b>room tone</b>the shot’s own sound'}</button>`).join('')}</div>
        <div class="lbl">cut</div><div class="hand">${h.E.map((c, k) => `<button class="cd edit ${pk.E === k ? 'on' : ''}" data-row="E" data-k="${k}"><b>${esc(c.n)}</b>${esc(c.x)}</button>`).join('')}</div>
        <button class="btn cta" id="sendB" ${ready && !S.sent ? '' : 'disabled'}>${S.sent ? 'in the can · change anything to resend' : ready ? 'send my take ▸' : 'pick a shot, a sound and a cut'}</button>`;
      el.querySelectorAll('[data-row]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'pick', row: b.dataset.row, k: +b.dataset.k }); });
      const sb = el.querySelector('#sendB'); if (sb) sb.onclick = () => { api.buzz(30); api.send({ t: 'send' }); }; } } };
    if (P === 'rolled') return { key: 'rolled' + S.reel, status: 'The house rolled every hand twelve ways', tabs: ['throw', 'me'] };
    if (P === 'dailies') return { key: 'dailies' + S.daily, status: 'Dailies · take ' + S.daily + ' of ' + S.nTakes + '', tab: 'throw', tabs: ['throw', 'me'] };
    if (P === 'circle') return { key: 'circle', takeover: { key: 'circle' + S.mine, render(el) {
      el.innerHTML = `<div class="center"><div class="say">Circle one</div><div class="sub">the take that gets printed · not your own</div>
        <div class="vote">${Array.from({ length: S.nTakes }, (_, k) => `<button data-k="${k}" class="${S.mine === k ? 'on' : ''}" ${k === S.own ? 'disabled' : ''}><svg viewBox="0 0 100 100"><ellipse cx="50" cy="52" rx="44" ry="38" transform="rotate(-8 50 52)"/></svg>${k + 1}</button>`).join('')}</div>
        <div class="sub">${(S.crowd || []).map((c, k) => c ? `take ${k + 1}: ${esc(c)}` : '').filter(Boolean).join(' · ')}</div><div class="sub">${S.own >= 0 ? 'Take ' + (S.own + 1) + ' is yours.' : ''}</div></div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', k: +b.dataset.k }); }); } } };
    if (P === 'printed') return { key: 'printed' + S.reel, status: esc(S.head) + (S.gain ? ' · you +' + S.gain + ' ★' : '') + (S.pct != null ? ' · the critic gave yours ' + S.pct + '%' : ''), tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.of}</div><div class="sub">${S.you.score} ★${S.awards && S.awards.length ? '<br>' + S.awards.map(esc).join(' · ') : ''}</div></div>`; } } };
    return null;
  }
  Party.games.pictures = { title: 'Monte Carlo Pictures', blurb: 'every phone holds a hand: a shot, a sound, a cut, under the day’s production problem', options: [{ k: 'reels', name: 'reels', values: [3, 4, 6], def: 4 }], host, phone };
})();
