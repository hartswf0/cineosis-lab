/* From Imagetext to Worldtext: the stage. One drawing function per scene, each a pure function of time,
   so the slides, the film, the frame render and the PDF all draw the same thing.
   Bolas is the drawing from the Bolas page and The Play, ported from SVG to canvas unchanged in its proportions. */
(function (root) {
'use strict';
const W = 1280, H = 720;
const C = { bg: '#0b0a09', paper: '#ece6da', ink: '#0b0a09', red: '#e0483a', gold: '#e8c070', dim: '#3a3631', mute: '#8d867a', faint: '#24211d', berry: '#4f63a8' };
const SERIF = '"Cormorant Garamond", Georgia, serif', MONO = '"IBM Plex Mono", ui-monospace, Menlo, monospace';
const cl = v => Math.max(0, Math.min(1, v)), lerp = (a, b, u) => a + (b - a) * u;
const io = t => t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2, out = t => 1 - Math.pow(1 - t, 3);
const T = (t, a, b) => cl((t - a) / Math.max(1e-6, b - a));
/* deterministic noise */
const rnd = s => { const x = Math.sin(s * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

let X = null;                           /* the current 2d context */
let IMG = {};

/* ---------------- primitives ---------------- */
function line(x1, y1, x2, y2, col = C.paper, w = 2, dash) { X.beginPath(); X.moveTo(x1, y1); X.lineTo(x2, y2); X.strokeStyle = col; X.lineWidth = w; X.setLineDash(dash || []); X.lineCap = 'round'; X.stroke(); X.setLineDash([]); }
function thr(x1, y1, x2, y2, u = 1, w = 2.4, col = C.red) { if (u <= 0) return; line(x1, y1, lerp(x1, x2, u), lerp(y1, y2, u), col, w); }
function poly(pts, col = C.paper, w = 2, close = false, fill = null, dash) {
  if (!pts.length) return; X.beginPath(); pts.forEach(([x, y], i) => i ? X.lineTo(x, y) : X.moveTo(x, y)); if (close) X.closePath();
  if (fill) { X.fillStyle = fill; X.fill(); } if (col) { X.strokeStyle = col; X.lineWidth = w; X.lineJoin = 'round'; X.lineCap = 'round'; X.setLineDash(dash || []); X.stroke(); X.setLineDash([]); }
}
function circ(x, y, r, fill, stroke, w = 2) { X.beginPath(); X.arc(x, y, Math.max(0, r), 0, Math.PI * 2); if (fill) { X.fillStyle = fill; X.fill(); } if (stroke) { X.strokeStyle = stroke; X.lineWidth = w; X.stroke(); } }
function rect(x, y, w, h, fill, stroke, lw = 2, dash) { if (fill) { X.fillStyle = fill; X.fillRect(x, y, w, h); } if (stroke) { X.strokeStyle = stroke; X.lineWidth = lw; X.setLineDash(dash || []); X.strokeRect(x, y, w, h); X.setLineDash([]); } }
function font(o) { return `${o.italic ? 'italic ' : ''}${o.weight || (o.mono ? 500 : 400)} ${o.size || 20}px ${o.mono ? MONO : SERIF}`; }
function txt(s, x, y, o = {}) {
  X.save(); X.font = font(o); X.fillStyle = o.col || C.paper; X.textAlign = o.align || 'left'; X.textBaseline = o.base || 'alphabetic';
  if ('letterSpacing' in X) X.letterSpacing = o.ls ? o.ls + 'px' : '0px';
  X.globalAlpha *= o.a == null ? 1 : o.a; X.fillText(s, x, y); X.restore();
}
function measure(s, o) { X.save(); X.font = font(o); if ('letterSpacing' in X) X.letterSpacing = o.ls ? o.ls + 'px' : '0px'; const w = X.measureText(s).width; X.restore(); return w; }
function wrap(s, maxw, o) {
  const words = s.split(' '), lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (measure(t, o) > maxw && cur) { lines.push(cur); cur = w; } else cur = t; }
  if (cur) lines.push(cur); return lines;
}
function alpha(a, fn) { if (a <= 0) return; X.save(); X.globalAlpha *= Math.min(1, a); fn(); X.restore(); }
function knot(x, y, u = 1, col = C.red) { if (u <= 0) return; const r = 6.5 * (u < 1 ? out(u) * 1.25 - .25 * u : 1); circ(x, y, r, col); }
function bars(x, y, ws, h = 7, gap = 9, col = C.dim) { let cx = x; ws.forEach(w => { rect(cx, y - h / 2, w, h, col); cx += w + gap; }); }
/* a mono label in a thin box */
function tag(s, x, y, o = {}) { const sz = o.size || 12, w = measure(s, { mono: 1, size: sz, ls: 1 }) + 16; const xx = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x; rect(xx, y - sz - 5, w, sz + 12, o.fill || null, o.col || C.mute, 1.2); txt(s, xx + 8, y + 1, { mono: 1, size: sz, col: o.tcol || o.col || C.mute, ls: 1 }); return w; }

/* ---------------- Bolas (from The Play, ported to canvas) ---------------- */
function bolas(p) {
  const q = Object.assign({ x: 0, y: 0, sx: 1, sy: 1, rot: 0, spread: 1, drag: 0, look: [0, .6], lit: 0, blink: 0, wink: 0, ax: null, ay: null, s: 1, legPhase: 0, tw: 1.6 }, p);
  const r = q.rot * Math.PI / 180, k = q.s, top = { x: q.x + Math.sin(r) * 28 * k * q.sy, y: q.y - Math.cos(r) * 28 * k * q.sy };
  if (q.ax != null) line(q.ax, q.ay, top.x, top.y, C.red, q.tw * Math.min(1.4, k));
  X.save(); X.translate(q.x, q.y); X.rotate(r); X.scale(q.sx * k, q.sy * k);
  for (const side of [-1, 1]) for (let i = 0; i < 4; i++) {
    const ay = 8 + i * 3.4, axx = side * 7.5, ph = Math.sin(q.legPhase + i * 1.3 + (side > 0 ? .7 : 0)) * 3;
    const kx = side * (17 + i * 3.2) * q.spread, ky = ay - 15 + i * 3 - q.drag * 5 + ph;
    const fx = side * (25 + i * 5.4) * q.spread, fy = ky + 19 + i * 3 - q.drag * 10 + ph * 1.5;
    poly([[axx, ay], [kx, ky], [fx, fy]], C.paper, 2.4);
  }
  X.beginPath(); X.ellipse(0, -8, 16, 19, 0, 0, Math.PI * 2); X.fillStyle = C.paper; X.fill();
  X.beginPath(); X.roundRect ? X.roundRect(-2.4, -27, 4.8, 25, 2.4) : X.rect(-2.4, -27, 4.8, 25); X.fillStyle = C.red; X.fill();
  circ(0, 15, 11.5, C.paper);
  [[-8.6, 9.6], [-4.2, 7], [4.2, 7], [8.6, 9.6], [-10.6, 15.5], [10.6, 15.5]].forEach(([x, y], j) => circ(x, y, 1.6, j < q.lit ? C.gold : C.ink));
  for (const side of [-1, 1]) {
    const ex = side * 4.6, ey = 15, c = Math.max(q.blink, side > 0 ? q.wink : 0);
    X.beginPath(); X.ellipse(ex, ey, 4.4, Math.max(.3, 4.4 * (1 - .9 * c)), 0, 0, Math.PI * 2); X.fillStyle = C.ink; X.fill();
    if (c < .6) circ(ex + q.look[0] * 1.5 - .9, ey + q.look[1] * 1.3 - 1.4, 1.5, '#ffffff');
  }
  X.beginPath(); X.moveTo(-2.4, 23.5); X.lineTo(-3.3, 26.1); X.moveTo(2.4, 23.5); X.lineTo(3.3, 26.1); X.strokeStyle = C.dim; X.lineWidth = 1.6; X.stroke();
  X.restore();
}
/* the y at which Bolas stands with its feet on ground g */
const stand = (g, s) => g - 40 * s - 2;
/* the wink mark from Wink, Not Blink: a ring, two eyes, the red thread; r = right lid */
function mark(x, y, R, e = {}) {
  const INK = e.ink || C.paper, l = e.l || 0, r = e.r || 0, w = R * .14, er = R * .17, ex = R * .34, ln = e.line ?? R * 1.2;
  if (ln) line(x, y - R - ln, x, y - R, C.red, Math.max(1.4, R * .05));
  X.save(); X.translate(x, y); X.rotate(r > .85 ? -6 * Math.PI / 180 : 0);
  circ(0, 0, R - w / 2, null, INK, w);
  [[-1, l], [1, r]].forEach(([sd, c]) => {
    const cx = sd * ex;
    if (c < .85) { X.beginPath(); X.ellipse(cx, 0, er, Math.max(.2, er * (1 - c)), 0, 0, Math.PI * 2); X.fillStyle = INK; X.fill(); }
    else { X.beginPath(); X.moveTo(cx - er * 1.15, 0); X.quadraticCurveTo(cx, .9 * er * 1.3, cx + er * 1.15, 0); X.strokeStyle = INK; X.lineWidth = er * .55; X.lineCap = 'round'; X.stroke(); }
  });
  X.restore();
}
/* keyframes: [[t, v], ...] where v is a number or an array; eased between keys */
function kf(t, keys, ease = io) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t < keys[i][0]) {
    const [t0, a] = keys[i - 1], [t1, b] = keys[i], u = ease((t - t0) / (t1 - t0));
    return Array.isArray(a) ? a.map((v, j) => lerp(v, b[j], u)) : lerp(a, b, u);
  }
  return keys[keys.length - 1][1];
}
/* is the keyframed value moving at t (for the legs) */
function moving(t, keys) { for (let i = 1; i < keys.length; i++) if (t >= keys[i - 1][0] && t < keys[i][0]) { const a = keys[i - 1][1], b = keys[i][1]; return (Array.isArray(a) ? a.some((v, j) => Math.abs(v - b[j]) > 1) : Math.abs(a - b) > 1); } return false; }
function blinkAt(t, at, d = .18) { const u = (t - at) / d; return u > 0 && u < 1 ? Math.sin(u * Math.PI) : 0; }
/* a hanging Bolas following keyframes [[t,[x,y]],...]; returns the pose for further tweaks */
function hang(t, keys, o = {}) {
  const [x, y] = kf(t, keys), mv = moving(t, keys);
  const p = Object.assign({ x, y, s: 1.3, ax: x, ay: -4, legPhase: mv ? t * 14 : Math.sin(t * 1.3) * .4, look: [0, .6] }, o);
  return p;
}
/* small figures */
function walker(x, g, o = {}) {
  const s = o.s || 1, ph = o.ph || 0, st = C.paper;
  circ(x, g - 62 * s, 9 * s, st);
  line(x, g - 52 * s, x, g - 24 * s, st, 3);
  const a = Math.sin(ph) * 9 * s;
  line(x, g - 24 * s, x - a, g, st, 3); line(x, g - 24 * s, x + a, g, st, 3);
  line(x, g - 46 * s, x - a * .8 - 3, g - 30 * s, st, 3); line(x, g - 46 * s, x + a * .8 + 3, g - 30 * s, st, 3);
  if (o.lookUp) circ(x - 2, g - 66 * s, 2, C.ink); else circ(x + (o.face || -1) * 4, g - 63 * s, 2, C.ink);
}
function frameGlyph(k, x, y, s, col = C.paper) {
  if (k === 0) circ(x, y, 12 * s, null, col, 2);
  else if (k === 1) rect(x - 11 * s, y - 11 * s, 22 * s, 22 * s, null, col, 2);
  else if (k === 2) poly([[x, y - 13 * s], [x + 13 * s, y + 10 * s], [x - 13 * s, y + 10 * s]], col, 2, true);
  else poly([[x - 14 * s, y], [x - 7 * s, y - 8 * s], [x, y], [x + 7 * s, y + 8 * s], [x + 14 * s, y]], col, 2);
}
/* the house facade, turnable about its centre: ang 0 faces us; 90 shows its edge */
function house(cx, g, sc, ang, door = {}) {
  const w = 380 * sc, h = 230 * sc, roof = 95 * sc, sx = Math.max(.012, Math.cos(ang));
  X.save(); X.translate(cx, 0); X.scale(sx, 1); X.translate(-cx, 0);
  const x0 = cx - w / 2, x1 = cx + w / 2, y0 = g - h;
  poly([[x0, g], [x0, y0], [cx, y0 - roof], [x1, y0], [x1, g]], C.paper, 2.4 / sx * Math.min(1, sx * 4) || 2.4);
  const dx = cx - 40 * sc, dw = 70 * sc, dh = 120 * sc;
  rect(dx, g - dh, dw, dh, null, C.paper, 2);
  circ(dx + dw - 12 * sc, g - dh / 2, 3.2 * sc, C.paper);
  rect(cx + 70 * sc, y0 + 40 * sc, 70 * sc, 56 * sc, null, C.paper, 2); line(cx + 105 * sc, y0 + 40 * sc, cx + 105 * sc, y0 + 96 * sc, C.paper, 1.5);
  X.restore();
  if (sx < .12) rect(cx - 2, g - h - roof, 4, h + roof, C.paper);
  return { dx: cx + (dx - cx) * sx, dw: dw * sx, dy: g - dh, dh };
}

/* ---------------- timing ---------------- */
function words(s) { return s.split(/\s+/).filter(Boolean); }
function estimate(deck) {
  let t = 0; return { scenes: deck.scenes.map(sc => {
    let c = .8; const s = sc.say.map(x => { const d = x.t.length / 14.5 + .2; const r = { t0: c, t1: c + d }; c += d + .35; return r; });
    const d = c - .35 + (sc.tail || 2); const o = { id: sc.id, t0: t, d, s }; t += d; return o;
  }), total: t };
}
function timingFor(deck, tm) {
  const base = tm && tm.scenes && tm.scenes.length === deck.scenes.length ? tm : estimate(deck);
  return base;
}

/* ---------------- scene context ---------------- */
function ctxFor(sc, tsc, t, opts) {
  const S = tsc.s.map((s, i) => ({ t0: s.t0, t1: s.t1, text: sc.say[i].t }));
  const w = (i, word, after) => {
    const s = S[i]; if (!s) return 0; const lo = s.text.toLowerCase(); let k = lo.indexOf(word.toLowerCase(), after || 0); if (k < 0) k = 0;
    return s.t0 + (k / Math.max(1, s.text.length)) * (s.t1 - s.t0);
  };
  const ev = [];
  return { t, D: tsc.d, S, w, a: i => S[Math.min(i, S.length - 1)].t0, e: i => S[Math.min(i, S.length - 1)].t1, ev: x => ev.push(x), events: ev, opts: opts || {} };
}

/* ================= the scenes ================= */
const SC = {};

/* 1 title / end */
function titleCard(k, sc, end) {
  const t = k.t, D = k.D, U = 418;
  const ttl = sc.line, tsz = 84;
  const tw = measure(ttl, { size: tsz });
  const x0 = 120, x1 = Math.max(1080, x0 + tw + 40);
  if (!end) {
    const tDrop = [0, 1.3], tSpin = [1.5, Math.max(4.2, D - 2.6)];
    k.ev(tDrop[1]); k.ev(tSpin[0]);
    line(x1, -4, x1, U, C.red, 2);
    const bx = kf(t, [[tSpin[0], x1], [tSpin[1], x0]], u => u);
    if (t > tSpin[0]) line(bx, U, x1, U, C.red, 2.6);
    const hy = U + 52;
    let p;
    if (t < tDrop[1]) p = { x: x1, y: lerp(-80, hy, out(T(t, tDrop[0], tDrop[1]))), ax: x1, ay: -4 };
    else p = { x: t < tSpin[0] ? x1 : bx, y: hy + Math.sin(t * 2) * 1.5, ax: t < tSpin[0] ? x1 : bx, ay: U, legPhase: t > tSpin[0] && t < tSpin[1] ? t * 16 : 0, look: [-1, .2] };
    p.s = 1.25; p.lit = Math.floor(6 * T(t, tSpin[1] - .2, tSpin[1] + 1.2)); p.blink = blinkAt(t, D - 1.0);
    if (t > tSpin[1]) p.look = [0, .8];
    bolas(p);
  } else {
    line(x0, U, x1, U, C.red, 2.6);
    const up = [k.e(0) + .4, D - .4]; k.ev(up[0]);
    const bx = x1 + 70, y = lerp(U + 40, -120, io(T(t, up[0], up[1])));
    bolas({ x: bx, y, ax: bx, ay: -4, s: 1.25, legPhase: t > up[0] ? t * 12 : 0, lit: 6, look: [0, -1], blink: blinkAt(t, up[0] - .6) });
  }
  revealLine(k, ttl, x0, 360, tsz, 0);
  alpha(end ? 1 : T(t, k.a(1) - .2, k.a(1) + .6), () => txt(sc.sub, x0 + 2, U + 140, { mono: 1, size: end ? 17 : 19, col: C.mute, ls: .5 }));
}
SC.title = (k, sc) => titleCard(k, sc, false);
SC.end = (k, sc) => titleCard(k, sc, true);

/* the line, revealed word by word across its sentence (film) or all at once (slides) */
function revealLine(k, s, x, y, size, maxw) {
  const o = { size };
  const show = k.sc.say.findIndex(q => q.show), si = show < 0 ? 0 : show;
  const S = k.S[si];
  const ws = words(s); let cx = x, cy = y; const sp = measure(' ', o), lineH = size * 1.08;
  const total = s.length; let pos = 0;
  ws.forEach(wd => {
    const ww = measure(wd, o);
    if (maxw && cx + ww > x + maxw && cx > x) { cx = x; cy += lineH; }
    let a = 1;
    if (k.opts.reveal) { const at = S.t0 + (pos / total) * (S.t1 - S.t0) - .05; a = T(k.t, at, at + .28); }
    else if (k.opts.fade) a = T(k.t, 0, .5);
    alpha(a, () => txt(wd, cx, cy + (1 - a) * 6, o));
    cx += ww + sp; pos += wd.length + 1;
  });
}

/* 2 a house can look right */
SC.entrance = (k) => {
  const t = k.t, g = 618, s = 1.3, sy = stand(g, s);
  const e0 = Math.max(k.e(0), 3.2), p1 = e0 + .25, p2 = e0 + 1.25, turn = [e0 + 2.4, e0 + 3.5, e0 + 4.4, e0 + 5.4];
  line(60, g, 1220, g, C.dim, 2);
  const ang = kf(t, [[turn[0], 0], [turn[1], 1.47], [turn[2], 1.47], [turn[3], 0]]);
  const d = house(830, g, 1, ang);
  const keys = [[.5, [170, sy]], [e0 - .1, [d.dx - 34, sy]]];
  const push = (a) => T(t, a, a + .18) - T(t, a + .35, a + .6);
  const pu = Math.max(push(p1), push(p2));
  const p = hang(t, keys, { s, ay: -4 });
  p.rot = 14 * pu; p.drag = -.5 * pu; p.spread = 1 - .15 * pu; p.look = t > turn[0] ? [1, .3] : [1, .5];
  if (t > turn[3] + .2) p.look = [0, 1];
  p.blink = blinkAt(t, turn[3] + 1.0);
  p.x += 8 * pu;
  bolas(p);
  if (pu > .5) [[0, -24], [6, -8], [0, 8]].forEach(([ox, oy]) => line(p.x + 44 + ox, p.y + oy, p.x + 54 + ox, p.y + oy - 2, C.mute, 1.5));
};

/* 3 a film can match every noun */
SC.voice = (k) => {
  const t = k.t;
  const LY = [300, 360, 420, 480], NX = [210, 330, 170, 290], ws = [[60, 40, 72, 50, 90], [80, 50, 70, 60, 44], [50, 76, 46, 88, 60], [70, 42, 66, 56, 74]];
  const nb = [];
  LY.forEach((y, i) => {
    let cx = 100; ws[i].forEach((w, j) => {
      if (j === (i % 2 ? 2 : 1)) { nb.push([cx, y, 70]); rect(cx, y - 15, 70, 30, null, C.paper, 1.6); frameGlyph(i, cx + 35, y, .6); cx += 70 + 10; }
      else { rect(cx, y - 4, w, 8, C.dim); cx += w + 10; }
    });
  });
  /* the voice: a line that runs under the poem's lines, phrase by phrase, and stops at the edge of the film */
  X.save(); X.beginPath(); let first = true;
  LY.forEach((y, i) => { for (let x = 100; x <= 560; x += 4) { const amp = 5 + 4 * Math.sin(x * .021 + i), yy = y + 26 + Math.sin(x * .09 - t * 4 + i * 2) * amp * (.6 + .4 * Math.sin(x * .013 + i)); if (first) { X.moveTo(x, yy); first = false; } else X.lineTo(x, yy); } });
  X.strokeStyle = C.mute; X.lineWidth = 1.6; X.stroke(); X.restore();
  txt('voice', 100, 540, { mono: 1, size: 12, col: C.mute, ls: 1 });
  /* the film */
  const fx = 700, fy = 290, fw = 480, fh = 150;
  rect(fx, fy, fw, fh, null, C.paper, 2);
  for (let i = 0; i < 16; i++) { rect(fx + 10 + i * 30, fy + 8, 12, 8, C.dim); rect(fx + 10 + i * 30, fy + fh - 16, 12, 8, C.dim); }
  const FR = [0, 1, 2, 3].map(i => [fx + 12 + i * 117, fy + 26, 105, 98]);
  FR.forEach(f => rect(...f, null, C.dim, 1.5));
  line(fx, 480, fx + fw, 480, C.mute, 1.6);
  txt('sound', fx, 540, { mono: 1, size: 12, col: C.mute, ls: 1 });
  const st = i => .9 + i * 1.9, carry = 1.1;
  [0, 1, 2, 3].forEach(i => k.ev(st(i)));
  let bx = 600, by = 210;
  nb.forEach(([x, y, w], i) => {
    const u = T(t, st(i), st(i) + carry), f = FR[i];
    const ax = x + w, ay = y, tx = f[0] + f[2] / 2, ty = f[1] + f[3] / 2;
    if (u > 0) thr(ax, ay, tx, ty, io(u), 1.8);
    if (u >= 1) frameGlyph(i, tx, ty, 1.3);
  });
  const keys = [[0, [620, 190]]]; nb.forEach(([x, y, w], i) => { const f = FR[i]; keys.push([st(i) - .45, [x + w + 18, y - 64]], [st(i) + carry, [f[0] + f[2] / 2, f[1] - 64]]); });
  keys.push([st(3) + carry + 1, [640, 200]]);
  const p = hang(t, keys, { s: 1.05 });
  p.look = [0, 1]; p.lit = Math.min(6, Math.floor(t / 1.9) + 1); p.blink = blinkAt(t, k.D - 1.2);
  bolas(p);
};

/* 4 an agent can follow each instruction */
SC.outcome = (k) => {
  const t = k.t, g = 620, B = 64;
  line(0, g, 1280, g, C.dim, 2);
  const cards = ['1  put a block on the road', '2  put a block on the block', '3  put a block on top'];
  const cyc = i => .7 + i * 2.3;
  cards.forEach((c, i) => { rect(780, 212 + i * 54, 360, 42, null, C.dim, 1.5); txt(c, 796, 239 + i * 54, { mono: 1, size: 15, col: C.paper }); if (t > cyc(i) + 2.0) poly([[1154, 233 + i * 54], [1162, 241 + i * 54], [1178, 222 + i * 54]], C.paper, 2.4); });
  /* the pile and the tower */
  const tx = 700, pile = 150;
  for (let i = 0; i < 3; i++) {
    const c0 = cyc(i), pick = c0 + .55, drop = c0 + 1.85;
    k.ev(pick);
    const by = g - B * (i + 1) + B / 2;
    let x = pile + (2 - i) * 6, y = g - B / 2 - (2 - i) * 0;
    if (i === 0) y = g - B / 2; else y = g - B / 2 - 0;
    /* blocks wait side by side on the pile */
    x = pile - 70 + i * 70; y = g - B / 2;
    let bxy = [x, y];
    if (t >= pick) {
      const u = T(t, pick, drop);
      const path = [[pick, [x, y]], [pick + .35, [x, 420]], [drop - .45, [tx, 420]], [drop, [tx, by]]];
      bxy = kf(t, path);
      if (t < drop + .2) { const bp = kf(t, [[pick, [x, 360]], [pick + .35, [x, 360]], [drop - .45, [tx, 360]], [drop, [tx, 360]]]); thr(bp[0], bp[1] + 40, bxy[0], bxy[1] - B / 2, 1, 1.8); }
    }
    rect(bxy[0] - B / 2, bxy[1] - B / 2, B, B, '#2b2722', C.paper, 2);
  }
  /* Bolas works the crane above */
  const keys = [[0, [pile - 70, 300]]];
  for (let i = 0; i < 3; i++) { const c0 = cyc(i); keys.push([c0 + .45, [pile - 70 + i * 70, 300]], [c0 + .55, [pile - 70 + i * 70, 300]], [c0 + 1.4, [tx, 300]], [c0 + 2.0, [tx, 300]]); }
  keys.push([cyc(2) + 2.8, [560, 290]]);
  const p = hang(t, keys, { s: 1.15 });
  const wStart = cyc(2) + 2.6, wStop = wStart + 2.4;
  p.look = t > wStart ? [1, .5] : [0, 1]; p.lit = t > cyc(2) + 2 ? 6 : 0;
  p.blink = blinkAt(t, wStop + 1.2);
  bolas(p);
  const wx = kf(t, [[wStart, 1330], [wStop, tx + 90]], u => u);
  walker(wx, g, { ph: t < wStop ? t * 9 : 0, lookUp: t > wStop + .3, face: -1 });
};

/* 5 the question */
SC.question = (k) => {
  const t = k.t;
  rect(170, 300, 260, 260, null, C.paper, 2);
  [[150, 190], [210, 120], [180, 160], [200, 90], [140, 170], [190, 110]].forEach((ws, i) => bars(196, 334 + i * 36, ws.slice(0, 1).concat(i % 2 ? [40] : []), 7, 10, C.dim));
  const tg = [[880, 290, 'intelligible action'], [880, 440, 'coherent worlds'], [880, 590, 'accountable interpretation']];
  const at = [k.w(1, 'intelligible') - .3, k.w(1, 'coherent') - .3, k.w(1, 'accountable') - .3];
  at.forEach(a => k.ev(a));
  tg.forEach(([x, y, lab], i) => {
    const on = T(t, at[i] + .7, at[i] + 1.1);
    alpha(.3 + .7 * on, () => {
      if (i === 0) { walker(x + 4, y + 38, { s: .9, ph: .8 }); line(x - 30, y + 38, x + 40, y + 38, C.mute, 1.5); }
      if (i === 1) { circ(x, y, 46, null, C.paper, 2); line(x - 46, y + 8, x + 46, y + 8, C.paper, 1.5); poly([[x - 14, y + 8], [x - 14, y - 10], [x, y - 22], [x + 14, y - 10], [x + 14, y + 8]], C.paper, 1.6); }
      if (i === 2) mark(x, y, 34, { r: 1, line: 0 });
      txt(lab, x + 70, y + 6, { mono: 1, size: 15, col: C.paper });
    });
    const u = T(t, at[i], at[i] + .8);
    thr(430, 360 + i * 70, x - 52, y, io(u), 2.2);
  });
  const keys = [[0, [470, 250]], [Math.max(.1, at[0] - .5), [470, 250]]];
  at.forEach((a, i) => keys.push([a, [470, 300 + i * 70 - 70]], [a + .8, [tg[i][0] - 120, tg[i][1] - 70]]));
  keys.push([at[2] + 1.8, [700, 230]]);
  const p = hang(t, keys, { s: 1.15 });
  p.lit = Math.floor(6 * T(t, .5, at[0])); p.look = [1, .4]; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 6 three thresholds */
SC.thresholds = (k) => {
  const t = k.t, g = 600, s = 1.15, sy = stand(g, s), XS = [380, 680, 980];
  line(60, g, 1220, g, C.dim, 2);
  XS.forEach((x, i) => { line(x, 300, x, g, C.mute, 2); txt(['I', 'II', 'III'][i], x, 284, { mono: 1, size: 15, col: C.mute, align: 'center', ls: 2 }); });
  const keys = [[0, [140, sy]], [k.a(1), [140, sy]], [k.e(1) + .2, [470, sy]], [k.a(2) + .1, [470, sy]], [k.e(2) + .2, [790, sy]], [k.a(3) + .1, [790, sy]], [k.a(3) + (k.e(3) - k.a(3)) * .7, [1110, sy]]];
  const p = hang(t, keys, { s });
  const bx = p.x, ty = g - 18;
  k.ev(k.a(1));
  if (t > k.a(1)) line(140, ty, bx - 10, ty, C.red, 2.2);
  /* the web after II */
  const tw = keys[4][0] - .9 * (keys[4][0] - keys[3][0]) + (XS[1] - 470) / (790 - 470) * (keys[4][0] - keys[3][0]);
  k.ev(tw);
  const wu = T(t, tw, tw + 1.1), cx = 530, cy = 430;
  if (wu > 0) {
    for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; thr(cx, cy, cx + Math.cos(a) * 82, cy + Math.sin(a) * 82, wu, 1.5); }
    [36, 64, 82].forEach((r, j) => alpha(T(wu, .3 + j * .2, .6 + j * .2), () => poly([...Array(9)].map((_, i) => { const a = i / 8 * Math.PI * 2; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; }), C.red, 1.4)));
    thr(cx, cy + 82, cx, ty, wu, 1.5);
  }
  /* the tangle after III */
  const tt = keys[6][0] - (1110 - XS[2]) / (1110 - 790) * (keys[6][0] - keys[5][0]);
  k.ev(tt);
  const nu = T(t, tt, tt + 2.6);
  if (nu > 0) for (let i = 0; i < 46; i++) {
    const a = [lerp(320, 1040, rnd(i * 3.1)), lerp(320, 560, rnd(i * 5.7))], b = [lerp(320, 1040, rnd(i * 7.3 + 1)), lerp(320, 560, rnd(i * 2.9 + 4))];
    const u = T(nu, i / 46 * .7, i / 46 * .7 + .3); if (u > 0) alpha(.55, () => thr(a[0], a[1], b[0], b[1], u, 1.1));
  }
  p.look = t > tt + 1 ? [-1, -.3] : [1, .4];
  if (t > tt + 1.2) { p.rot = -6; }
  p.blink = blinkAt(t, k.D - 1.2);
  bolas(p);
};

/* 7 from thick description to thick prompting: the documented encounter */
SC.encounter = (k) => {
  const t = k.t, Y = 440, KX = [230, 450, 670, 890, 1110], LB = ['wanted', 'supplied', 'appeared', 'judged', 'changed'];
  const at = LB.map(w => k.w(3, w) - .15);
  at.forEach(a => k.ev(a));
  const keys = [[0, 110], [.8, 140], [k.a(3) - .2, 190]]; at.forEach((a, i) => keys.push([a, KX[i]]));
  keys.push([k.D - .6, 1222]);
  const x = kf(t, keys, u => u);
  line(110, Y, x, Y, C.red, 2.4);
  KX.forEach((kx, i) => {
    const u = T(t, at[i], at[i] + .3);
    knot(kx, Y, u);
    alpha(T(t, at[i], at[i] + .4), () => txt(LB[i], kx, Y + 52, { mono: 1, size: 17, col: C.paper, align: 'center' }));
  });
  bolas({ x, y: Y + 50 + Math.sin(t * 2) * 1.2, ax: x, ay: Y, s: 1.1, legPhase: moving(t, keys) ? t * 15 : 0, look: [1, .3], lit: Math.floor(6 * T(t, at[0], at[4])), blink: blinkAt(t, k.D - .4) });
};

/* 8 the stopping rule */
SC.stopping = (k) => {
  const t = k.t;
  const cards = [['reference', true], ['more detail', false], ['constraint', true], ['more detail', false]];
  const span0 = k.a(1) + .3, span1 = k.e(3) - .5, step = (span1 - span0) / 4;
  rect(100, 230, 240, 64, null, C.paper, 2); txt('prompt', 116, 256, { mono: 1, size: 13, col: C.mute, ls: 1 }); bars(116, 278, [120, 60], 6, 8, C.dim);
  /* outcome frame */
  rect(820, 250, 340, 280, null, C.paper, 2); txt('outcome', 820, 236, { mono: 1, size: 13, col: C.mute, ls: 1 });
  line(840, 480, 1140, 480, C.dim, 1.5);
  let fx = 990, fy = 480, doorA = 0;
  let stacked = 0; const asideX = [380, 650];
  let bxy = [640, 180];
  const keys = [[0, [560, 190]]];
  cards.forEach(([lab, keep], i) => {
    const c0 = span0 + i * step, arrive = c0 + step * .35, judge = arrive + step * .25, leave = c0 + step * .85;
    k.ev(arrive);
    const slotY = 310 + stacked * 56;
    let pos;
    if (keep) { pos = kf(t, [[c0, [640, 170]], [arrive, [100, slotY]]]); }
    else { const ai = i === 1 ? 0 : 1; pos = kf(t, [[c0, [640, 170]], [arrive, [100, slotY]], [judge + .1, [100, slotY]], [leave, [asideX[ai], 600]]]); }
    if (t > c0 - .01) {
      const set = !keep && t > leave;
      alpha(set ? .5 : 1, () => { rect(pos[0], pos[1], 240, 46, C.bg, keep && t > judge ? C.red : C.paper, 1.6); txt(lab, pos[0] + 14, pos[1] + 29, { mono: 1, size: 15, col: C.paper }); });
      if (keep && t > judge) txt('changed it', pos[0] + 250, pos[1] + 29, { mono: 1, size: 12, col: C.red });
      if (!keep && t > judge && t < leave) txt('no change', pos[0] + 250, pos[1] + 29, { mono: 1, size: 12, col: C.mute });
    }
    if (keep) { stacked++; if (lab === 'reference') { const u = T(t, judge - .1, judge + .6); fx = lerp(990, 900, io(u)); } else { doorA = T(t, judge - .1, judge + .6); } }
    keys.push([c0 - .05, [660, 150]], [arrive, [220, slotY - 70]], [keep ? judge + .3 : leave, keep ? [240, slotY - 70] : [asideX[i === 1 ? 0 : 1] + 120, 530]]);
  });
  alpha(doorA, () => { rect(1060, 380, 54, 100, null, C.paper, 2); });
  if (doorA > 0) fx = lerp(fx, 1030, io(doorA));
  walker(fx, fy, { s: 1.1, face: 1 });
  txt('set aside', 380, 680, { mono: 1, size: 12, col: C.mute, ls: 1 });
  keys.push([span1 + .6, [560, 200]]);
  const p = hang(t, keys, { s: 1.05 });
  const stopped = t > span1 + .8; p.spread = stopped ? .78 : 1; p.look = stopped ? [0, 1] : [1, .5]; p.blink = blinkAt(t, k.D - 1.1);
  bolas(p);
};

/* 9, 14, 18: the experiment cards */
function expCard(k, sc, n) {
  const t = k.t, Y = 430, s = 1.3;
  txt(sc.numeral, 96, 600, { size: 230, col: C.paper, a: .92 });
  const lx0 = n === 1 ? 300 : n === 2 ? 340 : 400;
  line(lx0, Y, 1200, Y, C.paper, 2);
  /* what the earlier thresholds left behind */
  if (n >= 2) line(lx0, Y - 14, 1080, Y - 14, C.red, 2);
  if (n === 2) { const cx = 1000, cy = 300; for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; line(cx, cy, cx + Math.cos(a) * 52, cy + Math.sin(a) * 52, C.red, 1.2); } [26, 52].forEach(r => poly([...Array(9)].map((_, i) => { const a = i / 8 * Math.PI * 2; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; }), C.red, 1.2)); line(cx, cy + 52, cx, Y - 14, C.red, 1.2); }
  if (n === 3) alpha(.5, () => { for (let i = 0; i < 40; i++) { const a = [lerp(560, 1180, rnd(i * 3.1)), lerp(230, 400, rnd(i * 5.7))], b = [lerp(560, 1180, rnd(i * 7.3 + 1)), lerp(230, 400, rnd(i * 2.9 + 4))]; line(a[0], a[1], b[0], b[1], C.red, 1.1); } });
  const bx = 1110, land = 1.2; k.ev(land);
  const y = t < land ? lerp(-80, stand(Y, s), out(T(t, 0, land))) : stand(Y, s);
  const jolt = T(t, land, land + .15) - T(t, land + .15, land + .4);
  bolas({ x: bx, y: y + jolt * 4, ax: bx, ay: -4, s, sy: 1 - .12 * jolt, sx: 1 + .1 * jolt, look: [-1, .5], lit: n * 2, blink: blinkAt(t, k.D - 1.2), legPhase: 0 });
  sc.tags.forEach((nm, i) => {
    const at = k.a(1) + i * .45; k.ev(at);
    const u = T(t, at, at + .7); if (u <= 0) return;
    const x = 360 + i * 230 + (n === 1 ? -40 : 0), sw = Math.sin((t - at) * 6) * Math.exp(-(t - at) * 2.2) * .12;
    X.save(); X.translate(x + 95, Y); X.rotate(sw); X.translate(-(x + 95), -Y);
    const ty = lerp(Y - 30, Y + 44, out(u));
    line(x + 95, Y, x + 95, ty, C.red, 1.5);
    alpha(u, () => {
      rect(x, ty, 190, 88, C.bg, C.mute, 1.4);
      txt('PROVOCATION', x + 12, ty + 22, { mono: 1, size: 10, col: C.mute, ls: 1.5 });
      wrap(nm, 168, { size: 23, italic: 1 }).forEach((l, j) => txt(l, x + 12, ty + 50 + j * 24, { size: 23, italic: 1 }));
    });
    X.restore();
  });
}
SC.exp1 = (k, sc) => expCard(k, sc, 1);
SC.exp2 = (k, sc) => expCard(k, sc, 2);
SC.exp3 = (k, sc) => expCard(k, sc, 3);

