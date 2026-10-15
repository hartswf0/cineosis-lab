"""Media for Lessons 5 and 9: small looping clips and tiny frames, so a lesson can show many moving images at once.
  loops   explain/lesson/m/<id8>-<in>.mp4   320 px wide, 3.5 s, no sound, starting at the shot's own in-point (or a third in)
  frames  explain/lesson/m/f/<id8>.jpg      120 px wide
Writes explain/lesson/l5m.json and explain/lesson/l9m.json with the shots each lesson needs, their plain-language captions
and media paths. Films the lab keeps out of its examples are never used.   usage: python3 lab/explain/lesson_media.py"""
import json, os, re, subprocess
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); C44 = os.path.dirname(LAB)
M = os.path.join(H, 'lesson', 'm'); F = os.path.join(M, 'f'); os.makedirs(F, exist_ok=True)
BAN = re.compile(r'all my babies|kinderen naar buiten|exhibit 3', re.I)
U = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
corpus = json.load(open(os.path.join(LAB, 'cache', 'corpus.json')))
def title(u): return (corpus.get(u) or {}).get('sourceTitle') or ''
def year(u): return (corpus.get(u) or {}).get('sourceYear')
def ok(u): return not BAN.search(title(u)) and os.path.exists(os.path.join(LAB, 'clips', u + '.mp4'))
def dur(p):
    try: return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
    except Exception: return 0
def loop(u, at=None, secs=3.5):
    src = os.path.join(LAB, 'clips', u + '.mp4'); d = dur(src)
    if at is None: at = max(0, d / 3)
    at = max(0, min(at, max(0, d - secs)))
    name = f'{u[:8]}-{int(at * 10)}.mp4'; out = os.path.join(M, name)
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{at:.2f}', '-i', src, '-t', str(secs), '-an', '-vf', 'scale=320:-2,fps=24', '-c:v', 'libx264',
                        '-crf', '30', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out])
    return 'explain/lesson/m/' + name
def hero(u, at, secs):
    # a sharp loop for a shot that fills the screen: 960 px, the length of its line (at most 9 s)
    src = os.path.join(LAB, 'clips', u + '.mp4'); d = dur(src); secs = max(3.5, min(9, secs)); at = max(0, min(at, max(0, d - secs)))
    name = f'h-{u[:8]}-{int(at * 10)}.mp4'; out = os.path.join(M, name)
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{at:.2f}', '-i', src, '-t', f'{secs:.2f}', '-an', '-vf', 'scale=960:-2,fps=24', '-c:v', 'libx264',
                        '-crf', '27', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out])
    return 'explain/lesson/m/' + name
def frame(u):
    out = os.path.join(F, u[:8] + '.jpg'); src = os.path.join(LAB, 'thumbs', u + '.jpg')
    if not os.path.exists(out) and os.path.exists(src): subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', 'scale=120:-2', '-q:v', '6', out])
    return 'explain/lesson/m/f/' + u[:8] + '.jpg'
shot = lambda u, cap='', at=None: {'id': u, 'title': title(u), 'year': year(u), 'cap': cap, 'loop': loop(u, at), 'frame': frame(u)}

picks = json.load(open(os.path.join(C44, 'picks.json')))
signs = {s['n']: s for s in json.load(open(os.path.join(LAB, 'lab-data.json')))['signs']}
def examples(n, k):
    return [shot(u, c) for u, c in picks.get(n, []) if ok(u)][:k]
l5 = json.load(open(os.path.join(H, 'lesson', 'l5.json')))
T = json.load(open(os.path.join(H, 'ep', 'takes.json')))
# the table: every sign, by its first usable reference shot
table = {n: (examples(n, 1) or [None])[0] for n in signs}
need = {'6': 5, '34a': 5, '1': 3, '2': 2, '4': 2}
for p in l5['practice']:
    s = signs[str(p['signs'][0]['n'])]; need[s['n']] = max(need.get(s['n'], 0), 1)
    for c in s['confusions'][:2]: need[c] = max(need.get(c, 0), 1)
