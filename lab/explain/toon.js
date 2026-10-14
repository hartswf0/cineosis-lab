/* CINEOSIS TOONS · a hand-drawn cartoon kit for the explainer films.
   Drawn on twos (12 drawings a second) so lines boil like pencil tests. Two looks:
     scratch  white lines scratched into black film, hand-tinted colour inside the Os, grain, flicker, the odd hair in the gate
     grease   waxy grease-pencil strokes on warm paper
   TOON.play(canvas, scene, K, {style}) runs scene(d, t) where d is the drawing kit below and t the film's own clock (it follows the
   player's speed and pause). Everything is drawn from simple marks: line, circle, dot, and Bolas with four limbs. Red is the thread. */
(function () {
  const TAU = Math.PI * 2;
  const DOMC = { perception: '#d9b84a', affect: '#e07a5a', action: '#e8873f', reflection: '#8fbf5c', mental: '#5fb3b0', time: '#8f86e0', break: '#b3aa98', read: '#c886b6' };
  const ease = { lin: t => t, io: t => t < .5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t), out: t => 1 - (1 - t) * (1 - t), in: t => t * t,
    back: t => { const c = 1.9; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); }, bounce: t => { const n = 7.5625, d = 2.75; if (t < 1 / d) return n * t * t; if (t < 2 / d) return n * (t -= 1.5 / d) * t + .75; if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + .9375; return n * (t -= 2.625 / d) * t + .984375; } };
  /* keyframes: kv(t, [[t0, v0, 'ease'], [t1, v1], ...]); values may be numbers or arrays */
  function kv(t, ks) { if (t <= ks[0][0]) return ks[0][1]; for (let i = 0; i < ks.length - 1; i++) { const [a, va, e] = ks[i], [b, vb] = ks[i + 1]; if (t <= b) { const k = (ease[e || 'io'])((t - a) / (b - a || 1)); return Array.isArray(va) ? va.map((v, j) => v + (vb[j] - v) * k) : va + (vb - va) * k; } } return ks[ks.length - 1][1]; }
  const between = (t, a, b) => t >= a && t < b;
  function rnd(seed) { let s = (seed * 9301 + 49297) % 233280; return () => (s = (s * 9301 + 49297) % 233280) / 233280; }

  function kit(c, style, frame) {
    const S = style === 'grease', INK = S ? '#1b1712' : '#f2ede0', BG = S ? '#efe6d2' : '#0c0b0a', RED = S ? '#c8352a' : '#ff5a47';
    let sid = 0; const R = () => rnd(frame * 131 + (++sid) * 17);
    const d = { c, style, INK, BG, RED, frame, kv, ease, between, DOMC, W: c.canvas.width, H: c.canvas.height };
    /* one stroke, drawn the way the style draws: scratch = a bright incision with breaks, grease = several waxy passes */
    d.stroke = (pts, o = {}) => { if (pts.length < 2) return; const r = R(), col = o.col || INK, w = o.w || 3.2, j = o.j ?? 1.6;
      const passes = S ? 3 : 2;
      for (let p = 0; p < passes; p++) { c.beginPath(); let gap = false;
        pts.forEach(([x, y], i) => { const dx = (r() - .5) * j * 2, dy = (r() - .5) * j * 2; if (!S && p === 0 && r() < .03) gap = !gap; i && !gap ? c.lineTo(x + dx, y + dy) : c.moveTo(x + dx, y + dy); });
        c.strokeStyle = col; c.globalAlpha = (o.a ?? 1) * (S ? (p ? .5 : 1) : (p ? .5 : 1)); c.lineWidth = S ? w * (p ? .55 : 1.15) : w * (p ? .45 : 1.1); c.lineCap = 'round'; c.lineJoin = 'round'; c.stroke(); }
      c.globalAlpha = 1; };
    d.line = (x1, y1, x2, y2, o) => { const n = Math.max(2, Math.ceil(Math.hypot(x2 - x1, y2 - y1) / 18)); d.stroke([...Array(n + 1)].map((_, i) => [x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n]), o); };
    d.ring = (x, y, r, o = {}) => { const n = Math.max(16, Math.ceil(r * .9)), r0 = R(), wob = o.wob ?? Math.min(3, r * .05); d.stroke([...Array(n + 2)].map((_, i) => { const a = i / n * TAU + (o.rot || 0); const rr = r + (r0() - .5) * wob; return [x + Math.cos(a) * rr * (o.sx || 1), y + Math.sin(a) * rr * (o.sy || 1)]; }), o); };
    /* colour inside an O: hand-tinted, laid in with loose strokes that never quite fill */
    d.tint = (x, y, r, col, a = .85) => { const r0 = R(); c.save(); c.beginPath(); c.arc(x, y, r * .92, 0, TAU); c.clip(); c.globalAlpha = a * (S ? .55 : .7); c.strokeStyle = col; c.lineWidth = r * .16; c.lineCap = 'round';
      for (let k = -r; k < r; k += r * .13) { c.beginPath(); c.moveTo(x - r, y + k + (r0() - .5) * 6); c.lineTo(x + r, y + k - r * .5 + (r0() - .5) * 6); c.stroke(); } c.restore(); };
    d.dot = (x, y, r, col) => { c.fillStyle = col || INK; c.beginPath(); const r0 = R(); c.arc(x + (r0() - .5) * 1.5, y + (r0() - .5) * 1.5, r, 0, TAU); c.fill(); };
    d.thread = (x1, y1, x2, y2, o = {}) => d.line(x1, y1, x2, y2, { col: RED, w: o.w || 2.6, j: .9, ...o });
    d.curve = (pts, o = {}) => { const out = []; for (let i = 0; i < pts.length - 1; i++) for (let k = 0; k < 10; k++) { const t = k / 10, a = pts[i], b = pts[i + 1]; out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); } out.push(pts[pts.length - 1]); d.stroke(out, o); };
    d.text = (s, x, y, o = {}) => { const r0 = R(); c.save(); c.translate(x + (r0() - .5) * 1.2, y + (r0() - .5) * 1.2); c.rotate((o.rot || 0) + (r0() - .5) * .012); c.font = o.font || `italic ${o.size || 44}px Fraunces, Georgia, serif`; c.fillStyle = o.col || INK; c.textAlign = o.align || 'center'; c.textBaseline = 'middle'; c.globalAlpha = o.a ?? 1; c.fillText(s, 0, 0); c.restore(); };
    /* a picture always lives inside an O */
    d.pic = (img, x, y, r, o = {}) => { const isV = img && img.tagName === 'VIDEO', iw = img ? (isV ? img.videoWidth : img.naturalWidth) : 0, ih = img ? (isV ? img.videoHeight : img.naturalHeight) : 0;
      if (!img || !iw || (isV ? img.readyState < 2 : !img.complete)) { d.ring(x, y, r, o); return; } c.save(); c.beginPath(); c.arc(x, y, r * .95, 0, TAU); c.clip();
      const s = Math.max(2 * r / iw, 2 * r / ih) * (o.zoom || 1); c.globalAlpha = o.a ?? 1; if (!S) c.filter = 'sepia(.25) contrast(1.05)'; else c.filter = 'contrast(1.15) brightness(.95)';
      c.drawImage(img, x - iw * s / 2, y - ih * s / 2, iw * s, ih * s); c.restore(); d.ring(x, y, r, { w: o.w || 5, ...o }); };
    /* Bolas: an O body, the head with two eyes beneath, four limbs (two arms, two legs), hanging on its red thread.
       p: {x, y, r, sq (squash), lean, arms:[[dx,dy],[dx,dy]], legs:[[dx,dy],[dx,dy]], eyes:'open'|'blink'|'wink'|'shut', look:[x,y], thread:true|y0, fill, sym, body(d,x,y,r)} */
    d.bolas = (p) => { const r = p.r || 40, sq = p.sq || 1, sx = 1 / Math.sqrt(sq), x = p.x, y = p.y; c.save(); c.translate(x, y); c.rotate(p.lean || 0); c.translate(-x, -y);
      if (p.thread !== false) d.thread(x, p.thread ?? -20, x, y - r * sq, { w: Math.max(2, r * .07) });
      const arms = p.arms || [[-r * 1.5, r * .4], [r * 1.5, r * .4]], legs = p.legs || [[-r * .9, r * 2.3], [r * .9, r * 2.3]];
      arms.forEach(([ax, ay], i) => { const s = i ? 1 : -1, sxp = x + s * r * .9 * sx, syp = y - r * .1; const ex = (sxp + x + ax) / 2 + s * r * .25, ey = (syp + y + ay) / 2 - r * .45; d.curve([[sxp, syp], [ex, ey], [x + ax, y + ay]], { w: Math.max(2.4, r * .09) }); });
      legs.forEach(([lx, ly], i) => { const s = i ? 1 : -1, hx = x + s * r * .55, hy = y + r * .75 * sq; const kx = (hx + x + lx) / 2 + s * r * .35, ky = (hy + y + ly) / 2 - r * .2; d.curve([[hx, hy], [kx, ky], [x + lx, y + ly]], { w: Math.max(2.4, r * .09) }); });
      if (p.fill) d.tint(x, y, r, p.fill);
      c.save(); c.translate(x, y); c.scale(sx, sq); c.translate(-x, -y); d.ring(x, y, r, { w: Math.max(3, r * .13) }); if (p.body) p.body(d, x, y, r);
      if (p.sym) d.text(p.sym, x, y + r * .06, { size: r * .8, font: `600 ${r * .8}px Fraunces, Georgia, serif` }); c.restore();
      const hy = y + r * sq + r * .5, hr = r * .42; c.fillStyle = BG; c.beginPath(); c.arc(x, hy, hr, 0, TAU); c.fill(); d.ring(x, hy, hr, { w: Math.max(2.4, r * .09) });
      d.eyes(x, hy, hr, p.eyes || 'open', p.look || [0, 0]); c.restore(); };
    d.eyes = (x, y, r, st, look = [0, 0]) => { const ex = r * .42, er = r * .2, lx = look[0] * r * .2, ly = look[1] * r * .2;
      [-1, 1].forEach(s => { const shut = st === 'blink' || st === 'shut' || (st === 'wink' && s > 0); const cx = x + s * ex + lx, cy = y + ly;
        if (shut) d.curve([[cx - er * 1.2, cy], [cx, cy + (st === 'wink' ? er * 1.3 : er * .3)], [cx + er * 1.2, cy]], { w: Math.max(2, r * .12), j: .5 }); else d.dot(cx, cy, er); }); };
    /* the machine: a projector box with one lens eye that only blinks */
    d.machine = (x, y, s = 1, o = {}) => { const w = 150 * s, h = 100 * s; d.stroke([[x - w / 2, y - h / 2], [x + w / 2, y - h / 2], [x + w / 2, y + h / 2], [x - w / 2, y + h / 2], [x - w / 2, y - h / 2]], { w: 4 });
      d.ring(x - w * .22, y - h / 2 - 34 * s, 30 * s, { w: 4, rot: o.spin || 0 }); d.ring(x + w * .22, y - h / 2 - 34 * s, 30 * s, { w: 4, rot: -(o.spin || 0) });
      const lx = x + w / 2 + 26 * s; d.ring(lx, y, 26 * s, { w: 4 }); if (o.blink) d.line(lx - 20 * s, y, lx + 20 * s, y, { w: 5 }); else d.dot(lx + (o.look || 0) * 8 * s, y, 11 * s);
      d.line(x - w * .3, y + h / 2, x - w * .4, y + h / 2 + 40 * s, { w: 3 }); d.line(x + w * .3, y + h / 2, x + w * .4, y + h / 2 + 40 * s, { w: 3 }); };
    d.beam = (x1, y1, x2, y2, spread, a = .12) => { c.save(); c.globalAlpha = a * (S ? .45 : 1); c.fillStyle = S ? '#8a7650' : '#fff3c8'; c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2 - spread); c.lineTo(x2, y2 + spread); c.closePath(); c.fill(); c.restore(); };
    return d;
  }
  /* the film surface: scratch = black emulsion with grain, flicker and the odd hair; grease = paper with tooth */
  function surface(c, style, frame) { const W = c.canvas.width, H = c.canvas.height, r = rnd(frame * 7 + 3); c.filter = 'none';
    if (style === 'grease') { c.fillStyle = '#efe6d2'; c.fillRect(0, 0, W, H); c.fillStyle = 'rgba(80,60,30,.05)'; for (let i = 0; i < 260; i++) c.fillRect(r() * W, r() * H, 2 + r() * 3, 1); return; }
    const fl = .94 + r() * .06; c.fillStyle = `rgb(${12 * fl | 0},${11 * fl | 0},${10 * fl | 0})`; c.fillRect(0, 0, W, H);
    c.fillStyle = 'rgba(255,250,235,.06)'; for (let i = 0; i < 420; i++) c.fillRect(r() * W, r() * H, 1.4, 1.4);
    if (r() < .5) { c.strokeStyle = 'rgba(255,250,235,.14)'; c.lineWidth = 1; const x = r() * W; c.beginPath(); c.moveTo(x, 0); c.lineTo(x + (r() - .5) * 30, H); c.stroke(); }
    if (r() < .12) { c.strokeStyle = 'rgba(255,250,235,.35)'; c.lineWidth = 1.2; const x = r() * W, y = r() * H; c.beginPath(); c.moveTo(x, y); c.bezierCurveTo(x + 30, y - 20, x + 50, y + 30, x + 80, y + 4); c.stroke(); }
  }
  function post(c, style, frame) { if (style === 'grease') return; const W = c.canvas.width, H = c.canvas.height; const g = c.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, H * .85); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.55)'); c.fillStyle = g; c.fillRect(0, 0, W, H); }
  /* play a scene on a canvas, on twos, on the film's clock */
  function play(cv, scene, K, o = {}) { const c = cv.getContext('2d'), style = o.style || 'scratch'; let last = -1;
    const draw = t => { const fr = Math.floor(t * 12); if (fr === last) return true; last = fr; const tq = fr / 12;
      c.setTransform(1, 0, 0, 1, 0, 0); surface(c, style, Math.floor(fr / (o.hold || 1))); const d = kit(c, style, Math.floor(fr / 2)); scene(d, tq); post(c, style, fr); return true; };
    if (K && K.raf) K.raf(draw); else { const t0 = performance.now(); const go = () => { draw((performance.now() - t0) / 1000); requestAnimationFrame(go); }; go(); } }
  const IMG = {}; function img(src) { if (!IMG[src]) { const i = new Image(); i.src = src; IMG[src] = i; } return IMG[src]; }
  window.TOON = { play, kv, ease, between, img, DOMC };
})();