/* 10 a wink is an interpretation */
SC.wink = (k) => {
  const t = k.t, xs = [420, 860], y = 360, s = 2.3, ly = 600;
  const ev = [k.a(1) + .5, k.a(2) + .7];
  const clos = t0 => { const g = T(t, t0 - .5, t0 - .2), c = T(t, t0, t0 + .35) - T(t, t0 + .85, t0 + 1.3); return { g, c: io(Math.max(0, c)) }; };
  xs.forEach((x, i) => {
    let c = 0, look = [0, .6];
    ev.forEach(e => { const r = clos(e); c = Math.max(c, r.c); if (r.g > 0 && t < e + 1.3) look = [i ? -.4 : .4, 1]; });
    bolas({ x, y, ax: x, ay: -4, s, wink: c, look, lit: 0, legPhase: Math.sin(t * 1.1) * .3 });
    line(x - 170, ly, x + 170, ly, C.dim, 2);
    ev.forEach((e, j) => {
      const tx = x - 120 + j * 160; if (i === 1) k.ev(e + .3); if (t < e) return;
      if (i === 0) line(tx, ly - 9, tx, ly + 9, C.mute, 2);
      else { const u = T(t, e + .3, e + 1.1); const ex = x + 4.6 * s, ey = y + 15 * s; thr(ex, ey, tx, ly - 20, io(u), 2); if (u >= 1) mark(tx, ly, 16, { r: 1, line: 0 }); else line(tx, ly - 9, tx, ly + 9, C.mute, 2); }
    });
  });
  alpha(T(t, k.e(1) - .3, k.e(1) + .4), () => { txt('a closing eye', xs[0], 668, { mono: 1, size: 15, col: C.mute, align: 'center' }); txt('a reading someone made', xs[1], 668, { mono: 1, size: 15, col: C.paper, align: 'center' }); });
};

