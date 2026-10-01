"""Lanes for the Syzygy page: every body on her clock, clip by clip, so the page can slide them under one line.

    python3 lab/syzygy/build_lanes.py     # after build_vertebrae.py → lab/syzygy/lanes.json, lab/syzygy/sprites/l*.jpg

Bodies (lanes), each a list of [t0, t1, sprite cell | null, sign | null, id]:
  voice      her words                                  bets/kernel-data.json
  spine      the generated images (first variant)       syzygy/vertebrae.json (spine vertebrae)
  board      the storyboard frame of each beat           vertebrae (board of the beat)
  suite · scenes · cineosis · drift   the plan.py cuts   syntagma/syntagma-data.json
  spinecut   Spine-Cut's clean film                      spinecut/spinecut-data.json
  forage     the forage cut                              wygwyl/WYGWYL_Forage_Cut.json
  archive    the router's pick for every vertebra from the 36,144 archive clips    syzygy/routing.json (route.py)
             items carry [.., id, realised (1|0), vertebra id]; "route" holds each pick's rule, fit, start and runners-up
  halfworld  the author's Halfworld reference frames, one per movement of each poem (4:3)   wygwyl/collage-data.json
  taxonomy · compound   two films from the chemistry trials: the ordinary taxonomy's best pick per slot, and a blind
             compound laid over the slots                chemistry/trials.json
Beats carry the signs they ask for; a body is in line when its sign is one of them.
Sprites keep each source's own aspect: lg* generated frames 240×135, la* archive shots with a local thumb 128×72,
lh* Halfworld frames 240×180. A shot without a local thumb takes a frame from its local clip or Tempest loop
(lab/clips, lab/wygwyl/tempest); only a shot with neither stays dark.
Motion: every lane shot with a Tempest loop or a local clip gets a flipbook: 24 frames at 8 fps (3 s), 128×72,
96×54, one row per shot in lf* sheets (16 shots × 24 frames each), listed in "flips" as [sheet, row]. The page shows the
frame for the playhead's time inside the shot, so scrubbing moves the picture exactly and nothing needs decoding.
Sources: lab/wygwyl/tempest/<id>.mp4, else lab/clips/<id>.mp4 (a 3 s loop cut into lab/syzygy/loops/, git-ignored).
Halfworld motion: the author's Halfworld pages rendered at 4 frames a second on her clock by render_halfworld.mjs
(window.__hw.renderAt, the pages' own renderer) into lab/syzygy/.halfworld-frames/<clock×4>.jpg, packed here into
lw* sheets of 20×20 frames at 128×96 and listed in "hw": [[first frame index, last, rank of first], …] per poem.
Gaps: the spine lane holds storyboard boards between her lines (as Spine-Cut does), and each storyboard frame
holds until the next beat that has one. Spine-Cut sections whose clean pick has no local picture show Spine-Cut's
next-ranked candidate that has one (marked "alt").
"""
import json, os, subprocess
from PIL import Image
try:
    import imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FF = "ffmpeg"

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
PER = 100


