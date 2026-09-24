"""Pool search results into a diverse candidate set per sign + a vetting contact sheet.

Round-robin across a sign's queries by rank, at most one shot per source film,
up to POOL candidates. Writes candidates.json and contact.html (letters A.. per sign).
"""
import glob, json, os, string

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = 18

def skey(n):
    s = str(n); d = "".join(c for c in s if c.isdigit())
    return (int(d), s[len(d):])

def load_signs():
    signs = []
    for f in sorted(glob.glob(os.path.join(HERE, "grounding", "g*.json"))):
        signs += json.load(open(f))
    return sorted(signs, key=lambda s: skey(s["n"]))

def pool(sign):
    path = os.path.join(HERE, "results", f"{sign['n']}.json")
    if not os.path.exists(path):
        return []
    res = json.load(open(path))
    lists = [(qi, q, res.get(q, [])) for qi, q in enumerate(sign["queries"])]
    seen_films, seen_ids, out = set(), set(), []
    for rank in range(15):
        for qi, q, clips in lists:
            if rank >= len(clips) or len(out) >= POOL:
                continue
            c = clips[rank]
            film = c["sourceSlug"] or c["sourceTitle"]
            if c["id"] in seen_ids or film in seen_films:
                continue
            seen_ids.add(c["id"]); seen_films.add(film)
            out.append({**c, "query": q, "qi": qi, "rank": rank})
    return out

def main():
    signs = load_signs()
    cands = {str(s["n"]): pool(s) for s in signs}
    json.dump(cands, open(os.path.join(HERE, "candidates.json"), "w"), indent=1)
    rows = []
    for s in signs:
        cells = "".join(
            f'<figure><img loading="lazy" src="{c["thumbnailUrl"]}"><figcaption><b>{string.ascii_uppercase[i]}</b> q{c["qi"]} {(c["sourceTitle"] or "")[:22]}</figcaption></figure>'
            for i, c in enumerate(cands[str(s["n"])]))
        rows.append(f'<section id="s{s["n"]}"><h2>{s["n"]} {s["name"]}</h2><p>{s.get("shot_criteria","")}</p><div class="g">{cells}</div></section>')
    html = """<!doctype html><meta charset=utf-8><title>contact</title><style>
body{background:#111;color:#ddd;font:12px monospace;margin:8px}h2{font-size:18px;margin:10px 0 2px}p{margin:0 0 4px;color:#999;max-width:1400px}
.g{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:4px}figure{margin:0;min-width:0}img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#000}
figcaption{white-space:nowrap;overflow:hidden}b{font-size:15px;color:#fc6}</style>""" + "".join(rows)
    open(os.path.join(HERE, "contact.html"), "w").write(html)
    print({n: len(c) for n, c in cands.items()})

if __name__ == "__main__":
    main()
