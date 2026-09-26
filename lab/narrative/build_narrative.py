"""Build narrative/narrative-data.json: what the Narrative Lab needs beyond lab-data.json and bets/kernel-data.json.
  ranked · per beat, every ranked shot id in rank order (up to 48), with its verdict
  cuts   · the four WYGWYL cuts (suite, scenes, cineosis, drift) as [t0, t1, id] on the suite clock
The lab's shots are all in lab-data.json, so every id here resolves to a shot the eight views can show.
    python3 lab/narrative/build_narrative.py
"""
import json, os
LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(LAB, 'wygwyl', 'candidate-ranks.json')))
D = json.load(open(os.path.join(LAB, 'wygwyl', 'collage-data.json')))
out = {'ranked': {k: [[x['id'], x['verdict'][0], x['fit']] for x in b['ranked']] for k, b in R['beats'].items()},
       'cuts': {k: [[round(p['t0'], 3), round(p['t1'], 3), p['id']] for p in v] for k, v in D['cuts'].items()}}
json.dump(out, open(os.path.join(LAB, 'narrative', 'narrative-data.json'), 'w'), separators=(',', ':'))
print('beats', len(out['ranked']), 'ranked ids', sum(len(v) for v in out['ranked'].values()), 'cut events', sum(len(v) for v in out['cuts'].values()), os.path.getsize(os.path.join(LAB, 'narrative', 'narrative-data.json')) // 1024, 'KB')
