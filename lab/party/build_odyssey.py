"""The deck for THE FOUND ODYSSEY · CASTING: for each Homer line, the archive's ways of saying it, and pictures to put under it.
  versions  word by word (literal: a collage of many voices), in one breath (sense: one archival sentence that means it),
            the gist (spoken: one person saying it their own way), the performance (words borrowed for their sound)
  pics      the scene's pictures from odyssey/found-pics.json ('call' and its alternates)
Clips are kept once in a table.   usage: python3 lab/party/build_odyssey.py -> lab/party/odyssey.json"""
import json, os, random
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
F = json.load(open(os.path.join(L, "odyssey", "found.json"))); PICS = json.load(open(os.path.join(L, "odyssey", "found-pics.json")))
clips = F["clips"]; T = []; ix = {}
def cid(u):
    if u not in ix: ix[u] = len(T); T.append(u)
    return ix[u]
LABEL = {"literal": "word by word", "sense": "in one breath", "spoken": "the gist", "performance": "borrowed words", "kinship": "word by word"}
scenes = []
for sk, lines in F["scenes"].items():
    pics = []
    for e in (PICS.get(sk, {}) or {}).get("call", []) or []:
        alts = [{"v": cid(e["video"]), "in": e.get("in", 0)}] + [{"v": cid(a["video"]), "in": a.get("in", 0)} for a in (e.get("alts") or [])[:3]]
        pics.append(alts)
    out = []
    for l in lines:
        vs, seen = [], set()
        for m in ("literal", "sense", "spoken", "performance"):
            v = (l.get("modes") or {}).get(m)
            if not v or not v.get("frags"): continue
            fr = [[cid(clips[x["id"]]["video"]), round(x["t0"], 2), round(x["t1"], 2), x.get("words", "")] for x in v["frags"] if x.get("id") in clips]
            key = tuple((a, b) for a, b, c, d in fr)
            if not fr or key in seen or sum(c - b for a, b, c, d in fr) > 12: continue
            seen.add(key); vs.append({"m": m, "label": LABEL[m], "fr": fr})
        if len(vs) >= 2 and len(l["text"]) < 160: out.append({"text": l["text"], "who": l.get("who", ""), "vs": vs[:3]})
    if len(out) >= 4 and len(pics) >= 2: scenes.append({"id": sk, "lines": out, "pics": pics})
R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"; P = []
import re
def pack(u):
    m = re.fullmatch(re.escape(R2) + r"(.+)/clips/([^/]+)\.mp4", u)
    if not m: return u
    if m.group(1) not in P: P.append(m.group(1))
    return [P.index(m.group(1)), m.group(2)]
T = [pack(u) for u in T]
json.dump({"r2": R2, "P": P, "clips": T, "scenes": scenes}, open(os.path.join(D, "odyssey.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(scenes), "scenes", sum(len(s["lines"]) for s in scenes), "lines", len(T), "clips", round(os.path.getsize(os.path.join(D, "odyssey.json")) / 1e3), "KB")
