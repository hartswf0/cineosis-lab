"""LESSON 6 · THE SIEVE. Replays the shared law of CUTBASTARD's planner (cutbastard/plan.py) one rule at a time, to show how
a pool of archive shots narrows before any shot is chosen. Two sieves:
  the archive  every shot the searches brought home, then each standing rule switched on in turn: watched and measured, not
               broken, dead frames under 15 %, title cards under 35 %, has an embedding to be searched by
  the moment   for one line (P020, the Suite take): long enough for the moment, not already used in this take, not the same
               film as any of the last three shots. Counted for the focus line and for all 169 lines of the take.
  the words    the Suite's words for P020 switched on one at a time (beat title, treatment query, literal, place); at each step
               the top shots by CLIP match among the shots the law allows, and how many of the final top 50 are already there.
Every shot shown is a real clip with its measured value. Films kept out of the lab's examples are never shown.
Writes explain/lesson/l6.json.   usage: lab/.venv/bin/python lab/explain/l6.py"""
import json, os, importlib.util
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
spec = importlib.util.spec_from_file_location("plan", os.path.join(LAB, "cutbastard", "plan.py")); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
FOCUS, TAKE = 20, "suite"
BAN = {"all-my-babies", "jfk-exhibit-3-reconstruction-film"}
BANT = ("kinderen naar buiten", "all my babies", "exhibit 3")
corpus, E, ids, ana, aff = P.load_pool(); row = {i: k for k, i in enumerate(ids)}
patches = json.load(open(os.path.join(LAB, "cutbastard", "patches.json")))["patches"]
plan = json.load(open(os.path.join(P.CUTS, TAKE, "plan.json")))["patches"]
published = [x["clip"]["id"] for x in plan]

def ok_to_show(i):
    c = corpus.get(i) or {}
    t = (c.get("sourceTitle") or "").lower()
    return c.get("sourceSlug") not in BAN and not any(b in t for b in BANT) and os.path.exists(os.path.join(LAB, "thumbs", i + ".jpg"))
def card(i, **kw):
    c = corpus[i]; return {"id": i, "title": c.get("sourceTitle"), "year": c.get("sourceYear"), "thumb": f"thumbs/{i}.jpg", **kw}
def examples(ids_, key=None, n=8):
    out = []
    for i in ids_:
        if ok_to_show(i): out.append(card(i, **({"v": round(float(key(i)), 2)} if key else {})))
        if len(out) >= n: break
    return out

# ---- the archive sieve: the standing rules, switched on one at a time
allc = list(corpus)
Wall = {i: P.watched(i) for i in allc}
s0 = allc
s1 = [i for i in s0 if Wall[i]]
s2 = [i for i in s1 if not Wall[i].get("bad")]
s3 = [i for i in s2 if Wall[i]["dead"] < .15]
s4 = [i for i in s3 if Wall[i]["card"] < .35]
s5 = [i for i in s4 if i in row]
gone = lambda a, b: [i for i in a if i not in set(b)]
archive = [
    {"rule": "every shot the searches brought home", "n": len(s0)},
    {"rule": "watched and measured", "law": "a shot has to be downloaded and measured before it can be judged", "n": len(s1), "out": examples(gone(s0, s1))},
    {"rule": "not broken", "law": "a file that would not play, or played wrong", "n": len(s2), "out": examples(gone(s1, s2))},
    {"rule": "dead frames under 15%", "law": "no black, frozen or empty stretches", "n": len(s3), "out": examples(sorted(gone(s2, s3), key=lambda i: -Wall[i]["dead"]), key=lambda i: Wall[i]["dead"])},
    {"rule": "title cards under 35%", "law": "no title cards or leaders", "n": len(s4), "out": examples(sorted(gone(s3, s4), key=lambda i: -Wall[i]["card"]), key=lambda i: Wall[i]["card"])},
    {"rule": "can be searched", "law": "the shot has an embedding, so words can find it", "n": len(s5), "out": examples(gone(s4, s5))},
]
pool = s5; W = {i: Wall[i] for i in pool}; src = {i: corpus[i].get("sourceSlug") for i in pool}

