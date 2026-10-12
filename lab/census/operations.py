"""WHAT THE IMAGES DO. Reads census/uses.json against the whole embedded archive:
  1. one image-type vocabulary (CLIP, zero-shot, z-scored per type over the archive) for every embedded clip, used or not
  2. what each film uses vs what the archive holds: over- and under-used types, types never used
  3. what each recurring source is asked to do in each film (its jobs), and how alike those jobs are
  4. what follows what: image-type transitions in each film's running order, and what follows the recurring sources
  5. lab-data features (decade, colour, scale, sound, sign) for used vs unused shots
usage: lab/.venv/bin/python lab/census/operations.py   ->  lab/census/operations.json"""
import json, os, collections, numpy as np
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
J = lambda p: json.load(open(os.path.join(L, p)))

# ---- the archive as embedded (ViT-B-32 openai everywhere)
ids, X = [], []
e = np.load(os.path.join(L, "cache/emb.npy")); ids += J("cache/emb_ids.json"); X.append(e)
for lib, binf in (("markov/library.json", "markov/emb.bin"), ("odyssey/library.json", "odyssey/emb.bin")):
    m = J(lib); q = np.fromfile(os.path.join(L, binf), dtype=np.int8).reshape(m["n"], 512).astype(np.float32) * m["scale"]
    keep = [i for i, s in enumerate(m["shots"]) if s.get("kind", "archive") == "archive"]
    ids += [m["shots"][i]["id"] for i in keep]; X.append(q[keep])
X = np.concatenate(X); X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
first = {}
for i, k in enumerate(ids): first.setdefault(k, i)
ids = list(first); X = X[list(first.values())]; row = {k: i for i, k in enumerate(ids)}
print(len(ids), "archive clips embedded")

TYPES = {
 "face close-up": "a close-up of a person's face", "talking head": "a person talking to the camera in an interview",
 "speaker at podium": "a man giving a speech at a podium", "hearing / meeting": "people sitting at a table in a formal meeting or hearing",
 "crowd": "a large crowd of people", "protest / march": "people marching in a protest", "children": "children playing",
 "woman at home": "a woman working in a kitchen at home", "family": "a family together at home", "dancing": "people dancing",
 "hands at work": "close-up of hands doing a task", "factory work": "workers in a factory with machines", "office": "people working in an office",
 "classroom": "a teacher and students in a classroom", "hospital": "a doctor and patient in a hospital", "soldiers": "soldiers and military",
 "sport": "a sports game", "religion": "a church service or religious ceremony", "city street": "a busy city street with cars",
 "buildings": "tall buildings and architecture", "house exterior": "a house seen from outside", "room interior": "an empty room interior",
 "landscape": "a wide landscape with hills and mountains", "desert": "a desert", "water / sea": "the sea, waves or a river", "farm": "a farm field with crops",
 "forest": "trees in a forest", "aerial view": "an aerial view from an airplane", "sky / clouds": "the sky with clouds", "night": "a city at night with lights",
 "fire / smoke": "fire and smoke", "animals": "animals", "machine": "a large machine", "car / truck": "a car or truck on a road", "train": "a train",
 "aircraft / rocket": "an airplane or a rocket", "ship": "a ship at sea", "food": "food on a table", "text card": "a title card with text on a plain background",
 "map / diagram": "a map or a diagram", "animation": "a cartoon animation", "microscope / science": "a scientific image under a microscope",
 "screen / tv": "a television screen", "document / paper": "a newspaper or printed document", "abstract": "abstract shapes and light",
 "black / blank": "a black empty screen"}
import open_clip, torch
model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32")
def text(ts):
    with torch.no_grad(): t = model.encode_text(tok(ts)).float().numpy()
    return t / np.linalg.norm(t, axis=1, keepdims=True)
names = list(TYPES); T = text([f"a film still of {TYPES[k]}" for k in names])
S = X @ T.T; Z = (S - S.mean(0)) / (S.std(0) + 1e-9)
TYPE = Z.argmax(1)
tof = lambda k: names[TYPE[row[k]]] if k in row else None

uses = J("census/uses.json")
FILMS = ["Found Odyssey", "Markov Odyssey", "Norse Half Moon", "The Republic", "Found Republic", "WYGWYL"]
SEEN = ("picture", "place", "character")
def share(keys):
    c = collections.Counter(tof(k) for k in keys if k in row); n = sum(c.values()) or 1
    return {k: c[k] / n for k in names}, sum(c.values())
pool, npool = share(ids)
used_keys = [u["clip"] for u in uses if u["role"] in SEEN]
used, nused = share(used_keys)
per_film = {f: share([u["clip"] for u in uses if u["film"] == f and u["role"] in SEEN]) for f in FILMS}
cover = sum(1 for k in set(used_keys) if k in row) / max(1, len(set(used_keys)))
types = []
for k in names:
    types.append({"type": k, "pool": round(pool[k], 4), "used": round(used[k], 4), "ratio": round(used[k] / pool[k], 2) if pool[k] else None,
                  "films": {f: round(per_film[f][0][k], 4) for f in FILMS}})
