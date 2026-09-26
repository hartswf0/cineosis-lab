"""Spine-cut: films built from the prompt spine, timed to her voice.

1. Time every spine element to the words it sets (the suite's word timings); the scenario storyboard
   (WGY, one per beat) fills the time no element covers.
2. Rank archive shots for each section: her image (CLIP image-image) + her line and the prompt
   (CLIP text-image), each z-scored over the archive.
3. Films:
   echo   the best archive shot for each section, repeats allowed
   clean  no shot used twice (assignment over the whole suite), then a continuity pass:
          no two neighbours from one source film, no wild visual jump; review.json overrides last
   quad   the top four distinct shots for each section, as a 2x2 grid
   (blend is built by blend_spinecut.py on top of this file's output)
Writes spinecut/spinecut-data.json.
"""
import json, os, re
import numpy as np, torch, open_clip
from scipy.optimize import linear_sum_assignment

H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
K = json.load(open(os.path.join(LAB, "bets/kernel-data.json")))
SP = json.load(open(os.path.join(LAB, "spine/spine-data.json")))
X = np.load(os.path.join(LAB, "spine/spine-emb.npy")).astype(np.float32)
E = np.load(os.path.join(LAB, "cache/emb.npy")); IDS = json.load(open(os.path.join(LAB, "cache/emb_ids.json")))
LABS = {s["id"]: s for s in json.load(open(os.path.join(LAB, "lab-data.json")))["shots"]}
tok = lambda s: re.findall(r"[a-z0-9']+", (s or "").lower().replace("’", "'"))

def elements():
    by = {}
    for r in SP["records"]:
        if r["src"] != "cinome" or not r.get("id") or r.get("k") is None: continue
        e = by.setdefault(r["id"], {"id": r["id"], "code": re.sub(r"\d+$", "", r["id"]), "n": int(re.search(r"\d+$", r["id"]).group()),
                                    "line": r.get("line"), "prompt": r.get("prompt"), "declared": r.get("image"), "syntagma": r.get("syntagma"),
                                    "function": r.get("function"), "vars": []})
        e["vars"].append({"k": r["k"], "thumb": r["thumb"], "fit": r.get("fit", 0)})
    return sorted(by.values(), key=lambda e: (e["code"], e["n"]))

def align(els):
    W = []   # the suite's word stream
    for l in K["lines"]:
        for w in l["words"]: W.append({"w": tok(w["w"])[0] if tok(w["w"]) else "", "t0": w["t0"], "t1": w["t1"], "film": l["film"], "line": l["id"]})
    words = [w["w"] for w in W]
    def best(tt, lo, hi):
        bestv, bp = 0, None
        for p in range(max(0, lo), min(len(W) - len(tt) + 1, hi)):
            m = sum(1 for i, t in enumerate(tt) if words[p + i] == t) / len(tt)
            if m > bestv: bestv, bp = m, p
        return bestv, bp
    codes = {}
    for e in els: codes.setdefault(e["code"], []).append(e)
    for code, es in codes.items():
        # which film is this code? vote with each element's best global match
        votes = {}
        for e in es:
            tt = tok(e["line"])
            if len(tt) >= 2:
                v, p = best(tt, 0, len(W))
                if v >= .75: votes[W[p]["film"]] = votes.get(W[p]["film"], 0) + 1
        if not votes: continue
        film = max(votes, key=votes.get); fw = [i for i, w in enumerate(W) if w["film"] == film]
        cur = fw[0]
        for e in es:
            tt = tok(e["line"])
            if not tt: continue
            v, p = best(tt, cur, min(fw[-1] + 1, cur + 90))
            if v < .6 or p is None:   # the spine may re-read a phrase: search the whole poem once
                v, p = best(tt, fw[0], fw[-1] + 1)
                if v < .75: continue
            else: cur = p + len(tt)
            e.update({"film": film, "t0": W[p]["t0"], "t1": W[p + len(tt) - 1]["t1"], "match": round(v, 2)})
    return [e for e in els if "t0" in e]

def sections(timed):
    films = K["films"]; dur = K["duration"]
    beats = K["beats"]; wgy = sorted([r for r in SP["records"] if r["src"] == "storyboard" and r.get("k") is not None], key=lambda r: r["id"])
    # one element per phrase, earliest first; drop an element that starts inside the previous one's phrase
    timed.sort(key=lambda e: (e["t0"], e["id"])); keep = []
    for e in timed:
        if keep and e["t0"] < keep[-1]["t1"] - .05: continue
        keep.append(e)
    S = []
    for i, e in enumerate(keep):
        f = next(f for f in films if f["n"] == e["film"])
        nxt = keep[i + 1]["t0"] if i + 1 < len(keep) and keep[i + 1]["film"] == e["film"] else f["t1"]
        S.append({"t0": e["t0"], "t1": min(nxt, e["t1"] + 2.5), "el": e})
    # the storyboard fills the rest, beat by beat
    out, t = [], 0.0
    for s in S + [{"t0": dur, "t1": dur}]:
        while s["t0"] - t > .6:
            b = next((j for j, bb in enumerate(beats) if bb["t0"] <= t + .01 < bb["t1"]), len(beats) - 1)
            end = min(s["t0"], beats[b]["t1"])
            r = wgy[min(b, len(wgy) - 1)]
            out.append({"t0": t, "t1": end, "el": {"id": r["id"], "code": "WGY", "line": r.get("line"), "prompt": r.get("prompt"), "declared": r.get("image"),
                                                    "syntagma": r.get("syntagma"), "function": r.get("function"), "vars": [{"k": r["k"], "thumb": r["thumb"], "fit": r.get("fit", 0)}], "board": True}})
            t = end
        if s["t1"] > s["t0"]: out.append(s); t = s["t1"]
    return [s for s in out if s["t1"] - s["t0"] > .05]

