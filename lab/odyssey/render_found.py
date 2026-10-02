"""Render the found Odyssey's sound offline, one continuous track per scene and mode, so the page never cuts sound itself.
  pieces   every archival voice is taken from its clip's audio with room on both sides (it opens in the speaker's silence and its
           tail rings out under what follows), loudness-normalized to one speech level, faded in and out, never clipped
  check    every piece is heard back by Whisper; if the last word it should say is not heard, the tail is lengthened (up to
           0.9 s) and heard again; the before and after are reported (cache/render-check.json)
  fills    words the archive never says come from our studio recording, with the same treatment
  bed      under everything, the book's Bronze Council track, quiet, ducking under the voices and rising in the rests,
           so the sound never stops
  pace     a breath between voices, a long rest between lines, a slow opening and close
Writes found-audio/<mode>/<scene>.m4a (AAC mono, 48 kbps) and the timeline (when each voice and line begins) into found.json under
scene_tracks.   usage: ~/.cache/mlxw-venv/bin/python render_found.py [scene ...]"""
import glob, hashlib, json, os, re, subprocess, sys, urllib.parse
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly
H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, "cache", "aud"); HW = os.path.expanduser("~/Downloads/odyssey-halfworld")
OUT = os.path.join(H, "found-audio"); SR = 44100; meter = pyln.Meter(SR)
# head: up to this much of the speaker's room before the first word (never the word before), faded in
# ring: up to this much of the silence after the last word, at full; ghost: then whatever follows, fading out fast underneath
# lo, hi: the pause between two voices is the speakers' own (half what A left after its words, half what B left before its own),
# held within these bounds; rest: the pause between lines, likewise lengthened by how long the last speaker paused
# call: the line said plainly first by our studio voice, then the archive answers with the SPOKEN choice; cr is the breath
# between the call and its answer. Pauses are short: what fills them is sound (rooms, tails, the shot's own sound signs)
MODES = {"spoken": {"pre": .14, "tail": .55, "head": .8, "ring": .9, "ghost": .45, "lo": .3, "hi": .85, "rest": 1.0},
         "performance": {"pre": .08, "tail": .4, "head": .3, "ring": .35, "ghost": .2, "lo": .03, "hi": .22, "rest": .8},
         "call": {"pre": .14, "tail": .55, "head": .8, "ring": .9, "ghost": .45, "lo": .3, "hi": .85, "rest": 1.0, "cr": .35, "bed_db": -4}}   # a dialogue wants air around the voices
SPEECH, BED, MASTER = -21.0, -33.0, -19.0
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")
found = json.load(open(os.path.join(H, "found.json"))); radio = json.load(open(os.path.join(H, "radio.json")))
book_of = {s["id"]: b for b in radio["books"] for s in b["scenes"]}
_cache = {}
def audio(path, key):
    if key in _cache: return _cache[key]
    try:
        if path.endswith(".flac"): a, sr = sf.read(path, dtype="float32")
        else:
            raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
            a, sr = np.frombuffer(raw, np.float32).copy(), SR
        if a.ndim > 1: a = a.mean(1)
        if sr != SR: a = resample_poly(a, SR // 100, sr // 100).astype(np.float32)
    except Exception: a = None
    if len(_cache) > 60: _cache.pop(next(iter(_cache)))
    _cache[key] = a; return a
def loud(x):
    try:
        v = meter.integrated_loudness(x) if len(x) > SR * .45 else None
        return v if v is not None and np.isfinite(v) and v > -70 else None
    except Exception: return None
CLIPL = {}
def clip_level(i, a):
    if i not in CLIPL: CLIPL[i] = loud(a) or -26.0
    return CLIPL[i]
# ---- one medium for every voice. Archival voices differ (measured on 300: loudness -34..-20 LUFS, bandwidth 1.0..2.6 kHz,
# speech 12..29 dB over its hiss, pitch 115..229 Hz), so each is brought into one shared medium before it is heard:
#   hiss and hum lowered toward one floor (spectral subtraction from the clip's own quietest moments, gently, leaving some air)
#   its tone pulled 70% of the way toward the archive's median voice (third-octave match EQ, at most 9 dB)
#   one band for all, 90 Hz to 6 kHz, so a bright modern voice does not leap out of the muffled 1930s ones
#   its dynamics evened (2.5:1 above its own speaking level), then its loudness set from its words alone
# and all of them later share one room (a single reverb on the voice bus) and one floor (a continuous room tone).
from scipy.signal import stft, istft, butter, sosfiltfilt, lfilter, fftconvolve
WORDS = json.load(open(os.path.join(H, "cache", "ears", "words.json")))
for f in glob.glob(os.path.join(H, "cache", "ears", "words.*.json")): WORDS.update(json.load(open(f)))
def edges(i, t0, t1):
    ws = (WORDS.get(i) or {}).get("words") or []
    pe = max([w[2] for w in ws if w[2] <= t0 + .03] or [0.0]); ns = min([w[1] for w in ws if w[1] >= t1 - .03] or [t1 + 5])
    return pe, ns
BANDS = 100 * 2 ** (np.arange(20) / 3)                               # third octaves, 100 Hz to 6.3 kHz
def ltas(x):
    S = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR)
    e = np.array([S[(fr >= b / 2 ** (1 / 6)) & (fr < b * 2 ** (1 / 6))].mean() + 1e-12 for b in BANDS]); d = 10 * np.log10(e); return d - d.mean()
