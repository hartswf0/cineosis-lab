"""A Wes Anderson Cineosis: every shot in the repo scored for his signatures, and the films that hold the most of them.
  signatures (CLIP ViT-B-32, against neutral prompts): symmetry, facing the camera, pastel interiors, overhead inserts, dioramas
             and miniatures, uniforms in rows, title cards, compartments
  measured  (from the thumbnail, letterbox bars removed): mirror symmetry of the picture's edges, how much of its structure is
             level and plumb (planar staging) rather than diagonal, a pastel palette (light, softly saturated pinks, yellows,
             mints and powder blues; black and white scores none), and how centred its weight is
  the score  the signatures and the measures together, each standardized; films ranked by the mean of their five best shots
Writes wes/wes.json.   usage: ../.venv/bin/python wes/score.py"""
import json, os, colorsys, concurrent.futures as cf
import numpy as np, torch, open_clip
from PIL import Image
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ---- every shot: the library and the Odyssey forage, one CLIP space
lib = json.load(open(os.path.join(L, "markov", "library.json"))); sc = lib["scale"]
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * sc
shots, emb = [], []
for s, e in zip(lib["shots"], E1):
    if s.get("kind") == "poet": continue
    shots.append({"id": s["id"], "src": s["src"], "title": s.get("title"), "year": s.get("year"), "thumb": s["thumb"]}); emb.append(e)
seen = {s["id"] for s in shots}
oids = json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))); E2 = np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy")).astype(np.float32)
oc = {c["id"]: c for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json")))}
for i, e in zip(oids, E2):
    c = oc.get(i)
    if not c or i in seen: continue
    shots.append({"id": i, "src": c["sourceId"], "title": c["sourceTitle"], "year": c.get("sourceYear"), "thumb": f"odyssey/thumbs/{i}.jpg"}); emb.append(e)
EM = np.stack(emb); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
print(len(shots), "shots", flush=True)
# ---- his signatures, as words
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
SIG = {
    "symmetry": ["a perfectly symmetrical centered composition", "a symmetrical frontal view of a building facade", "a long symmetrical corridor seen straight on"],
    "facing": ["a person standing in the exact center of the frame facing the camera", "a group of people lined up in a row facing the camera", "a deadpan portrait of a person looking straight into the camera"],
    "pastel": ["a pastel pink and mint colored room", "a pastel colored building facade", "a candy colored interior with pink and yellow walls"],
    "overhead": ["a top-down overhead view of objects neatly arranged on a table", "hands seen from above opening a box on a table", "a flat lay of papers and objects photographed from directly above"],
    "diorama": ["a miniature model of a building", "a cross-section of a dollhouse with rooms", "a toy model train in a miniature landscape"],
    "uniform": ["people in matching uniforms standing in a neat row", "a marching band in bright uniforms", "bellboys in matching uniforms"],
    "title": ["a vintage title card with centered text", "a hand painted sign with old fashioned lettering", "a typed letter or telegram close up"],
    "compartment": ["the interior of a train compartment", "a small cabin interior seen straight on", "the inside of a submarine or ship cabin"],
}
NEUTRAL = ["a photo", "a scene from a film", "a landscape", "a crowd of people", "a blurry image", "a street", "a machine", "people talking"]
AVOID = ["a blank screen", "a black frame", "an empty sky", "the open sea", "a rocket on a launch pad", "a congressional hearing", "a man speaking at a podium", "a computer screen", "an out of focus blur", "film leader and scratches"]
with torch.no_grad():
    def te(ts): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
    T = {k: te(v) for k, v in SIG.items()}; N = te(NEUTRAL); AV = te(AVOID)
neu = (EM @ N.T).max(1)
clip = {k: (EM @ v.T).max(1) - neu for k, v in T.items()}
avoid = (EM @ AV.T).max(1) - neu                                     # what only looks like him: empty frames, rockets, hearings          # how much more like the signature than like nothing in particular
# ---- measured from the picture
bars = {}
try:
    for c in json.load(open(os.path.join(L, "aspect", "clips.json"))):
        if len(c) > 4: bars[c[0]] = c[4:8]
except Exception: pass
def measure(s):
    try: im = Image.open(os.path.join(L, s["thumb"])).convert("RGB")
    except Exception: return None
    w, h = im.size; t, b, l, r = bars.get(s["id"], [0, 0, 0, 0])
    im = im.crop((int(l * w), int(t * h), int(w - r * w), int(h - b * h))).resize((128, 96))
    a = np.asarray(im, np.float32) / 255; g = a.mean(2)
    gx = np.zeros_like(g); gy = np.zeros_like(g); gx[:, 1:-1] = g[:, 2:] - g[:, :-2]; gy[1:-1] = g[2:] - g[:-2]; mag = np.hypot(gx, gy) + 1e-6
    sym = 1 - np.abs(mag - mag[:, ::-1]).sum() / (2 * mag.sum())                                   # the edges mirror
    lsym = 1 - np.abs(g - g[:, ::-1]).mean() / (g.std() + .05) / 2                                  # the light mirrors
    ang = np.abs(np.arctan2(gy, gx)) % (np.pi / 2); plumb = (mag * ((ang < .17) | (ang > np.pi / 2 - .17))).sum() / mag.sum()
    xs = np.arange(128); cx = (mag.sum(0) * xs).sum() / mag.sum() / 127; centre = 1 - 2 * abs(cx - .5)
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in a[::4, ::4].reshape(-1, 3)])
    hue, sat, val = hsv[:, 0] * 360, hsv[:, 1], hsv[:, 2]
    soft = (val > .55) & (sat > .1) & (sat < .55)
    fam = ((hue > 320) | (hue < 25)) | ((hue > 38) & (hue < 65)) | ((hue > 85) & (hue < 175)) | ((hue > 180) & (hue < 225))
    pastel = float((soft & fam).mean()); colour = float((sat > .12).mean())
    swatch = [p for p in a[::8, ::8].reshape(-1, 3)]
    detail = float(np.log(mag.mean() + 1e-4)); tone = float(g.std()); light = float(g.mean())
    return {"sym": float(sym), "lsym": float(lsym), "plumb": float(plumb), "centre": float(centre), "pastel": pastel, "colour": colour, "detail": detail, "tone": tone, "light": light}
