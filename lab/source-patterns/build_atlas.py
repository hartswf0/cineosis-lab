"""Source-pattern census and explicitly provisional seed passages. No automatic Metz labels.
Run: python3 lab/source-patterns/build_atlas.py
"""
import json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
LAB=HERE.parent
NAMES=['master-hands','moonwalk-one-ca-1970','the-photographer','jfk-exhibit-3-reconstruction-film','duck-and-cover','all-my-babies']

def audit(clips):
    ordered=sorted(clips,key=lambda c:(c['startSeconds'],c['position']))
    if not ordered:return {'interval':None,'coverage':None,'gaps':[],'positionGaps':[],'overlaps':[]}
    start=ordered[0]['startSeconds'];end=start;union=0;gaps=[];overlaps=[]
    for c in ordered:
        a,b=c['startSeconds'],c['endSeconds']
        if a>end+.05:gaps.append([end,a])
        if a<end-.05:overlaps.append([a,min(end,b)])
        union+=max(0,b-max(end,a));end=max(end,b)
    return {'interval':[start,end],'coverage':union/(end-start) if end>start else None,'gaps':gaps,'overlaps':overlaps,
            'positionGaps':[[a['position'],b['position']] for a,b in zip(ordered,ordered[1:]) if b['position']!=a['position']+1]}

def build():
    pack=json.loads((LAB/'wygwyl/tempest/pack.json').read_text()); previews=set(pack['files'])
    obs=json.loads((HERE/'observations.json').read_text()); sources=[];by_slug={};passages=[];shots={}
    for p in sorted((LAB/'cutbastard/forage/sources').glob('*.json')):
        d=json.loads(p.read_text());cs=d['clips'];by_slug[d['slug']]=d
        sources.append({'slug':d['slug'],'title':cs[0]['sourceTitle'] if cs else d['slug'],'count':len(cs),'audit':audit(cs),
                        'previewCount':sum(c['id'] in previews for c in cs),'manifest':'cutbastard/forage/sources/'+p.name})
    for slug in NAMES:
        cs=by_slug[slug]['clips'];options=[];used=set();chosen=[]
        for i in range(len(cs)-2):
            win=cs[i:i+3]
            if any(b['position']!=a['position']+1 or abs(b['startSeconds']-a['endSeconds'])>.05 for a,b in zip(win,win[1:])):continue
            n=sum(c['id'] in previews for c in win)
            if n:options.append((n,i,win))
        for score,i,win in sorted(options,key=lambda x:(-x[0],x[1])):
            if any(c['id'] in used for c in win):continue
            chosen.append((i,win));used.update(c['id'] for c in win)
            if len(chosen)==4:break
        for i,win in sorted(chosen):
            ident=f'{slug}-{win[0]["position"]:04}'
            title,note,tags,tests,question=obs[ident]
            available=[c['id'] for c in win if c['id'] in previews]
            for c in win:
                shots[c['id']]={**c,'preview':f'wygwyl/tempest/{c["id"]}.mp4' if c['id'] in previews else None,
                    'page':f'https://www.movingimagearchive.com/sources/{slug}?clip={c["id"]}',
                    'thumb':f'thumbs/{c["id"]}.jpg'}
            passages.append({'id':ident,'slug':slug,'title':title,'first':i+1,'members':[c['id'] for c in win],
                'interval':[win[0]['startSeconds'],win[-1]['endSeconds']],'tags':tags,'questionsToTest':tests,
                'reading':{'type':'unknown','status':'candidate','evidence':note,'counterevidence':question,'autonomy':'unknown'},
                'inspection':{'level':'sampled-excerpt-frames','analyst':'Codex','date':'2026-09-26','clipsSampled':available,
                    'sampleFractions':[0,.4,.8],'media':'existing silent cropped Tempest excerpts; exact source offsets not recorded',
                    'audioReviewed':False,'fullClipsReviewed':False,'boundariesReviewed':False},'audit':audit(win)})
    out={'format':'cineosis-source-patterns/1','builtFrom':subprocess.check_output(['git','rev-parse','HEAD'],cwd=LAB.parent,text=True).strip(),
         'method':'Frame-sampled discovery set, not an annotated ground-truth corpus. Fixed three-clip windows selected for preview availability; film/clip boundaries unverified.',
         'sources':sources,'passages':passages,'shots':shots}
    (HERE/'data.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
    print(f'{len(sources)} source audits; {len(passages)} candidate passages; {sum(len(p["inspection"]["clipsSampled"]) for p in passages)} sampled excerpts; 0 reviewed syntagm labels')
if __name__=='__main__':build()
