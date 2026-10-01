"""The router: every archive clip the lab holds, sent to the vertebra it belongs to, cut the way that vertebra's syntagma asks.

    python3 lab/syzygy/route.py        # after build_vertebrae.py → lab/syzygy/routing.json, ROUTING.md
    python3 lab/syzygy/build_lanes.py  # then puts the route on the page as the "archive" lane

The pool is every clip in lab/markov/library.json and lab/odyssey/all/library.json (36,144 clips, OpenAI CLIP ViT-B/32).
The vertebrae speak LAION CLIP (the spine's images in lab/spine/spine-emb.npy, words through the Shannon text tower in
lab/shannon). The 15,149 clips held in both readings (lab/cache/emb.npy ↔ lab/markov/emb.bin) give a ridge map from
LAION to OpenAI; the map is checked on 1,500 held-out clips (does the mapped vector find its own clip?) and reported.

1. What fits (affinity). Each vertebra asks with its generated image (mapped) and, half as loud, with its words (the
   prompt's operativeEkphrasis and her line, mapped). Both z-scored over the pool; the best 40 clips are candidates.
2. How it is cut (the rule of the vertebra's syntagma, scored on the cut into it from the clip before):
     Descriptive (DS)        one space, things side by side: the next clip looks like the last (CLIP cosine), any source.
     Chronological (CS)      time goes on: the same film, later in it; else plain continuity.
     Action-Image            the action carries on: the same film, later; medium and long shots.
     Perception-Image        what is seen next: close continuity.
     Affection-Image         the face: close-ups.
     Crystal (CS) · Recollection-Image · Flashback
                             the past comes back: a clip already used, 2–12 vertebrae back (crystal, recollection) or
                             further (flashback).
     Thematic Montage (TM)   ideas, not places: a different film, unlike the last to look at.
     Autonomous (AS)         one shot holds: the same clip goes on.
     Sonsign                 a pure optical and sound situation: a wide, held view.
   Every cut also carries the direction term of the flip test (lab/syntagm/SWAP.md): the step from one clip to the next
   should point the way the step from one vertebra's words to the next points.
3. The path. A beam search (24 paths) over the vertebrae in clock order keeps the best total of affinity + rule +
   direction, less a reuse penalty: 2 + 0.6 per earlier use for a clip used before, 0.6 per use when the rule calls it
   back. Only an autonomous shot may hold the clip before it; for every other rule the same clip twice is not a cut. That is the Bellman backup:
   each pick is worth what it is worth now plus what it leaves the cuts after it.
4. Checks (ROUTING.md): how often each rule is realised by the route against the affinity-only pick (the best clip for
   each vertebra on its own), and how much affinity the route gives up to cut that way.
"""
import json, os, re
from collections import Counter, defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
K, BEAM = 40, 24
nrm = lambda A: A / (np.linalg.norm(A, axis=-1, keepdims=True) + 1e-9)


def text_tower():
    import onnxruntime as ort, open_clip
    M = json.load(open(os.path.join(LAB, "shannon", "text-model.json")))
    s = ort.InferenceSession(b"".join(open(os.path.join(LAB, "shannon", p), "rb").read() for p in M["parts"]))
    tok = open_clip.get_tokenizer("ViT-B-32")
    return lambda xs: np.concatenate([s.run(None, {"tokens": tok(xs[i:i + 64]).numpy()})[0] for i in range(0, len(xs), 64)])


def bridge():
    L = np.load(os.path.join(LAB, "cache", "emb.npy")).astype(np.float32); ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
    M = json.load(open(os.path.join(LAB, "markov", "library.json")))["shots"]
    O = np.fromfile(os.path.join(LAB, "markov", "emb.bin"), dtype=np.int8).reshape(-1, 512).astype(np.float32)
    mi = {s["id"]: k for k, s in enumerate(M)}
    pr = [(j, mi[i]) for j, i in enumerate(ids) if i in mi]
    X, Y = nrm(L[[a for a, _ in pr]]), nrm(O[[b for _, b in pr]])
    p = np.random.default_rng(0).permutation(len(X)); te, tr = p[:1500], p[1500:]
    fit = lambda idx: np.linalg.solve(X[idx].T @ X[idx] + np.eye(512), X[idx].T @ Y[idx])
    W = fit(tr); S = nrm(X[te] @ W) @ Y[te].T; r = (S > S.diagonal()[:, None]).sum(1)
    check = {"pairs": len(X), "held_out": len(te), "top1": round(float((r == 0).mean()), 3), "top10": round(float((r < 10).mean()), 3)}
    return fit(np.arange(len(X))), check


