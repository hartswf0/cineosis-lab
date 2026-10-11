"""PILOT · render: the cut as one film file, so nothing loads, stalls or drifts while it plays.
  title    the Mars ground, the episode's name
  narr     the narrator's voice over the archive shots that picture what it names, held, slowly pushed in, printed in one Mars duotone
  talk     the stage: the Mars ground running on, BIG HANK left and W.A.L.T.-E right always, paper cut-outs moving as their clips moved;
           who speaks is lit and lifts with the voice, who listens dims; their line under them, their name in their colour
  chorus   a citizen of the Republic: an archival person in their own picture and sound, untinted, with a lower third
  end      the ground, and what comes next
One subtitle at a time. No music: voices, and the archive's own room under them.
Writes republic/pilot/<ep>.mp4 (960x540, 24 fps).   usage: republic/.tts/bin/python republic/pilot/render.py ep01"""
import json, os, subprocess, sys, colorsys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); L = os.path.dirname(R)
EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"; cut = json.load(open(os.path.join(H, EP + ".picked.json")))
SCORED = "--score" in sys.argv and cut.get("score")                 # the version that thinks with sound (score/fit.py wrote the plan)
LIBS = {t["id"]: t for t in json.load(open(os.path.join(L, "score", "library.json")))["tracks"]} if SCORED else {}
PL = json.load(open(os.path.join(R, "planes.json")))
W_, H_, FPS, SR = 960, 540, 24, 48000
F = "/System/Library/Fonts/Supplemental/"
def font(n, s):
    for f in n:
        try: return ImageFont.truetype(F + f, s)
        except Exception: pass
    return ImageFont.load_default()
SUB = font(["Georgia Italic.ttf"], 30); NARR = font(["Georgia Italic.ttf"], 27); LAB = font(["Courier New Bold.ttf", "Arial Bold.ttf"], 17)
BIG = font(["Arial Black.ttf", "Impact.ttf"], 58); KICK = font(["Courier New Bold.ttf"], 18); SMALL = font(["Courier New.ttf"], 15)
DARK, LIGHT = np.array([22, 9, 6], np.float32), np.array([244, 178, 128], np.float32)
def duotone(fr):
    l = (fr.astype(np.float32) @ np.array([.299, .587, .114], np.float32)) / 255.; l = np.clip((l - .06) / .9, 0, 1) ** .9
    return (DARK + (LIGHT - DARK) * l[..., None]).astype(np.uint8)
def frames(v, t, dur):
    n = int(round(dur * FPS))
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", v, "-t", f"{dur + .5:.3f}", "-vf", f"scale={W_}:{H_}:force_original_aspect_ratio=increase,crop={W_}:{H_},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=300)
    a = np.frombuffer(p.stdout, np.uint8); k = len(a) // (W_ * H_ * 3)
    fr = a[: k * W_ * H_ * 3].reshape(k, H_, W_, 3) if k else np.zeros((1, H_, W_, 3), np.uint8)
    if len(fr) >= n: return [fr[i] for i in range(n)]
    per = max(1, 2 * (len(fr) - 1)); return [fr[(i % per) if (i % per) < len(fr) else per - (i % per)] for i in range(n)]   # too short: forward, then back
def sound(v, t, dur):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", v, "-t", f"{dur:.3f}", "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, timeout=300)
    a = np.frombuffer(p.stdout, np.float32).copy(); n = int(dur * SR); a = np.pad(a, (0, max(0, n - len(a))))[:n]
    f = min(len(a) // 4, int(.08 * SR))
    if f: a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    return a
def push(img, u):                                                        # the slow push-in: 0 → 6% over the shot
    z = 1 + .06 * u; w, h = int(W_ / z), int(H_ / z); x, y = (W_ - w) // 2, (H_ - h) // 2
    return img.crop((x, y, x + w, y + h)).resize((W_, H_), Image.BILINEAR)
def text_block(d, txt, f, y, fill, width=820, stroke=3):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) > width and cur: lines.append(cur); cur = w
        else: cur = t
    lines.append(cur); lh = f.size + 8; y0 = y - lh * len(lines)
    for i, l in enumerate(lines): d.text((W_ / 2, y0 + i * lh), l, font=f, fill=fill, anchor="ma", stroke_width=stroke, stroke_fill=(0, 0, 0))
    return y0
