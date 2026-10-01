"""A contact sheet for one scene: each beat, its best grounds then its best actions.   usage: python3 sheet.py OD-B01-S03 [out.jpg]"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); d = json.load(open(os.path.join(H, "scenes.json"))); s = next(x for x in d["scenes"] if x["id"] == sys.argv[1])
W, T = 200, 150; rows = len(s["beats"]); im = Image.new("RGB", (W * 8, rows * (T + 34) + 30), (12, 12, 12)); dr = ImageDraw.Draw(im)
try: F = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
except Exception: F = None
dr.text((6, 6), f"{s['id']}  {s['title']}  ·  {s['sign']['symbol']} {s['sign']['name']}", fill=(232, 192, 112), font=F)
for r, b in enumerate(s["beats"]):
    y = 30 + r * (T + 34); dr.text((6, y), b["text"][:170], fill=(220, 214, 200), font=F)
    for k, (i, sc) in enumerate(b["ground"][:3] + b["action"][:5]):
        try: t = Image.open(os.path.join(H, "thumbs", i + ".jpg")).convert("RGB"); t.thumbnail((W - 4, T)); im.paste(t, (k * W + 2, y + 18))
        except Exception: pass
        dr.text((k * W + 4, y + 20), ("G " if k < 3 else "A ") + f"{sc:.2f}", fill=(196, 244, 106) if k < 3 else (133, 189, 255), font=F)
im.save(sys.argv[2] if len(sys.argv) > 2 else os.path.join(H, "cache", f"sheet-{sys.argv[1]}.jpg"), quality=82)
