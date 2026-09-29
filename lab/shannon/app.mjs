import {splitSource,rankOffline,compose as composePath,metricsFor,evaluateBenchmark,normalizeCandidate,tracePlan} from './model.mjs';
import {BENCHMARKS} from './benchmarks.mjs';
const $=id=>document.getElementById(id); const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const LAB=new URL('./',location.href);
let catalog=null,local=false,plan=null,candidateSets=[],phrases=[],activeTest=null,current=0,playing=false,startedAt=0,recordAt=0,raf=0,recognition=null,listening=false,manual=new Map(),directives=new Map(),corrections=0,calls=new Map(),runHistory=[],runSerial=0,interventions=[];
const video=$('film');
const status=s=>$('status').textContent=s;

function options(){return {literal:+$('literal').value,continuity:+$('continuity').value,intercut:+$('intercut').value,surprise:+$('surprise').value,beam:12,pool:28};}
function composeOptions(){return {...options(),directives:Object.fromEntries([...directives.entries()].map(([i,d])=>[i,{operation:d.operation||null}]))};}
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
function mergeCandidates(a,b){const m=new Map();for(const c of [...a,...b])m.set(c.id,normalizeCandidate(c));return [...m.values()];}
async function sourceField(sourceKey,phrase){
  if(!sourceKey)return [];
  if(local){
    const r=await fetch('/api/shannon/source',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({sourceKey,phrase,limit:128})});
    if(r.ok){const d=await r.json();return (d.results||[]).map(normalizeCandidate);}
  }
  return (catalog?.shots||[]).filter(x=>(x.example||x.source||x.title)===sourceKey).map(normalizeCandidate);
}
async function expandDirectiveFields(sets){
  const out=sets.map(x=>x.slice());
  for(const [i,d] of directives){
    if(i<0||i>=out.length)continue;
    if(d.sourceEq)out[i]=mergeCandidates(out[i],await sourceField(d.sourceEq,phrases[i]?.text||''));
    if(d.inject)out[i]=mergeCandidates([d.inject],out[i]);
  }
  return out;
}
function applyDirectives(sets){
  const out=sets.map(x=>x.slice());
  for(const [i,d] of directives){
    if(i<0||i>=out.length)continue;
    let a=out[i];
    if(d.inject&&!a.some(c=>c.id===d.inject.id))a=[normalizeCandidate(d.inject),...a];
    if(d.exactId)a=a.filter(c=>c.id===d.exactId);
    if(d.avoidId)a=a.filter(c=>c.id!==d.avoidId);
    if(d.sourceEq)a=a.filter(c=>c.sourceKey===d.sourceEq);
    if(d.sourceNe)a=a.filter(c=>c.sourceKey!==d.sourceNe);
    if(d.sourceIn?.length)a=a.filter(c=>d.sourceIn.includes(c.sourceKey));
    if(Number.isFinite(d.startGt))a=a.filter(c=>c.sourceStart>d.startGt);
    if(Number.isFinite(d.startLt))a=a.filter(c=>c.sourceStart<d.startLt);
    d.failed=a.length?null:'no candidate satisfies this call';
    if(a.length)out[i]=a;
  }
  return applyManual(out);
}
function relationResult(call,pick,fullPlan=plan){
  if(!call||!pick)return {status:'pending',observed:'no outcome yet'};
  const c=pick.candidate;
  if(call.type==='KEEP_SOURCE_CHANGE_SHOT')return {status:c.sourceKey===call.baselineSource&&c.id!==call.baselineId?'hit':'miss',observed:c.sourceKey===call.baselineSource?(c.id===call.baselineId?'same shot survived':'source held, shot changed'):'source changed'};
  if(call.type==='LEAVE_SOURCE')return {status:c.sourceKey!==call.baselineSource?'hit':'miss',observed:c.sourceKey!==call.baselineSource?'source changed':'source held'};
  if(call.type==='RETURN_PRIOR')return {status:call.priorSources.includes(c.sourceKey)&&c.sourceKey!==call.baselineSource?'hit':'miss',observed:call.priorSources.includes(c.sourceKey)?'earlier source selected':'no earlier source selected'};
  if(call.type==='KEEP_SHOT')return {status:c.id===call.baselineId?'hit':'miss',observed:c.id===call.baselineId?'shot survived':'shot changed'};
  if(call.type==='AVOID_SHOT')return {status:c.id!==call.baselineId?'hit':'miss',observed:c.id!==call.baselineId?'shot avoided':'shot survived'};
  if(call.type==='LATER_SOURCE')return {status:c.sourceKey===call.baselineSource&&c.sourceStart>call.baselineStart?'hit':'miss',observed:c.sourceKey===call.baselineSource&&c.sourceStart>call.baselineStart?'later shot in source':'later-source target missed'};
  if(call.type==='EARLIER_SOURCE')return {status:c.sourceKey===call.baselineSource&&c.sourceStart<call.baselineStart?'hit':'miss',observed:c.sourceKey===call.baselineSource&&c.sourceStart<call.baselineStart?'earlier shot in source':'earlier-source target missed'};
  if(call.type==='RETURN_SCENE')return {status:c.sourceKey===call.targetSource?'hit':'miss',observed:c.sourceKey===call.targetSource?'target scene returned':'target scene missed'};
  if(call.type==='FORCE_OPERATION')return {status:pick.operation===call.operation?'hit':'miss',observed:pick.operation===call.operation?'operation executed':'operation not executed'};
  if(call.type==='HOLD_NEXT'){const n=fullPlan?.picks?.[call.phrase+1];const ok=c.id===call.baselineId&&n?.candidate?.id===call.baselineId;return {status:ok?'hit':'miss',observed:ok?'shot held through next phrase':'hold broke'};}
  if(call.type==='STAY_SOURCE_SPAN'){const xs=(fullPlan?.picks||[]).slice(call.phrase,call.phrase+call.count);const ok=xs.length===call.count&&xs.every(x=>x.candidate.sourceKey===call.baselineSource);return {status:ok?'hit':'miss',observed:ok?'source held across span':'source changed inside span'};}
  if(call.type==='HOLD_SPAN'){const xs=(fullPlan?.picks||[]).slice(call.phrase,call.phrase+call.count);const ok=xs.length===call.count&&xs.every(x=>x.candidate.id===call.baselineId);return {status:ok?'hit':'miss',observed:ok?'shot held across span':'shot changed inside span'};}
  return {status:'pending',observed:'unknown call'};
}
function evaluateCalls(){
  for(const call of calls.values()){
    if(call.run>=runSerial||call.phrase>=plan.picks.length)continue;
    const r=relationResult(call,plan.picks[call.phrase],plan);call.status=r.status;call.observed=r.observed;call.judgedRun=runSerial;
  }
}
function recordRun(text){
  runHistory.push({run:runSerial,time:new Date().toISOString(),source:text,options:options(),
    manual:[...manual.entries()].map(([phrase,c])=>({phrase,id:c.id,title:c.title,sourceKey:c.sourceKey})),
    calls:[...calls.values()].map(x=>({...x})),directives:[...directives.entries()].map(([phrase,d])=>({phrase,...d,inject:d.inject?{id:d.inject.id,title:d.inject.title,sourceKey:d.inject.sourceKey}:null})),metrics:{...plan.metrics},
    picks:plan.picks.map((p,i)=>({phrase:i,text:p.phrase.text,speaker:p.phrase.speaker||null,operation:p.operation,reason:p.reason,id:p.candidate.id,title:p.candidate.title,sourceKey:p.candidate.sourceKey,sourceStart:p.candidate.sourceStart,manual:!!p.manual})),
    trace:plan.trace});
}

