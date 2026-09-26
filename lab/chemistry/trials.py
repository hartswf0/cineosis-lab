"""Trials of Narrative Chemistry v1: does the chemistry predict, generate or distinguish anything the ordinary
Cineosis taxonomy cannot?  Writes chemistry/trials.json for lab/chemistry-trials.html.

One instrument for every film. Each shot is labelled with the sign of its highest affinity (lab-data.json
aff_top; for all 1,408 pool candidates this equals the sign the pool curated them for). Human cuts and generated
films are read the same way.

Spectroscopy (film → measurement). A film is a list of shots on the poem's clock. Its spectrum:
  stoichiometry   time-weighted share of each sign (45) and of each image type (16)
  pT              share of time in time-images × 14, overall and per tenth of the poem
  transitions     each adjacent pair, classed by what v1 says it could bond as: same sign · rhyme (same image
                  type) · resonance (confusion neighbours) · break (movement → time) · unbreak (time → movement) ·
                  within (same regime, no special bond)
  recurrence      share of shots whose sign already appeared in the poem

E1 Vacuity. What share of adjacent pairs in the human cuts would v1 forbid? (A single cut joins anything, so a
   linear film can never be unlawful; v1 can only speak through which bonds it favours.)
E2 Adjacency. Do human editors put pairs next to each other that v1 calls bonds (rhyme, resonance, break) more
   often than the same shots in shuffled order? Permutation test within each poem, 2,000 shuffles.
E3 Blind synthesis. Hide the four cuts. From the poem's clock, its beats and their candidate pools only, seven
   films per poem, each the same number of slots (two per beat):
     B-random     a random candidate per slot                                   (null)
     B-taxonomy   the best-ranked candidate per slot (the pool's own fit)      (the ordinary taxonomy)
     G-bond       fit plus the strongest lawful bond to the shot before         (the bench's rule)
     G-resonance  fit plus resonance and rhyme only
     G-break      movement-images first, one break, time-images after
     G-compound   a blind compound (built from the pools alone, as the natural one is from the cut) laid over
                  the slots: each atom a run of slots, the best candidate carrying it
     G-isomer     G-compound's own signs, same counts, reordered for the strongest bonds
   Each is measured against the four human cuts: stoichiometry distance, transition distance, a time-aligned
   image-type mismatch, and shot overlap. The four human cuts measured against each other give the ceiling.
E4 Isomers. G-isomer has G-compound's inventory exactly. If ordering alone moves the transition spectrum as far
   as a different inventory does, bonding is doing something the inventory cannot.

Predictions, fixed before the numbers:
  P1 chemistry films are nearer the human cuts' transitions than random ones      (the bonds capture editing)
  P2 chemistry films are nearer the human cuts than the ordinary taxonomy's        (chemistry adds to the taxonomy)
  P3 human cuts over-represent rhyme, resonance or break beyond their own shuffles (editors bond as v1 says)
  P4 isomers differ in transitions at least half as much as different inventories do (same atoms, different film)
Any prediction the numbers refute is reported as refuted.
    python3 lab/chemistry/trials.py
"""
import json, os, random, math, collections, statistics
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
L = json.load(open(os.path.join(LAB, 'lab-data.json')))
K = json.load(open(os.path.join(LAB, 'bets', 'kernel-data.json')))
D = json.load(open(os.path.join(LAB, 'wygwyl', 'collage-data.json')))
C = json.load(open(os.path.join(HERE, 'chem-data.json')))
A = C['atoms']; SIGNS = list(A.keys())
TYPES = sorted({a['col'] for a in A.values()})
shot = {s['id']: s for s in L['shots']}
def label(i): s = shot.get(i); return s['aff_top'][0][0] if s and s.get('aff_top') else None
def neighbours(x, y): return y in [f['to'] for f in A[x]['flips']] or x in [f['to'] for f in A[y]['flips']]
def klass(x, y):
    if x == y: return 'same'
    a, b = A[x], A[y]
    if a['col'] == b['col']: return 'rhyme'
    if neighbours(x, y): return 'resonance'
    if a['regime'] == 'movement' and b['regime'] == 'time': return 'break'
    if a['regime'] == 'time' and b['regime'] == 'movement': return 'unbreak'
    return 'within'
