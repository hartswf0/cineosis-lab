"""The rushes for MONTE CARLO PICTURES: everything the production has to work with, and nothing it doesn't.
  shots  every frame a judge looked at (monte/material.json, monte/judge2, monte/judge3), good and bad alike:
         clip path, length, the judge's score and words, what it sees, and tags the production problems deal by
  lines  spoken lines, 1-6 s, with their clip and times (a voice to lay over another film's picture)
  music  the music beds
  funny  lines the comedy judge found funny (for the studio note MAKE IT FUNNIER)
usage: python3 lab/pictures/build.py -> lab/pictures/rushes.json"""
import json, os, re, glob, random
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
J = lambda *p: json.load(open(os.path.join(L, *p)))
M = J("monte", "material.json"); R2 = M.get("r2") or "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"
V = J("aspect", "video.json")
TAGS = {"animal": r"\b(dogs?|pupp(y|ies)|horses?|cats?|cows?|cattle|birds?|animals?|sheep|goats?|pigs?|chickens?|hens?|ducks?|geese|elephants?|monkeys?|mules?|deer|lions?|bears?|pony|ponies|camels?|swans?|pigeons?)\b",
        "close": r"\b(close|close-up|closeup|face|faces|portrait|head)\b", "wide": r"\b(wide|distant|aerial|landscape|panorama|long shot|far)\b",
        "back": r"(from behind|backs?\b|rear view|back to)", "people": r"\b(man|men|woman|women|girl|boy|people|figure|figures|crowd|children|child|worker|workers|dancers?|soldiers?|guards?)\b",
        "train": r"\b(train|locomotive|rail|railway|tram)\b", "car": r"\b(car|cars|truck|automobile|bus)\b", "water": r"\b(water|sea|river|lake|ocean|boat|ship|waves?)\b",
        "empty": r"\b(empty|deserted|vacant)\b", "bw": r"\b(b&w|black and white|monochrome)\b"}
shots = {}
def add(i, why, sees, score, film, year, colour=None):
    if i in shots or i not in V or not why or why == "missing": return
    v, dur = V[i][0], V[i][1]; t = " ".join([why] + list(sees or []))
    tags = [k for k, p in TAGS.items() if re.search(p, t, re.I)]
    if colour is not None and colour < .15 and "bw" not in tags: tags.append("bw")
    shots[i] = {"v": v, "d": round(dur or 4, 1), "w": why, "s": list(sees or [])[:4], "sc": score, "f": film or "", "y": int(year) if str(year or "").isdigit() else None, "t": tags}
for s in M["shots"]:
    if not s["title"]: add(s["i"], s.get("why"), [], s["score"], s["film"], s.get("year"), s.get("colour"))
for d in ("judge3", "judge2"):
    pool = {p["n"]: p for p in J("monte", d, "pool.json")}
    for f in sorted(glob.glob(os.path.join(L, "monte", d, "verdicts_*.json"))):
        for v in json.load(open(f)):
            p = pool.get(v["n"])
            if p and not v.get("card"):
                if p["id"] in shots and v.get("sees"): shots[p["id"]]["s"] = v["sees"][:4]
                add(p["id"], v.get("why"), v.get("sees"), v["score"], p.get("film"), p.get("year"))
random.seed(5)
lines = [{"v": V[l["i"]][0], "t0": l["t0"], "t1": l["t1"], "x": l["text"], "f": l.get("film") or ""} for l in M["lines"] if l["i"] in V and 1 <= l["t1"] - l["t0"] <= 6 and 2 <= len(l["text"].split()) <= 16]
lines = random.sample(lines, min(700, len(lines)))
music = [{"v": V[m["i"]][0], "f": m.get("film") or "", "d": round(V[m["i"]][1] or 20, 1)} for m in M["music"] if m["i"] in V]
funny = []
for si, j, f in J("monte", "comic-jokes.json"):
    l = M["lines"][j]
    if f >= 7 and l["i"] in V: funny.append({"v": V[l["i"]][0], "t0": l["t0"], "t1": l["t1"], "x": l["text"], "f": l.get("film") or ""})
P = []   # clip paths are folder + /clips/ + id + .mp4: keep each folder once
def pack(x):
    m = re.fullmatch(r"(.+)/clips/([^/]+)\.mp4", x["v"])
    if m:
        if m.group(1) not in P: P.append(m.group(1))
        x["v"] = [P.index(m.group(1)), m.group(2)]
    return x
shots = {k: pack(v) for k, v in shots.items()}; lines = [pack(x) for x in lines]; music = [pack(x) for x in music]; funny = [pack(x) for x in funny]
out = {"r2": R2, "P": P, "shots": list(shots.values()), "lines": lines, "music": music, "funny": funny}
json.dump(out, open(os.path.join(D, "rushes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
from collections import Counter
print({k: len(v) for k, v in out.items() if isinstance(v, list)}, dict(Counter(t for s in shots.values() for t in s["t"])), round(os.path.getsize(os.path.join(D, "rushes.json")) / 1e3), "KB")
