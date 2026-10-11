"""SCORE · HEAR: the lab listens to its music the way it reads its pictures, so films can be scored by meaning.
For every cue of the albums below:
  windows  CLAP (laion/clap-htsat-unfused) over 10 s windows every 5 s: what each stretch sounds like, in the same space as text,
           so a scene's own words can find the music that sounds like them
  tags     the three nearest of a fixed vocabulary of moods and sounds, per window (a label to read, not the match itself)
  shape    loudness every half second, the tempo and the beat times (librosa), so cuts can land on the music
  file     a web copy (AAC 64k stereo) for the pages
Albums: D-A-E · Honed for Film (the 24 cues on the VOLHOLLA album page), The Republic Spilled Its Drink (12 songs).
Writes score/library.json and score/clap.npy.   usage: .venv/bin/python score/hear.py"""
import json, os, re, subprocess
import numpy as np, librosa, torch
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
H = os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(H, "cues"), exist_ok=True)
MOTO = os.path.expanduser("~/MOTO")
def dae_files():
    s = open(os.path.join(MOTO, "VOLHOLLA", "album-page.js")).read(); i = s.find("daehoned: {"); j = s.find("files: [", i); k = s.find("]", j)
    return [os.path.join(MOTO, "DAE STILL OPEN", f) for f in re.findall(r'"([^"]+\.ogg)"', s[j:k])]
ALBUMS = [("dae", "D-A-E · Honed for Film", dae_files()),
          ("republic", "The Republic Spilled Its Drink", sorted(os.path.join(MOTO, "THE REPUBLIC SPILLED ITS DRINK", f) for f in os.listdir(os.path.join(MOTO, "THE REPUBLIC SPILLED ITS DRINK")) if f.endswith(".ogg")))]
VOCAB = ["wonder and awe", "quiet calm", "tension and suspense", "dread", "sorrow", "triumph", "playful and comic", "driving rhythm", "dreamy ambient",
         "melancholy guitar", "surf guitar", "dub reggae", "funk groove", "folk acoustic", "glitchy electronic", "cinematic strings", "marching drums",
         "lonely desert", "ocean and waves", "a warm return home", "something breaking apart", "a journey in motion", "ritual and ceremony", "country western"]
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
with torch.no_grad(): TV = cm.get_text_features(**cp(text=[f"{v} music" for v in VOCAB], return_tensors="pt", padding=True)); TV = (TV / TV.norm(dim=-1, keepdim=True)).numpy()
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
lib, embs = [], []
for ak, an, files in ALBUMS:
    seen = set()
    for f in files:
        if not os.path.exists(f): print("  missing", f); continue
        title = re.sub(r" - Treblo.*$", "", os.path.basename(f).split(" - ", 1)[1]); tid = ak + "-" + slug(title)
        if tid in seen: tid += "-2"
        seen.add(tid)
        y48 = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
        y = np.frombuffer(y48, np.float32).copy(); dur = len(y) / 48000
        win, hop = 10 * 48000, 5 * 48000; starts = list(range(0, max(1, len(y) - win + 1), hop)) or [0]
        chunks = [y[s: s + win] for s in starts]
        E = []
        with torch.no_grad():
            for k in range(0, len(chunks), 8):
                e = cm.get_audio_features(**cp(audios=chunks[k:k + 8], sampling_rate=48000, return_tensors="pt")); E.append((e / e.norm(dim=-1, keepdim=True)).numpy())
        E = np.concatenate(E)
        y22 = librosa.resample(y, orig_sr=48000, target_sr=22050); tempo, beats = librosa.beat.beat_track(y=y22, sr=22050, units="time")
        rms = librosa.feature.rms(y=y22, frame_length=2048, hop_length=11025)[0]; db = 20 * np.log10(rms + 1e-6); top = np.percentile(db, 95)
        env = "".join("0123456789abcdefghijklmnopqrstuvwxyz"[int(round(x * 35))] for x in np.clip((db - (top - 30)) / 30, 0, 1))
        out = os.path.join(H, "cues", tid + ".m4a")
        if not os.path.exists(out): subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-ac", "2", "-c:a", "aac", "-b:a", "64k", out], check=True)
        tags = [[VOCAB[i] for i in np.argsort(-(e @ TV.T))[:3]] for e in E]
        lib.append({"id": tid, "album": an, "title": title, "f": f"score/cues/{tid}.m4a", "dur": round(dur, 2), "tempo": round(float(np.atleast_1d(tempo)[0]), 1),
                    "beats": [round(float(b), 2) for b in beats], "env": env, "w0": len(embs), "win": [round(s / 48000, 1) for s in starts], "tags": tags})
        embs.extend(E)
        print(f"  {an[:12]:12} {title[:44]:44} {dur:5.0f}s {float(np.atleast_1d(tempo)[0]):4.0f} bpm · {', '.join(sorted(set(t for w in tags for t in w), key=lambda t: -sum(t in w for w in tags))[:3])}", flush=True)
np.save(os.path.join(H, "clap.npy"), np.stack(embs).astype(np.float16))
json.dump({"albums": [a[1] for a in ALBUMS], "vocab": VOCAB, "tracks": lib}, open(os.path.join(H, "library.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(lib), "cues heard ·", len(embs), "windows")
