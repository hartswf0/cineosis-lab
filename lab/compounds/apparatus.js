/* THE APPARATUS — narrative analytical, physical, computational and test chemistry for WYGWYL.
 *
 * One current compound (a poem and a film of it), many projections. The films: the poem as written (its beats'
 * signs), its natural compound (the Compound Bench's measured molecule), the four cuts, the nine bets, the Narrative
 * Lab, and whatever the synthetic probe presses. Theory comes from chemistry/chem-data.json (valence, regime, image
 * type, confusable flips); observation from the films. Bonds between consecutive shots use the Bench's own rules:
 *   = held (same sign) · ≡ rhyme (same image type) · ⇌ resonance (a confusable flip) · → break (movement into time)
 *   ← regression (time back into movement: not a bond the Bench can make) · − a plain cut
 */
(() => {
'use strict';
const $ = s => document.querySelector(s);
const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
const FAM = ['perception', 'affect', 'action', 'reflection', 'mental', 'break', 'time', 'read'];
const FAMN = { perception: 'Perception', affect: 'Affect', action: 'Action', reflection: 'Reflection', mental: 'Mental', break: 'Opsign · Sonsign', time: 'Time', read: 'Lectosign' };
const BOND = { '=': 'held', '#': 'rhyme', '~': 'resonance', '>': 'break', '<': 'regression', '-': 'cut' };
const BSYM = { '=': '═', '#': '≡', '~': '⇌', '>': '→', '<': '←', '-': '−' };
const BKEYS = ['=', '#', '~', '>', '<', '-'];
const CUTS = [['suite', 'Suite cut'], ['scenes', 'Scenes cut'], ['cineosis', 'Cineosis cut'], ['drift', 'Drift cut']];
const BETS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'];
let D, T, CM = new Map(), SIGNS = [];
const S = { film: '01', src: 'suite', bench: [[]], benchCat: new Set(), press: null, pressFrom: null, pressed: null };
const col = dom => `var(--${dom || 'break'})`;
const fam = n => D.signs[n]?.dom;
const reg = n => T[n]?.regime || 'movement';
const sym = n => D.signs[n]?.symbol || '?';
const atom = (n, k, cls = '') => { const g = D.signs[n]; return g ? `<span class="at ${cls}" style="--c:${col(g.dom)}" title="${esc(n)} · ${esc(g.name)} · ${esc(FAMN[g.dom] || g.dom)} · valence ${T[n]?.valence ?? '?'} · ${esc(reg(n))}-image">${esc(g.symbol)}${k > 1 ? `<sub>${k}</sub>` : ''}</span>` : ''; };
const url = u => !u ? '' : /^https?:|^\/|^\./.test(u) ? u : D.cdn + u;
const pct = x => Math.round(100 * x) + '%';
const filmOf = n => D.films.find(f => f.n === n);
const win = f => { const ls = D.lines.filter(l => l.film === f.n); return [ls.length ? ls[0].t0 : f.t0, ls.length ? ls.at(-1).t1 : f.t1]; };
const lineAt = t => D.lines.find(l => t >= l.t0 && t < l.t1) || D.lines.find(l => l.t0 >= t);
const nlink = t => { const l = lineAt(t); return l ? `narrative.html?line=${encodeURIComponent(l.id)}` : 'narrative.html'; };

/* ---------- bonds, by the Bench's rules ---------- */
function bond(a, b) {
  if (!a || !b) return '-';
  if (a === b) return '=';
  const A = T[a], B = T[b]; if (!A || !B) return '-';
  if (A.col === B.col) return '#';
  if (A.flips.includes(b) || B.flips.includes(a)) return '~';
  if (A.regime === 'movement' && B.regime === 'time') return '>';
  if (A.regime === 'time' && B.regime === 'movement') return '<';
  return '-';
}

/* ---------- films of a poem ---------- */
function shotsOf(key, f) {
  const [a, b] = [f.t0, f.t1], clip = x => ({ ...x, t0: Math.max(a, x.t0), t1: Math.min(b, x.t1) });
  if (key === 'written') return D.beats.filter(x => x.film === f.n && x.codes.length).map(x => ({ t0: x.t0, t1: x.t1, sg: x.codes[0], sg2: x.codes[1], id: 'beat' + x.id, title: x.title }));
  if (key === 'natural') { const at = D.natural[f.n] || [], [p0, p1] = win(f), d = (p1 - p0) / Math.max(1, at.length); return at.map((n, i) => ({ t0: p0 + i * d, t1: p0 + (i + 1) * d, sg: n, id: 'nat' + i, title: 'natural compound' })); }
  if (key === 'pressed') return S.pressed ? S.pressed.filter(x => x.sg) : [];
  const cut = CUTS.find(c => c[0] === key);
  if (cut) return D.cuts[key].filter(x => x[1] > a && x[0] < b).map(x => clip({ t0: x[0], t1: x[1], id: x[2], sg: x[3], sg2: x[5], thumb: url(x[4]), title: x[6] }));
  let seats;
  if (key === 'HOUSE') { const hs = store.get('cineosis.house.v1', {}), c = hs[f.n]; seats = c ? store.get(`cineosis.film.${c}.v1`, []) : []; }
  else seats = store.get(`cineosis.film.${key}.v1`, []);
  return seats.filter(s => s.t1 > a && s.t0 < b).map(s => { const c = CM.get(s.clip.id); return clip({ t0: s.t0, t1: s.t1, id: s.clip.id, sg: s.clip.sg || c?.[1], sg2: c?.[2], thumb: s.clip.thumb, title: s.clip.title }); }).filter(x => x.sg);
}
function sources(f) {
  const out = [['written', 'as written'], ['natural', 'natural compound'], ...CUTS];
  BETS.concat(['NL', 'HOUSE']).forEach(c => { if (shotsOf(c, f).length) out.push([c, c === 'NL' ? 'Narrative Lab' : c === 'HOUSE' ? 'house cut' : c]); });
  if (S.pressed) out.push(['pressed', 'pressed']);
  return out;
}

/* ---------- the spectrometer ---------- */
function spectrum(shots) {
  const sec = {}, fs = {}, bonds = Object.fromEntries(BKEYS.map(k => [k, 0])); let tot = 0, time = 0;
  shots.forEach((x, i) => {
    const d = Math.max(0, x.t1 - x.t0); tot += d; sec[x.sg] = (sec[x.sg] || 0) + d; fs[fam(x.sg)] = (fs[fam(x.sg)] || 0) + d; if (reg(x.sg) === 'time') time += d;
    const nx = shots[i + 1]; if (nx && nx.id !== x.id) bonds[bond(x.sg, nx.sg)]++;
  });
  const nb = Object.values(bonds).reduce((a, x) => a + x, 0);
  return { sec, fs, bonds, tot, pT: tot ? 14 * time / tot : 0, sat: nb ? 1 - bonds['-'] / nb : 0, nb, n: shots.length };
}
function fingerprint(sp) {
  const v = [], nz = (arr) => { const s = arr.reduce((a, x) => a + x, 0) || 1; return arr.map(x => x / s); };
  v.push(...nz(SIGNS.map(n => sp.sec[n] || 0)));
  v.push(...nz(FAM.map(f => sp.fs[f] || 0)).map(x => x * 1.2));
  v.push(...nz(BKEYS.map(k => sp.bonds[k] || 0)).map(x => x * .8));
  return v;
}
const cos = (a, b) => { let d = 0, x = 0, y = 0; for (let i = 0; i < a.length; i++) { d += a[i] * b[i]; x += a[i] * a[i]; y += b[i] * b[i]; } return x && y ? d / Math.sqrt(x * y) : 0; };
function ptCurve(shots, a, b, step = 1, half = 8) {
  const pts = [];
  for (let t = a; t <= b; t += step) { let tot = 0, time = 0; shots.forEach(x => { const o = Math.min(t + half, x.t1) - Math.max(t - half, x.t0); if (o > 0) { tot += o; if (reg(x.sg) === 'time') time += o; } }); pts.push([t, tot ? 14 * time / tot : null]); }
  return pts;
}
const formula = sec => Object.entries(sec).sort((a, b) => FAM.indexOf(fam(a[0])) - FAM.indexOf(fam(b[0])) || b[1] - a[1]).map(([n, s]) => atom(n, 0) + `<span class="op" style="padding:0 4px 0 1px;font-size:10px">${Math.round(s)}s</span>`).join('');
const bars = (rows, max) => rows.map(([lab, v, c, tail]) => `<span>${lab}</span><span class="b"><i style="width:${max ? 100 * v / max : 0}%;--c:${c}"></i></span><span>${tail ?? ''}</span>`).join('');

/* ---------- the system, written ---------- */
function writeSystem() {
  $('#system').innerHTML = `<div class="card">
    <h3>Two chemistries <small>kept apart, joined by a loop</small></h3>
    <table><thead><tr><th></th><th>analytical · this page</th><th>synthetic · <a href="chemistry.html">the Bench</a></th></tr></thead><tbody>
      <tr><td>basis</td><td>observed WYGWYL footage</td><td>Deamer-derived rules</td></tr>
      <tr><td>question</td><td>what chemistry does this film exhibit?</td><td>what chemistry is lawful, generative?</td></tr>
      <tr><td>capacity</td><td><b>coordination</b>: partners a sign actually keeps</td><td><b>valence</b>: partners a sign can hold</td></tr>
      <tr><td>bonds</td><td>relations found between shots</td><td>editing operations</td></tr>
      <tr><td>direction</td><td>film → notation</td><td>notation → film</td></tr>
      <tr><td>instrument</td><td>spectrometer, chromatogram, fragments</td><td>bench, reactions, press</td></tr></tbody></table>
    <p style="margin-top:12px">The loop that makes it a science rather than a decoration: measure a film, write its chemistry, press that chemistry back into the archive, measure the new film, and ask what survived.</p>
    <div class="loop">film A ──spectrometer──▶ chemistry A ──press──▶ film B ──spectrometer──▶ chemistry B
   ▲                                                                    │
   └──────────── how much of A survives the round trip? ◀───────────────┘</div>
    <p class="rq">Can a formal chemistry of cinematic signs move reversibly between film and notation, expose structures not apparent in either alone, and generate viable films whose organisation was not hand-authored?</p>
  </div>
  <div class="card"><h3>Terms <small>each one an instrument below</small></h3><dl>
    <dt>valence</dt><dd>theory: how many relations a sign can sustain (composition 2, genesis 3, opsign or sonsign 1, lectosign 4).</dd>
    <dt>coordination</dt><dd>observation: how many partners it actually keeps in WYGWYL. <b>coordination − valence</b> is an anomaly worth inspecting, not an error.</dd>
    <dt>pT(t)</dt><dd>time pressure as a trajectory, not a score: 0 pure movement-image, 14 pure time-image. Where it crosses 7 is a phase transition.</dd>
    <dt>catalyst · dopant</dt><dd>a dopant is a foreign sign that stays and changes the compound; a catalyst makes a transition possible and does not remain (a sound event that lets movement break into time).</dd>
    <dt>isomers</dt><dd>same inventory, other order. <b>Enantiomer</b>: the mirror; film is directional, so a compound can be <b>chiral</b>. <b>Stereoisomer</b>: same connectivity, other orientation (voice IN or OUT). <b>Conformer</b>: same structure, other realisation (timing, takes).</dd>
    <dt>vacancy</dt><dd>a hole in chemical space: the compound asks for a sign combination no shot carries. It specifies the footage that ought to exist.</dd>
    <dt>fragments</dt><dd>break a finished film at family and regime changes; recurring fragments are molecules nobody defined.</dd>
  </dl></div>`;
}

/* ---------- the current compound ---------- */
function drawTabs() {
  $('#tabs').innerHTML = D.films.map(f => `<button data-n="${esc(f.n)}" class="${f.n === S.film ? 'on' : ''}" title="${esc(f.title)}">${esc(f.n)} <small>${esc(f.title.toLowerCase())}</small></button>`).join('');
  $('#tabs').querySelectorAll('button').forEach(b => b.onclick = () => { S.film = b.dataset.n; S.press = null; S.pressed = null; if (S.src === 'pressed') S.src = 'suite'; drawAll(); });
  const f = filmOf(S.film), src = sources(f);
  if (!src.some(s => s[0] === S.src)) S.src = 'suite';
  $('#srcs').innerHTML = `<span class="lbl">film</span>` + src.map(([k, n]) => `<button data-k="${esc(k)}" class="${k === S.src ? 'on' : ''}">${esc(n)}</button>`).join('');
  $('#srcs').querySelectorAll('button').forEach(b => b.onclick = () => { S.src = b.dataset.k; drawAll(false); });
}

/* ---------- 1 analytical ---------- */
function drawSpectrum() {
  const f = filmOf(S.film), sh = shotsOf(S.src, f), sp = spectrum(sh);
  const signRows = Object.entries(sp.sec).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([n, s]) => [atom(n), s, col(fam(n)), Math.round(s) + 's']);
  const famRows = FAM.filter(x => sp.fs[x]).map(x => [esc(FAMN[x]), sp.fs[x], col(x), pct(sp.fs[x] / sp.tot)]);
  const bondRows = BKEYS.map(k => [`<span class="bondsym">${BSYM[k]}</span>${BOND[k]}`, sp.bonds[k], k === '<' ? 'var(--hi)' : 'var(--ink)', sp.bonds[k]]);
  $('#spectrum').innerHTML = `<h3>Spectrum <small>${esc(sources(f).find(s => s[0] === S.src)?.[1] || S.src)} · ${sp.n} shots · ${Math.round(sp.tot)} s</small></h3>
    <p class="q">A film’s fingerprint: how long each sign holds the screen, which families carry it, how its cuts bond.</p>
    <div class="row" style="gap:28px;margin-bottom:10px"><span class="big">${sp.pT.toFixed(1)}<small> pT</small></span><span class="big">${pct(sp.sat)}<small> bonded</small></span><span class="big">${Object.keys(sp.sec).length}<small> elements</small></span></div>
    <div class="spec3"><div><h4>signs</h4><div class="bars">${bars(signRows, Math.max(...signRows.map(r => r[1]), 1))}</div></div>
      <div><h4>families</h4><div class="bars">${bars(famRows, Math.max(...famRows.map(r => r[1]), 1))}</div></div>
      <div><h4>bonds</h4><div class="bars">${bars(bondRows, Math.max(...bondRows.map(r => r[1]), 1))}</div></div></div>
    <h4 style="margin-top:10px">formula</h4><div class="formula">${formula(sp.sec) || '<span class="empty">no shots</span>'}</div>`;
}
function drawFingerprint() {
  const f = filmOf(S.film), src = sources(f), fps = src.map(([k]) => { const sh = shotsOf(k, f); return { k, fp: fingerprint(spectrum(sh)), ids: new Set(sh.map(x => x.id)) }; });
  const short = k => ({ written: 'written', natural: 'natural', suite: 'suite', scenes: 'scenes', cineosis: 'cineo', drift: 'drift', HOUSE: 'house', NL: 'NL', pressed: 'pressed' }[k] || k);
  let best = null;
  const cells = fps.map((a, i) => fps.map((b, j) => {
    const c = cos(a.fp, b.fp), inter = [...a.ids].filter(x => b.ids.has(x)).length, jac = (a.ids.size + b.ids.size - inter) ? inter / (a.ids.size + b.ids.size - inter) : 0;
    if (i < j && a.k !== 'written' && b.k !== 'written' && a.k !== 'natural' && b.k !== 'natural' && (!best || c - jac > best.d)) best = { a: a.k, b: b.k, c, jac, d: c - jac };
    return { c, jac, me: a.k === S.src || b.k === S.src };
  }));
  $('#fingerprint').innerHTML = `<h3>Fingerprints <small>chemistry vs footage</small></h3>
    <p class="q">Upper triangle: chemical similarity of two films (cosine of their spectra). Lower: how much footage they share. Same chemistry with different footage is the interesting case.</p>
    <div class="scroll"><table class="mat"><tr><th></th>${fps.map(x => `<th>${esc(short(x.k))}</th>`).join('')}</tr>
    ${fps.map((a, i) => `<tr><th>${esc(short(a.k))}</th>${fps.map((b, j) => { const x = cells[i][j]; const v = i === j ? '' : i < j ? x.c : x.jac; const bg = i === j ? 'var(--rule)' : i < j ? `color-mix(in srgb, var(--hi) ${Math.round(v * 80)}%, transparent)` : `color-mix(in srgb, var(--ink) ${Math.round(v * 60)}%, transparent)`; return `<td class="${x.me && i !== j ? 'me' : ''}" style="background:${bg}">${i === j ? '' : Math.round(v * 100)}</td>`; }).join('')}</tr>`).join('')}</table></div>
    ${best ? `<p class="meter" style="margin-top:8px"><b>${esc(short(best.a))}</b> and <b>${esc(short(best.b))}</b>: ${pct(best.c)} the same chemistry, ${pct(best.jac)} the same footage.</p>` : ''}`;
}
function drawChroma() {
  const f = filmOf(S.film), [a, b] = [f.t0, f.t1], sh = shotsOf(S.src, f), W = 1000, X = t => 90 + (W - 100) * (t - a) / (b - a);
  const order = []; sh.forEach(x => { if (!order.includes(x.sg)) order.push(x.sg); });
  const rows = order.slice(0, 16), rh = 13, top = 6, h1 = top + rows.length * rh, famY = h1 + 8, pY = famY + 22, pH = 90, H = pY + pH + 22;
  const cur = ptCurve(sh, a, b), P = v => pY + pH - pH * v / 14;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="chromatogram">`;
  D.lines.filter(l => l.film === f.n).forEach(l => s += `<line x1="${X(l.t0)}" x2="${X(l.t0)}" y1="${top}" y2="${pY + pH}" class="dim" stroke-width=".5"/>`);
  rows.forEach((n, i) => { const y = top + i * rh; s += `<text x="84" y="${y + 10}" text-anchor="end" font-size="10">${esc(sym(n))}</text>`;
    sh.filter(x => x.sg === n).forEach(x => s += `<rect x="${X(x.t0)}" y="${y + 1}" width="${Math.max(1.5, X(x.t1) - X(x.t0))}" height="${rh - 3}" fill="var(--${fam(n)})" stroke="#1d1b18" stroke-width=".4"><title>${esc(sym(n))} ${esc(D.signs[n]?.name)} · ${esc(x.title || '')} · ${x.t0.toFixed(1)}–${x.t1.toFixed(1)}s</title></rect>`); });
  s += `<text x="84" y="${famY + 11}" text-anchor="end" font-size="10">regime</text>`;
  sh.forEach(x => s += `<rect x="${X(x.t0)}" y="${famY}" width="${Math.max(1, X(x.t1) - X(x.t0))}" height="14" fill="${reg(x.sg) === 'time' ? 'var(--time)' : 'var(--action)'}" opacity=".85"/>`);
  s += `<text x="84" y="${pY + 10}" text-anchor="end" font-size="10">pT(t)</text><line x1="90" x2="${W - 10}" y1="${P(7)}" y2="${P(7)}" class="ink" stroke-dasharray="3 4" stroke-width=".7"/><text x="${W - 10}" y="${P(7) - 3}" text-anchor="end" font-size="9">7</text>`;
  const pts = cur.filter(p => p[1] != null).map(p => `${X(p[0]).toFixed(1)},${P(p[1]).toFixed(1)}`).join(' ');
  if (pts) s += `<polyline points="${pts}" fill="none" stroke="var(--hi)" stroke-width="1.8"/>`;
  const trans = []; for (let i = 1; i < cur.length; i++) { const p = cur[i - 1][1], q = cur[i][1]; if (p != null && q != null && (p < 7) !== (q < 7)) trans.push([cur[i][0], q >= 7 ? 'into time' : 'back to movement']); }
  trans.forEach(([t, k]) => s += `<line x1="${X(t)}" x2="${X(t)}" y1="${pY}" y2="${pY + pH}" stroke="var(--hi)" stroke-width="1"/><text x="${X(t) + 3}" y="${pY + 10}" font-size="9" fill="var(--hi)">${k}</text>`);
  s += `<text x="90" y="${H - 4}" font-size="9">${Math.round(a)}s</text><text x="${W - 10}" y="${H - 4}" text-anchor="end" font-size="9">${Math.round(b)}s</text></svg>`;
  $('#chroma').innerHTML = `<h3>Chromatogram <small>every sign’s arrival in time · pT as a trajectory</small></h3><p class="q">A spectrum forgets chronology; this keeps it. Each row is a sign in the order it first arrives. The regime band shows movement (orange) and time (violet); the curve is time pressure in a 16-second window, and red lines mark where it crosses 7.</p>${sh.length ? s : '<p class="empty">This film has no shots in this poem yet.</p>'}
    <p class="meter">${trans.length ? `${trans.length} phase transition${trans.length > 1 ? 's' : ''}: ${trans.map(([t, k]) => `${k} at ${Math.round(t)}s`).join(' · ')}` : 'no phase transition: the film stays in one regime'}</p>`;
}

/* fragmentation: break a film at family and regime changes; recurring fragments are discovered molecules */
let SPECIES = null;
function mineSpecies() {
  const grams = new Map();
  D.films.forEach(f => CUTS.forEach(([k]) => {
    const seq = []; shotsOf(k, f).forEach(x => { if (seq.at(-1) !== x.sg) seq.push(x.sg); });
    for (let n = 2; n <= 4; n++) for (let i = 0; i + n <= seq.length; i++) { const g = seq.slice(i, i + n); if (new Set(g).size < 2) continue; const key = g.join('|'); let e = grams.get(key); if (!e) grams.set(key, e = { g, count: 0, poems: new Set(), cuts: new Set() }); e.count++; e.poems.add(f.n); e.cuts.add(k); }
  }));
  SPECIES = [...grams.values()].filter(e => e.count >= 3 && e.poems.size >= 2).sort((a, b) => b.g.length * b.count - a.g.length * a.count);
  return SPECIES;
}
function drawFragments() {
  const f = filmOf(S.film), sh = shotsOf(S.src, f), frags = [];
  let cur = null;
  sh.forEach((x, i) => { const p = sh[i - 1], brk = !p || reg(p.sg) !== reg(x.sg); if (brk) { cur = { t0: x.t0, seq: [] }; frags.push(cur); } if (cur.seq.at(-1) !== x.sg) cur.seq.push(x.sg); cur.t1 = x.t1; });
  const known = new Set((SPECIES || mineSpecies()).map(e => e.g.join('|')));
  const hasKnown = seq => { for (let n = Math.min(4, seq.length); n >= 2; n--) for (let i = 0; i + n <= seq.length; i++) if (known.has(seq.slice(i, i + n).join('|'))) return seq.slice(i, i + n); return null; };
  $('#fragments').innerHTML = `<h3>Fragmentation <small>mass spectrometry of the current film</small></h3><p class="q">The film broken wherever it crosses between movement-image and time-image. Fragments that match a species found across the corpus are outlined; the rest are this film’s own.</p>
    ${frags.length ? `<div class="frags">${frags.map(fr => { const k = hasKnown(fr.seq); return `<a class="frag${k ? ' known' : ''}" href="${nlink(fr.t0)}" title="open this moment in the Narrative Lab" style="text-decoration:none"><span class="formula">${fr.seq.map((n, i) => (i ? `<span class="bondsym">${BSYM[bond(fr.seq[i - 1], n)]}</span>` : '') + atom(n)).join('')}</span><span class="k">${Math.round(fr.t0)}–${Math.round(fr.t1)}s${k ? ' · species ' + k.map(sym).join('') : ''}</span></a>`; }).join('')}</div>` : '<p class="empty">No shots to break.</p>'}`;
}

/* ---------- 2 physical ---------- */
function drawPhase() {
  const W = 560, H = 360, L0 = 46, B0 = 36, X = v => L0 + (W - L0 - 12) * v / 14, Y = v => H - B0 - (H - B0 - 12) * v, pts = [];
  D.films.forEach(f => sources(f).forEach(([k]) => { if (k === 'pressed' && f.n !== S.film) return; const sp = spectrum(shotsOf(k, f)); if (sp.n) pts.push({ f: f.n, k, x: sp.pT, y: sp.sat }); }));
  const shape = k => k === 'written' ? 'sq' : k === 'natural' ? 'di' : CUTS.some(c => c[0] === k) ? 'ci' : 'tr';
  const mark = (p, r, fill, stroke, sw) => { const x = X(p.x), y = Y(p.y), sh = shape(p.k);
    return sh === 'sq' ? `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>` : sh === 'di' ? `<path d="M${x},${y - r * 1.3} L${x + r * 1.3},${y} L${x},${y + r * 1.3} L${x - r * 1.3},${y}Z" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>` : sh === 'tr' ? `<path d="M${x},${y - r * 1.3} L${x + r * 1.2},${y + r} L${x - r * 1.2},${y + r}Z" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>` : `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`; };
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="phase diagram">`;
  [0, 3.5, 7, 10.5, 14].forEach(v => s += `<line x1="${X(v)}" x2="${X(v)}" y1="12" y2="${H - B0}" class="dim" stroke-width="${v === 7 ? 1 : .5}" ${v === 7 ? 'stroke-dasharray="3 3"' : ''}/><text x="${X(v)}" y="${H - B0 + 14}" text-anchor="middle" font-size="10">${v}</text>`);
  [0, .25, .5, .75, 1].forEach(v => s += `<line x1="${L0}" x2="${W - 12}" y1="${Y(v)}" y2="${Y(v)}" class="dim" stroke-width=".5"/><text x="${L0 - 6}" y="${Y(v) + 3}" text-anchor="end" font-size="10">${Math.round(v * 100)}</text>`);
  s += `<text x="${(W + L0) / 2}" y="${H - 4}" text-anchor="middle" font-size="10">pT · time pressure →</text><text x="12" y="${(H - B0) / 2}" font-size="10" transform="rotate(-90 12 ${(H - B0) / 2})" text-anchor="middle">bonded ↑</text>`;
  s += `<text x="${X(1.5)}" y="24" font-size="10" fill="var(--action)">movement</text><text x="${X(12.5)}" y="24" font-size="10" text-anchor="middle" fill="var(--time)">crystal</text>`;
  pts.filter(p => p.f !== S.film).forEach(p => s += mark(p, 3, 'var(--rule)', 'none', 0));
  const mine = pts.filter(p => p.f === S.film), wr = mine.find(p => p.k === 'written');
  mine.forEach(p => { if (wr && p !== wr) s += `<line x1="${X(wr.x)}" y1="${Y(wr.y)}" x2="${X(p.x)}" y2="${Y(p.y)}" stroke="var(--dim)" stroke-width=".7" stroke-dasharray="2 3"/>`; });
  mine.forEach(p => { s += mark(p, p.k === S.src ? 7 : 5, p.k === S.src ? 'var(--hi)' : 'var(--sheet)', 'var(--ink)', 1.2) + `<text x="${X(p.x) + 9}" y="${Y(p.y) + 4}" font-size="10" fill="var(--ink)">${esc(p.k === 'written' ? 'written' : p.k === 'natural' ? 'natural' : p.k)}</text>`; });
  s += '</svg>';
  $('#phase').innerHTML = `<h3>Phase diagram <small>states of cinematic matter</small></h3><p class="q">Every poem in every film, placed by time pressure and by how bonded its cuts are. Grey: the other poems. For ${esc(S.film)}, dotted lines run from the poem as written to each film of it: a reaction is a movement through this space. ■ written · ◆ natural · ● cuts · ▲ bets, lab, pressed.</p>${s}`;
}
let COORD = null;
function coordination() {
  if (COORD) return COORD;
  // a relation counts once it recurs: two signs bonded (adjacent in a cut, or written into one beat) at least three times.
  // Calibrated on the data: with that threshold the median sign's coordination equals its theoretical valence.
  const cnt = {}, occ = {}, add = (a, b) => { if (!a || !b || a === b) return; const k = a < b ? a + '|' + b : b + '|' + a; cnt[k] = (cnt[k] || 0) + 1; };
  D.beats.forEach(b => { b.codes.forEach(n => occ[n] = (occ[n] || 0) + 1); for (let i = 0; i < b.codes.length; i++) for (let j = i + 1; j < b.codes.length; j++) add(b.codes[i], b.codes[j]); });
  D.films.forEach(f => CUTS.forEach(([k]) => { const sh = shotsOf(k, f); sh.forEach((x, i) => { occ[x.sg] = (occ[x.sg] || 0) + 1; if (sh[i + 1]) add(x.sg, sh[i + 1].sg); }); }));
  const part = {}, once = {};
  Object.entries(cnt).forEach(([k, n]) => { const [a, b] = k.split('|'); [[a, b], [b, a]].forEach(([x, y]) => { (once[x] = once[x] || new Set()).add(y); if (n >= 3) (part[x] = part[x] || new Set()).add(y); }); });
  return COORD = { part, occ, once };
}
function drawValence() {
  const { part, occ, once } = coordination();
  const rows = SIGNS.map(n => { const V = T[n]?.valence ?? 2, C = part[n] ? part[n].size : 0; return { n, V, C, c1: once[n] ? once[n].size : 0, r: C - V, o: occ[n] || 0 }; }).sort((a, b) => b.r - a.r);
  const ratios = rows.filter(r => r.o).map(r => r.C / r.V).sort((a, b) => a - b), med = ratios[Math.floor(ratios.length / 2)] || 0;
  const maxC = Math.max(...rows.map(r => Math.max(r.C, r.V)), 1);
  $('#valence').innerHTML = `<h3>Valence ↔ coordination <small>theory’s capacity vs what the footage does</small></h3><p class="q">Valence from the Bench (composition 2, genesis 3, opsign or sonsign 1, lectosign 4). Coordination: distinct partners a sign bonds with <b>at least three times</b> in WYGWYL’s beats and cuts (a relation that recurs, not a contact). Median coordination ÷ valence: <b>${med.toFixed(2)}</b>. The black tick is the valence; the bar the coordination; “once” counts every partner ever touched.</p>
    <div class="scroll" style="max-height:340px;overflow-y:auto"><table class="vt"><thead><tr><th>sign</th><th>period</th><th class="num">V</th><th class="num">C</th><th class="num">once</th><th></th><th class="num">C−V</th><th></th></tr></thead><tbody>
    ${rows.map(r => `<tr><td>${atom(r.n)} ${esc(D.signs[r.n]?.name)}</td><td>${esc(T[r.n]?.period || '')}</td><td class="num">${r.V}</td><td class="num">${r.C}</td><td class="num" style="color:var(--dim)">${r.c1}</td>
      <td><div class="dv" style="--c:${col(fam(r.n))}"><i style="left:0;width:${100 * r.C / maxC}%"></i><b style="left:${100 * r.V / maxC}%"></b></div></td><td class="num">${r.r > 0 ? '+' : ''}${r.r}</td>
      <td>${r.o === 0 ? '<span class="flag a">absent</span>' : r.C >= 3 * r.V ? '<span class="flag x">excess</span>' : r.C < r.V ? '<span class="flag a">under</span>' : '<span class="flag ok">within</span>'}</td></tr>`).join('')}</tbody></table></div>`;
}

/* ---------- 3 theory ↔ data ---------- */
function drawResiduals() {
  const trans = new Map(), ex = [];
  D.films.forEach(f => CUTS.forEach(([k, kn]) => { const sh = shotsOf(k, f); sh.forEach((x, i) => { const y = sh[i + 1]; if (!y || x.sg === y.sg) return; const key = x.sg + '>' + y.sg; let e = trans.get(key); if (!e) trans.set(key, e = { a: x.sg, b: y.sg, n: 0, ex: [] }); e.n++; if (e.ex.length < 3) e.ex.push({ f: f.n, t: y.t0, k: kn }); }); }));
  const conf = [], abs = [];
  SIGNS.forEach(a => (T[a]?.flips || []).forEach(b => { if (a > b && (T[b]?.flips || []).includes(a)) return; const n = (trans.get(a + '>' + b)?.n || 0) + (trans.get(b + '>' + a)?.n || 0); (n ? conf : abs).push({ a, b, n, e: trans.get(a + '>' + b) || trans.get(b + '>' + a) }); }));
  conf.sort((x, y) => y.n - x.n);
  const { part } = coordination(), excess = SIGNS.map(n => ({ n, C: part[n]?.size || 0, V: T[n]?.valence ?? 2 })).filter(r => r.C >= 3 * r.V).sort((a, b) => b.C / b.V - a.C / a.V);
  const regress = [...trans.values()].filter(e => reg(e.a) === 'time' && reg(e.b) === 'movement').sort((a, b) => b.n - a.n);
  const enders = [...trans.values()].filter(e => T[e.a]?.valence === 1).sort((a, b) => b.n - a.n);
  const over = D.beats.filter(b => b.codes.length > 1 && b.codes.some(n => (T[n]?.valence ?? 2) < b.codes.length - 1));
  const exl = e => e.ex.map(x => `<a href="${nlink(x.t)}">${esc(x.f)} · ${Math.round(x.t)}s · ${esc(x.k)}</a>`).join(', ');
  const pair = (a, b, s = '→') => `${atom(a)}<span class="bondsym">${s}</span>${atom(b)}`;
  const nReg = regress.reduce((s, e) => s + e.n, 0), nEnd = enders.reduce((s, e) => s + e.n, 0);
  $('#residuals').innerHTML = `<p class="q">Every consecutive pair of shots in the four cuts, read against the Bench’s theory. The last column is not repaired: it is where WYGWYL argues with Deamer.</p>
    <div class="res4">
      <div style="--c:var(--ok)"><h4>Confirmations · ${conf.length}</h4><p class="d">Confusable flips the theory predicts, and the cuts actually make.</p>${conf.slice(0, 8).map(e => `<div class="it">${pair(e.a, e.b, '⇌')} ×${e.n}${e.e ? '<br>' + exl(e.e) : ''}</div>`).join('') || '<p class="empty">none</p>'}</div>
      <div style="--c:var(--warn)"><h4>Absences · ${abs.length}</h4><p class="d">Transformations the theory makes available that WYGWYL never performs.</p>${abs.slice(0, 10).map(e => `<div class="it">${pair(e.a, e.b, '⇌')} never</div>`).join('')}${abs.length > 10 ? `<p class="meter">and ${abs.length - 10} more</p>` : ''}</div>
      <div style="--c:var(--hi)"><h4>Excesses · ${excess.length}</h4><p class="d">Signs keeping three times as many recurring partners as their valence allows.</p>${excess.slice(0, 8).map(r => `<div class="it">${atom(r.n)} ${esc(D.signs[r.n]?.name)} · C ${r.C} vs V ${r.V}</div>`).join('') || '<p class="empty">none</p>'}</div>
      <div style="--c:var(--ink)"><h4>Forbidden, observed</h4><p class="d">Things the chemistry says should not happen, happening.</p>
        <div class="it"><b>${nReg}</b> regressions: time-image back into movement-image, which the Bench has no bond for.${regress.slice(0, 4).map(e => `<br>${pair(e.a, e.b, '←')} ×${e.n} · ${exl(e)}`).join('')}</div>
        <div class="it"><b>${nEnd}</b> continuations after an opsign or sonsign, which should end a chain (valence 1).${enders.slice(0, 3).map(e => `<br>${pair(e.a, e.b)} ×${e.n} · ${exl(e)}`).join('')}</div>
        <div class="it"><b>${over.length}</b> beats written with more signs than one of them can hold.${over.slice(0, 3).map(b => `<br><a href="${nlink(b.t0)}">beat ${b.id}</a> ${b.codes.map(n => atom(n)).join('')}`).join('')}</div></div>
    </div>`;
}

/* ---------- 4 computational ---------- */
function roundTrip(key, f) {
  const A = shotsOf(key, f); if (!A.length) return null;
  const used = new Set(), B = [];
  let vac = 0, same = 0, famSame = 0;
  A.forEach(x => {
    const m = (x.t0 + x.t1) / 2, be = D.beats.find(b => m >= b.t0 && m < b.t1) || D.beats.find(b => b.t1 > x.t0 && b.t0 < x.t1), pool = be ? D.cand[be.id] || [] : [];
    const c = pool.find(p => p[1] === x.sg && p[0] !== x.id && !used.has(p[0])) || pool.find(p => p[2] === x.sg && p[0] !== x.id && !used.has(p[0]));
    if (!c) { vac++; return; } used.add(c[0]); B.push({ t0: x.t0, t1: x.t1, sg: c[1], id: c[0] }); if (c[1] === x.sg) same++; if (fam(c[1]) === fam(x.sg)) famSame++;
  });
  return { survive: cos(fingerprint(spectrum(A)), fingerprint(spectrum(B))), sign: same / A.length, fam: famSame / A.length, vac: vac / A.length, n: A.length };
}
function drawRoundTrip() {
  const f = filmOf(S.film), cur = roundTrip(S.src, f);
  const cells = D.films.map(g => CUTS.map(([k]) => roundTrip(k, g)));
  const all = cells.flat().filter(Boolean), mean = k => all.length ? all.reduce((s, x) => s + x[k], 0) / all.length : 0;
  $('#roundtrip').innerHTML = `<h3>Round trip <small>film → chemistry → new film → chemistry</small></h3>
    <p class="q">Each cut is read, its sign sequence is pressed back into the archive with none of its own shots, and the new film is read again. What survives is narrative-chemical, not pixels.</p>
    ${cur ? `<p class="meter">current film: <b>${pct(cur.survive)}</b> of its chemistry survives · ${pct(cur.sign)} of shots keep their sign · ${pct(cur.vac)} vacancies</p>` : ''}
    <div class="scroll"><table class="mat"><tr><th>poem</th>${CUTS.map(c => `<th>${esc(c[1].replace(' cut', ''))}</th>`).join('')}</tr>
    ${D.films.map((g, i) => `<tr><th style="text-align:left">${esc(g.n)} ${esc(g.title.slice(0, 16).toLowerCase())}</th>${cells[i].map((c, j) => c ? `<td class="${g.n === S.film && CUTS[j][0] === S.src ? 'me' : ''}" style="background:color-mix(in srgb, var(--ok) ${Math.round(c.survive * 70)}%, transparent)" title="${pct(c.sign)} same sign · ${pct(c.vac)} vacancies">${Math.round(c.survive * 100)}</td>` : '<td>·</td>').join('')}</tr>`).join('')}</table></div>
    <p class="meter" style="margin-top:6px">mean survival <b>${pct(mean('survive'))}</b> · same sign <b>${pct(mean('sign'))}</b> · same family <b>${pct(mean('fam'))}</b> · vacancies <b>${pct(mean('vac'))}</b></p>`;
}
function drawSpecies() {
  const sp = SPECIES || mineSpecies();
  $('#species').innerHTML = `<h3>Discovered species <small>sequential motifs across all 56 cut sequences</small></h3><p class="q">Sign sequences of two to four that recur in at least three places and two poems. Nobody defined these molecules; the footage did. Bonds by the Bench’s rules; a ← means the species contains a regression.</p>
    <div class="sp">${sp.slice(0, 22).map(e => `<span class="formula">${e.g.map((n, i) => (i ? `<span class="bondsym">${BSYM[bond(e.g[i - 1], n)]}</span>` : '') + atom(n)).join('')}</span><span class="n">×${e.count}</span><span class="meter">${e.poems.size} poems · ${[...e.cuts].join(' ')}</span>`).join('') || '<p class="empty">none recur</p>'}</div>`;
}

/* ---------- 5 synthetic probe ---------- */
function seeds() {
  const f = filmOf(S.film), bs = D.beats.filter(b => b.film === f.n), c = {}; bs.forEach(b => b.codes.forEach(n => c[n] = (c[n] || 0) + 1));
  const ranked = Object.entries(c).sort((a, b) => b[1] - a[1]).map(x => x[0]);
  const nat = D.natural[f.n] || ranked.slice(0, 5), present = new Set(Object.keys(c).map(fam));
  const all = {}; D.beats.forEach(b => b.codes.forEach(n => all[n] = (all[n] || 0) + 1));
  const bestOf = pred => Object.entries(all).filter(([n]) => pred(n)).sort((a, b) => b[1] - a[1])[0]?.[0];
  const out = [];
  if (ranked.length >= 2) out.push({ name: 'Fusion', tag: 'covalent', groups: [[ranked[0], ranked[1]]], why: `${D.signs[ranked[0]].name} and ${D.signs[ranked[1]].name} fused into one body, held throughout.` });
  if (ranked.length >= 2) out.push({ name: 'Echo', tag: 'rhyme at distance', groups: [[ranked[0]], [ranked[1]], [ranked[0]]], why: `Open and close on ${D.signs[ranked[0]].name}: the return that makes a poem feel built.` });
  const miss = FAM.filter(x => x !== 'break' && !present.has(x)), dop = miss.length && bestOf(n => fam(n) === miss[0]);
  if (dop) out.push({ name: 'Dopant', tag: 'foreign, and it stays', groups: [[ranked[0]], [dop], [ranked[1] || ranked[0]]], why: `The poem never reaches ${FAMN[miss[0]]}. ${D.signs[dop].name} enters and remains, changing what the compound is.` });
  const mv = ranked.find(n => reg(n) === 'movement'), tm = ranked.find(n => reg(n) === 'time') || bestOf(n => reg(n) === 'time');
  if (mv && tm) out.push({ name: 'Catalyst', tag: 'sound, consumed', groups: [[mv], ['34b'], [tm]], cat: [1], why: `${D.signs[mv].name} cannot jump straight into ${D.signs[tm].name}. A sound event (the sonsign, Deamer p.168) lowers the barrier and is gone: the pressed film holds the picture across it, so the catalyst leaves no atom behind.` });
  if (nat.length >= 3) { const ch = chirality(nat); out.push({ name: 'Enantiomer', tag: `chirality ${pct(ch)}`, groups: nat.slice().reverse().map(n => [n]), why: `The natural compound mirrored. ${ch > .4 ? 'It is strongly chiral: reversed, departure becomes memory and the compound no longer does the same thing.' : ch > 0 ? 'Mildly chiral: its regimes do not read the same both ways.' : 'Achiral: its regimes read the same both ways.'}` }); }
  if (ranked.length && tm) out.push({ name: 'Time crystal', tag: 'held, then broken', groups: [[ranked[0]], [ranked[0], tm], [tm]], why: `${D.signs[ranked[0]].name} held until ${D.signs[tm].name} fuses into it and takes over.` });
  return out;
}
function chirality(seq) { const r = seq.map(n => reg(n) === 'time' ? 1 : 0), fa = seq.map(fam); let d = 0; for (let i = 0; i < seq.length; i++) d += (r[i] !== r[seq.length - 1 - i] ? .6 : 0) + (fa[i] !== fa[seq.length - 1 - i] ? .4 : 0); return d / seq.length; }
function groupsHTML(groups, cat = []) { return groups.map((g, i) => g.map(n => atom(n, 0, cat.includes(i) ? 'cat' : '')).join('')).join('<span class="op">→</span>'); }
function drawSeeds() {
  const sd = seeds();
  $('#seeds').innerHTML = `<h3>Seeds <small>new compounds from ${esc(S.film)}’s own formula</small></h3><div class="seeds">${sd.map((x, i) => `<div class="seed"><span class="nm">${esc(x.name)}<small>${esc(x.tag)}</small></span><button data-s="${i}">press</button><span class="why">${esc(x.why)}</span><span class="formula">${groupsHTML(x.groups, x.cat)}</span></div>`).join('')}</div>`;
  $('#seeds').querySelectorAll('button').forEach(b => b.onclick = () => { const x = sd[+b.dataset.s]; press(x.groups, x.name, x.cat || []); });
}
function drawBench() {
  const { part } = coordination(), cur = S.bench.length - 1;
  $('#bench').innerHTML = `<h3>Element bench <small>atoms with their valence (theory) and coordination (observed)</small></h3>
    <div class="palette">${FAM.map(fm => `<div class="fam"><small>${esc(FAMN[fm])}</small>${SIGNS.filter(n => fam(n) === fm).map(n => atom(n).replace('<span class="at "', `<span class="at" data-a="${esc(n)}" role="button" tabindex="0" title="${esc(D.signs[n].name)} · valence ${T[n]?.valence ?? '?'} · coordination ${part[n]?.size || 0}"`)).join('')}</div>`).join('')}</div>
    <div class="benchline">${S.bench.map((g, i) => `${i ? '<span class="op">→</span>' : ''}<span class="grp${i === cur ? ' cur' : ''}">${g.length ? g.map((n, j) => atom(n, 0, S.benchCat.has(i) ? 'cat' : '').replace('<span class="at', `<span data-rm="${i}:${j}" class="at`)).join('') : '<span class="op">empty</span>'}</span>`).join('')}</div>
    <div class="row"><button id="bThen">then →</button><button id="bCat" title="Mark this step as a catalyst: it makes the next step possible and does not remain">catalyst step</button><button id="bClear">clear</button><button id="bPress">press onto ${esc(S.film)}</button></div>`;
  $('#bench').querySelectorAll('[data-a]').forEach(a => { const add = () => { S.bench[S.bench.length - 1].push(a.dataset.a); drawBench(); }; a.onclick = add; a.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); add(); } }; });
  $('#bench').querySelectorAll('[data-rm]').forEach(a => a.onclick = () => { const [i, j] = a.dataset.rm.split(':').map(Number); S.bench[i].splice(j, 1); if (!S.bench[i].length && S.bench.length > 1) S.bench.splice(i, 1); drawBench(); });
  $('#bThen').onclick = () => { if (S.bench.at(-1).length) S.bench.push([]); drawBench(); };
  $('#bCat').onclick = () => { const i = S.bench.length - 1; S.benchCat.has(i) ? S.benchCat.delete(i) : S.benchCat.add(i); drawBench(); };
  $('#bClear').onclick = () => { S.bench = [[]]; S.benchCat.clear(); drawBench(); };
  $('#bPress').onclick = () => { const g = S.bench.filter(x => x.length); if (g.length) press(g, 'bench', [...S.benchCat]); };
}

