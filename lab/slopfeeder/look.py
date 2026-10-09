"""THE LOOKS: one colour table per register, shared by the browser (a PNG strip the shader reads) and the render (a .cube for ffmpeg lut3d),
so what the pass shows is what cut.py makes.
  cartoon    flat fills with no outlines (the meme's and our cartoons' style): edge-preserving smoothing, then every colour snapped to a palette
             learned from our own cartoon keyframes (k-means in Lab), with the four characters' colours (and the pails' orange) caught exactly
  newsreel   black and white with grain, EXCEPT the characters' and the pails' colours, which stay (pulled toward their exact hex)
The cartoon recipe is EVOLVED, not guessed: genomes (smoothing passes, strengths, median, palette size, saturation lift) are scored on frames
from the pickups and the archive by CLIP: likeness to our cartoons + likeness to the source (it must still read) - speckle ("snot":
the share of the picture in tiny islands of colour). The winner is written to looks.json, with each card's cartoonability measured under it.
usage: .venv/bin/python slopfeeder/look.py"""
import glob, json, os, random, subprocess
import numpy as np, cv2, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(D, "looks"); os.makedirs(OUT, exist_ok=True)
CH = {"purple": (0x56, 0x00, 0xf5), "orange": (0xf2, 0x5a, 0x17), "yellow": (0xe6, 0xc8, 0x08), "black": (0x1a, 0x1b, 0x1f)}
G = 33
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval()
def emb(ims):
    with torch.no_grad(): e = m.encode_image(torch.stack([prep(Image.fromarray(cv2.cvtColor(i, cv2.COLOR_BGR2RGB))) for i in ims])).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
lab = lambda rgb: cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2LAB)[0, 0].astype(np.float32)
# ---- the palette our cartoons actually use
keys = sorted(glob.glob(os.path.join(D, "cartoon", "keys", "*.png"))); px = []
for k in keys:
    im = cv2.imread(k); im = cv2.resize(im, (160, 90), interpolation=cv2.INTER_NEAREST); px.append(cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3))
px = np.concatenate(px).astype(np.float32); rng = np.random.default_rng(7); px = px[rng.choice(len(px), 60000, replace=False)]
_, lbl, cen = cv2.kmeans(px, 18, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, .5), 4, cv2.KMEANS_PP_CENTERS)
share = np.bincount(lbl.ravel(), minlength=18) / len(lbl); order = np.argsort(-share); CART = [cen[i] for i in order]          # Lab, most used first
CARTRGB = [tuple(int(x) for x in cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_LAB2RGB)[0, 0]) for c in CART]
print("cartoon palette:", ["#%02x%02x%02x" % c for c in CARTRGB], flush=True)
GRID = np.stack(np.meshgrid(*[np.linspace(0, 255, G)] * 3, indexing="ij"), -1).reshape(-1, 3)   # r, g, b (r slowest)
HSV = cv2.cvtColor(GRID.astype(np.uint8)[None], cv2.COLOR_RGB2HSV)[0].astype(np.float32)        # h 0-180, s, v 0-255
def charmask(hsv):
    h, s, v = hsv[:, 0] * 2, hsv[:, 1] / 255, hsv[:, 2] / 255; hd = lambda a: np.minimum(np.abs(h - a), 360 - np.abs(h - a))
    return {"orange": np.clip((1 - hd(18) / 16) * (s > .45) * (v > .35) * 1.0, 0, 1), "purple": np.clip((1 - hd(262) / 26) * (s > .4) * (v > .2) * 1.0, 0, 1),
            "yellow": np.clip((1 - hd(52) / 10) * (s > .45) * (v > .45) * 1.0, 0, 1)}
