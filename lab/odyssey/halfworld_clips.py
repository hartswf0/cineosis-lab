"""The halfworld's own film of every scene, small enough for a tile: cut from the halfworld book films (rendered by its harness,
not published there) using the render's own shot logs, 320x180, 12 fps, silent. The film follows our studio voice recording, so a
moment of the voice maps to the film by proportion (film length / recording length).
Writes halfworld/<scene>.mp4 and halfworld/index.json {scene: {dur, voice}}.   usage: python3 halfworld_clips.py"""
import glob, json, os, subprocess, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); HW = os.path.expanduser("~/Downloads/odyssey-halfworld/film"); OUT = os.path.join(H, "halfworld")
shots = []
for f in glob.glob(os.path.join(HW, ".segments", "1280x720@24", "seg-*.mp4.log.json")):
    shots += [(s[0], s[1].split("|")[0]) for s in json.load(open(f))["shots"]]
shots.sort(); start = {}
for fr, sid in shots: start.setdefault(sid, fr)
ids = sorted(start, key=start.get); end = {a: start[b] for a, b in zip(ids, ids[1:])}; end[ids[-1]] = shots[-1][0] + 24 * 30
voice = {s["id"]: s["total"] for b in json.load(open(os.path.join(H, "radio.json")))["books"] for s in b["scenes"]}
bookstart = {}
for sid in ids: bookstart.setdefault(sid[:6], start[sid])
def cut(sid):
    b = int(sid[4:6]); src = os.path.join(HW, "books", f"odyssey-book-{b:02d}.mp4"); out = os.path.join(OUT, sid + ".mp4")
    off, dur = (start[sid] - bookstart[sid[:6]]) / 24, (end[sid] - start[sid]) / 24
    if not os.path.exists(out):
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{off:.3f}", "-i", src, "-t", f"{dur:.3f}", "-an", "-vf", "scale=320:180,fps=12",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "34", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out])
    return sid, round(dur, 2)
with cf.ThreadPoolExecutor(4) as ex: idx = {sid: {"dur": d, "voice": voice.get(sid)} for sid, d in ex.map(cut, ids)}
json.dump(idx, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
print(len(idx), "scenes cut ·", round(sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT) if f.endswith(".mp4")) / 1e6, 1), "MB")
