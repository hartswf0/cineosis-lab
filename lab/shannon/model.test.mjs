import test from 'node:test'; import assert from 'node:assert/strict';
import {splitSource,inferOperation,compose,OPERATIONS} from './model.mjs';
const c=(id,source,raw,start=0)=>({id,title:source,sourceKey:source,sourceStart:start,duration:4,raw,media:'',poster:''});
test('segments speaker transcript',()=>{const p=splitSource('ALICE: We begin here.\nBOB: Then we go.');assert.equal(p.length,2);assert.equal(p[0].speaker,'ALICE');assert.equal(p[1].speaker,'BOB');});
test('return cue is visible',()=>{assert.equal(inferOperation({text:'She comes back again.'},{text:'She left.'}).op,OPERATIONS.RETURN);});
test('lookahead can beat isolated nearest neighbour',()=>{
 const p=splitSource('A door opens. Then the person crosses the room. Then the room goes dark.');
 const sets=[
  [c('x','SINGLE',.31),c('a','SCENE',.28,1)],
  [c('b','SCENE',.27,2),c('y','OTHER',.29)],
  [c('d','SCENE',.26,3),c('z','OTHER2',.29)]
 ];
 const plan=compose(p,sets,{literal:.55,continuity:.95,intercut:.1,surprise:.1,beam:12,pool:8});
 assert.equal(plan.picks[0].candidate.sourceKey,'SCENE');
 assert.ok(plan.metrics.sceneYield>=3);
});
test('explicit return prefers an established source',()=>{
 const p=splitSource('The kitchen is bright. A street appears. She comes back to the kitchen.');
 const sets=[
  [c('a','KITCHEN',.3),c('q','Q',.2)],
  [c('b','STREET',.3),c('c','KITCHEN',.16,2)],
  [c('d','KITCHEN',.22,3),c('e','NEW',.31)]
 ];
 const plan=compose(p,sets,{literal:.5,continuity:.5,intercut:.4,surprise:.1});
 assert.equal(plan.picks[2].operation,OPERATIONS.RETURN);
 assert.equal(plan.picks[2].candidate.sourceKey,'KITCHEN');
});
