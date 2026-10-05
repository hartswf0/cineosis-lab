/* What the Monte Carlo games share on the Party stand: the material (monte/material.json, loaded by monte/sim.js, with the clip
   paths of its spoken lines and music from party/monte-v.json), and a projector for its films: cards held as stills, shots as
   pictures that swap at the cut (the next one loads while this one plays), spoken lines on their own player, music beneath. */
(function () {
  let loading = null;
  function load() { return loading || (loading = Promise.all([fetch('monte/material.json').then(r => r.json()), fetch('party/monte-v.json').then(r => r.json())]).then(([M, VX]) => { MonteCinema.load(M); M.VX = VX; return M; })); }
  function Player(H, M) {
    const $ = s => document.querySelector(s), vids = [H.VP[0], H.VP[1]], voice = H.AP[0], mus = H.AP[1];
    let still = $('#vids img.still'); if (!still) { still = document.createElement('img'); still.className = 'still'; still.alt = ''; $('#vids').append(still); }
    const url = s => M.r2 + s.v, thumb = k => { const s = M.shots[k]; return s ? url(s).replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg') : ''; };
    let tok = 0, tm = [];
    function stop() { tok++; tm.forEach(clearTimeout); tm = []; vids.forEach(v => { v.pause(); v.classList.remove('on'); }); still.classList.remove('on'); voice.pause(); mus.pause(); H.cap(''); }
    function load(v, s) { const u = url(s); if (v.dataset.u !== u) { v.dataset.u = u; v.src = u; } }
    // play a film's events; o.maxSec trims it to a trailer; o.music false for none
    function play(f, o = {}, done) { stop(); const my = tok; H.show(null);
      let ev = f.ev, t = 0; if (o.maxSec) ev = ev.filter(e => { const keep = t < o.maxSec; t += e.dur; return keep; });
      const m = o.music !== false && f.music != null && M.music[f.music]; if (m && M.VX[m.i]) { const u = M.r2 + M.VX[m.i]; if (mus.dataset.u !== u) { mus.dataset.u = u; mus.src = u; } try { mus.currentTime = 0; } catch (e) { } mus.volume = .6; mus.play().catch(() => { }); }
      let side = 0;
      const nextShot = from => { for (let k = from; k < ev.length; k++) if (ev[k].kind === 'shot') return ev[k]; return null; };
      const step = n => { if (my !== tok) return; const e = ev[n]; if (!e) { stop(); done && done(); return; }
        const s = M.shots[e.k]; H.cap('');
        if (e.kind === 'card' || !s) { still.src = thumb(e.k); still.classList.add('on'); vids.forEach(v => { v.classList.remove('on'); v.pause(); }); mus.volume = e.silent ? 0 : .6; }
        else { const v = vids[side], o2 = vids[1 - side]; load(v, s); v.muted = true; try { v.currentTime = 0; } catch (x) { } v.play().catch(() => { }); v.classList.add('on'); o2.classList.remove('on'); o2.pause(); still.classList.remove('on'); side = 1 - side;
          const nx = nextShot(n + 1); if (nx) load(vids[side], M.shots[nx.k]);
          mus.volume = e.line != null ? .2 : .6;
          if (e.line != null) { const L = M.lines[e.line], u = M.r2 + (M.VX[L.i] || ''); tm.push(setTimeout(() => { if (my !== tok) return; if (voice.dataset.u !== u) { voice.dataset.u = u; voice.src = u; voice.addEventListener('loadedmetadata', () => { try { voice.currentTime = L.t0; } catch (x) { } }, { once: true }); } else { try { voice.currentTime = L.t0; } catch (x) { } } voice.play().catch(() => { }); H.cap('“' + L.text + '”'); tm.push(setTimeout(() => { voice.pause(); H.cap(''); }, (L.t1 - L.t0) * 1000 + 300)); }, (e.pause || 0) + 200)); } }
        tm.push(setTimeout(() => step(n + 1), Math.max(600, e.dur * 1000))); };
      step(0); }
    return { play, stop, thumb };
  }
  // what a card or a shot says, for a phone: the card's words, or the film it came from
  const label = (M, k) => { const s = M.shots[k]; if (!s) return ''; return s.title ? (s.text || '').split(' / ').slice(0, 3).join(' · ') : (s.why || s.film || ''); };
  Party.monte = { load, Player, label };
})();
