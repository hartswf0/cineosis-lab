const DATA = /*DATA*/{};
const COLS = [
  {img:"Perception", code:"0", dom:"perception", signs:["1","2","3"]},
  {img:"Affection", code:"111", dom:"affect", signs:["4","5","6"]},
  {img:"Impulse", code:"211", dom:"action", signs:["7","8","9"]},
  {img:"Action · small", code:"221", dom:"action", signs:["10","11","12"]},
  {img:"Action · large", code:"222", dom:"action", signs:["13","14","15"]},
  {img:"Attraction", code:"311", dom:"reflection", signs:["16","17","18"]},
  {img:"Inversion", code:"321", dom:"reflection", signs:["19","20","21"]},
  {img:"Discourse", code:"322", dom:"reflection", signs:["22","23","24"]},
  {img:"Dream", code:"331", dom:"mental", signs:["25","26","27"]},
  {img:"Recollection", code:"332", dom:"mental", signs:["28","29","30"]},
  {img:"Relation", code:"333", dom:"mental", signs:["31","32","33"]},
  {img:"Opsign · Sonsign", code:"0", dom:"break", signs:["34a","34b"]},
  {img:"Hyalosign", code:"1", dom:"time", signs:["35","36","37"]},
  {img:"Chronosign", code:"2", dom:"time", signs:["38","39","40"]},
  {img:"Noosign", code:"3", dom:"time", signs:["41","42","43"]},
  {img:"Lectosign", code:"∞", dom:"read", signs:["44"]},
];
const DOMS = {perception:"Perception · zeroness", affect:"Affect · Firstness", action:"Action · Secondness", reflection:"Thought · reflection-images", mental:"Thought · mental-images", break:"Opsign & sonsign · zeroness", time:"Time-images proper", read:"Lectosign"};
const S = Object.fromEntries(DATA.signs.map(s=>[s.n,s]));
const ORDER = DATA.signs.map(s=>s.n);
const colOf = {}; COLS.forEach((c,i)=>c.signs.forEach((n,r)=>colOf[n]={c,i,r}));
const domVar = n => `var(--${colOf[n].c.dom})`;
const esc = t => String(t??"").replace(/[&<>"]/g, m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
const tc = s => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,"0")}`;
const chip = n => `<span class="chip" style="background:${domVar(n)}">${esc(S[n].symbol)}</span>`;

document.getElementById("legend").innerHTML = Object.entries(DOMS).map(([k,v])=>`<span><i class="${k}"></i>${v}</span>`).join("");

const T = document.getElementById("table");
const add = (html, style="") => { const d=document.createElement("div"); d.innerHTML=html; const el=d.firstElementChild; if(style) el.style.cssText=style; T.appendChild(el); return el; };
add(`<div class="band"></div>`, "grid-column:1");
add(`<div class="band">Movement-image</div>`, "grid-column:2 / span 11");
add(`<div class="band">Time-image</div>`, "grid-column:13 / span 5");
add(`<div class="band dom"></div>`, "grid-column:1");
[["0 · perception",1],["I · affect",1],["II · action",3],["III · thought",6],["0",1],["1 · 2 · 3",3],["∞",1]].reduce((col,[t,span])=>{add(`<div class="band dom">${t}</div>`, `grid-column:${col} / span ${span}`);return col+span;},2);
add(`<div class="colh"></div>`);
COLS.forEach(c=>add(`<div class="colh"><b>${c.img}</b>${c.code}</div>`));
const ROWS = ["Composition I","Composition II","Genesis"];
const tiles = {};
for (let r=0;r<3;r++){
  add(`<div class="rowh">${ROWS[r]}</div>`, `grid-row:${4+r};grid-column:1`);
  COLS.forEach((c,i)=>{
    const n = c.signs[r];
    if (n===undefined) return;
    const s = S[n]; const tall = c.dom==="read";
    const strip = (s.examples||[]).slice(0, tall?4:3).map(e=>`<img loading="lazy" alt="" src="${esc(e.thumb)}">`).join("");
    const ceil = s.diff?.single_shot_ceiling;
    const code = c.dom==="break" ? (n==="34a"?"optical":"sound") : c.code+(tall?"":"·"+(r+1));
    const b = add(`<button class="tile ${c.dom}${tall?" tall":""}" data-n="${n}" aria-label="${n} ${esc(s.name)}">
      <span class="num">${n}</span><span class="code">${code}</span>
      <span class="sym">${esc(s.symbol)}</span><span class="nm">${esc(s.name)}</span>
      <span class="mass" title="mean reading across its shots · ceiling for any single shot">${s.mean_conf??"–"} · ⌈${ceil??"–"}</span>
      <span class="strip">${strip}</span></button>`, `grid-row:${4+r}${tall?" / span 3":""};grid-column:${i+2}`);
    b.onclick = () => openSign(n);
    b.onmouseenter = b.onfocus = () => focusSign(n);
    b.onmouseleave = b.onblur = () => focusSign(null);
    tiles[n] = b;
  });
}
add(`<div class="zero"><b>0</b> · the two actual slivers, seen and heard, from which the time-image is composed</div>`);
function focusSign(n){
  T.classList.toggle("focus", !!n);
  Object.values(tiles).forEach(t=>t.classList.remove("hl","src"));
  if(!n) return;
  tiles[n].classList.add("src");
  (S[n].diff?.confusions||[]).forEach(c=>tiles[String(c.n)]?.classList.add("hl"));
}

const dlg = document.getElementById("dlg"), sheet = document.getElementById("sheet");
let cur = null;
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
    // the still is the frame the reading was made from; video only while hovering
    v.style.visibility="hidden";
    if(!sound){
      f.addEventListener("mouseenter",()=>{ if(!v.src){ v.src=v.dataset.src; } v.style.visibility="visible"; v.play().catch(()=>{}); });
      f.addEventListener("mouseleave",()=>{ v.pause(); v.style.visibility="hidden"; });
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
        <video controls autoplay loop playsinline src="${esc(e.video)}#t=${(e.read_t ?? Math.max(0,e.match-e.start)).toFixed(2)}"></video>
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
const h = decodeURIComponent(location.hash.slice(1)); if (S[h]) openSign(h);
