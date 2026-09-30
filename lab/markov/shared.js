/* What the Markov Poet's pages share: the archive, reading words, voices, the clock, and a quiet status line.
   window.SH = { load, embed, phrases, voicesFor, status, onStatus, server }
   Reading words: the prepared cache first, then the lab server (/api/embed), then the browser itself (clip-text.js): same model, same numbers.
   Voices: the suite's recorded voice; Piper readings prepared for every text in the library (markov/voice/); Piper on the lab server for new words. */
(function () {
  const S = window.Shannon;
  const SH = window.SH = { server: null, data: null };
  const subs = []; let last = { stage: 'idle', text: '' };
  SH.onStatus = f => { subs.push(f); f(last); };
  SH.status = (stage, text, frac) => { last = { stage, text, frac }; subs.forEach(f => f(last)); };
  SH.isLab = () => /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  // readiness: two things must arrive before new words can become a film: the archive, and (away from the lab) the reader
  SH.ready = { archive: false, reader: false, frac: 0, eta: null }; const readySubs = [];
  SH.onReady = f => { readySubs.push(f); f(SH.ready); };
  const tellReady = () => { const r = SH.ready; r.frac = (r.archive ? .2 : 0) + .8 * (r.reader ? 1 : (window.ClipText ? ClipText.frac || 0 : 0)); r.all = r.archive && r.reader; readySubs.forEach(f => f(r)); };
  function startReader() { if (!window.ClipText) { SH.ready.reader = true; return; }
    ClipText.warm(s => { if (s.stage === 'ready') SH.ready.reader = true; SH.ready.eta = s.eta; SH.ready.failed = s.stage === 'failed' ? s.text : null; tellReady(); }); }
  // load({light: true}) fetches only what a room needs to answer a line: the shots, their vectors, the signs, a few starter lines
  SH.load = async (opts = {}) => {
    if (SH.data) return SH.data;
    SH.status('waking', 'waking the archive');
    const get = (u, bin) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return bin ? r.arrayBuffer() : r.json(); });
    if (!SH.isLab()) { SH.server = false; startReader(); }                 // the published site: the reader starts downloading at once, beside the archive
    const light = !!opts.light;
    const [J, B, K, ST, E, T, PO, V] = await Promise.all([get('markov/library.json'), get('markov/emb.bin', 1), get('bets/kernel-data.json'), get('markov/starters.json').catch(() => ({ starters: [], emb: {} })),
      light ? { events: [] } : get('markov/events.json'), light ? {} : get('markov/texts.json'), light ? { poems: [] } : get('markov/tests/poems.json'), light ? { poems: {}, wygwyl: {} } : get('markov/voice/index.json').catch(() => ({ poems: {}, wygwyl: {} }))]);
    SH.data = { LIB: new S.Library(J, new Int8Array(B), E.events), TX: Object.assign(T, ST.emb), K, POEMS: PO.poems, VOICE: V, starters: ST.starters, hasPoet: J.shots.some(s => s.kind === 'poet') };
    SH.ready.archive = true; tellReady();
    if (SH.isLab()) fetch('/api/embed', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ texts: ['a door'] }) })
      .then(r => SH.server = r.ok).catch(() => SH.server = false).finally(() => { if (SH.server) { SH.ready.reader = true; tellReady(); } else startReader(); });
    SH.status('rest', `${J.n.toLocaleString()} shots at rest`);
    return SH.data;
  };
  SH.embed = async texts => {
    const TX = SH.data.TX, miss = [...new Set(texts.filter(t => !TX[t]))];
    if (miss.length) {
      SH.status('reading', 'reading');
      if (SH.server !== false) {
        try { for (let i = 0; i < miss.length; i += 48) { const r = await fetch('/api/embed', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ texts: miss.slice(i, i + 48) }) });
            if (!r.ok) throw new Error(r.status); const j = await r.json(); miss.slice(i, i + 48).forEach((t, k) => TX[t] = j.emb[k]); } SH.server = true; }
        catch (e) { SH.server = false; }
      }
      const still = miss.filter(t => !TX[t]);
      if (still.length && window.ClipText) {
        const v = await window.ClipText.encode(still, s => { if (s.stage !== 'ready') SH.status('loading', 'your words are waiting for the reader' + (s.eta != null ? ' · about ' + Math.ceil(s.eta) + ' s' : ''), s.frac); }); still.forEach((t, k) => TX[t] = v[k]); SH.status('reading', 'reading');
      }
    }
    return texts.map(t => TX[t] || null);
  };
  const textOf = p => p.text || (() => { try { return JSON.parse(localStorage.getItem('shannon.byo.' + p.id)) || ''; } catch (e) { return ''; } })();
  SH.textOf = textOf;
  SH.voicesFor = src => {
    const V = SH.data.VOICE;
    if (src[0] === 'w') return [['recorded', 'the recorded voice'], ['piper', 'Piper (Ryan), in step'], ['both', 'both, mixed'], ['none', 'silence']];
    if (src.startsWith('t:') && V.poems[src.slice(2)]) return [['ryan', 'Piper (Ryan)'], ['lessac', 'Piper (Lessac)'], ['none', 'silence']];
    return [['ryan', 'Piper (Ryan)'], ['lessac', 'Piper (Lessac)'], ['none', 'silence']];
  };
  const VNAME = { ryan: 'en_US-ryan-high', lessac: 'en_US-lessac-medium' };
  function fromTimes(ph, times, T1) {
    ph.forEach((p, i) => { const t = times[i] || times[times.length - 1]; p.t0 = t[0]; p.t1 = t[1]; p.timed = true; });
    ph.forEach((p, i) => { p.t1 = ph[i + 1] ? Math.max(p.t1, ph[i + 1].t0) : Math.max(p.t1, T1); });
    if (ph.length) ph[0].t0 = 0;
  }
  function gaps(ph) { return ph.map((p, i) => { const n = ph[i + 1]; return !n ? 1.2 : n.scene !== p.scene ? 1.3 : n.sent !== p.sent ? .75 : .3; }); }
  // words -> phrases with a clock. src: 'wNN' | 't:id' | 'own' ; text overrides for 'own'
  SH.phrases = async (src, voice, text) => {
    const { K, POEMS, VOICE } = SH.data;
    if (src[0] === 'w') {
      const film = K.films.find(f => f.n === src.slice(1)), lines = K.lines.filter(l => l.film === film.n);
      const ph = S.parse(lines.map(l => l.text).join('\n')), W = [];
      lines.forEach(l => l.text.split(/\s+/).filter(Boolean).forEach((_, k) => { const w = l.words[Math.min(k, l.words.length - 1)]; W.push([w.t0, w.t1]); }));
      let w = 0; ph.forEach(p => { const n = p.text.split(/\s+/).filter(Boolean).length, a = W[Math.min(w, W.length - 1)], b = W[Math.min(w + n - 1, W.length - 1)]; p.t0 = a[0]; p.t1 = b[1]; w += n; p.timed = true; });
      ph.forEach((p, i) => { p.t1 = ph[i + 1] ? Math.max(p.t1, ph[i + 1].t0) : Math.max(p.t1, film.t1); }); if (ph.length) ph[0].t0 = Math.min(ph[0].t0, film.t0);
      const rec = { src: 'wygwyl/WYGWYL_Suite_Audio.mp3', offset: 0 }, al = VOICE.wygwyl[film.n] && { src: VOICE.wygwyl[film.n]['en_US-ryan-high'] + '.mp3', offset: film.t0 };
      const audio = voice === 'piper' && al ? al : voice === 'none' ? null : rec, second = voice === 'both' && al ? { ...al, vol: .85 } : null;
      return { ph, audio, second, T0: ph[0].t0, T1: film.t1, clockless: !audio };
    }
    const txt = src === 'own' ? (text != null ? text : '') : textOf(POEMS.find(p => p.id === src.slice(2)));
    const ph = S.parse(txt); if (!ph.length) return { ph, audio: null, T0: 0, T1: 0 };
    if (voice !== 'none' && VNAME[voice]) {
      const pre = src.startsWith('t:') && VOICE.poems[src.slice(2)] && VOICE.poems[src.slice(2)][VNAME[voice]];
      try {
        let meta, url;
        if (pre && POEMS.find(p => p.id === src.slice(2)).text) { meta = await fetch(pre + '.json').then(r => r.json()); url = pre + '.mp3'; }
        else if (SH.server) { SH.status('speaking', 'finding a voice'); const r = await fetch('/api/speak', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ phrases: ph.map(p => p.text), gaps: gaps(ph), voice: VNAME[voice] }) });
          if (r.ok) { meta = await r.json(); url = meta.audio; } }
        if (meta && meta.times.length === ph.length) { fromTimes(ph, meta.times, meta.duration); return { ph, audio: { src: url, offset: 0 }, second: null, T0: 0, T1: meta.duration }; }
      } catch (e) { }
    }
    return { ph, audio: null, second: null, T0: 0, T1: ph[ph.length - 1].t1, clockless: true };
  };
  // one run of the engine over timed phrases
  SH.compose = async (P, opts) => {
    const E = await SH.embed(P.ph.map(p => p.text)); if (E.some(x => !x)) throw new Error('some words could not be read');
    SH.status('weighing', `weighing ${SH.data.LIB.n.toLocaleString()} shots`);
    await new Promise(r => setTimeout(r, 20));
    const sims = E.map(e => SH.data.LIB.sims(e)), r = S.run(SH.data.LIB, P.ph, sims, opts);
    if (!P.audio) P.T1 = P.ph[P.ph.length - 1].t1;
    return { ...P, ...r, sims, T1: Math.max(P.T1, r.cut.length ? r.cut[r.cut.length - 1].t1 : 0) };
  };
  // a clock that is a voice when there is one (and keeps a second voice in step), else the wall clock
  SH.Clock = function (primary, secondary) {
    const a = primary, b = secondary; let cur = null, run = false, t = 0, last = 0;
    return {
      set(c) { cur = c; if (a) { a.pause(); } if (b) { b.pause(); }
        if (c.audio) { if (a.dataset.u !== c.audio.src) { a.src = c.audio.src; a.dataset.u = c.audio.src; } }
        if (b) { if (c.second) { if (b.dataset.u !== c.second.src) { b.src = c.second.src; b.dataset.u = c.second.src; } b.volume = c.second.vol || .8; } else b.removeAttribute('src'), b.dataset.u = ''; } },
      play() { run = true; last = performance.now(); if (cur.audio) { try { a.currentTime = Math.max(0, t - cur.audio.offset); } catch (e) { } a.play().catch(() => { }); }
        if (cur.second) { try { b.currentTime = Math.max(0, t - cur.second.offset); } catch (e) { } b.play().catch(() => { }); } },
      pause() { run = false; if (a) a.pause(); if (b) b.pause(); },
      seek(x) { t = x; if (cur && cur.audio) try { a.currentTime = Math.max(0, x - cur.audio.offset); } catch (e) { } if (cur && cur.second) try { b.currentTime = Math.max(0, x - cur.second.offset); } catch (e) { } },
      now() { const n = performance.now();
        if (run && cur && cur.audio && !a.paused) { t = a.currentTime + cur.audio.offset; if (cur.second && !b.paused && Math.abs(b.currentTime + cur.second.offset - t) > .25) b.currentTime = t - cur.second.offset; }
        else if (run) t += (n - last) / 1000; last = n; return t; },
      get running() { return run; } };
  };
})();
