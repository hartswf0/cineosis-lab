"""Blend pass: for each section, composite pairs of its top archive candidates with the CSS blend
modes the browser will use (multiply, screen, overlay, soft-light, darken, lighten, color-dodge,
color-burn, difference), embed every composite with the same CLIP, and keep the one closest to her
image, if it beats the best single shot. Formulas follow the W3C compositing spec, so the page's
mix-blend-mode reproduces what was scored. Adds `blend` to each section in spinecut-data.json.
"""
import json, os, itertools
import numpy as np, torch, open_clip
from PIL import Image

H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
P = os.path.join(H, "spinecut-data.json"); D = json.load(open(P))
X = np.load(os.path.join(LAB, "spine/spine-emb.npy")).astype(np.float32)
SP = json.load(open(os.path.join(LAB, "spine/spine-data.json")))["records"]
KOF = {r["thumb"]: r["k"] for r in SP if r.get("k") is not None}
MEAN = np.array([0.48145466, 0.4578275, 0.40821073], np.float32); STD = np.array([0.26862954, 0.26130258, 0.27577711], np.float32)

def load(i):
    im = Image.open(os.path.join(LAB, "thumbs", i + ".jpg")).convert("RGB"); w, h = im.size; s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((224, 224), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255

def soft(a, b):
    d = np.where(a <= .25, ((16 * a - 12) * a + 4) * a, np.sqrt(a))
    return np.where(b <= .5, a - (1 - 2 * b) * a * (1 - a), a + (2 * b - 1) * (d - a))
MODES = {  # a = backdrop (lower video), b = source (upper video)
    "multiply": lambda a, b: a * b, "screen": lambda a, b: a + b - a * b, "darken": np.minimum, "lighten": np.maximum,
    "difference": lambda a, b: np.abs(a - b),
    "overlay": lambda a, b: np.where(a <= .5, 2 * a * b, 1 - 2 * (1 - a) * (1 - b)),
    "soft-light": soft,
    "color-dodge": lambda a, b: np.where(a <= 0, 0, np.where(b >= 1, 1, np.minimum(1, a / np.maximum(1e-6, 1 - b)))),
    "color-burn": lambda a, b: np.where(a >= 1, 1, np.where(b <= 0, 0, 1 - np.minimum(1, (1 - a) / np.maximum(1e-6, b)))),
}
SYM = {"multiply", "screen", "darken", "lighten", "difference"}

def main():
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); model = model.to(dev).eval()
    def emb(ims):
        x = torch.tensor((np.stack(ims) - MEAN) / STD).permute(0, 3, 1, 2).to(dev)
        with torch.no_grad(): f = model.encode_image(x)
        return (f / f.norm(dim=-1, keepdim=True)).cpu().numpy()
    cache, gain = {}, []
    for n, s in enumerate(D["sections"]):
        q = X[KOF[s["hers"][0]]]
        c = [i for i in s["cand"][:4] if os.path.exists(os.path.join(LAB, "thumbs", i + ".jpg"))]
        for i in c:
            if i not in cache: cache[i] = load(i)
        tries, ims = [], []
        for a, b in itertools.permutations(c, 2):
            for m, f in MODES.items():
                if m in SYM and a > b: continue
                for al in (1.0, .6):
                    tries.append((a, b, m, al)); ims.append(np.clip((1 - al) * cache[a] + al * f(cache[a], cache[b]), 0, 1))
        singles = {i: float(emb([cache[i]])[0] @ q) for i in c}
        sc = np.concatenate([emb(ims[k:k + 256]) @ q for k in range(0, len(ims), 256)]) if ims else np.array([])
        bs = max(singles.values()) if singles else 0
        if len(sc) and sc.max() > bs:
            a, b, m, al = tries[int(sc.argmax())]
            s["blend"] = {"a": a, "b": b, "mode": m, "alpha": al, "score": round(float(sc.max()), 3), "single": round(bs, 3)}
            gain.append(float(sc.max()) - bs)
        else:
            s["blend"] = {"a": max(singles, key=singles.get) if singles else s["echo"], "b": None, "mode": None, "alpha": 1, "score": round(bs, 3), "single": round(bs, 3)}
        if n % 50 == 0: print(f"blend {n}/{len(D['sections'])}", flush=True)
    json.dump(D, open(P, "w"), ensure_ascii=False, separators=(",", ":"))
    from collections import Counter
    print("blended", len(gain), "/", len(D["sections"]), "mean gain", round(float(np.mean(gain)), 3) if gain else 0,
          Counter(s["blend"]["mode"] for s in D["sections"]).most_common())

if __name__ == "__main__":
    main()