def hexcolor(who):
    h = 0
    for c in who: h = (h * 31 + ord(c)) % 360
    r, g, b = colorsys.hls_to_rgb(h / 360, .64, .78); return (int(r * 255), int(g * 255), int(b * 255))
# ---- the cast: sprite frames, paper-edged, at their stage height
def puppet(name, height):
    f = PL["cast"][name][0]; sp = f.get("sp")
    if sp: sh = Image.open(os.path.join(L, sp["f"])).convert("RGBA"); fr = [sh.crop((k * sp["w"], 0, (k + 1) * sp["w"], sp["h"])) for k in range(sp["n"])]
    else: fr = [Image.open(os.path.join(L, f["f"].split("?")[0])).convert("RGBA")]
    out = []
    for im in fr:
        s = height / im.height; im = im.resize((max(1, int(im.width * s)), height), Image.LANCZOS)
        a = im.split()[3]; edge = a.filter(ImageFilter.MaxFilter(5)); paper = Image.new("RGBA", im.size, (241, 230, 210, 255)); paper.putalpha(edge)
        base = Image.new("RGBA", (im.width + 8, im.height + 8), (0, 0, 0, 0)); base.alpha_composite(paper, (4, 4)); base.alpha_composite(im, (4, 4)); out.append(base)
    return out
st = cut["stage"]; CAST = {st["left"]: {"fr": puppet(st["left"], 250), "x": .27}, st["right"]: {"fr": puppet(st["right"], 215), "x": .73}}
for c in CAST.values(): c.update(phase=0.0, lift=0.0)
EPS_ = {}
for fn in ("planes-eps.json", "planes-eps2.json"): EPS_.update(json.load(open(os.path.join(R, fn)))["episodes"])
gp = next(a for p in EPS_[cut["id"]]["places"] for a in p["alts"] if a["f"] == cut["stage"]["ground"])
def probe(u): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", u], capture_output=True, text=True).stdout.strip() or 0)
REEL = [gp] + [a for p in EPS_[cut["id"]]["places"][: cut["stage"].get("places", 2)] for a in p["alts"] if a is not gp]   # the stage is the land only: no strangers behind the puppets
REEL = [dict(v=a["video"], d=probe(a["video"]), t=a.get("t", 0)) for a in REEL]; REEL = [a for a in REEL if a["d"] > 3]
ground = {"i": 0, "at": max(0, REEL[0]["t"] - 1)}
def ground_take(dur):
    """the stage keeps running: the next stretch of the episode's places, moving on when a clip is spent"""
    for _ in range(len(REEL)):
        g = REEL[ground["i"] % len(REEL)]
        if g["d"] - ground["at"] >= min(dur, g["d"] * .6): v, t = g["v"], ground["at"]; ground["at"] += dur; return v, t
        ground["i"] += 1; ground["at"] = 0.3
    g = REEL[ground["i"] % len(REEL)]; return g["v"], 0.3
# ---- the timeline
segs = []
for b in cut["beats"]:
    if b["k"] == "title": segs.append(("title", 4.0, b))
    elif b["k"] == "narr": segs.append(("narr", b["d"] + .7, b))
    elif b["k"] == "talk": segs.append(("talk", b["d"] + .3, b))
    elif b["k"] == "chorus": segs.append(("chorus", b["d"] + .2, b))
    elif b["k"] == "end": segs.append(("end", 4.0, b))
total = sum(d for _, d, _ in segs); audio = np.zeros(int(total * SR) + SR, np.float32)
music = np.zeros_like(audio); gain = np.full(len(audio), .3, np.float32); credits = []
if SCORED:
    # the movements, as fit.py cut them: a title, a narration (with the exchange after it), the end
    starts, t_ = [], 0.0
    for kind, dur, b in segs:
        if kind in ("title", "narr", "end") or not starts: starts.append([t_, 0.0])
        starts[-1][1] += dur; t_ += dur
    for (st_, du), pl in zip(starts, cut["score"]):
        tr = LIBS[pl["track"]]; src = os.path.join(L, tr["f"]); xf = 1.2
        y = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{pl['offset']:.2f}", "-i", src, "-t", f"{du + xf:.2f}", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        y = np.frombuffer(y, np.float32).copy(); f = int(xf * SR)
        if len(y) > 2 * f: y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
        a = int(max(0, st_ - xf / 2) * SR); music[a: a + len(y)] += y[: len(music) - a]
        if not credits or credits[-1][1] != pl["title"]: credits.append((st_, pl["title"], ", ".join(pl["mood"])))
    music /= (np.percentile(np.abs(music), 99.5) + 1e-6)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W_}x{H_}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p", os.path.join(H, EP + "-video.mp4")], stdin=subprocess.PIPE)
