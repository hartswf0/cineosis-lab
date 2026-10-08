"""Moving cut-outs from the archive: for the best forage finds in each part of the SLOPFEEDER world, CLIP points SAM 2.1 at what the
search was for (the explosion, the ship, the cartoon character...), and the video predictor tracks it through four seconds of the clip.
Each becomes a packed mp4 (colour | matte) a page or the renderer can composite, plus a still cut-out. Resumable.
Writes slopfeeder/cut/<id>/ and slopfeeder/cuts.json.   usage: .venv/bin/python slopfeeder/archtrack.py [per_world]"""
import json, os, sys, subprocess, shutil, tempfile
import numpy as np, torch, open_clip, cv2
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); C = os.path.join(D, "cut"); os.makedirs(C, exist_ok=True)
CACHE = os.path.join(D, "fclips"); os.makedirs(CACHE, exist_ok=True)
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 5; FPS, H, SECS = 12, 480, 4.0
TARGET = {"the landing": "a soldier", "the guns": "a gun turret", "the sea": "a warship", "the kitchen": "a cook", "the screens": "a computer",
          "the machines": "a robot", "the future": "a spaceship", "the characters": "a cartoon character", "the work": "a worker", "the faces": "a man's head and shoulders"}
BG = ["the sky", "the sea", "sand", "a rock cliff", "a wall", "the ground", "smoke", "darkness", "grass", "water", "clouds", "a floor"]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
from sam2.build_sam import build_sam2_video_predictor, build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
cfg, ckpt = "configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt")
vp = build_sam2_video_predictor(cfg, ckpt, device=dev)
gen = SAM2AutomaticMaskGenerator(build_sam2(cfg, ckpt, device=dev), points_per_side=16, pred_iou_thresh=.8, stability_score_thresh=.88, min_mask_region_area=200)
cm, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); cm.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ti(t):
    with torch.no_grad(): e = cm.encode_text(tok([t])).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()[0]
def ii(ims):
    with torch.no_grad(): e = cm.encode_image(torch.stack([prep(Image.fromarray(x)) for x in ims])).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
F = json.load(open(os.path.join(D, "forage.json")))["clips"]; OUT = os.path.join(D, "cuts.json")
done = {c["id"]: c for c in json.load(open(OUT))} if os.path.exists(OUT) else {}
jobs = []
for world, tgt in TARGET.items():
    seen = set(); n = 0
    for c in F:
        if not any(w == world for w, _ in c["found"]) or c["title"] in seen or (c.get("dur") or 0) < 2: continue
        seen.add(c["title"]); jobs.append((world, tgt, c)); n += 1
        if n >= PER: break
