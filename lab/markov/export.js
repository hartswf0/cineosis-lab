/* Making a cut portable. One project format for every room, three ways out:
   MPExport.file(project)  one HTML page: the film plays (words, voice, the cut, each shot's signs), the score shows, and
                           REMIX reopens the same cut in the Markov Poet for the next person to change. The project JSON rides inside.
   MPExport.mp4(project)   a finished video, rendered by the lab machine (POST /api/render)
   MPExport.link(project)  a link: the words and the choices; the film recomposes where it opens
   MPExport.read(file)     a project back from an .html or .json file
   MPExport.score(cur, locks)  the game: relations kept, worlds held, choices made, daring (the surprise of the choices, in bits) */
(function () {
  const PUBLIC = 'https://hartswf0.github.io/cineosis-lab/lab/';
  const local = () => /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || location.protocol === 'file:';
  const privatePath = s => /^markov\/(voice\/live|recordings)\//.test(s);
  const abs = s => /^(https?:|data:)/.test(s) ? s : local() ? PUBLIC + s : new URL(s, location.href).href;
  const blobURL = b => new Promise(r => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b); });
  const b64u = u8 => { let s = ''; u8.forEach(c => s += String.fromCharCode(c)); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
  const ub64 = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
  async function pack(o) { const s = new Blob([JSON.stringify(o)]).stream().pipeThrough(new CompressionStream('deflate-raw')); return b64u(new Uint8Array(await new Response(s).arrayBuffer())); }
  async function unpack(t) { const s = new Blob([ub64(t)]).stream().pipeThrough(new DecompressionStream('deflate-raw')); return JSON.parse(await new Response(s).text()); }
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const slug = t => String(t || 'markov-poet').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'markov-poet';

  function score(cur, locks) {
    const m = cur.m || {}, f = cur.fid || { realized: 0, required: 0 }, lk = Object.keys(locks || {}).length;
    const mine = cur.cut.filter(s => { const n0 = cur.cut.findIndex(x => x.phrase === s.phrase); return locks && locks[s.phrase + ':' + (s.i - n0)] === s.k; });
    const daring = mine.length ? mine.reduce((a, s) => a + s.surprisal, 0) / mine.length : 0;
    const kept = f.required ? f.realized / f.required : 1, held = m.continuity == null ? 1 : m.continuity;
    return { kept: f.realized, required: f.required, held: Math.round(held * 100), worlds: m.worlds || 1, choices: lk, daring: +daring.toFixed(1),
      total: Math.round(50 * kept + 30 * held + 20 * Math.min(1, daring / 6)) };
  }
  // a project from any room's composed film. D: the loaded data (SH.data); extra: {room, title, lines, poem, voice, locks, take, calm, sound, audioData}
  function project(D, cur, extra) {
    const sign = c => (D.K.signs || {})[c];
    const au = cur.audio ? { rel: cur.audio.src, offset: cur.audio.offset || 0 } : null;
    return { format: 'markov-project/1', made: new Date().toISOString().slice(0, 16).replace('T', ' '), room: extra.room, title: extra.title || (extra.lines || [])[0] || 'The Markov Poet',
      lines: extra.lines || null, poem: extra.poem || null, voice: extra.voice || null, locks: extra.locks || {}, take: extra.take || 0, calm: !!extra.calm, sound: !!extra.sound,
      score: score(cur, extra.locks),
      film: { T0: cur.T0, T1: cur.T1, audio: au, audioData: extra.audioData || null,
        cut: cur.cut.map(s => { const x = D.LIB.shots[s.k]; return { v: x.video, in: s.in || 0, t0: s.t0, t1: s.t1, p: +s.p.toFixed(3), op: s.op,
          els: (x.signs || []).slice(0, 3).map(sign).filter(Boolean).map(g => [g.symbol, window.MPGuide ? MPGuide.color(g.dom) : '#ccc', g.name, g.dom]),
          cap: [x.scale, x.title, x.year].filter(Boolean).join(' · '), edit: (window.MPFilm && MPFilm.EDIT[s.op]) || '' }; }),
        ph: cur.ph.map(p => [p.t0, p.t1, p.text]) } };
  }
  async function withAudio(pr) {                 // a voice the friend can hear: published files by URL, private ones inside the file
    const a = pr.film.audio; if (pr.film.audioData || !a) return pr;
    if (privatePath(a.rel) || local() && !/^markov\/voice\/|^wygwyl\//.test(a.rel)) { try { pr.film.audioData = await blobURL(await (await fetch(a.rel)).blob()); } catch (e) { } }
    else pr.film.audio.url = abs(a.rel);
    return pr;
  }
  async function link(pr) {
    if (pr.lines) return PUBLIC + 'shannon-poet.html#p=' + await pack({ l: pr.lines, k: pr.locks });
    return PUBLIC + 'shannon-narrative.html?poem=' + encodeURIComponent(pr.poem) + '#k=' + await pack({ k: pr.locks, t: pr.take });
  }
  async function file(pr) {
    pr = await withAudio(JSON.parse(JSON.stringify(pr))); pr.remix = await link(pr);
    const html = CARD.replace('/*PROJECT*/', JSON.stringify(pr).replace(/</g, '\\u003c'));
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([html], { type: 'text/html' })); a.download = slug(pr.title) + '.markov.html'; document.body.append(a); a.click(); a.remove();
    return slug(pr.title) + '.markov.html';
  }
  async function mp4(pr) {
    const f = pr.film, job = { cut: f.cut.map(c => ({ video: c.v, in: c.in, t0: c.t0, t1: c.t1, dna: [c.els.map(e => e[0]).join(' '), c.cap].filter(Boolean).join(' · ') })),
      phrases: f.ph.map(p => ({ t0: p[0], t1: p[1], text: p[2] })), T0: f.T0, T1: f.T1, audio: f.audioData ? null : f.audio && { src: f.audio.rel, offset: f.audio.offset }, audio_b64: f.audioData || null, sound: pr.sound, calm: pr.calm };
    const r = await fetch('/api/render', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(job) }); const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status);
    const a = document.createElement('a'); a.href = j.video; a.download = slug(pr.title) + '.mp4'; document.body.append(a); a.click(); a.remove(); return slug(pr.title) + '.mp4';
  }
  async function read(fileObj) {
    const t = await fileObj.text();
    if (/^\s*{/.test(t)) return JSON.parse(t);
    const m = t.match(/<script type="application\/json" id="markov-project">([\s\S]*?)<\/script>/); if (!m) throw new Error('no Markov Poet project in this file');
    return JSON.parse(m[1]);
  }
  // the menu every room shows: the same three ways out, always available, with the score of the cut
  function menu(anchor, get, opts = {}) {
    let el = document.getElementById('mpx');
    if (!el) { el = document.createElement('div'); el.id = 'mpx'; document.body.append(el);
      const st = document.createElement('style'); st.textContent = `#mpx{position:fixed;z-index:90;background:#0e0d0c;border:1px solid #2a2723;border-radius:12px;padding:8px;width:min(340px,94vw);font:12px 'IBM Plex Mono',monospace;color:#efe9dd;box-shadow:0 18px 40px #000b}
      #mpx .sc{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;padding:6px 6px 10px;border-bottom:1px solid #1f1d1a;margin-bottom:4px}#mpx .sc div{text-align:center}#mpx .sc b{display:block;font:400 20px Fraunces,Georgia,serif}#mpx .sc span{color:#8a8378;font-size:9.5px;letter-spacing:.06em}
      #mpx .tot{grid-column:1/-1;display:flex;justify-content:space-between;align-items:baseline;padding:0 2px 6px}#mpx .tot b{font:400 30px Fraunces,serif;color:#e8c070}#mpx .tot span{color:#8a8378}
      #mpx button{display:block;width:100%;text-align:left;background:none;border:0;padding:11px 10px;border-radius:8px;cursor:pointer;color:#efe9dd;font:inherit;min-height:44px}#mpx button:hover{background:#ffffff0c}#mpx button:disabled{opacity:.35;cursor:default}
      #mpx small{display:block;color:#8a8378;font-size:10.5px;margin-top:2px}#mpx .msg{padding:8px 10px;color:#e8c070;min-height:0}`; document.head.append(st); }
    if (!el.hidden && el.dataset.for === anchor.id) { el.hidden = true; return; }
    const pr = get(); if (!pr) return;
    const s = pr.score, server = window.SH && SH.server;
    el.dataset.for = anchor.id; el.hidden = false;
    if (!pr.film) { el.innerHTML = `<div class="msg" style="color:#8a8378">Make a film first: type a line and press Return. Or open one a friend sent.</div>${opts.open ? '<button data-a="open">Open a project…<small>a .markov.html file from a friend</small></button>' : ''}<div class="msg" id="mpxMsg"></div>`; }
    else el.innerHTML = `<div class="sc"><div class="tot"><span>YOUR CUT</span><b>${s.total}</b><span>of 100</span></div>
      <div><b>${s.kept}/${s.required}</b><span>RELATIONS KEPT</span></div><div><b>${s.held}%</b><span>WORLDS HELD</span></div><div><b>${s.choices}</b><span>CHOICES</span></div><div><b>${s.daring}</b><span>DARING (BITS)</span></div></div>
      <button data-a="file">Project file (.html)<small>watch it, then REMIX: a friend reopens and changes the same cut</small></button>
      <button data-a="mp4" ${server ? '' : 'disabled'}>Finished film (.mp4)<small>${server ? 'rendered on this lab machine: shots, dissolves, words, voice' : 'needs the lab machine; the project file plays anywhere'}</small></button>
      <button data-a="link">Copy a link<small>the words and your choices, no voice</small></button>
      ${opts.open ? '<button data-a="open">Open a project…<small>a .markov.html file from a friend</small></button>' : ''}<div class="msg" id="mpxMsg"></div>`;
    const r = anchor.getBoundingClientRect(), w = Math.min(340, innerWidth * .94);
    el.style.left = Math.max(8, Math.min(innerWidth - w - 8, r.left + r.width / 2 - w / 2)) + 'px';
    if (r.top > innerHeight / 2) { el.style.top = ''; el.style.bottom = (innerHeight - r.top + 10) + 'px'; } else { el.style.bottom = ''; el.style.top = (r.bottom + 10) + 'px'; }
    const msg = t => el.querySelector('#mpxMsg').textContent = t;
    el.querySelectorAll('button').forEach(b => b.onclick = async () => { const a = b.dataset.a;
      try { if (a === 'file') { msg('folding the film into one page…'); msg('downloaded ' + await file(pr)); }
        else if (a === 'mp4') { msg('rendering: a minute or two…'); msg('downloaded ' + await mp4(pr)); }
        else if (a === 'link') { const u = await link(pr); try { await navigator.clipboard.writeText(u); msg('link copied'); } catch (e) { prompt('Copy this link', u); } }
        else if (a === 'open') { const i = document.createElement('input'); i.type = 'file'; i.accept = '.html,.json'; i.onchange = async () => { try { opts.open(await read(i.files[0])); el.hidden = true; } catch (e) { msg(e.message); } }; i.click(); }
      } catch (e) { msg('could not: ' + e.message); } });
    setTimeout(() => document.addEventListener('click', function off(e) { if (!el.contains(e.target) && e.target !== anchor && !anchor.contains(e.target)) { el.hidden = true; document.removeEventListener('click', off); } }), 0);
  }

  // ---------------------------------------------------------------- the project file: a player, a score, a remix
  const CARD = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>A Markov Poet film</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;1,9..144,300&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<script type="application/json" id="markov-project">/*PROJECT*/<\/script>
<style>html,body{margin:0;height:100%;background:#050505;color:#efe9dd;overflow:hidden;font:12px 'IBM Plex Mono',monospace}
.lay{position:fixed;inset:0;opacity:0}.lay video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;animation:d 40s ease-in-out infinite alternate}
.lay.cur{opacity:1}.lay.in{opacity:1;mix-blend-mode:screen;animation:i var(--d,1.5s) cubic-bezier(.3,.6,.2,1) both;z-index:2}.lay.out{animation:o var(--d,1.5s) ease both;z-index:1}
@keyframes i{0%{opacity:0;filter:blur(16px) brightness(1.7) saturate(.4);transform:scale(1.07)}45%{opacity:.9;filter:blur(5px) brightness(1.2)}100%{opacity:1;filter:none;transform:none}}
@keyframes o{to{opacity:0;filter:blur(20px) brightness(.55);transform:scale(1.035)}}@keyframes d{to{transform:scale(1.045) translate(-.6%,.4%)}}
.shade{position:fixed;inset:0;background:linear-gradient(180deg,#0009,transparent 24%,transparent 52%,#000c);z-index:3;pointer-events:none}
#say{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom));transform:translateX(-50%);width:min(1150px,90vw);text-align:center;font:300 clamp(24px,4vw,56px)/1.16 Fraunces,Georgia,serif;text-shadow:0 0 22px #000;z-index:5}
#say span{display:inline-block;opacity:0;filter:blur(10px);animation:w .9s cubic-bezier(.2,.7,.2,1) forwards;white-space:pre}@keyframes w{to{opacity:1;filter:none}}
#poem{position:fixed;left:18px;top:16px;max-width:55vw;font:300 15px/1.5 Fraunces,Georgia,serif;color:#8a8378;z-index:5}#poem .now{color:#efe9dd}
#dna{position:fixed;right:16px;top:16px;z-index:5;display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end;color:#efe9ddaa;font-size:10px;letter-spacing:.05em;max-width:42vw}
#dna .el{display:inline-grid;place-items:center;min-width:22px;height:22px;padding:0 4px;border-radius:3px;color:#15120d}#dna .ed{color:#e8c070}
#go{position:fixed;inset:0;z-index:9;display:grid;place-items:center;background:#000d;text-align:center;padding:20px}#go h1{font:300 clamp(28px,5vw,56px)/1.1 Fraunces,serif;margin:0 0 6px}#go p{color:#8a8378;margin:0 0 18px}
.sc{display:flex;gap:18px;justify-content:center;margin:0 0 22px;flex-wrap:wrap}.sc div b{display:block;font:300 28px Fraunces,serif}.sc div span{color:#8a8378;font-size:10px;letter-spacing:.08em}.sc .tot b{color:#e8c070;font-size:40px}
.btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}.btns a,.btns button{min-height:48px;padding:0 22px;border-radius:24px;border:1px solid #3a3631;background:none;color:#efe9dd;font:inherit;letter-spacing:.1em;cursor:pointer;display:inline-flex;align-items:center;text-decoration:none}
.btns .p{background:#e8c070;color:#1a1408;border-color:#e8c070}
#ctl{position:fixed;left:50%;bottom:calc(20px + env(safe-area-inset-bottom));transform:translateX(-50%);display:flex;gap:20px;z-index:6;letter-spacing:.1em}#ctl button,#ctl a{background:none;border:0;color:#8a8378;font:inherit;cursor:pointer;text-decoration:none;min-height:40px}#ctl button:hover,#ctl a:hover{color:#efe9dd}
#bar{position:fixed;left:0;right:0;bottom:0;height:3px;background:#ffffff14;z-index:6;display:flex}#bar i{display:block;height:100%}
</style></head><body><div class="lay"><video playsinline muted></video></div><div class="lay"><video playsinline muted></video></div><div class="shade"></div>
<div id="poem"></div><div id="dna"></div><div id="say"></div>
<div id="ctl"><button id="pp">PAUSE</button><button id="snd">FILM SOUND OFF</button><a id="rmx" target="_blank" rel="noopener">REMIX</a></div><div id="bar"></div>
<div id="go"><div><h1></h1><p id="by"></p><div class="sc" id="sc"></div><div class="btns"><button class="p" id="watch">WATCH</button><a id="rmx2" target="_blank" rel="noopener">REMIX THIS CUT</a></div></div></div><audio id="au"></audio>
<script>const P=JSON.parse(document.getElementById('markov-project').textContent),F=P.film;const $=s=>document.querySelector(s),L=[...document.querySelectorAll('.lay')],V=L.map(l=>l.firstChild),au=$('#au');
let on=0,run=!1,t=F.T0,last=0,shown=-1,ls=-1,snd=P.sound,dur=P.calm?2.6:1.5,off=F.audio?F.audio.offset:0;const e=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);
$('#go h1').textContent=P.title;$('#by').textContent='a Markov Poet film · '+P.made+' · '+F.cut.length+' shots';const s=P.score;
$('#sc').innerHTML='<div class="tot"><b>'+s.total+'</b><span>SCORE</span></div><div><b>'+s.kept+'/'+s.required+'</b><span>RELATIONS KEPT</span></div><div><b>'+s.held+'%</b><span>WORLDS HELD</span></div><div><b>'+s.choices+'</b><span>CHOICES</span></div><div><b>'+s.daring+'</b><span>DARING</span></div>';
$('#rmx').href=$('#rmx2').href=P.remix;const lines=P.lines||[...new Set(F.ph.map(p=>p[2]))];$('#poem').innerHTML=lines.map(l=>'<div>'+e(l)+'</div>').join('');
if(F.audioData)au.src=F.audioData;else if(F.audio&&F.audio.url)au.src=F.audio.url;else off=0;$('#snd').textContent='FILM SOUND '+(snd?'ON':'OFF');
$('#bar').innerHTML=F.cut.map(c=>'<i style="flex:'+Math.max(.1,c.t1-c.t0)+' 1 0;background:'+((c.els[0]||[])[1]||'#555')+';opacity:.35"></i>').join('');
function ld(v,u,a){if(v.dataset.u!==u){v.dataset.u=u;v.src=u}const x=()=>{try{v.currentTime=a}catch(r){}};v.readyState>=1?x():v.addEventListener('loadedmetadata',x,{once:!0})}
function show(c,a,i){const n=1-on;ld(V[n],c.v,a);V[n].playbackRate=P.calm?.8:1;L.forEach(l=>l.style.setProperty('--d',dur+'s'));L[n].className='lay in';L[on].className='lay out';V[n].muted=!snd;if(run)V[n].play().catch(()=>{});const w=on;on=n;setTimeout(()=>{if(on!==n)return;L[n].className='lay cur';L[w].className='lay';V[w].pause()},dur*1e3+60);
$('#dna').innerHTML='<span>'+c.els.map(x=>'<span class="el" style="background:'+x[1]+'" title="'+e(x[2])+'">'+x[0]+'</span>').join(' ')+'</span><span>'+e(c.cap)+'</span><span class="ed">'+e(c.edit)+'</span>';
[...$('#bar').children].forEach((b,j)=>b.style.opacity=j<i?.6:j===i?1:.25)}
function frame(){const i=F.cut.findIndex(c=>t>=c.t0&&t<c.t1);if(i>=0&&i!==shown){shown=i;show(F.cut[i],F.cut[i].in+Math.max(0,t-F.cut[i].t0),i)}const li=F.ph.findIndex(p=>t>=p[0]&&t<p[1]);
if(li>=0&&li!==ls){ls=li;const tx=F.ph[li][2];$('#say').innerHTML=tx.split(/(\\s+)/).map((w,k)=>/^\\s+$/.test(w)?w:'<span style="animation-delay:'+k*45+'ms">'+e(w)+'</span>').join('');[...$('#poem').children].forEach(d=>d.className=d.textContent===tx||tx.indexOf(d.textContent)===0||d.textContent.indexOf(tx)>=0?'now':'')}
const v=V[on];if(run){if(v.ended||(v.duration&&v.currentTime>=v.duration-.12))v.pause();else if(v.paused&&v.readyState>=2)v.play().catch(()=>{})}}
setInterval(()=>{if(!run)return;const n=performance.now();if(au.src&&!au.paused)t=au.currentTime+off;else t+=(n-last)/1e3;last=n;if(t>=F.T1){run=!1;au.pause();V.forEach(v=>v.pause());t=F.T0;shown=-1;ls=-1;$('#go').hidden=!1;$('#watch').textContent='WATCH AGAIN';return}frame()},40);
function play(){run=!0;last=performance.now();$('#go').hidden=!0;if(au.src){try{au.currentTime=Math.max(0,t-off)}catch(r){}au.play().catch(()=>{})}frame();V[on].play().catch(()=>{});$('#pp').textContent='PAUSE'}
function pause(){run=!1;au.pause();V.forEach(v=>v.pause());$('#pp').textContent='PLAY'}
$('#watch').onclick=play;$('#pp').onclick=()=>run?pause():play();$('#snd').onclick=()=>{snd=!snd;V[on].muted=!snd;$('#snd').textContent='FILM SOUND '+(snd?'ON':'OFF')};frame();<\/script></body></html>`;
  window.MPExport = { project, file, mp4, link, read, score, menu, pack, unpack, abs, PUBLIC };
})();
