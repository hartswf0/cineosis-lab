"""THE REPUBLIC, AS THE ARCHIVE SAYS IT. The screenplay proposes; the archive disposes.
  casting   every character is voiced by ONE archival film: the film whose spoken sentences best cover that character's lines
            (mean of each line's best match inside the film), no two characters of an episode sharing a film, so a character keeps
            one real voice and, mostly, one face
  lines     each line becomes that film's best unused sentence (all-mpnet-base-v2 meaning + shared words + a bonus where the clip
            shows a person talking); if the film has nothing near, the whole archive answers. What the archive says IS the new script
  actions   the place clips with their own sound, as long as the action takes to read; places are cut on their measured length
  timing    every segment's length is the sentence's own (from where it starts to where it ends) or the clip's real length
            (ffprobe, not the catalogue: the catalogue is sometimes a second long)
  bodies    each spoken segment carries the loudness of the archive's own sound (40 steps), so the actors move to it
Writes republic/archive.json (per episode: the cast's films and a timeline of segments).   usage: .venv/bin/python republic/archive_cut.py"""
import json, os, re, subprocess, collections, concurrent.futures as cf
import numpy as np, soundfile as sf
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); OD = os.path.join(L, "odyssey")
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index("# ---- words: Homer's content words said")]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "archive_cut"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, UV, embed, lib = G["U"], G["UV"], G["embed"], G["lib"]
UV = UV / (np.linalg.norm(UV, axis=1, keepdims=True) + 1e-9)
good = np.array([bool(whole and not cold and conf >= .7 and 1.0 <= t1 - t0 <= 9 and 3 <= n <= 30 and (lib.get(i) or {}).get("video") and not re.search(r"\b(fuck|shit)\b", text, re.I))
                 for (i, t0, t1, text, n, conf, whole, cold) in U])
# a person on screen: the clip's picture against "someone talking" (openai CLIP, the Odyssey's cache)
import torch, open_clip
ids = json.load(open(os.path.join(OD, "cache", "ids.json"))); EM = np.load(os.path.join(OD, "cache", "emb-openai.npy")).astype(np.float32); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
row = {i: k for k, i in enumerate(ids)}
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
with torch.no_grad(): T = m.encode_text(tok(["a film still of a person talking to the camera", "a film still of a man speaking, close up", "a film still of an empty landscape", "a film still of machinery"])).float(); T = (T / T.norm(dim=-1, keepdim=True)).numpy()
pers = np.zeros(len(U), np.float32)
for j, u in enumerate(U):
    r = row.get(u[0])
    if r is not None: s = EM[r] @ T.T; pers[j] = s[:2].max() - s[2:].max()
