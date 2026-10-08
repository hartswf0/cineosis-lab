"""The SLOPFEEDER studio plan: each VOLHOLLA song becomes a rough arc through the world. Each section of the song takes the part of the
world its sound and energy ask for (songs.json); each section is cut on the song's beats (two beats a shot where it is loudest, eight
where it is quiet); each shot gets an archival plate from that world's forage (forage.json) and offers the other layers a hybrid film
can use: a moving SAM cut-out from the archive (cuts.json), a tracked element from the source videos (src/tracks.json, local only),
a coded effect, and a prompt for an AI-video generator written in BEACHHEAD's continuity. Writes slopfeeder/studio.json.
usage: python3 slopfeeder/studio.py"""
import json, os, random
D = os.path.dirname(os.path.abspath(__file__))
WORLDS = {
 "THE LANDING": {"pools": ["the landing", "the guns", "the blast"], "cuts": ["the blast", "the guns", "the landing"], "track": None, "code": "shake + white flash on the downbeat",
   "prompt": "Handheld 16mm newsreel at dawn: a landing-craft ramp drops into grey surf; adults in dirty ivory pressure suits with faded orange shoulders charge past inverted orange bucket drills (closed bottoms up, open mouths down) toward a ruined brick fort, tracer fire overhead, water spray on the lens, no gore, 1944 grain, straight cut"},
 "THE FLEET": {"pools": ["the sea", "the guns", "the future"], "cuts": ["the sea", "the future"], "track": "login", "code": "laser beams from the horizon",
   "prompt": "Extreme wide from the beach: offshore, four colossal cartoon shapes (a purple rectangle, a black slab, an orange half-dome, a yellow arch) stand in the sea like warships, simple dot eyes tracking the crew on the sand; warships burn beneath them; heavy swell, overcast dawn, no one fires"},
 "THE RENDER": {"pools": ["the characters", "the future", "the screens"], "cuts": ["the characters", "the future"], "track": "login", "code": "scanlines + cursor",
   "prompt": "A login page the size of a cliff glows above the sea; its four cartoon characters lean and blink as a giant cursor drags across the sky; each click lands on the beach as a change request; flat colours against storm cloud"},
 "THE DRILL LINE": {"pools": ["the work", "the beach"], "cuts": ["the work"], "track": None, "code": "rope rhythm: cut on every beat",
   "prompt": "Low wide: a line of adults in ivory pressure suits pump rope-and-crossbar bucket drills along wet sand, orange pails mouths down, blue rope, bent shoulders on the downstroke, smoke drifting from the fort right, sea left"},
 "THE KITCHEN": {"pools": ["the kitchen", "the faces"], "cuts": ["the kitchen"], "track": "ghost", "code": "steam and grease particles",
   "prompt": "Medium: the skull-masked cook in black headset and apron turns real burgers and onions on a broad white-blue-red forearm griddle strapped to his left arm, steam in cold air, he lifts his head and stares into the lens without moving; crews eat behind him"},
 "THE SCREEN": {"pools": ["the screens", "the machines"], "cuts": ["the screens", "the machines"], "track": "ghost", "code": "terminal text: the change requests",
   "prompt": "Inside the fort: banks of 1960s mainframe consoles and oscilloscopes run on salvaged power; change requests type themselves on green screens ('could you move it slightly left?'); the cook watches the screens, unmoved"},
 "THE TIDE": {"pools": ["the sea", "the beach"], "cuts": ["the sea"], "track": None, "code": "slow drift",
   "prompt": "Sand level: a single cooked onion ring floats on a thin current through the drill holes toward a low brick drain, tide hissing in, the beach quiet after the shelling"},
 "THE AFTERMATH": {"pools": ["the beach", "the blast", "the faces"], "cuts": ["the blast"], "track": "ghost", "code": "slow drift",
   "prompt": "Smoke clears over a churned beach; orange pails stand mouth-down in rows like grave markers; the crew sits in the sand eating from steel plates; the tall Slopling holds the last beam over them"}}
S = json.load(open(os.path.join(D, "songs.json"))); F = json.load(open(os.path.join(D, "forage.json"))); C = [c for c in json.load(open(os.path.join(D, "cuts.json"))) if not c.get("none")] if os.path.exists(os.path.join(D, "cuts.json")) else []
TR = json.load(open(os.path.join(D, "src", "tracks.json"))) if os.path.exists(os.path.join(D, "src", "tracks.json")) else []
pool = {}
for c in F["clips"]:
    for w, _ in c["found"]: pool.setdefault(w, []).append(c)
def lit(c):   # a plate has to be a picture: not blown out to white, not black, not flat
    try:
        from PIL import Image, ImageStat
        st = ImageStat.Stat(Image.open(os.path.join(D, "fthumbs", c["id"] + ".jpg")).convert("L")); return 25 < st.mean[0] < 215 and st.stddev[0] > 22
    except Exception: return False
# each world's plates: chosen by CLIP across everything (pools.json); the landing and the fleet also take the forage's guns and blasts
PO = json.load(open(os.path.join(D, "pools.json")))["pools"]
EXTRA = {"THE LANDING": ["the guns", "the blast", "the landing"], "THE FLEET": ["the sea", "the guns"]}
for w in WORLDS:
    lst = list(PO[w]); ex = [c for q in EXTRA.get(w, []) for c in pool.get(q, [])[:60] if lit(c)]
    mixed, seen = [], set()
    for k in range(max(len(lst), len(ex))):
        for src in ((lst, ex) if k % 2 else (ex, lst)):
            if k < len(src) and src[k]["id"] not in seen: seen.add(src[k]["id"]); mixed.append(src[k])
    WORLDS[w]["plates"] = mixed