/* 11 put that there */
SC.putthat = (k) => {
  const t = k.t, g = 612, s = 1.15, sy = stand(g, s);
  const WX = { PUT: 480, THAT: 640, THERE: 810 }, WY = 270;
  Object.entries(WX).forEach(([w, x]) => txt(w, x, WY, { mono: 1, size: 34, align: 'center', ls: 3 }));
  line(80, g, 1200, g, C.dim, 2);
  const spot = { X: 860, Y: 1060 };
  Object.entries(spot).forEach(([n, x]) => { line(x - 9, g + 12, x + 9, g + 24, C.mute, 1.6); line(x + 9, g + 12, x - 9, g + 24, C.mute, 1.6); });
  /* round 1 during sentence 2, round 2 during sentence 3 */
  const r1 = { that: k.w(2, 'stone'), there: k.w(2, 'ground'), go: k.w(2, 'instruction') }, r2a = k.a(3) + .2, r2 = { that: r2a + .9, there: r2a + 2.1, go: r2a + 3.2 };
  [r1.that, r1.there, r2.that, r2.there].forEach(a => k.ev(a));
  const stoneY = g - 20;
  const A = kf(t, [[r1.go + .1, [300, stoneY]], [r1.go + .5, [300, 470]], [r1.go + 1.7, [spot.X, 470]], [r1.go + 2.1, [spot.X, stoneY]]]);
  const Bp = kf(t, [[r2.go + .1, [430, stoneY]], [r2.go + .5, [430, 470]], [r2.go + 1.7, [spot.Y, 470]], [r2.go + 2.1, [spot.Y, stoneY]]]);
  const stone = ([x, y], n) => { poly([[x - 36, y + 18], [x - 30, y - 12], [x - 6, y - 22], [x + 26, y - 16], [x + 36, y + 6], [x + 28, y + 18]], C.paper, 2, true, '#2b2722'); txt(n, x, y + 6, { mono: 1, size: 12, col: C.mute, align: 'center' }); };
  stone(A, 'a'); stone(Bp, 'b');
  const bind = (wx, target, a0, a1) => { const u = T(t, a0, a0 + .7) * (1 - T(t, a1, a1 + .5)); if (u > 0) alpha(u, () => thr(wx, WY + 12, target[0], target[1] - 24, 1, 2.2)); };
  bind(WX.THAT, A, r1.that, r2a);
  bind(WX.THERE, t < r1.go + 2.1 ? [spot.X, g] : A, r1.there, r2a);
  bind(WX.THAT, Bp, r2.that, 1e9);
  bind(WX.THERE, t < r2.go + 2.1 ? [spot.Y, g] : Bp, r2.there, 1e9);
  const hy = 400;
  const tap = (x, a) => [[a - .5, [x, hy]], [a - .15, [x, sy - 6]], [a + .25, [x, hy]]];
  const keys = [[0, [640, 380]], ...tap(300, r1.that), ...tap(spot.X, r1.there), [r1.go, [300, hy]], [r1.go + .5, [300, 420]], [r1.go + 1.7, [spot.X, 420]], [r1.go + 2.2, [spot.X, hy]],
    ...tap(430, r2.that), ...tap(spot.Y, r2.there), [r2.go, [430, hy]], [r2.go + .5, [430, 420]], [r2.go + 1.7, [spot.Y, 420]], [r2.go + 2.2, [spot.Y, hy]], [r2.go + 3.2, [960, 360]]];
  const p = hang(t, keys, { s });
  const carrying = (t > r1.go && t < r1.go + 2.1) ? A : (t > r2.go && t < r2.go + 2.1) ? Bp : null;
  if (carrying) thr(p.x, p.y + 40, carrying[0], carrying[1] - 22, 1, 1.8);
  p.look = [0, 1]; p.lit = t > r2.go + 2.2 ? 6 : t > r1.go + 2.2 ? 3 : 0; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
  alpha(T(t, k.a(2), k.a(2) + .5), () => txt(t < r2a ? 'binding 1' : 'binding 2', 1200, 680, { mono: 1, size: 13, col: C.mute, align: 'right', ls: 1 }));
};

