/* One clock for every instrument in the lab.
   Her voice runs through all of them on the same 24 minutes, so an instrument tells the others where it is:
   - switch tools while the film plays (same tab or a new one) and the next one picks up at the same moment;
   - keep several tools open side by side and the one you play leads: the others follow it silently, in step,
     until you press play in one of them, which then takes the lead.
   Usage:  LabClock.attach({ name: 'Studio', audio, play(), pause(), seek(t) })
   The page keeps its own transport; the clock only watches its audio element and calls those four. */
(function () {
  'use strict';
  const KEY = 'cineosis.clock.v1', FRESH = 15000;
  const me = Math.random().toString(36).slice(2, 9);
  const ch = 'BroadcastChannel' in window ? new BroadcastChannel('cineosis.clock') : null;
  let H = null, lead = null, quiet = 0, lastPost = 0, pill = null, hear = false, since = 0, pending = null;
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } };
  const ext = m => m.playing ? m.t + (Date.now() - m.at) / 1000 * (m.rate || 1) : m.t;
  const fmt = t => { t = Math.max(0, t || 0); const m = Math.floor(t / 60); return m + ':' + (t - m * 60).toFixed(1).padStart(4, '0'); };
  function post(force) {
    if (!H) return; const now = performance.now(); if (!force && now - lastPost < 400) return; lastPost = now;
    const a = H.audio, m = { id: me, name: H.name, t: a.currentTime || 0, playing: !a.paused && !lead && !pending, rate: a.playbackRate || 1, at: Date.now(), since, page: location.pathname };
    try { localStorage.setItem(KEY, JSON.stringify(m)); } catch (e) { /* storage blocked */ }
    if (ch) ch.postMessage(m);
  }
  // the clock's own calls to the page must not count as the person pressing play or pause
  const as = fn => { quiet++; try { return fn(); } finally { setTimeout(() => { quiet--; }, 300); } };
  function show(html, onclick) {
    if (!pill) {
      pill = document.createElement('button'); pill.type = 'button';
      pill.style.cssText = 'position:fixed;left:10px;bottom:calc(10px + env(safe-area-inset-bottom));z-index:9999;font:600 11px/1.2 ui-monospace,monospace;background:#141414;color:#fff;border:1px solid #444;border-radius:14px;padding:6px 11px;box-shadow:0 4px 14px #0006;cursor:pointer;max-width:80vw;text-align:left';
      document.body.appendChild(pill);
    }
    pill.innerHTML = html; pill.onclick = onclick; pill.hidden = !html;
  }
  function follow(m) {
    const a = H.audio;
    if (!lead) { lead = m; a.muted = true; as(() => { H.seek(ext(m)); H.play(); }); }
    lead = m;
    const want = ext(m);
    if (Math.abs((a.currentTime || 0) - want) > 0.25) try { a.currentTime = want; } catch (e) { /* not ready */ }
    show(`⟲ following <b>${m.name}</b> · ${fmt(want)} — tap to lead from here`, () => { a.muted = false; lead = null; show(''); post(true); });
  }
  function release(m) {
    if (!lead) return;
    const a = H.audio; lead = null; as(() => { H.pause(); H.seek(m.t); }); a.muted = false; show('');
  }
  function onMessage(m) {
    if (!H || !m || m.id === me) return;
    // the most recent press of play leads: a tab that started playing after the sender keeps its lead
    if (m.playing) { if (pending) { clearTimeout(pending); pending = null; } if (!lead && !H.audio.paused && since > (m.since || 0)) return; follow(m); }
    else if (lead && lead.id === m.id) release(m);
  }
  if (ch) ch.onmessage = e => onMessage(e.data);
  addEventListener('storage', e => { if (e.key === KEY && !ch) { try { onMessage(JSON.parse(e.newValue)); } catch (err) { /* ignore */ } } });

  function attach(host) {
    H = host; const a = H.audio;
    a.addEventListener('play', () => { if (quiet) return; since = Date.now(); if (pending) { clearTimeout(pending); pending = null; } if (lead) { lead = null; a.muted = false; show(''); } post(true); });
    a.addEventListener('pause', () => { if (!quiet && !lead) post(true); });
    a.addEventListener('seeked', () => { if (!lead) post(true); });
    a.addEventListener('timeupdate', () => { if (!lead) post(false); });
    addEventListener('pagehide', () => { if (!lead) post(true); });
    // arriving from another tool: pick up where it was
    const m = read();
    if (m && m.id !== me) {
      const age = Date.now() - m.at;
      if (m.playing && age < FRESH) {
        // is that tool still open and playing? then follow it; if it has gone quiet (you navigated away from it), carry on here
        pending = setTimeout(() => { pending = null; resume(m, age); }, 700);
      } else if (age < 12 * 3600e3) as(() => H.seek(m.t));
    }
    function resume(m, age) {
      {
        since = Date.now();
        const go = () => as(() => { H.seek(ext(m)); H.play(); });
        a.muted = false; quiet++;
        const done = () => setTimeout(() => { quiet--; }, 300);
        a.play().then(() => { a.pause(); go(); done(); }).catch(() => { done();
          // the browser wants a tap before sound: keep the beat in silence, and let a tap bring the voice back
          a.muted = true; hear = true; go();
          show(`🔈 continuing from <b>${m.name}</b> — tap to hear`, () => { a.muted = false; hear = false; show(''); });
        });
      }
    }
    return { post: () => post(true), get leading() { return !lead; }, get following() { return lead ? lead.name : null; } };
  }
  window.LabClock = { attach, read };
})();
