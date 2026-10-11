"""MARKOV SAM · REPUBLIC: the multiplane, built from the archive instead of drawn.
A Disney multiplane stacks painted glass at depths and moves the camera through them; parallax is 1/depth. Here every plane is cut
from archival film:
  places   each episode's three places (world.json) are searched in the archive (the lab's 28,611 read shots and the Republic forage, one
           CLIP space), the frame is pulled from the clip itself (768 wide), and Depth Anything V2 splits it into planes:
           FAR (the whole frame, its nearer things painted out by inpainting), MID (what stands in the middle distance) and NEAR
           (what is closest), each a transparent layer, so a camera move opens real parallax inside one archival picture
  cast     every character is searched as a figure (a robot, a cowboy, a coach...), cut out with SAM 2.1 (a box from the depth
           foreground, the mask that agrees with it) and kept with where its feet are; a character keeps one figure across episodes
  prop     each episode's one thing, cut out the same way
Two candidates are cut for each place and figure (the studio can swap); no film gives two pictures to one episode.
Writes republic/planes/<episode>/*.webp, republic/planes/cast/*.webp and republic/planes.json.   usage: .venv/bin/python republic/planes.py"""
import json, os, re, subprocess, sys, tempfile, collections
import numpy as np, torch, open_clip, cv2
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); PL = os.path.join(H, "planes")
S = json.load(open(os.path.join(H, "script.json"))); W = json.load(open(os.path.join(H, "world.json")))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
# ---- the archive, one CLIP space (openai ViT-B/32)
lib = {x["id"]: x for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"]}
ids = json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))); EM = np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy")).astype(np.float32)
cand = []
for i, e in zip(ids, EM):
    s = lib.get(i)
    if s and s.get("video") and s.get("kind") != "poet": cand.append({"id": i, "title": s.get("title") or "", "year": s.get("year"), "video": s["video"], "t": float(s.get("in") or 0), "dur": float(s.get("dur") or 0), "e": e})
RC = json.load(open(os.path.join(H, "cache", "clips.json"))); RE = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32)
for i, e in zip(json.load(open(os.path.join(H, "cache", "emb-ids.json"))), RE):
    c = RC[i]; t = max(0.0, float(c.get("in") or 0) - float(c.get("st") or 0)); cand.append({"id": i, "title": c["title"], "year": c.get("year"), "video": c["video"], "t": t, "dur": float(c.get("dur") or 0), "e": e, "forage": 1})
E = np.stack([c["e"] for c in cand]); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
print(len(cand), "archive shots in one space", flush=True)
cm, _, cpre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); cm.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def tx(ts):
    with torch.no_grad(): v = cm.encode_text(tok(ts)).float()
    return (v / v.norm(dim=-1, keepdim=True)).numpy()
HUB = np.sort(E @ tx([f"a film still of {w}" for w in "a man|a woman|a room|a street|a landscape|a crowd|a machine|an animal|a building|the sky".split("|")]).T, 1)[:, -3:].mean(1)
# ---- models: depth and SAM 2.1
from transformers import pipeline
depth = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device=dev)
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
gen = SAM2AutomaticMaskGenerator(build_sam2("configs/sam2.1/sam2.1_hiera_s.yaml", os.path.join(L, "models", "sam2.1_hiera_small.pt"), device=dev), points_per_side=16, pred_iou_thresh=.8, stability_score_thresh=.88, min_mask_region_area=600)
def grab(c):
    """the frame itself, from the clip, 768 wide; if the moment is dark, the middle of the clip"""
    for t in (min(max(c["t"], .3), max(.3, c["dur"] - .4)) if c["dur"] else c["t"], c["dur"] / 2 if c["dur"] else 1.0):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f: p = f.name
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", c["video"], "-frames:v", "1", "-vf", "scale=768:-2", p], capture_output=True, timeout=90)
        if r.returncode == 0 and os.path.getsize(p) > 1000:
            im = np.array(Image.open(p).convert("RGB")); os.unlink(p)
            if im.mean() > 28 and im.std() > 18: return im, t
        elif os.path.exists(p): os.unlink(p)
    return None, None
def dmap(im):
    r = depth(Image.fromarray(im)); pd = r.get("predicted_depth")
    d = np.array(pd.squeeze().cpu() if pd is not None else r["depth"], dtype=np.float32)
    d = cv2.resize(d, (im.shape[1], im.shape[0])); lo, hi = np.percentile(d, 2), np.percentile(d, 98)
    return np.clip((d - lo) / (hi - lo + 1e-6), 0, 1)                    # 1 = nearest
