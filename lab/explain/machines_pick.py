"""Pick frames for the depth and segmentation chapters by asking CLIP over the corpus (local clips only, blocked footage skipped).
Writes explain/machines/pick.json.   usage: lab/.venv/bin/python lab/explain/machines_pick.py"""
import json, os, numpy as np, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json"))); E = np.load(os.path.join(LAB, "cache", "emb.npy")); ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
ok = [k for k, i in enumerate(ids) if os.path.exists(os.path.join(LAB, "clips", i + ".mp4")) and not any(b in ((corpus.get(i) or {}).get("sourceTitle") or "").lower() for b in BLOCK)]
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32")
Q = {"flat": ["a painting hanging on a wall", "a map on a wall", "a television screen showing a picture", "a photograph held in hands", "a drawing on paper"],
     "deep": ["a long city street with buildings receding into the distance", "a road stretching to the horizon"],
     "busy": ["a kitchen table covered with objects", "a crowded street market", "a group of people standing together", "a workshop full of tools"]}
out = {}
with torch.no_grad():
    for g, qs in Q.items():
        T = m.encode_text(tok(qs)); T = (T / T.norm(dim=-1, keepdim=True)).numpy(); out[g] = []
        for q, t in zip(qs, T):
            s = E[ok] @ t; o = np.argsort(-s)[:6]
            out[g].append({"q": q, "ids": [ids[ok[j]] for j in o], "titles": [(corpus.get(ids[ok[j]]) or {}).get("sourceTitle") for j in o]})
            print(g, q, [(corpus.get(ids[ok[j]]) or {}).get("sourceTitle", "")[:22] for j in o[:4]])
json.dump(out, open(os.path.join(H, "machines", "pick.json"), "w"), ensure_ascii=False, indent=0)
