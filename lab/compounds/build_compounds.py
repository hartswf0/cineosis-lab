"""Build compounds/compounds-data.json for the Narrative Chemistry page.
  signs  · the 45 elements: symbol, name, family (domain)
  films · beats · lines   · the 14 poems on the suite clock; each beat carries the signs it was written for
  cand   · per beat, every ranked candidate with its two strongest signs (cache/affinity.json), so a compound's
           atoms can be found as real shots
  cuts   · the four WYGWYL cuts' shots with their strongest sign, to read each cut's own formula
    python3 lab/compounds/build_compounds.py
"""
import json, os
LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = json.load(open(os.path.join(LAB, 'bets', 'kernel-data.json')))
R = json.load(open(os.path.join(LAB, 'wygwyl', 'candidate-ranks.json')))
D = json.load(open(os.path.join(LAB, 'wygwyl', 'collage-data.json')))
AFF = json.load(open(os.path.join(LAB, 'cache', 'affinity.json')))
CDN = 'https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/'
def short(u):
    return u[len(CDN):] if u and u.startswith(CDN) else u
top = lambda i: [t[0] for t in (AFF.get(i, {}).get('top') or [])[:2]] + [None, None]
cand = {}
for bid, b in R['beats'].items():
    cand[bid] = [[x['id'], *top(x['id'])[:2], x['fit'], x['verdict'][0], (x['title'] or '')[:48], x['year'], short(x['thumb']), short(x['video'])] for x in b['ranked']]
cuts = {k: [[round(p['t0'], 2), round(p['t1'], 2), p['id'], top(p['id'])[0], short(p.get('thumb'))] for p in v] for k, v in D['cuts'].items()}
out = {'cdn': CDN, 'signs': K['signs'], 'films': K['films'], 'beats': K['beats'],
       'lines': [{'id': l['id'], 'film': l['film'], 'n': l['n'], 't0': l['t0'], 't1': l['t1'], 'text': l['text']} for l in K['lines']],
       'duration': K['duration'], 'cand': cand, 'cuts': cuts}
p = os.path.join(LAB, 'compounds', 'compounds-data.json')
json.dump(out, open(p, 'w'), ensure_ascii=False, separators=(',', ':'))
print('signs', len(out['signs']), 'beats', len(out['beats']), 'cand', sum(len(v) for v in cand.values()), 'cut shots', sum(len(v) for v in cuts.values()), os.path.getsize(p) // 1024, 'KB')