/* the press: stretch a compound over the poem's spoken beats; each beat gets the ranked shot that carries its atoms */
function candOf(c) { return { id: c[0], s1: c[1], s2: c[2], fit: c[3], v: c[4], title: c[5], year: c[6], thumb: url(c[7]), video: url(c[8]), aff: c[9] || [] }; }
function press(groups, name, cat = []) {
  const f = filmOf(S.film), bs = D.beats.filter(b => b.film === f.n && D.lines.some(l => l.film === f.n && l.t1 > b.t0 && l.t0 < b.t1)), used = new Set(), rows = [];
  bs.forEach((b, i) => {
    const gi = Math.min(groups.length - 1, Math.floor(i * groups.length / bs.length)), g = groups[gi], want = new Set(g), pool = (D.cand[b.id] || []).map(candOf);
    if (cat.includes(gi)) { rows.push({ beat: b, group: g, gi, cat: true }); return; }
    const score = x => (want.has(x.s1) ? 2 : 0) + (want.has(x.s2) ? 1.5 : 0) + (want.size > 1 && want.has(x.s1) && want.has(x.s2) ? 2 : 0) + x.fit / 100 - (used.has(x.id) ? 5 : 0);
    const ranked = pool.slice().sort((a, x) => score(x) - score(a)), best = ranked[0], carries = !!best && (want.has(best.s1) || want.has(best.s2));
    const second = ranked.find(x => x !== best && (want.has(x.s1) || want.has(x.s2)) && !used.has(x.id));
    if (carries) used.add(best.id);
    rows.push({ beat: b, group: g, gi, shot: carries ? best : null, alt: second || null, pool });
  });
  rows.forEach((r, i) => { if (r.cat) { const p = rows.slice(0, i).reverse().find(x => x.shot); r.shot = p ? p.shot : null; r.held = true; } });   // a catalyst is not a picture: the previous shot holds across it
  S.pressFrom = S.src === 'pressed' ? (S.pressFrom || 'written') : S.src;
  S.press = { name, groups, cat, rows };
  commitPress();
  $('#press').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
}
function commitPress() {
  S.pressed = S.press.rows.filter(r => r.shot && !r.deliberate).map(r => ({ t0: r.beat.t0, t1: r.beat.t1, id: r.shot.id, sg: r.cat ? (r.shot.s1) : (r.group.includes(r.shot.s1) ? r.shot.s1 : r.group.includes(r.shot.s2) ? r.shot.s2 : r.shot.s1), title: r.shot.title, thumb: r.shot.thumb }));
  drawPress(); drawConformers(); drawMicroscope(); drawTabs(); drawPhase();
}
function drawPress() {
  const box = $('#press'), P = S.press;
  if (!P) { box.innerHTML = `<h3>Molecule press</h3><p class="empty">Press a seed or a bench molecule. The pressed film joins the film choices above, so the spectrometer, chromatogram and phase diagram read it: the loop closes.</p>`; return; }
  const real = P.rows.filter(r => !r.cat), ok = real.filter(r => r.shot).length, vac = real.filter(r => !r.shot && !r.deliberate).length, del = real.filter(r => r.deliberate).length;
  box.innerHTML = `<div class="row" style="justify-content:space-between;margin-bottom:8px"><h3 style="margin:0">Pressed · ${esc(P.name)}</h3><span class="formula">${groupsHTML(P.groups, P.cat)}</span>
    <span class="meter"><b>${ok}/${real.length}</b> beats carried · <b>${vac}</b> vacancies${del ? ` · ${del} left on purpose` : ''}${P.cat.length ? ' · catalyst consumed' : ''}</span>
    <span class="row"><button id="pRead">read it</button><button id="pEDL">export EDL</button><button id="pSave">make it the Narrative Lab’s film</button></span></div>
    <div class="press">${P.rows.map((r, i) => { const s = r.shot, sg = s && D.signs[s.s1];
      if (r.cat) return `<div class="pb catb" style="--c:var(--break)"><div class="im">${s ? `<img src="${esc(s.thumb)}" alt="" loading="lazy">` : ''}<span class="vac del" style="background:rgba(0,0,0,.55)">catalyst · ${r.group.map(sym).join('')}<br>sound event, consumed</span></div><div class="meta"><span>beat ${r.beat.id} · held across</span></div></div>`;
      return `<div class="pb${!s && !r.deliberate ? ' miss' : ''}" style="--c:${col(sg?.dom)}"><div class="im">${s ? `<img src="${esc(s.thumb)}" alt="" loading="lazy">` : `<span class="vac${r.deliberate ? ' del' : ''}" data-v="${i}">${r.deliberate ? 'left empty<br>on purpose' : `VACANCY<br>${r.group.map(sym).join(' + ')}<br>inspect`}</span>`}</div>
        <div class="meta"><span>beat ${r.beat.id}</span><span class="atoms">${r.group.map(a => atom(a)).join('')}${s ? `<span class="op">·</span>${s.s1 ? atom(s.s1) : ''}${s.s2 ? atom(s.s2) : ''}` : ''}</span><span class="t" title="${esc(s?.title || '')}">${esc(s ? s.title + (s.year ? ' ' + s.year : '') : r.deliberate ? 'deliberate vacancy' : 'no shot carries it')}</span></div></div>`; }).join('')}</div>`;
  box.querySelectorAll('.vac[data-v]').forEach(v => v.onclick = () => vacancy(+v.dataset.v));
  box.querySelectorAll('.pb .im').forEach((im, i) => { const s = P.rows[i]?.shot; if (!s?.video) return; im.onmouseenter = () => { if (im.querySelector('video')) return; const v = document.createElement('video'); v.src = s.video; v.muted = true; v.loop = true; v.playsInline = true; v.play().catch(() => {}); im.append(v); }; im.onmouseleave = () => im.querySelector('video')?.remove(); });
  $('#pRead').onclick = () => { S.src = 'pressed'; drawAll(false); $('#analytical').scrollIntoView({ behavior: 'smooth' }); };
  $('#pEDL').onclick = () => download(`wygwyl-${S.film}-${P.name.toLowerCase().replace(/\W+/g, '-')}.cineosis-edl.json`, JSON.stringify(edl(), null, 1), 'application/json');
  const sv = $('#pSave'); let armed = false;
  sv.onclick = () => { if (!armed) { armed = true; sv.classList.add('arm'); sv.textContent = 'tap again to replace it'; setTimeout(() => { armed = false; sv.classList.remove('arm'); sv.textContent = 'make it the Narrative Lab’s film'; }, 3000); return; }
    const f = filmOf(S.film), keep = store.get('cineosis.film.NL.v1', []).filter(s => !(s.t1 > f.t0 && s.t0 < f.t1)); store.set('cineosis.film.NL.v1', keep.concat(seats()).sort((a, b) => a.t0 - b.t0)); sv.classList.remove('arm'); sv.textContent = 'saved to the Narrative Lab'; };
}
function seats() { return S.press.rows.filter(r => r.shot).map((r, i) => ({ id: 'c' + Date.now().toString(36) + i, t0: r.beat.t0, t1: r.beat.t1, text: D.lines.filter(l => l.t1 > r.beat.t0 && l.t0 < r.beat.t1).map(l => l.text).join(' / '),
  clip: { id: r.shot.id, title: r.shot.title, year: r.shot.year, thumb: r.shot.thumb, video: r.shot.video, loop: false, sg: r.shot.s1, in: 0, dur: null }, by: 'machine', bet: 'NL', why: `pressed · ${S.press.name} · ${r.group.map(sym).join('·')}${r.cat ? ' · catalyst held' : ''}` })); }
