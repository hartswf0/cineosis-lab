"""THE SEA OF TAKES — every alternative of every shot, as one lattice per film (the Found Odyssey's build_cuts.py idea, made visible):
a column per shot in program order, each holding the film's choice plus its alternatives. Views: the story cut (pickups, archive memories,
bridges) and each song's CUTBASTARD film (its raw-v2 cut list in edits/). AI-only is a filter the page applies to any view.
Per take: a 32-d PCA of its CLIP vector (the page scores any join live, as monte/sim.js scores a cut: a Gaussian of cosine around .72,
calibrated back to full cosine), 'same' (likeness to the shot it would replace), 'sym' (mirror symmetry of edges, after wes/score.py),
poison, its flipbook (sprites/: 12 frames, for scrubbing a take at deep zoom), the playable source.
Writes lattice/<view>.json + lattice/index.json (slopfeeder-takes.html, party/games/sea.js).   usage: .venv/bin/python slopfeeder/lattice.py"""
import json, os, io, glob, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); OUTD = os.path.join(D, "lattice"); os.makedirs(OUTD, exist_ok=True)
C = json.load(open(os.path.join(D, "atlas.json")))["cards"]; E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(len(C), -1).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
IX = {c["id"]: i for i, c in enumerate(C)}; AI = [i for i, c in enumerate(C) if c["type"] == "ai"]; AR = [i for i, c in enumerate(C) if c["type"] == "archive"]
FA = {c["id"]: c.get("fa") for c in json.load(open(os.path.join(D, "field.json")))["cards"]}; SP = json.load(open(os.path.join(D, "sprites.json")))["at"]
AP = np.load(os.path.join(D, "src", "archpool.npy")).astype(np.float32); APR = json.load(open(os.path.join(D, "src", "archpool.json"))); APX = {r["id"]: i for i, r in enumerate(APR)}
thumb_url = lambda v: v.replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg")
def img(src):
    try:
        if src.startswith("http"): return Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(src, headers={"User-Agent": "cineosis-44-research"}), timeout=20).read()))
        return Image.open(os.path.join(D, src))
    except Exception: return None
def sym(im):   # mirror symmetry of the edges (1 = a perfectly centred, Andersonian frame)
    if im is None: return 0.0
    g = np.asarray(im.convert("L").resize((64, 36)), np.float32); e = np.abs(np.diff(g, axis=1))[:35, :62] + np.abs(np.diff(g, axis=0))[:, :62]
    return float(max(0.0, 1 - np.abs(e - e[:, ::-1]).mean() / (e.mean() + 1e-6)))
def card_take(i, same):
    c = C[i]; t = {"id": c["id"], "kind": "ai" if c["type"] == "ai" else "archive", "same": round(float(same), 3), "poison": round(c.get("poison") or 0, 2), "_v": E[i]}
    if c["type"] == "ai": t.update(clip=c["clip"], ss=round(c["in"], 2), out=round(c["out"], 2), thumb=c["thumb"])
    else: t.update(v=c["media"], ss=None, title=c.get("title"), year=c.get("year"), thumb=c["thumb"])
    if c["id"] in SP: t["sp"] = SP[c["id"]]
    return t
def ai_takes(me, ss=None, extra_out=None):   # the shot, then the other generations nearest to it (same field family first)
    sim = E[AI] @ E[me]; fam = FA.get(C[me]["id"]); out = [card_take(me, 1.0)]
    if ss is not None: out[0]["ss"] = ss
    if extra_out: out[0]["out"] = extra_out
    for j in sorted(range(len(AI)), key=lambda j: -(sim[j] + (.08 if fam and FA.get(C[AI[j]]["id"]) == fam else 0))):
        c = C[AI[j]]
        if AI[j] == me or (c.get("out", 0) - c.get("in", 0)) < 1.2 or sim[j] < .70: continue
        if any(o.get("clip") == c["clip"] and abs(o["ss"] - c["in"]) < 1 for o in out): continue
        out.append(card_take(AI[j], sim[j]))
        if len(out) == 11: break
    return out
def ar_takes(me):   # an archive shot, then the archive nearest to it (and its bridges)
    sim = E[AR] @ E[me]; out = [card_take(me, 1.0)]; seen = {(C[me].get("title") or "")[:16]}
    for j in np.argsort(-sim):
        c = C[AR[j]]; f = (c.get("title") or "")[:16]
        if AR[j] == me or f in seen or sim[j] < .70: continue
        seen.add(f); out.append(card_take(AR[j], sim[j]))
        if len(out) == 9: break
    return out
def pool_takes(cands):   # archive candidates from the whole pool (the story cut's hand-picked memories and bridges)
    out, base = [], None
    for r in cands[:10]:
        if r["id"] not in APX: continue
        v = AP[APX[r["id"]]]; base = v if base is None else base
        t = {"id": r["id"], "kind": "archive", "v": r["v"], "ss": None, "title": r["title"], "year": r.get("year"), "thumb": thumb_url(r["v"]), "same": round(float(v @ base), 3), "poison": 0, "_v": v}
        if r["id"] in IX and r["id"] in SP: t["sp"] = SP[r["id"]]
        out.append(t)
    return out
