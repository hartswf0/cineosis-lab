"""Moving pictures for the main page's doors. For every door on index.html, three archive clips that play in its card, so the
pages can be told apart at a glance. Where a page is made of a known body of footage, the clips come from it (the Odyssey pages
from the Odyssey forage, the WYGWYL pages from the suite's own candidates); everywhere else they are the archive shots that look
most like what the door says (its words read through party/lexicon into the archive's CLIP space). No clip is used by two doors.
Writes lab/doors/doors.json: { href: [{v, in, th}, ...] }.  Run from lab/: python3 doors/build.py"""
import json, os, re, numpy as np
idx = open('../index.html').read()
doors = re.findall(r'<a class="door[^"]*" href="([^"]+)"[^>]*><b>(.*?)</b><span>(.*?)</span>', idx, re.S)
def load(lib, emb):
    J = json.load(open(lib)); E = np.frombuffer(open(emb, 'rb').read(), dtype=np.int8).reshape(J['n'], -1).astype(np.float32)
    E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9; return J['shots'], E
LS, LE = load('markov/library.json', 'markov/emb.bin'); OS, OE = load('odyssey/library.json', 'odyssey/emb.bin')
X = json.load(open('party/lexicon.json')); XV = np.frombuffer(open('party/lexicon.bin', 'rb').read(), dtype=np.int8).reshape(X['n'], -1).astype(np.float32)
XV /= np.linalg.norm(XV, axis=1, keepdims=True) + 1e-9; XI = {w: i for i, w in enumerate(X['words'])}
def stem(w):
    for x in ('ing', 'ed', 'es', 's'):
        if len(w) > len(x) + 3 and w.endswith(x): return w[:-len(x)]
    return w
def query(text):
    ws = [stem(w) for w in re.findall(r'[a-z]+', re.sub(r'<[^>]+>', ' ', text).lower())]; v = np.zeros(XV.shape[1], np.float32)
    for w in ws:
        if w in XI: v += XV[XI[w]] * X['idf'][XI[w]]
    n = np.linalg.norm(v); return v / n if n else None
C = json.load(open('wygwyl/collage-data.json')); wy = set()
for b in C['beats']:
    for c in b.get('candidates', []) + b.get('forage', []): wy.add(c['id'])
lid = {s['id']: i for i, s in enumerate(LS)}; WY = np.array(sorted(lid[i] for i in wy if i in lid))
ok = lambda s: s.get('video', '').startswith('http') and s.get('kind') != 'presence' and (s.get('dur') or 0) >= 3
used, srcs, out = set(), {}, {}
def pick(shots, E, pool, q, n=3):
    cand = pool if pool is not None else np.arange(len(shots))
    if q is None: order = np.random.default_rng(len(out)).permutation(cand)
    else: order = cand[np.argsort(-(E[cand] @ q))]
    got, seen = [], set()
    for i in order[:4000]:
        s = shots[int(i)]
        if not ok(s) or s['video'] in used or s['src'] in seen or srcs.get(s['src'], 0) >= 2: continue
        seen.add(s['src']); got.append(s)
        if len(got) >= n: break
    for s in got: used.add(s['video']); srcs[s['src']] = srcs.get(s['src'], 0) + 1
    th = lambda s: ('lab/' + s['thumb']) if s.get('thumb', '').startswith('thumbs/') and os.path.exists(s['thumb']) else s['video'].replace('/clips/', '/thumbnails/').replace('.mp4', '.jpg')
    return [{'v': s['video'], 'in': round(max(0, (s.get('in') or 0) - .4), 2), 'th': th(s)} for s in got]
for href, title, text in doors:
    if href in out: continue
    words = title + ' ' + text; q = query(words)
    if re.search(r'odyssey|homer', words, re.I): out[href] = pick(OS, OE, None, q)
    elif re.search(r'wygwyl|the poem|her reading|her voice|suite', words, re.I) and len(WY): out[href] = pick(LS, LE, WY, q)
    else: out[href] = pick(LS, LE, None, q)
json.dump(out, open('doors/doors.json', 'w'), separators=(',', ':'))
print(len(out), 'doors;', sum(len(v) for v in out.values()), 'clips;', sum(1 for v in out.values() if len(v) < 3), 'short')