/* 12 the house that language built */
SC.built = (k) => {
  const t = k.t;
  const N = 24, LX = 80, LY0 = 232, LH = 18.4;
  txt('source (illustrative)', LX, 214, { mono: 1, size: 11, col: C.mute, ls: 1 });
  /* the bricks: four wall rows of four, then the roof */
  const bricks = []; const bw = 88, bh = 34, hx = 650, g = 640;
  for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) bricks.push([hx + c * (bw + 4) + (r % 2 ? bw / 2 : 0) - (r % 2 ? 22 : 0), g - (r + 1) * (bh + 3)]);
  [[4, 0], [3, 1], [1, 2]].forEach(([n, r]) => { for (let c = 0; c < n; c++) bricks.push([hx + (4 - n) * (bw + 4) / 2 + c * (bw + 4), g - (5 + r) * (bh + 3)]); });
  /* line 22's brick sits in the roof */
  const DOOR = 21;
  const b0 = k.a(1) - .2, b1 = k.a(2) - .3, bt = i => b0 + (i / N) * (b1 - b0);
  const slip0 = k.a(3) + .2, slip1 = slip0 + 1.6, tug = k.a(4) + .1;
  k.ev(b0); k.ev(tug);
  const perm = i => i < 13 ? i : 13 + ((i - 13) * 5 + 3) % 11;
  const wrong = perm(DOOR);
  for (let i = 0; i < N; i++) {
    const ly = LY0 + i * LH, on = t > bt(i);
    const hl = i === DOOR && t > k.a(2) - .1;
    if (hl) rect(LX - 6, ly - 13, 352, LH, '#2b2722');
    const s = `${String(i + 1).padStart(2, ' ')}  1 ${[4, 15, 1, 14][i % 4]} ${(i % 4) * 40 - 60} ${-24 * Math.floor(i / 4)} 0 ... 3001.dat`;
    txt(s, LX, ly, { mono: 1, size: 11.5, col: on ? C.paper : C.dim });
    if (on) {
      const sl = io(T(t, slip0 + (i % 7) * .08, slip1));
      const j = lerp(0, 1, sl), tgt = bricks[i], wt = bricks[perm(i)];
      const bx = lerp(tgt[0], wt[0], j) + bw / 2, by = lerp(tgt[1], wt[1], j) + bh / 2;
      const strong = i === DOOR && t > tug;
      alpha(strong ? 1 : .42, () => thr(LX + 352, ly - 4, bx, by, T(t, bt(i), bt(i) + .3), strong ? 2.6 : 1.1));
    }
  }
  bricks.forEach(([x, y], i) => {
    const u = T(t, bt(i) + .15, bt(i) + .45); if (u <= 0) return;
    const lit = i === wrong && t > tug + .3;
    alpha(u, () => rect(x, y - (1 - u) * 20, bw, bh, lit ? C.red : '#2b2722', C.paper, 1.6));
  });
  /* the five steps */
  const steps = ['parse', 'place', 'connect', 'assemble', 'repair'];
  steps.forEach((s, i) => { const at = k.w(1, s); const on = t > at - .1 && t < k.a(2); txt(s, 640 + i * 118, 214, { mono: 1, size: 14, col: on ? C.paper : C.mute, ls: 1 }); if (i < 4) txt('→', 640 + i * 118 + 92, 214, { mono: 1, size: 12, col: C.dim }); });
  alpha(T(t, k.a(2), k.a(2) + .5), () => tag('repository-reported', 440, LY0 + DOOR * LH + 1, { size: 11, col: C.gold }));
  const keys = [[0, [540, 200]]];
  for (let i = 0; i < N; i += 3) keys.push([bt(i), [540, LY0 + i * LH - 60]]);
  keys.push([b1 + .4, [560, 330]], [tug - .3, [560, LY0 + DOOR * LH - 80]], [tug + .4, [520, LY0 + DOOR * LH - 70]]);
  const p = hang(t, keys, { s: 1.0 });
  p.look = t > tug ? [1, -.4] : [1, .6]; p.lit = Math.floor(6 * T(t, b0, b1)); if (t > slip1 + .3) p.blink = blinkAt(t, slip1 + .5);
  if (t > tug && t < tug + .5) { p.rot = -10 * Math.sin(T(t, tug, tug + .5) * Math.PI); }
  bolas(p);
};

