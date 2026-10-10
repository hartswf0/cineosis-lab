"""NORSE HALF MOON, stage three: the whole piece baked into one film, so a phone streams one file and nothing is ever late or missing.
Made to be watched, by anticipation rather than fades:
  cut ahead     each story picture cuts in (a quarter-second dissolve) in the pause before its line, so the eye arrives before the voice
  never still   every story picture pushes in slowly through its hold (4% a second at most, from the centre), at 80% speed
  the answer    the answering voice's own footage sweeps in full frame through a soft edge that travels fast and settles (0.7 s,
                ease-out) beginning just before the archive speaks, a thin gold light riding the edge while it moves; it sweeps back
                out as the answer ends. Nothing dims, nothing fades to black.
Each book is baked, then all are joined into norse/film/norse-half-moon.mp4 (854x480, 24 fps), and every scene in program.json gets its
offset in that film (t0).   usage: python3 norse/bake.py"""
import json, os, subprocess, sys
import numpy as np
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N); OUT = os.path.join(N, "film"); os.makedirs(OUT, exist_ok=True)
W, H, FPS = 854, 480, 24; FR = W * H * 3
P = json.load(open(os.path.join(N, "program.json")))
class Clip:
    """Frames of one clip from an in-point at a rate, cover-cropped, pushing in slowly if asked; holds its last frame if it runs out."""
    def __init__(s, url, t0, rate=1.0, push=0.0):
        z = f",scale=w='trunc(iw*(1+{push}*min(t\\,6))/2)*2':h=-2:eval=frame,crop={W}:{H}" if push else ""
        vf = f"setpts=PTS/{rate},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}{z},setsar=1,fps={FPS},format=rgb24"
        s.p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{max(0, t0):.3f}", "-i", url, "-an", "-vf", vf, "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=FR * 4)
        s.last = np.zeros((H, W, 3), np.uint8)
    def next(s):
        b = s.p.stdout.read(FR) if s.p else b""
        if len(b) == FR: s.last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        elif s.p: s.close()
        return s.last
    def close(s):
        if s.p: s.p.kill(); s.p.wait(); s.p = None
clamp = lambda x: min(1.0, max(0.0, x)); out3 = lambda x: 1 - (1 - clamp(x)) ** 3          # ease-out: fast, then settles
XS = (np.arange(W) / W * 100)[None, :, None] + (np.arange(H) / H * 100)[:, None, None] * np.tan(np.radians(10))   # the edge leans 10 degrees
GOLD = np.array([232, 192, 112], np.float32)
def bake(sc):
    dur = sc["dur"]; n = int(dur * FPS) + 1; pics, bes = sc["pics"], sc["beside"]
    out = os.path.join(OUT, sc["id"] + ".mp4"); aud = os.path.join(L, sc["audio"])
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", aud,
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "29", "-maxrate", "750k", "-bufsize", "1500k", "-pix_fmt", "yuv420p",
                            "-g", "48", "-c:a", "aac", "-b:a", "80k", "-ar", "44100", "-ac", "1", "-t", f"{dur:.3f}", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    open_s, open_b = {}, {}
    for f in range(n):
        t = f / FPS
        k = max([i for i, p in enumerate(pics) if p["sw"] - .15 <= t] or [0])
        for i in list(open_s):
            if i < k - 1 or (i == k - 1 and t - (pics[k]["sw"] - .15) > .3): open_s.pop(i).close()
        if k not in open_s: open_s[k] = Clip(pics[k]["video"], pics[k]["in"], pics[k].get("rate", 1), .04)
        fr = open_s[k].next().astype(np.float32)
        a = (t - (pics[k]["sw"] - .15)) / .25
        if k - 1 in open_s and a < 1: fr = open_s[k - 1].next().astype(np.float32) * (1 - clamp(a)) + fr * clamp(a)
        for j, b in enumerate(bes):
            st, en = b["sw"] - .15, b["end"] - .2
            if st <= t < en + .7:
                if j not in open_b: open_b[j] = Clip(b["video"], b["in"] + max(0, t - b["sw"]), 1.0)
                if t < en: g = out3((t - st) / .7); mix = clamp((t - st) / .3); moving = g < .98
                else: g = 1 - out3((t - en) / .6); mix = 1.0; moving = True
                edge = 135 - 105 * g
                m = np.clip((XS - (edge - 40)) / 40, 0, 1) * mix
                fb = open_b[j].next().astype(np.float32); fr = fr * (1 - m) + fb * m
                if moving:   # a thin gold light rides the travelling edge
                    glow = np.exp(-((XS - (edge - 20)) / 2.2) ** 2) * .55 * mix * (1 - g * .6)
                    fr = fr * (1 - glow) + GOLD * glow
            elif j in open_b: open_b.pop(j).close()
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    for c in list(open_s.values()) + list(open_b.values()): c.close()
    enc.stdin.close(); enc.wait(); return out
parts = []
for sc in P["scenes"]:
    o = bake(sc); parts.append(o); print(sc["id"], round(os.path.getsize(o) / 1e6, 1), "MB", flush=True)
# one film: the books joined end to end; each scene learns where it begins
lst = os.path.join(OUT, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts)); film = os.path.join(OUT, "norse-half-moon.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", film], check=True)
acc = 0.0
for sc, p in zip(P["scenes"], parts):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
    sc["t0"] = round(acc, 3); sc["fdur"] = round(d, 3); sc.pop("film", None); acc += d
P["film"] = "norse/film/norse-half-moon.mp4"; json.dump(P, open(os.path.join(N, "program.json"), "w"), separators=(",", ":"), ensure_ascii=False)
for p in parts: os.remove(p)
os.remove(lst); print("film", round(os.path.getsize(film) / 1e6, 1), "MB ·", round(acc / 60, 1), "min")
