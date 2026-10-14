"""DINO twins without title cards: DINOv2 on 4,000 random thumbnails that CLIP does not take for text on a plain ground;
pairs DINO calls near twins while CLIP thinks they show different things, from different films. Adds to explain/machines/eyes.json.
usage: lab/.venv/bin/python lab/explain/machines_dino.py"""
import json, os, random, numpy as np, torch, open_clip
from PIL import Image
import torchvision.transforms as TT
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json"))); E = np.load(os.path.join(LAB, "cache", "emb.npy")); ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32")
with torch.no_grad(): T = m.encode_text(tok(["white text on a black background", "a title card with words", "credits text on a screen", "a photograph of a real scene"])); T = (T / T.norm(dim=-1, keepdim=True)).numpy()
P = E @ T.T; textish = P[:, :3].max(1) - P[:, 3]
ok = [k for k, i in enumerate(ids) if os.path.exists(os.path.join(LAB, "thumbs", i + ".jpg")) and not any(b in ((corpus.get(i) or {}).get("sourceTitle") or "").lower() for b in BLOCK) and textish[k] < np.percentile(textish, 70)]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
dm = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14").to(dev).eval()
tf = TT.Compose([TT.Resize(224), TT.CenterCrop(224), TT.ToTensor(), TT.Normalize((.485, .456, .406), (.229, .224, .225))])
random.seed(9); ds = random.sample(ok, 4000); F = []
for k in range(0, len(ds), 64):
    x = torch.stack([tf(Image.open(os.path.join(LAB, "thumbs", ids[j] + ".jpg")).convert("RGB")) for j in ds[k:k + 64]]).to(dev)
    with torch.no_grad(): F.append(torch.nn.functional.normalize(dm(x), dim=-1).cpu().numpy())
F = np.concatenate(F); Dsim = F @ F.T; Csim = E[ds] @ E[ds].T; src = [(corpus.get(ids[j]) or {}).get("sourceSlug") for j in ds]
iu = np.triu_indices(len(ds), 1); dv, cv = Dsim[iu], Csim[iu]; pairs = []
for q in np.argsort(-(dv - cv))[:3000]:
    a, b = iu[0][q], iu[1][q]
    if src[a] == src[b] or dv[q] < .6 or any(x in p[:2] for p in pairs for x in (a, b)): continue
    pairs.append((a, b, float(dv[q]), float(cv[q])))
    if len(pairs) >= 20: break
card = lambda i: {"id": i, "title": (corpus.get(i) or {}).get("sourceTitle"), "year": (corpus.get(i) or {}).get("sourceYear"), "thumb": f"thumbs/{i}.jpg", "clip": f"clips/{i}.mp4" if os.path.exists(os.path.join(LAB, "clips", i + ".mp4")) else None}
p = os.path.join(H, "machines", "eyes.json"); e = json.load(open(p))
e["dino_cards_note"] = "before removing text frames, DINO's closest unlike-meaning pairs were all title cards"; e["dino_cards"] = e.get("dino", [])[:8]
e["dino"] = [{"a": card(ids[ds[a]]), "b": card(ids[ds[b]]), "dino": round(d, 3), "clip": round(c, 3)} for a, b, d, c in pairs]
json.dump(e, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
print([(x["a"]["title"][:22], x["b"]["title"][:22], x["dino"], x["clip"]) for x in e["dino"][:12]])
