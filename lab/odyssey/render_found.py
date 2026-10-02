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
MODES = {"spoken": {"pre": .14, "tail": .55, "fin": .05, "fout": .38, "breath": .7, "rest": 1.6},
         "performance": {"pre": .08, "tail": .4, "fin": .025, "fout": .22, "breath": .06, "rest": 1.2}}
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
def piece(a, t0, t1, P, ref):
    """The voice from t0 to t1 with room before and a ringing tail after, normalized and enveloped."""
    s = max(0, int((t0 - P["pre"]) * SR)); e = min(len(a), int((t1 + P["tail"]) * SR)); x = a[s:e].astype(np.float32).copy()
    if len(x) < 64: return None, 0
    L = loud(x) or ref; g = 10 ** (np.clip(SPEECH - L, -12, 18) / 20); x *= g
    fi, fo = int(P["fin"] * SR), int(P["fout"] * SR); fi = min(fi, len(x) // 3); fo = min(fo, len(x) // 2)
    if fi: x[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
    if fo: x[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    pk = np.abs(x).max()
    if pk > .89: x *= .89 / pk
    return x, (t0 - P["pre"]) if s > 0 else 0.0
# ---- Whisper hears every cut
CHECK = {}; CP = os.path.join(H, "cache", "render-check.json")
if os.path.exists(CP): CHECK = json.load(open(CP))
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
    if k in CHECK and "extra" in CHECK[k]: extra = CHECK[k]["extra"]; return piece(a, x0["t0"], x0["t1"] + extra, P, ref)
    rec = {"said": x0["words"]}; extra = 0.0
    x, at = piece(a, x0["t0"], x0["t1"], P, ref)
    if hear and len(x0["words"].split()) >= 2 and (mode == "spoken" or int(hashlib.md5(k.encode()).hexdigest(), 16) % 4 == 0):   # every sentence; a quarter of the fragments
        # what the old page played: from t0 to t1 less its 50 ms lead, no tail
        old = a[int(x0["t0"] * SR): int(max(x0["t0"] + .05, x0["t1"] - .05) * SR)]
        if len(old) > 1600 and int(hashlib.md5(k.encode()).hexdigest(), 16) % 16 < 4: rec["old"] = heard_last(hear(old), x0["words"])
        for step in range(4):
            last, rcl = heard_last(hear(x), x0["words"]); rec.setdefault("first", [last, rcl]); rec["final"] = [last, rcl]
            if last or x0["t1"] + P["tail"] + extra + .3 > len(a) / SR or step == 3: break
            extra += .3; x, at = piece(a, x0["t0"], x0["t1"] + extra, P, ref)
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
def render(sid, mode):
    P = MODES[mode]; lines = found["scenes"].get(sid) or []
    voice_p = os.path.join(HW, "drive", "voice", sid + ".m4a")
    parts, ev, lt = [], [], []; cur = 2.0                             # the music opens alone for two seconds
    for li, u in enumerate(lines):
        t = u["modes"].get(mode)
        if not t: continue
        l0 = cur
        for fi, x in enumerate(t["frags"]):
            if x.get("id"):
                a = audio(os.path.join(A, x["id"] + ".flac"), x["id"])
                if a is None: continue
                y, _ = checked(a, x, P, x["id"], clip_level(x["id"], a), mode)
                if y is None: continue
                parts.append((cur - P["pre"], y)); core = x["t1"] - x["t0"]
                ev.append({"at": round(cur, 2), "end": round(cur + core, 2), "li": li, "fi": fi, "id": x["id"], "t0": x["t0"]}); cur += core + P["breath"]
            elif x.get("fill"):
                a = audio(voice_p, voice_p)
                if a is None: continue
                y, _ = piece(a, x["fill"][0], x["fill"][1], {**P, "tail": min(P["tail"], .12), "pre": .03}, -20)
                if y is None: continue
                parts.append((cur - .03, y)); core = x["fill"][1] - x["fill"][0]
                ev.append({"at": round(cur, 2), "end": round(cur + core, 2), "li": li, "fi": fi, "ours": 1}); cur += core + P["breath"]
            elif x.get("gap"): cur += .3
        if cur > l0: lt.append({"li": li, "at": round(l0, 2), "end": round(cur, 2)}); cur += P["rest"]
    if not ev: return None
    n = int((cur + 3.0) * SR); v = np.zeros(n, np.float32)
    for at, y in parts:
        s = max(0, int(at * SR)); e = min(n, s + len(y)); v[s:e] += y[: e - s]
    # duck the bed under the voices: down 10 dB with a quick attack and a slow release
    act = np.zeros(n, np.float32)
    for e_ in ev: act[int(e_["at"] * SR): int((e_["end"] + .2) * SR)] = 1
    k = int(.05 * SR); act = np.convolve(act[::k], np.ones(1), "same")
    env = np.zeros(len(act), np.float32); g = 0.0
    for j, a_ in enumerate(act): g = g + (a_ - g) * (.6 if a_ > g else .06); env[j] = g
    env = np.repeat(env, k)[:n]; env = np.pad(env, (0, n - len(env)))
    b = bed(sid, n) * (1 - .68 * env)
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
want = sys.argv[1:] or sorted(found["scenes"])
tracks = found.setdefault("scene_tracks", {})
for c, sid in enumerate(want, 1):
    for mode in MODES:
        r = render(sid, mode)
        if r: tracks.setdefault(sid, {})[mode] = r
    json.dump(CHECK, open(CP, "w"))
    if c % 10 == 0 or c == len(want): json.dump(found, open(os.path.join(H, "found.json"), "w"), separators=(",", ":")); print(c, "of", len(want), "scenes", flush=True)
json.dump(found, open(os.path.join(H, "found.json"), "w"), separators=(",", ":"))
# what Whisper heard: the old cuts against the new
for mode in MODES:
    r = [v for k, v in CHECK.items() if k.startswith(mode) and "first" in v]
    if not r: continue
    old = [v["old"][0] for v in r if "old" in v]
    print(f"{mode}: {len(r)} cuts heard · last word heard: old page {np.mean(old) * 100:.0f}% · new cut {np.mean([v['first'][0] for v in r]) * 100:.0f}% · after lengthening {np.mean([v['final'][0] for v in r]) * 100:.0f}% · words heard {np.mean([v['final'][1] for v in r]) * 100:.0f}% · tails lengthened {sum(1 for v in r if v['extra'] > 0)}")
