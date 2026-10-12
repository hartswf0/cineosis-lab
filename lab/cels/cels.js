/* THE CEL LAYER, shared by the lab's pages: the WYGWYL film redrawn as cartoon cels (cels/build_cels.py writes cels/cels.json).
   CELS.ready      a promise; resolves once cels.json is in (or failed: the pages carry on without the layer)
   CELS.of(id)     an archive clip's cel, by corpus id: {patch, cel, poster, poem, window} or null
   CELS.able(id)   could this clip become a cel: {score 0–100, why[]} or null (every watched clip)
   CELS.patch(id)  a film patch by its id (P01-002 …)
   CELS.at(t)      the film's patch on screen at suite time t
   CELS.chip(id)   a small badge: "cel" (drawn) or the clip's cel-ability, for any tool's panel                        */
(function () {
  'use strict';
  const base = (document.currentScript && document.currentScript.src) ? new URL('.', document.currentScript.src).href : 'cels/';
  const C = { data: null, base };
  C.ready = fetch(base + 'cels.json').then(r => r.ok ? r.json() : null).then(d => { C.data = d; return d; }).catch(() => null);
  const url = p => p ? new URL(p.replace(/^cels\//, ''), base).href : null;
  C.of = id => { const c = C.data && C.data.clips[id]; return c ? { ...c, cel: url(c.cel), poster: url(c.poster) } : null; };
  C.able = id => (C.data && C.data.celability[id]) || null;
  C.patch = id => { const p = C.data && C.data.patches.find(x => x.id === id); return p ? { ...p, cel: url(p.cel), poster: url(p.poster) } : null; };
  C.at = t => { if (!C.data) return null; const P = C.data.patches; let lo = 0, hi = P.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (P[m].t0 <= t) lo = m; else hi = m - 1; } return P[lo] && P[lo].t0 <= t && t < P[lo].t1 ? C.patch(P[lo].id) : null; };
  C.chip = id => {
    const c = C.of(id), a = C.able(id);
    if (c) return `<span class="cel-chip on" title="redrawn as a cel in the WYGWYL film (${c.patch})">cel · ${c.patch}</span>`;
    if (a) return `<span class="cel-chip" title="could it become a cel? ${a.why.join(', ')}">cel-able ${a.score}</span>`;
    return '';
  };
  const st = document.createElement('style');
  st.textContent = '.cel-chip{display:inline-block;font:500 10.5px ui-monospace,Menlo,monospace;padding:2px 6px;border-radius:999px;border:1px solid rgba(255,255,255,.25);color:#cfd5e6;margin-left:4px}.cel-chip.on{background:#f2a541;color:#111;border-color:#f2a541}';
  document.head.appendChild(st);
  window.CELS = C;
})();
