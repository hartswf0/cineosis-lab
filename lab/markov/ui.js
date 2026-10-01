/* The Markov Poet's shared interface: the mark, one icon set, and one menu where every feature beyond the essentials lives.
   Rule: a surface shows only what the operator needs now (the words, the picture, play, record, choose, send); everything else
   registers here as a menu item. New features add items; they never add chrome.
   MPUI.mark(size)                         the logo: a Markov chain of two states and a self-loop, the next state taken (gold)
   MPUI.sprite()                           installs the icon symbols (#i-name)
   MPUI.menu(button, groups)               groups: [{title, items:[{icon,label,hint,on,act,hidden}]}]; values may be functions */
(function () {
  const MARK = s => `<svg class="mp-mark" viewBox="0 0 32 32" width="${s}" height="${s}" aria-hidden="true">
    <circle cx="8" cy="18" r="4.6" fill="none" stroke="currentColor" stroke-width="1.8"/>
    <path d="M13.4 18h6" stroke="currentColor" stroke-width="1.8"/><path d="M17.6 15.3l2.9 2.7-2.9 2.7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="25" cy="18" r="4.8" fill="#e8c070"/>
    <path d="M24 11.5C21 6 11 6 9 11.4" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" opacity=".45"/></svg>`;
  const ICONS = {
    play: '<path d="M6 4l10 6-10 6z" fill="currentColor"/>', pause: '<path d="M6 4h3v12H6zM11 4h3v12h-3z" fill="currentColor"/>',
    calm: '<path d="M14.5 13.5A6.5 6.5 0 0 1 7 4a6.5 6.5 0 1 0 7.5 9.5z" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    sound: '<path d="M3 8v4h3l4 3.5v-11L6 8z" fill="currentColor"/><path d="M13 7.5c1 1.4 1 3.6 0 5M15.5 5.5c2 2.5 2 6.5 0 9" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
    mute: '<path d="M3 8v4h3l4 3.5v-11L6 8z" fill="currentColor"/><path d="M13 7.5l4 5M17 7.5l-4 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    voice: '<path d="M3 10h1.5M6 7v6M9 4v12M12 6.5v7M15 8.5v3M17.5 10H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    wall: '<path d="M3 4h6v5H3zM11 4h6v5h-6zM3 11h6v5H3zM11 11h6v5h-6z" fill="none" stroke="currentColor" stroke-width="1.4"/>',
    send: '<path d="M10 13V3M6 7l4-4 4 4M4 12v4h12v-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
    undo: '<path d="M7 5L3 9l4 4M3 9h9a4 4 0 0 1 0 8h-2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    prev: '<path d="M5 4v12M16 4l-8 6 8 6z" stroke="currentColor" stroke-width="1.4" fill="currentColor"/>', next: '<path d="M15 4v12M4 4l8 6-8 6z" stroke="currentColor" stroke-width="1.4" fill="currentColor"/>',
    left: '<path d="M12 4l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>', right: '<path d="M8 4l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    close: '<path d="M5 5l10 10M15 5L5 15" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    mic: '<rect x="7.2" y="2.5" width="5.6" height="10" rx="2.8" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M4.5 9.5a5.5 5.5 0 0 0 11 0M10 15v3" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
    rec: '<circle cx="10" cy="10" r="6" fill="#e0453a"/>', stop: '<rect x="5" y="5" width="10" height="10" rx="1.5" fill="currentColor"/>',
    grid: '<path d="M3 3h8v8H3zM13 3h4v4h-4zM13 9h4v2h-4zM3 13h4v4H3zM9 13h8v4H9z" fill="none" stroke="currentColor" stroke-width="1.4"/>',
    take: '<path d="M3 6h3.5c3 0 4 8 7 8H17M3 14h3.5c1.3 0 2.2-1.6 3-3.4M13.6 6H17M15 4l2 2-2 2M15 12l2 2-2 2" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
    edit: '<path d="M4 16h3l8.5-8.5-3-3L4 13zM11 6l3 3" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/>',
    info: '<circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M10 9v5M10 6.2v.1" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>',
    full: '<path d="M3 8V3h5M12 3h5v5M17 12v5h-5M8 17H3v-5" stroke="currentColor" stroke-width="1.6" fill="none"/>',
    more: '<circle cx="4.5" cy="10" r="1.6" fill="currentColor"/><circle cx="10" cy="10" r="1.6" fill="currentColor"/><circle cx="15.5" cy="10" r="1.6" fill="currentColor"/>',
    open: '<path d="M3 6h5l2 2h7v8H3z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
    down: '<path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>', up: '<path d="M5 12l5-5 5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
    hand: '<path d="M7 10V4.5a1.2 1.2 0 0 1 2.4 0V9m0-5.5a1.2 1.2 0 0 1 2.4 0V9m0-4a1.2 1.2 0 0 1 2.4 0v5m0-3a1.2 1.2 0 0 1 2.4 0v4.5c0 3-2 5.5-5.2 5.5-2.6 0-3.7-1.2-5-3.4L4.2 11a1.2 1.2 0 0 1 2-1.3L7 11" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>',
    home: '<path d="M3 10l7-6 7 6M5 9v8h10V9" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>',
    book: '<path d="M3 4h5a2 2 0 0 1 2 2v10a2 2 0 0 0-2-2H3zM17 4h-5a2 2 0 0 0-2 2v10a2 2 0 0 1 2-2h5z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
    wrench: '<path d="M12.5 3.5a3.5 3.5 0 0 0-3.3 4.7L3.5 13.9l2.6 2.6 5.7-5.7a3.5 3.5 0 0 0 4.7-3.3l-2 .6-1.6-1.6.6-2z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>' };
  function sprite() {
    if (document.getElementById('mp-sprite')) return;
    const d = document.createElement('div'); d.innerHTML = `<svg id="mp-sprite" width="0" height="0" style="position:absolute" aria-hidden="true">${Object.entries(ICONS).map(([k, v]) => `<symbol id="i-${k}" viewBox="0 0 20 20">${v}</symbol>`).join('')}</svg>`;
    document.body.prepend(d.firstChild);
    const f = document.createElement('link'); f.rel = 'icon'; f.href = 'data:image/svg+xml,' + encodeURIComponent(MARK(32).replace('currentColor', '#efe9dd').replace(/currentColor/g, '#efe9dd')); document.head.append(f);
  }
  const css = `.mpm{position:fixed;z-index:95;background:#0e0d0c;border:1px solid #2a2723;border-radius:12px;padding:6px;width:min(300px,94vw);max-height:78dvh;overflow:auto;font:12px 'IBM Plex Mono',monospace;color:#efe9dd;box-shadow:0 18px 40px #000b}
  .mpm h5{margin:8px 10px 4px;font:500 9.5px 'IBM Plex Mono',monospace;letter-spacing:.2em;color:#6f695f}
  .mpm button{display:grid;grid-template-columns:22px 1fr auto;gap:10px;align-items:center;width:100%;text-align:left;background:none;border:0;padding:10px;border-radius:8px;cursor:pointer;color:#efe9dd;font:inherit;min-height:44px}
  .mpm button:hover{background:#ffffff0c}.mpm button svg{width:18px;height:18px;color:#9a938a}.mpm button.on svg{color:#e8c070}.mpm small{display:block;color:#8a8378;font-size:10.5px}
  .mpm .st{font-size:10px;color:#e8c070;letter-spacing:.06em}
  @media(max-width:640px){.mpm{left:0!important;right:0!important;bottom:0!important;top:auto!important;width:100%;border-radius:14px 14px 0 0;padding-bottom:calc(10px + env(safe-area-inset-bottom))}}`;
  let styled = false, el = null;
  function menu(btn, groups) {
    if (!styled) { const s = document.createElement('style'); s.textContent = css; document.head.append(s); styled = true; }
    if (el && el.dataset.for === btn.id && !el.hidden) { el.hidden = true; return; }
    if (!el) { el = document.createElement('div'); el.className = 'mpm'; el.setAttribute('role', 'menu'); document.body.append(el); }
    const v = x => typeof x === 'function' ? x() : x;
    el.dataset.for = btn.id; el.hidden = false; el.innerHTML = '';
    groups.forEach(g => { const items = g.items.filter(i => !v(i.hidden)); if (!items.length) return;
      const h = document.createElement('h5'); h.textContent = g.title; el.append(h);
      items.forEach(i => { const b = document.createElement('button'); b.setAttribute('role', 'menuitem'); const on = v(i.on);
        b.className = on ? 'on' : ''; b.innerHTML = `<svg><use href="#i-${v(i.icon)}"/></svg><span>${v(i.label)}${i.hint ? `<small>${v(i.hint)}</small>` : ''}</span>${i.state ? `<span class="st">${v(i.state)}</span>` : ''}`;
        b.onclick = e => { e.stopPropagation(); const keep = i.act(b); if (keep !== true) el.hidden = true; else menu.refresh(); }; el.append(b); }); });
    menu.refresh = () => { el.hidden = true; el.dataset.for = ''; menu(btn, groups); };
    const r = btn.getBoundingClientRect(), w = Math.min(300, innerWidth * .94);
    el.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.right - w)) + 'px';
    if (r.top > innerHeight / 2) { el.style.top = 'auto'; el.style.bottom = (innerHeight - r.top + 8) + 'px'; } else { el.style.bottom = 'auto'; el.style.top = (r.bottom + 8) + 'px'; }
    setTimeout(() => document.addEventListener('click', function off(e) { if (!el.contains(e.target) && !btn.contains(e.target)) { el.hidden = true; document.removeEventListener('click', off); } }), 0);
  }
  window.MPUI = { mark: MARK, sprite, menu, ICONS };
})();
