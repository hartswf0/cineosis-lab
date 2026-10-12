"""THE TALK-BACK DESK. A narration in the Curtis manner (locate, explain, turn, connect), and for every line four answers from the archive:
  MATCH      the picture nearest the words (what every lab film does now; shown so the others can be weighed against it)
  TURN       an archival voice on the same subject that doubts, refuses or asks: the archive answering back in its own sound
  LONG       the matched picture left running: the clips after it in its own source film, while they continue (the rush)
  ELSEWHERE  the nearest picture among the image types the lab's films leave out, and only clips no film has used
Writes curtis/rows.json (every archive clip: where it sits in its source, its image type, how often the films used it; for live asking
in the page) and curtis/film.json (the default essay, answered), and renders the default narration with Kokoro.
usage: lab/.venv/bin/python lab/curtis/build.py   then   lab/republic/.tts/bin/python lab/curtis/build.py --voice"""
import json, os, re, sys, collections, subprocess
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
J = lambda p: json.load(open(os.path.join(L, p)))
ESSAY = J("curtis/essay.json")

if "--voice" in sys.argv:   # the narrator: a woman's voice, against the archive's 51 men to 9 women
    from kokoro import KPipeline
    import soundfile as sf
    P = KPipeline(lang_code="b", repo_id="hexgrad/Kokoro-82M"); os.makedirs(os.path.join(H, "narr"), exist_ok=True)
    for i, ln in enumerate(ESSAY["lines"]):
        wav = os.path.join(H, "narr", f"{i:02d}.wav"); m4a = wav[:-3] + "m4a"
        a = np.concatenate([np.asarray(x, np.float32) for _, _, x in P(ln["text"], voice=ESSAY.get("voice", "bf_emma"), speed=.92)])
        sf.write(wav, np.concatenate([a, np.zeros(int(24000 * .25), np.float32)]), 24000)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "96k", m4a]); os.unlink(wav)
    film = J("curtis/film.json")
    for i, ln in enumerate(film["lines"]):
        p = os.path.join(H, "narr", f"{i:02d}.m4a")
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
        ln["narr"] = {"f": f"curtis/narr/{i:02d}.m4a", "d": round(d, 2)}
    json.dump(film, open(os.path.join(H, "film.json"), "w"), ensure_ascii=False, separators=(",", ":")); print("narration rendered"); sys.exit()

# ---- every archive clip the in-page reader can search (markov/emb.bin rows), with its type, its use, its place in its source
lib = J("markov/library.json"); M = np.fromfile(os.path.join(L, "markov/emb.bin"), dtype=np.int8).reshape(lib["n"], 512).astype(np.float32) * lib["scale"]
M /= np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
shots = lib["shots"]
BLOCK = [t.lower() for t in json.load(open(os.path.join(H, "block.json")))["titles"]]   # sources kept off this desk (e.g. children unclothed)
arch = [i for i, s in enumerate(shots) if s["kind"] == "archive" and not any(b in (s.get("title") or "").lower() for b in BLOCK)]
src = open(os.path.join(L, "census/operations.py")).read()
G = {}; exec(src[src.index("TYPES = {"): src.index("import open_clip")], G); TYPES = G["TYPES"]; names = list(TYPES)
import open_clip, torch
model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32")
def text(ts):
    with torch.no_grad(): t = model.encode_text(tok(ts)).float().numpy()
    return t / np.linalg.norm(t, axis=1, keepdims=True)
T = text([f"a film still of {TYPES[k]}" for k in names]); S = M[arch] @ T.T; Z = (S - S.mean(0)) / (S.std(0) + 1e-9)
typ = dict(zip(arch, Z.argmax(1).tolist()))
ops = J("census/operations.json"); ratio = {t["type"]: t["ratio"] for t in ops["types"]}
UNDER = [names.index(k) for k in names if ratio.get(k) is not None and ratio[k] <= .7]
used = collections.Counter(u["clip"] for u in J("census/uses.json") if u["clip"])
bysrc = collections.defaultdict(list)
for i in arch: bysrc[shots[i]["src"]].append(i)
nxt = {}
for s, rows in bysrc.items():
    rows.sort(key=lambda i: shots[i].get("st") or 0)
    for a, b in zip(rows, rows[1:]):
        gap = (shots[b].get("st") or 0) - ((shots[a].get("st") or 0) + (shots[a].get("dur") or 0))
        if -1.5 <= gap <= 2.5: nxt[a] = b   # the next clip carries straight on from this one
rows = [[i, shots[i]["video"], (shots[i].get("title") or "")[:70], shots[i].get("year"), round(shots[i].get("dur") or 0, 1), typ[i], used.get(shots[i]["id"], 0), nxt.get(i, -1)] for i in arch]
json.dump({"types": names, "under": UNDER, "cols": ["row", "video", "title", "year", "dur", "type", "used", "next"], "rows": rows},
          open(os.path.join(H, "rows.json"), "w"), ensure_ascii=False, separators=(",", ":"))
R = {r[0]: r for r in rows}
cand = lambda i, sc: {"row": i, "v": R[i][1], "ti": R[i][2], "y": R[i][3], "d": R[i][4], "type": names[R[i][5]], "used": R[i][6], "s": round(float(sc), 3)}
END = {names.index("text card"), names.index("black / blank")}   # a run neither starts nor continues on credits or darkness
def chain(i, cap=48):
    out, t = [i], R[i][4]
    while R[out[-1]][7] >= 0 and R[out[-1]][7] in R and R[R[out[-1]][7]][5] not in END and t < cap and len(out) < 8: out.append(R[out[-1]][7]); t += R[out[-1]][4]
    return out