function edl() { return { format: 'cineosis-edl/1', title: 'WYGWYL', bet: 'CHEM', compound: S.press.name, made: new Date().toISOString(), clock: { audio: 'WYGWYL_Suite_Audio.mp3', duration: D.duration, fps: 25 },
  events: S.press.rows.map((r, i) => ({ n: i + 1, rec: [r.beat.t0, r.beat.t1], words: D.lines.filter(l => l.t1 > r.beat.t0 && l.t0 < r.beat.t1).map(l => l.text).join(' / '), clip: r.shot ? { id: r.shot.id, title: r.shot.title, video: r.shot.video, thumb: r.shot.thumb, sg: r.shot.s1 } : null,
    vacancy: r.shot ? null : { requires: r.group, deliberate: !!r.deliberate }, catalyst: r.cat ? { requires: r.group, consumed: true } : null })) }; }
function download(name, text, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }

/* a vacancy, first-class: what it needs, what comes nearest, and what you can do about it */
function vacancy(i) {
  const r = S.press.rows[i], need = r.group, pop = $('#vacancy');
  const near = r.pool.map(c => { let s = 0; need.forEach(n => { const a = c.aff.find(x => x[0] === n); if (a) s += a[1]; }); return { c, s }; }).filter(x => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 8);
  const mx = near[0]?.s || 1;
  pop.innerHTML = `<h3>Vacancy · beat ${r.beat.id}</h3><p class="meter">required: ${need.map(n => atom(n) + ' ' + esc(D.signs[n]?.name)).join(' + ')}</p>
    <p class="q" style="font:14px/1.4 var(--serif);color:var(--dim)">No ranked shot for this beat carries ${need.length > 1 ? 'these signs' : 'this sign'} first or second. The nearest, by the machine’s affinity for what is required:</p>
    ${near.length ? near.map((x, j) => `<div class="alt"><img src="${esc(x.c.thumb)}" alt=""><span>${esc(x.c.title)} ${x.c.year || ''}<br><span class="meter">${(x.s / mx).toFixed(2)} · reads ${x.c.s1 ? atom(x.c.s1) : ''}${x.c.s2 ? atom(x.c.s2) : ''}</span></span><button data-j="${j}">substitute</button></div>`).join('') : '<p class="empty">Nothing in this beat’s pool reads the required signs at all: the world this compound asks for is not in the archive yet.</p>'}
    <div class="row" style="margin-top:10px"><button id="vLeave">leave it empty on purpose</button><button id="vBench">change the compound on the bench</button><a href="${nlink(r.beat.t0)}" target="_blank" rel="noopener" title="Open this moment in the Narrative Lab, where the lab's filters and archive search live">forage in the lab ↗</a><button id="vClose" style="margin-left:auto">close</button></div>`;
  pop.hidden = false;
  pop.querySelectorAll('button[data-j]').forEach(b => b.onclick = () => { r.shot = near[+b.dataset.j].c; r.substituted = true; pop.hidden = true; commitPress(); });
  $('#vLeave').onclick = () => { r.deliberate = true; pop.hidden = true; commitPress(); };
  $('#vBench').onclick = () => { S.bench = S.press.groups.map(g => g.slice()); S.benchCat = new Set(S.press.cat); pop.hidden = true; drawBench(); $('#bench').scrollIntoView({ behavior: 'smooth' }); };
  $('#vClose').onclick = () => { pop.hidden = true; };
}
addEventListener('keydown', e => { if (e.key === 'Escape') $('#vacancy').hidden = true; });

