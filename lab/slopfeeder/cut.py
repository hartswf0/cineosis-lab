"""Cut a SLOPFEEDER rough cut to a VOLHOLLA song from the studio plan (studio.json): every shot an archival plate filling the frame,
straight cuts on the song's beats; where the plan says so, a moving SAM cut-out from the archive composited over the plate, and in the
hybrid version the tracked elements of the source videos (the login characters as the fleet, Ghost as the cook). Coded effects: on the
landing's downbeats the frame shakes and flashes white. No grade, no added text.
  python3 slopfeeder/cut.py 26 archive   -> slopfeeder/roughcut/song-26-archive.mp4   (archive only: publishable)
  python3 slopfeeder/cut.py 26 hybrid    -> slopfeeder/src/roughcut/song-26-hybrid.mp4 (with the source videos' elements: local)
  python3 slopfeeder/cut.py --cutlist griddle-26.json   -> slopfeeder/roughcut/griddle-26.mp4 (a cut served from the griddle: its plates,
      its figures, the pickups' own sound under the song where the cut asked for it, and its trap cuts: flash, dissolve)"""
import json, os, sys, subprocess, math
D = os.path.dirname(os.path.abspath(__file__)); N = sys.argv[1] if len(sys.argv) > 1 else "26"; MODE = sys.argv[2] if len(sys.argv) > 2 else "archive"
P = json.load(open(os.path.join(D, "studio.json"))); cuts = {c["id"]: c for c in P["cuts"]}
if N == "--cutlist":   # a cut served from the griddle, read into the same shape as a plan
    CL = json.load(open(sys.argv[2])); N, MODE = CL["song"], "griddle"; secs = []
    for sl in CL["slots"]:
        pl = sl["plate"]; sh = {"t0": sl["t0"], "dur": sl["dur"], "alts": [], "trap": sl.get("cut_in", "cut"), "in": pl.get("in"), "rate": pl.get("rate") or 1}
        if pl["type"] == "drawn": sh["cartoon"] = pl["id"].replace("drawn-", "", 1); sh["clip"] = {"id": pl["id"]}
        elif pl["type"] == "ai":
            nm = os.path.basename(pl["media"])[:-4]; sh["clip"] = {"id": pl["id"], "ai": {"file": f"ai/src/{nm}.mp4" if os.path.exists(os.path.join(D, "ai", "src", nm + ".mp4")) else pl["media"], "t0": pl["in"] or 0, "t1": (pl["in"] or 0) + 12}}
            if sl.get("sound"): sh["sound"] = {"src": os.path.join(D, sh["clip"]["ai"]["file"]), "in": pl["in"] or 0}
        else: sh["clip"] = {"id": pl["id"], "v": pl["media"]}
        if sl.get("figure"): sh["figure"] = os.path.join(D, sl["figure"]["packed"])
        if not secs or secs[-1]["world"] != sl["world"]: secs.append({"world": sl["world"], "shots": []})
        secs[-1]["shots"].append(sh)
    flat = [x for sec in secs for x in sec["shots"]]; sd = float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"), CL["file"])], capture_output=True, text=True).stdout or 0)
    for a_, b_ in zip(flat, flat[1:] + [None]): a_["dur"] = round((b_["t0"] if b_ else sd) - a_["t0"], 3)   # each slot runs until the next begins: the cut covers the whole song
    song = {"file": CL["file"], "sections": secs}
