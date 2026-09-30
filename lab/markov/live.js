/* Live voice: the microphone streamed to OpenAI's realtime model over WebRTC. Nothing is downloaded, words come back while they
   are being spoken, and the model can act on the film through the tools the room gives it.
   The key is the operator's own, pasted into a hidden sheet and kept only in this browser's localStorage. It is sent to
   api.openai.com to mint a one-minute session secret and nowhere else. For testing; a shared site would put a relay in front.
   MPLive.hasKey() .setKey(k) .keySheet(onDone)
   MPLive.start({instructions, tools:[{name, description, parameters, run(args) -> any}], voice, on:{state, partial, heard, said, level, error}})
     -> Promise<{stop(), mute(bool), say(text)}>         call it directly inside the tap: Safari ties the microphone to the gesture
   states: asking · connecting · live · closed */
(function () {
  const KEY = 'mp.openai.key', MODEL = 'gpt-realtime', API = 'https://api.openai.com/v1/realtime';
  // the key lives in this browser's storage; when that storage is full or blocked (it is shared by every page on this site) it is
  // held for this tab only, so a full disk never reads as "no key"
  let mem = '';
  const get = () => { try { return localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || mem; } catch (e) { return mem; } };
  const api = { active: null, hasKey: () => !!get(), kept: 'browser',
    setKey: k => { k = (k || '').trim(); mem = k; api.kept = 'tab';
      try { k ? sessionStorage.setItem(KEY, k) : sessionStorage.removeItem(KEY); } catch (e) { }
      try { k ? localStorage.setItem(KEY, k) : localStorage.removeItem(KEY); if (!k || localStorage.getItem(KEY) === k) api.kept = 'browser'; } catch (e) { } } };

  // The microphone. A browser's default input is often a virtual or muted device (a light-sync driver, a loopback, a meeting app) that
  // gives only silence, so a stream from one of those is swapped for a real microphone before anything listens to it.
  const VIRTUAL = /virtual|hue sync|blackhole|loopback|soundflower|aggregate|zoomaudio|teams audio|krisp|obs|ndi|vb-?audio|cable|stereo mix/i;
  const Mic = { id: () => { try { return localStorage.getItem('mp.mic') || ''; } catch (e) { return ''; } }, set: id => { try { id ? localStorage.setItem('mp.mic', id) : localStorage.removeItem('mp.mic'); } catch (e) { } },
    audio: id => { const a = { echoCancellation: true, noiseSuppression: true, autoGainControl: true }; id = id == null ? Mic.id() : id; if (id) a.deviceId = { exact: id }; return a; },
    label: s => { const t = s && s.getAudioTracks()[0]; return t ? (t.label || 'microphone') : ''; },
    bad: s => { const t = s && s.getAudioTracks()[0]; return !t || t.muted || VIRTUAL.test(t.label || ''); },
    list: async () => (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'audioinput' && d.deviceId),
    open() { const first = navigator.mediaDevices.getUserMedia({ audio: Mic.audio() }).catch(e => { if (Mic.id() && /Overconstrained|NotFound/.test(e.name)) { Mic.set(''); return navigator.mediaDevices.getUserMedia({ audio: Mic.audio('') }); } throw e; });
      return first.then(async s => { if (Mic.id() || !Mic.bad(s)) return s;
        const real = (await Mic.list()).filter(d => d.deviceId !== 'default' && d.deviceId !== 'communications' && !VIRTUAL.test(d.label)), rank = d => /macbook|built-?in|internal|iphone/i.test(d.label) ? 0 : /microphone|mic|airpods|headset|usb/i.test(d.label) ? 1 : 2;
        real.sort((a, b) => rank(a) - rank(b));
        for (const d of real) { try { const t = await navigator.mediaDevices.getUserMedia({ audio: Mic.audio(d.deviceId) }); if (!t.getAudioTracks()[0].muted) { s.getTracks().forEach(x => x.stop()); Mic.set(d.deviceId); return t; } t.getTracks().forEach(x => x.stop()); } catch (e) { } }
        return s; }); } };
  window.MPMic = Mic;

  api.start = async function (o) {
    const on = o.on || {}, tell = (k, ...a) => { try { on[k] && on[k](...a); } catch (e) { } };
    if (api.active) api.active.stop();
    const key = get(); if (!key) throw new Error('no OpenAI key in this browser');
    tell('state', 'asking');
    // asked for first and synchronously in the tap, before any other await
    const micP = Mic.open();
    const out = new Audio(); out.autoplay = true; out.playsInline = true; out.play().catch(() => { });
    let AC = null, levelT = null; try { AC = new (window.AudioContext || window.webkitAudioContext)(); AC.resume(); } catch (e) { }
    const mic = await micP; tell('mic', Mic.label(mic) + (Mic.bad(mic) ? ' (silent: choose another in the menu)' : ''));
    const pc = new RTCPeerConnection(); let closed = false, dc = null;
    const stop = why => { if (closed) return; closed = true; clearInterval(levelT); try { mic.getTracks().forEach(t => t.stop()); } catch (e) { } try { dc && dc.close(); } catch (e) { } try { pc.close(); } catch (e) { } try { AC && AC.close(); } catch (e) { } out.srcObject = null; if (api.active === h) api.active = null; tell('state', 'closed', why); };
    const send = m => { if (dc && dc.readyState === 'open') dc.send(JSON.stringify(m)); };
    const h = { stop: () => stop(), mute: b => mic.getAudioTracks().forEach(t => t.enabled = !b), say: text => { send({ type: 'conversation.item.create', item: { type: 'message', role: 'user', content: [{ type: 'input_text', text }] } }); send({ type: 'response.create' }); } };
    api.active = h;
    try {
      tell('state', 'connecting');
      if (AC && on.level) { const an = AC.createAnalyser(); an.fftSize = 512; AC.createMediaStreamSource(mic).connect(an); const b = new Uint8Array(an.fftSize);
        levelT = setInterval(() => { an.getByteTimeDomainData(b); let m = 0; for (let i = 0; i < b.length; i++) m = Math.max(m, Math.abs(b[i] - 128)); tell('level', m / 128); }, 80); }
      pc.ontrack = e => { out.srcObject = e.streams[0]; out.play().catch(() => { }); };
      pc.onconnectionstatechange = () => { if (['failed', 'disconnected', 'closed'].includes(pc.connectionState)) stop('the connection dropped'); };
      mic.getTracks().forEach(t => pc.addTrack(t, mic));
      dc = pc.createDataChannel('oai-events');
      const tools = (o.tools || []), byName = Object.fromEntries(tools.map(t => [t.name, t]));
      const session = { type: 'realtime', model: MODEL, instructions: o.instructions || '', tool_choice: 'auto',
        tools: tools.map(t => ({ type: 'function', name: t.name, description: t.description, parameters: t.parameters || { type: 'object', properties: {} } })),
        audio: { input: { transcription: { model: 'gpt-4o-mini-transcribe', language: o.language || 'en' }, turn_detection: { type: 'server_vad', silence_duration_ms: 450, prefix_padding_ms: 250, create_response: true, interrupt_response: true }, noise_reduction: { type: 'near_field' } }, output: { voice: o.voice || 'marin' } } };
      dc.onopen = () => { send({ type: 'session.update', session }); tell('state', 'live'); };
      let part = '';
      dc.onmessage = async e => { let m; try { m = JSON.parse(e.data); } catch (x) { return; }
        if (m.type === 'input_audio_buffer.speech_started') { part = ''; tell('partial', ''); }
        else if (m.type === 'conversation.item.input_audio_transcription.delta') { part += m.delta || ''; tell('partial', part); }
        else if (m.type === 'conversation.item.input_audio_transcription.completed') { part = ''; tell('heard', (m.transcript || '').trim()); }
        else if (m.type === 'response.output_audio_transcript.done' || m.type === 'response.audio_transcript.done') tell('said', m.transcript || '');
        else if (m.type === 'response.function_call_arguments.done') { const t = byName[m.name]; let res;
          try { res = t ? await t.run(JSON.parse(m.arguments || '{}')) : { error: 'no such tool' }; } catch (x) { res = { error: String(x.message || x) }; }
          send({ type: 'conversation.item.create', item: { type: 'function_call_output', call_id: m.call_id, output: JSON.stringify(res == null ? { ok: true } : res) } }); send({ type: 'response.create' }); }
        else if (m.type === 'error') tell('error', (m.error && m.error.message) || 'the voice model reported an error'); };
      const offer = await pc.createOffer(); await pc.setLocalDescription(offer);
      const sec = await fetch(API + '/client_secrets', { method: 'POST', headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' }, body: JSON.stringify({ session: { type: 'realtime', model: MODEL } }) });
      if (!sec.ok) { const j = await sec.json().catch(() => ({})); throw new Error(sec.status === 401 ? 'OpenAI refused the key' : ((j.error && j.error.message) || 'OpenAI answered ' + sec.status)); }
      const sj = await sec.json(), eph = sj.value || (sj.client_secret && sj.client_secret.value); if (!eph) throw new Error('OpenAI gave no session secret');
      const ans = await fetch(API + '/calls?model=' + MODEL, { method: 'POST', headers: { Authorization: 'Bearer ' + eph, 'Content-Type': 'application/sdp' }, body: offer.sdp });
      if (!ans.ok) throw new Error('the call was refused (' + ans.status + '): ' + (await ans.text()).slice(0, 140));
      if (closed) return h;
      await pc.setRemoteDescription({ type: 'answer', sdp: await ans.text() });
      return h;
    } catch (e) { stop(e.message); throw e; }
  };

  // the hidden place for the key: a small sheet, reached from the menu
  api.keySheet = function (done) {
    const w = document.createElement('div'); w.style.cssText = 'position:fixed;inset:0;z-index:120;background:#000c;display:grid;place-items:end center';
    w.innerHTML = `<form style="width:min(460px,100%);background:#0e0d0c;border:1px solid #2a2723;border-radius:14px 14px 0 0;padding:18px 16px calc(18px + env(safe-area-inset-bottom));font:12px 'IBM Plex Mono',monospace;color:#efe9dd">
      <div style="letter-spacing:.2em;font-size:10px;color:#6f695f;margin-bottom:10px">LIVE VOICE · OPENAI KEY</div>
      <input type="text" name="mp-live-note" inputmode="text" autocorrect="off" data-lpignore="true" data-1p-ignore autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="sk-..." style="width:100%;box-sizing:border-box;background:#161412;border:1px solid #2e2b27;border-radius:8px;padding:12px;color:#efe9dd;font:16px 'IBM Plex Mono',monospace;-webkit-text-security:disc">
      <p style="color:#8a8378;line-height:1.5;margin:10px 0 14px">Kept only in this browser and sent only to api.openai.com. Speaking is billed to this key by the minute. For testing: use a key with a spending limit, and remove it on a shared device.</p>
      <div style="display:flex;gap:8px"><button type="submit" style="flex:1;min-height:44px;border-radius:8px;border:0;background:#e8c070;color:#14110c;font:inherit;cursor:pointer">SAVE</button>
      <button type="button" data-x="rm" style="min-height:44px;padding:0 14px;border-radius:8px;border:1px solid #2e2b27;background:none;color:#efe9dd;font:inherit;cursor:pointer">REMOVE</button>
      <button type="button" data-x="no" style="min-height:44px;padding:0 14px;border-radius:8px;border:1px solid #2e2b27;background:none;color:#efe9dd;font:inherit;cursor:pointer">CLOSE</button></div></form>`;
    const inp = w.querySelector('input'), end = () => { w.remove(); done && done(api.hasKey()); };
    if (api.hasKey()) inp.placeholder = 'a key is saved · paste a new one to replace it';
    // saved the moment it is pasted or typed: no way to close the sheet and lose it
    const keep = () => { const v = inp.value.trim(); if (v.length > 20) api.setKey(v); }; inp.addEventListener('input', keep); inp.addEventListener('change', keep);
    w.querySelector('form').onsubmit = e => { e.preventDefault(); keep(); if (inp.value.trim() && !api.hasKey()) { inp.value = ''; inp.placeholder = 'that does not look like a key · paste the whole sk-... key'; return; } end(); };
    w.querySelector('[data-x=rm]').onclick = () => { api.setKey(''); end(); }; w.querySelector('[data-x=no]').onclick = end;
    w.onclick = e => { if (e.target === w) end(); };
    document.body.append(w); setTimeout(() => inp.focus(), 50);
  };
  window.MPLive = api;
})();
