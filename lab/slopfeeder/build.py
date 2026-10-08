"""SLOPFEEDER, read from inside the Cineosis lab.
The series' frames (~/Downloads/SLOPFEEDER) and the two meme videos it comes from are taken apart and searched against the archive:
  1. the videos are segmented: shots (cuts found in each screen region) and regions (the split screen's login page vs its reaction)
  2. every frame is read for the world's entities (OWL-ViT finds them by name, SAM cuts them out): the cook, the buckets, the griddle...
  3. frames, video segments, entity cut-outs and the BEACHHEAD beats are embedded with CLIP ViT-B-32 (the archive's own space)
  4. each is matched against ~30,000 archival shots: the archive's rhymes, from which the scenes could be rebuilt
Writes slopfeeder/world.json, frames/, parts/, keys/.   usage: .venv/bin/python slopfeeder/build.py"""
import json, os, re, subprocess, glob, shutil
import numpy as np, torch
from PIL import Image
os.environ.setdefault("HF_HUB_OFFLINE", "1")
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); SRC = os.path.expanduser("~/Downloads/SLOPFEEDER")
DL = os.path.expanduser("~/Downloads")
VIDS = {"ghost": "COD Ghost Stare Meme Template 2 (Perfect Loop) - Morsicant (1080p).mp4", "devdes": "Developer vs Designer 😭 - AHXOZ (1080p).mp4"}
for d in ("frames", "parts", "keys", "src"): os.makedirs(os.path.join(D, d), exist_ok=True)
dev = "mps" if torch.backends.mps.is_available() else "cpu"

