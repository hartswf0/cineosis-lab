"""Data for HOW THE LAB SEES (lab/how-it-sees.html): every number on screen is a real output of the lab's own models on the lab's own shots.
  clip     8 of our frames x 8 of their captions, scored by our copy of CLIP (OpenCLIP ViT-B/32, LAION-2B): the matching game, for real
  zero     the seed frame against CLIP's 20 subject words and 5 shot scales; the seed's image and caption as 512 numbers each
  map      every shot's place on the picture map, and the seed's CLIP neighbours
  dino     DINOv2 ViT-S/14 (pictures only, no words) on every thumbnail: the seed's DINO neighbours beside its CLIP ones, and its patch
           features drawn as colour (PCA) for three frames. Also writes cache/dino.npy so DINO can become a layer of the lab later.
  sam      the seed's cut-outs and tracked boxes (copied here: seg/ is not published)
  clap     6 heard clips x 6 descriptions, scored by CLAP; a spectrogram of each
  whisper  a shot's timed words and its spectrogram
  blip     six frames and their captions
  signs    the 45 signs; two read shots CLIP calls near-identical that were read as different signs, two that look nothing alike read as
           the same sign; the seed's reading, rival and its 45 machine affinities
usage: lab/.venv/bin/python lab/explain/build.py"""
import json, os, re, shutil, subprocess, collections
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
D = J("lab-data.json"); shots = D["shots"]; by = {s["id"]: s for s in shots}; idx = {s["id"]: i for i, s in enumerate(shots)}
cap = J("rushes/captions.json"); SND = J("sound-layer.json"); WORDS = J("words.json")
SEED = "21171e70-f59f-55b6-85c3-29691c97e312"
base = lambda t: re.sub(r"\s*\((part|reel) [ivx\d]+\)|\s*-\s*.*$", "", (t or "").lower()).strip()
def card(k, **x):
    s = by[k]; return {"id": k, "title": s["title"], "year": s.get("year"), "thumb": s["thumb"], "video": s.get("video"), "t": s.get("read_t") or 0, "cap": cap.get(k, ""), **x}
q8 = lambda v: [int(x) for x in np.round(v / (np.abs(v).max() + 1e-9) * 127)]
E = np.load(os.path.join(LAB, "cache/emb.npy")).astype(np.float32); eid = J("cache/emb_ids.json"); E /= np.linalg.norm(E, axis=1, keepdims=True); er = {k: i for i, k in enumerate(eid)}
import torch, open_clip
dev = "mps" if torch.backends.mps.is_available() else "cpu"
model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); model = model.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
def T(texts):
    with torch.no_grad(): t = model.encode_text(tok(texts).to(dev)).float().cpu().numpy()
    return t / np.linalg.norm(t, axis=1, keepdims=True)
out = {"seed": card(SEED, reading=by[SEED]["signs"][0], subjects=by[SEED].get("subjects"), scale=by[SEED].get("scale"), found=by[SEED].get("found", [])[:1])}
fq = by[SEED]["found"][0]   # the real contact sheet: what that same search phrase returned
out["sheet"] = [card(s["id"], rank=f["rank"]) for s in shots for f in (s.get("found") or []) if f["q"] == fq["q"]]
out["sheet"].sort(key=lambda c: c["rank"]); out["sheet"] = out["sheet"][:9]
# ---- the matching game: 8 frames, 8 captions, all different from each other
read = [s for s in shots if s.get("signs") and cap.get(s["id"]) and s["id"] in er]
pick = [SEED]
for s in sorted(read, key=lambda s: -(s["signs"][0].get("conf") or 0)):
    if len(pick) == 8: break
    if all(E[er[s["id"]]] @ E[er[p]] < .62 for p in pick) and base(s["title"]) not in {base(by[p]["title"]) for p in pick}: pick.append(s["id"])
Ti = E[[er[k] for k in pick]]; Tt = T([cap[k] for k in pick]); M = Ti @ Tt.T
P = np.exp(100 * M); P /= P.sum(1, keepdims=True)
out["clip"] = {"shots": [card(k) for k in pick], "cos": np.round(M, 3).tolist(), "p": np.round(P, 3).tolist()}
# ---- asking it questions it was never trained on
SUBJ = ["a human face in close-up", "a person", "a crowd of people", "hands", "an animal", "birds", "a machine", "a vehicle", "buildings and architecture", "a room interior", "a landscape",
        "water or the sea", "the sky and clouds", "plants or trees", "text or a title card", "an animated cartoon", "a diagram or map", "an object close-up", "a screen or television", "a microscope or abstract pattern"]
SCALE = ["extreme close-up", "close-up", "medium shot", "long shot", "extreme long shot"]
v = E[er[SEED]]; ps = np.exp(100 * (T([f"a photo of {x}" for x in SUBJ]) @ v)); ps /= ps.sum(); pc = np.exp(100 * (T([f"a {x} of a scene" for x in SCALE]) @ v)); pc /= pc.sum()
tc = T([cap[SEED]])[0]
out["zero"] = {"subjects": [[SUBJ[i], round(float(ps[i]), 3)] for i in np.argsort(-ps)], "scales": [[SCALE[i], round(float(pc[i]), 3)] for i in range(5)],
               "img": q8(v), "txt": q8(tc), "cos": round(float(v @ tc), 3), "wrong": [[w, round(float(T([w])[0] @ v), 3)] for w in ["a city street at night", "a man speaking at a desk", "an explosion"]]}
