"""The sign families for the films: each family (domain) of Deamer's table, its signs, and the read shots of each sign (thumb, clip,
reading), so a film can show a family by its images. Appends "families" to explain/film.json.   usage: python3 lab/explain/families.py"""
import json, os, collections
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); D = json.load(open(os.path.join(LAB, "lab-data.json")))
F = json.load(open(os.path.join(H, "film.json"))); by = collections.defaultdict(list)
for s in D["shots"]:
    for e in s.get("signs") or []:
        by[str(e["n"])].append({"id": s["id"], "thumb": s["thumb"], "video": s.get("video"), "t": s.get("read_t") or 0, "title": s["title"], "note": e.get("note"), "conf": e.get("conf") or 0})
NAMES = {"perception": "The perception-image", "affect": "The affection-image", "action": "The action-image", "reflection": "The reflection-image", "mental": "The mental image", "break": "Opsigns and sonsigns", "time": "The time-image", "read": "The lectosign"}
fam = []
for dom in dict.fromkeys(s["dom"] for s in D["signs"]):
    signs = [s for s in D["signs"] if s["dom"] == dom]
    fam.append({"dom": dom, "name": NAMES.get(dom, dom), "signs": [{"n": s["n"], "symbol": s["symbol"], "name": s["name"], "question": s.get("question"),
                "shots": sorted(by[str(s["n"])], key=lambda x: -x["conf"])[:4]} for s in signs]})
F["families"] = fam; json.dump(F, open(os.path.join(H, "film.json"), "w"), ensure_ascii=False, separators=(",", ":"))
for f in fam: print(f["dom"], f["name"], len(f["signs"]), sum(len(s["shots"]) for s in f["signs"]))