KL = ['same', 'rhyme', 'resonance', 'break', 'unbreak', 'within']
STRENGTH = {'same': 0.2, 'rhyme': 3, 'resonance': 2, 'break': 1.5, 'unbreak': 0, 'within': 0.6}

def spectrum(film, t0, t1):
    film = [p for p in film if p['sg']]
    span = t1 - t0 or 1
    sto = collections.Counter(); typ = collections.Counter(); tt = 0; tenth = [0.0] * 10; tw = [0.0] * 10
    for p in film:
        d = max(0, min(t1, p['t1']) - max(t0, p['t0'])); sto[p['sg']] += d; typ[A[p['sg']]['col']] += d
        if A[p['sg']]['regime'] == 'time': tt += d
        for k in range(10):
            a, b = t0 + span * k / 10, t0 + span * (k + 1) / 10; o = max(0, min(b, p['t1']) - max(a, p['t0']))
            tw[k] += o; tenth[k] += o if A[p['sg']]['regime'] == 'time' else 0
    tot = sum(sto.values()) or 1
    tr = collections.Counter(klass(film[i - 1]['sg'], film[i]['sg']) for i in range(1, len(film)))
    trn = sum(tr.values()) or 1
    seen, rec = set(), 0
    for p in film:
        if p['sg'] in seen: rec += 1
        seen.add(p['sg'])
    return {'sto': {g: round(v / tot, 4) for g, v in sto.items()}, 'types': {str(c): round(v / tot, 4) for c, v in typ.items()},
            'pT': round(14 * tt / tot, 2), 'pT10': [round(14 * tenth[k] / tw[k], 1) if tw[k] else None for k in range(10)],
            'trans': {k: round(tr[k] / trn, 4) for k in KL}, 'trans_n': dict(tr), 'recurrence': round(rec / max(1, len(film)), 3),
            'shots': len(film), 'per_min': round(len(film) / (span / 60), 1)}
def cos(a, b):
    ks = set(a) | set(b); num = sum(a.get(k, 0) * b.get(k, 0) for k in ks)
    na = math.sqrt(sum(v * v for v in a.values())); nb = math.sqrt(sum(v * v for v in b.values()))
    return num / (na * nb) if na and nb else 0
def tv(a, b): return 0.5 * sum(abs(a.get(k, 0) - b.get(k, 0)) for k in KL)
def timeline(film, t0, t1, n=40):
    out = []
    for k in range(n):
        t = t0 + (t1 - t0) * (k + 0.5) / n; p = next((p for p in film if p['t0'] <= t < p['t1'] and p['sg']), None)
        out.append(A[p['sg']]['col'] if p else None)
    return out
