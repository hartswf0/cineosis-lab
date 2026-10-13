"""LESSON 7 · ASKING. How a moment of the poem becomes questions, what the archive gives back, and how 6,255 answers narrow.
  hook      the shot the archive gave back most often, with every question it answered, and where a take used it
  example   one line (P082, 'To pick a road') asked four ways: the cue's literal / oblique / place questions and the chapter's moods,
            the top five answers of each, and where in the poem each answer was finally used (answers travel)
  chose     what each take put under that line, and which question had found it
  words     the asker's habits: most-used words across 417 questions, keyword-in-context lines for 'night', what 'empty' brings back
  sieve     answers -> different shots -> came back more than once -> used in a cut
  practice  a second line, asked and answered, no explanation
Writes explain/lesson/l7.json.   usage: python3 lab/explain/l7.py"""
import json, os, re, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
S = J("cutbastard/forage/search.json"); Q = J("cutbastard/queries.json"); PT = J("cutbastard/patches.json")["patches"]
BAN = {"all-my-babies", "jfk-exhibit-3-reconstruction-film"}            # no birth, no assassination evidence as examples
TAKES = ("suite", "scenes", "cineosis", "drift")
plans = {t: J(f"wygwyl/cuts/{t}/plan.json")["patches"] for t in TAKES}
used = collections.defaultdict(list)
for t in TAKES:
    for p in plans[t]: used[p["clip"]["id"]].append({"take": t, "id": p["id"], "t0": round(p["t0"], 2), "t1": round(p["t1"], 2)})
asked = collections.defaultdict(list); info = {}
for v in S.values():
    for r, c in enumerate(v["clips"]): asked[c["id"]].append({"kind": v["kind"], "q": v["q"], "rank": r}); info[c["id"]] = c
def local(i): return f"clips/{i}.mp4" if os.path.exists(os.path.join(LAB, "clips", i + ".mp4")) else None
def hit(c, r):
    return {"id": c["id"], "rank": r, "title": c["sourceTitle"], "year": c.get("sourceYear"), "score": round(c["score"], 3), "bw": c.get("colorMode") == "black_and_white",
            "video": local(c["id"]) or c["videoUrl"], "t": round(max(0, c["matchTimestampSeconds"] - c["startSeconds"] - 1), 2), "thumb": c["thumbnailUrl"], "used": used.get(c["id"], []), "asked": len(asked[c["id"]])}
def top(q, n=5): return [hit(c, r) for r, c in enumerate(S[q]["clips"]) if c["sourceSlug"] not in BAN][:n]
def patch_at(t): return next(p for p in PT if abs(p["t0"] - t) < .01)
def ask_cue(i, moods=1):
    cue = Q["cues"][i]; p = patch_at(cue["start"]); ch = cue["chapter"]
    mq = [v["q"] for v in S.values() if v["kind"] == "mood" and v["chapter"] == ch]
    # the mood question whose answers were used most
    mq.sort(key=lambda q: -sum(1 for c in S[q]["clips"][:5] if c["id"] in used))
    asks = [{"kind": k, "q": cue[k], "hits": top(cue[k])} for k in ("literal", "oblique", "place")] + [{"kind": "mood", "q": q, "hits": top(q)} for q in mq[:moods]]
    chose = []
    for t in TAKES:
        pp = next(x for x in plans[t] if x["id"] == p["id"]); c = pp["clip"]; a = asked.get(c["id"], [])
        first = min(a, key=lambda x: x["rank"]) if a else None
        cueof = next((k for k in Q["cues"] for kk in ("literal", "oblique", "place") if first and k[kk] == first["q"]), None)
        chose.append({"take": t, "id": c["id"], "title": c["title"], "year": c.get("year"), "video": c["clip"], "in": c["in"], "match": pp["match"], "why": pp["why"],
                      "found_by": first, "found_at": cueof["start"] if cueof else None, "n_asked": len(a)})
    return {"i": i, "start": cue["start"], "chapter": ch, "patch": p["id"], "t0": p["t0"], "t1": p["t1"], "line": p["line"], "asks": asks, "chose": chose}
out = {"audio": "wygwyl/WYGWYL_Suite_Audio.mp3", "dur": J("cutbastard/patches.json")["duration"], "n_q": len(S),
       "kinds": collections.Counter(v["kind"] for v in S.values())}
# hook: the most-returned shot
hid = max(asked, key=lambda k: (len(asked[k]), k in used)); c = info[hid]
out["hook"] = {"id": hid, "title": c["sourceTitle"], "year": c.get("sourceYear"), "video": local(hid) or c["videoUrl"], "t": round(max(0, c["matchTimestampSeconds"] - c["startSeconds"] - 1), 2), "qs": asked[hid], "used": used.get(hid, [])}
out["example"] = ask_cue(52)
out["practice"] = ask_cue(18)
# words
STOP = set("a an the of in on at with and to from by for its his her their into over under through across up down out one two is as or that this while seen".split())
cnt = collections.Counter(w for v in S.values() for w in re.findall(r"[a-z']+", v["q"].lower()) if w not in STOP and len(w) > 2)
out["words"] = cnt.most_common(18)
def kwic(word, n=40):
    L = []
    for v in S.values():
        m = re.search(r"\b" + word + r"\b", v["q"], re.I)
        if m: L.append([v["q"][:m.start()], v["q"][m.start():m.end()], v["q"][m.end():], v["kind"]])
    return L[:n], len(L)
out["kwic"] = {w: dict(zip(("lines", "n"), kwic(w))) for w in ("night", "empty", "light")}
em = []
for v in S.values():
    if re.search(r"\bempty\b", v["q"]):
        for c in v["clips"][:2]:
            if c["sourceSlug"] not in BAN: em.append({"thumb": c["thumbnailUrl"], "title": c["sourceTitle"], "q": v["q"]})
out["empty"] = em[:48]
# sieve
dots = []
for k, a in asked.items(): dots.append([1 if info[k].get("colorMode") == "black_and_white" else 0, len(a), 1 if k in used else 0])
dots.sort(key=lambda d: (-d[2], -d[1]))
out["sieve"] = {"returned": sum(len(v["clips"]) for v in S.values()), "unique": len(asked), "multi": sum(1 for a in asked.values() if len(a) > 1),
                "used": sum(1 for k in asked if k in used), "used_all": len(used), "dots": dots,
                "kept": [info[k]["thumbnailUrl"] for k in asked if k in used and info[k]["sourceSlug"] not in BAN][:253]}
json.dump(out, open(os.path.join(H, "lesson", "l7.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("hook", out["hook"]["title"], len(out["hook"]["qs"]), out["hook"]["used"])
for k in ("example", "practice"):
    e = out[k]; print(k, e["patch"], e["line"][:80])
    for a in e["asks"]: print("  ", a["kind"], a["q"], [(h["title"][:22], h["score"], [u["take"] for u in h["used"]]) for h in a["hits"]])
    for c in e["chose"]: print("   chose", c["take"], c["title"][:30], c["match"], c["found_by"] and c["found_by"]["q"][:50], c["found_at"], c["n_asked"])
print(out["words"]); print({k: v["n"] for k, v in out["kwic"].items()}); print({k: v for k, v in out["sieve"].items() if k not in ("dots", "kept")})
