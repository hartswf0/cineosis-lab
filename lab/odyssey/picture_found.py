"""The picture for the found Odyssey: what we see while the archive speaks, and how one picture gives way to the next.
  story     the picture follows the poem, not the voice: each line sits on the footage the captains judged for the shot it falls in
            (the steersman's pick, or the alternatives the captains did not reject), held for the whole line, and held on across
            lines that stay in the same shot; voices are heard over it, as voice-over
  speaker   a line is cut to the person saying it only when the archive shows them: the voice's own clip, at the moment of the
            words, shows a face speaking (CLIP on the frame); then we see a found actor say the character's line, in sync
  choice    among the good pictures for a shot, the one that joins best: closest to the picture before it in look (CLIP) and in
            light (mean brightness), chosen across the whole scene at once (Viterbi), never too short for its hold
  joins     a near match is a straight cut; a related picture dissolves slowly; unrelated pictures dip toward dark through the
            pause and rise into the next, so the picture breathes when the sound does; every change happens in a pause, never
            over a word, beginning in the silence and finishing as the next voice begins
  motion    the story plays at 80% speed with a slow push-in; speakers play at true speed
Writes found-pics.json {scene: {mode: [{sw, dd, tr, kind, id, video, in, rate, hold}]}}.   usage: ../.venv/bin/python picture_found.py"""
import glob, json, os, subprocess, concurrent.futures as cf
import numpy as np, torch, open_clip
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__))
found = json.load(open(os.path.join(H, "found.json"))); TR = found.get("scene_tracks", {})
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); EM = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32)
EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9; row = {i: n for n, i in enumerate(ids)}
sea = {s["id"]: s for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))) for s in json.load(open(f))["scenes"]}
_b = {}
def bright(i):
    if i not in _b:
        try: _b[i] = float(np.asarray(Image.open(os.path.join(H, "thumbs", i + ".jpg")).convert("L"), np.float32).mean() / 255)
        except Exception: _b[i] = .4
    return _b[i]
def look(i): return EM[row[i]] if i in row else None
def join(a, b):
    """How badly two pictures join: unlike in look and in light."""
    ea, eb = look(a["id"]), look(b["id"]); cos = float(ea @ eb) if ea is not None and eb is not None else .7
    return (1 - cos) + 1.5 * abs(a.get("b", bright(a["id"])) - b.get("b", bright(b["id"]))), cos
def dur_of(i):
    try: return float(lib[i]["dur"])
    except Exception: return 8.0
# ---- speakers: does the voice's own clip show a face speaking at that moment?
SP = os.path.join(H, "cache", "speaker-frames.json"); SPK = json.load(open(SP)) if os.path.exists(SP) else {}
FR = os.path.join(H, "cache", "speaker-frames"); os.makedirs(FR, exist_ok=True)
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
POS = ["a close-up of a person talking", "a man speaking to the camera", "a woman speaking to the camera", "a person's face as they talk", "an actor delivering a line in an old film"]
NEG = ["a landscape", "a crowd of people far away", "a machine", "text on a screen", "an animal", "a building", "people walking", "a diagram", "the sea", "hands doing work"]
with torch.no_grad(): TX = m.encode_text(tok(POS + NEG)).float(); TX /= TX.norm(dim=-1, keepdim=True)
def grab(job):
    k, url, t = job; p = os.path.join(FR, k.replace("@", "_") + ".jpg")
    if not os.path.exists(p): subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{t:.2f}", "-i", url, "-frames:v", "1", "-vf", "scale=320:-2", p], timeout=60)
    return k, p
jobs = []
for sid, tm in TR.items():
    t = tm.get("spoken")
    if not t: continue
    for e in t["ev"]:
        u = found["scenes"][sid][e["li"]]
        if e.get("id") and u["who"] != "Epic Narrator" and e["end"] - e["at"] >= 1.2:
            k = f"{e['id']}@{e['t0']}"
            if k not in SPK and e["id"] in lib: jobs.append((k, lib[e["id"]]["video"], e["t0"] + .5 * (e["end"] - e["at"])))
print(len(jobs), "speaker frames to look at", flush=True)
with cf.ThreadPoolExecutor(4) as ex:
    for k, p in ex.map(grab, jobs):
        try:
            im = Image.open(p).convert("RGB")
            with torch.no_grad(): v = m.encode_image(pre(im)[None]).float(); v /= v.norm(dim=-1, keepdim=True)
            pr = (100 * v @ TX.T).softmax(-1)[0].numpy(); SPK[k] = {"talk": round(float(pr[: len(POS)].sum()), 3), "b": round(float(np.asarray(im.convert("L")).mean() / 255), 3), "emb": v[0].numpy().round(4).tolist()}
        except Exception: SPK[k] = {"talk": 0}
