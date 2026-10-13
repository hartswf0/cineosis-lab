"""WHY THAT SHOT: replay CUTBASTARD's choosing rule (cutbastard/plan.py, plan()) for the four takes of WYGWYL, exactly, and at a few
moments record every candidate the rule weighed: its CLIP match to the take's own description, each adjustment the rule made
(pacing, keeping black-and-white or colour, signs, reviewed picks, following the last shot, a penalty for clips an earlier take used),
and why the excluded ones were excluded (already used, same film within three shots, too short). Checks that the replay picks
the shot the published take picked. Earlier takes' choices are the ones the rule saw (run order: suite, scenes, cineosis, drift).
Writes explain/ep/ep5_why.json.   usage: lab/.venv/bin/python lab/explain/ep5_replay.py"""
import json, os, sys, importlib.util
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
spec = importlib.util.spec_from_file_location("plan", os.path.join(LAB, "cutbastard", "plan.py")); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
AT = [20, 61, 120]
ORDER = ["suite", "scenes", "cineosis", "drift"]
corpus, E, ids, ana, aff = P.load_pool(); row = {i: k for k, i in enumerate(ids)}
patches = json.load(open(os.path.join(LAB, "cutbastard", "patches.json")))["patches"]
published = {s: [x["clip"]["id"] for x in json.load(open(os.path.join(P.CUTS, s, "plan.json")))["patches"]] for s in ORDER}
W = {i: P.watched(i) for i in corpus}; W = {i: w for i, w in W.items() if w and not w.get("bad") and w["dead"] < .15 and w["card"] < .35}
pool = [i for i in W if i in row]; pidx = {i: j for j, i in enumerate(pool)}
Epool = np.stack([np.array(W[i]["emb"]) for i in pool]); motion = np.array([W[i]["motion"] for i in pool]); mz = (motion - motion.mean()) / (motion.std() + 1e-9)
bw = np.array([bool((ana.get(i) or {}).get("hue") is None) for i in pool]); src = [corpus[i].get("sourceSlug") for i in pool]
def card(i): c = corpus[i]; return {"id": i, "title": c.get("sourceTitle"), "year": c.get("sourceYear"), "thumb": f"thumbs/{i}.jpg"}
cat = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Catalogue.json"))); reviewed = {}
for b in cat["beats"]:
    for c in b["candidates"]:
        if c.get("grade") and c["grade"] not in ("U", "X", "R"): reviewed[(b["id"], c["id"])] = 1.0
q = json.load(open(os.path.join(LAB, "cutbastard", "queries.json"))); qc = {c["i"]: c for c in q["cues"]}; mood = {c["n"]: c["mood"] for c in q["chapters"]}; beats = {b["id"]: b for b in cat["beats"]}
def intent_text(p, s):
    c = qc.get(p["cue"]) if p["cue"] is not None else None; b = beats.get(p["beat"]) or {}
    if s == "suite": parts = [b.get("title"), b.get("query"), c and c["literal"], c and c["place"]]
    elif s == "scenes": parts = [c and c["literal"], c and c["oblique"], c and c["place"]]
    elif s == "cineosis": parts = [c and c["literal"], b.get("title")]
    else: ms = mood.get(p["chapter"], []); parts = [ms[(p["k"] + p["segment"]) % len(ms)] if ms else None, c and c["oblique"]]
    return [x for x in parts if x] or [p["film"].lower()]
out = {"at": AT, "takes": {}}
for k, s in enumerate(ORDER):
    I = P.intents(patches, s); sim = I @ Epool.T
    used_before = set().union(*[set(published[o]) for o in ORDER[:k]]) if k else set()
    used, last_src, prev_e, prev_bw, rec, match = set(), [], None, None, {}, 0
    for pi, p in enumerate(patches):
        dur = p["t1"] - p["t0"]; e = p["energy"]; pub = published[s][pi]
        if s == "scenes" or pi not in AT:                       # scenes walks whole films; outside the recorded moments follow the published take
            choice = pub
        else:
            base = sim[pi].copy(); pace = -.06 * np.abs(mz / 3 - (e - .5)); drift = (.35 * (Epool @ prev_e) - .1) if (s == "drift" and prev_e is not None) else 0 * base
            stock = -.03 * (bw != prev_bw) if prev_bw is not None else 0 * base
            sign = np.array([np.mean([((aff.get(i) or {}).get("all") or {}).get(str(c), 0) for c in p["codes"]]) if p["codes"] else 0 for i in pool]) / 100 * 1.5 if s == "cineosis" else 0 * base
            rev = np.array([.04 * reviewed.get((p["beat"], i), 0) for i in pool]) if (s == "suite" and p["beat"]) else 0 * base
            reuse = np.array([-.05 if i in used_before else 0 for i in pool]); sc = base + pace + drift + stock + sign + rev + reuse
            why = {}
            for j, i in enumerate(pool):
                if i in used: why[j] = "already used in this take"
                elif W[i]["dur"] < dur: why[j] = "too short for the moment"
                elif src[j] in last_src[-3:]: why[j] = "same film within the last three shots"
            ok = sc.copy(); ok[list(why)] = -9; j = int(np.argmax(ok)); choice = pool[j]
            order = list(np.argsort(-sc)[:40])
            cands = []
            for jj in order:
                cands.append({**card(pool[jj]), "base": round(float(base[jj]), 3), "pace": round(float(pace[jj]), 3), "drift": round(float(drift[jj]), 3), "stock": round(float(stock[jj]), 3),
                              "sign": round(float(sign[jj]), 3), "reviewed": round(float(rev[jj]), 3), "reuse": round(float(reuse[jj]), 3), "total": round(float(sc[jj]), 3), "out": why.get(jj), "won": pool[jj] == choice})
                if len([c for c in cands if not c["out"]]) >= 8 and any(c["won"] for c in cands): break
            rec[pi] = {"intent": intent_text(p, s), "line": p["line"], "t0": p["t0"], "t1": p["t1"], "codes": p["codes"], "energy": p["energy"], "cands": cands, "chose": card(choice), "published": card(pub), "agrees": choice == pub}
            match += choice == pub
        j = pidx[choice]; used.add(choice); last_src.append(src[j]); prev_e, prev_bw = Epool[j], bw[j]
    out["takes"][s] = rec; print(s, "replay agrees with the published take at", match, "of", len(rec) if s != "scenes" else 0)
out["pool"] = len(pool); out["used_before_rule"] = "a clip an earlier take used costs 0.05"
json.dump(out, open(os.path.join(H, "ep", "ep5_why.json"), "w"), ensure_ascii=False, separators=(",", ":"))
for s in ("suite", "cineosis", "drift"):
    r = out["takes"][s][20]; print(s, r["intent"], "->", r["chose"]["title"], "| published", r["published"]["title"], "| top:", [(c["title"][:18], c["total"], c["out"]) for c in r["cands"][:4]])
