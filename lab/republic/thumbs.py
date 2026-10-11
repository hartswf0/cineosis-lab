"""MARKOV SAM · REPUBLIC: a still for every place (FAR + MID + NEAR composited, 400 wide) for the chooser and the x-sheet, where the
FAR plate alone would show its painted-out middle.   usage: republic/.tts/bin/python republic/thumbs.py"""
import glob, os
from PIL import Image
for far in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "planes", "*", "p*_far.webp"))):
    base = far[:-9]; out = base + "_thumb.jpg"
    if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(far): continue
    try:
        im = Image.open(far).convert("RGBA")
        for k in ("mid", "near"): im.alpha_composite(Image.open(f"{base}_{k}.webp").convert("RGBA"))
        im = im.convert("RGB"); im.thumbnail((400, 400)); im.save(out, quality=78)
    except Exception as e: print("skip", base, e)
