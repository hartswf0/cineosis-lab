#!/usr/bin/env python3
"""THE CEL LAYER: the WYGWYL film redrawn as cartoon cels (butterfly-halfworld, wygwyl/world/districts/tools: story_carve.py →
story_cels.py, through wygwyl-world-arch's drawing pipeline), brought onto this lab's suite clock so every tool can show it.
  cels/cels.json   poems   per-poem map from the reading's own clock to the suite clock (fitted on her words: kernel-data.json)
                   patches every patch of the film on the suite clock: scene, line, source, cel, poster, status
                   clips   for archive shots of this lab's corpus that the film drew: their cel and poster, by corpus id
                   celability  for every watched clip (cache/watch): could it become a cel? 0–100 and why
  cels/posters/    a poster per patch (committed); cels/patches/<patch>.mp4 the moving cel (local, like every .mp4 here)
  wygwyl/cuts/cels/patches.json + cut.mp4   a fifth cut for wygwyl.html, in the same schema as the other four
Run from lab/:  python3 cels/build_cels.py   (paths to the film's working data are below)"""
import os, re, json, glob, shutil, subprocess, numpy as np

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BH = '/Users/gaia/Downloads/butterfly-halfworld/.claude/worktrees/hungry-cori-d982c1/wygwyl'          # the film's repository
FILM = f'{BH}/world/districts/tools/.work/story/film.json'; MIRROR = '/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH'
WORK = '/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab'                                          # the lab's working copy (watch data, clips)
OUT = os.path.join(LAB, 'cels'); os.makedirs(f'{OUT}/posters', exist_ok=True); os.makedirs(f'{OUT}/patches', exist_ok=True)
CUT = os.path.join(LAB, 'wygwyl', 'cuts', 'cels'); os.makedirs(CUT, exist_ok=True)
F = json.load(open(FILM)); K = json.load(open(os.path.join(LAB, 'bets', 'kernel-data.json'))); CLOCK = json.load(open(f'{BH}/clock.json'))
norm = lambda s: re.sub(r"[^a-z0-9']", '', s.lower().replace('’', "'"))

# ---------- the reading's clock → the suite's clock, per poem (least squares on the words both know) ----------
poems = {}
for p in sorted(F):
    T = json.load(open(f'{BH}/timings/{p}.json')); ours = [(norm(w['w']), w['s']) for sg in T['segments'] for w in sg['words']]
    theirs = [(norm(w['w']), w['t0']) for l in K['lines'] if str(l['film']).zfill(2) == p for w in l.get('words', [])]
    pairs, j = [], 0
    for wd, s in ours:                                                          # walk both word lists in order
        for k in range(j, min(j + 6, len(theirs))):
            if theirs[k][0] == wd: pairs.append((s, theirs[k][1])); j = k + 1; break
    x, y = np.array(pairs).T if len(pairs) > 3 else (np.array([0.0, 1.0]), np.array([0.0, 1.0]))
    a, b = np.polyfit(x, y, 1) if len(pairs) > 3 else (1.0, 0.0)
    span = next(s for s in CLOCK['spans'] if s['num'] == p)
    poems[p] = {'title': F[p]['title'], 'scale': round(float(a), 5), 'offset': round(float(b), 3), 'words_matched': len(pairs), 'chapter': [span['t0'], span['t1']],
                'residual_s': round(float(np.abs(np.polyval([a, b], x) - y).mean()), 3) if len(pairs) > 3 else None}
S = lambda p, t: round(poems[p]['scale'] * t + poems[p]['offset'], 3)

