/* THE ARCHIVE IN MOTION. Open the explorer with ?film and it shows you how it works, one shot at a time, by using itself:
     FIND      a cursor types into the search; the wall narrows to what it typed
     OPEN      it clicks the shot; the shot plays in the inspector, and each panel lights in turn: what the image model sees,
               the editor's reading, the search that found it, the subjects, the sound, the sign on the table, SAM's segments
     LOOKS     the map flies to the shot, lines run to its nearest shots by picture (CLIP), and they play side by side,
               with what they have in common, in the machine's own words
     SOUNDS    its nearest shots by sound (CLAP), each heard in turn
     SIGN      the ring turns to the shot's sign, stops, and the cursor opens another shot of it
   The shots and their neighbours come from film-seeds.json (film-seeds.py). Uses app.js's own Shell, F, SORT, refresh, parseQuery,
   Inspector, MapMode, Ring. A D-A-E score under it, ducked when a shot speaks. Esc or × hands the explorer back. */
(function () {
  if (!/[?&]film\b/.test(location.search)) return;
  const CUE = "score/cues/dae-paddle-meets-current.m4a";
  const css = document.createElement("style");
  css.textContent = `
    body.filming #facets,body.filming #status,body.filming #livebar,body.filming #guide,body.filming #tip{opacity:0!important;pointer-events:none!important}
    #fm-cur{position:fixed;left:0;top:0;z-index:120;width:26px;height:26px;pointer-events:none;transition:transform .9s cubic-bezier(.5,0,.2,1);transform:translate(50vw,50vh)}
    #fm-cur svg{width:26px;height:26px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.8))}
    #fm-cur.click::after{content:"";position:absolute;left:-14px;top:-14px;width:40px;height:40px;border-radius:50%;border:2px solid #f2c14e;animation:fmr .6s ease-out forwards}
    @keyframes fmr{from{transform:scale(.3);opacity:1}to{transform:scale(1.6);opacity:0}}
    .fm-hl{outline:3px solid #f2c14e!important;outline-offset:-3px;box-shadow:0 0 0 9999px rgba(0,0,0,.45)!important;position:relative;z-index:5;transition:outline .3s}
    #fm-tag{position:fixed;z-index:121;font:700 11px/1 "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.16em;color:#0b0a09;background:#f2c14e;padding:6px 10px;border-radius:3px;opacity:0;transition:opacity .4s;pointer-events:none;white-space:nowrap}
    #fm-tag.on{opacity:1}
    #fm-cap{position:fixed;left:50%;top:56px;transform:translateX(-50%);z-index:119;font:600 12px/1 "IBM Plex Mono",ui-monospace,monospace;letter-spacing:.2em;color:#fff;background:rgba(0,0,0,.7);padding:9px 16px;border-radius:18px;opacity:0;transition:opacity .6s;pointer-events:none;white-space:nowrap}
    #fm-cap.on{opacity:1}
    #fm-svg{position:fixed;inset:0;z-index:110;pointer-events:none}
    #fm-strip{position:fixed;left:2vw;right:2vw;bottom:3vh;z-index:115;display:flex;flex-direction:column;gap:8px;background:rgba(8,7,6,.94);border:1px solid #3a352e;border-radius:10px;padding:12px;opacity:0;transform:translateY(20px);transition:opacity .6s,transform .6s}
    #fm-strip.on{opacity:1;transform:none}
    #fm-strip .hd{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;font:700 12px "IBM Plex Mono",monospace;letter-spacing:.16em;color:#f2c14e}
    #fm-strip .hd small{font-weight:400;color:#ece6da;letter-spacing:.08em}
    #fm-strip .hd em{font-style:normal;color:#0b0a09;background:#ece6da;padding:3px 8px;border-radius:12px;font-size:11px;letter-spacing:.06em}
    #fm-strip .row{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px}
    #fm-strip .c{display:flex;flex-direction:column;gap:4px;min-width:0}
    #fm-strip .c video{width:100%;aspect-ratio:4/3;object-fit:cover;background:#000;border-radius:4px;border:2px solid transparent}
    #fm-strip .c.seed video{border-color:#f2c14e}#fm-strip .c.loud video{border-color:#ff7a45}
    #fm-strip .c b{font:italic 12px/1.25 Georgia,serif;color:#fff;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    #fm-strip .c span{font:10px "IBM Plex Mono",monospace;color:#9a9285;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    #fm-start{position:fixed;inset:0;z-index:130;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;text-align:center;padding:24px;background:rgba(8,7,6,.92);color:#ece6da}
    #fm-start h1{font:900 clamp(38px,8vw,96px)/.9 "Arial Black",Impact,sans-serif}
    #fm-start p{font:12px "IBM Plex Mono",monospace;letter-spacing:.12em;color:#9a9285;max-width:60ch}
    #fm-start button{font:700 13px "IBM Plex Mono",monospace;letter-spacing:.16em;padding:13px 28px;border-radius:26px;background:#ece6da;color:#0b0a09;border:0;cursor:pointer}
    #fm-x{position:fixed;right:14px;bottom:14px;z-index:131;width:36px;height:36px;border-radius:50%;border:1px solid rgba(255,255,255,.3);background:rgba(0,0,0,.6);color:#fff;font:16px sans-serif;cursor:pointer;opacity:.5}`;
  document.head.appendChild(css);
  const mk = (id, tag = "div") => { const e = document.createElement(tag); e.id = id; document.body.appendChild(e); return e; };
  const cur = mk("fm-cur"); cur.innerHTML = `<svg viewBox="0 0 24 24"><path d="M4 2l15 10-6.5 1.5L16 21l-3 1.2-3.4-7.4L4 19z" fill="#fff" stroke="#000" stroke-width="1.2"/></svg>`;
  const tag = mk("fm-tag"), cap = mk("fm-cap"), strip = mk("fm-strip");
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.id = "fm-svg"; document.body.appendChild(svg);
  const start = mk("fm-start"); start.innerHTML = `<h1>THE ARCHIVE<br>IN MOTION</h1><p>HOW THE EXPLORER READS A SHOT: FIND IT, OPEN IT, SEE WHAT THE MACHINES SAY ABOUT IT, THEN WHAT LOOKS LIKE IT, WHAT SOUNDS LIKE IT, AND WHAT SHARES ITS SIGN.</p><button id="fm-go">▶ PLAY</button><p id="fm-n">loading…</p>`;
  const x = mk("fm-x", "button"); x.textContent = "×"; x.title = "Stop and use the explorer yourself";
  let RUN = 0, AC = null, G = null, el = null, SEEDS = null;
  const sleep = (ms, run) => new Promise(r => setTimeout(() => r(run === RUN), ms));
  const say = (t, ms = 3600) => { cap.textContent = t; cap.classList.add("on"); clearTimeout(say.h); say.h = setTimeout(() => cap.classList.remove("on"), ms); };
  /* ---------- the hand ---------- */
  let cx = innerWidth / 2, cy = innerHeight / 2;
  async function moveTo(target, run, ms = 900) {
    let r = target && target.getBoundingClientRect ? target.getBoundingClientRect() : null;
    const tx = r ? r.left + Math.min(r.width * .35, 60) : target.x, ty = r ? r.top + Math.min(r.height * .5, 40) : target.y;
    cur.style.transitionDuration = ms + "ms"; cur.style.transform = `translate(${tx}px,${ty}px)`; cx = tx; cy = ty; return sleep(ms + 80, run);
  }
  async function click(run) { cur.classList.remove("click"); void cur.offsetWidth; cur.classList.add("click"); return sleep(350, run); }
  function light(elm, label) {
    document.querySelectorAll(".fm-hl").forEach(e => e.classList.remove("fm-hl"));
    if (!elm) { tag.classList.remove("on"); return; }
    elm.classList.add("fm-hl"); const r = elm.getBoundingClientRect();
    tag.textContent = label; tag.style.left = Math.max(8, Math.min(innerWidth - 320, r.left + 8)) + "px"; tag.style.top = Math.max(8, r.top - 30) + "px"; tag.classList.add("on");
  }
  /* ---------- the score ---------- */
  function score() {
    if (!AC) { AC = new (window.AudioContext || window.webkitAudioContext)(); el = new Audio(CUE); el.loop = true; G = AC.createGain(); G.gain.value = 0; AC.createMediaElementSource(el).connect(G).connect(AC.destination); }
    if (AC.state === "suspended") AC.resume(); el.currentTime = 0; el.play().catch(() => { }); level(.45);
  }
  const level = (v, s = .8) => G && G.gain.setTargetAtTime(v, AC.currentTime, s / 3);
  const reset = () => { F.signs = new Set(); F.dec = new Set(); F.hue = null; F.color = "all"; F.subj = new Set(); GROUP = "none"; SORT.key = "sign"; SORT.dir = 1; const q = document.getElementById("q"); if (q) q.value = ""; parseQuery(""); };
  const mode = m => { if (Shell.mode !== m) Shell.setMode(m); };
  const shotOf = id => L.shots.find(s => s.id === id);
  /* ---------- 1. FIND: type into the search, and the wall narrows ---------- */
  async function find(seed, run) {
    reset(); refresh(); mode("wall"); say("FIND IT");
    const q = document.getElementById("q"); await moveTo(q, run); await click(run);
    const words = (seed.caption || seed.title).split(/\s+/).filter(w => w.length > 3).slice(0, 3).join(" ") || seed.title;
    const text = seed.title.toLowerCase().split(/[\s:,(]+/).filter(w => w.length > 3).slice(0, 2).join(" ");
    q.value = "";
    for (const ch of text) { if (run !== RUN) return; q.value += ch; parseQuery(q.value); refresh(); await sleep(110, run); }
    say(`${VIEW.length} SHOTS MATCH “${text.toUpperCase()}”`); await sleep(1400, run);
    const s = shotOf(seed.id); if (!s) return;
    let img = null;
    for (let k = 0; k < 20 && !img; k++) { img = [...document.querySelectorAll("#m-wall img")].find(i => i.src && s.thumb && i.src.endsWith(s.thumb.split("/").pop())); if (!img) await sleep(150, run); }
    if (img) { await moveTo(img, run); light(img.parentElement, "THIS ONE"); await sleep(900, run); await click(run); light(null); }
    return words;
  }
  /* ---------- 2. OPEN: the inspector, panel by panel ---------- */
  async function open(seed, run) {
    const s = shotOf(seed.id); if (!s) return;
    Inspector.open(s, VIEW.length ? VIEW : [s]); say("OPEN IT"); await sleep(1800, run);
    const v = document.getElementById("insVid"); if (v) { v.muted = false; v.volume = .9; v.play().catch(() => { v.muted = true; v.play(); }); }
    const NAMES = { s1: "1 · SEARCHED · THE WORDS THAT FOUND IT", s2: "2 · SEEN · WHAT THE IMAGE MODELS SEE", s3: "3 · HEARD · WHAT THE SOUND MODEL HEARS", s4: "4 · SAID · WHAT ITS PEOPLE SAY",
      s5: "5 · READ · WHAT AN EDITOR SAW IN IT", s6: "6 · SUGGESTED · WHAT CLIP WOULD CALL IT", s7: "7 · CUT OUT · WHAT SAM LIFTED, FRAME BY FRAME" };
    level(.18);
    for (const k of ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]) {
      if (run !== RUN) return; let b = document.querySelector("#inspector .step." + k); if (!b) continue;
      if (k === "s6") b = b.nextElementSibling || b;   // the table of signs itself
      await moveTo(b, run, 650); light(b, NAMES[k]);
      if (k === "s7") { try { if (!Inspector.showSegs) Inspector.toggleSegs(); } catch (e) { } }
      await sleep(k === "s4" || k === "s5" || k === "s7" ? 3600 : 2700, run);
    }
    light(null); level(.45); await sleep(600, run);
    try { Inspector.close(); } catch (e) { }
  }
  /* ---------- strips: shots side by side, playing ---------- */
  function vid(c, sound) { const v = document.createElement("video"); v.src = c.video; v.muted = !sound; v.playsInline = true; v.loop = true; v.preload = "auto"; v.addEventListener("loadedmetadata", () => { try { v.currentTime = c.t || 0; } catch (e) { } v.play().catch(() => { v.muted = true; v.play().catch(() => { }); }); }, { once: true }); return v; }
  function showStrip(title, sub, shared, cards) {
    strip.innerHTML = `<div class="hd">${title}<small>${sub}</small>${shared.words && shared.words.length ? `<em>IN COMMON: ${shared.words.join(" · ")}${shared.decades ? " · " + shared.decades : ""}</em>` : (shared.decades ? `<em>${shared.decades}</em>` : "")}</div><div class="row"></div>`;
    const row = strip.querySelector(".row");
    cards.forEach((c, i) => { const d = document.createElement("div"); d.className = "c" + (i === 0 ? " seed" : ""); d.appendChild(vid(c, false));
      d.insertAdjacentHTML("beforeend", `<b>${(c.caption || (c.subjects || []).join(", ") || "").replace(/</g, "&lt;")}</b><span>${(c.title || "").replace(/</g, "&lt;")}${c.year ? " · " + c.year : ""}</span>`); row.appendChild(d); });
    strip.classList.add("on"); return [...row.children];
  }
  const hideStrip = () => { strip.classList.remove("on"); setTimeout(() => { strip.querySelectorAll("video").forEach(v => v.pause()); }, 700); };
  /* ---------- 3. LOOKS LIKE IT: the map, with lines to the nearest pictures ---------- */
  function lines(seed) {
    svg.innerHTML = ""; const c = MapMode.cam, cv = MapMode.cv; if (!cv) return; const R = cv.getBoundingClientRect();
    const pos = id => { const p = MapMode.P.find(q => q.s.id === id); return p ? { x: R.left + (p.x - c.x) * c.z + R.width / 2, y: R.top + (p.y - c.y) * c.z + R.height / 2 } : null; };
    const a = pos(seed.id); if (!a) return;
    let h = "";
    seed.looks.forEach(n => { const b = pos(n.id); if (b) h += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="#f2c14e" stroke-width="2" stroke-dasharray="6 5" opacity=".9"/><circle cx="${b.x}" cy="${b.y}" r="16" fill="none" stroke="#f2c14e" stroke-width="2"/>`; });
    h += `<circle cx="${a.x}" cy="${a.y}" r="22" fill="none" stroke="#fff" stroke-width="3"/>`; svg.innerHTML = h;
  }
  function frame(ids, run) {   // the camera frames the shot and its neighbours, so all of them can be seen playing
    const ps = ids.map(id => MapMode.P.find(q => q.s.id === id)).filter(Boolean); if (!ps.length) return Promise.resolve(true);
    const xs = ps.map(p => p.x), ys = ps.map(p => p.y), x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const c = MapMode.cam, from = { ...c }, W = MapMode.W, H = MapMode.H;
    const z = Math.min((W - 360) / Math.max(.004, x1 - x0), (H - 300) / Math.max(.004, y1 - y0), 60000), to = { x: (x0 + x1) / 2, y: (y0 + y1) / 2 + 20 / z, z };
    const t0 = performance.now();
    return new Promise(r => { const st = () => { if (run !== RUN) return r(false); const k = Math.min(1, (performance.now() - t0) / 2800), e = k * k * (3 - 2 * k);
      c.x = from.x + (to.x - from.x) * e; c.y = from.y + (to.y - from.y) * e; c.z = from.z * Math.pow(to.z / from.z, e); MapMode.draw(); if (k < 1) requestAnimationFrame(st); else r(true); }; st(); });
  }
  function lines(seed, list) {
    svg.innerHTML = ""; const c = MapMode.cam, cv = MapMode.cv; if (!cv) return; const R = cv.getBoundingClientRect();
    const pos = id => { const p = MapMode.P.find(q => q.s.id === id); return p ? { x: R.left + (p.x - c.x) * c.z + R.width / 2, y: R.top + (p.y - c.y) * c.z + R.height / 2 } : null; };
    const a = pos(seed.id); if (!a) return; let h = "";
    list.forEach(n => { const b = pos(n.id); if (b) h += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="#f2c14e" stroke-width="2.5" stroke-dasharray="7 6" opacity=".95"/>`; });
    svg.innerHTML = h;
  }
  const lab = c => (c.caption || (c.subjects || []).join(", ") || c.title || "").replace(/</g, "&lt;");
  async function looks(seed, run) {
    reset(); refresh(); mode("map"); [seed, ...seed.looks].forEach(c => { const i = new Image(); i.src = c.thumb; });
    await MapMode.morph("xy", 900); say("SEEN · WHAT LOOKS LIKE IT · CLIP PLACES SHOTS BY PICTURE", 5000);
    if (!await frame([seed.id, ...seed.looks.map(c => c.id)], run)) return;
    lines(seed, seed.looks);
    MapMode.playIn([{ ...seed, cls: "seed", px: 200, label: "THIS · " + lab(seed) }, ...seed.looks.map(c => ({ ...c, px: 170, label: lab(c) }))]);
    const sh = seed.looks_shared || {}; await sleep(1500, run);
    if (sh.words && sh.words.length) say(`IN COMMON · ${sh.words.join(" · ").toUpperCase()}${sh.decades ? " · " + sh.decades : ""}`, 6000);
    await sleep(7500, run); svg.innerHTML = "";
  }
  async function sounds(seed, run) {
    MapMode.stopIn(); say("HEARD · THE MAP REARRANGES ITSELF BY SOUND", 4000);
    await MapMode.morph("sound", 2600); if (run !== RUN) return;
    const H = (SND.d && SND.d.heard) || {}, tagOf = c => (H[c.id] || []).map(x => x[0]).join(" · ") || c.sound || "";
    if (!await frame([seed.id, ...seed.sounds.map(c => c.id)], run)) return;
    lines(seed, seed.sounds);
    const live = MapMode.playIn([{ ...seed, cls: "seed", px: 200, label: "THIS · " + tagOf(seed) }, ...seed.sounds.map(c => ({ ...c, px: 170, label: tagOf(c) }))]);
    say("NEAREST BY SOUND · EACH HEARD IN TURN", 4000); level(.1);
    for (const L1 of live) { if (run !== RUN) break; live.forEach(o => { o.box.classList.remove("loud"); o.v.muted = true; });
      L1.box.classList.add("loud"); L1.v.muted = false; L1.v.volume = 1; try { L1.v.currentTime = L1.o.t || 0; } catch (e) { } L1.v.play().catch(() => { }); await sleep(2800, run); }
    live.forEach(o => { o.v.muted = true; }); level(.45); svg.innerHTML = ""; MapMode.stopIn();
    say("COLOUR × DECADE · THE SAME SHOTS, ANOTHER ORDER", 3500); await MapMode.morph("hue", 2200); await sleep(1800, run);
  }
  /* ---------- 5. SAME SIGN: the ring turns to it, stops, and opens another ---------- */
  async function sign(seed, run) {
    if (!seed.sign || !L.S[seed.sign]) return;
    reset(); F.signs = new Set([String(seed.sign)]); refresh(); mode("ring"); Ring.auto = false; Ring.vel = 3.2;
    say(`THE SAME SIGN · ${L.S[seed.sign].symbol} · ${L.S[seed.sign].name.toUpperCase()}`); await sleep(4200, run); Ring.vel = 0;
    const cards = [...document.querySelectorAll("#m-ring .ring-rot > *")].filter(c => { const r = c.getBoundingClientRect(); return r.width > 60 && r.left > innerWidth * .3 && r.right < innerWidth * .7; });
    const card = cards.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    const other = VIEW.find(q => q.id !== seed.id && q.video);
    if (card && other) { await moveTo(card, run); await click(run); Inspector.open(other, VIEW); await sleep(1500, run);
      const v = document.getElementById("insVid"); if (v && !document.getElementById("inspector").hidden) { v.muted = false; v.play().catch(() => { }); await sleep(5500, run); try { Inspector.close(); } catch (e) { } } }
    Ring.auto = true;
  }
  async function film() {
    const run = ++RUN; document.body.classList.add("filming"); start.hidden = true; score(); try { CAPS.load(); SND.load(); } catch (e) { }
    reset(); refresh(); mode("wall"); say(`${L.shots.length.toLocaleString()} SHOTS · ONE AT A TIME`, 3000); await sleep(3200, run);
    for (const seed of SEEDS) {
      if (run !== RUN) return;
      await find(seed, run); if (run !== RUN) return;
      await open(seed, run); if (run !== RUN) return;
      await looks(seed, run); if (run !== RUN) return;
      await sounds(seed, run); if (run !== RUN) return;
      await sign(seed, run);
    }
    if (run === RUN) { reset(); refresh(); mode("map"); MapMode.kind = "xy"; MapMode.build(); MapMode.fit(); say("NOW YOU · CLICK ANY SHOT", 6000); level(0, 4); setTimeout(stop, 6500); }
  }
  function stop() { RUN++; document.body.classList.remove("filming"); light(null); hideStrip(); svg.innerHTML = ""; cur.style.display = "none"; start.hidden = true; x.hidden = true; if (G) level(0, .6); setTimeout(() => el && el.pause(), 900); }
  x.onclick = stop; addEventListener("keydown", e => { if (e.key === "Escape" && document.body.classList.contains("filming")) { e.stopPropagation(); stop(); } }, true);
  document.getElementById("fm-go").onclick = film;
  fetch("film-seeds.json").then(r => r.json()).then(d => { SEEDS = d.seeds; }).catch(() => { SEEDS = []; });
  const wait = setInterval(() => { if (typeof L !== "undefined" && L.shots && L.shots.length && SEEDS) { clearInterval(wait); document.getElementById("fm-n").textContent = `${SEEDS.length} shots, read five ways each`; } }, 300);
})();
