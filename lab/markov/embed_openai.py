"""Re-read every shot with OpenAI's CLIP ViT-B/32, the model whose text half runs in a browser (transformers.js, Xenova/clip-vit-base-patch32).
With it the published pages can read any words without the lab server. Writes shannon/emb-openai.bin (int8, library order) + its scale."""
import json, os, sys
import numpy as np, torch, open_clip
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
L = json.load(open(os.path.join(H, "library.json")))["shots"]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m = m.to(dev).eval()
out = np.zeros((len(L), 512), np.float32); miss = 0
for i in range(0, len(L), 64):
    ims, idx = [], []
    for j, s in enumerate(L[i:i + 64]):
        p = os.path.join(LAB, s["thumb"])
        try: ims.append(pre(Image.open(p).convert("RGB"))); idx.append(i + j)
        except Exception: miss += 1
    if ims:
        with torch.no_grad():
            e = m.encode_image(torch.stack(ims).to(dev)).float(); e = (e / e.norm(dim=-1, keepdim=True)).cpu().numpy()
        out[idx] = e
    if i % 1280 == 0: print(i, "of", len(L), flush=True)
sc = float(np.abs(out).max() / 127)
np.clip(np.round(out / sc), -127, 127).astype(np.int8).tofile(os.path.join(H, "emb-openai.bin"))
json.dump({"scale": sc, "missing": miss, "model": "ViT-B-32 openai"}, open(os.path.join(H, "emb-openai.json"), "w"))
import shutil; shutil.copy(os.path.join(H, "emb-openai.bin"), os.path.join(H, "emb.bin"))
J = json.load(open(os.path.join(H, "library.json"))); J["scale"] = sc; J["model"] = "ViT-B-32 openai"; json.dump(J, open(os.path.join(H, "library.json"), "w"), separators=(",", ":"))
print("done", len(L), "missing", miss)
