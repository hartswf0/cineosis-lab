"""THE MYTH, as a film about the film. The scenes myth/build.py chose (what each archive film was made for, what the lab made
of it) laid out as shots in a fixed 16:9 frame, so the footage is seen, not talked over:
  card    an act's title, its D-A-E cue fading in
  full    one archive clip, full frame, its own sound; the facts (year, maker, title) in a small caption, the narrator says
          only what the film was for, then the film's people speak
  long    the same film running on in its own clips, its own sound, no narration
  split   MADE FOR | MADE INTO: on the left the clip inside its source film (the shots around it), on the right the same clip
          inside our film (the shots our film put around it), both running, with what our film made it stand for
  mosaic  many clips at once: every place a recurring film turns up, or every shot of this film
  ui      the lab's own interface on screen (the fourth wall), a clip inset in it, the lab's voice speaking
Narrators: the lab (am_fenrir, the fourth wall), the history (bm_george), the myth (am_michael). The score: one D-A-E cue an act.
Writes myth/film.json; --voice renders myth/narr2/.   usage: python3 lab/myth/film.py   then   lab/republic/.tts/bin/python lab/myth/film.py --voice"""
import json, os, re, sys, collections, subprocess, time
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
J = lambda p: json.load(open(os.path.join(L, p)))
LAB, HIST, MYTH = "am_fenrir", "bm_george", "am_michael"

if "--voice" in sys.argv:
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    F = J("myth/film.json"); P = {}; ver = time.strftime("%Y%m%d%H%M"); os.makedirs(os.path.join(H, "narr2"), exist_ok=True)
    for n, b in enumerate(F["beats"]):
        if not b.get("line"): continue
        vo = b["voice"]; p = P.setdefault(vo[0], KPipeline(lang_code=vo[0], repo_id="hexgrad/Kokoro-82M"))
        a = np.concatenate([np.asarray(x, np.float32) for _, _, x in p(b["line"], voice=vo, speed=.9)])
        wav = os.path.join(H, "narr2", f"{n:03d}.wav"); sf.write(wav, np.concatenate([a, np.zeros(int(24000 * .3), np.float32)]), 24000)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "112k", wav[:-3] + "m4a"]); os.unlink(wav)
        b["a"] = f"myth/narr2/{n:03d}.m4a?v={ver}"; b["ad"] = round(len(a) / 24000 + .3, 2)
    json.dump(F, open(os.path.join(H, "film.json"), "w"), ensure_ascii=False, separators=(",", ":")); print("voiced"); sys.exit()

C = J("rushes/clips.json"); K = J("rushes/keys.json")["keys"]; UT = J("rushes/utts.json")["utts"]; PRE = C["pre"]
full = lambda v: v if v.startswith("http") else PRE + v
PUR = J("research/purpose.json"); M = J("myth/myth.json")["reel"]; uses = J("census/uses.json")
slug_of = {}
for f in ("markov/library.json", "odyssey/library.json"):
    for s in J(f)["shots"]:
        if s.get("src"): slug_of.setdefault(s["id"], s["src"])
for s in J("lab-data.json")["shots"]: slug_of.setdefault(s["id"], s.get("slug"))
row = {k: i for i, k in enumerate(K)}
prev = {}
for i, r in enumerate(C["rows"]):
    if r[6] >= 0: prev[r[6]] = i
FILMNAME = {"Found Odyssey": "our Odyssey", "Markov Odyssey": "our Odyssey", "Norse Half Moon": "Norse Half Moon", "The Republic": "the Republic", "Found Republic": "the Republic", "WYGWYL": "Where You Go When You Leave"}
UI = {"Found Odyssey": "odyssey", "Markov Odyssey": "odyssey", "Norse Half Moon": "norse", "The Republic": "republic", "Found Republic": "republic", "WYGWYL": "wygwyl"}
seqs = collections.defaultdict(dict)
for u in uses:
    if u["role"] == "picture" and u.get("seq"): seqs[u["film"]][u["seq"]] = u
