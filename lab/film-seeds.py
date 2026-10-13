"""Seeds for the explorer's film mode (film-mode.js): a few shots, each with what the lab knows about it and its two kinds of
neighbour, so the film can show, not tell, how the archive is read.
  looks   its nearest shots by picture (CLIP image embeddings, cache/emb.npy), other films only
  sounds  its nearest shots by sound (CLAP, odyssey/cache/ears/clap.npy), other films only
  shared  what the looks-alike shots have in common, in words the machine itself produced (caption words, subjects, decade)
Writes lab/film-seeds.json.   usage: python3 lab/film-seeds.py"""
import json, os, re, collections
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); J = lambda p: json.load(open(os.path.join(H, p)))
shots = J("lab-data.json")["shots"]; by = {s["id"]: s for s in shots}
cap = J("rushes/captions.json") if os.path.exists(os.path.join(H, "rushes/captions.json")) else {}
E = np.load(os.path.join(H, "cache/emb.npy")); eid = J("cache/emb_ids.json"); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9; er = {k: i for i, k in enumerate(eid)}
cid = J("odyssey/cache/ears/ids.json"); CL = np.load(os.path.join(H, "odyssey/cache/ears/clap.npy")).astype(np.float32)
keep = [i for i, k in enumerate(cid) if k in by]; cid = [cid[i] for i in keep]; CL = CL[keep]; CL /= np.linalg.norm(CL, axis=1, keepdims=True) + 1e-9; cr = {k: i for i, k in enumerate(cid)}
# what each clip's own people say (Rushes keeps it)
said = {}
try:
    R = J("rushes/clips.json"); U = J("rushes/utts.json")["utts"]; K = J("rushes/keys.json")["keys"]
    for k, r in zip(K, R["rows"]):
        if r[7] >= 0: said[k] = U[r[7]][3]
except Exception: pass
STOP = set("a an the of in on at with and to is are his her its their there front back side near next large small black white two three some object person screen text people".split())
base = lambda t: re.sub(r"\s*\((part|reel) [ivx\d]+\)|\s*-\s*.*$", "", (t or "").lower()).strip()
words = lambda t: [w for w in re.findall(r"[a-z]+", (t or "").lower()) if w not in STOP and len(w) > 2]
def card(k):
    s = by[k]; sig = (s.get("signs") or [{}])[0]
    return {"id": k, "title": s.get("title"), "year": s.get("year"), "video": s.get("video"), "thumb": s.get("thumb"), "t": max(0, (s.get("read_t") or 0)),
            "caption": cap.get(k, ""), "subjects": [x["label"] for x in (s.get("subjects") or [])[:3]], "sign": sig.get("n"), "note": sig.get("note"),
            "found": ((s.get("found") or [{}])[0]).get("q"), "sound": (s.get("audio") or {}).get("kind"), "said": said.get(k, ""), "scale": s.get("scale")}
def near(M, row, k, n=5):
    i = row[k]; sim = M @ M[i]; out = []; seen = {base(by[k].get("title"))}
    for j in np.argsort(-sim)[1:400]:
        kk = (eid if M is E else cid)[j]
        if kk not in by or base(by[kk].get("title")) in seen or not by[kk].get("video"): continue
        seen.add(base(by[kk].get("title"))); out.append({**card(kk), "sim": round(float(sim[j]), 3)})
        if len(out) == n: break
    return out
def shared(cards):
    c = collections.Counter(w for x in cards for w in set(words(x["caption"]) + [w for s in x["subjects"] for w in words(s)]))
    common = [w for w, n in c.most_common(8) if n >= max(2, len(cards) // 2)][:4]
    decs = sorted({(x["year"] // 10) * 10 for x in cards if x.get("year")})
    return {"words": common, "decades": f"{decs[0]}s–{decs[-1]}s" if len(decs) > 1 else (f"{decs[0]}s" if decs else "")}
# seeds: shots with a sign reading, a caption, a voice or a sound, both embeddings, and different signs and subjects from each other
cands = [s for s in shots if s["id"] in er and s["id"] in cr and s.get("signs") and s["signs"][0].get("note") and cap.get(s["id"]) and s.get("video")
         and (s.get("audio") or {}).get("kind") in ("speech", "sound", "music") and s.get("xy")]
cands.sort(key=lambda s: (-(s["signs"][0].get("conf") or 0), -len(said.get(s["id"], ""))))
seeds, signs, subs = [], set(), set()
for s in cands:
    sg = s["signs"][0]["n"]; sb = ((s.get("subjects") or [{}])[0]).get("label")
    if sg in signs or sb in subs: continue
    signs.add(sg); subs.add(sb)
    looks = near(E, er, s["id"]); sounds = near(CL, cr, s["id"])
    seeds.append({**card(s["id"]), "looks": looks, "sounds": sounds, "looks_shared": shared([card(s["id"])] + looks), "sounds_shared": shared([card(s["id"])] + sounds)})
    if len(seeds) == 5: break
json.dump({"seeds": seeds}, open(os.path.join(H, "film-seeds.json"), "w"), ensure_ascii=False, indent=0)
for x in seeds:
    print(f"{x['title'][:30]:30} {x['year']} sign={x['sign']} sound={x['sound']} | sees: {x['caption'][:50]} | says: {x['said'][:40]}")
    print("   looks:", [y["title"][:18] for y in x["looks"]], x["looks_shared"]); print("   sounds:", [y["title"][:18] for y in x["sounds"]], x["sounds_shared"])
