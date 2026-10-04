"""The casino's quiz deck: every round has one right answer the archive can show.
  said   a line of speech (for WHO SAID THIS: tap the picture that spoke it)
  heard  a line and two sound-alike corruptions (for WHAT DID THEY SAY)
  year   a clip and its year (for WHAT DECADE)
  next   a shot and the clip after it in its own film (for WHAT CAME NEXT)
  bin    frames the strict judge kept (8+) or binned (4 or less), with its reason (for KEEP OR BIN)
  dub    a line and the picture the comedy judge put under it (for THE DUB)
Paths are relative to r2.   usage: python3 casino/build_quiz.py -> casino/quiz.json"""
import json, os, random, collections
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
J = lambda *p: json.load(open(os.path.join(L, *p)))
M = J("monte", "material.json"); K = J("casino", "deck.json"); LIB = J("markov", "library.json")["shots"]; R2 = K["r2"]
V = {i: v[0] for i, v in J("aspect", "video.json").items()}; V.update(K["vid"])
S = {s["i"]: s for s in M["shots"]}
random.seed(7)
yr = lambda y: int(y) if y else None
said = [{"v": V[l["i"]], "t0": l["t0"], "t1": l["t1"], "text": l["text"], "film": l.get("film"), "year": yr(l.get("year"))}
        for l in M["lines"] if l["i"] in V and 3 <= len(l["text"].split()) <= 14 and 1 <= l["t1"] - l["t0"] <= 5]
said = random.sample(said, min(400, len(said)))
heard = []
for m in K["mishear"]:
    l = M["lines"][m["line"]]
    if l["i"] in V and l["t1"] - l["t0"] <= 7: heard.append({"v": V[l["i"]], "t0": l["t0"], "t1": l["t1"], "text": l["text"], "fakes": m["fakes"], "film": l.get("film"), "year": yr(l.get("year"))})
heard = heard[:300]
by = collections.defaultdict(list)
for s in LIB:
    if s.get("year") and s.get("title") and s.get("video") and 1900 <= int(s["year"]) < 2020: by[int(s["year"]) // 10 * 10].append(s)
year = []
for d, v in sorted(by.items()):
    for s in random.sample(v, min(45, len(v))): year.append({"v": s["video"].replace(R2, ""), "at": round(s.get("in") or 0, 2), "film": s["title"], "year": int(s["year"])})
nxt = []
for i, nb in K["next"].items():
    if nb[1] and i in S and nb[1][0] in V: nxt.append({"v": S[i]["v"], "nv": V[nb[1][0]], "film": S[i]["film"], "year": yr(S[i].get("year"))})
nxt = random.sample(nxt, min(300, len(nxt)))
keep = [{"v": s["v"], "score": s["score"], "why": s["why"], "film": s["film"], "year": yr(s.get("year"))} for s in M["shots"] if s["score"] >= 8 and not s["title"] and s.get("why")]
binned = [{"v": V[r["i"]], "score": r["score"], "why": r["why"], "film": r.get("film"), "year": yr(r.get("year"))} for r in K["rejects"] if r["i"] in V]
dub = []
for si, j, f in J("monte", "comic-jokes.json"):
    l = M["lines"][j]
    if f >= 7 and si in S and l["i"] in V: dub.append({"v": S[si]["v"], "film": S[si]["film"], "funny": f, "line": {"v": V[l["i"]], "t0": l["t0"], "t1": l["t1"], "text": l["text"], "film": l.get("film")}})
out = {"r2": R2, "said": said, "heard": heard, "year": year, "next": nxt, "bin": keep + binned, "dub": dub}
json.dump(out, open(os.path.join(D, "quiz.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print({k: len(v) for k, v in out.items() if isinstance(v, list)}, "keep", len(keep), "bin", len(binned), round(os.path.getsize(os.path.join(D, "quiz.json")) / 1e3), "KB")
