// A deliberately inspectable compiler: lexical cues propose operations, never certify readings.
export const METZ = {
 alternate:['Alternate','Two developing strands, proposed as simultaneous. Alternation alone cannot prove simultaneity.'],
 ordinary:['Ordinary sequence','One proposed progression with omitted intervals. Chronology needs source or editorial evidence.'],
 scene:['Scene','A continuous source passage. Continuity is supported only when neighbouring source blocks are retained.'],
 parallel:['Parallel','Compare two strands without asserting that they share a clock.'],
 bracket:['Bracket','Examples gathered under a common idea; their chronology is left unspecified.'],
 descriptive:['Descriptive','Inspect coexisting aspects. Shared space is a hypothesis unless source evidence supports it.'],
 episodic:['Episodic','Successive stages with ellipses. Repetition alone does not establish a developing history.'],
 autonomous:['Autonomous shot','One uninterrupted interval. Autonomy still depends on its boundary and context.']
};
export const DELEUZE = {
 action:['Action / response','Preserve source progression and its available responses.',['12','13','14']],
 suspend:['Suspend the response','Hold a selected interval; omit the next action. Duration is an operation, not proof of an opsign.',['34a','6']],
 return:['Return / difference','Revisit the same interval after another image; the second occurrence has a new context.',['35','36']],
 disjoin:['Separate voice / image','Insert black intervals and let the voice continue independently. A disjunction is proposed, not a certified time-image.',['34a','34b']],
 affect:['Attend to intensity','Prefer a face or expressive space and give it duration before another action.',['4','5','6']]
};
export function infer(text,engine){
 const s=text.toLowerCase();
 if(engine==='metz'){
  if(/\b(while|meanwhile|simultaneously|at the same time)\b/.test(s))return ['alternate','while / meanwhile → two concurrent strands'];
  if(/\b(after|before|then|finally)\b/.test(s))return ['ordinary','before / after / then → succession'];
  if(/\b(every|again|years|each day)\b/.test(s))return ['episodic','recurrence cue → proposed stages'];
  if(/\b(unlike|whereas|but|rich|poor)\b/.test(s))return ['parallel','contrast cue → comparison without a shared clock'];
  if(/\b(around|beside|surround|room contains)\b/.test(s))return ['descriptive','spatial cue → coexisting aspects'];
  if(/\b(for example|such as|some|others)\b/.test(s))return ['bracket','example cue → a collection'];
  return ['autonomous','no relation cue → one interval; choose a structure to develop it'];
 }
 if(/\b(cannot|can't|not|never|nothing|wait|waits|waiting|still)\b/.test(s))return ['suspend','blocked action / waiting → withhold the response'];
 if(/\b(remember|remembered|again|return|returned|past)\b/.test(s))return ['return','return / memory → repeat an interval after a difference'];
 if(/\b(voice|hear|heard|silence|sound|unseen)\b/.test(s))return ['disjoin','sound cue → separate the voice from the image'];
 if(/\b(face|fear|love|cry|tears)\b/.test(s))return ['affect','intensity cue → attend to face or space'];
 return ['action','default → follow available action; choose an operation to interrupt it'];
}
const STOP=new Set('a an the i you he she it we they his her their my our your is are was were be been to of in on at as and or but with for from that this those these do does did not while after before then every some'.split(' '));
export const tokens=t=>(t.toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).filter(x=>x.length>2&&!STOP.has(x)).map(x=>x.replace(/(ing|ed|s)$/,''));
export function rank(text,catalog,{material='all',signs=[]}={}){
 const terms=tokens(text),docs=catalog.shots.filter(x=>material==='all'||x.example===material);
 return docs.map(shot=>{
  const strong=tokens(shot.description+' '+shot.title+' '+shot.subjects.join(' '));
  const hints=tokens((shot.searchHints||[]).join(' '));
  const hits=[...new Set(terms.filter(w=>strong.includes(w)))];
  const hintHits=[...new Set(terms.filter(w=>!hits.includes(w)&&hints.includes(w)))];
  const signHits=shot.signs.filter(x=>signs.includes(x.n));
  return {shot,hits,hintHits,signHits,score:hits.length*4+hintHits.length*.4+signHits.length*3};
 }).sort((a,b)=>b.score-a.score||a.shot.id.localeCompare(b.shot.id));
}
export function compile(text,engine,catalog,opts={}){
 const [detected,cue]=infer(text,engine),mode=opts.mode==='auto'||!opts.mode?detected:opts.mode;
 const specs=engine==='metz'?METZ:DELEUZE;if(!specs[mode])throw Error('Unknown operation');
 const ranking=rank(text,catalog,opts);if(!ranking.length)throw Error('No material in this selection');
 // Material-lock retains a documented source order. Free retrieval remains a proposed relation.
 let pool=ranking.slice(0,12).map(x=>x.shot);
 if(opts.material&&opts.material!=='all')pool=ranking.map(x=>x.shot).sort((a,b)=>a.sourceIn-b.sourceIn);
 const span=Math.max(2,Math.min(12,Number(opts.span)||4));
 const duration=Math.max(4,Math.min(120,Number(opts.duration)||24));
 let items=[];
 const add=(s,role,seconds=span,hold=false)=>{
  const mediaDuration=Math.min(s.duration,seconds),extra=hold?Math.max(0,seconds-mediaDuration):0;
  items.push({id:s.id,media:s.media,poster:s.poster,in:s.offset||0,out:(s.offset||0)+mediaDuration,hold:extra,duration:mediaDuration+extra,role,strand:s.strand||role,title:s.title,description:s.description,source:s.source,sourceIn:s.sourceIn,signs:s.signs});
 };
 const split=()=>{
  const ordered=xs=>xs.length&&xs.every(x=>x.example===xs[0].example)?xs.sort((x,y)=>x.sourceIn-y.sourceIn):xs;
  const a=ordered(pool.filter(x=>x.strand==='A')),b=ordered(pool.filter(x=>x.strand==='B'));
  return a.length&&b.length?[a,b]:[pool.filter((_,i)=>i%2===0),pool.filter((_,i)=>i%2===1)];
 };
 if(engine==='metz'){
  let [a,b]=split();if(!b.length)b=a;
  if(mode==='alternate'||mode==='parallel'){for(let i=0;i<3;i++){add(a[i%a.length],'A');add(b[i%b.length],'B');}}
  else if(mode==='ordinary'){for(const s of [...a.slice(0,3),...b.slice(0,3)])add(s,s.strand||'next');}
  else if(mode==='autonomous')add(pool[0],'one shot',duration);
  else if(mode==='scene')for(const s of pool.slice(0,8))add(s,'continuous source',s.duration);
  else if(mode==='episodic'){for(let i=0;i<3;i++){add(pool[i%pool.length],'stage '+(i+1));add(pool[(i+1)%pool.length],'stage '+(i+1));}}
  else for(const s of pool.slice(0,6))add(s,mode==='bracket'?'example':'aspect');
 }else{
  if(mode==='action')for(const s of pool.slice(0,6))add(s,'action → response');
  if(mode==='suspend')add(pool[0],'response withheld',duration,true);
  if(mode==='affect'){
   const chosen=pool.find(x=>x.signs.some(z=>['4','5','6'].includes(z.n)))||pool[0];
   add(chosen,'attend / hold',duration*.65,true);add(pool.find(x=>x.id!==chosen.id)||chosen,'release',duration*.35,true);
  }
  if(mode==='return'){const b=pool.find(x=>x.id!==pool[0].id)||pool[0];add(pool[0],'first occurrence',duration/3,true);add(b,'interval / difference',duration/3,true);add(pool[0],'return',duration/3,true);}
  if(mode==='disjoin'){for(const s of pool.slice(0,3)){add(s,'image independent of voice',span);items.push({id:'black',duration:1.5,role:'black interval · voice continues',hold:0});}}
 }
 // Bound to a record-time budget without inventing source frames or changing speed.
 let t=0;items=items.flatMap(x=>{
  if(t>=duration-.05)return [];
  const n=Math.min(x.duration,duration-t),media=x.media?Math.min(x.out-x.in,n):0;
  const y={...x,out:x.media?x.in+media:undefined,hold:x.media?n-media:0,duration:n,recordIn:t,recordOut:t+n};t+=n;return [y];
 });
 const matched=ranking[0].hits.length>0;
 return {format:'cineosis-synthesis/1',engine,text,mode,title:specs[mode][0],claim:specs[mode][1],cue:opts.mode&&opts.mode!=='auto'?'Manual operation override':cue,items,duration:t,options:{...opts},coverage:matched?'Description overlap; review the proposed reading':ranking[0].hintHits.length?'Search-hint overlap only; not visual evidence':'No direct description match. Material is a structural fallback.',ranking:ranking.slice(0,18).map(x=>({id:x.shot.id,score:x.score,hits:x.hits,hintHits:x.hintHits,signHits:x.signHits.map(z=>z.n)})),validation:'Proposed construction; not an automatic classification of the finished film.'};
}
export function locate(plan,time){return Math.max(0,plan.items.findIndex(x=>time>=x.recordIn&&time<x.recordOut));}
export function comparePlans(a,b){return {sameMaterial:a.items.filter(x=>x.media).map(x=>x.id).join('|')===b.items.filter(x=>x.media).map(x=>x.id).join('|'),durationA:a.duration,durationB:b.duration,cutsA:a.items.length-1,cutsB:b.items.length-1,holdsA:a.items.reduce((s,x)=>s+x.hold,0),holdsB:b.items.reduce((s,x)=>s+x.hold,0),orderA:a.items.map(x=>x.strand||'—').join(' → '),orderB:b.items.map(x=>x.strand||'—').join(' → ')};}
