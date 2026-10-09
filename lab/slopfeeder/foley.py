"""THE FOLEY PASS: a second sound stem under the song, so the pictures are heard where they act.
  pounds    every pound the cut locked to the beat gets a thud, taken from the pickups' own sound (onsets inside stretches CLAP hears as
            drums, footsteps in mud, artillery, explosions: the kit, built once into src/foley-kit, local) and chosen by the part of the world
  archive   an archive shot's own sound comes in when CLAP hears it as the world (surf, wind, engines, fire, crowds, machinery),
            not when it hears narration, a score or hiss
Reads the parts list cut.py writes (when, which file, from where, how long, how fast, which card); writes one stereo stem.
usage: .venv/bin/python slopfeeder/foley.py parts.json stem.wav"""
import json, os, subprocess, sys
import numpy as np, librosa, soundfile as sf, torch
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
D = os.path.dirname(os.path.abspath(__file__)); SR = 48000; KIT = os.path.join(D, "src", "foley-kit")
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
WORLD = ["ocean surf and waves", "wind howling", "machinery clanking", "an engine rumbling", "an explosion", "artillery gunfire", "fire crackling", "a crowd of people", "footsteps", "rain", "metal clanging", "a sizzling griddle"]
NOT = ["a narrator speaking", "a man talking", "orchestral film score music", "a song with singing", "tape hiss and silence"]
with torch.no_grad(): T = cm.get_text_features(**cp(text=WORLD + NOT, return_tensors="pt", padding=True)); T = (T / T.norm(dim=-1, keepdim=True)).numpy()
def clap(y):
    with torch.no_grad(): f = cm.get_audio_features(**cp(audios=[y], sampling_rate=SR, return_tensors="pt")); f = (f / f.norm(dim=-1, keepdim=True)).numpy()[0]
    p = np.exp((T @ f) * 30); p /= p.sum(); return p[:len(WORLD)].sum(), WORLD[int(np.argmax(p[:len(WORLD)]))]
def audio(src, a, L):
    r = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{max(0, a):.3f}", "-t", f"{L:.3f}", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(r, np.float32).copy()
# ---- the kit (built once)
if not os.path.isdir(KIT) or not os.listdir(KIT):
    os.makedirs(KIT, exist_ok=True); AU = json.load(open(os.path.join(D, "ai", "audio.json"))); n = 0; KEEP = {"drums", "footsteps in mud", "artillery gunfire", "an explosion"}
    for name, au in AU.items():
        src = os.path.join(D, "ai", "src", name + ".mp4"); wins = [t for t, tags in au["windows"] if KEEP & set(tags)]
        if not wins or not os.path.exists(src): continue
        y = audio(src, 0, au["dur"]); on = librosa.onset.onset_detect(y=y, sr=SR, units="time", backtrack=True)
        for t in on:
            if not any(w <= t < w + 1 for w in wins): continue
            s = y[int(t * SR): int((t + .4) * SR)]
            if len(s) < .3 * SR or np.abs(s).max() < .08: continue
            tag = next(tg for w, tags in au["windows"] if w <= t < w + 1 for tg in tags if tg in KEEP)
            s = s * np.exp(-np.linspace(0, 5, len(s))); sf.write(os.path.join(KIT, f"{tag.replace(' ', '-')}-{n:03d}.wav"), s / (np.abs(s).max() + 1e-9) * .9, SR); n += 1
    print("foley kit:", n, "thuds", flush=True)
kit = {}
for f in sorted(os.listdir(KIT)):
    if f.endswith(".wav"): kit.setdefault(f.rsplit("-", 1)[0], []).append(sf.read(os.path.join(KIT, f))[0])
BY = {"THE LANDING": ["an-explosion", "artillery-gunfire", "drums"], "THE DRILL LINE": ["drums", "footsteps-in-mud"], "THE TIDE": ["footsteps-in-mud"], "THE KITCHEN": ["drums"]}
# ---- the stem
P = json.load(open(sys.argv[1])); BEATS = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3].endswith(".json") else next((x["beats"] for x in json.load(open(os.path.join(D, "songs.json")))["songs"] if len(sys.argv) > 3 and x["n"] == sys.argv[3]), []); A = {c["id"]: c for c in json.load(open(os.path.join(D, "atlas.json")))["cards"]}
end = max(p["t"] + p["L"] for p in P); stem = np.zeros(int((end + 1) * SR), np.float32); rng = np.random.default_rng(5); n_thud = n_arch = 0
def put(t, s, gain):
    i = int(t * SR); j = min(len(stem), i + len(s)); stem[i:j] += s[:j - i] * gain
for p in P:
    c = A.get(p["id"], {})
    if c.get("type") == "ai" and p.get("locked") and c.get("pound") and kit:
        names = [k for k in BY.get(p["world"], ["drums"]) if k in kit] or list(kit)
        for h in c["pound"]:
            tt = p["t"] + (h - p["a"]) / p["rate"]
            if BEATS:   # a thud belongs on the song's beat or nowhere: off-beat thuds were killing the groove
                b_ = min(BEATS, key=lambda b: abs(b - tt))
                if abs(b_ - tt) > .09: continue
                tt = b_
            if p["t"] <= tt < p["t"] + p["L"]: s = kit[names[rng.integers(len(names))]]; put(tt, s[rng.integers(len(s))], .55); n_thud += 1
    if c.get("type") == "archive" and p.get("src") and os.path.exists(p["src"]):
        y = audio(p["src"], p["a"], p["L"])
        if len(y) > SR * .4 and np.abs(y).max() > .02:
            w, tag = clap(y[:SR * 6])
            if w > .55:
                fade = np.minimum(1, np.minimum(np.arange(len(y)), np.arange(len(y))[::-1]) / (.08 * SR)); put(p["t"], y * fade / (np.abs(y).max() + 1e-9) * .35, 1); n_arch += 1
sf.write(sys.argv[2], np.stack([stem, stem], 1), SR)
print(f"foley stem: {n_thud} thuds on locked pounds, {n_arch} archive shots heard as the world", flush=True)
