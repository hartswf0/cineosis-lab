"""THE RECURRING CAST. Who the archive keeps sending back: every archive film, clip and voice used across the lab's films
(the Found Odyssey, the Markov Odyssey cut, Norse Half Moon, the Republic's 17 episodes and its found version, WYGWYL),
counted by the job it does there. A source film is the unit of "who" (no face recognition); a clip is the exact moment.
roles: picture (seen) · voice (heard speaking, its own sound) · word (lends single words to a spoken mosaic) ·
       character (a SAM cut-out cast as a role) · place (a ground plane) · playedby (its voice plays a named character)
usage: python3 lab/census/census.py   ->  lab/census/census.json"""
import json, os, re, collections
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
J = lambda p: json.load(open(os.path.join(L, p)))

# ---- what every clip and source is called: gathered from every catalogue that names one
meta, srcname, thumbs = {}, {}, {}
def src_of(url):
    m = re.search(r"/sources/([^/]+)/", url or ""); return m.group(1) if m else None
def cid(url):
    m = re.search(r"/clips/([^/]+)\.mp4", url or ""); return m.group(1) if m else url
def know(rec, url_key="video"):
    u = rec.get(url_key) or rec.get("video") or rec.get("v")
    t = rec.get("title") or rec.get("src")
    if not u: return
    s = src_of(u)
    if s and t and s not in srcname: srcname[s] = (t, rec.get("year") or rec.get("y"))
    th = rec.get("thumb") or rec.get("img")
    if th and th.startswith("http"): thumbs.setdefault(cid(u), th); thumbs.setdefault(s, th)
    if rec.get("id"): meta[rec["id"]] = u
for s in J("lab-data.json")["shots"]: know(s)
for s in J("odyssey/library.json")["shots"]: know(s)
for k, v in J("odyssey/found.json")["clips"].items(): know({**v, "id": k})
for k, v in J("norse/storyboard.json")["pics"].items(): know({**v, "id": k})
CAST = {}
for f in ("republic/planes.json", "republic/planes-eps.json", "republic/planes-eps2.json"):
    p = J(f)
    for w, alts in p["cast"].items():
        if alts: CAST.setdefault(w, alts[0])
        for a in alts: know(a)
    for ep in p["episodes"].values():
        for pl in ep.get("places", []):
            for a in pl.get("alts", []): know(a)
title_src = {t.lower(): s for s, (t, y) in srcname.items()}

uses = []   # one row per use; "job" is what the film asked of it, "seq" its place in the film's running order of pictures
SEQ = collections.Counter()
def use(film, role, url=None, *, title=None, where="", said="", who="", job=""):
    if url is None and title:   # archive.json keeps film titles cut at 70 characters; match the cut title to its full one
        tl = title.lower().strip(); s = title_src.get(tl) or next((v for k, v in title_src.items() if len(tl) >= 20 and k.startswith(tl)), "t:" + tl)
        title = None
    else: s = src_of(url) or "?"
    t = srcname.get(s, (title or (s.replace("-", " ").title() if s else "?"), None))
    seq = None
    if role == "picture": SEQ[film] += 1; seq = SEQ[film]
    uses.append({"film": film, "role": role, "src": s, "title": title or t[0], "year": t[1], "clip": cid(url) if url else None,
                 "video": url, "where": where, "said": said, "who": who, "job": job, "seq": seq})
def line_at(lines, t):
    cur = lines[0] if lines else {}
    for ln in lines:
        if ln.get("at", 0) <= t + .5: cur = ln
    return cur.get("text", "")

# ---- THE FOUND ODYSSEY (museum: the line is called, an archive person answers in their own voice, pictures carry it)
mus = J("odyssey/museum.json")
for sc in mus["scenes"]:
    for p in sc["pics"]: use("Found Odyssey", "picture", p["video"], where=sc["id"], job=line_at(sc["lines"], p.get("sw", 0)))
    for i, b in enumerate(sc["beside"]):
        ln = sc["lines"][i] if i < len(sc["lines"]) else {}
        use("Found Odyssey", "voice", b["video"], where=sc["id"], said=ln.get("ans", ""), job=ln.get("text", ""))
fo = J("odyssey/found.json")
for scid, lines in fo["scenes"].items():
    for ln in lines:
        for mode, m in (ln.get("modes") or {}).items():
            for fr in (m or {}).get("frags", []):
                if fr.get("id") in meta: use("Found Odyssey", "word", meta[fr["id"]], where=f"{scid} · {mode}", said=fr.get("words", ""), job=ln.get("text", ""))
