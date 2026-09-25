"""SOUND CENSUS — measure the sound of every downloaded archive clip so a mixer can blend
clips that carry music without them talking over each other.

  .venv/bin/python sound_census.py            # measure (resumable, 3 workers) then merge
  .venv/bin/python sound_census.py --merge    # re-classify cached raw features + merge only
  .venv/bin/python sound_census.py --validate # print validation numbers

Two stages:
  1. measure(): per clip, decode mono 22050 Hz with ffmpeg and write cache/sound/<id>.json holding
     the *measurements* (loudness, peak, LRA, envelope, spectral bands, onsets, tempo/beats, key)
     and the *raw per-second classifier features*. Skips clips whose cache file exists.
  2. classify()+merge(): turn raw per-second features into per-second speech / music
     probabilities (non-exclusive: narration over score is common in this archive), a per-second
     kind timeline, clip-level probabilities and a kind; write cache/sound-census.json and
     cache/sound-census.md. Retuning the classifier never needs the audio again.

Signal features only; no models are loaded.
"""
import json, os, subprocess, sys, time
from multiprocessing import Pool

for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(v, "1")

import numpy as np

LAB = os.path.dirname(os.path.abspath(__file__))
CLIPS = os.path.join(LAB, "clips")
CACHE = os.path.join(LAB, "cache", "sound")
OUT = os.path.join(LAB, "cache", "sound-census.json")
REPORT = os.path.join(LAB, "cache", "sound-census.md")
SR = 22050
NFFT = 2048
HOP = 512
FPS = SR / HOP              # ~43.07 feature frames per second
WORKERS = 3
RAW_VERSION = 4

# ----------------------------------------------------------------------------------------------
# ITU-R BS.1770 K-weighting, re-derived for 22050 Hz from the analog prototypes (the same
# parameterisation pyloudnorm uses): a +4 dB high shelf near 1.68 kHz, then a 38 Hz high-pass.
# ----------------------------------------------------------------------------------------------
def k_filter_sos(fs=SR):
    G, Q, fc = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    A = 10 ** (G / 40)
    w0 = 2 * np.pi * fc / fs
    c, al = np.cos(w0), np.sin(w0) / (2 * Q)
    sA = np.sqrt(A)
    b = [A * ((A + 1) + (A - 1) * c + 2 * sA * al), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - 2 * sA * al)]
    a = [(A + 1) - (A - 1) * c + 2 * sA * al, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - 2 * sA * al]
    shelf = np.r_[np.array(b) / a[0], np.array(a) / a[0]]
    Q, fc = 0.5003270373253953, 38.13547087613982
    w0 = 2 * np.pi * fc / fs
    c, al = np.cos(w0), np.sin(w0) / (2 * Q)
    b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    a = [1 + al, -2 * c, 1 - al]
    hp = np.r_[np.array(b) / a[0], np.array(a) / a[0]]
    return np.vstack([shelf, hp])

def _block_ms(y, win, hop):
    n = len(y)
    if n < win:
        return np.array([np.mean(y ** 2)]) if n else np.array([])
    idx = np.arange(0, n - win + 1, hop)
    cs = np.r_[0.0, np.cumsum(y.astype(np.float64) ** 2)]
    return (cs[idx + win] - cs[idx]) / win

def loudness(x):
    """Integrated loudness (LUFS, mono), gated per BS.1770-4; LRA per EBU Tech 3342 (p95-p10 of
    3 s short-term loudness, abs gate -70, rel gate -20). Clips shorter than 3 s use 1 s windows."""
    from scipy.signal import sosfilt
    y = sosfilt(k_filter_sos(), x)
    z = _block_ms(y, int(0.4 * SR), int(0.1 * SR))            # 400 ms blocks, 75 % overlap
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    g = z[lk > -70]
    if g.size == 0:
        return None, None
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = z[(lk > -70) & (lk > rel)]
    I = -0.691 + 10 * np.log10(g2.mean())
    sw = 3.0 if len(x) >= 3 * SR else 1.0
    st = -0.691 + 10 * np.log10(_block_ms(y, int(sw * SR), int(0.1 * SR)) + 1e-20)
    st = st[st > -70]
    if st.size:
        st_rel = -0.691 + 10 * np.log10(np.mean(10 ** ((st + 0.691) / 10))) - 20
        st = st[st > st_rel]
    lra = float(np.percentile(st, 95) - np.percentile(st, 10)) if st.size >= 2 else 0.0
    return float(I), lra

# ----------------------------------------------------------------------------------------------
def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                        "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    dur = float(j.get("format", {}).get("duration", 0) or 0)
    return dur, any(s.get("codec_type") == "audio" for s in j.get("streams", []))

def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def db(v):
    return 20 * np.log10(np.maximum(v, 1e-6))

def r(v, n=3):
    return None if v is None or not np.isfinite(v) else round(float(v), n)

KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def ks_key(chroma_mean):
    scores = []
    for mode, prof in (("major", KS_MAJ), ("minor", KS_MIN)):
        for k in range(12):
            scores.append((np.corrcoef(chroma_mean, np.roll(prof, k))[0, 1], NOTES[k], mode))
    scores.sort(key=lambda s: -s[0])
    return scores[0], scores[1]

def norm_ac(o, lo, hi):
    """Peak of the normalised autocorrelation of an onset envelope between lags lo..hi frames."""
    o = o - o.mean()
    if len(o) < hi + 4 or not np.any(o):
        return 0.0, 0
    ac = np.correlate(o, o, "full")[len(o) - 1:]
    ac = ac / (ac[0] + 1e-12) * len(o) / (len(o) - np.arange(len(o)))    # unbiased
    seg = ac[lo:hi]
    k = int(np.argmax(seg))
    return float(np.clip(seg[k], 0, 1)), lo + k

# ----------------------------------------------------------------------------------------------
def measure_one(cid):
    import librosa
    out = os.path.join(CACHE, cid + ".json")
    path = os.path.join(CLIPS, cid + ".mp4")
    t0 = time.time()
    dur, has_a = probe(path)
    rec = {"id": cid, "raw_version": RAW_VERSION, "dur": r(dur, 3), "has_audio": bool(has_a)}
    if not has_a:
        rec["kind_hint"] = "none"
        return _write(out, rec)
    x = decode(path)
    if x.size < SR // 2:
        rec.update(has_audio=False, kind_hint="none", note="audio stream decodes to < 0.5 s")
        return _write(out, rec)
    x = np.nan_to_num(x)
    adur = len(x) / SR
    peak = float(np.max(np.abs(x)))
    rec["peak_db"] = r(db(peak), 2)
    I, lra = loudness(x)
    rec["lufs"], rec["lra"] = r(I, 2), r(lra, 2)

    # frame energy (23 ms hop) -> silence fraction, per-second envelope
    S = np.abs(librosa.stft(x, n_fft=NFFT, hop_length=HOP, center=True))
    rms = librosa.feature.rms(y=x, frame_length=NFFT, hop_length=HOP, center=True)[0]
    n = min(S.shape[1], len(rms))
    S, rms = S[:, :n], rms[:n]
    rdb = db(rms)
    rec["silence"] = r(np.mean(rdb < -50), 3)
    nsec = max(1, int(np.ceil(adur - 0.25)))
    sec_of = (np.arange(n) / FPS).astype(int).clip(0, nsec - 1)
    env = [r(db(np.sqrt(np.mean(rms[sec_of == s] ** 2))) if np.any(sec_of == s) else -100.0, 1) for s in range(nsec)]
    rec["env"] = env
    if peak < 10 ** (-60 / 20) or rec["silence"] >= 0.995:
        rec["kind_hint"] = "silence"
        rec["raw"] = None
        return _write(out, rec)

    freqs = librosa.fft_frequencies(sr=SR, n_fft=NFFT)
    P = S ** 2
    tot = P.sum(0) + 1e-12
    low, mid, high = freqs < 250, (freqs >= 250) & (freqs < 4000), freqs >= 4000
    act = rdb > -50                                                       # frames with signal
    w = act if act.any() else np.ones(n, bool)
    Psum = P[:, w].sum(1)
    Pt = Psum.sum() + 1e-12
    rec["bands"] = {"low": r(Psum[low].sum() / Pt), "mid": r(Psum[mid].sum() / Pt), "high": r(Psum[high].sum() / Pt)}
    cent = librosa.feature.spectral_centroid(S=S, sr=SR)[0]
    roll = librosa.feature.spectral_rolloff(S=S, sr=SR, roll_percent=0.85)[0]
    rec["centroid"], rec["rolloff"] = r(np.mean(cent[w]), 0), r(np.mean(roll[w]), 0)

    # classifier frame features
    # flatness inside 60-5000 Hz only: archive optical tracks are band-limited, and the empty band
    # above the cutoff drives full-band flatness to ~0 for everything
    fb = (freqs >= 60) & (freqs <= 5000)
    Pb = P[fb] + 1e-10 * P[fb].max()
    flat = np.exp(np.log(Pb).mean(0)) / Pb.mean(0)
    zcr = librosa.feature.zero_crossing_rate(x, frame_length=NFFT, hop_length=HOP, center=True)[0][:n]
    H, Pp = librosa.decompose.hpss(S, kernel_size=31, margin=1.0)
    hE, pE = (H ** 2).sum(0), (Pp ** 2).sum(0)
    chroma = librosa.feature.chroma_stft(S=H ** 2, sr=SR, tuning=0.0, norm=None)  # harmonic chroma
    # pitch steadiness: YIN f0 on frames that are loud and mostly harmonic; music holds notes,
    # speech intonation glides. steady = share of consecutive voiced frames moving < 0.1 semitone
    try:
        f0 = librosa.yin(x, fmin=65, fmax=1000, sr=SR, frame_length=NFFT, hop_length=HOP, center=True)[:n]
    except Exception:
        f0 = np.full(n, np.nan)
    hr = hE / (hE + (Pp ** 2).sum(0) + 1e-12)
    voiced = (rdb > -45) & (hr > 0.6) & np.isfinite(f0)
    st = 12 * np.log2(np.maximum(f0, 1) / 440.0)
    dst = np.abs(np.diff(st, prepend=st[:1]))
    pair = voiced & np.r_[False, voiced[:-1]]
    vband = (freqs >= 300) & (freqs <= 3400)
    venv = np.sqrt(P[vband].sum(0))                                             # voice-band amplitude
    vfrac = P[vband].sum(0) / tot
    mel = librosa.feature.melspectrogram(S=P, sr=SR, n_mels=64)
    oenv = librosa.onset.onset_strength(S=librosa.power_to_db(mel), sr=SR, hop_length=HOP)[:n]

    # onsets for cut snapping
    on = librosa.onset.onset_detect(onset_envelope=oenv, sr=SR, hop_length=HOP, units="time")
    rec["onsets"] = [r(t, 2) for t in on[:64]]
    rec["n_onsets"] = int(len(on))

    # tempo / beats / key: computed always (cheap); merge exposes them when music >= 0.4
    lo, hi = int(FPS * 60 / 220), int(FPS * 60 / 45)
    bconf, lag = norm_ac(oenv, lo, hi)
    try:
        tempo, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=HOP, units="time")
        tempo = float(np.atleast_1d(tempo)[0])
    except Exception:
        tempo, beats = 0.0, []
    wch = (chroma / (chroma.max(0, keepdims=True) + 1e-12) * hE[None, :])[:, w].sum(1)
    (kr, kn, km), (kr2, _, _) = ks_key(wch / (wch.sum() + 1e-12))
    rec["music"] = {"tempo": r(tempo, 1), "beat_conf": r(bconf), "ac_tempo": r(60 * FPS / lag, 1) if lag else None,
                    "key": kn, "mode": km, "key_r": r(kr), "key_margin": r(kr - kr2),
                    "beats": [r(t, 2) for t in list(beats)[:32]]}

    # 10 Hz voice-band level + voice-band share, thresholded at classify time into speech spans
    vdb = db(venv / (NFFT * 0.433))          # hann one-sided STFT band power -> dBFS rms
    tgrid = np.arange(0, adur, 0.1)
    fi = np.clip((tgrid * FPS).astype(int), 0, n - 1)
    rec["vdb10"] = [r(np.mean(vdb[max(0, i - 2): i + 3]), 1) for i in fi]
    rec["vfr10"] = [r(np.mean(vfrac[max(0, i - 2): i + 3]), 2) for i in fi]

    # per-second raw features over a 3 s centered window
    feats = {k: [] for k in ("db", "mod4", "depth", "lster", "zcr_cv", "flat", "tonal", "cstab", "hp", "beat", "vfrac", "steady", "voiced", "floor_hp", "floor_tonal", "floor_rel")}
    cz = chroma - chroma.mean(0, keepdims=True)                                 # centred: a flat
    cn = cz / (np.linalg.norm(cz, axis=0, keepdims=True) + 1e-9)                 # chroma carries no pitch
    cpk = chroma / (chroma.max(0, keepdims=True) + 1e-12)
    peaky = 1 - np.median(cpk, axis=0)                                           # 0 flat .. 1 one pitch class
    blk = max(1, int(round(0.25 * FPS)))
    for s in range(nsec):
        a, b = int(max(0, (s - 1) * FPS)), int(min(n, (s + 2) * FPS))
        m = act[a:b]
        feats["db"].append(r(env[s], 1))
        if b - a < 8 or m.mean() < 0.2:
            for k in feats:
                if k != "db":
                    feats[k].append(None)
            continue
        e = venv[a:b]
        ec = (e - e.mean()) * np.hanning(len(e))
        spec = np.abs(np.fft.rfft(ec, n=max(256, len(ec)))) ** 2
        f = np.fft.rfftfreq(max(256, len(ec)), 1 / FPS)
        feats["mod4"].append(r(spec[(f >= 2.5) & (f <= 6.5)].sum() / (spec[(f >= 0.5) & (f <= 16)].sum() + 1e-12)))
        feats["depth"].append(r(np.std(e) / (np.mean(e) + 1e-12)))
        rr = rms[a:b]
        feats["lster"].append(r(np.mean(rr < 0.5 * rr.mean())))
        zz = zcr[a:b][m] if m.sum() > 4 else zcr[a:b]
        feats["zcr_cv"].append(r(np.std(zz) / (np.mean(zz) + 1e-9)))
        feats["flat"].append(r(np.median(flat[a:b][m]) if m.any() else np.median(flat[a:b]), 4))
        c = cn[:, a:b]
        feats["tonal"].append(r(np.mean(peaky[a:b][m]) if m.any() else np.mean(peaky[a:b])))
        pv = pair[a:b]
        feats["steady"].append(r(np.mean(dst[a:b][pv] < 0.1)) if pv.sum() >= 5 else None)
        feats["voiced"].append(r(np.mean(voiced[a:b])))
        # the floor between syllables: under bare speech it is room noise, under a score it is music
        ra = rms[a:b][m] if m.sum() >= 8 else rms[a:b]
        q = np.where(m)[0] if m.sum() >= 8 else np.arange(b - a)
        qq = q[ra <= np.percentile(ra, 30)] + a
        feats["floor_hp"].append(r(np.mean(hr[qq])))
        feats["floor_tonal"].append(r(np.mean(peaky[qq])))
        feats["floor_rel"].append(r(db(np.percentile(ra, 20)) - db(np.percentile(ra, 90)), 2))
        nb = c.shape[1] // blk
        if nb >= 3:
            cb = c[:, : nb * blk].reshape(12, nb, blk).mean(2)
            cb = cb - cb.mean(0, keepdims=True)
            cb = cb / (np.linalg.norm(cb, axis=0, keepdims=True) + 1e-9)
            feats["cstab"].append(r(np.mean((cb[:, 1:] * cb[:, :-1]).sum(0))))
        else:
            feats["cstab"].append(None)
        feats["hp"].append(r(hE[a:b].sum() / (hE[a:b].sum() + pE[a:b].sum() + 1e-12)))
        a4, b4 = int(max(0, (s - 1.5) * FPS)), int(min(n, (s + 2.5) * FPS))
        feats["beat"].append(r(norm_ac(oenv[a4:b4], lo, min(hi, (b4 - a4) // 2))[0]) if b4 - a4 > 2 * lo + 8 else None)
        feats["vfrac"].append(r(np.mean(vfrac[a:b][m]) if m.any() else np.mean(vfrac[a:b])))
    rec["raw"] = feats
    rec["secs"] = round(time.time() - t0, 2)
    return _write(out, rec)

def _write(out, rec):
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(rec, fh, separators=(",", ":"))
    os.replace(tmp, out)
    return rec["id"]

def _safe(cid):
    try:
        return measure_one(cid), None
    except Exception as e:                                   # keep going; record the failure
        _write(os.path.join(CACHE, cid + ".json"), {"id": cid, "raw_version": RAW_VERSION, "error": repr(e)[:300]})
        return cid, repr(e)

def measure():
    os.makedirs(CACHE, exist_ok=True)
    ids = sorted(f[:-4] for f in os.listdir(CLIPS) if f.endswith(".mp4"))
    def stale(i):
        f = os.path.join(CACHE, i + ".json")
        if not os.path.exists(f):
            return True
        try:
            return json.load(open(f)).get("raw_version") != RAW_VERSION
        except Exception:
            return True
    todo = [i for i in ids if stale(i)]
    print(f"{len(ids)} clips, {len(todo)} to measure with {WORKERS} workers", flush=True)
    t0 = time.time()
    with Pool(WORKERS) as pool:
        for k, (cid, err) in enumerate(pool.imap_unordered(_safe, todo, chunksize=2), 1):
            if err:
                print("ERR", cid, err, flush=True)
            if k % 50 == 0 or k == len(todo):
                el = time.time() - t0
                print(f"  {k}/{len(todo)}  {el:.0f}s  eta {el / k * (len(todo) - k):.0f}s", flush=True)

# ----------------------------------------------------------------------------------------------
# Classifier. Per second, speech and music are scored independently (they co-occur: narration
# over score). Each score is a logistic over a weighted sum of centred features.
# ----------------------------------------------------------------------------------------------
SIL_DB = -50.0
TH = {"speech": 0.5, "music": 0.5}

def sig(z):
    return 1 / (1 + np.exp(-z))

def _f(v, default):
    return default if v is None else v

# Weights were fitted (sign-constrained, L2-regularised logistic regression; signs fixed by
# acoustics, magnitudes learned) on a synthetic listen-free calibration set: macOS `say` narration
# degraded to optical-track quality (reverb, 150 Hz-4 kHz, hiss at 12-20 dB SNR, hum), the same
# narration over pre-1927 archive music beds and synthetic scores at -5..-11 dB, the beds alone,
# synthetic music, sung TTS. Held out: clean TTS, a second narration-over-bed set, 9 noise types.
FILL = {"cstab": 0.6, "beat": 0.25, "steady": 0.2, "floor_rel": -20.0, "floor_hp": 0.5, "floor_tonal": 0.7}
W_SPEECH = ({"depth": 1.16, "zcr_cv": 4.37, "steady": -1.07, "hp": -1.03, "beat": -5.70, "cstab": -2.52,
             "floor_hp": -6.83}, 8.61)
W_MUSIC = ({"steady": 2.53, "hp": 1.25, "beat": 2.13, "depth": -2.13, "zcr_cv": -2.98, "mod4": -1.78,
            "floor_hp": 3.92, "floor_tonal": 6.45}, -6.93)

def _g(F, k, s):
    x = F.get(k, [None] * (s + 1))[s]
    x = FILL.get(k, 0.0) if x is None else x
    return min(x, 1.5) if k == "zcr_cv" else min(x, 2.0) if k == "depth" else x

def second_probs(F, s):
    """-> (p_speech, p_music) for one second, or None when the second is silent."""
    d = F["db"][s]
    if d is None or d < SIL_DB or F["mod4"][s] is None:
        return None
    # gate: pitched, voice-band sound at all? (hiss, rain, wind, engine, hum and rumble fail it -> noise)
    gate = (sig(20 * (_g(F, "tonal", s) - 0.52)) * sig(25 * (0.22 - _g(F, "flat", s)))
            * sig(40 * (_g(F, "vfrac", s) - 0.12)))
    out = []
    for w, b in (W_SPEECH, W_MUSIC):
        out.append(float(gate * sig(sum(v * _g(F, k, s) for k, v in w.items()) + b)))
    return tuple(out)

def label(ps, pm):
    if ps >= TH["speech"] and pm >= TH["music"]:
        return "mixed"
    if ps >= TH["speech"]:
        return "speech"
    if pm >= TH["music"]:
        return "music"
    return "noise"

def spans_from(vdb10, vfr10, timeline, dur):
    """Speech spans (phrase level): 10 Hz voice-band level > clip floor + 6 dB (and > -50 dBFS) with
    voice-band share > 0.3, inside seconds whose kind carries speech; gaps < 0.5 s closed, spans < 0.4 s dropped."""
    v = np.array([-120.0 if x is None else x for x in vdb10]); fr = np.array([0.0 if x is None else x for x in vfr10])
    if not v.size:
        return []
    floor = np.percentile(v, 10)
    ok = (v > max(-50.0, floor + 6)) & (fr > 0.3)
    t = np.arange(len(ok)) * 0.1
    ok &= np.array([timeline[min(int(ti), len(timeline) - 1)] in ("speech", "mixed") for ti in t], bool)
    spans, st = [], None
    for i, on in enumerate(ok):
        if on and st is None:
            st = t[i]
        if (not on or i == len(ok) - 1) and st is not None:
            en = t[i] + (0.1 if on else 0.0)
            if spans and st - spans[-1][1] < 0.5:
                spans[-1][1] = en
            else:
                spans.append([st, en])
            st = None
    return [[round(a, 1), round(min(b, dur), 1)] for a, b in spans if b - a >= 0.4]

def classify(rec):
    c = {"dur": rec.get("dur"), "has_audio": rec.get("has_audio", False)}
    if "error" in rec:
        c.update(kind="none", error=rec["error"])
        return c
    if not rec.get("has_audio"):
        c["kind"] = "none"
        return c
    for k in ("lufs", "peak_db", "lra", "silence", "env", "centroid", "rolloff", "bands", "onsets"):
        if k in rec:
            c[k] = rec[k]
    F = rec.get("raw")
    if not F:
        c.update(kind="silence", p={"silence": 1.0, "speech": 0.0, "music": 0.0, "mixed": 0.0, "noise": 0.0},
                 timeline=["silence"] * len(rec.get("env", [])))
        return c
    nsec = len(F["db"])
    tl, PS, PM = [], [], []
    for s in range(nsec):
        pr = second_probs(F, s)
        if pr is None:
            tl.append("silence")
            continue
        ps, pm = pr
        PS.append(ps); PM.append(pm)
        tl.append(label(ps, pm))
    # smooth isolated single-second flips (a-b-a -> a-a-a)
    for s in range(1, nsec - 1):
        if tl[s - 1] == tl[s + 1] != tl[s] and tl[s] != "silence":
            tl[s] = tl[s - 1]
    fs = tl.count("silence") / nsec
    PS, PM = np.array(PS), np.array(PM)
    if PS.size:
        act = 1 - fs
        p = {"silence": fs, "speech": act * PS.mean(), "music": act * PM.mean(),
             "mixed": act * (PS * PM).mean(), "noise": act * ((1 - PS) * (1 - PM)).mean()}
    else:
        p = {"silence": 1.0, "speech": 0.0, "music": 0.0, "mixed": 0.0, "noise": 0.0}
    frac = {k: tl.count(k) / nsec for k in ("speech", "music", "mixed", "noise")}
    if fs >= 0.8 or not PS.size:
        kind = "silence"
    else:
        sp = frac["speech"] + frac["mixed"]
        mu = frac["music"] + frac["mixed"]
        act = 1 - fs
        if sp >= 0.25 * act and mu >= 0.25 * act:
            kind = "mixed"
        else:
            kind = max(("speech", sp), ("music", mu), ("noise", frac["noise"]), key=lambda z: z[1])[0]
    c["kind"] = kind
    c["p"] = {k: round(float(v), 3) for k, v in p.items()}
    c["timeline"] = tl
    if p["music"] >= 0.4 and rec.get("music"):
        m = rec["music"]
        c["music"] = {"tempo": m["tempo"], "beat_conf": m["beat_conf"], "key": m["key"], "mode": m["mode"],
                      "key_conf": m["key_margin"], "key_r": m["key_r"], "beats": m["beats"]}
    if p["speech"] >= 0.4 and rec.get("vdb10"):
        c["speech_spans"] = spans_from(rec["vdb10"], rec["vfr10"], tl, rec.get("dur") or nsec)
    return c


# Listen-free calibration results (lab/cache/sound-calib/: syn.py builds the set, fit2.py fits, ev.py
# scores). Clip-level kinds under the final weights; "held out" families were never used for fitting.
CALIBRATION = [
    ("held out", "clean TTS narration (8 voices x 3 texts)", 24, "speech 24"),
    ("held out", "TTS narration over pre-1927 archive music beds, bed -4..-8 dB", 24, "mixed 16, speech 5, music 3"),
    ("held out", "noise: hiss, pink, rumble, 60 Hz hum, crackle, rain, wind, engine, crowd babble", 9, "noise 8, mixed 1 (babble)"),
    ("fitted", "degraded narration (reverb, 150-4k Hz, hiss 12-20 dB SNR, hum)", 24, "speech 18, mixed 6"),
    ("fitted", "narration + noise at 10 dB SNR", 24, "speech 21, noise 2, mixed 1"),
    ("fitted", "degraded narration over beds / synthetic score, -5..-11 dB", 24, "mixed 24"),
    ("fitted", "synthetic score alone (chords, melody, +/- drums)", 8, "music 8"),
    ("fitted", "pre-1927 archive music beds (+/- added noise)", 12, "music 8, mixed 4"),
    ("fitted", "sung TTS (Cellos, Good News, Bells)", 3, "mixed 3"),
]
CALIB_SECONDS = ("Per second on the held-out narration-over-bed set: 'carries speech' right 72 %, 'carries music' "
                 "right 65 % (music under loud narration is the weak spot). Held-out clean narration: 100 % of "
                 "seconds speech. Degraded narration alone: ~20 % of seconds wrongly also flagged music (mixed).")

# ----------------------------------------------------------------------------------------------
METHOD = ("ffmpeg mono 22050 Hz. Loudness: ITU-R BS.1770-4 K-weighting (shelf+HPF biquads re-derived for "
          "22.05 kHz, scipy sosfilt), 400 ms blocks/75% overlap, -70 LUFS abs + -10 LU rel gates; mono downmix, so "
          "correlated stereo reads ~3 LU below a stereo meter. LRA = p95-p10 of 3 s short-term loudness (abs -70, "
          "rel -20 gates). Silence = fraction of 93 ms frames (23 ms hop) under -50 dBFS. Classifier (signal "
          "features, no models): per second over a 3 s window; a gate (harmonic-chroma peakiness, 60-5000 Hz "
          "spectral flatness, voice-band share) sends hiss/rain/wind/engine/hum/rumble to noise; then two "
          "independent logistic scores, sign-constrained and fitted on a synthetic listen-free calibration set: "
          "speech (+envelope depth, +ZCR variation, -pitch steadiness, -HPSS harmonic ratio, -beat strength, "
          "-chroma stability, -harmonicity of the inter-syllable floor) and music (+YIN pitch steadiness, "
          "+harmonic ratio, +beat strength, +harmonicity/tonality of the inter-syllable floor, -depth, "
          "-ZCR variation, -4 Hz syllabic modulation). Both high = mixed, neither = noise. Clip kind from the "
          "per-second timeline (mixed when >= 25 % of sounding seconds carry each). Key: Krumhansl-Schmuckler on "
          "energy-weighted harmonic chroma. Tempo/beats: librosa beat_track; beat_conf = normalised onset "
          "autocorrelation peak 45-220 bpm. Speech spans: 10 Hz voice-band (300-3400 Hz) level > clip floor + 6 dB "
          "inside speech/mixed seconds, gaps < 0.5 s closed.")

def load_all():
    recs = {}
    for f in os.listdir(CACHE):
        if f.endswith(".json"):
            with open(os.path.join(CACHE, f)) as fh:
                rec = json.load(fh)
            recs[rec["id"]] = rec
    return recs

def merge(recs=None):
    recs = recs or load_all()
    clips = {cid: classify(rec) for cid, rec in sorted(recs.items())}
    with open(OUT, "w") as fh:
        json.dump({"version": 1, "method": METHOD, "clips": clips}, fh, separators=(",", ":"))
    print(f"wrote {OUT}  ({len(clips)} clips, {os.path.getsize(OUT) / 1e6:.1f} MB)")
    return clips

# ----------------------------------------------------------------------------------------------
def old_labels():
    d = json.load(open(os.path.join(LAB, "lab-data.json")))
    return {s["id"]: s["audio"]["kind"] for s in d["shots"] if s.get("audio") and s["audio"].get("kind")}

def compare(clips, old):
    """Map ours onto the old 5-way scheme (speech|music|sound|silence|none)."""
    mapto = {"speech": "speech", "music": "music", "noise": "sound", "silence": "silence", "none": "none"}
    rows = []
    for cid, ok in old.items():
        if cid not in clips:
            continue
        ours = clips[cid]["kind"]
        rows.append((ok, ours, mapto.get(ours, ours)))
    return rows

def validate(clips=None, quiet=False):
    from collections import Counter, defaultdict
    clips = clips or json.load(open(OUT))["clips"]
    dist = Counter(c["kind"] for c in clips.values())
    old = old_labels()
    rows = compare(clips, old)
    conf = defaultdict(Counter)
    for ok, ours, _ in rows:
        conf[ok][ours] += 1
    strict = sum(1 for ok, _, m in rows if ok == m)
    # lenient: "mixed" agrees with speech or music (the old scheme had no mixed class)
    len_ok = sum(1 for ok, ours, m in rows if ok == m or (ours == "mixed" and ok in ("speech", "music")))
    # coarse: has sound-to-duck (speech/music/mixed) vs not
    carry = lambda k: k in ("speech", "music", "mixed")
    coarse = sum(1 for ok, ours, _ in rows if carry(ok) == carry(ours))
    res = {"dist": dict(dist), "n_compared": len(rows), "strict": strict, "lenient": len_ok, "coarse": coarse,
           "confusion": {k: dict(v) for k, v in conf.items()}}
    if not quiet:
        print("distribution:", dict(dist))
        print(f"vs lab-data labels (n={len(rows)}): strict {strict / max(1, len(rows)):.1%}  "
              f"lenient(mixed~speech/music) {len_ok / max(1, len(rows)):.1%}  "
              f"carries-voice-or-music {coarse / max(1, len(rows)):.1%}")
        kinds = ["speech", "music", "mixed", "noise", "silence", "none"]
        print("old \\ ours".ljust(10), *[k[:7].rjust(8) for k in kinds])
        for ok in ["speech", "music", "sound", "silence", "none"]:
            print(ok.ljust(10), *[str(conf[ok][k]).rjust(8) for k in kinds])
    return res

def wygwyl(clips):
    import glob
    out = []
    for pj in sorted(glob.glob(os.path.join(LAB, "wygwyl", "cuts", "*", "patches.json"))):
        cut = os.path.basename(os.path.dirname(pj))
        try:
            patches = json.load(open(pj))
        except Exception:
            continue
        if isinstance(patches, dict):
            patches = patches.get("patches", [])
        for p in patches:
            cid = (p.get("clip") or {}).get("id")
            c = clips.get(cid)
            if not c:
                out.append((cut, p.get("id"), cid, "unmeasured", None, None, (p.get("clip") or {}).get("title")))
                continue
            pr = c.get("p", {})
            out.append((cut, p.get("id"), cid, c["kind"], pr.get("speech"), pr.get("music"), (p.get("clip") or {}).get("title")))
    return out

def report(clips, res):
    from collections import Counter
    L = ["# SOUND CENSUS", "", f"Clips measured: {len(clips)} (`lab/clips/*.mp4`). Script: `lab/sound_census.py`; "
         "per-clip caches `lab/cache/sound/<id>.json`; merged `lab/cache/sound-census.json`.", "",
         "## Counts", "", "| kind | clips |", "|---|---|"]
    for k in ("none", "silence", "speech", "music", "mixed", "noise"):
        L.append(f"| {k} | {res['dist'].get(k, 0)} |")
    has_m = sum(1 for c in clips.values() if "music" in c)
    has_s = sum(1 for c in clips.values() if "speech_spans" in c)
    L += ["", f"Clips with music >= 0.4 (tempo/key/beats attached): {has_m}. "
          f"Clips with speech >= 0.4 (speech spans attached): {has_s}.", "", "## Method", "", METHOD, "",
          "## Validation", "",
          f"Compared with the existing `audio.kind` labels on {res['n_compared']} read shots in `lab-data.json`. "
          "Those labels are themselves a cruder heuristic (clipwork.py: 16 kHz, flatness + 3-7 Hz modulation, "
          "no mixed class), not human ground truth, so agreement measures consistency, not accuracy.", "",
          f"- strict agreement (noise=sound; mixed counted wrong): {res['strict']}/{res['n_compared']} "
          f"= {res['strict'] / max(1, res['n_compared']):.1%}",
          f"- lenient (mixed accepted for speech or music): {res['lenient']}/{res['n_compared']} "
          f"= {res['lenient'] / max(1, res['n_compared']):.1%}",
          f"- coarse 'carries voice or music' yes/no: {res['coarse']}/{res['n_compared']} "
          f"= {res['coarse'] / max(1, res['n_compared']):.1%}", "",
          "Confusion (rows old label, columns census kind):", "",
          "| old \\ census | speech | music | mixed | noise | silence | none |", "|---|---|---|---|---|---|---|"]
    for ok in ("speech", "music", "sound", "silence", "none"):
        row = res["confusion"].get(ok, {})
        L.append(f"| {ok} | " + " | ".join(str(row.get(k, 0)) for k in ("speech", "music", "mixed", "noise", "silence", "none")) + " |")
    L += ["", "### Listen-free calibration (ground truth by construction)", "",
          "| set | what | clips | census kinds |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {n} | {k} |" for a, b, n, k in CALIBRATION]
    L += ["", CALIB_SECONDS, "", "### Consistency checks on the archive", ""]
    corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
    src = {}
    for cid, c in clips.items():
        if c["kind"] in ("speech", "music", "mixed", "noise"):
            src.setdefault(corpus.get(cid, {}).get("sourceSlug"), []).append(c["kind"])
    many = [v for v in src.values() if len(v) >= 3]
    agree = np.mean([max(np.mean([k in ("speech", "mixed") for k in v]), 1 - np.mean([k in ("speech", "mixed") for k in v])) for v in many]) if many else 0
    L += [f"- Within one source film (sources with >= 3 sounding clips, n={len(many)}), clips agree on "
          f"'carries speech' {agree:.1%} of the time (films rarely switch between narrated and un-narrated).",
          "- Title anchors: " + "; ".join(
              f"`{t}` ({why}): " + ", ".join(f"{k} {v}" for k, v in Counter(
                  c["kind"] for cid, c in clips.items() if corpus.get(cid, {}).get("sourceTitle", "").startswith(t)).most_common())
              for t, why in (("Master Hands", "1936, symphonic score, no narration"),
                             ("Communications Primer", "1953 Eames film, narrated"),
                             ("River, The", "1937, Thomson score under Lorentz narration"))), "",
          "### How good is it, honestly", "",
          "- none / silence are exact (stream probe; -50 dBFS frames). The loudness numbers are measurements, not guesses "
          "(K-filter checked: 1 kHz sine at -20 dBFS peak reads -23.28 LUFS vs -23.01 reference, 0.27 dB of "
          "22.05 kHz bilinear warping; a 20 dB step reads LRA 20.0).",
          "- speech vs not-speech is the reliable split (clean narration 100 %, degraded 75-88 % speech-only, rest "
          "tagged mixed, which still carries speech). Use `p.speech` and `speech_spans` to duck.",
          "- music under narration is the weak spot: roughly a third of such seconds are missed and ~20 % of bare "
          "narration seconds are over-flagged as mixed. Treat `mixed` as 'speech, probably with a bed', and trust "
          "`music` (music without speech) more than `mixed` for music.",
          "- the old lab-data labels are a cruder heuristic (no mixed class; 'sound' mostly = noisy narration by "
          "our reading), so the low strict agreement is mainly definitional; the coarse carries-voice-or-music "
          "agreement is the fairer number.",
          "- tempo comes from librosa beat_track and is quantised by the 23 ms hop (values like 123.0/136.0/143.6 "
          "recur); only trust it when `beat_conf` > ~0.35 (median across music clips is ~0.16: most archive "
          "scores are rubato orchestral). Key confidence (`key_conf` = margin between best and 2nd-best "
          "Krumhansl correlation) is usually < 0.1, i.e. weak.", ""]
    L += ["## WYGWYL cut patches carrying music or speech", ""]
    rows = wygwyl(clips)
    by = {}
    for row in rows:
        by.setdefault(row[0], []).append(row)
    for cut, rs in by.items():
        cnt = Counter(x[3] for x in rs)
        L.append(f"### {cut} — {len(rs)} patches: " + ", ".join(f"{k} {v}" for k, v in cnt.most_common()))
        L.append("")
        hits = [x for x in rs if x[3] in ("music", "speech", "mixed")]
        if hits:
            L += ["| patch | clip | title | kind | p speech | p music |", "|---|---|---|---|---|---|"]
            for cut_, pid, cid, k, ps, pm, title in hits:
                L.append(f"| {pid} | `{cid[:8]}` | {title or ''} | {k} | {ps} | {pm} |")
        else:
            L.append("none")
        L.append("")
    with open(REPORT, "w") as fh:
        fh.write("\n".join(L))
    print("wrote", REPORT)

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--inspect" in args:                       # print 10 clips per kind with their features
        import random
        cl = json.load(open(OUT))["clips"]; recs = load_all(); random.seed(1)
        FK = ["mod4", "depth", "lster", "zcr_cv", "flat", "tonal", "hp", "beat", "steady", "floor_hp", "floor_tonal"]
        for kind in ("speech", "music", "mixed", "noise", "silence", "none"):
            ids = [i for i, c in cl.items() if c["kind"] == kind]
            print(f"\n== {kind} ({len(ids)})")
            for i in random.sample(ids, min(10, len(ids))):
                c, F = cl[i], recs[i].get("raw") or {}
                med = " ".join(f"{k}={np.median([v for v in F.get(k, []) if v is not None] or [np.nan]):.2f}" for k in FK) if F else ""
                print(i[:8], c.get("lufs"), c.get("p"), "".join(k[0] for k in c.get("timeline", [])), med)
        sys.exit()
    if "--validate" in args:
        validate()
        sys.exit()
    if "--merge" not in args:
        measure()
    clips = merge()
    res = validate(clips)
    report(clips, res)