pers = np.clip((pers - np.median(pers)) / (pers.std() + 1e-6), -2, 2)
film = lambda j: (lib[U[j][0]].get("src") or lib[U[j][0]].get("title") or U[j][0])
FILM = np.array([film(j) if good[j] else "" for j in range(len(U))])
byfilm = collections.defaultdict(list)
for j in np.where(good)[0]: byfilm[FILM[j]].append(j)
films = [f for f, js in byfilm.items() if len(js) >= 6]
print(int(good.sum()), "clean sentences ·", len(films), "films with six or more", flush=True)
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that i you he she we they me him her us them my your his our their not no so if then what who which when where how all any some one into out up down over very can will just do did have has had am would should could may might must oh well now there here let get got say said".split())
words = lambda t: {w for w in re.findall(r"[a-z']+", t.lower()) if len(w) > 2 and w not in STOP}
UW = [words(u[3]) for u in U]
D36 = "0123456789abcdefghijklmnopqrstuvwxyz"
def env(cid, t0, t1):
    p = os.path.join(OD, "cache", "aud", cid + ".flac")
    if not os.path.exists(p): return ""
    try:
        info = sf.info(p); a, _ = sf.read(p, start=int(max(0, t0) * info.samplerate), stop=int(t1 * info.samplerate), dtype="float32")
        if a.ndim > 1: a = a.mean(1)
        n = 40; k = max(1, len(a) // n); r = np.sqrt((a[: k * n].reshape(n, k) ** 2).mean(1)); db = 20 * np.log10(r + 1e-6); top = np.percentile(db, 95)
        return "".join(D36[int(round(x * 35))] for x in np.clip((db - (top - 30)) / 30, 0, 1))
    except Exception: return ""
def probe(u):
    try: return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", u], capture_output=True, text=True, timeout=40).stdout.strip())
    except Exception: return 0.0
S = json.load(open(os.path.join(H, "script.json"))); W = json.load(open(os.path.join(H, "world.json")))
F = json.load(open(os.path.join(H, "found.json")))
alias = lambda w: W["alias"].get(w, w)
OUT = {}; used_films = collections.Counter()
for e in S["episodes"]:
    lines = [(k, b) for k, b in enumerate(e["beats"]) if b["k"] == "line"]
    V = embed([b["text"] for _, b in lines]).astype(np.float32); V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-9
    SIM = V @ UV.T                                                           # lines × sentences
    for n, (_, b) in enumerate(lines):
        lw = words(b["text"]); SIM[n] += np.array([.1 * len(lw & UW[j]) / max(1, len(lw)) if lw & UW[j] else 0 for j in range(len(U))], np.float32) if lw else 0
    SIM += .04 * pers[None, :]; SIM[:, ~good] = -9
    who = [alias(b["who"]) for _, b in lines]; cast = list(dict.fromkeys(who)); taken = set(); voice = {}
    for c in sorted(cast, key=lambda c: -who.count(c)):                     # the most-speaking characters choose first
        rows_ = [n for n, w in enumerate(who) if w == c]; best = None
        for f in films:
            if f in taken: continue
            js = byfilm[f]
            if len(js) < len(rows_) + 2: continue
            sub = SIM[np.ix_(rows_, js)]; sc = float(np.sort(sub.max(1))[::-1][: max(1, len(rows_))].mean()) - .03 * used_films[f]
            if best is None or sc > best[0]: best = (sc, f)
        if best: voice[c] = best[1]; taken.add(best[1]); used_films[best[1]] += 1
    said, usedj = {}, set()
    for n, (k, b) in enumerate(lines):
        c = who[n]; js = [j for j in byfilm.get(voice.get(c), []) if j not in usedj]
        j = max(js, key=lambda j: SIM[n, j]) if js else None
        if j is None or SIM[n, j] < .22:                                     # the film has nothing near: the archive at large answers
            j = next(int(j) for j in np.argsort(-SIM[n]) if j not in usedj); src_ = "archive"
        else: src_ = "voice"
        usedj.add(j); said[k] = (j, src_)
    # ---- the timeline
    places = [dict(p) for p in F[e["id"]]["places"]]
    with cf.ThreadPoolExecutor(8) as ex: real = list(ex.map(lambda p: probe(p["v"]), places))
    for p, d in zip(places, real): p["d"] = d or p.get("d") or 0
    places = [p for p in places if p["d"] > 2]
    cur = {"i": 0, "at": max(0, places[0]["t"] - 1) if places else 0}
    def place_seg(want, kind, text):
        """the next stretch of the current place clip, as long as wanted (or what is left of it), moving on to the next clip when spent"""
        for _ in range(len(places)):
            p = places[cur["i"] % len(places)]; left = p["d"] - .15 - cur["at"]
            if left >= min(want, 2.2): d = min(want, left); s = {"k": kind, "v": p["v"], "in": round(cur["at"], 2), "dur": round(d, 2), "vol": .75 if kind == "act" else .55, "text": text, "src": p["ti"], "y": p.get("y")}; cur["at"] += d; return s
            cur["i"] += 1; q = places[cur["i"] % len(places)]; cur["at"] = max(0, min(q["t"] - 1, q["d"] - 4))
        return None
    segs = [place_seg(5.0, "title", e["logline"])]
    since = 0
    for k, b in enumerate(e["beats"]):
        if b["k"] == "act" and since >= 4 and k > 2:
            since = 0; cur["i"] = (cur["i"] // 2 + 1) * 2; q = places[cur["i"] % len(places)]; cur["at"] = max(0, min(q["t"] - 1, q["d"] - 4))
        if b["k"] == "card": segs.append({"k": "card", "dur": 2.2, "text": b["text"]})
        elif b["k"] == "act": segs.append(place_seg(min(5.5, max(2.6, len(b["text"].split()) / 2.8)), "act", b["text"]))
        elif k in said:
            since += 1; j, how = said[k]; i, t0, t1, text = U[j][:4]; s = lib[i]
            segs.append({"k": "line", "who": alias(b["who"]), "line": b["text"], "said": text.strip(), "v": s["video"], "in": round(max(0, t0 - .08), 2), "dur": round(t1 - t0 + .22, 2),
                         "vol": 1.0, "src": (s.get("title") or "")[:70], "y": s.get("year"), "env": env(i, t0 - .08, t1 + .14), "how": how})
    segs = [s for s in segs if s]
    t = 0
    for s in segs: s["t0"] = round(t, 2); t += s["dur"]
    OUT[e["id"]] = {"voices": {c: {"film": lib[byfilm[f][0][0] if False else U[byfilm[f][0]][0]].get("title", f)[:70]} for c, f in voice.items()}, "segs": segs, "total": round(t, 1)}
    nv = sum(1 for s in segs if s["k"] == "line" and s["how"] == "voice"); nl = sum(1 for s in segs if s["k"] == "line")
    print(f"{e['id']} {e['name'][:28]:28} {t/60:4.1f} min · {nv}/{nl} lines in the character's own archival voice · " + "; ".join(f"{c}={OUT[e['id']]['voices'][c]['film'][:22]}" for c in list(voice)[:3]), flush=True)
json.dump(OUT, open(os.path.join(H, "archive.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(f"{sum(o['total'] for o in OUT.values())/60:.1f} minutes in all")
