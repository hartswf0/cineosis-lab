"""Where each song has no words: the stretches an edit can give to the pickups' own voices, foley, or silence.
Every second, two listeners vote:
  CLAP     a 3 s window read against voice prompts (singing, choir, chant, speech, whisper) and voice-free ones (instrumental, drums, drone)
  REPET    the song split into what repeats (the band) and what doesn't (mostly the voice; librosa nn_filter), the foreground's share
           of energy in the 300-3400 Hz voice band
voice[t] = .65 CLAP + .35 REPET, smoothed, and forced high wherever Whisper heard a word (songwords.py); word-free = runs below .4 lasting 2 s or more.
Writes slopfeeder/voice.json {n: {voice: [per second], free: [[t0, t1], ...]}}.   usage: .venv/bin/python slopfeeder/voice.py"""
import json, os
import numpy as np, librosa, torch
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
D = os.path.dirname(os.path.abspath(__file__)); ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS")
VOX = ["a person singing", "a choir singing words", "chanting voices", "a man speaking", "a whispering voice", "a woman singing"]
NOV = ["instrumental music without any vocals", "drums and percussion only", "a synthesizer drone", "an orchestra playing with no singing", "ambient noise and wind"]
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
with torch.no_grad(): T = cm.get_text_features(**cp(text=VOX + NOV, return_tensors="pt", padding=True)); T = (T / T.norm(dim=-1, keepdim=True)).numpy()
S = json.load(open(os.path.join(D, "songs.json")))["songs"]; out = {}
WORDS = json.load(open(os.path.join(D, "songwords.json"))) if os.path.exists(os.path.join(D, "songwords.json")) else {}
for s in S:
    y, sr = librosa.load(os.path.join(ALB, s["file"]), sr=22050, mono=True); dur = len(y) / sr; n = int(dur)
    # REPET-SIM: the non-repeating foreground, its share of voice-band energy per second
    Sx, ph = librosa.magphase(librosa.stft(y, n_fft=2048, hop_length=512))
    Sn = Sx / (np.linalg.norm(Sx, axis=0, keepdims=True) + 1e-9); Sim = Sn.T @ Sn; w = int(librosa.time_to_frames(2, sr=sr))   # nn_filter by hand (scipy here breaks librosa's)
    for i in range(Sim.shape[0]): Sim[i, max(0, i - w): i + w] = -1
    nb = np.argpartition(-Sim, 10, axis=1)[:, :10]; del Sim
    Sf = np.minimum(Sx, np.median(Sx[:, nb], axis=2))
    fg = np.maximum(Sx - Sf, 0); fr = librosa.fft_frequencies(sr=sr, n_fft=2048); band = (fr > 300) & (fr < 3400)
    ratio = fg[band].sum(0) / (Sx[band].sum(0) + 1e-6); fps = sr / 512
    rep = np.array([ratio[int(t * fps): int((t + 1) * fps)].mean() for t in range(n)]); rep = (rep - np.quantile(rep, .1)) / (np.quantile(rep, .9) - np.quantile(rep, .1) + 1e-9)
    # CLAP, a 3 s window every second
    y48 = librosa.resample(y, orig_sr=sr, target_sr=48000); cl = []
    segs = [y48[int(max(0, t - 1) * 48000): int((t + 2) * 48000)] for t in range(n)]
    for k in range(0, n, 16):
        with torch.no_grad(): f = cm.get_audio_features(**cp(audios=segs[k:k + 16], sampling_rate=48000, return_tensors="pt", padding=True))
        f = (f / f.norm(dim=-1, keepdim=True)).numpy(); p = np.exp((f @ T.T) * 30); p /= p.sum(1, keepdims=True); cl += list(p[:, :len(VOX)].sum(1))
    v = .65 * np.array(cl) + .35 * np.clip(rep, 0, 1); v = np.convolve(v, np.ones(3) / 3, "same")
    for a_, b_, _w in WORDS.get(s["n"], []): v[max(0, int(a_ - .3)): min(n, int(b_ + .3) + 1)] = np.maximum(v[max(0, int(a_ - .3)): min(n, int(b_ + .3) + 1)], .9)   # Whisper heard a word: not free
    free, a = [], None
    for t, x in enumerate(list(v) + [1]):
        if x < .4 and a is None: a = t
        elif x >= .4 and a is not None:
            if t - a >= 2: free.append([a, t])
            a = None
    out[s["n"]] = {"voice": [round(float(x), 3) for x in v], "free": free}
    print(s["n"], s["title"], f"{dur:.0f}s · word-free {sum(b - a for a, b in free)} s in {len(free)} stretches:", free[:8], flush=True)
json.dump(out, open(os.path.join(D, "voice.json"), "w"))
