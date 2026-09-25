/* Videotext · Sheet 02 · Open the archive (051–100).
   Every view gets the shots for what you hold, ranked (o.list), and draws them one way.
   Shared helpers live on VT.h so the other sheets can use them. */
(() => {
'use strict';
const V = window.VT;
const { esc, wire } = V;
const h = V.h = {};
const S = () => V.S;

/* ---------- helpers ---------- */
h.top = (o, n, nw) => o.list.slice(0, o.wide ? (nw || n * 2) : n);
h.q = (n = 80) => { const t = S().sel ? V.selText() : (S().q || ''); return t.length > n ? t.slice(0, n - 1) + '…' : t; };
h.hub = (cls = '', n = 70) => S().sel ? `<span class="vnode hub ${cls}" data-sel="${S().sel.a}.${S().sel.b}">${esc(h.q(n))}</span>` : `<span class="vnode hub ${cls}">${esc(h.q(n))}</span>`;
h.t = (r, o = {}) => V.thumb(r.s, { in: r.in, ...o, style: (o.w != null ? `--w:${typeof o.w === 'number' ? o.w + 'px' : o.w};` : '') + (o.style || '') });
h.ts = (s, o = {}) => V.thumb(s, { ...o, style: (o.w != null ? `--w:${typeof o.w === 'number' ? o.w + 'px' : o.w};` : '') + (o.style || '') });
h.cap = (r, why = true) => `<span class="vcap">${esc(r.s.title || '')}<small>${r.s.year || '—'}${why ? ' · ' + esc(r.why) : ''}</small></span>`;
h.fig = (r, w, o = {}) => `<div class="vcol" style="--w:${w}px;width:${w}px;align-items:stretch;gap:0">${h.t(r, { w, ...o })}${o.nocap ? '' : h.cap(r, o.why !== false)}</div>`;
h.hash = str => { let x = 2166136261; for (const c of String(str)) { x ^= c.charCodeAt(0); x = Math.imul(x, 16777619); } return (x >>> 0) / 4294967295; };
const states = {};
h.state = (id, init) => states[id] || (states[id] = init || {});
h.stage = (ratio, max) => `<div class="vstage" style="aspect-ratio:${ratio};max-width:${max || '100%'}">`;
h.at = (x, y, html, extra = '') => `<div class="vp" style="left:${x.toFixed(2)}%;top:${y.toFixed(2)}%;${extra}">${html}</div>`;
h.polar = (r, deg, cx = 50, cy = 50, ry) => { const a = deg * Math.PI / 180; return [cx + r * Math.cos(a), cy + (ry || r) * Math.sin(a)]; };
h.note = t => `<p class="vnote">${t}</p>`;
h.grade = s => (s.grade && s.grade !== 'U') ? s.grade : 'unreviewed';
h.reviewed = s => !!s.grade && s.grade !== 'U';
h.groups = (list, key, max) => V.groupBy(list, key).slice(0, max || 99);
h.tree = (box, root, opt = {}) => {
  let n = 0; const links = [];
  const rec = (node, pid) => {
    const id = 'tn' + (n++); if (pid) links.push([pid, id]);
    const kids = node.kids || [];
    const leaf = kids.length && kids.every(k => !(k.kids && k.kids.length));
    return `<div class="vtn"><div class="vtl" data-tn="${id}">${node.html}</div>${kids.length ? `<div class="vtk${leaf ? ' leaf' : ''}"${leaf && opt.leafMax ? ` style="max-width:${opt.leafMax}px"` : ''}>${kids.map(k => rec(k, id)).join('')}</div>` : ''}</div>`;
  };
  box.insertAdjacentHTML('beforeend', `<div class="vtree${opt.wrap ? ' wrap' : ''}">${rec(root)}</div>`);
  const q = id => box.querySelector(`[data-tn="${id}"]`);
  wire(box, links.map(([a, b]) => [q(a), q(b), { color: opt.color, dash: opt.dash }]));
};
const tmap = {};
h.shotTime = s => {
  if (!tmap.built) {
    tmap.built = true;
    Object.values(V.D.cuts).forEach(l => l.forEach(p => { if (tmap[p.id] == null) tmap[p.id] = p.t0; }));
    V.D.beats.forEach(b => [...(b.candidates || []), ...(b.forage || [])].forEach(c => { if (tmap[c.id] == null) tmap[c.id] = b.start; }));
  }
  return tmap[s.id];
};
h.tokens = s => s._tok || (s._tok = new Set((s.text || '').split(/[^a-z']+/).filter(w => w.length > 3 && !/^(shot|film|clip|frame|with|from|that|this|into|their|there|which|while|about|visible|useful)$/.test(w))));
h.jac = (A, B) => { let i = 0; for (const x of A) if (B.has(x)) i++; return i / (A.size + B.size - i || 1); };
h.focus = o => { const pv = S().pv; if (pv) return V.shot(pv.id) || pv; return o.list[0] && o.list[0].s; };
h.stems = terms => terms.map(t => t.length > 5 ? t.slice(0, t.length - 2) : t);
h.srcName = r => V.source(r);
h.ranges = () => ({ line: V.around('line'), stanza: V.around('stanza'), passage: V.around('passage') });
h.lineThumb = (r, a, b, o = {}) => h.t(r, { ...o, style: (o.style || '') }).replace('<button class="vx', `<button data-line="${a}.${b}" class="vx`);
h.arrows = (box, pairs, o = {}) => wire(box, pairs.map(([a, b]) => [a, b, { arrow: true, color: o.color || 'var(--dim)', mode: o.mode || 'v', dash: o.dash }]));
h.vbtns = (items, cur, attr) => items.map(([k, label]) => `<button class="vbtn${String(k) === String(cur) ? ' on' : ''}" data-${attr}="${esc(k)}">${label}</button>`).join('');

const R = (id, name, desc, render, extra = {}) => V.register({ id, sheet: '02', name, desc, render, ...extra });

/* ---------- 051–055 trees ---------- */
R('051', 'Branch Tree', 'What you hold branches into where each shot came from: a cut, a beat, a word match.', (box, v, o) => {
  const g = h.groups(o.list, h.srcName, o.wide ? 5 : 3), n = o.wide ? 5 : 2, w = o.wide ? 92 : 56;
  h.tree(box, { html: h.hub(), kids: g.map(([k, l]) => ({ html: `<span class="vnode">${esc(k)}<small>${l.length}</small></span>`, kids: l.slice(0, n).map(r => ({ html: h.t(r, { w }) })) })) }, { wrap: !o.wide, leafMax: (w + 6) * n });
});
R('052', 'Split Branch', 'Two branches: shots found at this moment of the poem, and shots found by its words; each splits into reviewed and unreviewed.', (box, v, o) => {
  const atTime = o.list.filter(r => !/^matches/.test(r.why)), byWord = o.list.filter(r => /^matches/.test(r.why));
  const n = o.wide ? 3 : 1, w = o.wide ? 76 : 50;
  const split = l => [['reviewed', l.filter(r => h.reviewed(r.s))], ['unreviewed', l.filter(r => !h.reviewed(r.s))]].filter(x => x[1].length)
    .map(([k, l2]) => ({ html: `<span class="vnode dim">${k}<small>${l2.length}</small></span>`, kids: l2.slice(0, n).map(r => ({ html: h.t(r, { w }) })) }));
  h.tree(box, { html: h.hub(), kids: [['at this moment', atTime], ['in the words', byWord]].filter(x => x[1].length).map(([k, l]) => ({ html: `<span class="vnode sel">${k}<small>${l.length}</small></span>`, kids: split(l) })) }, { leafMax: (w + 6) * 2, wrap: !o.wide });
});
R('053', 'Deep Tree', 'Three levels down: source, then decade, then the shots.', (box, v, o) => {
  const w = o.wide ? 70 : 44;
  const kids = h.groups(o.list, h.srcName, o.wide ? 4 : 2).map(([k, l]) => ({ html: `<span class="vnode">${esc(k)}</span>`,
    kids: h.groups(l, r => V.decade(r.s), 2).map(([d, l2]) => ({ html: `<span class="vnode dim">${d}</span>`, kids: l2.slice(0, o.wide ? 2 : 1).map(r => ({ html: h.t(r, { w }) })) })) }));
  h.tree(box, { html: h.hub('', 50), kids });
});
R('054', 'Balanced Tree', 'The top eight shots as a bracket: halves, quarters, pairs.', (box, v, o) => {
  const l = o.list.slice(0, 8), w = o.wide ? 96 : 38;
  const build = (a, b) => b - a === 1 ? { html: h.t(l[a], { w, label: o.wide ? '#' + (a + 1) : '' }) } : { html: `<span class="vnode dim">${a + 1}–${Math.min(b, l.length)}</span>`, kids: [build(a, (a + b) / 2), build((a + b) / 2, b)].filter(k => k.html.indexOf('undefined') < 0) };
  if (l.length < 8) { l.forEach(r => box.insertAdjacentHTML('beforeend', h.t(r, { w: 60 }))); return; }
  h.tree(box, { html: h.hub('', 50), kids: [build(0, 4), build(4, 8)] });
});
R('055', 'Radial Tree', 'The same branches, drawn around what you hold.', (box, v, o) => {
  const g = h.groups(o.list, h.srcName, 5), per = o.wide ? 5 : 3, w = o.wide ? 70 : 38;
  let html = h.stage('1', o.wide ? '720px' : '100%') + h.at(50, 50, h.hub('', 40));
  const links = [];
  g.forEach(([k, l], i) => {
    const ang = -90 + i * 360 / g.length; const [x, y] = h.polar(20, ang);
    html += h.at(x, y, `<span class="vnode" data-g="${i}">${esc(k)}</span>`);
    l.slice(0, per).forEach((r, j) => { const a2 = ang + (j - (per - 1) / 2) * (300 / g.length / per); const [x2, y2] = h.polar(41, a2); html += h.at(x2, y2, h.t(r, { w }), `z-index:1" data-leaf="${i}`); });
  });
  box.innerHTML = html + '</div>';
  const st = box.querySelector('.vstage'), hub = st.querySelector('.hub');
  g.forEach((x, i) => { const gn = st.querySelector(`[data-g="${i}"]`); links.push([hub, gn, { mode: 'c' }]); st.querySelectorAll(`[data-leaf="${i}"] .vx`).forEach(t => links.push([gn, t, { mode: 'c', dash: true }])); });
  wire(box, links);
});

/* ---------- 056–060 radial and scattered ---------- */
R('056', 'Radial Fan', 'The best shots fanned from what you hold, the strongest on top.', (box, v, o) => {
  const l = h.top(o, 6, 9), w = o.wide ? 120 : 64;
  let html = h.stage('1.25', o.wide ? '760px' : '100%') + h.at(16, 86, h.hub('', 40));
  l.forEach((r, i) => { const ang = -88 + i * 84 / Math.max(1, l.length - 1); const [x, y] = h.polar(68, ang, 14, 88, 78); html += h.at(x, y, h.t(r, { w }), `transform:translate(-50%,-50%) rotate(${ang + 90}deg);z-index:${20 - i}`); });
  box.innerHTML = html + '</div>';
  const vx = box.querySelectorAll('.vx');
  h.arrows(box, vx.length > 1 ? [[vx[vx.length - 1], vx[0]]] : [], { mode: 'arc', color: 'var(--blue)' });
});
R('057', 'Circular Ring', 'A ring of shots around the words; the best at twelve o’clock.', (box, v, o) => {
  const l = h.top(o, 10, 16), w = o.wide ? 92 : 48;
  let html = h.stage('1', o.wide ? '720px' : '100%') + h.at(50, 50, h.hub('', 60));
  l.forEach((r, i) => { const [x, y] = h.polar(40, -90 + i * 360 / l.length); html += h.at(x, y, h.t(r, { w, label: String(i + 1) })); });
  box.innerHTML = html + '</div>';
  const hub = box.querySelector('.hub');
  wire(box, [...box.querySelectorAll('.vx')].map((t, i) => [hub, t, { mode: 'c', color: i ? 'var(--faint)' : 'var(--blue)', w: i ? 1 : 2, dash: i ? '2 3' : '' }]));
});
R('058', 'Spiral', 'The best shot at the centre; the list winds outward, each shot a little smaller.', (box, v, o) => {
  const l = h.top(o, 14, 30), W = o.wide ? 120 : 64;
  let html = h.stage('1', o.wide ? '760px' : '100%');
  l.forEach((r, i) => { const t = i / l.length; const ang = i * 0.62 * Math.PI * (o.wide ? 0.92 : 1); const rad = 6 + t * 40; const x = 50 + rad * Math.cos(ang), y = 50 + rad * Math.sin(ang); html += h.at(x, y, h.t(r, { w: Math.round(W * (1 - t * 0.62)) }), `z-index:${100 - i}`); });
  box.innerHTML = html + '</div>';
  const t = [...box.querySelectorAll('.vx')];
  wire(box, t.slice(1).map((x, i) => [t[i], x, { mode: 'c', color: 'var(--blue-mid)', w: 1.5 }]));
});
R('059', 'Constellation', 'Shots by year (across) and rank (the best at the top); shots of the same decade are joined.', (box, v, o) => {
  const l = h.top(o, 24, 60); const ys = l.map(r => r.s.year).filter(Boolean); const y0 = Math.min(...ys, 1900), y1 = Math.max(...ys, 1960);
  const sc = l.map(r => r.score), s0 = Math.min(...sc), s1 = Math.max(...sc) || 1, w = o.wide ? 56 : 32;
  let html = h.stage('1.6', '100%');
  l.forEach((r, i) => { const x = r.s.year ? 6 + 82 * (r.s.year - y0) / Math.max(1, y1 - y0) : 95; const y = 10 + 80 * i / Math.max(1, l.length - 1) + (h.hash(r.s.id) - 0.5) * 6; html += h.at(x, Math.max(6, Math.min(92, y)), h.t(r, { w, grade: false }), `z-index:${100 - i}" data-dec="${V.decade(r.s)}" data-x="${x}`); });
  [y0, Math.round((y0 + y1) / 2), y1].forEach((y, k) => html += `<span class="vaxis" style="left:${6 + 41 * k}%;bottom:-16px">${y}</span>`);
  html += `<span class="vaxis" style="right:0;bottom:-16px">undated</span><span class="vaxis" style="left:0;top:0">best ↑</span>`;
  box.innerHTML = html + '</div>';
  const links = [];
  h.groups([...box.querySelectorAll('.vp')], e => e.dataset.dec).forEach(([, es]) => { es.sort((a, b) => a.dataset.x - b.dataset.x); for (let i = 1; i < es.length; i++) links.push([es[i - 1].firstElementChild, es[i].firstElementChild, { mode: 'c', dash: '2 3' }]); });
  wire(box, links);
});
R('060', 'Cluster Map', 'Shots clustered by decade, each cluster a dashed island around what you hold.', (box, v, o) => {
  const g = h.groups(o.list.slice(0, 80), r => V.decade(r.s)).sort((a, b) => a[0].localeCompare(b[0])).slice(0, o.wide ? 8 : 6), per = o.wide ? 6 : 4, w = o.wide ? 62 : 40;
  const cl = g.map(([k, l]) => `<div class="vframe dash" data-cl style="border-radius:40px;padding:12px 14px;text-align:center"><div class="vlab">${k} · ${l.length}</div><div class="vrow" style="justify-content:center;max-width:${(w + 8) * 3}px">${l.slice(0, per).map(r => h.t(r, { w })).join('')}</div></div>`);
  cl.splice(Math.floor(cl.length / 2), 0, `<div style="align-self:center">${h.hub('', 60)}</div>`);
  box.innerHTML = `<div class="vrow" style="justify-content:center;gap:22px;align-items:center">${cl.join('')}</div>`;
  const hub = box.querySelector('.hub');
  wire(box, [...box.querySelectorAll('[data-cl]')].map(c => [hub, c, { mode: 'c', dash: true }]));
});

/* ---------- 061–065 drawers, tabs, cards ---------- */
R('061', 'Cascading Drawers', 'One drawer per source, cascading; open one to slide out its shots.', (box, v, o) => {
  const st = h.state('061', { open: {} }); const g = h.groups(o.list, h.srcName), w = o.wide ? 96 : 60;
  box.innerHTML = g.map(([k, l], i) => `<details data-k="${esc(k)}" ${st.open[k] ?? i < 2 ? 'open' : ''} style="margin-left:${i * (o.wide ? 26 : 10)}px;border:1.5px solid var(--rule);border-radius:3px;margin-bottom:6px;background:var(--panel)"><summary style="padding:6px 10px;cursor:pointer;font:700 12px var(--sans);text-transform:uppercase;letter-spacing:.05em">${esc(k)} <small style="color:var(--dim);font-weight:400">${l.length}</small></summary><div class="vrow nw" style="padding:4px 10px 10px">${l.slice(0, 30).map(r => h.t(r, { w })).join('')}</div></details>`).join('');
  box.querySelectorAll('details').forEach(d => d.addEventListener('toggle', () => { st.open[d.dataset.k] = d.open; }));
});
R('062', 'Accordion', 'The decades as an accordion: open one and the others close.', (box, v, o) => {
  const st = h.state('062', {}); const g = h.groups(o.list, r => V.decade(r.s)).sort((a, b) => a[0].localeCompare(b[0])); const w = o.wide ? 120 : 76;
  if (!st.open || !g.some(x => x[0] === st.open)) st.open = g[0] && g[0][0];
  box.innerHTML = g.map(([k, l]) => `<div style="border:1.5px solid var(--rule);border-radius:3px;margin-bottom:4px;background:var(--panel)"><button class="vbtn" data-acc="${k}" style="width:100%;text-align:left;border:0;padding:7px 10px;display:flex;gap:8px"><b>${k === st.open ? '▾' : '▸'} ${k}</b><span style="color:var(--dim)">${l.length} shots</span><span style="flex:1"></span>${l.slice(0, 5).map(r => `<i style="width:22px;height:16px;background:url('${esc(r.s.thumb)}') center/cover;border:1px solid var(--rule)"></i>`).join('')}</button>${k === st.open ? `<div class="vrow" style="padding:4px 10px 10px">${l.slice(0, 24).map(r => h.fig(r, w)).join('')}</div>` : ''}</div>`).join('');
  box.querySelectorAll('[data-acc]').forEach(b => b.onclick = () => { st.open = st.open === b.dataset.acc ? null : b.dataset.acc; V.rerender(); });
});
R('063', 'Tabs', 'A tab for each source; one set of shots at a time.', (box, v, o) => {
  const st = h.state('063', {}); const g = h.groups(o.list, h.srcName); if (!g.some(x => x[0] === st.tab)) st.tab = g[0][0];
  const cur = g.find(x => x[0] === st.tab)[1], w = o.wide ? 130 : 88;
  box.innerHTML = `<div class="vrow" style="gap:0;border-bottom:1.5px solid var(--ink);margin-bottom:12px">${g.map(([k, l]) => `<button data-tab="${esc(k)}" style="font:inherit;font-size:12px;border:1.5px solid ${k === st.tab ? 'var(--ink)' : 'transparent'};border-bottom:0;background:${k === st.tab ? 'var(--panel)' : 'none'};color:${k === st.tab ? 'var(--blue)' : 'var(--dim)'};padding:6px 10px;margin-bottom:-1.5px;border-radius:4px 4px 0 0;cursor:pointer">${esc(k)} <small>${l.length}</small></button>`).join('')}</div><div class="vrow">${cur.slice(0, o.wide ? 40 : 18).map(r => h.fig(r, w)).join('')}</div>`;
  box.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => { st.tab = b.dataset.tab; V.rerender(); });
});
R('064', 'Stacked Cards', 'The shots as a deck: the top card open, the rest stacked behind; turn to the next.', (box, v, o) => {
  const st = h.state('064', { i: 0 }); const l = o.list.slice(0, 24); st.i = Math.min(st.i, l.length - 1);
  const deck = [0, 1, 2, 3, 4].map(k => l[(st.i + k) % l.length]).filter(Boolean);
  const W = o.wide ? 460 : 260; const r = deck[0];
  box.innerHTML = `<div style="position:relative;width:${W + 40}px;max-width:100%;height:${Math.round(W * 0.75) + 150}px;margin:0 auto">${deck.slice().reverse().map((x, k) => { const d = deck.length - 1 - k; return `<div style="position:absolute;left:${d * 8}px;top:${d * 8}px;width:${W}px;max-width:calc(100% - 40px);background:var(--panel);border:1.5px solid var(--ink);border-radius:4px;padding:8px;transform:rotate(${d ? (h.hash(x.s.id) - 0.5) * 5 : 0}deg);opacity:${1 - d * 0.12}">${h.t(x, { w: '100%' })}${d ? '' : `<div style="margin-top:6px"><b style="font:700 15px/1.2 var(--sans)">${esc(x.s.title)}</b><div class="vnote" style="margin:2px 0">${x.s.year || ''} · ${esc(x.why)}</div><div style="font-size:12px">${esc(x.s.observed && !/^Unreviewed/.test(x.s.observed) ? x.s.observed : '')}</div></div>`}</div>`; }).join('')}</div>
  <div class="vbar" style="justify-content:center"><button class="vbtn" data-d="-1">‹ back</button><span class="vnote" style="margin:0">${st.i + 1} / ${l.length}</span><button class="vbtn" data-d="1">next ›</button><button class="vbtn on" data-cpl>couple this card</button></div>`;
  box.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { st.i = (st.i + +b.dataset.d + l.length) % l.length; V.rerender(); });
  box.querySelector('[data-cpl]').onclick = () => { V.preview(r.s, r.in); V.couple(); };
});
R('065', 'Carousel', 'One shot in front, its neighbours turned away on either side.', (box, v, o) => {
  const st = h.state('065', { i: 0 }); const l = o.list.slice(0, 30); st.i = Math.min(st.i, l.length - 1);
  const side = o.wide ? 3 : 1, W = o.wide ? 320 : 170;
  let html = `<div class="v3d" style="display:flex;justify-content:center;align-items:center;height:${Math.round(W * 0.75) + 40}px;gap:0;overflow:hidden">`;
  for (let d = -side; d <= side; d++) { const r = l[(st.i + d + l.length * 3) % l.length]; if (!r || (l.length <= 2 * side && Math.abs(d) > (l.length - 1) / 2)) continue; const sc = 1 - Math.abs(d) * 0.22; html += `<div data-go="${d}" style="transform:rotateY(${-d * 38}deg) scale(${sc});margin:0 ${d ? -W * 0.18 : 6}px;z-index:${10 - Math.abs(d)};opacity:${1 - Math.abs(d) * 0.18}">${h.t(r, { w: W })}</div>`; }
  html += `</div><div class="vbar" style="justify-content:center"><button class="vbtn" data-d="-1">‹</button><span class="vnote" style="margin:0">${esc(l[st.i].s.title)} · ${l[st.i].s.year || ''} (${st.i + 1}/${l.length})</span><button class="vbtn" data-d="1">›</button></div>`;
  box.innerHTML = html;
  box.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { st.i = (st.i + +b.dataset.d + l.length) % l.length; V.rerender(); });
  box.querySelectorAll('[data-go]').forEach(b => { if (+b.dataset.go) b.addEventListener('click', () => { st.i = (st.i + +b.dataset.go + l.length) % l.length; setTimeout(V.rerender, 0); }); });
});

/* ---------- 066–070 strips and lenses ---------- */
R('066', 'Sliding Window', 'A window of four slides along the whole list; what it frames is shown large.', (box, v, o) => {
  const st = h.state('066', { i: 0 }); const l = o.list.slice(0, 60), n = o.wide ? 5 : 3; st.i = Math.max(0, Math.min(st.i, l.length - n));
  const W = o.wide ? 190 : 94, tw = o.wide ? 40 : 26;
  box.innerHTML = `<div class="vrow" style="justify-content:center;margin-bottom:14px">${l.slice(st.i, st.i + n).map(r => h.fig(r, W)).join('')}</div>
  <div style="display:flex;align-items:center;gap:6px"><button class="vbtn" data-d="-1">←</button><div class="vrow nw" style="gap:2px;flex:1;position:relative" data-strip>${l.map((r, i) => `<span data-j="${i}" style="flex:none;outline:${i >= st.i && i < st.i + n ? '2px solid var(--blue)' : 'none'};outline-offset:-1px">${h.t(r, { w: tw, grade: false })}</span>`).join('')}</div><button class="vbtn" data-d="1">→</button></div>`;
  box.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { st.i = Math.max(0, Math.min(l.length - n, st.i + +b.dataset.d * n)); V.rerender(); });
  box.querySelectorAll('[data-j]').forEach(b => b.addEventListener('click', () => { st.i = Math.max(0, Math.min(l.length - n, +b.dataset.j - 1)); setTimeout(V.rerender, 0); }));
  const on = box.querySelector(`[data-j="${st.i}"]`); if (on) requestAnimationFrame(() => on.scrollIntoView({ block: 'nearest', inline: 'center' }));
});
R('067', 'Film Strip', 'The shots on a strip of film, sprockets and frame numbers.', (box, v, o) => {
  const l = h.top(o, 12, 32), w = o.wide ? 130 : 74;
  const holes = 'background:repeating-linear-gradient(90deg,transparent 0 6px,var(--paper) 6px 13px,transparent 13px 20px)';
  box.innerHTML = `<div style="background:#141414;padding:14px 8px;border-radius:3px;position:relative"><div style="position:absolute;left:0;right:0;top:3px;height:7px;${holes}"></div><div style="position:absolute;left:0;right:0;bottom:3px;height:7px;${holes}"></div><div class="vrow" style="gap:6px">${l.map((r, i) => `<div style="position:relative">${h.t(r, { w, style: 'border-color:#141414' })}<span style="position:absolute;left:3px;bottom:2px;color:#fffb;font:600 9px var(--mono);text-shadow:0 0 3px #000">${String(i + 1).padStart(2, '0')}</span></div>`).join('')}</div></div>`;
});
R('068', 'Multi-scale Strip', 'Three scales at once: the best three large, the next eight medium, the rest as a fine band.', (box, v, o) => {
  const l = o.list, W = o.wide ? [230, 110, 44] : [100, 56, 26];
  box.innerHTML = [[0, 3], [3, 11], [11, o.wide ? 71 : 41]].map(([a, b], k) => `<div class="vlab">${['best three', 'next eight', 'the rest'][k]}</div><div class="vrow" style="gap:${k === 2 ? 2 : 6}px;margin-bottom:12px">${l.slice(a, b).map(r => h.t(r, { w: W[k], grade: k < 2 })).join('')}</div>`).join('');
});
R('069', 'Timeline Lens', 'Every shot at the time in the poem where it was found; the lens magnifies the moment you hold.', (box, v, o) => {
  const D = V.D.duration, sel = S().sel; const l = o.list.slice(0, 160).map(r => ({ r, t: h.shotTime(r.s) })).filter(x => x.t != null);
  const lens0 = sel ? Math.max(0, sel.t0 - 20) : 0, lens1 = sel ? Math.min(D, sel.t1 + 20) : 60;
  const inLens = l.filter(x => x.t >= lens0 && x.t <= lens1).slice(0, o.wide ? 10 : 5);
  const rows = {}; const w = o.wide ? 26 : 18;
  let dots = '';
  l.forEach(x => { const col = Math.round(x.t / D * 60); rows[col] = (rows[col] || 0) + 1; if (rows[col] > 5) return; dots += `<div style="position:absolute;left:${(x.t / D * 100).toFixed(2)}%;bottom:${(rows[col] - 1) * (w * 0.8)}px;transform:translateX(-50%)">${h.t(x.r, { w, grade: false })}</div>`; });
  box.innerHTML = `<div class="vlab">the lens · ${V.fmt(lens0)}–${V.fmt(lens1)}</div><div class="vrow" data-lens style="justify-content:center;border:1.5px solid var(--blue);border-radius:6px;padding:10px;background:var(--blue-soft);margin-bottom:34px">${inLens.length ? inLens.map(x => h.fig(x.r, o.wide ? 120 : 70)).join('') : '<span class="vnote">No timed shots inside the lens.</span>'}</div>
  <div style="position:relative;height:${w * 4.3}px">${dots}<div data-win style="position:absolute;bottom:0;height:100%;left:${lens0 / D * 100}%;width:${Math.max(0.6, (lens1 - lens0) / D * 100)}%;background:#2463eb22;border:1.5px solid var(--blue)"></div></div>
  <div class="vruler">${[0, 5, 10, 15, 20].map(m => `<span style="left:${m * 60 / D * 100}%">${m}:00</span>`).join('')}</div>`;
  const lens = box.querySelector('[data-lens]'), win = box.querySelector('[data-win]');
  wire(box, [[lens, win, { dash: true, color: 'var(--blue)' }]]);
});
R('070', 'Zoom Levels', 'Three zooms: the fourteen passages, the stanzas of this passage, the shots for what you hold.', (box, v, o) => {
  const sel = S().sel; const fi = sel ? S().words[sel.a].film : 0; const f = S().films[fi];
  const cw = o.wide ? 64 : 34;
  const row1 = S().films.map(x => { const p = V.cutAt('suite', x.poem[0] + 1); return `<div class="vcol" data-z1="${x.i}" style="gap:2px">${p ? h.ts(V.shot(p.id) || p, { w: cw, in: p.in, grade: false, cls: x.i === fi ? 'mine' : '' }) : ''}<small style="font:500 9px var(--mono);color:${x.i === fi ? 'var(--blue)' : 'var(--dim)'}">${x.n}</small></div>`; }).join('');
  const sts = f.stanzas.map(i => S().stanzas[i]); const cur = sel ? S().words[sel.a].s : -1;
  const row2 = sts.map(st => { const p = V.cutAt('suite', st.t0 + 0.5); return `<div class="vcol" data-z2="${st.i}" style="gap:2px">${p ? h.ts(V.shot(p.id) || p, { w: o.wide ? 84 : 44, in: p.in, grade: false, cls: st.i === cur ? 'mine' : '' }) : ''}<small data-sel="${st.a}.${st.b}" style="cursor:pointer;font:500 9px var(--mono);color:${st.i === cur ? 'var(--blue)' : 'var(--dim)'}">${V.fmt0(st.t0)}</small></div>`; }).join('');
  box.innerHTML = `<div class="vlab">the poem · 14 passages</div><div class="vrow" style="gap:3px;margin-bottom:34px">${row1}</div><div class="vlab">${esc(f.n + ' ' + f.title)} · ${sts.length} stanzas</div><div class="vrow" style="gap:5px;margin-bottom:34px" data-r2>${row2}</div><div class="vlab">what you hold</div><div class="vrow" data-r3>${h.top(o, 4, 8).map(r => h.fig(r, o.wide ? 140 : 76)).join('')}</div>`;
  const a1 = box.querySelector(`[data-z1="${fi}"]`), r2 = box.querySelectorAll('[data-z2]'), a2 = box.querySelector(`[data-z2="${cur}"]`), r3 = box.querySelectorAll('[data-r3] .vx');
  wire(box, [[a1, r2[0], { dash: true, color: 'var(--blue)' }], [a1, r2[r2.length - 1], { dash: true, color: 'var(--blue)' }], [a2, r3[0], { dash: true, color: 'var(--blue)' }], [a2, r3[r3.length - 1], { dash: true, color: 'var(--blue)' }]]);
});

/* ---------- 072–075 grids ---------- */
R('072', 'Masonry Grid', 'Tall, square and wide tiles packed in columns; stronger shots get more room.', (box, v, o) => {
  const l = h.top(o, 16, 48); const cols = o.wide ? 5 : 2;
  box.innerHTML = `<div style="column-count:${cols};column-gap:8px">${l.map((r, i) => { const shape = i < 2 ? '4/3.4' : ['4/3', '1/1', '3/4', '16/9'][Math.floor(h.hash(r.s.id) * 4)]; return `<div style="break-inside:avoid;margin-bottom:8px">${h.t(r, { w: '100%', style: `aspect-ratio:${shape}` })}${h.cap(r, false)}</div>`; }).join('')}</div>`;
});
R('073', 'Focus + Context', 'The shot in view large in the middle; the rest around it as context.', (box, v, o) => {
  const f = h.focus(o); const rest = o.list.filter(r => r.s.id !== (f && f.id)).slice(0, o.wide ? 16 : 12); const fr = o.list.find(r => r.s.id === (f && f.id)) || { s: f, in: f && f.in, why: '' };
  const cols = 5; let cells = ''; let k = 0;
  for (let rr = 0; rr < 4; rr++) for (let c = 0; c < cols; c++) { if (rr >= 1 && rr <= 2 && c >= 1 && c <= 3) continue; const r = rest[k++]; cells += `<div style="grid-row:${rr + 1};grid-column:${c + 1}">${r ? h.t(r, { w: '100%', grade: false }) : ''}</div>`; }
  box.innerHTML = `<div style="display:grid;grid-template-columns:repeat(${cols},1fr);gap:6px;max-width:${o.wide ? '900px' : '100%'};margin:0 auto">${cells}<div style="grid-row:2/4;grid-column:2/5;display:flex;flex-direction:column;justify-content:center;border:2px solid var(--blue);border-radius:3px;padding:6px;background:var(--blue-soft)">${f ? h.t(fr, { w: '100%' }) : ''}<b style="font:700 13px/1.2 var(--sans);margin-top:4px">${esc(f ? f.title : '')}</b>${o.wide && f ? `<small style="color:var(--dim)">${esc(f.observed || '')}</small>` : ''}</div></div>`;
});
R('074', 'Mosaic', 'All the shots as one tiled picture; the best take the big tiles.', (box, v, o) => {
  const l = h.top(o, 30, 90);
  box.innerHTML = `<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(${o.wide ? 70 : 44}px,1fr));grid-auto-rows:${o.wide ? 54 : 34}px;grid-auto-flow:dense;gap:3px">${l.map((r, i) => `<div style="grid-column:span ${i === 0 ? 3 : i < 4 ? 2 : 1};grid-row:span ${i === 0 ? 3 : i < 4 ? 2 : 1}">${h.t(r, { w: '100%', grade: false, style: 'aspect-ratio:auto;height:100%;border-width:1px' })}</div>`).join('')}</div>`;
});
R('075', 'Expanding Grid', 'A small grid; click a tile and it opens in place with what the reviewer saw.', (box, v, o) => {
  const st = h.state('075', {}); const l = h.top(o, 24, 60); const W = o.wide ? 92 : 64;
  const cols = Math.max(1, Math.floor(((box.clientWidth || 340) - 20) / (W + 6)));
  const oi = l.findIndex(r => r.s.id === st.open); const insertAt = oi < 0 ? -1 : Math.min(l.length, (Math.floor(oi / cols) + 1) * cols);
  let html = `<div style="display:grid;grid-template-columns:repeat(${cols},${W}px);gap:6px;justify-content:center">`;
  l.forEach((r, i) => {
    if (i === insertAt) html += detail(l[oi]);
    html += `<div data-x="${esc(r.s.id)}">${h.t(r, { w: W, cls: r.s.id === st.open ? 'on' : '' })}</div>`;
  });
  if (insertAt === l.length) html += detail(l[oi]);
  box.innerHTML = html + '</div>';
  function detail(r) { return `<div style="grid-column:1/-1;display:grid;grid-template-columns:${o.wide ? '280px' : '120px'} 1fr;gap:12px;border:1.5px solid var(--blue);background:var(--blue-soft);border-radius:4px;padding:10px">${h.t(r, { w: '100%' })}<div><b style="font:700 15px/1.2 var(--sans)">${esc(r.s.title)}</b><div class="vnote" style="margin:2px 0 6px">${r.s.year || ''} · ${esc(r.why)}</div><div style="font-size:12px">${esc(r.s.observed || '')}</div><div style="font-size:12px;color:var(--dim);font-style:italic;margin-top:4px">${esc(r.s.use || '')}</div></div></div>`; }
  box.querySelectorAll('[data-x]').forEach(c => c.addEventListener('click', () => { st.open = st.open === c.dataset.x ? null : c.dataset.x; setTimeout(V.rerender, 0); }));
});

/* ---------- 076–080 narrowing ---------- */
R('076', 'Funnel', 'The archive narrowed stage by stage to the one shot the funnel lets through.', (box, v, o) => {
  const s1 = o.list, s2 = s1.filter(r => r.score >= 4), s3 = s2.filter(r => h.reviewed(r.s) || (r.s.cuts && r.s.cuts.length)), s4 = s3.filter(r => h.reviewed(r.s) && r.s.cuts && r.s.cuts.length);
  const pick = (s4[0] || s3[0] || s2[0] || s1[0]);
  const stages = [['everything the words and the moment reach', s1], ['close: at this moment or several words', s2], ['reviewed by an editor, or used by a cut', s3], ['reviewed and used by a cut', s4]];
  box.innerHTML = stages.map(([k, l], i) => `<div style="width:${100 - i * 16}%;margin:0 auto 4px;background:${i === 3 ? 'var(--blue-soft)' : 'var(--box)'};clip-path:polygon(0 0,100% 0,${100 - 3}% 100%,3% 100%);padding:8px 5% 10px;text-align:center"><div class="vlab" style="margin-bottom:4px">${k} · <b style="color:var(--ink)">${l.length}</b></div><div class="vrow nw" style="justify-content:center;gap:3px">${l.slice(0, o.wide ? 12 - i * 2 : 6 - i).map(r => h.t(r, { w: o.wide ? 46 : 30, grade: false })).join('')}</div></div>`).join('') + `<div style="text-align:center;margin-top:8px">↓<div style="display:inline-block;width:${o.wide ? 260 : 150}px;margin-top:6px">${pick ? h.fig(pick, o.wide ? 260 : 150) : ''}</div></div>`;
});
function facets(o) { return { source: h.groups(o.list, h.srcName), decade: h.groups(o.list, r => V.decade(r.s)).sort((a, b) => a[0].localeCompare(b[0])), grade: h.groups(o.list, r => h.grade(r.s)).sort((a, b) => a[0].localeCompare(b[0])) }; }
function applyF(o, f) { return o.list.filter(r => (!f.source || h.srcName(r) === f.source) && (!f.decade || V.decade(r.s) === f.decade) && (!f.grade || h.grade(r.s) === f.grade)); }
R('077', 'Refinement Steps', 'Refine in three steps (source, then decade, then grade) and watch the set shrink.', (box, v, o) => {
  const st = h.state('077', {}); const F = facets(o);
  const step = (k, n, list) => { const opts = h.groups(list, k === 'source' ? h.srcName : k === 'decade' ? r => V.decade(r.s) : r => h.grade(r.s)); if (st[k] && !opts.some(x => x[0] === st[k])) st[k] = null; return `<div class="vframe" style="margin-bottom:6px"><div class="vlab">step ${n} · ${k}</div><div class="vbar" style="margin:0">${h.vbtns([['', 'any <small>' + list.length + '</small>'], ...opts.map(([x, l]) => [x, esc(x) + ' <small>' + l.length + '</small>'])], st[k] || '', 'st-' + k)}</div></div>`; };
  const l1 = o.list, l2 = l1.filter(r => !st.source || h.srcName(r) === st.source), l3 = l2.filter(r => !st.decade || V.decade(r.s) === st.decade), l4 = l3.filter(r => !st.grade || h.grade(r.s) === st.grade);
  box.innerHTML = step('source', 1, l1) + '<div style="text-align:center;color:var(--dim)">↓</div>' + step('decade', 2, l2) + '<div style="text-align:center;color:var(--dim)">↓</div>' + step('grade', 3, l3) + `<div class="vlab" style="margin-top:12px">${l4.length} shots</div><div class="vrow">${l4.slice(0, 40).map(r => h.fig(r, o.wide ? 110 : 76)).join('')}</div>`;
  void F;
  ['source', 'decade', 'grade'].forEach(k => box.querySelectorAll(`[data-st-${k}]`).forEach(b => b.onclick = () => { st[k] = b.dataset['st' + k[0].toUpperCase() + k.slice(1)] || null; V.rerender(); }));
});
R('078', 'Sieve', 'Each word of the line is a mesh: switch it on and only shots that carry it fall through.', (box, v, o) => {
  const st = h.state('078', { on: new Set() }); const terms = V.selTerms().slice(0, 10); const stems = h.stems(terms);
  [...st.on].forEach(t => { if (!terms.includes(t)) st.on.delete(t); });
  const need = stems.filter((x, i) => st.on.has(terms[i]));
  const pass = o.list.filter(r => need.every(x => r.s.text.includes(x))), fail = o.list.filter(r => !pass.includes(r));
  box.innerHTML = `<div class="vbar">${terms.length ? terms.map(t => `<button class="vbtn${st.on.has(t) ? ' on' : ''}" data-t="${esc(t)}">${esc(t)}</button>`).join('') : '<span class="vnote">No content words to sieve with; grip a longer phrase.</span>'}</div>
  <div class="vrow" style="gap:2px;opacity:.45;justify-content:center">${fail.slice(0, o.wide ? 60 : 30).map(r => h.t(r, { w: o.wide ? 30 : 20, grade: false })).join('')}</div>
  <div style="text-align:center;margin:8px 0"><svg width="120" height="46" viewBox="0 0 120 46"><path d="M4 4 H116 L72 30 V44 H48 V30 Z" fill="none" stroke="var(--ink)" stroke-width="1.5"/><path d="M14 10 H106" stroke="var(--faint)" stroke-dasharray="2 3"/></svg><div class="vlab">${pass.length} through · ${fail.length} held back</div></div>
  <div class="vrow" style="justify-content:center">${pass.slice(0, o.wide ? 30 : 14).map(r => h.fig(r, o.wide ? 110 : 74)).join('')}</div>`;
  box.querySelectorAll('[data-t]').forEach(b => b.onclick = () => { const t = b.dataset.t; st.on.has(t) ? st.on.delete(t) : st.on.add(t); V.rerender(); });
});
R('079', 'Filter Columns', 'Tick boxes in three columns (decade, source, grade); the shots on the right keep up.', (box, v, o) => {
  const st = h.state('079', { decade: new Set(), source: new Set(), grade: new Set() }); const F = facets(o);
  const keep = r => (!st.decade.size || st.decade.has(V.decade(r.s))) && (!st.source.size || st.source.has(h.srcName(r))) && (!st.grade.size || st.grade.has(h.grade(r.s)));
  const l = o.list.filter(keep);
  const col = k => `<div style="min-width:0"><div class="vlab">${k}</div>${F[k].map(([x, n]) => `<label style="display:flex;gap:6px;font-size:11.5px;align-items:center;cursor:pointer;padding:1px 0"><input type="checkbox" data-c="${k}" value="${esc(x)}" ${st[k].has(x) ? 'checked' : ''}> ${esc(x)} <small style="color:var(--dim)">${n.length}</small></label>`).join('')}</div>`;
  box.innerHTML = `<div style="display:grid;grid-template-columns:${o.wide ? 'repeat(3,150px) 1fr' : '1fr 1fr 1fr'};gap:14px"><div style="display:contents">${col('decade')}${col('source')}${col('grade')}</div><div style="${o.wide ? '' : 'grid-column:1/-1'}"><div class="vlab">${l.length} shots</div><div class="vrow">${l.slice(0, 48).map(r => h.t(r, { w: o.wide ? 84 : 58 })).join('')}</div></div></div>`;
  box.querySelectorAll('[data-c]').forEach(c => c.onchange = () => { const s = st[c.dataset.c]; c.checked ? s.add(c.value) : s.delete(c.value); V.rerender(); });
});
R('080', 'Facet Panels', 'Each facet a bar chart: click a bar to narrow to it, click again to let go.', (box, v, o) => {
  const st = h.state('080', {}); const F = facets(o); const l = applyF(o, st);
  const panel = k => { const max = Math.max(...F[k].map(x => x[1].length)); return `<div class="vframe" style="min-width:0"><div class="vlab">${k}</div>${F[k].map(([x, n]) => `<button data-f="${k}" data-v="${esc(x)}" style="display:grid;grid-template-columns:${o.wide ? '96px' : '74px'} 1fr 26px;gap:6px;align-items:center;width:100%;background:none;border:0;padding:1px 0;cursor:pointer;font:inherit;font-size:11px;color:${st[k] === x ? 'var(--blue)' : 'var(--ink)'};text-align:left"><span style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis">${esc(x)}</span><i style="height:9px;background:${st[k] === x ? 'var(--blue)' : 'var(--faint)'};width:${(n.length / max * 100).toFixed(1)}%"></i><small style="color:var(--dim)">${n.length}</small></button>`).join('')}</div>`; };
  box.innerHTML = `<div style="display:grid;grid-template-columns:repeat(${o.wide ? 3 : 1},minmax(0,1fr));gap:8px;margin-bottom:12px">${panel('source')}${panel('decade')}${panel('grade')}</div><div class="vlab">${l.length} shots</div><div class="vrow">${l.slice(0, 48).map(r => h.t(r, { w: o.wide ? 96 : 62 })).join('')}</div>`;
  box.querySelectorAll('[data-f]').forEach(b => b.onclick = () => { const k = b.dataset.f; st[k] = st[k] === b.dataset.v ? null : b.dataset.v; V.rerender(); });
});

/* ---------- 081–085 the text beside the shots ---------- */
function occurrences(term) {
  const st = term.length > 5 ? term.slice(0, term.length - 2) : term; const seen = new Set(), out = [];
  S().words.forEach(w => { if (!w.key.startsWith(st)) return; const u = V.unitRange(w.i, 'line'); if (seen.has(u.a)) return; seen.add(u.a); out.push({ w, u }); });
  return out;
}
function termBar(st, terms) { if (!st.term || !terms.includes(st.term)) st.term = terms[0]; return `<div class="vbar">${terms.map(t => `<button class="vbtn${t === st.term ? ' on' : ''}" data-term="${esc(t)}">${esc(t)}</button>`).join('')}</div>`; }
function termWire(box, st) { box.querySelectorAll('[data-term]').forEach(b => b.onclick = () => { st.term = b.dataset.term; V.rerender(); }); }
R('081', 'Concordance', 'Every line of the whole poem that uses the word, each with the shot the suite cut gave it.', (box, v, o) => {
  const st = h.state('081'); const terms = V.selTerms().slice(0, 8); if (!terms.length) { box.innerHTML = h.note('Grip words with some content to see where else the poem uses them.'); return; }
  const bar = termBar(st, terms); const occ = occurrences(st.term).slice(0, 40); const sel = S().sel;
  const stem = st.term.length > 5 ? st.term.slice(0, st.term.length - 2) : st.term;
  box.innerHTML = bar + h.note(`“${esc(st.term)}” is in ${occ.length} line${occ.length === 1 ? '' : 's'} of the poem.`) + occ.map(({ w, u }) => {
    const words = S().words.slice(u.a, u.b + 1).map(x => x.key.startsWith(stem) ? `<mark class="vk">${esc(x.text)}</mark>` : esc(x.text)).join(' ');
    const p = V.cutAt('suite', w.t0 + 0.01); const s = p && (V.shot(p.id) || p);
    const cur = sel && u.a <= sel.a && u.b >= sel.a;
    return `<div class="vline${cur ? ' sel' : ''}" style="grid-template-columns:48px minmax(0,1fr) ${o.wide ? 80 : 54}px"><span class="t" data-sel="${u.a}.${u.b}">${V.fmt0(w.t0)}<br>${esc(S().films[w.film].n)}</span><span class="vtext" data-sel="${u.a}.${u.b}" style="cursor:pointer;font-size:${o.wide ? 15 : 13}px">${words}</span>${s ? h.lineThumb({ s, in: p.in }, u.a, u.b, { w: o.wide ? 80 : 54, grade: false }) : ''}</div>`;
  }).join('');
  termWire(box, st);
});
R('082', 'KWIC · Keyword in Context', 'The word lined up down the middle; its neighbours to the left and right, across the whole poem.', (box, v, o) => {
  const st = h.state('082'); const terms = V.selTerms().slice(0, 8); if (!terms.length) { box.innerHTML = h.note('Grip words with some content.'); return; }
  const bar = termBar(st, terms); const stem = st.term.length > 5 ? st.term.slice(0, st.term.length - 2) : st.term; const n = o.wide ? 7 : 3;
  const hits = S().words.filter(w => w.key.startsWith(stem)).slice(0, 60);
  box.innerHTML = bar + `<div style="display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr) ${o.wide ? 60 : 40}px;gap:4px 8px;align-items:center;font:400 ${o.wide ? 14 : 12}px/1.35 var(--sans)">${hits.map(w => {
    const L = S().words.slice(Math.max(0, w.i - n), w.i).filter(x => x.s === w.s).map(x => x.text).join(' '), Rr = S().words.slice(w.i + 1, w.i + 1 + n).filter(x => x.s === w.s).map(x => x.text).join(' ');
    const p = V.cutAt('suite', w.t0 + 0.01); const s = p && (V.shot(p.id) || p);
    return `<span style="text-align:right;white-space:nowrap;overflow:hidden;direction:rtl;color:var(--dim)"><bdi>${esc(L)}</bdi></span><mark class="vk" data-sel="${w.i}.${w.i}" style="cursor:pointer;font-weight:600">${esc(w.text)}</mark><span style="white-space:nowrap;overflow:hidden;color:var(--dim)">${esc(Rr)}</span>${s ? h.lineThumb({ s, in: p.in }, w.i, w.i, { w: o.wide ? 60 : 40, grade: false }) : '<span></span>'}`;
  }).join('')}</div>`;
  termWire(box, st);
});
R('083', 'Parallel Lines', 'The lines of the stanza side by side with their three best shots each. Click a shot to grip its line; double-click to couple it.', (box, v, o) => {
  const st = V.around('stanza'); if (!st) return; const lines = V.unitsIn(st.a, st.b, 'line');
  box.innerHTML = lines.map(u => { const l = V.results(u, 'all').slice(0, o.wide ? 4 : 3); const cur = S().sel && S().sel.a >= u.a && S().sel.a <= u.b; return `<div class="vline${cur ? ' sel' : ''}" style="grid-template-columns:${o.wide ? 'minmax(0,1fr) auto' : '1fr'}"><span class="vtext" data-sel="${u.a}.${u.b}" style="cursor:pointer;font-size:${o.wide ? 15 : 13.5}px">${esc(u.text)}</span><span class="vrow nw" style="gap:4px">${l.map(r => h.lineThumb(r, u.a, u.b, { w: o.wide ? 92 : 60 })).join('')}</span></div>`; }).join('');
});
R('084', 'Poem Columns', 'The passage in one column, a shot for each stanza in the next, joined across the gutter.', (box, v, o) => {
  const P = V.around('passage'); if (!P) return; const sts = V.unitsIn(P.a, P.b, 'stanza'); const sel = S().sel;
  box.innerHTML = `<div style="display:grid;grid-template-columns:minmax(0,1fr) ${o.wide ? 70 : 24}px ${o.wide ? 190 : 92}px;gap:10px 0">${sts.map((u, i) => {
    const b = V.bindsIn(u.t0, u.t1)[0]; const r = b ? { s: V.shot(b.shot.id) || b.shot, in: b.in } : V.bestFor(u, 'time');
    const cur = sel && sel.a >= u.a && sel.a <= u.b;
    return `<div class="vtext" data-sel="${u.a}.${u.b}" data-l="${i}" style="cursor:pointer;font-size:${o.wide ? 15 : 13}px;padding:4px 6px;border-radius:3px;${cur ? 'background:var(--blue-soft)' : ''}">${esc(u.text)}</div><span></span><div data-r="${i}">${r ? h.lineThumb(r, u.a, u.b, { w: o.wide ? 190 : 92, cls: b ? 'mine' : '' }) : ''}${b ? '<span class="vcap" style="color:var(--blue)">coupled</span>' : ''}</div>`;
  }).join('')}</div>`;
  wire(box, sts.map((x, i) => [box.querySelector(`[data-l="${i}"]`), box.querySelector(`[data-r="${i}"] .vx`), { mode: 'h', dash: true }]));
});
R('085', 'Text to Clips', 'Each word you hold drops to the clip that answers it best. Double-click a clip to couple it to that word alone.', (box, v, o) => {
  const sel = S().sel; if (!sel) return; const ws = S().words.slice(sel.a, sel.b + 1).filter(w => w.key.length > 2 && !/^(the|and|you|for|with|that|this|was|are|not|but|our|his|her|its|from|into|she|him|they|them|then|than|have|has|had)$/.test(w.key)).slice(0, o.wide ? 12 : 6);
  const used = new Set(); const W = o.wide ? 96 : 64;
  box.innerHTML = `<div class="vrow" style="gap:${o.wide ? 14 : 8}px;justify-content:center">${ws.map(w => { const r = V.results(null, 'words', w.key).find(x => !used.has(x.s.id)); if (r) used.add(r.s.id); return `<div class="vcol" style="width:${W}px"><span class="vnode sel" data-sel="${w.i}.${w.i}" data-w="${w.i}">${esc(w.text.replace(/[^\w'’-]/g, ''))}</span><div style="height:30px"></div>${r ? h.lineThumb(r, w.i, w.i, { w: W }) : '<span class="vx none" style="--w:' + W + 'px"></span>'}${r ? `<span class="vcap" style="max-width:${W}px">${esc(r.s.title)}</span>` : '<span class="vcap">nothing</span>'}</div>`; }).join('')}</div>`;
  h.arrows(box, [...box.querySelectorAll('[data-w]')].map(n => [n, n.parentElement.querySelector('.vx')]), { color: 'var(--blue)' });
});

/* ---------- 086–090 maps of meaning ---------- */
R('086', 'Association Web', 'The words you hold in the middle, each strand running out to the shots it calls up.', (box, v, o) => {
  const terms = V.selTerms().slice(0, o.wide ? 8 : 6); if (!terms.length) { box.innerHTML = h.note('Grip words with some content.'); return; }
  const used = new Set(); const w = o.wide ? 78 : 42;
  let html = h.stage(o.wide ? '1.5' : '1', o.wide ? '980px' : '100%') + h.at(50, 50, h.hub('', 40));
  terms.forEach((t, i) => { const ang = -90 + i * 360 / terms.length; const [x, y] = h.polar(22, ang, 50, 50, o.wide ? 24 : 22); html += h.at(x, y, `<span class="vnode" data-term="${i}">${esc(t)}</span>`);
    V.results(null, 'words', t).filter(r => !used.has(r.s.id)).slice(0, 2).forEach((r, j) => { used.add(r.s.id); const [x2, y2] = h.polar(o.wide ? 42 : 40, ang + (j ? 11 : -11), 50, 50, o.wide ? 40 : 40); html += h.at(x2, y2, h.t(r, { w }), `" data-of="${i}`); }); });
  box.innerHTML = html + '</div>';
  const hub = box.querySelector('.hub'), links = [];
  terms.forEach((t, i) => { const n = box.querySelector(`[data-term="${i}"]`); links.push([hub, n, { mode: 'c', color: 'var(--blue)', w: 1.5 }]); box.querySelectorAll(`[data-of="${i}"] .vx`).forEach(x => links.push([n, x, { mode: 'c' }])); });
  wire(box, links);
});
R('087', 'Semantic Map', 'Each word an anchor on the rim; each shot sits between the words it carries.', (box, v, o) => {
  const terms = V.selTerms().slice(0, 8); const stems = h.stems(terms); const l = h.top(o, 30, 70); const w = o.wide ? 50 : 30;
  if (terms.length < 2) { box.innerHTML = h.note('The map needs at least two content words; grip a longer phrase.'); return; }
  const A = terms.map((t, i) => h.polar(40, -90 + i * 360 / terms.length));
  let html = `<div style="padding:0 ${o.wide ? 40 : 28}px">` + h.stage('1', o.wide ? '760px' : '100%') + `<div style="position:absolute;inset:10%;border:1.5px dashed var(--rule);border-radius:50%"></div>`;
  terms.forEach((t, i) => html += h.at(A[i][0], A[i][1], `<span class="vnode sel">${esc(t)}</span>`, 'z-index:5'));
  l.forEach(r => { const hit = stems.map(x => r.s.text.includes(x)); const n = hit.filter(Boolean).length; let x = 50, y = 50; if (n) { x = 0; y = 0; hit.forEach((b, i) => { if (b) { x += A[i][0]; y += A[i][1]; } }); x /= n; y /= n; x = 50 + (x - 50) * 0.8; y = 50 + (y - 50) * 0.8; } x += (h.hash(r.s.id) - 0.5) * 12; y += (h.hash(r.s.id + 'y') - 0.5) * 12; html += h.at(x, y, h.t(r, { w, grade: false })); });
  box.innerHTML = html + '</div></div>';
});
R('088', 'Nearest Neighbors', 'The shot in view at the centre; its nearest neighbours in the archive by what reviewers wrote, nearer is closer.', (box, v, o) => {
  const f = h.focus(o); if (!f) return; const F = V.shot(f.id) || f; const T = h.tokens(F); const all = [...S().shots.values()].filter(s => s.id !== F.id);
  const nn = all.map(s => ({ s, d: h.jac(T, h.tokens(s)) })).sort((a, b) => b.d - a.d).slice(0, o.wide ? 14 : 8);
  const w = o.wide ? 80 : 44; const max = nn[0] ? nn[0].d : 1;
  let html = h.stage(o.wide ? '1.5' : '1', o.wide ? '980px' : '100%') + h.at(50, 50, h.ts(F, { w: o.wide ? 150 : 84, cls: 'on' }));
  nn.forEach((x, i) => { const r = 20 + (1 - x.d / (max || 1)) * 24 + 6; const [px, py] = h.polar(r, -90 + i * 360 / nn.length, 50, 50, o.wide ? r * 1.0 : r); html += h.at(px, py, `${h.ts(x.s, { w })}<small style="display:block;text-align:center;font:500 9px var(--mono);color:var(--dim)">${Math.round(x.d * 100)}%</small>`); });
  box.innerHTML = h.note(`Neighbours of <b>${esc(F.title)}</b>. Click any shot to make it the centre.`) + html + '</div>';
  const c = box.querySelector('.vx.on'); wire(box, [...box.querySelectorAll('.vp .vx')].filter(x => x !== c).map(x => [c, x, { mode: 'c', dash: '2 3' }]));
});
R('089', 'Similarity Field', 'A field of shots: across by how much of your words they carry, up by how like the shot in view they are.', (box, v, o) => {
  const f = h.focus(o); const T = f ? h.tokens(V.shot(f.id) || f) : new Set(); const stems = h.stems(V.selTerms()); const l = h.top(o, 40, 100); const w = o.wide ? 40 : 26;
  const pts = l.map(r => ({ r, x: stems.length ? stems.filter(x => r.s.text.includes(x)).length / stems.length : 0, y: h.jac(T, h.tokens(r.s)) }));
  const my = Math.max(0.05, ...pts.map(p => p.y));
  let html = h.stage('1.5', '100%') + `<div style="position:absolute;left:4%;right:2%;bottom:6%;top:2%;border-left:1.5px solid var(--ink);border-bottom:1.5px solid var(--ink)"></div><div style="position:absolute;left:52%;top:2%;bottom:6%;border-left:1px dashed var(--rule)"></div><div style="position:absolute;left:4%;right:2%;top:48%;border-top:1px dashed var(--rule)"></div>`;
  pts.forEach(p => html += h.at(6 + p.x * 88 + (h.hash(p.r.s.id) - 0.5) * 5, 90 - p.y / my * 80 + (h.hash(p.r.s.id + 'y') - 0.5) * 4, h.t(p.r, { w, grade: false })));
  html += `<span class="vaxis" style="right:2%;bottom:0">carries your words →</span><span class="vaxis" style="left:5%;top:0">↑ like ${esc(f ? f.title.slice(0, 28) : 'the shot in view')}</span>`;
  box.innerHTML = html + '</div>';
});
R('090', 'Concept Space', 'Three concepts from the beat under your words as three axes; each shot placed by how much of each it holds.', (box, v, o) => {
  const sel = S().sel; const b = sel && V.beatsIn(sel.t0, sel.t1)[0]; let items = (b && b.items || []).slice(0, 3); if (items.length < 3) items = items.concat(V.selTerms()).slice(0, 3);
  if (items.length < 3) { box.innerHTML = h.note('Needs three concepts; grip a longer passage.'); return; }
  const tk = items.map(it => it.toLowerCase().split(/\W+/).filter(x => x.length > 3).map(x => x.length > 5 ? x.slice(0, x.length - 2) : x));
  const l = h.top(o, 30, 70); const w = o.wide ? 44 : 28; const O = [50, 78];
  const proj = (a, b2, c) => [O[0] + (a - b2) * 36, O[1] + (a + b2) * 14 - c * 62];
  let html = h.stage('1.3', o.wide ? '860px' : '100%');
  const axes = [[1, 0, 0], [0, 1, 0], [0, 0, 1]].map(([a, b2, c], i) => { const e = proj(a, b2, c); return `<line x1="${O[0]}" y1="${O[1]}" x2="${e[0]}" y2="${e[1]}" stroke="var(--ink)" stroke-width=".35"/><text x="${e[0]}" y="${e[1] + (i === 2 ? -1.5 : 4)}" font-size="2.8" text-anchor="middle" fill="var(--blue)" font-family="sans-serif">${esc(items[i])}</text>`; }).join('');
  html += `<svg viewBox="0 0 100 100" preserveAspectRatio="none" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible">${axes}</svg>`;
  l.forEach(r => { const vv = tk.map(ts => ts.length ? ts.filter(x => r.s.text.includes(x)).length / ts.length : 0); const [x, y] = proj(vv[0], vv[1], vv[2]); html += h.at(x + (h.hash(r.s.id) - 0.5) * 6, y + (h.hash(r.s.id + 'z') - 0.5) * 5, h.t(r, { w, grade: false })); });
  box.innerHTML = html + '</div>';
});

/* ---------- 091–095 layers and depth ---------- */
R('091', 'Layers', 'What you hold as five stacked layers: text, clips, audio, places, time.', (box, v, o) => {
  const sel = S().sel; if (!sel) return; const segs = S().segs.filter(s => s.t1 > sel.t0 && s.t0 < sel.t1); const ws = S().words.slice(sel.a, Math.min(sel.b + 1, sel.a + 30));
  const b = V.beatsIn(sel.t0, sel.t1)[0]; const f = S().films[S().words[sel.a].film];
  const dur = Math.max(0.01, sel.t1 - sel.t0);
  const layer = (name, inner, k) => `<div style="display:grid;grid-template-columns:62px 1fr;align-items:center;margin-top:${k ? -8 : 0}px"><span class="vlab" style="margin:0">${name}</span><div style="transform:skewX(-24deg);border:1.5px solid ${k === 1 ? 'var(--blue)' : 'var(--ink)'};background:${k === 1 ? 'var(--blue-soft)' : 'var(--panel)'};padding:8px 14px;min-height:44px;box-shadow:4px 4px 0 var(--box);position:relative;z-index:${10 - k}"><div style="transform:skewX(24deg)">${inner}</div></div></div>`;
  box.innerHTML = `<div style="max-width:${o.wide ? '860px' : '100%'};margin:0 auto;display:flex;flex-direction:column;gap:14px;padding:0 22px 0 4px;overflow:hidden">` +
    layer('text', `<span class="vtext" style="font-size:13px">${esc(ws.map(w => w.text).join(' '))}${sel.b - sel.a > 29 ? '…' : ''}</span>`, 0) +
    layer('clips', `<div class="vrow nw" style="gap:3px">${segs.slice(0, 12).map(s => s.kind === 'text' ? `<span class="vx none" style="--w:${o.wide ? 70 : 40}px"></span>` : h.ts(s.kind === 'mine' ? (V.shot(s.ref.shot.id) || s.ref.shot) : (V.shot(s.ref.id) || s.ref), { w: o.wide ? 70 : 40, in: s.off, grade: false, cls: s.kind === 'mine' ? 'mine' : '' })).join('')}</div>`, 1) +
    layer('audio', `<div style="display:flex;align-items:center;height:30px;gap:1px">${ws.map(w => `<i style="flex:${(w.t1 - w.t0) / dur};height:${30 + 60 * h.hash(w.text)}%;background:var(--ink);opacity:.7;min-width:1px"></i>`).join('')}</div>`, 2) +
    layer('places', `<span style="font-size:12px">${esc(f.world.tagline || f.title)}${b ? ' · ' + esc((b.items || []).join(' · ')) : ''}</span>`, 3) +
    layer('time', `<span style="font:500 11px var(--mono)">${V.fmt(sel.t0)} → ${V.fmt(sel.t1)} · ${dur.toFixed(1)} s</span>`, 4) + '</div>';
});
R('092', 'Stack View', 'The sources as stacked planes; the plane that holds the shot in view rises to the top.', (box, v, o) => {
  const g = h.groups(o.list, h.srcName); const pv = S().pv; const hot = pv ? g.findIndex(([, l]) => l.some(r => r.s.id === pv.id)) : 0;
  box.innerHTML = `<div style="max-width:${o.wide ? '820px' : '100%'};margin:0 auto;padding:10px 20px">${g.map(([k, l], i) => `<div style="transform:perspective(900px) rotateX(48deg);transform-origin:50% 100%;border:1.5px solid ${i === hot ? 'var(--blue)' : 'var(--ink)'};background:${i === hot ? 'var(--blue-soft)' : 'var(--panel)'};padding:10px 14px 12px;margin-top:${i ? -24 : 0}px;box-shadow:0 6px 10px #0002;position:relative;z-index:${i === hot ? 50 : 20 - i}"><div class="vlab">${esc(k)} · ${l.length}</div><div class="vrow nw" style="gap:5px">${l.slice(0, o.wide ? 9 : 5).map(r => h.t(r, { w: o.wide ? 76 : 46, grade: false })).join('')}</div></div>`).join('')}</div>`;
});
R('093', 'Depth Stack', 'The list recedes into depth; step forward through it one shot at a time.', (box, v, o) => {
  const st = h.state('093', { i: 0 }); const l = o.list.slice(0, 40); st.i = Math.min(st.i, l.length - 1); const W = o.wide ? 380 : 210;
  let html = `<div class="v3d" style="position:relative;height:${Math.round(W * 0.75) + 110}px;perspective:700px;overflow:hidden">`;
  for (let d = 5; d >= 0; d--) { const r = l[st.i + d]; if (!r) continue; html += `<div style="position:absolute;left:50%;top:${50 + d * 0}%;transform:translate(-50%,-50%) translate3d(${d * 26}px,${-d * 22}px,${-d * 140}px);opacity:${1 - d * 0.14};z-index:${10 - d}">${h.t(r, { w: W })}${d ? '' : `<div class="vcap" style="--w:${W}px;font-size:13px">${esc(r.s.title)}<small>${r.s.year || ''} · ${esc(r.why)}</small></div>`}</div>`; }
  html += `</div><div class="vbar" style="justify-content:center"><button class="vbtn" data-d="-1">↑ back</button><span class="vnote" style="margin:0">${st.i + 1} / ${l.length}</span><button class="vbtn" data-d="1">deeper ↓</button></div>`;
  box.innerHTML = html;
  box.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { st.i = Math.max(0, Math.min(l.length - 1, st.i + +b.dataset.d)); V.rerender(); });
  box.querySelector('.v3d').addEventListener('wheel', e => { e.preventDefault(); st.i = Math.max(0, Math.min(l.length - 1, st.i + Math.sign(e.deltaY))); V.rerender(); }, { passive: false });
});
R('094', 'Card Flow', 'Cover flow: the list as cards turned edge-on, the one in front facing you.', (box, v, o) => {
  const st = h.state('094', { i: 0 }); const l = o.list.slice(0, 40); st.i = Math.min(st.i, l.length - 1); const W = o.wide ? 280 : 150, side = o.wide ? 5 : 2;
  let html = `<div class="v3d" style="display:flex;justify-content:center;align-items:center;height:${Math.round(W * 0.75) + 50}px;perspective:800px;overflow:hidden">`;
  for (let d = -side; d <= side; d++) { const r = l[st.i + d]; if (!r) continue; html += `<div data-go="${d}" style="flex:none;margin:0 ${d ? -W * 0.34 : W * 0.12}px;transform:rotateY(${d ? -Math.sign(d) * 62 : 0}deg) ${d ? '' : 'scale(1.08)'};z-index:${20 - Math.abs(d)};box-shadow:0 8px 16px #0003">${h.t(r, { w: W })}</div>`; }
  html += `</div><div class="vbar" style="justify-content:center"><button class="vbtn" data-d="-1">‹</button><span class="vnote" style="margin:0">${esc(l[st.i].s.title)} · ${l[st.i].s.year || ''}</span><button class="vbtn" data-d="1">›</button></div>`;
  box.innerHTML = html;
  box.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { st.i = Math.max(0, Math.min(l.length - 1, st.i + +b.dataset.d)); V.rerender(); });
  box.querySelectorAll('[data-go]').forEach(b => { if (+b.dataset.go) b.addEventListener('click', () => { st.i = Math.max(0, Math.min(l.length - 1, st.i + +b.dataset.go)); setTimeout(V.rerender, 0); }); });
});
R('095', 'Fold Out', 'A folded leaflet: the words on the first panel, the shots on the others. Unfold it flat.', (box, v, o) => {
  const st = h.state('095', { open: false }); const g = h.groups(o.list, h.srcName, 3); const sel = S().sel; const b = sel && V.beatsIn(sel.t0, sel.t1)[0];
  const panels = [`<div class="vlab">what you hold</div><div class="vtext" style="font-size:13px">${esc(h.q(160))}</div>${b ? `<div class="vnote" style="margin-top:8px">${esc(b.title)}</div>` : ''}`].concat(g.map(([k, l]) => `<div class="vlab">${esc(k)}</div><div class="vrow" style="gap:4px">${l.slice(0, 6).map(r => h.t(r, { w: o.wide ? 70 : 44, grade: false })).join('')}</div>`));
  box.innerHTML = `<div class="vbar"><button class="vbtn on" data-fold>${st.open ? 'fold it' : 'unfold it'}</button></div><div class="v3d" style="display:flex;justify-content:center;flex-wrap:${o.wide ? 'nowrap' : 'wrap'};padding:10px 0">${panels.map((p, i) => `<div style="flex:${o.wide ? '1 1 0' : '0 0 150px'};max-width:210px;min-width:0;min-height:170px;border:1.5px solid var(--ink);background:${i ? 'var(--panel)' : 'var(--blue-soft)'};padding:10px;transform:${st.open ? 'none' : `rotateY(${i % 2 ? -28 : 28}deg)`};transition:transform .5s;box-shadow:${st.open ? 'none' : (i % 2 ? '-6px' : '6px') + ' 6px 12px #0002'}">${p}</div>`).join('')}</div>`;
  box.querySelector('[data-fold]').onclick = () => { st.open = !st.open; V.rerender(); };
});

/* ---------- 096–100 from shots to a film ---------- */
R('096', 'Story Builder', 'The lines of the stanza as a list; beside each, what the film plays there now. Build it line by line.', (box, v, o) => {
  const P = V.around(o.wide ? 'passage' : 'stanza'); if (!P) return; const lines = V.unitsIn(P.a, P.b, 'line').slice(0, 30); const sel = S().sel;
  const shotAt = u => { const b = V.bindsIn(u.t0, u.t1)[0]; if (b) return { s: V.shot(b.shot.id) || b.shot, in: b.in, mine: true }; const p = V.cutAt(S().base === 'text' ? 'suite' : S().base, u.t0 + 0.05); return p ? { s: V.shot(p.id) || p, in: p.in } : null; };
  const rows = lines.map(u => ({ u, r: shotAt(u) }));
  box.innerHTML = `<div style="display:grid;grid-template-columns:minmax(0,1fr) ${o.wide ? 110 : 64}px;gap:6px 12px;align-items:center">${rows.map(({ u, r }) => { const cur = sel && sel.a >= u.a && sel.a <= u.b; return `<div data-sel="${u.a}.${u.b}" style="cursor:pointer;display:flex;gap:8px;font:400 ${o.wide ? 14 : 13}px/1.35 var(--sans);padding:3px 6px;border-radius:3px;${cur ? 'background:var(--blue-soft)' : ''}"><span style="color:${r && r.mine ? 'var(--blue)' : 'var(--faint)'}">●</span>${esc(u.text)}</div><div>${r ? h.lineThumb(r, u.a, u.b, { w: o.wide ? 110 : 64, cls: r.mine ? 'mine' : '', grade: false }) : '<span class="vx none"></span>'}</div>`; }).join('')}</div>
  <div style="text-align:center;margin:10px 0;color:var(--dim)">↓ the sequence</div><div class="vrow nw" style="gap:2px">${rows.filter(x => x.r).map(({ r }) => h.ts(r.s, { w: o.wide ? 70 : 42, in: r.in, grade: false, cls: r.mine ? 'mine' : '' })).join('')}</div>`;
});
R('097', 'Clip Sequence', 'The film around what you hold, clip by clip, numbered, each as long as it plays.', (box, v, o) => {
  const P = V.around('stanza'); if (!P) return; const t0 = P.t0 - 2, t1 = P.t1 + 2; const segs = S().segs.filter(s => s.t1 > t0 && s.t0 < t1); const span = t1 - t0;
  box.innerHTML = `<div style="display:flex;gap:2px;height:${o.wide ? 100 : 64}px">${segs.map((s, i) => { const w = (Math.min(s.t1, t1) - Math.max(s.t0, t0)) / span * 100; const sh = s.kind === 'mine' ? (V.shot(s.ref.shot.id) || s.ref.shot) : s.kind === 'base' ? (V.shot(s.ref.id) || s.ref) : null; return `<div style="flex:0 0 calc(${w.toFixed(2)}% - 2px);position:relative;min-width:0"><span style="position:absolute;top:-16px;left:0;font:600 10px var(--mono);color:${s.kind === 'mine' ? 'var(--blue)' : 'var(--dim)'}">${i + 1}</span>${sh ? h.ts(sh, { in: s.off, grade: false, cls: s.kind === 'mine' ? 'mine' : '', style: '--w:100%;aspect-ratio:auto;height:100%' }) : `<span class="vx none" style="--w:100%;aspect-ratio:auto;height:100%;display:flex;align-items:center;justify-content:center;font:700 9px var(--sans);color:var(--dim);padding:2px;text-align:center">${esc(s.text || '')}</span>`}</div>`; }).join('')}</div>
  <div class="vruler">${[0, .25, .5, .75].map(k => `<span style="left:${k * 100}%">${V.fmt(t0 + k * span)}</span>`).join('')}</div><div class="vspan" style="top:16px;height:${o.wide ? 100 : 64}px;left:${(P.t0 - t0) / span * 100}%;width:${(P.t1 - P.t0) / span * 100}%"></div>
  ${h.note(`${segs.length} clips over ${span.toFixed(0)} s; blue numbers are your couplings, the rest the ${S().base === 'text' ? 'text cards' : S().base + ' cut'}.`)}`;
  box.style.paddingTop = '26px';
});
R('098', 'Montage', 'The best shots scattered as a collage, then pulled into order along the bottom.', (box, v, o) => {
  const l = h.top(o, 6, 9); const w = o.wide ? 120 : 58;
  let html = h.stage(o.wide ? '2' : '1.2', '100%');
  l.forEach((r, i) => { const x = 10 + (i % 3) * 38 + (h.hash(r.s.id) - 0.5) * 12, y = 14 + Math.floor(i / 3) * (o.wide ? 24 : 22) + (h.hash(r.s.id + 'm') - 0.5) * 8; html += h.at(x, y, h.t(r, { w, grade: false }), `transform:translate(-50%,-50%) rotate(${(h.hash(r.s.id + 'r') - 0.5) * 14}deg)" data-m="${i}`); });
  html += `<div data-bot style="position:absolute;left:0;right:0;bottom:0;display:flex;gap:3px;justify-content:center">${l.map((r, i) => `<span data-b="${i}">${h.t(r, { w: o.wide ? 76 : 36, grade: false })}</span>`).join('')}</div>`;
  box.innerHTML = html + '</div>';
  h.arrows(box, l.map((r, i) => [box.querySelector(`[data-m="${i}"] .vx`), box.querySelector(`[data-b="${i}"] .vx`)]), { dash: '3 3' });
});
R('099', 'Playlist', 'A numbered playlist. Play it and the viewer runs down the list, four seconds a shot.', (box, v, o) => {
  const st = h.state('099', { i: -1 }); const l = o.list.slice(0, 40);
  box.innerHTML = `<div class="vbar"><button class="vbtn on" data-pl>${st.timer ? '■ stop' : '▷ play the list'}</button><span class="vnote" style="margin:0">${l.length} shots</span></div>` + l.map((r, i) => `<div class="vline${i === st.i ? ' sel' : ''}" style="grid-template-columns:26px ${o.wide ? 96 : 60}px minmax(0,1fr) auto;align-items:center"><span class="t" style="text-align:right">${i + 1}</span>${h.t(r, { w: o.wide ? 96 : 60, grade: false })}<span style="min-width:0"><b style="font:600 13px/1.2 var(--sans);display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(r.s.title)}</b><small style="color:var(--dim)">${r.s.year || ''} · ${esc(r.why)}</small></span><button class="vbtn" data-pi="${i}">▷</button></div>`).join('');
  const go = i => { st.i = i; const r = l[i]; if (r) V.preview(r.s, r.in); box.querySelectorAll('.vline').forEach((x, k) => x.classList.toggle('sel', k === i)); };
  box.querySelectorAll('[data-pi]').forEach(b => b.onclick = () => go(+b.dataset.pi));
  box.querySelector('[data-pl]').onclick = () => { if (st.timer) { clearInterval(st.timer); st.timer = null; V.rerender(); return; } go(Math.max(0, st.i)); st.timer = setInterval(() => { if (!document.body.contains(box)) { clearInterval(st.timer); st.timer = null; return; } go((st.i + 1) % l.length); }, 4000); V.rerender(); };
});
R('100', 'Export Film', 'The passage as it stands, on a strip, with the ways out: edit list, markers, link, a saved version.', (box, v, o) => {
  const fi = S().sel ? S().words[S().sel.a].film : 0; const f = S().films[fi]; const segs = S().segs.filter(s => s.t1 > f.container[0] && s.t0 < f.container[1]);
  const span = f.container[1] - f.container[0];
  box.innerHTML = `<div class="vlab">${esc(f.n + ' ' + f.title)} · ${segs.length} clips · ${V.fmt0(span)}</div><div style="background:#141414;padding:12px 6px;display:flex;gap:1px;border-radius:3px">${segs.map(s => { const sh = s.kind === 'mine' ? (V.shot(s.ref.shot.id) || s.ref.shot) : s.kind === 'base' ? (V.shot(s.ref.id) || s.ref) : null; return `<div style="flex:${(Math.min(s.t1, f.container[1]) - Math.max(s.t0, f.container[0])).toFixed(2)} 0 0;min-width:0;height:${o.wide ? 70 : 40}px">${sh ? h.ts(sh, { in: s.off, grade: false, cls: s.kind === 'mine' ? 'mine' : '', style: '--w:100%;aspect-ratio:auto;height:100%;border-width:1px' }) : '<span class="vx none" style="--w:100%;aspect-ratio:auto;height:100%"></span>'}</div>`; }).join('')}</div>
  <div style="text-align:center;margin:10px;color:var(--dim)">↓</div><div class="vrow" style="justify-content:center"><button class="vbtn on" data-x="rPlay">▷ play the film</button><button class="vbtn" data-x="rEdl">edit list (.json)</button><button class="vbtn" data-x="rVtt">markers (.vtt)</button><button class="vbtn" data-x="rLink">share link</button><button class="vbtn" data-x="rSave">archive a version</button></div>`;
  box.querySelectorAll('[data-x]').forEach(b => b.onclick = () => document.getElementById(b.dataset.x).click());
}, { needs: 'none' });
})();
