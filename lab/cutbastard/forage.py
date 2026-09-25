"""CUTBASTARD · forage: run the poem-line and mood queries against the archive; fetch source films' full clip lists.

    python3 forage.py search        # queries.json → forage/search.json   (rate-limited, resumable)
    python3 forage.py sources a b…  # source slugs → forage/sources/<slug>.json (ordered clip list, synopsis)
    python3 forage.py merge         # new clips → ../cache/corpus.json (collection "forage") + thumbnail list

Every clip keeps where it came from (query kind, cue, chapter) so a cut can be traced back to the line that asked for it.
"""
import json, os, re, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
F = os.path.join(HERE, "forage")
API = "https://www.movingimagearchive.com/api/search"
SRC = "https://www.movingimagearchive.com/sources/"
UA = {"user-agent": "cineosis-lab (research; contact via github.com/hartswf0/cineosis-lab)"}
GAP = 2.5

def get(url, data=None):
    tries = 0
    while True:
        req = urllib.request.Request(url, data=data, headers={**UA, **({"content-type": "application/json"} if data else {})})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and tries < 8:
                tries += 1; time.sleep(float(e.headers.get("retry-after") or 0) or 5 * tries); continue
            raise

def search():
    q = json.load(open(os.path.join(HERE, "queries.json")))
    jobs = []
    for c in q["cues"]:
        for kind in ("literal", "oblique", "place"):
            if c.get(kind): jobs.append({"q": c[kind], "kind": kind, "cue": c["i"], "chapter": c["chapter"]})
    for ch in q["chapters"]:
        for m in ch["mood"]: jobs.append({"q": m, "kind": "mood", "cue": None, "chapter": ch["n"]})
    os.makedirs(F, exist_ok=True)
    path = os.path.join(F, "search.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    for k, j in enumerate(jobs):
        if j["q"] in out: continue
        clips = json.loads(get(API, json.dumps({"query": j["q"]}).encode())).get("clips", [])[:15]
        out[j["q"]] = {**j, "clips": [{x: c.get(x) for x in ("id", "sourceSlug", "sourceTitle", "sourceYear", "startSeconds", "endSeconds",
                                                               "matchTimestampSeconds", "videoUrl", "thumbnailUrl", "colorMode", "score", "position")} for c in clips]}
        json.dump(out, open(path, "w"))
        print(f"{time.strftime('%X')} [{k + 1}/{len(jobs)}] {j['kind']:7s} ch{j['chapter']} {len(clips):2d}  {j['q'][:70]}", flush=True)
        time.sleep(GAP)
    print("DONE search", len(out), flush=True)

def sources(slugs):
    d = os.path.join(F, "sources"); os.makedirs(d, exist_ok=True)
    for k, slug in enumerate(slugs):
        path = os.path.join(d, slug + ".json")
        if os.path.exists(path): continue
        try:
            html = get(SRC + slug).decode("utf-8", "replace")
        except Exception as e:
            print("skip", slug, e, flush=True); continue
        # the page embeds its clip list as escaped JSON: pull each clip object by its fields
        t = html.replace('\\"', '"')
        clips = []
        for m in re.finditer(r'\{"id":"([0-9a-f-]{36})","sourceId":"[^"]*","sourceSlug":"([^"]*)","sourceTitle":"((?:[^"\\]|\\.)*)","sourceYear":(null|\d+),"position":(\d+),"startSeconds":([\d.]+),"endSeconds":([\d.]+),"durationSeconds":[\d.]+,"videoUrl":"([^"]+)","thumbnailUrl":"([^"]+)"', t):
            cid, sl, title, yr, pos, s0, s1, vu, tu = m.groups()
            clips.append({"id": cid, "sourceSlug": sl, "sourceTitle": title, "sourceYear": None if yr == "null" else int(yr), "position": int(pos),
                          "startSeconds": float(s0), "endSeconds": float(s1), "videoUrl": vu.split("?")[0], "thumbnailUrl": tu.split("?")[0]})
        seen, uniq = set(), []
        for c in sorted(clips, key=lambda c: c["position"]):
            if c["id"] not in seen: seen.add(c["id"]); uniq.append(c)
        syn = re.search(r'"synopsis":"((?:[^"\\]|\\.){20,})"', t)
        json.dump({"slug": slug, "synopsis": syn.group(1) if syn else None, "clips": uniq}, open(path, "w"))
        print(f"[{k + 1}/{len(slugs)}] {slug}: {len(uniq)} clips", flush=True)
        time.sleep(GAP)
    print("DONE sources", flush=True)

def merge():
    corpus_p = os.path.join(LAB, "cache", "corpus.json")
    corpus = json.load(open(corpus_p))
    new, thumbs = 0, []
    def add(c, via):
        nonlocal new
        i = c["id"]
        if i not in corpus:
            corpus[i] = {"id": i, "sourceSlug": c.get("sourceSlug"), "sourceTitle": c.get("sourceTitle"), "sourceYear": c.get("sourceYear"),
                         "startSeconds": c["startSeconds"], "endSeconds": c["endSeconds"],
                         "matchTimestampSeconds": c.get("matchTimestampSeconds") or c["startSeconds"], "videoUrl": c["videoUrl"],
                         "thumbnailUrl": c["thumbnailUrl"], "colorMode": c.get("colorMode"), "score": c.get("score"), "collections": []}
            new += 1
        if "position" in c and c["position"] is not None: corpus[i]["position"] = c["position"]
        if "forage" not in corpus[i].setdefault("collections", []): corpus[i]["collections"].append("forage")
        corpus[i].setdefault("forage", [])
        if via and via not in corpus[i]["forage"]: corpus[i]["forage"].append(via)
        if not os.path.exists(os.path.join(LAB, "thumbs", i + ".jpg")): thumbs.append(f"{c['thumbnailUrl']}\t{i}")
    sp = os.path.join(F, "search.json")
    for q, r in (json.load(open(sp)).items() if os.path.exists(sp) else []):
        for rank, c in enumerate(r["clips"]):
            add(c, {"q": q, "kind": r["kind"], "cue": r["cue"], "chapter": r["chapter"], "rank": rank})
    d = os.path.join(F, "sources")
    for f in (os.listdir(d) if os.path.isdir(d) else []):
        for c in json.load(open(os.path.join(d, f)))["clips"]:
            add(c, None)
    json.dump(corpus, open(corpus_p, "w"))
    open(os.path.join(F, "thumbs.txt"), "w").write("\n".join(sorted(set(thumbs))) + "\n")
    print("merged; new clips", new, "; corpus", len(corpus), "; thumbs to fetch", len(set(thumbs)))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "search"
    {"search": search, "merge": merge}.get(cmd, lambda: sources(sys.argv[2:]))()