types.sort(key=lambda x: -(x["ratio"] or 0))
print(f"type coverage of used picture clips: {cover:.0%}  ({nused} picture uses typed)")
print("OVER-USED:", [(t["type"], t["ratio"]) for t in types[:10]])
print("UNDER-USED:", [(t["type"], t["ratio"], f"{t['pool']:.1%} of archive") for t in types[-12:]])

# ---- what the job asks: one kind per use
def kind(u):
    j = u["job"] or ""
    if u["role"] == "voice": return "answers in its own voice"
    if u["role"] == "word": return "lends a word"
    if u["role"] == "character": return "cut out as a character"
    if u["role"] == "place": return "ground for the stage"
    if u["role"] == "playedby": return "voices a character"
    f = u["film"]
    if f == "Markov Odyssey": return "shot role " + j.split(":")[0].strip().lower()
    if f == "The Republic": return "establishes the place" if j.startswith("establishing") else "illustrates a named thing"
    if f == "Found Republic": return {"line": "pictures a character's line", "act": "illustrates the narration", "card": "under a title card", "title": "opens the episode"}.get(j.split(":")[0], "other")
    if f == "WYGWYL": return "wygwyl " + j.split(":")[0].strip()
    return "pictures the spoken line"
# ---- recurring sources: their jobs in each film and how alike those jobs are
by = collections.defaultdict(list)
for u in uses:
    if u["role"] != "word": by[u["src"]].append(u)
cen = J("census/census.json")
top = [s for s in cen["sources"] if s["afilms"] >= 4][:24]
jt_cache = {}
def jobvec(texts):
    new = [t for t in set(texts) if t not in jt_cache]
    for i in range(0, len(new), 256):
        for t, v in zip(new[i:i + 256], text([t[:300] for t in new[i:i + 256]])): jt_cache[t] = v
    return np.array([jt_cache[t] for t in texts])
def spread(us):
    js = [u["job"] for u in us if u["job"]]
    if len(js) < 2: return None
    V = jobvec(js); M = V @ V.T; n = len(js); return float((M.sum() - n) / (n * n - n))
# baseline: how alike two random jobs are
rng = np.random.default_rng(0); allj = [u["job"] for u in uses if u["job"] and u["role"] != "word"]
base = spread([{"job": j} for j in rng.choice(allj, 400, replace=False)])
recurring = []
for s in top:
    us = by[s["src"]]; ks = collections.Counter((u["film"], kind(u)) for u in us)
    ex = collections.defaultdict(list)
    for u in us:
        if u["job"] and len(ex[u["film"]]) < 3 and u["job"] not in ex[u["film"]]: ex[u["film"]].append(u["job"][:160])
    recurring.append({"title": s["title"], "src": s["src"], "afilms": s["afilms"], "alike": round(spread(us) or 0, 3),
                      "kinds": collections.Counter(kind(u) for u in us).most_common(), "by_film": {f: [k for (ff, k), c in ks.most_common() if ff == f] for f in FILMS if any(ff == f for ff, _ in ks)},
                      "jobs": dict(ex), "types": collections.Counter(tof(u["clip"]) for u in us if u["clip"] in row).most_common(3)})
print(f"\nhow alike two random jobs are: {base:.3f}")
for r in recurring[:12]: print(f"{r['alike']:.3f} {r['title'][:38]:38} kinds={r['kinds'][:4]} looks={r['types']}")

# ---- what follows what
seqs = {f: [u for u in sorted((u for u in uses if u["film"] == f and u["role"] == "picture" and u["seq"]), key=lambda u: u["seq"])] for f in FILMS}
trans, follow = {}, collections.defaultdict(collections.Counter)
glob = collections.Counter(); tcount = collections.Counter()
for f, sq in seqs.items():
    c = collections.Counter()
    for a, b in zip(sq, sq[1:]):
        ta, tb = tof(a["clip"]), tof(b["clip"])
        if a["src"] in {r["src"] for r in recurring}: follow[a["src"]][(f, tb)] += 1
        if ta and tb: c[(ta, tb)] += 1; glob[(ta, tb)] += 1; tcount[ta] += 1
    trans[f] = c
tot = sum(glob.values()) or 1; tb_count = collections.Counter(); [tb_count.update({b: n}) for (a, b), n in glob.items()]
patterns = []
for (a, b), n in glob.items():
    if n < 8: continue
    lift = (n / tcount[a]) / (tb_count[b] / tot)
    films = sum(1 for f in FILMS if trans[f].get((a, b)))
    patterns.append({"a": a, "b": b, "n": n, "lift": round(lift, 2), "films": films})
