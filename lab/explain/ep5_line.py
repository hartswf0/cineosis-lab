"""One line, four ways: the curtains line's own time in the poem (its cue), each take's shots across that time (where its cuts fall),
and, for the cineosis take, the beat's signs with their questions and how strongly each chosen shot carries them (machine affinity),
plus any reader's reading the shot has. Appends "line" to explain/ep/ep5.json.   usage: python3 lab/explain/ep5_line.py"""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
E = json.load(open(os.path.join(H, "ep", "ep5.json"))); D = J("lab-data.json"); by = {s["id"]: s for s in D["shots"]}; SG = {s["n"]: s for s in D["signs"]}
cue = next(c for c in E["poem"] if c["text"].lower().startswith("curtains"))
t0, t1 = cue["t"], cue["t"] + cue["d"]; out = {"t0": t0, "t1": t1, "text": cue["text"], "takes": {}}
for t in ("suite", "scenes", "cineosis", "drift"):
    P = J(f"wygwyl/cuts/{t}/plan.json")["patches"]; rows = []
    for p in P:
        if p["t1"] > t0 and p["t0"] < t1:
            c = p["clip"]; s = by.get(c["id"]) or {}
            rows.append({"t0": p["t0"], "t1": p["t1"], "title": c["title"], "year": c.get("year"), "thumb": c["thumb"], "why": p["why"], "codes": p["codes"], "match": p["match"], "in": c["in"],
                         "aff": {n: round(((s.get("affinity") or {}).get(n) or 0), 1) for n in p["codes"]}, "aff_top": (s.get("aff_top") or [])[:3],
                         "read": [{"n": e["n"], "note": e["note"]} for e in (s.get("signs") or [])]})
    out["takes"][t] = rows
codes = list(dict.fromkeys(c for r in out["takes"]["cineosis"] for c in r["codes"]))
out["signs"] = [{"n": n, "symbol": SG[n]["symbol"], "name": SG[n]["name"], "question": SG[n].get("question"), "dom": SG[n]["dom"]} for n in codes if n in SG]
E["line"] = out; json.dump(E, open(os.path.join(H, "ep", "ep5.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(t0, t1, cue["text"][:60]); print({k: [(r["title"][:22], round(r["t0"], 1), r["aff"]) for r in v] for k, v in out["takes"].items()}); print(out["signs"])
