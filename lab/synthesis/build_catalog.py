"""Build a small catalogue from bundled, ffprobe-verified media; do not import poem rankings."""
import json,pathlib,subprocess
from concurrent.futures import ThreadPoolExecutor
root=pathlib.Path(__file__).resolve().parents[1]
d=json.load(open(root/'lab-data.json'));s=json.load(open(root/'syntagm/operative/examples.json'))
shots=[x for x in d['shots'] if x.get('clip') and (root/x['clip']).is_file()]
def one(x):
 p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(root/x['clip'])],capture_output=True,text=True)
 try:dur=float(p.stdout)
 except ValueError:return None
 if dur<.5:return None
 notes=' '.join(z.get('note','') for z in x.get('signs',[]))
 return dict(id=x['id'],title=x['title'],media=x['clip'],poster=x['thumb'],duration=dur,offset=0,sourceIn=x.get('start',0),source=x['page'],description=notes or ' · '.join(z['label'] for z in x.get('subjects',[])),subjects=[z['label'] for z in x.get('subjects',[])],scale=x.get('scale',''),signs=x.get('signs',[]),searchHints=[z.get('q','') for z in x.get('found',[])],reading='Existing editorial annotation' if notes else 'Metadata only; no editorial reading')
with ThreadPoolExecutor(max_workers=8) as ex: items=[x for x in ex.map(one,shots) if x]
for e in s['examples']:
 for b in e['blocks']:
  items.append(dict(id='passage-'+b['id'],title=s['sources'][e['source']]['title'],media=e['media'],poster=e['poster'],duration=b['end']-b['start'],offset=b['start']-e['start'],sourceIn=b['start'],source=s['sources'][e['source']]['url'],description=b['label']+'. '+b['signEvidence'],subjects=[],scale='',signs=[dict(n=b['sign'],note=b['signEvidence'],conf=None)],reading='Existing editorial working reading',example=e['id'],strand=b['strand'],searchHints=[]))
json.dump(dict(signs=d['signs'],shots=items,examples=s['examples']),open(root/'synthesis/catalog.json','w'),ensure_ascii=False,separators=(',',':'))
print('Validated playable intervals:',len(items))