for k, (world, tgt, c) in enumerate(jobs):
    if c["id"] in done: continue
    src = os.path.join(CACHE, c["id"] + ".mp4")
    if not os.path.exists(src): subprocess.run(["curl", "-sfL", "-A", "cineosis-44-research", "-o", src, c["v"]])
    if not os.path.exists(src) or os.path.getsize(src) < 5000: continue
    d = tempfile.mkdtemp(prefix="arc_")
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout or 0)
        t0 = max(0.0, dur / 2 - SECS / 2)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.2f}", "-i", src, "-t", f"{SECS}", "-vf", f"fps={FPS},scale=-2:{H}", "-q:v", "2", "-start_number", "0", os.path.join(d, "%05d.jpg")], check=True)
        fs = sorted(os.listdir(d)); fr = [np.array(Image.open(os.path.join(d, f)).convert("RGB")) for f in fs]
        if len(fr) < 6: continue
        r = len(fr) // 2; img = fr[r]; hh, ww = img.shape[:2]; T = ti(f"a photo of {tgt}")
        # whole objects first (SAM 2 proposes), then CLIP keeps the one that is the target and not the ground, the sea or the sky
        TB = np.stack([T] + [ti(f"a photo of {b}") for b in BG]); cands = []
        with torch.inference_mode(): props = gen.generate(img)
        for pr in props:
            m = pr["segmentation"]; a = m.mean()
            if a < .01 or a > .45: continue
            ys, xs = np.where(m); x0_, x1_, y0_, y1_ = xs.min(), xs.max(), ys.min(), ys.max()
            edges = (x0_ <= 2) + (y0_ <= 2) + (x1_ >= ww - 3) + (y1_ >= hh - 3)
            if edges > 1: continue
            crop = np.where(m[..., None], img, 128).astype(np.uint8)[y0_:y1_ + 1, x0_:x1_ + 1]; e = ii([crop])[0]
            pz = np.exp(100 * (TB @ e)); pz /= pz.sum()
            if pz[0] < .35: continue
            solid = a / max(1e-6, (x1_ - x0_ + 1) * (y1_ - y0_ + 1) / (ww * hh))
            if solid > .9: continue
            cands.append((float(e @ T) + .05 * pz[0] + .02 * pr["predicted_iou"], m))
        if not cands: done[c["id"]] = {"id": c["id"], "world": world, "none": True}; continue
        fit, seed = max(cands, key=lambda t: t[0])
        tr = [None] * len(fr)
        with torch.inference_mode():
            st = vp.init_state(video_path=d, offload_video_to_cpu=True); vp.add_new_mask(st, frame_idx=r, obj_id=0, mask=seed)
            for rev in (False, True):
                for fi, oids, lg in vp.propagate_in_video(st, start_frame_idx=r, reverse=rev): tr[fi] = (lg[0][0] > 0).cpu().numpy()
            vp.reset_state(st)
        pres = [m for m in tr if m is not None and m.sum() > 30]
        if len(pres) < len(fr) * .6: done[c["id"]] = {"id": c["id"], "world": world, "none": True}; continue
        u = np.any(np.stack(pres), 0); ys, xs = np.where(u); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        x1 -= (x1 - x0) % 2; y1 -= (y1 - y0) % 2
        od = os.path.join(C, c["id"]); os.makedirs(os.path.join(od, "f"), exist_ok=True)
        for fi, (f, m) in enumerate(zip(fr, tr)):
            a = np.zeros((hh, ww), np.uint8) if m is None else cv2.GaussianBlur((m * 255).astype(np.uint8), (3, 3), 0)
            Image.fromarray(np.dstack([f, a])[y0:y1, x0:x1], "RGBA").save(os.path.join(od, "f", f"{fi:04d}.png"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(od, "f", "%04d.png"), "-filter_complex",
                        "[0]split[a][b];[a]format=rgb24[c];[b]alphaextract,format=rgb24[m];[c][m]hstack,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                        "-c:v", "libx264", "-crf", "21", "-movflags", "+faststart", os.path.join(od, "packed.mp4")], check=True)
        shutil.copy(os.path.join(od, "f", f"{r:04d}.png"), os.path.join(od, "still.png")); shutil.rmtree(os.path.join(od, "f"))
        done[c["id"]] = {"id": c["id"], "world": world, "target": tgt, "fit": round(fit, 3), "title": c["title"], "year": c["year"], "v": c["v"], "t": c["t"],
                         "t0": round(t0, 2), "secs": SECS, "fps": FPS, "box": [round(x0 / ww, 4), round(y0 / hh, 4), round((x1 - x0) / ww, 4), round((y1 - y0) / hh, 4)],
                         "area": round(float(seed.mean()), 4), "packed": f"cut/{c['id']}/packed.mp4", "still": f"cut/{c['id']}/still.png"}
        print(f"{k + 1}/{len(jobs)} {world:14s} {tgt:22s} fit {fit:.3f}  {c['title'][:40]}", flush=True)
    except Exception as e:
        print("skip", c["id"], e, flush=True)
    finally:
        shutil.rmtree(d, ignore_errors=True); json.dump(list(done.values()), open(OUT, "w"))
print("cuts:", sum(1 for c in done.values() if not c.get("none")))