def cartoon_lut(k, lift):
    rgb = GRID.copy(); hsv = HSV.copy(); hsv[:, 1] = np.clip(hsv[:, 1] * lift, 0, 255)
    rgb2 = cv2.cvtColor(hsv.astype(np.uint8)[None], cv2.COLOR_HSV2RGB)[0].astype(np.float32)
    L = cv2.cvtColor(rgb2.astype(np.uint8)[None], cv2.COLOR_RGB2LAB)[0].astype(np.float32); P = np.stack(CART[:k])
    d = ((L[:, None, :] - P[None]) ** 2 * np.array([1.4, 1, 1])).sum(-1); out = np.array(CARTRGB[:k], np.float32)[d.argmin(1)]
    for name, w in charmask(hsv).items(): out[w > .3] = CH[name]
    out[(HSV[:, 2] < 40)] = CH["black"]
    return out
def newsreel_lut():
    rgb = GRID / 255; y = rgb @ np.array([.299, .587, .114]); y = np.clip((y - .5) * 1.28 + .47, 0, 1)
    grey = np.stack([y * 1.04, y * 1.0, y * .9], -1).clip(0, 1) * 255; keep = np.zeros(len(GRID)); tgt = np.zeros_like(GRID)
    for name, w in charmask(HSV).items(): sel = w > keep; keep = np.maximum(keep, w); tgt[sel] = CH[name]
    col = GRID * .5 + tgt * .5; k = np.clip(keep * 1.6, 0, 1)[:, None]
    return grey * (1 - k) + col * k
