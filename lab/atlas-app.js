/* ATLAS OF THE LAB · the app. See atlas.html for what each view means. Data: atlas.json (atlas_build.py). */
const $ = s => document.querySelector(s), esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
let A, P, byPath, famOf, subOf, sel = null, view = 'city', q = '';
const ST = { colour: 'kind', size: 'lines', district: 'subject', show: 'all', scale: 'sqrt', off: new Set() };
try { const s = JSON.parse(localStorage.getItem('atlas.st') || '{}'); ['colour', 'size', 'district', 'scale'].forEach(k => s[k] && (ST[k] = s[k])); } catch (e) { }
const save = () => { try { localStorage.setItem('atlas.st', JSON.stringify({ colour: ST.colour, size: ST.size, district: ST.district, scale: ST.scale, view })); } catch (e) { } };
const KIND = { explainer: ['Explainer film', '#c4f46a'], film: ['Film or player', '#7fd6e8'], series: ['Series episode', '#6f8cff'], browser: ['Archive browser', '#d8d0c0'],
  machine: ['Machine view', '#b48ead'], bench: ['Bench or tool', '#e6a23c'], reading: ['Reading or paper', '#c9a4ff'], game: ['Game', '#f2c14e'],
  index: ['Front door or index', '#ffffff'], mark: ['Mark and identity', '#f4a3c0'], template: ['Template', '#5a544b'], pointer: ['Pointer, superseded', '#3d3832'] };
const STATUS = { reachable: ['On a road from the gate', '#8fc46a'], hidden: ['Only via a lost page', '#f2c14e'], orphan: ['No road: orphan', '#ff8f6e'], pointer: ['Signpost elsewhere', '#6f685d'], template: ['Template', '#3d3832'] };
const SIZE = { lines: ['Code', 'lines', p => p.lines, v => Math.round(v).toLocaleString() + ' lines', 20], hours: ['Hours', 'estimated', p => p.hours, v => '~' + v.toFixed(1) + ' h', .08],
  commits: ['Commits', 'versions saved', p => p.commits, v => v + ' commits', 1], importance: ['Importance', 'by links', p => p.importance, v => v.toFixed(2), .15] };
const COLOUR = { kind: ['Type', 'what it is'], subject: ['Serves', 'the work it is for'], family: ['Filed as', 'its name says'], status: ['Reach', 'is there a road?'] };
const LIGHT = new Set(['#ffffff', '#d8d0c0', '#c4f46a', '#f2c14e', '#e6a23c', '#7fd6e8', '#f4a3c0', '#8fc46a', '#ff8f6e', '#9fd36a', '#d9b44a', '#b9cfa0', '#f4c7d0', '#c9a4ff', '#6cc4d6', '#5fbf8f']);
const groupOf = p => ST.colour === 'kind' ? p.kind : ST.colour === 'subject' ? p.subject : ST.colour === 'family' ? p.family : p.status;
const groups = () => ST.colour === 'kind' ? Object.entries(KIND).map(([k, [n, c]]) => [k, n, c]) : ST.colour === 'subject' ? A.subjects.map(s => [s.id, s.name, s.color])
  : ST.colour === 'family' ? A.families.map(f => [f.id, f.name, f.color]) : Object.entries(STATUS).map(([k, [n, c]]) => [k, n, c]);
const colourOf = p => (groups().find(g => g[0] === groupOf(p)) || [, , '#888'])[2];
const val = p => { const v = Math.max(SIZE[ST.size][4], SIZE[ST.size][2](p) || 0); return ST.scale === 'sqrt' ? Math.sqrt(v) : v; };
const fmtDay = d => d ? new Date(d + 'T12:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : '—';
const href = p => '../' + p;
const problem = p => p.ia || p.status === 'orphan' || p.status === 'hidden' || (p.versions[0] && p.versions[0][1] >= .9);
function visible(p) {
  if (ST.off.has(groupOf(p))) return false;
  if (ST.show === 'problems' && !problem(p)) return false; if (ST.show === 'orphans' && !['orphan', 'hidden'].includes(p.status)) return false;
  if (ST.show === 'misfiled' && !p.ia) return false; if (ST.show === 'copies' && !(p.versions[0] && p.versions[0][1] >= .3)) return false;
  if (!q) return true; const s = (p.title + ' ' + p.path + ' ' + p.desc + ' ' + famOf[p.family].name + ' ' + (subOf[p.subject]?.name || '') + ' ' + KIND[p.kind][0]).toLowerCase(); return q.split(/\s+/).every(w => s.includes(w));
}
fetch('atlas.json?v=' + Date.now()).then(r => r.json()).then(d => {
  A = d; P = d.pages; byPath = Object.fromEntries(P.map(p => [p.path, p])); famOf = Object.fromEntries(d.families.map(f => [f.id, f])); subOf = Object.fromEntries(d.subjects.map(s => [s.id, s]));
  $('#sub').textContent = `THE REPOSITORY AS A CITY · ${d.totals.pages} PAGES · ${P.reduce((s, p) => s + p.lines, 0).toLocaleString()} LINES · ~${Math.round(d.hoursTotal)} HOURS · ${d.totals.commits} COMMITS`;
  let v0 = 'city'; try { v0 = JSON.parse(localStorage.getItem('atlas.st') || '{}').view || 'city'; } catch (e) { }
  const h = decodeURIComponent(location.hash.slice(1)); if (byPath[h]) sel = h; setView(v0, true); ctl(); dot(); draw();
  if (window.ATLAS) ATLAS.load('.', 'atlas/').then(() => { dot(); });
});
function setView(v, quiet) { view = v; document.body.classList.toggle('paper', v === 'ledger'); document.querySelectorAll('nav.views button').forEach(b => b.classList.toggle('on', b.dataset.v === v)); document.querySelectorAll('.view').forEach(e => e.classList.toggle('on', e.id === 'v-' + v)); save(); if (!quiet) { ctl(); draw(); } }
document.querySelectorAll('nav.views button').forEach(b => b.onclick = () => setView(b.dataset.v));
$('#q').oninput = e => { q = e.target.value.trim().toLowerCase(); ctl(); draw(); results(); };
/* the results list under the search: every match as a moving frame, with where the words were found */
let rk = -1;
function results() { const el = $('#res'); if (!q || !window.ATLAS || !ATLAS.pages.length) { el.classList.remove('on'); return; } const rs = ATLAS.search(q); rk = -1;
  el.innerHTML = rs.slice(0, 10).map((r, i) => `<div class="r" data-i="${i}" data-path="${esc(r.p.path)}"><img ${ATLAS.flipAttr(r.p, i)} alt=""><div><b>${ATLAS.mark(r.p.clean, q)}</b><small>${esc(ATLAS.subjects[r.p.subject].name)} · ${esc(ATLAS.KIND[r.p.kind])}${r.p.tags.length ? ' · looks like ' + esc(r.p.tags.slice(0, 2).join(', ')) : ''}</small>${r.snip ? `<p>${r.snip}</p>` : ''}</div></div>`).join('')
    + `<div class="more">${rs.length ? `${rs.length} match${rs.length > 1 ? 'es' : ''} · ↑ ↓ and Enter · <a href="atlas/wall.html?q=${encodeURIComponent(q)}">see them all on the Wall →</a>` : 'Nothing matches. Try a work (odyssey), a kind (game), or what it looked like (map, timeline, crowd).'}</div>`;
  el.classList.add('on'); el.querySelectorAll('.r').forEach(r => r.onmousedown = ev => { ev.preventDefault(); pickRes(r.dataset.path); }); }
function pickRes(path) { $('#res').classList.remove('on'); select(path); }
$('#q').addEventListener('blur', () => setTimeout(() => $('#res').classList.remove('on'), 150));
$('#q').addEventListener('focus', () => q && results());
$('#q').onkeydown = e => { const rows = [...document.querySelectorAll('#res .r')];
  if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && rows.length) { e.preventDefault(); rk = Math.max(0, Math.min(rows.length - 1, rk + (e.key === 'ArrowDown' ? 1 : -1))); rows.forEach((r, i) => r.classList.toggle('k', i === rk)); rows[rk].scrollIntoView({ block: 'nearest' }); return; }
  if (e.key === 'Enter' && rows.length) { pickRes(rows[Math.max(0, rk)].dataset.path); return; }
  if (e.key === 'Enter') { const hit = P.filter(visible).sort((a, b) => (b.title.toLowerCase().includes(q) - a.title.toLowerCase().includes(q)) || b.importance - a.importance)[0]; if (hit) select(hit.path); } };
