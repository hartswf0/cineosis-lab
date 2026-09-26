"""Build chemistry/chem-data.json: the elements, the reactions and each poem's measured compound for the Compound Bench.

  atoms      · the 45 signs as elements: grid place (image type = group, composition/genesis = period), Peirce code,
               regime (movement / time), valence, the three signs each is confused with and the flip that turns it
  ligands    · the sound table's elements (her voice first), which bind to an image atom IN, OFF or OUT of the world
  catalysts  · the sound table's moves (Deamer p.168): what breaks an action-image into a pure optical or sound situation
  poems      · per poem: its world (logline, thesis, tagline, accent), its spoken lines, its footage's signs (the beat
               pools and the suite cut), the shots that can realise each sign, and its natural compound, built from
               that footage by the rules below
The authored compounds (names, readings, new syntheses) are in chemistry/compounds.json.
    python3 lab/chemistry/build_chemistry.py
"""
import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE); ROOT = os.path.dirname(LAB)
L = json.load(open(os.path.join(LAB, 'lab-data.json')))
K = json.load(open(os.path.join(LAB, 'bets', 'kernel-data.json')))
D = json.load(open(os.path.join(LAB, 'wygwyl', 'collage-data.json')))
T = {s['n']: s for s in json.load(open(os.path.join(ROOT, 'cineosis-table.json')))['signs']}
ST = json.load(open(os.path.join(LAB, 'sound-table.json')))

TIME_COLS = set(range(11, 16))                      # opsign/sonsign, hyalosign, chronosign, noosign, lectosign
def valence(s):
    if s['n'] in ('34a', '34b'): return 1           # a pure situation: it cannot be discharged, so it ends a chain
    if s['n'] == '44': return 4                      # the lectosign reads everything around it
    return 3 if s['row'] == 2 else 2                 # genesis generates (a branch); composition joins a before and an after

atoms = {}
for s in L['signs']:
    t = T.get(s['n'], {}); conf = (t.get('diff') or {}).get('confusions') or []
    atoms[s['n']] = {
        'n': s['n'], 'sym': s['symbol'], 'name': s['name'], 'image': s['image'], 'col': s['col'], 'row': s['row'],
        'code': s['code'], 'dom': s['dom'], 'regime': 'time' if s['col'] in TIME_COLS else 'movement', 'valence': valence(s),
        'period': 'genesis' if s['row'] == 2 else 'singular' if s['n'] in ('34a', '34b', '44') else 'composition',
        'question': s['question'], 'gloss': s['gloss'], 'difference': s.get('difference', ''),
        'flips': [{'to': c['n'], 'if': c.get('flip', ''), 'why_not': c.get('why_not', '')} for c in conf] or [{'to': c, 'if': '', 'why_not': ''} for c in s['confusions']],
    }

ligands = [{'sym': c['sym'], 'name': c['name'], 'family': c['family'], 'what': c.get('what', ''), 'law': c.get('law', ''), 'priority': c.get('priority')} for c in ST['columns']]
rows = [{'id': r['id'], 'name': r['name'], 'gloss': r['gloss']} for r in ST['rows']]
catalysts = [{'name': m['name'], 'does': m['does'], 'page': m.get('page', ''), 'gives': '34a' if 'score' in m['name'].lower() or 'effects' in m['name'].lower() else '34b'} for m in ST['moves']]

shot = {s['id']: s for s in L['shots']}
pool_sg = {c['id']: c.get('sg') for v in K['pool'].values() for c in v}
def sg_of(i):
    s = shot.get(i)
    return s['signs'][0]['n'] if s and s.get('signs') else pool_sg.get(i)
def slim(c, sg):
    return {'id': c['id'], 'title': c.get('title', ''), 'year': c.get('year'), 'thumb': c.get('thumb', ''), 'video': c.get('video', ''), 'in': c.get('in', 0), 'dur': c.get('dur'), 'loop': bool(c.get('loop')), 'sg': sg, 'score': c.get('sign', 0), 'fit': c.get('fit', 0)}

BOND_ORDER = {'-': 1, '=': 2, '#': 1, '~': 1, '>': 1, '.': 0}   # a rhyme is one cut, however strong
def neighbours(a, b): return b in [f['to'] for f in atoms[a]['flips']] or a in [f['to'] for f in atoms[b]['flips']]
def best_bond(a, b, strong):
    A, B = atoms[a], atoms[b]
    if A['col'] == B['col']: return '#'
    if neighbours(a, b): return '~'
    if A['regime'] == 'movement' and B['regime'] == 'time': return '>'
    if A['regime'] == B['regime'] and strong: return '='
    return '-'

