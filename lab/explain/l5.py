"""LESSON 5 · THE TABLE OF SIGNS. What a sign is, read from the lab's own records:
  table      the 45 signs where the lab places them (16 columns, 3 rows), with family, symbol, question and defining difference
  confusions each sign's three recorded confusions, as threads across the table
  take       the Cineosis take: 169 moments, each shot chosen for the signs the suite's treatment assigns its beat (a reading),
             and, for the same shot, the machine's own top guess from cache/affinity.json; how often the two agree
  open       one moment with two signs on one picture, for the cold open; practice moments from three families
Films the lab keeps out of its examples are never shown.   Writes explain/lesson/l5.json.   usage: python3 lab/explain/l5.py"""
import json, os, re, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
BAN = re.compile(r'all my babies|kinderen naar buiten|exhibit 3', re.I)
U = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
S = json.load(open(os.path.join(LAB, 'lab-data.json')))['signs']
aff = json.load(open(os.path.join(LAB, 'cache', 'affinity.json')))
rows = json.load(open(os.path.join(H, 'ep', 'takes.json')))['cineosis']['rows']
by = {s['n']: s for s in S}
table = [{'n': s['n'], 'sym': s['symbol'], 'name': s['name'], 'dom': s['dom'], 'col': s['col'], 'row': s['row'], 'q': s.get('question', ''),
          'diff': s['difference'], 'conf': s.get('confusions', [])} for s in S]
take, agree, ranks = [], 0, []
for r in rows:
    i = U.search(r['thumb']).group(0); a = aff.get(i) or {}
    top = a.get('top') or []; mine = [str(x['n']) for x in (r.get('signs') or [])]
    guess = top[0][0] if top else None
    if guess in mine: agree += 1
    allr = sorted((a.get('all') or {}).items(), key=lambda kv: -kv[1]); order = [k for k, _ in allr]
    for m in mine:
        if m in order: ranks.append(order.index(m) + 1)
    take.append({'id': r['id'], 't0': r['t0'], 't1': r['t1'], 'ch': r['ch'], 'shot': i, 'title': r['title'], 'year': r['year'], 'hide': bool(BAN.search(r['title'] or '')),
                 'thumb': f'thumbs/{i}.jpg', 'clip': f'clips/{i}.mp4', 'in': r.get('in', 0), 'line': r.get('line', ''), 'why': r.get('why', ''),
                 'signs': [{'n': x['n'], 'sym': x['sym'], 'dom': x['dom'], 'aff': x.get('aff')} for x in (r.get('signs') or [])],
                 'guess': ({'n': guess, 'sym': by[guess]['symbol'], 'name': by[guess]['name'], 'dom': by[guess]['dom'], 'v': top[0][1]} if guess in by else None)})
fam = collections.Counter(by[str(x['n'])]['dom'] for t in take for x in t['signs'] if str(x['n']) in by)
ok = [t for t in take if not t['hide'] and os.path.exists(os.path.join(LAB, 'thumbs', t['shot'] + '.jpg'))]
op = next(t for t in ok if t['id'] == 'P003')
practice, seen = [], set()
for t in ok:
    d = by[str(t['signs'][0]['n'])]['dom']
    if d not in seen and d in ('affect', 'time', 'action') and t is not op: practice.append(t); seen.add(d)
    if len(practice) == 3: break
med = sorted(ranks)[len(ranks) // 2] if ranks else None
out = {'table': table, 'take': take, 'families': dict(fam), 'agree': agree, 'n': len(take), 'rank_median': med,
       'rank_top3': sum(1 for x in ranks if x <= 3), 'rank_n': len(ranks), 'open': op, 'practice': practice}
json.dump(out, open(os.path.join(H, 'lesson', 'l5.json'), 'w'), ensure_ascii=False)
print('agree', agree, 'of', len(take), '| assigned sign rank: median', med, 'top3', out['rank_top3'], 'of', len(ranks))
print('families', dict(fam)); print('open', op['title'], [s['sym'] for s in op['signs']], 'guess', op['guess']); print('practice', [(p['id'], p['title'], p['signs'][0]['sym']) for p in practice])
