"""The Task of the Translator, run on the archive. Each Odyssey line translated into what archival people actually said, four ways:
  literal      Hölderlin's way: Homer's words in Homer's order, word for word (inflections allowed); the archive is made to strain
               into Homer's shape, however many fragments it takes; what it never says stays a visible gap
  kinship      the same, but where the archive lacks Homer's word it may answer with a kindred word it does say (WordNet synonyms,
               then one step broader): marked as kin, never passed off as the original
  performance  for the ear and eye: fewer, longer runs from fewer voices; kin allowed; small words may be elided; gaps cost more
  sense        the archival sentence that says what the line says, in its own words (the echo, from ears_match.py), if any
Each is chosen by dynamic programming over the line (cost of a cut, of a kin word, of a gap, of an elision, per mode), and scored
for fidelity (exact 1, inflection .9, kin .6), cuts, and voices. Writes found.json (published).   usage: python3 translate_odyssey.py"""
import glob, json, os, re
from nltk.corpus import wordnet as wn
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears")
words = json.load(open(os.path.join(E, "words.json")))
for f in glob.glob(os.path.join(E, "words.*.json")): words.update(json.load(open(f)))   # workers still transcribing
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that i you he she we they me him her us them my your his our their not no so if then than there here what who which when where how all any some one into out up down over under o oh let now upon shall will would should could may might must do did does have has had am".split())
seq, at = {}, {}
for i, v in words.items():
    ws = [w for w in (v.get("words") or []) if norm(w[0]) and (len(w) < 4 or w[3] >= .45)]
    if not ws or i not in lib: continue
    seq[i] = ws
    for p, w in enumerate(ws): at.setdefault(norm(w[0]), []).append((i, p))
VOCAB = set(at)
def inflections(w):
    out = {w}
    for s in ("s", "es", "ed", "ing", "'s"):
        if w.endswith(s) and len(w) > len(s) + 2: out.add(w[: -len(s)])
        out.add(w + s)
    b = wn.morphy(w);
    if b: out.add(b)
    return {x for x in out if x in VOCAB}
KIN = {}
def kin(w):
    """Homer's word -> {archive word: cost}: exact 0, inflection .1, synonym .35, one step broader .55; only words the archive says."""
    if w in KIN: return KIN[w]
    k = {}
    if w in VOCAB: k[w] = 0.0
    for x in inflections(w): k.setdefault(x, .1)
    if w not in STOP:
        base = wn.morphy(w) or w
        for s in wn.synsets(base)[:4]:
            for l in s.lemma_names()[:6]:
                l = l.lower()
                if "_" not in l and l in VOCAB and l not in k: k[l] = .35
            for h in s.hypernyms()[:2]:
                for l in h.lemma_names()[:4]:
                    l = l.lower()
                    if "_" not in l and l in VOCAB and l not in k: k[l] = .55
    KIN[w] = k; return k
MODES = {"literal": {"cut": .15, "kin": False, "gap": 1.0, "drop_stop": None, "drop": None},
         "kinship": {"cut": .3, "kin": True, "gap": 1.3, "drop_stop": None, "drop": None},
         "performance": {"cut": 1.1, "kin": True, "gap": 1.6, "drop_stop": .75, "drop": 2.6}}
def spans(tokens, k, allow_kin):
    """Every run that starts at token k: (length, kin cost, clip, position, pairs), the best per length."""
    first = kin(tokens[k]) if allow_kin else {x: c for x, c in kin(tokens[k]).items() if c <= .1}
    best = {}
    for form, c0 in first.items():
        for i, p in at.get(form, [])[:2500]:
            ws = seq[i]; n = 0; cost = 0.0; pairs = []
            while k + n < len(tokens) and p + n < len(ws):
                a = norm(ws[p + n][0]); ks = kin(tokens[k + n]) if allow_kin else {x: c for x, c in kin(tokens[k + n]).items() if c <= .1}
                if a not in ks: break
                cost += ks[a]; pairs.append((tokens[k + n], a)); n += 1
                if n not in best or cost < best[n][0]: best[n] = (cost, i, p, list(pairs))
    return best
