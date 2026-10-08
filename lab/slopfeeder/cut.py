"""Cut a SLOPFEEDER rough cut to a VOLHOLLA song from the studio plan (studio.json): every shot an archival plate filling the frame,
straight cuts on the song's beats; where the plan says so, a moving SAM cut-out from the archive composited over the plate, and in the
hybrid version the tracked elements of the source videos (the login characters as the fleet, Ghost as the cook). Coded effects: on the
landing's downbeats the frame shakes and flashes white. No grade, no added text.
  python3 slopfeeder/cut.py 26 archive   -> slopfeeder/roughcut/song-26-archive.mp4   (archive only: publishable)
  python3 slopfeeder/cut.py 26 hybrid    -> slopfeeder/src/roughcut/song-26-hybrid.mp4 (with the source videos' elements: local)"""
import json, os, sys, subprocess, math
D = os.path.dirname(os.path.abspath(__file__)); N = sys.argv[1] if len(sys.argv) > 1 else "26"; MODE = sys.argv[2] if len(sys.argv) > 2 else "archive"
P = json.load(open(os.path.join(D, "studio.json"))); song = next(s for s in P["songs"] if s["n"] == N); cuts = {c["id"]: c for c in P["cuts"]}
ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"); CACHE = os.path.join(D, "fclips"); os.makedirs(CACHE, exist_ok=True)
OUTD = os.path.join(D, "roughcut") if MODE == "archive" else os.path.join(D, "src", "roughcut"); T = os.path.join(OUTD, f"parts-{N}-{MODE}"); os.makedirs(T, exist_ok=True)
W, H, FPS = 1280, 720, 24
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]
FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p"   # colour, even over a grey plate
def fetch(c):
    p = os.path.join(CACHE, c["id"] + ".mp4")
    if not os.path.exists(p) or os.path.getsize(p) < 5000: subprocess.run(["curl", "-sfL", "-A", "cineosis-44-research", "-o", p, c["v"]])
    return p if os.path.exists(p) and os.path.getsize(p) > 5000 else None
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
parts, n = [], 0
for si, sec in enumerate(song["sections"]):
    for sh in sec["shots"]:
        src = os.path.join(D, "cartoon", sh["cartoon"] + ".mp4") if sh.get("cartoon") else fetch(sh["clip"]) or next((fetch(a) for a in sh["alts"] if fetch(a)), None)
        if not src: continue
        L = sh["dur"]; d = dur(src); a = 0.0 if sh.get("cartoon") else max(0.0, min(d / 2 - L / 2, d - L - .05)); out = os.path.join(T, f"{n:03d}.mp4"); n += 1   # a cartoon plays from its first drawing
        ins = ["-ss", f"{a:.2f}", "-t", f"{L:.2f}", "-i", src]; fc = f"[0:v]{FILL}" + (f",tpad=stop_mode=clone:stop_duration={L:.2f}" if d < L + .1 else "") + "[p]"; last = "[p]"; k = 1
        lay = []
        if sh.get("cutout") and sh["cutout"] in cuts: lay.append(("cut", os.path.join(D, cuts[sh["cutout"]]["packed"]), .62, "bottom"))
        if MODE == "hybrid" and sh.get("track"):
            t = sh["track"]; tp = os.path.join(D, "src", "tracks", t, f"{t}-packed.mp4")
            if os.path.exists(tp): lay.append(("track", tp, .5 if t.startswith("login") else .9, "horizon" if t.startswith("login") else "right"))
        for kind, pk, sc, where in lay:
            if not os.path.exists(pk): continue
            ins += (["-ss", "1.6"] if "login" in pk else []) + ["-stream_loop", "-1", "-i", pk]   # the login characters: after their intro
            pos = {"bottom": "x=(W-w)/2:y=H-h", "horizon": f"x=(W-w)/2+{(n * 211) % 420 - 210}:y=H*0.56-h", "right": "x=W-w-40:y=H-h"}[where]
            fc += (f";[{k}:v]fps={FPS},split[c{k}][m{k}];[c{k}]crop=iw/2:ih:0:0,format=rgba[cc{k}];[m{k}]crop=iw/2:ih:iw/2:0,format=gray[mm{k}];[cc{k}][mm{k}]alphamerge,scale=-2:{int(H * sc)}[o{k}]"
                   f";{last}[o{k}]overlay={pos}:shortest=1[v{k}]"); last = f"[v{k}]"; k += 1
        if sec["world"] == "THE LANDING" and not sh.get("cartoon"):   # code: the shell hits on the downbeat (shake, then a white flash that fades)
            fc += f";{last}crop=iw-24:ih-24:12+10*sin(t*53):12+10*cos(t*41),scale={W}:{H},fade=t=in:st=0:d=0.12:color=white[sh]"; last = "[sh]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", last, "-t", f"{L:.2f}", *ENC, out], check=True)
        parts.append(out)
    print(f"section {si + 1}/{len(song['sections'])} {sec['world']} · {len(sec['shots'])} shots", flush=True)
lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
pic = os.path.join(T, "picture.mp4"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", pic], check=True)
out = os.path.join(OUTD, f"song-{N}-{MODE}.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", os.path.join(ALB, song["file"]), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                "-maxrate", "2500k", "-bufsize", "5000k", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
print("wrote", out, f"{dur(out):.1f} s ·", len(parts), "shots")
