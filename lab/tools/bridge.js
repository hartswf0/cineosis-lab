/* cineosis bridge — connects an editor (CUT or the WAG Cutting Room) to the Cineosis Lab corpus.
 *
 * lab → editor: a "bin" {id, title, layout, items:[{shot, title, year, n, symbol, note, a, b, media}]}
 *   arrives on BroadcastChannel('cineosis') (editor already open) or in localStorage 'cineosis.bin' (editor opening).
 *   Each item's media URL must be same-origin (the lab sends /media/<id>.mp4 from server.py, or clips/<id>.mp4 on Pages),
 *   so the editor can read it as a File and record its canvas without taint.
 * items may carry place {t,x,y,w,h} (CUT) to reopen a saved montage exactly; in the Cutting Room place.t sets when the
 *   clip lands (x/y are left to the room's cells). Items may also carry beat (a WYGWYL beat id) and role ('A'|'B').
 * bins may carry span (seconds): the Cutting Room deepens to the smallest depth that holds it.
 * take() returns a promise; bins are imported one after another, never interleaved.
 * layouts (CUT): sequence · grid (peaks of the present: several presents at once) · cascade (sheets of the past:
 *   each layer starts before the last ends) · split (two paths side by side, forking paths / binomial).
 *   The Cutting Room takes sequences; its own grid/pack/bend verbs do the rest by hand.
 * editor → lab: "↩ lab" saves the montage as data (which shots, which signs, in/out, when, where) via POST /api/edits,
 *   or to localStorage + a downloaded JSON when there is no server.
 */
