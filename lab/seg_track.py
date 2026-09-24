"""Directed, tracked segmentation for the read shots (replaces sam_cut.py's undirected single-frame pass).

1. Frames: the clip at FPS (window of <= MAXF frames centred on the reading frame), scaled to 480p.
2. Proposals: SAM 2.1 automatic masks on the reading frame (dense grid, small objects allowed).
3. Direction: every proposal is scored by CLIP against WHAT THE READING IS ABOUT (the note's lead clause,
   e.g. "A crop-duster low over a field"), the search query that found the shot, and a background vocabulary.
   Backgrounds are dropped; the best reading match becomes the primary segment ("reading"), then up to
   MAXO-1 other distinct figures ranked by SAM quality x size. Each gets a description label.
4. Tracking: the chosen masks seed SAM 2's video predictor, propagated forward and backward through the window.
5. Output per object: a still cut-out at the reading frame, an RGBA sprite of the tracked cut-out over time,
   and per-frame boxes (normalised) for overlaying outlines on the playing video.

Writes seg/<id>/... and cache/segments.json. Resumable.   usage: python seg_track.py [id ...]
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile
import cv2, numpy as np, torch, open_clip
from PIL import Image

LAB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LAB)
C = os.path.join(LAB, "cache")
FPS, MAXF, MAXO, H = 6, 24, 4, 480
DESCRIBE = ["man", "woman", "child", "face", "hands", "crowd of people", "soldier", "worker", "dancer",
            "dog", "horse", "cow", "sheep", "bird", "insect", "fish", "animal",
            "car", "truck", "train", "airplane", "boat", "bicycle", "machine", "tool", "weapon",
            "building", "house", "tower", "bridge", "window", "door", "mirror", "screen", "television",
            "clock", "lamp", "light bulb", "flag", "sign with text", "book", "paper", "photograph", "map",
            "chair", "table", "bed", "cup", "bottle", "food", "plant", "flower", "tree", "rock",
            "cloud", "cartoon character", "statue", "musical instrument", "phonograph", "telephone"]
BACKGROUND = ["plain wall", "curtain", "floor", "empty sky", "blank surface", "dark shadow", "patch of ground",
              "water surface", "grass field", "film grain noise", "black frame border"]

FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
HOG = cv2.HOGDescriptor(); HOG.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def lead(note):
    """The noun phrase a reading is about: text before the first colon, e.g. 'A crop-duster low over a field'."""
    return re.split(r"[:;]", note)[0].strip()

def extract(clip, t_read, dur, out_dir):
    n_total = int(dur * FPS)
    if n_total <= MAXF:
        t0, n = 0.0, max(1, n_total)
    else:
        t0 = min(max(0.0, t_read - MAXF / FPS / 2), dur - MAXF / FPS); n = MAXF
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.3f}", "-i", clip, "-t", f"{n / FPS:.3f}",
                    "-vf", f"fps={FPS},scale=-2:{H}", "-q:v", "2", "-start_number", "0", os.path.join(out_dir, "%05d.jpg")])
    files = sorted(os.listdir(out_dir))
    r = min(len(files) - 1, max(0, int(round((t_read - t0) * FPS))))
    return t0, len(files), r

def main():
    from sam2.build_sam import build_sam2, build_sam2_video_predictor
    from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
    dev = os.environ.get("SEG_DEVICE") or ("mps" if torch.backends.mps.is_available() else "cpu")
    cfg, ckpt = "configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(LAB, "models", "sam2.1_hiera_small.pt")
    gen = SAM2AutomaticMaskGenerator(build_sam2(cfg, ckpt, device=dev), points_per_side=20, pred_iou_thresh=0.7,
                                     stability_score_thresh=0.85, min_mask_region_area=60, crop_n_layers=0)
    vp = build_sam2_video_predictor(cfg, ckpt, device=dev)
    clip_m, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    clip_m = clip_m.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
    def enc_text(ts):
        with torch.no_grad():
            t = clip_m.encode_text(tok(ts).to(dev)); return t / t.norm(dim=-1, keepdim=True)
    Tdesc = enc_text([f"a photo of a {l}" for l in DESCRIBE]); Tbg = enc_text([f"a photo of a {l}" for l in BACKGROUND])

    data = json.load(open(os.path.join(LAB, "lab-data.json")))
    shots = {s["id"]: s for s in data["shots"] if s["signs"] and s["clip"]}
    args = sys.argv[1:]
    shard = next((a for a in args if a.startswith("--shard=")), None)   # --shard=k/n : this worker's slice
    only = [a for a in args if not a.startswith("--")]
    done = {}
    for f in glob.glob(os.path.join(C, "segments*.json")):
        done.update(json.load(open(f)))
    todo = [i for i in sorted(shots) if not only or i in only]
    if shard:
        k_, n_ = map(int, shard.split("=")[1].split("/")); todo = todo[k_::n_]
    out_path = os.path.join(C, f"segments_{shard.split('=')[1].replace('/', 'of')}.json" if shard else "segments.json")
    out = json.load(open(out_path)) if os.path.exists(out_path) else {}
    todo = [i for i in todo if i not in done or only]
    for k, i in enumerate(todo):
        s = shots[i]
        dur = s["end"] - s["start"]
        t_read = s["read_t"] if s.get("read_t") is not None else s["match"] - s["start"]
        tmp = tempfile.mkdtemp(prefix="seg_")
        try:
            t0, nfr, r = extract(os.path.join(LAB, s["clip"]), t_read, dur, tmp)
            if nfr == 0:
                continue
            frame = np.array(Image.open(os.path.join(tmp, f"{r:05d}.jpg")).convert("RGB"))
            Hh, Ww = frame.shape[:2]; A = Hh * Ww
            with torch.inference_mode():
                props = gen.generate(frame)
            targets = [lead(r_["note"]) for r_ in s["signs"]]      # what the reading says the shot is about
            Ttar = enc_text([f"a photo of {t}" for t in targets])
            cands = []
            def score(seg, q, src):
                ys, xs = np.where(seg)
                if len(xs) < 40: return None
                x, y = int(xs.min()), int(ys.min()); w, h = int(xs.max() - x + 1), int(ys.max() - y + 1)
                a = seg.sum() / A
                if a < 0.004 or a > 0.92: return None
                crop = np.where(seg[..., None], frame, 128).astype(np.uint8)[y:y + h, x:x + w]
                with torch.no_grad():
                    f = clip_m.encode_image(pre(Image.fromarray(crop)).unsqueeze(0).to(dev)); f = f / f.norm(dim=-1, keepdim=True)
                    pd = torch.softmax(torch.cat([f @ Tdesc.T, f @ Tbg.T], 1) * 100, 1)[0].cpu().numpy()
                    tar = (f @ Ttar.T)[0].cpu().numpy()
                if pd[len(DESCRIBE):].sum() > 0.5 and src != "detector": return None
                j = int(pd[: len(DESCRIBE)].argmax())
                return {"seg": seg, "bbox": (x, y, w, h), "area": float(a), "label": DESCRIBE[j], "p": float(pd[j]),
                        "match": float(tar.max()), "target": targets[int(tar.argmax())], "q": q * a ** 0.35, "src": src}
            pred = gen.predictor
            with torch.inference_mode():
                pred.set_image(frame)
            def prompt(points=None, box=None):
                with torch.inference_mode():
                    ms, sc, _ = pred.predict(point_coords=None if points is None else np.array(points, np.float32),
                                             point_labels=None if points is None else np.ones(len(points), np.int32),
                                             box=None if box is None else np.array(box, np.float32), multimask_output=True)
                return [(ms[j] > 0, float(sc[j])) for j in range(len(sc))]
            # (a) directed: where in the frame does CLIP see what the reading is about?
            with torch.no_grad():
                best = []
                for gs in (2, 3):
                    cw, ch = Ww // gs, Hh // gs
                    for gy in range(gs * 2 - 1):
                        for gx in range(gs * 2 - 1):
                            x0, y0 = gx * cw // 2, gy * ch // 2
                            f = clip_m.encode_image(pre(Image.fromarray(frame[y0:y0 + ch, x0:x0 + cw])).unsqueeze(0).to(dev))
                            f = f / f.norm(dim=-1, keepdim=True)
                            best.append((float((f @ Ttar[:1].T)[0, 0]), x0 + cw // 2, y0 + ch // 2))
            best.sort(reverse=True)
            for _, px, py in best[:2]:
                for seg, sc in prompt(points=[[px, py]]):
                    c = score(seg, sc, "directed")
                    if c: cands.append(c)
            # (b) people and faces (OpenCV's bundled detectors) as box prompts
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            boxes = [("face", b) for b in FACE.detectMultiScale(gray, 1.1, 5, minSize=(24, 24))]
            boxes += [("person", b) for b in HOG.detectMultiScale(gray, winStride=(8, 8), scale=1.05)[0]]
            for kind, (bx, by, bw, bh) in boxes[:6]:
                segs = prompt(box=[bx, by, bx + bw, by + bh])
                seg, sc = max(segs, key=lambda t: t[1])
                c = score(seg, sc, "detector")
                if c: c["label"] = kind if kind == "face" else ("person" if c["label"] not in ("man", "woman", "child", "soldier", "worker", "dancer") else c["label"]); cands.append(c)
            for m in props:
                x, y, w, h = [int(v) for v in m["bbox"]]; a = m["area"] / A
                if a < 0.004 or a > 0.92 or w < 8 or h < 8: continue
                c = score(m["segmentation"], m["predicted_iou"] * m["stability_score"], "auto")
                if c: cands.append(c)
            chosen = []
            def free(c): return all((c["seg"] & o["seg"]).sum() < 0.3 * min(c["seg"].sum(), o["seg"].sum()) for o in chosen)
            for c in sorted(cands, key=lambda c: -(c["match"] * c["area"] ** 0.08)):  # the reading's subject first; prefer whole objects over fragments
                if free(c): chosen.append({**c, "role": "reading"}); break
            for c in sorted(cands, key=lambda c: -c["q"]):           # then the other distinct figures
                if len(chosen) >= MAXO: break
                if free(c): chosen.append({**c, "role": "figure"})
            if not chosen:
                out[i] = {"fps": FPS, "t0": t0, "frames": nfr, "read_idx": r, "objects": []}; continue
            # track through the window
            tracks = {k_: {} for k_ in range(len(chosen))}
            with torch.inference_mode():
                st = vp.init_state(video_path=tmp, offload_video_to_cpu=True)
                for k_, c in enumerate(chosen):
                    vp.add_new_mask(st, frame_idx=r, obj_id=k_, mask=c["seg"])
                for rev in (False, True):
                    for fi, oids, logits in vp.propagate_in_video(st, start_frame_idx=r, reverse=rev):
                        for oi, lg in zip(oids, logits):
                            tracks[int(oi)][fi] = (lg[0] > 0).cpu().numpy()
                vp.reset_state(st)
            d = os.path.join(LAB, "seg", i); os.makedirs(d, exist_ok=True)
            frames = [np.array(Image.open(os.path.join(tmp, f"{fi:05d}.jpg")).convert("RGB")) for fi in range(nfr)]
            objs = []
            for c in chosen:
                if c["p"] < 0.35 and c["src"] != "detector": c["label"] = "figure"
            for k_, c in enumerate(chosen):
                ms = [tracks[k_].get(fi) for fi in range(nfr)]
                boxes = []
                for m in ms:
                    if m is None or m.sum() < 20: boxes.append(None); continue
                    ys, xs = np.where(m); boxes.append([round(xs.min() / Ww, 4), round(ys.min() / Hh, 4),
                                                        round((xs.max() - xs.min() + 1) / Ww, 4), round((ys.max() - ys.min() + 1) / Hh, 4)])
                present = [b for b in boxes if b]
                if not present: continue
                ux0 = min(b[0] for b in present); uy0 = min(b[1] for b in present)
                ux1 = max(b[0] + b[2] for b in present); uy1 = max(b[1] + b[3] for b in present)
                X0, Y0, X1, Y1 = int(ux0 * Ww), int(uy0 * Hh), int(ux1 * Ww), int(uy1 * Hh)
                cw, ch = max(1, X1 - X0), max(1, Y1 - Y0)
                sc = min(1.0, 200 / max(cw, ch)); sw, sh = max(1, int(cw * sc)), max(1, int(ch * sc))
                sprite = Image.new("RGBA", (sw * nfr, sh), (0, 0, 0, 0))
                for fi, m in enumerate(ms):
                    if m is None: continue
                    rgba = np.dstack([frames[fi], (m * 255).astype(np.uint8)])[Y0:Y1, X0:X1]
                    sprite.paste(Image.fromarray(rgba, "RGBA").resize((sw, sh), Image.LANCZOS), (fi * sw, 0))
                sprite.save(os.path.join(d, f"{k_}_track.png"))
                x, y, w, h = c["bbox"]
                still = np.dstack([frame, (c["seg"] * 255).astype(np.uint8)])[y:y + h, x:x + w]
                Image.fromarray(still, "RGBA").save(os.path.join(d, f"{k_}.png"))
                objs.append({"k": k_, "role": c["role"], "label": c["label"], "p": round(c["p"], 3), "src": c["src"],
                             "desc": c["target"] if c["role"] == "reading" else c["label"],
                             "target": c["target"], "match": round(c["match"], 3),
                             "png": f"seg/{i}/{k_}.png", "bbox": [round(x / Ww, 4), round(y / Hh, 4), round(w / Ww, 4), round(h / Hh, 4)],
                             "area": round(c["area"], 4), "sprite": f"seg/{i}/{k_}_track.png", "sw": sw, "sh": sh,
                             "union": [round(ux0, 4), round(uy0, 4), round(ux1 - ux0, 4), round(uy1 - uy0, 4)],
                             "boxes": boxes, "present": round(len(present) / nfr, 3)})
            out[i] = {"fps": FPS, "t0": round(t0, 3), "frames": nfr, "read_idx": r, "proposals": len(props),
                      "kept": len(cands), "objects": objs}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        json.dump(out, open(out_path, "w"))
        o = out.get(i, {}).get("objects", [])
        print(f"{k + 1}/{len(todo)} {s['title'][:28]:28s} props={out.get(i,{}).get('proposals')} objs={len(o)} "
              f"reading→{o[0]['label'] + ' ~ ' + o[0]['target'][:30] if o else '-'}", flush=True)
    print("DONE", sum(len(v["objects"]) for v in out.values()), "tracked objects in", len(out), "shots", flush=True)

if __name__ == "__main__":
    main()
