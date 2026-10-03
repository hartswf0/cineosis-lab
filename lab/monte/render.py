"""Render a film the Monte Carlo cinema found (monte/evolution.json, best[k]) from the archive itself, the way Precisely So was made
(wes/precisely_cut.py): each title card frozen on its own archival frame at the moment it is fully up (never mid-fade, never the black
before it), each shot playing its real motion over its steadiest, best-lit stretch (no fades, no black, no flash frames), straight cuts,
and the archive's music (the chosen piece, continued by the pieces nearest its mood), each piece levelled, silent in the acts the rules
made silent, and the whole levelled in two passes. No added text, no grade, no borrowed voices.
usage: python3 monte/render.py [k]  -> monte/film-<k>.mp4, monte/film-<k>.json (the edit: every piece, its source and its moment)"""
import json, os, re, subprocess, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); T = os.path.join(D, "cache"); os.makedirs(T, exist_ok=True)
K = int(sys.argv[1]) if len(sys.argv) > 1 else 0
EV = json.load(open(os.path.join(D, "evolution.json"))); F = EV["best"][K]; M = json.load(open(os.path.join(D, "material.json")))
V = json.load(open(os.path.join(L, "aspect", "video.json"))); R2 = M["r2"]; W_, H_, FPS = 960, 720, 24
def fetch(i):
    p = os.path.join(T, i + ".mp4")
    if not os.path.exists(p) or os.path.getsize(p) < 1000: subprocess.run(["curl", "-sfL", "--retry", "3", "-A", "cineosis-44-research", "-o", p, R2 + V[i][0]], check=True)
    return p
# ---- the moment: read the clip small and grey, eight frames a second, and find where the picture is really there
SR, SW, SH = 8, 64, 48
def frames(p):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-vf", f"fps={SR},scale={SW}:{SH},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, SH, SW).astype(np.float32)
def moment(p, kind, need):
    """(start, the frame to hold) in seconds. The judge saw the clip's middle frame, so everything is anchored there. A card: the steady,
    fully-lit stretch of the same card as the middle frame (nearest it), held at its middle, so never mid-fade and never the next card.
    A shot: the window of `need` seconds around the middle with no black, no fade and no cut inside it."""
    f = frames(p); n = len(f)
    if n < 2: return 0.0, 0.0
    m = n // 2; lum, con = f.mean((1, 2)), f.std((1, 2)); diff = np.r_[0, np.abs(np.diff(f, axis=0)).mean((1, 2))]
    z = (f - lum[:, None, None]) / (con[:, None, None] + 1e-3); ref = z[m]; same = (z * ref).mean((1, 2))   # each frame against the judged one
    up = (lum > 5) & (con > max(6, 0.6 * np.percentile(con, 90)))
    if kind == "card":
        if con[m] < 6: same[:] = 1                                   # the judged frame was black: any steady card will do
        ok = up & (diff < 2.5) & (same > .7); runs, a = [], None
        for k in range(n + 1):
            if k < n and ok[k]: a = k if a is None else a
            elif a is not None: runs.append((a, k - 1)); a = None
        if not runs: return m / SR, m / SR
        a, b = min(runs, key=lambda r: (0 if r[0] <= m <= r[1] else min(abs(r[0] - m), abs(r[1] - m)), -(r[1] - r[0])))
        full = [k for k in range(a, b + 1) if con[k] >= .97 * con[a:b + 1].max()]; k = full[len(full) // 2]   # the card at full strength
        return k / SR, k / SR
    w = max(1, int(round(need * SR))); good = up & (diff < 22) & (same > .35)   # a jump this big, or a frame this unlike the judged one, is a cut
    if n <= w: return 0.0, m / SR
    ok = np.convolve(good.astype(np.float32), np.ones(w), "valid") / w; c = np.clip(m - w / 2, 0, len(ok) - 1)
    score = ok - 0.4 * np.abs(np.arange(len(ok)) - c) / max(1, n)  # all-good first, then nearest the judged moment
    a = int(np.argmax(score)); return a / SR, (a + w / 2) / SR
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
VF = f"scale={W_}:{H_}:force_original_aspect_ratio=decrease,pad={W_}:{H_}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p"   # no grade
parts, table, silent, t = [], [], [], 0.0
for n, e in enumerate(F["ev"]):
    src = fetch(e["i"]); d = dur(src); out = os.path.join(T, f"f{K}_{n:02d}.mp4"); L_ = e["dur"]
    if e["kind"] == "card":   # the archival frame itself, held to be read
        _, at = moment(src, "card", L_); png = os.path.join(T, f"f{K}_{n:02d}.png")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{at:.2f}", "-i", src, "-frames:v", "1", "-update", "1", png], check=True)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-t", f"{L_:.2f}", "-i", png, "-vf", VF, *ENC, out], check=True); v0 = v1 = round(at, 2)
    else:                     # real motion over its best stretch
        a, _ = moment(src, "shot", L_); a = max(0.0, min(a, d - L_ - .05))
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{a:.2f}", "-t", f"{L_:.2f}", "-i", src, "-an", "-vf", VF + (f",tpad=stop_mode=clone:stop_duration={L_:.2f}" if d < L_ + .1 else ""), "-t", f"{L_:.2f}", *ENC, out], check=True)
        v0, v1 = round(a, 2), round(a + L_, 2)
    if e.get("silent"): silent.append((t, t + L_))   # a silent act, or the card that stops the film
    parts.append(out)
    table.append({"pos": n + 1, "at": round(t, 1), "dur": round(L_, 2), "kind": e["kind"], "id": e["i"], "film": e.get("film"), "year": e.get("year"), "score": e.get("score"),
                  "source": [v0, v1] if v1 > v0 else f"frame at {v0} s, held", "text": e.get("text"), "silent": bool(e.get("silent"))})
    t += L_
