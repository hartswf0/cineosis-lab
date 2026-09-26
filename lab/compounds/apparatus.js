/* THE APPARATUS — WYGWYL's films as chemistry you can see.
 * One current compound (a poem and a film of it); every panel draws it. Theory from chemistry/chem-data.json
 * (valence, regime, image type, confusable flips); observation from the films. Bonds by the Bench's rules:
 *   ─ cut · ═ held (same sign) · ≡ rhyme (same image type) · ⇢ resonance (confusable flip)
 *   ▶ break (movement into time: solid wedge) · ◁ regression (time back into movement: hashed red wedge)
 */
(() => {
'use strict';
const $ = s => document.querySelector(s);
const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
const FAM = ['perception', 'affect', 'action', 'reflection', 'mental', 'break', 'time', 'read'];
const FAMN = { perception: 'perception', affect: 'affect', action: 'action', reflection: 'reflection', mental: 'mental', break: 'op·son', time: 'time', read: 'lecto' };
const BKEYS = ['=', '#', '~', '>', '<', '-'], BSYM = { '=': '═', '#': '≡', '~': '⇢', '>': '▶', '<': '◁', '-': '─' }, BNAME = { '=': 'held', '#': 'rhyme', '~': 'resonance', '>': 'break', '<': 'regression', '-': 'cut' };
const CUTS = [['suite', 'suite'], ['scenes', 'scenes'], ['cineosis', 'cineosis'], ['drift', 'drift']];
const BETS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'];
let D, T, SIGNS = [], CM = new Map(), POOLTH = {};
const S = { film: '01', src: 'suite', bench: [[]], benchCat: new Set(), press: null, pressFrom: null, pressed: null };
const C = dom => getComputedStyle(document.documentElement).getPropertyValue('--' + (dom || 'break')).trim() || '#999';
let COL = {};
const fam = n => D.signs[n]?.dom, reg = n => T[n]?.regime || 'movement', sym = n => D.signs[n]?.symbol || '?', colOf = n => COL[fam(n)] || '#999';
const atom = n => D.signs[n] ? `<span class="at" style="--c:${colOf(n)}" title="${esc(n)} ${esc(D.signs[n].name)} · V${T[n]?.valence ?? '?'} · ${esc(reg(n))}">${esc(sym(n))}</span>` : '';
const url = u => !u ? '' : /^https?:|^\/|^\./.test(u) ? u : D.cdn + u;
const pct = x => Math.round(100 * x) + '%';
const filmOf = n => D.films.find(f => f.n === n);
const win = f => { const ls = D.lines.filter(l => l.film === f.n); return [ls.length ? ls[0].t0 : f.t0, ls.length ? ls.at(-1).t1 : f.t1]; };
const lineAt = t => D.lines.find(l => t >= l.t0 && t < l.t1) || D.lines.find(l => l.t0 >= t);
const nlink = t => { const l = lineAt(t); return l ? `narrative.html?line=${encodeURIComponent(l.id)}` : 'narrative.html'; };
let uid = 0;

/* ---------- bonds ---------- */
function bond(a, b) {
  if (!a || !b) return '-'; if (a === b) return '=';
  const A = T[a], B = T[b]; if (!A || !B) return '-';
  if (A.col === B.col) return '#';
  if (A.flips.includes(b) || B.flips.includes(a)) return '~';
  if (A.regime === 'movement' && B.regime === 'time') return '>';
  if (A.regime === 'time' && B.regime === 'movement') return '<';
  return '-';
}

/* ---------- films ---------- */
function thumbFor(x, f) {
  if (x.thumb) return x.thumb;
  const m = (x.t0 + x.t1) / 2, be = D.beats.find(b => m >= b.t0 && m < b.t1), p = be && (D.cand[be.id] || []).find(c => c[1] === x.sg);
  return p ? url(p[7]) : (POOLTH[x.sg] || '');
}
function shotsOf(key, f) {
  const [a, b] = [f.t0, f.t1], clip = x => ({ ...x, t0: Math.max(a, x.t0), t1: Math.min(b, x.t1) });
  let out;
  if (key === 'written') out = D.beats.filter(x => x.film === f.n && x.codes.length).map(x => ({ t0: x.t0, t1: x.t1, sg: x.codes[0], sg2: x.codes[1], id: 'beat' + x.id }));
  else if (key === 'natural') { const at = D.natural[f.n] || [], [p0, p1] = win(f), d = (p1 - p0) / Math.max(1, at.length); out = at.map((n, i) => ({ t0: p0 + i * d, t1: p0 + (i + 1) * d, sg: n, id: 'nat' + i })); }
  else if (key === 'pressed') out = S.pressed ? S.pressed.filter(x => x.sg) : [];
  else if (CUTS.some(c => c[0] === key)) out = D.cuts[key].filter(x => x[1] > a && x[0] < b).map(x => clip({ t0: x[0], t1: x[1], id: x[2], sg: x[3], sg2: x[5], thumb: url(x[4]), title: x[6] }));
  else {
    let seats; if (key === 'HOUSE') { const hs = store.get('cineosis.house.v1', {}), c = hs[f.n]; seats = c ? store.get(`cineosis.film.${c}.v1`, []) : []; } else seats = store.get(`cineosis.film.${key}.v1`, []);
    out = seats.filter(s => s.t1 > a && s.t0 < b).map(s => { const c = CM.get(s.clip.id); return clip({ t0: s.t0, t1: s.t1, id: s.clip.id, sg: s.clip.sg || c?.[1], sg2: c?.[2], thumb: s.clip.thumb || (c && url(c[7])), title: s.clip.title }); }).filter(x => x.sg);
  }
  out.forEach(x => { if (!x.thumb) x.thumb = thumbFor(x, f); });
  return out;
}
function sources(f) {
  const out = [['written', 'written'], ['natural', 'natural'], ...CUTS];
  BETS.concat(['NL', 'HOUSE']).forEach(c => { if (shotsOf(c, f).length) out.push([c, c === 'NL' ? 'lab' : c === 'HOUSE' ? 'house' : c]); });
  if (S.pressed) out.push(['pressed', 'pressed']);
  return out;
}
function runs(sh) { const r = []; sh.forEach(x => { const p = r.at(-1); if (p && p.sg === x.sg) { p.t1 = x.t1; p.n++; } else r.push({ sg: x.sg, t0: x.t0, t1: x.t1, thumb: x.thumb, n: 1, id: x.id }); }); return r; }

/* ---------- measurement ---------- */
function spectrum(shots) {
  const sec = {}, fs = {}, bonds = Object.fromEntries(BKEYS.map(k => [k, 0])); let tot = 0, time = 0;
  shots.forEach((x, i) => { const d = Math.max(0, x.t1 - x.t0); tot += d; sec[x.sg] = (sec[x.sg] || 0) + d; fs[fam(x.sg)] = (fs[fam(x.sg)] || 0) + d; if (reg(x.sg) === 'time') time += d; const nx = shots[i + 1]; if (nx && nx.id !== x.id) bonds[bond(x.sg, nx.sg)]++; });
  const nb = Object.values(bonds).reduce((a, x) => a + x, 0);
  return { sec, fs, bonds, tot, pT: tot ? 14 * time / tot : 0, sat: nb ? 1 - bonds['-'] / nb : 0, nb, n: shots.length };
}
function fingerprint(sp) { const nz = a => { const s = a.reduce((x, y) => x + y, 0) || 1; return a.map(x => x / s); }; return [...nz(SIGNS.map(n => sp.sec[n] || 0)), ...nz(FAM.map(f => sp.fs[f] || 0)).map(x => x * 1.2), ...nz(BKEYS.map(k => sp.bonds[k] || 0)).map(x => x * .8)]; }
const cos = (a, b) => { let d = 0, x = 0, y = 0; for (let i = 0; i < a.length; i++) { d += a[i] * b[i]; x += a[i] * a[i]; y += b[i] * b[i]; } return x && y ? d / Math.sqrt(x * y) : 0; };
function ptCurve(shots, a, b, step = 1, half = 8) { const pts = []; for (let t = a; t <= b; t += step) { let tot = 0, time = 0; shots.forEach(x => { const o = Math.min(t + half, x.t1) - Math.max(t - half, x.t0); if (o > 0) { tot += o; if (reg(x.sg) === 'time') time += o; } }); pts.push([t, tot ? 14 * time / tot : null]); } return pts; }

/* ---------- drawing: a skeletal formula whose atoms are shots ---------- */
function bondSVG(x1, y1, x2, y2, k, r) {
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
  const ax = x1 + ux * r, ay = y1 + uy * r, bx = x2 - ux * r, by = y2 - uy * r, ln = (o, extra = '') => `<line x1="${ax + nx * o}" y1="${ay + ny * o}" x2="${bx + nx * o}" y2="${by + ny * o}" stroke="#ece6da" stroke-width="1.6" ${extra}/>`;
  if (k === '=') return ln(-3) + ln(3);
  if (k === '#') return ln(-4.5) + ln(0) + ln(4.5);
  if (k === '~') return ln(-2.5) + ln(2.5, 'stroke-dasharray="4 3"');
  if (k === '>') return `<path d="M${ax},${ay} L${bx + nx * 6},${by + ny * 6} L${bx - nx * 6},${by - ny * 6}Z" fill="#ece6da"/>`;
  if (k === '<') { let s = ''; for (let i = 1; i <= 7; i++) { const t = i / 8, w = 6 * t, cx = ax + (bx - ax) * t, cy = ay + (by - ay) * t; s += `<line x1="${cx + nx * w}" y1="${cy + ny * w}" x2="${cx - nx * w}" y2="${cy - ny * w}" stroke="${COL.hi}" stroke-width="1.6"/>`; } return s; }
  return ln(0);
}
function skeletal(nodes, W, o = {}) {
  const n = nodes.length; if (!n) return '<p class="empty">no shots</p>';
  const r = o.r || Math.max(10, Math.min(30, (W - 40) / (n * 2.3))), pad = r + 8, H = o.h || r * 4.4 + 34, mid = H / 2 - 6, amp = n > 1 ? r * 1.05 : 0;
  const X = i => n === 1 ? W / 2 : pad + i * (W - 2 * pad) / (n - 1), Y = i => mid + (i % 2 ? amp : -amp), id = 'k' + (++uid);
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="skeletal formula"><defs>${nodes.map((_, i) => `<clipPath id="${id}c${i}"><circle cx="${X(i)}" cy="${Y(i)}" r="${r - 2}"/></clipPath>`).join('')}</defs>`;
  if (o.echo !== false) { const seen = {}; let arcs = 0; nodes.forEach((x, i) => { const j = seen[x.sg]; if (j != null && i - j > 1 && arcs < 14) { arcs++; const x1 = X(j), x2 = X(i), yy = Math.min(Y(j), Y(i)) - r - 4; s += `<path d="M${x1},${Y(j) - r} Q${(x1 + x2) / 2},${yy - Math.min(40, (x2 - x1) * .25)} ${x2},${Y(i) - r}" fill="none" stroke="${colOf(x.sg)}" stroke-width="1.2" stroke-dasharray="1.5 3"/>`; } seen[x.sg] = i; }); }
  nodes.forEach((x, i) => { if (i) s += bondSVG(X(i - 1), Y(i - 1), X(i), Y(i), o.kinds ? o.kinds[i - 1] : bond(nodes[i - 1].sg, x.sg), r); });
  nodes.forEach((x, i) => {
    const c = colOf(x.sg), tm = reg(x.sg) === 'time';
    s += `<g><title>${esc(sym(x.sg))} ${esc(D.signs[x.sg]?.name)}${x.fused ? ' · ' + esc(D.signs[x.fused]?.name) : ''}${x.n > 1 ? ' · ' + x.n + ' shots' : ''}${x.t0 != null ? ' · ' + Math.round(x.t0) + 's' : ''}</title>`;
    s += x.thumb ? `<circle cx="${X(i)}" cy="${Y(i)}" r="${r}" fill="#000"/><image href="${esc(x.thumb)}" x="${X(i) - r}" y="${Y(i) - r}" width="${2 * r}" height="${2 * r}" preserveAspectRatio="xMidYMid slice" clip-path="url(#${id}c${i})"/>` : `<circle cx="${X(i)}" cy="${Y(i)}" r="${r}" fill="${c}"/>`;
    s += `<circle cx="${X(i)}" cy="${Y(i)}" r="${r}" fill="none" stroke="${c}" stroke-width="${x.cat ? 2 : 3.5}" ${x.cat ? 'stroke-dasharray="3 3"' : ''}/>` + (tm ? `<circle cx="${X(i)}" cy="${Y(i)}" r="${r + 4}" fill="none" stroke="${c}" stroke-width="1"/>` : '');
    if (x.fused) s += `<circle cx="${X(i) + r * .72}" cy="${Y(i) - r * .72}" r="${r * .42}" fill="${colOf(x.fused)}" stroke="#141412" stroke-width="1.5"/><text x="${X(i) + r * .72}" y="${Y(i) - r * .72 + 3}" text-anchor="middle" font-size="${Math.max(7, r * .36)}" font-weight="600" fill="#1d1b18">${esc(sym(x.fused))}</text>`;
    const ly = Y(i) + (i % 2 ? r + 12 : -r - 5);
    s += `<text x="${X(i)}" y="${ly}" text-anchor="middle" font-size="${Math.max(9, Math.min(12, r * .55))}" font-weight="600" fill="${c}">${esc(sym(x.sg))}</text></g>`;
  });
  return s + '</svg>';
}

/* ---------- panels ---------- */
function drawTabs() {
  $('#tabs').innerHTML = D.films.map(f => `<button data-n="${esc(f.n)}" class="${f.n === S.film ? 'on' : ''}" title="${esc(f.title)}">${esc(f.n)} ${esc(f.title.toLowerCase().slice(0, 18))}</button>`).join('');
  $('#tabs').querySelectorAll('button').forEach(b => b.onclick = () => { S.film = b.dataset.n; S.press = null; S.pressed = null; if (S.src === 'pressed') S.src = 'suite'; drawAll(); });
  const f = filmOf(S.film), src = sources(f); if (!src.some(s => s[0] === S.src)) S.src = 'suite';
  $('#srcs').innerHTML = src.map(([k, n]) => `<button data-k="${esc(k)}" class="${k === S.src ? 'on' : ''}">${esc(n)}</button>`).join('');
  $('#srcs').querySelectorAll('button').forEach(b => b.onclick = () => { S.src = b.dataset.k; drawAll(); });
}
function drawSkel() {
  const f = filmOf(S.film), sh = shotsOf(S.src, f), rs = runs(sh), sp = spectrum(sh), W = Math.max(600, $('#skel').clientWidth || 1200);
  const nodes = rs.length > 34 ? rs.filter((_, i) => i % Math.ceil(rs.length / 34) === 0) : rs;
  $('#skel').innerHTML = `<div class="nums"><span class="num">${sp.pT.toFixed(1)}<small>pT</small></span><span class="num">${pct(sp.sat)}<small>bonded</small></span><span class="num">${Object.keys(sp.sec).length}<small>elements</small></span><span class="num">${rs.length}<small>atoms</small></span>
    ${BKEYS.map(k => `<span class="num" style="font-size:16px">${BSYM[k]}${sp.bonds[k]}<small>${BNAME[k]}</small></span>`).join('')}</div>` + skeletal(nodes, W, { h: 150 });
}
function drawTimeline() {
  const f = filmOf(S.film), [a, b] = [f.t0, f.t1], sh = shotsOf(S.src, f), W = 1200, L0 = 34, X = t => L0 + (W - L0 - 6) * (t - a) / (b - a);
  const sH = 58, cY = sH + 8, cH = 120, pY = cY + cH + 10, pH = 64, lY = pY + pH + 6, H = lY + 16, id = 'tl' + (++uid);
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="timeline"><defs><clipPath id="${id}"><rect x="${L0}" y="0" width="${W - L0}" height="${sH}"/></clipPath></defs>`;
  s += `<g clip-path="url(#${id})">${sh.map(x => { const x0 = X(x.t0), w = Math.max(1, X(x.t1) - x0); return `<image href="${esc(x.thumb)}" x="${x0}" y="0" width="${w}" height="${sH - 5}" preserveAspectRatio="xMidYMid slice"><title>${esc(sym(x.sg))} · ${esc(x.title || '')} · ${Math.round(x.t0)}s</title></image><rect x="${x0}" y="${sH - 5}" width="${w}" height="4" fill="${colOf(x.sg)}"/><line x1="${x0}" x2="${x0}" y1="0" y2="${sH}" stroke="#000" stroke-width="1"/>`; }).join('')}</g>`;
  const signs = [...new Set(sh.map(x => x.sg))], step = 3, xs = []; for (let px = L0; px <= W - 6; px += step) xs.push(px);
  const tOf = px => a + (px - L0) / (W - L0 - 6) * (b - a);
  const traces = signs.map(n => { const ys = xs.map(px => { const t = tOf(px); let v = 0; sh.forEach(x => { if (x.sg !== n) return; const m = (x.t0 + x.t1) / 2, sd = Math.max(1.2, (x.t1 - x.t0) / 2.2); v += Math.exp(-((t - m) ** 2) / (2 * sd * sd)) * Math.min(1, (x.t1 - x.t0) / 6 + .35); }); return v; }); return { n, ys, mx: Math.max(...ys) }; });
  const top = Math.max(1, ...traces.map(t => t.mx));
  s += `<text x="${L0 - 4}" y="${cY + 10}" text-anchor="end" font-size="9">GC</text><line x1="${L0}" x2="${W - 6}" y1="${cY + cH}" y2="${cY + cH}" stroke="#2a2824"/>`;
  traces.sort((p, q) => q.mx - p.mx).forEach(tr => { const pts = xs.map((px, i) => `${px},${(cY + cH - cH * tr.ys[i] / top).toFixed(1)}`).join(' '); s += `<polygon points="${L0},${cY + cH} ${pts} ${W - 6},${cY + cH}" fill="${colOf(tr.n)}" fill-opacity=".28"/><polyline points="${pts}" fill="none" stroke="${colOf(tr.n)}" stroke-width="1.4"/>`;
    const i = tr.ys.indexOf(tr.mx); s += `<text x="${xs[i]}" y="${cY + cH - cH * tr.mx / top - 3}" text-anchor="middle" font-size="10" font-weight="600" fill="${colOf(tr.n)}">${esc(sym(tr.n))}</text>`; });
  const cur = ptCurve(sh, a, b), P = v => pY + pH - pH * v / 14, pts = cur.filter(p => p[1] != null);
  s += `<text x="${L0 - 4}" y="${pY + 10}" text-anchor="end" font-size="9">pT</text>`;
  if (pts.length) {
    s += `<polygon points="${X(pts[0][0])},${pY + pH} ${pts.map(p => `${X(p[0]).toFixed(1)},${P(Math.min(7, p[1])).toFixed(1)}`).join(' ')} ${X(pts.at(-1)[0])},${pY + pH}" fill="${COL.action}" fill-opacity=".55"/>`;
    s += `<polygon points="${X(pts[0][0])},${P(7)} ${pts.map(p => `${X(p[0]).toFixed(1)},${P(Math.max(7, p[1])).toFixed(1)}`).join(' ')} ${X(pts.at(-1)[0])},${P(7)}" fill="${COL.time}" fill-opacity=".8"/>`;
    s += `<line x1="${L0}" x2="${W - 6}" y1="${P(7)}" y2="${P(7)}" stroke="#ece6da" stroke-width=".6" stroke-dasharray="2 3"/>`;
    for (let i = 1; i < cur.length; i++) { const p = cur[i - 1][1], q = cur[i][1]; if (p != null && q != null && (p < 7) !== (q < 7)) s += `<path d="M${X(cur[i][0])},${pY - 2} l-4,-6 l8,0z" fill="${q >= 7 ? COL.time : COL.action}"/>`; }
  }
  D.lines.filter(l => l.film === f.n).forEach(l => s += `<line x1="${X(l.t0)}" x2="${X(l.t0)}" y1="${lY - 2}" y2="${lY + 4}" stroke="#8f887c"/><a href="${nlink(l.t0)}"><text x="${X(l.t0) + 2}" y="${lY + 10}" font-size="9">${l.n}</text></a>`);
  $('#tl').innerHTML = sh.length ? s + '</svg>' : '<p class="empty">no shots in this poem</p>';
}
function drawMS() {
  const f = filmOf(S.film), sp = spectrum(shotsOf(S.src, f)), W = 420, H = 190, L0 = 20, B0 = 22, n = SIGNS.length, X = i => L0 + 4 + i * (W - L0 - 10) / (n - 1), mx = Math.max(1, ...Object.values(sp.sec)), Y = v => H - B0 - (H - B0 - 14) * v / mx;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="sign spectrum"><line x1="${L0}" x2="${W - 4}" y1="${H - B0}" y2="${H - B0}" stroke="#8f887c"/>`;
  FAM.forEach(fm => { const idx = SIGNS.map((x, i) => [x, i]).filter(([x]) => fam(x) === fm).map(([, i]) => i); if (idx.length) s += `<rect x="${X(Math.min(...idx)) - 2}" y="${H - B0 + 2}" width="${X(Math.max(...idx)) - X(Math.min(...idx)) + 4}" height="3" fill="${COL[fm]}"/>`; });
  const top = Object.entries(sp.sec).sort((p, q) => q[1] - p[1]).slice(0, 7).map(x => x[0]);
  SIGNS.forEach((x, i) => { const v = sp.sec[x] || 0; if (!v) return; s += `<line x1="${X(i)}" x2="${X(i)}" y1="${H - B0}" y2="${Y(v)}" stroke="${colOf(x)}" stroke-width="3"><title>${esc(sym(x))} ${Math.round(v)}s</title></line>`; if (top.includes(x)) s += `<text x="${X(i)}" y="${Y(v) - 3}" text-anchor="middle" font-size="10" font-weight="600" fill="${colOf(x)}">${esc(sym(x))}</text>`; });
  [1, 10, 20, 30, 40].forEach(z => { const i = SIGNS.indexOf(String(z)); if (i >= 0) s += `<text x="${X(i)}" y="${H - 4}" text-anchor="middle" font-size="9">${z}</text>`; });
  $('#ms').innerHTML = s + '</svg>';
}
function drawRec() {
  const f = filmOf(S.film); let sh = shotsOf(S.src, f); if (sh.length > 90) sh = sh.filter((_, i) => i % Math.ceil(sh.length / 90) === 0);
  const n = sh.length, W = 300, c = n ? W / n : 1;
  let s = `<svg viewBox="0 0 ${W} ${W}" width="100%" style="max-width:320px;margin:auto" role="img" aria-label="recurrence map">`;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const A = sh[i].sg, B = sh[j].sg; const fill = A === B ? colOf(A) : fam(A) === fam(B) ? colOf(A) : reg(A) === reg(B) ? '#2b2926' : null; if (fill) s += `<rect x="${j * c}" y="${i * c}" width="${c + .2}" height="${c + .2}" fill="${fill}" fill-opacity="${A === B ? 1 : fam(A) === fam(B) ? .35 : 1}"/>`; }
  $('#rec').innerHTML = n ? s + '</svg>' : '<p class="empty">no shots</p>';
}
function drawPhase() {
  const W = 380, H = 240, L0 = 26, B0 = 20, X = v => L0 + (W - L0 - 8) * v / 14, Y = v => H - B0 - (H - B0 - 8) * v, pts = [];
  D.films.forEach(f => sources(f).forEach(([k]) => { if (k === 'pressed' && f.n !== S.film) return; const sp = spectrum(shotsOf(k, f)); if (sp.n) pts.push({ f: f.n, k, x: sp.pT, y: sp.sat }); }));
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="phase diagram"><rect x="${X(7)}" y="8" width="${X(14) - X(7)}" height="${H - B0 - 8}" fill="${COL.time}" fill-opacity=".08"/><rect x="${L0}" y="8" width="${X(7) - L0}" height="${H - B0 - 8}" fill="${COL.action}" fill-opacity=".06"/>`;
  [0, 7, 14].forEach(v => s += `<text x="${X(v)}" y="${H - 6}" text-anchor="middle" font-size="9">${v}</text>`); [0, .5, 1].forEach(v => s += `<text x="${L0 - 4}" y="${Y(v) + 3}" text-anchor="end" font-size="9">${v * 100}</text>`);
  pts.filter(p => p.f !== S.film).forEach(p => s += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="2.2" fill="#4a4640"/>`);
  const mine = pts.filter(p => p.f === S.film), wr = mine.find(p => p.k === 'written');
  mine.forEach(p => { if (wr && p !== wr) s += `<line x1="${X(wr.x)}" y1="${Y(wr.y)}" x2="${X(p.x)}" y2="${Y(p.y)}" stroke="#8f887c" stroke-width=".6"/>`; });
  mine.forEach(p => s += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${p.k === S.src ? 6 : 4}" fill="${p.k === S.src ? COL.hi : p.k === 'written' ? '#ece6da' : '#141412'}" stroke="#ece6da" stroke-width="1.2"><title>${esc(p.k)} · pT ${p.x.toFixed(1)} · ${pct(p.y)} bonded</title></circle><text x="${X(p.x) + 7}" y="${Y(p.y) + 3}" font-size="9" fill="#ece6da">${esc(p.k === 'written' ? 'W' : p.k === 'natural' ? 'N' : p.k.slice(0, 3))}</text>`);
  $('#phase').innerHTML = s + '</svg>';
}
let COORD = null;
function coordination() {
  if (COORD) return COORD;
  const cnt = {}, occ = {}, add = (a, b) => { if (!a || !b || a === b) return; const k = a < b ? a + '|' + b : b + '|' + a; cnt[k] = (cnt[k] || 0) + 1; };
  D.beats.forEach(b => { b.codes.forEach(n => occ[n] = (occ[n] || 0) + 1); for (let i = 0; i < b.codes.length; i++) for (let j = i + 1; j < b.codes.length; j++) add(b.codes[i], b.codes[j]); });
  D.films.forEach(f => CUTS.forEach(([k]) => { const sh = shotsOf(k, f); sh.forEach((x, i) => { occ[x.sg] = (occ[x.sg] || 0) + 1; if (sh[i + 1]) add(x.sg, sh[i + 1].sg); }); }));
  const part = {}; Object.entries(cnt).forEach(([k, n]) => { if (n < 3) return; const [a, b] = k.split('|'); (part[a] = part[a] || new Set()).add(b); (part[b] = part[b] || new Set()).add(a); });   // a relation counts once it recurs three times
  return COORD = { part, occ };
}
function drawLewis() {
  const { part, occ } = coordination(), f = filmOf(S.film), here = new Set(shotsOf(S.src, f).map(x => x.sg));
  const W = 1280, cw = W / 16, H = cw * 3 + 24, r = cw * .26;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Lewis periodic table">`;
  SIGNS.forEach(n => {
    const t = T[n]; if (!t) return; const cx = t.col * cw + cw / 2, cy = t.row * cw + cw / 2 + 4, V = t.valence, Cn = part[n]?.size || 0, c = colOf(n), on = here.has(n);
    for (let k = 0; k < Cn; k++) { const ang = -Math.PI / 2 + 2 * Math.PI * k / Cn, r1 = r + 3, r2 = r + 3 + Math.min(cw * .2, 4 + Cn * .5); s += `<line x1="${cx + r1 * Math.cos(ang)}" y1="${cy + r1 * Math.sin(ang)}" x2="${cx + r2 * Math.cos(ang)}" y2="${cy + r2 * Math.sin(ang)}" stroke="${c}" stroke-width="1"/>`; }
    const ex = Cn >= 3 * V, under = (occ[n] || 0) > 0 && Cn < V;
    s += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${on ? c : '#1d1c19'}" stroke="${ex ? COL.hi : c}" stroke-width="${ex ? 2.2 : 1.2}" ${under ? 'stroke-dasharray="2 2"' : ''}><title>${esc(sym(n))} ${esc(D.signs[n].name)} · valence ${V} · coordination ${Cn}${ex ? ' · EXCESS' : under ? ' · under' : ''}</title></circle>`;
    for (let k = 0; k < V; k++) { const ang = -Math.PI / 2 + (k - (V - 1) / 2) * .55; s += `<circle cx="${cx + (r - 3.5) * Math.cos(ang)}" cy="${cy + (r - 3.5) * Math.sin(ang)}" r="2.6" fill="${on ? '#1d1b18' : c}"/>`; }
    s += `<text x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="${cw * .22}" font-weight="600" fill="${on ? '#1d1b18' : c}">${esc(sym(n))}</text><text x="${cx}" y="${cy + r + 14}" text-anchor="middle" font-size="11">${Cn}/${V}</text>`;
  });
  $('#lewis').innerHTML = s + '</svg>';
}
function drawContact() {
  const n = SIGNS.length, W = 460, L0 = 18, c = (W - L0) / n, H = W;
  const M = {}, mine = new Set(), f = filmOf(S.film);
  D.films.forEach(g => CUTS.forEach(([k]) => { const sh = shotsOf(k, g); sh.forEach((x, i) => { const y = sh[i + 1]; if (!y || x.sg === y.sg) return; const key = x.sg + '>' + y.sg; M[key] = (M[key] || 0) + 1; }); }));
  const cur = shotsOf(S.src, f); cur.forEach((x, i) => { const y = cur[i + 1]; if (y && x.sg !== y.sg) mine.add(x.sg + '>' + y.sg); });
  const mx = Math.max(1, ...Object.values(M)), idx = Object.fromEntries(SIGNS.map((x, i) => [x, i]));
  let conf = 0, abs = 0, regress = 0, ends = 0;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:480px" role="img" aria-label="contact map">`;
  SIGNS.forEach((x, i) => { s += `<rect x="${L0 + i * c}" y="4" width="${c}" height="6" fill="${colOf(x)}"/><rect x="4" y="${L0 + i * c}" width="6" height="${c}" fill="${colOf(x)}"/>`; });
  Object.entries(M).forEach(([k, v]) => { const [a, b] = k.split('>'), i = idx[a], j = idx[b]; if (i == null || j == null) return; const rg = reg(a) === 'time' && reg(b) === 'movement'; if (rg) regress += v; if (T[a]?.valence === 1) ends += v;
    s += `<rect x="${L0 + j * c}" y="${L0 + i * c}" width="${c}" height="${c}" fill="${rg ? COL.hi : '#ece6da'}" fill-opacity="${.18 + .82 * Math.sqrt(v / mx)}"><title>${esc(sym(a))} → ${esc(sym(b))} ×${v}${rg ? ' · regression' : ''}</title></rect>`; });
  SIGNS.forEach(a => (T[a]?.flips || []).forEach(b => { const i = idx[a], j = idx[b]; if (i == null || j == null) return; const seen = M[a + '>' + b] || M[b + '>' + a]; if (a < b) seen ? conf++ : abs++; s += `<rect x="${L0 + j * c + .5}" y="${L0 + i * c + .5}" width="${c - 1}" height="${c - 1}" fill="none" stroke="${seen ? COL.ok : COL.warn}" stroke-width="1.2"/>`; }));
  mine.forEach(k => { const [a, b] = k.split('>'), i = idx[a], j = idx[b]; if (i != null && j != null) s += `<circle cx="${L0 + j * c + c / 2}" cy="${L0 + i * c + c / 2}" r="${c * .22}" fill="#000"/>`; });
  const { part } = coordination(), ex = SIGNS.filter(x => (part[x]?.size || 0) >= 3 * (T[x]?.valence || 2)).length;
  $('#contact').innerHTML = `<div class="nums"><span class="num" style="color:var(--ok)">${conf}<small>✓ flips made</small></span><span class="num" style="color:var(--warn)">${abs}<small>○ never</small></span><span class="num" style="color:var(--hi)">${regress}<small>◁ regressions</small></span><span class="num">${ends}<small>after op/son</small></span><span class="num" style="color:var(--hi)">${ex}<small>excess</small></span></div>` + s + '</svg>';
}

/* ---------- round trip ---------- */
function roundTrip(key, f) {
  const A = shotsOf(key, f); if (!A.length) return null;
  const used = new Set(), B = []; let same = 0, famS = 0, vac = 0;
  A.forEach(x => { const m = (x.t0 + x.t1) / 2, be = D.beats.find(b => m >= b.t0 && m < b.t1) || D.beats.find(b => b.t1 > x.t0 && b.t0 < x.t1), pool = be ? D.cand[be.id] || [] : [];
    const c = pool.find(p => p[1] === x.sg && p[0] !== x.id && !used.has(p[0])) || pool.find(p => p[2] === x.sg && p[0] !== x.id && !used.has(p[0]));
    if (!c) { vac++; B.push(null); return; } used.add(c[0]); B.push({ t0: x.t0, t1: x.t1, sg: c[1], id: c[0], thumb: url(c[7]) }); if (c[1] === x.sg) same++; if (fam(c[1]) === fam(x.sg)) famS++; });
  return { A, B, survive: cos(fingerprint(spectrum(A)), fingerprint(spectrum(B.filter(Boolean)))), sign: same / A.length, fam: famS / A.length, vac: vac / A.length };
}
const stripHTML = (sh, mark) => `<div class="strip">${sh.map((x, i) => x ? `<div class="sh${mark && mark(i) ? ' x' : ''}" style="background-image:url('${esc(x.thumb || '')}');--c:${colOf(x.sg)};flex-grow:${Math.max(.3, x.t1 - x.t0)}" title="${esc(sym(x.sg))}"><b>${esc(sym(x.sg))}</b></div>` : `<div class="sh v" style="flex-grow:1"></div>`).join('')}</div>`;
function drawRT() {
  const f = filmOf(S.film), r = roundTrip(S.src, f);
  const grid = D.films.map(g => CUTS.map(([k]) => roundTrip(k, g)?.survive ?? null));
  let g = `<svg viewBox="0 0 ${14 * 18 + 40} ${4 * 18 + 16}" width="260" role="img" aria-label="round trip grid">`;
  CUTS.forEach(([k], j) => g += `<text x="36" y="${12 + j * 18 + 10}" text-anchor="end" font-size="9">${k.slice(0, 5)}</text>`);
  D.films.forEach((fg, i) => CUTS.forEach(([k], j) => { const v = grid[i][j]; g += `<rect x="${40 + i * 18}" y="${12 + j * 18}" width="16" height="16" fill="${COL.ok}" fill-opacity="${v == null ? 0 : .15 + .85 * v * v}" stroke="${fg.n === S.film && k === S.src ? '#fff' : 'none'}"><title>${fg.n} ${k} · ${v == null ? '—' : pct(v)} survives</title></rect>`; }));
  D.films.forEach((fg, i) => g += `<text x="${40 + i * 18 + 8}" y="9" text-anchor="middle" font-size="8">${fg.n}</text>`);
  $('#rt').innerHTML = r ? `<div class="nums"><span class="num">${pct(r.survive)}<small>survives</small></span><span class="num">${pct(r.sign)}<small>same sign</small></span><span class="num">${pct(r.vac)}<small>∅ vacancies</small></span></div>
    <div class="lbl"><b>A</b><span>film</span></div>${stripHTML(r.A)}<div class="lbl"><b>B</b><span>its chemistry, none of A’s shots</span></div>${stripHTML(r.B, i => r.B[i] && r.B[i].sg !== r.A[i].sg)}<div style="margin-top:8px">${g}</svg></div>` : '<p class="empty">no shots</p>';
}

/* ---------- species ---------- */
let SPECIES = null;
function mineSpecies() {
  const grams = new Map();
  D.films.forEach(f => CUTS.forEach(([k]) => { const rs = runs(shotsOf(k, f));
    for (let n = 2; n <= 4; n++) for (let i = 0; i + n <= rs.length; i++) { const g = rs.slice(i, i + n); if (new Set(g.map(x => x.sg)).size < 2) continue; const key = g.map(x => x.sg).join('|'); let e = grams.get(key); if (!e) grams.set(key, e = { g: g.map(x => x.sg), ex: g, count: 0, poems: new Set() }); e.count++; e.poems.add(f.n); } }));
  return SPECIES = [...grams.values()].filter(e => e.count >= 3 && e.poems.size >= 2).sort((a, b) => b.g.length * b.count - a.g.length * a.count);
}
function drawSpecies() {
  const sp = (SPECIES || mineSpecies()).slice(0, 12);
  $('#species').innerHTML = `<div class="seeds">${sp.map(e => `<div class="seed" title="${esc(e.g.map(sym).join(' '))}"><span class="nm"><span>${e.g.map(sym).join(' ')}</span><i>×${e.count} · ${e.poems.size} poems</i></span>${skeletal(e.ex.map(x => ({ sg: x.sg, thumb: x.thumb })), 200, { r: 17, h: 74, echo: false })}</div>`).join('')}</div>`;
}

/* ---------- synthesis ---------- */
function seeds() {
  const f = filmOf(S.film), bs = D.beats.filter(b => b.film === f.n), c = {}; bs.forEach(b => b.codes.forEach(n => c[n] = (c[n] || 0) + 1));
  const ranked = Object.entries(c).sort((a, b) => b[1] - a[1]).map(x => x[0]), nat = D.natural[f.n] || ranked.slice(0, 5), present = new Set(Object.keys(c).map(fam));
  const all = {}; D.beats.forEach(b => b.codes.forEach(n => all[n] = (all[n] || 0) + 1)); const bestOf = p => Object.entries(all).filter(([n]) => p(n)).sort((a, b) => b[1] - a[1])[0]?.[0];
  const out = [];
  if (ranked.length >= 2) out.push({ name: 'fusion', tag: 'A·B', groups: [[ranked[0], ranked[1]]] });
  if (ranked.length >= 2) out.push({ name: 'echo', tag: 'A─B─A', groups: [[ranked[0]], [ranked[1]], [ranked[0]]] });
  const miss = FAM.filter(x => x !== 'break' && !present.has(x)), dop = miss.length && bestOf(n => fam(n) === miss[0]);
  if (dop) out.push({ name: 'dopant', tag: '+' + FAMN[miss[0]], groups: [[ranked[0]], [dop], [ranked[1] || ranked[0]]] });
  const mv = ranked.find(n => reg(n) === 'movement'), tm = ranked.find(n => reg(n) === 'time') || bestOf(n => reg(n) === 'time');
  if (mv && tm) out.push({ name: 'catalyst', tag: 'M ≈ T', groups: [[mv], ['34b'], [tm]], cat: [1] });
  if (nat.length >= 3) { const ch = chirality(nat); out.push({ name: 'enantiomer', tag: 'χ ' + pct(ch), groups: nat.slice().reverse().map(n => [n]) }); }
  if (ranked.length && tm) out.push({ name: 'time crystal', tag: 'A═A·T─T', groups: [[ranked[0]], [ranked[0], tm], [tm]] });
  return out;
}
function chirality(seq) { const r = seq.map(n => reg(n) === 'time' ? 1 : 0), fa = seq.map(fam); let d = 0; for (let i = 0; i < seq.length; i++) d += (r[i] !== r[seq.length - 1 - i] ? .6 : 0) + (fa[i] !== fa[seq.length - 1 - i] ? .4 : 0); return d / seq.length; }
const molNodes = (groups, cat = []) => groups.map((g, i) => ({ sg: g[0], fused: g[1], cat: cat.includes(i), thumb: POOLTH[g[0]] }));
function drawSeeds() {
  const sd = seeds();
  $('#seeds').innerHTML = `<div class="seeds">${sd.map((x, i) => `<button class="seed" data-s="${i}" title="press ${esc(x.name)}"><span class="nm"><span>${esc(x.name)}</span><i>${esc(x.tag)}</i></span>${skeletal(molNodes(x.groups, x.cat), 200, { r: 16, h: 70, echo: false })}</button>`).join('')}</div>`;
  $('#seeds').querySelectorAll('.seed').forEach(b => b.onclick = () => { const x = sd[+b.dataset.s]; press(x.groups, x.name, x.cat || []); });
}
function drawBench() {
  const { part } = coordination(), cur = S.bench.length - 1;
  $('#bench').innerHTML = `<div class="palette">${FAM.map(fm => `<div class="fam">${SIGNS.filter(n => fam(n) === fm).map(n => atom(n).replace('<span class="at"', `<span class="at" data-a="${esc(n)}" role="button" tabindex="0" title="${esc(D.signs[n].name)} · V${T[n]?.valence} · C${part[n]?.size || 0}"`)).join('')}</div>`).join('')}</div>
    <div class="benchline">${S.bench.map((g, i) => `${i ? '<span style="color:var(--dim)">─</span>' : ''}<span class="grp${i === cur ? ' cur' : ''}${S.benchCat.has(i) ? ' cat' : ''}">${g.length ? g.map((n, j) => atom(n).replace('<span class="at"', `<span class="at" data-rm="${i}:${j}"`)).join('') : '·'}</span>`).join('')}</div>
    <div class="row"><button id="bThen">─ next</button><button id="bCat">≈ catalyst</button><button id="bClear">clear</button><button id="bPress">press ▶</button></div>`;
  $('#bench').querySelectorAll('[data-a]').forEach(a => { const add = () => { S.bench[S.bench.length - 1].push(a.dataset.a); drawBench(); }; a.onclick = add; a.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); add(); } }; });
  $('#bench').querySelectorAll('[data-rm]').forEach(a => a.onclick = () => { const [i, j] = a.dataset.rm.split(':').map(Number); S.bench[i].splice(j, 1); if (!S.bench[i].length && S.bench.length > 1) S.bench.splice(i, 1); drawBench(); });
  $('#bThen').onclick = () => { if (S.bench.at(-1).length) S.bench.push([]); drawBench(); };
  $('#bCat').onclick = () => { const i = S.bench.length - 1; S.benchCat.has(i) ? S.benchCat.delete(i) : S.benchCat.add(i); drawBench(); };
  $('#bClear').onclick = () => { S.bench = [[]]; S.benchCat.clear(); drawBench(); };
  $('#bPress').onclick = () => { const g = S.bench.filter(x => x.length); if (g.length) press(g, 'bench', [...S.benchCat]); };
}
function candOf(c) { return { id: c[0], s1: c[1], s2: c[2], fit: c[3], v: c[4], title: c[5], year: c[6], thumb: url(c[7]), video: url(c[8]), aff: c[9] || [] }; }
function press(groups, name, cat = []) {
  const f = filmOf(S.film), bs = D.beats.filter(b => b.film === f.n && D.lines.some(l => l.film === f.n && l.t1 > b.t0 && l.t0 < b.t1)), used = new Set(), rows = [];
  bs.forEach((b, i) => {
    const gi = Math.min(groups.length - 1, Math.floor(i * groups.length / bs.length)), g = groups[gi], want = new Set(g), pool = (D.cand[b.id] || []).map(candOf);
    if (cat.includes(gi)) { rows.push({ beat: b, group: g, gi, cat: true }); return; }
    const score = x => (want.has(x.s1) ? 2 : 0) + (want.has(x.s2) ? 1.5 : 0) + (want.size > 1 && want.has(x.s1) && want.has(x.s2) ? 2 : 0) + x.fit / 100 - (used.has(x.id) ? 5 : 0);
    const ranked = pool.slice().sort((a, x) => score(x) - score(a)), best = ranked[0], carries = !!best && (want.has(best.s1) || want.has(best.s2));
    if (carries) used.add(best.id);
    rows.push({ beat: b, group: g, gi, shot: carries ? best : null, alt: ranked.find(x => x !== best && (want.has(x.s1) || want.has(x.s2))) || null, pool });
  });
  rows.forEach((r, i) => { if (r.cat) { const p = rows.slice(0, i).reverse().find(x => x.shot); r.shot = p ? p.shot : null; } });
  S.pressFrom = S.src === 'pressed' ? (S.pressFrom || 'written') : S.src;
  S.press = { name, groups, cat, rows }; commit();
  $('#press').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
}
function commit() {
  S.pressed = S.press.rows.filter(r => r.shot && !r.deliberate).map(r => ({ t0: r.beat.t0, t1: r.beat.t1, id: r.shot.id, sg: r.group.includes(r.shot.s1) ? r.shot.s1 : r.group.includes(r.shot.s2) ? r.shot.s2 : r.shot.s1, thumb: r.shot.thumb, title: r.shot.title }));
  drawPress(); drawMicro(); drawConf(); drawTabs(); drawPhase();
}
function drawPress() {
  const box = $('#press'), P = S.press;
  if (!P) { box.innerHTML = ''; return; }
  const real = P.rows.filter(r => !r.cat), ok = real.filter(r => r.shot).length, vac = real.filter(r => !r.shot && !r.deliberate).length;
  box.innerHTML = `<div class="row" style="justify-content:space-between"><span class="nums" style="margin:0"><span class="num">${ok}/${real.length}<small>carried</small></span><span class="num" style="color:var(--hi)">${vac}<small>∅ vacancies</small></span><span class="num" style="font-size:15px">${esc(P.name)}</span></span>
    <span class="row"><button id="pRead">read ▶</button><button id="pEDL">EDL ↓</button><button id="pSave">→ lab film</button></span></div>
    ${skeletal(molNodes(P.groups, P.cat), Math.max(400, box.clientWidth - 20), { r: 18, h: 76, echo: false })}
    <div class="press">${P.rows.map((r, i) => { const s = r.shot, sg = s && (r.group.includes(s.s1) ? s.s1 : r.group.includes(s.s2) ? s.s2 : s.s1);
      const a = `<span class="a">${r.group.map(atom).join('')}</span>`;
      if (r.cat) return `<div class="pb cat" style="background-image:url('${esc(s?.thumb || '')}');--c:${COL.break}" title="catalyst ${r.group.map(sym).join('')}: consumed">${a}</div>`;
      if (!s) return `<div class="pb hole${r.deliberate ? ' del' : ''}" data-v="${i}" title="vacancy · needs ${r.group.map(sym).join('+')}">${a}</div>`;
      return `<div class="pb${r.sub ? ' sub' : ''}" style="background-image:url('${esc(s.thumb)}');--c:${colOf(sg)}" title="${esc(s.title)} ${s.year || ''} · beat ${r.beat.id}">${a}</div>`; }).join('')}</div>`;
  box.querySelectorAll('.pb.hole').forEach(v => v.onclick = () => vacancy(+v.dataset.v));
  $('#pRead').onclick = () => { S.src = 'pressed'; drawAll(); scrollTo({ top: 0, behavior: 'smooth' }); };
  $('#pEDL').onclick = () => download(`wygwyl-${S.film}-${P.name.replace(/\W+/g, '-')}.cineosis-edl.json`, JSON.stringify(edl(), null, 1), 'application/json');
  const sv = $('#pSave'); let armed = false;
  sv.onclick = () => { if (!armed) { armed = true; sv.textContent = 'again: replace'; sv.style.borderColor = 'var(--hi)'; setTimeout(() => { armed = false; sv.textContent = '→ lab film'; sv.style.borderColor = ''; }, 3000); return; }
    const f = filmOf(S.film), keep = store.get('cineosis.film.NL.v1', []).filter(s => !(s.t1 > f.t0 && s.t0 < f.t1)); store.set('cineosis.film.NL.v1', keep.concat(seats()).sort((a, b) => a.t0 - b.t0)); sv.textContent = 'saved ✓'; };
}
function seats() { return S.press.rows.filter(r => r.shot).map((r, i) => ({ id: 'c' + Date.now().toString(36) + i, t0: r.beat.t0, t1: r.beat.t1, text: D.lines.filter(l => l.t1 > r.beat.t0 && l.t0 < r.beat.t1).map(l => l.text).join(' / '), clip: { id: r.shot.id, title: r.shot.title, year: r.shot.year, thumb: r.shot.thumb, video: r.shot.video, loop: false, sg: r.shot.s1, in: 0, dur: null }, by: 'machine', bet: 'NL', why: `pressed · ${S.press.name}` })); }
function edl() { return { format: 'cineosis-edl/1', title: 'WYGWYL', bet: 'CHEM', compound: S.press.name, formula: S.press.groups.map(g => g.map(sym).join('·')).join('─'), made: new Date().toISOString(), clock: { audio: 'WYGWYL_Suite_Audio.mp3', duration: D.duration, fps: 25 },
  events: S.press.rows.map((r, i) => ({ n: i + 1, rec: [r.beat.t0, r.beat.t1], clip: r.shot ? { id: r.shot.id, title: r.shot.title, video: r.shot.video, thumb: r.shot.thumb, sg: r.shot.s1 } : null, vacancy: r.shot ? null : { requires: r.group, deliberate: !!r.deliberate }, catalyst: r.cat ? { requires: r.group, consumed: true } : null })) }; }
