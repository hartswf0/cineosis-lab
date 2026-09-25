"""Build bets/kernel-data.json: everything the nine bet studios share, in one small file.
  films  · the 14 poems with their window on the 1440.1 s suite clock
  lines  · 267 spoken lines, each word on the suite clock (from sound-cineosis.json word timings)
  beats  · the 88 beats with their signs
  pool   · per beat, the top 16 ranked clips (candidate-ranks.json) with fit, scores and the category of why;
           `loop` marks the ones with a same-origin 3 s loop in wygwyl/tempest/ (the rest show a still)
  each clip carries `sg`, its strongest sign in the whole table (cache/affinity.json), so it can wear the
  periodic table's colour for that sign's domain, and `bs`, its strongest among the beat's own signs
    python3 lab/bets/build_pool.py
"""
import json, os
LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(LAB, 'wygwyl', 'collage-data.json')))
R = json.load(open(os.path.join(LAB, 'wygwyl', 'candidate-ranks.json')))
S = json.load(open(os.path.join(LAB, 'sound-cineosis.json')))
AFF = json.load(open(os.path.join(LAB, 'cache', 'affinity.json')))
PK = set(json.load(open(os.path.join(LAB, 'wygwyl', 'tempest', 'pack.json')))['files'])
lines = []
for p in S['poems']:
    for l in p['lines']:
        off = l['clock'] - l['s']
        ws = [{'w': w['w'], 't0': round(w['s'] + off, 3), 't1': round(w['e'] + off, 3), 'st': w.get('st')} for w in l['words']]
        lines.append({'id': l['id'], 'film': p['n'], 'n': l['n'], 'text': l['text'], 't0': ws[0]['t0'], 't1': ws[-1]['t1'], 'words': ws})
lines.sort(key=lambda l: l['t0'])
beats = [{'id': b['id'], 'film': b['chapter'], 'title': b['title'], 't0': b['start'], 't1': b['end'], 'codes': b['codes']} for b in D['beats']]
pool = {}
for b in beats:
    r = R['beats'].get(str(b['id']))
    if not r: continue
    out = []
    for x in r['ranked']:
        if x['verdict'] == 'FLOOR' and len(out) >= 8: continue
        c = x['comp']
        out.append({'id': x['id'], 'title': x['title'], 'year': x['year'], 'thumb': x['thumb'], 'video': x['video'], 'score': x['score'], 'fit': x['fit'],
                    'verdict': x['verdict'], 'cat': x['cat'], 'fl': c['fl'], 'fs': c['fs'], 'sign': c['sign'], 'craft': c['craft'], 'loop': x['id'] in PK,
                    'in': x.get('in') or 0, 'dur': x.get('dur'),
                    # the clip's own sign: its strongest in the whole table, and its strongest among this beat's signs
                    'sg': (AFF.get(x['id'], {}).get('top') or [[None]])[0][0],
                    'bs': max(b['codes'], key=lambda n: AFF.get(x['id'], {}).get('all', {}).get(n, 0)) if b['codes'] else None})
        if len(out) >= 16: break
    pool[b['id']] = out
signs = {k: {'symbol': v['symbol'], 'name': v['name'], 'dom': v.get('dom')} for k, v in S['signs'].items()}
films = [{'n': f['n'], 'title': f['title'], 't0': f['container'][0], 't1': f['container'][1]} for f in D['films']]
json.dump({'duration': D['duration'], 'audio': '../wygwyl/WYGWYL_Suite_Audio.mp3', 'films': films, 'lines': lines, 'beats': beats, 'pool': pool, 'signs': signs},
          open(os.path.join(LAB, 'bets', 'kernel-data.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
n = sum(len(v) for v in pool.values()); lp = sum(1 for v in pool.values() for x in v if x['loop'])
print('lines', len(lines), 'words', sum(len(l['words']) for l in lines), 'beats', len(beats), 'pool', n, 'with loop', lp, os.path.getsize(os.path.join(LAB, 'bets', 'kernel-data.json')) // 1024, 'KB')
