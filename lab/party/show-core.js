/* THE SHOW's projector, shared by the stand and by a kept episode. A panel is a ground (an archive shot, looping, silent), figures
   (SAM cut-outs from other films, moving in place, lower on the screen is nearer), the speaker's own recorded voice, a bed of
   music, and an echo (an archival person saying a word of the line, after it). Panel, resolved:
   { text, dur, g: {v, th}, figs: [{id, x, y, s, flip, png, sp, sw, sh, fps}], voice: {u, dur} | null, bed: {u, t0} | null, echo: {u, t0, t1} | null }
   ShowCore.Stage(el)                 -> { show(panel), stop() }      ShowCore.play(E, stage, audios, hooks) -> stop()        */
(function (root) {
  const frames = new Map();
  function figEl(g) { const d = document.createElement('div'); d.className = 'sfig'; d.dataset.id = g.id; set(d, g);
    d.style.backgroundImage = `url("${g.png}")`; d.style.aspectRatio = (g.w || 1) + ' / ' + (g.h || 1);
    if (g.sp && g.sw) { const go = n => { if (n < 2) return; d.style.aspectRatio = g.sw + ' / ' + g.sh; d.style.backgroundImage = `url("${g.sp}")`; d.style.backgroundSize = n * 100 + '% 100%'; d.style.animation = `sspr ${(n / (g.fps || 6)).toFixed(2)}s steps(${n}, jump-none) infinite alternate`; };
      if (frames.has(g.sp)) go(frames.get(g.sp)); else { const im = new Image(); im.onload = () => { const n = Math.round(im.naturalWidth / (im.naturalHeight * g.sw / g.sh)); frames.set(g.sp, n); if (d.isConnected) go(n); }; im.src = g.sp; } }
    return d; }
  function set(d, g) { d.style.left = g.x * 100 + '%'; d.style.top = g.y * 100 + '%'; d.style.width = g.s * 100 + '%'; d.style.zIndex = 10 + Math.round(g.y * 100); d.classList.toggle('flip', !!g.flip); }
  function Stage(el) {
    el.classList.add('sstage'); el.innerHTML = '<video class="sg" muted playsinline loop preload="auto"></video><video class="sg" muted playsinline loop preload="auto"></video><div class="sfigs"></div>';
    const vids = [...el.querySelectorAll('video')], figs = el.querySelector('.sfigs'); let side = 0;
    function ground(g) { const on = vids[side]; if (!g) { vids.forEach(v => { v.classList.remove('on'); v.pause(); }); return; }
      if (on.dataset.u === g.v) { if (!on.classList.contains('on')) on.classList.add('on'); if (on.paused) on.play().catch(() => { }); return; }
      const nx = vids[1 - side]; nx.dataset.u = g.v; nx.poster = g.th || ''; nx.src = g.v; nx.play().catch(() => { });
      const swap = () => { nx.classList.add('on'); on.classList.remove('on'); setTimeout(() => { if (!on.classList.contains('on')) on.pause(); }, 500); };
      let done = false; const ok = () => { if (done) return; done = true; swap(); }; nx.addEventListener('playing', ok, { once: true }); setTimeout(ok, 900); side = 1 - side; }
    function dress(list) { const have = new Map([...figs.children].map(d => [d.dataset.id, d])), keep = new Set();
      (list || []).forEach(g => { const id = String(g.id); keep.add(id); const d = have.get(id); if (d && d.dataset.png === g.png) set(d, g); else { if (d) d.remove(); const n = figEl(g); n.dataset.png = g.png; figs.append(n); } });
      have.forEach((d, id) => { if (!keep.has(id)) d.remove(); }); }
    return { show(p) { ground(p && p.g); dress(p ? p.figs : []); }, dress, ground, stop() { vids.forEach(v => v.pause()); } };
  }
  // play an episode from panel `from`: every voice keeps its own time; the bed runs on beneath panels that share it, under the voice
  function play(E, st, A, h = {}) {
    let dead = false, i = h.from || 0; const tm = [], later = (f, ms) => tm.push(setTimeout(() => { if (!dead) f(); }, ms));
    const stopA = () => [A.voice, A.echo].forEach(a => { try { a.pause(); } catch (e) { } });
    function step() { if (dead) return; const p = E.panels[i]; if (!p) { end(); h.onEnd && h.onEnd(); return; }
      stopA(); st.show(p); h.onPanel && h.onPanel(i, p);
      const vd = p.voice ? p.voice.dur : 0, ed = p.echo ? Math.max(.4, p.echo.t1 - p.echo.t0) : 0;
      if (p.voice) { A.voice.src = p.voice.u; try { A.voice.currentTime = 0; } catch (e) { } A.voice.play().catch(() => { }); }
      if (p.bed) { if (A.bed.dataset.u !== p.bed.u) { A.bed.dataset.u = p.bed.u; A.bed.src = p.bed.u; A.bed.addEventListener('loadedmetadata', () => { try { A.bed.currentTime = p.bed.t0 || 0; } catch (e) { } }, { once: true }); }
        A.bed.volume = vd ? .22 : .55; A.bed.play().catch(() => { }); later(() => { A.bed.volume = .55; }, vd * 1000 + 200); }
      else { A.bed.pause(); A.bed.dataset.u = ''; }
      if (p.echo) later(() => { const a = A.echo; const go = () => { try { a.currentTime = p.echo.t0; } catch (e) { } a.play().catch(() => { }); };
        if (a.dataset.u !== p.echo.u) { a.dataset.u = p.echo.u; a.src = p.echo.u; a.addEventListener('loadedmetadata', go, { once: true }); } else go(); h.onCap && h.onCap(p.echo.x ? '“' + p.echo.x + '”' : '');
        later(() => a.pause(), ed * 1000 + 150); }, vd * 1000 + 250);
      h.onCap && h.onCap(p.text || '');
      later(() => { i++; step(); }, Math.max(2.6, vd + (ed ? ed + .45 : 0) + .8) * 1000); }
    function end() { dead = true; tm.forEach(clearTimeout); stopA(); try { A.bed.pause(); A.bed.dataset.u = ''; } catch (e) { } h.onCap && h.onCap(''); }
    step(); return end;
  }
  root.ShowCore = { Stage, play, figEl, set };
})(window);
