/* CINEOSIS MARKS · the four sets the lessons draw with, as small functions returning SVG or drawing to a canvas.
   06 line, circle, dot  : MK.o(sign) an O holding a symbol, colour only inside it; MK.line / MK.dot for timelines
   07 wink, not blink    : MK.eye(state) the ring with two eyes; 'open', 'blink' (a machine pass, a cut), 'wink' (a reading, a choice)
   13 the web of cineosis: MK.radar(axes, values) a web with its spokes labelled
   11 bolas pixel        : MK.pixel(canvas, draw) a 32-pixel grid drawn crisp; MK.pixSign(canvas, sym, colour)
   Red is only ever the thread. */
(function () {
  const DOMC = { perception: '#b0952f', affect: '#c0674a', action: '#c06a32', reflection: '#6e9445', mental: '#4f8f8f', time: '#6b63b0', break: '#8a8274', read: '#a0648f' };
  const DOMN = { perception: 'Perception', affect: 'Affection', action: 'Action', reflection: 'Reflection', mental: 'Mental', time: 'Time', break: 'Break', read: 'Readable' };
  const INK = '#ece6da', RED = '#e0483a', PAPER = '#0b0a09';
  const esc = t => String(t ?? '').replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  /* 06: an O holding a symbol */
  function o(sym, dom, r = 30, opt = {}) {
    const c = DOMC[dom] || '#888', w = r * .12, st = opt.state || 'solid';
    const fill = st === 'empty' ? 'none' : st === 'hatched' ? `url(#h-${dom})` : c;
    return `<svg width="${2 * r + w * 2}" height="${2 * r + w * 2 + (opt.thread ? r : 0)}" viewBox="${-r - w} ${-r - w - (opt.thread ? r : 0)} ${2 * r + 2 * w} ${2 * r + 2 * w + (opt.thread ? r : 0)}" style="overflow:visible;display:block">
      <defs><pattern id="h-${dom}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="${PAPER}"/><line x1="0" y1="0" x2="0" y2="6" stroke="${c}" stroke-width="2.4"/></pattern></defs>
      ${opt.thread ? `<line x1="0" y1="${-r - w - r}" x2="0" y2="${-r}" stroke="${RED}" stroke-width="${Math.max(1.5, r * .06)}"/>` : ''}
      <circle r="${r * .93}" fill="${fill}"/><circle r="${r}" fill="none" stroke="${INK}" stroke-width="${w}"/>
      <text y="${r * .12}" text-anchor="middle" dominant-baseline="middle" font-family="Fraunces, Georgia, serif" font-weight="600" font-size="${r * .82}" fill="${st === 'empty' ? INK : '#111'}">${esc(sym)}</text></svg>`;
  }
  /* 07: the mark. 'open' watching; 'blink' both eyes closed for one beat (a machine pass); 'wink' one eye held shut (a reading) */
  function eye(state = 'open', r = 22, opt = {}) {
    const w = r * .14, ex = r * .34, er = r * .17, ink = opt.ink || INK;
    const e = (x, closed, curve) => closed ? `<path d="M ${x - er * 1.1} 0 Q ${x} ${er * 1.3 * curve} ${x + er * 1.1} 0" fill="none" stroke="${ink}" stroke-width="${r * .08}" stroke-linecap="round"/>` : `<circle cx="${x}" cy="0" r="${er}" fill="${ink}"/>`;
    return `<svg width="${2 * r + 2 * w}" height="${2 * r + 2 * w + (opt.thread ? r : 0)}" viewBox="${-r - w} ${-r - w - (opt.thread ? r : 0)} ${2 * r + 2 * w} ${2 * r + 2 * w + (opt.thread ? r : 0)}" style="overflow:visible;display:block" role="img" aria-label="${state === 'wink' ? 'a wink: a reading' : state === 'blink' ? 'a blink: a machine pass' : 'watching'}">
      ${opt.thread ? `<line x1="0" y1="${-r - w - r}" x2="0" y2="${-r}" stroke="${RED}" stroke-width="${Math.max(1.5, r * .06)}"/>` : ''}
      <circle r="${r}" fill="${opt.fill || 'none'}" stroke="${ink}" stroke-width="${w}"/>${e(-ex, state === 'blink', 0)}${e(ex, state !== 'open', state === 'wink' ? .9 : 0)}</svg>`;
  }
  /* 13: a radar, spokes labelled */
  function radar(axes, vals, opt = {}) {
    const W = opt.w || 640, H = opt.h || 560, cx = W / 2, cy = H / 2 + 10, R = Math.min(W, H) * .34, n = axes.length, mx = Math.max(...vals);
    const pt = (i, v) => { const a = -Math.PI / 2 + i / n * Math.PI * 2; return [cx + Math.cos(a) * R * v, cy + Math.sin(a) * R * v]; };
    let s = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" style="overflow:visible">`;
    for (let k = 1; k <= 4; k++) s += `<polygon points="${axes.map((_, i) => pt(i, k / 4).join(',')).join(' ')}" fill="none" stroke="#3a362f" stroke-width="1"/>`;
    axes.forEach((a, i) => { const [x, y] = pt(i, 1), [lx, ly] = pt(i, 1.2); s += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#3a362f"/><text x="${lx}" y="${ly}" text-anchor="${Math.abs(lx - cx) < 8 ? 'middle' : lx > cx ? 'start' : 'end'}" dominant-baseline="middle" font-family="IBM Plex Mono, monospace" font-size="17" fill="${opt.colors ? opt.colors[i] : '#a29d90'}">${esc(a)}</text>`; });
    const P = vals.map((v, i) => pt(i, v / mx).join(',')).join(' ');
    s += `<polygon class="rpoly" points="${P}" fill="rgba(224,72,58,.12)" stroke="${RED}" stroke-width="3" stroke-linejoin="round"/>`;
    vals.forEach((v, i) => { const [x, y] = pt(i, v / mx); s += `<circle cx="${x}" cy="${y}" r="5" fill="${RED}"/>`; });
    return s + '</svg>';
  }
  /* 11: pixel */
  const FONT = { A: ['010', '101', '111', '101', '101'], B: ['110', '101', '110', '101', '110'], C: ['011', '100', '100', '100', '011'], D: ['110', '101', '101', '101', '110'], E: ['111', '100', '110', '100', '111'], F: ['111', '100', '110', '100', '100'], G: ['011', '100', '101', '101', '011'], H: ['101', '101', '111', '101', '101'], I: ['111', '010', '010', '010', '111'], K: ['101', '110', '100', '110', '101'], L: ['100', '100', '100', '100', '111'], M: ['101', '111', '111', '101', '101'], N: ['101', '111', '111', '111', '101'], O: ['010', '101', '101', '101', '010'], P: ['110', '101', '110', '100', '100'], Q: ['010', '101', '101', '110', '011'], R: ['110', '101', '110', '101', '101'], S: ['011', '100', '010', '001', '110'], T: ['111', '010', '010', '010', '010'], U: ['101', '101', '101', '101', '111'], V: ['101', '101', '101', '101', '010'], W: ['101', '101', '111', '111', '101'], X: ['101', '101', '010', '101', '101'], Y: ['101', '101', '010', '010', '010'] };
  function pixel(cv, draw) {
    const N = 32, b = new Array(N * N).fill(null), px = (x, y, c) => { x = Math.round(x); y = Math.round(y); if (x >= 0 && y >= 0 && x < N && y < N) b[y * N + x] = c; };
    const g = { px, line(x0, y0, x1, y1, c) { const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1; for (let i = 0; i <= n; i++) px(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, c); },
      ring(cx, cy, r, c) { for (let a = 0; a < 360; a += 3) px(cx + Math.cos(a * Math.PI / 180) * r, cy + Math.sin(a * Math.PI / 180) * r, c); },
      disc(cx, cy, r, c) { for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) if (x * x + y * y <= r * r + r * .6) px(cx + x, cy + y, c); },
      text(s, x, y, c) { for (const ch of s.toUpperCase()) { (FONT[ch] || []).forEach((row, j) => [...row].forEach((v, i) => v === '1' && px(x + i, y + j, c))); x += 4; } } };
    draw(g); const c = cv.getContext('2d'); cv.width = cv.height = N; c.fillStyle = PAPER; c.fillRect(0, 0, N, N);
    b.forEach((col, i) => { if (col) { c.fillStyle = col; c.fillRect(i % N, Math.floor(i / N), 1, 1); } });
  }
  const pixSign = (cv, sym, dom) => pixel(cv, g => { g.line(16, 0, 16, 3, RED); g.disc(16, 13, 9, PAPER); g.disc(16, 13, 8, DOMC[dom]); g.ring(16, 13, 9, INK); g.text(sym.slice(0, 2), 16 - 3.5, 11, '#111'); g.disc(16, 25, 2, INK); g.px(15, 25, PAPER); g.px(17, 25, PAPER); });
  window.MK = { DOMC, DOMN, o, eye, radar, pixel, pixSign, esc };
})();
