/* STEER THE MACHINE on the Party platform: the Grand Editing Machine (a Monte Carlo tree search, monte/mcts.js) directs a film one
   piece at a time; the room decides each piece. The machine imagines a few hundred futures and offers its three most-visited next
   pieces; every phone picks one; the room's pick is cut in (the machine re-roots its tree there and keeps what it learned).
   Points for siding with the room, more for thinking like the machine. At the end, the film the room and the machine made. */
(function () {
  const { esc, rnd, pick, mini } = Party;
  const THINK = 256;
  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    const G = { phase: 'loading', n: 0, pieces: H.opt.pieces, opts: [], votes: {}, agree: 0, all: [] };
    let M = null, live = null, play = null;
    H.slate(H.card(`<div class="big">Steer the Machine<small>the Grand Editing Machine is warming up · loading the archive…</small></div>`, 'house'));
    Party.monte.load().then(m => { M = m; play = Party.monte.Player(H, M); live = GrandEditingMachine.machine(M, { seed: (Date.now() % 1e6) | 1, iters: THINK }); think(); });
    const kindName = (o) => o.kind === 'turn' ? 'turn the page' : o.kind === 'end' ? 'the end' : o.kind === 'stop' ? 'stop the projector' : o.kind === 'card' ? 'a title card' : o.kind === 'punch' ? 'a punchline' : 'a shot';
    const optLabel = o => o.kind === 'turn' ? 'the next act begins' : Party.monte.label(M, o.k);
    // ---- the machine thinks: a few hundred futures, a frame at a time, shown as they come
    function think() {
      if (live.done || G.n >= G.pieces) return finale();
      G.phase = 'think'; G.votes = {}; H.sign = {}; G.n++; let done = 0; draw();
      const tick = () => { if (G.phase !== 'think') return; const t0 = performance.now(); while (performance.now() - t0 < 30 && done < THINK) { live.iterate(); done++; }
        const rec = live.recent.slice(-6);
        H.slate(H.card(`<div class="big">The machine is thinking<small>${live.total.toLocaleString()} futures imagined · piece ${G.n} of ${G.pieces}</small><div class="steps" style="grid-template-columns:repeat(6,1fr)">${rec.map(r => `<div style="padding:.4cqh"><div style="aspect-ratio:4/3;background:#000 center/cover;background-image:url('${esc(play.thumb(r.first[0]))}')"></div><b style="font-size:4cqh">${Math.round(r.score * 100)}</b></div>`).join('')}</div></small></div>`, 'house'));
        if (done < THINK) requestAnimationFrame(tick); else offer(); };
      requestAnimationFrame(tick); }
    function offer() {
      const kids = live.kids(); const tot = kids.reduce((a, c) => a + c.n, 0) || 1;
      G.opts = kids.slice(0, 3).map(c => ({ kind: c.kind, k: c.k, n: c.n, share: c.n / tot, q: c.q })); G.machine = 0;
      if (G.opts.length === 1) { commit(0, true); return; }
      G.phase = 'vote';
      H.slate(H.card(`<div class="big">Which piece next?<small>the machine has a favourite · pick yours on your phone</small><div class="steps" style="grid-template-columns:repeat(${G.opts.length},1fr)">${G.opts.map((o, i) => `<div><b>${'ABC'[i]}</b>${o.k != null ? `<div style="aspect-ratio:4/3;background:#000 center/cover;background-image:url('${esc(play.thumb(o.k))}')"></div>` : ''}${esc(kindName(o))}</div>`).join('')}</div></div>`, 'night'));
      draw(); }
    const voters = () => H.players.filter(p => p.local || p.conn);
    function vote(pid, i) { if (G.phase !== 'vote' || i < 0 || i >= G.opts.length) return; const first = G.votes[pid] == null; G.votes[pid] = i; H.sign[pid] = 'picked';
      if (first) { H.act(pid, 'hit', 280); }
      if (voters().every(p => G.votes[p.id] != null)) H.gate('Cut it in ▸', 'any', () => tally()); draw(); }
    function tally() { const n = G.opts.map(() => 0); Object.values(G.votes).forEach(i => n[i]++); const max = Math.max(...n); const tied = n.map((v, i) => v === max ? i : -1).filter(i => i >= 0); const room = tied.includes(0) ? 0 : pick(tied);
      G.gain = {}; H.players.forEach(p => { const v = G.votes[p.id]; if (v == null) return; let g = 0; if (v === room) g += 1; if (v === 0) g += 2; if (g) { p.score += g; G.gain[p.id] = g; } if (v === 0) H.act(p.id, 'hop', 820); });
      if (room === 0) G.agree++; commit(room, false, n); }
    function commit(i, forced, n) {
      const o = G.opts[i], root = live.root, kid = root.kids.find(c => c.m.kind === o.kind && c.m.k === o.k);
      if (kid) { const mx = Math.max(...root.kids.map(c => c.n)); kid.n = mx + 1; }
      const m = live.commit(); G.all.push({ o, room: i, machine: 0, n: n || [], forced });
      G.phase = 'cut'; G.last = { i, n: n || [] }; H.sign = {};
      const lastEv = live.root.s.ev.slice(-1)[0];
      H.slate(H.card(`<div class="big">${i === 0 ? 'The room and the machine agree' : 'The room overrules the machine'}<small>${esc(kindName(o))} · the machine gave it ${Math.round(o.share * 100)}% of its futures${G.opts[0] && i !== 0 ? ' · its favourite had ' + Math.round(G.opts[0].share * 100) + '%' : ''}</small></div>`, i === 0 ? 'gold' : 'stage'));
      if (i === 0) H.act('house', 'hop', 820); else { H.act('house', 'slump', 1600); }
      setTimeout(() => { if (G.phase === 'cut' && lastEv) play.play({ ev: [lastEv], music: null }, { music: false }); }, 1800);
      H.gate(live.done || G.n >= G.pieces ? 'Watch our film ▸' : 'Think again ▸', 'any', think); draw(); }
    function finale() { G.phase = 'film'; const f = live.film(); H.sign = {};
      H.slate(H.card(`<div class="big">Directed by the room<br>and the machine<small>they agreed ${G.agree} of ${G.all.length} times · the critic gives it ${Math.round(f.score * 100)}</small></div>`, 'gold'));
      setTimeout(() => { if (G.phase === 'film') play.play(f, {}, () => { G.phase = 'wrap'; draw(); H.gate('Edit the film ▸', 'any', () => { H.seed = toFilm(); H.playGame('cut'); }); }); }, 2600);
      H.gate('Skip ▸', 'any', () => { play.stop(); G.phase = 'wrap'; const r = rank(); if (r[0]) H.act(r[0].id, 'cheer', 2200); draw(); H.gate('Edit the film ▸', 'any', () => { H.seed = toFilm(); H.playGame('cut'); }); }); draw(); }
    const toFilm = () => Party.monte.toFilm(M, live.film(), 'Directed by the room and the machine');
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function drawSide() { const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">Steer the Machine <small>loading the archive</small></div>`, ph);
      const optRows = (show) => `<div class="takes">${G.opts.map((o, i) => `<div class="tk ${show && i === G.last.i ? 'win' : ''}"><span class="n">${'ABC'[i]}</span><span class="strip">${o.k != null ? `<i style="background-image:url('${esc(play.thumb(o.k))}');max-width:72px"></i>` : ''}</span><span class="by" style="max-width:55%;text-align:left">${esc(kindName(o))}<br><span class="hint" style="margin:0">${esc(optLabel(o)).slice(0, 70)}</span>${show ? `<br><b style="color:var(--verm)">machine ${Math.round(o.share * 100)}%</b> · <span class="vs">${H.players.filter(p => G.votes[p.id] === i).map(p => mini(p.av)).join('') || '·'}</span>` : ''}</span></div>`).join('')}</div>`;
      if (ph === 'think') return H.side(`<div class="ph">Piece ${G.n} of ${G.pieces} <small>the machine is imagining futures</small></div><div class="hint" style="text-align:left">Selection, expansion, rollout, backpropagation: ${THINK} times. Its three most-visited next pieces become the room’s choice.</div>${rankHTML()}`, ph + G.n);
      if (ph === 'vote') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Piece ${G.n} · pick one <small>${Object.keys(G.votes).length} of ${voters().length} picked</small></div>${optRows(false)}
          ${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.opts.map((o, i) => `<button class="btn chip ${G.votes[p.id] === i ? 'on' : ''}" data-p="${p.id}" data-i="${i}">${'ABC'[i]}</button>`).join('')}</div>`).join('')}
          ${!H._gate ? `<button class="btn chip" id="force" style="margin-top:8px">cut it in now</button>` : ''}`, ph + G.n);
        S.querySelectorAll('[data-p]').forEach(b => b.onclick = () => vote(b.dataset.p, +b.dataset.i)); const f = $('#force'); if (f) f.onclick = tally; return; }
      if (ph === 'cut') return H.side(`<div class="ph">Piece ${G.n} · cut in <small>the machine’s favourite is A</small></div>${optRows(true)}${rankHTML()}`, ph + G.n);
      if (ph === 'film' || ph === 'wrap') return H.side(`<div class="ph">The film <small>${G.agree} of ${G.all.length} agreed</small></div>${rankHTML()}${H.awardsHTML(H.awards([]).filter(a => a.id !== 'house'))}`, ph);
    }
    const rankHTML = () => rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}${G.gain && G.gain[p.id] && G.phase === 'cut' ? ` <span class="hint" style="margin:0">+${G.gain[p.id]}</span>` : ''}<b>${p.score}</b></div>`).join('');
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, n: G.n, pieces: G.pieces };
      if (G.phase === 'vote' || G.phase === 'cut') s.opts = G.opts.map(o => ({ th: o.k != null ? play.thumb(o.k) : '', kind: kindName(o), label: optLabel(o).slice(0, 80) })), s.mine = G.votes[p.id];
      if (G.phase === 'cut') { s.room = G.last.i; s.shares = G.opts.map(o => Math.round(o.share * 100)); s.gain = (G.gain || {})[p.id] || 0; }
      if (G.phase === 'wrap' || G.phase === 'film') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; s.agree = G.agree; }
      return s; }
    return { stateFor, draw, onMsg(p, m) { if (m.t === 'vote') vote(p.id, m.k); }, crowdTarget: () => null, performer: () => null, stop() { G.phase = 'over'; if (play) play.stop(); } };
  }
  function phone(S, api) { const P = S.phase, { esc } = api;
    if (P === 'loading') return { key: 'loading', status: 'the machine is warming up', tabs: ['me', 'throw'] };
    if (P === 'think') return { key: 'think' + S.n, status: 'Piece ' + S.n + ' of ' + S.pieces + ' · the machine is imagining futures', tabs: ['throw', 'me'] };
    if (P === 'vote') return { key: 'vote' + S.n, status: 'Piece ' + S.n + ' of ' + S.pieces, takeover: { key: 'v' + S.n + '|' + S.mine, render(el) {
      el.innerHTML = `<div class="say" style="text-align:center;font-size:26px;margin:4px 0 8px">Which piece next?</div><div class="answers">${S.opts.map((o, i) => `<button class="btn ${S.mine === i ? 'on' : ''}" data-k="${i}" style="display:flex;gap:10px;align-items:center">${o.th ? `<img alt="" src="${esc(o.th)}" style="width:42%;aspect-ratio:4/3;object-fit:cover;border:2px solid var(--ink);border-radius:4px">` : ''}<span><span class="k">${'ABC'[i]}</span>${esc(o.kind)}<br><small style="color:#6d6052">${esc(o.label)}</small></span></button>`).join('')}</div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', k: +b.dataset.k }); }); } } };
    if (P === 'cut') return { key: 'cut' + S.n, status: (S.room === 0 ? 'The room went with the machine' : 'The room overruled the machine') + ' · machine: ' + S.shares.map((v, i) => 'ABC'[i] + ' ' + v + '%').join(' · ') + (S.gain ? ' · you +' + S.gain : ''), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'Our film is playing · directed by the room and the machine', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.of}</div><div class="sub">${S.you.score} points · the room agreed with the machine ${S.agree} times</div></div>`; } } };
    return null; }
  Party.games.machine = { title: 'Steer the Machine', blurb: 'the Grand Editing Machine imagines the futures; the room picks every piece of the film', options: [{ k: 'pieces', name: 'pieces', values: [8, 12, 16], def: 12 }], host, phone };
})();
