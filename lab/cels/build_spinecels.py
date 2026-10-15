#!/usr/bin/env python3
"""THE SPINE-CUT CEL CUT: every Spine-Cut section's reviewed pick redrawn as cartoon cels (butterfly-halfworld,
wygwyl/world/districts/tools/story_spinecels.py: a drawing every 3 s and at every cut, each started from the one before, EbSynth
between), on the suite clock and audio, brought into this lab.
  wygwyl/cuts/spinecels/patches.json + cut.mp4   a sixth cut for wygwyl.html, in the same schema as the others (one patch per section)
  cels/spine.json      per section: the clip drawn, whether it is the reviewed pick, a poster; and where the cut plays (spine-cut.html)
  cels/spine/<S###>.jpg  a poster per section (committed); the cut itself is local, like every .mp4 here, and on the release
Run from lab/:  python3 cels/build_spinecels.py"""
import os, json, shutil, subprocess

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = '/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH'; VD = f'{MIRROR}/shots/video'
RELEASE = 'https://github.com/hartswf0/cineosis-lab/releases/download/wygwyl-v1/'
PLAN = json.load(open(f'{MIRROR}/spinecut_cels_plan.json')); D = json.load(open(os.path.join(LAB, 'spinecut', 'spinecut-data.json')))
TITLE = {f['n']: f['title'].title() for f in D['films']}
OUT = os.path.join(LAB, 'cels'); os.makedirs(f'{OUT}/spine', exist_ok=True)
CUT = os.path.join(LAB, 'wygwyl', 'cuts', 'spinecels'); os.makedirs(CUT, exist_ok=True)

patches, rows = [], []
for p in PLAN:
    s = D['sections'][p['i']]; poster = f"cels/spine/{p['pid']}.jpg"; cel = os.path.join(VD, p['pid'], 'cartoon_v2.mp4')
    if os.path.exists(cel) and not os.path.exists(os.path.join(LAB, poster)):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{min(0.5, p['len'] / 2):.2f}", '-i', cel, '-frames:v', '1', '-vf', 'scale=320:-2', '-q:v', '5', os.path.join(LAB, poster)])
    has = os.path.exists(os.path.join(LAB, poster)); reviewed = p['clip'] == s.get('clean')
    x = D['shots'].get(p['clip']) or {}
    patches.append({'id': s['id'], 't0': p['t0'], 't1': p['t1'], 'chapter': p['film'], 'film': TITLE.get(p['film'], p['film']), 'line': p['line'],
                    'why': ('Spine-Cut’s reviewed pick for this line' if reviewed else p['why'][0].upper() + p['why'][1:]) + (' · a storyboard beat between spoken lines' if p['board'] else ''),
                    'codes': [], 'clip': {'id': p['clip'], 'title': p['title'] or x.get('title'), 'year': p['year'] or x.get('year'), 'source': 'archive',
                                          'thumb': poster if has else x.get('thumb'), 'clip': None, 'in': round(p['in'], 2), 'out': round(p['in'] + p['len'], 2), 'dur': round(p['len'], 2), 'page': None}})
    rows.append({'id': s['id'], 'sec': p['pid'], 'clip': p['clip'], 'reviewed': reviewed, 'poster': poster if has else None})
json.dump(patches, open(os.path.join(CUT, 'patches.json'), 'w'), indent=1, ensure_ascii=False)
src = f'{MIRROR}/film/spinecut_cels.mp4'
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
json.dump({'cut': 'wygwyl/cuts/spinecels/cut.mp4', 'release': RELEASE + 'wygwyl-spinecels.mp4', 'duration': dur, 'sections': rows}, open(os.path.join(OUT, 'spine.json'), 'w'), indent=1)
shutil.copy(src, os.path.join(CUT, 'cut.mp4'))

idx = os.path.join(LAB, 'wygwyl', 'cuts', 'index.json'); I = [c for c in json.load(open(idx)) if c.get('slug') != 'spinecels']
I.append({'slug': 'spinecels', 'title': 'Spine-Cut Cels', 'idea': 'Spine-Cut’s reviewed picks redrawn as cartoon cels: every spine section plays the archive shot its editor chose for the line, drawn every 3 s from the drawing before, EbSynth between.',
          'film': RELEASE + 'wygwyl-spinecels.mp4', 'duration': dur, 'patches': 'wygwyl/cuts/spinecels/patches.json'})
json.dump(I, open(idx, 'w'), indent=1, ensure_ascii=False)
print(len(patches), 'sections ·', sum(r['reviewed'] for r in rows), 'reviewed picks ·', sum(bool(r['poster']) for r in rows), 'posters ·', round(dur, 1), 's')