def tile(v, t=0, d=None, label="", sound=False): return {"v": full(v), "in": round(t, 2), **({"d": d} if d else {}), "label": label, "sound": sound}
def rowtile(i, label="", sound=False): r = C["rows"][i]; return tile(r[0], 0, r[3], label, sound)
def speech(i):
    r = C["rows"][i]; return [UT[r[7]][1], UT[r[7]][2]] if r[7] >= 0 else None
def our_use(s, clipids):
    """where our films put this film's footage, and what they asked of it: the clearest use, its film, and the shots around it"""
    best = None
    rank = {"WYGWYL": 0, "The Republic": 1, "Markov Odyssey": 1, "Found Odyssey": 2, "Norse Half Moon": 2, "Found Republic": 3}
    for u in uses:
        if u["role"] != "picture" or not u.get("job") or slug_of.get(u.get("clip")) != s or not u.get("seq"): continue
        j = u["job"]
        if u["film"] == "Found Odyssey":
            if len(j.split()) < 7: continue
            say = f"In our Odyssey, it carried Homer's line: {j.rstrip('.;,—- ')}."
        elif u["film"] == "Markov Odyssey":
            br = re.sub(r"^\w+:\s*", "", j)
            if len(br.split()) < 4: continue
            say = f"In our Odyssey, it was cast as {br.rstrip('.')}."
        elif u["film"] == "The Republic":
            q, _, narr = j.partition(" | ")
            say = f"In the Republic, it set the scene: {narr.split('.')[0]}." if q.startswith("establishing") else f"In the Republic, it stood for {q.rstrip('.')}."
        elif u["film"] == "Found Republic":
            t = re.sub(r"^(act|line|card|title):\s*", "", j); t = re.sub(r"^[A-Z .\-']+ says: ", "", t)
            if len(t.split()) < 5: continue
            say = f"In the Republic, it carried this: {t.rstrip('.')}."
        elif u["film"] == "WYGWYL": say = f"In Where You Go When You Leave, it played this: {j.split(': ', 1)[-1].rstrip('.')}."
        elif u["film"] == "Norse Half Moon":
            if len(j.split()) < 5: continue
            say = f"In Norse Half Moon, it answered this: {j.rstrip('.')}."
        else: continue
        if len(say.split()) > 30: continue
        k = (rank[u["film"]], -len(say))
        if best is None or k < best[0]: best = (k, u, say)
    if not best: return None
    _, u, say = best; sq = seqs[u["film"]]
    around = [sq.get(u["seq"] + d) for d in (-1, 0, 1)]
    return {"film": u["film"], "say": say, "seq": [tile(x["video"], 0, 3.5, FILMNAME[x["film"]]) for x in around if x], "live": live_for(u)}
MUS = [sc["id"] for sc in J("odyssey/museum.json")["scenes"]]; NOR = [sc["id"] for sc in J("norse/program.json")["scenes"]]
ARC = list(J("republic/archive.json"))
def rep_time(n, video):
    """when a narration picture appears in a rendered Republic episode, roughly: the beats before it, by their lengths"""
    f = os.path.join(L, f"republic/pilot/ep{n:02d}.picked.json")
    if not os.path.exists(f): return 0
    t = 0
    for b in json.load(open(f))["beats"]:
        if b["k"] == "narr" and any(x.get("v") == video for x in b.get("shots", [])): return int(t)
        t += {"title": 4, "intro": 6, "end": 4}.get(b["k"], (b.get("d") or 2) + (1 if b["k"] == "chorus" else .4))
    return 0
PLAY = [{"wait": 1500}, {"mute": 1}, {"click": "#play"}, {"wait": 1500}, {"click": "#play"}]   # muted first: an embedded page may only autoplay silently
def live_for(u):
    f, w = u["film"], u.get("where") or ""
    if f in ("Found Odyssey", "Markov Odyssey") and w in MUS: return {"page": f"found-odyssey-museum.html?scene={MUS.index(w) + 1}", "steps": PLAY}
    if f == "The Republic" and w.startswith("EP"): n = int(w[2:]); return {"page": f"markov-republic.html#ep={n}&t={rep_time(n, u['video'])}", "steps": PLAY}
    if f == "Found Republic" and w in ARC: return {"page": f"markov-republic.html#ep={ARC.index(w) + 1}", "steps": PLAY}
    if f == "Norse Half Moon" and w in NOR: return {"page": f"norse-half-moon.html?scene={NOR.index(w) + 1}", "steps": PLAY}
    return None