/* conformers: the same compound, realised differently; structure vs performance */
function drawConformers() {
  const box = $('#conformers'), P = S.press;
  if (!P) { box.innerHTML = '<h3>Conformers</h3><p class="empty">Press something first.</p>'; return; }
  const A = S.pressed, B = P.rows.filter(r => r.alt || r.shot).map(r => { const s = r.alt || r.shot; return { t0: r.beat.t0, t1: r.beat.t1, id: s.id, sg: r.group.includes(s.s1) ? s.s1 : r.group.includes(s.s2) ? s.s2 : s.s1 }; });
  const C = []; A.forEach(x => { const p = C.at(-1); if (p && p.sg === x.sg) p.t1 = x.t1; else C.push({ ...x }); });
  const Dd = []; P.rows.forEach(r => { if (!r.shot) return; const m = (r.beat.t0 + r.beat.t1) / 2, s2 = r.alt || r.shot; Dd.push({ t0: r.beat.t0, t1: m, id: r.shot.id, sg: r.shot.s1 }, { t0: m, t1: r.beat.t1, id: s2.id + 'b', sg: s2.s1 }); });
  const base = fingerprint(spectrum(A)), ids = new Set(A.map(x => x.id));
  const rows = [['A · as pressed', A], ['B · other takes', B], ['C · long takes', C], ['D · staccato', Dd]].map(([n, f]) => { const sp = spectrum(f), share = f.filter(x => ids.has(x.id)).length / Math.max(1, f.length); return { n, cuts: f.length, struct: cos(base, fingerprint(sp)), share, pT: sp.pT }; });
  box.innerHTML = `<h3>Conformers <small>one compound, four realisations</small></h3><p class="q">The same compound performed four ways: the pressed takes, the next-best takes, runs of one sign held as long takes, and every beat split into two quick shots. Structure should survive while footage and rhythm change: that separates montage structure from editing performance.</p>
    <table class="vt"><thead><tr><th>conformer</th><th class="num">cuts</th><th class="num">structure kept</th><th class="num">same footage</th><th class="num">pT</th></tr></thead><tbody>${rows.map(r => `<tr><td>${esc(r.n)}</td><td class="num">${r.cuts}</td><td class="num">${pct(r.struct)}</td><td class="num">${pct(r.share)}</td><td class="num">${r.pT.toFixed(1)}</td></tr>`).join('')}</tbody></table>`;
}
/* the reaction microscope: git diff for cinematic structure */
function drawMicroscope() {
  const box = $('#microscope'), P = S.press;
  if (!P) { box.innerHTML = '<h3>Reaction microscope</h3><p class="empty">Press something to see what it changed.</p>'; return; }
  const f = filmOf(S.film), before = shotsOf(S.pressFrom, f), after = S.pressed, sb = spectrum(before), sa = spectrum(after);
  const B = new Set(Object.keys(sb.sec)), A = new Set(Object.keys(sa.sec)), fb = new Set(Object.keys(sb.fs)), fa = new Set(Object.keys(sa.fs));
  const kept = [...A].filter(n => B.has(n)), lost = [...B].filter(n => !A.has(n)), gained = [...A].filter(n => !B.has(n));
  let changed = 0; after.forEach(x => { const m = (x.t0 + x.t1) / 2, y = before.find(z => m >= z.t0 && m < z.t1); if (y && y.sg !== x.sg) changed++; });
  const elig = atoms => D.beats.filter(b => b.film === f.n).reduce((s, b) => s + (D.cand[b.id] || []).filter(c => atoms.has(c[1]) || atoms.has(c[2])).length, 0);
  const pool = new Set(P.groups.flat());
  box.innerHTML = `<h3>Reaction microscope <small>${esc(sources(f).find(s => s[0] === S.pressFrom)?.[1] || S.pressFrom)} → pressed</small></h3>
    <dl class="diff"><dt>preserved</dt><dd class="formula">${kept.map(n => atom(n)).join('') || '—'}</dd>
      <dt>lost</dt><dd class="formula">${lost.map(n => atom(n)).join('') || '—'}</dd>
      <dt>gained</dt><dd class="formula">${gained.map(n => atom(n)).join('') || '—'}</dd>
      <dt>families</dt><dd>${[...fa].filter(x => !fb.has(x)).map(x => '+' + FAMN[x]).concat([...fb].filter(x => !fa.has(x)).map(x => '−' + FAMN[x])).join(' · ') || 'unchanged'}</dd>
      <dt>changed</dt><dd>${changed} of ${after.length} shots read a different sign than before at that moment</dd>
      <dt>pT</dt><dd>${sb.pT.toFixed(1)} → ${sa.pT.toFixed(1)} (${sa.pT - sb.pT >= 0 ? '+' : ''}${(sa.pT - sb.pT).toFixed(1)})</dd>
      <dt>bonds</dt><dd>${BKEYS.map(k => `${BSYM[k]} ${sb.bonds[k]}→${sa.bonds[k]}`).join(' · ')}</dd>
      <dt>eligible</dt><dd>${elig(B)} shots in this poem’s pools carry the old signs; ${elig(pool)} carry the compound’s</dd></dl>`;
}

