"""LESSON 9 · VERSIONS ON ONE CLOCK. The four takes of the WYGWYL suite laid on the poem's one clock, each in its own row:
  lanes      169 moments per take: the shot, its source film, its recorded reason
  agree      the moments where two or more takes chose the same shot, or the same source film
  shared     how many shots each pair of takes shares anywhere in the film
  runs       how long each take stays with one source film (Scenes stays a whole line; Drift almost never)
  open       one line and the four shots it got, for the cold open
Films the lab keeps out of its examples are never shown.   Writes explain/lesson/l9.json.   usage: python3 lab/explain/l9.py"""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
BAN = re.compile(r'all my babies|kinderen naar buiten|exhibit 3', re.I)
U = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
T = json.load(open(os.path.join(H, 'ep', 'takes.json'))); TK = ['suite', 'scenes', 'cineosis', 'drift']
ideas = json.load(open(os.path.join(H, 'ep', 'ep5.json')))['ideas']
lanes = {}
for k in TK:
    lanes[k] = [{'id': r['id'], 't0': r['t0'], 't1': r['t1'], 'ch': r['ch'], 'shot': U.search(r['thumb']).group(0), 'src': r.get('src'),
                 'title': r['title'], 'year': r['year'], 'why': r.get('why', ''), 'hide': bool(BAN.search(r['title'] or ''))} for r in T[k]['rows']]
    for x in lanes[k]: x['thumb'] = f"thumbs/{x['shot']}.jpg"
n = len(lanes['suite'])
same_shot, same_src = [], []
for i in range(n):
    shots = {k: lanes[k][i]['shot'] for k in TK}; srcs = {k: lanes[k][i]['src'] for k in TK}
    g = [[k for k in TK if shots[k] == s] for s in set(shots.values())]; g = [x for x in g if len(x) > 1]
    if g: same_shot.append({'i': i, 'takes': g[0]})
    g2 = [[k for k in TK if srcs[k] == s] for s in set(srcs.values())]; g2 = [x for x in g2 if len(x) > 1]
    if g2: same_src.append({'i': i, 'takes': g2[0]})
S = {k: set(x['shot'] for x in lanes[k]) for k in TK}
shared = [[len(S[a] & S[b]) for b in TK] for a in TK]
runs = {}
for k in TK:
    r, cur = [], 1
    for a, b in zip(lanes[k], lanes[k][1:]):
        if a['src'] == b['src']: cur += 1
        else: r.append(cur); cur = 1
    r.append(cur); runs[k] = {'longest': max(r), 'mean': round(sum(r) / len(r), 2), 'runs': r}
# the cold open: the Lesson 7 line, if none of its four shots is from a film kept out; otherwise the first line that qualifies
cand = [i for i in range(n) if lanes['suite'][i]['id'] == 'P082'] + list(range(n))
oi = next(i for i in cand if not any(lanes[k][i]['hide'] for k in TK) and all(os.path.exists(os.path.join(LAB, 'thumbs', lanes[k][i]['shot'] + '.jpg')) for k in TK))
line = T['suite']['rows'][oi].get('line', '')
out = {'takes': TK, 'ideas': ideas, 'parts': T['parts'], 'lanes': lanes, 'n': n, 'same_shot': same_shot, 'same_src': same_src, 'shared': shared,
       'runs': {k: {'longest': v['longest'], 'mean': v['mean']} for k, v in runs.items()}, 'films': {k: T[k]['films'] for k in TK},
       'open': {'i': oi, 'line': line, 't0': lanes['suite'][oi]['t0'], 't1': lanes['suite'][oi]['t1'], 'shots': {k: lanes[k][oi] for k in TK}}}
json.dump(out, open(os.path.join(H, 'lesson', 'l9.json'), 'w'), ensure_ascii=False)
print('same shot at the same moment:', len(same_shot), [(x['i'], x['takes']) for x in same_shot]); print('same film at the same moment:', len(same_src))
print('shared anywhere:', shared); print('runs:', {k: (v['longest'], v['mean']) for k, v in runs.items()})
print('open:', lanes['suite'][oi]['id'], [(k, lanes[k][oi]['title']) for k in TK])
