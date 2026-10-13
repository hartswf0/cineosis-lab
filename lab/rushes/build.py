"""RUSHES. Start from the footage, not a script: every archive clip is a place to stand, and each one offers four ways on.
  KEEP WATCHING  the clip that follows it in its own film (the rush runs on)
  ANSWER         an archival voice that answers what this clip says (or, if it is silent, what it shows): on the subject, and
                 doubting, refusing or asking (no, not, but, why, a question)
  ECHO           the nearest picture from another film (what the lab's films do now, kept so it can be weighed)
  ELSEWHERE      the nearest picture among the image types the lab's films leave out, from clips no film has used
and SAYS: what the clip's own people say in it. All of it is worked out here, so the page needs no model.
Writes rushes/clips.json (one row per clip) and rushes/utts.json (the voices it uses).
usage: lab/.venv/bin/python lab/rushes/build.py"""
import json, os, re, collections
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); OD = os.path.join(L, "odyssey")
J = lambda p: json.load(open(os.path.join(L, p)))
BLOCK = [t.lower() for t in J("curtis/block.json")["titles"]]
blocked = lambda t: any(b in (t or "").lower() for b in BLOCK)
PRE = "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/"

# ---- the archive's utterances and their meaning (the Odyssey's machinery)
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index("# ---- words: Homer's content words said")]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "rushes"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, UV, ulib = G["U"], G["UV"], G["lib"]; UV /= np.linalg.norm(UV, axis=1, keepdims=True) + 1e-9

# ---- every clip with a picture embedding (ViT-B-32 openai), and what is known of it
meta, vec = {}, {}
lab = {s["id"]: s for s in J("lab-data.json")["shots"]}
e = np.load(os.path.join(L, "cache/emb.npy")); ids = J("cache/emb_ids.json")
for k, v in zip(ids, e): vec[k] = v
for libf, binf in (("markov/library.json", "markov/emb.bin"), ("odyssey/library.json", "odyssey/emb.bin")):
    m = J(libf); q = np.fromfile(os.path.join(L, binf), dtype=np.int8).reshape(m["n"], 512).astype(np.float32) * m["scale"]
    for s, v in zip(m["shots"], q):
        if s.get("kind", "archive") != "archive": continue
        vec.setdefault(s["id"], v); meta.setdefault(s["id"], {"video": s["video"], "title": s.get("title"), "year": s.get("year"), "src": s.get("src"), "st": s.get("st") or 0, "dur": s.get("dur") or 0})
for k, s in lab.items():
    meta.setdefault(k, {"video": s["video"], "title": s.get("title"), "year": s.get("year"), "src": s.get("slug"), "st": s.get("start") or 0, "dur": (s.get("end") or 0) - (s.get("start") or 0)})
keys = [k for k in vec if k in meta and meta[k]["video"] and not blocked(meta[k]["title"])]
X = np.stack([vec[k] for k in keys]).astype(np.float32); X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
row = {k: i for i, k in enumerate(keys)}; N = len(keys); print(N, "clips", flush=True)
srcid = lambda k: (re.search(r"/sources/([^/]+)/", meta[k]["video"]) or [None, meta[k]["src"]])[1]
SRC = [srcid(k) for k in keys]

# ---- image types (the Recurring Cast's vocabulary) and how often the lab's films used each clip
opsrc = open(os.path.join(L, "census/operations.py")).read(); Gt = {}; exec(opsrc[opsrc.index("TYPES = {"): opsrc.index("import open_clip")], Gt)
TYPES = Gt["TYPES"]; names = list(TYPES)
import open_clip, torch
model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32")
with torch.no_grad(): T = model.encode_text(tok([f"a film still of {TYPES[k]}" for k in names])).float().numpy()
T /= np.linalg.norm(T, axis=1, keepdims=True); S = X @ T.T; TY = ((S - S.mean(0)) / (S.std(0) + 1e-9)).argmax(1)
ratio = {t["type"]: t["ratio"] for t in J("census/operations.json")["types"]}
UNDER = np.array([ratio.get(names[t]) is not None and ratio[names[t]] <= .7 for t in TY])
END = np.isin(TY, [names.index("text card"), names.index("black / blank")])
used = collections.Counter(u["clip"] for u in J("census/uses.json") if u["clip"])
USED = np.array([used.get(k, 0) for k in keys])

# ---- keep watching: the clip that carries straight on in the same film
bysrc = collections.defaultdict(list)
for i, k in enumerate(keys): bysrc[SRC[i]].append(i)
NEXT = np.full(N, -1)
for s, rs in bysrc.items():
    rs.sort(key=lambda i: meta[keys[i]]["st"])
    for a, b in zip(rs, rs[1:]):
        gap = meta[keys[b]]["st"] - (meta[keys[a]]["st"] + meta[keys[a]]["dur"])
        if -1.5 <= gap <= 2.5 and not END[b]: NEXT[a] = b

