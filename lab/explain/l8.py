"""LESSON 8 · CHOOSING. Replays CUTBASTARD's choosing rule (cutbastard/plan.py) at EVERY moment of three takes (suite, cineosis, drift;
scenes walks whole films and has no choice to replay), with the take's own earlier choices as the state, and records:
  per moment   the winner's total, the best allowed rival, the margin; whether the CLIP match alone would have picked the same shot;
               which adjustment (pace, colour/black-and-white, signs, a reviewed pick, following the last shot, reuse) the margin hangs on
  P020         the full race for one line in all three takes: top candidates, every adjustment, bans and their reasons
  pool         every shot the rule could use, placed by its CLIP match to the Suite's description at P020 (to show how tightly packed they are)
  strip        the Suite's winner at P020: the three frames CLIP judged (25/50/75 % of the clip) against the window the film plays
Writes explain/lesson/l8.json.   usage: lab/.venv/bin/python lab/explain/l8.py"""
import json, os, importlib.util, subprocess
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
spec = importlib.util.spec_from_file_location("plan", os.path.join(LAB, "cutbastard", "plan.py")); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
ORDER = ["suite", "scenes", "cineosis", "drift"]; FOCUS = 20
BAN = {"all-my-babies", "jfk-exhibit-3-reconstruction-film"}
corpus, E, ids, ana, aff = P.load_pool(); row = {i: k for k, i in enumerate(ids)}
patches = json.load(open(os.path.join(LAB, "cutbastard", "patches.json")))["patches"]
plans = {s: json.load(open(os.path.join(P.CUTS, s, "plan.json")))["patches"] for s in ORDER}
published = {s: [x["clip"]["id"] for x in plans[s]] for s in ORDER}
W = {i: P.watched(i) for i in corpus}; W = {i: w for i, w in W.items() if w and not w.get("bad") and w["dead"] < .15 and w["card"] < .35}
pool = [i for i in W if i in row]; pidx = {i: j for j, i in enumerate(pool)}
Epool = np.stack([np.array(W[i]["emb"]) for i in pool]); motion = np.array([W[i]["motion"] for i in pool]); mz = (motion - motion.mean()) / (motion.std() + 1e-9)
bw = np.array([bool((ana.get(i) or {}).get("hue") is None) for i in pool]); src = [corpus[i].get("sourceSlug") for i in pool]
cat = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Catalogue.json"))); reviewed, notes = {}, {}
for b in cat["beats"]:
    for c in b["candidates"]:
        if c.get("grade") and c["grade"] not in ("U", "X", "R"): reviewed[(b["id"], c["id"])] = 1.0
        notes[(b["id"], c["id"])] = {"grade": c.get("grade"), "observed": c.get("observed"), "use": c.get("use"), "query": c.get("query")}
q = json.load(open(os.path.join(LAB, "cutbastard", "queries.json"))); qc = {c["i"]: c for c in q["cues"]}; mood = {c["n"]: c["mood"] for c in q["chapters"]}; beats = {b["id"]: b for b in cat["beats"]}
def intent_text(p, s):
    c = qc.get(p["cue"]) if p["cue"] is not None else None; b = beats.get(p["beat"]) or {}
    if s == "suite": parts = [b.get("title"), b.get("query"), c and c["literal"], c and c["place"]]
    elif s == "cineosis": parts = [c and c["literal"], b.get("title")]
    else: ms = mood.get(p["chapter"], []); parts = [ms[(p["k"] + p["segment"]) % len(ms)] if ms else None, c and c["oblique"]]
    return [x for x in parts if x] or [p["film"].lower()]
def card(i): c = corpus[i]; return {"id": i, "title": c.get("sourceTitle"), "year": c.get("sourceYear"), "thumb": f"thumbs/{i}.jpg", "clip": f"clips/{i}.mp4",
                                     "hide": c.get("sourceSlug") in BAN, "bw": bool((ana.get(i) or {}).get("hue") is None)}
