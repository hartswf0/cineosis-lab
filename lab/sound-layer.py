"""The explorer's sound layer: for every shot the archive's ears have heard (CLAP, odyssey/cache/ears/clap.npy):
  xy     where it sits on a map laid out by sound alone (UMAP of its CLAP embedding), 0..1
  heard  what it sounds like, in words: CLAP's two best matches among everyday sounds, z-scored per sound over the archive
and for every shot whose own people speak (Rushes' utterances):
  said   the sentence spoken in it
Writes lab/sound-layer.json.   usage: lab/.venv/bin/python lab/sound-layer.py"""
import json, os
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); J = lambda p: json.load(open(os.path.join(H, p)))
lab = {s["id"] for s in J("lab-data.json")["shots"]}
ids = J("odyssey/cache/ears/ids.json"); X = np.load(os.path.join(H, "odyssey/cache/ears/clap.npy")).astype(np.float32)
KIND = J("odyssey/cache/ears/kind.json")
quiet = {s["id"] for s in J("lab-data.json")["shots"] if (s.get("audio") or {}).get("kind") in ("silence", "none") or (s.get("audio") or {}).get("has_audio") is False}
keep = [i for i, k in enumerate(ids) if k in lab and (KIND.get(k) or {}).get("k") != "none" and k not in quiet]   # a clip with no sound has no place on a map of sounds
ids = [ids[i] for i in keep]; X = X[keep]; X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
# identical vectors are one silence copied: drop exact duplicates of the commonest vector
key = [hash(np.round(x, 3).tobytes()) for x in X]; from collections import Counter; top, n = Counter(key).most_common(1)[0]
if n > 20: keep2 = [i for i, h in enumerate(key) if h != top]; ids = [ids[i] for i in keep2]; X = X[keep2]; print("dropped", n, "identical silent clips")
print(len(ids), "shots heard", flush=True)
SOUNDS = ["a man speaking", "a woman speaking", "children's voices", "people talking at once", "a crowd cheering", "applause", "a radio announcer",
          "orchestral music", "jazz music", "a piano", "singing", "a marching band", "an engine running", "traffic and car horns", "a train", "an airplane",
          "machinery clanking", "typing", "a telephone ringing", "birds", "dogs barking", "water and waves", "wind", "rain", "fire crackling",
          "gunfire and explosions", "footsteps", "silence", "electronic beeps", "bells ringing"]
from transformers import ClapModel, ClapProcessor
import torch
m = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); p = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
with torch.no_grad(): T = m.get_text_features(**p(text=[f"the sound of {s}" for s in SOUNDS], return_tensors="pt", padding=True)).numpy()
T /= np.linalg.norm(T, axis=1, keepdims=True)
S = X @ T.T; Z = (S - S.mean(0)) / (S.std(0) + 1e-9)
heard = {}
for k, z in zip(ids, Z):
    o = np.argsort(-z)[:2]; heard[k] = [[SOUNDS[j], round(float(z[j]), 1)] for j in o]
import umap
U = umap.UMAP(n_neighbors=20, min_dist=.08, metric="cosine", random_state=7).fit_transform(X)
U = (U - U.min(0)) / (U.max(0) - U.min(0) + 1e-9)
xy = {k: [round(float(a), 4), round(float(b), 4)] for k, (a, b) in zip(ids, U)}
said = {}
try:
    R = J("rushes/clips.json"); Ut = J("rushes/utts.json")["utts"]; K = J("rushes/keys.json")["keys"]
    for k, r in zip(K, R["rows"]):
        if k in lab and r[7] >= 0: said[k] = Ut[r[7]][3]
except Exception as e: print("no utterances:", e)
json.dump({"sounds": SOUNDS, "xy": xy, "heard": heard, "said": said}, open(os.path.join(H, "sound-layer.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(xy), "on the sound map ·", len(said), "say something ·", os.path.getsize(os.path.join(H, "sound-layer.json")) // 1024, "KB")
for k in ids[:6]: print(" ", heard[k], "|", said.get(k, "")[:60])
