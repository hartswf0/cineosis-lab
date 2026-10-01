"""The steersman's instruments. For every shot of every scene and every possibility in its sea, how well the picture answers
  line     the words spoken while it is on screen (the voice, aligned)
  beat     the beat of the scene it belongs to
  sign     the scene's cinematic sign: its operation, what the sign asks the image to do
  role     the shot's role (WIDE MID CLOSE OBJ EMPTY)
each as a percentile against every possibility in the whole Odyssey (so 80 means better than 80% of all candidates), and a
combined confidence. Also a contact sheet per scene (each shot beside its five strongest possibilities, the words over it) for
the visual critic, and the blend partner a scene's sign asks for (recollection, dream, the marked past) or none.
Writes cache/steer-inst.json and cache/steer-sheets/<scene>.jpg.   usage: ../.venv/bin/python steer_build.py"""
import json, os, textwrap
import numpy as np, torch, open_clip
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); SH = os.path.join(H, "cache", "steer-sheets"); os.makedirs(SH, exist_ok=True)
books = [json.load(open(os.path.join(H, "sea", f))) for f in sorted(os.listdir(os.path.join(H, "sea"))) if f.startswith("b")]
scenes = {s["id"]: s for s in json.load(open(os.path.join(H, "scenes.json")))["scenes"]}
ids = json.load(open(os.path.join(H, "cache", "ids.json"))); X = np.load(os.path.join(H, "cache", "emb-openai.npy")).astype(np.float32); row = {i: n for n, i in enumerate(ids)}
M = os.path.join(os.path.dirname(H), "markov"); ml = json.load(open(os.path.join(M, "library.json")))
MX = np.fromfile(os.path.join(M, "emb.bin"), np.int8).reshape(-1, 512).astype(np.float32) * ml["scale"]; mrow = {s["id"]: n for n, s in enumerate(ml["shots"])}
def vec(i):
    if i in row: return X[row[i]]
    if i in mrow: v = MX[mrow[i]]; return v / (np.linalg.norm(v) + 1e-6)
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
cache = {}
def enc(ts):
    miss = [t for t in dict.fromkeys(ts) if t not in cache]
    for i in range(0, len(miss), 200):
        with torch.no_grad(): e = m.encode_text(tok(miss[i:i + 200])).float(); e = (e / e.norm(dim=-1, keepdim=True)).numpy()
        for t, v in zip(miss[i:i + 200], e): cache[t] = v
    return np.array([cache[t] for t in ts]) if ts else np.zeros((0, 512), np.float32)
ROLE = {"EMPTY": "an empty place with no people", "WIDE": "a wide view of a place", "MID": "people doing something", "CLOSE": "a close-up of a face", "OBJ": "a close-up of an object"}
BLEND_SIGNS = {"Sd": "a marked memory of the past", "Sp": "the past as layers", "Rd": "a dream", "Rs": "a dream", "Wd": "a memory", "Pf": "a lie and its truth at once", "Lo": "a disguise and the face beneath", "Cr": "a mirror of the present and past"}
raw = []                                           # every (scene, shot, candidate) reading, to turn into percentiles
plan = {}
for b in books:
    for s in b["scenes"]:
        sc = scenes.get(s["id"], {}); op = (s.get("sign") or {}).get("operation") or ""; beats = [x["text"] for x in sc.get("beats", [])]
        nshot = len(s["shots"])
        for k, sh in enumerate(s["shots"]):
            lines = [u["text"] for u in s["subs"] if u["t1"] > sh["t0"] and u["t0"] < sh["t0"] + sh["dur"] and u["kind"] != "SCENE_HEADER"]
            beat = beats[min(len(beats) - 1, int(k / max(1, nshot) * len(beats)))] if beats else s["title"]
            cands = [sh] + sh.get("sea", [])
            L = enc([" ".join(lines)[:300]]) if lines else None; Bv = enc([beat]); Sv = enc([op]) if op else None; Rv = enc([ROLE.get(sh.get("role"), "a scene")])
            for c, cand in enumerate(cands):
                v = vec(cand["id"])
                if v is None: continue
                raw.append((s["id"], k, c, cand["id"], float(L[0] @ v) if L is not None else None, float(Bv[0] @ v), float(Sv[0] @ v) if Sv is not None else None, float(Rv[0] @ v)))
            plan[(s["id"], k)] = {"lines": lines, "beat": beat}
A = np.array([[r[4] if r[4] is not None else np.nan, r[5], r[6] if r[6] is not None else np.nan, r[7]] for r in raw], np.float32)
P = np.zeros_like(A)
for j in range(4):                                 # percentile against every possibility in the Odyssey
    col = A[:, j]; ok = ~np.isnan(col); order = np.argsort(np.argsort(col[ok])); P[ok, j] = order / max(1, ok.sum() - 1); P[~ok, j] = np.nan
