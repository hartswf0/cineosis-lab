"""Machine sign-affinity for every shot: how much each of the 45 signs' descriptions and exemplars
resemble the shot in CLIP space. NOT a reading — a pointer for where to look.

For each sign s:  text prototype  = mean CLIP text embedding of its shot_criteria + its search queries
                  image prototype = mean CLIP image embedding of its read shots (the editor's exemplars)
score(shot, s) = 0.5 * cos(shot, text_s) + 0.5 * cos(shot, image_s), z-scored per sign across the corpus
(so a sign that CLIP likes everywhere doesn't dominate), then softmax over the 45 signs.
Leave-one-out: a read shot is not compared with a prototype that includes itself.
Writes cache/affinity.json: id -> {"top": [[n, pct], ...8], "all": {n: pct}}.
"""
import glob, json, os
import numpy as np, torch, open_clip

LAB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LAB)
C = os.path.join(LAB, "cache")

def main():
    E = np.load(os.path.join(C, "emb.npy")); ids = json.load(open(os.path.join(C, "emb_ids.json")))
    row = {i: k for k, i in enumerate(ids)}
    g = [s for f in sorted(glob.glob(os.path.join(ROOT, "grounding", "g*.json"))) for s in json.load(open(f))]
    picks = json.load(open(os.path.join(ROOT, "picks.json")))
    ns = [str(s["n"]) for s in g]
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model = model.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
    Tp = []
    with torch.no_grad():
        for s in g:
            texts = [f"a film still: {s['shot_criteria'][:300]}"] + [f"a film still of {q}" for q in s["queries"]]
            t = model.encode_text(tok(texts, context_length=77).to(dev)); t = t / t.norm(dim=-1, keepdim=True)
            m = t.mean(0); Tp.append((m / m.norm()).cpu().numpy())
    Tp = np.stack(Tp)
    ex = {n: [row[c] for c, _ in picks.get(n, []) if c in row] for n in ns}
    St = E @ Tp.T                                    # shots x signs, text side
    Si = np.zeros_like(St)
    for j, n in enumerate(ns):
        rows = ex[n]
        if not rows: Si[:, j] = St[:, j]; continue
        P = E[rows]; tot = P.sum(0)
        proto = tot / np.linalg.norm(tot)
        Si[:, j] = E @ proto
        for r in rows:                               # leave-one-out for the exemplars themselves
            if len(rows) > 1:
                lo = tot - E[r]; Si[r, j] = E[r] @ (lo / np.linalg.norm(lo))
    S = 0.5 * St + 0.5 * Si
    Z = (S - S.mean(0)) / (S.std(0) + 1e-6)
    P = torch.softmax(torch.tensor(Z) * 1.2, dim=1).numpy()
    out = {}
    for k, i in enumerate(ids):
        order = np.argsort(-P[k])
        out[i] = {"top": [[ns[j], round(float(P[k, j]) * 100, 1)] for j in order[:8]],
                  "all": {ns[j]: round(float(P[k, j]) * 100, 1) for j in range(len(ns))}}
    json.dump(out, open(os.path.join(C, "affinity.json"), "w"))
    # sanity: how often does a read shot's own sign land in its top-5?
    hit = tot = 0
    for n in ns:
        for r in ex[n]:
            tot += 1; hit += n in [x[0] for x in out[ids[r]]["top"][:5]]
    print(f"affinity for {len(out)} shots; read shots with their sign in machine top-5: {hit}/{tot} ({100*hit/tot:.0f}%, chance {500/45:.0f}%)")

if __name__ == "__main__":
    main()
