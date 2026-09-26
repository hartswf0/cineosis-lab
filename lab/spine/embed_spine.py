"""Put the prompt-spine's generated images in the same space as the lab's archive shots.

Same CLIP (ViT-B-32 laion2b_s34b_b79k) and preprocessing as analyze.py; same 45 sign prototypes as
affinity.py (text of each sign + its picked exemplars), z-scored with the ARCHIVE's per-sign mean and
spread, so a generated image's sign reading sits on the archive's scale. Also records each image's six
nearest archive shots.

Writes spine/spine-emb.npy (float16), spine/spine-data.json and spine/thumbs/<key>.webp (320 px).
"""
import glob, json, os, re, sys
import numpy as np, torch, open_clip
from PIL import Image

H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); ROOT = os.path.dirname(LAB)
RA = os.path.dirname(ROOT)                      # "resurrecting atlantis"
C = os.path.join(LAB, "cache")
SRC = [("ANT/total-cinome.json", "cinome"), ("ANT/storyboard-cinome.json", "storyboard")]

def index_pngs():
    idx = {}
    for d in ("TIGER", "ANT", "CAT", "LIZARD"):
        for p in glob.glob(os.path.join(RA, d, "**", "*.png"), recursive=True):
            idx.setdefault(os.path.basename(p), p)
    return idx

def main():
    recs, idx = [], None
    for f, src in SRC:
        for r in json.load(open(os.path.join(RA, f))):
            p = r.get("image_path") or ""
            if not os.path.exists(p):
                idx = idx or index_pngs(); p = idx.get(os.path.basename(p), "")
            recs.append({**r, "_src": src, "_file": p if p and os.path.exists(p) else None})
    files = sorted({r["_file"] for r in recs if r["_file"]})
    print(len(recs), "records,", len(files), "images found", flush=True)
    key = {p: re.sub(r"[^A-Za-z0-9_-]", "", os.path.splitext(os.path.basename(p))[0].split("__")[0]) + "-" + os.path.basename(p)[-12:-4].replace("_", "")
           for p in files}
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model = model.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
    os.makedirs(os.path.join(H, "thumbs"), exist_ok=True)
    X = []
    with torch.no_grad():
        for b in range(0, len(files), 64):
            ims = []
            for p in files[b:b + 64]:
                im = Image.open(p).convert("RGB"); ims.append(pre(im))
                t = os.path.join(H, "thumbs", key[p] + ".webp")
                if not os.path.exists(t):
                    im.thumbnail((320, 320)); im.save(t, "WEBP", quality=72)
            f = model.encode_image(torch.stack(ims).to(dev)); f = f / f.norm(dim=-1, keepdim=True)
            X.append(f.cpu().numpy()); print(f"clip {min(b + 64, len(files))}/{len(files)}", flush=True)
        X = np.concatenate(X).astype(np.float32)
        # sign prototypes exactly as affinity.py builds them
        E = np.load(os.path.join(C, "emb.npy")); ids = json.load(open(os.path.join(C, "emb_ids.json")))
        row = {i: k for k, i in enumerate(ids)}
        g = [s for f in sorted(glob.glob(os.path.join(ROOT, "grounding", "g*.json"))) for s in json.load(open(f))]
        picks = json.load(open(os.path.join(ROOT, "picks.json"))); ns = [str(s["n"]) for s in g]
        Tp = []
        for s in g:
            texts = [f"a film still: {s['shot_criteria'][:300]}"] + [f"a film still of {q}" for q in s["queries"]]
            t = model.encode_text(tok(texts, context_length=77).to(dev)); t = t / t.norm(dim=-1, keepdim=True)
            m = t.mean(0); Tp.append((m / m.norm()).cpu().numpy())
        Tp = np.stack(Tp)
        Ip = np.stack([(lambda v: v / np.linalg.norm(v))(E[[row[c] for c, _ in picks.get(n, []) if c in row]].sum(0))
                       if any(c in row for c, _ in picks.get(n, [])) else Tp[j] for j, n in enumerate(ns)])
        # the prompt itself, embedded as text: how far did the picture land from what was asked?
        prompts = [r.get("operativeEkphrasis") or r.get("content") or "" for r in recs]
        PT = []
        for b in range(0, len(prompts), 128):
            t = model.encode_text(tok(prompts[b:b + 128], context_length=77).to(dev)); PT.append((t / t.norm(dim=-1, keepdim=True)).cpu().numpy())
        PT = np.concatenate(PT)
    S_arch = 0.5 * E @ Tp.T + 0.5 * E @ Ip.T
    mu, sd = S_arch.mean(0), S_arch.std(0) + 1e-6
    S = 0.5 * X @ Tp.T + 0.5 * X @ Ip.T
    P = torch.softmax(torch.tensor((S - mu) / sd) * 1.2, dim=1).numpy()
    near = np.argsort(-(X @ E.T), axis=1)[:, :6]
    lab = {s["id"]: s for s in json.load(open(os.path.join(LAB, "lab-data.json")))["shots"]}
    fi = {p: k for k, p in enumerate(files)}
    out = []
    for r, pt in zip(recs, PT):
        k = fi.get(r["_file"])
        o = {"id": r.get("id"), "src": r["_src"], "poem": r.get("poem"), "t": r.get("timestamp"), "line": r.get("content"),
             "syntagma": r.get("syntagmaType"), "image": r.get("imageType"), "function": r.get("cineosisFunction"),
             "prompt": r.get("operativeEkphrasis")}
        if k is not None:
            v = X[k]; top = np.argsort(-P[k])[:8]
            o.update({"k": k, "thumb": "spine/thumbs/" + key[r["_file"]] + ".webp",
                      "aff": [[ns[j], round(float(P[k, j]) * 100, 1)] for j in top],
                      "fit": round(float(v @ pt), 3),
                      "near": [[ids[j], round(float(v @ E[j]), 3)] for j in near[k]]})
        out.append(o)
    np.save(os.path.join(H, "spine-emb.npy"), X.astype(np.float16))
    shots = {i: {"title": lab[i]["title"], "year": lab[i].get("year"), "thumb": lab[i]["thumb"], "video": lab[i]["video"], "read_t": lab[i].get("read_t"), "aff_top": lab[i].get("aff_top", [])[:3]}
             for o in out for i, _ in o.get("near", []) if i in lab}
    signs = [{k: s[k] for k in ("n", "symbol", "name", "dom", "col", "row", "image")} for s in json.load(open(os.path.join(LAB, "lab-data.json")))["signs"]]
    json.dump({"model": "ViT-B-32 laion2b_s34b_b79k", "images": len(files), "signs": signs, "records": out, "archive": shots},
              open(os.path.join(H, "spine-data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("records", len(out), "with image", sum("k" in o for o in out), "archive neighbours", len(shots))

if __name__ == "__main__":
    main()
