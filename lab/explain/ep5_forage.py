"""The CUTBASTARD forage as it happened (cutbastard/forage/search.log, search.json, run_all.log): every question with the second it
was asked, its kind (literal / oblique / place / mood), its chapter, and a few of the shots that came back; then the chain that
turned 4,460 answers into four films. Appends "laps" and "chain" to explain/ep/ep5.json.   usage: python3 lab/explain/ep5_forage.py"""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
S = json.load(open(os.path.join(LAB, "cutbastard/forage/search.json"))); E = json.load(open(os.path.join(H, "ep", "ep5.json")))
laps, t00 = [], None
for ln in open(os.path.join(LAB, "cutbastard/forage/search.log")):
    m = re.match(r"(\d\d):(\d\d):(\d\d) \[(\d+)/417\] (\w+)\s+ch(\d\d)\s+(\d+)\s+(.*)", ln.rstrip())
    if not m: continue
    t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]); t00 = t00 if t00 is not None else t
    qtext = m[8].strip(); key = next((k for k in S if k.startswith(qtext[:60])), None)
    clips = (S.get(key) or {}).get("clips", [])
    laps.append({"t": t - t00, "kind": m[5], "ch": m[6], "n": int(m[7]), "q": key or qtext, "th": [c["thumbnailUrl"] for c in clips[:4]]})
E["laps"] = laps
E["chain"] = [["24 Sep 18:03", "417 questions sent", "literal, oblique, place, and each chapter's moods"], ["18:35", "4,460 different shots came back", ""],
              ["18:41", "1,651 shortlisted", "the best matches for any of the four ways of asking"], ["18:42", "60 whole films fetched", "so a line could play as one film's consecutive shots"],
              ["", "1,731 clips watched", "three frames each, plus how much they move and whether they are dead or a title card"], ["19:20", "four films planned and rendered", "suite, scenes, cineosis, drift"]]
json.dump(E, open(os.path.join(H, "ep", "ep5.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(laps), "laps over", laps[-1]["t"], "s;", sum(1 for l in laps if l["th"]), "with thumbs;", {k: sum(1 for l in laps if l["kind"] == k) for k in ("literal", "oblique", "place", "mood")})
