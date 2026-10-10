"""Give each memo line in storyboard.json the archive's answer as the film has it: the clip, from when to when, what is said, the film.
usage: python3 norse/answers.py (after storyboard.py)"""
import json, os
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N)
P = json.load(open(os.path.join(N, "poem.json"))); S = json.load(open(os.path.join(N, "storyboard.json")))
lib = {x["id"]: x for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"]}
n = 0
for B, SB in zip(P["books"], S["books"]):
    for u, l in zip(B["lines"], SB["lines"]):
        fr = (u["modes"].get("spoken") or {}).get("frags") or []
        if fr and fr[0].get("id") in lib: x = fr[0]; s = lib[x["id"]]; l["av"] = {"v": s["video"], "t0": x["t0"], "t1": x["t1"], "s": x["words"], "ti": (s.get("title") or "")[:60], "y": s.get("year")}; n += 1
json.dump(S, open(os.path.join(N, "storyboard.json"), "w"), separators=(",", ":"), ensure_ascii=False); print(n, "memo lines carry their answer")