def short_purpose(p):
    t = p.get("purpose") or ""
    t = re.sub(r"^This (\d{4} )?((?:[\w.\-]+ ){0,4})(film|documentary|newsreel|short|video|cartoon)\s+(\w+)\b", lambda m: "It " + m.group(4), t)
    t = re.sub(r"\s*\bon \d{1,2}/\d{1,2}/\d{2,4}\b|\s*\d{1,2}/\d{1,2}/\d{2,4}\b", "", t).replace("interveiwed", "interviewed")
    w = t.split()
    if len(w) > 18:
        cut = max((i for i, x in enumerate(w[:18]) if x.endswith((",", ";", ":"))), default=17); t = " ".join(w[:cut + 1]).rstrip(",;:")
    return t.rstrip(".") + "." if t else ""
def maker(p):
    sp = p.get("sponsor")
    if sp: return sp
    return {"government": "United States government", "corporation": "a company", "studio": "a film studio", "people": "a townsperson"}.get(p.get("kind"), "maker unknown")
def spoken_title(t):
    t = re.sub(r"\s*\((Part|Reel) [IVX\d]+\)", "", t or ""); t = re.sub(r"\s*\d{1,2}/\d{1,2}/\d{2,4}\b", "", t); t = re.sub(r"^.*? Presents:?\s*", "", t)
    return re.split(r"\s+:\s+", t)[0].strip()

CUES = {0: ("score/cues/dae-paddle-meets-current.m4a", "Paddle Meets Current"), 1: ("score/cues/dae-odin-above-the-breakers.m4a", "Odin Above the Breakers"),
        2: ("score/cues/dae-rusty-carnivals-barnacled-porch-stride.m4a", "Rusty Carnivals & Barnacled Porch Stride"), 3: ("score/cues/dae-jerry-s-mutron-solar-wind-boogie.m4a", "Jerry's Mutron & Solar Wind Boogie"),
        4: ("score/cues/dae-preparation-drift.m4a", "Preparation & Drift"), 5: ("score/cues/dae-slide-carousel-at-blue-hour.m4a", "Slide Carousel at Blue Hour"),
        6: ("score/cues/dae-snowbound-umea-cabin.m4a", "Snowbound Umeå Cabin"), 7: ("score/cues/dae-conquerors-of-the-useless.m4a", "Conquerors of the Useless")}
beats = []
FRESH = ["None of our films has used it. Until now.", "We never used this one.", "No film of ours has touched it.", "This one waited in the archive. We had left it alone.",
         "It has never been in any of our films.", "Nobody in the lab had picked it up. Until now."]
def B(**k): beats.append(k); return k

# ---- the scenes myth/build.py chose, read back from its reel
acts, a = [], None
for it in M:
    if it.get("card", "").startswith("THE MYTH"): break
    if it.get("card"): a = {"card": it["card"], "opener": it["line"].split(". ")[0] + ".", "scenes": []}; acts.append(a)
    if it.get("voice") == HIST: a["scenes"].append({"r": it["r"], "answer": None})
    elif it["k"] == "u" and a["scenes"]: a["scenes"][-1]["answer"] = it["u"]

# ---- PROLOGUE: the lab, on its own screens
photo = [u for u in uses if u["title"] == "THE PHOTOGRAPHER" and u["role"] == "picture"]
seen, ptiles = set(), []
for u in photo:
    if u["clip"] in seen: continue
    seen.add(u["clip"]); ptiles.append(tile(u["video"], 0, None, FILMNAME[u["film"]]))
    if len(ptiles) == 9: break
