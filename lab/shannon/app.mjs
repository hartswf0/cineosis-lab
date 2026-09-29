import {splitSource,rankOffline,compose as composePath,metricsFor,evaluateBenchmark,normalizeCandidate,tracePlan} from './model.mjs';
import {BENCHMARKS} from './benchmarks.mjs';
const $=id=>document.getElementById(id); const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const LAB=new URL('./',location.href);
let catalog=null,local=false,plan=null,candidateSets=[],phrases=[],activeTest=null,current=0,playing=false,startedAt=0,recordAt=0,raf=0,recognition=null,listening=false,manual=new Map(),corrections=0,calls=new Map(),runHistory=[],runSerial=0,interventions=[];
const video=$('film');
const status=s=>$('status').textContent=s;

function options(){return {literal:+$('literal').value,continuity:+$('continuity').value,intercut:+$('intercut').value,surprise:+$('surprise').value,beam:12,pool:28};}
function mediaUrl(c){if(!c)return ''; if(c.media?.startsWith('/'))return c.media; try{return new URL(c.media||'',LAB).href}catch{return c.media||''}}
function imageUrl(c){if(!c?.poster)return ''; try{return new URL(c.poster,LAB).href}catch{return c.poster}}
async function checkLocal(){
  try{const r=await fetch('/api/shannon/status',{signal:AbortSignal.timeout(1200)});if(!r.ok)throw 0;const d=await r.json();local=true;$('serverState').textContent=`lab online · ${Number(d.embedded||0).toLocaleString()} embedded`;}
  catch{local=false;$('serverState').textContent='hosted mode';}
}
async function loadCatalog(){try{catalog=await fetch(new URL('synthesis/catalog.json',LAB)).then(r=>{if(!r.ok)throw Error('catalog');return r.json()});}catch{catalog={shots:[]};}}

function batch(a,n){const out=[];for(let i=0;i<a.length;i+=n)out.push(a.slice(i,i+n));return out;}
async function getCandidates(ps){
  if(local){
    const all=[];
    for(const group of batch(ps,32)){
      const r=await fetch('/api/shannon/search',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({phrases:group.map(x=>x.text),limit:64})});
      if(!r.ok)throw Error((await r.json().catch(()=>({}))).error||'local embedding search failed');
      const d=await r.json(); all.push(...d.results.map(row=>row.map(c=>normalizeCandidate(c))));
    }
    return all;
  }
  return ps.map(p=>rankOffline(p.text,catalog,{limit:64}));
}

function applyManual(sets){return sets.map((set,i)=>{const c=manual.get(i);return c?[normalizeCandidate(c)]:set;});}
function relationResult(call,pick){
  if(!call||!pick)return {status:'pending',observed:'no outcome yet'};
  const c=pick.candidate;
  if(call.type==='KEEP_SOURCE_CHANGE_SHOT')return {status:c.sourceKey===call.baselineSource&&c.id!==call.baselineId?'hit':'miss',observed:c.sourceKey===call.baselineSource?(c.id===call.baselineId?'same shot survived':'source held, shot changed'):'source changed'};
  if(call.type==='LEAVE_SOURCE')return {status:c.sourceKey!==call.baselineSource?'hit':'miss',observed:c.sourceKey!==call.baselineSource?'source changed':'source held'};
  if(call.type==='RETURN_PRIOR')return {status:call.priorSources.includes(c.sourceKey)&&c.sourceKey!==call.baselineSource?'hit':'miss',observed:call.priorSources.includes(c.sourceKey)?'earlier source selected':'no earlier source selected'};
  if(call.type==='KEEP_SHOT')return {status:c.id===call.baselineId?'hit':'miss',observed:c.id===call.baselineId?'shot survived':'shot changed'};
  if(call.type==='AVOID_SHOT')return {status:c.id!==call.baselineId?'hit':'miss',observed:c.id!==call.baselineId?'shot avoided':'shot survived'};
  return {status:'pending',observed:'unknown call'};
}
function evaluateCalls(){
  for(const call of calls.values()){
    if(call.run>=runSerial||call.phrase>=plan.picks.length)continue;
    const r=relationResult(call,plan.picks[call.phrase]);call.status=r.status;call.observed=r.observed;call.judgedRun=runSerial;
  }
}
function recordRun(text){
  runHistory.push({run:runSerial,time:new Date().toISOString(),source:text,options:options(),
    manual:[...manual.entries()].map(([phrase,c])=>({phrase,id:c.id,title:c.title,sourceKey:c.sourceKey})),
    calls:[...calls.values()].map(x=>({...x})),metrics:{...plan.metrics},
    picks:plan.picks.map((p,i)=>({phrase:i,text:p.phrase.text,speaker:p.phrase.speaker||null,operation:p.operation,reason:p.reason,id:p.candidate.id,title:p.candidate.title,sourceKey:p.candidate.sourceKey,sourceStart:p.candidate.sourceStart,manual:!!p.manual})),
    trace:plan.trace});
}

