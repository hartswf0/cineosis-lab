/* CINEOSIS LESSONS · the shared devices, drawn at film size. Load after player.js has defined nothing yet: lessons call LX inside
   EPISODE.build(D, B, K). Every device returns html and, where it moves, a function to run once the beat is on screen.
   band    one sentence at a time beneath the picture: LX.band([[sec, html], ...])
   bar     the search bar: a question typed to the archive, its kind as a chip
   sheet   what came back: five answers that arrive after a beat of not knowing, with how close each picture sits to the words
   clock   the poem as a line of 24 minutes, with moments marked and joined
   words   counts as bars;  kwic  one word held in a column with every question that used it
   tick    a small sound for typing and arrival (Web Audio, quiet; the film's own sound always wins) */
(function () {
  'use strict';
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const mmss = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  const KIND = { literal: 'says what the line shows', oblique: 'says what it feels like, as a picture', place: 'says where it could happen', mood: "the chapter's weather, asked once for all its lines" };
  let ac = null; const audio = () => { try { ac = ac || new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { } return ac; };
  function tick(f = 1800, d = .03, v = .025) { const a = audio(); const sb = document.getElementById('bSnd'); if (!a || (sb && !sb.textContent.includes('on'))) return; const o = a.createOscillator(), g = a.createGain(); o.frequency.value = f * (0.9 + Math.random() * .2); o.type = 'triangle'; g.gain.setValueAtTime(v, a.currentTime); g.gain.exponentialRampToValueAtTime(.0001, a.currentTime + d); o.connect(g); g.connect(a.destination); o.start(); o.stop(a.currentTime + d + .02); }
  const ping = () => { tick(660, .5, .05); setTimeout(() => tick(990, .6, .035), 90); };
  window.__lxSound = true;

  function band(lines, label = '') { return `<div class="bd">${lines.map(([t, h], i) => `<p data-t="${t}">${label && i === 0 ? `<small>${esc(label)}</small>` : ''}${h}</p>`).join('')}</div>`; }
  function runBand(el, K) { const ps = [...el.querySelectorAll('.bd p')]; ps.forEach((p, i) => K.later(+p.dataset.t * 1000, () => { ps.forEach(q => q.classList.remove('on')); p.classList.add('on'); })); }

  function bar(q, kind, def = true) { return `<div class="k-${kind}"><div class="sb"><b class="chip">${kind}</b><span data-q="${esc(q)}"></span></div>${def ? `<div class="kdef">${esc(KIND[kind] || '')}</div>` : ''}</div>`; }
  function typeBar(el, K, at = 0, cps = 30) { const s = el.querySelector('.sb span'); if (!s) return; const text = s.dataset.q; let i = 0;
    K.later(at * 1000, function step() { s.textContent = text.slice(0, ++i); if (i % 2) tick(); if (i < text.length) K.later(1000 / cps, step); }); return text.length / cps + at; }

  const lo = .2, hi = .36, w = s => Math.max(4, Math.min(100, (s - lo) / (hi - lo) * 100));
  function sheet(hits, kind, o = {}) {
    return `<div class="sh k-${kind}">${hits.map((h, i) => `<figure data-i="${i}" data-kept="${(h.used || []).length ? 1 : 0}"><span class="rk">#${h.rank + 1}</span>
      <span class="used">${esc((h.used || []).map(u => u.take.toUpperCase() + ' ' + mmss(u.t0)).slice(0, 2).join(' · '))}</span>
      <div class="tile"><video muted playsinline loop preload="none" data-v="${esc(h.video)}" data-t="${h.t || 0}"></video></div>
      <div class="meter"><i data-w="${w(h.score)}"></i></div><figcaption>${esc(h.title)}<small>${h.year || ''} · ${h.score.toFixed(3)}</small></figcaption></figure>`).join('')}</div>`;
  }
  function revealSheet(el, K, at, gap = .45) { el.querySelectorAll('.sh figure').forEach((f, i) => K.later((at + i * gap) * 1000, () => {
      const v = f.querySelector('video'), t = f.querySelector('.tile'); v.preload = 'auto'; v.src = v.dataset.v; v.addEventListener('loadedmetadata', () => { try { v.currentTime = +v.dataset.t || 0; } catch (e) { } v.play().catch(() => { }); }, { once: true }); v.load();
      v.addEventListener('playing', () => t.classList.add('in'), { once: true }); setTimeout(() => t.classList.add('in'), 1500);
      f.classList.add('shown'); f.querySelector('.meter i').style.width = f.querySelector('.meter i').dataset.w + '%'; tick(1200 + i * 120, .08, .03); })); }
  function markKept(el, K, at) { K.later(at * 1000, () => { let any = false; el.querySelectorAll('.sh figure').forEach(f => { if (f.dataset.kept === '1') { f.classList.add('kept'); any = true; } }); if (any) ping(); }); }

  function clock(dur, marks) { const x = t => (t / dur * 100).toFixed(2) + '%';
    const ticks = [0, 4, 8, 12, 16, 20, 24].filter(m => m * 60 <= dur + 1).map(m => `<span class="tk" style="left:${x(m * 60)}">${m}:00</span>`).join('');
    return `<div class="clk">${ticks}${marks.map((m, i) => `<div class="mk ${m.right ? 'r' : ''}" data-at="${m.at || 0}" style="left:${x(m.t)};--c:${m.c || 'var(--lime)'}"><span><small>${esc(m.k)} · ${mmss(m.t)}</small>${m.h}</span></div>`).join('')}<svg></svg></div>`; }
  function runClock(el, K, dur, arcs = []) { el.querySelectorAll('.clk .mk').forEach(m => K.later(+m.dataset.at * 1000, () => { m.classList.add('on'); tick(900, .1, .04); }));
    const svg = el.querySelector('.clk svg'); if (!svg) return; const W = svg.getBoundingClientRect().width / (el.getBoundingClientRect().width / 1600) || 1440;
    arcs.forEach(a => K.later(a.at * 1000, () => { const x0 = a.from / dur * W, x1 = a.to / dur * W, h = Math.min(260, Math.abs(x1 - x0) * .45 + 40);
      const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('d', `M${x0},300 C${x0},${300 - h} ${x1},${300 - h} ${x1},300`); p.setAttribute('fill', 'none'); p.setAttribute('stroke', a.c || '#c4f46a'); p.setAttribute('stroke-width', 3);
      svg.appendChild(p); const L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; p.getBoundingClientRect(); p.style.transition = 'stroke-dashoffset 2.2s ease'; p.style.strokeDashoffset = 0; })); }

  function words(list, hot = []) { const m = list[0][1]; return `<div class="wb">${list.map(([wd, n]) => `<div class="${hot.includes(wd) ? 'hot' : ''}"><span>${esc(wd)}</span><i data-w="${(n / m * 100).toFixed(1)}"></i><b>${n}</b></div>`).join('')}</div>`; }
  function runWords(el, K, at = .3) { el.querySelectorAll('.wb i').forEach((i, k) => K.later((at + k * .12) * 1000, () => { i.style.width = i.dataset.w + '%'; if (k % 3 === 0) tick(1400, .03, .02); })); }
  function kwic(lines) { return `<div class="kw"><div class="rows">${lines.map(([l, k, r, kind]) => `<div class="row"><span class="l"><span>${esc(l)}</span></span><b>${esc(k)}</b><span class="r">${esc(r)}</span></div>`).join('')}</div></div>`; }
  function runKwic(el, K, secs) { const r = el.querySelector('.kw .rows'), H = r.scrollHeight - 600; K.raf(t => { r.style.transform = `translateY(${200 - Math.min(1, t / secs) * (H + 200)}px)`; return t < secs; }); }


  /* DEVICE · the ranking: candidates as rows; each adjustment of the rule is applied in turn, the rows re-sort, bans turn red */
  const ADJ = { pace: 'pace', stock: 'colour switch', sign: 'signs', reviewed: 'reviewed', drift: 'follows the last', reuse: 'used before' };
  function race(cands, o = {}) { const n = cands.length, rh = Math.min(92, 690 / n);
    return `<div class="rc" style="--rh:${rh}px">${cands.map((c, i) => `<div class="rr" data-i="${i}" style="transform:translateY(${i * rh}px)">
      <div class="rt">${c.hide ? '<span>not shown</span>' : `<video muted playsinline loop preload="none" data-v="${esc(c.clip)}"></video><img src="${esc(c.thumb)}" alt="">`}</div>
      <div class="rn">${esc(c.title)}<small>${c.year || ''}</small></div><div class="rb"><i></i><b class="dl"></b></div><div class="rv">0.000</div><div class="rx"></div></div>`).join('')}</div>`; }
  function runRace(el, K, cands, steps, o = {}) {
    const rows = [...el.querySelectorAll('.rc .rr')], lo = o.lo ?? .2, hi = o.hi ?? .36, rh = parseFloat(getComputedStyle(el.querySelector('.rc')).getPropertyValue('--rh')) || 80;
    const cur = cands.map(c => c.base), out = cands.map(() => null), W = v => Math.max(1, (v - lo) / (hi - lo) * 100);
    const draw = (delta, key) => {
      const order = cands.map((c, i) => i).sort((a, b) => (out[a] ? 1 : 0) - (out[b] ? 1 : 0) || cur[b] - cur[a]);
      order.forEach((i, k) => { const r = rows[i]; r.style.transform = `translateY(${k * rh}px)`; r.querySelector('.rb i').style.width = W(cur[i]) + '%'; r.querySelector('.rv').textContent = cur[i].toFixed(3);
        const d = delta && delta[i], dl = r.querySelector('.dl'); if (d) { dl.textContent = (d > 0 ? '+' : '−') + Math.abs(d).toFixed(3) + ' ' + (ADJ[key] || key); dl.className = 'dl on ' + (d > 0 ? 'up' : 'down'); } else dl.className = 'dl';
        r.classList.toggle('ban', !!out[i]); if (out[i]) r.querySelector('.rx').textContent = out[i]; });
      return order; };
    draw(); rows.forEach((r, i) => { const v = r.querySelector('video'); if (v) { v.src = v.dataset.v; v.preload = 'auto'; v.addEventListener('loadedmetadata', () => { try { v.currentTime = Math.min(2, v.duration / 3); } catch (e) { } v.play().catch(() => { }); }, { once: true }); v.load(); v.addEventListener('playing', () => r.classList.add('live'), { once: true }); } });
    steps.forEach(st => K.later(st.at * 1000, () => {
      let delta = null;
      if (st.ban) cands.forEach((c, i) => { if (c.out) out[i] = c.out; });
      else if (st.key) { delta = cands.map((c, i) => c[st.key] || 0); delta.forEach((d, i) => cur[i] += d); }
      if (st.win) { const w = cands.findIndex(c => c.won); rows[w].classList.add('won'); ping(); }
      draw(delta, st.key); if (delta && delta.some(d => d)) tick(700, .2, .04); else if (st.ban) tick(300, .3, .05); }));
  }

  /* the poem, from a to b, through the episode's voice channel; the score ducks under it */
  function poem(K, src, a, b) { const v = K.voice(); v.src = src; K.duck(true); v.addEventListener('loadedmetadata', () => { v.currentTime = a; if (K.sound()) v.play().catch(() => { }); }, { once: true }); K.raf(() => { if (v.currentTime >= b) { v.pause(); K.duck(false); return false; } return true; }); }

  window.LX = { esc, mmss, KIND, tick, ping, band, runBand, bar, typeBar, sheet, revealSheet, markKept, clock, runClock, words, runWords, kwic, runKwic, poem, race, runRace };
})();
