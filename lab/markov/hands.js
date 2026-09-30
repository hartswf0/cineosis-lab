/* Hands, through the camera: the hand language of the WAG Cutting Room (hand-butter), carried to the Markov Poet's rooms.
   The tracker is the same one (MediaPipe hand landmarker, run in a worker on the CPU: the GPU delegate fails on some machines),
   one camera frame in flight at a time, and the same pose reader (open · point · pinch · fist · V · thumb up · thumb down).
   A hand is a cursor over the whole page: x and y are page coordinates, mirrored so the hand moves like a reflection.
   MPHands.start({preview: canvas, on: {frame(tracks), state(text), error(msg)}}) -> Promise<{stop()}>       call it in a tap
   track: {id: 'Left'|'Right', x, y (css px), closed (pinching, with hysteresis), pose, span (hand size in the camera: nearer is larger), marks}
   MPHands.active */
(function () {
  const SRC = `let tracker;onmessage=async({data:d})=>{try{if(d.type==='init'){const mod=await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/+esm');const files=await mod.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/wasm');tracker=await mod.HandLandmarker.createFromOptions(files,{baseOptions:{modelAssetPath:'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',delegate:'CPU'},runningMode:'VIDEO',numHands:2,minHandDetectionConfidence:.5,minHandPresenceConfidence:.5,minTrackingConfidence:.5});postMessage({type:'ready'});}else if(d.type==='frame'){try{const r=tracker.detectForVideo(d.frame,d.time);postMessage({type:'result',landmarks:r.landmarks,handedness:r.handedness});}finally{d.frame.close();}}}catch(e){postMessage({type:'error',message:e.message});}}`;
  const LINKS = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12], [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [0, 17], [17, 18], [18, 19], [19, 20]];
  const api = { active: null };
  function poseOf(h, aspect, closed) {                                     // hand-butter's gestureOf
    const d = (a, b) => Math.hypot((a.x - b.x) * aspect, a.y - b.y);
    const ext = [8, 12, 16, 20].map((tip, i) => { const pip = h[[6, 10, 14, 18][i]], base = h[[5, 9, 13, 17][i]], end = h[tip]; return d(end, h[0]) > d(pip, h[0]) * 1.06 && d(end, base) > d(pip, base) * 1.35; });
    const n = ext.filter(Boolean).length, span = Math.max(.025, d(h[5], h[17])), ty = h[4].y - h[2].y, tx = (h[4].x - h[2].x) * aspect;
    const thumbOut = d(h[4], h[5]) > span * .55 && d(h[4], h[2]) > span * .55;
    if (n <= 1 && thumbOut && Math.abs(ty) > Math.abs(tx) * .65 && Math.abs(ty) > span * .38) return ty > 0 ? 'down' : 'up';
    if (closed) return 'pinch';
    if (ext[0] && ext[1] && !ext[2] && !ext[3]) return 'V';
    if (n === 0) return 'fist';
    if (n >= 3) return 'open';
    return 'point';
  }
  api.start = async function (o = {}) {
    const on = o.on || {}, tell = (k, ...a) => { try { on[k] && on[k](...a); } catch (e) { } };
    if (api.active) api.active.stop();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error('this browser gives pages no camera (it needs https)');
    tell('step', 'camera', null, 'asking: allow the camera when the browser asks');
    const want = id => ({ video: Object.assign({ width: { ideal: 640 }, height: { ideal: 480 } }, id ? { deviceId: { exact: id } } : { facingMode: 'user' }), audio: false });
    let stream; try { stream = await navigator.mediaDevices.getUserMedia(want()); } catch (e) { tell('step', 'camera', false, /NotAllowed/.test(e.name) ? 'blocked: allow the camera for this site (the camera icon in the address bar), then tap the hand again' : /NotFound/.test(e.name) ? 'no camera was found' : /NotReadable/.test(e.name) ? 'the camera is in use by another app' : (e.name + ': ' + e.message)); throw e; }
    // a virtual camera (a streaming or meeting driver) is often the default and shows nothing: take a real one instead
    const VIRT = /virtual|obs|snap camera|ndi|mmhmm|camo|epoccam|droidcam|hue/i, lab = () => (stream.getVideoTracks()[0] || {}).label || 'camera';
    if (VIRT.test(lab())) { try { const real = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput' && d.deviceId && !VIRT.test(d.label)); if (real.length) { const s2 = await navigator.mediaDevices.getUserMedia(want(real[0].deviceId)); stream.getTracks().forEach(t => t.stop()); stream = s2; } } catch (e) { } }
    const video = o.view || document.createElement('video'); video.muted = true; video.playsInline = true; video.setAttribute('playsinline', ''); video.srcObject = stream; await video.play().catch(() => { });
    tell('step', 'camera', true, lab());
    const url = URL.createObjectURL(new Blob([SRC], { type: 'text/javascript' })), worker = new Worker(url); URL.revokeObjectURL(url);
    let stopped = false, busy = false, timer = 0, ready = false, lastSeen = 0; const mem = {};
    const h = { stop() { if (stopped) return; stopped = true; clearInterval(timer); worker.terminate(); stream.getTracks().forEach(t => t.stop()); if (api.active === h) api.active = null; try { video.srcObject = null; } catch (e) { } if (o.preview) o.preview.getContext('2d').clearRect(0, 0, o.preview.width, o.preview.height); tell('frame', []); tell('state', 'hands off'); } };
    api.active = h; tell('state', 'fetching the hand tracker'); tell('step', 'tracker', null, 'fetching the hand tracker (about 10 MB, once)'); const tLoad = performance.now(); let nRes = 0, tRes = performance.now(), seenEver = false;
    await new Promise((ok, no) => { const t = setTimeout(() => no(Error('the hand tracker took too long to download')), 45000);
      worker.onerror = e => { clearTimeout(t); tell('step', 'tracker', false, e.message || 'the hand tracker could not start'); no(Error(e.message || 'the hand tracker could not start')); };
      worker.onmessage = ({ data: d }) => {
        if (d.type === 'ready') { ready = true; clearTimeout(t); tell('step', 'tracker', true, 'ready in ' + ((performance.now() - tLoad) / 1000).toFixed(1) + ' s'); tell('step', 'hands', null, 'hold a hand up to the camera'); ok(); }
        else if (d.type === 'error') { clearTimeout(t); tell('step', 'tracker', false, d.message); if (!ready) no(Error(d.message)); else { tell('error', d.message); h.stop(); } }
        else if (d.type === 'result') { busy = false; if (stopped) return; const aspect = video.videoWidth / video.videoHeight || 4 / 3, W = innerWidth, H = innerHeight, now = performance.now();
          const tracks = (d.landmarks || []).map((m, i) => { const hd = d.handedness && d.handedness[i] && d.handedness[i][0], id = hd ? hd.categoryName : 'Hand' + i, s = mem[id] || (mem[id] = { closed: false, x: null, y: null });
            const dist = (a, b) => Math.hypot((a.x - b.x) * aspect, a.y - b.y), span = Math.max(.025, dist(m[5], m[17])), pr = dist(m[4], m[8]) / span;
            s.closed = s.closed ? pr < .62 : pr < .38;                                                 // pinch, with hysteresis so a held thing is not dropped by jitter
            // the middle 70% of the camera covers the whole page, so edges can be reached without leaving the frame
            const px = (m[4].x + m[8].x) / 2, py = (m[4].y + m[8].y) / 2, tx = Math.min(1, Math.max(0, ((1 - px) - .15) / .7)) * W, ty = Math.min(1, Math.max(0, (py - .12) / .7)) * H, k = s.closed ? .35 : .5;
            s.x = s.x == null ? tx : s.x + (tx - s.x) * k; s.y = s.y == null ? ty : s.y + (ty - s.y) * k; s.seen = now;
            return { id, x: s.x, y: s.y, closed: s.closed, pose: poseOf(m, aspect, s.closed), span, marks: m }; });
          for (const k in mem) if (now - mem[k].seen > 600) delete mem[k];
          if (tracks.length) lastSeen = now; nRes++;
          if (now - tRes > 500) { const fps = Math.round(nRes * 1000 / (now - tRes)); nRes = 0; tRes = now; if (tracks.length) seenEver = true; tell('step', 'hands', tracks.length ? true : null, tracks.length ? tracks.map(t => t.id.toLowerCase() + ' ' + t.pose).join(' · ') + ' · ' + fps + '/s' : (seenEver ? 'no hand in view' : 'hold a hand up to the camera') + ' · looking ' + fps + '/s'); }
          if (o.preview) { const c = o.preview, x = c.getContext('2d'); c.width = 160; c.height = 120; x.clearRect(0, 0, 160, 120); tracks.forEach((t, i) => { x.strokeStyle = x.fillStyle = i ? '#85bdff' : '#c4f46a'; x.lineWidth = 2.5;
            for (const [a, b] of LINKS) { x.beginPath(); x.moveTo((1 - t.marks[a].x) * 160, t.marks[a].y * 120); x.lineTo((1 - t.marks[b].x) * 160, t.marks[b].y * 120); x.stroke(); } }); }
          tell('frame', tracks); } };
      worker.postMessage({ type: 'init' }); }).catch(e => { h.stop(); throw e; });
    tell('state', 'hands on · show a hand to the camera');
    let sent = 0; setTimeout(() => { if (!stopped && !sent) tell('step', 'camera', false, 'the camera opened but gives no picture: another app may hold it, or it is covered'); }, 4000);
    timer = setInterval(async () => { if (busy || stopped || video.readyState < 2 || !video.videoWidth) return; busy = true; sent++; try { const f = await createImageBitmap(video); worker.postMessage({ type: 'frame', frame: f, time: performance.now() }, [f]); } catch (e) { busy = false; } }, 33);
    return h;
  };
  window.MPHands = api;
})();
