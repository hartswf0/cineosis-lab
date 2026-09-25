/* CUT · the sound desk: the WYGWYL · ATLAS sound experiments as tracks on CUT's own clock, mixed by a law.
 *
 * Tracks (one per atlas experiment, on the 24:00 suite clock the atlas shares with the WYGWYL cut):
 *   suite · drone · reading · codex · one cut · duets · radio atlantis · transmission · poem worlds · fx · archive
 * Every track is an element of the sound table (lab/sound-table.html): a kind (Po, Mo, Sg, Dr…) in a family
 * (voice / music / field / signal) standing OUT of the film-world — except the archive, whose sound is IN.
 *
 * The mix law (lab/sound-table.json "laws", the atlas's own constants from poemworlds / watertable / pacing desk):
 *   1 one clock            nothing is re-timed except by rule 3
 *   2 her voice untouched  voice tracks with priority 1 are never ducked or carved
 *   3 one speaker          a lower voice (codex) never starts over her words: it moves to the next gap in the
 *                          chapter that is ≥ 2 s after her and long enough, or it is held (drawn hollow)
 *   4 one music            of the music tracks sounding, only the first plays in front; the rest sink to texture
 *                          (lowpass 900 Hz, ×0.3); archive music sinks under atlas music
 *   5 carve, don't bury    under her voice, music and field lose the mid band (peaking 1.4 kHz, Q 0.7, −7 dB·amt)
 *                          and the bus drops to 1 − 0.9·amt; amt bows in 30 ms, rises in 160 ms; rms > 0.012 = speaking
 *   6 snap to breath       hits and risers added from the library land in her next silence ≥ 1 s within 3 s,
 *                          ≥ 7 s apart; whispers only in silences ≥ 3.5 s
 *   7 level                archive clips are normalised toward −24 LUFS from their measured loudness
 *                          (lab/tools/sound-kinds.json); a found voice drops to 0.12 under hers
 * The mix plays through CUT's AudioContext, so CUT's Export records it. A readout on CUT's frame shows what is
 * sounding now, as sound-table elements. Mixes save in this browser; fresco-score v0.1 export/import.
 */
