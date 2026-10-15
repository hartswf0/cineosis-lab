/* REEL · the film grammar for lessons that should play like films, not slides.
   The picture area is x 40..1400, y 40..750; the band of words sits beneath; Bolas lives in the right-hand gutter (x 1440..1580),
   so his red thread never crosses a picture. Exception: when the screen holds no picture he may come to the centre.
     REEL.cam(world, K)           a camera on a world div: to(x, y, scale, secs), fit({x,y,w,h}, secs), set(...)
     REEL.box(r, src, o)          html for a moving picture placed at rect r; REEL.place(el, r, secs) flies it to a new rect
     REEL.cuts(K, els, times, f)  hard cuts: show one element at a time, call f(i) at each cut
     REEL.bolas(stage, K, o)      the character: a ring with two eyes on the red thread, with weight, spring and moods
        .to(x,y,r) .drop(x,y,r) .hop() .nod() .shake() .spin() .blink() .wink() .look(x,y|null) .wide(s) .think(s) .sad(s)
        .feel(mood, secs) .leap(x,y,r) .anchor(x,y) .tilt via moods; see MOOD below
        .iris(holder, secs) opens his ring into the picture held in holder;  .unIris(holder, secs) closes it again
     REEL.strand(svg, K, a, b, secs)  a red thread drawn between two points;  REEL.jiggle(el, K) a picture's cartoon wobble
   Every timer runs on the player's clock (K.later / K.raf), so pause and speed work. */
