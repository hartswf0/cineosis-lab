"""PILOT · voices: every narrator and character line of the cut, in the cast's Kokoro voices (machines through the metal filter).
Writes pilot/<ep>/v<n>.wav and adds "wav", "d", "e" to each spoken beat in pilot/<ep>.voiced.json.   usage: republic/.tts/bin/python republic/pilot/tts.py ep01"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from kokoro import KPipeline
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"; cut = json.load(open(os.path.join(H, EP + ".json"))); W = json.load(open(os.path.join(R, "world.json")))
out = os.path.join(H, EP); os.makedirs(out, exist_ok=True)
P = {"a": KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M"), "b": KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M")}
D36 = "0123456789abcdefghijklmnopqrstuvwxyz"
def clean(t):
    t = re.sub(r"\b((?:[A-Z]\.){2,}[A-Z]?\.?)(-[A-Z0-9]+)?", lambda m: m.group(1).replace(".", "").capitalize() + (m.group(2) or ""), t)
    return t.replace("—", ", ").replace("…", "...").replace("“", "").replace("”", "")
for n, b in enumerate(cut["beats"]):
    if b["k"] not in ("narr", "talk"): continue
    c = W["cast"].get(b.get("who"), {}) if b["k"] == "talk" else {}
    voice, speed, robot = (c.get("voice"), c.get("speed", 1), c.get("robot", 0)) if c else (W["narrator"]["voice"], .97, 0)
    a = np.concatenate([np.asarray(x, np.float32) for _, _, x in P[voice[0]](clean(b["text"]), voice=voice, speed=speed)])
    raw = tempfile.mktemp(suffix=".wav"); sf.write(raw, a, 24000); f = os.path.join(out, f"v{n:02d}.wav")
    af = "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=7"
    if robot: af = f"flanger=delay=1:depth={2 + 6 * robot:.1f}:regen={int(20 + 50 * robot)}:width=70:speed=0.6,aecho=0.8:{0.25 + 0.5 * robot:.2f}:{int(9 + 10 * robot)}:{0.25 + 0.4 * robot:.2f}," + af
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", "-ac", "1", f], check=True); os.unlink(raw)
    y, sr = sf.read(f, dtype="float32"); b["wav"] = os.path.relpath(f, R); b["d"] = round(len(y) / sr, 3)
    k = max(1, len(y) // 40); r = np.sqrt((y[: k * 40].reshape(40, k) ** 2).mean(1)); db = 20 * np.log10(r + 1e-6); top = np.percentile(db, 95)
    b["e"] = "".join(D36[int(round(x * 35))] for x in np.clip((db - (top - 30)) / 30, 0, 1))
    print(f"{n:02d} {b['k']:5} {b.get('who', 'NARRATOR')[:12]:12} {b['d']:5.1f}s  {b['text'][:60]}", flush=True)
json.dump(cut, open(os.path.join(H, EP + ".voiced.json"), "w"), ensure_ascii=False, indent=1)
