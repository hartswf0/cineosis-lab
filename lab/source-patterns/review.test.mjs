import {test} from 'node:test';import assert from 'node:assert/strict';import {validateReviews} from './review.mjs';
const data={passages:[{id:'p',members:['a','b'],interval:[10,20]}]},types=['unknown','scene'];
const r={members:['a','b'],interval:[10,20],type:'scene',rival:'unknown',status:'draft',relation:'successive',structure:'A A',evidence:'Action continues.',counterevidence:'Check boundary.',reader:'Reader',fullContextAttested:false};
const pack=x=>({format:'cineosis-source-patterns-review/1',annotations:{p:x}});
test('round-trip preserves source identity and evidence',()=>assert.deepEqual(validateReviews(JSON.parse(JSON.stringify(pack(r))),data,types),{p:r}));
test('review requires a named reader, evidence and full-context attestation',()=>{
 assert.throws(()=>validateReviews(pack({...r,status:'reviewed'}),data,types));
 assert.throws(()=>validateReviews(pack({...r,status:'reviewed',fullContextAttested:true,reader:''}),data,types));
 assert.equal(validateReviews(pack({...r,status:'reviewed',fullContextAttested:true}),data,types).p.status,'reviewed');
});
test('changed source membership or interval cannot inherit a reading',()=>{
 for(const bad of [{...r,members:['b','a']},{...r,interval:[11,20]},{...r,type:'fabricated'},{...r,relation:'maybe'}])assert.throws(()=>validateReviews(pack(bad),data,types));
});
