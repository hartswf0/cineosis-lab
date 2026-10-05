"""Words for the room: every word the lab uses to describe its shots (readings, forage queries, subjects, figure descriptions),
each as the mean picture of the shots it describes, in the archive's own CLIP space (markov/emb.bin). A spoken line becomes a
search by averaging its words' pictures, with no model to download. Writes party/lexicon.json + party/lexicon.bin (int8)."""
import json, re, collections, numpy as np
L = json.load(open('markov/library.json')); E = np.frombuffer(open('markov/emb.bin', 'rb').read(), dtype=np.int8).reshape(L['n'], L['dim']).astype(np.float32)
row = {s['id']: i for i, s in enumerate(L['shots'])}
D = json.load(open('lab-data.json'))
STOP = set('a an the and or of to in on at by for with from into onto over under is are was were be been it its this that these those as his her their our your my he she they we you i me him them us one two not no but so if then than there here what which who whom whose when where while out up down off about after before again all any both each few more most other some such only own same very can will just do does did has have had am also yet too nor shot frame film image scene seen shows show shown showing view camera deleuze sign signs simply its own like'.split())
def stem(w):
    for x in ('ing', 'ed', 'es', 's'):
        if len(w) > len(x) + 3 and w.endswith(x): return w[:-len(x)]
    return w
tok = lambda t: [stem(w) for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 2 and w not in STOP]
docs = collections.defaultdict(set)
for s in D['shots']:
    r = row.get(s['id'])
    if r is None: continue
    words = []
    for g in s.get('signs') or []: words += tok((g.get('note') or '').split(':')[0])
    for f in s.get('found') or []: words += tok(f.get('q') or '')
    for u in s.get('subjects') or []: words += tok(u['label'])
    if s.get('scale'): words += tok(s['scale'])
    for w in set(words): docs[w].add(r)
S = json.load(open('markov/sam.json'))
for i, f in enumerate(S['figs']):
    r = row.get(f['shot'])
    if r is None: continue
    for w in set(tok(f.get('desc') or '')): docs[w].add(r)
words = sorted((w for w, rs in docs.items() if len(rs) >= 3), key=lambda w: -len(docs[w]))[:6000]
mean = E.mean(0); out = np.zeros((len(words), L['dim']), np.float32); n = len(row)
for k, w in enumerate(words):
    v = E[sorted(docs[w])].mean(0) - mean; out[k] = v / (np.linalg.norm(v) + 1e-9)
q = np.clip(np.round(out * 127 / np.abs(out).max(1, keepdims=True)), -127, 127).astype(np.int8)
idf = [round(float(np.log(n / len(docs[w]))), 3) for w in words]
json.dump({'n': len(words), 'dim': L['dim'], 'words': words, 'idf': idf}, open('party/lexicon.json', 'w'), separators=(',', ':'))
open('party/lexicon.bin', 'wb').write(q.tobytes())
print(len(words), 'words', q.nbytes // 1024, 'KB')