function drawAll(tabs = true) {
  if (tabs !== false) drawTabs(); else drawTabs();
  drawSpectrum(); drawFingerprint(); drawChroma(); drawFragments(); drawPhase(); drawValence(); drawSeeds(); drawBench(); drawPress(); drawConformers(); drawMicroscope();
}
// the data is revalidated on every visit (usually a quick 304) and checked to really be JSON, with two retries:
// a stale cached page, or a load during a deploy, can otherwise get an HTML "not found" page in its place
function loadData(tries = 0) {
  return fetch('compounds/compounds-data.json', { cache: tries ? 'reload' : 'no-cache' }).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status + ' for compounds/compounds-data.json');
    if (/html/i.test(r.headers.get('content-type') || '')) throw new Error('the site sent a page instead of the data (it may be updating)');
    return r.json();
  }).catch(e => tries < 2 ? new Promise(res => setTimeout(res, 1500 * (tries + 1))).then(() => loadData(tries + 1)) : Promise.reject(e));
}
loadData().then(d => {
  D = d; T = d.theory; SIGNS = Object.keys(d.signs);
  Object.values(d.cand).forEach(v => v.forEach(c => CM.set(c[0], c)));
  const q = new URLSearchParams(location.search).get('poem'); if (q && d.films.some(f => f.n === q)) S.film = q;
  writeSystem(); mineSpecies(); drawAll(); drawResiduals(); drawRoundTrip(); drawSpecies();
  $('#tabs').addEventListener('click', () => { drawRoundTrip(); });
}).catch(e => { document.body.insertAdjacentHTML('beforeend', `<p class="empty">Could not load the apparatus data: ${esc(e.message)}. If the site was just updated, <button type="button" onclick="location.reload()">reload the page</button>.</p>`); console.error(e); });
})();