TP = os.path.join(H, "cache", "voice-target.npy"); TARGET = np.load(TP) if os.path.exists(TP) else None
SOS_BAND = butter(2, [90, 6000], "bandpass", fs=SR, output="sos")
def medium(x, core, ctx):
    """x: the piece; core: (s, e) samples of its words; ctx: the clip around it, for the noise print."""
    if len(x) < 2048: return x
    f, t, Z = stft(ctx, SR, nperseg=1024, noverlap=768); pw = np.abs(Z) ** 2
    fe = pw.sum(0); q = pw[:, fe <= np.percentile(fe, 15)].mean(1, keepdims=True)          # its noise: the quietest 15%
    f, t, X = stft(x, SR, nperseg=1024, noverlap=768); P_ = np.abs(X) ** 2
    snr = 10 * np.log10(P_.sum(0).mean() / (q.sum() + 1e-12) + 1e-12)
    if snr < 26:                                                       # noisy: subtract it, leave a quarter so it still breathes
        g = np.maximum(1 - 1.0 * q / (P_ + 1e-12), .25 ** 2); X = X * np.sqrt(g)
    x = istft(X, SR, nperseg=1024, noverlap=768)[1][: len(x)].astype(np.float32)
    if TARGET is not None:
        c = x[core[0]: core[1]]
        if len(c) > SR * .25:
            corr = np.clip(TARGET - ltas(c), -9, 9) * .7; n = 1 << int(np.ceil(np.log2(len(x) * 2))); fr = np.fft.rfftfreq(n, 1 / SR)
            gain = 10 ** (np.interp(np.log2(np.maximum(fr, 50)), np.log2(BANDS), corr) / 20)
            x = np.fft.irfft(np.fft.rfft(x, n) * gain, n)[: len(x)].astype(np.float32)
    x = sosfiltfilt(SOS_BAND, x).astype(np.float32)
    env = np.sqrt(lfilter([.003], [1, -.997], x ** 2) + 1e-12); c = env[core[0]: core[1]]
    thr = np.percentile(c, 60) if len(c) else env.max(); g = np.where(env > thr, (env / thr) ** (1 / 2.5 - 1), 1.0)
    return (x * g).astype(np.float32)