(() => {
  'use strict';
  const HERE = document.currentScript?.src || location.href;
  const ATLAS = 'https://hartswf0.github.io/butterfly-halfworld/wygwyl/';
  const SUITE = new URL('../wygwyl/WYGWYL_Suite_Audio.mp3', HERE).href;
  const TABLE = new URL('../sound-table.html', HERE).href;
  const KEY = 'cineosis.sound.v1';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tc = t => { t = Math.max(0, t || 0); const m = Math.floor(t / 60); return String(m).padStart(2, '0') + ':' + String(Math.floor(t % 60)).padStart(2, '0'); };
  const abs = f => /^https?:/.test(f) ? f : ATLAS + f.split('/').map(encodeURIComponent).join('/');
  const ls = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
               set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } } };
  const COLOR = { voice: '#ff5a1f', music: '#1d6bff', field: '#1f9d57', signal: '#e3262d', ground: '#8b8a86', archive: '#b3ab9e' };
  const KIND = { speech: ['Fv', 'Found voice', 'voice'], music: ['Fm', 'Found music', 'music'], noise: ['Fn', 'Found noise', 'field'],
                 mixed: ['Fv', 'Found voice + music', 'voice'], silence: ['Si', 'Silence', 'ground'], none: ['Si', 'No sound', 'ground'] };

  /* ---------- the tracks, as sound-table elements ---------- */
  const TRACKS = [
    { id: 'suite', name: 'Suite', sym: 'Sg', fam: 'music', note: 'the album the cut was timed to · carries her voice' },
    { id: 'drone', name: 'Drone', sym: 'Dr', fam: 'field', note: 'the unified drone · the corpus clock' },
    { id: 'reading', name: 'Reading', sym: 'Po', fam: 'voice', prio: 1, note: 'RY reading, at each poem’s window' },
    { id: 'codex', name: 'Codex', sym: 'Mo', fam: 'voice', prio: 4, note: 'sung lines · wait for her gaps' },
    { id: 'onecut', name: 'One cut', sym: 'Po', fam: 'voice', prio: 1, note: 'her reading as spine, the song on the strong lines' },
    { id: 'duets', name: 'Duets', sym: 'Kn', fam: 'voice', prio: 1, note: 'her line, then another mouth answering' },
    { id: 'radio', name: 'Radio Atlantis', sym: 'Sg', fam: 'music', note: 'fourteen scores · carries her voice' },
    { id: 'transmission', name: 'Transmission', sym: 'Sg', fam: 'music', note: 'the readings as broadcast · carries her voice' },
    { id: 'worlds', name: 'Poem worlds', sym: 'Sg', fam: 'music', note: 'each poem’s referred songs as beds' },
    { id: 'fx', name: 'FX', sym: 'Ht', fam: 'field', note: 'library sounds you place · snapped to breath' },
    { id: 'archive', name: 'Archive', sym: 'Fn', fam: 'archive', note: 'the footage’s own sound, by its measured kind' }
  ];
  const PRESETS = [
    ['Suite', { suite: 1, archive: .4 }],
    ['Reading + drone', { drone: .7, reading: 1, archive: .5 }],
    ['Codex ghosts', { drone: .6, reading: 1, codex: .8 }],
    ['One cut', { onecut: 1, drone: .45 }],
    ['Duets', { duets: 1, drone: .4 }],
    ['Radio Atlantis', { radio: 1, archive: .3 }],
    ['Transmission', { transmission: 1 }],
    ['Poem worlds', { reading: 1, worlds: .6, drone: .35 }],
    ['The found film', { archive: 1, drone: .25 }]
  ];
  const saved = ls.get(KEY, {});
  const T = Object.fromEntries(TRACKS.map(t => [t.id, { ...t, on: false, gain: 1, solo: false, duck: t.fam !== 'voice', ...(saved.tracks?.[t.id] || {}), clips: [], state: '' }]));
  if (!saved.tracks) { T.suite.on = true; T.archive.on = true; T.archive.gain = .4; }
  const FX = saved.fx || [];
  let QUIET = saved.quiet ?? 2;                     // seconds of her quiet before another mouth may answer (water table: 2)
  let IMPORTED = saved.imported || [];
  IMPORTED.forEach(addImported);

  /* ---------- data → clips on the clock ---------- */
  let ready = false, D = null, KINDS = {}, SPEECH = [];
  async function load() {
    const j = u => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
    const [clock, samples, worlds, idx, kinds] = await Promise.all([j(ATLAS + 'clock.json'), j(ATLAS + 'samples.json').catch(() => null),
      j(ATLAS + 'poemworlds.json').catch(() => null), j(new URL('cineosis-index.json', HERE).href), j(new URL('sound-kinds.json?v=2', HERE).href).catch(() => null)]);
    KINDS = kinds?.clips || {};
    const films = idx.wygwyl.films, dur = clock.duration || 1440.07;
    const readDur = Object.fromEntries((samples?.tracks || []).map(t => [t.num, t.dur]));
    const span = n => clock.spans.find(s => s.num === n);
    const poem0 = n => { const f = films.find(x => x.n === n); return f?.poem?.[0] ?? span(n)?.t0 ?? 0; };
    const fit = (at, len, n, extra = {}) => { const end = span(n).t1, e = Math.max(.1, Math.min(len ?? end - at, end - at));
      return { at: +at.toFixed(3), s: 0, e: +e.toFixed(3), fadeIn: .05, fadeOut: len && len > end - at ? 1.5 : .3, gain: 1, end, start: span(n).t0, ...extra }; };
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
      if (w) {                                     // referred songs laid end to end across the span, 20 s each at most
        let at = s.t0;
        for (const snd of (w.sounds || [])) {      // .ogg plays in Chrome/Firefox; a failed file is skipped
          if (at >= s.t1 - 2) break;
          const len = Math.min(20, s.t1 - at);
          T.worlds.clips.push({ at: +at.toFixed(3), s: 0, e: +len.toFixed(3), fadeIn: 1.5, fadeOut: 1.5, gain: .8, src: abs(snd.file), label: snd.label || snd.id, loop: true });
          at += len;
        }
      }
      // where she is actually speaking: the reading's own line timings, on the suite clock
      const tr = samples?.tracks?.find(x => x.num === n);
      for (const l of tr?.lines || []) SPEECH.push([p0 + l.s, p0 + l.e]);
    }
    SPEECH.sort((a, b) => a[0] - b[0]);
    T.codex.clips.forEach(c => { c.at0 = c.at; });
    T.fx.clips = FX;
    D = { dur, clock };
    schedule();
    ready = true;
  }

  /* ---------- law 3: one speaker — lower voices move to her gaps, or are held ---------- */
  const herOn = () => ['reading', 'onecut', 'duets'].some(id => audible(T[id]));
  function schedule() {
    const cx = T.codex.clips; if (!cx.length) return;
    cx.forEach(c => { c.at = c.at0; c.held = false; c.moved = false; c.frag = false; if (c.e0 != null) { c.e = c.e0; c.fadeOut = c.fo0; } });
    if (!herOn()) return;
    // her pauses are short (median 0.68 s, never > 2.05 s): a mouth answers in the free stretches of its chapter —
    // before she starts (foreshadowing) or after she ends (coda) — nearest to where its line belongs
    const busy = SPEECH.map(([a, b]) => [a - .3, b + QUIET]);
    const freeIn = (lo, hi) => {                                // free intervals in [lo, hi]
      const B = busy.filter(([x, y]) => y > lo && x < hi).sort((p, q) => p[0] - q[0]); const out = []; let cur = lo;
      for (const [x, y] of B) { if (x > cur) out.push([cur, Math.min(x, hi)]); cur = Math.max(cur, y); if (cur >= hi) break; }
      if (cur < hi) out.push([cur, hi]); return out;
    };
    for (const c of [...cx].sort((p, q) => p.at0 - q.at0)) {
      const len = c.e - c.s, F = freeIn(c.start ?? c.at0, c.end);
      const whole = F.filter(([a, b]) => b - a >= len + .2);
      if (whole.length) {                                       // the whole line, as near its own place as the gap allows
        const at = whole.map(([a, b]) => Math.min(Math.max(c.at0, a), b - len - .1)).sort((p, q) => Math.abs(p - c.at0) - Math.abs(q - c.at0))[0];
        c.moved = Math.abs(at - c.at0) > .05; c.at = +at.toFixed(3); busy.push([c.at - .2, c.at + len + .4]); continue;
      }
      const part = F.filter(([a, b]) => b - a >= 2.5).sort((p, q) => (q[1] - q[0]) - (p[1] - p[0]))[0];
      if (part) {                                               // a fragment of the line in the longest free stretch
        if (c.e0 == null) { c.e0 = c.e; c.fo0 = c.fadeOut; }
        c.at = +(part[0] + .1).toFixed(3); c.e = +(c.s + Math.min(len, part[1] - part[0] - .3)).toFixed(3); c.fadeOut = .8; c.moved = true; c.frag = true;
        busy.push([c.at - .2, c.at + (c.e - c.s) + .4]);
      } else c.held = true;
    }
  }
  const silenceAfter = (t, min) => {                          // the next gap in her speech ≥ min s, starting at or after t
    if (!herOn() || !SPEECH.length) return t;
    const inWord = SPEECH.find(([a, b]) => t >= a && t < b);
    let cand = inWord ? inWord[1] : t;
    for (const [a, b] of SPEECH) {
      if (b <= cand) continue;
      if (a - cand >= min) return cand;
      cand = Math.max(cand, b);
    }
    return cand;
  };

  /* ---------- the audio graph ---------- */
  let ctx = null, master = null, keyBus = null, analyser = null, buf = null, amt = 0, lastT = 0, wiredDest = null;
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
    if (!ctx || bus[t.id] || t.id === 'archive') return;
    const g = ctx.createGain(), eq = ctx.createBiquadFilter(), lp = ctx.createBiquadFilter(), d = ctx.createGain(), m = ctx.createAnalyser();
    eq.type = 'peaking'; eq.frequency.value = 1400; eq.Q.value = .7; eq.gain.value = 0;
    lp.type = 'lowpass'; lp.frequency.value = 20000; m.fftSize = 512;
    g.connect(eq); eq.connect(lp); lp.connect(d); d.connect(master); d.connect(m);
    if (t.fam === 'voice') g.connect(keyBus);
    bus[t.id] = { g, eq, lp, d, m, a: new Float32Array(512) };
  }
  ['pointerdown', 'keydown'].forEach(ev => addEventListener(ev, () => { if (graph() && ctx.state !== 'running') ctx.resume().catch(() => {}); }, true));

  const all = () => [...TRACKS.map(t => T[t.id]), ...IMPORTED.map(i => T[i.id])].filter(Boolean);
  const anySolo = () => all().some(t => t.solo && t.on);
  const audible = t => !!t && t.on && (!anySolo() || t.solo);
  const voices = new Map();
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
  const inside = (c, t) => !c.held && t >= c.at && t < c.at + (c.e - c.s);

  /* ---------- the archive: CUT's clips, gained by their measured sound (law 7) ---------- */
  const kindOf = c => { const id = c?.cineosis?.shot; return id && KINDS[id] ? KINDS[id] : null; };
  let atlasMusicFront = false;
  function clipGain(c) {
    const A = T.archive; if (!audible(A)) return 0;
    const k = kindOf(c); let g = A.gain;
    if (k && typeof k[1] === 'number') g *= Math.min(1, Math.pow(10, (-24 - k[1]) / 20));
    const kind = k?.[0];
    if (kind === 'speech' || kind === 'mixed') g *= (1 - .88 * amt) * (kind === 'mixed' && atlasMusicFront ? .5 : 1);   // a found voice never speaks over hers
    else if (kind === 'music') g *= atlasMusicFront ? .3 : (A.duck ? 1 - .9 * amt : 1);
    else if (A.duck) g *= 1 - .9 * amt;
    return Math.max(0, Math.min(1, g));
  }

  let NOW = [];                                       // what is sounding: [{sym, name, fam, row, state, track}]
  function tick() {
    requestAnimationFrame(tick);
    const C = window.CUT; if (!C || !ready) return;
    C.S.archiveGain = 1; C.S.clipGain = clipGain;
    const t = C.S.time, playing = C.S.playing;
    if (!ctx) { if (playing) graph(); if (!ctx) { hud([]); return; } }
    if (C.S.dest && wiredDest !== C.S.dest) { master.connect(C.S.dest); wiredDest = C.S.dest; }
    const now = performance.now(), dt = Math.min(.1, (now - (lastT || now)) / 1000); lastT = now;
    // law 5: her level → amt, 30 ms down, 160 ms up (poemworlds)
    const target = rms(analyser, buf) > .012 ? 1 : 0;
    amt += (target - amt) * (1 - Math.exp(-dt / (target > amt ? .03 : .16)));
    // law 4: the first music track sounding plays in front, the rest sink
    const sounding = all().filter(tr => tr.id !== 'archive' && audible(tr) && tr.clips.some(c => inside(c, t)));
    const front = sounding.find(tr => tr.fam === 'music');
    atlasMusicFront = !!front;
    const nowList = [];
    for (const tr of all()) {
      if (tr.id === 'archive') continue;
      mkBus(tr);
      const b = bus[tr.id], on = audible(tr), isMusic = tr.fam === 'music', protectedVoice = tr.fam === 'voice' && tr.prio === 1;
      const under = on && isMusic && front && front !== tr && sounding.includes(tr);
      tr.state = !on ? '' : under ? 'under' : isMusic && front === tr ? 'front' : sounding.includes(tr) ? 'on' : 'waiting';
      b.g.gain.setTargetAtTime(on ? tr.gain * (under ? .3 : 1) : 0, ctx.currentTime, .05);
      b.lp.frequency.setTargetAtTime(under ? 900 : 20000, ctx.currentTime, .1);
      const carve = !protectedVoice && tr.fam !== 'voice' && tr.duck;
      b.eq.gain.setTargetAtTime(carve ? -7 * amt : 0, ctx.currentTime, .02);
      b.d.gain.setTargetAtTime(carve ? 1 - .9 * amt : 1, ctx.currentTime, .02);   // voices are kept apart by law 3, not ducked
      if (!on) continue;
      tr.clips.forEach((c, i) => {
        const len = c.e - c.s, k = tr.id + ':' + i + ':' + c.src;
        if (c.held || failed.has(c.src) || t < c.at - 1.5 || t > c.at + len + .5) return;
        if (!playing && !voices.has(k)) return;
        const v = voiceFor(tr, c, k); v.last = now;
        const rel = t - c.at, isIn = rel >= 0 && rel < len;
        const env = !isIn ? 0 : Math.min(1, c.fadeIn ? rel / c.fadeIn : 1, c.fadeOut ? (len - rel) / c.fadeOut : 1);
        v.gain.gain.setTargetAtTime(env * (c.gain ?? 1), ctx.currentTime, .02);
        let want = c.s + Math.max(0, rel);
        if (c.loop && v.el.duration) want = want % v.el.duration;
        if (playing && isIn) {
          if (v.el.paused) { try { v.el.currentTime = want; } catch (e) { /* not ready */ } v.el.play().catch(() => {}); }
          else if (Math.abs(v.el.currentTime - want) > .3 && !v.el.seeking) v.el.currentTime = want;
        } else if (!v.el.paused) v.el.pause();
        if (isIn) nowList.push({ sym: c.sym || tr.sym, name: tr.name, fam: c.fam || tr.fam, row: 'OUT', state: tr.state === 'under' ? 'under' : c.moved ? 'moved to her gap' : '', label: c.label });
      });
    }
    for (const [k, v] of voices) if (now - v.last > 2000 || !audible(v.track)) drop(k);
    // the archive: what the top clip on CUT's sheet sounds like
    if (audible(T.archive)) {
      const top = (C.onSheet?.() || []).slice(-1)[0], k = kindOf(top);
      if (top) { const K = KIND[k?.[0]] || ['Fn', 'Archive (unmeasured)', 'field'];
        nowList.push({ sym: K[0], name: K[1], fam: K[2], row: 'IN', state: `${Math.round(clipGain(top) * 100)}%${k && typeof k[1] === 'number' ? ' · ' + k[1] + ' LUFS' : ''}`, label: C.S.sources.get(top.src)?.name || '' }); }
    }
    NOW = nowList;
    hud(nowList, amt);
    meters();
  }
  requestAnimationFrame(tick);

  /* ---------- seeing sound: a readout on CUT's frame ---------- */
  let hudEl = null, hudLast = 0;
  function hud(list, a = 0) {
    if (performance.now() - hudLast < 120) return; hudLast = performance.now();
    const st = document.getElementById('stage'); if (!st) return;
    if (!hudEl) { hudEl = document.createElement('div'); hudEl.className = 'sd-hud'; document.body.appendChild(hudEl); }
    const r = st.getBoundingClientRect();
    Object.assign(hudEl.style, { left: r.left + 10 + 'px', top: r.bottom - 10 + 'px' });
    hudEl.hidden = !list.length;
    const key = JSON.stringify(list.map(x => [x.sym, x.state, x.row])) + (a > .5);
    if (hudEl.dataset.k === key) return; hudEl.dataset.k = key;
    hudEl.innerHTML = (a > .5 ? '<span class="sd-her">her voice · the rest carved</span>' : '') + list.map(x =>
      `<a href="${TABLE}#${esc(x.sym)}-${esc(x.row)}" target="_blank" title="${esc(x.label)} — open ${esc(x.sym)} in the sound table" style="--c:${COLOR[x.fam] || '#888'}">
        <b>${esc(x.sym)}</b>${esc(x.name)}<em>${esc(x.row)}</em>${x.state ? `<small>${esc(x.state)}</small>` : ''}</a>`).join('');
  }

  /* ---------- the desk ---------- */
  let host = null, overview = null, libList = null, LIB = null;
  function save() {
    const tracks = Object.fromEntries(all().map(t => [t.id, { on: t.on, gain: t.gain, solo: t.solo, duck: t.duck }]));
    ls.set(KEY, { tracks, fx: FX, imported: IMPORTED, quiet: QUIET });
  }
  function changed() { schedule(); save(); render(); }
  function preset(map) {
    for (const t of all()) { t.on = t.id in map; t.solo = false; if (t.on) t.gain = map[t.id]; }
    changed(); window.CineosisPanel?.status('sound: ' + Object.keys(map).join(' + '));
  }
  function warnings() {
    const w = [];
    const herTracks = ['reading', 'onecut', 'duets'].filter(id => T[id].on).length + ['suite', 'radio', 'transmission'].filter(id => T[id].on).length;
    if (herTracks > 1) w.push('Two tracks carry her voice: she will be heard twice. Keep one of Reading / One cut / Duets / Suite / Radio / Transmission.');
    const held = T.codex.clips.filter(c => c.held).length, moved = T.codex.clips.filter(c => c.moved).length;
    if (T.codex.on && herOn()) w.push(`One speaker: ${moved} sung line${moved === 1 ? '' : 's'} moved out from under her words, before or after her reading (${T.codex.clips.filter(c => c.frag).length} as fragments), ${held} held — no free stretch ≥ 2.5 s left in the chapter.`);
    if (failed.size) w.push(`${failed.size} file${failed.size === 1 ? '' : 's'} would not play (missing, or a format this browser lacks).`);
    return w;
  }
  function row(t) {
    const n = t.clips.length;
    return `<div class="sd-tr${t.on ? ' on' : ''}" data-id="${esc(t.id)}" style="--c:${COLOR[t.fam] || '#888'}">
      <button class="sd-on" title="${t.on ? 'turn off' : 'turn on'}"><b>${esc(t.sym || '··')}</b></button>
      <span class="sd-nm"><b>${esc(t.name)}</b><small>${esc(t.note)}${t.id === 'archive' || !n ? '' : ` · ${n}`}</small></span>
      <input type="range" min="0" max="1.5" step="0.05" value="${t.gain}" title="gain" aria-label="${esc(t.name)} gain">
      <button class="sd-s${t.solo ? ' act' : ''}" title="solo">S</button>
      ${t.fam === 'voice' && t.prio === 1 ? '<span class="sd-k" title="her voice: never ducked or carved; everything else yields">her</span>' : `<button class="sd-d${t.duck ? ' act' : ''}" title="carve and duck under her voice">duck</button>`}
      <i class="sd-m"><i></i></i><span class="sd-st"></span></div>`;
  }
  function render() {
    host = window.CineosisPanel?.soundHost?.(); if (!host) return;
    const W = ready ? warnings() : [];
    host.innerHTML = `
      <div class="sd-dev">
      <div class="sd-head"><b>SOUND DESK</b><span class="sd-state">${ready ? 'the WYGWYL atlas on CUT’s clock' : 'loading the atlas…'}</span>
        <a href="${TABLE}" target="_blank" title="The periodic table of sound: every element here, by where it stands to the image">sound table ↗</a></div>
      <div class="sd-pre">${PRESETS.map(([n], i) => `<button data-p="${i}">${esc(n)}</button>`).join('')}</div>
      <canvas class="sd-ov" height="${14 * all().length + 8}" aria-label="The tracks on the 24-minute clock · click to move the playhead"></canvas>
      <div class="sd-trs">${all().map(row).join('')}</div>
      <div class="sd-quiet"><span>Quiet before an answer</span>${[[2, '2 s · water table'], [.5, '0.5 s · call and response']].map(([v, l]) => `<button data-q="${v}" class="${QUIET === v ? 'act' : ''}">${l}</button>`).join('')}</div>
      ${W.map(w => `<p class="sd-warn">${esc(w)}</p>`).join('')}
      <details class="sd-law"><summary>The mix law</summary><ol>
        <li><b>One clock.</b> Nothing is re-timed except by law 3.</li>
        <li><b>Her voice untouched.</b> Reading, One cut, Duets are never ducked or carved.</li>
        <li><b>One speaker.</b> Sung lines wait for her line to end and the quiet set above; a line too long for the gap answers as a fragment (≥ 2.5 s), or is held.</li>
        <li><b>One music.</b> The first music track sounding leads; the rest sink (lowpass 900 Hz, ×0.3).</li>
        <li><b>Carve, don’t bury.</b> Under her voice: −7 dB at 1.4 kHz and ×0.1, 30 ms down, 160 ms up.</li>
        <li><b>Snap to breath.</b> Hits and risers land in her next silence ≥ 1 s, 7 s apart.</li>
        <li><b>Level.</b> Archive clips toward −24 LUFS; a found voice drops under hers.</li></ol></details>
      </div>
      <h4 class="sd-h">Sound library · <span class="sd-libn"></span></h4>
      <input type="search" class="cx-fq sd-q" placeholder="search the atlas sounds · hit, loop, bed, riser, a word…">
      <div class="sd-lib"></div>
      <h4 class="sd-h">Placed on the clock · ${FX.length}</h4>
      <div class="sd-fx">${FX.map((c, i) => `<div class="sd-fxr" style="--c:${COLOR[c.fam] || '#888'}"><span>${tc(c.at)}</span><b><i>${esc(c.sym || '')}</i> ${esc(c.label)}${c.snapped ? ' <small>· snapped to breath</small>' : ''}</b><button data-fx="${i}" title="remove">×</button></div>`).join('') || '<p class="cx-none">Nothing yet: + a sound from the library at the playhead.</p>'}</div>
      <h4 class="sd-h">Score files</h4>
      <div class="sd-files"><button data-x="export">Export fresco score</button><button data-x="import">Import fresco score</button>
        <button data-x="atlas-drone">+ atlas: unified drone</button><button data-x="atlas-06">+ atlas: reading 06 rebuilt</button><input type="file" accept=".json" hidden></div>
      ${IMPORTED.length ? `<p class="cx-lbl">Imported: ${IMPORTED.map(i => `${esc(i.name)} <button data-rm="${esc(i.id)}" title="remove">×</button>`).join(' · ')}</p>` : ''}`;
    overview = host.querySelector('.sd-ov');
    host.querySelectorAll('[data-p]').forEach(b => b.onclick = () => preset(PRESETS[+b.dataset.p][1]));
    host.querySelectorAll('[data-q]').forEach(b => b.onclick = () => { QUIET = +b.dataset.q; changed(); });
    host.querySelectorAll('.sd-tr').forEach(r => {
      const t = T[r.dataset.id];
      r.querySelector('.sd-on').onclick = () => { t.on = !t.on; changed(); };
      r.querySelector('input').oninput = e => { t.gain = +e.target.value; save(); };
      r.querySelector('.sd-s').onclick = () => { t.solo = !t.solo; if (t.solo) t.on = true; changed(); };
      const d = r.querySelector('.sd-d'); if (d) d.onclick = () => { t.duck = !t.duck; changed(); };
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
  }
  function meters() {
    if (!host || !host.isConnected) return;
    for (const r of host.querySelectorAll('.sd-tr')) {
      const t = T[r.dataset.id], m = r.querySelector('.sd-m i'), s = r.querySelector('.sd-st'); if (!t || !m) continue;
      const lv = t.id === 'archive' ? (audible(t) ? .4 : 0) : (bus[t.id] ? Math.min(1, rms(bus[t.id].m, bus[t.id].a) * 6) : 0);
      m.style.width = (lv * 100).toFixed(0) + '%';
      const st = t.id === 'archive' ? '' : t.state === 'under' ? 'under' : t.state === 'front' ? 'front' : '';
      if (s.textContent !== st) s.textContent = st;
    }
    drawOverview();
  }
  let ovLast = 0;
  function drawOverview() {
    if (!overview || !D || performance.now() - ovLast < 150) return; ovLast = performance.now();
    const w = overview.clientWidth; if (overview.width !== w) overview.width = w;
    const g = overview.getContext('2d'), tr = all(), dur = D.dur; g.clearRect(0, 0, w, overview.height);
    tr.forEach((t, i) => {
      const y = 4 + i * 14, col = COLOR[t.fam] || '#888';
      g.fillStyle = '#0002'; g.fillRect(0, y, w, 10);
      g.globalAlpha = audible(t) ? 1 : .25;
      if (t.id === 'archive') {                        // CUT's clips, coloured by their measured kind
        for (const c of window.CUT?.S.clips || []) { const k = kindOf(c)?.[0]; g.fillStyle = COLOR[(KIND[k] || [0, 0, 'archive'])[2]]; g.fillRect(c.t / dur * w, y + 2, Math.max(1, (c.out - c.in) / dur * w), 6); }
      } else for (const c of t.clips) {
        const x = c.at / dur * w, cw = Math.max(1, (c.e - c.s) / dur * w);
        if (c.held) { g.strokeStyle = col; g.lineWidth = 1; g.strokeRect(x + .5, y + .5, cw, 9); }
        else { g.fillStyle = col; g.fillRect(x, y, cw, 10); }
      }
      g.globalAlpha = 1;
    });
    if (T.reading.on || T.onecut.on || T.duets.on) { g.fillStyle = COLOR.voice + '66'; for (const [a, b] of SPEECH) g.fillRect(a / dur * w, 0, Math.max(1, (b - a) / dur * w), 3); }
    const x = (window.CUT?.S.time || 0) / dur * w; g.fillStyle = '#e0483a'; g.fillRect(x - 1, 0, 2, overview.height);
  }

  /* ---------- the library: sonic.json, searchable, placed at the playhead by law 6 ---------- */
  let preview = null;
  const famOfSound = s => s.cls === 'VOX' ? ['Wh', 'voice'] : s.cls === 'HIT' ? ['Ht', 'signal'] : s.cls === 'RISER' ? ['Rs', 'signal'] : s.cls === 'LOOP' ? ['Lp', 'music']
    : s.cls === 'BED' ? ['Bd', 'field'] : s.cls === 'TEXTURE' ? ['Tx', 'field'] : s.eco === 'song' ? ['Sg', 'music'] : s.eco === 'keynote' ? ['Dr', 'field'] : ['Tx', 'field'];
  async function loadLib() {
    if (LIB) return;
    try { LIB = (await (await fetch(ATLAS + 'sonic/sonic.json')).json()).sounds.filter(s => s.file); } catch (e) { LIB = []; }
    const n = host?.querySelector('.sd-libn'); if (n) n.textContent = `${LIB.length} sounds`;
  }
  function drawLib(q) {
    if (!libList || !LIB) return;
    const w = q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const L = LIB.filter(s => !w.length || w.every(x => `${s.label} ${s.eco} ${s.cls} ${s.phr || ''} ${s.key || ''}`.toLowerCase().includes(x)));
    libList.innerHTML = L.slice(0, 80).map(s => { const [sym, fam] = famOfSound(s); return `<div class="sd-snd" data-i="${LIB.indexOf(s)}" style="--c:${COLOR[fam]}"><button class="sd-pv" title="listen">▶</button>
      <span><b><i>${sym}</i> ${esc(s.label)}</b><small>${esc(s.eco)} · ${esc(s.cls || '')} · ${(+s.dur || 0).toFixed(1)} s${s.key ? ' · ' + esc(s.key) : ''}${s.phr ? ' · ' + esc(s.phr) : ''}</small></span>
      <button class="sd-add" title="place at the playhead${fam === 'signal' ? ', snapped to her next breath' : ''}">+ here</button></div>`; }).join('')
      + (L.length > 80 ? `<p class="cx-none">${L.length - 80} more · narrow the search</p>` : '') + (L.length ? '' : '<p class="cx-none">No sound matches.</p>');
    libList.querySelectorAll('.sd-snd').forEach(r => {
      const s = LIB[+r.dataset.i];
      r.querySelector('.sd-pv').onclick = () => { if (preview) { preview.pause(); preview = null; } preview = new Audio(abs(s.file)); preview.play().catch(() => {}); };
      r.querySelector('.sd-add').onclick = () => {
        const t0 = window.CUT?.S.time || 0, len = Math.max(.2, Math.min(+s.dur || 4, 60)), [sym, fam] = famOfSound(s);
        let at = t0, snapped = false;
        if (fam === 'signal' || sym === 'Wh') {                            // law 6: land in her breath
          const gap = silenceAfter(t0, sym === 'Wh' ? 3.5 : 1);
          if (gap - t0 <= (sym === 'Wh' ? 12 : 3)) { at = gap + .05; snapped = at - t0 > .05; }
          const last = FX.filter(c => c.fam === 'signal' && Math.abs(c.at - at) < 7);
          if (fam === 'signal' && last.length) { window.CineosisPanel?.status(`held: another hit within 7 s (at ${tc(last[0].at)})`); return; }
        }
        FX.push({ at: +at.toFixed(3), s: 0, e: +len.toFixed(3), fadeIn: .01, fadeOut: .05, gain: 1, src: abs(s.file), label: s.label, sym, fam, snapped });
        FX.sort((a, b) => a.at - b.at); T.fx.on = true; save(); render();
        window.CineosisPanel?.status(`sound: ${sym} ${s.label} at ${tc(at)}${snapped ? ' · snapped to her breath' : ''}`);
      };
    });
  }

  /* ---------- fresco-score v0.1 in and out ---------- */
  function exportFresco() {
    const tracks = all().filter(t => audible(t) && t.id !== 'archive' && t.clips.length).map(t => ({ id: t.id, name: t.name.toUpperCase(), gain: t.gain,
      clips: t.clips.filter(c => !c.held).map(c => ({ at: c.at, source: c.src, s: c.s, e: c.e, gain: c.gain ?? 1, fadeIn: c.fadeIn || 0, fadeOut: c.fadeOut || 0, label: c.label || '', ...(c.moved ? { movedFrom: c.at0 } : {}) })) }));
    const cuts = (window.CUT?.S.clips || []).map(c => ({ t: +c.t.toFixed(3), value: c.cineosis ? `${c.cineosis.symbol || ''} ${c.cineosis.note || ''}`.trim() : (window.CUT.S.sources.get(c.src)?.name || 'clip'), kind: kindOf(c)?.[0] || null }));
    const score = { fresco: '0.1', title: 'CUT · cineosis sound desk', duration: D?.dur || 1440.07, base: '', tracks,
      lanes: [{ id: 'picture', name: 'PICTURE', type: 'marker', events: cuts.map(e => ({ t: e.t, type: 'CUT', value: e.value, sound: e.kind })) },
              { id: 'speech', name: 'HER WORDS', type: 'marker', events: SPEECH.map(([a, b]) => ({ t: +a.toFixed(3), type: 'LINE', value: +(b - a).toFixed(2) })) }],
      law: ['one clock', 'her voice untouched', 'one speaker', 'one music', 'carve, don’t bury', 'snap to breath', 'level'],
      provenance: { generator: 'cineosis-lab/lab/tools/atlas-sound.js', generated: new Date().toISOString(), from: ['WYGWYL · ATLAS (' + ATLAS + ')', 'CUT timeline', 'lab/tools/sound-kinds.json'] } };
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
    changed(); window.CineosisPanel?.status(`imported ${j.tracks.length} track${j.tracks.length === 1 ? '' : 's'} from ${name}`);
  }
  function addImported(rec) {
    const prev = saved.tracks?.[rec.id] || {};
    const voicey = /voice|read|vox/i.test(rec.name);
    T[rec.id] = { id: rec.id, name: rec.name, sym: voicey ? 'Po' : 'Sg', fam: voicey ? 'voice' : 'music', prio: voicey ? 1 : undefined, note: 'imported fresco track',
      on: prev.on ?? true, gain: prev.gain ?? rec.gain ?? 1, solo: false, duck: prev.duck ?? !voicey, clips: rec.clips, state: '' };
    mkBus(T[rec.id]);
  }

  /* ---------- boot: wait for the panel, then the atlas ---------- */
  (async function boot() {
    for (let k = 0; k < 200 && !window.CineosisPanel?.soundHost?.(); k++) await new Promise(r => setTimeout(r, 100));
    render();
    try { await load(); } catch (e) { const s = host?.querySelector('.sd-state'); if (s) s.textContent = 'the atlas did not load · ' + e.message; return; }
    render();
  })();
  window.AtlasSound = { tracks: () => all(), preset: name => { const p = PRESETS.find(x => x[0] === name); if (p) preset(p[1]); }, exportFresco,
    amt: () => amt, voices: () => voices.size, now: () => NOW, speech: () => SPEECH.length,
    debug: () => ({ failed: [...failed], codex: { moved: T.codex.clips.filter(c => c.moved).length, frag: T.codex.clips.filter(c => c.frag).length, held: T.codex.clips.filter(c => c.held).length },
      voices: [...voices.values()].map(v => ({ track: v.track.id, src: v.clip.src.split('/').pop(), t: +v.el.currentTime.toFixed(2), paused: v.el.paused, ready: v.el.readyState })) }) };
})();