def write(name, lut):
    lut = np.clip(lut, 0, 255)
    with open(os.path.join(OUT, name + ".cube"), "w") as f:   # .cube: red fastest
        f.write(f"LUT_3D_SIZE {G}\n"); L = lut.reshape(G, G, G, 3)
        for b in range(G):
            for g in range(G):
                for r in range(G): f.write("%.5f %.5f %.5f\n" % tuple(L[r, g, b] / 255))
    # PNG strip for the browser: width G*G (blue slices side by side, red across each), height G (green down)
    L = lut.reshape(G, G, G, 3); img = np.zeros((G, G * G, 3), np.uint8)
    for b in range(G): img[:, b * G:(b + 1) * G] = L[:, :, b].transpose(1, 0, 2)
    cv2.imwrite(os.path.join(OUT, name + ".png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
def apply_lut(im, lut):   # nearest, as ffmpeg lut3d interp=nearest
    idx = np.rint(cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) * (G - 1) / 255).astype(int)
    L = lut.reshape(G, G, G, 3); return cv2.cvtColor(L[idx[..., 0], idx[..., 1], idx[..., 2]].astype(np.uint8), cv2.COLOR_RGB2BGR)
def stylise(im, g, lut):
    x = im
    for _ in range(g["passes"]): x = cv2.bilateralFilter(x, 9, g["r"] * 255, g["s"])
    if g["med"]: x = cv2.medianBlur(x, 2 * g["med"] + 1)
    x = apply_lut(x, lut)
    return cv2.medianBlur(x, 3) if g["post"] else x
def speckle(x):
    q = (x[..., 0].astype(np.int32) << 16) | (x[..., 1].astype(np.int32) << 8) | x[..., 2]; tot = 0; A = q.size
    for v in np.unique(q):
        n, lab_, st, _ = cv2.connectedComponentsWithStats((q == v).astype(np.uint8), connectivity=4)
        tot += st[1:, 4][st[1:, 4] < A * .0008].sum()
    return tot / A
# ---- the test bench: frames from the pickups (640x360) and the archive thumbnails (upscaled)
AT = json.load(open(os.path.join(D, "atlas.json"))); random.seed(3)
ai = [c for c in AT["cards"] if c["type"] == "ai"]; ar = [c for c in AT["cards"] if c["type"] == "archive"]
bench = []
for c in random.sample(ai, 14):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{(c['in'] + c['out']) / 2:.2f}", "-i", os.path.join(D, c["src"]), "-frames:v", "1", "-vf", "scale=640:360", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    if len(raw) == 640 * 360 * 3: bench.append(np.frombuffer(raw, np.uint8).reshape(360, 640, 3).copy())
for c in random.sample(ar, 8): bench.append(cv2.resize(cv2.imread(os.path.join(D, c["thumb"])), (640, 360), interpolation=cv2.INTER_CUBIC))
KE = emb([cv2.imread(k) for k in keys]); KC = KE.mean(0); KC /= np.linalg.norm(KC); OE = emb(bench)
base_k = float(np.mean(OE @ KC))
def fitness(g):
    lut = cartoon_lut(g["k"], g["lift"]); outs = [stylise(b, g, lut) for b in bench]; E = emb(outs)
    car = float(np.mean(E @ KC)) - base_k; keep = float(np.mean((E * OE).sum(1))); sp = float(np.mean([speckle(cv2.resize(o, (320, 180), interpolation=cv2.INTER_NEAREST)) for o in outs[:8]]))
    return 4 * car + 1.0 * keep - 3 * sp, car, keep, sp
def rand():
    return {"passes": random.choice([1, 2, 3]), "s": random.choice([4, 7, 10, 14]), "r": random.choice([.06, .1, .14, .2]), "med": random.choice([0, 1, 2, 3]),
            "k": random.choice([8, 10, 12, 14, 18]), "lift": random.choice([1.0, 1.2, 1.45]), "post": random.choice([0, 1])}
def mutate(g):
    h = dict(g); k = random.choice(list(h)); h[k] = rand()[k]; return h
pop = [rand() for _ in range(12)]; scored = []
for gen in range(5):
    scored = sorted([(fitness(g), g) for g in pop], key=lambda x: -x[0][0])
    b = scored[0]; print(f"generation {gen}: best {b[0][0]:.3f} (cartoon +{b[0][1]:.3f}, still reads {b[0][2]:.3f}, speckle {b[0][3]:.3f})", b[1], flush=True)
    pop = [g for _, g in scored[:4]] + [mutate(random.choice(scored[:4])[1]) for _ in range(8)]
best = scored[0][1]; LUTC = cartoon_lut(best["k"], best["lift"]); write("cartoon", LUTC); write("newsreel", newsreel_lut())
# contact sheet: source / cartoon / newsreel for six bench frames
rows = [np.hstack([cv2.resize(b, (320, 180)), cv2.resize(stylise(b, best, LUTC), (320, 180)), cv2.resize(apply_lut(cv2.addWeighted(b, 1, b, 0, 0), newsreel_lut()), (320, 180))]) for b in bench[:4] + bench[-2:]]
cv2.imwrite(os.path.join(OUT, "bench.jpg"), np.vstack(rows))
# ---- each card under the winning look: how cartoon it becomes, how much it still reads, how speckled (where cartoonising matters / works)
cards = AT["cards"]; res = {}
for i in range(0, len(cards), 64):
    ims = []
    for c in cards[i:i + 64]:
        p = os.path.join(D, c["thumb"]); im = cv2.imread(p) if os.path.exists(p) else None
        ims.append(cv2.resize(im, (320, 180)) if im is not None else np.zeros((180, 320, 3), np.uint8))
    E0 = emb(ims); st = [stylise(im, dict(best, s=max(2, best["s"] // 2)), LUTC) for im in ims]; E1 = emb(st)
    for c, a, b, s_ in zip(cards[i:i + 64], E0, E1, st):
        res[c["id"]] = {"was": round(float(a @ KC), 3), "becomes": round(float(b @ KC), 3), "reads": round(float(a @ b), 3), "speckle": round(speckle(cv2.resize(s_, (160, 90), interpolation=cv2.INTER_NEAREST)), 3)}
json.dump({"palette": ["#%02x%02x%02x" % c for c in CARTRGB[:best["k"]]], "chars": {k: "#%02x%02x%02x" % v for k, v in CH.items()}, "genome": best, "grid": G,
           "cards": res}, open(os.path.join(D, "looks.json"), "w"))
print("wrote looks/cartoon.cube|png, looks/newsreel.cube|png, looks.json; best", best, flush=True)