def mismatch(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    return sum(x != y for x, y in pairs) / len(pairs) if pairs else 1
def distance(f, g, t0, t1):
    sf, sg = spectrum(f, t0, t1), spectrum(g, t0, t1)
    ids_f, ids_g = {p['id'] for p in f}, {p['id'] for p in g}
    return {'d_sto': round(1 - cos(sf['sto'], sg['sto']), 4), 'd_type': round(1 - cos(sf['types'], sg['types']), 4), 'd_trans': round(tv(sf['trans'], sg['trans']), 4),
            'd_time': round(mismatch(timeline(f, t0, t1), timeline(g, t0, t1)), 4), 'overlap': round(len(ids_f & ids_g) / max(1, len(ids_f | ids_g)), 4)}

def piece(c, t0, t1):
    return {'id': c['id'], 'title': c.get('title', ''), 'year': c.get('year'), 'thumb': c.get('thumb', ''), 'video': c.get('video', ''), 'in': c.get('in', 0) or 0, 'loop': bool(c.get('loop')), 't0': round(t0, 3), 't1': round(t1, 3), 'sg': label(c['id'])}

# ---------- the generators: blind to the cuts ----------
def slots_for(f, beats):
    n = max(4, 2 * len(beats)); span = f['t1'] - f['t0']
    out = []
    for k in range(n):
        a, b = f['t0'] + span * k / n, f['t0'] + span * (k + 1) / n; m = (a + b) / 2
        bt = next((x for x in beats if x['t0'] <= m < x['t1']), None) or min(beats, key=lambda x: min(abs(x['t0'] - m), abs(x['t1'] - m)))
        out.append((a, b, [c for c in K['pool'].get(str(bt['id']), []) if label(c['id'])]))
    return out
def fitn(c): return (c.get('fit') or 0) / 100
def gen_random(slots, rng):
    used, film = set(), []
    for a, b, cands in slots:
        cs = [c for c in cands if c['id'] not in used] or cands; c = rng.choice(cs); used.add(c['id']); film.append(piece(c, a, b))
    return film
def gen_taxonomy(slots):
    used, film = set(), []
    for a, b, cands in slots:
        cs = sorted([c for c in cands if c['id'] not in used] or cands, key=lambda c: -(c.get('fit') or 0)); c = cs[0]; used.add(c['id']); film.append(piece(c, a, b))
    return film
def gen_scored(slots, score):
    used, film, prev = set(), [], None
    for i, (a, b, cands) in enumerate(slots):
        cs = [c for c in cands if c['id'] not in used] or cands
        c = max(cs, key=lambda c: score(c, prev, i, len(slots))); used.add(c['id']); film.append(piece(c, a, b)); prev = label(c['id'])
    return film
def bond_score(c, prev, i, n): return fitn(c) + (0.35 * STRENGTH[klass(prev, label(c['id']))] / 3 if prev else 0)
def res_score(c, prev, i, n): return fitn(c) + (0.5 if prev and klass(prev, label(c['id'])) in ('rhyme', 'resonance') else 0)
def break_score(c, prev, i, n):
    want = 'movement' if i < n / 2 else 'time'
    return fitn(c) + (0.6 if A[label(c['id'])]['regime'] == want else 0)
def blind_compound(f, beats):
    """the natural compound's rule, from the pools alone: the signs that carry most of the poem's candidates, in the order the beats reach them"""
    w = collections.Counter(); first = {}
    for k, bt in enumerate(beats):
        for c in K['pool'].get(str(bt['id']), []):
            g = label(c['id'])
            if not g: continue
            w[g] += (c.get('sign') or 50) / 100; first.setdefault(g, k)
    top = [g for g, _ in w.most_common(6)]
    return sorted(top, key=lambda g: first[g])
def realise(slots, atoms_seq):
    """lay a sequence of atoms over the slots: each atom a contiguous run; per slot the best candidate carrying it, else a neighbour (a flip), else the best"""
    used, film = set(), []
    n, m = len(slots), len(atoms_seq)
    for i, (a, b, cands) in enumerate(slots):
        g = atoms_seq[min(m - 1, i * m // n)]
        cs = [c for c in cands if c['id'] not in used] or cands
        exact = [c for c in cs if label(c['id']) == g]; near = [c for c in cs if neighbours(g, label(c['id']))]
        pickfrom = exact or near or cs
        c = max(pickfrom, key=fitn); used.add(c['id']); film.append(piece(c, a, b))
    return film
def isomer_order(labels):
    """the same signs, the same counts, reordered greedily for the strongest bond at each step"""
    left = collections.Counter(labels); out = [labels[0]]; left[labels[0]] -= 1
    while sum(left.values()):
        prev = out[-1]; nxt = max((g for g in left if left[g] > 0), key=lambda g: (STRENGTH[klass(prev, g)] if g != prev else -1, left[g]))
        out.append(nxt); left[nxt] -= 1
    return out
def realise_seq(slots, seq):
    used, film = set(), []
    for (a, b, cands), g in zip(slots, seq):
        cs = [c for c in cands if c['id'] not in used] or cands
        pickfrom = [c for c in cs if label(c['id']) == g] or [c for c in cs if neighbours(g, label(c['id']))] or cs
        c = max(pickfrom, key=fitn); used.add(c['id']); film.append(piece(c, a, b))
    return film

rng = random.Random(1440)
HUMAN = ['suite', 'scenes', 'cineosis', 'drift']
GENS = ['B-random', 'B-taxonomy', 'G-bond', 'G-resonance', 'G-break', 'G-compound', 'G-isomer']
poems, vac_pairs, vac_bad = [], 0, 0
adj = {cut: collections.Counter() for cut in HUMAN}; adj_null = {cut: collections.defaultdict(list) for cut in HUMAN}
for f in K['films']:
    t0, t1 = f['t0'], f['t1']; beats = [b for b in K['beats'] if b['film'] == f['n']]
    human = {cut: [piece({'id': p['id'], 'title': p.get('title'), 'year': p.get('year'), 'thumb': p.get('thumb'), 'video': p.get('video'), 'in': p.get('in', 0)}, max(t0, p['t0']), min(t1, p['t1'])) for p in D['cuts'][cut] if p['t1'] > t0 and p['t0'] < t1] for cut in HUMAN}
    # E1 vacuity and E2 adjacency, on the human cuts
    for cut, film in human.items():
        labs = [p['sg'] for p in film if p['sg']]
        vac_pairs += max(0, len(labs) - 1)
        obs = collections.Counter(klass(labs[i - 1], labs[i]) for i in range(1, len(labs))); adj[cut].update(obs)
        sims = []
        for _ in range(2000):
            sh = labs[:]; rng.shuffle(sh); sims.append(collections.Counter(klass(sh[i - 1], sh[i]) for i in range(1, len(sh))))
        for k in KL: adj_null[cut][k].append([s[k] for s in sims])
    # E3 blind synthesis
    slots = slots_for(f, beats)
    comp = blind_compound(f, beats)
    g_comp = realise(slots, comp)
    films = {
        'B-random': gen_random(slots, rng), 'B-taxonomy': gen_taxonomy(slots),
        'G-bond': gen_scored(slots, bond_score), 'G-resonance': gen_scored(slots, res_score), 'G-break': gen_scored(slots, break_score),
        'G-compound': g_comp, 'G-isomer': realise_seq(slots, isomer_order([p['sg'] for p in g_comp])),
    }
    specs = {k: spectrum(v, t0, t1) for k, v in {**films, **human}.items()}
    dist = {g: {cut: distance(films[g], human[cut], t0, t1) for cut in HUMAN} for g in GENS}
    ceil = {f'{a}~{b}': distance(human[a], human[b], t0, t1) for i, a in enumerate(HUMAN) for b in HUMAN[i + 1:]}
    iso = {'isomer_vs_compound': distance(films['G-isomer'], films['G-compound'], t0, t1), 'bond_vs_compound': distance(films['G-bond'], films['G-compound'], t0, t1), 'taxonomy_vs_compound': distance(films['B-taxonomy'], films['G-compound'], t0, t1)}
    poems.append({'n': f['n'], 'title': f['title'], 't0': t0, 't1': t1, 'blind_compound': comp, 'films': films, 'human': human, 'spectra': specs, 'dist': dist, 'ceiling': ceil, 'isomer': iso})

# ---------- the verdicts ----------
def mean(xs): xs = [x for x in xs if x is not None]; return round(statistics.mean(xs), 4) if xs else None
def summary(metric):
    return {g: mean([p['dist'][g][cut][metric] for p in poems for cut in HUMAN]) for g in GENS} | {'human ceiling': mean([d[metric] for p in poems for d in p['ceiling'].values()])}
def wins(g, base, metric, lower=True):
    w = sum(1 for p in poems if (mean([p['dist'][g][c][metric] for c in HUMAN]) < mean([p['dist'][base][c][metric] for c in HUMAN])) == lower)
    n = len(poems); p = sum(math.comb(n, k) for k in range(w, n + 1)) / 2 ** n          # one-sided sign test
    return {'wins': w, 'of': n, 'p': round(p, 4)}
metrics = {m: summary(m) for m in ['d_sto', 'd_type', 'd_trans', 'd_time', 'overlap']}
chem = ['G-bond', 'G-resonance', 'G-break', 'G-compound', 'G-isomer']
tests = {g: {'vs_random': {m: wins(g, 'B-random', m) for m in ['d_trans', 'd_time', 'd_type']}, 'vs_taxonomy': {m: wins(g, 'B-taxonomy', m) for m in ['d_trans', 'd_time', 'd_type']}} for g in chem}
e2 = {}
for cut in HUMAN:
    e2[cut] = {}
    for k in KL:
        obs = adj[cut][k]; null = [sum(col[i] for col in adj_null[cut][k]) for i in range(2000)]
        mu, sd = statistics.mean(null), statistics.pstdev(null) or 1
        e2[cut][k] = {'observed': obs, 'expected': round(mu, 1), 'z': round((obs - mu) / sd, 2), 'p_over': round(sum(x >= obs for x in null) / 2000, 4), 'p_under': round(sum(x <= obs for x in null) / 2000, 4)}
iso_t = mean([p['isomer']['isomer_vs_compound']['d_trans'] for p in poems]); inv_t = mean([p['isomer']['taxonomy_vs_compound']['d_trans'] for p in poems])
iso_s = mean([p['isomer']['isomer_vs_compound']['d_sto'] for p in poems]); inv_s = mean([p['isomer']['taxonomy_vs_compound']['d_sto'] for p in poems])
best_chem_trans = min(chem, key=lambda g: metrics['d_trans'][g])
bonded = ['rhyme', 'resonance', 'break']
p3 = {cut: [k for k in bonded if e2[cut][k]['p_over'] < 0.05] for cut in HUMAN}
verdicts = {
  'P1': {'claim': 'chemistry films are nearer the human cuts’ transitions than random films', 'holds': sum(tests[g]['vs_random']['d_trans']['p'] < 0.05 for g in chem) >= 3,
         'evidence': {g: tests[g]['vs_random']['d_trans'] for g in chem}},
  'P2': {'claim': 'chemistry films are nearer the human cuts than the ordinary taxonomy’s', 'holds': any(tests[g]['vs_taxonomy'][m]['p'] < 0.05 for g in chem for m in ['d_trans', 'd_time']),
         'evidence': {g: tests[g]['vs_taxonomy'] for g in chem}},
  'P3': {'claim': 'human cuts over-represent rhyme, resonance or break beyond their own shuffles', 'holds': sum(bool(v) for v in p3.values()) >= 2, 'evidence': p3},
  'P4': {'claim': 'isomers differ in transitions at least half as much as different inventories do', 'holds': iso_t >= 0.5 * inv_t,
         'evidence': {'isomer transition distance': iso_t, 'different-inventory transition distance': inv_t, 'isomer stoichiometry distance': iso_s, 'different-inventory stoichiometry distance': inv_s}},
}
out = {'ontology': 'v1', 'labeller': 'aff_top[0] (lab-data.json) for every shot', 'generators': GENS, 'human': HUMAN, 'classes': KL, 'metrics': metrics, 'tests': tests, 'adjacency': e2,
       'vacuity': {'pairs': vac_pairs, 'forbidden': vac_bad, 'share_forbidden': 0.0, 'note': 'a single cut may join any two signs, so no linear film breaks v1; v1 speaks only through which bonds it favours'},
       'verdicts': verdicts, 'poems': poems}
json.dump(out, open(os.path.join(HERE, 'trials.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
print('trials.json', os.path.getsize(os.path.join(HERE, 'trials.json')) // 1024, 'KB')
for m, v in metrics.items(): print(m.ljust(8), '  '.join(f'{k} {v[k]}' for k in v))
for k, v in verdicts.items(): print(k, 'HOLDS' if v['holds'] else 'REFUTED', '·', v['claim'])
print('adjacency (suite):', {k: (e2['suite'][k]['observed'], e2['suite'][k]['expected'], e2['suite'][k]['z']) for k in KL})
for g in chem: print(g, 'vs random', {m: (t['wins'], t['p']) for m, t in tests[g]['vs_random'].items()}, 'vs taxonomy', {m: (t['wins'], t['p']) for m, t in tests[g]['vs_taxonomy'].items()})
