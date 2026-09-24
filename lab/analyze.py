"""Colour, CLIP subjects/scale and similarity layout for every downloaded thumbnail.

Writes cache/analysis.json (id -> palette, hue, lum, sat, subjects, scale, xy, sim) and cache/emb.npy.
Re-runnable: embeddings are cached per id.
"""
import json, os, sys
import cv2, numpy as np, torch, open_clip
from PIL import Image

LAB = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(LAB, "cache")

SUBJECTS = ["a human face in close-up", "a person", "a crowd of people", "hands", "an animal", "birds",
            "a machine", "a vehicle", "buildings and architecture", "a room interior", "a landscape",
            "water or the sea", "the sky and clouds", "plants or trees", "text or a title card",
            "an animated cartoon", "a diagram or map", "an object close-up", "a screen or television",
            "a microscope or abstract pattern"]
LABELS = ["face close-up", "person", "crowd", "hands", "animal", "birds", "machine", "vehicle", "architecture",
          "interior", "landscape", "water", "sky", "plants", "text", "animation", "diagram", "object",
          "screen", "pattern"]
SCALES = ["extreme close-up", "close-up", "medium shot", "long shot", "extreme long shot"]

def colour(path):
    img = cv2.imread(path)
    if img is None:
        return None
    small = cv2.resize(img, (64, 48), interpolation=cv2.INTER_AREA)
    px = small.reshape(-1, 3).astype(np.float32)
    k = 5
    _, lab, cen = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(lab.ravel(), minlength=k)
    order = np.argsort(-counts)
    cen_bgr = cen[order].clip(0, 255).astype(np.uint8)
    palette = ["#%02x%02x%02x" % (int(c[2]), int(c[1]), int(c[0])) for c in cen_bgr]
    hsv = cv2.cvtColor(cen_bgr.reshape(1, -1, 3), cv2.COLOR_BGR2HSV)[0].astype(float)  # H 0-179, S,V 0-255
    w = counts[order] / counts.sum()
    sat_w = (hsv[:, 1] / 255) * (hsv[:, 2] / 255) * w
    hue = None
    if sat_w.sum() > 0.03:  # enough chroma to name a hue (faded colour stock included)
        ang = np.deg2rad(hsv[:, 0] * 2)
        hue = float((np.rad2deg(np.arctan2((np.sin(ang) * sat_w).sum(), (np.cos(ang) * sat_w).sum())) + 360) % 360)
    full = cv2.cvtColor(small, cv2.COLOR_BGR2HSV).reshape(-1, 3) / 255.0
    return {"palette": palette, "hue": None if hue is None else round(hue, 1),
            "lum": round(float(full[:, 2].mean()), 3), "sat": round(float(full[:, 1].mean()), 3)}

def main():
    corpus = json.load(open(os.path.join(C, "corpus.json")))
    ids = [i for i in corpus if os.path.exists(os.path.join(LAB, "thumbs", i + ".jpg"))]
    print(len(ids), "thumbnails", flush=True)
    out = {}
    for n, i in enumerate(ids):
        c = colour(os.path.join(LAB, "thumbs", i + ".jpg"))
        if c: out[i] = c
    print("colour done", flush=True)

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    tok = open_clip.get_tokenizer("ViT-B-32")
    model = model.to(dev).eval()
    emb_path, ids_path = os.path.join(C, "emb.npy"), os.path.join(C, "emb_ids.json")
    cache = {}
    if os.path.exists(emb_path):
        E0, I0 = np.load(emb_path), json.load(open(ids_path))
        cache = {i: E0[k] for k, i in enumerate(I0)}
    todo = [i for i in ids if i in out and i not in cache]
    with torch.no_grad():
        for b in range(0, len(todo), 64):
            batch = todo[b:b + 64]
            ims = []
            for i in batch:
                try:
                    ims.append(pre(Image.open(os.path.join(LAB, "thumbs", i + ".jpg")).convert("RGB")))
                except Exception:
                    ims.append(None)
            keep = [(i, im) for i, im in zip(batch, ims) if im is not None]
            if not keep: continue
            x = torch.stack([im for _, im in keep]).to(dev)
            f = model.encode_image(x); f = f / f.norm(dim=-1, keepdim=True)
            for (i, _), v in zip(keep, f.cpu().numpy()):
                cache[i] = v
            print(f"clip {min(b + 64, len(todo))}/{len(todo)}", flush=True)
        ids_e = [i for i in ids if i in cache]
        E = np.stack([cache[i] for i in ids_e]).astype(np.float32)
        np.save(emb_path, E); json.dump(ids_e, open(ids_path, "w"))

        def text(prompts):
            t = model.encode_text(tok(prompts).to(dev)); return (t / t.norm(dim=-1, keepdim=True)).cpu().numpy()
        Ts = text([f"a film still of {s}" for s in SUBJECTS])
        Tc = text([f"a film still, {s}" for s in SCALES])
    ps = torch.softmax(torch.tensor(E @ Ts.T) * 100, dim=1).numpy()
    pc = torch.softmax(torch.tensor(E @ Tc.T) * 100, dim=1).numpy()
    for k, i in enumerate(ids_e):
        top = np.argsort(-ps[k])[:3]
        out[i]["subjects"] = [{"label": LABELS[j], "p": round(float(ps[k, j]), 3)} for j in top]
        out[i]["scale"] = SCALES[int(np.argmax(pc[k]))]

    from sklearn.manifold import TSNE
    xy = TSNE(n_components=2, perplexity=35, init="pca", random_state=7, metric="cosine").fit_transform(E)
    xy = (xy - xy.min(0)) / (xy.max(0) - xy.min(0))
    one = TSNE(n_components=1, perplexity=35, init="pca", random_state=7, metric="cosine").fit_transform(E)[:, 0]
    rank = np.argsort(np.argsort(one))
    for k, i in enumerate(ids_e):
        out[i]["xy"] = [round(float(xy[k, 0]), 4), round(float(xy[k, 1]), 4)]
        out[i]["sim"] = int(rank[k])
    json.dump(out, open(os.path.join(C, "analysis.json"), "w"))
    print("DONE analysed", len(out), flush=True)

if __name__ == "__main__":
    main()
