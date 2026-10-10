"""The sound, drawn: each scene's rendered track as a loudness envelope (10 per second, 0-35 as one base-36 character each), so the page
can show the voices as they sound, who is speaking and the rests between, without analysing audio on the phone.
usage: python3 envelope.py program.json [program.json ...]   (adds "env" to every scene; audio paths are relative to lab/)"""
import json, os, subprocess, sys, concurrent.futures as cf
import numpy as np
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = "0123456789abcdefghijklmnopqrstuvwxyz"
def env(path):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", os.path.join(L, path), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32); n = len(a) // 800; r = np.sqrt((a[: n * 800].reshape(n, 800) ** 2).mean(1)) if n else np.zeros(1)
    db = 20 * np.log10(r + 1e-6); top = np.percentile(db, 99) if n else 0; v = np.clip((db - (top - 42)) / 42, 0, 1)   # 42 dB of range under the loudest
    return "".join(D[int(round(x * 35))] for x in v)
for p in sys.argv[1:]:
    P = json.load(open(p))
    with cf.ThreadPoolExecutor(8) as ex: E = list(ex.map(lambda s: env(s["audio"]), P["scenes"]))
    for s, e in zip(P["scenes"], E): s["env"] = e
    json.dump(P, open(p, "w"), separators=(",", ":"), ensure_ascii=False); print(p, sum(len(e) for e in E), "samples")
