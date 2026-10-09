"""The takes: for every pickup shot in the story cut, the other generations of (more or less) the same shot — same field family (CLIP > .85)
or the nearest pickups in CLIP above .84 — so slopfeeder-takes.html can let the viewer choose which one to watch. Adds "alts" to story.json.
usage: python3 slopfeeder/takes.py   (after story.py)"""
import json, os
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(D, "atlas.json")))["cards"]; E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(len(C), -1).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
IX = {c["id"]: i for i, c in enumerate(C)}; AI = [i for i, c in enumerate(C) if c["type"] == "ai"]
FA = {c["id"]: c.get("fa") for c in json.load(open(os.path.join(D, "field.json")))["cards"]}
ST = json.load(open(os.path.join(D, "story.json"))); n_alt = 0
for s in ST["shots"]:
    if s["kind"] != "ai": continue
    own = [i for i in AI if C[i]["clip"] == s["clip"]]; me = min(own, key=lambda i: abs((C[i].get("in") or 0) - s["ss"]) if (C[i].get("in") or 0) <= s["ss"] + .1 else 99)
    sim = E[AI] @ E[me]; fam = FA.get(C[me]["id"]); alts = []
    for j in np.argsort(-sim):
        i = AI[j]; c = C[i]
        if i == me or (c.get("out", 0) - c.get("in", 0)) < 1.2: continue
        if not ((fam and FA.get(c["id"]) == fam) or sim[j] > .84): continue
        if any(a["clip"] == c["clip"] and abs(a["ss"] - c["in"]) < 1 for a in alts): continue
        alts.append({"clip": c["clip"], "ss": round(c["in"], 2), "out": round(c["out"], 2), "thumb": c["thumb"], "sim": round(float(sim[j]), 3)})
        if len(alts) == 6: break
    s["thumb"] = C[me]["thumb"]; s["alts"] = alts; n_alt += bool(alts)
json.dump(ST, open(os.path.join(D, "story.json"), "w"), indent=0)
print(sum(s["kind"] == "ai" for s in ST["shots"]), "pickup shots ·", n_alt, "with other takes ·", sum(len(s.get("alts", [])) for s in ST["shots"]), "takes")
