"""Everything the collage page offers for each WYGWYL beat → wygwyl/collage-data.json.

Per beat: the suite's own treatment (operation, gap, edit, mode, A/B), every graded candidate, the forage clips its
search recipes retrieved, and its Halfworld reference movement. Per chapter: moods, symbols, motifs, characters,
tone, and the movements with their reference frames placed on the suite clock. Cue lines carry the poem.
The four cuts' shots and the sign families are read by the page itself (cuts/*/patches.json, tools/cineosis-index.json).
    python3 wygwyl/build_collage_data.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
cat = json.load(open(os.path.join(HERE, "WYGWYL_Forage_Catalogue.json")))
CODE = {"34O": "34a", "34S": "34b"}
GRADE = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, "U": 9}

def clip(c, why=None):
    return {"id": c["id"], "title": c.get("title"), "year": c.get("year"), "thumb": c.get("thumb"), "video": c.get("video"),
            "url": c.get("url"), "dur": round((c.get("end") or 0) - (c.get("start") or 0), 2), "grade": c.get("grade") or "U",
            "observed": c.get("observed"), "use": c.get("use"), "query": c.get("query"), "why": why}

by_query = {}
for c in cat["catalogue"]:
    for q in set(c.get("queries") or [c.get("query")]):
        if q: by_query.setdefault(q, []).append(c)

frames = set(os.listdir(os.path.join(HERE, "Halfworld_Reference_Frames")))
worlds = []
for w in cat["worlds"]:
    win = w["window"]; tot = sum(m["seconds"] for m in w["movements"]) or 1; sc = (win[1] - win[0]) / tot
    mv = []
    for m in w["movements"]:
        img = f"{w['n']}-{m['index']}.png"
        mv.append({"index": m["index"], "label": m["label"], "line": m.get("line", ""), "t0": round(win[0] + m["start"] * sc, 3),
                   "t1": round(win[0] + (m["start"] + m["seconds"]) * sc, 3), "frame": f"wygwyl/Halfworld_Reference_Frames/{img}" if img in frames else None})
    worlds.append({k: w.get(k) for k in ("n", "title", "tagline", "window", "accent", "moods", "symbols", "motifs", "characters", "logline", "thesis", "tone", "referenceUrl")} | {"movements": mv})

beats = []
for b in cat["beats"]:
    cands = [clip(c, "candidate") for c in b.get("candidates", [])]
    seen = {c["id"] for c in cands}
    forage = []
    for q in b.get("searchRecipes") or [b.get("query")]:
        for c in by_query.get(q, []):
            if c["id"] not in seen: seen.add(c["id"]); forage.append(clip(c, "forage"))
    forage.sort(key=lambda c: GRADE.get(c["grade"], 9))
    codes = [CODE.get(str(c), str(c)) for c in b.get("codes", [])]
    beats.append({"id": b["id"], "chapter": cat["films"][b["chapter"]]["n"], "sequence": b.get("sequence"), "title": b.get("title"),
                  "start": round(b["start"], 3), "end": round(b["end"], 3), "mode": b.get("mode"), "codes": codes,
                  "operation": b.get("operation"), "gap": b.get("gap"), "edit": b.get("edit"), "items": b.get("items", []),
                  "query": b.get("query"), "recipes": b.get("searchRecipes", []), "selected": b.get("selected"), "partner": b.get("partner"),
                  "opacity": b.get("opacity"), "movement": b.get("referenceMovement"), "candidates": cands, "forage": forage[:60]})

LAB = os.path.dirname(HERE)
corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
remote = lambda i: corpus.get(i) or {}
cuts = {}
for slug in ("suite", "scenes", "cineosis", "drift"):
    P = json.load(open(os.path.join(HERE, "cuts", slug, "patches.json")))
    cuts[slug] = [{"t0": p["t0"], "t1": p["t1"], "id": p["clip"]["id"], "title": p["clip"]["title"], "year": p["clip"]["year"],
                   "thumb": remote(p["clip"]["id"]).get("thumbnailUrl"), "video": remote(p["clip"]["id"]).get("videoUrl"),
                   "in": p["clip"]["in"], "url": p["clip"]["page"], "why": p.get("why")} for p in P if p.get("clip")]
T = json.load(open(os.path.join(LAB, "tools", "cineosis-index.json")))
used = {c for b in beats for c in b["codes"]}
signs = {}
for sg in T["signs"]:
    fam = [{"id": f["id"], "title": f["title"], "year": f["year"], "thumb": remote(f["id"]).get("thumbnailUrl"), "video": remote(f["id"]).get("videoUrl"),
            "in": max(0, (f.get("read_t") or 0) - 1.5), "note": f.get("note"), "conf": f.get("conf")} for f in sg.get("family", [])]
    signs[str(sg["n"])] = {"symbol": sg["symbol"], "name": sg["name"], "dom": sg["dom"], "difference": sg.get("difference"), "family": fam if str(sg["n"]) in used else []}

out = {"title": cat["title"], "duration": cat["duration"], "audio": "wygwyl/WYGWYL_Suite_Audio.mp3",
       "films": [{k: f.get(k) for k in ("n", "title", "container", "poem")} for f in cat["films"]],
       "cues": [{"t0": round(c["start"], 3), "t1": round(c["start"] + c["duration"], 3), "text": c.get("text", ""), "screen": c.get("screen", "")} for c in cat["cues"]],
       "worlds": worlds, "beats": beats, "cuts": cuts, "signs": signs}
json.dump(out, open(os.path.join(HERE, "collage-data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
n = [len(b["candidates"]) + len(b["forage"]) for b in beats]
print(f"{len(beats)} beats · clips per beat min {min(n)} median {sorted(n)[len(n) // 2]} max {max(n)} · {os.path.getsize(os.path.join(HERE, 'collage-data.json')) // 1024} KB")