# ---- the map, and the seed's neighbours there
def near(V, row, ids, k=6):
    i = row[SEED]; sim = V @ V[i]; o, seen = [], {base(by[SEED]["title"])}
    for j in np.argsort(-sim)[1:500]:
        kk = ids[j]
        if kk in by and base(by[kk]["title"]) not in seen: seen.add(base(by[kk]["title"])); o.append(card(kk, sim=round(float(sim[j]), 3)))
        if len(o) == k: break
    return o
out["map"] = {"xy": [[round(s["xy"][0], 3), round(s["xy"][1], 3)] if s.get("xy") else None for s in shots], "seed": idx[SEED], "near": near(E, er, eid)}
# ---- DINO: pictures alone
from PIL import Image
dpath = os.path.join(LAB, "cache/dino.npy")
dino = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14", source="github" if not os.path.exists(os.path.expanduser("~/.cache/torch/hub/facebookresearch_dinov2_main")) else "local" if False else "github").to(dev).eval() if False else torch.hub.load(os.path.expanduser("~/.cache/torch/hub/facebookresearch_dinov2_main"), "dinov2_vits14", source="local").to(dev).eval()
import torchvision.transforms as tv
tf = tv.Compose([tv.Resize(224), tv.CenterCrop(224), tv.ToTensor(), tv.Normalize((.485, .456, .406), (.229, .224, .225))])
if os.path.exists(dpath): Dn = np.load(dpath)
else:
    Dn = np.zeros((len(shots), 384), np.float32); B = []
    def flush():
        with torch.no_grad(): f = dino(torch.stack([b[1] for b in B]).to(dev)).float().cpu().numpy()
        for (i, _), x in zip(B, f): Dn[i] = x
        B.clear()
    for i, s in enumerate(shots):
        try: B.append((i, tf(Image.open(os.path.join(LAB, s["thumb"])).convert("RGB"))))
        except Exception: continue
        if len(B) == 64: flush()
        if i % 2000 == 0: print("dino", i, flush=True)
    if B: flush()
    np.save(dpath, Dn)
Dn = Dn / (np.linalg.norm(Dn, axis=1, keepdims=True) + 1e-9)
out["dino"] = {"near": near(Dn, idx, [s["id"] for s in shots]), "clip_near": out["map"]["near"]}
def patches(k):   # DINO's patch features, three main directions drawn as red, green, blue
    p = os.path.join(LAB, "frames", k + ".jpg"); im = Image.open(p if os.path.exists(p) else os.path.join(LAB, by[k]["thumb"])).convert("RGB")
    w, h = im.size; s = 448 / max(w, h); W, Hh = int(w * s) // 14 * 14, int(h * s) // 14 * 14
    x = tv.Compose([tv.Resize((Hh, W)), tv.ToTensor(), tv.Normalize((.485, .456, .406), (.229, .224, .225))])(im)[None].to(dev)
    with torch.no_grad(): f = dino.forward_features(x)["x_norm_patchtokens"][0].float().cpu().numpy()
    f = f - f.mean(0); u, sv, vt = np.linalg.svd(f, full_matrices=False); c = f @ vt[:3].T
    c = (c - np.percentile(c, 2, 0)) / (np.percentile(c, 98, 0) - np.percentile(c, 2, 0) + 1e-9); c = np.clip(c, 0, 1).reshape(Hh // 14, W // 14, 3)
    Image.fromarray((c * 255).astype(np.uint8)).resize((W, Hh), Image.NEAREST).save(os.path.join(H, f"dino_{k}.png")); return f"explain/dino_{k}.png"
out["dino"]["patch"] = [{"id": k, "thumb": by[k]["thumb"], "frame": f"frames/{k}.jpg" if os.path.exists(os.path.join(LAB, "frames", k + ".jpg")) else by[k]["thumb"], "png": patches(k)} for k in [SEED] + pick[1:3]]
# ---- SAM: the seed's cut-outs (copied: seg/ is not published)
g = by[SEED]["segments"]; objs = []
for o in g["objects"][:4]:
    for key in ("png", "sprite"):
        if o.get(key) and os.path.exists(os.path.join(LAB, o[key])): dst = f"explain/sam_{SEED[:8]}_{o['k']}_{key}.png"; shutil.copy(os.path.join(LAB, o[key]), os.path.join(LAB, dst)); o[key] = dst
    objs.append({k: o.get(k) for k in ("label", "role", "png", "bbox", "boxes", "sprite", "sw", "sh")})
out["sam"] = {"objects": objs, "fps": g["fps"], "t0": g["t0"], "frames": g["frames"], "frame": f"frames/{SEED}.jpg"}
# ---- spectrograms: sound drawn as a picture (time across, pitch up, loud is bright)
def spec(k, t, dur=4.0):
    src = os.path.join(LAB, "clips", k + ".mp4"); dst = os.path.join(H, f"spec_{k[:8]}.png")
    if not os.path.exists(src): return None
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, t)), "-t", str(dur), "-i", src, "-lavfi", "showspectrumpic=s=640x200:legend=0:scale=log:fscale=log:color=magma:gain=2", dst])
    return f"explain/{os.path.basename(dst)}" if os.path.exists(dst) else None
