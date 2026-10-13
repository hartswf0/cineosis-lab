/* HOW A SHOT IS MADE — the lab's whole process for one shot, as a grid you can read and a film you can watch.
   GRID (right): one row per operation, grouped in phases (SOURCE · SEE · HEAR · ASK · READ · USE). Every row has the same cells:
     step + verb · the actual model · how much of the archive it reached (a Gantt bar on one shared 0–15,149 axis; the gold pip is this
     shot) · what it laid down for this shot · the day it last ran. Read top to bottom: the bars shrink where shots are taken up.
   FILM (left): ▶ plays the process as scenes on the shot itself: the caption arrives as a subtitle, the transcript as timed subtitles,
     the sign's question as a title card, the contact sheet as a grid of what the search returned. Click any row or block to jump there.
   Data: made.json (made.py), vec-pic.i8 / vec-snd.i8 (made_vec.py, one 512-byte row per shot by Range request). Uses app.js globals. */
const Made = {
  M: null, s: null, root: null, timer: 0, k: -1, gesture: false,
  PHASES: [['SOURCE', 'where the shot comes from', ['film', 'cut', 'frame']], ['SEE', 'machines read the picture', ['embed', 'name', 'describe']],
    ['HEAR', 'machines read the sound', ['measure', 'listen', 'transcribe']], ['ASK', 'the 45 signs put their questions', ['ask', 'point', 'search']],
    ['READ', 'a person reads it', ['vet', 'read', 'rate', 'locate', 'segment']], ['USE', 'our films take it up', ['use']]],
  MED: { film: 'arc', cut: 'arc', frame: 'pic', embed: 'pic', name: 'pic', describe: 'word', measure: 'snd', listen: 'snd', transcribe: 'snd', ask: 'hand', point: 'word', search: 'arc', vet: 'hand', read: 'hand', rate: 'hand', locate: 'pic', segment: 'pic', use: 'ours' },
  COL: { arc: '#a8a196', pic: '#6f8cff', snd: '#ff9f43', word: '#c9a4ff', hand: '#f2c14e', ours: '#7fd6a4' },
  get ORDER() { return this.PHASES.flatMap(p => p[2]); },
  async data() {
    if (!this.M) this.M = await fetch('made.json?v=20261013w').then(r => r.json());
    const w = (o, f) => new Promise(r => { if (o.d || o.map) return r(); f(); const t = setInterval(() => { if (o.d || o.map) { clearInterval(t); r(); } }, 120); setTimeout(() => { clearInterval(t); r(); }, 8000); });
    await Promise.all([w(PROV, () => PROV.load()), w(TX, () => TX.load()), w(SND, () => SND.load()), w(CAPS, () => CAPS.load()), w(WORDS, () => WORDS.load())]);
  },
  async vec(file, s) {
    const i = L.shots.indexOf(s); if (i < 0) return null;
    try { const r = await fetch(file, { headers: { Range: `bytes=${i * 512}-${i * 512 + 511}` } }); let b = new Int8Array(await r.arrayBuffer());
      if (r.status === 200 && b.length > 512) b = b.slice(i * 512, i * 512 + 512); return b.length === 512 && b.some(x => x) ? b : null; } catch (e) { return null; }
  },
  examples() {
    const read = L.byId.get('21171e70-f59f-55b6-85c3-29691c97e312') || L.shots.find(s => s._read.length);
    const found = L.shots.find(s => !s._read.length && s.found && s.found.length && CAPS.map && CAPS.map[s.id] && (WORDS.d || {})[s.id] && SND.d && SND.d.heard && SND.d.heard[s.id]) || L.shots.find(s => !s._read.length && s._found.length);
    const forage = L.shots.find(s => !s._found.length && (s.collections || []).includes('wygwyl') && CAPS.map && CAPS.map[s.id] && SND.d && SND.d.heard && SND.d.heard[s.id]) || L.shots.find(s => !s._found.length);
    return { read, found, forage };
  },
  async open(s) {
    if (!this.root) this.build();
    this.from = s || null; this.root.hidden = false; document.body.classList.add('made-on');
    await this.data(); this.ex = this.examples(); this.show(s || this.ex.read);
  },
  close() { clearTimeout(this.timer); if (this.root) { this.root.hidden = true; const v = $('#mdVid', this.root); v.pause(); v.muted = true; } document.body.classList.remove('made-on'); },
  build() {
    const R = this.root = el('div', 'made mg'); R.id = 'made'; R.hidden = true;
    R.innerHTML = `<div class="md-top"><b>HOW A SHOT IS MADE</b><span id="mdTitle"></span>
        <span class="md-ex" id="mdEx"></span><button class="ghost" id="mdRun" title="play the process as a film, with sound">▶ play</button><button class="ghost" id="mdOpen" title="open this shot in the inspector">open shot</button><button class="ghost" id="mdClose" title="close (Esc)">✕</button></div>
      <div class="mg-body">
        <section class="mg-film">
          <div class="mg-screen"><video id="mdVid" muted playsinline loop></video><div class="mg-ov" id="mgOv"></div><div class="mg-step" id="mgStep"></div></div>
          <div class="mg-blocks" id="mgBlocks"></div>
          <div class="mg-scene" id="mgScene"></div>
          <div class="mg-totals" id="mgTotals"></div>
        </section>
        <section class="mg-grid" id="mgGrid"></section>
      </div>`;
    document.body.appendChild(R);
    $('#mdClose', R).onclick = () => this.close();
    $('#mdRun', R).onclick = () => { this.gesture = true; this.play(0); };
    $('#mdOpen', R).onclick = () => { const s = this.s; this.close(); Inspector.open(s); };
    $('#mdEx', R).onclick = e => { const b = e.target.closest('[data-ex]'); if (!b) return; const k = b.dataset.ex;
      this.show(k === 'random' ? L.shots[Math.floor(Math.random() * L.shots.length)] : k === 'this' ? this.from : this.ex[k]); };
    R.addEventListener('click', e => { const r = e.target.closest('[data-go]'); if (r) { this.gesture = true; this.play(this.ORDER.indexOf(r.dataset.go)); } });
    addEventListener('keydown', e => { if (R.hidden) return; if (e.key === 'Escape') { e.stopImmediatePropagation(); this.close(); }
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.stopImmediatePropagation(); e.preventDefault(); this.play(clamp(this.k + (e.key === 'ArrowRight' ? 1 : -1), 0, this.ORDER.length - 1)); } }, true);
  },
  /* what each operation laid down for shot s: [true, html] or [false, why not] — one line, for its grid cell */
  result(id, s) {
    const pv = PROV.d || {}, film = pv.films && pv.films[s.slug], cap = CAPS.map && CAPS.map[s.id], snd = SND.d || {}, tx = (TX.d || {})[s.id];
    const rd = (s.signs || [])[0], fd = (s.found || [])[0], forage = (s.collections || []).includes('wygwyl') && !s._found.length, ex = this.exit(s), stop = ex ? this.ORDER.indexOf(ex) : 99;
    if (this.ORDER.indexOf(id) > stop && id !== 'use') return [false, `not reached: taken up at ${ex.toUpperCase()}`];
    switch (id) {
      case 'film': return [true, `<span class="md-t">${esc(film ? film[0] : s.title)}</span> <em>${esc((film ? film[1] : s.year) || '')}</em>${film && film[2] ? ` · ${esc(film[2])}` : ''}`];
      case 'cut': { const o = film ? film[6] : [], at = o.indexOf(s.id); return [true, `shot <b>${at + 1}</b> of ${o.length || '?'} · ${s._dur.toFixed(1)} s · at ${tc(s.start || 0)}`]; }
      case 'frame': return [true, `<img src="${esc(s.thumb)}" alt=""> the one frame every machine reads`];
      case 'embed': return s.xy ? [true, `<canvas class="md-code" data-vec="vec-pic.i8" width="512" height="20"></canvas>`] : [false, 'not yet embedded'];
      case 'name': return s.subjects && s.subjects.length ? [true, s.subjects.slice(0, 3).map(x => `${esc(x.label)} <em>${Math.round((x.p || 0) * 100)}</em>`).join(' · ') + (s.scale ? ` · ${esc(s.scale)}` : '')] : [false, 'not yet named'];
      case 'describe': return cap ? [true, `<span class="md-t">“${esc(cap)}”</span>`] : [false, 'not yet: BLIP has captioned half the archive'];
      case 'measure': return s.audio ? [true, `${esc(s.audio.kind || '')}${s.audio.rms_db != null && s.audio.rms_db > -100 ? ` · ${s.audio.rms_db.toFixed(0)} dB` : ''}`] : [false, 'measured only for read shots'];
      case 'listen': { const hd = (snd.heard || {})[s.id]; return hd ? [true, `<canvas class="md-code snd" data-vec="vec-snd.i8" width="512" height="20"></canvas> ${hd.map(([t]) => `<span class="md-tag">${esc(t)}</span>`).join('')}`] : [false, 'silent, or not yet heard']; }
      case 'transcribe': return tx ? [true, `<span class="md-said">${esc(tx.split(/\s+/).slice(0, 14).join(' '))}…</span>`] : [false, 'no words spoken, or not yet transcribed'];
      case 'ask': { const n = this.signOf(s), sg = L.S[n]; return sg ? [true, `${chip(n, 'sm')} <span class="md-q">${esc(sg.question || '')}</span>`] : [true, '45 questions']; }
      case 'point': return s.aff_top ? [true, s.aff_top.slice(0, 3).map(([n, v]) => `${chip(String(n), 'sm')} ${esc((L.S[String(n)] || {}).name || '')} <em>${(+v).toFixed(0)}%</em>`).join(' ')] : [false, 'not pointed'];
      case 'search': return fd ? [true, `${chip(String(fd.n), 'sm')} <span class="md-said">“${esc(fd.q)}”</span> <em>#${fd.rank + 1}</em>`] : [false, forage ? 'came by the WYGWYL forage: no sign search returned it' : 'no sign search returned it'];
      case 'vet': return rd ? [true, `kept on the contact sheet for ${chip(String(rd.n), 'sm')}`] : [false, 'returned by a search, not kept on the sheet'];
      case 'read': return rd ? [true, `${chip(String(rd.n), 'sm')} <span class="md-t">${esc(rd.note || '')}</span>`] : [false, 'not read yet'];
      case 'rate': return rd && rd.conf != null ? [true, `in context <em>${rd.conf}%</em> · shot alone <em>${rd.shot ?? '—'}%</em>${rd.alt != null && L.S[String(rd.alt)] ? ` · rival ${chip(String(rd.alt), 'sm')} <em>${rd.alt_conf ?? ''}%</em>` : ''}`] : [false, 'nothing to rate until it is read'];
      case 'locate': return rd && s.read_t != null ? [true, `the read frame is <b>${(+s.read_t).toFixed(2)} s</b> in`] : [false, 'only for read shots'];
      case 'segment': { const g = s.segments; return g && g.objects && g.objects.length ? [true, g.objects.slice(0, 4).map(o => `<span class="md-tag pic">${esc(o.label || o.role || '')}</span>`).join('') + ` <em>${g.frames} frames</em>`] : [false, 'only for read shots']; }
      case 'use': { const u = (pv.used || {})[s.id] || []; return u.length ? [true, u.slice(0, 2).map(([n, w, r]) => `<b>${esc(n)}</b> ${esc(w)} · ${esc(r)}`).join(' / ')] : [false, 'not yet used by any of our films']; }
    }
    return [false, ''];
  },
  signOf(s) { const rd = (s.signs || [])[0], fd = (s.found || [])[0]; return rd ? String(rd.n) : fd ? String(fd.n) : s._aff3[0]; },
  exit(s) { return !s._found.length ? 'search' : !s._read.length ? 'vet' : null; },
  lane(s) { let h = 0; for (const c of s.id) h = (h * 31 + c.charCodeAt(0)) >>> 0; return (h % 1000) / 1000; },
  show(s) {
    if (!s) return; clearTimeout(this.timer); this.s = s; this.k = -1; const R = this.root, M = this.M, T = M.total, st = Object.fromEntries(M.stages.map(x => [x.id, x]));
    $('#mdTitle', R).innerHTML = `${esc(s.title)} <em>${esc(s.year || '')}</em>`;
    const ex = this.ex, kind = x => x === ex.read ? 'read' : x === ex.found ? 'found' : x === ex.forage ? 'forage' : '';
    $('#mdEx', R).innerHTML = `${this.from ? `<button class="ghost${s === this.from ? ' on' : ''}" data-ex="this">this shot</button>` : ''}<button class="ghost${kind(s) === 'read' ? ' on' : ''}" data-ex="read">a read shot</button><button class="ghost${kind(s) === 'found' ? ' on' : ''}" data-ex="found">a found shot</button><button class="ghost${kind(s) === 'forage' ? ' on' : ''}" data-ex="forage">a forage shot</button><button class="ghost" data-ex="random">random</button>`;
    const v = $('#mdVid', R); v.muted = true; v.src = s.video; v.onloadedmetadata = () => { try { v.currentTime = readT(s); } catch (e) { } v.play().catch(() => { }); };
    // the grid: phases of rows, every row the same cells
    const pip = this.lane(s);
    let h = `<div class="mgr mgh"><span>#</span><span>operation · model</span><span>reached <em>0 ─ ${fmt(T)} shots</em></span><span>what it laid down for this shot</span><span>ran</span></div>`;
    let i = 0;
    for (const [ph, gloss, ids] of this.PHASES) {
      h += `<div class="mgp"><b>${ph}</b> ${esc(gloss)}</div>`;
      for (const id of ids) { const x = st[id], [ok, body] = this.result(id, s), n = x.n ?? 0, f = id === 'ask' ? 1 : Math.min(1, n / T);
        h += `<div class="mgr ${ok ? 'ok' : 'no'}" data-go="${id}" style="--c:${this.COL[this.MED[id]]}"><span class="mg-i">${++i}</span>
          <span class="mg-op"><b>${esc(x.verb)}</b><small>${esc(x.model)}</small></span>
          <span class="mg-bar"><i style="width:${f * 100}%"></i><u class="${ok ? '' : 'out'}" style="left:${ok ? pip * f * 100 : Math.min(98, f * 100 + 2)}%"></u><em>${id === 'ask' ? '45 signs' : fmt(n)}</em></span>
          <span class="mg-out">${ok ? body : `<i class="md-why">${esc(body)}</i>`}</span><span class="mg-day">${x.day ? x.day.slice(5).replace('-', '·') : ''}</span></div>`; }
    }
    $('#mgGrid', R).innerHTML = h;
    $('#mgBlocks', R).innerHTML = this.PHASES.map(([ph, , ids]) => `<span class="mb-ph"><em>${ph}</em>${ids.map(id => { const ok = this.result(id, s)[0]; return `<b data-go="${id}" class="${ok ? 'ok' : 'no'}" style="--c:${this.COL[this.MED[id]]}" title="${esc(st[id].verb)}"></b>`; }).join('')}</span>`).join('');
    const read = L.shots.filter(o => o._read.length).length, found = L.shots.filter(o => o._found.length).length;
    $('#mgTotals', R).innerHTML = `<b>${fmt(T)}</b> shots from <b>${fmt(st.film.n)}</b> films · <b>7</b> models and an editor · <b>45</b> signs · <b>${fmt(found)}</b> found by a sign · <b>${fmt(read)}</b> read · <b>${fmt(st.use.n)}</b> placed in our films`;
    this.codes(s); this.play(0);
  },
  async codes(s) {
    for (const cv of $$('canvas.md-code', this.root)) { const b = await this.vec(cv.dataset.vec, s); if (this.s !== s) return; this.bars(cv, b); }
  },
  bars(cv, b) {
    const g = cv.getContext('2d'), H = cv.height, W = cv.width; g.clearRect(0, 0, W, H);
    if (!b) { g.fillStyle = '#6f685d'; g.font = '11px monospace'; g.fillText('numbers not published', 4, H / 2 + 4); return; }
    const col = cv.dataset.vec.includes('snd') ? '255,159,67' : '111,140,255', bw = W / 512;
    for (let i = 0; i < 512; i++) { const v = b[i] / 127, h = Math.abs(v) * (H / 2); g.fillStyle = `rgba(${col},${.3 + Math.abs(v) * .7})`; g.fillRect(i * bw, v > 0 ? H / 2 - h : H / 2, Math.max(1, bw), Math.max(1, h)); }
  },
  /* THE FILM: scene k of the process, played on the shot itself */
  play(k) {
    clearTimeout(this.timer); if (k < 0 || k >= this.ORDER.length) return; this.k = k;
    const R = this.root, id = this.ORDER[k], s = this.s, x = this.M.stages.find(t => t.id === id), [ok, why] = this.result(id, s), v = $('#mdVid', R), O = $('#mgOv', R);
    $$('.mgr[data-go]', R).forEach(r => { r.classList.toggle('now', r.dataset.go === id); r.classList.toggle('past', this.ORDER.indexOf(r.dataset.go) < k); });
    $$('.mg-blocks b', R).forEach(b => { b.classList.toggle('now', b.dataset.go === id); b.classList.toggle('past', this.ORDER.indexOf(b.dataset.go) < k); });
    const row = $(`.mgr[data-go="${id}"]`, R); if (row) row.scrollIntoView({ block: 'nearest' });
    $('#mgStep', R).innerHTML = `<b style="color:${this.COL[this.MED[id]]}">${k + 1}/${this.ORDER.length} · ${esc(x.verb)}</b> ${esc(x.model)}`;
    $('#mgScene', R).innerHTML = `<p class="sc-do"><b style="color:${this.COL[this.MED[id]]}">${esc(x.verb)}</b> ${esc(x.does.startsWith(x.verb.split(' ')[0].toLowerCase() + ' ') ? x.does.slice(x.verb.split(' ')[0].length + 1) : x.does)}.</p>
      <dl><dt>model</dt><dd>${esc(x.model)}</dd><dt>learned from</dt><dd>${esc(x.trained)}</dd><dt>lays down</dt><dd>${esc(x.puts)}</dd><dt>cannot see</dt><dd>${esc(x.blind)}</dd>
      <dt>reached</dt><dd>${x.n != null ? fmt(x.n) + (id === 'ask' ? ' signs' : ` of ${fmt(this.M.total)} shots`) : '—'}${x.day ? ` · last ran ${x.day}` : ''}</dd></dl>`;
    v.muted = true; if (v.paused) v.play().catch(() => { });
    let ms = ok ? 3600 : 1800;
    if (!ok) O.innerHTML = `<div class="ov-skip"><b>${esc(x.verb)}</b><span>${esc(why)}</span></div>`;
    else { try { ms = this.scene(id, s, v, O) || ms; } catch (e) { O.innerHTML = ''; } }
    this.timer = setTimeout(() => { if (k + 1 < this.ORDER.length) this.play(k + 1); else { O.innerHTML = ''; v.muted = true; $$('.mgr', R).forEach(r => r.classList.remove('now')); } }, ms);
  },
  scene(id, s, v, O) {
    const pv = PROV.d || {}, film = pv.films && pv.films[s.slug], rd = (s.signs || [])[0], fd = (s.found || [])[0], snd = SND.d || {};
    const sub = t => `<div class="ov-sub">${t}</div>`, seek = t => { try { v.currentTime = Math.max(0, t); } catch (e) { } };
    switch (id) {
      case 'film': O.innerHTML = `<div class="ov-card"><small>source film</small><b>${esc(film ? film[0] : s.title)}</b><span>${esc((film ? film[1] : s.year) || '')}${film && film[2] ? ' · made by ' + esc(film[2]) : ''}</span>${film && film[4] ? `<p>${esc(film[4])}</p>` : ''}</div>`; return 4200;
      case 'cut': { const o = film ? film[6] : [s.id], at = o.indexOf(s.id), lo = Math.max(0, at - 6), list = o.slice(lo, lo + 13);
        O.innerHTML = `<div class="ov-strip">${list.map(i => { const o2 = L.byId.get(i); return o2 ? `<i class="${i === s.id ? 'on' : ''}" style="background-image:url('${esc(o2.thumb)}')"></i>` : ''; }).join('')}</div>${sub(`shot ${at + 1} of ${o.length}: the film cut where the picture changes`)}`; return 3800; }
      case 'frame': seek(readT(s)); v.pause(); O.innerHTML = `<div class="ov-frame"></div>${sub('this one frame is all the picture machines will ever read')}`; setTimeout(() => { if (this.ORDER[this.k] !== 'frame') return; v.play().catch(() => { }); }, 3000); return 3400;
      case 'embed': O.innerHTML = `<canvas class="ov-code" data-vec="vec-pic.i8" width="512" height="56"></canvas>${sub('CLIP turns the frame into 512 numbers. Shots with close numbers sit close on the picture map')}`;
        this.vec('vec-pic.i8', s).then(b => { const c = $('.ov-code', O); if (c) this.bars(c, b); }); return 4200;
      case 'name': O.innerHTML = `<div class="ov-tags">${(s.subjects || []).slice(0, 4).map(x => `<span><b style="width:${Math.round((x.p || 0) * 100)}%"></b>${esc(x.label)} ${Math.round((x.p || 0) * 100)}</span>`).join('')}${s.scale ? `<span class="sc">${esc(s.scale)}</span>` : ''}</div>${sub('CLIP scores the frame against 20 subject words and 5 shot scales')}`; return 3600;
      case 'describe': O.innerHTML = sub(`<span class="blip">“${esc(CAPS.map[s.id])}”</span>`); return 4000;
      case 'measure': O.innerHTML = `<div class="ov-meter"><b>${esc(s.audio.kind || '')}</b><span>${s.audio.rms_db != null && s.audio.rms_db > -100 ? s.audio.rms_db.toFixed(0) + ' dB' : 'no level'}</span></div>`; return 2800;
      case 'listen': { const hd = (snd.heard || {})[s.id] || []; if (this.gesture) { v.muted = false; v.volume = 1; }
        O.innerHTML = `<canvas class="ov-code snd" data-vec="vec-snd.i8" width="512" height="56"></canvas>${sub(`CLAP hears ${hd.map(([t]) => `<span class="md-tag">${esc(t)}</span>`).join(' and ')}`)}`;
        this.vec('vec-snd.i8', s).then(b => { const c = $('.ov-code', O); if (c) this.bars(c, b); }); return 4800; }
      case 'transcribe': { const w = (WORDS.d || {})[s.id] || []; if (!w.length) { O.innerHTML = sub(`<span class="said">${esc((TX.d || {})[s.id] || '')}</span>`); return 4000; }
        if (this.gesture) { v.muted = false; v.volume = 1; } const t0 = Math.max(0, w[0][1] - .2); seek(t0); v.play().catch(() => { });
        const tick = () => { if (this.ORDER[this.k] !== 'transcribe' || this.root.hidden) return; const t = v.currentTime, said = w.filter(x => x[1] <= t + .05 && x[1] >= t - 3.5).map(x => x[0]).join(' ');
          const e = $('.said', O); if (e) e.textContent = said; else O.innerHTML = sub(`<span class="said">${esc(said)}</span>`); requestAnimationFrame(tick); }; tick();
        return Math.min(9000, Math.max(3500, ((w.at(-1)[1] - t0) + .8) * 1000)); }
      case 'ask': { const n = this.signOf(s), sg = L.S[n]; O.innerHTML = `<div class="ov-q">${chip(n, 'big')}<small>${esc(sg.name)} asks</small><b>${esc(sg.question || '')}</b><span>it is this sign if ${esc((sg.difference || '').split(/(?<=[.;—])\s/)[0])}</span></div>`; return 5400; }
      case 'point': O.innerHTML = `<div class="ov-tags sig">${(s.aff_top || []).slice(0, 3).map(([n, p]) => `<span>${chip(String(n), 'sm')} ${esc((L.S[String(n)] || {}).name || '')} <b style="width:${Math.min(100, p * 4)}%"></b> ${(+p).toFixed(0)}%</span>`).join('')}</div>${sub('where CLIP points: three places to look, not a reading')}`; return 3800;
      case 'search': { const q = fd.q; O.innerHTML = `<div class="ov-search">${chip(String(fd.n), 'sm')}<span id="ovQ"></span><em>result #${fd.rank + 1}</em></div>${sub(`the sign's question, written as a scene, run on the archive's shot search`)}`;
        let i = 0; const type = () => { const e = $('#ovQ', O); if (!e || this.ORDER[this.k] !== 'search') return; e.textContent = q.slice(0, ++i); if (i < q.length) setTimeout(type, 28); }; type(); return Math.max(3800, q.length * 28 + 2000); }
      case 'vet': { const n = String(rd.n), pool = L.shots.filter(o => o._found.includes(n) && o !== s).slice(0, 11); pool.splice(5, 0, s);
        O.innerHTML = `<div class="ov-sheet">${pool.map(o => `<i class="${o === s ? 'keep' : o._read.includes(n) ? 'kept' : ''}" style="background-image:url('${esc(o.thumb)}')"></i>`).join('')}</div>${sub(`the contact sheet for ${esc(L.S[n].name)}: the editor keeps the shots that answer its question`)}`; return 4400; }
      case 'read': O.innerHTML = sub(`${chip(String(rd.n), 'sm')} <span class="rd">${esc(rd.note || '')}</span>`); return 5200;
      case 'rate': O.innerHTML = `<div class="ov-tags sig"><span>in context <b style="width:${rd.conf}%"></b> ${rd.conf}%</span>${rd.shot != null ? `<span>from the shot alone <b style="width:${rd.shot}%"></b> ${rd.shot}%</span>` : ''}${rd.alt != null && L.S[String(rd.alt)] ? `<span>rival ${chip(String(rd.alt), 'sm')} <b style="width:${rd.alt_conf || 0}%"></b> ${rd.alt_conf ?? ''}%</span>` : ''}</div>${rd.flip ? sub(`what would flip it: ${esc(rd.flip)}`) : ''}`; return 4600;
      case 'locate': seek(s.read_t); v.pause(); O.innerHTML = `<div class="ov-time"><i style="left:${clamp(s.read_t / Math.max(.1, s._dur), 0, 1) * 100}%"></i></div>${sub(`the read frame: ${(+s.read_t).toFixed(2)} s into the clip`)}`; setTimeout(() => { if (this.ORDER[this.k] === 'locate') v.play().catch(() => { }); }, 2600); return 3000;
      case 'segment': { const g = s.segments; O.innerHTML = `<div class="ov-cuts">${g.objects.slice(0, 4).map(o => o.png ? `<figure><img src="${esc(o.png)}" alt=""><figcaption>${esc(o.label || o.role || '')}</figcaption></figure>` : '').join('')}</div>${sub('SAM cuts out the figure the reading is about and follows it frame by frame')}`; return 4400; }
      case 'use': { const u = (pv.used || {})[s.id] || []; O.innerHTML = `<div class="ov-card use"><small>taken up into our films</small>${u.slice(0, 4).map(([n, w, r, j]) => `<p><b>${esc(n)}</b> ${esc(w)} · ${esc(r)}${j ? `<br><em>${esc(j)}</em>` : ''}</p>`).join('')}</div>`; return 5000; }
    }
  },
};
(function () {
  const q = new URLSearchParams(location.search); if (!q.has('made')) return;
  const go = () => { if (!L.shots || !L.shots.length || !L.byId) return setTimeout(go, 300); const id = q.get('made'); Made.open(id ? L.byId.get(id) : null); };
  setTimeout(go, 600);
})();
