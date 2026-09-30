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
      worker.onmessage = e => { const d = e.data; if (d.status === 'cached') return; if (d.status) { onStat && onStat(d); return; } const w = waiting.get(d.id); if (!w) return; waiting.delete(d.id); d.error ? w.no(new Error(d.error)) : w.ok(d); };
      worker.onerror = e => { const err = new Error('the listener could not start: ' + (e.message || 'it could not be loaded')); waiting.forEach(w => w.no(err)); waiting.clear(); worker = null; onStat && onStat({ status: 'error', message: err.message }); }; }
    return worker;
  }
  const warm = cb => { onStat = cb || onStat; W().postMessage({ warm: true }); };
  const prefetch = () => { try { if (navigator.connection && navigator.connection.saveData) return; W().postMessage({ prefetch: true }); } catch (e) { } };
  function words(pcm, cb) { onStat = cb || onStat; return new Promise((ok, no) => { const id = nextId++; waiting.set(id, { ok, no }); const copy = new Float32Array(pcm); W().postMessage({ id, pcm: copy }, [copy.buffer]);
    setTimeout(() => { if (waiting.has(id)) { waiting.delete(id); no(new Error('the listener took too long')); } }, 180000); }); }
  const AC = window.AudioContext || window.webkitAudioContext, OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  async function resample(data, rate) {                       // to the 16 kHz mono the listener wants
    if (rate === 16000 || !data.length) return data;
    const off = new OAC(1, Math.max(1, Math.ceil(data.length * 16000 / rate)), 16000), b = off.createBuffer(1, data.length, rate); b.copyToChannel(data, 0);
    const s = off.createBufferSource(); s.buffer = b; s.connect(off.destination); s.start(); return (await off.startRendering()).getChannelData(0).slice();
  }
  function decode(ac, buf) { return new Promise((ok, no) => { try { const p = ac.decodeAudioData(buf, ok, no); if (p && p.catch) p.catch(no); } catch (e) { no(e); } }); }
  // Call take() directly inside a tap: Safari and iPhones only start audio that begins in the tap itself, so the audio context is
  // created and resumed here, before anything is awaited.
  const Mic = window.MPMic || { audio: () => ({ echoCancellation: true, noiseSuppression: true }), label: () => 'microphone' };
  function take(opts = {}) {
    const ac = new AC(), resumed = ac.resume ? ac.resume().catch(() => { }) : Promise.resolve();
    return (async () => {
      let stream;
      try { stream = await navigator.mediaDevices.getUserMedia({ audio: Mic.audio() }); } catch (e) { try { ac.close(); } catch (x) { } throw e; }
      const label = Mic.label(stream);
      await Promise.race([resumed, sleep(1200)]);
      const src = ac.createMediaStreamSource(stream), an = ac.createAnalyser(); an.fftSize = 1024; src.connect(an);
      // two copies of the sound: the browser's own recording (made off the page's thread: the reliable one), and raw samples as a fallback
      const proc = ac.createScriptProcessor(4096, 1, 1), chunks = [], mute = ac.createGain(); mute.gain.value = 0;
      proc.onaudioprocess = e => chunks.push(new Float32Array(e.inputBuffer.getChannelData(0))); src.connect(proc); proc.connect(mute); mute.connect(ac.destination);
      let media = null, parts = []; const mime = ['audio/mp4', 'audio/webm;codecs=opus', 'audio/webm'].find(m => window.MediaRecorder && MediaRecorder.isTypeSupported(m));
      try { media = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined); media.ondataavailable = e => e.data.size && parts.push(e.data); media.start(250); } catch (e) { media = null; }
      const t0 = performance.now(), buf = new Uint8Array(an.fftSize); let spoke = 0, quiet = 0, done = null, timer = 0, stopped = false, peak = 0;
      function finish() {
        if (stopped) return done; stopped = true; clearInterval(timer);
        done = (async () => {
          const seconds = (performance.now() - t0) / 1000;
          const blob = await new Promise(r => { if (!media || media.state === 'inactive') return r(parts.length ? new Blob(parts, { type: mime || 'audio/webm' }) : null); media.onstop = () => r(new Blob(parts, { type: media.mimeType || mime || 'audio/webm' })); try { media.stop(); } catch (e) { r(null); } });
          try { proc.disconnect(); src.disconnect(); } catch (e) { } stream.getTracks().forEach(t => t.stop());
          let pcm = null, via = '';
          if (blob && blob.size > 800) { try { const d = await decode(ac, await blob.arrayBuffer()); if (d.duration > seconds * .5) { pcm = await resample(d.getChannelData(0).slice(), d.sampleRate); via = 'recorder'; } } catch (e) { } }
          if (!pcm) { const n = chunks.reduce((a, c) => a + c.length, 0), raw = new Float32Array(n); let o = 0; chunks.forEach(c => { raw.set(c, o); o += c.length; }); pcm = await resample(raw, ac.sampleRate); via = 'samples'; }
          let pk = 0; for (let i = 0; i < pcm.length; i += 3) { const v = pcm[i] < 0 ? -pcm[i] : pcm[i]; if (v > pk) pk = v; } peak = Math.max(peak, pk);   // the recording itself is the evidence; the live meter can be asleep
          try { ac.close(); } catch (e) { }
          return { label, blob, pcm, seconds, peak, via, mime: blob ? blob.type : '', bytes: blob ? blob.size : 0, state: ac.state };
        })();
        return done;
      }
      let resolveAuto; const auto = new Promise(r => resolveAuto = r);
      timer = setInterval(() => { if (ac.state !== 'running' && ac.resume) ac.resume().catch(() => { }); an.getByteTimeDomainData(buf); let m = 0; for (const v of buf) m = Math.max(m, Math.abs(v - 128)); const lv = m / 128; peak = Math.max(peak, lv); opts.onLevel && opts.onLevel(lv, (performance.now() - t0) / 1000);
        if (opts.autoStop) { if (lv > .035) { spoke++; quiet = 0; } else if (spoke > 3) quiet++; const t = (performance.now() - t0) / 1000; if ((spoke > 3 && quiet > 26) || t > 25 || (!spoke && t > 8)) resolveAuto(finish()); } }, 50);
      return { label, stop: finish, auto, state: () => ac.state, cancel() { stopped = true; clearInterval(timer); try { media && media.state !== 'inactive' && media.stop(); } catch (e) { } try { proc.disconnect(); stream.getTracks().forEach(t => t.stop()); ac.close(); } catch (e) { } } };
    })();
  }
  // A microphone check that says what happens at each step, on screen: row(name, ok, detail)
  async function check(row, speakMs = 4000) {
    row('browser', !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && AC && window.Worker), `${window.isSecureContext ? 'secure page' : 'NOT a secure page (needs https)'} · recorder ${window.MediaRecorder ? 'yes' : 'no'}`);
    let t; try { t = await take({ onLevel: lv => row('level', null, 'speak now… ' + '▮'.repeat(Math.round(lv * 20))) }); } catch (e) { row('microphone', false, (e.name || '') + ': ' + e.message + (/NotAllowed/.test(e.name) ? ' — allow the microphone for this site in the browser or phone settings' : '')); return false; }
    row('microphone', true, 'allowed · ' + t.label + ' · audio ' + t.state()); await sleep(speakMs);
    const r = await t.stop(); row('level', r.peak > .04, r.peak > .04 ? 'heard sound (peak ' + r.peak.toFixed(2) + ')' : 'silence: the microphone gave no sound (peak ' + r.peak.toFixed(2) + ')');
    row('recording', r.pcm.length > 8000, `${(r.pcm.length / 16000).toFixed(1)} s from the ${r.via} · ${r.mime || 'no file'} ${Math.round(r.bytes / 1024)} KB`);
    if (r.pcm.length < 8000) return false;
    const t0 = performance.now(); row('listener', null, 'fetching the listener…');
    try { const out = await words(r.pcm, d => row('listener', null, d.status === 'ready' ? 'finding words…' : 'fetching the listener ' + Math.round((d.frac || 0) * 100) + '%'));
      row('listener', true, 'ran in ' + ((performance.now() - t0) / 1000).toFixed(1) + ' s'); row('words', !!out.text, out.text ? '"' + out.text + '"' : 'no words were found in the sound'); return !!out.text;
    } catch (e) { row('listener', false, e.message); return false; }
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
  window.MPHear = { warm, prefetch, take, words, align, sentences, check, supported: () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.Worker) };
})();
