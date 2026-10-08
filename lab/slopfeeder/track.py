"""The two source videos, their main elements tracked and cut out with SAM 2.1 (video predictor), shot by shot:
  devdes · the login page: the four characters (purple, black, orange, yellow), seeded by their own colours
  devdes · the reaction: the developer (Ghost) in its shots, the designer in his
  ghost  · the stare: Ghost, the whole loop
For every element: RGBA frames, a ProRes 4444 .mov with real alpha (for an editor), a packed mp4 (colour | matte) for the web, and a
contact sheet. Everything stays under slopfeeder/src/ (never published).   usage: .venv/bin/python slopfeeder/track.py"""
import json, os, subprocess, shutil, tempfile
import numpy as np, cv2, torch
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); S = os.path.join(D, "src"); O = os.path.join(S, "tracks"); os.makedirs(O, exist_ok=True)
FPS, H = 15, 720
dev = "mps" if torch.backends.mps.is_available() else "cpu"
from sam2.build_sam import build_sam2_video_predictor, build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
cfg, ckpt = "configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt")
vp = build_sam2_video_predictor(cfg, ckpt, device=dev); ip = SAM2ImagePredictor(build_sam2(cfg, ckpt, device=dev))
def frames(video, t0, t1, crop, d):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", video, "-t", f"{t1 - t0:.3f}", "-vf", f"crop={crop},fps={FPS},scale=-2:{H}", "-q:v", "2", "-start_number", "0", os.path.join(d, "%05d.jpg")], check=True)
    return [np.array(Image.open(os.path.join(d, f))) for f in sorted(os.listdir(d))]
def colour_seeds(img):
    """the login page's four characters, by colour (HSV), each its largest blob in the illustration's left half"""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV); h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int); W_ = img.shape[1]
    left = np.zeros_like(v, bool); left[:, : int(W_ * .62)] = True
    rules = {"purple": (h > 120) & (h < 145) & (s > 120) & (v > 90), "orange": ((h < 14) | (h > 172)) & (s > 150) & (v > 150),
             "yellow": (h > 20) & (h < 34) & (s > 140) & (v > 150), "black": (v < 50) & (s < 90)}
    out = {}
    for k, m in rules.items():
        m = (m & left).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        if n < 2: continue
        j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); x, y, w, hh, a = st[j]
        if a < 400: continue
        ys, xs = np.where(lab == j); pick = np.random.default_rng(0).choice(len(xs), min(4, len(xs)), replace=False)
        out[k] = {"box": [x, y, x + w, y + hh], "pts": [[int(xs[i]), int(ys[i])] for i in pick]}
    return out
def track(fr, d, seeds):
    """seeds: {name: {box?, pts}} on frame 0 -> {name: [mask per frame]}"""
    with torch.inference_mode():
        st = vp.init_state(video_path=d, offload_video_to_cpu=True)
        names = list(seeds)
        for oi, k in enumerate(names):
            sd = seeds[k]; vp.add_new_points_or_box(st, frame_idx=0, obj_id=oi, points=np.array(sd["pts"], np.float32), labels=np.ones(len(sd["pts"]), np.int32),
                                                     box=np.array(sd["box"], np.float32) if sd.get("box") else None)
        ms = {k: [None] * len(fr) for k in names}
        for fi, oids, logits in vp.propagate_in_video(st):
            for oi, lg in zip(oids, logits): ms[names[int(oi)]][fi] = (lg[0] > 0).cpu().numpy()
        vp.reset_state(st)
    return ms
