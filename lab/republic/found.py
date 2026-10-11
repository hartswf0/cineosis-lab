"""MARKOV FOUND · REPUBLIC: the Republic answered by the archive in its own pictures and its own sound (no stills, no assemblies).
For every line of the screenplay, the archive's whole spoken sentence that best answers it (the found Odyssey's way: all-mpnet-base-v2
meaning of the line against every clean archival utterance, plus the words they share), played as the clip itself, from where the
sentence begins to where it ends. For every place, the clips the planes were cut from, played whole with their own sound.
Timing is the point: every answer lasts exactly as long as its sentence, every call as long as its voice.
Writes republic/found.json.   usage: .venv/bin/python republic/found.py"""
import json, os, re, collections
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); OD = os.path.join(L, "odyssey")
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index("# ---- words: Homer's content words said")]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "found_republic"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, UV, embed, lib = G["U"], G["UV"], G["embed"], G["lib"]
UV = UV / (np.linalg.norm(UV, axis=1, keepdims=True) + 1e-9)
good = np.array([bool(whole and not cold and conf >= .7 and 1.0 <= t1 - t0 <= 9 and 3 <= n <= 30 and (lib.get(i) or {}).get("video") and not re.search(r"\b(fuck|shit)\b", text, re.I))
                 for (i, t0, t1, text, n, conf, whole, cold) in U])
print(int(good.sum()), "clean archival sentences", flush=True)
S = json.load(open(os.path.join(H, "script.json"))); W = json.load(open(os.path.join(H, "world.json")))
P = json.load(open(os.path.join(H, "planes.json"))); [P["episodes"].update(json.load(open(os.path.join(H, f)))["episodes"]) for f in ("planes-eps.json", "planes-eps2.json") if os.path.exists(os.path.join(H, f))]
RC = json.load(open(os.path.join(H, "cache", "clips.json")))
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that i you he she we they me him her us them my your his our their not no so if then what who which when where how all any some one into out up down over very can will just do did have has had am would should could may might must oh well now there here let get got say said".split())
words = lambda t: {w for w in re.findall(r"[a-z']+", t.lower()) if len(w) > 2 and w not in STOP}
UW = [words(u[3]) for u in U]
def dur_of(cid):
    s = lib.get(cid) or RC.get(cid) or {}; return float(s.get("dur") or 0)
used = collections.Counter(); out = {}
for e in S["episodes"]:
    lines = [(k, b) for k, b in enumerate(e["beats"]) if b["k"] == "line"]
    V = embed([b["text"] for _, b in lines]).astype(np.float32); V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-9
    clips_here, ans = set(), {}
    for (k, b), v in zip(lines, V):
        lw = words(b["text"]); sc = UV @ v
        best = None
        for j in np.argsort(-np.where(good, sc, -9))[:300]:
            i = U[j][0]
            if i in clips_here: continue
            s = float(sc[j]) + .12 * (len(lw & UW[j]) / max(1, len(lw))) - .05 * used[i]
            if best is None or s > best[0]: best = (s, j)
            if best and sc[j] < best[0] - .2: break
        s, j = best; i, t0, t1, text = U[j][:4]; clips_here.add(i); used[i] += 1
        ans[k] = {"v": lib[i]["video"], "t0": round(t0, 2), "t1": round(t1, 2), "s": text.strip(), "ti": (lib[i].get("title") or "")[:70], "y": lib[i].get("year"), "fit": round(s, 3)}
    places = []
    for p in P["episodes"][e["id"]]["places"]:
        for a in p["alts"]:
            d = dur_of(a["id"]); places.append({"v": a["video"], "t": a.get("t", 0), "d": round(d, 2), "ti": a["title"][:70], "y": a.get("year")})
    out[e["id"]] = {"answers": ans, "places": places}
    print(f"{e['id']} {e['name'][:30]:30} mean fit {np.mean([a['fit'] for a in ans.values()]):.2f} · e.g. “{next(iter(ans.values()))['s'][:70]}”", flush=True)
json.dump(out, open(os.path.join(H, "found.json"), "w"), ensure_ascii=False, separators=(",", ":"))
