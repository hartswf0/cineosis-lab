"""The spoken Odyssey: each line answered by whole things archival people said, delivered as speech, not stitched from syllables.
The archive's transcripts are cut into utterances where the speaker cut them (a sentence's end, a held breath, or for long sentences
a comma), each opening and closing inside the speaker's own silence so no word is clipped. A line of Homer (or, if it is long, each of
its clauses, at most three) is given the one utterance that best says it:
  meaning   sentence embedding (all-mpnet-base-v2) of the line against the utterance
  words     how many of Homer's content words it says, or says in kind (inflection, WordNet synonym, one step broader)
  delivery  a whole sentence over a fragment; not begun before the clip begins; about as long as the line takes to say;
            a woman's voice for Athena, Penelope and the other women, a man's for the men (CLAP), when the archive allows
  seams     a voice whose recording sounds like the one before it (CLAP) joins better and is preferred
  casting   a character keeps the archival voice it already has in the scene; another character's voice costs; an utterance
            already used anywhere costs more
The player breathes between utterances. Adds modes.spoken to found.json.   usage: ../.venv/bin/python spoken_odyssey.py"""
import glob, json, os, re, hashlib
import numpy as np, torch
from nltk.corpus import wordnet as wn
from transformers import AutoTokenizer, AutoModel
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears")
words = json.load(open(os.path.join(E, "words.json")))
for f in glob.glob(os.path.join(E, "words.*.json")): words.update(json.load(open(f)))   # workers still transcribing
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that these those i you he she we they me him her us them my your his our their not no so if then than there here what who whom which when where how all any some one into out up down over under again very can will just do did does have has had am shall would should could may might must o oh let now upon thy thee thou ye".split())
# ---- the archive's utterances
U = []   # (clip, t0, t1, text, nwords, conf, whole, cold)
for i, v in words.items():
    ws = [w for w in (v.get("words") or []) if norm(w[0])]
    if len(ws) < 3 or i not in lib: continue
    def emit(a, b, whole):
        seg = ws[a:b]; n = len(seg)
        if n < 3 or n > 34: return
        s0, s1 = seg[0][1], seg[-1][2]; dur = s1 - s0
        if dur < .9 or dur > 12 or not (1.1 <= n / dur <= 5.2): return
        conf = float(np.mean([w[3] if len(w) > 3 else .8 for w in seg]))
        if conf < .6: return
        pe = ws[a - 1][2] if a > 0 else 0.0; ns = ws[b][1] if b < len(ws) else s1 + .6
        t0 = max(0.0, s0 - min(.22, max(.03, (s0 - pe) * .5))); t1 = s1 + min(.32, max(.05, (ns - s1) * .5))
        cold = a == 0 and s0 < .25                              # the clip may begin mid-sentence
        cut = b == len(ws) and s1 > 29.2 and not re.search(r"[.!?]$", seg[-1][0])   # ran past the 30 s we heard
        if cut: return
        w0 = seg[0][0].lstrip("\"'(¿¡")
        begins = bool(w0[:1].isupper()) and (a == 0 or bool(re.search(r"[.!?]$", ws[a - 1][0])) or s0 - pe > .75)
        ends = bool(re.search(r"[.!?]$", seg[-1][0])) or (norm(seg[-1][0]) not in STOP and not re.search(r"[,;:]$", seg[-1][0]))
        U.append((i, round(t0, 2), round(t1, 2), " ".join(w[0] for w in seg), n, conf, whole and begins, cold or not begins or not ends))
    a = 0
    ABBR = {"mr.", "mrs.", "ms.", "dr.", "st.", "mt.", "jr.", "sr.", "u.s.", "vs.", "co.", "inc.", "no.", "gen.", "col.", "capt.", "lt.", "rev.", "prof."}
    for k in range(len(ws)):
        end = (re.search(r"[.!?]$", ws[k][0]) and ws[k][0].lower() not in ABBR and not re.fullmatch(r"[A-Z]\.", ws[k][0])) or k == len(ws) - 1 or (ws[k + 1][1] - ws[k][2] > .75)
        if not end: continue
        b = k + 1; emit(a, b, bool(re.search(r"[.!?]$", ws[k][0])))
        if b - a > 14:                                          # long sentences also offer their clauses
            c = a
            for j in range(a, b):
                if (re.search(r"[,;:]$", ws[j][0]) or j == b - 1) and j + 1 - c >= 4: emit(c, j + 1, False); c = j + 1
        a = b
