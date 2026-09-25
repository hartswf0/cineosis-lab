#!/bin/sh
# CUTBASTARD · the whole chain after the forage search: merge → analyse → shortlist → expand films → download → watch → plan ×4 → render ×4
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
step() { echo "== $(date +%X) $*"; }
step merge;          python3 cutbastard/forage.py merge
step thumbs;         sh fetch.sh cutbastard/forage/thumbs.txt thumbs jpg
step analyse;        $PY analyze.py > cache/analyze3.log 2>&1; $PY affinity.py
step shortlist;      $PY cutbastard/plan.py shortlist
step sources;        python3 cutbastard/forage.py sources $(cat cutbastard/sources.txt)
step merge2;         python3 cutbastard/forage.py merge
step thumbs2;        sh fetch.sh cutbastard/forage/thumbs.txt thumbs jpg
step analyse2;       $PY analyze.py > cache/analyze4.log 2>&1; $PY affinity.py
step shortlist2;     $PY cutbastard/plan.py shortlist
step clips;          python3 -c "
import json
c=json.load(open('cache/corpus.json')); ids=[l.strip() for l in open('cutbastard/shortlist.txt') if l.strip()]
import os
open('cutbastard/clips.txt','w').write(''.join(f\"{c[i]['videoUrl']}\t{i}\n\" for i in ids if i in c and not os.path.exists(f'clips/{i}.mp4')))"
                     sh fetch.sh cutbastard/clips.txt clips mp4
step watch;          $PY cutbastard/watch.py cutbastard/shortlist.txt
for s in suite scenes cineosis drift; do step plan $s; $PY cutbastard/plan.py cut $s; done
for s in suite scenes cineosis drift; do step render $s; python3 cutbastard/render_cut.py $s; done
step build;          python3 build_lab.py
echo "== ALL DONE $(date +%X)"