addEventListener('keydown', e => { if (e.key === '/' && document.activeElement !== $('#q')) { e.preventDefault(); $('#q').focus(); } if (e.key === 'Escape') { if (document.activeElement === $('#q')) { $('#q').value = ''; q = ''; $('#q').blur(); ctl(); draw(); } else select(null); } });
addEventListener('hashchange', () => { const h = decodeURIComponent(location.hash.slice(1)); if (byPath[h] && h !== sel) select(h); });
addEventListener('resize', () => { clearTimeout(window._rz); window._rz = setTimeout(draw, 160); });
function draw() { if (A) ({ city, ledger, work, lineage, time, list, dig })[view](); }

/* CONTROLS · big switches; each one redraws the map so you can see what it changes */
function ctl() {
  const seg = (title, key, opts, note) => `<div class="cg"><h4>${title}</h4><div class="seg">${opts.map(([k, a, b]) => `<button data-k="${key}" data-v="${k}" class="${ST[key] === k ? 'on' : ''}">${a}<small>${b}</small></button>`).join('')}</div>${note ? `<div class="hint" style="margin-top:6px">${note}</div>` : ''}</div>`;
  const n = g => P.filter(p => groupOf(p) === g).length;
  $('#ctl').innerHTML = seg('Colour by', 'colour', Object.entries(COLOUR).map(([k, [a, b]]) => [k, a, b]))
    + `<div class="cg"><h4>${COLOUR[ST.colour][0]} · click to hide or show</h4><div class="leg">${groups().filter(g => n(g[0])).map(([k, name, c]) => `<button class="${ST.off.has(k) ? 'off' : ''}" data-g="${k}"><i style="--c:${c}"></i><span>${esc(name)}</span><b>${n(k)}</b></button>`).join('')}</div>${ST.off.size ? '<button class="hint" id="showall" style="margin-top:6px;text-decoration:underline">show all</button>' : ''}</div>`
    + seg('Size by', 'size', Object.entries(SIZE).map(([k, [a, b]]) => [k, a, b]), view === 'city' ? 'Size is a building’s footprint. Taller buildings have more commits.' : '')
    + (view === 'city' ? seg('Scale', 'scale', [['sqrt', 'Compressed', 'small pages stay visible'], ['true', 'True to size', 'area = amount']], ST.scale === 'sqrt' ? 'Areas follow the square root, so one huge page cannot flatten the rest. WORK shows the true amounts.' : 'Areas are exact: compare them directly.') : '')
    + (view === 'city' ? seg('Districts by', 'district', [['subject', 'What it serves', 'read from the page'], ['family', 'Where it is filed', 'its file name']], 'Switch between the two to see where the filing and the purpose disagree.') : '')
    + seg('Show', 'show', [['all', 'Everything', 'all pages'], ['problems', 'Problems', 'anything to fix'], ['orphans', 'Lost', 'no road'], ['misfiled', 'Misfiled', 'name ≠ purpose'], ['copies', 'Versions', 'share code']])
    + `<div class="hint">Hours are estimated from the gaps between commits, shared by lines changed: a measure of attention, not a timesheet. Importance is PageRank over the links. Alt-click a colour to show only it.</div>`;
  $('#ctl').querySelectorAll('.seg button').forEach(b => b.onclick = () => { ST[b.dataset.k] = b.dataset.v; if (b.dataset.k === 'colour') ST.off.clear(); save(); ctl(); draw(); });
  $('#ctl').querySelectorAll('.leg button').forEach(b => b.onclick = e => { const g = b.dataset.g; if (e.altKey) ST.off = new Set(groups().map(x => x[0]).filter(x => x !== g)); else ST.off.has(g) ? ST.off.delete(g) : ST.off.add(g); ctl(); draw(); });
  const sa = $('#showall'); if (sa) sa.onclick = () => { ST.off.clear(); ctl(); draw(); };
}
const tip = $('#tip');
function showTip(e, p) {
  tip.innerHTML = `<b>${esc(p.title)}</b>${esc(p.path)}<br>${esc(KIND[p.kind][0])} · serves ${esc(subOf[p.subject].name)}<br>${p.lines.toLocaleString()} lines${p.dataLines > 200 ? ` (+${p.dataLines.toLocaleString()} pasted in)` : ''} · ~${p.hours.toFixed(1)} h · ${p.commits} commits · importance #${p.rank}${p.parent ? `<br>descends from ${esc(byPath[p.parent]?.title)}` : ''}${p.ia ? `<br><span style="color:#f2c14e">⚑ ${esc(p.ia)}</span>` : ''}${p.status !== 'reachable' ? `<br><span style="color:#ff8f6e">${esc(STATUS[p.status][0])}</span>` : ''}`;
  tip.style.display = 'block'; tip.style.left = Math.min(innerWidth - 400, e.clientX + 16) + 'px'; tip.style.top = Math.min(innerHeight - 160, e.clientY + 14) + 'px';
}
const hideTip = () => tip.style.display = 'none';
function wire(el) { el.querySelectorAll('[data-p]').forEach(g => { const p = byPath[g.dataset.p]; if (!p) return; g.addEventListener('click', ev => { ev.stopPropagation(); select(p.path); }); if (g.dataset.tip !== 'no') { g.addEventListener('mousemove', e => showTip(e, p)); g.addEventListener('mouseleave', hideTip); } }); }

