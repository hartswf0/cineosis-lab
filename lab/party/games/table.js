/* THE TABLE (Cineosis Ludens) on the Party platform: the light table, played. Each round lays a START on the table (the film so far)
   and an END (the story's next beat). Every phone builds a bridge between them: up to three shots, chosen from a hand of six (the critic
   deals two that bridge well, two that might, two wild). Each card tapped on a phone lands on that player's branch on the stand, every seam
   scored live by the lab's cut critic (ludens/ludens.js), including the last seam into END. LOCK; the stand SCREENS every branch as a little
   film (START, the bridge, END); everyone votes for the best branch but their own (the machine builds one too); the winner is JOINED to our
   film, END becomes the next START, and the next beat is laid down. 2 points per vote, 1 for voting for the winner, 1 for the critic's best. */
(function () {
  const { esc, mini } = Party;
  const PCOL = ['#5acde6', '#f06e64', '#f0cd46', '#7fc28b', '#e3a0f0', '#f0a050', '#90b0ff', '#c0c0c0'];
  function host(H) {
    const $ = s => document.querySelector(s), L = Ludens; L.root = '';
    const G = { phase: 'loading', n: 0, film: [], hands: {}, lanes: {}, locked: {}, votes: {}, last: null };
    let pool = [], beats = [];
    H.slate(H.card(`<div class="big">The Table<small>laying out the shots…</small></div>`, 'house'));
    L.load().then(() => {
      const ch = H.opt.chapter === 'all' ? null : (L.chapters.find(c => c[1] === H.opt.chapter) || [])[0];
      pool = L.cards.filter(c => (H.opt.footage === 'all' || c.k === H.opt.footage) && (!ch || c.ch === ch)); if (pool.length < 40) pool = L.cards.slice();
      beats = L.beats(pool); if (beats.length < 3) beats = L.beats(L.cards);
      G.rounds = Math.min(H.opt.rounds, beats.length - 1); G.film = [{ c: beats[0].c, who: null, q: 1 }]; round();
    });
    const voters = () => H.players.filter(p => p.local || p.conn);
    const colOf = k => k === 'house' ? '#aa82f0' : PCOL[Math.max(0, H.players.findIndex(p => p.id === k)) % 8];
    const nameOf = k => k === 'house' ? 'the machine' : (H.players.find(p => p.id === k) || {}).name || '?';
    const initial = k => k === 'house' ? 'M' : (nameOf(k)[0] || '?').toUpperCase();
    const chain = lane => [G.start, ...lane, G.end];
    const seams = lane => { const c = chain(lane), out = []; for (let i = 1; i < c.length; i++) out.push(L.join(c[i - 1], c[i])); return out; };
    const score = lane => lane.length ? L.mean(seams(lane)) : 0;
    /* the deal: two that bridge START to END well, two that might, two wild; nothing already in the film, no card twice */
    function deal() {
      const used = new Set(G.film.map(f => f.c.id).concat([G.end.id])), sample = []; for (let k = 0; k < 600; k++) { const c = pool[Math.floor(Math.random() * pool.length)]; if (!used.has(c.id)) sample.push(c); }
      const ranked = [...new Set(sample)].map(c => ({ c, q: (L.join(G.start, c) + L.join(c, G.end)) / 2 })).sort((a, b) => b.q - a.q), taken = new Set();
      const take = list => { const l = list.slice().sort(() => Math.random() - .5); for (const x of l) if (!taken.has(x.c.id)) { taken.add(x.c.id); return x.c; } return list[0].c; };
      G.hands = {}; voters().forEach(p => { const top = ranked.slice(0, 50), mid = ranked.slice(50, 200), wild = ranked.slice(200); G.hands[p.id] = [take(top), take(top), take(mid), take(mid), take(wild), take(wild)].sort(() => Math.random() - .5); });
      let prev = G.start; G.house = []; for (let k = 0; k < 2; k++) { let best = null, bs = -1; for (const x of ranked.slice(0, 150)) { if (G.house.includes(x.c) || taken.has(x.c.id)) continue; const q = L.join(prev, x.c) + (k === 1 ? L.join(x.c, G.end) : 0); if (q > bs) { bs = q; best = x.c; } } if (best) { G.house.push(best); prev = best; } }
    }
    function round() {
      G.n++; if (G.n > G.rounds) return finale();
      G.start = G.film[G.film.length - 1].c; G.end = beats[Math.min(beats.length - 1, G.n)].c; G.endBeat = beats[Math.min(beats.length - 1, G.n)];
      G.phase = 'build'; G.lanes = {}; G.locked = {}; G.votes = {}; H.sign = {}; deal(); voters().forEach(p => G.lanes[p.id] = []); draw();
    }
    function play(pid, i) { if (G.phase !== 'build' || G.locked[pid]) return; const h = G.hands[pid], lane = G.lanes[pid]; if (!h || !h[i] || lane.length >= 3) return; lane.push(h[i]); h.splice(i, 1); G.flyTo = { pid, t: Date.now() }; H.act(pid, 'hit', 280); draw(); }
    function back(pid, j) { if (G.phase !== 'build' || G.locked[pid]) return; const lane = G.lanes[pid]; if (!lane || !lane[j]) return; G.hands[pid].push(lane[j]); lane.splice(j, 1); draw(); }
    function lock(pid) { if (G.phase !== 'build' || !(G.lanes[pid] || []).length) return; G.locked[pid] = true; H.sign[pid] = 'locked'; H.act(pid, 'hop', 600); if (voters().every(p => G.locked[p.id])) H.gate('Screen the branches', 'any', screen); draw(); }
    const branches = () => Object.keys(G.lanes).filter(k => G.lanes[k].length).concat(H.opt.machine === 'on' ? ['house'] : []);
    const laneOf = k => k === 'house' ? G.house : G.lanes[k];
    /* SCREEN: every branch plays as a little film on the stand, START, the bridge, END; then the vote */
    function screen() {
      G.phase = 'screen'; H.sign = {}; const list = branches(); let i = 0; draw();
      const nx = () => { if (G.phase !== 'screen') return; if (i >= list.length) { G.phase = 'vote'; G.playing = null; draw(); return; } const k = list[i++]; G.playing = k; draw(); playSeq(chain(laneOf(k)), nx, 1.6); };
      setTimeout(nx, 300); H.gate('Skip to the vote', 'any', () => { G.phase = 'vote'; G.playing = null; const v = $('#tbv'); if (v) { clearTimeout(v._t); v.pause(); } draw(); });
    }
    function vote(pid, v) { if (G.phase !== 'vote' || v === pid) return; G.votes[pid] = v; H.sign[pid] = 'voted'; H.act(pid, 'hit', 280); if (voters().every(p => G.votes[p.id] != null || branches().filter(k => k !== p.id).length === 0)) H.gate('Join the winner', 'any', join); draw(); }
    function join() {
      const cands = branches(); if (!cands.length) return round();
      const tally = k => Object.values(G.votes).filter(v => v === k).length, crit = cands.slice().sort((a, b) => score(laneOf(b)) - score(laneOf(a)))[0], win = cands.slice().sort((a, b) => tally(b) - tally(a) || score(laneOf(b)) - score(laneOf(a)))[0];
      G.gain = {}; const add = (id, g) => { const p = H.players.find(x => x.id === id); if (p && g) { p.score += g; G.gain[id] = (G.gain[id] || 0) + g; } };
      cands.forEach(k => add(k, tally(k) * 2)); add(crit, 1); Object.entries(G.votes).forEach(([pid, v]) => { if (v === win) add(pid, 1); });
      const lane = laneOf(win), sm = seams(lane); lane.forEach((c, j) => G.film.push({ c, who: win, q: sm[j] })); G.film.push({ c: G.end, who: 'beat', q: sm[sm.length - 1] });
      G.last = { win, crit, tallies: Object.fromEntries(cands.map(k => [k, tally(k)])) }; G.phase = 'join'; H.sign = {}; draw(); if (win !== 'house') H.act(win, 'cheer', 1600);
      H.gate(G.n >= G.rounds ? 'Watch our film' : 'Next beat', 'any', round);
    }
    function playSeq(list, then, each = 2.4) { setTimeout(() => { const v = $('#tbv'); if (!v) { then && then(); return; } let i = 0; const nx = () => { if (i >= list.length) { then && then(); return; } const c = list[i++]; G.cur = c; v.src = /^https?:/.test(c.m) ? c.m : L.root + c.m; v.onloadedmetadata = () => { v.currentTime = c.ss != null ? c.ss : Math.max(0, v.duration / 2 - each / 2); v.play().catch(() => { }); }; clearTimeout(v._t); v._t = setTimeout(nx, each * 1000); const t = $('#tbcap'); if (t) t.textContent = c.ti || ''; }; nx(); }, 120); }
    function finale() { G.phase = 'film'; H.sign = {}; draw(); playSeq(G.film.map(f => f.c), () => { G.phase = 'wrap'; draw(); }); H.gate('Skip', 'any', () => { G.phase = 'wrap'; const r = rank(); if (r[0]) H.act(r[0].id, 'cheer', 2200); draw(); }); }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    /* ---- the stand: the light table. START on the left, END (the story's next beat) on the right, every player's branch between them */
    const tint = q => `rgb(${L.tint(q)})`;
    function table() {
      const ks = G.phase === 'build' ? Object.keys(G.lanes) : branches(), n = Math.max(1, ks.length), rowH = 74 / n, cardW = Math.min(13, rowH * .82);
      const box = (c, x, y, w, extra = '') => `<div style="position:absolute;left:${x}cqw;top:${y}cqh;width:${w}cqw;aspect-ratio:16/9;border-radius:6px;background:#000 center/cover url('${esc(c.th)}');${extra}"></div>`;
      const sy = 50 - 15 * .5625 * 16 / 9 / 2, startEl = box(G.start, 2, 50 - 9, 16, 'outline:3px solid #ebe5d8') + `<div style="position:absolute;left:2cqw;top:${50 + 9.6}cqh;width:16cqw;font:600 1.9cqh 'IBM Plex Mono',monospace;color:#ebe5d8">START · ${esc((G.start.ti || '').slice(0, 26))}</div>`;
      const endEl = box(G.end, 82, 50 - 9, 16, 'outline:3px solid #f25a17') + `<div style="position:absolute;left:82cqw;top:${50 + 9.6}cqh;width:16cqw;font:600 1.9cqh 'IBM Plex Mono',monospace;color:#f25a17">END · ${esc(G.endBeat.act)} · ${esc((G.end.ti || '').slice(0, 22))}</div>`;
      let paths = '', rows = '';
      ks.forEach((k, r) => {
        const y = 13 + r * rowH + rowH / 2, lane = laneOf(k), sm = seams(lane), col = colOf(k), x0 = 28, play = G.playing === k, dim = G.playing && !play ? .35 : 1;
        paths += `<path d="M18 50 C 23 50, 23 ${y}, ${x0 - 2.5} ${y}" stroke="${col}" stroke-width="${play ? .6 : .35}" fill="none" opacity="${dim}"/><path d="M${x0 + 3 * (cardW + 1.2)} ${y} C 78 ${y}, 78 50, 82 50" stroke="${lane.length ? tint(sm[sm.length - 1]) : '#444'}" stroke-width="${play ? .6 : .35}" fill="none" stroke-dasharray="${lane.length ? '0' : '1 1'}" opacity="${dim}"/>`;
        rows += `<div style="position:absolute;left:${x0 - 4.6}cqw;top:${y}cqh;translate:0 -50%;width:3.6cqw;aspect-ratio:1;border-radius:50%;background:${col};display:flex;align-items:center;justify-content:center;font:700 2.2cqh 'Barlow Condensed',sans-serif;color:#0c0d0f;opacity:${dim}">${initial(k)}</div>`;
        for (let j = 0; j < 3; j++) { const c = lane[j], x = x0 + j * (cardW + 1.2), fresh = G.flyTo && G.flyTo.pid === k && j === lane.length - 1 && Date.now() - G.flyTo.t < 900;
          rows += c ? `<div style="position:absolute;left:${x}cqw;top:${y}cqh;translate:0 -50%;width:${cardW}cqw;aspect-ratio:16/9;border-radius:4px;background:#000 center/cover url('${esc(c.th)}');outline:2px solid ${col};opacity:${dim};${fresh ? 'animation:tbin .7s ease-out;' : ''}"></div><div style="position:absolute;left:${x - 1.1}cqw;top:${y}cqh;translate:0 -50%;width:1cqw;height:.7cqh;border-radius:2px;background:${tint(sm[j])};opacity:${dim}"></div>`
            : `<div style="position:absolute;left:${x}cqw;top:${y}cqh;translate:0 -50%;width:${cardW}cqw;aspect-ratio:16/9;border-radius:4px;border:1.5px dashed #3a3f46"></div>`; }
        rows += `<div style="position:absolute;left:${x0}cqw;top:${y + cardW * .5625 * 16 / 9 / 2 + .5}cqh;font:600 1.7cqh 'IBM Plex Mono',monospace;color:${col};opacity:${dim};white-space:nowrap">${esc(nameOf(k))} · ${lane.length ? 'bridge ' + Math.round(score(lane) * 100) : 'building'}${G.locked[k] || k === 'house' ? ' · LOCKED' : ''}${G.phase === 'vote' ? ' · ' + Object.values(G.votes).filter(v => v === k).length + ' votes' : ''}</div>`;
      });
      const strip = G.film.slice(-14).map(f => `<div style="width:5cqw;aspect-ratio:16/9;background:center/cover url('${esc(f.c.th)}');border-bottom:3px solid ${f.who === 'beat' || !f.who ? '#f25a17' : colOf(f.who)};border-radius:2px;flex:none"></div>`).join('');
      const screenEl = G.phase === 'screen' && G.playing ? `<div style="position:absolute;left:30cqw;top:4cqh;width:40cqw;z-index:3;background:#000;border-radius:6px;outline:3px solid ${colOf(G.playing)};overflow:hidden"><video id="tbv" muted playsinline style="width:100%;aspect-ratio:16/9;display:block;object-fit:cover"></video><div style="padding:.6cqh 1cqw;font:600 1.9cqh 'IBM Plex Mono',monospace;color:${colOf(G.playing)}">${esc(nameOf(G.playing))}’s branch · <span id="tbcap"></span></div></div>` : '';
      return `<style>@keyframes tbin{from{transform:translate(-40cqw,30cqh) scale(.3);opacity:0}to{transform:none;opacity:1}}</style><div style="position:relative;width:100%;height:100%;background:#f3efe7;color:#16171a;font-family:'IBM Plex Mono',monospace">
        <div style="position:absolute;left:2cqw;top:2cqh;display:flex;gap:.6cqw;align-items:center"><b style="font:700 2.6cqh 'Barlow Condensed',sans-serif;letter-spacing:.14em;color:#16171a">OUR FILM · ${G.film.length}</b>${strip}</div>
        <div style="position:absolute;right:2cqw;top:2cqh;font:700 2.6cqh 'Barlow Condensed',sans-serif;letter-spacing:.12em;color:#16171a">ROUND ${G.n}/${G.rounds} · ${G.phase === 'build' ? 'BUILD A BRIDGE' : G.phase === 'screen' ? 'SCREENING' : 'VOTE'}</div>
        <div style="position:absolute;inset:10cqh 1cqw 4cqh 1cqw;background:#0e1013;border-radius:14px"></div>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style="position:absolute;inset:0;width:100%;height:100%">${paths}</svg>${startEl}${endEl}${rows}${screenEl}
        <div style="position:absolute;left:3cqw;bottom:5cqh;font-size:1.8cqh;color:#858b93">${G.phase === 'build' ? 'On your phone: tap shots to bridge START to END (up to three). Each seam is scored as you build, the last one into END too. LOCK when it is right.' : G.phase === 'screen' ? 'Every branch plays as a film: START, the bridge, END.' : 'Vote on your phone for the best branch that is not yours.'} · lens: ${esc(L.V.lens)}</div></div>`;
    }
    function stand() {
      if (G.phase === 'build' || G.phase === 'screen' || G.phase === 'vote') return table();
      const head = G.film.slice(-14).map(f => `<div style="width:5cqw;aspect-ratio:16/9;background:center/cover url('${esc(f.c.th)}');border-bottom:3px solid ${f.who === 'beat' || !f.who ? '#f25a17' : colOf(f.who)};border-radius:2px;flex:none"></div>`).join('');
      return `<div style="padding:2cqh 2cqw;color:#ebe5d8;font-family:'IBM Plex Mono',monospace"><div style="display:flex;gap:.6cqw;align-items:center"><b style="font:700 2.6cqh 'Barlow Condensed',sans-serif;letter-spacing:.14em">OUR FILM · ${G.film.length}</b>${head}</div>
        <div style="font:700 3.6cqh 'Barlow Condensed',sans-serif;letter-spacing:.1em;margin-top:1cqh;color:${G.phase === 'join' ? colOf(G.last.win) : '#ebe5d8'}">${G.phase === 'join' ? `${esc(nameOf(G.last.win)).toUpperCase()}’S BRIDGE JOINS THE FILM` : 'OUR FILM'}</div>
        ${G.phase === 'join' ? `<div style="display:flex;gap:1cqw;align-items:center;margin-top:1cqh">${chain(laneOf(G.last.win)).map((c, j, a) => `${j ? `<div style="width:2cqw;height:.8cqh;background:${tint(seams(laneOf(G.last.win))[j - 1])}"></div>` : ''}<div style="width:15cqw;aspect-ratio:16/9;border-radius:4px;background:center/cover url('${esc(c.th)}');outline:2px solid ${j === 0 ? '#ebe5d8' : j === a.length - 1 ? '#f25a17' : colOf(G.last.win)}"></div>`).join('')}</div><div style="margin-top:1.4cqh;font-size:2.1cqh;color:#cfc9bc">${Object.entries(G.last.tallies).map(([k, n]) => `<span style="color:${colOf(k)}">${esc(nameOf(k))} ${n} vote${n === 1 ? '' : 's'}</span>`).join(' · ')} · the critic liked ${esc(nameOf(G.last.crit))}’s bridge best · next: ${G.n < G.rounds ? esc(beats[Math.min(beats.length - 1, G.n + 1)].act) : 'the whole film'}</div>`
          : `<video id="tbv" muted playsinline style="width:100%;max-height:60cqh;aspect-ratio:16/9;background:#000;border-radius:6px;margin-top:1cqh;object-fit:cover"></video><div id="tbcap" style="font-size:2cqh;color:#cfc9bc"></div>`}</div>`;
    }
    function drawSide() { const ph = G.phase, r = rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}${G.gain && G.gain[p.id] && ph === 'join' ? ` <span class="hint" style="margin:0">+${G.gain[p.id]}</span>` : ''}<b>${p.score}</b></div>`).join('');
      if (ph === 'loading') return H.side(`<div class="ph">The Table <small>laying out the shots</small></div>`, ph);
      if (ph === 'build') { const locals = H.players.filter(p => p.local); const S = H.side(`<div class="ph">Round ${G.n} · bridge <small>${Object.keys(G.locked).length} of ${voters().length} locked</small></div>${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${(G.hands[p.id] || []).map((c, i) => `<button class="btn chip" data-p="${p.id}" data-i="${i}" title="${esc(c.ti)}" style="width:54px;height:30px;background:center/cover url('${esc(c.th)}')"></button>`).join('')}<button class="btn chip" data-l="${p.id}">lock</button></div>`).join('')}${!H._gate ? '<button class="btn chip" id="force" style="margin-top:8px">screen now</button>' : ''}${r}`, ph + G.n);
        S.querySelectorAll('[data-i]').forEach(b => b.onclick = () => play(b.dataset.p, +b.dataset.i)); S.querySelectorAll('[data-l]').forEach(b => b.onclick = () => lock(b.dataset.l)); const f = $('#force'); if (f) f.onclick = screen; return; }
      if (ph === 'vote') { const locals = H.players.filter(p => p.local), opts = branches(); const S = H.side(`<div class="ph">Round ${G.n} · vote <small>${Object.keys(G.votes).length} of ${voters().length} voted</small></div>${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${opts.filter(k => k !== p.id).map(k => `<button class="btn chip ${G.votes[p.id] === k ? 'on' : ''}" data-p="${p.id}" data-v="${k}">${esc(nameOf(k))}</button>`).join('')}</div>`).join('')}${!H._gate ? '<button class="btn chip" id="force" style="margin-top:8px">join now</button>' : ''}${r}`, ph + G.n);
        S.querySelectorAll('[data-v]').forEach(b => b.onclick = () => vote(b.dataset.p, b.dataset.v)); const f = $('#force'); if (f) f.onclick = join; return; }
      H.side(`<div class="ph">${ph === 'join' ? 'Joined' : ph === 'screen' ? 'Screening' : 'Our film'} <small>${G.film.length} shots</small></div>${r}${ph === 'wrap' ? H.awardsHTML(H.awards([]).filter(a => a.id !== 'house')) : ''}`, ph + G.n);
    }
    let drawn = ''; function draw() { if (G.phase !== 'loading') { const html = stand(); const keepVideo = $('#tbv') && (G.phase === 'screen' || G.phase === 'film') && drawn === G.phase + (G.playing || ''); if (!keepVideo) H.slate(html); drawn = G.phase + (G.playing || ''); } drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, n: G.n, rounds: G.rounds };
      if (G.phase === 'build') { const lane = G.lanes[p.id] || [], sm = seams(lane); s.start = { th: G.start.th, ti: G.start.ti }; s.end = { th: G.end.th, ti: G.end.ti, act: G.endBeat.act }; s.hand = (G.hands[p.id] || []).map(c => ({ th: c.th, ti: c.ti, a: Math.round(L.join(lane.length ? lane[lane.length - 1] : G.start, c) * 100), b: Math.round(L.join(c, G.end) * 100) })); s.lane = lane.map((c, j) => ({ th: c.th, ti: c.ti, q: sm[j] })); s.last = lane.length ? sm[sm.length - 1] : null; s.score = Math.round(score(lane) * 100); s.locked = !!G.locked[p.id]; s.col = colOf(p.id); }
      if (G.phase === 'vote') { s.opts = branches().filter(k => k !== p.id).map(k => ({ k, name: nameOf(k), col: colOf(k), th: laneOf(k).map(c => c.th), sc: Math.round(score(laneOf(k)) * 100) })); s.mine = G.votes[p.id]; s.start = G.start.th; s.end = G.end.th; }
      if (G.phase === 'join') { s.win = nameOf(G.last.win); s.gain = (G.gain || {})[p.id] || 0; }
      if (G.phase === 'wrap' || G.phase === 'film') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; }
      return s; }
    return { stateFor, draw, onMsg(p, m) { if (m.t === 'play') play(p.id, m.i); if (m.t === 'back') back(p.id, m.j); if (m.t === 'lock') lock(p.id); if (m.t === 'vote') vote(p.id, m.v); }, onJoin(p) { if (G.phase === 'build' && !G.hands[p.id]) { deal(); G.lanes[p.id] = []; draw(); } }, crowdTarget: () => null, performer: () => null, stop() { G.phase = 'over'; const v = $('#tbv'); if (v) { clearTimeout(v._t); v.pause(); } } };
  }
  /* ---- the phone: START, your bridge, END along the top; your hand of six below, each marked with how it cuts from your last shot and into END */
  function phone(S, api) { const P = S.phase, { esc } = api, tint = q => q == null ? '#bbb' : q >= .6 ? '#5ea86b' : q >= .35 ? '#d3a33a' : '#d0533c';
    if (P === 'loading') return { key: 'loading', status: 'laying out the shots', tabs: ['me', 'throw'] };
    if (P === 'build') return { key: 'build' + S.n, status: 'Round ' + S.n + ' of ' + S.rounds + (S.locked ? ' · locked, waiting' : ' · bridge START to END'), takeover: { key: 'b' + S.n + '|' + S.hand.length + '|' + S.lane.length + '|' + S.locked, render(el) {
      const cell = (th, extra = '') => `<div style="aspect-ratio:16/9;border-radius:5px;background:#000 center/cover url('${esc(th)}');${extra}"></div>`;
      el.innerHTML = `<div style="display:grid;grid-template-columns:1fr 10px 1fr 10px 1fr 10px 1fr 10px 1fr;gap:2px;align-items:center;margin:2px 0 4px">${cell(S.start.th, 'outline:2px solid #333')}${[0, 1, 2].map(j => `<div style="height:4px;border-radius:2px;background:${S.lane[j] ? tint(S.lane[j].q) : '#ddd'}"></div>${S.lane[j] ? `<button data-j="${j}" style="padding:0;border:0;background:none">${cell(S.lane[j].th, `outline:2px solid ${S.col}`)}</button>` : '<div style="aspect-ratio:16/9;border:2px dashed #bbb;border-radius:5px"></div>'}`).join('')}<div style="height:4px;border-radius:2px;background:${tint(S.last)}"></div>${cell(S.end.th, 'outline:2px solid #f25a17')}</div>
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:6px"><span>START</span><b>bridge ${S.lane.length ? S.score : '-'}</b><span style="color:#d4501c">END · ${esc(S.end.act)}</span></div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px">${S.hand.map((c, i) => `<button class="btn" data-i="${i}" ${S.locked || S.lane.length >= 3 ? 'disabled' : ''} style="padding:0;position:relative;aspect-ratio:16/9;background:center/cover url('${esc(c.th)}')"><span style="position:absolute;left:3px;bottom:3px;display:flex;gap:3px"><i style="font-style:normal;font-size:11px;background:${tint(c.a / 100)};color:#fff;padding:0 4px;border-radius:3px">in ${c.a}</i><i style="font-style:normal;font-size:11px;background:${tint(c.b / 100)};color:#fff;padding:0 4px;border-radius:3px">to end ${c.b}</i></span></button>`).join('')}</div>
        <button class="btn" id="lk" ${S.locked || !S.lane.length ? 'disabled' : ''} style="width:100%;margin-top:8px">LOCK MY BRIDGE</button>`;
      el.querySelectorAll('[data-i]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'play', i: +b.dataset.i }); });
      el.querySelectorAll('[data-j]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'back', j: +b.dataset.j }); });
      const lk = el.querySelector('#lk'); if (lk) lk.onclick = () => { api.buzz(20); api.send({ t: 'lock' }); }; } } };
    if (P === 'screen') return { key: 'screen' + S.n, status: 'Every branch is playing on the stand', tabs: ['throw', 'me'] };
    if (P === 'vote') return { key: 'vote' + S.n, status: 'Round ' + S.n + ' · vote', takeover: { key: 'v' + S.n + '|' + S.mine, render(el) {
      el.innerHTML = `<div class="say" style="text-align:center;font-size:22px;margin:4px 0 8px">Which bridge joins the film?</div>${S.opts.map(o => `<button class="btn ${S.mine === o.k ? 'on' : ''}" data-v="${esc(o.k)}" style="display:block;width:100%;margin-bottom:6px;text-align:left;border-left:6px solid ${o.col}"><b>${esc(o.name)}</b> · bridge ${o.sc}<div style="display:flex;gap:3px;margin-top:4px">${[S.start].concat(o.th, [S.end]).map(t => `<img src="${esc(t)}" style="width:${100 / (o.th.length + 2) - 1}%;aspect-ratio:16/9;object-fit:cover;border-radius:3px" alt="">`).join('')}</div></button>`).join('') || '<div class="sub">no other branches this round</div>'}`;
      el.querySelectorAll('[data-v]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', v: b.dataset.v }); }); } } };
    if (P === 'join') return { key: 'join' + S.n, status: esc(S.win) + '’s bridge joins the film' + (S.gain ? ' · you +' + S.gain : ''), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'Our film is playing on the stand', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.of}</div><div class="sub">${S.you.score} points</div></div>`; } } };
    return null; }
  Party.games.table = { title: 'The Table', blurb: 'the light table, played: bridge the film to the story’s next beat from your phone; the room joins the best bridge', options: [{ k: 'rounds', name: 'beats', values: [4, 6, 8], def: 6 }, { k: 'footage', name: 'footage', values: ['all', 'ai', 'ar'], def: 'all' }, { k: 'chapter', name: 'chapter', values: ['all', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'], def: 'all' }, { k: 'machine', name: 'machine', values: ['on', 'off'], def: 'on' }], host, phone };
})();