# ---- echo and elsewhere: picture neighbours from other films
ECHO = np.full((N, 3), -1); ELSE = np.full((N, 3), -1)
cand_else = np.where(UNDER & (USED == 0) & ~END)[0]
for a in range(0, N, 2000):
    sim = X[a:a + 2000] @ X.T
    for j, i in enumerate(range(a, min(N, a + 2000))):
        s = sim[j]; o = np.argsort(-s)
        got, seen = [], {SRC[i]}
        for c in o[1:200]:
            if SRC[c] in seen or END[c]: continue
            seen.add(SRC[c]); got.append(c)
            if len(got) == 3: break
        ECHO[i, :len(got)] = got
        se = s[cand_else]; o2 = cand_else[np.argsort(-se)[:40]]; got, seen = [], {SRC[i]}
        for c in o2:
            if SRC[c] in seen: continue
            seen.add(SRC[c]); got.append(c)
            if len(got) == 3: break
        ELSE[i, :len(got)] = got
print("echo, elsewhere", flush=True)

# ---- the voices: whole, clean sentences, 1.2 to 9 s
good = [k for k, (i, t0, t1, text, n, conf, whole, cold) in enumerate(U)
        if whole and not cold and conf >= .72 and 1.2 <= t1 - t0 <= 9 and 4 <= n <= 28 and i in row and not re.search(r"\b(fuck|shit)\b", text, re.I)]
GV = UV[good]; GCLIP = np.array([row[U[k][0]] for k in good]); GSRC = [SRC[c] for c in GCLIP]
DOUBT = re.compile(r"\b(no|not|never|nobody|nothing|none|cannot|can't|don't|didn't|won't|wasn't|isn't|aren't|weren't|couldn't|wouldn't|but|why|wrong|afraid|lie|lies|failed|fail|instead|nowhere|doubt|lost|without)\b|\?", re.I)
GD = np.array([.08 if DOUBT.search(U[k][3]) else -.12 for k in good], np.float32)
print(len(good), "voices", flush=True)
says = {}   # the clip's own best sentence
for gi, k in enumerate(good):
    c = GCLIP[gi]; i0, t0, t1, text = U[k][:4]
    if c not in says or (t1 - t0) > (U[good[says[c]]][2] - U[good[says[c]]][1]): says[c] = gi
ANS = np.full((N, 3), -1)
GX = X[GCLIP]   # each voice's own picture
for a in range(0, N, 1000):
    rs = list(range(a, min(N, a + 1000)))
    img = X[rs] @ GX.T                                  # what the clip shows, against what each voice's clip shows
    spk = [says.get(i) for i in rs]
    txt = np.zeros_like(img)
    have = [j for j, g in enumerate(spk) if g is not None]
    if have: txt[have] = GV[[spk[j] for j in have]] @ GV.T   # what the clip says, against what each voice says
    for j, i in enumerate(rs):
        sc = (txt[j] if spk[j] is not None else 1.6 * img[j] - .35) + GD
        o = np.argsort(-sc)[:60]; got, seen = [], {SRC[i]}
        for g in o:
            if GSRC[g] in seen or (spk[j] is not None and U[good[g]][3].lower() == U[good[spk[j]]][3].lower()): continue
            seen.add(GSRC[g]); got.append(g)
            if len(got) == 3: break
        ANS[i, :len(got)] = got
print("answers", flush=True)

# ---- write: voices referenced, then clips
need = sorted({int(g) for g in ANS.flatten() if g >= 0} | set(says.values()))
ui = {g: n for n, g in enumerate(need)}
short = lambda v: v[len(PRE):] if v.startswith(PRE) else v
utts = [[ui and short(meta[keys[GCLIP[g]]]["video"]), U[good[g]][1], U[good[g]][2], U[good[g]][3]] + [int(GCLIP[g])] for g in need]
rows = []
for i, k in enumerate(keys):
    m = meta[k]
    rows.append([short(m["video"]), (m["title"] or "")[:72], m["year"], round(m["dur"], 1), int(TY[i]), int(USED[i]), int(NEXT[i]),
                 ui[says[i]] if i in says else -1, [int(x) for x in ECHO[i] if x >= 0], [int(x) for x in ELSE[i] if x >= 0], [ui[int(x)] for x in ANS[i] if x >= 0]])
starts = [i for i, r in enumerate(rows) if r[7] >= 0 and r[6] >= 0 and len(r[10]) == 3 and len(r[9]) and not END[i] and r[3] >= 4]
json.dump({"pre": PRE, "types": names, "cols": ["video", "title", "year", "dur", "type", "used", "next", "says", "echo", "else", "ans"], "rows": rows, "starts": starts},
          open(os.path.join(H, "clips.json"), "w"), ensure_ascii=False, separators=(",", ":"))
json.dump({"pre": PRE, "cols": ["video", "t0", "t1", "s", "clip"], "utts": utts}, open(os.path.join(H, "utts.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(N, "clips ·", len(utts), "voices ·", len(starts), "good starts ·", os.path.getsize(os.path.join(H, "clips.json")) // 1024, "KB +", os.path.getsize(os.path.join(H, "utts.json")) // 1024, "KB")
for i in starts[:3]:
    r = rows[i]; print(" ", r[1], "| says:", utts[r[7]][3][:60], "| answer:", utts[r[10][0]][3][:60], "| echo:", rows[r[8][0]][1][:30], "| else:", rows[r[9][0]][1][:30], names[rows[r[9][0]][4]])
