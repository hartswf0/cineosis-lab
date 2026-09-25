"""Assemble lab/lab-data.json from the table data, the search corpus and whatever analysis exists.

Every analysis field is optional: re-run after each pipeline step (analyze.py, sam_cut.py,
strips.py, audio.py) and the lab picks it up. Contract: see DATA_CONTRACT.md.
"""
import glob, json, os

LAB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LAB)
SITE = "https://www.movingimagearchive.com"

def load(p, default):
    p = os.path.join(LAB, p)
    return json.load(open(p)) if os.path.exists(p) else default

COLS = [("Perception","0","perception",["1","2","3"]),("Affection","111","affect",["4","5","6"]),
        ("Impulse","211","action",["7","8","9"]),("Action · small","221","action",["10","11","12"]),
        ("Action · large","222","action",["13","14","15"]),("Attraction","311","reflection",["16","17","18"]),
        ("Inversion","321","reflection",["19","20","21"]),("Discourse","322","reflection",["22","23","24"]),
        ("Dream","331","mental",["25","26","27"]),("Recollection","332","mental",["28","29","30"]),
        ("Relation","333","mental",["31","32","33"]),("Opsign · Sonsign","0","break",["34a","34b"]),
        ("Hyalosign","1","time",["35","36","37"]),("Chronosign","2","time",["38","39","40"]),
        ("Noosign","3","time",["41","42","43"]),("Lectosign","∞","read",["44"])]