(function () {
  const NS = 'http://www.w3.org/2000/svg', RED = '#e0483a', INK = '#ece6da', BG = '#0b0a09';
  const PA = { x: 40, y: 40, w: 1360, h: 710 }, PARK = { x: 1510, y: 600, r: 40 };
  const E = { io: k => k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2, out: k => 1 - Math.pow(1 - k, 3), in: k => k * k * k, lin: k => k };
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  function tween(K, secs, f, e = 'io', done) { let t0 = null; K.raf(t => { if (t0 === null) t0 = t; const k = secs <= 0 ? 1 : Math.min(1, (t - t0) / secs); f(E[e](k)); if (k >= 1) { done && done(); return false; } return true; }); }

  function cam(world, K) {
    let c = { x: PA.x + PA.w / 2, y: PA.y + PA.h / 2, s: 1 }; world.style.transformOrigin = '0 0';
    const put = () => world.style.transform = `translate(${PA.x + PA.w / 2 - c.x * c.s}px,${PA.y + PA.h / 2 - c.y * c.s}px) scale(${c.s})`; put();
    const api = {
      set(x, y, s) { c = { x, y, s }; put(); return api; },
      to(x, y, s, secs = 1.5, e = 'io') { const a = { ...c }; tween(K, secs, k => { c = { x: a.x + (x - a.x) * k, y: a.y + (y - a.y) * k, s: a.s * Math.pow(s / a.s, k) }; put(); }, e); return api; },
      fit(r, secs = 1.5, e = 'io', pad = .96, max = 3.2) { const s = Math.min(max, Math.min(PA.w / r.w, PA.h / r.h) * pad); return secs ? api.to(r.x + r.w / 2, r.y + r.h / 2, s, secs, e) : api.set(r.x + r.w / 2, r.y + r.h / 2, s); },
      whip(x, y, s, secs = .55) { world.style.transition = 'filter .2s'; world.style.filter = 'blur(6px)'; K.later(secs * 700, () => world.style.filter = ''); return api.to(x, y, s, secs, 'io'); },
      home(secs = 1.5, e) { return api.to(PA.x + PA.w / 2, PA.y + PA.h / 2, 1, secs, e); } };
    return api;
  }
  const R = r => `left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px`;
  function box(r, src, o = {}) {
    const vid = src ? `<video muted ${o.once ? '' : 'loop'} playsinline preload="auto" data-src="${esc(src)}" data-t="${o.t || 0}" ${o.end ? `data-end="${o.end}"` : ''}></video>` : '';
    return `<div class="bx ${o.cls || ''}" ${o.id ? `id="${o.id}"` : ''} style="${R(r)};${o.hide ? 'opacity:0;' : ''}${o.style || ''}">${vid}${o.cap ? `<span class="cap">${o.cap}</span>` : ''}</div>`;
  }
  function place(el, r, secs = 1, e = 'cubic-bezier(.45,.05,.25,1)') { el.style.transition = `left ${secs}s ${e},top ${secs}s ${e},width ${secs}s ${e},height ${secs}s ${e},opacity .4s`; Object.assign(el.style, { left: r.x + 'px', top: r.y + 'px', width: r.w + 'px', height: r.h + 'px' }); }
  function cuts(K, els, times, f) { times.forEach((t, i) => K.later(t * 1000, () => { els.forEach((e, j) => { e.style.transition = 'none'; e.style.opacity = j === i ? 1 : 0; }); f && f(i); })); }
  const grid = (n, cols, r = PA, gap = 14, aspect = .75) => { const w = (r.w - gap * (cols - 1)) / cols, h = w * aspect, rows = Math.ceil(n / cols), H = rows * h + (rows - 1) * gap, y0 = r.y + Math.max(0, (r.h - H) / 2);
    return [...Array(n).keys()].map(i => ({ x: r.x + (i % cols) * (w + gap), y: y0 + Math.floor(i / cols) * (h + gap), w, h })); };

  /* THE CHARACTER, drawn like a cartoon: squash and stretch along his motion, anticipation before a leap, a thread that whips behind
     him, and eyes built from lids (top lid angle, bottom lid, openness, pupil size) so one ring and two dots can carry a face.
     He breathes, glances and blinks on his own. Moods: neutral happy laugh surprised curious suspicious angry sad sleepy dizzy
     determined confused think excited. g.feel(mood, secs) sets one; the short names (wide, sad, think, squint, wink) still work. */
  const MOOD = {
    neutral: {}, happy: { shape: ['arc', 'arc'], tilt: 6 }, laugh: { shape: ['arc', 'arc'], bounce: 1, tilt: -4 },
    surprised: { ps: [1.5, 1.5], lt: -.2, hop: 460, stretch: .22 }, curious: { ps: [1.3, .9], o: [1, .85], tilt: 14 },
    suspicious: { o: [.42, .42], lt: .08, lo: .12, tilt: -6 }, angry: { o: [.75, .75], lt: .6, shiver: 1 }, sad: { o: [.65, .65], lt: -.55, tilt: -8, sink: 26, look: [0, 1] },
    sleepy: { o: [.2, .2], lt: -.1, zz: 1, tilt: 10 }, dizzy: { shape: ['spiral', 'spiral'], wobble: 1 }, determined: { o: [.78, .78], lt: .32, tilt: -3 },
    confused: { ps: [1.25, .8], o: [1, .62], tilt: -12, wobble: .4 }, think: { o: [.8, .8], lo: .1, tilt: 9, look: [.6, -.9] }, excited: { ps: [1.3, 1.3], bounce: 1, hop: 300 } };
  function eyePath(cx, cy, rx, ry, o, lt, lo, inner) {
    const top = cy - ry + 2 * ry * (1 - o), bot = cy + ry - 2 * ry * lo, lid = x => top + lt * ry * ((x - cx) / rx) * inner, pts = [];
    if (o < .1 || lid(cx) >= bot - ry * .12) { const y = Math.min(bot, cy + ry * .2); return { line: `M${cx - rx * 1.1},${y + lt * ry * -inner * .6} Q${cx},${y + ry * .5} ${cx + rx * 1.1},${y + lt * ry * inner * .6}` }; }
    for (let i = 0; i <= 28; i++) { const a = i / 28 * Math.PI * 2, x = cx + rx * Math.cos(a), y = cy + ry * Math.sin(a); pts.push([x, Math.min(bot, Math.max(lid(x), y))]); }
    return { fill: 'M' + pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('L') + 'Z' };
  }
  function bolas(stage, K, o = {}) {
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', '0 0 1600 900'); svg.setAttribute('width', 1600); svg.setAttribute('height', 900);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none;z-index:6';
    svg.innerHTML = `<path class="th" fill="none" stroke="${RED}" stroke-linecap="round"/><g class="zz"></g><g class="bd"><circle fill="${BG}" stroke="${INK}"/><g class="ey"><path/><path/></g></g>`;
    stage.appendChild(svg);
    const th = svg.querySelector('.th'), body = svg.querySelector('.bd'), ring = body.querySelector('circle'), eyes = [...body.querySelectorAll('.ey path')], eg = body.querySelector('.ey'), zz = svg.querySelector('.zz');
    const x0 = o.x ?? PARK.x, y0 = o.y ?? -160;
    const S = { T: { x: x0, y: y0 }, P: { x: x0, y: y0 }, V: { x: 0, y: 0 }, px: x0, anchor: null, r: o.r || PARK.r, rT: o.r || PARK.r, tilt: 0, spin: 0, spinV: 0, sq: 0,
      look: null, pupil: [0, 0], glance: [0, 0], E: [0, 1].map(() => ({ o: 1, lt: 0, lo: 0, ps: 1, shape: 'n', blink: 1 })), mood: 'neutral', moodUntil: 0, wink: -1, winkUntil: 0,
      shake: 0, nod: 0, time: 0, nextBlink: 1.5 + Math.random() * 2, nextGlance: 1.2, nextBounce: 0, nextZ: 0, eyeA: 1, ringOnly: 0, thread: 1, k: 34, c: 6.5 };
    let last = 0;
    const want = () => { const m = MOOD[S.mood] || {}, a = (v, i, d) => v == null ? d : Array.isArray(v) ? v[i] : v; return [0, 1].map(i => ({ o: a(m.o, i, 1), lt: a(m.lt, i, 0), lo: a(m.lo, i, 0), ps: a(m.ps, i, 1), shape: a(m.shape, i, 'n') })); };
    const frame = t => {
      const dt = Math.min(.05, Math.max(0, t - last)); last = t; S.time = t; const m = MOOD[S.mood] || {};
      if (S.mood !== 'neutral' && t > S.moodUntil) S.mood = 'neutral';
      const ty = S.T.y + (m.sink || 0);
      S.px += (S.T.x - S.px) * Math.min(1, dt * 7);
      S.V.x += (S.k * (S.T.x - S.P.x) - S.c * S.V.x) * dt; S.V.y += (S.k * (ty - S.P.y) - S.c * S.V.y) * dt; S.P.x += S.V.x * dt; S.P.y += S.V.y * dt;
      S.r += (S.rT - S.r) * Math.min(1, dt * 8); S.sq *= Math.pow(.004, dt);
      if (m.bounce && t > S.nextBounce) { S.V.y -= 240; S.nextBounce = t + .26; K.later(130, () => S.sq = .14); }
      if (m.zz && t > S.nextZ) { S.nextZ = t + 1.1; const z = document.createElementNS(NS, 'text'); z.textContent = 'z'; z.setAttribute('fill', INK); z.setAttribute('font-family', 'Fraunces, Georgia, serif'); z.setAttribute('font-style', 'italic');
        const bx = S.P.x + S.r * .8, by = S.P.y - S.r * .6; zz.appendChild(z); tween(K, 1.6, k => { z.setAttribute('x', bx + k * 26 + Math.sin(k * 6) * 6); z.setAttribute('y', by - k * 60); z.setAttribute('font-size', 14 + k * 16); z.style.opacity = 1 - k; }, 'lin', () => z.remove()); }
      const breathe = Math.sin(t * 1.7) * 3, wob = (m.wobble || 0) * Math.sin(t * 7) * 9, shiv = (m.shiver ? Math.sin(t * 60) * 2.2 : 0);
      const x = S.P.x + Math.sin(t * .9) * 2 + Math.sin(S.shake * 40) * S.shake * 26 + shiv, y = S.P.y + breathe + Math.sin(S.nod * 30) * S.nod * 18;
      S.shake = Math.max(0, S.shake - dt); S.nod = Math.max(0, S.nod - dt);
      S.spin += S.spinV * dt; S.spinV *= Math.pow(.02, dt); if (Math.abs(S.spinV) < 5) S.spin += (Math.round(S.spin / 360) * 360 - S.spin) * Math.min(1, dt * 6);
      S.tilt += ((m.tilt || 0) + wob - S.tilt) * Math.min(1, dt * 6);
      // eyes: auto blink, glances, look, mood targets
      if (t > S.nextBlink) { S.E.forEach(e => e.blink = 0); S.nextBlink = t + 2.2 + Math.random() * 3.2; }
      if (!S.look && t > S.nextGlance) { S.glance = [Math.random() * 2 - 1, Math.random() * 1.4 - .7]; S.nextGlance = t + .7 + Math.random() * 1.8; }
      let d = m.look || S.glance; if (S.look && !m.look) { const dx = S.look[0] - x, dy = S.look[1] - y, n = Math.hypot(dx, dy) || 1; d = [dx / n, dy / n]; }
      S.pupil[0] += (d[0] - S.pupil[0]) * Math.min(1, dt * 14); S.pupil[1] += (d[1] - S.pupil[1]) * Math.min(1, dt * 14);
      const W = want(); if (S.wink >= 0 && t < S.winkUntil) { W[S.wink].shape = 'arc'; } else S.wink = -1;
      const r = S.r, ex = r * .34, er = r * .17, f = Math.min(1, dt * 16);
      S.E.forEach((e, i) => { const w = W[i]; e.o += (w.o - e.o) * f; e.lt += (w.lt - e.lt) * f; e.lo += (w.lo - e.lo) * f; e.ps += (w.ps - e.ps) * f; e.shape = w.shape; e.blink += (1 - e.blink) * Math.min(1, dt * 11); });
      // body: stretch along the motion, squash on impulse, lean on the thread
      const v = Math.hypot(S.V.x, S.V.y), st = Math.min(.24, v * .00032) + (m.stretch && t < S.moodUntil - .6 ? 0 : 0), va = Math.atan2(S.V.y, S.V.x) * 180 / Math.PI;
      const ax = S.anchor ? S.anchor[0] : S.px, ay = S.anchor ? S.anchor[1] : -30, lean = S.anchor ? 0 : Math.atan2(x - S.px, Math.max(40, y + 30)) * 180 / Math.PI;
      body.setAttribute('transform', `translate(${x},${y}) rotate(${va}) scale(${1 + st},${1 - st * .55}) rotate(${-va}) rotate(${-lean * .6 + S.tilt + S.spin}) scale(${1 + S.sq * .7},${1 - S.sq})`);
      const tx = x, tyy = y - r * (1 - S.sq), mx = (ax + tx) / 2 - S.V.x * .09, my = (ay + tyy) / 2 - S.V.y * .03;
      th.setAttribute('d', `M${ax},${ay} Q${mx},${my} ${tx},${tyy}`); th.setAttribute('stroke-width', Math.max(2, Math.min(5, r * .07))); th.style.opacity = S.thread;
      ring.setAttribute('r', r); ring.setAttribute('stroke-width', Math.min(14, Math.max(3, r * .13))); ring.style.fillOpacity = 1 - S.ringOnly; eg.style.opacity = S.eyeA;
      eyes.forEach((p, i) => { const e = S.E[i], cx = (i ? ex : -ex) + S.pupil[0] * r * .12, cy = S.pupil[1] * r * .12, rx = er * e.ps, ry = er * 1.12 * e.ps, inner = i ? -1 : 1;
        let g;
        if (e.shape === 'arc') g = { line: `M${cx - rx * 1.2},${cy + ry * .45} Q${cx},${cy - ry * 1.5} ${cx + rx * 1.2},${cy + ry * .45}` };
        else if (e.shape === 'spiral') { let s = ''; for (let k = 0; k <= 30; k++) { const a = k * .55 + t * 9 * (i ? -1 : 1), rr = rx * 1.3 * k / 30; s += (k ? 'L' : 'M') + (cx + Math.cos(a) * rr).toFixed(1) + ',' + (cy + Math.sin(a) * rr).toFixed(1); } g = { line: s }; }
        else g = eyePath(cx, cy, rx, ry, e.o * e.blink, e.lt, e.lo, inner);
        if (g.fill) { p.setAttribute('d', g.fill); p.setAttribute('fill', INK); p.setAttribute('stroke', 'none'); }
        else { p.setAttribute('d', g.line); p.setAttribute('fill', 'none'); p.setAttribute('stroke', INK); p.setAttribute("stroke-width", Math.max(2, r * (e.shape === "spiral" ? .045 : .075))); p.setAttribute('stroke-linecap', 'round'); } });
      return true;
    };
    K.raf(frame);
    const g = {
      el: svg, state: S,
      to(x, y, r) { S.T = { x, y }; if (r) S.rT = r; return g; },
      park(y = PARK.y, r = PARK.r) { S.anchor = null; return g.to(PARK.x, y, r); },
      drop(x, y, r) { S.P = { x, y: -180 }; S.px = x; S.V = { x: 0, y: 0 }; K.later(650, () => S.sq = .3); return g.to(x, y, r); },
      leap(x, y, r, wind = .16) { S.sq = .32; K.later(wind * 1000, () => { S.sq = -.12; const dx = x - S.P.x, dy = y - S.P.y; S.V.x += dx * 2.2; S.V.y += dy * 2.2 - 260; g.to(x, y, r); K.later(520, () => S.sq = .22); }); return g; },
      anchor(x, y) { S.anchor = x == null ? null : [x, y]; return g; },
      hop(v = 520) { S.sq = .25; K.later(90, () => { S.sq = -.15; S.V.y -= v; }); K.later(560, () => S.sq = .2); return g; },
      nod() { S.nod = .5; return g; }, shake() { S.shake = .5; return g; }, spin(v = 900) { S.spinV = v; return g; },
      blink() { S.E.forEach(e => e.blink = 0); return g; },
      feel(mood, secs = 1.6) { S.mood = mood; S.moodUntil = S.time + secs; const m = MOOD[mood] || {}; if (m.hop) g.hop(m.hop); if (m.stretch) S.sq = -m.stretch; return g; },
      wink(secs = 1, side = 1) { S.wink = side ? 1 : 0; S.winkUntil = S.time + secs; S.tilt += 10; g.nod(); return g; },
      look(x, y) { S.look = x == null ? null : [x, y]; return g; },
      wide(secs = 1.2) { return g.feel('surprised', secs); }, think(secs = 2) { return g.feel('think', secs); }, sad(secs = 2) { return g.feel('sad', secs); }, squint(secs = 1.5) { return g.feel('suspicious', secs); },
      iris(holder, secs = 1.4) {
        const cx = S.P.x - PA.x, cy = S.P.y - PA.y, r0 = S.r; holder.style.opacity = 1; holder.style.clipPath = `circle(${r0}px at ${cx}px ${cy}px)`;
        tween(K, secs, k => { const rr = r0 + (1700 - r0) * k; holder.style.clipPath = `circle(${rr}px at ${cx}px ${cy}px)`; S.rT = S.r = rr; S.eyeA = 1 - Math.min(1, k * 8); S.ringOnly = 1; S.thread = 1 - k; }, 'in',
          () => { holder.style.clipPath = 'none'; S.eyeA = 1; S.ringOnly = 0; S.thread = 1; S.r = S.rT = PARK.r; S.P = { x: PARK.x, y: -200 }; S.px = PARK.x; S.T = { x: PARK.x, y: PARK.y }; S.V = { x: 0, y: 0 }; S.anchor = null; });
        return g; },
      unIris(holder, x, y, r, secs = 1.2) {
        const cx = x - PA.x, cy = y - PA.y; S.P = { x, y }; S.px = x; S.T = { x, y }; S.V = { x: 0, y: 0 }; S.ringOnly = 1; S.eyeA = 0; S.thread = 0;
        tween(K, secs, k => { const rr = 1700 + (r - 1700) * k; holder.style.clipPath = `circle(${rr}px at ${cx}px ${cy}px)`; S.r = S.rT = rr; S.thread = k; S.eyeA = Math.max(0, k * 3 - 2); }, 'out',
          () => { holder.style.opacity = 0; holder.style.clipPath = 'none'; S.ringOnly = 0; S.eyeA = 1; S.thread = 1; g.blink(); });
        return g; } };
    return g;
  }
  /* a strand of red thread drawn from a to b over secs, into an svg layer (the web Bolas spins) */
  function strand(svgLayer, K, a, b, secs = .8, w = 3) {
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', `M${a[0]},${a[1]} L${b[0]},${b[1]}`); p.setAttribute('stroke', RED); p.setAttribute('stroke-width', w); p.setAttribute('fill', 'none'); p.setAttribute('stroke-linecap', 'round');
    svgLayer.appendChild(p); const L = Math.hypot(b[0] - a[0], b[1] - a[1]); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; tween(K, secs, k => p.style.strokeDashoffset = L * (1 - k), 'out'); return p;
  }
  /* a picture that reacts: a quick cartoon wobble when something lands on it */
  function jiggle(el, K, amt = 1) { tween(K, .7, k => { const d = Math.exp(-5 * k) * Math.sin(k * 26); el.style.transform = `scale(${1 + .05 * amt * d},${1 - .04 * amt * d}) rotate(${1.4 * amt * d}deg)`; }, 'lin', () => el.style.transform = ''); }
  window.REEL = { PA, PARK, cam, box, place, cuts, grid, bolas, strand, jiggle, tween, esc, MOOD };
})();