def translate(text, mode):
    P = MODES[mode]; tokens = [norm(w) for w in text.split() if norm(w)]; N = len(tokens)
    if not N: return None
    INF = 1e9; dp = [INF] * (N + 1); back = [None] * (N + 1); dp[0] = 0
    cache = {}
    for k in range(N):
        if dp[k] >= INF: continue
        if k not in cache: cache[k] = spans(tokens, k, P["kin"])
        for n, (kc, i, p, pairs) in cache[k].items():
            c = dp[k] + P["cut"] + kc
            if c < dp[k + n]: dp[k + n] = c; back[k + n] = ("run", k, n, i, p, pairs)
        g = dp[k] + P["gap"]
        if g < dp[k + 1]: dp[k + 1] = g; back[k + 1] = ("gap", k)
        d = P["drop_stop"] if tokens[k] in STOP else P["drop"]
        if d is not None and dp[k] + d < dp[k + 1]: dp[k + 1] = dp[k] + d; back[k + 1] = ("drop", k)
    out = []; k = N
    while k > 0:
        b = back[k]
        if b[0] == "run":
            _, s, n, i, p, pairs = b; ws = seq[i][p:p + n]
            kinp = [[h, a] for h, a in pairs if h != a and a not in inflections(h) | {h}]
            S = seq[i]; pe = S[p - 1][2] if p > 0 else 0.0; ns = S[p + n][1] if p + n < len(S) else ws[-1][2] + .4   # open and close in the speaker's own silence
            t0 = max(0.0, ws[0][1] - min(.18, max(.03, (ws[0][1] - pe) * .5))); t1 = ws[-1][2] + min(.25, max(.05, (ns - ws[-1][2]) * .5))
            out.append({"id": i, "t0": round(t0, 2), "t1": round(t1, 2), "words": " ".join(w[0] for w in ws), "homer": " ".join(h for h, _ in pairs), "kin": kinp}); k = s
        elif b[0] == "gap": out.append({"gap": tokens[b[1]]}); k = b[1]
        else: out.append({"elided": tokens[b[1]]}); k = b[1]
    out.reverse()
    fid = 0.0
    for x in out:
        if "id" in x:
            for h, a in zip(x["homer"].split(), [norm(w) for w in x["words"].split()]): fid += 1 if h == a else (.9 if a in inflections(h) else .6)
    runs = [x for x in out if "id" in x]
    return {"frags": out, "fidelity": round(fid / N, 2), "cuts": len(runs), "voices": len({x["id"] for x in runs}), "gaps": sum(1 for x in out if "gap" in x), "elided": sum(1 for x in out if "elided" in x)}
found = {}; stats = {m: [] for m in MODES}
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    for s in json.load(open(f))["scenes"]:
        out = []
        for u in s["subs"]:
            if u["kind"] == "SCENE_HEADER": continue
            modes = {m: translate(u["text"], m) for m in MODES}
            for m in MODES:
                if modes[m]: stats[m].append(modes[m])
            e = (u.get("echo") or [None])[0]
            modes["sense"] = {"frags": [{"id": e["id"], "t0": max(0, e["t0"] - .05), "t1": e["t1"] + .08, "words": e["said"], "homer": "", "kin": []}], "score": e["score"], "fidelity": None, "cuts": 1, "voices": 1} if e else None
            out.append({"t0": u["t0"], "t1": u["t1"], "who": u["who"], "text": u["text"], "modes": modes})
        found[s["id"]] = out
clips = {x["id"] for v in found.values() for u in v for m in u["modes"].values() if m for x in m["frags"] if "id" in x}
json.dump({"clips": {i: {"video": lib[i]["video"], "thumb": lib[i]["thumb"], "title": lib[i].get("title"), "year": lib[i].get("year")} for i in clips if i in lib}, "scenes": found}, open(os.path.join(H, "found.json"), "w"), separators=(",", ":"))
import statistics as st
for m, v in stats.items():
    print(f"{m:12s} fidelity {st.mean(x['fidelity'] for x in v):.2f} · cuts per line {st.mean(x['cuts'] for x in v):.1f} · voices {st.mean(x['voices'] for x in v):.1f} · gaps {st.mean(x['gaps'] for x in v):.2f} · elided {st.mean(x['elided'] for x in v):.2f}")
print("sense echoes on", sum(1 for v in found.values() for u in v if u["modes"]["sense"]), "lines · clips", len(clips))
import subprocess, sys
subprocess.run([sys.executable, os.path.join(H, "spoken_odyssey.py")])   # then the spoken mode: whole utterances (adds modes.spoken)