# the Studio's word grid: every spoken word in the order of the lines' times (videotext-studio.html, tokenizeSpoken)
W0, acc = {}, 0
for l in sorted(K['lines'], key=lambda l: l['t0']): W0[l['id']] = acc; acc += len(l['words'])
poems = []
for i, f in enumerate(K['films']):
    w = D['worlds'][i]
    lines = sorted(({'id': l['id'], 't0': l['t0'], 't1': l['t1'], 'text': l['text'], 'w0': W0[l['id']], 'wn': len(l['words'])} for l in K['lines'] if l['film'] == f['n']), key=lambda l: l['t0'])
    beats = [b for b in K['beats'] if b['film'] == f['n']]
    pool, pw = collections.defaultdict(list), collections.Counter()
    for b in beats:
        for c in K['pool'].get(str(b['id']), []):
            g = c.get('sg')
            if not g or g not in atoms: continue
            pw[g] += (c.get('sign') or 50) / 100
            pool[g].append(slim(c, g))
    suite, secs, seq = [], collections.Counter(), []
    for p in D['cuts']['suite']:
        if p['t1'] <= f['t0'] or p['t0'] >= f['t1']: continue
        g = sg_of(p['id'])
        if g in atoms:
            d = min(p['t1'], f['t1']) - max(p['t0'], f['t0']); secs[g] += d
            if not seq or seq[-1] != g: seq.append(g)
            s = shot.get(p['id']) or {}
            pool[g].append({'id': p['id'], 'title': p.get('title', ''), 'year': p.get('year'), 'thumb': p.get('thumb', ''), 'video': p.get('video', ''), 'in': p.get('in', 0), 'dur': None, 'loop': False, 'sg': g, 'score': (s.get('signs') or [{}])[0].get('conf', 80), 'fit': 100, 'suite': True})
    # the measured composition: share of the suite cut's seconds and of the pools' sign weight, equally
    tot_s, tot_p = sum(secs.values()) or 1, sum(pw.values()) or 1
    score = collections.Counter({g: secs[g] / tot_s + pw[g] / tot_p for g in set(secs) | set(pw)})
    top = [g for g, _ in score.most_common(6) if score[g] >= 0.06][:6]
    order = [g for g in seq if g in top] + [g for g, _ in pw.most_common() if g in top]
    order = list(dict.fromkeys(order))
    # the natural compound: its atoms in the order the footage reaches them, each bonded to the last it can still hold
    mol_atoms = [{'k': 'a%d' % k, 'el': g} for k, g in enumerate(order)]
    used = collections.Counter(); bonds = []
    for k in range(1, len(order)):
        a, b = order[k - 1], order[k]
        partner = next((j for j in range(k - 1, -1, -1) if used['a%d' % j] < atoms[order[j]]['valence']), None)
        if partner is None:                              # everything before is full: open the last multiple bond so the chain stays one molecule
            mb = next((x for x in reversed(bonds) if BOND_ORDER[x[2]] > 1), None)
            if mb is None: continue
            used[mb[0]] -= BOND_ORDER[mb[2]] - 1; used[mb[1]] -= BOND_ORDER[mb[2]] - 1; mb[2] = '-'
            partner = next((j for j in range(k - 1, -1, -1) if used['a%d' % j] < atoms[order[j]]['valence']), None)
            if partner is None: continue
        pa = order[partner]; strong = score[pa] > 0.3 and score[b] > 0.3
        t = best_bond(pa, b, strong)
        while BOND_ORDER[t] > min(atoms[pa]['valence'] - used['a%d' % partner], atoms[b]['valence'] - used['a%d' % k]):
            t = {'#': '=', '=': '-', '~': '.', '>': '.', '-': '.'}[t]
        bonds.append(['a%d' % partner, 'a%d' % k, t]); used['a%d' % partner] += BOND_ORDER[t]; used['a%d' % k] += BOND_ORDER[t]
    if order:
        host = max(order, key=lambda g: secs[g] or 0)
        mol_atoms.append({'k': 'l0', 'el': 'Po', 'lig': 'OUT'}); bonds.append(['l0', 'a%d' % order.index(host), ':'])
    for g in pool: pool[g] = sorted({c['id']: c for c in pool[g]}.values(), key=lambda c: (-(c.get('suite') or 0), -(c['score'] or 0), -(c['fit'] or 0)))[:8]
    poems.append({
        'n': f['n'], 'title': f['title'], 't0': f['t0'], 't1': f['t1'], 'accent': w.get('accent'), 'tagline': w.get('tagline', ''),
        'logline': w.get('logline', ''), 'thesis': w.get('thesis', ''), 'tone': w.get('tone', ''), 'moods': w.get('moods', []), 'symbols': w.get('symbols', []),
        'lines': lines, 'secs': {g: round(v, 1) for g, v in secs.most_common()}, 'pool_weight': {g: round(v, 2) for g, v in pw.most_common()},
        'score': {g: round(v, 3) for g, v in score.most_common()}, 'suite_seq': seq, 'shots': dict(pool),
        'natural': {'id': f['n'] + '-natural', 'poem': f['n'], 'kind': 'natural', 'atoms': mol_atoms, 'bonds': bonds},
    })

out = {'atoms': atoms, 'ligands': ligands, 'rows': rows, 'catalysts': catalysts, 'bond_order': BOND_ORDER, 'duration': K['duration'], 'audio': 'wygwyl/WYGWYL_Suite_Audio.mp3', 'poems': poems}
json.dump(out, open(os.path.join(HERE, 'chem-data.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
print('atoms', len(atoms), 'ligands', len(ligands), 'poems', len(poems), os.path.getsize(os.path.join(HERE, 'chem-data.json')) // 1024, 'KB')
for p in poems:
    sym = lambda k: next(atoms[a['el']]['sym'] if a['el'] in atoms else a['el'] for a in p['natural']['atoms'] if a['k'] == k)
    print(p['n'], p['title'][:22].ljust(22), ' '.join(sym(a) + b[2] + sym(c) if False else f"{sym(a)}{b}{sym(c)}" for a, c, b in p['natural']['bonds']))
