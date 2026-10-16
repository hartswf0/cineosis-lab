"""THE ABSENCE LEDGER · every way a shot can be missing from the lab, kept apart, from the lab's own records.
After Kumbier's distinction between absence and failed retrieval: "missing" can mean never asked for, asked but not well answered,
found but never fetched, fetched but removed by a rule, withheld on purpose, or misdescribed by a machine. Each stage counts what the
records show and keeps a few real examples. Nothing here is a claim about what the Moving Image Archive lacks: only what the lab
asked, got, kept and did.
Sources: explain/ep/ep1.json (the archive estimate, searches), ../results/<sign>.json (every Cineosis question and its scored
answers), explain/lesson/l6.json (the sieve), cache/corpus.json, rushes/captions.json (BLIP), explain/ep/takes.json (what the four
takes used), the withholding rule written into the pipelines. Writes explain/lesson/ledger.json.   usage: python3 lab/explain/ledger.py"""
import json, os, re, glob, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); C44 = os.path.dirname(LAB)
J = lambda p: json.load(open(os.path.join(LAB, p)))
BAN = re.compile(r'all my babies|kinderen naar buiten|exhibit 3', re.I)
ep1 = J('explain/ep/ep1.json'); l6 = J('explain/lesson/l6.json'); corpus = J('cache/corpus.json'); cap = J('rushes/captions.json')
signs = {s['n']: s for s in J('lab-data.json')['signs']}
# questions and how well they were answered
Q = []
for f in sorted(glob.glob(os.path.join(C44, 'results', '*.json')), key=lambda p: (len(p), p)):
    n = os.path.basename(f)[:-5]; r = json.load(open(f))
    for q, hits in r.items():
        best = max((h.get('score') or 0 for h in hits), default=0); Q.append({'sign': n, 'q': q, 'n': len(hits), 'best': round(best, 4), 'hit': hits[0] if hits else None})
bests = sorted(x['best'] for x in Q); med = bests[len(bests) // 2]
WEAK = .25   # CLIP similarity of words to a frame: the median best answer scores about .30; under .25 (the bottom twentieth) the best answer rarely shows what was asked
weak = sorted([x for x in Q if x['best'] < WEAK], key=lambda x: x['best'])
empty = [x for x in Q if x['n'] == 0]
by_sign = collections.defaultdict(list)
for x in Q: by_sign[x['sign']].append(x['best'])
sign_weak = sorted(((n, sum(1 for b in v if b < WEAK), len(v)) for n, v in by_sign.items()), key=lambda t: -t[1])
# the sieve
A = l6['archive']; found, measured, kept = A[0]['n'], A[1]['n'], A[-1]['n']
dead = A[2]['n'] - A[3]['n'] if len(A) > 3 else 0
rules = [{'rule': a.get('rule', ''), 'removed': A[i]['n'] - a['n'], 'law': a.get('law', '')} for i, a in enumerate(A[1:]) if A[i]['n'] - a['n'] > 0]
# withheld on purpose
withheld = collections.Counter(v.get('sourceTitle') for v in corpus.values() if BAN.search(v.get('sourceTitle') or ''))
# misdescribed: machine captions that invent or hedge
eyes = J('explain/machines/eyes.json')['blip']   # the BLIP pass the machines film measured
inv = eyes.get('invented') or []
mis = [x if isinstance(x, str) else (x.get('cap') or x.get('caption') or '') for x in (inv if isinstance(inv, list) else list(inv.values()))]
n_cap = len(eyes.get('caps') or []) or len(cap)   # the sample BLIP was measured on
# used
T = J('explain/ep/takes.json'); used = set()
for k, t in ((k, t) for k, t in T.items() if isinstance(t, dict)):
    for r in t.get('rows', []):
        m = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', r.get('thumb', '') or '')
        if m: used.add(m.group(0))
src_used = {corpus[u]['sourceSlug'] for u in used if u in corpus}
out = {
  'archive_films': ep1['archive_est'], 'libraries': ep1['all_libraries'], 'films_found': ep1['films'], 'hours_found': ep1['hours'],
  'questions': len(Q), 'questions_signs': len(by_sign), 'median_best': med, 'weak_threshold': WEAK, 'weak': len(weak), 'empty': len(empty),
  'weak_examples': [{'sign': x['sign'], 'name': signs.get(x['sign'], {}).get('name', x['sign']), 'q': x['q'], 'best': x['best'],
                     'got': (x['hit'] or {}).get('sourceTitle'), 'thumb': ('thumbs/' + x['hit']['id'] + '.jpg') if x['hit'] and os.path.exists(os.path.join(LAB, 'thumbs', x['hit']['id'] + '.jpg')) else None} for x in weak[:8]],
  'weak_by_sign': [{'sign': n, 'name': signs.get(n, {}).get('name', n), 'weak': w, 'of': t} for n, w, t in sign_weak[:6] if w],
  'found': found, 'measured': measured, 'not_fetched': found - measured, 'kept': kept, 'rules': rules,
  'withheld_films': [{'title': t, 'shots': c} for t, c in withheld.most_common()], 'withheld_shots': sum(withheld.values()),
  'captions': n_cap, 'misdescribed': len(mis), 'misdescribed_examples': [m for m in mis if m][:5],
  'used_shots': len(used), 'used_films': len(src_used),
}
yrs = [v.get('sourceYear') for v in corpus.values() if v.get('sourceYear')]
shots = J('lab-data.json')['shots']
out.update({'decades': sorted(collections.Counter((y // 10) * 10 for y in yrs).items()), 'year_min': min(yrs), 'year_max': max(yrs), 'year_median': sorted(yrs)[len(yrs) // 2],
  'bw_share': round(sum(1 for x in shots if x.get('bw')) / len(shots), 3), 'projects': collections.Counter(c for v in corpus.values() for c in (v.get('collections') or [])).most_common(),
  'signs_asked': len(by_sign), 'questions_per_sign': round(len(Q) / max(1, len(by_sign)), 1)})
json.dump(out, open(os.path.join(H, 'lesson', 'ledger.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, indent=0))
print('weak examples', [(x['name'], x['q'][:50], x['best']) for x in out['weak_examples'][:4]])
print('withheld', out['withheld_films'], 'misdescribed eg', out['misdescribed_examples'][:2])
