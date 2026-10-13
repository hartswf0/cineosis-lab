"""EPISODE 5 · WHERE YOU GO WHEN YOU LEAVE — data, all from WYGWYL's own files.
  poem     the suite's timed lines (cues: start, duration, on-screen title) and its 14 parts
  takes    the four takes' shot lists on the poem's clock (169 patches each), where they agree, how many clips they share
  beats    the treatment's 88 beats on the same clock: what each asks the archive for, and its gap (what the archive could not give)
  search   one beat's real question and what came back
Writes explain/ep/ep5.json.   usage: python3 lab/explain/ep5.py"""
import json, os, itertools
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
W = J("wygwyl/WYGWYL_Forage_Catalogue.json"); CUT = {s["id"]: s for s in J("wygwyl/WYGWYL_Forage_Cut.json")["shots"]}; IDX = {w["slug"]: w for w in J("wygwyl/cuts/index.json")}
T = {t: J(f"wygwyl/cuts/{t}/patches.json") for t in ("suite", "scenes", "cineosis", "drift")}
out = {"poem": [{"t": c["start"], "d": c["duration"], "text": c["text"], "screen": c.get("screen")} for c in W["cues"]],
       "parts": [{"n": f["n"], "title": f["title"], "t": (f.get("poem") or f["container"])[0]} for f in W["films"]],
       "audio": "wygwyl/WYGWYL_Suite_Audio.mp3", "dur": W["duration"],
       "films": {t: IDX[t]["film"] for t in T}, "ideas": {t: IDX[t]["idea"] for t in T},
       "takes": {t: [[round(p["t0"], 2), round(p["t1"], 2), p["clip"]["thumb"], p["clip"]["title"], p["clip"]["id"][:8]] for p in T[t]] for t in T},
       "beats": [{"id": b["id"], "title": b["title"], "query": b["query"], "gap": b.get("gap"), "t0": CUT[b["id"]]["start"], "t1": CUT[b["id"]]["end"], "seq": b.get("sequence")} for b in W["beats"] if b["id"] in CUT],
       "scope": W["scope"]}
ids = {t: {p["clip"]["id"] for p in T[t]} for t in T}
out["shared"] = {f"{a}+{b}": len(ids[a] & ids[b]) for a, b in itertools.combinations(T, 2)}
out["agree"] = [i for i in range(len(T["suite"])) if len({T[t][i]["clip"]["id"] for t in T}) < 4]
b0 = W["beats"][0]; out["search"] = {"q": b0["query"], "beat": b0["title"], "hits": [{"thumb": c["thumb"], "title": c["title"], "year": c.get("year")} for c in W["catalogue"] if b0["query"] in (c.get("queries") or [])][:12]}
json.dump(out, open(os.path.join(H, "ep", "ep5.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out["poem"]), "lines;", len(out["parts"]), "parts;", out["shared"], "agree", len(out["agree"]))
print(out["poem"][0], out["poem"][1]["text"][:80]); print([ (b["id"], b["t0"], b["gap"][:60]) for b in out["beats"][:3]])
