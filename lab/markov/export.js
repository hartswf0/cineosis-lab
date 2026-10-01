/* Sending a cut. One project format for every room, and a Send sheet built for a phone:
   SHARE A LINK     the link carries the cut itself (shots, times, words, score), so it opens on a small watch page and plays at
                    once: no engine to load. Lines are spoken by the friend's own device. REMIX reopens it in the Poet.
   WITH MY VOICE    one small file (.markov.html) with the recording inside; goes through the share sheet where the phone allows
   A VIDEO          an MP4, rendered by the lab machine
   MPExport.project(D, cur, extra) · sheet(anchor, getProject, {open}) · link(pr) · file(pr) · mp4(pr) · read(file) · fromLink(hash) · cardHTML(pr) · score(cur, locks) */
(function () {
  const PUBLIC = 'https://hartswf0.github.io/cineosis-lab/lab/', CDN = 'https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/';
  const local = () => /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || location.protocol === 'file:';
  const base = () => local() ? PUBLIC : new URL('.', location.href).href;
  const blobURL = b => new Promise(r => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b); });
  const b64u = u8 => { let s = ''; u8.forEach(c => s += String.fromCharCode(c)); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
  const ub64 = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
  async function pack(o) { const s = new Blob([JSON.stringify(o)]).stream().pipeThrough(new CompressionStream('deflate-raw')); return b64u(new Uint8Array(await new Response(s).arrayBuffer())); }
  async function unpack(t) { const s = new Blob([ub64(t)]).stream().pipeThrough(new DecompressionStream('deflate-raw')); return JSON.parse(await new Response(s).text()); }
  const slug = t => String(t || 'markov-poet').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'markov-poet';
  const DOMI = () => (window.MPGuide ? MPGuide.DOMS.map(d => d[0]) : []);
  const r2 = x => Math.round(x * 100) / 100;

  function score(cur, locks) {
    const m = cur.m || {}, f = cur.fid || { realized: 0, required: 0 }, lk = Object.keys(locks || {}).length;
    const mine = cur.cut.filter(s => { const n0 = cur.cut.findIndex(x => x.phrase === s.phrase); return locks && locks[s.phrase + ':' + (s.i - n0)] === s.k; });
    const daring = mine.length ? mine.reduce((a, s) => a + s.surprisal, 0) / mine.length : 0;
    const kept = f.required ? f.realized / f.required : 1, held = m.continuity == null ? 1 : m.continuity;
    return { kept: f.realized, required: f.required, held: Math.round(held * 100), worlds: m.worlds || 1, choices: lk, daring: +daring.toFixed(1), total: Math.round(50 * kept + 30 * held + 20 * Math.min(1, daring / 6)) };
  }
  function project(D, cur, extra) {
    const sign = c => (D.K.signs || {})[c];
    return { format: 'markov-project/1', made: new Date().toISOString().slice(0, 16).replace('T', ' '), room: extra.room, title: extra.title || (extra.lines || [])[0] || 'The Markov Poet',
      lines: extra.lines || null, poem: extra.poem || null, voice: extra.voice || null, locks: extra.locks || {}, take: extra.take || 0, calm: !!extra.calm, sound: !!extra.sound, score: score(cur, extra.locks),
      film: { T0: cur.T0, T1: cur.T1, audio: cur.audio && !/^blob:/.test(cur.audio.src) ? { rel: cur.audio.src, offset: cur.audio.offset || 0 } : null, audioData: extra.audioData || null,
        cut: cur.cut.map(s => { const x = D.LIB.shots[s.k]; return { v: x.video, in: s.in || 0, t0: s.t0, t1: s.t1, p: +s.p.toFixed(3), op: s.op,
          els: (x.signs || []).slice(0, 3).map(sign).filter(Boolean).map(g => [g.symbol, window.MPGuide ? MPGuide.color(g.dom) : '#ccc', g.name, g.dom]),
          cap: [x.scale, x.title, x.year].filter(Boolean).join(' · '), edit: (window.MPFilm && MPFilm.EDIT[s.op]) || '' }; }),
        ph: cur.ph.map(p => [p.t0, p.t1, p.text]) } };
  }
  async function remixLink(pr) {
    if (pr.lines) return base() + 'shannon-poet.html#p=' + await pack({ l: pr.lines, k: pr.locks });
    return base() + 'shannon-narrative.html?poem=' + encodeURIComponent(pr.poem) + '#k=' + await pack({ k: pr.locks, t: pr.take });
  }
  // the link: the cut itself, small. Shots by their archive path; signs as symbol + domain number.
  async function link(pr) {
    const di = DOMI(), f = pr.film, pub = f.audio && /^(markov\/voice\/(?!live)|wygwyl\/)/.test(f.audio.rel) ? [f.audio.rel, r2(f.audio.offset)] : 0;
    const o = { t: pr.title, L: pr.lines, o: pr.poem, k: pr.locks, n: pr.take || 0, c: pr.calm ? 1 : 0, T: [r2(f.T0), r2(f.T1)], s: [pr.score.total, pr.score.kept, pr.score.required, pr.score.held, pr.score.choices, pr.score.daring], a: pub,
      C: f.cut.map(c => [c.v.startsWith(CDN) ? '~' + c.v.slice(CDN.length) : c.v, r2(c.in), r2(c.t0), r2(c.t1), c.els.map(e => e[0] + Math.max(0, di.indexOf(e[3]))).join(' '), c.cap, c.edit]),
      P: f.ph.map(p => [r2(p[0]), r2(p[1]), p[2]]) };
    return base() + 'markov-watch.html#f=' + await pack(o);
  }
  async function fromLink(hash) {
    const o = await unpack(hash), D = window.MPGuide ? MPGuide.DOMS : [];
    const pr = { format: 'markov-project/1', title: o.t, lines: o.L, poem: o.o, locks: o.k || {}, take: o.n || 0, calm: !!o.c, sound: false, voice: 'device', made: '',
      score: { total: o.s[0], kept: o.s[1], required: o.s[2], held: o.s[3], choices: o.s[4], daring: o.s[5] },
      film: { T0: o.T[0], T1: o.T[1], audio: o.a ? { rel: o.a[0], url: base() + o.a[0], offset: o.a[1] } : null, audioData: null,
        cut: o.C.map(c => ({ v: c[0][0] === '~' ? CDN + c[0].slice(1) : c[0], in: c[1], t0: c[2], t1: c[3], cap: c[5], edit: c[6],
          els: (c[4] ? c[4].split(' ') : []).map(e => { const d = D[+e.slice(-1)] || ['', '#ccc', '']; return [e.slice(0, -1), d[1], d[2], d[0]]; }) })),
        ph: o.P } };
    pr.remix = await remixLink(pr); return pr;
  }
  async function withAudio(pr) {
    const a = pr.film.audio; if (pr.film.audioData || !a) return pr;
    if (/^markov\/(voice\/live|recordings)\//.test(a.rel)) { try { pr.film.audioData = await blobURL(await (await fetch(a.rel)).blob()); } catch (e) { } }
    else pr.film.audio.url = base() + a.rel;
    return pr;
  }
  async function cardHTML(pr) { pr = await withAudio(JSON.parse(JSON.stringify(pr))); if (!pr.remix) pr.remix = await remixLink(pr); return CARD.replace('/*PROJECT*/', JSON.stringify(pr).replace(/</g, '\\u003c')); }
  function download(href, name) { const a = document.createElement('a'); a.href = href; a.download = name; document.body.append(a); a.click(); a.remove(); }
  async function file(pr, share) {
    const name = slug(pr.title) + '.markov.html', blob = new Blob([await cardHTML(pr)], { type: 'text/html' });
    if (share && navigator.canShare) { const f = new File([blob], name, { type: 'text/html' }); if (navigator.canShare({ files: [f] })) { try { await navigator.share({ files: [f], title: pr.title }); return 'shared ' + name; } catch (e) { if (e.name === 'AbortError') return 'not sent'; } } }
    download(URL.createObjectURL(blob), name); return 'saved ' + name;
  }
  async function mp4(pr) {
    const f = pr.film, job = { cut: f.cut.map(c => ({ video: c.v, in: c.in, t0: c.t0, t1: c.t1, dna: [c.els.map(e => e[0]).join(' '), c.cap].filter(Boolean).join(' · ') })),
      phrases: f.ph.map(p => ({ t0: p[0], t1: p[1], text: p[2] })), T0: f.T0, T1: f.T1, audio: f.audioData ? null : f.audio && { src: f.audio.rel, offset: f.audio.offset }, audio_b64: f.audioData || null, sound: pr.sound, calm: pr.calm };
    const r = await fetch('/api/render', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(job) }); const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
    download(j.video, slug(pr.title) + '.mp4'); return 'saved ' + slug(pr.title) + '.mp4';
  }
  async function read(fileObj) {
    const t = await fileObj.text(); if (/^\s*{/.test(t)) return JSON.parse(t);
    const m = t.match(/<script type="application\/json" id="markov-project">([\s\S]*?)<\/script>/); if (!m) throw new Error('no Markov Poet project in this file'); return JSON.parse(m[1]);
  }

  // ---------------------------------------------------------------- the Send sheet
  const CSS = `#mpx{position:fixed;inset:0;z-index:90;background:#000a;display:flex;align-items:flex-end;justify-content:center;font:13px 'IBM Plex Mono',monospace;color:#efe9dd}
  #mpx article{background:#0e0d0c;border:1px solid #2a2723;border-radius:16px 16px 0 0;width:min(460px,100%);padding:16px 16px calc(16px + env(safe-area-inset-bottom));max-height:90dvh;overflow:auto}
  @media(min-width:700px){#mpx{align-items:center}#mpx article{border-radius:16px}}
  #mpx .hd{display:flex;align-items:baseline;gap:10px;margin-bottom:12px}#mpx .hd b{font:400 22px/1.2 Fraunces,Georgia,serif;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  #mpx .hd .sc{color:#e8c070;font:400 22px Fraunces,serif}#mpx .hd small{color:#8a8378;font-size:10px}#mpx .x{background:none;border:0;color:#8a8378;font:inherit;cursor:pointer;min-width:44px;min-height:44px;margin:-10px -10px -10px 0}
  #mpx .meters{display:flex;gap:14px;color:#8a8378;font-size:10.5px;letter-spacing:.04em;margin:-4px 0 14px;flex-wrap:wrap}#mpx .meters b{color:#efe9dd;font-weight:500}
  #mpx .act{display:block;width:100%;text-align:left;border:1px solid #2a2723;background:none;color:#efe9dd;font:inherit;border-radius:12px;padding:13px 14px;margin-top:8px;cursor:pointer;min-height:56px}
  #mpx .act b{display:block;font-weight:500;font-size:14px}#mpx .act small{display:block;color:#8a8378;font-size:11.5px;margin-top:2px;line-height:1.35}
  #mpx .act.p{background:#e8c070;border-color:#e8c070;color:#1a1408}#mpx .act.p small{color:#4a3d1c}#mpx .act:disabled{opacity:.4;cursor:default}
  #mpx .url{display:flex;gap:6px;margin-top:8px}#mpx .url input{flex:1;min-width:0;background:#151412;border:1px solid #2a2723;border-radius:8px;color:#8a8378;font:11px 'IBM Plex Mono',monospace;padding:0 10px;height:40px}
  #mpx .url button{border:1px solid #2a2723;background:none;color:#efe9dd;font:inherit;border-radius:8px;padding:0 14px;cursor:pointer}
  #mpx .msg{color:#e8c070;min-height:18px;margin-top:10px;font-size:12px}#mpx .quiet{background:none;border:0;color:#8a8378;font:inherit;cursor:pointer;padding:12px 0 0;text-decoration:underline}`;
  function sheet(anchor, get, opts = {}) {
    let el = document.getElementById('mpx'); if (el) { el.remove(); return; }
    if (!document.getElementById('mpx-css')) { const st = document.createElement('style'); st.id = 'mpx-css'; st.textContent = CSS; document.head.append(st); }
    const pr = get(); el = document.createElement('div'); el.id = 'mpx'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-label', 'Send');
    const close = () => el.remove(), server = window.SH && SH.server, canShare = !!navigator.share;
    if (!pr || !pr.film) { el.innerHTML = `<article><div class="hd"><b>Nothing to send yet</b><button class="x">CLOSE</button></div><p style="color:#8a8378;margin:0">Type or say a line first. Or open a film a friend sent.</p>${opts.open ? '<button class="act" data-a="open"><b>Open a project file</b><small>a .markov.html from a friend</small></button>' : ''}<div class="msg"></div></article>`; }
    else { const s = pr.score, mine = !!pr.film.audioData;
      el.innerHTML = `<article><div class="hd"><b>${String(pr.title).replace(/</g, '&lt;')}</b><span class="sc">${s.total}</span><small>/100</small><button class="x">CLOSE</button></div>
      <div class="meters"><span><b>${s.kept}/${s.required}</b> relations kept</span><span><b>${s.held}%</b> worlds held</span><span><b>${s.choices}</b> choices</span><span><b>${s.daring}</b> bits daring</span></div>
      <button class="act p" data-a="link"><b>${canShare ? 'Share a link' : 'Copy a link'}</b><small>It plays at once on any phone: the film, the words, each shot's signs. ${mine ? 'Their phone speaks the lines; your recording travels in the file below.' : 'Their phone speaks the lines.'} REMIX lets them change it.</small></button>
      <div class="url"><input readonly aria-label="The link" value="making the link…"><button data-a="copy">COPY</button></div>
      <button class="act" data-a="file"><b>${mine ? 'Send it with my voice' : 'Send it as a file'}</b><small>${mine ? 'One small file with your recording inside.' : 'One small file that plays on its own.'} ${canShare ? 'Opens the share sheet where the phone allows; otherwise it is saved.' : 'Saved to this computer.'}</small></button>
      <button class="act" data-a="mp4" ${server ? '' : 'disabled'}><b>Save a video (MP4)</b><small>${server ? 'Rendered on this lab machine: shots, dissolves, words, voice.' : 'Made by the lab machine; not available on the public site.'}</small></button>
      ${opts.open ? '<button class="quiet" data-a="open">Open a project file a friend sent</button>' : ''}<div class="msg"></div></article>`;
      link(pr).then(u => { pr._link = u; const i = el.querySelector('.url input'); if (i) i.value = u; }).catch(() => { }); }
    const msg = t => { const m = el.querySelector('.msg'); if (m) m.textContent = t; };
    el.onclick = e => { if (e.target === el) close(); }; el.querySelector('.x').onclick = close;
    el.querySelectorAll('[data-a]').forEach(b => b.onclick = async () => { const a = b.dataset.a;
      try {
        if (a === 'link') { const u = pr._link || await link(pr); if (navigator.share) { try { await navigator.share({ title: pr.title, text: pr.title + ': a Markov Poet film', url: u }); msg('sent'); } catch (e) { if (e.name !== 'AbortError') { await navigator.clipboard.writeText(u); msg('link copied'); } } } else { await navigator.clipboard.writeText(u); msg('link copied'); } }
        else if (a === 'copy') { const u = pr._link || await link(pr); try { await navigator.clipboard.writeText(u); msg('link copied'); } catch (e) { el.querySelector('.url input').select(); msg('select and copy the link'); } }
        else if (a === 'file') { msg('folding the film into one file…'); msg(await file(pr, true)); }
        else if (a === 'mp4') { msg('rendering: a minute or two…'); msg(await mp4(pr)); }
        else if (a === 'open') { const i = document.createElement('input'); i.type = 'file'; i.accept = '.html,.json,text/html'; i.onchange = async () => { try { const p = await read(i.files[0]); close(); opts.open(p); } catch (e) { msg(e.message); } }; i.click(); }
      } catch (e) { msg('could not: ' + e.message); } });
    document.body.append(el);
  }

  // ---------------------------------------------------------------- the player: one page, used by the project file and by the watch page
  const CARD = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>A Markov Poet film</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<script type="application/json" id="markov-project">/*PROJECT*/<\/script>
<style>[hidden]{display:none!important}html,body{margin:0;height:100%;background:#050505;color:#efe9dd;overflow:hidden;font:12px 'IBM Plex Mono',monospace;-webkit-tap-highlight-color:transparent}
.lay{position:fixed;inset:0;opacity:0}.lay video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;animation:d 40s ease-in-out infinite alternate}
.lay.cur{opacity:1}.lay.in{opacity:1;mix-blend-mode:screen;animation:i var(--d,1.5s) cubic-bezier(.3,.6,.2,1) both;z-index:2}.lay.out{animation:o var(--d,1.5s) ease both;z-index:1}
@keyframes i{0%{opacity:0;filter:blur(16px) brightness(1.7) saturate(.4);transform:scale(1.07)}45%{opacity:.9;filter:blur(5px) brightness(1.2)}100%{opacity:1;filter:none;transform:none}}
@keyframes o{to{opacity:0;filter:blur(20px) brightness(.55);transform:scale(1.035)}}@keyframes d{to{transform:scale(1.045) translate(-.6%,.4%)}}
.shade{position:fixed;inset:0;background:linear-gradient(180deg,#0009,transparent 24%,transparent 50%,#000d);z-index:3;pointer-events:none}
#say{position:fixed;left:50%;bottom:calc(74px + env(safe-area-inset-bottom));transform:translateX(-50%);width:min(1150px,90vw);text-align:center;font:300 clamp(24px,4vw,56px)/1.16 Fraunces,Georgia,serif;text-shadow:0 0 22px #000;z-index:5}
#say span{display:inline-block;opacity:0;filter:blur(10px);animation:w .9s cubic-bezier(.2,.7,.2,1) forwards;white-space:pre}@keyframes w{to{opacity:1;filter:none}}
#dna{position:fixed;left:14px;right:14px;top:calc(14px + env(safe-area-inset-top));z-index:5;display:flex;gap:8px;align-items:center;flex-wrap:wrap;color:#efe9ddaa;font-size:10px;letter-spacing:.05em}
#dna .el{display:inline-grid;place-items:center;min-width:22px;height:22px;padding:0 4px;border-radius:3px;color:#15120d}#dna .ed{color:#e8c070}
#go{position:fixed;inset:0;z-index:9;display:grid;place-items:center;background:#000d;text-align:center;padding:20px}#go h1{font:300 clamp(28px,6vw,56px)/1.1 Fraunces,serif;margin:0 0 6px}#go p{color:#8a8378;margin:0 0 18px}
.sc{display:flex;gap:16px;justify-content:center;margin:0 0 22px;flex-wrap:wrap}.sc div b{display:block;font:300 26px Fraunces,serif}.sc div span{color:#8a8378;font-size:9.5px;letter-spacing:.08em}.sc .tot b{color:#e8c070;font-size:38px}
.btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}.btns a,.btns button{min-height:52px;padding:0 26px;border-radius:26px;border:1px solid #3a3631;background:none;color:#efe9dd;font:inherit;letter-spacing:.1em;cursor:pointer;display:inline-flex;align-items:center;text-decoration:none}
.btns .p{background:#e8c070;color:#1a1408;border-color:#e8c070}
#ctl{position:fixed;left:0;right:0;bottom:calc(10px + env(safe-area-inset-bottom));display:flex;justify-content:center;gap:4px;z-index:6;letter-spacing:.1em}#ctl button,#ctl a{background:none;border:0;color:#a59e93;font:inherit;cursor:pointer;text-decoration:none;min-height:44px;padding:0 12px;display:inline-flex;align-items:center}
#bar{position:fixed;left:0;right:0;bottom:0;height:4px;z-index:6;display:flex;gap:1px}#bar i{display:block;height:100%}
</style></head><body><div class="lay"><video playsinline webkit-playsinline muted></video></div><div class="lay"><video playsinline webkit-playsinline muted></video></div><div class="shade"></div>
<div id="dna"></div><div id="say"></div>
<div id="ctl"><button id="pp">PAUSE</button><button id="vo">VOICE ON</button><button id="snd">FILM SOUND OFF</button><a id="rmx">REMIX</a></div><div id="bar"></div>
<div id="go"><div><h1></h1><p id="by"></p><div class="sc" id="sc"></div><div class="btns"><button class="p" id="watch">WATCH</button><a id="rmx2">REMIX THIS CUT</a></div></div></div><audio id="au" playsinline></audio>
<script>const P=JSON.parse(document.getElementById('markov-project').textContent),F=P.film;const $=s=>document.querySelector(s),L=[...document.querySelectorAll('.lay')],V=L.map(l=>l.firstChild),au=$('#au');
let on=0,run=!1,t=F.T0,last=0,shown=-1,ls=-1,snd=P.sound,vo=!0,dur=P.calm?2.6:1.5,off=F.audio?F.audio.offset:0;const e=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
$('#go h1').textContent=P.title;$('#by').textContent='a Markov Poet film · '+F.cut.length+' shot'+(F.cut.length>1?'s':'');const s=P.score;
$('#sc').innerHTML='<div class="tot"><b>'+s.total+'</b><span>SCORE</span></div><div><b>'+s.kept+'/'+s.required+'</b><span>RELATIONS KEPT</span></div><div><b>'+s.held+'%</b><span>WORLDS HELD</span></div><div><b>'+s.choices+'</b><span>CHOICES</span></div><div><b>'+s.daring+'</b><span>DARING</span></div>';
$('#rmx').href=$('#rmx2').href=P.remix;if(F.audioData)au.src=F.audioData;else if(F.audio&&F.audio.url)au.src=F.audio.url;else off=0;
const tts=!au.getAttribute('src')&&'speechSynthesis'in window;$('#snd').textContent='FILM SOUND '+(snd?'ON':'OFF');
$('#bar').innerHTML=F.cut.map(c=>'<i style="flex:'+Math.max(.1,c.t1-c.t0)+' 1 0;background:'+((c.els[0]||[])[1]||'#555')+';opacity:.3"></i>').join('');
function ld(v,u,a){if(v.dataset.u!==u){v.dataset.u=u;v.src=u}const x=()=>{try{v.currentTime=a}catch(r){}};v.readyState>=1?x():v.addEventListener('loadedmetadata',x,{once:!0})}
function show(c,a,i){const n=1-on;ld(V[n],c.v,a);V[n].playbackRate=P.calm?.8:1;L.forEach(l=>l.style.setProperty('--d',dur+'s'));L[n].className='lay in';L[on].className='lay out';V[n].muted=!snd;if(run)V[n].play().catch(()=>{});const w=on;on=n;setTimeout(()=>{if(on!==n)return;L[n].className='lay cur';L[w].className='lay';V[w].pause()},dur*1e3+60);
$('#dna').innerHTML='<span>'+c.els.map(x=>'<span class="el" style="background:'+x[1]+'" title="'+e(x[2])+'">'+x[0]+'</span>').join(' ')+'</span><span>'+e(c.cap)+'</span><span class="ed">'+e(c.edit)+'</span>';
[...$('#bar').children].forEach((b,j)=>b.style.opacity=j<i?.6:j===i?1:.25)}
function speak(tx){if(!tts||!vo)return;try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(tx);u.rate=.92;speechSynthesis.speak(u)}catch(r){}}
function frame(){const i=F.cut.findIndex(c=>t>=c.t0&&t<c.t1);if(i>=0&&i!==shown){shown=i;show(F.cut[i],F.cut[i].in+Math.max(0,t-F.cut[i].t0),i)}const li=F.ph.findIndex(p=>t>=p[0]&&t<p[1]);
if(li>=0&&li!==ls){ls=li;const tx=F.ph[li][2];$('#say').innerHTML=tx.split(/(\\s+)/).map((w,k)=>/^\\s+$/.test(w)?w:'<span style="animation-delay:'+k*45+'ms">'+e(w)+'</span>').join('');if(run)speak(tx)}
const v=V[on];if(run){if(v.ended||(v.duration&&v.currentTime>=v.duration-.12))v.pause();else if(v.paused&&v.readyState>=2)v.play().catch(()=>{})}}
setInterval(()=>{if(!run)return;const n=performance.now();if(au.getAttribute('src')&&!au.paused)t=au.currentTime+off;else t+=(n-last)/1e3;last=n;if(t>=F.T1){run=!1;au.pause();V.forEach(v=>v.pause());t=F.T0;shown=-1;ls=-1;$('#go').hidden=!1;$('#watch').textContent='WATCH AGAIN';return}frame()},40);
function play(){run=!0;last=performance.now();$('#go').hidden=!0;if(au.getAttribute('src')){au.muted=!vo;try{au.currentTime=Math.max(0,t-off)}catch(r){}au.play().catch(()=>{})}ls=-1;frame();V[on].play().catch(()=>{});$('#pp').textContent='PAUSE'}
function pause(){run=!1;au.pause();V.forEach(v=>v.pause());if(tts)speechSynthesis.cancel();$('#pp').textContent='PLAY'}
$('#watch').onclick=play;$('#pp').onclick=()=>run?pause():play();$('#snd').onclick=()=>{snd=!snd;V[on].muted=!snd;$('#snd').textContent='FILM SOUND '+(snd?'ON':'OFF')};
$('#vo').onclick=()=>{vo=!vo;au.muted=!vo;if(!vo&&tts)speechSynthesis.cancel();$('#vo').textContent='VOICE '+(vo?'ON':'OFF')};frame();<\/script></body></html>`;
  window.MPExport = { project, sheet, menu: sheet, link, fromLink, file, mp4, read, score, pack, unpack, cardHTML, PUBLIC };
})();
