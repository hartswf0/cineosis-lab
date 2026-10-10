"""MARKOV SAM · NORSE: the voices. For any line the filmmaker writes or says, the page finds the archival utterance that best answers it,
as the found Odyssey does (spoken_odyssey.py), with no model in the page.
  utterances  the archive's whole spoken sentences (cut where the speaker cut them, opening and closing in their own silence), the good
              ones only: a whole sentence, not begun before the clip began, heard clearly, 1.2 to 8 seconds, 4 to 24 words; 12,000 of them
  meaning     each utterance's sentence embedding (all-mpnet-base-v2, the Odyssey's own, from its cache), and the same for every word the
              page knows (wordmap.json's 4,000); in the page a line is the mean of its words' vectors
  space       both folded to 128 dimensions (PCA on the utterances), int8
Writes norse/voices.json (each utterance: its clip's video, from when to when, what is said, the film and year) and norse/voices.bin
(the words' vectors, then the utterances'). Run after wordmap.py.   usage: ../.venv/bin/python norse/voices.py"""
import json, os, re
import numpy as np
N = os.path.dirname(os.path.abspath(__file__)); OD = os.path.join(os.path.dirname(N), "odyssey")
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index("# ---- words: Homer's content words said")]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "voices_norse"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, UV, embed, lib = G["U"], G["UV"], G["embed"], G["lib"]
UV = UV / (np.linalg.norm(UV, axis=1, keepdims=True) + 1e-9)
good = [k for k, (i, t0, t1, text, n, conf, whole, cold) in enumerate(U)
        if whole and not cold and conf >= .72 and 1.2 <= t1 - t0 <= 8 and 4 <= n <= 24 and (lib.get(i) or {}).get("video") and not re.search(r"\b(fuck|shit)\b", text, re.I)]
rng = np.random.default_rng(7); seen = set(); pick = []
for k in rng.permutation(good):   # one utterance per exact text; at most six from any one clip, so many voices are heard
    i, text = U[k][0], U[k][3].strip().lower()
    if text in seen or sum(1 for j in pick[-400:] if U[j][0] == i) >= 6: continue
    seen.add(text); pick.append(int(k))
    if len(pick) >= 12000: break
print(len(good), "good utterances ·", len(pick), "kept", flush=True)
WM = json.load(open(os.path.join(N, "wordmap.json"))); words = WM["words"]
WVm = embed(words).astype(np.float32); WVm /= np.linalg.norm(WVm, axis=1, keepdims=True) + 1e-9
P = UV[pick]; mu = P.mean(0); _, _, Vt = np.linalg.svd(P - mu, full_matrices=False); B = Vt[:128].T
def fold(A): Z = (A - mu) @ B; Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9; return np.clip(np.round(Z * 127), -127, 127).astype(np.int8)
Wq, Uq = fold(WVm), fold(P)
# how well a line read as the mean of its words finds what the whole sentence would find (the sentence itself, read by mpnet, as truth)
tests = ["Fog lifts off the wooden domes at dawn", "His hands carve the statue", "I am nervous about all this", "The house is a sculpture", "Friends dancing at night", "What happens to the house after he is gone",
         "The hotel burned down", "We travelled to Nepal and Mongolia", "Waves under the cliff", "He built it all by hand"]
idx = {w: i for i, w in enumerate(words)}; S = embed(tests).astype(np.float32); S /= np.linalg.norm(S, axis=1, keepdims=True); St = fold(S).astype(np.float32)
agree = []
for t, st in zip(tests, St):
    ws = [w for w in (re.sub(r"[^a-z]", "", x.lower()) for x in t.split()) if w in idx and len(w) > 2]
    q = Wq[[idx[w] for w in ws]].astype(np.float32).mean(0); a = set(np.argsort(-(Uq @ st))[:20]); b = set(np.argsort(-(Uq @ q))[:20]); agree.append(len(a & b))
    print(f"  {t[:40]:40} → {U[pick[int(np.argmax(Uq @ q))]][3][:70]}")
print("agreement with the whole sentence (top 20):", agree)
out = [{"v": lib[U[k][0]]["video"], "t0": U[k][1], "t1": U[k][2], "s": U[k][3], "ti": (lib[U[k][0]].get("title") or "")[:60], "y": lib[U[k][0]].get("year")} for k in pick]
json.dump({"dim": 128, "n": len(out), "utts": out}, open(os.path.join(N, "voices.json"), "w"), separators=(",", ":"), ensure_ascii=False)
open(os.path.join(N, "voices.bin"), "wb").write(Wq.tobytes() + Uq.tobytes())
print("voices:", os.path.getsize(os.path.join(N, "voices.json")) // 1024, "KB ·", os.path.getsize(os.path.join(N, "voices.bin")) // 1024, "KB")
