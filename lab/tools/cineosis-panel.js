/* cineosis panel — the periodic table of the 45 signs, mounted inside an editor (CUT or the WAG Cutting Room).
 *
 * One module for both tools. It reads cineosis-index.json (signs + the WYGWYL cut) and gives the editor:
 *   TABLE    the 45 signs in their 16×3 layout; arrows move, Enter adds the sign's lead shot, Shift+Enter its family
 *   SIGN     the focused sign: gloss, the deciding test, the single-shot ceiling, confusions, and its family of read shots
 *   INSPECT  the selected clip's reading (sign, confidence, rival, flip), from the data the bridge attached to it
 *   WYGWYL   the 14 chapters and 88 beats of the WYGWYL cut; load all of it, a chapter, or one beat
 * Shots go in through window.CineosisBridge.take (bridge.js), which fetches /media/<id>.mp4 same-origin.
 * ?load=wygwyl loads the whole cut once per browser; ?load=wygwyl&fresh=1 empties the editor first.
 * CUT: the panel docks left (P or the ▦ button toggles it). Room: the table replaces the ADD A CLIP row in the dock,
 * and the sign card + WYGWYL sit in a collapsible panel on the stage's right edge (P toggles it).
 */
(function () {
  'use strict';
  const HERE = new URL('.', document.currentScript?.src || location.href);
  const DOM = { perception: '#e9d9a8', affect: '#f0b9a4', action: '#e7a37c', reflection: '#b9cfa0', mental: '#a9c9c9', break: '#d9d3c7', time: '#b8b3d8', read: '#d9b8d2' };
  const DOMNAME = { perception: 'perception-image', affect: 'affection-image', action: 'action-image', reflection: 'reflection-image', mental: 'relation / mental image', break: 'the break', time: 'time-image', read: 'lectosign · reading' };
  const tool = window.CUT ? 'cut' : (window.ButterCut || document.getElementById('cutDock')) ? 'room' : null;
  if (!tool) return;
  const ls = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
               set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } } };
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tc = t => { t = Math.max(0, t || 0); const m = Math.floor(t / 60), s = t - m * 60; return String(m).padStart(2, '0') + ':' + s.toFixed(1).padStart(4, '0'); };
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const thumbUrl = p => new URL('../' + p, HERE).href;
  const media = id => new URL('/media/' + id + '.mp4', location).href;
  const uid = p => p + '-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7);

  let D = null, SIGN = new Map(), CELL = new Map(), BEAT = new Map();
  const V = { pinned: '1', shown: '1', inspected: null, hover: false, tab: ls.get('cineosis.panel.tab', 'sign'), status: '' };
  document.documentElement.classList.add('cx-' + tool);

  /* ---------- the URL: ?load=wygwyl[&fresh=1] ---------- */
  const Q = new URLSearchParams(location.search);
  const AUTO = Q.get('load') === 'wygwyl' ? { fresh: Q.get('fresh') === '1' } : null;
  if (AUTO) {
    const key = 'cineosis.wygwyl.autoload.' + tool;
    if (!AUTO.fresh && ls.get(key, null)) AUTO.skip = true; else ls.set(key, Date.now());
    Q.delete('load'); Q.delete('fresh');                         // a reload must not load (or clear) again
    history.replaceState(history.state, '', location.pathname + (Q.toString() ? '?' + Q : '') + location.hash);
  }

  /* ---------- editor adapters ---------- */
  const ED = tool === 'cut' ? {
    time: () => window.CUT.S.time,
    selection() {
      const C = window.CUT, c = C.S.clips.find(q => q.id === C.S.sel);
      if (!c) return null;
      const name = C.S.sources.get(c.src)?.name || 'clip';
      return { id: c.id, name, info: c.cineosis || window.CineosisBridge?.tagOf?.(name) || null };
    },
    async clear() { const C = window.CUT; if (C.S.clips.length) C.mutate(() => { C.S.clips.length = 0; C.S.sel = null; }); },
    count: () => window.CUT.S.clips.length
  } : {
    time: () => window.ButterCut?.state().time || 0,
    selection() {
      const st = window.ButterCut?.state(); if (!st) return null;
      const id = (st.selected || [])[0], c = id && st.clips.find(q => q.id === id);
      if (!c) return null;
      return { id: c.id, name: c.source || 'clip', info: window.CineosisBridge?.tagOf?.(c.source) || null };
    },
    async clear() {
      for (let k = 0; k < 600 && window.ButterCut?.state().booted === false; k++) await new Promise(r => setTimeout(r, 100));
      window.ButterCut?.clear?.();
    },
    count: () => window.ButterCut?.state().clips.length || 0
  };

  /* ---------- building blocks ---------- */
  const signOf = n => SIGN.get(String(n));
  function chip(n, extra = '') {
    const s = signOf(n); if (!s) return `<span class="cx-code">${esc(n)}</span>`;
    return `<button class="cx-code ${extra}" data-sign="${esc(s.n)}" style="--dc:${DOM[s.dom]}" title="${esc(s.n + ' · ' + s.name)}"><b>${esc(s.symbol)}</b><small>${esc(s.n)}</small></button>`;
  }
  const shotItem = (s, f) => ({ shot: f.id, title: f.title, year: f.year, n: s.n, symbol: s.symbol, note: f.note,
    a: Math.max(0, (f.read_t ?? 0) - 1.5), b: Math.min(f.dur || 4, (f.read_t ?? 0) + 2.5), media: media(f.id) });
  function send(bin, what) {
    const B = window.CineosisBridge;
    if (!B) return status('the bridge is missing on this page');
    status(`${what} → the ${tool === 'cut' ? 'frame' : 'room'} · ${bin.items.length} piece${bin.items.length === 1 ? '' : 's'}…`);
    return Promise.resolve(B.take(bin)).then(() => status(`${what} · in`));
  }
  function addShot(s, f) { return send({ id: uid('cx-shot'), title: `${s.symbol} · ${f.title}`, layout: 'sequence', items: [shotItem(s, f)] }, `${s.symbol} · ${f.title}`); }
  function addFamily(s, layout = 'sequence') {
    if (!s.family.length) return status(`${s.symbol} has no read shots yet`);
    return send({ id: uid('cx-family'), title: `${s.symbol} ${s.name} · family (${layout})`, layout, items: s.family.map(f => shotItem(s, f)) }, `${s.symbol} family as ${layout}`);
  }

  /* ---------- WYGWYL: beats → placed pieces ---------- */
  const PIECE = .25, MONT = 1.5;
  function piece(beat, clip, role, a, b, place) {
    const n = beat.codes?.[0], s = signOf(n);
    return { shot: clip.id, title: clip.title, year: clip.year, n: s?.n || null, symbol: s?.symbol || null,
      note: `WYGWYL #${beat.id} ${role} · ${beat.title}`, a, b, media: media(clip.id), place, beat: beat.id, role };
  }
  function trimOf(clip, trim) { return clip.dur - (trim || 0) > PIECE * 2 ? (trim || 0) : 0; }
  function fill(out, beat, clip, role, trim, t0, t1, box) {       // the clip back to back until the span is full
    const a0 = trimOf(clip, trim); let t = t0;
    for (let k = 0; k < 80 && t < t1 - PIECE; k++) {
      const len = Math.min(clip.dur - a0, t1 - t);
      out.push(piece(beat, clip, role, a0, a0 + len, { t, ...box }));
      t += len;
    }
  }
  const FULL = { x: 0, y: 0, w: 1, h: 1 };
  function beatPieces(beat, forRoom) {
    const out = [], A = beat.a, B = beat.b, t0 = beat.start, t1 = beat.end, len = t1 - t0;
    if (beat.mode === 'black' || !A || len < PIECE) return out;
    if (forRoom) {                                                  // the Cutting Room takes the A line only
      const a = trimOf(A, beat.trim);
      out.push(piece(beat, A, 'A', a, Math.min(A.dur, a + len), { t: t0 }));
      return out;
    }
    const bTrim = BEAT.get(beat.partner)?.trim || 0;
    const mode = B ? beat.mode : 'hold';
    if (mode === 'hold') fill(out, beat, A, 'A', beat.trim, t0, t1, FULL);
    else if (mode === 'split') { fill(out, beat, A, 'A', beat.trim, t0, t1, { x: 0, y: .25, w: .5, h: .5 }); fill(out, beat, B, 'B', bTrim, t0, t1, { x: .5, y: .25, w: .5, h: .5 }); }
    else if (mode === 'inset') { fill(out, beat, A, 'A', beat.trim, t0, t1, FULL); fill(out, beat, B, 'B', bTrim, t0 + len / 2, t1, { x: .64, y: .02, w: .34, h: .34 }); }
    else if (mode === 'dissolve') { fill(out, beat, A, 'A', beat.trim, t0, t0 + len * .6, FULL); fill(out, beat, B, 'B', bTrim, t0 + len * .4, t1, FULL); }
    else if (mode === 'montage') {                                   // A and B alternate in ~1.5 s pieces, each running on
      const pos = { A: trimOf(A, beat.trim), B: trimOf(B, bTrim) }, clip = { A, B };
      let t = t0, i = 0;
      while (t < t1 - PIECE && i < 200) {
        const r = i++ % 2 ? 'B' : 'A', c = clip[r];
        let n = Math.min(MONT, t1 - t); if (t1 - t - n < PIECE) n = t1 - t;
        if (c.dur - pos[r] < Math.min(n, .6)) pos[r] = trimOf(c, r === 'A' ? beat.trim : bTrim);
        n = Math.min(n, c.dur - pos[r]);
        out.push(piece(beat, c, r, pos[r], pos[r] + n, { t, ...FULL }));
        pos[r] += n; t += n;
      }
    } else fill(out, beat, A, 'A', beat.trim, t0, t1, FULL);
    return out.filter(p => p.b - p.a >= PIECE - 1e-6);
  }
  function wygwylBin(beats, title) {
    const room = tool === 'room', items = beats.flatMap(b => beatPieces(b, room));
    return { id: uid('cx-wygwyl'), title, layout: 'wygwyl', span: room ? D.wygwyl.duration : undefined, items };
  }
  const loadBeats = (beats, title) => send(wygwylBin(beats, title), title);
  const loadAll = () => loadBeats(D.wygwyl.beats, 'WYGWYL · the whole cut');
  const loadChapter = i => loadBeats(D.wygwyl.beats.filter(b => b.chapter === i), `WYGWYL · ${D.wygwyl.films[i].n} ${D.wygwyl.films[i].title}`);

  /* ---------- DOM ---------- */
  const table = el('div', 'cx-table' + (tool === 'room' ? ' cx-compact' : ''));
  table.setAttribute('role', 'grid'); table.setAttribute('aria-label', 'Periodic table of cineosis · arrows move, Enter adds the lead shot, Shift+Enter the family');
  const panel = el('aside', 'cx-panel ' + (tool === 'cut' ? 'cx-left' : 'cx-right'));
  panel.id = 'cxPanel'; panel.setAttribute('aria-label', 'Cineosis');
  panel.innerHTML = `
    <div class="cx-head">
      <span class="cx-brand"><b>CINEOSIS</b> · 45 signs</span>
      <span class="cx-status" role="status" aria-live="polite"></span>
      <button class="cx-x" title="Hide the panel · P" aria-label="Hide the cineosis panel">×</button>
    </div>
    <div class="cx-tablehost"></div>
    <div class="cx-tabs" role="tablist">
      <button role="tab" data-tab="sign">Sign</button>
      <button role="tab" data-tab="wygwyl">WYGWYL</button>
    </div>
    <div class="cx-body">
      <section class="cx-pane" data-pane="sign"><div class="cx-inspect"></div><div class="cx-card"></div></section>
      <section class="cx-pane" data-pane="wygwyl"><div class="cx-wy"></div></section>
    </div>`;
  const $p = s => panel.querySelector(s);
  function status(t) { V.status = t; const s = $p('.cx-status'); if (s) { s.textContent = t; s.title = t; } }

  let toggleBtn = null, openState = innerWidth < 760 ? false : ls.get('cineosis.panel.open.' + tool, innerWidth >= 900);   // phones start with the stage
  function setOpen(open) {
    openState = open; ls.set('cineosis.panel.open.' + tool, open);
    panel.classList.toggle('cx-closed', !open);
    toggleBtn?.classList.toggle('on', open); toggleBtn?.setAttribute('aria-expanded', open);
    if (tool === 'cut') relayout();
  }
  function relayout() {
    const docked = openState && innerWidth >= 760;
    const w = docked ? panel.getBoundingClientRect().width : 0;
    window.CUT_INSET = w;
    document.documentElement.style.setProperty('--cx-inset', w + 'px');
    window.CUT?.layout?.();
  }

  function mount() {
    if (tool === 'cut') {
      $p('.cx-tablehost').append(table, legend());
      document.body.appendChild(panel);
      toggleBtn = el('button', 'cx-toggle', '<svg viewBox="0 0 24 24"><path d="M3 5h5v5H3zM10 5h5v5h-5zM17 5h4v14h-4zM3 12h5v5H3zM10 12h5v5h-5z"/></svg><span>Table</span>');
      toggleBtn.id = 'cxToggle'; toggleBtn.title = 'The periodic table of cineosis · P';
      toggleBtn.onclick = () => setOpen(!openState);
      document.getElementById('bar')?.prepend(toggleBtn);
      // the bridge's status + ↩ lab chip joins the bar (floating, it sat on the frame)
      const chipIn = () => { const c = document.getElementById('cxChip'), gap = document.querySelector('#bar .gap'); if (c && gap && c.previousElementSibling !== gap) gap.after(c); };
      chipIn(); addEventListener('load', chipIn);
      addEventListener('resize', relayout);
      new ResizeObserver(relayout).observe(panel);
    } else {
      $p('.cx-tablehost').remove();
      const row = el('div', 'cx-dockrow'); row.id = 'cxDockRow';
      row.append(el('div', 'cx-docklabel', '<b>CINEOSIS</b><span>45 signs · ↵ adds</span>'), table);
      const place = () => { const bar = document.getElementById('cutBar'); if (bar && row.previousElementSibling !== bar) bar.after(row); };
      place();
      const dock = document.getElementById('cutDock'); if (dock) new MutationObserver(place).observe(dock, { childList: true });
      const stage = document.getElementById('stage') || document.body;
      stage.appendChild(panel);
      toggleBtn = el('button', 'cx-tab', '<b>SIGN</b>'); toggleBtn.title = 'Sign card, inspector and WYGWYL · P';
      toggleBtn.onclick = () => setOpen(!openState);
      panel.appendChild(toggleBtn);
      // the bridge's status + ↩ lab chip moves into the dock beside the table (floating, it covered the stage's own buttons)
      const chipIn = () => { const c = document.getElementById('cxChip'); if (c && c.parentNode !== row.firstChild) row.firstChild.appendChild(c); };
      chipIn(); addEventListener('load', chipIn);
    }
    // keys typed in the panel or table belong to it, not to the editor (Space, arrows, Backspace would edit the cut)
    for (const host of [panel, table]) host.addEventListener('keydown', e => { if (!e.ctrlKey && !e.metaKey) e.stopPropagation(); });
    document.addEventListener('keydown', e => {
      if (e.ctrlKey || e.metaKey || e.altKey || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
      if (e.key === 'p' || e.key === 'P') { setOpen(!openState); e.preventDefault(); }
    });
    $p('.cx-x').onclick = () => setOpen(false);
    panel.querySelectorAll('.cx-tabs button').forEach(b => b.onclick = () => setTab(b.dataset.tab));
    panel.addEventListener('click', e => {
      const c = e.target.closest('[data-sign]');
      if (c && !c.classList.contains('cx-tile')) { pin(c.dataset.sign, true); if (tool === 'room' || V.tab !== 'sign') setTab('sign'); }
    });
    setTab(V.tab); setOpen(openState);
  }
  function setTab(t) {
    V.tab = t; ls.set('cineosis.panel.tab', t);
    panel.querySelectorAll('.cx-tabs button').forEach(b => { b.classList.toggle('on', b.dataset.tab === t); b.setAttribute('aria-selected', b.dataset.tab === t); });
    panel.querySelectorAll('.cx-pane').forEach(p => p.hidden = p.dataset.pane !== t);
  }
  function legend() {
    return el('div', 'cx-legend', Object.entries(DOM).map(([k, c]) => `<span><i style="background:${c}"></i>${esc(DOMNAME[k])}</span>`).join(''));
  }

  /* ---------- the table ---------- */
  function buildTable() {
    table.innerHTML = '';
    for (const s of D.signs) {
      const b = el('button', 'cx-tile');
      b.dataset.sign = s.n; b.tabIndex = -1;
      b.style.cssText = `grid-column:${s.col + 1};grid-row:${s.row + 1}${s.dom === 'read' ? ' / span 3' : ''};--dc:${DOM[s.dom]}`;
      b.setAttribute('aria-label', `${s.n} ${s.symbol} · ${s.name} · ${s.family.length} read shots`);
      b.title = `${s.n} · ${s.name} — ${s.family.length} read shot${s.family.length === 1 ? '' : 's'}\n${s.question || ''}`;
      b.innerHTML = `<span class="cx-n">${esc(s.n)}</span><b>${esc(s.symbol)}</b><span class="cx-k" aria-hidden="true">${'<i></i>'.repeat(s.family.length)}</span>`;
      table.appendChild(b);
      const rows = s.dom === 'read' ? [0, 1, 2] : [s.row];
      for (const r of rows) CELL.set(s.col + ',' + r, s);
    }
    table.addEventListener('mouseover', e => { const t = e.target.closest('.cx-tile'); if (t) { V.hover = true; show(t.dataset.sign); } });
    table.addEventListener('mouseleave', () => { V.hover = false; show(V.pinned); });
    table.addEventListener('click', e => {
      const t = e.target.closest('.cx-tile'); if (!t) return;
      pin(t.dataset.sign); t.focus();
      if (tool === 'room') { setTab('sign'); if (!openState) setOpen(true); }   // the card lives in the side panel here
    });
    table.addEventListener('dblclick', e => { const t = e.target.closest('.cx-tile'); if (t) { const s = signOf(t.dataset.sign); if (s.family[0]) addShot(s, s.family[0]); } });
    table.addEventListener('focusin', e => { const t = e.target.closest('.cx-tile'); if (t && t.dataset.sign !== V.pinned) pin(t.dataset.sign); });
    table.addEventListener('keydown', e => {
      const s = signOf(V.pinned); if (!s) return;
      const d = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
      if (d) { const n = step(s, d[0], d[1]); if (n) { pin(n.n); tileOf(n.n)?.focus(); } e.preventDefault(); return; }
      if (e.key === 'Home' || e.key === 'End') { const n = e.key === 'Home' ? D.signs[0] : D.signs[D.signs.length - 1]; pin(n.n); tileOf(n.n)?.focus(); e.preventDefault(); return; }
      if (e.key === 'Enter') { e.preventDefault(); if (e.shiftKey) addFamily(s, tool === 'cut' ? V.layout || 'sequence' : 'sequence'); else if (s.family[0]) addShot(s, s.family[0]); }
    });
  }
  const tileOf = n => table.querySelector(`.cx-tile[data-sign="${CSS.escape(String(n))}"]`);
  const rowOf = s => s.dom === 'read' ? (V.readRow ?? 0) : s.row;
  function step(s, dc, dr) {
    let c = s.col, r = rowOf(s);
    if (dc) {                                            // along the row; a gap (the break has no third row) is jumped
      for (c += dc; c >= 0 && c < 16; c += dc) {
        const hit = CELL.get(c + ',' + r);
        if (hit && hit !== s) { if (hit.dom === 'read') V.readRow = r; return hit; }
      }
      return null;
    }
    if (s.dom === 'read') { const nr = r + dr; if (nr < 0 || nr > 2) return null; V.readRow = nr; return s; }
    const hit = CELL.get(c + ',' + (r + dr));
    return hit || null;
  }
  function pin(n, reveal) {
    const s = signOf(n); if (!s) return;
    if (V.pinned !== s.n) { V.pinned = s.n; ls.set('cineosis.panel.sign', s.n); }
    table.querySelectorAll('.cx-tile').forEach(t => { const on = t.dataset.sign === s.n; t.classList.toggle('is-on', on); t.tabIndex = on ? 0 : -1; t.setAttribute('aria-selected', on); });
    if (reveal) tileOf(s.n)?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    show(s.n);
  }

  /* ---------- the sign card ---------- */
  function show(n) {
    const s = signOf(n); if (!s || (V.shown === s.n && $p('.cx-card').childElementCount)) return;
    V.shown = s.n;
    const card = $p('.cx-card');
    card.style.setProperty('--dc', DOM[s.dom]);
    const lay = tool === 'cut'
      ? `<span class="cx-lbl">add family as</span>${['sequence', 'grid', 'cascade', 'split'].map(l => `<button data-lay="${l}" title="${esc({ sequence: 'one after another, at the end of the cut', grid: 'peaks of the present: all at once, tiled', cascade: 'sheets of the past: each starts before the last ends', split: 'two paths side by side' }[l])}">${l}</button>`).join('')}`
      : `<button data-lay="sequence" title="Add every read shot of this sign, one after another, after the last clip">add family</button><span class="cx-lbl">then arrange with grid / pack / bend</span>`;
    card.innerHTML = `
      <div class="cx-cardhead">
        <div class="cx-sym"><small>${esc(s.n)}</small><b>${esc(s.symbol)}</b></div>
        <div><h3>${esc(s.name)}</h3><p class="cx-dom">${esc(DOMNAME[s.dom])}${s.image ? ' · ' + esc(s.image) : ''}</p></div>
      </div>
      ${s.question ? `<p class="cx-q">${esc(s.question)}</p>` : ''}
      <p class="cx-gloss">${esc(s.gloss)}</p>
      <h4>the deciding test</h4><p>${esc(s.difference)}</p>
      <div class="cx-ceil"><span>single-shot ceiling</span><span class="cx-bar"><i style="width:${+s.ceiling || 0}%"></i></span><b>${esc(s.ceiling)}%</b></div>
      ${s.confusions?.length ? `<h4>confused with</h4><div class="cx-chips">${s.confusions.map(c => chip(c)).join('')}</div>` : ''}
      <h4>family · ${s.family.length} read shot${s.family.length === 1 ? '' : 's'}, best first</h4>
      <div class="cx-actions">${lay}</div>
      <div class="cx-family">${s.family.map((f, i) => `
        <button class="cx-shot" data-i="${i}" title="Add this shot (${tc(Math.max(0, f.read_t - 1.5))}–${tc(Math.min(f.dur, f.read_t + 2.5))} around its reading)">
          <span class="cx-img"><img loading="lazy" alt="" src="${esc(thumbUrl(f.thumb))}"><em>${esc(f.conf)}%</em></span>
          <span class="cx-meta"><b>${esc(f.title)}</b>${f.year ? ' · ' + esc(f.year) : ''}<span>${esc(f.note)}</span>${f.alt ? `<span class="cx-alt">rival ${esc(signOf(f.alt)?.symbol || f.alt)} ${esc(f.alt_conf)}%</span>` : ''}</span>
        </button>`).join('') || '<p class="cx-none">No read shots yet.</p>'}</div>`;
    card.querySelectorAll('.cx-shot').forEach(b => b.onclick = () => addShot(s, s.family[+b.dataset.i]));
    card.querySelectorAll('[data-lay]').forEach(b => b.onclick = () => { V.layout = b.dataset.lay; addFamily(s, b.dataset.lay); });
    card.querySelectorAll('img').forEach(im => im.onerror = () => im.replaceWith(el('span', 'cx-noimg', 'no still')));
  }

  /* ---------- inspect: what the selected clip reads as ---------- */
  function inspect() {
    const box = $p('.cx-inspect'); if (!box || !D) return;
    let sel = null; try { sel = ED.selection(); } catch (e) { /* editor mid-edit */ }
    const key = sel ? sel.id + '|' + sel.name + '|' + JSON.stringify(sel.info) : '';
    if (key === V.inspectKey) return; V.inspectKey = key;
    const was = V.inspected; V.inspected = sel?.info?.n ? String(sel.info.n) : null;
    table.querySelectorAll('.cx-tile.is-inspected').forEach(t => t.classList.remove('is-inspected'));
    if (V.inspected) tileOf(V.inspected)?.classList.add('is-inspected');
    if (!sel) { box.innerHTML = `<p class="cx-quiet">Select a clip in the ${tool === 'cut' ? 'frame' : 'room'} to read it here.</p>`; return; }
    const nm = esc(sel.name.replace(/\.[a-z0-9]+$/i, ''));
    if (!sel.info) { box.innerHTML = `<p class="cx-quiet"><b>${nm}</b> carries no cineosis reading — it did not come from the lab or the table.</p>`; return; }
    const s = signOf(sel.info.n), fam = s?.family.find(f => f.id === sel.info.shot), beat = sel.info.beat && BEAT.get(+sel.info.beat);
    let html = `<div class="cx-reads"><span class="cx-lbl">this clip reads as</span>${s ? chip(s.n, 'cx-big') + `<b>${esc(s.name)}</b>` : esc(sel.info.symbol || sel.info.n || '?')}</div>`;
    if (fam) html += `<p><span class="cx-conf">${esc(fam.conf)}%</span> ${esc(fam.note)}</p>` +
      (fam.alt ? `<p class="cx-rival">rival ${chip(fam.alt)} ${esc(fam.alt_conf)}%${fam.flip ? ` · <i>flips if</i> ${esc(fam.flip)}` : ''}</p>` : '');
    else if (sel.info.note) html += `<p>${esc(sel.info.note)}</p>`;
    if (beat) html += `<p class="cx-beatref">WYGWYL beat #${beat.id} · ${esc(sel.info.role || '')} · ${esc(beat.mode)} · ${beat.codes.map(c => chip(c)).join('')}</p><p class="cx-quiet">${esc(beat.operation || beat.edit || '')}</p>`;
    else if (!fam) html += `<p class="cx-quiet">${esc(sel.info.title || '')} — not in ${esc(s?.symbol || 'the sign')}'s family, so no confidence or rival is recorded.</p>`;
    box.innerHTML = html;
    if (V.inspected && V.inspected !== was && !V.hover) pin(V.inspected, true);
  }

  /* ---------- WYGWYL ---------- */
  function buildWygwyl() {
    const W = D.wygwyl, box = $p('.cx-wy');
    const byCh = W.films.map(() => []); for (const b of W.beats) (byCh[b.chapter] ||= []).push(b);
    box.innerHTML = `
      <div class="cx-wyhead">
        <h3>${esc(W.title)}</h3>
        <p class="cx-quiet">${tc(W.duration).slice(0, 5)} · ${W.films.length} films · ${W.beats.length} beats</p>
        <button class="cx-primary" data-all>load the whole WYGWYL cut</button>
        <p class="cx-quiet">${tool === 'cut'
          ? 'Placed by beat mode: hold = A full frame (repeated to fill) · split = A left, B right · inset = A with B top-right from the midpoint · dissolve = A then B overlapping · montage = A/B in 1.5 s pieces · black = empty. Beat rates are not applied.'
          : 'The room takes the A line only, each clip at its beat time; the room deepens to 30 min.'}</p>
        <p class="cx-note">Neither editor holds the suite's audio track — play it alongside: <a href="../wygwyl/WYGWYL_Suite_Audio.mp3" target="_blank" rel="noopener">suite audio (mp3)</a><span class="cx-film"></span></p>
      </div>
      ${W.films.map((f, i) => `
        <details class="cx-ch" data-ch="${i}">
          <summary><b>${esc(f.n)}</b> ${esc(f.title)} <span>${tc(f.container[0]).slice(0, 5)}–${tc(f.container[1]).slice(0, 5)} · ${byCh[i].length} beats</span></summary>
          <button class="cx-chload" data-ch="${i}">load chapter ${esc(f.n)}</button>
          <div class="cx-beats"></div>
        </details>`).join('')}`;
    box.querySelector('[data-all]').onclick = loadAll;
    box.querySelectorAll('.cx-chload').forEach(b => b.onclick = () => loadChapter(+b.dataset.ch));
    box.querySelectorAll('details.cx-ch').forEach(d => d.addEventListener('toggle', () => {
      const list = d.querySelector('.cx-beats'); if (!d.open || list.childElementCount) return;
      list.innerHTML = byCh[+d.dataset.ch].map(beatRow).join('');
      list.querySelectorAll('[data-beat-add]').forEach(b => b.onclick = () => { const bt = BEAT.get(+b.dataset.beatAdd); loadBeats([bt], `WYGWYL beat #${bt.id}`); });
      list.querySelectorAll('img').forEach(im => im.onerror = () => im.replaceWith(el('span', 'cx-noimg', 'no still')));
    }));
    // the rendered film, when there is one: read the folder listing (lab server) rather than probe the file with a 404
    fetch('../wygwyl/').then(r => r.ok ? r.text() : '').then(t => {
      const has = f => t.includes('href="' + f + '"'), out = [];
      if (has('wygwyl-cut.mp4')) out.push('<a href="../wygwyl/wygwyl-cut.mp4" target="_blank" rel="noopener">the rendered film</a>');
      if (has('player.html')) out.push('<a href="../wygwyl/player.html" target="_blank" rel="noopener">the WYGWYL player</a>');
      if (out.length) box.querySelector('.cx-film').innerHTML = ' · ' + out.join(' · ');
    }).catch(() => {});
  }
  function beatRow(b) {
    const ab = (c, r) => c ? `<span class="cx-ab"><img loading="lazy" alt="" src="${esc(thumbUrl(c.thumb))}"><span><i>${r}</i> ${esc(c.title)}${c.year ? ' · ' + esc(c.year) : ''}</span></span>` : '';
    return `<div class="cx-beat" data-beat="${b.id}">
      <div class="cx-bt-top"><span class="cx-time">${tc(b.start)}–${tc(b.end)}</span><span class="cx-mode m-${esc(b.mode)}">${esc(b.mode)}</span><span class="cx-chips">${(b.codes || []).map(c => chip(c)).join('')}</span></div>
      <div class="cx-bt-title"><b>#${b.id}</b> ${esc(b.title)}</div>
      ${b.mode === 'black' ? '<p class="cx-quiet">black · nothing is placed</p>' : `<div class="cx-abrow">${ab(b.a, 'A')}${tool === 'cut' ? ab(b.b, 'B') : ''}</div>`}
      ${b.edit ? `<p class="cx-edit">${esc(b.edit)}</p>` : ''}
      ${b.mode === 'black' ? '' : `<button data-beat-add="${b.id}">add this beat</button>`}
    </div>`;
  }
  function markNow() {
    if (V.tab !== 'wygwyl' || !D || panel.classList.contains('cx-closed')) return;
    const t = ED.time(), b = D.wygwyl.beats.find(q => t >= q.start && t < q.end);
    const id = b ? String(b.id) : '';
    if (id === V.nowBeat) return; V.nowBeat = id;
    panel.querySelectorAll('.cx-beat.is-now').forEach(e => e.classList.remove('is-now'));
    if (b) panel.querySelector(`.cx-beat[data-beat="${id}"]`)?.classList.add('is-now');
  }

  /* ---------- boot ---------- */
  async function boot() {
    mount();
    status('loading the table…');
    try { D = await (await fetch(new URL('cineosis-index.json', HERE))).json(); }
    catch (e) { status('could not read cineosis-index.json · ' + e.message); return; }
    SIGN = new Map(D.signs.map(s => [String(s.n), s]));
    BEAT = new Map(D.wygwyl.beats.map(b => [b.id, b]));
    buildTable(); buildWygwyl();
    pin(ls.get('cineosis.panel.sign', '1'));
    status('ready');
    setInterval(() => { inspect(); markNow(); }, 400); inspect();
    if (AUTO && !AUTO.skip) {
      if (AUTO.fresh) { status('emptying the editor…'); await ED.clear(); }
      setTab('wygwyl');
      loadAll();
    } else if (AUTO?.skip) status('WYGWYL was already loaded here once · use ?load=wygwyl&fresh=1 to reload it clean');
  }
  window.CineosisPanel = { open: () => setOpen(true), close: () => setOpen(false), pin: n => pin(n, true), loadAll, loadChapter, beatPieces: (b, room) => beatPieces(b, room), wygwylBin: (beats, t) => wygwylBin(beats || D.wygwyl.beats, t || 'test'), data: () => D };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', boot); else boot();
})();