B(lay="card", act=0, card="THE MYTH", sub="a film about the films of Cineosis Lab", hold=4)
B(lay="live", act=0, page="../index.html", steps=[{"wait": 1500}, {"scroll": 500}], line="This is Cineosis Lab.", voice=LAB, hold=6, cap="CINEOSIS LAB")
B(lay="live", act=0, page="index.html", steps=[{"wait": 2500}, {"mute": 1}], line="It keeps twenty-eight thousand clips, cut from fifteen hundred films that were made to explain the world to somebody.", voice=LAB, hold=9, cap="CINEOSIS LAB · THE EXPLORER")
B(lay="live4", act=0, pages=[{"page": "found-odyssey-museum.html?scene=3", "steps": PLAY}, {"page": "markov-republic.html#ep=1&t=20", "steps": PLAY},
                             {"page": "norse-half-moon.html?scene=2", "steps": PLAY}, {"page": "wygwyl-collage.html", "steps": [{"wait": 1500}, {"mute": 1}]}],
  line="Out of them we made an Odyssey, a Republic on Mars, a house on the Norse coast, and a poem about leaving.", voice=LAB, hold=11, cap="OUR FILMS · RUNNING")
B(lay="live", act=0, page="recurring-cast.html", steps=[{"wait": 2500}, {"find": "THE PHOTOGRAPHER"}, {"mute": 1}], line="A machine chose most of the pictures. It looked for whatever matched our words. Then we counted what it chose.", voice=LAB, hold=9, cap="CINEOSIS LAB · THE RECURRING CAST")
B(lay="mosaic", act=0, tiles=ptiles, cap="THE PHOTOGRAPHER · 1948 · in five of our films",
  line="Some footage we used again and again. These shots come from one film, made in 1948. They turn up in five of ours.", voice=LAB, hold=9)
B(lay="card", act=0, card="What were they made for?", sub="and what did we make them into?", line="This is a film about what those pictures were made for, and what we made them into.", voice=LAB, hold=5)

# ---- THE ACTS
def tool_beat(ai, r0, s):
    said = UT[C["rows"][r0][7]][3] if C["rows"][r0][7] >= 0 else ""
    word = next((w for w in re.findall(r"[a-z]{5,}", said.lower()) if w not in ("there", "their", "these", "which", "would", "about", "where")), "future")
    title = (PUR.get(s) or {}).get("title") or C["rows"][r0][1]
    T = [("rushes.html#c=%d" % r0, [{"wait": 2000}, {"mute": 1}, {"wait": 4500}, {"click": '[data-w="ans"]'}, {"wait": 5000}, {"click": '[data-w="echo"]'}], "This is how we found it. In a page called Rushes, every clip offers four ways on: keep watching, an answer, an echo, somewhere else."),
         ("markov-transcripts.html?q=" + word, [{"wait": 2500}, {"mute": 1}], f"We searched sixty thousand things people said on film. This is everyone who said the word {word}."),
         ("../periodic-table.html", [{"wait": 2000}, {"scroll": 300}], "We read the shots against forty-four signs from a book about cinema."),
         ("recurring-cast.html", [{"wait": 2500}, {"find": title[:28]}, {"mute": 1}], "We counted which films came back, and how often."),
         ("ludens/tennis.html?world=odyssey", [{"wait": 2500}, {"mute": 1}], "We played games with them. In this one, every rally is a cut."),
         ("sound-cineosis.html", [{"wait": 2500}, {"mute": 1}], "And we listened to what they sound like, not only what they show.")]
    pg, st, ln = T[(ai - 1) % len(T)]
    return dict(lay="live", act=ai, page=pg, steps=st, line=ln, voice=LAB, hold=15 if pg.startswith("rushes") else 11, cap="CINEOSIS LAB · " + pg.split("?")[0].split("#")[0].replace(".html", "").replace("../", "").upper())