# ---------- patches, clips ----------
cid_of = lambda path: (re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.(?:mp4|jpg)$', path or '') or [None, None])[1]
corpus = json.load(open(os.path.join(WORK, 'cache', 'corpus.json')))
patches, clips = [], {}
for p, f in sorted(F.items()):
    for s in f['shots']:
        if not s.get('id'): continue
        pid = s['id']; cel = f'{MIRROR}/shots/video/{pid}/cartoon.mp4'; cid = cid_of((s.get('clip') or {}).get('path')) or cid_of(s.get('path'))
        drawn = os.path.exists(cel)
        if drawn:
            shutil.copy(cel, f'{OUT}/patches/{pid}.mp4')
            for at in (min(2.0, (s['t1'] - s['t0']) / 2), 0.0):                     # a held drawing's cel is short: fall back to its first frame
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{at:.2f}', '-i', cel, '-frames:v', '1', '-vf', 'scale=320:-1', f'{OUT}/posters/{pid}.jpg'])
                if os.path.exists(f'{OUT}/posters/{pid}.jpg'): break
        c = corpus.get(cid) if cid else None
        rec = {'id': pid, 'poem': p, 't0': S(p, s['t0']), 't1': S(p, s['t1']), 'scene': s['scene'], 'name': s['name'], 'what': s['what'], 'line': s.get('said', ''),
               'family': s.get('source'), 'clip': cid if c else None, 'title': (c or {}).get('sourceTitle') or (s.get('clip') or {}).get('title'), 'year': (c or {}).get('sourceYear'),
               'window': [(s.get('clip') or {}).get('in'), (s.get('clip') or {}).get('len')] if s.get('clip') else None,
               'cel': f'cels/patches/{pid}.mp4' if drawn else None, 'poster': f'cels/posters/{pid}.jpg' if drawn else None,
               'status': 'drawn' if drawn else 'to make' if not s.get('k') else 'not drawn', 'generate': bool(s.get('generate'))}
        patches.append(rec)
        if c and drawn: clips[cid] = {'patch': pid, 'cel': rec['cel'], 'poster': rec['poster'], 'poem': p, 'window': rec['window']}

# ---------- could a clip become a cel? (every watched clip) ----------
W = {}
for f in glob.glob(os.path.join(WORK, 'cache', 'watch', '*.json')):
    try: j = json.load(open(f))
    except Exception: continue
    if not j.get('bad'): W[j['id']] = j
mot = np.array([w.get('motion', 0) for w in W.values()]); lo, hi = np.percentile(mot, [15, 85]) if len(mot) else (0, 1)
celab = {}
for i, w in W.items():
    why, sc = [], 100.0
    if w.get('dead', 0) > 0.05: sc *= max(0, 1 - w['dead'] / 0.3); why.append(f"dead frames {w['dead']:.2f}")
    if w.get('card', 0) > 0.2: sc *= max(0, 1 - w['card'] / 0.6); why.append(f"title card {w['card']:.2f}")
    m = w.get('motion', 0)
    if m < lo: sc *= 0.8; why.append('barely moves: a held drawing')
    elif m > hi: sc *= max(0.3, 1 - (m - hi) / (hi + 1e-6)); why.append('fast: in-betweens will tear')
    if w.get('dur', 0) < 4: sc *= 0.7; why.append(f"short ({w['dur']:.1f} s)")
    if i in clips: sc = max(sc, 90); why.append('drawn')
    celab[i] = {'score': int(round(sc)), 'why': why or ['clean, moving, long enough']}

json.dump({'version': 1, 'about': 'the WYGWYL film as cartoon cels, on the suite clock (see cels/build_cels.py)', 'poems': poems, 'patches': patches, 'clips': clips, 'celability': celab},
          open(f'{OUT}/cels.json', 'w'), separators=(',', ':'), ensure_ascii=False)

# ---------- a fifth cut for wygwyl.html ----------
cut = [{'id': r['id'], 't0': r['t0'], 't1': r['t1'], 'chapter': r['poem'], 'film': poems[r['poem']]['title'], 'line': r['line'], 'why': f"{r['name']}: {r['what']}", 'codes': [],
        'clip': {'id': r['clip'] or r['id'], 'title': r['title'] or (r['family'] or '') + ' footage', 'year': r['year'], 'source': r['family'], 'thumb': r['poster'], 'clip': r['cel'],
                 'in': (r['window'] or [0, 0])[0] or 0, 'out': ((r['window'] or [0, 0])[0] or 0) + ((r['window'] or [0, 0])[1] or 0), 'dur': round(r['t1'] - r['t0'], 2), 'page': None}}
       for r in patches]
json.dump(cut, open(f'{CUT}/patches.json', 'w'), indent=1, ensure_ascii=False)
idx = json.load(open(os.path.join(LAB, 'wygwyl', 'cuts', 'index.json'))); idx = [x for x in idx if x['slug'] != 'cels']
idx.append({'slug': 'cels', 'title': 'Cels', 'idea': 'The film redrawn as cartoon cels: each poem carved into patches on her reading, each patch one moving shot redrawn in the angular multiplane style.',
            'film': 'https://github.com/hartswf0/cineosis-lab/releases/download/wygwyl-v1/wygwyl-cels.mp4', 'duration': K['duration'], 'patches': 'wygwyl/cuts/cels/patches.json'})
json.dump(idx, open(os.path.join(LAB, 'wygwyl', 'cuts', 'index.json'), 'w'), indent=1, ensure_ascii=False)
import sys
if '--no-film' in sys.argv: print('patches', len(patches)); raise SystemExit
# the suite-length film: each poem's clean cel film placed at its reading's place in its chapter, the first and last drawings held to fill
parts = []
for p in sorted(poems):
    c0, c1 = poems[p]['chapter']; src = f'{MIRROR}/film/{p}_cel_clean.mp4'
    if not os.path.exists(src): continue
    lead = max(0.0, poems[p]['offset'] - c0); dur = c1 - c0; o = f'{CUT}/_part{p}.mp4'
    vf = f"setpts=PTS/{poems[p]['scale']},tpad=start_mode=clone:start_duration={lead:.3f}:stop_mode=clone:stop_duration={dur:.3f},trim=duration={dur:.3f},fps=24,scale=1280:720,format=yuv420p"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '21', '-preset', 'veryfast', o], check=True); parts.append(o)
open(f'{CUT}/_list.txt', 'w').write(''.join(f"file '{x}'\n" for x in parts))
audio = os.path.join(WORK, 'wygwyl', 'WYGWYL_Suite_Audio.mp3')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{CUT}/_list.txt', '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest',
                '-movflags', '+faststart', f'{CUT}/cut.mp4'], check=True)
for x in parts + [f'{CUT}/_list.txt']: os.remove(x)
print('poems', {p: (v['offset'], v['scale'], v['words_matched'], v['residual_s']) for p, v in poems.items()})
print('patches', len(patches), '· drawn', sum(r['status'] == 'drawn' for r in patches), '· archive clips drawn', len(clips), '· watched clips scored', len(celab))
