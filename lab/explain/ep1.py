"""EPISODE 1 · WHERE THE ARCHIVE CAME FROM — data. The lab's 15,149 shots were not taken from the Moving Image Archive; they were asked
for, film by film. For each project: one of its real questions and what the archive answered (its own search records), the day,
and how many it asked and got. Then the 253 read shots, and the films that were made.
Writes explain/ep/ep1.json.   usage: python3 lab/explain/ep1.py"""
import json, os, random, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); ROOT = os.path.dirname(LAB); J = lambda p: json.load(open(os.path.join(LAB, p)))
D = J("lab-data.json"); by = {s["id"]: s for s in D["shots"]}; Sg = {s["n"]: s for s in D["signs"]}
th = lambda k, fallback=None: (by[k]["thumb"] if k in by else fallback)
out = {}
# the wall: the archive's breadth, one moving shot per decade or so
random.seed(7); dec = collections.defaultdict(list)
for s in D["shots"]:
    if s.get("video") and s.get("decade") and (s.get("lum") or 0) > .25: dec[str(s["decade"])].append(s)
out["wall"] = [{"video": s["video"], "t": s.get("read_t") or 0, "thumb": s["thumb"], "year": s.get("year")} for d in sorted(dec) for s in random.sample(dec[d], min(3, len(dec[d])))][:24]
# five searches, in the order they happened
S = []
r = json.load(open(os.path.join(ROOT, "results/32.json"))); q = "flock of white sheep with a single black sheep in the middle"
S.append({"project": "Cineosis", "col": "#f2c14e", "day": "24 September", "q": q, "why": "the sign Demark, asked as a scene", "asked": 352, "got": 4788, "hits": [{"thumb": th(x["id"]), "title": x["sourceTitle"], "year": x.get("sourceYear")} for x in r[q][:12] if th(x["id"])]})
W = J("wygwyl/WYGWYL_Forage_Catalogue.json"); b = W["beats"][0]; hits = [c for c in W["catalogue"] if b["query"] in (c.get("queries") or [])][:12]
S.append({"project": "Where You Go When You Leave", "col": "#c4f46a", "day": "24 September", "q": b["query"], "why": f"beat 1 of the poem: {b['title']}", "asked": 228, "got": 3981, "hits": [{"thumb": c["thumb"], "title": c["title"], "year": c.get("year")} for c in hits]})
C = J("cutbastard/forage/search.json"); q = next(iter(C)); 
S.append({"project": "CUTBASTARD", "col": "#9fd36a", "day": "24 September", "q": q, "why": "a line of the poem, asked literally", "asked": 417, "got": 9475, "hits": [{"thumb": th(x["id"]), "title": x["sourceTitle"], "year": x.get("sourceYear")} for x in C[q]["clips"][:14] if th(x["id"])][:12]})
O = J("odyssey/results/raw.json"); q = next(iter(O))
S.append({"project": "The Odyssey", "col": "#6f8cff", "day": "1 October", "q": q, "why": "Homer, book 1: the gods in council", "asked": 4537, "got": 28611, "hits": [{"thumb": x["thumbnailUrl"], "title": x["sourceTitle"], "year": x.get("sourceYear")} for x in O[q][:12]]})
F = J("slopfeeder/forage-raw.json"); q = next(iter(F)); fx = F[q] if isinstance(F[q], list) else F[q].get("clips", [])
S.append({"project": "Slopfeeder", "col": "#ff6b5b", "day": "8 October", "q": q, "why": "a meme read as a beach landing", "asked": 108, "got": 2232, "hits": [{"thumb": x.get("thumbnailUrl") or th(x.get("id")), "title": x.get("sourceTitle"), "year": x.get("sourceYear")} for x in fx[:12] if (x.get("thumbnailUrl") or th(x.get("id")))]})
out["searches"] = S
# how the lab was filled: the three routes of 24 September
routes = collections.Counter()
for s in D["shots"]:
    c = set(s.get("collections") or []); routes["cineosis" if "cineosis" in c else "wygwyl" if "wygwyl" in c else "forage"] += 1
out["routes"] = routes; out["total"] = len(D["shots"]); out["films"] = len({s["slug"] for s in D["shots"]}); out["hours"] = round(sum(float(s.get("end") or 0) - float(s.get("start") or 0) for s in D["shots"]) / 3600, 1)
out["archive_est"] = 122000; out["all_libraries"] = 36538
# the 253, in table order, each with its family colour
DOMC = {"perception": "#e9d9a8", "affect": "#f0b9a4", "action": "#e7a37c", "reflection": "#b9cfa0", "mental": "#a9c9c9", "break": "#d9d3c7", "time": "#b8b3d8", "read": "#d9b8d2"}
order = {s["n"]: i for i, s in enumerate(D["signs"])}
R = sorted([s for s in D["shots"] if s.get("signs")], key=lambda s: order.get(str(s["signs"][0]["n"]), 99))
out["read"] = [{"thumb": s["thumb"], "col": DOMC[Sg[str(s["signs"][0]["n"])]["dom"]], "sym": Sg[str(s["signs"][0]["n"])]["symbol"]} for s in R]
out["read_films"] = len({s["slug"] for s in R}); out["read_dec"] = collections.Counter(str(s.get("decade")) for s in R)
# the films that were made from it (published), each at a moment worth seeing
out["made"] = [
 {"title": "The Odyssey", "by": "after Homer", "col": "#6f8cff", "audio": "odyssey/found-audio/call/OD-B01-S01.m4a", "a0": 2.0, "video": J("odyssey/museum.json")["scenes"][0]["pics"][0]["video"], "t": 3, "len": 11},
 {"title": "Where You Go When You Leave", "by": "a poem by Mark Anthony Thomas", "col": "#c4f46a", "video": "https://github.com/hartswf0/cineosis-lab/releases/download/wygwyl-v1/wygwyl-suite.mp4", "t": 179.4, "len": 8},
 {"title": "Norse Half Moon", "by": "with Brandon Polack", "col": "#6cc4d6", "video": "norse/film/norse-half-moon.mp4", "t": 212, "len": 8},
 {"title": "The Republic", "by": "a satire in seventeen episodes", "col": "#e0572a", "video": "republic/pilot/ep01-score.mp4", "t": 48, "len": 8},
 {"title": "Slopfeeder", "by": "a meme, eight songs, the archive and AI", "col": "#ff6b5b", "video": "slopfeeder/roughcut/slopfeeder-final-web.mp4", "t": 140, "len": 8},
 {"title": "Precisely So", "by": "a Wes Anderson cineosis", "col": "#f4c7d0", "video": "wes/precisely-so.mp4", "t": 18, "len": 7},
 {"title": "Monte Carlo Cinema", "by": "films that evolve their own rules", "col": "#b8b3d8", "video": "monte/film-0.mp4", "t": 30, "len": 7}]
json.dump(out, open(os.path.join(H, "ep", "ep1.json"), "w"), ensure_ascii=False, separators=(",", ":"))
for s in S: print(s["project"], "|", s["q"][:60], "|", len(s["hits"]))
print(out["routes"], out["films"], out["hours"], len(out["read"]), out["read_films"])
