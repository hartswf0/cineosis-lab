// Pure passage operations. Source time, record time and story time stay distinct.
export const TYPES = [
  ['unknown', 'Unresolved', 'Record evidence before choosing a reading.'],
  ['autonomous', 'Autonomous shot', 'A single shot functions as an autonomous unit or insert in context.'],
  ['parallel', 'Parallel', 'Alternating motifs establish a comparison; their temporal relation is unspecified.'],
  ['bracket', 'Bracket', 'Brief examples describe one category without specifying chronological order.'],
  ['descriptive', 'Descriptive', 'Successive views describe a situation understood to coexist.'],
  ['alternate', 'Alternate', 'Developing action strands are presented as simultaneous.'],
  ['scene', 'Scene', 'One action unfolds with continuous diegetic time across camera changes.'],
  ['episodic', 'Episodic sequence', 'Selected chronological phases summarize a development.'],
  ['ordinary', 'Ordinary sequence', 'One action proceeds through omitted intervals without a phase-summary structure.']
];
export const QUESTIONS = [
  ['autonomy', 'Autonomous unit?', [['unknown','Unresolved'],['yes','Yes'],['no','Only a fragment']]],
  ['time', 'Time between images', [['unknown','Unresolved'],['unspecified','Unspecified by the film'],['defined','Established by the film']]],
  ['organization', 'Organization', [['unknown','Unresolved'],['alternating','Alternating strands'],['examples','Examples of a category'],['coexistence','Coexisting views'],['linear','One action succession']]],
  ['progression', 'Within each strand', [['unknown','Unresolved'],['yes','Action develops'],['no','No action progression']]],
  ['simultaneous', 'Between strands', [['unknown','Unresolved'],['yes','Simultaneous'],['no','Not simultaneous']]],
  ['ellipsis', 'Story-time omissions', [['unknown','Unresolved'],['none','None'],['scattered','Omitted intervals'],['phases','Distinct stages of development']]]
];
export function emptyReading() {
  return {type:'unknown', rival:'unknown', intended:'unknown', scope:'candidate', evidence:'', counterevidence:'',
    analyst:'', status:'unreviewed', answers:Object.fromEntries(QUESTIONS.map(q=>[q[0],'unknown']))};
}
export function timeline(items, offset=0) {
  let t = offset;
  return items.map(item=> {const duration=item.out-item.in, rec=[t,t+duration];t+=duration;return {...item,rec};});
}
export function suggest(reading, n) {
  const a=reading.answers;
  if(a.autonomy!=='yes') return {type:'unknown',reason:'Autonomy in the surrounding film is not established.'};
  if(n===1) return {type:'autonomous',reason:'One shot; autonomy is your recorded judgement.'};
  if(a.time==='unspecified' && a.organization==='alternating') return {type:'parallel',reason:'Alternating motifs, with no specified chronology.'};
  if(a.time==='unspecified' && a.organization==='examples') return {type:'bracket',reason:'Examples grouped without a specified chronology.'};
  if(a.time==='defined' && a.organization==='coexistence' && a.progression==='no') return {type:'descriptive',reason:'Established coexistence without an action progression.'};
  if(a.time==='defined' && a.organization==='alternating' && a.progression==='yes' && a.simultaneous==='yes') return {type:'alternate',reason:'Developing strands and established simultaneity.'};
  if(a.time==='defined' && a.organization==='linear' && a.progression==='yes') {
    const type={none:'scene', scattered:'ordinary', phases:'episodic'}[a.ellipsis];
    if(type) return {type,reason:'One developing action; your omission judgement determines this category.'};
  }
  return {type:'unknown',reason:'The recorded relations do not yet support one category.'};
}
export function coverage(clips) {
  const sorted=[...clips].sort((a,b)=>a.startSeconds-b.startSeconds);
  if(!sorted.length)return {ratio:null,gaps:[],span:0};
  let end=sorted[0].startSeconds, union=0; const gaps=[];
  for (const c of sorted) {
    if(c.startSeconds>end+.05)gaps.push([end,c.startSeconds]);
    const start=Math.max(end,c.startSeconds);union+=Math.max(0,c.endSeconds-start);end=Math.max(end,c.endSeconds);
  }
  const span=end-sorted[0].startSeconds;
  return {ratio:span?union/span:null,gaps,span};
}
export function metrics(items, shots) {
  let sameSource=0, comparable=0, adjacent=0, unknown=0, switches=0;
  const joins=items.slice(1).map((b,i)=> {
    const a=items[i],sa=shots[a.shotId],sb=shots[b.shotId];
    if(a.strand && b.strand && a.strand!==b.strand)switches++;
    if(!sa||!sb||!sa.slug||!sb.slug){unknown++;return {kind:'unknown',label:'Source relation unknown'};}
    comparable++;
    if(sa.slug!==sb.slug)return {kind:'different',label:'Different source films'};
    sameSource++;
    if(!Number.isFinite(sa.start)||!Number.isFinite(sb.start)){unknown++;return {kind:'unknown',label:'Source timing unknown'};}
    const gap=(sb.start+b.in)-(sa.start+a.out);
    if(Math.abs(gap)<.05)adjacent++;
    return {kind:Math.abs(gap)<.05?'adjacent':gap>0?'gap':'back',gap,
      label:Math.abs(gap)<.05?'Source intervals touch':gap>0?`${gap.toFixed(2)} s skipped in source`:`${Math.abs(gap).toFixed(2)} s backward / overlap in source`};
  });
  return {duration:items.reduce((t,x)=>t+x.out-x.in,0),sameSource,comparable,adjacent,unknown,switches,joins};
}
export function reorder(items, operation, seed=1) {
  const out=items.map(x=>({...x}));
  if(operation==='reverse')return out.reverse();
  if(operation==='group')return out.sort((a,b)=>(a.strand||'').localeCompare(b.strand||''));
  if(operation==='alternate') {
    const groups=new Map();for(const x of out){const key=x.strand||'?';if(!groups.has(key))groups.set(key,[]);groups.get(key).push(x);}
    const result=[];while(result.length<out.length)for(const g of groups.values())if(g.length)result.push(g.shift());return result;
  }
  if(operation==='shuffle'){
    let x=seed>>>0;for(let i=out.length-1;i>0;i--){x=(Math.imul(1664525,x)+1013904223)>>>0;const j=x%(i+1);[out[i],out[j]]=[out[j],out[i]];}return out;
  }
  return out;
}
export function validate(doc, shots) {
  if(doc?.format!=='cineosis-syntagm/1'||!Array.isArray(doc.items)||!doc.items.length||doc.items.length>100)throw Error('Expected a passage with 1–100 occurrences.');
  const ids=new Set();
  for(const x of doc.items){
    const shot=shots[x.shotId];
    if(!shot)throw Error('Missing source shot: '+x.shotId);
    if(typeof x.id!=='string'||ids.has(x.id))throw Error('Occurrence IDs must be unique.');ids.add(x.id);
    if(!Number.isFinite(x.in)||!Number.isFinite(x.out)||x.in<0||x.out<=x.in||x.out>shot.end-shot.start+.05)throw Error('Invalid clip trim: '+x.id);
  }
  if(!Number.isFinite(doc.offset)||doc.offset<0)throw Error('Invalid record offset.');
  return true;
}
export function toEDL(doc, shots, baseURL) {
  validate(doc,shots);
  const abs=s=>s?new URL(s,baseURL).href:undefined;
  return {format:'cineosis-edl/1',title:doc.title,bet:'SYNTAGM',made:new Date().toISOString(),
    clock:{duration:doc.offset+metrics(doc.items,shots).duration,fps:25},
    events:timeline(doc.items,doc.offset).map((x,i)=>{const s=shots[x.shotId];return {n:i+1,rec:x.rec,src:[x.in,x.out],
      clip:{id:s.id,title:s.title,year:s.year,video:abs(s.video||s.clip),thumb:abs(s.thumb)},
      words:x.words||'',by:'you',bet:'SYNTAGM',kind:'syntagm',why:doc.reading?.evidence||'',occurrence:x.id};}),
    syntagm:{reading:doc.reading,context:doc.context,history:doc.history,sourceTime:'clip.start + src; not inferred story time'}};
}
