/* WAG · Tempest: every clip is a LEGO brick, and the film is what you build with them.
 *
 * At the back of the plate a row of five dark sockets is a page of the film: one socket per beat, printed with its
 * number. A seated beat is a video brick standing on its socket, playing, so reading along the row is watching the
 * film. At the lego man's feet lie the current beat's best clips (lab/wygwyl/candidate-ranks.json) as video bricks.
 * Lay one on a socket (pinch it, drag it, snap it: WAG's own hands, mouse, seating and sounds) and that beat is
 * seated, the clip placed in WAG's cut at the beat's time. Seating the current beat moves on to the next one.
 * MOVE walks the lego man: the socket he stands in front of becomes the current beat and its bricks come to him;
 * walk off either end of the row for the next or previous page. LOOK turns the plate. No panels, no menus.
 * The bricks carry small same-origin loops (wygwyl/tempest/): the archive sends no CORS headers, so WebGL cannot
 * draw its own files. Seats are shared with the cutting room floor.   [ ] beat · B seat the best
 *     hand-butter.html?tempest=1        (or the ▣ toggle)
 */
(() => {
  'use strict';
  if (window.__noWebGL) return;
  const HERE = document.currentScript?.src || location.href;
  const U = p => new URL(p, HERE).href;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } } };
  const T = { on: false, D: null, P: null, i: 0, seats: store.get('floor.seats', {}), sockets: [], bricks: [], vids: new Map(), mv: { x: 0, y: 0 }, lk: { x: 0, y: 0 }, busy: false, server: false, near: null };
  const W = () => window.WagWorkshop?.world?.();
  const beat = () => T.D.beats[T.i];
  const ROWZ = -340, STEP = 150, BRICK = '3032', PAGE = 5;
  const COL = { KEEP: 2, MAYBE: 14 };

  /* ---------- one toggle and two sticks ---------- */
  const css = document.createElement('style');
  css.textContent = `
  #tpOn{position:fixed;left:12px;top:64px;z-index:60;width:40px;height:40px;border-radius:9px;border:1px solid #2c383c;background:#101a1fdd;color:#e8eeeb;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0}
  #tpOn svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
  #tpOn.on{background:#c4f46a;color:#111;border-color:#c4f46a}
  .tpStick{position:fixed;z-index:60;width:108px;height:108px;border-radius:50%;border:1px solid #3b5560;background:#0a1114cc;touch-action:none;display:none}
  .tpStick.show{display:block}
  .tpStick i{position:absolute;left:50%;top:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:#1d2b31;border:1px solid #4a6670}
  .tpStick.act i{background:#c4f46a;border-color:#c4f46a}`;
  document.head.appendChild(css);
  const on = document.createElement('button'); on.id = 'tpOn'; on.title = 'Tempest: build the film with video bricks';
  on.innerHTML = '<svg viewBox="0 0 24 24"><path d="M3 10h18v9H3zM6 10V6h3v4M15 10V6h3v4"/></svg>'; document.body.appendChild(on);
  const stick = t => { const s = document.createElement('div'); s.className = 'tpStick'; s.title = t; s.innerHTML = '<i></i>'; document.body.appendChild(s); return s; };
  const SM = stick('MOVE: walk the lego man along the film'), SL = stick('LOOK: turn the plate');
  function placeSticks() { const v = document.getElementById('view')?.getBoundingClientRect(); if (!v) return; SM.style.left = (v.left + 18) + 'px'; SM.style.top = (v.bottom - 128) + 'px'; SL.style.left = (v.right - 126) + 'px'; SL.style.top = (v.bottom - 128) + 'px'; }
  function drive(el, out) {
    const k = el.querySelector('i'); let id = null, r;
    el.addEventListener('pointerdown', e => { id = e.pointerId; r = el.getBoundingClientRect(); el.setPointerCapture(id); el.classList.add('act'); upd(e); e.stopPropagation(); });
    el.addEventListener('pointermove', e => { if (e.pointerId === id) upd(e); });
    const end = () => { id = null; el.classList.remove('act'); out.x = out.y = 0; k.style.transform = ''; };
    el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    function upd(e) { let x = (e.clientX - r.left - r.width / 2) / (r.width / 2 - 18), y = (e.clientY - r.top - r.height / 2) / (r.height / 2 - 18); const L = Math.hypot(x, y); if (L > 1) { x /= L; y /= L; } out.x = x; out.y = -y; k.style.transform = `translate(${x * 32}px,${y * 32}px)`; }
  }
  drive(SM, T.mv); drive(SL, T.lk);

  /* ---------- textures ---------- */
  function vtex(id) {
    let v = T.vids.get(id);
    if (!v) { v = document.createElement('video'); v.src = U(`../wygwyl/tempest/${id}.mp4`); v.muted = true; v.loop = true; v.playsInline = true; v.crossOrigin = 'anonymous'; v.play().catch(() => {}); T.vids.set(id, v); }
    const t = new THREE.VideoTexture(v); t.minFilter = THREE.LinearFilter; return t;
  }
  function numTex(n, fg, bg) { const c = document.createElement('canvas'); c.width = 128; c.height = 64; const g = c.getContext('2d'); g.fillStyle = bg; g.fillRect(0, 0, 128, 64); g.fillStyle = fg; g.font = '600 44px ui-monospace,Menlo,monospace'; g.textAlign = 'center'; g.fillText(n, 64, 48); return new THREE.CanvasTexture(c); }
  function flat(w, h, mat, y, x = 0, z = 0, order = 20) {   // WAG's part pass hides anything this close to a plate: draw it on top
    mat.depthTest = false; mat.side = THREE.DoubleSide;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); m.renderOrder = order; return m;
  }

  /* WAG saves its scene: remember which parts are Tempest's, so a reload never finds last session's bricks in the way */
  function mine(p) { const ids = store.get('tempest.parts', []); ids.push(p.id); store.set('tempest.parts', ids); return p; }
  function sweep() {
    const w = W(), ids = new Set(store.get('tempest.parts', [])); if (!w) return;
    // once: the earlier Tempest (≤ v8) did not keep a list; its candidate plates sit in the front half of the plate
    const old = store.get('tempest.swept', 0) < 9 ? p => p.part === BRICK && /^p\d+$/.test(p.id) && [2, 14, 71].includes(p.color) && p.z > 90 && Math.abs(p.x) < 250 : () => false;
    w.remove(w.parts.filter(p => ids.has(p.id) || old(p)).map(p => p.id)); store.set('tempest.parts', []); store.set('tempest.swept', 9);
  }

  /* ---------- a video brick: a real WAG part carrying its clip ---------- */
  function videoBrick(w, c, x, z, y = 0) {
    const p = mine(w.create({ id: w.nextId(), part: BRICK, color: COL[c.verdict] ?? 71, x, y, z, r: 0 }));
    p.mesh.add(flat(112, 84, new THREE.MeshBasicMaterial({ map: vtex(c.id) }), 22));
    p.tempest = c; return p;
  }

  /* ---------- the page of the film around the current beat ---------- */
  function clear() {
    const w = W(); if (!w) return;
    w.remove([...T.sockets, ...T.bricks].map(p => p.id)); T.sockets = []; T.bricks = []; sweep();
    T.vids.forEach(v => { v.pause(); v.removeAttribute('src'); v.load(); }); T.vids.clear();
  }
  const pageOf = i => Math.floor(i / PAGE) * PAGE;
  function lay() {
    const w = W(); if (!w) return; clear();
    const b = beat(), lo = pageOf(T.i);
    for (let k = 0; k < PAGE && lo + k < T.D.beats.length; k++) {
      const x = (k - 2) * STEP, bb = T.D.beats[lo + k], cur = lo + k === T.i;
      const s = mine(w.create({ id: w.nextId(), part: BRICK, color: cur ? 15 : 0, x, y: 0, z: ROWZ, r: 0 }));
      s.mesh.add(flat(46, 23, new THREE.MeshBasicMaterial({ map: numTex(bb.id, cur ? '#111' : '#e8eeeb', cur ? '#c4f46a' : '#23343c') }), 22, 0, -62, 21));
      s.socketFor = bb.id; s.idx = lo + k; T.sockets.push(s);
      const seat = T.seats[bb.id];
      if (seat && T.P.files.includes(seat.id)) { const p = videoBrick(w, { ...seat, verdict: 'KEEP' }, x, ROWZ, 8); p.seatedFor = bb.id; T.bricks.push(p); }
    }
    const cands = (T.P.beats[b.id]?.cands || []).filter(c => T.P.files.includes(c.id) && T.seats[b.id]?.id !== c.id);
    const spots = [[-230, 130], [0, 130], [230, 130], [-230, 280], [0, 280], [230, 280]];   // clear of WAG's own scene (z 40)
    cands.slice(0, 6).forEach((c, k) => T.bricks.push(videoBrick(w, c, spots[k][0], spots[k][1])));
    T.near = nearest();
    w.refresh();
    try { const q = new URLSearchParams(location.search); q.set('tb', b.id); history.replaceState(history.state, '', location.pathname + '?' + q); } catch (e) { /* file: */ }
  }
  function go(i) { if (i < 0 || i >= T.D.beats.length) return; T.i = i; lay(); }
  function nearest() {   // which socket the lego man stands in front of; 'prev'/'next' off either end of the row
    const r = window.ButterPerformer?.state?.rig; if (!r || r.pos.z > ROWZ + 170) return null;
    const k = Math.round(r.pos.x / STEP) + 2;
    return k < 0 ? 'prev' : k >= T.sockets.length ? 'next' : T.sockets[k].idx;
  }

  /* ---------- seating: a brick laid on a socket ---------- */
  function seat(bb, c, brick) {
    T.seats[bb.id] = { id: c.id, title: c.title, year: c.year, thumb: c.thumb, video: c.video, in: c.in || 0, score: c.score, fit: c.fit };
    store.set('floor.seats', T.seats);
    try { W()?.feedback?.('check'); } catch (e) { /* sound optional */ }
    const w = W(), old = T.bricks.find(p => p.seatedFor === bb.id && p !== brick);
    if (old) { w.remove([old.id]); T.bricks = T.bricks.filter(p => p !== old); w.refresh(); }
    brick.seatedFor = bb.id;
    const media = T.server ? `/media/${c.id}.mp4` : U(`../wygwyl/tempest/${c.id}.mp4`), piece = T.server ? Math.min(bb.end - bb.start, 30) : 3, items = [];
    for (let t = bb.start; t < bb.end - .5 && items.length < (T.server ? 1 : 4); t += piece)
      items.push({ shot: c.id, title: c.title, year: c.year, n: bb.codes?.[0] || null, note: `WYGWYL #${bb.id}`, a: T.server ? c.in || 0 : 0, b: (T.server ? c.in || 0 : 0) + Math.min(piece, bb.end - t), media, place: { t } });
    window.CineosisBridge?.take({ id: 'tempest-' + bb.id, title: `WYGWYL #${bb.id} · ${c.title}`, layout: 'sequence', span: 1800, items });
    if (bb.id === beat().id && T.i < T.D.beats.length - 1) { T.busy = true; setTimeout(() => { T.busy = false; go(T.i + 1); }, 900); }
  }
  const beatById = id => T.D.beats.find(b => b.id === id);
  function seatBest() { const p = T.bricks.find(q => !q.seatedFor); if (p) seat(beat(), p.tempest, p); }

  /* ---------- the loop ---------- */
  let last = performance.now(); const dwell = new Map();
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    const w = T.on && W();
    if (w && !T.busy) {
      // a brick at rest on a socket seats that beat
      if (!w.held()) for (const p of T.bricks) {
        if (p.seatedFor) continue;
        const s = T.sockets.find(s => Math.abs(p.x - s.x) < 70 && Math.abs(p.z - s.z) < 60);
        if (!s) { dwell.delete(p); continue; }
        if (!dwell.has(p)) dwell.set(p, now);
        if (now - dwell.get(p) > 300) { dwell.delete(p); p.x = s.x; p.z = s.z; p.y = 8; w.sync(p); w.refresh(); seat(beatById(s.socketFor), p.tempest, p); break; }
      }
      // MOVE walks the lego man; the socket he stands in front of becomes the current beat
      const P = window.ButterPerformer, ps = P?.state;
      if ((T.mv.x || T.mv.y) && ps?.on && ps.rig) {
        const dx = T.mv.x, dz = -T.mv.y, L = Math.hypot(dx, dz) || 1;
        P.command('walk there', new THREE.Vector3(ps.rig.pos.x + dx / L * 60, 0, ps.rig.pos.z + dz / L * 60));
      }
      const n = nearest();
      if (n !== T.near && !w.held()) {
        T.near = n;
        if (n === 'prev' && pageOf(T.i) > 0) go(pageOf(T.i) - 1);
        else if (n === 'next' && pageOf(T.i) + PAGE < T.D.beats.length) go(pageOf(T.i) + PAGE);
        else if (typeof n === 'number' && n !== T.i) { go(n); try { w.feedback?.('tick'); } catch (e) { /* sound optional */ } }
      }
      // LOOK spins the plate, a quarter turn on release (WAG's camera is fixed; the plate turns)
      const SR = window.ButterSpatialRuntime;
      if (SR?.spinPlate) {
        if (T.lk.x) { if (T.spin == null) T.spin = SR.plate?.rotation?.y || 0; T.spin += T.lk.x * 1.8 * dt; SR.spinPlate(T.spin); T.spinning = true; }
        else if (T.spinning) { T.spinning = false; T.spin = Math.round(T.spin / (Math.PI / 2)) * Math.PI / 2; SR.spinPlate(T.spin, true); try { w.feedback?.('tick'); } catch (e) { /* sound optional */ } }
      }
    }
    requestAnimationFrame(frame);
  }

  async function start() {
    if (T.on) { T.on = false; clear(); W()?.refresh(); on.classList.remove('on'); SM.classList.remove('show'); SL.classList.remove('show'); return; }
    for (let k = 0; k < 300 && !(W() && window.WagWorkshop.ready?.() && window.ButterCut?.state?.().booted); k++) await new Promise(r => setTimeout(r, 100));
    if (!W()) return;
    sweep();
    if (!T.D) {
      [T.D, T.P] = await Promise.all([fetch(U('../wygwyl/collage-data.json')).then(r => r.json()), fetch(U('../wygwyl/tempest/pack.json')).then(r => r.json())]);
      T.server = !/github\.io$/.test(location.hostname) && await fetch('/api/assignments', { signal: AbortSignal.timeout(1500) }).then(r => r.ok).catch(() => false);
      const tb = +new URLSearchParams(location.search).get('tb'), first = T.D.beats.findIndex(b => !T.seats[b.id]);
      T.i = tb ? Math.max(0, T.D.beats.findIndex(b => b.id === tb)) : Math.max(0, first);
    }
    window.ButterPerformer?.state?.rig?.figure?.traverse?.(o => { if (o.isMesh) o.renderOrder = 30; });   // the lego man stands in front of the clips
    T.on = true; on.classList.add('on'); SM.classList.add('show'); SL.classList.add('show'); placeSticks();
    lay();
  }
  on.onclick = start;
  addEventListener('keydown', e => {
    if (!T.on || e.metaKey || e.ctrlKey || e.target.closest?.('input,textarea,select')) return;
    if (e.key === '[') go(T.i - 1); else if (e.key === ']') go(T.i + 1); else if (e.key === 'b' || e.key === 'B') seatBest(); else return;
    e.preventDefault(); e.stopPropagation();
  }, true);
  addEventListener('resize', placeSticks);
  requestAnimationFrame(frame);
  if (/[?&]tempest=1/.test(location.search)) start();
  window.WagTempest = { start, go, seatBest, state: () => ({ on: T.on, beat: T.D && beat().id, near: T.near, sockets: T.sockets.map(s => [s.socketFor, Math.round(s.x)]), bricks: T.bricks.map(p => [p.id, Math.round(p.x), Math.round(p.z), p.seatedFor || null]), seats: Object.keys(T.seats).length }) };
})();