# ---- THE MARKOV ODYSSEY (152 scenes cut from shots)
for scid, c in J("odyssey/cuts.json")["cuts"].items():
    for s in c["shots"]:
        if s.get("clip") in meta: use("Markov Odyssey", "picture", meta[s["clip"]], where=scid, job=f"{s.get('role', '')}: {s.get('see', '')}")
# ---- NORSE HALF MOON
for sc in J("norse/program.json")["scenes"]:
    for p in sc["pics"]: use("Norse Half Moon", "picture", p["video"], where=sc["id"], job=line_at(sc["lines"], p.get("sw", 0)))
    for i, b in enumerate(sc["beside"]):
        ln = sc["lines"][i] if i < len(sc["lines"]) else {}
        use("Norse Half Moon", "voice", b["video"], where=sc["id"], said=ln.get("ans", ""), job=ln.get("text", ""))
# ---- THE REPUBLIC, 17 episodes
kokoro = collections.defaultdict(set); world = J("republic/world.json")
for n in range(1, 18):
    f = os.path.join(L, f"republic/pilot/ep{n:02d}.picked.json")
    if not os.path.exists(f): continue
    e = json.load(open(f)); ep = f"EP{n:02d}"
    for b in e["beats"]:
        if b["k"] == "narr":
            for s in b.get("shots", []):
                q = s.get("q", ""); q = "establishing the place" if re.fullmatch(r"p\d+[ab]?", q or "") else q
                use("The Republic", "picture", s["v"], where=ep, job=f"{q} | {b.get('text', '')}")
        elif b["k"] == "chorus": use("The Republic", "voice", b["v"], where=ep, said=b.get("said", ""), who=b.get("who", ""), job=b.get("ask", ""))
        elif b["k"] == "intro" and b["who"] in CAST:
            c = CAST[b["who"]]; use("The Republic", "character", c["video"], where=ep, who=b["who"], job=f"cut out as {b['who']}")
        elif b["k"] == "talk" and b["who"] in world["cast"]: kokoro[world["cast"][b["who"]]["voice"]].add(b["who"])
    g = e["stage"].get("ground", "")
    for f2 in ("republic/planes-eps.json", "republic/planes-eps2.json"):
        for epi in J(f2)["episodes"].values():
            for pl in epi.get("places", []):
                for a in pl.get("alts", []):
                    if a.get("f") == g: use("The Republic", "place", a["video"], where=ep, job=f"the ground: {pl.get('q', '')}")
# ---- THE FOUND REPUBLIC (versions page): archive voices play the characters
for epid, ep in J("republic/archive.json").items():
    for who, v in ep["voices"].items():
        use("Found Republic", "playedby", title=v["film"], where=epid, who=who, job=f"voice of {who}")
    for s in ep.get("segs", []):
        if not s.get("v"): continue
        job = {"line": f"{s.get('who', '')} says: {s.get('line', '')}", "act": s.get("text", ""), "card": s.get("text", ""), "title": s.get("text", "")}.get(s.get("k"), "")
        use("Found Republic", "picture", s["v"], where=epid, who=s.get("who", ""), job=f"{s.get('k')}: {job}")
        if s.get("k") == "line" and s.get("a", {}).get("v"):   # the montage: another clip's voice speaks this character's line
            use("Found Republic", "voice", s["a"]["v"], where=epid, who=s.get("who", ""), job=s.get("line", ""))
# ---- WYGWYL
for b in J("wygwyl/wygwyl-cut.edl.json")["beats"]:
    for k in ("a", "b"):
        if b.get(k) in meta: use("WYGWYL", "picture", meta[b[k]], where=f"beat {b['beat']}", job=f"{b.get('mode', '')}: {b.get('title', '')}")