# ---- the moment sieve: the rules that depend on where we are in the film
def moment(pi):
    p = patches[pi]; dur = p["t1"] - p["t0"]
    used = set(published[:pi]); last3 = [src.get(x) or corpus.get(x, {}).get("sourceSlug") for x in published[max(0, pi - 3):pi]]
    a = pool
    b = [i for i in a if W[i]["dur"] >= dur]
    c = [i for i in b if i not in used]
    d = [i for i in c if src[i] not in last3]
    return p, dur, a, b, c, d
counts = []
for pi in range(len(patches)):
    p, dur, a, b, c, d = moment(pi); counts.append([len(a), len(b), len(c), len(d)])
C = np.array(counts)
p, dur, a, b, c, d = moment(FOCUS)
mom = [
    {"rule": "the pool", "n": len(a)},
    {"rule": f"long enough for {dur:.1f} seconds", "law": "a shot must cover the whole moment: no slowing, no looping", "n": len(b), "out": examples(sorted(gone(a, b), key=lambda i: -W[i]["dur"]), key=lambda i: W[i]["dur"])},
    {"rule": "not used earlier in this take", "law": "a shot is never used twice in a cut", "n": len(c), "out": examples(gone(b, c))},
    {"rule": "not the film of the last three shots", "law": "the same source film does not return within three moments", "n": len(d), "out": examples(gone(c, d))},
]
across = {"labels": ["the pool", "long enough", "not used yet", "not a recent film"], "median": [int(np.median(C[:, k])) for k in range(4)],
          "min": [int(C[:, k].min()) for k in range(4)], "max": [int(C[:, k].max()) for k in range(4)], "per_line": C[:, 3].tolist()}

# ---- the words, switched on one at a time
q = json.load(open(os.path.join(LAB, "cutbastard", "queries.json"))); qc = {x["i"]: x for x in q["cues"]}
cat = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Catalogue.json"))); beats = {x["id"]: x for x in cat["beats"]}
cq = qc.get(p["cue"]); bt = beats.get(p["beat"]) or {}
parts = [("beat title", bt.get("title")), ("treatment", bt.get("query")), ("literal", cq and cq["literal"]), ("place", cq and cq["place"])]
parts = [(k, v) for k, v in parts if v]
T = P.text_emb([v for _, v in parts])
allowed = d; Ea = np.stack([np.array(W[i]["emb"]) for i in allowed])
final = T.mean(0); final /= np.linalg.norm(final); top_final = set(np.argsort(-(Ea @ final))[:50].tolist())
words = []
for k in range(1, len(parts) + 1):
    v = T[:k].mean(0); v /= np.linalg.norm(v); s = Ea @ v; order = np.argsort(-s)
    top50 = set(order[:50].tolist()); show = [j for j in order[:40] if ok_to_show(allowed[j])][:8]
    words.append({"on": parts[k - 1][0], "text": parts[k - 1][1], "kept": len(top50 & top_final),
                  "top": [card(allowed[j], v=round(float(s[j]), 3)) for j in show]})
chosen = published[FOCUS]
out = {"focus": {"id": p["id"], "line": p["line"], "chapter": p["chapter"], "dur": round(dur, 2), "take": TAKE,
                 "chosen": card(chosen) if ok_to_show(chosen) else None, "chosen_in_allowed": chosen in set(allowed)},
       "archive": archive, "moment": mom, "across": across, "words": words}
json.dump(out, open(os.path.join(H, "lesson", "l6.json"), "w"), ensure_ascii=False)
print([(x["rule"], x["n"]) for x in archive]); print([(x["rule"], x["n"]) for x in mom]); print(across["median"], across["min"])
print([(w["on"], w["kept"]) for w in words], out["focus"]["chosen"] and out["focus"]["chosen"]["title"], out["focus"]["chosen_in_allowed"])
