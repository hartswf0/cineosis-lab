"""SPACE CHICKEN: a deadpan science fiction, assembled from the archive. A farm hen is crated, launched by accident, looked after by a
junior mission-control crew and pursued by a galactic bureaucracy, then comes home to the grass she started on.
Every picture and every spoken word is archival (sponsored, educational, government and NASA films; one 1939 cartoon and one 1949
fiction film lend a line of sound); the story is made only by the cutting. The typed form cards are added. No colour grade: the
archive's own colour. Every window was checked on frame sheets; lines are cut on Whisper word times; picture and sound are cut
as separate inputs. Writes wes/space-chicken.mp4 and wes/space-cut.json (the edit list).   usage: python3 wes/space_cut.py"""
import json, os, subprocess, urllib.request
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(D, "film-cache"); W_, H_, FPS = 960, 720, 24
DIRS = [os.path.join(D, "space"), os.path.join(D, "chicken")]
def clip(k):
    for d in DIRS:
        for f in os.listdir(d):
            if f.startswith(k) and f.endswith(".mp4"): return os.path.join(d, f)
    raise FileNotFoundError(k)
FONTS = {}
for name, url in [("reg", "https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Regular.ttf"), ("bold", "https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Bold.ttf")]:
    p = os.path.join(T, f"courier-{name}.ttf")
    if not os.path.exists(p): urllib.request.urlretrieve(url, p)
    FONTS[name] = p