/* 13 the beautiful wrong answer */
SC.wrong = (k) => {
  const t = k.t, SY = 250, SW = 170, SH = 96, SX = [210, 420, 630, 840];
  const plain = (x, y, w, h, v = 0) => { rect(x, y, w, h, '#15130f', C.paper, 1.6); line(x + 8, y + h * .66, x + w - 8, y + h * .66, C.mute, 1.4); const fx = x + w * (.3 + .4 * v); circ(fx, y + h * .66 - 26, 5, C.paper); line(fx, y + h * .66 - 20, fx, y + h * .66 - 4, C.paper, 2); };
  const bright = (x, y, w, h, a = 1) => {
    X.save(); X.globalAlpha *= a;
    const gr = X.createRadialGradient(x + w * .5, y + h * .55, 4, x + w * .5, y + h * .55, w * .7); gr.addColorStop(0, '#f6dc9a'); gr.addColorStop(.45, C.gold); gr.addColorStop(1, '#7a3b1e');
    rect(x, y, w, h, gr, C.paper, 1.6);
    for (let i = 0; i < 12; i++) { const a2 = i / 12 * Math.PI * 2; line(x + w * .5, y + h * .55, x + w * .5 + Math.cos(a2) * w * .6, y + h * .55 + Math.sin(a2) * h * .6, 'rgba(255,245,220,.5)', 1.2); }
    circ(x + w * .5, y + h * .55, 14, '#fff6e0'); X.restore();
  };
  [0, 1, 3].forEach((i, j) => plain(SX[i], SY, SW, SH, j * .4));
  const pickB = k.a(2) + .3, pinA = k.w(2, 'relation') - .2, ev2 = k.a(3) + .2;
  k.ev(pickB); k.ev(pinA); k.ev(ev2);
  const B = kf(t, [[pickB, [720, 440]], [pickB + 1.2, [SX[2], SY]]]);
  const A = kf(t, [[pinA, [300, 440]], [pinA + 1.2, [300, 560]]]);
  if (t < pickB + 1.2) rect(SX[2], SY, SW, SH, null, C.mute, 1.4, [6, 6]);
  line(120, 548, 1160, 548, C.dim, 1.5);
  txt('kept', 120, 538, { mono: 1, size: 12, col: C.mute, ls: 1 });
  bright(A[0], A[1], SW, SH);
  plain(B[0], B[1], SW, SH, .2);
  if (t > pinA + 1.2) {
    thr(A[0] + SW / 2, 548, A[0] + SW / 2, A[1], 1, 2);
    const u = T(t, pinA + 1.2, pinA + 2);
    alpha(u, () => { rect(A[0] + SW + 24, A[1] + 6, 230, 84, null, C.paper, 1.4); txt('rejected', A[0] + SW + 38, A[1] + 30, { mono: 1, size: 12, col: C.red, ls: 1 }); bars(A[0] + SW + 38, A[1] + 50, [150], 6, 8, C.dim); bars(A[0] + SW + 38, A[1] + 68, [110, 50], 6, 8, C.dim); });
    alpha(u, () => line(A[0] + SW / 2, A[1], SX[2] + SW / 2, SY + SH, C.red, 1.4, [5, 6]));
  }
  if (t > ev2) mark(A[0] - 34, A[1] + SH / 2, 18, { r: T(t, ev2, ev2 + .5) > .9 ? 1 : 0, line: 0 });
  const keys = [[0, [640, 200]], [pickB - .4, [720 + SW / 2, 370]], [pickB + 1.2, [SX[2] + SW / 2, 180]], [pinA - .3, [300 + SW / 2, 370]], [pinA + 1.2, [300 + SW / 2, 470]], [pinA + 2.0, [520, 470]], [ev2, [560, 440]]];
  const p = hang(t, keys, { s: 1.05 });
  if (t > pickB - .4 && t < pickB + 1.2) thr(p.x, p.y + 40, B[0] + SW / 2, B[1], 1, 1.6);
  if (t > pinA - .3 && t < pinA + 1.2) thr(p.x, p.y + 40, A[0] + SW / 2, A[1], 1, 1.6);
  p.look = [0, 1]; p.lit = t > pickB ? 6 : 2; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 15 the blueberry */
SC.berry = (k) => {
  const t = k.t, g = 620, bxy = [430, 392];
  line(80, g, 1200, g, C.dim, 2);
  /* bush */
  poly([[380, g], [384, 520], [400, 450], [425, 400]], C.paper, 2.6); poly([[384, 520], [340, 470], [320, 430]], C.paper, 2.2); poly([[392, 480], [460, 455], [500, 440]], C.paper, 2.2);
  [[318, 425], [500, 438], [352, 470]].forEach(([x, y], i) => { X.save(); X.translate(x, y); X.rotate(i - .5); X.beginPath(); X.ellipse(0, 0, 16, 7, 0, 0, Math.PI * 2); X.strokeStyle = C.mute; X.lineWidth = 1.6; X.stroke(); X.restore(); });
  const run1 = k.a(1), eat1 = run1 + 1.4, rew = k.a(2) + .4, run2 = k.a(3), eat2 = run2 + 1.2;
  k.ev(rew); k.ev(eat2 + .4);
  const turnsOf = (t0, tEat) => t < t0 ? 0 : t < tEat ? 1 : 1 + Math.min(3, Math.floor((t - tEat) / 1.0) + 1);
  let turn, run = t < rew ? 1 : 2;
  if (run === 1) turn = turnsOf(run1, eat1); else turn = t < run2 ? 1 : turnsOf(run2, eat2);
  /* the berry */
  let berry = 1;
  if (run === 1) { if (t > eat1) berry = 0; if (t > eat1 + 2.0) berry = out(T(t, eat1 + 2.0, eat1 + 2.3)); }
  else { berry = t > eat2 ? 0 : 1; }
  if (berry > 0) circ(bxy[0], bxy[1], 14 * berry, C.berry, '#22283f', 1.4);
  if (run === 2 && t > eat2) { line(bxy[0] - 3, bxy[1] - 14, bxy[0] + 2, bxy[1] - 4, C.paper, 2); circ(bxy[0] + 2, bxy[1] - 3, 2.5, C.mute); }
  /* the bird */
  const bird = (t0) => {
    const p = kf(t, [[t0 - 1.2, [1320, 230]], [t0, [bxy[0] + 34, bxy[1] - 14]], [t0 + .5, [bxy[0] + 34, bxy[1] - 14]], [t0 + 1.8, [-80, 200]]]);
    if (t < t0 - 1.2 || t > t0 + 1.8) return null;
    const flap = Math.sin(t * 22) * 10, dir = t < t0 + .3 ? -1 : -1;
    X.save(); X.translate(p[0], p[1]);
    X.beginPath(); X.ellipse(0, 0, 18, 10, 0, 0, Math.PI * 2); X.fillStyle = C.paper; X.fill();
    circ(dir * 16, -6, 7, C.paper); poly([[dir * 22, -6], [dir * 30, -3], [dir * 22, -1]], C.gold, 1.6, true, C.gold); circ(dir * 18, -8, 1.4, C.ink);
    poly([[-4, -2], [6, -16 - flap], [12, -2]], C.paper, 2.2);
    X.restore(); return p;
  };
  bird(eat1); const bp = bird(eat2);
  /* the seed and what grows */
  if (run === 2 && t > eat2 + .8) {
    const sx = 760, fall = T(t, eat2 + .8, eat2 + 1.4);
    if (fall < 1) circ(sx, lerp(260, g - 4, fall * fall), 3.5, C.berry);
    const gr = Math.min(3, turn - 1) / 3 * T(t, eat2 + 1.4, eat2 + 1.8);
    if (fall >= 1) { line(sx, g, sx, g - 90 * gr, C.paper, 2.4); if (gr > .3) { X.save(); X.translate(sx - 12 * gr, g - 50 * gr); X.rotate(-.5); X.beginPath(); X.ellipse(0, 0, 14 * gr, 6 * gr, 0, 0, Math.PI * 2); X.strokeStyle = C.paper; X.lineWidth = 1.8; X.stroke(); X.restore(); } if (gr > .7) circ(sx, g - 90 * gr, 6, null, C.paper, 1.8); }
  }
  /* the turn counter */
  txt('turn', 1000, 234, { mono: 1, size: 13, col: C.mute, ls: 1 });
  for (let i = 0; i < 4; i++) circ(1060 + i * 30, 230, 7, i < turn ? C.paper : null, C.mute, 1.5);
  txt(run === 1 ? 'run 1' : 'run 2 · state kept', 80, 680, { mono: 1, size: 13, col: run === 1 ? C.mute : C.paper, ls: 1 });
  /* the event knot: what remains */
  if (run === 2 && t > eat2 + .4) { const u = T(t, eat2 + .4, eat2 + 1.2); thr(bxy[0] + 14, bxy[1], 560, 560, io(u), 1.8); knot(560, 560, T(t, eat2 + 1.1, eat2 + 1.4)); alpha(T(t, eat2 + 1.2, eat2 + 1.6), () => txt('turn 1 · eaten', 576, 565, { mono: 1, size: 13, col: C.paper })); }
  /* Bolas watches, then winds the counter back */
  const keys = [[0, [640, 260]], [rew - .6, [700, 260]], [rew, [1080, 180]], [rew + 1.0, [1080, 180]], [rew + 1.6, [620, 300]]];
  const p = hang(t, keys, { s: 1.1 });
  if (t > rew && t < rew + 1.0) { thr(p.x, p.y + 40, 1105, 222, 1, 1.6); p.legPhase = t * 22; }
  p.look = run === 1 ? (t > eat1 + 2.0 ? [-1, 1] : [-.6, .6]) : [-.3, .8]; p.lit = run === 2 ? 6 : 2; p.blink = blinkAt(t, eat1 + 2.5) || blinkAt(t, k.D - 1);
  bolas(p);
};

/* 16 a poem becomes a place */
SC.place = (k) => {
  const t = k.t, CX = [175, 410, 645, 880, 1115], cy = 400, names = ['House of Dust', 'Shield Grid', 'TEXT-URE', 'Association Field', 'WYGWYL Atlas'];
  const kw = ['dwelling', 'addresses', 'texture', 'sequence', 'city'];
  const at = kw.map(w => k.w(1, w) - .7);
  at.forEach(a => k.ev(a));
  const pr = i => T(t, at[i], at[i] + 1.3);
  const ends = [];
  CX.forEach((cx, i) => {
    const u = pr(i), dimA = .35 + .65 * T(t, at[i] - .2, at[i] + .2);
    alpha(dimA, () => txt(names[i], cx, 580, { mono: 1, size: 13, col: C.paper, align: 'center' }));
    alpha(dimA, () => {
      if (i === 0) { [150, 120, 160, 130].forEach((w, j) => rect(cx - w / 2, 320 + j * 28, w, 7, C.dim)); poly([[cx - 40, 500], [cx - 40, 462], [cx, 436], [cx + 40, 462], [cx + 40, 500]], C.paper, 1.8, true); }
      if (i === 1) for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) { rect(cx - 80 + c * 32, 320 + r * 32, 30, 30, null, C.dim, 1.2); if (rnd(r * 5 + c) > .6) circ(cx - 65 + c * 32, 335 + r * 32, 3, C.mute); }
      if (i === 2) for (let r = 0; r < 14; r++) for (let c = 0; c < 9; c++) line(cx - 85 + c * 20 + (r % 2) * 8, 316 + r * 13, cx - 77 + c * 20 + (r % 2) * 8, 316 + r * 13 + (rnd(r * 9 + c) - .5) * 6, C.dim, 1.6);
      if (i === 3) { for (let j = 0; j < 14; j++) rect(cx - 90 + rnd(j * 2.3) * 160, 312 + rnd(j * 4.1) * 120, 20, 13, null, C.mute, 1.2); for (let j = 0; j < 4; j++) rect(cx - 86 + j * 44, 470, 40, 26, null, C.dim, 1.2); }
      if (i === 4) { for (let j = 0; j < 4; j++) { line(cx - 90, 330 + j * 45, cx + 90, 330 + j * 45, C.dim, 1.2); line(cx - 90 + j * 60, 320, cx - 90 + j * 60, 500, C.dim, 1.2); } [[-70, 380, 30, 30], [-10, 340, 26, 36], [40, 400, 34, 48], [-60, 440, 24, 26], [20, 452, 30, 34]].forEach(([dx, y, w, h]) => rect(cx + dx, y - h + 20, w, h, '#2b2722', C.paper, 1.4)); }
    });
    /* the red line's form in each */
    let pts = [];
    if (i === 0) pts = [[cx - 60, 362], [cx + 60, 362]];
    if (i === 1) pts = [[cx - 65, 335], [cx - 33, 335], [cx - 33, 399], [cx + 31, 399], [cx + 31, 431], [cx + 63, 431], [cx + 63, 463]];
    if (i === 2) pts = [...Array(9)].map((_, j) => [cx - 80 + j * 20, 330 + Math.sin(j * 1.1) * 40 + j * 12]);
    if (i === 3) { const pick = [1, 5, 9, 12]; pts = pick.map(j => [cx - 80 + rnd(j * 2.3) * 160, 318 + rnd(j * 4.1) * 120]); }
    if (i === 4) pts = [[cx - 90, 330], [cx - 30, 330], [cx - 30, 420], [cx + 30, 420], [cx + 30, 465], [cx + 90, 465]];
    if (u > 0) { const n = Math.max(2, Math.ceil(pts.length * u)); const sub = pts.slice(0, n); const last = sub[sub.length - 1], prev = sub[sub.length - 2], f = pts.length * u - (n - 1); if (u < 1 && prev) sub[sub.length - 1] = [lerp(prev[0], last[0], cl(f + 1)), lerp(prev[1], last[1], cl(f + 1))]; poly(sub, C.red, 2.6); }
    if (i === 2 && u > .2) pts.forEach(([x, y], j) => { if (j / pts.length < u) circ(x, y, 3.5, C.red); });
    if (i === 3) for (let j = 0; j < 4; j++) if (u > (j + 1) / 4.2) rect(cx - 86 + j * 44, 470, 40, 26, '#5a2a24', C.red, 1.6);
    if (i === 0 && u > .5) alpha(T(u, .5, 1), () => line(cx - 60, 362 - 6, cx + 60, 362 - 6, C.paper, 1));
    ends.push([pts[0], pts[pts.length - 1]]);
  });
  /* one line throughout: the arcs between forms */
  for (let i = 0; i < 4; i++) { const u = T(t, at[i] + 1.3, at[i + 1]); if (u <= 0) continue; const a = ends[i][1], b = ends[i + 1][0], mx = (a[0] + b[0]) / 2; const n = 20, pts = []; for (let j = 0; j <= n * u; j++) { const s = j / n; pts.push([lerp(a[0], b[0], s), lerp(a[1], b[1], s) - Math.sin(s * Math.PI) * 90]); } poly(pts, C.red, 1.8); void mx; }
  const keys = [[0, [175, 220]]]; at.forEach((a, i) => keys.push([a, [CX[i], 236]], [a + 1.3, [CX[i] + 40, 236]]));
  const p = hang(t, keys, { s: 1.0 });
  p.look = [0, 1]; p.lit = Math.min(6, at.filter(a => t > a).length + 1); p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 17 the histories a world keeps */
SC.branches = (k) => {
  const t = k.t, Y = 440, FX = 470;
  const fk = k.a(3), up = [1180, 320], dn = [1180, 560];
  line(100, Y, FX, Y, C.paper, 2.2);
  const fu = T(t, fk, fk + .8);
  if (fu > 0) { line(FX, Y, lerp(FX, up[0], fu), lerp(Y, up[1], fu), C.paper, 2.2); line(FX, Y, lerp(FX, dn[0], fu), lerp(Y, dn[1], fu), C.paper, 2.2); }
  const roles = [['refuge', k.w(1, 'refuge')], ['obstacle', k.w(1, 'obstacle')], ['object of return', k.w(1, 'object')]];
  const ex = kf(t, [[k.a(1) - .3, 160], [k.w(1, 'object') + .4, 400]]);
  circ(ex, Y, 15, C.paper); txt('the city', ex, Y + 44, { mono: 1, size: 13, col: C.mute, align: 'center' });
  let role = null; roles.forEach(([r, a]) => { if (t > a - .1) role = r; });
  if (role) txt(role, ex, Y - 32, { mono: 1, size: 15, col: C.paper, align: 'center' });
  const chg = k.w(3, 'change') - .1, cont = k.w(3, 'continue'), chk = k.w(3, 'check');
  k.ev(chg); k.ev(cont);
  const on = (a, b, u) => [lerp(FX, a, u), lerp(Y, b, u)];
  const NU = [.3, .5, .7, .9];
  NU.forEach((u, j) => {
    const a = j === 0 ? fk + .5 : cont + (j - 1) * .45;
    const pu = on(...up, u), pd = on(...dn, u);
    const vis = T(t, a, a + .3);
    knot(pu[0], pu[1], vis, C.paper); knot(pd[0], pd[1], vis, j === 0 && t > chg ? C.red : C.paper);
    if (j > 0) { const ca = chk + .5 + (j) * .7; if (t > ca) circ(pu[0], pu[1], 14, null, C.mute, 1.5); }
    if (j === 0) { const ca = chk + .5; if (t > ca) circ(pu[0], pu[1], 14, null, C.mute, 1.5); }
  });
  if (t > chg) alpha(T(t, chg, chg + .4), () => txt('one fact changed', on(...dn, .3)[0], on(...dn, .3)[1] + 36, { mono: 1, size: 13, col: C.red, align: 'center' }));
  const keys = [[0, [640, 230]], [chg - .7, [on(...dn, .3)[0], 400]], [chg, [on(...dn, .3)[0], 460]], [chg + .6, [on(...dn, .3)[0], 400]], [chk, [on(...up, .3)[0] - 20, 220]]];
  NU.forEach((u, j) => keys.push([chk + .5 + j * .7, [on(...up, u)[0], on(...up, u)[1] - 80]]));
  keys.push([chk + .5 + 3 * .7 + .8, [on(...up, .9)[0] - 30, 200]]);
  const p = hang(t, keys, { s: 1.0 });
  if (t > chg - .1 && t < chg + .5) thr(p.x, p.y + 40, on(...dn, .3)[0], on(...dn, .3)[1] - 8, 1, 1.6);
  p.look = t > chk ? [0, 1] : [0, .8]; p.lit = t > chk ? Math.min(6, 2 + Math.floor((t - chk) / .7)) : 1; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 19 the model changes what it can see */
SC.ontology = (k) => {
  const t = k.t;
  const P = [[100, 262, 480, 330], [700, 262, 480, 330]];
  txt('parameter change', 100, 248, { mono: 1, size: 13, col: C.mute, ls: 1 }); txt('ontology change', 700, 248, { mono: 1, size: 13, col: C.mute, ls: 1 });
  P.forEach(([x, y, w, h]) => rect(x, y, w, h, null, C.dim, 1.5));
  const s1 = k.a(1) + .3, s2 = k.a(2) + .3;
  k.ev(s1); k.ev(s2);
  const v = kf(t, [[s1, .3], [s1 + 1.2, .85]]);
  /* integrate speed so the dots do not jump when the dial turns */
  const phase = (tt) => { const a = Math.min(tt, s1), b = cl((tt - s1) / 1.2) * 1.2, c = Math.max(0, tt - s1 - 1.2); return .3 * a + (b > 0 ? (.3 * b + .55 * b * b / 2.4) : 0) + .85 * c; };
  const ph = phase(t);
  const dot = (i, px, py, pw, ph2, s, kind) => {
    const x = px + 30 + (pw - 60) * (.5 + .45 * Math.sin(s * (1 + rnd(i) * .6) + i * 2.1)), y = py + 30 + (ph2 - 60) * (.5 + .45 * Math.sin(s * (.8 + rnd(i + 9) * .7) + i * 1.3));
    return [x, y, kind];
  };
  const N = 14;
  /* left: same kinds, faster */
  for (let i = 0; i < N; i++) { const [x, y] = dot(i, ...P[0], ph * 2.2, 0); i % 2 ? circ(x, y, 8, C.paper) : circ(x, y, 7, null, C.paper, 2); }
  /* right: the same, until the account is redrawn */
  const r = io(T(t, s2, s2 + 1.6));
  const groups = [[860, 350], [1060, 350], [960, 510]];
  const pts = [];
  for (let i = 0; i < N; i++) {
    const [x0, y0] = dot(i, ...P[1], t * .3 * 2.2, 0); const gi = i % 3, gc = groups[gi], a = i / N * Math.PI * 6;
    const x = lerp(x0, gc[0] + Math.cos(a) * 46, r), y = lerp(y0, gc[1] + Math.sin(a) * 36, r); pts.push([x, y, gi]);
  }
  if (r > .3) alpha(T(r, .3, 1), () => { pts.forEach(([x, y, g], i) => pts.forEach(([x2, y2, g2], j) => { if (j > i && (g === g2 ? rnd(i * 13 + j) > .5 : rnd(i * 7 + j) > .93)) line(x, y, x2, y2, C.mute, 1); })); });
  pts.forEach(([x, y, g], i) => {
    const kind = r < .5 ? (i % 2) : g;
    if (kind === 1) circ(x, y, 8, C.paper); else if (kind === 0) circ(x, y, 7, null, C.paper, 2); else { rect(x - 7, y - 7, 14, 14, null, C.paper, 2); }
  });
  /* the dials */
  [[140, 655, v, 'a · speed'], [740, 655, .3, r < .5 ? 'a · speed' : 'a · redefined']].forEach(([x, y, val, lab]) => { line(x, y, x + 400, y, C.dim, 3); circ(x + 400 * val, y, 11, C.paper); txt(lab, x, y - 22, { mono: 1, size: 13, col: C.paper }); });
  const keys = [[0, [640, 214]], [s1 - .5, [140 + 400 * .3, 585]], [s1 + 1.2, [140 + 400 * .85, 585]], [s2 - .6, [640, 214]], [s2 + 1.6, [640, 214]], [s2 + 2.4, [640, 214]]];
  const p = hang(t, keys, { s: 1.0 });
  if (t > s1 - .2 && t < s1 + 1.3) thr(p.x, p.y + 40, p.x, 644, 1, 1.6);
  if (t > s2 && t < s2 + 1.6) { groups.forEach(([gx, gy], j) => alpha(T(t, s2 + j * .3, s2 + j * .3 + .3), () => thr(p.x, p.y + 40, gx, gy - 50, 1, 1.4))); p.legPhase = t * 18; }
  p.look = [0, 1]; p.lit = t > s2 ? 6 : 3; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 20 the archive cannot be read all at once */
function sprite(i, x, y, w, h) {
  const im = IMG.wg050;
  if (im && im.complete && im.naturalWidth) { const c = i % 8, r = Math.floor(i / 8); X.drawImage(im, c * 256, r * 144, 256, 144, x, y, w, h); }
  else { rect(x, y, w, h, '#2b2722'); }
}
SC.archive = (k) => {
  const t = k.t, COLS = 26, ROWS = 20, fx = 64, fy = 222, cw = 20, ch = 12, gx = 4, gy = 4;
  const sight = kf(t, [[0, [150, 300]], [k.a(1), [420, 420]], [k.a(1) + 1.6, [520, 330]], [k.a(2), [300, 520]], [k.D, [560, 470]]]);
  const R = 72;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const x = fx + c * (cw + gx), y = fy + r * (ch + gy), d = Math.hypot(x + cw / 2 - sight[0], y + ch / 2 - sight[1]);
    const v = .14 + rnd(r * 31 + c) * .16;
    rect(x, y, cw, ch, d < R ? `rgba(236,230,218,${.35 + .3 * rnd(r + c * 7)})` : `rgba(236,230,218,${v})`);
  }
  circ(sight[0], sight[1], R, null, 'rgba(232,192,112,.5)', 1.2);
  const picks = [[k.a(1) + .1, [7, 8]], [k.a(1) + .8, [17, 6]], [k.a(1) + 1.5, [12, 12]]];
  picks.forEach(p => k.ev(p[0]));
  const CH = [800, 228, 256, 144];
  const EX = [[790, 560, 128, 72], [960, 560, 128, 72]];
  const dest = [CH, EX[0], EX[1]];
  const excl = k.w(3, 'exclusions') - .4;
  picks.forEach(([a, [c, r]], i) => {
    if (t < a) return;
    const sx = fx + c * (cw + gx), sy = fy + r * (ch + gy);
    const u = io(T(t, a, a + .9));
    const d = i === 0 ? dest[0] : (t < excl ? [1076, 228 + (i - 1) * 84, 128, 72] : dest[i]);
    const prev = i === 0 ? [sx, sy, cw, ch] : [1076, 228 + (i - 1) * 84, 128, 72];
    const box = u < 1 ? [lerp(sx, d[0], u), lerp(sy, d[1], u), lerp(cw, d[2], u), lerp(ch, d[3], u)] : (i > 0 && t > excl ? [lerp(prev[0], d[0], io(T(t, excl, excl + .8))), lerp(prev[1], d[1], io(T(t, excl, excl + .8))), 128, 72] : d);
    if (i === 0) { const fi = Math.floor(((Math.max(0, t - a - .9)) % 6.5) / .1); sprite(Math.min(64, fi), ...box); rect(...box, null, C.paper, 1.4); }
    else { rect(...box, '#24211d', C.mute, 1.4); line(box[0] + 8, box[1] + box[3] * .66, box[0] + box[2] - 8, box[1] + box[3] * .66, C.dim, 1.2); }
    if (u < 1) thr(sx + cw / 2, sy + ch / 2, box[0] + box[2] / 2, box[1], 1, 1.4);
  });
  if (t > picks[0][0] + .9) txt('wg_050 · WarGames, 1983', 800, 392, { mono: 1, size: 12, col: C.mute });
  /* three claims, kept apart */
  const claims = [['present', 'a hand on a door', k.w(2, 'visibly')], ['research', 'a principal sees David out', k.w(2, 'research')], ['might do', 'a courtesy, or a control', k.w(2, 'new composition')]];
  claims.forEach(([a, b, at], i) => { k.ev(at); const u = T(t, at, at + .5); if (u <= 0) return; const y = 420 + i * 36; thr(800 - 14, 300, 800 - 14, y - 4, 1, 1.2); knot(786, y - 4, u); alpha(u, () => { txt(a, 800, y, { mono: 1, size: 12, col: C.red, ls: 1 }); txt(b, 890, y, { mono: 1, size: 13, col: C.paper }); }); });
  k.ev(excl);
  if (t > excl) { const u = T(t, excl, excl + .8); line(770, 548, lerp(770, 1180, u), 548, C.red, 1.6); alpha(T(t, excl + .6, excl + 1.2), () => { txt('excluded · reasons kept', 790, 660, { mono: 1, size: 12, col: C.mute, ls: 1 }); [0, 1].forEach(j => thr(EX[j][0] + 64, 548, EX[j][0] + 64, 560, 1, 1.4)); }); }
  const keys = [[0, [150, 196]], [k.a(1), [420, 196]], [k.a(1) + 1.6, [520, 196]], [k.a(2), [300, 196]], [k.D, [560, 196]]];
  const p = hang(t, keys, { s: .95 });
  const eye = [p.x, p.y + 15 * .95];
  line(eye[0], eye[1], sight[0] - R * .7, sight[1] - R * .7, 'rgba(232,192,112,.35)', 1); line(eye[0], eye[1], sight[0] + R * .7, sight[1] - R * .7, 'rgba(232,192,112,.35)', 1);
  p.look = [(sight[0] - p.x) / 300, 1]; p.lit = 6; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 21 found odyssey: the match and the question */
SC.odyssey = (k) => {
  const t = k.t;
  txt('new narrative', 150, 262, { mono: 1, size: 12, col: C.mute, ls: 1 });
  const ws = [70, 44, 96, 58, 80, 0, 52, 74, 60, 90]; let x = 150; let wx = 0;
  ws.forEach(w => { if (w === 0) { wx = x; rect(x, 284, 80, 14, C.paper); x += 92; } else { rect(x, 287, w, 8, C.dim); x += w + 12; } });
  /* the archival clip */
  rect(420, 400, 440, 230, '#15130f', C.mute, 1.5); txt('archival utterance', 420, 390, { mono: 1, size: 12, col: C.mute, ls: 1 });
  circ(560, 490, 30, C.paper); poly([[505, 600], [520, 535], [600, 535], [615, 600]], null, 0, true, C.paper);
  for (let i = 0; i < 24; i++) { const h = 6 + 18 * Math.abs(Math.sin(i * .9 + t * 6)) * (Math.sin(t * 1.3 + i) > -.2 ? 1 : .2); line(660 + i * 7, 500 - h / 2, 660 + i * 7, 500 + h / 2, C.mute, 2); }
  bars(470, 612, [50, 40], 6, 10, C.dim); rect(580, 605, 80, 12, C.paper); bars(672, 612, [60, 44], 6, 10, C.dim);
  const tie = k.w(0, 'word') - .2, q = k.w(1, 'appropriateness') - .2, rl = k.a(2) + .3;
  k.ev(tie); k.ev(q); k.ev(rl);
  const u = io(T(t, tie, tie + 1.0));
  thr(wx + 40, 298, 620, 605, u, 2.4);
  if (t > q) { const mx = lerp(wx + 40, 620, .45), my = lerp(298, 605, .45); alpha(T(t, q, q + .4), () => { mark(mx + 70, my + 10, 24, { line: 0 }); line(mx, my, mx + 46, my + 10, C.red, 1.4); txt('open', mx + 104, my + 16, { mono: 1, size: 12, col: C.mute }); }); }
  /* the new role: not established */
  rect(960, 440, 210, 70, null, C.paper, 1.4); txt('new role', 976, 470, { mono: 1, size: 13, col: C.paper }); bars(976, 492, [120], 6, 8, C.dim);
  if (t > rl) { const v = T(t, rl, rl + 1.2); line(592, 480, lerp(592, 958, v), lerp(480, 475, v), C.red, 1.6, [7, 8]); }
  const keys = [[0, [900, 220]], [tie - .3, [wx + 40, 220]], [tie + 1.0, [700, 480]], [q, [720, 380]], [rl + 1.4, [880, 360]]];
  const p = hang(t, keys, { s: 1.0 });
  if (t > tie - .3 && t < tie + 1.0) thr(p.x, p.y + 40, lerp(wx + 40, 620, u), lerp(298, 605, u), 1, 1.4);
  p.look = [-.3, 1]; p.lit = 4; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 22 who can change what happens next */
SC.who = (k) => {
  const t = k.t, Y = 470, KX = [140, 340, 540, 740, 940, 1140], LB = ['proposal', 'alternatives', 'selection', 'authorized', 'consequence', 'revision'], fixed = [2, 3];
  rect(452, 380, 376, 170, null, C.mute, 1.4, [6, 6]);
  for (let i = 0; i < 10; i++) line(452 + i * 37.6, 550, 452 + i * 37.6 + 20, 560, C.dim, 1);
  const at = LB.map(w => k.w(1, w) - .1);
  at.forEach((a, i) => k.ev(a));
  const pull = KX.map((_, i) => fixed.includes(i) ? 0 : (T(t, at[i] + .1, at[i] + .4) - .6 * T(t, at[i] + .6, at[i] + 1.2)));
  const KY = KX.map((_, i) => Y + 26 * pull[i]);
  poly(KX.map((x, i) => [x, KY[i]]), C.red, 2.4);
  line(60, Y, KX[0], KY[0], C.red, 2.4); line(KX[5], KY[5], 1220, Y, C.red, 2.4);
  KX.forEach((x, i) => { knot(x, KY[i], 1); txt(LB[i], x, Y + 56, { mono: 1, size: 14, col: C.paper, align: 'center' }); if (i === 3) txt('action', x, Y + 76, { mono: 1, size: 14, col: C.paper, align: 'center' }); });
  const keys = [[0, [70, 300]], [k.a(1) - .2, [90, 300]]];
  at.forEach((a, i) => { const x = fixed.includes(i) ? (i === 2 ? 452 - 20 : 828 + 20) : KX[i]; keys.push([a - .1, [x, 300]], [a + .9, [x, 300]]); });
  keys.push([k.D - .5, [1180, 260]]);
  const p = hang(t, keys, { s: 1.0 });
  at.forEach((a, i) => {
    if (t > a && t < a + .9) {
      if (fixed.includes(i)) { const ex = KX[i]; line(p.x, p.y + 40, ex, 378, C.red, 1.6); p.x += Math.sin(t * 60) * 1.4; p.rot = (i === 2 ? 1 : -1) * 10; }
      else thr(p.x, p.y + 40, KX[i], KY[i] - 8, 1, 1.6);
    }
  });
  p.look = [0, 1]; p.lit = 4; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 23 the argument table */
SC.table = (k, sc) => {
  const t = k.t, CX = [80, 380, 820], ROW = [300, 425, 550];
  txt('EXPERIMENT', CX[0], 236, { mono: 1, size: 12, col: C.mute, ls: 2 }); txt('WHAT MUST BE ESTABLISHED', CX[1], 236, { mono: 1, size: 12, col: C.mute, ls: 2 }); txt('CHARACTERISTIC FAILURE', CX[2], 236, { mono: 1, size: 12, col: C.mute, ls: 2 });
  line(80, 252, 1200, 252, C.dim, 1.5);
  alpha(T(t, 0, .6), () => txt('The argument connecting them', 80, 150, { size: 46 }));
  sc.rows.forEach((r, i) => {
    const a = k.a(1 + i) - .2, u = T(t, a, a + .6), y = ROW[i];
    alpha(u, () => {
      wrap(r[0], 270, { size: 27, italic: 1 }).forEach((l, j) => txt(l, CX[0], y + 8 + j * 30, { size: 27, italic: 1 }));
      wrap(r[1], 360, { size: 25 }).forEach((l, j) => txt(l, CX[1], y + 8 + j * 28, { size: 25 }));
    });
    const f = k.w(1 + i, 'the failure') - .2; k.ev(f);
    const fu = T(t, f, f + .6);
    alpha(fu, () => wrap(r[2], 380, { size: 25 }).forEach((l, j) => txt(l, CX[2], y + 8 + j * 28, { size: 25, col: C.paper })));
    if (fu > 0) thr(760, y, 808, y, io(fu), 2.4);
    if (u > 0) alpha(u, () => line(80, y + 74, 1200, y + 74, C.faint, 1.5));
  });
  const ys = ROW.map((y, i) => [k.w(1 + i, 'the failure') - .7, [784, y - 66]]);
  const keys = [[0, [784, 190]], ...ys.flatMap(([a, p]) => [[a, p], [a + 1.2, p]]), [k.D - .5, [784, 196]]];
  const p = hang(t, keys, { s: .8, ay: 160 });
  p.ax = p.x; p.look = [1, .7]; p.lit = 6; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 24 three kinds of agreement */
SC.agree = (k) => {
  const t = k.t, g = 560;
  const XS = [...Array(13)].map((_, i) => 100 + i * 90), meas = XS.map((x, i) => g + (rnd(i * 4.7) - .5) * 44);
  const s1 = k.a(1) + .5, s2 = k.a(2) + .3, s3 = k.a(3) + .3;
  k.ev(s1); k.ev(s2); k.ev(s3);
  const fit = io(T(t, s1, s1 + 1.8));
  const drawn = XS.map((x, i) => [x, lerp(g - 70 + Math.sin(i * .7) * 18, meas[i], fit)]);
  poly(drawn, C.paper, 2.4);
  XS.forEach((x, i) => { line(x - 6, meas[i], x + 6, meas[i], C.gold, 2); line(x, meas[i] - 6, x, meas[i] + 6, C.gold, 2); });
  txt('measured', 100, 640, { mono: 1, size: 12, col: C.gold, ls: 1 }); txt('drawn', 200, 640, { mono: 1, size: 12, col: C.paper, ls: 1 });
  [['operational', 100, k.a(1)], ['interpretive', 480, k.a(2)], ['normative', 880, k.a(3)]].forEach(([s, x, a]) => alpha(T(t, a - .2, a + .3), () => txt(s, x, 230, { mono: 1, size: 14, col: C.paper, ls: 2 })));
  /* the event and its two readings */
  const ei = 6, ev = [XS[ei], lerp(drawn[ei][1], meas[ei], 1)];
  if (t > s2) {
    knot(ev[0], ev[1], T(t, s2, s2 + .3));
    [[-90, 0], [90, 1]].forEach(([dx, j]) => { const a = s2 + .5 + j * .7; const u = T(t, a, a + .6); if (u <= 0) return; thr(ev[0], ev[1] - 8, ev[0] + dx, 360, io(u), 1.8); if (u >= 1) { mark(ev[0] + dx, 336, 24, { r: j ? 1 : 0, l: j ? 0 : 1, line: 0 }); txt('reading ' + (j + 1), ev[0] + dx, 296, { mono: 1, size: 12, col: C.mute, align: 'center' }); } });
  }
  /* the gate */
  const gx = 1030, gy = meas[10];
  if (t > s3 - .3) alpha(T(t, s3 - .3, s3 + .3), () => {
    line(gx - 40, gy - 110, gx - 40, gy, C.paper, 3); line(gx + 40, gy - 110, gx + 40, gy, C.paper, 3);
    line(gx - 40, gy - 70, gx + 40, gy - 70, C.paper, 3);
    poly([[gx - 130, gy - 30], [gx - 74, gy - 30], [gx - 74, gy - 42], [gx - 52, gy - 22], [gx - 74, gy - 2], [gx - 74, gy - 14], [gx - 130, gy - 14]], C.paper, 1.6, true);
    txt('proposed', gx - 130, gy + 30, { mono: 1, size: 12, col: C.mute });
  });
  const keys = [[0, [400, 300]], [s1 - .3, [400, 380]], [s1 + 1.8, [400, 420]], [s2, [600, 220]], [s2 + 1.6, [600, 220]], [s3, [gx, 300]], [k.D, [gx, 300]]];
  const p = hang(t, keys, { s: 1.0 });
  if (t > s1 - .3 && t < s1 + 1.8) thr(p.x, p.y + 40, 400, drawn[3][1], 1, 1.6);
  if (t > s3 + .2) thr(p.x, p.y + 40, gx, gy - 72, 1, 1.6);
  p.look = [0, 1]; p.lit = t > s3 ? 6 : 3; p.blink = blinkAt(t, k.D - 1);
  bolas(p);
};

/* 25 the episode record */
SC.record = (k) => {
  const t = k.t, Y = 420, KX = [...Array(8)].map((_, i) => 110 + i * 150), LB = ['source', 'situation', 'description', 'realization', 'judgment', 'revision', 'consequence', 'limits'];
  const at = LB.map(w => k.w(1, w) - .12);
  at.forEach(a => k.ev(a));
  const keys = [[0, 70], [k.a(1) - .2, 90]]; at.forEach((a, i) => keys.push([a, KX[i]])); keys.push([at[7] + 1, 1222]);
  const x = kf(t, keys, u => u);
  line(70, Y, x, Y, C.red, 2.4);
  KX.forEach((kx, i) => { knot(kx, Y, T(t, at[i], at[i] + .3)); alpha(T(t, at[i], at[i] + .4), () => txt(LB[i], kx, Y + (i % 2 ? 76 : 52), { mono: 1, size: 15, col: C.paper, align: 'center' })); });
  const st = ['observed', 'repository-reported', 'reconstructed', 'proposed'];
  st.forEach((s, i) => { const a = k.w(2, s) - .1; k.ev(a); const u = T(t, a, a + .5); if (u <= 0) return; const ty = 520 + i * 42; thr(1160, Y + 6, 1160, ty - 14, i === 0 ? u : 1, 1.4); alpha(u, () => tag(s, 1172, ty, { size: 12, col: C.paper, align: 'right' })); });
  bolas({ x, y: Y + 48 + Math.sin(t * 2) * 1.2, ax: x, ay: Y, s: 1.05, legPhase: moving(t, keys) ? t * 15 : 0, look: [1, .3], lit: Math.floor(6 * T(t, at[0], at[7])), blink: blinkAt(t, k.D - .8) });
};

/* 26 the story for anyone */
SC.story = (k) => {
  const t = k.t, g = 620, s = 1.05, sy = stand(g, s), XS = [300, 480, 660];
  line(60, g, 1220, g, C.dim, 2);
  XS.forEach((x, i) => { line(x, 380, x, g, C.mute, 1.6); txt(['I', 'II', 'III'][i], x, 366, { mono: 1, size: 13, col: C.mute, align: 'center', ls: 2 }); });
  const d = house(1010, g, .62, 0);
  const t0 = k.a(0) + .5, t1 = k.a(3) + 1.2;
  const doorX = d.dx + d.dw / 2;
  const keys = [[0, [110, sy]], [t0, [110, sy]], [t1, [doorX - 52, sy]]];
  const p = hang(t, keys, { s });
  const ty = g - 22;
  if (t > t0) line(110, ty, p.x - 12, ty, C.red, 2.2);
  const KN = [...Array(8)].map((_, i) => 160 + i * 82);
  KN.forEach((x, i) => { const at = lerp(t0, t1, (x - 110) / (doorX - 52 - 110)); if (i === 0) k.ev(at); knot(x, ty, T(t, at, at + .3)); });
  const tie = t1 + .4; k.ev(tie);
  const u = T(t, tie, tie + .8);
  if (u > 0) { thr(p.x + 10, ty, d.dx + d.dw / 2, d.dy + d.dh / 2, io(u), 2.2); knot(d.dx + d.dw / 2, d.dy + d.dh / 2, T(t, tie + .7, tie + 1)); }
  p.look = t > tie ? [0, 1] : [1, .4]; p.lit = Math.floor(6 * T(t, t0, t1)); p.blink = blinkAt(t, k.D - 1.2);
  bolas(p);
  alpha(T(t, k.a(2) - .5, k.a(2) + .5), () => txt('worldtext', 820, 300, { size: 34, italic: 1, col: C.paper, a: .9 }));
  alpha(T(t, k.a(2) - .5, k.a(2) + .5), () => txt('thick prompting', 300, 300, { size: 34, italic: 1, col: C.paper, a: .9 }));
};

/* ================= the frame ================= */
function draw(ctx, deck, tm, i, t, opts = {}) {
  X = ctx; const sc = deck.scenes[i], tsc = tm.scenes[i];
  const k = ctxFor(sc, tsc, Math.max(0, t), opts); k.sc = sc;
  X.save(); X.setTransform(ctx.canvas.width / W, 0, 0, ctx.canvas.height / H, 0, 0);
  X.fillStyle = C.bg; X.fillRect(0, 0, W, H);
  if (sc.section) txt(sc.section.toUpperCase(), 80, 58, { mono: 1, size: 13, col: C.mute, ls: 2.5 });
  if (sc.line && sc.layout !== 'title' && sc.id !== 'title') {
    const lines = wrap(sc.line, 1110, { size: 52 });
    revealLine(k, sc.line, 80, lines.length > 1 ? 112 : 132, lines.length > 1 ? 48 : 52, 1110);
  }
  (SC[sc.id] || (() => {}))(k, sc);
  if (sc.status) alpha(T(k.t, .2, .8), () => tag(sc.status, 1200, 64, { size: 11, col: C.gold, align: 'right' }));
  if (opts.number) txt(`${String(i + 1).padStart(2, '0')} / ${deck.scenes.length}`, 1200, 690, { mono: 1, size: 12, col: C.mute, align: 'right', ls: 1 });
  X.restore();
  return k.events;
}
/* events (thread attachments) for the sound, without drawing */
function events(deck, tm, i) {
  const noop = () => {}; const grad = { addColorStop: noop };
  const fake = new Proxy({ canvas: { width: W, height: H }, measureText: s => ({ width: String(s).length * 11 }), createRadialGradient: () => grad, createLinearGradient: () => grad }, { get: (o, p) => p in o ? o[p] : noop, set: () => true, has: () => false });
  return draw(fake, deck, tm, i, 0, {});
}
function load(base, done) {
  if (typeof Image === 'undefined') return done && done();
  const im = new Image(); im.onload = im.onerror = () => done && done(); im.src = (base || '') + 'the-play/wg_050-sprite.jpg'; IMG.wg050 = im;
}
const API = { W, H, C, draw, events, timingFor, estimate, load };
root.STAGE = API;
if (typeof module !== 'undefined') module.exports = API;
})(typeof window !== 'undefined' ? window : globalThis);
