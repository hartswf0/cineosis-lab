"""PILOT · the archive's two jobs.
  pictures  for each narration, one shot per thing it names ("see"): CLIP over the read archive, minus pictures that suit
            everything, minus talking heads (a face would seem to speak the narrator's words), one film once
  citizens  for each chorus beat, an archival person saying something near what was asked (all-mpnet-base-v2 over the clean
            sentences), whose clip shows a person (so the voice has a face), short (1.5-6 s), one film once
Writes pilot/<ep>.picked.json.   usage: .venv/bin/python republic/pilot/pick.py ep01"""
import json, os, re, sys
import numpy as np, torch, open_clip
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); L = os.path.dirname(R); OD = os.path.join(L, "odyssey")
EP = sys.argv[1] if len(sys.argv) > 1 else "ep01"; cut = json.load(open(os.path.join(H, EP + ".voiced.json")))
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index("# ---- words: Homer's content words said")]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "pilot"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, UV, embed, lib = G["U"], G["UV"], G["embed"], G["lib"]; UV = UV / (np.linalg.norm(UV, axis=1, keepdims=True) + 1e-9)
ids = json.load(open(os.path.join(OD, "cache", "ids.json"))); EM = np.load(os.path.join(OD, "cache", "emb-openai.npy")).astype(np.float32); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
row = {i: k for k, i in enumerate(ids)}
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def tx(ts):
    with torch.no_grad(): v = m.encode_text(tok(ts)).float()
    return (v / v.norm(dim=-1, keepdim=True)).numpy()
HUB = np.sort(EM @ tx([f"a film still of {w}" for w in "a man|a woman|a room|a street|a landscape|a crowd|a machine|a building|people".split("|")]).T, 1)[:, -3:].mean(1)
HEAD = (EM @ tx(["a film still of a person talking to the camera", "a film still of a man speaking, close up", "a film still of a woman speaking, close up"]).T).max(1)
okv = np.array([bool((lib.get(i) or {}).get("video")) and lib[i].get("kind") != "poet" and float(lib[i].get("dur") or 0) >= 4 for i in ids])
import subprocess, tempfile
from PIL import Image
_, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai")
def frame_fit(v, t, q):
    """the picture actually at that moment, read by CLIP against what we want (the catalogue's thumbnail is not always it)"""
    p = tempfile.mktemp(suffix=".jpg")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", v, "-frames:v", "1", "-vf", "scale=320:-2", p], capture_output=True, timeout=60)
    if r.returncode or not os.path.exists(p): return -1, None
    im = Image.open(p).convert("RGB"); os.unlink(p)
    if np.asarray(im).mean() < 25: return -1, None
    with torch.no_grad(): e = m.encode_image(pre(im).unsqueeze(0)).float(); e = (e / e.norm()).numpy()[0]
    return float(e @ tx([f"a film still of {q}"])[0]), e
PL = json.load(open(os.path.join(R, "planes.json"))); [PL["episodes"].update(json.load(open(os.path.join(R, f)))["episodes"]) for f in ("planes-eps.json", "planes-eps2.json") if os.path.exists(os.path.join(R, f))]
used = {"crossroads usa"}                                             # refused by eye: its talker is off frame
for b in cut["beats"]:
    if b["k"] != "narr": continue
    shots = []
    for q in b["see"]:
        if isinstance(q, dict):                                          # a place or a cast member already chosen by eye
            if "place" in q:
                pi, ai = int(q["place"][1]), "ab".index(q["place"][2]); a = PL["episodes"][cut["id"]]["places"][pi]["alts"][ai]
                shots.append({"v": a["video"], "in": max(0.0, a.get("t", 0) - 1.0), "src": a["title"][:70], "y": a.get("year"), "q": q["place"]})
            else:
                f = PL["cast"][q["cast"]][0]; shots.append({"v": f["video"], "in": max(0.0, f.get("t", 0) - .5), "src": f["title"][:70], "y": f.get("year"), "q": q["cast"]})
            used.add(shots[-1]["src"].lower()); continue
        s = EM @ tx([f"a film still of {q}"])[0] - .55 * HUB - .25 * np.clip(HEAD - np.median(HEAD), 0, None); s[~okv] = -9
        tries = 0
        for k in np.argsort(-s)[:200]:
            x = lib[ids[k]]; t = (x.get("title") or "").lower()
            if t in used: continue
            st = max(0.0, float(x.get("in") or 0) - 1.0); fit, _ = frame_fit(x["video"], st + 1.5, q); tries += 1
            if fit < .25 and tries < 10: continue
            used.add(t); shots.append({"v": x["video"], "in": st, "dur": float(x.get("dur") or 0), "src": (x.get("title") or "")[:70], "y": x.get("year"), "q": q, "fit": round(fit, 3)}); break
    b["shots"] = shots; print("narr ·", " | ".join(f"{s['q'][:24]} → {s['src'][:30]}" for s in shots), flush=True)
good = [j for j, (i, t0, t1, text, n, conf, whole, cold) in enumerate(U) if whole and not cold and conf >= .75 and 1.5 <= t1 - t0 <= 6 and (lib.get(i) or {}).get("video") and i in row]
gU = UV[good]; gH = np.array([HEAD[row[U[j][0]]] for j in good]); gH = (gH - gH.mean()) / gH.std()
for b in cut["beats"]:
    if b["k"] != "chorus": continue
    q = embed([b["ask"]]).astype(np.float32)[0]; q /= np.linalg.norm(q)
    s = gU @ q + .06 * np.clip(gH, -1, 2)
    for k in np.argsort(-s):
        j = good[k]; i, t0, t1, text = U[j][:4]; x = lib[i]; t = (x.get("title") or "").lower()
        if t in used or gH[k] < .3: continue
        fit, e = frame_fit(x["video"], t0 + .8, "a person talking"); fit2, e2 = frame_fit(x["video"], t0 + (t1 - t0) * .7, "a person talking")
        if e2 is None or float(e2 @ tx(["a film still of a person talking to the camera"])[0]) < .22: continue
        if e is None or float(e @ tx(["a film still of a person talking to the camera"])[0]) < .22: continue
        used.add(t); b.update(v=x["video"], **{"in": round(max(0, t0 - .1), 2)}, d=round(t1 - t0 + .25, 2), said=text.strip(), src=(x.get("title") or "")[:70], y=x.get("year")); break
    print(f"chorus · “{b['ask']}” → “{b['said']}” ({b['src'][:40]})", flush=True)
json.dump(cut, open(os.path.join(H, EP + ".picked.json"), "w"), ensure_ascii=False, indent=1)
