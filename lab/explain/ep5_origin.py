"""Where every shot of the four WYGWYL takes came from: which question brought it back (CUTBASTARD's literal / oblique / place / mood
questions, the WYGWYL forage suite's searches, the Cineosis sign searches) or whether it came in only because its whole film was
fetched. Then: each take's mix of origins, the questions that supplied the most shots to the takes, and the shots more than one
take used. Appends "origin" to explain/ep/ep5.json.   usage: python3 lab/explain/ep5_origin.py"""
import json, os, glob, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); ROOT = os.path.dirname(LAB); J = lambda p: json.load(open(os.path.join(LAB, p)))
E = json.load(open(os.path.join(H, "ep", "ep5.json"))); TK = ("suite", "scenes", "cineosis", "drift")
found = collections.defaultdict(list)      # clip id -> [(kind, question, where)]
for q, v in J("cutbastard/forage/search.json").items():
    for c in v["clips"]: found[c["id"]].append((v["kind"], q, f"chapter {v['chapter']}"))
for c in J("wygwyl/WYGWYL_Forage_Catalogue.json")["catalogue"]:
    for q in c.get("queries") or []: found[c["id"]].append(("suite forage", q, "the forage suite"))
for f in glob.glob(os.path.join(ROOT, "results", "*.json")):
    n = os.path.basename(f)[:-5]
    for q, cs in json.load(open(f)).items():
        for c in cs: found[c["id"]].append(("sign search", q, f"sign {n}"))
whole = set()
for f in glob.glob(os.path.join(LAB, "cutbastard/forage/sources/*.json")):
    for c in json.load(open(f))["clips"]: whole.add(c["id"])
takes = {t: [p["clip"] for p in J(f"wygwyl/cuts/{t}/plan.json")["patches"]] for t in TK}
KINDS = ["literal", "oblique", "place", "mood", "suite forage", "sign search", "whole film"]
mix, qcount, qthumbs = {}, collections.Counter(), collections.defaultdict(list)
for t, clips in takes.items():
    m = collections.Counter()
    for c in clips:
        hits = found.get(c["id"]) or []
        if hits:
            k0 = hits[0][0]; m[k0] += 1
            for k, q, w in {(k, q, w) for k, q, w in hits}:
                qcount[(k, q)] += 1
                if len(qthumbs[(k, q)]) < 6 and c["thumb"] not in qthumbs[(k, q)]: qthumbs[(k, q)].append(c["thumb"])
        elif c["id"] in whole: m["whole film"] += 1
        else: m["other"] += 1
    mix[t] = {k: m.get(k, 0) for k in KINDS + ["other"]}
top = [{"kind": k, "q": q, "n": n, "thumbs": qthumbs[(k, q)]} for (k, q), n in qcount.most_common(12)]
use = collections.Counter(c["id"] for t in TK for c in {x["id"]: x for x in takes[t]}.values())
cross = []
for cid, n in use.most_common():
    if n < 2: break
    c = next(x for t in TK for x in takes[t] if x["id"] == cid)
    cross.append({"id": cid, "n": n, "title": c["title"], "year": c.get("year"), "thumb": c["thumb"], "in": [t for t in TK if any(x["id"] == cid for x in takes[t])], "found": [list(h) for h in (found.get(cid) or [])[:2]]})
E["origin"] = {"kinds": KINDS, "mix": mix, "top": top, "cross": cross[:16], "n_cross": len(cross)}
json.dump(E, open(os.path.join(H, "ep", "ep5.json"), "w"), ensure_ascii=False, separators=(",", ":"))
for t in TK: print(t, mix[t])
print("cross", len(cross), [(c["title"][:20], c["n"], c["in"]) for c in cross[:5]])
for x in top[:8]: print(x["n"], x["kind"], x["q"][:70])
