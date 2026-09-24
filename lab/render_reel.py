"""Render the Cineosis reel: one film that walks the periodic table.

For each of the 45 signs: a title card (symbol in its domain colour, name, number, the deciding test),
then its PER_SIGN best-read shots, each SHOT_S seconds from the matched frame with a lower-third caption
(the reading, film, year, confidence). Output: reel/cineosis-reel.mp4 (1280x720, 24 fps).

    python3 render_reel.py [n n ...]     # optional subset of sign numbers
"""
import json, os, subprocess, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

LAB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LAB)
OUT = os.path.join(LAB, "reel")
W, H, FPS = 1280, 720, 24
CARD_S, SHOT_S, PER_SIGN = 3.0, 3.5, 3
DOM = {"perception": "#e9d9a8", "affect": "#f0b9a4", "action": "#e7a37c", "reflection": "#b9cfa0",
       "mental": "#a9c9c9", "break": "#d9d3c7", "time": "#b8b3d8", "read": "#d9b8d2"}
SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SERIF_B = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
SERIF_I = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"

def font(p, s): return ImageFont.truetype(p, s)

def card(sign, path):
    im = Image.new("RGB", (W, H), "black"); d = ImageDraw.Draw(im)
    col = DOM[sign["dom"]]
    d.rounded_rectangle((96, 190, 296, 410), 10, fill=col)
    d.text((110, 202), sign["n"], font=font(MONO, 22), fill="#1d1b18")
    d.text((196, 318), sign["symbol"], font=font(SERIF_B, 92), fill="#1d1b18", anchor="mm")
    d.text((340, 196), sign["image"].upper() + "  " + sign["code"], font=font(MONO, 20), fill="#8d877c")
    d.text((340, 228), sign["name"], font=font(SERIF_B, 54), fill="#ece6da")
    y = 312
    for line in textwrap.wrap(sign.get("difference") or "", 52)[:5]:
        d.text((340, y), line, font=font(SERIF_I, 27), fill="#cfc8bb"); y += 38
    d.text((96, 640), "THE PERIODIC TABLE OF CINEMATIC SIGNS · after Deamer (2016)", font=font(MONO, 16), fill="#5c574f")
    ceil = sign.get("ceiling")
    if ceil is not None:
        d.text((W - 96, 640), f"one shot can carry ≤ {ceil}%", font=font(MONO, 16), fill="#5c574f", anchor="ra")
    im.save(path)

def caption(sign, shot, r, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, H - 150, W, H), fill=(0, 0, 0, 185))
    col = DOM[sign["dom"]]
    d.rounded_rectangle((40, H - 128, 118, H - 50), 6, fill=col)
    d.text((79, H - 89), sign["symbol"], font=font(SERIF_B, 34), fill="#1d1b18", anchor="mm")
    lines = textwrap.wrap(r["note"], 78)[:2]
    y = H - 132
    for line in lines:
        d.text((140, y), line, font=font(SERIF, 25), fill="#f3efe6"); y += 33
    meta = f"{shot['title'][:60]}{' (' + str(shot['year']) + ')' if shot.get('year') else ''}"
    d.text((140, H - 52), meta, font=font(MONO, 16), fill="#b9b2a5")
    if r.get("conf") is not None:
        x0, y0, bw = W - 360, H - 46, 300
        d.rectangle((x0, y0, x0 + bw, y0 + 8), fill="#3a3631")
        d.rectangle((x0, y0, x0 + bw * r["shot"] / 100, y0 + 8), fill=col)
        d.text((x0 + bw, y0 - 24), f"{sign['symbol']} {r['conf']}%  (shot alone {r['shot']}%)", font=font(MONO, 15), fill="#b9b2a5", anchor="ra")
    im.save(path)

def run(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)

def main():
    data = json.load(open(os.path.join(LAB, "lab-data.json")))
    signs = data["signs"]
    only = set(sys.argv[1:])
    by_sign = {}
    for sh in data["shots"]:
        for r in sh["signs"]:
            if sh.get("clip"):
                by_sign.setdefault(r["n"], []).append((sh, r))
    os.makedirs(os.path.join(OUT, "parts"), exist_ok=True)
    parts = []
    for s in signs:
        if only and s["n"] not in only:
            continue
        cp = os.path.join(OUT, "parts", f"{s['n']}_card.png"); card(s, cp)
        cv = os.path.join(OUT, "parts", f"{s['n']}_0card.mp4")
        run(["-loop", "1", "-t", str(CARD_S), "-i", cp, "-f", "lavfi", "-t", str(CARD_S), "-i", "anullsrc=r=48000:cl=stereo",
             "-vf", f"fps={FPS},format=yuv420p,fade=in:0:8,fade=out:st={CARD_S - 0.35}:d=0.35",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", cv])
        parts.append(cv)
        best = sorted(by_sign.get(s["n"], []), key=lambda t: -(t[1].get("conf") or 0))[:PER_SIGN]
        for k, (sh, r) in enumerate(best):
            clip = os.path.join(LAB, sh["clip"])
            dur = sh["end"] - sh["start"]
            rt = sh["read_t"] if sh.get("read_t") is not None else sh["match"] - sh["start"]
            off = max(0.0, min(rt - 0.6, dur - SHOT_S))  # open on the frame the reading describes
            t = min(SHOT_S, max(1.0, dur - off))
            capp = os.path.join(OUT, "parts", f"{s['n']}_{k}_cap.png"); caption(s, sh, r, capp)
            pv = os.path.join(OUT, "parts", f"{s['n']}_{k + 1}.mp4")
            has_a = (sh.get("audio") or {}).get("has_audio")
            vol = 1.0 if s["n"] == "34b" else 0.55
            inputs = ["-ss", f"{off:.3f}", "-t", f"{t:.3f}", "-i", clip, "-loop", "1", "-t", f"{t:.3f}", "-i", capp]
            vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,"
                  f"setsar=1,fps={FPS}[v];[v][1:v]overlay=0:0,format=yuv420p,fade=in:0:5,fade=out:st={t - 0.25:.3f}:d=0.25[out]")
            if has_a:
                args = inputs + ["-filter_complex", vf + f";[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},"
                                 f"afade=in:0:d=0.2,afade=out:st={t - 0.3:.3f}:d=0.3[a]", "-map", "[out]", "-map", "[a]"]
            else:
                args = inputs + ["-f", "lavfi", "-t", f"{t:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
                                 "-filter_complex", vf, "-map", "[out]", "-map", "2:a"]
            run(args + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", pv])
            parts.append(pv)
        print("sign", s["n"], len(best), "shots", flush=True)
    lst = os.path.join(OUT, "parts", "list.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{p}'\n")
    name = "cineosis-reel.mp4" if not only else f"cineosis-reel-{'-'.join(sorted(only))}.mp4"
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", os.path.join(OUT, name)])
    print("DONE", os.path.join(OUT, name), flush=True)

if __name__ == "__main__":
    main()