def main():
    els = elements(); timed = align(els)
    print(len(els), "elements,", len(timed), "timed to her words")
    S = sections(timed); print(len(S), "sections,", sum(1 for s in S if not s["el"].get("board")), "from the spine")
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); model = model.to(dev).eval(); tk = open_clip.get_tokenizer("ViT-B-32")
    def txt(ts):
        out = []
        with torch.no_grad():
            for b in range(0, len(ts), 128):
                t = model.encode_text(tk(ts[b:b + 128], context_length=77).to(dev)); out.append((t / t.norm(dim=-1, keepdim=True)).cpu().numpy())
        return np.concatenate(out)
    Tl = txt([f"a film still: {s['el'].get('line') or ''}" for s in S]); Tp = txt([s["el"].get("prompt") or s["el"].get("line") or "" for s in S])
    Xi = np.stack([X[s["el"]["vars"][0]["k"]] for s in S])
    z = lambda M: (M - M.mean(1, keepdims=True)) / (M.std(1, keepdims=True) + 1e-6)
    SC = z(Xi @ E.T) + .5 * z(Tl @ E.T) + .5 * z(Tp @ E.T)
    top = np.argsort(-SC, axis=1)[:, :40]
    # clean: each archive shot at most once over the whole suite
    pool = sorted(set(top.flatten().tolist()))
    col = {j: c for c, j in enumerate(pool)}
    cost = np.full((len(S), len(pool)), 1e3)
    for i in range(len(S)):
        for j in top[i]: cost[i, col[j]] = -SC[i, j]
    r, c = linear_sum_assignment(cost); clean = [None] * len(S)
    for i, cc in zip(r, c): clean[i] = pool[cc]
    used = set(clean)
    src = lambda j: LABS[IDS[j]]["slug"]
    fixes = 0
    for i in range(1, len(S)):     # continuity: neighbours from one film, or a wild jump, get the next free candidate
        a, b = clean[i - 1], clean[i]
        if src(a) == src(b) or float(E[a] @ E[b]) < .45:
            for j in top[i]:
                if j in used or src(j) == src(a) or float(E[a] @ E[j]) < .45: continue
                if SC[i, j] < SC[i, b] - 1.0: break
                used.discard(b); used.add(j); clean[i] = j; fixes += 1; break
    rv = os.path.join(H, "review.json")
    review = json.load(open(rv)) if os.path.exists(rv) else {}
    for i, s in enumerate(S):
        o = review.get(s["el"]["id"])
        if o and o.get("use") in IDS: clean[i] = IDS.index(o["use"])
    print("clean: continuity fixes", fixes, "review overrides", sum(1 for s in S if s["el"]["id"] in review))
    shots = {}
    def ref(j):
        i = IDS[j]; x = LABS[i]
        shots[i] = {"title": x["title"][:48], "year": x.get("year"), "slug": x["slug"], "thumb": x["video"].replace("/clips/", "/thumbnails/")[:-4] + ".jpg", "video": x["video"], "read_t": x.get("read_t"), "dur": round(x["end"] - x["start"], 2), "sg": (x.get("aff_top") or [[None]])[0][0]}
        return i
    out = []
    for i, s in enumerate(S):
        e = s["el"]; cand = [ref(j) for j in top[i][:12]]
        out.append({"t0": round(s["t0"], 3), "t1": round(s["t1"], 3), "id": e["id"], "board": bool(e.get("board")), "film": e.get("film"), "line": e.get("line"), "prompt": e.get("prompt"),
                    "declared": e.get("declared"), "syntagma": e.get("syntagma"), "function": e.get("function"), "hers": [v["thumb"] for v in e["vars"]],
                    "cand": cand, "score": [round(float(SC[i, j]), 2) for j in top[i][:12]],
                    "echo": cand[0], "clean": ref(clean[i]), "quad": cand[:4], "note": (review.get(e["id"]) or {}).get("note")})
    json.dump({"duration": K["duration"], "audio": "wygwyl/WYGWYL_Suite_Audio.mp3", "films": K["films"], "sections": out, "shots": shots},
              open(os.path.join(H, "spinecut-data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    ech = [s["echo"] for s in out]; print("echo distinct", len(set(ech)), "/", len(ech), "· clean distinct", len(set(s["clean"] for s in out)), "· shots", len(shots))

if __name__ == "__main__":
    main()
