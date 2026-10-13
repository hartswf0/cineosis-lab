/* HOW A SHOT IS MADE — the lab's pipeline drawn as an operative flow diagram for one shot (made.json, from made.py).
   Columns run left to right in the order the lab works (once per film, per sign, per shot, per word, per read shot, per frame, per use);
   rows are what is worked on (picture, sound, words). Each box is one operation with its result for THIS shot, or, dashed, the
   reason the shot never went through it. ▶ runs the shot through the boxes in order.
   Opens from the inspector ("how this shot was made") and from ?made or ?made=<shot id>. Uses app.js globals. */
const Made = {
  M: null, s: null, root: null, timer: 0, i: 0,
  ORDER: ['film', 'cut', 'frame', 'embed', 'name', 'describe', 'measure', 'listen', 'transcribe', 'ask', 'point', 'search', 'vet', 'read', 'rate', 'locate', 'segment', 'use'],
  async data() {
    if (!this.M) this.M = await fetch('made.json?v=20261013n').then(r => r.json());
    const w = (o, f) => new Promise(r => { if (o.d || o.map) return r(); f(); const t = setInterval(() => { if (o.d || o.map) { clearInterval(t); r(); } }, 120); setTimeout(() => { clearInterval(t); r(); }, 8000); });
    await Promise.all([w(PROV, () => PROV.load()), w(TX, () => TX.load()), w(SND, () => SND.load()), w(CAPS, () => CAPS.load())]);
  },
  examples() {
    const read = L.byId.get('21171e70-f59f-55b6-85c3-29691c97e312') || L.shots.find(s => s._read.length);
    const found = L.shots.find(s => !s._read.length && s.found && s.found.length && CAPS.map && CAPS.map[s.id] && (TX.d || {})[s.id]) || L.shots.find(s => !s._read.length && s._found.length);
    const forage = L.shots.find(s => !s._found.length && (s.collections || []).includes('wygwyl') && CAPS.map && CAPS.map[s.id] && SND.d && SND.d.heard && SND.d.heard[s.id]) || L.shots.find(s => !s._found.length);
    return { read, found, forage };
  },
  async open(s) {
    if (!this.root) this.build();
    this.from = s || null; this.root.hidden = false; document.body.classList.add('made-on');
    await this.data();
    this.ex = this.examples(); this.show(s || this.ex.read);
  },
  close() { clearTimeout(this.timer); if (this.root) { this.root.hidden = true; const v = $('#mdVid', this.root); v.pause(); } document.body.classList.remove('made-on'); },
  build() {
    const R = this.root = el('div', 'made'); R.id = 'made'; R.hidden = true;
    R.innerHTML = `<div class="md-top"><b>HOW A SHOT IS MADE</b><span id="mdTitle"></span><span class="md-now" id="mdNow"></span>
        <span class="md-ex" id="mdEx"></span><button class="ghost" id="mdRun" title="run the shot through again">▶ run</button><button class="ghost" id="mdOpen" title="open this shot in the inspector">open shot</button><button class="ghost" id="mdClose" title="close (Esc)">✕</button></div>
      <div class="md-body"><aside class="md-left">
          <video id="mdVid" muted playsinline loop></video>
          <ol class="md-rules">
            <li><b>A box is one operation.</b> Read its verb, then what it produced for this shot.</li>
            <li><b>Solid box:</b> the shot went through it. <b>Dashed:</b> it did not, and the grey line says what would send it through.</li>
            <li><b>Left to right</b> is the order the lab works: per film, per sign, per shot, per word, per read shot, per frame, per use.</li>
            <li><b>Gold wire:</b> the road this shot took. Press <b>▶ run</b> to send it down again.</li></ol>
          <div class="md-fun" id="mdFun"></div>
        </aside><div class="md-patch" id="mdPatch"></div></div>`;
    document.body.appendChild(R);
    $('#mdClose', R).onclick = () => this.close();
    $('#mdRun', R).onclick = () => this.run();
    $('#mdOpen', R).onclick = () => { const s = this.s; this.close(); Inspector.open(s); };
    $('#mdEx', R).onclick = e => { const b = e.target.closest('[data-ex]'); if (!b) return; const k = b.dataset.ex;
      this.show(k === 'random' ? L.shots[Math.floor(Math.random() * L.shots.length)] : k === 'this' ? this.from : this.ex[k]); };
    addEventListener('keydown', e => { if (!R.hidden && e.key === 'Escape') { e.stopImmediatePropagation(); this.close(); } }, true);
    new ResizeObserver(() => { if (!R.hidden) { this.fit(); this.wires(); } }).observe(R);
  },
  /* what each operation produced for shot s: [done, html] or [false, why it did not run] */
  result(id, s) {
    const pv = PROV.d || {}, film = pv.films && pv.films[s.slug], cap = CAPS.map && CAPS.map[s.id], snd = SND.d || {}, tx = (TX.d || {})[s.id];
    const rd = (s.signs || [])[0], fd = (s.found || [])[0], forage = (s.collections || []).includes('wygwyl') && !s._found.length;
    const pct = v => `<i class="md-bar"><b style="width:${Math.round(v)}%"></b></i>`;
    const notRead = forage ? 'came in by the WYGWYL forage, so no sign search ever returned it and no contact sheet held it' : fd ? `the search for ${L.S[String(fd.n)] ? L.S[String(fd.n)].symbol : ''} returned it, but it was not kept on that sign's contact sheet` : 'no sign search returned it';
    switch (id) {
      case 'film': return film ? [true, `<p class="md-t">${esc(film[0])} <em>${esc(film[1] || '')}</em></p>${film[2] ? `<p>made by <b>${esc(film[2])}</b></p>` : ''}${film[5] ? `<p class="md-k">${esc(film[5])}</p>` : ''}`] : [true, `<p class="md-t">${esc(s.title)} <em>${esc(s.year || '')}</em></p>`];
      case 'cut': { const pass = (/\/(v\d-[a-z0-9-]+?)-\d\//.exec(s.video || '') || [])[1]; const o = film ? film[6] : [], at = o.indexOf(s.id);
        return [true, `<p class="md-t">shot ${at + 1} of ${o.length || '?'}</p><p>${tc(s.start || 0)} · ${s._dur.toFixed(1)} s</p>${pass ? `<p class="md-k">pass ${esc(pass)}</p>` : ''}`]; }
      case 'frame': return [true, `<img src="${esc(s.thumb)}" alt="">`];
      case 'embed': return s.xy ? [true, `<canvas class="md-mini" data-map="xy" width="300" height="160"></canvas>`] : [false, 'not yet embedded'];
      case 'name': return s.subjects && s.subjects.length ? [true, s.subjects.slice(0, 3).map(x => `<p class="md-r"><span>${esc(x.label)}</span>${pct((x.p || 0) * 100)}</p>`).join('') + (s.scale ? `<p class="md-k">${esc(s.scale)}</p>` : '')] : [false, 'not yet named'];
      case 'describe': return cap ? [true, `<p class="md-t">“${esc(cap)}”</p>`] : [false, 'not yet described: BLIP ran on half the archive so far'];
      case 'measure': return s.audio ? [true, `<p class="md-t">${esc(s.audio.kind || '')}</p><p>${s.audio.rms_db != null && s.audio.rms_db > -100 ? s.audio.rms_db.toFixed(0) + ' dB' : 'no level'}</p>`] : [false, 'measured only for read shots'];
      case 'listen': { const hd = (snd.heard || {})[s.id]; return hd ? [true, `<div class="md-tags">${hd.map(([t]) => `<span>${esc(t)}</span>`).join('')}</div><canvas class="md-mini" data-map="sound" width="300" height="120"></canvas>`] : [false, s.audio && /silen/.test(s.audio.kind || '') ? 'silent: nothing to listen to' : 'silent or not yet heard']; }
      case 'transcribe': return tx ? [true, `<p class="md-said">${esc(tx.split(/\s+/).slice(0, 16).join(' '))}${tx.split(/\s+/).length > 16 ? '…' : ''}</p>`] : [false, 'no words spoken, or not yet transcribed'];
      case 'ask': { const n = rd ? String(rd.n) : fd ? String(fd.n) : s._aff3[0], sg = L.S[n]; return sg ? [true, `<p>${chip(n, 'sm')} <b>${esc(sg.name)}</b></p><p class="md-q">${esc(sg.question || '')}</p>`] : [true, '<p>45 questions</p>']; }
      case 'point': return s.aff_top ? [true, s.aff_top.slice(0, 3).map(([n, v]) => `<p class="md-r">${chip(String(n), 'sm')}<span>${esc((L.S[String(n)] || {}).name || '')}</span><em>${(+v).toFixed(0)}%</em></p>`).join('') + '<p class="md-k">places to look, not a reading</p>'] : [false, 'not pointed'];
      case 'search': return fd ? [true, `<p>${chip(String(fd.n), 'sm')} <span class="md-said">“${esc(fd.q)}”</span></p><p class="md-k">result #${fd.rank + 1}${s.found.length > 1 ? ` · and ${s.found.length - 1} more searches` : ''}</p>`] : [false, forage ? 'came in by the WYGWYL forage, not by a sign search' : 'no sign search returned it'];
      case 'vet': return rd ? [true, `<p>kept on the contact sheet for ${chip(String(rd.n), 'sm')}</p>`] : [false, notRead];
      case 'read': return rd ? [true, `<p>${chip(String(rd.n), 'sm')} <b>${esc(L.S[String(rd.n)].name)}</b></p><p class="md-t">${esc(rd.note || '')}</p>`] : [false, 'nobody has read it yet. Open it, ask the question, press “read it as”'];
      case 'rate': return rd && rd.conf != null ? [true, `<p class="md-r"><span>in context</span>${pct(rd.conf)}<em>${rd.conf}%</em></p>${rd.shot != null ? `<p class="md-r"><span>shot alone</span>${pct(rd.shot)}<em>${rd.shot}%</em></p>` : ''}${rd.alt != null && L.S[String(rd.alt)] ? `<p>rival ${chip(String(rd.alt), 'sm')} ${rd.alt_conf ?? ''}%</p>` : ''}`] : [false, 'nothing to rate until it is read'];
      case 'locate': return rd && s.read_t != null ? [true, `<p class="md-t">${(+s.read_t).toFixed(2)} s into the clip</p><p class="md-k">the read frame</p>`] : [false, 'located only for read shots'];
      case 'segment': { const g = s.segments; return g && g.objects && g.objects.length ? [true, `<div class="md-tags">${g.objects.slice(0, 4).map(o => `<span>${esc(o.label || o.desc || o.role || '')}</span>`).join('')}</div><p class="md-k">${g.frames} frames @ ${g.fps} fps</p>`] : [false, 'segmented only for read shots']; }
      case 'use': { const u = (pv.used || {})[s.id] || []; return u.length ? [true, u.slice(0, 4).map(([n, w, r]) => `<p><b>${esc(n)}</b> <span class="md-k">${esc(w)} · ${esc(r)}</span></p>`).join('')] : [false, 'not yet used by any of our films']; }
    }
    return [false, ''];
  },
  show(s) {
    if (!s) return; this.s = s;
    const M = this.M, R = this.root, P = $('#mdPatch', R), byBand = {};
    $('#mdTitle', R).innerHTML = `${esc(s.title)} <em>${esc(s.year || '')}</em>`;
    const ex = this.ex, kind = x => x === ex.read ? 'read' : x === ex.found ? 'found' : x === ex.forage ? 'forage' : '';
    $('#mdEx', R).innerHTML = `${this.from ? `<button class="ghost${s === this.from ? ' on' : ''}" data-ex="this">this shot</button>` : ''}<button class="ghost${kind(s) === 'read' ? ' on' : ''}" data-ex="read">a read shot</button><button class="ghost${kind(s) === 'found' ? ' on' : ''}" data-ex="found">a found shot</button><button class="ghost${kind(s) === 'forage' ? ' on' : ''}" data-ex="forage">a forage shot</button><button class="ghost" data-ex="random">random</button>`;
    const v = $('#mdVid', R); v.src = s.video; v.onloadedmetadata = () => { try { v.currentTime = readT(s); } catch (e) { } v.play().catch(() => { }); };
    // the patch: a grid, columns = rate bands, rows = picture / sound / words
    const cols = M.bands.filter(b => M.stages.some(x => x.band === b[0])), rows = M.cols;
    let h = `<div class="md-grid" style="grid-template-columns:64px repeat(${cols.length},minmax(0,1fr))"><div></div>${cols.map(b => `<div class="md-band">${esc(b[1])}</div>`).join('')}`;
    for (const [rk, rl] of rows) {
      h += `<div class="md-row">${esc(rl)}</div>`;
      for (const [bk] of cols) {
        const here = M.stages.filter(x => x.band === bk && (x.col === rk || (x.col === 'all' && rk === 'word')));
        h += `<div class="md-cell${M.stages.some(x => x.band === bk && x.col === 'all') ? ' all' : ''}">${here.map(st => { const [ok, body] = this.result(st.id, s);
          return `<div class="md-node${ok ? ' ok' : ' no'}" data-id="${st.id}"><div class="md-v">${esc(st.verb)}<small>${st.n != null ? fmt(st.n) + (st.id === 'ask' ? '' : ' / ' + fmt(M.total)) : ''}</small></div>
            <div class="md-does" title="${esc(st.does)}">${esc(st.does)}</div><div class="md-out">${ok ? body : `<p class="md-why">${esc(body)}</p>`}</div>
            <div class="md-tool">${esc(st.tool)}${st.day ? ` · ${st.day.slice(5)}` : ''}</div></div>`; }).join('')}</div>`;
      }
    }
    P.innerHTML = h + '</div><svg class="md-wires"></svg>';
    this.minis(); this.funnel(s); this.fit(); this.run();
  },
  minis() {
    $$('canvas.md-mini', this.root).forEach(cv => {
      const g = cv.getContext('2d'), W = cv.width, H = cv.height, s = this.s, sound = cv.dataset.map === 'sound', XY = sound ? (SND.d || {}).xy || {} : null;
      g.fillStyle = '#060606'; g.fillRect(0, 0, W, H); g.fillStyle = 'rgba(200,190,170,.35)';
      for (const o of L.shots) { const p = sound ? XY[o.id] : o.xy; if (p) g.fillRect(p[0] * (W - 8) + 4, p[1] * (H - 8) + 4, 1, 1); }
      const p = sound ? XY[s.id] : s.xy; if (!p) return; const x = p[0] * (W - 8) + 4, y = p[1] * (H - 8) + 4;
      g.strokeStyle = '#f2c14e'; g.lineWidth = 2; g.beginPath(); g.arc(x, y, 7, 0, 7); g.stroke(); g.fillStyle = '#f2c14e'; g.fillRect(x - 2, y - 2, 4, 4);
    });
  },
  funnel(s) {
    const M = this.M, by = Object.fromEntries(M.stages.map(x => [x.id, x])), T = M.total;
    const rows = [['cut', 'cut into shots'], ['point', 'pointed at 3 signs by the machine'], ['search', 'returned by a sign search'], ['vet', 'kept on a contact sheet'], ['read', 'read by the editor'], ['use', 'used in our films']];
    const at = id => this.result(id, s)[0];
    $('#mdFun', this.root).innerHTML = `<h4>why most shots carry no reading</h4>${rows.map(([id, t]) => `<div class="md-f${at(id) ? ' in' : ''}"><i style="width:${Math.max(.6, by[id].n / T * 100)}%"></i><span>${fmt(by[id].n)}</span><em>${t}</em></div>`).join('')}
      <p>A reading comes by one road only: a sign's search returns the shot, the editor keeps it, the editor writes the sentence. Every other shot carries the machine's three places to look. Gold rows: where this shot got to.</p>`;
  },
  /* the whole patch on one screen: shrink it until it fits, never grow it */
  fit() {
    const P = $('#mdPatch', this.root), G = $('.md-grid', P); if (!G) return; G.style.transform = ''; G.style.width = '';
    const k = Math.min(1, (P.clientHeight - 14) / G.scrollHeight);
    if (k < 1) { G.style.width = (100 / k) + '%'; G.style.transform = `scale(${k})`; const k2 = Math.min(1, (P.clientHeight - 14) / G.scrollHeight); if (k2 < k) G.style.transform = `scale(${k2})`; }
  },
  wires() {
    const R = this.root, svg = $('svg.md-wires', R), P = $('#mdPatch', R); if (!svg) return; const pr = P.getBoundingClientRect();
    svg.setAttribute('width', P.scrollWidth); svg.setAttribute('height', P.scrollHeight);
    const box = id => { const n = $(`.md-node[data-id="${id}"]`, P); if (!n) return null; const r = n.getBoundingClientRect(); return { n, l: r.left - pr.left, r: r.right - pr.left, t: r.top - pr.top, b: r.bottom - pr.top, cx: (r.left + r.right) / 2 - pr.left, cy: (r.top + r.bottom) / 2 - pr.top }; };
    svg.innerHTML = this.M.wires.map(([a, b]) => { const A = box(a), B = box(b); if (!A || !B) return '';
      const lit = A.n.classList.contains('ok') && B.n.classList.contains('ok') && A.n.classList.contains('seen') && B.n.classList.contains('seen');
      let d; if (Math.abs(A.cx - B.cx) < 20) d = A.cy < B.cy ? `M${A.cx},${A.b} L${B.cx},${B.t}` : `M${A.cx},${A.t} L${B.cx},${B.b}`;
      else if (B.l > A.r) { const k = (B.l - A.r) / 2; d = `M${A.r},${A.cy} C${A.r + k},${A.cy} ${B.l - k},${B.cy} ${B.l},${B.cy}`; }
      else { const k = 40; d = `M${A.l},${A.cy} C${A.l - k},${A.cy} ${B.r + k},${B.cy} ${B.r},${B.cy}`; }
      return `<path d="${d}" class="${lit ? 'lit' : ''}"/>`; }).join('');
  },
  run() {
    clearTimeout(this.timer); const R = this.root; $$('.md-node', R).forEach(n => n.classList.remove('seen', 'now')); this.wires();
    const order = this.ORDER.filter(id => $(`.md-node[data-id="${id}"]`, R)); let i = 0;
    const step = () => { $$('.md-node.now', R).forEach(n => n.classList.remove('now'));
      if (i >= order.length) { $('#mdNow', R).textContent = ''; return; }
      const id = order[i++], n = $(`.md-node[data-id="${id}"]`, R), st = this.M.stages.find(x => x.id === id);
      n.classList.add('seen', 'now'); this.wires();
      $('#mdNow', R).innerHTML = `${i}/${order.length} · <b>${esc(st.verb)}</b> ${n.classList.contains('ok') ? '' : '<em>· did not run for this shot</em>'}`;
      this.timer = setTimeout(step, n.classList.contains('ok') ? 1100 : 650); };
    step();
  },
};
(function () {
  const q = new URLSearchParams(location.search); if (!q.has('made')) return;
  const go = () => { if (!L.shots || !L.shots.length || !L.byId) return setTimeout(go, 300); const id = q.get('made'); Made.open(id ? L.byId.get(id) : null); };
  setTimeout(go, 600);
})();
