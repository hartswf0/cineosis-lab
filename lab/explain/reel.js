/* REEL · the film grammar for lessons that should play like films, not slides.
   The picture area is x 40..1400, y 40..750; the band of words sits beneath; Bolas lives in the right-hand gutter (x 1440..1580),
   so his red thread never crosses a picture. Exception: when the screen holds no picture he may come to the centre.
     REEL.cam(world, K)           a camera on a world div: to(x, y, scale, secs), fit({x,y,w,h}, secs), set(...)
     REEL.box(r, src, o)          html for a moving picture placed at rect r; REEL.place(el, r, secs) flies it to a new rect
     REEL.cuts(K, els, times, f)  hard cuts: show one element at a time, call f(i) at each cut
     REEL.bolas(stage, K, o)      the character: a ring with two eyes on the red thread, with weight, spring and moods
        .to(x,y,r) .drop(x,y,r) .hop() .nod() .shake() .spin() .blink() .wink() .look(x,y|null) .wide(s) .think(s) .sad(s)
        .iris(holder, secs) opens his ring into the picture held in holder;  .unIris(holder, secs) closes it again
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

  /* THE CHARACTER. Physics: the thread's pivot follows the target quickly; the ring hangs on a soft spring beneath it, so he swings,
     overshoots and settles. He breathes, glances about and blinks on his own when nothing is asked of him. */
  function bolas(stage, K, o = {}) {
    const svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', '0 0 1600 900'); svg.setAttribute('width', 1600); svg.setAttribute('height', 900);
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;pointer-events:none;z-index:6';
    svg.innerHTML = `<line stroke="${RED}" stroke-linecap="round"/><g><circle fill="${BG}" stroke="${INK}"/><g class="ey"><ellipse fill="${INK}"/><ellipse fill="${INK}"/></g></g>`;
    stage.appendChild(svg);
    const [th, body] = [svg.querySelector('line'), svg.querySelector('g')], ring = body.querySelector('circle'), eyes = [...body.querySelectorAll('ellipse')], eg = body.querySelector('.ey');
    const S = { T: { x: o.x ?? PARK.x, y: o.y ?? -160 }, P: { x: o.x ?? PARK.x, y: o.y ?? -160 }, V: { x: 0, y: 0 }, px: o.x ?? PARK.x, r: o.r || PARK.r, rT: o.r || PARK.r,
      look: null, pupil: [0, 0], ps: 1, psT: 1, lids: [1, 1], lidT: [1, 1], spin: 0, spinV: 0, shake: 0, nod: 0, time: 0, nextBlink: 2 + Math.random() * 2, nextGlance: 1.5, glance: [0, 0],
      hold: 0, mood: null, moodUntil: 0, ringOnly: 0, eyeA: 1, thread: 1 };
    let last = 0;
    const frame = t => {
      const dt = Math.min(.05, t - last); last = t; S.time = t;
      S.px += (S.T.x - S.px) * Math.min(1, dt * 7);
      const k = 34, c = 6.5; S.V.x += (k * (S.T.x - S.P.x) - c * S.V.x) * dt; S.V.y += (k * (S.T.y - S.P.y) - c * S.V.y) * dt; S.P.x += S.V.x * dt; S.P.y += S.V.y * dt;
      S.r += (S.rT - S.r) * Math.min(1, dt * 8);
      const breathe = Math.sin(t * 1.7) * 3.2, x = S.P.x + Math.sin(t * .9) * 2 + Math.sin(S.shake * 40) * S.shake * 26, y = S.P.y + breathe + Math.sin(S.nod * 30) * S.nod * 18;
      S.shake = Math.max(0, S.shake - dt); S.nod = Math.max(0, S.nod - dt);
      S.spin += S.spinV * dt; S.spinV *= Math.pow(.02, dt); if (Math.abs(S.spinV) < 5) { S.spin += (Math.round(S.spin / 360) * 360 - S.spin) * Math.min(1, dt * 6); }
      // moods expire
      if (S.mood && t > S.moodUntil) { S.mood = null; S.psT = 1; S.lidT = [1, 1]; }
      // auto blink and glances when idle
      if (!S.mood && t > S.nextBlink) { S.lids = [0, 0]; S.nextBlink = t + 2.4 + Math.random() * 3; }
      if (!S.look && !S.mood && t > S.nextGlance) { S.glance = [Math.random() * 2 - 1, Math.random() * 1.4 - .7]; S.nextGlance = t + .8 + Math.random() * 1.8; }
      let d = S.glance; if (S.look) { const dx = S.look[0] - x, dy = S.look[1] - y, m = Math.hypot(dx, dy) || 1; d = [dx / m, dy / m]; }
      if (S.mood === 'think') d = [.6, -.9]; if (S.mood === 'sad') d = [0, .8];
      S.pupil[0] += (d[0] - S.pupil[0]) * Math.min(1, dt * 14); S.pupil[1] += (d[1] - S.pupil[1]) * Math.min(1, dt * 14);
      S.ps += (S.psT - S.ps) * Math.min(1, dt * 10); for (let i = 0; i < 2; i++) S.lids[i] += (S.lidT[i] - S.lids[i]) * Math.min(1, dt * 16);
      // draw
      const r = S.r, sq = Math.max(-.22, Math.min(.22, S.V.y * .0005)), sx = 1 - sq * .6, sy = 1 + sq, lean = Math.atan2(x - S.px, Math.max(40, y + 30)) * 180 / Math.PI;
      th.setAttribute('x1', S.px); th.setAttribute('y1', -30); th.setAttribute('x2', x); th.setAttribute('y2', y - r * sy); th.setAttribute('stroke-width', Math.max(2, r * .07)); th.style.opacity = S.thread;
      body.setAttribute('transform', `translate(${x},${y}) rotate(${-lean * .6 + S.spin}) scale(${sx},${sy})`);
      ring.setAttribute('r', r); ring.setAttribute('stroke-width', Math.min(14, Math.max(3, r * .13))); ring.style.fillOpacity = 1 - S.ringOnly;
      const ex = r * .34, er = r * .17 * S.ps; eg.style.opacity = S.eyeA;
      eyes.forEach((e, i) => { e.setAttribute('cx', (i ? ex : -ex) + S.pupil[0] * r * .13); e.setAttribute('cy', S.pupil[1] * r * .13 - (S.mood === 'wide' ? r * .04 : 0)); e.setAttribute('rx', er); e.setAttribute('ry', Math.max(er * .12, er * S.lids[i] * (S.mood === 'sad' ? .55 : 1))); });
      return true;
    };
    K.raf(frame);
    const g = {
      el: svg, state: S,
      to(x, y, r, opt) { S.T = { x, y }; if (r) S.rT = r; return g; },
      park(y = PARK.y, r = PARK.r) { return g.to(PARK.x, y, r); },
      drop(x, y, r) { S.P = { x, y: -180 }; S.px = x; S.V = { x: 0, y: 0 }; return g.to(x, y, r); },
      hop(v = 520) { S.V.y -= v; return g; }, nod() { S.nod = .5; return g; }, shake() { S.shake = .5; return g; }, spin(v = 900) { S.spinV = v; return g; },
      blink() { S.lids = [0, 0]; S.lidT = [1, 1]; return g; },
      wink(secs = 1, side = 1) { S.mood = 'wink'; S.moodUntil = S.time + secs; S.lidT = side ? [1, 0] : [0, 1]; S.psT = 1.05; g.nod(); return g; },
      look(x, y) { S.look = x == null ? null : [x, y]; return g; },
      wide(secs = 1.2) { S.mood = 'wide'; S.moodUntil = S.time + secs; S.psT = 1.6; S.lidT = [1, 1]; g.hop(380); return g; },
      think(secs = 2) { S.mood = 'think'; S.moodUntil = S.time + secs; S.lidT = [.6, .6]; return g; },
      sad(secs = 2) { S.mood = 'sad'; S.moodUntil = S.time + secs; S.lidT = [.5, .5]; return g; },
      squint(secs = 1.5) { S.mood = 'squint'; S.moodUntil = S.time + secs; S.lidT = [.3, .3]; return g; },
      /* the ring opens into the picture: holder is a full picture-area element (hidden), revealed through a growing circle */
      iris(holder, secs = 1.4) {
        const cx = S.P.x - PA.x, cy = S.P.y - PA.y, r0 = S.r; holder.style.opacity = 1; holder.style.clipPath = `circle(${r0}px at ${cx}px ${cy}px)`;
        tween(K, secs, k => { const rr = r0 + (1700 - r0) * k; holder.style.clipPath = `circle(${rr}px at ${cx}px ${cy}px)`; S.rT = S.r = rr; S.eyeA = 1 - Math.min(1, k * 8); S.ringOnly = 1; S.thread = 1 - k; }, 'in',
          () => { holder.style.clipPath = 'none'; S.eyeA = 1; S.ringOnly = 0; S.thread = 1; S.r = S.rT = PARK.r; S.P = { x: PARK.x, y: -200 }; S.px = PARK.x; S.T = { x: PARK.x, y: PARK.y }; S.V = { x: 0, y: 0 }; });
        return g; },
      unIris(holder, x, y, r, secs = 1.2) {
        const cx = x - PA.x, cy = y - PA.y; S.P = { x, y }; S.px = x; S.T = { x, y }; S.V = { x: 0, y: 0 }; S.ringOnly = 1; S.eyeA = 0; S.thread = 0;
        tween(K, secs, k => { const rr = 1700 + (r - 1700) * k; holder.style.clipPath = `circle(${rr}px at ${cx}px ${cy}px)`; S.r = S.rT = rr; S.thread = k; S.eyeA = Math.max(0, k * 3 - 2); }, 'out',
          () => { holder.style.opacity = 0; holder.style.clipPath = 'none'; S.ringOnly = 0; S.eyeA = 1; S.thread = 1; g.blink(); });
        return g; } };
    return g;
  }
  window.REEL = { PA, PARK, cam, box, place, cuts, grid, bolas, tween, esc };
})();
