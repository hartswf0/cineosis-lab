/* How the lab feels under a finger: one small set of haptics and sounds that every instrument shares.
   Feel.play('select' | 'tap' | 'tick' | 'snap' | 'grab' | 'drop' | 'couple' | 'like' | 'success' | 'undo' | 'warn' | 'zoom')
   Haptics: navigator.vibrate where it exists (Android); on iPhone, Safari's switch control gives a system haptic
   when it is toggled inside a tap, so a hidden one is toggled. Sounds are synthesised, short and quiet, and step
   back further while her voice is playing. Feel.cycle() goes sound + touch → touch only → off; the choice is kept. */
(function () {
  'use strict';
  const KEY = 'cineosis.feel.v1';
  const load = () => { try { return Object.assign({ sound: true, touch: true, vol: 0.55 }, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) { return { sound: true, touch: true, vol: 0.55 }; } };
  let P = load(), ctx = null, iosSw = null, voice = null, last = {};
  const iOS = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  function ac() {
    if (!ctx) { const C = window.AudioContext || window.webkitAudioContext; if (!C) return null; ctx = new C(); }
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    return ctx;
  }
  function iosTap() {
    if (!iosSw) {
      const l = document.createElement('label'); l.setAttribute('aria-hidden', 'true');
      l.style.cssText = 'position:fixed;left:-9999px;top:0;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none';
      const i = document.createElement('input'); i.type = 'checkbox'; i.setAttribute('switch', ''); i.tabIndex = -1;
      l.appendChild(i); document.body.appendChild(l); iosSw = l;
    }
    iosSw.click();
  }
  function haptic(p) {
    if (!P.touch) return;
    if (navigator.vibrate) { try { navigator.vibrate(p); } catch (e) { /* not allowed */ } return; }
    if (iOS) { const n = Array.isArray(p) ? Math.ceil(p.length / 2) : 1; iosTap(); for (let k = 1; k < Math.min(n, 3); k++) setTimeout(iosTap, 70 * k); }
  }
  // one voice: an oscillator (or a noise burst) through a filter and an envelope
  function tone(c, o, g0) {
    const t = c.currentTime + (o.at || 0), d = o.d || 0.04, g = c.createGain(), peak = (o.g || 0.06) * g0;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), t + Math.min(0.006, d / 3)); g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    let src;
    if (o.noise) {
      const n = Math.max(1, Math.floor(c.sampleRate * d)), buf = c.createBuffer(1, n, c.sampleRate), ch = buf.getChannelData(0);
      for (let i = 0; i < n; i++) ch[i] = (Math.random() * 2 - 1) * (1 - i / n);
      src = c.createBufferSource(); src.buffer = buf;
      const f = c.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = o.f || 1800; f.Q.value = o.q || 1.2; src.connect(f); f.connect(g);
    } else {
      src = c.createOscillator(); src.type = o.type || 'sine'; src.frequency.setValueAtTime(o.f || 880, t);
      if (o.f2) src.frequency.exponentialRampToValueAtTime(o.f2, t + d);
      const f = c.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = o.lp || 6000; src.connect(f); f.connect(g);
    }
    g.connect(c.destination); src.start(t); src.stop(t + d + 0.02);
  }
  const K = {
    tick:    { h: 3,  gap: 40,  s: [{ f: 3200, d: 0.008, type: 'square', g: 0.012, lp: 5000 }] },
    tap:     { h: 6,  gap: 25,  s: [{ f: 1500, d: 0.02, type: 'triangle', g: 0.04 }] },
    select:  { h: 10, gap: 40,  s: [{ f: 620, f2: 930, d: 0.06, type: 'sine', g: 0.07 }, { noise: true, f: 3200, d: 0.015, g: 0.02 }] },
    snap:    { h: 4,  gap: 30,  s: [{ f: 2400, d: 0.012, type: 'square', g: 0.02, lp: 4000 }] },
    grab:    { h: 14, gap: 60,  s: [{ noise: true, f: 1400, d: 0.05, g: 0.05 }, { f: 300, f2: 420, d: 0.05, g: 0.04 }] },
    drop:    { h: [10, 30, 16], gap: 60, s: [{ f: 240, f2: 130, d: 0.1, g: 0.12 }, { noise: true, f: 800, d: 0.05, g: 0.04 }] },
    couple:  { h: [12, 40, 22], gap: 80, s: [{ f: 523.3, d: 0.08, g: 0.07, type: 'triangle' }, { f: 784, d: 0.12, g: 0.07, type: 'triangle', at: 0.07 }, { f: 196, f2: 150, d: 0.12, g: 0.07 }] },
    like:    { h: [6, 50, 6], gap: 80, s: [{ f: 988, d: 0.05, g: 0.05 }, { f: 1319, d: 0.08, g: 0.05, at: 0.075 }] },
    success: { h: [10, 30, 10, 30, 26], gap: 150, s: [{ f: 523.3, d: 0.09, g: 0.06, type: 'triangle' }, { f: 659.3, d: 0.09, g: 0.06, type: 'triangle', at: 0.08 }, { f: 784, d: 0.16, g: 0.07, type: 'triangle', at: 0.16 }] },
    undo:    { h: 8,  gap: 60,  s: [{ f: 760, f2: 480, d: 0.08, g: 0.05 }] },
    warn:    { h: [30, 40, 30], gap: 150, s: [{ f: 196, d: 0.07, g: 0.07, type: 'sawtooth', lp: 900 }, { f: 185, d: 0.1, g: 0.07, type: 'sawtooth', lp: 900, at: 0.09 }] },
    zoom:    { h: 4,  gap: 50,  s: [{ f: 1100, f2: 1500, d: 0.03, g: 0.025 }] },
  };
  function play(kind) {
    const k = K[kind]; if (!k) return;
    const now = performance.now(); if (last[kind] && now - last[kind] < k.gap) return; last[kind] = now;
    haptic(k.h);
    if (!P.sound) return;
    const c = ac(); if (!c) return;
    const under = voice && !voice.paused && !voice.muted ? 0.45 : 1;          // her voice first: feedback steps back under it
    k.s.forEach(o => tone(c, o, P.vol * under));
  }
  function set(o) { Object.assign(P, o); try { localStorage.setItem(KEY, JSON.stringify(P)); } catch (e) { /* storage blocked */ } }
  function cycle() { if (P.sound) set({ sound: false, touch: true }); else if (P.touch) set({ sound: false, touch: false }); else set({ sound: true, touch: true }); play('tap'); return label(); }
  function label() { return P.sound ? '🔊' : P.touch ? '📳' : '🔇'; }
  function title() { return P.sound ? 'sound and touch feedback (S: next)' : P.touch ? 'touch feedback only (S: next)' : 'no feedback (S: next)'; }
  // the first touch anywhere unlocks audio on browsers that need a gesture
  addEventListener('pointerdown', () => { if (P.sound) ac(); }, { once: true, capture: true });
  window.Feel = { play, set, cycle, label, title, get prefs() { return { ...P }; }, voice(a) { voice = a; } };
})();
