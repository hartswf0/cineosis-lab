"""The cook, cut out of every AI pickup shot he is in (and any other figure a shot is about): SAM 2 proposes whole objects on the shot's
middle frame, CLIP keeps the one that is "a man in a skull mask and a black hood" (and not the sky, the sea, the fire), the video predictor
tracks him through the whole shot. Each becomes a packed mp4 (colour | matte, 12 fps) the griddle's FIGURE lane composites over any plate.
Writes ai/cut/<clip>-<k>/ and ai/cuts.json.   usage: .venv/bin/python slopfeeder/ai_cook.py"""
import json, os, subprocess, shutil, tempfile
import numpy as np, torch, open_clip, cv2
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); A = os.path.join(D, "ai"); C = os.path.join(A, "cut"); os.makedirs(C, exist_ok=True)
FPS, H = 12, 480
dev = "mps" if torch.backends.mps.is_available() else "cpu"
from sam2.build_sam import build_sam2_video_predictor, build_sam2
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
cfg, ckpt = "configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt")
vp = build_sam2_video_predictor(cfg, ckpt, device=dev)
gen = SAM2AutomaticMaskGenerator(build_sam2(cfg, ckpt, device=dev), points_per_side=16, pred_iou_thresh=.8, stability_score_thresh=.88, min_mask_region_area=300)
cm, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); cm.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ti(ts):
    with torch.no_grad(): e = cm.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ii(ims):
    with torch.no_grad(): e = cm.encode_image(torch.stack([prep(Image.fromarray(x)) for x in ims])).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
TARGETS = {"skull": ("cook", "a man in a white skull mask and a black hood"), "characters": ("four", "a flat colourful cartoon shape with dot eyes"), "pails": ("pail", "an orange bucket")}
BG = ti([f"a photo of {b}" for b in ["the sky", "the sea", "wet sand", "fire", "smoke", "a brick wall", "the ground", "darkness", "a crowd of people"]])
AI = json.load(open(os.path.join(A, "ai.json"))); OUT = os.path.join(A, "cuts.json"); done = {c["id"]: c for c in json.load(open(OUT))} if os.path.exists(OUT) else {}
jobs = []
for c in AI["clips"]:
    for s in c["shots"]:
        for mot, (kind, txt) in TARGETS.items():
            if mot in s["motifs"] and s["t1"] - s["t0"] >= 1.5: jobs.append((c, s, kind, txt)); break
print(len(jobs), "shots to cut", flush=True)
for n, (c, s, kind, txt) in enumerate(jobs):
    cid = f"{c['name']}-{s['k']}"
    if cid in done: continue
    d = tempfile.mkdtemp(prefix="cook_")
    try:
        L_ = min(6.0, s["t1"] - s["t0"]); t0 = (s["t0"] + s["t1"]) / 2 - L_ / 2
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.2f}", "-i", os.path.join(A, "src", c["name"] + ".mp4"), "-t", f"{L_:.2f}", "-vf", f"fps={FPS},scale=-2:{H}", "-q:v", "2", "-start_number", "0", os.path.join(d, "%05d.jpg")], check=True)
        fr = [np.array(Image.open(os.path.join(d, f)).convert("RGB")) for f in sorted(os.listdir(d))]
        if len(fr) < 6: continue
        r = len(fr) // 2; img = fr[r]; hh, ww = img.shape[:2]; T = ti([f"a photo of {txt}"])[0]; TB = np.vstack([T[None], BG])
        with torch.inference_mode(): props = gen.generate(img)
        cands = []
        for pr in props:
            m = pr["segmentation"]; a = m.mean()
            if a < .01 or a > .6: continue
            ys, xs = np.where(m); crop = np.where(m[..., None], img, 128).astype(np.uint8)[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; e = ii([crop])[0]
            pz = np.exp(100 * (TB @ e)); pz /= pz.sum()
            if pz[0] < .4: continue
            cands.append((float(e @ T) + .05 * pz[0] + .03 * a ** .3, m))
        if not cands: done[cid] = {"id": cid, "kind": kind, "none": True}; continue
        fit, seed = max(cands, key=lambda t: t[0]); tr = [None] * len(fr)
        with torch.inference_mode():
            st = vp.init_state(video_path=d, offload_video_to_cpu=True); vp.add_new_mask(st, frame_idx=r, obj_id=0, mask=seed)
            for rev in (False, True):
                for fi, oids, lg in vp.propagate_in_video(st, start_frame_idx=r, reverse=rev): tr[fi] = (lg[0][0] > 0).cpu().numpy()
            vp.reset_state(st)
        pres = [m for m in tr if m is not None and m.sum() > 50]
        if len(pres) < len(fr) * .7: done[cid] = {"id": cid, "kind": kind, "none": True}; continue
        u = np.any(np.stack(pres), 0); ys, xs = np.where(u); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1; x1 -= (x1 - x0) % 2; y1 -= (y1 - y0) % 2
        od = os.path.join(C, cid); os.makedirs(os.path.join(od, "f"), exist_ok=True)
        for fi, (f, m) in enumerate(zip(fr, tr)):
            a = np.zeros((hh, ww), np.uint8) if m is None else cv2.GaussianBlur((m * 255).astype(np.uint8), (3, 3), 0)
            Image.fromarray(np.dstack([f, a])[y0:y1, x0:x1], "RGBA").save(os.path.join(od, "f", f"{fi:04d}.png"))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(od, "f", "%04d.png"), "-filter_complex",
                        "[0]split[a][b];[a]format=rgb24[c];[b]alphaextract,format=rgb24[m];[c][m]hstack,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264", "-crf", "21", "-movflags", "+faststart", os.path.join(od, "packed.mp4")], check=True)
        shutil.copy(os.path.join(od, "f", f"{r:04d}.png"), os.path.join(od, "still.png")); shutil.rmtree(os.path.join(od, "f"))
        done[cid] = {"id": cid, "kind": kind, "clip": c["name"], "k": s["k"], "world": s["world"], "fit": round(fit, 3), "secs": round(L_, 2), "fps": FPS, "area": round(float(seed.mean()), 3),
                     "box": [round(x0 / ww, 4), round(y0 / hh, 4), round((x1 - x0) / ww, 4), round((y1 - y0) / hh, 4)], "packed": f"ai/cut/{cid}/packed.mp4", "still": f"ai/cut/{cid}/still.png"}
        print(f"{n + 1}/{len(jobs)} {kind:5s} fit {fit:.3f} {cid}", flush=True)
    except Exception as e: print("skip", cid, e, flush=True)
    finally: shutil.rmtree(d, ignore_errors=True); json.dump(list(done.values()), open(OUT, "w"))
print("cuts:", sum(1 for c in done.values() if not c.get("none")))
