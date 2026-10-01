"""Embed every phrase the page can show offline (shannon/phrases.json from dump_phrases.mjs) -> shannon/texts.json"""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import numpy as np, open_clip, torch
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
ph = json.load(open(os.path.join(H, "phrases.json")))
with torch.no_grad():
    E = np.concatenate([(lambda e: (e / e.norm(dim=-1, keepdim=True)).numpy())(m.encode_text(tok(ph[i:i + 256])).float()) for i in range(0, len(ph), 256)])
json.dump({t: [round(float(v), 4) for v in e] for t, e in zip(ph, E)}, open(os.path.join(H, "texts.json"), "w"), separators=(",", ":"))
print(len(ph), "phrases embedded")