def pool():
    shots, E = [], []
    for lib, emb in (("markov", "emb.bin"), (os.path.join("odyssey", "all"), "emb.bin")):
        D = json.load(open(os.path.join(LAB, lib, "library.json")))
        X = np.fromfile(os.path.join(LAB, lib, emb), dtype=np.int8).reshape(-1, 512).astype(np.float32)
        seen = {s["id"] for s in shots}
        for k, s in enumerate(D["shots"]):
            if s["id"] in seen: continue
            shots.append(s); E.append(X[k])
    return shots, nrm(np.stack(E))


def rule_of(label):
    l = (label or "").lower()
    for key, name in (("descriptive", "DS"), ("chronological", "CS"), ("crystal", "CRYSTAL"), ("action", "ACTION"),
                      ("perception", "PERCEPTION"), ("affection", "AFFECTION"), ("recollection", "RECALL"),
                      ("flashback", "FLASHBACK"), ("thematic", "TM"), ("autonomous", "AS"), ("sonsign", "SONSIGN")):
        if key in l: return name
    return None


WIDE, CLOSE = {"long shot", "extreme long shot"}, {"close-up", "extreme close-up"}


def rule_score(rule, c, prev, path_ids, back):
    """How well the cut prev → c realises the rule (0..1), and whether it does (bool)."""
    if rule is None or prev is None: return 0.0, None
    if rule != "AS" and c["id"] == prev["id"]: return 0.0, False       # only an autonomous shot may hold the clip
    vis = float(c["e"] @ prev["e"])
    same_src, later = c["src"] == prev["src"], c["src"] == prev["src"] and (c["st"] or 0) > (prev["st"] or 0)
    if rule == "DS": return max(0.0, (vis - 0.6) / 0.3), vis > 0.75
    if rule in ("CS", "ACTION"):
        s = 1.0 if later else 0.3 * max(0.0, (vis - 0.6) / 0.3)
        if rule == "ACTION" and c["scale"] in WIDE | {"medium shot"}: s += 0.3
        return s, later
    if rule == "PERCEPTION": return max(0.0, (vis - 0.65) / 0.25), vis > 0.8
    if rule == "AFFECTION": return (1.0 if c["scale"] in CLOSE else 0.0), c["scale"] in CLOSE
    if rule == "SONSIGN": return (1.0 if c["scale"] in WIDE else 0.0), c["scale"] in WIDE
    if rule == "TM": ok = not same_src and vis < 0.7; return (1.0 if ok else 0.0), ok
    if rule == "AS": return (1.0 if c["id"] == prev["id"] else 0.0), c["id"] == prev["id"]
    if rule in ("CRYSTAL", "RECALL", "FLASHBACK"):
        lo, hi = (2, 12) if rule != "FLASHBACK" else (13, 10 ** 6)
        ok = any(lo <= len(path_ids) - j <= hi for j in back.get(c["id"], ()))
        return (1.0 if ok else 0.0), ok
    return 0.0, None


