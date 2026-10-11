"""MARKOV SAM · REPUBLIC: the page. Inlines the screenplay, the art direction, the planes and the voices into republic/template.html
and writes lab/markov-sam-republic.html (one file, nothing to wait for but the pictures and the sound).   usage: python3 republic/make_page.py"""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
S = json.load(open(os.path.join(H, "script.json"))); W = json.load(open(os.path.join(H, "world.json")))
P = json.load(open(os.path.join(H, "planes.json"))); [P["episodes"].update(json.load(open(os.path.join(H, f)))["episodes"]) for f in ("planes-eps.json", "planes-eps2.json") if os.path.exists(os.path.join(H, f))]; V = json.load(open(os.path.join(H, "voices.json")))
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
scores = {f[:-4]: f"republic/score/{f}" for f in os.listdir(os.path.join(H, "score")) if f.endswith(".m4a")}
def score(name):
    s = slug(name); return next((v for k, v in scores.items() if k.startswith(s)), None)
def trim(x, keys): return {k: x[k] for k in keys if k in x}
eps = []
for e in S["episodes"]:
    pe = P["episodes"].get(e["id"]); vo = V.get(e["id"])
    if not pe or not vo or not any(p["alts"] for p in pe["places"]): print("skip", e["id"], e["name"], "(planes or voices not built)"); continue
    ew = W["episodes"][e["id"]]
    places = [{"q": p["q"], "alts": [trim(a, ("f", "title", "year", "video", "t", "cover")) for a in p["alts"]]} for p in pe["places"] if p["alts"]]
    eps.append({"id": e["id"], "name": e["name"], "series": e.get("series", ""), "genre": e["genre"], "logline": e["logline"], "slug": e["slug"], "witness": e["witness"],
                "grade": ew["grade"], "score": score(ew.get("score", "")), "places": places, "prop": trim(pe["prop"], ("f", "w", "h", "cut", "title", "year")) if pe.get("prop") else None,
                "beats": [trim(b, ("k", "who", "how", "text")) for b in e["beats"]], "voice": vo, "alias": W["alias"]})
ver = lambda f: f"{f}?v={int(os.path.getmtime(os.path.join(L, f))) % 100000}" if os.path.exists(os.path.join(L, f)) else f   # a re-cut figure is fetched fresh
cast = {n: [dict(trim(f, ("f", "w", "h", "cut", "feet", "title", "year", "video", "t", "sp")), f=ver(f["f"]), **({"sp": dict(f["sp"], f=ver(f["sp"]["f"]))} if f.get("sp") else {})) for f in fs] for n, fs in P["cast"].items() if fs}
D = {"eps": eps, "cast": cast, "castInfo": {n: trim(c, ("as", "voice", "robot")) for n, c in W["cast"].items()}, "grades": W["grades"], "source": S["source"]}
page = open(os.path.join(H, "template.html")).read().replace("{{DATA}}", json.dumps(D, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(L, "markov-sam-republic.html"), "w").write(page)
print(len(eps), "episodes ·", len(cast), "cast ·", len(page) // 1024, "KB")
# ---- the found page: the archive's own moving pictures and sound (republic/found.json from found.py)
FJ = os.path.join(H, "found.json")
if os.path.exists(FJ):
    F = json.load(open(FJ)); feps = []
    for e in eps:
        f = F.get(e["id"])
        if not f: continue
        places = [p for p in f["places"] if p["v"]]
        feps.append({k: e[k] for k in ("id", "name", "series", "genre", "logline", "grade", "score", "beats", "voice")} |
                    {"answers": {int(k): v for k, v in f["answers"].items()}, "places": places, "thumb": e["places"][0]["alts"][0]["f"] + "_thumb.jpg", "alias": W["alias"],
                     "cast": list(dict.fromkeys(W["alias"].get(c, c) for c in next(x for x in S["episodes"] if x["id"] == e["id"])["cast"]))})
    page = open(os.path.join(H, "found-template.html")).read().replace("{{DATA}}", json.dumps({"eps": feps, "grades": W["grades"], "cast": {n: fs[:1] for n, fs in cast.items()}}, ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(L, "markov-found-republic.html"), "w").write(page)
    print("found:", len(feps), "episodes ·", len(page) // 1024, "KB")
