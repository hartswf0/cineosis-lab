"""Build reels.json for ABC FLIX: the footage it can rip, sorted into its four probability tracks.

    python3 lab/abc-flix/build_reels.py

Reads lab/lab-data.json (read shots and their readings) and lab/wygwyl/collage-data.json (beats, candidates, cuts).
Tracks, weakest to strongest evidence:
  0 POSSIBLE   unreviewed forage / a reading under 40
  1 PLAUSIBLE  another cut's pick / a reading of 40-54
  2 PROBABLE   a reviewed candidate (graded F or P) / a reading of 55-69
  3 PREFERRED  the shot the beat's review chose, or the suite cut's pick / a reading of 70 and over
"""
import json, os

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(LAB, "abc-flix", "reels.json")
PER_TIER = 6
CDN = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/"   # stored once; the page adds it back


def shot(c, t_in=0.0, **extra):
    """video is kept without the CDN prefix; the thumbnail sits beside it (clips/X.mp4 -> thumbnails/X.jpg)."""
    v = c.get("video") or ""
    return {"id": c["id"], "title": (c.get("title") or "")[:80], "year": c.get("year"),
            "v": v[len(CDN):] if v.startswith(CDN) else v, "in": round(max(0.0, t_in or 0.0), 2), **extra}


def tiers_from(ranked):
    """ranked: list of (tier, shot); keep each shot once at its strongest tier."""
    best = {}
    for tier, s in ranked:
        if s["id"] not in best or best[s["id"]][0] < tier:
            best[s["id"]] = (tier, s)
    out = [[], [], [], []]
    for tier, s in best.values():
        if len(out[tier]) < PER_TIER:
            out[tier].append(s)
    return out


def main():
    ld = json.load(open(os.path.join(LAB, "lab-data.json")))
    local = sorted(s["id"] for s in ld["shots"] if s.get("clip"))
    read = [s for s in ld["shots"] if s.get("clip") and s.get("signs")]

    signs = []
    for g in ld["signs"]:
        ranked = []
        for s in read:
            for r in s["signs"]:
                if r["n"] != g["n"]:
                    continue
                conf = r.get("conf") or 0
                tier = 3 if conf >= 70 else 2 if conf >= 55 else 1 if conf >= 40 else 0
                ranked.append((tier, shot(s, (s.get("read_t") or 0) - 0.5, conf=conf, note=(r.get("note") or "")[:140])))
        tiers = tiers_from(ranked)
        for t in tiers:
            t.sort(key=lambda x: -x["conf"])
        if any(tiers):
            signs.append({"n": g["n"], "symbol": g["symbol"], "name": g["name"], "dom": g["dom"], "tiers": tiers})

    cd = json.load(open(os.path.join(LAB, "wygwyl", "collage-data.json")))
    beats = []
    for b in cd["beats"]:
        ranked = []
        for cut, patches in cd["cuts"].items():
            for p in patches:
                if p["t1"] > b["start"] and p["t0"] < b["end"]:
                    ranked.append((3 if cut == "suite" else 1, shot(p, p.get("in", 0) + max(0, b["start"] - p["t0"]), why=cut + " cut")))
        for c in b.get("candidates", []):
            g = c.get("grade") or "U"
            tier = 3 if c["id"] == b.get("selected") else 2 if g in ("F", "P") else 0
            ranked.append((tier, shot(c, 0, why="review chose it" if tier == 3 else "reviewed " + g if tier == 2 else "unreviewed candidate")))
        for c in b.get("forage", []):
            ranked.append((0, shot(c, 0, why="forage")))
        beats.append({"id": b["id"], "film": b["chapter"], "title": b["title"], "start": b["start"], "end": b["end"],
                      "mode": b.get("mode"), "tiers": tiers_from(ranked)})

    films = [{"n": f["n"], "title": f["title"]} for f in cd["films"]]
    json.dump({"cdn": CDN, "local": local, "films": films, "beats": beats, "signs": signs}, open(OUT, "w"), separators=(",", ":"))
    print(f"{OUT}: {len(local)} local clips, {len(beats)} beats, {len(signs)} signs, {os.path.getsize(OUT) // 1024} KB")


if __name__ == "__main__":
    main()
