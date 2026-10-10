"""NORSE HALF MOON, stage three: each book baked into one film, so a phone plays one file and nothing is ever late or missing.
The picture is composed exactly as the page composes it live: the story picture (its in-point, at 80% speed, dissolving into the next
over 1.6 s), and while the archive answers, the answering voice's own footage blended in full frame through a soft edge that travels
across (135% to 38% over 1.8 s, eased) while it rises (1.4 s) and the story dims, then travels back. The book's rendered sound track is
laid under it. 960x540, 24 fps, small enough for a phone.   usage: python3 norse/bake.py [book-id ...]   -> norse/film/<book>.mp4"""
import json, os, subprocess, sys
import numpy as np
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N); OUT = os.path.join(N, "film"); os.makedirs(OUT, exist_ok=True)
W, H, FPS = 960, 540, 24; FR = W * H * 3
P = json.load(open(os.path.join(N, "program.json")))
class Clip:
    """Frames of one clip from an in-point at a rate, cover-cropped to the frame; holds its last frame if it runs out."""
    def __init__(s, url, t0, rate=1.0):
        vf = f"setpts=PTS/{rate},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=rgb24"
        s.p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{max(0, t0):.3f}", "-i", url, "-an", "-vf", vf, "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=FR * 4)
        s.last = np.zeros((H, W, 3), np.uint8)
    def next(s):
        b = s.p.stdout.read(FR) if s.p else b""
        if len(b) == FR: s.last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        elif s.p: s.close()
        return s.last
    def close(s):
        if s.p: s.p.kill(); s.p.wait(); s.p = None
ease = lambda x: (lambda c: c * c * (3 - 2 * c))(min(1, max(0, x)))
XS = (np.arange(W) / W * 100)[None, :, None]; XS = XS + (np.arange(H) / H * 100)[:, None, None] * np.tan(np.radians(10))   # the edge leans 10 degrees, as the page's 100deg gradient
def bake(sc):
    dur = sc["dur"]; n = int(dur * FPS) + 1; pics, bes = sc["pics"], sc["beside"]
    out = os.path.join(OUT, sc["id"] + ".mp4"); aud = os.path.join(L, sc["audio"])
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", aud,
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "27", "-maxrate", "1100k", "-bufsize", "2200k", "-pix_fmt", "yuv420p",
                            "-g", "48", "-c:a", "aac", "-b:a", "96k", "-ac", "1", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    open_s = {}; open_b = {}
    for f in range(n):
        t = f / FPS
        k = max([i for i, p in enumerate(pics) if p["sw"] <= t] or [0])
        for i in list(open_s):
            if i < k - 1 or (i == k - 1 and t - pics[k]["sw"] > pics[k].get("dd", 1600) / 1000 + .1): open_s.pop(i).close()
        if k not in open_s: open_s[k] = Clip(pics[k]["video"], pics[k]["in"] + max(0, t - pics[k]["sw"]) * pics[k].get("rate", 1), pics[k].get("rate", 1))
        fr = open_s[k].next().astype(np.float32)
        dd = pics[k].get("dd", 1600) / 1000
        if k - 1 in open_s and t - pics[k]["sw"] < dd:   # the story dissolves into its next picture
            a = ease((t - pics[k]["sw"]) / dd); fr = open_s[k - 1].next().astype(np.float32) * (1 - a) + fr * a
        # the answer: rising and travelling in at its start, travelling back out at its end
        for j, b in enumerate(bes):
            if b["sw"] - .05 <= t < b["end"] + 1.9:
                if j not in open_b: open_b[j] = Clip(b["video"], b["in"] + max(0, t - b["sw"]), 1.0)
                g_in = t - b["sw"]; g_out = t - b["end"]
                if g_out < 0: edge = 135 - 97 * ease(g_in / 1.8); mix = ease(g_in / 1.4)
                else: edge = 38 + 97 * ease(g_out / 1.8); mix = 1 - ease(g_out / 1.4)
                fb = open_b[j].next().astype(np.float32)
                m = np.clip((XS - (edge - 46)) / 46, 0, 1) * mix
                fr = fr * (1 - .22 * mix)                   # the story dims under the answer
                fr = fr * (1 - m) + fb * m
            elif j in open_b: open_b.pop(j).close()
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    for c in list(open_s.values()) + list(open_b.values()): c.close()
    enc.stdin.close(); enc.wait(); return out
want = sys.argv[1:] or [s["id"] for s in P["scenes"]]
for sc in P["scenes"]:
    if sc["id"] in want: o = bake(sc); print(sc["id"], round(os.path.getsize(o) / 1e6, 1), "MB", flush=True)