(function () {
  'use strict';
  const CH = 'BroadcastChannel' in window ? new BroadcastChannel('cineosis') : null;
  const DONE = 'cineosis.bin.done', PENDING = 'cineosis.bin', TAGS = 'cineosis.tags';
  const ls = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } },
               set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } } };
  const tool = () => window.ButterCut ? 'cutting-room' : window.CUT ? 'cut' : null;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const tags = ls.get(TAGS, {});                       // source file name → corpus item, so clips stay traceable

  /* ---- a small status chip, and the way back ---- */
  const chip = document.createElement('div');
  chip.id = 'cxChip';
  chip.style.cssText = 'position:fixed;left:10px;bottom:52px;z-index:99;display:flex;gap:6px;align-items:center;font:12px ui-monospace,Menlo,monospace;color:#e8eeeb;pointer-events:auto';
  chip.innerHTML = '<span id="cxMsg" style="background:#0b0f11d9;border:1px solid #243033;padding:6px 9px;max-width:52vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">cineosis · waiting for shots from the lab</span>' +
    '<button id="cxBack" title="Save this montage back to the Cineosis Lab as data" style="min-height:32px;padding:0 10px;border:1px solid #c4f46a;background:#141b1e;color:#c4f46a;font:inherit;cursor:pointer">↩ lab</button>';
  const say = t => { const m = chip.querySelector('#cxMsg'); if (m) m.textContent = 'cineosis · ' + t; };
  addEventListener('DOMContentLoaded', () => document.body.appendChild(chip));
  if (document.body) document.body.appendChild(chip);

  const files = new Map();                             // media URL → blob, so a shot repeated across a cut is fetched once
  async function fileFor(it) {
    const name = `${it.symbol ? it.symbol + ' · ' : ''}${(it.title || 'shot').replace(/[\\/:*?"<>|]/g, ' ').slice(0, 40)} [${it.shot.slice(0, 8)}].mp4`;
    tags[name] = { shot: it.shot, n: it.n, symbol: it.symbol, note: it.note, title: it.title, year: it.year };
    if (it.beat) Object.assign(tags[name], { beat: it.beat, role: it.role || null });
    ls.set(TAGS, tags);
    if (files.has(it.media)) return new File([files.get(it.media)], name, { type: 'video/mp4' });
    const r = await fetch(it.media);
    if (!r.ok) throw new Error((await r.text().catch(() => '')).slice(0, 80) || 'HTTP ' + r.status);
    const blob = await r.blob();
    files.set(it.media, blob);
    return new File([blob], name, { type: 'video/mp4' });
  }

  /* ---- CUT: the frame, depth as time. Clips carry {x,y,w,h} in the frame and t (start) ---- */
  async function intoCut(bin) {
    const C = window.CUT, items = bin.items;
    let t = bin.layout === 'sequence' ? C.total() : Math.max(C.S.time, 0);
    const placed = items.filter(it => it.place);
    const t0 = placed.length === items.length && items.length ? Math.min(...placed.map(it => +it.place.t || 0)) : t;
    const n = items.length, cols = Math.ceil(Math.sqrt(n));
    for (let i = 0; i < n; i++) {
      const it = items[i];
      say(`fetching ${i + 1}/${n} · ${it.title}`);
      let f; try { f = await fileFor(it); } catch (e) { say(`skipped ${it.title}: ${e.message}`); continue; }
      const before = C.S.clips.length;
      await C.importFile(f);
      if (C.S.clips.length === before) continue;
      const c = C.S.clips[C.S.clips.length - 1], src = C.S.sources.get(c.src), dur = src?.dur || 0;
      c.in = clamp(it.a ?? 0, 0, Math.max(0, dur - .2)); c.out = clamp(it.b ?? dur, c.in + .2, dur);
      const len = c.out - c.in;
      c.cineosis = { shot: it.shot, n: it.n, symbol: it.symbol, note: it.note };
      if (it.beat) Object.assign(c.cineosis, { beat: it.beat, role: it.role || null });
      if (it.place) {                                      // explicit: a saved montage reopened as it was
        Object.assign(c, { t: +it.place.t || 0, x: +it.place.x || 0, y: +it.place.y || 0, w: +it.place.w || 1, h: +it.place.h || 1 });
      } else if (bin.layout === 'grid') {                  // several presents at once
        const s = 1 / cols; c.w = c.h = s; c.x = (i % cols) * s; c.y = Math.floor(i / cols) * s; c.t = t;
      } else if (bin.layout === 'cascade') {               // each layer starts before the last ends
        c.w = c.h = .62; c.x = c.y = Math.min(.38, i * .38 / Math.max(1, n - 1)); c.t = t + i * Math.min(1.5, len * .5);
      } else if (bin.layout === 'split') {                 // two lines side by side
        c.w = c.h = .5; c.x = (i % 2) * .5; c.y = .25; c.t = t + Math.floor(i / 2) * len;
      } else {                                             // sequence
        c.x = c.y = 0; c.w = c.h = 1; c.t = t; t += len;
      }
      C.thumb?.(c);
    }
    C.save?.(); C.seek(t0);                              // the playhead waits where the new material begins
    say(`${n} shot${n > 1 ? 's' : ''} in · ${bin.title || bin.layout}`);
  }

  /* ---- the WAG Cutting Room: clips are worldtubes in the plate volume; they arrive as a sequence, or at place.t ---- */
  const SPANS = [20, 30, 60, 120, 300, 600, 1200, 1800, 3600];
  async function intoRoom(bin) {
    const B = window.ButterCut, items = bin.items;
    if (B.state().booted === false) say('the room is starting up · your shots follow in a few seconds');
    for (let k = 0; k < 600 && B.state().booted === false; k++) await sleep(100);   // the room boots on its first frame
    if (bin.span) { const sp = SPANS.find(s => s >= bin.span) || SPANS[SPANS.length - 1]; if (B.state().span < sp) B.setSpan(sp); }
    let t0 = null, n = 0;
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      say(`fetching ${i + 1}/${items.length} · ${it.title}`);
      let f; try { f = await fileFor(it); } catch (e) { say(`skipped ${it.title}: ${e.message}`); continue; }
      const st0 = B.state(), seqEnd = Math.max(0, ...st0.clips.map(c => c.end));
      const at = it.place ? Math.max(0, +it.place.t || 0) : seqEnd;
      t0 = t0 === null ? at : Math.min(t0, at);
      if (B.addRange) {                                   // import without placing, then place exactly the range at its time
        const src = await B.importFile(f, false);
        if (!src) continue;
        const a = clamp(it.a ?? 0, 0, Math.max(0, src.dur - .2)), b = clamp(it.b ?? src.dur, a + .2, src.dur);
        if (B.addRange(src.id, a, b, at)) n++;
        continue;
      }
      const before = new Set(st0.clips.map(c => c.id));
      const a0 = Math.max(0, it.a ?? 0);
      B.seek(Math.max(0, at - a0));                     // the room places an imported clip at the playhead; start it early
                                                        // by its in-point so that, once the head is trimmed, it lands at `at`
      const src = B.importFile ? await B.importFile(f) : (await B.importFiles([f]), null);
      await sleep(60);
      let c = B.state().clips.find(q => !before.has(q.id));
      if (!c && src) { B.add(src.id); await sleep(60); c = B.state().clips.find(q => !before.has(q.id)); }  // a known source: place a fresh clip of it
      if (!c) continue;
      // trims are playhead verbs here: put the head at the cut, then trim that side; pack closes the gap it leaves
      const dur = c.end - c.start, a = clamp(it.a ?? 0, 0, dur - .2), b = clamp(it.b ?? dur, a + .2, dur);
      if (b < dur - .05) { B.seek(c.start + b); B.trimTo('out'); await sleep(30); }
      if (a > .05) { B.seek(c.start + a); B.trimTo('in'); await sleep(30); }
      n++;
    }
    if (t0 !== null) B.seek(t0);
    say(`${n} shot${n === 1 ? '' : 's'} in · ${bin.title || 'sequence'} · arrange them with grid / pack / bend`);
  }

  let queue = Promise.resolve(), pending = 0;
  function take(bin) { pending++; return (queue = queue.then(() => takeNow(bin)).catch(() => {}).finally(() => pending--)); }
  async function takeNow(bin) {
    if (!bin || !bin.id || !Array.isArray(bin.items)) return;
    const done = ls.get(DONE, []);
    if (done.includes(bin.id)) return;
    ls.set(DONE, done.concat(bin.id).slice(-200));
    for (let k = 0; k < 100 && !tool(); k++) await sleep(100);   // the Cutting Room builds itself after load
    const t = tool();
    if (!t) return say('no editor API found on this page');
    CH?.postMessage({ type: 'ack', id: bin.id, tool: t });
    try { await (t === 'cut' ? intoCut(bin) : intoRoom(bin)); }
    catch (e) { say('import failed: ' + e.message); }
  }

  /* ---- the way back: the montage as data ---- */
  function montage() {
    const t = tool();
    if (t === 'cut') {
      const C = window.CUT;
      return C.S.clips.map(c => {
        const name = C.S.sources.get(c.src)?.name || '', tag = c.cineosis || tags[name] || {};
        return { shot: tag.shot || null, n: tag.n || null, symbol: tag.symbol || null, note: tag.note || null, source: name,
                 in: +c.in.toFixed(3), out: +c.out.toFixed(3), t: +c.t.toFixed(3), x: +c.x.toFixed(4), y: +c.y.toFixed(4), w: +c.w.toFixed(4), h: +c.h.toFixed(4) };
      }).sort((a, b) => a.t - b.t);
    }
    if (t === 'cutting-room') {
      return window.ButterCut.state().clips.map(c => {
        const tag = tags[c.source] || {};
        return { shot: tag.shot || null, n: tag.n || null, symbol: tag.symbol || null, note: tag.note || null, source: c.source,
                 in: c.in, out: c.out, t: c.start, end: c.end, rate: c.rate, x: c.x, y: c.y };
      }).sort((a, b) => a.t - b.t);
    }
    return [];
  }
  async function back() {
    const clips = montage();
    if (!clips.length) return say('nothing to save yet');
    const title = prompt('Name this montage (e.g. "mark → demark, crop-duster")', '') ?? '';
    const body = { tool: tool(), title, clips, signs: [...new Set(clips.map(c => c.n).filter(Boolean))] };
    try {
      const r = await fetch('/api/edits', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json();
      say(`saved to the lab · ${j.saved}`);
      CH?.postMessage({ type: 'edit', ...body });
    } catch (e) {                                           // static site: keep it in the browser and hand over a file
      const kept = ls.get('cineosis.edits', []); kept.push({ ...body, ts: new Date().toISOString() }); ls.set('cineosis.edits', kept);
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(body, null, 1)], { type: 'application/json' }));
      a.download = 'cineosis-montage-' + Date.now() + '.json'; a.click();
      say('no lab server · kept in this browser and downloaded as JSON');
    }
  }
  chip.querySelector('#cxBack').onclick = back;

  CH && (CH.onmessage = e => { if (e.data?.type === 'bin') take(e.data.bin); if (e.data?.type === 'ping') CH.postMessage({ type: 'pong', tool: tool() }); });
  addEventListener('load', () => take(ls.get(PENDING, null)));
  addEventListener('storage', e => { if (e.key === PENDING) take(ls.get(PENDING, null)); });
  const tagOf = name => (name && tags[name]) || null;
  window.CineosisBridge = { take, montage, back, tagOf, say, busy: () => pending > 0 };
})();
