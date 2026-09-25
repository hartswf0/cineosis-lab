"""Render the WYGWYL Forage cut from real archive footage (the suite's animatic was stills: its downloads 403'd).

Each of the 88 beats is built from its chosen clip (A) and its partner beat's clip (B, the counter-image),
composed by the beat's mode, at the beat's exact duration:
  hold      A fills the frame
  split     A | B side by side
  inset     A full; B enters as a bounded inset (top right) at the beat's midpoint
  dissolve  A, then a long dissolve into B over the middle fifth
  montage   A and B alternate in 1.5 s pieces
  black     black with the film's title, held
A clip shorter than its beat is slowed (to at most half speed) before it loops, so a hold stays a hold.
Chapter titles appear small, lower left, for the first 3 s of each of the 14 films. The suite audio is the only
soundtrack (source sound is dropped). Output: wygwyl/wygwyl-cut.mp4 (1280x720, 24 fps) + wygwyl/wygwyl-cut.edl.json.

    python3 render_wygwyl.py [beat ids...]    # a subset renders wygwyl/wygwyl-cut-<ids>.mp4 without audio
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

LAB = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(LAB, "wygwyl")
PARTS = os.path.join(OUT, "parts")
W, H, FPS = 1280, 720, 24
PIECE = 1.5
SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SERIF_I = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]

def run(args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])

def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

def fit(w, h):
    return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"

def src(clip, trim, need):
    """input args + a speed filter so a short clip fills `need` seconds: slow to ≥0.5x, then loop."""
    L = max(0.1, probe(clip) - trim)
    slow = min(2.0, max(1.0, need / L))                  # 1.0 = real speed; up to 2.0 = half speed
    return ["-stream_loop", "-1", "-ss", f"{trim:.3f}", "-i", clip], f"setpts={slow:.4f}*(PTS-STARTPTS),fps={FPS}", slow

def title_png(text, sub, path, big=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255 if big else 0)); d = ImageDraw.Draw(im)
    if big:
        f = ImageFont.truetype(SERIF, 64); d.text((W / 2, H / 2 - 20), text, font=f, fill="#ece6da", anchor="mm")
        if sub: d.text((W / 2, H / 2 + 44), sub, font=ImageFont.truetype(SERIF_I, 26), fill="#b3ab9e", anchor="mm")
    else:
        d.rectangle((0, H - 92, W, H), fill=(0, 0, 0, 120))
        d.text((40, H - 76), text, font=ImageFont.truetype(SERIF, 30), fill="#ece6da")
        if sub: d.text((40, H - 38), sub, font=ImageFont.truetype(MONO, 15), fill="#b3ab9e")
    im.save(path)

def beat_video(b, film, out):
    # frame-exact from the cumulative timeline, so 88 roundings never drift against the suite audio
    N = round(b["end"] * FPS) - round(b["start"] * FPS)
    D = N / FPS
    A = os.path.join(LAB, b["a"]["clip"]) if b.get("a") and b["a"].get("clip") else None
    B = os.path.join(LAB, b["b"]["clip"]) if b.get("b") and b["b"].get("clip") else None
    mode = b["mode"] if (b["mode"] == "black" or A) else "black"
    if mode in ("split", "inset", "dissolve", "montage") and not B:
        mode = "hold"
    trim = float(b.get("trim") or 0)
    if mode == "black":
        png = out + ".png"; title_png(film["title"], None, png, big=True)
        run(["-loop", "1", "-t", f"{D:.3f}", "-i", png, "-vf", f"fps={FPS},format=yuv420p,fade=in:0:12,fade=out:st={max(0, D - .5):.3f}:d=0.5", *ENC, "-frames:v", str(N), out])
        return mode
    ia, fa, _ = src(A, trim, D)
    if mode == "hold":
        run([*ia, "-filter_complex", f"[0:v]{fa},{fit(W, H)}[v]", "-map", "[v]", "-frames:v", str(N), *ENC, out])
    elif mode == "split":
        ib, fb, _ = src(B, 0, D)
        run([*ia, *ib, "-filter_complex", f"[0:v]{fa},{fit(W // 2, H)}[a];[1:v]{fb},{fit(W // 2, H)}[b];[a][b]hstack=inputs=2[v]",
             "-map", "[v]", "-frames:v", str(N), *ENC, out])
    elif mode == "inset":
        ib, fb, _ = src(B, 0, D)
        iw, ih = 448, 252
        run([*ia, *ib, "-filter_complex",
             f"[0:v]{fa},{fit(W, H)}[a];[1:v]{fb},{fit(iw, ih)},drawbox=x=0:y=0:w={iw}:h={ih}:color=white@0.85:t=2,setpts=PTS+{D / 2:.3f}/TB[b];"
             f"[a][b]overlay=x={W - iw - 40}:y=40:enable='gte(t,{D / 2:.3f})':eof_action=pass[v]",
             "-map", "[v]", "-frames:v", str(N), *ENC, out])
    elif mode == "dissolve":
        ib, fb, _ = src(B, 0, D)
        off, dur = 0.4 * D, 0.2 * D
        run([*ia, *ib, "-filter_complex",
             f"[0:v]{fa},{fit(W, H)},trim=duration={off + dur:.3f},setpts=PTS-STARTPTS[a];"
             f"[1:v]{fb},{fit(W, H)},trim=duration={D - off:.3f},setpts=PTS-STARTPTS[b];"
             f"[a][b]xfade=transition=fade:duration={dur:.3f}:offset={off:.3f}[v]",
             "-map", "[v]", "-frames:v", str(N), *ENC, out])
    elif mode == "montage":
        ib, fb, _ = src(B, 0, D)
        n = max(2, round(D / PIECE))
        fr = [round((k + 1) * N / n) - round(k * N / n) for k in range(n)]     # piece lengths in frames, summing to N
        labels = [f"[p{k}]" for k in range(n)]
        # each input feeds several pieces: split them; each stream advances by its own pieces
        na, nb = (n + 1) // 2, n // 2
        pre = f"[0:v]split={na}" + "".join(f"[a{j}]" for j in range(na)) + f";[1:v]split={nb}" + "".join(f"[b{j}]" for j in range(nb))
        ai = bi = 0; pos = [0, 0]; body = []
        for k in range(n):
            s_ = k % 2
            if s_ == 0: inp, ai = f"[a{ai}]", ai + 1
            else: inp, bi = f"[b{bi}]", bi + 1
            f = fa if s_ == 0 else fb
            body.append(f"{inp}{f},{fit(W, H)},trim=start_frame={pos[s_]}:end_frame={pos[s_] + fr[k]},setpts=PTS-STARTPTS[p{k}]")
            pos[s_] += fr[k]
        fc = pre + ";" + ";".join(body) + ";" + "".join(labels) + f"concat=n={n}:v=1:a=0[v]"
        run([*ia, *ib, "-filter_complex", fc, "-map", "[v]", "-frames:v", str(N), *ENC, out])
    return mode

def main():
    idx = json.load(open(os.path.join(LAB, "tools", "cineosis-index.json")))["wygwyl"]
    beats, films = idx["beats"], idx["films"]
    only = {int(a) for a in sys.argv[1:]}
    os.makedirs(PARTS, exist_ok=True)
    def film_of(b):
        return next((f for f in films if f["container"][0] - 1e-3 <= b["start"] < f["container"][1] + 1e-3), films[-1])
    seen, parts, edl = set(), [], []
    for b in beats:
        if only and b["id"] not in only:
            continue
        f = film_of(b)
        part = os.path.join(PARTS, f"{b['id']:03d}.mp4")
        mode = beat_video(b, f, part)
        if f["n"] not in seen and mode != "black" and not only:      # chapter title over the chapter's first beat
            seen.add(f["n"])
            png = os.path.join(PARTS, f"title-{f['n']}.png"); title_png(f"{f['n']} · {f['title']}", "WYGWYL", png)
            titled = part.replace(".mp4", "-t.mp4")
            run(["-i", part, "-loop", "1", "-t", "3.2", "-i", png, "-filter_complex",
                 "[1:v]format=rgba,fade=in:0:8:alpha=1,fade=out:st=2.6:d=0.6:alpha=1[t];[0:v][t]overlay=0:0:eof_action=pass[v]",
                 "-map", "[v]", *ENC, titled])
            os.replace(titled, part)
        elif f["n"] not in seen and mode == "black":
            seen.add(f["n"])
        parts.append(part)
        edl.append({"beat": b["id"], "mode": mode, "start": b["start"], "end": b["end"], "title": b.get("title"),
                    "a": (b.get("a") or {}).get("id"), "b": (b.get("b") or {}).get("id"), "codes": b.get("codes")})
        print(f"beat {b['id']:3d} {mode:8s} {b['end'] - b['start']:6.2f}s  {b.get('title', '')[:50]}", flush=True)
    lst = os.path.join(PARTS, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(OUT, "wygwyl-cut-silent.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    if only:
        os.replace(silent, os.path.join(OUT, "wygwyl-cut-" + "-".join(map(str, sorted(only))) + ".mp4"))
        print("DONE subset"); return
    audio = os.path.join(LAB, idx["audio"])
    final = os.path.join(OUT, "wygwyl-cut.mp4")
    run(["-i", silent, "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", final])
    os.remove(silent)
    json.dump({"title": idx.get("title"), "duration": idx["duration"], "beats": edl}, open(os.path.join(OUT, "wygwyl-cut.edl.json"), "w"), indent=1)
    print("DONE", final, round(probe(final), 1), "s", flush=True)

if __name__ == "__main__":
    main()