async function runCompose({target=null}={}){
  const text=$('sourceText').value.trim(); if(!text){status('Add a source first.');return;}
  phrases=splitSource(text); if(!phrases.length){status('No phrases found.');return;}
  $('compose').disabled=true;$('composeStatus').textContent=`Reading ${phrases.length} phrases across the archive.`;status('Building candidate fields');
  try{
    candidateSets=await getCandidates(phrases); const expanded=await expandDirectiveFields(candidateSets); const constrained=applyDirectives(expanded);
    plan=composePath(phrases,constrained,composeOptions());
    for(const i of manual.keys())if(plan.picks[i])plan.picks[i].manual=true;
    plan.metrics=metricsFor(plan.picks,phrases);plan.trace=tracePlan(plan,phrases,expanded,composeOptions());runSerial++;evaluateCalls();recordRun(text);current=target==null?0:Math.max(0,Math.min(plan.picks.length-1,target));prepareTimeline();renderPlan();loadPick(current);status(`Film ready · ${plan.metrics.scenes} scenes from ${phrases.length} phrases`);
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
function callLabel(type){return ({
  KEEP_SOURCE_CHANGE_SHOT:'same source, different shot',LATER_SOURCE:'same source, later shot',EARLIER_SOURCE:'same source, earlier shot',
  LEAVE_SOURCE:'leave this source',RETURN_PRIOR:'return to an earlier source',RETURN_SCENE:'return to scene',
  KEEP_SHOT:'keep this shot',AVOID_SHOT:'avoid this shot',HOLD_NEXT:'hold this shot through next phrase',
  STAY_SOURCE_SPAN:'stay in this source',HOLD_SPAN:'hold this shot',FORCE_OPERATION:'force operation'
})[type]||type;}
function mostRecentPriorSource(){
  if(!plan?.picks?.length)return null;
  const here=plan.picks[current].candidate.sourceKey;
  for(let i=current-1;i>=0;i--){const k=plan.picks[i].candidate.sourceKey;if(k!==here)return k;}
  return null;
}
function installDirective(type,payload={}){
  const p=plan.picks[current],c=p.candidate,base={root:current,type};
  const set=(i,d)=>{manual.delete(i);directives.set(i,{...d,...base,root:current});};
  if(type==='KEEP_SOURCE_CHANGE_SHOT')set(current,{sourceEq:c.sourceKey,avoidId:c.id});
  else if(type==='LATER_SOURCE')set(current,{sourceEq:c.sourceKey,avoidId:c.id,startGt:c.sourceStart+.01});
  else if(type==='EARLIER_SOURCE')set(current,{sourceEq:c.sourceKey,avoidId:c.id,startLt:c.sourceStart-.01});
  else if(type==='LEAVE_SOURCE')set(current,{sourceNe:c.sourceKey});
  else if(type==='RETURN_PRIOR'){const k=payload.sourceKey||mostRecentPriorSource();if(!k)throw Error('No earlier distinct source exists yet.');set(current,{sourceEq:k});payload.targetSource=k;}
  else if(type==='RETURN_SCENE'){const scene=plan.scenes[(payload.scene||1)-1];if(!scene)throw Error('That scene does not exist.');set(current,{sourceEq:scene.sourceKey});payload.targetSource=scene.sourceKey;}
  else if(type==='KEEP_SHOT')set(current,{exactId:c.id,inject:c});
  else if(type==='AVOID_SHOT')set(current,{avoidId:c.id});
  else if(type==='HOLD_NEXT'){
    set(current,{exactId:c.id,inject:c,operation:'HOLD'});
    if(current+1<phrases.length)set(current+1,{exactId:c.id,inject:c,operation:'HOLD'});
  }else if(type==='STAY_SOURCE_SPAN'){
    const count=Math.max(2,Math.min(12,Number(payload.count)||2));payload.count=count;
    for(let i=current;i<Math.min(phrases.length,current+count);i++)set(i,{sourceEq:c.sourceKey});
  }else if(type==='HOLD_SPAN'){
    const count=Math.max(2,Math.min(12,Number(payload.count)||2));payload.count=count;
    for(let i=current;i<Math.min(phrases.length,current+count);i++)set(i,{exactId:c.id,inject:c,operation:'HOLD'});
  }else if(type==='FORCE_OPERATION'){
    const op=String(payload.operation||'').toUpperCase();if(!['OPEN','CONTINUE','HOLD','REPEAT','RETURN','ALTERNATE','SUSPEND','COMPLETE','ABSENCE','INSERT'].includes(op))throw Error('Unknown operation.');
    payload.operation=op;set(current,{operation:op});
  }
  return payload;
}
function parseCallText(text){
  const s=String(text||'').trim().toLowerCase();if(!s)return null;
  let m;
  if((m=s.match(/(?:return|go back)\s+(?:to\s+)?scene\s*(\d+)/)))return {type:'RETURN_SCENE',scene:+m[1]};
  if((m=s.match(/(?:stay|keep|remain).*?(?:source|scene).*?(?:next|for)\s*(\d+)/)))return {type:'STAY_SOURCE_SPAN',count:+m[1]};
  if((m=s.match(/(?:hold|keep).*?(?:shot|image).*?(?:next|for)\s*(\d+)/)))return {type:'HOLD_SPAN',count:+m[1]};
  if(/later.*source|same source.*later|forward.*source/.test(s))return {type:'LATER_SOURCE'};
  if(/earlier.*source|same source.*earlier|backward.*source/.test(s))return {type:'EARLIER_SOURCE'};
  if(/same source.*different|different shot.*same source/.test(s))return {type:'KEEP_SOURCE_CHANGE_SHOT'};
  if(/leave.*source|new source|different source/.test(s))return {type:'LEAVE_SOURCE'};
  if(/return.*prior|return.*earlier|go back.*source/.test(s))return {type:'RETURN_PRIOR'};
  if(/hold.*next|through.*next/.test(s))return {type:'HOLD_NEXT'};
  if(/keep.*shot|keep.*image|same shot/.test(s))return {type:'KEEP_SHOT'};
  if(/avoid.*shot|not this shot|different shot/.test(s))return {type:'AVOID_SHOT'};
  m=s.match(/\b(open|continue|hold|repeat|return|alternate|suspend|complete|absence|insert)\b/);
  if(m)return {type:'FORCE_OPERATION',operation:m[1].toUpperCase()};
  return null;
}
function releaseDirective(at=current){
  const root=directives.get(at)?.root??at;
  for(const [i,d] of [...directives])if((d.root??i)===root)directives.delete(i);
  calls.delete(root);
  renderDirectCall();renderPath();
}
async function makeCall(type,payload={}){
  if(!plan?.picks[current]){status('Compose a film before calling a shot.');return;}
  const target=current,p=plan.picks[target],c=p.candidate;
  try{payload=installDirective(type,payload);}catch(e){status(e.message);return;}
  const call={type,phrase:target,run:runSerial,created:new Date().toISOString(),baselineId:c.id,baselineTitle:c.title,baselineSource:c.sourceKey,baselineStart:c.sourceStart,
    priorSources:[...new Set(plan.picks.slice(0,target).map(x=>x.candidate.sourceKey))],targetSource:payload.targetSource||null,operation:payload.operation||null,count:payload.count||null,status:'pending',observed:'constraint installed'};
  calls.set(target,call);
  interventions.push({kind:'called-shot',run:runSerial,phrase:target,type,time:call.created,baselineId:call.baselineId,baselineSource:call.baselineSource,payload:{...payload}});
  renderDirectCall();status('Calling '+callLabel(type));
  await runCompose({target});
}
function renderDirectCall(){
  const p=plan?.picks?.[current];$('callBeat').textContent=p?('beat '+(current+1)+' · '+p.phrase.text):'compose, then select a beat';
  const call=calls.get(current),d=directives.get(current);
  const msg=call?(callLabel(call.type)+(call.operation?' '+call.operation:'')+' · '+call.status.toUpperCase()+' · '+call.observed):(d?('constraint active'+(d.failed?' · '+d.failed:'')):'A call is a constraint, not a suggestion.');
  $('directCallResult').className='directCallResult'+(call?.status?' '+call.status:'');$('directCallResult').textContent=msg;
}
function renderPath(){
  renderInside();
  const call=calls.get(current);renderDirectCall();
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
  renderState();renderRail();renderInside();renderPath();renderDirectCall();
  video.pause();video.muted=$('sound').getAttribute('aria-pressed')!=='true'; const url=mediaUrl(c); if(!url){video.removeAttribute('src');video.load();return;}
  if(video.src!==url)video.src=url; const seek=()=>{try{video.currentTime=(c.mediaIn||0)+Math.min(offset,Math.max(0,c.duration-.05));}catch{}};
  if(video.readyState>=1)seek();else video.addEventListener('loadedmetadata',seek,{once:true});
  recordAt=p.recordIn+offset;$('scrub').value=recordAt;updateClock();
}
function updateClock(){$('clock').textContent=`${recordAt.toFixed(1)} / ${(plan?.duration||0).toFixed(1)}`;$('scrub').value=recordAt;}
function play(){if(!plan?.picks?.length)return;if(recordAt>=plan.duration-.05)loadPick(0);playing=true;$('play').textContent='Pause';startedAt=performance.now()-Math.max(0,recordAt-plan.picks[current].recordIn)*1000;video.play().catch(()=>{});cancelAnimationFrame(raf);raf=requestAnimationFrame(tick);}
function pause(){playing=false;$('play').textContent='Play';video.pause();cancelAnimationFrame(raf);}
function tick(now){if(!playing)return;const p=plan.picks[current];let localT=(now-startedAt)/1000;recordAt=p.recordIn+localT;if(recordAt>=p.recordOut-.02){if(current>=plan.picks.length-1){recordAt=plan.duration;updateClock();pause();return;}loadPick(current+1);startedAt=performance.now();video.play().catch(()=>{});}else{const c=p.candidate,max=(c.mediaIn||0)+Math.min(c.duration,p.recordDuration);if(video.currentTime>=max-.04)video.pause();updateClock();}raf=requestAnimationFrame(tick);}
function replaceCurrent(c){if(!plan?.picks[current])return;const target=current,from=plan.picks[target].candidate;releaseDirective(target);manual.set(target,c);corrections++;interventions.push({kind:'replacement',run:runSerial,phrase:target,time:new Date().toISOString(),from:{id:from.id,title:from.title,sourceKey:from.sourceKey},to:{id:c.id,title:c.title,sourceKey:c.sourceKey}});status(`Replacement fixed at phrase ${target+1}. Recompose to propagate it.`);runCompose({target});}

async function runSearch(){const q=$('searchText').value.trim();if(!q)return;status('Searching');try{const ps=splitSource(q)||[];const p=ps[0]||{text:q};const set=(await getCandidates([p]))[0]||[];$('searchResults').innerHTML=set.slice(0,18).map(c=>`<div class="result"><img alt="" src="${esc(imageUrl(c))}"><div><b>${esc(c.title)}</b><small>${c.raw.toFixed(3)} · ${esc(c.sourceKey)}</small></div><button data-id="${esc(c.id)}">Preview</button></div>`).join('');$('searchResults').querySelectorAll('button').forEach(b=>b.onclick=()=>preview(set.find(c=>c.id===b.dataset.id)));status(`${set.length} candidates`);}catch(e){status(e.message)}}
function preview(c){if(!c)return;$('sourceTitle').textContent=c.title;$('opTag').textContent='SEARCH';$('caption').textContent=$('searchText').value;video.pause();video.src=mediaUrl(c);video.muted=true;video.addEventListener('loadedmetadata',()=>{video.currentTime=c.mediaIn||0;video.play().catch(()=>{});},{once:true});}

function renderTests(filter=''){$('testList').innerHTML=BENCHMARKS.filter(b=>(b.title+' '+b.author+' '+b.group+' '+b.challenge).toLowerCase().includes(filter.toLowerCase())).map(b=>`<div class="test ${activeTest?.id===b.id?'active':''}" data-id="${b.id}"><b>${esc(b.title)}</b><span>${esc(b.author)} · ${esc(b.group)}</span><small>${esc(b.challenge)}</small></div>`).join('');$('testList').querySelectorAll('.test').forEach(el=>el.onclick=()=>{activeTest=BENCHMARKS.find(b=>b.id===el.dataset.id);renderTests($('testFilter').value);renderBenchmark();status(`Benchmark set: ${activeTest.title}`);});}
function selectTab(name){document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===name)));for(const n of ['compose','search','tests','path'])$(n+'Panel').hidden=n!==name;if(name==='path')renderPath();}

