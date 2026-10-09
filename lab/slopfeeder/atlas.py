"""THE ATLAS: every shot the blacktop can serve, measured the ways an editor sorts abundance.
  vector     CLIP ViT-B-32 (openai): the lab's one space (words typed in the browser land in it too)
  map        UMAP of the vectors to 2-D (the MAP view), k-means clusters (the CLUSTER grouping)
  twins      near-duplicate AI shots grouped (cos > .93): one family, so the same shot stops coming back
  colour     dominant hue, luminance, saturation, and how much of each of the four characters' colours is in frame (purple, orange, yellow)
  frame      where the weight of the picture sits (edge centre of mass) and where its horizon runs: for composition match cuts
  tempo      for AI shots: the period of the motion (pumping, pounding, walking), its strength and phase, to retime pounds onto a song's beat
  sound      what the pickup sounds like (CLAP) and says (Whisper)
  chapters   each card's affinity to each chapter's idea (a CLIP attractor built from the chapter's own words)
Writes slopfeeder/atlas.json + atlas-emb.bin.   usage: .venv/bin/python slopfeeder/atlas.py"""
import json, os, subprocess
import numpy as np, cv2, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ci(ps):
    out = []
    for k in range(0, len(ps), 48):
        with torch.no_grad(): e = m.encode_image(torch.stack([prep(Image.open(p).convert("RGB")) for p in ps[k:k + 48]])).float()
        out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    return np.concatenate(out)
def colour(path):
    try: im = cv2.imread(path); im = cv2.resize(im, (160, 90))
    except Exception: return None
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    ch = {"purple": float(((h > 120) & (h < 148) & (s > 110) & (v > 70)).mean()), "orange": float((((h < 14) | (h > 172)) & (s > 150) & (v > 130)).mean()), "yellow": float(((h > 20) & (h < 34) & (s > 130) & (v > 130)).mean())}
    w = (s / 255.0) * (v / 255.0); hist = np.bincount((h // 15).ravel(), weights=w.ravel(), minlength=12)[:12]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); ed = cv2.Canny(g, 60, 160).astype(np.float32); ys, xs = np.nonzero(ed)
    cx, cy = (float(xs.mean() / 160), float(ys.mean() / 90)) if len(xs) > 30 else (.5, .5)
    rows = np.abs(cv2.Sobel(g.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)).mean(1); hz = float(np.argmax(rows[8:-8]) + 8) / 90
    return {"hue": int(np.argmax(hist)) * 15 + 7, "sat": round(float(s.mean() / 255), 3), "lum": round(float(v.mean() / 255), 3), "bw": float(s.mean()) < 22,
            "chars": {k: round(x, 4) for k, x in ch.items()}, "weight": [round(cx, 3), round(cy, 3)], "horizon": round(hz, 3)}
def tempo(src, t0, t1):
    """the motion's own beat: frame-difference energy, autocorrelated; a period between .3 and 1.6 s"""
    L_ = min(6.0, t1 - t0); a = (t0 + t1) / 2 - L_ / 2
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{a:.2f}", "-i", src, "-t", f"{L_:.2f}", "-vf", "fps=24,scale=96:54,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 54, 96).astype(np.float32)
    if len(f) < 30: return None
    e = np.abs(np.diff(f, axis=0)).mean((1, 2)); e = e - np.convolve(e, np.ones(12) / 12, "same"); e = (e - e.mean()) / (e.std() + 1e-6)
    ac = np.correlate(e, e, "full")[len(e) - 1:]; ac /= ac[0] + 1e-9; lo, hi = int(.3 * 24), min(len(ac) - 1, int(1.6 * 24))
    if hi <= lo + 2: return None
    k = lo + int(np.argmax(ac[lo:hi])); per = k / 24; strength = float(ac[k])
    ph = float(np.argmax(e[:k]) / 24) if k > 0 else 0.0
    return {"period": round(per, 3), "bpm": round(60 / per, 1), "strength": round(strength, 3), "phase": round(a + ph, 3)}
cards, E = [], []
# ---- AI pickups
AI = json.load(open(os.path.join(D, "ai", "ai.json"))); AU = json.load(open(os.path.join(D, "ai", "audio.json"))) if os.path.exists(os.path.join(D, "ai", "audio.json")) else {}
for c in AI["clips"]:
    au = AU.get(c["name"], {}); src = os.path.join(D, "ai", "src", c["name"] + ".mp4")
    for s in c["shots"]:
        win = [x for x in au.get("windows", []) if s["t0"] - 1 <= x[0] < s["t1"]]; tags = {}
        for _, ts in win:
            for t in ts: tags[t] = tags.get(t, 0) + 1
        cd = {"id": f"ai-{c['name']}-{s['k']}", "type": "ai", "clip": c["name"], "world": s["world"], "title": c["title"], "thumb": s["key"], "media": c["web"], "src": f"ai/src/{c['name']}.mp4",
              "in": s["t0"], "out": s["t1"], "dur": round(s["t1"] - s["t0"], 2), "pov": s["pov"], "motifs": s["motifs"], "sound": sorted(tags, key=lambda t: -tags[t])[:3],
              "words": [x["text"] for x in au.get("words", []) if x["t1"] > s["t0"] and x["t0"] < s["t1"]], "hits": [h for h in au.get("hits", []) if s["t0"] <= h < s["t1"]],
              "colour": colour(os.path.join(D, s["key"])), "tempo": tempo(src, s["t0"], s["t1"]) if s["t1"] - s["t0"] > 2 else None}
        cards.append(cd); E.append(np.array(s["emb"], np.float32))
print(len(cards), "AI shots measured", flush=True)
# ---- the archive
lib = json.load(open(os.path.join(L, "markov", "library.json")))
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]; emb = {}
for s, e in zip(lib["shots"], E1): emb[s["id"]] = e
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))): emb.setdefault(i, e)
for i, e in zip(json.load(open(os.path.join(D, "forage-ids.json"))), np.load(os.path.join(D, "forage-emb.npy")).astype(np.float32)): emb.setdefault(i, e)
PO = json.load(open(os.path.join(D, "pools.json")))["pools"]; seen = set()
for w, lst in PO.items():
    for x in lst[:200]:
        if x["id"] in seen or x["id"] not in emb or not os.path.exists(os.path.join(D, "athumbs", x["id"] + ".jpg")): continue
        seen.add(x["id"]); e = emb[x["id"]]; e = e / (np.linalg.norm(e) + 1e-9)
        cards.append({"id": x["id"], "type": "archive", "world": w, "title": x.get("title"), "year": x.get("year"), "thumb": f"athumbs/{x['id']}.jpg", "media": x["v"], "dur": x.get("dur"),
                      "colour": colour(os.path.join(D, "athumbs", x["id"] + ".jpg"))}); E.append(e)
