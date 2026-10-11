"""MARKOV SAM · REPUBLIC: forage the Moving Image Archive for what the Republic's seventeen worlds need and the lab's archive lacks
(robots, oil rigs, football, the Alamo, barbecue, rodeo, rockets, board rooms, server rooms, dinosaurs...). One search at a time (the
archive rate-limits), resumable: republic/cache/raw.json keeps each answer. Then each new clip's thumbnail is read by CLIP (openai
ViT-B/32, the same space as odyssey/cache/emb-openai.npy) so it can be matched beside the old archive.
Writes republic/cache/clips.json and republic/cache/emb-openai.npy.   usage: .venv/bin/python republic/forage.py"""
import json, os, sys, time, io, urllib.request, urllib.error, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(H, "cache"); os.makedirs(C, exist_ok=True)
sys.path.insert(0, os.path.join(os.path.dirname(H), "odyssey"))
from forage import search, KEEP, GAP   # the Odyssey's own polite searcher (waits out 429s and network drops)
Q = """robot walking 1939 world's fair|mechanical man robot|toy robot tin|industrial robot arm factory|automaton
oil derrick west texas|oil rig pumpjack field|oil gusher|refinery at night|abandoned gas station desert
football practice tackling dummy|football coach on sideline|high school football game crowd|football locker room|cheerleaders stadium
school cafeteria lunch line|cafeteria workers serving food|vending machine
the alamo san antonio|texas capitol building austin|texas flag waving|governor speech podium|politician giving speech crowd
barbecue pit smoking meat|cattle ranch roundup|cowboys on horseback|rodeo bronco|ranch gate fence|longhorn cattle|goat on farm|cow close up
desert sand dunes wind|red rock desert canyon|dust storm|tumbleweed|lone highway desert|salt flats
rocket launch|astronaut space suit|planet mars surface|space station model|science fiction spaceship|flying saucer
geodesic dome|greenhouse plants|futuristic city model|world's fair futurama|monorail
office conference room meeting|office workers typing pool|board of directors meeting table|filing cabinets office|fluorescent office
suburban kitchen housewife 1950s|model home tour|gated community suburb houses|television family living room
map room war room|globe spinning|ruler and blueprint drafting|waiter serving tray hotel
wrestling match arena|boxing match crowd|beauty pageant runway|game show host|television studio cameras|nightclub stage spotlight
cave entrance darkness|shadows on wall puppet|projector beam dark room|prison cell bars|handcuffs police
mainframe computer room|punch card machine|television monitors control room|warehouse workers|data center tape drives
dinosaur stop motion|tyrannosaurus|jeep in desert|monster truck|motorcycle gang|military convoy desert
gorilla zoo|marching band|parade float|crowd cheering stadium|man in cowboy hat close up|old woman portrait|young man portrait|soldier helmet
vault door bank|underground bunker corridor|fallout shelter|zombie movie|scientist laboratory|statue greek marble|philosopher statue|toga actors greek play""".replace("\n", "|").split("|")
raw = json.load(open(os.path.join(C, "raw.json"))) if os.path.exists(os.path.join(C, "raw.json")) else {}
todo = [q.strip() for q in Q if q.strip() and q.strip() not in raw]
print(len(Q), "searches ·", len(todo), "to go", flush=True)
for n, q in enumerate(todo):
    raw[q] = [{k: c.get(k) for k in KEEP} for c in search(q)]
    if n % 10 == 0: json.dump(raw, open(os.path.join(C, "raw.json"), "w")); print(f"  {n}/{len(todo)} {q} → {len(raw[q])}", flush=True)
    time.sleep(GAP)
json.dump(raw, open(os.path.join(C, "raw.json"), "w"))
clips = {}
for q, cs in raw.items():
    for r, c in enumerate(cs):
        if not c.get("videoUrl") or not c.get("thumbnailUrl"): continue
        x = clips.setdefault(c["id"], {"id": c["id"], "title": c.get("sourceTitle") or "", "year": c.get("sourceYear"), "video": c["videoUrl"], "thumb": c["thumbnailUrl"],
                                        "in": c.get("matchTimestampSeconds") or 0, "st": c.get("startSeconds"), "dur": c.get("durationSeconds"), "color": c.get("colorMode"), "q": []})
        x["q"].append([q, r])
ids = list(clips); print(len(ids), "clips", flush=True)
import numpy as np, torch, open_clip
from PIL import Image
EP = os.path.join(C, "emb-openai.npy"); IP = os.path.join(C, "emb-ids.json")
have = dict(zip(json.load(open(IP)), np.load(EP))) if os.path.exists(EP) else {}
need = [i for i in ids if i not in have]
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval()
def get(i):
    try: return i, Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(clips[i]["thumb"], headers={"User-Agent": "cineosis-44-research"}), timeout=30).read())).convert("RGB")
    except Exception: return i, None
with cf.ThreadPoolExecutor(8) as ex:
    for k in range(0, len(need), 64):
        got = [(i, im) for i, im in ex.map(get, need[k:k + 64]) if im is not None]
        if got:
            with torch.no_grad(): v = m.encode_image(torch.stack([pre(im) for _, im in got])).float(); v = (v / v.norm(dim=-1, keepdim=True)).numpy()
            for (i, _), e in zip(got, v): have[i] = e
        print(f"  read {min(k + 64, len(need))}/{len(need)}", flush=True)
ok = [i for i in ids if i in have]
np.save(EP, np.stack([have[i] for i in ok]).astype(np.float16)); json.dump(ok, open(IP, "w"))
json.dump({i: clips[i] for i in ok}, open(os.path.join(C, "clips.json"), "w"), ensure_ascii=False)
print(len(ok), "clips read and kept")
