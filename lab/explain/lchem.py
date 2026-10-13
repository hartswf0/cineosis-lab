"""NARRATIVE CHEMISTRY, ON TRIAL: the chemistry trials (chemistry/trials.json, TRIALS.md) as a film. The theory's compound for a
poem, the seven blind films per poem, the distances to the cut films, the four registered predictions and their verdicts, the
vacuity test, the one pattern the theory has no word for, and the isomer (same atoms, different order). Footage kept out of
examples is dropped from every strip. Writes explain/lesson/chem.json.   usage: python3 lab/explain/lchem.py"""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
T = J("chemistry/trials.json"); CP = J("chemistry/compounds.json"); K = J("bets/kernel-data.json")
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
ok = lambda s: not any(b in (s.get("title") or "").lower() for b in BLOCK)
def strip(p, g): return [{k: s.get(k) for k in ("title", "year", "thumb", "video", "in", "t0", "t1", "sg")} for s in p["films"][g] if ok(s)]
out = {k: T[k] for k in ("generators", "metrics", "verdicts", "vacuity", "adjacency", "tests")}
out["signs"] = {k: v["symbol"] for k, v in K["signs"].items()}; out["sign_names"] = {k: v["name"] for k, v in K["signs"].items()}
out["audio"] = "wygwyl/WYGWYL_Suite_Audio.mp3"
pick = []
for n in ("01", "07"):
    p = next(x for x in T["poems"] if x["n"] == n); c = next((x for x in CP if x["poem"] == n), {})
    pick.append({"n": n, "title": p["title"], "t0": p["t0"], "t1": p["t1"], "compound": p["blind_compound"], "natural": c.get("natural"), "films": {g: strip(p, g) for g in T["generators"]}})
out["poems"] = pick
json.dump(out, open(os.path.join(H, "lesson", "chem.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print({g: len(v) for g, v in pick[0]["films"].items()}, pick[0]["natural"]["name"], pick[1]["natural"]["name"] if pick[1]["natural"] else None)
print(out["metrics"]["d_trans"])
