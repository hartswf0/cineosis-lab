"""The Odyssey forage as a Cineosis collection: odyssey/library.json + odyssey/emb.bin, in the same form as markov/library.json,
so any room can load it beside the main library (SH.load({extra: ['odyssey']})). Clips the main library already holds are left
there. Each new shot gets what the library gives every shot: its three strongest events (the same vocabulary, read relative to
the whole archive), a place (the place of its nearest shot in the main library), and signs inferred from its ten nearest read
shots (marked as inferred).   usage: ../.venv/bin/python build_library.py"""
import json, os, collections
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(os.path.dirname(H), "markov")
lib = json.load(open(os.path.join(M, "library.json"))); have = {s["id"] for s in lib["shots"]}
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); XO = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32); XL = np.load(os.path.join(H, "cache", "emb-laion.npy")).astype(np.float32)
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
keep = [n for n, i in enumerate(ids) if i not in have and i in clips and np.linalg.norm(XO[n]) > .5]
MO = np.fromfile(os.path.join(M, "emb.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]
ML = np.fromfile(os.path.join(M, "emb-laion.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale_laion"]
TE = np.array(json.load(open(os.path.join(M, "events.json")))["emb"], np.float32)
Sm = ML @ TE.T; mu, sd = Sm.mean(0), Sm.std(0)
Z = (XL[keep] @ TE.T - mu) / sd
nn = np.argsort(-(XO[keep] @ MO.T), 1)[:, :10]
shots = []
for r, n in enumerate(keep):
    c = clips[ids[n]]; nb = [lib["shots"][j] for j in nn[r]]
    votes = collections.Counter(s for b in nb for s in (b.get("signs") or [])[:2])
    shots.append({"id": c["id"], "kind": "archive", "coll": "odyssey", "src": c["sourceSlug"], "title": c["sourceTitle"], "year": c.get("sourceYear"),
                  "st": c["startSeconds"], "dur": round((c.get("endSeconds") or 0) - (c.get("startSeconds") or 0), 2), "video": c["videoUrl"], "thumb": c["thumbnailUrl"],
                  "in": round(max(0, (c.get("matchTimestampSeconds") or c["startSeconds"]) - c["startSeconds"]), 2), "scale": None,
                  "signs": [s for s, v in votes.most_common(3) if v >= 3], "signs_inferred": True,
                  "ev": [[int(t), round(float(Z[r, t]), 2)] for t in np.argsort(-Z[r])[:3]], "place": nb[0].get("place", 0)})
X = XO[keep]; sc = float(np.abs(X).max() / 127)
def write(d, rows):
    os.makedirs(d, exist_ok=True)
    np.clip(np.round(X[rows] / sc), -127, 127).astype(np.int8).tofile(os.path.join(d, "emb.bin"))
    json.dump({"n": len(rows), "dim": 512, "scale": sc, "model": "ViT-B-32 openai", "collection": "odyssey", "shots": [shots[r] for r in rows]}, open(os.path.join(d, "library.json"), "w"), separators=(",", ":"))
# the whole forage (odyssey/all/), and the core the room loads at once (odyssey/): the shots its scenes and cuts name
write(os.path.join(H, "all"), list(range(len(shots))))
ref = set()
for f, get in (("cuts.json", lambda d: [i for v in d["cuts"].values() for x in v["shots"] for i in ([x["clip"]] if x["clip"] else []) + x["alts"]]),
               ("scenes.json", lambda d: [i for sc_ in d["scenes"] for b in sc_["beats"] for i, _ in b["ground"] + b["action"]] + [i for sc_ in d["scenes"] for f_ in sc_["figures"] for i in f_["clips"]])):
    if os.path.exists(os.path.join(H, f)): ref |= set(get(json.load(open(os.path.join(H, f)))))
core = [r for r, x in enumerate(shots) if x["id"] in ref] if ref else list(range(len(shots)))
write(H, core); print("core", len(core), "of", len(shots))
print("odyssey collection:", len(shots), "new shots;", len(ids) - len(keep), "already in the main library")
