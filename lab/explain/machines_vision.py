"""THE MACHINES WATCH · depth and scissors. For chosen shots: the full-resolution frame nearest the shot's thumbnail, then
  depth   Depth Anything V2 (small): a depth map, and the frame split into near / middle / far planes (PNG with transparency)
  sam     SAM (ViT-B) automatic masks: an overlay with every region it cut, and its largest cut-outs, each alone
Writes explain/machines/vision/*.png and explain/machines/vision.json.   usage: lab/republic/.tts/bin/python lab/explain/machines_vision.py"""
import json, os, subprocess, io
import numpy as np, torch
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); OUT = os.path.join(H, "machines", "vision"); os.makedirs(OUT, exist_ok=True)
SHOTS = {"depth": ["7a714af0-aad1-5c5d-b3fc-b4f4e75a1358", "360aebd8-b73c-5c2d-8aa2-7107dc3118f8", "949ddb76-9dbb-5655-8166-27b9cc831d58", "4cee2a4a-d7f4-53a9-8067-d4c85825f61a", "2171860c-caf3-5d52-8fe0-f15ffa99914c"],
         "sam": ["ce8590ca-25b9-59f7-a840-8fc92c583ff7", "ba6c7ddc-b3a4-532f-a829-e519fd0fb322", "b9008c05-0f78-558a-aa6d-da850ecb32a4"]}
dev = "mps" if torch.backends.mps.is_available() else "cpu"
def frame(i):
    p = os.path.join(LAB, "clips", i + ".mp4"); th = np.asarray(Image.open(os.path.join(LAB, "thumbs", i + ".jpg")).convert("L").resize((64, 48)), float)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 4)
    best, bt, bim = 1e18, 0, None
    for k in range(12):
        t = dur * (k + .5) / 12
        b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        if not b: continue
        im = Image.open(io.BytesIO(b)).convert("RGB"); e = ((np.asarray(im.convert("L").resize((64, 48)), float) - th) ** 2).mean()
        if e < best: best, bt, bim = e, t, im
    return bim, bt
out = {"depth": [], "sam": []}
from transformers import pipeline
dp = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=dev)
for i in SHOTS["depth"]:
    im, t = frame(i); im.save(os.path.join(OUT, f"{i[:8]}_frame.jpg"), quality=90)
    d = np.asarray(dp(im)["depth"], float); d = (d - d.min()) / (np.ptp(d) + 1e-9)            # 1 = near
    stops = np.array([[0, 0, 4], [80, 18, 123], [182, 54, 121], [251, 136, 97], [252, 253, 191]], float); x = d * 4; k0 = np.clip(x.astype(int), 0, 3); f = (x - k0)[..., None]
    Image.fromarray((stops[k0] * (1 - f) + stops[k0 + 1] * f).astype(np.uint8)).save(os.path.join(OUT, f"{i[:8]}_depth.jpg"), quality=90)
    a = np.asarray(im); q1, q2 = np.quantile(d, [.4, .75]); planes = []
    for k, (lo, hi) in enumerate([(-1, q1), (q1, q2), (q2, 2)]):
        m = ((d > lo) & (d <= hi)).astype(np.uint8) * 255; rgba = np.dstack([a, m]); fn = f"{i[:8]}_plane{k}.png"; Image.fromarray(rgba).save(os.path.join(OUT, fn)); planes.append(fn)
    out["depth"].append({"id": i, "t": round(t, 2), "frame": f"{i[:8]}_frame.jpg", "depth": f"{i[:8]}_depth.jpg", "planes": planes, "near_share": round(float((d > .66).mean()), 3), "spread": round(float(d.std()), 3)})
    print("depth", i[:8], t, out["depth"][-1]["spread"], flush=True)
sg = pipeline("mask-generation", model="facebook/sam-vit-base", device=dev)
rng = np.random.default_rng(3)
for i in SHOTS["sam"]:
    im, t = frame(i); W0 = im.width
    if im.width > 1024: im = im.resize((1024, int(im.height * 1024 / im.width)))
    im.save(os.path.join(OUT, f"{i[:8]}_frame.jpg"), quality=90)
    r = sg(im, points_per_batch=64, pred_iou_thresh=.88)
    masks = sorted([np.asarray(m, bool) for m in r["masks"]], key=lambda m: -m.sum())
    a = np.asarray(im).astype(float); ov = a * .35
    for m in masks[::-1]:
        c = rng.integers(60, 255, 3); ov[m] = ov[m] * .25 + c * .75
    Image.fromarray(ov.astype(np.uint8)).save(os.path.join(OUT, f"{i[:8]}_sam.jpg"), quality=90)
    cuts = []
    for k, m in enumerate([m for m in masks if .01 < m.mean() < .5][:8]):
        ys, xs = np.where(m); box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        rgba = np.dstack([np.asarray(im), m.astype(np.uint8) * 255]); fn = f"{i[:8]}_cut{k}.png"; Image.fromarray(rgba).crop(box).save(os.path.join(OUT, fn)); cuts.append({"src": fn, "share": round(float(m.mean()), 3)})
    out["sam"].append({"id": i, "t": round(t, 2), "frame": f"{i[:8]}_frame.jpg", "sam": f"{i[:8]}_sam.jpg", "n": len(masks), "cuts": cuts})
    print("sam", i[:8], len(masks), "masks", flush=True)
json.dump(out, open(os.path.join(H, "machines", "vision.json"), "w"), indent=0)