def finish(name, title, video, dur, program, cols, offset=0.0):
    allc = [x for c in cols for x in c["cands"]]; V = np.stack([x["_v"] for x in allc]); V /= np.linalg.norm(V, axis=1, keepdims=True); mu = V.mean(0)
    _, _, Wt = np.linalg.svd(V - mu, full_matrices=False); P = (V - mu) @ Wt[:32].T; P /= np.linalg.norm(P, axis=1, keepdims=True) + 1e-9
    with cf.ThreadPoolExecutor(16) as ex: syms = list(ex.map(lambda x: sym(img(x["thumb"])), allc))
    for x, p, sy in zip(allc, P, syms): x["e"] = [int(round(v * 127)) for v in p]; x["sym"] = round(sy, 3); del x["_v"]
    pr = np.random.default_rng(0).integers(0, len(allc), (4000, 2)); a, b = np.polyfit((P[pr[:, 0]] * P[pr[:, 1]]).sum(1), (V[pr[:, 0]] * V[pr[:, 1]]).sum(1), 1)
    J = {"id": name, "title": title, "video": video, "dur": round(dur, 2), "offset": offset, "program": program, "cal": [round(float(a), 4), round(float(b), 4)], "sprites": {"fw": 128, "fh": 72, "nf": 12, "path": "slopfeeder/sprites/s%03d.jpg"}, "cols": cols}
    json.dump(J, open(os.path.join(OUTD, name + ".json"), "w"), separators=(",", ":"))
    print(f"{name:8s} {len(cols):4d} shots · {len(allc):5d} takes · {sum(c['kind'] == 'ai' for c in cols)} AI", flush=True)
    return {"id": name, "title": title, "n": len(cols), "takes": len(allc), "dur": round(dur, 1)}
index = []
# ---- the story cut
ST = json.load(open(os.path.join(D, "story.json"))); ARC = json.load(open(os.path.join(D, "story-archive.json"))); CANDS = json.load(open(os.path.join(D, "story-archive-cands.json")))
key_of = {r["v"]: k for k, r in ARC.items()}; key_by_title = {r["title"]: k for k, r in ARC.items()}; cols = []
for s in ST["shots"]:
    if s["kind"] == "ai":
        own = [i for i in AI if C[i]["clip"] == s["clip"]]; me = min(own, key=lambda i: abs((C[i].get("in") or 0) - s["ss"]) if (C[i].get("in") or 0) <= s["ss"] + .1 else 99)
        cols.append({"t": s["t"], "d": s["d"], "act": s["act"], "cap": s.get("cap", ""), "kind": "ai", "hold": bool(s.get("cap") or s.get("poison")), "poison": s.get("poison", False), "cands": ai_takes(me, s["ss"], round(s["ss"] + s["d"] * s.get("rate", 1) + 3, 2))})
    else:
        k = key_of.get(s["v"]); cols.append({"t": s["t"], "d": s["d"], "act": None, "cap": "", "kind": "memory", "hold": False, "cands": pool_takes(CANDS.get(k, [])) if k else []})
for p in ST["program"]:
    if p["kind"] == "bridge":
        k = key_by_title.get(p["title"]); cols.append({"t": p["t"], "d": p["d"], "act": None, "cap": "", "kind": "bridge", "hold": False, "cands": pool_takes(CANDS.get(k, [])) if k else []})
cols = [c for c in sorted(cols, key=lambda c: c["t"]) if c["cands"]]; acts = [p for p in ST["program"] if p["kind"] == "act"]
for c in cols:
    if not c["act"]: c["act"] = next((a["roman"] for a in reversed(acts) if a["t"] <= c["t"] + .01), "I")
index.append(finish("story", "The story cut", ST["video"], ST["dur"], ST["program"], cols))
# ---- each song's CUTBASTARD film (raw-v2 cut lists; the standalone film opens with a 12.6 s cold open)
SONG = {s["n"]: s for s in json.load(open(os.path.join(D, "songs.json")))["songs"]}
from assemble import CHAPTERS
for f in sorted(glob.glob(os.path.join(L, "edits", "*-blacktop.json"))):
    e = json.load(open(f))
    if e.get("version") != "raw-v2": continue
    n = e["song"]; name = next(t for k, r, t in CHAPTERS if k == n); roman = next(r for k, r, t in CHAPTERS if k == n)
    video = f"slopfeeder/roughcut/slopfeeder-{n}-{name.lower().replace(' ', '-')}.mp4"
    if not os.path.exists(os.path.join(L, video)): continue
    off = 12.63; cols = []; prog = []
    for s in e["slots"]:
        pl = s.get("plate") or {}; i = IX.get(pl.get("id"))
        if i is None: continue
        t = off + s["t0"]; ph = (s.get("patch") or "").split("-")[-1]
        if not prog or prog[-1]["patch"] != s.get("patch"): prog.append({"t": round(t, 2), "d": 0, "kind": "act", "roman": ph, "title": s.get("patch"), "patch": s.get("patch")})
        prog[-1]["d"] = round(t + s["dur"] - prog[-1]["t"], 2)
        tk = ai_takes(i, pl.get("in")) if C[i]["type"] == "ai" else ar_takes(i)
        cols.append({"t": round(t, 3), "d": round(s["dur"], 3), "act": ph, "cap": "", "kind": "ai" if C[i]["type"] == "ai" else "memory", "hold": False, "poison": False, "cands": tk})
    dur = float(__import__("subprocess").run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(L, video)], capture_output=True, text=True).stdout or 0)
    index.append(finish(f"song-{n}", f"{roman} · {name} (song {n})", video, dur, prog, cols, off))
json.dump(index, open(os.path.join(OUTD, "index.json"), "w"), indent=1)
