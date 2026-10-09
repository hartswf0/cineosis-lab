"""The cartoon look applied to a rendered part, frame by frame, exactly as look.py evolved it (its genome + the cartoon colour table):
edge-preserving smoothing, median, every colour snapped to the palette learned from our cartoons (the characters' and pails' colours caught).
usage: .venv/bin/python slopfeeder/lookfx.py in.mp4 out.mp4"""
import json, os, subprocess, sys
import numpy as np, cv2
D = os.path.dirname(os.path.abspath(__file__)); LK = json.load(open(os.path.join(D, "looks.json"))); g = LK["genome"]; G = LK["grid"]
rows = [list(map(float, l.split())) for l in open(os.path.join(D, "looks", "cartoon.cube")) if l[:1].isdigit() or l[:1] == "-" or (l[:1] == "0")]
rows = [r for r in rows if len(r) == 3]; L = np.array(rows, np.float32).reshape(G, G, G, 3)   # .cube: red fastest -> index [b, g, r]
LUT = (L.transpose(2, 1, 0, 3) * 255).astype(np.uint8)                                          # -> [r, g, b]
def stylise(bgr):
    x = bgr
    for _ in range(g["passes"]): x = cv2.bilateralFilter(x, 9, g["r"] * 255, g["s"] * 2)          # *2: these frames are twice the width the look was evolved on
    if g["med"]: x = cv2.medianBlur(x, 2 * g["med"] * 2 + 1)
    idx = np.rint(cv2.cvtColor(x, cv2.COLOR_BGR2RGB).astype(np.float32) * (G - 1) / 255).astype(np.intp)
    x = cv2.cvtColor(LUT[idx[..., 0], idx[..., 1], idx[..., 2]], cv2.COLOR_RGB2BGR)
    return cv2.medianBlur(x, 5) if g["post"] else x
src, out = sys.argv[1], sys.argv[2]; cap = cv2.VideoCapture(src); w, h = int(cap.get(3)), int(cap.get(4)); fps = cap.get(5) or 24
p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps}", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
while True:
    ok, f = cap.read()
    if not ok: break
    p.stdin.write(stylise(f).tobytes())
p.stdin.close(); p.wait()