import cv2                                                              # and is there a real face, large enough to be speaking to us
FC = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
for k, v in SPK.items():
    if "face" in v: continue
    g = cv2.imread(os.path.join(FR, k.replace("@", "_") + ".jpg"), 0)
    f = FC.detectMultiScale(cv2.equalizeHist(g), 1.1, 6, minSize=(24, 24)) if g is not None else []
    v["face"] = round(max([w / g.shape[1] for x, y, w, h in f] or [0]), 3) if g is not None else 0
json.dump(SPK, open(SP, "w"))
# ---- the plan
def shot_of(sc, u):
    best, ov = None, 0
    for sh in sc["shots"]:
        a, b = float(sh["t0"]), float(sh["t0"]) + float(sh["dur"]); o = min(b, u["t1"]) - max(a, u["t0"])
        if o > ov: best, ov = sh, o
    return best
def options(sh):
    """The pictures the shot may wear: the captain's pick first, then the alternatives (the captain's NOTHING costs every one)."""
    if not sh: return []
    cap = sh.get("captain") or {}; alts = [sh] + list(sh.get("sea") or []); out = []
    pick = cap.get("pick") if cap.get("verdict") in ("KEEP", "REPLACE") else None
    for n, a in enumerate(alts):
        if a["id"] not in lib: continue
        c = 0.0 if a["id"] == pick else (.12 + .03 * n) + (.1 if cap.get("verdict") == "NOTHING" else 0)
        out.append({"id": a["id"], "in": float(a.get("in") or 0), "cost": c, "video": a.get("video") or lib[a["id"]]["video"]})
    out.sort(key=lambda o: o["cost"]); return out[:6]
