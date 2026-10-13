/* HOW A SHOT IS MADE — the lab as a river. All 15,149 shots enter at the left and flow right through the stations, in the order
   the lab works. Every model the river passes lays a stratum into the bed: its numbers, words or tags for THIS shot, read in the core
   sample at the right (newest on top, like sediment). Every filter takes shots up out of the river, and the bank says how many and why.
   This shot is the gold pebble; where it is taken up, its line leaves the water. ▶ sends it down again.
   Data: made.json (made.py: stations, models, counts), vec-pic.i8 / vec-snd.i8 (made_vec.py: the shot's real 512 CLIP and CLAP numbers,
   fetched one row at a time with an HTTP Range request). Opens from the inspector and from ?made / ?made=<id>. Uses app.js globals. */
const Made = {
  M: null, s: null, root: null, timer: 0,
  ORDER: ['film', 'cut', 'frame', 'embed', 'name', 'describe', 'measure', 'listen', 'transcribe', 'ask', 'point', 'search', 'vet', 'read', 'rate', 'locate', 'segment', 'use'],
  MED: { film: 'arc', cut: 'arc', frame: 'pic', embed: 'pic', name: 'pic', describe: 'word', measure: 'snd', listen: 'snd', transcribe: 'snd', ask: 'hand', point: 'word', search: 'arc', vet: 'hand', read: 'hand', rate: 'hand', locate: 'pic', segment: 'pic', use: 'ours' },
  COL: { arc: '#8f877a', pic: '#6f8cff', snd: '#ff9f43', word: '#c9a4ff', hand: '#f2c14e', ours: '#7fd6a4' },
  async data() {
    if (!this.M) this.M = await fetch('made.json?v=20261013t').then(r => r.json());
    const w = (o, f) => new Promise(r => { if (o.d || o.map) return r(); f(); const t = setInterval(() => { if (o.d || o.map) { clearInterval(t); r(); } }, 120); setTimeout(() => { clearInterval(t); r(); }, 8000); });
    await Promise.all([w(PROV, () => PROV.load()), w(TX, () => TX.load()), w(SND, () => SND.load()), w(CAPS, () => CAPS.load())]);
  },
  async vec(file, s) {   // the shot's 512 numbers: one row of the file, by Range request
    const i = L.shots.indexOf(s); if (i < 0) return null;
    try { const r = await fetch(file, { headers: { Range: `bytes=${i * 512}-${i * 512 + 511}` } }); let b = new Int8Array(await r.arrayBuffer());
      if (r.status === 200 && b.length > 512) b = b.slice(i * 512, i * 512 + 512); return b.some(x => x) ? b : null; } catch (e) { return null; }
  },
  examples() {
    const read = L.byId.get('21171e70-f59f-55b6-85c3-29691c97e312') || L.shots.find(s => s._read.length);
    const found = L.shots.find(s => !s._read.length && s.found && s.found.length && CAPS.map && CAPS.map[s.id] && (TX.d || {})[s.id] && SND.d && SND.d.heard && SND.d.heard[s.id]) || L.shots.find(s => !s._read.length && s._found.length);
    const forage = L.shots.find(s => !s._found.length && (s.collections || []).includes('wygwyl') && CAPS.map && CAPS.map[s.id] && SND.d && SND.d.heard && SND.d.heard[s.id]) || L.shots.find(s => !s._found.length);
    return { read, found, forage };
  },
  async open(s) {
    if (!this.root) this.build();
    this.from = s || null; this.root.hidden = false; document.body.classList.add('made-on');
    await this.data(); this.ex = this.examples(); this.show(s || this.ex.read);
  },
  close() { clearTimeout(this.timer); this.running = false; if (this.root) { this.root.hidden = true; $('#mdVid', this.root).pause(); } document.body.classList.remove('made-on'); },
  build() {
    const R = this.root = el('div', 'made'); R.id = 'made'; R.hidden = true;
    R.innerHTML = `<div class="md-top"><b>HOW A SHOT IS MADE</b><span id="mdTitle"></span><span class="md-now" id="mdNow"></span>
        <span class="md-ex" id="mdEx"></span><button class="ghost" id="mdRun" title="send the shot down the river again">▶ run</button><button class="ghost" id="mdOpen" title="open this shot in the inspector">open shot</button><button class="ghost" id="mdClose" title="close (Esc)">✕</button></div>
      <div class="md-body"><aside class="md-left"><video id="mdVid" muted playsinline loop></video><div class="md-card" id="mdCard"></div>
          <p class="md-legend"><b>River</b>: the shots still flowing, as wide as how many. <b>Up and out</b>: shots taken up, and why. <b>Bed</b>: what each model laid down for this shot, newest on top. <b>Gold</b>: this shot.</p></aside>
        <div class="md-patch" id="mdPatch"></div></div>`;
    document.body.appendChild(R);
    $('#mdClose', R).onclick = () => this.close();
    $('#mdRun', R).onclick = () => this.run();
    $('#mdOpen', R).onclick = () => { const s = this.s; this.close(); Inspector.open(s); };
    $('#mdEx', R).onclick = e => { const b = e.target.closest('[data-ex]'); if (!b) return; const k = b.dataset.ex;
      this.show(k === 'random' ? L.shots[Math.floor(Math.random() * L.shots.length)] : k === 'this' ? this.from : this.ex[k]); };
    $('#mdPatch', R).addEventListener('pointerover', e => { const r = e.target.closest('[data-st]'); if (r && !this.running) this.card(r.dataset.st); });
    addEventListener('keydown', e => { if (!R.hidden && e.key === 'Escape') { e.stopImmediatePropagation(); this.close(); } }, true);
    new ResizeObserver(() => { if (!R.hidden && this.s && this.F) { this.draw(); this.place(this.at ?? this.ORDER.length - 1, true); } }).observe(R);
  },
  /* what each model laid down for shot s: [true, html] or [false, why not] */
  result(id, s) {
    const pv = PROV.d || {}, film = pv.films && pv.films[s.slug], cap = CAPS.map && CAPS.map[s.id], snd = SND.d || {}, tx = (TX.d || {})[s.id];
    const rd = (s.signs || [])[0], fd = (s.found || [])[0], forage = (s.collections || []).includes('wygwyl') && !s._found.length;
    switch (id) {
      case 'film': return [true, `<span class="md-t">${esc(film ? film[0] : s.title)} <em>${esc((film ? film[1] : s.year) || '')}</em></span>${film && film[2] ? ` · made by <b>${esc(film[2])}</b>` : ''}${film && film[5] ? ` · <span class="md-k">${esc(film[5])}</span>` : ''}`];
      case 'cut': { const pass = (/\/(v\d-[a-z0-9-]+?)-\d\//.exec(s.video || '') || [])[1]; const o = film ? film[6] : [], at = o.indexOf(s.id);
        return [true, `shot <b>${at + 1}</b> of ${o.length || '?'} · ${tc(s.start || 0)} · ${s._dur.toFixed(1)} s${pass ? ` · <span class="md-k">pass ${esc(pass)}</span>` : ''}`]; }
      case 'frame': return [true, `<img src="${esc(s.thumb)}" alt=""><span class="md-k">every machine below reads this one frame</span>`];
      case 'embed': return s.xy ? [true, `<canvas class="md-code" data-vec="vec-pic.i8" width="512" height="22"></canvas><canvas class="md-mini" width="96" height="44"></canvas>`] : [false, 'not yet embedded'];
      case 'name': return s.subjects && s.subjects.length ? [true, s.subjects.slice(0, 3).map(x => `<span class="md-w">${esc(x.label)} <em>${Math.round((x.p || 0) * 100)}</em></span>`).join('') + (s.scale ? `<span class="md-w sc">${esc(s.scale)}</span>` : '')] : [false, 'not yet named'];
      case 'describe': return cap ? [true, `<span class="md-t">“${esc(cap)}”</span>`] : [false, 'not described yet: BLIP has run on half the archive'];
      case 'measure': return s.audio ? [true, `<b>${esc(s.audio.kind || '')}</b>${s.audio.rms_db != null && s.audio.rms_db > -100 ? ` · ${s.audio.rms_db.toFixed(0)} dB` : ''}`] : [false, 'measured only for read shots'];
      case 'listen': { const hd = (snd.heard || {})[s.id]; return hd ? [true, `<canvas class="md-code" data-vec="vec-snd.i8" width="512" height="22"></canvas><span class="md-tags">${hd.map(([t]) => `<span>${esc(t)}</span>`).join('')}</span>`] : [false, s.audio && /silen/.test(s.audio.kind || '') ? 'silent: nothing to lay down' : 'silent or not yet heard']; }
      case 'transcribe': return tx ? [true, `<span class="md-said">${esc(tx.split(/\s+/).slice(0, 22).join(' '))}${tx.split(/\s+/).length > 22 ? '…' : ''}</span>`] : [false, 'no words spoken, or not yet transcribed'];
      case 'ask': { const n = rd ? String(rd.n) : fd ? String(fd.n) : s._aff3[0], sg = L.S[n]; return sg ? [true, `${chip(n, 'sm')} <b>${esc(sg.name)}</b> asks <span class="md-q">${esc(sg.question || '')}</span>`] : [true, '45 questions']; }
      case 'point': return s.aff_top ? [true, s.aff_top.slice(0, 3).map(([n, v]) => `<span class="md-w">${chip(String(n), 'sm')} ${esc((L.S[String(n)] || {}).name || '')} <em>${(+v).toFixed(0)}%</em></span>`).join('')] : [false, 'not pointed'];
      case 'search': return fd ? [true, `${chip(String(fd.n), 'sm')} <span class="md-said">“${esc(fd.q)}”</span> <span class="md-k">#${fd.rank + 1}${s.found.length > 1 ? ` · +${s.found.length - 1} more` : ''}</span>`] : [false, forage ? 'came in by the WYGWYL forage: no sign search returned it' : 'no sign search returned it'];
      case 'vet': return rd ? [true, `kept on the contact sheet for ${chip(String(rd.n), 'sm')}`] : [false, fd ? 'returned by a search, not kept on the contact sheet' : 'never on a contact sheet'];
      case 'read': return rd ? [true, `${chip(String(rd.n), 'sm')} <span class="md-t">${esc(rd.note || '')}</span>`] : [false, 'not read: open it, ask the question, press “read it as”'];
      case 'rate': return rd && rd.conf != null ? [true, `<span class="md-w">in context <em>${rd.conf}%</em></span>${rd.shot != null ? `<span class="md-w">shot alone <em>${rd.shot}%</em></span>` : ''}${rd.alt != null && L.S[String(rd.alt)] ? `<span class="md-w">rival ${chip(String(rd.alt), 'sm')} <em>${rd.alt_conf ?? ''}%</em></span>` : ''}`] : [false, 'nothing to rate until it is read'];
      case 'locate': return rd && s.read_t != null ? [true, `the read frame sits <b>${(+s.read_t).toFixed(2)} s</b> into the clip`] : [false, 'only for read shots'];
      case 'segment': { const g = s.segments; return g && g.objects && g.objects.length ? [true, `<span class="md-tags">${g.objects.slice(0, 4).map(o => `<span>${esc(o.label || o.desc || o.role || '')}</span>`).join('')}</span> <span class="md-k">${g.frames} frames @ ${g.fps} fps</span>`] : [false, 'only for read shots']; }
      case 'use': { const u = (pv.used || {})[s.id] || []; return u.length ? [true, u.slice(0, 3).map(([n, w, r]) => `<span class="md-w"><b>${esc(n)}</b> ${esc(w)} · ${esc(r)}</span>`).join('')] : [false, 'not yet used by any of our films']; }
    }
    return [false, ''];
  },
  /* how many shots are still in the river at each station, and what leaves */
  flow() {
    const T = L.shots.length, found = L.shots.filter(s => s._found.length).length, read = L.shots.filter(s => s._read.length).length;
    const by = Object.fromEntries(this.M.stages.map(x => [x.id, x])), vet = Math.max(read, by.vet.n || read), forage = L.shots.filter(s => !s._found.length && (s.collections || []).includes('wygwyl')).length;
    const U = (PROV.d && PROV.d.used) || {}, used = Object.keys(U).length || by.use.n, usedRead = L.shots.filter(s => s._read.length && U[s.id]).length;
    const n = {}; let k = T; for (const id of this.ORDER) { if (id === 'search') k = found; if (id === 'vet') k = vet; if (id === 'read') k = read; n[id] = k; }
    const out = { search: [T - found, 'never returned by a sign search', `${fmt(forage)} came in by the WYGWYL forage`],
      vet: [found - vet, 'returned, not kept on a contact sheet', ''], read: [vet - read, 'kept, not read yet', ''],
      use: [used, 'taken up into our films', `${fmt(usedRead)} of them read`] };
    const cover = { describe: by.describe.n, measure: by.measure.n, listen: by.listen.n, transcribe: by.transcribe.n };
    const exit = s => !s._found.length ? 'search' : !s._read.length ? 'vet' : null;
    return { T, n, out, cover, exit };
  },
  show(s) {
    if (!s) return; this.s = s; const R = this.root;
    $('#mdTitle', R).innerHTML = `${esc(s.title)} <em>${esc(s.year || '')}</em>`;
    const ex = this.ex, kind = x => x === ex.read ? 'read' : x === ex.found ? 'found' : x === ex.forage ? 'forage' : '';
    $('#mdEx', R).innerHTML = `${this.from ? `<button class="ghost${s === this.from ? ' on' : ''}" data-ex="this">this shot</button>` : ''}<button class="ghost${kind(s) === 'read' ? ' on' : ''}" data-ex="read">a read shot</button><button class="ghost${kind(s) === 'found' ? ' on' : ''}" data-ex="found">a found shot</button><button class="ghost${kind(s) === 'forage' ? ' on' : ''}" data-ex="forage">a forage shot</button><button class="ghost" data-ex="random">random</button>`;
    const v = $('#mdVid', R); v.src = s.video; v.onloadedmetadata = () => { try { v.currentTime = readT(s); } catch (e) { } v.play().catch(() => { }); };
    // the core sample: one stratum per station, newest on top
    const st = Object.fromEntries(this.M.stages.map(x => [x.id, x])), F = this.F = this.flow(), ex2 = F.exit(s), stop = ex2 ? this.ORDER.indexOf(ex2) : 99;
    const rows = this.ORDER.slice().reverse().map(id => { const i = this.ORDER.indexOf(id), reached = i <= stop || id === 'use';
      const [ok, body] = reached ? this.result(id, s) : [false, `not reached: this shot left the river at ${st[ex2].verb}`];
      return `<div class="cr ${ok ? 'ok' : 'no'}" data-st="${id}" style="--c:${this.COL[this.MED[id]]}"><div class="cr-m"><b>${esc(st[id].verb)}</b><span>${esc(st[id].model)}</span></div><div class="cr-b">${ok ? body : `<em class="md-why">${esc(body)}</em>`}</div></div>`; }).join('');
    $('#mdPatch', R).innerHTML = `<svg class="rv-svg"></svg><div class="rv-heads"></div><div class="rv-core">${rows}</div>`;
    this.minis(); this.codes(s); this.draw(); this.run();
  },
  minis() {
    $$('canvas.md-mini', this.root).forEach(cv => {
      const g = cv.getContext('2d'), W = cv.width, H = cv.height, s = this.s;
      g.fillStyle = '#060606'; g.fillRect(0, 0, W, H); g.fillStyle = 'rgba(200,190,170,.4)';
      for (const o of L.shots) if (o.xy) g.fillRect(o.xy[0] * (W - 4) + 2, o.xy[1] * (H - 4) + 2, 1, 1);
      if (!s.xy) return; const x = s.xy[0] * (W - 4) + 2, y = s.xy[1] * (H - 4) + 2;
      g.strokeStyle = '#f2c14e'; g.lineWidth = 1.5; g.beginPath(); g.arc(x, y, 4, 0, 7); g.stroke();
    });
  },
  async codes(s) {   // the 512 numbers, drawn: one thin bar per number, up is positive
    for (const cv of $$('canvas.md-code', this.root)) { const b = await this.vec(cv.dataset.vec, s); if (this.s !== s) return; const g = cv.getContext('2d'), H = cv.height;
      g.clearRect(0, 0, 512, H); if (!b) { g.fillStyle = '#6f685d'; g.font = '11px monospace'; g.fillText('numbers not published', 4, 15); continue; }
      const col = cv.dataset.vec.includes('snd') ? '255,159,67' : '111,140,255';
      for (let i = 0; i < 512; i++) { const v = b[i] / 127; g.fillStyle = `rgba(${col},${.25 + Math.abs(v) * .75})`; const h = Math.abs(v) * (H / 2); g.fillRect(i, v > 0 ? H / 2 - h : H / 2, 1, Math.max(1, h)); }
      cv.title = '512 numbers ' + (cv.dataset.vec.includes('snd') ? 'CLAP heard' : 'CLIP saw') + ' in this shot; the first ten: ' + [...b.slice(0, 10)].map(x => (x / 127).toFixed(2)).join(' '); }
  },
  /* geometry: stations across the river; each stratum runs from its station into the core row that holds it */
  geo() {
    const P = $('#mdPatch', this.root), core = $('.rv-core', P), W = P.clientWidth, cw = core.offsetWidth, x0 = 24, x1 = W - cw - 30, N = this.ORDER.length;
    const xs = this.ORDER.map((id, i) => x0 + (i + .5) * (x1 - x0) / N), yc = 128, hw0 = 52;
    const hw = id => Math.max(1.2, hw0 * this.F.n[id] / this.F.T);
    return { P, W, H: P.clientHeight, x0, x1, xs, yc, hw, hw0, coreL: W - cw - 12 };
  },
  draw() {
    const G = this.g = this.geo(), F = this.F, st = Object.fromEntries(this.M.stages.map(x => [x.id, x])), svg = $('svg.rv-svg', G.P), heads = $('.rv-heads', G.P);
    const { xs, yc, hw } = G, ids = this.ORDER, pr = G.P.getBoundingClientRect();
    svg.setAttribute('width', G.W); svg.setAttribute('height', G.H);
    // the river: one channel, as wide as the shots still in it
    const top = ids.map((id, i) => `${xs[i]},${yc - hw(id)}`), bot = ids.map((id, i) => `${xs[i]},${yc + hw(id)}`).reverse(), xe = G.x1 + 8;
    let h = `<path class="rv-water" d="M${G.x0 - 14},${yc - G.hw0} L${top.join(' L')} L${xe},${yc - hw('use')} L${xe},${yc + hw('use')} L${bot.join(' L')} L${G.x0 - 14},${yc + G.hw0} Z"/>`;
    // partial coverage: how much of the river a model reached, lit across the water
    for (const [id, n] of Object.entries(F.cover)) { const i = ids.indexOf(id), f = Math.min(1, n / F.n[id]), x = xs[i]; h += `<rect class="rv-cov" x="${x - 2.5}" y="${yc - hw(id)}" width="5" height="${2 * hw(id)}"/><rect class="rv-cov on" x="${x - 2.5}" y="${yc + hw(id) - 2 * hw(id) * f}" width="5" height="${2 * hw(id) * f}" style="fill:${this.COL[this.MED[id]]}"/>`; }
    // taken up: streams lifting out of the river into the bank, where a ledger says how many and why
    let j = 0;
    for (const [id, [n, why, sub]] of Object.entries(F.out)) { if (!n) continue; const i = ids.indexOf(id), x = xs[i], w = Math.max(1.5, G.hw0 * 2 * n / F.T), y0 = yc - hw(ids[Math.max(0, i - 1)]), ly = 24 + j++ * 34, lx = G.coreL + 4;
      h += `<path class="rv-out${id === 'use' ? ' use' : ''}" d="M${x - 8},${y0 + Math.min(28, w) / 2} C${x - 4},${ly + 40} ${x + 30},${ly} ${lx - 8},${ly - 4}" style="stroke-width:${Math.min(50, w)}"/>`;
      h += `<text class="rv-ol${id === 'use' ? ' use' : ''}" x="${lx}" y="${ly}"><tspan class="n">${fmt(n)}</tspan> ${esc(why)} <tspan class="at">at ${esc(st[id].verb)}</tspan></text>${sub ? `<text class="rv-ol sub" x="${lx}" y="${ly + 13}">${esc(sub)}</text>` : ''}`; }
    // added: what flows in from outside the machines
    for (const [id, t, dy] of [['ask', '45 questions flow in', 92], ['vet', 'the editor steps in', 66]]) { const x = xs[ids.indexOf(id)]; h += `<path class="rv-in" d="M${x - 6},${yc - dy + 4} C${x - 6},${yc - dy + 30} ${x - 3},${yc - 40} ${x - 3},${yc - hw(id) - 1}"/><text class="rv-il" x="${x - 6}" y="${yc - dy}" text-anchor="end">${esc(t)}</text>`; }
    // the bed: each stratum from its station into its core row
    const rows = Object.fromEntries($$('.cr', G.P).map(r => { const b = r.getBoundingClientRect(); return [r.dataset.st, [b.top - pr.top, b.bottom - pr.top, r.classList.contains('ok')]]; }));
    h += `<line class="rv-floor" x1="${G.x0 - 14}" x2="${G.coreL}" y1="${yc + G.hw0 + 14}" y2="${yc + G.hw0 + 14}"/>`;
    for (const id of ids) { const [a, b, ok] = rows[id] || []; if (a == null) continue; const x = xs[ids.indexOf(id)];
      h += `<path class="rv-st${ok ? ' ok' : ''}" data-st="${id}" d="M${x - 4},${a + 2} L${G.coreL},${a + 2} L${G.coreL},${b - 2} L${x + 6},${b - 2} Z" style="--c:${this.COL[this.MED[id]]}"/>`; }
    // the gold pebble's road, and the drops it lets fall into the bed
    h += `<path class="rv-road" id="rvRoad" d=""/><g id="rvDrops"></g><circle class="rv-peb" id="rvPeb" r="6" cx="${xs[0]}" cy="${yc}"/>`;
    svg.innerHTML = h;
    heads.style.top = (yc + G.hw0 + 18) + 'px';
    heads.innerHTML = ids.map((id, i) => `<span data-st="${id}" style="left:${xs[i]}px;--c:${this.COL[this.MED[id]]}">${esc(st[id].verb.split(' ')[0])}${F.cover[id] ? ` <i>${fmt(F.cover[id])}</i>` : ''}</span>`).join('');
  },
  lane() { let h = 0; for (const c of this.s.id) h = (h * 31 + c.charCodeAt(0)) >>> 0; return ((h % 1000) / 1000 - .5) * 1.4; },
  /* the pebble at station k: its road so far, and a drop into every stratum it laid */
  place(k, instant) {
    const G = this.g, ids = this.ORDER, s = this.s, ln = this.lane(), ex = this.F.exit(s), stop = ex ? ids.indexOf(ex) : 99, svg = $('svg.rv-svg', G.P); if (!svg || !G) return;
    const used = ((PROV.d && PROV.d.used) || {})[s.id], pt = i => [G.xs[i], G.yc + ln * G.hw(ids[Math.min(i, stop - 1)])];
    let d = `M${G.x0 - 14},${G.yc + ln * G.hw0}`, last = [G.x0, G.yc];
    for (let i = 0; i <= Math.min(k, ids.length - 1); i++) {
      const lift = i === stop || (ids[i] === 'use' && used);
      if (lift) { const x = G.xs[i], [, y] = pt(i - 1), row = Object.keys(this.F.out).filter(o => this.F.out[o][0]).indexOf(ids[i]), ly = 24 + Math.max(0, row) * 34;
        d += ` C${x - 4},${ly + 40} ${x + 30},${ly} ${G.coreL - 4},${ly - 4}`; last = [G.coreL - 4, ly - 4]; break; }
      const [x, y] = pt(i); d += ` L${x},${y}`; last = [x, y]; }
    $('#rvRoad', svg).setAttribute('d', d); const p = $('#rvPeb', svg); p.setAttribute('cx', last[0]); p.setAttribute('cy', last[1]);
    const pr = G.P.getBoundingClientRect(), laid = ids.slice(0, k + 1).filter(id => { const r = $(`.cr[data-st="${id}"]`, G.P); return r && r.classList.contains('ok') && (ids.indexOf(id) < stop || id === 'use'); });
    $('#rvDrops', svg).innerHTML = laid.map(id => { const i = ids.indexOf(id), r = $(`.cr[data-st="${id}"]`, G.P).getBoundingClientRect(), y = (r.top + r.bottom) / 2 - pr.top, x = G.xs[i], y0 = G.yc + G.hw(id) + 2;
      return `<line x1="${x}" y1="${y0}" x2="${x}" y2="${y}"/><circle cx="${x}" cy="${y}" r="3.5"/>`; }).join('');
    $$('.rv-st', svg).forEach(w => w.classList.toggle('laid', ids.indexOf(w.dataset.st) <= k));
    $$('.cr', G.P).forEach(r => { r.classList.toggle('laid', ids.indexOf(r.dataset.st) <= k); r.classList.toggle('now', !instant && r.dataset.st === ids[k]); });
    $$('.rv-heads span', G.P).forEach(h => h.classList.toggle('now', !instant && h.dataset.st === ids[k]));
  },
  card(id) {
    const x = this.M.stages.find(t => t.id === id); if (!x) return;
    $('#mdCard', this.root).innerHTML = `<div class="mc-v" style="--c:${this.COL[this.MED[id]]}">${esc(x.verb)}</div><div class="mc-m">${esc(x.model)}</div>
      <dl><dt>learned from</dt><dd>${esc(x.trained)}</dd><dt>lays down</dt><dd>${esc(x.puts)}</dd><dt>cannot see</dt><dd>${esc(x.blind)}</dd>
      <dt>ran on</dt><dd>${x.n != null ? fmt(x.n) + (id === 'ask' ? ' signs' : ` of ${fmt(this.M.total)} shots`) : '—'}${x.day ? ` · last ${x.day}` : ''}</dd></dl>`;
    $$('.cr', this.root).forEach(r => r.classList.toggle('hov', r.dataset.st === id));
  },
  run() {
    clearTimeout(this.timer); const ids = this.ORDER, R = this.root; let k = 0; this.running = true;
    const step = () => { this.at = k; this.place(k); this.card(ids[k]); const ok = $(`.cr[data-st="${ids[k]}"]`, R).classList.contains('ok');
      $('#mdNow', R).innerHTML = `${k + 1}/${ids.length} · <b>${esc(this.M.stages.find(t => t.id === ids[k]).verb)}</b>${ok ? '' : ' <em>· nothing laid down for this shot</em>'}`;
      if (++k < ids.length) this.timer = setTimeout(step, ok ? 1300 : 700); else { this.running = false; this.timer = setTimeout(() => { $('#mdNow', R).textContent = ''; }, 1500); } };
    step();
  },
};
(function () {
  const q = new URLSearchParams(location.search); if (!q.has('made')) return;
  const go = () => { if (!L.shots || !L.shots.length || !L.byId) return setTimeout(go, 300); const id = q.get('made'); Made.open(id ? L.byId.get(id) : null); };
  setTimeout(go, 600);
})();
