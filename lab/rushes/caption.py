"""What each clip shows, in words: BLIP (large) reads every clip's thumbnail (odyssey/thumbs, the archive's 28,611) into a short caption.
Resumable; cached in rushes/captions.json by clip id. The narration Rushes drafts is written from these, so it says only what is seen.
usage: lab/.venv/bin/python lab/rushes/caption.py [--limit N]"""
import json, os, sys, glob, time
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
OUT = os.path.join(H, "captions.json")
cap = json.load(open(OUT)) if os.path.exists(OUT) else {}
files = sorted(glob.glob(os.path.join(L, "odyssey", "thumbs", "*.jpg")))
KF = os.path.join(H, "keys.json")   # Rushes' clips first, its good starts first of all
if os.path.exists(KF):
    kj = json.load(open(KF)); order = [kj["keys"][i] for i in kj["starts"]] + kj["keys"]; seen = set(); pri = []
    for k in order:
        if k not in seen: seen.add(k); pri.append(k)
    have = {os.path.basename(f)[:-4]: f for f in files}; files = [have[k] for k in pri if k in have] + [f for f in files if os.path.basename(f)[:-4] not in seen]
todo = [f for f in files if os.path.basename(f)[:-4] not in cap]
if "--limit" in sys.argv: todo = todo[: int(sys.argv[sys.argv.index("--limit") + 1])]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
P = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
M = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large", torch_dtype=torch.float16 if dev == "mps" else torch.float32).to(dev).eval()
print(len(files), "thumbs ·", len(cap), "done ·", len(todo), "to read on", dev, flush=True)
t0 = time.time(); B = 48
for k in range(0, len(todo), B):
    batch = todo[k:k + B]; ims = []
    for f in batch:
        try: ims.append(Image.open(f).convert("RGB"))
        except Exception: ims.append(Image.new("RGB", (64, 64)))
    inp = P(images=ims, text=["a film still of"] * len(ims), return_tensors="pt").to(dev)
    if dev == "mps": inp["pixel_values"] = inp["pixel_values"].half()
    with torch.no_grad(): out = M.generate(**inp, max_new_tokens=22, num_beams=1, repetition_penalty=1.3)
    for f, o in zip(batch, out):
        c = P.decode(o, skip_special_tokens=True).replace("a film still of", "").strip()
        cap[os.path.basename(f)[:-4]] = c
    if (k // B) % 20 == 0 or k + B >= len(todo):
        json.dump(cap, open(OUT, "w"), ensure_ascii=False)
        el = time.time() - t0; done = k + len(batch); print(f"{done}/{len(todo)} · {done / el:.1f}/s · eta {(len(todo) - done) / max(.1, done / el) / 60:.0f} min · {c}", flush=True)
json.dump(cap, open(OUT, "w"), ensure_ascii=False)
