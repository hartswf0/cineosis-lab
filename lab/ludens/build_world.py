"""LUDENS for any world: the ball games played over any of the lab's films, not only Slopfeeder's field.
A world is a pool of archive shots with chapters (the film's parts) and holes (its story beats, in order, each with a caption).
For each shot, as build.py does for Slopfeeder:
  e      a 32-d PCA of its CLIP vector (openai ViT-B/32, the lab's cache), calibrated back to full cosine, so the games score cuts
  x, y   its place in the field: UMAP of CLIP, so like sits near like
  f      its framing: where the weight of the frame sits (a 4x4 grid of light from its still, centred), as a calibrated 16-d PCA;
         fx, fy its 2-d map
  col    its colour (hue, saturation, lightness, black-and-white) from its still
Worlds: republic (the episodes' places, narration pictures, citizens, cast clips and archive voices; holes are each narration's
first picture), odyssey (the found Odyssey's pictures; holes are each scene's first), norse (the storyboard's grounds; holes are
each memo line), signs (the lab's read shots across the eight families; holes are each sign's exemplar).
Writes ludens/corpus-<world>.json.   usage: .venv/bin/python ludens/build_world.py republic|odyssey|norse|signs"""
import io, json, os, re, sys, glob, colorsys, urllib.request, concurrent.futures as cf, collections
import numpy as np
from PIL import Image
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(L)
WORLD = sys.argv[1]; MAX = 1400
lib = {x["id"]: x for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"]}
ids = json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))); EM = np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy")).astype(np.float32)
EMB = dict(zip(ids, EM))
RC = os.path.join(L, "republic", "cache")
if os.path.exists(os.path.join(RC, "emb-ids.json")):
    EMB.update(zip(json.load(open(os.path.join(RC, "emb-ids.json"))), np.load(os.path.join(RC, "emb-openai.npy")).astype(np.float32)))
    RCL = json.load(open(os.path.join(RC, "clips.json")))
else: RCL = {}
VID = {}
for i, s in lib.items():
    if s.get("video"): VID[s["video"]] = i
for i, c in RCL.items(): VID[c["video"]] = i
def info(i):
    s = lib.get(i) or RCL.get(i) or {}
    t = float(s.get("in") or 0); st = s.get("st")
    if i in RCL: t = max(0.0, float(s.get("in") or 0) - float(s.get("st") or 0))
    return {"video": s.get("video"), "title": (s.get("title") or "")[:60], "year": s.get("year"), "dur": float(s.get("dur") or 6), "t": t}
def still(v):
    return re.sub(r"/clips/([^/]+)\.mp4$", r"/thumbnails/\1.jpg", v) if v and re.search(r"/clips/[^/]+\.mp4$", v) else None
shots, chapters, holes = collections.OrderedDict(), [], []
def add(i, ch, w, at=None):
    if i not in EMB or i in shots: return i in shots
    x = info(i)
    if not x["video"]: return False
    shots[i] = dict(x, ch=ch, w=w, at=at if at is not None else x["t"]); return True
ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV".split()
if WORLD == "republic":
    S = json.load(open(os.path.join(L, "republic", "script.json")))["episodes"]; A = json.load(open(os.path.join(L, "republic", "archive.json")))
    P = json.load(open(os.path.join(L, "republic", "planes.json"))); EP = {}
    for f in ("planes-eps.json", "planes-eps2.json"): EP.update(json.load(open(os.path.join(L, "republic", f)))["episodes"])
    for n, e in enumerate(S, 1):
        key = str(n); chapters.append([key, ROMAN[n - 1], e["name"].title()[:28]])
        cut = os.path.join(L, "republic", "pilot", f"ep{n:02d}.picked.json")
        if os.path.exists(cut):
            for b in json.load(open(cut))["beats"]:
                if b["k"] == "narr":
                    first = True
                    for s in b.get("shots", []):
                        i = VID.get(s["v"])
                        if i and add(i, key, "NARRATION", s.get("in")) and first: holes.append({"id": i, "act": key, "cap": b["text"][:90]}); first = False
                elif b["k"] == "chorus" and VID.get(b.get("v")): add(VID[b["v"]], key, "CITIZENS", b.get("in"))
        for p in EP.get(e["id"], {}).get("places", []):
            for a in p["alts"]: add(a["id"], key, "PLACES", a.get("t"))
        for s in A.get(e["id"], {}).get("segs", []):
            if s["k"] == "line" and s.get("a") and VID.get(s["a"]["v"]): add(VID[s["a"]["v"]], key, "VOICES", s["a"]["in"])
    for name, fs in P["cast"].items():
        for f in fs[:1]:
            if f.get("id"): add(f["id"], "1", "CAST", f.get("t"))
