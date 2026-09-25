/* WAG · Tempest: make the WYGWYL film inside the Cutting Room, with WAG's own lego man, hands, sounds and parts.
 *
 * For the beat you are on, its best-ranked clips (lab/wygwyl/candidate-ranks.json) lie on the plate as real
 * WAG parts — 4×6 plates carrying the clip on top — so everything WAG can do to a part works on a candidate:
 * pinch it with a hand, drag it with the mouse, snap it, hear it. Put one on the SEAT pad at the back and it is
 * seated: it goes into WAG's cut at the beat's time, and the room moves to the next beat. The beats before and
 * after play on panels at the sides; the line hangs over the back wall. MOVE walks the lego man (WAG's performer),
 * LOOK turns the room. The clips are small same-origin loops (wygwyl/tempest/, 240×180, 3 s): the archive sends no
 * CORS headers, so its own files cannot be WebGL textures. Seats are shared with the cutting room floor.
 *     hand-butter.html?tempest=1        (or the ▣ button top-left)
 */
(() => {
  'use strict';
  const HERE = document.currentScript?.src || location.href;
  const U = p => new URL(p, HERE).href;
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } } };
  const T = { on: false, D: null, R: null, P: null, i: 0, seats: store.get('floor.seats', {}), parts: [], deco: [], vids: [], mv: { x: 0, y: 0 }, lk: { x: 0, y: 0 }, busy: false, server: false };
  const W = () => window.WagWorkshop?.world?.();
  const beat = () => T.D.beats[T.i];
  const PAD = { x: 0, z: -150, w: 200, d: 150 };
  const COL = { KEEP: 2, MAYBE: 14 };

  /* ---------- overlay: icons only ---------- */
  const css = document.createElement('style');
  css.textContent = `
  #tpBar{position:fixed;left:12px;top:64px;z-index:60;display:flex;gap:6px;align-items:center}
  #tpBar button{width:38px;height:38px;border-radius:8px;border:1px solid #2c383c;background:#101a1fdd;color:#e8eeeb;display:inline-flex;align-items:center;justify-content:center;padding:0;cursor:pointer}
  #tpBar button svg{width:19px;height:19px;stroke:currentColor;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
  #tpBar button.on{background:#c4f46a;color:#111;border-color:#c4f46a}
  #tpBar .n{min-width:48px;height:38px;border-radius:8px;background:#101a1fdd;border:1px solid #2c383c;color:#c4f46a;font:600 18px/38px ui-monospace,Menlo,monospace;text-align:center}
  #tpBar .ring{position:relative;width:38px;height:38px}#tpBar .ring svg{transform:rotate(-90deg)}
  #tpBar .ring span{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font:10px ui-monospace,monospace;color:#8e9a97}
  .tpStick{position:fixed;z-index:60;width:108px;height:108px;border-radius:50%;border:1px solid #3b5560;background:#0a1114cc;touch-action:none;display:none}
  .tpStick.show{display:block}
  .tpStick i{position:absolute;left:50%;top:50%;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:#1d2b31;border:1px solid #4a6670}
  .tpStick.act i{background:#c4f46a;border-color:#c4f46a}
  .tpStick b{position:absolute;bottom:-17px;left:0;right:0;text-align:center;font:10px ui-monospace,monospace;letter-spacing:.14em;color:#8e9a97}
  .tpHide{display:none!important}`;
  document.head.appendChild(css);
  const ic = d => `<svg viewBox="0 0 24 24"><path d="${d}"/></svg>`;
  const bar = document.createElement('div'); bar.id = 'tpBar';
  bar.innerHTML = `<button id="tpOn" title="Tempest: the scene's best clips on the plate">${ic('M3 3h18v14H3zM8 21h8M12 17v4')}</button>
    <span class="tpHide" id="tpUI" style="display:flex;gap:6px;align-items:center">
    <button id="tpPrev" title="beat before ( [ )">${ic('M15 5l-7 7 7 7M6 5v14')}</button><span class="n" id="tpN">–</span><button id="tpNext" title="beat after ( ] )">${ic('M9 5l7 7-7 7M18 5v14')}</button>
    <button id="tpBest" title="seat the best (B)">${ic('M12 3l2.8 5.8 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.3l1.1-6.2L3 9.7l6.2-.9z')}</button>
    <span class="ring" title="beats seated"><svg viewBox="0 0 38 38" width="38" height="38"><circle cx="19" cy="19" r="15" stroke="#23343c" stroke-width="4" fill="none"/><circle id="tpRing" cx="19" cy="19" r="15" stroke="#c4f46a" stroke-width="4" fill="none" stroke-dasharray="94.2" stroke-dashoffset="94.2"/></svg><span id="tpRingN">0</span></span></span>`;
  document.body.appendChild(bar);
  const stick = (side, label) => { const s = document.createElement('div'); s.className = 'tpStick'; s.innerHTML = `<i></i><b>${label}</b>`; document.body.appendChild(s); s.dataset.side = side; return s; };
  const SM = stick('l', 'MOVE'), SL = stick('r', 'LOOK');
  function placeSticks() {
    const v = document.getElementById('view')?.getBoundingClientRect(); if (!v) return;
    SM.style.left = (v.left + 18) + 'px'; SM.style.top = (v.bottom - 140) + 'px';
    SL.style.left = (v.right - 126) + 'px'; SL.style.top = (v.bottom - 140) + 'px';
  }
  function drive(el, out) {
    const k = el.querySelector('i'); let id = null, r;
    el.addEventListener('pointerdown', e => { id = e.pointerId; r = el.getBoundingClientRect(); el.setPointerCapture(id); el.classList.add('act'); upd(e); e.stopPropagation(); });
    el.addEventListener('pointermove', e => { if (e.pointerId === id) upd(e); });
    const end = () => { id = null; el.classList.remove('act'); out.x = out.y = 0; k.style.transform = ''; };
    el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    function upd(e) { let x = (e.clientX - r.left - r.width / 2) / (r.width / 2 - 18), y = (e.clientY - r.top - r.height / 2) / (r.height / 2 - 18); const L = Math.hypot(x, y); if (L > 1) { x /= L; y /= L; } out.x = x; out.y = -y; k.style.transform = `translate(${x * 32}px,${y * 32}px)`; }
  }
  drive(SM, T.mv); drive(SL, T.lk);

  /* ---------- video textures ---------- */
  function vtex(id) {
    const v = document.createElement('video'); v.src = U(`../wygwyl/tempest/${id}.mp4`); v.muted = true; v.loop = true; v.playsInline = true; v.crossOrigin = 'anonymous'; v.play().catch(() => {});
    T.vids.push(v); const t = new THREE.VideoTexture(v); t.minFilter = THREE.LinearFilter; return t;
  }
  function textTex(lines, w = 1024, h = 160) {
    const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d');
    g.fillStyle = '#0a1114'; g.fillRect(0, 0, w, h); g.fillStyle = '#c4f46a'; g.font = '600 64px ui-monospace,Menlo,monospace'; g.fillText(lines[0], 24, 96);
    g.fillStyle = '#d6e6c7'; g.font = '30px ui-monospace,Menlo,monospace'; const x0 = 24 + g.measureText(lines[0]).width + 60;
    g.font = '30px ui-monospace,Menlo,monospace'; wrap(g, lines[1] || '', x0, 58, w - x0 - 24, 38, 3);
    return new THREE.CanvasTexture(c);
  }
  function wrap(g, text, x, y, maxW, lh, maxL) { const words = text.split(/\s+/); let line = '', n = 0; for (const w of words) { const t = line ? line + ' ' + w : w; if (g.measureText(t).width > maxW && line) { g.fillText(line, x, y); y += lh; line = w; if (++n >= maxL - 1) { line = line + '…'; break; } } else line = t; } if (line) g.fillText(line, x, y); }
  function numTex(n, color) { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'); g.fillStyle = color; g.beginPath(); g.arc(32, 32, 30, 0, 7); g.fill(); g.fillStyle = '#111'; g.font = '600 38px ui-monospace,Menlo,monospace'; g.textAlign = 'center'; g.fillText(n, 32, 45); return new THREE.CanvasTexture(c); }

  /* ---------- the room for one beat ---------- */
  const cueFor = b => T.D.cues.filter(c => c.t1 > b.start && c.t0 < b.end && c.text).map(c => c.text).join(' ') || b.title;
  const shotFor = b => { const s = T.seats[b.id]; if (s && T.P.files.includes(s.id)) return s.id; return T.P.beats[b.id]?.suite?.id; };
  function clear() {
    const w = W(); if (!w) return;
    w.remove(T.parts.map(p => p.id)); T.parts = [];
    T.deco.forEach(o => { o.parent?.remove(o); o.traverse?.(m => { m.material?.map?.dispose?.(); m.material?.dispose?.(); m.geometry?.dispose?.(); }); }); T.deco = [];
    T.vids.forEach(v => { v.pause(); v.removeAttribute('src'); v.load(); }); T.vids = [];
  }
  function lay() {
    const w = W(); if (!w) return; clear();
    const b = beat(), cands = T.P.beats[b.id]?.cands || [], seat = T.seats[b.id];
    // candidates: real 4×6 plates, the clip on top, best at the front-left
    const spots = [[-230, 120], [0, 120], [230, 120], [-230, 290], [0, 290], [230, 290]];
    cands.forEach((c, k) => {
      if (!T.P.files.includes(c.id)) return;
      const [x, z] = spots[k]; const id = w.nextId();
      const p = w.create({ id, part: '3032', color: COL[c.verdict] ?? 71, x, y: 0, z, r: 0 });
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(176, 132), new THREE.MeshBasicMaterial({ map: vtex(c.id), side: THREE.DoubleSide }));
      pl.material.depthTest = false; pl.renderOrder = 20; pl.rotation.x = -Math.PI / 2; pl.position.y = 22; p.mesh.add(pl);   // WAG's part pass hides anything this close to a plate: draw the clip last
      const badge = new THREE.Mesh(new THREE.PlaneGeometry(34, 34), new THREE.MeshBasicMaterial({ map: numTex(k + 1, c.verdict === 'KEEP' ? '#c4f46a' : '#e3a600'), transparent: true }));
      badge.material.depthTest = false; badge.renderOrder = 21; badge.rotation.x = -Math.PI / 2; badge.position.set(-72, 23, -50); p.mesh.add(badge);
      if (seat && seat.id === c.id) { const ring = new THREE.Mesh(new THREE.RingGeometry(96, 104, 48), new THREE.MeshBasicMaterial({ color: 0xc4f46a, side: THREE.DoubleSide })); ring.material.depthTest = false; ring.renderOrder = 21; ring.rotation.x = -Math.PI / 2; ring.position.y = 23; p.mesh.add(ring); }
      p.tempest = c; T.parts.push(p);
    });
    // the SEAT pad at the back: put a clip here to seat it
    const g = new THREE.Group(), padG = new THREE.Group();
    const rect = new THREE.Mesh(new THREE.PlaneGeometry(PAD.w, PAD.d), new THREE.MeshBasicMaterial({ color: 0xc4f46a, transparent: true, opacity: .16, side: THREE.DoubleSide }));
    rect.rotation.x = -Math.PI / 2; rect.position.set(PAD.x, 1, PAD.z); padG.add(rect);
    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(PAD.w, PAD.d)), new THREE.LineBasicMaterial({ color: 0xc4f46a }));
    edge.rotation.x = -Math.PI / 2; edge.position.set(PAD.x, 2, PAD.z); padG.add(edge);
    const arrow = new THREE.Mesh(new THREE.ConeGeometry(16, 34, 4), new THREE.MeshBasicMaterial({ color: 0xc4f46a })); arrow.rotation.x = Math.PI; arrow.position.set(PAD.x, 60, PAD.z); padG.add(arrow); T.arrow = arrow;
    // the line over the back wall
    const line = new THREE.Mesh(new THREE.PlaneGeometry(640, 100), new THREE.MeshBasicMaterial({ map: textTex([String(b.id), cueFor(b)]), transparent: true }));
    line.position.set(0, 470, -430); g.add(line);
    // the beats before and after, playing, on the side panels
    [[-1, -330], [1, 330]].forEach(([d, x]) => {
      const nb = T.D.beats[T.i + d]; if (!nb) return; const sid = shotFor(nb); if (!sid) return;
      const panel = new THREE.Group();
      const frame = new THREE.Mesh(new THREE.PlaneGeometry(312, 238), new THREE.MeshBasicMaterial({ color: T.seats[nb.id] ? 0xc4f46a : 0x05090b }));
      const pic = new THREE.Mesh(new THREE.PlaneGeometry(296, 222), new THREE.MeshBasicMaterial({ map: vtex(sid), color: T.seats[nb.id] ? 0xffffff : 0x777777 })); pic.position.z = 1;
      const tag = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshBasicMaterial({ map: numTex(nb.id, T.seats[nb.id] ? '#c4f46a' : '#8e9a97'), transparent: true })); tag.position.set(d < 0 ? -120 : 120, 95, 2);
      panel.add(frame, pic, tag); panel.position.set(x, 210, -260); panel.rotation.y = d < 0 ? Math.PI / 4 : -Math.PI / 4;
      panel.userData.tempestStep = d; g.add(panel);
    });
    w.scene.add(g); T.deco.push(g);
    window.ButterPerformer?.state?.rig?.figure?.traverse?.(o => { if (o.isMesh) o.renderOrder = 30; });   // the lego man draws after the clips, so he stands in front of them
    const frameObj = w.scene.getObjectByName('construction-frame') || w.scene; frameObj.add(padG); T.deco.push(padG);
    w.refresh();
    document.getElementById('tpN').textContent = b.id;
    ring();
    try { history.replaceState(history.state, '', location.pathname + location.search.replace(/([?&])tb=\d+/, '') + (location.search.includes('?') ? '&' : '?') + 'tb=' + b.id); } catch (e) { /* file: */ }
  }
  function ring() { const n = T.D.beats.filter(b => T.seats[b.id]).length; document.getElementById('tpRing').style.strokeDashoffset = 94.2 * (1 - n / T.D.beats.length); document.getElementById('tpRingN').textContent = n; }
  function go(i) { if (i < 0 || i >= T.D.beats.length) return; T.i = i; lay(); }

  /* ---------- seating: into the shared seats and into WAG's cut at the beat's time ---------- */
  async function seat(c) {
    if (T.busy) return; const b = beat(); c = c || (T.P.beats[b.id]?.cands || [])[0]; if (!c) return;
    T.busy = true;
    T.seats[b.id] = { id: c.id, title: c.title, year: c.year, thumb: c.thumb, video: c.video, in: c.in || 0, score: c.score, fit: c.fit };
    store.set('floor.seats', T.seats);
    try { W()?.feedback?.('check'); } catch (e) { /* sound optional */ }
    const media = T.server ? `/media/${c.id}.mp4` : U(`../wygwyl/tempest/${c.id}.mp4`), piece = T.server ? Math.min(b.end - b.start, 30) : 3;
    const items = []; for (let t = b.start; t < b.end - .5 && items.length < (T.server ? 1 : 4); t += piece)
      items.push({ shot: c.id, title: c.title, year: c.year, n: b.codes?.[0] || null, note: `WYGWYL #${b.id} seated`, a: (T.server ? c.in || 0 : 0), b: (T.server ? (c.in || 0) : 0) + Math.min(piece, b.end - t), media, place: { t } });
    window.CineosisBridge?.take({ id: 'tempest-' + b.id, title: `WYGWYL #${b.id} · ${c.title}`, layout: 'sequence', span: 1800, items });
    setTimeout(() => { T.busy = false; go(T.i + 1); }, 700);
  }

  /* ---------- the loop: a candidate put on the pad is seated; MOVE walks the lego man; LOOK turns the room ---------- */
  let last = performance.now(), padT = null;
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    if (T.on && W()) {
      const w = W();
      if (T.arrow) T.arrow.position.y = 60 + Math.sin(now / 300) * 8;
      if (!w.held()) {
        const on = T.parts.find(p => Math.abs(p.x - PAD.x) < PAD.w / 2 && Math.abs(p.z - PAD.z) < PAD.d / 2);
        if (on && !padT) padT = setTimeout(() => { padT = null; const still = T.parts.find(p => p === on && Math.abs(p.x - PAD.x) < PAD.w / 2 && Math.abs(p.z - PAD.z) < PAD.d / 2); if (still && !W().held()) seat(still.tempest); }, 350);
      }
      const st = window.ButterStage?.state?.();
      const SR = window.ButterSpatialRuntime;
      if (SR?.spinPlate) {
        if (T.lk.x) { if (T.spin == null) T.spin = SR.plate?.rotation?.y || 0; T.spin += T.lk.x * 1.8 * dt; SR.spinPlate(T.spin); T.spinning = true; }
        else if (T.spinning) { T.spinning = false; T.spin = Math.round(T.spin / (Math.PI / 2)) * Math.PI / 2; SR.spinPlate(T.spin, true); try { W()?.feedback?.('tick'); } catch (e) { /* sound optional */ } }
      }
      const P = window.ButterPerformer, ps = P?.state;
      if ((T.mv.x || T.mv.y) && ps?.on && ps.rig) {
        const yaw = st?.yaw || 0, fx = -Math.sin(yaw), fz = -Math.cos(yaw), rx = Math.cos(yaw), rz = -Math.sin(yaw);
        const dx = fx * T.mv.y + rx * T.mv.x, dz = fz * T.mv.y + rz * T.mv.x, L = Math.hypot(dx, dz) || 1;
        P.command('walk there', new THREE.Vector3(ps.rig.pos.x + dx / L * 60, 0, ps.rig.pos.z + dz / L * 60));
      }
    }
    requestAnimationFrame(frame);
  }

  /* clicking a side panel steps the beat */
  function panelClick(e) {
    if (!T.on || !W()) return; const view = document.getElementById('view'); if (e.target !== view) return;
    const r = view.getBoundingClientRect(), m = new THREE.Vector2((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
    const ray = new THREE.Raycaster(); ray.setFromCamera(m, W().camera);
    const hit = ray.intersectObjects(T.deco, true).find(h => { let o = h.object; while (o && o.userData.tempestStep == null) o = o.parent; return o; });
    if (hit) { let o = hit.object; while (o.userData.tempestStep == null) o = o.parent; go(T.i + o.userData.tempestStep); e.stopPropagation(); }
  }

  async function start() {
    if (T.on) { T.on = false; clear(); document.getElementById('tpUI').classList.add('tpHide'); document.getElementById('tpOn').classList.remove('on'); SM.classList.remove('show'); SL.classList.remove('show'); return; }
    for (let k = 0; k < 300 && !(W() && window.WagWorkshop.ready?.() && window.ButterCut?.state?.().booted); k++) await new Promise(r => setTimeout(r, 100));
    if (!T.D) {
      [T.D, T.P] = await Promise.all([fetch(U('../wygwyl/collage-data.json')).then(r => r.json()), fetch(U('../wygwyl/tempest/pack.json')).then(r => r.json())]);
      T.server = !/github\.io$/.test(location.hostname) && await fetch('/api/assignments', { signal: AbortSignal.timeout(1500) }).then(r => r.ok).catch(() => false);
      const q = new URLSearchParams(location.search), tb = +q.get('tb'), first = T.D.beats.findIndex(b => !T.seats[b.id]);
      T.i = tb ? Math.max(0, T.D.beats.findIndex(b => b.id === tb)) : Math.max(0, first);
    }
    T.on = true; document.getElementById('tpUI').classList.remove('tpHide'); document.getElementById('tpOn').classList.add('on'); SM.classList.add('show'); SL.classList.add('show'); placeSticks();
    lay();
  }
  document.getElementById('tpOn').onclick = start;
  document.getElementById('tpPrev').onclick = () => go(T.i - 1);
  document.getElementById('tpNext').onclick = () => go(T.i + 1);
  document.getElementById('tpBest').onclick = () => seat();
  addEventListener('keydown', e => {
    if (!T.on || e.metaKey || e.ctrlKey || e.target.closest?.('input,textarea,select')) return;
    if (e.key === '[') go(T.i - 1); else if (e.key === ']') go(T.i + 1); else if (e.key === 'b' || e.key === 'B') seat(); else return;
    e.preventDefault(); e.stopPropagation();
  }, true);
  addEventListener('pointerdown', panelClick, true);
  addEventListener('resize', placeSticks);
  requestAnimationFrame(frame);
  if (/[?&]tempest=1/.test(location.search)) start();
  window.WagTempest = { start, go, seat, state: () => ({ on: T.on, beat: T.D && beat().id, parts: T.parts.map(p => [p.id, Math.round(p.x), Math.round(p.z)]), seats: Object.keys(T.seats).length }) };
})();