else: song = next(s for s in P["songs"] if s["n"] == N); CL = {}
REG = {"raw": "", "newsreel": ",hue=s=0,eq=contrast=1.28:brightness=-0.03,noise=alls=9:allf=t",   # one look for the whole film, so archive, pickup and drawing belong to one world
       "flat": ",split[ra][rb];[ra]format=rgb24,lutrgb=r='floor(val/52)*52+20':g='floor(val/52)*52+20':b='floor(val/52)*52+20',format=gbrp[rp];[rb]format=gray,gblur=sigma=1.4,edgedetect=low=0.1:high=0.25,negate,format=gbrp[re];[rp][re]blend=all_mode=multiply,format=yuv420p"}[CL.get("register", "raw")]
ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"); CACHE = os.path.join(D, "fclips"); os.makedirs(CACHE, exist_ok=True)
OUTD = os.path.join(D, "roughcut") if MODE in ("archive", "griddle") else os.path.join(D, "src", "roughcut"); T = os.path.join(OUTD, f"parts-{N}-{MODE}"); os.makedirs(T, exist_ok=True)
W, H, FPS = 1280, 720, 24
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]
FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p"   # colour, even over a grey plate
def fetch(c):
    p = os.path.join(CACHE, c["id"] + ".mp4")
    if not os.path.exists(p) or os.path.getsize(p) < 5000: subprocess.run(["curl", "-sfL", "-A", "cineosis-44-research", "-o", p, c["v"]])
    return p if os.path.exists(p) and os.path.getsize(p) > 5000 else None
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
parts, n, SOUNDS, t_at = [], 0, [], 0.0
for si, sec in enumerate(song["sections"]):
    for sh in sec["shots"]:
        ai = sh["clip"].get("ai") if not sh.get("cartoon") else None
        src = os.path.join(D, "cartoon", sh["cartoon"] + ".mp4") if sh.get("cartoon") else os.path.join(D, ai["file"]) if ai and os.path.exists(os.path.join(D, ai["file"])) else fetch(sh["clip"]) or next((fetch(a) for a in sh["alts"] if fetch(a)), None)
        if not src: continue
        L = sh["dur"]; R = sh.get("rate", 1); d = dur(src); a = 0.0 if sh.get("cartoon") else (max(ai["t0"], min((ai["t0"] + ai["t1"]) / 2 - L / 2, ai["t1"] - L)) if ai else max(0.0, min(d / 2 - L / 2, d - L - .05))); a = sh["in"] if sh.get("in") is not None and not sh.get("cartoon") else a; a = min(a, max(0.0, d - .4)); out = os.path.join(T, f"{n:03d}.mp4"); n += 1   # a cartoon plays from its first drawing; no in-point past the clip's end
        ins = ["-ss", f"{a:.2f}", "-t", f"{L * R:.2f}", "-i", src]; fc = f"[0:v]" + (f"setpts=PTS/{R:.3f}," if R != 1 else "") + FILL + (f",tpad=stop_mode=clone:stop_duration={L:.2f}" if d - a < L * R + .1 else "") + "[p]"; last = "[p]"; k = 1   # rate: a pounding retimed onto the song's beat
        lay = []
        if sh.get("cutout") and sh["cutout"] in cuts: lay.append(("cut", os.path.join(D, cuts[sh["cutout"]]["packed"]), .62, "bottom"))
        if sh.get("figure"): lay.append(("fig", sh["figure"], .7, "right"))
        if MODE == "hybrid" and sh.get("track"):
            t = sh["track"]; tp = os.path.join(D, "src", "tracks", t, f"{t}-packed.mp4")
            if os.path.exists(tp): lay.append(("track", tp, .5 if t.startswith("login") else .9, "horizon" if t.startswith("login") else "right"))
        for kind, pk, sc, where in lay:
            if not os.path.exists(pk): continue
            ins += (["-ss", "1.6"] if "login" in pk else []) + ["-stream_loop", "-1", "-i", pk]   # the login characters: after their intro
            pos = {"bottom": "x=(W-w)/2:y=H-h", "horizon": f"x=(W-w)/2+{(n * 211) % 420 - 210}:y=H*0.56-h", "right": "x=W-w-40:y=H-h"}[where]
            fc += (f";[{k}:v]fps={FPS},split[c{k}][m{k}];[c{k}]crop=iw/2:ih:0:0,format=rgba[cc{k}];[m{k}]crop=iw/2:ih:iw/2:0,format=gray[mm{k}];[cc{k}][mm{k}]alphamerge,scale=-2:{int(H * sc)}[o{k}]"
                   f";{last}[o{k}]overlay={pos}:shortest=1[v{k}]"); last = f"[v{k}]"; k += 1
        if sh.get("trap") in ("flash", "dissolve"):   # the trap lane: a white flash or a short dip in from black
            fc += f";{last}fade=t=in:st=0:d={'0.14' if sh['trap'] == 'flash' else '0.35'}:color={'white' if sh['trap'] == 'flash' else 'black'}[tp]"; last = "[tp]"
        if sh.get("sound"): SOUNDS.append((t_at, sh["sound"]["src"], sh["sound"]["in"] + (a - (ai["t0"] if ai else 0) if ai else 0), L))
        t_at += L
        if MODE != "griddle" and sec["world"] == "THE LANDING" and not sh.get("cartoon"):   # code: the shell hits on the downbeat (shake, then a white flash that fades)
            fc += f";{last}crop=iw-24:ih-24:12+10*sin(t*53):12+10*cos(t*41),scale={W}:{H},fade=t=in:st=0:d=0.12:color=white[sh]"; last = "[sh]"
        if REG: fc += f";{last}null{REG}[rg]"; last = "[rg]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", last, "-t", f"{L:.2f}", *ENC, out], check=True)
        parts.append(out)
    print(f"section {si + 1}/{len(song['sections'])} {sec['world']} · {len(sec['shots'])} shots", flush=True)
lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
pic = os.path.join(T, "picture.mp4"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", pic], check=True)
out = os.path.join(OUTD, (f"blacktop-{N}-{CL.get('bet', '').lower()}-{CL.get('register', 'raw')}" if CL.get("tool") == "blacktop" else os.path.basename(sys.argv[2])[:-5]) + ".mp4" if MODE == "griddle" else f"song-{N}-{MODE}.mp4")
# the song, and under it the pickups' own sound wherever the cut let it in (ducked, faded at the edges)
sins, sfc = [], "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=1.0[s0]"; mix = "[s0]"
for j, (t0_, src_, in_, L_) in enumerate(SOUNDS):
    if not os.path.exists(src_): continue
    sins += ["-ss", f"{max(0, in_):.2f}", "-t", f"{L_:.2f}", "-i", src_]; k_ = 2 + len(sins) // 6 - 1
    sfc += f";[{k_}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.55,afade=t=in:d=0.15,afade=t=out:st={max(.1, L_ - .25):.2f}:d=0.25,adelay={int(t0_ * 1000)}|{int(t0_ * 1000)}[x{j}]"; mix += f"[x{j}]"
n_in = 1 + len(sins) // 6
sfc += f";{mix}amix=inputs={n_in}:duration=first,volume={n_in},loudnorm=I=-14:TP=-1.5[a]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", os.path.join(ALB, song["file"]), *sins, "-filter_complex", sfc, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "23",
                "-maxrate", "1300k", "-bufsize", "2600k", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
print("wrote", out, f"{dur(out):.1f} s ·", len(parts), "shots")
