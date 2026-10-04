"""The casino's deck: what the twelve tables deal from, beyond monte/material.json.
  next      each judged shot's neighbours in its own film (the clip before and after), for THE WRONG CARD
  rejects   frames the strict judge refused, with its reason, for THE REJECT BIN
  decades   words that title films across the century, with clips from each decade, for SAME TITLE, WRONG CENTURY
  routines  the tactical comedy's charges and their routines (and the charges it refused), for THE REFUSAL and WING NUTS
  mishear   spoken lines with two sound-alike corruptions each, for THE MISHEARING
  vid       clip paths for every line and neighbour the tables may play
usage: python3 casino/build_deck.py -> casino/deck.json"""
import json, os, re, random, collections, glob
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
J = lambda *p: json.load(open(os.path.join(L, *p)))
R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"
V = {i: v[0] for i, v in J("aspect", "video.json").items()}; M = J("monte", "material.json"); LIB = J("markov", "library.json")["shots"]
rel = lambda u: u.replace(R2, "")
random.seed(44); vid = {}
# ---- neighbours: the clip before and after each judged shot, in its own film
by = collections.defaultdict(list)
for s in LIB: by[s["src"]].append(s)
for v in by.values(): v.sort(key=lambda s: s.get("st") or 0)   # a clip without a start time sorts first
where = {s["id"]: (s["src"], k) for src, v in by.items() for k, s in enumerate(v)}
nxt = {}
for s in M["shots"]:
    if s["i"] not in where or s.get("title"): continue
    src, k = where[s["i"]]; row = by[src]; nb = []
    for d in (-1, 1):
        if 0 <= k + d < len(row): x = row[k + d]; nb.append([x["id"], round(x.get("dur") or 3, 2)]); vid[x["id"]] = rel(x["video"])
        else: nb.append(None)
    nxt[s["i"]] = nb
# ---- the reject bin: frames refused, with the judge's own words
rej = []
for d in ("judge2", "judge3"):
    pool = {p["n"]: p for p in J("monte", d, "pool.json")}
    for f in sorted(glob.glob(os.path.join(L, "monte", d, "verdicts_*.json"))):
        for v in json.load(open(f)):
            p = pool.get(v["n"]); i = p and p["id"]
            if not i or v.get("card") or v["score"] > 4 or i not in V or not v.get("why") or v["why"] == "missing": continue
            rej.append({"i": i, "film": p.get("film"), "year": p.get("year"), "score": v["score"], "why": v["why"], "sees": v.get("sees") or []}); vid[i] = V[i]
random.shuffle(rej); rej = rej[:420]
# ---- the century in a word: title words that recur across many decades
STOP = set("the a an of and in to for on at with from part i ii iii iv reel by your you how what film amateur collection new is are".split())
words = collections.defaultdict(lambda: collections.defaultdict(list))
for s in LIB:
    if not s.get("year") or not s.get("title"): continue
    dec = int(s["year"]) // 10 * 10
    for w in set(re.findall(r"[a-z]{4,}", s["title"].lower())):
        if w not in STOP: words[w][dec].append(s)
dec_out = []
for w, ds in words.items():
    ds = {d: v for d, v in ds.items() if len(v) >= 2}
    if len(ds) < 4: continue
    pick = {}
    for d, v in sorted(ds.items()):
        films = {}
        for s in v: films.setdefault(s["title"], s)
        ch = random.sample(list(films.values()), min(2, len(films)))
        pick[d] = [[s["id"], s["title"], s["year"]] for s in ch]
        for s in ch: vid[s["id"]] = rel(s["video"])
    dec_out.append({"word": w, "decades": pick})
dec_out.sort(key=lambda x: -len(x["decades"])); dec_out = dec_out[:40]
# ---- the tactical routines, and the charges refused
tin = J("monte", "comic", "tactical_input.json"); pairs = {p["n"]: p for p in J("monte", "comic", "pairs.json")}
shotI = lambda s: tin["shots"][s - 1]["i"] if 0 < s <= len(tin["shots"]) else None
routines, refused = [], []
for f in sorted(glob.glob(os.path.join(L, "monte", "comic", "routines_*.json"))):
    for c in json.load(open(f)):
        ch = next((x for x in tin["charges"] if x["id"] == c["charge"]), None)
        if not ch: continue
        rs = [{"shot": pairs[r["pair"]]["shot"], "line": pairs[r["pair"]]["line"], "pause": r.get("pause_ms", 700), "laugh": r.get("laugh_ms", 1200), "exit": shotI(r.get("exit") or 0),
               "mech": r.get("mechanism"), "vice": r.get("vice"), "color": r.get("local_color"), "giggle": r.get("giggle", 0)} for r in c.get("routines") or [] if r.get("pair") in pairs]
        (routines if rs else refused).append({"charge": ch["i"], "text": ch["text"], "routines": rs})
for r in routines:
    for x in r["routines"]: vid.setdefault(M["lines"][x["line"]]["i"], V.get(M["lines"][x["line"]]["i"]))
# ---- the mishearing: a word in each line swapped for one that sounds near it
def sdx(w):
    w = w.lower(); codes = {**dict.fromkeys("bfpv", "1"), **dict.fromkeys("cgjkqsxz", "2"), **dict.fromkeys("dt", "3"), "l": "4", **dict.fromkeys("mn", "5"), "r": "6"}
    out, last = w[0], codes.get(w[0], "")
    for ch in w[1:]:
        c = codes.get(ch, "")
        if c and c != last: out += c
        last = c
    return (out + "000")[:4]
vocab = collections.defaultdict(set)
for l in M["lines"]:
    for w in re.findall(r"[A-Za-z]{4,}", l["text"]): vocab[sdx(w)].add(w.lower())
mis = []
for j, l in enumerate(M["lines"]):
    ws = l["text"].split()
    if not (6 <= len(ws) <= 14): continue
    cand = [k for k, w in enumerate(ws) if re.fullmatch(r"[\"'(]?[A-Za-z]{5,}[.,!?;:\"')]*", w) and re.sub(r"\W", "", w).lower() not in STOP]   # plain words only
    if not cand: continue
    k = random.choice(cand); core = re.sub(r"\W", "", ws[k]); alts = [a for a in vocab[sdx(core)] if a != core.lower()]
    if len(alts) < 2: continue
    fakes = []
    for a in random.sample(alts, 2):
        w2 = ws[:]; w2[k] = ws[k].replace(core, a if core[0].islower() else a.capitalize()); fakes.append(" ".join(w2))
    if len({l["text"], *fakes}) < 3: continue   # every version different
    mis.append({"line": j, "fakes": fakes}); vid[l["i"]] = V.get(l["i"])
random.shuffle(mis); mis = mis[:500]
for l in M["lines"]: vid.setdefault(l["i"], V.get(l["i"]))
for m in M["music"]: vid.setdefault(m["i"], V.get(m["i"]))   # the music beds
vid = {k: v for k, v in vid.items() if v}
out = {"r2": R2, "next": nxt, "rejects": rej, "decades": dec_out, "routines": routines, "refused": refused, "mishear": mis, "vid": vid}
json.dump(out, open(os.path.join(D, "deck.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print({k: len(v) for k, v in out.items() if isinstance(v, (list, dict))}, round(os.path.getsize(os.path.join(D, "deck.json")) / 1e6, 2), "MB")
