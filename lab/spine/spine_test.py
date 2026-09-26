"""Two readings of the prompt spine, once embed_spine.py has run.

    python3 lab/spine/spine_test.py            # → lab/spine/spine.json

1. The listener. Can the label a shot was generated under be read back from the picture alone? Nearest-centroid
   classifier on CLIP image embeddings, trained on every poem but one and tested on the one left out. Chance is the
   majority class and a label-shuffled null. The same classifier on the prompt text (operativeEkphrasis) shows how much
   of the label the prompt already carried. Labels: syntagmaType (full string: the two "CS" classes are kept apart)
   and imageType.
2. The flip. Along each poem (ids in order, the first variant of each id), does the real order of two neighbouring
   shots beat the swap? Terms as in lab/syntagm/swap_test.py:
     V  visual continuity across the cuts;
     W  image · text of the line each shot sets (content);
     D  cut direction: cos(e_b − e_a, t_b − t_a) against the lines.
NM (no labels) is left out of 1 and kept in 2.
"""
import json, math, os, random, re, sys
from collections import Counter, defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "syntagm"))
from swap_test import binom_p, wilson


def load():
    I = np.load(os.path.join(HERE, "img-emb.npy")).astype(np.float32)
    ik = json.load(open(os.path.join(HERE, "img-keys.json")))
    T = np.load(os.path.join(HERE, "text-emb.npy")).astype(np.float32)
    tk = json.load(open(os.path.join(HERE, "text-keys.json")))
    img = {k: I[j] for j, k in enumerate(ik)}
    txt = {k: T[j] for j, k in enumerate(tk)}
    R = json.load(open(os.path.join(HERE, "total-cinome.json")))
    by = defaultdict(list)
    for r in R:
        if r.get("image_path") in img: by[r["id"]].append(r)
    shots = []
    for i, rs in by.items():
        r = sorted(rs, key=lambda r: r["image_path"])[0]
        shots.append({"id": i, "poem": re.match(r"[A-Z]+", i).group(), "n": int(re.search(r"\d+", i).group()),
                      "syn": r.get("syntagmaType"), "img_type": r.get("imageType"), "e": img[r["image_path"]],
                      "t_line": txt.get((r.get("content") or "").strip()), "t_prompt": txt.get((r.get("operativeEkphrasis") or "").strip())})
    return shots


def listener(shots, label, feat, rng):
    S = [s for s in shots if s[label] and s[feat] is not None]
    poems = sorted({s["poem"] for s in S})

    def run(labels):
        hit = 0
        for p in poems:
            tr = [(s, l) for s, l in zip(S, labels) if s["poem"] != p]
            cen = defaultdict(list)
            for s, l in tr: cen[l].append(s[feat])
            names = sorted(cen); C = np.stack([np.mean(cen[n], axis=0) for n in names])
            C /= np.linalg.norm(C, axis=1, keepdims=True)
            for s, l in zip(S, labels):
                if s["poem"] == p: hit += names[int(np.argmax(C @ s[feat]))] == l
        return hit / len(S)

    labels = [s[label] for s in S]
    acc = run(labels)
    null = []
    for _ in range(50):
        sh = labels[:]; rng.shuffle(sh); null.append(run(sh))
    maj = Counter(labels).most_common(1)[0][1] / len(S)
    return {"n": len(S), "classes": len(set(labels)), "acc": round(acc, 3), "majority": round(maj, 3),
            "null_mean": round(float(np.mean(null)), 3), "null_sd": round(float(np.std(null)), 3)}


def flips(shots):
    seqs = defaultdict(list)
    for s in shots: seqs[s["poem"]].append(s)
    res = {t: [0, 0] for t in "VWD"}

    def cut(t, a, b, sa, sb):
        if t == "V": return float(a["e"] @ b["e"])
        if t == "D":
            if sa["t_line"] is None or sb["t_line"] is None: return None
            dt = sb["t_line"] - sa["t_line"]
            if not dt.any(): return None
            de = b["e"] - a["e"]; return float(de @ dt / (np.linalg.norm(de) * np.linalg.norm(dt) + 1e-9))

    def win(t, seq, order, i):
        parts = [cut(t, order[k], order[k + 1], seq[k], seq[k + 1]) for k in (i - 1, i, i + 1) if 0 <= k < len(seq) - 1] if t != "W" else \
                [None if seq[k]["t_line"] is None else float(order[k]["e"] @ seq[k]["t_line"]) for k in (i, i + 1)]
        parts = [p for p in parts if p is not None]
        return sum(parts) if parts else None

    for seq in seqs.values():
        seq.sort(key=lambda s: s["n"])
        for i in range(len(seq) - 1):
            sw = seq[:]; sw[i], sw[i + 1] = sw[i + 1], sw[i]
            for t in "VWD":
                a, b = win(t, seq, seq, i), win(t, seq, sw, i)
                if a is None or b is None or abs(a - b) < 1e-9: continue
                res[t][0 if a > b else 1] += 1
    out = {}
    for t, (w, l) in res.items():
        n = w + l
        out[t] = {"wins": w, "decided": n, "acc": round(w / n, 3) if n else None, "ci95": wilson(w, n), "p": round(binom_p(w, n), 5) if n else None}
    return out


def main():
    shots = load()
    rng = random.Random(3)
    report = {"shots": len(shots), "listener": {}, "flip": flips(shots)}
    for label in ("syn", "img_type"):
        for feat in ("e", "t_prompt"):
            report["listener"][f"{label} from {'image' if feat == 'e' else 'prompt'}"] = listener(shots, label, feat, rng)
    json.dump(report, open(os.path.join(HERE, "spine.json"), "w"), indent=1)
    print(f"{len(shots)} shots with an image")
    for k, r in report["listener"].items():
        print(f"  {k:24} acc {r['acc']:.3f}  majority {r['majority']:.3f}  shuffled {r['null_mean']:.3f}±{r['null_sd']:.3f}  ({r['n']} shots, {r['classes']} classes)")
    for t, r in report["flip"].items():
        print(f"  flip {t}  {r['acc']} {r['ci95']} n={r['decided']} p={r['p']}")


if __name__ == "__main__":
    main()
