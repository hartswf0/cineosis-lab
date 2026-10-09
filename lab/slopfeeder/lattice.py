"""THE SEA OF TAKES — every alternative of every shot in the story cut, as one lattice (the Found Odyssey's build_cuts.py idea, made visible):
a column per shot in program order (pickups, archive memories, bridges), each column holding the cut's choice plus its alternatives
(pickups: the other pickups nearest in CLIP, same field family first; archive: every shot I looked at for that phrase). For each candidate:
a 32-d PCA of its CLIP vector (the page computes any join live, scored as monte/sim.js scores a cut: a Gaussian of cosine around .72),
'same' (likeness to the shot it would replace), 'sym' (mirror symmetry of edges, wes/score.py's idea, cheap), poison, the playable source.
Writes story-lattice.json (slopfeeder-takes.html).   usage: .venv/bin/python slopfeeder/lattice.py   (after story.py)"""
import json, os, io, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
C = json.load(open(os.path.join(D, "atlas.json")))["cards"]; E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(len(C), -1).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
AI = [i for i, c in enumerate(C) if c["type"] == "ai"]; FA = {c["id"]: c.get("fa") for c in json.load(open(os.path.join(D, "field.json")))["cards"]}
AP = np.load(os.path.join(D, "src", "archpool.npy")).astype(np.float32); APR = json.load(open(os.path.join(D, "src", "archpool.json"))); APX = {r["id"]: i for i, r in enumerate(APR)}
ST = json.load(open(os.path.join(D, "story.json"))); ARC = json.load(open(os.path.join(D, "story-archive.json"))); CANDS = json.load(open(os.path.join(D, "story-archive-cands.json")))
key_of = {r["v"]: k for k, r in ARC.items()}; key_by_title = {r["title"]: k for k, r in ARC.items()}
thumb_url = lambda r: r["v"].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg")
def img(src):
    try:
        if src.startswith("http"): return Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": "cineosis-44-research"}), timeout=20).read()))
        return Image.open(os.path.join(D, src))
    except Exception: return None
def sym(im):   # mirror symmetry of the edges (1 = a perfectly centred, Andersonian frame)
    if im is None: return 0.0
    g = np.asarray(im.convert("L").resize((64, 36)), np.float32); e = np.abs(np.diff(g, axis=1))[:, :62] + np.abs(np.diff(g, axis=0))[:, :62][:35].mean()
    return float(max(0.0, 1 - np.abs(e - e[:, ::-1]).mean() / (e.mean() + 1e-6)))
cols, vecs = [], []
def ai_col(s):
    own = [i for i in AI if C[i]["clip"] == s["clip"]]; me = min(own, key=lambda i: abs((C[i].get("in") or 0) - s["ss"]) if (C[i].get("in") or 0) <= s["ss"] + .1 else 99)
    sim = E[AI] @ E[me]; fam = FA.get(C[me]["id"]); out = [{"kind": "ai", "clip": s["clip"], "ss": s["ss"], "out": round(s["ss"] + s["d"] * s.get("rate", 1) + 3, 2), "thumb": C[me]["thumb"], "same": 1.0, "poison": round(C[me].get("poison") or 0, 2), "_v": E[me]}]
    order = sorted(range(len(AI)), key=lambda j: -(sim[j] + (.08 if fam and FA.get(C[AI[j]]["id"]) == fam else 0)))
    for j in order:
        c = C[AI[j]]
        if AI[j] == me or (c.get("out", 0) - c.get("in", 0)) < 1.2 or sim[j] < .70: continue
        if any(o["clip"] == c["clip"] and abs(o["ss"] - c["in"]) < 1 for o in out): continue
        out.append({"kind": "ai", "clip": c["clip"], "ss": round(c["in"], 2), "out": round(c["out"], 2), "thumb": c["thumb"], "same": round(float(sim[j]), 3), "poison": round(c.get("poison") or 0, 2), "_v": E[AI[j]]})
        if len(out) == 11: break
    return out
def arch_col(k):
    out, base = [], None
    for r in CANDS.get(k, [])[:10]:
        if r["id"] not in APX: continue
        v = AP[APX[r["id"]]]; base = v if base is None else base
        out.append({"kind": "archive", "v": r["v"], "ss": None, "title": r["title"], "year": r.get("year"), "thumb": thumb_url(r), "same": round(float(v @ base), 3), "poison": 0, "_v": v})
    return out
for s in ST["shots"]:
    if s["kind"] == "ai": cols.append({"t": s["t"], "d": s["d"], "act": s["act"], "cap": s.get("cap", ""), "kind": "ai", "poison": s.get("poison", False), "cands": ai_col(s)})
    else:
        k = key_of.get(s["v"]); cols.append({"t": s["t"], "d": s["d"], "act": None, "cap": "", "kind": "memory", "key": k, "cands": arch_col(k) if k else []})
for p in ST["program"]:
    if p["kind"] == "bridge":
        k = key_by_title.get(p["title"]); cols.append({"t": p["t"], "d": p["d"], "act": None, "cap": "", "kind": "bridge", "key": k, "cands": arch_col(k) if k else []})
cols = [c for c in sorted(cols, key=lambda c: c["t"]) if c["cands"]]
# acts for archive columns: the act they sit in
acts = [p for p in ST["program"] if p["kind"] == "act"]
for c in cols:
    if not c["act"]: c["act"] = next((a["roman"] for a in acts if a["t"] - .01 <= c["t"] < a["t"] + a["d"]), next((a["roman"] for a in reversed(acts) if a["t"] <= c["t"]), "I")) + ("·" if c["kind"] == "bridge" else "")
# ---- one shared 32-d space (PCA over every candidate), symmetry from thumbnails
allc = [x for c in cols for x in c["cands"]]; V = np.stack([x["_v"] for x in allc]); V /= np.linalg.norm(V, axis=1, keepdims=True); mu = V.mean(0)
U, S_, Wt = np.linalg.svd(V - mu, full_matrices=False); P = (V - mu) @ Wt[:32].T; P /= np.linalg.norm(P, axis=1, keepdims=True) + 1e-9
with cf.ThreadPoolExecutor(16) as ex: syms = list(ex.map(lambda x: sym(img(x["thumb"])), allc))
for x, p, sy in zip(allc, P, syms): x["e"] = [int(round(v * 127)) for v in p]; x["sym"] = round(sy, 3); del x["_v"]
# the page compares joins in the PCA space: calibrate its cosine to the full CLIP cosine (linear fit) so .72 still means .72
pairs = np.random.default_rng(0).integers(0, len(allc), (4000, 2)); full = (V[pairs[:, 0]] * V[pairs[:, 1]]).sum(1); low = (P[pairs[:, 0]] * P[pairs[:, 1]]).sum(1); a, b = np.polyfit(low, full, 1)
json.dump({"dur": ST["dur"], "video": ST["video"], "program": ST["program"], "cal": [round(float(a), 4), round(float(b), 4)], "cols": cols}, open(os.path.join(D, "story-lattice.json"), "w"), separators=(",", ":"))
print(len(cols), "columns ·", len(allc), "takes ·", f"cal {a:.3f}x+{b:.3f}", "·", os.path.getsize(os.path.join(D, "story-lattice.json")) // 1024, "KB")