async function runCompose(){
  const text=$('sourceText').value.trim(); if(!text){status('Add a source first.');return;}
  phrases=splitSource(text); if(!phrases.length){status('No phrases found.');return;}
  $('compose').disabled=true;$('composeStatus').textContent=`Reading ${phrases.length} phrases across the archive.`;status('Building candidate fields');
  try{
    candidateSets=await getCandidates(phrases); const constrained=applyManual(candidateSets);
    plan=composePath(phrases,constrained,options());
    for(const i of manual.keys())if(plan.picks[i])plan.picks[i].manual=true;
    plan.metrics=metricsFor(plan.picks,phrases);plan.trace=tracePlan(plan,phrases,candidateSets,options());runSerial++;evaluateCalls();recordRun(text);current=0;prepareTimeline();renderPlan();loadPick(0);status(`Film ready · ${plan.metrics.scenes} scenes from ${phrases.length} phrases`);
  }catch(e){status(e.message);$('composeStatus').textContent=e.message;}
  finally{$('compose').disabled=false;}
}

function prepareTimeline(){let t=0;for(const p of plan.picks){p.recordIn=t;p.recordDuration=p.phrase.duration||3.5;p.recordOut=t+p.recordDuration;t=p.recordOut;}plan.duration=t;$('scrub').max=Math.max(.1,t);$('scrub').value=0;$('clock').textContent=`0.0 / ${t.toFixed(1)}`;}
function renderPlan(){
  $('emptyStage').hidden=true;$('play').disabled=false;$('previous').disabled=false;$('next').disabled=false;
  const m=plan.metrics;$('composeStatus').textContent=`${m.scenes} scenes · ${m.sceneYield.toFixed(2)} phrases/scene · ${(m.coverage*100).toFixed(0)}% covered · ${corrections} replacements`;
  $('stripLabel').textContent=`FILM PATH · ${m.scenes} SCENES · ${plan.picks.length} PHRASES`;
  $('timeline').innerHTML=plan.picks.map((p,i)=>`<button class="node ${i===current?'active':''}" data-i="${i}"><img alt="" src="${esc(imageUrl(p.candidate))}"><div><b>${esc(p.operation)}${p.manual?' · SET':''}</b><span>${esc(p.phrase.text)}</span><small>${esc(p.candidate.title)}</small></div></button>`).join('');
  $('timeline').querySelectorAll('.node').forEach(b=>b.onclick=()=>{pause();loadPick(+b.dataset.i);});
  renderInside();renderState();renderRail();renderBenchmark();renderPath();
}
function renderState(){
  if(!plan?.picks[current]){$('nowState').textContent='No state yet.';return;}
  const p=plan.picks[current]; const sceneIndex=plan.scenes.findIndex(s=>s.picks.includes(p));
  $('nowState').innerHTML=`<div><b>phrase</b><span>${current+1}/${plan.picks.length}</span></div><div><b>operation</b><span>${esc(p.operation)}</span></div><div><b>scene</b><span>${sceneIndex+1}/${plan.scenes.length}</span></div><div><b>strand</b><span>${esc(p.phrase.speaker||'voice')}</span></div><div><b>source</b><span>${esc(p.candidate.title)}</span></div><div><b>future support</b><span>${(p.parts?.future||0).toFixed(3)}</span></div>`;
}
function renderRail(){
  const set=candidateSets[current]||[];$('candidateRail').innerHTML=set.slice(0,8).map(c=>`<div class="railcand" data-id="${esc(c.id)}"><img alt="" src="${esc(imageUrl(c))}"><div><b>${esc(c.title)}</b><small>${c.raw.toFixed(3)} · ${esc(c.sourceKey)}</small></div></div>`).join('');
  $('candidateRail').querySelectorAll('.railcand').forEach(el=>el.onclick=()=>{const c=set.find(x=>x.id===el.dataset.id);if(c)replaceCurrent(c);});
}
function renderInside(){
  const m=plan?.metrics||{}; const p=plan?.picks?.[current];
  $('insideState').innerHTML=[['phrases',m.phrases??0],['scenes',m.scenes??0],['scene yield',m.sceneYield??0],['coverage',m.coverage!=null?Math.round(m.coverage*100)+'%':'—'],['now',p?.operation||'—'],['look-ahead',p?(p.parts?.future||0).toFixed(3):'—'],['corrections',corrections],['mode',local?'local embeddings':'hosted fallback']].map(([a,b])=>`<div><b>${a}</b><span>${esc(b)}</span></div>`).join('');
  $('diagnostics').innerHTML=[['continuity',m.continuity??'n/a'],['return',m.returnAccuracy??'n/a'],['strand purity',m.strandPurity??'n/a'],['singleton rate',m.singletonRate??'n/a'],['path score',plan?.score?.toFixed(2)??'n/a'],['candidate pool',options().pool]].map(([a,b])=>`<div><b>${a}</b><span>${esc(b)}</span></div>`).join('');
}
function callLabel(type){return ({KEEP_SOURCE_CHANGE_SHOT:'same source, different shot',LEAVE_SOURCE:'leave this source',RETURN_PRIOR:'return to an earlier source',KEEP_SHOT:'keep this shot',AVOID_SHOT:'avoid this shot'})[type]||type;}
function makeCall(type){
  if(!plan?.picks[current]){status('Compose a film before calling a shot.');return;}
  const p=plan.picks[current];
  const call={type,phrase:current,run:runSerial,created:new Date().toISOString(),baselineId:p.candidate.id,baselineTitle:p.candidate.title,baselineSource:p.candidate.sourceKey,priorSources:[...new Set(plan.picks.slice(0,current).map(x=>x.candidate.sourceKey))],status:'pending',observed:'change the film, then recompose'};
  calls.set(current,call);
  interventions.push({kind:'call',run:runSerial,phrase:current,type,time:call.created,baselineId:call.baselineId,baselineSource:call.baselineSource});
  renderPath();status('Call recorded before the next outcome.');
}
function renderPath(){
  renderInside();
  const call=calls.get(current);
  $('callResult').className='callResult'+(call?.status?' '+call.status:'');
  $('callResult').textContent=call?callLabel(call.type)+' · '+call.status.toUpperCase()+' · '+call.observed:'No call made.';
  const t=plan?.trace?.[current];
  if(!t){$('pathTrace').textContent='Compose a film to expose the path.';return;}
  const alts=t.alternatives||[];
  $('pathTrace').innerHTML='<div class="pathChoice"><span class="eyebrow">CHOICE '+(current+1)+'</span><b>'+esc(t.chosen.title)+'</b><small>'+esc(t.operation)+' · local rank '+t.localRank+' · score '+t.chosenScore.toFixed(3)+'</small><p>'+esc(plan.picks[current].reason||'')+'</p></div><div class="pathAlternatives"><span class="eyebrow">NEARBY ROUTES THAT DID NOT SURVIVE</span>'+alts.map((a,i)=>'<div><b>'+(i+1)+'. '+esc(a.candidate.title)+'</b><span>'+a.score.toFixed(3)+' · words '+a.semantic.toFixed(3)+' · structure '+a.structural.toFixed(3)+' · toward '+a.toward.toFixed(3)+'</span></div>').join('')+'</div>';
}
function exportPath(){
  if(!plan)return;
  const dossier={format:'cineosis-shannon-path/1',created:new Date().toISOString(),claim:'A class is not a path.',currentRun:runSerial,source:$('sourceText').value,history:runHistory,interventions,calls:[...calls.values()].map(x=>({...x}))};
  const blob=new Blob([JSON.stringify(dossier,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='shannon-path-dossier.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status('Exported path dossier: alternatives, calls, interventions and surviving choices.');
}
function renderBenchmark(){
  if(!activeTest){$('activeTest').textContent='No benchmark selected.';return;}
  const ev=plan?evaluateBenchmark(plan,activeTest):null;
  let html=`<b>${esc(activeTest.title)}</b> · ${esc(activeTest.author)}<br>${esc(activeTest.challenge)}<br><span>Expected operations: ${activeTest.ops.join(', ')}</span>`;
  if(ev?.checks?.length)html+=`<div class="checks">${ev.checks.map(c=>`<span class="${c.pass?'pass':'fail'}">${c.pass?'PASS':'FAIL'} ${esc(c.label)}: ${esc(c.value)}</span>`).join(' · ')}</div>`;
  $('activeTest').innerHTML=html;
}
function loadPick(i,offset=0){
  if(!plan?.picks?.length)return; current=Math.max(0,Math.min(plan.picks.length-1,i)); const p=plan.picks[current],c=p.candidate;
  $('caption').textContent=p.phrase.text;$('sourceTitle').textContent=c.title;$('opTag').textContent=p.operation;
  document.querySelectorAll('.node').forEach((n,j)=>n.classList.toggle('active',j===current)); const node=document.querySelector(`.node[data-i="${current}"]`);node?.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});
  renderState();renderRail();renderInside();renderPath();
  video.pause();video.muted=$('sound').getAttribute('aria-pressed')!=='true'; const url=mediaUrl(c); if(!url){video.removeAttribute('src');video.load();return;}
  if(video.src!==url)video.src=url; const seek=()=>{try{video.currentTime=(c.mediaIn||0)+Math.min(offset,Math.max(0,c.duration-.05));}catch{}};
  if(video.readyState>=1)seek();else video.addEventListener('loadedmetadata',seek,{once:true});
  recordAt=p.recordIn+offset;$('scrub').value=recordAt;updateClock();
}
function updateClock(){$('clock').textContent=`${recordAt.toFixed(1)} / ${(plan?.duration||0).toFixed(1)}`;$('scrub').value=recordAt;}
function play(){if(!plan?.picks?.length)return;if(recordAt>=plan.duration-.05)loadPick(0);playing=true;$('play').textContent='Pause';startedAt=performance.now()-Math.max(0,recordAt-plan.picks[current].recordIn)*1000;video.play().catch(()=>{});cancelAnimationFrame(raf);raf=requestAnimationFrame(tick);}
function pause(){playing=false;$('play').textContent='Play';video.pause();cancelAnimationFrame(raf);}
function tick(now){if(!playing)return;const p=plan.picks[current];let localT=(now-startedAt)/1000;recordAt=p.recordIn+localT;if(recordAt>=p.recordOut-.02){if(current>=plan.picks.length-1){recordAt=plan.duration;updateClock();pause();return;}loadPick(current+1);startedAt=performance.now();video.play().catch(()=>{});}else{const c=p.candidate,max=(c.mediaIn||0)+Math.min(c.duration,p.recordDuration);if(video.currentTime>=max-.04)video.pause();updateClock();}raf=requestAnimationFrame(tick);}
function replaceCurrent(c){if(!plan?.picks[current])return;const from=plan.picks[current].candidate;manual.set(current,c);corrections++;interventions.push({kind:'replacement',run:runSerial,phrase:current,time:new Date().toISOString(),from:{id:from.id,title:from.title,sourceKey:from.sourceKey},to:{id:c.id,title:c.title,sourceKey:c.sourceKey}});status(`Replacement fixed at phrase ${current+1}. Recompose to propagate it.`);runCompose();}

async function runSearch(){const q=$('searchText').value.trim();if(!q)return;status('Searching');try{const ps=splitSource(q)||[];const p=ps[0]||{text:q};const set=(await getCandidates([p]))[0]||[];$('searchResults').innerHTML=set.slice(0,18).map(c=>`<div class="result"><img alt="" src="${esc(imageUrl(c))}"><div><b>${esc(c.title)}</b><small>${c.raw.toFixed(3)} · ${esc(c.sourceKey)}</small></div><button data-id="${esc(c.id)}">Preview</button></div>`).join('');$('searchResults').querySelectorAll('button').forEach(b=>b.onclick=()=>preview(set.find(c=>c.id===b.dataset.id)));status(`${set.length} candidates`);}catch(e){status(e.message)}}
function preview(c){if(!c)return;$('sourceTitle').textContent=c.title;$('opTag').textContent='SEARCH';$('caption').textContent=$('searchText').value;video.pause();video.src=mediaUrl(c);video.muted=true;video.addEventListener('loadedmetadata',()=>{video.currentTime=c.mediaIn||0;video.play().catch(()=>{});},{once:true});}

function renderTests(filter=''){$('testList').innerHTML=BENCHMARKS.filter(b=>(b.title+' '+b.author+' '+b.group+' '+b.challenge).toLowerCase().includes(filter.toLowerCase())).map(b=>`<div class="test ${activeTest?.id===b.id?'active':''}" data-id="${b.id}"><b>${esc(b.title)}</b><span>${esc(b.author)} · ${esc(b.group)}</span><small>${esc(b.challenge)}</small></div>`).join('');$('testList').querySelectorAll('.test').forEach(el=>el.onclick=()=>{activeTest=BENCHMARKS.find(b=>b.id===el.dataset.id);renderTests($('testFilter').value);renderBenchmark();status(`Benchmark set: ${activeTest.title}`);});}
function selectTab(name){document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===name)));for(const n of ['compose','search','tests','path'])$(n+'Panel').hidden=n!==name;if(name==='path')renderPath();}

