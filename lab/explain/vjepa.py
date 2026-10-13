"""V-JEPA 2 on the read shots: a model that learned from video itself (Meta, ViT-L, 64-frame clips at 256 px), so a shot becomes one
set of numbers made from its motion as well as its look. 32 frames spread across each clip -> mean of the encoder's patch features.
Then each shot's nearest neighbours by V-JEPA, beside its nearest by CLIP on the thumbnail: where moving and still disagree.
Writes cache/vjepa.npy + explain/vjepa.json.   usage: republic/.tts/bin/python lab/explain/vjepa.py"""
import json, os, time, warnings
import numpy as np, cv2, torch
warnings.filterwarnings("ignore")
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
from transformers import AutoModel, AutoVideoProcessor
dev = "mps" if torch.backends.mps.is_available() else "cpu"
proc = AutoVideoProcessor.from_pretrained("facebook/vjepa2-vitl-fpc64-256"); model = AutoModel.from_pretrained("facebook/vjepa2-vitl-fpc64-256").to(dev).eval()
shots = [s for s in json.load(open(os.path.join(LAB, "lab-data.json")))["shots"] if s.get("signs") and os.path.exists(os.path.join(LAB, "clips", s["id"] + ".mp4"))]
def frames(path, n=32):
    cap = cv2.VideoCapture(path); N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0); out = []
    for i in np.linspace(0, max(0, N - 2), n).round().astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i)); ok, f = cap.read()
        if ok: out.append(cv2.cvtColor(cv2.resize(f, (256, 256)), cv2.COLOR_BGR2RGB))
    while out and len(out) < n: out.append(out[-1])
    return np.stack(out) if out else None
V, ids, t0 = [], [], time.time()
for i, s in enumerate(shots):
    v = frames(os.path.join(LAB, "clips", s["id"] + ".mp4"))
    if v is None: continue
    x = proc(v, return_tensors="pt")["pixel_values_videos"].to(dev)
    with torch.no_grad(): f = model.get_vision_features(x).mean(1).float().cpu().numpy()[0]
    V.append(f / (np.linalg.norm(f) + 1e-9)); ids.append(s["id"])
    if i % 25 == 0: print(i, round(time.time() - t0), "s", flush=True)
V = np.array(V); np.save(os.path.join(LAB, "cache/vjepa.npy"), V); json.dump(ids, open(os.path.join(LAB, "cache/vjepa_ids.json"), "w"))
E = np.load(os.path.join(LAB, "cache/emb.npy")); eid = json.load(open(os.path.join(LAB, "cache/emb_ids.json"))); er = {k: i for i, k in enumerate(eid)}
C = E[[er[k] for k in ids]].astype(np.float32); C /= np.linalg.norm(C, axis=1, keepdims=True)
SV, SC = V @ V.T, C @ C.T; np.fill_diagonal(SV, -1); np.fill_diagonal(SC, -1)
nv, nc = np.argsort(-SV, 1)[:, :5], np.argsort(-SC, 1)[:5 * 0 + 5] if False else np.argsort(-SC, 1)[:, :5]
overlap = float(np.mean([len(set(nv[i]) & set(nc[i])) / 5 for i in range(len(ids))]))
# pairs V-JEPA calls close that CLIP's still frames call far: alike in how they move, not how they look
rv, rc = SV.argsort(1).argsort(1) / len(ids), SC.argsort(1).argsort(1) / len(ids)
pairs = sorted([(float(rv[i, j] - rc[i, j]), i, j) for i in range(len(ids)) for j in range(i + 1, len(ids))], reverse=True)
used, mv = set(), []
for d, i, j in pairs:
    if i in used or j in used: continue
    used |= {i, j}; mv.append({"a": ids[i], "b": ids[j], "vjepa": round(float(SV[i, j]), 3), "clip": round(float(SC[i, j]), 3)})
    if len(mv) == 6: break
json.dump({"model": "V-JEPA 2 ViT-L (facebook/vjepa2-vitl-fpc64-256), 32 frames per shot", "shots": len(ids), "seconds": round(time.time() - t0),
           "top5_overlap": round(overlap, 3), "move_alike": mv}, open(os.path.join(H, "vjepa.json"), "w"), indent=1)
print("done", len(ids), "shots", round(time.time() - t0), "s; top-5 neighbour overlap with CLIP", round(overlap, 3))
