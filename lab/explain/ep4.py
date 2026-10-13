"""Data for EPISODE 1's 'how a question is made' and EPISODE 4 · THE ODYSSEY. Everything from the projects' own files.
  howq     the sign Demark: its definition (after Deamer), the eight scenes written for it, one request to the archive's search
           and its real answer, the contact sheet of 18 candidates with the editor's kept shots; a CUTBASTARD cue asked three ways
  odyssey  152 scenes; one scene's spec (world, roles, queries) and what two of its questions brought back; the critic's verdict;
           scenes to play with their audio, pictures and lines; the sheep's two jobs
Writes explain/ep/ep4.json and adds "howq" to explain/ep/ep1.json.   usage: python3 lab/explain/ep4.py"""
import json, os, glob
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); ROOT = os.path.dirname(LAB); J = lambda p: json.load(open(os.path.join(LAB, p)))
D = J("lab-data.json"); by = {s["id"]: s for s in D["shots"]}
G = [g for f in sorted(glob.glob(os.path.join(ROOT, "grounding", "g*.json"))) for g in json.load(open(f))]; dm = next(g for g in G if str(g["n"]) == "32")
res = json.load(open(os.path.join(ROOT, "results/32.json"))); q0 = "flock of white sheep with a single black sheep in the middle"
cand = json.load(open(os.path.join(ROOT, "candidates.json")))["32"]; picks = {p[0] for p in json.load(open(os.path.join(ROOT, "picks.json")))["32"]}
CQ = J("cutbastard/queries.json")["cues"][0]
howq = {"sign": {"n": "32", "name": dm["name"], "symbol": dm["symbol"], "definition": dm["definition"], "quote": dm.get("deamer_quote"), "operation": dm.get("operation"), "queries": dm["queries"]},
        "request": q0, "response": [{k: r.get(k) for k in ("sourceTitle", "sourceYear", "startSeconds", "endSeconds", "matchTimestampSeconds", "score")} for r in res[q0][:4]],
        "first": {"video": res[q0][0]["videoUrl"], "t": round(res[q0][0]["matchTimestampSeconds"] - res[q0][0]["startSeconds"], 2), "title": res[q0][0]["sourceTitle"]},
        "sheet": [{"thumb": by[c["id"]]["thumb"] if c["id"] in by else c["thumbnailUrl"], "kept": c["id"] in picks, "title": c["sourceTitle"], "q": c["query"]} for c in cand],
        "cue": CQ, "total_signs": 45, "asked": 352, "kept_per_q": 15, "unique": 4788}
E1 = json.load(open(os.path.join(H, "ep", "ep1.json"))); E1["howq"] = howq; json.dump(E1, open(os.path.join(H, "ep", "ep1.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# ---- the Odyssey
M = J("odyssey/museum.json"); SC = {s["id"]: s for s in M["scenes"]}
qq = {}
for f in glob.glob(os.path.join(LAB, "odyssey/src/q_b*.json")): qq.update(json.load(open(f)))
spec = {}
for f in glob.glob(os.path.join(LAB, "odyssey/src/q_spec_b*.json")): spec.update(json.load(open(f)))
raw = J("odyssey/results/raw.json"); cap = {}
for f in glob.glob(os.path.join(LAB, "odyssey/cache/steer/captain_*.json")): cap.update(json.load(open(f)))
def scene(k, lines):
    s = SC[k]; return {"id": k, "book": s["bnum"] if "bnum" in s else s["book"], "title": s["title"], "card": s["card"], "audio": s["audio"], "dur": s["dur"],
                       "pics": [{"sw": p["sw"], "video": p["video"], "in": p.get("in", 0), "rate": p.get("rate", 1)} for p in s["pics"]],
                       "lines": [{k2: s["lines"][i].get(k2) for k2 in ("at", "end", "text", "who", "ans", "aat", "aend", "src", "sc")} for i in lines]}
k0 = "OD-B01-S01"; sp = spec[k0]
O = {"count": {"scenes": len(SC), "lines": sum(len(s["lines"]) for s in SC.values()), "questions": sum(len(v) for v in raw.values()) and len(raw), "clips": 28611, "films": 1795},
     "scenes": [{"id": s["id"], "book": s.get("bnum"), "title": s["title"], "thumb": s.get("thumb")} for s in M["scenes"]],
     "spec": {"id": k0, "title": SC[k0]["title"], "card": SC[k0]["card"], "world": sp.get("world"), "roles": qq[k0], "shots": [{"role": x["role"], "see": x["see"], "q": x["q"]} for b in sp["beats"] for x in b["shots"]][:4]},
     "answers": {q: [{"thumb": c["thumbnailUrl"], "title": c["sourceTitle"], "year": c.get("sourceYear")} for c in raw[q][:12]] for q in (qq[k0]["ground"][0], qq[k0]["action"][0])},
     "captain": {"asks": cap[k0]["asks"], "diagnosis": cap[k0]["diagnosis"], "shots": [{k2: x.get(k2) for k2 in ("seen", "verdict", "why", "conf")} for x in cap[k0]["shots"][:3]], "coherence": cap[k0].get("coherence")},
     "captain22": {"asks": cap["OD-B22-S01"]["asks"], "diagnosis": cap["OD-B22-S01"]["diagnosis"][:2]},
     "play": [scene(k0, [0]), scene("OD-B09-S09", [0, 1, 2]), scene("OD-B11-S01", [0]), scene("OD-B12-S03", [0]), scene("OD-B22-S01", [0])],
     "sheep": {"video": by["21171e70-f59f-55b6-85c3-29691c97e312"]["video"], "uses": ["men crouched among sheep, faces pressed into wool", "sheep led to the trench's edge"]},
     "found_clips": len(J("odyssey/found.json").get("modes", {}).get("spoken", {}).get("frags", []) or [])}
json.dump(O, open(os.path.join(H, "ep", "ep4.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(O["count"], O["found_clips"]); print(O["spec"]["world"]); print([ (p["title"], [l["text"][:30] + " -> " + (l["ans"] or "")[:30] for l in p["lines"]]) for p in O["play"]])
print(howq["sign"]["definition"][:150]); print(sum(1 for c in howq["sheet"] if c["kept"]), "kept of", len(howq["sheet"]))
