import sys, os, json, glob, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
sys.path.insert(0, "/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab")
import sound_census as S
SP = os.path.dirname(os.path.abspath(__file__)); D = SP + "/syn"; os.makedirs(D + "/clips", exist_ok=True); os.makedirs(D + "/cache", exist_ok=True)
rng = np.random.default_rng(0); SR = S.SR
def load(p):
    return S.decode(p)
def optical(x):
    x = sosfilt(butter(4, [120, 5000], "bandpass", fs=SR, output="sos"), x)
    return x
def lvl(x, dbfs):  # set RMS of active part
    a = x[np.abs(x) > 1e-4]; r = np.sqrt(np.mean(a ** 2)) if a.size else 1
    return x * 10 ** (dbfs / 20) / r
def hiss(n, dbfs=-50): return lvl(rng.standard_normal(n), dbfs)
def pink(n):
    f = np.fft.rfftfreq(n, 1 / SR); X = np.fft.rfft(rng.standard_normal(n)); X[1:] /= np.sqrt(f[1:]); X[0] = 0
    return np.fft.irfft(X, n)
def brown(n): return np.cumsum(rng.standard_normal(n)) - np.convolve(np.cumsum(rng.standard_normal(n)), np.ones(2000) / 2000, "same")
def save(name, x):
    x = np.clip(x, -1, 1).astype(np.float32); sf.write(D + "/clips/" + name + ".mp4.wav", x, SR)
    os.replace(D + "/clips/" + name + ".mp4.wav", D + "/clips/" + name + ".mp4")
