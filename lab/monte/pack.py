"""Pack the material for the Monte Carlo cinema: every judged shot and archival title card (with CLIP image embeddings, judge scores,
roles, colour), a few thousand spoken lines from the archive's transcripts (with CLIP text embeddings, so a line can be compared with
a picture), and the archive's music (with CLAP mood profiles, so a score can be compared with the words on the cards).
Embeddings are stored as int8 with a scale. Writes monte/material.json.   usage: .venv/bin/python monte/pack.py"""
import json, os, re, base64, random
import numpy as np, torch, open_clip
from PIL import Image
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
q8 = lambda A: base64.b64encode(np.clip(np.round(A / (np.abs(A).max() / 127)), -127, 127).astype(np.int8).tobytes()).decode()
def norm(A): A = np.asarray(A, np.float32); return A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9)
# ---- shots and cards: the judged pool
pool = json.load(open(os.path.join(L, "wes", "judge", "judged.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
lib = json.load(open(os.path.join(L, "markov", "library.json"))); sc = lib["scale"]
E1 = np.fromfile(os.path.join(L, "markov", "emb-openai.bin"), np.int8).reshape(-1, 512).astype(np.float32) * sc
EMB = {s["id"]: e for s, e in zip(lib["shots"], E1)}
for i, e in zip(json.load(open(os.path.join(L, "odyssey", "cache", "ids.json"))), np.load(os.path.join(L, "odyssey", "cache", "emb-openai.npy"))): EMB.setdefault(i, e)
items = [p for p in pool if p["id"] in EMB and p["id"] in V]
def colour(i):
    try: a = np.asarray(Image.open(os.path.join(L, "wes", "judge", "thumbs", i + ".jpg")).convert("HSV").resize((32, 24)), np.float32); return float((a[..., 1] > 40).mean())
    except Exception: return .5
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ctext(ts):
    out = []
    for k in range(0, len(ts), 256):
        with torch.no_grad(): e = m.encode_text(tok(ts[k:k + 256])).float(); out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    return np.concatenate(out) if out else np.zeros((0, 512), np.float32)
shots = [{"i": p["id"], "film": p.get("film"), "year": p.get("year"), "score": p.get("score", 0), "role": p.get("role", "other"), "title": p.get("role") == "title",
          "text": (p.get("text") or "").replace(" [sponsor]", ""), "why": p.get("why"), "colour": round(colour(p["id"]), 2),
          "v": V[p["id"]][0], "dur": None} for p in items]
SE = norm([EMB[p["id"]] for p in items])
cards = [k for k, s in enumerate(shots) if s["title"] and s["text"] and s["score"] >= 5]
CT = ctext([shots[k]["text"].replace(" / ", " ")[:200] for k in cards])      # what each card says, in CLIP's words
# ---- spoken lines: whole short sentences, cleanly heard, from the archive's transcripts
W = json.load(open(os.path.join(L, "odyssey", "cache", "ears", "words.json")))
title = {}
for c in json.load(open(os.path.join(L, "odyssey", "results", "clips.json"))): title[c["id"]] = (c["sourceTitle"], c.get("sourceYear"))
for s in lib["shots"]: title.setdefault(s["id"], (s.get("title"), s.get("year")))
lines = []
for i, v in W.items():
    ws = v.get("words") or []
    if not ws or i not in V or i not in title: continue
    a = 0
    for k, w in enumerate(ws):
        if not re.search(r"[.!?]$", w[0]): continue
        seg = ws[a:k + 1]; a = k + 1
        if not (3 <= len(seg) <= 14): continue
        conf = np.mean([x[3] if len(x) > 3 else .8 for x in seg]); txt = " ".join(x[0] for x in seg)
        if conf < .8 or not txt[:1].isupper() or re.search(r"\d", txt): continue
        dur = seg[-1][2] - seg[0][1]
        if not (.8 < dur < 5.5): continue
        lines.append({"i": i, "t0": round(max(0, seg[0][1] - .12), 2), "t1": round(seg[-1][2] + .25, 2), "text": txt, "film": title[i][0], "year": title[i][1]})
random.seed(7); random.shuffle(lines)
seen, keep = set(), []
for l in lines:                                                    # no more than three lines from any one film
    k = l["film"]; seen.add(k)
    if sum(1 for x in keep if x["film"] == k) < 3: keep.append(l)
    if len(keep) >= 2600: break
LT = ctext([l["text"] for l in keep])
# ---- music: the archive's music clips and their moods (CLAP)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
E = os.path.join(L, "odyssey", "cache", "ears"); eids = json.load(open(os.path.join(E, "ids.json"))); CL = np.load(os.path.join(E, "clap.npy")).astype(np.float32); kind = json.load(open(os.path.join(E, "kind.json")))
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
MOODS = ["whimsical playful music", "a jaunty march", "melancholy slow strings", "suspenseful tense music", "romantic sweeping orchestra", "light jazz", "a gentle lullaby", "a triumphant fanfare"]
with torch.no_grad():
    def clt(ts): e = cm.get_text_features(**cp(text=ts, return_tensors="pt", padding=True)); return (e / e.norm(dim=-1, keepdim=True)).numpy()
    MQ = clt(MOODS); NQ = clt(["a man speaking", "a woman speaking", "noise and static"])
mus = [k for k, i in enumerate(eids) if kind.get(i, {}).get("k") == "music" and i in V and os.path.exists(os.path.join(L, "odyssey", "cache", "aud", i + ".flac"))]
X = norm(CL[mus]); ok = (X @ MQ.T).max(1) - (X @ NQ.T).max(1)
best = [mus[j] for j in np.argsort(-ok)[:400]]; folders, music = set(), []
for k in best:
    f = V[eids[k]][0].split("/clips/")[0]
    if f in folders: continue
    folders.add(f); x = CL[k] / (np.linalg.norm(CL[k]) + 1e-9); prof = (x @ MQ.T)
    music.append({"i": eids[k], "film": title.get(eids[k], ("?", None))[0], "mood": [round(float(v), 3) for v in prof]})
    if len(music) >= 80: break
CM = ctext([MOODS[0]]) * 0                                          # placeholder kept for format symmetry
# card moods (CLAP text of the card's words against the same moods)
with torch.no_grad(): CTM = clt([shots[k]["text"].replace(" / ", " ")[:120] for k in cards]) @ MQ.T
json.dump({"moods": MOODS, "shots": shots, "shotEmb": q8(SE), "cards": cards, "cardText": q8(CT), "cardMood": np.round(CTM, 3).tolist(),
           "lines": keep, "lineEmb": q8(LT), "music": music, "r2": "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/"},
          open(os.path.join(L, "monte", "material.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(shots), "shots ·", len(cards), "cards ·", len(keep), "lines ·", len(music), "music ·", round(os.path.getsize(os.path.join(L, "monte", "material.json")) / 1e6, 1), "MB")
