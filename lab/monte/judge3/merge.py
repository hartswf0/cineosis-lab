"""Fold the strict judge's verdicts (monte/judge3/verdicts_*.json, on the sheets of monte/judge3/sheets) into the Monte Carlo cinema's
material: every frame scored 5 or more becomes a shot (or, if it is mainly lettering with text, a card), with its CLIP image embedding
from the archive's library, its colour from its tile, and what the judge saw in it. Cards come in with no CLIP text embedding (the
story lexicon, monte/story.json, does that work) and the average card mood.   usage: python3 monte/judge3/merge.py"""
import json, os, base64, glob
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(os.path.dirname(D))
M = json.load(open(os.path.join(L, "monte", "material.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
LB = json.load(open(os.path.join(L, "markov", "library.json"))); E = np.fromfile(os.path.join(L, "markov", "emb.bin"), np.int8).reshape(-1, 512).astype(np.float32) * LB["scale"]
idx = {s["id"]: k for k, s in enumerate(LB["shots"])}
P = {p["n"]: p for p in json.load(open(os.path.join(D, "pool.json")))}
VV = [v for f in sorted(glob.glob(os.path.join(D, "verdicts_*.json"))) for v in json.load(open(f))]
def dec(b, n): a = np.frombuffer(base64.b64decode(b), np.int8).reshape(n, -1).astype(np.float32); return a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
q8 = lambda A: base64.b64encode(np.clip(np.round(A / (np.abs(A).max() / 127)), -127, 127).astype(np.int8).tobytes()).decode()
TW, TH, C, PER = 320, 240, 6, 30; sheets = {}
def colour(n):   # the share of saturated pixels in the frame's tile, as pack.py measures it from a thumbnail
    s = (n - 1) // PER + 1; j = (n - 1) % PER
    if s not in sheets: sheets[s] = Image.open(os.path.join(D, "sheets", f"sheet_{s:02d}.jpg")).convert("HSV")
    x, y = (j % C) * TW, (j // C) * TH; t = sheets[s].crop((x + 2, y + 40, x + TW - 2, y + TH - 2)).resize((32, 24))
    return float((np.asarray(t, np.float32)[..., 1] > 40).mean())
SE = dec(M["shotEmb"], len(M["shots"])); CT = dec(M["cardText"], len(M["cards"])); have = {s["i"] for s in M["shots"]}
mood0 = np.mean(np.array(M["cardMood"]), 0).round(3).tolist(); newSE, newCT, added = [], [], 0
for v in VV:
    p = P[v["n"]]; i = p["id"]; card = bool(v.get("card")); text = (v.get("text") or "").strip()
    if v["score"] < 5 or i in have or i not in V or i not in idx or (card and not text): continue
    M["shots"].append({"i": i, "film": p.get("film"), "year": p.get("year"), "score": v["score"], "role": "title" if card else v.get("role", "other"), "title": card,
                       "text": text if card else "", "why": v.get("why"), "sees": v.get("sees") or [], "colour": round(colour(v["n"]), 2), "v": V[i][0], "dur": None, "judge": "monte/judge3"})
    k = len(M["shots"]) - 1; have.add(i); e = E[idx[i]]; newSE.append(e / np.linalg.norm(e)); added += 1
    if card: M["cards"].append(k); newCT.append(np.zeros(512, np.float32)); M["cardMood"].append(mood0)
M["shotEmb"] = q8(np.vstack([SE] + ([np.array(newSE)] if newSE else []))); M["cardText"] = q8(np.vstack([CT] + ([np.array(newCT)] if newCT else [])))
M["lexicon"] = json.load(open(os.path.join(L, "monte", "story.json")))
json.dump(M, open(os.path.join(L, "monte", "material.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("added", added, "· shots", len(M["shots"]), "· cards", len(M["cards"]), "· lexicon", len(M["lexicon"]))
