"""MARKOV SAM · REPUBLIC: the voices. Every line of the screenplay is spoken by Kokoro-82M (an open, local text-to-speech model;
Apache-2.0), one voice per character, the same voice wherever the character returns; machines are passed through a light metal
filter (flanger + short echo, by how much of a machine they are). The narrator reads each episode's title and logline, the place,
and what we see. No voice imitates a real person.
Writes republic/voice/<episode>/<n>.m4a and republic/voices.json (for each beat: its file, seconds, and a 40-step loudness shape).
usage: republic/.tts/bin/python republic/voices.py [episode id ...]"""
import json, os, re, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from kokoro import KPipeline
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, "voice")
S = json.load(open(os.path.join(H, "script.json"))); W = json.load(open(os.path.join(H, "world.json")))
ONLY = set(sys.argv[1:])
P = {"a": KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M"), "b": KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M")}
D36 = "0123456789abcdefghijklmnopqrstuvwxyz"
def who(n): return W["alias"].get(n, n)
def say_text(t):
    t = re.sub(r"\b((?:[A-Z]\.){2,}[A-Z]?\.?)(-[A-Z0-9]+)?", lambda m: m.group(1).replace(".", "").capitalize() + (m.group(2) or ""), t)   # W.A.L.T.-E → Walt-E
    t = t.replace("—", ", ").replace("–", ", ").replace("…", "... ").replace("“", "").replace("”", "").replace("*", "")
    t = re.sub(r"\(([^)]*)\)", r", \1,", t); t = re.sub(r"\s+", " ", t).strip(" ,")
    return t
def speak(text, voice, speed):
    out = [a for _, _, a in P[voice[0]](text, voice=voice, speed=speed)]
    a = np.concatenate([np.asarray(x, dtype=np.float32) for x in out]) if out else np.zeros(2400, np.float32)
    return a
def shape(a, sr=24000):
    n = 40; k = max(1, len(a) // n); r = np.sqrt((a[: k * n].reshape(n, k) ** 2).mean(1)); db = 20 * np.log10(r + 1e-6); top = np.percentile(db, 95)
    return "".join(D36[int(round(x * 35))] for x in np.clip((db - (top - 36)) / 36, 0, 1))
def write(a, path, robot=0):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: sf.write(f.name, a, 24000); tmp = f.name
    af = "highpass=f=70,loudnorm=I=-17:TP=-1.5:LRA=7"
    if robot: af = f"flanger=delay=1:depth={2 + 6 * robot:.1f}:regen={int(20 + 50 * robot)}:width=70:speed=0.6,aecho=0.8:{0.25 + 0.5 * robot:.2f}:{int(9 + 10 * robot)}:{0.25 + 0.4 * robot:.2f}," + af
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af, "-ac", "1", "-ar", "24000", "-c:a", "aac", "-b:a", "56k", path], check=True); os.unlink(tmp)
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())
V = json.load(open(os.path.join(H, "voices.json"))) if os.path.exists(os.path.join(H, "voices.json")) else {}
NV = W["narrator"]
for e in S["episodes"]:
    if ONLY and e["id"] not in ONLY: continue
    d = os.path.join(OUT, e["id"]); os.makedirs(d, exist_ok=True); rows = []
    open_line = f"{e['name'].title()}. {e['logline']}"
    items = [("open", "NARRATOR", open_line)] + [(b["k"], who(b.get("who", "NARRATOR")) if b["k"] == "line" else "NARRATOR", b["text"]) for b in e["beats"]]
    for n, (k, w, text) in enumerate(items):
        if k == "card": rows.append(None); continue          # cards are read, not spoken
        c = W["cast"].get(w) or {}; voice = c.get("voice") or NV["voice"]; speed = c.get("speed") or NV["speed"]
        if k in ("open", "act") or w == "NARRATOR": voice, speed, robot = NV["voice"], NV["speed"], 0
        else: robot = c.get("robot", 0)
        a = speak(say_text(text), voice, speed)
        f = os.path.join(d, f"{n:02d}.m4a"); dur = write(a, f, robot)
        rows.append({"f": f"republic/voice/{e['id']}/{n:02d}.m4a", "d": round(dur, 2), "e": shape(a), "v": voice})
    V[e["id"]] = rows; json.dump(V, open(os.path.join(H, "voices.json"), "w"), separators=(",", ":"))
    print(e["id"], e["name"][:30], f"{sum(r['d'] for r in rows if r):.0f}s", flush=True)
