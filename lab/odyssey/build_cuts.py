"""Assembly: each scene's cut, composed as a whole, not looked up shot by shot.

The spec (src/q_spec_*.json) gives every scene a palette, a world (the look all its shots share), and per beat a shot list:
role (WIDE MID CLOSE OBJ EMPTY), what the frame must show, its searches, its length, and (rarely) a figure to cut in.

1. Candidates per shot: the clips its own searches found, the scene's other finds, and its location's; up to 14 each.
2. Fit of a clip to a shot = what the frame must show (most), its searches, the beat, its role (an EMPTY shot is penalised for
   people, a CLOSE rewarded for a face...), the scene's palette, timelessness, and whether the clip is long enough.
3. The cut is chosen jointly (Viterbi over the shots): no clip twice in a scene, a cost for switching between black and white and
   colour, a small reward for staying with one source film across a cut (one world), a cost for jumping back to a film just left.
4. Figures: a shot only gets one when the spec asked for it, and the room places it only when a cut-out passes a fit gate.

Writes cuts.json (published) and cuts-report.json.   usage: ../.venv/bin/python build_cuts.py"""
import glob, json, os
import numpy as np, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__))
SPEC = {}
for f in sorted(glob.glob(os.path.join(H, "src", "q_spec_*.json"))): SPEC.update(json.load(open(f)))
S = {s["id"]: s for s in json.load(open(os.path.join(H, "src", "scenes_in.json")))}
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); X = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32); row = {i: n for n, i in enumerate(ids)}
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
cache = {}
def enc(ts):
    miss = [t for t in dict.fromkeys(ts) if t not in cache]
    for i in range(0, len(miss), 256):
        with torch.no_grad(): e = m.encode_text(tok(miss[i:i + 256])).float(); e = (e / e.norm(dim=-1, keepdim=True)).numpy()
        for t, v in zip(miss[i:i + 256], e): cache[t] = v
    return np.array([cache[t] for t in ts])
def z(v): return (v - v.mean()) / (v.std() + 1e-6)
OLD = enc(["an ancient Greek scene", "people in robes and tunics", "a rocky Mediterranean landscape", "stone ruins and columns", "the open sea", "animals in a field", "firelight in a dark hall"])
NEW = enc(["people in modern suits and dresses", "cars and a paved street", "a modern office or corridor", "electric wires and signs", "a modern kitchen", "a factory with machines"])
ANC = (X @ OLD.T).max(1) - (X @ NEW.T).max(1)
ROLE = {"EMPTY": z(X @ enc(["an empty landscape with no people", "an empty room"]).T.max(1) - X @ enc(["people", "a crowd of people"]).T.max(1)),
        "WIDE": z((X @ enc(["a wide view of a landscape", "a long shot of a place"]).T).max(1)),
        "MID": z((X @ enc(["people doing something, medium shot"]).T).max(1)),
        "CLOSE": z((X @ enc(["a close-up of a face", "a close-up of a person's face"]).T).max(1)),
        "OBJ": z((X @ enc(["a close-up of an object", "a close-up of hands holding something"]).T).max(1))}
SAT = json.load(open(os.path.join(H, "cache", "sat.json")))                 # measured colour (saturation.py): the archive's own label calls faded footage colour
BW = np.array([(SAT.get(i) if SAT.get(i) is not None else 0) < .13 for i in ids])
SRC = [clips.get(i, {}).get("sourceId") for i in ids]
DUR = np.array([clips.get(i, {}).get("durationSeconds") or 0 for i in ids])
asks = {}
for c in clips.values():
    for key, role, q, rank, sc in c["asks"]: asks.setdefault(key, {}).setdefault(role, set()).add(c["id"])
