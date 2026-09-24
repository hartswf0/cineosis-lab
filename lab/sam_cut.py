"""SAM 2.1 cut-outs for the read shots.

For each matched frame (frames/<id>.jpg) run SAM 2.1 (hiera small) automatic mask generation, keep up to
MAX well-formed, non-overlapping figures, save each as a transparent PNG cropped to its box, and label it
with CLIP (zero-shot). Writes cutouts/<id>_<k>.png and cache/cutouts.json.
"""
import json, os, sys
import numpy as np, torch, open_clip
from PIL import Image

LAB = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(LAB, "cache")
MAX = 4
LABELS = ["person", "face", "hands", "child", "crowd", "animal", "bird", "vehicle", "aircraft", "machine",
          "building", "tree", "plant", "flower", "object", "sign or text", "screen", "furniture", "water", "sky"]

def main():
    from sam2.build_sam import build_sam2
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    sam = build_sam2("configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(LAB, "models", "sam2.1_hiera_small.pt"), device=dev)
    gen = SAM2AutomaticMaskGenerator(sam, points_per_side=24, pred_iou_thresh=0.82, stability_score_thresh=0.9,
                                     min_mask_region_area=400)
    clip, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    clip = clip.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
    with torch.no_grad():
        T = clip.encode_text(tok([f"a photo of a {l}" for l in LABELS]).to(dev)); T = T / T.norm(dim=-1, keepdim=True)
    os.makedirs(os.path.join(LAB, "cutouts"), exist_ok=True)
    out_path = os.path.join(C, "cutouts.json")
    out = json.load(open(out_path)) if os.path.exists(out_path) else {}
    frames = sorted(f[:-4] for f in os.listdir(os.path.join(LAB, "frames")) if f.endswith(".jpg"))
    for k, i in enumerate(frames):
        if i in out:
            continue
        im = Image.open(os.path.join(LAB, "frames", i + ".jpg")).convert("RGB")
        W, H = im.size
        arr = np.array(im)
        with torch.inference_mode():
            masks = gen.generate(arr)
        A = W * H
        # figures, not backgrounds: 1.5%–45% of the frame, not touching 3+ edges
        cand = []
        for m in masks:
            x, y, w, h = m["bbox"]; a = m["area"] / A
            edges = (x <= 2) + (y <= 2) + (x + w >= W - 2) + (y + h >= H - 2)
            if 0.015 <= a <= 0.45 and edges < 3:
                cand.append((m["predicted_iou"] * m["stability_score"] * (a ** 0.35), m))
        cand.sort(key=lambda t: -t[0])
        kept, cuts = [], []
        for _, m in cand:
            seg = m["segmentation"]
            if any((seg & o).sum() > 0.3 * min(seg.sum(), o.sum()) for o in kept):
                continue
            kept.append(seg)
            x, y, w, h = [int(v) for v in m["bbox"]]
            rgba = np.dstack([arr, (seg * 255).astype(np.uint8)])[y:y + h, x:x + w]
            png = f"cutouts/{i}_{len(cuts)}.png"
            Image.fromarray(rgba, "RGBA").save(os.path.join(LAB, png))
            crop = Image.fromarray(np.where(seg[..., None], arr, 0).astype(np.uint8)[y:y + h, x:x + w])
            with torch.no_grad():
                f = clip.encode_image(pre(crop).unsqueeze(0).to(dev)); f = f / f.norm(dim=-1, keepdim=True)
                p = torch.softmax(f @ T.T * 100, dim=1)[0]
            j = int(p.argmax())
            cuts.append({"png": png, "label": LABELS[j], "p": round(float(p[j]), 3),
                         "bbox": [round(x / W, 4), round(y / H, 4), round(w / W, 4), round(h / H, 4)],
                         "area": round(m["area"] / A, 4)})
            if len(cuts) >= MAX:
                break
        out[i] = cuts
        if k % 10 == 0:
            json.dump(out, open(out_path, "w"))
            print(f"{k + 1}/{len(frames)} {len(cuts)} cut-outs", flush=True)
    json.dump(out, open(out_path, "w"))
    print("DONE", sum(len(v) for v in out.values()), "cut-outs from", len(out), "frames", flush=True)

if __name__ == "__main__":
    main()
