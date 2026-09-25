import sys, os, json, numpy as np
from collections import Counter, defaultdict
sys.path.insert(0, "/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab")
import sound_census as S
SP = os.path.dirname(os.path.abspath(__file__)); D = SP + "/syn"
truth = json.load(open(D + "/truth.json"))
keys = ["mod4","depth","lster","zcr_cv","flat","tonal","cstab","hp","beat","vfrac","steady","voiced"]
res = defaultdict(Counter); secs = defaultdict(Counter)
verbose = "-v" in sys.argv
for f in sorted(os.listdir(D + "/cache")):
    rec = json.load(open(D + "/cache/" + f)); cid = rec["id"]; t = truth[cid]
    c = S.classify(rec); res[t][c["kind"]] += 1
    for k in c.get("timeline", []): secs[t][k] += 1
    if verbose:
        F = rec["raw"]; med = {k: np.nanmedian([v for v in F[k] if v is not None] or [np.nan]) for k in keys}
        print(cid.ljust(14), c["kind"].ljust(8), c["p"], " ".join(f"{k[:5]}={med[k]:.2f}" for k in keys))
for t in res: print(t.ljust(26), "clips:", dict(res[t]), " seconds:", dict(secs[t]))
# archive side
recs = S.load_all(); corpus = json.load(open(S.LAB + "/cache/corpus.json"))
cl = {cid: S.classify(r) for cid, r in recs.items()}
print("archive dist:", Counter(c["kind"] for c in cl.values()))
pre = [c for cid, c in cl.items() if (corpus.get(cid, {}).get("sourceYear") or 3000) < 1927 and c["kind"] not in ("none", "silence")]
print("pre-1927 w/ sound:", len(pre), Counter(c["kind"] for c in pre))
res2 = S.validate(cl, quiet=True); n = res2["n_compared"]
print(f"vs old labels strict {res2['strict']/n:.1%} lenient {res2['lenient']/n:.1%} coarse {res2['coarse']/n:.1%}", res2["confusion"])
