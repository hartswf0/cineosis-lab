"""Contact sheets for the strict judge (wes/judge/RUBRIC.md): each candidate's middle frame (the moment the renderer anchors on), fetched
from the archive, numbered in yellow, 30 to a sheet. Runs where the archive's clips can be reached (.github/workflows/monte-sheets.yml).
usage: python3 lab/monte/judge3/sheets.py -> lab/monte/judge3/sheets/sheet_NN.jpg"""
import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(D, "frames"); O = os.path.join(D, "sheets"); os.makedirs(F, exist_ok=True); os.makedirs(O, exist_ok=True)
P = json.load(open(os.path.join(D, "pool.json")))
def grab(p):
    out = os.path.join(F, p["id"] + ".jpg")
    for _ in range(3):
        if os.path.exists(out) and os.path.getsize(out) > 500: return True
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", str(p["mid"]), "-i", p["video"], "-frames:v", "1", "-vf", "scale=316:-2", out], timeout=90)
    return os.path.exists(out)
with ThreadPoolExecutor(16) as ex: ok = list(ex.map(grab, P))
print(sum(ok), "of", len(P), "frames")
try: FT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
except Exception: FT = ImageFont.load_default()
TW, TH, C, R = 320, 240, 6, 5; per = C * R
for s in range(0, len(P), per):
    im = Image.new("RGB", (C * TW, R * TH), "black"); d = ImageDraw.Draw(im)
    for j, p in enumerate(P[s:s + per]):
        x, y = (j % C) * TW, (j // C) * TH
        try: t = Image.open(os.path.join(F, p["id"] + ".jpg")).convert("RGB"); t.thumbnail((TW - 4, TH - 4)); im.paste(t, (x + 2 + (TW - 4 - t.width) // 2, y + 2 + (TH - 4 - t.height) // 2))
        except Exception: pass
        d.rectangle([x + 2, y + 2, x + 74, y + 36], fill="black"); d.text((x + 6, y + 4), str(p["n"]), fill="yellow", font=FT)
    im.save(os.path.join(O, f"sheet_{s // per + 1:02d}.jpg"), quality=80)
