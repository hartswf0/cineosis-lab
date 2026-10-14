"""THE MACHINES WATCH · the ears. On 300 local clips (fixed seed): loudness, CLAP's choice among sixteen sounds, and Whisper's
transcript with its silence filter off, on clips CLAP calls music or that are near silent. Looks for: silence CLAP still names,
and words Whisper writes where the sound is music or nothing. Writes explain/machines/audio.json.
usage: lab/.venv/bin/python lab/explain/machines_audio.py"""
import json, os, random, subprocess, glob
import numpy as np, torch
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
D = json.load(open(os.path.join(LAB, "lab-data.json"))); by = {s["id"]: s for s in D["shots"]}
corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
files = sorted(glob.glob(os.path.join(LAB, "clips", "*.mp4"))); random.seed(11); random.shuffle(files)
def title(i): c = corpus.get(i) or by.get(i) or {}; return c.get("sourceTitle") or c.get("title") or ""
files = [f for f in files if not any(b in title(os.path.basename(f)[:-4]).lower() for b in BLOCK)][:300]
def audio(path, sr=48000, secs=10):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-t", str(secs), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(r, np.float32)
LABELS = ["a man speaking", "a woman speaking", "orchestral music", "a crowd cheering", "applause", "rain", "a train", "a car engine", "an airplane", "birds singing",
          "ocean waves", "wind", "a dog barking", "typing on a typewriter", "a gunshot", "silence"]
from transformers import ClapModel, ClapProcessor
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
with torch.no_grad():
    T = cm.get_text_features(**cp(text=LABELS, return_tensors="pt", padding=True)); T = T / T.norm(dim=-1, keepdim=True)
from faster_whisper import WhisperModel
wm = WhisperModel("base.en", device="cpu", compute_type="int8")
out = []
for k, f in enumerate(files):
    i = os.path.basename(f)[:-4]; a = audio(f)
    if len(a) < 48000: continue
    rms = float(20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9))
    with torch.no_grad():
        A = cm.get_audio_features(**cp(audios=a, sampling_rate=48000, return_tensors="pt")); A = A / A.norm(dim=-1, keepdim=True)
        p = torch.softmax(A @ T.T * 100, dim=1)[0].numpy()
    top = [[LABELS[j], round(float(p[j]), 3)] for j in np.argsort(-p)[:4]]
    rec = {"id": i, "title": title(i), "clip": f"clips/{i}.mp4", "thumb": f"thumbs/{i}.jpg", "rms": round(rms, 1), "clap": top}
    if top[0][0] in ("orchestral music", "silence", "wind", "rain", "ocean waves") or rms < -45:
        a16 = audio(f, 16000)
        segs, _ = wm.transcribe(a16, vad_filter=False, condition_on_previous_text=False, beam_size=1)
        rec["whisper"] = " ".join(s.text.strip() for s in segs).strip()
    out.append(rec)
    if k % 25 == 0: print(k, rec["title"][:30], rms, top[0], rec.get("whisper", "")[:60], flush=True)
json.dump(out, open(os.path.join(H, "machines", "audio.json"), "w"), ensure_ascii=False, indent=0)
sil = [r for r in out if r["rms"] < -50]; print("near silent", len(sil), [(r["title"][:24], r["clap"][0]) for r in sil[:10]])
wh = [r for r in out if r.get("whisper")]; print("whisper wrote words on music/quiet clips:", len(wh)); [print("  ", r["rms"], r["clap"][0], "|", r["whisper"][:90], "|", r["title"][:30]) for r in wh[:25]]