W = np.array([.4, .25, .2, .15])
inst = {}
for r, p in zip(raw, P):
    w = W * ~np.isnan(p); conf = float(np.nansum(p * W) / w.sum()) if w.sum() else 0
    inst.setdefault(r[0], {}).setdefault(str(r[1]), {})[r[3]] = {"c": round(conf * 100), "line": None if np.isnan(p[0]) else round(float(p[0]) * 100), "beat": round(float(p[1]) * 100), "sign": None if np.isnan(p[2]) else round(float(p[2]) * 100), "role": round(float(p[3]) * 100)}
# blend: only where the sign asks for layered time, with the partner that best carries what it asks for
for b in books:
    for s in b["scenes"]:
        sym = (s.get("sign") or {}).get("symbol"); secs = [x for x in (scenes.get(s["id"], {}).get("secondary") or []) if x]
        ask = BLEND_SIGNS.get(sym) or next((BLEND_SIGNS[x] for x in secs if x in BLEND_SIGNS), None)
        for k, sh in enumerate(s["shots"]):
            if not ask: continue
            av = enc([ask])[0]; best = max((c for c in sh.get("sea", []) if vec(c["id"]) is not None), key=lambda c: float(vec(c["id"]) @ av), default=None)
            if best: inst[s["id"]].setdefault("_blend", {})[str(k)] = {"id": best["id"], "why": f"{sym if sym in BLEND_SIGNS else 'a secondary sign'} asks for {ask}", "amt": 35 if sym in BLEND_SIGNS else 22}
json.dump(inst, open(os.path.join(H, "cache", "steer-inst.json"), "w"), separators=(",", ":"))
# contact sheets for the visual critic
F = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13); FB = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 14)
TH = os.path.join(H, "thumbs"); MT = os.path.join(os.path.dirname(H), "thumbs")
def thumb(i):
    for p in (os.path.join(TH, i + ".jpg"), os.path.join(MT, i + ".jpg")):
        if os.path.exists(p):
            try: return Image.open(p).convert("RGB")
            except Exception: pass
for b in books:
    for s in b["scenes"]:
        W_, T_ = 200, 150; rows = len(s["shots"]); im = Image.new("RGB", (W_ * 6 + 8, 64 + rows * (T_ + 58)), (14, 14, 14)); d = ImageDraw.Draw(im)
        sg = s.get("sign") or {}
        d.text((6, 6), f"{s['id']}  {s['title']}  ·  sign {sg.get('symbol')} {sg.get('name')}  ·  palette {s.get('palette')}", font=FB, fill=(232, 192, 112))
        d.text((6, 26), textwrap.shorten("SIGN ASKS: " + (sg.get("operation") or ""), 190), font=F, fill=(200, 200, 200)); d.text((6, 44), textwrap.shorten("WORLD: " + (s.get("world") or ""), 190), font=F, fill=(160, 160, 160))
        for k, sh in enumerate(s["shots"]):
            y = 64 + k * (T_ + 58); pl = plan[(s["id"], k)]; ins = inst.get(s["id"], {}).get(str(k), {})
            d.text((6, y), textwrap.shorten(f"SHOT {k + 1} · {sh.get('role')} · {sh['dur']:.1f}s · MUST SHOW: {sh.get('see')}", 200), font=FB, fill=(196, 244, 106))
            d.text((6, y + 18), textwrap.shorten("WORDS OVER IT: " + (" / ".join(pl["lines"]) or "(no words: music and the archive's sound)"), 210), font=F, fill=(220, 214, 200))
            cands = [sh] + sh.get("sea", [])
            top = [cands[0]] + sorted(cands[1:], key=lambda c: -(ins.get(c["id"], {}).get("c") or 0))[:5]
            for c, cand in enumerate(top):
                t = thumb(cand["id"])
                if t: t.thumbnail((W_ - 6, T_ - 4)); im.paste(t, (c * W_ + 4, y + 38))
                cc = ins.get(cand["id"], {}).get("c")
                d.rectangle([c * W_ + 4, y + 38, c * W_ + 92, y + 56], fill=(0, 0, 0)); d.text((c * W_ + 7, y + 39), ("NOW " if c == 0 else f"#{c} ") + (f"{cc}%" if cc is not None else ""), font=FB, fill=(255, 255, 255) if c else (232, 192, 112))
            s.setdefault("_sheet_order", {})[str(k)] = [x["id"] for x in top]
        im.save(os.path.join(SH, s["id"] + ".jpg"), quality=80)
json.dump({s["id"]: s["_sheet_order"] for b in books for s in b["scenes"]}, open(os.path.join(H, "cache", "steer-order.json"), "w"))
print("readings", len(raw), "· scenes", len(inst), "· blend asked in", sum(1 for v in inst.values() if "_blend" in v), "scenes · sheets", len(os.listdir(SH)))
