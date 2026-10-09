/* LUDENS — what the ball games share: the field of shots (corpus.json), the lab's cut score (as sea-core.js: a Gaussian of CLIP cosine
   around .72, from a calibrated 32-d PCA), pictures and flipbooks drawn without decoding video, and WATCH: a film played back as real
   video, shot after shot, from each shot's own in-point. */
(function (root) {
  const L = { root: '../', P: ['#5acde6', '#f06e64', '#f0cd46', '#aa82f0'], cards: [], byId: {}, holes: [], cal: [1, 0], sprites: null };
  L.load = () => fetch(L.root + 'ludens/corpus.json').then(r => r.json()).then(j => { L.signs = j.signs || []; L.SIGN = {}; L.signs.forEach(x => L.SIGN[x.s] = x); L.chapters = j.chapters || []; L.calf = j.calf || [1, 0]; L.holeIds = new Set(j.holes.map(h => h.id)); L.cards = j.cards; L.holes = j.holes; L.cal = j.cal; L.sprites = j.sprites; j.cards.forEach((c, i) => { c.i = i; L.byId[c.id] = c; }); return L; });
  L.cos = (a, b) => { let s = 0; for (let i = 0; i < 32; i++) s += a.e[i] * b.e[i]; return L.cal[0] * s / 16129 + L.cal[1]; };
  L.word = v => v >= .6 ? 'a good cut' : v >= .35 ? 'a loose cut' : 'a jarring cut';
  L.tint = v => v >= .6 ? '127,194,139' : v >= .35 ? '227,179,65' : '224,83,58';
  const imgs = {}, sheets = {};
  L.img = c => { if (!imgs[c.id]) { const im = new Image(); im.src = L.root + c.th; imgs[c.id] = im; } return imgs[c.id]; };
  L.sheet = n => { if (!sheets[n]) { const im = new Image(); im.src = L.root + L.sprites.path.replace('%03d', String(n).padStart(3, '0')); sheets[n] = im; } return sheets[n]; };
  L.draw = (ctx, c, x, y, w, h, frame) => {   /* the picture, or frame f of its flipbook; cover-cropped */
    if (frame != null && c.sp) { const S = L.sheet(c.sp[0]); if (S.complete && S.naturalWidth) { ctx.drawImage(S, (frame % 12) * 128, c.sp[1] * 72, 128, 72, x, y, w, h); return; } }
    const im = L.img(c); if (!im.complete || !im.naturalWidth) { ctx.fillStyle = '#1b1e22'; ctx.fillRect(x, y, w, h); return; }
    const r = Math.max(w / im.naturalWidth, h / im.naturalHeight), sw = w / r, sh = h / r; ctx.drawImage(im, (im.naturalWidth - sw) / 2, (im.naturalHeight - sh) / 2, sw, sh, x, y, w, h);
  };
  L.rng = seed => { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };

  /* ---- FILTER: which archives, worlds, chapters and eras are in play (every game); kept per browser */
  const FK = 'ludens-filter'; L.F = { kind: 'all', ch: [], w: [], era: [] };
  try { Object.assign(L.F, JSON.parse(localStorage.getItem(FK) || '{}')); } catch (e) { }
  const era = c => c.k === 'ai' ? 'AI' : c.y0 ? (Math.floor(c.y0 / 10) * 10) + 's' : 'undated';
  L.pool = (o = {}) => L.cards.filter(c => (L.F.kind === 'all' || c.k === L.F.kind) && (o.anyChapter || !L.F.ch.length || L.F.ch.includes(c.ch)) && (!L.F.w.length || L.F.w.includes(c.w)) && (!L.F.era.length || L.F.era.includes(era(c))));
  L.filterUI = (el, onchange) => {
    const worlds = [...new Set(L.cards.map(c => c.w))].filter(Boolean), eras = [...new Set(L.cards.map(era))].sort();
    const chip = (grp, v, lab, on) => `<button data-g="${grp}" data-v="${v}" style="padding:3px 8px;font-size:12px" class="${on ? 'on' : ''}">${lab}</button>`;
    const draw = () => {
      const n = L.pool().length;
      el.innerHTML = `<div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center"><span style="color:#858b93;min-width:72px">footage</span>${[['all', 'ALL'], ['ai', 'AI PICKUPS'], ['ar', 'ARCHIVE']].map(([v, l]) => chip('kind', v, l, L.F.kind === v)).join('')}</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center"><span style="color:#858b93;min-width:72px">chapter</span>${L.chapters.map(([n_, r, t]) => chip('ch', n_, r + ' · ' + t, L.F.ch.includes(n_))).join('')}</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center"><span style="color:#858b93;min-width:72px">world</span>${worlds.map(w => chip('w', w, w.replace('THE ', ''), L.F.w.includes(w))).join('')}</div>
        <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center"><span style="color:#858b93;min-width:72px">era</span>${eras.map(e => chip('era', e, e.toUpperCase(), L.F.era.includes(e))).join('')}<span style="margin-left:auto;color:${n < 40 ? '#e0533a' : '#ebe5d8'}">${n} shots in play${n < 40 ? ' · too few, widen it' : ''}</span>${(L.F.kind !== 'all' || L.F.ch.length || L.F.w.length || L.F.era.length) ? chip('reset', '', 'EVERYTHING', false) : ''}</div>`;
      el.querySelectorAll('button').forEach(b => b.onclick = () => {
        const g = b.dataset.g, v = b.dataset.v;
        if (g === 'kind') L.F.kind = v; else if (g === 'reset') Object.assign(L.F, { kind: 'all', ch: [], w: [], era: [] }); else { const a = L.F[g], i = a.indexOf(v); i < 0 ? a.push(v) : a.splice(i, 1); }
        try { localStorage.setItem(FK, JSON.stringify(L.F)); } catch (e) { } draw(); onchange && onchange();
      });
    };
    el.style.cssText += ';display:flex;flex-direction:column;gap:6px'; draw();
  };


  /* ---- CINEOSIS CHEMISTRY: every shot is an element (its sign in Deamer's table); a cut is a reaction between two elements.
     Forward along the movement-image chain (perception, affection, impulse, action, reflection, relation) BONDS; the same family is an
     ISOTOPE (stable); action breaking into a time- or memory-image is a CRYSTAL (the rupture the time-image makes); the same sign twice
     is an ECHO; running the chain backwards is BACKFLOW. */
  L.FAMS = ['perception', 'affection', 'impulse', 'action', 'reflection', 'relation', 'memory', 'time'];
  L.FCOL = { perception: '#7fb6e6', affection: '#e68fb0', impulse: '#e0533a', action: '#f2a03a', reflection: '#c9b04a', relation: '#7fc28b', memory: '#a98be6', time: '#9aa3ad' };
  L.fam = c => (L.SIGN[c.sg] || {}).fam || 'time';
  L.chem = (a, b) => {
    if (!a || !b) return { v: 0, kind: '' }; const A = L.FAMS.indexOf(L.fam(a)), B = L.FAMS.indexOf(L.fam(b));
    if (a.sg === b.sg) return { v: -.05, kind: 'echo' }; if (A === B) return { v: .05, kind: 'isotope' };
    if (A < 6 && B < 6 && (B - A === 1 || B - A === 2)) return { v: .25, kind: 'bond' };
    if (A >= 2 && A <= 5 && B >= 6) return { v: .2, kind: 'crystal' }; if (A >= 6 && B >= 6) return { v: .05, kind: 'drift' };
    if (A < 6 && B < 6 && B < A) return { v: -.15, kind: 'backflow' }; return { v: 0, kind: 'leap' };
  };
  L.CHEMCOL = { bond: '#7fc28b', crystal: '#a98be6', isotope: '#9aa3ad', drift: '#9aa3ad', echo: '#e3b341', backflow: '#e0533a', leap: '#555' };
  L.tile = (ctx, c, x, y, sz) => { const S = L.SIGN[c.sg]; if (!S) return; ctx.fillStyle = L.FCOL[S.fam]; ctx.fillRect(x, y, sz, sz); ctx.fillStyle = '#0c0d0f'; ctx.font = `700 ${Math.round(sz * .55)}px IBM Plex Mono`; ctx.textAlign = 'center'; ctx.fillText(S.s, x + sz / 2, y + sz * .7); ctx.textAlign = 'left'; };
  /* ---- VIEW: how the field is laid out, and which lens the cut is judged through (kept per browser) */
  const VK = 'ludens-view'; L.V = { layout: 'story', lens: 'meaning', topo: true };
  try { Object.assign(L.V, JSON.parse(localStorage.getItem(VK) || '{}')); } catch (e) { }
  const saveV = () => { try { localStorage.setItem(VK, JSON.stringify(L.V)); } catch (e) { } };
  L.LAYOUTS = { story: 'STORY · between the beats, left to right', signs: 'SIGNS · the periodic table of Cineosis', meaning: 'MEANING · CLIP map', framing: 'FRAMING · where the weight sits', colour: 'COLOUR · hue by light', time: 'TIME · year by world', chapter: 'CHAPTER · the eight songs' };
  L.LENSES = { meaning: 'MEANING · the lab’s cut (CLIP, best near .72)', framing: 'FRAMING · a match cut on composition', colour: 'COLOUR · a match cut on palette' };
  const WORLDS = ['THE FLEET', 'THE LANDING', 'THE DRILL LINE', 'THE KITCHEN', 'THE SCREEN', 'THE RENDER', 'THE TIDE', 'THE AFTERMATH'];
  const hash = (s, k) => { let h = k; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return (h % 1000) / 1000; };
  L.pos = c => {
    const lay = L.V.layout;
    if (lay === 'story') return [c.sx, c.y];
    if (lay === 'signs') { const S = L.SIGN[c.sg] || { fam: 'time', n: 0 }, fi = L.FAMS.indexOf(S.fam), sib = L.signs.filter(x => x.fam === S.fam), si = Math.max(0, sib.indexOf(S)); return [(fi + .1 + .8 * (si + .15 + .7 * hash(c.id, 11)) / Math.max(1, sib.length)) / L.FAMS.length, .05 + .9 * hash(c.id, 13)]; }
    if (lay === 'framing') return [c.fx, c.fy];
    if (lay === 'colour') { const [h, sa, l, bw] = c.col || [0, 0, .5, 1]; return bw || sa < .08 ? [.02 + .08 * hash(c.id, 3), 1 - l] : [.12 + .88 * (h / 360), 1 - l]; }
    if (lay === 'time') { const x = c.k === 'ai' ? .93 + .06 * hash(c.id, 5) : c.y0 ? Math.min(.9, Math.max(0, (c.y0 - 1915) / 95)) : .9 * hash(c.id, 7); const w = Math.max(0, WORLDS.indexOf(c.w)); return [x, (w + .1 + .8 * hash(c.id, 9)) / WORLDS.length]; }
    if (lay === 'chapter') { const i = Math.max(0, L.chapters.findIndex(ch => ch[0] === c.ch)); return [(i + .08 + .84 * c.x) / 8, c.y]; }
    return [c.x, c.y];
  };
  /* the cut through the chosen lens */
  const cosF = (a, b) => { let s = 0; for (let i = 0; i < 16; i++) s += a.f[i] * b.f[i]; return L.calf[0] * s / 16129 + L.calf[1]; };
  const colSim = (a, b) => { const A = a.col || [0, 0, .5, 1], B = b.col || [0, 0, .5, 1]; const dh = (A[3] || B[3]) ? 0 : Math.min(Math.abs(A[0] - B[0]), 360 - Math.abs(A[0] - B[0])) / 180; return Math.exp(-(dh * dh / .06 + (A[2] - B[2]) ** 2 / .03 + (A[1] - B[1]) ** 2 / .05 + ((A[3] ? 1 : 0) - (B[3] ? 1 : 0)) ** 2 * 1.5)); };
  let FN = null;
  const meaningJoin = (a, b) => Math.exp(-(((L.cos(a, b) - .72) / .12) ** 2) / 2);
  L.join = (a, b) => {
    if (!a || !b) return .5; if (a === b) return 0;
    if (L.V.lens === 'framing') { if (!FN) { const xs = []; for (let i = 0; i < 2000; i++) { const p = L.cards[(i * 7919) % L.cards.length], q = L.cards[(i * 104729 + 13) % L.cards.length]; if (p !== q) xs.push(cosF(p, q)); } xs.sort((x, y) => x - y); FN = [xs[Math.floor(xs.length * .5)], xs[Math.floor(xs.length * .97)]]; } return Math.max(0, Math.min(1, (cosF(a, b) - FN[0]) / (FN[1] - FN[0]))); }
    if (L.V.lens === 'colour') return colSim(a, b);
    return meaningJoin(a, b);
  };
  /* the land: a shot's pull on the ball, from what it would cut to, and from what the data says it is */
  L.well = (prev, c, target) => {   /* target: the story's next beat; shots that cut well INTO it sit lower (the story's gravity) */
    const cut = (L.join(prev, c) - .42) * 2.2, story = (L.holeIds && L.holeIds.has(c.id) ? .35 : 0) + (target && target !== c ? (L.join(c, target) - .45) * 1.2 : target === c ? 1.2 : 0), poison = c.po > .5 ? -.45 * (c.po - .3) : 0, chain = (c.mc - .5) * .3;
    const chem = prev ? L.chem(prev, c).v * 1.4 : 0; return { w: cut + story + poison + chain + chem, cut, story, poison, chain, chem, kind: prev ? L.chem(prev, c).kind : '' };
  };
  /* contours of a scalar field sampled on a grid (marching squares), for the topography */
  L.contours = (ctx, val, nx, ny, toPx, levels, colour) => {
    for (const lv of levels) {
      ctx.strokeStyle = colour(lv); ctx.beginPath();
      for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) {
        const a = val[j * nx + i], b = val[j * nx + i + 1], c = val[(j + 1) * nx + i + 1], d = val[(j + 1) * nx + i];
        const idx = (a > lv ? 8 : 0) | (b > lv ? 4 : 0) | (c > lv ? 2 : 0) | (d > lv ? 1 : 0); if (idx === 0 || idx === 15) continue;
        const t = (p, q) => (lv - p) / (q - p || 1e-9), P = { T: [i + t(a, b), j], R: [i + 1, j + t(b, c)], B: [i + t(d, c), j + 1], L: [i, j + t(a, d)] };
        const segs = { 1: ['L', 'B'], 2: ['B', 'R'], 3: ['L', 'R'], 4: ['T', 'R'], 5: ['L', 'T', 'B', 'R'], 6: ['T', 'B'], 7: ['L', 'T'], 8: ['L', 'T'], 9: ['T', 'B'], 10: ['T', 'R', 'L', 'B'], 11: ['T', 'R'], 12: ['L', 'R'], 13: ['B', 'R'], 14: ['L', 'B'] }[idx];
        for (let k = 0; k < segs.length; k += 2) { const [x1, y1] = toPx(...P[segs[k]]), [x2, y2] = toPx(...P[segs[k + 1]]); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); }
      }
      ctx.stroke();
    }
  };
  /* ---- the header every game shares: the games, then menus for footage, layout, lens and the land */
  L.header = (el, game, onchange) => {
    const games = [['putt.html', 'PUTT-OFF'], ['tennis.html', 'TENNIS'], ['open-cut.html', 'OPEN CUT'], ['../party.html?game=table', 'THE TABLE']];
    el.className = 'lhd'; el.innerHTML = `<a class="brand" href="index.html">LUDENS</a><nav>${games.map(([h, t]) => `<a href="${h}"${t.startsWith(game) ? ' class="on"' : ''}>${t}</a>`).join('')}</nav><span class="slot"></span><span class="sp"></span><button class="mn">MENU</button><div class="pop" hidden></div>`;
    const pop = el.querySelector('.pop');
    const sec = (t, sub) => `<div class="ph">${t}<i>${sub}</i></div>`;
    function fill() {
      pop.innerHTML = `${sec('FOOTAGE', L.pool().length + ' shots in play')}<div class="fl"></div>
        ${sec('LAYOUT', 'where each shot sits')}<div class="ops">${Object.entries(L.LAYOUTS).map(([v, t]) => `<button class="opt${L.V.layout === v ? ' on' : ''}" data-l="${v}">${t}</button>`).join('')}</div>
        ${sec('LENS', 'what makes a good cut; it reshapes the land')}<div class="ops">${Object.entries(L.LENSES).map(([v, t]) => `<button class="opt${L.V.lens === v ? ' on' : ''}" data-n="${v}">${t}</button>`).join('')}</div>
        ${sec('THE LAND', 'how data, story and chemistry shape the ground')}<p>A shot pulls the ball when it <b>cuts</b> well from the last shot (through the lens), cuts well into the <b>story</b>'s next beat, makes a good <b>reaction</b> (below), or leads to many good cuts (<b>chain</b>); poison is a ridge.</p>
        <div class="chem">${[['bond', 'forward along the chain: perception, affection, impulse, action, reflection, relation'], ['crystal', 'action breaking into a time- or memory-image'], ['isotope', 'the same family'], ['echo', 'the same sign twice'], ['backflow', 'the chain run backwards']].map(([k, t]) => `<span><i style="background:${L.CHEMCOL[k]}"></i><b>${k.toUpperCase()}</b> ${t}</span>`).join('')}</div>
        <div class="ops">${L.FAMS.map(f => `<span class="fam"><i style="background:${L.FCOL[f]}"></i>${f}</span>`).join('')}</div><button class="opt${L.V.topo ? ' on' : ''}" data-t="1">CONTOURS ${L.V.topo ? 'ON' : 'OFF'}</button>`;
      L.filterUI(pop.querySelector('.fl'), () => { fill(); onchange && onchange('footage'); });
      pop.querySelectorAll('[data-l]').forEach(b => b.onclick = () => { L.V.layout = b.dataset.l; saveV(); fill(); onchange && onchange('layout'); });
      pop.querySelectorAll('[data-n]').forEach(b => b.onclick = () => { L.V.lens = b.dataset.n; FN = null; saveV(); fill(); onchange && onchange('lens'); });
      pop.querySelector('[data-t]').onclick = () => { L.V.topo = !L.V.topo; saveV(); fill(); onchange && onchange('land'); };
    }
    el.querySelector('.mn').onclick = () => { pop.hidden = !pop.hidden; if (!pop.hidden) fill(); };
    document.addEventListener('pointerdown', e => { if (!pop.hidden && !el.contains(e.target)) pop.hidden = true; });
    if (!document.getElementById('lhd-css')) { const st = document.createElement('style'); st.id = 'lhd-css'; st.textContent = `.lhd{position:relative;display:flex;gap:14px;align-items:center;padding:7px 14px;flex-wrap:nowrap;border-bottom:1px solid #24282d;z-index:20;background:#0c0d0f;color:#ebe5d8;min-height:46px}.lhd .brand{font:700 17px 'Barlow Condensed',sans-serif;letter-spacing:.2em;color:#f25a17;text-decoration:none}.lhd nav{display:flex;gap:2px}.lhd nav a{font:700 12.5px 'Barlow Condensed',sans-serif;letter-spacing:.14em;color:#858b93;text-decoration:none;padding:4px 9px;border-radius:3px;white-space:nowrap}.lhd nav a:hover{color:#ebe5d8}.lhd nav a.on{color:#170b04;background:#ebe5d8}.lhd .sp{flex:1}.lhd .slot{display:flex;gap:10px;align-items:center;min-width:0;overflow:hidden;white-space:nowrap}.lhd button{color:#ebe5d8;border-color:#2c3138}.lhd .mn{padding:5px 12px}.lhd .pop{position:absolute;right:14px;top:100%;margin-top:4px;background:#16181b;border:1px solid #2c3138;border-radius:8px;padding:14px;width:min(700px,94vw);max-height:80vh;overflow:auto;display:flex;flex-direction:column;gap:8px;box-shadow:0 14px 44px #000b}.lhd .pop .ph{font:700 14px 'Barlow Condensed',sans-serif;letter-spacing:.14em;color:#ebe5d8;border-top:1px solid #24282d;padding-top:8px}.lhd .pop .ph:first-child{border-top:0;padding-top:0}.lhd .pop .ph i{font:400 11.5px 'IBM Plex Mono',monospace;letter-spacing:0;color:#858b93;margin-left:8px;font-style:normal}.lhd .pop .ops{display:flex;flex-wrap:wrap;gap:4px}.lhd .pop .opt{text-align:left;font-size:12px;padding:4px 9px}.lhd .pop p{margin:0;color:#cfc9bc;font-size:12px}.lhd .pop p b{color:#ebe5d8;font-weight:500}.lhd .chem{display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:#cfc9bc}.lhd .chem i,.lhd .fam i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}.lhd .fam{font-size:11.5px;color:#cfc9bc;margin-right:8px}@media(max-width:760px){.lhd{flex-wrap:wrap}.lhd nav a{padding:3px 6px;font-size:11.5px}}`; document.head.appendChild(st); }
    return { slot: el.querySelector('.slot'), refresh: () => { } };
  };
  /* ---- LINES OF FLIGHT: the ball's path through the field IS the edit. Every shot it crosses is cut in, for as long as the ball is over
     it (a fast flight cuts quickly, a slow roll holds); the shot it comes to rest on holds longest. Feed positions tick by tick. */
  L.TICK = .075;   /* seconds of film per tick of flight */
  L.recorder = (cellAt, opts = {}) => {
    const min = opts.min || 1.1, max = opts.max || 4.5, hold = opts.hold || 2.2, graze = opts.graze || .5, segs = []; let cur = null, n = 0;
    return {
      feed(x, y) { const c = cellAt(x, y); if (cur && c === cur.c) { cur.k++; return; } if (cur) segs.push(cur); cur = c ? { c, k: 1 } : null; n++; },
      shots(rest = true) {   /* [{c, d}]: grazes shorter than one frame of attention are dropped; repeats of the last shot merge */
        const all = segs.concat(cur ? [cur] : []), out = [];
        /* a shot the ball only grazes (under ~half a second) is passed over, not cut in; a shot the line crosses twice is cut in once, and holds the longer dwell */
        all.forEach((g, i) => { if (g.k * L.TICK < graze && i < all.length - 1) return; const d = Math.min(max, Math.max(min, g.k * L.TICK)); const had = out.find(o => o.c === g.c); if (had) had.d = Math.min(max, Math.max(had.d, d)); else out.push({ c: g.c, d }); });
        if (rest && out.length) out[out.length - 1].d = Math.max(hold, out[out.length - 1].d); return out;
      }
    };
  };
  L.seams = (from, shots) => { let prev = from; return shots.map(s => { const q = L.join(prev, s.c); prev = s.c; return q; }); };
  L.mean = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0;
  L.tc = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}.${Math.floor((s % 1) * 10)}`;
  /* a timeline: each shot as wide as it plays, the cut after it coloured by how it joins */
  L.timeline = (shots, seams, opts = {}) => { const total = opts.total || shots.reduce((a, s) => a + s.d, 0) || 1; let t = opts.t0 || 0; return shots.map((s, n) => { const w = s.d / total * 100, q = seams ? seams[n] : null, h = `<div class="seg${opts.cls ? ' ' + opts.cls : ''}" style="width:${w}%;background-image:url('${L.root + s.c.th}');${q != null ? `box-shadow:inset 3px 0 0 rgb(${L.tint(q)})` : ''}" title="${(s.c.ti || '').replace(/"/g, '')} · ${s.d.toFixed(1)}s${q != null ? ' · ' + L.word(q) : ''}"><span>${L.tc(t)}</span></div>`; t += s.d; return h; }).join(''); };

  /* ---- THE STORY: its beats in order (the story cut's riverbed shots), and which beat a film of a given length is heading for */
  L.beats = (pool) => { const ids = new Set((pool || L.cards).map(c => c.id)); return L.holes.filter(h => ids.has(h.id)).map(h => Object.assign({ c: L.byId[h.id] }, h)); };
  /* the story's slope: each card sits somewhere on the story's axis (sx, 0 = the opening, 1 = the end); a film tells the story when its shots climb
     that axis as it plays. storyAt(pool) maps film time to where on the axis the film should be, within whatever chapters are in play */
  L.storyAt = (pool) => { const xs = pool.map(c => c.sx).sort((a, b) => a - b), lo = xs[Math.floor(xs.length * .03)] || 0, hi = xs[Math.floor(xs.length * .97)] || 1; return { lo, hi, at: f => lo + (hi - lo) * Math.max(0, Math.min(1, f)), err: (c, f) => Math.abs(c.sx - (lo + (hi - lo) * Math.max(0, Math.min(1, f)))) / Math.max(.05, hi - lo) }; };
  L.beatFor = (beats, t, total) => beats.length ? beats[Math.min(beats.length - 1, Math.floor(t / Math.max(1, total) * beats.length))] : null;

  /* ---- THE FILM AS TERRITORY: a film is a path through the field. at(shots, t) says which shot is playing at film time t and how far
     into it; scrubber() is a tall, readable, scrubbable strip (after putt-op's time-scrub): drag through it, or PLAY, and onTime(t) fires
     so the game can send a light along the lines of flight and lift the playing shot out of the field. */
  L.at = (shots, t) => { let acc = 0; for (let i = 0; i < shots.length; i++) { if (t < acc + shots[i].d) return { i, f: (t - acc) / shots[i].d, t0: acc }; acc += shots[i].d; } return shots.length ? { i: shots.length - 1, f: 1, t0: acc - shots[shots.length - 1].d } : null; };
  L.scrubber = (el, opts) => {
    const S = { t: null, k: 0, playing: false, last: 0, px: 44 }; let films = [], vidFor = null;
    if (!document.getElementById('scrub-css')) { const st = document.createElement('style'); st.id = 'scrub-css'; st.textContent = `.scr{display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:stretch}.scr .pv{width:220px;display:flex;flex-direction:column;gap:4px}.scr .pv video{width:220px;aspect-ratio:16/9;background:#000;border-radius:4px;object-fit:cover}.scr .pv .cap{font:500 11px 'IBM Plex Mono',monospace;color:#858b93;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.scr .main{display:flex;flex-direction:column;gap:5px;min-width:0}.scr .bar{display:flex;gap:8px;align-items:center}.scr .bar b{font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.14em}.scr .tc{font:600 13px 'IBM Plex Mono',monospace;min-width:116px}.scr .bar button{padding:4px 10px}.scr .rows{overflow-x:auto;overflow-y:hidden;display:flex;flex-direction:column;gap:4px;padding-bottom:4px}.scr .row{display:flex;gap:8px;align-items:center}.scr .who{position:sticky;left:0;z-index:2;width:74px;flex:none;font:600 12px 'IBM Plex Mono',monospace;white-space:nowrap;overflow:hidden;background:inherit}.scr .track{position:relative;height:58px;display:flex;border-radius:4px;background:#101215;touch-action:none;cursor:pointer;flex:none}.scr .row:not(.on) .track{height:28px;opacity:.6}.scr .sg{position:relative;height:100%;flex:none;background:center/cover no-repeat;border-right:2px solid #0c0d0f}.scr .sg i{position:absolute;left:0;bottom:0;height:4px;width:100%}.scr .sg span{position:absolute;left:4px;top:2px;font:600 10px 'IBM Plex Mono',monospace;color:#fff;text-shadow:0 0 3px #000,0 0 3px #000;white-space:nowrap}.scr .sg em{position:absolute;right:2px;top:2px;font:700 9.5px 'IBM Plex Mono',monospace;font-style:normal;color:#0c0d0f;padding:0 3px;border-radius:2px}.scr .sg u{position:absolute;left:-5px;top:50%;width:8px;height:8px;margin-top:-4px;border-radius:50%;z-index:1;box-shadow:0 0 0 2px #0c0d0f}.scr .sg.pv2{outline:2px dashed #ebe5d8;outline-offset:-3px;opacity:.8}.scr .ph{position:absolute;top:0;bottom:0;width:3px;background:#fff;box-shadow:0 0 6px #000;pointer-events:none;z-index:3}`; document.head.appendChild(st); }
    const dur = f => f.shots.reduce((a, s) => a + s.d, 0);
    const seg = (s, n, prev, cls) => { const S_ = L.SIGN[s.c.sg], ch = prev ? L.chem(prev, s.c) : null; return `<div class="sg${cls ? ' ' + cls : ''}" data-n="${n}" style="width:${Math.max(18, s.d * S.px)}px;background-image:url('${L.root + s.c.th}')" title="${(s.c.ti || '').replace(/"/g, '')} · ${s.d.toFixed(1)}s${S_ ? ' · ' + S_.name : ''}${ch && ch.kind ? ' · ' + ch.kind : ''}"><span>${n}</span>${S_ ? `<em style="background:${L.FCOL[S_.fam]}">${S_.s}</em>` : ''}${s.q != null ? `<i style="background:rgb(${L.tint(s.q)})"></i>` : ''}${ch && ch.kind ? `<u style="background:${L.CHEMCOL[ch.kind]}" title="${ch.kind}"></u>` : ''}</div>`; };
    function render() {
      films = opts.films(); if (S.k >= films.length) S.k = 0; if (S.t == null) setTimeout(video, 0); const f = films[S.k], keepScroll = el.querySelector('.rows') ? el.querySelector('.rows').scrollLeft : null;
      if (!el.querySelector('.pv')) { el.className = 'scr'; el.innerHTML = `<div class="pv"><video muted playsinline preload="metadata"></video><div class="cap">double-click any shot to rewatch it</div></div><div class="main"></div>`; }
      el.querySelector('.main').innerHTML = `<div class="bar"><button class="pp">${S.playing ? 'PAUSE' : 'PLAY'}</button><span class="tc">${S.t == null ? (f ? L.tc(dur(f)) : '0:00.0') : L.tc(S.t) + ' / ' + L.tc(f ? dur(f) : 0)}</span><b style="color:${f ? f.col : '#fff'}">${f ? f.name.toUpperCase() : ''}</b><span style="flex:1"></span><button class="zo" title="zoom out">-</button><button class="zi" title="zoom in">+</button>${S.t != null ? '<button class="lv">BACK TO THE GAME</button>' : ''}</div>
        <div class="rows">${films.map((F, k) => `<div class="row${k === S.k ? ' on' : ''}" data-k="${k}"><span class="who" style="color:${F.col}">${F.name}</span><div class="track">${F.shots.map((s, n) => seg(s, n, n ? F.shots[n - 1].c : null)).join('')}${(F.preview || []).map((s, n) => seg(s, F.shots.length + n, n ? F.preview[n - 1].c : (F.shots.length ? F.shots[F.shots.length - 1].c : null), 'pv2')).join('')}${k === S.k && S.t != null ? `<div class="ph" style="left:${S.t * S.px}px"></div>` : ''}</div></div>`).join('')}</div>`;
      if (keepScroll != null) el.querySelector('.rows').scrollLeft = keepScroll;
      el.querySelector('.pp').onclick = () => { S.playing = !S.playing; if (S.playing && (S.t == null || S.t >= dur(films[S.k]) - .05)) S.t = 0; S.last = performance.now(); render(); fire(); };
      el.querySelector('.zi').onclick = () => { S.px = Math.min(160, S.px * 1.4); render(); }; el.querySelector('.zo').onclick = () => { S.px = Math.max(8, S.px / 1.4); render(); };
      const lv = el.querySelector('.lv'); if (lv) lv.onclick = () => { S.t = null; S.playing = false; const v = el.querySelector('.pv video'); v.pause(); render(); fire(); };
      el.querySelectorAll('.row').forEach(r => { const k = +r.dataset.k, tr = r.querySelector('.track'); tr.onpointerdown = e => { S.k = k; S.playing = false; const go = ev => { const b = tr.getBoundingClientRect(); S.t = Math.max(0, Math.min(dur(films[k]) - .01, (ev.clientX - b.left) / S.px)); render(); fire(); }; go(e); const mv = ev => go(ev), up = () => { removeEventListener('pointermove', mv); removeEventListener('pointerup', up); }; addEventListener('pointermove', mv); addEventListener('pointerup', up); };
        r.querySelectorAll('.sg').forEach(g => g.ondblclick = () => { const F = films[k], n = +g.dataset.n; if (n >= F.shots.length) return; S.k = k; S.t = F.shots.slice(0, n).reduce((a, s) => a + s.d, 0) + .01; S.playing = true; S.last = performance.now(); render(); fire(); }); });
    }
    /* the rewatch: real video of the shot under the playhead, from its own in-point, following the scrub */
    function video() {
      const v = el.querySelector('.pv video'), cap = el.querySelector('.pv .cap'), f = films[S.k]; if (!v || !f || !f.shots.length) return;
      if (S.t == null) {   /* live: the monitor keeps the newest shot of the film running, from its in-point, so the last cut is always watchable */
        const i = f.shots.length - 1, c = f.shots[i].c; if (vidFor === c) { if (v.paused) v.play().catch(() => { }); return; } vidFor = c; v.loop = true; v.src = /^https?:/.test(c.m) ? c.m : L.root + c.m;
        v.onloadedmetadata = () => { v.currentTime = c.ss != null ? c.ss : Math.max(0, (c.du || 4) / 2 - f.shots[i].d / 2); v.play().catch(() => { }); }; cap.textContent = `now · ${i} · ${c.ti || ''}`; return;
      }
      v.loop = false; const at = L.at(f.shots, S.t); if (!at) return; const c = f.shots[at.i].c, src = /^https?:/.test(c.m) ? c.m : L.root + c.m;
      const start = c.ss != null ? c.ss : Math.max(0, (c.du || 4) / 2 - f.shots[at.i].d / 2), want = start + at.f * f.shots[at.i].d;
      if (vidFor !== c) { vidFor = c; v.src = src; v.onloadedmetadata = () => { v.currentTime = Math.min(want, v.duration - .1); if (S.playing) v.play().catch(() => { }); }; cap.textContent = `${at.i} · ${c.ti || ''}`; }
      else if (v.readyState >= 1 && (!S.playing || Math.abs(v.currentTime - want) > .4)) v.currentTime = Math.min(want, v.duration - .1);
      if (S.playing && v.paused) v.play().catch(() => { }); if (!S.playing && !v.paused) v.pause();
    }
    function fire() { video(); opts.onTime && opts.onTime(S.t, films[S.k]); }
    (function loop() { if (S.playing) { const now = performance.now(), f = films[S.k]; S.t += (now - S.last) / 1000; S.last = now; if (!f || S.t >= dur(f)) { S.playing = false; S.t = f ? dur(f) - .01 : null; render(); }
        const ph = el.querySelector('.row.on .ph'), tc = el.querySelector('.tc'), rows = el.querySelector('.rows'); if (ph && f) { ph.style.left = (S.t * S.px) + 'px'; tc.textContent = L.tc(S.t) + ' / ' + L.tc(dur(f)); const x = S.t * S.px + 80; if (x < rows.scrollLeft + 40 || x > rows.scrollLeft + rows.clientWidth - 60) rows.scrollLeft = x - rows.clientWidth / 3; } else render(); fire(); } requestAnimationFrame(loop); })();
    render(); S.render = render; Object.defineProperty(S, 'film', { get: () => films[S.k] }); return S;
  };
  /* draw the playing shot lifted out of the field at its place: large, outlined, playing its flipbook at the film's own pace */
  L.lift = (ctx, c, x, y, w, col, f, label, bounds) => { const h = w * .5625; let X = x - w / 2, Y = y - h - 14; if (bounds) { X = Math.max(bounds[0] + 4, Math.min(bounds[2] - w - 4, X)); Y = Math.max(bounds[1] + 4, Math.min(bounds[3] - h - 30, Y)); } ctx.save(); ctx.shadowColor = '#000'; ctx.shadowBlur = 24; ctx.fillStyle = '#000'; ctx.fillRect(X, Y, w, h); ctx.restore(); L.draw(ctx, c, X, Y, w, h, Math.min(11, Math.floor(f * 12))); ctx.strokeStyle = col; ctx.lineWidth = 3; ctx.strokeRect(X, Y, w, h); ctx.fillStyle = '#000c'; ctx.fillRect(X, Y + h, w, 22); ctx.fillStyle = '#fff'; ctx.font = '600 12px IBM Plex Mono'; ctx.fillText(label, X + 6, Y + h + 15); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(Math.max(X, Math.min(X + w, x)), Y + h + 22); ctx.stroke(); };
  /* ---- a shot plays its flipbook ONCE, slowly, then holds its last frame: no flashing */
  L.playFrame = (since, dur = 2.4) => Math.min(11, Math.floor((performance.now() - since) / (dur * 1000 / 12)));
  /* ---- a smooth path (Catmull-Rom) through points, for the ball's interpolated trail */
  L.spline = (ctx, pts) => {
    if (pts.length < 2) return; ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 0; i < pts.length - 1; i++) { const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)]; ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]); }
    ctx.stroke();
  };
  let AC = null; L.tone = (f, d = .08, g = .05, type = 'sine') => { try { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === 'suspended') AC.resume(); const o = AC.createOscillator(), v = AC.createGain(); o.type = type; o.frequency.value = f; v.gain.value = g; v.gain.exponentialRampToValueAtTime(.0001, AC.currentTime + d); o.connect(v).connect(AC.destination); o.start(); o.stop(AC.currentTime + d); } catch (e) { } };
  /* WATCH: a film (a list of shots) as real video, each shot `each` seconds from its in-point; two videos, the next one pre-seeked */
  L.watch = (films, opts = {}) => {
    const each = opts.each || 2.6, wrap = document.createElement('div');
    wrap.style.cssText = 'position:fixed;inset:0;z-index:50;background:#000e;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:16px';
    wrap.innerHTML = `<div style="position:relative;width:min(92vw,150vh);aspect-ratio:16/9;background:#000;border-radius:6px;overflow:hidden"><video muted playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video><video muted playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0"></video><div class="wt" style="position:absolute;left:12px;bottom:10px;font:600 15px 'IBM Plex Mono',monospace;color:#fff;text-shadow:0 0 4px #000"></div></div><div class="wb" style="display:flex;gap:6px;flex-wrap:wrap;justify-content:center"></div><button style="font:700 14px 'Barlow Condensed',sans-serif;letter-spacing:.14em;background:none;color:#ebe5d8;border:1px solid #444;border-radius:3px;padding:6px 14px;cursor:pointer">CLOSE</button>`;
    document.body.appendChild(wrap); const [A, B] = wrap.querySelectorAll('video'), T = wrap.querySelector('.wt'), bar = wrap.querySelector('.wb');
    const seq = []; films.forEach((f, p) => f.shots.forEach((c0, i) => { const c = c0.c || c0, d = c0.d; seq.push({ c, d, p, name: (f.names && f.names[i]) || f.name, col: (f.cols && f.cols[i]) || f.col }); }));
    bar.innerHTML = films.map(f => `<span style="font:600 13px 'IBM Plex Mono',monospace;color:${f.col}">● ${f.name} · ${f.shots.length} shots</span>`).join(' ');
    const start = (c, d) => c.ss != null ? c.ss : Math.max(0, (c.du || 4) / 2 - (d || each) / 2);
    const load = (v, s) => { const c = s.c; v.src = /^https?:/.test(c.m) ? c.m : L.root + c.m; v.onloadedmetadata = () => { v.currentTime = Math.min(start(c, s.d), Math.max(0, v.duration - .2)); }; };
    let i = 0, cur = A, nxt = B, timer = null, stopped = false;
    const step = () => {
      if (stopped) return; if (i >= seq.length) { T.textContent = 'THE END'; return; }
      const s = seq[i]; cur.style.opacity = 1; nxt.style.opacity = 0; cur.play().catch(() => { }); T.innerHTML = `<span style="color:${s.col}">|</span> ${s.name} · ${i + 1}/${seq.length} · ${s.c.ti || ''}${s.d ? ' · ' + s.d.toFixed(1) + 's' : ''}`;
      if (seq[i + 1]) load(nxt, seq[i + 1]); i++;
      timer = setTimeout(() => { cur.pause(); [cur, nxt] = [nxt, cur]; step(); }, (s.d || each) * 1000);
    };
    if (seq.length) { load(cur, seq[0]); cur.oncanplay = () => { cur.oncanplay = null; step(); }; }
    const close = () => { stopped = true; clearTimeout(timer); A.pause(); B.pause(); wrap.remove(); if (opts.onclose) opts.onclose(); };
    wrap.querySelector('button').onclick = close; return { close };
  };
  root.Ludens = L;
})(this);
