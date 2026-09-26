/* Grand Syntagmatique. Every cut of WYGWYL (the four rendered cuts, plus any bet film kept in
   this browser) is divided on the suite's beats and each slot is typed with Metz's eight
   autonomous segments (metz.js). All cuts play at once against the suite's voice; the table
   shows the same beat in every cut, so one treatment can be commuted against another.
   The machine proposes a type; the analyst can overrule it (right-click or 1–8), stored in
   cineosis.syntagma.v1. */
(() => {
  const $ = s => document.querySelector(s);
  const h = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  const store = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* blocked */ } } };
  const OVK = 'cineosis.syntagma.v1';
  const DOMC = { perception: '#e9d9a8', affect: '#f0b9a4', action: '#e7a37c', reflection: '#b9cfa0', mental: '#a9c9c9', break: '#d9d3c7', time: '#b8b3d8', read: '#d9b8d2' };
  const T = Metz.TYPES;
  const fmt = s => { s = Math.max(0, s | 0); return (s / 60 | 0) + ':' + String(s % 60).padStart(2, '0'); };
  let D, V = [], vi = 0, fi = 0, t = 0, playing = false, bi = -1, OV = store.get(OVK, {});
  const A = new Audio(); A.preload = 'auto';

  const cdn = p => !p ? '' : /^(https?:|\.|\/|wygwyl)/.test(p) ? p : D.cdn + p;
  const clipOf = th => th.replace('/thumbnails/', '/clips/').replace(/\.jpg$/, '.mp4');
  const regime = sg => (D.signs[sg] || [])[2] || 'movement';
  const colorOf = sg => DOMC[(D.signs[sg] || [])[1]] || '#444';

  function fromCut(v) {
    return { code: v.slug, name: v.title, idea: v.idea, shots: v.shots.map(s => ({ t0: s[0], t1: s[1], id: s[2], title: s[3], year: s[4], src: s[5], thumb: cdn(s[6]), video: cdn(clipOf(s[6])), in: s[7], st: s[8], sg: s[9] })) };
  }
  // a bet film kept in this browser: same record format as every bet (seats with a clip)
  function fromFilm(code, seats) {
    const shots = seats.filter(s => s && s.clip && s.t1 > s.t0).sort((a, b) => a.t0 - b.t0).map(s => {
      const c = s.clip, p = c.video || '', m = p.match(/\/sources\/([^/]+)\//), tc = p.match(/\/clips\/(\d{10})-\d{10}\.mp4/);
      return { t0: s.t0, t1: s.t1, id: c.id, title: c.title || '', year: c.year, src: m ? m[1] : (c.title || c.id), thumb: c.thumb, video: p, in: c.in || 0, st: tc ? +tc[1] / 1000 + (c.in || 0) : null, sg: c.sg };
    });
    return { code, name: code, idea: 'kept in this browser', shots };
  }
  function bets() {
    const out = [];
    ['NL', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'].forEach(c => { const f = store.get(`cineosis.film.${c}.v1`, []); if (Array.isArray(f) && f.length >= 3) out.push(fromFilm(c, f)); });
    return out;
  }
  // the voice at a join: seconds of silence between the lines either side (0 when a line runs across it)
  function pauseAt(j) {
    let before = -1e9, after = 1e9;
    for (const l of D.lines) { const a = l[2], b = l[3]; if (a < j - .2 && b > j + .2) return 0; if (b <= j + .2) before = Math.max(before, b); if (a >= j - .2) after = Math.min(after, a); }
    return Math.max(0, after - before);
  }
  function segment(v) {
    v.segs = D.beats.map((b, i) => { const shots = Metz.members(v.shots, b[2], b[3]); return { i, b, shots, r: Metz.classify(shots) }; });
    v.segs.forEach((s, i) => { const n = v.segs[i + 1]; s.out = n ? Metz.punct(s.shots, n.shots, s.b[3], s.b[1] !== n.b[1], D.pause[i], regime) : '■'; });
  }
  const typeOf = (v, s) => OV[v.code + '|' + s.b[0]] || s.r.t;
  const shotAt = (v, x) => { for (const s of v.shots) if (x >= s.t0 && x < s.t1) return s; return null; };
  const beatAt = x => { for (let i = 0; i < D.beats.length; i++) if (x < D.beats[i][3]) return i; return D.beats.length - 1; };
  const filmAt = x => { for (let i = 0; i < D.films.length; i++) if (x < D.films[i].t1) return i; return D.films.length - 1; };
  const lineAt = x => D.lines.find(l => x >= l[2] && x < l[3]);

  /* ---------- playback: the suite's voice is the clock; every cut's video follows it ---------- */
  function follow(el, s, x) {
    if (!s) { el.removeAttribute('src'); el._k = null; el.load(); return; }
    const want = () => { const d = el.duration || 1e9; let p = s.in + (x - s.t0); if (p >= d) p = p % d; return Math.max(0, p); };
    const k = s.id + '@' + s.t0;
    if (el._k !== k) {
      el._k = k; el.poster = s.thumb || ''; el.src = s.video;
      el.addEventListener('loadedmetadata', () => { try { el.currentTime = want(); } catch (e) { } if (playing) el.play().catch(() => { }); }, { once: true });
      return;
    }
    if (el.readyState < 1) return;
    if (Math.abs(el.currentTime - want()) > (playing ? .6 : .05)) { try { el.currentTime = want(); } catch (e) { } }
    if (playing && el.paused) el.play().catch(() => { });
    if (!playing && !el.paused) el.pause();
  }
  function frame() {
    if (playing) t = A.currentTime;
    const mv = $('#mv'); follow(mv, shotAt(V[vi], t), t);
    V.forEach((v, i) => follow(v.el, shotAt(v, t), t));
    const nb = beatAt(t);
    if (filmAt(t) !== fi) { fi = filmAt(t); drawTable(); }
    if (nb !== bi) { bi = nb; nowCell(); }
    const l = lineAt(t); $('#sub').textContent = l ? l[4] : '';
    $('#clock').textContent = fmt(t);
    playhead();
    requestAnimationFrame(frame);
  }
  function seek(x, keepPlaying = true) {
    t = Math.max(0, Math.min(D.duration - .05, x)); A.currentTime = t;
    if (!keepPlaying) pause();
  }
  function play() { playing = true; A.currentTime = t; A.play().catch(() => { playing = false; }); $('#play').textContent = '❚❚'; }
  function pause() { playing = false; A.pause(); $('#play').textContent = '▶'; }

  /* ---------- the one diagram: Metz's table of dichotomies, lit for the segment now playing ---------- */
  function drawTree() {
    const v = V[vi], seg = v.segs[bi] || v.segs[0], ty = typeOf(v, seg), path = new Set(Metz.PATH[ty] || []);
    const cnt = {}; v.segs.forEach(s => { const k = typeOf(v, s); cnt[k] = (cnt[k] || 0) + 1; });
    const max = Math.max(1, ...Object.values(cnt));
    const W = 330, LX = 176, Y = k => 14 + (k - 1) * 27;
    // internal nodes: [key, x, leaves under it, label]
    const N = [['root', 8, [1, 2, 3, 4, 5, 6, 7, 8], 'segment'], ['many', 38, [2, 3, 4, 5, 6, 7, 8], 'syntagma'], ['achron', 70, [2, 3], 'achron.'], ['chron', 70, [4, 5, 6, 7, 8], 'chron.'],
      ['narr', 100, [5, 6, 7, 8], 'narrative'], ['lin', 124, [6, 7, 8], 'linear'], ['disc', 150, [7, 8], 'sequence']];
    const ny = n => (Y(n[2][0]) + Y(n[2][n[2].length - 1])) / 2;
    const kids = { root: [['one', 1], ['many']], many: [['achron'], ['chron']], achron: [['alt', 2], ['noalt', 3]], chron: [['desc', 4], ['narr']], narr: [['altn', 5], ['lin']], lin: [['cont', 6], ['disc']], disc: [['org', 7], ['scat', 8]] };
    const byK = Object.fromEntries(N.map(n => [n[0], n]));
    let s = `<svg viewBox="0 0 ${W} ${Y(8) + 14}" width="100%" role="img" aria-label="Metz's table of autonomous segments">`;
    const on = k => k === 'root' || path.has(k);
    N.forEach(n => {
      const x0 = n[1], y0 = ny(n);
      kids[n[0]].forEach(([k, leaf]) => {
        const lit = on(n[0]) && path.has(k);
        const tx = leaf ? LX : byK[k][1], ty2 = leaf ? Y(leaf) : ny(byK[k]);
        s += `<path d="M${x0} ${y0}H${x0 + 6}V${ty2}H${tx}" fill="none" stroke="${lit ? 'var(--hi)' : '#3a3730'}" stroke-width="${lit ? 2 : 1}"/>`;
      });
      s += `<circle cx="${x0}" cy="${y0}" r="2.5" fill="${on(n[0]) ? 'var(--hi)' : '#5a554b'}"/>`;
    });
    for (let k = 1; k <= 8; k++) {
      const c = cnt[k] || 0, lit = k === ty, y = Y(k);
      s += `<text x="${LX + 4}" y="${y + 4}" font-size="11" fill="${lit ? 'var(--hi)' : c ? '#ece6da' : '#5a554b'}">${k} ${T[k].n}</text>`;
      s += `<rect x="${LX + 4}" y="${y + 7}" width="${Math.max(c ? 1 : 0, 120 * c / max)}" height="2" fill="${lit ? 'var(--hi)' : '#6a655a'}"/>`;
      s += `<text x="${W - 2}" y="${y + 4}" font-size="11" text-anchor="end" fill="${c ? '#8a8378' : '#3a3730'}">${c || '·'}</text>`;
    }
    $('#tree').innerHTML = s + '</svg>';
    const r = seg.r, srcs = new Set(seg.shots.map(x => x.src)).size, ov = OV[v.code + '|' + seg.b[0]];
    $('#why').innerHTML = `<b>${v.name}</b> · beat ${seg.b[0]} · ${seg.shots.length} shot${seg.shots.length === 1 ? '' : 's'} · ${srcs} film${srcs === 1 ? '' : 's'}<br>` +
      (ov ? `set by you: ${T[ov].n} <span style="opacity:.6">(machine: ${T[r.t] ? T[r.t].n : '—'})</span>` : `${r.why}${r.doubt ? ' <b>?</b>' : ''}`) + `<br>join out <b>${seg.out}</b> ${Metz.PUNCT[seg.out]}`;
    const tg = $('#tag'); tg.innerHTML = T[ty] ? `<b>${ty}</b>${T[ty].n}${!ov && r.doubt ? ' ?' : ''}${r.insert ? ' + insert' : ''}` : '';
  }

  /* ---------- monitors ---------- */
  function drawMons() {
    const m = $('#mons'); m.innerHTML = '';
    V.forEach((v, i) => {
      const b = h('button', 'mon' + (i === vi ? ' on' : '')); b.title = v.idea;
      const el = h('video'); el.muted = true; el.playsInline = true; el.preload = 'auto'; v.el = el; el._k = null;
      const sp = h('span'); sp.innerHTML = `<i>${v.name}</i><b></b>`; v.monTag = sp.querySelector('b');
      b.append(el, sp); b.onclick = () => pick(i); m.append(b);
    });
  }
  function pick(i) {
    vi = (i + V.length) % V.length; $('#mv')._k = null;
    document.querySelectorAll('.mon').forEach((b, k) => b.classList.toggle('on', k === vi));
    drawTable(); drawFreq();
  }

  /* ---------- the commutation table for one poem ---------- */
  function span() { const bs = D.beats.filter(b => b[1] === D.films[fi].n); return [bs, bs[0][2], bs[bs.length - 1][3]]; }
  function drawTable() {
    const [bs, a, z] = span(), tb = $('#tbl'); tb.innerHTML = '';
    document.querySelectorAll('.poems button').forEach((b, k) => b.classList.toggle('on', k === fi));
    const head = h('div', 'trow head'), hl = h('div', 'lab', D.films[fi].n + ' ' + D.films[fi].title.toLowerCase()); hl.style.cursor = 'default'; hl.title = D.films[fi].title;
    const hc = h('div', 'cells');
    bs.forEach(b => { const e = h('div', 'bh'); e.style.flexGrow = b[3] - b[2]; e.innerHTML = `<span class="p">${b[0]}</span>`; e.append(b[4]); e.title = b[4]; hc.append(e); });
    // punctuation marks sit on the joins, read from the selected cut
    const v0 = V[vi]; let acc = 0;
    bs.forEach((b, k) => { acc += b[3] - b[2]; if (k === bs.length - 1) return; const seg = v0.segs[D.beats.indexOf(b)], p = h('span', 'pu' + (seg.out === '!' ? ' fx' : ''), seg.out); p.style.left = (100 * acc / (z - a)) + '%'; p.title = Metz.PUNCT[seg.out]; hc.append(p); });
    head.append(hl, hc); tb.append(head);
    V.forEach((v, i) => {
      const row = h('div', 'trow' + (i === vi ? ' on' : '')); row.dataset.v = i;
      const lab = h('div', 'lab', v.name); lab.title = v.idea; lab.onclick = () => pick(i);
      const cells = h('div', 'cells');
      bs.forEach(b => {
        const seg = v.segs[D.beats.indexOf(b)], ty = typeOf(v, seg), ov = OV[v.code + '|' + b[0]];
        const c = h('div', 'cell'); c.style.flexGrow = b[3] - b[2]; c.dataset.t = ty; c.dataset.b = seg.i;
        c.innerHTML = `<div class="ty"><b class="${ov ? 'ov' : ''}">${ty || '·'}</b>${T[ty] ? T[ty].k : ''}${!ov && seg.r.doubt ? '?' : ''}${seg.r.insert ? '+i' : ''}</div>`;
        const st = h('div', 'st');
        seg.shots.forEach(s => { const o = Math.min(s.t1, b[3]) - Math.max(s.t0, b[2]); const e = h('i'); e.style.flexGrow = Math.max(.2, o); e.style.backgroundImage = `url("${s.thumb}")`; e.style.setProperty('--c', colorOf(s.sg)); e.title = `${s.title}${s.year ? ' (' + s.year + ')' : ''}`; st.append(e); });
        c.append(st);
        c.onclick = e => { const r = c.getBoundingClientRect(); pick(i); seek(b[2] + (b[3] - b[2]) * (e.clientX - r.left) / r.width); };
        c.oncontextmenu = e => { e.preventDefault(); pick(i); seek(b[2] + .01); menu(e.clientX, e.clientY, v, seg); };
        cells.append(c);
      });
      row.append(lab, cells); tb.append(row);
    });
    const ph = h('div', 'ph'); ph.id = 'ph'; tb.append(ph);
    nowCell(); playhead();
  }
  function playhead() {
    const ph = $('#ph'); if (!ph) return;
    const [, a, z] = span(), cells = $('.trow.head .cells'); if (!cells) return;
    const r = cells.getBoundingClientRect(), tr = $('#tbl').getBoundingClientRect();
    ph.style.left = (r.left - tr.left + r.width * Math.min(1, Math.max(0, (t - a) / (z - a)))) + 'px';
  }
  function nowCell() {
    document.querySelectorAll('.cell.now').forEach(c => c.classList.remove('now'));
    const c = document.querySelector(`.trow[data-v="${vi}"] .cell[data-b="${bi}"]`); if (c) c.classList.add('now');
    V.forEach(v => { const s = v.segs[bi]; if (s && v.monTag) { const ty = typeOf(v, s); v.monTag.textContent = T[ty] ? ty + ' ' + T[ty].k : ''; } });
    drawTree();
  }

  /* ---------- frequencies: Metz ch. 7, each cut against the others ---------- */
  function drawFreq() {
    const cnt = V.map(v => { const c = {}; v.segs.forEach(s => { const k = typeOf(v, s); c[k] = (c[k] || 0) + 1; }); c.doubt = v.segs.filter(s => !OV[v.code + '|' + s.b[0]] && s.r.doubt).length; c.ins = v.segs.filter(s => s.r.insert).length; return c; });
    let s = `<table><caption>${D.beats.length} beats per cut · each count against the mean of the cuts</caption><tr><th></th>${V.map((v, i) => `<th class="${i === vi ? 'on' : ''}">${v.name}</th>`).join('')}<th>mean</th></tr>`;
    for (let k = 1; k <= 8; k++) {
      const row = V.map((v, i) => cnt[i][k] || 0), mean = row.reduce((a, b) => a + b, 0) / row.length, mx = Math.max(...row);
      s += `<tr><td>${k} ${T[k].n}</td>${row.map(n => `<td class="${!n ? 'z' : Math.abs(n - mean) >= Math.max(4, mean * .5) ? 'dev' : n === mx ? 'hi' : ''}">${n || '·'}</td>`).join('')}<td class="${mean ? '' : 'z'}">${mean ? mean.toFixed(1) : '·'}</td></tr>`;
    }
    s += `<tr><td>? doubtful</td>${cnt.map(c => `<td class="${c.doubt ? '' : 'z'}">${c.doubt || '·'}</td>`).join('')}<td></td></tr>`;
    s += `<tr><td>+ insert</td>${cnt.map(c => `<td class="${c.ins ? '' : 'z'}">${c.ins || '·'}</td>`).join('')}<td></td></tr>`;
    s += `<tr><td>types used</td>${cnt.map(c => `<td class="hi">${[1, 2, 3, 4, 5, 6, 7, 8].filter(k => c[k]).length}/8</td>`).join('')}<td></td></tr></table>`;
    $('#freq').innerHTML = s;
  }

  /* ---------- the analyst decides ---------- */
  function setType(v, seg, k) {
    const key = v.code + '|' + seg.b[0];
    if (!k || k === seg.r.t) delete OV[key]; else OV[key] = k;
    store.set(OVK, OV); drawTable(); drawFreq();
  }
  function menu(x, y, v, seg) {
    const m = $('#menu'); m.innerHTML = '';
    for (let k = 1; k <= 8; k++) { const b = h('button'); b.innerHTML = `<b>${k}</b>${T[k].n}${k === seg.r.t ? ' ·' : ''}`; b.onclick = () => { setType(v, seg, k); m.hidden = true; }; m.append(b); }
    const c = h('button'); c.innerHTML = '<b>0</b>machine\'s reading'; c.onclick = () => { setType(v, seg, 0); m.hidden = true; }; m.append(c);
    m.hidden = false; m.style.left = Math.min(x, innerWidth - 200) + 'px'; m.style.top = Math.min(y, innerHeight - 260) + 'px';
  }
  addEventListener('click', e => { if (!e.target.closest('#menu')) $('#menu').hidden = true; if (!e.target.closest('#pop') && e.target.id !== 'helpBtn') $('#pop').hidden = true; });

  /* ---------- the outline, in the form of Metz's Adieu Philippine ---------- */
  function outline() {
    const v = V[vi], P = { 'o': 'o', '⌒': 'o (overlap)', '■': 'fade (poem ends)', '‖': 'pause in the voice', '!': 'montage with effect' };
    let s = `WYGWYL · ${v.name}\nAutonomous segments on the suite's ${D.beats.length} beats (Metz, Film Language, ch. 5–6)\n`, n = 0, f = null;
    v.segs.forEach((seg, i) => {
      if (seg.b[1] !== f) { f = seg.b[1]; const F = D.films.find(x => x.n === f); s += `\n${F.n} ${F.title}\n`; }
      n++; const ty = typeOf(v, seg), ov = OV[v.code + '|' + seg.b[0]];
      if (i) s += `  ${n - 1}-${n} = ${P[v.segs[i - 1].out]}\n`;
      s += `${n}. ${(T[ty] ? T[ty].n : 'no shot').toUpperCase()}${!ov && seg.r.doubt ? '?' : ''}${seg.r.insert ? ' (with insert)' : ''}   [${fmt(seg.b[2])}] ${seg.b[4]}\n`;
      s += `   ${seg.shots.map(x => x.title + (x.year ? ' ' + x.year : '')).join(' / ')}\n`;
    });
    const a = h('a'); a.href = URL.createObjectURL(new Blob([s], { type: 'text/plain' })); a.download = `wygwyl-${v.code}-syntagmas.txt`; a.click();
  }
  function help() {
    const p = $('#pop'); p.innerHTML = `<dl>
      <dt>1–8</dt><dd>Metz's autonomous segments. The table on the right is his, read left to right; the lit path is the segment playing.</dd>
      <dt>?</dt><dd>the source times needed to decide are unknown</dd><dt>+i</dt><dd>one film carries the beat, a shot of another cuts in</dd>
      ${Object.entries(Metz.PUNCT).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}
      <dt>click</dt><dd>play that cut from that point</dd><dt>right-click · 1–8 · 0</dt><dd>overrule the reading for the lit beat · back to the machine</dd>
      <dt>space ← → ↑ ↓ [ ]</dt><dd>play · beat · cut · poem</dd><dt>underline</dt><dd>colour of the shot's strongest sign</dd></dl>`;
    p.hidden = false;
  }

  addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey || /INPUT|TEXTAREA/.test(e.target.tagName)) return;
    const k = e.key;
    if (k === ' ') { e.preventDefault(); playing ? pause() : play(); }
    else if (k === 'ArrowRight' || k === 'ArrowLeft') { e.preventDefault(); const n = Math.max(0, Math.min(D.beats.length - 1, beatAt(t) + (k === 'ArrowRight' ? 1 : -1))); seek(D.beats[n][2] + .01); }
    else if (k === 'ArrowDown' || k === 'ArrowUp') { e.preventDefault(); pick(vi + (k === 'ArrowDown' ? 1 : -1)); }
    else if (k === ']' || k === '[') { const f = Math.max(0, Math.min(D.films.length - 1, fi + (k === ']' ? 1 : -1))); seek(D.films[f].t0 + .01); }
    else if (/^[0-8]$/.test(k)) { const v = V[vi]; setType(v, v.segs[beatAt(t)], +k); }
    else if (k === 'Escape') { $('#menu').hidden = true; $('#pop').hidden = true; }
  });
  addEventListener('resize', playhead);

  function load(tries = 0) {
    return fetch('syntagma/syntagma-data.json', { cache: tries ? 'reload' : 'no-cache' }).then(r => { if (!r.ok || /html/i.test(r.headers.get('content-type') || '')) throw new Error('data'); return r.json(); })
      .catch(e => tries < 2 ? new Promise(res => setTimeout(res, 1500 * (tries + 1))).then(() => load(tries + 1)) : Promise.reject(e));
  }
  load().then(d => {
    D = d; A.src = D.audio;
    D.pause = D.beats.map((b, i) => i < D.beats.length - 1 ? pauseAt(b[3]) : 0);
    V = D.versions.map(fromCut).concat(bets()); V.forEach(segment);
    const pn = $('#poems'); D.films.forEach((f, i) => { const b = h('button', '', f.n); b.title = f.title; b.onclick = () => seek(f.t0 + .01); pn.append(b); });
    $('#play').onclick = () => playing ? pause() : play();
    $('#exp').onclick = outline; $('#helpBtn').onclick = e => { e.stopPropagation(); help(); };
    A.addEventListener('ended', pause);
    const q = new URLSearchParams(location.search); if (q.get('t')) t = +q.get('t') || 0;
    fi = filmAt(t); bi = beatAt(t);
    drawMons(); drawTable(); drawFreq(); requestAnimationFrame(frame);
  }).catch(() => { document.querySelector('main').innerHTML = '<p style="color:#8a8378">The data did not load. Reload in a moment.</p>'; });
})();
