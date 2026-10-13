"""SYZYGY, filmed: thirteen lanes on one clock (syzygy/lanes.json), and the moments when lanes chosen by separate rules agree.
At every quarter second, for the nine lanes that hold archive shots (archive, suite, scenes, cineosis, drift, spinecut, forage,
taxonomy, compound): how many carry the same sign, and how many show a shot from the same film. The tide is that count over 24 minutes;
the peaks are the syzygies. Peaks on footage kept out of examples (a birth film, assassination evidence, one children's film) are
listed but not filmed. Writes explain/lesson/syz.json.   usage: python3 lab/explain/lsyz.py"""
import json, os, collections, bisect
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
d = json.load(open(os.path.join(LAB, "syzygy", "lanes.json"))); L = d["lanes"]; META = d["meta"]; SG = d["signs"]
PIC = ["archive", "suite", "scenes", "cineosis", "drift", "spinecut", "forage", "taxonomy", "compound"]
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
starts = {k: [x[0] for x in L[k]] for k in L}
def at(k, t):
    i = bisect.bisect_right(starts[k], t) - 1
    if i < 0: return None
    x = L[k][i]; return x if x[0] <= t < x[1] else None
def film(cid): m = META.get(cid); return m[0] if m else None
words = L["voice"]
def said(t0, t1): return " ".join(w[4] for w in words if w[0] >= t0 - .05 and w[1] <= t1 + .05)
tide, rows = [], []
T = 0.0
while T < d["dur"]:
    items = {k: at(k, T) for k in PIC}; items = {k: v for k, v in items.items() if v}
    sg = collections.Counter(str(v[3]) for v in items.values() if v[3] is not None)
    fm = collections.Counter(film(v[4]) for v in items.values() if film(v[4]))
    s, sn = (sg.most_common(1)[0] if sg else (None, 0)); f, fn = (fm.most_common(1)[0] if fm else (None, 0))
    tide.append([round(T, 2), sn, fn]); rows.append((T, s, sn, f, fn, items)); T += .25
def peaks(key, label):
    out, last = [], -99
    for T, s, sn, f, fn, items in sorted(rows, key=lambda r: -(r[2] if key == "sign" else r[4])):
        n = sn if key == "sign" else fn
        if n < 4: break
        if any(abs(T - p["t"]) < 20 for p in out): continue
        agree = [k for k, v in items.items() if (str(v[3]) == s if key == "sign" else film(v[4]) == f)]
        lanes = [{"lane": k, "id": v[4], "sign": v[3], "film": film(v[4]), "year": (META.get(v[4]) or [None, None])[1], "video": (META.get(v[4]) or [None, None, None])[2],
                  "t0": v[0], "t1": v[1], "agree": k in agree} for k, v in items.items()]
        blocked = any(any(b in (x["film"] or "").lower() for b in BLOCK) for x in lanes)
        a, b = min(x["t0"] for x in lanes if x["agree"]), max(x["t1"] for x in lanes if x["agree"])
        out.append({"kind": key, "t": T, "n": n, "of": len(items), "sign": s if key == "sign" else None, "sign_name": SG.get(s, [None, None])[1] if key == "sign" and s else None,
                    "sign_sym": SG.get(s, [None])[0] if key == "sign" and s else None, "film": f if key == "film" else None, "lanes": lanes, "blocked": blocked, "said": said(T - 3, T + 3)})
        if len(out) >= 12: break
    return out
P = {"sign": peaks("sign", "sign"), "film": peaks("film", "film")}
hist = {k: collections.Counter(r[2 if k == "sign" else 4] for r in rows) for k in ("sign", "film")}
out = {"dur": d["dur"], "order": d["order"], "films": d["films"], "tide": tide, "peaks": P, "hist": {k: dict(v) for k, v in hist.items()}, "routing": d["routing"],
       "audio": "wygwyl/WYGWYL_Suite_Audio.mp3", "lane_counts": {k: len(L[k]) for k in d["order"]}}
json.dump(out, open(os.path.join(H, "lesson", "syz.json"), "w"), ensure_ascii=False, separators=(",", ":"))
n = len(rows); print("samples", n, "sign agreement >=5:", sum(1 for r in rows if r[2] >= 5) / n, ">=7:", sum(1 for r in rows if r[2] >= 7) / n, "| same film >=4:", sum(1 for r in rows if r[4] >= 4) / n)
for k in P:
    for p in P[k][:8]: print(k, round(p["t"]), p["n"], "/", p["of"], p["sign_name"] or p["film"], "BLOCKED" if p["blocked"] else "", "|", p["said"][:70])
# CHANCE: slide each lane along the clock by a random amount (keeping its own order and lengths) and count agreement again.
import random
random.seed(7); dur = d["dur"]; grid = [r[0] for r in rows]
seq = {k: [(str(at(k, T)[3]) if at(k, T) and at(k, T)[3] is not None else None) for T in grid] for k in PIC}
fseq = {k: [(film(at(k, T)[4]) if at(k, T) else None) for T in grid] for k in PIC}
def score(S, sh):
    hi5 = hi7 = 0; mx = 0
    for j in range(len(grid)):
        c = collections.Counter(S[k][(j + sh[k]) % len(grid)] for k in PIC); c.pop(None, None)
        n = max(c.values()) if c else 0; mx = max(mx, n); hi5 += n >= 5; hi7 += n >= 7
    return hi5 / len(grid), hi7 / len(grid), mx
real = score(seq, {k: 0 for k in PIC}); realf = score(fseq, {k: 0 for k in PIC})
trials = [score(seq, {k: random.randrange(len(grid)) for k in PIC}) for _ in range(300)]
ftrials = [score(fseq, {k: random.randrange(len(grid)) for k in PIC}) for _ in range(300)]
import numpy as np
out["chance"] = {"real_sign_ge5": real[0], "real_sign_ge7": real[1], "real_sign_max": real[2],
                 "shuffled_sign_ge5_mean": float(np.mean([t[0] for t in trials])), "shuffled_sign_ge5_p95": float(np.percentile([t[0] for t in trials], 95)),
                 "shuffled_sign_max_ge8": sum(1 for t in trials if t[2] >= 8) / len(trials), "shuffled_sign_max_mean": float(np.mean([t[2] for t in trials])),
                 "real_film_ge4": None, "real_film_max": realf[2], "shuffled_film_max_mean": float(np.mean([t[2] for t in ftrials])), "shuffled_film_max_ge4": sum(1 for t in ftrials if t[2] >= 4) / len(ftrials)}
out["sign_share"] = {k: collections.Counter(s for s in seq[k] if s).most_common(3) for k in PIC}
out["lanes_draw"] = {k: [[round(x[0], 2), round(x[1], 2)] for x in L[k]] for k in d["order"]}
out["signs"] = {k: v[0] for k, v in SG.items()}
pk = P["sign"][0]; out["peak_distinct"] = len({x["id"] for x in pk["lanes"] if x["agree"]})
json.dump(out, open(os.path.join(H, "lesson", "syz.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("chance", out["chance"]); print("distinct shots at the top peak", out["peak_distinct"]); print({k: v[:2] for k, v in out["sign_share"].items()})
