/* LUDENS — what the ball games share: the field of shots (corpus.json), the lab's cut score (as sea-core.js: a Gaussian of CLIP cosine
   around .72, from a calibrated 32-d PCA), pictures and flipbooks drawn without decoding video, and WATCH: a film played back as real
   video, shot after shot, from each shot's own in-point. */
(function (root) {
  const L = { root: '../', P: ['#5acde6', '#f06e64', '#f0cd46', '#aa82f0'], cards: [], byId: {}, holes: [], cal: [1, 0], sprites: null };
  L.load = () => fetch(L.root + 'ludens/corpus.json').then(r => r.json()).then(j => { L.chapters = j.chapters || []; L.cards = j.cards; L.holes = j.holes; L.cal = j.cal; L.sprites = j.sprites; j.cards.forEach((c, i) => { c.i = i; L.byId[c.id] = c; }); return L; });
  L.cos = (a, b) => { let s = 0; for (let i = 0; i < 32; i++) s += a.e[i] * b.e[i]; return L.cal[0] * s / 16129 + L.cal[1]; };
  L.join = (a, b) => !a || !b ? .5 : a === b ? 0 : Math.exp(-(((L.cos(a, b) - .72) / .12) ** 2) / 2);
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
  L.pool = () => L.cards.filter(c => (L.F.kind === 'all' || c.k === L.F.kind) && (!L.F.ch.length || L.F.ch.includes(c.ch)) && (!L.F.w.length || L.F.w.includes(c.w)) && (!L.F.era.length || L.F.era.includes(era(c))));
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
