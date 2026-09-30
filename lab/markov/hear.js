/* The Markov Poet's own ears. No browser speech recognition (it does not work on iPhone, and fails silently elsewhere):
   the page records the microphone itself and Whisper, running in this browser, turns the sound into words with a time for each.
   MPHear.warm(onStatus)                 fetch the listener ahead of time (~45 MB, cached by the browser)
   MPHear.take({onLevel, autoStop})      start recording (call from a tap). Returns {stop(): Promise<{blob, pcm, seconds}>, cancel()}
                                         autoStop: stop by itself after speech then ~1.3 s of quiet (for one spoken line)
   MPHear.words(pcm, onStatus)           -> {text, words: [{w, t0, t1}]}
   MPHear.align(words, lines)            -> [[t0, t1] per line]: where in the recording each line of a known poem was read
   MPHear.sentences(words)               -> [{text, t0, t1}]: spoken lines, cut at sentence ends and long pauses */
(function () {
  let worker = null, nextId = 1; const waiting = new Map(); let onStat = null;
  function W() {
    if (!worker) { worker = new Worker(new URL('markov/hear-worker.js', document.baseURI), { type: 'module' });
      worker.onmessage = e => { const d = e.data; if (d.status) { onStat && onStat(d); return; } const w = waiting.get(d.id); if (!w) return; waiting.delete(d.id); d.error ? w.no(new Error(d.error)) : w.ok(d); };
      worker.onerror = e => { waiting.forEach(w => w.no(new Error('the listener could not start: ' + (e.message || 'worker error')))); waiting.clear(); worker = null; }; }
    return worker;
  }
  const warm = cb => { onStat = cb || onStat; W().postMessage({ warm: true }); };
  function words(pcm, cb) { onStat = cb || onStat; return new Promise((ok, no) => { const id = nextId++; waiting.set(id, { ok, no }); W().postMessage({ id, pcm }, [pcm.buffer]); }); }
  async function take(opts = {}) {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 } });
    const AC = window.AudioContext || window.webkitAudioContext, ac = new AC(); if (ac.state === 'suspended') await ac.resume();
    const src = ac.createMediaStreamSource(stream), an = ac.createAnalyser(); an.fftSize = 1024; src.connect(an);
    // the raw samples, kept ourselves: no dependence on what the browser's recorder can later decode
    const proc = ac.createScriptProcessor(4096, 1, 1), chunks = []; const mute = ac.createGain(); mute.gain.value = 0;
    proc.onaudioprocess = e => chunks.push(new Float32Array(e.inputBuffer.getChannelData(0))); src.connect(proc); proc.connect(mute); mute.connect(ac.destination);
    let media = null, parts = []; const mime = ['audio/mp4', 'audio/webm;codecs=opus', 'audio/webm'].find(m => window.MediaRecorder && MediaRecorder.isTypeSupported(m));
    try { media = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined); media.ondataavailable = e => e.data.size && parts.push(e.data); media.start(250); } catch (e) { media = null; }
    const t0 = performance.now(), buf = new Uint8Array(an.fftSize); let spoke = 0, quiet = 0, done = null, timer = 0, stopped = false;
    async function finish() {
      if (stopped) return done; stopped = true; clearInterval(timer);
      done = (async () => {
        const seconds = (performance.now() - t0) / 1000;
        const blob = await new Promise(r => { if (!media || media.state === 'inactive') return r(parts.length ? new Blob(parts, { type: mime || 'audio/webm' }) : null); media.onstop = () => r(new Blob(parts, { type: media.mimeType || mime || 'audio/webm' })); media.stop(); });
        proc.disconnect(); src.disconnect(); stream.getTracks().forEach(t => t.stop());
        const n = chunks.reduce((a, c) => a + c.length, 0), raw = new Float32Array(n); let o = 0; chunks.forEach(c => { raw.set(c, o); o += c.length; });
        const rate = ac.sampleRate; try { ac.close(); } catch (e) { }
        let pcm = raw;
        if (rate !== 16000 && n) { const OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext, off = new OAC(1, Math.max(1, Math.ceil(n * 16000 / rate)), 16000), b = off.createBuffer(1, n, rate); b.copyToChannel(raw, 0);
          const s = off.createBufferSource(); s.buffer = b; s.connect(off.destination); s.start(); pcm = (await off.startRendering()).getChannelData(0).slice(); }
        return { blob, pcm, seconds };
      })();
      return done;
    }
    let resolveAuto; const auto = new Promise(r => resolveAuto = r);
    timer = setInterval(() => { an.getByteTimeDomainData(buf); let m = 0; for (const v of buf) m = Math.max(m, Math.abs(v - 128)); const lv = m / 128; opts.onLevel && opts.onLevel(lv, (performance.now() - t0) / 1000);
      if (opts.autoStop) { if (lv > .06) { spoke++; quiet = 0; } else if (spoke > 3) quiet++; const t = (performance.now() - t0) / 1000; if ((spoke > 3 && quiet > 26) || t > 25 || (!spoke && t > 8)) resolveAuto(finish()); } }, 50);
    return { stop: finish, auto, cancel() { stopped = true; clearInterval(timer); try { media && media.state !== 'inactive' && media.stop(); } catch (e) { } try { proc.disconnect(); stream.getTracks().forEach(t => t.stop()); ac.close(); } catch (e) { } } };
  }
  const norm = w => w.toLowerCase().replace(/[^a-z0-9']/g, '');
  // a known poem, read aloud: each line starts where its share of the words starts, snapped to the nearest pause
  function align(ws, lines) {
    if (!ws.length) return lines.map((_, i) => [i * 2, i * 2 + 2]);
    const counts = lines.map(l => Math.max(1, l.split(/\s+/).filter(Boolean).length)), total = counts.reduce((a, b) => a + b, 0), n = ws.length, cuts = [0]; let cum = 0;
    for (let L = 0; L < lines.length - 1; L++) { cum += counts[L]; let j = Math.round(cum / total * n), best = j, bestScore = -1;
      const first = norm(lines[L + 1].split(/\s+/)[0] || '');
      for (let k = Math.max(cuts[L] + 1, j - 4); k <= Math.min(n - 1, j + 4); k++) { const gap = ws[k].t0 - ws[k - 1].t1, score = gap + (norm(ws[k].w) === first ? .8 : 0) - Math.abs(k - j) * .05; if (score > bestScore) { bestScore = score; best = k; } }
      cuts.push(Math.min(n - 1, Math.max(cuts[L] + 1, best))); }
    return lines.map((_, L) => { const a = ws[Math.min(cuts[L], n - 1)], bIdx = L + 1 < lines.length ? cuts[L + 1] : n; return [Math.max(0, a.t0 - .05), L + 1 < lines.length ? ws[Math.min(bIdx, n - 1)].t0 - .02 : ws[n - 1].t1 + .4]; });
  }
  function sentences(ws) {
    const out = []; let cur = [];
    ws.forEach((w, i) => { cur.push(w); const nx = ws[i + 1], end = /[.!?]$/.test(w.w) || (nx && nx.t0 - w.t1 > .9) || (cur.length >= 14 && /[,;:]$/.test(w.w));
      if (end || !nx) { const t = cur.map(x => x.w).join(' ').replace(/\s+([,.!?;:])/g, '$1').trim(); if (t) out.push({ text: t.replace(/^\w/, c => c.toUpperCase()), t0: cur[0].t0, t1: cur[cur.length - 1].t1 }); cur = []; } });
    return out;
  }
  window.MPHear = { warm, take, words, align, sentences, supported: () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.Worker) };
})();
