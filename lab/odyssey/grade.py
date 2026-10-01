"""Grade each scene's archival cut against the Odyssey's own halfworld film: its three rendered keyframes per scene
(odyssey-halfworld renders/tiles/scene__<id>__t0.15|0.5|0.85.png) and its prompts (the staging direction of every turn,
atlas/spoken-lines). Two readings per shot, by OpenAI CLIP:
  render  how close the archival frame is to the halfworld frame at the same point of the scene (image to image)
  prompt  how well it shows what the scene's directions say happens (text to image)
A scene's grade is the mean over its shots, ranked against all 152 scenes (A top fifth ... E bottom fifth).
Writes grade.json.   usage: ../.venv/bin/python grade.py [path to odyssey-halfworld]"""
import glob, json, os, sys
import numpy as np, torch, open_clip
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); HW = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/odyssey-halfworld")
cuts = json.load(open(os.path.join(H, "cuts.json")))["cuts"]
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); X = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32); row = {i: n for n, i in enumerate(ids)}
M = os.path.join(os.path.dirname(H), "markov"); ml = json.load(open(os.path.join(M, "library.json")))
MX = np.fromfile(os.path.join(M, "emb.bin"), np.int8).reshape(-1, 512).astype(np.float32) * ml["scale"]; mrow = {s["id"]: n for n, s in enumerate(ml["shots"])}
def vec(i):
    if i in row: return X[row[i]]
    if i in mrow: v = MX[mrow[i]]; return v / (np.linalg.norm(v) + 1e-6)
dirs = {}
for f in glob.glob(os.path.join(HW, "atlas", "spoken-lines", "lines-*.json")):
    for tid, t in json.load(open(f)).items():
        if t.get("direction"): dirs.setdefault(tid[:10], []).append(t["direction"])
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m = m.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
out = {}
for sid, cut in cuts.items():
    tiles = sorted(glob.glob(os.path.join(HW, "renders", "tiles", f"scene__{sid}__t*.png")))
    with torch.no_grad():
        T = m.encode_image(torch.stack([pre(Image.open(p).convert("RGB")) for p in tiles]).to(dev)).float() if tiles else None
        T = (T / T.norm(dim=-1, keepdim=True)).cpu().numpy() if T is not None else None
        ds = dirs.get(sid, [])
        D = m.encode_text(tok(ds[:24]).to(dev)).float() if ds else None
        D = (D / D.norm(dim=-1, keepdim=True)).cpu().numpy() if D is not None else None
    shots = []; n = len(cut["shots"])
    for k, x in enumerate(cut["shots"]):
        v = vec(x["clip"]) if x["clip"] else None
        if v is None: shots.append(None); continue
        r = None
        if T is not None:   # the halfworld frame at the same point of the scene, and the best of the three
            near = min(range(len(T)), key=lambda j: abs((k + .5) / n - [.15, .5, .85][min(j, 2)]))
            r = round(float(max(T[near] @ v, (T @ v).max() - .01)), 3)
        p = round(float((D @ v).max()), 3) if D is not None else None
        shots.append({"render": r, "prompt": p})
    got = [s for s in shots if s]
    out[sid] = {"render": round(float(np.mean([s["render"] for s in got if s["render"] is not None])), 3) if any(s["render"] is not None for s in got) else None,
                "prompt": round(float(np.mean([s["prompt"] for s in got if s["prompt"] is not None])), 3) if any(s["prompt"] is not None for s in got) else None, "shots": shots, "tiles": len(tiles)}
def rank(key):
    v = sorted(x[key] for x in out.values() if x[key] is not None)
    for x in out.values(): x[key + "_pct"] = round(sum(1 for y in v if y <= x[key]) / len(v), 2) if x[key] is not None else None
rank("render"); rank("prompt")
for x in out.values():
    s = np.mean([y for y in (x["render_pct"], x["prompt_pct"]) if y is not None]) if (x["render_pct"] is not None or x["prompt_pct"] is not None) else 0
    x["score"] = round(float(s), 2); x["grade"] = "EDCBA"[min(4, int(s * 5))]
json.dump(out, open(os.path.join(H, "grade.json"), "w"), separators=(",", ":"))
import collections; print("grades", dict(sorted(collections.Counter(x["grade"] for x in out.values()).items())), "· tiles found for", sum(1 for x in out.values() if x["tiles"]), "scenes")
w = sorted(out.items(), key=lambda kv: kv[1]["score"])[:8]; print("lowest", [(k, v["grade"], v["render"], v["prompt"]) for k, v in w])
