"""Lesson 3 · The Neighbourhood. What "near" means inside the machine, measured on the shots the lab has downloaded (lab/clips).
  CLIP  ViT-B/32 image vectors (cache/emb.npy, learned from pictures with words)
  DINO  DINOv2 ViT-S/14 vectors (cache/dino.npy, learned from pictures alone)
For every shot: its 8 nearest by cosine in each machine. Then what neighbours share, against random pairs:
  same source film, black-and-white match, brightness gap, year gap; and how many of the 8 the two machines agree on.
A seed shot for the film, its 8 nearest in each machine, the whole field ordered by closeness to the seed (as a sprite atlas),
and two walks, neighbour of a neighbour, never staying in one film. Captions are BLIP's (rushes/captions.json): a machine's words.
Writes explain/lesson/l3.json and media into explain/lesson/m.   usage: python3 lab/explain/l3.py"""
import json, os, re, subprocess, random
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
M = os.path.join(H, 'lesson', 'm'); F = os.path.join(M, 'f'); os.makedirs(F, exist_ok=True)
J = lambda p: json.load(open(os.path.join(LAB, p)))
BAN = re.compile(r'all my babies|kinderen naar buiten|exhibit 3', re.I)
D = J('lab-data.json'); shots = D['shots']; by = {s['id']: s for s in shots}; drow = {s['id']: i for i, s in enumerate(shots)}
cap = J('rushes/captions.json'); corpus = J('cache/corpus.json')
E = np.load(os.path.join(LAB, 'cache/emb.npy')).astype(np.float32); eid = J('cache/emb_ids.json'); erow = {k: i for i, k in enumerate(eid)}
DN = np.load(os.path.join(LAB, 'cache/dino.npy')).astype(np.float32)
have = {f[:-4] for f in os.listdir(os.path.join(LAB, 'clips')) if f.endswith('.mp4')}
U = [k for k in eid if k in have and k in by and k in drow and not BAN.search(by[k].get('title') or '') and np.abs(DN[drow[k]]).sum() > 0]
n = len(U); print('universe', n)
C = E[[erow[k] for k in U]]; C /= np.linalg.norm(C, axis=1, keepdims=True)
Dv = DN[[drow[k] for k in U]]; Dv /= np.linalg.norm(Dv, axis=1, keepdims=True)
SC, SD = C @ C.T, Dv @ Dv.T; np.fill_diagonal(SC, -2); np.fill_diagonal(SD, -2)
K = 8
NC, ND = np.argsort(-SC, axis=1)[:, :K], np.argsort(-SD, axis=1)[:, :K]
src = [corpus.get(k, {}).get('sourceSlug') or by[k].get('slug') for k in U]
bw = np.array([bool(by[k].get('bw')) for k in U]); lum = np.array([by[k].get('lum') or 0 for k in U], float)
yr = np.array([by[k].get('year') or np.nan for k in U], float)
rng = np.random.default_rng(7); R = rng.integers(0, n, size=(n, K)); R[R == np.arange(n)[:, None]] = (R[R == np.arange(n)[:, None]] + 1) % n
def stats(N):
    i = np.repeat(np.arange(n), K); j = N.ravel()
    same = np.mean([src[a] == src[b] for a, b in zip(i, j)])
    return {'same_film': round(float(same), 3), 'same_bw': round(float(np.mean(bw[i] == bw[j])), 3),
            'lum_gap': round(float(np.mean(np.abs(lum[i] - lum[j]))), 3), 'year_gap': round(float(np.nanmedian(np.abs(yr[i] - yr[j]))), 1)}
S = {'clip': stats(NC), 'dino': stats(ND), 'random': stats(R)}
agree = np.array([len(set(NC[a]) & set(ND[a])) for a in range(n)])
S['agree_mean'] = round(float(agree.mean()), 2); S['agree_none'] = round(float(np.mean(agree == 0)), 3); S['agree_hist'] = np.bincount(agree, minlength=K + 1).tolist()
S['n'] = n; S['bw_share'] = round(float(bw.mean()), 3)
print(json.dumps(S))

def dur(p):
    try: return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
    except Exception: return 0
def enc(k, at, secs, w, name):
    out = os.path.join(M, name)
    if not os.path.exists(out):
        s = os.path.join(LAB, 'clips', k + '.mp4'); d = dur(s); a = max(0, min(at, max(0, d - secs)))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a:.2f}', '-i', s, '-t', str(secs), '-an', '-vf', f'scale={w}:-2,fps=24', '-c:v', 'libx264',
                        '-crf', '30' if w < 500 else '27', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out])
    return 'explain/lesson/m/' + name
