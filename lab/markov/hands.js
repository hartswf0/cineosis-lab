/* Hands, through the camera: the hand language of the WAG Cutting Room (hand-butter), carried to the Markov Poet's rooms.
   The tracker is the same one (MediaPipe hand landmarker, run in a worker on the CPU: the GPU delegate fails on some machines),
   one camera frame in flight at a time, and the same pose reader (open · point · pinch · fist · V · thumb up · thumb down).
   A hand is a cursor over the whole page: x and y are page coordinates, mirrored so the hand moves like a reflection.
   MPHands.start({preview: canvas, on: {frame(tracks), state(text), error(msg)}}) -> Promise<{stop()}>       call it in a tap
   track: {id: 'Left'|'Right', x, y (css px), closed (pinching, with hysteresis), pose, span (hand size in the camera: nearer is larger), marks}
   MPHands.active      {engine: 'slow'} forces the tracker that needs no WebGL */
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
    let stopped = false, busy = false, timer = 0, lastSeen = 0, worker = null, nRes = 0, tRes = performance.now(), seenEver = false; const mem = {};
    const h = { engine: '', stop() { if (stopped) return; stopped = true; clearInterval(timer); if (worker) worker.terminate(); stream.getTracks().forEach(t => t.stop()); if (api.active === h) api.active = null; try { video.srcObject = null; } catch (e) { } if (o.preview) o.preview.getContext('2d').clearRect(0, 0, o.preview.width, o.preview.height); tell('frame', []); tell('state', 'hands off'); } };
    api.active = h;
    // every result, from either tracker, comes through here: marks are 21 points per hand in camera fractions, ids say which hand
    function handle(marks, ids) { if (stopped) return; const aspect = video.videoWidth / video.videoHeight || 4 / 3, W = innerWidth, H = innerHeight, now = performance.now();
          const tracks = (marks || []).map((m, i) => { const id = ids[i] || 'Hand' + i, s = mem[id] || (mem[id] = { closed: false, x: null, y: null });
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
          tell('frame', tracks); }
    const tLoad = performance.now(), readyMsg = how => { tell('step', 'tracker', true, 'ready in ' + ((performance.now() - tLoad) / 1000).toFixed(1) + ' s' + how); tell('step', 'hands', null, 'hold a hand up to the camera'); };
    // The fast tracker (MediaPipe in a worker) reads each camera frame through WebGL, even on the CPU. Where the browser has WebGL
    // switched off it cannot run at all, so there is a second tracker that needs none: the same hand model on TensorFlow's WASM backend.
    const hasGL = (() => { try { const c = document.createElement('canvas'); return !!(c.getContext('webgl2') || c.getContext('webgl')); } catch (e) { return false; } })();
    async function startFast() { tell('step', 'tracker', null, 'fetching the hand tracker (about 10 MB, once)');
      const url = URL.createObjectURL(new Blob([SRC], { type: 'text/javascript' })); worker = new Worker(url); URL.revokeObjectURL(url); let ready = false;
      await new Promise((ok, no) => { const t = setTimeout(() => no(Error('the hand tracker took too long to download')), 45000);
        worker.onerror = e => { clearTimeout(t); no(Error(e.message || 'the hand tracker could not start')); };
        worker.onmessage = ({ data: d }) => {
          if (d.type === 'ready') { ready = true; clearTimeout(t); ok(); }
          else if (d.type === 'error') { clearTimeout(t); if (!ready) no(Error(d.message)); else { clearInterval(timer); worker.terminate(); worker = null; busy = false; startSlow(d.message).catch(e => { tell('step', 'tracker', false, e.message); tell('error', e.message); h.stop(); }); } }
          else if (d.type === 'result') { busy = false; handle(d.landmarks, (d.landmarks || []).map((_, i) => { const hd = d.handedness && d.handedness[i] && d.handedness[i][0]; return hd ? hd.categoryName : 'Hand' + i; })); } };
        worker.postMessage({ type: 'init' }); });
      h.engine = 'fast'; readyMsg('');
      timer = setInterval(async () => { if (busy || stopped || !worker || video.readyState < 2 || !video.videoWidth) return; busy = true; sent++; try { const f = await createImageBitmap(video); worker.postMessage({ type: 'frame', frame: f, time: performance.now() }, [f]); } catch (e) { busy = false; } }, 33); }
    const script = src => new Promise((ok, no) => { if (document.querySelector(`script[src="${src}"]`)) return ok(); const e = document.createElement('script'); e.src = src; e.onload = ok; e.onerror = () => no(Error('could not fetch ' + src.split('/').slice(-3).join('/'))); document.head.append(e); });
    async function startSlow(why) { tell('step', 'tracker', null, 'this browser has WebGL off: fetching the tracker that runs without it');
      const V = '4.22.0', base = 'https://cdn.jsdelivr.net/npm/@tensorflow/';
      await script(base + 'tfjs-core@' + V + '/dist/tf-core.min.js'); await script(base + 'tfjs-converter@' + V + '/dist/tf-converter.min.js'); await script(base + 'tfjs-backend-wasm@' + V + '/dist/tf-backend-wasm.min.js');
      await script('https://cdn.jsdelivr.net/npm/@tensorflow-models/hand-pose-detection@2.0.1/dist/hand-pose-detection.min.js');
      tf.wasm.setWasmPaths(base + 'tfjs-backend-wasm@' + V + '/dist/'); await tf.setBackend('wasm'); await tf.ready();
      const det = await handPoseDetection.createDetector(handPoseDetection.SupportedModels.MediaPipeHands, { runtime: 'tfjs', modelType: 'lite', maxHands: 2 });
      const cv = document.createElement('canvas'); cv.width = 320; cv.height = 240; const cx = cv.getContext('2d', { willReadFrequently: true });
      if (stopped) return; h.engine = 'slow'; readyMsg(' · without WebGL (slower)');
      timer = setInterval(async () => { if (busy || stopped || video.readyState < 2 || !video.videoWidth) return; busy = true; sent++;
        try { cx.drawImage(video, 0, 0, 320, 240); const r = await det.estimateHands(cx.getImageData(0, 0, 320, 240), { flipHorizontal: false }), seen = {};
          handle(r.map(x => x.keypoints.map(k => ({ x: k.x / 320, y: k.y / 240 }))), r.map(x => { let id = x.handedness === 'Left' ? 'Right' : 'Left'; if (seen[id]) id += '2'; seen[id] = 1; return id; })); }   // this model names hands as a mirror would: swapped to match the other tracker
        catch (e) { } busy = false; }, 50); }
    let sent = 0; setTimeout(() => { if (!stopped && !sent) tell('step', 'camera', false, 'the camera opened but gives no picture: another app may hold it, or it is covered'); }, 6000);
    try { if (o.engine === 'slow' || !hasGL) await startSlow(); else { try { await startFast(); } catch (e) { if (worker) { worker.terminate(); worker = null; } await startSlow(e.message); } } }
    catch (e) { tell('step', 'tracker', false, e.message || String(e)); h.stop(); throw e; }
    tell('state', 'hands on · show a hand to the camera');
    return h;
  };
  window.MPHands = api;
})();
