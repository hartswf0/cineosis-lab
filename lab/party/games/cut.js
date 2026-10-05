/* THE CUT on the Party platform: one film, edited by everyone at once. The stand plays it and shows the timeline; every phone is
   an editing station. Select a clip; trim its in and out, slide it, move it, cut it, set how it comes in, open its own sound,
   slip and level the sounds laid on it. Search the rushes by word and add or replace; lay a voice; start music; write a card.
   Anyone can undo. Share makes the film a link (lab/film.html) that plays anywhere. The other games end here with what they made. */
(function () {
  const { esc, rnd, pick, shuffle, mini } = Party;
  function host(H) {
    const $ = s => document.querySelector(s), P = H.P;
    let F = H.seed || Cut.blank('Untitled'); H.seed = null;
    let R = null, SH = [], url = null; const bins = {}, undo = [], log = [];
    const G = { playing: false, at: -1, link: '', ver: 0 };
    let cardEl = $('#cardv'); if (!cardEl) { cardEl = document.createElement('div'); cardEl.id = 'cardv'; $('#screen').append(cardEl); }
    const player = Cut.Player({ vids: H.VP.slice(0, 3), auds: H.AP, card: cardEl, cap: $('#cap') });
    H.show(null); H.slate('');
    if (!F.clips.length && location.hash.length > 4) Cut.decode(location.hash.slice(1)).then(f => { F = f; history.replaceState(null, '', location.pathname + location.search); draw(); }).catch(() => { });
    fetch('pictures/rushes.json').then(r => r.json()).then(d => { R = d; SH = R.shots.filter(s => s.d >= 1.5); url = v => Array.isArray(v) ? R.r2 + R.P[v[0]] + '/clips/' + v[1] + '.mp4' : R.r2 + v; H.players.forEach(p => fill(p.id)); draw(); });
    const words = s => ((s.w || '') + ' ' + (s.s || []).join(' ') + ' ' + (s.f || '')).toLowerCase();
    function fill(id, q) { if (!R) return; const b = bins[id] = bins[id] || { q: '', shots: [], voices: [], music: [] };
      if (q != null) b.q = String(q).slice(0, 40).toLowerCase().trim();
      const ws = b.q ? b.q.split(/\s+/) : [];
      const hit = ws.length ? SH.filter(s => ws.every(w => words(s).includes(w))) : SH.filter(s => s.sc >= 6);
      b.shots = shuffle(hit).slice(0, 12).map(s => SH.indexOf(s));
      const lh = ws.length ? R.lines.filter(l => ws.some(w => l.x.toLowerCase().includes(w))) : R.lines; b.voices = shuffle(lh.map((l, i) => R.lines.indexOf(l))).slice(0, 10);
      const mh = ws.length ? R.music.filter(m => ws.some(w => (m.f || '').toLowerCase().includes(w))) : R.music; b.music = shuffle(mh.map(m => R.music.indexOf(m))).slice(0, 8); }
    // ---- an edit from anyone; the film changes, the stand says who did what, anyone can undo it
    function edit(p, op) {
      if (op.op === 'undo') { const last = undo.pop(); if (!last) return; F = JSON.parse(last.film); say(p, 'undid: ' + last.what); return draw(); }
      if (op.op === 'add' || op.op === 'replace' || op.op === 'voice' || op.op === 'music' || op.op === 'card') op = resolve(p, op); if (!op) return;
      const before = JSON.stringify(F), what = Cut.apply(F, op); if (!what) return;
      undo.push({ film: before, what: (p ? p.name + ' ' : '') + what }); if (undo.length > 60) undo.shift();
      G.ver++; say(p, what); if (G.playing && op.op !== 'title') { /* keep playing the old cut until stopped */ } draw(); }
    function resolve(p, op) { const b = bins[p.id] || {};
      if (op.op === 'add' || op.op === 'replace') { const s = SH[op.key]; if (!s) return null; const d = s.d || 4, t0 = Math.max(0, +(d / 2 - 1.5).toFixed(2)), it = Cut.shot(url(s.v), t0, Math.min(d, t0 + 3), { d, by: p.id, label: s.w || s.f });
        return op.op === 'add' ? { op: 'insert', after: op.after, item: it } : { op: 'replace', id: op.id, item: it }; }
      if (op.op === 'voice') { const l = R.lines[op.key]; if (!l) return null; return { op: 'sound', sound: Cut.voice(op.id, url(l.v), l.t0, l.t1, { text: l.x, off: .3, by: p.id }) }; }
      if (op.op === 'music') { const m = R.music[op.key]; if (!m) return null; return { op: 'sound', sound: Cut.music(op.id, url(m.v), Math.min(4, Math.max(0, (m.d || 20) - 32)), 30, { text: null, label: m.f, by: p.id }) }; }
      if (op.op === 'card') return { op: 'insert', after: op.after, item: Cut.card(String(op.text || '').slice(0, 120) || '…', 2.5, { by: p.id }) };
      return null; }
    function say(p, what) { log.unshift({ who: p ? p.id : null, what: (p ? p.name + ' ' : '') + what }); if (log.length > 30) log.pop(); if (p) H.act(p.id, 'hit', 260); H.logLine((p ? mini(p.av) + ' ' : '') + esc(what)); }
    function playFrom(k) { if (!F.clips.length) return; G.playing = true; H.show(null); player.play(F, k || 0, { onTick: (t, i) => { if (i !== G.at) { G.at = i; drawSide(); H.broadcast(); } }, onEnd: () => { G.playing = false; G.at = -1; draw(); } }); draw(); }
    function stopPlay() { player.stop(); G.playing = false; G.at = -1; draw(); }
    function preview(p, key) { if (G.playing) return; const s = SH[key]; if (!s) return; const d = s.d || 4, t0 = Math.max(0, d / 2 - 1.5); player.play({ title: '', clips: [Cut.shot(url(s.v), t0, Math.min(d, t0 + 3))], sounds: [] }, 0, { onEnd: () => draw() }); }
    async function share() { G.link = location.origin + location.pathname.replace(/party\.html$/, '') + 'film.html#' + await Cut.encode(F); say(null, 'shared the film'); draw(); }
    // ---- the stand's sheet: the timeline, top to bottom
    function drawSide() { const S = Cut.starts(F);
      const rows = F.clips.map((c, k) => { const ss = F.sounds.filter(s => s.clip === c.id), by = P(c.by);
        return `<div class="tk ${k === G.at ? 'now' : ''}" style="align-items:flex-start"><span class="n" style="font-size:18px">${k + 1}</span>${c.kind === 'card' ? `<span class="strip"><i style="background:#111;color:#f4ecd8;display:grid;place-items:center;font-size:10px;max-width:56px">card</i></span>` : `<span class="strip"><i style="background-image:url('${esc(Cut.thumbOf(c.u))}');max-width:56px"></i></span>`}
          <span style="flex:1;min-width:0;font-size:14px;line-height:1.2">${c.kind === 'card' ? '“' + esc(c.text) + '”' : esc((c.label || '').slice(0, 40))}<br><span class="hint" style="margin:0">${Cut.len(c).toFixed(1)}s${c.tr !== 'cut' ? ' · ' + c.tr : ''}${c.own ? ' · own sound' : ''}${ss.map(s => ' · ' + (s.kind === 'music' ? '♪' : 'voice')).join('')}${by ? ' · ' + esc(by.name) : ''}</span></span></div>`; }).join('');
      const S2 = H.side(`<div class="ph">${esc(F.title)} <small>${F.clips.length} clips · ${Cut.starts(F).total.toFixed(1)}s</small></div>
        <div class="row" style="margin-bottom:6px"><button class="btn chip" id="cPlay">${G.playing ? '■ stop' : '▶ play'}</button><button class="btn chip" id="cUndo" ${undo.length ? '' : 'disabled'}>undo</button><button class="btn chip" id="cShare">share</button><button class="btn chip" id="cLobby">lobby</button></div>
        ${G.link ? `<div class="hint" style="text-align:left;word-break:break-all">Film link (on every phone too): <a href="${esc(G.link)}" target="_blank" style="color:var(--verm)">open</a> · ${G.link.length} characters</div>` : ''}
        <div class="takes">${rows || '<div class="hint">The timeline is empty. Phones: Add → pick a shot.</div>'}</div>
        <div class="ph" style="margin-top:8px">Edits <small>${undo.length} to undo</small></div><div style="font-size:13px">${log.slice(0, 8).map(l => `<div>${esc(l.what)}</div>`).join('')}</div>`, 'cut');
      $('#cPlay').onclick = () => G.playing ? stopPlay() : playFrom(0); $('#cUndo').onclick = () => edit(null, { op: 'undo' }); $('#cShare').onclick = share; $('#cLobby').onclick = () => H.end(); }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); if (!G.playing && !F.clips.length) H.slate(H.card(`<div class="big">${esc(F.title)}<small>empty · add shots from your phone</small></div>`, 'night')); else if (!G.playing) H.slate(H.card(`<div class="big">${esc(F.title)}<small>${F.clips.length} clips · ${Cut.starts(F).total.toFixed(1)}s</small></div>`, 'night')); }
    function stateFor(p) { if (!bins[p.id]) fill(p.id); const b = bins[p.id] || {};
      return { phase: 'cut', noScore: true, ver: G.ver, title: F.title, total: +Cut.starts(F).total.toFixed(1), at: G.at, playing: G.playing, link: G.link, undo: undo.length ? undo[undo.length - 1].what : '',
        clips: F.clips.map(c => ({ id: c.id, kind: c.kind, th: c.u ? Cut.thumbOf(c.u) : '', text: c.text, l: +Cut.len(c).toFixed(2), t0: c.t0, t1: c.t1, d: c.d, tr: c.tr, own: !!c.own, label: c.label || '',
          ss: F.sounds.filter(s => s.clip === c.id).map(s => ({ id: s.id, kind: s.kind, label: s.text || s.label || (s.kind === 'music' ? 'music' : 'voice'), off: s.off, vol: s.vol, l: +Cut.slen(s).toFixed(1) })) })),
        bin: R ? { q: b.q, shots: (b.shots || []).map(i => ({ key: i, th: Cut.thumbOf(url(SH[i].v)), w: SH[i].w })), voices: (b.voices || []).map(i => ({ key: i, x: R.lines[i].x, f: R.lines[i].f })), music: (b.music || []).map(i => ({ key: i, f: R.music[i].f })) } : null }; }
    function onMsg(p, m) {
      if (m.t === 'op') edit(p, m.o || {});
      if (m.t === 'search') { fill(p.id, m.q); H.send(p, stateFor(p)); }
      if (m.t === 'play') playFrom(m.k || 0); if (m.t === 'stop') stopPlay(); if (m.t === 'share') share(); if (m.t === 'preview') preview(p, m.key);
    }
    draw();
    return { stateFor, draw, onMsg, house: false, throwable: () => false, crowdTarget: () => null, performer: () => null, onJoin: p => fill(p.id), stop() { player.stop(); H.VP.forEach(v => v.style.transition = ''); cardEl.classList.remove('on'); } };
  }

  // ======================================================== THE PHONE: an editing station
  let sel = null, mode = 'edit', binTab = 'shots', pickKey = null, known = null, want = false;
  function phone(S, api) {
    const { esc } = api;
    if (S.phase !== 'cut') return null;
    return { key: 'cut', cls: 'cutp', takeover: { key: 'cut', render(el) { build(el, S, api); }, patch(el) { build(el, api.S(), api, true); } } };
  }
  const fmt = n => (Math.round(n * 100) / 100).toFixed(2);
  function build(el, S, api, isPatch) {
    const { esc } = api, send = o => { api.buzz(8); api.send({ t: 'op', o }); };
    if (!el.querySelector('#cTop')) el.innerHTML = `<div id="cTop" class="row" style="flex-wrap:nowrap"><input type="text" id="cTitle" maxlength="80" style="flex:1"><button class="btn chip" id="cPlay"></button><button class="btn chip" id="cUndo">undo</button></div>
      <div id="cStrip" class="cstrip"></div><div class="row" style="margin:6px 0"><button class="btn chip" data-mode="edit">Edit</button><button class="btn chip" data-mode="add">Add</button><button class="btn chip" id="cShare">Share</button><span id="cTot" class="hint" style="margin:0 0 0 auto"></span></div><div id="cBody"></div><div id="cLink"></div>`;
    const active = document.activeElement;
    const t = el.querySelector('#cTitle'); if (active !== t) t.value = S.title; t.onchange = () => send({ op: 'title', text: t.value });
    el.querySelector('#cPlay').textContent = S.playing ? '■' : '▶ all'; el.querySelector('#cPlay').onclick = () => api.send(S.playing ? { t: 'stop' } : { t: 'play', k: 0 });
    el.querySelector('#cUndo').disabled = !S.undo; el.querySelector('#cUndo').onclick = () => send({ op: 'undo' });
    el.querySelector('#cShare').onclick = () => api.send({ t: 'share' });
    el.querySelector('#cTot').textContent = S.clips.length + ' clips · ' + S.total + 's';
    el.querySelectorAll('[data-mode]').forEach(b => { b.classList.toggle('on', b.dataset.mode === mode); b.onclick = () => { mode = b.dataset.mode; build(el, api.S(), api); }; });
    const fresh = known ? S.clips.filter(c => !known.has(c.id)) : []; known = new Set(S.clips.map(c => c.id)); if (want && fresh.length) { sel = fresh[0].id; want = false; }
    if (sel && !S.clips.some(c => c.id === sel)) sel = null; if (!sel && S.clips.length) sel = S.clips[S.clips.length - 1].id;
    // the strip: every clip, as wide as it is long
    const strip = el.querySelector('#cStrip'), sx = strip.scrollLeft;
    strip.innerHTML = S.clips.map((c, k) => `<button class="cc ${c.id === sel ? 'sel' : ''} ${k === S.at ? 'now' : ''}" data-id="${c.id}" style="width:${Math.max(44, Math.min(140, c.l * 26))}px">${c.kind === 'card' ? `<span class="ct">${esc(c.text)}</span>` : `<img alt="" src="${esc(c.th)}">`}<b>${c.l.toFixed(1)}</b>${c.ss.length ? `<i>${c.ss.map(s => s.kind === 'music' ? '♪' : '“').join('')}</i>` : ''}${c.tr !== 'cut' ? `<u>${c.tr === 'dissolve' ? '⟋' : '▮'}</u>` : ''}</button>`).join('') || '<span class="hint" style="margin:8px">empty · tap Add</span>';
    strip.scrollLeft = sx;
    strip.querySelectorAll('[data-id]').forEach(b => b.onclick = () => { sel = b.dataset.id; mode = 'edit'; build(el, api.S(), api); });
    const body = el.querySelector('#cBody'); if (body.contains(active) && active.tagName === 'INPUT') return;
    const c = S.clips.find(x => x.id === sel), k = S.clips.findIndex(x => x.id === sel);
    if (mode === 'edit') {
      if (!c) { body.innerHTML = '<div class="hint">Nothing selected. Add a shot.</div>'; return; }
      const step = (lbl, edge) => `<div class="ed"><span>${lbl}</span><button data-trim="${edge}" data-d="-0.5">−½</button><button data-trim="${edge}" data-d="-0.1">−⅒</button><b>${edge === 'in' ? fmt(c.t0) : fmt(c.t1)}</b><button data-trim="${edge}" data-d="0.1">+⅒</button><button data-trim="${edge}" data-d="0.5">+½</button></div>`;
      body.innerHTML = `<div class="ed"><span>clip ${k + 1}</span><button data-mv="-1">◀</button><button data-mv="1">▶</button><button data-del>cut</button><button data-from>▶ from here</button></div>
        ${c.kind === 'card' ? `<div class="ed"><span>hold</span><button data-trim="out" data-d="-0.5">−½</button><b>${fmt(c.l)}s</b><button data-trim="out" data-d="0.5">+½</button></div><div class="row"><input type="text" id="cText" maxlength="120" value="${esc(c.text)}"><button class="btn chip" id="cTextB">set</button></div>`
          : `${step('in', 'in')}${step('out', 'out')}<div class="ed"><span>slide</span><button data-slide="-0.5">◀ ½</button><b>${fmt(c.l)}s</b><button data-slide="0.5">½ ▶</button></div><div class="hint" style="text-align:left;margin:0">${esc(c.label)}${c.d ? ' · source ' + c.d.toFixed(1) + 's' : ''}</div>`}
        <div class="ed"><span>in by</span>${['cut', 'dissolve', 'dip'].map(x => `<button data-tr="${x}" class="${c.tr === x ? 'on' : ''}">${x}</button>`).join('')}</div>
        ${c.kind === 'shot' ? `<div class="ed"><span>own sound</span><button data-own="1" class="${c.own ? 'on' : ''}">on</button><button data-own="0" class="${!c.own ? 'on' : ''}">off</button><button data-replace>replace…</button></div>` : ''}
        ${c.ss.map(s => `<div class="ed snd"><span>${s.kind === 'music' ? '♪ ' : '“'}${esc(s.label.slice(0, 26))}${s.kind === 'music' ? '' : '”'}</span><button data-soff="${s.id}" data-d="-0.25">◀</button><b>${s.off >= 0 ? '+' : ''}${fmt(s.off)}</b><button data-soff="${s.id}" data-d="0.25">▶</button><button data-svol="${s.id}" data-d="-0.2">−</button><b>${Math.round((s.vol == null ? 1 : s.vol) * 100)}%</b><button data-svol="${s.id}" data-d="0.2">+</button>${s.kind === 'music' ? `<button data-slen="${s.id}" data-d="-5">−5s</button><button data-slen="${s.id}" data-d="5">+5s</button>` : ''}<button data-sdel="${s.id}">✕</button></div>`).join('')}
        <div class="row"><button class="btn chip" data-go="voices">+ voice on this clip</button><button class="btn chip" data-go="music">+ music from here</button><button class="btn chip" data-go="card">+ card after</button></div>`;
      body.querySelectorAll('[data-trim]').forEach(b => b.onclick = () => send({ op: 'trim', id: c.id, edge: b.dataset.trim, d: +b.dataset.d }));
      body.querySelectorAll('[data-slide]').forEach(b => b.onclick = () => send({ op: 'slide', id: c.id, d: +b.dataset.slide }));
      body.querySelectorAll('[data-mv]').forEach(b => b.onclick = () => send({ op: 'move', id: c.id, d: +b.dataset.mv }));
      const del = body.querySelector('[data-del]'); if (del) del.onclick = () => send({ op: 'del', id: c.id });
      body.querySelector('[data-from]').onclick = () => api.send({ t: 'play', k });
      body.querySelectorAll('[data-tr]').forEach(b => b.onclick = () => send({ op: 'tr', id: c.id, tr: b.dataset.tr }));
      body.querySelectorAll('[data-own]').forEach(b => b.onclick = () => send({ op: 'own', id: c.id, on: b.dataset.own === '1' }));
      const rp = body.querySelector('[data-replace]'); if (rp) rp.onclick = () => { mode = 'add'; binTab = 'shots'; pickKey = 'replace'; build(el, api.S(), api); };
      body.querySelectorAll('[data-soff]').forEach(b => b.onclick = () => send({ op: 'soff', sid: b.dataset.soff, d: +b.dataset.d }));
      body.querySelectorAll('[data-svol]').forEach(b => b.onclick = () => send({ op: 'svol', sid: b.dataset.svol, d: +b.dataset.d }));
      body.querySelectorAll('[data-slen]').forEach(b => b.onclick = () => send({ op: 'slen', sid: b.dataset.slen, d: +b.dataset.d }));
      body.querySelectorAll('[data-sdel]').forEach(b => b.onclick = () => send({ op: 'sdel', sid: b.dataset.sdel }));
      body.querySelectorAll('[data-go]').forEach(b => b.onclick = () => { mode = 'add'; binTab = b.dataset.go; build(el, api.S(), api); });
      const tb = body.querySelector('#cTextB'); if (tb) tb.onclick = () => send({ op: 'text', id: c.id, text: body.querySelector('#cText').value });
    } else {
      const B = S.bin; if (!B) { body.innerHTML = '<div class="hint">loading the rushes…</div>'; return; }
      const target = c ? 'after clip ' + (k + 1) : 'at the start';
      body.innerHTML = `<div class="row">${['shots', 'voices', 'music', 'card'].map(x => `<button class="btn chip ${binTab === x ? 'on' : ''}" data-bt="${x}">${x}</button>`).join('')}</div>
        ${binTab !== 'card' ? `<div class="row" style="margin-top:6px"><input type="text" id="cQ" placeholder="search: dog, door, crowd, water…" value="${esc(B.q || '')}"><button class="btn chip" id="cQB">find</button></div>` : ''}
        ${binTab === 'shots' ? `<div class="hint" style="text-align:left;margin:4px 0">${pickKey === 'replace' && c ? 'tap a shot to replace clip ' + (k + 1) : 'tap a shot to add it ' + target}</div><div class="tiles">${B.shots.map(s => `<button class="tile" data-add="${s.key}"><img alt="" src="${esc(s.th)}"><span>${esc(s.w || '')}</span></button>`).join('')}</div>` : ''}
        ${binTab === 'voices' ? `<div class="hint" style="text-align:left;margin:4px 0">${c ? 'tap a voice to lay it on clip ' + (k + 1) : 'add a shot first'}</div>${B.voices.map(v => `<button class="btn" data-voice="${v.key}" style="display:block;width:100%;text-align:left;margin-top:5px;font-size:15px" ${c ? '' : 'disabled'}>“${esc(v.x)}” <small style="color:#6d6052">${esc(v.f)}</small></button>`).join('')}` : ''}
        ${binTab === 'music' ? `<div class="hint" style="text-align:left;margin:4px 0">${c ? 'tap music to start it at clip ' + (k + 1) : 'add a shot first'}</div>${B.music.map(m => `<button class="btn" data-music="${m.key}" style="display:block;width:100%;text-align:left;margin-top:5px;font-size:15px" ${c ? '' : 'disabled'}>♪ ${esc(m.f)}</button>`).join('')}` : ''}
        ${binTab === 'card' ? `<div class="row" style="margin-top:6px"><input type="text" id="cCard" maxlength="120" placeholder="Chapter one · That night · The end"><button class="btn chip" id="cCardB">add ${esc(target)}</button></div>` : ''}`;
      body.querySelectorAll('[data-bt]').forEach(b => b.onclick = () => { binTab = b.dataset.bt; pickKey = null; build(el, api.S(), api); });
      const q = body.querySelector('#cQ'), qb = body.querySelector('#cQB'); if (qb) { const go = () => api.send({ t: 'search', q: q.value }); qb.onclick = go; q.onkeydown = e => { if (e.key === 'Enter') { go(); q.blur(); } }; }
      body.querySelectorAll('[data-add]').forEach(b => b.onclick = () => { const key = +b.dataset.add; if (pickKey === 'replace' && c) { send({ op: 'replace', id: c.id, key }); pickKey = null; mode = 'edit'; } else { want = true; send({ op: 'add', after: c ? c.id : null, key }); } });
      body.querySelectorAll('[data-voice]').forEach(b => b.onclick = () => { send({ op: 'voice', id: c.id, key: +b.dataset.voice }); mode = 'edit'; build(el, api.S(), api); });
      body.querySelectorAll('[data-music]').forEach(b => b.onclick = () => { send({ op: 'music', id: c.id, key: +b.dataset.music }); mode = 'edit'; build(el, api.S(), api); });
      const cb = body.querySelector('#cCardB'); if (cb) cb.onclick = () => { want = true; send({ op: 'card', after: c ? c.id : null, text: body.querySelector('#cCard').value }); mode = 'edit'; };
    }
    const L = el.querySelector('#cLink'); L.innerHTML = S.link ? `<div class="row" style="margin-top:8px"><a class="btn chip" href="${esc(S.link)}" target="_blank" style="text-decoration:none">open the film ↗</a><button class="btn chip" id="cCopy">copy link</button></div>` : '';
    const cp = L.querySelector('#cCopy'); if (cp) cp.onclick = () => { try { navigator.clipboard.writeText(S.link); cp.textContent = 'copied'; } catch (e) { } };
  }
  Party.games.cut = { title: 'The Cut', blurb: 'one film, edited by everyone at once · trim, order, sound, titles · share it as a link', host, phone };
})();
