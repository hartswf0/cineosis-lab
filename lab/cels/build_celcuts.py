#!/usr/bin/env python3
"""EVERY CEL CUT, for cel-cuts.html: the cuts of the WYGWYL suite drawn as cartoon cels, side by side on one clock, each with its
chapters, its patch list and how it drew (measured the same way on every cut: the bench's pops/s, ghosting and tracking, the scene
program's colour error, and seconds of compute per second of film). Run after build_cels.py and build_spinecels.py.
  cels/cuts.json   the cuts, the suite's chapters, the measures
  wygwyl/cuts/cels-v1/patches.json   the first way's patch list (kept so the two ways can be compared)
Run from lab/:  python3 cels/build_celcuts.py"""
import os, json, glob, numpy as np

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = '/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH'; VD = f'{MIRROR}/shots/video'
QUALITY = '/Users/gaia/Downloads/butterfly-halfworld/.claude/worktrees/hungry-cori-d982c1/wygwyl/world/districts/tools/.work/story/quality.json'
RELEASE = 'https://github.com/hartswf0/cineosis-lab/releases/download/wygwyl-v1/'
D = json.load(open(os.path.join(LAB, 'spinecut', 'spinecut-data.json')))
med = lambda xs: round(float(np.nanmedian(xs)), 3) if len(xs) else None

v2 = [json.load(open(f)) for f in glob.glob(f'{VD}/P*/v2.json')]; v2 = [m for m in v2 if 'v2' in m]
sp = [json.load(open(f)) for f in glob.glob(f'{VD}/S*/v2.json')]
Q = json.load(open(QUALITY)) if os.path.exists(QUALITY) else []
PS = json.load(open(f'{MIRROR}/progress_spine.json'))
spine_cost = [x['secs'] / x['len'] for P in PS['poems'].values() for x in P['patches'] if x.get('secs')]
measure = lambda R, k: med([r[k] for r in R if r.get(k) is not None])

cuts = [
 {'slug': 'cels', 'title': 'Cels', 'way': 'the second way',
  'idea': 'The film redrawn as cartoon cels: each poem carved into 6–12 s patches on his reading, each patch one moving shot, redrawn every 3 s from the drawing before, EbSynth between.',
  'local': 'wygwyl/cuts/cels/cut.mp4', 'film': RELEASE + 'wygwyl-cels.mp4', 'patches': 'wygwyl/cuts/cels/patches.json', 'tool': 'wygwyl.html#cels',
  'n': len(v2), 'drawings': measure([{'k': m['keys_v2']} for m in v2], 'k'),
  'pops_per_s': measure([m['v2'] for m in v2], 'pops_per_s'), 'ghost': measure([m['v2'] for m in v2], 'ghost'), 'track': measure([m['v2'] for m in v2], 'track'),
  'dE': measure([{'d': m['dE_v2']} for m in v2], 'd'), 'cost': measure([m['v2'] for m in v2], 'total_s_per_s')},
 {'slug': 'spinecels', 'title': 'Spine-Cut Cels', 'way': 'the second way',
  'idea': 'Spine-Cut’s reviewed picks redrawn as cartoon cels: every spine section plays the archive shot its editor chose for the line, redrawn every 3 s from the drawing before, EbSynth between.',
  'local': 'wygwyl/cuts/spinecels/cut.mp4', 'film': RELEASE + 'wygwyl-spinecels.mp4', 'patches': 'wygwyl/cuts/spinecels/patches.json', 'tool': 'spine-cut.html?film=cel',
  'n': len(sp), 'drawings': measure(sp, 'keys'), 'pops_per_s': measure(sp, 'pops_per_s'), 'ghost': measure(sp, 'ghost'), 'track': measure(sp, 'track'), 'dE': measure(sp, 'dE'),
  'cost': med(spine_cost)},
 {'slug': 'cels-v1', 'title': 'Cels, first way', 'way': 'the first way',
  'idea': 'The same patches as Cels, drawn the first way: every keyframe drawn from scratch every second, the frames between blended along the footage’s motion. Kept to compare.',
  'local': 'wygwyl/cuts/cels-v1/cut.mp4', 'film': RELEASE + 'wygwyl-cels-v1.mp4', 'patches': 'wygwyl/cuts/cels-v1/patches.json', 'tool': None,
  'n': len(Q), 'drawings': measure([{'k': m['keys_v1']} for m in v2], 'k'), 'pops_per_s': measure(Q, 'pops_per_s'), 'ghost': measure(Q, 'ghost'), 'track': measure(Q, 'track'),
  'dE': measure(Q, 'dE'), 'cost': measure(Q, 'secs_per_s')},
]
chapters = [{'n': f['n'], 'title': f['title'].title(), 't0': f['t0'], 't1': f['t1']} for f in D['films']]
json.dump({'about': 'every cel cut of the WYGWYL suite (cels/build_celcuts.py)', 'duration': 1440.07, 'chapters': chapters, 'cuts': cuts,
           'measures': {'pops_per_s': 'drawings that jump: sudden changes per second the footage does not explain (lower is steadier)',
                        'ghost': 'double images between drawings (lower is cleaner)', 'track': 'how well the drawing follows the footage’s motion (1 = exactly)',
                        'dE': 'colour error of each drawing against its frame (lower is closer)', 'cost': 'seconds of compute per second of film',
                        'drawings': 'drawings per patch (median)'}},
          open(os.path.join(LAB, 'cels', 'cuts.json'), 'w'), indent=1, ensure_ascii=False)
for c in cuts: print(c['slug'], {k: c[k] for k in ('n', 'drawings', 'pops_per_s', 'ghost', 'track', 'dE', 'cost')})