# (video asset, v0, v1, sound asset or None for the clip's own sound, a0, a1 or None for room tone only, card, job)
C = None
EDIT = [
  (C, 0, 3.5, None, 0, 0, ("REPORT TO THE GALACTIC AUTHORITY", "SPACE CHICKEN", "IN FIVE FORMS"), "orients: the film is a report, and the report is the joke"),
  (C, 0, 1.6, None, 0, 0, ("FORM 1", "THE CHICKEN", ""), "the procedure begins"),
  ("556924d1", 0.0, 3.5, "5a2b4557", 8.6, 12.0, None, "the hen in grass; a farmer: 'I'm trying to raise chickens good enough to rate a 4-H club championship'"),
  ("de13a508", 0.0, 3.4, None, 0, None, None, "hens in a crate, being moved: the accident is set up"),
  (C, 0, 1.6, None, 0, 0, ("FORM 2", "THE LAUNCH", "(NOT AUTHORIZED)"), "the procedure, already broken"),
  ("83ba8737", 5.6, 8.6, None, 5.6, 8.6, None, "the junior crew at the blockhouse panels: 'We're all good. We're waiting for a lift off.'"),
  ("93375d54", 3.2, 7.4, None, 3.2, 6.4, None, "the crowd with binoculars: 'T minus 15 seconds. Guidance is internal.'"),
  ("c6c26518", 5.0, 8.4, "93375d54", 7.2, 10.6, None, "the countdown continues over a hen in a crate and a watching boy: '12, 11, 10, nine.'"),
  ("47780f2f", 0.0, 5.0, None, 0.0, 5.0, None, "liftoff, with its own roar: the accident is complete"),
  (C, 0, 1.6, None, 0, 0, ("FORM 3", "THE CREW", ""), "the procedure repeats"),
  ("921b0461", 0.0, 3.4, "78384883", 0.1, 3.2, None, "mission control in rows: 'Roger, … confirms that they are go'"),
  ("f090135e", 3.5, 7.0, "7978dcdb", 18.4, 21.4, None, "the craft over the Earth: 'Hello. Anybody in there?'"),
  ("21037f09", 3.5, 6.5, None, 0, None, None, "the answer: a chick, looking about, silent"),
  ("020ea46e", 0.0, 3.7, None, 0.0, 3.7, None, "a finger on a map: 'We have a problem, so I want to know in a few miles where we are.'"),
  (C, 0, 1.6, None, 0, 0, ("FORM 4", "THE EMPIRE", ""), "the procedure repeats, on the other side"),
  ("a708a938", 0.0, 4.6, "9473b0ed", 0.0, 3.0, None, "the council at its long table: 'What we do is hold a meeting and vote on things.'"),
  ("46e45998", 1.0, 5.2, "02182f1e", 6.5, 9.2, None, "the typing pool: 'Okay? All you simply need to do is fill out a copy of the pet application.'"),
  ("e31e12f6", 1.0, 4.2, None, 0, None, None, "the empire's chart: a chicken-shaped question mark over the map, silent"),
  ("1782b680", 0.5, 3.4, None, 0, None, None, "an urgent telephone"),
  ("ef08453f", 8.8, 11.6, None, 0, None, None, "the weapon's screen, ready"),
  ("3aaf1d1b", 0.0, 3.4, None, 0.0, 3.4, None, "the weapon waits: a man sips coffee. 'He passes the regulation flight check.'"),
  (C, 0, 1.6, None, 0, 0, ("FORM 5", "RE-ENTRY", ""), "the last form"),
  ("65b4504b", 0.0, 3.6, None, 0, None, None, "the capsule in the sea, small and upright"),
  ("19d75078", 6.4, 10.2, None, 0, None, None, "the recovery helicopter arrives"),
  ("556924d1", 0.5, 4.1, "6daf681e", 0.0, 3.2, None, "the return: the same hen in the same grass, now: 'Good news. The legislature has approved our petition'"),
  ("b16e5a32", 0.3, 3.0, None, 0, None, None, "a stamp comes down"),
  (C, 0, 3.0, None, 0, 0, ("FILED", "THE END", "IN TRIPLICATE"), "closes the report"),
]
def card(png, top, big, sub):
    im = Image.new("RGB", (W_, H_), (232, 224, 204)); d = ImageDraw.Draw(im); ink = (40, 34, 30)
    fr = ImageFont.truetype(FONTS["reg"], 26); fb = ImageFont.truetype(FONTS["bold"], 76); fs = ImageFont.truetype(FONTS["reg"], 30)
    for y in range(110, H_ - 100, 46): d.line([(90, y), (W_ - 90, y)], fill=(214, 204, 182), width=1)       # ruled form paper
    d.rectangle([70, 70, W_ - 70, H_ - 70], outline=ink, width=2)
    def c(y, t, f, col=ink): w = d.textlength(t, font=f); d.text(((W_ - w) / 2, y), t, font=f, fill=col)
    c(H_ / 2 - 110, top, fr); sz = 76
    while d.textlength(big, font=fb) > W_ - 200 and sz > 34: sz -= 4; fb = ImageFont.truetype(FONTS["bold"], sz)
    c(H_ / 2 - 46, big, fb)
    if sub: c(H_ / 2 + 56, sub, fs, (150, 40, 34))
    im.save(png)
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
VF = f"scale={W_}:{H_}:force_original_aspect_ratio=decrease,pad={W_}:{H_}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p"   # no grade: the archive's own colour
parts, table, t = [], [], 0.0
for n, (va, v0, v1, sa, a0, a1, txt, job) in enumerate(EDIT):
    out = os.path.join(T, f"sc_{n:02d}.mp4"); dur = v1 - v0
    if va is None:
        png = os.path.join(T, f"sc_{n:02d}.png"); card(png, *txt)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-t", f"{dur}", "-i", png, "-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=stereo",
                        "-vf", f"setsar=1,fps={FPS},format=yuv420p", *ENC, "-shortest", out], check=True)
    else:
        vsrc = clip(va); ssrc = clip(sa) if sa else vsrc
        if a1 is None: aseek, alen, af = v0, dur, f"volume=-45dB,afade=t=in:d=0.08,afade=t=out:st={dur - 0.1:.2f}:d=0.1"
        else: aseek, alen = a0, min(a1 - a0, dur); af = f"apad,afade=t=in:d=0.04,afade=t=out:st={alen - 0.08:.2f}:d=0.08"
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{v0}", "-t", f"{dur}", "-i", vsrc, "-ss", f"{aseek}", "-t", f"{alen}", "-i", ssrc,
                        "-filter_complex", f"[0:v]setpts=PTS-STARTPTS,{VF}[v];[1:a]asetpts=PTS-STARTPTS,{af},atrim=0:{dur},aformat=sample_rates=48000:channel_layouts=stereo[a]",
                        "-map", "[v]", "-map", "[a]", "-t", f"{dur}", *ENC, out], check=True)
    parts.append(out)
    table.append({"pos": n + 1, "at": round(t, 1), "dur": round(dur, 1), "picture": va or "card (added)", "picture_src": None if va is None else [v0, v1],
                  "sound": None if va is None else (sa or va), "sound_src": None if va is None else ([a0, a1] if a1 is not None else "room tone, -45 dB"),
                  "sound_elsewhere": bool(sa and sa != va), "card": " / ".join(x for x in txt if x) if txt else None, "job": job})
    t += dur
lst = os.path.join(T, "sc_list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
out = os.path.join(D, "space-chicken.mp4")
# one fixed gain for the whole film (two-pass, linear): a dynamic normalizer would lift the held silences back into speech
_m = subprocess.run(["ffmpeg", "-hide_banner", "-f", "concat", "-safe", "0", "-i", lst, "-af", "loudnorm=I=-17:TP=-1.5:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
_j = json.loads(_m[_m.rindex("{"):_m.rindex("}") + 1])
LN = f"loudnorm=I=-17:TP=-1.5:linear=true:measured_I={_j['input_i']}:measured_TP={_j['input_tp']}:measured_LRA={_j['input_lra']}:measured_thresh={_j['input_thresh']}:offset={_j['target_offset']}"
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-af", LN, "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "1600k", "-bufsize", "3200k", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
json.dump({"title": "Space Chicken", "seconds": round(t, 1), "edit": table}, open(os.path.join(D, "space-cut.json"), "w"), indent=1)
print(f"wrote {out} · {t:.1f} s · {len(EDIT)} pieces · {os.path.getsize(out) / 1e6:.1f} MB")
