/* SEA OF TAKES on the Party platform: the room recuts a Slopfeeder film shot by shot against the machine. For each shot the machine
   (slopfeeder/sea-core.js: monte/mcts.js's loop over the lattice of takes) imagines futures of the next shots and offers its three
   most-visited takes; every phone picks one; the room's pick is cut in. Points as in Steer the Machine: 1 for siding with the room,
   2 more for thinking like the machine. At the end, the room's recut plays, take after take. The same lattice the Sea of Takes page shows. */
(function () {
  const { esc, pick, mini } = Party;
  const THINK = 320;
  const thumbOf = x => /^http/.test(x.thumb) ? x.thumb : 'slopfeeder/' + x.thumb, srcOf = x => x.kind === 'ai' ? `slopfeeder/ai/web/${x.clip}.mp4` : x.v;
  const nameOf = x => x.kind === 'ai' ? x.clip.replace(/_/g, ' ') : `${x.title || 'archive'}${x.year ? ' (' + x.year + ')' : ''}`;
  function host(H) {
    const $ = s => document.querySelector(s);
    const G = { phase: 'loading', n: 0, pieces: H.opt.pieces, opts: [], votes: {}, agree: 0, all: [] };
    let M = null, S = null, vis = [], ch = [], lock = [], at = 0, mc = null;
    H.slate(H.card(`<div class="big">Sea of Takes<small>loading the lattice of takes…</small></div>`, 'house'));
    const view = H.opt.film === 'story' ? 'story' : 'song-' + H.opt.film;
    fetch(`slopfeeder/lattice/${view}.json`).then(r => r.json()).then(j => {
      M = j; S = SeaCore.Sea(j); ch = j.cols.map(() => 0); lock = j.cols.map(() => false);
      vis = j.cols.map((c, i) => i).filter(i => H.opt.footage !== 'ai' || j.cols[i].kind === 'ai');
      at = vis.findIndex(c => j.cols[c].cands.length > 1); think();
    });
    /* ---- the machine thinks: futures of the next shots, shown as they come */
    function think() {
      while (at >= 0 && at < vis.length && M.cols[vis[at]].cands.length < 2) at++;
      if (at < 0 || at >= vis.length || G.n >= G.pieces) return finale();
      G.phase = 'think'; G.votes = {}; H.sign = {}; G.n++; mc = S.machine(ch, lock, vis, at); let done = 0; draw();
      const C = M.cols[vis[at]];
      const tick = () => { if (G.phase !== 'think') return; const t0 = performance.now(); while (performance.now() - t0 < 30 && done < THINK) { mc.iterate(); done++; }
        const k = mc.kids().slice(0, 3);
        H.slate(H.card(`<div class="big">The machine is imagining<small>${mc.total} futures of the next ${Math.min(10, vis.length - at)} shots · shot ${G.n} of ${G.pieces} · ${esc(C.act)}${C.cap ? ' · “' + esc(C.cap.slice(0, 60)) + '”' : ''}</small><div class="steps" style="grid-template-columns:repeat(3,1fr)">${k.map(o => `<div><div style="aspect-ratio:16/9;background:center/cover url('${esc(thumbOf(C.cands[o.k]))}');border-radius:6px;opacity:${.35 + o.share}"></div><small>${Math.round(o.share * 100)}%</small></div>`).join('')}</div></div>`, 'house'));
        if (done < THINK) requestAnimationFrame(tick); else offer(); };
      requestAnimationFrame(tick);
    }
    function offer() {
      const kids = mc.kids(); G.opts = kids.slice(0, 3).map(o => ({ k: o.k, share: o.share })); const C = M.cols[vis[at]];
      if (G.opts.length === 1) { commit(0, true); return; }
      G.phase = 'vote';
      H.slate(H.card(`<div class="big">Which take?<small>shot ${G.n} of ${G.pieces} · ${esc(C.act)} · the machine has a favourite · pick yours on your phone</small><div class="steps" style="grid-template-columns:repeat(${G.opts.length},1fr)">${G.opts.map((o, i) => `<div><b>${'ABC'[i]}</b><div style="aspect-ratio:16/9;background:center/cover url('${esc(thumbOf(C.cands[o.k]))}');border-radius:6px"></div><small>${esc(nameOf(C.cands[o.k])).slice(0, 40)}</small></div>`).join('')}</div></div>`, 'house'));
      draw();
    }
    const voters = () => H.players.filter(p => p.local || p.conn);
    function vote(pid, i) { if (G.phase !== 'vote' || i < 0 || i >= G.opts.length) return; const first = G.votes[pid] == null; G.votes[pid] = i; H.sign[pid] = 'picked';
      if (first) H.act(pid, 'hit', 280);
      if (voters().every(p => G.votes[p.id] != null)) H.gate('Cut it in ▸', 'any', () => tally()); draw(); }
    function tally() { const n = G.opts.map(() => 0); Object.values(G.votes).forEach(i => n[i]++); const max = Math.max(...n); const tied = n.map((v, i) => v === max ? i : -1).filter(i => i >= 0); const room = tied.includes(0) ? 0 : pick(tied);
      G.gain = {}; H.players.forEach(p => { const v = G.votes[p.id]; if (v == null) return; let g = 0; if (v === room) g += 1; if (v === 0) g += 2; if (g) { p.score += g; G.gain[p.id] = g; } if (v === 0) H.act(p.id, 'hop', 820); });
      if (room === 0) G.agree++; commit(room, false, n); }
    function commit(i, forced, n) {
      const o = G.opts[i], c = vis[at], C = M.cols[c], x = C.cands[o.k]; ch[c] = o.k; lock[c] = true; G.all.push({ c, k: o.k, room: i, forced });
      G.phase = 'cut'; G.last = { i, n: n || [] }; H.sign = {};
      H.slate(H.card(`<div class="big">${i === 0 ? 'The room and the machine agree' : 'The room overrules the machine'}<small>${esc(nameOf(x))} · the machine gave it ${Math.round(o.share * 100)}% of its futures</small><video id="seav" muted playsinline autoplay style="width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;margin-top:1cqh;background:#000"></video></div>`, i === 0 ? 'gold' : 'house'));
      playTake(c, o.k);
      if (i === 0) H.act('house', 'hop', 820); else H.act('house', 'slump', 1600);
      at++; H.gate(at >= vis.length || G.n >= G.pieces ? 'Watch our recut ▸' : 'Think again ▸', 'any', think); draw();
    }
    function playTake(c, k, then) { const v = $('#seav'); if (!v) return; const C = M.cols[c], x = C.cands[k]; v.src = srcOf(x);
      v.onloadedmetadata = () => { v.currentTime = x.ss != null ? x.ss : Math.max(0, v.duration / 2 - C.d / 2); v.play().catch(() => { }); };
      clearTimeout(v._t); v._t = setTimeout(() => { v.pause(); if (then) then(); }, C.d * 1000); }
    function finale() { G.phase = 'film'; H.sign = {};
      const T = S.total(ch, vis), C0 = S.total(M.cols.map(() => 0), vis);
      H.slate(H.card(`<div class="big">Recut by the room<br>and the machine<small>they agreed ${G.agree} of ${G.all.length} times · seams ${Math.round(T.seams * 100)} (the cut: ${Math.round(C0.seams * 100)}) · ${T.weak} jarring</small><video id="seav" muted playsinline autoplay style="width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;margin-top:1cqh;background:#000"></video></div>`, 'gold'));
      let j = 0; const next = () => { if (G.phase !== 'film' || j >= G.all.length) { G.phase = 'wrap'; draw(); return; } const a = G.all[j++]; playTake(a.c, a.k, next); };
      setTimeout(next, 600); draw();
      H.gate('Skip ▸', 'any', () => { G.phase = 'wrap'; const r = rank(); if (r[0]) H.act(r[0].id, 'cheer', 2200); draw(); });
    }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    const rankHTML = () => rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}${G.gain && G.gain[p.id] && G.phase === 'cut' ? ` <span class="hint" style="margin:0">+${G.gain[p.id]}</span>` : ''}<b>${p.score}</b></div>`).join('');
    function drawSide() { const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">Sea of Takes <small>loading the lattice</small></div>`, ph);
      const C = M.cols[vis[Math.min(at, vis.length - 1)]] || M.cols[vis[vis.length - 1]];
      const optRows = show => `<div class="takes">${G.opts.map((o, i) => { const x = (G.phase === 'cut' ? M.cols[G.all[G.all.length - 1].c] : C).cands[o.k]; return `<div class="tk ${show && i === G.last.i ? 'win' : ''}"><span class="n">${'ABC'[i]}</span><span class="strip"><i style="background-image:url('${esc(thumbOf(x))}');max-width:72px"></i></span><span class="by" style="max-width:55%;text-align:left">${esc(nameOf(x)).slice(0, 44)}${show ? `<br><b style="color:var(--verm)">machine ${Math.round(o.share * 100)}%</b> · <span class="vs">${H.players.filter(p => G.votes[p.id] === i).map(p => mini(p.av)).join('') || '·'}</span>` : ''}</span></div>`; }).join('')}</div>`;
      if (ph === 'think') return H.side(`<div class="ph">Shot ${G.n} of ${G.pieces} <small>the machine is imagining futures</small></div><div class="hint" style="text-align:left">Selection, expansion, rollout, backpropagation: ${THINK} times over the lattice of takes. Its three most-visited takes become the room’s choice.</div>${rankHTML()}`, ph + G.n);
      if (ph === 'vote') { const locals = H.players.filter(p => p.local);
        const Sd = H.side(`<div class="ph">Shot ${G.n} · pick one <small>${Object.keys(G.votes).length} of ${voters().length} picked</small></div>${optRows(false)}
          ${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.opts.map((o, i) => `<button class="btn chip ${G.votes[p.id] === i ? 'on' : ''}" data-p="${p.id}" data-i="${i}">${'ABC'[i]}</button>`).join('')}</div>`).join('')}
          ${!H._gate ? `<button class="btn chip" id="force" style="margin-top:8px">cut it in now</button>` : ''}`, ph + G.n);
        Sd.querySelectorAll('[data-p]').forEach(b => b.onclick = () => vote(b.dataset.p, +b.dataset.i)); const f = $('#force'); if (f) f.onclick = tally; return; }
      if (ph === 'cut') return H.side(`<div class="ph">Shot ${G.n} · cut in <small>the machine’s favourite is A</small></div>${optRows(true)}${rankHTML()}`, ph + G.n);
      if (ph === 'film' || ph === 'wrap') return H.side(`<div class="ph">The recut <small>${G.agree} of ${G.all.length} agreed</small></div>${rankHTML()}${H.awardsHTML(H.awards([]).filter(a => a.id !== 'house'))}`, ph);
    }
    function draw() { if (M) drawSide(); else H.side(`<div class="ph">Sea of Takes <small>loading the lattice</small></div>`, 'loading'); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, n: G.n, pieces: G.pieces };
      if ((G.phase === 'vote' || G.phase === 'cut') && M) { const C = G.phase === 'cut' ? M.cols[G.all[G.all.length - 1].c] : M.cols[vis[at]]; s.opts = G.opts.map(o => ({ th: thumbOf(C.cands[o.k]), label: nameOf(C.cands[o.k]).slice(0, 60) })); s.mine = G.votes[p.id]; }
      if (G.phase === 'cut') { s.room = G.last.i; s.shares = G.opts.map(o => Math.round(o.share * 100)); s.gain = (G.gain || {})[p.id] || 0; }
      if (G.phase === 'wrap' || G.phase === 'film') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; s.agree = G.agree; }
      return s; }
    return { stateFor, draw, onMsg(p, m) { if (m.t === 'vote') vote(p.id, m.k); }, crowdTarget: () => null, performer: () => null, stop() { G.phase = 'over'; const v = $('#seav'); if (v) v.pause(); } };
  }
  function phone(S, api) { const P = S.phase, { esc } = api;
    if (P === 'loading') return { key: 'loading', status: 'loading the lattice of takes', tabs: ['me', 'throw'] };
    if (P === 'think') return { key: 'think' + S.n, status: 'Shot ' + S.n + ' of ' + S.pieces + ' · the machine is imagining futures', tabs: ['throw', 'me'] };
    if (P === 'vote') return { key: 'vote' + S.n, status: 'Shot ' + S.n + ' of ' + S.pieces, takeover: { key: 'v' + S.n + '|' + S.mine, render(el) {
      el.innerHTML = `<div class="say" style="text-align:center;font-size:26px;margin:4px 0 8px">Which take?</div><div class="answers">${S.opts.map((o, i) => `<button class="btn ${S.mine === i ? 'on' : ''}" data-k="${i}" style="display:flex;gap:10px;align-items:center"><img alt="" src="${esc(o.th)}" style="height:min(16vh,96px);width:auto;max-width:48%;aspect-ratio:16/9;object-fit:cover;border-radius:6px;flex:none"><span><b>${'ABC'[i]}</b> ${esc(o.label)}</span></button>`).join('')}</div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', k: +b.dataset.k }); }); } } };
    if (P === 'cut') return { key: 'cut' + S.n, status: (S.room === 0 ? 'The room went with the machine' : 'The room overruled the machine') + ' · machine: ' + S.shares.map((v, i) => 'ABC'[i] + ' ' + v + '%').join(' · ') + (S.gain ? ' · you +' + S.gain : ''), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'Our recut is playing', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.of}</div><div class="sub">${S.you.score} points · the room agreed with the machine ${S.agree} times</div></div>`; } } };
    return null; }
  Party.games.sea = { title: 'Sea of Takes', blurb: 'the machine imagines the futures of a Slopfeeder film; the room picks every take', options: [{ k: 'film', name: 'film', values: ['story', '26', '14', '13', '23', '20', '09', '06', '07'], def: 'story' }, { k: 'footage', name: 'footage', values: ['all', 'ai'], def: 'all' }, { k: 'pieces', name: 'shots', values: [6, 10, 16], def: 10 }], host, phone };
})();
