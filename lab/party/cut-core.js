/* THE CUT: a film as an edit list, the edits that change it, and a projector that plays it.
   film = { title, clips: [clip], sounds: [sound] }
   clip  = { id, kind: 'shot' | 'card', u (clip url), t0, t1 (in and out, seconds of the source), d (source length), text (a card's
             words), tr: 'cut' | 'dissolve' | 'dip' (how it comes in), own (play the shot's own sound), by (who placed it) }
           a card has no u; its length is t1 - t0
   sound = { id, kind: 'voice' | 'music' | 'frags', clip (the clip it is anchored to), off (seconds after that clip begins), u, t0, t1
             (the part of the source heard), vol, text, frags ([[u, t0, t1, words]] for a line said by many voices) }
   Sounds stay with their clip when the clip moves; a voice goes when its clip goes; music moves to the next clip.
   Runs on the Party stand (lab/party.html) and in the viewer (lab/film.html); a film travels as a link (deflate, base64url). */
(function (root) {
  const thumbOf = u => u ? String(u).replace('/clips/', '/thumbnails/').replace(/\.mp4.*$/, '.jpg') : '';
  let seq = 0; const nid = () => (Date.now() % 1e7).toString(36) + (seq++).toString(36);
  const len = c => Math.max(.3, (c.t1 || 0) - (c.t0 || 0));
  const slen = s => s.kind === 'frags' ? s.frags.reduce((a, f) => a + Math.max(.1, f[2] - f[1]), 0) + .06 * s.frags.length : Math.max(.1, (s.t1 || 0) - (s.t0 || 0));
  function starts(f) { let t = 0; const m = {}; f.clips.forEach(c => { m[c.id] = t; t += len(c); }); return { m, total: t }; }
  const blank = title => ({ title: title || 'Untitled', clips: [], sounds: [] });
  const shot = (u, t0, t1, x = {}) => Object.assign({ id: nid(), kind: 'shot', u, t0: +(+t0 || 0).toFixed(2), t1: +(+t1).toFixed(2), d: x.d || null, tr: 'cut', own: false }, x);
  const card = (text, secs = 2.5, x = {}) => Object.assign({ id: nid(), kind: 'card', text: String(text || ''), t0: 0, t1: secs, tr: 'cut' }, x);
  const voice = (clipId, u, t0, t1, x = {}) => Object.assign({ id: nid(), kind: 'voice', clip: clipId, off: 0, u, t0, t1, vol: 1 }, x);
  const music = (clipId, u, t0, secs, x = {}) => Object.assign({ id: nid(), kind: 'music', clip: clipId, off: 0, u, t0: t0 || 0, t1: (t0 || 0) + secs, vol: .7 }, x);
  const frags = (clipId, fr, x = {}) => Object.assign({ id: nid(), kind: 'frags', clip: clipId, off: .2, frags: fr, vol: 1 }, x);
  const R2 = s => +(+s).toFixed(2);

  // ---- the edits; each returns what it did, in words, or null if it changed nothing
  function apply(f, op) {
    const ix = id => f.clips.findIndex(c => c.id === id), c = op.id != null ? f.clips[ix(op.id)] : null;
    switch (op.op) {
      case 'title': f.title = String(op.text || '').slice(0, 80) || 'Untitled'; return 'titled the film “' + f.title + '”';
      case 'trim': { if (!c) return null; const d = +op.d || 0, max = c.kind === 'card' ? 12 : (c.d || c.t1 + 30);
        if (c.kind === 'card') { c.t1 = R2(Math.max(.8, Math.min(12, c.t1 + d))); return 'held a card ' + len(c).toFixed(1) + 's'; }
        if (op.edge === 'in') c.t0 = R2(Math.max(0, Math.min(c.t1 - .4, c.t0 + d))); else c.t1 = R2(Math.max(c.t0 + .4, Math.min(max, c.t1 + d)));
        return 'trimmed the ' + op.edge + ' of a shot to ' + len(c).toFixed(2) + 's'; }
      case 'slide': { if (!c || c.kind !== 'shot') return null; const d = +op.d || 0, max = c.d || c.t1 + 30, l = len(c); const t0 = Math.max(0, Math.min(max - l, c.t0 + d)); c.t0 = R2(t0); c.t1 = R2(t0 + l); return 'slid a shot to ' + c.t0.toFixed(2) + 's'; }
      case 'move': { const i = ix(op.id), j = i + (op.d > 0 ? 1 : -1); if (i < 0 || j < 0 || j >= f.clips.length) return null; [f.clips[i], f.clips[j]] = [f.clips[j], f.clips[i]]; return 'moved a ' + f.clips[j].kind + (op.d > 0 ? ' later' : ' earlier'); }
      case 'del': { const i = ix(op.id); if (i < 0) return null; const gone = f.clips.splice(i, 1)[0], next = f.clips[i] || f.clips[i - 1];
        f.sounds = f.sounds.filter(s => s.clip !== gone.id || (s.kind === 'music' && next && (s.clip = next.id))); return 'cut a ' + gone.kind; }
      case 'insert': { const it = op.item; if (!it) return null; it.id = it.id || nid(); const i = op.after == null ? -1 : ix(op.after); f.clips.splice(i + 1, 0, it); (op.sounds || []).forEach(s => { s.id = s.id || nid(); s.clip = it.id; f.sounds.push(s); }); return 'added a ' + it.kind; }
      case 'replace': { if (!c || !op.item) return null; const keep = { id: c.id, tr: c.tr, by: c.by }; Object.keys(c).forEach(k => delete c[k]); Object.assign(c, op.item, keep); return 'replaced a shot'; }
      case 'tr': { if (!c || !['cut', 'dissolve', 'dip'].includes(op.tr)) return null; c.tr = op.tr; return 'set a ' + op.tr; }
      case 'own': { if (!c || c.kind !== 'shot') return null; c.own = !!op.on; return (c.own ? 'opened' : 'muted') + ' a shot’s own sound'; }
      case 'text': { if (!c || c.kind !== 'card') return null; c.text = String(op.text || '').slice(0, 120); return 'wrote a card'; }
      case 'sound': { const s = op.sound; if (!s || ix(s.clip) < 0) return null; s.id = s.id || nid(); f.sounds.push(s); return 'laid ' + (s.kind === 'music' ? 'music' : 'a voice'); }
      case 'soff': { const s = f.sounds.find(x => x.id === op.sid); if (!s) return null; s.off = R2(Math.max(-3, Math.min(30, s.off + (+op.d || 0)))); return 'slipped a ' + s.kind + ' to ' + (s.off >= 0 ? '+' : '') + s.off.toFixed(2) + 's'; }
      case 'svol': { const s = f.sounds.find(x => x.id === op.sid); if (!s) return null; s.vol = R2(Math.max(0, Math.min(1, s.vol + (+op.d || 0)))); return 'set a ' + s.kind + ' to ' + Math.round(s.vol * 100) + '%'; }
      case 'slen': { const s = f.sounds.find(x => x.id === op.sid); if (!s || s.kind !== 'music') return null; s.t1 = R2(Math.max(s.t0 + 1, s.t1 + (+op.d || 0))); return 'music runs ' + (s.t1 - s.t0).toFixed(0) + 's'; }
      case 'sdel': { const n = f.sounds.length; f.sounds = f.sounds.filter(x => x.id !== op.sid); return f.sounds.length < n ? 'removed a sound' : null; }
    }
    return null;
  }
  // ---- a film as a link
  const b64u = buf => { let s = ''; const b = new Uint8Array(buf); for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
  const unb64u = s => { const t = atob(s.replace(/-/g, '+').replace(/_/g, '/')); const b = new Uint8Array(t.length); for (let i = 0; i < t.length; i++) b[i] = t.charCodeAt(i); return b; };
  async function encode(f) { const lean = { t: f.title, c: f.clips.map(c => c.kind === 'card' ? { k: 'c', id: c.id, x: c.text, l: len(c), tr: c.tr } : { id: c.id, u: c.u, a: c.t0, b: c.t1, tr: c.tr !== 'cut' ? c.tr : undefined, o: c.own ? 1 : undefined }), s: f.sounds };
    const raw = new TextEncoder().encode(JSON.stringify(lean));
    if (!root.CompressionStream) return 'j' + b64u(raw);
    const z = await new Response(new Blob([raw]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer(); return 'z' + b64u(z); }
  async function decode(s) { const kind = s[0], b = unb64u(s.slice(1));
    const txt = kind === 'z' ? await new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text() : new TextDecoder().decode(b);
    const L = JSON.parse(txt); return { title: L.t, clips: L.c.map(c => c.k === 'c' ? { id: c.id, kind: 'card', text: c.x, t0: 0, t1: c.l, tr: c.tr || 'cut' } : { id: c.id, kind: 'shot', u: c.u, t0: c.a, t1: c.b, tr: c.tr || 'cut', own: !!c.o }), sounds: L.s || [] }; }

  // ---- the projector: three pictures in rotation (the next two load while one plays), cards drawn over black, a dissolve or a dip
  // between shots, voices and music on a pool of players (music dips under a voice)
  function Player(o) {
    const vids = o.vids, auds = o.auds; let tok = 0, tm = [], raf = 0, ducks = 0;
    const later = (ms, fn) => tm.push(setTimeout(fn, ms));
    function stop() { tok++; tm.forEach(clearTimeout); tm = []; cancelAnimationFrame(raf); vids.forEach(v => { v.pause(); v.classList.remove('on'); v.style.transition = ''; }); auds.forEach(a => { a.pause(); a._busy = 0; }); if (o.card) o.card.classList.remove('on'); if (o.cap) o.cap.textContent = ''; ducks = 0; }
    function load(v, c) { if (v._u !== c.u) { v._u = c.u; v.src = c.u; } v._t0 = c.t0; const set = () => { try { v.currentTime = v._t0; } catch (e) { } }; if (v.readyState >= 1) set(); else v.addEventListener('loadedmetadata', set, { once: true }); }
    function grab() { const a = auds.find(x => !x._busy) || auds[0]; a._busy = 1; return a; }
    function hear(a, u, t0, secs, vol, my, isMusic) { if (a._u !== u) { a._u = u; a.src = u; } const set = () => { try { a.currentTime = t0; } catch (e) { } }; if (a.readyState >= 1) set(); else a.addEventListener('loadedmetadata', set, { once: true });
      a.volume = Math.max(0, Math.min(1, vol * (isMusic && ducks ? .35 : 1))); a._music = isMusic; a._vol = vol; a.play().catch(() => { }); later(secs * 1000, () => { if (my !== tok) return; a.pause(); a._busy = 0; }); }
    const duck = on => { ducks = Math.max(0, ducks + (on ? 1 : -1)); auds.forEach(a => { if (a._music && a._busy) a.volume = Math.max(0, Math.min(1, a._vol * (ducks ? .35 : 1))); }); };
    function play(f, from = 0, opts = {}) {
      stop(); const my = tok, clips = f.clips; if (!clips.length) { opts.onEnd && opts.onEnd(); return; }
      from = Math.max(0, Math.min(clips.length - 1, from)); const S = starts(f), base = S.m[clips[from].id], end = opts.until != null ? Math.min(S.total, opts.until) : S.total;
      const put = new Map(); let rot = 0;
      const prep = k => { const c = clips[k]; if (!c || c.kind !== 'shot' || put.has(k)) return; const v = vids[rot++ % vids.length]; load(v, c); put.set(k, v); };
      prep(from); prep(from + 1);
      const t00 = performance.now();
      const step = k => { if (my !== tok) return; const c = clips[k]; if (!c || S.m[c.id] >= end - .01) { stop(); opts.onEnd && opts.onEnd(); return; }
        const showIt = () => { if (my !== tok) return;
          if (c.kind === 'card') { o.card.innerHTML = `<div>${String(c.text).replace(/[&<>]/g, x => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[x])).replace(/\n/g, '<br>')}</div>`; o.card.classList.add('on'); vids.forEach(v => { v.classList.remove('on'); v.pause(); }); }
          else { const v = put.get(k) || (prep(k), put.get(k)); v.muted = !c.own; v.volume = 1; try { if (Math.abs(v.currentTime - c.t0) > .15) v.currentTime = c.t0; } catch (e) { } v.play().catch(() => { });
            v.style.transition = c.tr === 'dissolve' ? 'opacity .7s' : ''; v.style.zIndex = 2; v.classList.add('on');
            vids.forEach(w => { if (w !== v) { w.style.zIndex = 1; if (c.tr === 'dissolve') later(750, () => { if (my === tok && !w._keep) { w.classList.remove('on'); w.pause(); } }); else { w.classList.remove('on'); w.pause(); } } });
            o.card.classList.remove('on'); }
          later(400, () => { prep(k + 1); prep(k + 2); }); };
        if (c.tr === 'dip' && k > from) { vids.forEach(v => v.classList.remove('on')); o.card.classList.remove('on'); later(350, showIt); } else showIt();
        later(len(c) * 1000, () => step(k + 1)); };
      // the sounds, each at its clip's start plus its offset
      f.sounds.forEach(s => { if (S.m[s.clip] == null) return; const at = S.m[s.clip] + (s.off || 0) - base, L = slen(s); if (at + L <= 0 || at >= end - base) return; const skip = Math.max(0, -at);
        later(Math.max(0, at) * 1000, () => { if (my !== tok) return;
          if (s.kind === 'music') { hear(grab(), s.u, s.t0 + skip, Math.min(L - skip, end - base - Math.max(0, at)), s.vol == null ? .7 : s.vol, my, true); return; }
          duck(true); if (s.text && o.cap) o.cap.textContent = '“' + s.text + '”';
          const done = () => { duck(false); if (o.cap && s.text && o.cap.textContent === '“' + s.text + '”') o.cap.textContent = ''; };
          if (s.kind === 'voice') { hear(grab(), s.u, s.t0 + skip, Math.max(.1, L - skip), s.vol == null ? 1 : s.vol, my, false); later((L - skip) * 1000, done); return; }
          let t = 0, said = ''; s.frags.forEach((fr, i) => { const d = Math.max(.1, fr[2] - fr[1]); if (t + d > skip) later(Math.max(0, t - skip) * 1000, () => { if (my !== tok) return; hear(grab(), fr[0], fr[1], d, s.vol == null ? 1 : s.vol, my, false); said += (said ? ' ' : '') + fr[3]; if (o.cap && !s.text) o.cap.textContent = said; }); t += d + .06; });
          later((L - skip) * 1000, done); }); });
      const tick = () => { if (my !== tok) return; const t = base + (performance.now() - t00) / 1000; let k = clips.findIndex((c, i) => S.m[c.id] <= t && t < S.m[c.id] + len(c)); opts.onTick && opts.onTick(t, k, S.total); raf = requestAnimationFrame(tick); };
      raf = requestAnimationFrame(tick); step(from); }
    return { play, stop };
  }
  root.Cut = { thumbOf, nid, len, slen, starts, blank, shot, card, voice, music, frags, apply, encode, decode, Player };
})(typeof window !== 'undefined' ? window : globalThis);
