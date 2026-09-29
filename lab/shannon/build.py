import json,re
from pathlib import Path
from retrieval import retrieve
P=Path(__file__).parent; LAB=P.parent
cases=json.load(open(P/'tests.json'))
def phrases(t):
 blocks=re.split(r'\n\s*\n',t.strip())
 if len(blocks)>1:return [re.sub(r'\s+',' ',s).strip() for s in blocks if s.strip()]
 return [s.strip() for s in re.split(r'(?<=[.!?;])\s+|\n+',t.strip()) if s.strip()]
queries=[]
for c in cases:
 for t in [c['brief'],c['text']]:
  if t:queries+=phrases(t)
 queries+=[c['goal']]
queries=list(dict.fromkeys(queries))
print('Encoding',len(queries),'phrases',flush=True)
r=retrieve(queries)
(P/'retrieval.json').write_text(json.dumps(dict(zip(queries,r)),separators=(',',':')))
corpus=json.load(open(LAB/'cache/corpus.json')); analysis=json.load(open(LAB/'cache/analysis.json'))
shots={}
for id,s in corpus.items():
 a=analysis.get(id,{})
 shots[id]=dict(id=id,title=s.get('sourceTitle','Archive'),film=s.get('sourceSlug',id),start=s.get('startSeconds',0),duration=max(.25,s.get('endSeconds',0)-s.get('startSeconds',0)),url=('clips/'+id+'.mp4') if (LAB/'clips'/f'{id}.mp4').exists() else s['videoUrl'],poster=s.get('thumbnailUrl',''),subjects=[x['label'] for x in a.get('subjects',[])],scale=a.get('scale',''),lum=a.get('lum',.5))
(P/'shots.json').write_text(json.dumps(shots,separators=(',',':')))
print('Saved',len(shots),'shots and',len(queries),'queries',flush=True)
