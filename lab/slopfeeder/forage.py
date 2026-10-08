"""Forage the Moving Image Archive for the SLOPFEEDER world: the war on the beach, the fleet offshore, the kitchen, the screens,
the machines that think, the cartoon characters. One query at a time (the archive rate-limits), resumable (forage-raw.json).
Then every clip found is read by its thumbnail with CLIP (the archive's model) against the query that found it, so a query's bad
answers sink. Writes slopfeeder/forage.json.   usage: .venv/bin/python slopfeeder/forage.py"""
import json, os, sys, time, urllib.request, urllib.error, subprocess
D = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(D, "forage-raw.json"); API = "https://www.movingimagearchive.com/api/search"
Q = {
 "the landing": ["D-Day landing craft ramp drops", "soldiers storming a beach under fire", "Normandy invasion beach", "landing craft approaching the beach", "troops wading ashore", "beach obstacles hedgehogs", "soldiers taking cover on the beach", "amphibious assault", "wounded soldiers on the beach", "soldiers climbing a cliff"],
 "the guns": ["artillery firing", "naval guns firing broadside", "battleship firing its guns", "howitzer recoil", "anti-aircraft guns firing at night", "rocket launcher barrage", "tracer fire at night", "machine gun firing", "mortar firing"],
 "the sea": ["ship sinking", "burning ship at sea", "torpedo explosion ship", "destroyer at sea in heavy waves", "warships convoy at sea", "ocean waves crashing", "stormy sea", "aircraft carrier", "submarine surfacing", "wreckage floating in the sea"],
 "the blast": ["huge explosion", "explosion fireball", "atomic bomb mushroom cloud", "bomb explosion in a field", "demolition explosion", "smoke screen", "fire and smoke battlefield", "bombs falling from a plane", "flares lighting the night sky"],
 "the beach": ["empty beach at dawn", "sand dunes", "barbed wire on a beach", "old coastal fort", "bunker on the coast", "tide coming in over sand", "beach at sunset"],
 "the kitchen": ["hamburgers on a grill", "cook flipping burgers", "field kitchen soldiers eating", "army cook serving food", "chow line mess hall", "frying onions", "short order cook diner", "barbecue grill smoke", "feeding a crowd", "sandwich being made"],
 "the screens": ["early computer room", "computer screen text", "punch cards", "programmer at a terminal", "mainframe computer tape drives", "radar screen", "oscilloscope", "control room screens", "computer printout", "video game screen", "typing on a keyboard"],
 "the machines": ["robot", "automation factory machines", "cybernetics", "electronic brain", "artificial intelligence", "assembly line robots", "missile launch", "rocket launch", "satellite in space", "astronauts in spacesuits", "space station"],
 "the future": ["science fiction spaceship", "flying saucer", "laser beam", "ray gun", "space battle", "futuristic city", "planet in space", "alien landscape"],
 "the characters": ["cartoon characters with big eyes", "animated shapes dancing", "cartoon blob character", "purple cartoon character", "orange cartoon character", "yellow cartoon character", "geometric animation", "cartoon soldier", "puppet show"],
 "the work": ["men hauling rope", "workers carrying a beam", "digging in sand", "building a sandbag wall", "hand pump drilling", "repairing a brick wall", "bucket brigade", "soldiers digging trenches"],
 "the faces": ["soldier staring at the camera", "man in a gas mask", "pilot in a helmet and goggles", "man laughing hysterically", "deadpan stare", "commander giving orders"],
}
def search(q):
    tries = 0
    while True:
        req = urllib.request.Request(API, data=json.dumps({"query": q}).encode(), headers={"content-type": "application/json", "user-agent": "cineosis-44-research"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r: return json.load(r).get("clips", [])
        except urllib.error.HTTPError as e:
            tries += 1
            if e.code == 429 or e.code >= 500: time.sleep(float(e.headers.get("retry-after") or 0) or min(60, 5 * tries)); continue
            raise
        except Exception as e:
            tries += 1; print("  retry", e, flush=True); time.sleep(min(120, 10 * tries))
raw = json.load(open(RAW)) if os.path.exists(RAW) else {}
for world, qs in Q.items():
    for q in qs:
        if q in raw: continue
        cl = search(q); raw[q] = [{k: c.get(k) for k in ("id", "sourceTitle", "sourceYear", "startSeconds", "endSeconds", "durationSeconds", "videoUrl", "thumbnailUrl", "colorMode", "aspectRatio", "score")} for c in cl]
        json.dump(raw, open(RAW, "w")); print(f"{world:14s} {q[:40]:40s} {len(cl)}", flush=True); time.sleep(1.4)
# ---- read every find with CLIP against its own query
import numpy as np, torch, open_clip
from PIL import Image
T = os.path.join(D, "fthumbs"); os.makedirs(T, exist_ok=True)
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
clips = {}
for world, qs in Q.items():
    for q in qs:
        for c in raw.get(q, []):
            if not c.get("thumbnailUrl") or not c.get("videoUrl"): continue
            x = clips.setdefault(c["id"], {**c, "found": []}); x["found"].append([world, q])
need = [c for c in clips.values() if not os.path.exists(os.path.join(T, c["id"] + ".jpg"))]
for k, c in enumerate(need):
    subprocess.run(["curl", "-sfL", "-A", "cineosis-44-research", "-o", os.path.join(T, c["id"] + ".jpg"), c["thumbnailUrl"]])
    if k % 100 == 0: print("thumbs", k, "/", len(need), flush=True)
ids = [i for i in clips if os.path.exists(os.path.join(T, i + ".jpg")) and os.path.getsize(os.path.join(T, i + ".jpg")) > 500]
E = []
for k in range(0, len(ids), 64):
    ims = []
    for i in ids[k:k + 64]:
        try: ims.append(prep(Image.open(os.path.join(T, i + ".jpg")).convert("RGB")))
        except Exception: ims.append(torch.zeros(3, 224, 224))
    with torch.no_grad(): e = m.encode_image(torch.stack(ims)).float()
    E.append((e / e.norm(dim=-1, keepdim=True)).numpy())
E = np.concatenate(E); qs = sorted({q for c in clips.values() for _, q in c["found"]})
with torch.no_grad(): QT = m.encode_text(tok(qs)).float(); QT = (QT / QT.norm(dim=-1, keepdim=True)).numpy()
qi = {q: j for j, q in enumerate(qs)}
out = []
for i, e in zip(ids, E):
    c = clips[i]; s = max(float(e @ QT[qi[q]]) for _, q in c["found"])
    out.append({"id": i, "title": c["sourceTitle"], "year": c["sourceYear"], "dur": c["durationSeconds"], "v": c["videoUrl"], "t": c["thumbnailUrl"], "bw": c["colorMode"],
                "found": c["found"], "fit": round(s, 3)})
np.save(os.path.join(D, "forage-emb.npy"), E.astype(np.float16)); json.dump(ids, open(os.path.join(D, "forage-ids.json"), "w"))
json.dump({"queries": Q, "clips": sorted(out, key=lambda c: -c["fit"])}, open(os.path.join(D, "forage.json"), "w"), ensure_ascii=False)
print("forage.json:", len(out), "clips from", sum(len(v) for v in Q.values()), "queries")
