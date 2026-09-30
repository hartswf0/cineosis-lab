import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createEngine, initial, suggest } from './engine.js';

test('blocked actions stop before the barrier and suspend later scenes', async () => {
  const engine=await createEngine(), p=initial();
  const film=await engine.compose(p.cues,p.world);
  assert.equal(film.blocked,true);
  assert.equal(film.completed,0);
  assert.ok(film.frames.every(f=>f.p[0]<.464));
  assert.ok(film.frames.every(f=>f.scene===0));
  assert.equal(film.events.filter(e=>e.kind==='blocked').length,1);
  await engine.dispose();
});

test('a stepping stone opens a valid path, holds, and returns to the same start', async () => {
  const engine=await createEngine(), p=initial();p.world.stones=[[.5,p.world.gapY]];
  const film=await engine.compose(p.cues,p.world);
  assert.equal(film.blocked,false);assert.equal(film.completed,3);
  const end=film.frames.at(-1).p;
  assert.ok(Math.hypot(end[0]-p.world.origin[0],end[1]-p.world.origin[1])<.001);
  const hold=film.frames.filter(f=>f.scene===1);
  assert.equal(hold.length,60);assert.ok(hold.every(f=>JSON.stringify(f.p)===JSON.stringify(hold[0].p)));
  for(const f of film.frames){if(Math.abs(f.p[0]-.5)<.036)assert.ok(Math.abs(f.p[1]-p.world.gapY)<=p.world.gap/2-.018)}
  await engine.dispose();
});

test('restoring the same world produces identical frames after intervening runs', async () => {
  const engine=await createEngine(),p=initial();
  const a=await engine.compose(p.cues,p.world);
  await engine.compose(p.cues,{...p.world,stones:[[.5,p.world.gapY]]});
  const b=await engine.compose(p.cues,p.world);assert.deepEqual(a,b);
  const cold=await createEngine();assert.deepEqual(b,await cold.compose(p.cues,p.world));
  await engine.dispose();await cold.dispose();
});

test('a gap narrower than the body remains impassable even with a stone', async () => {
  const e=await createEngine(),p=initial();p.world.gap=.02;p.world.stones=[[.5,p.world.gapY]];
  assert.equal((await e.compose(p.cues,p.world)).blocked,true);await e.dispose();
});

test('moving the passage into the direct route changes the outcome',async()=>{
  const e=await createEngine(),p=initial();p.world.gapY=p.world.origin[1];
  const f=await e.compose(p.cues,p.world);assert.equal(f.blocked,false);assert.equal(f.completed,3);await e.dispose();
});

test('unrecognized language receives a visible hold instead of invented interpretation',()=>{
  assert.equal(suggest('The red wheelbarrow beside the chickens'),'hold');
  assert.equal(suggest('I return home'),'return');assert.equal(suggest('Go through the gap'),'cross');
});

test('departure exits the world and uses a fixed wide shot',async()=>{
  const e=await createEngine(),p=initial();p.world.gapY=.67;
  const f=await e.compose([{text:'I leave.',action:'depart',duration:2}],p.world);
  assert.equal(f.blocked,false);assert.ok(f.frames.at(-1).p[0]>1);assert.equal(f.frames.at(-1).lens,'wide');await e.dispose();
});