print(len(cards), "with the archive", flush=True)
# ---- the cartoons (drawn): only as opt-in cards
CA = json.load(open(os.path.join(D, "cartoon", "cartoon.json"))); ks = []
for w, c in CA.items():
    k = c["keys"][len(c["keys"]) // 2]; ks.append(os.path.join(D, k)); cards.append({"id": "drawn-" + c["slug"], "type": "drawn", "world": w, "title": "cartoon · " + w.lower(), "thumb": k, "media": c["mp4"], "in": 0, "dur": c["dur"], "colour": colour(os.path.join(D, k))})
E += list(ci(ks))
A = np.stack(E).astype(np.float32); A /= np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
# ---- the map, the clusters, the twins
import umap
from sklearn.cluster import KMeans
xy = umap.UMAP(n_neighbors=18, min_dist=.12, metric="cosine", random_state=7).fit_transform(A); xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0) + 1e-9)
km = KMeans(n_clusters=28, n_init=6, random_state=7).fit(A); T = ct(["a photo"])  # cluster names: the nearest of a small vocabulary
VOC = ["soldiers charging on a beach", "orange buckets in sand", "a skull-masked cook", "a griddle with burgers", "workers pumping drills", "flat cartoon shapes", "a computer screen", "a control room",
       "warships at sea", "ocean waves", "an explosion", "smoke and ruins", "a crowd eating", "a cook in a kitchen", "a login page", "a landing craft", "a brick fort", "a desert landscape", "men digging",
       "a rocket", "a factory machine", "a face close up", "people walking on a beach", "fire at night", "masked figures chanting", "an airship in the sky", "a drain in the sand", "a mess hall"]
VT = ct(VOC); cname = [VOC[int(np.argmax(VT @ (c / np.linalg.norm(c))))] for c in km.cluster_centers_]
ai_idx = [i for i, c in enumerate(cards) if c["type"] == "ai"]; fam = {}
for a in ai_idx:
    if a in fam: continue
    fam[a] = a
    for b in ai_idx:
        if b not in fam and float(A[a] @ A[b]) > .93: fam[b] = a
for i, c in enumerate(cards):
    c["xy"] = [round(float(xy[i, 0]), 4), round(float(xy[i, 1]), 4)]; c["cluster"] = int(km.labels_[i])
    if i in fam: c["twin"] = cards[fam[i]]["id"]
# ---- the chapters' attractors: each chapter's words, read by CLIP
B = json.load(open(os.path.join(D, "bible.json")))["chapters"]; att = {}
for ch in B:
    words = [ch["idea"], ch["four"], *ch["symbols"], *[s["moment"] for s in ch["shots"]]]; v = ct([w[:300] for w in words]).mean(0); att[ch["n"]] = v / np.linalg.norm(v)
for i, c in enumerate(cards): c["aff"] = {n: round(float(A[i] @ v), 3) for n, v in att.items()}
sc = float(np.abs(A).max() / 127); np.clip(np.round(A / sc), -127, 127).astype(np.int8).tofile(os.path.join(D, "atlas-emb.bin"))
S = json.load(open(os.path.join(D, "songs.json")))["songs"]
json.dump({"scale": sc, "n": len(cards), "cards": cards, "clusters": cname, "chapters": {ch["n"]: {"roman": ch["roman"], "title": ch["title"], "song": ch["song"], "idea": ch["idea"]} for ch in B},
           "songs": {s["n"]: {"title": s["title"], "file": s["file"], "dur": s["dur"], "tempo": s["tempo"], "beats": s["beats"], "energy": s["energy"], "sections": s["sections"]} for s in S}},
          open(os.path.join(D, "atlas.json"), "w"), ensure_ascii=False, separators=(",", ":"))
import collections
print(len(cards), "cards ·", dict(collections.Counter(c["type"] for c in cards)), "· twins families:", len(set(fam.values())), "of", len(ai_idx), "AI shots ·",
      sum(1 for c in cards if c.get("tempo") and c["tempo"]["strength"] > .35), "AI shots with a strong motion beat")
