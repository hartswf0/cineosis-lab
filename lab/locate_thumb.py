"""Find where in each downloaded clip its archive thumbnail was taken (the frame the readings were made from).

Samples every clip at 8 fps (small greyscale), compares with the thumbnail, keeps the best time.
Writes cache/read_t.json: id -> {"t": seconds into clip, "err": mean abs diff 0-255}.
"""
import json, os, subprocess
import cv2, numpy as np

LAB = os.path.dirname(os.path.abspath(__file__))
SW, SH, FPS = 64, 48, 8

def main():
    out = {}
    for f in sorted(os.listdir(os.path.join(LAB, "clips"))):
        i = f[:-4]
        th = cv2.imread(os.path.join(LAB, "thumbs", i + ".jpg"), cv2.IMREAD_GRAYSCALE)
        if th is None:
            continue
        th = cv2.resize(th, (SW, SH), interpolation=cv2.INTER_AREA).astype(np.float32)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(LAB, "clips", f), "-vf",
                              f"fps={FPS},scale={SW}:{SH},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
        n = len(raw) // (SW * SH)
        if n == 0:
            continue
        fr = np.frombuffer(raw[: n * SW * SH], np.uint8).reshape(n, SH, SW).astype(np.float32)
        err = np.abs(fr - th).mean(axis=(1, 2))
        k = int(err.argmin())
        out[i] = {"t": round(k / FPS, 3), "err": round(float(err[k]), 1)}
    json.dump(out, open(os.path.join(LAB, "cache", "read_t.json"), "w"))
    errs = np.array([v["err"] for v in out.values()])
    print(len(out), "located; median err", float(np.median(errs)), "; err>25:", int((errs > 25).sum()))

if __name__ == "__main__":
    main()
