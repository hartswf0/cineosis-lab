/* Where a clip comes from. Attrib.show([{ role, video, at }]) opens a sheet naming each clip's source film: its title and year, the
   Internet Archive item that holds the whole film (attrib/sources.json, found by attrib/resolve.py), its collection, sponsor or maker,
   and licence, with a link to watch the whole film there; when no item was found with confidence, a search for it instead. */
(function (root) {
  const base = (document.currentScript && document.currentScript.src || '').replace(/attrib\.js.*$/, '');
  let S = null, T = null; const load = () => S || (S = Promise.all([fetch(base + 'sources.json').then(r => r.ok ? r.json() : {}).catch(() => ({})), fetch(base + 'titles.json').then(r => r.json()).catch(() => ({}))]).then(([s, t]) => { T = t; return s; }));
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const folder = v => { const m = /sources\/([^/]+)\//.exec(v || ''); return m && m[1]; };
  const lic = u => !u ? '' : /publicdomain\/mark|zero/.test(u) ? 'Public domain' : /licenses\/by-nc-sa/.test(u) ? 'CC BY-NC-SA' : /licenses\/by-nc/.test(u) ? 'CC BY-NC' : /licenses\/by-sa/.test(u) ? 'CC BY-SA' : /licenses\/by/.test(u) ? 'CC BY' : 'Licence';
  const mmss = t => t == null ? '' : `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
  const css = `#attribSheet{ position:fixed; inset:0; z-index:99999; display:grid; place-items:end center; background:#0008; font:13px/1.45 ui-monospace,Menlo,monospace; }
    #attribSheet .box{ width:min(560px,100%); max-height:86dvh; overflow:auto; background:#141210; color:#efe9dd; border-radius:16px 16px 0 0; padding:18px 18px calc(18px + env(safe-area-inset-bottom)); box-shadow:0 -10px 40px #0009; }
    @media (min-width:700px){ #attribSheet{ place-items:center; } #attribSheet .box{ border-radius:16px; } }
    #attribSheet .x{ float:right; background:none; border:0; color:#efe9dd; font-size:24px; line-height:1; cursor:pointer; }
    #attribSheet h4{ margin:0 0 12px; font:500 10px ui-monospace,Menlo,monospace; letter-spacing:.3em; color:#e8c070; }
    #attribSheet .it{ border-top:1px solid #2a2723; padding:12px 0; } #attribSheet .role{ font-size:9.5px; letter-spacing:.22em; color:#8a8378; text-transform:uppercase; }
    #attribSheet .t{ font:300 20px/1.25 Fraunces,Georgia,serif; margin:3px 0 4px; } #attribSheet .m{ color:#a59e93; font-size:11.5px; }
    #attribSheet .bt{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; } #attribSheet a{ text-decoration:none; border:1px solid #5a4e33; color:#e8c070; border-radius:16px; padding:7px 12px; font-size:11px; letter-spacing:.06em; }
    #attribSheet a.q{ border-color:#2a2723; color:#a59e93; } #attribSheet .note{ color:#6b655d; font-size:10.5px; margin-top:10px; }`;
  function sheet(html) { let el = document.getElementById('attribSheet'); if (!el) { const st = document.createElement('style'); st.textContent = css; document.head.append(st); el = document.createElement('div'); el.id = 'attribSheet'; document.body.append(el);
      el.addEventListener('click', e => { if (e.target === el || e.target.closest('.x')) el.remove(); }); addEventListener('keydown', e => { if (e.key === 'Escape') { const s = document.getElementById('attribSheet'); if (s) s.remove(); } }); }
    el.innerHTML = `<div class="box"><button class="x" aria-label="Close">×</button><h4>THE SOURCES</h4>${html}</div>`; return el; }
  async function show(items) { const S_ = await load(); const seen = new Set();
    const rows = items.filter(x => x && x.video).filter(x => { const f = folder(x.video); if (seen.has(f + x.role)) return false; seen.add(f + x.role); return true; }).map(x => {
      const f = folder(x.video), r = S_[f] || (T && T[f]) || {}, title = r.title || x.title || 'Unknown film', yr = r.year || x.year, sure = r.url && r.conf >= .85;   // sure: the title and the year both agree
      const meta = [r.found && (r.found !== title || !sure) ? `catalogued as “${esc(r.found)}”${r.found_year ? ' (' + esc(r.found_year) + ')' : ''}` : '', r.sponsor ? 'sponsor: ' + esc(r.sponsor) : '', r.creator ? 'by ' + esc(r.creator) : '',
        (r.collection || []).filter(c => !/^(stream_only|fav-|moviesandfilms)/.test(c)).slice(0, 2).map(esc).join(', '), lic(r.license)].filter(Boolean).join(' · ');
      const search = r.search || 'https://archive.org/search?query=' + encodeURIComponent('"' + title.replace(/\s*\((part|reel)[^)]*\)/gi, '') + '"');
      return `<div class="it"><div class="role">${esc(x.role || 'the clip')}${x.at != null ? ' · from ' + mmss(x.at) + ' of this clip' : ''}</div><div class="t">${esc(title)}${yr ? ' <span style="color:#8a8378">(' + esc(yr) + ')</span>' : ''}</div>
        ${meta ? `<div class="m">${meta}</div>` : ''}<div class="bt">${sure ? `<a href="${esc(r.url)}" target="_blank" rel="noopener">Watch the whole film ↗</a>` : r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener">Possibly the whole film ↗</a><a href="${esc(search)}" target="_blank" rel="noopener">Search for it ↗</a>` : `<a href="${esc(search)}" target="_blank" rel="noopener">Find the whole film ↗</a>`}
        <a class="q" href="${esc(x.video)}" target="_blank" rel="noopener">This clip ↗</a></div></div>`; });
    sheet((rows.join('') || '<div class="it">No clip on screen yet.</div>') + `<div class="note">Films from the Internet Archive and its collections (Prelinger and others), matched by title and year; a search is offered where no match was certain.</div>`); }
  root.Attrib = { show, load, folder };
})(this);
