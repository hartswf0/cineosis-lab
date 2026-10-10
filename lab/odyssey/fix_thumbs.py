"""Every still a published page shows must be a URL that resolves on GitHub Pages: the archive's own thumbnail beside each clip
(…/clips/ID.mp4 -> …/thumbnails/ID.jpg) where it has one, checked; otherwise the next picture that has one.   usage: python3 fix_thumbs.py program.json ..."""
import json, re, sys, urllib.request, concurrent.futures as cf
def poster(v): return re.sub(r"/clips/([^/]+)\.mp4$", r"/thumbnails/\1.jpg", v) if re.search(r"/clips/[^/]+\.mp4$", v or "") else None
def ok(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "cineosis-44-research"}), timeout=15).status == 200
    except Exception: return False
for p in sys.argv[1:]:
    P = json.load(open(p))
    def pick(s):
        for c in s["pics"][:6]:
            u = poster(c["video"])
            if u and ok(u): return u
        return None
    with cf.ThreadPoolExecutor(12) as ex: T = list(ex.map(pick, P["scenes"]))
    for s, t in zip(P["scenes"], T): s["thumb"] = t
    json.dump(P, open(p, "w"), separators=(",", ":"), ensure_ascii=False); print(p, sum(1 for t in T if t), "of", len(T), "scenes have a still")