def soft(mask, r=3):
    a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), r); return np.clip(a, 0, 1)
def save(rgba, path, q=72):
    Image.fromarray(rgba).save(path, "WEBP", quality=q, method=6); return os.path.getsize(path)
def split(im, d, base):
    """FAR / MID / NEAR by depth; the far plate has the nearer things painted out"""
    qm, qn = np.percentile(d, 55), np.percentile(d, 82)
    mid = d > qm; near = d > qn
    hole = cv2.dilate((mid * 255).astype(np.uint8), np.ones((15, 15), np.uint8))
    small = cv2.resize(im, (im.shape[1] // 2, im.shape[0] // 2)); hs = cv2.resize(hole, (small.shape[1], small.shape[0]))
    far = cv2.inpaint(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), hs, 9, cv2.INPAINT_TELEA); far = cv2.cvtColor(cv2.resize(far, (im.shape[1], im.shape[0])), cv2.COLOR_BGR2RGB)
    far = np.where(hole[..., None] > 0, far, im)
    out = {"far": save(np.dstack([far, np.full(d.shape, 255, np.uint8)]), base + "_far.webp", 70)}
    for name, m in (("mid", mid), ("near", near)):
        a = (soft(m, 2.5) * 255).astype(np.uint8); out[name] = save(np.dstack([im, a]), base + f"_{name}.webp", 74)
    return {"cover": [round(float(mid.mean()), 2), round(float(near.mean()), 2)]}
def iclip(ims):
    with torch.no_grad(): v = cm.encode_image(torch.stack([cpre(Image.fromarray(x)) for x in ims])).float()
    return (v / v.norm(dim=-1, keepdim=True)).numpy()
def cutout(im, d, base, q):
    """one figure: SAM 2.1 proposes every object in the frame; CLIP reads each one alone (on grey) against what we asked for; the best
    sized, best fitting one is kept, with where its feet are. Ground and sky (wide, touching both sides) are refused."""
    H_, W_ = d.shape; ms = gen.generate(im)
    ms = [m for m in ms if .03 < m["area"] / (H_ * W_) < .7]
    keep = []
    for m in ms:
        x, y, w, h = [int(v) for v in m["bbox"]]
        if w > .92 * W_ and h < .5 * H_: continue                         # a band across the frame: ground, sky, a table edge
        seg = m["segmentation"]; crop = np.where(seg[..., None], im, 128).astype(np.uint8)[y:y + h, x:x + w]
        if crop.size: keep.append((m, crop))
    if not keep: return None
    t = tx([f"a photo of {q}"])[0]; neg = tx(["a photo of the ground", "a photo of the sky", "a photo of a wall", "a blurry photo", "a photo of a window", "a photo of a door", "a grey rectangle", "a photo of fabric"])
    V = iclip([c for _, c in keep]); sc = V @ t - .5 * (V @ neg.T).max(1)
    sc = sc + .02 * np.array([float(np.clip(d[m["segmentation"]].mean() - .4, 0, .6)) for m, _ in keep])    # nearer is likelier the figure
    k = int(np.argmax(sc)); m = keep[k][0]["segmentation"]
    if V[k] @ t < .225 or sc[k] < .03: return None
    ys, xs = np.where(m); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    a = (soft(m, 1.0) * 255).astype(np.uint8); rgba = np.dstack([im, a])[y0:y1, x0:x1]
    s = 420 / max(rgba.shape[0], 1)
    if s < 1: rgba = cv2.resize(rgba, (max(1, int(rgba.shape[1] * s)), 420), interpolation=cv2.INTER_AREA)
    save(rgba, base + ".webp", 76)
    return {"w": int(rgba.shape[1]), "h": int(rgba.shape[0]), "feet": round(float(y1 / H_), 2), "cut": int(y1 >= H_ - 2), "x": round(float((x0 + x1) / 2 / W_), 2), "fit": round(float(V[k] @ t), 3)}
def framefit(im, q):
    return float(iclip([im])[0] @ tx([f"a film still of {q}"])[0])
used_titles_global = collections.Counter(); used_ids = set()
def pick(q, n, avoid, kind):
    """the archive's best answers to q, minus hub pictures that answer everything, at most one per film, fresh films first"""
    t = tx([f"a film still of {q}"])[0]; s = E @ t - .6 * HUB
    out = []
    for k in np.argsort(-s)[:400]:
        c = cand[k]; ti = c["title"].lower()
        if c["id"] in used_ids: continue
        if ti in avoid or used_titles_global[ti] >= (2 if kind == "place" else 3): continue
        out.append(c); avoid.add(ti)
        if len(out) >= n: break
    return out
def src(c, t): return {"id": c["id"], "title": c["title"], "year": c["year"], "video": c["video"], "t": round(t or 0, 2), "forage": c.get("forage", 0)}
MODE = sys.argv[1] if len(sys.argv) > 1 else "cast"          # cast | eps (two processes, two files; make_page.py joins them)
RECUT = json.load(open(os.path.join(H, "recut.json"))) if MODE == "recut" else {}
OF = os.path.join(H, {"cast": "planes.json", "recut": "planes.json", "eps": "planes-eps.json", "epsr": "planes-eps2.json"}[MODE])
OTHER = os.path.join(H, "planes-eps2.json" if MODE == "eps" else "planes-eps.json")
def done_elsewhere(i):
    try: return i in json.load(open(OTHER))["episodes"]
    except Exception: return False
OUT = json.load(open(OF)) if os.path.exists(OF) else {"cast": {}, "episodes": {}}
os.makedirs(os.path.join(PL, "cast"), exist_ok=True)
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
# ---- the cast, once each
if MODE == "recut":   # every clip already on a plane is spent; the named characters are cut again from a sharper search
    for fs in OUT["cast"].values(): used_ids.update(f["id"] for f in fs)
    for e in OUT.get("episodes", {}).values(): pass
for name, c in W["cast"].items():
    if MODE == "recut" and name in RECUT: c = dict(c, fig=RECUT[name]); OUT["cast"].pop(name, None)
    elif MODE != "cast" or not c.get("fig") or name in OUT["cast"]: continue
    got = []
    for cd in pick(f"{c['fig']}", 14, set(), "fig"):
        im, t = grab(cd)
        if im is None or framefit(im, c["fig"]) < .22: continue
        r = cutout(im, dmap(im), os.path.join(PL, "cast", f"{slug(name)}-{len(got)}"), c["fig"])
        if r: r.update(src(cd, t)); r["f"] = f"republic/planes/cast/{slug(name)}-{len(got)}.webp"; got.append(r); used_titles_global[cd["title"].lower()] += 1; used_ids.add(cd["id"])
        if len(got) >= 2: break
    OUT["cast"][name] = got; print(f"cast {name:20} {len(got)} · {' / '.join(g['title'][:28] for g in got)}", flush=True)
    json.dump(OUT, open(OF, "w"), ensure_ascii=False, separators=(",", ":"))
# ---- each episode's places and prop
for e in (S["episodes"][::-1] if MODE == "epsr" else S["episodes"]):
    if MODE not in ("eps", "epsr") or e["id"] in OUT["episodes"] or done_elsewhere(e["id"]): continue
    ew = W["episodes"][e["id"]]; d = os.path.join(PL, e["id"]); os.makedirs(d, exist_ok=True); avoid = set(); places = []
    for pi, q in enumerate(ew["places"]):
        alts = []
        for cd in pick(q + ", wide shot", 6, avoid, "place"):
            im, t = grab(cd)
            if im is None or framefit(im, q) < .21: continue
            base = os.path.join(d, f"p{pi}{'ab'[len(alts)]}"); r = split(im, dmap(im), base)
            r.update(src(cd, t)); r["f"] = f"republic/planes/{e['id']}/p{pi}{'ab'[len(alts)]}"; r["w"], r["h"] = int(im.shape[1]), int(im.shape[0]); alts.append(r); used_titles_global[cd["title"].lower()] += 1; used_ids.add(cd["id"])
            if len(alts) >= 2: break
        places.append({"q": q, "alts": alts})
    prop = None
    for cd in pick(ew["prop"], 8, avoid, "fig"):
        im, t = grab(cd)
        if im is None: continue
        if framefit(im, ew["prop"]) < .22: continue
        r = cutout(im, dmap(im), os.path.join(d, "prop"), ew["prop"])
        if r: r.update(src(cd, t)); r["f"] = f"republic/planes/{e['id']}/prop.webp"; prop = r; break
    OUT["episodes"][e["id"]] = {"places": places, "prop": prop}
    print(f"{e['id']} {e['name'][:28]:28} places {[len(p['alts']) for p in places]} prop {bool(prop)} · {' / '.join(p['alts'][0]['title'][:24] for p in places if p['alts'])}", flush=True)
    json.dump(OUT, open(OF, "w"), ensure_ascii=False, separators=(",", ":"))
tot = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(PL) for f in fs)
print("planes:", tot // 1024, "KB")
