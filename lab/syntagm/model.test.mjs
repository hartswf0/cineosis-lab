import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyReading,suggest,coverage,metrics,reorder,timeline,validate,toEDL} from './model.mjs';

test('alternation does not establish simultaneity',()=>{
  const r=emptyReading();Object.assign(r.answers,{autonomy:'yes',organization:'alternating'});
  assert.equal(suggest(r,4).type,'unknown');
  r.answers.time='unspecified';assert.equal(suggest(r,4).type,'parallel');
  r.answers.time='defined';assert.equal(suggest(r,4).type,'unknown');
  Object.assign(r.answers,{progression:'yes',simultaneous:'yes'});assert.equal(suggest(r,4).type,'alternate');
});
test('one isolated archive clip is not automatically autonomous',()=>{
  assert.equal(suggest(emptyReading(),1).type,'unknown');
});
test('all eight types follow explicit relation judgements',()=>{
  for(const [expected,n,answers] of [
    ['autonomous',1,{}],['parallel',4,{time:'unspecified',organization:'alternating'}],
    ['bracket',3,{time:'unspecified',organization:'examples'}],
    ['descriptive',3,{time:'defined',organization:'coexistence',progression:'no'}],
    ['alternate',4,{time:'defined',organization:'alternating',progression:'yes',simultaneous:'yes'}],
    ...[['scene','none'],['ordinary','scattered'],['episodic','phases']].map(([t,e])=>[t,3,{time:'defined',organization:'linear',progression:'yes',ellipsis:e}])]){
    const r=emptyReading();Object.assign(r.answers,{autonomy:'yes'},answers);assert.equal(suggest(r,n).type,expected);
  }
});
test('coverage unions overlaps and reports retrieval gaps',()=>{
  const c=coverage([{startSeconds:0,endSeconds:10},{startSeconds:5,endSeconds:12},{startSeconds:15,endSeconds:20}]);
  assert.equal(c.ratio,17/20);assert.deepEqual(c.gaps,[[12,15]]);
});
const shots={a:{id:'a',slug:'film',start:20,end:30,title:'A',video:'https://example.com/a.mp4'},b:{id:'b',slug:'film',start:40,end:50,title:'B',video:'https://example.com/b.mp4'}};
const items=[{id:'one',shotId:'a',in:1,out:3,strand:'A'},{id:'two',shotId:'b',in:2,out:6,strand:'B'},{id:'three',shotId:'a',in:4,out:6,strand:'A'}];
test('reordering preserves exact occurrences and trims, including reuse',()=>{
  for(const op of ['shuffle','reverse','alternate','group']){
    const out=reorder(items,op,42);assert.deepEqual([...out].sort((a,b)=>a.id.localeCompare(b.id)),[...items].sort((a,b)=>a.id.localeCompare(b.id)));
    assert.equal(metrics(out,shots).duration,8);
  }
  assert.deepEqual(reorder(items,'shuffle',42),reorder(items,'shuffle',42));
});
test('source gaps are measured without inferring story ellipsis',()=>{
  const m=metrics(items,shots);assert.equal(m.joins[0].gap,19);assert.equal(m.joins[1].gap,-22);
  assert.equal(m.adjacent,0);assert.equal(suggest(emptyReading(),items.length).type,'unknown');
});
test('EDL keeps record offset separate from clip and source-film time',()=>{
  const d={format:'cineosis-syntagm/1',items,offset:100,title:'Test',reading:emptyReading()};
  const edl=toEDL(d,shots,'https://example.com/lab/syntagm.html');
  assert.deepEqual(edl.events.map(e=>e.rec),[[100,102],[102,106],[106,108]]);
  assert.deepEqual(edl.events[0].src,[1,3]);assert.equal(edl.events[0].clip.id,'a');
  assert.deepEqual(timeline(items).map(x=>x.rec),[[0,2],[2,6],[6,8]]);
});
test('invalid imports do not silently clip, merge occurrences, or accept NaN',()=>{
  const d={format:'cineosis-syntagm/1',items,offset:0};assert.equal(validate(d,shots),true);
  for(const bad of [
    {...d,items:[{...items[0],out:11}]}, {...d,items:[items[0],items[0]]},
    {...d,items:[{...items[0],in:NaN}]}, {...d,offset:-1}, {...d,items:[]}])assert.throws(()=>validate(bad,shots));
});