ADJ = ["pace", "stock", "sign", "reviewed", "drift", "reuse"]
out = {"pool": len(pool), "takes": {}, "focus": FOCUS}
for k, s in enumerate(ORDER):
    if s == "scenes": continue
    I = P.intents(patches, s); sim = I @ Epool.T
    used_before = set().union(*[set(published[o]) for o in ORDER[:k]])
    used, last_src, prev_e, prev_bw, rows = set(), [], None, None, []
    for pi, p in enumerate(patches):
        dur = p["t1"] - p["t0"]; e = p["energy"]; pub = published[s][pi]
        base = sim[pi].copy(); z = 0 * base
        A = {"pace": -.06 * np.abs(mz / 3 - (e - .5)),
             "drift": (.35 * (Epool @ prev_e) - .1) if (s == "drift" and prev_e is not None) else z,
             "stock": -.03 * (bw != prev_bw) if prev_bw is not None else z,
             "sign": np.array([np.mean([((aff.get(i) or {}).get("all") or {}).get(str(c), 0) for c in p["codes"]]) if p["codes"] else 0 for i in pool]) / 100 * 1.5 if s == "cineosis" else z,
             "reviewed": np.array([.04 * reviewed.get((p["beat"], i), 0) for i in pool]) if (s == "suite" and p["beat"]) else z,
             "reuse": np.array([-.05 if i in used_before else 0 for i in pool])}
        sc = base + sum(A.values())
        why = {}
        for j, i in enumerate(pool):
            if i in used: why[j] = "already used in this take"
            elif W[i]["dur"] < dur: why[j] = "too short for the moment"
            elif src[j] in last_src[-3:]: why[j] = "same film within the last three shots"
        ok = sc.copy(); bad = list(why); ok[bad] = -9; order = np.argsort(-ok); j1, j2 = int(order[0]), int(order[1])
        ob = base.copy(); ob[bad] = -9; jb = int(np.argmax(ob))
        diff = {a: float(A[a][j1] - A[a][j2]) for a in ADJ}
        r = {"i": pi, "id": p["id"], "t0": p["t0"], "win": pool[j1], "agree": pool[j1] == pub, "margin": round(float(ok[j1] - ok[j2]), 4),
             "base_same": jb == j1, "base_gap": round(float(base[j1] - base[j2]), 4), "hinge": max(diff, key=lambda a: abs(diff[a])), "hinge_v": round(max(diff.values(), key=abs), 4),
             "spread40": round(float(np.sort(ob)[-1] - np.sort(ob)[-40]), 4), "banned_above": int(sum(1 for jj in np.argsort(-sc)[:np.where(np.argsort(-sc) == j1)[0][0]] if jj in why))}
        if pi == FOCUS:
            top = list(np.argsort(-sc)[:40]); cands = []
            for jj in top:
                cands.append({**card(pool[jj]), "base": round(float(base[jj]), 4), **{a: round(float(A[a][jj]), 4) for a in ADJ}, "total": round(float(sc[jj]), 4), "out": why.get(jj),
                              "won": jj == j1, "note": notes.get((p["beat"], pool[jj])) if s == "suite" else None, "motion": round(float(motion[jj]), 4)})
                if len([c for c in cands if not c["out"]]) >= 7 and any(c["won"] for c in cands): break
            r["race"] = {"intent": intent_text(p, s), "line": p["line"], "t0": p["t0"], "t1": p["t1"], "energy": e, "codes": p["codes"], "cands": cands,
                         "prev": card(published[s][pi - 1]) if pi else None}
            if s == "suite":
                hist, edges = np.histogram(base, bins=60); out["pool_hist"] = {"counts": hist.tolist(), "lo": round(float(edges[0]), 4), "hi": round(float(edges[-1]), 4)}
                out["pool_top"] = [round(float(x), 4) for x in np.sort(base)[::-1][:200]]
        rows.append(r)
        jp = pidx.get(pub)
        if jp is not None: used.add(pub); last_src.append(src[jp]); prev_e, prev_bw = Epool[jp], bw[jp]
    m = np.array([r["margin"] for r in rows])
    out["takes"][s] = {"rows": rows, "agree": sum(r["agree"] for r in rows), "n": len(rows), "median_margin": round(float(np.median(m)), 4),
                       "under_005": int((m < .005).sum()), "under_001": int((m < .001).sum()), "base_same": sum(r["base_same"] for r in rows),
                       "hinges": {a: sum(1 for r in rows if not r["base_same"] and r["hinge"] == a) for a in ADJ}}
    print(s, "agree", out["takes"][s]["agree"], "/", len(rows), "median margin", out["takes"][s]["median_margin"], "<.005:", out["takes"][s]["under_005"], "<.001:", out["takes"][s]["under_001"],
          "CLIP alone same:", out["takes"][s]["base_same"], "hinges", out["takes"][s]["hinges"], "spread40 median", float(np.median([r["spread40"] for r in rows])))
# the Suite's winner at P020: what CLIP judged vs what the film plays
sp = plans["suite"][FOCUS]["clip"]; w = W.get(sp["id"]) or P.watched(sp["id"]); d = w["dur"]
out["strip"] = {"id": sp["id"], "title": sp["title"], "dur": d, "judged": [round(d * f, 2) for f in (.25, .5, .75)], "in": sp["in"], "out": sp["out"], "clip": sp["clip"]}
SD = os.path.join(H, "lesson", "l8"); os.makedirs(SD, exist_ok=True)
for k2, t in enumerate([round(d * x / 11, 2) for x in range(12)]):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", os.path.join(LAB, sp["clip"]), "-frames:v", "1", "-vf", "scale=320:-2", os.path.join(SD, f"s{k2:02d}.jpg")])
out["strip"]["frames"] = [{"t": round(d * x / 11, 2), "src": f"explain/lesson/l8/s{x:02d}.jpg"} for x in range(12)]
json.dump(out, open(os.path.join(H, "lesson", "l8.json"), "w"), ensure_ascii=False, separators=(",", ":"), default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("pool", len(pool), "strip", out["strip"]["judged"], out["strip"]["in"], out["strip"]["out"])
for s in ("suite", "cineosis", "drift"):
    rr = out["takes"][s]["rows"][FOCUS]; print(s, [(c["title"][:20], c["base"], c["total"], c["out"]) for c in rr["race"]["cands"][:6]], rr["margin"], rr["hinge"])