ex = {n: examples(n, k) for n, k in need.items()}
def take_shot(r): u = U.search(r['thumb']).group(0); return {'id': u, 'title': r['title'], 'year': r['year'], 'hide': bool(BAN.search(r['title'] or '')),
    'loop': loop(u, r.get('in')) if ok(u) else None, 'frame': frame(u), 'signs': [s['n'] for s in (r.get('signs') or [])]}
rows = T['cineosis']['rows']
op = rows[[r['id'] for r in rows].index(l5['open']['id'])]
practice = [take_shot(rows[[r['id'] for r in rows].index(p['id'])]) for p in l5['practice']]
for x, p in zip(practice, l5['practice']): x['hero'] = hero(x['id'], p.get('in') or 0, p['t1'] - p['t0'])
start = 40; montage = [take_shot(r) for r in rows[start:start + 16] if not BAN.search(r['title'] or '')][:12]
tally = [{'frame': frame(U.search(r['thumb']).group(0)), 'hide': bool(BAN.search(r['title'] or ''))} for r in rows]
OPN = take_shot(op); OPN['loop'] = loop(OPN['id'], (op.get('in') or 0) + 1.6)   # past the fade-in, into the room
OPN['hero'] = hero(OPN['id'], (op.get('in') or 0) + 1.6, op['t1'] - op['t0'])
json.dump({'table': table, 'ex': ex, 'open': OPN, 'practice': practice, 'montage': montage, 'tally': tally},
          open(os.path.join(H, 'lesson', 'l5m.json'), 'w'), ensure_ascii=False)
# Lesson 9
l9 = json.load(open(os.path.join(H, 'lesson', 'l9.json'))); TK = l9['takes']; oi = l9['open']['i']
open4 = {k: take_shot(T[k]['rows'][oi]) for k in TK}
for k in TK: r = T[k]['rows'][oi]; open4[k]['hero'] = hero(open4[k]['id'], r.get('in') or 0, r['t1'] - r['t0']) if ok(open4[k]['id']) else None
lanes = {k: [{'frame': frame(U.search(r['thumb']).group(0)), 'hide': bool(BAN.search(r['title'] or '')), 'src': r.get('src')} for r in T[k]['rows']] for k in TK}
W0 = max(0, min(l9['n'] - 6, oi - 2)); loom = {k: [take_shot(T[k]['rows'][i]) for i in range(W0, W0 + 6)] for k in TK}
scenes_run = next(i for i in range(len(T['scenes']['rows']) - 2) if T['scenes']['rows'][i]['src'] == T['scenes']['rows'][i + 1]['src'] == T['scenes']['rows'][i + 2]['src'] and not BAN.search(T['scenes']['rows'][i]['title'] or ''))
stay = {k: [take_shot(T[k]['rows'][i]) for i in range(scenes_run, scenes_run + 3)] for k in TK}
meet = [{'i': m['i'], 'takes': m['takes'], 'shot': take_shot(T[m['takes'][0]]['rows'][m['i']])} for m in l9['same_shot']]
json.dump({'open': open4, 'lanes': lanes, 'loom': loom, 'W0': W0, 'stay': stay, 'stay_i': scenes_run, 'meet': meet},
          open(os.path.join(H, 'lesson', 'l9m.json'), 'w'), ensure_ascii=False)
n = len(os.listdir(M)); size = sum(os.path.getsize(os.path.join(M, f)) for f in os.listdir(M) if f.endswith('.mp4')) + sum(os.path.getsize(os.path.join(F, f)) for f in os.listdir(F))
print('media files', n, 'frames', len(os.listdir(F)), 'MB', round(size / 1e6, 1))
print('table missing', [n for n, v in table.items() if not v]); print('scenes run at', scenes_run, [s['title'] for s in stay['scenes']])