for ai, act in enumerate(acts, start=1):
    B(lay="card", act=ai, card=act["card"], line=act["opener"], voice=HIST, hold=4)
    first = act["scenes"][0]["r"]; B(**tool_beat(ai, first, slug_of.get(K[first])))
    for sc in act["scenes"]:
        r0 = sc["r"]; k = K[r0]; s = slug_of.get(k); p = PUR.get(s, {}); y = p.get("year")
        cap = " · ".join(x for x in (str(y) if y else "", maker(p), spoken_title(p.get("title") or C["rows"][r0][1])) if x)
        sp = speech(r0)
        B(lay="full", act=ai, tiles=[rowtile(r0, sound=True)], cap=cap, line=short_purpose(p), voice=HIST, speak=sp, hold=7)
        # the film runs on, in its own clips and its own sound
        run, i, t = [], C["rows"][r0][6], 0
        while i >= 0 and len(run) < 3 and t < 22:
            run.append(i); t += C["rows"][i][3] or 6; i = C["rows"][i][6]
        if run: B(lay="long", act=ai, tiles=[rowtile(x, sound=True) for x in run], cap=cap + " · running on", hold=min(24, max(8, t)))
        ou = our_use(s, None)
        ctx = [x for x in (prev.get(r0), r0, C["rows"][r0][6]) if x is not None and x >= 0]
        left = [rowtile(x, f"MADE FOR · {y or ''} · {maker(p)}".strip(" ·")) for x in ctx]
        if ou:
            B(lay="split", act=ai, left=left, right=ou["seq"], live=ou["live"], lcap=f"MADE FOR · {y or ''} · {maker(p)}", rcap=f"MADE INTO · {FILMNAME[ou['film']].upper()}",
              line=ou["say"], voice=MYTH, hold=10 if ou["live"] else 8)
        else:
            B(lay="split", act=ai, left=left, right=None, ui="myth/ui/rushes.jpg", lcap=f"MADE FOR · {y or ''} · {maker(p)}", rcap="MADE INTO · NOTHING YET",
              line=FRESH[ai % len(FRESH)], voice=MYTH, hold=7)
        if sc["answer"] is not None:
            u = UT[sc["answer"]]; ar = C["rows"][u[4]]
            B(lay="full", act=ai, tiles=[tile(u[0], max(0, u[1] - 1.6), None, "", True)], cap=f"{ar[2] or ''} · {spoken_title(ar[1])} · answers".strip(" ·"), speak=[u[1], u[2]], answer=True, hold=5)

# ---- EPILOGUE: the fourth wall
alltiles, seen = [], set()
for b in beats:
    for t in (b.get("tiles") or [])[:1]:
        if t["v"] not in seen and len(alltiles) < 16: seen.add(t["v"]); alltiles.append({**t, "label": "", "sound": False, "in": t["in"]})
B(lay="card", act=7, card="THE MYTH", sub="", hold=3)
B(lay="live", act=7, page="rushes.html#myth", steps=[{"wait": 2500}], line="This film is also a reel in Rushes. Here it is, every shot of it, waiting to be cut.", voice=LAB, hold=8, cap="CINEOSIS LAB · RUSHES")
B(lay="mosaic", act=7, tiles=alltiles, line="Every picture in it can be kept, cut, or answered by another.", voice=LAB, hold=7)
B(lay="live", act=7, page="../periodic-table.html", steps=[{"wait": 2000}, {"scroll": 600}], line="The words you heard were written by a script, from library records. The voices reading them are synthetic. The people in the films are not.", voice=LAB, hold=8)
B(lay="mosaic", act=7, tiles=alltiles[:9], line="These films were made to explain the future. We made them play gods, settlers and ghosts.", voice=MYTH, hold=7)
B(lay="card", act=7, card="Now take it apart.", sub="open this film in Rushes", link="rushes.html#myth", line="The people in them are still talking. Now take this film apart.", voice=LAB, hold=8)
# a line already voiced keeps its voice: only new or changed lines need --voice
try:
    was = {(b["voice"], b["line"]): (b["a"], b["ad"]) for b in J("myth/film.json")["beats"] if b.get("a")}
except Exception: was = {}
for b in beats:
    if b.get("line") and (b["voice"], b["line"]) in was: b["a"], b["ad"] = was[(b["voice"], b["line"])]
json.dump({"title": "THE MYTH", "cues": {str(k): v for k, v in CUES.items()}, "beats": beats}, open(os.path.join(H, "film.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(sum(1 for b in beats if b.get("line") and not b.get("a")), "lines still to voice")
print(len(beats), "beats ·", sum(1 for b in beats if b.get("line")), "lines ·", collections.Counter(b["lay"] for b in beats))
