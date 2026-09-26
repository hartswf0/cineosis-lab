"""The flip test: does the order a sequence was cut in beat the same two shots swapped?

    python3 lab/syntagm/swap_test.py            # → lab/syntagm/swap.json

For every adjacent pair (i, i+1) with a shot on each side, swap the two shots and keep everything else in place: the
words under each slot, the shots before and after. Each term scores the local window (the cuts i-1→i, i→i+1, i+1→i+2
and, for words, the two slots) both ways. The real order wins, loses or ties. Chance is 50% of the decided pairs.

Terms (all read from files the lab already has):
  V  visual continuity   cos(e_a, e_b) of CLIP image embeddings across each cut          cache/emb.npy
  S  sign held           both sides of a cut have the same top machine sign              lab-data.json aff_top
  F  forward in source   same source film, later in-point (Metz: chronology asserted)     clip in-points
  W  words under shot    e_shot · t_words for the two slots                               words-emb.npy (embed_words.py)
  D  cut direction       cos(e_b − e_a, t_b − t_a): the picture moves the way the words move
W and D need the word embeddings; without them they are reported as not run.

Sequences:
  poem     the four WYGWYL cuts (made by cutbastard/plan.py, a machine) and the forage cut (88 shots, one per beat).
           Words under a shot are the words her voice speaks inside it (bets/kernel-data.json alignment).
           Pairs never straddle a chapter seam.
  archive  the archive films' own order: runs of ≥4 lab shots that abut in their source (gap < 1 s). Edited by people.
           No words, so only V and S.
A permutation null (each sequence shuffled, 200 times) checks the test sits at 50% when order means nothing.
"""
import json, math, os, random
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
CUTS = ["suite", "scenes", "cineosis", "drift"]


def load_sequences():
    K = json.load(open(os.path.join(LAB, "bets", "kernel-data.json")))
    words = [w for L in K["lines"] for w in L["words"]]
    films = K["films"]

    def words_in(t0, t1):
        return " ".join(w["w"] for w in words if t0 <= (w["t0"] + w["t1"]) / 2 < t1)

    def film_at(t):
        for f in films:
            if f["t0"] <= t < f["t1"]:
                return f["n"]
        return films[-1]["n"]

    poem = []
    for c in CUTS:
        P = json.load(open(os.path.join(LAB, "wygwyl", "cuts", c, "patches.json")))
        poem.append({"name": c, "kind": "machine (plan.py)", "shots": [
            {"id": p["clip"]["id"], "t0": p["t0"], "t1": p["t1"], "film": p["chapter"], "src": p["clip"]["title"],
             "in": p["clip"]["in"], "words": words_in(p["t0"], p["t1"])} for p in P]})
    F = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Cut.json")))["shots"]
    poem.append({"name": "forage", "kind": "forage cut", "shots": [
        {"id": s["selected"], "t0": s["start"], "t1": s["end"], "film": film_at(s["start"]), "src": None, "in": None,
         "words": words_in(s["start"], s["end"])} for s in F if s.get("selected")]})

    D = json.load(open(os.path.join(LAB, "lab-data.json")))
    by = defaultdict(list)
    for s in D["shots"]:
        if s.get("start") is not None and s.get("end") is not None:
            by[s["title"]].append(s)
    archive = []
    for title, v in by.items():
        v.sort(key=lambda s: s["start"])
        run = [v[0]]
        for a, b in zip(v, v[1:]):
            if 0 <= b["start"] - a["end"] < 1.0:
                run.append(b)
            else:
                if len(run) >= 4: archive.append(run)
                run = [b]
        if len(run) >= 4: archive.append(run)
    archive = [{"name": r[0]["title"], "decade": r[0].get("decade"), "shots": [
        {"id": s["id"], "film": "0", "src": title, "in": s["start"], "words": ""} for s in r]} for r in archive]
    return {"poem": poem, "archive": archive, "shots": {s["id"]: s for s in D["shots"]}}


def binom_p(k, n):
    """Two-sided exact sign test."""
    if n == 0: return 1.0
    k = max(k, n - k)
    tail = sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


class Scorer:
    def __init__(self, data):
        E = np.load(os.path.join(LAB, "cache", "emb.npy")).astype(np.float32)
        ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
        E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
        self.E = {i: E[j] for j, i in enumerate(ids)}
        self.sign = {i: (s.get("aff_top") or [[None]])[0][0] for i, s in data["shots"].items()}
        self.T = {}
        wp = os.path.join(HERE, "words-emb.npy")
        if os.path.exists(wp):
            T = np.load(wp); keys = json.load(open(os.path.join(HERE, "words-keys.json")))
            self.T = {k: T[j] for j, k in enumerate(keys)}

    # a cut from shot a (in slot sa) to shot b (in slot sb)
    def cut(self, term, a, b, sa, sb):
        if term == "V":
            return float(self.E[a["id"]] @ self.E[b["id"]])
        if term == "S":
            return float(self.sign.get(a["id"]) is not None and self.sign.get(a["id"]) == self.sign.get(b["id"]))
        if term == "F":
            return float(a["src"] is not None and a["src"] == b["src"] and b["in"] > a["in"])
        if term == "D":
            ta, tb = self.T.get(sa["words"]), self.T.get(sb["words"])
            if ta is None or tb is None or sa["words"] == sb["words"]: return None
            de, dt = self.E[b["id"]] - self.E[a["id"]], tb - ta
            return float(de @ dt / (np.linalg.norm(de) * np.linalg.norm(dt) + 1e-9))
        return None

    def slot(self, term, shot, sl):
        if term == "W":
            t = self.T.get(sl["words"])
            return None if t is None else float(self.E[shot["id"]] @ t)
        return None

    def window(self, term, seq, order, i):
        """Score slots i-1 .. i+2 of a sequence whose slot k holds shot order[k]. None = the term cannot see it."""
        parts = []
        for k in (i - 1, i, i + 1):
            if 0 <= k and k + 1 < len(seq) and seq[k]["film"] == seq[k + 1]["film"]:
                parts.append(self.cut(term, order[k], order[k + 1], seq[k], seq[k + 1]))
        for k in (i, i + 1):
            parts.append(self.slot(term, order[k], seq[k]))
        parts = [p for p in parts if p is not None]
        return sum(parts) if parts else None


