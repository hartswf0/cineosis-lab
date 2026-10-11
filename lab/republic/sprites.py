"""MARKOV FOUND · REPUBLIC: the cast, alive. Each character's cut-out came from one frame of an archival clip; here SAM 2.1 follows that
same figure through three seconds of its own clip (video propagation from the cut-out's mask), so the actor breathes, turns and
gestures as the archive filmed it. Each becomes a sprite sheet (frames side by side, one fixed box so the feet stay put).
A track that loses the figure (it vanishes or doubles) is cut where it fails; fewer than eight good frames keeps the still.
Writes republic/planes/cast/<name>-sprite.webp and adds "sp" {f, n, w, h, fps} to planes.json.   usage: republic/.tts/bin/python republic/sprites.py"""
import json, os, re, subprocess, sys, tempfile, shutil
import numpy as np, cv2, torch
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
P = json.load(open(os.path.join(H, "planes.json")))
from sam2.build_sam import build_sam2_video_predictor
dev = "mps" if torch.backends.mps.is_available() else "cpu"
try: pred = build_sam2_video_predictor("configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt"), device=dev)
except Exception: dev = "cpu"; pred = build_sam2_video_predictor("configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt"), device=dev)
FPS, SECS, SH = 8, 3.0, 300
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
ONLY = set(sys.argv[1:])
def frames(video, t, d):
    os.makedirs(d, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t):.2f}", "-i", video, "-t", f"{SECS}", "-vf", f"fps={FPS},scale=768:-2", "-q:v", "3", os.path.join(d, "%05d.jpg")], check=True, timeout=120)
    return sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
def locate(frame, cut):
    """where the cut-out sits in the first frame: masked template match over the scales it could have been shrunk from"""
    fh, fw = frame.shape[:2]; ch, cw = cut.shape[:2]; rgb, a = cut[..., :3], cut[..., 3]
    scales = [1.0] if ch < 418 else [h / ch for h in range(ch, fh + 1, 6)]
    best = None
    for s in scales:
        tw, th = int(round(cw * s)), int(round(ch * s))
        if tw > fw or th > fh or tw < 8 or th < 8: continue
        t = cv2.resize(rgb, (tw, th)); m = cv2.resize(a, (tw, th))
        r = cv2.matchTemplate(frame, t, cv2.TM_CCORR_NORMED, mask=cv2.merge([m, m, m]))
        r[~np.isfinite(r)] = 0; _, v, _, loc = cv2.minMaxLoc(r)
        if best is None or v > best[0]: best = (v, loc, tw, th, m)
    if not best: return None, 0
    v, (x, y), tw, th, m = best; full = np.zeros((fh, fw), bool); full[y:y + th, x:x + tw] = m > 127
    return full, v
done = 0
for name, figs in P["cast"].items():
    if not figs or (ONLY and name not in ONLY): continue
    f = figs[0]
    if f.get("sp") and not ONLY: continue
    tmp = tempfile.mkdtemp(prefix="sp-")
    try:
        fs = frames(f["video"], f.get("t", 0), tmp)
        if len(fs) < 8: print("  short clip", name); continue
        f0 = cv2.cvtColor(cv2.imread(os.path.join(tmp, fs[0])), cv2.COLOR_BGR2RGB)
        cut = np.array(Image.open(os.path.join(L, f["f"].split("?")[0])).convert("RGBA"))
        m0, conf = locate(f0, cut)
        if m0 is None or conf < .85 or m0.sum() < 200: print(f"  {name}: not found in its clip ({conf:.2f})"); continue
        with torch.inference_mode():
            st = pred.init_state(video_path=tmp)
            pred.add_new_mask(st, frame_idx=0, obj_id=1, mask=m0)
            masks = {}
            for fi, _, lg in pred.propagate_in_video(st): masks[fi] = (lg[0] > 0).cpu().numpy()[0]
        a0 = m0.sum(); good = []
        for k in range(len(fs)):
            m = masks.get(k)
            if m is None or not (.4 < m.sum() / a0 < 2.4): break
            good.append(k)
        if len(good) < 6: print(f"  {name}: track held {len(good)} frames — keeps the still"); continue
        ys, xs = np.where(np.any([masks[k] for k in good], axis=0)); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        s = min(1, SH / (y1 - y0)); w, h = max(1, int((x1 - x0) * s)), max(1, int((y1 - y0) * s))
        sheet = Image.new("RGBA", (w * len(good), h))
        for n, k in enumerate(good):
            im = cv2.cvtColor(cv2.imread(os.path.join(tmp, fs[k])), cv2.COLOR_BGR2RGB)
            a = cv2.GaussianBlur(masks[k].astype(np.float32), (0, 0), 1.0)
            rgba = np.dstack([im, (np.clip(a, 0, 1) * 255).astype(np.uint8)])[y0:y1, x0:x1]
            sheet.paste(Image.fromarray(cv2.resize(rgba, (w, h), interpolation=cv2.INTER_AREA)), (n * w, 0))
        out = f"republic/planes/cast/{slug(name)}-sprite.webp"; sheet.save(os.path.join(L, out), "WEBP", quality=72, method=6)
        f["sp"] = {"f": out, "n": len(good), "w": w, "h": h, "fps": FPS, "cut": int(y1 >= f0.shape[0] - 2)}
        json.dump(P, open(os.path.join(H, "planes.json"), "w"), ensure_ascii=False, separators=(",", ":")); done += 1
        print(f"  {name:20} {len(good)} frames · {w}x{h} · {os.path.getsize(os.path.join(L, out)) // 1024} KB · match {conf:.2f}", flush=True)
    except Exception as e: print("  fail", name, str(e)[:120], flush=True)
    finally: shutil.rmtree(tmp, ignore_errors=True)
print(done, "actors alive")
