"""The whole archive the lab can reach (library + Odyssey clips + forage, ~38k shots) as one CLIP index for written queries, cached:
src/archpool.npy (unit openai ViT-B-32 vectors, float16) + src/archpool.json (id, title, year, v, dur). Same sources as pools.py.
usage: .venv/bin/python slopfeeder/archpool.py   (story.py imports query())"""
import json, os
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); NP, JS = os.path.join(D, "src", "archpool.npy"), os.path.join(D, "src", "archpool.json")
def build():
    lib = json.load(open(os.path.join(L, "markov", "library.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
    E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]; meta, emb = {}, {}
    for s, e in zip(lib["shots"], E1):
        if s["kind"] == "archive": meta[s["id"]] = (s.get("title"), s.get("year")); emb[s["id"]] = e
    title = {c["id"]: (c["sourceTitle"], c.get("sourceYear")) for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json")))}
    for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))):
        if i not in emb and i in title: meta[i] = title[i]; emb[i] = e
    R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"; rec = {}
    for i in emb:
        if i in V: rec[i] = {"id": i, "title": meta[i][0], "year": meta[i][1], "v": R2 + V[i][0], "dur": V[i][1]}
    F = {c["id"]: c for c in json.load(open(os.path.join(D, "forage.json")))["clips"]}
    for i, e in zip(json.load(open(os.path.join(D, "forage-ids.json"))), np.load(os.path.join(D, "forage-emb.npy")).astype(np.float32)):
        if i in F and i not in emb: c = F[i]; emb[i] = e; rec[i] = {"id": i, "title": c["title"], "year": c["year"], "v": c["v"], "dur": c["dur"]}
    ids = list(rec); A = np.stack([emb[i] for i in ids]).astype(np.float32); A /= np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
    np.save(NP, A.astype(np.float16)); json.dump([rec[i] for i in ids], open(JS, "w")); print(len(ids), "archive shots")
_m, _A, _R = [], None, None
def text(q):
    import torch, open_clip
    if not _m: _m.extend([open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai")[0].eval(), open_clip.get_tokenizer("ViT-B-32-quickgelu")])
    with torch.no_grad(): e = _m[0].encode_text(_m[1](["a film still of " + q])).numpy()[0]
    return e / np.linalg.norm(e)
def load():
    global _A, _R
    if _A is None:
        if not os.path.exists(NP): build()
        _A = np.load(NP).astype(np.float32); _R = json.load(open(JS))
        dark = _A @ np.stack([text(x) for x in ["a completely black dark empty frame", "a completely white blank overexposed frame", "a title card with text on it", "a blurry out of focus frame"]]).T
        _A_pen[:] = [np.clip(dark.max(1) - .2, 0, None)]
    return _A, _R
_A_pen = [None]
def query(q, k=40, vec=None, w=.25):   # ranked records for a written phrase (+ a little of an image vector, if given); dark/blank/title frames sink
    A, R = load(); s = A @ text(q) - .6 * _A_pen[0]
    if vec is not None: s = s + w * (A @ (vec / (np.linalg.norm(vec) + 1e-9)))
    return [(float(s[i]), R[i]) for i in np.argsort(-s)[:k]]
if __name__ == "__main__":
    build()
    import sys
    for q in sys.argv[1:]: print(q, "|", " ; ".join(f"{s:.3f} {r['title'][:28]}" for s, r in query(q, 6)))