elif WORLD == "odyssey":
    SC = json.load(open(os.path.join(L, "odyssey", "scenes.json")))["scenes"]; FP = json.load(open(os.path.join(L, "odyssey", "found-pics.json")))
    for b in range(1, 25): chapters.append([str(b), ROMAN[b - 1], f"Book {b}"])
    for sc in SC:
        key = str(sc["book"]); first = True
        for p in (FP.get(sc["id"]) or {}).get("spoken", []):
            for i in [p.get("id")] + [a.get("id") for a in (p.get("alts") or [])[:2]]:
                if i and add(i, key, (p.get("kind") or "story").upper(), p.get("in") if i == p.get("id") else None) and first and i == p.get("id"):
                    holes.append({"id": i, "act": key, "cap": sc["title"]}); first = False
elif WORLD == "norse":
    SB = json.load(open(os.path.join(L, "norse", "storyboard.json"))); WM = json.load(open(os.path.join(L, "norse", "wordmap.json")))
    for k, b in enumerate(SB["books"], 1):
        key = str(k); chapters.append([key, ROMAN[k - 1], b.get("title", f"Book {k}")[:28]])
        for ln in b["lines"]:
            first = True
            for g in ln.get("grounds", [])[:3]:
                pic = SB["pics"].get(g) or {}; i = g if g in lib else VID.get(pic.get("video"))
                if i and add(i, key, "GROUNDS", pic.get("in")) and first: holes.append({"id": i, "act": key, "cap": ln["text"][:90]}); first = False
    for p in WM["pics"][:900]:
        i = VID.get(p.get("video"))
        if i: add(i, str(1 + hash(i) % len(SB["books"])), "THE POOL", p.get("in"))
elif WORLD == "signs":
    T = json.load(open(os.path.join(ROOT, "cineosis-table.json")))["signs"]; FAM = {}
    fam_of = lambda t: next((v for k, v in {"Perception": "perception", "Affection": "affection", "Impulse": "impulse", "Action": "action", "Attraction": "reflection", "Inversion": "reflection", "Discourse": "reflection", "relation": "relation", "recollection": "memory", "dream": "memory"}.items() if t.startswith(k)), "time")
    for s in T: FAM[str(s["n"])] = fam_of(s["image_type"])
    fams = ["perception", "affection", "impulse", "action", "reflection", "relation", "memory", "time"]
    for k, f in enumerate(fams, 1): chapters.append([f, ROMAN[k - 1], f.title()])
    picks = json.load(open(os.path.join(ROOT, "picks.json"))); byn = {str(s["n"]): s for s in T}
    for n, lst in picks.items():
        for c, _ in lst[:1]:
            if add(c, FAM.get(n, "time"), "EXEMPLAR"): holes.append({"id": c, "act": FAM.get(n, "time"), "cap": f"{byn[n]['symbol']} · {byn[n]['name']}" if n in byn else n})
    read = [s for s in lib.values() if s.get("signs") and not s.get("signs_inferred") and s["id"] in EMB]
    per = collections.defaultdict(list)
    for s in read: per[FAM.get(str(s["signs"][0]), "time")].append(s["id"])
    rng = np.random.default_rng(3)
    for f in fams:
        for i in rng.permutation(per[f])[:170]: add(str(i), f, "READ SHOTS")
order = list(shots)[:MAX] if len(shots) > MAX else list(shots)
keep_holes = [h for h in holes if h["id"] in set(order)]
print(f"{WORLD}: {len(shots)} shots ({len(order)} kept) · {len(chapters)} chapters · {len(keep_holes)} holes", flush=True)
# ---- each still: its colour and where its light sits
def fetch(i):
    s = shots[i]; u = still(s["video"]) or (lib.get(i) or {}).get("thumb") or ""
    if not u.startswith("http"): return i, None, u
    try:
        im = Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "cineosis-44-research"}), timeout=30).read())).convert("RGB"); return i, im, u
    except Exception: return i, None, u
