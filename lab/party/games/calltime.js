/* CALL TIME on the Party platform: make today's movie with whatever survived yesterday.
   A shooting day: the call sheet; the guide (shared channels and three private ones on each remote); the clapboard, held until
   the director shouts ACTION; the hot remote (tap a channel to cut on the beat, a planned cut list played with NEXT); the house
   rolls forty takes and keeps one; dailies, unlabelled, one at a time when someone says next; every phone circles one (not its
   own); the reveal when someone says so; the continuity report, which is tomorrow's call sheet. Nothing advances by itself. */
(function () {
  const { esc, pad, UP, rnd, pick, shuffle, mini } = Party;
  const BEAT = .75, MAXT = 15, NB = Math.round(MAXT / BEAT), SPLIT = 6;
  const SCENES = [
    { n: 'Odysseus leaves home', call: 'MAKE THE GOODBYE', cast: ['Odysseus', 'Penelope', 'a dog'], re: /house|home|door|gate|woman|women|family|road|dog|garden|street|window/i },
    { n: 'Out to sea', call: 'GET US ONTO THE WATER', cast: ['Odysseus', '6 sailors'], re: /water|sea|boat|ship|wave|harbou?r|river|dock|sail|lake/i },
    { n: 'The Cyclops cave', call: 'FIND THE MONSTER', cast: ['Odysseus', 'the Cyclops', '2 sailors', 'sheep'], re: /cave|dark|rock|fire|giant|eye|sheep|goat|tunnel|machine|mine|furnace/i },
    { n: 'The escape', call: 'MAKE THE ESCAPE', cast: ['Odysseus', '3 sailors', 'sheep'], re: /run|sheep|boat|crowd|car|train|road|smoke|water|horse/i },
    { n: 'The Sirens', call: 'SURVIVE THE SONG', cast: ['Odysseus, tied to the mast', 'the Sirens'], re: /woman|women|girl|sing|dancer|dance|music|water|rock|stage/i },
    { n: 'Home at last', call: 'BRING HIM HOME', cast: ['Odysseus', 'Penelope', 'the old dog'], re: /house|home|dog|door|bed|woman|old|table|family|window/i }];
  const SKIP = /^(and|the|for|its|two|row|off|top|set|one|three|four|five|many|pink|golden|green|blue|yellow|orange|pastel|dead|retro|overhead|single|tidy|grid|array|pair|group|with|from|over|under|into|onto|through|frame|shot|wide|close|frontal|distant|empty|small|large|black|white|colour|color|light|dark|washed|centre|center|left|right|half|low|high|soft|flat|deep|pale|tight|loose|b&w)$|(y|ed|al|ive|ous|ful|ic|ish|less|ing|ly)$/i;

  // ======================================================== THE STAND
  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    let R = null, url, thumb, SH, key, txt, noun, words, jac;
    const G = { phase: 'loading', day: 0, days: H.opt.days, sheets: [], film: [], all: [], cont: {}, takes: [], votes: {}, turn: 0, order: [] };
    H.houseScore = 0;
    H.slate(H.card(`<div class="big">Call Time<small>loading the rushes…</small></div>`, 'dawn'));
    fetch('pictures/rushes.json').then(r => r.json()).then(d => { R = d;
      url = v => Array.isArray(v) ? R.r2 + R.P[v[0]] + '/clips/' + v[1] + '.mp4' : R.r2 + v; thumb = v => url(v).replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg');
      SH = R.shots.filter(s => s.d >= 2); key = s => Array.isArray(s.v) ? s.v[1] : s.v; txt = s => (s.w || '') + ' ' + (s.s || []).join(' ');
      noun = s => (s && s.s && s.s[0]) || ((s && s.w || '').toLowerCase().match(/[a-z]{3,}/g) || []).find(w => !SKIP.test(w)) || 'shot';
      words = s => new Set(txt(s).toLowerCase().match(/[a-z]{4,}/g) || []); jac = (a, b) => { let n = 0; a.forEach(w => b.has(w) && n++); return n / Math.max(1, Math.min(a.size, b.size)); };
      G.day = 1; callSheet(); });

    // ---- the rushes for a scene: the judged shots that answer it; each channel's next program is the shot most like it
    function pickShots(scene, n, avoid) {
      let pool = SH.filter(s => scene.re.test(txt(s)) && !avoid.has(key(s)));
      if (pool.length < n * 4) pool = pool.concat(shuffle(SH.filter(s => !avoid.has(key(s)))).slice(0, 200));
      const out = [], films = new Set();
      for (const s of pool.map(s => [s, s.sc + rnd() * 5]).sort((a, b) => b[1] - a[1]).map(x => x[0])) { if (out.length >= n) break; if (films.has(s.f) || avoid.has(key(s))) continue; films.add(s.f); avoid.add(key(s)); out.push(s); }
      return out; }
    function tailFor(F, avoid) { const a = words(F); let best = null, bv = -1;
      for (let k = 0; k < 60; k++) { const c = pick(SH); if (key(c) === key(F) || avoid.has(key(c))) continue; const v = .5 * c.sc / 10 + .5 * jac(a, words(c)) + rnd() * .3; if (v > bv) { bv = v; best = c; } }
      avoid.add(key(best)); return best; }
    const chanOf = (A, avoid, x = {}) => Object.assign({ A, B: tailFor(A, avoid), name: UP(noun(A)) + ' CAM', visits: 0, seenB: false }, x);
    const voiceOf = l => ({ kind: 'voice', l, name: 'VOICE “' + l.x.split(' ').slice(0, 3).join(' ') + '…”' });
    const musicOf = m => ({ kind: 'music', m, st: Math.max(0, ((m.d || 20) - 14) * rnd()), name: 'MUSIC · ' + (m.f || '').slice(0, 18) });
    const ROOMT = () => ({ kind: 'room', name: 'ROOM TONE' });

    // ---- a shooting day: the call sheet, made from yesterday's continuity
    function newDay() {
      const scene = SCENES[(G.day - 1) % SCENES.length], C = G.cont, avoid = new Set(G.film.flatMap(f => f.shots.map(key)));
      const shared = [];
      if (C.regular) shared.push(chanOf(C.regular.shot, avoid, { name: C.regular.name, star: true }));
      pickShots(scene, 3 - shared.length, avoid).forEach(s => shared.push(chanOf(s, avoid)));
      { const u = new Set(C.off ? [C.off.name] : []); shared.forEach(c => { if (u.has(c.name)) { const alt = (c.A.s || []).map(x => UP(x) + ' CAM').find(n => !u.has(n)); c.name = alt || c.name + ' II'; while (u.has(c.name)) c.name += 'I'; } u.add(c.name); }); }
      shared.forEach((c, k) => c.no = 2 + k);
      const sSnd = [C.heard ? Object.assign({}, C.heard, { star: true }) : voiceOf(pick(R.lines)), musicOf(pick(R.music))].slice(0, C.strike ? 1 : 2); sSnd.forEach((c, k) => c.no = 17 + k);
      const mine = {}; [...H.players.map(p => p.id), 'house'].forEach(id => { mine[id] = { pics: pickShots(scene, 3, avoid).map((s, k) => chanOf(s, avoid, { no: 5 + k, own: id })), snds: [voiceOf(pick(R.lines)), ROOMT()].map((c, k) => Object.assign(c, { no: 19 + k, own: id })) }; });
      const seen = new Set([...(C.off ? [C.off.name] : []), ...shared.map(c => c.name)]);
      const rename = c => { if (!seen.has(c.name)) { seen.add(c.name); return; } const alt = (c.A.s || []).map(x => UP(x) + ' CAM').find(n => !seen.has(n)); c.name = alt || c.name + ' II'; while (seen.has(c.name)) c.name += 'I'; seen.add(c.name); };
      Object.values(mine).forEach(m => { const keep = new Set(seen); m.pics.forEach(rename); seen.clear(); keep.forEach(n => seen.add(n)); });
      G.today = { scene, shared, sSnd, mine, off: C.off || null };
      G.sheets.push({ day: G.day, scene: scene.n, call: scene.call, cast: scene.cast, props: C.props || [], off: C.off ? [C.off] : [], notes: C.notes || [], cams: shared.map(c => pad(c.no) + ' ' + c.name + (c.star ? ' ★' : '')), sound: sSnd.map(c => pad(c.no) + ' ' + c.name), crew: H.players.map(p => p.name) });
      G.takes = []; G.votes = {}; G.turn = 0;
      const ids = H.players.map(p => p.id); const r = (G.day - 1) % Math.max(1, ids.length); G.order = ids.slice(r).concat(ids.slice(0, r));
    }
    const ensureMine = id => { if (G.today && !G.today.mine[id]) { const avoid = new Set(); G.today.mine[id] = { pics: pickShots(G.today.scene, 3, avoid).map((s, k) => chanOf(s, avoid, { no: 5 + k, own: id })), snds: [voiceOf(pick(R.lines)), ROOMT()].map((c, k) => Object.assign(c, { no: 19 + k, own: id })) }; } };
    const lineup = id => { ensureMine(id); return { pics: [...G.today.shared, ...G.today.mine[id].pics], snds: [...G.today.sSnd, ...G.today.mine[id].snds] }; };
    function sheetHTML(s, small) { if (!s) return '';
      return `<h3><span>DAY ${s.day}</span><span>CALL SHEET</span></h3><div class="g"><div><div class="k">SCENE</div>${esc(s.day)} · ${esc(s.scene)}<div class="k">CAST</div>${s.cast.map(esc).join('<br>')}</div>
        <div><div class="k">PROPS</div>${s.props.length ? s.props.map(x => esc(UP(x))).join('<br>') : '<span class="sm">whatever is on set</span>'}${s.off.map(o => `<br><span class="no">${esc(o.name)}</span>`).join('')}</div>
        ${small ? '' : `<div><div class="k">CAMERAS</div>${s.cams.map(esc).join('<br>')}<br><span class="sm">+ 3 private on each remote</span></div><div><div class="k">SOUND</div>${s.sound.map(esc).join('<br>')}<br><span class="sm">+ a voice, room tone</span></div>`}</div>
        ${s.notes.map(n => `<div class="note">PRODUCTION NOTE · ${esc(n)}</div>`).join('')}<div class="call">CALL: ${esc(s.call)}</div>
        ${small ? '' : `<div class="k">CREW</div><div>${s.crew.map(esc).join(' · ')}</div>`}${s.onAir ? `<div class="k">ON AIR</div><div>${esc(s.onAir)}</div>` : ''}`; }

    // ---- the screen: video channels from the stand's pool, voices and beds on their own players
    let CUR = null;
    const hushAll = () => { if (CUR) CUR.stop(true); CUR = null; };
    function Engine(lu, o) {
      const used = new Map(), free = H.VP.slice(), sounds = lu.snds.map(s => s.kind === 'room' ? null : H.AP[lu.snds.indexOf(s) % H.AP.length]);
      let t0 = 0, st = { cam: 0, snd: 0, slip: 0, mute: false, hold: false }, cur = null, curKey = '', tick = 0, timers = [], ended = false, sT = [];
      lu.snds.forEach((s, k) => { const a = sounds[k]; if (!a) return; const u = url(s.kind === 'voice' ? s.l.v : s.m.v); if (a.dataset.u !== u) { a.dataset.u = u; a.src = u; } a.pause(); });
      function el(i, part) { const k = i + part; if (!used.has(k)) { const v = free.shift() || H.VP[0], sh = lu.pics[i][part]; const u = url(sh.v); if (v.dataset.u !== u) { v.dataset.u = u; v.src = u; } v._sh = sh; used.set(k, v); } return used.get(k); }
      lu.pics.forEach((_, i) => el(i, 'A'));
      const now = () => t0 ? (performance.now() - t0) / 1000 : 0;
      const livePos = (sh, local) => { const d = Math.max(1, sh.d || 4); return local % d; };
      function showPic() { const t = now(), part = t < SPLIT ? 'A' : 'B', v = el(st.cam, part);
        if (o.live && part === 'B') lu.pics[st.cam].seenB = true;
        if (cur !== v) { if (cur) { cur.pause(); cur.classList.remove('on'); } cur = v; try { v.currentTime = livePos(v._sh, part === 'A' ? t : t - SPLIT); } catch (e) { } v.classList.add('on'); }
        v.muted = !(lu.snds[st.snd].kind === 'room' && !st.mute); if (st.hold) v.pause(); else v.play().catch(() => { });
        curKey = st.cam + part; if (part === 'A') el(st.cam, 'B'); }
      function sound() { sounds.forEach(a => a && a.pause()); sT.forEach(clearTimeout); sT = []; H.cap('');
        const s = lu.snds[st.snd], a = sounds[st.snd];
        if (!st.mute && s.kind === 'voice') { const skip = Math.max(0, -st.slip); sT.push(setTimeout(() => { if (ended) return; try { a.currentTime = s.l.t0 + skip; } catch (e) { } a.play().catch(() => { }); H.cap('“' + s.l.x + '”'); sT.push(setTimeout(() => { a.pause(); H.cap(''); }, Math.max(.3, s.l.t1 - s.l.t0 - skip) * 1000 + 200)); }, Math.max(0, st.slip) * 1000)); }
        if (!st.mute && s.kind === 'music') { try { a.currentTime = s.st + Math.max(0, now() + st.slip); } catch (e) { } a.volume = .85; a.play().catch(() => { }); }
        showPic(); }
      function apply(ev) { const n = lu.pics.length, m = lu.snds.length;
        if (ev.k === 'cam') st.cam = ((ev.v % n) + n) % n; if (ev.k === 'snd') st.snd = ((ev.v % m) + m) % m;
        if (ev.k === 'slip') st.slip = Math.max(-3, Math.min(3, Math.round((st.slip + ev.v) * 10) / 10)); if (ev.k === 'mute') st.mute = !st.mute; if (ev.k === 'hold') st.hold = !st.hold;
        if (ev.k === 'cam' && o.live) lu.pics[st.cam].visits++;
        if (ev.k === 'cam' || ev.k === 'hold') showPic(); else sound(); o.onChange && o.onChange(st); }
      function start(edl) { if (CUR && CUR !== api) CUR.stop(true); CUR = api; t0 = performance.now(); H.show(null); sound(); tick = setInterval(() => { const t = now(); if (t >= SPLIT && curKey === st.cam + 'A') showPic(); o.onTick && o.onTick(t, st); if (t >= (edl ? edl.end : MAXT)) stop(); }, 100);
        if (edl) edl.ev.forEach(e => timers.push(setTimeout(() => !ended && apply(e), e.t * 1000))); }
      function stop(quiet) { if (ended) return; ended = true; if (CUR === api) CUR = null; clearInterval(tick); timers.forEach(clearTimeout); sT.forEach(clearTimeout); used.forEach(v => { v.pause(); v.classList.remove('on'); }); sounds.forEach(a => a && a.pause()); H.cap(''); if (!quiet && o.onEnd) o.onEnd(Math.min(now(), MAXT)); }
      const api = { start, apply, stop, now, st: () => st };
      return api;
    }

    // ---- the turn: the clapboard waits for ACTION; the remote is live; REC prints
    function bug(p, st, lu, t) { const c = lu.pics[st.cam], s = lu.snds[st.snd];
      H.bug(`<span class="onair">ON AIR</span><span>${p ? mini(p.av) + ' ' + esc(p.name) : 'the house'}</span><span>CH ${pad(c.no)} ${esc(c.name)}<br>SND ${pad(s.no)} ${esc(s.name.slice(0, 22))}${st.slip ? ' ' + (st.slip > 0 ? '+' : '') + st.slip + 's' : ''}${st.mute ? ' · MUTE' : ''}${st.hold ? ' · HOLD' : ''}</span><span class="sp"></span><span class="left">${Math.max(0, Math.ceil(MAXT - t))}</span>`); }
    function clapboard(take) { const s = G.today.scene, p = P(take.by);
      return H.card(`<div class="clap"><div class="sticks"></div><div class="body"><div><small>DAY</small><span class="n">${G.day}</span></div><div><small>SCENE</small><span class="n">${G.day}</span></div><div><small>TAKE</small><span class="n">${take.n}</span></div><div class="w"><small>PRODUCTION</small>${esc(s.n)}</div><div class="w"><small>ON THE REMOTE</small>${p ? mini(p.av) + ' ' + esc(p.name) : 'the house'} · pick your opening shot, then ACTION</div></div></div>`, 'stage'); }
    function nextTurn() {
      if (G.turn >= G.order.length) return houseTurn();
      const id = G.order[G.turn], p = P(id); if (!p) { G.turn++; return nextTurn(); }
      const take = { by: id, n: G.takes.length + 1, lu: lineup(id), edl: { ev: [], end: MAXT }, start: { cam: 0, snd: 0 }, r: {} }; G.air = take; G.phase = 'slate'; H.spot = id;
      H.slate(clapboard(take)); H.crowdShow(take); H.act(id, 'hop', 820); H.say(id, 'ready!');
      H.gate('ACTION! ▸', p.local ? 'any' : [id], () => { if (G.air !== take) return; const c = $('#slate .clap'); if (c) c.classList.add('shut'); setTimeout(H.clap, 300); setTimeout(() => goLive(take), 700); });
      draw();
    }
    function goLive(take) {
      const p = P(take.by); G.phase = 'air'; let lastSec = -1, lastBeat = -1;
      G.eng = Engine(take.lu, { live: true, onChange: st => { bug(p, st, take.lu, G.eng.now()); drawSide(); H.broadcast(); },
        onTick: (t, st) => { bug(p, st, take.lu, t); const s = Math.ceil(MAXT - t); if (s !== lastSec) { lastSec = s; H.broadcast(); } const b = Math.floor(t / BEAT); if (b !== lastBeat) { lastBeat = b; const l = $('#bug .left'); if (l && b % 4 === 0) { l.classList.add('tick'); setTimeout(() => l.classList.remove('tick'), 160); } } },
        onEnd: t => { G.pend.forEach(clearTimeout); G.pend = []; take.edl.end = Math.max(2, Math.round(t * 10) / 10); G.eng = null; H.bug(''); G.takes.push(take); G.air = null; H.act(take.by, 'hop', 820); H.say(take.by, 'print it!'); afterTake(take.by); } });
      G.pend = []; G.eng.start();
      if (take.start.cam) { G.eng.apply({ k: 'cam', v: take.start.cam }); take.edl.ev.push({ t: 0, k: 'cam', v: G.eng.st().cam }); } else take.lu.pics[0].visits++;
      if (take.start.snd) { G.eng.apply({ k: 'snd', v: take.start.snd }); take.edl.ev.push({ t: 0, k: 'snd', v: G.eng.st().snd }); }
      draw();
    }
    const LABEL = { sndto: 'SND', ch: 'CH', 'slip-': '◀ slip', 'slip+': 'slip ▶', mute: 'MUTE', hold: 'HOLD', 'cam+': 'CAM +', 'cam-': 'CAM −', 'snd+': 'SND +', 'snd-': 'SND −' };
    function press(pid, b, v) {
      if (!G.air || G.air.by !== pid) return;
      if (G.phase === 'slate' && G.air.start) { const n = G.air.lu; if (b === 'ch') G.air.start.cam = Math.max(0, Math.min(n.pics.length - 1, v | 0)); if (b === 'sndto') G.air.start.snd = Math.max(0, Math.min(n.snds.length - 1, v | 0)); H.broadcast(); H.act(pid, 'hit', 280); return; }
      if (!G.eng || G.phase !== 'air') return;
      const p = P(pid), take = G.air, eng = G.eng, now = eng.now();
      if (b === 'rec') { if (now >= 2) eng.stop(); return; }
      H.act(pid, 'hit', 280);
      const at = Math.min(MAXT - .05, Math.ceil((now + .04) / BEAT) * BEAT);
      G.pend.push(setTimeout(() => { if (G.eng !== eng || G.air !== take) return;
        const st = eng.st(), t = Math.round(at * 100) / 100;
        const ev = b === 'cam+' ? { k: 'cam', v: st.cam + 1 } : b === 'cam-' ? { k: 'cam', v: st.cam - 1 } : b === 'ch' ? { k: 'cam', v: v | 0 } : b === 'snd+' ? { k: 'snd', v: st.snd + 1 } : b === 'snd-' ? { k: 'snd', v: st.snd - 1 } : b === 'sndto' ? { k: 'snd', v: v | 0 } : b === 'slip-' ? { k: 'slip', v: -.5 } : b === 'slip+' ? { k: 'slip', v: .5 } : b === 'mute' ? { k: 'mute' } : b === 'hold' ? { k: 'hold' } : null;
        if (!ev) return;
        eng.apply(ev); take.edl.ev.push(Object.assign({ t }, ev, { v: ev.k === 'cam' ? eng.st().cam : ev.k === 'snd' ? eng.st().snd : ev.v }));
        const s2 = eng.st(), what = ev.k === 'cam' ? '→ ' + pad(take.lu.pics[s2.cam].no) + ' ' + take.lu.pics[s2.cam].name : ev.k === 'snd' ? '→ ' + take.lu.snds[s2.snd].name : ev.k === 'slip' ? (s2.slip > 0 ? '+' : '') + s2.slip + 's' : ev.k === 'mute' ? (s2.mute ? 'on' : 'off') : (s2.hold ? 'on' : 'off');
        H.logLine(`${mini(p.av)} ${LABEL[b] || ''} ${esc(what)}`); }, Math.max(0, (at - now) * 1000)));
    }
    function afterTake(fromId) {
      G.turn++; const nid = G.order[G.turn], n = nid && P(nid);
      if (n) { G.phase = 'pass'; G.air = { by: nid }; H.spot = null;
        H.slate(H.card(`<div class="big">The remote passes to<br>${H.who(nid)}<small>${n.local ? 'tap the button when you’re ready' : 'tap your phone when you’re ready'}</small></div>`, 'dawn'));
        setTimeout(() => H.throwRemote(fromId, nid), 250);
        H.gate('Take the remote ▸', n.local ? 'any' : [nid], () => nextTurn()); draw(); }
      else { G.air = null; H.spot = null; houseTurn(); }
    }
    // ---- the house makes a take too: forty cuts through its channels on the beat, kept by the critic
    function houseTurn() {
      G.phase = 'house'; G.air = null; H.spot = 'house'; H.slate(H.card(`<div class="big">The house<br>is rolling<small>forty takes through its own channels · it keeps one</small></div>`, 'house'));
      H.act('house', 'hop', 820); H.say('house', 'forty takes…', 2000);
      const lu = lineup('house'), sc = G.today.scene; let best = null;
      for (let k = 0; k < 40; k++) { const ev = []; let t = 0, cam = 0, v = 0, cuts = 0, snd = Math.floor(rnd() * lu.snds.length); ev.push({ t: 0, k: 'snd', v: snd });
        let segs = [], last = 0;
        while (true) { const dt = 1.5 + rnd() * 2.8; if (t + dt > 12) break; t += dt; segs.push([cam, t - last]); last = t; cam = Math.floor(rnd() * lu.pics.length); ev.push({ t: Math.round(t / BEAT) * BEAT, k: 'cam', v: cam }); cuts++; if (rnd() < .15) ev.push({ t: Math.round(t / BEAT) * BEAT, k: 'slip', v: rnd() < .5 ? -.5 : .5 }); }
        segs.push([cam, 12 - last]);
        segs.forEach(([c, d]) => { const s = lu.pics[c].A; v += d * (s.sc / 10 + (sc.re.test(txt(s)) ? .4 : 0)); });
        v = v / 12 + .3 * (1 - Math.abs(cuts - 3) * .15) + (lu.snds[snd].kind === 'voice' ? .15 : 0) + rnd() * .1;
        if (!best || v > best.v) best = { v, ev, end: 12 }; }
      G.takes.push({ by: 'house', n: G.takes.length + 1, lu, edl: { ev: best.ev, end: best.end }, r: {} });
      H.gate('Screen the dailies ▸', 'any', dailies); draw();
    }
    // ---- dailies: every take, unlabelled, shuffled; the next one when someone says so
    function dailies() { G.takes = shuffle(G.takes); G.phase = 'dailies'; G.daily = 0; H.spot = null; playDaily(); }
    function playDaily() {
      const k = G.daily, t = G.takes[k]; G.watching = true; draw(); H.crowdShow(t);
      H.slate(H.card(`<div class="big">Dailies<br>take ${k + 1}<small>day ${G.day} · ${esc(G.today.scene.n)}</small></div>`, 'night'));
      setTimeout(() => { if (G.phase !== 'dailies' || G.daily !== k) return; const e = Engine(t.lu, { onEnd: () => { G.watching = false;
        H.slate(H.card(`<div class="big">Take ${k + 1}<small>${G.daily + 1 < G.takes.length ? 'next take when you’re ready' : 'that’s all of them'}</small></div>`, 'night'));
        if (G.daily + 1 < G.takes.length) H.gate('Next take ▸', 'any', () => { G.daily++; playDaily(); }); else H.gate('Circle one ▸', 'any', circle); draw(); } }); e.start(t.edl); }, 1500);
    }
    function circle() { G.phase = 'circle'; G.votes = {}; H.crowdShow(null); H.slate(H.card(`<div class="big">Circle one<small>every phone · not your own take</small></div>`, 'night')); draw(); }
    const voters = () => H.players.filter(p => p.local || p.conn);
    function castVote(pid, k) { if (G.phase !== 'circle' || k < 0 || k >= G.takes.length || G.takes[k].by === pid) return; const first = G.votes[pid] == null; G.votes[pid] = k; H.sign[pid] = 'circled';
      if (first) { H.act(pid, 'hit', 280); H.say(pid, pick(['that one!', 'circle it', 'got mine', 'easy'])); }
      if (voters().every(p => G.votes[p.id] != null)) H.gate('Reveal ▸', 'any', reveal); draw(); }
    function reveal() {
      const n = G.takes.map(() => 0); Object.values(G.votes).forEach(k => n[k]++);
      const max = Math.max(...n); let win = n.indexOf(max); const tied = n.map((v, k) => v === max ? k : -1).filter(k => k >= 0); if (tied.length > 1) win = pick(tied);
      G.win = win; G.gain = {}; H.sign = {};
      G.takes.forEach((t, k) => { const g = n[k] + (k === win ? 2 : 0); if (!g) return; if (t.by === 'house') H.houseScore += g; else { const p = P(t.by); if (p) { p.score += g; G.gain[p.id] = g; } } });
      const w = G.takes[win], wp = P(w.by); G.sheets[G.sheets.length - 1].onAir = 'take ' + (win + 1) + ' · ' + (wp ? wp.name : 'the house') + ' · ' + n[win] + ' circled';
      G.film.push({ day: G.day, scene: G.today.scene.n, take: w, shots: usage(w).shots }); G.all = G.all.concat(G.takes);
      G.phase = 'result'; G.n = n;
      H.slate(H.card(`<div class="big">On air: take ${win + 1}<br>${H.who(w.by)}<small>${n[win]} circled · +${n[win] + 2} ★</small></div>`, 'gold'));
      H.act(w.by, 'cheer', 2200); H.say(w.by, pick(['we did it!', 'print!', 'that’s the one', 'magic!']), 2200);
      G.takes.forEach((t, k) => { if (k !== win && !n[k]) setTimeout(() => H.act(t.by, 'slump', 2000), 400); });
      setTimeout(() => { if (G.phase !== 'result') return; Engine(w.lu, {}).start(w.edl); }, 2600);
      H.gate('Continuity ▸', 'any', continuity); draw();
    }
    function usage(t) { const lu = t.lu, cams = {}, snds = {}; let cam = 0, snd = 0, last = 0, slip = false, mute = false, hold = false;
      const ev = t.edl.ev.slice().sort((a, b) => a.t - b.t).concat([{ t: t.edl.end, k: 'end' }]);
      ev.forEach(e => { const d = e.t - last; if (d > 0) { const part = last < SPLIT ? 'A' : 'B'; cams[cam] = (cams[cam] || 0) + d; cams['s' + cam + part] = lu.pics[cam][part]; snds[snd] = (snds[snd] || 0) + d; } last = e.t;
        if (e.k === 'cam') cam = e.v; if (e.k === 'snd') snd = e.v; if (e.k === 'slip') slip = true; if (e.k === 'mute') mute = true; if (e.k === 'hold') hold = true; });
      const shots = Object.keys(cams).filter(k => k[0] === 's').map(k => cams[k]);
      const topCam = Object.keys(cams).filter(k => k[0] !== 's').sort((a, b) => cams[b] - cams[a])[0], topSnd = Object.keys(snds).sort((a, b) => snds[b] - snds[a])[0];
      return { shots, topCam: +topCam, topSnd: +topSnd, slip, mute, hold }; }
    // ---- continuity: what the circled take changed becomes tomorrow's facts
    function continuity() {
      const w = G.takes[G.win], u = usage(w), lu = w.lu, wp = P(w.by), main = lu.pics[u.topCam], mainShot = u.shots[0] || main.A, L = [], C = {};
      const shared = G.today.shared, most = shared.slice().sort((a, b) => b.visits - a.visits)[0], least = shared.filter(c => c !== most).sort((a, b) => a.visits - b.visits)[0];
      if (most && most.visits > 0) { C.regular = { name: most.name, shot: most.B }; L.push([most.name, `tuned ${most.visits}× today · it stays on tomorrow, and the house runs what comes next on it`]); }
      const gone = least ? least.name.replace(/ CAM$/, '') : '', built = (u.shots.map(x => UP(noun(x))).find(x => x !== gone) || UP(noun(mainShot)) === gone && 'NEXT' || UP(noun(mainShot)));
      if (least) { C.off = { name: least.name, why: 'dismantled to build the ' + built + ' set (day ' + G.day + ')' }; L.push([least.name, (least.visits ? 'barely watched' : 'nobody tuned in') + ' · dismantled to build the ' + built + ' set · OFF AIR tomorrow']); C.notes = [least.name + ' UNAVAILABLE · currently the ' + built + ' set']; }
      C.props = [...new Set(u.shots.map(noun).map(x => x.toLowerCase()))].slice(0, 3);
      C.props.forEach(x => L.push(['THE ' + UP(x), 'on air today · survives to tomorrow’s call sheet']));
      const hs = lu.snds[u.topSnd]; if (hs && hs.kind !== 'room') { C.heard = Object.assign({}, hs); delete C.heard.own; L.push([hs.name, 'heard on air · it will be heard again']); }
      if (u.mute) { C.strike = true; L.push(['SOUND DEPARTMENT', 'muted on air · tomorrow one sound channel short']); (C.notes = C.notes || []).push('SOUND IS ONE CHANNEL SHORT · they were muted on day ' + G.day); }
      if (u.hold) L.push(['THE ' + UP(noun(mainShot)), 'held on air · still holding the pose']);
      if (u.slip) L.push(['SYNC', 'slipped on air · nobody fixed it']);
      L.push(wp ? [UP(wp.name), 'directed today’s scene'] : ['THE HOUSE', 'directed today’s scene · ' + H.houseScore + ' ★ so far']);
      G.cont = C; G.sheets[G.sheets.length - 1].ledger = L;
      hushAll(); G.phase = 'continuity';
      H.paper(`<div class="ledger"><div class="hd">CONTINUITY REPORT · AFTER DAY ${G.day}</div>${L.map(([a, b]) => `<div><b>${esc(a)}</b> — ${esc(b)}</div>`).join('')}</div>`);
      H.gate(G.day < G.days ? 'Tomorrow’s call sheet ▸' : 'That’s a wrap ▸', 'any', () => { if (G.day < G.days) { G.day++; callSheet(); } else wrap(); }); draw();
    }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function wrap() { hushAll(); G.phase = 'wrap'; const r = rank(), top = r[0], houseWins = H.houseScore > (top ? top.score : 0); G.awards = H.awards(G.all);
      H.slate(H.card(houseWins ? `<div class="big">The house directed<br>this picture<small>${H.houseScore} ★ · the crew’s best: ${top ? esc(top.name) + ' ' + top.score + ' ★' : '—'}</small></div>` : `<div class="big">Best director<br>${H.who(top.id)}<small>${top.score} ★ · the house ${H.houseScore} ★</small></div>`, 'gold'));
      const champ = houseWins ? 'house' : top.id; H.act(champ, 'cheer', 2200); H.say(champ, 'thank you all!', 2400);
      [...H.players.map(p => p.id), 'house'].filter(id => id !== champ).forEach((id, i) => setTimeout(() => H.act(id, 'bow', 1300), 500 + i * 160));
      H.gate('Back to the lobby ▸', 'any', () => H.end()); draw(); }
    function playFilm() { let k = 0; const next = () => { if (k >= G.film.length) { H.slate(H.card(`<div class="big">The end<small>made with whatever survived</small></div>`, 'gold')); return; } const f = G.film[k++];
        H.slate(H.card(`<div class="big">Day ${f.day}<small>${esc(f.scene)}</small></div>`, 'dawn')); setTimeout(() => { Engine(f.take.lu, { onEnd: next }).start(f.take.edl); }, 1700); }; next(); }
    function callSheet() { hushAll(); newDay(); G.phase = 'call'; H.spot = null; H.sign = {}; H.paper(`<div class="sheet">${sheetHTML(G.sheets[G.sheets.length - 1], false)}</div>`); H.bug(''); H.gate('Roll camera ▸', 'any', nextTurn); draw(); }

    // ---- the exposure sheet beside the screen
    function guideHTML(id) {
      const lu = id ? lineup(id) : { pics: G.today.shared, snds: G.today.sSnd }, nowShot = G.film.length ? G.film[G.film.length - 1].shots.slice(-1)[0] : null, cur = G.eng && G.air && G.air.by === id ? G.eng.st() : null;
      const th = (s, q) => q ? '<i class="q">?</i>' : s ? `<i style="background-image:url('${esc(thumb(s.v))}')"></i>` : '<i class="q">—</i>';
      return `<table class="guide"><tr class="hd"><td>CH</td><td>PROGRAM</td><td class="th nowc">NOW</td><td class="th">+0</td><td class="th">+${SPLIT}s</td><td class="vis">TUNED</td></tr>
        ${lu.pics.map((c, k) => `<tr class="${cur && cur.cam === k ? 'cur' : ''} ${c.own ? 'mine' : ''}"><td class="no">${pad(c.no)}</td><td class="nm">${esc(c.name)}${c.star ? ' ★' : ''}</td><td class="th nowc">${th(nowShot)}</td><td class="th">${th(c.A)}</td><td class="th">${th(c.B, !(c.seenB || c.visits >= 2))}</td><td class="vis">${'●'.repeat(Math.min(5, c.visits))}</td></tr>`).join('')}
        ${G.today.off ? `<tr class="off"><td class="no">··</td><td class="nm" colspan="4">${esc(G.today.off.name)} <span class="rs">off air · ${esc(G.today.off.why)}</span></td><td></td></tr>` : ''}
        <tr class="sec"><td colspan="6">SOUND</td></tr>
        ${lu.snds.map((s, k) => `<tr class="${cur && cur.snd === k ? 'cur' : ''} ${s.own ? 'mine' : ''}"><td class="no">${pad(s.no)}</td><td class="nm" colspan="5">${esc(s.name)}${s.star ? ' ★' : ''}</td></tr>`).join('')}</table>`; }
    const stripOf = t => usage(t).shots.slice(0, 5).map(s => `<i style="background-image:url('${esc(thumb(s.v))}')"></i>`).join('');
    function localRemote() { const st = G.eng ? G.eng.st() : { mute: false, hold: false };
      return `<div class="lrem"><button class="btn" data-b="cam-">CAM −</button><button class="btn" data-b="cam+">CAM +</button><button class="btn rec" data-b="rec">● REC</button><button class="btn" data-b="snd-">SND −</button><button class="btn" data-b="snd+">SND +</button><button class="btn ${st.mute ? 'on' : ''}" data-b="mute">MUTE</button><button class="btn" data-b="slip-">◀ slip</button><button class="btn" data-b="slip+">slip ▶</button><button class="btn ${st.hold ? 'on' : ''}" data-b="hold">HOLD</button></div><div class="hint" style="margin:-4px 0 6px">keys: ↑↓ cam · [ ] sound · ←→ slip · M · H · Enter</div>`; }
    function drawSide() {
      const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">Call Time <small>loading</small></div>`, ph);
      if (ph === 'call') return H.side(`<div class="ph">The guide <small>day ${G.day} of ${G.days} · shared channels</small></div>${guideHTML(null)}<div class="hint">Each remote also gets three private channels (05–07), a voice (19) and room tone (20). First on the remote: ${esc((P(G.order[0]) || {}).name || '')}</div>`, ph);
      if (ph === 'slate' || ph === 'air' || ph === 'pass') { const p = G.air && P(G.air.by), local = p && p.local && ph === 'air';
        const S = H.side(`<div class="ph">The guide <small>${p ? esc(p.name) + '’s remote' : ''}</small></div>${local ? localRemote() : ''}${p ? guideHTML(p.id) : ''}`, ph);
        if (local) S.querySelectorAll('[data-b]').forEach(b => b.onclick = () => press(p.id, b.dataset.b)); return; }
      if (ph === 'house') return H.side(`<div class="ph">The house <small>rolled</small></div>${guideHTML('house')}`, ph);
      if (ph === 'dailies') return H.side(`<div class="ph">Dailies <small>nobody knows whose is whose</small></div><div class="takes">${G.takes.map((t, k) => `<div class="tk ${k === G.daily ? 'now' : ''}"><span class="n">${k + 1}</span><span class="strip">${k < G.daily || (k === G.daily && !G.watching) ? stripOf(t) : ''}</span><span class="by hint" style="margin:0">${esc(H.crowdText(t))}</span></div>`).join('')}</div>${!G.watching ? `<button class="btn chip" id="again" style="margin-top:8px">↻ replay take ${G.daily + 1}</button>` : ''}`, ph + G.daily);
      if (ph === 'circle') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Circle take <small>${Object.keys(G.votes).length} of ${voters().length} circled</small></div><div class="takes">${G.takes.map((t, k) => `<div class="tk"><span class="n">${k + 1}</span><span class="strip">${stripOf(t)}</span><span class="by hint" style="margin:0">${esc(H.crowdText(t))}</span></div>`).join('')}</div>
          ${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.takes.map((t, k) => `<button class="btn chip ${G.votes[p.id] === k ? 'on' : ''}" data-p="${p.id}" data-k="${k}" ${t.by === p.id ? 'disabled' : ''}>${k + 1}</button>`).join('')}</div>`).join('')}
          ${!H._gate ? `<button class="btn chip" id="force" style="margin-top:8px">reveal now (skip the stragglers)</button>` : ''}`, ph);
        S.querySelectorAll('[data-p]').forEach(b => b.onclick = () => castVote(b.dataset.p, +b.dataset.k)); const f = $('#force'); if (f) f.onclick = reveal; return; }
      if (ph === 'result') { const S = H.side(`<div class="ph">On air <small>who made what · who circled it</small></div><div class="takes">${G.takes.map((t, k) => { const vs = Object.entries(G.votes).filter(([, v]) => v === k).map(([id]) => P(id) ? mini(P(id).av) : ''); return `<div class="tk ${k === G.win ? 'win' : ''}"><span class="n">${k + 1}</span><span class="strip">${stripOf(t)}</span><span class="by">${H.who(t.by)}<br><span class="vs">${vs.join('') || '·'}</span>${H.crowdText(t) ? `<br><span class="hint" style="margin:0">${esc(H.crowdText(t))}</span>` : ''}</span></div>`; }).join('')}</div>
          <div class="hint"><button id="srcB" style="text-decoration:underline">where this footage comes from ↗</button></div>`, ph);
        const sb = $('#srcB'); if (sb) sb.onclick = () => window.Attrib && Attrib.show(usage(G.takes[G.win]).shots.map(s => ({ role: 'on air', video: url(s.v) }))); return S; }
      if (ph === 'continuity') return H.side(`<div class="ph">Tomorrow <small>these are facts now</small></div><div class="sheet">${sheetHTML(G.sheets[G.sheets.length - 1], true)}</div>`, ph);
      if (ph === 'wrap') { const r = rank();
        const S = H.side(`<div class="ph">That’s a wrap <small>+1 a circle · +2 on air</small></div>${r.map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}<b>${p.score}</b></div>`).join('')}<div class="rk">· ${mini('house')} the house<b>${H.houseScore}</b></div>${H.awardsHTML(G.awards)}
          <button class="btn cta alt" id="pf">▶ The film</button><div class="ph" style="margin-top:12px">The call sheets <small>the history of the production</small></div><div class="stack">${G.sheets.map(s => `<div class="sheet">${sheetHTML(s, false)}${s.ledger ? `<div class="k">CONTINUITY</div>${s.ledger.map(([a, b]) => `<div class="sm"><b>${esc(a)}</b> — ${esc(b)}</div>`).join('')}` : ''}</div>`).join('')}</div>`, ph);
        $('#pf').onclick = playFilm; return S; }
    }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    const again = () => { const t = G.takes[G.daily]; if (!t || G.watching) return; G.watching = true; draw(); Engine(t.lu, { onEnd: () => { G.watching = false; draw(); } }).start(t.edl); };
    document.addEventListener('click', e => { if (e.target && e.target.id === 'again' && G.phase === 'dailies') again(); });
    const keys = e => { if (G.phase !== 'air' || !G.air) return; const p = P(G.air.by); if (!p || !p.local) return;
      const b = { ArrowUp: 'cam+', ArrowDown: 'cam-', ']': 'snd+', '[': 'snd-', ArrowLeft: 'slip-', ArrowRight: 'slip+', m: 'mute', h: 'hold', Enter: 'rec' }[e.key]; if (b) { e.preventDefault(); press(p.id, b); } };
    addEventListener('keydown', keys);

    // ---- what each phone is told
    function stateFor(p) {
      const s = { phase: G.phase, day: G.day, days: G.days };
      const air = G.air && P(G.air.by);
      if (air) { s.onAir = { name: air.name, av: air.av }; s.isYou = air.id === p.id; }
      if (G.today && ['call', 'slate', 'air', 'pass', 'house', 'dailies'].includes(G.phase)) { const lu = lineup(p.id); s.scene = G.today.scene.n; s.mineCh = { pics: lu.pics.map(c => ({ no: c.no, name: c.name, own: !!c.own, th: thumb(c.A.v) })), snds: lu.snds.map(c => ({ no: c.no, name: c.name })) }; }
      if (G.phase === 'call') s.youNext = G.order[0] === p.id;
      if (G.phase === 'pass') s.nextYou = G.order[G.turn] === p.id;
      if (s.isYou && G.eng) { const st = G.eng.st(); s.air = { t: G.eng.now(), cam: st.cam, snd: st.snd, slip: st.slip, mute: st.mute, hold: st.hold }; }
      if (s.isYou && G.phase === 'slate') s.air = { t: 0, cam: G.air.start.cam, snd: G.air.start.snd, slip: 0 };
      if (G.phase === 'dailies') { s.daily = G.daily + 1; s.nTakes = G.takes.length; }
      if (G.phase === 'circle') { s.nTakes = G.takes.length; s.own = G.takes.findIndex(t => t.by === p.id); s.mine = G.votes[p.id]; s.crowd = G.takes.map(t => H.crowdText(t)); }
      if (G.phase === 'result') { const w = G.takes[G.win], b = P(w.by); s.win = G.win; s.winBy = b ? b.name : 'the house'; s.winAv = b ? b.av : null; s.gain = G.gain[p.id] || 0; }
      if (G.phase === 'wrap') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; s.awards = (G.awards || []).filter(a => a.id === p.id).map(a => a.name); }
      return s; }
    return { stateFor, draw, onMsg(p, m) { if (m.t === 'btn') press(p.id, m.b, m.v); if (m.t === 'vote') castVote(p.id, m.k); },
      crowdTarget: () => G.phase === 'air' || G.phase === 'slate' ? G.air : G.phase === 'dailies' ? G.takes[G.daily] : null,
      performer: () => (G.phase === 'air' || G.phase === 'slate') && G.air ? G.air.by : null,
      stop() { hushAll(); removeEventListener('keydown', keys); } };
  }

  // ======================================================== THE PHONE
  let plan = [], planAt = 0, planDay = -1, raf = 0, base = 0, lastBeat = -1;
  function phone(S, api) {
    const P = S.phase; if (S.day !== planDay) { planDay = S.day; plan = []; planAt = 0; }
    const planTab = { k: 'plan', name: 'Plan my turn', key: plan.length, render(el) { const M = S.mineCh;
      if (!M) { el.innerHTML = '<div class="hint">your channels arrive with the call sheet</div>'; return; }
      el.innerHTML = `<div class="lbl">your plan · tap channels in the order you’ll cut</div><div class="planbar">${plan.length ? plan.map((s, i) => `<button class="st" data-rm="${i}">${i + 1}. ${s.k === 'cam' ? pad(M.pics[s.v].no) + ' ' + esc(M.pics[s.v].name) : '♪ ' + esc(M.snds[s.v].name.slice(0, 14))}</button>`).join('') : '<span class="hint" style="margin:0">empty · tap below</span>'}${plan.length ? '<button class="st" data-rm="all">clear</button>' : ''}</div>
        <div class="lbl">picture</div><div class="tiles">${M.pics.map((c, i) => `<button class="tile" data-pc="${i}"><img alt="" src="${esc(c.th)}"><span>${pad(c.no)} ${esc(c.name)}${c.own ? ' · yours' : ''}</span></button>`).join('')}</div>
        <div class="lbl">sound</div><div class="snds">${M.snds.map((c, i) => `<button class="btn" data-ps="${i}">${pad(c.no)} ${esc(c.name)}</button>`).join('')}</div>`;
      el.querySelectorAll('[data-pc]').forEach(b => b.onclick = () => { if (plan.length >= 8) return; api.buzz(); plan.push({ k: 'cam', v: +b.dataset.pc }); api.rebuild(); });
      el.querySelectorAll('[data-ps]').forEach(b => b.onclick = () => { if (plan.length >= 8) return; api.buzz(); plan.push({ k: 'snd', v: +b.dataset.ps }); api.rebuild(); });
      el.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { b.dataset.rm === 'all' ? plan = [] : plan.splice(+b.dataset.rm, 1); api.rebuild(); }); } };
    const look = (key, big, sub, k, pose) => ({ key, takeover: { key, render(el) { el.innerHTML = `<div class="center">${k != null ? api.hero(k, pose) : ''}<div class="say">${big}</div><div class="sub">${sub || ''}</div></div>`; } } });
    if (P === 'loading') return look('loading', 'Call Time', 'loading the rushes…');
    if ((P === 'slate' || P === 'air') && S.isYou) return { key: 'remote' + P, cls: 'rem2', status: P === 'slate' ? 'You’re up. Pick your opening shot, then ACTION.' : null, takeover: remote(S, api) };
    if (P === 'circle') return { key: 'circle', takeover: { key: 'circle' + S.mine, render(el) {
      el.innerHTML = `<div class="center"><div class="say">Circle one</div><div class="sub">the take that goes on air · not your own</div>
        <div class="vote">${Array.from({ length: S.nTakes }, (_, k) => `<button data-k="${k}" class="${S.mine === k ? 'on' : ''}" ${k === S.own ? 'disabled' : ''}><svg viewBox="0 0 100 100"><ellipse cx="50" cy="52" rx="44" ry="38" transform="rotate(-8 50 52)"/></svg>${k + 1}</button>`).join('')}</div>
        <div class="sub">${(S.crowd || []).map((c, k) => c ? `take ${k + 1}: ${esc(c)}` : '').filter(Boolean).join(' · ')}</div><div class="sub">${S.own >= 0 ? 'Take ' + (S.own + 1) + ' is yours.' : ''} ${S.mine != null ? 'Circled take ' + (S.mine + 1) + '.' : ''}</div></div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', k: +b.dataset.k }); }); } } };
    if (P === 'result') return look('result' + S.win, 'On air:<br>take ' + (S.win + 1), esc(S.winBy) + (S.gain ? ' · you +' + S.gain + ' ★' : ''), S.gain ? S.you.av : S.winAv == null ? 'house' : S.winAv, S.gain ? 'cheer' : '');
    if (P === 'wrap') return look('wrap', 'That’s a<br>wrap', 'you placed #' + S.rank + ' of ' + S.of + ' · ' + S.you.score + ' ★' + (S.awards && S.awards.length ? '<br>' + S.awards.map(esc).join(' · ') : ''), S.you.av, S.rank === 1 ? 'cheer' : 'bow');
    const st = P === 'call' ? 'Day ' + S.day + ' · ' + esc(S.scene || '') + ' · plan your turn' + (S.youNext ? ' · you’re first' : '')
      : P === 'slate' || P === 'air' ? esc(S.onAir ? S.onAir.name : '') + (P === 'slate' ? ' is getting ready' : ' is on air') + ' · throw something'
      : P === 'pass' ? (S.nextYou ? 'You get the remote next · tap when you’re ready' : 'The remote passes to ' + esc(S.onAir ? S.onAir.name : ''))
      : P === 'house' ? 'The house rolled its own take' : P === 'dailies' ? 'Dailies · take ' + S.daily + ' of ' + S.nTakes + ' · nobody knows whose · throw something'
      : P === 'continuity' ? 'Continuity · what changed is on the TV · tomorrow it’s true' : '';
    const tab = P === 'call' ? 'plan' : (P === 'air' || P === 'dailies' || P === 'slate') ? 'throw' : null;
    return { key: P + (P === 'dailies' ? S.daily : ''), status: st, tab, tabs: P === 'continuity' ? ['throw', 'me'] : ['throw', planTab, 'me'] };
  }
  // ---- the remote: tap a channel to cut (on the next beat); NEXT plays the plan; drawn once and patched in place
  function remote(S, api) {
    const M = S.mineCh;
    return { key: 'r' + S.phase + plan.length, render(el) {
      planAt = Math.min(planAt, plan.length);
      el.innerHTML = `<div class="rhead"><span id="rs"></span><span id="rt"></span></div><div class="beats" id="beats">${'<i></i>'.repeat(NB)}</div>
        ${plan.length ? `<button class="btn next" id="nextB"></button>` : ''}
        <div class="lbl">picture · tap to cut (on the beat)</div><div class="tiles">${M.pics.map((c, i) => `<button class="tile" data-c="${i}"><img alt="" src="${esc(c.th)}"><span>${pad(c.no)} ${esc(c.name)}</span></button>`).join('')}</div>
        <div class="lbl">sound</div><div class="snds">${M.snds.map((c, i) => `<button class="btn" data-s="${i}">${pad(c.no)} ${esc(c.name)}</button>`).join('')}</div>
        <div class="tools"><button class="btn" data-b="slip-">◀ slip</button><button class="btn" data-b="mute">mute</button><button class="btn" data-b="hold">hold</button><button class="btn" data-b="slip+">slip ▶</button></div>
        <button class="btn rec" data-b="rec" ${S.phase === 'air' ? '' : 'disabled'}>● REC</button>`;
      el.querySelectorAll('[data-c]').forEach(b => b.onclick = () => { api.buzz(); b.classList.add('q'); api.send({ t: 'btn', b: 'ch', v: +b.dataset.c }); });
      el.querySelectorAll('[data-s]').forEach(b => b.onclick = () => { api.buzz(); b.classList.add('q'); api.send({ t: 'btn', b: 'sndto', v: +b.dataset.s }); });
      el.querySelectorAll('[data-b]').forEach(b => b.onclick = () => { api.buzz(b.dataset.b === 'rec' ? 40 : 12); api.act(b, 'hit', 200); api.send({ t: 'btn', b: b.dataset.b }); });
      const nb = el.querySelector('#nextB'); if (nb) nb.onclick = () => { if (planAt >= plan.length) return; api.buzz(); const s = plan[planAt++]; api.send(s.k === 'cam' ? { t: 'btn', b: 'ch', v: s.v } : { t: 'btn', b: 'sndto', v: s.v }); const t = el.querySelector(s.k === 'cam' ? `[data-c="${s.v}"]` : `[data-s="${s.v}"]`); if (t) t.classList.add('q'); this.patch(el, api); };
      base = 0; lastBeat = -1; this.patch(el, api); tick(el, api);
    }, patch(el) { const St = api.S(), A = St.air; if (!A) return;
      el.querySelectorAll('[data-c]').forEach(b => { const on = +b.dataset.c === A.cam; b.classList.toggle('on', on); if (on) b.classList.remove('q'); });
      el.querySelectorAll('[data-s]').forEach(b => { const on = +b.dataset.s === A.snd; b.classList.toggle('on', on); if (on) b.classList.remove('q'); });
      const mu = el.querySelector('[data-b="mute"]'), ho = el.querySelector('[data-b="hold"]'); if (mu) mu.classList.toggle('on', !!A.mute); if (ho) ho.classList.toggle('on', !!A.hold);
      const rec = el.querySelector('[data-b="rec"]'); if (rec) rec.disabled = St.phase !== 'air';
      const nb = el.querySelector('#nextB'); if (nb) { const s = plan[planAt], Mx = St.mineCh; nb.disabled = !s; nb.innerHTML = s ? `NEXT ▸ ${s.k === 'cam' ? pad(Mx.pics[s.v].no) + ' ' + esc(Mx.pics[s.v].name) : '♪ ' + esc(Mx.snds[s.v].name.slice(0, 16))} <small>(${planAt + 1}/${plan.length})</small>` : 'plan played · cut freely'; }
      const rs = el.querySelector('#rs'); if (rs) rs.textContent = St.phase === 'air' ? 'ON AIR' + (A.slip ? ' · slip ' + (A.slip > 0 ? '+' : '') + A.slip + 's' : '') : 'READY · your first shot is lit';
      if (St.phase === 'air') { const b = performance.now() - A.t * 1000; if (!base || Math.abs(b - base) > 250) base = b; } } };
  }
  function tick(el, api) { cancelAnimationFrame(raf); const beats = el.querySelector('#beats'), rt = el.querySelector('#rt');
    const frame = () => { if (!document.body.contains(beats)) return; const St = api.S();
      if (St.phase === 'air' && base) { const t = (performance.now() - base) / 1000, bi = Math.min(NB - 1, Math.floor(t / BEAT)); rt.textContent = Math.max(0, MAXT - t).toFixed(1);
        if (bi !== lastBeat) { lastBeat = bi; [...beats.children].forEach((x, i) => { x.className = i < bi ? 'past' : i === bi ? 'now' : ''; }); if (bi % 4 === 0) api.buzz(10); } } else rt.textContent = '';
      raf = requestAnimationFrame(frame); };
    frame(); }

  Party.games.calltime = { title: 'Call Time', blurb: 'make today’s movie with whatever survived yesterday', options: [{ k: 'days', name: 'shooting days', values: [2, 3, 4, 6], def: 3 }], host, phone };
})();