def main():
    table = json.load(open(os.path.join(ROOT, "cineosis-table.json")))["signs"]
    corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
    ana = load("cache/analysis.json", {})        # id -> palette/hue/lum/sat/subjects/scale/tsne/sim
    cuts = load("cache/cutouts_clean.json", None) or load("cache/cutouts.json", {})  # id -> [cutout], cleaned when available
    strips = load("cache/strips.json", {})       # id -> {"strip": path, "frames": n}
    audio = load("cache/audio.json", {})         # id -> {...}
    affinity = load("cache/affinity.json", {})   # id -> {"top": [[n, pct]...], "all": {n: pct}}
    segs = {}                                    # id -> tracked, directed SAM segments (merged from worker shards)
    for f in sorted(glob.glob(os.path.join(LAB, "cache", "segments*.json"))):
        segs.update(json.load(open(f)))
    read_t = load("cache/read_t.json", {})       # id -> {"t": s into clip} where the thumbnail (the frame read) sits
    found = {}                                   # id -> [{n, q, rank}]
    for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
        n = os.path.basename(f)[:-5]
        for q, cs in json.load(open(f)).items():
            for r, c in enumerate(cs):
                found.setdefault(c["id"], []).append({"n": n, "q": q, "rank": r})
    place = {}
    for ci, (img, code, dom, ns) in enumerate(COLS):
        for ri, n in enumerate(ns):
            place[n] = dict(col=ci, row=ri if dom != "read" else 0, image=img, code=code, dom=dom)
    signs, readings = [], {}
    for s in table:
        d = s.get("diff", {})
        signs.append({"n": s["n"], "symbol": s["symbol"], "name": s["name"], **place[s["n"]],
                      "gloss": s.get("gloss"), "difference": d.get("difference"), "ceiling": d.get("single_shot_ceiling"),
                      "confusions": [str(c["n"]) for c in d.get("confusions", [])], "question": s.get("question")})
        for e in s["examples"]:
            cid = e["page"].split("clip=")[1]
            readings.setdefault(cid, []).append({"n": s["n"], "note": e["note"], "conf": e.get("conf"), "shot": e.get("shot"),
                                                 "alt": e.get("alt"), "alt_conf": e.get("alt_conf"), "flip": e.get("flip")})
    wyg = {}                                    # id -> WYGWYL review + where the cut uses it
    wbeats, wfilms, wcut = [], [], None
    wd = os.path.join(LAB, "wygwyl")
    if os.path.exists(os.path.join(wd, "WYGWYL_Forage_Catalogue.json")):
        cat = json.load(open(os.path.join(wd, "WYGWYL_Forage_Catalogue.json")))
        cutj = json.load(open(os.path.join(wd, "WYGWYL_Forage_Cut.json")))
        chosen = {x["selected"]: x["id"] for x in cutj["shots"] if x.get("selected")}
        for c in cat["catalogue"]:
            wyg[c["id"]] = {"grade": c.get("grade"), "observed": c.get("observed"), "use": c.get("use"),
                            "queries": c.get("queries"), "beats": [], "chosen": None}
        for b in cat["beats"]:
            for c in b["candidates"]:
                w = wyg.setdefault(c["id"], {"grade": c.get("grade"), "observed": c.get("observed"), "use": c.get("use"),
                                             "queries": [c.get("query")], "beats": [], "chosen": None})
                if c.get("grade") and c.get("grade") != "U":        # a reviewed placement is more specific
                    w.update(grade=c.get("grade"), observed=c.get("observed"), use=c.get("use"))
                w["beats"].append(b["id"])
        for cid, bid in chosen.items():
            wyg.setdefault(cid, {"beats": []})["chosen"] = bid
        idx = json.load(open(os.path.join(LAB, "tools", "cineosis-index.json"))) if os.path.exists(os.path.join(LAB, "tools", "cineosis-index.json")) else {}
        wbeats = idx.get("wygwyl", {}).get("beats", [])
        wfilms = idx.get("wygwyl", {}).get("films", [])
        edl = os.path.join(wd, "wygwyl-cut.edl.json")
        wcut = {"title": cat.get("title"), "duration": cutj["duration"], "audio": "wygwyl/WYGWYL_Suite_Audio.mp3",
                "film": "wygwyl/wygwyl-cut.mp4" if os.path.exists(os.path.join(wd, "wygwyl-cut.mp4")) else None,
                "animatic_note": "The suite's own animatic is stills (its downloads 403'd); wygwyl-cut.mp4 is rendered from the archive footage.",
                "scope": cat.get("scope")}
    shots = []
    for cid, c in corpus.items():
        a = ana.get(cid, {})
        year = c.get("sourceYear")
        local_clip = os.path.join("clips", cid + ".mp4")
        shots.append({
            "id": cid, "title": c["sourceTitle"], "year": year, "decade": (year // 10 * 10) if year else None,
            "slug": c["sourceSlug"], "page": f"{SITE}/sources/{c['sourceSlug']}?clip={cid}",
            "video": c["videoUrl"], "clip": local_clip if os.path.exists(os.path.join(LAB, local_clip)) else None,
            "thumb": f"thumbs/{cid}.jpg" if os.path.exists(os.path.join(LAB, "thumbs", cid + ".jpg")) else c["thumbnailUrl"],
            "start": round(c["startSeconds"], 3), "end": round(c["endSeconds"], 3),
            "match": round(c.get("matchTimestampSeconds") or c["startSeconds"], 3),
            "read_t": read_t.get(cid, {}).get("t"),
            "bw": c.get("colorMode") == "black_and_white",
            "palette": a.get("palette"), "hue": a.get("hue"), "lum": a.get("lum"), "sat": a.get("sat"),
            "subjects": a.get("subjects"), "scale": a.get("scale"), "xy": a.get("xy"), "sim": a.get("sim"),
            "signs": readings.get(cid, []), "found": found.get(cid, []),
            "strip": strips.get(cid, {}).get("strip"), "frames": strips.get(cid, {}).get("frames"),
            "cutouts": cuts.get(cid, []), "audio": audio.get(cid),
            "affinity": affinity.get(cid, {}).get("all"), "aff_top": affinity.get(cid, {}).get("top"),
            "segments": segs.get(cid),
            "collections": c.get("collections", ["cineosis"]), "wygwyl": wyg.get(cid),
        })
    shots.sort(key=lambda s: (not s["signs"], s["sim"] if s["sim"] is not None else 1e9))
    out = {"signs": signs, "shots": shots, "assignments": load("assignments.json", []),
           "wygwyl": {"cut": wcut, "films": wfilms, "beats": wbeats} if wcut else None}
    tmp = os.path.join(LAB, "lab-data.json.tmp")         # atomic: readers never see a half-written file
    json.dump(out, open(tmp, "w"), ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(LAB, "lab-data.json"))
    print(len(signs), "signs;", len(shots), "shots;", sum(1 for s in shots if s["signs"]), "read;",
          sum(1 for s in shots if s["palette"]), "analysed;", sum(1 for s in shots if s["cutouts"]), "cut out")

if __name__ == "__main__":
    main()
