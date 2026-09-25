"""Rank every clip for every WYGWYL beat, with the reasons → wygwyl/candidate-ranks.json.

For each of the 88 beats, the pool is the suite's own candidates and forage, the four cuts' shots at that time, the
sign families of the beat's signs — plus ARCHIVE FINDS: the best clips for the beat in the whole 15,149-shot corpus,
which the suite's forage never retrieved.

Two questions, answered separately:
  FIT (absolute, 0–100): does the clip actually show what the beat needs? CLIP (ViT-B/32) similarity of its thumbnail to
      the poem line and to the beat's treatment (title + the suite's own visual searches), mapped 0.15 → 0, 0.30 → 100.
      For scale: the archive's median shot scores 0.135 against a line, the suite's forage 0.157, the archive's best ~0.29.
  RANK (relative): which of the clips on offer for THIS beat is best. Five pieces of evidence, each a percentile within
      the beat's own pool: line and scene (the CLIP similarities above), sign (the machine's affinity for the beat's
      signs), review (the suite's reviewer: F moderate visual match 100 · P limited 55 · never reviewed 35), craft
      (measured: dead frames and title-card likelihood lower it, and so does being shorter than the beat; unmeasured 60).
      score = .35 line + .25 scene + .15 sign + .10 review + .15 craft; a second clip from the same film loses 6 points.
Verdict: KEEP = among the beat's top 8 and fit ≥ 45 · FLOOR = bottom half of the pool, a title card, or dead frames ·
MAYBE between. Each beat: strong (best fit ≥ 67) · thin (≥ 45) · weak (no good candidate yet: forage again).
    lab/.venv/bin/python lab/wygwyl/rank_candidates.py
"""
import json, os
import numpy as np, torch, open_clip

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, "collage-data.json")))
E = np.load(os.path.join(LAB, "cache", "emb.npy")).astype(np.float32)
E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
IDS = json.load(open(os.path.join(LAB, "cache", "emb_ids.json"))); IX = {i: k for k, i in enumerate(IDS)}
AFF = json.load(open(os.path.join(LAB, "cache", "affinity.json")))
CORPUS = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
WATCH = {}
for f in os.listdir(os.path.join(LAB, "cache", "watch")):
    try: w = json.load(open(os.path.join(LAB, "cache", "watch", f))); WATCH[w["id"]] = w
    except Exception: pass
W = {"line": .35, "scene": .25, "sign": .15, "review": .10, "craft": .15}

model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
tok = open_clip.get_tokenizer("ViT-B-32"); model.eval()
def enc(texts):
    with torch.no_grad():
        t = model.encode_text(tok([x[:300] for x in texts])).float(); t /= t.norm(dim=-1, keepdim=True)
    return t.numpy()

# sign affinity percentiles, per sign, across the archive
signs = sorted({n for b in D["beats"] for n in b["codes"]})
aff_rank = {}
for n in signs:
    v = np.array([AFF[i]["all"].get(n, 0) if i in AFF else 0 for i in IDS]); order = v.argsort().argsort()
    aff_rank[n] = {IDS[k]: 100 * order[k] / (len(IDS) - 1) for k in range(len(IDS))}

def pct(sims):                                      # percentile of every shot against the archive, for one text
    o = sims.argsort().argsort(); return 100 * o / (len(sims) - 1)

