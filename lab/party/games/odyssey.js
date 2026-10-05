/* THE FOUND ODYSSEY · CASTING on the Party platform. The Odyssey spoken by the archive itself, cast by the room. For each line of
   Homer the archive offers its ways of saying it (word by word, a collage of many voices; in one breath, one archival sentence
   that means it; the gist, one person saying it their own way; borrowed words, kept for their sound) and pictures to put under
   it. The stand plays them; every phone picks a voice and a picture; the chorus decides; the line is cast and played. A point
   for every choice you share with the room. At the end, the scene, cast, played through. */
(function () {
  const { esc, rnd, pick, shuffle, mini } = Party;
  const AB = ['A', 'B', 'C'];
  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    const G = { phase: 'loading', i: -1, lines: [], cast: [], votes: {}, all: [] };
    let O = null, url, thumb;
    H.houseScore = 0;
    H.slate(H.card(`<div class="big">The Found Odyssey<small>the Odyssey spoken by the archive · cast by the room · loading…</small></div>`, 'sea'));
    fetch('party/odyssey.json').then(r => r.json()).then(o => { O = o;
      url = i => { const c = O.clips[i]; return Array.isArray(c) ? O.r2 + O.P[c[0]] + '/clips/' + c[1] + '.mp4' : c; }; thumb = i => url(i).replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg');
      const ok = O.scenes.filter(s => s.lines.length >= H.opt.lines); G.scene = pick(ok.length ? ok : O.scenes); G.lines = G.scene.lines.slice(0, H.opt.lines); next(); });
    const book = () => { const m = /B(\d+)-S(\d+)/.exec(G.scene.id); return m ? 'Book ' + (+m[1]) + ' · scene ' + (+m[2]) : ''; };
    // ---- voices: archival fragments, word by word, on the stand's audio players (the next one loads while this one speaks)
    let tok = 0, tm = [];
    function hush() { tok++; tm.forEach(clearTimeout); tm = []; H.AP.forEach(a => a.pause()); H.VP.slice(0, 2).forEach(v => { v.pause(); v.classList.remove('on'); }); H.cap(''); }
    function prime(a, fr) { const u = url(fr[0]); if (a.dataset.u !== u) { a.dataset.u = u; a.src = u; } a._t0 = fr[1]; a.addEventListener('loadedmetadata', () => { try { a.currentTime = fr[1]; } catch (e) { } }, { once: true }); try { a.currentTime = fr[1]; } catch (e) { } }
    function speak(frs, done, my) { let i = 0, said = ''; const A = H.AP; prime(A[0], frs[0]); if (frs[1]) prime(A[1], frs[1]);
      const go = () => { if (my !== tok) return; if (i >= frs.length) { done && done(); return; } const a = A[i % A.length], fr = frs[i];
        try { a.currentTime = fr[1]; } catch (e) { } a.volume = 1; a.play().catch(() => { }); said += (said ? ' ' : '') + fr[3]; H.cap(said);
        const nx = frs[i + 2]; if (nx) prime(A[(i + 2) % A.length], nx); i++;
        tm.push(setTimeout(() => { a.pause(); go(); }, Math.max(.2, fr[2] - fr[1]) * 1000 + 60)); };
      tm.push(setTimeout(go, 250)); }
    function picture(p) { const v = H.VP[0], u = url(p.v); if (v.dataset.u !== u) { v.dataset.u = u; v.src = u; } v.muted = true; v.loop = true; try { v.currentTime = p.in || 0; } catch (e) { } v.addEventListener('loadedmetadata', () => { try { v.currentTime = p.in || 0; } catch (e) { } }, { once: true }); H.show(null); v.classList.add('on'); v.play().catch(() => { }); }
    const picsFor = i => (G.scene.pics[i % G.scene.pics.length] || []).slice(0, 3);
    // ---- a line: the card, the voices, the pictures; then everyone casts
    function next() {
      G.i++; hush(); if (G.i >= G.lines.length) return finale();
      G.phase = 'cast'; G.votes = {}; H.sign = {}; const L = G.lines[G.i];
      H.slate(H.card(`<div class="big" style="font-size:9cqh">“${esc(L.text)}”<small>${esc(L.who)} · ${esc(book())} · line ${G.i + 1} of ${G.lines.length}</small></div>`, 'sea'));
      draw(); setTimeout(() => { if (G.phase === 'cast' && G.lines[G.i] === L) audition(); }, 2600); }
    function audition(only) { hush(); const my = tok, L = G.lines[G.i], vs = L.vs, ps = picsFor(G.i); let k = 0;
      const voice = () => { if (my !== tok) return; if (k >= vs.length || (only && only.v == null)) return pics(); const j = only && only.v != null ? only.v : k;
        H.slate(H.card(`<div class="big">Voice ${AB[j]}<small>${esc(vs[j].label)}</small></div>`, 'night')); tm.push(setTimeout(() => { if (my !== tok) return; H.show(null); speak(vs[j].fr, () => { if (only) return; k++; tm.push(setTimeout(voice, 500)); }, my); }, 1100)); };
      const pics = () => { if (my !== tok || (only && only.v != null)) return; let j = only && only.p != null ? only.p : 0; const show = () => { if (my !== tok || j >= ps.length) { if (!only) H.slate(H.card(`<div class="big">Cast it<small>a voice and a picture · on your phone</small></div>`, 'sea')); return; }
          picture(ps[j]); H.cap('picture ' + (j + 1)); tm.push(setTimeout(() => { if (only) return; j++; show(); }, 2600)); }; show(); };
      voice(); }
    const voters = () => H.players.filter(p => p.local || p.conn);
    function choose(pid, kind, k) { if (G.phase !== 'cast') return; const L = G.lines[G.i], n = kind === 'v' ? L.vs.length : picsFor(G.i).length; if (k < 0 || k >= n) return;
      const v = G.votes[pid] || (G.votes[pid] = {}); v[kind] = k; const done = v.v != null && v.p != null; if (done && !H.sign[pid]) { H.sign[pid] = 'cast'; H.act(pid, 'hit', 280); }
      if (voters().every(p => G.votes[p.id] && G.votes[p.id].v != null && G.votes[p.id].p != null)) H.gate('Cast it ▸', 'any', castIt); draw(); }
    function castIt() { const L = G.lines[G.i], maj = kind => { const n = {}; Object.values(G.votes).forEach(v => { if (v[kind] != null) n[v[kind]] = (n[v[kind]] || 0) + 1; }); const max = Math.max(0, ...Object.values(n)); const top = Object.keys(n).filter(k => n[k] === max).map(Number); return top.length ? pick(top) : 0; };
      const v = maj('v'), p = maj('p'); G.choice = { v, p }; G.gain = {}; H.sign = {};
      H.players.forEach(pl => { const x = G.votes[pl.id]; if (!x) return; const g = (x.v === v ? 1 : 0) + (x.p === p ? 1 : 0); if (g) { pl.score += g; G.gain[pl.id] = g; } H.act(pl.id, g === 2 ? 'hop' : g ? 'hit' : 'slump', g === 2 ? 820 : g ? 280 : 1600); });
      G.cast.push({ i: G.i, text: L.text, who: L.who, voice: L.vs[v], pic: picsFor(G.i)[p], v, p, r: {} }); G.phase = 'cast-done';
      play(G.cast[G.cast.length - 1]);
      H.gate(G.i + 1 < G.lines.length ? 'Next line ▸' : 'Play our scene ▸', 'any', next); draw(); }
    function play(c, done) { hush(); const my = tok; picture(c.pic); H.crowdShow(c); speak(c.voice.fr, () => { tm.push(setTimeout(() => done && done(), 700)); }, my); }
    function finale() { G.phase = 'film'; H.sign = {}; H.crowdShow(null); let k = 0;
      H.slate(H.card(`<div class="big">The Found Odyssey<small>${esc(book())} · cast by the room</small></div>`, 'sea'));
      const go = () => { if (G.phase !== 'film') return; if (k >= G.cast.length) { hush(); wrap(); return; } play(G.cast[k++], go); };
      tm.push(setTimeout(go, 2600));
      H.gate('Skip ▸', 'any', () => { hush(); wrap(); }); draw(); }
    function wrap() { if (G.phase === 'wrap') return; G.phase = 'wrap'; H.slate(H.card(`<div class="big">The chorus<small>who chose with the room most often</small></div>`, 'gold')); const r = rank(); if (r[0]) H.act(r[0].id, 'cheer', 2200); G.awards = H.awards(G.cast.map(c => ({ by: null, r: c.r }))); H.gate('Edit the film ▸', 'any', () => { H.seed = toFilm(); H.playGame('cut'); }); draw(); }
    function toFilm() { const F = Cut.blank('The Found Odyssey · ' + book()); F.clips.push(Cut.card('The Found Odyssey\n' + book(), 2.5));
      G.cast.forEach(c => { const fr = c.voice.fr.map(x => [url(x[0]), x[1], x[2], x[3]]), L = fr.reduce((a, x) => a + Math.max(.1, x[2] - x[1]) + .06, 0) + .9, t0 = c.pic.in || 0;
        const clip = Cut.shot(url(c.pic.v), t0, t0 + L, { label: c.text }); F.clips.push(clip); F.sounds.push(Cut.frags(clip.id, fr, { text: c.text })); });
      return F; }
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function drawSide() { const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">The Found Odyssey <small>loading</small></div>`, ph);
      const L = G.lines[G.i];
      if (ph === 'cast' || ph === 'cast-done') { const locals = ph === 'cast' ? H.players.filter(p => p.local) : [], show = ph === 'cast-done', ps = picsFor(G.i);
        const tally = (kind, k) => H.players.filter(p => G.votes[p.id] && G.votes[p.id][kind] === k).map(p => mini(p.av)).join('');
        const S = H.side(`<div class="ph">Line ${G.i + 1} of ${G.lines.length} <small>${show ? 'with the room' : Object.values(G.votes).filter(v => v.v != null && v.p != null).length + ' of ' + voters().length + ' cast'}</small></div><div class="hint" style="text-align:left;color:var(--ink);font-size:16px">“${esc(L.text)}” <span style="color:#7a6a58">— ${esc(L.who)}</span></div>
          <div class="lbl">voices</div><div class="takes">${L.vs.map((v, k) => `<div class="tk ${show && G.choice.v === k ? 'win' : ''}"><span class="n">${AB[k]}</span><span style="flex:1;font-size:14px">${esc(v.label)} · <span class="hint" style="margin:0">${esc(v.fr.map(f => f[3]).join(' ').slice(0, 80))}</span></span><span class="by vs">${show ? tally('v', k) : ''}</span><button class="btn chip" data-hear="${k}">▶</button></div>`).join('')}</div>
          <div class="lbl">pictures</div><div class="takes">${ps.map((p, k) => `<div class="tk ${show && G.choice.p === k ? 'win' : ''}"><span class="n">${k + 1}</span><span class="strip"><i style="background-image:url('${esc(thumb(p.v))}');max-width:70px"></i></span><span class="by vs">${show ? tally('p', k) : ''}</span><button class="btn chip" data-see="${k}">▶</button></div>`).join('')}</div>
          ${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${L.vs.map((v, k) => `<button class="btn chip ${(G.votes[p.id] || {}).v === k ? 'on' : ''}" data-p="${p.id}" data-kind="v" data-k="${k}">${AB[k]}</button>`).join('')}${ps.map((x, k) => `<button class="btn chip ${(G.votes[p.id] || {}).p === k ? 'on' : ''}" data-p="${p.id}" data-kind="p" data-k="${k}">${k + 1}</button>`).join('')}</div>`).join('')}
          ${ph === 'cast' && !H._gate ? `<div class="row" style="margin-top:6px"><button class="btn chip" id="aud">↻ hear them all again</button><button class="btn chip" id="force">cast it now</button></div>` : ''}`, ph + G.i);
        S.querySelectorAll('[data-hear]').forEach(b => b.onclick = () => audition({ v: +b.dataset.hear })); S.querySelectorAll('[data-see]').forEach(b => b.onclick = () => audition({ p: +b.dataset.see }));
        S.querySelectorAll('[data-kind]').forEach(b => b.onclick = () => choose(b.dataset.p, b.dataset.kind, +b.dataset.k)); const a = $('#aud'); if (a) a.onclick = () => audition(); const f = $('#force'); if (f) f.onclick = castIt; return; }
      if (ph === 'film' || ph === 'wrap') return H.side(`<div class="ph">Our scene <small>${esc(book())}</small></div><div class="ledger" style="font-size:13px">${G.cast.map(c => `<div>“${esc(c.text)}” <span style="color:#7a6a58">— voice ${AB[c.v]} (${esc(c.voice.label)}) · picture ${c.p + 1}</span></div>`).join('')}</div>${rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}<b>${p.score}</b></div>`).join('')}${G.awards ? H.awardsHTML(G.awards) : ''}`, ph);
    }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, i: G.i + 1, n: G.lines.length };
      const L = G.lines[G.i];
      if ((G.phase === 'cast' || G.phase === 'cast-done') && L) { s.text = L.text; s.who = L.who; s.vs = L.vs.map(v => ({ label: v.label, words: v.fr.map(f => f[3]).join(' ').slice(0, 90), n: v.fr.length })); s.ps = picsFor(G.i).map(x => thumb(x.v)); s.mine = G.votes[p.id] || {}; s.in = Object.values(G.votes).filter(v => v.v != null && v.p != null).length; s.of = voters().length; }
      if (G.phase === 'cast-done') { s.choice = G.choice; s.gain = (G.gain || {})[p.id] || 0; }
      if (G.phase === 'wrap') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.ofN = r.length; }
      return s; }
    return { stateFor, draw, house: false, onMsg(p, m) { if (m.t === 'cast') choose(p.id, m.kind, m.k); }, crowdTarget: () => G.phase === 'cast-done' || G.phase === 'film' ? G.cast[G.cast.length - 1] : null, performer: () => null, stop() { G.phase = 'over'; hush(); H.VP[0].loop = false; } };
  }
  function phone(S, api) { const P = S.phase, { esc } = api;
    if (P === 'loading') return { key: 'loading', status: 'loading the archive’s voices', tabs: ['me', 'throw'] };
    if (P === 'cast') return { key: 'cast' + S.i, status: 'Line ' + S.i + ' of ' + S.n + ' · ' + S.in + ' of ' + S.of + ' cast', takeover: { key: 'cast' + S.i + JSON.stringify(S.mine), render(el) {
      el.innerHTML = `<div class="problem"><b style="font-size:18px">“${esc(S.text)}”</b>${esc(S.who)}</div>
        <div class="lbl">which voice says it best?</div><div class="answers compact">${S.vs.map((v, k) => `<button class="btn ${S.mine.v === k ? 'on' : ''}" data-kind="v" data-k="${k}"><span class="k">${AB[k]}</span>${esc(v.label)}${v.n > 1 ? ' · ' + v.n + ' voices' : ''}<br><small style="color:#6d6052">${esc(v.words)}</small></button>`).join('')}</div>
        <div class="lbl">which picture goes under it?</div><div class="tiles">${S.ps.map((t, k) => `<button class="tile ${S.mine.p === k ? 'on' : ''}" data-kind="p" data-k="${k}"><img alt="" src="${esc(t)}"><span>${k + 1}</span></button>`).join('')}</div>`;
      el.querySelectorAll('[data-kind]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'cast', kind: b.dataset.kind, k: +b.dataset.k }); }); } } };
    if (P === 'cast-done') return { key: 'done' + S.i, status: 'Cast: voice ' + AB[S.choice.v] + ' and picture ' + (S.choice.p + 1) + (S.gain ? ' · you +' + S.gain : ' · the room went another way'), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'Our scene is playing', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.ofN}</div><div class="sub">${S.you.score} choices shared with the room</div></div>`; } } };
    return null; }
  Party.games.odyssey = { title: 'The Found Odyssey', blurb: 'Homer spoken by the archive: for each line, every phone casts a voice and a picture; the chorus decides', options: [{ k: 'lines', name: 'lines', values: [4, 6, 8], def: 6 }], host, phone };
})();
