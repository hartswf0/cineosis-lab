/* THE BREEDING GROUND on the Party platform: Monte Carlo cinema bred by applause. A rule set is a genome of twenty dials
   (acts, shots per act, trust the judge, match cuts, rule of three, chance…; monte/sim.js). Every phone holds a copy of the
   current generation's genome and turns four of its dials; the machine makes a film from each player's rules; the trailers
   play with their breeders named; the room circles its favourite and the fixed critic names its own; the two cross (with a
   little mutation) into the next generation, which everyone inherits. At the end, the film the room bred, in full. */
(function () {
  const { esc, rnd, pick, shuffle, mini } = Party;
  const LEVELS = [['low', .15], ['mid', .5], ['high', .85]];
  function host(H) {
    const $ = s => document.querySelector(s), P = H.P, MC = window.MonteCinema;
    const G = { phase: 'loading', gen: 0, gens: H.opt.gens, base: null, dials: {}, set: {}, sent: {}, films: [], votes: {}, lineage: [], all: [] };
    let M = null, play = null;
    H.houseScore = 0;
    H.slate(H.card(`<div class="big">The Breeding Ground<small>Monte Carlo cinema, bred by applause · loading the archive…</small></div>`, 'sea'));
    Promise.all([Party.monte.load(), fetch('monte/evolution.json').then(r => r.json())]).then(([m, ev]) => { M = m; play = Party.monte.Player(H, M); G.base = (ev.genome || MC.GENES.map(() => .5)).slice(); generation(); });
    const label = k => MC.GENES[k][3], lvl = v => v < .33 ? 'low' : v < .67 ? 'mid' : 'high';
    function generation() {
      G.gen++; G.phase = 'tune'; G.dials = {}; G.set = {}; G.sent = {}; G.films = []; G.votes = {}; H.sign = {}; if (play) play.stop();
      const pool = shuffle(MC.GENES.map((_, k) => k).filter(k => MC.GENES[k][0] !== 'acts'));
      H.players.forEach((p, i) => { G.dials[p.id] = pool.slice((i * 4) % (pool.length - 3), (i * 4) % (pool.length - 3) + 4); G.set[p.id] = {}; });
      H.slate(H.card(`<div class="big">Generation ${G.gen}<small>${G.gen === 1 ? 'the rules the machine evolved overnight' : 'born of ' + esc(G.lineage[G.lineage.length - 1].of)} · turn four dials on your phone</small></div>`, 'sea'));
      draw(); }
    const dialsOf = id => { if (!G.dials[id]) { G.dials[id] = shuffle(MC.GENES.map((_, k) => k)).slice(0, 4); G.set[id] = {}; } return G.dials[id]; };
    const voters = () => H.players.filter(p => p.local || p.conn);
    function setDial(pid, k, v) { if (G.phase !== 'tune' || !dialsOf(pid).includes(k)) return; G.set[pid][k] = Math.max(0, Math.min(1, v)); if (G.sent[pid]) { G.sent[pid] = false; delete H.sign[pid]; if (H._gate) H.ungate(); } draw(); }
    function send(pid) { if (G.phase !== 'tune') return; G.sent[pid] = true; H.sign[pid] = 'bred'; H.act(pid, 'hop', 820);
      if (voters().every(p => G.sent[p.id])) H.gate('Make the films ▸', 'any', make); draw(); }
    function make() {
      G.phase = 'made'; H.sign = {};
      H.players.forEach(p => { if (!G.sent[p.id]) return; const g = G.base.slice(); Object.entries(G.set[p.id]).forEach(([k, v]) => g[k] = v);
        let best = null; for (let s = 0; s < 3; s++) { const f = MC.generate(M, g, Math.floor(rnd() * 1e9)); MC.critic(M, f); if (!best || f.score > best.score) best = f; }
        G.films.push({ by: p.id, g, f: best, r: {}, turned: Object.keys(G.set[p.id]).map(k => label(+k) + ' ' + lvl(G.set[p.id][k])) }); });
      G.films = shuffle(G.films);
      H.slate(H.card(`<div class="big">${G.films.length} films made<small>each from its breeder’s rules · three tries each, the critic kept the best</small></div>`, 'house'));
      H.gate('Screen the trailers ▸', 'any', () => { G.phase = 'screen'; G.k = 0; trailer(); }); draw(); }
    function trailer() { const d = G.films[G.k], p = P(d.by); G.watching = true; H.spot = d.by; H.crowdShow(d); draw();
      H.slate(H.card(`<div class="big">${p ? esc(p.name) + '’s rules' : 'a film'}<small>${d.turned.map(esc).join(' · ') || 'the inherited rules'}</small></div>`, 'sea'));
      setTimeout(() => { if (G.phase !== 'screen' || G.films[G.k] !== d) return; play.play(d.f, { maxSec: 16 }, () => { G.watching = false; H.slate(H.card(`<div class="big">${p ? esc(p.name) + '’s film' : 'that film'}<small>${G.k + 1 < G.films.length ? 'next trailer when you’re ready' : 'that’s all of them'}</small></div>`, 'sea'));
        H.gate(G.k + 1 < G.films.length ? 'Next trailer ▸' : 'Circle one ▸', 'any', () => { if (G.k + 1 < G.films.length) { G.k++; trailer(); } else { G.phase = 'circle'; H.spot = null; H.crowdShow(null); H.slate(H.card(`<div class="big">Circle one<small>not your own · the critic picks its own too</small></div>`, 'night')); draw(); } }); draw(); }); }, 2200); }
    function vote(pid, k) { if (G.phase !== 'circle' || k < 0 || k >= G.films.length || G.films[k].by === pid) return; const first = G.votes[pid] == null; G.votes[pid] = k; H.sign[pid] = 'circled'; if (first) H.act(pid, 'hit', 280);
      if (voters().every(p => G.votes[p.id] != null || G.films.every(f => f.by === p.id))) H.gate('Breed them ▸', 'any', breed); draw(); }
    function breed() {
      const n = G.films.map(() => 0); Object.values(G.votes).forEach(k => n[k]++); const max = Math.max(...n); const tied = n.map((v, k) => v === max ? k : -1).filter(k => k >= 0); const room = pick(tied);
      const critic = G.films.reduce((b, d, k) => d.f.score > G.films[b].f.score ? k : b, 0); G.room = room; G.critic = critic; G.n = n; G.gain = {}; H.sign = {};
      G.films.forEach((d, k) => { const p = P(d.by); if (!p) return; const g = n[k] + (k === room ? 2 : 0) + (k === critic ? 2 : 0); if (g) { p.score += g; G.gain[p.id] = g; } });
      const a = G.films[room].g, b = G.films[critic].g, sigma = .08; G.base = a.map((x, k) => { let y = rnd() < .5 ? x : b[k]; if (rnd() < .3) y += (rnd() + rnd() + rnd() - 1.5) * sigma * 2; return Math.min(1, Math.max(0, y)); });
      const pa = P(G.films[room].by), pb = P(G.films[critic].by), of = room === critic ? (pa ? pa.name + '’s rules, which the room and the critic both chose' : 'one film') : (pa ? pa.name : '?') + '’s rules (the room) × ' + (pb ? pb.name : '?') + '’s rules (the critic)';
      G.lineage.push({ gen: G.gen, of, score: G.films[critic].f.score }); G.all = G.all.concat(G.films); G.phase = 'bred';
      H.slate(H.card(`<div class="big">${room === critic ? 'The room and the critic agree' : 'The room and the critic disagree'}<small>generation ${G.gen + 1} will be born of ${esc(of)}</small></div>`, room === critic ? 'gold' : 'stage'));
      if (pa) H.act(pa.id, 'cheer', 2100); if (pb && pb !== pa) setTimeout(() => H.act(pb.id, 'cheer', 2100), 400);
      H.gate(G.gen < G.gens ? 'Generation ' + (G.gen + 1) + ' ▸' : 'The film we bred ▸', 'any', () => { if (G.gen < G.gens) generation(); else finale(); }); draw(); }
    function finale() { G.phase = 'film'; let best = null; for (let s = 0; s < 4; s++) { const f = MC.generate(M, G.base, Math.floor(rnd() * 1e9)); MC.critic(M, f); if (!best || f.score > best.score) best = f; } G.final = best;
      H.slate(H.card(`<div class="big">The film we bred<small>${G.gens} generations · the critic gives it ${Math.round(best.score * 100)}</small></div>`, 'gold'));
      setTimeout(() => { if (G.phase === 'film') play.play(best, {}, () => wrap()); }, 2400);
      H.gate('Skip ▸', 'any', () => { play.stop(); wrap(); }); draw(); }
    function wrap() { G.phase = 'wrap'; const r = rank(); if (r[0]) { H.act(r[0].id, 'cheer', 2200); H.say(r[0].id, 'good genes', 2200); } G.awards = H.awards(G.all); H.gate('Edit the film ▸', 'any', () => { H.seed = toFilm(); H.playGame('cut'); }); draw(); }
    const toFilm = () => Party.monte.toFilm(M, G.final || G.films[0].f, 'The film we bred');
    const rank = () => H.players.slice().sort((a, b) => b.score - a.score);
    function drawSide() { const ph = G.phase;
      if (ph === 'loading') return H.side(`<div class="ph">The Breeding Ground <small>loading</small></div>`, ph);
      if (ph === 'tune') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Generation ${G.gen} of ${G.gens} <small>${Object.values(G.sent).filter(Boolean).length} of ${voters().length} bred</small></div><div class="hint" style="text-align:left">Everyone inherits the same twenty rules; each phone turns four of them.</div>
          ${locals.map(p => `<div style="margin-top:6px">${mini(p.av)} ${esc(p.name)} ${dialsOf(p.id).map(k => `<div class="vrow"><span style="min-width:130px">${esc(label(k))}</span>${LEVELS.map(([n, v]) => `<button class="btn chip ${G.set[p.id][k] === v ? 'on' : ''}" data-p="${p.id}" data-k="${k}" data-v="${v}">${n}</button>`).join('')}</div>`).join('')}<button class="btn chip" data-send="${p.id}">${G.sent[p.id] ? 'bred ✓' : 'breed'}</button></div>`).join('')}
          ${!H._gate && Object.values(G.sent).some(Boolean) ? `<button class="btn chip" id="force" style="margin-top:8px">make the films now</button>` : ''}`, ph + G.gen);
        S.querySelectorAll('[data-k]').forEach(b => b.onclick = () => setDial(b.dataset.p, +b.dataset.k, +b.dataset.v)); S.querySelectorAll('[data-send]').forEach(b => b.onclick = () => send(b.dataset.send)); const f = $('#force'); if (f) f.onclick = make; return; }
      const rows = (show) => `<div class="takes">${G.films.map((d, k) => `<div class="tk ${show && k === G.room ? 'win' : ''} ${G.phase === 'screen' && k === G.k ? 'now' : ''}"><span class="n">${k + 1}</span><span class="by" style="flex:1;text-align:left">${H.who(d.by)}<br><span class="hint" style="margin:0">${esc(d.turned.join(' · '))}</span>${show ? `<br>critic <b style="color:var(--verm)">${Math.round(d.f.score * 100)}</b>${k === G.critic ? ' · the critic’s pick' : ''} · <span class="vs">${Object.entries(G.votes).filter(([, v]) => v === k).map(([id]) => P(id) ? mini(P(id).av) : '').join('') || '·'}</span>` : ''}${H.crowdText(d) ? `<br><span class="hint" style="margin:0">${esc(H.crowdText(d))}</span>` : ''}</span></div>`).join('')}</div>`;
      if (ph === 'made' || ph === 'screen') return H.side(`<div class="ph">Trailers <small>sixteen seconds each</small></div>${rows(false)}`, ph + (G.k || 0));
      if (ph === 'circle') { const locals = H.players.filter(p => p.local);
        const S = H.side(`<div class="ph">Circle one <small>${Object.keys(G.votes).length} of ${voters().length}</small></div>${rows(false)}${locals.map(p => `<div class="vrow"><span>${mini(p.av)} ${esc(p.name)}</span>${G.films.map((d, k) => `<button class="btn chip ${G.votes[p.id] === k ? 'on' : ''}" data-p="${p.id}" data-k="${k}" ${d.by === p.id ? 'disabled' : ''}>${k + 1}</button>`).join('')}</div>`).join('')}${!H._gate ? `<button class="btn chip" id="force" style="margin-top:8px">breed now</button>` : ''}`, ph);
        S.querySelectorAll('[data-p]').forEach(b => b.onclick = () => vote(b.dataset.p, +b.dataset.k)); const f = $('#force'); if (f) f.onclick = breed; return; }
      if (ph === 'bred') return H.side(`<div class="ph">Generation ${G.gen} <small>circles · picks</small></div>${rows(true)}${lineageHTML()}`, ph + G.gen);
      if (ph === 'film' || ph === 'wrap') return H.side(`<div class="ph">The lineage <small>${G.gens} generations</small></div>${lineageHTML()}${rank().map((p, k) => `<div class="rk">#${k + 1} ${mini(p.av)} ${esc(p.name)}<b>${p.score}</b></div>`).join('')}${G.awards ? H.awardsHTML(G.awards.filter(a => a.id !== 'house')) : ''}`, ph);
    }
    const lineageHTML = () => `<div class="ledger" style="font-size:13px;margin-top:6px">${G.lineage.map(l => `<div><b>GEN ${l.gen + 1}</b> — born of ${esc(l.of)}</div>`).join('') || '<div>generation 1: the machine’s own overnight rules</div>'}</div>`;
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); }
    function stateFor(p) { const s = { phase: G.phase, gen: G.gen, gens: G.gens };
      if (G.phase === 'tune') { s.dials = dialsOf(p.id).map(k => ({ k, name: label(k), base: lvl(G.base[k]), v: G.set[p.id][k] })); s.sent = !!G.sent[p.id]; s.in = Object.values(G.sent).filter(Boolean).length; s.of = voters().length; }
      if (G.phase === 'screen') { const d = G.films[G.k]; s.k = G.k + 1; s.nF = G.films.length; s.whose = (P(d.by) || {}).name; }
      if (G.phase === 'circle') { s.nF = G.films.length; s.own = G.films.findIndex(d => d.by === p.id); s.mine = G.votes[p.id]; s.names = G.films.map(d => (P(d.by) || {}).name || ''); }
      if (G.phase === 'bred') { s.gain = (G.gain || {})[p.id] || 0; s.of = G.lineage[G.lineage.length - 1].of; }
      if (G.phase === 'wrap') { const r = rank(); s.rank = r.findIndex(x => x.id === p.id) + 1; s.ofN = r.length; }
      return s; }
    return { stateFor, draw, house: false, onMsg(p, m) { if (m.t === 'dial') setDial(p.id, m.k, m.v); if (m.t === 'send') send(p.id); if (m.t === 'vote') vote(p.id, m.k); },
      crowdTarget: () => G.phase === 'screen' ? G.films[G.k] : null, performer: () => G.phase === 'screen' && G.films[G.k] ? G.films[G.k].by : null, stop() { G.phase = 'over'; if (play) play.stop(); } };
  }
  function phone(S, api) { const P = S.phase, { esc } = api;
    if (P === 'loading') return { key: 'loading', status: 'loading the archive', tabs: ['me', 'throw'] };
    if (P === 'tune') return { key: 'tune' + S.gen, status: 'Generation ' + S.gen + ' of ' + S.gens + ' · ' + S.in + ' of ' + S.of + ' bred', takeover: { key: 'tune' + S.gen + JSON.stringify(S.dials.map(d => d.v)) + S.sent, render(el) {
      el.innerHTML = `<div class="say" style="text-align:center;font-size:24px;margin:2px 0 6px">Turn four dials</div><div class="sub" style="text-align:center;margin:0 0 8px">everyone starts from the same rules · the machine makes your film from yours</div>
        ${S.dials.map(d => `<div class="lbl">${esc(d.name)} · inherited: ${d.base}</div><div class="tools" style="grid-template-columns:repeat(3,1fr);margin-top:2px">${LEVELS.map(([n, v]) => `<button class="btn ${d.v === v ? 'on' : ''}" data-k="${d.k}" data-v="${v}">${n}</button>`).join('')}</div>`).join('')}
        <button class="btn cta" id="sendB" ${S.sent ? 'disabled' : ''}>${S.sent ? 'bred · change a dial to rebreed' : 'breed my rules ▸'}</button>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'dial', k: +b.dataset.k, v: +b.dataset.v }); });
      el.querySelector('#sendB').onclick = () => { api.buzz(30); api.send({ t: 'send' }); }; } } };
    if (P === 'made') return { key: 'made', status: 'The machine made a film from everyone’s rules', tabs: ['throw', 'me'] };
    if (P === 'screen') return { key: 'screen' + S.k, status: 'Trailer ' + S.k + ' of ' + S.nF + ' · ' + esc(S.whose || '') + '’s rules', tab: 'throw', tabs: ['throw', 'me'] };
    if (P === 'circle') return { key: 'circle', takeover: { key: 'c' + S.mine, render(el) {
      el.innerHTML = `<div class="center"><div class="say">Circle one</div><div class="sub">the rules that should breed · not your own</div><div class="vote">${S.names.map((n, k) => `<button data-k="${k}" class="${S.mine === k ? 'on' : ''}" ${k === S.own ? 'disabled' : ''}><svg viewBox="0 0 100 100"><ellipse cx="50" cy="52" rx="44" ry="38" transform="rotate(-8 50 52)"/></svg>${k + 1}</button>`).join('')}</div><div class="sub">${S.names.map((n, k) => (k + 1) + ': ' + esc(n)).join(' · ')}</div></div>`;
      el.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { api.buzz(); api.send({ t: 'vote', k: +b.dataset.k }); }); } } };
    if (P === 'bred') return { key: 'bred' + S.gen, status: 'Next generation: born of ' + esc(S.of) + (S.gain ? ' · you +' + S.gain : ''), tabs: ['throw', 'me'] };
    if (P === 'film') return { key: 'film', status: 'The film the room bred is playing', tabs: ['throw', 'me'] };
    if (P === 'wrap') return { key: 'wrap', takeover: { key: 'wrap', render(el) { el.innerHTML = `<div class="center">${api.hero(S.you.av, S.rank === 1 ? 'cheer' : 'bow')}<div class="say">#${S.rank} of ${S.ofN}</div><div class="sub">${S.you.score} points</div></div>`; } } };
    return null; }
  Party.games.breed = { title: 'The Breeding Ground', blurb: 'Monte Carlo cinema bred by applause: turn the rules, watch the films, the room and the critic breed the next generation', options: [{ k: 'gens', name: 'generations', values: [2, 3, 4], def: 3 }], host, phone };
})();
