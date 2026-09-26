"""Review sheets for the clean cut: one row per section, in time order.
row = her image | her words | 0 the clean pick | 1-3 unused alternates. Writes spinecut/sheets/NN.jpg
and sheets/index.json (sheet -> rows -> section id, options)."""
import json, os
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
D = json.load(open(os.path.join(H, "spinecut-data.json"))); S = D["sections"]
used = {s["clean"] for s in S}
F = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15); FS = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
RH, TW, W = 120, 300, 160
os.makedirs(os.path.join(H, "sheets"), exist_ok=True)
def img(p, w, h):
    try: im = Image.open(p).convert("RGB")
    except Exception: return Image.new("RGB", (w, h), (40, 40, 40))
    im.thumbnail((w, h)); c = Image.new("RGB", (w, h)); c.paste(im, ((w - im.width) // 2, (h - im.height) // 2)); return c
def wrap(t, n=38):
    out, cur = [], ""
    for w in (t or "").split():
        if len(cur) + len(w) > n: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    return out + [cur]
idx = []
for k in range(0, len(S), 20):
    rows = S[k:k + 20]; sh = Image.new("RGB", (RH + TW + 4 * W + 40, RH * len(rows) + 30), (18, 18, 16)); d = ImageDraw.Draw(sh)
    d.text((6, 6), f"sheet {k // 20 + 1:02d}   her image | words | 0 = clean pick | 1-3 unused alternates", fill=(200, 190, 170), font=F)
    meta = []
    for r, s in enumerate(rows):
        y = 30 + r * RH
        sh.paste(img(os.path.join(LAB, s["hers"][0]), RH - 4, RH - 4), (4, y))
        alts = [s["clean"]] + [c for c in s["cand"] if c not in used and c != s["clean"]][:3]
        tx = RH + 8
        d.text((tx, y + 2), f"{k + r:03d}  {s['id']}  {s['t0']:.1f}s  {s['t1'] - s['t0']:.1f}s" + ("  [storyboard]" if s["board"] else ""), fill=(255, 107, 74), font=FS)
        for i, ln in enumerate(wrap(s.get("line"))[:5]): d.text((tx, y + 20 + i * 17), ln, fill=(236, 230, 218), font=F)
        for j, a in enumerate(alts):
            x = RH + TW + 10 + j * W; sh.paste(img(os.path.join(LAB, "thumbs", a + ".jpg"), W - 6, RH - 22), (x, y))
            t = D["shots"].get(a, {}).get("title", "")
            d.text((x, y + RH - 20), f"{j}  {t[:20]}", fill=(255, 255, 255) if j else (255, 107, 74), font=FS)
        meta.append({"row": k + r, "id": s["id"], "line": s.get("line"), "options": alts})
    p = os.path.join(H, "sheets", f"{k // 20 + 1:02d}.jpg"); sh.save(p, quality=80); idx.append({"sheet": p, "rows": meta})
json.dump(idx, open(os.path.join(H, "sheets", "index.json"), "w"), indent=0)
print(len(idx), "sheets")
