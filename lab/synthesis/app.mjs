import {METZ,DELEUZE,compile,comparePlans} from './model.mjs';
const $=id=>document.getElementById(id),engine=document.body.dataset.engine,other=engine==='metz'?'deleuze':'metz';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ROOT=window.CINEOSIS_BASE||new URL('./',location.href).href;
const media=p=>new URL(p,ROOT).href;
let catalog,plan,pending=null,playing=false,index=0,record=0,holdElapsed=0,lastTick=0,seeking=false,generation=0,loadedKey='',debounce,recognition,listening=false,exampleIndex=0;
const film=$('film'),specs=engine==='metz'?METZ:DELEUZE,chosenSigns=new Set();
const examples=[['telephone','She calls while he listens.'],['telephone','She calls. After the call, he listens again.'],['feast','Some feast, whereas others wait for bread.'],['sower','Every evening, the field remembers. Nothing is resolved.'],['fire','He descends, then boards the engine, then leaves.'],['all','A face watches the water. The voice continues after the image disappears.']];
$('heading').textContent=engine==='metz'?'Make a relation.':'Change what the image does.';
$('operation').innerHTML='<option value="auto">From the words · visible rules</option>'+Object.entries(specs).map(([k,v])=>`<option value="${k}">${esc(v[0])}</option>`).join('');
if(engine==='deleuze'){$('text').value='She waits. The call cannot become an answer.';document.documentElement.style.setProperty('--accent','#a5c8ff');}
const params=new URLSearchParams(location.search);let importedText=params.get('text');if(importedText)$('text').value=importedText.slice(0,10000);
for(const key of ['material','span','duration'])if(params.has(key))$(key).value=params.get(key);
if(!$('material').value)$('material').value='telephone';
for(const n of (params.get('signs')||'').split(','))if(n)chosenSigns.add(n);
$('budget').textContent=$('duration').value+' s';$('window').textContent=$('span').value+' s';
$('tableLink').href=new URL('../periodic-table.html',ROOT).href;
const status=s=>$('status').textContent=s;
const options=()=>({mode:$('operation').value,material:$('material').value,span:+$('span').value,duration:+$('duration').value,signs:[...chosenSigns]});
function synthesize({immediate=false}={}){
 if(!catalog)return;
 const text=$('text').value.trim();if(!text){status('Write or speak a phrase first.');return;}
 try{
  const next=compile(text,engine,catalog,options());
  const shared=new URLSearchParams({text,material:$('material').value,span:$('span').value,duration:$('duration').value,signs:[...chosenSigns].join(',')});$('other').href=(window.CINEOSIS_OTHER||`${other}-synthesis.html`)+'?'+shared;
  if(playing&&!immediate){pending=next;status('New score queued · enters at next interval');return;}
  setPlaying(false);pending=null;plan=next;record=0;render();loadInterval(0,0);status('Score ready · '+plan.items.length+' intervals');
 }catch(e){status(e.message);}
}
function render(){
 $('play').disabled=false;$('scrub').max=plan.duration;$('claimTitle').textContent=plan.title+' · proposed';$('claim').textContent=plan.claim;
 $('coverage').textContent=plan.coverage;$('cue').textContent=plan.cue;
 $('timeline').innerHTML=plan.items.map((x,i)=>`<button class="node" data-index="${i}" aria-label="Interval ${i+1}: ${esc(x.role)}"><img alt="" src="${x.poster?media(x.poster):''}" ${x.poster?'':'hidden'}><span class="info"><b>${String(i+1).padStart(2,'0')} · ${x.duration.toFixed(1)}s</b>${esc(x.role)}<small>${esc(x.strand||'gap')}${x.hold?' · '+x.hold.toFixed(1)+'s held frame':''}</small></span></button>`).join('');
 $('timeline').querySelectorAll('button').forEach(b=>b.onclick=()=>{pending=null;loadInterval(+b.dataset.index,0);});
 $('candidates').innerHTML=plan.ranking.slice(0,8).map(r=>{let s=catalog.shots.find(x=>x.id===r.id);return `<div class="candidate"><img src="${media(s.poster)}" alt=""><div><p>${esc(s.title)}</p><p class="subtle">${esc(r.hits.length?'Description: '+r.hits.join(', '):r.hintHits.length?'Search hints only: '+r.hintHits.join(', '):'Structural fallback')}${r.signHits.length?' · signs '+esc(r.signHits.join(', ')):''}</p><button data-inspect="${esc(s.id)}">Read evidence</button></div></div>`;}).join('');
 $('candidates').querySelectorAll('button').forEach(b=>b.onclick=()=>{let s=catalog.shots.find(x=>x.id===b.dataset.inspect);$('currentEvidence').textContent=s.reading+': '+s.description;status(s.title);});
 $('stripTitle').textContent=`${engine.toUpperCase()} · ${plan.items.length} INTERVALS · ${plan.duration.toFixed(1)}s`;
}
function reportError(message){setPlaying(false);$('failure').hidden=false;$('errorText').textContent=message;status('Playback stopped · source unavailable');}
function loadInterval(i,offset=0){
 if(!plan?.items[i])return;
 const token=++generation;index=i;const x=plan.items[index];holdElapsed=0;record=x.recordIn+offset;
 $('failure').hidden=true;$('modeTag').textContent=x.role.toUpperCase();$('words').textContent=plan.text;$('source').textContent=x.title||'BLACK INTERVAL';
 $('currentEvidence').textContent=x.description?`${x.description} · ${x.sourceIn.toFixed(2)}s in source${x.hold?' · held frame explicitly added':''}`:'Voice continues on its own clock. No footage is shown.';
 $('sourceLink').href=x.source||'#';$('sourceLink').hidden=!x.source;
 $('timeline').querySelectorAll('button').forEach((b,j)=>b.classList.toggle('active',j===index));
 film.pause();film.style.visibility=x.media?'visible':'hidden';
 if(!x.media){seeking=false;holdElapsed=offset;updateClock();return;}
 seeking=true;
 const sourceDuration=x.out-x.in,position=x.in+Math.min(offset,Math.max(0,sourceDuration-.03));
 holdElapsed=Math.max(0,offset-sourceDuration);
 const ready=()=>{
  if(token!==generation)return;
  if(!Number.isFinite(film.duration)||x.out>film.duration+.25){reportError('The media duration differs from the catalogue. Inspect its source interval.');return;}
  film.currentTime=position;
  const done=()=>{if(token!==generation)return;seeking=false;if(playing&&offset<sourceDuration)film.play().catch(e=>{if(e.name!=='AbortError')reportError('Press Play again to start this browser’s media playback.');});updateClock();};
  if(Math.abs(film.currentTime-position)<.005&&!film.seeking)done();else film.addEventListener('seeked',done,{once:true});
 };
 const url=media(x.media);
 if(loadedKey!==url){loadedKey=url;film.src=url;film.addEventListener('loadedmetadata',ready,{once:true});film.load();}
 else if(film.readyState>=1)ready();else film.addEventListener('loadedmetadata',ready,{once:true});
 updateClock();
}
function updateClock(){$('scrub').value=record;$('clock').textContent=record.toFixed(1)+' / '+(plan?.duration||0).toFixed(1);}
function speak(){
 if(!$('voice').checked||!('speechSynthesis'in window)||!plan)return;
 speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(plan.text);u.rate=.9;u.onerror=()=>status('Synthetic voice unavailable; text and footage remain playable.');speechSynthesis.speak(u);
}
function setPlaying(value){playing=value;$('play').textContent=value?'Ⅱ Pause':'▶ Play';lastTick=performance.now();
 if(!value){film.pause();if('speechSynthesis'in window)speechSynthesis.pause();}
 else{const x=plan?.items[index];if(x?.media&&!seeking&&record-x.recordIn<x.out-x.in)film.play().catch(e=>{if(e.name!=='AbortError')reportError('Browser playback requires another press of Play.');});if('speechSynthesis'in window)speechSynthesis.resume();}
}
function advance(){
 if(pending){plan=pending;pending=null;record=0;render();loadInterval(0);speak();status('Queued language is now playing.');return;}
 if(index+1>=plan.items.length){record=plan.duration;setPlaying(false);if('speechSynthesis'in window)speechSynthesis.cancel();status('End of score · replay or change the words');updateClock();return;}
 loadInterval(index+1);
}
function tick(now){
 const dt=Math.min(.1,(now-lastTick)/1000||0);lastTick=now;
 if(playing&&plan&&!seeking){const x=plan.items[index];
  if(!x.media){holdElapsed+=dt;record=x.recordIn+holdElapsed;if(holdElapsed>=x.duration)advance();}
  else {const len=x.out-x.in;
   if(film.currentTime>=x.out-.045||film.ended){film.pause();holdElapsed+=dt;record=x.recordIn+len+holdElapsed;$('modeTag').textContent=x.hold?'HELD FRAME · '+Math.max(0,x.hold-holdElapsed).toFixed(1)+'s':x.role.toUpperCase();if(holdElapsed>=x.hold)advance();}
   else record=x.recordIn+Math.max(0,film.currentTime-x.in);
  }updateClock();
 }requestAnimationFrame(tick);
}
film.addEventListener('error',()=>{if(loadedKey)reportError('This bundled clip did not load. Retry or open its source.');});
$('play').onclick=()=>{if(!plan)return;if(!playing&&record>=plan.duration-.05){loadInterval(0);speak();}else if(!playing&&record<.1)speak();setPlaying(!playing);};
$('make').onclick=()=>synthesize({immediate:true});
$('retry').onclick=()=>{loadedKey='';loadInterval(index);};
$('back').onclick=()=>{pending=null;loadInterval(Math.max(0,index-1));};$('next').onclick=()=>{pending=null;loadInterval(Math.min(plan.items.length-1,index+1));};
$('scrub').oninput=()=>{if(!plan)return;pending=null;const t=+$('scrub').value;const i=plan.items.findIndex(x=>t<x.recordOut);loadInterval(i<0?plan.items.length-1:i,t-(plan.items[i<0?plan.items.length-1:i].recordIn));};
$('sound').onclick=()=>{film.muted=!film.muted;$('sound').textContent=film.muted?'Sound off':'Sound on';$('sound').setAttribute('aria-pressed',String(!film.muted));};
function schedule(){clearTimeout(debounce);if($('live').checked)debounce=setTimeout(()=>synthesize(),650);else status('Text changed · press Synthesize');}
$('text').oninput=schedule;
for(const id of ['operation','material','duration','span'])$(id).oninput=()=>{$('budget').textContent=$('duration').value+' s';$('window').textContent=$('span').value+' s';schedule();};
$('example').onclick=()=>{exampleIndex=(exampleIndex+1)%examples.length;const [material,text]=examples[exampleIndex];$('material').value=material;$('text').value=text;$('operation').value='auto';synthesize({immediate:true});};
$('voice').onchange=()=>{if(!('speechSynthesis'in window)){status('Read-aloud is not available in this browser.');$('voice').checked=false;return;}if(!$('voice').checked)speechSynthesis.cancel();else if(playing)speak();};
function drawPalette(){
 $('palette').innerHTML=catalog.signs.map(s=>`<button title="${esc(s.name)}" aria-label="${esc(s.symbol+' · '+s.name)}" aria-pressed="${chosenSigns.has(s.n)}" class="${chosenSigns.has(s.n)?'selected':''}" data-sign="${s.n}">${s.symbol}</button>`).join('');
 $('palette').querySelectorAll('button').forEach(b=>b.onclick=()=>{const s=catalog.signs.find(s=>s.n===b.dataset.sign);chosenSigns.has(s.n)?chosenSigns.delete(s.n):chosenSigns.add(s.n);$('signInfo').textContent=s.name+': '+s.difference;drawPalette();schedule();});
}
$('clearSigns').onclick=()=>{chosenSigns.clear();drawPalette();$('signInfo').textContent='No sign constraint.';schedule();};
for(const b of document.querySelectorAll('[data-panel]'))b.onclick=()=>{document.querySelectorAll('.panel').forEach(p=>p.hidden=p.id!==b.dataset.panel);document.querySelectorAll('[data-panel]').forEach(x=>x.setAttribute('aria-selected',String(x===b)));};
$('method').onclick=()=>$('about').showModal();document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>b.closest('dialog').close());
$('compare').onclick=()=>{
 if(!catalog)return;
 const opts=options(),modeA=engine==='metz'?'alternate':'action',modeB=engine==='metz'?'ordinary':'suspend';
 const a=compile($('text').value,engine,catalog,{...opts,mode:modeA}),b=compile($('text').value,engine,catalog,{...opts,mode:modeB}),c=comparePlans(a,b);
 $('comparisonBody').innerHTML=[a,b].map((p,i)=>`<div><p class="eyebrow">${i?'B':'A'} · ${esc(p.title)}</p><p>${esc(p.items.map(x=>x.strand||'gap').join(' → '))}</p><p>${p.items.length-1} cuts · ${p.duration.toFixed(1)}s · ${p.items.reduce((s,x)=>s+x.hold,0).toFixed(1)}s held frame</p><button data-version="${i}">Play ${i?'B':'A'}</button></div>`).join('');
 $('comparisonResult').textContent='Available source pool is unchanged. '+(engine==='metz'?'Order changes; the words remain fixed. Judge whether the temporal relation changes.':'The response is withheld in B. Judge what the longer interval does; it does not automatically become an opsign.');
 $('comparisonBody').querySelectorAll('button').forEach(btn=>btn.onclick=()=>{setPlaying(false);pending=null;plan=+btn.dataset.version?b:a;record=0;render();loadInterval(0);$('comparison').close();setPlaying(true);speak();});
 $('comparison').showModal();
};
$('export').onclick=()=>{if(!plan)return;const doc={...plan,created:new Date().toISOString(),mediaBase:ROOT,voice:$('voice').checked?'browser synthetic reading; not included':'none',sourceSound:!film.muted,signConstraints:[...chosenSigns]};const blob=new Blob([JSON.stringify(doc,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=engine+'-synthesis.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status('Exported source ranges, screen timing, words and proposed readings.');};
const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!Recognition){$('mic').disabled=true;$('mic').textContent='Speech unavailable';$('mic').title='Use text input; this browser does not provide speech recognition.';}
$('mic').onclick=()=>{
 if(listening){recognition.stop();return;}
 recognition=new Recognition();recognition.continuous=true;recognition.interimResults=true;recognition.lang=navigator.language||'en-US';
 let prefix=$('text').value.trim();recognition.onstart=()=>{listening=true;$('mic').textContent='■ Stop';status('Listening · final phrases append to the score');};
 recognition.onresult=e=>{let final='',interim='';for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal)final+=e.results[i][0].transcript+' ';else interim+=e.results[i][0].transcript;}
  if(final){prefix=(prefix+' '+final).trim();$('text').value=prefix;synthesize();}if(interim)status('Hearing: '+interim);
 };
 recognition.onerror=e=>status('Speech: '+e.error+'. You can keep typing.');recognition.onend=()=>{listening=false;$('mic').textContent='● Speak';};
 try{recognition.start();}catch(e){status('Speech could not start. Use text input.');}
};
window.addEventListener('pagehide',()=>{recognition?.stop();if('speechSynthesis'in window)speechSynthesis.cancel();});
try{
 catalog=window.CINEOSIS_CATALOG||await fetch(media('synthesis/catalog.json')).then(r=>{if(!r.ok)throw Error('Catalogue could not load');return r.json();});
 drawPalette();$('loading').hidden=true;synthesize({immediate:true});status(catalog.shots.length+' playable intervals · no poem rankings');requestAnimationFrame(tick);
}catch(e){$('loading').innerHTML='<h2>Archive unavailable</h2><p>'+esc(e.message)+'</p>';status('Reload when the archive is reachable.');}
