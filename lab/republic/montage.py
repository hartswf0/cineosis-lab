"""THE REPUBLIC, BY MONTAGE. The archive's voice and the archive's picture are never the same clip: one film speaks, another is
seen, and the cast converse in front of the picture through the borrowed voice (Kuleshov: the meaning is in the join).
For every spoken line (archive.json, from archive_cut.py):
  sound     stays the sentence from the character's film (its audio only)
  picture   either the scene's ground (the place clip running on, so the conversation has somewhere to stand) or an INSERT: the
            archival shot that best pictures what the line is about (CLIP, openai ViT-B/32, on the screenplay's line and the
            archive's words together, minus pictures that suit every line, minus talking heads, never a clip that is speaking in
            this episode, never twice). A line takes an insert when its best insert is clearly about it (above the episode's
            median); the rest stay on the ground. Lines after an insert return to the ground, so the eye rests.
Rewrites archive.json: each line gains a (its sound: v, in) and its picture moves into v/in/vol, with pk "insert" or "ground".
usage: .venv/bin/python republic/montage.py"""
import json, os, re, collections
import numpy as np, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); OD = os.path.join(L, "odyssey")
A = json.load(open(os.path.join(H, "archive.json")))
lib = {x["id"]: x for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"]}
ids = json.load(open(os.path.join(OD, "cache", "ids.json"))); EM = np.load(os.path.join(OD, "cache", "emb-openai.npy")).astype(np.float32); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
ok = np.array([bool((lib.get(i) or {}).get("video")) and lib[i].get("kind") != "poet" and float(lib[i].get("dur") or 0) >= 3 for i in ids])
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def tx(ts):
    with torch.no_grad(): v = m.encode_text(tok(ts)).float()
    return (v / v.norm(dim=-1, keepdim=True)).numpy()
G = tx([f"a film still of {w}" for w in "a man|a woman|a room|a street|a landscape|a crowd|a machine|a building|people".split("|")])
HUB = np.sort(EM @ G.T, 1)[:, -3:].mean(1)
HEAD = (EM @ tx(["a film still of a person talking to the camera", "a film still of a man speaking at a desk, close up"]).T).max(1)
HEAD = (HEAD - HEAD.mean()) / HEAD.std()
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that i you he she we they me him her us them my your his our their not no so if then what who which when where how all any some one into out up down over very can will just do did have has had am would should could may might must oh well now there here let get got say said yes yeah okay right like know think going".split())
def gist(t): return " ".join(w for w in re.findall(r"[A-Za-z']+", t) if w.lower() not in STOP and len(w) > 2)[:200]
vid2id = {lib[i]["video"]: i for i in lib if lib[i].get("video")}
import subprocess, concurrent.futures as cf
def probe(u):
    try: return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", u], capture_output=True, text=True, timeout=40).stdout.strip())
    except Exception: return 0.0
PL = sorted({s["v"] for ep in A.values() for s in ep["segs"] if s["k"] in ("act", "title") and s.get("v")} | {s["a"]["v"] if "a" in s else "" for ep in A.values() for s in ep["segs"] if s["k"] == "line" and s.get("pk") == "ground"} - {""})
with cf.ThreadPoolExecutor(10) as ex: REAL = dict(zip(PL, ex.map(probe, PL)))
used_global = collections.Counter()
for eid, ep in A.items():
    segs = ep["segs"]; lines = [s for s in segs if s["k"] == "line"]
    speaking = {s["v"] for s in lines}                                    # clips whose voices are in this episode: never seen
    Q = tx([f"a film still of {gist(s['line'] + ' ' + s['said']) or 'a scene'}" for s in lines])
    S = Q @ EM.T - .55 * HUB[None] - .03 * np.clip(HEAD, 0, None)[None]
    S[:, ~ok] = -9
    for n, s in enumerate(lines):
        for k in np.argsort(-S[n])[:1]: pass
    best = []
    taken = set()
    for n, s in enumerate(lines):
        cand = None
        for k in np.argsort(-S[n])[:60]:
            i = ids[k]; v = lib[i]["video"]
            if v in speaking or i in taken or used_global[i] >= 1: continue
            cand = (float(S[n, k]), i); break
        best.append(cand); taken.add(cand[1]) if cand else None
    med = float(np.median([b[0] for b in best if b])) if any(best) else 9
    # the ground: the place clip that was running before each line, continued
    ground, cur = None, None
    reel = list({s["v"]: {"v": s["v"], "src": s["src"], "y": s.get("y")} for s in segs if s["k"] in ("act", "title") and s.get("v")}.values())   # every place of the episode
    prev_insert = False; ni = 0
    for s in segs:
        if s["k"] in ("act", "title"):
            cur = {"v": s["v"], "at": s["in"] + s["dur"], "src": s["src"], "y": s.get("y")}
            continue
        if s["k"] != "line": continue
        n = lines.index(s); b = best[n]
        s["a"] = {"v": s["v"], "in": s["in"], "src": s["src"], "y": s.get("y")}       # the voice: sound only
        if b and b[0] > med and not prev_insert:
            i = b[1]; x = lib[i]; d = float(x.get("dur") or 0); mid = float(x.get("in") or 0)
            st = max(0.0, min(mid - s["dur"] / 2, d - s["dur"] - .2)) if d else 0.0
            s.update(v=x["video"], **{"in": round(st, 2)}, vol=.1, pk="insert", src=(x.get("title") or "")[:70], y=x.get("year")); used_global[i] += 1; prev_insert = True; ni += 1
        elif cur:
            if REAL.get(cur["v"], 0) and cur["at"] + s["dur"] > REAL[cur["v"]] - .15 and len(reel) > 1:   # the ground clip is spent: the next one of the scene
                i0 = next((n for n, r in enumerate(reel) if r["v"] == cur["v"]), 0)
                k = next((reel[(i0 + d) % len(reel)] for d in range(1, len(reel)) if REAL.get(reel[(i0 + d) % len(reel)]["v"], 0) >= s["dur"] + .5), None)
                if k: cur = {"v": k["v"], "at": 0.3, "src": k["src"], "y": k["y"]}
            s.update(v=cur["v"], **{"in": round(cur["at"], 2)}, vol=.12, pk="ground", src=cur["src"], y=cur["y"]); cur["at"] += s["dur"]; prev_insert = False
        else:
            s.update(pk="ground"); prev_insert = False
    print(f"{eid}: {ni}/{len(lines)} lines cut to an insert · e.g. " + "; ".join(f"“{s['said'][:28]}” over {s['src'][:26]}" for s in lines if s.get("pk") == "insert")[:150], flush=True)
json.dump(A, open(os.path.join(H, "archive.json"), "w"), ensure_ascii=False, separators=(",", ":"))
# ---- inserts fitted to their clips' real lengths (the catalogue's length is sometimes wrong)
segs = [s for ep in A.values() for s in ep["segs"] if s["k"] == "line" and s.get("pk") == "insert"]
vs = sorted({s["v"] for s in segs})
with cf.ThreadPoolExecutor(10) as ex: RI = dict(zip(vs, ex.map(probe, vs)))
for s in segs:
    d = RI.get(s["v"], 0)
    if d and s["in"] + s["dur"] > d - .1: s["in"] = round(max(0, d - s["dur"] - .15), 2)
json.dump(A, open(os.path.join(H, "archive.json"), "w"), ensure_ascii=False, separators=(",", ":"))
