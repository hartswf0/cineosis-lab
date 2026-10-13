"""THE RECURRING CAST, filmed: the census of six lab films (census/census.json, census/operations.json): one clip given many jobs,
the sources used most, the jobs archive shots are asked to do, the signs no film used, whose voices are heard and from when.
Footage kept out of examples (a birth film, assassination evidence, one children's film) is dropped from every list.
Writes explain/lesson/cast.json.   usage: python3 lab/explain/lcast.py"""
import json, os
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
C = J("census/census.json"); O = J("census/operations.json"); K = J("bets/kernel-data.json")
BLOCK = ("all my babies", "jfk exhibit", "kinderen naar buiten")
ok = lambda t: not any(b in (t or "").lower() for b in BLOCK)
out = {k: C[k] for k in ("films", "n_uses", "n_words", "n_sources", "n_clips", "per_film", "multi_role")}
out["n_archive"] = O["n_archive"]; out["job_baseline"] = O["job_baseline"]; out["kinds_by_film"] = {f: v[:5] for f, v in O["kinds_by_film"].items()}
out["same_clip"] = [c for c in O["same_clip"] if ok(c["title"])][:6]
out["sources"] = [{k: s.get(k) for k in ("title", "year", "uses", "nfilms", "films", "roles", "thumb", "top_video", "said")} for s in C["sources"] if ok(s["title"])][:30]
out["recurring"] = [r for r in O["recurring"] if ok(r["title"])][:8]
out["never_signs"] = O["never_signs"]; out["signs"] = {k: v for k, v in K["signs"].items()}
out["voice_sex"] = O["voice_sex"]; out["voice_want"] = O["voice_want"]; out["decades_heard"] = O["decades_heard"]
out["types"] = sorted([t for t in O["types"] if t["pool"] >= .004], key=lambda t: -t["ratio"])
json.dump(out, open(os.path.join(H, "lesson", "cast.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(out["n_uses"], out["n_sources"], out["n_clips"], "| same-clip", [c["title"] for c in out["same_clip"]]); print("top", [(s["title"], s["uses"], s["nfilms"]) for s in out["sources"][:8]])
print("never", len(out["never_signs"]), out["never_signs"][:6]); print("types", [(t["type"], t["ratio"]) for t in out["types"][:4]], [(t["type"], t["ratio"]) for t in out["types"][-4:]])
print("decades", list(out["decades_heard"].items())[:6]); print("multi", [(m["title"], m["plays"]) for m in out["multi_role"]][:5])
