"""THE DECK: every card the griddle can play, in one index with one CLIP vector each (the archive's model, ViT-B-32 openai, the same space
markov/clip-text.js reads words into in the browser):
  ai       the AI pickups, shot by shot (media + in/out + what they sound like and say)
  archive  each world's archival plates (pools.json)
  drawn    the multiplane cartoons
  figure   moving cut-outs (archive figures, the cook and the pails cut out of the pickups)
Writes slopfeeder/deck.json (cards) and slopfeeder/deck-emb.bin (int8, card order; scale in deck.json).   usage: .venv/bin/python slopfeeder/deck.py"""
import json, os
import numpy as np, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval()
def ci(ps):
    out = []
    for k in range(0, len(ps), 48):
        with torch.no_grad(): e = m.encode_image(torch.stack([prep(Image.open(p).convert("RGB")) for p in ps[k:k + 48]])).float()
        out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    return np.concatenate(out) if out else np.zeros((0, 512), np.float32)
cards, E = [], []
# ---- the AI pickups
AI = json.load(open(os.path.join(D, "ai", "ai.json"))); AU = json.load(open(os.path.join(D, "ai", "audio.json"))) if os.path.exists(os.path.join(D, "ai", "audio.json")) else {}
for c in AI["clips"]:
    au = AU.get(c["name"], {})
    for s in c["shots"]:
        w = [x for x in au.get("words", []) if x["t1"] > s["t0"] and x["t0"] < s["t1"]]; win = [x for x in au.get("windows", []) if s["t0"] - 1 <= x[0] < s["t1"]]
        tags = {}
        for _, ts in win:
            for t in ts: tags[t] = tags.get(t, 0) + 1
        cards.append({"id": f"ai-{c['name']}-{s['k']}", "type": "ai", "world": s["world"], "title": c["title"], "thumb": s["key"], "media": c["web"], "in": s["t0"], "out": s["t1"], "dur": round(s["t1"] - s["t0"], 2),
                      "pov": s["pov"], "motifs": s["motifs"], "sound": sorted(tags, key=lambda t: -tags[t])[:3], "words": [x["text"] for x in w], "hits": [h for h in au.get("hits", []) if s["t0"] <= h < s["t1"]]})
        E.append(np.array(s["emb"], np.float32))
# ---- the archive (each world's pool), embedded from the lab's own vectors
lib = json.load(open(os.path.join(L, "markov", "library.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]; emb = {}
for s, e in zip(lib["shots"], E1): emb[s["id"]] = e
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))): emb.setdefault(i, e)
for i, e in zip(json.load(open(os.path.join(D, "forage-ids.json"))), np.load(os.path.join(D, "forage-emb.npy")).astype(np.float32)): emb.setdefault(i, e)
PO = json.load(open(os.path.join(D, "pools.json")))["pools"]; seen = set()
for w, lst in PO.items():
    for x in lst[:200]:
        if x["id"] in seen or x["id"] not in emb: continue
        seen.add(x["id"]); e = emb[x["id"]]; e = e / (np.linalg.norm(e) + 1e-9)
        cards.append({"id": x["id"], "type": "archive", "world": w, "title": x.get("title"), "year": x.get("year"), "thumb": x["t"], "media": x["v"], "dur": x.get("dur"), "why": x.get("why")}); E.append(e)
# ---- the cartoons
CA = json.load(open(os.path.join(D, "cartoon", "cartoon.json"))); keys = []
for w, c in CA.items(): keys.append(os.path.join(D, c["keys"][len(c["keys"]) // 2])); cards.append({"id": "drawn-" + c["slug"], "type": "drawn", "world": w, "title": "cartoon · " + w.lower(), "thumb": c["keys"][len(c["keys"]) // 2], "media": c["mp4"], "in": 0, "dur": c["dur"]})
E += list(ci(keys))
# ---- figures: archive cut-outs and the pickups' cook / pails / four
figs = [({**c, "src": "archive"}, c["still"]) for c in json.load(open(os.path.join(D, "cuts.json"))) if not c.get("none")]
if os.path.exists(os.path.join(D, "ai", "cuts.json")): figs += [({**c, "src": "ai"}, c["still"]) for c in json.load(open(os.path.join(D, "ai", "cuts.json"))) if not c.get("none")]
fs = []
for c, st in figs:
    if not os.path.exists(os.path.join(D, st)): continue
    fs.append(os.path.join(D, st)); kind = c.get("kind") or c.get("target", "figure")
    cards.append({"id": "fig-" + c["id"], "type": "figure", "world": (c.get("world") or "").upper() if c.get("world", "").startswith("the ") else c.get("world"), "title": f"{kind} · " + (c.get("title") or c.get("clip") or ""), "thumb": st, "packed": c["packed"], "dur": c.get("secs", 4), "kind": kind})
if fs:   # a figure's vector: its cut-out on grey
    tmp = []
    for p in fs:
        im = Image.open(p).convert("RGBA"); bg = Image.new("RGB", im.size, (128, 128, 128)); bg.paste(im, mask=im.split()[3]); q = p + ".grey.jpg"; bg.save(q); tmp.append(q)
    E += list(ci(tmp)); [os.remove(q) for q in tmp]
for c in cards:   # worlds as the griddle names them
    if c.get("world") and not c["world"].startswith("THE "): c["world"] = {"THE LANDING": "THE LANDING"}.get(c["world"], "THE " + c["world"].upper().replace("THE ", ""))
A = np.stack(E).astype(np.float32); A /= np.linalg.norm(A, axis=1, keepdims=True) + 1e-9; sc = float(np.abs(A).max() / 127)
np.clip(np.round(A / sc), -127, 127).astype(np.int8).tofile(os.path.join(D, "deck-emb.bin"))
S = json.load(open(os.path.join(D, "songs.json")))["songs"]
json.dump({"scale": sc, "n": len(cards), "cards": cards, "beats": {s["n"]: s["beats"] for s in S}}, open(os.path.join(D, "deck.json"), "w"), ensure_ascii=False, separators=(",", ":"))
import collections; print(len(cards), "cards ·", dict(collections.Counter(c["type"] for c in cards)), "·", round(os.path.getsize(os.path.join(D, "deck.json")) / 1e6, 2), "MB")