def top(sc, k, keep=lambda i: True):
    out, seen = [], collections.Counter()
    for j in np.argsort(-sc):
        i = arch[j]
        if not keep(i): continue
        t = R[i][2].lower()
        if seen[t] >= 1: continue
        seen[t] += 1; out.append(cand(i, sc[j]))
        if len(out) >= k: break
    return out

# ---- the voices: the Norse bank (12,000 whole sentences, the speaker's own sound), asked exactly as the page asks it
VO = J("norse/voices.json"); WM = J("norse/wordmap.json"); VD = 128
vb = np.fromfile(os.path.join(L, "norse/voices.bin"), dtype=np.int8); nW = len(WM["words"])
VW = vb[: nW * VD].reshape(nW, VD).astype(np.float32); VU = vb[nW * VD:].reshape(-1, VD).astype(np.float32)
STOP = set("a an the and or but of to in on at by for with from off onto near around through across behind front toward towards above below beside as is are was were be been it its this that these those i you he she we they me him her us them my your his our their not no so if then than there here what who which when where how all any some one into out up down over under very can will just do did does have has had am would should could may might must oh yeah okay well also about like know think get got really thing things kind sort lot little much many more most way even still back right".split())
norm = lambda w: re.sub(r"[^a-z]", "", w.lower())
variants = lambda w: [w, re.sub("ies$", "y", w), re.sub("es$", "", w), re.sub("s$", "", w), re.sub("ing$", "", w), re.sub("ing$", "e", w), re.sub("ed$", "", w), re.sub("ed$", "e", w)]
stem = lambda w: re.sub("(ing|ed|es|s)$", "", w) if len(w) > 4 else w
WIDX = {w: i for i, w in enumerate(WM["words"])}
UW = [set(stem(w) for w in (norm(x) for x in u["s"].split()) if len(w) > 2 and w not in STOP) for u in VO["utts"]]
DOUBT = re.compile(r"\b(no|not|never|nobody|nothing|none|cannot|can't|don't|didn't|won't|wasn't|isn't|aren't|weren't|couldn't|wouldn't|but|why|wrong|afraid|lie|lies|failed|fail|instead|nowhere|doubt|lost|without)\b|\?", re.I)
TAKEN_V, TAKEN_R = set(), set()   # across the essay, nothing answers twice
def voices(line, k=4):
    ws = [w for w in (norm(x) for x in line.split()) if len(w) > 2 and w not in STOP]
    gi = [next((WIDX[v] for v in variants(w) if v in WIDX), None) for w in ws]; got = [w for w, g in zip(ws, gi) if g is not None]; gi = [g for g in gi if g is not None]
    if not gi: return []
    q = VW[gi].sum(0); qn = np.linalg.norm(q) * 127 or 1; st = set(map(stem, got))
    topic = (VU @ q) / qn + .4 * np.array([len(w & st) for w in UW]) / max(1, len(st))
    turn = topic + np.array([.12 if DOUBT.search(u["s"]) else -.2 for u in VO["utts"]])   # on the subject, and saying no, not, but, why
    out = []
    for j in np.argsort(-turn)[:k * 4]:
        u = VO["utts"][j]
        if u["s"].lower() in TAKEN_V or len(out) >= k or any(b in (u["ti"] or "").lower() for b in BLOCK): continue
        if not out: TAKEN_V.add(u["s"].lower())
        out.append({"v": u["v"], "t0": u["t0"], "t1": u["t1"], "s": u["s"], "ti": u["ti"], "y": u["y"], "vc": u.get("vc"), "wy": u.get("wy"), "topic": round(float(topic[j]), 3)})
    return out

Q = text([ln["text"] for ln in ESSAY["lines"]]); SC = M[arch] @ Q.T
film = {"title": ESSAY["title"], "sub": ESSAY["sub"], "types": names, "under": [names[i] for i in UNDER], "lines": []}
DEFAULT = {"locate": "long", "explain": "match", "turn": "turn", "connect": "elsewhere"}
for li, ln in enumerate(ESSAY["lines"]):
    sc = SC[:, li]
    match = top(sc, 4, keep=lambda i: i not in TAKEN_R)
    lng, best = [], 0
    for c in top(sc, 12, keep=lambda i: i not in TAKEN_R and R[i][5] not in END):   # the near match whose own film runs on longest
        ch = chain(c["row"]); d = sum(R[i][4] for i in ch)
        if d > best: best, lng = d, [cand(i, sc[arch.index(i)]) for i in ch]
    else_ = top(sc, 4, keep=lambda i: R[i][5] in UNDER and R[i][6] == 0 and i not in TAKEN_R and R[i][2] != match[0]["ti"])
    TAKEN_R.update(x["row"] for x in match[:1] + lng + else_[:1])
    film["lines"].append({"move": ln["move"], "text": ln["text"], "lane": ln.get("lane") or DEFAULT[ln["move"]],
                          "lanes": {"match": match, "turn": voices(ln["text"]), "long": lng, "elsewhere": else_}})
    print(f"[{ln['move']:7}] {ln['text'][:60]}\n   MATCH {match[0]['ti'][:40]} · LONG {len(lng)} clips {sum(x['d'] for x in lng):.0f}s · ELSE {else_[0]['ti'][:30]} ({else_[0]['type']}) · TURN “{(film['lines'][-1]['lanes']['turn'] or [{'s': '-'}])[0]['s'][:70]}”")
json.dump(film, open(os.path.join(H, "film.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(rows), "rows ·", os.path.getsize(os.path.join(H, "rows.json")) // 1024, "KB")
