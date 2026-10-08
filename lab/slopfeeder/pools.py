"""Each part of the SLOPFEEDER world as a pool of archival shots, chosen by CLIP across everything the lab has (the library and the
Odyssey clips, ~36,000) and everything the forage brought back (~2,200): each world is described in several concrete sentences, a shot's
score is its best match to any of them, dark/empty frames sink, no more than two shots from one source film.
Writes slopfeeder/pools.json (studio.py reads it).   usage: .venv/bin/python slopfeeder/pools.py"""
import json, os
import numpy as np, torch, open_clip
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
WORLDS = {
 "THE LANDING": ["soldiers running across a beach under fire", "a landing craft full of soldiers in the surf", "an explosion throwing up sand on a beach", "soldiers firing rifles from a trench",
                 "a battleship firing its big guns", "artillery firing with a flash of smoke", "a huge explosion fireball", "soldiers wading ashore from boats", "tracer fire in the night sky", "a building exploding"],
 "THE FLEET": ["a fleet of warships at sea", "a battleship in heavy waves", "a burning ship sinking", "an aircraft carrier at sea", "warships on the horizon", "a flying saucer in the sky", "a spaceship in space", "a rocket launch"],
 "THE RENDER": ["cartoon characters with big eyes", "an animated cartoon", "abstract animated shapes", "a giant face on a screen", "a television screen glowing in the dark", "science fiction laser beam"],
 "THE DRILL LINE": ["a line of men hauling on a rope", "workers digging in sand with shovels", "men carrying a heavy wooden beam", "soldiers building a sandbag wall", "workers drilling into the ground", "a bucket brigade passing buckets"],
 "THE KITCHEN": ["a cook flipping hamburgers on a grill", "an army field kitchen feeding soldiers", "a cook in a white hat stirring a big pot", "soldiers lining up for food", "meat sizzling on a griddle", "a mess hall full of men eating"],
 "THE SCREEN": ["a room full of computers with blinking lights", "a programmer at a computer terminal", "a radar screen", "an oscilloscope screen", "a control room with screens", "a robot arm in a factory", "tape drives of a mainframe computer"],
 "THE TIDE": ["waves washing over sand", "the tide coming in on an empty beach", "the ocean at dawn", "a quiet sea with mist", "water flowing into a drain"],
 "THE AFTERMATH": ["smoke drifting over a battlefield", "wreckage on a beach", "exhausted soldiers sitting on the ground", "a ruined building after a bombing", "a soldier staring at the camera"]}
lib = json.load(open(os.path.join(L, "markov", "library.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]
meta, emb = {}, {}
for s, e in zip(lib["shots"], E1):
    if s["kind"] == "archive": meta[s["id"]] = (s.get("title"), s.get("year")); emb[s["id"]] = e
title = {c["id"]: (c["sourceTitle"], c.get("sourceYear")) for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json")))}
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))):
    if i not in emb and i in title: meta[i] = title[i]; emb[i] = e
R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"; rec = {}
for i in emb:
    if i in V: rec[i] = {"id": i, "title": meta[i][0], "year": meta[i][1], "v": R2 + V[i][0], "t": R2 + V[i][0].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg"), "dur": V[i][1]}
F = json.load(open(os.path.join(D, "forage.json")))["clips"]; fids = json.load(open(os.path.join(D, "forage-ids.json"))); FE = np.load(os.path.join(D, "forage-emb.npy")).astype(np.float32)
fmap = {c["id"]: c for c in F}
for i, e in zip(fids, FE):
    if i in fmap and i not in emb: c = fmap[i]; emb[i] = e; rec[i] = {"id": i, "title": c["title"], "year": c["year"], "v": c["v"], "t": c["t"], "dur": c["dur"]}
ids = [i for i in rec if i in emb]; A = np.stack([emb[i] for i in ids]); A /= np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
dark = A @ ct(["a completely black dark empty frame", "a completely white blank overexposed frame", "a title card with text", "a blurry out of focus frame"]).T; pen = np.clip(dark.max(1) - .2, 0, None)
out = {}
for w, sents in WORLDS.items():
    S = A @ ct(sents).T; best = S.max(1) - .6 * pen; arg = S.argmax(1); seen, lst = {}, []
    for j in np.argsort(-best):
        r = rec[ids[j]]
        if (r.get("dur") or 0) < 1.5: continue
        t = r["title"] or "?"
        if seen.get(t, 0) >= 2: continue
        seen[t] = seen.get(t, 0) + 1; lst.append({**r, "fit": round(float(best[j]), 3), "why": sents[int(arg[j])]})
        if len(lst) >= 220: break
    out[w] = lst; print(w, len(lst), "·", lst[0]["title"], "/", lst[1]["title"], "/", lst[2]["title"])
json.dump({"worlds": WORLDS, "pools": out}, open(os.path.join(D, "pools.json"), "w"), ensure_ascii=False)
