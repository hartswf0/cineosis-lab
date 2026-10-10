"""MARKOV SAM · NORSE: each picture's Cineosis sign, by the lab's own affinity method (../affinity.py), so the storyboard can show what kind
of image every shot is (Deamer's 45 signs of Deleuze's cinema, in eight families) and the board can be read as a chain of signs.
  text side   each sign's shot criteria and search queries, read by CLIP (LAION ViT-B/32)
  image side  the editor's own read exemplars of each sign (picks.json), as a prototype
  score       half each, z-scored per sign against the lab's whole corpus (so a sign CLIP likes everywhere does not dominate), softmax
Adds "sg" (top sign, its second, and how sure) to every picture in storyboard.json and wordmap.json, and the sign table to storyboard.json.
NOT a reading: a pointer for where to look.   usage: ../.venv/bin/python norse/signs.py"""
import glob, json, os, re
import numpy as np, torch, open_clip
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N); ROOT = os.path.dirname(L)
FAMILY = {"Perception": "perception", "Affection": "affection", "Impulse": "impulse", "Action": "action", "Attraction": "reflection", "Inversion": "reflection", "Discourse": "reflection", "discourse": "reflection", "relation": "relation", "recollection": "memory", "dream": "memory", "Chronosign": "time", "Noosign": "time", "Hyalosign": "time", "Opsign": "time", "Sonsign": "time", "Lectosigns": "time"}
fam_of = lambda t: next((v for k, v in FAMILY.items() if t.startswith(k)), "time")
TABLE = json.load(open(os.path.join(ROOT, "cineosis-table.json")))["signs"]
g = [s for f in sorted(glob.glob(os.path.join(ROOT, "grounding", "g*.json"))) for s in json.load(open(f))]; picks = json.load(open(os.path.join(ROOT, "picks.json")))
ns = [str(s["n"]) for s in g]; byn = {str(t["n"]): t for t in TABLE}
model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); model.eval(); tok = open_clip.get_tokenizer("ViT-B-32")
Tp = []
with torch.no_grad():
    for s in g:
        texts = [f"a film still: {s['shot_criteria'][:300]}"] + [f"a film still of {q}" for q in s["queries"]]
        t = model.encode_text(tok(texts, context_length=77)); t = t / t.norm(dim=-1, keepdim=True); m = t.mean(0); Tp.append((m / m.norm()).numpy())
Tp = np.stack(Tp)
# the image side and the z-score come from the lab's whole read corpus (cache/emb.npy, LAION)
E = np.load(os.path.join(L, "cache", "emb.npy")).astype(np.float32); lid = json.load(open(os.path.join(L, "cache", "emb_ids.json"))); lrow = {i: k for k, i in enumerate(lid)}
Ip = np.stack([(lambda r: (E[r].sum(0) / np.linalg.norm(E[r].sum(0))) if len(r) else Tp[j])([lrow[c] for c, _ in picks.get(n, []) if c in lrow]) for j, n in enumerate(ns)])
Sl = .5 * (E @ Tp.T) + .5 * (E @ Ip.T); mu, sd = Sl.mean(0), Sl.std(0) + 1e-6
oids = json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))); OE = np.load(os.path.join(L, "odyssey", "cache", "emb-laion.npy")).astype(np.float32); orow = {i: k for k, i in enumerate(oids)}
OE /= np.linalg.norm(OE, axis=1, keepdims=True) + 1e-9
def sign_of(i):
    r = orow.get(i)
    if r is None: return None
    z = ((.5 * (OE[r] @ Tp.T) + .5 * (OE[r] @ Ip.T)) - mu) / sd; p = np.exp(z * 1.2 - (z * 1.2).max()); p /= p.sum(); o = np.argsort(-p)
    return [ns[o[0]], ns[o[1]], round(float(p[o[0]]), 2)]
VID = {x.get("video"): x["id"] for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"] if x.get("video")}
idof = lambda v: VID.get(v)   # the pool keeps each picture's video, which names its shot in the library
SB = json.load(open(os.path.join(N, "storyboard.json"))); hit = 0
for i, m in SB["pics"].items(): m["sg"] = sign_of(i); hit += bool(m["sg"])
WM = json.load(open(os.path.join(N, "wordmap.json"))); whit = 0
for m in WM["pics"]: m["sg"] = sign_of(idof(m.get("video"))); whit += bool(m["sg"])
SB["signs"] = {n: {"s": byn[n]["symbol"], "name": byn[n]["name"], "type": byn[n]["image_type"], "fam": fam_of(byn[n]["image_type"]), "def": byn[n]["definition"][:240]} for n in ns if n in byn}
json.dump(SB, open(os.path.join(N, "storyboard.json"), "w"), separators=(",", ":"), ensure_ascii=False); json.dump(WM, open(os.path.join(N, "wordmap.json"), "w"), separators=(",", ":"), ensure_ascii=False)
import collections; c = collections.Counter(SB["signs"][m["sg"][0]]["fam"] for m in list(SB["pics"].values()) + WM["pics"] if m.get("sg"))
print(f"signs: storyboard {hit}/{len(SB['pics'])} · pool {whit}/{len(WM['pics'])} ·", dict(c.most_common()))
