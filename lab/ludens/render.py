"""Render a film played in Ludens to an MP4: each shot from its own in-point for exactly its length (the line of flight's timing), a song
under it, and a measure of the film by the same critic the games use (the cut, the chemistry, the story's beats, repetition), against
the story cut. Films are JSON: {"name", "shots": [{"id", "d"}]} (Ludens: copy(JSON.stringify(...)) or the games' export).
usage: python3 lab/ludens/render.py film.json out.mp4 [--song 14 --at 0]   |   python3 lab/ludens/render.py --measure film.json"""
import json, os, sys, subprocess, math
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); SF = os.path.join(L, "slopfeeder")
C = json.load(open(os.path.join(D, "corpus.json"))); BY = {c["id"]: c for c in C["cards"]}; SIG = {s["s"]: s for s in C["signs"]}
FAMS = ['perception', 'affection', 'impulse', 'action', 'reflection', 'relation', 'memory', 'time']
A = json.load(open(os.path.join(SF, "atlas.json")))["cards"]; IX = {c["id"]: i for i, c in enumerate(A)}
E = np.fromfile(os.path.join(SF, "atlas-emb.bin"), np.int8).reshape(len(A), -1).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
def cut(a, b): c = float(E[IX[a]] @ E[IX[b]]); return math.exp(-(((c - .72) / .12) ** 2) / 2)
def chem(a, b):
    fa, fb = SIG.get(BY[a]["sg"], {}).get("fam", "time"), SIG.get(BY[b]["sg"], {}).get("fam", "time"); A_, B_ = FAMS.index(fa), FAMS.index(fb)
    if BY[a]["sg"] == BY[b]["sg"]: return "echo"
    if A_ == B_: return "isotope"
    if A_ < 6 and B_ < 6 and B_ - A_ in (1, 2): return "bond"
    if 2 <= A_ <= 5 and B_ >= 6: return "crystal"
    if A_ < 6 and B_ < 6 and B_ < A_: return "backflow"
    return "leap"
def slope(ids):   # Spearman rho between when a shot plays and where it sits on the story axis: 1 = the film climbs the story, 0 = no story
    if len(ids) < 3: return 0
    r = lambda v: np.argsort(np.argsort(v)).astype(float); x = r(np.arange(len(ids))); y = r(np.array([BY[i]["sx"] for i in ids])); return round(float(np.corrcoef(x, y)[0, 1]), 3)
def measure(ids, name, durs=None):
    ids = [i for i in ids if i in BY and i in IX]; seams = [cut(a, b) for a, b in zip(ids, ids[1:])]; ch = [chem(a, b) for a, b in zip(ids, ids[1:])]
    beats = [h["id"] for h in C["holes"]]; hit = [b for b in beats if b in ids]; order = [ids.index(b) for b in hit]; inorder = sum(1 for x, y in zip(order, order[1:]) if y > x)
    n = max(1, len(seams)); m = {"film": name, "shots": len(ids), "mean cut": round(float(np.mean(seams)) if seams else 0, 3), "jarring": round(sum(1 for s in seams if s < .35) / n, 3), "good": round(sum(1 for s in seams if s >= .6) / n, 3),
         "bonds+crystals": round(sum(1 for k in ch if k in ("bond", "crystal")) / n, 3), "backflow+echo": round(sum(1 for k in ch if k in ("backflow", "echo")) / n, 3), "story beats": len(hit), "beats in order": f"{inorder}/{max(0, len(hit) - 1)}", "repeats": len(ids) - len(set(ids)), "story slope": slope(ids), "flickers": sum(1 for d in (durs or []) if d < .9)}
    return m
def story_cut():
    st = json.load(open(os.path.join(SF, "story.json"))); lat = json.load(open(os.path.join(SF, "lattice", "story.json"))); return [c["cands"][0].get("id") for c in lat["cols"] if c["cands"][0].get("id") in BY]
def luma(src, t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=32:18", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).astype(float) if b else np.zeros(1)
def lit(src, du, d):   # the in-point nearest the middle whose window is neither black nor a blank card (fades and leaders are common in the archive)
    for f in (.5, .35, .65, .2, .8, .05):
        ss = max(0.0, min(du - d, du * f - d / 2)); fr = [luma(src, ss + d * g) for g in (.1, .5, .9)]
        if all(x.mean() > 18 and x.std() > 6 for x in fr): return ss
    return max(0.0, du / 2 - d / 2)
def render(film, out, song=None, at=0.0):
    T = os.path.join(SF, "src", "ludens", os.path.splitext(os.path.basename(out))[0]); os.makedirs(T, exist_ok=True); parts = []; ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "24", "-an"]
    for k, s in enumerate(film["shots"]):
        c = BY[s["id"]]; d = max(.4, float(s["d"]))
        if c["k"] == "ai": src = os.path.join(SF, "ai", "src", os.path.basename(c["m"])); src = src if os.path.exists(src) else os.path.join(L, c["m"]); ss = c.get("ss") or 0
        else:
            src = os.path.join(SF, "fclips", c["id"] + ".mp4")
            if not os.path.exists(src): subprocess.run(["curl", "-sfL", "-A", "cineosis-44-research", "-o", src, c["m"]])
            ss = lit(src, c.get("du") or 4, d)
        o = os.path.join(T, f"{k:03d}.mp4"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-i", src, "-vf", f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1,fps=24,tpad=stop_mode=clone:stop_duration={d:.2f}", "-t", f"{d:.3f}", *ENC, o], check=True); parts.append(o)
    lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts)); vid = os.path.join(T, "v.mp4"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    total = sum(max(.4, float(s["d"])) for s in film["shots"])
    if song:
        S = {x["n"]: x for x in json.load(open(os.path.join(SF, "songs.json")))["songs"]}[song]; f = os.path.join(os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"), S["file"])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-ss", str(at), "-t", f"{total:.2f}", "-i", f, "-filter_complex", f"[1:a]afade=t=in:d=0.8,afade=t=out:st={max(0, total - 2):.2f}:d=2[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    else: os.replace(vid, out)
    return out
if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--measure":
        for p in a[1:]: f = json.load(open(p)); print(json.dumps(measure([s["id"] for s in f["shots"]], f.get("name", p), [s["d"] for s in f["shots"]])))
        print(json.dumps(measure(story_cut(), "the story cut (as made)"))); sys.exit()
    f = json.load(open(a[0])); song = a[a.index("--song") + 1] if "--song" in a else None; at = float(a[a.index("--at") + 1]) if "--at" in a else 0.0
    print(render(f, a[1], song, at)); print(json.dumps(measure([s["id"] for s in f["shots"]], f.get("name", a[0]))))