/* squarified treemap */
function squarify(items, r) {
  const out = [], rest = items.filter(i => i.w > 0).sort((a, b) => b.w - a.w), tot = rest.reduce((s, i) => s + i.w, 0); if (!tot) return out;
  let { x, y, w, h } = r; const k = w * h / tot; let row = [];
  const worst = (rw, side) => { const s = rw.reduce((a, i) => a + i.w * k, 0), mx = Math.max(...rw.map(i => i.w * k)), mn = Math.min(...rw.map(i => i.w * k)); return Math.max(side * side * mx / (s * s), s * s / (side * side * mn)); };
  const lay = rw => { const s = rw.reduce((a, i) => a + i.w * k, 0); if (w >= h) { const cw = s / h; let yy = y; rw.forEach(i => { const hh = i.w * k / cw; out.push({ ...i, x, y: yy, w: cw, h: hh }); yy += hh; }); x += cw; w -= cw; } else { const rh = s / w; let xx = x; rw.forEach(i => { const ww = i.w * k / rh; out.push({ ...i, x: xx, y, w: ww, h: rh }); xx += ww; }); y += rh; h -= rh; } };
  while (rest.length) { const side = Math.min(w, h), c = rest[0]; if (!row.length || worst([...row, c], side) <= worst(row, side)) { row.push(c); rest.shift(); } else { lay(row); row = []; } }
  if (row.length) lay(row); return out;
}