# ---- CLAP: the same game with sound
heard = SND["heard"]; cid = J("odyssey/cache/ears/ids.json"); C = np.load(os.path.join(LAB, "odyssey/cache/ears/clap.npy")).astype(np.float32); cr = {k: i for i, k in enumerate(cid)}
cands = [s for s in shots if s["id"] in heard and s["id"] in cr and os.path.exists(os.path.join(LAB, "clips", s["id"] + ".mp4")) and heard[s["id"]][0][1] > 2.2]
cands.sort(key=lambda s: -heard[s["id"]][0][1]); cl, labs = [], set()
for s in cands:
    l = heard[s["id"]][0][0]
    if l in labs or l == "silence": continue
    labs.add(l); cl.append(s["id"])
    if len(cl) == 6: break
from transformers import ClapModel, ClapProcessor
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
texts = [f"the sound of {heard[k][0][0]}" for k in cl]
with torch.no_grad(): tt = cm.get_text_features(**cp(text=texts, return_tensors="pt", padding=True)).numpy()
tt /= np.linalg.norm(tt, axis=1, keepdims=True); A = C[[cr[k] for k in cl]]; A /= np.linalg.norm(A, axis=1, keepdims=True); MC = A @ tt.T
out["clap"] = {"shots": [card(k, heard=heard[k], spec=spec(k, max(0, (by[k].get("read_t") or 0) - 1))) for k in cl], "texts": texts, "cos": np.round(MC, 3).tolist()}
# ---- Whisper: words with their times
wk = next(k for k in sorted(WORDS, key=lambda k: -len(WORDS[k])) if os.path.exists(os.path.join(LAB, "clips", k + ".mp4")) and 12 <= len(WORDS[k]) <= 40 and k in by)
out["whisper"] = card(wk, words=WORDS[wk], spec=spec(wk, 0, min(12, WORDS[wk][-1][1] + 1)))
# ---- BLIP: six frames, six sentences
bl = [k for k in pick[1:]][:6]
out["blip"] = [card(k) for k in bl]
# ---- the signs: the table, and where CLIP and the reading part ways
out["signs"] = [{k: s.get(k) for k in ("n", "symbol", "name", "dom", "col", "row", "question", "difference", "gloss", "confusions", "ceiling")} for s in D["signs"]]
R = [s for s in shots if s.get("signs") and s["id"] in er]; RV = E[[er[s["id"]] for s in R]]; S = RV @ RV.T
alike, unlike = [], []
for i in range(len(R)):
    for j in range(i + 1, len(R)):
        a, b = R[i], R[j]
        if base(a["title"]) == base(b["title"]): continue
        same = str(a["signs"][0]["n"]) == str(b["signs"][0]["n"])
        if not same: alike.append((S[i, j], i, j))
        else: unlike.append((S[i, j], i, j))
alike.sort(reverse=True); unlike.sort()
def pair(t):
    c, i, j = t; return {"cos": round(float(c), 3), "a": card(R[i]["id"], reading=R[i]["signs"][0]), "b": card(R[j]["id"], reading=R[j]["signs"][0])}
used = set(); al = []
for t in alike:
    if t[1] in used or t[2] in used: continue
    used |= {t[1], t[2]}; al.append(pair(t))
    if len(al) == 2: break
out["alike"] = al; out["unlike"] = [pair(t) for t in unlike[:2]]
out["seed_aff"] = sorted([[n, v] for n, v in by[SEED]["affinity"].items()], key=lambda x: -x[1])
out["counts"] = {"shots": len(shots), "films": len({s["slug"] for s in shots}), "read": len(R) if False else sum(1 for s in shots if s.get("signs")), "found": sum(1 for s in shots if s.get("found"))}
json.dump(out, open(os.path.join(H, "film.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("clip pick", [by[k]["title"][:20] for k in pick]); print("diag mean", float(np.mean(np.diag(M))), "off", float((M.sum() - np.trace(M)) / 56))
print("alike", [(p["cos"], p["a"]["reading"]["n"], p["b"]["reading"]["n"]) for p in al]); print("unlike", [(p["cos"], p["a"]["reading"]["n"], p["b"]["reading"]["n"]) for p in out["unlike"]])
print("clap", texts, np.round(np.diag(MC), 3)); print("whisper", by[wk]["title"], " ".join(w[0] for w in WORDS[wk])[:120])
print(os.path.getsize(os.path.join(H, "film.json")) // 1024, "KB")
