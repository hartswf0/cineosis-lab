"""EPISODE 7 · THE REPUBLIC — data, all from the Republic's own files, plus two measurements:
  replay   the answering rule of republic/found.py, run again for the first lines of episode 1 (the first episode, so nothing was used
           before it and the replay is exact): every candidate sentence the archive could have said, its meaning score, its shared-words
           bonus, and the winner, checked against found.json
  heard    episode 1's own soundtrack transcribed (faster-whisper base.en) so the film can find the moment each line is spoken
  and      the 17 episodes; the seven witnesses and which one wrote episode 1; the cast and their voices; the casting of one archival
           film per character; the depth planes and cut-outs; the forage questions
Writes explain/ep/ep7.json.   usage: lab/.venv/bin/python lab/explain/ep7.py"""
import json, os, re, collections
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); RP = os.path.join(LAB, "republic"); OD = os.path.join(LAB, "odyssey")
J = lambda p: json.load(open(os.path.join(LAB, p)))
S = J("republic/script.json"); W = J("republic/world.json"); F = J("republic/found.json"); A = J("republic/archive.json")
ep = S["episodes"][0]; EID = ep["id"]
# ---- the replay (found.py, verbatim logic)
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index("# ---- words: Homer's content words said")]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "found_republic"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, UV, embed, lib = G["U"], G["UV"], G["embed"], G["lib"]; UV = UV / (np.linalg.norm(UV, axis=1, keepdims=True) + 1e-9)
good = np.array([bool(whole and not cold and conf >= .7 and 1.0 <= t1 - t0 <= 9 and 3 <= n <= 30 and (lib.get(i) or {}).get("video") and not re.search(r"\b(fuck|shit)\b", text, re.I)) for (i, t0, t1, text, n, conf, whole, cold) in U])
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that i you he she we they me him her us them my your his our their not no so if then what who which when where how all any some one into out up down over very can will just do did have has had am would should could may might must oh well now there here let get got say said".split())
words = lambda t: {w for w in re.findall(r"[a-z']+", t.lower()) if len(w) > 2 and w not in STOP}
lines = [(k, b) for k, b in enumerate(ep["beats"]) if b["k"] == "line"][:3]
V = embed([b["text"] for _, b in lines]).astype(np.float32); V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-9
clips_here, replay = set(), []
for (k, b), v in zip(lines, V):
    lw = words(b["text"]); sc = UV @ v; cands = []
    for j in np.argsort(-np.where(good, sc, -9))[:300]:
        i = U[j][0]
        if i in clips_here: continue
        bonus = .12 * (len(lw & words(U[j][3])) / max(1, len(lw))); cands.append((float(sc[j]) + bonus, float(sc[j]), bonus, j))
    cands.sort(reverse=True); s, m, bo, j = cands[0]; clips_here.add(U[j][0])
    pub = F[EID]["answers"][str(k)]
    replay.append({"who": b["who"], "line": b["text"], "won": U[j][3].strip(), "published": pub["s"], "agrees": U[j][3].strip() == pub["s"].strip(),
                   "cands": [{"s": U[jj][3].strip(), "meaning": round(mm, 3), "words": round(bb, 3), "total": round(ss, 3), "title": (lib[U[jj][0]].get("title") or "")[:60], "year": lib[U[jj][0]].get("year"),
                              "v": lib[U[jj][0]]["video"], "t0": round(U[jj][1], 2), "t1": round(U[jj][2], 2)} for ss, mm, bb, jj in cands[:7]]})
    print(b["who"], "|", b["text"][:40], "->", U[j][3][:50], "| agrees", replay[-1]["agrees"])
print(int(good.sum()), "clean archival sentences to choose from")
# ---- episode 1's own soundtrack, heard
from faster_whisper import WhisperModel
wm = WhisperModel("base.en", device="cpu", compute_type="int8"); segs, _ = wm.transcribe(os.path.join(RP, "pilot", "ep01-score.mp4"), word_timestamps=False)
heard = [[round(s.start, 2), round(s.end, 2), s.text.strip()] for s in segs]
# ---- everything else
cast = {n: W["cast"][n] for n in ep["cast"] if n in W["cast"]}
segs_a = [s for s in A[EID]["segs"] if s.get("k") in ("line", "talk", "voice") or s.get("who")][:6]
pe = J("republic/planes-eps.json")["episodes"].get(EID) or {}
out = {"episodes": [{"id": e["id"], "name": e["name"], "series": e.get("series"), "genre": e.get("genre"), "logline": e.get("logline"), "witness": e.get("witness"), "takes": e.get("takes"),
                     "mp4": f"republic/pilot/ep{i + 1:02d}-score.mp4"} for i, e in enumerate(S["episodes"])],
       "ep": {"id": EID, "name": ep["name"], "logline": ep["logline"], "witness": ep["witness"], "takes": ep["takes"], "cast": cast, "casting": A[EID]["voices"], "segs": segs_a,
              "places": [{"q": p["q"], "alt": p["alts"][0]} for p in pe.get("places", [])], "world": W["episodes"].get(EID)},
       "replay": replay, "clean": int(good.sum()), "heard": heard, "forage": list(J("republic/cache/raw.json"))[:40], "forage_n": len(J("republic/cache/raw.json")), "forage_clips": 2197}
json.dump(out, open(os.path.join(H, "ep", "ep7.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(heard), "heard segments;", [h for h in heard if "decline" in h[2].lower()][:2]); print(json.dumps(segs_a[:2])[:500])
