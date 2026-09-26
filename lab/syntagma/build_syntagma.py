"""Build syntagma-data.json: the four WYGWYL cuts as shot lists placed on the suite's
beats (scenario units) and lines, with each shot's source film and source time, so the
page can divide every cut into Metz's autonomous segments and compare them.

shot: [t0, t1, id, title, year, source, thumb, in, st, sign]
  thumb  CDN path under `cdn` (video = thumbnails->clips, .jpg->.mp4)
  in     seconds into the clip file where the shot starts
  st     seconds into the source film (null when the clip path carries no timecode)
"""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
C = json.load(open(os.path.join(L, 'compounds/compounds-data.json')))
K = json.load(open(os.path.join(L, 'bets/kernel-data.json')))
IDX = json.load(open(os.path.join(L, 'wygwyl/cuts/index.json')))
TC = re.compile(r'/thumbnails/(\d{10})-(\d{10})\.jpg$')
versions = []
for v in IDX:
    P = json.load(open(os.path.join(L, v['patches'])))
    cu = C['cuts'][v['slug']]
    shots = []
    for p, c in zip(P, cu):
        assert p['clip']['id'] == c[2]
        cl = p['clip']; m = TC.search(c[4])
        st = round(int(m.group(1)) / 1000 + cl['in'], 2) if m else None
        shots.append([round(p['t0'], 2), round(p['t1'], 2), cl['id'], (cl.get('title') or '')[:48], cl.get('year'), cl['source'], c[4], round(cl['in'], 2), st, c[3]])
    versions.append({'slug': v['slug'], 'title': v['title'], 'idea': v['idea'], 'shots': shots})
lines = [[l['id'], l['film'], round(l['t0'], 2), round(l['t1'], 2), l['text']] for l in K['lines']]
beats = [[b['id'], b['film'], round(b['t0'], 2), round(b['t1'], 2), b['title']] for b in C['beats']]
signs = {k: [s['symbol'], s['dom'], C['theory'][k]['regime']] for k, s in C['signs'].items()}
out = {'cdn': C['cdn'], 'audio': 'wygwyl/WYGWYL_Suite_Audio.mp3', 'duration': C['duration'], 'films': C['films'],
       'beats': beats, 'lines': lines, 'signs': signs, 'versions': versions}
p = os.path.join(H, 'syntagma-data.json'); json.dump(out, open(p, 'w'), separators=(',', ':'))
print('versions', len(versions), 'beats', len(beats), 'lines', len(lines), os.path.getsize(p) // 1024, 'KB')
