"""The actual numbers the models put down for each shot, so the riverbed (made.js) can show them instead of describing them.
  vec-pic.i8   CLIP ViT-B/32 image embedding, 512 per shot
  vec-snd.i8   CLAP audio embedding, 512 per shot (all zeros: never heard)
Row i is lab-data.json's shot i; each row is scaled to -127..127 (the direction is what CLIP and CLAP compare, not the size).
The page fetches one row with an HTTP Range request: 512 bytes, not the file.   usage: lab/.venv/bin/python lab/made_vec.py"""
import json, os
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); J = lambda p: json.load(open(os.path.join(H, p)))
order = [s["id"] for s in J("lab-data.json")["shots"]]
def write(X, ids, name):
    row = {k: i for i, k in enumerate(ids)}; out = np.zeros((len(order), 512), np.int8)
    for j, k in enumerate(order):
        if k in row: x = X[row[k]].astype(np.float32); out[j] = np.round(x / (np.abs(x).max() + 1e-9) * 127).astype(np.int8)
    out.tofile(os.path.join(H, name)); print(name, sum(1 for k in order if k in row), "shots", os.path.getsize(os.path.join(H, name)) // 1024, "KB")
write(np.load(os.path.join(H, "cache/emb.npy")), J("cache/emb_ids.json"), "vec-pic.i8")
snd = J("sound-layer.json")["xy"]   # only the shots the sound map keeps (silent duplicates dropped)
ids = J("odyssey/cache/ears/ids.json"); C = np.load(os.path.join(H, "odyssey/cache/ears/clap.npy"))
keep = [i for i, k in enumerate(ids) if k in snd]
write(C[keep], [ids[i] for i in keep], "vec-snd.i8")
