/* Videotext · Sheet 04 · Couple word and shot (151–200).
   In these views a click on a shot with data-a/data-b couples it to those words at once. */
(() => {
'use strict';
const V = window.VT, h = V.h, { esc, wire } = V;
const S = () => V.S;
const R = (id, name, desc, render, extra = {}) => V.register({ id, sheet: '04', name, desc, render, ...extra });

const mineIn = u => { const b = V.bindsIn(u.t0, u.t1).find(x => x.a <= u.a && x.b >= u.b) || V.bindsIn(u.t0, u.t1)[0]; return b ? { s: V.shot(b.shot.id) || b.shot, in: b.in, b, why: 'coupled' } : null; };
const ghost = (u, skip) => V.bestFor(u, 'all', skip);
const at = (u, o = {}) => ({ a: u.a, b: u.b, ...o });
const sel = () => S().sel;
const selR = () => sel() && V.rangeOf(sel().a, sel().b);
const W = (o, pane, wide) => o.wide ? wide : pane;
const words = u => S().words.slice(u.a, u.b + 1);
const shotOfSeg = s => s.kind === 'mine' ? (V.shot(s.ref.shot.id) || s.ref.shot) : s.kind === 'base' ? (V.shot(s.ref.id) || s.ref) : null;
const slot = (w, label) => `<span class="vx none" style="--w:${w}px;display:flex;align-items:center;justify-content:center;font:600 9px var(--sans);color:var(--dim)">${label || ''}</span>`;

R('151', 'Text to Strip', 'The words over a strip of shots; the coupled one is joined to them. Click a shot to couple it.', (box, v, o) => {
  const u = selR(); const m = mineIn(u); const l = h.top(o, 5, 8);
  box.innerHTML = `<div style="text-align:center">${h.hub('', 90)}</div><div style="height:34px"></div><div class="vrow" style="justify-content:center;gap:6px">${l.map(r => h.t(r, at(u, { w: W(o, 60, 110), cls: m && m.s.id === r.s.id ? 'mine' : '' }))).join('')}</div>`;
  const hub = box.querySelector('.hub'), tgt = box.querySelector('.vx.mine') || box.querySelector('.vx');
  h.arrows(box, [[hub, tgt]], { color: 'var(--blue)', dash: m ? '' : '4 3' });
});
R('153', 'Dual Attach', 'Two shots for the same words, side by side. Couple either; the other stays one click away.', (box, v, o) => {
  const u = selR(); const l = o.list.slice(0, 2); const m = mineIn(u);
  box.innerHTML = `<div style="text-align:center">${h.hub('', 90)}</div><div class="vrow" style="justify-content:center;gap:${o.wide ? 60 : 16}px;margin-top:40px">${l.map((r, i) => `<div class="vcol">${h.t(r, at(u, { w: W(o, 130, 260), cls: m && m.s.id === r.s.id ? 'mine' : '' }))}<span class="vcap" style="--w:${W(o, 130, 260)}px">${'AB'[i]} · ${esc(r.s.title)}<small>${esc(r.why)}</small></span></div>`).join('')}</div>`;
  const hub = box.querySelector('.hub'); wire(box, [...box.querySelectorAll('.vx')].map(x => [hub, x, { color: x.classList.contains('mine') ? 'var(--blue)' : 'var(--faint)', w: 1.6 }]));
});
R('154', 'Inline Thumbnails', 'The stanza with a thumbnail at the end of every line: blue where you coupled, faint where the archive suggests. Click a faint one to take it.', (box, v, o) => {
  const P = V.around(o.wide ? 'passage' : 'stanza'); const lines = V.unitsIn(P.a, P.b, 'line');
  box.innerHTML = `<div class="vtext" style="font-size:${W(o, 15, 18)}px;line-height:2.1;max-width:70ch">${lines.map(u => { const m = mineIn(u); const g = m ? null : ghost(u, V.used()); const r = m || g; return `<span data-sel="${u.a}.${u.b}" style="cursor:pointer;${sel() && sel().a >= u.a && sel().a <= u.b ? 'background:var(--blue-soft);' : ''}">${esc(u.text)}</span> ${r ? `<span style="display:inline-block;vertical-align:middle;opacity:${m ? 1 : .45}">${h.t(r, at(u, { w: W(o, 34, 46), grade: false, cls: m ? 'mine' : '' }))}</span>` : ''} `; }).join('')}</div>`;
});
R('155', 'Bracket Link', 'A bracket around the words, three branches down to three shots.', (box, v, o) => {
  const u = selR(); const l = o.list.slice(0, 3);
  box.innerHTML = `<div style="text-align:center;font:400 ${W(o, 16, 22)}px var(--sans)"><span style="font-size:1.6em;color:var(--blue);vertical-align:-3px">[</span> <span data-br>${esc(h.q(80))}</span> <span style="font-size:1.6em;color:var(--blue);vertical-align:-3px">]</span></div><div class="vrow" style="justify-content:center;gap:${W(o, 10, 40)}px;margin-top:44px">${l.map(r => h.t(r, at(u, { w: W(o, 90, 180) }))).join('')}</div>`;
  const br = box.querySelector('[data-br]'); wire(box, [...box.querySelectorAll('.vx')].map(x => [br, x, { color: 'var(--blue)' }]));
});
R('156', 'Magnetic Lane', 'The line’s phrases laid out as lengths of time; a shot snaps under each. Faint ones are suggestions: click to couple.', (box, v, o) => {
  const L = V.around('line'); const ph = V.unitsIn(L.a, L.b, 'phrase'); const span = L.t1 - L.t0 || 1; const used = V.used();
  box.innerHTML = `<div class="vlab">${V.fmt(L.t0)} – ${V.fmt(L.t1)}</div><div style="display:flex;gap:3px">${ph.map(u => `<div style="flex:${(u.t1 - u.t0) / span} 0 0;min-width:0"><div class="vnode${sel().a <= u.a && sel().b >= u.b ? ' sel' : ''}" data-sel="${u.a}.${u.b}" style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px">${esc(u.text)}</div></div>`).join('')}</div>
  <div style="display:flex;gap:3px;margin-top:10px;background:var(--box);padding:4px;border-radius:3px">${ph.map(u => { const m = mineIn(u); const r = m || ghost(u, used); if (r && !m) used.add(r.s.id); return `<div style="flex:${(u.t1 - u.t0) / span} 0 0;min-width:0;opacity:${m ? 1 : .5}">${r ? h.t(r, at(u, { w: '100%', grade: false, cls: m ? 'mine' : '', style: 'aspect-ratio:auto;height:' + W(o, 48, 90) + 'px' })) : ''}</div>`; }).join('')}</div>
  <div style="display:flex;justify-content:space-between;font:500 10px var(--mono);color:var(--dim);margin-top:4px"><span>←</span><span>${ph.length} phrases on one lane</span><span>→</span></div>`;
});
R('157', 'Hinged Card', 'Each line as a card that opens like a book: words on the left page, the shot on the right. Turn the pages.', (box, v, o) => {
  const st = h.state('157', {}); const P = V.around('stanza'); const lines = V.unitsIn(P.a, P.b, 'line');
  let i = lines.findIndex(u => sel().a >= u.a && sel().a <= u.b); if (i < 0) i = 0;
  const u = lines[i]; const m = mineIn(u); const r = m || ghost(u); void st;
  box.innerHTML = `<div class="v3d" style="display:flex;justify-content:center"><div style="display:grid;grid-template-columns:1fr 1fr;width:${W(o, 330, 720)}px;max-width:100%;border:1.5px solid var(--ink);border-radius:4px;background:var(--panel);box-shadow:0 8px 20px #0002"><div style="padding:${W(o, 12, 24)}px;border-right:3px double var(--rule);transform:rotateY(8deg);transform-origin:right"><div class="vlab">line ${i + 1} of ${lines.length}</div><div class="vtext" style="font-size:${W(o, 14, 20)}px">${esc(u.text)}</div></div><div style="padding:${W(o, 10, 20)}px;display:flex;flex-direction:column;gap:6px;justify-content:center">${r ? h.t(r, { w: '100%', cls: m ? 'mine' : '' }) : ''}<small style="color:${m ? 'var(--blue)' : 'var(--dim)'}">${m ? 'coupled · ' : 'suggested · '}${r ? esc(r.s.title) : ''}</small>${!m && r ? `<button class="vbtn on" data-take>couple this page</button>` : ''}</div></div></div>
  <div class="vbar" style="justify-content:center;margin-top:12px"><button class="vbtn" data-p="-1">‹ page</button><button class="vbtn" data-p="1">page ›</button></div>`;
  box.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { const n = lines[(i + +b.dataset.p + lines.length) % lines.length]; V.setSel({ a: n.a, b: n.b }); });
  const tk = box.querySelector('[data-take]'); if (tk) tk.onclick = () => V.coupleTo(r.s, u.a, u.b, r.in);
});
R('158', 'Word to Frame', 'The word you hold, and the frame the film shows while it is spoken.', (box, v, o) => {
  const w = S().words[sel().a]; const seg = V.segAt(w.t0 + 0.01); const sh = seg && shotOfSeg(seg);
  box.innerHTML = `<div style="text-align:center"><span class="vnode sel" style="font-size:${W(o, 15, 22)}px" data-w>${esc(w.text)}</span><div class="vnote" style="margin:4px 0 30px">${V.fmt(w.t0)} · ${(w.t1 - w.t0).toFixed(2)} s</div></div><div style="max-width:${W(o, 260, 560)}px;margin:0 auto">${sh ? h.ts(sh, { w: '100%', in: seg.off, cls: seg.kind === 'mine' ? 'mine' : '' }) : `<div class="vx none" style="--w:100%;display:flex;align-items:center;justify-content:center;font:900 20px var(--sans);text-transform:uppercase">${esc(seg ? seg.text : '')}</div>`}<div class="vcap" style="--w:100%">${seg ? (seg.kind === 'mine' ? 'your shot · ' : seg.kind === 'base' ? S().base + ' cut · ' : 'text card') + esc(sh ? sh.title : '') : ''}</div></div>`;
  h.arrows(box, [[box.querySelector('[data-w]'), box.querySelector('.vx')]], { color: 'var(--blue)' });
});
R('160', 'Overlay Anchor', 'The shot with its words laid over it, anchored where they are spoken.', (box, v, o) => {
  const u = selR(); const m = mineIn(u); const r = m || o.list[0]; if (!r) return;
  box.innerHTML = `<div style="position:relative;max-width:${W(o, 360, 760)}px;margin:0 auto">${h.t(r, { w: '100%', cls: m ? 'mine' : '' })}<div style="position:absolute;left:6%;right:6%;bottom:8%;pointer-events:none;text-align:center;font:600 ${W(o, 14, 22)}px/1.3 var(--sans);color:#fff;text-shadow:0 1px 4px #000,0 0 10px #000">${esc(h.q(120))}</div><span style="position:absolute;left:50%;bottom:calc(8% + 2.6em);width:2px;height:22px;background:var(--blue);pointer-events:none"></span><span style="position:absolute;left:calc(50% - 6px);bottom:calc(8% + 2.6em + 18px);width:12px;height:12px;border-radius:50%;border:2px solid var(--blue);background:#fff;pointer-events:none"></span></div><div class="vnote" style="text-align:center;margin-top:8px">${m ? 'Your coupling.' : 'The archive’s first answer; double-click it to couple.'}</div>`;
});
R('164', 'Stack Bind', 'The words bracketed against a stack of candidate shots. Click one in the stack to couple it.', (box, v, o) => {
  const u = selR(); const l = o.list.slice(0, W(o, 4, 6));
  box.innerHTML = `<div style="display:grid;grid-template-columns:minmax(0,1fr) 34px ${W(o, 130, 220)}px;gap:0 10px;align-items:center"><div class="vtext" style="font-size:${W(o, 15, 20)}px;text-align:right">${esc(h.q(160))}</div><svg viewBox="0 0 30 100" preserveAspectRatio="none" style="width:30px;height:100%;min-height:${l.length * 40}px"><path d="M2 2 H14 V46 L26 50 L14 54 V98 H2" fill="none" stroke="var(--blue)" stroke-width="2" vector-effect="non-scaling-stroke"/></svg><div class="vcol" style="gap:6px">${l.map(r => h.t(r, at(u, { w: W(o, 130, 220) }))).join('')}</div></div>`;
});
R('165', 'Drag to Couple', 'Drag a shot onto a line to couple it there. On a phone: tap a shot, then tap the line.', (box, v, o) => {
  const st = h.state('165', {}); const P = V.around('stanza'); const lines = V.unitsIn(P.a, P.b, 'line'); const l = h.top(o, 10, 20);
  box.innerHTML = `<div class="vrow" style="gap:6px;margin-bottom:16px">${l.map(r => `<span draggable="true" data-drag="${esc(r.s.id)}" data-din="${r.in}" style="cursor:grab;${st.pick === r.s.id ? 'outline:3px solid var(--blue);outline-offset:1px;' : ''}">${h.ts(r.s, { w: W(o, 58, 84), grade: false }).replace('data-id=', 'data-nid=')}</span>`).join('')}</div>${lines.map(u => { const m = mineIn(u); return `<div data-drop="${u.a}.${u.b}" style="display:grid;grid-template-columns:minmax(0,1fr) ${W(o, 58, 84)}px;gap:10px;align-items:center;border:1.5px dashed var(--rule);border-radius:4px;padding:6px 10px;margin-bottom:6px;background:var(--panel)"><span class="vtext" style="font-size:${W(o, 13.5, 16)}px">${esc(u.text)}</span>${m ? h.ts(m.s, { w: W(o, 58, 84), in: m.in, cls: 'mine', grade: false }) : slot(W(o, 58, 84), 'drop here')}</div>`; }).join('')}`;
  const pick = new Map(l.map(r => [r.s.id, r]));
  box.querySelectorAll('[data-drag]').forEach(d => {
    d.addEventListener('dragstart', e => { e.dataTransfer.setData('text/plain', d.dataset.drag); e.dataTransfer.effectAllowed = 'link'; });
    d.addEventListener('click', e => { e.stopPropagation(); st.pick = st.pick === d.dataset.drag ? null : d.dataset.drag; const r = pick.get(d.dataset.drag); if (r) V.preview(r.s, r.in); box.querySelectorAll('[data-drag]').forEach(x => x.style.outline = x.dataset.drag === st.pick ? '3px solid var(--blue)' : ''); });
  });
  box.querySelectorAll('[data-drop]').forEach(z => {
    const [a, b] = z.dataset.drop.split('.').map(Number);
    z.addEventListener('dragover', e => { e.preventDefault(); z.style.borderColor = 'var(--blue)'; z.style.background = 'var(--blue-soft)'; });
    z.addEventListener('dragleave', () => { z.style.borderColor = ''; z.style.background = 'var(--panel)'; });
    z.addEventListener('drop', e => { e.preventDefault(); const r = pick.get(e.dataTransfer.getData('text/plain')); if (r) V.coupleTo(r.s, a, b, r.in); });
    z.addEventListener('click', e => { if (e.target.closest('.vx:not(.none)')) return; if (!st.pick) { V.setSel({ a, b }); return; } const r = pick.get(st.pick); st.pick = null; if (r) V.coupleTo(r.s, a, b, r.in); });
  });
});
R('167', 'Column Align', 'Each word in a column, lined up with the shot the film shows while it is spoken.', (box, v, o) => {
  const L = V.around('line'); const ws = words(L).slice(0, 40);
  box.innerHTML = `<div style="display:grid;grid-template-columns:${W(o, 110, 180)}px 60px ${W(o, 64, 96)}px 1fr;gap:3px 10px;align-items:center">${ws.map(w => { const seg = V.segAt(w.t0 + 0.01); const sh = seg && shotOfSeg(seg); return `<span class="vnode${w.i >= sel().a && w.i <= sel().b ? ' sel' : ''}" data-sel="${w.i}.${w.i}" style="text-align:left">${esc(w.text)}</span><small style="font:500 10px var(--mono);color:var(--dim)">${V.fmt(w.t0)}</small>${sh ? h.ts(sh, { w: W(o, 64, 96), in: seg.off, grade: false, cls: seg.kind === 'mine' ? 'mine' : '' }) : slot(W(o, 64, 96), seg && seg.text)}<small style="color:var(--dim);overflow:hidden;white-space:nowrap;text-overflow:ellipsis">${sh ? esc(sh.title) : ''}</small>`; }).join('')}</div>`;
});
R('168', 'Bridge Bar', 'The stanza’s lines above, the film’s shots below, on one clock: where a cut falls mid-line, the bar bridges it.', (box, v, o) => {
  const P = V.around('stanza'); const lines = V.unitsIn(P.a, P.b, 'line'); const segs = S().segs.filter(s => s.t1 > P.t0 && s.t0 < P.t1); const span = P.t1 - P.t0 || 1; const x = t => ((Math.max(P.t0, Math.min(P.t1, t)) - P.t0) / span * 100).toFixed(2);
  const bridges = segs.slice(1).filter(s => lines.some(u => s.t0 > u.t0 + 0.3 && s.t0 < u.t1 - 0.3));
  box.innerHTML = `<div style="position:relative;height:${W(o, 70, 60)}px">${lines.map(u => `<div data-sel="${u.a}.${u.b}" style="position:absolute;left:${x(u.t0)}%;width:calc(${x(u.t1) - x(u.t0)}% - 2px);top:0;bottom:0;border:1.5px solid ${sel().a >= u.a && sel().a <= u.b ? 'var(--blue)' : 'var(--ink)'};background:var(--panel);padding:3px 5px;overflow:hidden;font:400 ${W(o, 10.5, 12)}px/1.25 var(--sans);cursor:pointer">${esc(u.text)}</div>`).join('')}</div>
  <div style="position:relative;height:18px">${bridges.map(s => `<span style="position:absolute;left:${x(s.t0)}%;top:2px;bottom:2px;width:3px;background:var(--red);transform:translateX(-1px)" title="cut at ${V.fmt(s.t0)} falls inside a line"></span>`).join('')}<div style="position:absolute;left:0;right:0;top:8px;border-top:3px solid var(--blue)"></div></div>
  <div style="position:relative;height:${W(o, 50, 80)}px">${segs.map(s => { const sh = shotOfSeg(s); return `<div style="position:absolute;left:${x(s.t0)}%;width:calc(${x(s.t1) - x(s.t0)}% - 2px);top:0;bottom:0">${sh ? h.ts(sh, { in: s.off, grade: false, cls: s.kind === 'mine' ? 'mine' : '', style: '--w:100%;aspect-ratio:auto;height:100%;border-width:1px' }) : slot(10)}</div>`; }).join('')}</div>
  ${h.note(`${lines.length} lines, ${segs.length} shots; <b style="color:var(--red)">${bridges.length}</b> cut${bridges.length === 1 ? '' : 's'} fall inside a line (red).`)}`;
});
R('169', 'Context Panel', 'Everything known about the moment you hold: the beat’s treatment, its signs, the world, the moods.', (box, v, o) => {
  const s0 = sel(); const f = S().films[S().words[s0.a].film]; const bs = V.beatsIn(s0.t0, s0.t1); const wd = f.world || {};
  box.innerHTML = `<div style="display:grid;grid-template-columns:${o.wide ? 'minmax(0,1.2fr) minmax(0,1fr)' : '1fr'};gap:14px"><div class="vframe"><div class="vlab">what you hold · ${V.kindOf(s0)}</div><div class="vtext" style="font-size:${W(o, 15, 19)}px">${esc(h.q(300))}</div><div class="vrow" style="margin-top:10px;gap:5px">${o.list.slice(0, W(o, 5, 8)).map(r => h.t(r, { w: W(o, 54, 76) })).join('')}</div></div>
  <div style="display:flex;flex-direction:column;gap:10px">${bs.slice(0, 2).map(b => `<div class="vframe"><div class="vlab">beat ${b.id} · ${esc(b.mode)}</div><b style="font:700 14px/1.25 var(--sans)">${esc(b.title)}</b><p style="font-size:12px;margin:6px 0">${esc(b.operation || '')}</p><p style="font-size:12px;margin:0 0 6px;color:var(--dim)"><b>edit</b> ${esc(b.edit || '')}</p><div class="signs">${V.signChips(b.codes)}</div></div>`).join('')}
  <div class="vframe"><div class="vlab">${esc(f.n + ' ' + f.title)}</div><p style="font-size:12px;margin:0 0 6px">${esc(wd.logline || wd.tagline || '')}</p><div class="vrow" style="gap:4px">${(wd.moods || []).map(m => `<span class="vnode dim" style="font-size:11px">${esc(m)}</span>`).join('')}</div></div></div></div>`;
});
R('171', 'Word Menu', 'The menu the sheet draws on a word: play it, find what is like it, add it to the film.', (box, v, o) => {
  const u = selR(); const r = o.list[0]; const k = V.selTerms()[0] || '';
  box.innerHTML = `<div style="display:flex;justify-content:center;gap:24px;flex-wrap:wrap;align-items:flex-start"><div style="text-align:center"><span class="vnode sel" style="font-size:${W(o, 15, 20)}px" data-anchor>${esc(h.q(50))}</span></div><div class="vframe" style="min-width:210px;padding:4px 0;box-shadow:0 8px 20px #0002" data-menu>${[['play', '▷ play it'], ['loop', '⟲ loop it'], ['similar', '≈ find similar' + (k ? ' to “' + esc(k) + '”' : '')], ['add', '＋ add to film' + (r ? ' · ' + esc(r.s.title.slice(0, 22)) : '')], ['wider', '[ ] hold more'], ['lift', '✕ lift its coupling']].map(([a, l]) => `<button data-m="${a}" style="display:block;width:100%;text-align:left;background:none;border:0;padding:6px 14px;cursor:pointer;font:inherit;font-size:12.5px;color:var(--ink)" onmouseover="this.style.background='var(--blue-soft)'" onmouseout="this.style.background='none'">${l}</button>`).join('')}</div></div>`;
  wire(box, [[box.querySelector('[data-anchor]'), box.querySelector('[data-menu]'), { mode: 'h', dash: true }]]);
  box.querySelectorAll('[data-m]').forEach(b => b.onclick = () => { const a = b.dataset.m; if (a === 'play') V.playSel(false); else if (a === 'loop') V.playSel(true); else if (a === 'similar') { const q = document.getElementById('q'); q.value = k; q.dispatchEvent(new Event('input')); } else if (a === 'add' && r) V.coupleTo(r.s, u.a, u.b, r.in); else if (a === 'wider') document.dispatchEvent(new KeyboardEvent('keydown', { key: ']' })); else if (a === 'lift') V.liftSel(); });
});
R('172', 'Phrase Rail', 'The stanza’s phrases on a rail; step along it, and the shots for the phrase you are on come with you.', (box, v, o) => {
  const P = V.around('stanza'); const ph = V.unitsIn(P.a, P.b, 'phrase'); let i = ph.findIndex(u => sel().a >= u.a && sel().a <= u.b); if (i < 0) i = 0; const u = ph[i];
  box.innerHTML = `<div style="display:flex;align-items:center;gap:6px"><button class="vbtn" data-p="-1">‹</button><div class="vrow nw" style="flex:1;gap:4px;border-top:2px solid var(--ink);border-bottom:2px solid var(--ink);padding:6px 4px" data-rail>${ph.map((x, k) => `<span class="vnode${k === i ? ' sel' : ''}" data-sel="${x.a}.${x.b}" data-k="${k}" style="flex:none;white-space:nowrap;font-size:12px">${esc(x.text)}</span>`).join('')}</div><button class="vbtn" data-p="1">›</button></div><div class="vrow" style="justify-content:center;margin-top:34px">${V.results(u, 'all').slice(0, W(o, 4, 7)).map(r => h.t(r, at(u, { w: W(o, 70, 120) }))).join('')}</div>`;
  const on = box.querySelector(`[data-k="${i}"]`); requestAnimationFrame(() => on && on.scrollIntoView({ block: 'nearest', inline: 'center' }));
  box.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { const n = ph[(i + +b.dataset.p + ph.length) % ph.length]; V.setSel({ a: n.a, b: n.b }); });
  wire(box, [...box.querySelectorAll('.vrow:not([data-rail]) .vx')].map(x => [on, x, { color: 'var(--blue)', dash: '3 3' }]));
});
R('174', 'Swap Shot', 'What plays under your words now, and the shots that could take its place. Click one to swap it in.', (box, v, o) => {
  const u = selR(); const m = mineIn(u); const seg = V.segAt(u.t0 + 0.01); const cur = m ? m.s : seg && shotOfSeg(seg); const alts = o.list.filter(r => !cur || r.s.id !== cur.id).slice(0, W(o, 4, 8));
  box.innerHTML = `<div style="display:flex;gap:${W(o, 16, 40)}px;align-items:center;justify-content:center;flex-wrap:wrap"><div class="vcol"><div class="vlab">now</div>${cur ? h.ts(cur, { w: W(o, 140, 240), in: m ? m.in : seg.off, cls: m ? 'mine' : '' }) : slot(W(o, 140, 240), 'text card')}<span class="vcap" style="--w:${W(o, 140, 240)}px">${cur ? esc(cur.title) : ''}<small>${m ? 'your coupling' : 'the ' + S().base + ' cut'}</small></span></div><div style="font-size:26px;color:var(--blue)">⇄</div><div><div class="vlab">swap for</div><div class="vrow" style="max-width:${W(o, 160, 440)}px">${alts.map(r => h.t(r, at(u, { w: W(o, 70, 100) }))).join('')}</div></div></div>`;
});
R('175', 'Multi-Link', 'The four cuts’ answers for the same words, linked at once: suite, scenes, cineosis, drift.', (box, v, o) => {
  const u = selR(); const cuts = ['suite', 'scenes', 'cineosis', 'drift'];
  box.innerHTML = `<div style="text-align:center">${h.hub('', 80)}</div><div class="vrow" style="justify-content:center;gap:${W(o, 8, 26)}px;margin-top:40px">${cuts.map(c => { const p = V.cutAt(c, u.t0 + 0.01); const s = p && (V.shot(p.id) || p); return `<div class="vcol">${s ? h.ts(s, { ...at(u), w: W(o, 70, 170), in: p.in + Math.max(0, u.t0 - p.t0) }) : slot(W(o, 70, 170))}<span class="vcap" style="--w:${W(o, 70, 170)}px;color:var(--blue)">${c}<small>${s ? esc(s.title) : ''}</small></span></div>`; }).join('')}</div>`;
  const hub = box.querySelector('.hub'); wire(box, [...box.querySelectorAll('.vx')].map(x => [hub, x, { color: 'var(--blue)' }]));
});
R('177', 'Pin to Shot', 'Pin the words to an exact moment inside the shot: scrub to the frame you want, then pin.', (box, v, o) => {
  const u = selR(); const pv = S().pv; const r = pv ? { s: V.shot(pv.id) || pv, in: pv.in || 0 } : o.list[0]; if (!r) return;
  const dur = r.s.dur || 30;
  box.innerHTML = `<div style="max-width:${W(o, 340, 640)}px;margin:0 auto"><video muted playsinline preload="metadata" src="${esc(r.s.video)}" style="width:100%;aspect-ratio:16/9;background:#000;border:1.5px solid var(--ink);display:block"></video><input type="range" min="0" max="${dur.toFixed(2)}" step="0.1" value="${(+r.in || 0).toFixed(1)}" style="width:100%;margin:8px 0"><div class="vbar"><span style="font:500 12px var(--mono)" data-tc>in ${(+r.in || 0).toFixed(1)} s</span><span class="grow"></span><button class="vbtn on" data-pin>📌 pin “${esc(h.q(30))}” here</button></div>${h.note('<b>' + esc(r.s.title) + '</b> · the words start the shot at this frame.')}</div>`;
  const vid = box.querySelector('video'), rg = box.querySelector('input'), tc = box.querySelector('[data-tc]');
  const set = () => { try { vid.currentTime = +rg.value; } catch (e) { /* not loaded yet */ } tc.textContent = 'in ' + (+rg.value).toFixed(1) + ' s'; };
  vid.addEventListener('loadedmetadata', () => { rg.max = vid.duration.toFixed(2); set(); }, { once: true });
  rg.oninput = set;
  box.querySelector('[data-pin]').onclick = () => V.coupleTo(r.s, u.a, u.b, +rg.value);
});
R('178', 'Flow Chain', 'The line as a chain: phrase, shot, phrase, shot, each passing to the next.', (box, v, o) => {
  const L = V.around('line'); const ph = V.unitsIn(L.a, L.b, 'phrase'); const used = V.used();
  box.innerHTML = `<div class="vrow" style="align-items:center;gap:${W(o, 14, 26)}px;row-gap:22px">${ph.map(u => { const m = mineIn(u); const r = m || ghost(u, used); if (r && !m) used.add(r.s.id); return `<span class="vnode" data-sel="${u.a}.${u.b}" data-c>${esc(u.text)}</span>${r ? `<span data-c style="opacity:${m ? 1 : .55}">${h.t(r, at(u, { w: W(o, 56, 90), grade: false, cls: m ? 'mine' : '' }))}</span>` : ''}`; }).join('')}</div>`;
  const cs = [...box.querySelectorAll('[data-c]')]; h.arrows(box, cs.slice(1).map((c, i) => [cs[i], c]), { mode: 'h', color: 'var(--blue)' });
});
R('180', 'Arc Connect', 'Arcs from the words above to the shots below them, one per phrase.', (box, v, o) => {
  const L = V.around('line'); const ph = V.unitsIn(L.a, L.b, 'phrase'); const used = V.used();
  const pairs = ph.map(u => { const r = mineIn(u) || ghost(u, used); if (r) used.add(r.s.id); return { u, r }; });
  box.innerHTML = `<div class="vrow" style="justify-content:center;gap:10px">${pairs.map(({ u }, i) => `<span class="vnode" data-sel="${u.a}.${u.b}" data-w="${i}">${esc(u.text)}</span>`).join('')}</div><div class="vrow" style="justify-content:center;gap:${W(o, 10, 22)}px;margin-top:${W(o, 60, 90)}px">${pairs.slice().reverse().map(({ u, r }, k) => `<span data-s="${pairs.length - 1 - k}">${r ? h.t(r, at(u, { w: W(o, 60, 100), grade: false })) : ''}</span>`).join('')}</div>`;
  wire(box, pairs.map((p, i) => [box.querySelector(`[data-w="${i}"]`), box.querySelector(`[data-s="${i}"] .vx`), { color: 'var(--blue)', w: 1.5 }]));
});
R('182', 'Matrix Bind', 'Lines down the side, the four cuts and your couplings across: a matrix of every shot each line has had. Click a cell to couple it.', (box, v, o) => {
  const P = V.around('stanza'); const lines = V.unitsIn(P.a, P.b, 'line'); const cols = ['mine', 'suite', 'scenes', 'cineosis', 'drift']; const cw = W(o, 46, 96);
  box.innerHTML = `<div style="display:grid;grid-template-columns:minmax(0,1fr) repeat(5,${cw}px);gap:4px 6px;align-items:center"><span></span>${cols.map(c => `<span class="vlab" style="text-align:center;margin:0;overflow:hidden;letter-spacing:${o.wide ? '.09em' : '0'};color:${c === 'mine' ? 'var(--blue)' : ''}">${o.wide ? c : { mine: 'mine', suite: 'suite', scenes: 'scene', cineosis: 'cine', drift: 'drift' }[c]}</span>`).join('')}${lines.map(u => `<span data-sel="${u.a}.${u.b}" style="cursor:pointer;font:400 ${W(o, 12, 14)}px/1.3 var(--sans);padding:3px 4px;border-radius:3px;${sel().a >= u.a && sel().a <= u.b ? 'background:var(--blue-soft)' : ''}">${esc(u.text)}</span>${cols.map(c => { if (c === 'mine') { const m = mineIn(u); return m ? h.ts(m.s, { w: cw, in: m.in, cls: 'mine', grade: false }) : slot(cw, '—'); } const p = V.cutAt(c, u.t0 + 0.05); const s = p && (V.shot(p.id) || p); return s ? h.ts(s, { ...at(u), w: cw, in: p.in + Math.max(0, u.t0 - p.t0), grade: false }) : slot(cw); }).join('')}`).join('')}</div>`;
});
R('185', 'Fork Couple', 'The words fork two ways; take the left shot or the right one.', (box, v, o) => {
  const u = selR(); const [A, B] = o.list;
  box.innerHTML = `<div style="text-align:center">${h.hub('', 80)}</div><div style="display:flex;justify-content:space-between;max-width:${W(o, 320, 640)}px;margin:${W(o, 50, 70)}px auto 0">${[A, B].map((r, i) => r ? `<div class="vcol">${h.t(r, at(u, { w: W(o, 120, 230) }))}<span class="vcap" style="--w:${W(o, 120, 230)}px">${i ? 'right' : 'left'} · ${esc(r.s.title)}</span></div>` : '').join('')}</div>`;
  const hub = box.querySelector('.hub'); wire(box, [...box.querySelectorAll('.vx')].map(x => [hub, x, { color: 'var(--blue)', w: 1.8 }]));
});
R('186', 'Clip Basket', 'Gather shots into a basket, then pour it over the words: the words are shared out evenly among them, in order.', (box, v, o) => {
  const st = h.state('186', { ids: [] }); const u = selR(); const l = h.top(o, 12, 24); const bw = W(o, 60, 90);
  const basket = st.ids.map(id => V.shot(id)).filter(Boolean);
  box.innerHTML = `<div class="vlab">shots · click + to put one in the basket</div><div class="vrow" style="gap:6px">${l.map(r => `<span style="position:relative">${h.t(r, { w: W(o, 60, 84), grade: false })}<button class="vbtn" data-add="${esc(r.s.id)}" style="position:absolute;right:-4px;bottom:-4px;padding:0 5px;border-radius:50%;z-index:3">${st.ids.includes(r.s.id) ? '✓' : '+'}</button></span>`).join('')}</div>
  <div style="margin-top:16px;border:2px dashed var(--ink);border-radius:10px;padding:10px 12px;background:var(--panel)"><div class="vlab">the basket · ${basket.length}</div><div class="vrow" style="gap:6px;min-height:${bw * 0.75}px">${basket.map((s, i) => `<span style="position:relative">${h.ts(s, { w: bw, grade: false, label: String(i + 1) })}<button class="vbtn" data-rm="${i}" style="position:absolute;right:-4px;top:-4px;padding:0 5px;border-radius:50%;z-index:3">×</button></span>`).join('')}</div></div>
  <div class="vbar" style="margin-top:10px"><button class="vbtn on" data-pour ${basket.length && S().sel ? '' : 'disabled'}>pour over “${esc(h.q(40))}” (${u.b - u.a + 1} words)</button><button class="vbtn" data-empty>empty</button></div>`;
  box.querySelectorAll('[data-add]').forEach(b => b.onclick = e => { e.stopPropagation(); const id = b.dataset.add; st.ids = st.ids.includes(id) ? st.ids.filter(x => x !== id) : st.ids.concat(id); V.rerender(); });
  box.querySelectorAll('[data-rm]').forEach(b => b.onclick = e => { e.stopPropagation(); st.ids.splice(+b.dataset.rm, 1); V.rerender(); });
  box.querySelector('[data-empty]').onclick = () => { st.ids = []; V.rerender(); };
  box.querySelector('[data-pour]').onclick = () => {
    const n = Math.min(basket.length, u.b - u.a + 1); const per = (u.b - u.a + 1) / n; const keep = { a: u.a, b: u.b };
    for (let k = 0; k < n; k++) { const a = u.a + Math.round(k * per), b = u.a + Math.round((k + 1) * per) - 1; V.coupleTo(basket[k], a, Math.max(a, b), basket[k].in || 0); }
    V.setSel(keep); V.toast(`Poured ${n} shots over ${u.b - u.a + 1} words.`);
  };
});
R('190', 'List Couple', 'Tick lines in the list, then click a shot: it is coupled to every ticked line.', (box, v, o) => {
  const st = h.state('190', { on: new Set() }); const P = V.around(o.wide ? 'passage' : 'stanza'); const lines = V.unitsIn(P.a, P.b, 'line');
  const keys = new Set(lines.map(u => u.a + '.' + u.b)); [...st.on].forEach(k => { if (!keys.has(k)) st.on.delete(k); });
  box.innerHTML = `<div style="display:grid;grid-template-columns:${o.wide ? 'minmax(0,1fr) 360px' : '1fr'};gap:16px"><div>${lines.map(u => { const k = u.a + '.' + u.b; const m = mineIn(u); return `<label style="display:grid;grid-template-columns:20px minmax(0,1fr) 44px;gap:8px;align-items:center;padding:4px 0;border-top:1px solid var(--rule);cursor:pointer"><input type="checkbox" data-k="${k}" ${st.on.has(k) ? 'checked' : ''}><span style="font:400 13px/1.3 var(--sans)">${esc(u.text)}</span>${m ? h.ts(m.s, { w: 44, in: m.in, cls: 'mine', grade: false }) : '<span></span>'}</label>`; }).join('')}</div><div><div class="vlab">${st.on.size} line${st.on.size === 1 ? '' : 's'} ticked · click a shot</div><div class="vrow" data-pick>${h.top(o, 9, 18).map(r => h.t(r, { w: W(o, 66, 80) }).replace('data-id=', 'data-lid=')).join('')}</div></div></div>`;
  box.querySelectorAll('[data-k]').forEach(c => c.onchange = () => { c.checked ? st.on.add(c.dataset.k) : st.on.delete(c.dataset.k); V.rerender(); });
  box.querySelectorAll('[data-lid]').forEach(b => b.onclick = () => { const s = V.shot(b.dataset.lid); if (!st.on.size) { V.preview(s, +b.dataset.in); V.toast('Tick one or more lines first.'); return; } const ks = [...st.on]; st.on.clear(); ks.forEach(k => { const [a, bb] = k.split('.').map(Number); V.coupleTo(s, a, bb, +b.dataset.in); }); V.toast(`Coupled ${s.title} to ${ks.length} line${ks.length > 1 ? 's' : ''}.`); });
});
R('191', 'Timeline Couple', 'The words on a clock with a tick for each; your couplings sit beneath them. Click a shot to couple it to what you hold.', (box, v, o) => {
  const L = V.around('line'); const t0 = L.t0, span = (L.t1 - L.t0) || 1; const ws = words(L); const x = t => ((t - t0) / span * 100).toFixed(2);
  const bs = V.bindsIn(L.t0, L.t1);
  box.innerHTML = `<div style="position:relative;height:30px">${ws.map(w => `<span data-sel="${w.i}.${w.i}" style="position:absolute;left:${x(w.t0)}%;bottom:2px;font:400 ${W(o, 10, 13)}px var(--sans);cursor:pointer;white-space:nowrap;color:${w.i >= sel().a && w.i <= sel().b ? 'var(--blue)' : 'var(--ink)'};transform-origin:left bottom;transform:rotate(-${o.wide ? 0 : 30}deg)">${esc(w.text)}</span>`).join('')}</div>
  <div style="position:relative;height:12px;border-top:1.5px solid var(--ink)">${ws.map(w => `<i style="position:absolute;left:${x(w.t0)}%;top:0;height:8px;border-left:1px solid var(--ink)"></i>`).join('')}<i class="vspan" style="top:-40px;height:52px;left:${x(Math.max(t0, sel().t0))}%;width:${x(Math.min(L.t1, sel().t1)) - x(Math.max(t0, sel().t0))}%"></i></div>
  <div style="position:relative;height:${W(o, 44, 70)}px;background:var(--box)">${bs.map(b => `<div style="position:absolute;left:${x(Math.max(t0, b.t0))}%;width:${x(Math.min(L.t1, b.t1)) - x(Math.max(t0, b.t0))}%;top:0;bottom:0">${h.ts(V.shot(b.shot.id) || b.shot, { in: b.in, cls: 'mine', grade: false, style: '--w:100%;aspect-ratio:auto;height:100%' })}</div>`).join('')}</div>
  <div class="vruler"><span style="left:0">${V.fmt(t0)}</span><span style="left:90%">${V.fmt(L.t1)}</span></div><div class="vlab" style="margin-top:14px">couple to the blue span</div><div class="vrow">${h.top(o, 6, 12).map(r => h.t(r, at(selR(), { w: W(o, 60, 84) }))).join('')}</div>`;
});
R('195', 'Span Map', 'Every coupling in the passage as a span over its words and its time.', (box, v, o) => {
  const fi = S().words[sel().a].film; const f = S().films[fi]; const t0 = f.container[0], span = f.container[1] - t0; const x = t => ((t - t0) / span * 100).toFixed(2);
  const bs = S().binds.filter(b => S().words[b.a].film === fi); const sts = f.stanzas.map(i => S().stanzas[i]);
  box.innerHTML = `<div class="vlab">${esc(f.n + ' ' + f.title)} · ${bs.length} coupling${bs.length === 1 ? '' : 's'}</div><div style="position:relative;height:22px">${sts.map(s => `<span data-sel="${s.a}.${s.b}" title="${esc(s.screen || '')}" style="position:absolute;left:${x(s.t0)}%;width:calc(${x(s.t1) - x(s.t0)}% - 1px);top:4px;height:12px;background:var(--faint);cursor:pointer"></span>`).join('')}</div>
  ${bs.map((b, k) => `<div style="position:relative;height:${W(o, 30, 40)}px;margin:3px 0"><div style="position:absolute;left:${x(b.t0)}%;width:max(${x(b.t1) - x(b.t0)}%,2px);top:0;bottom:0;border:1.5px solid var(--blue);background:var(--blue-soft)"></div><div style="position:absolute;left:min(${x(b.t0)}%, calc(100% - 260px));top:0;display:flex;gap:6px;align-items:center;height:100%;padding-left:4px">${h.ts(V.shot(b.shot.id) || b.shot, { w: W(o, 36, 50), in: b.in, grade: false })}<span data-sel="${b.a}.${b.b}" style="cursor:pointer;font:400 11.5px/1.2 var(--sans);white-space:nowrap;overflow:hidden;max-width:210px;text-overflow:ellipsis">“${esc(V.selText(b))}”</span></div></div>`).join('')}
  <div class="vruler">${[0, .25, .5, .75].map(k => `<span style="left:${k * 100}%">${V.fmt0(t0 + k * span)}</span>`).join('')}</div>${bs.length ? '' : h.note('Nothing coupled in this passage yet.')}`;
});
R('196', 'Crosslink', 'Shots the four cuts used more than once across the poem, each linked to the lines it sat under.', (box, v, o) => {
  const m = new Map(); Object.entries(V.D.cuts).forEach(([c, l]) => l.forEach(p => { const k = p.id; if (!m.has(k)) m.set(k, []); m.get(k).push({ c, p }); }));
  S().binds.forEach(b => { if (!m.has(b.shot.id)) m.set(b.shot.id, []); m.get(b.shot.id).push({ c: 'mine', p: { t0: b.t0, id: b.shot.id, in: b.in } }); });
  const multi = [...m.entries()].filter(([, l]) => new Set(l.map(x => Math.round(x.p.t0))).size > 1).sort((a, b) => b[1].length - a[1].length).slice(0, W(o, 6, 12));
  if (!multi.length) { box.innerHTML = h.note('No shot is used in more than one place yet.'); return; }
  box.innerHTML = multi.map(([id, l], k) => { const s = V.shot(id); return `<div style="display:grid;grid-template-columns:${W(o, 70, 110)}px minmax(0,1fr);gap:12px;align-items:center;border-top:1px solid var(--rule);padding:8px 0"><div data-src="${k}">${s ? h.ts(s, { w: W(o, 70, 110), grade: false }) : ''}</div><div class="vrow" style="gap:6px">${l.slice(0, 6).map(x => { const w = V.wordAt(x.p.t0 + 0.05) || S().words.find(y => y.t0 >= x.p.t0); const u = w && V.unitRange(w.i, 'line'); return `<span class="vnode${x.c === 'mine' ? ' sel' : ''}" data-to="${k}" ${u ? `data-sel="${u.a}.${u.b}"` : `data-seek="${x.p.t0}"`} style="font-size:11px;text-align:left;max-width:${W(o, 200, 260)}px"><small style="margin:0 4px 0 0">${x.c} ${V.fmt0(x.p.t0)}</small>${u ? esc(V.selText(u).slice(0, 60)) : ''}</span>`; }).join('')}</div></div>`; }).join('');
  const links = []; multi.forEach((x, k) => { const src = box.querySelector(`[data-src="${k}"] .vx`); box.querySelectorAll(`[data-to="${k}"]`).forEach(t => links.push([src, t, { mode: 'h', dash: '2 3' }])); }); wire(box, links);
}, { needs: 'text' });
R('198', 'Reassign', 'Move a coupling: pick one from the list and it moves, shot and in-point, onto the words you hold.', (box, v, o) => {
  const u = selR(); const bs = S().binds.slice().sort((a, b) => a.t0 - b.t0);
  box.innerHTML = `<div class="vframe" style="margin-bottom:12px;background:var(--blue-soft);border-color:var(--blue)"><div class="vlab">move to</div><div class="vtext" style="font-size:15px">“${esc(h.q(120))}”</div></div>${bs.length ? bs.map((b, i) => `<div class="vline" style="grid-template-columns:${W(o, 60, 90)}px minmax(0,1fr) auto;align-items:center">${h.ts(V.shot(b.shot.id) || b.shot, { w: W(o, 60, 90), in: b.in, grade: false })}<span style="min-width:0"><span data-sel="${b.a}.${b.b}" style="cursor:pointer;font:400 13px var(--sans)">“${esc(V.selText(b).slice(0, 90))}”</span><small style="display:block;color:var(--dim)">${V.fmt(b.t0)} · ${esc(b.shot.title)}</small></span><button class="vbtn on" data-mv="${i}">move here ↑</button></div>`).join('') : h.note('Nothing coupled yet to move.')}`;
  box.querySelectorAll('[data-mv]').forEach(btn => btn.onclick = () => { const b = bs[+btn.dataset.mv]; S().binds = S().binds.filter(x => x !== b); V.afterBinds(); V.coupleTo(V.shot(b.shot.id) || b.shot, u.a, u.b, b.in); });
});
R('199', 'Composite Bind', 'Several shots in one frame for the same words: a split, a picture in picture, a four-way.', (box, v, o) => {
  const st = h.state('199', { mode: 'quad' }); const l = o.list.slice(0, 4); const im = i => l[i] ? `background:url('${esc(l[i].s.thumb)}') center/cover` : 'background:var(--box)';
  const layouts = { quad: [[0, 0, 50, 50], [50, 0, 50, 50], [0, 50, 50, 50], [50, 50, 50, 50]], split: [[0, 0, 50, 100], [50, 0, 50, 100]], pip: [[0, 0, 100, 100], [62, 58, 34, 36]], strip: [[0, 0, 33.3, 100], [33.3, 0, 33.4, 100], [66.7, 0, 33.3, 100]] };
  box.innerHTML = `<div class="vbar">${h.vbtns([['quad', 'four-way'], ['split', 'split screen'], ['pip', 'picture in picture'], ['strip', 'three-up']], st.mode, 'cm')}</div><div style="position:relative;max-width:${W(o, 360, 760)}px;aspect-ratio:16/9;margin:0 auto;background:#000;border:1.5px solid var(--ink)">${layouts[st.mode].map((q, i) => `<div data-id="${l[i] ? esc(l[i].s.id) : ''}" data-in="${l[i] ? l[i].in : 0}" style="position:absolute;left:${q[0]}%;top:${q[1]}%;width:${q[2]}%;height:${q[3]}%;${im(i)};border:1px solid #000;${st.mode === 'pip' && i ? 'border:2px solid #fff;box-shadow:0 4px 12px #000a;' : ''}cursor:pointer"></div>`).join('')}<div style="position:absolute;left:0;right:0;bottom:6%;text-align:center;color:#fff;font:600 ${W(o, 12, 17)}px var(--sans);text-shadow:0 1px 4px #000;pointer-events:none">${esc(h.q(80))}</div></div>${h.note('A sketch of the composite; the player itself cuts one shot at a time. Click a panel to look at its shot.')}`;
  box.querySelectorAll('[data-cm]').forEach(b => b.onclick = () => { st.mode = b.dataset.cm; V.rerender(); });
});
R('200', 'Release to Film', 'The stanza’s shots, as they stand, carried onto the film.', (box, v, o) => {
  const P = V.around('stanza'); const segs = S().segs.filter(s => s.t1 > P.t0 && s.t0 < P.t1);
  box.innerHTML = `<div style="display:flex;align-items:center;gap:${W(o, 8, 20)}px;justify-content:center;flex-wrap:wrap"><div class="vrow" style="gap:3px;max-width:${W(o, 190, 460)}px">${segs.map(s => { const sh = shotOfSeg(s); return sh ? h.ts(sh, { w: W(o, 42, 70), in: s.off, grade: false, cls: s.kind === 'mine' ? 'mine' : '' }) : slot(W(o, 42, 70), '▭'); }).join('')}</div><span style="font-size:28px">→</span><div style="background:#141414;padding:${W(o, 8, 12)}px 4px;border-radius:3px;display:flex;gap:2px;position:relative">${segs.slice(0, 6).map(s => { const sh = shotOfSeg(s); return `<i style="display:block;width:${W(o, 30, 54)}px;aspect-ratio:4/3;background:${sh ? `url('${esc(sh.thumb)}') center/cover` : '#333'}"></i>`; }).join('')}</div></div><div class="vbar" style="justify-content:center;margin-top:14px"><button class="vbtn on" data-play>▷ play the stanza</button></div>`;
  box.querySelector('[data-play]').onclick = () => { V.setSel({ a: P.a, b: P.b }, { seek: false }); V.playSel(false); };
});
})();
