/* THE CASINO on the Party platform: a quiz night on the archive. A clip plays on the stand; every phone answers one of three
   (and can change its mind until someone says reveal); the archive plays the truth. Two points for a right answer, one more
   for the fastest right answer. Who said it · what they said · the decade · the shot that came next · kept or binned · the dub. */
(function () {
  const { esc, rnd, pick, shuffle, mini } = Party;
  const LETTERS = ['A', 'B', 'C'];

  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    let Q = null, R2 = '', DECADES = [];
    const G = { phase: 'loading', n: 0, rounds: H.opt.rounds, order: [], cur: null, answers: {}, all: [] };
    H.slate(H.card(`<div class="big">The Casino<small>shuffling the deck…</small></div>`, 'night'));
    const thumb = v => R2 + v.replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg');
    const from = x => x.film ? x.film + (x.year ? ' (' + x.year + ')' : '') : '';
    const others = (pool, a, n) => shuffle(pool.filter(x => x.film !== a.film && x.v !== a.v)).slice(0, n);
    const KINDS = {
      said() { const a = pick(Q.said), line = { v: a.v, t0: a.t0, t1: a.t1, cap: '“' + a.text + '”' };
        return { q: 'Which picture spoke this line?', ask: [{ ...line, black: true }], show: [line], fact: from(a), src: [a.v], opts: shuffle([{ pic: a.v, ok: true }, ...others(Q.said, a, 2).map(x => ({ pic: x.v }))]) }; },
      heard() { const a = pick(Q.heard);
        return { q: 'What did they say?', ask: [{ v: a.v, t0: a.t0, t1: a.t1 }], show: [{ v: a.v, t0: a.t0, t1: a.t1, cap: '“' + a.text + '”' }], fact: from(a), src: [a.v], opts: shuffle([{ text: a.text, ok: true }, ...a.fakes.map(t => ({ text: t }))]) }; },
      year() { const a = pick(Q.year), d = Math.floor(a.year / 10) * 10, clip = { v: a.v, t0: a.at, t1: a.at + 6 };
        return { q: 'Which decade was this filmed?', ask: [clip], show: [{ ...clip, cap: String(a.year) }], fact: from(a), src: [a.v], opts: [d, ...shuffle(DECADES.filter(x => Math.abs(x - d) >= 20)).slice(0, 2)].sort().map(x => ({ text: x + 's', ok: x === d })) }; },
      next() { const a = pick(Q.next);
        return { q: 'Which shot came next in this film?', ask: [{ v: a.v, t1: 5 }], show: [{ v: a.v, t1: 2.5 }, { v: a.nv, t1: 5, cap: 'next' }], fact: from(a), src: [a.v], opts: shuffle([{ pic: a.nv, ok: true }, ...others(Q.next, a, 2).map(x => ({ pic: x.nv }))]) }; },
      bin() { const keep = rnd() < .5, a = pick(Q.bin.filter(x => keep ? x.score >= 8 : x.score <= 4));
        return { q: 'The judge scored this shot. Kept or binned?', ask: [{ v: a.v, t1: 5 }], show: [{ v: a.v, t1: 5, cap: a.score + '/10: ' + a.why }], fact: 'The judge: ' + a.score + '/10, “' + a.why + '” · ' + from(a), src: [a.v], opts: [{ text: 'Kept', ok: keep }, { text: 'Binned', ok: !keep }] }; },
      dub() { const a = pick(Q.dub), L = a.line;
        return { q: 'Which picture did the comedy judge put under this voice?', ask: [{ v: L.v, t0: L.t0, t1: L.t1, black: true, cap: '“' + L.text + '”' }], show: [{ v: a.v, t1: L.t1 - L.t0 + 1.4, mute: true, voice: L, cap: '“' + L.text + '”' }],
          fact: 'Funny: ' + a.funny + '/10 · voice from ' + (L.film || '?') + ' · picture from ' + a.film, src: [L.v, a.v], opts: shuffle([{ pic: a.v, ok: true }, ...others(Q.dub, a, 2).map(x => ({ pic: x.v }))]) }; } };
    const NAMES = { said: 'Who said it', heard: 'What was said', year: 'The decade', next: 'What came next', bin: 'Kept or binned', dub: 'The dub' };

    // ---- the projector: clips in order, each from t0 to t1 (at most 7 s); a voice can play over a muted picture
    let tok = 0, timers = [];
    const pic = H.VP[0], voice = H.AP[0];
    function seek(el, src, t0) { if (el.dataset.u !== src) { el.dataset.u = src; el.src = src; el.addEventListener('loadedmetadata', () => { try { el.currentTime = t0; } catch (e) { } }, { once: true }); } else { try { el.currentTime = t0; } catch (e) { } } el.play().catch(() => { }); }
    function hush() { tok++; timers.forEach(clearTimeout); timers = []; pic.pause(); voice.pause(); pic.classList.remove('on'); H.cap(''); }
    function play(steps, done) { hush(); const my = tok; let n = 0;
      const go = () => { if (my !== tok) return; const s = steps[n++]; if (!s) { pic.pause(); done && done(); return; }
        H.show(null); pic.classList.toggle('on', !s.black); H.cap(s.cap || ''); pic.muted = !!s.mute;
        const t0 = s.t0 || 0, len = Math.min(7, (s.t1 != null ? s.t1 - t0 : 7)) + .25;
        seek(pic, R2 + s.v, t0);
        if (s.voice) timers.push(setTimeout(() => { if (my === tok) seek(voice, R2 + s.voice.v, s.voice.t0); }, 300));
        timers.push(setTimeout(() => { if (my !== tok) return; if (s.voice) voice.pause(); go(); }, (s.voice ? Math.max(len, s.voice.t1 - s.voice.t0 + .6) : len) * 1000 + 300)); };
      go(); }

    fetch('casino/quiz.json').then(r => r.json()).then(d => { Q = d; R2 = Q.r2; DECADES = [...new Set(Q.year.map(x => Math.floor(x.year / 10) * 10))].sort();
      const k = Object.keys(KINDS); G.order = shuffle(k); while (G.order.length < G.rounds) { const n = pick(k); if (n !== G.order[G.order.length - 1]) G.order.push(n); }
      round(); });
    function round() {
      G.n++; const kind = G.order[G.n - 1]; G.cur = Object.assign(KINDS[kind](), { kind, r: {} }); G.answers = {}; G.at = {}; G.phase = 'ask'; H.sign = {}; G.t0 = performance.now();
      H.slate(H.card(`<div class="big">Round ${G.n}<small>${esc(NAMES[kind])} · ${esc(G.cur.q)}</small></div>`, 'night'));
      setTimeout(() => { if (G.phase === 'ask' && G.cur.kind === kind) play(G.cur.ask, () => { if (G.phase === 'ask') H.slate(H.card(`<div class="big">${esc(G.cur.q)}<small>answer on your phone · change it until the reveal</small></div>`, 'night')); }); }, 1800);
      draw(); }
    const voters = () => H.players.filter(p => p.local || p.conn);
    function answer(pid, k) { if (G.phase !== 'ask' || k < 0 || k >= G.cur.opts.length) return; const first = G.answers[pid] == null; G.answers[pid] = k; G.at[pid] = performance.now(); H.sign[pid] = 'locked';
      if (first) { H.act(pid, 'hit', 280); H.say(pid, pick(['got it', 'easy', 'hmm…', 'final answer', 'sure?'])); }
      if (voters().every(p => G.answers[p.id] != null)) H.gate('Reveal ▸', 'any', reveal); draw(); }
    function reveal() {
      const right = G.cur.opts.findIndex(o => o.ok), ok = H.players.filter(p => G.answers[p.id] === right).sort((a, b) => G.at[a.id] - G.at[b.id]);
      G.gain = {}; ok.forEach((p, i) => { const g = 2 + (i === 0 ? 1 : 0); p.score += g; G.gain[p.id] = g; });
      G.phase = 'reveal'; G.right = right; G.fastest = ok[0] && ok[0].id; H.sign = {}; G.all.push(G.cur);
      H.players.forEach(p => { if (G.answers[p.id] == null) return; if (G.answers[p.id] === right) { H.act(p.id, p.id === G.fastest ? 'cheer' : 'hop', p.id === G.fastest ? 2100 : 820); if (p.id === G.fastest) H.say(p.id, 'fastest!', 1600); } else H.act(p.id, 'slump', 1800); });
      play(G.cur.show, () => { if (G.phase === 'reveal') H.slate(H.card(`<div class="big">${LETTERS[right]}<small>${esc(G.cur.fact)}</small></div>`, 'gold')); });
      H.gate(G.n < G.rounds ? 'Next round ▸' : 'Final scores ▸', 'any', () => { if (G.n < G.rounds) round(); else wrap(); }); draw(); }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function wrap() { hush(); G.phase = 'wrap'; const r = rank(), top = r[0]; G.awards = H.awards(G.all.map(x => ({ by: null, r: x.r })));
      H.slate(H.card(`<div class="big">Top of the table<br>${H.who(top.id)}<small>${top.score} points</small></div>`, 'gold')); H.act(top.id, 'cheer', 2200); H.say(top.id, 'I knew it!', 2400);
      r.slice(1).forEach((p, i) => setTimeout(() => H.act(p.id, 'bow', 1300), 500 + i * 160));
      H.gate('Back to the lobby ▸', 'any', () => H.end()); draw(); }
    const optHTML = (o, k, extra = '') => `<div class="tk ${extra}"><span class="n">${LETTERS[k]}</span>${o.pic ? `<span class="strip"><i style="background-image:url('${esc(thumb(o.pic))}');max-width:90px"></i></span>` : `<span style="flex:1;font-size:15px">${esc(o.text)}</span>`}`;
    function drawSide() {
      const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">The Casino <small>loading</small></div>`, ph);
      if (ph === 'ask') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Round ${G.n} of ${G.rounds} <small>${Object.keys(G.answers).length} of ${voters().length} answered</small></div><div class="hint" style="text-align:left;font-size:16px;color:var(--ink)">${esc(G.cur.q)}</div>
          <div class="takes">${G.cur.opts.map((o, k) => optHTML(o, k) + `<span class="by"></span></div>`).join('')}</div>
          ${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.cur.opts.map((o, k) => `<button class="btn chip ${G.answers[p.id] === k ? 'on' : ''}" data-p="${p.id}" data-k="${k}">${LETTERS[k]}</button>`).join('')}</div>`).join('')}
          <div class="row" style="margin-top:8px"><button class="btn chip" id="rp">↻ replay the clip</button>${!H._gate ? `<button class="btn chip" id="force">reveal now</button>` : ''}</div>`, ph + G.n);
        S.querySelectorAll('[data-p]').forEach(b => b.onclick = () => answer(b.dataset.p, +b.dataset.k)); $('#rp').onclick = () => play(G.cur.ask); const f = $('#force'); if (f) f.onclick = reveal; return; }
      if (ph === 'reveal') { const S = H.side(`<div class="ph">Round ${G.n} · the answer <small>+2 right · +1 fastest</small></div>
          <div class="takes">${G.cur.opts.map((o, k) => optHTML(o, k, k === G.right ? 'win' : '') + `<span class="by vs">${H.players.filter(p => G.answers[p.id] === k).map(p => mini(p.av)).join('') || '·'}</span></div>`).join('')}</div>
          <div class="hint" style="text-align:left">${esc(G.cur.fact)}</div><div class="row" style="margin-top:6px"><button class="btn chip" id="rp">↻ replay</button><button class="btn chip" id="srcB">source ↗</button></div>
          ${rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}${G.gain[p.id] ? ` <span class="hint" style="margin:0">+${G.gain[p.id]}</span>` : ''}<b>${p.score}</b></div>`).join('')}`, ph + G.n);
        $('#rp').onclick = () => play(G.cur.show); $('#srcB').onclick = () => window.Attrib && Attrib.show(G.cur.src.map(v => ({ role: 'the clip', video: R2 + v }))); return S; }
      if (ph === 'wrap') return H.side(`<div class="ph">Final scores <small>${G.rounds} rounds</small></div>${rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}<b>${p.score}</b></div>`).join('')}${H.awardsHTML(G.awards.filter(a => a.id !== 'house'))}`, ph);
    }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, n: G.n, rounds: G.rounds };
      if (G.cur && (G.phase === 'ask' || G.phase === 'reveal')) { s.q = G.cur.q; s.kind = NAMES[G.cur.kind]; s.opts = G.cur.opts.map(o => o.pic ? { th: thumb(o.pic) } : { text: o.text }); s.mine = G.answers[p.id]; s.answered = Object.keys(G.answers).length; s.of = voters().length; }
      if (G.phase === 'reveal') { s.right = G.right; s.gain = G.gain[p.id] || 0; s.fastest = G.fastest === p.id; s.fact = G.cur.fact; }
      if (G.phase === 'wrap') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.of = r.length; }
      return s; }
    return { stateFor, draw, house: false, onMsg(p, m) { if (m.t === 'answer') answer(p.id, m.k); }, crowdTarget: () => G.cur, performer: () => null, stop() { hush(); } };
  }

  function phone(S, api) {
    const P = S.phase;
    if (P === 'loading') return { key: 'loading', status: 'shuffling the deck…', tabs: ['me', 'throw'] };
    if (P === 'ask') return { key: 'ask' + S.n, status: 'Round ' + S.n + ' of ' + S.rounds + ' · ' + esc(S.kind) + ' · ' + S.answered + ' of ' + S.of + ' answered', takeover: { key: 'ask' + S.n + '|' + S.mine, render(el) {
      const pics = S.opts[0] && S.opts[0].th;
      el.innerHTML = `<div class="say" style="text-align:center;font-size:26px;margin:4px 0 8px">${esc(S.q)}</div><div class="answers ${pics ? 'pics' : ''}">${S.opts.map((o, k) => o.th ? `<button class="tile ${S.mine === k ? 'on' : ''}" data-k="${k}" style="aspect-ratio:3/4"><img alt="" src="${esc(o.th)}"><span>${LETTERS[k]}</span></button>` : `<button class="btn ${S.mine === k ? 'on' : ''}" data-k="${k}"><span class="k">${LETTERS[k]}</span>${esc(o.text)}</button>`).join('')}</div>
        <div class="sub" style="text-align:center;margin-top:8px">${S.mine != null ? 'Locked in ' + LETTERS[S.mine] + ' · tap another to change' : 'watch the TV, then tap'}</div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'answer', k: +b.dataset.k }); }); } } };
    if (P === 'reveal') { const right = S.mine === S.right, none = S.mine == null;
      return { key: 'reveal' + S.n, status: (none ? 'No answer · ' : right ? (S.fastest ? 'Right, and fastest! +' : 'Right! +') + S.gain + ' · ' : 'Not this time · ') + 'the answer is ' + LETTERS[S.right] + ' · throw something', tab: 'throw', tabs: ['throw', 'me'] }; }
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.of}</div><div class="sub">${S.you.score} points</div></div>`; } } };
    return null;
  }
  Party.games.quiz = { title: 'The Casino', blurb: 'a quiz night: a clip plays, everyone answers on their phone, the archive shows the truth', options: [{ k: 'rounds', name: 'rounds', values: [6, 10, 15], def: 10 }], host, phone };
})();
