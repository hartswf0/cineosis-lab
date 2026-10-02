"""Render a film the Monte Carlo cinema found (monte/evolution.json, best[k]) from the archive itself: each shot around its judged
moment (the clip's middle frame), each title card frozen on its own archival frame, each spoken line cut from its clip's sound at the
transcript's word times, and the archive's music (the chosen piece, continued by the pieces nearest its mood), dipped under the voices
and silent in the acts the rules made silent. No added text, no grade.   usage: python3 monte/render.py [k]  -> monte/film-<k>.mp4"""
import json, os, re, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); T = os.path.join(D, "cache"); os.makedirs(T, exist_ok=True)
K = int(sys.argv[1]) if len(sys.argv) > 1 else 0
EV = json.load(open(os.path.join(D, "evolution.json"))); F = EV["best"][K]; M = json.load(open(os.path.join(D, "material.json")))
V = json.load(open(os.path.join(L, "aspect", "video.json"))); R2 = M["r2"]; W_, H_, FPS = 960, 720, 24
DX = 0.8   # every join is a dissolve this long: no blinking; each piece runs DX longer and the next fades in over its tail
def fetch(i):
    p = os.path.join(T, i + ".mp4")
    if not os.path.exists(p) or os.path.getsize(p) < 1000: subprocess.run(["curl", "-sfL", "--retry", "3", "-A", "cineosis-44-research", "-o", p, R2 + V[i][0]], check=True)
    return p
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
VF = f"scale={W_}:{H_}:force_original_aspect_ratio=decrease,pad={W_}:{H_}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p"
parts, voices, silent, t = [], [], [], 0.0
for n, e in enumerate(F["ev"]):
    src = fetch(e["i"]); d = dur(src); mid = d / 2; out = os.path.join(T, f"f{K}_{n:02d}.mp4"); L_ = e["dur"]; LL = L_ + (DX if n < len(F["ev"]) - 1 else 0)
    if e["kind"] == "card":
        png = os.path.join(T, f"f{K}_{n:02d}.png"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{mid:.2f}", "-i", src, "-frames:v", "1", "-update", "1", png], check=True)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-t", f"{LL:.2f}", "-i", png, "-vf", VF, *ENC, out], check=True)
    else:
        a = max(0.0, min(mid - LL / 2, d - LL - .05))
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{a:.2f}", "-t", f"{LL:.2f}", "-i", src, "-an", "-vf", VF + (f",tpad=stop_mode=clone:stop_duration={LL:.2f}" if d < LL + .1 else ""), "-t", f"{LL:.2f}", *ENC, out], check=True)
        if e.get("line"):
            ln = e["line"]; flac = os.path.join(L, "odyssey", "cache", "aud", ln["i"] + ".flac")
            voices.append((t + .35, flac if os.path.exists(flac) else fetch(ln["i"]), ln["t0"], ln["t1"]))
        if e.get("silent"): silent.append((t, t + L_))
    parts.append(out); t += L_
# the joins: dissolves between shots, a dip through black into and out of a card
pic = os.path.join(T, f"f{K}_picture.mp4"); vfc, ch, at = "", "[0:v]", 0.0
for n in range(1, len(parts)):
    at += F["ev"][n - 1]["dur"]; kind = "fadeblack" if "card" in (F["ev"][n - 1]["kind"], F["ev"][n]["kind"]) else "fade"
    vfc += f"{ch}[{n}:v]xfade=transition={kind}:duration={DX}:offset={at:.3f}[j{n}];"; ch = f"[j{n}]"
subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", p] for p in parts], []), "-filter_complex", vfc + f"{ch}format=yuv420p[v]", "-map", "[v]", *ENC, pic], check=True)
# the music: the chosen piece, then the pieces nearest its mood, crossfaded, long enough for the film
mood = F["music"]["mood"]; cosv = lambda a, b: sum(x * y for x, y in zip(a, b)) / ((sum(x * x for x in a) * sum(y * y for y in b)) ** .5 or 1)
order = [F["music"]] + sorted([m for m in M["music"] if m["film"] != F["music"]["film"] and not re.search(r"interview|lecture|speech", m["film"] or "", re.I)], key=lambda m: -cosv(m["mood"], mood))
seenf = set(); order = [m for m in order if not (m["film"] in seenf or seenf.add(m["film"]))]   # one piece per film
music = order[: int(t // 24) + 2]
ins = sum([["-i", os.path.join(L, "odyssey", "cache", "aud", m["i"] + ".flac")] for m in music], [])
fc = "".join(f"[{k}:a]atrim=0:27,asetpts=PTS-STARTPTS,loudnorm=I=-21:TP=-2,aformat=sample_rates=48000:channel_layouts=stereo[m{k}];" for k in range(len(music))); ch = "[m0]"
for k in range(1, len(music)): fc += f"{ch}[m{k}]acrossfade=d=2.5:c1=tri:c2=tri[x{k}];"; ch = f"[x{k}]"
duck = "+".join(f"between(t,{a - .2:.2f},{a + (t1 - t0) + .2:.2f})" for a, _, t0, t1 in voices) or "0"
mute = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in silent) or "0"
fc += f"{ch}atrim=0:{t:.2f},volume='if({mute},0.0,if({duck},0.3,1))':eval=frame,afade=t=in:d=1,afade=t=out:st={t - 2.5:.2f}:d=2.5[mus];"
vin = len(music); vins = []
for k, (a, src, t0, t1) in enumerate(voices):
    vins += ["-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", src]
    fc += f"[{vin + k}:a]loudnorm=I=-17:TP=-2,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:d=0.05,afade=t=out:st={max(.1, t1 - t0 - .12):.2f}:d=0.12,adelay={int(a * 1000)}|{int(a * 1000)}[v{k}];"
fc += "[mus]" + "".join(f"[v{k}]" for k in range(len(voices))) + f"amix=inputs={1 + len(voices)}:duration=first,volume={1 + len(voices)}[a]"   # this ffmpeg's amix divides by the inputs: give it back
wav = os.path.join(T, f"f{K}_sound.wav"); subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, *vins, "-filter_complex", fc, "-map", "[a]", wav], check=True)
out = os.path.join(D, f"film-{K}.mp4")
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "1800k", "-bufsize", "3600k",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
print(f"wrote {out} · {t:.1f} s · {len(parts)} pieces · {len(voices)} voices · music {[m['film'] for m in music]}")