# ---- tally
FILMS = ["Found Odyssey", "Markov Odyssey", "Norse Half Moon", "The Republic", "Found Republic", "WYGWYL"]
by = collections.defaultdict(lambda: {"uses": 0, "films": collections.Counter(), "roles": collections.Counter(), "clips": collections.Counter(), "said": [], "who": set(), "cast": set(), "title": None, "year": None})
for u in uses:
    r = by[u["src"]]; r["uses"] += 1; r["films"][u["film"]] += 1; r["roles"][u["role"]] += 1
    r["title"] = r["title"] or u["title"]; r["year"] = r["year"] or u["year"]
    if u["clip"]: r["clips"][u["clip"]] += 1
    if u["said"] and u["role"] in ("voice",) and len(r["said"]) < 6 and u["said"] not in r["said"]: r["said"].append(u["said"])
    if u["who"] and u["who"] != "A CITIZEN" and u["role"] in ("voice", "playedby"): r["who"].add(u["who"])
    if u["role"] == "character": r["cast"].add(u["who"])   # the chorus's generic citizen is not a character
wordsin = collections.defaultdict(collections.Counter)
for u in uses:
    if u["role"] == "word": wordsin[u["src"]][u["film"]] += 1
cvid = {u["clip"]: u["video"] for u in uses if u["clip"]}
src = []
for s, r in by.items():
    src.append({"src": s, "title": r["title"], "year": r["year"], "uses": r["uses"], "nfilms": len(r["films"]), "films": dict(r["films"]),
                "roles": dict(r["roles"]), "clips": len(r["clips"]), "top_clip": r["clips"].most_common(1)[0] if r["clips"] else None,
                "said": r["said"], "plays": sorted(r["who"]), "cast": sorted(r["cast"]), "thumb": thumbs.get(s), "top_video": cvid.get(r["clips"].most_common(1)[0][0]) if r["clips"] else None})
for x in src:
    x["words"] = x["roles"].get("word", 0); x["appear"] = x["uses"] - x["words"]
    x["afilms"] = sum(1 for f in FILMS if any(u for u in [1] if by[x["src"]]["films"].get(f, 0) - wordsin[x["src"]][f] > 0))
src.sort(key=lambda x: (-x["afilms"], -x["appear"], -x["words"]))
clips = collections.defaultdict(lambda: {"films": collections.Counter(), "roles": collections.Counter(), "video": None, "src": None, "title": None})
for u in uses:
    if not u["clip"]: continue
    c = clips[u["clip"]]; c["films"][u["film"]] += 1; c["roles"][u["role"]] += 1; c["video"] = u["video"]; c["src"] = u["src"]; c["title"] = u["title"]
clist = [{"clip": k, "title": c["title"], "src": c["src"], "video": c["video"], "thumb": thumbs.get(k) or thumbs.get(c["src"]),
          "uses": sum(c["films"].values()), "nfilms": len(c["films"]), "films": dict(c["films"]), "roles": dict(c["roles"])} for k, c in clips.items()]
clist.sort(key=lambda x: (-x["nfilms"], -x["uses"]))
# a voice that plays more than one character, and a source that is both seen and heard somewhere
multi = [{"title": s["title"], "plays": s["plays"], "films": s["films"]} for s in src if len(s["plays"]) > 1]
out = {"films": FILMS, "n_uses": len(uses), "n_words": sum(1 for u in uses if u["role"] == "word"), "n_sources": len(src), "n_clips": len(clist),
       "per_film": {f: {"uses": sum(1 for u in uses if u["film"] == f), "sources": len({u["src"] for u in uses if u["film"] == f})} for f in FILMS},
       "sources": src[:400], "clips": clist[:300], "multi_role": multi,
       "kokoro": {v: sorted(w) for v, w in sorted(kokoro.items(), key=lambda x: -len(x[1]))}}
json.dump(out, open(os.path.join(H, "census.json"), "w"), ensure_ascii=False, default=list)
json.dump(uses, open(os.path.join(H, "uses.json"), "w"), ensure_ascii=False)   # every use, for operations.py
print(len(uses), "uses ·", len(src), "sources ·", len(clist), "clips")
for f in FILMS: print(f"  {f:16} {out['per_film'][f]}")
for s in src[:25]: print(f"{s['afilms']}/{s['nfilms']} films {s['appear']:4} seen/heard {s['words']:4} words {s['clips']:3} clips  {s['title'][:50]:50} {s['films']}  {s['roles']}")
print("clips in 3+ films:", sum(1 for c in clist if c["nfilms"] >= 3), " 2+:", sum(1 for c in clist if c["nfilms"] >= 2))
for c in clist[:12]: print(c["nfilms"], c["uses"], c["title"][:40], c["films"], c["roles"])
print("voices playing several characters:"); [print("  ", m) for m in multi[:15]]
print("kokoro:", {k: len(v) for k, v in out["kokoro"].items()})