/* CITY */
function city() {
  const el = $('#v-city'), W = Math.max(320, el.clientWidth), H = Math.max(420, el.clientHeight), M = 10;
  const key = ST.district === 'subject' ? 'subject' : 'family', D = ST.district === 'subject' ? A.subjects : A.families;
  const vis = P.filter(visible), dists = D.map(d => ({ d, ps: vis.filter(p => p[key] === d.id) })).filter(x => x.ps.length).map(x => ({ ...x, w: x.ps.reduce((s, p) => s + val(p), 0) }));
  const drs = squarify(dists, { x: M, y: M, w: W - 2 * M, h: H - 2 * M }), B = {};
  let blocks = '', bld = '', roads = '', labels = '';
  drs.forEach(dr => {
    const pad = 5, top = dr.h > 60 && dr.w > 70 ? 28 : 4, tot = dr.ps.reduce((s, p) => s + (SIZE[ST.size][2](p) || 0), 0);
    blocks += `<rect x="${dr.x + 2}" y="${dr.y + 2}" width="${dr.w - 4}" height="${dr.h - 4}" rx="7" fill="#14120f" stroke="${dr.d.color}" stroke-opacity=".7" stroke-width="2"/>`;
    if (top > 10) labels += `<text x="${dr.x + 11}" y="${dr.y + 21}" font-family="Fraunces, serif" font-weight="600" font-size="${Math.min(17, Math.max(11.5, dr.w / 16))}" fill="${dr.d.color}" pointer-events="none">${esc(dr.d.name.length * 8.5 > dr.w - 90 ? dr.d.name.slice(0, Math.max(4, Math.floor((dr.w - 90) / 8.5))) + '…' : dr.d.name)}</text><text x="${dr.x + dr.w - 11}" y="${dr.y + 21}" text-anchor="end" font-size="11.5" fill="#7b7468" pointer-events="none">${dr.ps.length} · ${SIZE[ST.size][3](tot)}</text>`;
    squarify(dr.ps.map(p => ({ p, w: val(p) })), { x: dr.x + pad, y: dr.y + pad + top, w: dr.w - 2 * pad, h: dr.h - 2 * pad - top }).forEach(b => { B[b.p.path] = b; });
  });
  const cx = p => B[p].x + B[p].w / 2, cy = p => B[p].y + B[p].h / 2, street = (a, b) => `M${cx(a)},${cy(a)} H${cx(b)} V${cy(b)}`;
  vis.forEach(p => { const par = p.route[p.route.length - 1]; if (!par || !B[par] || !B[p.path]) return; roads += `<path d="${street(par, p.path)}" fill="none" stroke="#5a544b" stroke-width="${1.2 + Math.sqrt(p.traffic + 1) * 1.1}" stroke-linecap="round" opacity=".9"/>`; });
  let selRoad = '';
  if (sel && B[sel]) {
    const s = byPath[sel], chain = [...s.route, sel].filter(x => B[x]);
    s.out.filter(o => B[o] && !chain.includes(o)).forEach(o => selRoad += `<path d="M${cx(sel)},${cy(sel)} L${cx(o)},${cy(o)}" stroke="#e0483a" stroke-width="1.3" opacity=".5" stroke-dasharray="5 5"/>`);
    for (let i = 1; i < chain.length; i++) selRoad += `<path d="${street(chain[i - 1], chain[i])}" fill="none" stroke="#e0483a" stroke-width="4.5" stroke-linecap="round"/>`;
  }
  Object.values(B).forEach(b => {
    const p = b.p, g = 2.5, x = b.x + g, y = b.y + g, w = Math.max(1, b.w - 2 * g), h = Math.max(1, b.h - 2 * g), e = Math.min(18, Math.max(1.5, Math.sqrt(p.commits) * 2.6), w * .3, h * .3);
    const c = colourOf(p), s = sel === p.path, lost = p.status === 'orphan' || p.status === 'hidden', rw = w - e, rh = h - e, dark = LIGHT.has(c) && !lost;
    bld += `<g data-p="${esc(p.path)}" style="cursor:pointer"><path d="M${x + rw},${y} l${e},${e} v${rh} h${-rw} l${-e},${-e} z" fill="#000" opacity=".6"/>
      <rect x="${x}" y="${y}" width="${rw}" height="${rh}" rx="2.5" fill="${c}" fill-opacity="${lost ? .3 : .95}" stroke="${s ? '#e0483a' : lost ? '#ff8f6e' : '#0b0a09'}" stroke-width="${s ? 3.5 : lost ? 2 : .8}" ${lost ? 'stroke-dasharray="5 3"' : ''}/>
      ${p.ia ? `<path d="M${x + rw - 14},${y} h14 v14 z" fill="#f2c14e" stroke="#0b0a09" stroke-width=".8"/>` : ''}${p.parent || p.children.length ? `<circle cx="${x + 7}" cy="${y + rh - 7}" r="3.2" fill="none" stroke="${dark ? '#0b0a09' : '#ece6da'}" stroke-width="1.6"/>` : ''}
      ${rw > 62 && rh > 22 ? `<text x="${x + 7}" y="${y + 16}" font-size="${Math.min(14, Math.max(10.5, rw / 14))}" fill="${dark ? '#0b0a09' : '#ece6da'}" font-family="Fraunces, serif" font-weight="600" pointer-events="none">${esc(p.title.length * 6.8 > rw - 12 ? p.title.slice(0, Math.max(3, Math.floor((rw - 12) / 6.8))) + '…' : p.title)}</text>` : ''}
      ${rw > 62 && rh > 40 ? `<text x="${x + 7}" y="${y + 31}" font-size="11" fill="${dark ? '#2a2621' : '#b3ab9e'}" pointer-events="none">${SIZE[ST.size][3](SIZE[ST.size][2](p) || 0)}</text>` : ''}</g>`;
  });
  const gate = B['lab/index.html'];
  const gateMark = gate ? `<g transform="translate(${cx('lab/index.html')},${cy('lab/index.html')})" pointer-events="none"><line x1="0" y1="-44" x2="0" y2="-16" stroke="#e0483a" stroke-width="3"/><circle r="15" fill="#0b0a09" stroke="#ece6da" stroke-width="3.5"/><circle cx="4" cy="2" r="3.8" fill="#ece6da"/><rect x="-24" y="21" width="48" height="17" rx="3" fill="#0b0a09"/><text y="34" text-anchor="middle" font-size="11.5" fill="#ece6da" font-weight="600" letter-spacing="1.5">GATE</text></g>` : '';
  const here = sel && B[sel] && sel !== 'lab/index.html' ? (() => { const x = cx(sel), y = B[sel].y + 6; return `<g pointer-events="none"><line x1="${x}" y1="0" x2="${x}" y2="${y - 24}" stroke="#e0483a" stroke-width="2.5"/><circle cx="${x}" cy="${y - 13}" r="11" fill="#0b0a09" stroke="#ece6da" stroke-width="3"/><circle cx="${x + 3}" cy="${y - 12}" r="2.8" fill="#ece6da"/></g>`; })() : '';
  el.innerHTML = `<svg width="${W}" height="${H}" style="display:block">${blocks}${roads}${bld}${selRoad}${labels}${gateMark}${here}</svg>`;
  el.querySelector('svg').onclick = () => select(null); wire(el);
}

/* WORK · how much went into each, compared */
function work() {
  const el = $('#v-work'), vis = P.filter(visible), f = SIZE[ST.size], v = p => f[2](p) || 0, max = Math.max(...vis.map(v), 1e-9);
  const D = A.subjects.map(s => ({ s, ps: vis.filter(p => p.subject === s.id) })).filter(x => x.ps.length).map(x => ({ ...x, t: x.ps.reduce((a, p) => a + v(p), 0) })).sort((a, b) => b.t - a.t), dmax = Math.max(...D.map(d => d.t), 1e-9);
  const tot = vis.reduce((a, p) => a + v(p), 0);
  el.innerHTML = `<div class="work"><div class="wh"><span>${f[0]} by the work each page serves</span><span>${f[3](tot)} in all</span></div>
    ${D.map(d => `<div class="wrow" style="cursor:default"><div class="t"><span class="sw" style="--c:${d.s.color};margin-right:8px"></span>${esc(d.s.name)} <small style="color:var(--faint);font:12px var(--mono)">${d.ps.length} pages</small></div>
      <div class="stack" style="width:${d.t / dmax * 100}%">${groups().map(([k, name, c]) => { const s = d.ps.filter(p => groupOf(p) === k).reduce((a, p) => a + v(p), 0); return s ? `<i style="--c:${c};width:${s / d.t * 100}%" title="${esc(name)}: ${esc(f[3](s))}"></i>` : ''; }).join('')}</div><div class="v">${f[3](d.t)}</div></div>`).join('')}
    <div class="hint" style="margin:6px 6px 0">Each bar is split by the colour chosen on the left (${COLOUR[ST.colour][0].toLowerCase()}). Hover a piece for its name.</div>
    <div class="wh"><span>Every page, by ${f[0].toLowerCase()}</span><span>${vis.length} pages</span></div>
    ${[...vis].sort((a, b) => v(b) - v(a)).map(p => `<div class="wrow ${sel === p.path ? 'sel' : ''}" data-p="${esc(p.path)}"><div class="t">${p.ia ? '<span style="color:#f2c14e">⚑ </span>' : ''}${esc(p.title)}</div><div><div class="b" style="--c:${colourOf(p)};width:${v(p) / max * 100}%"></div></div><div class="v">${f[3](v(p))}</div></div>`).join('')}</div>`;
  wire(el);
}