# a cut-out has to be a figure, not a box of sky: reject masks that fill their own bounding box, or are too small
from PIL import Image
def solid(c):
    try: a = (np.asarray(Image.open(os.path.join(D, c["still"])).split()[3]) > 128); return a.mean()
    except Exception: return 1
import numpy as np
C = [c for c in C if c.get("fit", 0) >= .22 and .12 < solid(c) < .82]
plans = []
PACE = {"THE LANDING": 3, "THE DRILL LINE": 4, "THE RENDER": 6, "THE SCREEN": 5, "THE FLEET": 8, "THE KITCHEN": 7, "THE AFTERMATH": 10, "THE TIDE": 12}   # half-beats a shot
def arc(song):
    """the shape of a D-Day opening laid over the song: the approach, the landing at its loudest, the line held (the kitchen) right after,
    the tide at the end; between, the screens and the render take its electronic and whispering stretches, the drill line its chant"""
    ss = song["sections"]; es = [x["energy"] for x in ss]; mx = max(es); peak = sorted(sorted([i for i, e in enumerate(es) if e >= .8 * mx and i > 0], key=lambda i: -es[i])[: max(1, len(ss) // 2 - 1)])
    for i, x in enumerate(ss):
        lead = x.get("lead", x["sound"][0])
        x["world"] = ("THE SCREEN" if lead in ("electronic synthesizer pulses", "tense suspense music") else "THE RENDER" if lead == "a creepy whispering voice"
                      else "THE KITCHEN" if lead in ("a sacred hymn", "a solo voice singing") else "THE DRILL LINE")
        if i in peak: x["world"] = "THE LANDING"
    if ss[0]["world"] != "THE LANDING": ss[0]["world"] = "THE FLEET"
    if peak and peak[-1] + 1 < len(ss) - 1: ss[peak[-1] + 1]["world"] = "THE KITCHEN"
    ss[-1]["world"] = "THE TIDE"
NEXT = {"THE KITCHEN": "THE SCREEN", "THE FLEET": "THE RENDER", "THE DRILL LINE": "THE KITCHEN", "THE LANDING": "THE AFTERMATH", "THE SCREEN": "THE DRILL LINE", "THE RENDER": "THE FLEET", "THE TIDE": "THE TIDE", "THE AFTERMATH": "THE TIDE"}
def split(song):   # no part of the world outstays its welcome: a section over 36 s hands its second half to the next part
    out = []
    for x in song["sections"]:
        if x["t1"] - x["t0"] > 36 and x["world"] != "THE LANDING":
            m = round((x["t0"] + x["t1"]) / 2, 2); out += [{**x, "t1": m}, {**x, "t0": m, "world": NEXT[x["world"]]}]
        else: out.append(x)
    song["sections"] = out
for song in S["songs"]:
    arc(song); split(song); half = 60 / song["tempo"] / 2 if song["tempo"] < 140 else 60 / song["tempo"]
    rnd = random.Random(int(song["n"])); used = set(); secs = []
    for sec in song["sections"]:
        W_ = WORLDS[sec["world"]]; e = sec["energy"]; per = PACE[sec["world"]] * (1.25 if e < .3 else .85 if e > .6 else 1)
        bs = [b for b in song["beats"] if sec["t0"] <= b < sec["t1"]]; grid = sorted(set(bs + [round((x + y) / 2, 2) for x, y in zip(bs, bs[1:])])) or [sec["t0"]]   # half-beats
        marks, acc = [sec["t0"]], 0.0
        for g in grid:                                    # cut on the grid, every `per` half-beats (alternating 1 and 2 at the landing)
            if g - marks[-1] >= per * half * .95: marks.append(g)
        marks = sorted(set(round(m, 2) for m in marks + [sec["t1"]]))
        plates = [c for c in W_["plates"] if c["id"] not in used and (c.get("dur") or 0) >= 1.5]
        shots = []
        for k, (a, b) in enumerate(zip(marks, marks[1:])):
            if b - a < .4: continue
            lst = [c for c in plates if c["id"] not in used]
            if not lst: continue
            top = lst[:6]; c = top[rnd.randrange(len(top))]; used.add(c["id"]); p = c.get("why") or (c.get("found") or [["", ""]])[0][1]
            alts = [x for x in lst if x["id"] != c["id"]][:3]
            cut = [x for x in C if x["world"] in W_["cuts"]]; layer = {}
            if cut and k % 4 == 3 and sec["world"] != "THE LANDING": layer["cutout"] = cut[(k // 3) % len(cut)]["id"]
            if W_["track"] and k % 4 == 1:
                names = [t["name"] for t in TR if t["name"].startswith(W_["track"])]
                if names: layer["track"] = names[(k // 4) % len(names)]
            shots.append({"t0": a, "dur": round(b - a, 2), "pool": p, "clip": {x: c.get(x) for x in ("id", "title", "year", "v", "t", "dur")}, "alts": [{x: y.get(x) for x in ("id", "title", "t", "v")} for y in alts], **layer})
        secs.append({**sec, "per": per, "code": W_["code"], "prompt": W_["prompt"], "shots": shots})
    plans.append({k: song[k] for k in ("n", "title", "note", "file", "dur", "tempo", "sound")} | {"sections": secs, "energy": song["energy"]})
    print(song["n"], song["title"], "·", sum(len(s["shots"]) for s in secs), "shots ·", " → ".join(f"{s['world'][4:]}" for s in secs))
json.dump({"worlds": {w: {k: v for k, v in x.items() if k != "plates"} for w, x in WORLDS.items()}, "songs": plans, "cuts": C, "tracks": [{k: t[k] for k in ("name", "desc", "size", "frames", "fps")} for t in TR]}, open(os.path.join(D, "studio.json"), "w"), ensure_ascii=False)
