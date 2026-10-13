"""Where every explorer shot comes from, and where it goes.
  films   each source film: title, year, maker, kind of maker, purpose (research/purpose.json), act, and its clips in the order
          they run in the film, so a shot can be seen among its neighbours in its own film
  used    for each shot, every one of OUR films that uses it: which film, where in it, what it was asked to do, and a link that
          opens that film at that place. New films only need a line in OURS and a census entry.
  text    (written to transcripts.json, loaded on demand) everything said in the shot, transcribed
usage: python3 lab/provenance.py   (after census/census.py)"""
import json, os, re, glob, collections
H = os.path.dirname(os.path.abspath(__file__)); J = lambda p: json.load(open(os.path.join(H, p)))
shots = J("lab-data.json")["shots"]; ids = {s["id"] for s in shots}
PUR = J("research/purpose.json")
# ---- our films: name, colour, and how to open each at a place
MUS = [sc["id"] for sc in J("odyssey/museum.json")["scenes"]]; NOR = [sc["id"] for sc in J("norse/program.json")["scenes"]]; ARC = list(J("republic/archive.json"))
OURS = {"Found Odyssey": ("The Odyssey", "#6f8cff", lambda w: f"found-odyssey-museum.html?scene={MUS.index(w) + 1}" if w in MUS else "found-odyssey-museum.html"),
        "Markov Odyssey": ("The Odyssey", "#6f8cff", lambda w: f"found-odyssey-museum.html?scene={MUS.index(w) + 1}" if w in MUS else "markov-odyssey.html"),
        "The Republic": ("The Republic", "#e0572a", lambda w: f"markov-republic.html#ep={int(w[2:])}" if w.startswith("EP") else "markov-republic.html"),
        "Found Republic": ("The Republic", "#e0572a", lambda w: f"markov-republic.html#ep={ARC.index(w) + 1}" if w in ARC else "markov-found-republic.html"),
        "Norse Half Moon": ("Norse Half Moon", "#6cc4d6", lambda w: f"norse-half-moon.html?scene={NOR.index(w) + 1}" if w in NOR else "norse-half-moon.html"),
        "WYGWYL": ("Where You Go When You Leave", "#c4f46a", lambda w: "wygwyl.html")}
def role(film, job):
    j = (job or "").strip()
    j = re.sub(r"^(WIDE|MID|CLOSE|OBJ|EMPTY|act|line|card|title|hold|montage|dissolve|split|inset|black)\s*:\s*", "", j, flags=re.I)
    j = re.sub(r"^establishing the place \| ", "", j); j = re.sub(r"^[A-Z .\-']+ says: ", "", j); j = j.split(" | ")[0]
    return j[:140]
used = collections.defaultdict(list)
for u in J("census/uses.json"):
    k = u.get("clip")
    if k not in ids or u["role"] == "word" or u["film"] not in OURS: continue
    name, col, link = OURS[u["film"]]; w = u.get("where") or ""
    row = [name, w, u["role"], role(u["film"], u.get("job")), link(w)]
    if row not in used[k] and len(used[k]) < 12: used[k].append(row)
# ---- source films, their clips in order
byslug = collections.defaultdict(list)
for s in shots: byslug[s["slug"]].append(s)
films = {}
for sl, ss in byslug.items():
    ss.sort(key=lambda s: s.get("start") or 0); p = PUR.get(sl, {})
    films[sl] = [p.get("title") or ss[0].get("title"), p.get("year") or ss[0].get("year"), p.get("sponsor"), p.get("kind"), p.get("purpose"), p.get("act"), [s["id"] for s in ss]]
json.dump({"ours": {k: [v[0], v[1]] for k, v in OURS.items()}, "films": films, "used": used}, open(os.path.join(H, "provenance.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# ---- everything said, transcribed
W = J("odyssey/cache/ears/words.json")
for f in glob.glob(os.path.join(H, "odyssey/cache/ears/words.*.json")): W.update(json.load(open(f)))
text = {k: (W[k].get("text") or " ".join(w[0] for w in W[k].get("words") or [])).strip() for k in ids if k in W and (W[k].get("words") or W[k].get("text"))}
text = {k: v for k, v in text.items() if len(v.split()) >= 3}
json.dump(text, open(os.path.join(H, "transcripts.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# ---- every word with when it is said, on the clip's own clock (for the inspector's time track)
words = {k: [[w[0], round(w[1], 2)] for w in (W[k].get("words") or [])] for k in text}
json.dump(words, open(os.path.join(H, "words.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(films), "source films ·", len(used), "shots used by our films ·", len(text), "transcribed ·",
      os.path.getsize(os.path.join(H, "provenance.json")) // 1024, "KB +", os.path.getsize(os.path.join(H, "transcripts.json")) // 1024, "KB")