/* LINEAGE · which pages are versions of which, and what came from what */
function lineage() {
  const el = $('#v-lineage'), chip = (x, extra = '') => byPath[x] ? `<button class="chip" data-p="${esc(x)}" data-tip="no"><i style="--c:${colourOf(byPath[x])}"></i><span>${esc(byPath[x].title)}</span><small>${fmtDay(byPath[x].born)} · ${byPath[x].lines.toLocaleString()} lines${extra}</small></button>` : '';
  const pairs = []; P.forEach(p => p.versions.forEach(([o, s]) => { if (p.path < o) pairs.push([p.path, o, s]); }));
  const copies = pairs.filter(x => x[2] >= .9).sort((a, b) => b[2] - a[2]), near = pairs.filter(x => x[2] >= .3 && x[2] < .9 && !(/republic-ep/.test(x[0]) && /republic-ep/.test(x[1]))).sort((a, b) => b[2] - a[2]);
  const tree = (p, depth) => { const x = byPath[p]; return `<div class="node" style="padding-left:${depth * 30}px">${depth ? `<span class="arrow">└ ${Math.round(x.parentSim * 100)}% of its code →</span>` : ''}${chip(p, x.descendants ? ` · ${x.descendants} descendant${x.descendants > 1 ? 's' : ''}` : '')}</div>` + x.children.map(c => tree(c, depth + 1)).join(''); };
  el.innerHTML = `<div class="lin"><h3>Copies: ${copies.length} pairs with nine-tenths of their code the same</h3><p>These are the same page twice. Keep one and point the other at it.</p>
    ${copies.map(([a, b, s]) => `<div class="tree"><div class="node">${chip(a)}<span class="arrow">${Math.round(s * 100)}% the same</span>${chip(b)}</div></div>`).join('') || '<p>None.</p>'}
    <h3>Family trees: ${A.clusters.length} lines of descent</h3><p>A page descends from an earlier page when at least three tenths of its code is shared with it. The percentage is how much it kept.</p>
    ${A.clusters.map(c => `<div class="tree">${tree(c.root, 0)}</div>`).join('')}
    <h3>Relatives: ${near.length} more pairs that share code</h3><p>Not one copied from the other, but kin: the same machinery used again.</p>
    ${near.slice(0, 40).map(([a, b, s]) => `<div class="tree"><div class="node">${chip(a)}<span class="arrow">${Math.round(s * 100)}%</span>${chip(b)}</div></div>`).join('')}</div>`;
  wire(el);
}

/* TIME · a thread per district, a bead per page on the day it was born, its tail to its last change */
function time() {
  const el = $('#v-time'), days = A.days.map(d => d.date), d0 = new Date(days[0] + 'T00:00'), nd = Math.round((new Date(days.at(-1) + 'T00:00') - d0) / 864e5) + 1;
  const W = Math.max(900, el.clientWidth - 20), L = 230, R = 24, cw = (W - L - R) / nd, X = d => L + (Math.round((new Date(d + 'T00:00') - d0) / 864e5) + .5) * cw;
  const vis = P.filter(p => visible(p) && p.born), rowsD = A.subjects.map(s => ({ s, ps: vis.filter(p => p.subject === s.id).sort((a, b) => a.born.localeCompare(b.born)) })).filter(x => x.ps.length);
  let y = 40, out = '';
  rowsD.forEach(({ s, ps }) => {
    const lanes = []; ps.forEach(p => { const x0 = X(p.born) - 9, x1 = X(p.last || p.born) + 9; let k = lanes.findIndex(e => e < x0); if (k < 0) { k = lanes.length; lanes.push(0); } lanes[k] = x1; p._lane = k; });
    const h = Math.max(34, lanes.length * 19 + 14);
    out += `<text x="${L - 16}" y="${y + h / 2 + 5}" text-anchor="end" font-size="14" fill="${s.color}" font-family="Fraunces, serif" font-weight="600">${esc(s.name)}</text><line x1="${L}" x2="${W - R}" y1="${y + h + 3}" y2="${y + h + 3}" stroke="#1d1b17"/>`;
    ps.forEach(p => { const py = y + 14 + p._lane * 19, r = Math.min(8, 3.5 + Math.sqrt(p.commits)), c = colourOf(p);
      out += `<g data-p="${esc(p.path)}" style="cursor:pointer"><line x1="${X(p.born)}" x2="${X(p.last || p.born)}" y1="${py}" y2="${py}" stroke="${c}" stroke-width="3" opacity=".55"/><circle cx="${X(p.born)}" cy="${py}" r="${r}" fill="${c}" stroke="${sel === p.path ? '#e0483a' : '#0b0a09'}" stroke-width="${sel === p.path ? 3 : 1}"/></g>`; });
    y += h + 8;
  });
  const mx = Math.max(...A.days.map(d => d.commits.length)), hb = 70, yb = y + 26;
  let ax = A.days.map(d => `<rect x="${X(d.date) - cw / 2 + 1}" y="${yb + hb - d.commits.length / mx * hb}" width="${Math.max(2, cw - 2)}" height="${d.commits.length / mx * hb}" fill="#f2c14e" opacity=".85"><title>${fmtDay(d.date)}: ${d.commits.length} commits</title></rect>`).join('');
  for (let i = 0; i < nd; i++) { const dt = new Date(d0.getTime() + i * 864e5), ds = dt.toISOString().slice(0, 10); if (i % 2 === 0) ax += `<text x="${X(ds)}" y="${yb + hb + 18}" text-anchor="middle" font-size="12" fill="#b3ab9e">${dt.getDate()} ${dt.toLocaleString('en-GB', { month: 'short' })}</text>`; }
  el.innerHTML = `<svg width="${W}" height="${yb + hb + 40}" style="display:block;margin:0 10px"><text x="${L}" y="22" font-size="12" fill="#7b7468" letter-spacing="1.2">A BEAD IS A PAGE ON THE DAY IT WAS BORN · ITS TAIL RUNS TO ITS LAST CHANGE · BIGGER BEADS, MORE COMMITS</text>${out}${ax}<text x="${L - 16}" y="${yb + hb - 4}" text-anchor="end" font-size="12" fill="#b3ab9e">commits each day</text></svg>`;
  wire(el);
}

