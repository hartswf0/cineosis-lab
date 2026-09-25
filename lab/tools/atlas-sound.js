/* CUT · the sound desk: the WYGWYL · ATLAS sound experiments as tracks on CUT's own clock.
 *
 * Every track is one experiment, placed on the 24:00 suite clock the atlas shares with the WYGWYL cut
 * (clock.json spans = the fourteen films):
 *   suite · drone · reading (RY, at each poem's window) · codex (sung lines where the reading says them)
 *   one cut · duets · radio atlantis · transmission · poem worlds (referred sounds as beds)
 *   fx (sounds dropped from the sonic library) · archive (the footage's own sound, CUT's clips)
 * Voice tracks key a sidechain: tracks marked "duck" drop under the voice. The mix follows CUT.S.time and
 * CUT.S.playing, and plays through CUT's AudioContext, so CUT's Export records the picture with this mix.
 * The mix saves in this browser and exports/imports as a fresco-score v0.1 (the atlas's shared clock format).
 */
(() => {
  'use strict';
  const HERE = document.currentScript?.src || location.href;
  const ATLAS = 'https://hartswf0.github.io/butterfly-halfworld/wygwyl/';
  const SUITE = new URL('../wygwyl/WYGWYL_Suite_Audio.mp3', HERE).href;
  const KEY = 'cineosis.sound.v1';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tc = t => { t = Math.max(0, t || 0); const m = Math.floor(t / 60); return String(m).padStart(2, '0') + ':' + String(Math.floor(t % 60)).padStart(2, '0'); };
  const abs = f => /^https?:/.test(f) ? f : ATLAS + f.split('/').map(encodeURIComponent).join('/');
  const ls = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
               set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } } };

  /* ---------- the tracks ---------- */
  const TRACKS = [
    { id: 'suite', name: 'Suite', note: 'the album the cut was timed to', lane: 'score' },
    { id: 'drone', name: 'Drone', note: 'the unified drone · the atlas’s master axis', lane: 'score', duck: true },
    { id: 'reading', name: 'Reading', note: 'the RY reading, at each poem’s window', lane: 'voice', key: true },
    { id: 'codex', name: 'Codex', note: 'sung lines, where the reading says them', lane: 'voice', key: true },
    { id: 'onecut', name: 'One cut', note: 'her reading as spine, the song carrying the strong lines', lane: 'voice', key: true },
    { id: 'duets', name: 'Duets', note: 'her line, then another mouth answering', lane: 'voice', key: true },
    { id: 'radio', name: 'Radio Atlantis', note: 'fourteen scores from the samples · voice included', lane: 'score' },
    { id: 'transmission', name: 'Transmission', note: 'the readings as broadcast radio · voice included', lane: 'score' },
    { id: 'worlds', name: 'Poem worlds', note: 'each poem’s referred sounds as beds', lane: 'beds', duck: true },
    { id: 'fx', name: 'FX', note: 'sounds you drop from the library', lane: 'fx', duck: true },
    { id: 'archive', name: 'Archive', note: 'the footage’s own sound (CUT’s clips)', lane: 'archive', duck: true }
  ];
  const PRESETS = [
    ['Suite', { suite: 1, archive: .5 }],
    ['Reading + drone', { drone: .7, reading: 1, archive: .4 }],
    ['Codex ghosts', { drone: .6, reading: 1, codex: .75 }],
    ['One cut', { onecut: 1, drone: .45 }],
    ['Duets', { duets: 1, drone: .4 }],
    ['Radio Atlantis', { radio: 1 }],
    ['Transmission', { transmission: 1 }],
    ['Poem worlds', { reading: 1, worlds: .55, drone: .35 }],
    ['Archive only', { archive: 1 }]
  ];
  const saved = ls.get(KEY, {});
  const T = Object.fromEntries(TRACKS.map(t => [t.id, { ...t, on: false, gain: 1, solo: false, duck: !!t.duck, clips: [], ...(saved.tracks?.[t.id] || {}), clips: [] }]));
  if (!saved.tracks) { T.suite.on = true; T.archive.on = true; T.archive.gain = .5; }
  const FX = saved.fx || [];
  let IMPORTED = saved.imported || [];            // fresco tracks loaded from files: {id,name,clips}
  IMPORTED.forEach(addImported);

  /* ---------- data → clips on the clock ---------- */
  let ready = false, D = null;
  async function load() {
    const j = u => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const [clock, samples, worlds, idx] = await Promise.all([j(ATLAS + 'clock.json'), j(ATLAS + 'samples.json').catch(() => null),
      j(ATLAS + 'poemworlds.json').catch(() => null), j(new URL('cineosis-index.json', HERE).href)]);
    const films = idx.wygwyl.films, dur = clock.duration || 1440.07;
    const readDur = Object.fromEntries((samples?.tracks || []).map(t => [t.num, t.dur]));
    const span = n => clock.spans.find(s => s.num === n);
    const poem0 = n => { const f = films.find(x => x.n === n); return f?.poem?.[0] ?? span(n)?.t0 ?? 0; };
    const fit = (at, len, n, extra = {}) => { const end = span(n).t1, e = Math.max(.1, Math.min(len ?? end - at, end - at));
      return { at: +at.toFixed(3), s: 0, e: +e.toFixed(3), fadeIn: .05, fadeOut: len && len > end - at ? 1.5 : .3, gain: 1, ...extra }; };
    T.suite.clips = [{ at: 0, src: SUITE, s: 0, e: dur, fadeIn: .02, fadeOut: .5, gain: 1, label: 'WYGWYL suite' }];
    T.drone.clips = [{ at: 0, src: abs(clock.drone), s: 0, e: dur, fadeIn: .02, fadeOut: .5, gain: 1, label: 'unified drones' }];
    for (const s of clock.spans) {
      const n = s.num, p0 = poem0(n);
      T.reading.clips.push({ ...fit(p0, readDur[n], n), src: abs(s.reading), label: `${n} reading` });
      for (const m of s.mouths || []) if (m.read) T.codex.clips.push({ ...fit(p0 + m.read[0], m.dur, n), src: abs(m.file), label: m.text });
      T.onecut.clips.push({ ...fit(p0, null, n), src: abs(`onecut/${n}.mp3`), label: `${n} one cut` });
      T.duets.clips.push({ ...fit(s.t0, null, n), src: abs(`duets/${n}.mp3`), label: `${n} duets` });
      T.radio.clips.push({ ...fit(s.t0, null, n), src: abs(`radio/${n}.mp3`), label: `${n} radio atlantis` });
      T.transmission.clips.push({ ...fit(s.t0, null, n), src: abs(`transmission/${n}.mp3`), label: `${n} transmission` });
      const w = worlds?.worlds?.find(x => x.num === n);
      if (w) {                                     // referred sounds laid end to end across the span, 20 s each at most
        let at = s.t0;
        for (const snd of (w.sounds || []).filter(x => !/\.ogg($|\?)/i.test(x.file))) {
          if (at >= s.t1 - 2) break;
          const len = Math.min(20, s.t1 - at);
          T.worlds.clips.push({ at: +at.toFixed(3), s: 0, e: +len.toFixed(3), fadeIn: 1.5, fadeOut: 1.5, gain: .8, src: abs(snd.file), label: snd.label || snd.id, loop: true });
          at += len;
        }
      }
    }
    T.fx.clips = FX;
    D = { dur, clock };
    ready = true;
  }

  /* ---------- the audio graph ---------- */
  let ctx = null, master = null, keyBus = null, analyser = null, buf = null, duckVal = 1, wiredDest = null;
  const bus = {};
  function graph() {
    if (ctx) return true;
    const C = window.CUT; if (!C) return false;
    ctx = C.S.ac || new (window.AudioContext || window.webkitAudioContext)();
    C.S.ac = ctx;                                    // CUT's Export records from this context
    master = ctx.createGain(); master.connect(ctx.destination);
    keyBus = ctx.createGain(); analyser = ctx.createAnalyser(); analyser.fftSize = 1024; keyBus.connect(analyser);
    buf = new Float32Array(analyser.fftSize);
    for (const t of all()) mkBus(t);
    return true;
  }
  function mkBus(t) {
    if (!ctx || bus[t.id]) return;
    const g = ctx.createGain(), d = ctx.createGain(), m = ctx.createAnalyser(); m.fftSize = 512;
    g.connect(d); d.connect(master); d.connect(m);
    if (t.key) g.connect(keyBus);
    bus[t.id] = { g, d, m, a: new Float32Array(512) };
  }
  ['pointerdown', 'keydown'].forEach(ev => addEventListener(ev, () => { if (graph() && ctx.state !== 'running') ctx.resume().catch(() => {}); }, true));

  const all = () => [...TRACKS.map(t => T[t.id]), ...IMPORTED.map(i => T[i.id])].filter(Boolean);
  const anySolo = () => all().some(t => t.solo && t.on);
  const audible = t => t.on && (!anySolo() || t.solo);
  const voices = new Map();                          // clip key → {el, node, gain, clip, track, last}
  const failed = new Set();
  function voiceFor(t, c, k) {
    let v = voices.get(k); if (v) return v;
    const el = new Audio(); el.crossOrigin = 'anonymous'; el.preload = 'auto'; el.loop = !!c.loop; el.src = c.src;
    el.addEventListener('error', () => { failed.add(c.src); drop(k); });
    const node = ctx.createMediaElementSource(el), gain = ctx.createGain(); gain.gain.value = 0;
    node.connect(gain); gain.connect(bus[t.id].g);
    v = { el, node, gain, clip: c, track: t, last: 0 }; voices.set(k, v); return v;
  }
  function drop(k) {
    const v = voices.get(k); if (!v) return;
    try { v.el.pause(); v.el.removeAttribute('src'); v.el.load(); v.node.disconnect(); v.gain.disconnect(); } catch (e) { /* already gone */ }
    voices.delete(k);
  }
  const rms = (an, a) => { an.getFloatTimeDomainData(a); let s = 0; for (let i = 0; i < a.length; i++) s += a[i] * a[i]; return Math.sqrt(s / a.length); };

  function tick() {
    requestAnimationFrame(tick);
    const C = window.CUT; if (!C || !ready) return;
    const t = C.S.time, playing = C.S.playing && !C.S.rec?.paused;
    // archive: CUT's own clips, scaled in its drive loop
    const A = T.archive;
    C.S.archiveGain = audible(A) ? A.gain * (A.duck ? duckVal : 1) : 0;
    if (!ctx) { if (playing) graph(); if (!ctx) return; }
    if (C.S.dest && wiredDest !== C.S.dest) { master.connect(C.S.dest); wiredDest = C.S.dest; }
    const now = performance.now();
    for (const tr of all()) {
      if (tr.id === 'archive') continue;
      mkBus(tr);
      const b = bus[tr.id], on = audible(tr);
      b.g.gain.setTargetAtTime(on ? tr.gain : 0, ctx.currentTime, .05);
      b.d.gain.setTargetAtTime(tr.duck ? duckVal : 1, ctx.currentTime, .08);
      if (!on) continue;
      tr.clips.forEach((c, i) => {
        const len = c.e - c.s, k = tr.id + ':' + i + ':' + c.src;
        if (failed.has(c.src) || t < c.at - 1.5 || t > c.at + len + .5) return;
        if (!playing && !voices.has(k)) return;        // paused: nothing new starts
        const v = voiceFor(tr, c, k); v.last = now;
        const rel = t - c.at, inside = rel >= 0 && rel < len;
        const env = !inside ? 0 : Math.min(1, c.fadeIn ? rel / c.fadeIn : 1, c.fadeOut ? (len - rel) / c.fadeOut : 1);
        v.gain.gain.setTargetAtTime(env * (c.gain ?? 1), ctx.currentTime, .02);
        let want = c.s + Math.max(0, rel);
        if (c.loop && v.el.duration) want = want % v.el.duration;
        if (playing && inside) {
          if (v.el.paused) { try { v.el.currentTime = want; } catch (e) { /* not ready */ } v.el.play().catch(() => {}); }
          else if (Math.abs(v.el.currentTime - want) > .3 && !v.el.seeking) v.el.currentTime = want;
        } else if (!v.el.paused) v.el.pause();
      });
    }
    for (const [k, v] of voices) {                   // release what the playhead has left, or what was switched off
      if (now - v.last > 2000 || !audible(v.track)) drop(k);
    }
    // sidechain: the voice tracks push the ducked tracks down ~10 dB
    const lvl = rms(analyser, buf), target = lvl > .012 ? .32 : 1;
    duckVal += (target - duckVal) * (target < duckVal ? .35 : .04);
    meters();
  }
  requestAnimationFrame(tick);

  /* ---------- the desk ---------- */
  let host = null, overview = null, libList = null, LIB = null;
  function save() {
    const tracks = Object.fromEntries(all().map(t => [t.id, { on: t.on, gain: t.gain, solo: t.solo, duck: t.duck }]));
    ls.set(KEY, { tracks, fx: FX, imported: IMPORTED });
  }
  function preset(map) {
    for (const t of all()) { t.on = t.id in map; t.solo = false; if (t.on) t.gain = map[t.id]; }
    save(); render(); window.CineosisPanel?.status('sound: ' + Object.keys(map).join(' + '));
  }
  function row(t) {
    const n = t.clips.length;
    return `<div class="sd-tr${t.on ? ' on' : ''}" data-id="${esc(t.id)}">
      <button class="sd-on" title="${t.on ? 'turn off' : 'turn on'}">${t.on ? '●' : '○'}</button>
      <span class="sd-nm"><b>${esc(t.name)}</b><small>${esc(t.note)}${t.id === 'archive' ? '' : ` · ${n} clip${n === 1 ? '' : 's'}`}</small></span>
      <input type="range" min="0" max="1.5" step="0.05" value="${t.gain}" title="gain" aria-label="${esc(t.name)} gain">
      <button class="sd-s${t.solo ? ' act' : ''}" title="solo">S</button>
      ${t.key ? '<span class="sd-k" title="this track is the voice: ducked tracks drop under it">voice</span>' : `<button class="sd-d${t.duck ? ' act' : ''}" title="duck under the voice">duck</button>`}
      <i class="sd-m"><i></i></i></div>`;
  }
  function render() {
    host = window.CineosisPanel?.soundHost?.(); if (!host) return;
    host.innerHTML = `
      <div class="sd-head"><b>SOUND DESK</b> · the WYGWYL atlas on CUT’s clock
        <span class="sd-state">${ready ? '' : 'loading the atlas…'}</span></div>
      <p class="cx-lbl">Pick a mix, or switch tracks on and set their levels. Tracks follow the playhead. Export (top bar) records the picture with this sound.</p>
      <div class="sd-pre">${PRESETS.map(([n], i) => `<button data-p="${i}">${esc(n)}</button>`).join('')}</div>
      <canvas class="sd-ov" height="${14 * all().length + 8}" aria-label="The tracks on the 24-minute clock · click to move the playhead"></canvas>
      <div class="sd-trs">${all().map(row).join('')}</div>
      <p class="sd-fail" hidden></p>
      <h4 class="sd-h">Sound library · <span class="sd-libn"></span></h4>
      <input type="search" class="cx-fq sd-q" placeholder="search the atlas sounds · keynote, signal, soundmark, loop, a word…">
      <div class="sd-lib"></div>
      <h4 class="sd-h">FX on the clock · ${FX.length}</h4>
      <div class="sd-fx">${FX.map((c, i) => `<div class="sd-fxr"><span>${tc(c.at)}</span><b>${esc(c.label)}</b><button data-fx="${i}" title="remove">×</button></div>`).join('') || '<p class="cx-none">Nothing yet: + a sound from the library at the playhead.</p>'}</div>
      <h4 class="sd-h">Score files</h4>
      <div class="sd-files"><button data-x="export">Export fresco score</button><button data-x="import">Import fresco score</button>
        <button data-x="atlas-drone">+ atlas: unified drone</button><button data-x="atlas-06">+ atlas: reading 06 rebuilt</button><input type="file" accept=".json" hidden></div>
      ${IMPORTED.length ? `<p class="cx-lbl">Imported: ${IMPORTED.map(i => `${esc(i.name)} <button data-rm="${esc(i.id)}" title="remove">×</button>`).join(' · ')}</p>` : ''}`;
    overview = host.querySelector('.sd-ov');
    host.querySelectorAll('[data-p]').forEach(b => b.onclick = () => preset(PRESETS[+b.dataset.p][1]));
    host.querySelectorAll('.sd-tr').forEach(r => {
      const t = T[r.dataset.id];
      r.querySelector('.sd-on').onclick = () => { t.on = !t.on; save(); render(); };
      r.querySelector('input').oninput = e => { t.gain = +e.target.value; save(); };
      r.querySelector('.sd-s').onclick = () => { t.solo = !t.solo; if (t.solo) t.on = true; save(); render(); };
      const d = r.querySelector('.sd-d'); if (d) d.onclick = () => { t.duck = !t.duck; save(); render(); };
    });
    overview.onclick = e => { const r = overview.getBoundingClientRect(); window.CUT?.seek((e.clientX - r.left) / r.width * (D?.dur || 1440)); };
    host.querySelectorAll('[data-fx]').forEach(b => b.onclick = () => { FX.splice(+b.dataset.fx, 1); save(); render(); });
    host.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { IMPORTED = IMPORTED.filter(i => i.id !== b.dataset.rm); delete T[b.dataset.rm]; save(); render(); });
    const file = host.querySelector('.sd-files input');
    host.querySelector('[data-x=export]').onclick = exportFresco;
    host.querySelector('[data-x=import]').onclick = () => file.click();
    host.querySelector('[data-x=atlas-drone]').onclick = () => fetchFresco(ATLAS + 'scores/unified-drone.fresco.json', 0);
    host.querySelector('[data-x=atlas-06]').onclick = () => fetchFresco(ATLAS + 'scores/reading-06.fresco.json', D?.clock.spans.find(s => s.num === '06')?.t0 || 0);
    file.onchange = async () => { const f = file.files[0]; file.value = ''; if (!f) return; try { importFresco(JSON.parse(await f.text()), 0, f.name); } catch (e) { window.CineosisPanel?.status('import failed: ' + e.message); } };
    libList = host.querySelector('.sd-lib');
    host.querySelector('.sd-q').oninput = e => drawLib(e.target.value);
    loadLib().then(() => drawLib(''));
    const fl = host.querySelector('.sd-fail'); if (failed.size) { fl.hidden = false; fl.textContent = `${failed.size} file${failed.size === 1 ? '' : 's'} would not play (missing, or a format this browser lacks).`; }
  }
  function meters() {
    if (!host || !host.isConnected) return;
    for (const r of host.querySelectorAll('.sd-tr')) {
      const t = T[r.dataset.id], m = r.querySelector('.sd-m i'); if (!t || !m) continue;
      const lv = t.id === 'archive' ? (window.CUT?.S.archiveGain || 0) * .5 : (bus[t.id] ? Math.min(1, rms(bus[t.id].m, bus[t.id].a) * 6) : 0);
      m.style.width = (lv * 100).toFixed(0) + '%';
    }
    drawOverview();
  }
  let ovLast = 0;
  function drawOverview() {
    if (!overview || !D || performance.now() - ovLast < 100) return; ovLast = performance.now();
    const w = overview.clientWidth; if (overview.width !== w) overview.width = w;
    const g = overview.getContext('2d'), tr = all(), dur = D.dur; g.clearRect(0, 0, w, overview.height);
    tr.forEach((t, i) => {
      const y = 4 + i * 14;
      g.fillStyle = '#1b2428'; g.fillRect(0, y, w, 10);
      g.fillStyle = audible(t) ? (t.key ? '#c4f46a' : '#8fb8c9') : '#3a4a4e';
      if (t.id === 'archive') { g.fillRect(0, y + 3, w, 4); return; }
      for (const c of t.clips) g.fillRect(c.at / dur * w, y, Math.max(1, (c.e - c.s) / dur * w), 10);
    });
    const x = (window.CUT?.S.time || 0) / dur * w; g.fillStyle = '#e0483a'; g.fillRect(x - 1, 0, 2, overview.height);
  }

  /* ---------- the library: sonic.json (pack + chops + songs), searchable, added at the playhead ---------- */
  let preview = null;
  async function loadLib() {
    if (LIB) return;
    try { LIB = (await (await fetch(ATLAS + 'sonic/sonic.json')).json()).sounds.filter(s => s.file && !/\.ogg($|\?)/i.test(s.file)); }
    catch (e) { LIB = []; }
    const n = host?.querySelector('.sd-libn'); if (n) n.textContent = `${LIB.length} sounds`;
  }
  function drawLib(q) {
    if (!libList || !LIB) return;
    const w = q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const L = LIB.filter(s => !w.length || w.every(x => `${s.label} ${s.eco} ${s.cls} ${s.phr || ''} ${s.key || ''}`.toLowerCase().includes(x)));
    libList.innerHTML = L.slice(0, 80).map((s, i) => `<div class="sd-snd" data-i="${LIB.indexOf(s)}"><button class="sd-pv" title="listen">▶</button>
      <span><b>${esc(s.label)}</b><small>${esc(s.eco)} · ${esc(s.cls || '')} · ${(+s.dur || 0).toFixed(1)} s${s.key ? ' · ' + esc(s.key) : ''}${s.phr ? ' · ' + esc(s.phr) : ''}</small></span>
      <button class="sd-add" title="add at the playhead on the FX track">+ at ${tc(window.CUT?.S.time || 0)}</button></div>`).join('')
      + (L.length > 80 ? `<p class="cx-none">${L.length - 80} more · narrow the search</p>` : '') + (L.length ? '' : '<p class="cx-none">No sound matches.</p>');
    libList.querySelectorAll('.sd-snd').forEach(r => {
      const s = LIB[+r.dataset.i];
      r.querySelector('.sd-pv').onclick = () => { if (preview) { preview.pause(); preview = null; } preview = new Audio(abs(s.file)); preview.play().catch(() => {}); };
      r.querySelector('.sd-add').onclick = () => {
        const at = window.CUT?.S.time || 0, len = Math.max(.2, Math.min(+s.dur || 4, 60));
        FX.push({ at: +at.toFixed(3), s: 0, e: +len.toFixed(3), fadeIn: .01, fadeOut: .05, gain: 1, src: abs(s.file), label: s.label });
        FX.sort((a, b) => a.at - b.at); T.fx.on = true; save(); render();
        window.CineosisPanel?.status(`sound: ${s.label} at ${tc(at)}`);
      };
    });
  }

  /* ---------- fresco-score v0.1 in and out ---------- */
  function exportFresco() {
    const tracks = all().filter(t => audible(t) && t.id !== 'archive' && t.clips.length).map(t => ({ id: t.id, name: t.name.toUpperCase(), gain: t.gain,
      clips: t.clips.map(c => ({ at: c.at, source: c.src, s: c.s, e: c.e, gain: c.gain ?? 1, fadeIn: c.fadeIn || 0, fadeOut: c.fadeOut || 0, label: c.label || '' })) }));
    const cuts = (window.CUT?.S.clips || []).map(c => ({ t: +c.t.toFixed(3), value: c.cineosis ? `${c.cineosis.symbol || ''} ${c.cineosis.note || ''}`.trim() : (window.CUT.S.sources.get(c.src)?.name || 'clip') }));
    const score = { fresco: '0.1', title: 'CUT · cineosis sound desk', duration: D?.dur || 1440.07, base: '', tracks,
      lanes: [{ id: 'picture', name: 'PICTURE', type: 'marker', events: cuts.map(e => ({ t: e.t, type: 'CUT', value: e.value })) }],
      provenance: { generator: 'cineosis-lab/lab/tools/atlas-sound.js', generated: new Date().toISOString(), from: ['WYGWYL · ATLAS (' + ATLAS + ')', 'CUT timeline'] } };
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(score, null, 1)], { type: 'application/json' }));
    a.download = 'cut-sound.fresco.json'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    window.CineosisPanel?.status(`exported ${tracks.length} track${tracks.length === 1 ? '' : 's'} · cut-sound.fresco.json`);
  }
  async function fetchFresco(url, offset) {
    try { importFresco(await (await fetch(url)).json(), offset, url.split('/').pop()); }
    catch (e) { window.CineosisPanel?.status('could not load ' + url.split('/').pop()); }
  }
  function importFresco(j, offset, name) {
    if (!j || !Array.isArray(j.tracks)) throw new Error('not a fresco score');
    const base = j.base ? new URL(j.base, ATLAS).href : ATLAS;
    for (const tr of j.tracks) {
      const id = 'imp-' + (name || 'score').replace(/\W+/g, '-') + '-' + tr.id;
      const rec = { id, name: `${tr.name || tr.id} · ${name || 'imported'}`, gain: tr.gain ?? 1,
        clips: (tr.clips || []).map(c => ({ at: +(c.at + offset).toFixed(3), s: c.s || 0, e: c.e ?? (c.s || 0) + 10, gain: c.gain ?? 1, fadeIn: c.fadeIn || 0, fadeOut: c.fadeOut || 0,
          src: /^https?:|^blob:/.test(c.source) ? c.source : new URL(c.source, base).href, label: c.label || '' })) };
      IMPORTED = IMPORTED.filter(i => i.id !== id).concat(rec); addImported(rec); T[id].on = true;
    }
    save(); render(); window.CineosisPanel?.status(`imported ${j.tracks.length} track${j.tracks.length === 1 ? '' : 's'} from ${name}`);
  }
  function addImported(rec) {
    const prev = saved.tracks?.[rec.id] || {};
    T[rec.id] = { id: rec.id, name: rec.name, note: 'imported fresco track', lane: 'import', on: prev.on ?? true, gain: prev.gain ?? rec.gain ?? 1, solo: false, duck: prev.duck ?? false, clips: rec.clips };
    mkBus(T[rec.id]);
  }

  /* ---------- boot: wait for the panel, then the atlas ---------- */
  (async function boot() {
    for (let k = 0; k < 200 && !window.CineosisPanel?.soundHost?.(); k++) await new Promise(r => setTimeout(r, 100));
    render();
    try { await load(); } catch (e) { const s = host?.querySelector('.sd-state'); if (s) s.textContent = 'the atlas did not load · ' + e.message; return; }
    render();
  })();
  window.AtlasSound = { tracks: () => all(), preset: name => { const p = PRESETS.find(x => x[0] === name); if (p) preset(p[1]); }, exportFresco, duck: () => duckVal, voices: () => voices.size,
    debug: () => ({ failed: [...failed], voices: [...voices.values()].map(v => ({ track: v.track.id, src: v.clip.src.split('/').pop(), t: +v.el.currentTime.toFixed(2), paused: v.el.paused, ready: v.el.readyState })) }) };
})();
