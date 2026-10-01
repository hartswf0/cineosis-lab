"""After the forage: fetch every clip's thumbnail and read it with both CLIPs the lab uses (OpenAI ViT-B/32 quickgelu, which the
browser pages share, and LAION ViT-B/32, which the library's events and places were built on). Resumable at every step.
Writes thumbs/<id>.jpg, cache/ids.json, cache/emb-openai.npy, cache/emb-laion.npy.   usage: ../.venv/bin/python ingest.py"""
import json, os, sys, concurrent.futures as cf, urllib.request
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, "thumbs"); C = os.path.join(H, "cache"); os.makedirs(T, exist_ok=True); os.makedirs(C, exist_ok=True)
clips = json.load(open(os.path.join(H, "results", "clips.json")))
def get(c):
    p = os.path.join(T, c["id"] + ".jpg")
    if os.path.exists(p) and os.path.getsize(p) > 500: return True
    try:
        with urllib.request.urlopen(urllib.request.Request(c["thumbnailUrl"], headers={"user-agent": "cineosis-44-research"}), timeout=30) as r: b = r.read()
        open(p, "wb").write(b); return True
    except Exception as e: return False
with cf.ThreadPoolExecutor(8) as ex: ok = list(ex.map(get, clips))
print("thumbs", sum(ok), "of", len(clips), flush=True)
import torch, open_clip
from PIL import Image
dev = "mps" if torch.backends.mps.is_available() else "cpu"
ids_path = os.path.join(C, "ids.json"); old = json.load(open(ids_path)) if os.path.exists(ids_path) else []
have = {i: n for n, i in enumerate(old)}
new = [c["id"] for c, k in zip(clips, ok) if k and c["id"] not in have]
print("to read", len(new), flush=True)
for name, arch, pre_name in (("openai", "ViT-B-32-quickgelu", "openai"), ("laion", "ViT-B-32", "laion2b_s34b_b79k")):
    path = os.path.join(C, f"emb-{name}.npy"); E0 = np.load(path) if os.path.exists(path) and old else np.zeros((0, 512), np.float32)
    if not new: continue
    m, _, pre = open_clip.create_model_and_transforms(arch, pretrained=pre_name); m = m.to(dev).eval(); out = []
    for i in range(0, len(new), 64):
        ims = []
        for x in new[i:i + 64]:
            try: ims.append(pre(Image.open(os.path.join(T, x + ".jpg")).convert("RGB")))
            except Exception: ims.append(torch.zeros(3, 224, 224))
        with torch.no_grad(): e = m.encode_image(torch.stack(ims).to(dev)).float(); out.append((e / e.norm(dim=-1, keepdim=True)).cpu().numpy())
    np.save(path, np.concatenate([E0] + out).astype(np.float16)); print(name, "read", len(new), flush=True)
json.dump(old + new, open(ids_path, "w"))
print("ids", len(old) + len(new))
