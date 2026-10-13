"""THE SPINE of Where You Go When You Leave: every question the cut asked the archive, traced back to the text it came from and
forward to what the archive answered and what each take kept. One record per question, one per moment.
  source     a mood question comes from its chapter's lists in the poem's own suite data (moods: feelings; symbols: images);
             a literal / oblique / place question comes from the poem line at its cue
  words      for each question, which of its words the source text already had (the poet's) and which the model added (the asker's);
             for each chapter, which feelings and symbols no question carried (what was dropped)
  answers    the top answers, their scores, and which take used each, where
  moments    for each of the 169 moments: its line, the questions written for it, and each take's shot with how it was found
Writes explain/lesson/spine.json and prints the headline counts.   usage: python3 lab/explain/spine.py"""
import json, os, re, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
S = J("cutbastard/forage/search.json"); Q = J("cutbastard/queries.json"); PT = J("cutbastard/patches.json")["patches"]
WORLDS = {w["n"]: w for w in J("wygwyl/WYGWYL_Mood_and_Scene_Index.json")["worlds"]}
TAKES = ("suite", "scenes", "cineosis", "drift"); plans = {t: J(f"wygwyl/cuts/{t}/plan.json")["patches"] for t in TAKES}
STOP = set("a an the of in on at with and to from by for its his her their into over under through across up down out one two is as or that this while seen it be".split())
def stem(w): w = w.lower().strip("'"); w = re.sub(r"(ies)$", "y", w); w = re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 4 else w; return w
def toks(t): return [w for w in re.findall(r"[A-Za-z']+", t) if w.lower() not in STOP and len(w) > 2]
def split(q, src):
    have = {stem(w) for w in toks(src)}; ws = toks(q)
    return [{"w": w, "from": stem(w) in have} for w in ws]
used = collections.defaultdict(list)
for t in TAKES:
    for p in plans[t]: used[p["clip"]["id"]].append({"take": t, "id": p["id"], "t0": round(p["t0"], 2)})
asked = collections.defaultdict(list)
for v in S.values():
    for r, c in enumerate(v["clips"]): asked[c["id"]].append({"q": v["q"], "rank": r, "kind": v["kind"]})
def line_at(t): return next((p for p in PT if p["t0"] <= t + .01 < p["t1"]), PT[-1])
recs = []
for cue in Q["cues"]:
    p = line_at(cue["start"])
    for k in ("literal", "oblique", "place"):
        q = cue[k]; v = S.get(q, {"clips": []}); sp = split(q, p["line"])
        recs.append({"q": q, "kind": k, "cue": cue["i"], "at": cue["start"], "chapter": cue["chapter"], "source": p["line"], "source_kind": "poem line", "patch": p["id"],
                     "words": sp, "poet_share": round(sum(x["from"] for x in sp) / max(1, len(sp)), 3),
                     "answers": [{"id": c["id"], "title": c["sourceTitle"], "year": c.get("sourceYear"), "score": round(c["score"], 3), "thumb": c["thumbnailUrl"], "used": used.get(c["id"], [])} for c in v["clips"][:8]]})
dropped = {}
for ch in Q["chapters"]:
    w = WORLDS[ch["n"]]; src = "; ".join(w["symbols"] + w["moods"])
    carried = set()
    for q in ch["mood"]:
        sp = split(q, src); v = S.get(q, {"clips": []})
        hit = [s for s in w["symbols"] + w["moods"] if {stem(x) for x in toks(s)} & {stem(x["w"]) for x in sp}]
        carried.update(hit)
        recs.append({"q": q, "kind": "mood", "cue": None, "at": w["window"][0], "chapter": ch["n"], "source": src, "source_kind": "chapter moods and symbols (the suite's own data)",
                     "from_items": hit, "words": sp, "poet_share": round(sum(x["from"] for x in sp) / max(1, len(sp)), 3),
                     "answers": [{"id": c["id"], "title": c["sourceTitle"], "year": c.get("sourceYear"), "score": round(c["score"], 3), "thumb": c["thumbnailUrl"], "used": used.get(c["id"], [])} for c in v["clips"][:8]]})
    dropped[ch["n"]] = {"title": w["title"], "tagline": w["tagline"], "moods": w["moods"], "symbols": w["symbols"], "carried": sorted(carried),
                        "dropped_moods": [m for m in w["moods"] if m not in carried], "dropped_symbols": [s for s in w["symbols"] if s not in carried], "logline": w.get("logline"), "thesis": w.get("thesis")}
moments = []
for i, p in enumerate(PT):
    qs = [r["q"] for r in recs if r.get("patch") == p["id"]]
    takes = {}
    for t in TAKES:
        c = plans[t][i]["clip"]; a = asked.get(c["id"], [])
        takes[t] = {"id": c["id"], "title": c["title"], "year": c.get("year"), "match": plans[t][i]["match"], "why": plans[t][i]["why"],
                    "found_by": min(a, key=lambda x: x["rank"]) if a else None}
    moments.append({"id": p["id"], "t0": p["t0"], "t1": p["t1"], "chapter": p["chapter"], "line": p["line"], "questions": qs, "takes": takes})
kinds = collections.defaultdict(list)
for r in recs: kinds[r["kind"]].append(r["poet_share"])
head = {"questions": len(recs), "poet_share": {k: round(sum(v) / len(v), 3) for k, v in kinds.items()},
        "added_words": collections.Counter(x["w"].lower() for r in recs for x in r["words"] if not x["from"]).most_common(30),
        "kept_from_poet": collections.Counter(x["w"].lower() for r in recs for x in r["words"] if x["from"]).most_common(30),
        "found_by_question": {t: sum(1 for m in moments if m["takes"][t]["found_by"]) for t in TAKES},
        "dropped_moods": sum(len(d["dropped_moods"]) for d in dropped.values()), "all_moods": sum(len(d["moods"]) for d in dropped.values()),
        "dropped_symbols": sum(len(d["dropped_symbols"]) for d in dropped.values()), "all_symbols": sum(len(d["symbols"]) for d in dropped.values())}
json.dump({"head": head, "questions": recs, "chapters": dropped, "moments": moments}, open(os.path.join(H, "lesson", "spine.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps(head, indent=1)[:2500])
print(dropped["01"]["carried"], dropped["01"]["dropped_moods"])
