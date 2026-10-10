"""The film's own answers (storyboard.json, each memo line's av) drawn and described like every other voice: waveform, speed, who, how,
what is under it, by voicekinds.py's own methods.   usage: ../.venv/bin/python norse/answerkinds.py (after answers.py)"""
import json, os, sys
import numpy as np
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N)
src = open(os.path.join(N, "voicekinds.py")).read(); src = src[: src.index("eids = json.load")]
sys.argv = [sys.argv[0], "0"]; G = {"__file__": os.path.join(N, "voicekinds.py"), "__name__": "answerkinds"}; exec(compile(src, "voicekinds.py", "exec"), G)
seg, shape, VID, TX, LABELS = G["seg"], G["shape"], G["VID"], G["TX"], G["LABELS"]
eids = json.load(open(os.path.join(L, "odyssey", "cache", "ears", "ids.json"))); CL = np.load(os.path.join(L, "odyssey", "cache", "ears", "clap.npy")).astype(np.float32); erow = {i: n for n, i in enumerate(eids)}
CL /= np.linalg.norm(CL, axis=1, keepdims=True) + 1e-9; MU = {g: (CL[np.abs(CL).sum(1) > 0] @ T.T).mean(0) for g, T in TX.items()}
S = json.load(open(os.path.join(N, "storyboard.json"))); n = 0
for B in S["books"]:
    for l in B["lines"]:
        a = l.get("av")
        if not a: continue
        x, sr = seg(a)
        if x is not None: a["e"] = shape(x)
        a["ws"] = round(len(a["s"].split()) / max(.3, a["t1"] - a["t0"]), 1); r = erow.get(VID.get(a["v"]))
        if r is not None and np.abs(CL[r]).sum() > 0:
            v = CL[r] @ TX["vc"].T; d = v[0] - v[1]; a["vc"] = "child" if v[2] > max(v[0], v[1]) + .02 else "many" if v[3] > max(v[0], v[1]) + .03 else ("man" if d > .005 else "woman" if d < -.005 else "")
            for g in ("wy", "un"): a[g] = LABELS[g][int(((CL[r] @ TX[g].T) - MU[g]).argmax())][0]
        n += 1
json.dump(S, open(os.path.join(N, "storyboard.json"), "w"), separators=(",", ":"), ensure_ascii=False); print(n, "film answers drawn and described")
