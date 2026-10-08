"""The cartoons, read by CLIP (the archive's model): does each shot read as its own part of the world (its key drawings against every
world's sentences), and which archival shot does its last drawing rhyme with: the match cut out of the cartoon into the archive.
Adds "clip" and "match" to slopfeeder/cartoon/cartoon.json.   usage: .venv/bin/python slopfeeder/cartoon_clip.py"""
import json, os, glob
import numpy as np, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); CJ = os.path.join(D, "cartoon", "cartoon.json")
CA = json.load(open(CJ)); PO = json.load(open(os.path.join(D, "pools.json"))); WORLDS = PO["worlds"]
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ci(ps):
    with torch.no_grad(): e = m.encode_image(torch.stack([prep(Image.open(p).convert("RGB")) for p in ps])).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
# every world's sentences, plus a cartoon frame of mind (the drawings are cartoons: we ask what the cartoon is OF)
names = list(WORLDS); WT = {w: ct([f"a cartoon drawing of {s}" for s in WORLDS[w]]) for w in names}
# the archive, as pools.py sees it
lib = json.load(open(os.path.join(L, "markov", "library.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]
rec, emb = {}, {}
R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"
for s, e in zip(lib["shots"], E1):
    if s["kind"] == "archive" and s["id"] in V: emb[s["id"]] = e; rec[s["id"]] = {"id": s["id"], "title": s.get("title"), "year": s.get("year"), "v": R2 + V[s["id"]][0], "t": R2 + V[s["id"]][0].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg"), "dur": V[s["id"]][1]}
title = {c["id"]: (c["sourceTitle"], c.get("sourceYear")) for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json")))}
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))):
    if i not in emb and i in title and i in V: emb[i] = e; rec[i] = {"id": i, "title": title[i][0], "year": title[i][1], "v": R2 + V[i][0], "t": R2 + V[i][0].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg"), "dur": V[i][1]}
F = {c["id"]: c for c in json.load(open(os.path.join(D, "forage.json")))["clips"]}
for i, e in zip(json.load(open(os.path.join(D, "forage-ids.json"))), np.load(os.path.join(D, "forage-emb.npy")).astype(np.float32)):
    if i not in emb and i in F: c = F[i]; emb[i] = e; rec[i] = {"id": i, "title": c["title"], "year": c["year"], "v": c["v"], "t": c["t"], "dur": c["dur"]}
ids = [i for i in rec if (rec[i].get("dur") or 0) >= 2]; A = np.stack([emb[i] for i in ids]); A /= np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
dark = A @ ct(["a completely black dark empty frame", "a completely white blank frame", "a title card with text"]).T; pen = np.clip(dark.max(1) - .2, 0, None)
for w, c in CA.items():
    ks = [os.path.join(D, k) for k in c["keys"]]; K = ci(ks)
    S = np.array([[float((K[j] @ WT[x].T).max()) for x in names] for j in range(len(K))]); mean = S.mean(0); order = np.argsort(-mean)
    c["clip"] = {"own": round(float(mean[names.index(w)]), 3), "rank": int(list(order).index(names.index(w)) + 1), "reads_as": names[int(order[0])],
                 "per_key": [names[int(np.argmax(r))] for r in S]}
    # the match cut: the archive's nearest shot to the last drawing (and to the key drawings), pulled toward this world's own sentences
    last = K[-1] * .7 + ct([WORLDS[w][0]])[0] * .3; last /= np.linalg.norm(last)
    own = np.array([k_ in set(x["id"] for x in PO["pools"][w]) for k_ in ids])          # the match cut lands in this world's own footage
    sims = A @ last - .6 * pen - 2 * (~own); j = int(np.argmax(sims)); c["match"] = {**rec[ids[j]], "s": round(float(sims[j]), 3)}
    rh = []
    for k in K[::max(1, len(K) // 4)][:4]:
        q = k * .7 + ct([WORLDS[w][0]])[0] * .3; q /= np.linalg.norm(q); jj = int(np.argmax(A @ q - .6 * pen - 2 * (~own))); rh.append(rec[ids[jj]])
    c["rhymes"] = rh
    print(f"{w:14s} reads as itself? rank {c['clip']['rank']}/8 (top: {c['clip']['reads_as']})  match cut -> {c['match']['title']}")
json.dump(CA, open(CJ, "w"), indent=1)
