"""The shape of every picture in the repo. For each clip: the frame (the video's own proportions, from its thumbnail) and the
picture inside it, found by measuring the black bars a transfer adds (letterbox: a wide film in a squarer frame; pillarbox: a
square film in a wide frame; windowbox: both). A film's shape is agreed across its clips (one dark shot cannot invent a bar).
The measured shape is named by the nearest standard of cinema history, if one is near.
Writes aspect/aspect.json (sources, clips).   usage: python3 measure.py"""
import json, os, statistics as st, concurrent.futures as cf
import numpy as np
from PIL import Image
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDARDS = [(1.19, "Movietone 1.19"), (1.33, "Academy 4:3 (1.33)"), (1.37, "Academy 1.37"), (1.5, "3:2 (1.50)"),
             (1.6, "16:10 (1.60)"), (1.66, "European widescreen 1.66"), (1.75, "MGM 1.75"), (1.78, "HD 16:9 (1.78)"), (1.85, "American widescreen 1.85"),
             (2.0, "Univisium 2.00"), (2.2, "70 mm 2.20"), (2.35, "CinemaScope 2.35"), (2.39, "Scope 2.39"), (2.55, "CinemaScope 2.55"), (2.76, "Ultra Panavision 2.76")]
SINCE = {1.19: 1928, 1.37: 1932, 1.66: 1953, 1.75: 1953, 1.85: 1953, 2.35: 1953, 2.55: 1953, 2.2: 1955, 2.76: 1957, 2.39: 1970, 1.78: 1980, 1.6: 1980, 2.0: 1990}
def standard(r, year=None):
    """the nearest standard that existed when the film was made (a 1921 short cannot be in Scope)"""
    try: y = int(year)
    except Exception: y = None
    cand = [x for x in STANDARDS if y is None or y >= SINCE.get(x[0], 0) - 2] or STANDARDS
    s = min(cand, key=lambda x: abs(np.log(x[0] / r)))
    return s[1] if abs(np.log(s[0] / r)) < .04 else f"other {r:.2f}"
def bars(p):
    """Black bars on each side, as fractions: rows/columns from the edge that are dark and flat across the whole picture."""
    try: g = np.asarray(Image.open(p).convert("L"), np.float32)
    except Exception: return None
    h, w = g.shape
    def run(lines):
        n = 0
        for ln in lines:
            if ln.mean() < 22 and np.percentile(ln, 95) < 40: n += 1
            else: break
        return n
    t, b = run(g), run(g[::-1]); l, r = run(g.T), run(g.T[::-1])
    if t + b > .6 * h or l + r > .6 * w: return {"w": w, "h": h, "dark": True}     # a dark frame, not a bar
    return {"w": w, "h": h, "bars": [round(t / h, 3), round(b / h, 3), round(l / w, 3), round(r / w, 3)]}
clips = []
for x in json.load(open(os.path.join(L, "odyssey", "results", "clips.json"))):
    clips.append({"id": x["id"], "src": x["sourceId"], "thumb": f"odyssey/thumbs/{x['id']}.jpg", "video": x["videoUrl"], "in": round(float(x.get("matchTimestampSeconds") or 0) - float(x.get("startSeconds") or 0), 2), "label": x.get("aspectRatio")})
seen = {c["id"] for c in clips}
for x in json.load(open(os.path.join(L, "markov", "library.json")))["shots"]:
    if x.get("kind") == "poet" or x["id"] in seen: continue
    clips.append({"id": x["id"], "src": x["src"], "thumb": x["thumb"], "video": x["video"], "in": float(x.get("in") or 0), "label": None})
def job(c):
    m = bars(os.path.join(L, c["thumb"])); return c, m
with cf.ThreadPoolExecutor(8) as ex: done = list(ex.map(job, clips))
out, by = [], {}
for c, m in done:
    if not m: continue
    c["frame"] = round(m["w"] / m["h"], 3)
    if m.get("dark"): c["dark"] = 1
    else:
        t, b, l, r = m["bars"]; c["bars"] = m["bars"]; c["pic"] = round(c["frame"] * (1 - l - r) / max(.05, 1 - t - b), 3)
    out.append(c); by.setdefault(c["src"], []).append(c)
