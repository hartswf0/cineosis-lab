/* CINEOSIS LIVE: the room directs live television from the archive. Atari's one stick and one button; Adobe's real edit.
   A song plays (archive music with a known tempo). Every phone is a gamepad holding one channel of the archive: the stick ↕
   changes channel (each step goes to a neighbour of where you are), ‹› picks the moment in the clip. The big red button CUTS
   the program to your channel; holding it DISSOLVES for as long as you hold. The stand shows the program, everyone's monitor,
   the timeline filling up, and the score: time on air (up to a point: hogging stops paying), cuts on the beat, and the room's
   roses (tomatoes cost) during the replay. After each reel the clean edit replays and joins the film: real in-points, cut
   times, dissolves and the song, which opens in The Cut and leaves as a link. Nothing to read: the stand shows how to play.
   Built on markov/shared.js (the archive, CLIP neighbours), tools/sound-kinds.json (which clips are music and their tempo). */
(function () {
  const { esc, rnd, pick, shuffle, mini } = Party;
  const NEON = ['#ff4fa3', '#3aa0ff', '#32d17c', '#ffc93c', '#b06bff', '#ff7a3d', '#2fe0d6', '#ff5e5e', '#9bdc3a', '#ff9de1', '#7ea8ff', '#e8e8e8'];
  const col = av => NEON[av % NEON.length], HOUSE = '#6f7a8a';
  const thumbOf = u => u ? u.replace('/clips/', '/thumbnails/').replace(/\.mp4.*$/, '.jpg') : '';
  const HOG = 6, COOL = .8, MAXMIX = 2;
  const PAD = '<svg viewBox="0 0 80 80"><circle cx="40" cy="40" r="37" fill="none" stroke="currentColor" stroke-width="3" opacity=".5"/><path d="M40 8 L48 20 H32Z M40 72 L48 60 H32Z M8 40 L20 32 V48Z M72 40 L60 32 V48Z" fill="currentColor"/><circle cx="40" cy="40" r="13" fill="currentColor"/></svg>';

  function host(H) {
    const $ = s => document.querySelector(s), P = H.P, ARC = window.SH;
    H.show(null); H.slate(''); H.cap(''); $('#host').classList.add('cin', 'live');
    let root$ = $('#livev'); if (!root$) { root$ = document.createElement('div'); root$.id = 'livev'; $('#vids').after(root$); } root$.hidden = false;
    root$.innerHTML = `<div class="lhead" id="lHead"></div><div class="lprog" id="lProg"><video class="ll" muted playsinline preload="auto"></video><video class="ll" muted playsinline preload="auto"></video><div class="lair" id="lAir"></div><div class="lpops" id="lPops"></div><div class="lcount" id="lCount"></div></div>
      <div class="lmons" id="lMons"></div><div class="ltl"><div class="ltrack" id="lTrack"></div><i class="lph" id="lPh"></i></div><div class="lattract" id="lAttract"></div>`;
    const lay = [...root$.querySelectorAll('.ll')], bed = H.AP[0];
    const G = { ready: false, why: 'opening the archive', phase: 'load', reel: 0, len: 30, t0: 0, song: null, log: [], on: null, onAt: 0, air: 0, lastCut: -9, ch: {}, pts: {}, film: [], replay: null, at: -1, press: {} };
    window.__live = G;
    let LIB = null, MUS = [], top = 0, tick = 0, timers = [];
    const players = () => H.players.filter(p => !p.house);
    const shot = k => LIB.shots[k], nameOf = id => (P(id) || {}).name || 'the archive', colOf = id => P(id) ? col(P(id).av) : HOUSE;
    const later = (f, ms) => timers.push(setTimeout(f, ms));
    Promise.all([ARC.load({ light: true }), fetch('tools/sound-kinds.json').then(r => r.json())]).then(([d, sk]) => { LIB = d.LIB; const byId = new Map(LIB.shots.map((s, i) => [s.id, i]));
      for (const id in sk.clips) { const v = sk.clips[id], k = byId.get(id); if (k != null && v[0] === 'music' && v[2] && shot(k).dur >= 8) MUS.push({ k, bpm: v[2] }); }
      G.ready = true; G.why = ''; tune(); }).catch(e => { G.why = 'the archive did not load: ' + e.message; draw(); });
    // ---- channels: each step goes to a neighbour of where you are; the room's favourites pull a little
    const norm = v => { let n = 0; for (let j = 0; j < v.length; j++) n += v[j] * v[j]; n = Math.sqrt(n) || 1; for (let j = 0; j < v.length; j++) v[j] /= n; return v; };
    const vecK = k => { const o = new Float32Array(512), r = k * 512; for (let j = 0; j < 512; j++) o[j] = LIB.q[r + j]; return norm(o); };
    const isArc = k => shot(k) && shot(k).kind !== 'presence' && shot(k).dur >= 2;
    const fav = [];
    function anyShot() { let k; do { k = Math.floor(rnd() * LIB.n); } while (!isArc(k)); return k; }
    function ring(c) { const v = vecK(c.k); fav.forEach(f => { for (let j = 0; j < 512; j++) v[j] += f.v[j] * f.w; }); const s = LIB.sims(v), seen = new Set([shot(c.k).src]), idx = [];
      for (let i = 0; i < s.length; i++) if (isArc(i)) idx.push(i); idx.sort((a, b) => s[b] - s[a]); const out = [];
      for (const k of idx.slice(1 + Math.floor(rnd() * 8), 260)) { if (seen.has(shot(k).src)) continue; seen.add(shot(k).src); out.push(k); if (out.length >= 5) break; } c.ring = out; }
    function chan(id) { let c = G.ch[id]; if (!c) { c = G.ch[id] = { k: anyShot(), in: 0, hist: [], ready: false }; c.in = startIn(c.k); ring(c); } return c; }
    const startIn = k => Math.max(0, Math.min((shot(k).dur || 4) - 3, (shot(k).in || 0) - 1));
    // ---- a reel: tune in, count down, go live, replay, score
    function tune() { stopAll(); H.crowdShow && H.crowdShow(null); G.reel++; G.phase = 'tune'; G.log = []; G.on = null; G.pts = {}; G.press = {}; players().forEach(p => { const c = chan(p.id); c.ready = false; });
      const m = pick(MUS.filter(x => !G.film.some(f => f.song === x.k))) || pick(MUS); G.song = { k: m.k, bpm: m.bpm, u: shot(m.k).video, title: (shot(m.k).title || '').slice(0, 40), dur: shot(m.k).dur };
      G.len = Math.round(Math.max(20, Math.min(30, G.song.dur))); bed.pause(); bed.src = G.song.u; bed.loop = true; bed.volume = .85; bed.load();
      lay.forEach(v => { v.style.opacity = 0; v.pause(); }); attract(true); draw(); }
    function go() { if (G.phase !== 'tune') return; G.phase = 'count'; attract(false); let n = 3; const cd = root$.querySelector('#lCount');
      const step = () => { if (G.phase !== 'count') return; if (n) { cd.textContent = n; cd.className = 'lcount on'; beep(440, .08); n--; later(step, 800); } else { cd.className = 'lcount'; live(); } }; step(); draw(); }
    function live() { G.phase = 'live'; G.t0 = performance.now(); G.lastCut = -9; try { bed.currentTime = 0; } catch (e) { } bed.play().catch(() => { });
      const first = players()[Math.floor(rnd() * Math.max(1, players().length))]; if (first) take(first.id, 0, 0, true);
      clearInterval(tick); tick = setInterval(frame, 100); draw(); }
    const now = () => (performance.now() - G.t0) / 1000;
    function frame() { if (G.phase !== 'live') return; const t = now();
      if (G.on) { const held = t - G.onAt; if (held <= HOG) { G.pts[G.on] = (G.pts[G.on] || 0) + .1; } root$.querySelector('#lAir').classList.toggle('hog', held > HOG); }
      const beat = 60 / G.song.bpm, ph = (t % beat) / beat; root$.classList.toggle('beat', ph < .18);
      root$.querySelector('#lPh').style.left = Math.min(100, t / G.len * 100) + '%'; drawHead(t); drawTrack(t);
      if (t >= G.len) end(); }
    // the cut: tap = cut at the press; hold = dissolve for as long as the hold
    function take(id, t, mix, quiet) { const c = chan(id), u = shot(c.k).video, inn = c.in, vNew = lay.find(v => !v.dataset.on) || lay[0], vOld = lay.find(v => v !== vNew);
      vNew.dataset.on = '1'; if (vOld) delete vOld.dataset.on; if (vNew.dataset.u !== u) { vNew.dataset.u = u; vNew.src = u; } try { vNew.currentTime = inn; } catch (e) { } vNew.muted = false; vNew.volume = .25; vNew.play().catch(() => { });
      vNew.style.zIndex = 2; if (vOld) vOld.style.zIndex = 1; vNew.style.transition = mix ? `opacity ${mix}s linear` : 'none'; requestAnimationFrame(() => { vNew.style.opacity = 1; if (vOld) { vOld.style.transition = mix ? `opacity ${mix}s linear` : 'none'; if (!mix) vOld.style.opacity = 0; else later(() => { if (!vOld.dataset.on) vOld.style.opacity = 0; }, mix * 1000); } });
      G.log.push({ t, id, k: c.k, in: inn, mix: mix || 0 }); G.on = id; G.onAt = t; G.lastCut = t;
      const ap = root$.querySelector('#lAir'); ap.style.setProperty('--c', colOf(id)); ap.innerHTML = `<b>ON AIR</b>${P(id) ? mini(P(id).av) : ''}`;
      if (!quiet) { const beat = 60 / G.song.bpm, off = Math.min(t % beat, beat - (t % beat)); let gain = 1; if (off < .12) { gain += 3; pop(id, '+3 ON THE BEAT'); beep(880, .06); } else { pop(id, '+1 CUT'); beep(660, .04); } if (mix > .3) { gain += 1; pop(id, '+1 MIX', 1); } G.pts[id] = (G.pts[id] || 0) + gain; H.act(id, 'hop', 820); }
      drawMons(); H.broadcast(); }
    function down(p) { if (G.phase === 'tune') { const c = chan(p.id); c.ready = !c.ready; H.act(p.id, 'hop', 820); if (players().length && players().every(q => chan(q.id).ready)) later(go, 600); draw(); return; }
      if (G.phase === 'scores') { tune(); return; }
      if (G.phase !== 'live') return; const t = now(); if (G.on === p.id) { H.send(p, { t: 'buzz', why: 'onair' }); return; } if (t - G.lastCut < COOL) { H.send(p, { t: 'buzz', why: 'soon' }); return; }
      G.press[p.id] = t; const c = chan(p.id), vNew = lay.find(v => !v.dataset.on) || lay[0], u = shot(c.k).video; if (vNew.dataset.u !== u) { vNew.dataset.u = u; vNew.src = u; } try { vNew.currentTime = c.in; } catch (e) { }
      later(() => { if (G.press[p.id] === t) up(p); }, MAXMIX * 1000); }
    function up(p) { const t0 = G.press[p.id]; if (t0 == null || G.phase !== 'live') return; delete G.press[p.id]; const held = now() - t0; take(p.id, t0, held < .25 ? 0 : Math.min(MAXMIX, held)); }
    function end() { clearInterval(tick); G.phase = 'replay'; bed.pause(); root$.classList.remove('beat');
      const pieces = G.log.map((e, i) => { const nx = G.log[i + 1], len = (nx ? nx.t : G.len) - e.t; return { id: G.reel * 1000 + i, k: e.k, in: e.in, len, mix: e.mix, by: e.id, at: e.t, r: {} }; }).filter(p => p.len > .2);
      G.cur = { reel: G.reel, song: G.song, len: G.len, pieces }; replay(G.cur, () => { score(); }); draw(); }
    function replay(R, done) { stopProg(); G.replay = R; G.at = -1; try { bed.src !== R.song.u && (bed.src = R.song.u); bed.currentTime = 0; } catch (e) { } bed.play().catch(() => { }); const t0 = performance.now();
      R.pieces.forEach((p, i) => later(() => { if (G.replay !== R) return; G.at = i; const vNew = lay[i % 2], vOld = lay[(i + 1) % 2], u = shot(p.k).video; if (vNew.dataset.u !== u) { vNew.dataset.u = u; vNew.src = u; } try { vNew.currentTime = p.in; } catch (e) { } vNew.play().catch(() => { });
        vNew.style.zIndex = 2; vOld.style.zIndex = 1; vNew.style.transition = p.mix ? `opacity ${p.mix}s linear` : 'none'; requestAnimationFrame(() => { vNew.style.opacity = 1; if (!p.mix) vOld.style.opacity = 0; else later(() => vOld.style.opacity = 0, p.mix * 1000); });
        const ap = root$.querySelector('#lAir'); ap.style.setProperty('--c', colOf(p.by)); ap.innerHTML = `<b>REPLAY</b>${P(p.by) ? mini(P(p.by).av) : ''}`; H.act(p.by, 'hop', 820); H.broadcast(); }, p.at * 1000));
      const sweep = setInterval(() => { if (G.replay !== R) return clearInterval(sweep); const t = (performance.now() - t0) / 1000; root$.querySelector('#lPh').style.left = Math.min(100, t / R.len * 100) + '%'; drawHead(t); }, 100); timers.push(sweep);
      later(() => { if (G.replay !== R) return; G.replay = null; G.at = -1; bed.pause(); done && done(); }, R.len * 1000 + 300); }
    function score() { const R = G.cur; R.pieces.forEach(p => { const r = (p.r.rose || 0) * 2 + (p.r.bravo || 0) * 3 - (p.r.tomato || 0) - (p.r.cut || 0); if (r) G.pts[p.by] = (G.pts[p.by] || 0) + r; if (r > 0) fav.push({ v: vecK(p.k), w: .3 }); });
      while (fav.length > 8) fav.shift(); G.film.push({ reel: R.reel, song: R.song.k, title: R.song.title, songU: R.song.u, len: R.len, pieces: R.pieces });
      Object.entries(G.pts).forEach(([id, v]) => { const p = P(id); if (p) p.score = (p.score || 0) + Math.round(v); }); G.phase = 'scores'; H.syncCrew(); draw(); }
    function stopProg() { timers.forEach(t => { clearTimeout(t); clearInterval(t); }); timers = []; G.replay = null; }
    function stopAll() { stopProg(); clearInterval(tick); bed.pause(); }
    // ---- the stand
    const pops$ = () => root$.querySelector('#lPops');
    function pop(id, text, dy = 0) { const d = document.createElement('div'); d.className = 'lpop'; d.style.setProperty('--c', colOf(id)); d.style.top = (40 + dy * 12) + '%'; d.textContent = text; pops$().append(d); setTimeout(() => d.remove(), 1400); }
    let AC = null; function beep(f, d) { try { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); const o = AC.createOscillator(), g = AC.createGain(); o.type = 'square'; o.frequency.value = f; g.gain.value = .05; o.connect(g); g.connect(AC.destination); o.start(); o.stop(AC.currentTime + d); } catch (e) { } }
    function attract(on) { const A = root$.querySelector('#lAttract'); A.classList.toggle('on', !!on); A.innerHTML = on ? `<div class="la1"><span class="pad">${PAD}<i class="v">↕</i></span><b>channel</b></div><div class="la1"><span class="pad h">${PAD}<i class="h">‹ ›</i></span><b>the moment</b></div><div class="la1"><span class="btn1"></span><b>cut</b></div><div class="la1"><span class="btn1 hold"></span><b>hold = mix</b></div>` : ''; }
    const mmss = t => Math.floor(t / 60) + ':' + String(Math.floor(t % 60)).padStart(2, '0');
    function drawHead(t) { const ph = G.phase, rec = ph === 'live';
      root$.querySelector('#lHead').innerHTML = `<b>LIVE</b><span class="reel">REEL ${G.reel}</span><span class="rec ${rec ? 'on' : ''}">● ${rec ? 'REC' : ph === 'replay' ? 'REPLAY' : ph === 'scores' ? 'SCORES' : 'TUNE IN'}</span><span class="tm">${mmss(t || 0)} / ${mmss(G.len)}</span><span class="song">♪ ${esc(G.song ? G.song.title : '')}</span><i class="beatlamp"></i>`; }
    function drawTrack(t) { const T = root$.querySelector('#lTrack'), L = G.phase === 'replay' || G.phase === 'scores' ? (G.cur ? G.cur.pieces.map(p => ({ t: p.at, id: p.by, mix: p.mix })) : []) : G.log;
      T.innerHTML = L.map((e, i) => { const nx = L[i + 1], end = nx ? nx.t : (G.phase === 'live' ? t : G.len); return `<span style="left:${e.t / G.len * 100}%;width:${Math.max(.3, (end - e.t) / G.len * 100)}%;--c:${colOf(e.id)}" class="${e.mix ? 'mix' : ''}"></span>`; }).join(''); }
    function drawMons() { const M = root$.querySelector('#lMons'), ids = players().map(p => p.id);
      const have = new Map([...M.children].map(d => [d.dataset.id, d])); ids.forEach(id => { let d = have.get(id); have.delete(id); const c = chan(id);
        if (!d) { d = document.createElement('div'); d.className = 'lmon'; d.dataset.id = id; d.innerHTML = '<video muted playsinline loop preload="auto"></video><b></b><i class="tally"></i>'; M.append(d); }
        const v = d.querySelector('video'), u = shot(c.k).video; if (v.dataset.u !== u) { v.dataset.u = u; v.src = u; v.poster = thumbOf(u); } if (Math.abs((v.dataset.in || 0) - c.in) > .05) { v.dataset.in = c.in; try { v.currentTime = c.in; } catch (e) { } } v.play().catch(() => { });
        if (!v._seg) { v._seg = 1; v.addEventListener('timeupdate', () => { const i = +v.dataset.in || 0; if (v.currentTime > i + 3.2 || v.currentTime < i - .2) try { v.currentTime = i; } catch (e) { } }); }
        d.style.setProperty('--c', colOf(id)); d.classList.toggle('on', G.on === id && G.phase === 'live'); d.classList.toggle('ready', G.phase === 'tune' && c.ready);
        d.querySelector('b').innerHTML = `${P(id) ? mini(P(id).av) : ''}<span>${Math.round(G.pts[id] || 0)}</span>`; });
      have.forEach(d => d.remove()); }
    function drawSide() { const ph = G.phase, rows = players().slice().sort((a, b) => (b.score || 0) + (G.pts[b.id] || 0) - (a.score || 0) - (G.pts[a.id] || 0)).map(p => `<div class="lrow ${G.on === p.id && ph === 'live' ? 'on' : ''}" style="--c:${col(p.av)}"><span class="m">${mini(p.av)}</span><b>${esc(p.name)}</b><span class="pts">${String(Math.round((p.score || 0) + (ph === 'scores' ? 0 : G.pts[p.id] || 0))).padStart(4, '0')}</span>${ph === 'tune' && G.ready ? `<i>${chan(p.id).ready ? '✓' : ''}</i>` : ''}</div>`).join('');
      H.side(`<div class="ph">Live <small>${G.film.length} reels · ${G.film.reduce((a, f) => a + f.pieces.length, 0)} cuts</small></div>
        <div class="row" style="margin-bottom:6px"><button class="btn chip" id="lGo">${ph === 'tune' ? '● go live' : ph === 'scores' ? 'next reel ▸' : ph === 'live' ? '■ stop' : '…'}</button><button class="btn chip" id="lFilm" ${G.film.length ? '' : 'disabled'}>▶ the film</button><button class="btn chip" id="lCut" ${G.film.length ? '' : 'disabled'}>edit the film</button></div>
        ${G.ready ? '' : `<div class="hint">${esc(G.why)}</div>`}<div class="lrows">${rows}</div>`, 'live');
      $('#lGo').onclick = () => { if (G.phase === 'tune') go(); else if (G.phase === 'scores') tune(); else if (G.phase === 'live') end(); };
      $('#lFilm').onclick = () => playFilm(); $('#lCut').onclick = () => { stopAll(); H.seed = toFilm(); H.playGame('cut'); }; }
    function playFilm() { stopAll(); let i = 0; const nx = () => { const R = G.film[i++]; if (!R) { draw(); return; } replay({ reel: R.reel, song: { u: R.songU }, len: R.len, pieces: R.pieces }, nx); }; G.phase = 'scores'; nx(); }
    function draw() { if (!G.ready) { H.slate(H.card(`<div class="big">Live<small>${esc(G.why)}</small></div>`, 'night')); drawSide(); H.broadcast(); return; } H.slate(''); drawHead(G.phase === 'live' ? now() : 0); drawMons(); drawTrack(G.phase === 'live' ? now() : 0); drawSide(); H.syncCrew(); H.broadcast(); }
    function toFilm() { const F = Cut.blank('Cineosis Live'); G.film.forEach(R => { let first = null; R.pieces.forEach(p => { const s = shot(p.k), c = Cut.shot(s.video, p.in, Math.min(s.dur || p.in + p.len, p.in + p.len), { d: s.dur || null, by: p.by, label: (s.title || '').slice(0, 30) }); if (p.mix > .3) c.tr = 'dissolve'; F.clips.push(c); if (!first) first = c; });
        if (first) F.sounds.push(Cut.music(first.id, R.songU, 0, R.len, { vol: .85 })); }); return F; }
    // ---- the gamepads
    function onMsg(p, m) { if (!G.ready) return; const c = chan(p.id);
      if (m.t === 'down') return down(p); if (m.t === 'up') return up(p);
      if (m.t === 'stick') { if (G.on === p.id && G.phase === 'live') { H.send(p, { t: 'buzz', why: 'onair' }); return; }
        if (m.d === 'up') { c.hist.push(c.k); if (c.hist.length > 20) c.hist.shift(); c.k = c.ring[Math.floor(rnd() * Math.min(3, c.ring.length))] || anyShot(); c.in = startIn(c.k); ring(c); }
        else if (m.d === 'down') { if (c.hist.length) { c.k = c.hist.pop(); c.in = startIn(c.k); ring(c); } }
        else if (m.d === 'left' || m.d === 'right') { const dur = shot(c.k).dur || 4; c.in = Math.max(0, Math.min(dur - 1, c.in + (m.d === 'right' ? 1 : -1) * (m.fast ? 1.5 : .5))); }
        drawMons(); H.broadcast(); return; } }
    function stateFor(p) { const c = G.ready ? chan(p.id) : null, cur = G.replay && G.at >= 0 ? G.replay.pieces[G.at] : null;
      return { phase: 'live', me: p.id, ready: G.ready, ph: G.phase, reel: G.reel, on: G.on === p.id && G.phase === 'live', onC: G.on ? colOf(G.on) : '', len: G.len, t0: G.phase === 'live' ? Date.now() - (performance.now() - G.t0) : 0,
        ch: c ? { v: shot(c.k).video, th: thumbOf(shot(c.k).video), in: c.in, dur: shot(c.k).dur, ready: c.ready } : null, pts: Math.round(G.pts[p.id] || 0), c: col((P(p.id) || {}).av || 0),
        now: cur ? { by: nameOf(cur.by), c: colOf(cur.by) } : null }; }
    draw();
    return { stateFor, draw, onMsg, onJoin: p => { if (G.ready) chan(p.id); draw(); },
      crowdTarget: () => G.replay && G.at >= 0 ? G.replay.pieces[G.at] : null, performer: () => G.replay && G.at >= 0 ? G.replay.pieces[G.at].by : (G.phase === 'live' ? G.on : null),
      stop() { stopAll(); root$.hidden = true; root$.innerHTML = ''; $('#host').classList.remove('cin', 'live'); } };
  }

  // ======================================================================= the phone: a gamepad
  const L = { key: '', rep: 0, dir: '', held: false, vid: null };
  function phone(S, api) {
    if (S.phase !== 'live') return null; L.S = S;
    const take = {
      key: 'live' + (S.ready ? 1 : 0),
      render(el) { el.innerHTML = `<div class="gp"><div class="gmon" id="gMon"><video id="gV" muted playsinline loop preload="auto"></video><i class="glamp" id="gLamp"></i><b class="gpts" id="gPts"></b><span class="gmsg" id="gMsg"></span></div>
          <div class="gpad" id="gPad">${PAD}<i class="gnub" id="gNub"></i></div><button class="gfire" id="gFire" aria-label="cut"><span></span></button></div>`;
        wire(el, api); take.patch(el, api); },
      patch(el) { const S = L.S, v = el.querySelector('#gV'), c = S.ch;
        if (c) { if (v.dataset.u !== c.v) { v.dataset.u = c.v; v.src = c.v; v.poster = c.th; } if (Math.abs((+v.dataset.in || 0) - c.in) > .05 || !v.dataset.in) { v.dataset.in = c.in; try { v.currentTime = c.in; } catch (e) { } } v.play().catch(() => { }); }
        el.querySelector('#gMon').classList.toggle('on', !!S.on); el.querySelector('#gMon').style.setProperty('--c', S.c);
        el.querySelector('#gPts').textContent = String(S.pts).padStart(4, '0');
        const msg = S.ph === 'tune' ? (c && c.ready ? 'READY ✓' : 'find a shot · press ● when ready') : S.ph === 'count' ? 'GET READY' : S.ph === 'live' ? (S.on ? 'ON AIR' : '● to cut · hold to mix') : S.ph === 'replay' ? (S.now ? 'REPLAY · ' + S.now.by : 'REPLAY') : S.ph === 'scores' ? '● next reel' : '';
        el.querySelector('#gMsg').textContent = msg; el.querySelector('#gFire').classList.toggle('ready', S.ph === 'tune' && !!(c && c.ready)); el.querySelector('#gFire').classList.toggle('dim', !!S.on); }
    };
    function wire(el, api) { const v = el.querySelector('#gV');
      v.addEventListener('timeupdate', () => { const i = +v.dataset.in || 0; if (v.currentTime > i + 3.2 || v.currentTime < i - .2) try { v.currentTime = i; } catch (e) { } });
      // the stick: drag from the centre; ↕ channel, ‹› the moment; holding a direction repeats it, faster further out
      const pad = el.querySelector('#gPad'), nub = el.querySelector('#gNub'); let pid = null;
      const dirOf = e => { const r = pad.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2), R = r.width / 2, d = Math.hypot(dx, dy);
        nub.style.transform = `translate(${Math.max(-R * .6, Math.min(R * .6, dx))}px,${Math.max(-R * .6, Math.min(R * .6, dy))}px)`; if (d < R * .28) return ['', false]; return [Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up'), d > R * .75]; };
      const send = (d, fast) => { api.buzz(8); api.send({ t: 'stick', d, fast: fast ? 1 : 0 }); };
      const loop = () => { clearTimeout(L.rep); if (!L.dir) return; send(L.dir, L.fast); L.rep = setTimeout(loop, L.dir === 'up' || L.dir === 'down' ? 650 : (L.fast ? 160 : 320)); };
      pad.onpointerdown = e => { e.preventDefault(); pid = e.pointerId; try { pad.setPointerCapture(pid); } catch (x) { } const [d, f] = dirOf(e); L.fast = f; if (d) { L.dir = d; loop(); } };
      pad.onpointermove = e => { if (e.pointerId !== pid) return; const [d, f] = dirOf(e); L.fast = f; if (d !== L.dir) { L.dir = d; loop(); } };
      const rel = e => { if (e.pointerId !== pid) return; pid = null; L.dir = ''; clearTimeout(L.rep); nub.style.transform = ''; };
      pad.onpointerup = rel; pad.onpointercancel = rel;
      // the button: press = cut; hold = mix
      const fire = el.querySelector('#gFire');
      fire.onpointerdown = e => { e.preventDefault(); try { fire.setPointerCapture(e.pointerId); } catch (x) { } fire.classList.add('down'); api.buzz(30); api.send({ t: 'down' }); };
      const fup = () => { if (!fire.classList.contains('down')) return; fire.classList.remove('down'); api.send({ t: 'up' }); };
      fire.onpointerup = fup; fire.onpointercancel = fup; fire.oncontextmenu = e => e.preventDefault();
      Party.onHost = m => { if (m.t === 'buzz') { api.buzz([20, 40, 20]); const g = document.getElementById('gMsg'); if (g) { const was = g.textContent; g.textContent = m.why === 'soon' ? 'too soon!' : 'you’re on air'; g.classList.add('bad'); setTimeout(() => { g.classList.remove('bad'); }, 700); } } }; }
    return { key: take.key, status: null, cls: 'cinp livep', throws: true, takeover: take };
  }
  Party.games.live = { title: 'Cineosis Live', blurb: 'direct live television from the archive: your phone is a gamepad holding one channel. ↕ changes channel, ‹› picks the moment, the red button cuts to you, hold it to dissolve. A song plays; cut on the beat; the replay becomes the film.', options: [], host, phone };
})();
