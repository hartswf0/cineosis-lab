"""Markov Sea: the radio Odyssey opened up. On top of radio.json (voices on their words, the cut, the bed) it adds
  the sea    for every shot, the other footage it could have been (the cut's own alternatives, then the beat's pool), each
             with what its own sound is like, so the picture can be retuned by hand or steered by sound
  the cast   for every speaking part, archival people actually talking (searches cast:<name>), ranked by how much the frame
             looks like a person speaking and how much the clip sounds like talk; one face per part per book by default
Writes sea.json (published).   usage: ../.venv/bin/python sea_build.py"""
import json, os
import numpy as np, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(H, "radio.json"))); cuts = json.load(open(os.path.join(H, "cuts.json")))["cuts"]
scenes = {s["id"]: s for s in json.load(open(os.path.join(H, "scenes.json")))["scenes"]}
audio = json.load(open(os.path.join(H, "cache", "audio.json"))) if os.path.exists(os.path.join(H, "cache", "audio.json")) else {}
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); X = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32); row = {i: n for n, i in enumerate(ids)}
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def enc(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
TALK = enc(["a close-up of a person talking", "a person speaking to the camera", "a man speaking, his mouth open"])
def snd(i):
    a = audio.get(i) or {}
    if not a.get("audio") or a.get("lufs") is None: return {"snd": 0}
    talky = a.get("band_db") is not None and a["band_db"] - a["lufs"] > -6
    return {"snd": round(max(0, min(1, (a["lufs"] + 45) / 30)), 2), "talky": talky, "lufs": a["lufs"]}
def item(i):
    L = lib.get(i)
    if not L: return None
    return {"id": i, "video": L["video"], "thumb": L["thumb"], "in": L.get("in", 0), "title": L.get("title"), "year": L.get("year"), **snd(i)}
# the cast: for every speaking part, archival people talking
asks = {}
for c in clips.values():
    for key, role, q, rank, sc in c["asks"]:
        if key.startswith("cast:") and c["id"] in row: asks.setdefault(key[5:], {})[c["id"]] = max(asks.get(key[5:], {}).get(c["id"], 0), sc or 0)
cast = {}
for name, pool in asks.items():
    idx = list(pool); E = X[[row[i] for i in idx]]
    sc = (E @ TALK.T).max(1) + .3 * np.array([pool[i] for i in idx]) + np.array([.02 if snd(i).get("talky") else 0 for i in idx])
    order = [idx[j] for j in np.argsort(-sc)]
    seen, picked = set(), []
    for i in order:                              # one clip per source film, so the faces differ
        s = (clips.get(i) or {}).get("sourceId")
        if s in seen: continue
        seen.add(s); it = item(i)
        if it: picked.append(it)
        if len(picked) >= 8: break
    cast[name] = picked
# the sea: each shot's other possibilities
for b in R["books"]:
    for s in b["scenes"]:
        cut = cuts[s["id"]]; sc = scenes.get(s["id"], {})
        beat_pool = {}
        for bt in sc.get("beats", []):
            for i, f in bt["action"][:6] + bt["ground"][:4]: beat_pool[i] = f
        live = [x for x in cut["shots"] if x["clip"] and x["clip"] in lib]
        for sh, x in zip(s["shots"], live):
            sea = [i for i in x["alts"] if i in lib][:10] + [i for i in sorted(beat_pool, key=lambda k: -beat_pool[k]) if i in lib and i not in x["alts"] and i != x["clip"]][:4]
            sh["sea"] = [y for y in (item(i) for i in sea) if y]
            sh.update(snd(x["clip"]))
        s["speakers"] = sorted({u["who"] for u in s["subs"] if u["kind"] == "DIALOGUE"})
R["cast"] = cast
R["albums"] = [{"id": a["id"], "name": a["name"], "tracks": [{"title": t["title"], "url": R["site"] + __import__("urllib.parse").parse.quote(a["dir"] + "/" + t["file"])} for t in a["tracks"]]}
               for a in json.load(open(os.path.expanduser("~/Downloads/odyssey-halfworld/audio/albums.json")))["albums"]]
D = os.path.join(H, "sea"); os.makedirs(D, exist_ok=True)            # one file per book, so a phone fetches only the station it is on
for b in R["books"]: json.dump(b, open(os.path.join(D, f"b{b['n']:02d}.json"), "w"), separators=(",", ":"))
json.dump({"site": R["site"], "cast": R["cast"], "albums": R["albums"], "books": [{"n": b["n"], "title": b["title"]} for b in R["books"]]}, open(os.path.join(D, "index.json"), "w"), separators=(",", ":"))
if os.path.exists(os.path.join(H, "sea.json")): os.remove(os.path.join(H, "sea.json"))
print("cast", {k: len(v) for k, v in cast.items()}); print("sea per shot", round(float(np.mean([len(sh.get("sea", [])) for b in R["books"] for s in b["scenes"] for sh in s["shots"]])), 1))