GR = {"F": 100, "P": 55}
# title-card likelihood for every shot from its thumbnail (the same prompts as watch.py): text-matching favours printed words
CARD = ["a title card with printed words", "white text on a black screen", "a film leader countdown", "a test pattern or color bars"]
REAL = ["a photograph of a real scene", "people in a place", "a landscape", "an object in a room"]
_T = enc(CARD + REAL); _P = np.exp((E @ _T.T) * 100); _P /= _P.sum(1, keepdims=True)
CARDP = {IDS[k]: float(_P[k, :len(CARD)].sum()) for k in range(len(IDS))}
out = {"method": __doc__.strip().split("\n\n")[1], "weights": W, "beats": {}}
for b in D["beats"]:
    line = " ".join(c["text"] for c in D["cues"] if c["t1"] > b["start"] and c["t0"] < b["end"] and c["text"]) or b["title"]
    scene_txt = [b["title"]] + (b.get("recipes") or [b.get("query") or b["title"]])[:4]
    T = enc([line] + scene_txt)
    s_line = E @ T[0]; s_scene = (E @ T[1:].T).mean(1)
    p_line, p_scene = pct(s_line), pct(s_scene)
    blen = b["end"] - b["start"]
    pool, seen = [], set()
    def put(c, src, tag):
        if not c or not c.get("id") or c["id"] in seen or not c.get("video"): return
        seen.add(c["id"]); pool.append({"id": c["id"], "title": c.get("title"), "year": c.get("year"), "thumb": c.get("thumb"), "video": c.get("video"),
                                        "url": c.get("url"), "in": c.get("in") or 0, "dur": c.get("dur"), "grade": c.get("grade") or "U",
                                        "observed": c.get("observed"), "use": c.get("use"), "src": src, "tag": tag})
    for k in ("suite", "scenes", "cineosis", "drift"):
        for p in D["cuts"][k]:
            if p["t1"] > b["start"] and p["t0"] < b["end"]: put(p, "cut", k + " cut")
    for c in b["candidates"]: put(c, "candidate", "candidate")
    for n in b["codes"]:
        for f in (D["signs"].get(n) or {}).get("family", []): put(f, "sign", f"{D['signs'][n]['symbol']} family")
    for c in b["forage"]: put(c, "forage", "forage")
    # archive finds: the corpus's best for this beat that the forage never brought
    comb = .6 * p_line + .4 * p_scene
    for k in np.argsort(-comb)[:40]:
        i = IDS[k]; c = CORPUS.get(i)
        if not c or i in seen or sum(1 for x in pool if x["src"] == "archive" and x["title"] == c.get("sourceTitle")) >= 2: continue
        put({"id": i, "title": c.get("sourceTitle"), "year": c.get("sourceYear"), "thumb": c.get("thumbnailUrl"), "video": c.get("videoUrl"),
             "url": f"https://www.movingimagearchive.com/sources/{c.get('sourceSlug')}?clip={i}", "dur": (c.get("endSeconds") or 0) - (c.get("startSeconds") or 0)},
            "archive", "archive find")
        if sum(1 for x in pool if x["src"] == "archive") >= 12: break
    ranked = []
    fitmap = lambda c: max(0.0, min(100.0, (c - .15) / .15 * 100))
    ks = [IX.get(c["id"]) for c in pool]
    raw_l = np.array([s_line[k] if k is not None else np.median(s_line) for k in ks]); raw_s = np.array([s_scene[k] if k is not None else np.median(s_scene) for k in ks])
    rel = lambda v: 100 * v.argsort().argsort() / max(1, len(v) - 1)
    sg = np.array([max([AFF[c["id"]]["all"].get(n, 0) for n in b["codes"]] or [0]) if c["id"] in AFF else 0 for c in pool])
    R_l, R_s, R_g = rel(raw_l), rel(raw_s), rel(sg)
    for j, c in enumerate(pool):
        review = GR.get(c["grade"], 35)
        w = WATCH.get(c["id"]); dur = (w or {}).get("dur") or c.get("dur") or 0
        flags = []
        if w:
            craft = 100 * (1 - min(1, w.get("dead", 0) * 1.6)) * (1 - min(1, max(0, w.get("card", 0) - .25) * 1.4))
            if w.get("card", 0) >= .55: flags.append("title card")
            if w.get("dead", 0) >= .35: flags.append("dead frames")
        else:
            cp = CARDP.get(c["id"], 0); craft = 60 * (1 - min(1, max(0, cp - .25) * 1.4))
            if cp >= .55: flags.append("title card")
        if dur and dur < blen * .6: craft *= .75; flags.append(f"{dur:.1f} s for a {blen:.1f} s beat")
        comp = {"line": round(R_l[j]), "scene": round(R_s[j]), "sign": round(R_g[j]), "review": review, "craft": round(craft),
                "fl": round(fitmap(raw_l[j])), "fs": round(fitmap(raw_s[j])), "cl": round(float(raw_l[j]), 3), "cs": round(float(raw_s[j]), 3), "aff": round(float(sg[j]), 1)}
        score = sum(W[x] * comp[x] for x in W)
        strongest = max(("line", "scene", "sign"), key=lambda x: comp[x])
        cat = {"line": "carries the line", "scene": "holds the scene", "sign": "reads the sign"}[strongest]
        if c["grade"] == "F" and review >= comp[strongest]: cat = "reviewed fit"
        if c["src"] == "archive": cat = "archive find"
        ranked.append({**{k2: c[k2] for k2 in ("id", "title", "year", "thumb", "video", "url", "in", "src", "tag", "grade")},
                       "dur": round(dur, 1) if dur else None, "score": score, "fit": max(comp["fl"], comp["fs"]), "cat": cat, "comp": comp, "flags": flags,
                       "obs": c["observed"] if c.get("observed") and not str(c["observed"]).startswith("Unreviewed") else None})
    ranked.sort(key=lambda x: -x["score"])
    films = {}
    for x in ranked:                                 # one film should not fill the top: each repeat of a source loses 6
        n = films.get(x["title"], 0); x["score"] = round(x["score"] - 6 * n); films[x["title"]] = n + 1
    half = len(ranked) / 2
    ranked.sort(key=lambda x: -x["score"])
    for r, x in enumerate(ranked):
        x["rank"] = r + 1
        bad = any(f in ("title card", "dead frames") for f in x["flags"])
        x["verdict"] = "FLOOR" if (bad or r >= half) else "KEEP" if (r < 8 and x["fit"] >= 45) else "MAYBE"
    ranked = ranked[:48]
    best_fit = max([x["fit"] for x in ranked] or [0])
    v = [x["verdict"] for x in ranked]
    out["beats"][str(b["id"])] = {"line": line, "best": ranked[0]["id"] if ranked else None, "best_fit": best_fit,
                                  "strength": "strong" if best_fit >= 67 else "thin" if best_fit >= 45 else "weak",
                                  "keep": v.count("KEEP"), "maybe": v.count("MAYBE"), "floor": v.count("FLOOR"), "pool": len(pool),
                                  "archive_first": bool(ranked and ranked[0]["src"] == "archive"),
                                  "forage_fit": round(float(np.median([x["fit"] for x in ranked if x["src"] in ("candidate", "forage")] or [0]))), "ranked": ranked}
json.dump(out, open(os.path.join(HERE, "candidate-ranks.json"), "w"), ensure_ascii=False, separators=(",", ":"))
B = out["beats"].values()
import collections
print("beats", len(out["beats"]), "·", dict(collections.Counter(b["strength"] for b in B)), "· KEEP per beat median", int(np.median([b["keep"] for b in B])),
      "· forage fit median", int(np.median([b["forage_fit"] for b in B])), "· archive find first in", sum(1 for b in B if b["archive_first"]), "· size", os.path.getsize(os.path.join(HERE, "candidate-ranks.json")) // 1024, "KB")
