"""What the AI pickups sound like and say: every clip's soundtrack heard second by second by CLAP (explosion, sizzle, surf, chant,
speech, music, wind, machinery...), its loud hits found (onsets), and its words transcribed (whisper, run separately in the mlx venv:
ai/words.json). The griddle's SOUND lane reads ai/audio.json: what each clip can lend a song (a hit on a downbeat, a sizzle under a
kitchen, a line said between verses).   usage: .venv/bin/python slopfeeder/ai_audio.py   (after ~/.cache/mlxw-venv/bin/python slopfeeder/ai_audio.py --words)"""
import json, os, sys, subprocess
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(D, "ai"); SRC = os.path.join(A, "src"); WAV = os.path.join(A, "wav"); os.makedirs(WAV, exist_ok=True)
names = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".mp4"))
for n in names:
    w = os.path.join(WAV, n + ".wav")
    if not os.path.exists(w): subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", os.path.join(SRC, n + ".mp4"), "-ac", "1", "-ar", "48000", w])
if "--words" in sys.argv:   # the mlx venv: whisper base.en with word times
    import mlx_whisper, soundfile as sf
    from scipy.signal import resample_poly
    out = {}
    for n in names:
        a, sr = sf.read(os.path.join(WAV, n + ".wav")); a = resample_poly(a, 1, 3).astype(np.float32)
        r = mlx_whisper.transcribe(a, path_or_hf_repo="mlx-community/whisper-base.en-mlx", word_timestamps=True, condition_on_previous_text=False, no_speech_threshold=.5)
        segs = [{"t0": round(s["start"], 2), "t1": round(s["end"], 2), "text": s["text"].strip(), "nsp": round(s.get("no_speech_prob", 0), 2)} for s in r["segments"] if s["text"].strip()]
        out[n] = [s for s in segs if s["nsp"] < .6 and len(s["text"]) > 2]; print(n, "·", " / ".join(s["text"] for s in out[n])[:120], flush=True)
    json.dump(out, open(os.path.join(A, "words.json"), "w"), indent=1); sys.exit()
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import torch, librosa, soundfile as sf
from transformers import ClapModel, ClapProcessor
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
SOUNDS = ["an explosion", "artillery gunfire", "a sizzling griddle frying meat", "ocean surf and waves", "wind howling", "a crowd chanting", "a man speaking", "a woman speaking",
          "orchestral music", "a choir singing", "electronic synth music", "drums", "machinery clanking", "footsteps in mud", "fire crackling", "silence", "a laser zap", "a computer beep", "rain"]
with torch.no_grad(): ST = cm.get_text_features(**cp(text=SOUNDS, return_tensors="pt", padding=True)); ST = (ST / ST.norm(dim=-1, keepdim=True)).numpy()
words = json.load(open(os.path.join(A, "words.json"))) if os.path.exists(os.path.join(A, "words.json")) else {}
res = {}
for n in names:
    y, sr = sf.read(os.path.join(WAV, n + ".wav")); y = y.astype(np.float32); dur = len(y) / sr
    if dur < .5 or np.abs(y).max() < 1e-4: res[n] = {"dur": round(dur, 2), "silent": True}; continue
    win = []
    for a in np.arange(0, max(.01, dur - 1), 1.0):
        seg = y[int(a * sr): int((a + 2) * sr)]
        with torch.no_grad(): f = cm.get_audio_features(**cp(audios=[seg], sampling_rate=48000, return_tensors="pt"))
        p = ((f / f.norm(dim=-1, keepdim=True)).numpy()[0] @ ST.T); win.append([round(float(a), 1), [SOUNDS[j] for j in np.argsort(-p)[:2]]])
    y22 = librosa.resample(y, orig_sr=sr, target_sr=22050); on = librosa.onset.onset_detect(y=y22, sr=22050, units="time", backtrack=False)
    rms = librosa.feature.rms(y=y22)[0]; tt = librosa.frames_to_time(np.arange(len(rms)), sr=22050); thr = np.percentile(rms, 92)
    hits = sorted({round(float(t), 2) for t in on if rms[min(len(rms) - 1, int(np.searchsorted(tt, t)))] >= thr})
    tags = {}
    for _, ts in win:
        for t in ts: tags[t] = tags.get(t, 0) + 1
    res[n] = {"dur": round(dur, 2), "windows": win, "tags": sorted(tags, key=lambda t: -tags[t])[:4], "hits": hits, "loud": round(float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9)), 1),
              "words": words.get(n, [])}
    print(f"{n[:34]:34s} {', '.join(res[n]['tags'][:3])} · {len(hits)} hits · " + " / ".join(w["text"] for w in res[n]["words"])[:80], flush=True)
json.dump(res, open(os.path.join(A, "audio.json"), "w"), indent=1); print("audio.json:", len(res))
