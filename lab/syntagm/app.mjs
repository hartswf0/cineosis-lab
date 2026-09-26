import {TYPES,QUESTIONS,emptyReading,timeline,suggest,coverage,metrics,reorder,validate,toEDL} from './model.mjs';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clone=o=>JSON.parse(JSON.stringify(o)), video=$('#video'), KEY='cineosis.syntagm.v1';
const colors={A:'#6b8a72',B:'#bc684e',C:'#6b8dba','':'#a6aaa0'};
const family={perception:'#829786',affect:'#cca481',action:'#bac07d',reflection:'#9cb7c8',mental:'#b2a1c3',break:'#dba593',time:'#90b8b0',read:'#b7b8c9'};
let D,shots={},doc,original,history=[],selected=0,playing=false,comparing=false,loadedId=null,sourceToken=0,loadToken=0,frame=0,pendingSeek=null;
let pool=[],currentSource=null,selectedSign=null,storageOK=true,statusTimer;
const sources=new Map();
const fmt=t=>`${Math.floor(t/60)}:${(t%60).toFixed(1).padStart(4,'0')}`;
const name=t=>TYPES.find(x=>x[0]===t)?.[1]||'Unresolved';
function status(s){$('#status').textContent=s;$('#status').title=s;$('#status').classList.add('visible');clearTimeout(statusTimer);statusTimer=setTimeout(()=>$('#status').classList.remove('visible'),5000);}
function saved(){try{return JSON.parse(localStorage.getItem(KEY)||'[]');}catch{return [];}}
function writeSaved(rows){try{localStorage.setItem(KEY,JSON.stringify(rows));return true;}catch{storageOK=false;status('Could not save. Export JSON to keep this passage.');return false;}}
function uid(){return crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random().toString(36).slice(2)}`;}
async function json(url){const r=await fetch(url);if(!r.ok)throw Error(`${url}: HTTP ${r.status}`);return r.json();}
function stop(){playing=false;video.pause();cancelAnimationFrame(frame);$('#play').textContent='Play';$('#bigPlay').hidden=false;}
function workingItems(){return comparing?original.items:doc.items;}
function snapshot(){history.push(clone(doc));if(history.length>40)history.shift();$('#undo').disabled=false;}
function change(fn,label){stop();if(comparing){comparing=false;selected=0;}snapshot();fn();doc.revision++;doc.reading.status='needs-review';doc.history.push({operation:label,revision:doc.revision,at:new Date().toISOString()});selected=Math.min(selected,doc.items.length-1);render();show(selected);status(label+' · reading needs review');}
function restore(d){validate(d,shots);stop();doc=clone(d);doc.reading={...emptyReading(),...d.reading,answers:{...emptyReading().answers,...d.reading?.answers}};doc.history=Array.isArray(d.history)?d.history:[];doc.revision=Number.isInteger(d.revision)?d.revision:0;original=clone(doc);history=[];comparing=false;selected=0;loadedId=null;render();show(0);$('#undo').disabled=true;}
function make(items,title,context,offset=0){restore({format:'cineosis-syntagm/1',id:uid(),title,context,offset,revision:0,items,reading:emptyReading(),history:[]});}
function linkedPassage(){
  const q=new URLSearchParams(location.search),cut=q.get('cut'),a=Number(q.get('start')),b=Number(q.get('end'));
  if(!D.cuts[cut]||!q.has('start')||!q.has('end')||!Number.isFinite(a)||!Number.isFinite(b)||a<0||b<=a)return false;
  const ps=D.cuts[cut].patches.filter(p=>p.record[1]>a&&p.record[0]<b);if(!ps.length||ps.length>100)return false;
  $('#origin').value=cut;fillChapters();$('#chapter').value=ps[0].chapter;
  const offset=Math.max(a,ps[0].record[0]);
  make(ps.map(p=>{const lo=Math.max(a,p.record[0]),hi=Math.min(b,p.record[1]);return occurrence(p.shotId,p.in+lo-p.record[0],p.in+hi-p.record[0],{originalRecord:[lo,hi],words:p.words});}),
    `${ps[0].title} · ${D.cuts[cut].title}`,{kind:'edit',cut,chapter:ps[0].chapter,boundaries:'candidate beat imported from Grand Syntagmatique',requestedInterval:[a,b]},offset);
  status('Passage transferred; establish its reading from evidence');return true;
}
function occurrence(shotId,a,b,extra={}){return {id:uid(),shotId,in:a,out:b,strand:'',...extra};}
function safeMedia(s){if(!s)return '';const u=new URL(s,location.href);if(!['http:','https:'].includes(u.protocol))throw Error('Media must use HTTP or HTTPS.');return u.href;}
function shotURL(s){return safeMedia(s.clip||s.video);}
function fillChapters(){
  const key=$('#origin').value;
  $('#chapter').disabled=!D.cuts[key];
  if(D.cuts[key]){
    const seen=new Map(D.cuts[key].patches.map(p=>[p.chapter,p.title]));
    $('#chapter').innerHTML=[...seen].map(([k,v])=>`<option value="${esc(k)}">${esc(k+' · '+v)}</option>`).join('');
  }else $('#chapter').innerHTML='<option>Source order</option>';
  $('#from').value=1;
}
async function getSource(slug){
  if(sources.has(slug))return sources.get(slug);
  const meta=D.sources.find(s=>s.slug===slug);if(!meta)throw Error('No cached source manifest for this film. Use its archive page to inspect context.');
  const s=await json(meta.path);
  for(const c of s.clips){
    const old=shots[c.id]||{};
    shots[c.id]={id:c.id,title:c.sourceTitle,year:c.sourceYear,slug:c.sourceSlug,
      start:c.startSeconds,end:c.endSeconds,position:c.position,video:c.videoUrl,
      thumb:c.thumbnailUrl,page:`https://www.movingimagearchive.com/sources/${encodeURIComponent(c.sourceSlug)}?clip=${encodeURIComponent(c.id)}`,...old};
  }
  sources.set(slug,s);return s;
}
async function load(){
  const token=++loadToken;$('#load').disabled=true;status('Loading passage…');
  try{
    const key=$('#origin').value,from=Math.max(0,Math.floor(Number($('#from').value)||1)-1),count=Math.min(24,Math.max(1,Math.floor(Number($('#count').value)||6)));
    if(D.cuts[key]){
      const ps=D.cuts[key].patches.filter(p=>p.chapter===$('#chapter').value);pool=ps;
      const subset=ps.slice(from,from+count);if(!subset.length)throw Error(`Start must be between 1 and ${ps.length}.`);
      if(token!==loadToken)return;
      const groups=[...new Set(subset.map(p=>shots[p.shotId].slug))];
      make(subset.map(p=>occurrence(p.shotId,p.in,p.out,{originalRecord:p.record,words:p.words,strand:groups.indexOf(shots[p.shotId].slug)%2?'B':'A'})),`${subset[0].title} · ${D.cuts[key].title}`,{kind:'edit',cut:key,chapter:subset[0].chapter,boundaries:'user-selected candidate window',strandBasis:'initial A/B groups partition source films; edit these before interpreting'},subset[0].record[0]);
      status('A/B seeded by source film; review their meaning');
    }else{
      const slug=key.slice(7),s=await getSource(slug);if(token!==loadToken)return;
      currentSource=s;pool=s.clips;const subset=s.clips.slice(from,from+count);if(!subset.length)throw Error(`Start must be between 1 and ${s.clips.length}.`);
      make(subset.map(c=>occurrence(c.id,0,c.endSeconds-c.startSeconds,{strand:'A'})),`${subset[0].sourceTitle} · source passage`,{kind:'source',slug,boundaries:'archive clip boundaries; unverified shots'},0);
      status('Source order loaded; shot boundaries unverified');
    }
  }catch(e){status(e.message);}finally{if(token===loadToken)$('#load').disabled=false;}
}
function render(){
  const items=workingItems();$('#passageTitle').textContent=doc.title;
  $('#version').textContent=comparing?'Original arrangement':doc.revision?`Your arrangement · revision ${doc.revision}`:'Original arrangement';
  $('#compare').textContent=comparing?'Return to your edit':'Compare original';$('#compare').classList.toggle('on',comparing);
  $('#ribbon').innerHTML=timeline(items).map((x,i)=>{const s=shots[x.shotId];return `<button class="tile ${i===selected?'active':''}" data-index="${i}" style="flex-grow:${Math.min(20,x.out-x.in)};--strand:${colors[x.strand]||'#9c93ad'}" aria-label="Shot ${i+1}: ${esc(s.title)}"><img src="${esc(s.thumb||'')}" alt="" loading="lazy"><span>${i+1} · ${esc(x.strand||'?')}</span><small>${(x.out-x.in).toFixed(1)}s</small></button>`;}).join('');
  $('#scrub').max=metrics(items,shots).duration;renderOccurrence();renderMeasures();renderReading();renderTable();
  $$('[data-op]').forEach(b=>b.disabled=comparing);$('#offset').value=doc.offset;
}
function renderOccurrence(){
  const item=workingItems()[selected],s=shots[item.shotId];
  $('#occurrence').innerHTML=`<div class="occ-title">${selected+1}. ${esc(s.title)}${s.year?' · '+esc(s.year):''}</div><div class="trim-row"><label>Clip in / s<input id="trimIn" type="number" step="0.04" min="0" value="${item.in.toFixed(3)}" ${comparing?'disabled':''}></label><label>Clip out / s<input id="trimOut" type="number" step="0.04" min="0" value="${item.out.toFixed(3)}" ${comparing?'disabled':''}></label><label>Strand<select id="strand" ${comparing?'disabled':''}>${['','A','B','C'].map(v=>`<option value="${v}" ${item.strand===v?'selected':''}>${v||'Unassigned'}</option>`).join('')}</select></label><button id="trim" ${comparing?'disabled':''}>Apply</button></div><div class="move-row"><button id="left" ${selected===0||comparing?'disabled':''}>Move ←</button><button id="right" ${selected===doc.items.length-1||comparing?'disabled':''}>Move →</button><button id="duplicate" ${comparing||doc.items.length>=100?'disabled':''}>Duplicate</button><button id="remove" ${doc.items.length===1||comparing?'disabled':''}>Remove</button></div><p class="hint">Source ${fmt(s.start+item.in)}–${fmt(s.start+item.out)} · clip length ${(s.end-s.start).toFixed(2)}s. Story time unresolved.</p>`;
  $('#strand').onchange=e=>change(()=>{doc.items[selected].strand=e.target.value;},'Strand changed');
  $('#trim').onclick=()=>{const a=Number($('#trimIn').value),b=Number($('#trimOut').value);if(!Number.isFinite(a)||!Number.isFinite(b)||a<0||b<=a||b>s.end-s.start+.001){status('Trim must be inside the clip, with out after in.');return;}change(()=>{doc.items[selected].in=a;doc.items[selected].out=b;},'Trim changed');};
  $('#left').onclick=()=>change(()=>{[doc.items[selected-1],doc.items[selected]]=[doc.items[selected],doc.items[selected-1]];selected--;},'Moved left');
  $('#right').onclick=()=>change(()=>{[doc.items[selected+1],doc.items[selected]]=[doc.items[selected],doc.items[selected+1]];selected++;},'Moved right');
  $('#duplicate').onclick=()=>change(()=>doc.items.splice(selected+1,0,{...clone(doc.items[selected]),id:uid()}),'Duplicated occurrence');
  $('#remove').onclick=()=>change(()=>doc.items.splice(selected,1),'Removed occurrence');
}
function renderMeasures(){
  const m=metrics(workingItems(),shots),pairs=Math.max(0,workingItems().length-1);
  $('#measurements').innerHTML=`<div>${m.duration.toFixed(1)}s<small>screen duration</small></div><div>${m.sameSource}/${pairs}<small>same-source joins</small></div><div>${m.adjacent}/${pairs}<small>touching source intervals</small></div><div>${m.switches}<small>assigned strand switches</small></div>`;
  $('#joins').innerHTML=m.joins.map((j,i)=>`<div class="join ${j.kind}">${i+1} → ${i+2} · ${esc(j.label)}</div>`).join('')||'<p class="hint">One occurrence: no cut relations to measure.</p>';
}
function renderReading(){
  const r=doc.reading;
  for(const id of ['intended','rival','scope','evidence','counterevidence','analyst'])$('#'+id).value=r[id]||'';
  $('#readingType').value=r.type;
  for(const q of QUESTIONS)$(`[data-question="${q[0]}"]`).value=r.answers[q[0]];
  $('#reviewStatus').textContent=r.status;
  const proposal=suggest(r,doc.items.length);$('#suggestion').textContent='Proposed: '+name(proposal.type);$('#suggestionReason').textContent=proposal.reason;
  $('#useSuggestion').disabled=proposal.type==='unknown'||comparing;
  $('#read').querySelectorAll('input,select,textarea,button').forEach(e=>{if(e.id!=='useSuggestion')e.disabled=comparing;});
}
function bindReadings(){
  const opts=TYPES.map(([k,n])=>`<option value="${k}">${n}</option>`).join('');
  for(const id of ['intended','readingType','rival'])$('#'+id).innerHTML=opts;
  $('#questions').innerHTML=QUESTIONS.map(([key,label,options])=>`<label>${label}<select data-question="${key}">${options.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select></label>`).join('');
  $('#typeGuide').innerHTML=TYPES.slice(1).map(([,n,d])=>`<p><b>${n}</b>${d}</p>`).join('');
  for(const el of $$('#read select,#read textarea,#read input'))el.onchange=()=>{
    snapshot();const r=doc.reading;if(el.dataset.question)r.answers[el.dataset.question]=el.value;else r[el.id==='readingType'?'type':el.id]=el.value;
    r.status='needs-review';renderReading();status('Reading edited; Save to keep it');
  };
  $('#useSuggestion').onclick=()=>{snapshot();doc.reading.type=suggest(doc.reading,doc.items.length).type;doc.reading.status='needs-review';renderReading();};
  $('#review').onclick=()=>{if(!doc.reading.evidence.trim()||!doc.reading.analyst.trim()){status('Add evidence and a reader before marking reviewed.');return;}
    if(doc.reading.type!=='unknown'&&doc.reading.answers.autonomy!=='yes'){status('A Metz type needs an autonomy judgement; use Unresolved for fragments.');return;}
    snapshot();doc.reading.status='reviewed';doc.reading.reviewedAt=new Date().toISOString();doc.reading.reviewedRevision=doc.revision;renderReading();status('Reviewed by '+doc.reading.analyst+' · Save to keep it');};
}
function renderTable(){
  const items=workingItems(),duration=metrics(items,shots).duration,weights={};let measured=0;
  for(const x of items){const s=shots[x.shotId],dt=x.out-x.in;if(s.aff_top?.length){measured+=dt;for(const [n,v] of s.aff_top)weights[n]=(weights[n]||0)+v*dt;}}
  const max=Math.max(1,...Object.values(weights));
  $('#periodic').innerHTML=D.signs.map(s=>`<button class="element ${selectedSign===s.n?'selected':''}" data-sign="${esc(s.n)}" style="grid-column:${s.col+1};grid-row:${s.row+1};--family:${family[s.dom]||'#aaa'};--heat:${Math.round(10+75*(weights[s.n]||0)/max)}%" title="${esc(s.symbol+' · '+s.name)}" aria-label="${esc(s.symbol+' · '+s.name)}">${esc(s.symbol)}</button>`).join('');
  $('#periodic').dataset.coverage=`${duration?Math.round(100*measured/duration):0}%`;
  if(selectedSign)showSign(selectedSign);else $('#signDetail').textContent=`Select a sign. Shading is relative duration-weighted top-eight machine affinity, available for ${duration?Math.round(100*measured/duration):0}% of passage seconds. Unlisted affinity values are omitted, not zero.`;
}
function showSign(n){
  selectedSign=n;$$('.element').forEach(b=>b.classList.toggle('selected',b.dataset.sign===n));
  const s=D.signs.find(x=>x.n===n),readings=workingItems().flatMap((x,i)=>(shots[x.shotId].signs||[]).filter(r=>r.n===n).map(r=>`${i+1}: ${r.note}`));
  $('#signDetail').innerHTML=`<b>${esc(s.symbol+' · '+s.name)}</b>${esc(s.difference)}<p class="hint">Single-shot ceiling: ${s.ceiling}%. Affinity coverage: ${$('#periodic').dataset.coverage} of passage seconds; shading is a retrieval cue, not a reading.</p>${readings.map(r=>`<p>${esc(r)}</p>`).join('')||'<p>No editor reading for this sign in this passage.</p>'}`;
  const examples=D.readIds.map(id=>shots[id]).filter(s=>s?.signs?.some(r=>r.n===n)).slice(0,6);
  $('#examples').innerHTML=examples.map(s=>`<button class="example" data-add="${esc(s.id)}" ${comparing?'disabled':''} title="Append an occurrence of ${esc(s.title)}"><img src="${esc(s.thumb)}" alt=""><span>+ ${esc(s.title)}</span></button>`).join('');
}
function addShot(id){
  if(doc.items.length>=100){status('Passage limit: 100 occurrences.');return;}
  const s=shots[id];if(!s)return;
  change(()=>{doc.items.push(occurrence(id,0,Math.min(8,s.end-s.start)));selected=doc.items.length-1;},'Appended excerpt');
}
async function inspectSource(){
  const token=++sourceToken,s=shots[workingItems()[selected].shotId];$('#sourceContext').textContent='Loading original neighborhood…';
  try{
    const source=await getSource(s.slug);if(token!==sourceToken)return;
    const c=coverage(source.clips),i=source.clips.findIndex(x=>x.id===s.id),neighbors=i>=0?source.clips.slice(Math.max(0,i-2),i+3):[];
    $('#sourceContext').innerHTML=`<div class="coverage">${source.clips.length} cached clips · ${c.ratio===null?'unknown':(100*c.ratio).toFixed(1)+'%'} coverage of the cached first-to-last interval.<br>${c.gaps.length} missing intervals. These are retrieval gaps, not established story ellipses.</div><p>${esc((source.synopsis||'').replace(/\\n/g,' '))}</p>${i<0?'<p class="warning">Selected clip is absent from this manifest.</p>':''}${neighbors.map(n=>`<div class="neighbor"><span>${n.id===s.id?'● ':''}#${n.position} · ${fmt(n.startSeconds)}–${fmt(n.endSeconds)}</span><button data-neighbor="${n.id}" ${comparing?'disabled':''}>Append</button></div>`).join('')}<p class="hint">Append to inspect or reassemble a neighbor. Trims remain clip-relative. No claim of diegetic continuity is made.</p>`;
  }catch(e){if(token===sourceToken)$('#sourceContext').textContent=e.message;}
}
function show(i,relative=0,keepPlaying=false){
  const items=workingItems();if(i<0||i>=items.length)return;
  if(!keepPlaying)stop();selected=i;const x=items[i],s=shots[x.shotId];
  $('#position').textContent=`${i+1} / ${items.length} · strand ${x.strand||'?'}`;
  $('#sourceLink').textContent=s.title;$('#sourceLink').href=safeMedia(s.page||`https://www.movingimagearchive.com/sources/${encodeURIComponent(s.slug)}`);
  $('#mediaError').hidden=true;$('#bigPlay').hidden=keepPlaying;
  const target=x.in+Math.min(Math.max(0,relative),x.out-x.in-.001),key=x.id+':'+x.in+':'+x.out+':'+comparing;
  const seek=()=>{if(loadedId!==key)return;pendingSeek={key,target};video.currentTime=target;if(keepPlaying)video.play().catch(failPlay);};
  if(loadedId!==key){loadedId=key;video.onloadedmetadata=seek;video.dataset.fallback='0';video.poster=safeMedia(s.thumb);video.src=shotURL(s);video.load();}
  else if(video.readyState>=1)seek();else video.onloadedmetadata=seek;
  $$('.tile').forEach((b,k)=>b.classList.toggle('active',k===selected));
  renderOccurrence();updateClock(target);sourceToken++;$('#sourceContext').textContent='Inspect this shot’s original neighborhood and source coverage.';
  if(keepPlaying)tick();
}
function failPlay(e){stop();$('#mediaError').hidden=false;$('#mediaReason').textContent=e?.message||'The browser could not start playback. Try again or open the source link.';}
video.onseeked=()=>{if(!pendingSeek||pendingSeek.key!==loadedId)return;const target=pendingSeek.target;pendingSeek=null;
  if(Math.abs(video.currentTime-target)>.15)failPlay(Error('The media server did not honor this in-point. Use the Cineosis local server or the hosted site, which support byte-range seeking.'));
};
video.onerror=()=>{
  const s=shots[workingItems()?.[selected]?.shotId];
  if(s?.clip&&s.video&&video.dataset.fallback==='0'){video.dataset.fallback='1';video.src=safeMedia(s.video);video.load();return;}
  failPlay(Error('Media unavailable here. The source link remains available; Retry or Next clip to continue.'));
};
function updateClock(t=video.currentTime){
  if(!doc)return;const items=workingItems(),x=items[selected],row=timeline(items)[selected],relative=Math.max(0,Math.min(x.out-x.in,t-x.in));
  $('#scrub').value=row.rec[0]+relative;$('#clock').textContent=`${fmt(row.rec[0]+relative)} / ${fmt(metrics(items,shots).duration)}`;
  const s=shots[x.shotId];$('#sourceTime').textContent=`source ${fmt(s.start+x.in+relative)} · edit ${fmt(doc.offset+row.rec[0]+relative)}`;
}
function advance(){const items=workingItems();if(selected+1<items.length)show(selected+1,0,true);else{stop();updateClock(items[selected].out);}}
function tick(){cancelAnimationFrame(frame);if(!playing)return;const x=workingItems()[selected];updateClock();if(video.readyState>=2&&video.currentTime>=x.out-.035){advance();return;}frame=requestAnimationFrame(tick);}
video.onended=()=>{if(playing)advance();};
video.ontimeupdate=()=>{if(!playing)updateClock();};
function play(){if(playing){stop();return;}playing=true;$('#play').textContent='Pause';$('#bigPlay').hidden=true;const x=workingItems()[selected];if(video.currentTime>=x.out-.04){show(0,0,true);}else{video.play().catch(failPlay);tick();}}
function download(file,obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=file;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function packed(){const ids=new Set(doc.items.map(x=>x.shotId));return {...clone(doc),shots:Object.fromEntries([...ids].map(id=>[id,shots[id]]))};}
function save(){
  const rows=saved().filter(r=>r.id!==doc.id);rows.unshift({...packed(),savedAt:new Date().toISOString()});
  if(writeSaved(rows.slice(0,30))){status('Saved in this browser');renderSaved();}
}
function renderSaved(){
  $('#saved').innerHTML=saved().map(d=>`<div><span>${esc(d.title)}<small> · ${d.items.length} shots · ${esc(d.reading?.type||'unknown')}</small></span><button data-saved="${esc(d.id)}">Open</button></div>`).join('')||'<p>No saved passages yet.</p>';
}
function importDoc(d){
  const candidate={...shots};
  for(const [id,s] of Object.entries(d.shots||{})){
    if(!s||s.id!==id||!Number.isFinite(s.start)||!Number.isFinite(s.end)||s.end<=s.start)throw Error('Invalid source record.');
    for(const f of ['video','clip','thumb','page'])if(s[f])safeMedia(s[f]);candidate[id]=s;
  }
  validate(d,candidate);shots=candidate;restore(d);status('Imported passage; source records preserved');
}
function wire(){
  $('#origin').onchange=fillChapters;$('#load').onclick=load;
  $('#chapter').onchange=()=>{$('#from').value=1;};
  $('#ribbon').onclick=e=>{const b=e.target.closest('[data-index]');if(b)show(Number(b.dataset.index));};
  $('#play').onclick=play;$('#bigPlay').onclick=play;$('#prev').onclick=()=>show(Math.max(0,selected-1));$('#next').onclick=()=>show(Math.min(workingItems().length-1,selected+1));
  $('#retry').onclick=()=>{loadedId=null;show(selected);play();};$('#skip').onclick=()=>{show(Math.min(workingItems().length-1,selected+1));};
  $('#sound').onclick=()=>{video.muted=!video.muted;$('#sound').textContent=video.muted?'Sound off':'Source sound';$('#sound').setAttribute('aria-pressed',String(!video.muted));};
  $('#scrub').oninput=()=>{const t=Number($('#scrub').value),rows=timeline(workingItems()),i=rows.findIndex(r=>t<r.rec[1]);const k=i<0?rows.length-1:i;show(k,t-rows[k].rec[0]);};
  $$('[data-op]').forEach(b=>b.onclick=()=>{const seed=doc.revision+1;change(()=>{doc.items=reorder(doc.items,b.dataset.op,seed);selected=0;},b.textContent+(b.dataset.op==='shuffle'?` (seed ${seed})`:''));});
  $('#undo').onclick=()=>{const prev=history.pop();if(!prev)return;stop();doc=prev;comparing=false;selected=Math.min(selected,doc.items.length-1);render();loadedId=null;show(selected);$('#undo').disabled=!history.length;status('Undone');};
  $('#compare').onclick=()=>{stop();comparing=!comparing;selected=0;render();loadedId=null;show(0);status(comparing?'Original footage and trims; reading panel belongs to your edit':'Your arrangement');};
  $$('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelector('.workspace').dataset.active=b.dataset.tab;$$('[data-tab]').forEach(x=>x.classList.toggle('on',x===b));});
  let sx=null;$('.workspace').addEventListener('touchstart',e=>{if(e.target.closest('input,select,textarea,button'))return;sx=e.touches[0].clientX;},{passive:true});
  $('.workspace').addEventListener('touchend',e=>{if(sx===null)return;const dx=e.changedTouches[0].clientX-sx;sx=null;if(Math.abs(dx)<80)return;const tabs=$$('[data-tab]'),i=tabs.findIndex(b=>b.classList.contains('on'));tabs[Math.max(0,Math.min(2,i+(dx<0?1:-1)))].click();},{passive:true});
  $('#periodic').onclick=e=>{const b=e.target.closest('[data-sign]');if(b)showSign(b.dataset.sign);};
  $('#examples').onclick=e=>{const b=e.target.closest('[data-add]');if(b&&!b.disabled)addShot(b.dataset.add);};
  $('#inspectSource').onclick=inspectSource;
  $('#sourceContext').onclick=e=>{const b=e.target.closest('[data-neighbor]');if(b&&!b.disabled)addShot(b.dataset.neighbor);};
  $('#more').onclick=()=>{renderSaved();$('#offset').value=doc.offset;$('#fullFilm').href='syntagma.html?'+new URLSearchParams({t:doc.offset,cut:doc.context?.cut||'suite'});$('#menu').showModal();};$('#save').onclick=save;
  $('#offset').onchange=e=>{const n=Number(e.target.value);if(Number.isFinite(n)&&n>=0){snapshot();doc.offset=n;status('EDL record offset updated');}else e.target.value=doc.offset;};
  $('#exportPassage').onclick=()=>download('cineosis-syntagm.json',packed());
  $('#exportEDL').onclick=()=>{try{download('syntagm.cineosis-edl.json',toEDL(doc,shots,location.href));status('EDL exported with clip trims and record offset');}catch(e){status(e.message);}};
  $('#import').onclick=()=>$('#file').click();$('#file').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{importDoc(JSON.parse(await f.text()));$('#menu').close();}catch(err){status('Import failed: '+err.message);}e.target.value='';};
  $('#saved').onclick=e=>{const b=e.target.closest('[data-saved]');if(!b)return;try{importDoc(saved().find(d=>d.id===b.dataset.saved));$('#menu').close();}catch(err){status(err.message);}};
  document.addEventListener('keydown',e=>{if(e.target.closest('input,select,textarea')||$('#menu').open)return;if(e.code==='Space'){e.preventDefault();play();}if(e.key==='ArrowRight')$('#next').click();if(e.key==='ArrowLeft')$('#prev').click();if((e.ctrlKey||e.metaKey)&&e.key==='z'){e.preventDefault();$('#undo').click();}});
}
async function boot(){
  try{
    D=await json('syntagm/data.json');shots={...D.shots};
    $('#origin').innerHTML='<optgroup label="WYGWYL edits">'+Object.entries(D.cuts).map(([k,c])=>`<option value="${k}">${esc('WYGWYL · '+c.title)}</option>`).join('')+'</optgroup><optgroup label="Original source films">'+D.sources.map(s=>`<option value="source:${esc(s.slug)}">${esc(s.title)} · ${s.count}</option>`).join('')+'</optgroup>';
    bindReadings();wire();fillChapters();$('#loader').hidden=true;$('#app').hidden=false;if(!linkedPassage()){const q=new URLSearchParams(location.search);if(q.has('source')&&D.sources.some(s=>s.slug===q.get('source'))){$('#origin').value='source:'+q.get('source');fillChapters();$('#from').value=Math.max(1,Number(q.get('first'))||1);$('#count').value=Math.min(24,Math.max(1,Number(q.get('count'))||3));}await load();}
  }catch(e){$('#loader').innerHTML=`Could not load the lab: ${esc(e.message)} <button id="reload">Retry</button>`;$('#reload').onclick=()=>location.reload();}
}
boot();