# the joins: straight cuts, as in Precisely So
pic = os.path.join(T, f"f{K}_picture.mp4")   # re-encoded through the concat filter: a stream copy can stop at a piece whose timing differs
subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", x] for x in parts], []), "-filter_complex", "".join(f"[{k}:v]settb=1/{FPS},setpts=PTS-STARTPTS[p{k}];" for k in range(len(parts))) + "".join(f"[p{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]", "-map", "[v]", *ENC, pic], check=True)
assert abs(dur(pic) - t) < 1, f"picture is {dur(pic):.1f} s, the edit {t:.1f} s"
# the music: the chosen piece, then the pieces nearest its mood, one per film, each levelled before they meet, crossfaded
mood = F["music"]["mood"]; cosv = lambda a, b: sum(x * y for x, y in zip(a, b)) / ((sum(x * x for x in a) * sum(y * y for y in b)) ** .5 or 1)
order = [F["music"]] + sorted([m for m in M["music"] if m["film"] != F["music"]["film"] and not re.search(r"interview|lecture|speech", m["film"] or "", re.I)], key=lambda m: -cosv(m["mood"], mood))
seenf = set(); order = [m for m in order if not (m["film"] in seenf or seenf.add(m["film"]))]
music = order[: int(t // 24) + 2]
aud = lambda i: (lambda f: f if os.path.exists(f) else fetch(i))(os.path.join(L, "odyssey", "cache", "aud", i + ".flac"))   # the clip's own sound if the local copy is missing
ins = sum([["-i", aud(m["i"])] for m in music], [])
fc = "".join(f"[{k}:a]atrim=0:27,asetpts=PTS-STARTPTS,loudnorm=I=-20:TP=-2,aformat=sample_rates=48000:channel_layouts=stereo[a{k}];" for k in range(len(music))); ch = "[a0]"
for k in range(1, len(music)): fc += f"{ch}[a{k}]acrossfade=d=2.5:c1=tri:c2=tri[x{k}];"; ch = f"[x{k}]"
mute = "+".join(f"between(t,{a - .15:.2f},{b + .1:.2f})" for a, b in silent) or "0"
fc += f"{ch}atrim=0:{t:.2f},volume='if({mute},0,1)':eval=frame,afade=t=in:d=1.2,afade=t=out:st={t - 2.5:.2f}:d=2.5[m]"
wav = os.path.join(T, f"f{K}_score.wav"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", *ins, "-filter_complex", fc, "-map", "[m]", wav], check=True)
_m = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-18:TP=-1.5:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
_j = json.loads(_m[_m.rindex("{"):_m.rindex("}") + 1])
LN = f"loudnorm=I=-18:TP=-1.5:linear=true:measured_I={_j['input_i']}:measured_TP={_j['input_tp']}:measured_LRA={_j['input_lra']}:measured_thresh={_j['input_thresh']}:offset={_j['target_offset']}"
out = os.path.join(D, f"film-{K}.mp4")
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-af", LN, "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-maxrate", "1800k", "-bufsize", "3600k",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
json.dump({"seconds": round(t, 1), "music": [m["i"] for m in music], "edit": table}, open(os.path.join(D, f"film-{K}.json"), "w"), ensure_ascii=False, indent=1)
print(f"wrote {out} · {t:.1f} s · {len(parts)} pieces · music {[m['film'] for m in music]} · {os.path.getsize(out) / 1e6:.1f} MB")
