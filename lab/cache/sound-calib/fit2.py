import sys, os, json, numpy as np
sys.path.insert(0, "/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab")
import sound_census as S
D = os.path.dirname(os.path.abspath(__file__)) + "/syn"
truth = json.load(open(D + "/truth.json"))
SIGN = {"speech": {"mod4": 1, "depth": 1, "lster": 1, "zcr_cv": 1, "steady": -1, "hp": -1, "beat": -1, "cstab": -1, "floor_rel": -1, "floor_hp": -1},
        "music": {"steady": 1, "hp": 1, "voiced": 1, "beat": 1, "cstab": 1, "depth": -1, "lster": -1, "zcr_cv": -1, "mod4": -1, "floor_hp": 1, "floor_tonal": 1, "floor_rel": 1}}
FILL = {"cstab": 0.6, "beat": 0.25, "steady": 0.2, "floor_rel": -20.0, "floor_hp": 0.5, "floor_tonal": 0.7}
def get(F, k, s):
    x = F[k][s]; x = FILL.get(k, 0.0) if x is None else x
    return min(x, 1.5) if k == "zcr_cv" else min(x, 2.0) if k == "depth" else x
def gate(F, s):  # 'is this tonal, voice-band sound at all' (hand-set; noise otherwise)
    return S.sig(20 * (get(F, "tonal", s) - 0.52)) * S.sig(25 * (0.22 - get(F, "flat", s))) * S.sig(40 * (get(F, "vfrac", s) - 0.12))
LAM = float(os.environ.get('LAM', 50))
rows = []
for f in os.listdir(D + "/cache"):
    rec = json.load(open(D + "/cache/" + f)); cid = rec["id"]; t = truth[cid]; F = rec.get("raw")
    if not F: continue
    fam = "".join(c for c in cid if not c.isdigit())
    for s in range(len(F["db"])):
        if F["mod4"][s] is None or F["db"][s] < S.SIL_DB: continue
        rows.append((cid, fam, t, F, s))
def fitc(kind, train, lam=LAM, it=4000, lr=0.2):
    ks = list(SIGN[kind]); sg = np.array([SIGN[kind][k] for k in ks])
    X = np.array([[get(F, k, s) for k in ks] for _, _, _, F, s in train]); 
    y = np.array([(t in ("speech", "mixed", "sung(music+speech)")) if kind == "speech" else (t not in ("speech",) and not t.startswith("noise")) for _, _, t, _, _ in train], float)
    mu, sd = X.mean(0), X.std(0) + 1e-9; Z = (X - mu) / sd
    w = np.zeros(len(ks)); b = 0.0; sw = np.where(y > 0, 0.5 / y.mean(), 0.5 / (1 - y.mean()))
    for _ in range(it):
        p = S.sig(Z @ w + b); g = (p - y) * sw
        w -= lr * (Z.T @ g / len(y) + lam * w / len(y)); b -= lr * g.mean()
        w = np.where(w * sg < 0, 0, w)            # sign constraint
    # convert to raw-feature weights: z = sum w (x-mu)/sd + b
    wr = w / sd; br = b - (w * mu / sd).sum()
    return dict(zip(ks, wr)), br
train_fams = lambda r: r[1] not in ("speech", "mixed") and not r[2].startswith("noise")
tr = [r for r in rows if train_fams(r)]
M = {k: fitc(k, tr) for k in ("speech", "music")}
for k, (w, b) in M.items(): print(k, {a: round(float(v), 2) for a, v in w.items()}, "b", round(float(b), 2))
def probs(F, s):
    gt = gate(F, s); out = []
    for k in ("speech", "music"):
        w, b = M[k]; out.append(gt * S.sig(sum(w[a] * get(F, a, s) for a in w) + b))
    return out
from collections import Counter, defaultdict
acc = defaultdict(list)
for cid, fam, t, F, s in rows:
    ps, pm = probs(F, s)
    lab = "mixed" if ps > .5 and pm > .5 else "speech" if ps > .5 else "music" if pm > .5 else "noise"
    exp = {"speech": "speech", "mixed": "mixed", "sung(music+speech)": "mixed"}.get(t, "noise" if t.startswith("noise") else "music")
    acc[fam + ("(train)" if train_fams((cid, fam, t)) else "(held)")].append((lab, exp))
for fam, v in sorted(acc.items()):
    c = Counter(l for l, _ in v); print(fam.ljust(18), f"acc {np.mean([l == e for l, e in v]):.2f}", "carries-speech", f"{np.mean([(l in ('speech','mixed')) == (e in ('speech','mixed')) for l, e in v]):.2f}", "carries-music", f"{np.mean([(l in ('music','mixed')) == (e in ('music','mixed')) for l, e in v]):.2f}", dict(c))
json.dump({k: [{a: float(x) for a, x in w.items()}, float(b)] for k, (w, b) in M.items()}, open(D + "/../model.json", "w"))
