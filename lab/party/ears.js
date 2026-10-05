/* EARS: how a room hears its phones, with one key. The OpenAI key lives only on the stand (the same key the Markov Poet keeps,
   markov/live.js, put in once from the stand's sheet). A phone that wants to speak asks the stand for a one-minute pass; the stand
   mints it from the key and hands it over; the phone streams its microphone straight to the realtime listener and the words come
   back while they are being said (and go on to the stand, so the room sees them appear). The phone also records the line itself:
   the recording is what plays in the film. No pass (no key, no network): the stand reads the recording with the same key, or
   with Whisper in its own browser; no words at all, and the games still go on.
   phone: Ears.hold(api, {onLevel, onPartial}) in the tap  -> { stop(): Promise<{a, mime, dur, lv, text} | null>, cancel() }
   stand: Ears.host(H) -> { has(), sheet(cb), onMsg(p, m) -> handled, read(buf, mime) -> Promise<text> }                     */
(function () {
  const API = 'https://api.openai.com/v1', MODEL = 'gpt-realtime', HEAR = 'gpt-4o-mini-transcribe';
  const waiting = new Map(); let seq = 0;
  const onHost = m => { if (m.t !== 'ear') return false; const f = waiting.get(m.id); if (f) { waiting.delete(m.id); f(m.v); } return true; };
  function hold(api, o = {}) {
    const AC = window.AudioContext || window.webkitAudioContext; let ac = null; try { ac = new AC(); ac.resume && ac.resume().catch(() => { }); } catch (e) { }
    const st = { lv: [], parts: [], finals: [], part: '', t0: performance.now(), done: false, rec: null, pc: null, dc: null, timer: 0, wake: null };
    const open = window.MPMic ? MPMic.open() : navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    st.ready = open.then(stream => { st.stream = stream;
      if (ac) { const an = ac.createAnalyser(); an.fftSize = 1024; ac.createMediaStreamSource(stream).connect(an); const b = new Uint8Array(1024);
        st.timer = setInterval(() => { an.getByteTimeDomainData(b); let m = 0; for (let i = 0; i < b.length; i++) m = Math.max(m, Math.abs(b[i] - 128)); const l = m / 128; st.lv.push(+l.toFixed(3)); o.onLevel && o.onLevel(l); }, 60); }
      const mime = ['audio/mp4', 'audio/webm;codecs=opus', 'audio/webm'].find(m => window.MediaRecorder && MediaRecorder.isTypeSupported(m));
      try { st.rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined); st.rec.ondataavailable = e => e.data.size && st.parts.push(e.data); st.rec.start(250); } catch (e) { st.rec = null; }
      const id = ++seq; waiting.set(id, v => { if (v && !st.done) live(st, v, o).catch(() => drop(st)); }); setTimeout(() => waiting.delete(id), 8000); api.send({ t: 'ear', id });
      return stream; });
    return { ready: st.ready, stop: () => finish(st, ac), cancel() { st.done = true; close(st, ac); } };
  }
  async function live(st, eph, o) {
    const pc = st.pc = new RTCPeerConnection(); st.stream.getAudioTracks().forEach(t => pc.addTrack(t, st.stream));
    const dc = st.dc = pc.createDataChannel('oai-events'), tell = () => o.onPartial && o.onPartial((st.finals.join(' ') + ' ' + st.part).trim());
    dc.onopen = () => dc.send(JSON.stringify({ type: 'session.update', session: { type: 'realtime', output_modalities: ['text'], audio: { input: { transcription: { model: HEAR, language: 'en' }, turn_detection: { type: 'server_vad', silence_duration_ms: 400, create_response: false, interrupt_response: false } } } } }));
    dc.onmessage = e => { let m; try { m = JSON.parse(e.data); } catch (x) { return; }
      if (m.type === 'conversation.item.input_audio_transcription.delta') { st.part += m.delta || ''; tell(); }
      else if (m.type === 'conversation.item.input_audio_transcription.completed') { const t = (m.transcript || '').trim(); if (t) st.finals.push(t); st.part = ''; tell(); if (st.wake) st.wake(); } };
    const offer = await pc.createOffer(); await pc.setLocalDescription(offer);
    const r = await fetch(API + '/realtime/calls?model=' + MODEL, { method: 'POST', headers: { Authorization: 'Bearer ' + eph, 'Content-Type': 'application/sdp' }, body: offer.sdp });
    if (!r.ok || st.done) { drop(st); return; } await pc.setRemoteDescription({ type: 'answer', sdp: await r.text() }); }
  function drop(st) { try { st.dc && st.dc.close(); } catch (e) { } try { st.pc && st.pc.close(); } catch (e) { } st.dc = st.pc = null; }
  function close(st, ac) { clearInterval(st.timer); try { st.dc && st.dc.close(); } catch (e) { } try { st.pc && st.pc.close(); } catch (e) { } try { st.stream && st.stream.getTracks().forEach(t => t.stop()); } catch (e) { } try { ac && ac.close(); } catch (e) { } }
  async function finish(st, ac) {
    try { await st.ready; } catch (e) { st.done = true; close(st, ac); return null; }
    const dur = (performance.now() - st.t0) / 1000; clearInterval(st.timer);
    const blob = await new Promise(r => { if (!st.rec || st.rec.state === 'inactive') return r(st.parts.length ? new Blob(st.parts, { type: st.parts[0].type }) : null); st.rec.onstop = () => r(st.parts.length ? new Blob(st.parts, { type: st.rec.mimeType || st.parts[0].type }) : null); try { st.rec.stop(); } catch (e) { r(null); } });
    // what was said after the last pause is still in the listener: ask for it, and wait a moment for its words
    if (st.dc && st.dc.readyState === 'open') { try { st.dc.send(JSON.stringify({ type: 'input_audio_buffer.commit' })); } catch (e) { } await new Promise(r => { st.wake = r; setTimeout(r, st.part || !st.finals.length ? 2600 : 900); }); }
    st.done = true; close(st, ac);
    if (dur < .35) return null;
    const n = st.lv.length, lv = n > 60 ? Array.from({ length: 60 }, (_, i) => Math.max(...st.lv.slice(Math.floor(i * n / 60), Math.max(Math.floor(i * n / 60) + 1, Math.floor((i + 1) * n / 60))))) : st.lv;
    return { a: blob && blob.size > 600 ? await blob.arrayBuffer() : null, mime: blob ? blob.type : '', dur, lv, text: (st.finals.join(' ') + ' ' + st.part).trim() || window.__sayText || '' };
  }
  // ---- the stand: the only place the key lives
  function host(H) {
    const key = () => { try { return localStorage.getItem('mp.openai.key') || sessionStorage.getItem('mp.openai.key') || ''; } catch (e) { return ''; } };
    let whisper = window.MPHear ? 'maybe' : 'none';
    async function mint() { const k = key(); if (!k) return null;
      const r = await fetch(API + '/realtime/client_secrets', { method: 'POST', headers: { Authorization: 'Bearer ' + k, 'Content-Type': 'application/json' }, body: JSON.stringify({ session: { type: 'realtime', model: MODEL } }) });
      if (!r.ok) return null; const j = await r.json(); return j.value || (j.client_secret && j.client_secret.value) || null; }
    async function read(buf, mime) { if (!buf) return '';
      const k = key(); if (k) { try { const f = new FormData(); f.append('file', new File([buf], 'line.' + (/mp4|m4a|aac/.test(mime) ? 'm4a' : /wav/.test(mime) ? 'wav' : 'webm'), { type: mime || 'audio/webm' })); f.append('model', HEAR);
          const r = await fetch(API + '/audio/transcriptions', { method: 'POST', headers: { Authorization: 'Bearer ' + k }, body: f }); if (r.ok) { const j = await r.json(); if (j.text != null) return String(j.text).trim(); } } catch (e) { } }
      if (whisper === 'none') return '';
      const AC = window.AudioContext || window.webkitAudioContext, OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext, ac = new AC();
      try { const ab = await new Promise((ok, no) => { const r = ac.decodeAudioData(buf.slice(0), ok, no); if (r && r.catch) r.catch(no); }), d = ab.getChannelData(0);
        const off = new OAC(1, Math.max(1, Math.ceil(d.length * 16000 / ab.sampleRate)), 16000), b = off.createBuffer(1, d.length, ab.sampleRate); b.copyToChannel(d, 0); const s = off.createBufferSource(); s.buffer = b; s.connect(off.destination); s.start();
        const r = await MPHear.words((await off.startRendering()).getChannelData(0).slice()); whisper = 'yes'; return (r && r.text || '').trim(); }
      catch (e) { if (/load|start|fetch|listener/i.test(e.message || '')) whisper = 'none'; return ''; } finally { try { ac.close(); } catch (e) { } } }
    return { has: () => !!key(), sheet: cb => window.MPLive ? MPLive.keySheet(cb) : cb && cb(false), read,
      onMsg(p, m) { if (m.t !== 'ear') return false; mint().then(v => H.send(p, { t: 'ear', id: m.id, v })).catch(() => H.send(p, { t: 'ear', id: m.id, v: null })); return true; } };
  }
  window.Ears = { hold, host, onHost };
})();
