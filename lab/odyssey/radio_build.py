"""The Markov Cool Radio Odyssey: each book a radio film. The scene's studio voice recording (odyssey-halfworld) is the clock;
the archival cut is laid along it; the book's own track from Bronze Council is the bed; the archive's own sound comes up where
the scene is sound-forward and in the gaps between lines, and stays down under speech. A stranger's layer (a prologue and cast per
book, a card per scene) makes it followable without knowing the Odyssey. A refrain (the book's home ground) opens the book, rings
between scenes and closes it, so each book reads as one poem.
Writes radio.json (published).   usage: python3 radio_build.py [path to odyssey-halfworld]"""
import glob, json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from align import align
H = os.path.dirname(os.path.abspath(__file__)); HW = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/odyssey-halfworld")
SITE = "https://hartswf0.github.io/odyssey-halfworld/"
url = lambda p: SITE + urllib.parse.quote(p)
cuts = json.load(open(os.path.join(H, "cuts.json")))["cuts"]; scenes = {s["id"]: s for s in json.load(open(os.path.join(H, "scenes.json")))["scenes"]}
grade = json.load(open(os.path.join(H, "grade.json"))) if os.path.exists(os.path.join(H, "grade.json")) else {}
audio = json.load(open(os.path.join(H, "cache", "audio.json"))) if os.path.exists(os.path.join(H, "cache", "audio.json")) else {}
voice = json.load(open(os.path.join(HW, "drive", "voice-manifest.json"))); script = {s["id"]: s for s in json.load(open(os.path.join(HW, "drive", "drive-script.json")))["scenes"]}
albums = json.load(open(os.path.join(HW, "audio", "albums.json")))["albums"]; bronze = next(a for a in albums if a["id"] == "bronze-council")
track = {t["num"]: url(bronze["dir"] + "/" + t["file"]) for t in bronze["tracks"]}; tname = {t["num"]: t["title"] for t in bronze["tracks"]}
direction = {s["id"]: s.get("direction") or {} for s in json.load(open(os.path.join(H, "src", "cineosis_score.json")))["scenes"] + json.load(open(os.path.join(H, "src", "cineosis_score.json")))["dropped"]}
ST = {"books": {}, "scenes": {}}
for f in glob.glob(os.path.join(H, "src", "stranger_*.json")):
    d = json.load(open(f)); ST["books"].update(d.get("books", {})); ST["scenes"].update(d.get("scenes", {}))
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
SPOKEN = {}
for f in glob.glob(os.path.join(HW, "atlas", "spoken-lines", "lines-*.json")):
    for k, x in json.load(open(f)).items():
        if (x.get("line") or "").strip(): SPOKEN[k] = x["line"].strip()
import re
def chunks(text, start, dur, most=110):
    """A long speech becomes phrases on screen, each held for its share of the recording by length, so the words keep pace with the voice."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?;:—])\s+", text) if p.strip()]
    out = []
    for p in parts:   # a sentence still too long is cut at commas
        if len(p) <= most: out.append(p); continue
        cur = ""
        for w in re.split(r"(?<=,)\s+", p):
            if cur and len(cur) + len(w) > most: out.append(cur); cur = w
            else: cur = (cur + " " + w).strip()
        if cur: out.append(cur)
    tot = sum(len(p) + 6 for p in out) or 1; t = start; res = []
    for p in out:
        d = dur * (len(p) + 6) / tot; res.append((round(t, 2), round(t + d, 2), p)); t += d
    return res
def clipgain(i, forward):
    """(gain under speech, gain in the clear): the archive's own sound, levelled to sit under the voice or carry the gap."""
    a = audio.get(i)
    if not a or not a.get("audio") or a.get("lufs") is None or a["lufs"] < -45: return 0, 0
    talky = a.get("band_db") is not None and a["band_db"] - a["lufs"] > -6            # most of its energy in the voice band: probably talk
    lift = lambda target: max(0, min(1, 10 ** ((target - a["lufs"]) / 20)))
    under = 0 if talky else lift(-36 if not forward else -27)
    clear = lift(-30 if talky else (-21 if forward else -25))
    return round(under, 2), round(clear, 2)