def write(name, fr, ms, meta):
    od = os.path.join(O, name); shutil.rmtree(od, ignore_errors=True); os.makedirs(os.path.join(od, "rgba"))
    hh, ww = fr[0].shape[:2]; present = [m for m in ms if m is not None and m.sum() > 50]
    if not present: return None
    u = np.any(np.stack(present), 0); ys, xs = np.where(u); pad = 12
    x0, y0, x1, y1 = max(0, xs.min() - pad), max(0, ys.min() - pad), min(ww, xs.max() + pad), min(hh, ys.max() + pad)
    x1 -= (x1 - x0) % 2; y1 -= (y1 - y0) % 2
    for fi, (f, m) in enumerate(zip(fr, ms)):
        a = np.zeros((hh, ww), np.uint8) if m is None else cv2.GaussianBlur((m * 255).astype(np.uint8), (3, 3), 0)
        Image.fromarray(np.dstack([f, a])[y0:y1, x0:x1], "RGBA").save(os.path.join(od, "rgba", f"{fi:05d}.png"))
    rg = os.path.join(od, "rgba", "%05d.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", rg, "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", os.path.join(od, f"{name}.mov")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", rg, "-filter_complex", "[0]split[a][b];[a]format=rgb24[c];[b]alphaextract,format=rgb24[m];[c][m]hstack,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                    "-c:v", "libx264", "-crf", "20", "-movflags", "+faststart", os.path.join(od, f"{name}-packed.mp4")], check=True)
    n = len(fr); pick = np.linspace(0, n - 1, min(8, n)).astype(int)
    sheet = Image.new("RGB", ((x1 - x0) * len(pick), y1 - y0), (40, 160, 70))
    for j, fi in enumerate(pick): sheet.paste(Image.open(os.path.join(od, "rgba", f"{fi:05d}.png")), ((x1 - x0) * j, 0), Image.open(os.path.join(od, "rgba", f"{fi:05d}.png")))
    sheet.thumbnail((2400, 400)); sheet.save(os.path.join(od, "sheet.jpg"), quality=85)
    return {"name": name, **meta, "frames": n, "fps": FPS, "size": [int(x1 - x0), int(y1 - y0)], "present": round(len(present) / n, 3),
            "mov": f"src/tracks/{name}/{name}.mov", "packed": f"src/tracks/{name}/{name}-packed.mp4", "sheet": f"src/tracks/{name}/sheet.jpg"}
def points_seed(img, rel):   # points given as fractions of the frame -> SAM picks the figure under them
    hh, ww = img.shape[:2]; pts = [[int(x * ww), int(y * hh)] for x, y in rel]
    with torch.inference_mode():
        ip.set_image(img); m, sc, _ = ip.predict(point_coords=np.array(pts, np.float32), point_labels=np.ones(len(pts), np.int32), multimask_output=True)
    j = int(np.argmax([mm.sum() * s_ for mm, s_ in zip(m, sc)])); ys, xs = np.where(m[j] > 0)
    return {"pts": pts, "box": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]}
W = json.load(open(os.path.join(D, "world.json"))); out = []
devdes = os.path.join(S, "devdes.mp4"); ghost = os.path.join(S, "ghost.mp4")
JOBS = [("ghost-stare", ghost, 0, 9.86, "1080:1260:0:330", "points", [(.5, .3), (.5, .72), (.38, .62)], "Ghost, the whole loop")]
JOBS.append(("login-characters", devdes, 0, 8.49, "930:745:75:255", "colour", None, "the four characters of the login page"))
for j, s in enumerate(s for s in W["videos"][1]["segments"] if s["region"] == "the reaction"):
    who = "developer" if "skull" in s["label"] else "designer"
    rel = [(.52, .3), (.5, .75)] if who == "developer" else [(.47, .4), (.5, .88)]
    JOBS.append((f"{who}-{j}", devdes, s["t0"] + .03, s["t1"] - .03, "1080:810:0:1110", "points", rel, f"the {who}, {s['t0']}–{s['t1']} s"))
for name, video, t0, t1, crop, how, rel, desc in JOBS:
    d = tempfile.mkdtemp(prefix="trk_")
    try:
        fr = frames(video, t0, t1, crop, d)
        if how == "colour":
            seeds = colour_seeds(fr[0]); ms = track(fr, d, seeds)
            for k, m in ms.items():
                r = write(f"login-{k}", fr, m, {"desc": f"the {k} character", "source": "devdes", "t0": t0, "t1": t1}); r and out.append(r); print(r and (r["name"], r["present"]), flush=True)
        else:
            ms = track(fr, d, {name: points_seed(fr[0], rel)})
            r = write(name, fr, ms[name], {"desc": desc, "source": os.path.basename(video)[:-4], "t0": t0, "t1": t1}); r and out.append(r); print(r and (r["name"], r["present"]), flush=True)
    finally: shutil.rmtree(d, ignore_errors=True)
json.dump(out, open(os.path.join(S, "tracks.json"), "w"), indent=1); print("tracks:", len(out))