t0 = 0.0; prev_who = None
for kind, dur, b in segs:
    n = int(round(dur * FPS)); s0 = int(t0 * SR)
    if kind in ("title", "end", "talk"):
        gv, gt = ground_take(dur); fr = frames(gv, gt, dur); bed = sound(gv, gt, dur) * (.18 if kind != "talk" else .07)
    elif kind == "narr":
        shots = b["shots"]; each = dur / max(1, len(shots)); fr = []; bed = np.zeros(int(dur * SR), np.float32)
        for k, s in enumerate(shots):
            got = frames(s["v"], s["in"], each); fr += got; bed[int(k * each * SR): int(k * each * SR) + int(each * SR)] = sound(s["v"], s["in"], each)[: len(bed[int(k * each * SR): int(k * each * SR) + int(each * SR)])] * .1
        fr = (fr + fr[-1:] * n)[:n]
    else:
        fr = frames(b["v"], b["in"], dur); bed = sound(b["v"], b["in"], dur); pk = np.abs(bed).max() + 1e-6; bed = bed / pk * .7
    audio[s0: s0 + len(bed)] += bed[: len(audio) - s0]
    if SCORED:   # the score never sits on a voice: low under the cast and narrator, gone under a citizen, up where no one speaks
        g = {"title": .42, "end": .42, "narr": .10, "talk": .07, "chorus": .025}[kind]; gain[s0: s0 + int(dur * SR)] = g
        if kind == "narr": gain[s0: s0 + int(.35 * SR)] = .3
    env = b.get("e", ""); voice = None
    if b.get("wav"):
        y, sr = sf.read(os.path.join(R, b["wav"]), dtype="float32"); y = y if y.ndim == 1 else y.mean(1)
        off = s0 + int((.35 if kind == "narr" else .08) * SR); audio[off: off + len(y)] += y[: len(audio) - off] * .9
    for i in range(n):
        u = i / max(1, n - 1); tt = i / FPS
        f = fr[i]
        if kind != "chorus": f = duotone(f)
        img = Image.fromarray(f)
        if kind == "narr":
            each_n = n / max(1, len(b["shots"])); img = push(img, (i % each_n) / max(1, each_n))
        img = img.convert("RGBA"); d = ImageDraw.Draw(img)
        if kind == "talk":
            vt = tt - .08; lv = 0.0
            if env and 0 <= vt <= b["d"]: q = min(39, int(vt / b["d"] * 40)); lv = int(env[q], 36) / 35
            for name, c in CAST.items():
                speaking = name == b["who"]
                c["phase"] += (FPS * (.25 + 1.3 * lv) if speaking else FPS * .3) / FPS
                c["lift"] += ((lv if speaking else 0) - c["lift"]) * .35
                frs = c["fr"]; m = len(frs); per = max(1, 2 * (m - 1)); k = int(c["phase"]) % per; im = frs[k if k < m else per - k]
                if not speaking: im = Image.fromarray((np.asarray(im).astype(np.float32) * [.62, .62, .62, 1]).astype(np.uint8))
                x = int(c["x"] * W_ - im.width / 2); y = int(H_ * .80 - im.height - c["lift"] * 8); c["top"] = (int(c["x"] * W_), y)
                sh = Image.new("RGBA", (im.width, 26), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((im.width * .15, 4, im.width * .85, 22), fill=(0, 0, 0, 110)); img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (x, int(H_ * .80) - 16))
                img.alpha_composite(im, (x, y))
            band = Image.new("RGBA", (W_, int(H_ * .2)), (8, 4, 3, 215)); img.alpha_composite(band, (0, int(H_ * .80))); d = ImageDraw.Draw(img)
            text_block(d, b["text"], SUB, H_ - 18, (255, 255, 255), stroke=0)
            lab = b["who"]; w = d.textlength(lab, font=LAB) + 14; cx, cy = CAST[lab]["top"]
            d.rectangle((cx - w / 2, cy - 30, cx + w / 2, cy - 8), fill=hexcolor(lab)); d.text((cx, cy - 27), lab, font=LAB, fill=(0, 0, 0), anchor="ma")
        elif kind == "narr":
            band = Image.new("RGBA", (W_, int(H_ * .2)), (8, 4, 3, 200)); img.alpha_composite(band, (0, int(H_ * .80))); d = ImageDraw.Draw(img)
            if tt > .3: text_block(d, b["text"], NARR, H_ - 18, (246, 236, 222), stroke=0)
            d.text((22, 18), "NARRATOR", font=LAB, fill=(246, 236, 222), stroke_width=2, stroke_fill=(0, 0, 0))
        elif kind == "chorus":
            d.rectangle((0, 22, 420, 74), fill=(12, 8, 6, 210)); d.text((18, 28), "A CITIZEN OF THE REPUBLIC", font=LAB, fill=(242, 193, 78)); d.text((18, 50), f"{b['src'][:44]}{' · ' + str(b['y']) if b.get('y') else ''}", font=SMALL, fill=(220, 210, 200))
            text_block(d, "“" + b["said"] + "”", SUB, H_ - 22, (255, 240, 200))
        elif kind == "title":
            a = min(1, tt / .8, (dur - tt) / .6); ov = Image.new("RGBA", img.size, (0, 0, 0, int(120 * a))); img.alpha_composite(ov); d = ImageDraw.Draw(img)
            d.text((W_ / 2, H_ / 2 - 52), cut["kicker"], font=KICK, fill=(224, 87, 42, int(255 * a)), anchor="ma"); d.text((W_ / 2, H_ / 2 - 20), cut["title"], font=BIG, fill=(255, 255, 255, int(255 * a)), anchor="ma")
        elif kind == "end":
            a = min(1, tt / .8); ov = Image.new("RGBA", img.size, (0, 0, 0, int(150 * a))); img.alpha_composite(ov); d = ImageDraw.Draw(img)
            d.text((W_ / 2, H_ / 2 - 10), "TO BE CONTINUED", font=BIG, fill=(255, 255, 255, int(255 * a)), anchor="ma")
            d.text((W_ / 2, H_ / 2 + 66), "voices: Kokoro · pictures and citizens: the Moving Image Archive · words: the Republic writers' room", font=SMALL, fill=(220, 210, 200, int(255 * a)), anchor="ma")
        if SCORED:
            now_ = t0 + tt
            for (cs, ct, cmood) in credits:
                if cs <= now_ < cs + 3.5 and kind != "chorus":
                    a_ = min(1, (now_ - cs) / .4, (cs + 3.5 - now_) / .5); d = ImageDraw.Draw(img)
                    d.text((W_ - 18, 18), f"SCORE · {ct}", font=LAB, fill=(241, 230, 210, int(255 * a_)), anchor="ra", stroke_width=2, stroke_fill=(0, 0, 0))
                    d.text((W_ - 18, 40), f"D-A-E · Honed for Film · {cmood}", font=SMALL, fill=(220, 200, 180, int(230 * a_)), anchor="ra", stroke_width=2, stroke_fill=(0, 0, 0))
        if i < 4 and kind in ("narr", "chorus", "title"): img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, int(255 * (1 - i / 4)))))
        enc.stdin.write(img.convert("RGB").tobytes())
    t0 += dur; print(f"  {kind:6} {dur:5.1f}s  {(b.get('text') or b.get('said') or '')[:50]}", flush=True)
enc.stdin.close(); enc.wait()
if SCORED:
    k_ = int(.3 * SR); gs = np.convolve(gain, np.ones(k_) / k_, mode="same"); audio += music * gs
pk = np.abs(audio).max() + 1e-6; audio = audio / pk * .9
sf.write(os.path.join(H, EP + "-audio.wav"), audio[: int(total * SR)], SR)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(H, EP + "-video.mp4"), "-i", os.path.join(H, EP + "-audio.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-af", "loudnorm=I=-16:TP=-1.5", "-shortest", "-movflags", "+faststart", os.path.join(H, EP + ("-score" if SCORED else "") + ".mp4")], check=True)
os.unlink(os.path.join(H, EP + "-video.mp4")); os.unlink(os.path.join(H, EP + "-audio.wav"))
print(f"{EP}{'-score' if SCORED else ''}.mp4 · {total:.0f}s")