function download(name, text, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
function vacancy(i) {
  const r = S.press.rows[i], pop = $('#pop');
  const near = r.pool.map(c => { let s = 0; r.group.forEach(n => { const a = c.aff.find(x => x[0] === n); if (a) s += a[1]; }); return { c, s }; }).filter(x => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 12), mx = near[0]?.s || 1;
  pop.innerHTML = `<h4>∅ beat ${r.beat.id} · needs ${r.group.map(atom).join(' ')}</h4>
    ${near.length ? `<div class="alts">${near.map((x, j) => `<button class="alt" data-j="${j}" style="background-image:url('${esc(x.c.thumb)}');--c:${colOf(x.c.s1)}" title="${esc(x.c.title)} · reads ${esc(sym(x.c.s1))} ${esc(sym(x.c.s2))}"><span>${(x.s / mx).toFixed(2)}</span></button>`).join('')}</div>` : '<p class="empty">∅ nothing in this beat’s pool reads it: the footage does not exist yet</p>'}
    <div class="row"><button id="vLeave">◌ leave empty</button><button id="vBench">edit compound</button><a href="${nlink(r.beat.t0)}" target="_blank" rel="noopener">forage ↗</a><button id="vClose" style="margin-left:auto">✕</button></div>`;
  pop.hidden = false;
  pop.querySelectorAll('.alt').forEach(b => b.onclick = () => { r.shot = near[+b.dataset.j].c; r.sub = true; pop.hidden = true; commit(); });
  $('#vLeave').onclick = () => { r.deliberate = true; pop.hidden = true; commit(); };
  $('#vBench').onclick = () => { S.bench = S.press.groups.map(g => g.slice()); S.benchCat = new Set(S.press.cat); pop.hidden = true; drawBench(); };
  $('#vClose').onclick = () => { pop.hidden = true; };
}
function drawMicro() {
  const box = $('#micro'), P = S.press; if (!P) { box.innerHTML = '<p class="empty">press something</p>'; return; }
  const f = filmOf(S.film), before = shotsOf(S.pressFrom, f), after = S.pressed, sb = spectrum(before), sa = spectrum(after);
  const map = after.map(x => { const m = (x.t0 + x.t1) / 2; return before.find(z => m >= z.t0 && m < z.t1) || null; });
  const B = new Set(Object.keys(sb.sec)), A = new Set(Object.keys(sa.sec));
  box.innerHTML = `<div class="nums"><span class="num">${sb.pT.toFixed(1)} → ${sa.pT.toFixed(1)}<small>pT</small></span><span class="num">${after.filter((x, i) => map[i] && map[i].sg !== x.sg).length}/${after.length}<small>atoms changed</small></span></div>
    <div class="lbl"><b>before</b><span>${esc(S.pressFrom)}</span></div>${stripHTML(map.map((z, i) => z ? { ...z, t0: after[i].t0, t1: after[i].t1 } : null))}
    <div class="lbl"><b>after</b><span>pressed</span></div>${stripHTML(after, i => map[i] && map[i].sg !== after[i].sg)}
    <div class="lbl"><span>kept</span></div><div class="formula">${[...A].filter(n => B.has(n)).map(atom).join('') || '·'}</div>
    <div class="lbl"><span style="color:var(--hi)">− lost</span></div><div class="formula" style="opacity:.55">${[...B].filter(n => !A.has(n)).map(atom).join('') || '·'}</div>
    <div class="lbl"><span style="color:var(--ok)">+ gained</span></div><div class="formula">${[...A].filter(n => !B.has(n)).map(atom).join('') || '·'}</div>`;
}
function drawConf() {
  const box = $('#conf'), P = S.press; if (!P) { box.innerHTML = '<p class="empty">press something</p>'; return; }
  const A = S.pressed, Bc = P.rows.filter(r => r.shot || r.alt).map(r => { const s = r.alt || r.shot; return { t0: r.beat.t0, t1: r.beat.t1, id: s.id, sg: r.group.includes(s.s1) ? s.s1 : r.group.includes(s.s2) ? s.s2 : s.s1, thumb: s.thumb }; });
  const Cc = []; A.forEach(x => { const p = Cc.at(-1); if (p && p.sg === x.sg) p.t1 = x.t1; else Cc.push({ ...x }); });
  const Dd = []; P.rows.forEach(r => { if (!r.shot) return; const m = (r.beat.t0 + r.beat.t1) / 2, s2 = r.alt || r.shot; Dd.push({ t0: r.beat.t0, t1: m, id: r.shot.id, sg: r.shot.s1, thumb: r.shot.thumb }, { t0: m, t1: r.beat.t1, id: s2.id + 'b', sg: s2.s1, thumb: s2.thumb }); });
  const base = fingerprint(spectrum(A)), ids = new Set(A.map(x => x.id));
  box.innerHTML = [['A', 'takes', A], ['B', 'other takes', Bc], ['C', 'long takes', Cc], ['D', 'staccato', Dd]].map(([k, n, f]) => `<div class="lbl"><b>${k} · ${n}</b><span>structure ${pct(cos(base, fingerprint(spectrum(f))))} · footage ${pct(f.filter(x => ids.has(x.id)).length / Math.max(1, f.length))} · ${f.length} cuts</span></div>${stripHTML(f)}`).join('');
}

function help() {
  const pop = $('#pop');
  pop.innerHTML = `<h4>notation</h4><div class="help"><dl>
    <dt>atom</dt><dd>a shot, ringed in its sign’s family colour; a second ring = time-image; a small satellite = a fused second sign</dd>
    <dt>─ ═ ≡</dt><dd>cut · held (same sign) · rhyme (same image type)</dd><dt>⇢</dt><dd>resonance: a confusable flip</dd>
    <dt>▶ ◁</dt><dd>break into time (wedge) · regression back to movement (hashed, red)</dd><dt>┄ arc</dt><dd>echo: a sign returning</dd>
    <dt>• ─</dt><dd>Lewis table: dots = valence (theory), spokes = coordination (partners that recur 3×)</dd>
    <dt>□ ■</dt><dd>contact map: outlined = a flip the theory allows (green made, amber never); filled = observed; red = regression; ● = this film</dd>
    <dt>pT</dt><dd>time pressure 0 (movement) – 14 (time); ▼ marks a phase transition</dd><dt>∅ ◌ ≈</dt><dd>vacancy · left empty on purpose · catalyst, consumed</dd>
    <dt>loop</dt><dd>film → chemistry → pressed film → chemistry (round trip)</dd></dl></div><div class="row" style="margin-top:8px"><button id="hClose" style="margin-left:auto">✕</button></div>`;
  pop.hidden = false; $('#hClose').onclick = () => { pop.hidden = true; };
}
addEventListener('keydown', e => { if (e.key === 'Escape') $('#pop').hidden = true; });

function drawAll() { drawTabs(); drawSkel(); drawTimeline(); drawMS(); drawRec(); drawPhase(); drawLewis(); drawContact(); drawRT(); drawSeeds(); drawBench(); drawPress(); drawMicro(); drawConf(); }
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
  D = d; T = d.theory; SIGNS = Object.keys(d.signs).sort((a, b) => parseFloat(a) - parseFloat(b) || a.localeCompare(b));
  FAM.forEach(f => COL[f] = C(f)); COL.hi = C('hi'); COL.ok = C('ok'); COL.warn = C('warn');
  Object.values(d.cand).forEach(v => v.forEach(c => { CM.set(c[0], c); if (c[1] && !POOLTH[c[1]]) POOLTH[c[1]] = url(c[7]); }));
  $('#legend').innerHTML = FAM.map(f => `<span><i style="--c:${COL[f]}"></i>${FAMN[f]}</span>`).join('') + BKEYS.map(k => `<span><b>${BSYM[k]}</b>${BNAME[k]}</span>`).join('');
  $('#helpBtn').onclick = help;
  const q = new URLSearchParams(location.search).get('poem'); if (q && d.films.some(f => f.n === q)) S.film = q;
  mineSpecies(); drawAll(); drawSpecies();
  addEventListener('resize', () => { clearTimeout(drawAll.t); drawAll.t = setTimeout(() => { drawSkel(); drawPress(); }, 200); });
}).catch(e => { document.body.insertAdjacentHTML('beforeend', `<p class="empty">could not load the apparatus data: ${esc(e.message)}. If the site was just updated, <button type="button" onclick="location.reload()">reload</button>.</p>`); console.error(e); });
})();