$('compose').onclick=runCompose;$('find').onclick=runSearch;$('play').onclick=()=>playing?pause():play();$('previous').onclick=()=>{pause();loadPick(current-1)};$('next').onclick=()=>{pause();loadPick(current+1)};$('sound').onclick=()=>{const on=$('sound').getAttribute('aria-pressed')!=='true';$('sound').setAttribute('aria-pressed',String(on));$('sound').textContent=on?'Sound on':'Sound off';video.muted=!on;};
$('scrub').oninput=()=>{if(!plan)return;pause();const t=+$('scrub').value;let i=plan.picks.findIndex(p=>t<p.recordOut);if(i<0)i=plan.picks.length-1;loadPick(i,Math.max(0,t-plan.picks[i].recordIn));};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>selectTab(b.dataset.tab));
for(const id of ['literal','continuity','intercut','surprise']){$(id).onchange=()=>{interventions.push({kind:'tuning',run:runSerial,time:new Date().toISOString(),control:id,value:+$(id).value});if(plan)runCompose();};}
$('loadText').onclick=()=>$('textFile').click();$('textFile').onchange=async()=>{const f=$('textFile').files?.[0];if(!f)return;$('sourceText').value=await f.text();status(`Loaded ${f.name}`);};
$('testFilter').oninput=()=>renderTests($('testFilter').value);
document.querySelectorAll('[data-call]').forEach(b=>b.onclick=()=>makeCall(b.dataset.call));
$('clearCalls').onclick=()=>{calls.clear();renderPath();status('Calls cleared.');};
$('exportPath').onclick=exportPath;

const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!Recognition){$('listen').disabled=true;$('listen').textContent='Speech unavailable';}
$('listen').onclick=()=>{if(!Recognition)return;if(listening){recognition.stop();return;}recognition=new Recognition();recognition.continuous=true;recognition.interimResults=true;recognition.lang=navigator.language||'en-US';let fixed=$('sourceText').value.trim();recognition.onstart=()=>{listening=true;$('listen').textContent='Stop';status('Listening');};recognition.onresult=e=>{let interim='',done='';for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;if(e.results[i].isFinal)done+=t+' ';else interim+=t;}if(done){fixed=(fixed+' '+done).trim();$('sourceText').value=fixed;}if(interim)status('Hearing: '+interim);};recognition.onerror=e=>status('Speech: '+e.error);recognition.onend=()=>{listening=false;$('listen').textContent='Listen';status('Speech stopped');};try{recognition.start()}catch{status('Speech could not start')}};
window.addEventListener('pagehide',()=>{recognition?.stop();pause();});

await Promise.all([checkLocal(),loadCatalog()]);renderTests();renderInside();renderPath();status(local?'Local archive ready':'Hosted fallback ready');
