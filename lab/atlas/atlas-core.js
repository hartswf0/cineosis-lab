/* ATLAS CORE · shared by every finder in lab/atlas/. Loads the excavation (../atlas.json), the frames each page was filmed into
   (frames.json, frames/*.jpg) and what each page looks like to CLIP (look.json); then
     ATLAS.search(q)      ranked pages with a snippet of where the words were found; ranks title > work, type, look words > description > visible text
     ATLAS.frames(p)      the page's frames, in order (a page is a short film)
     ATLAS.flip(root)     every <img data-flip="a|b|c"> under root steps through its frames on one shared clock: the thumbnails move
     ATLAS.open(p)        the page's own address
   ATLAS.load(base, dir): base is where atlas.json lives relative to the page ('..' from lab/atlas/, '.' from lab/), dir where frames live ('' or 'atlas/').
   Every finder is a bet on a different Bolas set; this file is the part they share. */
(function () {
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  const KIND = { explainer: 'explainer film', film: 'film or player', series: 'series episode', browser: 'archive browser', machine: 'machine view', bench: 'bench or tool',
    reading: 'reading or paper', game: 'game', index: 'front door', mark: 'mark and identity', template: 'template', pointer: 'pointer' };
  const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const A = { ready: null, pages: [], by: {}, esc, KIND };
  A.load = (base = '..', dir = '') => A.ready || (A.root = base === '..' ? '../../' : '../', A.ready = Promise.all([fetch(base + '/atlas.json?v=' + Date.now()).then(r => r.json()), fetch(dir + 'frames.json?v=' + Date.now()).then(r => r.json()).catch(() => ({})), fetch(dir + 'look.json?v=' + Date.now()).then(r => r.json()).catch(() => ({}))])
    .then(([d, fr, lk]) => { A.data = d; A.subjects = Object.fromEntries(d.subjects.map(s => [s.id, s])); A.families = Object.fromEntries(d.families.map(f => [f.id, f]));
      d.pages.forEach(p => { const f = fr[p.path] || {}, l = lk[p.path] || {}; p.frameFiles = (f.frames || []).map(x => dir + 'frames/' + x); p.text = f.text || ''; p.tags = l.tags || []; p.looks = l.looks || []; p.xy = l.xy || null;
        p.clean = p.title.replace(/ · (lab\/)?[\w/.-]+\.html$/, '');
        p._f = { title: norm(p.clean + ' ' + p.path.split('/').pop().replace('.html', '').replace(/-/g, ' ')), cat: norm((A.subjects[p.subject]?.name || '') + ' ' + KIND[p.kind] + ' ' + (A.families[p.family]?.name || '')),
          tags: norm(p.tags.join(' ')), desc: norm(p.desc), text: norm(p.text) }; });
      A.pages = d.pages; A.by = Object.fromEntries(d.pages.map(p => [p.path, p])); return A; }));
  A.frames = p => p.frameFiles.length ? p.frameFiles : [];
  A.open = p => (A.root || '../../') + p.path;
  const W = { title: 10, cat: 4, tags: 4, desc: 2.5, text: 1 };
  A.search = (q, pool) => {
    const terms = norm(q).split(/[^a-z0-9]+/).filter(t => t.length > 1 || /\d/.test(t)); pool = pool || A.pages;
    if (!terms.length) return pool.map(p => ({ p, s: 0, snip: '' }));
    const out = [];
    pool.forEach(p => { let s = 0, hitAll = true, where = '';
      terms.forEach(t => { let best = 0; const re = new RegExp('(^|[^a-z0-9])' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
        for (const [k, w] of Object.entries(W)) { const f = p._f[k]; if (!f) continue; if (re.test(f)) { best = Math.max(best, w); if (!where && (k === 'text' || k === 'desc')) where = k; } else if (t.length > 3 && f.includes(t)) best = Math.max(best, w * .4); }
        if (!best) hitAll = false; s += best; });
      if (s > 0) { if (hitAll) s *= 1.6; s += Math.log10(1 + p.importance) * .5; out.push({ p, s, snip: where ? snippet(where === 'text' ? p.text : p.desc, terms) : '' }); } });
    return out.sort((a, b) => b.s - a.s);
  };
  function snippet(txt, terms) { const n = norm(txt); let i = -1; for (const t of terms) { i = n.indexOf(t); if (i >= 0) break; } if (i < 0) return '';
    const a = Math.max(0, i - 50), b = Math.min(txt.length, i + 110); let s = (a ? '…' : '') + txt.slice(a, b) + (b < txt.length ? '…' : '');
    s = esc(s); terms.forEach(t => { s = s.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'), '<mark>$1</mark>'); }); return s; }
  A.mark = (s, q) => { let h = esc(s); norm(q).split(/[^a-z0-9]+/).filter(t => t.length > 1).forEach(t => { h = h.replace(new RegExp('(' + t + ')', 'ig'), '<mark>$1</mark>'); }); return h; };
  /* one clock for every moving thumbnail */
  let tick = 0; setInterval(() => { tick++; document.querySelectorAll('img[data-flip]').forEach(im => { const f = im.dataset.flip.split('|'); if (f.length > 1 && !im.dataset.hold) im.src = f[(tick + (+im.dataset.off || 0)) % f.length]; }); }, 650);
  A.flipAttr = (p, off = 0) => { const f = A.frames(p); return f.length ? `src="${esc(f[Math.min(1, f.length - 1)])}" data-flip="${esc(f.join('|'))}" data-off="${off}"` : 'src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" '; };
  A.color = p => A.subjects[p.subject]?.color || '#888';
  window.ATLAS = A;
})();
