"""Choose the Odyssey clips worth cutting figures out of, fetch them, and write the job list for ../seg_track.py --jobs=.
A figure ask (a scene's "figures" query, or an animal/ship/people motion) keeps its best PER clips by archive score, one per
source film. usage: python3 seg_jobs.py [PER] [LIMIT]"""
import json, os, sys, urllib.request, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); D = os.path.join(H, "clips"); os.makedirs(D, exist_ok=True)
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 2; LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
MOTION_FIG = ("motion:animals", "motion:dog", "motion:birds", "motion:giant", "motion:disguise", "motion:archery", "motion:loom", "motion:sailing", "motion:rowing", "motion:horses", "motion:strait")
clips = json.load(open(os.path.join(H, "results", "clips.json")))
by_q = {}
for c in clips:
    for key, role, q, rank, sc in c["asks"]:
        if role == "figures" or key in MOTION_FIG: by_q.setdefault(q, []).append((rank, c))
# a scene's own figure asks are ranked by CLIP in scenes.json (build_scenes.py): take those orders where they exist
if os.path.exists(os.path.join(H, "scenes.json")):
    C = {c["id"]: c for c in clips}
    for sc in json.load(open(os.path.join(H, "scenes.json")))["scenes"]:
        for f in sc["figures"]:
            if f["clips"]: by_q[f["q"]] = [(n, C[i]) for n, i in enumerate(f["clips"]) if i in C]
jobs, seen = [], set()
for q, xs in by_q.items():
    srcs = set(); n = 0
    for rank, c in sorted(xs, key=lambda t: t[0]):
        if n >= PER: break
        if c["id"] in seen or c["sourceId"] in srcs or (c.get("durationSeconds") or 0) < 1: continue
        seen.add(c["id"]); srcs.add(c["sourceId"]); n += 1
        jobs.append({"id": c["id"], "url": c["videoUrl"], "clip": f"odyssey/clips/{c['id']}.mp4", "dur": round(c["durationSeconds"], 3),
                     "t": round(max(0, min(c["durationSeconds"] - .2, (c.get("matchTimestampSeconds") or c["startSeconds"]) - c["startSeconds"])), 3), "targets": [q]})
jobs = jobs[:LIMIT]
def get(j):
    p = os.path.join(LAB, j["clip"])
    if os.path.exists(p) and os.path.getsize(p) > 5000: return True
    try:
        with urllib.request.urlopen(urllib.request.Request(j["url"], headers={"user-agent": "cineosis-44-research"}), timeout=120) as r: open(p, "wb").write(r.read())
        return True
    except Exception: return False
with cf.ThreadPoolExecutor(6) as ex: ok = list(ex.map(get, jobs))
jobs = [j for j, k in zip(jobs, ok) if k]
json.dump(jobs, open(os.path.join(H, "cache", "seg-jobs.json"), "w"), indent=0)
print(len(jobs), "figure clips fetched from", len(by_q), "figure asks")