/* LIST */
let sort = { k: 'hours', d: -1 };
function list() {
  const cols = [['title', 'Page'], ['kind', 'Type'], ['subject', 'Serves'], ['lines', 'Lines'], ['hours', 'Hours'], ['commits', 'Commits'], ['rank', 'Importance #'], ['descendants', 'Descendants'], ['born', 'Born'], ['status', 'Reach']];
  const vv = (p, k) => k === 'kind' ? KIND[p.kind][0] : k === 'subject' ? subOf[p.subject].name : p[k] ?? 0;
  const rows = P.filter(visible).sort((a, b) => { const x = vv(a, sort.k), y = vv(b, sort.k); return (x > y ? 1 : x < y ? -1 : 0) * sort.d; });
  $('#v-list').innerHTML = `<table><thead><tr>${cols.map(([k, t]) => `<th data-k="${k}">${t}${sort.k === k ? (sort.d > 0 ? ' ↑' : ' ↓') : ''}</th>`).join('')}</tr></thead><tbody>${rows.map(p => `<tr data-p="${esc(p.path)}" data-tip="no" class="${sel === p.path ? 'sel' : ''}">
    <td class="t"><span style="display:inline-flex;gap:8px;align-items:center"><span class="sw" style="--c:${colourOf(p)}"></span>${p.ia ? '<span style="color:#f2c14e">⚑</span>' : ''}${esc(p.title)}</span><small>${esc(p.path)}</small></td><td>${esc(KIND[p.kind][0])}</td><td>${esc(subOf[p.subject].name)}</td>
    <td class="n">${p.lines.toLocaleString()}</td><td class="n">${p.hours.toFixed(1)}</td><td class="n">${p.commits}</td><td class="n">${p.rank}</td><td class="n">${p.descendants || ''}</td><td class="n">${fmtDay(p.born)}</td><td><span class="pill" style="--c:${STATUS[p.status][1]}">${p.status}</span></td></tr>`).join('')}</tbody></table>`;
  $('#v-list').querySelectorAll('th').forEach(th => th.onclick = () => { sort = { k: th.dataset.k, d: sort.k === th.dataset.k ? -sort.d : (['title', 'kind', 'subject', 'born', 'rank'].includes(th.dataset.k) ? 1 : -1) }; list(); });
  wire($('#v-list'));
}

/* DIG · what is wrong with the architecture, and what to do */
function dig() {
  const row = (p, why) => `<button data-p="${esc(p.path)}" data-tip="no"><span class="sw" style="--c:${colourOf(p)}"></span><span>${esc(p.title)}</span><em>${esc(why)}</em></button>`;
  const mis = P.filter(p => p.ia), lost = P.filter(p => p.status === 'orphan' || p.status === 'hidden'), ptr = P.filter(p => p.status === 'pointer'), deep = P.filter(p => p.depth >= 4).sort((a, b) => b.depth - a.depth);
  const copies = []; P.forEach(p => p.versions.forEach(([o, s]) => { if (p.path < o && s >= .9) copies.push([p, byPath[o], s]); }));
  const byS = A.subjects.map(s => ({ s, ps: P.filter(p => p.subject === s.id) })).filter(x => x.ps.length);
  const scatter = byS.map(({ s, ps }) => ({ s, ps, fams: [...new Set(ps.map(p => p.family))] })).filter(x => x.fams.length > 2 && x.s.id !== 'lab').sort((a, b) => b.fams.length - a.fams.length);
  $('#v-dig').innerHTML = `<div class="dig"><h2>What to fix</h2>
    <p>${P.length} pages, ${P.reduce((s, p) => s + p.lines, 0).toLocaleString()} lines of page code, about ${Math.round(A.hoursTotal)} hours of attention by the commit clock, ${A.totals.commits} commits in ${A.days.length} days. The city has one gate, the lab’s front door; ${P.filter(p => p.status === 'reachable').length} buildings are on a road from it.</p>
    <h3>Scattered works: what a page is for is not where it is filed</h3><p>Each of these works is spread across several families of file names, so no one place holds it. Give each work one district: one index page that links all of its pages. Click one to see it on the map, coloured by where its pages are filed.</p>
    <div class="prob">${scatter.map(({ s, ps, fams }) => `<button data-sub="${s.id}"><span class="sw" style="--c:${s.color}"></span><span>${esc(s.name)}</span><em>${ps.length} pages filed under ${fams.length} names: ${fams.map(f => famOf[f].name).join(', ')}</em></button>`).join('')}</div>
    <h3>Misfiled: ${mis.length} pages named for one thing and made for another</h3><div class="prob">${mis.map(p => row(p, p.ia)).join('')}</div>
    <h3>Copies: ${copies.length} pairs that are the same page twice</h3><div class="prob">${copies.map(([a, b, s]) => row(a, `${Math.round(s * 100)}% the same as ${b.title} (${b.path})`)).join('')}</div>
    <h3>Lost: ${lost.length} buildings with no road from the gate</h3><div class="prob">${lost.map(p => row(p, `${STATUS[p.status][0]} · ${p.lines.toLocaleString()} lines${p.dataLines > 200 ? ` (+${p.dataLines.toLocaleString()} pasted in)` : ''} · ~${p.hours.toFixed(1)} h of work`)).join('')}</div>
    <h3>Signposts: ${ptr.length} pages that only send you elsewhere</h3><div class="prob">${ptr.map(p => row(p, p.desc.slice(0, 110))).join('')}</div>
    <h3>Far: ${deep.length} pages four or more clicks from the gate</h3><div class="prob">${deep.map(p => row(p, `${p.depth} clicks: ${p.route.map(r => byPath[r]?.title || r).join(' → ')}`)).join('')}</div></div>`;
  wire($('#v-dig'));
  $('#v-dig').querySelectorAll('[data-sub]').forEach(b => b.onclick = () => { ST.colour = 'family'; ST.district = 'subject'; ST.show = 'all'; ST.off.clear(); q = ''; $('#q').value = ''; setView('city'); });
}

