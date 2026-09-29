export const MODES={journey:['Develop','Move forward through successive scenes.'],return:['Return','Establish a motif, depart, then revisit the opening.'],contrast:['Contradict','Let a second scene challenge the first.'],alternate:['Interweave','Keep two strands in play through A–B–A–B.'],hold:['Attend','Stay with one source and give it time.'],arrive:['Arrive','Plan the ending first and work toward it.']};
export function phrases(text){const p=text.trim().split(/\n\s*\n/);return (p.length>1?p:text.trim().split(/(?<=[.!?;])\s+|\n+/)).map(s=>s.replace(/\s+/g,' ').trim()).filter(Boolean);}
export function distribution(rows,temp=.025){if(!rows.length)return {H:0,p:[]};const max=rows[0][1],w=rows.map(r=>Math.exp((r[1]-max)/temp)),z=w.reduce((a,b)=>a+b,0),p=w.map(x=>x/z);return {p,H:-p.reduce((s,x)=>s+(x?x*Math.log2(x):0),0)};}
// Search whole paths, not independent winners. Scores are engineering heuristics, not measured meaning.
export function compose({texts,pools,goalPool=[],shots,mode='journey',seconds=60,variant=0,locks={},baseline=false}){
 if(!texts.length||texts.length!==pools.length||pools.some(p=>!p?.length))throw Error('Every scene needs a retrieval pool.');
 const n=texts.length,goals=new Map(goalPool),width=12;let beams=[{path:[],score:0}];
 for(let i=0;i<n;i++){
  let next=[];
  for(const b of beams){
   let choices=locks[i]?[pools[i].find(r=>r[0]===locks[i])||[locks[i],0]]:pools[i].slice(0,24);
   if(!locks[i]&&!baseline&&mode==='arrive'&&i===n-1&&goalPool.length){const seen=new Set(choices.map(x=>x[0]));choices=[...choices,...goalPool.slice(0,12).filter(x=>!seen.has(x[0])).map(x=>[x[0],pools[i].find(r=>r[0]===x[0])?.[1]??Math.max(0,pools[i].at(-1)[1]-.03)])];}
   if(!locks[i]&&!baseline&&mode==='return'&&i===n-1&&n>1)choices=[[b.path[0][0],pools[i].find(r=>r[0]===b.path[0][0])?.[1]||0]];
   if(!locks[i]&&!baseline&&mode==='alternate'&&i>=2)choices=[[b.path[i%2][0],pools[i].find(r=>r[0]===b.path[i%2][0])?.[1]||0]];
   for(const c of choices){const s=shots[c[0]];if(!s)continue;const prev=shots[b.path.at(-1)?.[0]],repeat=b.path.filter(x=>x[0]===c[0]).length;
    let score=c[1];
    if(!baseline){
     score-=repeat*.085;
     if(prev){const same=prev.film===s.film,forward=s.start>prev.start;
      score+=mode==='hold'?(same?.16:-.14):mode==='contrast'?(same?-.13:.035):same&&forward?.035:0;
      if(mode==='journey'&&same&&!forward)score-=.07;
     }
     // Destination affinity rises as the cut approaches its ending.
     score+=(goals.get(c[0])||0)*(mode==='arrive'?.6:.2)*(n===1?1:i/(n-1));
     score+=variant?Math.sin((i+1)*(pools[i].findIndex(r=>r[0]===c[0])+1)*17+variant*29)*.022:0;
    }
    next.push({path:[...b.path,c],score:b.score+score});
   }
  }
  beams=next.sort((a,b)=>b.score-a.score).slice(0,width);if(!beams.length)throw Error('No playable path in this archive.');
 }
 const chosen=beams[0].path,byFilm=new Map();for(const s of Object.values(shots)){if(!byFilm.has(s.film))byFilm.set(s.film,[]);byFilm.get(s.film).push(s);}for(const v of byFilm.values())v.sort((a,b)=>a.start-b.start);
 const weights=texts.map(t=>Math.max(4,t.split(/\s+/).length)),total=weights.reduce((a,b)=>a+b,0),scenes=[];let clock=0;
 for(let i=0;i<n;i++){
  const anchor=shots[chosen[i][0]],budget=seconds*weights[i]/total,neighbors=byFilm.get(anchor.film),at=neighbors.findIndex(s=>s.id===anchor.id);
  const count=baseline?1:Math.max(1,Math.min(3,Math.ceil(budget/5))),seq=[anchor];
  for(let j=1;j<count;j++){const s=neighbors[at+j];if(s&&s.start>=seq.at(-1).start+seq.at(-1).duration-.2&&s.start-seq.at(-1).start-seq.at(-1).duration<10)seq.push(s);else break;}
  let remaining=budget,items=[];
  for(let j=0;j<seq.length;j++){const s=seq[j],allocated=remaining/(seq.length-j),duration=Math.min(allocated,s.duration);items.push({id:s.id,in:0,out:duration,duration,recordIn:clock,scene:i});clock+=duration;remaining-=duration;}
  // Explicit hold of the final frame fills a requested duration without inventing source footage.
  if(remaining>.01){items.at(-1).hold=remaining;items.at(-1).duration+=remaining;clock+=remaining;}
  const d=distribution(pools[i]),rank=pools[i].findIndex(r=>r[0]===anchor.id),prob=rank<0?null:d.p[rank];
  scenes.push({text:texts[i],anchor:anchor.id,items,alternatives:pools[i].slice(0,12),H:d.H,surprisal:prob?-Math.log2(prob):null,coverage:pools[i][0][1],reason:locks[i]?'Your locked selection':baseline?'Independent phrase retrieval':mode==='return'&&i===n-1?'Opening motif returns':mode==='alternate'&&i>=2?'Earlier strand returns':i===n-1&&mode==='arrive'?'Destination affinity weighted at the ending':`${MODES[mode][0]} · whole-path selection; source neighbours extend the scene`});
 }
 return {version:1,mode,baseline,scenes,items:scenes.flatMap(s=>s.items),duration:clock,score:beams[0].score,text:texts.join('\n\n')};
}
export function measures(p,shots){return {scenes:p.scenes.length,shots:p.items.length,sources:new Set(p.items.map(x=>shots[x.id].film)).size,returns:p.scenes.filter((s,i)=>i&&p.scenes.slice(0,i).some(x=>x.anchor===s.anchor)).length,heldSeconds:p.items.reduce((s,x)=>s+(x.hold||0),0),coverage:p.scenes.reduce((s,x)=>s+x.coverage,0)/p.scenes.length};}
