/* PARTY: one room for every game. One screen is the stand (a TV, a laptop, a phone on its side); every phone joins once with a
   name and a drawn character and stays on the crew while the games change. The platform carries what every game shares:
   the wire (PeerJS between devices, BroadcastChannel between tabs with ?net=bc), joining by QR, reconnecting, a heartbeat,
   the screen kept awake, the room remembered if the stand reloads; the crew on the ground plane (they walk, jump, dance,
   catch, cheer, slump, bow); throwing tomatoes and roses and CUT! and BRAVO! at whatever is on screen, tallied and awarded;
   and gates: nothing moves on until a person says so.
   A game is a module: Party.games[id] = { title, blurb, options, host(H) -> { stateFor(p), onMsg(p, m), crowdTarget(),
   performer(), stop() }, phone(S, api) -> { status, tab, tabs, takeover } }. */
(function (root) {
  const $ = s => document.querySelector(s), esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const Q = new URLSearchParams(location.search), NET = Q.get('net') === 'bc' ? 'bc' : 'peer';
  const rnd = Math.random, pick = xs => xs[Math.floor(rnd() * xs.length)], shuffle = xs => { xs = xs.slice(); for (let k = xs.length - 1; k > 0; k--) { const j = Math.floor(rnd() * (k + 1)); [xs[k], xs[j]] = [xs[j], xs[k]]; } return xs; };
  const UP = s => String(s).toUpperCase(), pad = n => String(n).padStart(2, '0');
  const store = { get(k, d) { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } } };
  const fullscreen = lock => { try { const d = document.documentElement, f = d.requestFullscreen || d.webkitRequestFullscreen; if (f && !document.fullscreenElement) { const r = f.call(d); if (r && r.then) r.then(() => { if (lock && screen.orientation && screen.orientation.lock) screen.orientation.lock('landscape').catch(() => { }); }).catch(() => { }); } } catch (e) { } };
  let wakeLock = null; const wake = async () => { try { if ('wakeLock' in navigator && document.visibilityState === 'visible' && !wakeLock) { wakeLock = await navigator.wakeLock.request('screen'); wakeLock.addEventListener('release', () => wakeLock = null); } } catch (e) { } };
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') wake(); });
  // ---- the crew: twelve characters in ink and gouache, and the house (a camera on legs, film reels for ears)
  const KINDS = [{ n: 'fox', c: '#d9772b' }, { n: 'octopus', c: '#9b77bd' }, { n: 'owl', c: '#a07b55' }, { n: 'frog', c: '#78a957' }, { n: 'tiger', c: '#e5a93f' }, { n: 'panda', c: '#f3eee2' },
    { n: 'unicorn', c: '#efb3c3' }, { n: 'bee', c: '#ecc94b' }, { n: 'turtle', c: '#6fae99' }, { n: 'dino', c: '#5d9fb0' }, { n: 'penguin', c: '#3f5470' }, { n: 'lion', c: '#dcaa52' }];
  const NK = KINDS.length, colOf = k => k === 'house' ? '#4a4a55' : KINDS[k].c;
  let clipN = 0;
  function toon(k, o = {}) {
    const ink = '#2a1f1a', S = `stroke="${ink}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"`, c = colOf(k), K = k === 'house' ? 'house' : KINDS[k].n;
    let back = '', body = `<ellipse cx="50" cy="88" rx="23" ry="24" fill="${c}" ${S}/>`, belly = '', earsB = '', head = `<circle cx="50" cy="46" r="21" fill="${c}" ${S}/>`, face = '';
    let eyes = `<g class="eyes"><circle cx="42" cy="45" r="3.6" fill="${ink}"/><circle cx="58" cy="45" r="3.6" fill="${ink}"/><circle cx="43.2" cy="43.8" r="1.1" fill="#fff"/><circle cx="59.2" cy="43.8" r="1.1" fill="#fff"/></g>`;
    let mouth = `<path d="M45 55 Q50 59 55 55" fill="none" ${S}/>`, feet = `<ellipse cx="40" cy="112" rx="8" ry="4.5" fill="${c}" ${S}/><ellipse cx="60" cy="112" rx="8" ry="4.5" fill="${c}" ${S}/>`;
    let arms = `<path class="aL" d="M29 80 Q21 90 25 100" fill="none" ${S} stroke-width="5"/><path class="aR" d="M71 80 Q79 90 75 100" fill="none" ${S} stroke-width="5"/>`, top = '';
    const muzzle = (col = '#fff4e6') => `<ellipse cx="50" cy="54" rx="9" ry="6.5" fill="${col}" ${S}/><ellipse cx="50" cy="50.5" rx="2.6" ry="2" fill="${ink}"/><path d="M47 56 Q50 58.5 53 56" fill="none" ${S} stroke-width="2"/>`;
    if (K === 'fox') { back = `<path d="M68 100 Q98 96 92 66 Q84 84 70 90Z" fill="${c}" ${S}/><path d="M92 66 Q90 78 85 80 Q90 72 92 66Z" fill="#fff4e6" ${S} stroke-width="2"/>`; earsB = `<path d="M34 36 L29 15 L46 28Z" fill="${c}" ${S}/><path d="M66 36 L71 15 L54 28Z" fill="${c}" ${S}/>`; belly = `<ellipse cx="50" cy="92" rx="12" ry="14" fill="#fff4e6"/>`; face = muzzle(); mouth = ''; }
    if (K === 'octopus') { body = ''; feet = ''; arms = ''; back = [22, 36, 50, 64, 78].map((x, i) => `<path d="M${x} 74 Q${x + (i % 2 ? 8 : -8)} 92 ${x} 112" fill="none" stroke="${ink}" stroke-width="11" stroke-linecap="round"/><path d="M${x} 74 Q${x + (i % 2 ? 8 : -8)} 92 ${x} 112" fill="none" stroke="${c}" stroke-width="6" stroke-linecap="round"/>`).join(''); head = `<path d="M22 80 Q18 22 50 22 Q82 22 78 80Z" fill="${c}" ${S}/>`; eyes = eyes.replace(/cy="45"/g, 'cy="54"').replace(/cy="43.8"/g, 'cy="52.8"'); mouth = `<path d="M45 64 Q50 68 55 64" fill="none" ${S}/>`; }
    if (K === 'owl') { earsB = `<path d="M31 34 L27 16 L42 28Z" fill="${c}" ${S}/><path d="M69 34 L73 16 L58 28Z" fill="${c}" ${S}/>`; face = `<circle cx="41" cy="45" r="8" fill="#fff4e6" ${S} stroke-width="2"/><circle cx="59" cy="45" r="8" fill="#fff4e6" ${S} stroke-width="2"/><path d="M47 51 L53 51 L50 57Z" fill="#e5a93f" ${S} stroke-width="2"/>`; mouth = ''; belly = `<ellipse cx="50" cy="92" rx="13" ry="15" fill="#e8d6b8"/><path d="M44 86 l3 3 l3 -3 l3 3 l3 -3 M44 94 l3 3 l3 -3 l3 3 l3 -3" fill="none" ${S} stroke-width="1.6"/>`; }
    if (K === 'frog') { head = `<ellipse cx="50" cy="50" rx="26" ry="17" fill="${c}" ${S}/>`; earsB = `<circle cx="37" cy="36" r="9" fill="${c}" ${S}/><circle cx="63" cy="36" r="9" fill="${c}" ${S}/>`; eyes = `<g class="eyes"><circle cx="37" cy="36" r="4.2" fill="${ink}"/><circle cx="63" cy="36" r="4.2" fill="${ink}"/><circle cx="38.4" cy="34.6" r="1.2" fill="#fff"/><circle cx="64.4" cy="34.6" r="1.2" fill="#fff"/></g>`; mouth = `<path d="M33 53 Q50 65 67 53" fill="none" ${S}/>`; belly = `<ellipse cx="50" cy="92" rx="13" ry="14" fill="#cfe3a8"/>`; }
    if (K === 'tiger') { earsB = `<circle cx="34" cy="30" r="7" fill="${c}" ${S}/><circle cx="66" cy="30" r="7" fill="${c}" ${S}/>`; face = muzzle() + `<path d="M44 28 l2 6 M50 26 v7 M56 28 l-2 6" ${S} stroke-width="2.4"/>`; mouth = ''; belly = `<path d="M28 82 l8 3 M28 92 l9 2 M72 82 l-8 3 M72 92 l-9 2" ${S} stroke-width="2.6"/>`; }
    if (K === 'panda') { earsB = `<circle cx="33" cy="30" r="7.5" fill="${ink}"/><circle cx="67" cy="30" r="7.5" fill="${ink}"/>`; face = `<ellipse cx="41" cy="46" rx="6" ry="7.5" transform="rotate(-20 41 46)" fill="${ink}"/><ellipse cx="59" cy="46" rx="6" ry="7.5" transform="rotate(20 59 46)" fill="${ink}"/>`; eyes = `<g class="eyes"><circle cx="42" cy="45" r="2.2" fill="#fff"/><circle cx="58" cy="45" r="2.2" fill="#fff"/></g>`; arms = arms.replace(/stroke="#2a1f1a" stroke-width="3"([^>]*)stroke-width="5"/g, 'stroke="#2a1f1a"$1stroke-width="7"'); feet = feet.replace(/fill="#f3eee2"/g, `fill="${ink}"`); mouth = `<ellipse cx="50" cy="52" rx="2.6" ry="2" fill="${ink}"/><path d="M47 56 Q50 58.5 53 56" fill="none" ${S} stroke-width="2"/>`; }
    if (K === 'unicorn') { top = `<path d="M50 4 L44 27 L56 27Z" fill="#f3d27a" ${S}/><path d="M46 20 l8 -3 M47 13 l6 -2" ${S} stroke-width="1.6"/>`; earsB = `<path d="M35 33 L33 20 L44 28Z" fill="${c}" ${S}/><path d="M65 33 L67 20 L56 28Z" fill="${c}" ${S}/>`; back = `<path d="M60 26 Q80 30 76 50 Q84 60 74 70 Q70 52 62 44Z" fill="#a88ad0" ${S}/>`; }
    if (K === 'bee') { const id = 'cb' + (++clipN); body = `<clipPath id="${id}"><ellipse cx="50" cy="88" rx="23" ry="24"/></clipPath><ellipse cx="50" cy="88" rx="23" ry="24" fill="${c}"/><g clip-path="url(#${id})"><rect x="20" y="80" width="60" height="6" fill="${ink}"/><rect x="20" y="94" width="60" height="6" fill="${ink}"/></g><ellipse cx="50" cy="88" rx="23" ry="24" fill="none" ${S}/>`; back = `<ellipse cx="28" cy="70" rx="12" ry="8" transform="rotate(-30 28 70)" fill="#dff1f7" ${S} stroke-width="2"/><ellipse cx="72" cy="70" rx="12" ry="8" transform="rotate(30 72 70)" fill="#dff1f7" ${S} stroke-width="2"/>`; top = `<path d="M42 27 Q38 14 32 12 M58 27 Q62 14 68 12" fill="none" ${S} stroke-width="2.4"/><circle cx="32" cy="12" r="3" fill="${ink}"/><circle cx="68" cy="12" r="3" fill="${ink}"/>`; }
    if (K === 'turtle') { belly = `<path d="M24 96 Q24 64 50 62 Q76 64 76 96Z" fill="#9a7a4a" ${S}/><path d="M38 70 L50 66 L62 70 L60 84 L40 84Z M40 84 L30 92 M60 84 L70 92 M50 66 L50 64" fill="none" ${S} stroke-width="2"/>`; head = `<circle cx="50" cy="46" r="19" fill="#9fd0b9" ${S}/>`; }
    if (K === 'dino') { back = `<path d="M70 98 Q100 104 98 84 Q90 94 72 88Z" fill="${c}" ${S}/>`; earsB = [[34, 30], [42, 24], [50, 22], [58, 24], [66, 30]].map(([x, y]) => `<path d="M${x - 5} ${y + 5} L${x} ${y - 7} L${x + 5} ${y + 5}Z" fill="#e5a93f" ${S} stroke-width="2.2"/>`).join(''); arms = `<path class="aL" d="M32 80 Q27 85 30 89" fill="none" ${S} stroke-width="5"/><path class="aR" d="M68 80 Q73 85 70 89" fill="none" ${S} stroke-width="5"/>`; belly = `<ellipse cx="50" cy="92" rx="12" ry="14" fill="#cfe7ea"/>`; mouth = `<path d="M40 55 Q50 61 60 55" fill="none" ${S}/>`; }
    if (K === 'penguin') { belly = `<ellipse cx="50" cy="92" rx="15" ry="18" fill="#f6f1e6"/>`; face = `<circle cx="44" cy="47" r="9" fill="#f6f1e6"/><circle cx="56" cy="47" r="9" fill="#f6f1e6"/><path d="M45 52 L55 52 L50 59Z" fill="#e5a93f" ${S} stroke-width="2"/>`; mouth = ''; feet = `<ellipse cx="40" cy="112" rx="8" ry="4.5" fill="#e5a93f" ${S}/><ellipse cx="60" cy="112" rx="8" ry="4.5" fill="#e5a93f" ${S}/>`; arms = `<path class="aL" d="M28 76 Q18 92 26 102" fill="none" stroke="${ink}" stroke-width="9" stroke-linecap="round"/><path class="aR" d="M72 76 Q82 92 74 102" fill="none" stroke="${ink}" stroke-width="9" stroke-linecap="round"/>`; }
    if (K === 'lion') { earsB = `<path d="${Array.from({ length: 14 }, (_, i) => { const a = i / 14 * Math.PI * 2, b = (i + .5) / 14 * Math.PI * 2; return (i ? 'L' : 'M') + (50 + 26 * Math.cos(a)).toFixed(1) + ' ' + (46 + 26 * Math.sin(a)).toFixed(1) + ' Q' + (50 + 34 * Math.cos(b)).toFixed(1) + ' ' + (46 + 34 * Math.sin(b)).toFixed(1) + ' ' + (50 + 26 * Math.cos(a + Math.PI / 7)).toFixed(1) + ' ' + (46 + 26 * Math.sin(a + Math.PI / 7)).toFixed(1); }).join(' ')}Z" fill="#b56a2c" ${S}/>`; face = muzzle(); mouth = ''; back = `<path d="M70 100 Q92 104 90 86" fill="none" ${S}/><circle cx="90" cy="84" r="5" fill="#b56a2c" ${S}/>`; }
    if (K === 'house') { body = `<rect x="30" y="66" width="40" height="34" rx="5" fill="#3a3a44" ${S}/><path d="M50 66 L50 100" ${S} stroke-width="1.5"/><circle cx="50" cy="80" r="2" fill="#d9a441"/><circle cx="50" cy="90" r="2" fill="#d9a441"/>`;
      feet = `<path d="M38 100 L30 114 M50 100 L50 115 M62 100 L70 114" fill="none" ${S} stroke-width="4"/>`; earsB = `<circle cx="32" cy="18" r="12" fill="#3a3a44" ${S}/><circle cx="68" cy="18" r="12" fill="#3a3a44" ${S}/><circle cx="32" cy="18" r="3" fill="#d9a441"/><circle cx="68" cy="18" r="3" fill="#d9a441"/>`;
      head = `<rect x="27" y="28" width="46" height="36" rx="6" fill="#3a3a44" ${S}/>`; face = `<circle cx="50" cy="46" r="12" fill="#d9a441" ${S}/>`; eyes = `<g class="eyes"><circle cx="50" cy="46" r="7.5" fill="#8fb8c9" ${S} stroke-width="2"/><circle cx="52.5" cy="43.5" r="2" fill="#fff"/></g>`; mouth = ''; arms = arms.replace(/stroke-width="5"/g, 'stroke-width="4"'); }
    const flt = o.still ? '' : ' filter="url(#boil)"', delay = o.still ? '' : ` style="animation-delay:${(rnd() * 4).toFixed(2)}s"`;
    return `<svg class="toon" viewBox="-4 -2 108 122" xmlns="http://www.w3.org/2000/svg"><g${flt}>${back}${earsB}${arms}${body}${belly}${feet}${head}${top}${face}${eyes.replace('class="eyes"', 'class="eyes"' + delay)}${mouth}</g></svg>`;
  }
  const mini = k => `<span class="mini">${toon(k, { still: true })}</span>`;
  const BEAT = .75, MAXT = 12, THROWS = ['tomato', 'rose', 'cut', 'bravo'];
  const ICON = {
    tomato: `<svg viewBox="0 0 40 40"><g filter="url(#boil)"><circle cx="20" cy="23" r="14" fill="#d8392b" stroke="#2a1f1a" stroke-width="2.5"/><path d="M20 8 l2.5 4.5 l5 -1.5 l-3 4 l4 3 l-5 0 l-1 5 l-2.5 -4.5 l-4.5 2.5 l1.5 -5 l-5 -2 l5 -1Z" fill="#5f9a3a" stroke="#2a1f1a" stroke-width="1.6" stroke-linejoin="round"/><ellipse cx="14" cy="19" rx="3.4" ry="2.2" fill="#fff" opacity=".55"/></g></svg>`,
    rose: `<svg viewBox="0 0 40 40"><g filter="url(#boil)"><path d="M20 22 Q18 30 21 39" fill="none" stroke="#3f7a3a" stroke-width="2.6"/><path d="M20 31 Q12 27 11 31 Q15 34 20 32Z" fill="#5f9a3a" stroke="#2a1f1a" stroke-width="1.4"/><circle cx="20" cy="14" r="10" fill="#c8303f" stroke="#2a1f1a" stroke-width="2.4"/><path d="M15 14 Q20 7 25 13 Q21 20 16 16 Q19 11 22 14" fill="none" stroke="#2a1f1a" stroke-width="1.6"/></g></svg>`,
    cut: `<svg viewBox="0 0 40 40"><g filter="url(#boil)"><path d="M20 26 V39" stroke="#7a5a3a" stroke-width="3"/><rect x="3" y="6" width="34" height="20" rx="2" fill="#f4ecd8" stroke="#2a1f1a" stroke-width="2.4" transform="rotate(-6 20 16)"/><text x="20" y="21" text-anchor="middle" font-family="Fredericka the Great, Georgia, serif" font-size="12" fill="#c8553d" transform="rotate(-6 20 16)">CUT!</text></g></svg>`,
    bravo: `<svg viewBox="0 0 40 40"><g filter="url(#boil)"><path d="M20 3 L24 14 L36 14 L26 21 L30 33 L20 26 L10 33 L14 21 L4 14 L16 14Z" fill="#ecc94b" stroke="#2a1f1a" stroke-width="2.4" stroke-linejoin="round"/></g></svg>`,
    splat: `<svg viewBox="0 0 60 60"><g filter="url(#boil)"><path d="M30 8 Q36 18 44 12 Q42 22 54 24 Q44 30 50 40 Q40 38 38 50 Q32 42 24 52 Q22 40 10 44 Q16 34 6 28 Q18 24 12 14 Q22 18 30 8Z" fill="#d8392b" stroke="#2a1f1a" stroke-width="2"/><circle cx="26" cy="28" r="2" fill="#f3d27a"/><circle cx="34" cy="32" r="2" fill="#f3d27a"/><circle cx="30" cy="22" r="1.6" fill="#f3d27a"/><path d="M28 50 Q28 58 30 59" stroke="#d8392b" stroke-width="3" fill="none"/></g></svg>` };


  // ---- the wire: PeerJS between devices; BroadcastChannel between tabs of one browser (?net=bc). The stand is the authority.
  const ICE = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:global.stun.twilio.com:3478' }] };
  const Net = {
    host(code, onMsg, onState) {
      if (NET === 'bc') { const ch = new BroadcastChannel('party-' + code); ch.onmessage = e => { if (e.data.to === 'host') onMsg(e.data.pid, e.data.msg); }; setTimeout(() => onState('open')); return { send: (pid, msg) => ch.postMessage({ to: pid, msg }), close: () => ch.close() }; }
      const peer = new Peer('party-' + code, { debug: 0, config: ICE }), conns = new Map();
      peer.on('open', () => onState('open')); peer.on('error', e => onState(e.type === 'unavailable-id' ? 'taken' : 'error', e.type));
      peer.on('disconnected', () => { try { peer.reconnect(); } catch (e) { } });
      peer.on('connection', c => { c.on('data', m => { if (m && m.pid) { conns.set(m.pid, c); onMsg(m.pid, m.msg); } });
        c.on('close', () => { for (const [k, v] of conns) if (v === c) { conns.delete(k); onMsg(k, { t: 'gone' }); } }); });
      return { send: (pid, msg) => { const c = conns.get(pid); if (c && c.open) try { c.send(msg); } catch (e) { } }, close: () => peer.destroy() };
    },
    join(code, pid, onMsg, onState) {
      if (NET === 'bc') { const ch = new BroadcastChannel('party-' + code); ch.onmessage = e => { if (e.data.to === pid) onMsg(e.data.msg); }; setTimeout(() => onState('open')); return { send: msg => ch.postMessage({ to: 'host', pid, msg }), restart() { onState('open'); } }; }
      let conn = null, peer = null, wait = 1000, dead = false;
      const go = () => { if (dead) return; try { if (peer) peer.destroy(); } catch (e) { } peer = new Peer({ debug: 0, config: ICE });
        peer.on('open', () => { conn = peer.connect('party-' + code, { reliable: true }); conn.on('open', () => { wait = 1000; onState('open'); }); conn.on('data', onMsg); conn.on('close', () => { onState('lost'); retry(); }); });
        peer.on('error', e => { onState('error', e.type); retry(); }); };
      const retry = () => { clearTimeout(go.t); go.t = setTimeout(go, wait); wait = Math.min(8000, wait * 1.6); };
      go(); return { send: msg => { if (conn && conn.open) try { conn.send({ pid, msg }); } catch (e) { } }, restart() { retry(); } };
    }
  };

  // ---- the painted card: sky, far hills, near hills, the words, foreground foliage; each plane trucks in at its depth, then drifts
  const MOODS = { dawn: ['#f6d9a8', '#f0b48c', '#c99b84', '#8f9a6a', '#5d6b45', '#2f3a26', '#fff3c4'], night: ['#1f2d4d', '#3b4e78', '#3d4a6b', '#2c3858', '#1c2540', '#0f1426', '#f3eccf'],
    stage: ['#6e2a26', '#c8553d', '#8c3a32', '#6b2a25', '#4a1d1a', '#2a100e', '#ffd9a0'], gold: ['#f6e4a4', '#e7b65a', '#d39a4a', '#b07a3a', '#7d5428', '#3d2a14', '#fffbe8'], house: ['#2b2b33', '#4b4b5c', '#3a3a48', '#2b2b36', '#1c1c24', '#0d0d12', '#d9a441'],
    rose: ['#f6d1cc', '#e7aaa4', '#d58f8a', '#b07a86', '#7d5866', '#3d2a34', '#fff3f0'], sea: ['#cfe6ea', '#8fb8c9', '#6f9fb0', '#4f8090', '#335f6e', '#1c3640', '#fffbe8'] };
  function card(html, mood = 'dawn') { const m = MOODS[mood] || MOODS.dawn, L = (d, svg) => `<div class="l" style="--d:${d}"><div class="dr"><svg viewBox="0 0 200 100" preserveAspectRatio="none">${svg}</svg></div></div>`;
    return `<div class="card ${mood === 'dawn' || mood === 'gold' || mood === 'rose' || mood === 'sea' ? 'light' : ''}" style="background:linear-gradient(${m[0]},${m[1]})">${L(.05, `<circle cx="150" cy="28" r="11" fill="${m[6]}" opacity=".85"/>`)}${L(.16, `<path d="M0 62 Q18 44 36 56 T72 50 T110 58 T150 44 T200 56 V100 H0Z" fill="${m[2]}"/>`)}${L(.34, `<path d="M0 76 Q26 62 52 72 T104 69 T156 76 T200 70 V100 H0Z" fill="${m[3]}"/>`)}${L(.58, `<path d="M0 88 Q40 79 80 86 T160 83 T200 88 V100 H0Z" fill="${m[4]}"/>`)}
      ${L(1, `<path d="M0 100 V44 Q5 34 9 46 Q13 30 18 48 Q22 42 21 60 Q27 64 22 80 Q29 88 25 100Z M200 100 V48 Q195 36 191 50 Q187 32 182 52 Q178 46 179 64 Q173 68 178 84 Q171 90 175 100Z" fill="${m[5]}"/>`)}<div class="l words" style="--d:.28"><div class="txt">${html}</div></div></div>`; }

  // =====================================================================  THE STAND
  function host(games) {
    document.body.classList.add('is-host');
    const app = $('#app');
    app.innerHTML = `<div id="host"><header id="top"><div class="pegs"><i></i><i></i><i></i></div><div class="logo" id="logo">Party</div><div class="tagline" id="tagline">one room · every game · the archive’s films</div><span id="roomTag"></span><button class="btn" id="earsB" title="the key that lets the room be heard: only this screen holds it">ears</button><button class="btn" id="goneB" hidden title="take everyone who has left off the stand">clear gone</button><button class="btn" id="newB" title="a fresh room: new code, nobody joined">new room</button><button class="btn" id="lobbyB" hidden>lobby</button><button class="btn" id="fsB">full screen</button><a href="index.html">lab</a></header>
      <main id="stage"><div id="stand"><div id="screen"><div id="vids"></div><div id="slate"></div><div id="paper" hidden></div><div id="cap"></div><div id="splats"></div><div id="crowd"></div><div id="bug"></div><div id="log"></div></div></div><aside id="side"></aside></main>
      <footer id="crew"><div class="pl"><svg viewBox="0 0 200 100" preserveAspectRatio="none"><path d="M0 40 Q20 22 44 34 T90 30 T140 36 T200 28 V100 H0Z" fill="#86a58a"/><path d="M0 58 Q30 48 60 56 T120 54 T200 56 V100 H0Z" fill="#6c8c63"/></svg></div><div id="toons"></div><div class="pl"><svg viewBox="0 0 200 100" preserveAspectRatio="none" style="top:auto;bottom:0;height:30%"><path d="M0 100 V60 Q4 40 8 62 Q12 36 16 64 Q20 44 24 70 V100Z M176 100 V70 Q180 44 184 64 Q188 36 192 62 Q196 40 200 60 V100Z" fill="#3e5a36"/></svg></div></footer></div>`;
    $('#fsB').onclick = () => fullscreen(true);
    $('#lobbyB').onclick = () => H.end();
    $('#goneB').onclick = () => H.clearGone();
    $('#newB').onclick = () => { const b = $('#newB'); if (b.classList.contains('sure')) return H.newRoom(); b.classList.add('sure'); b.textContent = 'sure? tap again'; setTimeout(() => { b.classList.remove('sure'); b.textContent = 'new room'; }, 3000); };
    const saved = store.get('party.host', null), H = { players: [], code: null, gameId: null, game: null, gate: null, opts: store.get('party.opts', {}), wireNote: '', card, esc, pad, UP, rnd, pick, shuffle, toon, mini, ICON };
    H.P = id => H.players.find(p => p.id === id);
    H.VP = Array.from({ length: 14 }, () => { const v = document.createElement('video'); v.muted = true; v.playsInline = true; v.preload = 'auto'; $('#vids').append(v); return v; });
    H.AP = Array.from({ length: 6 }, () => { const a = new Audio(); a.preload = 'auto'; return a; });
    H.ears = window.Ears ? Ears.host(H) : null; const earsTag = () => { const b = $('#earsB'); if (!H.ears) { b.hidden = true; return; } b.textContent = H.ears.has() ? 'ears on' : 'ears'; b.classList.toggle('on', H.ears.has()); };
    $('#earsB').onclick = () => H.ears && H.ears.sheet(() => earsTag()); earsTag();
    H.unlock = () => { [...H.VP, ...H.AP].forEach(m => { m.muted = true; m.play().catch(() => { }); m.pause(); m.muted = m.tagName === 'VIDEO'; }); try { H.actx = H.actx || new (window.AudioContext || window.webkitAudioContext)(); H.actx.resume(); } catch (e) { } wake(); };
    H.clap = () => { try { const a = H.actx = H.actx || new (window.AudioContext || window.webkitAudioContext)(); const n = a.sampleRate * .12, b = a.createBuffer(1, n, a.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = (rnd() * 2 - 1) * Math.pow(1 - i / n, 6); const s = a.createBufferSource(); s.buffer = b; s.connect(a.destination); s.start(); } catch (e) { } };
    H.show = id => { ['#slate', '#paper'].forEach(s => $(s).hidden = s !== id); if (id) H.VP.forEach(v => v.classList.remove('on')); };
    H.slate = html => { $('#slate').innerHTML = html; H.show('#slate'); };
    H.paper = html => { $('#paper').innerHTML = html; H.show('#paper'); };
    H.cap = t => { $('#cap').textContent = t || ''; };
    H.bug = html => { $('#bug').innerHTML = html || ''; };
    H.logLine = html => { const d = document.createElement('div'); d.innerHTML = html; $('#log').prepend(d); setTimeout(() => d.remove(), 4000); while ($('#log').children.length > 4) $('#log').lastChild.remove(); };
    H.who = id => { const p = H.P(id); return p ? `<span class="who">${mini(p.av)} ${esc(p.name)}</span>` : `<span class="who">${mini('house')} the house</span>`; };
    let sideKey = '';
    H.side = (html, key) => { const S = $('#side'); S.innerHTML = html + '<button class="btn cta" id="gateB" hidden></button>'; if (key !== sideKey) { sideKey = key; S.scrollTop = 0; } H.drawGate(); return S; };
    // gates: the game never moves on by itself; a person does. who: 'any' (any phone or the stand), 'host', or a list of player ids
    H.gate = (label, who, go) => { H._gate = { label, who: who || 'any', go, id: Math.random() }; H.broadcast(); H.drawGate(); H.syncCrew && H.syncCrew(); };
    H.ungate = () => { H._gate = null; H.broadcast(); H.drawGate(); };
    const gateOK = p => { const g = H._gate; if (!g) return false; if (g.who === 'any') return true; if (g.who === 'host') return false; return Array.isArray(g.who) ? g.who.includes(p.id) : false; };
    H.pass = (fromWho) => { const g = H._gate; if (!g) return; H._gate = null; H.drawGate(); g.go(fromWho); };
    H.drawGate = () => { const b = $('#gateB'); if (!b) return; const g = H._gate; b.hidden = !g; if (g) { b.textContent = g.label; b.onclick = () => H.pass(null); } };
    H.score = p => p.score || 0;

    // ---- the room: opened once, remembered if the stand reloads (phones find it again by the same code)
    let net = null, tries = 0;
    function openRoom(code) { H.code = code || Array.from({ length: 4 }, () => 'ABCDEFGHJKLMNPQRSTUVWXYZ'[Math.floor(rnd() * 24)]).join('');
      net = Net.host(H.code, onMsg, (st, why) => {
        if (st === 'taken') { net.close(); if (saved && saved.code === H.code && tries++ < 6) setTimeout(() => openRoom(H.code), 2500); else openRoom(); return; }
        H.wireNote = st === 'open' ? '' : 'Phones cannot reach this stand (' + why + '). Add players here instead, or reload.'; persist(); draw(); }); }
    const persist = () => store.set('party.host', { code: H.code, players: H.players.map(p => ({ id: p.id, name: p.name, av: p.av, local: p.local, at: p.conn || p.local ? Date.now() : (p.at || 0) })) });
    H.joinURL = () => location.origin + location.pathname + '?room=' + H.code + (NET === 'bc' ? '&net=bc' : '');
    const freeAv = want => { const used = new Set(H.players.map(p => p.av)); if (want != null && !used.has(want)) return want; for (let k = 0; k < NK; k++) if (!used.has(k)) return k; return 0; };
    H.addPlayer = (id, name, av, local) => { if (H.players.length >= 12) return null; const p = { id, name: String(name || 'Crew').slice(0, 12), av: freeAv(av), local: !!local, score: 0, conn: !!local, seen: performance.now() }; H.players.push(p); persist(); return p; };
    if (saved && saved.players) saved.players.filter(x => x.local || (x.at && Date.now() - x.at < 30 * 60000)).forEach(x => { const p = H.addPlayer(x.id, x.name, x.av, x.local); if (p && !p.local) { p.conn = false; p.at = x.at; } });
    // taking players off the stand: one at a time (tap a greyed-out character twice), everyone who has gone, or a whole new room
    H.removePlayer = id => { const i = H.players.findIndex(p => p.id === id); if (i < 0) return; H.players.splice(i, 1); persist(); syncCrew(); if (H.game && H.game.draw) H.game.draw(); else draw(); };
    H.clearGone = () => { H.players.filter(p => !p.local && !p.conn).forEach(p => H.removePlayer(p.id)); };
    H.newRoom = () => { try { localStorage.removeItem('party.host'); } catch (e) { } location.href = location.pathname + (NET === 'bc' ? '?net=bc' : ''); };
    function onMsg(pid, m) {
      let p = H.P(pid); if (!m) return;
      if (m.t === 'hello') { if (!p) { const nm = String(m.name || '').trim().toLowerCase(), ghost = nm && H.players.find(x => !x.local && !x.conn && x.name.trim().toLowerCase() === nm); if (ghost) { const sc = ghost.score; H.players.splice(H.players.indexOf(ghost), 1); p = H.addPlayer(pid, m.name, ghost.av, false); if (p) p.score = sc || 0; } else p = H.addPlayer(pid, m.name, m.av, false); if (!p) { net.send(pid, { t: 'full' }); return; } p.late = !!H.game; } p.conn = true; p.back = true; p.seen = performance.now(); p.name = String(m.name || p.name).slice(0, 12); persist(); draw(); H.send(p, { t: 'pong' }); H.send(p, stateFor(p)); if (H.game && H.game.onJoin) H.game.onJoin(p); return; }
      if (!p) { net.send(pid, { t: 'who' }); return; }
      p.seen = performance.now(); if (!p.conn) { p.conn = true; syncCrew(); }
      if (m.t === 'ping') { H.send(p, { t: 'pong' }); return; }
      if (m.t === 'gone') { p.conn = false; syncCrew(); return; }
      if (m.t === 'gate') { if (H._gate && H._gate.id === m.id && gateOK(p)) H.pass(p.id); return; }
      if (m.t === 'me') return move(p, m.m);
      if (m.t === 'throw' && THROWS.includes(m.w)) return throwFrom(p, m.w);
      if (m.t === 'ear' && H.ears) { H.ears.onMsg(p, m); return; }
      if (H.game && H.game.onMsg) H.game.onMsg(p, m);
    }
    setInterval(() => { const now = performance.now(); let ch = false; H.players.forEach(p => { if (!p.local && p.conn && now - p.seen > 15000) { p.conn = false; ch = true; } }); if (ch) syncCrew(); }, 5000);
    function stateFor(p) { const s = { t: 'state', game: H.gameId, you: { name: p.name, av: p.av, score: H.score(p) }, room: H.code };
      if (H._gate) s.gate = { label: H._gate.label, id: H._gate.id, mine: gateOK(p) };
      s.throwable = !H.game || !H.game.throwable || H.game.throwable(p);
      return H.game && H.game.stateFor ? Object.assign(s, H.game.stateFor(p) || {}) : Object.assign(s, { phase: 'lobby' }); }
    H.send = (p, m) => { if (net && p && !p.local) net.send(p.id, m); };
    H.broadcast = () => { H.players.forEach(p => { if (!p.local) H.send(p, stateFor(p)); }); };

    // ---- the crew on the ground plane: each character keeps its drawing; the games ask it to perform
    const tw = id => document.querySelector(`#toons .tw[data-id="${id}"]`);
    H.act = (id, cls, ms = 900) => { const t = tw(id), j = t && t.querySelector('.jump'); if (!j) return; j.classList.remove('hop', 'hit', 'cheer', 'catch', 'slump', 'bow', 'dance'); void j.offsetWidth; j.classList.add(cls); clearTimeout(j._t); j._t = setTimeout(() => j.classList.remove(cls), ms); };
    H.say = (id, text, ms = 1600) => { const t = tw(id); if (!t) return; t.querySelector('.bubble').textContent = text; t.classList.remove('say'); void t.offsetWidth; t.classList.add('say'); clearTimeout(t._s); t._s = setTimeout(() => t.classList.remove('say'), ms); };
    H.sign = {}; H.spot = null;
    function syncCrew() {
      const box = $('#toons'), ids = [...H.players.map(p => p.id), ...(H.game && H.game.house !== false ? ['house'] : [])], n = ids.length;
      box.style.setProperty('--tw', Math.max(40, Math.min(92, Math.floor((innerWidth - 40) / Math.max(1, n)) - 14)) + 'px');
      [...box.children].forEach(c => { if (!ids.includes(c.dataset.id)) c.remove(); });
      ids.forEach(id => { let t = tw(id); const p = H.P(id);
        if (!t) { t = document.createElement('div'); t.className = 'tw enter'; t.dataset.id = id; t.innerHTML = `<div class="bubble"></div><div class="sign"></div><div class="jump"><div class="rig">${toon(p ? p.av : 'house')}</div></div><div class="tag"></div>`; setTimeout(() => t.classList.remove('enter'), 1200);
          if (id === 'house') box.append(t); else { const h = tw('house'); h ? box.insertBefore(t, h) : box.append(t); } setTimeout(() => H.act(id, 'hop', 820), 900);
          if (id !== 'house') t.onclick = () => { const q = H.P(id); if (!q || q.local || q.conn) return; if (t.classList.contains('bye')) { H.removePlayer(id); return; } t.classList.add('bye'); t.querySelector('.bubble').textContent = 'tap again to remove'; t.classList.add('say'); setTimeout(() => { t.classList.remove('bye', 'say'); }, 2500); }; }
        t.querySelector('.tag').innerHTML = p ? `${esc(p.name)}${p.local ? ' · here' : ''}<b>${H.score(p)}</b>` : `the house<b>${H.houseScore || 0}</b>`;
        t.classList.toggle('air', H.spot === id);
        const sg = H.sign[id]; t.querySelector('.sign').textContent = sg || ''; t.classList.toggle('voted', !!sg);
        t.classList.toggle('off', !!(p && !p.local && !p.conn)); t.style.translate = p && p.x ? p.x + 'px 0' : ''; });
      const gb = $('#goneB'); if (gb) { const n = H.players.filter(p => !p.local && !p.conn).length; gb.hidden = !n; gb.textContent = 'clear gone (' + n + ')'; }
    }
    H.syncCrew = syncCrew;
    H.throwRemote = (fromId, toId) => { const a = tw(fromId), b = tw(toId); if (!a || !b) return; const r0 = a.getBoundingClientRect(), r1 = b.getBoundingClientRect();
      const el = document.createElement('div'); el.className = 'prop'; el.innerHTML = `<svg viewBox="0 0 26 40"><g filter="url(#boil)"><rect x="3" y="2" width="20" height="36" rx="6" fill="#3a3a44" stroke="#2a1f1a" stroke-width="2.5"/><circle cx="13" cy="10" r="3.5" fill="#c8553d"/><rect x="8" y="18" width="10" height="3" rx="1.5" fill="#d9a441"/><rect x="8" y="25" width="10" height="3" rx="1.5" fill="#d9a441"/></g></svg>`; document.body.append(el);
      const x0 = r0.left + r0.width / 2 - 13, y0 = r0.top + r0.height * .35, x1 = r1.left + r1.width / 2 - 13, y1 = r1.top + r1.height * .35, peak = Math.min(y0, y1) - 140;
      H.act(fromId, 'hit', 300);
      const an = el.animate([{ transform: `translate(${x0}px,${y0}px) rotate(0)` }, { transform: `translate(${(x0 + x1) / 2}px,${peak}px) rotate(380deg)`, offset: .5 }, { transform: `translate(${x1}px,${y1}px) rotate(720deg)` }], { duration: 900, easing: 'linear' });
      an.onfinish = () => { el.remove(); H.act(toId, 'catch', 520); H.say(toId, 'got it!', 1100); }; };
    function move(p, m) { const W = Math.max(60, innerWidth / 2 - 60);
      if (m === 'left' || m === 'right') { p.x = Math.max(-W, Math.min(W, (p.x || 0) + (m === 'left' ? -34 : 34))); syncCrew(); H.act(p.id, 'hit', 260); }
      if (m === 'jump') H.act(p.id, 'hop', 820); if (m === 'dance') H.act(p.id, 'dance', 1600); if (m === 'bow') H.act(p.id, 'bow', 1300);
      if (m === 'wave') { H.act(p.id, 'hit', 280); H.say(p.id, pick(['hi!', 'hello!', 'over here!', 'yoo-hoo'])); } }

    // ---- the crowd: what lands is counted against whatever the game says is on screen
    const crowdText = t => t && t.r ? THROWS.filter(w => t.r[w]).map(w => t.r[w] + ' ' + (w === 'cut' ? 'CUT!' : w === 'bravo' ? 'bravo' : w) + (t.r[w] > 1 && (w === 'tomato' || w === 'rose') ? (w === 'tomato' ? 'es' : 's') : '')).join(' · ') : '';
    H.crowdText = crowdText;
    H.crowdShow = (t) => { const box = $('#crowd'); box.innerHTML = t && t.r ? THROWS.filter(w => t.r[w]).map(w => `<span data-w="${w}">${ICON[w]}×${t.r[w]}</span>`).join('') : ''; };
    function fly(fromId, x1, y1, html, ms, done) { const a = tw(fromId); const r0 = a ? a.getBoundingClientRect() : { left: innerWidth / 2, top: innerHeight, width: 0, height: 0 };
      const el = document.createElement('div'); el.className = 'prop'; el.style.width = el.style.height = '34px'; el.innerHTML = html; document.body.append(el);
      const x0 = r0.left + r0.width / 2 - 17, y0 = r0.top + r0.height * .3, peak = Math.min(y0, y1) - 120 - rnd() * 60;
      const an = el.animate([{ transform: `translate(${x0}px,${y0}px) rotate(0) scale(1)` }, { transform: `translate(${(x0 + x1) / 2}px,${peak}px) rotate(${200 + rnd() * 200}deg) scale(1.25)`, offset: .5 }, { transform: `translate(${x1 - 17}px,${y1 - 17}px) rotate(560deg) scale(1.1)` }], { duration: ms, easing: 'linear' });
      an.onfinish = () => { el.remove(); done && done(); }; }
    const bump = w => { const s = document.querySelector(`#crowd span[data-w="${w}"]`); if (s) { s.classList.remove('bump'); void s.offsetWidth; s.classList.add('bump'); } };
    function throwFrom(p, w) {
      const now = performance.now(); if (p.lastThrow && now - p.lastThrow < 500) return; p.lastThrow = now;
      const t = H.game && H.game.crowdTarget ? H.game.crowdTarget() : null; if (t && t.by !== p.id) { t.r = t.r || {}; t.r[w] = (t.r[w] || 0) + 1; }
      p.threw = p.threw || {}; p.threw[w] = (p.threw[w] || 0) + 1;
      const scr = $('#screen').getBoundingClientRect(), perf = H.game && H.game.performer ? H.game.performer() : null, air = perf && perf !== p.id ? perf : null, show = () => { H.crowdShow(t); bump(w); };
      H.act(p.id, 'hit', 260);
      if (w === 'tomato') { const fx = .15 + rnd() * .7, fy = .15 + rnd() * .6; fly(p.id, scr.left + scr.width * fx, scr.top + scr.height * fy, ICON.tomato, 650, () => { const s = document.createElement('div'); s.className = 'splat'; s.style.left = fx * 100 + '%'; s.style.top = fy * 100 + '%'; s.innerHTML = ICON.splat; $('#splats').append(s); setTimeout(() => s.remove(), 3400); if (air) { H.act(air, 'hit', 280); if (rnd() < .5) H.say(air, pick(['hey!', 'rude!', 'it’s art!', 'philistines!'])); } show(); }); }
      if (w === 'rose') { const tgt = air && tw(air); if (tgt) { const r = tgt.getBoundingClientRect(); fly(p.id, r.left + r.width / 2, r.top + r.height * .55, ICON.rose, 700, () => { H.act(air, 'hop', 820); H.say(air, pick(['thank you!', 'for me?', 'merci!', 'oh stop'])); show(); }); }
        else { const fx = .2 + rnd() * .6, fy = .55 + rnd() * .3; fly(p.id, scr.left + scr.width * fx, scr.top + scr.height * fy, ICON.rose, 700, () => { const s = document.createElement('div'); s.className = 'sticker'; s.style.left = fx * 100 + '%'; s.style.top = fy * 100 + '%'; s.innerHTML = ICON.rose; $('#splats').append(s); setTimeout(() => s.remove(), 3000); show(); }); } }
      if (w === 'cut' || w === 'bravo') { const c = document.createElement('div'); c.className = 'placard ' + w; c.innerHTML = `${w === 'cut' ? 'CUT!' : 'Bravo!'}<small>${mini(p.av)} ${esc(p.name)}</small>`; c.style.left = (35 + rnd() * 30) + '%'; $('#splats').append(c); setTimeout(() => c.remove(), 1500);
        H.say(p.id, w === 'cut' ? 'CUT!' : 'bravo!', 1200); if (w === 'bravo') H.act(p.id, 'cheer', 1500); if (air) { H.act(air, w === 'cut' ? 'slump' : 'hop', w === 'cut' ? 1200 : 820); if (w === 'cut' && rnd() < .5) H.say(air, pick(['never!', 'I’m not done!', 'keep rolling!'])); } show(); }
    }
    // awards from what was thrown at whose work, and who did the throwing
    H.awards = (works) => { const got = {}; (works || []).forEach(t => { if (!t.r || !t.by) return; got[t.by] = got[t.by] || {}; THROWS.forEach(w => got[t.by][w] = (got[t.by][w] || 0) + (t.r[w] || 0)); });
      const best = (w, f) => { let id = null, n = 0; Object.entries(f).forEach(([k, v]) => { if ((v[w] || 0) > n) { n = v[w]; id = k; } }); return id ? { id, n } : null; };
      const threw = {}; H.players.forEach(p => threw[p.id] = p.threw || {});
      const out = [], A = (name, r, why) => { if (r && (r.id === 'house' || H.P(r.id))) out.push({ name, id: r.id, why: why(r.n) }); };
      A('the Golden Tomato', best('tomato', got), n => n + (n === 1 ? ' tomato' : ' tomatoes') + ' received'); A('the Bouquet', best('rose', got), n => n + (n === 1 ? ' rose' : ' roses') + ' received'); A('the Standing Ovation', best('bravo', got), n => n + (n === 1 ? ' bravo' : ' bravos'));
      A('the Heckler', best('cut', threw), n => 'shouted CUT! ' + (n === 1 ? 'once' : n + ' times')); A('the Tomato Arm', best('tomato', threw), n => n + (n === 1 ? ' tomato' : ' tomatoes') + ' thrown');
      return out; };
    H.awardsHTML = list => list.map(a => `<div class="rk" style="font-size:15px">${esc(a.name)}: ${a.id === 'house' ? mini('house') + ' the house' : mini(H.P(a.id).av) + ' ' + esc(H.P(a.id).name)} <span class="hint" style="margin:0 0 0 auto">${esc(a.why)}</span></div>`).join('');

    // ---- the lobby: the crew gathers; the stand picks a game
    function lobbyCard() { H.slate(card(`<div class="big">Party<small>${H.code ? 'room ' + H.code : ''}</small></div>`, 'dawn')); }
    function drawLobby() {
      let svg = ''; if (H.code && !H.wireNote && root.qrcode) { const q = qrcode(0, 'M'); q.addData(H.joinURL()); q.make(); svg = q.createSvgTag({ cellSize: 4, margin: 1, scalable: true }); }
      const ids = Object.keys(games).sort((a, b) => (b === H.wantPlay) - (a === H.wantPlay));
      const S = H.side(`<div class="ph">The crew <small>${H.players.length} joined · 12 at most</small></div>
        ${H.wireNote ? `<p class="hint" style="color:var(--verm)">${esc(H.wireNote)}</p>` : `<div class="lob"><div class="qr">${svg}</div><div style="min-width:0"><div class="hint" style="text-align:left;margin:0">scan to join · room</div><div class="code">${esc(H.code || '')}</div><div class="url">${esc(H.joinURL().replace(/^https?:\/\//, ''))}</div><div class="row" style="margin-top:6px"><input type="text" id="lname" maxlength="12" placeholder="add a player here"><button class="btn chip" id="ladd">+</button></div></div></div>`}
        ${H.wireNote ? `<div class="row" style="margin-top:6px"><input type="text" id="lname" maxlength="12" placeholder="add a player here"><button class="btn chip" id="ladd">+</button></div>` : ''}
        <div class="ph" style="margin-top:10px">Games</div>
        ${ids.map(id => { const g = games[id], o = H.opts[id] || {}; return `<div class="game"><div><b>${esc(g.title)}</b><span>${esc(g.blurb)}</span>${(g.options || []).map(op => `<div class="row" style="margin-top:3px"><span>${esc(op.name)}</span>${op.values.map(v => `<button class="btn chip ${(o[op.k] != null ? o[op.k] : op.def) === v ? 'on' : ''}" data-g="${id}" data-o="${op.k}" data-v="${v}">${v}</button>`).join('')}</div>`).join('')}</div><button class="btn cta" data-play="${id}" ${H.players.length ? '' : 'disabled'}>${H.players.length ? 'play ▸' : 'waiting…'}</button></div>`; }).join('')}`, 'lobby');
      const add = () => { const v = ($('#lname').value || '').trim().slice(0, 12); if (!v) return; H.addPlayer('L' + Date.now(), v, null, true); draw(); };
      const lb = $('#ladd'); if (lb) { lb.onclick = add; $('#lname').onkeydown = e => { if (e.key === 'Enter') add(); }; }
      S.querySelectorAll('[data-o]').forEach(b => b.onclick = () => { const o = H.opts[b.dataset.g] = H.opts[b.dataset.g] || {}; o[b.dataset.o] = isNaN(+b.dataset.v) ? b.dataset.v : +b.dataset.v; store.set('party.opts', H.opts); draw(); });
      S.querySelectorAll('[data-play]').forEach(b => b.onclick = () => play(b.dataset.play));
    }
    function play(id) { const g = games[id]; if (!g || !H.players.length) return;
      const nowT = performance.now(); H.players.filter(p => !p.local && !p.conn && (!p.back || nowT - p.seen > 120000)).forEach(p => H.removePlayer(p.id)); fullscreen(true); H.unlock();
      H.players.forEach(p => { p.score = 0; p.threw = {}; p.late = false; }); H.houseScore = 0; H.sign = {}; H.spot = null; H._gate = null; H.bug(''); H.crowdShow(null); $('#splats').innerHTML = '';
      H.gameId = id; $('#logo').textContent = g.title; $('#tagline').textContent = g.blurb; H.opt = Object.assign({}, ...(g.options || []).map(o => ({ [o.k]: o.def })), H.opts[id] || {});
      H.game = g.host(H) || {}; $('#lobbyB').hidden = false; draw(); }
    H.playGame = play;
    H.end = () => { if (H.game && H.game.stop) H.game.stop(); H.game = null; H.gameId = null; H._gate = null; H.spot = null; H.sign = {}; H.bug(''); H.crowdShow(null); H.cap('');
      $('#logo').textContent = 'Party'; $('#tagline').textContent = 'one room · every game · the archive’s films'; $('#lobbyB').hidden = true; [H.VP, H.AP].flat().forEach(m => m.pause()); lobbyCard(); draw(); };
    function draw() { $('#roomTag').textContent = H.code && !H.wireNote ? 'ROOM ' + H.code : ''; syncCrew(); if (!H.game) drawLobby(); else if (H.game.draw) H.game.draw(); H.broadcast(); }
    H.draw = draw;
    addEventListener('resize', () => syncCrew());
    const want = Q.get('play'); if (want && games[want]) H.wantPlay = want;
    openRoom(saved && saved.code); lobbyCard(); draw();
    return H;
  }

  // =====================================================================  THE PHONE: pick a character once; then your hand, your remote, your tomatoes
  function phone(games, ROOM) {
    const app = $('#app'); document.body.classList.add('is-phone');
    let pid = null; try { pid = sessionStorage.getItem('party.pid'); } catch (e) { }
    if (!pid) { pid = 'p' + Math.random().toString(36).slice(2, 9); try { sessionStorage.setItem('party.pid', pid); } catch (e) { } }
    let me = Object.assign({ name: '', av: Math.floor(rnd() * NK) }, store.get('party.me', {}));
    let S = null, net = null, joined = false, wire = 'connecting', lastMsg = 0, built = '', tab = 'me', lastPhaseKey = '', lastThrow = 0, heroes = {}, view = null;
    const thrown = { tomato: 0, rose: 0, cut: 0, bravo: 0 };
    const api = { send: m => net && net.send(m), buzz: (ms = 12) => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { } }, act: (el, cls, ms = 900) => { if (!el) return; el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); setTimeout(() => el.classList.remove(cls), ms); },
      rebuild: () => { built = ''; draw(); }, setTab: k => { tab = k; built = ''; draw(); }, esc, pad, UP, toon, mini, ICON, hero: (k, pose) => `<div class="hero"><div class="jump ${pose || ''}" id="heroJ"><div class="rig">${heroes[k] || (heroes[k] = toon(k))}</div></div></div>`, $ };
    function form() { built = '';
      app.innerHTML = `<div class="phone"><h1>Party</h1><div class="hint" style="font-size:16px">room ${esc(ROOM)} · join the crew</div>
        <div class="row" style="margin-top:8px"><input type="text" id="nm" maxlength="12" placeholder="Your name" value="${esc(me.name)}" autocomplete="off"></div>
        <div class="hint" style="text-align:left;margin-top:6px">Pick your character</div><div class="pick">${KINDS.map((_, k) => `<button data-a="${k}" class="${k === me.av ? 'on' : ''}" aria-label="${KINDS[k].n}">${toon(k, { still: true })}</button>`).join('')}</div>
        <button class="btn cta" id="jn">Join the crew</button></div>`;
      app.querySelectorAll('[data-a]').forEach(b => b.onclick = () => { me.av = +b.dataset.a; app.querySelectorAll('[data-a]').forEach(x => x.classList.toggle('on', x === b)); });
      $('#jn').onclick = () => { me.name = ($('#nm').value || '').trim().slice(0, 12) || 'Crew'; store.set('party.me', me); joined = true; try { sessionStorage.setItem('party.joined', ROOM); } catch (e) { } fullscreen(false); wake(); connect(); draw(); };
    }
    function connect() { if (net) return;
      net = Net.join(ROOM, pid, m => { lastMsg = performance.now(); if (m.t === 'state') { S = m; draw(); } if (m.t === 'full') { S = { phase: 'full' }; draw(); } if (m.t === 'who') api.send({ t: 'hello', name: me.name, av: me.av }); if (m.t && !/^(state|full|who|pong)$/.test(m.t)) { if (!(window.Ears && Ears.onHost(m)) && root.Party.onHost) root.Party.onHost(m); } },
        st => { wire = st === 'open' ? 'open' : st; if (st === 'open') { lastMsg = performance.now(); api.send({ t: 'hello', name: me.name, av: me.av }); } if (!S) draw(); });
      setInterval(() => { api.send({ t: 'ping' }); if (lastMsg && performance.now() - lastMsg > 12000) { lastMsg = performance.now(); net.restart(); } }, 4000);
      document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') api.send({ t: 'hello', name: me.name, av: me.av }); }); }
    api.S = () => S;
    // the built-in tabs every game can use
    const TABS = {
      throw: { name: 'Throw', render(el) { el.innerHTML = `<div class="throws">${THROWS.map(w => `<button class="btn th-${w}" data-w="${w}">${ICON[w]}<span>${w === 'cut' ? 'CUT!' : w === 'bravo' ? 'bravo!' : w}</span><span class="n" id="n-${w}">${thrown[w] ? thrown[w] + ' thrown' : ''}</span></button>`).join('')}</div>`;
        el.querySelectorAll('[data-w]').forEach(b => b.onclick = () => { const now = performance.now(); if (now - lastThrow < 600) return; lastThrow = now; const w = b.dataset.w; api.buzz(18); thrown[w]++; const n = $('#n-' + w); if (n) n.textContent = thrown[w] + ' thrown'; api.act(b, 'fly', 450); api.act(b, 'cool', 600); api.send({ t: 'throw', w }); }); } },
      me: { name: 'My character', render(el) { el.innerHTML = `<div class="center" style="flex:0 0 auto">${api.hero(S && S.you ? S.you.av : me.av)}</div><div class="pad"><button class="btn" data-m="left">◀ walk</button><button class="btn" data-m="jump">jump</button><button class="btn" data-m="right">walk ▶</button><button class="btn" data-m="wave">wave</button><button class="btn" data-m="dance">dance</button><button class="btn" data-m="bow">bow</button></div>`;
        el.querySelectorAll('[data-m]').forEach(b => { const go = () => { api.buzz(8); const m = b.dataset.m; api.send({ t: 'me', m }); const h = $('#heroJ'); if (m === 'jump') api.act(h, 'hop', 820); if (m === 'dance') api.act(h, 'dance', 1600); if (m === 'bow') api.act(h, 'bow', 1300); if (m === 'wave' || m === 'left' || m === 'right') api.act(h, 'hit', 300); };
          b.onclick = go; if (b.dataset.m === 'left' || b.dataset.m === 'right') { let iv = 0; b.onpointerdown = () => { iv = setInterval(go, 260); }; b.onpointerup = b.onpointerleave = () => clearInterval(iv); } });
        const h = $('#heroJ'); if (h) h.onclick = () => { api.buzz(); api.act(h, 'hop', 820); api.send({ t: 'me', m: 'jump' }); }; } } };
    function lobbyView() { return { key: 'lobby', status: 'Joined. Waiting for the stand to start a game.', tab: 'me', tabs: ['me', 'throw'] }; }
    function draw() {
      if (!joined) return form();
      if (!S) { built = ''; app.innerHTML = `<div class="phone"><div class="me">${mini(me.av)}${esc(me.name)}</div><div class="center">${api.hero(me.av)}<div class="say">Finding<br>the stand…</div><div class="sub">${wire === 'open' ? 'room ' + esc(ROOM) : wire === 'error' || wire === 'lost' ? 'the stand is not answering yet · still trying' : 'connecting'}</div></div></div>`; return; }
      if (S.phase === 'full') { built = ''; app.innerHTML = `<div class="phone"><div class="center"><div class="say">The crew<br>is full</div><div class="sub">twelve is the limit</div></div></div>`; return; }
      const mod = S.game && games[S.game]; view = (mod && mod.phone(S, api)) || lobbyView();
      const pk = (S.game || 'lobby') + '|' + (view.key || '');
      if (pk !== lastPhaseKey) { lastPhaseKey = pk; if (view.tab) tab = view.tab; }
      const tabs = (view.tabs || []).map(t => typeof t === 'string' ? Object.assign({ k: t }, TABS[t]) : t).filter(t => t.render && (t.k !== 'throw' || S.throwable !== false));
      if (!view.takeover && tabs.length && !tabs.some(t => t.k === tab)) tab = tabs[0].k;
      const g = S.gate && S.gate.mine ? S.gate : null;
      const key = pk + '|' + (view.takeover ? 'T' + view.takeover.key : 'tabs:' + tabs.map(t => t.k).join(',') + '|' + tab + '|' + ((tabs.find(t => t.k === tab) || {}).key || '')) + '|g:' + (g ? g.id : '');
      if (key === built) return patch(g);
      built = key;
      app.innerHTML = `<div class="phone ${view.cls || ''}"><div class="me">${mini(S.you.av)}${esc(S.you.name)}${S.noScore ? '' : `<b id="myScore">${S.you.score} ★</b>`}</div>${view.status != null ? `<div class="status" id="st">${view.status}</div>` : ''}
        ${g ? `<button class="btn gate" id="gateB">${esc(g.label)}</button>` : ''}
        ${view.takeover ? `<div class="pane" id="pane"></div>${view.throws && S.throwable !== false ? `<div class="tstrip">${THROWS.map(w => `<button class="th-${w}" data-w="${w}" aria-label="${w}">${ICON[w]}</button>`).join('')}</div>` : ''}` : `${tabs.length > 1 ? `<div class="tabs">${tabs.map(t => `<button class="btn ${tab === t.k ? 'on' : ''}" data-tab="${t.k}">${esc(t.name)}</button>`).join('')}</div>` : ''}<div class="pane" id="pane"></div>`}</div>`;
      if (g) $('#gateB').onclick = () => { api.buzz(20); api.send({ t: 'gate', id: g.id }); $('#gateB').disabled = true; };
      app.querySelectorAll('[data-tab]').forEach(b => b.onclick = () => api.setTab(b.dataset.tab));
      app.querySelectorAll('.tstrip [data-w]').forEach(b => b.onclick = () => { const now = performance.now(); if (now - lastThrow < 500) return; lastThrow = now; api.buzz(18); thrown[b.dataset.w]++; api.act(b, 'fly', 450); api.send({ t: 'throw', w: b.dataset.w }); });
      const pane = $('#pane'); if (view.takeover) view.takeover.render(pane, api); else { const t = tabs.find(t => t.k === tab); if (t) t.render(pane, api); }
    }
    function patch(g) { const st = $('#st'); if (st && view.status != null && st.innerHTML !== view.status) st.innerHTML = view.status; const sc = $('#myScore'); if (sc) sc.textContent = S.you.score + ' ★';
      const pane = $('#pane'); if (view.takeover && view.takeover.patch) view.takeover.patch(pane, api); else if (!view.takeover) { const t = (view.tabs || []).find(t => typeof t !== 'string' && t.k === tab); if (t && t.patch) t.patch(pane, api); } }
    let again = null; try { again = sessionStorage.getItem('party.joined'); } catch (e) { }
    if (again === ROOM && me.name) { joined = true; connect(); }
    draw();
  }

  function start(games) { const ROOM = (Q.get('room') || '').toUpperCase().replace(/[^A-Z0-9]/g, ''); return ROOM ? phone(games, ROOM) : host(games); }
  root.Party = { start, games: {}, toon, mini, ICON, THROWS, KINDS, card, esc, pad, UP, rnd, pick, shuffle, fullscreen, store, NET };
})(window);
