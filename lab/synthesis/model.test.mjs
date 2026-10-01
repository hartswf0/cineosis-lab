import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {compile,infer,comparePlans,METZ,DELEUZE} from './model.mjs';
const cat=JSON.parse(fs.readFileSync(new URL('./catalog.json',import.meta.url)));
const opts={material:'telephone',duration:24,span:4};
test('relation change alters actual interval order with material held fixed',()=>{
 const a=compile('She calls while he listens.','metz',cat,opts),b=compile('She calls. After the call, he listens.','metz',cat,opts);
 assert.equal(a.mode,'alternate');assert.equal(b.mode,'ordinary');
 assert.notDeepEqual(a.items.map(x=>x.id),b.items.map(x=>x.id));
 assert.deepEqual([...new Set(a.items.map(x=>x.id))].sort(),[...new Set(b.items.map(x=>x.id))].sort());
});
test('Deleuze suspension changes duration and omits response, with explicit held frames',()=>{
 const a=compile('She calls.','deleuze',cat,{...opts,mode:'action'}),b=compile('She cannot act.','deleuze',cat,{...opts,mode:'suspend'});
 assert.ok(a.items.length>1);assert.equal(b.items.length,1);assert.equal(b.duration,24);assert.ok(b.items[0].hold>0);
 assert.equal(b.items[0].out-b.items[0].in+b.items[0].hold,b.items[0].duration);
});
test('every operation maintains bounded source intervals and contiguous record times',()=>{
 for(const [engine,spec] of [['metz',METZ],['deleuze',DELEUZE]])for(const mode of Object.keys(spec))for(const material of ['all','telephone','sower','fire']){
  const p=compile('The room waits for a voice.',engine,cat,{material,mode,duration:37,span:7});let time=0;
  for(const x of p.items){assert.ok(x.duration>0);assert.equal(x.recordIn,time);time=x.recordOut;
   if(x.media){const s=cat.shots.find(s=>s.id===x.id);assert.ok(x.in>=s.offset-.001);assert.ok(x.out<=s.offset+s.duration+.001);assert.ok(Math.abs(x.out-x.in+x.hold-x.duration)<.001);}
  }assert.ok(time<=37+.001);assert.equal(time,p.duration);
 }
});
test('unknown concepts are reported as unsupported, not silently labelled understood',()=>{
 const p=compile('qxzorbflax','metz',cat,{material:'all'});assert.match(p.coverage,/No direct/);assert.equal(p.ranking[0].hits.length,0);
});
test('return reprises the same source interval; disjunction inserts playable gaps',()=>{
 const p=compile('Remember again.','deleuze',cat,{...opts,mode:'return'});assert.equal(p.items[0].id,p.items[2].id);assert.notEqual(p.items[0].id,p.items[1].id);
 const d=compile('Hear the voice.','deleuze',cat,{...opts,mode:'disjoin'});assert.ok(d.items.some(x=>!x.media));
});
test('table constraint changes retrieval without importing poem assignments',()=>{
 const a=compile('qxzorbflax','metz',cat,{material:'all',signs:['4']}),b=compile('qxzorbflax','metz',cat,{material:'all',signs:['34a']});
 assert.notEqual(a.items[0].id,b.items[0].id);assert.ok(a.ranking[0].signHits.includes('4'));assert.ok(b.ranking[0].signHits.includes('34a'));
});
