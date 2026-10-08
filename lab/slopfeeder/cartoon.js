/* SLOPFEEDER — the multiplane cartoon. One shot per part of the world, drawn in code the way a hand-drawn department works:
   staging in planes, key poses, breakdowns on arcs, eased in-betweens, characters on twos (their lines boil like pencil),
   camera on ones through a multiplane stack (near planes move more), holds, squash and stretch that keeps volume.
   The cast is the login page's four characters (flat shapes, dot eyes that watch) grown into the world: the render offshore,
   and the series' own figures drawn in the same language: the skull-masked cook, the crew in ivory suits, the pails mouths-down.
   Runs in the browser (slopfeeder-cartoon.html) and in node (render-cartoon.js -> frames -> mp4).            */
(function (root) {
  const W = 1280, H = 720, FPS = 24, TAU = Math.PI * 2;
  const C = { purple: '#5b1fe6', black: '#1d1d1f', orange: '#f2591a', yellow: '#e8c21a', ivory: '#efe6d2', shoulder: '#e8692c', ink: '#1a1612',
    sea: '#4e5f6b', sea2: '#3b4a55', foam: '#dfe3dc', sky: '#b9b2a2', sky2: '#d9cdb4', sand: '#c9b38c', sand2: '#a8916c', brick: '#8f4a34', brick2: '#6d3626',
    smoke: '#6c6862', fire: '#f39b2b', steel: '#9aa3a8', screen: '#2f6b4a', glow: '#9df2b4', bun: '#d69a4a', patty: '#5a2f1c' };
  // ---- noise, easing, tracks
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
  const lerp = (a, b, t) => Array.isArray(a) ? a.map((x, k) => lerp(x, b[k], t)) : a + (b - a) * t;
  const E = { lin: t => t, in: t => t * t * t, out: t => 1 - Math.pow(1 - t, 3), io: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
    back: t => { const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); }, snap: t => t < 1 ? 0 : 1 };
  // keys: [{f, v, e, via}] -> value at frame f. `via` bends a 2-D move onto an arc (the breakdown says how it travels)
  function track(keys) { return f => { if (f <= keys[0].f) return keys[0].v;
    for (let i = 1; i < keys.length; i++) { const a = keys[i - 1], b = keys[i]; if (f <= b.f) { const t = (E[b.e || 'io'])((f - a.f) / Math.max(1, b.f - a.f));
      if (b.via) { const u = 1 - t; return a.v.map((x, k) => u * u * x + 2 * u * t * b.via[k] + t * t * b.v[k]); } return lerp(a.v, b.v, t); } }
    return keys[keys.length - 1].v; }; }
  const twos = f => f - (f % 2);                   // characters are drawn on twos
  // ---- the hand: every outline drawn twice (a light construction pass, then the clean line), its points boiling per drawing
  function wob(pts, d, amt) { return pts.map(([x, y], k) => [x + (hash(d * 31.7 + k * 7.3) - .5) * amt, y + (hash(d * 17.1 + k * 3.9 + 99) - .5) * amt]); }
  function path(g, pts, closed) { g.beginPath(); pts.forEach(([x, y], k) => k ? g.lineTo(x, y) : g.moveTo(x, y)); if (closed) g.closePath(); }
  function ink(g, pts, o = {}) { const d = o.d || 0, closed = o.closed !== false;
    if (o.fill) { path(g, wob(pts, d, (o.boil ?? 1.6) * .5), closed); g.fillStyle = o.fill; g.fill(); if (o.grain !== false) hatch(g, pts, d, o.fill); }
    if (o.line !== false) { g.lineJoin = g.lineCap = 'round';
      g.strokeStyle = 'rgba(40,30,25,.22)'; g.lineWidth = (o.w || 2.4) * .7; path(g, wob(pts, d + 500, (o.boil ?? 1.6) * 1.8), closed); g.stroke();   // construction pass
      g.strokeStyle = o.stroke || C.ink; g.lineWidth = o.w || 2.4; path(g, wob(pts, d, o.boil ?? 1.6), closed); g.stroke(); } }
  function hatch(g, pts, d, col) { const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    if (x1 - x0 < 30) return; g.save(); path(g, pts, true); g.clip(); g.strokeStyle = 'rgba(0,0,0,.07)'; g.lineWidth = 1.2;
    for (let x = x0 - (y1 - y0); x < x1; x += 9) { g.beginPath(); g.moveTo(x + hash(d + x) * 3, y1); g.lineTo(x + (y1 - y0) * .55 + hash(d + x + 1) * 3, y0); g.stroke(); } g.restore(); }
  // ---- shapes (as point lists), all about a foot point (x,y) so squash and stretch keep the feet on the ground
  const N = 28;
  function ell(cx, cy, rx, ry, a0 = 0, a1 = TAU, n = N) { const p = []; for (let k = 0; k <= n; k++) { const a = a0 + (a1 - a0) * k / n; p.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); } return p; }
  function rr(x, y, w, h, r = 6) { return [...ell(x + w - r, y + r, r, r, -Math.PI / 2, 0, 4), ...ell(x + w - r, y + h - r, r, r, 0, Math.PI / 2, 4), ...ell(x + r, y + h - r, r, r, Math.PI / 2, Math.PI, 4), ...ell(x + r, y + r, r, r, Math.PI, 1.5 * Math.PI, 4)]; }
  const sq = (pts, fx, fy, s, lean = 0) => pts.map(([x, y]) => { const dy = y - fy; return [fx + (x - fx) * s + dy * lean, fy + dy / s]; });   // volume kept: width*s, height/s
  // ---- the login characters, grown: shape + dot eyes that look at something + a mouth that changes its mind
  function eyes(g, x, y, sp, r, look, blink, d) { for (const s of [-1, 1]) { const ex = x + s * sp, lx = Math.max(-1, Math.min(1, look[0])), ly = Math.max(-1, Math.min(1, look[1]));
      if (blink > .5) ink(g, [[ex - r * 1.4, y], [ex + r * 1.4, y]], { closed: false, d, w: 2.4 }); else { ink(g, ell(ex, y, r * 1.7, r * 1.7), { fill: '#fff', d, w: 1.6, grain: false }); ink(g, ell(ex + lx * r * .7, y + ly * r * .7, r, r), { fill: C.ink, d: d + 3, line: false, grain: false }); } } }
  function mouth(g, x, y, w, kind, d) { const p = kind === 'smile' ? ell(x, y - w * .25, w, w * .55, .2, Math.PI - .2, 8) : kind === 'frown' ? ell(x, y + w * .35, w, w * .5, Math.PI + .3, TAU - .3, 8) : kind === 'o' ? ell(x, y, w * .35, w * .45) : [[x - w, y], [x + w, y]];
    ink(g, p, { closed: kind === 'o', fill: kind === 'o' ? C.ink : null, d, w: 2.6, grain: false }); }
  function shape(g, kind, x, y, s, o) {   // x,y = foot; s = scale; o = {squash, lean, look, blink, mouth, f}
    const d = o.d, q = o.squash || 1, ln = o.lean || 0; let pts, face;
    if (kind === 'purple') { pts = rr(x - 55 * s, y - 230 * s, 110 * s, 230 * s, 8 * s); face = [x + 8 * s, y - 190 * s, 15 * s]; }
    if (kind === 'black') { pts = rr(x - 42 * s, y - 165 * s, 84 * s, 165 * s, 6 * s); face = [x + 4 * s, y - 135 * s, 12 * s]; }
    if (kind === 'orange') { pts = ell(x, y, 120 * s, 115 * s, Math.PI, TAU, 24).concat([[x + 120 * s, y], [x - 120 * s, y]]); face = [x, y - 62 * s, 16 * s]; }
    if (kind === 'yellow') { pts = [[x - 48 * s, y], [x - 48 * s, y - 120 * s], ...ell(x, y - 120 * s, 48 * s, 48 * s, Math.PI, TAU, 14), [x + 48 * s, y]]; face = [x + 6 * s, y - 128 * s, 11 * s]; }
    pts = sq(pts, x, y, q, ln); const fy = y + (face[1] - y) / q, fx = x + (face[0] - x) * q + (face[1] - y) * ln;
    ink(g, pts, { fill: C[kind], d, w: 3 * Math.max(.6, s) });
    eyes(g, fx, fy, face[2] * 1.15, face[2] * .42, o.look || [0, 0], o.blink || 0, d + 7);
    if (o.mouth) mouth(g, fx, fy + face[2] * 1.4, face[2] * .7, o.mouth, d + 9); }
  // ---- the series' figures in the same hand
  function crew(g, x, y, s, o) {   // ivory pressure suit, orange shoulder, round helmet; o: crouch (0..1), arm (rad), lean, d
    const d = o.d, c = o.crouch || 0, ln = o.lean || 0, hip = y - (62 - 26 * c) * s, chest = hip - 46 * s;
    const knee = c * 14 * s; ink(g, [[x - 10 * s, y], [x - 12 * s - knee, (y + hip) / 2], [x - 6 * s, hip]], { closed: false, d, w: 6 * s, stroke: C.ivory });
    ink(g, [[x + 12 * s, y], [x + 14 * s + knee, (y + hip) / 2], [x + 6 * s, hip]], { closed: false, d: d + 1, w: 6 * s, stroke: C.ivory });
    const body = sq(ell(x + ln * 20 * s, (hip + chest) / 2, 22 * s, 32 * s), x, hip + 6 * s, 1 + c * .12, 0); ink(g, body, { fill: C.ivory, d: d + 2, w: 2.2 });
    ink(g, ell(x + ln * 20 * s - 12 * s, chest + 8 * s, 9 * s, 6 * s), { fill: C.shoulder, d: d + 3, w: 1.6, grain: false });
    const a = o.arm ?? .6, ax = x + ln * 20 * s + 14 * s, ay = chest + 10 * s; ink(g, [[ax, ay], [ax + Math.cos(a) * 30 * s, ay + Math.sin(a) * 30 * s]], { closed: false, d: d + 4, w: 6 * s, stroke: C.ivory });
    const hx = x + ln * 30 * s, hy = chest - 18 * s; ink(g, ell(hx, hy, 16 * s, 16 * s), { fill: C.ivory, d: d + 5, w: 2.2 }); ink(g, ell(hx + 5 * s, hy, 9 * s, 6 * s), { fill: '#3d4a52', d: d + 6, w: 1.4, grain: false }); }
  function cook(g, x, y, s, o) {   // hooded cloak, the skull mask, headset; o: turn (0 profile .. 1 facing us), tray (the griddle on the left arm), flip (spatula angle), d
    const d = o.d, t = o.turn || 0;
    ink(g, [[x - 70 * s, y], [x - 46 * s, y - 150 * s], [x, y - 196 * s], [x + 46 * s, y - 150 * s], [x + 70 * s, y]], { fill: '#2a2622', d, w: 2.6 });   // the cloak
    const hx = x + (1 - t) * 14 * s, hy = y - 196 * s; ink(g, ell(hx, hy, 40 * s, 46 * s), { fill: '#2a2622', d: d + 1, w: 2.4 });                     // the hood
    const mx = hx + (1 - t) * 10 * s, mw = (22 + 10 * t) * s; ink(g, ell(mx, hy + 6 * s, mw, 32 * s), { fill: '#dcd8cc', d: d + 2, w: 2 });            // the skull
    for (const sgn of t > .3 ? [-1, 1] : [1]) ink(g, ell(mx + sgn * mw * .42, hy - 2 * s, 7 * s, 8 * s), { fill: C.ink, d: d + 3, line: false, grain: false });   // sockets
    ink(g, [[mx, hy + 8 * s], [mx - 3 * s, hy + 14 * s], [mx + 3 * s, hy + 14 * s]], { fill: C.ink, d: d + 4, w: 1, grain: false });
    for (let k = -2; k <= 2; k++) ink(g, [[mx + k * 5 * s, hy + 22 * s], [mx + k * 5 * s, hy + 30 * s]], { closed: false, d: d + 5 + k, w: 1.3 });       // teeth
    ink(g, ell(hx - 34 * s, hy, 9 * s, 14 * s), { fill: C.black, d: d + 9, w: 1.6, grain: false });                                                       // headset
    if (o.tray !== false) { const ty = y - 104 * s, tx = x - 64 * s;                                                                                       // the griddle on the left forearm
      ink(g, rr(tx - 70 * s, ty, 120 * s, 16 * s, 4), { fill: '#f3f1ea', d: d + 10, w: 2 }); ink(g, rr(tx - 70 * s, ty + 3 * s, 28 * s, 10 * s, 2), { fill: '#2c56c9', d: d + 11, line: false, grain: false });
      ink(g, rr(tx + 20 * s, ty + 3 * s, 28 * s, 10 * s, 2), { fill: '#d23c2f', d: d + 12, line: false, grain: false });
      for (let k = 0; k < 3; k++) burger(g, tx - 40 * s + k * 34 * s, ty, s * .55, d + 13 + k); }
    const sa = o.flip ?? -.4, sx = x + 48 * s, sy = y - 112 * s; ink(g, [[sx, sy], [sx + Math.cos(sa) * 46 * s, sy + Math.sin(sa) * 46 * s]], { closed: false, d: d + 20, w: 4 * s, stroke: C.steel }); }
  function burger(g, x, y, s, d) { ink(g, ell(x, y - 6 * s, 20 * s, 9 * s, Math.PI, TAU, 10), { fill: C.bun, d, w: 1.6 }); ink(g, rr(x - 21 * s, y - 7 * s, 42 * s, 8 * s, 3), { fill: C.patty, d: d + 1, w: 1.4, grain: false }); }
  function pail(g, x, y, s, o) {   // the drill: narrow closed bottom UP, broad open mouth DOWN, spindle, crossbar, rope
    const d = o.d, up = o.up || 0; ink(g, [[x - 34 * s, y], [x - 22 * s, y - 54 * s], [x + 22 * s, y - 54 * s], [x + 34 * s, y]], { fill: C.orange, d, w: 2.2 });
    ink(g, [[x - 36 * s, y - 6 * s], [x + 36 * s, y - 6 * s]], { closed: false, d: d + 1, w: 2 }); const sy = y - 54 * s - 70 * s + up * 30 * s;
    ink(g, [[x, y - 54 * s], [x, sy]], { closed: false, d: d + 2, w: 3, stroke: '#6b5032' }); ink(g, [[x - 40 * s, sy + 34 * s - up * 30 * s], [x + 40 * s, sy + 34 * s - up * 30 * s]], { closed: false, d: d + 3, w: 5, stroke: '#7a5a38' });
    ink(g, [[x - 40 * s, sy + 34 * s - up * 30 * s], [x, sy], [x + 40 * s, sy + 34 * s - up * 30 * s]], { closed: false, d: d + 4, w: 1.6, stroke: '#2c6fb5' }); }
  function ship(g, x, y, s, o) { const d = o.d; ink(g, [[x - 160 * s, y - 20 * s], [x + 170 * s, y - 20 * s], [x + 120 * s, y + 12 * s], [x - 140 * s, y + 12 * s]], { fill: '#4a4f52', d, w: 2 });
    ink(g, [[x - 50 * s, y - 20 * s], [x - 40 * s, y - 62 * s], [x + 20 * s, y - 62 * s], [x + 36 * s, y - 20 * s]], { fill: '#5b6164', d: d + 1, w: 2 }); ink(g, rr(x - 10 * s, y - 96 * s, 16 * s, 34 * s, 2), { fill: '#3d4144', d: d + 2, w: 1.6 });
    if (o.burn) for (let k = 0; k < 4; k++) { const fx = x - 30 * s + k * 18 * s, h = (24 + 18 * Math.sin(o.f * .4 + k * 2)) * s; ink(g, [[fx - 8 * s, y - 62 * s], [fx, y - 62 * s - h], [fx + 8 * s, y - 62 * s]], { fill: C.fire, d: d + 5 + k, w: 1.4, grain: false }); } }
  function fort(g, x, y, s, d) { ink(g, [[x - 260 * s, y], [x - 260 * s, y - 120 * s], [x - 220 * s, y - 120 * s], [x - 220 * s, y - 140 * s], [x - 180 * s, y - 140 * s], [x - 180 * s, y - 120 * s], [x + 200 * s, y - 120 * s], [x + 200 * s, y - 150 * s], [x + 250 * s, y - 150 * s], [x + 250 * s, y]], { fill: C.brick, d, w: 2.4 });
    ink(g, ell(x, y, 46 * s, 50 * s, Math.PI, TAU, 12).concat([[x + 46 * s, y], [x - 46 * s, y]]), { fill: '#24140f', d: d + 1, w: 2 });
    for (let r = 1; r < 6; r++) ink(g, [[x - 255 * s, y - r * 22 * s], [x + 245 * s, y - r * 22 * s]], { closed: false, d: d + 2 + r, w: 1, stroke: C.brick2 }); }
  function waves(g, y, amp, len, col, f, sp, d) { const p = [[-W, H * 2]]; for (let x = -W; x <= W * 2; x += 24) p.push([x, y + Math.sin(x / len + f * sp) * amp + Math.sin(x / (len * .37) - f * sp * 1.7) * amp * .3]); p.push([W * 2, H * 2]);
    ink(g, p, { fill: col, d, w: 2, boil: 1.2 }); }
  function puff(g, x, y, r, col, d, n = 7) { for (let k = 0; k < n; k++) { const a = k / n * TAU + hash(d + k) * .6, rr_ = r * (.45 + hash(d + k + 9) * .35);
      ink(g, ell(x + Math.cos(a) * r * .55, y + Math.sin(a) * r * .38, rr_, rr_ * .9, 0, TAU, 14), { fill: col, d: d + k, w: 1.8 }); } }
  function blast(g, x, y, f0, f, s, d) {   // effects animation: flash, fireball that squashes as it rises, smoke that keeps rising and thins
    const t = (f - f0) / FPS; if (t < 0 || t > 3.2) return;
    if (t < .12) { g.save(); g.globalAlpha = .85 - t * 6; g.fillStyle = '#fff6dc'; g.fillRect(-W, -H, W * 3, H * 3); g.restore(); }
    const r = s * (40 + 140 * E.out(Math.min(1, t / .5))), rise = s * 120 * E.out(Math.min(1, t / 2.4));
    g.save(); g.globalAlpha = Math.max(0, 1 - Math.max(0, t - 1.6) / 1.6); puff(g, x, y - rise - r * .3, r * .9, C.smoke, d, 8);
    if (t < 1) { g.globalAlpha = 1 - t; puff(g, x, y - rise * .6, r * .55, C.fire, d + 40, 6); } g.restore();
    for (let k = 0; k < 9; k++) { const a = -Math.PI * (.15 + .7 * hash(d + k)), v = (260 + 300 * hash(d + k + 5)) * s, px = x + Math.cos(a) * v * t, py = y + Math.sin(a) * v * t + 420 * s * t * t;   // debris on parabolas
      if (t < 1.4) ink(g, rr(px, py, 8 * s, 6 * s, 2), { fill: C.sand2, d: d + 60 + k, w: 1, grain: false }); } }
  function screen(g, x, y, w, h, text, n, d) { ink(g, rr(x - 14, y - 14, w + 28, h + 28, 10), { fill: '#cfc6ae', d, w: 2.4 }); ink(g, rr(x, y, w, h, 14), { fill: C.screen, d: d + 1, w: 2 });
    g.save(); g.fillStyle = C.glow; g.font = `${Math.round(h / 9)}px "IBM Plex Mono", monospace`; const lines = text.slice(0, n).split('\n');
    lines.slice(-6).forEach((l, k) => g.fillText(l, x + 12, y + h / 7 + k * h / 7.5)); g.restore(); }
  function onion(g, x, y, s, d) { ink(g, ell(x, y, 26 * s, 12 * s), { fill: '#e9d29a', d, w: 2 }); ink(g, ell(x, y, 13 * s, 5 * s), { fill: C.sea, d: d + 1, w: 1.6, grain: false }); }
  // ---- the multiplane camera: each plane at a depth z (character plane z=1); near planes move and grow more, far ones less
  function photograph(g, shot, f) { const cam = shot.camera(f), shake = shot.shake ? shot.shake(f) : 0;
    g.fillStyle = C.sky2; g.fillRect(0, 0, W, H);
    for (const pl of shot.planes) { const p = 1 / pl.z, z = 1 + (cam.zoom - 1) * p;
      g.save(); g.translate(W / 2 + (hash(twos(f) + pl.z * 9) - .5) * 1.2, H / 2 + (hash(twos(f) * 1.3 + pl.z) - .5) * 1.2);          // a hair of registration wobble per drawing
      g.scale(z, z); g.translate(-cam.x * p + Math.sin(f * 1.9) * shake * p, -H / 2 - cam.y * p + Math.cos(f * 2.3) * shake * p);   // world x = 0 is the centre of frame, y is the screen's
      pl.draw(g, f, twos(f)); g.restore(); }
    // the paper: tone and grain over everything (on twos, like a new sheet)
    g.save(); g.globalAlpha = .06; for (let k = 0; k < 260; k++) { g.fillStyle = hash(k + twos(f)) > .5 ? '#000' : '#fff'; g.fillRect(hash(k * 3.1 + twos(f)) * W, hash(k * 7.7 + twos(f)) * H, 2, 2); } g.restore();
    const v = g.createRadialGradient(W / 2, H / 2, H * .45, W / 2, H / 2, H * .95); v.addColorStop(0, 'rgba(60,40,20,0)'); v.addColorStop(1, 'rgba(60,40,20,.28)'); g.fillStyle = v; g.fillRect(0, 0, W, H); }
  const cam = (keys) => { const t = track(keys); return f => { const [x, y, zoom] = t(f); return { x, y, zoom }; }; };
  const sky = (top, bot) => (g) => { const gr = g.createLinearGradient(0, -H, 0, H); gr.addColorStop(0, top); gr.addColorStop(1, bot); g.fillStyle = gr; g.fillRect(-W, -H, W * 3, H * 3); };
  // ======================== the shots: one per part of the world ========================
  const SHOTS = {
  'THE FLEET': (() => {   // the render arrives: the sea bulges (anticipation), four shapes rise, overshoot, settle, and their eyes find the beach
    const rise = [0, 1, 2, 3].map(k => track([{ f: 0, v: 260 }, { f: 30 + k * 10, v: 250, e: 'io' }, { f: 70 + k * 10, v: -30, e: 'out' }, { f: 84 + k * 10, v: 12, e: 'io' }, { f: 98 + k * 10, v: 0, e: 'io' }]));
    const squash = [0, 1, 2, 3].map(k => track([{ f: 0, v: 1 }, { f: 66 + k * 10, v: .82, e: 'out' }, { f: 80 + k * 10, v: 1.12, e: 'io' }, { f: 96 + k * 10, v: 1, e: 'io' }]));
    const look = track([{ f: 0, v: [0, -1] }, { f: 120, v: [0, -1] }, { f: 132, v: [-.2, .9], e: 'back' }, { f: 168, v: [-.2, .9] }, { f: 176, v: [.9, .6], e: 'out' }]);
    const blink = f => (f > 150 && f < 154) || (f > 186 && f < 189) ? 1 : 0, kinds = ['purple', 'black', 'orange', 'yellow'], xs = [-260, -90, 90, 280];
    return { dur: 200, camera: cam([{ f: 0, v: [0, 40, 1] }, { f: 110, v: [0, 30, 1] }, { f: 200, v: [0, -10, 1.35], e: 'io' }]),
      planes: [{ z: 9, draw: sky('#8e98a2', '#d6c9ad') },
        { z: 4, draw: (g, f, d) => { waves(g, 400, 6, 90, C.sea2, f, .05, d); for (const [x, b] of [[-420, 1], [380, 0]]) ship(g, x, 404, .6, { d: d + 50 + x, burn: b, f }); } },
        { z: 2.2, draw: (g, f, d) => kinds.forEach((k, i) => { const y = 430 + rise[i](f); if (y > 520) return; g.save(); g.beginPath(); g.rect(-W, -H, W * 3, H + 432); g.clip();
            shape(g, k, xs[i], y, 1.25, { d: d + i * 100, squash: squash[i](f), look: look(f), blink: blink(f + i * 3), mouth: f > 176 ? 'line' : null }); g.restore(); }) },
        { z: 2.2, draw: (g, f, d) => { waves(g, 432, 9, 70, C.sea, f, .08, d + 7); if (f > 26 && f < 72) [0, 1, 2, 3].forEach(i => { const b = Math.sin(Math.min(1, (f - 26 - i * 10) / 30) * Math.PI) * 26; if (b > 0) ink(g, ell(xs[i], 434, 120, b, Math.PI, TAU, 16), { fill: C.foam, d: d + 300 + i, w: 2 }); }); } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 560], [W * 2, 540], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 }); [-420, -300, 340, 470].forEach((x, i) => pail(g, x, 600 + (i % 2) * 18, .9, { d: d + 20 + i })); } },
        { z: .55, draw: (g, f, d) => { ink(g, [[-W, 700], [-80, 660], [120, 690], [W * 2, 640], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand2, d, w: 3 }); crew(g, -380, 720, 1.6, { d: d + 9, crouch: .6, lean: .1, arm: -1.2 }); } }],
      xsheet: [[1, 'K01', 30, 'the sea, still; two ships burn', 'hold', 'swell'], [27, 'K02', 40, 'the sea bulges four times (anticipation)', 'hold', 'low rumble'], [66, 'K03', 14, 'the shapes break the surface, stretched', 'hold', 'roar of water'],
        [84, 'B01', 14, 'overshoot, squash', 'slow push begins', ''], [98, 'K04', 30, 'settle: four colossi on the horizon', 'push', ''], [120, 'K05', 12, 'eyes snap down to the beach', 'push', 'click'], [176, 'K06', 24, 'eyes slide to the crew; mouths go flat', 'push in 35%', '']] }; })(),
  'THE RENDER': (() => {   // a cursor the size of the sky drags across; the shapes' eyes follow it; it clicks; a change request falls onto the beach
    const cur = track([{ f: 0, v: [-760, 40] }, { f: 50, v: [-120, 70], e: 'out' }, { f: 80, v: [-80, 60], e: 'io' }, { f: 92, v: [-80, 60] }, { f: 132, v: [300, 120], e: 'io', via: [100, -10] }, { f: 150, v: [290, 120] }]);
    const click = f => f > 150 && f < 156 ? .82 : 1, shell = track([{ f: 156, v: [290, 150] }, { f: 196, v: [-120, 470], e: 'in', via: [140, 0] }]);
    return { dur: 230, shake: f => f > 196 && f < 214 ? 10 : 0, camera: cam([{ f: 0, v: [0, -40, 1] }, { f: 150, v: [40, -60, 1.08] }, { f: 196, v: [-60, 60, 1.18], e: 'io' }, { f: 230, v: [-60, 60, 1.18] }]),
      planes: [{ z: 9, draw: sky('#7d7690', '#cdbfa6') },
        { z: 3, draw: (g, f, d) => { const [cx, cy] = cur(f); ['purple', 'black', 'orange', 'yellow'].forEach((k, i) => { const x = -330 + i * 210, y = 330, dx = cx - x, dy = cy - (y - 150) + 120;
            shape(g, k, x, y, .95, { d: d + i * 50, look: [dx / 260, dy / 200], lean: Math.max(-.12, Math.min(.12, dx / 4000)), mouth: f > 156 && f < 200 ? 'o' : 'line', blink: (f + i * 7) % 90 < 3 ? 1 : 0 }); }); waves(g, 330, 5, 80, C.sea2, f, .05, d); } },
        { z: 1.6, draw: (g, f, d) => { const [cx, cy] = cur(f), s = click(f); ink(g, sq([[cx, cy], [cx, cy + 120], [cx + 30, cy + 92], [cx + 52, cy + 140], [cx + 70, cy + 132], [cx + 48, cy + 86], [cx + 88, cy + 86]], cx, cy, 1 / s), { fill: '#fff', d, w: 4 });
            if (f >= 156 && f < 196) { const [sx, sy] = shell(f); ink(g, rr(sx - 60, sy - 18, 120, 36, 8), { fill: '#f7f3e8', d: d + 3, w: 2.4 }); g.save(); g.fillStyle = C.ink; g.font = '600 15px "IBM Plex Mono",monospace'; g.fillText('move it left?', sx - 54, sy + 5); g.restore(); } } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 470], [W * 2, 450], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 }); fort(g, 420, 470, .7, d + 9); [-300, -170, -40].forEach((x, i) => crew(g, x, 520 + i * 6, 1, { d: d + 30 + i, crouch: f > 190 ? .7 : .1, arm: f > 190 ? -1.4 : .6, lean: f > 190 ? -.2 : 0 })); blast(g, -120, 470, 196, f, 1, d + 80); } }],
      xsheet: [[1, 'K01', 50, 'a cursor enters the sky', 'drift', 'hum'], [50, 'K02', 42, 'it hovers; four pairs of eyes follow it', 'hold', ''], [92, 'B01', 40, 'it drags on an arc to the fort', 'drift R', 'drag'],
        [150, 'K03', 6, 'click: the cursor squashes', 'hold', 'CLICK'], [156, 'K04', 40, 'a change request falls on a parabola; mouths open', 'tilt down', 'whistle'], [196, 'K05', 34, 'impact; the crew dive', 'shake', 'boom']] }; })(),
  'THE LANDING': (() => {   // three shells walk up the beach; a crewman anticipates, leaps, lands, compresses, crawls on
    const hits = [24, 70, 118], run = track([{ f: 0, v: [-460, 0] }, { f: 60, v: [-200, 0], e: 'lin' }, { f: 66, v: [-190, 0] }, { f: 84, v: [10, -150], e: 'out', via: [-110, -260] }, { f: 98, v: [120, 0], e: 'in', via: [80, -90] }, { f: 112, v: [130, 0] }, { f: 200, v: [380, 0], e: 'io' }]);
    const crouch = track([{ f: 0, v: .1 }, { f: 60, v: .1 }, { f: 66, v: .9, e: 'out' }, { f: 72, v: 0, e: 'in' }, { f: 98, v: 0 }, { f: 102, v: 1, e: 'out' }, { f: 116, v: .9 }, { f: 130, v: .5, e: 'io' }]);
    return { dur: 210, shake: f => hits.some(h => f >= h && f < h + 12) ? 14 : 2, camera: cam([{ f: 0, v: [-260, 0, 1.1] }, { f: 200, v: [240, -20, 1.2], e: 'io' }]),
      planes: [{ z: 10, draw: sky('#6e6a66', '#b8ab92') }, { z: 5, draw: (g, f, d) => { waves(g, 330, 4, 100, C.sea2, f, .04, d); ship(g, -200, 334, .45, { d: d + 4, burn: 1, f }); ship(g, 520, 336, .38, { d: d + 9 }); } },
        { z: 2.5, draw: (g, f, d) => { fort(g, 420, 420, .8, d); ink(g, [[-W, 430], [W * 2, 420], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand2, d: d + 3, w: 2 }); } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 500], [W * 2, 480], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 }); [-520, -350, 260, 560].forEach((x, i) => pail(g, x, 560 + (i % 2) * 14, 1, { d: d + 40 + i }));
            const [x, y] = run(f), c = crouch(f), air = y < -10; crew(g, x, 540 + y, 1.25, { d: d + 70, crouch: c, lean: air ? .35 : .15, arm: air ? -2.2 : -.4 + Math.sin(f * .6) * .5 });
            [[-330, hits[0]], [-60, hits[1]], [230, hits[2]]].forEach(([bx, h], i) => blast(g, bx, 520, h, f, 1.1, d + 200 + i * 40)); } },
        { z: .5, draw: (g, f, d) => { ink(g, [[-W, 740], [0, 690], [260, 720], [W * 2, 700], [W * 2, H * 2], [-W, H * 2]], { fill: '#8c7656', d, w: 3 }); for (let k = 0; k < 5; k++) ink(g, [[-500 + k * 340, 700], [-480 + k * 340, 610], [-470 + k * 340, 700]], { fill: '#3b3530', d: d + k, w: 2 }); } }],
      xsheet: [[1, 'K01', 24, 'the crewman runs (cycle on twos)', 'truck R', 'surf'], [24, 'FX1', 30, 'first shell: flash, fireball, debris on parabolas', 'shake', 'boom'], [60, 'K02', 6, 'anticipation: he compresses', 'truck', ''],
        [66, 'K03', 18, 'leap on an arc, stretched', 'truck', 'whoosh'], [70, 'FX2', 30, 'second shell behind him', 'shake', 'boom'], [98, 'K04', 4, 'landing contact', '', 'thud'], [102, 'K05', 14, 'compression, held', '', ''], [118, 'FX3', 30, 'third shell', 'shake', 'boom'], [130, 'K06', 70, 'he crawls on toward the fort', 'truck R', '']] }; })(),
  'THE DRILL LINE': (() => {   // the line pumps; each drill a cycle on twos, each man a frame behind the last (overlap), a lateral truck through the planes
    return { dur: 200, camera: cam([{ f: 0, v: [-200, 0, 1] }, { f: 200, v: [260, 0, 1], e: 'lin' }]),
      planes: [{ z: 12, draw: sky('#9aa0a2', '#d8c9a8') }, { z: 6, draw: (g, f, d) => { waves(g, 360, 4, 120, C.sea2, f, .03, d); ship(g, 500, 366, .4, { d: d + 3, burn: 1, f }); } },
        { z: 3, draw: (g, f, d) => { fort(g, 640, 420, 1, d); ink(g, [[-W, 430], [W * 2, 425], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand2, d: d + 5, w: 2 }); } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 470], [W * 2, 465], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 });
            for (let k = 0; k < 7; k++) { const x = -560 + k * 210, ph = (twos(f) - k * 4) / 16 * TAU, up = (Math.sin(ph) + 1) / 2;   // the stroke: down hard, up slow
              const u = Math.pow(up, 1.6); pail(g, x, 560, 1.1, { d: d + k * 20, up: u }); crew(g, x - 50, 566, 1.05, { d: d + k * 20 + 9, crouch: .2 + (1 - u) * .7, arm: -.9 - u * .9, lean: .15 }); } } },
        { z: .45, draw: (g, f, d) => { for (let k = 0; k < 8; k++) ink(g, rr(-900 + k * 520, 380, 30, 400, 6), { fill: '#5a4632', d: d + k, w: 2.4 }); ink(g, [[-W * 2, 520], [W * 3, 470]], { closed: false, d: d + 30, w: 5, stroke: '#2c6fb5' }); } }],
      xsheet: [[1, 'CYC', 16, 'the drill stroke: down fast, up slow (a 16-frame cycle on twos)', 'truck R', 'rope rasp'], [1, 'OVL', 4, 'each man four frames behind the last: a wave down the line', '', 'the chant'],
        [1, 'MP', 200, 'posts in the foreground race past; the fort barely moves', 'lateral truck', 'surf']] }; })(),
  'THE KITCHEN': (() => {   // the cook flips a burger: anticipation, the toss on an arc, the spin, the catch with squash; then the turn, and the stare, held
    const b = track([{ f: 0, v: [-62, -108] }, { f: 30, v: [-62, -108] }, { f: 36, v: [-62, -100] }, { f: 66, v: [-40, -108], e: 'in', via: [-50, -360] }, { f: 70, v: [-40, -108] }]);
    const spin = track([{ f: 0, v: 0 }, { f: 36, v: 0 }, { f: 66, v: TAU * 1.5, e: 'lin' }]), flip = track([{ f: 0, v: -.4 }, { f: 26, v: .3, e: 'io' }, { f: 36, v: -1.4, e: 'out' }, { f: 70, v: -.4, e: 'io' }]);
    const turn = track([{ f: 0, v: 0 }, { f: 96, v: 0 }, { f: 104, v: -.08, e: 'io' }, { f: 122, v: 1, e: 'out' }, { f: 130, v: .96 }]);
    return { dur: 230, camera: cam([{ f: 0, v: [0, 0, 1] }, { f: 100, v: [0, 0, 1] }, { f: 130, v: [-40, -150, 1.6], e: 'io' }, { f: 230, v: [-40, -150, 1.68] }]),
      planes: [{ z: 8, draw: sky('#58606a', '#a89c86') }, { z: 3, draw: (g, f, d) => { fort(g, -240, 430, .9, d); ink(g, [[-W, 440], [W * 2, 432], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand2, d: d + 2, w: 2 });
            [-60, 90, 230].forEach((x, i) => crew(g, x, 470, .8, { d: d + 10 + i, crouch: .8, arm: -1.8 + Math.sin(twos(f) * .2 + i) * .3 })); } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 560], [W * 2, 556], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 }); const x = 120, y = 600; cook(g, x, y, 1.5, { d: d + 40, turn: turn(f), flip: flip(f), tray: true });
            if (f < 70) { const [bx, by] = b(f); g.save(); g.translate(x + bx * 1.5, y + by * 1.5); g.rotate(spin(f)); burger(g, 0, 0, .9, d + 90); g.restore(); }
            for (let k = 0; k < 4; k++) { const t = ((f + k * 22) % 88) / 88; g.save(); g.globalAlpha = .5 * (1 - t); puff(g, x - 100 + k * 22 + Math.sin(t * 6 + k) * 12, y - 200 - t * 170, 10 + t * 26, '#e8e2d6', d + 120 + k, 4); g.restore(); } } }],
      xsheet: [[1, 'K01', 26, 'the cook works the griddle', 'hold', 'sizzle'], [26, 'K02', 10, 'anticipation: the spatula dips', 'hold', ''], [36, 'K03', 30, 'the toss: up on an arc, one and a half turns', 'hold', 'flip'],
        [66, 'K04', 30, 'the catch, a small squash', 'hold', 'slap'], [96, 'K05', 8, 'anticipation: the head dips the other way', 'hold', ''], [104, 'K06', 18, 'he turns to us', 'push in 60%', ''], [130, 'HOLD', 100, 'the stare. nothing moves but the steam', 'creep', 'silence']] }; })(),
  'THE SCREEN': (() => {   // inside the fort: the change requests type themselves; the four characters blink up in the screens; the cook watches, unmoved
    const msg = 'could you move it slightly left?\n> moved.\ncould the onions\nlook happier?\n> ...\nmake the wall\nmatch the render.\n> the tide disagrees.';
    return { dur: 220, camera: cam([{ f: 0, v: [-120, 0, 1] }, { f: 220, v: [100, -30, 1.3], e: 'io' }]),
      planes: [{ z: 6, draw: (g) => { g.fillStyle = '#2b2622'; g.fillRect(-W, -H, W * 3, H * 3); for (let r = 0; r < 14; r++) ink(g, [[-W, r * 60 - 100], [W * 2, r * 60 - 100]], { closed: false, d: r, w: 1, stroke: '#3a322c' }); } },
        { z: 2.5, draw: (g, f, d) => { const n = Math.floor(Math.max(0, f - 10) * 1.1); screen(g, -360, 140, 330, 240, msg, n, d); screen(g, 60, 110, 260, 200, '', 0, d + 9); screen(g, 380, 150, 280, 220, '', 0, d + 18);
            if (f > 60) shape(g, 'purple', 190, 300, .55, { d: d + 30, look: [Math.sin(f * .05), .3], blink: f % 70 < 3 ? 1 : 0 }); if (f > 100) shape(g, 'orange', 520, 360, .6, { d: d + 40, look: [-1, .2], mouth: f > 160 ? 'frown' : 'smile' }); } },
        { z: 1, draw: (g, f, d) => { ink(g, rr(-W, 470, W * 3, 400, 0), { fill: '#4a3d33', d, w: 2 }); cook(g, -40, 760, 1.6, { d: d + 9, turn: .15, tray: false, flip: 1.2 }); } },
        { z: .5, draw: (g, f, d) => { for (const x of [-720, 820]) ink(g, rr(x, -200, 240, 1200, 20), { fill: '#1d1916', d: d + x, w: 3 }); } }],
      xsheet: [[1, 'K01', 60, 'the screens wake; a change request types itself', 'slow truck R', 'keys'], [60, 'K02', 40, 'the purple character surfaces in a screen, eyes searching', 'truck', 'chime'],
        [100, 'K03', 60, 'the orange one, smiling, then not', 'push', ''], [160, 'HOLD', 60, 'the cook, from behind, does not move', 'push in 30%', 'hum']] }; })(),
  'THE TIDE': (() => {   // the onion ring rides a thin current through the drill holes to the drain; the camera follows at sand level
    const o = track([{ f: 0, v: [-520, 40] }, { f: 120, v: [80, 10], e: 'io', via: [-200, 70] }, { f: 190, v: [440, 0], e: 'in', via: [300, 30] }, { f: 206, v: [500, 0], e: 'in' }]);
    return { dur: 230, camera: cam([{ f: 0, v: [-380, 0, 1.2] }, { f: 200, v: [300, -10, 1.35], e: 'io' }, { f: 230, v: [320, -10, 1.4] }]),
      planes: [{ z: 9, draw: sky('#9fa6a8', '#e0d6bf') }, { z: 4, draw: (g, f, d) => { waves(g, 300, 3, 140, C.sea, f, .02, d); fort(g, 540, 350, 1.1, d + 9); } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 360], [W * 2, 350], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 });
            ink(g, [[-W, 440], [-300, 438], [0, 446], [300, 440], [470, 446], [470, 470], [300, 486], [0, 482], [-300, 494], [-W, 498]], { fill: '#7f9196', d: d + 3, w: 2 }); ink(g, rr(470, 380, 150, 110, 6), { fill: C.brick, d: d + 4, w: 2.4 }); ink(g, ell(500, 470, 34, 34, Math.PI, TAU, 10).concat([[534, 470], [466, 470]]), { fill: '#24140f', d: d + 5, w: 2 });
            [-400, -150, 120].forEach((x, i) => ink(g, ell(x, 520 + i * 6, 46, 14), { fill: '#6f5f48', d: d + 10 + i, w: 2 })); const [x, y] = o(f); if (f < 206) onion(g, Math.min(x, 500), 466 + y * .4, 1.2 - Math.max(0, x - 430) / 200, d + 20);
            for (let k = 0; k < 6; k++) ink(g, [[-500 + k * 200 + (f * 2 % 200), 462], [-470 + k * 200 + (f * 2 % 200), 458]], { closed: false, d: d + 30 + k, w: 1.6, stroke: '#cfd8d6' }); } },
        { z: .5, draw: (g, f, d) => { ink(g, [[-W, 690], [-200, 660], [400, 700], [W * 2, 670], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand2, d, w: 3 }); pail(g, -380, 700, 1.8, { d: d + 4 }); } }],
      xsheet: [[1, 'K01', 120, 'the onion rides the current on a long eased arc', 'truck R at sand level', 'trickle'], [120, 'K02', 70, 'it speeds as the channel narrows (slow-in, fast-out)', 'truck', ''], [190, 'K03', 20, 'into the dark of the drain', 'push', 'gulp'], [210, 'HOLD', 20, 'the arch, empty', 'hold', 'tide']] }; })(),
  'THE AFTERMATH': (() => {   // smoke thins; the pails stand like markers; the crew eat; the tall Slopling holds the last beam; the camera cranes up
    return { dur: 220, camera: cam([{ f: 0, v: [0, 120, 1.25] }, { f: 220, v: [0, -60, 1], e: 'io' }]),
      planes: [{ z: 9, draw: sky('#857e78', '#d4c4a4') }, { z: 4, draw: (g, f, d) => { waves(g, 330, 3, 120, C.sea2, f, .02, d); ship(g, 420, 336, .5, { d: d + 3, burn: 1, f }); } },
        { z: 2, draw: (g, f, d) => { fort(g, -300, 420, .8, d); ink(g, [[-420, 330], [-360, 290], [-300, 340], [-250, 300], [-200, 340], [-200, 420], [-420, 420]], { fill: '#d4c4a4', d: d + 1, w: 0, line: false, grain: false });   // the breach in the wall
            ink(g, [[-W, 430], [W * 2, 428], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand2, d: d + 2, w: 2 }); for (let k = 0; k < 9; k++) { g.save(); g.translate(-600 + k * 150, 470); g.rotate((hash(k) - .5) * (k % 3 ? .9 : 0)); pail(g, 0, 0, .55, { d: d + 10 + k }); g.restore(); }
            for (let k = 0; k < 5; k++) ink(g, rr(-560 + k * 260, 440 + hash(k + 3) * 20, 60 + hash(k) * 40, 14, 4), { fill: '#6e6258', d: d + 40 + k, w: 1.6 }); } },
        { z: 1, draw: (g, f, d) => { ink(g, [[-W, 520], [W * 2, 512], [W * 2, H * 2], [-W, H * 2]], { fill: C.sand, d, w: 2.4 }); const sx = 220, sy = 600, br = Math.sin(twos(f) * .08) * 3;
            ink(g, rr(sx - 30, sy - 260 + br, 60, 260 - br, 18), { fill: C.ivory, d: d + 5, w: 2.4 }); ink(g, ell(sx, sy - 284 + br, 26, 26), { fill: C.ivory, d: d + 6, w: 2.4 });   // the Slopling, tall, breathing
            ink(g, rr(sx - 260, sy - 330 + br, 520, 26, 4), { fill: '#7a5a38', d: d + 7, w: 2.4 }); for (const s of [-1, 1]) ink(g, [[sx + s * 24, sy - 230 + br], [sx + s * 40, sy - 320 + br]], { closed: false, d: d + 8 + s, w: 10, stroke: C.ivory });
            [-260, -120, 20].forEach((x, i) => { crew(g, x, sy, 1, { d: d + 20 + i, crouch: 1, arm: -1.5 - .3 * Math.max(0, Math.sin((twos(f) + i * 9) * .15)) }); burger(g, x + 30, sy - 70, .6, d + 30 + i); });
            [[380, 640], [-560, 650]].forEach(([x, y], i) => { g.save(); g.translate(x, y); g.rotate(-Math.PI / 2 + .1); crew(g, 0, 0, 1, { d: d + 70 + i, crouch: 0, arm: 1.2 }); g.restore(); });   // two lie flat, spent
            cook(g, -420, sy + 10, .9, { d: d + 50, turn: .9, tray: true }); } },
        { z: .6, draw: (g, f, d) => { const t = f / 220; g.save(); g.globalAlpha = .45 * (1 - t); for (let k = 0; k < 6; k++) puff(g, -500 + k * 240 + f * .6, 300 - k % 2 * 40, 140, C.smoke, d + k * 9, 6); g.restore(); } }],
      xsheet: [[1, 'K01', 80, 'smoke across the lens, thinning', 'crane up', 'wind'], [80, 'K02', 80, 'the crew eat; the Slopling breathes under the beam (a moving hold)', 'crane', 'chewing'], [160, 'K03', 60, 'the cook, facing us, a little apart', 'crane up, pull out', '']] }; })(),
  };
  // one sheet of the stack on its own (for the exploded view): the same camera, only plane i
  function sheet(g, shot, f, i) { const cam = shot.camera(f), pl = shot.planes[i], p = 1 / pl.z, z = 1 + (cam.zoom - 1) * p;
    g.save(); g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-cam.x * p, -H / 2 - cam.y * p); pl.draw(g, f, twos(f)); g.restore(); }
  const api = { W, H, FPS, SHOTS, photograph, sheet };
  if (typeof module !== 'undefined') module.exports = api; else root.SlopCartoon = api;
})(this);