LOC = {l["name"]: "loc:" + l["id"] for l in json.load(open(os.path.join(H, "src", "locations_in.json")))}
out, report = {}, []
for sid, sp in SPEC.items():
    s = S.get(sid)
    if not s: continue
    mine = asks.get(sid, {}); scene_pool = set().union(*mine.values()) if mine else set()
    for p in s["places"]:
        for v in asks.get(LOC.get(p["name"], ""), {}).values(): scene_pool |= v
    scene_pool = [i for i in scene_pool if i in row]
    pal = sp.get("palette", "either"); world = sp.get("world", "")
    W = enc([world])[0] if world else None
    slots = []
    for bi, b in enumerate(sp["beats"]):
        beat = s["beats"][bi] if bi < len(s["beats"]) else ""
        for si, sh in enumerate(b.get("shots", [])):
            own = [i for i in mine.get(f"shot:{bi}:{si}", set()) if i in row]
            pool = list(dict.fromkeys(own + scene_pool)); r = np.array([row[i] for i in pool])
            if not len(r): slots.append((bi, si, sh, beat, [], [])); continue
            E = X[r]; see = enc([sh.get("see") or beat])[0]; qs = enc(sh.get("q") or [beat]); bt = enc([beat])[0]
            fit = .5 * (E @ see) + .2 * (E @ qs.T).max(1) + .15 * (E @ bt) + (.1 * (E @ W) if W is not None else 0)
            fit += .012 * ROLE.get(sh.get("role", "MID"), ROLE["MID"])[r] + .2 * ANC[r]
            fit += .008 * np.array([1 if i in own else 0 for i in pool])          # the shot's own searches found it
            if pal == "bw": fit -= .06 * (~BW[r])
            elif pal == "colour": fit -= .06 * BW[r]
            fit -= .03 * (DUR[r] < .6 * float(sh.get("sec") or 3))
            top = np.argsort(-fit)[:14]
            slots.append((bi, si, sh, beat, [pool[j] for j in top], [float(fit[j]) for j in top]))
    # Viterbi over the shots: the best whole cut, not the best shot each time
    N = len(slots); best = [dict() for _ in range(N)]
    for k, (bi, si, sh, beat, cand, fit) in enumerate(slots):
        for c, f in zip(cand, fit):
            if k == 0 or not best[k - 1]: best[k][c] = (f, None, (c,)); continue
            opts = []
            for pc, (pv, _, path) in best[k - 1].items():
                if c in path: continue
                t = 0.0; a, b_ = row[pc], row[c]
                if BW[a] != BW[b_]: t -= .04
                if SRC[a] == SRC[b_]: t += .015
                elif SRC[b_] in {SRC[row[x]] for x in path[-4:-1]}: t -= .01
                opts.append((pv + f + t, pc, path + (c,)))
            if opts: v, pc, path = max(opts); best[k][c] = (v, pc, path)
        best[k] = dict(sorted(best[k].items(), key=lambda kv: -kv[1][0])[:40])   # a beam, so paths stay tractable
    last = next((b for b in reversed(best) if b), None)
    path = max(last.values())[2] if last else ()
    shots = []; pi = 0
    for k, (bi, si, sh, beat, cand, fit) in enumerate(slots):
        if not cand: shots.append({"beat": bi, "role": sh.get("role"), "see": sh.get("see"), "sec": sh.get("sec"), "clip": None, "alts": [], "figure": sh.get("figure")}); continue
        c = path[pi] if pi < len(path) else cand[0]; pi += 1
        cl = clips[c]
        shots.append({"beat": bi, "role": sh.get("role"), "see": sh.get("see"), "sec": sh.get("sec"), "clip": c, "fit": round(fit[cand.index(c)] if c in cand else 0, 3),
                      "in": round(max(0, (cl.get("matchTimestampSeconds") or cl["startSeconds"]) - cl["startSeconds"]), 2), "alts": [x for x in cand if x != c][:10], "figure": sh.get("figure")})
    got = [x for x in shots if x["clip"]]
    bwn = sum(BW[row[x["clip"]]] for x in got); srcs = len({SRC[row[x["clip"]]] for x in got})
    out[sid] = {"palette": pal, "world": world, "shots": shots}
    report.append({"id": sid, "title": s["title"], "shots": len(shots), "filled": len(got), "fit": round(float(np.mean([x["fit"] for x in got])) if got else 0, 3),
                   "bw": round(bwn / max(1, len(got)), 2), "films": srcs, "figures": sum(1 for x in shots if x["figure"])})
used = {x["clip"] for v in out.values() for x in v["shots"] if x["clip"]} | {a for v in out.values() for x in v["shots"] for a in x["alts"]}
json.dump({"cuts": out}, open(os.path.join(H, "cuts.json"), "w"), separators=(",", ":"))
report.sort(key=lambda r: r["fit"]); json.dump(report, open(os.path.join(H, "cuts-report.json"), "w"), indent=0)
print("scenes", len(out), "shots", sum(r["shots"] for r in report), "figures", sum(r["figures"] for r in report))
print("mean fit", round(float(np.mean([r["fit"] for r in report])), 3), "· palette held", round(float(np.mean([max(r["bw"], 1 - r["bw"]) for r in report])), 2), "· films per scene", round(float(np.mean([r["films"] for r in report])), 1))
print("weakest", [(r["id"], r["fit"]) for r in report[:6]])
