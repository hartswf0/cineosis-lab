"""SCORE · FIT: a film's movements find their music by what they say.
A movement is a stretch of film with one feeling (a beat of the Republic, a chapter of the Norse house, a narration and its
exchange in the pilot), given as its own words and its length. Each movement's words are read by CLAP's text side
("music for a film scene: ..."), centred against how music prompts read in general, and set against every 10-second window of
the chosen album, centred against the whole library (so no cue answers for everything). A movement takes the run of windows
that fits it best for its length; it stays with the previous cue when that cue still fits nearly as well (continuity), never
takes a cue used in the last two movements otherwise, and enters on one of the cue's beats.
  plan(movements, album) → [{track, title, offset, fit, mood}]      (importable; .venv)
  CLI: .venv/bin/python score/fit.py republic | pilot <ep> | norse    writes the plans those pages and renders read"""
import json, os, sys, re
import numpy as np, torch
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
from transformers import ClapModel, ClapProcessor
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
LIB = json.load(open(os.path.join(H, "library.json"))); E = np.load(os.path.join(H, "clap.npy")).astype(np.float32)
Ec = E - E.mean(0); Ec /= np.linalg.norm(Ec, axis=1, keepdims=True) + 1e-9
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
def tx(ts):
    with torch.no_grad(): v = cm.get_text_features(**cp(text=ts, return_tensors="pt", padding=True, truncation=True))
    return (v / v.norm(dim=-1, keepdim=True)).numpy()
TMEAN = tx([f"{v} music" for v in LIB["vocab"]]).mean(0)
def read(text):
    t = tx([f"music for a film scene: {text}"[:300]])[0] - TMEAN; return t / (np.linalg.norm(t) + 1e-9)
def plan(movements, album, used_before=()):
    tracks = [t for t in LIB["tracks"] if t["album"].lower().startswith(album.lower()[:6])]
    out, recent, prev = [], list(used_before)[-2:], None
    for mv in movements:
        q = read(mv["text"])
        if mv.get("mood"): q = q + 1.4 * read(mv["mood"] + " music"); q /= np.linalg.norm(q)      # what the scene should feel like weighs above what it says
        need = max(1, int(np.ceil(mv["dur"] / 5)))
        best = None
        for t in tracks:
            sc = Ec[t["w0"]: t["w0"] + len(t["win"])] @ q
            for s in range(0, max(1, len(sc) - min(need, len(sc)) + 1)):
                v = float(sc[s: s + need].mean())
                cont = prev and prev["track"] == t["id"] and abs(t["win"][s] - prev["end"]) < 12
                if cont: v += .09
                elif t["id"] in recent: continue
                if best is None or v > best[0]: best = (v, t, s)
        v, t, s = best; off = t["win"][s]
        if prev and prev["track"] == t["id"] and abs(off - prev["end"]) < 12: off = prev["end"]             # the cue simply runs on
        else: off = next((b for b in t["beats"] if b >= off), off)                                       # a new cue enters on a beat
        if off + mv["dur"] > t["dur"] - 2: off = max(0.0, t["dur"] - mv["dur"] - 2)
        from collections import Counter
        mood = [k for k, _ in Counter(x for w in t["tags"][s: s + need] for x in w).most_common(2)]
        p = {"track": t["id"], "title": t["title"], "f": t["f"], "offset": round(off, 2), "fit": round(v, 3), "mood": mood, "end": round(off + mv["dur"], 2)}
        out.append(p); prev = p; recent = (recent + [t["id"]])[-2:]
    return out
if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "republic"
    if what == "republic":                      # each beat of each episode (between its actions), read by its action and the scene's world
        A = json.load(open(os.path.join(L, "republic", "archive.json"))); S = {e["id"]: e for e in json.load(open(os.path.join(L, "republic", "script.json")))["episodes"]}
        WG = json.load(open(os.path.join(L, "republic", "world.json")))["episodes"]
        MOOD = {"mars": "lonely desert, wonder", "fluoro": "playful and comic", "gold": "triumph, driving rhythm", "noir": "tension and suspense, dread", "sepia": "melancholy guitar, lonely desert",
                "pastel": "playful and comic, dreamy", "cartoon": "playful and comic", "matrix": "glitchy electronic, tension", "comic": "triumph, a journey in motion", "neon": "driving rhythm, glitchy electronic",
                "vault": "tension and suspense", "western": "lonely desert, country western", "server": "glitchy electronic, dread"}
        OUT = {}
        for album in ("D-A-E", "The Republic"):
            for eid, ep in A.items():
                mvs, cur = [], None
                for s in ep["segs"]:
                    if s["k"] in ("title", "act") or cur is None:
                        cur = {"text": (s.get("text") or S[eid]["logline"]) + " · " + S[eid]["slug"].lower(), "mood": MOOD.get(WG[eid]["grade"], ""), "dur": 0.0, "first": s["t0"]}; mvs.append(cur)
                    cur["dur"] += s["dur"]
                OUT.setdefault(eid, {})[album] = plan(mvs, album)
            print(album, "·", "; ".join(f"{p['title'][:26]} @{p['offset']:.0f}s ({', '.join(p['mood'])})" for p in OUT[next(iter(A))][album][:4]), flush=True)
        json.dump(OUT, open(os.path.join(L, "republic", "score.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    elif what == "pilot":                        # each narration and the exchange it introduces
        ep = sys.argv[2] if len(sys.argv) > 2 else "ep01"; P = os.path.join(L, "republic", "pilot", ep + ".picked.json"); cut = json.load(open(P))
        mvs, cur = [], None
        for b in cut["beats"]:
            d = {"title": 4.0, "end": 4.0, "narr": b.get("d", 0) + .7, "talk": b.get("d", 0) + .3, "chorus": b.get("d", 0) + .2}[b["k"]]
            if b["k"] in ("title", "narr", "end") or cur is None:
                cur = {"text": b.get("text") or cut["title"], "mood": b.get("mood", ""), "dur": 0.0}; mvs.append(cur)
            cur["dur"] += d
        pl = plan(mvs, sys.argv[3] if len(sys.argv) > 3 else "D-A-E"); cut["score"] = pl
        json.dump(cut, open(P, "w"), ensure_ascii=False, indent=1)
        for m_, p in zip(mvs, pl): print(f"  {m_['dur']:5.1f}s  {p['title'][:30]:30} @{p['offset']:5.1f} fit {p['fit']:+.2f} ({', '.join(p['mood'])}) ← {m_['text'][:50]}")
    elif what == "norse":                        # each chapter of the Norse house, read by its title, what it shows, and the feeling it asks for
        P = json.load(open(os.path.join(L, "norse", "poem.json")))
        MOOD = ["quiet calm, dreamy ambient", "wonder and awe, folk acoustic", "ocean and waves, dreamy ambient", "ocean and waves, melancholy guitar",
                "a journey in motion, driving rhythm", "playful and comic, funk groove", "sorrow, a warm return home"]
        mvs = [{"text": f"{b['title']}: {b['see']}", "mood": MOOD[k % len(MOOD)], "dur": 9.0 * len(b["lines"])} for k, b in enumerate(P["books"])]
        pl = plan(mvs, "D-A-E")
        json.dump([{k: p[k] for k in ("f", "offset", "title", "mood")} for p in pl], open(os.path.join(L, "norse", "score.json"), "w"), ensure_ascii=False, indent=1)
        for b, p in zip(P["books"], pl): print(f"  {b['title'][:36]:36} {p['title'][:32]:32} @{p['offset']:5.1f} ({', '.join(p['mood'])})")
