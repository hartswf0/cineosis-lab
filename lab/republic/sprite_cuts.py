"""MARKOV FOUND · REPUBLIC: a sprite must stay one figure. Where its clip cuts to another shot the track jumps to whatever is there;
each sprite is shortened to before its first jump (frame-to-frame difference of the figure, against that sprite's own median),
and one that jumps before its sixth frame goes back to the still.   usage: republic/.tts/bin/python republic/sprite_cuts.py"""
import json, os
import numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
P = json.load(open(os.path.join(H, "planes.json")))
for name, figs in P["cast"].items():
    if not figs or not figs[0].get("sp"): continue
    sp = figs[0]["sp"]; sh = np.asarray(Image.open(os.path.join(L, sp["f"])).convert("RGBA")).astype(np.float32)
    fr = [sh[:, k * sp["w"]:(k + 1) * sp["w"]] for k in range(sp["n"])]
    d = []
    for a, b in zip(fr, fr[1:]):
        wa, wb = a[..., 3:] / 255, b[..., 3:] / 255
        d.append(float((np.abs(a[..., :3] * wa - b[..., :3] * wb).mean() + 40 * np.abs(wa - wb).mean())))
    med = float(np.median(d)) + 1e-3; cut = next((k + 1 for k, x in enumerate(d) if x > max(3.2 * med, med + 12)), sp["n"])
    if cut < sp["n"]:
        if cut < 6: figs[0].pop("sp"); print(f"{name:20} jumps at {cut} — back to the still")
        else:
            Image.fromarray(sh[:, :cut * sp["w"]].astype(np.uint8)).save(os.path.join(L, sp["f"]), "WEBP", quality=72, method=6); sp["n"] = cut
            print(f"{name:20} cut to {cut} frames")
json.dump(P, open(os.path.join(H, "planes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