/* DOT · one page in full */
function select(p) { sel = p; if (p) history.replaceState(null, '', '#' + encodeURIComponent(p)); else history.replaceState(null, '', location.pathname); hideTip(); dot(); draw(); }
function dot() {
  const el = $('#dot');
  if (!sel) {
    el.innerHTML = `<svg width="60" height="86" viewBox="-30 0 60 86" style="display:block;margin:0 auto"><line x1="0" y1="0" x2="0" y2="46" stroke="#e0483a" stroke-width="2.4"/><circle cy="62" r="15" fill="#0b0a09" stroke="#ece6da" stroke-width="3.4"/><circle cx="5" cy="64" r="3.8" fill="#ece6da"/></svg>
    <div class="empty"><h2 style="font-size:25px;margin:6px 0 10px">Read the city</h2>Each <b>district</b> is a work the pages serve. Each <b>building</b> is a page: its footprint is what you size by, its colour what you colour by, its height its commits. <b>Roads</b> run from the <b>gate</b>, the lab’s front door, along the clicks a visitor makes; the thicker the road, the more pages lie beyond it. A <b>dashed</b> building has no road. A <b>gold corner</b> means the page is filed under the wrong name. A small <b>ring</b> means it is a version of another page.<br><br>Click any building, or any row of the Ledger.</div>`;
    return;
  }
  const p = byPath[sel], all = k => Math.max(...P.map(x => x[k] || 0)), chip = x => byPath[x] ? `<button class="chip" data-p="${esc(x)}" data-tip="no"><i style="--c:${colourOf(byPath[x])}"></i><span>${esc(byPath[x].title)}</span></button>` : '';
  const meter = (label, v, mx, txt) => `<span>${label}</span><div class="bar"><i style="width:${Math.max(1, v / mx * 100)}%"></i></div><b>${txt}</b>`;
  const subs = Object.entries(p.subjects || {});
  const AP = window.ATLAS && ATLAS.by && ATLAS.by[p.path];
  el.innerHTML = `${AP && ATLAS.frames(AP).length ? `<img class="flip" ${ATLAS.flipAttr(AP)} alt="">${AP.tags.length ? `<div class="hint" style="margin-top:6px">looks like ${esc(AP.tags.join(' · '))}</div>` : ''}` : ''}<div style="height:14px"></div><span class="pill" style="--c:${colourOf(p)}">${esc(groups().find(g => g[0] === groupOf(p))?.[1] || '')}</span>
    <h2>${esc(p.title)}</h2><div class="path">${esc(p.path)}</div>
    <a class="btn" href="${esc(href(p.path))}" target="_blank" rel="noopener">Open the page ↗</a>
    ${p.ia ? `<div class="warn">⚑ ${esc(p.ia)}.</div>` : ''}${p.status !== 'reachable' ? `<div class="warn" style="border-color:#ff8f6e">${esc(STATUS[p.status][0])}.</div>` : ''}
    <p class="desc">${esc(p.desc)}</p>${p.dataLines > 200 ? `<div class="route">Besides its own ${p.lines.toLocaleString()} lines it carries ${p.dataLines.toLocaleString()} lines pasted in: data and whole libraries (${p.kb.toLocaleString()} KB on disk).</div>` : ''}
    <div class="meters">${meter('Code', p.lines, all('lines'), p.lines.toLocaleString())}${meter('Hours', p.hours, all('hours'), '~' + p.hours.toFixed(1))}${meter('Commits', p.commits, all('commits'), p.commits)}${meter('Days worked', p.days, all('days'), p.days)}
      ${meter('Importance', P.length - p.rank + 1, P.length, '#' + p.rank)}${meter('Traffic', p.traffic, Math.max(1, all('traffic')), p.traffic)}${meter('Descendants', p.descendants, Math.max(1, all('descendants')), p.descendants)}</div>
    <div class="route" style="margin-bottom:6px">${esc(KIND[p.kind][0])} · serves <b style="color:var(--ink)">${esc(subOf[p.subject].name)}</b>${subs.length ? ' (' + subs.map(([k, n]) => `${esc(subOf[k]?.name || k)} ${Math.round(n)}`).join(', ') + ')' : ''} · filed as ${esc(famOf[p.family].name)}<br>born ${fmtDay(p.born)} · last changed ${fmtDay(p.last)}${p.pipeHours ? ` · its data took ~${p.pipeHours.toFixed(1)} h of scripts` : ''}</div>
    <div class="sh">The road from the gate</div><div class="route">${p.route.length ? [...p.route, p.path].map(x => x === p.path ? `<b style="color:var(--ink)">${esc(p.title)}</b>` : `<button data-p="${esc(x)}" data-tip="no">${esc(byPath[x]?.title || x)}</button>`).join(' → ') : 'No road. Nothing in the lab leads here.'}</div>
    ${p.parent ? `<div class="sh">Descends from</div><div class="chips">${chip(p.parent)}<small class="route">kept ${Math.round(p.parentSim * 100)}% of its code</small></div>` : ''}
    ${p.children.length ? `<div class="sh">Its descendants · ${p.descendants}</div><div class="chips">${p.children.map(chip).join('')}</div>` : ''}
    ${p.versions.length ? `<div class="sh">Shares code with</div><div class="chips">${p.versions.map(([o, s]) => chip(o).replace('</span></button>', `</span><small>${Math.round(s * 100)}%</small></button>`)).join('')}</div>` : ''}
    ${p.embeds.length ? `<div class="sh">Shows inside a frame</div><div class="chips">${p.embeds.map(chip).join('')}</div>` : ''}${p.embeddedBy.length ? `<div class="sh">Shown inside</div><div class="chips">${p.embeddedBy.map(chip).join('')}</div>` : ''}
    <div class="sh">Links out · ${p.out.length}${p.menu ? ' (with the films menu)' : ''}</div><div class="chips">${p.out.slice(0, 40).map(chip).join('') || '<span class="empty">none</span>'}</div>
    <div class="sh">Linked from · ${p.in.length}</div><div class="chips">${p.in.map(chip).join('') || '<span class="empty">nothing</span>'}</div>
    ${p.madeBy.length ? `<div class="sh">Its data is made by</div><div class="route">${p.madeBy.map(esc).join('<br>')}</div>` : ''}`;
  wire(el); el.scrollTop = 0;
}


/* LEDGER · after Tufte. Every page on one sheet, one row each, all on shared scales: a sparkline of its commits day by day, a bar of
   the code written for it, its hours, commits, importance and links in, and a note in the margin when something is wrong. Works are
   sections, read like a core sample: oldest layer first. Colour is kept for nothing; the ink is the data. */
