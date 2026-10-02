"""THE ARCHIVE OF SMALL WONDERS: a Wes Anderson picture cut from the archive (wes/score.py chose the shots; this cuts the film).
  material  the most Andersonian shots of the best films (no more than two from a film), in seven chapters
  order     inside a chapter, CLIP decides: each next shot is the one nearest the last in image space (the match cut), so the
            chapter rhymes in form and colour; the chapter opens on its most symmetrical shot
  picture   4:3, letterbox removed, a soft pastel grade (colour films only); straight cuts inside a chapter, a whip pan into
            each chapter card; the cards are pastel, set in Jost, centred
  sound     the archive's own music: CLAP finds the clips that sound most like his scores (pizzicato strings, harpsichord, a
            music box, a small brass march), and they are laid end to end with crossfades, loudness-normalized
Writes wes/archive-of-small-wonders.mp4 and wes/film.json (the shot list).   usage: .venv/bin/python wes/make_film.py"""
import json, os, subprocess, urllib.request, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(L, "wes"); T = os.path.join(D, "film-cache"); os.makedirs(T, exist_ok=True)
R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"; W_, H_, FPS, SHOT, CARD, WHIP = 960, 720, 24, 2.6, 2.8, .28
wes = json.load(open(os.path.join(D, "wes.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
bars = {c[0]: c[4:8] for c in json.load(open(os.path.join(L, "aspect", "clips.json"))) if len(c) > 4}
# ---- CLIP space (the same as score.py)
lib = json.load(open(os.path.join(L, "markov", "library.json"))); sc = lib["scale"]
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * sc
EMB = {s["id"]: e for s, e in zip(lib["shots"], E1)}
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy")).astype(np.float32)): EMB.setdefault(i, e)
emb = lambda i: (lambda e: e / (np.linalg.norm(e) + 1e-9))(EMB[i]) if i in EMB else None
# ---- the chapters and their shots
CH = [("title", "The Title Card"), ("symmetry", "The Facade"), ("pastel", "The Pastel"), ("overhead", "The Overhead"), ("uniform", "The Uniforms"), ("diorama", "The Miniature"), ("facing", "The Face")]
NUM = ["One", "Two", "Three", "Four", "Five", "Six", "Seven"]
# every candidate's own picture, measured: no near-white, near-black or flat frames; for The Face, a real face
import cv2
FC = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); _q = {}
def fetch(i):
    src = os.path.join(T, i + ".mp4")
    if not os.path.exists(src) or os.path.getsize(src) < 1000:
        subprocess.run(["curl", "-sfL", "--retry", "3", "-A", "cineosis-44-research", "-o", src, R2 + V[i][0]])
    return src if os.path.exists(src) and os.path.getsize(src) > 1000 else None
def frame(src, t):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=320:240,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(240, 320) if len(raw) == 320 * 240 else None
def quality(i, k):
    """The footage itself, not its thumbnail: several windows of the clip, each sampled three times; the window with real tone
    (and, for The Face, a face) is the one the film uses."""
    key = (i, k == "facing")
    if key in _q: return _q[key]
    src = fetch(i)
    if not src: _q[key] = None; return None
    d = float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout or 0)
    if d < SHOT + .2: _q[key] = None; return None
    best = None
    for st in sorted({max(0.0, min(float(V[i][1] or 0), d - SHOT - .1)), .3, d * .3, d * .55, max(0.0, d - SHOT - .4)}):
        fr = [frame(src, st + o) for o in (.3, 1.2, 2.1)]; fr = [f for f in fr if f is not None]
        if not fr: continue
        light = np.mean([f.mean() for f in fr]) / 255; tone = np.mean([f.std() for f in fr]) / 255
        face = np.mean([max([w / 320 for x, y, w, h in FC.detectMultiScale(cv2.equalizeHist(f), 1.1, 6, minSize=(24, 24))] or [0]) for f in fr])
        ok = .14 < light < .76 and tone > .12 and (face >= .1 or k != "facing")
        sc = tone - abs(light - .47) * .5 + (face if k == "facing" else 0)
        if ok and (not best or sc > best["score"]): best = {"start": round(st, 2), "light": light, "tone": tone, "face": face, "score": sc}
    _q[key] = best; return best
def good(x, k): return quality(x["id"], k) is not None
used_film, used = {}, set(); plan = []
for (k, name), num in zip(CH, NUM):
    src_list = wes["chapters"][k] + (wes["best"] if k == "facing" else [])
    pool = [x for x in src_list if x["id"] in V and x["id"] in EMB and x["id"] not in used and used_film.get(x["src"], 0) < 2 and (k == "title" or x.get("colour", 1) > .12) and good(x, k)]
    if len(pool) < 5: pool += [x for x in src_list if x["id"] in V and x["id"] in EMB and x["id"] not in used and x not in pool and good(x, k)]
    pool = pool[:14]; seq = [max(pool[:6], key=lambda x: x.get("sym", 0))]; rest = [x for x in pool if x is not seq[0]]
    while len(seq) < 5 and rest:                                       # the match cut: nearest in CLIP space to the last shot
        e = emb(seq[-1]["id"]); nxt = max(rest, key=lambda x: float(emb(x["id"]) @ e)); seq.append(nxt); rest.remove(nxt)
    for x in seq: used.add(x["id"]); used_film[x["src"]] = used_film.get(x["src"], 0) + 1
    plan.append({"chapter": num, "name": name, "shots": [{"id": x["id"], "title": x["title"], "year": x["year"], "colour": x.get("colour", 1), "start": quality(x["id"], k)["start"]} for x in seq]})
    print(f"Chapter {num} · {name}: " + " | ".join(f"{x['title'][:24]}" for x in seq), flush=True)
# ---- the cards
FT = os.path.join(T, "Jost.ttf")
if not os.path.exists(FT): urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/jost/Jost%5Bwght%5D.ttf", FT)
COL = [(234, 180, 180), (185, 217, 198), (226, 189, 90), (246, 236, 223), (217, 140, 143), (199, 214, 231), (240, 214, 170)]
def card(path, small, big, sub=None, col=(234, 180, 180)):
    im = Image.new("RGB", (W_, H_), col); d = ImageDraw.Draw(im); ink = (59, 42, 42)
    fs = ImageFont.truetype(FT, 22); fs.set_variation_by_axes([500]); fb = ImageFont.truetype(FT, 64); fb.set_variation_by_axes([500]); fsub = ImageFont.truetype(FT, 24); fsub.set_variation_by_axes([300])
    def ctext(y, t, f, sp):
        t = " ".join(t) if sp else t; w = d.textlength(t, font=f); d.text(((W_ - w) / 2, y), t, font=f, fill=ink)
    d.rectangle([60, 60, W_ - 60, H_ - 60], outline=ink, width=3); d.rectangle([72, 72, W_ - 72, H_ - 72], outline=ink, width=1)
    ctext(H_ / 2 - 80, small.upper(), fs, True)
    lines = []
    for word in big.upper().split():
        if lines and d.textlength(lines[-1] + " " + word, font=fb) < W_ - 220: lines[-1] += " " + word
        else: lines.append(word)
    for n, ln in enumerate(lines): ctext(H_ / 2 - 30 + n * 76, ln, fb, False)
    if sub:
        for n, ln in enumerate(sub): ctext(H_ / 2 - 20 + len(lines) * 76 + 10 + n * 34, ln, fsub, False)
    im.save(path)
# ---- the shots: fetched, cut, cropped to 4:3 without the letterbox, graded
def shot_clip(x, k):
    i = x["id"]; src = fetch(i); out = os.path.join(T, f"s_{k:03d}.mp4")
    t, b, l, r = bars.get(i, [0, 0, 0, 0])
    crop = f"crop=iw*{1 - l - r:.4f}:ih*{1 - t - b:.4f}:iw*{l:.4f}:ih*{t:.4f},"
    level = "normalize=blackpt=black:whitept=white:smoothing=48:independence=0.3,"   # faded film brought back to true black and white
    grade = level + ("eq=saturation=1.18:contrast=1.04,colorbalance=rs=.025:bs=-.015," if x.get("colour", 1) > .12 else "eq=contrast=1.04,")
    vf = f"{crop}scale={W_}:{H_}:force_original_aspect_ratio=increase,crop={W_}:{H_},{grade}fps={FPS},format=yuv420p"
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{x['start']:.2f}", "-i", src, "-t", f"{SHOT}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18", out], check=True)
    return out
def still(png, k, dur):
    out = os.path.join(T, f"c_{k:03d}.mp4")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-i", png, "-t", f"{dur}", "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "18", out], check=True); return out
