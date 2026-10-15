#!/usr/bin/env python3
"""
DECOMPOSE WARGAMES SOUND & PRE-RENDER NORMALIZED CONCATENATED ARCHIVAL AUDIO
============================================================================
Applies the full WYGWYL · ATLAS (`sound_census.py` + `sound-cineosis.json` + `render_found.py` + `sound-table.json`)
acoustic decomposition and normalization pipeline to all 105 beats of WarGames (1983):

1. Full Acoustic Window Alignment (`[a0, a1]`):
   - Aligns each beat's spoken text and overlapping Whisper segments across the beat's full scene window
     (not just the primary visual cut) so no spoken words or clauses are truncated.
2. Signal Decomposition on 22,050 Hz Master Audio (`NFFT=2048, HOP=512`, ~23ms hop):
   - ITU-R BS.1770-4 K-Weighted Integrated Loudness (`lufs`), Loudness Range (`lra`), and Peak (`peak_db`).
   - HPSS (Harmonic-Percussive Source Separation via Wiener-masked `median_filter(S, (1,31))` vs `(31,1)`):
     - Separates Harmonic Formant/Tone Energy $H(f,t)$ from Percussive Consonant/Klaxon/Key-Click Energy $P(f,t)$.
     - Extracts the Inter-Syllable Floor (`floor_hp`, `floor_rel_db`, `floor_tonal`) to measure room-tone vs score/klaxon bed.
     - Computes 4 Hz Syllabic Modulation (`mod4` in `2.5–6.5 Hz`).
   - Vectorized YIN Fundamental Pitch Tracker $f_0(t)$ (`65–500 Hz`) & Voice Register (`ABYSSAL < 80Hz`, `DEEP 80–110Hz`, `LOW 110–160Hz`, `HIGH > 160Hz`).
   - 16-Band Log-Mel Spectrogram (`60–8000 Hz`, 64 time-steps) decomposed into:
     - `mel16`: Full 16-band spectrogram (16 Base-36 strings of length 64)
     - `harm_env`: Continuous Harmonic Formant Envelope (64 steps)
     - `perc_env`: Continuous Percussive Transient Envelope (64 steps)
     - `floor_env`: Continuous Inter-Syllable Floor / Drone Envelope (64 steps)
   - High-Resolution `rms` & `f0` contours sampled at `hop = 0.05s` (`20 Hz`) for the WYGWYL Sound Bench SVG lane.
   - Word-by-Word Prosodic & Event Decomposition (`words` & `events`):
     - Each spoken word has `{w, s, e, ts, te, dur, gr ('A'|'B'|'C'), st (prosodic stress z-score), f0 (Hz), lufs, mass, syllables, band, hp_ratio}`.
     - Explicit `events`: `[{t, dur, type: 'PAUSE' | 'BREATH' | 'ACCENT' | 'PITCH_HIGH' | 'PLOSIVE' | 'KLAXON_TRANSIENT', word}]`.
3. Local Verified Archival Speech & Audio Corpus (`100%` Local Playable MP4 + Odyssey Pre-Rendered M4A):
   - Indexes all 161 local speaking MP4 clips in `lab/clips/` (with `sound-census.json` LUFS, `kind`, `onsets`, `centroid`, and `words.json` timestamps)
     PLUS all 9,289 pre-rendered archival speech pieces in `lab/odyssey/found-audio/{performance,spoken}/*.m4a`.
   - Matches every beat's words and clauses to real local audio slices, measures each slice's true K-weighted `lufs`, `f0` (Hz), `register`, `voice_dist` (distance from the 1983 speaker's pitch/timbre), and `census_kind` (`speech | mixed | music | noise`).
4. Pre-Rendered Normalized Concatenated Audio Comparison Tracks (`lab/cache/wg_sound/`):
   - For every beat (1..105), renders and caches 3 directly comparable audio files + full decomposed spectrograms:
     - `BXX_orig.m4a`: The 1983 WarGames original audio across `[a0, a1]`, normalized to `-21 LUFS`.
     - `BXX_aligned.m4a`: **1983 Prosodic Clock Lock (WYGWYL Mix Law)** — each archival word/phrase is denoised (spectral subtraction of quietest 15% frames), bandpass-matched (`90–6000 Hz`), normalized to `-21 LUFS`, and placed at the **exact `[s, e]` word timestamps of the 1983 speaker**, preserving the 1983 speaker's exact `PAUSE / BREATH` gaps over a carved `-33 LUFS` harmonic room-tone/drone bridge (`bridges()`).
     - `BXX_tight.m4a`: **Tight Bumblebee Radio Splice** — concatenates the normalized archival pieces back-to-back with `35ms` cosine overlap-add and `18ms` FM tuning/carrier micro-seams, plus computes the decomposed spectrogram of the concatenated audio itself so the user can visually compare the 1983 spectrogram vs. the Concatenated spectrogram!
"""
import glob
import json
import math
import os
import re
import subprocess
import sys
import time
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import butter, sosfilt, sosfiltfilt, stft, istft

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.join(ROOT, "lab")
OUT_AUDIO_DIR = os.path.join(LAB, "cache", "wg_sound")
OUT_JSON_PATH = os.path.join(LAB, "wargames-sound-bench.json")
OUT_SPEC_CACHE = os.path.join(HERE, "wargames_decomposed_sound.json")

SR = 22050
NFFT = 2048
HOP = 512
FPS = SR / HOP  # ~43.066 frames/sec
D36 = "0123456789abcdefghijklmnopqrstuvwxyz"

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "out", "into", "over", "after", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "it", "its", "it's", "that", "this", "these", "those", "i", "you", "he", "she",
    "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "our",
    "their", "what", "which", "who", "whom", "where", "when", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "just", "should", "now", "don't", "didn't", "can't", "won't", "i'm", "you're",
    "we're", "they're", "i've", "you've", "there", "here", "about", "as", "well",
    "oh", "uh", "um", "yeah", "yes", "okay", "ok", "got", "get", "go", "going"
}

norm = lambda w: re.sub(r"[^a-z0-9']", "", str(w).lower()).strip("'")