let LSORT = 'born';
function spark(daily, w, h, mx, opt = {}) {
  const n = daily.length, bw = w / n; let s = `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><line x1="0" y1="${h - .5}" x2="${w}" y2="${h - .5}" stroke="#ccc" stroke-width="1"/>`;
  const first = daily.findIndex(v => v > 0), last = n - 1 - [...daily].reverse().findIndex(v => v > 0);
  if (first >= 0 && opt.life !== false) s += `<line x1="${first * bw + bw / 2}" y1="${h - 1.5}" x2="${last * bw + bw / 2}" y2="${h - 1.5}" stroke="#bbb" stroke-width="1"/>`;
  daily.forEach((v, i) => { if (!v) return; const bh = Math.max(1.5, Math.min(h - 1, Math.sqrt(v / mx) * (h - 1))); s += `<rect x="${i * bw + .5}" y="${h - 1 - bh}" width="${Math.max(1, bw - 1)}" height="${bh}" fill="${opt.c || '#222'}"/>`; });
  if (opt.mark != null && opt.mark >= 0) s += `<circle cx="${opt.mark * bw + bw / 2}" cy="${h - 1}" r="1.8" fill="#8a3b12"/>`;
  return s + '</svg>';
}
function ledger() {
  const el = $('#v-ledger'), cal = A.calendar, vis = P.filter(visible), N = P.length;
  const cap = 4000, mxDay = Math.max(...P.map(p => Math.max(...p.daily))), allDaily = cal.map((_, i) => P.reduce((s, p) => s + p.daily[i], 0));
  const lines = P.reduce((s, p) => s + p.lines, 0), hrs = A.hoursTotal, peak = allDaily.indexOf(Math.max(...allDaily));
  const fmtD = i => fmtDay(cal[i]);
  const note = p => p.status === 'orphan' ? ['no road from the lab'] : p.status === 'hidden' ? ['reachable only through a lost page'] : p.versions[0] && p.versions[0][1] >= .9 ? [`copy of ${byPath[p.versions[0][0]]?.title || p.versions[0][0]}`]
    : p.ia ? [p.ia.replace('made for ', 'for ').replace(', but filed as', '; filed as').replace(" (a different project's name)", '')] : p.parent ? [`from ${byPath[p.parent]?.title} (${Math.round(p.parentSim * 100)}%)`, 'q'] : p.status === 'pointer' ? ['only points elsewhere', 'q'] : ['', 'q'];
  const sorter = { born: (a, b) => (a.born || '9').localeCompare(b.born || '9') || a.title.localeCompare(b.title), lines: (a, b) => b.lines - a.lines, hours: (a, b) => b.hours - a.hours, rank: (a, b) => a.rank - b.rank };
  const secs = A.subjects.map(s => ({ s, ps: vis.filter(p => p.subject === s.id).sort(sorter[LSORT]) })).filter(x => x.ps.length).sort((a, b) => b.ps.reduce((t, p) => t + p.lines, 0) - a.ps.reduce((t, p) => t + p.lines, 0));
  const row = p => { const [nt, cls] = note(p);
    return `<div class="lg row ${sel === p.path ? 'sel' : ''}" data-p="${esc(p.path)}" data-tip="no"><span class="t">${esc(p.title.replace(/ · (lab\/)?[\w/.-]+\.html$/, ''))}<small>${esc(KIND[p.kind][0].split(/[ ,]/)[0].toLowerCase())}</small></span>
      <span>${spark(p.daily, 150, 16, mxDay, { mark: cal.indexOf(p.born) })}</span>
      <span><div class="bar ${p.lines > cap ? 'big' : ''}" style="width:${Math.max(.4, Math.min(1, p.lines / cap) * 100)}%"></div></span>
      <span class="n">${p.lines.toLocaleString()}</span><span class="n">${p.hours >= .05 ? p.hours.toFixed(1) : '·'}</span><span class="n">${p.commits}</span><span class="n">${p.in.length}</span>
      <span class="note ${cls || ''}" title="${esc(nt)}">${esc(nt)}</span></div>`; };
  el.innerHTML = `<div class="ledger"><h2>The lab, page by page</h2>
    <p class="lede">Over ${cal.length} days ${spark(allDaily, 132, 16, Math.max(...allDaily), { life: false })} the lab laid down ${A.totals.commits} commits and ${N} pages: ${lines.toLocaleString()} lines of code written for it, about ${Math.round(hrs)} hours of attention by the commit clock. The busiest day was ${fmtD(peak)}, with ${allDaily[peak]}. ${P.filter(p => p.status === 'reachable').length} pages are on a road from the front door; ${P.filter(p => p.ia).length} are made for one work and filed under another.</p>
    <div class="ctl2"><span>Within each work, order by</span>${[['born', 'when it was laid down'], ['lines', 'code'], ['hours', 'hours'], ['rank', 'importance']].map(([k, t]) => `<button data-s="${k}" class="${LSORT === k ? 'on' : ''}">${t}</button>`).join('')}</div>
    <div class="lg head"><span>page, and what kind</span><span><div class="laxis"><span>${fmtD(0)}</span><span>${fmtD(cal.length - 1)}</span></div>commits each day</span><span>code written for it, to ${cap.toLocaleString()} lines</span><span>lines</span><span>hours</span><span>commits</span><span>linked from</span><span>note</span></div>
    ${secs.map(({ s, ps }) => { const d = cal.map((_, i) => ps.reduce((t, p) => t + p.daily[i], 0));
      return `<div class="lsec"><h3>${esc(s.name)}</h3><span>${spark(d, 150, 22, Math.max(...allDaily), { life: false })}</span><p>${ps.length} page${ps.length > 1 ? 's' : ''} · ${ps.reduce((t, p) => t + p.lines, 0).toLocaleString()} lines · ${ps.reduce((t, p) => t + p.hours, 0).toFixed(0)} hours · ${(n => n > 1 ? `filed under ${n} names` : 'filed under one name')(new Set(ps.map(p => p.family)).size)}</p></div>${ps.map(row).join('')}`; }).join('')}
    <p style="font-size:14.5px;color:#666;font-style:italic;margin-top:30px;max-width:80ch">Every sparkline shares one scale: a full-height mark is the busiest single day any page had (${mxDay} commits); heights follow the square root so a single commit still shows. The thin grey line under a sparkline is the page’s life from first to last change; the small dot is the day it was born. Bars share one scale up to ${cap.toLocaleString()} lines; a broken bar runs past it. Hours are estimated from the gaps between commits. Notes in the margin: lost pages, copies, misfiled pages, and the page each one descends from.</p></div>`;
  el.querySelectorAll('[data-s]').forEach(b => b.onclick = () => { LSORT = b.dataset.s; ledger(); });
  wire(el);
}
