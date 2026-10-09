"""MOTION THUMBNAILS: every card as 12 frames (128x72) across its shot, packed 16 cards to a sheet, so the blacktop can play hundreds of
shots at once on one canvas (a flipbook per card) and load in a few requests instead of a video per shot.
AI shots from their sources (in..out), archive shots from the cached clip or straight from the archive's CDN, drawings from their mp4.
Writes sprites/s000.jpg... and sprites.json {id: [sheet, row]}.   usage: python3 slopfeeder/sprites.py"""
import json, os, subprocess, concurrent.futures as cf
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); OUT = os.path.join(D, "sprites"); TMP = os.path.join(D, "src", "strips"); os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
FW, FH, NF, PER = 128, 72, 12, 16
A = json.load(open(os.path.join(D, "atlas.json")))["cards"]
def source(c):
    if c["type"] == "ai": return os.path.join(D, c["src"]), c["in"], c["out"] - c["in"]
    if c["type"] == "drawn": return os.path.join(D, c["media"]), 0, c.get("dur") or 8
    for p in (os.path.join(D, "fclips", c["id"] + ".mp4"), os.path.join(L, "cache", "remote", c["id"] + ".mp4"), os.path.join(L, "clips", c["id"] + ".mp4")):
        if os.path.exists(p) and os.path.getsize(p) > 5000: return p, None, c.get("dur")
    return c["media"], None, c.get("dur")
def strip(c):
    out = os.path.join(TMP, c["id"] + ".jpg")
    if os.path.exists(out) and os.path.getsize(out) > 2000: return c["id"], True
    src, a, d = source(c)
    if a is None:   # archive: the middle of the clip, at most 6 s
        d = float(d or 0) or 5.0; L_ = min(6.0, d); a = max(0.0, d / 2 - L_ / 2); d = L_
    d = max(.5, float(d))
    vf = f"fps={NF / d:.4f},scale={FW}:{FH}:force_original_aspect_ratio=increase,crop={FW}:{FH},tile={NF}x1"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-user_agent", "cineosis-44-research", "-ss", f"{a:.2f}", "-t", f"{d + .3:.2f}", "-i", src, "-vf", vf, "-frames:v", "1", "-q:v", "5", out] if src.startswith("http") else
                       ["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-t", f"{d + .3:.2f}", "-i", src, "-vf", vf, "-frames:v", "1", "-q:v", "5", out], capture_output=True, timeout=120)
    return c["id"], os.path.exists(out)
ok = {}
with cf.ThreadPoolExecutor(10) as ex:
    for k, (i, good) in enumerate(ex.map(strip, A)):
        ok[i] = good
        if k % 150 == 0: print(f"  {k}/{len(A)} strips", flush=True)
idx, sheet, rows = {}, None, 0; n = 0
cards = [c for c in A if ok.get(c["id"])]
for k in range(0, len(cards), PER):
    im = Image.new("RGB", (FW * NF, FH * PER))
    for r, c in enumerate(cards[k:k + PER]):
        try: s = Image.open(os.path.join(TMP, c["id"] + ".jpg")).convert("RGB")
        except Exception: continue
        if s.width < FW * NF:   # a short clip gave fewer frames: repeat what there is
            f = [s.crop((j * FW, 0, (j + 1) * FW, FH)) for j in range(max(1, s.width // FW))]; s = Image.new("RGB", (FW * NF, FH)); [s.paste(f[j % len(f)], (j * FW, 0)) for j in range(NF)]
        im.paste(s, (0, r * FH)); idx[c["id"]] = [n, r]
    im.save(os.path.join(OUT, f"s{n:03d}.jpg"), quality=72, optimize=True); n += 1
json.dump({"fw": FW, "fh": FH, "nf": NF, "per": PER, "sheets": n, "at": idx}, open(os.path.join(D, "sprites.json"), "w"), separators=(",", ":"))
print(f"{len(idx)} of {len(A)} cards in {n} sheets", flush=True)
