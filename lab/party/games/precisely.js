/* PRECISELY SO on the Party platform: a film in chapters, after the Wes Anderson cineosis. Each round is a chapter on one of its
   eight themes (symmetry, facing the camera, pastel, from above, the diorama, uniforms, title cards, compartments). Every phone
   is dealt six of the archive's most Andersonian shots on the theme, lays three of them in order, and writes the chapter's title
   card ("Chapter 2: In which…"). The chapters screen unsigned, title card first; the room circles one; the strict judge names its
   own (the shots it measured most Andersonian); the circled chapter goes into the film. At the end, the film in its chapters. */
(function () {
  const { esc, rnd, pick, shuffle, mini } = Party;
  const PROMPTS = ['In which nobody moves', 'In which the porter is late', 'In which a door will not open', 'In which everyone faces us', 'In which the pastry arrives', 'In which a uniform is issued'];
  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    const G = { phase: 'loading', ch: 0, chapters: H.opt.chapters, order: [], hands: {}, picks: {}, titles: {}, sent: {}, subs: [], votes: {}, film: [], all: [] };
    let W = null, music = [], R2 = '', url, thumb;
    H.houseScore = 0;
    H.slate(H.card(`<div class="big">Precisely So<small>a film in chapters · loading the archive’s most Andersonian shots…</small></div>`, 'rose'));
    Promise.all([fetch('party/wes.json').then(r => r.json()), fetch('pictures/rushes.json').then(r => r.json()).catch(() => null)]).then(([w, rs]) => { W = w; R2 = W.r2;
      url = v => Array.isArray(v) ? R2 + W.P[v[0]] + '/clips/' + v[1] + '.mp4' : R2 + v; thumb = v => url(v).replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg');
      if (rs) music = rs.music.map(m => Array.isArray(m.v) ? rs.r2 + rs.P[m.v[0]] + '/clips/' + m.v[1] + '.mp4' : rs.r2 + m.v);
      G.order = shuffle(Object.keys(W.chapters)); chapter(); });
    // ---- the projector: a title card, then three shots that swap at the cut, a music bed beneath
    const vids = [H.VP[0], H.VP[1]], bed = H.AP[0]; let tok = 0, tm = [];
    function stop() { tok++; tm.forEach(clearTimeout); tm = []; vids.forEach(v => { v.pause(); v.classList.remove('on'); }); bed.pause(); H.cap(''); }
    function screenChapter(sub, n, done, opt = {}) { stop(); const my = tok;
      H.slate(H.card(`<div class="big" style="font-size:9cqh">Chapter ${n}<br><span style="font-size:12cqh">${esc(sub.title)}</span><small>${esc(W.chapters[sub.theme].name)}</small></div>`, 'rose'));
      if (music.length && opt.music !== false) { bed.src = pick(music); bed.volume = .45; bed.play().catch(() => { }); }
      const shots = sub.shots; let side = 0; const load = (v, s) => { const u = url(s.v); if (v.dataset.u !== u) { v.dataset.u = u; v.src = u; } };
      load(vids[0], shots[0]); if (shots[1]) load(vids[1], shots[1]);
      const step = i => { if (my !== tok) return; if (i >= shots.length) { if (opt.keepBed) tm.push(setTimeout(() => done && done(), 200)); else { stop(); done && done(); } return; }
        H.show(null); const v = vids[side], o = vids[1 - side]; load(v, shots[i]); v.muted = true; try { v.currentTime = Math.min(1, (shots[i].d || 3) / 4); } catch (e) { } v.play().catch(() => { }); v.classList.add('on'); o.classList.remove('on'); o.pause();
        H.cap(shots[i].f + (shots[i].y ? ' · ' + shots[i].y : '')); side = 1 - side; if (shots[i + 1]) load(vids[side], shots[i + 1]);
        tm.push(setTimeout(() => step(i + 1), 2700)); };
      tm.push(setTimeout(() => step(0), 3000)); }
    function chapter() {
      G.ch++; stop(); G.theme = G.order[(G.ch - 1) % G.order.length]; G.hands = {}; G.picks = {}; G.titles = {}; G.sent = {}; G.subs = []; G.votes = {}; H.sign = {}; G.phase = 'deal';
      const pool = shuffle(W.chapters[G.theme].shots); H.players.forEach((p, i) => { G.hands[p.id] = pool.slice((i * 6) % Math.max(6, pool.length - 6), (i * 6) % Math.max(6, pool.length - 6) + 6); G.picks[p.id] = []; });
      H.slate(H.card(`<div class="big">Chapter ${G.ch}<br>${esc(W.chapters[G.theme].name)}<small>three shots in order, and a title card · on your phone</small></div>`, 'rose'));
      draw(); }
    const handOf = id => { if (!G.hands[id]) { G.hands[id] = shuffle(W.chapters[G.theme].shots).slice(0, 6); G.picks[id] = []; } return G.hands[id]; };
    const voters = () => H.players.filter(p => p.local || p.conn);
    function toggle(pid, k) { if (G.phase !== 'deal') return; const pk = G.picks[pid] || (G.picks[pid] = []), i = pk.indexOf(k); if (i >= 0) pk.splice(i, 1); else if (pk.length < 3) pk.push(k); unsend(pid); draw(); }
    function title(pid, t) { if (G.phase !== 'deal') return; G.titles[pid] = String(t || '').slice(0, 60); draw(); }
    const unsend = pid => { if (G.sent[pid]) { G.sent[pid] = false; delete H.sign[pid]; if (H._gate) H.ungate(); } };
    function send(pid) { if (G.phase !== 'deal' || (G.picks[pid] || []).length !== 3) return; G.sent[pid] = true; H.sign[pid] = 'in the can'; H.act(pid, 'hop', 820);       if (voters().every(p => G.sent[p.id])) H.gate('Screen the chapters ▸', 'any', screen0); draw(); }
    function screen0() { G.subs = shuffle(H.players.filter(p => G.sent[p.id]).map(p => { const h = handOf(p.id), shots = G.picks[p.id].map(k => h[k]); return { by: p.id, theme: G.theme, shots, title: (G.titles[p.id] || '').trim() || pick(PROMPTS), judge: shots.reduce((a, s) => a + (s.js || s.a * 2.5 || 0) + (s.sym || 0) * 2, 0) / 3, r: {} }; }));
      G.phase = 'screen'; G.k = 0; one(); }
    function one() { const s = G.subs[G.k]; G.watching = true; H.crowdShow(s); draw();
      screenChapter(s, G.ch, () => { G.watching = false; H.slate(H.card(`<div class="big">${esc(s.title)}<small>${G.k + 1 < G.subs.length ? 'the next chapter when you’re ready' : 'that’s all of them'}</small></div>`, 'rose'));
        H.gate(G.k + 1 < G.subs.length ? 'Next chapter ▸' : 'Circle one ▸', 'any', () => { if (G.k + 1 < G.subs.length) { G.k++; one(); } else { G.phase = 'circle'; H.crowdShow(null); H.slate(H.card(`<div class="big">Circle one<small>not your own · the judge picks too</small></div>`, 'night')); draw(); } }); draw(); }); }
    function vote(pid, k) { if (G.phase !== 'circle' || k < 0 || k >= G.subs.length || G.subs[k].by === pid) return; const first = G.votes[pid] == null; G.votes[pid] = k; H.sign[pid] = 'circled'; if (first) H.act(pid, 'hit', 280);
      if (voters().every(p => G.votes[p.id] != null || G.subs.every(s => s.by === p.id))) H.gate('Reveal ▸', 'any', reveal); draw(); }
    function reveal() {
      const n = G.subs.map(() => 0); Object.values(G.votes).forEach(k => n[k]++); const max = Math.max(...n); const tied = n.map((v, k) => v === max ? k : -1).filter(k => k >= 0); const win = pick(tied);
      const judge = G.subs.reduce((b, s, k) => s.judge > G.subs[b].judge ? k : b, 0); G.win = win; G.judge = judge; G.n = n; G.gain = {}; H.sign = {};
      G.subs.forEach((s, k) => { const p = P(s.by); if (!p) return; const g = n[k] + (k === win ? 2 : 0) + (k === judge ? 1 : 0); if (g) { p.score += g; G.gain[p.id] = g; } });
      G.film.push(Object.assign({ n: G.ch }, G.subs[win])); G.all = G.all.concat(G.subs); G.phase = 'reveal';
      const wp = P(G.subs[win].by), jp = P(G.subs[judge].by);
      H.slate(H.card(`<div class="big">“${esc(G.subs[win].title)}”<br>${wp ? H.who(wp.id) : ''}<small>${n[win]} circled${judge === win ? ' · and the judge says: precisely so.' : ' · the judge preferred ' + (jp ? esc(jp.name) + '’s' : 'another') + ' chapter'}</small></div>`, 'gold'));
      if (wp) H.act(wp.id, 'cheer', 2100); if (jp && jp !== wp) { H.act(jp.id, 'hop', 820); H.say(jp.id, 'precisely so', 1800); }
      H.gate(G.ch < G.chapters ? 'Next chapter ▸' : 'Our film ▸', 'any', () => { if (G.ch < G.chapters) chapter(); else finale(); }); draw(); }
    function finale() { G.phase = 'film'; let i = 0; H.sign = {};
      H.slate(H.card(`<div class="big">A film in ${G.film.length} chapters<small>made by the room, precisely</small></div>`, 'gold'));
      const next = () => { if (G.phase !== 'film') return; if (i >= G.film.length) { stop(); H.slate(H.card(`<div class="big">The end</div>`, 'gold')); wrap(); return; } const c = G.film[i++]; screenChapter(c, c.n, next, { keepBed: i < G.film.length, music: i === 1 }); };
      tm.push(setTimeout(next, 2500));
      H.gate('Skip ▸', 'any', () => { stop(); wrap(); }); draw(); }
    function wrap() { if (G.phase === 'wrap') return; G.phase = 'wrap'; const r = rank(); if (r[0]) H.act(r[0].id, 'cheer', 2200); G.awards = H.awards(G.all); H.gate('Edit the film ▸', 'any', () => { H.seed = toFilm(); H.playGame('cut'); }); draw(); }
    function toFilm() { const F = Cut.blank('A film in ' + G.film.length + ' chapters');
      G.film.forEach(c => { const card = Cut.card('Chapter ' + c.n + '\n' + c.title, 3); F.clips.push(card); c.shots.forEach(s => { const d = s.d || 4, t0 = Math.min(1, d / 4); F.clips.push(Cut.shot(url(s.v), +t0.toFixed(2), +Math.min(d, t0 + 2.7).toFixed(2), { d, label: s.f })); }); });
      if (music.length && F.clips.length) F.sounds.push(Cut.music(F.clips[0].id, pick(music), 0, Cut.starts(F).total, { vol: .5 }));
      return F; }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function drawSide() { const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">Precisely So <small>loading</small></div>`, ph);
      if (ph === 'deal') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Chapter ${G.ch} of ${G.chapters} <small>${Object.values(G.sent).filter(Boolean).length} of ${voters().length} in · ${esc(W.chapters[G.theme].name)}</small></div><div class="hint" style="text-align:left">Lay three shots in order and write the title card.</div>
          ${locals.map(p => { const h = handOf(p.id), pk = G.picks[p.id] || []; return `<div style="margin-top:6px">${mini(p.av)} ${esc(p.name)}<div class="tk" style="flex-wrap:wrap">${h.map((s, k) => `<button class="btn chip ${pk.includes(k) ? 'on' : ''}" data-p="${p.id}" data-k="${k}" style="padding:2px"><i style="display:block;width:44px;aspect-ratio:4/3;background:#000 center/cover;background-image:url('${esc(thumb(s.v))}')"></i>${pk.includes(k) ? pk.indexOf(k) + 1 : ''}</button>`).join('')}</div><div class="row"><input type="text" data-t="${p.id}" maxlength="60" placeholder="In which…" value="${esc(G.titles[p.id] || '')}"><button class="btn chip" data-send="${p.id}">${G.sent[p.id] ? 'in ✓' : 'send'}</button></div></div>`; }).join('')}
          ${!H._gate && Object.values(G.sent).some(Boolean) ? `<button class="btn chip" id="force" style="margin-top:8px">screen now</button>` : ''}`, ph + G.ch);
        S.querySelectorAll('[data-k]').forEach(b => b.onclick = () => toggle(b.dataset.p, +b.dataset.k)); S.querySelectorAll('[data-t]').forEach(i => i.onchange = () => title(i.dataset.t, i.value)); S.querySelectorAll('[data-send]').forEach(b => b.onclick = () => { const i = S.querySelector(`[data-t="${b.dataset.send}"]`); if (i) G.titles[b.dataset.send] = i.value.slice(0, 60); send(b.dataset.send); }); const f = $('#force'); if (f) f.onclick = screen0; return; }
      const strip = s => s.shots.map(x => `<i style="background-image:url('${esc(thumb(x.v))}')"></i>`).join('');
      const rows = show => `<div class="takes">${G.subs.map((s, k) => `<div class="tk ${show && k === G.win ? 'win' : ''} ${ph === 'screen' && k === G.k ? 'now' : ''}"><span class="n">${k + 1}</span><span style="flex:1;min-width:0"><span class="strip">${ph !== 'screen' || k < G.k || (k === G.k && !G.watching) ? strip(s) : ''}</span><span class="hint" style="margin:0;display:block;text-align:left">“${esc(s.title)}”${show ? ' · ' + (P(s.by) ? esc(P(s.by).name) : '') + (k === G.judge ? ' · the judge’s pick' : '') : ''}</span></span><span class="by vs">${show ? Object.entries(G.votes).filter(([, v]) => v === k).map(([id]) => P(id) ? mini(P(id).av) : '').join('') : ''}${H.crowdText(s) ? `<br><span class="hint" style="margin:0">${esc(H.crowdText(s))}</span>` : ''}</span></div>`).join('')}</div>`;
      if (ph === 'screen') return H.side(`<div class="ph">Chapter ${G.ch} · screening <small>unsigned</small></div>${rows(false)}`, ph + G.k);
      if (ph === 'circle') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Circle one <small>${Object.keys(G.votes).length} of ${voters().length}</small></div>${rows(false)}${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.subs.map((s, k) => `<button class="btn chip ${G.votes[p.id] === k ? 'on' : ''}" data-p="${p.id}" data-k="${k}" ${s.by === p.id ? 'disabled' : ''}>${k + 1}</button>`).join('')}</div>`).join('')}${!H._gate ? `<button class="btn chip" id="force" style="margin-top:8px">reveal now</button>` : ''}`, ph);
        S.querySelectorAll('[data-p]').forEach(b => b.onclick = () => vote(b.dataset.p, +b.dataset.k)); const f = $('#force'); if (f) f.onclick = reveal; return; }
      if (ph === 'reveal') return H.side(`<div class="ph">Chapter ${G.ch} <small>circles</small></div>${rows(true)}`, ph + G.ch);
      if (ph === 'film' || ph === 'wrap') return H.side(`<div class="ph">Our film <small>${G.film.length} chapters</small></div><div class="ledger" style="font-size:13px">${G.film.map(c => `<div><b>CHAPTER ${c.n}</b> — ${esc(c.title)} <span style="color:#7a6a58">(${esc(W.chapters[c.theme].name)} · ${esc((P(c.by) || {}).name || '')})</span></div>`).join('')}</div>${rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}<b>${p.score}</b></div>`).join('')}${G.awards ? H.awardsHTML(G.awards) : ''}`, ph);
    }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, ch: G.ch, chapters: G.chapters };
      if (G.theme) s.theme = W.chapters[G.theme].name;
      if (G.phase === 'deal') { s.hand = handOf(p.id).map(x => ({ th: thumb(x.v), f: x.f, y: x.y })); s.picks = G.picks[p.id] || []; s.title = G.titles[p.id] || ''; s.sent = !!G.sent[p.id]; s.in = Object.values(G.sent).filter(Boolean).length; s.of = voters().length; s.prompt = PROMPTS[(G.ch + H.players.indexOf(p)) % PROMPTS.length]; }
      if (G.phase === 'screen') { s.k = G.k + 1; s.nS = G.subs.length; }
      if (G.phase === 'circle') { s.nS = G.subs.length; s.own = G.subs.findIndex(x => x.by === p.id); s.mine = G.votes[p.id]; s.titles = G.subs.map(x => x.title); }
      if (G.phase === 'reveal') { s.gain = (G.gain || {})[p.id] || 0; s.winTitle = G.subs[G.win].title; }
      if (G.phase === 'wrap') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.ofN = r.length; }
      return s; }
    return { stateFor, draw, house: false, onMsg(p, m) { if (m.t === 'toggle') toggle(p.id, m.k); if (m.t === 'title') title(p.id, m.v); if (m.t === 'send') { if (m.v != null) G.titles[p.id] = String(m.v).slice(0, 60); send(p.id); } if (m.t === 'vote') vote(p.id, m.k); },
      crowdTarget: () => G.phase === 'screen' ? G.subs[G.k] : null, performer: () => null, stop() { G.phase = 'over'; stop(); } };
  }
  function phone(S, api) { const P = S.phase, { esc } = api;
    if (P === 'loading') return { key: 'loading', status: 'loading the shots', tabs: ['me', 'throw'] };
    if (P === 'deal') return { key: 'deal' + S.ch, status: 'Chapter ' + S.ch + ' of ' + S.chapters + ' · ' + esc(S.theme) + ' · ' + S.in + ' of ' + S.of + ' in', takeover: { key: 'deal' + S.ch + S.picks.join() + S.sent, render(el) {
      el.innerHTML = `<div class="problem"><b>Chapter ${S.ch}: ${esc(S.theme)}</b>tap three shots in the order they play</div>
        <div class="tiles">${S.hand.map((x, k) => `<button class="tile ${S.picks.includes(k) ? 'on' : ''}" data-k="${k}"><img alt="" src="${esc(x.th)}"><span>${S.picks.includes(k) ? '<b style="font-size:16px">' + (S.picks.indexOf(k) + 1) + '</b> ' : ''}${esc(x.f)}</span></button>`).join('')}</div>
        <div class="lbl">the title card</div><div class="row"><span style="font:400 18px var(--title);color:var(--verm)">Chapter ${S.ch}:</span><input type="text" id="ttl" maxlength="60" placeholder="${esc(S.prompt)}…" value="${esc(S.title || '')}"></div>
        <button class="btn cta" id="sendB" ${S.picks.length === 3 && !S.sent ? '' : 'disabled'}>${S.sent ? 'in the can · change anything to resend' : S.picks.length === 3 ? 'send my chapter ▸' : 'pick ' + (3 - S.picks.length) + ' more'}</button>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'toggle', k: +b.dataset.k }); });
      const t = el.querySelector('#ttl'); let tt = 0; t.oninput = () => { clearTimeout(tt); tt = setTimeout(() => api.send({ t: 'title', v: t.value }), 350); }; t.onchange = () => api.send({ t: 'title', v: t.value });
      el.querySelector('#sendB').onclick = () => { api.buzz(30); api.send({ t: 'send', v: t.value }); }; } } };
    if (P === 'screen') return { key: 'screen' + S.k, status: 'Chapter ' + S.k + ' of ' + S.nS + ' · unsigned', tab: 'throw', tabs: ['throw', 'me'] };
    if (P === 'circle') return { key: 'circle', takeover: { key: 'c' + S.mine, render(el) {
      el.innerHTML = `<div class="center"><div class="say">Circle one</div><div class="sub">the chapter that goes in the film · not your own</div><div class="answers" style="width:100%;margin-top:10px">${S.titles.map((t, k) => `<button class="btn ${S.mine === k ? 'on' : ''}" data-k="${k}" ${k === S.own ? 'disabled' : ''}><span class="k">${k + 1}</span>“${esc(t)}”</button>`).join('')}</div></div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', k: +b.dataset.k }); }); } } };
    if (P === 'reveal') return { key: 'reveal' + S.ch, status: 'In the film: “' + esc(S.winTitle) + '”' + (S.gain ? ' · you +' + S.gain : ''), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'Our film is playing, chapter by chapter', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.ofN}</div><div class="sub">${S.you.score} points</div></div>`; } } };
    return null; }
  Party.games.precisely = { title: 'Precisely So', blurb: 'a film in chapters after Wes Anderson: three shots and a title card from every phone; the room and the strict judge choose', options: [{ k: 'chapters', name: 'chapters', values: [3, 4, 5], def: 4 }], host, phone };
})();
