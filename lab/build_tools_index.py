"""Compact data for the editors (CUT, the WAG Cutting Room): lab/tools/cineosis-index.json.

signs     the 45 elements with table position, deciding test, confusions, ceiling, family (read shots, best first)
wygwyl    the WYGWYL Forage cut as editable beats: chapter, title, sign codes, composition, times, chosen clip,
          counter-image (partner beat's clip), editorial note, operation, gap — plus the 14 films' windows
Media paths are relative to lab/ ("clips/<id>.mp4", "thumbs/<id>.jpg"); the bridge turns them into /media/ URLs.
"""
import json, os

LAB = os.path.dirname(os.path.abspath(__file__))

def main():
    data = json.load(open(os.path.join(LAB, "lab-data.json")))
    shots = {s["id"]: s for s in data["shots"]}
    fam = {}
    for s in data["shots"]:
        for r in s["signs"]:
            dur = round(s["end"] - s["start"], 2)
            fam.setdefault(r["n"], []).append({
                "id": s["id"], "title": s["title"], "year": s["year"], "thumb": s["thumb"], "clip": s["clip"],
                "dur": dur, "read_t": s.get("read_t"), "note": r["note"], "conf": r.get("conf"), "shot": r.get("shot"),
                "alt": r.get("alt"), "alt_conf": r.get("alt_conf"), "flip": r.get("flip")})
    signs = []
    for g in data["signs"]:
        signs.append({k: g.get(k) for k in ("n", "symbol", "name", "col", "row", "image", "code", "dom", "gloss",
                                            "difference", "ceiling", "confusions", "question")}
                     | {"family": sorted(fam.get(g["n"], []), key=lambda e: -(e["conf"] or 0))})
    out = {"signs": signs}
    wd = os.path.join(LAB, "wygwyl")
    if os.path.exists(os.path.join(wd, "WYGWYL_Forage_Cut.json")):
        cut = json.load(open(os.path.join(wd, "WYGWYL_Forage_Cut.json")))
        cat = json.load(open(os.path.join(wd, "WYGWYL_Forage_Catalogue.json")))
        clips = {c["id"]: c for c in cat["catalogue"]}
        for b in cat["beats"]:
            for c in b["candidates"]:
                clips.setdefault(c["id"], c)
        beats = {b["id"]: b for b in cat["beats"]}
        cuts = {s["id"]: s for s in cut["shots"]}
        def clip_ref(cid):
            c = clips.get(cid)
            if not c:
                return None
            return {"id": cid, "title": c["title"], "year": c.get("year"), "dur": round(c["end"] - c["start"], 2),
                    "thumb": f"thumbs/{cid}.jpg", "clip": f"clips/{cid}.mp4" if os.path.exists(os.path.join(LAB, "clips", cid + ".mp4")) else None,
                    "observed": c.get("observed"), "grade": c.get("grade")}
        wb = []
        for sid in sorted(cuts):
            s, b = cuts[sid], beats.get(sid, {})
            wb.append({"id": sid, "chapter": b.get("chapter"), "sequence": b.get("sequence"), "title": b.get("title"),
                       "codes": [{"34O": "34a", "34S": "34b"}.get(str(c), str(c)) for c in b.get("codes", [])],   # WYGWYL: 34O/34S = 34a/34b
                       "mode": s["mode"], "start": round(s["start"], 3), "end": round(s["end"], 3),
                       "trim": s.get("trim", 0), "rate": s.get("rate", 1), "opacity": s.get("opacity"),
                       "a": clip_ref(s["selected"]), "partner": s.get("partner"),
                       "b": clip_ref(cuts.get(s.get("partner"), {}).get("selected")) if s.get("partner") in cuts else None,
                       "edit": s.get("edit"), "operation": b.get("operation"), "gap": b.get("gap"), "query": b.get("query")})
        out["wygwyl"] = {"title": cat.get("title"), "duration": cut["duration"], "audio": "wygwyl/WYGWYL_Suite_Audio.mp3",
                         "films": [{k: f.get(k) for k in ("n", "title", "slug", "container", "poem")} for f in cat["films"]],
                         "beats": wb}
    os.makedirs(os.path.join(LAB, "tools"), exist_ok=True)
    json.dump(out, open(os.path.join(LAB, "tools", "cineosis-index.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print(len(signs), "signs;", sum(len(s["family"]) for s in signs), "family shots;",
          len(out.get("wygwyl", {}).get("beats", [])), "wygwyl beats")

if __name__ == "__main__":
    main()
