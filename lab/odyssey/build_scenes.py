"""The Odyssey's scenes, each answered by the forage. For every scene and every beat of it: the grounds (the place, nearly empty)
and the actions (what happens) that fit best, read by OpenAI CLIP against the beat itself and against the searches that found
them; for every figure the scene needs, the clips to cut it out of. Also a plain quality number per scene, so weak ones show.
Writes scenes.json (published) and report.json.   usage: ../.venv/bin/python build_scenes.py"""
import json, os, re
import numpy as np, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(H, "src", "scenes_in.json"))); SC = json.load(open(os.path.join(H, "src", "cineosis_score.json")))
sign = {s["id"]: s for s in SC["scenes"] + SC["dropped"]}
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); X = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32); row = {i: n for n, i in enumerate(ids)}
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def enc(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
NAMES = r"\b(Odysseus|Telemachus|Penelope|Athena|Zeus|Poseidon|Hermes|Calypso|Circe|Nausicaa|Alcinous|Arete|Menelaus|Helen|Nestor|Eumaeus|Eurycleia|Laertes|Antinous|Eurymachus|Amphinomus|Polyphemus|Tiresias|Elpenor|Eurylochus|Aeolus|Proteus|Irus|Melanthius|Melantho|Philoetius|Theoclymenus|Phemius|Demodocus|Mentor|Mentes|Argos|Pisistratus|Halitherses|Leiodes|Medon|Dolius|Eupithes|Anticleia|Achilles|Agamemnon|Heracles|Aegisthus|Orestes|Ajax)\b"
ROLE = {"Odysseus": "a bearded man", "Telemachus": "a young man", "Penelope": "a veiled woman", "Athena": "a tall woman", "Nausicaa": "a young woman", "Helen": "a beautiful woman", "Eurycleia": "an old woman", "Eumaeus": "an old herdsman", "Laertes": "an old farmer", "Polyphemus": "a huge man", "Argos": "an old dog", "Circe": "a woman", "Calypso": "a woman"}
# timelessness: footage that could pass for the ancient world (sea, rock, fields, animals, stone, robes, fire) over the plainly
# modern (suits, cars, offices, wires, signs). A light correction to fit, never a filter.
OLD = enc(["an ancient Greek scene", "people in robes and tunics", "a rocky Mediterranean landscape", "stone ruins and columns", "the open sea", "animals in a field", "firelight in a dark hall"])
NEW = enc(["people in modern suits and dresses", "cars and a paved street", "a modern office or corridor", "electric wires and signs", "a modern kitchen", "a factory with machines"])
ANC = (X @ OLD.T).max(1) - (X @ NEW.T).max(1)
def plain(t): return re.sub(NAMES, lambda k: ROLE.get(k.group(0), "a man"), t)
def asked(sid, loc_ids, roles):
    out = {}
    for c in clips.values():
        for key, role, q, rank, sc in c["asks"]:
            if (key == sid and role in roles) or (key in loc_ids and "ground" in roles):
                if c["id"] in row: out[c["id"]] = max(out.get(c["id"], 0), (sc or 0))
    return out
scenes, report = [], []
L = {l["name"]: l["id"] for l in json.load(open(os.path.join(H, "src", "locations_in.json")))}
Q = {}
for f in os.listdir(os.path.join(H, "src")):
    if f.startswith("q_b"): Q.update(json.load(open(os.path.join(H, "src", f))))
for s in S:
    sid = s["id"]; g = sign.get(sid, {}); locs = ["loc:" + L[p["name"]] for p in s["places"] if p["name"] in L]
    beats = s["beats"] or [s["title"]]; B = enc([plain(b) for b in beats])
    gq = Q.get(sid, {}).get("ground", []); GQ = enc(gq) if gq else None
    ground = asked(sid, locs, {"ground", "sign"}); action = asked(sid, [], {"action", "sign"})
    def rank(pool, vecs, extra=None, k=10):
        if not pool: return [], 0
        idx = list(pool); E = X[[row[i] for i in idx]]; sc = (E @ vecs.T).max(1)
        if extra is not None: sc = .6 * sc + .4 * (E @ extra.T).max(1)
        sc = sc + .15 * np.array([pool[i] for i in idx]) + .25 * ANC[[row[i] for i in idx]]        # the archive's own score, and timelessness, lightly
        o = np.argsort(-sc)[:k]; return [[idx[j], round(float(sc[j]), 3)] for j in o], float(sc[o[0]])
    bs = []; qual = []
    for n, b in enumerate(beats):
        gr, g0 = rank(ground, B[n:n + 1], GQ); ac, a0 = rank(action, B[n:n + 1]); bs.append({"text": b, "ground": gr, "action": ac}); qual.append(a0)
    figs = []
    for q in Q.get(sid, {}).get("figures", []):
        pool = {c["id"]: 0 for c in clips.values() if any(a[2] == q for a in c["asks"]) and c["id"] in row}
        r, _ = rank(pool, enc([q]), k=6); figs.append({"q": q, "clips": [x[0] for x in r]})
    p = g.get("primary") or {}
    scenes.append({"id": sid, "title": s["title"], "book": s["book"], "act": g.get("act"), "in_cut": g.get("in_cut"), "place": [p_["name"] for p_ in s["places"]], "at_sea": s["at_sea"],
                   "sign": {"n": p.get("n"), "symbol": p.get("symbol"), "name": p.get("name"), "operation": p.get("operation")}, "secondary": [x.get("symbol") for x in g.get("secondary", [])],
                   "key_beat": s.get("key_beat"), "beats": bs, "figures": figs})
    report.append([sid, s["title"], round(float(np.mean(qual)), 3) if qual else 0, len(ground), len(action)])
json.dump({"scenes": scenes, "clips": {i: {k: clips[i].get(k) for k in ("sourceTitle", "sourceYear", "sourceSlug", "startSeconds", "durationSeconds", "matchTimestampSeconds", "videoUrl", "thumbnailUrl", "colorMode")} for i in {x[0] for sc in scenes for b in sc["beats"] for x in b["ground"] + b["action"]} | {i for sc in scenes for f in sc["figures"] for i in f["clips"]}}},
          open(os.path.join(H, "scenes.json"), "w"), separators=(",", ":"))
report.sort(key=lambda r: r[2]); json.dump(report, open(os.path.join(H, "report.json"), "w"), indent=0)
print("scenes", len(scenes)); print("weakest", report[:8]); print("strongest", report[-5:])
