"""CUTBASTARD · watch: look at the actual footage of shortlisted clips.

For each clip (downloaded to lab/clips/ first): sample 4 fps grey frames and three colour frames, then record
  dur        real duration
  motion     mean absolute frame difference (0..1) — how much the picture moves
  pan        mean global shift per second (phase correlation) — camera travel vs. a locked frame
  dead       fraction of frames that are black, blank or flat (to reject leaders, fades, empty frames)
  card       CLIP p(title card / printed text / slate) over the 3 frames — cards are refused unless a cut wants text
  emb        mean CLIP embedding of the 3 frames (a better semantic fingerprint than one thumbnail)
  motion_t   per-second motion, so a patch can take the liveliest window of the right length
Writes cache/watch/<id>.json.       usage: python watch.py ids.txt   (one clip id per line)
"""
import json, os, subprocess, sys
import cv2, numpy as np, torch, open_clip
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
OUT = os.path.join(LAB, "cache", "watch")
CARD = ["a title card with printed words", "white text on a black screen", "a film leader countdown", "a test pattern or color bars"]
REAL = ["a photograph of a real scene", "people in a place", "a landscape", "an object in a room"]

def frames(path, fps=4, w=96, h=72):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32) / 255

def still(path, t):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    return cv2.imdecode(np.frombuffer(r, np.uint8), cv2.IMREAD_COLOR) if r else None

def main():
    ids = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    sh = os.environ.get("WATCH_SHARD")                  # "k/n": this process takes every n-th clip from k
    if sh:
        k_, n_ = map(int, sh.split("/")); ids = ids[k_::n_]
    os.makedirs(OUT, exist_ok=True)
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model = model.to(dev).eval(); tok = open_clip.get_tokenizer("ViT-B-32")
    with torch.no_grad():
        T = model.encode_text(tok(CARD + REAL).to(dev)); T = T / T.norm(dim=-1, keepdim=True)
    done = 0
    for k, i in enumerate(ids):
        o = os.path.join(OUT, i + ".json"); p = os.path.join(LAB, "clips", i + ".mp4")
        if os.path.exists(o) or not os.path.exists(p): continue
        fr = frames(p)
        if len(fr) < 3: json.dump({"id": i, "dur": len(fr) / 4, "bad": True}, open(o, "w")); continue
        dur = len(fr) / 4
        diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
        dead = float(np.mean([(f.mean() < .06) or (f.std() < .035) for f in fr]))
        shifts = []
        for a, b in zip(fr[:-1:2], fr[1::2]):
            (dx, dy), _ = cv2.phaseCorrelate(a, b); shifts.append(np.hypot(dx, dy))
        per_s = [float(diff[s * 4:(s + 1) * 4].mean()) for s in range(int(np.ceil(len(diff) / 4)))]
        ims = [still(p, dur * q) for q in (.25, .5, .75)]
        ims = [Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)) for im in ims if im is not None]
        with torch.no_grad():
            E = model.encode_image(torch.stack([pre(im) for im in ims]).to(dev)); E = E / E.norm(dim=-1, keepdim=True)
            P = torch.softmax(E @ T.T * 100, dim=1).cpu().numpy()
        e = E.mean(0); e = (e / e.norm()).cpu().numpy()
        json.dump({"id": i, "dur": round(dur, 2), "motion": round(float(diff.mean()), 4), "pan": round(float(np.mean(shifts)) * 2, 3),
                   "dead": round(dead, 3), "card": round(float(P[:, :len(CARD)].sum(1).mean()), 3),
                   "motion_t": [round(x, 4) for x in per_s], "emb": [round(float(x), 5) for x in e]}, open(o, "w"))
        done += 1
        if done % 50 == 0: print(f"watched {done} ({k + 1}/{len(ids)})", flush=True)
    print("DONE watched", done, flush=True)

if __name__ == "__main__":
    main()