truth = {}
sp = sorted(glob.glob(D + "/src/sp*.aiff")); sing = sorted(glob.glob(D + "/src/sing*.aiff"))
corpus = json.load(open(S.LAB + "/cache/corpus.json")); recs = S.load_all()
beds = [cid for cid, r in recs.items() if r.get("raw") and (corpus.get(cid, {}).get("sourceYear") or 3000) < 1927 and (r.get("lufs") or -99) > -40]
beds = sorted(beds)[:: max(1, len(beds) // 12)][:12]
print("music beds (pre-1927 archive):", len(beds))
for i, p in enumerate(sp):
    x = lvl(optical(load(p)), -20); x = x + hiss(len(x), -52); save(f"speech{i:02d}", x); truth[f"speech{i:02d}"] = "speech"
    b = load(S.CLIPS + "/" + beds[i % len(beds)] + ".mp4")
    n = min(len(x), len(b)); m = lvl(optical(load(p))[:n], -20) + lvl(b[:n], -28 if i % 2 else -24)
    save(f"mixed{i:02d}", m); truth[f"mixed{i:02d}"] = "mixed"
for i, p in enumerate(sing):
    x = lvl(optical(load(p)), -20) + hiss(0, -52) if False else lvl(optical(load(p)), -20); save(f"sing{i}", x); truth[f"sing{i}"] = "sung(music+speech)"
n = SR * 15
t = np.arange(n) / SR
noises = {
 "hiss": hiss(n, -30),
 "pink": lvl(optical(pink(n)), -28),
 "rumble": lvl(sosfilt(butter(2, 200, fs=SR, output="sos"), brown(n)), -28),
 "crackle": lvl(optical((rng.random(n) < 0.002) * rng.standard_normal(n) * 20 + rng.standard_normal(n) * 0.05), -30),
 "wind": lvl(optical(pink(n)) * (1 + 0.8 * np.sin(2 * np.pi * 0.3 * t)) * (1 + 0.3 * np.sin(2 * np.pi * 1.7 * t)), -28),
 "hum60": lvl(sum(np.sin(2 * np.pi * 60 * k * t) / k for k in range(1, 8)), -30) + hiss(n, -45),
 "rain": lvl(optical(np.convolve((rng.random(n) < 0.02) * rng.standard_normal(n), np.exp(-np.arange(200) / 30), "same")), -28),
 "engine": lvl(optical(sosfilt(butter(2, [80, 900], "bandpass", fs=SR, output="sos"), rng.standard_normal(n)) * (1 + 0.6 * np.sin(2 * np.pi * 25 * t))), -26),
 "crowd": lvl(sum(optical(np.roll(load(sp[k]), rng.integers(0, 20000)))[:n] if len(load(sp[k])) >= n else np.pad(optical(load(sp[k])), (0, n - len(load(sp[k])))) for k in range(0, 24, 2)), -26),
}
for k, x in noises.items(): save("noise_" + k, x); truth["noise_" + k] = "noise"
for i, b in enumerate(beds[:8]):
    save(f"bed{i}", load(S.CLIPS + "/" + b + ".mp4")); truth[f"bed{i}"] = "music?(pre-1927 archive)"
json.dump(truth, open(D + "/truth.json", "w"))

# ---- extension set: noisy speech, synthetic music, music + noise
S.CLIPS = S.LAB + "/clips"
def synth_music(seed, dur=15, drums=True):
    g = np.random.default_rng(seed); n = int(dur * SR); y = np.zeros(n)
    bpm = g.uniform(70, 150); beat = 60 / bpm; root = g.integers(0, 12); scale = [0, 2, 4, 5, 7, 9, 11]
    def tone(f, t0, d, amp, h=6):
        i0 = int(t0 * SR); m = min(int(d * SR), n - i0)
        if m <= 0: return
        tt = np.arange(m) / SR; env = np.minimum(1, tt / 0.02) * np.exp(-tt / (d * 0.8))
        y[i0:i0 + m] += amp * env * sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.3 for k in range(1, h))
    t = 0.0; chords = [0, 5, 3, 4]
    while t < dur:
        for c in chords:
            base = 110 * 2 ** ((root + scale[c]) / 12)
            for iv in (0, 4, 7): tone(base * 2 ** (iv / 12), t, beat * 4, 0.15)
            for b in range(4):
                if g.random() < 0.8: tone(220 * 2 ** ((root + scale[g.integers(0, 7)] + 12 * g.integers(0, 2)) / 12), t + b * beat, beat * g.choice([0.5, 1]), 0.3)
                if drums:
                    i0 = int((t + b * beat) * SR)
                    if i0 < n - 3000:
                        k = np.arange(3000) / SR; y[i0:i0 + 3000] += (0.5 * np.sin(2 * np.pi * 60 * k) if b % 2 == 0 else 0.2 * g.standard_normal(3000)) * np.exp(-k / 0.05)
            t += beat * 4
            if t >= dur: break
    return y
nz = [k for k in noises if k not in ("crowd",)]
for i, p in enumerate(sp):
    x = lvl(optical(load(p)), -20); nk = nz[i % len(nz)]; bg = noises[nk]
    bg = np.resize(bg, len(x)); save(f"nspeech{i:02d}", x + lvl(bg, -30)); truth[f"nspeech{i:02d}"] = "speech"
for i in range(8):
    m = lvl(optical(synth_music(100 + i, drums=i % 2 == 0)), -22); save(f"synmus{i}", m + hiss(len(m), -50)); truth[f"synmus{i}"] = "music"
    x = lvl(optical(load(sp[(i * 5) % len(sp)])), -20); mm = np.resize(m, len(x))
    save(f"synmix{i}", x + lvl(mm, -27)); truth[f"synmix{i}"] = "mixed"
for i, b in enumerate(beds):
    bb = load(S.CLIPS + "/" + b + ".mp4"); save(f"bednoise{i}", bb + lvl(np.resize(noises[nz[i % len(nz)]], len(bb)), -34)); truth[f"bednoise{i}"] = "music?(pre-1927 archive)"
json.dump(truth, open(D + "/truth.json", "w"))
S.CLIPS = D + "/clips"; S.CACHE = D + "/cache"
for f in sorted(os.listdir(S.CLIPS)):
    if not os.path.exists(S.CACHE + "/" + f[:-4] + ".json"): S.measure_one(f[:-4])
print("ext done", len(truth))

# ---- degraded (archive-like) speech: room reverb, 4 kHz optical roll-off, hiss at ~15 dB SNR, hum, flutter
S.CLIPS = S.LAB + "/clips"
def degrade(x, seed):
    g = np.random.default_rng(seed)
    ir = g.standard_normal(int(0.5 * SR)) * np.exp(-np.arange(int(0.5 * SR)) / (SR * g.uniform(0.05, 0.15))); ir[0] = 8
    y = np.convolve(x, ir)[: len(x)]
    y = sosfilt(butter(3, [150, g.uniform(3000, 4500)], "bandpass", fs=SR, output="sos"), y)
    y = np.tanh(3 * y / (np.abs(y).max() + 1e-9)) 
    y = lvl(y, -22); t = np.arange(len(y)) / SR
    return y + hiss(len(y), -22 - g.uniform(12, 20)) + lvl(np.sin(2 * np.pi * 60 * t), -50)
for i, p in enumerate(sp):
    x = degrade(load(p), 500 + i); save(f"dspeech{i:02d}", x); truth[f"dspeech{i:02d}"] = "speech"
    b = load(S.CLIPS + "/" + beds[(i + 3) % len(beds)] + ".mp4") if i % 2 else synth_music(300 + i, dur=len(x) / SR + 1, drums=i % 4 == 1)
    b = np.resize(b, len(x)); save(f"dmix{i:02d}", x + lvl(optical(b), -22 - 5 - (i % 3) * 3)); truth[f"dmix{i:02d}"] = "mixed"
json.dump(truth, open(D + "/truth.json", "w"))
S.CLIPS = D + "/clips"; S.CACHE = D + "/cache"
for f in sorted(os.listdir(S.CLIPS)):
    if not os.path.exists(S.CACHE + "/" + f[:-4] + ".json"): S.measure_one(f[:-4])
print("deg done", len(truth))