books = {}
for sid in sorted(cuts):
    sc = scenes.get(sid); cut = cuts[sid]; v = voice.get(sid); sp = script.get(sid)
    if not sc or not v or not sp: continue
    T = v["total"] + 1.2; dirn = direction.get(sid, {}); fwd = bool(dirn.get("sound_forward"))
    segs = sp["segments"]; subs = []
    for g in v["segments"]:
        s = segs[g["gi"]] if g["gi"] < len(segs) else None
        if not s or s["kind"] == "SPEAKER_CUE": continue
        # what was actually spoken: the recordings read the full line (atlas/spoken-lines) where the script often carries a summary;
        # take whichever text fits the length of the recording at a speaking pace
        cands = [s["text"]] + ([SPOKEN[s["sourceTurnId"]]] if SPOKEN.get(s.get("sourceTurnId") or "") else [])
        text = min(cands, key=lambda t: abs(len(t) / max(.4, g["dur"]) - 13.5))
        for c0, c1, piece in chunks(text, g["start"], g["dur"]): subs.append({"t0": c0, "t1": c1, "who": s["speakerName"], "kind": s["kind"], "text": piece})
    wf = os.path.join(H, "cache", "voice-words", sid + ".json")
    if os.path.exists(wf): subs = align(subs, json.load(open(wf)))       # on the words as spoken
    shots = [x for x in cut["shots"] if x["clip"] and x["clip"] in lib]
    if not shots: continue
    tot = sum(float(x["sec"] or 4) for x in shots); k = T / tot; t = 0.0; starts = [g["t0"] for g in subs]
    out = []
    for n, x in enumerate(shots):
        d = float(x["sec"] or 4) * k; t1 = t + d
        if n < len(shots) - 1:   # a cut lands on a line where one is near: the picture turns with the voice
            near = min(starts, key=lambda s: abs(s - t1), default=None)
            if near is not None and abs(near - t1) < 1.6 and near - t > 1.2: t1 = near
        else: t1 = T
        L = lib[x["clip"]]; u, c = clipgain(x["clip"], fwd)
        out.append({"t0": round(t, 2), "dur": round(t1 - t, 2), "id": x["clip"], "video": L["video"], "thumb": L["thumb"], "in": L.get("in", 0), "role": x["role"], "see": x["see"],
                    "under": u, "clear": c, "title": L.get("title"), "year": L.get("year")})
        t = t1
    g = grade.get(sid, {}); s_ = ST["scenes"].get(sid, {})
    b = books.setdefault(sc["book"], {"n": sc["book"], "title": sp.get("bookTitle"), "track": track.get(sc["book"]), "track_title": tname.get(sc["book"]), "scenes": []})
    b["scenes"].append({"id": sid, "title": sc["title"], "card": s_.get("card"), "who": s_.get("who", []), "voice": url(v["file"]), "total": round(T, 2), "subs": subs, "shots": out,
                        "sign": sc["sign"], "forward": fwd, "palette": cut["palette"], "world": cut["world"], "grade": g.get("grade"), "render": g.get("render"), "prompt": g.get("prompt")})
for n, b in books.items():
    sb = ST["books"].get(str(n), {}); b.update({"prologue": sb.get("prologue"), "cast": sb.get("cast", []), "carry": sb.get("carry")})
    # the refrain: the book's home ground, one EMPTY or WIDE shot from its most-used palette, best fit first
    pal = max(("bw", "colour", "either"), key=lambda p: sum(1 for s in b["scenes"] if s["palette"] == p))
    cand = [(x.get("fit", 0), x) for s in b["scenes"] for x in cuts[s["id"]]["shots"] if x["clip"] in lib and x["role"] in ("EMPTY", "WIDE") and cuts[s["id"]]["palette"] == pal]
    if cand:
        x = max(cand, key=lambda c: c[0])[1]; L = lib[x["clip"]]; b["refrain"] = {"id": x["clip"], "video": L["video"], "thumb": L["thumb"], "in": L.get("in", 0), "see": x["see"]}
json.dump({"site": SITE, "books": [books[k] for k in sorted(books)]}, open(os.path.join(H, "radio.json"), "w"), separators=(",", ":"))
print("books", len(books), "· scenes", sum(len(b["scenes"]) for b in books.values()), "· minutes", round(sum(s["total"] for b in books.values() for s in b["scenes"]) / 60, 1),
      "· shots with archive sound", sum(1 for b in books.values() for s in b["scenes"] for x in s["shots"] if x["clear"] > 0), "of", sum(len(s["shots"]) for b in books.values() for s in b["scenes"]),
      "· stranger cards", sum(1 for b in books.values() for s in b["scenes"] if s["card"]))
