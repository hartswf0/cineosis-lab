"""A Markov Poet film as a real video (MP4), rendered by the lab: the same cut the room played, the shots dissolving into one
another, the words large, each shot's Cineosis DNA small in the corner, the voice (Piper, the recording, or the person's own).

    python markov/render.py job.json      (the lab server calls it: POST /api/render)
job = {"cut": [{"video", "in", "t0", "t1", "dna"}], "phrases": [{"t0", "t1", "text"}], "T0", "T1",
       "audio": {"src", "offset"} | null, "audio_b64": "data:audio/...;base64,..." | null, "sound": bool, "calm": bool, "out": "markov/renders/x"}
Prints the output path. Clips are cached in markov/cache/clips/."""
import base64, hashlib, json, os, subprocess, sys, tempfile, textwrap, urllib.request
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
W, HH, FPS = 1280, 720, 25
FONT = "/System/Library/Fonts/Supplemental/Georgia.ttf"; MONO = "/System/Library/Fonts/Supplemental/Courier New.ttf"
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(" ".join(cmd[:6]) + " … " + r.stderr[-600:])
def source(u):
    if not u.startswith("http"): return os.path.join(LAB, u)
    os.makedirs(os.path.join(H, "cache", "clips"), exist_ok=True)
    p = os.path.join(H, "cache", "clips", hashlib.sha1(u.encode()).hexdigest()[:20] + ".mp4")
    if not os.path.exists(p):
        with urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "cineosis-44-research"}), timeout=120) as r: open(p + ".part", "wb").write(r.read())
        os.replace(p + ".part", p)
    return p
def esc_path(p): return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
def main(job):
    cut, T0, T1 = job["cut"], job["T0"], job["T1"]
    tmp = tempfile.mkdtemp(prefix="mp-render-")
    X = 1.4 if job.get("calm") else .8
    durs = [max(.3, c["t1"] - c["t0"]) for c in cut]; durs[-1] = max(durs[-1], T1 - cut[-1]["t0"])
    xs = [0] + [min(X, durs[i - 1] * .45, durs[i] * .45) for i in range(1, len(cut))]
    segs, auds = [], []
    for i, c in enumerate(cut):
        L = durs[i] + (xs[i + 1] if i + 1 < len(cut) else 0); src = source(c["video"])
        tf = os.path.join(tmp, f"dna{i}.txt"); open(tf, "w").write(c.get("dna") or "")
        vf = (f"scale={W}:{HH}:force_original_aspect_ratio=increase,crop={W}:{HH},fps={FPS},setsar=1,tpad=stop_mode=clone:stop_duration={L:.2f},"
              + ("setpts=PTS/0.8," if job.get("calm") else "")
              + f"drawtext=fontfile='{MONO}':textfile='{esc_path(tf)}':fontsize=15:fontcolor=white@0.62:x=w-tw-28:y=h-th-24,format=yuv420p")
        out = os.path.join(tmp, f"s{i:03d}.mp4")
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{max(0, c.get('in', 0)):.2f}", "-i", src, "-t", f"{L + 1:.2f}", "-vf", vf,
             "-frames:v", str(max(1, round(L * FPS))), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])
        segs.append(out)
        if job.get("sound"):
            a = os.path.join(tmp, f"a{i:03d}.wav")
            r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{max(0, c.get('in', 0)):.2f}", "-i", src, "-t", f"{durs[i]:.2f}", "-vn", "-ac", "2", "-ar", "44100",
                                "-af", f"apad=whole_dur={durs[i]:.3f},afade=t=in:d=.25,afade=t=out:st={max(0, durs[i] - .3):.2f}:d=.3", a], capture_output=True)
            if r.returncode or not os.path.exists(a):
                run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{durs[i]:.3f}", a])
            auds.append(a)
    # the shots dissolve into one another: each segment carries the overlap its successor fades in over
    inputs, fc, last, off = [], [], "0:v", 0.0
    for s in segs: inputs += ["-i", s]
    for k in range(1, len(segs)):
        off += durs[k - 1]; lab = f"v{k}"
        fc.append(f"[{last}][{k}:v]xfade=transition=fade:duration={xs[k]:.3f}:offset={off:.3f}[{lab}]"); last = lab
    # the words, large, fading in and out on their own clock
    total = sum(durs); tx = []
    for j, p in enumerate(job["phrases"]):
        a, b = max(0, p["t0"] - T0), min(total, p["t1"] - T0)
        if b - a < .2: continue
        rows = textwrap.wrap(p["text"], 40)[:3]
        for r, row in enumerate(rows):
            tf = os.path.join(tmp, f"l{j}_{r}.txt"); open(tf, "w").write(row)
            y = f"h*0.74-{(len(rows) - 1 - r) * 58}"
            al = f"if(lt(t,{a:.2f}),0,if(lt(t,{a + .45:.2f}),(t-{a:.2f})/.45,if(lt(t,{b - .45:.2f}),1,max(0,({b:.2f}-t)/.45))))"
            tx.append(f"drawtext=fontfile='{FONT}':textfile='{esc_path(tf)}':fontsize=46:fontcolor=white:alpha='{al}':shadowcolor=black@0.7:shadowx=0:shadowy=2:borderw=1:bordercolor=black@0.35:x=(w-tw)/2:y={y}:enable='between(t,{a:.2f},{b:.2f})'")
    fc.append(f"[{last}]" + (",".join(tx) if tx else "null") + "[vout]")
    n = len(segs)
    # the voice, and under it (if asked) the films' own sound
    voice = None
    if job.get("audio_b64"):
        head, data = job["audio_b64"].split(",", 1); ext = ".webm" if "webm" in head else ".mp4" if "mp4" in head else ".mp3"
        voice = os.path.join(tmp, "voice" + ext); open(voice, "wb").write(base64.b64decode(data)); vss = 0.0
    elif job.get("audio"):
        voice = os.path.join(LAB, job["audio"]["src"]); vss = max(0.0, T0 - job["audio"].get("offset", 0))
    ain = []
    if voice: inputs += ["-ss", f"{vss:.2f}", "-i", voice]; ain.append(f"[{n}:a]atrim=0:{total:.3f},apad=whole_dur={total:.3f}[voice]")
    if auds:
        lst = os.path.join(tmp, "bed.txt"); open(lst, "w").write("".join(f"file '{a}'\n" for a in auds))
        bed = os.path.join(tmp, "bed.wav"); run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", bed])
        inputs += ["-i", bed]; ain.append(f"[{n + (1 if voice else 0)}:a]volume=0.4,apad=whole_dur={total:.3f}[bed]")
    if voice and auds: ain.append("[voice]volume=2[v2];[v2][bed]amix=inputs=2:duration=first[aout]")
    elif voice: ain.append("[voice]anull[aout]")
    elif auds: ain.append("[bed]anull[aout]")
    else: inputs += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]; ain.append(f"[{n}:a]anull[aout]")
    out = os.path.join(LAB, job["out"] + ".mp4"); os.makedirs(os.path.dirname(out), exist_ok=True)
    fcs = os.path.join(tmp, "graph.txt"); open(fcs, "w").write(";".join(fc + ain))
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex_script", fcs, "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.3f}", "-movflags", "+faststart", out])
    return job["out"] + ".mp4"
if __name__ == "__main__":
    print(main(json.load(open(sys.argv[1]))))
