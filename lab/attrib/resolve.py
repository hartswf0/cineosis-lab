"""Where every clip comes from: each source film in the archive (attrib/titles.json: folder -> title, year) is looked up in the
Internet Archive by its title (advancedsearch, moving images), and the best item is kept when its title and year agree well enough:
its identifier (the whole film), collection, sponsor or maker, and licence. A film with no confident match keeps a search link
instead of a guess. Runs where archive.org can be reached (.github/workflows/attrib.yml).   usage: python3 lab/attrib/resolve.py
-> lab/attrib/sources.json"""
import json, os, re, time, urllib.parse, urllib.request
D = os.path.dirname(os.path.abspath(__file__)); T = json.load(open(os.path.join(D, "titles.json")))
OUT = os.path.join(D, "sources.json"); have = json.load(open(OUT)) if os.path.exists(OUT) else {}
STOP = set("a an the and or of to in on at by for with from part reel i ii iii iv v vi 1 2 3 4 5 6 amateur film".split())
def norm(t):   # the title as a library would catalogue it: no part or reel, no brackets
    t = re.sub(r"^\[?amateur film:\s*", "", t or "", flags=re.I).replace("]", " ")
    t = re.sub(r"\((part|reel)[^)]*\)|\bpart\s+[ivx\d]+\b|\breel\s+\d+(\s+of\s+\d+)?\b", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s'&-]", " ", t)).strip()
toks = lambda t: {w for w in re.findall(r"[a-z0-9']+", norm(t).lower()) if w not in STOP}
def ask(q):
    u = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode([("q", q), *[("fl[]", f) for f in ("identifier", "title", "year", "date", "creator", "sponsor", "collection", "licenseurl")], ("rows", "12"), ("output", "json")])
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "cineosis-lab attribution (github.com/hartswf0/cineosis-lab)"}), timeout=30) as r: return json.load(r)["response"]["docs"]
        except Exception: time.sleep(2 * (k + 1))
    return []
one = lambda x: (x[0] if isinstance(x, list) and x else x) or None
def score(t, y, d):
    a, b = toks(t), toks(one(d.get("title")) or ""); j = len(a & b) / max(1, len(a | b))   # a record may list several titles: the first is its own
    dy = one(d.get("year")) or (str(one(d.get("date")) or "")[:4] or None)
    try: dy = int(dy)
    except Exception: dy = None
    if y and dy: j += .15 if abs(int(y) - dy) <= 1 else (-.2 if abs(int(y) - dy) > 3 else 0)
    col = d.get("collection") or []; col = col if isinstance(col, list) else [col]
    if any(c in ("prelinger", "ephemera", "prelinger_library", "prelinger_homemovie") for c in col): j += .05
    return j
n = 0
for folder, s in T.items():
    if folder in have: continue
    t, y = s["title"], s.get("year"); nt = norm(t)
    try:   # one odd record never stops the run
        docs = ask(f'title:("{nt}") AND mediatype:(movies)') if nt else []
        if not docs and nt: docs = ask(" ".join(sorted(toks(t))) + " AND mediatype:(movies)")
        best = max(docs, key=lambda d: score(t, y, d), default=None); sc = score(t, y, best) if best else 0
    except Exception as ex: print("skipped", folder, ex, flush=True); best, sc = None, 0
    rec = {"title": t, "year": y, "search": "https://archive.org/search?query=" + urllib.parse.quote(f'"{nt}"') + "&sin=&and[]=mediatype%3A%22movies%22"}
    if best and sc >= .62:
        col = best.get("collection") or []; col = col if isinstance(col, list) else [col]
        rec.update({"id": best["identifier"], "url": "https://archive.org/details/" + best["identifier"], "found": one(best.get("title")), "found_year": one(best.get("year")) or str(one(best.get("date")) or "")[:4] or None,
                    "collection": col, "creator": one(best.get("creator")), "sponsor": one(best.get("sponsor")), "license": one(best.get("licenseurl")), "conf": round(sc, 2)})
    have[folder] = rec; n += 1
    if n % 50 == 0: json.dump(have, open(OUT, "w"), ensure_ascii=False, indent=0); print(n, "looked up ·", sum(1 for v in have.values() if v.get("id")), "found", flush=True)
    time.sleep(.25)
json.dump(have, open(OUT, "w"), ensure_ascii=False, indent=0)
print("done ·", len(have), "sources ·", sum(1 for v in have.values() if v.get("id")), "matched to an archive.org item")
