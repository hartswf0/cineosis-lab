/* THE TABLE (Cineosis Ludens) on the Party platform: the light table, played. One shot lies on the stand; every phone is dealt a hand of
   six shots (the critic deals two that cut well from it, two that might, two wild ones). Tap a card and it flies onto your lane on the
   stand; build a branch of up to three shots, every seam scored live by the lab's cut critic (ludens/ludens.js: the lens chosen in Ludens).
   LOCK, then everyone votes for the best branch but their own (the machine builds one too). The winning branch is JOINED to our film and
   plays on the stand; its last shot is the next round's start. 2 points for each vote your branch gets, 1 for voting for the winner,
   1 for the branch the critic scores best. At the end, our film plays. */
(function () {
  const { esc, mini } = Party;
  function host(H) {
    const $ = s => document.querySelector(s), L = Ludens; L.root = '';
    const G = { phase: 'loading', n: 0, rounds: H.opt.rounds, start: null, film: [], hands: {}, lanes: {}, votes: {}, last: null, fly: [] };
    let pool = [];
    H.slate(H.card(`<div class="big">The Table<small>laying out the shots…</small></div>`, 'house'));
    L.load().then(() => {
      const ch = H.opt.chapter === 'all' ? null : (L.chapters.find(c => c[1] === H.opt.chapter) || [])[0];
      pool = L.cards.filter(c => (H.opt.footage === 'all' || c.k === H.opt.footage) && (!ch || c.ch === ch)); if (pool.length < 40) pool = L.cards.slice();
      const opens = L.holes.map(h => L.byId[h.id]).filter(c => c && pool.includes(c)); G.start = opens[0] || pool.slice().sort((a, b) => b.mc - a.mc)[0];
      G.film = [{ c: G.start, who: null }]; round();
    });
    const voters = () => H.players.filter(p => p.local || p.conn);
    const used = () => new Set(G.film.map(f => f.c.id));
    /* the deal: two that cut well from the start, two that might, two wild; nobody gets a shot already in the film */
    function deal() {
      const u = used(), taken = new Set(), sample = []; for (let k = 0; k < 500; k++) { const c = pool[Math.floor(Math.random() * pool.length)]; if (!u.has(c.id)) sample.push(c); }
      const ranked = sample.map(c => ({ c, q: L.join(G.start, c) })).sort((a, b) => b.q - a.q);
      const take = (list) => { for (const x of list) if (!taken.has(x.c.id)) { taken.add(x.c.id); return x.c; } return list[0].c; };
      G.hands = {}; voters().forEach(p => { const top = ranked.slice(0, 40), mid = ranked.slice(40, 160), wild = ranked.slice(160); G.hands[p.id] = [take(top.sort(() => Math.random() - .5)), take(top), take(mid.sort(() => Math.random() - .5)), take(mid), take(wild.sort(() => Math.random() - .5)), take(wild)].sort(() => Math.random() - .5); });
      G.house = (() => { let prev = G.start; const lane = []; for (let k = 0; k < 3; k++) { let best = null, bs = -1; for (const x of ranked.slice(0, 120)) { if (lane.includes(x.c) || taken.has(x.c.id)) continue; const q = L.join(prev, x.c); if (q > bs) { bs = q; best = x.c; } } if (!best) break; lane.push(best); prev = best; } return lane; })();
    }
    function round() {
      G.n++; if (G.n > G.rounds) return finale();
      G.phase = 'build'; G.lanes = {}; G.locked = {}; G.votes = {}; H.sign = {}; deal(); voters().forEach(p => { G.lanes[p.id] = []; }); draw();
    }
    const score = lane => { if (!lane.length) return 0; let prev = G.start, s = 0; lane.forEach(c => { s += L.join(prev, c); prev = c; }); return s / lane.length; };
    const seams = lane => { let prev = G.start; return lane.map(c => { const q = L.join(prev, c); prev = c; return q; }); };
    function play(pid, i) { if (G.phase !== 'build' || G.locked[pid]) return; const h = G.hands[pid], lane = G.lanes[pid]; if (!h || !h[i] || lane.length >= 3) return; lane.push(h[i]); h.splice(i, 1); G.fly.push({ pid, t: performance.now() }); H.act(pid, 'hit', 280); draw(); }
    function back(pid, j) { if (G.phase !== 'build' || G.locked[pid]) return; const lane = G.lanes[pid]; if (!lane || !lane[j]) return; G.hands[pid].push(lane[j]); lane.splice(j, 1); draw(); }
    function lock(pid) { if (G.phase !== 'build' || !(G.lanes[pid] || []).length) return; G.locked[pid] = true; H.sign[pid] = 'locked'; H.act(pid, 'hop', 600); if (voters().every(p => G.locked[p.id])) H.gate('Reveal the branches', 'any', reveal); draw(); }
    function reveal() { G.phase = 'vote'; H.sign = {}; voters().forEach(p => { if (!G.locked[p.id]) G.lanes[p.id] = G.lanes[p.id] || []; }); draw(); }
    function vote(pid, v) { if (G.phase !== 'vote' || v === pid) return; G.votes[pid] = v; H.sign[pid] = 'voted'; H.act(pid, 'hit', 280); if (voters().every(p => G.votes[p.id] != null || !(Object.keys(G.lanes).some(k => k !== p.id && G.lanes[k].length) || H.opt.machine === 'on'))) H.gate('Join the winner', 'any', join); draw(); }
    function join() {
      const cands = Object.keys(G.lanes).filter(k => G.lanes[k].length).concat(H.opt.machine === 'on' ? ['house'] : []); if (!cands.length) return round();
      const laneOf = k => k === 'house' ? G.house : G.lanes[k], tally = k => Object.values(G.votes).filter(v => v === k).length;
      const crit = cands.slice().sort((a, b) => score(laneOf(b)) - score(laneOf(a)))[0]; const win = cands.slice().sort((a, b) => tally(b) - tally(a) || score(laneOf(b)) - score(laneOf(a)))[0];
      G.gain = {}; const add = (id, g) => { const p = H.players.find(x => x.id === id); if (p && g) { p.score += g; G.gain[id] = (G.gain[id] || 0) + g; } };
      cands.forEach(k => add(k, tally(k) * 2)); add(crit, 1); Object.entries(G.votes).forEach(([pid, v]) => { if (v === win) add(pid, 1); });
      const lane = laneOf(win); lane.forEach(c => G.film.push({ c, who: win })); G.start = lane[lane.length - 1]; G.last = { win, crit, lane, tallies: Object.fromEntries(cands.map(k => [k, tally(k)])) };
      G.phase = 'join'; H.sign = {}; draw(); playSeq(lane, () => {}); if (win !== 'house') H.act(win, 'cheer', 1600); else H.act('house', 'hop', 900);
      H.gate(G.n >= G.rounds ? 'Watch our film' : 'Next round', 'any', round);
    }
    function playSeq(list, then) { setTimeout(() => { const v = $('#tbv'); if (!v) return; let i = 0; const nx = () => { if (i >= list.length) { v.pause(); then && then(); return; } const c = list[i++]; v.src = L.root + c.m.replace(/^\.\.\//, ''); if (/^https?:/.test(c.m)) v.src = c.m; v.onloadedmetadata = () => { v.currentTime = c.ss != null ? c.ss : Math.max(0, v.duration / 2 - 1.3); v.play().catch(() => { }); }; clearTimeout(v._t); v._t = setTimeout(nx, 2600); }; nx(); }, 120); }
    function finale() { G.phase = 'film'; H.sign = {}; draw(); playSeq(G.film.map(f => f.c), () => { G.phase = 'wrap'; draw(); }); H.gate('Skip', 'any', () => { G.phase = 'wrap'; const r = rank(); if (r[0]) H.act(r[0].id, 'cheer', 2200); draw(); }); }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    const nameOf = k => k === 'house' ? 'the machine' : (H.players.find(p => p.id === k) || {}).name || '?';
    const colOf = k => { if (k === 'house') return '#aa82f0'; const i = H.players.findIndex(p => p.id === k); return ['#5acde6', '#f06e64', '#f0cd46', '#7fc28b', '#e3a0f0', '#f0a050', '#90b0ff', '#c0c0c0'][i % 8]; };
    const tint = q => `rgb(${L.tint(q)})`;
    /* ---- the stand: the start shot, every player's lane growing as they play cards, seams scored live */
    function stand() {
      const T = (c, w, extra = '') => `<div style="position:relative;width:${w}cqw;aspect-ratio:16/9;border-radius:4px;background:#000 center/cover url('${esc(c.th)}');flex:none;${extra}"></div>`;
      const strip = G.film.slice(-12).map(f => `<div style="width:6cqw;aspect-ratio:16/9;background:center/cover url('${esc(f.c.th)}');border-bottom:3px solid ${f.who ? colOf(f.who) : '#ebe5d8'};border-radius:2px;flex:none"></div>`).join('');
      const head = `<div style="display:flex;gap:10px;align-items:center;margin-bottom:1cqh"><b style="font:700 2.8cqh 'Barlow Condensed',sans-serif;letter-spacing:.14em;white-space:nowrap">OUR FILM · ${G.film.length} SHOTS</b><div style="display:flex;gap:3px;overflow:hidden">${strip}</div></div>`;
      if (G.phase === 'join' || G.phase === 'film') return `<div style="padding:1.5cqh 2cqw;color:#ebe5d8;font-family:'IBM Plex Mono',monospace">${head}<div style="font:700 3.4cqh 'Barlow Condensed',sans-serif;letter-spacing:.1em;color:${G.phase === 'join' ? colOf(G.last.win) : '#ebe5d8'}">${G.phase === 'join' ? `${esc(nameOf(G.last.win)).toUpperCase()}’S BRANCH JOINS THE FILM` : 'OUR FILM'}</div><video id="tbv" muted playsinline style="width:100%;max-height:58cqh;aspect-ratio:16/9;background:#000;border-radius:6px;margin-top:1cqh;object-fit:cover"></video>${G.phase === 'join' ? `<div style="margin-top:1cqh;font-size:2.2cqh;color:#cfc9bc">${Object.entries(G.last.tallies).map(([k, n]) => `<span style="color:${colOf(k)}">${esc(nameOf(k))} ${n} vote${n === 1 ? '' : 's'}</span>`).join(' · ')} · the critic liked ${esc(nameOf(G.last.crit))}’s seams best</div>` : ''}</div>`;
      const lanes = Object.keys(G.lanes).concat(G.phase === 'vote' && H.opt.machine === 'on' ? ['house'] : []);
      const rows = lanes.map(k => { const lane = k === 'house' ? G.house : G.lanes[k], sm = seams(lane), sc = score(lane), fly = G.fly.find(f => f.pid === k && performance.now() - f.t < 700); return `<div style="display:flex;align-items:center;gap:.6cqw;margin:.7cqh 0">
        <div style="width:12cqw;flex:none;font:600 2.2cqh 'IBM Plex Mono',monospace;color:${colOf(k)};white-space:nowrap;overflow:hidden">${k === 'house' ? '' : mini((H.players.find(p => p.id === k) || {}).av)} ${esc(nameOf(k))}<br><span style="color:#858b93;font-weight:400">${G.locked[k] || k === 'house' ? 'LOCKED' : 'building'} · ${lane.length ? Math.round(sc * 100) : '-'}</span></div>
        <div style="width:1.6cqw;flex:none;height:4px;background:${lane.length ? tint(sm[0]) : '#333'}"></div>
        ${[0, 1, 2].map(j => lane[j] ? `${j ? `<div style="width:1cqw;flex:none;height:4px;background:${tint(sm[j])}"></div>` : ''}${T(lane[j], 13, `outline:3px solid ${colOf(k)};${fly && j === lane.length - 1 ? 'animation:tbfly .6s ease-out;' : ''}${G.phase === 'build' && !G.locked[k] && k !== 'house' ? '' : ''}`)}` : `${j ? '<div style="width:1cqw;flex:none"></div>' : ''}<div style="width:13cqw;aspect-ratio:16/9;border:2px dashed #2c3138;border-radius:4px;flex:none"></div>`).join('')}
        ${G.phase === 'vote' ? `<div style="margin-left:1cqw;font:700 2cqh 'Barlow Condensed',sans-serif;color:${colOf(k)}">${Object.values(G.votes).filter(v => v === k).length || ''}</div>` : ''}</div>`; }).join('');
      return `<style>@keyframes tbfly{from{transform:translateY(40cqh) scale(.4);opacity:.2}to{transform:none;opacity:1}}</style><div style="padding:1.5cqh 2cqw;color:#ebe5d8;font-family:'IBM Plex Mono',monospace;height:100%;overflow:hidden">${head}
        <div style="display:flex;gap:1.5cqw;align-items:center"><div style="flex:none">${T(G.start, 24, 'outline:3px solid #f25a17')}<div style="font-size:2.2cqh;color:#cfc9bc;margin-top:.5cqh;max-width:24cqw">ROUND ${G.n}/${G.rounds} · from “${esc((G.start.ti || '').slice(0, 40))}”</div></div>
        <div style="flex:1;min-width:0">${rows || '<div style="color:#858b93">waiting for players…</div>'}</div></div>
        <div style="margin-top:1.4cqh;font-size:2.1cqh;color:#858b93">${G.phase === 'build' ? 'Tap a card on your phone: it lands on your lane. Up to three. Each seam is coloured by the critic (green joins well, red jars). LOCK when your branch is done.' : 'Vote on your phone for the best branch that is not yours.'} · lens: ${esc(L.V.lens)}</div></div>`;
    }
    function drawSide() { const ph = G.phase, r = rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}${G.gain && G.gain[p.id] && ph === 'join' ? ` <span class="hint" style="margin:0">+${G.gain[p.id]}</span>` : ''}<b>${p.score}</b></div>`).join('');
      if (ph === 'loading') return H.side(`<div class="ph">The Table <small>laying out the shots</small></div>`, ph);
      if (ph === 'build') { const locals = H.players.filter(p => p.local); const S = H.side(`<div class="ph">Round ${G.n} · build <small>${Object.keys(G.locked).length} of ${voters().length} locked</small></div>${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${(G.hands[p.id] || []).map((c, i) => `<button class="btn chip" data-p="${p.id}" data-i="${i}" title="${esc(c.ti)}" style="width:54px;height:30px;background:center/cover url('${esc(c.th)}')"></button>`).join('')}<button class="btn chip" data-l="${p.id}">lock</button></div>`).join('')}${!H._gate ? '<button class="btn chip" id="force" style="margin-top:8px">reveal now</button>' : ''}${r}`, ph + G.n);
        S.querySelectorAll('[data-i]').forEach(b => b.onclick = () => play(b.dataset.p, +b.dataset.i)); S.querySelectorAll('[data-l]').forEach(b => b.onclick = () => lock(b.dataset.l)); const f = $('#force'); if (f) f.onclick = reveal; return; }
      if (ph === 'vote') { const locals = H.players.filter(p => p.local), opts = Object.keys(G.lanes).filter(k => G.lanes[k].length).concat(H.opt.machine === 'on' ? ['house'] : []);
        const S = H.side(`<div class="ph">Round ${G.n} · vote <small>${Object.keys(G.votes).length} of ${voters().length} voted</small></div>${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${opts.filter(k => k !== p.id).map(k => `<button class="btn chip ${G.votes[p.id] === k ? 'on' : ''}" data-p="${p.id}" data-v="${k}">${esc(nameOf(k))}</button>`).join('')}</div>`).join('')}${!H._gate ? '<button class="btn chip" id="force" style="margin-top:8px">join now</button>' : ''}${r}`, ph + G.n);
        S.querySelectorAll('[data-v]').forEach(b => b.onclick = () => vote(b.dataset.p, b.dataset.v)); const f = $('#force'); if (f) f.onclick = join; return; }
      H.side(`<div class="ph">${ph === 'join' ? 'Joined' : 'Our film'} <small>${G.film.length} shots</small></div>${r}${ph === 'wrap' ? H.awardsHTML(H.awards([]).filter(a => a.id !== 'house')) : ''}`, ph + G.n);
    }
    let raf = 0; function draw() { if (G.phase !== 'loading') H.slate(stand()); drawSide(); H.syncCrew(); H.broadcast(); cancelAnimationFrame(raf); if (G.fly.length) { G.fly = G.fly.filter(f => performance.now() - f.t < 700); } }
    function stateFor(p) { const s = { phase: G.phase, n: G.n, rounds: G.rounds };
      if (G.phase === 'build') { s.start = G.start && { th: G.start.th, ti: G.start.ti }; s.hand = (G.hands[p.id] || []).map(c => ({ th: c.th, ti: c.ti, q: Math.round(L.join(G.lanes[p.id] && G.lanes[p.id].length ? G.lanes[p.id][G.lanes[p.id].length - 1] : G.start, c) * 100) })); s.lane = (G.lanes[p.id] || []).map(c => ({ th: c.th, ti: c.ti })); s.locked = !!G.locked[p.id]; }
      if (G.phase === 'vote') { s.opts = Object.keys(G.lanes).filter(k => G.lanes[k].length && k !== p.id).concat(H.opt.machine === 'on' ? ['house'] : []).map(k => ({ k, name: nameOf(k), th: (k === 'house' ? G.house : G.lanes[k]).map(c => c.th) })); s.mine = G.votes[p.id]; }
      if (G.phase === 'join') s.win = nameOf(G.last.win), s.gain = (G.gain || {})[p.id] || 0;
      if (G.phase === 'wrap' || G.phase === 'film') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; }
      return s; }
    return { stateFor, draw, onMsg(p, m) { if (m.t === 'play') play(p.id, m.i); if (m.t === 'back') back(p.id, m.j); if (m.t === 'lock') lock(p.id); if (m.t === 'vote') vote(p.id, m.v); }, onJoin(p) { if (G.phase === 'build' && !G.hands[p.id]) { deal(); G.lanes[p.id] = []; draw(); } }, crowdTarget: () => null, performer: () => null, stop() { G.phase = 'over'; const v = $('#tbv'); if (v) v.pause(); } };
  }
  function phone(S, api) { const P = S.phase, { esc } = api;
    if (P === 'loading') return { key: 'loading', status: 'laying out the shots', tabs: ['me', 'throw'] };
    if (P === 'build') return { key: 'build' + S.n, status: 'Round ' + S.n + ' of ' + S.rounds + (S.locked ? ' · locked, waiting' : ' · build your branch'), takeover: { key: 'b' + S.n + '|' + S.hand.length + '|' + S.lane.length + '|' + S.locked, render(el) {
      el.innerHTML = `<div class="say" style="text-align:center;font-size:20px;margin:2px 0 6px">${S.locked ? 'Locked' : 'Tap a shot to put it on your lane'}</div>
        <div style="display:flex;gap:6px;align-items:center;margin-bottom:8px"><img src="${esc(S.start.th)}" style="width:28%;aspect-ratio:16/9;object-fit:cover;border-radius:4px;outline:3px solid #f25a17" alt=""><span style="font-size:12px">from “${esc((S.start.ti || '').slice(0, 40))}”</span></div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:8px">${[0, 1, 2].map(j => S.lane[j] ? `<button class="btn" data-j="${j}" style="padding:0;aspect-ratio:16/9;background:center/cover url('${esc(S.lane[j].th)}')" title="take it back"></button>` : '<div style="aspect-ratio:16/9;border:2px dashed #999;border-radius:6px"></div>').join('')}</div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">${S.hand.map((c, i) => `<button class="btn" data-i="${i}" ${S.locked || S.lane.length >= 3 ? 'disabled' : ''} style="padding:0;position:relative;aspect-ratio:16/9;background:center/cover url('${esc(c.th)}')"><span style="position:absolute;right:3px;bottom:2px;font-size:11px;background:#000c;color:#fff;padding:0 4px;border-radius:3px">${c.q}</span></button>`).join('')}</div>
        <button class="btn" id="lk" ${S.locked || !S.lane.length ? 'disabled' : ''} style="width:100%;margin-top:10px">LOCK MY BRANCH</button>`;
      el.querySelectorAll('[data-i]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'play', i: +b.dataset.i }); });
      el.querySelectorAll('[data-j]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'back', j: +b.dataset.j }); });
      const lk = el.querySelector('#lk'); if (lk) lk.onclick = () => { api.buzz(20); api.send({ t: 'lock' }); }; } } };
    if (P === 'vote') return { key: 'vote' + S.n, status: 'Round ' + S.n + ' · vote', takeover: { key: 'v' + S.n + '|' + S.mine, render(el) {
      el.innerHTML = `<div class="say" style="text-align:center;font-size:22px;margin:4px 0 8px">Which branch joins the film?</div>${S.opts.map(o => `<button class="btn ${S.mine === o.k ? 'on' : ''}" data-v="${esc(o.k)}" style="display:block;width:100%;margin-bottom:6px;text-align:left"><b>${esc(o.name)}</b><div style="display:flex;gap:3px;margin-top:4px">${o.th.map(t => `<img src="${esc(t)}" style="width:32%;aspect-ratio:16/9;object-fit:cover;border-radius:3px" alt="">`).join('')}</div></button>`).join('') || '<div class="sub">no other branches this round</div>'}`;
      el.querySelectorAll('[data-v]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', v: b.dataset.v }); }); } } };
    if (P === 'join') return { key: 'join' + S.n, status: esc(S.win) + '’s branch joins the film' + (S.gain ? ' · you +' + S.gain : ''), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'Our film is playing on the stand', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.of}</div><div class="sub">${S.you.score} points</div></div>`; } } };
    return null; }
  Party.games.table = { title: 'The Table', blurb: 'the light table, played: every phone builds a branch from one shot, the room joins the best to our film', options: [{ k: 'rounds', name: 'rounds', values: [4, 6, 8], def: 6 }, { k: 'footage', name: 'footage', values: ['all', 'ai', 'ar'], def: 'all' }, { k: 'chapter', name: 'chapter', values: ['all', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'], def: 'all' }, { k: 'machine', name: 'machine', values: ['on', 'off'], def: 'on' }], host, phone };
})();
