/* CINEOSIS EPISODES · the shared player. An episode page defines EPISODE = { data: [urls], cues: [score cue names], build(D, B, K) }
   and loads explain/film.css + this file. B(chapter, seconds, html(), after(el), {voice}) adds a scene; K is the kit below.
   One line of type at a time (K.line), moving pictures first, the project's own sound when it carries meaning (K.scene plays a
   scene's audio with its pictures cut by time; the score ducks under it). Keys: space pause, ← → scenes, [ ] chapters,
   < > speed (1×, 1.5×, 2×), N / P next or previous film, F films, L log, Esc closes a panel or leaves the film. */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const fmt = n => Number(n).toLocaleString('en-US');
  let beats = [], chapters = [], cur = -1, timer = 0, paused = false, sound = true, tok = 0, t0 = 0, left = 0;
  const SPEEDS = [1, 1.5, 2]; let speed = 1; try { const sv = +new URLSearchParams(location.search).get('speed') || +localStorage.getItem('cineosis.speed'); if (SPEEDS.includes(sv)) speed = sv; } catch (e) { }
  const stage = $('#stage'), score = $('#score'), voice = $('#voice');
  const duck = on => { score.volume = sound ? (on ? .05 : .28) : 0; };
  const later = (ms, f) => { const my = tok; setTimeout(() => { if (my === tok) f(); }, ms / speed); };
  const raf = f => { const my = tok; let last = performance.now(), el = 0; const go = () => { if (my !== tok) return; const now = performance.now(); el += (now - last) / 1000 * (paused ? 0 : speed); last = now; if (f(el) !== false) requestAnimationFrame(go); }; go(); };
  const line = (ls, sm = '', gap = 2.2) => `<div class="line">${ls.map((l, i) => `<span style="animation-delay:${.4 + i * gap}s">${l}</span>`).join('')}${sm ? `<small style="animation-delay:${.6 + ls.length * gap}s">${sm}</small>` : ''}</div>`;
  function startVideos(el) { el.querySelectorAll('video[data-src]').forEach(v => { v.src = v.dataset.src; if (v.dataset.end) v.addEventListener('timeupdate', () => { if (v.currentTime > +v.dataset.end) v.currentTime = +v.dataset.t; }); v.addEventListener('loadedmetadata', () => { try { v.currentTime = +v.dataset.t || 0; } catch (e) { } if (v.dataset.snd && sound) { v.muted = false; v.volume = 1; } v.play().catch(() => { v.muted = true; v.play().catch(() => { }); }); }, { once: true }); }); }
  function typeIn(el, text, cps = 26) { const my = tok; let i = 0; const step = () => { if (my !== tok || !el) return; el.textContent = text.slice(0, ++i); if (i < text.length) setTimeout(step, 1000 / cps / speed); }; step(); }
  /* speed: every clock the film keeps runs at the chosen rate (CSS animations, videos, the voice, the scene timer) */
  function rates() { try { document.getAnimations().forEach(a => { if (a.playbackRate !== speed) a.playbackRate = speed; }); } catch (e) { }
    document.querySelectorAll('video').forEach(v => { if (v.playbackRate !== speed) v.playbackRate = speed; }); if (voice.playbackRate !== speed) voice.playbackRate = speed; }
  setInterval(rates, 400);
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
  /* THE LOG: every beat records, as it plays, the data it was built from and every picture and sound it loaded (with offsets),
     so each film carries its own spine. Open it with L or the "log" button; copy it out as JSON. */
  const LOG = [], logBox = document.createElement('div'); logBox.id = 'eplog';
  logBox.style.cssText = 'position:fixed;right:12px;top:12px;bottom:76px;width:min(520px,92vw);overflow:auto;background:rgba(10,10,9,.94);border:1px solid #2e2a26;border-radius:6px;padding:14px 16px;font:12px/1.5 "IBM Plex Mono",monospace;color:#cfc8ba;z-index:50;display:none';
  document.body.appendChild(logBox);
  const short = u => { try { const x = new URL(u, location.href); return x.host === location.host ? x.pathname.split('/').slice(-2).join('/') : x.host.split('.')[0] + '…/' + x.pathname.split('/').slice(-1)[0]; } catch (e) { return String(u); } };
  function logBeat(i, el) { const b = beats[i], rec = { beat: i + 1, chapter: b.ch, at: beats.slice(0, i).reduce((a, x) => a + x.secs, 0), secs: b.secs, data: (window.EPISODE.data || []).map(short), media: [] };
    const seen = new Set(), grab = () => { el.querySelectorAll('video').forEach(v => { const u = v.currentSrc || v.src || v.dataset.src; if (u && !seen.has(u)) { seen.add(u); rec.media.push({ kind: 'picture', src: short(u), from: +(v.currentTime || 0).toFixed(2) }); } });
      [voice, score].forEach((a, k) => { const u = a.currentSrc || a.src; if (u && !a.paused && !seen.has(u + k)) { seen.add(u + k); rec.media.push({ kind: k ? 'score' : 'sound', src: short(u), from: +(a.currentTime || 0).toFixed(2) }); } });
      el.querySelectorAll('img').forEach(m => { if (m.src && !seen.has(m.src)) { seen.add(m.src); rec.media.push({ kind: 'still', src: short(m.src) }); } }); renderLog(); };
    LOG[i] = rec; [1200, 4000, Math.max(5000, b.secs * 900)].forEach(ms => later(ms, grab)); }
  function renderLog() { if (logBox.style.display === 'none') return;
    logBox.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><b style="color:#ece6da;letter-spacing:.12em">THE LOG · ${esc(document.title)}</b><button id="logCopy" style="font:inherit;color:#111;background:#c4f46a;border:0;border-radius:3px;padding:3px 10px;cursor:pointer">copy JSON</button></div>`
      + LOG.filter(Boolean).map(r => `<div style="border-top:1px solid #2e2a26;padding:8px 0"><div style="color:#ece6da">${r.beat} · ${esc(r.chapter)} · ${Math.floor(r.at / 60)}:${String(Math.floor(r.at % 60)).padStart(2, '0')} · ${r.secs}s</div><div style="color:#8c867a">data: ${r.data.map(esc).join(', ')}</div>${r.media.map(m => `<div>${m.kind} · ${esc(m.src)}${m.from != null ? ' @ ' + m.from + 's' : ''}</div>`).join('')}</div>`).join('');
    const c = logBox.querySelector('#logCopy'); if (c) c.onclick = () => { const t = JSON.stringify({ film: document.title, url: location.href, beats: LOG.filter(Boolean) }, null, 1); (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => c.textContent = 'copied').catch(() => { const ta = document.createElement('textarea'); ta.value = t; logBox.appendChild(ta); ta.select(); }); }; }
  const toggleLog = () => { logBox.style.display = logBox.style.display === 'none' ? 'block' : 'none'; renderLog(); };

  /* THE FILMS: one list (explain/films.js) for the whole series. A "films" menu on every film, the line under each title saying
     what it makes visible, and a card at the end that leads to the next film. Keys: F opens the menu. */
  const films = () => window.FILMS || [];
  function here() { const F = films(), q = new URLSearchParams(location.search), base = location.pathname.split('/').pop() || 'index.html';
    return F.findIndex(f => { const [p, qs] = f.href.split('?'); if (p !== base) return false; const fq = new URLSearchParams(qs || '');
      if (!qs) return !q.get('part') && !q.get('t'); return [...fq].every(([k, v]) => q.get(k) === v); }); }
  const navBox = document.createElement('div'); navBox.id = 'epfilms';
  navBox.style.cssText = 'position:fixed;inset:0 0 64px 0;background:rgba(8,8,7,.97);z-index:60;display:none;overflow:auto;padding:40px 16px';
  document.body.appendChild(navBox);
  function drawNav() { const F = films(), h = here(); let unit = '';
    const link = (f, i) => `<a href="${f.href}" style="display:grid;grid-template-columns:64px minmax(0,1fr);gap:4px 16px;padding:12px 14px;border-radius:6px;text-decoration:none;${i === h ? 'background:#1f1d19;outline:2px solid #c4f46a;' : ''}"><span style="font:600 15px 'IBM Plex Mono',monospace;color:#a29d90;padding-top:4px">${esc(f.n)}</span><span><b style="display:block;font:600 22px Fraunces,Georgia,serif;color:#ece6da">${esc(f.t)}${i === h ? ' <small style="font:600 12px IBM Plex Mono,monospace;color:#c4f46a;letter-spacing:.12em">YOU ARE HERE</small>' : ''}</b><span style="font:italic 17px Fraunces,Georgia,serif;color:#a29d90">makes visible ${esc(f.v)}</span></span></a>`;
    navBox.innerHTML = `<div style="max-width:880px;margin:0 auto;display:flex;flex-direction:column;gap:6px"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px"><b style="font:600 14px 'IBM Plex Mono',monospace;letter-spacing:.2em;color:#a29d90">CINEOSIS · THE FILMS, IN ORDER</b><span style="display:flex;gap:10px">${h > 0 ? `<a href="${F[h - 1].href}" style="${btn}">‹ previous</a>` : ''}${h >= 0 && h < F.length - 1 ? `<a href="${F[h + 1].href}" style="${btn};background:#c4f46a;color:#111">next ›</a>` : ''}<a href="series.html" style="${btn}">series page</a><a href="papers.html" style="${btn}">papers</a><button id="navX" style="${btn}">close</button></span></div><p style="margin:0 0 10px;font:13px/1.6 'IBM Plex Mono',monospace;color:#8c867a">space pause · ← → scene · [ ] chapter · &lt; &gt; speed · N P film · F films · L log · Esc leave</p>`
      + F.map((f, i) => { const u = f.unit !== unit ? `<div style="font:600 12px 'IBM Plex Mono',monospace;letter-spacing:.18em;color:#6d675d;text-transform:uppercase;margin:18px 0 4px">${esc(unit = f.unit)}</div>` : ''; return u + link(f, i); }).join('') + '</div>';
    navBox.querySelector('#navX').onclick = toggleNav; }
  const btn = "font:600 14px 'IBM Plex Mono',monospace;color:#ece6da;background:none;border:1px solid #3a362f;border-radius:4px;padding:6px 12px;text-decoration:none;cursor:pointer";
  function toggleNav() { const on = navBox.style.display === 'none'; navBox.style.display = on ? 'block' : 'none'; if (on) { drawNav(); if (!paused && cur >= 0) pause(true); } }
  function endCard() { const F = films(), h = here(), nx = F[h + 1]; clearTimeout(timer); tok++;
    stage.querySelectorAll('.beat').forEach(o => { o.classList.remove('on'); o.querySelectorAll('video').forEach(v => { v.pause(); v.removeAttribute('src'); v.load(); }); setTimeout(() => o.remove(), 1000); });
    const el = document.createElement('div'); el.className = 'beat'; stage.appendChild(el);
    el.innerHTML = `<div style="position:absolute;left:140px;right:140px;top:200px;display:flex;flex-direction:column;gap:26px"><small style="font:600 18px 'IBM Plex Mono',monospace;letter-spacing:.22em;color:#a29d90">${nx ? 'NEXT FILM · ' + esc(nx.n) : 'THE END OF THE SERIES'}</small>
      <h1 style="margin:0;font:600 96px/1.05 Fraunces,Georgia,serif;color:#ece6da">${nx ? esc(nx.t) : 'Cineosis'}</h1>${nx ? `<p style="margin:0;font:italic 36px/1.3 Fraunces,Georgia,serif;color:#a29d90">It makes visible ${esc(nx.v)}.</p>` : ''}
      <div style="display:flex;gap:18px;margin-top:20px">${nx ? `<a href="${nx.href}" style="pointer-events:auto;font:600 24px 'IBM Plex Mono',monospace;color:#111;background:#c4f46a;padding:16px 28px;border-radius:5px;text-decoration:none">▶ watch it</a>` : ''}<a href="#" id="endAll" style="pointer-events:auto;font:600 24px 'IBM Plex Mono',monospace;color:#c4f46a;border:2px solid #c4f46a;padding:14px 26px;border-radius:5px;text-decoration:none">all films</a></div></div>`;
    el.querySelector('#endAll').onclick = e => { e.preventDefault(); toggleNav(); }; requestAnimationFrame(() => el.classList.add('on')); duck(false); }
  function show(i) {
    if (i >= beats.length && beats.length) { endCard(); return; } if (i < 0 || i >= beats.length) return; clearTimeout(timer); tok++; cur = i; const b = beats[i]; voice.pause(); while (leaving.length) { try { leaving.pop()(); } catch (e) { } }
    stage.querySelectorAll('.beat').forEach(o => { o.classList.remove('on'); o.querySelectorAll('video').forEach(v => { v.pause(); v.muted = true; }); setTimeout(() => { o.querySelectorAll('video').forEach(v => { v.removeAttribute('src'); v.load(); }); o.remove(); }, 1000); });
    const el = document.createElement('div'); el.className = 'beat'; el.innerHTML = b.html(); stage.appendChild(el); requestAnimationFrame(() => el.classList.add('on'));
    duck(false); if (b.after) b.after(el); cue(chapters.findIndex(c => c.name === b.ch)); logBeat(i, el);
    left = b.secs * 1000; t0 = performance.now(); if (!paused) timer = setTimeout(() => show(i + 1), left / speed); requestAnimationFrame(rates); ui();
  }
  function ui() {
    const done = beats.slice(0, cur).reduce((a, b) => a + b.secs, 0), tot = beats.reduce((a, b) => a + b.secs, 0);
    document.querySelectorAll('#chs div').forEach((d, ci) => { const c = chapters[ci], cb = beats.filter(b => b.ch === c.name), first = beats.indexOf(cb[0]), passed = beats.slice(first, cur).reduce((a, b) => a + b.secs, 0);
      d.classList.toggle('on', beats[cur] && beats[cur].ch === c.name); d.querySelector('i').style.width = Math.min(100, (cur > first + cb.length - 1 ? 1 : cur < first ? 0 : passed / c.secs) * 100) + '%'; });
    const m = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; const t = $('#time'); t.textContent = `${m(done)} / ${m(tot)} · ${m((tot - done) / speed)} left`; t.title = `scene ${cur + 1} of ${beats.length} · ${m((tot - done) / speed)} left at ${speed}×`;
  }
  function pause(p) { paused = p; $('#bPlay').textContent = p ? '▶' : '❚❚';
    stage.querySelectorAll('.beat.on video').forEach(v => p ? v.pause() : (v.style.opacity !== '0' && v.play().catch(() => { }))); p ? (score.pause(), voice.pause()) : (score.play().catch(() => { }), beats[cur] && beats[cur].voice && voice.play().catch(() => { }));
    if (p) { clearTimeout(timer); left -= (performance.now() - t0) * speed; } else { t0 = performance.now(); timer = setTimeout(() => show(cur + 1), Math.max(500, left) / speed); } }
  function setSpeed(v) { if (!SPEEDS.includes(v) || v === speed) return; if (!paused && cur >= 0) { clearTimeout(timer); left -= (performance.now() - t0) * speed; t0 = performance.now(); timer = setTimeout(() => show(cur + 1), Math.max(300, left) / v); }
    speed = v; try { localStorage.setItem('cineosis.speed', v); } catch (e) { } rates(); const b = $('#bSpeed'); if (b) b.textContent = v + '×'; ui(); }
  const faster = d => setSpeed(SPEEDS[Math.max(0, Math.min(SPEEDS.length - 1, SPEEDS.indexOf(speed) + d))]);
  const chapterJump = d => { if (!chapters.length) return; const ci = Math.max(0, chapters.findIndex(c => beats[cur] && c.name === beats[cur].ch)); const t = chapters[ci + d]; if (t) show(beats.findIndex(b => b.ch === t.name)); else if (d > 0) endCard(); else show(0); };
  const filmJump = d => { const F = films(), h = here(); const f = F[h + d]; if (h >= 0 && f) location.href = f.href; };
  const exitFilm = () => { location.href = 'series.html'; };
  function fit() { const W = innerWidth, H = innerHeight - 64, k = Math.min(W / 1600, H / 900); stage.style.transform = `translate(-50%, -50%) scale(${k})`; $('#wrap').style.height = H + 'px'; }
  addEventListener('resize', fit);
  addEventListener('keydown', e => { if (e.metaKey || e.ctrlKey || e.altKey) return; const k = e.key;
    if (k === 'Escape') { if (navBox.style.display !== 'none') toggleNav(); else if (logBox.style.display !== 'none') toggleLog(); else exitFilm(); return; }
    if (k === 'l' || k === 'L') toggleLog(); if (k === 'f' || k === 'F') toggleNav(); if (k === ' ') { e.preventDefault(); pause(!paused); }
    if (k === 'ArrowRight') show(cur + 1); if (k === 'ArrowLeft') show(cur - 1); if (k === ']') chapterJump(1); if (k === '[') chapterJump(-1);
    if (k === '>' || k === '.') faster(1); if (k === '<' || k === ',') faster(-1); if (k === 'n' || k === 'N') filmJump(1); if (k === 'p' || k === 'P') filmJump(-1); });
  $('#bPlay').onclick = () => pause(!paused); { const lb = document.createElement('button'); lb.id = 'bLog'; lb.title = 'the log: what each beat was made from (L)'; lb.textContent = 'log'; lb.onclick = toggleLog; $('#bSnd').before(lb); const fb = document.createElement('button'); fb.id = 'bFilms'; fb.title = 'all the films, in order (F)'; fb.textContent = '☰ films'; fb.onclick = toggleNav; $('#bPrev').before(fb); } $('#bNext').onclick = () => show(cur + 1); $('#bPrev').onclick = () => show(cur - 1);
  { const sb = document.createElement('button'); sb.id = 'bSpeed'; sb.title = 'speed: 1×, 1.5×, 2× (< >)'; sb.textContent = speed + '×'; sb.onclick = () => setSpeed(SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]); $('#bSnd').before(sb);
    const xb = document.createElement('button'); xb.id = 'bExit'; xb.title = 'leave the film, back to the series page (Esc)'; xb.setAttribute('aria-label', 'leave the film'); xb.textContent = '✕'; xb.onclick = exitFilm; $('#bar').appendChild(xb);
    $('#bPrev').title = 'previous scene (←) · previous chapter ([)'; $('#bNext').title = 'next scene (→) · next chapter (])'; }
  $('#bSnd').onclick = () => { sound = !sound; $('#bSnd').textContent = sound ? '♪ on' : '♪ off'; duck(false); voice.muted = !sound; stage.querySelectorAll('video').forEach(v => { if (!sound) v.muted = true; }); };
  (async function () {
    if (!window.FILMS) await new Promise(r => { const sc = document.createElement('script'); sc.src = 'explain/films.js?v=2'; sc.onload = r; sc.onerror = r; document.head.appendChild(sc); });
    fit(); const EP = window.EPISODE, D = await Promise.all(EP.data.map(u => fetch(u).then(r => r.json())));
    EP.build(D, (ch, secs, html, after, opt = {}) => beats.push({ ch, secs, html, after, ...opt }), K); if (EP.ready) EP.ready(K);
    beats.forEach(b => { let c = chapters.find(c => c.name === b.ch); if (!c) chapters.push(c = { name: b.ch, secs: 0 }); c.secs += b.secs; });
    $('#chs').innerHTML = chapters.map(c => `<div style="--w:${c.secs}"><i></i><span>${esc(c.name)}</span></div>`).join('');
    document.querySelectorAll('#chs div').forEach((d, ci) => d.onclick = () => show(beats.findIndex(b => b.ch === chapters[ci].name)));
    const q = new URLSearchParams(location.search), at = q.get('ch');
    const F = films(), h = here(), st = $('#start > div');
    if (st && h >= 0) { const add = document.createElement('div'); add.style.cssText = 'margin-top:22px;display:flex;flex-direction:column;gap:14px';
      add.innerHTML = `<p style="margin:0;font:italic 22px/1.35 Fraunces,Georgia,serif;color:#cfc8ba">Makes visible ${esc(F[h].v)}.</p><span style="display:flex;gap:10px;flex-wrap:wrap;justify-content:center;font-size:14px">${h > 0 ? `<a href="${F[h - 1].href}" style="${btn}">‹ ${esc(F[h - 1].t)}</a>` : ''}<a href="#" class="allf" style="${btn}">☰ all films</a>${h < F.length - 1 ? `<a href="${F[h + 1].href}" style="${btn}">${esc(F[h + 1].t)} ›</a>` : ''}</span>`;
      add.querySelectorAll('a').forEach(a => a.addEventListener('click', e => { e.stopPropagation(); if (a.classList.contains('allf')) { e.preventDefault(); toggleNav(); } }));
      const go = st.querySelector('b'); st.insertBefore(add, go ? go.nextSibling : null); }
    $('#start').onclick = () => { $('#start').remove(); score.volume = .28; show(at ? Math.max(0, beats.findIndex(b => b.ch.toLowerCase().startsWith(at.toLowerCase()))) : 0); };
    if (q.has('auto')) $('#start').onclick();
    window.__ep = { beats, chapters, show, pause, log: LOG, get paused() { return paused; }, set paused(v) { paused = v; } };
  })();
})();
