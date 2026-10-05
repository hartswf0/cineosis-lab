"""Small decks for the Party games that grew out of the Wes Anderson cinema and the Monte Carlo cinema.
  wes.json      the eight chapters of the Wes Anderson cineosis (symmetry, facing, pastel, overhead, diorama, uniform, title,
                compartment), sixty shots each: clip, length, film, year, and the measures (Anderson score, symmetry, pastel);
                the strict judge's score and words where it looked at the shot
  monte-v.json  clip paths for the material's spoken lines and music (the shots carry their own), so the Monte Carlo games
                need not load the whole video index
usage: python3 lab/party/build_decks.py"""
import json, os, re
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D)
J = lambda *p: json.load(open(os.path.join(L, *p)))
V = J("aspect", "video.json"); W = J("wes", "wes.json"); M = J("monte", "material.json")
judged = {x["id"]: x for x in J("wes", "judge", "judged.json") if x.get("id")}
P = []
def pack(path):
    m = re.fullmatch(r"(.+)/clips/([^/]+)\.mp4", path)
    if not m: return path
    if m.group(1) not in P: P.append(m.group(1))
    return [P.index(m.group(1)), m.group(2)]
NAMES = {"symmetry": "Symmetry", "facing": "Facing the camera", "pastel": "Pastel", "overhead": "From above", "diorama": "The diorama", "uniform": "Uniforms", "title": "Title cards", "compartment": "Compartments"}
ch = {}
for k, xs in W["chapters"].items():
    out = []
    for x in xs:
        if x["id"] not in V: continue
        j = judged.get(x["id"], {})
        out.append({"v": pack(V[x["id"]][0]), "d": round(V[x["id"]][1] or 4, 1), "f": x.get("title") or "", "y": x.get("year"), "a": round(x.get("score") or 0, 2), "sym": x.get("sym"), "pas": x.get("pastel"), "js": j.get("score"), "jw": j.get("why")})
    ch[k] = {"name": NAMES.get(k, k), "shots": out}
R2 = M["r2"]
json.dump({"r2": R2, "P": P, "chapters": ch}, open(os.path.join(D, "wes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
mv = {x["i"]: V[x["i"]][0] for x in M["lines"] + M["music"] if x["i"] in V}
json.dump(mv, open(os.path.join(D, "monte-v.json"), "w"), separators=(",", ":"))
print({k: len(v["shots"]) for k, v in ch.items()}, round(os.path.getsize(os.path.join(D, "wes.json")) / 1e3), "KB ·", len(mv), "lines+music", round(os.path.getsize(os.path.join(D, "monte-v.json")) / 1e3), "KB")