print(len(U), "archival utterances from", len({u[0] for u in U}), "clips", flush=True)
# ---- meaning: sentence embeddings, cached by text
tk = AutoTokenizer.from_pretrained(os.path.expanduser("~/.cache/mpnet")); em = AutoModel.from_pretrained(os.path.expanduser("~/.cache/mpnet")).eval()
torch.set_num_threads(4)
def embed(ts):
    out = []
    for k in range(0, len(ts), 128):
        with torch.no_grad():
            b = tk(ts[k:k + 128], padding=True, truncation=True, max_length=96, return_tensors="pt"); h = em(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1).float(); e = (h * m).sum(1) / m.sum(1); out.append(torch.nn.functional.normalize(e, dim=-1).numpy())
        if k and k % 12800 == 0: print("  embedded", k, "of", len(ts), flush=True)
    return np.concatenate(out).astype(np.float16) if out else np.zeros((0, 768), np.float16)
CP = os.path.join(E, "utter-emb.npz"); cache = {}
if os.path.exists(CP):
    z = np.load(CP, allow_pickle=True); cache = dict(zip(z["keys"].tolist(), z["vecs"]))
key = lambda t: hashlib.md5(t.lower().encode()).hexdigest()[:16]
new = sorted({u[3] for u in U if key(u[3]) not in cache})
if new:
    for t, v in zip(new, embed(new)): cache[key(t)] = v
    np.savez(CP, keys=np.array(list(cache)), vecs=np.stack(list(cache.values())))
UV = np.stack([cache[key(u[3])] for u in U]).astype(np.float32)
# ---- words: Homer's content words said, or said in kind
def lem(w): return wn.morphy(w) or w
UL = [{lem(norm(w)) for w in u[3].split() if norm(w) and norm(w) not in STOP} for u in U]
KIN = {}
def kin(w):
    if w in KIN: return KIN[w]
    k = {lem(w): 1.0}
    for s in wn.synsets(lem(w))[:4]:
        for l in s.lemma_names()[:6]: k.setdefault(l.lower(), .65)
        for h in s.hypernyms()[:2]:
            for l in h.lemma_names()[:4]: k.setdefault(l.lower(), .4)
    KIN[w] = k; return k
def said(hw, ul):
    if not hw: return 0.0
    return sum(max([c for x, c in kin(h).items() if x in ul] or [0]) for h in hw) / len(hw)
# ---- voices: a man or a woman (CLAP, where the archive has been heard)
gender = {}; SND = {}
try:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from transformers import ClapModel, ClapProcessor
    eids = json.load(open(os.path.join(E, "ids.json"))); CL = np.load(os.path.join(E, "clap.npy")).astype(np.float32)
    cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cpr = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    with torch.no_grad(): g = cm.get_text_features(**cpr(text=["a man speaking", "a woman speaking"], return_tensors="pt", padding=True)); g = (g / g.norm(dim=-1, keepdim=True)).numpy()
    for n, i in enumerate(eids):
        if np.abs(CL[n]).sum() > 0: SND[i] = CL[n] / (np.linalg.norm(CL[n]) + 1e-9)
        if np.abs(CL[n]).sum() > 0: d = float(CL[n] @ g[0] - CL[n] @ g[1]); gender[i] = "man" if d > .01 else "woman" if d < -.01 else None
except Exception as e: print("no voices:", e)
WOMEN = {"Athena", "Penelope", "Calypso", "Circe", "Nausicaa", "Helen", "Eurycleia", "Melantho", "Mill woman", "Arete"}
MEN = set()   # everyone else who speaks in character is a man; the narrator may be anyone
# ---- the lines
def clauses(text):
    ws = text.split()
    if len(ws) <= 10: return [text]
    parts = [p.strip() for p in re.split(r"(?<=[,;:—–])\s+|\s+[—–]\s+", text) if p.strip()]
    out = []
    for p in parts:
        if out and (len(p.split()) < 4 or len(out[-1].split()) < 4): out[-1] += " " + p
        else: out.append(p)
    while len(out) > 3:                                          # at most three answers to a line
        k = min(range(len(out) - 1), key=lambda j: len(out[j].split()) + len(out[j + 1].split())); out[k:k + 2] = [out[k] + " " + out[k + 1]]
    return out
