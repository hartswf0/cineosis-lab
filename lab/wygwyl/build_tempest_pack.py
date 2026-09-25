"""Tempest pack: tiny same-origin loops so WAG's WebGL room can show the candidates (the archive sends no CORS).
Per beat: the top 6 ranked candidates (KEEP/MAYBE) and the suite-cut shot → wygwyl/tempest/<id>.mp4 (3 s, 240×180,
silent, faststart) + wygwyl/tempest/pack.json. Local clips are cut from lab/clips; the rest from the archive URL.
    python3 lab/wygwyl/build_tempest_pack.py
"""
import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE); OUT = os.path.join(HERE, "tempest")
D = json.load(open(os.path.join(HERE, "collage-data.json"))); R = json.load(open(os.path.join(HERE, "candidate-ranks.json")))
jobs, pack = {}, {"beats": {}}
for b in D["beats"]:
    rk = [c for c in R["beats"][str(b["id"])]["ranked"] if c["verdict"] != "FLOOR"][:6]
    suite = next((p for p in D["cuts"]["suite"] if p["t0"] <= b["start"] + .05 < p["t1"]), None)
    for c in rk: jobs[c["id"]] = (c["video"], (c.get("in") or 0) + min(1.0, (c.get("dur") or 3) / 3))
    if suite: jobs.setdefault(suite["id"], (suite["video"], suite["in"] + .5))
    pack["beats"][str(b["id"])] = {"cands": [{k: c[k] for k in ("id", "title", "year", "score", "fit", "verdict", "cat", "thumb", "video", "in")} for c in rk],
                                   "suite": {"id": suite["id"], "title": suite["title"], "video": suite["video"], "in": suite["in"], "thumb": suite["thumb"]} if suite else None}
def enc(item):
    i, (url, t) = item; out = os.path.join(OUT, i + ".mp4")
    if os.path.exists(out) and os.path.getsize(out) > 1000: return 1
    src = os.path.join(LAB, "clips", i + ".mp4"); src = src if os.path.exists(src) else url
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t):.2f}", "-i", src, "-t", "3", "-an", "-vf", "scale=240:180:force_original_aspect_ratio=increase,crop=240:180,fps=20",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], capture_output=True)
    return int(r.returncode == 0)
with ThreadPoolExecutor(4) as ex: ok = sum(ex.map(enc, jobs.items()))
have = {f[:-4] for f in os.listdir(OUT) if f.endswith(".mp4")}
pack["files"] = sorted(have)
json.dump(pack, open(os.path.join(OUT, "pack.json"), "w"), separators=(",", ":"))
size = sum(os.path.getsize(os.path.join(OUT, f + ".mp4")) for f in have)
print("clips", len(jobs), "ok", ok, "·", round(size / 1e6, 1), "MB")