# ---- the archive: library + odyssey clips, one CLIP space
lib = json.load(open(os.path.join(L, "markov", "library.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]
meta, emb = {}, {}
for s, e in zip(lib["shots"], E1):
    if s["kind"] == "archive": meta[s["id"]] = (s.get("title"), s.get("year")); emb[s["id"]] = e
title = {c["id"]: (c["sourceTitle"], c.get("sourceYear")) for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json")))}
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))):
    if i not in emb and i in title: meta[i] = title[i]; emb[i] = e
ids = [i for i in emb if i in V]; A = np.stack([emb[i] for i in ids]).astype(np.float32); A /= np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
src_of = {i: V[i][0].split("/clips/")[0] for i in ids}
print(len(ids), "archival shots")
R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"
def card(i, s): return {"i": i, "s": round(float(s), 3), "title": meta[i][0], "year": meta[i][1], "v": V[i][0], "t": V[i][0].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg")}
DARK = None
def nearest(q, k=8, per_src=1):
    sims = A @ q - (.25 * DARK if DARK is not None else 0); out, seen = [], {}
    for j in np.argsort(-sims):
        f = src_of[ids[j]]
        if seen.get(f, 0) >= per_src: continue
        seen[f] = seen.get(f, 0) + 1; out.append(card(ids[j], sims[j]))
        if len(out) >= k: break
    return out

# ---- CLIP (the archive's model)
import open_clip
cm, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); cm.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def cimg(ims):
    with torch.no_grad(): e = cm.encode_image(torch.stack([prep(im.convert("RGB")) for im in ims])).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ctxt(ts):
    with torch.no_grad(): e = cm.encode_text(tok(ts)).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()

DARK = A @ ctxt(["a completely black dark empty frame"])[0]; DARK = np.clip((DARK - DARK.mean()) / DARK.std(), 0, None) * .02
# the archive's lexicon for this world: words alone, the concrete things the series is made of
LEX = [("stare", "a man in a mask staring silently at the camera"), ("helmet", "a man in a helmet and goggles staring"), ("grin", "a man in a suit laughing with delight"),
       ("passenger", "a man sitting in the passenger seat of a car looking back"), ("screen", "a computer screen with a form to fill in"), ("shapes", "colorful cartoon shapes with eyes"),
       ("beach", "soldiers landing on a beach"), ("fort", "a ruined brick fort by the sea"), ("burning", "ships burning at sea with black smoke"), ("spacesuit", "men in white spacesuits"),
       ("drill", "men turning a hand drill into the ground"), ("rope", "men hauling on a rope"), ("beam", "workers carrying a heavy wooden beam"), ("griddle", "a cook flipping hamburgers on a griddle"),
       ("feeding", "a man feeding another man a sandwich"), ("chow", "soldiers lining up for food from a field kitchen"), ("bucket", "an orange bucket"), ("tide", "the tide washing in over sand"),
       ("drain", "water running into a brick drain"), ("skull", "a skull"), ("wall", "men repairing a brick wall"), ("blueprint", "a man holding up a drawing of a building")]
# ---- 1. the frames
frames = []
for p in sorted(glob.glob(os.path.join(SRC, "*")), key=lambda x: (not os.path.basename(x).startswith("slopfeeder"), [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", os.path.basename(x))])):
    if not re.search(r"\.(png|jpe?g)$", p, re.I): continue
    name = os.path.splitext(os.path.basename(p))[0]; slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    im = Image.open(p).convert("RGB"); im.thumbnail((1400, 1400)); out = os.path.join(D, "frames", slug + ".jpg"); im.save(out, quality=86)
    frames.append({"id": slug, "name": name, "src": f"frames/{slug}.jpg", "w": im.width, "h": im.height})
FE = cimg([Image.open(os.path.join(D, f["src"])) for f in frames])
for f, e in zip(frames, FE): f["archive"] = nearest(e, 10)
LXT = ctxt([w for _, w in LEX]); lexicon = [{"k": k, "words": w, "archive": nearest(e, 12)} for (k, w), e in zip(LEX, LXT)]
print(len(frames), "frames")

# ---- 2. the videos: shots per screen region (local copies; never published)
def probe(p): return json.loads(subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", p], capture_output=True, text=True).stdout)
def cuts(p, crop):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vf", f"crop={crop},select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r)]
videos = []
for key, fn in VIDS.items():
    p = os.path.join(DL, fn); loc = os.path.join(D, "src", key + ".mp4")
    if not os.path.exists(loc): shutil.copy(p, loc)
    pr = probe(loc); dur = float(pr["format"]["duration"]); w, h = [(s["width"], s["height"]) for s in pr["streams"] if s["codec_type"] == "video"][0]
    regions = {"ghost": [("frame", f"{w}:{int(h*.5)}:0:{int(h*.25)}")], "devdes": [("the login screen", f"{w}:{int(h*.43)}:0:0"), ("the reaction", f"{w}:{int(h*.45)}:0:{int(h*.55)}")]}[key]
    segs = []
    for rname, crop in regions:
        cs = [0.0] + [c for c in cuts(loc, crop) if .3 < c < dur - .3] + [dur]
        for a, b in zip(cs, cs[1:]):
            m = (a + b) / 2; kp = os.path.join(D, "keys", f"{key}-{rname.split()[-1]}-{len(segs):02d}.jpg")
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{m:.2f}", "-i", loc, "-vf", f"crop={crop},scale=480:-2", "-frames:v", "1", kp], check=True)
            segs.append({"region": rname, "t0": round(a, 2), "t1": round(b, 2), "key": os.path.relpath(kp, D)})
    videos.append({"id": key, "file": fn, "dur": round(dur, 2), "w": w, "h": h, "segments": segs})
LABELS = ["a skull-masked soldier staring blankly from a car seat", "a grinning man in a suit reacting with delight", "a login screen with colorful cartoon shapes that have eyes", "a man staring in silence", "a delighted face"]
LT = ctxt(LABELS)
for v in videos:
    KE = cimg([Image.open(os.path.join(D, s["key"])) for s in v["segments"]])
    for s, e in zip(v["segments"], KE):
        j = int(np.argmax(LT[:3] @ e)); s["label"] = LABELS[j]; q = .4 * e + .6 * LT[j]; s["archive"] = nearest(q / np.linalg.norm(q), 8)
print(sum(len(v["segments"]) for v in videos), "video segments")

# ---- 3. the world, segmented: SAM cuts every frame into pieces without being told what to look for; CLIP names each piece
from transformers import pipeline
gen = pipeline("mask-generation", model="facebook/sam-vit-base", device=-1)
WORLD = [("cook", "a man in a skull mask and a black hood"), ("worker", "a worker in a dirty white spacesuit"), ("bucket", "an orange plastic bucket"), ("griddle", "a metal griddle tray of burgers"),
         ("burger", "a hamburger patty"), ("onion", "an onion ring"), ("rope", "a rope"), ("beam", "a heavy wooden beam"), ("wall", "a crumbling brick wall"), ("arch", "a brick archway"),
         ("fort", "a stone fort on the coast"), ("ship", "a warship at sea"), ("craft", "a flying spaceship"), ("flag", "a flag"), ("fire", "fire and flames"), ("helmet", "a helmet"),
         ("glove", "a gloved hand"), ("shape", "a purple cartoon rectangle with eyes"), ("balloon", "a yellow balloon face")]
GROUND = ["wet sand", "a cloudy sky", "sea water", "mud", "a dark blurry background", "smoke"]
WT = ctxt([q for _, q in WORLD] + GROUND)
parts = []
for f in frames:
    im = Image.open(os.path.join(D, f["src"])).convert("RGB"); sm_ = im.copy(); sm_.thumbnail((1024, 1024)); sx = im.width / sm_.width
    ms = gen(sm_, points_per_batch=64, pred_iou_thresh=.88, stability_score_thresh=.92)["masks"]
    cand = []
    for mk in ms:
        mk = np.asarray(mk); ar = mk.mean()
        if ar < .002 or ar > .35: continue
        ys, xs = np.where(mk); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        if (x1 - x0) < 24 or (y1 - y0) < 24: continue
        rgb = np.asarray(sm_)[y0:y1, x0:x1]; a = (mk[y0:y1, x0:x1] * 255).astype(np.uint8)
        crop = Image.fromarray(rgb); bg = Image.new("RGB", crop.size, (128, 128, 128)); bg.paste(crop, mask=Image.fromarray(a))
        cand.append((ar, [x0, y0, x1, y1], rgb, a, bg))
    if not cand: f["entities"] = {}; continue
    CE = cimg([c[4] for c in cand]); P = np.exp(100 * CE @ WT.T); P /= P.sum(1, keepdims=True)
    got = {}
    for (ar, bx, rgb, a, bg), pr in zip(cand, P):
        j = int(np.argmax(pr))
        if j >= len(WORLD) or pr[j] < .35: continue          # the ground, or nothing clearly named
        got.setdefault(WORLD[j][0], []).append((float(pr[j]), ar, bx, rgb, a))
    f["entities"] = {}
    for k, lst in got.items():
        lst.sort(key=lambda x: -(x[0] * np.sqrt(x[1]))); f["entities"][k] = len(lst)
        for n, (pr, ar, bx, rgb, a) in enumerate(lst[:3]):
            pid = f"{f['id']}--{k}{n}"; Image.fromarray(np.dstack([rgb, a]), "RGBA").save(os.path.join(D, "parts", pid + ".png"))
            parts.append({"id": pid, "frame": f["id"], "kind": k, "p": round(pr, 3), "box": [int(v * sx) for v in bx], "png": f"parts/{pid}.png", "area": round(float(ar), 4)})
    print(f["id"], f["entities"], flush=True)
print(len(parts), "cut-outs")
# each kind of thing, as the archive has it: its name, steered by what its cut-outs look like
kinds = {}
for k, q in WORLD:
    ps = sorted([p for p in parts if p["kind"] == k], key=lambda p: -p["p"] * p["area"])
    if not ps: continue
    crops = []
    for p in ps[:12]:
        c = Image.open(os.path.join(D, p["png"])); bg = Image.new("RGB", c.size, (128, 128, 128)); bg.paste(c, mask=c.split()[3]); crops.append(bg)
    e = cimg(crops).mean(0); e = .35 * e / np.linalg.norm(e) + .65 * ctxt([q])[0]; e /= np.linalg.norm(e)
    kinds[k] = {"name": q, "n": len(ps), "frames": sorted({p["frame"] for p in ps}), "best": [p["id"] for p in ps[:6]], "archive": nearest(e, 12)}
# ---- 4. the BEACHHEAD beats, in words, against the archive
BEATS = [("01", "THE DEPLOYMENT ENVIRONMENT", "workers pumping hand drills in a line along a beach, a cook grilling, ships burning offshore"),
         ("02", "LOOKED GOOD IN THE RENDER", "a woman holds a drawing up against a crooked brick wall"),
         ("03", "DESIGN REVIEW", "a woman braces a leaning wall with her shoulder"),
         ("04", "IT'S NOT MY KNOT", "close-up of hands tying a rope knot around timber"),
         ("05", "WE HIRED ANOTHER PROMPT ENGINEER", "two men push down on a wooden crossbar together"),
         ("06", "IT GREW UP", "a very tall man carries a heavy beam over a crew of workers"),
         ("07", "YES, I'M THE DEVELOPER. ONIONS?", "a cook feeds a burger to a worker whose hands are busy"),
         ("08", "LET HIM COOK", "a cook covers food with a metal lid as debris falls"),
         ("09", "THE TIDE FOUND A BUG", "water flows under a brick wall on a beach"),
         ("10", "HOTFIX COMING THROUGH", "a tray of food passed through a low brick opening")]
BT = ctxt([b[2] for b in BEATS])
beats = [{"n": n, "caption": c, "words": w, "archive": nearest(e, 8)} for (n, c, w), e in zip(BEATS, BT)]
json.dump({"lexicon": lexicon, "frames": frames, "videos": videos, "parts": parts, "kinds": kinds, "beats": beats, "archive_n": len(ids), "r2": R2},
          open(os.path.join(D, "world.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("world.json:", len(frames), "frames ·", sum(len(v["segments"]) for v in videos), "segments ·", len(parts), "cut-outs ·", len(kinds), "kinds ·", len(beats), "beats")