$('compose').onclick=runCompose;$('find').onclick=runSearch;$('play').onclick=()=>playing?pause():play();$('previous').onclick=()=>{pause();loadPick(current-1)};$('next').onclick=()=>{pause();loadPick(current+1)};$('sound').onclick=()=>{const on=$('sound').getAttribute('aria-pressed')!=='true';$('sound').setAttribute('aria-pressed',String(on));$('sound').textContent=on?'Sound on':'Sound off';video.muted=!on;};
$('scrub').oninput=()=>{if(!plan)return;pause();const t=+$('scrub').value;let i=plan.picks.findIndex(p=>t<p.recordOut);if(i<0)i=plan.picks.length-1;loadPick(i,Math.max(0,t-plan.picks[i].recordIn));};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>selectTab(b.dataset.tab));
for(const id of ['literal','continuity','intercut','surprise']){$(id).onchange=()=>{interventions.push({kind:'tuning',run:runSerial,time:new Date().toISOString(),control:id,value:+$(id).value});if(plan)runCompose({target:current});};}
$('loadText').onclick=()=>$('textFile').click();$('textFile').onchange=async()=>{const f=$('textFile').files?.[0];if(!f)return;$('sourceText').value=await f.text();status(`Loaded ${f.name}`);};
$('testFilter').oninput=()=>renderTests($('testFilter').value);
document.querySelectorAll('[data-call]').forEach(b=>b.onclick=()=>makeCall(b.dataset.call));
document.querySelectorAll('[data-call-now]').forEach(b=>b.onclick=()=>makeCall(b.dataset.callNow));
$('callApply').onclick=()=>{const x=parseCallText($('callText').value);if(!x){status('Call not understood. Try “same source, later shot”, “return to scene 2”, “hold shot for next 3”, or an operation name.');return;}makeCall(x.type,x);};
$('callText').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();$('callApply').click();}};
$('releaseCall').onclick=()=>{const target=current;releaseDirective(target);status('Released call on beat '+(target+1));if(plan)runCompose({target});};
$('clearCalls').onclick=()=>{calls.clear();directives.clear();renderPath();renderDirectCall();status('Calls cleared.');if(plan)runCompose({target:current});};
$('exportPath').onclick=exportPath;

const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!Recognition){$('listen').disabled=true;$('listen').textContent='Speech unavailable';}
$('listen').onclick=()=>{if(!Recognition)return;if(listening){recognition.stop();return;}recognition=new Recognition();recognition.continuous=true;recognition.interimResults=true;recognition.lang=navigator.language||'en-US';let fixed=$('sourceText').value.trim();recognition.onstart=()=>{listening=true;$('listen').textContent='Stop';status('Listening');};recognition.onresult=e=>{let interim='',done='';for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;if(e.results[i].isFinal)done+=t+' ';else interim+=t;}if(done){fixed=(fixed+' '+done).trim();$('sourceText').value=fixed;}if(interim)status('Hearing: '+interim);};recognition.onerror=e=>status('Speech: '+e.error);recognition.onend=()=>{listening=false;$('listen').textContent='Listen';status('Speech stopped');};try{recognition.start()}catch{status('Speech could not start')}};
window.addEventListener('pagehide',()=>{recognition?.stop();pause();});

await Promise.all([checkLocal(),loadCatalog()]);renderTests();renderInside();renderPath();renderDirectCall();status(local?'Local archive ready':'Hosted fallback ready');