def piece(a, t0, t1, P, ref, i=None, raw=False):
    """The voice from t0 to t1 in the shared medium, opening out of its own room and ringing out after, normalized on its words."""
    pe, ns = edges(i, t0, t1) if i else (t0 - P["pre"], t1 + P["tail"])
    head = max(P["pre"], min(P["head"], t0 - pe - .04)); ring = max(P["tail"], min(P["ring"], ns - t1 - .04))
    s = max(0.0, t0 - head); e = min(len(a) / SR, t1 + ring + P["ghost"])
    S, E = int(s * SR), int(e * SR); x = a[S:E].astype(np.float32).copy()
    if len(x) < 256: return None, 0
    core = (int((t0 - s) * SR), int((t1 - s) * SR)); ctx = a[max(0, S - 3 * SR): min(len(a), E + 3 * SR)]
    if not raw: x = medium(x, core, ctx)                                # our studio voice stays clean: it is the text
    c = x[core[0]: core[1]]
    if 0 < len(c) < SR * .5: c = np.tile(c, int(np.ceil(SR * .55 / len(c))))   # a single word is too short to meter: meter it repeated
    L = loud(c) or ref; x *= 10 ** (np.clip(SPEECH - L, -12, 18) / 20)
    n = len(x); env = np.ones(n, np.float32); h = max(1, int((t0 - .06 - s) * SR))
    env[:h] = np.sin(np.linspace(0, np.pi / 2, h)) ** 2                # the room fades up before the first word
    r = min(n, int((t1 + ring - s) * SR))
    if r < n: env[r:] = np.exp(-np.arange(n - r) / (SR * P["ghost"] / 4))   # what follows the ring fades away underneath
    fo = min(int(.05 * SR), n // 4); env[-fo:] *= np.linspace(1, 0, fo)
    x *= env; pk = np.abs(x).max()
    if pk > .89: x *= .89 / pk
    return x, s
# ---- Whisper hears every cut
PART = (int(sys.argv[2]), int(sys.argv[3])) if sys.argv[1:2] == ["--part"] else None
CHECK = {}; CP = os.path.join(H, "cache", f"render-check{'.' + str(PART[0]) if PART else ''}.json")
for f in glob.glob(os.path.join(H, "cache", "render-check*.json")): CHECK.update(json.load(open(f)))
try:
    import mlx_whisper
    def hear(x):
        y = resample_poly(x, 160, 441).astype(np.float32)
        return mlx_whisper.transcribe(np.pad(y, (3200, 3200)), path_or_hf_repo="mlx-community/whisper-base.en-mlx", condition_on_previous_text=False, language="en")["text"]
except Exception as e: hear = None; print("no ears:", e)
def heard_last(text, said):
    want = [norm(w) for w in said.split() if norm(w)]; got = {norm(w) for w in text.split() if norm(w)}
    return (want[-1] in got if want else True), (sum(w in got for w in want) / len(want) if want else 1)
def checked(a, x0, P, i, ref, mode):
    """Cut, hear it back, lengthen the tail until the last word is heard (at most 0.9 s more)."""
    k = f"{mode}|{i}|{x0['t0']}|{x0['t1']}"
    if k in CHECK and "extra" in CHECK[k]: extra = CHECK[k]["extra"]; return piece(a, x0["t0"], x0["t1"] + extra, P, ref, i)
    rec = {"said": x0["words"]}; extra = 0.0
    x, at = piece(a, x0["t0"], x0["t1"], P, ref, i)
    if hear and len(x0["words"].split()) >= 2 and (mode == "spoken" or int(hashlib.md5(k.encode()).hexdigest(), 16) % 4 == 0):   # every sentence; a quarter of the fragments
        # what the old page played: from t0 to t1 less its 50 ms lead, no tail
        old = a[int(x0["t0"] * SR): int(max(x0["t0"] + .05, x0["t1"] - .05) * SR)]
        if len(old) > 1600 and int(hashlib.md5(k.encode()).hexdigest(), 16) % 16 < 4: rec["old"] = heard_last(hear(old), x0["words"])
        for step in range(4):
            last, rcl = heard_last(hear(x), x0["words"]); rec.setdefault("first", [last, rcl]); rec["final"] = [last, rcl]
            if last or x0["t1"] + P["tail"] + extra + .3 > len(a) / SR or step == 3: break
            extra += .3; x, at = piece(a, x0["t0"], x0["t1"] + extra, P, ref, i)
    rec["extra"] = round(extra, 2); CHECK[k] = rec; return x, at
# ---- the bed: the book's track, quiet, ducking under the voices
def bed(sid, n):
    b = book_of.get(sid)
    if not b or not b.get("track"): return np.zeros(n, np.float32)
    p = os.path.join(HW, urllib.parse.unquote(b["track"].split("odyssey-halfworld/")[1]))
    m = audio(p, p)
    if m is None or not len(m): return np.zeros(n, np.float32)
    off = (int(sid[-2:]) * 41 * SR) % max(1, len(m) - SR)          # each scene enters the track somewhere else
    m = np.tile(m, int(np.ceil((n + off) / len(m))) + 1)[off: off + n].copy()
    L = loud(m[: min(len(m), 60 * SR)]) or -20; m *= 10 ** ((BED - L) / 20); return m.astype(np.float32)
_rng = np.random.default_rng(7)
_t = np.arange(int(1.4 * SR)) / SR; IR = _rng.standard_normal(len(_t)) * np.exp(-6.9 * _t / 1.1); IR[: int(.018 * SR)] = 0
IR = sosfiltfilt(butter(2, 3200, "lowpass", fs=SR, output="sos"), IR).astype(np.float32); IR /= np.sqrt((IR ** 2).sum())
def glue(v):
    w = fftconvolve(v, IR)[: len(v)].astype(np.float32); rv, rw = np.sqrt((v ** 2).mean()) + 1e-9, np.sqrt((w ** 2).mean()) + 1e-9
    return w * (rv / rw) * 10 ** (-14 / 20)
def room(n):
    w = np.fft.rfft(_rng.standard_normal(n)); fr = np.fft.rfftfreq(n, 1 / SR); w /= np.sqrt(np.maximum(fr, 20))   # pink
    x = np.fft.irfft(w, n).astype(np.float32); x = sosfiltfilt(butter(2, [150, 4000], "bandpass", fs=SR, output="sos"), x).astype(np.float32)
    L = loud(x[: 20 * SR]) or -30; return x * 10 ** ((SPEECH - 36 - L) / 20)
def room_print(y):
    """The sound of a voice's room: the quiet moments inside it (between its words), away from the faded edges."""
    f, t, Z = stft(y, SR, nperseg=2048, noverlap=1536); m = np.abs(Z); k = m.shape[1]; m = m[:, int(k * .15): max(int(k * .15) + 1, int(k * .85))]
    e = m.sum(0); q = m[:, (e >= np.percentile(e, 8)) & (e <= np.percentile(e, 30))]
    return q.mean(1) if q.size else m.mean(1)
def bridges(n, parts):
    """The in-between, made: across every pause a bed of room sound that begins as the room of the voice that ends and becomes,
    spectrum by spectrum, the room of the voice that begins (log-magnitude interpolation, random phase), so no pause is a hole."""
    out = np.zeros(n, np.float32); pr = [room_print(y) for _, y, _, _ in parts]
    spans = [(max(0.0, parts[0][2] - 1.5), parts[0][2], pr[0], pr[0])] + [(parts[k][3], parts[k + 1][2], pr[k], pr[k + 1]) for k in range(len(parts) - 1)] + [(parts[-1][3], min(n / SR, parts[-1][3] + 2.5), pr[-1], pr[-1])]
    for a_, b_, pa, pb in spans:
        a_, b_ = max(0.0, a_ - .3), min(n / SR, b_ + .3); L = int((b_ - a_) * SR)
        if L < 4096: continue
        nf = L // 512 + 2; w = np.linspace(0, 1, nf)[None, :]
        mag = np.exp((1 - w) * np.log(pa[:, None] + 1e-9) + w * np.log(pb[:, None] + 1e-9))
        _, x = istft(mag * np.exp(2j * np.pi * _rng.random(mag.shape)), SR, nperseg=2048, noverlap=1536); x = x[:L].astype(np.float32)
        f = min(int(.25 * SR), L // 3); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        s = int(a_ * SR); out[s: s + len(x)] += x[: n - s] * .8
    return out
# ---- sound signs: each shot's own sounds (CLAP-matched field and music clips, ears_match.py), a short excerpt where the sound is
# most alive, laid under the end of one voice and into the next: the sound that receives the next sentence
SEA = {sc["id"]: sc for f in glob.glob(os.path.join(H, "sea", "b*.json")) for sc in json.load(open(f))["scenes"]}
def shot_for(sid, u):
    best, ov = None, 0
    for sh in (SEA.get(sid) or {}).get("shots", []):
        a, b = float(sh["t0"]), float(sh["t0"]) + float(sh["dur"]); o = min(b, u["t1"]) - max(a, u["t0"])
        if o > ov: best, ov = sh, o
    return best
def sign(sid, u, k, dur=2.6):
    sh = shot_for(sid, u); fl = (sh or {}).get("foley") or []
    for j in range(len(fl)):
        f = fl[(k + j) % len(fl)]; a = audio(os.path.join(A, f["id"] + ".flac"), f["id"])
        if a is None or len(a) < SR * 3: continue
        w = int(dur * SR); e = np.convolve(a[: SR * 30] ** 2, np.ones(SR // 10) / (SR // 10), "valid")[:: SR // 20]
        rise = np.maximum(0, np.diff(e, prepend=e[0]))                  # where it comes alive: the strongest onset
        st = int(np.argmax(rise[: max(1, len(rise) - int(dur * 20))])) * (SR // 20); x = a[st: st + w].astype(np.float32).copy()
        if len(x) < w * .8: continue
        L = loud(x)
        if L is None: continue
        x *= 10 ** ((-27 - L) / 20); fi, fo = int(.5 * SR), int(.9 * SR); x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo)
        return x, f["id"]
    return None, None
def render(sid, mode):
    P = MODES[mode]; lines = found["scenes"].get(sid) or []
    voice_p = os.path.join(HW, "drive", "voice", sid + ".m4a")
    parts, ev, lt, signs = [], [], [], []; cur = 2.0; after = None; prev_end = None   # the music opens alone for two seconds
    for li, u in enumerate(lines):
        t = u["modes"].get("spoken" if mode == "call" else mode)
        if not t: continue
        l0 = None
        if mode == "call":                                              # the call: our voice says the line plainly
            a = audio(voice_p, voice_p)
            if a is not None:
                y, s0 = piece(a, u["t0"], u["t1"], {**P, "pre": .06, "tail": .3, "head": .12, "ring": .3, "ghost": .05}, -20, None, raw=True)
                if y is not None:
                    l0 = cur; parts.append((cur - (u["t0"] - s0), y, cur, cur + u["t1"] - u["t0"]))
                    ev.append({"at": round(cur, 2), "end": round(cur + u["t1"] - u["t0"], 2), "li": li, "fi": -1, "call": 1, "gap": round(prev_end, 2) if prev_end is not None else 0})
                    cur += u["t1"] - u["t0"]; prev_end = cur
                    sg, sgid = sign(sid, u, li)                          # a sound sign carries the call into its answer
                    if sg is not None: signs.append((cur - .9, sg))
                    cur += P["cr"]; after = None
        for fi, x in enumerate(t["frags"]):
            if x.get("id"):
                a = audio(os.path.join(A, x["id"] + ".flac"), x["id"])
                if a is None: continue
                y, s0 = checked(a, x, P, x["id"], clip_level(x["id"], a), "spoken" if mode == "call" else mode)
                if y is None: continue
                pe, ns = edges(x["id"], x["t0"], x["t1"]); before, aft = x["t0"] - pe, ns - x["t1"]; c0, c1 = x["t0"], x["t1"]
            elif x.get("fill"):
                a = audio(voice_p, voice_p)
                if a is None: continue
                y, s0 = piece(a, x["fill"][0], x["fill"][1], {**P, "tail": .14, "pre": .05, "head": .05, "ring": .14, "ghost": .06}, -20)
                if y is None: continue
                before = aft = .12; c0, c1 = x["fill"]
            else:
                if x.get("gap"): cur += .3
                continue
            if l0 is not None and after is not None and not (mode == "call" and ev and ev[-1].get("call")): cur += float(np.clip(.5 * (after + before), P["lo"], P["hi"]))
            if l0 is None: l0 = cur
            parts.append((cur - (c0 - s0), y, cur, cur + c1 - c0))
            e_ = {"at": round(cur, 2), "end": round(cur + c1 - c0, 2), "li": li, "fi": fi, "gap": round(prev_end, 2) if prev_end is not None else 0}
            e_.update({"id": x["id"], "t0": x["t0"]} if x.get("id") else {"ours": 1}); ev.append(e_)
            cur += c1 - c0; after = min(aft, 2.0); prev_end = cur
        if l0 is not None:
            lt.append({"li": li, "at": round(l0, 2), "end": round(cur, 2)})
            if mode != "call" or li % 2 == 1:                           # and between lines, the next shot's sound receives the next voice
                nu = next((lines[j] for j in range(li + 1, len(lines)) if lines[j]["modes"].get("spoken")), None)
                sg, _ = sign(sid, nu or u, li + 7)
                if sg is not None: signs.append((cur - .5, sg))
            cur += float(np.clip(.6 * P["rest"] + .5 * (after or 0), .75 * P["rest"], 1.4 * P["rest"]))
    if not ev: return None
    n = int((cur + 3.0) * SR); v = np.zeros(n, np.float32)
    for at, y, _, _ in parts:
        s = max(0, int(at * SR)); e = min(n, s + len(y)); v[s:e] += y[: e - s]
    v = v + bridges(n, parts)
    # one room for all of them: a single soft reverb on the voices (1.1 s, dark, 14 dB under), and one floor: a quiet
    # continuous room tone, so the hiss never switches with the voice
    v = v + glue(v); v = v + room(n)
    # duck the bed under the voices: down 10 dB with a quick attack and a slow release
    act = np.zeros(n, np.float32)
    for e_ in ev: act[int(e_["at"] * SR): int((e_["end"] + .2) * SR)] = 1
    k = int(.05 * SR); act = np.convolve(act[::k], np.ones(1), "same")
    env = np.zeros(len(act), np.float32); g = 0.0
    for j, a_ in enumerate(act): g = g + (a_ - g) * (.6 if a_ > g else .06); env[j] = g
    env = np.repeat(env, k)[:n]; env = np.pad(env, (0, n - len(env)))
    sb = np.zeros(n, np.float32)
    for at, y in signs:
        s_ = max(0, int(at * SR)); e_ = min(n, s_ + len(y)); sb[s_:e_] += y[: e_ - s_]
    b = (bed(sid, n) + sb) * (1 - .68 * env) * 10 ** (P.get("bed_db", 0) / 20)                             # the signs ride the music bus: they recede under voices
    fade = np.ones(n, np.float32); fade[: 2 * SR] = np.linspace(0, 1, 2 * SR); fade[-3 * SR:] = np.linspace(1, 0, 3 * SR)
    mix = v + b * fade
    L = loud(mix) or MASTER; mix *= 10 ** ((MASTER - L) / 20)
    c = .6; hot = np.abs(mix) > c                                       # a soft knee above -4.4 dBFS, no hard clips
    mix[hot] = np.sign(mix[hot]) * (c + (1 - c) * np.tanh((np.abs(mix[hot]) - c) / (1 - c)))
    pk = np.abs(mix).max()
    if pk > .89: mix *= .89 / pk                                         # room for the encoder's overshoot
    os.makedirs(os.path.join(OUT, mode), exist_ok=True); wav = os.path.join(OUT, mode, sid + ".wav"); m4a = wav[:-4] + ".m4a"
    sf.write(wav, mix, SR)
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", wav, "-c:a", "aac_at", "-b:a", "48k", "-ac", "1", m4a]); os.remove(wav)
    return {"url": f"odyssey/found-audio/{mode}/{sid}.m4a", "dur": round(n / SR, 2), "lines": lt, "ev": ev}
if sys.argv[1:2] == ["--merge"]:                                     # fold the parts' timelines into found.json
    tr = found.setdefault("scene_tracks", {})
    for f in glob.glob(os.path.join(OUT, "*", "*.json")):
        mode, sid = f.split(os.sep)[-2], os.path.basename(f)[:-5]; tr.setdefault(sid, {})[mode] = json.load(open(f))
    json.dump(found, open(os.path.join(H, "found.json"), "w"), separators=(",", ":")); print("merged", len(tr), "scenes"); sys.exit()
want = sorted(found["scenes"])[PART[0]::PART[1]] if PART else (sys.argv[1:] or sorted(found["scenes"]))
if os.environ.get("ONLY"): MODES = {k: v for k, v in MODES.items() if k in os.environ["ONLY"].split(",")}   # re-render some modes only
tracks = found.setdefault("scene_tracks", {})
for c, sid in enumerate(want, 1):
    for mode in MODES:
        r = render(sid, mode)
        if r: tracks.setdefault(sid, {})[mode] = r; json.dump(r, open(os.path.join(OUT, mode, sid + ".json"), "w"), separators=(",", ":"))
    json.dump(CHECK, open(CP, "w"))
    if not PART and (c % 10 == 0 or c == len(want)): json.dump(found, open(os.path.join(H, "found.json"), "w"), separators=(",", ":")); print(c, "of", len(want), "scenes", flush=True)
if not PART: json.dump(found, open(os.path.join(H, "found.json"), "w"), separators=(",", ":"))
# what Whisper heard: the old cuts against the new
for mode in MODES:
    r = [v for k, v in CHECK.items() if k.startswith(mode) and "first" in v]
    if not r: continue
    old = [v["old"][0] for v in r if "old" in v]
    print(f"{mode}: {len(r)} cuts heard · last word heard: old page {np.mean(old) * 100:.0f}% · new cut {np.mean([v['first'][0] for v in r]) * 100:.0f}% · after lengthening {np.mean([v['final'][0] for v in r]) * 100:.0f}% · words heard {np.mean([v['final'][1] for v in r]) * 100:.0f}% · tails lengthened {sum(1 for v in r if v['extra'] > 0)}")
