"""Clean SAM cut-outs: relabel on neutral grey with background classes, drop junk.

Reads cache/cutouts.json (raw SAM output), writes cache/cutouts_clean.json (what the lab shows).
Drops: masks that CLIP calls background (wall, curtain, floor, sky, blank surface, shadow), near-black
fragments, slivers (aspect > 5), sparse masks (fill < 0.3 of their box), and tiny pieces.
"""
import json, os
import numpy as np, torch, open_clip
from PIL import Image

LAB = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(LAB, "cache")
KEEP = ["person", "face", "hands", "child", "group of people", "animal", "bird", "vehicle", "aircraft", "machine",
        "building", "tree", "plant", "flower", "clock", "tool", "object", "sign with text", "television screen",
        "furniture", "boat", "statue"]
DROP = ["plain wall", "curtain", "floor", "blank sky", "blank surface", "dark shadow", "patch of ground",
        "water surface", "window glass", "film grain noise"]

def main():
    raw = json.load(open(os.path.join(C, "cutouts.json")))
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model = model.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
    labels = KEEP + DROP
    with torch.no_grad():
        T = model.encode_text(tok([f"a photo of a {l}" for l in labels]).to(dev)); T = T / T.norm(dim=-1, keepdim=True)
    clean, stats = {}, {"kept": 0, "dropped": {}}
    def drop(why): stats["dropped"][why] = stats["dropped"].get(why, 0) + 1
    for i, cuts in raw.items():
        keep = []
        for c in cuts:
            im = Image.open(os.path.join(LAB, c["png"])).convert("RGBA")
            a = np.array(im); alpha = a[..., 3] > 0
            h, w = alpha.shape
            fill = alpha.mean()
            if min(w, h) < 24: drop("tiny"); continue
            if max(w, h) / max(1, min(w, h)) > 5: drop("sliver"); continue
            if fill < 0.3: drop("sparse"); continue
            lum = a[..., :3][alpha].mean()
            if lum < 22: drop("dark"); continue
            bg = Image.new("RGBA", im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
            with torch.no_grad():
                f = model.encode_image(pre(bg.convert("RGB")).unsqueeze(0).to(dev)); f = f / f.norm(dim=-1, keepdim=True)
                p = torch.softmax(f @ T.T * 100, dim=1)[0].cpu().numpy()
            j = int(p.argmax())
            if labels[j] in DROP or p[len(KEEP):].sum() > 0.5:
                drop("background:" + labels[j]); continue
            keep.append({**c, "label": labels[j], "p": round(float(p[j]), 3)})
        clean[i] = keep
        stats["kept"] += len(keep)
    json.dump(clean, open(os.path.join(C, "cutouts_clean.json"), "w"))
    from collections import Counter
    print("kept", stats["kept"], "dropped", sum(stats["dropped"].values()),
          sorted(stats["dropped"].items(), key=lambda kv: -kv[1])[:8])
    print(Counter(c["label"] for v in clean.values() for c in v).most_common(15))

if __name__ == "__main__":
    main()