got = {}
with cf.ThreadPoolExecutor(10) as ex:
    for i, im, u in ex.map(fetch, order):
        if im is None: continue
        a = np.asarray(im.resize((64, 36))).astype(np.float32) / 255; r, g, b = a.reshape(-1, 3).mean(0); h, l_, s_ = colorsys.rgb_to_hls(r, g, b)
        sat = float(np.mean(np.abs(a - a.mean(2, keepdims=True)))) * 3; bw = int(sat < .05)
        lum = np.asarray(im.convert("L").resize((4, 4), Image.BOX)).astype(np.float32).ravel() / 255
        got[i] = {"th": u, "col": [round(h * 360), round(min(1, sat), 3), round(l_, 3), bw], "comp": lum - lum.mean()}
order = [i for i in order if i in got]; keep_holes = [h for h in keep_holes if h["id"] in got]
print(len(order), "stills read", flush=True)
V = np.stack([EMB[i] for i in order]); V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-9
mu = V.mean(0); _, _, Wt = np.linalg.svd(V - mu, full_matrices=False); Pq = (V - mu) @ Wt[:32].T; Pq /= np.linalg.norm(Pq, axis=1, keepdims=True) + 1e-9
pr = np.random.default_rng(0).integers(0, len(order), (6000, 2)); ca, cb = np.polyfit((Pq[pr[:, 0]] * Pq[pr[:, 1]]).sum(1), (V[pr[:, 0]] * V[pr[:, 1]]).sum(1), 1)
K = np.stack([got[i]["comp"] for i in order]); K /= np.linalg.norm(K, axis=1, keepdims=True) + 1e-9
km = K.mean(0); _, _, Kt = np.linalg.svd(K - km, full_matrices=False); KP = (K - km) @ Kt[:16].T; K2 = KP[:, :2].copy(); KP /= np.linalg.norm(KP, axis=1, keepdims=True) + 1e-9
kpr = np.random.default_rng(1).integers(0, len(order), (6000, 2)); ka, kb = np.polyfit((KP[kpr[:, 0]] * KP[kpr[:, 1]]).sum(1), (K[kpr[:, 0]] * K[kpr[:, 1]]).sum(1), 1)
norm2 = lambda X: np.clip((X - np.percentile(X, 2, 0)) / (np.percentile(X, 98, 0) - np.percentile(X, 2, 0) + 1e-9), 0, 1)
K2 = norm2(K2)
import umap
XY = norm2(umap.UMAP(n_neighbors=18, min_dist=.12, metric="cosine", random_state=7).fit_transform(V))
cards = []
for n, i in enumerate(order):
    s = shots[i]; du = max(1.5, s["dur"]); ss = round(min(max(0.0, float(s["at"] or 0) - .5), max(0.0, du - 1.2)), 2)
    cards.append({"id": i, "k": "ar", "x": round(float(XY[n, 0]), 4), "y": round(float(XY[n, 1]), 4), "th": got[i]["th"], "m": s["video"], "ss": ss, "du": round(du, 2),
                  "ti": s["title"], "w": s["w"], "ch": s["ch"], "src": s["title"][:24], "y0": s["year"], "po": 0, "mc": .5, "sp": None,
                  "e": [int(round(v * 127)) for v in Pq[n]], "f": [int(round(v * 127)) for v in KP[n]], "fx": round(float(K2[n, 0]), 4), "fy": round(float(K2[n, 1]), 4), "col": got[i]["col"], "cc": 0})
base = json.load(open(os.path.join(L, "ludens", "corpus.json")))
out = {"world": WORLD, "signs": base["signs"], "chapters": chapters, "calf": [round(float(ka), 4), round(float(kb), 4)], "cal": [round(float(ca), 4), round(float(cb), 4)],
       "sprites": None, "cards": cards, "holes": keep_holes}
json.dump(out, open(os.path.join(L, "ludens", f"corpus-{WORLD}.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(f"corpus-{WORLD}.json · {len(cards)} shots · {len(keep_holes)} holes · {os.path.getsize(os.path.join(L, 'ludens', f'corpus-{WORLD}.json')) // 1024} KB")