patterns.sort(key=lambda p: -p["lift"] * min(p["n"], 30))
same = sum(n for (a, b), n in glob.items() if a == b) / tot
print(f"\nsame type cut to same type: {same:.0%} of cuts")
print("PATTERNS:", [(p["a"], p["b"], p["n"], p["lift"], p["films"]) for p in patterns[:14]])
for r in recurring:
    fl = follow[r["src"]]; r["followed_by"] = [(f, t, n) for (f, t), n in fl.most_common(6)]

# ---- lab-data features, used vs unused
d = J("lab-data.json")["shots"]; usedset = set(used_keys)
def dist(rows, key):
    c = collections.Counter(key(r) for r in rows); n = sum(c.values()) or 1; return {str(k): round(v / n, 4) for k, v in c.most_common()}
U = [r for r in d if r["id"] in usedset]; N = [r for r in d if r["id"] not in usedset]
FEAT = {"decade": lambda r: r.get("decade"), "colour": lambda r: "black and white" if r.get("bw") else "colour", "scale": lambda r: r.get("scale"),
        "sound": lambda r: (r.get("audio") or {}).get("kind"), "sign": lambda r: (r.get("signs") or [{}])[0].get("n"),
        "subject": lambda r: ((r.get("subjects") or [{}])[0]).get("label")}
features = {k: {"used": dist(U, f), "unused": dist(N, f)} for k, f in FEAT.items()}
print(f"\nlab-data shots used: {len(U)} of {len(d)}")
for k in ("decade", "colour", "scale", "sound"): print(k, "USED", list(features[k]["used"].items())[:7], "\n   ", "ALL", list(features[k]["unused"].items())[:7])
signs_all = collections.Counter(str((r.get("signs") or [{}])[0].get("n")) for r in d); signs_used = collections.Counter(str((r.get("signs") or [{}])[0].get("n")) for r in U)
never_signs = sorted([s for s in signs_all if s != "None" and not signs_used[s]], key=lambda s: -signs_all[s])
print("signs never used (count in archive):", [(s, signs_all[s]) for s in never_signs])

# voices: who is heard (the Found Republic records CLAP gender per character voice)
sex = collections.Counter(v["sex"] or "?" for ep in J("republic/archive.json").values() for v in ep["voices"].values())
want = collections.Counter(v["want"] or "?" for ep in J("republic/archive.json").values() for v in ep["voices"].values())
decades_heard = collections.Counter((u["year"] // 10 * 10) if isinstance(u["year"], int) else None for u in uses if u["role"] == "voice")
# the same exact clip in three or more films, and what each film asked of it
cl = collections.defaultdict(list)
for u in uses:
    if u["clip"] and u["role"] != "word": cl[u["clip"]].append(u)
same_clip = []
for k, us in sorted(cl.items(), key=lambda kv: -len({u["film"] for u in kv[1]})):
    if len({u["film"] for u in us}) < 3: break
    seenf, jobs = set(), []
    for u in us:
        if u["film"] in seenf: continue
        seenf.add(u["film"]); jobs.append({"film": u["film"], "role": u["role"], "job": (u["job"] or "")[:180]})
    same_clip.append({"clip": k, "title": us[0]["title"], "video": us[0]["video"], "jobs": jobs})
selfnext = {}
for f, sq in seqs.items(): selfnext[f] = round(sum(a["src"] == b["src"] for a, b in zip(sq, sq[1:])) / max(1, len(sq) - 1), 3)
by_dec = lambda role: {str(k): v for k, v in sorted(collections.Counter((u["year"] // 10 * 10) if isinstance(u["year"], int) else 0 for u in uses if u["role"] == role).items())}
json.dump({"n_archive": len(ids), "same_clip": same_clip[:12], "self_next": selfnext, "dec_voice": by_dec("voice"), "dec_picture": by_dec("picture"), "types": types, "type_cover": cover, "recurring": recurring, "job_baseline": base,
           "patterns": patterns[:40], "same_type_cuts": same, "features": features, "never_signs": [(s, signs_all[s]) for s in never_signs],
           "voice_sex": dict(sex), "voice_want": dict(want), "decades_heard": {str(k): v for k, v in decades_heard.most_common()},
           "kinds_by_film": {f: collections.Counter(kind(u) for u in uses if u["film"] == f and u["role"] != "word").most_common() for f in FILMS}},
          open(os.path.join(H, "operations.json"), "w"), ensure_ascii=False, default=list)
print("\nvoice sex (Found Republic):", dict(sex), "wanted:", dict(want)); print("decades heard:", decades_heard.most_common(8))
print("kinds by film:"); [print(" ", f, collections.Counter(kind(u) for u in uses if u["film"] == f and u["role"] != "word").most_common(6)) for f in FILMS]
