"""The AI pickups (lab/slopfeeder/ai/src, 44 clips generated from the studio's prompts), read into the SLOPFEEDER world:
each clip split at its own cuts; each shot's middle frame embedded with CLIP; read for its part of the world, its camera position
(embedded first-person, hovering witness, wide, close...), the motifs it carries (pails, skull mask, the four characters, cursor, login
screen, burned-in subtitles); matched to its nearest archival shot in that world (the rhyme) and the SLOPFEEDER frame it grew from.
Writes ai/ai.json, ai/keys/*.jpg, ai/web/*.mp4 (640x360 previews for the pages).   usage: .venv/bin/python slopfeeder/ai_ingest.py"""
import json, os, re, subprocess
import numpy as np, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); A_ = os.path.join(D, "ai"); SRC = os.path.join(A_, "src")
for d in ("keys", "web"): os.makedirs(os.path.join(A_, d), exist_ok=True)
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ci(ims):
    with torch.no_grad(): e = m.encode_image(torch.stack([prep(i.convert("RGB")) for i in ims])).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float()
    return (e / e.norm(dim=-1, keepdim=True)).numpy()
PO = json.load(open(os.path.join(D, "pools.json"))); WORLDS = PO["worlds"]; WN = list(WORLDS); WT = {w: ct(WORLDS[w]) for w in WN}
POV = {"embedded": "a first-person view with the viewer's own hands and arms in the foreground", "shoulder": "an over-the-shoulder view close behind a person",
       "witness": "a low hovering drone view from above and behind people", "face": "an extreme close-up of a face", "hands": "a close-up of hands holding an object",
       "medium": "a medium shot of people working", "wide": "a wide shot of a landscape with small figures", "optic": "a view through binoculars or a lens",
       "screen": "a computer screen filling the frame"}
MOTIF = {"pails": "orange buckets turned upside down in wet sand", "skull": "a person wearing a skull mask", "characters": "colorful cartoon shapes with dot eyes",
         "login": "a computer login screen with cartoon characters", "cursor": "a giant white mouse cursor arrow", "burgers": "burgers and onions on a griddle",
         "craft": "a landing craft with its ramp down", "airship": "a huge airship in a stormy sky", "laser": "a bright laser beam", "fort": "a ruined brick fort by the sea",
         "subtitle": "white subtitle text at the bottom of the frame", "fire": "fires burning on a beach", "terminal": "green text on an old computer terminal"}
PT = ct(list(POV.values())); MT = ct(list(MOTIF.values())); NT = ct(["a photo", "a blurry photo", "an empty scene"])
# the archive, the same way pools.py sees it
lib = json.load(open(os.path.join(L, "markov", "library.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json"))); R2 = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * lib["scale"]; emb, rec = {}, {}
for s, e in zip(lib["shots"], E1):
    if s["kind"] == "archive" and s["id"] in V: emb[s["id"]] = e; rec[s["id"]] = {"id": s["id"], "title": s.get("title"), "year": s.get("year"), "v": R2 + V[s["id"]][0], "t": R2 + V[s["id"]][0].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg")}
title = {c["id"]: (c["sourceTitle"], c.get("sourceYear")) for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json")))}
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))):
    if i not in emb and i in title and i in V: emb[i] = e; rec[i] = {"id": i, "title": title[i][0], "year": title[i][1], "v": R2 + V[i][0], "t": R2 + V[i][0].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg")}
F = {c["id"]: c for c in json.load(open(os.path.join(D, "forage.json")))["clips"]}
for i, e in zip(json.load(open(os.path.join(D, "forage-ids.json"))), np.load(os.path.join(D, "forage-emb.npy")).astype(np.float32)):
    if i not in emb and i in F: c = F[i]; emb[i] = e; rec[i] = {"id": i, "title": c["title"], "year": c["year"], "v": c["v"], "t": c["t"]}
ids = list(rec); AE = np.stack([emb[i] for i in ids]); AE /= np.linalg.norm(AE, axis=1, keepdims=True) + 1e-9
pool_of = {w: np.array([i in {x["id"] for x in PO["pools"][w]} for i in ids]) for w in WN}
# the SLOPFEEDER frames (where most pickups began)
W = json.load(open(os.path.join(D, "world.json"))); FR = W["frames"]; FE = ci([Image.open(os.path.join(D, f["src"])) for f in FR])
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
out = []
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".mp4"): continue
    p = os.path.join(SRC, fn); name = fn[:-4]; d = dur(p)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-vf", "select='gt(scene,0.32)',showinfo", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    cuts = [0.0] + [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r) if .4 < float(x) < d - .4] + [d]
    shots = []
    for k, (a, b) in enumerate(zip(cuts, cuts[1:])):
        if b - a < .35: continue
        kp = os.path.join(A_, "keys", f"{name}-{k}.jpg"); mid = (a + b) / 2
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{mid:.2f}", "-i", p, "-frames:v", "1", "-vf", "scale=480:-2", kp])
        # a still held at the head of a clip (image-to-video start) moves very little
        f0, f1 = os.path.join(A_, "keys", "_a.jpg"), os.path.join(A_, "keys", "_b.jpg")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{a + .05:.2f}", "-i", p, "-frames:v", "1", "-vf", "scale=96:-2,format=gray", f0]); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{max(a + .1, b - .1):.2f}", "-i", p, "-frames:v", "1", "-vf", "scale=96:-2,format=gray", f1])
        motion = float(np.abs(np.asarray(Image.open(f0), np.float32) - np.asarray(Image.open(f1), np.float32)).mean())
        e = ci([Image.open(kp)])[0]
        ws = {w: float((WT[w] @ e).max()) for w in WN}; world = max(ws, key=ws.get)
        pv = PT @ e; pov = list(POV)[int(np.argmax(pv))]
        ms = MT @ e - float((NT @ e).max()); motifs = [list(MOTIF)[j] for j in np.argsort(-ms)[:4] if ms[j] > .015]
        sims = AE @ e - 2 * (~pool_of[world]); j = int(np.argmax(sims))
        ref = int(np.argmax(FE @ e))
        shots.append({"k": k, "t0": round(a, 2), "t1": round(b, 2), "key": f"ai/keys/{name}-{k}.jpg", "motion": round(motion, 1), "still": motion < 2.2,
                      "world": world, "pov": pov, "motifs": motifs, "rhyme": {**rec[ids[j]], "s": round(float(sims[j]), 3)},
                      "ref": {"frame": FR[ref]["id"], "src": FR[ref]["src"], "s": round(float(FE[ref] @ e), 3)}, "emb": [round(float(x), 4) for x in e]})
    web = os.path.join(A_, "web", fn)
    if not os.path.exists(web): subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-vf", "scale=640:-2", "-c:v", "libx264", "-crf", "27", "-preset", "slow", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", web])
    out.append({"name": name, "title": name.replace("_", " "), "dur": round(d, 2), "web": f"ai/web/{fn}", "shots": shots})
    print(f"{name[:36]:36s} {len(shots)} shots · " + " | ".join(f"{s['world'][4:10]}/{s['pov']}{'/still' if s['still'] else ''}" for s in shots), flush=True)
for f in ("_a.jpg", "_b.jpg"):
    try: os.remove(os.path.join(A_, "keys", f))
    except Exception: pass
json.dump({"clips": out, "pov": POV, "motif": MOTIF}, open(os.path.join(A_, "ai.json"), "w"))
print("ai.json:", len(out), "clips,", sum(len(c["shots"]) for c in out), "shots")
