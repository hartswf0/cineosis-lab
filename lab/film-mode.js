/* THE ARCHIVE IN MOTION. Open the explorer with ?film and it plays itself: a director drives its own views (wall, map, ring, strata,
   cut-outs, reel) and its own filters (decade, colour, sign) as a film, under a D-A-E score. No narration; only the name of what you
   are seeing, small, as it changes. Esc or the × hands the explorer back to you. Uses app.js's own objects: Shell, F, SORT, refresh,
   Wall, MapMode, Ring, Strata. */
(function () {
  if (!/[?&]film\b/.test(location.search)) return;
  const CUE = "score/cues/dae-chicha-surf-boreal-glitch-workshop.m4a";
  const css = document.createElement("style");
  css.textContent = `body.filming #top,body.filming #facets,body.filming #status,body.filming #livebar,body.filming .hud,body.filming #guide,body.filming #tip{opacity:0!important;pointer-events:none!important;transition:opacity .8s}
    body.filming #stage{inset:0!important;left:0!important;top:0!important}
    #fm-cap{position:fixed;left:50%;top:18px;transform:translateX(-50%);z-index:90;font:600 12px/1 "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.22em;color:#fff;background:rgba(0,0,0,.55);padding:8px 14px;border-radius:16px;opacity:0;transition:opacity .7s;pointer-events:none;white-space:nowrap}
    #fm-cap.on{opacity:1}
    #fm-start{position:fixed;inset:0;z-index:95;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;text-align:center;padding:24px;background:rgba(8,7,6,.9);color:#ece6da}
    #fm-start h1{font:900 clamp(38px,8vw,96px)/.9 "Arial Black",Impact,sans-serif}
    #fm-start p{font:12px "IBM Plex Mono",monospace;letter-spacing:.12em;color:#9a9285}
    #fm-start button{font:700 13px "IBM Plex Mono",monospace;letter-spacing:.16em;padding:13px 28px;border-radius:26px;background:#ece6da;color:#0b0a09;border:0;cursor:pointer}
    #fm-x{position:fixed;right:14px;top:12px;z-index:96;width:36px;height:36px;border-radius:50%;border:1px solid rgba(255,255,255,.3);background:rgba(0,0,0,.5);color:#fff;font:16px sans-serif;cursor:pointer;opacity:.35}
    #fm-x:hover{opacity:1}`;
  document.head.appendChild(css);
  const cap = Object.assign(document.createElement("div"), { id: "fm-cap" });
  const start = Object.assign(document.createElement("div"), { id: "fm-start" });
  start.innerHTML = `<h1>THE ARCHIVE<br>IN MOTION</h1><p>THE EXPLORER PLAYS ITSELF · WALL · MAP · RING · STRATA · CUT-OUTS · REEL</p><button id="fm-go">▶ PLAY</button><p id="fm-n">loading the archive…</p>`;
  const x = Object.assign(document.createElement("button"), { id: "fm-x", textContent: "×", title: "Stop the film and use the explorer" });
  document.body.append(cap, start, x);
  let RUN = 0, AC = null, G = null, el = null;
  const sleep = (ms, run) => new Promise(r => setTimeout(() => r(run === RUN), ms));
  const say = t => { cap.textContent = t; cap.classList.add("on"); clearTimeout(say.h); say.h = setTimeout(() => cap.classList.remove("on"), 3200); };
  const tween = (ms, fn, run) => new Promise(r => { const t0 = performance.now(); const step = () => { if (run !== RUN) return r(false); const k = Math.min(1, (performance.now() - t0) / ms), e = k * k * (3 - 2 * k); fn(e); if (k < 1) requestAnimationFrame(step); else r(true); }; step(); });
  function score() {
    if (!AC) { AC = new (window.AudioContext || window.webkitAudioContext)(); el = new Audio(CUE); el.loop = true; G = AC.createGain(); G.gain.value = 0; AC.createMediaElementSource(el).connect(G).connect(AC.destination); }
    if (AC.state === "suspended") AC.resume(); el.currentTime = 0; el.play().catch(() => { }); G.gain.setTargetAtTime(.6, AC.currentTime, 1.5);
  }
  const reset = () => { F.signs = new Set(); F.dec = new Set(); F.hue = null; F.color = "all"; F.subj = new Set(); F.q = ""; F.terms = []; F.signTerms = []; F.decTerms = []; GROUP = "none"; SORT.key = "sign"; SORT.dir = 1; };
  const mode = m => { if (Shell.mode !== m) Shell.setMode(m); };
  const DECS = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010];
  const HUES = [[345, 15], [15, 45], [45, 75], [75, 150], [150, 210], [210, 260], [260, 300], [300, 345]];

  async function wall(run) {
    reset(); SORT.key = "hue"; refresh(); mode("wall"); say("WALL · EVERY SHOT, BY COLOUR");
    const sc = Wall.grid && Wall.grid.sc;
    if (sc) await tween(16000, e => { sc.scrollTop = e * Math.min(sc.scrollHeight - sc.clientHeight, 9000); }, run);
    for (const d of DECS) {   // the decades, one after another
      if (run !== RUN) return; F.dec = new Set([d]); SORT.key = "hue"; refresh(); if (sc) sc.scrollTop = 0; say(`WALL · THE ${d}s`); if (!await sleep(1500, run)) return;
    }
    F.dec = new Set();
    for (const h of HUES) { if (run !== RUN) return; F.hue = h; refresh(); say("WALL · ONE COLOUR AT A TIME"); if (!await sleep(1100, run)) return; }
    F.hue = null; refresh();
  }
  async function map(run) {
    reset(); refresh(); mode("map"); MapMode.kind = L.has.xy ? "xy" : "hue"; MapMode.build(); MapMode.fit(); say("MAP · SHOTS BY LIKENESS");
    if (!await sleep(2500, run)) return;
    const pts = MapMode.P.filter(p => p.s.xy);
    for (let k = 0; k < 5 && pts.length; k++) {   // fly into a neighbourhood of alike shots, and out again
      const p = pts[Math.floor(Math.random() * pts.length)], c = MapMode.cam, from = { x: c.x, y: c.y, z: c.z }, to = { x: p.x, y: p.y, z: from.z * (7 + Math.random() * 5) };
      if (!await tween(4200, e => { c.x = from.x + (to.x - from.x) * e; c.y = from.y + (to.y - from.y) * e; c.z = from.z * Math.pow(to.z / from.z, e); MapMode.req(); }, run)) return;
      if (!await sleep(1600, run)) return;
      const back = { x: c.x, y: c.y, z: c.z }; if (!await tween(2600, e => { c.z = back.z * Math.pow(from.z * 1.6 / back.z, e); MapMode.req(); }, run)) return;
    }
    for (const [kind, name] of [["hue", "MAP · COLOUR × DECADE"], ["sign", "MAP · SIGN × DECADE"]]) {
      if (run !== RUN) return; MapMode.kind = kind; MapMode.build(); MapMode.fit(); say(name);
      if (!await sleep(2800, run)) return;
      const c = MapMode.cam, z0 = c.z, x0 = c.x;
      if (!await tween(9000, e => { c.z = z0 * (1 + 2.2 * Math.sin(e * Math.PI)); c.x = x0 + (e - .5) * .5; MapMode.req(); }, run)) return;
    }
    for (const d of DECS.slice(2, 10)) { if (run !== RUN) return; F.dec = new Set([d]); refresh(); say(`MAP · THE ${d}s`); if (!await sleep(1300, run)) return; }
    F.dec = new Set(); refresh();
  }
  async function ring(run) {
    reset(); refresh(); mode("ring"); Ring.auto = true; say("RING · THE FIRST 240, ON A CYLINDER");
    if (!await tween(6000, e => { Ring.vel = 2.4 * (1 - e) + .3; Ring.tilt = -6 + 14 * Math.sin(e * Math.PI); Ring.apply && Ring.apply(); }, run)) return;
    const signs = L.signs.map(s => s.n).filter(n => VIEW.some(v => (v._read || []).includes(n))).slice(0, 44);
    for (let k = 0; k < 7 && signs.length; k++) {   // one sign at a time: the ring rebuilds from its shots
      const n = signs[Math.floor(Math.random() * signs.length)]; F.signs = new Set([n]); refresh();
      say(`RING · ${L.S[n].symbol} · ${L.S[n].name.toUpperCase()}`); Ring.vel = 3;
      if (!await sleep(3600, run)) return;
    }
    F.signs = new Set(); refresh();
  }
  async function strata(run) {
    reset(); SORT.key = "hue"; refresh(); mode("strata"); say("STRATA · EVERY SHOT AS A STACK OF ITS FRAMES");
    if (!await sleep(1500, run)) return;
    const t0 = performance.now(), sc = Strata.grid && Strata.grid.sc;
    while (run === RUN && performance.now() - t0 < 22000) {   // run the stacks in a wave, a cell at a time
      const cells = [...document.querySelectorAll("#m-strata .stc")].filter(c => { const r = c.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
      for (const c of cells) { if (run !== RUN) return; Strata.heat(c); await sleep(260, run); }
      if (sc) await tween(1800, e => { sc.scrollTop += 6; }, run);
      if (sc) sc.scrollTop += Math.round(innerHeight * .6);
    }
    Strata.heat(null);
  }
  async function cuts(run) { reset(); refresh(); mode("cuts"); say("CUT-OUTS · FIGURES LIFTED FROM THE SHOTS"); await sleep(9000, run); }
  async function reel(run) { reset(); refresh(); mode("reel"); say("REEL · THE TABLE, SIGN BY SIGN"); await sleep(1200, run); try { Reel.start && Reel.start(); } catch (e) { } await sleep(26000, run); }
  async function film() {
    const run = ++RUN; document.body.classList.add("filming"); start.hidden = true; score();
    for (const part of [wall, map, ring, strata, cuts, reel, map]) { if (run !== RUN) return; await part(run); }
    if (run === RUN) { G && G.gain.setTargetAtTime(0, AC.currentTime, 2); say("THE ARCHIVE · " + L.shots.length.toLocaleString() + " SHOTS"); }
  }
  function stop() { RUN++; document.body.classList.remove("filming"); start.hidden = true; x.hidden = true; if (G) G.gain.setTargetAtTime(0, AC.currentTime, .6); setTimeout(() => el && el.pause(), 900); }
  x.onclick = stop; addEventListener("keydown", e => { if (e.key === "Escape" && document.body.classList.contains("filming")) stop(); }, true);
  document.getElementById("fm-go").onclick = film;
  const wait = setInterval(() => { if (typeof L !== "undefined" && L.shots && L.shots.length) { clearInterval(wait); document.getElementById("fm-n").textContent = L.shots.length.toLocaleString() + " shots ready"; } }, 300);
})();
