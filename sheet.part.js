function bar(s, e){
  const c = domVar(s.n), a = domVar(e.alt);
  const hatch = Math.max(0, e.conf - e.shot);
  return `<div class="bar" title="${e.shot}% from the shot alone · ${e.conf}% in context · ${S[e.alt].symbol} ${e.alt_conf}%">
    <span style="width:${e.shot}%;background:${c}"></span>
    <span class="hatch" style="width:${hatch}%;--c:${c}"></span>
    <span style="width:${e.alt_conf}%;background:${a};opacity:.85"></span></div>`;
}
const pct = (sym, v, n) => `<span class="pct" style="background:${domVar(n)}">${esc(sym)} ${v}</span>`;
let curEx = [], insIdx = -1;

function openSign(n){
  cur = n; insIdx = -1; const s = S[n]; const {c} = colOf[n];
  const ex = curEx = s.examples||[]; const d = s.diff||{};
  const sound = n==="34b";
  sheet.innerHTML = `
  <div class="shead">
    <div class="el ${c.dom}"><span class="num">${n}</span><span class="sym">${esc(s.symbol)}</span></div>
    <div><h2>${esc(s.name)}</h2><div class="sub">${esc(s.gloss)} · ${c.img} ${c.code} · ${esc(s.position)}</div></div>
    <div class="nav"><button class="ghost" data-go="-1" aria-label="previous sign">←</button><button class="ghost" data-go="1" aria-label="next sign">→</button><button class="ghost close" aria-label="close">×</button></div>
  </div>
  <div class="sbody2">
    <div class="lead"><span class="lab">The test</span> ${esc(d.difference)}</div>
    <div class="shots2">${ex.map((e,i)=>`
      <figure class="card" data-i="${i}" tabindex="0" aria-label="inspect shot ${i+1}">
        <div class="frame">
          <img alt="" src="${esc(e.thumb)}">
          <video muted loop playsinline preload="none" data-src="${esc(e.video)}" data-off="${Math.max(0,e.match-e.start).toFixed(2)}"></video>
          ${e.conf!=null?`<span class="badge">${pct(s.symbol, e.conf, n)}</span>`:""}
        </div>
        <figcaption>
          <div class="why">${esc(e.note)}</div>
          ${e.conf!=null?bar(s,e)+`<div class="readout">else ${esc(S[e.alt].symbol)} ${e.alt_conf}% · shot alone ${e.shot}%</div>`:""}
        </figcaption>
      </figure>`).join("")}</div>
    <div class="hint">${sound?"Click a shot to inspect it and hear it. Each has an audio track; its content is not yet verified by listening.":"Hover to play · click a shot to inspect its reading."} Bar: <i class="sw" style="background:${domVar(n)}"></i>shot alone <i class="sw" style="background:repeating-linear-gradient(135deg,${domVar(n)} 0 3px,transparent 3px 6px)"></i>if the sequence cooperates <i class="sw" style="background:var(--rule)"></i>rival / unassigned</div>

    <details class="sec" open><summary>Not to be confused with</summary>
      <div class="conf-grid">${(d.confusions||[]).map(x=>{const m=String(x.n);return `<div class="cf">
        <a data-open="${m}">${chip(m)}<b>${esc(S[m]?.name||x.name)}</b></a>
        <div class="flip">${esc(x.flip)}</div><div class="why">${esc(x.why_not)}</div></div>`}).join("")}</div>
      <p class="small"><b>Counterfeit.</b> ${esc(d.counterfeit)}</p>
    </details>
    <details class="sec"><summary>Confidence · ceiling ${d.single_shot_ceiling}%</summary>
      <div class="rubric">
        <b>High</b><span>${esc(d.confidence?.high)}</span>
        <b>Medium</b><span>${esc(d.confidence?.medium)}</span>
        <b>Low</b><span>${esc(d.confidence?.low)}</span>
        <b>Ceiling</b><span>A single isolated shot can carry at most ${d.single_shot_ceiling}% of this sign.${d.single_shot_ceiling<=20?" The rest has to come from the sequence or the whole film.":""}</span>
      </div>
      <p class="small">Axis · ${esc(d.axis)}${d.deamer_anchor?`<br>Anchor · ${esc(d.deamer_anchor)}`:""}</p>
    </details>
    <details class="sec"><summary>Definition · question · operation</summary>
      <p>${esc(s.definition)}</p>
      ${s.deamer_quote?`<div class="quote">“${esc(s.deamer_quote)}”</div>`:""}
      <p class="q">${esc(s.question)}</p>
      <p class="op">${esc(s.operation)}</p>
      ${s.fig?`<p class="small">Deamer, Fig. ${esc(s.fig)}</p>`:""}
    </details>
    <details class="sec"><summary>Deamer's case · ${esc(s.section3?.film)}</summary>
      <ul class="films">${(s.section3?.scenes||[]).map(f=>`<li>${esc(f)}</li>`).join("")}</ul>
    </details>
    <details class="sec"><summary>In Deleuze's Cinema books (recalled, unverified)</summary>
      <div class="caveat">Deamer's Section II names no films; these are recalled from <i>Cinema 1/2</i>. Check before citing.</div>
      <ul class="films">${(s.deleuze_examples||[]).map(f=>`<li>${esc(String(f).replace(/\s*\((cited by Deleuze|NOTE)[^)]*\)\s*$/,""))}</li>`).join("")}</ul>
    </details>
  </div>
  <div class="insp" id="insp" hidden></div>`;
  sheet.scrollTop = 0;
  sheet.querySelector(".close").onclick = () => dlg.close();
  sheet.querySelectorAll("[data-go]").forEach(b=>b.onclick=()=>step(+b.dataset.go));
  sheet.querySelectorAll("[data-open]").forEach(a=>a.onclick=()=>openSign(a.dataset.open));
  sheet.querySelectorAll(".card").forEach(f=>{
    const v=f.querySelector("video"), img=f.querySelector("img");
    v.src = v.dataset.src + "#t=" + v.dataset.off; v.preload="metadata";
    v.addEventListener("loadeddata", ()=>{ img.style.display="none"; }, {once:true});
    if(!sound){
      f.addEventListener("mouseenter",()=>v.play().catch(()=>{}));
      f.addEventListener("mouseleave",()=>{ v.pause(); v.currentTime=+v.dataset.off; });
    }
    const go=()=>inspect(+f.dataset.i);
    f.addEventListener("click",go);
    f.addEventListener("keydown",e=>{ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); go(); } });
  });
  if (!dlg.open) dlg.showModal();
  history.replaceState(null,"","#"+n);
}

