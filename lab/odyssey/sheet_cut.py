"""Contact sheet of one scene's composed cut, in order: role, seconds, fit, what the frame must show.   usage: python3 sheet_cut.py OD-B12-S03"""
import json, os, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); cut = json.load(open(os.path.join(H, "cuts.json")))["cuts"][sys.argv[1]]
sc = next(x for x in json.load(open(os.path.join(H, "scenes.json")))["scenes"] if x["id"] == sys.argv[1])
W, T, COLS = 260, 195, 6; sh = cut["shots"]; rows = (len(sh) + COLS - 1) // COLS
im = Image.new("RGB", (W * COLS, rows * (T + 64) + 40), (12, 12, 12)); dr = ImageDraw.Draw(im)
F = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
dr.text((6, 6), f"{sys.argv[1]}  {sc['title']}  ·  {sc['sign']['symbol']} {sc['sign']['name']}  ·  {cut['palette']}  ·  {cut['world'][:120]}", fill=(232, 192, 112), font=F)
for k, x in enumerate(sh):
    X, Y = (k % COLS) * W, 30 + (k // COLS) * (T + 64)
    try: t = Image.open(os.path.join(H, "thumbs", x["clip"] + ".jpg")).convert("RGB"); t.thumbnail((W - 6, T)); im.paste(t, (X + 3, Y))
    except Exception: pass
    dr.text((X + 4, Y + 2), f"{k + 1} b{x['beat'] + 1} {x['role']} {x['sec']}s {x.get('fit', 0):.3f}{'  FIG' if x.get('figure') else ''}", fill=(196, 244, 106), font=F)
    for n, l in enumerate(textwrap.wrap(x["see"] or "", 38)[:3]): dr.text((X + 4, Y + T + 4 + n * 15), l, fill=(210, 204, 192), font=F)
im.save(os.path.join(H, "cache", f"cut-{sys.argv[1]}.jpg"), quality=82)