UID = [u[0] for u in U]; used_u = set()
def best(clause, who, used_clip, qv, cast=None, prev=None):
    hw = {lem(norm(w)) for w in clause.split() if norm(w) and norm(w) not in STOP}
    sim = UV @ qv; top = np.argpartition(-sim, 300)[:300] if len(sim) > 300 else np.arange(len(sim))
    want = len(clause.split()) / 2.6; res = None
    for j in top:
        i, t0, t1, text, n, conf, whole, cold = U[j]
        s = .72 * float(sim[j]) + .34 * said(hw, UL[j])
        s += .04 * whole - .07 * cold + .04 * (conf - .8) - .05 * abs(np.log(max(.5, t1 - t0) / max(1.0, want)))
        gv = gender.get(i)
        if who in WOMEN and gv: s += .05 if gv == "woman" else -.05
        elif who != "Epic Narrator" and gv: s += .03 if gv == "man" else -.03
        if prev in SND and i in SND: s += .12 * (float(SND[prev] @ SND[i]) - .6)   # the seam: sounds like the recording before it
        mine = cast.get(who, set()) if cast else set()
        if i in mine: s += .07                                          # casting: a character keeps the voice it already has
        elif i in used_clip: s -= .08                                   # and does not borrow another character's

        if j in used_u: s -= .15
        if not res or s > res[0]: res = (s, j)
    return res
found = json.load(open(os.path.join(H, "found.json"))); clips = found["clips"]; stats = []; nc = 0
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    for sc in json.load(open(f))["scenes"]:
        lines = found["scenes"].get(sc["id"]) or []; used_clip = set(); cast = {}; prev = None
        for u in lines:
            whole = [u["text"]]; parts = clauses(u["text"])
            Q = embed(whole + (parts if len(parts) > 1 else [])).astype(np.float32)
            a = best(u["text"], u["who"], used_clip, Q[0], cast, prev); pick = [(u["text"], a)]
            if len(parts) > 1:
                bs = [best(p, u["who"], used_clip, q, cast, prev) for p, q in zip(parts, Q[1:])]
                if all(bs) and np.mean([b[0] for b in bs]) > a[0] + .05: pick = list(zip(parts, bs))
            frags = []
            for h, (s, j) in pick:
                i, t0, t1, text, n, conf, wh, cold = U[j]; used_u.add(j); used_clip.add(i); cast.setdefault(u["who"], set()).add(i); prev = i
                frags.append({"id": i, "t0": t0, "t1": t1, "words": text, "homer": h, "score": round(s, 3), "voice": gender.get(i)})
                if i not in clips: L = lib[i]; clips[i] = {"video": L["video"], "thumb": L["thumb"], "title": L.get("title"), "year": L.get("year")}
            sm = round(float(np.mean([x["score"] for x in frags])), 3)
            u["modes"]["spoken"] = {"frags": frags, "score": sm, "cuts": len(frags), "voices": len({x["id"] for x in frags}), "fidelity": None}
            stats.append((sm, len(frags), sum(x["t1"] - x["t0"] for x in frags), u["text"], " / ".join(x["words"] for x in frags)))
        nc += 1
json.dump(found, open(os.path.join(H, "found.json"), "w"), separators=(",", ":"))
print(f"spoken: {len(stats)} lines in {nc} scenes · utterances per line {np.mean([s[1] for s in stats]):.2f} · seconds per utterance {np.mean([s[2] / s[1] for s in stats]):.1f} · match {np.mean([s[0] for s in stats]):.2f}")
stats.sort(reverse=True)
for s in stats[:6] + stats[len(stats) // 2: len(stats) // 2 + 4]: print(f"  {s[0]:.2f}  {s[3][:70]}\n        → {s[4][:150]}")