function inspect(i){
  const box = document.getElementById("insp"); if(!box) return;
  sheet.querySelectorAll(".card video").forEach(v=>v.pause());
  if(i<0){ box.hidden=true; box.innerHTML=""; insIdx=-1; return; }
  insIdx = (i+curEx.length)%curEx.length;
  const s=S[cur], e=curEx[insIdx], d=s.diff||{};
  const rival = (d.confusions||[]).find(x=>String(x.n)===e.alt);
  box.hidden=false;
  box.innerHTML = `
    <div class="ibar">
      <span>${esc(s.symbol)} ${esc(s.name)} · shot ${insIdx+1} of ${curEx.length}</span>
      <span class="nav"><button class="ghost" data-si="-1" aria-label="previous shot">←</button><button class="ghost" data-si="1" aria-label="next shot">→</button><button class="ghost" data-si="x" aria-label="close shot">×</button></span>
    </div>
    <div class="igrid">
      <div class="istage">
        <video controls autoplay loop playsinline src="${esc(e.video)}#t=${Math.max(0,e.match-e.start).toFixed(2)}"></video>
        <div class="src"><a href="${esc(e.page)}" target="_blank" rel="noopener">${esc(e.title)}</a>${e.year?` (${e.year})`:""} · ${tc(e.start)}–${tc(e.end)} · ${(e.end-e.start).toFixed(1)}s shot · found by “${esc(e.query)}”</div>
      </div>
      <div class="iread">
        <div class="why big">${esc(e.note)}</div>
        ${e.conf!=null?`
        <div class="verdict">${pct(s.symbol, e.conf, cur)}<span>reads as <b>${esc(s.name)}</b></span></div>
        ${bar(s,e)}
        <dl>
          <dt>The test</dt><dd>${esc(d.difference)}</dd>
          <dt>From this shot alone</dt><dd>${e.shot}%. A single shot can carry at most ${d.single_shot_ceiling}% of this sign; the other ${Math.max(0,e.conf-e.shot)} points depend on the surrounding sequence.</dd>
          <dt>Rival reading</dt><dd><a data-open="${esc(e.alt)}">${chip(e.alt)} <b>${esc(S[e.alt].name)}</b></a> ${e.alt_conf}%. It would be that if ${esc(e.flip)}.
            ${rival?`<div class="small">${esc(rival.why_not)}</div>`:""}</dd>
          <dt>Unassigned</dt><dd>${Math.max(0,100-e.conf-e.alt_conf)}%: no single sign claims it.</dd>
        </dl>`:""}
      </div>
    </div>`;
  box.querySelectorAll("[data-si]").forEach(b=>b.onclick=()=>{ const v=b.dataset.si; v==="x"?inspect(-1):inspect(insIdx+ +v); });
  box.querySelectorAll("[data-open]").forEach(a=>a.onclick=()=>openSign(a.dataset.open));
  box.scrollTop = 0;
}

const step = d => openSign(ORDER[(ORDER.indexOf(cur)+d+ORDER.length)%ORDER.length]);
dlg.addEventListener("close",()=>{ sheet.querySelectorAll("video").forEach(v=>{v.pause();v.removeAttribute("src");v.load();}); history.replaceState(null,"",location.pathname); });
dlg.addEventListener("click",e=>{ if(e.target===dlg) dlg.close(); });
dlg.addEventListener("cancel",e=>{ if(insIdx>=0){ e.preventDefault(); inspect(-1); } });
document.addEventListener("keydown",e=>{
  if(!dlg.open) return;
  if(insIdx>=0){ if(e.key==="ArrowRight") inspect(insIdx+1); if(e.key==="ArrowLeft") inspect(insIdx-1); return; }
  if(e.key==="ArrowRight") step(1); if(e.key==="ArrowLeft") step(-1);
});