S = json.load(open(os.path.join(L, "aspect", "sources.json")))
src = []
for k, cs in by.items():
    frames = [c["frame"] for c in cs]; fr = st.median(frames); lit = [c for c in cs if "bars" in c]
    # the film's bars: only if most of its shots agree on them (to within 2% of the frame)
    tb = [c["bars"][0] + c["bars"][1] for c in lit]; lr = [c["bars"][2] + c["bars"][3] for c in lit]
    mtb = st.median(tb) if tb else 0; mlr = st.median(lr) if lr else 0
    agree_tb = sum(1 for v in tb if abs(v - mtb) < .02) / max(1, len(tb)); agree_lr = sum(1 for v in lr if abs(v - mlr) < .02) / max(1, len(lr))
    vtb = mtb if mtb > .03 and agree_tb >= .5 else 0; vlr = mlr if mlr > .03 and agree_lr >= .5 else 0
    pic = round(fr * (1 - vlr) / (1 - vtb), 3)
    kind = "windowbox" if vtb and vlr else "letterbox" if vtb else "pillarbox" if vlr else "full frame"
    s = S.get(k, {}); src.append({"src": k, "title": s.get("title"), "year": s.get("year"), "n": len(cs), "frame": round(fr, 3), "pic": pic, "box": kind,
                                 "standard": standard(pic, s.get("year")), "frame_standard": standard(fr)})
    for c in cs: c["film_pic"] = pic
LB = json.load(open(os.path.join(L, "aspect", "labels.json")))       # what kind of film each is (labelled by title and year)
for s in src:
    lb = LB.get(f"{s['title']}|{s['year']}") or {}
    s.update({"kind": lb.get("category", "unknown"), "fiction": lb.get("fiction"), "director": lb.get("director"), "sure": lb.get("sure", False)})
src.sort(key=lambda s: -s["n"])
for s in src: s["sure_shape"] = s["box"] == "full frame" or s["n"] >= 3      # bars seen in fewer than three shots may be one dark shot
films = [{k: s[k] for k in ("title", "year", "n", "frame", "pic", "box", "standard", "kind", "fiction", "director", "sure", "sure_shape")} for s in src]
si = {s["src"]: k for k, s in enumerate(src)}; R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"
json.dump({"standards": STANDARDS, "films": films}, open(os.path.join(L, "aspect", "films.json"), "w"), ensure_ascii=False, separators=(",", ":"))
json.dump([[c["id"], si[c["src"]], 1 if c["thumb"].startswith("odyssey/") else 0, c["frame"]] + (c["bars"] if "bars" in c else []) for c in out if c["src"] in si],
          open(os.path.join(L, "aspect", "clips.json"), "w"), separators=(",", ":"))
json.dump({c["id"]: [c["video"].replace(R2, ""), c.get("in", 0)] for c in out}, open(os.path.join(L, "aspect", "video.json"), "w"), separators=(",", ":"))
json.dump({"standards": STANDARDS, "sources": src, "clips": [{k: c[k] for k in ("id", "src", "thumb", "video", "in", "frame", "film_pic") if k in c} | ({"bars": c["bars"]} if "bars" in c else {}) for c in out]},
          open(os.path.join(L, "aspect", "aspect.json"), "w"), separators=(",", ":"))
import collections
print(len(out), "clips measured from", len(src), "films")
print("frames:", collections.Counter(s["frame_standard"] for s in src).most_common(8))
print("pictures:", collections.Counter(s["standard"] for s in src).most_common(14))
print("kinds:", collections.Counter(s["kind"] for s in src).most_common())
print("boxes:", collections.Counter(s["box"] for s in src).most_common())
for s in [s for s in src if s["box"] != "full frame"][:12]: print(f"  {s['title']} ({s['year']}) · frame {s['frame']} · picture {s['pic']} · {s['box']} · {s['standard']}")
