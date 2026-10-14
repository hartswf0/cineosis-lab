"""THE MACHINES WATCH · the eyes. Fresh examples for three models over the 15,149-shot corpus.
  clip   asked for things the archive cannot hold (a ghost, a dragon, the year 3000, a broken heart, nothing at all) and a few it can;
         its best answer and score for each, and the score spread, to show it never says no
  blip   captions for 240 random shots (fixed seed): the captions, their most repeated words, invented words
  dino   DINOv2 on 3,000 random thumbnails: pairs DINO calls near twins that CLIP thinks are about different things
Footage kept out of examples is skipped. Writes explain/machines/eyes.json.   usage: lab/.venv/bin/python lab/explain/machines_eyes.py"""
import json, os, random, collections, re
import numpy as np, torch
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json"))); E = np.load(os.path.join(LAB, "cache", "emb.npy")); ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
def title(i): return (corpus.get(i) or {}).get("sourceTitle") or ""
def year(i): return (corpus.get(i) or {}).get("sourceYear")
okid = [k for k, i in enumerate(ids) if not any(b in title(i).lower() for b in BLOCK) and os.path.exists(os.path.join(LAB, "thumbs", i + ".jpg"))]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
def card(i, **kw): return {"id": i, "title": title(i), "year": year(i), "thumb": f"thumbs/{i}.jpg", "clip": f"clips/{i}.mp4" if os.path.exists(os.path.join(LAB, "clips", i + ".mp4")) else None, **kw}
out = {}
# CLIP
import open_clip
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32")
ASK = ["a ghost", "a dragon", "the year 3000", "a broken heart", "a photo of nothing at all", "a dog driving a car", "the smell of bread", "a person crying",
       "a train", "a kiss", "an explosion", "a cat"]
with torch.no_grad():
    T = m.encode_text(tok(ASK)); T = (T / T.norm(dim=-1, keepdim=True)).numpy()
Ek = E[okid]; S = T @ Ek.T
out["clip"] = []
for a, row in zip(ASK, S):
    o = np.argsort(-row); best = [card(ids[okid[j]], score=round(float(row[j]), 3)) for j in o[:4]]
    out["clip"].append({"ask": a, "best": best, "median": round(float(np.median(row)), 3), "p99": round(float(np.percentile(row, 99)), 3)})
    print("CLIP", a, "->", [(b["title"][:28], b["score"]) for b in best[:2]], "median", round(float(np.median(row)), 3))
# BLIP
from transformers import BlipProcessor, BlipForConditionalGeneration
bp = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large"); bm = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large").to(dev).eval()
random.seed(5); samp = random.sample(okid, 240); caps = []
for k in range(0, len(samp), 16):
    ims = [Image.open(os.path.join(LAB, "thumbs", ids[j] + ".jpg")).convert("RGB") for j in samp[k:k + 16]]
    with torch.no_grad():
        g = bm.generate(**bp(images=ims, return_tensors="pt").to(dev), max_new_tokens=30)
    for j, c in zip(samp[k:k + 16], bp.batch_decode(g, skip_special_tokens=True)): caps.append(card(ids[j], cap=c))
STOP = set("a an the of in on at with and to is are there it its this that his her their from by for as".split())
wc = collections.Counter(w for c in caps for w in re.findall(r"[a-z]+", c["cap"].lower()) if w not in STOP)
openings = collections.Counter(" ".join(c["cap"].split()[:3]) for c in caps)
out["blip"] = {"caps": caps, "words": wc.most_common(25), "openings": openings.most_common(8), "invented": [c for c in caps if re.search(r"\barafe?d|araff", c["cap"])]}
print("BLIP words", wc.most_common(12)); print("openings", openings.most_common(5)); print("arafed", len(out["blip"]["invented"]))
# DINO
dm = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14").to(dev).eval()
import torchvision.transforms as TT
tf = TT.Compose([TT.Resize(224), TT.CenterCrop(224), TT.ToTensor(), TT.Normalize((.485, .456, .406), (.229, .224, .225))])
random.seed(9); ds = random.sample(okid, 3000); F = []
for k in range(0, len(ds), 64):
    x = torch.stack([tf(Image.open(os.path.join(LAB, "thumbs", ids[j] + ".jpg")).convert("RGB")) for j in ds[k:k + 64]]).to(dev)
    with torch.no_grad(): f = dm(x)
    F.append(torch.nn.functional.normalize(f, dim=-1).cpu().numpy())
F = np.concatenate(F); Dsim = F @ F.T; Csim = E[ds] @ E[ds].T
np.fill_diagonal(Dsim, -1); src = [(corpus.get(ids[j]) or {}).get("sourceSlug") for j in ds]
pairs = []
iu = np.triu_indices(len(ds), 1); dv, cv = Dsim[iu], Csim[iu]
score = dv - cv                                   # alike in form, unlike in meaning
for q in np.argsort(-score)[:400]:
    a, b = iu[0][q], iu[1][q]
    if src[a] == src[b] or dv[q] < .55: continue
    if any(a in (p[0], p[1]) or b in (p[0], p[1]) for p in pairs): continue
    pairs.append((a, b, float(dv[q]), float(cv[q])))
    if len(pairs) >= 16: break
out["dino"] = [{"a": card(ids[ds[a]]), "b": card(ids[ds[b]]), "dino": round(d, 3), "clip": round(c, 3)} for a, b, d, c in pairs]
out["dino_typical"] = {"dino_median": round(float(np.median(dv)), 3), "clip_median": round(float(np.median(cv)), 3)}
print("DINO twins", [(p["a"]["title"][:20], p["b"]["title"][:20], p["dino"], p["clip"]) for p in out["dino"][:8]])
json.dump(out, open(os.path.join(H, "machines", "eyes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
