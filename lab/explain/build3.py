"""Part II, downstream: how our films decide what to show and what to say (appended to explain/film2.json).
  odyssey  a Found Odyssey line: Homer's line, the archive's spoken answer and its score, the picture and the captain's verdict
  sheep    the seed shot's two jobs in the Markov Odyssey (its shot specs)
  captain  a machine critic's diagnosis of a scene
  norse    a Norse Half Moon line: the voice memo, the archive's answer, the picture
  republic a Republic line: the script, the archive sentence that replaced it
  takes    one WYGWYL moment in its four takes, and how many clips the takes share
usage: python3 lab/explain/build3.py"""
import json, os, glob, itertools
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
F = json.load(open(os.path.join(H, "film2.json"))); D = {s["id"]: s for s in J("lab-data.json")["shots"]}
M = J("odyssey/museum.json"); sc = M["scenes"][0]; ln = sc["lines"][0]; pic = sc["pics"][0]
cap = {}
for f in glob.glob(os.path.join(LAB, "odyssey/cache/steer/captain_*.json")): cap.update(json.load(open(f)))
F["odyssey"] = {"scene": sc["id"], "title": sc["title"], "audio": sc["audio"], "line": ln, "pic": pic}
c = cap.get("OD-B22-S01") or next(iter(cap.values()))
F["captain"] = {"scene": "OD-B22-S01", "asks": c.get("asks"), "diagnosis": (c.get("diagnosis") or [])[:3]}
U = J("census/uses.json"); SEED = "21171e70-f59f-55b6-85c3-29691c97e312"
F["sheep"] = [{"where": u["where"], "job": u["job"]} for u in U if u.get("clip") == SEED]
N = J("norse/program.json"); ns = next(s for s in N["scenes"] if s["id"].startswith("NHM-B02")); F["norse"] = {"scene": ns["id"], "audio": ns["audio"], "line": ns["lines"][0], "pic": ns["pics"][0], "t0": ns.get("t0", 0)}
S = J("republic/script.json"); ep = S["episodes"][0]; R = J("republic/found.json")[ep["id"]]["answers"]
lines = ep.get("beats") or []
k = next(iter(R)); li = lines[int(k)] if isinstance(lines, list) and len(lines) > int(k) else {}
F["republic"] = {"episode": ep["name"], "line": li, "answer": R[k]}
T = {}
for t in ["suite", "scenes", "cineosis", "drift"]: T[t] = J(f"wygwyl/cuts/{t}/patches.json")
films = {w["slug"]: w for w in J("wygwyl/cuts/index.json")}
moments = []
for i in (20, 61, 120):
    p0 = T["suite"][i]; moments.append({"t0": p0["t0"], "t1": p0["t1"], "line": p0["line"], "codes": p0.get("codes"), "chapter": p0.get("film"),
        "takes": {t: {"title": T[t][i]["clip"]["title"], "year": T[t][i]["clip"].get("year"), "thumb": T[t][i]["clip"]["thumb"], "why": T[t][i]["why"]} for t in T}})
ids = {t: {p["clip"]["id"] for p in T[t]} for t in T}
F["takes"] = {"films": {t: films[t]["film"] for t in T}, "ideas": {t: films[t]["idea"] for t in T}, "moments": moments, "sizes": {t: len(ids[t]) for t in T},
              "shared": {f"{a}+{b}": len(ids[a] & ids[b]) for a, b in itertools.combinations(T, 2)}}
# a strip of the archive sorted by hue, and the Demark sign's own search phrases
hs = sorted([x for x in D.values() if x.get("hue") is not None and (x.get("sat") or 0) > .2], key=lambda x: x["hue"])
F["hue_strip"] = [{"thumb": hs[int(i * (len(hs) - 1) / 59)]["thumb"], "hue": hs[int(i * (len(hs) - 1) / 59)]["hue"]} for i in range(60)]
G = [g for f in sorted(glob.glob(os.path.join(os.path.dirname(LAB), "grounding", "g*.json"))) for g in json.load(open(f))]
dm = next(g for g in G if str(g["n"]) == "32"); F["phrases"] = dm.get("queries") or dm.get("search_queries") or []
F["nphrases"] = sum(len(g.get("queries") or g.get("search_queries") or []) for g in G)
json.dump(F, open(os.path.join(H, "film2.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(F["odyssey"]["line"]["text"], "->", F["odyssey"]["line"]["ans"]); print(F["captain"]); print(F["sheep"]); print(F["norse"]["line"]["text"], "->", F["norse"]["line"]["ans"])
print("republic", json.dumps(F["republic"])[:400]); print(F["takes"]["shared"], F["takes"]["sizes"])
