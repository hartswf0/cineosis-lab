import {TYPES} from '../syntagm/model.mjs';
import {validateReviews} from './review.mjs';
const types=[...TYPES,['outside','Outside this scheme','']],$=s=>document.querySelector(s);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=t=>`${Math.floor(t/60)}:${(t%60).toFixed(1).padStart(4,'0')}`;
const KEY='cineosis.source-patterns.v1';let D,annotations={},filtered=[],current,clipIndex=0,mode='preview',continuous=false,mediaKey=0,storageInvalid=false;
function notice(s){$('#notice').textContent=s;}
function state(p){return annotations[p.id]?.status||'candidate';}
function draft(p){return annotations[p.id]||{type:'unknown',rival:'unknown',relation:'unknown',structure:'',evidence:'',counterevidence:p.reading.counterevidence,reader:'',status:'candidate',fullContextAttested:false};}
function persist(next){try{localStorage.setItem(KEY,JSON.stringify(next));annotations=next;return true;}catch{notice('Could not save in this browser. Export before leaving.');return false;}}
function renderList(){
  const query=$('#search').value.toLowerCase(),film=$('#film').value,q=$('#question').value,st=$('#status').value;
  filtered=D.passages.filter(p=>(!film||p.slug===film)&&(!q||p.questionsToTest.includes(q))&&(!st||state(p)===st)&&JSON.stringify([p.title,p.tags,p.reading,p.slug,draft(p)]).toLowerCase().includes(query));
  $('#counts').textContent=`${D.sources.length} audited sources · ${D.passages.length} candidates · ${Object.values(annotations).filter(x=>x.status==='reviewed').length} reader-reviewed locally. Seed readings remain unresolved.`;
  $('#list').innerHTML=filtered.map(p=>`<button data-id="${p.id}" class="${current?.id===p.id?'active':''}"><b>${esc(p.title)}</b><small>${esc(D.sources.find(s=>s.slug===p.slug).title)}<br>${fmt(p.interval[0])}–${fmt(p.interval[1])} · ${state(p)}</small></button>`).join('')||'<p class="empty">No matches. Clear a filter.</p>';
  $('#pick').innerHTML=filtered.map(p=>`<option value="${p.id}">${esc(p.title)}</option>`).join('')||'<option>No matches</option>';
  if(current)$('#pick').value=current.id;
  $('#previous').disabled=!filtered.length;$('#next').disabled=!filtered.length;$('#operator').hidden=!filtered.length;if(!filtered.length)notice('No matching passages. Clear a filter to continue.');
}
function select(id){
  const p=D.passages.find(x=>x.id===id);if(!p)return;current=p;location.hash=p.id;continuous=false;clipIndex=Math.max(0,p.members.findIndex(id=>D.shots[id].preview));
  $('#filmName').textContent=D.sources.find(s=>s.slug===p.slug).title;$('#title').textContent=p.title;
  $('#bench').href='syntagm.html?'+new URLSearchParams({source:p.slug,first:p.first,count:p.members.length});
  $('#observation').textContent=p.reading.evidence;$('#counter').textContent=p.reading.counterevidence;
  $('#limits').textContent=`Sampled ${p.inspection.clipsSampled.length}/${p.members.length} silent cropped excerpts at 0%, 40%, 80% of each excerpt. Full clips, audio and autonomous boundaries were not reviewed. Exact excerpt offsets within source clips were not recorded.`;
  $('#facts').innerHTML=`SOURCE INTERVAL ${fmt(p.interval[0])}–${fmt(p.interval[1])}<br>${p.members.length} archive clips · camera-shot count unverified<br>${p.audit.gaps.length} missing intervals inside this window<br>TEST ${p.questionsToTest.map(t=>types.find(x=>x[0]===t)?.[1]).join(' / ')}<br>Seed type: UNRESOLVED`;
  const r=draft(p);for(const k of ['type','rival','relation','structure','evidence','reader'])$('#'+k).value=r[k];$('#rivalEvidence').value=r.counterevidence;$('#attest').checked=!!r.fullContextAttested;$('#readingState').textContent=state(p);
  renderList();renderClips();loadMedia('preview');
}
function renderClips(){
  $('#clips').innerHTML=current.members.map((id,i)=>{const c=D.shots[id];return `<button data-clip="${i}" class="${i===clipIndex?'on':''}"><b>Clip #${c.position}</b><small>${fmt(c.startSeconds)}–${fmt(c.endSeconds)}</small><small>${c.preview?'Local silent excerpt':'Original stream only'}</small></button>`;}).join('');
}
function loadMedia(nextMode,play=false){
  const c=D.shots[current.members[clipIndex]],v=$('#video');mode=nextMode;const key=++mediaKey;v.pause();$('#mediaError').hidden=true;$('#archive').href=c.page;$('#fallback').disabled=!c.preview;
  $('#preview').disabled=!c.preview;$('#preview').classList.toggle('on',mode==='preview');$('#original').classList.toggle('on',mode==='original');
  $('#mode').textContent=mode==='preview'?'SILENT EXCERPT · CROPPED · NOT THE FULL CLIP':'ORIGINAL ARCHIVE CLIP';
  $('#time').textContent=`Source clip ${fmt(c.startSeconds)}–${fmt(c.endSeconds)}`;
  if(mode==='preview'&&!c.preview){v.removeAttribute('src');v.removeAttribute('poster');v.load();$('#mediaError').hidden=false;$('#mode').textContent='NO LOCAL EXCERPT · OPEN ORIGINAL';return;}
  v.loop=mode==='preview';v.muted=mode==='preview';v.poster=c.thumb;v.src=mode==='preview'?c.preview:c.videoUrl;
  v.onloadedmetadata=()=>{if(key!==mediaKey)return;if(play)v.play().catch(e=>notice('Press play to start: '+e.message));};
  v.onerror=()=>{if(key!==mediaKey)return;continuous=false;$('#mediaError').hidden=false;notice('This media is unavailable here. No missing clip was skipped.');};
  v.load();renderClips();
}
function save(reviewed){
  if(storageInvalid){notice('Stored annotations failed validation. Import a valid export before saving; existing browser data is preserved.');return;}
  const r={members:current.members,interval:current.interval,type:$('#type').value,rival:$('#rival').value,relation:$('#relation').value,structure:$('#structure').value,
    evidence:$('#evidence').value,counterevidence:$('#rivalEvidence').value,reader:$('#reader').value,fullContextAttested:$('#attest').checked,
    status:reviewed?'reviewed':'draft',updatedAt:new Date().toISOString(),seedCommit:D.builtFrom};
  try{validateReviews({format:'cineosis-source-patterns-review/1',annotations:{[current.id]:r}},D,types.map(t=>t[0]));
    if(persist({...annotations,[current.id]:r})){renderList();$('#readingState').textContent=r.status;notice(reviewed?'Saved as reader-reviewed, based on your context attestation.':'Draft saved in this browser.');}
  }catch(e){notice(e.message);}
}
function exportFile(){
  const obj={format:'cineosis-source-patterns-review/1',exportedAt:new Date().toISOString(),seedCommit:D.builtFrom,annotations,
    seedAtlas:'source-patterns/data.json',note:'Seed observations remain frame-sampled candidates. Reviewed status records a named reader’s attestation.'};
  const a=document.createElement('a'),url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}));a.href=url;a.download='cineosis-source-patterns-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function auditRows(){
  const q=$('#auditSearch').value.toLowerCase();$('#auditRows').innerHTML=D.sources.filter(s=>s.title.toLowerCase().includes(q)).map(s=>`<div class="audit-row"><div><b>${esc(s.title)}</b><small>${s.audit.interval?fmt(s.audit.interval[0])+'–'+fmt(s.audit.interval[1]):'No clips'}</small><details><summary>Inspect intervals</summary>${s.audit.gaps.map(g=>`<p>Missing ${fmt(g[0])}–${fmt(g[1])}</p>`).join('')||'<p>No timestamp gaps inside the cached span.</p>'}<p>${s.audit.positionGaps.length} nonconsecutive position joins; ${s.audit.overlaps.length} overlaps.</p></details></div><span>${s.count} clips</span><span>${s.audit.coverage===null?'Unknown':(100*s.audit.coverage).toFixed(1)+'%'} coverage</span><span>${s.audit.gaps.length} gaps</span><a href="syntagm.html?${esc(new URLSearchParams({source:s.slug,first:1,count:3}))}">Inspect source ↗</a></div>`).join('');
}
async function boot(){
  try{
    const res=await fetch('source-patterns/data.json');if(!res.ok)throw Error('Atlas data: HTTP '+res.status);D=await res.json();
    try{const raw=JSON.parse(localStorage.getItem(KEY)||'{}');annotations=validateReviews({format:'cineosis-source-patterns-review/1',annotations:raw},D,types.map(t=>t[0]));}catch{storageInvalid=true;notice('Stored annotations could not be validated. They were not overwritten; export or inspect browser storage before saving.');}
    const seeds=new Set(D.passages.map(p=>p.slug));$('#film').innerHTML+=[...seeds].map(slug=>`<option value="${slug}">${esc(D.sources.find(s=>s.slug===slug).title)}</option>`).join('');
    const options=types.map(([k,n])=>`<option value="${k}">${n}</option>`).join('');$('#type').innerHTML=options;$('#rival').innerHTML=options;$('#question').innerHTML+=types.slice(1,-1).map(([k,n])=>`<option value="${k}">${n}</option>`).join('');
    for(const id of ['search','film','question','status'])$('#'+id).addEventListener('input',()=>{renderList();if(filtered.length&&!filtered.some(p=>p.id===current?.id))select(filtered[0].id);});
    $('#list').onclick=e=>{const b=e.target.closest('[data-id]');if(b)select(b.dataset.id);};$('#pick').onchange=e=>select(e.target.value);
    function step(n){const i=filtered.findIndex(p=>p.id===current.id);if(filtered.length)select(filtered[(i+n+filtered.length)%filtered.length].id);}
    $('#previous').onclick=()=>step(-1);$('#next').onclick=()=>step(1);
    $('#clips').onclick=e=>{const b=e.target.closest('[data-clip]');if(b){continuous=false;clipIndex=Number(b.dataset.clip);loadMedia(D.shots[current.members[clipIndex]].preview?'preview':'original');}};
    $('#preview').onclick=()=>{continuous=false;loadMedia('preview',true);};$('#original').onclick=()=>{continuous=false;loadMedia('original',true);};$('#fallback').onclick=()=>{continuous=false;loadMedia('preview',true);};
    $('#passage').onclick=()=>{clipIndex=0;continuous=true;loadMedia('original',true);};$('#video').onended=()=>{if(continuous&&clipIndex<current.members.length-1){clipIndex++;loadMedia('original',true);}else continuous=false;};
    $('#video').ontimeupdate=()=>{if(mode==='original'&&current)$('#time').textContent='Source '+fmt(D.shots[current.members[clipIndex]].startSeconds+$('#video').currentTime);};
    $('#save').onclick=()=>save(false);$('#review').onclick=()=>save(true);$('#reset').onclick=()=>{if(storageInvalid){notice('Existing invalid storage was preserved. Import a valid export first.');return;}const next={...annotations};delete next[current.id];if(persist(next))select(current.id);};
    $('#export').onclick=exportFile;$('#import').onclick=()=>$('#file').click();$('#file').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{const imported=validateReviews(JSON.parse(await f.text()),D,types.map(t=>t[0]));if(persist({...annotations,...imported})){storageInvalid=false;select(current.id);notice('Imported annotations with matching source intervals and clip IDs.');}}catch(err){notice('Import failed: '+err.message);}e.target.value='';};
    $('#audit').onclick=()=>{auditRows();$('#auditDialog').showModal();};$('#closeAudit').onclick=()=>$('#auditDialog').close();$('#auditSearch').oninput=auditRows;
    window.addEventListener('hashchange',()=>{if(location.hash.slice(1)!==current?.id)select(location.hash.slice(1));});
    const id=D.passages.some(p=>p.id===location.hash.slice(1))?location.hash.slice(1):D.passages[0].id;select(id);
    notice('24 candidate passages · 34 silent excerpts sampled · 0 complete-passage seed readings. Read originals before assigning a syntagm.');
  }catch(e){notice('Could not load atlas: '+e.message);}
}
boot();