def main():
    V = sorted(json.load(open(os.path.join(HERE, "vertebrae.json")))["vertebrae"], key=lambda v: (v["t0"], v["t1"]))
    SD = json.load(open(os.path.join(LAB, "spine", "spine-data.json")))
    SE = nrm(np.load(os.path.join(LAB, "spine", "spine-emb.npy")).astype(np.float32))
    kth = {r["thumb"]: r["k"] for r in SD["records"]}
    W, check = bridge()
    shots, P = pool()
    print(f"bridge {check} · pool {len(shots)} clips")
    enc = text_tower()

    q_img, q_txt, rules, labels = [], [], [], []
    for v in V:
        th = (v.get("image") or [{}])[0].get("thumb") if v["kind"] == "spine" else ((v["beat"]["board"] or [{}])[0].get("thumb"))
        k = kth.get(th)
        q_img.append(SE[k] if k is not None else None)
        it = v.get("intended") or {}
        label = it.get("syntagmaType") if v["kind"] == "spine" else ((v["beat"]["board"] or [{}])[0].get("syntagma"))
        words = " ".join(x for x in (it.get("operativeEkphrasis"), v["clock"].get("words"), v["beat"].get("title")) if x)
        q_txt.append(words or v["beat"].get("title") or ""); rules.append(rule_of(label)); labels.append(label)
    T = nrm(enc(q_txt))
    QI = np.stack([nrm(q @ W) if q is not None else np.zeros(512, np.float32) for q in q_img]); QT = nrm(T @ W)
    z = lambda S: (S - S.mean(1, keepdims=True)) / (S.std(1, keepdims=True) + 1e-9)
    A = np.zeros((len(V), len(shots)), np.float32)
    for i in range(0, len(V), 64):
        si, st = QI[i:i + 64] @ P.T, QT[i:i + 64] @ P.T
        has = np.array([q is not None for q in q_img[i:i + 64]])[:, None]
        A[i:i + 64] = np.where(has, z(si) + 0.5 * z(st), z(st))
    Q = nrm(np.where(np.array([q is not None for q in q_img])[:, None], QI + 0.5 * QT, QT))
    cand = np.argsort(-A, axis=1)[:, :K]

    C = lambda j: {"j": int(j), "id": shots[j]["id"], "src": shots[j].get("src"), "st": shots[j].get("st"), "scale": shots[j].get("scale"), "e": P[j]}
    # beam: (score, picks[list of j], back{id: [positions]}, parts)
    beams = [(0.0, [], {}, [])]
    for i, v in enumerate(V):
        rule = rules[i]; nxt = []
        for sc, picks, back, parts in beams:
            prev = C(picks[-1]) if picks else None
            opts = list(cand[i])
            if rule in ("AS",) and picks: opts.append(picks[-1])
            if rule in ("CRYSTAL", "RECALL", "FLASHBACK"): opts += picks[-40:]
            for j in dict.fromkeys(opts):
                c = C(j); a = float(A[i, j])
                r, ok = rule_score(rule, c, prev, picks, back)
                d = 0.0
                if prev is not None and i > 0:
                    de, dq = c["e"] - prev["e"], Q[i] - Q[i - 1]
                    if np.linalg.norm(de) > 1e-6 and np.linalg.norm(dq) > 1e-6: d = float(de @ dq / (np.linalg.norm(de) * np.linalg.norm(dq)))
                held = rule == "AS" and prev is not None and c["id"] == prev["id"]
                n = len(back.get(c["id"], ()))
                reuse = 0.0 if held or not n else (0.6 * n if ok else 2.0 + 0.6 * n)   # a callback is cheap once, dear often
                s = a + 1.5 * r + 1.0 * d - reuse
                nxt.append((sc + s, picks + [j], back, parts + [(a, r, d, ok)], c["id"]))
        nxt.sort(key=lambda x: -x[0]); beams, keep = [], set()
        for sc, picks, back, parts, cid in nxt:
            key = tuple(picks[-3:])
            if key in keep: continue
            keep.add(key)
            b = {k: list(x) for k, x in back.items()}; b.setdefault(cid, []).append(len(picks) - 1)
            beams.append((sc, picks, b, parts))
            if len(beams) == BEAM: break
    _, picks, _, parts = beams[0]

    # the affinity-only pick, for the checks
    greedy = [int(cand[i][0]) for i in range(len(V))]
    def realised(seq):
        out, back = defaultdict(lambda: [0, 0]), {}
        for i, j in enumerate(seq):
            if i:
                _, ok = rule_score(rules[i], C(j), C(seq[i - 1]), seq[:i], back)
                if ok is not None: out[rules[i]][0] += bool(ok); out[rules[i]][1] += 1
            back.setdefault(shots[j]["id"], []).append(i)
        return out
    R, G = realised(picks), realised(greedy)
    aff_route = float(np.mean([A[i, j] for i, j in enumerate(picks)])); aff_greedy = float(np.mean([A[i, j] for i, j in enumerate(greedy)]))
    films = Counter(shots[j].get("src") for j in picks)

    def clip(j, t0, t1):
        s = shots[j]; dur = float(s.get("dur") or 8); L = t1 - t0
        start = max(0.0, min(float(s.get("in") or 0) - L / 2, dur - L)) if L < dur else 0.0
        th = s.get("thumb") or ""
        if not th.startswith("http"): th = s["video"].replace("/clips/", "/thumbnails/").rsplit(".", 1)[0] + ".jpg" if "/clips/" in s["video"] else None
        return {"id": s["id"], "title": s.get("title"), "year": s.get("year"), "src": s.get("src"), "coll": s.get("coll", "markov"),
                "scale": s.get("scale"), "video": s["video"], "thumb": th, "dur": round(dur, 2), "start": round(start, 2)}
    out = []
    for i, v in enumerate(V):
        t1 = min(v["t1"], V[i + 1]["t0"]) if i + 1 < len(V) and V[i + 1]["t0"] > v["t0"] else v["t1"]
        a, r, d, ok = parts[i]
        out.append({"v": v["id"], "kind": v["kind"], "t0": round(v["t0"], 3), "t1": round(max(t1, v["t0"] + 0.2), 3),
                    "syntagma": labels[i], "rule": rules[i], "realised": ok, "fit": round(a, 2), "rule_score": round(r, 2), "direction": round(d, 2),
                    "clip": clip(picks[i], v["t0"], t1), "alts": [shots[j]["id"] for j in cand[i][:6] if j != picks[i]][:5]})
    json.dump({"bridge": check, "pool": len(shots), "beam": BEAM, "candidates": K,
               "realised": {k: {"route": R[k], "affinity_only": G.get(k, [0, 0])} for k in R},
               "fit": {"route": round(aff_route, 3), "affinity_only": round(aff_greedy, 3)},
               "films": len(films), "clips": len(set(picks)), "route": out},
              open(os.path.join(HERE, "routing.json"), "w"), ensure_ascii=False, separators=(",", ":"))

    rows = "\n".join(f"| {k} | {R[k][0]}/{R[k][1]} ({R[k][0] / max(1, R[k][1]):.0%}) | {G.get(k, [0, 0])[0]}/{G.get(k, [0, 0])[1]} ({G.get(k, [0, 0])[0] / max(1, G.get(k, [0, 0])[1]):.0%}) |" for k in sorted(R))
    md = f"""# Routing: archive clips to vertebrae

Made by `route.py` (read its docstring for the method). {len(V)} vertebrae, a pool of {len(shots):,} archive clips.

**The bridge.** A ridge map from LAION CLIP to OpenAI CLIP, fitted on the {check['pairs']:,} clips read both ways. On
{check['held_out']:,} held-out clips the mapped vector finds its own clip first {check['top1']:.0%} of the time and in the top ten
{check['top10']:.0%}. The map is fitted on images; words go through it too, which is weaker, so words count half.

**The route** uses {len(set(picks))} different clips from {len(films)} films. Mean fit (z-score of affinity over the pool)
{aff_route:.2f}, against {aff_greedy:.2f} for the affinity-only pick: what the route gives up to cut the way the syntagmas ask.

How often each rule is realised on the cut into its vertebra:

| rule | route | affinity only |
|---|---|---|
{rows}

What this does not show: that the cuts read as their syntagmas to a viewer. The rules are operational stand-ins (same
film later in it for chronological; a returning clip for crystal and recollection; close-ups for affection). A screening
says the rest.
"""
    open(os.path.join(HERE, "ROUTING.md"), "w").write(md)
    print(md)


if __name__ == "__main__":
    main()
