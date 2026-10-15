/* THE GUIDE · Bolas as the one who tells the story: the ring with two eyes, hanging on the red thread. It descends to a picture,
   moves between pictures, blinks when a film cuts (a machine pass) and winks when a reading is made. It never stands in for the
   picture and never covers one. Needs explain/marks.js.
     const g = GUIDE(el, K)            create inside a beat
     g.to(x, y, r, secs)               move (stage pixels, 1600 x 900); r is the ring's radius
     g.blink() / g.wink(secs) / g.look(dx, dy) / g.hide() */
(function () {
  window.GUIDE = function (el, K, o = {}) {
    const box = document.createElement('div'); box.className = 'guide';
    box.style.cssText = 'position:absolute;left:0;top:0;z-index:5;pointer-events:none;transition:transform 1s cubic-bezier(.45,.05,.25,1),opacity .6s;will-change:transform';
    const th = document.createElement('div'); th.style.cssText = 'position:absolute;left:50%;bottom:100%;width:3px;height:2400px;margin-left:-1.5px;background:#e0483a';
    const face = document.createElement('div'); box.append(th, face); el.appendChild(box);
    let r = o.r || 34, state = 'open', look = [0, 0], x = o.x ?? 800, y = o.y ?? -120;
    const draw = () => { face.innerHTML = MK.eye(state, r, { fill: '#0b0a09' }); const s = face.firstElementChild; if (s && (look[0] || look[1])) s.querySelectorAll('circle[cx],path').forEach(e => e.setAttribute('transform', `translate(${look[0] * r * .16},${look[1] * r * .16})`)); };
    const place = (secs) => { box.style.transitionDuration = (secs ?? 1) + 's'; box.style.transform = `translate(${x - r}px,${y - r}px)`; };
    draw(); place(0);
    const g = {
      to(nx, ny, nr, secs = 1) { x = nx; y = ny; if (nr && nr !== r) { r = nr; draw(); } place(secs); return g; },
      blink() { state = 'blink'; draw(); K.later(140, () => { state = 'open'; draw(); }); return g; },
      wink(secs = 1.1) { state = 'wink'; draw(); K.later(secs * 1000, () => { state = 'open'; draw(); }); return g; },
      look(dx, dy) { look = [dx, dy]; draw(); return g; },
      hide() { box.style.opacity = 0; return g; }, show() { box.style.opacity = 1; return g; }, el: box };
    return g;
  };
})();
