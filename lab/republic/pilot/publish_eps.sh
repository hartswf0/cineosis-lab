#!/bin/sh
# push the finished episodes: their films, posters, cuts, the pages and the index (only what changed; the lab's publish rule otherwise)
LAB="$(cd "$(dirname "$0")/../.." && pwd)"; DEST=~/cineosis-lab
cd "$LAB" && republic/.tts/bin/python republic/pilot/make_episodes.py || exit 1
cd "$DEST" && git pull -q --no-rebase || exit 1
mkdir -p lab/republic/pilot lab/score/cues
cp "$LAB"/markov-republic*.html lab/
for f in "$LAB"/republic/pilot/ep*-score.mp4; do n=$(basename "$f" -score.mp4); [ -f "$LAB/republic/pilot/$n.mp4" ] || continue
  for x in "$n-score.mp4" "$n.mp4" "$n-poster.jpg" "$n.json" "$n.picked.json"; do [ -f "$LAB/republic/pilot/$x" ] && cp "$LAB/republic/pilot/$x" lab/republic/pilot/; done; done
cp "$LAB"/republic/pilot/*.py "$LAB"/republic/pilot/CUT_SPEC.md "$LAB"/republic/pilot/batch.sh "$LAB"/republic/pilot/publish_eps.sh lab/republic/pilot/ 2>/dev/null
cp "$LAB"/score/fit.py lab/score/
# the cues the published episodes use
"$LAB"/republic/.tts/bin/python - "$LAB" <<'PY'
import json, glob, os, shutil, sys
lab = sys.argv[1]
for p in glob.glob(os.path.join(lab, "republic/pilot/ep*.picked.json")):
    for s in json.load(open(p)).get("score", []):
        d = os.path.join("lab", s["f"]); os.path.exists(d) or shutil.copy(os.path.join(lab, s["f"]), d)
PY
git add -f lab/republic/pilot/*.mp4 lab/score/cues/*.m4a
git add lab/markov-republic*.html lab/republic/pilot lab/score/fit.py
git reset -q lab/republic/pilot/ep01 2>/dev/null
git commit -q -m "THE REPUBLIC · episodes: $(ls lab/republic/pilot/ep*-score.mp4 | wc -l | tr -d ' ') published, each with its page; every figure introduced where the archive found it.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q && echo "pushed: $(git log --oneline -1)"
