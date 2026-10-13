"""THE MOVING IMAGE PASS — the lab reads one still frame per shot; this reads the shot as it moves. For every read shot (its clip is local):
  frames   8 frames spread across the whole clip, each through CLIP and DINOv2: how far the shot travels from its own thumbnail,
           frame by frame (1 - cosine to the frame the lab read)
  cuts     the clip scanned at 4 fps for hard cuts the archive's cutter missed (colour-histogram jumps)
  camera   optical flow between 4 fps frames, fitted with one similarity transform per pair: pan (x), tilt (y), zoom (scale);
           what the camera cannot explain is the subject moving. Labelled static / pan / tilt / zoom in / zoom out / handheld.
  depth    Depth Anything V2 (small) on the middle frame: how deep the picture is (near/far spread); depth maps saved for a few shots
Writes explain/moving.json (+ explain/depth_<id8>.png, explain/strip8_<id8>.jpg for the showcase).   usage: lab/.venv/bin/python lab/explain/moving.py"""
import json, os, warnings
import numpy as np, cv2, torch
warnings.filterwarnings("ignore")
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
shots = [s for s in J("lab-data.json")["shots"] if s.get("signs") and os.path.exists(os.path.join(LAB, "clips", s["id"] + ".mp4"))]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
from PIL import Image
import open_clip, torchvision.transforms as tv
cm, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); cm = cm.to(dev).eval()
dino = torch.hub.load(os.path.expanduser("~/.cache/torch/hub/facebookresearch_dinov2_main"), "dinov2_vits14", source="local").to(dev).eval()
dtf = tv.Compose([tv.Resize(224), tv.CenterCrop(224), tv.ToTensor(), tv.Normalize((.485, .456, .406), (.229, .224, .225))])
from transformers import pipeline
depth = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=dev)
SHOW = ["21171e70-f59f-55b6-85c3-29691c97e312"]
def emb(ims):
    with torch.no_grad():
        a = cm.encode_image(torch.stack([pre(i) for i in ims]).to(dev)).float().cpu().numpy(); b = dino(torch.stack([dtf(i) for i in ims]).to(dev)).float().cpu().numpy()
    return a / np.linalg.norm(a, axis=1, keepdims=True), b / np.linalg.norm(b, axis=1, keepdims=True)
def similarity(p0, p1):
    M, _ = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    return M