TERMS = {"V": "visual continuity", "S": "sign held", "F": "forward in source", "W": "words under shot",
         "D": "cut direction", "WD": "words + direction"}


def swap_counts(sc, seqs, terms, shuffle=None):
    res = {t: [0, 0, 0] for t in terms}             # wins, losses, ties
    for s in seqs:
        slots = s["shots"]
        order = list(slots)
        if shuffle:                                  # the null: shots shuffled within each chapter
            groups = defaultdict(list)
            for k, x in enumerate(slots): groups[x["film"]].append(k)
            for ks in groups.values():
                xs = [order[k] for k in ks]; shuffle.shuffle(xs)
                for k, x in zip(ks, xs): order[k] = x
        for i in range(len(slots) - 1):
            if slots[i]["film"] != slots[i + 1]["film"]: continue
            sw = list(order); sw[i], sw[i + 1] = sw[i + 1], sw[i]
            for t in terms:
                parts = list(t) if t == "WD" else [t]
                r = [sc.window(p, slots, order, i) for p in parts]
                w = [sc.window(p, slots, sw, i) for p in parts]
                if any(x is None for x in r + w):
                    continue
                d = sum(r) - sum(w)
                res[t][0 if d > 1e-9 else 1 if d < -1e-9 else 2] += 1
    return res


def summarise(res, null=None):
    out = {}
    for t, (w, l, ties) in res.items():
        n = w + l
        row = {"term": TERMS[t], "wins": w, "losses": l, "ties": ties, "decided": n,
               "acc": round(w / n, 3) if n else None, "ci95": wilson(w, n), "p": round(binom_p(w, n), 5) if n else None}
        if null and null.get(t):
            row["null_mean"], row["null_sd"] = round(float(np.mean(null[t])), 3), round(float(np.std(null[t])), 3)
        out[t] = row
    return out


def main():
    data = load_sequences()
    sc = Scorer(data)
    words_ok = bool(sc.T)
    poem_terms = ["V", "S", "F"] + (["W", "D", "WD"] if words_ok else [])
    rng = random.Random(7)
    report = {"words_embedded": words_ok, "poem": {}, "archive": {}}

    for s in data["poem"]:
        res = swap_counts(sc, [s], poem_terms)
        null = defaultdict(list)
        for _ in range(200):
            for t, (w, l, _) in swap_counts(sc, [s], poem_terms, shuffle=rng).items():
                if w + l: null[t].append(w / (w + l))
        report["poem"][s["name"]] = {"kind": s["kind"], "shots": len(s["shots"]),
                                    "with_words": sum(1 for x in s["shots"] if x["words"]), "terms": summarise(res, null)}

    arc = data["archive"]
    res = swap_counts(sc, arc, ["V", "S"])
    null = defaultdict(list)
    for _ in range(50):
        for t, (w, l, _) in swap_counts(sc, arc, ["V", "S"], shuffle=rng).items():
            if w + l: null[t].append(w / (w + l))
    report["archive"]["all"] = {"runs": len(arc), "shots": sum(len(r["shots"]) for r in arc), "terms": summarise(res, null)}
    by_dec = defaultdict(list)
    for r in arc: by_dec[r["decade"]].append(r)
    report["archive"]["by_decade"] = {str(d): {"runs": len(v), "terms": summarise(swap_counts(sc, v, ["V", "S"]))}
                                      for d, v in sorted(by_dec.items(), key=lambda kv: kv[0] or 0) if d}

    json.dump(report, open(os.path.join(HERE, "swap.json"), "w"), indent=1)
    fmt = lambda r: (f"{r['acc']:.3f} [{r['ci95'][0]:.2f}–{r['ci95'][1]:.2f}] n={r['decided']} p={r['p']:.4f}"
                     + (f"  null {r['null_mean']:.3f}±{r['null_sd']:.3f}" if "null_mean" in r else "")) if r["decided"] else "—"
    print(f"words embedded: {words_ok}")
    for name, v in report["poem"].items():
        print(f"\n{name} ({v['kind']}, {v['shots']} shots, {v['with_words']} with words)")
        for t, r in v["terms"].items(): print(f"  {t:2} {r['term']:20} {fmt(r)}")
    a = report["archive"]["all"]
    print(f"\narchive films' own order ({a['runs']} runs, {a['shots']} shots)")
    for t, r in a["terms"].items(): print(f"  {t:2} {r['term']:20} {fmt(r)}")
    for d, v in report["archive"]["by_decade"].items():
        r = v["terms"]["V"]; print(f"  {d}s  runs {v['runs']:3}  V {fmt(r)}")


if __name__ == "__main__":
    main()
