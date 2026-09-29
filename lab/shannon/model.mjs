export const OPERATIONS = Object.freeze({
  OPEN:'OPEN', CONTINUE:'CONTINUE', HOLD:'HOLD', REPEAT:'REPEAT', RETURN:'RETURN',
  ALTERNATE:'ALTERNATE', SUSPEND:'SUSPEND', COMPLETE:'COMPLETE', ABSENCE:'ABSENCE', INSERT:'INSERT'
});

const WORDS = /[\p{L}\p{N}'’]+/gu;
const STOP = new Set('a an the i me my mine you your yours he him his she her hers it its we us our ours they them their theirs is are was were be been being to of in on at as and or with for from that this these those do does did have has had'.split(' '));
const clamp=(n,a=0,b=1)=>Math.max(a,Math.min(b,n));
const terms=s=>(String(s||'').toLowerCase().match(WORDS)||[]).map(x=>x.replace(/’/g,"'")).filter(x=>x.length>1&&!STOP.has(x));
const uniq=a=>[...new Set(a)];

export function splitSource(input){
  const raw=String(input||'').replace(/\r/g,'').trim();
  if(!raw)return [];
  const lines=raw.split('\n');
  const out=[];
  let pendingTime=null, index=0;
  const timeRx=/(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}\s*-->\s*(\d{1,2}:)?\d{1,2}:\d{2}[.,]\d{3}/;
  const toSec=s=>{
    const p=s.replace(',','.').split(':').map(Number); return p.length===3?p[0]*3600+p[1]*60+p[2]:p[0]*60+p[1];
  };
  for(let i=0;i<lines.length;i++){
    let line=lines[i].trim();
    if(!line||/^\d+$/.test(line))continue;
    if(timeRx.test(line)){
      const [a,b]=line.split('-->').map(x=>x.trim()); pendingTime={start:toSec(a),end:toSec(b)}; continue;
    }
    const speaker=(line.match(/^([A-Z][A-Z0-9 _.-]{1,30}|[A-Z][\p{L}'’.-]{1,30}):\s*/u)||[])[1]||null;
    line=line.replace(/^([A-Z][A-Z0-9 _.-]{1,30}|[A-Z][\p{L}'’.-]{1,30}):\s*/u,'').trim();
    const chunks = pendingTime ? [line] : line.split(/(?<=[.!?])\s+(?=[“"'‘’A-Z0-9])/u).filter(Boolean);
    for(const text of chunks){
      const t=text.trim(); if(!t)continue;
      const dur=pendingTime?Math.max(.5,pendingTime.end-pendingTime.start):clamp(1.7+terms(t).length*.23,2.2,7.5);
      out.push({id:index++,text:t,speaker,start:pendingTime?.start??null,end:pendingTime?.end??null,duration:dur});
    }
    pendingTime=null;
  }
  return out;
}

export function lexicalNovelty(a,b){
  const A=new Set(terms(a)),B=new Set(terms(b));
  if(!A.size||!B.size)return .55;
  let hit=0; for(const x of A)if(B.has(x))hit++;
  return clamp(1-hit/(A.size+B.size-hit));
}

export function inferOperation(phrase,prev=null,next=null,state={}){
  const s=String(phrase?.text??phrase??'').toLowerCase();
  const speaker=phrase?.speaker||null, prevSpeaker=prev?.speaker||null;
  if(/\b(gone|empty|emptied|nobody|no one|nothing there|without anyone|vacant|missing)\b/.test(s))return {op:OPERATIONS.ABSENCE,reason:'absence named'};
  if(/\b(remember|remembered|imagined|imagine|dream|dreamed|flashback|once there was)\b/.test(s))return {op:OPERATIONS.INSERT,reason:'memory or imagined material enters'};
  if(/\b(back|return|returned|comes back|came back|again here|still there)\b/.test(s))return {op:OPERATIONS.RETURN,reason:'a prior place or state is called back'};
  if(/\b(every|each time|each day|again and again|repeated|repeats|always)\b/.test(s))return {op:OPERATIONS.REPEAT,reason:'recurrence is explicit'};
  if(/\b(cannot|can't|could not|never|refuse|refuses|blocked|stopped|no answer|won't|will not)\b/.test(s))return {op:OPERATIONS.SUSPEND,reason:'an expected action is blocked'};
  if(/\b(still|wait|waits|waiting|remains|remain|silence|silent|nothing had moved|nothing moves)\b/.test(s))return {op:OPERATIONS.HOLD,reason:'persistence or waiting'};
  if(/\b(finally|at last|ends|ended|closes|closed|arrives|arrived|finished|complete|completed)\b/.test(s))return {op:OPERATIONS.COMPLETE,reason:'closure is explicit'};
  if(/\b(while|meanwhile|at the same time|across the|whereas|but|yet)\b/.test(s)||(speaker&&prevSpeaker&&speaker!==prevSpeaker))return {op:OPERATIONS.ALTERNATE,reason:speaker&&prevSpeaker&&speaker!==prevSpeaker?'speaker changes':'simultaneity or contrast'};
  if(/\b(after|then|next|already|later|now|continues|continued|keeps|kept)\b/.test(s))return {op:OPERATIONS.CONTINUE,reason:'succession continues'};
  const novelty=prev?lexicalNovelty(prev.text,phrase.text):1;
  if(state.currentSource && novelty<.55)return {op:OPERATIONS.CONTINUE,reason:'low information change keeps the established scene'};
  return {op:OPERATIONS.OPEN,reason:prev?'new information opens material':'first phrase opens the film'};
}

export function rankOffline(text,catalog,{limit=64}={}){
  const q=uniq(terms(text));
  const rows=(catalog?.shots||[]).map((shot,idx)=>{
    const body=terms([shot.description,shot.title,(shot.subjects||[]).join(' '),(shot.searchHints||[]).join(' ')].join(' '));
    const set=new Set(body); let hits=0; for(const w of q)if(set.has(w))hits++;
    const raw=q.length?hits/q.length:0;
    return normalizeCandidate({
      id:shot.id, title:shot.title, source:shot.source, sourceKey:shot.example||shot.source||shot.title,
      sourceStart:Number(shot.sourceIn||0), duration:Number(shot.duration||4), poster:shot.poster, media:shot.media,
      description:shot.description||'', raw, idx
    });
  });
  return rows.sort((a,b)=>b.raw-a.raw||a.idx-b.idx).slice(0,limit);
}

export function normalizeCandidate(c){
  return {
    id:String(c.id), title:c.title||'Untitled source', source:c.source||'', sourceKey:String(c.sourceKey||c.sourceSlug||c.title||c.id),
    sourceStart:Number(c.sourceStart??c.startSeconds??c.in??0)||0,
    sourceEnd:Number(c.sourceEnd??c.endSeconds??((c.sourceStart??0)+(c.duration??4)))||0,
    duration:clamp(Number(c.duration)||4,.4,15), mediaIn:Number(c.mediaIn??c.offset??0)||0, poster:c.poster||c.thumbnailUrl||'', media:c.media||c.videoUrl||'',
    description:c.description||'', raw:Number(c.raw??c.score??0)||0, idx:Number(c.idx)||0
  };
}

function futureSupport(sourceKey,step,candidateSets,horizon=3){
  if(!sourceKey)return 0;
  let total=0,n=0;
  for(let j=step+1;j<Math.min(candidateSets.length,step+1+horizon);j++){
    const same=(candidateSets[j]||[]).filter(c=>c.sourceKey===sourceKey);
    if(same.length){total+=Math.max(...same.map(c=>c.raw));n++;}
  }
  return n?total/n:0;
}

function countUsed(state,id){return state.used[id]||0;}
function sourceWear(state,key){return state.sourceWear[key]||0;}
function strandKey(p){return p.speaker||'voice';}

export function scoreCandidate(candidate,phrase,step,candidateSets,state,options,opInfo){
  const c=normalizeCandidate(candidate), op=opInfo.op;
  const literal=clamp(options.literal??.72), continuity=clamp(options.continuity??.68), intercut=clamp(options.intercut??.42), surprise=clamp(options.surprise??.28);
  const semantic=c.raw*(1.2+2.5*literal);
  const sameCurrent=state.currentSource&&c.sourceKey===state.currentSource;
  const sk=strandKey(phrase), strandAnchor=state.strands[sk];
  const sameStrand=strandAnchor&&c.sourceKey===strandAnchor.sourceKey;
  const priorAnchor=state.anchors[c.sourceKey];
  const used=countUsed(state,c.id), wear=sourceWear(state,c.sourceKey);
  const forward=sameCurrent && c.sourceStart>=state.currentSourceStart-.25;
  const future=futureSupport(c.sourceKey,step,candidateSets,3);
  let structural=0;

  if(op===OPERATIONS.CONTINUE){structural += sameCurrent?1.5*continuity:-.5*continuity; structural+=forward?.55:-.25;}
  if(op===OPERATIONS.HOLD){structural += c.id===state.currentId?1.8: sameCurrent?.65:0;}
  if(op===OPERATIONS.REPEAT){structural += priorAnchor?1.3:0; structural += c.id===state.currentId?.7:0;}
  if(op===OPERATIONS.RETURN){structural += priorAnchor?1.8:0; structural += sameCurrent?-.4:0;}
  if(op===OPERATIONS.ALTERNATE){
    const other=Object.entries(state.strands).find(([k,v])=>k!==sk&&v?.sourceKey);
    structural += other&&c.sourceKey===other[1].sourceKey?1.1*intercut:(!sameCurrent?.45*intercut:0);
  }
  if(op===OPERATIONS.OPEN){structural += !priorAnchor?.7:.05; structural += !sameCurrent?.35:0;}
  if(op===OPERATIONS.INSERT){structural += !sameCurrent?.7:0;}
  if(op===OPERATIONS.COMPLETE){structural += sameCurrent?.85*continuity:0; structural+=forward?.45:0;}
  if(op===OPERATIONS.ABSENCE){structural += !sameStrand?.15:0;}
  if(op===OPERATIONS.SUSPEND){structural += sameCurrent?.55*continuity:0; structural += c.id===state.currentId?.45:0;}
  if(sameStrand) structural+=.5*(1-intercut*.4);

  const toward=future*(.55+1.65*continuity);
  const noveltyReward=surprise*((!priorAnchor?.34:0)+Math.min(.35,c.raw*.2));
  const reusePenalty=used*(.65+.55*(1-surprise))+Math.max(0,wear-2)*.10;
  const singletonPenalty=(op===OPERATIONS.OPEN&&future<.08)?(.25*continuity):0;
  return {score:semantic+structural+toward+noveltyReward-reusePenalty-singletonPenalty,semantic,structural,toward,reusePenalty,future};
}

function cloneState(s){return {currentSource:s.currentSource,currentSourceStart:s.currentSourceStart,currentId:s.currentId,anchors:{...s.anchors},strands:{...s.strands},used:{...s.used},sourceWear:{...s.sourceWear},picks:s.picks.slice(),score:s.score};}
function updateState(state,candidate,phrase,opInfo,scoreParts){
  const s=cloneState(state), c=normalizeCandidate(candidate), sk=strandKey(phrase);
  s.currentSource=c.sourceKey;s.currentSourceStart=c.sourceStart;s.currentId=c.id;
  s.anchors[c.sourceKey] ||= {sourceKey:c.sourceKey,title:c.title,firstStep:s.picks.length};
  if(opInfo.op!==OPERATIONS.INSERT)s.strands[sk]={sourceKey:c.sourceKey,title:c.title,lastStep:s.picks.length};
  s.used[c.id]=(s.used[c.id]||0)+1;s.sourceWear[c.sourceKey]=(s.sourceWear[c.sourceKey]||0)+1;
  s.score+=scoreParts.score;
  s.picks.push({step:s.picks.length,phrase,candidate:c,operation:opInfo.op,reason:opInfo.reason,parts:scoreParts});
  return s;
}

export function compose(phrases,candidateSets,options={}){
  if(!phrases.length)return {picks:[],scenes:[],metrics:metricsFor([],phrases)};
  const width=Math.max(4,Math.min(24,Number(options.beam)||12));
  let beam=[{currentSource:null,currentSourceStart:0,currentId:null,anchors:{},strands:{},used:{},sourceWear:{},picks:[],score:0}];
  for(let step=0;step<phrases.length;step++){
    const phrase=phrases[step], pool=(candidateSets[step]||[]).slice(0,Math.max(8,Math.min(48,Number(options.pool)||28)));
    if(!pool.length)continue;
    const next=[];
    for(const state of beam){
      const opInfo=inferOperation(phrase,phrases[step-1],phrases[step+1],state);
      for(const c of pool){
        const parts=scoreCandidate(c,phrase,step,candidateSets,state,options,opInfo);
        next.push(updateState(state,c,phrase,opInfo,parts));
      }
    }
    next.sort((a,b)=>b.score-a.score);
    const seen=new Set(); beam=[];
    for(const s of next){
      const sig=s.picks.slice(-3).map(p=>p.candidate.sourceKey).join('|');
      if(seen.has(sig))continue; seen.add(sig);beam.push(s);if(beam.length>=width)break;
    }
  }
  const best=beam[0]||{picks:[],score:0};
  const scenes=toScenes(best.picks);
  return {format:'cineosis-shannon/1',picks:best.picks,scenes,score:best.score,metrics:metricsFor(best.picks,phrases),options:{...options}};
}

export function toScenes(picks){
  const scenes=[];
  for(const p of picks){
    const prev=scenes[scenes.length-1];
    const hardBreak=[OPERATIONS.OPEN,OPERATIONS.INSERT,OPERATIONS.RETURN].includes(p.operation);
    if(!prev||hardBreak||prev.sourceKey!==p.candidate.sourceKey){
      scenes.push({sourceKey:p.candidate.sourceKey,title:p.candidate.title,operation:p.operation,picks:[p]});
    }else prev.picks.push(p);
  }
  return scenes;
}

export function metricsFor(picks,phrases=[]){
  const scenes=toScenes(picks), sceneYield=scenes.length?picks.length/scenes.length:0;
  const singleton=scenes.filter(s=>s.picks.length===1).length;
  let contN=0,contOK=0,retN=0,retOK=0,cov=0,future=0;
  const anchors=new Set();
  for(let i=0;i<picks.length;i++){
    const p=picks[i],prev=picks[i-1];
    if(p.candidate.raw>.12)cov++;
    future+=p.parts?.future||0;
    if(p.operation===OPERATIONS.CONTINUE){contN++;if(prev&&p.candidate.sourceKey===prev.candidate.sourceKey&&p.candidate.sourceStart>=prev.candidate.sourceStart-.25)contOK++;}
    if([OPERATIONS.RETURN,OPERATIONS.REPEAT].includes(p.operation)){retN++;if(anchors.has(p.candidate.sourceKey))retOK++;}
    anchors.add(p.candidate.sourceKey);
  }
  const speakers={};
  for(const p of picks){const k=strandKey(p.phrase);(speakers[k]||=[]).push(p.candidate.sourceKey);}
  let purity=0,spN=0;
  for(const a of Object.values(speakers)){const count={};for(const x of a)count[x]=(count[x]||0)+1;purity+=Math.max(...Object.values(count))/a.length;spN++;}
  return {
    phrases:phrases.length||picks.length, scenes:scenes.length, sceneYield:+sceneYield.toFixed(2), singletonRate:scenes.length?+(singleton/scenes.length).toFixed(2):0,
    coverage:picks.length?+(cov/picks.length).toFixed(2):0, continuity:contN?+(contOK/contN).toFixed(2):null,
    returnAccuracy:retN?+(retOK/retN).toFixed(2):null, strandPurity:spN?+(purity/spN).toFixed(2):null,
    futureSupport:picks.length?+(future/picks.length).toFixed(3):0
  };
}

export function evaluateBenchmark(plan,benchmark){
  const m=plan.metrics||metricsFor(plan.picks||[]);
  const checks=[]; const want=benchmark?.expect||{};
  const test=(label,value,pass)=>checks.push({label,value,pass});
  if(want.minSceneYield!=null)test('scene yield',m.sceneYield,m.sceneYield>=want.minSceneYield);
  if(want.maxSingletonRate!=null)test('singleton scenes',m.singletonRate,m.singletonRate<=want.maxSingletonRate);
  if(want.minCoverage!=null)test('coverage',m.coverage,m.coverage>=want.minCoverage);
  if(want.minContinuity!=null&&m.continuity!=null)test('continuity',m.continuity,m.continuity>=want.minContinuity);
  if(want.minReturnAccuracy!=null&&m.returnAccuracy!=null)test('return',m.returnAccuracy,m.returnAccuracy>=want.minReturnAccuracy);
  if(want.minStrandPurity!=null&&m.strandPurity!=null)test('strand purity',m.strandPurity,m.strandPurity>=want.minStrandPurity);
  if(want.requireOps?.length){const got=new Set((plan.picks||[]).map(p=>p.operation));for(const op of want.requireOps)test(op,got.has(op)?'present':'missing',got.has(op));}
  return {checks,passed:checks.length?checks.every(x=>x.pass):null};
}
