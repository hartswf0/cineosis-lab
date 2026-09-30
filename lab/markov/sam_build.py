"""The cast for Markov SAM: every tracked SAM 2.1 figure the lab has cut out of a read shot (seg_track.py), read by the same CLIP
that reads the shots and the words, so a line can call for figures the way it calls for shots.
Each figure's vector is half what it looks like (the cut-out on grey) and half what it was named (its description).
Writes markov/sam.json (figures, in order) + markov/sam-emb.bin (int8, 512 per figure).   usage: .venv/bin/python markov/sam_build.py"""
import json, os
import numpy as np, torch, open_clip
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
POET = ("cdmx", "temple", "ding", "presence", "afro")            # never published
shots = json.load(open(os.path.join(LAB, "lab-data.json")))["shots"]
figs = []
for s in shots:
    g = s.get("segments") or {}
    if any(p in (s.get("collections") or []) for p in POET) or any(("/" + p + "/") in (s.get("thumb") or "") for p in POET): continue
    for o in g.get("objects") or []:
        if not os.path.exists(os.path.join(LAB, o["png"])) or o.get("area", 0) > .8: continue      # a mask of nearly the whole frame is a background, not a figure
        bx = o.get("union") or o["bbox"]
        figs.append({"shot": s["id"], "k": o["k"], "title": s.get("title"), "year": s.get("year"), "png": o["png"], "sprite": o.get("sprite"), "sw": o.get("sw"), "sh": o.get("sh"),
                     "frames": g.get("frames"), "fps": g.get("fps"), "desc": o.get("desc") or o.get("label") or "figure", "role": o.get("role"), "box": [round(x, 4) for x in bx], "present": o.get("present", 1)})
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m = m.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
out = np.zeros((len(figs), 512), np.float32)
for i in range(0, len(figs), 64):
    B = figs[i:i + 64]; ims = []
    for f in B:
        im = Image.open(os.path.join(LAB, f["png"])).convert("RGBA"); f["w"], f["h"] = im.size
        side = max(im.size); bg = Image.new("RGBA", (side, side), (118, 118, 118, 255)); bg.alpha_composite(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2)); ims.append(pre(bg.convert("RGB")))
    with torch.no_grad():
        a = m.encode_image(torch.stack(ims).to(dev)).float(); a = a / a.norm(dim=-1, keepdim=True)
        t = m.encode_text(tok([f["desc"] if len(f["desc"]) > 12 else "a photo of a " + f["desc"] for f in B]).to(dev)).float(); t = t / t.norm(dim=-1, keepdim=True)
        generic = torch.tensor([f["desc"] in ("figure", "object") for f in B], device=dev).float()[:, None]
        e = a + (1 - generic) * t; e = (e / e.norm(dim=-1, keepdim=True)).cpu().numpy()
    out[i:i + len(B)] = e; print(i, "of", len(figs), flush=True)
sc = float(np.abs(out).max() / 127)
np.clip(np.round(out / sc), -127, 127).astype(np.int8).tofile(os.path.join(H, "sam-emb.bin"))
json.dump({"n": len(figs), "dim": 512, "scale": sc, "model": "ViT-B-32 openai", "figs": figs}, open(os.path.join(H, "sam.json"), "w"), separators=(",", ":"))
print("figures", len(figs), "from", len({f["shot"] for f in figs}), "shots")
