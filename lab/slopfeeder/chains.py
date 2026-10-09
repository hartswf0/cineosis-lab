"""THE FIELD and its CHAINS (Monte Carlo cinema on the blacktop): what the one surface needs, small enough to load at once.
  field      every card placed by meaning with the AI-vs-archive gap taken out (UMAP), so pickups sit among the archive shots they
             are about instead of on a continent of their own
  families   near-identical AI shots (CLIP > .85) are one family: one card stands for it (the least poisoned), the rest stack behind
  edges      for every card its strongest next shots by four lenses: MEANING (gap removed), FRAME (composition), TWIN (across the AI/archive
             divide, meaning and frame together) and COLOUR; strengths z-scored within each lens, 0..1
  decisions  how many distinct strong next shots a card leaves (strength > .6 on any lens): an open shot or a dead end
  chain      Monte Carlo: 96 random walks of four cuts from the card, each step drawn by edge strength (no family twice); a walk scores its
             mean strength plus a bonus for changing lens (rhyme by meaning, then by frame...); the card's chain value is the mean of its
             best third of walks, ranked across the corpus 0..1. High = it opens strong chains.
Writes field.json (compact, everything the page needs) and keeps atlas.json for the pipeline.   usage: .venv/bin/python slopfeeder/chains.py"""
import json, os
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
AT = json.load(open(os.path.join(D, "atlas.json"))); C = AT["cards"]; n = len(C)
E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(-1, 512).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True)
K = np.fromfile(os.path.join(D, "comp-emb.bin"), np.int8).reshape(n, -1).astype(np.float32); K /= np.linalg.norm(K, axis=1, keepdims=True) + 1e-9
typ = np.array([c["type"] for c in C]); Ec = E.copy()
for t in set(typ): Ec[typ == t] -= E[typ == t].mean(0)
Ec /= np.linalg.norm(Ec, axis=1, keepdims=True) + 1e-9
def colv(c):
    l = c.get("colour") or {}; ch = l.get("chars", {}); h = np.radians(l.get("hue", 0)); s = l.get("sat", 0); w = l.get("weight", [.5, .5])
    return np.array([np.cos(h) * s * 2, np.sin(h) * s * 2, l.get("lum", 0) - .45, 1 if l.get("bw") else 0, ch.get("purple", 0) * 8, ch.get("orange", 0) * 8, ch.get("yellow", 0) * 8, w[0] - .5, w[1] - .5, l.get("horizon", .5) - .5, c.get("pails", 0)])
V = np.stack([colv(c) for c in C]); V -= V.mean(0); V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-9
# ---- families
ai = [i for i in range(n) if typ[i] == "ai"]; fam = np.arange(n); fams = []
for i in sorted(ai, key=lambda i: C[i].get("poison", 0)):
    for f in fams:
        if E[i] @ E[f[0]] > .85: f.append(i); fam[i] = f[0]; break
    else: fams.append([i])
size = {f[0]: len(f) for f in fams}
print(len(ai), "AI shots ->", len(fams), "families", flush=True)
# ---- the field
import umap
xy = umap.UMAP(n_neighbors=24, min_dist=.35, spread=1.6, metric="cosine", random_state=11).fit_transform(Ec); xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0) + 1e-9)
# ---- edges per lens
def top(S, k=6):
    S = S.copy(); np.fill_diagonal(S, -9)
    S[fam[:, None] == fam[None, :]] = -9                           # never to its own family
    z = (S - S[S > -9].mean()) / (S[S > -9].std() + 1e-9); idx = np.argsort(-S, axis=1)[:, :k]
    st = np.clip((np.take_along_axis(z, idx, 1) - 1) / 2.5, 0, 1); return idx, st
lenses = {"meaning": Ec @ Ec.T, "frame": K @ K.T, "colour": V @ V.T}
tw = .5 * (Ec @ Ec.T) / .3 + .5 * (K @ K.T) / .3; cross = typ[:, None] != typ[None, :]; tw[~cross] = -9; lenses["twin"] = tw
EDG = {k: top(S) for k, S in lenses.items()}
names = list(EDG)
# ---- decisions and Monte Carlo chains
dec = np.zeros(n, int)
for i in range(n): dec[i] = len({int(j) for k in names for j, s in zip(*[x[i] for x in EDG[k]]) if s > .6})
rng = np.random.default_rng(3); val = np.zeros(n)
for i in range(n):
    scores = []
    for _ in range(96):
        cur, seen, tot, last, bonus = i, {fam[i]}, 0.0, None, 0.0
        for step in range(4):
            opts = [(int(j), float(s), k) for k in names for j, s in zip(*[x[cur] for x in EDG[k]]) if s > 0 and fam[j] not in seen]
            if not opts: tot -= .5; break
            w = np.array([o[1] for o in opts]) ** 2 + 1e-6; j, s, k = opts[rng.choice(len(opts), p=w / w.sum())]
            tot += s; bonus += .15 if last and k != last else 0; last = k; seen.add(fam[j]); cur = j
        scores.append(tot / 4 + bonus / 4)
    sc = np.sort(scores)[::-1]; val[i] = sc[:32].mean()
rank = val.argsort().argsort() / (n - 1)
# ---- the compact field
def keep(c, i):
    o = {"id": c["id"], "t": c["type"], "w": c["world"], "ti": (c.get("title") or "")[:60], "xy": [round(float(xy[i, 0]), 4), round(float(xy[i, 1]), 4)],
         "th": c["thumb"], "m": c["media"], "sg": [s[0] for s in c.get("signs", [])], "sp": [s[1] for s in c.get("signs", [])],
         "pl": c.get("pails", 0), "ca": c.get("cartoon", 0), "aff": c.get("aff", {}), "mc": round(float(rank[i]), 3), "dc": int(dec[i]),
         "col": [(c.get("colour") or {}).get(k) for k in ("hue", "sat", "lum")] + [1 if (c.get("colour") or {}).get("bw") else 0],
         "ch": (c.get("colour") or {}).get("chars", {})}
    if c["type"] == "ai":
        o.update({"src": c["src"], "in": c["in"], "out": c["out"], "po": c.get("poison", 0), "why": c.get("why", []), "pd": c.get("pound", []), "so": c.get("sound", []), "wd": c.get("words", []),
                  "tp": c.get("tempo"), "fa": C[fam[i]]["id"], "fn": size.get(int(fam[i]), 1)})
    if c.get("year"): o["y"] = c["year"]
    o["cl"] = c.get("cluster")
    if c.get("dur"): o["du"] = round(float(c["dur"]), 2)
    return o
out = {"cards": [keep(c, i) for i, c in enumerate(C)], "lenses": names,
       "edges": {k: {"to": EDG[k][0].tolist(), "s": np.round(EDG[k][1], 2).tolist()} for k in names},
       "signs": AT["signs"], "chapters": AT["chapters"], "songs": AT["songs"], "clusters": AT["clusters"], "scale": AT["scale"], "comp_scale": AT["comp_scale"], "comp_dim": AT["comp_dim"]}
json.dump(out, open(os.path.join(D, "field.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("field.json:", os.path.getsize(os.path.join(D, "field.json")) // 1024, "KB · decisions median", int(np.median(dec)), "· dead ends", int((dec == 0).sum()),
      "· strongest openers:", [C[i]["title"][:30] for i in np.argsort(-val)[:6]], flush=True)
