/* THE SHOW: a television show spoken into being by the room, a line at a time.
   One phone holds the microphone. Hold it and say a line; let go. The stand hears it (Whisper in the stand's browser, else nothing:
   the pictures still come) and the archive answers: a ground for the line (the shots that look like its words; each speaker keeps
   returning to their own world, so a conversation cuts between places the way a show cuts between people), and every phone is
   dealt a different hand of figures that SAM cut out of other films, music beds, and archival people saying the line's words.
   Phones place them by hand on the scene: drag up to place, drag to move, pinch to size, lower is nearer, double-tap to turn,
   drag off to throw away. Pass the microphone by tapping a face. The episode plays on the stand in the speakers' own voices,
   and the stand can keep it as one file that plays anywhere.
   Reuses: markov/shared.js (the archive and its CLIP vectors), markov/sam.json (the cast), markov/hear.js (the microphone and the
   listener), party/lexicon (words to pictures without a model), pictures/rushes.json (music), odyssey/transcripts.json (who said what). */
(function () {
  const { esc, rnd, pick, shuffle, mini, KINDS } = Party;
  const STOP = new Set('a an the and or of to in on at by for with from into onto over under is are was were be been it its this that these those as his her their our your my he she they we you i me him them us one two not no but so if then than there here what which who whom whose when where while out up down off about after before again all any both each few more most other some such only own same very can will just do does did has have had am also yet too nor like said say says get got going gone go went come came want know think yeah okay well really thing things'.split(' '));
  const stem = w => { for (const x of ['ing', 'ed', 'es', 's']) if (w.length > x.length + 3 && w.endsWith(x)) return w.slice(0, -x.length); return w; };
  const content = t => ((t || '').toLowerCase().match(/[a-z']+/g) || []).map(w => w.replace(/'/g, '')).filter(w => w.length > 2 && !STOP.has(w));
  const thumbOf = u => u ? u.replace('/clips/', '/thumbnails/').replace(/\.mp4.*$/, '.jpg') : '';
  const col = av => (KINDS[av] || KINDS[0]).c;
  // pictograms: no words on the phones
  const I = {
    mic: '<svg viewBox="0 0 40 40"><rect x="14" y="4" width="12" height="20" rx="6" fill="currentColor"/><path d="M9 18 Q9 30 20 30 Q31 30 31 18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M20 30 V36 M13 36 H27" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
    hand: '<svg viewBox="0 0 40 40"><path d="M12 22 V9 a2.5 2.5 0 0 1 5 0 V19 V6 a2.5 2.5 0 0 1 5 0 V19 V8 a2.5 2.5 0 0 1 5 0 V21 V13 a2.5 2.5 0 0 1 5 0 V25 Q32 37 21 37 Q14 37 10 31 L5 23 a2.6 2.6 0 0 1 4 -3Z" fill="currentColor"/></svg>',
    fig: '<svg viewBox="0 0 40 40"><circle cx="20" cy="9" r="5" fill="currentColor"/><path d="M12 36 L15 16 H25 L28 36 H23 L20 24 L17 36Z" fill="currentColor"/></svg>',
    ground: '<svg viewBox="0 0 40 40"><rect x="3" y="7" width="34" height="26" rx="3" fill="none" stroke="currentColor" stroke-width="3"/><path d="M6 30 L16 17 L23 25 L28 20 L35 30Z" fill="currentColor"/><circle cx="28" cy="13" r="3" fill="currentColor"/></svg>',
    music: '<svg viewBox="0 0 40 40"><path d="M15 29 V8 L33 4 V25" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="11" cy="29" r="5" fill="currentColor"/><circle cx="29" cy="25" r="5" fill="currentColor"/></svg>',
    mouth: '<svg viewBox="0 0 40 40"><path d="M4 20 Q20 6 36 20 Q20 34 4 20Z" fill="currentColor"/><path d="M8 20 Q20 25 32 20" stroke="#fff" stroke-width="2.5" fill="none"/></svg>',
    more: '<svg viewBox="0 0 40 40"><path d="M6 13 H24 L20 8 M24 13 L20 18" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M34 27 H16 L20 22 M16 27 L20 32" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    play: '<svg viewBox="0 0 40 40"><path d="M12 7 L33 20 L12 33Z" fill="currentColor"/></svg>',
    stop: '<svg viewBox="0 0 40 40"><rect x="10" y="10" width="20" height="20" rx="2" fill="currentColor"/></svg>',
    undo: '<svg viewBox="0 0 40 40"><path d="M15 9 L7 17 L15 25" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 17 H24 Q33 17 33 25 Q33 33 24 33 H17" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/></svg>',
    left: '<svg viewBox="0 0 40 40"><path d="M25 7 L12 20 L25 33" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    right: '<svg viewBox="0 0 40 40"><path d="M15 7 L28 20 L15 33" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    bin: '<svg viewBox="0 0 40 40"><path d="M9 11 H31 M16 11 V7 H24 V11 M12 11 L14 35 H26 L28 11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    ear: '<svg viewBox="0 0 40 40"><path d="M13 16 Q13 5 22 5 Q31 5 31 15 Q31 21 26 25 Q23 28 23 32 Q23 37 18 37 Q14 37 13 33" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round"/><path d="M19 17 Q19 11 23 11 Q26 11 26 15" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>'
  };
  const ribbon = (lv, c, n = 36) => { const L = lv && lv.length ? lv : []; const bars = Array.from({ length: n }, (_, i) => { const a = L.length ? L[Math.floor(i * L.length / n)] : 0; return Math.max(.08, Math.min(1, a * 2.4)); });
    return `<svg class="rib" viewBox="0 0 ${n * 4} 20" preserveAspectRatio="none">${bars.map((b, i) => `<rect x="${i * 4 + .6}" y="${(10 - b * 9.5).toFixed(1)}" width="2.8" height="${(b * 19).toFixed(1)}" rx="1.2" fill="${c}"/>`).join('')}</svg>`; };

  function host(H) {
    const $ = s => document.querySelector(s), P = H.P, ARC = window.SH;
    H.show(null); H.slate(''); H.cap('');
    let host$ = $('#showv'); if (!host$) { host$ = document.createElement('div'); host$.id = 'showv'; $('#vids').after(host$); } host$.hidden = false;
    const ST = ShowCore.Stage(host$), A = { voice: H.AP[0], bed: H.AP[1], echo: H.AP[2] };
    const G = { ready: false, mic: null, rec: null, hearing: 0, raised: new Set(), panels: [], playing: false, at: -1, ears: window.MPHear ? 'maybe' : 'none', why: 'waking the archive' };
    const hands = {}, home = {}, sel = {}, undo = []; let nid = 1, stopPlay = null, LIB = null, SAM = null, FE = null, X = null, XV = null, XI = null, R = null, TW = null, TR = null, EXT = '.webp';
    const players = () => H.players.filter(p => !p.house);
    // ---- the archive, the cast, the words: everything the stand needs to answer a line
    Promise.all([ARC.load({ light: true }), fetch('markov/sam.json').then(r => r.json()), fetch('markov/sam-emb.bin').then(r => r.arrayBuffer()), fetch('party/lexicon.json').then(r => r.json()), fetch('party/lexicon.bin').then(r => r.arrayBuffer()),
      fetch('pictures/rushes.json').then(r => r.json()), new Promise(r => { const i = new Image(); i.onload = () => r('.webp'); i.onerror = () => r('.png'); i.src = 'seg/' + '0046aa70-365f-5128-88eb-90cfe9e075e4/0.webp'; })])
      .then(([d, sj, sb, xj, xb, rj, ext]) => { LIB = d.LIB; SAM = sj; FE = new Int8Array(sb); X = xj; XV = new Int8Array(xb); XI = new Map(X.words.map((w, i) => [w, i])); R = rj; EXT = ext; G.ready = true; G.why = '';
        players().forEach(p => deal(p.id)); draw(); })
      .catch(e => { G.why = 'the archive did not load: ' + e.message; draw(); });
    fetch('odyssey/transcripts.json').then(r => r.json()).then(t => { TR = t; }).catch(() => { });
    if (window.MPHear && MPHear.prefetch) try { MPHear.prefetch(); } catch (e) { }
    // ---- words -> a vector in the archive's picture space: CLIP when the reader is here, the lexicon always
    async function vec(text) { const t = (text || '').trim(); if (!t) return null;
      if (ARC.ready && ARC.ready.reader && window.ClipText && ClipText.state === 'ready') { try { const [v] = await ARC.embed([t]); if (v) return Float32Array.from(v); } catch (e) { } }
      const ws = content(t).map(stem).filter(w => XI.has(w)); if (!ws.length) return null;
      const v = new Float32Array(X.dim); ws.forEach(w => { const i = XI.get(w), f = X.idf[i]; for (let j = 0; j < X.dim; j++) v[j] += XV[i * X.dim + j] * f; }); return v; }
    const ranked = (s, n, ok) => { const ix = []; for (let i = 0; i < s.length; i++) if (!ok || ok(i)) ix.push(i); ix.sort((a, b) => s[b] - s[a]); return ix.slice(0, n); };
    const figSims = v => { const n = SAM.figs.length, d = 512, o = new Float32Array(n); for (let i = 0; i < n; i++) { let a = 0, r = i * d; for (let j = 0; j < d; j++) a += v[j] * FE[r + j]; o[i] = a; } return o; };
    const isArc = k => LIB.shots[k].kind !== 'presence';
    const usedG = () => new Set(G.panels.map(p => p.g));
    // grounds for a line: what its words look like; a speaker's own world first, the way a show returns to each person's place
    function grounds(v, who) { const used = usedG(); let top;
      if (v) { const s = LIB.sims(v); top = ranked(s, 60, k => isArc(k) && !used.has(k)); const h = home[who]; if (h) top = top.map((k, r) => [k, r - (LIB.shots[k].src === h ? 10 : 0)]).sort((a, b) => a[1] - b[1]).map(x => x[0]); }
      else { const h = home[who], own = h ? (LIB.bySrc[h] || []).filter(k => !used.has(k)) : []; top = shuffle(own).concat(Array.from({ length: 40 }, () => Math.floor(rnd() * LIB.n)).filter(k => isArc(k) && !used.has(k))); }
      return [...new Set(top)].slice(0, 24); }
    const soft = (arr, T) => { let r = Math.random() * arr.reduce((a, _, i) => a + Math.exp(-i / T), 0); for (let i = 0; i < arr.length; i++) { r -= Math.exp(-i / T); if (r <= 0) return arr[i]; } return arr[0]; };
    function figCands(v) { if (!v) return shuffle(Array.from(SAM.figs.keys())).slice(0, 120); return ranked(figSims(v), 120); }
    // the archive's own people saying the line's words: [clip, t0, t1, words]
    function echoes(text) { if (!TR) return []; if (!TW) { TW = new Map(); for (const id in TR) { const w = TR[id].words; for (let i = 0; i < w.length; i++) { const k = stem(String(w[i][0]).toLowerCase().replace(/[^a-z]/g, '')); if (k.length < 4 || STOP.has(k)) continue; let l = TW.get(k); if (!l) TW.set(k, l = []); if (l.length < 30) l.push([id, i]); } } }
      const out = []; content(text).map(stem).forEach(k => (TW.get(k) || []).forEach(([id, i]) => { const w = TR[id].words, a = Math.max(0, i - 1), b = Math.min(w.length - 1, i + 2), t1 = w[b + 1] ? w[b + 1][1] : w[b][1] + .5;
        if (t1 - w[a][1] < 4) out.push({ c: id, t0: Math.max(0, w[a][1] - .05), t1: t1 + .05, x: w.slice(a, b + 1).map(x => x[0]).join(' ') }); }));
      return shuffle(out); }
    const musicUrl = m => R.r2 + R.P[m.v[0]] + '/clips/' + m.v[1] + '.mp4';
    // ---- a hand for each phone: different things in every hand, so the room has to build together
    function deal(id, kind) { if (!G.ready) return; const pan = panel(sel[id]) || G.panels[G.panels.length - 1], h = hands[id] = hands[id] || { figs: [], beds: [], echo: [], gr: [], page: 0 };
      const mine = players().findIndex(p => p.id === id), N = Math.max(1, players().length);
      if (!kind || kind === 'figs') { const c = pan ? pan.fc : figCands(null), off = (Math.max(0, mine) + (h.page || 0) * N) * 7 % Math.max(1, c.length - 8), seen = new Set(), out = [];
        for (const f of c.slice(off).concat(c.slice(0, off))) { const s = SAM.figs[f].shot; if (seen.has(s)) continue; seen.add(s); out.push(f); if (out.length >= 7) break; } h.figs = out; }
      if (!kind || kind === 'beds') h.beds = shuffle(R.music.map((_, i) => i)).slice(0, 3);
      if (!kind || kind === 'echo') { const e = pan ? (pan.ec || []) : []; h.echo = e.length ? shuffle(e).slice(0, 3) : []; }
      if (!kind || kind === 'gr') h.gr = pan ? pan.alts.filter(k => k !== pan.g).slice((h.page || 0) * 3 % 18, (h.page || 0) * 3 % 18 + 5) : []; }
    const panel = id => G.panels.find(p => p.id === id);
    // ---- a line arrives: a panel at once (the speaker's own world), then the words refine it when the listener has them
    async function line(p, m) {
      const id = nid++, url = m.a ? URL.createObjectURL(new Blob([m.a], { type: m.mime || 'audio/webm' })) : null;
      const pan = { id, who: p.id, text: '', dur: Math.max(.6, +m.dur || 0), url, lv: (m.lv || []).slice(0, 60), g: null, alts: [], figs: [], bed: null, echo: null, fc: figCands(null), ec: [], hearing: true };
      G.panels.push(pan); G.at = G.panels.length - 1; undo.push({ what: 'line', id }); answer(pan, null);
      H.act(p.id, 'hop', 820); players().forEach(q => { sel[q.id] = id; deal(q.id); }); show(pan); draw();
      if (url) { A.voice.src = url; A.voice.play().catch(() => { }); }
      let text = String(m.text || '').trim();
      if (!text && m.a && G.ears !== 'none') { G.hearing++; draw(); text = await hear(m.a).catch(() => ''); G.hearing--; }
      pan.hearing = false; if (text) { pan.text = text.slice(0, 200); H.say(p.id, pan.text.slice(0, 60), 3200); const v = await vec(text); if (v) { if (!pan.touched) answer(pan, v, true); pan.fc = figCands(v); } pan.ec = echoes(text); players().forEach(q => { if (sel[q.id] === id) deal(q.id); }); }
      show(panel(sel.__tv) || pan); draw(); }
    function answer(pan, v, refine) { const gs = grounds(v, pan.who); if (!gs.length) return; const g = refine ? gs[0] : soft(gs.slice(0, 12), 3); pan.g = g; pan.alts = gs; if (!home[pan.who] || v) home[pan.who] = LIB.shots[g].src; }
    async function hear(buf) { const AC = window.AudioContext || window.webkitAudioContext, OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext; const ac = new AC();
      try { const ab = await new Promise((ok, no) => { const r = ac.decodeAudioData(buf.slice(0), ok, no); if (r && r.catch) r.catch(no); }), d = ab.getChannelData(0);
        const off = new OAC(1, Math.max(1, Math.ceil(d.length * 16000 / ab.sampleRate)), 16000), b = off.createBuffer(1, d.length, ab.sampleRate); b.copyToChannel(d, 0); const s = off.createBufferSource(); s.buffer = b; s.connect(off.destination); s.start();
        const pcm = (await off.startRendering()).getChannelData(0).slice(); const r = await MPHear.words(pcm); G.ears = 'yes'; return (r && r.text || '').trim(); }
      catch (e) { if (/load|start|fetch|listener/i.test(e.message || '')) G.ears = 'none'; return ''; } finally { try { ac.close(); } catch (e) { } } }
    // ---- what a phone or the stand sees: a panel resolved into pictures and sounds
    const figOf = (g, by) => { const F = SAM.figs[g.f]; return { id: g.id, x: g.x, y: g.y, s: g.s, flip: g.flip, png: F.png.replace(/\.png$/, EXT), sp: F.sprite ? F.sprite.replace(/\.png$/, EXT) : '', sw: F.sw, sh: F.sh, fps: F.fps, w: F.w, h: F.h }; };
    function res(p) { const s = p.g != null ? LIB.shots[p.g] : null; return { text: p.text, dur: p.dur, g: s ? { v: s.video, th: thumbOf(s.video) } : null, figs: p.figs.map(g => figOf(g)), voice: p.url ? { u: p.url, dur: p.dur } : null,
      bed: p.bed ? { u: musicUrl(R.music[p.bed.k]), t0: Math.min(4, Math.max(0, (R.music[p.bed.k].d || 20) - 30)) } : null, echo: p.echo ? { u: TR[p.echo.c].video, t0: p.echo.t0, t1: p.echo.t1, x: p.echo.x } : null }; }
    function show(p) { if (G.playing) return; sel.__tv = p ? p.id : null; ST.show(p ? res(p) : null); H.cap(p ? p.text : ''); }
    // ---- everything a phone can do
    const clamp = (v, a, b) => Math.max(a, Math.min(b, +v || 0));
    function mark(p, pan, what) { pan.touched = true; undo.push({ what, id: pan.id, snap: JSON.stringify({ g: pan.g, figs: pan.figs, bed: pan.bed, echo: pan.echo }) }); if (undo.length > 80) undo.shift(); if (p) H.act(p.id, 'hit', 260); }
    function onMsg(p, m) { if (!p) return;
      if (m.t === 'say') { if (!G.ready) return; if (m.find) return find(p, m); if (G.mic && G.mic !== p.id && P(G.mic) && P(G.mic).conn) return; G.mic = p.id; G.rec = null; G.raised.delete(p.id); H.bug(''); line(p, m); return; }
      if (m.t === 'rec') { if (G.mic && G.mic !== p.id && P(G.mic) && P(G.mic).conn) return; G.mic = p.id; G.rec = m.on ? p.id : null; if (m.on) { stopIt(); H.act(p.id, 'hop', 820); } H.bug(m.on ? `<span class="onair">${mini(p.av)}${I.mic}</span>` : ''); draw(); return; }
      if (m.t === 'pass') { if (G.mic !== p.id && G.mic) return; const q = P(m.to); if (!q) return; G.mic = q.id; G.raised.delete(q.id); H.act(q.id, 'cheer', 1600); draw(); return; }
      if (m.t === 'raise') { if (G.raised.has(p.id)) G.raised.delete(p.id); else G.raised.add(p.id); H.act(p.id, 'hop', 820); draw(); return; }
      if (m.t === 'sel') { if (panel(m.pan)) { sel[p.id] = m.pan; deal(p.id); show(panel(m.pan)); H.broadcast(); } return; }
      if (m.t === 'more') { const h = hands[p.id]; if (h) { h.page = (h.page || 0) + 1; deal(p.id, m.kind); } H.send(p, stateFor(p)); return; }
      if (m.t === 'play') return playAll(m.from);
      if (m.t === 'stop') return stopIt();
      if (m.t === 'undo') return undoIt(p);
      const pan = panel(m.pan); if (!pan) return;
      if (m.t === 'place') { const h = hands[p.id]; if (!h || !h.figs.includes(m.f) || pan.figs.length >= 14) return; mark(p, pan, 'figure'); const F = SAM.figs[m.f];
        pan.figs.push({ id: nid++, f: m.f, x: clamp(m.x, 0, 1), y: clamp(m.y, 0, 1), s: clamp(m.s || Math.min(.42, Math.max(.14, F.box[2] * .7)), .04, 1.6), flip: 0, by: p.id }); }
      else if (m.t === 'move') { const g = pan.figs.find(g => g.id === m.id); if (!g) return; if (m.first) mark(p, pan, 'move'); g.x = clamp(m.x, -.1, 1.1); g.y = clamp(m.y, -.1, 1.1); if (m.s) g.s = clamp(m.s, .04, 1.6); if (m.flip != null) g.flip = m.flip ? 1 : 0; g.by = p.id;
        if (sel.__tv === pan.id && !G.playing) ST.dress(res(pan).figs); if (!m.end) return; }
      else if (m.t === 'del') { const i = pan.figs.findIndex(g => g.id === m.id); if (i < 0) return; mark(p, pan, 'remove'); pan.figs.splice(i, 1); }
      else if (m.t === 'ground') { if (!LIB.shots[m.k]) return; mark(p, pan, 'ground'); pan.g = m.k; home[pan.who] = LIB.shots[m.k].src; }
      else if (m.t === 'bed') { if (!R.music[m.k]) return; mark(p, pan, 'music'); pan.bed = { k: m.k, by: p.id }; }
      else if (m.t === 'unbed') { mark(p, pan, 'music'); pan.bed = null; }
      else if (m.t === 'echo') { const e = (pan.ec || []).find(e => e.c === m.c && Math.abs(e.t0 - m.t0) < .01); if (!e) return; mark(p, pan, 'echo'); pan.echo = { ...e, by: p.id }; }
      else if (m.t === 'unecho') { mark(p, pan, 'echo'); pan.echo = null; }
      else if (m.t === 'shift') { const i = G.panels.indexOf(pan), j = i + (m.d > 0 ? 1 : -1); if (j < 0 || j >= G.panels.length) return; undo.push({ what: 'order', order: G.panels.map(x => x.id) }); G.panels.splice(i, 1); G.panels.splice(j, 0, pan); H.act(p.id, 'hit', 260); }
      else if (m.t === 'drop') { undo.push({ what: 'order', order: G.panels.map(x => x.id), gone: pan }); G.panels = G.panels.filter(x => x !== pan); players().forEach(q => { if (sel[q.id] === pan.id) sel[q.id] = (G.panels[G.panels.length - 1] || {}).id; }); H.act(p.id, 'hit', 260); }
      else return;
      if (sel.__tv === pan.id || m.t === 'drop') show(panel(sel.__tv) || G.panels[G.panels.length - 1]); draw(); }
    async function find(p, m) { let text = String(m.text || '').trim(); if (!text && m.a && G.ears !== 'none') { G.hearing++; draw(); text = await hear(m.a).catch(() => ''); G.hearing--; }
      const h = hands[p.id]; if (!h) return; const v = await vec(text); if (v) { h.figs = []; const seen = new Set(); for (const f of ranked(figSims(v), 40)) { if (seen.has(SAM.figs[f].shot)) continue; seen.add(SAM.figs[f].shot); h.figs.push(f); if (h.figs.length >= 7) break; }
        const pan = panel(sel[p.id]); if (pan) { const gs = ranked(LIB.sims(v), 8, isArc); h.gr = gs; pan.alts = [...new Set([...gs, ...pan.alts])].slice(0, 30); } }
      else { h.page = (h.page || 0) + 1; deal(p.id, 'figs'); }
      h.heard = text ? text.slice(0, 40) : ''; draw(); }
    function undoIt(p) { const u = undo.pop(); if (!u) return; H.act(p.id, 'hit', 260);
      if (u.what === 'line') { G.panels = G.panels.filter(x => x.id !== u.id); }
      else if (u.what === 'order') { if (u.gone && !G.panels.includes(u.gone)) G.panels.push(u.gone); const pos = new Map(u.order.map((id, i) => [id, i])); G.panels.sort((a, b) => (pos.get(a.id) ?? 1e9) - (pos.get(b.id) ?? 1e9)); }
      else { const pan = panel(u.id); if (pan) Object.assign(pan, JSON.parse(u.snap)); }
      show(panel(sel.__tv) || G.panels[G.panels.length - 1]); draw(); }
    // ---- the episode
    function playAll(from) { if (!G.panels.length) return; stopIt(); G.playing = true; G.at = 0; H.cap('');
      stopPlay = ShowCore.play({ panels: G.panels.map(res) }, ST, A, { from: Math.max(0, G.panels.findIndex(p => p.id === from)), onPanel: i => { G.at = i; const p = G.panels[i]; if (p) H.act(p.who, 'hop', 820); drawSide(); H.broadcast(); }, onCap: t => H.cap(t), onEnd: () => { G.playing = false; stopPlay = null; show(G.panels[G.panels.length - 1]); draw(); } }); draw(); }
    function stopIt() { if (stopPlay) { const s = stopPlay; stopPlay = null; s(); } if (G.playing) { G.playing = false; show(panel(sel.__tv) || G.panels[G.panels.length - 1]); draw(); } }
    // keep: one html file with the voices inside it; pictures and music still come from the archive
    async function keep() { const toData = u => fetch(u).then(r => r.blob()).then(b => new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.readAsDataURL(b); }));
      const abs = u => new URL(u, location.href).href, E = { title: 'A show', made: new Date().toISOString().slice(0, 10), crew: players().map(p => p.name), panels: [] };
      for (const p of G.panels) { const r = res(p); if (r.voice) r.voice.u = await toData(r.voice.u).catch(() => ''); r.figs.forEach(g => { g.png = abs(g.png); if (g.sp) g.sp = abs(g.sp); }); E.panels.push(r); }
      const core = await fetch('party/show-core.js').then(r => r.text()), css = SHOW_CSS;
      const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(E.title)}</title><style>${css}
html,body{margin:0;height:100%;background:#0c0c0c;color:#f4ecd8;font:17px/1.3 Georgia,serif}.w{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:12px;box-sizing:border-box}
#scr{position:relative;width:min(100%,calc((100dvh - 90px)*16/9));aspect-ratio:16/9;background:#000;overflow:hidden;container-type:size}#cap{position:absolute;left:0;right:0;bottom:0;padding:4cqh 6% 2.5cqh;text-align:center;font-size:5.5cqh;text-shadow:0 2px 0 #000;z-index:90}#cap:empty{display:none}
button{font:inherit;background:#c8553d;color:#fff;border:0;border-radius:20px;padding:6px 18px;cursor:pointer}small{color:#999}</style></head><body><div class="w"><div id="scr"><div id="st"></div><div id="cap"></div></div><div><button id="go">play</button> <small>${esc(E.crew.join(' · '))} · ${E.made} · pictures from the Moving Image Archive</small></div></div>
<script>${core}<\/script><script>const E=${JSON.stringify(E).replace(/</g, '\\u003c')};const st=ShowCore.Stage(document.getElementById('st'));const A={voice:new Audio(),bed:new Audio(),echo:new Audio()};st.show(E.panels[0]);let stop=null;
document.getElementById('go').onclick=()=>{if(stop){stop();stop=null;return;}stop=ShowCore.play(E,st,A,{onCap:t=>document.getElementById('cap').textContent=t,onEnd:()=>{stop=null;}});};<\/script></body></html>`;
      const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([html], { type: 'text/html' })); a.download = 'the-show-' + E.made + '.html'; a.click(); G.kept = true; draw(); }
    // ---- the stand's sheet
    function drawSide() { const mic = P(G.mic);
      const tiles = G.panels.map((p, i) => { const q = P(p.who), s = p.g != null ? LIB.shots[p.g] : null; return `<div class="stile ${i === G.at && G.playing ? 'now' : ''} ${sel.__tv === p.id && !G.playing ? 'cur' : ''}">
        <span class="n">${i + 1}</span><img src="${s ? esc(thumbOf(s.video)) : ''}" alt=""><span class="who">${q ? mini(q.av) : ''}</span><span class="tx">${p.hearing ? '<i>…</i>' : esc(p.text || '')}${ribbon(p.lv, q ? col(q.av) : '#999', 28)}</span><span class="ic">${p.figs.length ? p.figs.length + I.fig : ''}${p.bed ? I.music : ''}${p.echo ? I.mouth : ''}</span></div>`; }).join('');
      const S2 = H.side(`<div class="ph">The Show <small>${G.panels.length} lines${G.hearing ? ' · listening' : ''}</small></div>
        <div class="row" style="margin-bottom:6px"><button class="btn chip" id="sPlay" ${G.panels.length ? '' : 'disabled'}>${G.playing ? '■ stop' : '▶ play the show'}</button><button class="btn chip" id="sKeep" ${G.panels.length ? '' : 'disabled'}>${G.kept ? 'kept ✓' : 'keep'}</button><button class="btn chip" id="sLobby">lobby</button></div>
        ${G.ready ? '' : `<div class="hint">${esc(G.why)}</div>`}
        <div class="stiles">${tiles || `<div class="hint" style="text-align:left">${mic ? esc(mic.name) + ' has the microphone.' : 'Whoever presses the microphone first has it.'} Hold it, say a line, let go.</div>`}</div>`, 'show');
      $('#sPlay').onclick = () => G.playing ? stopIt() : playAll(); $('#sKeep').onclick = () => keep().catch(e => H.logLine('could not keep it: ' + esc(e.message))); $('#sLobby').onclick = () => H.end(); }
    function draw() { drawSide(); H.syncCrew(); H.broadcast(); if (!G.panels.length && !G.playing) H.slate(H.card(`<div class="big">The Show<small>${G.ready ? (P(G.mic) ? esc(P(G.mic).name) + ' has the microphone' : 'hold the microphone and say a line') : esc(G.why)}</small></div>`, 'night')); else H.slate(''); }
    function stateFor(p) { if (G.ready && !hands[p.id]) deal(p.id); const h = hands[p.id] || {}, cur = panel(sel[p.id]) || G.panels[G.panels.length - 1];
      const pk = (k) => { const s = LIB.shots[k]; return { k, th: thumbOf(s.video) }; };
      return { phase: 'show', noScore: true, me: p.id, ready: G.ready, mic: G.mic, rec: G.rec, hearing: G.hearing, raised: [...G.raised], playing: G.playing, at: G.at, sel: cur ? cur.id : null,
        crew: players().map(q => ({ id: q.id, av: q.av, name: q.name, c: col(q.av), on: q.conn !== false })),
        panels: G.panels.map(x => { const s = x.g != null ? LIB.shots[x.g] : null, q = P(x.who); return { id: x.id, who: x.who, av: q ? q.av : 0, c: q ? col(q.av) : '#999', th: s ? thumbOf(s.video) : '', text: x.text, hearing: !!x.hearing, lv: x.lv.length > 36 ? x.lv.filter((_, i) => i % Math.ceil(x.lv.length / 36) === 0) : x.lv,
          figs: x.figs.map(g => ({ id: g.id, x: g.x, y: g.y, s: g.s, flip: g.flip, png: SAM.figs[g.f].png.replace(/\.png$/, EXT), ar: SAM.figs[g.f].w / SAM.figs[g.f].h, c: P(g.by) ? col(P(g.by).av) : '#999' })),
          bed: x.bed ? { th: thumbOf(musicUrl(R.music[x.bed.k])), c: P(x.bed.by) ? col(P(x.bed.by).av) : '#999' } : null, echo: x.echo ? { th: TR[x.echo.c].thumb, c: P(x.echo.by) ? col(P(x.echo.by).av) : '#999' } : null }; }),
        hand: G.ready ? { figs: (h.figs || []).map(f => ({ f, png: SAM.figs[f].png.replace(/\.png$/, EXT), ar: SAM.figs[f].w / SAM.figs[f].h })), beds: (h.beds || []).map(k => ({ k, th: thumbOf(musicUrl(R.music[k])), u: musicUrl(R.music[k]), t0: Math.min(4, Math.max(0, (R.music[k].d || 20) - 30)) })),
          echo: (h.echo || []).map(e => ({ c: e.c, t0: e.t0, t1: e.t1, th: TR[e.c].thumb, u: TR[e.c].video })), gr: (h.gr || []).map(pk), heard: h.heard || '' } : null }; }
    G.mic = null; draw();
    return { stateFor, draw, onMsg, crowdTarget: () => G.mic, performer: () => G.mic, throwable: false, onJoin: p => { deal(p.id); draw(); },
      stop() { stopIt(); ST.stop(); host$.hidden = true; host$.innerHTML = ''; H.cap(''); [A.voice, A.bed, A.echo].forEach(a => { try { a.pause(); } catch (e) { } }); } };
  }

  // ======================================================================= the phone: a hand, a scene, a microphone
  const L = { tab: 'figs', drag: null, rec: null, lv: [], sending: false, prev: null, pts: new Map(), last: 0, lastTap: 0, flash: '' };
  function phone(S, api) {
    if (S.phase !== 'show') return null;
    L.S = S;
    const me = S.me, cur = (S.panels || []).find(p => p.id === S.sel), holder = S.mic, mine = !holder || holder === me || !(S.crew.find(c => c.id === holder) || {}).on;
    const take = {
      key: 'show',
      render(el) { el.innerHTML = `<div class="sh"><div class="shl"><div class="hstage" id="hStage"><img class="hg" alt=""><div class="hfigs"></div><div class="hsnd"></div><div class="hbin">${I.bin}</div><div class="hempty">${I.mic}</div></div>
          <div class="hrib" id="hRib"></div><div class="hstrip" id="hStrip"></div></div>
          <div class="shr"><div class="hmic" id="hMic"></div><div class="htabs" id="hTabs">${['figs', 'gr', 'beds', 'echo'].map(k => `<button data-tab2="${k}" aria-label="${k}">${{ figs: I.fig, gr: I.ground, beds: I.music, echo: I.mouth }[k]}</button>`).join('')}</div><div class="htray" id="hTray"></div></div></div><div class="ghost" id="hGhost" hidden></div>`;
        el.querySelectorAll('[data-tab2]').forEach(b => b.onclick = () => { L.tab = b.dataset.tab2; api.buzz(6); L.take.patch(el, api, true); });
        wireStage(el, api); take.patch(el, api, true); },
      patch(el, api, force) { const H = S.hand;
        // the microphone, or a raised hand and the face that has it
        const m = el.querySelector('#hMic'), mk = [mine, holder, (S.raised || []).join(), S.crew.map(c => c.id + c.on).join(), S.hearing, S.ready].join('|');
        if (!L.rec && !L.sending && (force || m.dataset.k !== mk)) { m.dataset.k = mk;
          if (mine) m.innerHTML = `<button class="bigmic ${L.rec ? 'on' : ''} ${L.sending ? 'busy' : ''}" id="hTalk" aria-label="hold and speak">${I.mic}<i id="hLv"></i></button>
            <div class="faces">${S.crew.filter(c => c.id !== me).map(c => `<button data-pass="${c.id}" class="${(S.raised || []).includes(c.id) ? 'up' : ''}" style="--c:${c.c}" aria-label="${esc(c.name)}">${mini(c.av)}${(S.raised || []).includes(c.id) ? `<b>${I.hand}</b>` : ''}</button>`).join('')}</div>`;
          else { const h = S.crew.find(c => c.id === holder) || {}; m.innerHTML = `<div class="holder" style="--c:${h.c}">${mini(h.av || 0)}<span class="${S.rec === holder ? 'live' : ''}">${I.mic}</span></div><button class="raise ${(S.raised || []).includes(me) ? 'on' : ''}" id="hRaise" aria-label="raise your hand">${I.hand}</button>`; }
          const t = m.querySelector('#hTalk'); if (t) wireTalk(t, api, false);
          m.querySelectorAll('[data-pass]').forEach(b => b.onclick = () => { api.buzz(14); api.send({ t: 'pass', to: b.dataset.pass }); });
          const r = m.querySelector('#hRaise'); if (r) r.onclick = () => { api.buzz(10); api.send({ t: 'raise' }); }; }
        el.querySelectorAll('[data-tab2]').forEach(b => b.classList.toggle('on', b.dataset.tab2 === L.tab));
        // the hand
        const tr = el.querySelector('#hTray'), tk = JSON.stringify([L.tab, H, S.sel]);
        if (!L.rec && !(L.drag && !L.drag.stage) && (force || tr.dataset.k !== tk)) { tr.dataset.k = tk;
          if (!H) tr.innerHTML = `<div class="wait">${I.ear}</div>`;
          else if (L.tab === 'figs') tr.innerHTML = H.figs.map(f => `<button class="it fig" data-f="${f.f}" data-png="${esc(f.png)}" data-ar="${f.ar}"><img src="${esc(f.png)}" alt="" draggable="false"></button>`).join('') + `<button class="it more" data-more="figs" aria-label="more">${I.more}</button><button class="it ask" id="hAsk" aria-label="say what you want">${I.mic}</button>`;
          else if (L.tab === 'gr') tr.innerHTML = H.gr.map(g => `<button class="it gr" data-k="${g.k}"><img src="${esc(g.th)}" alt="" draggable="false"></button>`).join('') + `<button class="it more" data-more="gr" aria-label="more">${I.more}</button>`;
          else if (L.tab === 'beds') tr.innerHTML = H.beds.map(b => `<button class="it disc bed" data-k="${b.k}" data-u="${esc(b.u)}" data-t0="${b.t0}"><img src="${esc(b.th)}" alt="" draggable="false"><b>${I.music}</b></button>`).join('') + `<button class="it more" data-more="beds" aria-label="more">${I.more}</button>`;
          else tr.innerHTML = H.echo.length ? H.echo.map(e => `<button class="it disc echo" data-c="${e.c}" data-t0="${e.t0}" data-t1="${e.t1}" data-u="${esc(e.u)}"><img src="${esc(e.th)}" alt="" draggable="false"><b>${I.mouth}</b></button>`).join('') : `<div class="wait">${I.mouth}</div>`;
          wireTray(tr, api); const ask = tr.querySelector('#hAsk'); if (ask) wireTalk(ask, api, true); }
        // the scene
        const st = el.querySelector('#hStage'); st.classList.toggle('empty', !cur); const im = st.querySelector('.hg'); const th = cur ? cur.th : ''; if (im.dataset.u !== th) { im.dataset.u = th; im.src = th || 'data:,'; }
        const fl = st.querySelector('.hfigs'), have = new Map([...fl.children].map(d => [d.dataset.id, d])), keep = new Set();
        (cur ? cur.figs : []).forEach(g => { const id = String(g.id); keep.add(id); let d = have.get(id); if (!d) { d = document.createElement('div'); d.className = 'hf'; d.dataset.id = id; d.innerHTML = `<img src="${esc(g.png)}" alt="" draggable="false">`; fl.append(d); }
          if (L.drag && L.drag.id === g.id) return; d.style.left = g.x * 100 + '%'; d.style.top = g.y * 100 + '%'; d.style.width = g.s * 100 + '%'; d.style.zIndex = 10 + Math.round(g.y * 100); d.style.setProperty('--c', g.c); d.classList.toggle('flip', !!g.flip); });
        have.forEach((d, id) => { if (!keep.has(id) && !(L.drag && String(L.drag.id) === id)) d.remove(); });
        const sn = st.querySelector('.hsnd'), sk = JSON.stringify(cur ? [cur.bed, cur.echo] : 0); if (sn.dataset.k !== sk) { sn.dataset.k = sk; sn.innerHTML = cur ? (cur.bed ? `<button class="disc on" data-un="bed" style="--c:${cur.bed.c}"><img src="${esc(cur.bed.th)}" alt=""><b>${I.music}</b></button>` : '') + (cur.echo ? `<button class="disc on" data-un="echo" style="--c:${cur.echo.c}"><img src="${esc(cur.echo.th)}" alt=""><b>${I.mouth}</b></button>` : '') : '';
          sn.querySelectorAll('[data-un]').forEach(b => b.onclick = () => { api.buzz(10); api.send({ t: 'un' + b.dataset.un, pan: S.sel }); }); }
        // the speaker's voice, as a ribbon in their colour
        const rb = el.querySelector('#hRib'), rk = cur ? cur.id + '|' + cur.hearing + '|' + cur.lv.length : ''; if (rb.dataset.k !== rk) { rb.dataset.k = rk; rb.innerHTML = cur ? `${mini(cur.av)}${ribbon(cur.lv, cur.c)}${cur.hearing ? `<span class="dots">${I.ear}</span>` : ''}` : ''; }
        // the show so far
        const sp = el.querySelector('#hStrip'), sk2 = JSON.stringify([S.panels.map(p => [p.id, p.th, p.c, p.figs.length, !!p.bed, !!p.echo]), S.sel, S.playing, S.at]);
        if (sp.dataset.k !== sk2) { sp.dataset.k = sk2;
          sp.innerHTML = `<button class="pl" id="hPlay" aria-label="play">${S.playing ? I.stop : I.play}</button>` + S.panels.map((p, i) => `<button class="tl ${p.id === S.sel ? 'cur' : ''} ${S.playing && S.at === i ? 'now' : ''}" data-pan="${p.id}" style="--c:${p.c}"><img src="${esc(p.th)}" alt=""><i></i></button>`).join('')
            + (cur ? `<span class="ops"><button data-op="shift" data-d="-1" aria-label="earlier">${I.left}</button><button data-op="shift" data-d="1" aria-label="later">${I.right}</button><button data-op="drop" aria-label="remove">${I.bin}</button><button data-op="undo" aria-label="undo">${I.undo}</button></span>` : '');
          sp.querySelector('#hPlay').onclick = () => { api.buzz(12); api.send(S.playing ? { t: 'stop' } : { t: 'play' }); };
          sp.querySelectorAll('[data-pan]').forEach(b => b.onclick = () => { api.buzz(6); api.send({ t: 'sel', pan: +b.dataset.pan }); });
          sp.querySelectorAll('[data-op]').forEach(b => b.onclick = () => { api.buzz(10); const o = b.dataset.op; api.send(o === 'undo' ? { t: 'undo' } : { t: o, pan: S.sel, d: +b.dataset.d || 0 }); });
          const c = sp.querySelector('.tl.cur'); if (c) c.scrollIntoView({ inline: 'center', block: 'nearest' }); } }
    };
    // ---- hold to speak; let go to send. ask: a word to find figures, not a line of the show
    function wireTalk(b, api, ask) {
      const start = e => { e.preventDefault(); if (L.rec || L.sending) return; api.buzz(16);
        if (!window.MPHear || !navigator.mediaDevices) { L.flash = 'nomic'; if (!ask) api.send({ t: 'say', dur: 2, lv: [], text: window.__sayText || '' }); return; }
        L.lv = []; const lvEl = () => document.getElementById('hLv');
        try { L.rec = MPHear.take({ onLevel: v => { L.lv.push(+v.toFixed(3)); const i = lvEl(); if (i) i.style.transform = `scale(${1 + Math.min(1, v * 3)})`; } }); } catch (x) { L.rec = null; return; }
        const mine = L.rec; try { b.setPointerCapture(e.pointerId); } catch (x) { } b.classList.add('on'); if (!ask) api.send({ t: 'rec', on: 1 });
        mine.catch(() => { if (L.rec !== mine) return; L.rec = null; b.classList.remove('on'); if (!ask) { api.send({ t: 'rec', on: 0 }); api.send({ t: 'say', dur: 2, lv: [], text: window.__sayText || '' }); } }); };
      const end = async e => { if (!L.rec) return; e.preventDefault(); const pr = L.rec; L.rec = null; b.classList.remove('on'); L.sending = true; api.buzz(10);
        try { const t = await pr, r = await t.stop(); let a = r.blob && r.blob.size > 800 ? await r.blob.arrayBuffer() : (r.pcm ? wav(r.pcm) : null), mime = r.blob && r.blob.size > 800 ? r.blob.type : 'audio/wav';
          const n = L.lv.length, lv = n > 60 ? Array.from({ length: 60 }, (_, i) => Math.max(...L.lv.slice(Math.floor(i * n / 60), Math.floor((i + 1) * n / 60) || 1))) : L.lv;
          api.send({ t: 'say', find: ask ? 1 : 0, a, mime, dur: r.seconds, lv, text: window.__sayText || '' }); }
        catch (x) { if (!ask) api.send({ t: 'say', dur: 2, lv: [], text: window.__sayText || '' }); }
        L.sending = false; if (L.take) L.take.patch(document.getElementById('pane'), api, true); };
      b.addEventListener('pointerdown', start); b.addEventListener('pointerup', end); b.addEventListener('pointercancel', end); b.oncontextmenu = e => e.preventDefault(); }
    function wav(pcm) { const n = pcm.length, b = new ArrayBuffer(44 + n * 2), v = new DataView(b), w = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
      w(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); w(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, 16000, true); v.setUint32(28, 32000, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, n * 2, true);
      for (let i = 0; i < n; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, pcm[i])) * 32767, true); return b; }
    // ---- the hand to the scene: press a thing in the hand and carry it up; let go on the scene to put it there
    function wireTray(tr, api) {
      tr.querySelectorAll('[data-more]').forEach(b => b.onclick = () => { api.buzz(8); api.send({ t: 'more', kind: b.dataset.more }); });
      tr.querySelectorAll('.it.gr').forEach(b => b.onclick = () => { api.buzz(10); api.send({ t: 'ground', pan: L.S.sel, k: +b.dataset.k }); });
      tr.querySelectorAll('.it.fig, .it.disc').forEach(b => { b.onpointerdown = e => { if (!L.S.sel) return; e.preventDefault(); const gh = document.getElementById('hGhost'); const r = b.getBoundingClientRect();
        L.drag = { from: b, kind: b.classList.contains('fig') ? 'fig' : b.classList.contains('bed') ? 'bed' : 'echo', x0: e.clientX, y0: e.clientY, moved: false, pid: e.pointerId };
        gh.innerHTML = b.innerHTML; gh.style.width = r.width + 'px'; gh.style.left = e.clientX + 'px'; gh.style.top = e.clientY + 'px'; gh.className = 'ghost ' + L.drag.kind; try { b.setPointerCapture(e.pointerId); } catch (x) { } };
        b.onpointermove = e => { const d = L.drag; if (!d || d.from !== b) return; if (Math.hypot(e.clientX - d.x0, e.clientY - d.y0) > 8 && !d.moved) { d.moved = true; document.getElementById('hGhost').hidden = false; }
          const gh = document.getElementById('hGhost'); gh.style.left = e.clientX + 'px'; gh.style.top = e.clientY + 'px'; gh.classList.toggle('over', !!onStage(e)); };
        const up = e => { const d = L.drag; if (!d || d.from !== b) return; L.drag = null; document.getElementById('hGhost').hidden = true; const at = onStage(e);
          if (!d.moved) { if (d.kind === 'fig') { api.buzz(12); api.send({ t: 'place', pan: L.S.sel, f: +b.dataset.f, x: .3 + Math.random() * .4, y: .55 + Math.random() * .2 }); } else hearDisc(b); return; }
          if (!at) return; api.buzz(16);
          if (d.kind === 'fig') api.send({ t: 'place', pan: L.S.sel, f: +b.dataset.f, x: at.x, y: at.y });
          else if (d.kind === 'bed') api.send({ t: 'bed', pan: L.S.sel, k: +b.dataset.k });
          else api.send({ t: 'echo', pan: L.S.sel, c: b.dataset.c, t0: +b.dataset.t0 }); };
        b.onpointerup = up; b.onpointercancel = up; b.oncontextmenu = e => e.preventDefault(); }); }
    function hearDisc(b) { const a = L.prev || (L.prev = new Audio()); if (a.dataset.b === b.dataset.u + b.dataset.t0 && !a.paused) { a.pause(); return; } a.dataset.b = b.dataset.u + b.dataset.t0; a.src = b.dataset.u;
      const t0 = +b.dataset.t0 || 0, t1 = +b.dataset.t1 || t0 + 8; a.addEventListener('loadedmetadata', () => { try { a.currentTime = t0; } catch (e) { } a.play().catch(() => { }); }, { once: true }); clearTimeout(a._t); a._t = setTimeout(() => a.pause(), (t1 - t0) * 1000 + 300);
      document.querySelectorAll('.it.disc').forEach(x => x.classList.toggle('hearing', x === b)); setTimeout(() => b.classList.remove('hearing'), (t1 - t0) * 1000 + 300); }
    function onStage(e) { const st = document.getElementById('hStage'); if (!st) return null; const r = st.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height; return x >= -.02 && x <= 1.02 && y >= -.02 && y <= 1.02 ? { x: Math.max(0, Math.min(1, x)), y: Math.max(0, Math.min(1, y)) } : null; }
    // ---- the scene: drag to move, pinch to size, double-tap to turn, drag off the scene to throw away
    function wireStage(el, api) { const st = el.querySelector('#hStage'), pts = L.pts;
      st.onpointerdown = e => { const f = e.target.closest('.hf'); pts.set(e.pointerId, [e.clientX, e.clientY]);
        if (pts.size === 2 && L.drag && L.drag.stage) { const [a, b] = [...pts.values()]; L.drag.pinch = Math.hypot(a[0] - b[0], a[1] - b[1]); L.drag.s0 = L.drag.s; return; }
        if (!f) return; e.preventDefault(); const S = L.S, id = +f.dataset.id, g = (S.panels.find(p => p.id === S.sel) || { figs: [] }).figs.find(g => g.id === id); if (!g) return; const r = st.getBoundingClientRect(), now = performance.now();
        if (now - L.lastTap < 320 && L.lastId === id) { api.buzz(12); api.send({ t: 'move', pan: L.S.sel, id, x: g.x, y: g.y, flip: g.flip ? 0 : 1, first: 1, end: 1 }); L.lastTap = 0; return; } L.lastTap = now; L.lastId = id;
        L.drag = { stage: true, id, el: f, x: g.x, y: g.y, s: g.s, dx: g.x - (e.clientX - r.left) / r.width, dy: g.y - (e.clientY - r.top) / r.height, first: 1 }; f.classList.add('held'); try { st.setPointerCapture(e.pointerId); } catch (x) { } api.buzz(6); };
      st.onpointermove = e => { if (!pts.has(e.pointerId)) return; pts.set(e.pointerId, [e.clientX, e.clientY]); const d = L.drag; if (!d || !d.stage) return; const r = st.getBoundingClientRect();
        if (d.pinch && pts.size >= 2) { const [a, b] = [...pts.values()]; d.s = Math.max(.04, Math.min(1.6, d.s0 * Math.hypot(a[0] - b[0], a[1] - b[1]) / d.pinch)); d.el.style.width = d.s * 100 + '%'; }
        else if (!d.pinch) { d.x = (e.clientX - r.left) / r.width + d.dx; d.y = (e.clientY - r.top) / r.height + d.dy; d.el.style.left = d.x * 100 + '%'; d.el.style.top = d.y * 100 + '%'; d.el.style.zIndex = 10 + Math.round(d.y * 100); }
        const out = d.x < -.08 || d.x > 1.08 || d.y < -.08 || d.y > 1.08; d.el.classList.toggle('gone', out); st.classList.toggle('binning', out);
        const now = performance.now(); if (now - L.last > 90 && !out) { L.last = now; api.send({ t: 'move', pan: L.S.sel, id: d.id, x: d.x, y: d.y, s: d.s, first: d.first }); d.first = 0; } };
      const up = e => { pts.delete(e.pointerId); const d = L.drag; if (!d || !d.stage) return; if (d.pinch && pts.size) return; L.drag = null; d.el.classList.remove('held'); st.classList.remove('binning');
        const out = d.x < -.08 || d.x > 1.08 || d.y < -.08 || d.y > 1.08; if (out) { api.buzz(20); d.el.remove(); api.send({ t: 'del', pan: L.S.sel, id: d.id }); } else api.send({ t: 'move', pan: L.S.sel, id: d.id, x: d.x, y: d.y, s: d.s, first: d.first, end: 1 }); };
      st.onpointerup = up; st.onpointercancel = up; }
    L.take = take;
    return { key: 'show', status: null, cls: 'showp', takeover: take };
  }

  // the stand's figures and the kept file share these rules
  const SHOW_CSS = `.sstage{position:absolute;inset:0;overflow:hidden;background:#000}.sstage .sg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity .45s}.sstage .sg.on{opacity:1}
.sfigs{position:absolute;inset:0}.sfig{position:absolute;background-repeat:no-repeat;background-size:100% 100%;transform:translate(-50%,-50%);filter:drop-shadow(0 4px 10px #000b);transition:left .12s linear,top .12s linear,width .12s linear}.sfig.flip{transform:translate(-50%,-50%) scaleX(-1)}
@keyframes sspr{to{background-position:100% 0}}`;
  window.SHOW_CSS = SHOW_CSS;
  const tag = document.createElement('style'); tag.textContent = SHOW_CSS; document.head.append(tag);
  Party.games.show = { title: 'The Show', blurb: 'hold the microphone and say a line; the archive answers with a scene; every phone holds different figures, music and voices to place in it by hand. A show spoken into being, then played in your own voices.', options: [], host, phone };
})();
