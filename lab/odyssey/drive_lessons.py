"""The spoken lessons for the Odyssey Drive: short pieces that sit between the found scenes, read by two voices, over the book's
music, rendered offline so the drive plays from files (screen locked, steering-wheel buttons, any car).
  herald   (Daniel, English) where we are: the book and its prologue at a book's first scene, then the scene in a sentence
  greek    the scene's key line in Homer's Greek (Melina; modern Greek pronunciation of the ancient words, accents kept, breathings
           dropped), then word by word, the Greek and then its meaning, then the line again at speaking pace, then what it says
  theme    the word to carry: one of Homer's great words, said in Greek and explained, coming back across the books
Writes drive/<scene>-{herald,greek,theme}.m4a and drive/index.json (texts and durations).   usage: ~/.cache/mlxw-venv/bin/python drive_lessons.py"""
import json, os, re, subprocess, threading, unicodedata, urllib.parse, concurrent.futures as cf
LOCK = threading.Lock()
import numpy as np, soundfile as sf, pyloudnorm as pyln
H = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(H, "drive"); TMP = os.path.join(H, "cache", "tts"); SR = 44100
HW = os.path.expanduser("~/Downloads/odyssey-halfworld"); os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)
radio = json.load(open(os.path.join(H, "radio.json"))); greek = json.load(open(os.path.join(H, "greek.json"))); meter = pyln.Meter(SR)
def mono(s):
    """Homer's polytonic Greek in the single-accent spelling the Greek voice reads (breathings and circumflex marks dropped)."""
    d = unicodedata.normalize("NFD", s); d = "".join(c for c in d if c not in "̓̔ͅ").replace("̀", "́").replace("͂", "́")
    return unicodedata.normalize("NFC", d)
def say(text, voice, rate, key):
    p = os.path.join(TMP, key + ".aiff")
    with LOCK:
      if not os.path.exists(p):
        f = os.path.join(TMP, key + ".txt"); open(f, "w").write(text)
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", p, "-f", f], check=True)
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()
def gap(s): return np.zeros(int(s * SR), np.float32)
EN, GR = ("Daniel", 168), ("Melina", 118)
def short(g): return re.split(r"[;,]", g)[0].strip() if g else None
def bed_for(b, n, off):
    bk = next(x for x in radio["books"] if x["n"] == b); p = os.path.join(HW, urllib.parse.unquote(bk["track"].split("odyssey-halfworld/")[1]))
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", str(off), "-i", p, "-t", str(n / SR + 1), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    m = np.frombuffer(raw, np.float32).copy(); m = np.pad(m, (0, max(0, n - len(m))))[:n]
    L = meter.integrated_loudness(m) if len(m) > SR else -20
    return m * 10 ** ((-35 - (L if np.isfinite(L) else -20)) / 20)
def master(parts, b, off, path):
    v = np.concatenate([gap(.6)] + parts + [gap(.9)]); L = meter.integrated_loudness(v); v *= 10 ** ((-19 - L) / 20)
    n = len(v); f = np.ones(n, np.float32); k = min(n // 3, int(.8 * SR)); f[:k] = np.linspace(0, 1, k); f[-k:] = np.linspace(1, 0, k)
    mix = v + bed_for(b, n, off) * f; pk = np.abs(mix).max()
    if pk > .89: mix *= .89 / pk
    w = path[:-4] + ".wav"; sf.write(w, mix, SR)
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", w, "-c:a", "aac_at", "-b:a", "40k", "-ac", "1", path]); os.remove(w); return round(n / SR, 2)
def scene_job(job):
    b, k, sc, first, bk = job; sid = sc["id"]; g = greek.get(sid); out = {"id": sid}; off = (int(sid[-2:]) * 37) % 150
    # herald
    t = (f"Book {b}. {bk['title']}. {bk['prologue']} " if first else "") + f"Scene {k}. {sc['title']}. {sc['card']}"
    out["herald"] = {"text": t, "dur": master([say(t, *EN, f"{sid}-h")], b, off, os.path.join(OUT, f"{sid}-herald.m4a"))}
    if g and g["key"]["greek"]:
        kg = g["key"]; ws = [w for w in kg["words"] if short(w.get("means"))]
        parts = [say(f"In Homer's Greek. Book {b}, line {kg['n']}.", *EN, f"{sid}-g0"), gap(.5), say(mono(kg["greek"]), *GR, f"{sid}-g1"), gap(.9),
                 say("Word by word.", *EN, "word-by-word"), gap(.4)]
        for n, w in enumerate(ws):
            parts += [say(mono(w["w"]), GR[0], 105, f"{sid}-w{n}"), gap(.22), say(short(w["means"]), *EN, "gl-" + re.sub(r"\W+", "_", short(w["means"]))[:60]), gap(.45)]
        parts += [gap(.4), say(mono(kg["greek"]), GR[0], 150, f"{sid}-g2"), gap(.6), say(f"{kg['who']}: {kg['english']}", *EN, f"{sid}-g3")]
        out["greek"] = {"n": kg["n"], "greek": kg["greek"], "words": [[w["w"], short(w["means"])] for w in ws], "english": kg["english"], "who": kg["who"],
                        "dur": master(parts, b, off + 40, os.path.join(OUT, f"{sid}-greek.m4a"))}
    if g and g["theme"]:
        th = g["theme"]; parts = [say("The word to carry.", *EN, "carry"), gap(.4), say(mono(th["word"]), GR[0], 100, f"{sid}-t1"), gap(.5),
                                 say(f"{th['say']}. {th['means']}.", *EN, f"{sid}-t2"), gap(.5), say(mono(th["word"]), GR[0], 100, f"{sid}-t1")]
        out["theme"] = {"word": th["word"], "say": th["say"], "means": th["means"], "dur": master(parts, b, off + 80, os.path.join(OUT, f"{sid}-theme.m4a"))}
    return out
jobs = []
for bk in radio["books"]:
    for k, sc in enumerate(bk["scenes"], 1): jobs.append((bk["n"], k, sc, k == 1, bk))
index = {}
with cf.ThreadPoolExecutor(4) as ex:
    for n, r in enumerate(ex.map(scene_job, jobs), 1):
        index[r["id"]] = r
        if n % 20 == 0: print(n, "of", len(jobs), flush=True)
json.dump({"books": [{"n": bk["n"], "title": bk["title"], "scenes": [sc["id"] for sc in bk["scenes"]]} for bk in radio["books"]], "scenes": index},
          open(os.path.join(OUT, "index.json"), "w"), ensure_ascii=False, separators=(",", ":"))
tot = sum(v.get(p, {}).get("dur", 0) for v in index.values() for p in ("herald", "greek", "theme"))
print(f"lessons for {len(index)} scenes · {tot / 3600:.1f} hours of teaching voice")