def stem(w):
    w = norm(w)
    for suf in ("ing", "ed", "es", "s", "ly", "er", "or", "tion", "ment"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def reg_of(f0):
    if not f0 or f0 <= 0:
        return "UNVOICED"
    return "ABYSSAL" if f0 < 80 else "DEEP" if f0 < 110 else "LOW" if f0 < 160 else "HIGH"


# -----------------------------------------------------------------------------
# ITU-R BS.1770-4 K-Weighting Filter & Gated Integrated Loudness (from sound_census.py)
# -----------------------------------------------------------------------------
def k_filter_sos(fs=SR):
    G, Q, fc = 3.999843853973347, 0.7071752369554196, 1681.974450955533
    A = 10 ** (G / 40)
    w0 = 2 * np.pi * fc / fs
    c, al = np.cos(w0), np.sin(w0) / (2 * Q)
    sA = np.sqrt(A)
    b = [
        A * ((A + 1) + (A - 1) * c + 2 * sA * al),
        -2 * A * ((A - 1) + (A + 1) * c),
        A * ((A + 1) + (A - 1) * c - 2 * sA * al),
    ]
    a = [
        (A + 1) - (A - 1) * c + 2 * sA * al,
        2 * ((A - 1) - (A + 1) * c),
        (A + 1) - (A - 1) * c - 2 * sA * al,
    ]
    shelf = np.r_[np.array(b) / a[0], np.array(a) / a[0]]
    Q2, fc2 = 0.5003270373253953, 38.13547087613982
    w02 = 2 * np.pi * fc2 / fs
    c2, al2 = np.cos(w02), np.sin(w02) / (2 * Q2)
    b2 = [(1 + c2) / 2, -(1 + c2), (1 + c2) / 2]
    a2 = [1 + al2, -2 * c2, 1 - al2]
    hp = np.r_[np.array(b2) / a2[0], np.array(a2) / a2[0]]
    return np.vstack([shelf, hp])


K_SOS = k_filter_sos(SR)
BAND_SOS = butter(2, [85, 6200], "bandpass", fs=SR, output="sos")


def _block_ms(y, win, hop):
    n = len(y)
    if n < win:
        return np.array([np.mean(y ** 2)]) if n else np.array([])
    idx = np.arange(0, n - win + 1, hop)
    cs = np.r_[0.0, np.cumsum(y.astype(np.float64) ** 2)]
    return (cs[idx + win] - cs[idx]) / win


def measure_lufs(x):
    if x is None or len(x) < SR // 8:
        return -32.0, 4.0
    # Tile very short word slices so BS.1770 400ms blocks measure accurately (as in render_found.py)
    if len(x) < int(0.55 * SR):
        x = np.tile(x, int(np.ceil(0.55 * SR / max(1, len(x)))))
    y = sosfilt(K_SOS, x)
    z = _block_ms(y, int(0.4 * SR), int(0.1 * SR))
    lk = -0.691 + 10 * np.log10(z + 1e-20)
    g = z[lk > -70]
    if g.size == 0:
        return -45.0, 2.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = z[(lk > -70) & (lk > rel)]
    I = -0.691 + 10 * np.log10((g2.mean() if g2.size else g.mean()) + 1e-20)
    sw = 1.0 if len(x) < 3 * SR else 3.0
    st = -0.691 + 10 * np.log10(_block_ms(y, int(sw * SR), int(0.1 * SR)) + 1e-20)
    st = st[st > -70]
    lra = float(np.percentile(st, 95) - np.percentile(st, 10)) if st.size >= 2 else 3.0
    return round(float(I), 2), round(float(lra), 2)


def encode_b36(arr_01):
    return "".join(D36[int(round(float(v) * 35))] for v in np.clip(arr_01, 0.0, 1.0))


# -----------------------------------------------------------------------------
# Vectorized YIN Fundamental Pitch Tracker (65–500 Hz)
# -----------------------------------------------------------------------------
def compute_yin_f0(x, sr=SR, win=NFFT, hop=HOP):
    if len(x) < win + hop:
        return np.zeros(max(1, len(x) // hop + 1), dtype=np.float32)
    pad_x = np.pad(x, (win // 2, win // 2), mode="reflect")
    n_frames = 1 + (len(pad_x) - win) // hop
    frames = np.lib.stride_tricks.sliding_window_view(pad_x, win)[::hop][:n_frames]
    W = win // 2
    tau_min = int(sr / 500)  # 500 Hz
    tau_max = int(sr / 65)   # 65 Hz
    F = np.fft.rfft(frames, n=2 * win, axis=1)
    F1 = np.fft.rfft(frames[:, :W], n=2 * win, axis=1)
    acf = np.fft.irfft(F1.conj() * F, n=2 * win, axis=1)[:, :tau_max + 1]
    e0 = np.sum(frames[:, :W] ** 2, axis=1, keepdims=True)
    cs = np.cumsum(frames ** 2, axis=1)
    e_tau = cs[:, W:W + tau_max + 1] - cs[:, :tau_max + 1]
    d = np.maximum(0.0, e0 + e_tau - 2.0 * acf)
    d[:, 0] = 1.0
    cm = np.cumsum(d[:, 1:], axis=1)
    d_norm = np.ones_like(d)
    d_norm[:, 1:] = d[:, 1:] * np.arange(1, tau_max + 1)[None, :] / (cm + 1e-12)
    seg = d_norm[:, tau_min:tau_max + 1]
    best_tau = tau_min + np.argmin(seg, axis=1)
    best_val = np.min(seg, axis=1)
    f0 = np.where(best_val < 0.34, sr / np.maximum(1, best_tau), 0.0).astype(np.float32)
    return f0


# -----------------------------------------------------------------------------
# 16-Band Mel/Bark Filterbank (60 Hz .. 8000 Hz) + HPSS Decomposition
# -----------------------------------------------------------------------------
MEL_EDGES = np.geomspace(60.0, 8000.0, 17)


def decompose_signal(x, n_steps=64):
    """
    Decomposes a 22,050 Hz mono signal x into:
      - LUFS, LRA, Peak dB
      - STFT Magnitude S, Harmonic H, Percussive P (via 2D median filtering HPSS)
      - 16-Band Log-Spectrogram (64 time-steps, Base-36 encoded)
      - Harmonic Formant Envelope, Percussive Transient Envelope, Inter-Syllable Floor Envelope
      - YIN f0 pitch contour & RMS contour at hop=0.05s (20 Hz)
      - 4 Hz Syllabic Modulation (mod4), Harmonic-to-Percussive Ratio (hp_ratio), Floor Harmonicity (floor_hp)
    """
    if len(x) < NFFT:
        x = np.pad(x, (0, NFFT - len(x)))
    dur = len(x) / SR
    lufs, lra = measure_lufs(x)
    peak_db = round(float(20.0 * np.log10(max(float(np.max(np.abs(x))), 1e-6))), 2)

    freqs, t_frames, Z = stft(x, fs=SR, nperseg=NFFT, noverlap=NFFT - HOP)
    S = np.abs(Z) + 1e-8
    n_f = S.shape[1]

    # HPSS via median filtering along time (Harmonic: kernel 31 frames ~0.7s) and frequency (Percussive: kernel 31 bins ~330Hz)
    H_med = median_filter(S, size=(1, min(31, max(3, n_f // 2))))
    P_med = median_filter(S, size=(31, 1))
    Mh = (H_med ** 2) / (H_med ** 2 + P_med ** 2 + 1e-12)
    Mp = 1.0 - Mh
    H = S * np.sqrt(Mh)
    Pp = S * np.sqrt(Mp)

    P_pow = S ** 2
    H_pow = H ** 2
    Pp_pow = Pp ** 2

    hE = H_pow.sum(0)
    pE = Pp_pow.sum(0)
    hr_frame = hE / (hE + pE + 1e-12)
    hp_ratio = round(float(hE.sum() / (hE.sum() + pE.sum() + 1e-12)), 3)

    # Frame RMS & Voice-band (300–3400 Hz) energy
    rms_frame = np.sqrt(np.mean(P_pow, axis=0))
    rdb = 20.0 * np.log10(np.maximum(rms_frame, 1e-6))
    vband = (freqs >= 300) & (freqs <= 3400)
    venv = np.sqrt(H_pow[vband].sum(0))  # Harmonic voice-band amplitude!
    p_venv = np.sqrt(Pp_pow[(freqs >= 1000) & (freqs <= 7500)].sum(0))  # Percussive consonant/klaxon transients!

    # Inter-syllable floor (quietest 30% of active frames, as in sound_census.py)
    act = rdb > -52.0
    q_idx = np.where(rms_frame <= np.percentile(rms_frame[act] if act.any() else rms_frame, 30))[0]
    floor_hp = round(float(np.mean(hr_frame[q_idx])) if q_idx.size else 0.5, 3)
    floor_rel_db = round(float(np.percentile(rdb, 20) - np.percentile(rdb, 90)), 2)

    # 4 Hz syllabic modulation (2.5–6.5 Hz share of voice-band envelope spectrum)
    if len(venv) >= 16:
        ec = (venv - venv.mean()) * np.hanning(len(venv))
        spec_e = np.abs(np.fft.rfft(ec, n=max(256, len(ec)))) ** 2
        f_e = np.fft.rfftfreq(max(256, len(ec)), 1.0 / FPS)
        mod4 = round(float(spec_e[(f_e >= 2.5) & (f_e <= 6.5)].sum() / (spec_e[(f_e >= 0.5) & (f_e <= 16.0)].sum() + 1e-12)), 3)
    else:
        mod4 = 0.25

    # Spectral centroid & flatness (60–5000 Hz)
    w_act = act if act.any() else np.ones(n_f, dtype=bool)
    cent_frames = np.sum(S * freqs[:, None], axis=0) / np.sum(S, axis=0)
    centroid_hz = round(float(np.mean(cent_frames[w_act])), 1)
    fb = (freqs >= 60) & (freqs <= 5000)
    Pb = P_pow[fb] + 1e-10 * P_pow[fb].max()
    flat_frames = np.exp(np.log(Pb).mean(0)) / Pb.mean(0)
    flatness = round(float(np.median(flat_frames[w_act])), 3)

    # YIN f0 pitch contour
    f0_raw = compute_yin_f0(x)
    if len(f0_raw) < n_f:
        f0_raw = np.pad(f0_raw, (0, n_f - len(f0_raw)))
    else:
        f0_raw = f0_raw[:n_f]
    voiced_mask = (rdb > -46.0) & (hr_frame > 0.45) & (f0_raw >= 65.0) & (f0_raw <= 450.0)
    f0_clean = np.where(voiced_mask, f0_raw, 0.0)
    voiced_vals = f0_clean[f0_clean > 0]
    f0_median = round(float(np.median(voiced_vals)), 1) if voiced_vals.size else 125.0
    register = reg_of(f0_median)

    # 16-Band Log-Spectrogram resampled to n_steps (64 columns)
    idx_grid = np.linspace(0, n_f - 1, n_steps)

    def norm_db_curve(arr, dyn_range=38.0):
        interp = np.interp(idx_grid, np.arange(n_f), arr)
        db = 20.0 * np.log10(np.maximum(interp, 1e-6))
        top = float(np.percentile(db, 96)) if len(db) else 0.0
        return np.clip((db - (top - dyn_range)) / dyn_range, 0.0, 1.0)

    mel16_b36 = []
    for b_i in range(16):
        f_lo, f_hi = MEL_EDGES[b_i], MEL_EDGES[b_i + 1]
        b_mask = (freqs >= f_lo) & (freqs < f_hi)
        if not np.any(b_mask):
            b_mask[min(len(freqs) - 1, int(f_lo * NFFT / SR))] = True
        band_amp = np.sqrt(np.mean(P_pow[b_mask], axis=0))
        mel16_b36.append(encode_b36(norm_db_curve(band_amp, 40.0)))

    # Legacy 4 bands for backward compatibility
    b0_n = norm_db_curve(np.sqrt(np.mean(P_pow[(freqs >= 60) & (freqs < 300)], axis=0)))
    b1_n = norm_db_curve(np.sqrt(np.mean(P_pow[(freqs >= 300) & (freqs < 1200)], axis=0)))
    b2_n = norm_db_curve(np.sqrt(np.mean(P_pow[(freqs >= 1200) & (freqs < 3200)], axis=0)))
    b3_n = norm_db_curve(np.sqrt(np.mean(P_pow[(freqs >= 3200) & (freqs <= 8000)], axis=0)))

    harm_n = norm_db_curve(venv, 36.0)
    perc_n = norm_db_curve(p_venv, 36.0)
    # Moving minimum / floor envelope across time
    floor_curve = median_filter(venv, size=max(5, int(0.45 * FPS)))
    floor_n = norm_db_curve(floor_curve, 36.0)

    # High-res hop=0.05s (20 Hz) curves for WYGWYL Sound Bench SVG track
    hop_bench = 0.05
    n_hops = max(4, int(np.ceil(dur / hop_bench)))
    t_hops = np.arange(n_hops) * hop_bench
    f_hops = np.clip(t_hops * FPS, 0, n_f - 1)
    rms_hop = np.interp(f_hops, np.arange(n_f), venv)
    rms_p95 = float(np.percentile(rms_hop, 95)) if rms_hop.size else 1.0
    rms_bench = [round(float(v / max(rms_p95, 1e-5)), 3) for v in rms_hop]
    f0_bench = [int(round(float(f0_clean[int(round(fi))]))) for fi in f_hops]

    # Acoustic onset detection from percussive + harmonic rise
    oenv = np.maximum(0.0, np.diff( np.log1p(venv * 50.0) + 0.6 * np.log1p(p_venv * 50.0), prepend=0.0 ))
    o_thresh = float(np.percentile(oenv, 82)) if oenv.size else 0.1
    onset_frames = [
        i for i in range(1, len(oenv) - 1)
        if oenv[i] > o_thresh and oenv[i] >= oenv[i - 1] and oenv[i] >= oenv[i + 1]
    ]
    onsets_sec = []
    for oi in onset_frames:
        t_o = round(oi / FPS, 2)
        if not onsets_sec or t_o - onsets_sec[-1] >= 0.12:
            onsets_sec.append(t_o)

    return {
        "dur": round(dur, 3),
        "lufs": lufs,
        "lra": lra,
        "peak_db": peak_db,
        "f0_median": f0_median,
        "register": register,
        "hp_ratio": hp_ratio,
        "mod4": mod4,
        "floor_hp": floor_hp,
        "floor_rel_db": floor_rel_db,
        "centroid_hz": centroid_hz,
        "flatness": flatness,
        "mel16": mel16_b36,
        "bands": {
            "sub": encode_b36(b0_n),
            "f1f2": encode_b36(b1_n),
            "pres": encode_b36(b2_n),
            "sib": encode_b36(b3_n),
        },
        "vocal_env": encode_b36(harm_n),
        "harm_env": encode_b36(harm_n),
        "perc_env": encode_b36(perc_n),
        "floor_env": encode_b36(floor_n),
        "hop": hop_bench,
        "rms": rms_bench,
        "f0": f0_bench,
        "onsets": onsets_sec[:48],
        "_venv": venv,
        "_p_venv": p_venv,
        "_f0_clean": f0_clean,
        "_hr_frame": hr_frame,
        "_Z": Z,
        "_Mh": Mh,
        "_Mp": Mp,
    }


# -----------------------------------------------------------------------------
# Decompose Words & Events (WYGWYL sound-cineosis.json format: Grade A/B/C, Stress st, f0, PAUSE/BREATH)
# -----------------------------------------------------------------------------
def align_and_grade_words(line_text, whisper_segs, a0, a1, dec, x_pcm, estimate_phys_fn):
    dur = max(0.5, a1 - a0)
    venv = dec["_venv"]
    p_venv = dec["_p_venv"]
    f0_clean = dec["_f0_clean"]
    hr_frame = dec["_hr_frame"]
    n_f = len(venv)
    onsets = dec["onsets"]

    # Gather Whisper segments overlapping [a0, a1]
    ov_segs = [
        s for s in whisper_segs
        if float(s["end"]) > a0 + 0.1 and float(s["start"]) < a1 - 0.1
    ]
    raw_line_ws = [w for w in line_text.split() if norm(w)]
    if not raw_line_ws:
        return [], []

    # Map words to time spans using overlapping Whisper segments if they match the beat text,
    # otherwise distribute across active harmonic speech spans inside [0, dur]!
    b_norms = [norm(w) for w in raw_line_ws]
    seg_words_pool = []
    for seg in ov_segs:
        s_s = max(0.0, float(seg["start"]) - a0)
        s_e = min(dur, float(seg["end"]) - a0)
        sws = [w for w in str(seg.get("text") or "").split() if norm(w)]
        if not sws or s_e <= s_s + 0.08:
            continue
        phys_l = [estimate_phys_fn(w) for w in sws]
        tot_i = sum(p["intrinsic_dur"] for p in phys_l) or 1.0
        cur = s_s
        for w_s, p_s in zip(sws, phys_l):
            sp = (s_e - s_s) * (p_s["intrinsic_dur"] / tot_i)
            seg_words_pool.append({"w": w_s, "nw": norm(w_s), "s": cur, "e": cur + sp})
            cur += sp

    # Align raw_line_ws to seg_words_pool if there is lexical overlap, else use harmonic energy peaks
    phys_all = [estimate_phys_fn(w) for w in raw_line_ws]
    matched_times = [None] * len(raw_line_ws)
    used_pool = set()
    for i, nw in enumerate(b_norms):
        for j, pw in enumerate(seg_words_pool):
            if j in used_pool:
                continue
            if pw["nw"] == nw or (len(nw) >= 4 and stem(pw["nw"]) == stem(nw)):
                matched_times[i] = (pw["s"], pw["e"])
                used_pool.add(j)
                break

    # Interpolate any unmatched words monotonically between anchors (or across the active speech window)
    # Find active speech start/end from harmonic envelope
    v_thr = float(np.percentile(venv, 30)) if n_f else 0.0
    act_frames = np.where(venv > v_thr)[0]
    sp_start = float(act_frames[0] / FPS) if act_frames.size else 0.15
    sp_end = float(min(dur - 0.1, act_frames[-1] / FPS + 0.18)) if act_frames.size else dur - 0.15
    if sp_end <= sp_start + 0.4:
        sp_start, sp_end = 0.1, max(0.5, dur - 0.1)

    # Fill gaps in matched_times
    i = 0
    while i < len(raw_line_ws):
        if matched_times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(raw_line_ws) and matched_times[j] is None:
            j += 1
        t_left = matched_times[i - 1][1] if i > 0 and matched_times[i - 1] is not None else sp_start
        t_right = matched_times[j][0] if j < len(raw_line_ws) and matched_times[j] is not None else sp_end
        if t_right <= t_left + 0.15 * (j - i):
            t_right = min(dur, t_left + max(0.35, 0.28 * (j - i)))
        # Add natural clause pauses at punctuation inside [i..j]
        weights = []
        pauses_after = []
        for k in range(i, j):
            w_str = raw_line_ws[k]
            p_pause = 0.42 if w_str.endswith((".", "!", "?", "—")) else (0.24 if w_str.endswith((",", ";", ":")) else 0.04)
            if k == j - 1:
                p_pause = 0.0
            weights.append(phys_all[k]["intrinsic_dur"])
            pauses_after.append(p_pause)
        tot_Need = sum(weights) + sum(pauses_after) or 1.0
        scale = (t_right - t_left) / tot_Need
        cur_t = t_left
        for idx_k, k in enumerate(range(i, j)):
            w_d = weights[idx_k] * scale
            p_d = pauses_after[idx_k] * scale
            matched_times[k] = (cur_t, cur_t + w_d)
            cur_t += w_d + p_d
        i = j

    # Refine each word's [s, e] and tight trim [ts, te] using spectrogram onsets & energy!
    words_out = []
    raw_stresses = []
    for idx, (w_str, phys, (w_s, w_e)) in enumerate(zip(raw_line_ws, phys_all, matched_times)):
        w_s = max(0.0, min(dur - 0.12, float(w_s)))
        w_e = max(w_s + 0.12, min(dur, float(w_e)))
        # Cap excessive Whisper span if a pause was swallowed into the word
        max_reasonable = max(0.32, phys["intrinsic_dur"] * 1.65)
        if w_e - w_s > max_reasonable:
            # Find where energy peaks inside [w_s, w_e]
            fa = max(0, min(n_f - 1, int(w_s * FPS)))
            fb = max(fa + 1, min(n_f, int(w_e * FPS) + 1))
            pk_f = fa + int(np.argmax(venv[fa:fb]))
            pk_t = pk_f / FPS
            w_s = max(w_s, pk_t - 0.35 * max_reasonable)
            w_e = min(w_e, w_s + max_reasonable)

        # Snap ts to nearest acoustic onset within ±0.08s
        near_on = [o for o in onsets if abs(o - w_s) <= 0.09]
        ts = max(0.0, (near_on[0] if near_on else w_s) - phys["pre_roll"] * 0.5)
        te = min(dur, w_e + phys["tail_pad"] * 0.65)

        fa = max(0, min(n_f - 1, int(w_s * FPS)))
        fb = max(fa + 1, min(n_f, int(w_e * FPS) + 1))
        w_venv = venv[fa:fb]
        w_pvenv = p_venv[fa:fb]
        w_f0s = f0_clean[fa:fb]
        w_voiced = w_f0s[w_f0s > 0]
        w_f0 = round(float(np.median(w_voiced)), 1) if w_voiced.size else None
        w_hr = round(float(np.mean(hr_frame[fa:fb])), 2) if fb > fa else 0.65

        # Slice PCM for word LUFS
        s_i0 = max(0, int(ts * SR))
        s_i1 = min(len(x_pcm), int(te * SR))
        w_lufs, _ = measure_lufs(x_pcm[s_i0:s_i1]) if s_i1 - s_i0 > 256 else (dec["lufs"], 2.0)

        # Prosodic stress score combining energy, pitch excursion, and duration
        e_score = float(np.max(w_venv)) / (float(np.mean(venv)) + 1e-6) if w_venv.size else 1.0
        p_score = (w_f0 / max(80.0, dec["f0_median"])) if w_f0 else 0.95
        raw_st = 0.55 * e_score + 0.30 * p_score + 0.15 * (phys["acoustic_mass"] / 0.6)
        raw_stresses.append(raw_st)

        words_out.append({
            "w": w_str,
            "s": round(w_s, 2),
            "e": round(w_e, 2),
            "ts": round(ts, 3),
            "te": round(te, 3),
            "t0": round(w_s, 2),
            "t1": round(w_e, 2),
            "dur": round(w_e - w_s, 3),
            "f0": w_f0,
            "lufs": w_lufs,
            "hp_ratio": w_hr,
            "mass": round(phys["acoustic_mass"] * min(1.5, max(0.6, e_score * 0.7)), 3),
            "syllables": phys["syllables"],
            "energy": round(min(1.0, e_score / 2.2), 2),
            "sibilance": round(min(1.0, float(np.max(w_pvenv)) / (float(np.percentile(p_venv, 92)) + 1e-6)), 2) if w_pvenv.size else 0.25,
            "band": phys["dominant_band"],
        })

    # Normalize prosodic stress z-score (st) and assign WYGWYL Cut Grade A / B / C!
    st_arr = np.array(raw_stresses, dtype=np.float32)
    st_mean = float(np.mean(st_arr)) if st_arr.size else 1.0
    st_std = float(np.std(st_arr)) if st_arr.size > 1 and np.std(st_arr) > 1e-4 else 0.35

    events = []
    for idx, w in enumerate(words_out):
        z_st = round(float(np.clip((raw_stresses[idx] - st_mean) / st_std, -1.5, 2.4)), 2)
        w["st"] = z_st
        is_content = norm(w["w"]) not in STOPWORDS and len(norm(w["w"])) > 2
        if (is_content and z_st >= 0.15) or z_st >= 0.65 or w["w"].endswith((".", "!", "?")):
            w["gr"] = "A"
        elif is_content or z_st >= -0.35:
            w["gr"] = "B"
        else:
            w["gr"] = "C"

        if z_st >= 0.75:
            events.append({"t": w["s"], "dur": w["dur"], "type": "ACCENT", "word": w["w"]})
        if w["f0"] and w["f0"] >= dec["f0_median"] * 1.18:
            events.append({"t": w["s"], "dur": w["dur"], "type": "PITCH_HIGH", "word": w["w"]})
        if w["sibilance"] >= 0.78:
            events.append({"t": w["s"], "dur": 0.08, "type": "PLOSIVE", "word": w["w"]})

        # Check inter-word gap for PAUSE and BREATH events (exact WYGWYL sound-cineosis.json rules!)
        if idx + 1 < len(words_out):
            g_s = w["e"]
            g_e = words_out[idx + 1]["s"]
            g_dur = round(g_e - g_s, 2)
            if g_dur >= 0.22:
                events.append({"t": g_s, "dur": g_dur, "type": "PAUSE", "word": w["w"]})
                # Check if gap contains mid/high-band breath inspiration energy
                fa = max(0, min(n_f - 1, int(g_s * FPS)))
                fb = max(fa + 1, min(n_f, int(g_e * FPS)))
                if g_dur >= 0.38 and fb > fa and float(np.mean(p_venv[fa:fb])) > float(np.percentile(p_venv, 35)):
                    events.append({"t": round(g_s + 0.05, 2), "dur": round(min(0.32, g_dur * 0.6), 2), "type": "BREATH", "word": w["w"]})

    # Trailing pause after last word
    if words_out and dur - words_out[-1]["e"] >= 0.30:
        events.append({
            "t": words_out[-1]["e"],
            "dur": round(dur - words_out[-1]["e"], 2),
            "type": "PAUSE",
            "word": words_out[-1]["w"],
        })

    events.sort(key=lambda e: e["t"])
    return words_out, events


# -----------------------------------------------------------------------------
# 1983 Multi-Speaker Diarization & Character Vocal Profiles
# -----------------------------------------------------------------------------
SPEAKER_PROFILES = {
    "Capt. Jerry Lawson": {"f0": 118.0, "reg": "LOW", "color": "#ff5538", "role_tag": "MISSILE COMMANDER"},
    "Lt. Steve Phelps": {"f0": 144.0, "reg": "LOW", "color": "#45b1ff", "role_tag": "DEPUTY MISSILE OFFICER"},
    "SAC Duty Officer": {"f0": 124.0, "reg": "LOW", "color": "#f4b938", "role_tag": "SAC / EAM VOICE"},
    "General Beringer": {"f0": 104.0, "reg": "DEEP", "color": "#ff5538", "role_tag": "NORAD COMMANDER"},
    "John McKittrick": {"f0": 122.0, "reg": "LOW", "color": "#45b1ff", "role_tag": "SYSTEMS ARCHITECT"},
    "Col. Joe Conley": {"f0": 116.0, "reg": "LOW", "color": "#2cc89b", "role_tag": "NORAD COLONEL"},
    "Lyle Watson": {"f0": 136.0, "reg": "LOW", "color": "#a77bff", "role_tag": "SYSTEMS ENGINEER"},
    "Paul Richter": {"f0": 130.0, "reg": "LOW", "color": "#f4b938", "role_tag": "WOPR TECHNICIAN"},
    "Arthur Cabot": {"f0": 112.0, "reg": "LOW", "color": "#c9a66b", "role_tag": "PENTAGON AIDE"},
    "David Lightman": {"f0": 148.0, "reg": "LOW", "color": "#45b1ff", "role_tag": "TEENAGER / HACKER"},
    "Jennifer Mack": {"f0": 205.0, "reg": "HIGH", "color": "#ff7ab8", "role_tag": "PARTNER / WITNESS"},
    "Mr. Liggett": {"f0": 120.0, "reg": "LOW", "color": "#c9a66b", "role_tag": "BIOLOGY TEACHER"},
    "Jim Sting": {"f0": 140.0, "reg": "LOW", "color": "#2cc89b", "role_tag": "UW PROGRAMMER"},
    "Malvin": {"f0": 156.0, "reg": "LOW", "color": "#f4b938", "role_tag": "UW LAB GEEK"},
    "WOPR (Joshua)": {"f0": 108.0, "reg": "DEEP", "color": "#f4b938", "role_tag": "WAR COMPUTER"},
    "Stephen Falken": {"f0": 114.0, "reg": "LOW", "color": "#a77bff", "role_tag": "AI CREATOR"},
    "Agent Ginsberg": {"f0": 118.0, "reg": "LOW", "color": "#ff8844", "role_tag": "FBI AGENT"},
    "NORAD Guard": {"f0": 122.0, "reg": "LOW", "color": "#2cc89b", "role_tag": "SECURITY POST"},
    "NORAD Controller": {"f0": 125.0, "reg": "LOW", "color": "#2cc89b", "role_tag": "COMMAND POST"},
    "TV Anchor": {"f0": 128.0, "reg": "LOW", "color": "#c9a66b", "role_tag": "NEWS BROADCAST"},
    "Pan Am Clerk": {"f0": 195.0, "reg": "HIGH", "color": "#ff7ab8", "role_tag": "RESERVATIONS"},
    "Operator": {"f0": 198.0, "reg": "HIGH", "color": "#ff7ab8", "role_tag": "TELEPHONE OPERATOR"},
}

BOOK_CAST = {
    1: ["Capt. Jerry Lawson", "Lt. Steve Phelps", "SAC Duty Officer"],
    2: ["General Beringer", "John McKittrick", "Col. Joe Conley", "Lyle Watson", "Arthur Cabot"],
    3: ["David Lightman", "Mr. Liggett", "Jennifer Mack"],
    4: ["David Lightman", "Jennifer Mack"],
    5: ["David Lightman", "Jennifer Mack", "Pan Am Clerk"],
    6: ["David Lightman", "Operator"],
    7: ["Jim Sting", "Malvin", "David Lightman", "Jennifer Mack"],
    8: ["David Lightman", "Jennifer Mack", "WOPR (Joshua)", "TV Anchor"],
    9: ["David Lightman", "WOPR (Joshua)", "Jennifer Mack"],
    10: ["Col. Joe Conley", "John McKittrick", "Paul Richter", "General Beringer"],
    11: ["John McKittrick", "Paul Richter", "David Lightman", "TV Anchor"],
    12: ["David Lightman", "WOPR (Joshua)", "Agent Ginsberg"],
    13: ["John McKittrick", "David Lightman", "Paul Richter", "Col. Joe Conley"],
    14: ["David Lightman", "WOPR (Joshua)", "NORAD Guard"],
    15: ["David Lightman", "Jennifer Mack", "Operator"],
    16: ["Stephen Falken", "David Lightman", "Jennifer Mack"],
    17: ["Stephen Falken", "David Lightman", "Jennifer Mack"],
    18: ["General Beringer", "John McKittrick", "Col. Joe Conley", "Stephen Falken", "David Lightman"],
    19: ["General Beringer", "Stephen Falken", "John McKittrick", "Col. Joe Conley", "NORAD Controller"],
    20: ["John McKittrick", "Paul Richter", "General Beringer", "Stephen Falken", "David Lightman", "WOPR (Joshua)"],
    21: ["David Lightman", "WOPR (Joshua)", "Stephen Falken", "General Beringer", "John McKittrick", "Jennifer Mack"],
}

WHISPER_CORRECTIONS = [
    (r"trains game, the only winning mood is not too bad\.?", "A strange game. The only winning move is not to play."),
    (r"\bLyle forgot, Sanks\b", "Lyle, for God's sakes"),
    (r"\bWhy am I on a wedding\??", "Why am I out of line?"),
    (r"\bDefcar 5\b", "DEFCON 5"),
    (r"\bcrystal palace\b", "Crystal Palace"),
    (r"\bsack headquarters\b", "SAC Headquarters"),
    (r"\bSack Headquarters\b", "SAC Headquarters"),
    (r"\bmcketric\b", "McKittrick"),
    (r"\bmcketrick\b", "McKittrick"),
    (r"\bmckitrick\b", "McKittrick"),
    (r"\bwhopper\b", "WOPR"),
    (r"\bwopper\b", "WOPR"),
    (r"\bB\.O\.P\.R\.", "WOPR"),
    (r"\bfalcon\b", "Falken"),
    (r"\bfalkin\b", "Falken"),
    (r"\bbarringer\b", "Beringer"),
    (r"\bberringer\b", "Beringer"),
    (r"\bconnelly\b", "Conley"),
    (r"\bnorad\b", "NORAD"),
    (r"\bdefcon\b", "DEFCON"),
    (r"\bproto ?vision\b", "Protovision"),
    (r"\bprodivision\b", "Protovision"),
    (r"\bskybird\b", "Skybird"),
]


def clean_whisper_seg_text(txt):
    s = str(txt or "").strip()
    s = re.sub(r"[^\x00-\x7F]+", " ", s)
    for pat, rep in WHISPER_CORRECTIONS:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    s = re.sub(r",\s*\.", ".", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(re.findall(r"[A-Za-z]{2,}", s)) < 1:
        return ""
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    if s and s[-1] not in ".!?—":
        s += "."
    return s


def canonical_speaker_name(raw_who, book_num):
    w = str(raw_who or "").strip()
    wl = w.lower()
    if "jerry" in wl or "lawson" in wl:
        return "Capt. Jerry Lawson"
    if "steve" in wl or "phelps" in wl:
        return "Lt. Steve Phelps"
    if "beringer" in wl:
        return "General Beringer"
    if "mckittrick" in wl:
        return "John McKittrick"
    if "conley" in wl:
        return "Col. Joe Conley"
    if "watson" in wl:
        return "Lyle Watson"
    if "richter" in wl or "paul" in wl:
        return "Paul Richter"
    if "cabot" in wl:
        return "Arthur Cabot"
    if "david" in wl or "lightman" in wl:
        return "David Lightman"
    if "jennifer" in wl or "mack" in wl:
        return "Jennifer Mack"
    if "liggett" in wl:
        return "Mr. Liggett"
    if "jim" in wl or "sting" in wl:
        return "Jim Sting"
    if "malvin" in wl:
        return "Malvin"
    if "joshua" in wl or "wopr" in wl:
        return "WOPR (Joshua)"
    if "falken" in wl:
        return "Stephen Falken"
    if "ginsberg" in wl or "fbi" in wl:
        return "Agent Ginsberg"
    if "guard" in wl or "tour" in wl:
        return "NORAD Guard"
    if "sac" in wl or "speaker" in wl or "controller" in wl:
        return "SAC Duty Officer" if book_num == 1 else "NORAD Controller"
    return w if w in SPEAKER_PROFILES else (BOOK_CAST.get(book_num, ["David Lightman"])[0])


def infer_segment_speaker(seg_text, seg_f0, primary_speaker, book_num, prev_speaker, beat_text):
    """
    Determines which 1983 character spoke `seg_text` inside `book_num` using:
      1. Direct screenplay quote / vocative / lexical rules
      2. Vocal register (YIN f0 Hz) — e.g. Jennifer Mack (~205 Hz) vs David (~148 Hz) vs Falken (~114 Hz) vs Beringer (~104 Hz)
      3. Scene cast alternation (`BOOK_CAST[book_num]`)
    """
    tl = seg_text.lower()
    cast = BOOK_CAST.get(book_num, [primary_speaker])

    # 1. Explicit Book-specific & Vocative rules (who is addressing whom)
    if book_num == 1:
        if any(p in tl for p in ("turn your key", "launch order", "we have a launch", "turn your key, sir", "put your hand", "sorry, jerry", "authentication")):
            return "Lt. Steve Phelps"
        if any(p in tl for p in ("not until", "get some", "verify", "sack headquarters", "sac headquarters", "nobody", "phone", "talk to somebody", "sweet jesus", "hell is going")):
            return "Capt. Jerry Lawson"
        if any(p in tl for p in ("skybird", "dropkick", "red dash", "alpha", "romeo", "stand by")):
            return "SAC Duty Officer"

    if book_num == 2:
        if any(p in tl for p in ("good morning, mr. mckittrick", "two-man", "twenty percent", "missile commanders", "refused")):
            return "Col. Joe Conley"
        if any(p in tl for p in ("psych", "screen", "evaluation", "silo", "watson")):
            return "Lyle Watson"
        if any(p in tl for p in ("turn the key", "not the point", "general", "out of the loop", "wopr", "twenty-four hours", "tear those", "boxes", "men out")):
            return "John McKittrick"
        if any(p in tl for p in ("cabot", "washington", "president")):
            return "Arthur Cabot"
        if any(p in tl for p in ("bluff", "poker", "synapse", "hell", "damned", "plugged", "push the button", "mckittrick", "john")):
            return "General Beringer"

    if book_num == 3:
        if any(p in tl for p in ("asexual", "reproduce", "liggett", "who will tell", "miss mack", "lightman", "office")):
            return "Mr. Liggett"
        if any(p in tl for p in ("one", "grade", "fail", "summer school", "change it", "Really", "you can do")):
            return "Jennifer Mack"

    if book_num == 7:
        if any(p in tl for p in ("backdoor", "falken", "play a game", "design", "system", "protovision", "poker", "chess")):
            return "Jim Sting"
        if any(p in tl for p in ("malvin", "dork", "password", "pencil", "printout")):
            return "Malvin"
        if "jennifer" in tl or (seg_f0 and seg_f0 >= 182.0):
            return "Jennifer Mack"

    # Global character lexical signatures across the film
    if any(p in tl for p in ("shall we play a game", "greet", "professor falken", "hello, joshua", "strange game", "only winning move", "how about a nice game")):
        if "hello, joshua" in tl or "play global" in tl or "love to" in tl:
            return "David Lightman"
        return "WOPR (Joshua)"

    if any(p in tl for p in ("mr. mckittrick", "dr. mckittrick")) and "John McKittrick" in cast:
        return "Paul Richter" if "Paul Richter" in cast else "Col. Joe Conley"
    if any(p in tl for p in ("general", "sir, the", "crystal palace", "defcon")) and "Col. Joe Conley" in cast and "General Beringer" in cast:
        if any(q in tl for q in ("what the hell", "flush", "goddam", "plugged", "turn the", "cabot", "hold", "shoot")):
            return "General Beringer"
        return "Col. Joe Conley"
    if any(p in tl for p in ("dinosaur", "extinct", "nature", "general, you are listening", "not a circus", "trucks", "paths lead", "chess", "hume")) and "Stephen Falken" in cast:
        return "Stephen Falken"

    # 2. Check if segment closely matches the screenplay's primary `beat_text` (and `beat_text` isn't a stage direction)
    bt_toks = {norm(w) for w in beat_text.split() if len(norm(w)) > 2 and norm(w) not in STOPWORDS}
    seg_toks = {norm(w) for w in seg_text.split() if len(norm(w)) > 2 and norm(w) not in STOPWORDS}
    if bt_toks and len(bt_toks & seg_toks) >= max(1, min(2, len(bt_toks) // 2)):
        return primary_speaker

    # 3. Pitch / Register separation (especially Jennifer ~205 Hz vs David ~148 Hz vs Falken/Beringer ~108 Hz)
    if seg_f0 and seg_f0 > 0:
        if "Jennifer Mack" in cast and seg_f0 >= 180.0:
            return "Jennifer Mack"
        if "David Lightman" in cast and 136.0 <= seg_f0 < 180.0 and primary_speaker != "Jennifer Mack":
            if "Stephen Falken" in cast and seg_f0 < 126.0:
                return "Stephen Falken"
            return "David Lightman"
        if "General Beringer" in cast and seg_f0 <= 112.0:
            return "General Beringer"
        if "Stephen Falken" in cast and seg_f0 <= 122.0 and primary_speaker in ("David Lightman", "Jennifer Mack", "Stephen Falken"):
            return "Stephen Falken"

    # 4. Conversational turn alternation among the scene's cast
    if prev_speaker and len(cast) >= 2:
        if prev_speaker == primary_speaker:
            for alt in cast:
                if alt != primary_speaker:
                    return alt
        else:
            return primary_speaker

    return primary_speaker


def is_stage_direction(txt):
    tl = str(txt or "").strip().lower()
    return any(
        tl.startswith(p)
        for p in ("holding the ", "looking at ", "typing ", "he ", "she ", "david ", "jennifer ", "falken ", "mckittrick ")
    ) and ("recorder" in tl or "terminal" in tl or "screen" in tl)


def diarize_1983_turns(bk, bt_idx, bt, whisper_segs, a0, a1, dec, x_orig, estimate_phys_fn):
    """
    Decomposes the 1983 audio window `[a0, a1]` into speaker-attributed conversational turns (`turns_1983`)
    and word-level prosodic alignments (`words_1983`, `events_1983`):
      - Identifies WHO spoke every segment in the 1983 original (`speaker`, `speaker_color`, `role_tag`, `f0`, `lufs`)
      - Marks which turn is `★ THE LINE (FULCRUM)` vs `SETUP / PROMPT` vs `COUNTER / REACTION`
      - Ensures every audible word in `{beat_id}_orig.m4a` is represented on Lane A and attributed to its speaker!
    """
    book_num = int(bk.get("book") or 1)
    dur = max(0.5, a1 - a0)
    venv = dec["_venv"]
    p_venv = dec["_p_venv"]
    f0_clean = dec["_f0_clean"]
    hr_frame = dec["_hr_frame"]
    n_f = len(venv)
    onsets = dec["onsets"]

    primary_speaker = canonical_speaker_name(bt["who"], book_num)
    beat_text = str(bt.get("text") or "").strip()

    # Gather overlapping Whisper segments inside [a0, a1]
    ov_segs = [
        s for s in whisper_segs
        if float(s["end"]) > a0 + 0.12 and float(s["start"]) < a1 - 0.12
    ]

    raw_pieces = []
    for seg in ov_segs:
        s_s = max(0.0, float(seg["start"]) - a0)
        s_e = min(dur, float(seg["end"]) - a0)
        if s_e <= s_s + 0.15:
            continue
        cleaned = clean_whisper_seg_text(seg.get("text") or "")
        if not cleaned or len(cleaned) < 2:
            continue
        sub_sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", cleaned) if x.strip()]
        if len(sub_sents) >= 2 and (s_e - s_s) >= 2.2:
            tot_chars = sum(max(1, len(x)) for x in sub_sents)
            cur_t = s_s
            for sub in sub_sents:
                if len(re.findall(r"[A-Za-z]{2,}", sub)) < 1:
                    continue
                sp_d = (s_e - s_s) * (max(1, len(sub)) / tot_chars)
                raw_pieces.append({"s": cur_t, "e": cur_t + sp_d, "text": sub})
                cur_t += sp_d
        else:
            raw_pieces.append({"s": s_s, "e": s_e, "text": cleaned})

    # Fallback if no Whisper segments overlapped [a0, a1]
    if not raw_pieces:
        fallback_txt = clean_whisper_seg_text(bt.get("whisper") or beat_text)
        raw_pieces = [{"s": 0.15, "e": max(0.8, dur - 0.15), "text": fallback_txt}]

    # Attribute each piece to a 1983 speaker and measure its pitch f0 & LUFS
    attributed = []
    prev_sp = None
    for pc in raw_pieces:
        fa = max(0, min(n_f - 1, int(pc["s"] * FPS)))
        fb = max(fa + 1, min(n_f, int(pc["e"] * FPS) + 1))
        seg_f0s = f0_clean[fa:fb]
        voiced = seg_f0s[seg_f0s > 0]
        seg_f0 = round(float(np.median(voiced)), 1) if voiced.size else None

        sp_name = infer_segment_speaker(pc["text"], seg_f0, primary_speaker, book_num, prev_sp, beat_text)
        prev_sp = sp_name
        prof = SPEAKER_PROFILES.get(sp_name) or {"f0": 125.0, "reg": "LOW", "color": "#45b1ff", "role_tag": "CHARACTER"}
        eff_f0 = seg_f0 if (seg_f0 and 70.0 <= seg_f0 <= 265.0) else prof["f0"]

        s_i0 = max(0, int(pc["s"] * SR))
        s_i1 = min(len(x_orig), int(pc["e"] * SR))
        seg_lufs, _ = measure_lufs(x_orig[s_i0:s_i1]) if s_i1 - s_i0 > 256 else (dec["lufs"], 2.0)

        attributed.append({
            "speaker": sp_name,
            "speaker_color": prof["color"],
            "role_tag": prof["role_tag"],
            "s": round(pc["s"], 2),
            "e": round(pc["e"], 2),
            "text": pc["text"],
            "f0": round(eff_f0, 1),
            "reg": reg_of(eff_f0),
            "lufs": round(seg_lufs, 1),
        })

    # Merge consecutive pieces by the same speaker if gap < 0.65s and combined duration <= 7.0s
    turns = []
    for item in attributed:
        if (
            turns
            and turns[-1]["speaker"] == item["speaker"]
            and (item["s"] - turns[-1]["e"] <= 0.65)
            and (item["e"] - turns[-1]["s"] <= 7.0)
        ):
            turns[-1]["e"] = item["e"]
            turns[-1]["text"] = turns[-1]["text"].rstrip() + " " + item["text"].lstrip()
            turns[-1]["f0"] = round(0.5 * (turns[-1]["f0"] + item["f0"]), 1)
            turns[-1]["reg"] = reg_of(turns[-1]["f0"])
        else:
            turns.append(dict(item))

    # Identify which turn in `turns` is ★ THE LINE (FULCRUM)
    bt_toks = {norm(w) for w in beat_text.split() if len(norm(w)) > 2 and norm(w) not in STOPWORDS}
    best_t_idx = 0
    best_t_score = -1e9
    for idx_t, tr in enumerate(turns):
        tr_toks = {norm(w) for w in tr["text"].split() if len(norm(w)) > 2 and norm(w) not in STOPWORDS}
        ov = len(tr_toks & bt_toks)
        sp_match = 1.5 if tr["speaker"] == primary_speaker else 0.0
        len_score = min(1.2, len(tr["text"].split()) * 0.12)
        sc = ov * 2.0 + sp_match + len_score
        if sc > best_t_score:
            best_t_score = sc
            best_t_idx = idx_t

    # If the screenplay's `beat_text` is genuine spoken dialogue (not a stage direction) and the matched
    # Whisper turn had ASR corruption or missed words, restore the clean screenplay phrasing on the Fulcrum Turn!
    if beat_text and not is_stage_direction(beat_text):
        f_tr = turns[best_t_idx]
        f_toks = {norm(w) for w in f_tr["text"].split() if len(norm(w)) > 2 and norm(w) not in STOPWORDS}
        if len(f_toks & bt_toks) >= 1 and len(beat_text.split()) <= 20:
            f_tr["text"] = clean_whisper_seg_text(beat_text)
            f_tr["speaker"] = primary_speaker
            prof_p = SPEAKER_PROFILES.get(primary_speaker) or {"color": "#ff5538", "role_tag": "CHARACTER"}
            f_tr["speaker_color"] = prof_p["color"]

    for idx_t, tr in enumerate(turns):
        tr["turn_num"] = idx_t + 1
        tr["dur"] = round(max(0.25, tr["e"] - tr["s"]), 2)
        tr["is_fulcrum"] = idx_t == best_t_idx
        if idx_t == best_t_idx:
            tr["role"] = "★ THE LINE (FULCRUM)"
        elif idx_t < best_t_idx:
            tr["role"] = "SETUP / PROMPT"
        else:
            tr["role"] = "COUNTER / REACTION"

    # Now align words across all `turns` so Lane A displays every speaker's words with speaker attribution!
    words_out = []
    raw_stresses = []
    for tr in turns:
        t_ws = [w for w in tr["text"].split() if norm(w)]
        if not t_ws:
            continue
        phys_l = [estimate_phys_fn(w) for w in t_ws]
        pauses_l = [
            0.22 if w.endswith((".", "!", "?", "—")) else (0.10 if w.endswith((",", ";", ":")) else 0.02)
            for idx_w, w in enumerate(t_ws)
        ]
        if pauses_l:
            pauses_l[-1] = 0.0
        tot_need = sum(p["intrinsic_dur"] for p in phys_l) + sum(pauses_l) or 1.0
        span = max(0.25, tr["e"] - tr["s"])
        scale = span / tot_need
        cur_t = tr["s"]
        for w_str, phys, p_after in zip(t_ws, phys_l, pauses_l):
            w_d = max(0.11, phys["intrinsic_dur"] * scale)
            w_s = max(0.0, min(dur - 0.10, cur_t))
            w_e = max(w_s + 0.10, min(dur, cur_t + w_d))
            cur_t += w_d + p_after * scale

            near_on = [o for o in onsets if abs(o - w_s) <= 0.08]
            ts = max(0.0, (near_on[0] if near_on else w_s) - phys["pre_roll"] * 0.4)
            te = min(dur, w_e + phys["tail_pad"] * 0.5)

            fa = max(0, min(n_f - 1, int(w_s * FPS)))
            fb = max(fa + 1, min(n_f, int(w_e * FPS) + 1))
            w_venv = venv[fa:fb]
            w_pvenv = p_venv[fa:fb]
            w_f0s = f0_clean[fa:fb]
            w_voiced = w_f0s[w_f0s > 0]
            w_f0 = round(float(np.median(w_voiced)), 1) if w_voiced.size else tr["f0"]
            w_hr = round(float(np.mean(hr_frame[fa:fb])), 2) if fb > fa else 0.65

            s_i0 = max(0, int(ts * SR))
            s_i1 = min(len(x_orig), int(te * SR))
            w_lufs, _ = measure_lufs(x_orig[s_i0:s_i1]) if s_i1 - s_i0 > 256 else (tr["lufs"], 2.0)

            e_score = float(np.max(w_venv)) / (float(np.mean(venv)) + 1e-6) if w_venv.size else 1.0
            p_score = (w_f0 / max(80.0, dec["f0_median"])) if w_f0 else 0.95
            raw_st = 0.55 * e_score + 0.30 * p_score + 0.15 * (phys["acoustic_mass"] / 0.6)
            if tr["is_fulcrum"]:
                raw_st += 0.18
            raw_stresses.append(raw_st)

            words_out.append({
                "w": w_str,
                "speaker": tr["speaker"],
                "speaker_color": tr["speaker_color"],
                "turn_num": tr["turn_num"],
                "turn_role": tr["role"],
                "is_fulcrum": tr["is_fulcrum"],
                "s": round(w_s, 2),
                "e": round(w_e, 2),
                "ts": round(ts, 3),
                "te": round(te, 3),
                "t0": round(w_s, 2),
                "t1": round(w_e, 2),
                "dur": round(w_e - w_s, 3),
                "f0": w_f0,
                "lufs": w_lufs,
                "hp_ratio": w_hr,
                "mass": round(phys["acoustic_mass"] * min(1.5, max(0.6, e_score * 0.7)), 3),
                "syllables": phys["syllables"],
                "energy": round(min(1.0, e_score / 2.2), 2),
                "sibilance": round(min(1.0, float(np.max(w_pvenv)) / (float(np.percentile(p_venv, 92)) + 1e-6)), 2) if w_pvenv.size else 0.25,
                "band": phys["dominant_band"],
            })

    st_arr = np.array(raw_stresses, dtype=np.float32)
    st_mean = float(np.mean(st_arr)) if st_arr.size else 1.0
    st_std = float(np.std(st_arr)) if st_arr.size > 1 and np.std(st_arr) > 1e-4 else 0.35

    events = []
    for idx, w in enumerate(words_out):
        z_st = round(float(np.clip((raw_stresses[idx] - st_mean) / st_std, -1.5, 2.4)), 2)
        w["st"] = z_st
        is_content = norm(w["w"]) not in STOPWORDS and len(norm(w["w"])) > 2
        if (is_content and z_st >= 0.15) or z_st >= 0.65 or w["w"].endswith((".", "!", "?")):
            w["gr"] = "A"
        elif is_content or z_st >= -0.35:
            w["gr"] = "B"
        else:
            w["gr"] = "C"

        if z_st >= 0.75:
            events.append({"t": w["s"], "dur": w["dur"], "type": "ACCENT", "word": w["w"], "speaker": w["speaker"]})
        if w["f0"] and w["f0"] >= dec["f0_median"] * 1.18:
            events.append({"t": w["s"], "dur": w["dur"], "type": "PITCH_HIGH", "word": w["w"], "speaker": w["speaker"]})
        if w["sibilance"] >= 0.78:
            events.append({"t": w["s"], "dur": 0.08, "type": "PLOSIVE", "word": w["w"], "speaker": w["speaker"]})

        if idx + 1 < len(words_out):
            g_s = w["e"]
            g_e = words_out[idx + 1]["s"]
            g_dur = round(g_e - g_s, 2)
            if g_dur >= 0.20:
                events.append({"t": g_s, "dur": g_dur, "type": "PAUSE", "word": w["w"], "speaker": w["speaker"]})
                fa = max(0, min(n_f - 1, int(g_s * FPS)))
                fb = max(fa + 1, min(n_f, int(g_e * FPS)))
                if g_dur >= 0.35 and fb > fa and float(np.mean(p_venv[fa:fb])) > float(np.percentile(p_venv, 35)):
                    events.append({"t": round(g_s + 0.05, 2), "dur": round(min(0.32, g_dur * 0.6), 2), "type": "BREATH", "word": w["w"], "speaker": w["speaker"]})

    events.sort(key=lambda e: e["t"])
    return turns, words_out, events


# -----------------------------------------------------------------------------
# Tarantino "The Line" (Pars Pro Toto) Unbroken Archival Sentence Corpus
# -----------------------------------------------------------------------------
BAN_DOMAIN_WORDS = {
    "cow", "cows", "cattle", "sheep", "pig", "pigs", "hog", "hogs", "chicken",
    "chickens", "turkey", "corn", "wheat", "crop", "crops", "soil", "plow",
    "tractor", "barn", "milk", "cheese", "butter", "baking", "kitchen", "recipe",
    "lettuce", "potato", "tomato", "pasture", "manure", "fertilizer", "beef",
    "pork", "poultry", "silage", "hay", "alfalfa", "ranch", "orchard", "sewing",
    "dress", "skirt", "shoes", "grocery", "supermarket", "laundry", "soap",
    "tooth", "teeth", "dentist", "cereal", "breakfast", "dinner", "supper",
    "dog", "dogs", "cat", "cats", "pet", "pets", "puppy", "kitten", "football",
    "baseball", "basketball", "coach", "touchdown", "quarterback", "christmas",
    "santa", "easter", "birthday", "wedding", "bride", "groom", "grandma",
    "grandpa", "bedtime", "pillow", "blanket", "wife", "husband", "mother",
    "father", "mom", "dad", "betty", "jimmy", "billy", "johnny", "bobby",
    "tommy", "mary", "sally", "tippy", "horse", "horses", "wagon", "wagons",
    "cowboy", "tomahawk", "axe", "prayer", "suit", "dance", "dancing", "party",
}

FULCRUM_THESIS_KEYWORDS = {
    "turn your key": ("command authority launch key", "Refusal to turn the nuclear launch key without human verification"),
    "no response": ("silence radar communication", "Dead communication channel across the missile command line"),
    "tear": ("tear out machine automation", "Replacing hesitant human operators with an unblinking machine"),
    "loop": ("take men out of the loop", "Removing human judgment from the nuclear command chain"),
    "synapse": ("brain machine electrical", "Not trusting a handful of chemical synapses to fire on command"),
    "bluff": ("bluff poker nerve button", "Testing who has the nerve to push the button when the clock runs out"),
    "grade": ("change record computer", "Quietly rewriting official records from a bedroom terminal"),
    "protovision": ("game list discovery", "Stumbling onto a hidden military simulation disguised as games"),
    "falken": ("creator scientist dead", "Tracing the ghost of the vanished AI architect Stephen Falken"),
    "chess": ("play game strategy", "Challenging human arrogance with a game that requires thought"),
    "global thermonuclear": ("thermonuclear war game", "Choosing Global Thermonuclear War over a harmless game of chess"),
    "backdoor": ("password key secret", "Finding the creator's personal backdoor into the war computer"),
    "joshua": ("hello voice waking up", "The machine awakes and recognizes its creator's secret name"),
    "las vegas": ("target city destruction", "Selecting real American cities as opening salvo targets"),
    "bomber": ("perimeter alert sky", "Soviet bombers probing the air defense perimeter"),
    "simulation": ("illusion real false", "Mistaking a computer hallucination for an actual military attack"),
    "real": ("what is real illusion", "Asking whether the difference between simulation and reality matters"),
    "arrest": ("fbi capture interrogation", "Locking the one witness who knows the truth inside NORAD"),
    "primary goal": ("win game objective", "The machine's relentless drive to complete its programmed objective"),
    "wopr": ("machine brain intelligence", "A war computer that runs every catastrophe twenty-four hours a day"),
    "learn": ("learn mistake child", "Can an artificial mind learn what it was never explicitly taught?"),
    "dinosaur": ("extinction nature history", "Humanity facing the same extinction clock as the dinosaurs"),
    "extinct": ("extinction survival", "Accepting extinction rather than fighting the inevitable"),
    "ferry": ("run hurry time", "Racing the closing perimeter before the mountain seals shut"),
    "defcon": ("alert defense warning", "Sealing Cheyenne Mountain as the world steps to DEFCON 1"),
    "submarine": ("ocean missile launch", "Submarine missiles rising from the sea on automated telemetry"),
    "countdown": ("clock seconds zero", "Counting down the final seconds before retaliatory launch"),
    "wait": ("hold fire wait impact", "Holding fire past zero hour to see if the bombs are real"),
    "nobody here": ("alive survived intact", "Confirming the bases are still standing—there was no attack"),
    "launch code": ("code decrypt lock", "The machine brute-forcing the Ten-Digit Launch Code on its own"),
    "tic-tac-toe": ("draw stalemate zero", "Forcing the machine to experience a game where neither side can win"),
    "strange game": ("no winner peace", "The only winning move is not to play"),
}


def load_clip_wordmap():
    """Loads the 4,000-word × 512-D OpenAI CLIP text embedding matrix from lab/norse/wordmap.{json,bin}."""
    wm_json = os.path.join(LAB, "norse", "wordmap.json")
    wm_bin = os.path.join(LAB, "norse", "wordmap.bin")
    if not (os.path.exists(wm_json) and os.path.exists(wm_bin)):
        return {}, np.zeros((1, 512), dtype=np.float32)
    meta = json.load(open(wm_json))
    words = meta["words"]
    dim = int(meta["dim"])
    raw = np.fromfile(wm_bin, dtype=np.int8, count=len(words) * dim).reshape(len(words), dim).astype(np.float32)
    raw = raw - raw.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(raw, axis=1, keepdims=True) + 1e-8
    vecs = raw / norms
    w2idx = {w: i for i, w in enumerate(words)}
    return w2idx, vecs


def sentence_clip_vec(text, w2idx, vecs, get_synonym_tokens=None):
    """Computes a L2-normalized 512-D CLIP semantic vector for a sentence or thesis query."""
    toks = [norm(w) for w in re.findall(r"[A-Za-z']+", text)]
    idxs = []
    for t in toks:
        if t in STOPWORDS or len(t) <= 2:
            continue
        if t in w2idx:
            idxs.append(w2idx[t])
        elif get_synonym_tokens is not None:
            for syn in get_synonym_tokens(t, t):
                if syn in w2idx:
                    idxs.append(w2idx[syn])
                    break
    if not idxs:
        for t in toks:
            if t in w2idx:
                idxs.append(w2idx[t])
    if not idxs:
        return np.zeros(vecs.shape[1], dtype=np.float32)
    v = vecs[idxs].mean(axis=0)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-8 else v


def is_clean_complete_sentence(text):
    """
    Verifies that `text` is a complete, grammatical, unbroken human sentence
    suitable for Tarantino's 'The Line' (Pars Pro Toto):
      - Starts with a capital letter
      - Ends with terminal punctuation (., !, ?), not ',.'
      - 4 to 22 words long
      - Contains no agricultural/food/domestic/pet/sports/family ban words
    """
    s = str(text or "").strip()
    if not s or len(s) < 15:
        return False
    if not s[0].isupper():
        return False
    if s[-1] not in ".!?" or s.endswith(",.") or s.endswith(", ."):
        return False
    words = s.split()
    if not (4 <= len(words) <= 22):
        return False
    norm_ws = [re.sub(r"'s$", "", norm(w)) for w in words if norm(w)]
    if not norm_ws:
        return False
    if any(w in BAN_DOMAIN_WORDS or stem(w) in BAN_DOMAIN_WORDS for w in norm_ws):
        return False
    last_w = norm_ws[-1]
    if last_w in {"and", "or", "but", "the", "a", "an", "to", "of", "in", "for", "with", "that", "which", "because", "if", "is", "are", "was", "were"}:
        return False
    return True


def build_local_archival_audio_index(get_synonym_tokens=None):
    """
    Builds the Tarantino 'The Line' Corpus of 100% complete, unbroken, single-speaker
    archival sentences (`1.55s` to `6.0s`, 0 internal cuts) across:
      1. `lab/clips/*.mp4` + `lab/words.json` (with local video & audio, using spoken_odyssey.py pause rules)
      2. `lab/norse/program.json` (both `stages -> scenes -> beats` AND `scenes -> lines` call/ans)
      3. `lab/odyssey/found.json` + `lab/odyssey/found-audio/spoken/*.m4a` (Whisper-verified spoken sentences)
    """
    census_path = os.path.join(LAB, "cache", "sound-census.json")
    census = json.load(open(census_path))["clips"] if os.path.exists(census_path) else {}
    words_db = json.load(open(os.path.join(LAB, "words.json")))
    corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
    clips_dir = os.path.join(LAB, "clips")
    local_mp4s = {f[:-4] for f in os.listdir(clips_dir) if f.endswith(".mp4") and not f.startswith("wg_")}

    w2idx, clip_vecs = load_clip_wordmap()
    sentences = []
    seen_texts = set()

    def add_sentence_entry(entry):
        txt_key = re.sub(r"\s+", " ", entry["spoken"].strip().lower())
        if txt_key in seen_texts:
            return
        seen_texts.add(txt_key)
        toks = [norm(w) for w in entry["spoken"].split() if norm(w)]
        c_toks = {t for t in toks if t not in STOPWORDS and len(t) > 2}
        c_stems = {stem(t) for t in c_toks}
        entry["tokens"] = list(c_toks)
        entry["stems"] = c_stems
        entry["word_count"] = len(toks)
        entry["clip_vec"] = sentence_clip_vec(entry["spoken"], w2idx, clip_vecs, get_synonym_tokens)
        sentences.append(entry)

    # 1. Extract complete grammatical sentences from local MP4 clips (`lab/clips/*.mp4`)
    for cid in sorted(local_mp4s):
        ws = words_db.get(cid)
        if not ws:
            continue
        c_meta = corpus.get(cid) or {}
        sc = census.get(cid) or {}
        if sc.get("kind") in ("silence", "none"):
            continue
        lufs = float(sc.get("lufs") or -23.0)
        kind = sc.get("kind") or "speech"
        cent = float(sc.get("centroid") or 1280.0)
        p_speech = float((sc.get("p") or {}).get("speech", 0.82))
        p_music = float((sc.get("p") or {}).get("music", 0.12))
        est_f0 = round(max(85.0, min(225.0, 78.0 + (cent - 600.0) * 0.055)), 1)
        reg = reg_of(est_f0)
        mp4_path = os.path.join(clips_dir, cid + ".mp4")
        rel_url = f"clips/{cid}.mp4"
        title = c_meta.get("sourceTitle") or "Archival Broadcast"
        year = c_meta.get("sourceYear")
        thumb = f"thumbs/{cid}.jpg"

        cur = []
        for idx, item in enumerate(ws):
            w_raw = str(item[0]).strip()
            t_w = float(item[1])
            if not cur:
                prev_ok = (
                    idx == 0
                    or str(ws[idx - 1][0]).strip().endswith((".", "!", "?"))
                    or (t_w - float(ws[idx - 1][1]) >= 0.42)
                )
                if not (prev_ok and w_raw and w_raw[0].isupper()):
                    continue
            cur.append((w_raw, t_w, idx))
            next_onset = float(ws[idx + 1][1]) if idx + 1 < len(ws) else (t_w + 0.55)
            pause_after = next_onset - t_w
            is_end = w_raw.endswith((".", "!", "?")) or (pause_after >= 0.48 and len(cur) >= 5)
            if is_end:
                s_t0 = cur[0][1]
                s_t1 = cur[-1][1] + min(0.58, max(0.32, pause_after - 0.04))
                s_dur = round(s_t1 - s_t0, 2)
                s_txt = " ".join(x[0] for x in cur)
                if s_txt and s_txt[-1] not in ".!?":
                    s_txt += "."
                if 1.55 <= s_dur <= 6.2 and is_clean_complete_sentence(s_txt):
                    add_sentence_entry({
                        "source_type": "clip_mp4",
                        "has_local_video": True,
                        "id": cid,
                        "audio_path": mp4_path,
                        "audio_url": rel_url,
                        "video_url": rel_url,
                        "thumb": thumb,
                        "title": title,
                        "year": year,
                        "spoken": s_txt,
                        "t0": round(s_t0, 2),
                        "t1": round(s_t1, 2),
                        "ts": round(max(0.0, s_t0 - 0.08), 3),
                        "te": round(s_t1 + 0.14, 3),
                        "clip_t0": round(s_t0, 2),
                        "clip_t1": round(s_t1, 2),
                        "dur": s_dur,
                        "lufs": round(lufs, 1),
                        "gain_db": round(float(np.clip(-21.0 - lufs, -12.0, 16.0)), 1),
                        "kind": kind,
                        "p_speech": round(p_speech, 2),
                        "p_music": round(p_music, 2),
                        "centroid": round(cent, 0),
                        "f0": est_f0,
                        "reg": reg,
                    })
                cur = []

    # 2. Index unbroken archival calls & answers from `lab/norse/program.json`
    norse_prog_path = os.path.join(LAB, "norse", "program.json")
    if os.path.exists(norse_prog_path):
        norse_prog = json.load(open(norse_prog_path))
        for st in norse_prog.get("stages") or []:
            for sc in st.get("scenes") or []:
                for b in sc.get("beats") or []:
                    call = b.get("call") or {}
                    a_rel = (b.get("audio") or {}).get("call") or ""
                    a_path = os.path.join(LAB, "norse", a_rel)
                    if not (a_rel and os.path.exists(a_path)):
                        continue
                    txt = str(call.get("text") or "").strip()
                    if txt and txt[0].islower():
                        txt = txt[0].upper() + txt[1:]
                    if txt and txt[-1] not in ".!?":
                        txt += "."
                    if not is_clean_complete_sentence(txt):
                        continue
                    cid = str(call.get("cid") or "")
                    c_meta = corpus.get(cid) or {}
                    sc_c = census.get(cid) or {}
                    lufs_c = float(sc_c.get("lufs") or -21.5)
                    cent_c = float(sc_c.get("centroid") or 1310.0)
                    f0_c = round(max(85.0, min(225.0, 80.0 + (cent_c - 650.0) * 0.055)), 1)
                    c_t0 = float(call.get("t0") or 0.0)
                    c_t1 = float(call.get("t1") or 3.0)
                    dur_c = round(max(1.6, min(5.8, c_t1 - c_t0 + 0.35)), 2)
                    add_sentence_entry({
                        "source_type": "norse_m4a",
                        "has_local_video": cid in local_mp4s,
                        "id": cid or f"norse_{b.get('idx', 0)}",
                        "audio_path": a_path,
                        "audio_url": f"norse/{a_rel}",
                        "video_url": f"clips/{cid}.mp4" if cid in local_mp4s else (call.get("video") or c_meta.get("videoUrl") or ""),
                        "thumb": f"thumbs/{cid}.jpg" if os.path.exists(os.path.join(LAB, "thumbs", f"{cid}.jpg")) else (call.get("thumb") or ""),
                        "title": call.get("title") or c_meta.get("sourceTitle") or "Archival Broadcast",
                        "year": call.get("year") or c_meta.get("sourceYear"),
                        "spoken": txt,
                        "t0": 0.0,
                        "t1": dur_c,
                        "ts": 0.0,
                        "te": dur_c,
                        "clip_t0": round(c_t0, 2),
                        "clip_t1": round(c_t1, 2),
                        "dur": dur_c,
                        "lufs": round(lufs_c, 1),
                        "gain_db": round(float(np.clip(-21.0 - lufs_c, -12.0, 16.0)), 1),
                        "kind": sc_c.get("kind") or "speech",
                        "p_speech": 0.88,
                        "p_music": 0.08,
                        "centroid": round(cent_c, 0),
                        "f0": f0_c,
                        "reg": reg_of(f0_c),
                    })
        # Also index `scenes -> lines` (`ans` and `call` slices inside `norse/audio/scene-*.m4a`)
        for sc in norse_prog.get("scenes") or []:
            sc_audio_rel = sc.get("audio") or ""
            sc_audio_path = os.path.join(LAB, "norse", sc_audio_rel)
            if not (sc_audio_rel and os.path.exists(sc_audio_path)):
                continue
            for ln in sc.get("lines") or []:
                for part_key, t0_key, t1_key in (("ans", "aat", "aend"), ("call", "cat", "cend")):
                    part = ln.get(part_key) or {}
                    p_t0 = float(ln.get(t0_key) or 0.0)
                    p_t1 = float(ln.get(t1_key) or 0.0)
                    p_dur = round(p_t1 - p_t0, 2)
                    if not (1.55 <= p_dur <= 6.0):
                        continue
                    txt = str(part.get("said") or "").strip()
                    if txt and txt[0].islower():
                        txt = txt[0].upper() + txt[1:]
                    if txt and txt[-1] not in ".!?":
                        txt += "."
                    if not is_clean_complete_sentence(txt):
                        continue
                    cid = str(part.get("id") or "")
                    c_meta = corpus.get(cid) or {}
                    sc_c = census.get(cid) or {}
                    lufs_c = float(sc_c.get("lufs") or -21.0)
                    cent_c = float(sc_c.get("centroid") or 1315.0)
                    f0_c = round(max(85.0, min(225.0, 80.0 + (cent_c - 650.0) * 0.055)), 1)
                    add_sentence_entry({
                        "source_type": "norse_scene_m4a",
                        "has_local_video": cid in local_mp4s,
                        "id": cid or f"norse_sc_{sc.get('n', 0)}",
                        "audio_path": sc_audio_path,
                        "audio_url": f"norse/{sc_audio_rel}",
                        "video_url": f"clips/{cid}.mp4" if cid in local_mp4s else (part.get("video") or c_meta.get("videoUrl") or ""),
                        "thumb": f"thumbs/{cid}.jpg" if os.path.exists(os.path.join(LAB, "thumbs", f"{cid}.jpg")) else (part.get("thumb") or ""),
                        "title": part.get("title") or c_meta.get("sourceTitle") or "Archival Broadcast",
                        "year": part.get("year") or c_meta.get("sourceYear"),
                        "spoken": txt,
                        "t0": round(p_t0, 2),
                        "t1": round(p_t1, 2),
                        "ts": round(p_t0, 3),
                        "te": round(p_t1, 3),
                        "clip_t0": float(part.get("t0") or 0.0),
                        "clip_t1": float(part.get("t1") or p_dur),
                        "dur": p_dur,
                        "lufs": round(lufs_c, 1),
                        "gain_db": round(float(np.clip(-21.0 - lufs_c, -12.0, 16.0)), 1),
                        "kind": sc_c.get("kind") or "speech",
                        "p_speech": 0.88,
                        "p_music": 0.08,
                        "centroid": round(cent_c, 0),
                        "f0": f0_c,
                        "reg": reg_of(f0_c),
                    })

    # 3. Index Whisper-verified unbroken spoken sentences from `lab/odyssey/found-audio/spoken/*.m4a`
    od_found_path = os.path.join(LAB, "odyssey", "found.json")
    if os.path.exists(od_found_path):
        od_found = json.load(open(od_found_path))
        od_clips = od_found.get("clips") or {}
        for sc_id, lines in (od_found.get("scenes") or {}).items():
            sp_json = os.path.join(LAB, "odyssey", "found-audio", "spoken", f"{sc_id}.json")
            sp_m4a = os.path.join(LAB, "odyssey", "found-audio", "spoken", f"{sc_id}.m4a")
            if not (os.path.exists(sp_json) and os.path.exists(sp_m4a)):
                continue
            ev_list = json.load(open(sp_json)).get("ev") or []
            for ev in ev_list:
                if ev.get("ours") or not ev.get("id"):
                    continue
                li, fi = ev.get("li", -1), ev.get("fi", -1)
                if not (0 <= li < len(lines)):
                    continue
                frags = ((lines[li].get("modes") or {}).get("spoken") or {}).get("frags") or []
                if not (0 <= fi < len(frags)):
                    continue
                frag = frags[fi]
                said = str(frag.get("words") or "").strip()
                if said and said[0].islower():
                    said = said[0].upper() + said[1:]
                if said and said[-1] not in ".!?":
                    said += "."
                at_s, end_s = float(ev["at"]), float(ev["end"])
                dur_s = round(end_s - at_s, 2)
                if not (1.6 <= dur_s <= 5.8 and is_clean_complete_sentence(said)):
                    continue
                cid = ev["id"]
                c_info = od_clips.get(cid) or corpus.get(cid) or {}
                sc_c = census.get(cid) or {}
                lufs_c = float(sc_c.get("lufs") or -21.0)
                cent_c = float(sc_c.get("centroid") or 1320.0)
                f0_c = round(max(85.0, min(225.0, 80.0 + (cent_c - 650.0) * 0.055)), 1)
                add_sentence_entry({
                    "source_type": "odyssey_spoken_m4a",
                    "has_local_video": cid in local_mp4s,
                    "id": cid,
                    "audio_path": sp_m4a,
                    "audio_url": f"odyssey/found-audio/spoken/{sc_id}.m4a",
                    "video_url": f"clips/{cid}.mp4" if cid in local_mp4s else (c_info.get("video") or c_info.get("videoUrl") or ""),
                    "thumb": f"thumbs/{cid}.jpg" if os.path.exists(os.path.join(LAB, "thumbs", f"{cid}.jpg")) else (c_info.get("thumb") or c_info.get("thumbnailUrl") or ""),
                    "title": c_info.get("title") or c_info.get("sourceTitle") or "Archival Broadcast",
                    "year": c_info.get("year") or c_info.get("sourceYear"),
                    "spoken": said,
                    "t0": round(at_s, 2),
                    "t1": round(end_s, 2),
                    "ts": round(at_s, 3),
                    "te": round(end_s, 3),
                    "clip_t0": float(frag.get("t0") or 0.0),
                    "clip_t1": float(frag.get("t1") or dur_s),
                    "dur": dur_s,
                    "lufs": round(lufs_c, 1),
                    "gain_db": round(float(np.clip(-21.0 - lufs_c, -12.0, 16.0)), 1),
                    "kind": sc_c.get("kind") or "speech",
                    "p_speech": round(float((sc_c.get("p") or {}).get("speech", 0.85)), 2),
                    "p_music": round(float((sc_c.get("p") or {}).get("music", 0.10)), 2),
                    "centroid": round(cent_c, 0),
                    "f0": f0_c,
                    "reg": reg_of(f0_c),
                })

    print(
        f"Indexed Tarantino 'The Line' Unbroken Corpus: {len(sentences)} complete single-speaker sentences "
        f"({sum(1 for s in sentences if s['has_local_video'])} with local MP4 video)."
    )
    return sentences, census, w2idx, clip_vecs


def classify_tarantino_beat(bk, bt_idx, bt):
    """
    Phase 1 (Anchor Identification) & Phase 4 (Punctuation Matching):
    Identifies which beats in each 5-beat scene are '★ THE FULCRUM LINE' vs. connective setup/escalation,
    and formulates the Pars Pro Toto thesis ('what we need to say to carry the scene').
    """
    txt_low = bt["text"].lower()
    cue_low = (bt.get("foley_cue") or "").lower()
    combined = txt_low + " " + cue_low

    # Determine Fulcrum Thesis & Semantic Query
    matched_query = ""
    matched_thesis = ""
    for kw, (q_words, thesis_desc) in FULCRUM_THESIS_KEYWORDS.items():
        if kw in combined:
            matched_query = q_words
            matched_thesis = thesis_desc
            break
    if not matched_thesis:
        matched_query = bt["text"]
        matched_thesis = f"{bt['who']} shifts the scene's center of gravity ({bt.get('foley_label') or 'dramatic turn'})"

    # In each 5-beat scene (indices 0..4), Beat 2 (middle turn) and Beat 4 (scene-closing line) are the primary Fulcrum anchors
    is_fulcrum = bt_idx in (2, 4) or any(
        k in txt_low for k in ("turn your key", "only winning move", "global thermonuclear", "take the men out", "what is the primary goal", "nobody here")
    )
    role_map = {
        0: "1 · SCENE ENTRY",
        1: "2 · ESCALATION",
        2: "★ 3 · THE FULCRUM LINE",
        3: "4 · COUNTER-BEAT",
        4: "★ 5 · THE LINE (SCENE PAYOFF)",
    }
    beat_role = role_map.get(bt_idx, "★ THE FULCRUM LINE" if is_fulcrum else "SCENE BEAT")
    if is_fulcrum and not beat_role.startswith("★"):
        beat_role = "★ THE FULCRUM LINE"

    framing_optics = (
        "TIGHT ISOLATED SINGLE FRAME (1:1 Fulcrum Lock)"
        if is_fulcrum
        else "SCENE COVERAGE (Contextual Cut)"
    )

    return {
        "is_fulcrum": is_fulcrum,
        "beat_role": beat_role,
        "fulcrum_thesis": matched_thesis,
        "semantic_query": matched_query + " " + bt["text"],
        "framing_optics": framing_optics,
    }


# -----------------------------------------------------------------------------
# Clean Room-Air Synthesis & Unbroken Sentence Extraction (spoken_odyssey.py)
# -----------------------------------------------------------------------------
_audio_file_cache = {}
_pink_rng = np.random.default_rng(1983)


def make_pink_room_air(n_samples, lufs_db=-54.0):
    """
    Synthesizes a whisper-quiet, continuous optical room-tone floor (-54 LUFS)
    with zero voices or harmonic bleed from the 1983 speaker.
    """
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float32)
    w = _pink_rng.standard_normal(n_samples).astype(np.float32)
    f = np.fft.rfftfreq(n_samples, 1.0 / SR)
    f[0] = 1.0
    spec = np.fft.rfft(w) / np.sqrt(f)
    spec[(f < 90) | (f > 4200)] = 0.0
    p = np.fft.irfft(spec, n=n_samples).astype(np.float32)
    p /= float(np.sqrt(np.mean(p * p)) + 1e-9)
    return p * float(10.0 ** (lufs_db / 20.0))


def load_audio_22k(path):
    if path in _audio_file_cache:
        return _audio_file_cache[path]
    if not path or not os.path.exists(path):
        return None
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True,
    ).stdout
    arr = np.frombuffer(raw, dtype=np.float32).copy()
    if len(_audio_file_cache) > 96:
        _audio_file_cache.pop(next(iter(_audio_file_cache)))
    _audio_file_cache[path] = arr
    return arr


def extract_unbroken_sentence_audio(item, target_lufs=-21.0):
    """
    Extracts a complete, unbroken archival sentence `[ts, te]` from `item["audio_path"]`
    without ANY internal cuts or time-truncation:
      1. Opens in the speaker's own room (`ts`) and rings out after the final word (`te`)
      2. Gentle spectral noise floor subtraction (`spoken_odyssey.py` / `render_found.py`)
      3. Optical bandpass (`85–6200 Hz`) so all archival decades share one clean acoustic room
      4. BS.1770-4 K-weighted loudness normalization to `-21.0 LUFS`
      5. Smooth `35ms` cosine entrance and `65ms` breath release tail
    """
    a = load_audio_22k(item.get("audio_path"))
    if a is None or len(a) < SR // 4:
        return np.zeros(int(2.0 * SR), dtype=np.float32)

    ts = max(0.0, float(item.get("ts", item.get("t0", 0.0))))
    te = min(len(a) / SR, float(item.get("te", item.get("t1", ts + 2.5))))
    if te <= ts + 0.5:
        te = min(len(a) / SR, ts + 2.2)

    s_idx = max(0, int(ts * SR))
    e_idx = min(len(a), int(te * SR))
    x = a[s_idx:e_idx].astype(np.float32).copy()
    if len(x) < 512:
        return np.zeros(int(2.0 * SR), dtype=np.float32)

    # For raw MP4 clips, subtract stationary room hiss; pre-rendered odyssey/norse m4a are already mastered
    if item.get("source_type") == "clip_mp4":
        ctx = a[max(0, s_idx - SR):min(len(a), e_idx + SR)]
        if len(ctx) >= 1024:
            _, _, Zc = stft(ctx, fs=SR, nperseg=512, noverlap=384)
            pw_c = np.abs(Zc) ** 2
            fe = pw_c.sum(0)
            q_floor = pw_c[:, fe <= np.percentile(fe, 18)].mean(1, keepdims=True)
            _, _, Zx = stft(x, fs=SR, nperseg=512, noverlap=384)
            pw_x = np.abs(Zx) ** 2
            g_sub = np.maximum(1.0 - 0.80 * q_floor / (pw_x + 1e-12), 0.25 ** 2)
            Zx = Zx * np.sqrt(g_sub)
            x = istft(Zx, fs=SR, nperseg=512, noverlap=384)[1][:len(x)].astype(np.float32)
        if len(x) > 64:
            x = sosfiltfilt(BAND_SOS, x).astype(np.float32)

    measured_l, _ = measure_lufs(x)
    gain_db = float(np.clip(target_lufs - measured_l, -14.0, 16.0))
    x *= 10.0 ** (gain_db / 20.0)

    # Smooth room entrance (35ms) and natural breath ring-out (65ms)
    n = len(x)
    fi = min(int(0.035 * SR), n // 6)
    fo = min(int(0.065 * SR), n // 5)
    if fi > 1:
        x[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi, dtype=np.float32)) ** 2
    if fo > 1:
        x[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo, dtype=np.float32)) ** 2

    pk = float(np.max(np.abs(x)))
    if pk > 0.89:
        x *= 0.89 / pk
    return x


def write_m4a(x, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    raw_bytes = np.clip(x, -0.98, 0.98).astype(np.float32).tobytes()
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out_path,
        ],
        input=raw_bytes,
        capture_output=True,
    )


def render_tarantino_beat_audio(beat_id, x_orig, dec_orig, take1_sentence, bumblebee_pair, out_dir):
    """
    Renders 3 crystal-clear, unbroken audio tracks for `beat_id`:
      1. `{beat_id}_orig.m4a`: 1983 WarGames original dialogue normalized to -21.0 LUFS.
      2. `{beat_id}_aligned.m4a`: TARANTINO "THE LINE" (1 Cut, 1 Voice) — A single, unbroken,
         grammatical archival sentence (`take1_sentence`) delivered at its natural cadence over
         a pure -54 LUFS room-air floor (ZERO word-chopping, ZERO 1983 ghost voice!).
      3. `{beat_id}_tight.m4a`: BUMBLEBEE 2-STATION DIAL (2 Unbroken Clauses) — At most 2 intact
         archival sentences (`[Station 1 Setup] -> [0.34s Breath Reset] -> [Station 2 The Line]`),
         never single-word fragments.
    """
    # 1. 1983 Original normalized to -21.0 LUFS
    orig_lufs = dec_orig["lufs"]
    orig_gain = 10.0 ** (np.clip(-21.0 - orig_lufs, -12.0, 16.0) / 20.0)
    x_orig_norm = np.clip(x_orig * orig_gain, -0.95, 0.95).astype(np.float32)
    orig_path = os.path.join(out_dir, f"{beat_id}_orig.m4a")
    write_m4a(x_orig_norm, orig_path)

    # 2. Tarantino "THE LINE" (`{beat_id}_aligned.m4a`): 1 Unbroken Sentence, 1 Voice, 0 Internal Cuts
    y_line = extract_unbroken_sentence_audio(take1_sentence, target_lufs=-21.0)
    lead_pad = int(0.14 * SR)
    tail_pad = int(0.24 * SR)
    x_aligned = make_pink_room_air(lead_pad + len(y_line) + tail_pad, lufs_db=-54.0)
    x_aligned[lead_pad:lead_pad + len(y_line)] += y_line
    pk_al = float(np.max(np.abs(x_aligned))) if len(x_aligned) else 1.0
    if pk_al > 0.91:
        x_aligned *= 0.91 / pk_al
    aligned_path = os.path.join(out_dir, f"{beat_id}_aligned.m4a")
    write_m4a(x_aligned, aligned_path)

    # 3. Bumblebee 2-Station Dial (`{beat_id}_tight.m4a`): 2 Unbroken Clauses separated by a 0.34s breath reset
    clause_wavs = [extract_unbroken_sentence_audio(c_item, target_lufs=-21.0) for c_item in bumblebee_pair]
    breath_gap = int(0.34 * SR)
    total_len = lead_pad + sum(len(w) for w in clause_wavs) + breath_gap * max(0, len(clause_wavs) - 1) + tail_pad
    x_tight = make_pink_room_air(total_len, lufs_db=-54.0)
    cur_p = lead_pad
    for idx_c, w_arr in enumerate(clause_wavs):
        x_tight[cur_p:cur_p + len(w_arr)] += w_arr
        cur_p += len(w_arr) + (breath_gap if idx_c + 1 < len(clause_wavs) else 0)
    pk_t = float(np.max(np.abs(x_tight))) if len(x_tight) else 1.0
    if pk_t > 0.91:
        x_tight *= 0.91 / pk_t
    tight_path = os.path.join(out_dir, f"{beat_id}_tight.m4a")
    write_m4a(x_tight, tight_path)

    dec_aligned = decompose_signal(x_aligned, n_steps=64)
    dec_tight = decompose_signal(x_tight, n_steps=64)
    for d_clean in (dec_aligned, dec_tight):
        for k_priv in ("_venv", "_p_venv", "_f0_clean", "_hr_frame", "_Z", "_Mh", "_Mp"):
            d_clean.pop(k_priv, None)

    return {
        "orig_audio": f"cache/wg_sound/{beat_id}_orig.m4a",
        "aligned_audio": f"cache/wg_sound/{beat_id}_aligned.m4a",
        "tight_audio": f"cache/wg_sound/{beat_id}_tight.m4a",
        "aligned_spec": dec_aligned,
        "tight_spec": dec_tight,
    }


def format_frag_from_sentence(sent, role_label, target_text, target_f0, wg_s, wg_e, wg_speaker="", wg_speaker_color="#45b1ff", wg_turn_num=1, is_fulcrum=True):
    """Formats an unbroken archival sentence entry for both `found_wargames.json` and `wargames-sound-bench.json`."""
    voice_dist = round(abs(sent["f0"] - target_f0) / 12.0, 2)
    return {
        "id": sent["id"],
        "source_type": sent["source_type"],
        "has_local_video": sent.get("has_local_video", False),
        "audio_path": sent["audio_path"],
        "audio_url": sent["audio_url"],
        "video": sent["video_url"],
        "thumb": sent["thumb"],
        "title": sent["title"],
        "year": sent["year"],
        "words": target_text,
        "target": target_text,
        "spoken_as": sent["spoken"],
        "spoken": sent["spoken"],
        "wg_speaker": wg_speaker,
        "wg_speaker_color": wg_speaker_color,
        "wg_turn_num": wg_turn_num,
        "is_fulcrum": is_fulcrum,
        "match_type": "tarantino_line",
        "exact": True,
        "tier": role_label,
        "bumblebee_tier": role_label,
        "wg_s": round(wg_s, 2),
        "wg_e": round(wg_e, 2),
        "wg_dur": round(wg_e - wg_s, 2),
        "t0": sent["t0"],
        "t1": sent["t1"],
        "ts": sent["ts"],
        "te": sent["te"],
        "clip_t0": sent.get("clip_t0", sent["t0"]),
        "clip_t1": sent.get("clip_t1", sent["t1"]),
        "dur": sent["dur"],
        "true_speech_dur": sent["dur"],
        "gr": "A",
        "st": 0.92,
        "f0": sent["f0"],
        "wg_f0": round(target_f0, 1),
        "reg": sent["reg"],
        "voice_dist": voice_dist,
        "lufs": sent["lufs"],
        "gain_db": sent["gain_db"],
        "kind": sent["kind"],
        "p_speech": sent["p_speech"],
        "p_music": sent["p_music"],
        "centroid": sent["centroid"],
        "mass": round(sent["dur"] * 0.28, 3),
        "acoustic_mass": round(sent["dur"] * 0.28, 3),
        "syllables": max(4, sent["word_count"] * 2),
        "band": "mid",
        "dominant_band": "mid",
        "target_cost": round(min(0.35, voice_dist * 0.05), 2),
        "concat_cost": 0.0,
        "seam_glue": f"UNBROKEN SENTENCE (1 Cut, 1 Voice) · Answering {wg_speaker or '1983 Speaker'} · LUFS {sent['gain_db']:+.1f}dB → -21.0 LUFS",
    }


def main():
    t_start_all = time.time()
    os.makedirs(OUT_AUDIO_DIR, exist_ok=True)
    sys.path.insert(0, HERE)
    from build_found_wargames import estimate_acoustic_word_physics, get_synonym_tokens

    fw_path = os.path.join(HERE, "found_wargames.json")
    fw = json.load(open(fw_path))
    whisper_segs = json.load(open(os.path.join(HERE, "whisper_transcript.json")))
    master_mp4 = os.path.join(HERE, "WarGames_1983_H264.mp4")
    sound_table = json.load(open(os.path.join(LAB, "sound-table.json")))

    sentences, census, w2idx, clip_vecs = build_local_archival_audio_index(get_synonym_tokens)

    used_take1_spoken = {}  # track usage count so every beat gets a distinct primary sentence
    bench_books = []
    total_beats_processed = 0

    for bk in fw["books"]:
        bench_lines = []
        for bt_idx, bt in enumerate(bk["beats"]):
            beat_id = bt["beat_id"]
            who = bt["who"]
            line_text = bt["text"]
            sh = bt["wg_shot"]
            s0, s1 = float(sh["start"]), float(sh["end"])

            # 1. Compute full acoustic dialogue window [a0, a1]
            b_ws_set = {norm(w) for w in line_text.split() if norm(w) and len(norm(w)) > 2}
            near_segs = [
                s for s in whisper_segs
                if float(s["end"]) > s0 - 10.0 and float(s["start"]) < s1 + 12.0
                and len({norm(w) for w in str(s.get("text") or "").split()} & b_ws_set) >= 1
            ]
            if near_segs:
                a0 = max(0.0, min(s0, min(float(s["start"]) for s in near_segs)) - 0.15)
                a1 = min(s0 + 18.0, max(s1, max(float(s["end"]) for s in near_segs)) + 0.25)
            else:
                a0, a1 = s0, max(s0 + 2.5, s1)
            if a1 - a0 > 18.0:
                a1 = a0 + 18.0

            # 2. Decode 22,050 Hz PCM from WarGames_1983_H264.mp4 across [a0, a1]
            raw_pcm = subprocess.run(
                [
                    "ffmpeg", "-v", "error", "-nostdin",
                    "-ss", f"{a0:.3f}", "-t", f"{a1 - a0:.3f}",
                    "-i", master_mp4, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-",
                ],
                capture_output=True,
            ).stdout
            x_orig = np.frombuffer(raw_pcm, dtype=np.float32).copy()
            if len(x_orig) < SR // 2:
                x_orig = np.zeros(int(2.5 * SR), dtype=np.float32)

            # 3. Decompose 1983 Signal
            dec = decompose_signal(x_orig, n_steps=64)

            # 4. Diarize 1983 Multi-Speaker Turns (`turns_1983`) and Align Every Spoken Word (`words_1983`)!
            turns_1983, words_1983, events_1983 = diarize_1983_turns(
                bk, bt_idx, bt, whisper_segs, a0, a1, dec, x_orig, estimate_acoustic_word_physics
            )
            fulcrum_turn = next((tr for tr in turns_1983 if tr["is_fulcrum"]), turns_1983[0])
            fulcrum_speaker = fulcrum_turn["speaker"]
            fulcrum_speaker_color = fulcrum_turn["speaker_color"]
            fulcrum_1983_text = fulcrum_turn["text"]
            target_f0 = fulcrum_turn["f0"]

            # 5. Tarantino Phase 1: Anchor Identification & Fulcrum Thesis
            t_meta = classify_tarantino_beat(bk, bt_idx, bt)
            fulcrum_query_text = t_meta["semantic_query"] + " " + fulcrum_1983_text
            q_vec = sentence_clip_vec(fulcrum_query_text, w2idx, clip_vecs, get_synonym_tokens)

            # Expand beat tokens & synonyms for lexical kinship boost
            beat_toks = {norm(w) for w in re.findall(r"[A-Za-z']+", fulcrum_query_text) if norm(w) not in STOPWORDS and len(norm(w)) > 2}
            beat_stems = {stem(t) for t in beat_toks}
            syn_stems = set()
            for t in list(beat_toks):
                for syn in get_synonym_tokens(t, t):
                    syn_stems.add(stem(syn))

            # Score all unbroken archival sentences for the Fulcrum Turn (`★ THE LINE`)
            scored_candidates = []
            for s_entry in sentences:
                cos_sim = float(np.dot(q_vec, s_entry["clip_vec"]))
                exact_ov = len(s_entry["stems"] & beat_stems)
                syn_ov = len(s_entry["stems"] & syn_stems)
                f0_pen = abs(s_entry["f0"] - target_f0) / 140.0
                video_bonus = 0.08 if s_entry["has_local_video"] else 0.0
                dur_bonus = 0.07 if (2.0 <= s_entry["dur"] <= 4.6 and 5 <= s_entry["word_count"] <= 16) else 0.0
                reuse_pen = used_take1_spoken.get(s_entry["spoken"], 0) * 0.65

                score = (
                    cos_sim * 1.35
                    + exact_ov * 0.28
                    + syn_ov * 0.12
                    + video_bonus
                    + dur_bonus
                    - f0_pen * 0.18
                    - reuse_pen
                )
                scored_candidates.append((score, cos_sim, exact_ov, s_entry))

            scored_candidates.sort(key=lambda x: x[0], reverse=True)

            # Select 3 distinct Unbroken Sentence Takes for the Fulcrum Turn (Tarantino Phase 5: Coverage Verification)
            takes_entries = []
            seen_take_ids = set()
            for sc_val, cos_val, ex_ov, cand in scored_candidates:
                if cand["spoken"] in seen_take_ids:
                    continue
                if len(takes_entries) == 2 and not any(t[3]["has_local_video"] for t in takes_entries):
                    if not cand["has_local_video"]:
                        continue
                takes_entries.append((sc_val, cos_val, ex_ov, cand))
                seen_take_ids.add(cand["spoken"])
                if len(takes_entries) == 3:
                    break

            take1_sent = takes_entries[0][3]
            used_take1_spoken[take1_sent["spoken"]] = used_take1_spoken.get(take1_sent["spoken"], 0) + 1

            # Match EVERY 1983 speaker turn in `turns_1983` to its own distinct archival speaker!
            used_turn_arch_ids = {take1_sent["id"]}
            used_turn_arch_spoken = {take1_sent["spoken"]}
            for tr in turns_1983:
                if tr["is_fulcrum"]:
                    tr_sent = take1_sent
                else:
                    tr_vec = sentence_clip_vec(tr["text"], w2idx, clip_vecs, get_synonym_tokens)
                    tr_toks = {norm(w) for w in re.findall(r"[A-Za-z']+", tr["text"]) if norm(w) not in STOPWORDS and len(norm(w)) > 2}
                    tr_stems = {stem(t) for t in tr_toks}
                    best_tr_cand = takes_entries[1][3] if len(takes_entries) > 1 else take1_sent
                    best_tr_sc = -1e9
                    for s_entry in sentences:
                        if s_entry["spoken"] in used_turn_arch_spoken or s_entry["id"] in used_turn_arch_ids:
                            continue
                        if not (1.55 <= s_entry["dur"] <= 3.8):
                            continue
                        c_sim = float(np.dot(tr_vec, s_entry["clip_vec"]))
                        ex_o = len(s_entry["stems"] & tr_stems)
                        f0_p = abs(s_entry["f0"] - tr["f0"]) / 120.0
                        r_pen = used_take1_spoken.get(s_entry["spoken"], 0) * 0.35
                        sc_tr = c_sim * 1.25 + ex_o * 0.28 - f0_p * 0.22 - r_pen
                        if sc_tr > best_tr_sc:
                            best_tr_sc = sc_tr
                            best_tr_cand = s_entry
                    tr_sent = best_tr_cand
                    used_turn_arch_ids.add(tr_sent["id"])
                    used_turn_arch_spoken.add(tr_sent["spoken"])

                tr["_arch_sent"] = tr_sent
                tr["arch_take"] = {
                    "id": tr_sent["id"],
                    "title": tr_sent["title"],
                    "year": tr_sent["year"],
                    "spoken": tr_sent["spoken"],
                    "audio_url": tr_sent["audio_url"],
                    "video": tr_sent["video_url"],
                    "thumb": tr_sent["thumb"],
                    "t0": tr_sent["t0"],
                    "t1": tr_sent["t1"],
                    "dur": tr_sent["dur"],
                    "f0": tr_sent["f0"],
                    "reg": tr_sent["reg"],
                    "lufs": tr_sent["lufs"],
                    "gain_db": tr_sent["gain_db"],
                }

            # Build the Multi-Speaker Cast sequence (`bumblebee_pair` & `bumblebee_2clause_frags`)
            if len(turns_1983) >= 2:
                # Pick up to 2 key turns in chronological order (a Setup/Counter turn + the ★ Fulcrum Turn)
                f_idx = next((i for i, tr in enumerate(turns_1983) if tr["is_fulcrum"]), 0)
                if f_idx > 0:
                    selected_turns = [turns_1983[f_idx - 1], turns_1983[f_idx]]
                else:
                    selected_turns = [turns_1983[0], turns_1983[1]]
                bumblebee_pair = [tr["_arch_sent"] for tr in selected_turns]
                bumblebee_2clause_frags = []
                cur_arch_t = 0.0
                for idx_st, tr in enumerate(selected_turns):
                    s_sent = tr["_arch_sent"]
                    r_lbl = (
                        f"★ TURN {tr['turn_num']} · THE LINE [{tr['speaker']}]"
                        if tr["is_fulcrum"]
                        else f"TURN {tr['turn_num']} · {tr['role']} [{tr['speaker']}]"
                    )
                    bumblebee_2clause_frags.append(
                        format_frag_from_sentence(
                            s_sent,
                            r_lbl,
                            tr["text"],
                            tr["f0"],
                            cur_arch_t,
                            round(cur_arch_t + s_sent["dur"], 2),
                            wg_speaker=tr["speaker"],
                            wg_speaker_color=tr["speaker_color"],
                            wg_turn_num=tr["turn_num"],
                            is_fulcrum=tr["is_fulcrum"],
                        )
                    )
                    cur_arch_t = round(cur_arch_t + s_sent["dur"] + 0.34, 2)
            else:
                station1_sent = takes_entries[1][3] if len(takes_entries) > 1 else take1_sent
                for sc_val, cos_val, ex_ov, cand in scored_candidates[1:25]:
                    if cand["spoken"] != take1_sent["spoken"] and cand["id"] != take1_sent["id"] and 1.6 <= cand["dur"] <= 3.2:
                        station1_sent = cand
                        break
                bumblebee_pair = [station1_sent, take1_sent]
                station1_frag = format_frag_from_sentence(
                    station1_sent,
                    f"STATION 1 · SETUP CLAUSE [{fulcrum_speaker}]",
                    fulcrum_1983_text,
                    target_f0,
                    0.0,
                    station1_sent["dur"],
                    wg_speaker=fulcrum_speaker,
                    wg_speaker_color=fulcrum_speaker_color,
                    wg_turn_num=1,
                    is_fulcrum=False,
                )
                station2_frag = format_frag_from_sentence(
                    take1_sent,
                    f"★ STATION 2 · THE FULCRUM LINE [{fulcrum_speaker}]",
                    fulcrum_1983_text,
                    target_f0,
                    round(station1_sent["dur"] + 0.34, 2),
                    round(station1_sent["dur"] + 0.34 + take1_sent["dur"], 2),
                    wg_speaker=fulcrum_speaker,
                    wg_speaker_color=fulcrum_speaker_color,
                    wg_turn_num=1,
                    is_fulcrum=True,
                )
                bumblebee_2clause_frags = [station1_frag, station2_frag]

            for tr in turns_1983:
                tr.pop("_arch_sent", None)

            # Format `the_line_frag` (1 Unbroken Sentence answering the Fulcrum Speaker's ★ THE LINE)
            the_line_frag = format_frag_from_sentence(
                take1_sent,
                f"★ TARANTINO 'THE LINE' · Answering {fulcrum_speaker} (1 Cut · 1 Voice)",
                fulcrum_1983_text,
                target_f0,
                0.0,
                take1_sent["dur"],
                wg_speaker=fulcrum_speaker,
                wg_speaker_color=fulcrum_speaker_color,
                wg_turn_num=fulcrum_turn["turn_num"],
                is_fulcrum=True,
            )
            arch_frags = [the_line_frag]

            # Build the 3 Auditionable Takes metadata for Tarantino Phase 5
            take_roles = [
                f"Take 1 ★ Chosen Fulcrum Line (Answering {fulcrum_speaker})",
                f"Take 2 · Alternate Meter & Inflection ({fulcrum_speaker})",
                f"Take 3 · Subtext & Visual Counterweight ({fulcrum_speaker})",
            ]
            takes_meta = []
            for idx_t, (sc_val, cos_val, ex_ov, t_sent) in enumerate(takes_entries):
                takes_meta.append({
                    "take_num": idx_t + 1,
                    "role": take_roles[idx_t],
                    "chosen": idx_t == 0,
                    "wg_speaker": fulcrum_speaker,
                    "wg_speaker_color": fulcrum_speaker_color,
                    "wg_line": fulcrum_1983_text,
                    "id": t_sent["id"],
                    "source_type": t_sent["source_type"],
                    "has_local_video": t_sent["has_local_video"],
                    "audio_url": t_sent["audio_url"],
                    "video": t_sent["video_url"],
                    "thumb": t_sent["thumb"],
                    "title": t_sent["title"],
                    "year": t_sent["year"],
                    "spoken": t_sent["spoken"],
                    "t0": t_sent["t0"],
                    "t1": t_sent["t1"],
                    "clip_t0": t_sent.get("clip_t0", t_sent["t0"]),
                    "clip_t1": t_sent.get("clip_t1", t_sent["t1"]),
                    "dur": t_sent["dur"],
                    "lufs": t_sent["lufs"],
                    "gain_db": t_sent["gain_db"],
                    "f0": t_sent["f0"],
                    "reg": t_sent["reg"],
                    "clip_cos": round(cos_val, 3),
                    "score": round(sc_val, 3),
                })

            unique_1983_speakers = list(dict.fromkeys(tr["speaker"] for tr in turns_1983))
            tarantino_checklist = {
                "is_fulcrum": t_meta["is_fulcrum"],
                "beat_role": t_meta["beat_role"],
                "fulcrum_thesis": t_meta["fulcrum_thesis"],
                "fulcrum_speaker": fulcrum_speaker,
                "fulcrum_speaker_color": fulcrum_speaker_color,
                "fulcrum_1983_line": fulcrum_1983_text,
                "scene_speakers": unique_1983_speakers,
                "turns_1983": turns_1983,
                "framing_optics": t_meta["framing_optics"],
                "phase1_anchor": f"{fulcrum_speaker} ({fulcrum_turn['f0']} Hz): \"{fulcrum_1983_text}\" — {t_meta['fulcrum_thesis']}",
                "phase2_cadence": (
                    f"1 Unbroken Utterance ({take1_sent['dur']}s, {take1_sent['word_count']} words, 0 internal cuts) · "
                    f"Archive {take1_sent['f0']} Hz ({take1_sent['reg']}) answering {fulcrum_speaker} ({fulcrum_turn['f0']} Hz)"
                ),
                "phase3_decoupling": (
                    f"{len(turns_1983)} 1983 speaker turn(s) ({' ↔ '.join(unique_1983_speakers)}) · "
                    f"Cut inside speaker silence [{take1_sent['t0']:.2f}s–{take1_sent['t1']:.2f}s] from '{take1_sent['title']}' over -54 LUFS room air"
                ),
                "phase4_optics": t_meta["framing_optics"],
                "phase5_takes": takes_meta,
            }

            # Twin object (`Take 2`) for A/B comparison
            twin_sent = takes_entries[1][3] if len(takes_entries) > 1 else take1_sent
            twin_obj = {
                "id": twin_sent["id"],
                "file": twin_sent["audio_url"],
                "video": twin_sent["video_url"],
                "thumb": twin_sent["thumb"],
                "title": twin_sent["title"],
                "year": twin_sent["year"],
                "text": twin_sent["spoken"],
                "t0": twin_sent["t0"],
                "t1": twin_sent["t1"],
                "dur": twin_sent["dur"],
                "kind": twin_sent["kind"],
                "lufs": twin_sent["lufs"],
                "gain_db": twin_sent["gain_db"],
                "f0": twin_sent["f0"],
                "dist": round(abs(twin_sent["f0"] - target_f0) / 10.0 + 0.8, 1),
                "reg": twin_sent["reg"],
            }

            # 6. Render the 3 Unbroken Audio Tracks (`orig`, `aligned` = The Line, `tight` = Multi-Speaker Cast)
            rendered_tracks = render_tarantino_beat_audio(
                beat_id, x_orig, dec, take1_sent, bumblebee_pair, OUT_AUDIO_DIR
            )

            for k_priv in ("_venv", "_p_venv", "_f0_clean", "_hr_frame", "_Z", "_Mh", "_Mp"):
                dec.pop(k_priv, None)

            dec["a0"] = round(a0, 2)
            dec["a1"] = round(a1, 2)
            dec["turns_1983"] = turns_1983
            dec["words_timed"] = words_1983
            dec["events"] = events_1983

            # Update `found_wargames.json`
            sh["audio_start"] = round(a0, 2)
            sh["audio_end"] = round(a1, 2)
            sh["audio_dur"] = dec["dur"]
            sh["lufs"] = dec["lufs"]
            sh["lra"] = dec["lra"]
            sh["f0_median"] = dec["f0_median"]
            sh["register"] = dec["register"]
            sh["hp_ratio"] = dec["hp_ratio"]
            sh["mod4"] = dec["mod4"]
            sh["floor_hp"] = dec["floor_hp"]
            sh["spectrogram"] = dec

            bt["who"] = fulcrum_speaker
            bt["turns_1983"] = turns_1983
            bt["scene_speakers"] = unique_1983_speakers
            bt["fulcrum_1983_line"] = fulcrum_1983_text
            bt["tarantino"] = tarantino_checklist
            bt["bumblebee"]["turns_1983"] = turns_1983
            bt["bumblebee"]["scene_speakers"] = unique_1983_speakers
            bt["bumblebee"]["fulcrum_speaker"] = fulcrum_speaker
            bt["bumblebee"]["fulcrum_1983_line"] = fulcrum_1983_text
            bt["bumblebee"]["chain"] = arch_frags
            bt["bumblebee"]["two_station_chain"] = bumblebee_2clause_frags
            bt["bumblebee"]["takes"] = takes_meta
            bt["bumblebee"]["tarantino"] = tarantino_checklist
            bt["bumblebee"]["orig_audio"] = rendered_tracks["orig_audio"]
            bt["bumblebee"]["aligned_audio"] = rendered_tracks["aligned_audio"]
            bt["bumblebee"]["tight_audio"] = rendered_tracks["tight_audio"]
            bt["bumblebee"]["aligned_spec"] = rendered_tracks["aligned_spec"]
            bt["bumblebee"]["tight_spec"] = rendered_tracks["tight_spec"]
            bt["bumblebee"]["twin"] = twin_obj
            bt["bumblebee"]["lufs_target"] = -21.0
            bt["bumblebee"]["orig_lufs"] = dec["lufs"]
            bt["bumblebee"]["aligned_lufs"] = rendered_tracks["aligned_spec"]["lufs"]
            bt["bumblebee"]["tight_lufs"] = rendered_tracks["tight_spec"]["lufs"]
            bt["bumblebee"]["f0_median"] = dec["f0_median"]
            bt["bumblebee"]["register"] = dec["register"]
            bt["bumblebee"]["hp_ratio"] = dec["hp_ratio"]
            bt["bumblebee"]["mod4"] = dec["mod4"]
            bt["bumblebee"]["floor_hp"] = dec["floor_hp"]

            # Replace `bt["literal"]["frags"]` with the unbroken Tarantino takes so `found-wargames.html` never shows word-salad fragments
            bt["literal"]["mode_note"] = f"Tarantino 'The Line' · Answering {fulcrum_speaker} · 1 Unbroken Archival Sentence"
            bt["literal"]["frags"] = [
                {
                    "id": tk["id"],
                    "title": tk["title"],
                    "year": tk["year"],
                    "words": fulcrum_1983_text if idx_tk == 0 else tk["role"],
                    "spoken_as": tk["spoken"],
                    "wg_speaker": fulcrum_speaker,
                    "match_type": "tarantino_line" if idx_tk == 0 else f"take_{idx_tk+1}",
                    "exact": idx_tk == 0,
                    "t0": tk["clip_t0"],
                    "t1": tk["clip_t1"],
                    "dur": tk["dur"],
                    "thumb": tk["thumb"],
                    "video": tk["video"],
                    "local_audio": tk["audio_url"],
                    "local_t0": tk["t0"],
                    "local_t1": tk["t1"],
                    "lufs": tk["lufs"],
                    "gain_db": tk["gain_db"],
                    "f0": tk["f0"],
                    "reg": tk["reg"],
                    "kind": "speech",
                }
                for idx_tk, tk in enumerate(takes_meta)
            ]

            # Build `chops` as the 3 complete Auditionable Takes (never single-word slices!)
            chops = [
                {
                    "id": f"{beat_id}_TAKE{tk['take_num']}",
                    "label": f"Take {tk['take_num']}" + (f" ★ THE LINE ({fulcrum_speaker})" if tk["chosen"] else ""),
                    "spoken": tk["spoken"],
                    "wg_speaker": fulcrum_speaker,
                    "file": rendered_tracks["aligned_audio"] if tk["chosen"] else tk["audio_url"],
                    "t0": 0.0 if tk["chosen"] else tk["t0"],
                    "t1": rendered_tracks["aligned_spec"]["dur"] if tk["chosen"] else tk["t1"],
                    "dur": tk["dur"],
                    "lufs": tk["lufs"],
                    "gain_db": tk["gain_db"],
                    "f0": tk["f0"],
                    "hook": 3 if tk["chosen"] else 2,
                    "title": tk["title"],
                    "year": tk["year"],
                }
                for tk in takes_meta
            ]

            bench_lines.append({
                "id": beat_id,
                "n": bt["index"],
                "who": fulcrum_speaker,
                "who_color": fulcrum_speaker_color,
                "scene_speakers": unique_1983_speakers,
                "turns_1983": turns_1983,
                "fulcrum_1983_line": fulcrum_1983_text,
                "text": fulcrum_1983_text,
                "screenplay_summary": line_text,
                "whisper": bt.get("whisper") or "",
                "foley_label": bt.get("foley_label") or "",
                "foley_cue": bt.get("foley_cue") or "",
                "s": 0.0,
                "e": dec["dur"],
                "a0": round(a0, 2),
                "a1": round(a1, 2),
                "clock": round(a0, 2),
                "orig_file": rendered_tracks["orig_audio"],
                "aligned_file": rendered_tracks["aligned_audio"],
                "tight_file": rendered_tracks["tight_audio"],
                "lufs": dec["lufs"],
                "lra": dec["lra"],
                "f0_median": dec["f0_median"],
                "register": dec["register"],
                "hp_ratio": dec["hp_ratio"],
                "mod4": dec["mod4"],
                "floor_hp": dec["floor_hp"],
                "centroid_hz": dec["centroid_hz"],
                "flatness": dec["flatness"],
                "words": words_1983,
                "events": events_1983,
                "hop": dec["hop"],
                "rms": dec["rms"],
                "f0": dec["f0"],
                "mel16": dec["mel16"],
                "harm_env": dec["harm_env"],
                "perc_env": dec["perc_env"],
                "floor_env": dec["floor_env"],
                "onsets": dec["onsets"],
                "arch_frags": arch_frags,
                "two_station_frags": bumblebee_2clause_frags,
                "takes": takes_meta,
                "tarantino": tarantino_checklist,
                "aligned_spec": rendered_tracks["aligned_spec"],
                "tight_spec": rendered_tracks["tight_spec"],
                "twin": twin_obj,
                "chops": chops,
                "illocutionary_force": bt["bumblebee"]["illocutionary_force"],
                "vibe_filter": bt["bumblebee"]["vibe_filter"],
                "picture": {
                    "wg_shot": {
                        "id": sh["id"],
                        "start": sh["start"],
                        "end": sh["end"],
                        "a0": round(a0, 2),
                        "a1": round(a1, 2),
                        "thumb": sh["thumb"],
                        "strip": sh["strip"],
                        "sign": sh.get("sign") or "1",
                        "sign_note": sh.get("sign_note") or "",
                        "scale": sh.get("scale") or "medium",
                    },
                    "arch_shot": (bt["lenses"].get("synthesis") or [{}])[0],
                },
            })
            total_beats_processed += 1
            if total_beats_processed % 15 == 0 or total_beats_processed == 105:
                print(
                    f"  Rendered {total_beats_processed}/105 beats ({time.time() - t_start_all:.1f}s) · "
                    f"{beat_id} [{' ↔ '.join(unique_1983_speakers)}] ★ {fulcrum_speaker}: \"{fulcrum_1983_text}\" -> \"{take1_sent['spoken']}\" ({take1_sent['dur']}s)"
                )

        bench_books.append({
            "n": f"{bk['book']:02d}",
            "id": bk["id"],
            "bnum": bk["bnum"],
            "act": bk["act"],
            "title": bk["title"],
            "milieu": bk["milieu"],
            "start": bk["start"],
            "end": bk["end"],
            "lines": bench_lines,
        })

    with open(fw_path, "w") as f:
        json.dump(fw, f, indent=2)

    cine_idx_path = os.path.join(LAB, "tools", "cineosis-index.json")
    signs_map = {}
    if os.path.exists(cine_idx_path):
        for s_item in json.load(open(cine_idx_path)).get("signs") or []:
            signs_map[str(s_item["n"])] = {
                "symbol": s_item.get("symbol", s_item["n"]),
                "name": s_item.get("name", ""),
                "dom": s_item.get("dom", "perception"),
            }

    bench_payload = {
        "title": "WarGames (1983) · Tarantino 'The Line' (Pars Pro Toto) & Bumblebee Sound Bench",
        "subtitle": "Unbroken Single-Speaker Sentences (1 Cut, 1 Voice) · 5-Phase Directing Checklist · HPSS, YIN f0 & BS.1770-4 LUFS",
        "target_lufs": -21.0,
        "census_clips": len(census),
        "books": bench_books,
        "signs": signs_map,
        "sound_table": {
            "rows": sound_table["rows"],
            "columns": [
                {
                    "sym": c["sym"],
                    "name": c["name"],
                    "family": c["family"],
                    "what": c["what"],
                    "law": c["law"],
                    "priority": c.get("priority"),
                    "rows": c.get("rows", {}),
                }
                for c in sound_table["columns"]
            ],
            "laws": sound_table["laws"],
            "moves": sound_table["moves"],
        },
    }
    with open(OUT_JSON_PATH, "w") as f:
        json.dump(bench_payload, f, ensure_ascii=False, separators=(",", ":"))

    print(
        f"COMPLETE in {time.time() - t_start_all:.1f}s! "
        f"Wrote {OUT_JSON_PATH} ({os.path.getsize(OUT_JSON_PATH) // 1024} KB) "
        f"and {total_beats_processed * 3} unbroken M4A tracks in {OUT_AUDIO_DIR}."
    )


if __name__ == "__main__":
    main()

