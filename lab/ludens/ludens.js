/* LUDENS — what the ball games share: the field of shots (corpus.json), the lab's cut score (as sea-core.js: a Gaussian of CLIP cosine
   around .72, from a calibrated 32-d PCA), pictures and flipbooks drawn without decoding video, and WATCH: a film played back as real
   video, shot after shot, from each shot's own in-point. */
(function (root) {
  const L = { root: '../', P: ['#5acde6', '#f06e64', '#f0cd46', '#aa82f0'], cards: [], byId: {}, holes: [], cal: [1, 0], sprites: null };
  L.load = () => fetch(L.root + 'ludens/corpus.json').then(r => r.json()).then(j => { L.chapters = j.chapters || []; L.calf = j.calf || [1, 0]; L.holeIds = new Set(j.holes.map(h => h.id)); L.cards = j.cards; L.holes = j.holes; L.cal = j.cal; L.sprites = j.sprites; j.cards.forEach((c, i) => { c.i = i; L.byId[c.id] = c; }); return L; });
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

  /* ---- VIEW: how the field is laid out, and which lens the cut is judged through (kept per browser) */
  const VK = 'ludens-view'; L.V = { layout: 'meaning', lens: 'meaning', topo: true };
  try { Object.assign(L.V, JSON.parse(localStorage.getItem(VK) || '{}')); } catch (e) { }
  const saveV = () => { try { localStorage.setItem(VK, JSON.stringify(L.V)); } catch (e) { } };
  L.LAYOUTS = { meaning: 'MEANING · CLIP map', framing: 'FRAMING · where the weight sits', colour: 'COLOUR · hue by light', time: 'TIME · year by world', chapter: 'CHAPTER · the eight songs' };
  L.LENSES = { meaning: 'MEANING · the lab’s cut (CLIP, best near .72)', framing: 'FRAMING · a match cut on composition', colour: 'COLOUR · a match cut on palette' };
  const WORLDS = ['THE FLEET', 'THE LANDING', 'THE DRILL LINE', 'THE KITCHEN', 'THE SCREEN', 'THE RENDER', 'THE TIDE', 'THE AFTERMATH'];
  const hash = (s, k) => { let h = k; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return (h % 1000) / 1000; };
  L.pos = c => {
    const lay = L.V.layout;
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
  L.well = (prev, c) => {
    const cut = (L.join(prev, c) - .42) * 2.2, story = L.holeIds && L.holeIds.has(c.id) ? .35 : 0, poison = c.po > .5 ? -.45 * (c.po - .3) : 0, chain = (c.mc - .5) * .3;
    return { w: cut + story + poison + chain, cut, story, poison, chain };
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
    const games = [['putt.html', 'PUTT-OFF'], ['tennis.html', 'TENNIS'], ['open-cut.html', 'OPEN CUT'], ['../party.html?game=table', 'THE TABLE · PHONES']];
    el.className = 'lhd'; el.innerHTML = `<a class="brand" href="index.html">CINEOSIS <b>LUDENS</b></a><nav>${games.map(([h, t]) => `<a href="${h}"${t.startsWith(game) ? ' class="on"' : ''}>${t}</a>`).join('')}</nav><span class="slot"></span><span class="sp"></span>
      <div class="menus"><button data-p="foot">FOOTAGE <i>${L.pool().length}</i></button><button data-p="lay">LAYOUT <i>${L.V.layout}</i></button><button data-p="lens">LENS <i>${L.V.lens}</i></button><button data-p="land">LAND</button></div><div class="pop" hidden></div>`;
    const pop = el.querySelector('.pop'), refresh = () => { el.querySelector('[data-p="foot"] i').textContent = L.pool().length; el.querySelector('[data-p="lay"] i').textContent = L.V.layout; el.querySelector('[data-p="lens"] i').textContent = L.V.lens; };
    const open = k => {
      if (!pop.hidden && pop.dataset.k === k) { pop.hidden = true; return; } pop.hidden = false; pop.dataset.k = k;
      if (k === 'foot') { pop.innerHTML = '<div class="ph">FOOTAGE IN PLAY · which shots the field is made of</div><div class="fl"></div>'; L.filterUI(pop.querySelector('.fl'), () => { refresh(); onchange && onchange('footage'); }); return; }
      const opts = k === 'lay' ? L.LAYOUTS : k === 'lens' ? L.LENSES : null;
      if (opts) { pop.innerHTML = `<div class="ph">${k === 'lay' ? 'LAYOUT · where each shot sits on the field' : 'LENS · what makes a good cut (it shapes the land)'}</div>` + Object.entries(opts).map(([v, t]) => `<button class="opt${L.V[k === 'lay' ? 'layout' : 'lens'] === v ? ' on' : ''}" data-v="${v}">${t}</button>`).join(''); pop.querySelectorAll('.opt').forEach(b => b.onclick = () => { L.V[k === 'lay' ? 'layout' : 'lens'] = b.dataset.v; FN = null; saveV(); refresh(); open(k); open(k); onchange && onchange(k === 'lay' ? 'layout' : 'lens'); }); return; }
      pop.innerHTML = `<div class="ph">THE LAND · how the data shapes the ground</div><p>Every shot pulls or pushes the ball. <b>Cut</b>: how well it cuts from the last shot, through the lens. <b>Story</b>: the story’s own shots are deep wells. <b>Poison</b>: the shots the poison reading flagged are ridges. <b>Chain</b>: shots that lead to many good next cuts sit lower.</p><button class="opt${L.V.topo ? ' on' : ''}" data-t="1">CONTOURS ${L.V.topo ? 'ON' : 'OFF'}</button>`;
      pop.querySelector('[data-t]').onclick = () => { L.V.topo = !L.V.topo; saveV(); open('land'); open('land'); onchange && onchange('land'); };
    };
    el.querySelectorAll('.menus button').forEach(b => b.onclick = () => open(b.dataset.p));
    document.addEventListener('pointerdown', e => { if (!pop.hidden && !el.contains(e.target)) pop.hidden = true; });
    if (!document.getElementById('lhd-css')) { const st = document.createElement('style'); st.id = 'lhd-css'; st.textContent = `.lhd{position:relative;display:flex;gap:12px;align-items:center;padding:8px 14px;flex-wrap:wrap;border-bottom:1px solid #24282d;z-index:20}.lhd .brand{font:700 18px 'Barlow Condensed',sans-serif;letter-spacing:.16em;color:#ebe5d8;text-decoration:none}.lhd .brand b{color:#f25a17}.lhd nav{display:flex;gap:2px}.lhd nav a{font:700 12.5px 'Barlow Condensed',sans-serif;letter-spacing:.14em;color:#858b93;text-decoration:none;padding:4px 9px;border-radius:3px}.lhd nav a:hover{color:#ebe5d8}.lhd nav a.on{color:#170b04;background:#ebe5d8}.lhd .sp{flex:1}.lhd .slot{display:flex;gap:10px;align-items:center}.lhd .menus{display:flex;gap:4px}.lhd .menus button{padding:4px 9px;font-size:12px}.lhd .menus i{font-style:normal;color:#858b93;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0;margin-left:4px}.lhd .pop{position:absolute;right:14px;top:100%;margin-top:4px;background:#16181b;border:1px solid #2c3138;border-radius:6px;padding:12px;width:min(640px,94vw);display:flex;flex-direction:column;gap:6px;box-shadow:0 12px 40px #0009}.lhd .pop .ph{font:700 13px 'Barlow Condensed',sans-serif;letter-spacing:.14em;color:#858b93}.lhd .pop .opt{text-align:left}.lhd .pop p{margin:0;color:#cfc9bc;font-size:12px}.lhd .pop p b{color:#ebe5d8;font-weight:500}@media(max-width:700px){.lhd nav a{padding:3px 6px;font-size:11.5px}}`; document.head.appendChild(st); }
    return { slot: el.querySelector('.slot'), refresh };
  };
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
    const seq = []; films.forEach((f, p) => f.shots.forEach((c, i) => seq.push({ c, p, name: (f.names && f.names[i]) || f.name, col: (f.cols && f.cols[i]) || f.col })));
    bar.innerHTML = films.map(f => `<span style="font:600 13px 'IBM Plex Mono',monospace;color:${f.col}">● ${f.name} · ${f.shots.length} shots</span>`).join(' ');
    const start = c => c.ss != null ? c.ss : Math.max(0, (c.du || 4) / 2 - each / 2);
    const load = (v, c) => { v.src = L.root + c.m.replace(/^\.\.\//, ''); if (/^https?:/.test(c.m)) v.src = c.m; v.onloadedmetadata = () => { v.currentTime = Math.min(start(c), Math.max(0, v.duration - .2)); }; };
    let i = 0, cur = A, nxt = B, timer = null, stopped = false;
    const step = () => {
      if (stopped) return; if (i >= seq.length) { T.textContent = 'THE END'; return; }
      const s = seq[i]; cur.style.opacity = 1; nxt.style.opacity = 0; cur.play().catch(() => { }); T.innerHTML = `<span style="color:${s.col}">●</span> ${s.name} · ${i + 1}/${seq.length} · ${s.c.ti || ''}`;
      if (seq[i + 1]) load(nxt, seq[i + 1].c); i++;
      timer = setTimeout(() => { cur.pause(); [cur, nxt] = [nxt, cur]; step(); }, each * 1000);
    };
    if (seq.length) { load(cur, seq[0].c); cur.oncanplay = () => { cur.oncanplay = null; step(); }; }
    const close = () => { stopped = true; clearTimeout(timer); A.pause(); B.pause(); wrap.remove(); if (opts.onclose) opts.onclose(); };
    wrap.querySelector('button').onclick = close; return { close };
  };
  root.Ludens = L;
})(this);
