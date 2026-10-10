"""NORSE HALF MOON, stage two: the sound, rendered by the found Odyssey's own CALL renderer (../odyssey/render_found.py, run as written):
the memo's voice says each line plainly from its own seconds, a breath, then the archival answer in the shared medium (hiss lowered,
tone matched, one band, evened, loudness set on its words), every answer heard back by Whisper and its tail lengthened until its last
word is heard, one room and one floor under all of it, the pauses filled with each voice's own room sound. No music: the Odyssey's
bed belongs to the Odyssey. Then the program for the one-button page (program.json).   usage: ~/.cache/mlxw-venv/bin/python norse/render.py"""
import json, os, re, sys
N = os.path.dirname(os.path.abspath(__file__)); OD = os.path.join(os.path.dirname(N), "odyssey")
sys.path.insert(0, N); from build_marks import marks   # the shared-word marks, as the museum program makes them
poem = json.load(open(os.path.join(N, "poem.json"))); pics = json.load(open(os.path.join(N, "pics.json")))
# the memo is our Homer: the renderer looks for each scene's voice at HW/drive/voice/<scene>.m4a
HW = os.path.join(N, "hw"); os.makedirs(os.path.join(HW, "drive", "voice"), exist_ok=True)
for B in poem["books"]:
    v = os.path.join(HW, "drive", "voice", B["id"] + ".m4a")
    if not os.path.exists(v): os.symlink(os.path.join(N, "source.mp3"), v)
src = open(os.path.join(OD, "render_found.py")).read(); src = src[: src.index('if sys.argv[1:2] == ["--merge"]')]
argv = sys.argv; sys.argv = [argv[0]]
G = {"__file__": os.path.join(OD, "render_found.py"), "__name__": "render_norse"}; exec(compile(src, "render_found.py", "exec"), G); sys.argv = argv
G["HW"] = HW; G["OUT"] = os.path.join(N, "audio"); G["CP"] = os.path.join(N, "render-check.json"); G["book_of"] = {}
G["found"]["scenes"] = {B["id"]: B["lines"] for B in poem["books"]}
W = [w for s in json.load(open(os.path.join(N, "whisper.json")))["segments"] for w in s["words"]]
scenes = []
for B in poem["books"]:
    r = G["render"](B["id"], "call"); json.dump(G["CHECK"], open(G["CP"], "w"))
    if not r: print("no sound for", B["id"]); continue
    calls = {e["li"]: e for e in r["ev"] if e.get("call")}; answers = {}
    for e in r["ev"]:
        if not e.get("call") and "id" in e: answers.setdefault(e["li"], []).append(e)
    lines, beside, P = [], [], []
    for li, u in enumerate(B["lines"]):
        c = calls.get(li); A = answers.get(li, [])
        if not c: continue
        sp = u["modes"]["spoken"]["frags"]; atext = " ".join(f["words"] for f in sp); hl, ha = marks(u["say"], atext)
        ws = [w for w in W if w["start"] >= u["t0"] - .05 and w["end"] <= u["t1"] + .05]; sw = u["say"].split()
        lt = [round(c["at"] + max(0, w["start"] - u["t0"]), 2) for w in ws if re.sub(r"[^a-z]", "", w["word"].lower()) not in ("um", "uh", "erm", "umm")]
        L0 = poem["clips"].get(sp[0]["id"], {}) if sp else {}
        lines.append({"at": c["at"], "end": c["end"], "text": u["say"], "who": "the memo", "ans": atext, "aat": A[0]["at"] if A else c["end"], "aend": A[-1]["end"] if A else c["end"],
                      "hl": hl, "ha": ha, "lt": lt if len(lt) == len(sw) else None, "src": ", ".join(str(x) for x in (L0.get("title"), L0.get("year")) if x), "sc": u["modes"]["spoken"]["score"]})
        for e in A: beside.append({"sw": round(e["at"] - .35, 2), "end": round(e["end"] + .45, 2), "video": poem["clips"][e["id"]]["video"], "in": round(max(0, e["t0"] - .35), 2)})
        p = pics[B["id"]][li]; P.append({"sw": round(max(.25, c["at"] - .6), 2), "dd": 1600, "tr": "dissolve", "video": p["video"], "in": p["in"], "rate": .8})
    scenes.append({"id": B["id"], "book": B["n"], "bnum": "ONE TWO THREE FOUR FIVE SIX SEVEN".split()[B["n"] - 1], "btitle": B["title"], "title": "", "card": B["card"],
                   "audio": "norse/audio/call/" + B["id"] + ".m4a", "dur": r["dur"], "lines": lines, "pics": P, "beside": beside})
    print(B["id"], B["title"], r["dur"], "s ·", len(lines), "lines", flush=True)
prog = {"title": "Norse Half Moon", "sub": "", "root": "", "end": "A voice memo about a house on the Half Moon Bay coast, answered by the archive.", "scenes": scenes}
json.dump(prog, open(os.path.join(N, "program.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(len(scenes), "books ·", round(sum(s["dur"] for s in scenes) / 60, 1), "min")