def at_of(k): s = os.path.join(LAB, 'clips', k + '.mp4'); return max(0, dur(s) / 3)
def frame(k):
    out = os.path.join(F, k[:8] + '.jpg'); s = os.path.join(LAB, 'thumbs', k + '.jpg')
    if not os.path.exists(out) and os.path.exists(s): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', s, '-vf', 'scale=120:-2', '-q:v', '6', out])
    return 'explain/lesson/m/f/' + k[:8] + '.jpg'
def card(a, hero=False, sim=None):
    k = U[a]; s = by[k]; t = at_of(k)
    c = {'id': k, 'title': s.get('title'), 'year': s.get('year'), 'cap': cap.get(k, ''), 'bw': bool(s.get('bw')), 'src': src[a], 'lum': round(float(lum[a]), 3),
         'loop': enc(k, t, 3.5, 320, f'{k[:8]}-{int(t * 10)}.mp4'), 'frame': frame(k)}
    if hero: c['hero'] = enc(k, t, 6, 960, f'h-{k[:8]}-{int(t * 10)}.mp4')
    if sim is not None: c['sim'] = round(float(sim), 3)
    return c

# the seed: a captioned shot whose two neighbourhoods disagree, whose CLIP neighbours come from several films
capd = np.array([bool(cap.get(k)) for k in U])
score = [(agree[a] == 0) * 2 + len({src[b] for b in NC[a]}) / K + len({src[b] for b in ND[a]}) / K - (0 if capd[a] else 9) - (0 if all(capd[b] for b in NC[a]) else 1) for a in range(n)]
seed = int(np.argmax(score)); print('seed', U[seed], by[U[seed]]['title'], cap.get(U[seed]))
clipN = [card(b, sim=SC[seed, b]) for b in NC[seed]]; dinoN = [card(b, sim=SD[seed, b]) for b in ND[seed]]
# the walks: always to the nearest shot not yet visited and not from a film already visited
def walk(Sm, steps=12):
    path, films = [seed], {src[seed]}
    for _ in range(steps):
        a = path[-1]
        for b in np.argsort(-Sm[a]):
            if b not in path and src[b] not in films: path.append(int(b)); films.add(src[b]); break
    return path
WC, WD = walk(SC), walk(SD)
walks = {'clip': [card(a, sim=(SC[p, a] if i else None)) for i, (p, a) in enumerate(zip([WC[0]] + WC[:-1], WC))],
         'dino': [card(a, sim=(SD[p, a] if i else None)) for i, (p, a) in enumerate(zip([WD[0]] + WD[:-1], WD))]}
# the field: every shot's frame in one sprite atlas; order by closeness to the seed in each machine
CW, CH, COLS = 48, 36, 48
atlas = Image.new('RGB', (CW * COLS, CH * ((n + COLS - 1) // COLS)))
for a, k in enumerate(U):
    try: im = Image.open(os.path.join(LAB, 'thumbs', k + '.jpg')).convert('RGB').resize((CW, CH))
    except Exception: continue
    atlas.paste(im, ((a % COLS) * CW, (a // COLS) * CH))
atlas.save(os.path.join(M, 'l3-atlas.jpg'), quality=72)
oc = np.argsort(-SC[seed]); od = np.argsort(-SD[seed])
rank_c = np.empty(n, int); rank_c[oc] = np.arange(n); rank_d = np.empty(n, int); rank_d[od] = np.arange(n); rank_c[seed] = rank_d[seed] = -1
ex_same = next(a for a in range(n) if capd[a] and sum(src[b] == src[a] for b in NC[a]) >= 6 and all(capd[b] for b in NC[a][:4]))
out = {'n': n, 'K': K, 'stats': S, 'seed': card(seed, hero=True), 'clip': clipN, 'dino': dinoN, 'shared': sorted(set(U[b] for b in NC[seed]) & set(U[b] for b in ND[seed])),
       'walks': walks, 'atlas': {'src': 'explain/lesson/m/l3-atlas.jpg', 'w': CW, 'h': CH, 'cols': COLS, 'rank_clip': rank_c.tolist(), 'rank_dino': rank_d.tolist()},
       'rand': [card(int(a)) for a in np.random.default_rng(11).choice([a for a in range(n) if capd[a] and a != seed and not np.isnan(yr[a])], 8, replace=False)],
       'same_film_case': {'seed': card(ex_same), 'near': [card(b) for b in NC[ex_same]]}}
json.dump(out, open(os.path.join(H, 'lesson', 'l3.json'), 'w'), ensure_ascii=False)
print('clip walk', [cap.get(U[a], by[U[a]]['title'])[:40] for a in WC])
print('dino walk', [cap.get(U[a], by[U[a]]['title'])[:40] for a in WD])
print('shared', len(out['shared']), 'same-film case', by[U[ex_same]]['title'])