out, n = {}, 0
for s in shots:
    path = os.path.join(LAB, "clips", s["id"] + ".mp4"); cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 24; N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if N < 8: continue
    step = max(1, round(fps / 4)); frames, small, hist, k = [], [], [], 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if k % step == 0:
            frames.append((k / fps, f)); g = cv2.resize(f, (320, 240)); small.append(cv2.cvtColor(g, cv2.COLOR_BGR2GRAY))
            hsv = cv2.cvtColor(g, cv2.COLOR_BGR2HSV); h = cv2.calcHist([hsv], [0, 1], None, [16, 8], [0, 180, 0, 256]); hist.append(cv2.normalize(h, h).flatten())
        k += 1
    if len(frames) < 4: continue
    # cuts the archive missed: a histogram jump far above the shot's own frame-to-frame change
    d = np.array([1 - cv2.compareHist(hist[i], hist[i + 1], cv2.HISTCMP_CORREL) for i in range(len(hist) - 1)])
    cuts = [round(frames[i + 1][0], 2) for i in np.where((d > .5) & (d > 6 * (np.median(d) + .02)))[0]]
    # the camera: one similarity transform per frame pair, fitted to tracked corners
    moves = []
    for i in range(len(small) - 1):
        p0 = cv2.goodFeaturesToTrack(small[i], 200, .01, 8)
        if p0 is None or len(p0) < 12: moves.append([0, 0, 1, 0]); continue
        p1, st, _ = cv2.calcOpticalFlowPyrLK(small[i], small[i + 1], p0, None); ok = st.ravel() == 1
        if ok.sum() < 12: moves.append([0, 0, 1, 0]); continue
        M = similarity(p0[ok], p1[ok])
        if M is None: moves.append([0, 0, 1, 0]); continue
        sc = float(np.hypot(M[0, 0], M[1, 0])); pred = (p0[ok].reshape(-1, 2) @ M[:, :2].T) + M[:, 2]; res = float(np.median(np.linalg.norm(p1[ok].reshape(-1, 2) - pred, axis=1)))
        moves.append([float(M[0, 2]), float(M[1, 2]), sc, res])
    mv = np.array(moves); tx, ty, sc, res = np.median(mv[:, 0]), np.median(mv[:, 1]), np.median(mv[:, 2]), np.median(mv[:, 3]); jit = float(np.std(mv[:, 0]) + np.std(mv[:, 1]))
    label = "zoom in" if sc > 1.004 else "zoom out" if sc < .996 else "pan" if abs(tx) > 1.2 and abs(tx) >= abs(ty) else "tilt" if abs(ty) > 1.2 else "handheld" if jit > 2.5 else "static"
    # 8 frames across the shot, read by CLIP and DINO against the frame the lab read
    idx = np.linspace(0, len(frames) - 1, 8).round().astype(int); ims = [Image.fromarray(cv2.cvtColor(frames[i][1], cv2.COLOR_BGR2RGB)) for i in idx]
    th = Image.open(os.path.join(LAB, s["thumb"])).convert("RGB"); A, B = emb([th] + ims)
    clip_far = [round(float(1 - A[0] @ a), 3) for a in A[1:]]; dino_far = [round(float(1 - B[0] @ b), 3) for b in B[1:]]
    dm = np.array(depth(ims[4])["depth"], dtype=np.float32); dn = (dm - dm.min()) / (dm.max() - dm.min() + 1e-9)
    o = {"t": [round(frames[i][0], 2) for i in idx], "clip_far": clip_far, "dino_far": dino_far, "cuts": cuts, "camera": label,
         "pan": round(float(tx), 2), "tilt": round(float(ty), 2), "zoom": round(float(sc), 4), "subject": round(float(res), 3), "jitter": round(jit, 2),
         "flow": [[round(m[0], 2), round(m[1], 2), round(m[2], 4), round(m[3], 3)] for m in moves], "depth_spread": round(float(np.percentile(dn, 90) - np.percentile(dn, 10)), 3), "dur": round(frames[-1][0], 2)}
    if s["id"] in SHOW or n < 0: pass
    out[s["id"]] = o; n += 1
    if n % 50 == 0: print(n, flush=True)
# showcase: the shots that move most, change most, and the seed: their 8-frame strips and depth maps
def strip(k):
    o = out[k]; cap = cv2.VideoCapture(os.path.join(LAB, "clips", k + ".mp4")); ims = []
    for t in o["t"]:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
        if ok: ims.append(cv2.resize(f, (320, 240)))
    cv2.imwrite(os.path.join(H, f"strip8_{k[:8]}.jpg"), np.hstack(ims), [cv2.IMWRITE_JPEG_QUALITY, 82])
    cap.set(cv2.CAP_PROP_POS_MSEC, o["t"][4] * 1000); ok, f = cap.read()
    dm = np.array(depth(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))["depth"], dtype=np.float32); dm = ((dm - dm.min()) / (dm.max() - dm.min() + 1e-9) * 255).astype(np.uint8)
    cv2.imwrite(os.path.join(H, f"depth_{k[:8]}.png"), cv2.applyColorMap(dm, cv2.COLORMAP_INFERNO)); cv2.imwrite(os.path.join(H, f"mid_{k[:8]}.jpg"), f)
ids = list(out)
pick = set(SHOW) | set(sorted(ids, key=lambda k: -max(out[k]["clip_far"]))[:3]) | set(sorted(ids, key=lambda k: -len(out[k]["cuts"]))[:2]) \
       | set([k for k in ids if out[k]["camera"] == "zoom in"][:1]) | set([k for k in ids if out[k]["camera"] == "pan"][:1]) | set(sorted(ids, key=lambda k: -out[k]["depth_spread"])[:1])
for k in pick: strip(k)
summ = {"shots": len(out), "with_cuts": sum(1 for o in out.values() if o["cuts"]), "camera": {c: sum(1 for o in out.values() if o["camera"] == c) for c in ["static", "pan", "tilt", "zoom in", "zoom out", "handheld"]},
        "far_mean": round(float(np.mean([max(o["clip_far"]) for o in out.values()])), 3), "far_gt": sum(1 for o in out.values() if max(o["clip_far"]) > .25), "showcase": sorted(pick)}
json.dump({"summary": summ, "shots": out}, open(os.path.join(H, "moving.json"), "w"), separators=(",", ":"))
print(json.dumps(summ, indent=1))
