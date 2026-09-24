"""Run every grounded query against movingimagearchive.com's shot search.

Reads grounding/g*.json, writes results/<n>.json (one per sign), resumable:
queries already cached in results/ are skipped. Rate-limited with 429 backoff.
"""
import glob, json, os, sys, time, urllib.request, urllib.error

API = "https://www.movingimagearchive.com/api/search"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")
KEEP = 15
GAP = 2.5

def skey(n):
    s = str(n); d = "".join(c for c in s if c.isdigit())
    return (int(d), s[len(d):])

def search(q):
    tries = 0
    while True:
        req = urllib.request.Request(API, data=json.dumps({"query": q}).encode(),
                                     headers={"content-type": "application/json",
                                              "user-agent": "cineosis-44-research"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get("clips", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                tries += 1
                print(f"  {time.strftime('%X')} 429 (try {tries}) retry-after={e.headers.get('retry-after')}", flush=True)
                time.sleep(float(e.headers.get("retry-after") or 0) or min(30, 5 * tries))
                continue
            raise

def main():
    os.makedirs(OUT, exist_ok=True)
    signs = []
    for f in sorted(glob.glob(os.path.join(HERE, "grounding", "g*.json"))):
        signs += json.load(open(f))
    only = set(sys.argv[1:])
    todo = sum(len(s["queries"]) for s in signs if not only or str(s["n"]) in only)
    done = 0
    for s in sorted(signs, key=lambda s: skey(s["n"])):
        if only and str(s["n"]) not in only:
            continue
        path = os.path.join(OUT, f"{s['n']}.json")
        cache = json.load(open(path)) if os.path.exists(path) else {}
        for q in s["queries"]:
            done += 1
            if q in cache:
                continue
            clips = search(q)[:KEEP]
            cache[q] = [{k: c.get(k) for k in (
                "id", "sourceSlug", "sourceTitle", "sourceYear", "startSeconds", "endSeconds",
                "matchTimestampSeconds", "videoUrl", "thumbnailUrl", "colorMode", "score")}
                for c in clips]
            json.dump(cache, open(path, "w"), indent=1)
            print(f"{time.strftime('%X')} [{done}/{todo}] #{s['n']} {len(clips):2d}  {q}", flush=True)
            time.sleep(GAP)
    print("DONE", flush=True)

if __name__ == "__main__":
    main()
