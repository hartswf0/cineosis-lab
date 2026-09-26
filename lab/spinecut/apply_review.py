"""Apply the sheet review to the clean cut: each reviewed row's chosen option replaces the machine's
pick, and its note travels with the section. A shot chosen twice keeps its first use; the later row
falls back to its machine pick. Updates spinecut-data.json in place (the blend pass is kept)."""
import glob, json, os
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, "spinecut-data.json"); D = json.load(open(P))
rows = {r["row"]: r for s in json.load(open(os.path.join(H, "sheets", "index.json"))) for r in s["rows"]}
rev = {}
for f in sorted(glob.glob(os.path.join(H, "review", "part-*.json"))): rev.update(json.load(open(f)))
seen, switched, missing, clash = set(), 0, 0, 0
for i, s in enumerate(D["sections"]):
    r = rows.get(i); o = rev.get(f"{s['id']}#{i}") or rev.get(s["id"]) if r else None
    s.setdefault("machine", s["clean"])
    if not o: missing += 1; seen.add(s["clean"]); continue
    opts = r["options"]; u = o.get("use", 0)
    pick = opts[u] if isinstance(u, int) and 0 <= u < len(opts) else opts[0]
    if pick in seen: pick, clash = s["machine"], clash + 1
    switched += pick != s["machine"]; s["clean"] = pick; s["note"] = o.get("note"); seen.add(pick)
json.dump(D, open(P, "w"), ensure_ascii=False, separators=(",", ":"))
print("reviewed", len(D["sections"]) - missing, "switched", switched, "clashes", clash, "unreviewed", missing, "distinct", len({s["clean"] for s in D["sections"]}))