segs = []   # (file, how it enters: cut or whip)
films_used = sorted({(s["title"], s["year"]) for c in plan for s in c["shots"]}, key=lambda t: str(t[1]))
card(os.path.join(T, "c_open.png"), "The Cineosis Archive presents", "The Archive of Small Wonders", ["a picture in seven chapters", "assembled from the Moving Image Archive"], COL[3])
segs.append((still(os.path.join(T, "c_open.png"), 0, 4.0), "cut"))
for n, c in enumerate(plan):
    card(os.path.join(T, f"c_{n}.png"), f"Chapter {c['chapter']}", c["name"], None, COL[n % len(COL)])
    segs.append((still(os.path.join(T, f"c_{n}.png"), n + 1, CARD), "whip"))
    for k, x in enumerate(c["shots"]):
        try: segs.append((shot_clip(x, n * 10 + k), "cut"))
        except Exception as e: print("skipped", x["title"], e)
card(os.path.join(T, "c_end.png"), "The End", "With thanks to", [(t if len(t) < 44 else t[:42] + "…") + (f" ({y})" if y else "") for t, y in films_used[:6]] + [f"and {len(films_used) - 6} more films of the Moving Image Archive"] if len(films_used) > 6 else [], COL[3])
segs.append((still(os.path.join(T, "c_end.png"), 99, 6.0), "whip"))
# join: straight cuts inside a chapter; into each card a whip pan (the last frame of the shot slides off as the card slides in).
# Every piece is encoded alike, so the film is one plain concatenation.
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-video_track_timescale", "12288"]
def norm(f, k):
    out = os.path.join(T, f"n_{k:03d}.mp4"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", f, "-vf", f"scale={W_}:{H_},setsar=1,fps={FPS},format=yuv420p", *ENC, out], check=True); return out
dur = lambda f: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout or 0)
parts, total = [], 0.0
for k, (f, how) in enumerate(segs):
    if how == "whip" and parts:
        last = os.path.join(T, f"last_{k:03d}.png"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-sseof", "-0.1", "-i", parts[-1], "-frames:v", "1", "-update", "1", last], check=True)
        first = os.path.join(T, f"first_{k:03d}.png"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", f, "-frames:v", "1", "-update", "1", first], check=True)
        wp = os.path.join(T, f"w_{k:03d}.mp4")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-t", "1", "-i", last, "-loop", "1", "-t", "1", "-i", first, "-filter_complex",
                        f"[0:v]scale={W_}:{H_},setsar=1,fps={FPS}[a];[1:v]scale={W_}:{H_},setsar=1,fps={FPS}[b];[a][b]xfade=transition=slideleft:duration={WHIP}:offset=0,trim=0:{WHIP},format=yuv420p[v]",
                        "-map", "[v]", *ENC, wp], check=True)
        parts.append(wp); total += dur(wp)
    n = norm(f, k); parts.append(n); total += dur(n)
lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
cur = os.path.join(T, "picture.mp4"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", cur], check=True); total = dur(cur)
print(f"picture {total:.1f} s from {len(parts)} pieces", flush=True)
# ---- the score: the archive's own music, chosen by CLAP for his sound
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import torch
from transformers import ClapModel, ClapProcessor
E = os.path.join(L, "odyssey", "cache", "ears"); eids = json.load(open(os.path.join(E, "ids.json"))); CL = np.load(os.path.join(E, "clap.npy")).astype(np.float32); kind = json.load(open(os.path.join(E, "kind.json")))
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
Q = ["playful pizzicato strings", "a harpsichord playing a light melody", "a music box melody", "a small brass band playing a jaunty march", "whimsical baroque chamber music"]
with torch.no_grad(): q = cm.get_text_features(**cp(text=Q, return_tensors="pt", padding=True)); q = (q / q.norm(dim=-1, keepdim=True)).numpy()
mus = [n for n, i in enumerate(eids) if kind.get(i, {}).get("k") == "music" and os.path.exists(os.path.join(L, "odyssey", "cache", "aud", i + ".flac"))]
X = CL[mus]; X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9; s = (X @ q.T).max(1)
need = int(total // 24) + 2; pick = [eids[mus[j]] for j in np.argsort(-s)[: need * 3]]
seen, music = set(), []
for i in pick:                                                         # different pieces, not two cuts of one reel
    v = V.get(i, ["", 0])[0].split("/clips/")[0]
    if v in seen: continue
    seen.add(v); music.append(i)
    if len(music) >= need: break
print("score:", music, flush=True)
ins = sum([["-i", os.path.join(L, "odyssey", "cache", "aud", i + ".flac")] for i in music], [])
fc = "".join(f"[{k}:a]atrim=0:26,asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=stereo[a{k}];" for k in range(len(music)))
chain = "[a0]"
for k in range(1, len(music)): fc += f"{chain}[a{k}]acrossfade=d=3:c1=tri:c2=tri[x{k}];"; chain = f"[x{k}]"
fc += f"{chain}atrim=0:{total:.2f},afade=t=in:d=1.5,afade=t=out:st={total - 3:.2f}:d=3,loudnorm=I=-17:TP=-1.5[m]"
mus_wav = os.path.join(T, "score.wav")
subprocess.run(["ffmpeg", "-v", "quiet", "-y", *ins, "-filter_complex", fc, "-map", "[m]", mus_wav], check=True)
out = os.path.join(D, "archive-of-small-wonders.mp4")
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", cur, "-i", mus_wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-maxrate", "1400k", "-bufsize", "2800k",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
json.dump({"title": "The Archive of Small Wonders", "chapters": plan, "score": music, "films": films_used, "seconds": round(total, 1)}, open(os.path.join(D, "film.json"), "w"), ensure_ascii=False, indent=1)
print("wrote", out, round(os.path.getsize(out) / 1e6, 1), "MB ·", round(total, 1), "s")
