/* CINEOSIS EPISODES · the shared player. An episode page defines EPISODE = { data: [urls], cues: [score cue names], build(D, B, K) }
   and loads explain/film.css + this file. B(chapter, seconds, html(), after(el), {voice}) adds a scene; K is the kit below.
   One line of type at a time (K.line), moving pictures first, the project's own sound when it carries meaning (K.scene plays a
   scene's audio with its pictures cut by time; the score ducks under it). Keys: space pause, ← → scenes; chapters on the bar. */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const fmt = n => Number(n).toLocaleString('en-US');
  let beats = [], chapters = [], cur = -1, timer = 0, paused = false, sound = true, tok = 0, t0 = 0, left = 0;
  const stage = $('#stage'), score = $('#score'), voice = $('#voice');
  const duck = on => { score.volume = sound ? (on ? .05 : .28) : 0; };
  const later = (ms, f) => { const my = tok; setTimeout(() => { if (my === tok) f(); }, ms); };
  const raf = f => { const my = tok, t = performance.now(); const go = () => { if (my !== tok) return; if (f((performance.now() - t) / 1000) !== false) requestAnimationFrame(go); }; go(); };
  const line = (ls, sm = '', gap = 2.2) => `<div class="line">${ls.map((l, i) => `<span style="animation-delay:${.4 + i * gap}s">${l}</span>`).join('')}${sm ? `<small style="animation-delay:${.6 + ls.length * gap}s">${sm}</small>` : ''}</div>`;
  function startVideos(el) { el.querySelectorAll('video[data-src]').forEach(v => { v.src = v.dataset.src; if (v.dataset.end) v.addEventListener('timeupdate', () => { if (v.currentTime > +v.dataset.end) v.currentTime = +v.dataset.t; }); v.addEventListener('loadedmetadata', () => { try { v.currentTime = +v.dataset.t || 0; } catch (e) { } if (v.dataset.snd && sound) { v.muted = false; v.volume = 1; } v.play().catch(() => { v.muted = true; v.play().catch(() => { }); }); }, { once: true }); }); }
  function typeIn(el, text, cps = 26) { const my = tok; let i = 0; const step = () => { if (my !== tok || !el) return; el.textContent = text.slice(0, ++i); if (i < text.length) setTimeout(step, 1000 / cps); }; step(); }
  /* a scene of one of our films: its audio from a to b, its pictures switched by the scene's own cut list, subtitles from its lines */
  function scene(el, sc, a, b, subs) {
    const box = el.querySelector('.scn'), vs = [0, 1].map(() => { const v = document.createElement('video'); v.muted = true; v.playsInline = true; v.className = 'full'; v.style.opacity = 0; box.appendChild(v); return v; });
    const pics = sc.pics.slice().sort((x, y) => x.sw - y.sw), at = t => { let k = 0; pics.forEach((p, i) => { if (p.sw <= t) k = i; }); return k; };
    let shown = -1, front = 0; const load = (v, i, t) => { const p = pics[i]; if (!p) return; if (v.dataset.k != i) { v.dataset.k = i; v.src = p.video; } const go = () => { try { v.currentTime = p.in + Math.max(0, t - p.sw) * (p.rate || 1); } catch (e) { } }; if (v.readyState >= 1) go(); else v.addEventListener('loadedmetadata', go, { once: true }); };
    voice.src = sc.audio; voice.addEventListener('loadedmetadata', () => { voice.currentTime = a; if (sound && !paused) voice.play().catch(() => { }); }, { once: true }); duck(true);
    const sub = el.querySelector('.subl');
    raf(() => { const t = voice.currentTime || a, k = at(t);
      if (k !== shown) { const v = vs[1 - front]; load(v, k, t); v.play().catch(() => { }); v.style.opacity = 1; vs[front].style.opacity = 0; front = 1 - front; shown = k; load(vs[1 - front], k + 1, pics[k + 1] ? pics[k + 1].sw : t); }
      if (sub) { const L = subs.find(l => t >= l.at - .1 && t <= l.aend + .4); sub.innerHTML = !L ? '' : t < L.aat - .1 ? `<small>${esc(L.who || 'Homer')}</small><span>${esc(L.text)}</span>` : `<small class="arch">the archive answers · ${esc(L.src || '')}</small><span class="arch">${esc(L.ans)}</span>`; }
      if (t >= b) { voice.pause(); return false; } return true; });
  }

  /* a room of the lab, filmed: the page runs live at 1280x720 in a frame above a caption bar; a camera glides and zooms between its
     regions (shots: {sel, frac:[x,y,w,h] of that element, pad, at: seconds, cap, act(doc)}). The room may not save anything. */
  const snapLS = {}; try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); snapLS[k] = localStorage.getItem(k); } } catch (e) { }
  const restoreLS = () => { try { Object.keys(localStorage).forEach(k => { if (!(k in snapLS)) localStorage.removeItem(k); }); Object.entries(snapLS).forEach(([k, v]) => { if (localStorage.getItem(k) !== v) localStorage.setItem(k, v); }); } catch (e) { } };
  addEventListener('pagehide', restoreLS);
  function room(el, url, shots, o = {}) {
    const AW = 1600, AH = o.h || 770, box = document.createElement('div'); box.style.cssText = `position:absolute;left:0;top:0;width:${AW}px;height:${AH}px;overflow:hidden;background:#000`;
    const cam = document.createElement('div'); cam.style.cssText = 'position:absolute;left:0;top:0;width:1280px;height:720px;transform-origin:0 0;transition:transform 2.4s cubic-bezier(.45,.05,.25,1)';
    const f = document.createElement('iframe'); f.src = url; f.style.cssText = 'width:1280px;height:720px;border:0;background:#0b0a09'; cam.appendChild(f); box.appendChild(cam); el.prepend(box);
    const capb = el.querySelector('.roomcap'); const s0 = Math.min(AW / 1280, AH / 720); cam.style.transition = 'none'; cam.style.transform = `translate(${(AW - 1280 * s0) / 2}px,${(AH - 720 * s0) / 2}px) scale(${s0})`;
    f.addEventListener('load', () => { try { const P = f.contentWindow.Storage.prototype; P.setItem = function () { }; P.removeItem = function () { }; } catch (e) { }
      const my = tok, d = () => f.contentDocument;
      shots.forEach(sh => setTimeout(() => { if (my !== tok) return; try {
          if (sh.act) sh.act(d(), f.contentWindow);
          let z = s0, tx = (AW - 1280 * s0) / 2, ty = (AH - 720 * s0) / 2;
          if (sh.sel) { const e = d().querySelector(sh.sel); if (e) { e.scrollIntoView({ block: 'center', inline: 'center' }); let r = e.getBoundingClientRect(); if (sh.frac) r = { left: r.left + r.width * sh.frac[0], top: r.top + r.height * sh.frac[1], width: r.width * sh.frac[2], height: r.height * sh.frac[3] };
              const pad = sh.pad ?? 16; z = Math.min(sh.max || 2.6, AW / (r.width + 2 * pad), AH / (r.height + 2 * pad)); tx = AW / 2 - z * (r.left + r.width / 2); ty = AH / 2 - z * (r.top + r.height / 2); } }
          cam.style.transition = 'transform 2.4s cubic-bezier(.45,.05,.25,1)'; cam.style.transform = `translate(${tx}px,${ty}px) scale(${z})`;
          if (capb && sh.cap) { capb.innerHTML = sh.cap; capb.classList.remove('in'); void capb.offsetWidth; capb.classList.add('in'); }
        } catch (e) { } }, (sh.at || 0) * 1000 + 600));
      K.leave(() => { restoreLS(); });
    });
  }
  const leaving = []; const leave = f => leaving.push(f);
  const K = { room, leave, $, esc, fmt, line, later, raf, startVideos, typeIn, duck, scene, voice: () => voice, sound: () => sound };
  function cue(ci) { const C = window.EPISODE.cues || []; if (!C.length) return; const src = `score/cues/${C[ci % C.length]}.m4a`; if (score.dataset.src === src) return; score.dataset.src = src;
    const v0 = score.volume, t = performance.now(); const out = () => { const k = Math.min(1, (performance.now() - t) / 900); score.volume = v0 * (1 - k); if (k < 1) requestAnimationFrame(out); else { score.src = src; score.currentTime = 0; duck(false); if (!paused) score.play().catch(() => { }); } }; out(); }
  function show(i) {
    if (i < 0 || i >= beats.length) return; clearTimeout(timer); tok++; cur = i; const b = beats[i]; voice.pause(); while (leaving.length) { try { leaving.pop()(); } catch (e) { } }
    stage.querySelectorAll('.beat').forEach(o => { o.classList.remove('on'); o.querySelectorAll('video').forEach(v => { v.pause(); v.muted = true; }); setTimeout(() => { o.querySelectorAll('video').forEach(v => { v.removeAttribute('src'); v.load(); }); o.remove(); }, 1000); });
    const el = document.createElement('div'); el.className = 'beat'; el.innerHTML = b.html(); stage.appendChild(el); requestAnimationFrame(() => el.classList.add('on'));
    duck(false); if (b.after) b.after(el); cue(chapters.findIndex(c => c.name === b.ch));
    left = b.secs * 1000; t0 = performance.now(); if (!paused) timer = setTimeout(() => show(i + 1), left); ui();
  }
  function ui() {
    const done = beats.slice(0, cur).reduce((a, b) => a + b.secs, 0), tot = beats.reduce((a, b) => a + b.secs, 0);
    document.querySelectorAll('#chs div').forEach((d, ci) => { const c = chapters[ci], cb = beats.filter(b => b.ch === c.name), first = beats.indexOf(cb[0]), passed = beats.slice(first, cur).reduce((a, b) => a + b.secs, 0);
      d.classList.toggle('on', beats[cur] && beats[cur].ch === c.name); d.querySelector('i').style.width = Math.min(100, (cur > first + cb.length - 1 ? 1 : cur < first ? 0 : passed / c.secs) * 100) + '%'; });
    const m = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; $('#time').textContent = `${m(done)} / ${m(tot)}`;
  }
  function pause(p) { paused = p; $('#bPlay').textContent = p ? '▶' : '❚❚';
    stage.querySelectorAll('.beat.on video').forEach(v => p ? v.pause() : (v.style.opacity !== '0' && v.play().catch(() => { }))); p ? (score.pause(), voice.pause()) : (score.play().catch(() => { }), beats[cur] && beats[cur].voice && voice.play().catch(() => { }));
    if (p) { clearTimeout(timer); left -= performance.now() - t0; } else { t0 = performance.now(); timer = setTimeout(() => show(cur + 1), Math.max(500, left)); } }
  function fit() { const W = innerWidth, H = innerHeight - 64, k = Math.min(W / 1600, H / 900); stage.style.transform = `translate(-50%, -50%) scale(${k})`; $('#wrap').style.height = H + 'px'; }
  addEventListener('resize', fit);
  addEventListener('keydown', e => { if (e.key === ' ') { e.preventDefault(); pause(!paused); } if (e.key === 'ArrowRight') show(cur + 1); if (e.key === 'ArrowLeft') show(cur - 1); });
  $('#bPlay').onclick = () => pause(!paused); $('#bNext').onclick = () => show(cur + 1); $('#bPrev').onclick = () => show(cur - 1);
  $('#bSnd').onclick = () => { sound = !sound; $('#bSnd').textContent = sound ? '♪ on' : '♪ off'; duck(false); voice.muted = !sound; stage.querySelectorAll('video').forEach(v => { if (!sound) v.muted = true; }); };
  (async function () {
    fit(); const EP = window.EPISODE, D = await Promise.all(EP.data.map(u => fetch(u).then(r => r.json())));
    EP.build(D, (ch, secs, html, after, opt = {}) => beats.push({ ch, secs, html, after, ...opt }), K); if (EP.ready) EP.ready(K);
    beats.forEach(b => { let c = chapters.find(c => c.name === b.ch); if (!c) chapters.push(c = { name: b.ch, secs: 0 }); c.secs += b.secs; });
    $('#chs').innerHTML = chapters.map(c => `<div style="--w:${c.secs}"><i></i><span>${esc(c.name)}</span></div>`).join('');
    document.querySelectorAll('#chs div').forEach((d, ci) => d.onclick = () => show(beats.findIndex(b => b.ch === chapters[ci].name)));
    const q = new URLSearchParams(location.search), at = q.get('ch');
    $('#start').onclick = () => { $('#start').remove(); score.volume = .28; show(at ? Math.max(0, beats.findIndex(b => b.ch.toLowerCase().startsWith(at.toLowerCase()))) : 0); };
    if (q.has('auto')) $('#start').onclick();
    window.__ep = { beats, chapters, show, pause, get paused() { return paused; }, set paused(v) { paused = v; } };
  })();
})();
