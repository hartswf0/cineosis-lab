"""Data for Part II, HOW THE IMAGE BECOMES OPERATIVE (lab/operative.html): the lab's own numbers about its own operations.
  hue      one colour shot taken through the hue calculation step by step (analyze.colour): 3,072 pixels, 5 k-means colours,
           each colour's angle weighted by saturation x brightness x share, the vector sum; and the sheep (black and white: no hue)
  vocab    how few words the machines identify with: label lists, the caption vocabulary and its most repeated words
  skew     what the archive is made of: decades, makers, purposes, black-and-white share, unheard and unspoken shares
  motion   a pass none of our models makes: optical flow over the sheep clip, as arrows per frame and a curve of how much moves
  costs    seconds per shot for every pass on this machine (explain/costs.json, measured), scaled to the whole archive
usage: lab/.venv/bin/python lab/explain/build2.py"""
import json, os, re, collections, sys
import numpy as np, cv2
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
sys.path.insert(0, LAB)
D = J("lab-data.json"); shots = D["shots"]; by = {s["id"]: s for s in shots}; cap = J("rushes/captions.json"); SND = J("sound-layer.json"); TX = J("transcripts.json")
SEED = "21171e70-f59f-55b6-85c3-29691c97e312"
card = lambda k, **x: {"id": k, "title": by[k]["title"], "year": by[k].get("year"), "thumb": by[k]["thumb"], "video": by[k].get("video"), "t": by[k].get("read_t") or 0, "cap": cap.get(k, ""), **x}
out = {}
# ---- hue, step by step, exactly as analyze.colour does it
def hue_steps(k):
    img = cv2.imread(os.path.join(LAB, by[k]["thumb"])); small = cv2.resize(img, (64, 48), interpolation=cv2.INTER_AREA); px = small.reshape(-1, 3).astype(np.float32)
    cv2.setRNGSeed(7); _, lab, cen = cv2.kmeans(px, 5, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(lab.ravel(), minlength=5); order = np.argsort(-counts); rank = np.empty(5, int); rank[order] = np.arange(5)
    cb = cen[order].clip(0, 255).astype(np.uint8); hsv = cv2.cvtColor(cb.reshape(1, -1, 3), cv2.COLOR_BGR2HSV)[0].astype(float)
    w = counts[order] / counts.sum(); sw = (hsv[:, 1] / 255) * (hsv[:, 2] / 255) * w; ang = hsv[:, 0] * 2
    vx, vy = float((np.cos(np.deg2rad(ang)) * sw).sum()), float((np.sin(np.deg2rad(ang)) * sw).sum())
    hue = (np.rad2deg(np.arctan2(vy, vx)) + 360) % 360 if sw.sum() > .03 else None
    rgb = small[:, :, ::-1].reshape(-1, 3)
    return {"id": k, "thumb": by[k]["thumb"], "title": by[k]["title"], "year": by[k].get("year"), "px": rgb.flatten().tolist(), "lab": rank[lab.ravel()].tolist(),
            "cols": ["#%02x%02x%02x" % (c[2], c[1], c[0]) for c in cb], "share": np.round(w, 3).tolist(), "ang": np.round(ang, 1).tolist(),
            "sat": np.round(hsv[:, 1] / 255, 3).tolist(), "val": np.round(hsv[:, 2] / 255, 3).tolist(), "weight": np.round(sw, 4).tolist(),
            "vec": [round(vx, 4), round(vy, 4)], "chroma": round(float(sw.sum()), 4), "hue": None if hue is None else round(float(hue), 1), "stored": by[k].get("hue")}
colour_read = [s for s in shots if s.get("signs") and s.get("hue") is not None and (s.get("sat") or 0) > .32 and os.path.exists(os.path.join(LAB, "clips", s["id"] + ".mp4"))]
colour_read.sort(key=lambda s: -(s.get("sat") or 0))
out["hue"] = [hue_steps(colour_read[0]["id"]), hue_steps(SEED)]
hs = [s.get("hue") for s in shots]
out["hue_stats"] = {"none": sum(h is None for h in hs), "total": len(shots), "hist": np.histogram([h for h in hs if h is not None], bins=36, range=(0, 360))[0].tolist()}
# ---- vocabulary: what the machines can say
words = collections.Counter(); phr = collections.Counter(); lens = []
for c in cap.values():
    ws = re.findall(r"[a-z']+", c.lower()); words.update(ws); lens.append(len(ws))
    for n in (3, 4):
        for i in range(len(ws) - n + 1): phr[" ".join(ws[i:i + n])] += 1
STOP = set("a an the of in on at with and to is are there it its his her their this that from by".split())
out["vocab"] = {"subjects": 20, "scales": 5, "sounds": 30, "signs": 45, "captions": len(cap), "unique": len(words), "mean_len": round(float(np.mean(lens)), 1),
                "top": [[w, n] for w, n in words.most_common(80) if w not in STOP][:24], "phrases": [[p, n] for p, n in phr.most_common(40) if not set(p.split()) <= STOP][:12],
                "gender": {w: words[w] for w in ["man", "men", "woman", "women", "boy", "girl", "people", "person"]},
                "old": sum(1 for c in cap.values() if re.search(r"\b(old|vintage|black and white)\b", c.lower()))}
# ---- what the archive is made of
PUR = J("research/purpose.json"); dec = collections.Counter(str(s.get("decade") or "undated") for s in shots); kinds = collections.Counter(); acts = collections.Counter()
for s in shots:
    p = PUR.get(s["slug"]) or {}; kinds[p.get("kind") or "unknown"] += 1; acts[p.get("act") or "unknown"] += 1
heard = set(SND["heard"])
out["skew"] = {"decades": sorted(dec.items(), key=lambda x: x[0]), "kinds": kinds.most_common(10), "acts": acts.most_common(8), "bw": sum(1 for s in shots if s.get("bw")),
               "unheard": sum(1 for s in shots if s["id"] not in heard), "unspoken": sum(1 for s in shots if s["id"] not in TX), "uncaptioned": sum(1 for s in shots if s["id"] not in cap),
               "read": sum(1 for s in shots if s.get("signs")), "found": sum(1 for s in shots if s.get("found")), "films": len({s["slug"] for s in shots}),
               "read_by_sign": collections.Counter(str(s["signs"][0]["n"]) for s in shots if s.get("signs")).most_common(), "found_by_sign": collections.Counter(str(f["n"]) for s in shots for f in (s.get("found") or [])[:1]).most_common()}
# ---- motion: optical flow, a pass none of our models makes
def motion(k, fps=6, gw=16, gh=12):
    cap_ = cv2.VideoCapture(os.path.join(LAB, "clips", k + ".mp4")); src = cap_.get(cv2.CAP_PROP_FPS) or 24; step = max(1, round(src / fps)); fr, n, prev = [], 0, None
    while True:
        ok, f = cap_.read()
        if not ok: break
        if n % step == 0:
            g = cv2.cvtColor(cv2.resize(f, (320, 240)), cv2.COLOR_BGR2GRAY)
            if prev is not None:
                fl = cv2.calcOpticalFlowFarneback(prev, g, None, .5, 3, 15, 3, 5, 1.2, 0)
                cell = fl.reshape(gh, 240 // gh, gw, 320 // gw, 2).mean((1, 3)); mag = float(np.linalg.norm(fl, axis=2).mean())
                fr.append({"t": round(n / src, 2), "m": round(mag, 3), "v": np.round(cell, 2).reshape(-1).tolist()})
            prev = g
        n += 1
    return {"id": k, "video": by[k]["video"], "fps": fps, "gw": gw, "gh": gh, "frames": fr}
mov = [s for s in shots if s.get("signs") and os.path.exists(os.path.join(LAB, "clips", s["id"] + ".mp4")) and (s.get("subjects") or [{}])[0].get("label") in ("vehicle", "crowd", "animal", "water")]
out["motion"] = [motion(SEED)] + [motion(m["id"]) for m in mov[:1]]
out["costs"] = json.load(open(os.path.join(H, "costs.json"))); out["total"] = len(shots)
out["seed"] = card(SEED); out["colour_card"] = card(colour_read[0]["id"])
json.dump(out, open(os.path.join(H, "film2.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("hue", out["hue"][0]["title"], out["hue"][0]["hue"], "stored", out["hue"][0]["stored"], "| sheep", out["hue"][1]["hue"], "chroma", out["hue"][1]["chroma"])
print("no hue", out["hue_stats"]["none"]); print("vocab", out["vocab"]["unique"], out["vocab"]["mean_len"], out["vocab"]["top"][:10], out["vocab"]["phrases"][:6], out["vocab"]["gender"])
print("skew", out["skew"]["kinds"][:6], out["skew"]["acts"][:6], "bw", out["skew"]["bw"]); print("read by sign", out["skew"]["read_by_sign"][:5], len(out["skew"]["read_by_sign"]))
print("motion frames", [len(m["frames"]) for m in out["motion"]], [max(f["m"] for f in m["frames"]) for m in out["motion"]]); print(os.path.getsize(os.path.join(H, "film2.json")) // 1024, "KB")