RATE = .8
# what counts as alike is measured, not assumed: across the archive's pictures a join in the top 15% of likeness is a cut, the
# bottom 30% a dip, the rest a dissolve
_r = np.random.default_rng(0); _a = EM[_r.integers(0, len(EM), 4000)]; _c = (_a[:2000] * _a[2000:]).sum(1)
CUT, DIP = float(np.percentile(_c, 85)), float(np.percentile(_c, 30)); print(f"likeness: cut above {CUT:.2f}, dip below {DIP:.2f}")
bv = lambda o: o["b"] if o.get("b") is not None else bright(o["id"])
plan = {}; stats = {"cut": 0, "dissolve": 0, "dip": 0, "speaker": 0, "story": 0}
for sid, tm in TR.items():
    sc = sea.get(sid); lines = found["scenes"].get(sid) or []
    if not sc: continue
    for mode, t in tm.items():
        # slots: stretches of the track with one picture
        slots = []
        for L in t["lines"]:
            u = lines[L["li"]]; sh = shot_of(sc, u); key = sh["id"] if sh else None
            evs = [e for e in t["ev"] if e["li"] == L["li"]]
            if slots and slots[-1]["kind"] == "story" and slots[-1]["key"] == key: slots[-1]["end"] = L["end"]
            else: slots.append({"kind": "story", "key": key, "opts": options(sh), "start": L["at"], "end": L["end"], "pause": L["at"] - (slots[-1]["end"] if slots else 0)})
            if mode == "spoken" and u["who"] != "Epic Narrator":           # (in call, the speakers stand beside the story instead)
                for e in evs:
                    s_ = SPK.get(f"{e.get('id')}@{e.get('t0')}")
                    if e.get("id") and s_ and s_.get("face", 0) >= .12 and s_["talk"] >= .9 and e["end"] - e["at"] >= 1.2:   # a real face, speaking
                        if slots[-1]["kind"] == "story": slots[-1]["end"] = e["at"]          # the story gives way to the speaker
                        slots.append({"kind": "speaker", "id": e["id"], "in": e["t0"], "video": lib[e["id"]]["video"], "start": e["at"], "end": e["end"], "pause": e["at"] - (e.get("gap") or e["at"] - .7), "b": s_["b"], "emb": s_.get("emb")})
                        slots.append({"kind": "story", "key": key, "opts": options(sh), "start": e["end"], "end": L["end"], "pause": 0})
        slots = [s for s in slots if s["end"] - s["start"] >= .3 or s["kind"] == "speaker"]
        # merge story slots too short to hold (under 3 s) into the one before
        merged = []
        for s in slots:
            if merged and s["kind"] == "story" and merged[-1]["kind"] == "story" and (s["key"] == merged[-1]["key"] or s["end"] - s["start"] < 3): merged[-1]["end"] = s["end"]
            else: merged.append(s)
        slots, merged = merged, []
        for k, s in enumerate(slots):                                   # a short story stretch after a speaker: the next picture comes in its place
            if s["kind"] == "story" and s["end"] - s["start"] < 3 and merged and merged[-1]["kind"] == "speaker":
                if k + 1 < len(slots): slots[k + 1]["start"], slots[k + 1]["pause"] = s["start"], max(slots[k + 1]["pause"], s["start"] - merged[-1]["end"] + .4)
                else: merged[-1]["end"] = s["end"]
                continue
            merged.append(s)
        slots = merged
        # Viterbi over the story pictures: the captain's choice against the join with the picture before
        node = []
        for s in slots:
            if s["kind"] == "speaker": node.append([{"id": s["id"], "in": s["in"], "video": s["video"], "cost": 0, "b": s["b"], "emb": s.get("emb")}])
            else:
                hold = s["end"] - s["start"] + 2
                ops = [dict(o, cost=o["cost"] + (.4 if dur_of(o["id"]) - o["in"] < hold * RATE * .6 else 0)) for o in s["opts"]] or [{"id": None, "cost": 1}]
                node.append(ops)
        def jc(a, b):
            if not a.get("id") or not b.get("id"): return .5, .5
            if a.get("emb") or b.get("emb"):
                ea = np.array(a["emb"]) if a.get("emb") else look(a["id"]); eb = np.array(b["emb"]) if b.get("emb") else look(b["id"])
                cos = float(ea @ eb) if ea is not None and eb is not None else .7
                return (1 - cos) + 1.5 * abs(a.get("b", bright(a["id"])) - b.get("b", bright(b["id"]))), cos
            return join(a, b)
        D = [[o["cost"] for o in node[0]]]; B = [[None] * len(node[0])]
        for k in range(1, len(node)):
            d, bk = [], []
            for o in node[k]:
                c = [D[-1][j] + .35 * jc(p, o)[0] for j, p in enumerate(node[k - 1])]; j = int(np.argmin(c)); d.append(c[j] + o["cost"]); bk.append(j)
            D.append(d); B.append(bk)
        j = int(np.argmin(D[-1])); pick = [None] * len(node)
        for k in range(len(node) - 1, -1, -1): pick[k] = node[k][j]; j = B[k][j] if B[k][j] is not None else 0
        # the joins: kind and timing, always inside a pause
        out = []
        for k, (s, o) in enumerate(zip(slots, pick)):
            if not o.get("id"): continue
            if out:
                _, cos = jc(pick[k - 1], o) if pick[k - 1].get("id") else (0, .5)
                db = abs(bv(pick[k - 1]) - bv(o))
                tr = "cut" if cos > CUT and db < .12 else "dissolve" if cos > DIP else "dip"
            else: tr = "dissolve"
            pause = max(.25, s["pause"]) if out else 2.0
            if s["kind"] == "speaker": sw, dd = s["start"] - min(.6, pause * .6), 400 if tr != "cut" else 0
            elif tr == "cut": sw, dd = s["start"] - min(.35, pause * .5), 0
            else: dd = int(1000 * min(2.0, max(.8, pause + .25))); sw = s["start"] + .25 - dd / 1000
            stats[tr] += 1 if out else 0; stats[s["kind"]] += 1
            out.append({"sw": round(sw, 2), "dd": dd, "tr": tr, "kind": s["kind"], "id": o["id"], "video": o.get("video") or lib[o["id"]]["video"],
                        "in": round(float(o["in"]) - (s["start"] - sw if s["kind"] == "speaker" else 0), 2), "rate": 1.0 if s["kind"] == "speaker" else RATE,
                        "hold": round(s["end"] - s["start"], 2), "dur": dur_of(o["id"]),
                        "alts": [{"id": a_["id"], "in": round(float(a_["in"]), 2), "video": a_["video"]} for a_ in s.get("opts", []) if a_["id"] != o["id"]][:3]})   # other takes, for the grid
        plan.setdefault(sid, {})[mode] = out
        if mode == "call":                                              # beside the story: the footage each answer comes from, in sync
            plan[sid]["call_beside"] = [{"sw": round(e["at"] - .35, 2), "end": round(e["end"] + .45, 2), "id": e["id"], "in": round(max(0, e["t0"] - .35), 2),
                                         "video": lib[e["id"]]["video"], "li": e["li"]} for e in t["ev"] if e.get("id") and e["id"] in lib and e["end"] - e["at"] >= .9]
json.dump(plan, open(os.path.join(H, "found-pics.json"), "w"), separators=(",", ":"))
n = sum(len(v) for s in plan.values() for v in s.values())
print(f"pictures {n} in {len(plan)} scenes · story {stats['story']} · speakers {stats['speaker']} · joins: cut {stats['cut']}, dissolve {stats['dissolve']}, dip {stats['dip']}")
holds = [p["hold"] for s in plan.values() for k, v in s.items() if k != "call_beside" for p in v]; print(f"hold per picture: median {np.median(holds):.1f} s, 10% {np.percentile(holds, 10):.1f} s")
