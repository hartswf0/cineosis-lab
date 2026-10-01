"""How much colour each thumbnail really has (the archive's colorMode calls faded or tinted black and white 'color'):
the 80th-percentile HSV saturation over the frame, resumable. Writes cache/sat.json {id: s}.   usage: ../.venv/bin/python saturation.py"""
import json, os, numpy as np
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, "cache", "sat.json")
out = json.load(open(P)) if os.path.exists(P) else {}
for i in json.load(open(os.path.join(H, "cache", "ids.json"))):
    if i in out: continue
    try: a = np.asarray(Image.open(os.path.join(H, "thumbs", i + ".jpg")).convert("RGB").resize((96, 72)).convert("HSV"))[..., 1] / 255.0; out[i] = round(float(np.percentile(a, 80)), 3)
    except Exception: out[i] = None
json.dump(out, open(P, "w")); v = np.array([x for x in out.values() if x is not None]); print(len(out), "thumbs · saturation quartiles", np.percentile(v, [10, 25, 50, 75, 90]).round(3))
