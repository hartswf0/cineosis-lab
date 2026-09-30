import { createEngine, initial, suggest, graphDocument } from './engine.js';

const $ = id => document.getElementById(id);
const clone = value => structuredClone(value);
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = seconds => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
const canvas = $('canvas'), ctx = canvas.getContext('2d');
let project = initial(), film, engine, frame = 0, view = 'world', playing = false;
let history = [], takes = [], compare = false, selectedTake = 0, drag, serial = 0, computing = false, dirty = false, recording = false;
let bounds = { x: 0, y: 0, w: 1, h: 1 }, viewport = { w: 1, h: 1 }, lastTick = 0;
let selectedNode = 'motor', traceDetail = false;
const storageKey = 'cineosis-cascade-engine-v1';

function validated(value) {
  if (!value || !Array.isArray(value.cues) || value.cues.length < 1 || value.cues.length > 8 || !value.world) throw new Error('A session needs 1 to 8 scenes and a world.');
  const point = p => Array.isArray(p) && p.length === 2 && p.every(n => Number.isFinite(n) && n >= .04 && n <= .96);
  const w = value.world;
  if (!point(w.origin) || !point(w.target) || !Array.isArray(w.stones) || w.stones.length > 5 || !w.stones.every(point) || !Number.isFinite(w.gapY) || w.gapY < .12 || w.gapY > .88 || !Number.isFinite(w.gap) || w.gap < .02 || w.gap > .70) throw new Error('World coordinates are outside the supported range.');
  return { title: String(value.title || 'Untitled score').slice(0, 100), world: clone(w), cues: value.cues.map(c => {
    if (!['cross','hold','return','depart'].includes(c.action) || !Number.isFinite(c.duration) || c.duration < .5 || c.duration > 8) throw new Error('Invalid scene action or duration.');
    return { text: String(c.text || '').slice(0, 240), action: c.action, duration: c.duration };
  }) };
}
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify({ project, takes: takes.map(t => ({ name:t.name, project:t.project })), selectedTake })); }
  catch { $('runtime-status').textContent = 'Storage full; export to keep changes'; }
}
function checkpoint() { history.push(clone(project)); if (history.length > 40) history.shift(); $('undo').disabled = false; }
function update(mutator, remember = true) { if (recording) return; if (remember) checkpoint(); mutator(); playing = false; frame = 0; renderInspector(); requestCompose(); }
async function requestCompose() {
  dirty = true;
  if (computing) return;
  computing = true;
  try {
    while (dirty) {
      dirty = false;
      const next = await engine.compose(clone(project.cues), clone(project.world));
      if (!dirty) { film = next; frame = clamp(frame, 0, Math.max(0, film.frames.length - 1)); }
    }
    $('scrub').max = Math.max(0, film.frames.length - 1);
    $('runtime-status').textContent = 'Cascade runtime 0.7.1';
    persist(); renderStatus(); draw();
  } catch (error) { $('status').textContent = 'Could not compose'; $('reason').textContent = error.message; }
  finally { computing = false; }
}
function switchPanel(panel) {
  document.querySelectorAll('[data-panel]').forEach(b => b.setAttribute('aria-selected', b.dataset.panel === panel));
  ['score','conditions','takes'].forEach(p => $(`${p}-panel`).hidden = p !== panel);
}
function setView(next) {
  view = next;
  document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', b.dataset.view === view));
  canvas.setAttribute('aria-label', view==='trace' ? 'Causal trace. Left and right arrows select a stage; Enter toggles detail.' : 'Interactive world. Drag start, destination, passage, or stepping stones. Keyboard alternatives are in Conditions.');
  $('hint').textContent = view === 'world' ? 'Drag the passage or add a stepping stone.' : view === 'film' ? 'The same actions, assembled as shots.' : 'Select a stage to inspect its inputs and consequences.';
  draw();
}
function renderInspector() {
  $('title').textContent = project.title;
  $('cues').innerHTML = project.cues.map((cue, i) => `<article class="cue" data-cue="${i}"><div class="cue-head"><span class="cue-number">SCENE ${String(i+1).padStart(2,'0')}</span><select aria-label="Action for scene ${i+1}" data-action="${i}">${[['cross','Cross to destination'],['hold','Hold position'],['return','Return to start'],['depart','Leave the frame']].map(([v,t])=>`<option value="${v}" ${cue.action===v?'selected':''}>${t}</option>`).join('')}</select><button data-remove="${i}" ${project.cues.length===1?'disabled':''} aria-label="Remove scene ${i+1}">Remove</button></div><textarea aria-label="Words for scene ${i+1}" maxlength="240" data-text="${i}">${escape(cue.text)}</textarea><label>Minimum length <input data-duration="${i}" aria-label="Minimum duration for scene ${i+1}" type="range" min="0.5" max="8" step="0.5" value="${cue.duration}"><output>${cue.duration}s</output></label></article>`).join('');
  $('add-cue').disabled = project.cues.length >= 8;
  $('gap-y').value = project.world.gapY*100; $('gap').value = project.world.gap*100;
  $('origin-y').value = project.world.origin[1]*100; $('target-y').value = project.world.target[1]*100;
  $('gap-y-value').textContent = `${Math.round(project.world.gapY*100)}%`;
  $('gap-value').textContent = `${Math.round(project.world.gap*100)}%`;
  $('stones').innerHTML = project.world.stones.map((p,i)=>`<div class="stone-row"><span>Stone ${i+1}</span><label>X <input data-stone="${i}" data-axis="0" aria-label="Stone ${i+1} X" type="number" min="4" max="96" value="${Math.round(p[0]*100)}"></label><label>Y <input data-stone="${i}" data-axis="1" aria-label="Stone ${i+1} Y" type="number" min="4" max="96" value="${Math.round(p[1]*100)}"></label><button data-delete-stone="${i}" aria-label="Remove stone ${i+1}">Remove</button></div>`).join('');
  $('add-stone').disabled = project.world.stones.length >= 5;
  $('clear-stones').disabled = project.world.stones.length === 0;
  $('undo').disabled = !history.length;
  renderTakes();
}
function renderTakes() {
  $('count').textContent = takes.length;
  $('compare').disabled = takes.length === 0;
  $('compare').textContent = compare ? 'Hide comparison' : 'Compare';
  $('take-summary').textContent = compare && takes[selectedTake] ? `Dashed route: ${takes[selectedTake].name}` : takes.length ? `${takes.length} saved ${takes.length === 1 ? 'take' : 'takes'}` : 'Keep a take, then change one condition.';
  $('takes').innerHTML = takes.length ? takes.map((t,i)=>`<article class="take ${i===selectedTake?'active':''}"><strong>${escape(t.name)}</strong><p>${t.film.blocked?'Blocked':'Complete'} · ${t.film.completed}/${t.project.cues.length} scenes · ${t.film.duration.toFixed(1)}s</p><div class="inline"><button data-restore="${i}">Restore</button><button data-compare="${i}">Compare</button><button data-delete-take="${i}">Delete</button></div></article>`).join('') : '<p class="fine">No takes yet. Keep this attempt before opening a passage.</p>';
}
function currentFrame() { return film?.frames[frame] || {p:project.world.origin, scene:0, status:'ready', lens:'wide'}; }
function renderStatus() {
  if (!film) return;
  const f = currentFrame(), cue = project.cues[f.scene];
  $('frame-label').textContent = `${String(f.scene+1).padStart(2,'0')} / ${cue?.action || 'scene'} · ${f.status}`;
  $('take-label').textContent = compare && takes[selectedTake] ? `vs ${takes[selectedTake].name}` : `${film.completed}/${project.cues.length} scenes completed`;
  $('status').textContent = film.blocked ? 'The route meets a barrier.' : 'The sequence can complete.';
  $('reason').textContent = film.blocked ? 'Move a condition or add an intermediate destination. Later scenes wait.' : `${film.completed} scenes assembled. ${project.world.stones.length ? 'The route includes your stepping stones.' : 'The route is clear.'}`;
  $('indicator').classList.toggle('blocked',film.blocked);
  $('passage').textContent = project.world.stones.length ? 'Align passage' : 'Find passage';
  $('time').textContent = `${fmt(frame/30)} / ${fmt(film.duration)}`;
  $('scrub').value = frame; $('play').textContent = playing ? 'Pause' : 'Play';
  $('play').setAttribute('aria-label',playing?'Pause film':'Play film');
  document.querySelectorAll('.cue').forEach(el=>el.classList.toggle('selected',Number(el.dataset.cue)===f.scene));
}
function resize() {
  const r = $('viewport').getBoundingClientRect(), dpr = Math.min(devicePixelRatio||1, 2);
  viewport = { w:r.width, h:r.height };
  canvas.width = Math.round(r.width*dpr); canvas.height = Math.round(r.height*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0); draw();
}
function sceneBounds() {
  const pad = view==='film'?0:Math.max(30,Math.min(viewport.w*.075,65));
  return {x:pad,y:35,w:viewport.w-pad*2,h:Math.max(20,viewport.h-75)};
}
function projectPoint(p,b=bounds) { return [b.x+p[0]*b.w,b.y+p[1]*b.h]; }
function line(a,b,color,width=1,dash=[]) {ctx.beginPath();ctx.setLineDash(dash);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.setLineDash([]);}
function text(label,x,y,size=10,color='#64725c',align='left') {ctx.fillStyle=color;ctx.font=`${size}px "DM Sans", sans-serif`;ctx.textAlign=align;ctx.fillText(label,x,y);}
function drawRoute(points,color,width=1,dashed=false,b=bounds) { if(points.length<2)return;ctx.beginPath();ctx.setLineDash(dashed?[5,5]:[]);ctx.strokeStyle=color;ctx.lineWidth=width;points.forEach((p,i)=>{const q=projectPoint(p,b);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.stroke();ctx.setLineDash([]);}
function draw() {
  const {w,h}=viewport;
  ctx.clearRect(0,0,w,h); ctx.fillStyle=view==='film'?'#14291f':'#dce2d2';ctx.fillRect(0,0,w,h);
  $('overlay').style.color=view==='film'?'#dfe7d2':'#45523e';
  $('hint').style.color=view==='film'?'#95aa90':'#64725c';
  if(view==='trace'){drawTrace();return;}
  bounds=sceneBounds(); const world=project.world, f=currentFrame();
  const filmMode=view==='film';
  if(filmMode){
    const zoom=f.lens==='close'?1.8:f.lens==='follow'?1.15:1;
    if(f.lens!=='wide')bounds={w:bounds.w*zoom,h:bounds.h*zoom,x:viewport.w/2-f.p[0]*bounds.w*zoom,y:viewport.h/2-f.p[1]*bounds.h*zoom};
  } else {
    for(let x=0;x<=1;x+=.05)for(let y=0;y<=1;y+=.05){const p=projectPoint([x,y]);ctx.fillStyle='#b4bfa9';ctx.fillRect(p[0],p[1],1,1);}
  }
  const top=world.gapY-world.gap/2,bottom=world.gapY+world.gap/2;
  const wallX=bounds.x+(.5-.018)*bounds.w,wallW=.036*bounds.w;
  ctx.fillStyle=filmMode?'#718568':'#a4b097';
  ctx.fillRect(wallX,bounds.y,wallW,Math.max(0,top)*bounds.h);
  ctx.fillRect(wallX,bounds.y+bottom*bounds.h,wallW,Math.max(0,1-bottom)*bounds.h);
  if(!filmMode){
    line(projectPoint([.5,top]),projectPoint([.5,bottom]),'#6b8a55',1,[3,4]);
    text('PASSAGE',wallX+wallW+9,bounds.y+world.gapY*bounds.h,9);
    const future=[world.origin,...world.stones,world.target];drawRoute(future,'#93a382',1,true);
    if(compare&&takes[selectedTake]){
      drawRoute(takes[selectedTake].film.frames.map(f=>f.p),'#ab765e',2,true);
      const old=takes[selectedTake].project.world;
      line(projectPoint([.5,old.gapY-old.gap/2]),projectPoint([.5,old.gapY+old.gap/2]),'#ab765e',4,[3,3]);
    }
    if(film)drawRoute(film.frames.slice(0,frame+1).map(f=>f.p),'#547442',2);
    for(const [label,p] of [['START',world.origin],['DESTINATION',world.target]]){
      const q=projectPoint(p);ctx.strokeStyle='#718661';ctx.lineWidth=1;ctx.beginPath();ctx.arc(...q,11,0,Math.PI*2);ctx.stroke();
      text(label,q[0],q[1]+25,8,'#526747','center');
    }
    world.stones.forEach((p,i)=>{const q=projectPoint(p);ctx.fillStyle='#f0f0d8';ctx.beginPath();ctx.arc(...q,13,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#668052';ctx.stroke();text(String(i+1),q[0],q[1]+4,10,'#2e5b41','center')});
  }
  const actor=projectPoint(f.p),size=Math.max(10,.036*Math.min(bounds.w,bounds.h));
  ctx.fillStyle='#182e2050';ctx.fillRect(actor[0]-size/2+3,actor[1]-size/2+4,size,size);
  ctx.fillStyle=f.status==='blocked'?'#b56340':filmMode?'#d9e7b9':'#2e5b41';ctx.fillRect(actor[0]-size/2,actor[1]-size/2,size,size);
  if(f.status==='blocked'){
    ctx.strokeStyle=filmMode?'#eebd99':'#a45333';ctx.lineWidth=1;ctx.beginPath();ctx.arc(...actor,size+6,0,Math.PI*2);ctx.stroke();
    if(!filmMode)text('STOPPED',actor[0]-10,actor[1]-size-13,9,'#914d32','right');
  }
  if(filmMode){
    ctx.fillStyle='#14291f';ctx.fillRect(0,0,w,35);ctx.fillRect(0,h-45,w,45);
    const words=project.cues[f.scene]?.text||'';const short=words.length>74?words.slice(0,71)+'…':words;
    ctx.font=`${Math.min(15,w/28)}px sans-serif`; let caption=short; while(ctx.measureText(caption).width>w-28)caption=caption.slice(0,-2); text(caption+(caption.length<short.length?'…':''),w/2,h-52,Math.min(15,w/28),'#eff0df','center');
  }
}
function drawTrace() {
  const {w,h}=viewport,f=currentFrame();
  const labels=[['score','Score',`${project.cues.length} scenes`],['route','Route',`${project.world.stones.length} stones`],['motor','Motor',film?.blocked?'blocked':'clear']];
  const margin=w<500?18:35,gap=12,boxW=(w-2*margin-2*gap)/3,boxH=Math.min(67,h*.28),y=48;
  labels.forEach(([id,label,value],i)=>{const x=margin+i*(boxW+gap);ctx.fillStyle=selectedNode===id?'#2e5b41':'#e9edde';ctx.fillRect(x,y,boxW,boxH);text(label,x+12,y+22,12,selectedNode===id?'#f1f3e8':'#2e5b41');text(value,x+12,y+boxH-12,10,selectedNode===id?'#d1dfc2':'#64725c');if(i<2)line([x+boxW,y+boxH/2],[x+boxW+gap,y+boxH/2],'#718661');});
  const title=selectedNode==='score'?'The words have an explicit action.':selectedNode==='route'?'Intermediate destinations change the route.':'Every next position must fit the world.';
  const detail=traceDetail ? `Frame ${frame}; position [${f.p.map(n=>n.toFixed(3)).join(', ')}]; status ${f.status}.` : selectedNode==='score'?`Scene ${f.scene+1}: ${project.cues[f.scene]?.action||'hold'}. Unrecognized pasted lines start as HOLD.`:selectedNode==='route'?`${project.world.stones.length? 'Via '+project.world.stones.length+' stones':'Direct route'}; return reverses those stones.`:`Body width 3.6%; passage ${Math.round(project.world.gap*100)}%. ${film?.blocked?'Collision revokes the action.':'No collision in the full sequence.'}`;
  const contentY=y+boxH+24;
  text(title,margin,contentY,w<500?11:14,'#2e5b41');
  wrapText(detail,margin,contentY+22,w-2*margin,16,10,'#64725c');
  if(h>280){
    const events=(film?.events||[]).slice(0,6);let ey=contentY+65;
    events.forEach(e=>{text(`${fmt(e.frame/30)}  ${e.kind==='blocked'?'STOP':e.kind.toUpperCase()}  ·  scene ${e.scene+1}`,margin,ey,10,e.kind==='blocked'?'#a45333':'#526747');ey+=19;});
    if(traceDetail){let x=w*.52;const p=f.p.map(n=>n.toFixed(3)).join(', ');text(`position [${p}]`,x,contentY+65,10);text(`frame ${frame} / ${film?.frames.length||0}`,x,contentY+84,10);text(`status ${f.status}`,x,contentY+103,10);}
  }
  text(traceDetail?'Detail visible · tap again to simplify':'Tap a stage again for numerical detail',margin,h-35,9);
}
function wrapText(value,x,y,width,lineHeight,size,color){let line='';for(const word of value.split(' ')){const test=line+word+' ';ctx.font=`${size}px sans-serif`;if(ctx.measureText(test).width>width&&line){text(line,x,y,size,color);line=word+' ';y+=lineHeight}else line=test}text(line,x,y,size,color)}
function animate(now) {
  if(playing && film && !recording && now-lastTick>=1000/30){frame+=Math.max(1,Math.floor((now-lastTick)/(1000/30)));lastTick=now;if(frame>=film.frames.length-1){frame=film.frames.length-1;playing=false}renderStatus();draw();}
  requestAnimationFrame(animate);
}

$('play').onclick=()=>{if(!film||recording)return;if(frame>=film.frames.length-1)frame=0;playing=!playing;lastTick=performance.now();renderStatus();draw()};
$('restart').onclick=()=>{if(recording)return;frame=0;playing=true;lastTick=performance.now();renderStatus();draw()};
$('scrub').oninput=()=>{if(recording)return;playing=false;frame=Number($('scrub').value);renderStatus();draw()};
$('undo').onclick=()=>{if(!history.length||recording)return;project=history.pop();playing=false;frame=0;renderInspector();requestCompose()};
$('passage').onclick=()=>update(()=>{project.world.stones=[[.5,project.world.gapY]];project.world.gap=Math.max(.10,project.world.gap)});
$('add-stone').onclick=()=>update(()=>{if(project.world.stones.length<5)project.world.stones.push([.5,project.world.gapY])});
$('clear-stones').onclick=()=>update(()=>project.world.stones=[]);
$('add-cue').onclick=()=>update(()=>{if(project.cues.length<8)project.cues.push({text:'A moment passes.',action:'hold',duration:2})});
$('reset').onclick=()=>update(()=>project=initial());
$('save').onclick=async()=>{if(!film||computing||recording)return;if(takes.length>=12){showDialog('Twelve takes kept','<p>Export this session or delete a take before saving another.</p>');return}const name=`Take ${++serial}`;takes.push({name,project:clone(project),film:clone(film)});selectedTake=takes.length-1;renderTakes();persist()};
$('compare').onclick=()=>{compare=!compare;renderTakes();renderStatus();draw()};
for(const b of document.querySelectorAll('[data-panel]'))b.onclick=()=>switchPanel(b.dataset.panel);
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>setView(b.dataset.view);
$('cues').addEventListener('change',e=>{const el=e.target;if(el.dataset.action!==undefined)update(()=>project.cues[+el.dataset.action].action=el.value);if(el.dataset.text!==undefined)update(()=>project.cues[+el.dataset.text].text=el.value);if(el.dataset.duration!==undefined)update(()=>project.cues[+el.dataset.duration].duration=+el.value)});
$('cues').addEventListener('input',e=>{if(e.target.dataset.duration!==undefined)e.target.nextElementSibling.textContent=e.target.value+'s'});
$('cues').addEventListener('click',e=>{if(e.target.dataset.remove!==undefined)update(()=>project.cues.splice(+e.target.dataset.remove,1))});
for(const id of ['gap-y','gap','origin-y','target-y']){
  let editing=false;
  $(id).addEventListener('input',()=>{if(recording)return;if(!editing){checkpoint();editing=true}const value=+$(id).value/100;if(id==='gap-y')project.world.gapY=value;if(id==='gap')project.world.gap=value;if(id==='origin-y')project.world.origin[1]=value;if(id==='target-y')project.world.target[1]=value;playing=false;frame=0;$('gap-y-value').textContent=Math.round(project.world.gapY*100)+'%';$('gap-value').textContent=Math.round(project.world.gap*100)+'%';requestCompose()});
  $(id).addEventListener('change',()=>{editing=false;persist()});
}
$('stones').addEventListener('change',e=>{const el=e.target;if(el.dataset.stone!==undefined)update(()=>project.world.stones[+el.dataset.stone][+el.dataset.axis]=clamp(Number(el.value)||50,4,96)/100)});
$('stones').addEventListener('click',e=>{if(e.target.dataset.deleteStone!==undefined)update(()=>project.world.stones.splice(+e.target.dataset.deleteStone,1))});
$('takes').addEventListener('click',e=>{const d=e.target.dataset;if(d.restore!==undefined)update(()=>project=clone(takes[+d.restore].project));if(d.compare!==undefined){selectedTake=+d.compare;compare=true;renderTakes();setView('world');renderStatus()}if(d.deleteTake!==undefined){takes.splice(+d.deleteTake,1);selectedTake=Math.max(0,Math.min(selectedTake,takes.length-1));if(!takes.length)compare=false;renderTakes();persist();draw()}});

canvas.addEventListener('keydown',e=>{if(view!=='trace')return;const ids=['score','route','motor'];if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();selectedNode=ids[(ids.indexOf(selectedNode)+(e.key==='ArrowRight'?1:2))%3];traceDetail=false;draw()}if(e.key==='Enter'){e.preventDefault();traceDetail=!traceDetail;draw()}});
canvas.addEventListener('pointerdown',e=>{
  if(recording)return;const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;
  if(view==='trace'){const i=clamp(Math.floor((x-(viewport.w<500?18:35))/((viewport.w-2*(viewport.w<500?18:35)+12)/3)),0,2);const id=['score','route','motor'][i];traceDetail=selectedNode===id?!traceDetail:false;selectedNode=id;draw();return}
  if(view!=='world')return;
  const candidates=[{kind:'origin',p:project.world.origin},{kind:'target',p:project.world.target},...project.world.stones.map((p,i)=>({kind:'stone',index:i,p})),{kind:'gap',p:[.5,project.world.gapY]}];
  let best,dist=32;for(const c of candidates){const p=projectPoint(c.p),d=Math.hypot(x-p[0],y-p[1]);if(d<dist){best=c;dist=d}}
  if(!best)return;checkpoint();drag=best;playing=false;frame=0;canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove',e=>{if(!drag)return;const r=canvas.getBoundingClientRect(),p=[clamp((e.clientX-r.left-bounds.x)/bounds.w,.04,.96),clamp((e.clientY-r.top-bounds.y)/bounds.h,.04,.96)];if(drag.kind==='gap')project.world.gapY=clamp(p[1],.12,.88);else if(drag.kind==='stone')project.world.stones[drag.index]=p;else project.world[drag.kind]=p;requestCompose()});
function stopDrag(){if(!drag)return;drag=null;renderInspector();persist()}
canvas.addEventListener('pointerup',stopDrag);canvas.addEventListener('pointercancel',stopDrag);

function showDialog(title,body){$('dialog-title').textContent=title;$('dialog-body').innerHTML=body;$('dialog').showModal()}
$('close-dialog').onclick=()=>$('dialog').close();
$('about').onclick=()=>showDialog('Inside Cascade Engine',`<p>A new study from Cineosis Lab. Text becomes an editable score; the score proposes a route; the motor tests whether that route can happen. The resulting movement becomes a sequence of shots.</p><p><b>What is real here</b><br>Three portable nodes run in the FIELD.IO Cascade 0.7.1 runtime. Collision tests, intermediate destinations, scene changes, saved takes, and comparison use the same computed film.</p><p><b>What you control</b><br>Drag the world, change a scene’s action, scrub time, or inspect the causal stages. Kept takes preserve the full world and score. Undo reverses edits. Sessions stay in this browser and can be exported.</p><p><b>Current boundary</b><br>This is a silent, two-dimensional procedural film engine. Pasted text gets simple, visible action suggestions. It does not understand arbitrary poetry, transcribe recordings, retrieve archive footage, or connect to Shannon yet.</p><p><a href="cascade-engine/index.cascade" download>Download the graph</a> · <a href="https://github.com/hartswf0/cineosis-lab/tree/main/lab/cascade-engine" target="_blank" rel="noreferrer">Source and tests</a></p>`);
$('input-text').onclick=()=>{showDialog('Compose from text','<p>One line per scene, up to eight. Recognized verbs suggest actions; other lines become holds. Review every action after composing.</p><label for="pasted">Poem, transcript, or your own words</label><textarea id="pasted" maxlength="2000" placeholder="I cross the room.\nI wait.\nI return."></textarea><button id="compose-text" class="accent">Compose scenes</button>');$('compose-text').onclick=()=>{const lines=$('pasted').value.split(/\n+/).map(s=>s.trim()).filter(Boolean).slice(0,8);if(!lines.length){$('pasted').focus();return}update(()=>{project.title=lines[0].slice(0,70);project.cues=lines.map(text=>({text:text.slice(0,240),action:suggest(text),duration:2}))});$('dialog').close();switchPanel('score')}};
const examples={
  departure:{title:'Where you go when you leave',lines:['I go towards the other side.','I stay there for a moment.','I return to where I began.'],actions:['cross','hold','return']},
  ding:{title:'Cook Ding / find the interval',lines:['Approach the resistant surface.','Pass through the space between.','Rest after the movement.'],actions:['hold','cross','hold']},
  pond:{title:'Old Pond / before and after',lines:['The field remains still.','One movement crosses it.','Stillness returns, changed.'],actions:['hold','cross','hold']},
  meeting:{title:'A meeting / a shared threshold',lines:['We approach the meeting place.','We wait before speaking.','We leave with something unresolved.'],actions:['cross','hold','depart']},
  rhyme:{title:'Out and back / a repeating score',lines:['Go across.','Come back.','Go across again.','Come back again.'],actions:['cross','return','cross','return']}
};
$('example').onchange=()=>update(()=>{const e=examples[$('example').value];project.title=e.title;project.cues=e.lines.map((text,i)=>({text,action:e.actions[i],duration:2}))});
function download(name,content,type){const url=URL.createObjectURL(content instanceof Blob?content:new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
$('export').onclick=()=>download('cascade-session.json',JSON.stringify({format:'cineosis-cascade-session',version:1,runtime:'@field/cascade@0.7.1',project,takes:takes.map(t=>({name:t.name,project:t.project})),graph:graphDocument},null,2),'application/json');
$('import').onclick=()=>$('file').click();
$('file').onchange=async()=>{try{const file=$('file').files[0];if(!file)return;if(file.size>250000)throw new Error('Session is too large.');const data=JSON.parse(await file.text());if(data.format!=='cineosis-cascade-session'||data.version!==1||!Array.isArray(data.takes)||data.takes.length>12)throw new Error('Not a supported Cascade session.');const next=validated(data.project),nextTakes=data.takes.map(t=>({name:String(t.name).slice(0,40),project:validated(t.project)}));playing=false;for(const t of nextTakes)t.film=await engine.compose(t.project.cues,t.project.world);checkpoint();project=next;takes=nextTakes;serial=Math.max(takes.length,...takes.map(t=>Number(t.name.match(/\d+/)?.[0])||0));compare=false;frame=0;renderInspector();await requestCompose()}catch(e){showDialog('Could not import',`<p class="error">${escape(e.message)}</p>`)}finally{$('file').value=''}};
$('video').onclick=async()=>{
  if(!film||recording)return;
  if(!canvas.captureStream||typeof MediaRecorder==='undefined'){$('record-status').textContent='Recording is not supported in this browser. Export the session instead.';return}
  const oldView=view,oldFrame=frame;let stream,recorder;const controls=[...document.querySelectorAll('.app button,.app input,.app select,.app textarea')].map(el=>[el,el.disabled]);
  try{
    playing=false;recording=true;controls.forEach(([el])=>el.disabled=true);setView('film');frame=0;draw();
    const formats=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/mp4','video/webm'];const mimeType=formats.find(x=>MediaRecorder.isTypeSupported(x));if(!mimeType)throw new Error('No supported recording format.');
    stream=canvas.captureStream(30);recorder=new MediaRecorder(stream,{mimeType});const chunks=[];recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
    const done=new Promise(resolve=>recorder.onstop=resolve);recorder.start();
    $('video').disabled=true;
    for(let i=0;i<film.frames.length;i++){frame=i;renderStatus();draw();$('record-status').textContent=`Recording ${Math.round(i/film.frames.length*100)}%. Keep this tab open.`;await new Promise(r=>setTimeout(r,1000/30));}
    recorder.stop();await done;download('cascade-film.'+(mimeType.includes('mp4')?'mp4':'webm'),new Blob(chunks,{type:mimeType}),mimeType);$('record-status').textContent='Film exported. Silent procedural animation, 30 fps capture.';
  }catch(e){$('record-status').textContent=`Could not record: ${e.message}`;if(recorder?.state==='recording')recorder.stop()}
  finally{stream?.getTracks().forEach(t=>t.stop());recording=false;controls.forEach(([el,disabled])=>el.disabled=disabled);$('video').disabled=false;frame=oldFrame;setView(oldView);renderStatus()}
};

try{
  engine=await createEngine();
  try{const data=JSON.parse(localStorage.getItem(storageKey)||'null');if(data){project=validated(data.project);for(const t of (data.takes||[]).slice(0,12)){const p=validated(t.project);takes.push({name:String(t.name).slice(0,40),project:p,film:await engine.compose(p.cues,p.world)})}selectedTake=clamp(Number(data.selectedTake)||0,0,Math.max(0,takes.length-1));serial=Math.max(takes.length,...takes.map(t=>Number(t.name.match(/\d+/)?.[0])||0))}}catch{project=initial();takes=[]}
  renderInspector();await requestCompose();new ResizeObserver(resize).observe($('viewport'));resize();requestAnimationFrame(animate);
  window.cascadeStudy={inspect:()=>engine.inspect(),snapshot:()=>clone({project,film,frame,takes,compare}),ready:true};
}catch(e){$('status').textContent='The engine could not start.';$('reason').textContent=e.message;$('runtime-status').textContent='Reload to retry';console.error(e)}