with cf.ThreadPoolExecutor(8) as ex: M = list(ex.map(measure, shots))
keep = [k for k, x in enumerate(M) if x]
z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
def col(k): return np.array([M[i][k] for i in keep])
C = {k: v[keep] for k, v in clip.items()}
sym, lsym, plumb, centre, pastel, colour, detail, tone, light = (col(k) for k in ("sym", "lsym", "plumb", "centre", "pastel", "colour", "detail", "tone", "light"))
AVd = avoid[keep]
yr = np.array([int(shots[i]["year"]) if str(shots[i]["year"] or "").isdigit() else 1960 for i in keep])
LBk = {}
try: LBk = {(f["title"], f["year"]): f["kind"] for f in json.load(open(os.path.join(L, "aspect", "films.json")))["films"]}
except Exception: pass
rec = np.array([LBk.get((shots[i]["title"], shots[i]["year"])) == "record" for i in keep])
# a picture must have something in it: structure (edges), tonal range, and light; an empty frame mirrors perfectly and means nothing
full = np.clip((detail - np.percentile(detail, 30)) / (np.percentile(detail, 70) - np.percentile(detail, 30) + 1e-9), 0, 1) * np.clip((tone - .06) / .08, 0, 1) * (light > .12)
wes_clip = np.mean([z(C[k]) for k in ("symmetry", "facing", "pastel", "overhead", "diorama", "uniform", "title", "compartment")], axis=0) + .6 * np.max([z(C[k]) for k in C], axis=0)
score = (.4 * z(wes_clip) + .28 * z(sym) * full + .12 * z(lsym) * full + .1 * z(plumb) + .08 * z(centre) + .22 * z(pastel) * (colour > .15) - .25 * (colour < .08)
         - .35 * z(AVd) - .8 * rec - .5 * (yr >= 1985) - 2.5 * (full < .15))   # his look is a made, retro, staged look
# per signature: its words, steadied by the measure that belongs to it
pen = -.35 * z(AVd) - .8 * rec - .5 * (yr >= 1985) - 3 * (full < .15)
sigscore = {"symmetry": z(C["symmetry"]) + .8 * z(sym) * full + .3 * z(lsym) * full, "facing": z(C["facing"]) + .5 * z(sym) + .3 * z(centre),
            "pastel": z(C["pastel"]) + 1.0 * z(pastel) - (colour < .1) * 3, "overhead": z(C["overhead"]) + .2 * z(plumb),
            "diorama": z(C["diorama"]) + .2 * z(sym), "uniform": z(C["uniform"]) + .3 * z(sym), "title": z(C["title"]) + .3 * z(sym), "compartment": z(C["compartment"]) + .5 * z(sym) * full}
sigscore = {k: v + pen for k, v in sigscore.items()}
def row(n): i = keep[n]; s = shots[i]; return {"id": s["id"], "t": s["thumb"], "src": s["src"], "title": s["title"], "year": s["year"], "score": round(float(score[n]), 2),
                                                "sym": round(float(sym[n]), 3), "pastel": round(float(pastel[n]), 3), "colour": round(float(colour[n]), 2)}
order = np.argsort(-score); best = []; per_src = {}
for n in order:                                                     # the best shots, no more than three from one film
    s = shots[keep[n]]
    if per_src.get(s["src"], 0) >= 3: continue
    per_src[s["src"]] = per_src.get(s["src"], 0) + 1; best.append(row(n))
    if len(best) >= 360: break
chapters = {}
for k, v in sigscore.items():
    o = np.argsort(-v); out = []; ps = {}
    for n in o:
        s = shots[keep[n]]
        if ps.get(s["src"], 0) >= 2: continue
        ps[s["src"]] = ps.get(s["src"], 0) + 1; out.append(row(n))
        if len(out) >= 60: break
    chapters[k] = out
# the films: by the mean of their five best shots (films of three shots or more)
films = {}
for n in range(len(keep)): films.setdefault(shots[keep[n]]["src"], []).append(n)
LB = {}
try: LB = {(f["title"], f["year"]): f for f in json.load(open(os.path.join(L, "aspect", "films.json")))["films"]}
except Exception: pass
fr = []
for k, ns in films.items():
    if len(ns) < 3: continue
    sc5 = sorted((float(score[n]) for n in ns), reverse=True)[:5]; s = shots[keep[ns[0]]]; lb = LB.get((s["title"], s["year"]), {})
    top = sorted(ns, key=lambda n: -score[n])[:6]
    fr.append({"src": k, "title": s["title"], "year": s["year"], "n": len(ns), "score": round(float(np.mean(sc5)), 2), "kind": lb.get("kind"), "pic": lb.get("pic"),
               "colour": round(float(np.mean([colour[n] for n in ns])), 2), "shots": [row(n) for n in top]})
fr.sort(key=lambda f: -f["score"])
json.dump({"best": best, "chapters": chapters, "films": fr[:80]}, open(os.path.join(L, "wes", "wes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("films, best first:")
for f in fr[:25]: print(f"  {f['score']:.2f}  {f['title']} ({f['year']}) · {f['kind']} · {f['n']} shots · colour {f['colour']}")
for k, v in chapters.items(): print(k, "→", " | ".join(f"{x['title'][:28]}" for x in v[:4]))
