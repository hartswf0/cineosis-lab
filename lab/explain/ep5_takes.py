"""WYGWYL, take by take: for every patch of each take, the shot and the evidence that take used to choose it.
  suite     the treatment's beat for that moment: its title, the operation it asks for, its gap, its edit note, the forager's search,
            and whether the chosen shot was one the forager reviewed (and what they saw in it)
  scenes    the source film the passage comes from, and where the shot sits in that film's own order (shot k of n)
  cineosis  the beat's signs, each with its question, and how strongly the chosen shot carries them (machine affinity)
  drift     how alike the shot is to the one before it (CLIP on three watched frames), and the chapter mood it drifted toward
Also per take: a passage to watch whole, its weakest matches, and how many films and colour/black-and-white switches it uses.
Writes explain/ep/takes.json.   usage: python3 lab/explain/ep5_takes.py"""
import json, os, glob
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
D = J("lab-data.json"); by = {s["id"]: s for s in D["shots"]}; SG = {s["n"]: s for s in D["signs"]}
cat = J("wygwyl/WYGWYL_Forage_Catalogue.json"); beats = {b["id"]: b for b in cat["beats"]}
P = {p["id"]: p for p in J("cutbastard/patches.json")["patches"]}; q = J("cutbastard/queries.json"); mood = {c["n"]: c["mood"] for c in q["chapters"]}
srcs = {}
for f in glob.glob(os.path.join(LAB, "cutbastard/forage/sources/*.json")):
    d = json.load(open(f)); srcs[d["slug"]] = [c["id"] for c in d["clips"]]
def watched(i):
    p = os.path.join(LAB, "cache/watch", i + ".json"); return json.load(open(p)) if os.path.exists(p) else None
parts = [{"n": f["n"], "title": f["title"], "t0": (f.get("poem") or f["container"])[0], "t1": (f.get("poem") or f["container"])[1]} for f in cat["films"]]
WATCH = {"suite": "01", "scenes": "06", "cineosis": "10", "drift": "14"}
out = {"parts": parts}
for t in ("suite", "scenes", "cineosis", "drift"):
    rows, prev = [], None
    for p in J(f"wygwyl/cuts/{t}/plan.json")["patches"]:
        c = p["clip"]; s = by.get(c["id"]) or {}; w = watched(c["id"]); pp = P.get(p["id"], {})
        r = {"id": p["id"], "t0": p["t0"], "t1": p["t1"], "ch": p["chapter"], "film": p["film"], "title": c["title"], "year": c.get("year"), "thumb": c["thumb"], "in": c["in"],
             "why": p["why"], "match": p["match"], "line": p["line"], "bw": s.get("hue") is None, "src": c.get("source")}
        b = beats.get(p["beat"]) or {}
        if t == "suite":
            rev = next((x for x in b.get("candidates", []) if x["id"] == c["id"]), None)
            r["beat"] = {"title": b.get("title"), "operation": b.get("operation"), "gap": b.get("gap"), "edit": b.get("edit"), "query": b.get("query")}
            r["review"] = {"grade": rev.get("grade"), "observed": rev.get("observed")} if rev else None
        if t == "scenes":
            lst = srcs.get(c.get("source")) or []; r["pos"] = [lst.index(c["id"]) + 1, len(lst)] if c["id"] in lst else None
        if t == "cineosis":
            r["signs"] = [{"n": n, "sym": SG[n]["symbol"], "name": SG[n]["name"], "q": SG[n].get("question"), "dom": SG[n]["dom"], "aff": round(((s.get("affinity") or {}).get(n) or 0), 1)} for n in p["codes"] if n in SG]
        if t == "drift":
            e = np.array(w["emb"]) if w else None
            r["follow"] = round(float(e @ prev), 3) if (e is not None and prev is not None) else None
            ms = mood.get(p["chapter"], []); r["mood"] = ms[(pp.get("k", 0) + pp.get("segment", 0)) % len(ms)] if ms else None
            prev = e / np.linalg.norm(e) if e is not None else prev
            if e is not None: prev = e / np.linalg.norm(e)
        rows.append(r)
    flips = sum(1 for a, b in zip(rows, rows[1:]) if a["bw"] != b["bw"])
    wk = sorted([r for r in rows if r["why"] != "scene: consecutive shot"], key=lambda r: r["match"])[:3]
    out[t] = {"rows": rows, "films": len({r["src"] for r in rows}), "flips": flips, "mean": round(float(np.mean([r["match"] for r in rows])), 3), "weak": [r["id"] for r in wk], "watch": WATCH[t]}
    print(t, "films", out[t]["films"], "flips", flips, "mean match", out[t]["mean"], "weakest", [(r["title"][:20], r["match"]) for r in wk])
# scenes: the runs inside their own films, with the shots around them
full = {}
for f in glob.glob(os.path.join(LAB, "cutbastard/forage/sources/*.json")):
    d = json.load(open(f)); full[d["slug"]] = {"title": (d.get("title") or d["slug"]), "clips": [(c["id"], c.get("thumbnailUrl")) for c in d["clips"]]}
runs, cur = [], None
for r in out["scenes"]["rows"]:
    if r["ch"] != WATCH["scenes"] or not r["pos"]: continue
    if cur and cur["src"] == r["src"] and r["pos"][0] == cur["k1"] + 1: cur["k1"] = r["pos"][0]
    else: cur = {"src": r["src"], "k0": r["pos"][0], "k1": r["pos"][0]}; runs.append(cur)
strips = []
for ru in runs[:4]:
    fl = full.get(ru["src"]); 
    if not fl: continue
    a, b = max(1, ru["k0"] - 6), min(len(fl["clips"]), ru["k1"] + 6)
    strips.append({"src": ru["src"], "title": fl["title"], "n": len(fl["clips"]), "k0": ru["k0"], "k1": ru["k1"], "a": a, "thumbs": [fl["clips"][i - 1][1] for i in range(a, b + 1)]})
out["scenes"]["strips"] = strips
json.dump(out, open(os.path.join(H, "ep", "takes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("drift follow:", [r["follow"] for r in out["drift"]["rows"][:8]]); print("scenes pos:", [r["pos"] for r in out["scenes"]["rows"][:6]])
print("suite review:", sum(1 for r in out["suite"]["rows"] if r["review"]), "reviewed of 169"); print([ (p["n"], p["title"], round(p["t0"]), round(p["t1"])) for p in parts])