class Sheets:
    def __init__(self, prefix, w, h):
        self.prefix, self.w, self.h, self.idx, self.sheets = prefix, w, h, {}, []

    def add(self, key, path):
        if key in self.idx: return self.idx[key]
        if not path or not os.path.exists(path): return None
        k = len(self.idx)
        if k % PER == 0: self.sheets.append(Image.new("RGB", (self.w * 10, self.h * 10), (8, 8, 8)))
        im = Image.open(path).convert("RGB")
        r = max(self.w / im.width, self.h / im.height); im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))))
        l, t = (im.width - self.w) // 2, (im.height - self.h) // 2
        self.sheets[-1].paste(im.crop((l, t, l + self.w, t + self.h)), ((k % PER) % 10 * self.w, (k % PER) // 10 * self.h))
        self.idx[key] = k
        return k

    def save(self):
        for n, s in enumerate(self.sheets): s.save(os.path.join(HERE, "sprites", f"{self.prefix}{n}.jpg"), quality=74)
        return len(self.sheets)



J = lambda *p: json.load(open(os.path.join(LAB, *p)))


def main():
    V = json.load(open(os.path.join(HERE, "vertebrae.json")))["vertebrae"]
    K = J("bets", "kernel-data.json"); SD = J("syntagma", "syntagma-data.json"); SC = J("spinecut", "spinecut-data.json")
    FC = J("wygwyl", "WYGWYL_Forage_Cut.json")["shots"]; LDd = J("lab-data.json")
    LD = {s["id"]: s for s in LDd["shots"]}
    sign_of = lambda i: ((LD.get(i) or {}).get("aff_top") or [[(SC["shots"].get(i) or {}).get("sg")]])[0][0]
    for f in os.listdir(os.path.join(HERE, "sprites")):
        if f.startswith("l"): os.remove(os.path.join(HERE, "sprites", f))
    G, A, HW = Sheets("lg", 240, 135), Sheets("la", 128, 72), Sheets("lh", 240, 180)
    meta = {}

    FR = os.path.join(HERE, ".frames"); LO = os.path.join(HERE, "loops"); os.makedirs(FR, exist_ok=True); os.makedirs(LO, exist_ok=True)
    vids = {}
    def src_video(i):
        t, c = os.path.join(LAB, "wygwyl", "tempest", f"{i}.mp4"), os.path.join(LAB, "clips", f"{i}.mp4")
        return (1, t) if os.path.exists(t) else (2, c) if os.path.exists(c) else (0, None)
    def picture(i):
        th = os.path.join(LAB, "thumbs", f"{i}.jpg")
        if os.path.exists(th): return th
        kind, v = src_video(i)
        if not v: return None
        out = os.path.join(FR, f"{i}.jpg")
        if not os.path.exists(out):
            subprocess.run([FF, "-v", "error", "-y", "-ss", "0.8", "-i", v, "-frames:v", "1", out], check=False)
        return out if os.path.exists(out) else None
    def video(i):
        if i in vids: return
        kind, v = src_video(i)
        if kind == 2:
            out = os.path.join(LO, f"{i}.mp4")
            if not os.path.exists(out):
                subprocess.run([FF, "-v", "error", "-y", "-ss", "1", "-t", "3", "-i", v, "-an", "-vf", "scale=240:-2,fps=20",
                                "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=False)
            if not os.path.exists(out): return
        if kind: vids[i] = kind

    def arch(i):
        if not i: return None
        video(i)
        k = A.add(i, picture(i))
        if k is not None and i not in meta:
            s = LD.get(i) or SC["shots"].get(i) or {}
            meta[i] = [s.get("title"), s.get("year"), s.get("video")]
        return k

    lanes = {}
    lanes["voice"] = [[round(w["t0"], 2), round(w["t1"], 2), None, None, w["w"]] for L in K["lines"] for w in L["words"]]
    sp, prompts = [], {}
    for v in V:
        if v["kind"] != "spine": continue
        th = (v.get("image") or [{}])[0].get("thumb")
        k = G.add(th, os.path.join(LAB, th)) if th else None
        rd = [a[0] for a in ((v.get("image") or [{}])[0].get("aff") or [])]
        sp.append([v["t0"], v["t1"], k, rd, v["id"]])
        it = v.get("intended") or {}
        prompts[v["id"]] = [it.get("syntagmaType"), it.get("cineosisFunction"), it.get("operativeEkphrasis"), v["clock"]["words"]]
    # between her lines the spine is held by storyboard boards, as in Spine-Cut
    for v in V:
        if v["kind"] == "board":
            th = (v.get("image") or [{}])[0].get("thumb")
            if th: sp.append([v["t0"], v["t1"], G.add(th, os.path.join(LAB, th)), None, v["id"]])
    lanes["spine"] = sorted(sp)
    bd, seen = [], set()
    for b in K["beats"]:
        vb = next((v for v in V if v["beat"]["n"] == b["id"] and v["beat"]["board"]), None)
        if not vb: continue
        x = vb["beat"]["board"][0]
        if x.get("thumb"): bd.append([b["t0"], b["t1"], G.add(x["thumb"], os.path.join(LAB, x["thumb"])), None, x["id"]])
    for a, b in zip(bd, bd[1:]): a[1] = max(a[1], b[0])       # a storyboard frame holds until the next one
    lanes["board"] = bd
    for ver in SD["versions"]:
        lanes[ver["slug"]] = [[s[0], s[1], arch(s[2]), s[9], s[2]] for s in ver["shots"]]
    spc = []
    for s in SC["sections"]:
        pick = s.get("clean")
        if not pick: continue
        alt = 0
        if not picture(pick):
            nxt = next((c for c in [s.get("echo")] + (s.get("quad") or []) + (s.get("cand") or []) if c and picture(c)), None)
            if nxt: pick, alt = nxt, 1
        spc.append([s["t0"], s["t1"], arch(pick), sign_of(pick), pick] + ([1] if alt else []))
    lanes["spinecut"] = spc
    lanes["forage"] = [[s["start"], s["end"], arch(s.get("selected")), sign_of(s.get("selected")), s.get("selected")] for s in FC if s.get("selected")]

    # the route: every vertebra's archive clip (route.py). Pictures from a local thumb or clip where the lab has one; the
    # page streams the rest (thumbnail and video) from the archive
    RT = json.load(open(os.path.join(HERE, "routing.json")))
    pool = {}
    for lib in (os.path.join(LAB, "markov", "library.json"), os.path.join(LAB, "odyssey", "all", "library.json")):
        for s_ in json.load(open(lib))["shots"]: pool.setdefault(s_["id"], s_)
    ar, route = [], {}
    for r in RT["route"]:
        c = r["clip"]; i = c["id"]
        k = arch(i) if picture(i) else None
        if i not in meta: meta[i] = [c["title"], c["year"], c["video"]]
        meta[i] = meta[i][:3] + [c["thumb"], c["dur"]]
        sg = ((pool.get(i) or {}).get("signs") or [None])[0]
        ar.append([r["t0"], r["t1"], k, sg, i, 1 if r["realised"] else 0, r["v"]])
        route[r["v"]] = [r["syntagma"], r["rule"], r["fit"], c["start"], [a for a in r["alts"][:4]]]
        for a in r["alts"][:4]:
            if a not in meta and a in pool:
                x = pool[a]; v = x["video"]
                meta[a] = [x.get("title"), x.get("year"), v, v.replace("/clips/", "/thumbnails/").rsplit(".", 1)[0] + ".jpg" if "/clips/" in v else None, x.get("dur")]
    lanes["archive"] = ar

    CD = J("wygwyl", "collage-data.json"); hw = []
    for wd in CD["worlds"]:
        for m in wd.get("movements", []):
            k = HW.add(m["frame"], os.path.join(LAB, m["frame"]))
            hw.append([m["t0"], m["t1"], k, None, m["frame"]]); prompts[m["frame"]] = [wd["title"], m.get("label"), m.get("line"), None]
    lanes["halfworld"] = sorted(hw)
    T = J("chemistry", "trials.json")
    for lane, film in (("taxonomy", "B-taxonomy"), ("compound", "G-compound")):
        lanes[lane] = sorted([[x["t0"], x["t1"], arch(x["id"]), x.get("sg"), x["id"]] for p in T["poems"] for x in p["films"][film]])
    # flipbooks: the frame at any moment of a shot, for scrubbing
    for f in os.listdir(os.path.join(HERE, "sprites")):
        if f.startswith("lf"): os.remove(os.path.join(HERE, "sprites", f))
    FW, FH, NF, ROWS = 96, 54, 24, 16
    flips, fsheets = {}, []
    for i, kind in sorted(vids.items()):
        src = os.path.join(LAB, "wygwyl", "tempest", f"{i}.mp4") if kind == 1 else os.path.join(LO, f"{i}.mp4")
        r = subprocess.run([FF, "-v", "error", "-i", src, "-vf", f"fps=8,scale={FW}:{FH}:force_original_aspect_ratio=increase,crop={FW}:{FH}",
                            "-frames:v", str(NF), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
        n = len(r.stdout) // (FW * FH * 3)
        if n < 2: continue
        k = len(flips)
        if k % ROWS == 0: fsheets.append(Image.new("RGB", (FW * NF, FH * ROWS), (0, 0, 0)))
        for j in range(NF):   # a short clip repeats its frames to fill the row
            fr = Image.frombytes("RGB", (FW, FH), r.stdout[(j % n) * FW * FH * 3:((j % n) + 1) * FW * FH * 3])
            fsheets[-1].paste(fr, (j * FW, (k % ROWS) * FH))
        flips[i] = [k // ROWS, k % ROWS]
    for n, sh in enumerate(fsheets): sh.save(os.path.join(HERE, "sprites", f"lf{n}.jpg"), quality=70)
    # Halfworld: the rendered pages, frame by frame on her clock
    for f in os.listdir(os.path.join(HERE, "sprites")):
        if f.startswith("lw"): os.remove(os.path.join(HERE, "sprites", f))
    HWD, hw_runs, hw_sheets = os.path.join(HERE, ".halfworld-frames"), [], []
    if os.path.isdir(HWD):
        idxs = sorted(int(f[:-4]) for f in os.listdir(HWD) if f.endswith(".jpg"))
        for rank, i in enumerate(idxs):
            if hw_runs and hw_runs[-1][1] == i - 1: hw_runs[-1][1] = i
            else: hw_runs.append([i, i, rank])
            if rank % 400 == 0: hw_sheets.append(Image.new("RGB", (128 * 20, 96 * 20)))
            im = Image.open(os.path.join(HWD, f"{i:05d}.jpg")).convert("RGB").resize((128, 96))
            hw_sheets[-1].paste(im, ((rank % 400) % 20 * 128, (rank % 400) // 20 * 96))
        for n, sh in enumerate(hw_sheets): sh.save(os.path.join(HERE, "sprites", f"lw{n}.jpg"), quality=72)
    ng, na, nh = G.save(), A.save(), HW.save()
    signs = {s["n"]: [s["symbol"], s["name"], s["dom"]] for s in LDd["signs"]}
    out = {"dur": SD["duration"], "films": [[f["n"], f["title"], f["t0"], f["t1"]] for f in K["films"]],
           "beats": [[b["t0"], b["t1"], b["codes"], b["title"], b["id"]] for b in K["beats"]],
           "order": ["voice", "spine", "archive", "halfworld", "board", "suite", "scenes", "cineosis", "drift", "spinecut", "forage", "taxonomy", "compound"],
           "lanes": lanes, "sheets": {"lg": [ng, 240, 135], "la": [na, 128, 72], "lh": [nh, 240, 180]}, "meta": meta, "prompts": prompts, "route": route, "routing": {k: RT[k] for k in ("bridge", "pool", "realised", "fit", "films", "clips")}, "signs": signs, "flips": flips, "flip": [len(fsheets), FW, FH, NF, 8], "hw": hw_runs, "hwf": [len(hw_sheets), 128, 96, 4]}
    json.dump(out, open(os.path.join(HERE, "lanes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    dark = {k: sum(1 for x in v if x[2] is None) for k, v in lanes.items() if k != "voice"}
    print({k: len(v) for k, v in lanes.items()}, "·", len(G.idx), "generated,", len(A.idx), "archive pictures,", len(flips), "flipbooks in", len(fsheets), "sheets · dark:", dark)


if __name__ == "__main__":
    main()
