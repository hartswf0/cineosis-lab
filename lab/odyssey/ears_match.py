"""Match the Odyssey to the archive's own sound.
  echoes  for every phrase spoken in the Odyssey, the archival clips whose real spoken words (archive_words.py) come closest:
          by meaning (CLIP text) and by shared content words; each echo keeps the exact seconds in the clip where those words are said
  foley   for every shot, the archival sounds (CLAP, archive_ears.py) that best answer what the shot must show and the scene's world,
          from clips heard as field sound or music, never speech
  voice   for every clip heard as speech, whether the voice sounds like a man or a woman (CLAP), so a part can be voiced in kind
Writes them into sea/b<nn>.json (sub.echo, shot.foley) and cache/ears/report.json.   usage: ../.venv/bin/python ears_match.py"""
import glob, json, os, re
import numpy as np, torch, open_clip
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears")
eids = json.load(open(os.path.join(E, "ids.json"))); CL = np.load(os.path.join(E, "clap.npy")).astype(np.float32); erow = {i: n for n, i in enumerate(eids)}
kind = json.load(open(os.path.join(E, "kind.json"))); words = json.load(open(os.path.join(E, "words.json"))) if os.path.exists(os.path.join(E, "words.json")) else {}
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
def clap_text(ts):
    with torch.no_grad(): t = cp(text=ts, return_tensors="pt", padding=True); e = cm.get_text_features(**t); return (e / e.norm(dim=-1, keepdim=True)).numpy()
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ctext(ts):
    out = []
    for i in range(0, len(ts), 256):
        with torch.no_grad(): e = m.encode_text(tok(ts[i:i + 256])).float(); out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    return np.concatenate(out) if out else np.zeros((0, 512), np.float32)
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that these those i you he she we they me him her us them my your his our their not no so if then than there here what who whom which when where how all any some one into out up down over under again very can will just do did does have has had shall would should could may might must o oh let now upon".split())
cw = lambda t: {w.rstrip("s") for w in re.findall(r"[a-z']+", t.lower()) if len(w) > 2 and w not in STOP}
# the archive's spoken sentences, each with its seconds
sent = []
for i, v in words.items():
    ws = v.get("words") or []
    if not ws or i not in lib: continue
    cur = []
    for w in ws:
        cur.append(w)
        if re.search(r"[.!?]$", w[0]) or len(cur) >= 22:
            sent.append((i, cur[0][1], cur[-1][2], " ".join(x[0] for x in cur), float(np.mean([x[3] for x in cur])))); cur = []
    if cur: sent.append((i, cur[0][1], cur[-1][2], " ".join(x[0] for x in cur), float(np.mean([x[3] for x in cur]))))
sent = [s for s in sent if len(s[3].split()) >= 3 and s[4] > .5]
SV = ctext([s[3][:200] for s in sent]) if sent else np.zeros((0, 512)); SW = [cw(s[3]) for s in sent]
print(len(sent), "archival sentences heard", flush=True)
# voices: a man or a woman, for speech clips
G = clap_text(["a man speaking", "a woman speaking"])
gender = {i: ("man" if CL[erow[i]] @ G[0] > CL[erow[i]] @ G[1] else "woman") for i in eids if kind.get(i, {}).get("k") == "speech"}
SOUND = [i for i in eids if kind.get(i, {}).get("k") in ("field", "music") and np.abs(CL[erow[i]]).sum() > 0 and i in lib]
SX = CL[[erow[i] for i in SOUND]] if SOUND else np.zeros((0, 512))
def item(i, **kw): L = lib[i]; return {"id": i, "video": L["video"], "thumb": L["thumb"], "title": L.get("title"), "year": L.get("year"), **kw}
n_echo = n_fol = 0; rep = []
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    b = json.load(open(f))
    for s in b["scenes"]:
        subs = [u for u in s["subs"] if u["kind"] != "SCENE_HEADER" and len(u["text"].split()) >= 3]
        if subs and len(sent):
            V = ctext([u["text"][:200] for u in subs])
            for u, v in zip(subs, V):
                sim = SV @ v; ow = cw(u["text"])
                jac = np.array([len(ow & w) / max(1, len(ow | w)) for w in SW]) if ow else np.zeros(len(sent))
                score = .65 * sim + .9 * jac
                top = np.argsort(-score)[:6]; ech = []; seen = set()
                for j in top:
                    i, t0, t1, text, conf = sent[j]
                    if i in seen: continue
                    seen.add(i); ech.append(item(i, t0=t0, t1=t1, said=text, score=round(float(score[j]), 3), voice=gender.get(i)))
                u["echo"] = ech[:4]; n_echo += 1
                rep.append((round(float(score[top[0]]), 3), u["text"][:80], ech[0]["said"][:80] if ech else ""))
        if len(SOUND):
            Q = clap_text([((sh.get("see") or "") + " · " + (s.get("world") or ""))[:200] for sh in s["shots"]])
            for sh, q in zip(s["shots"], Q):
                sc = SX @ q; top = np.argsort(-sc)[:4]
                sh["foley"] = [item(SOUND[j], score=round(float(sc[j]), 3), kind=kind[SOUND[j]]["k"]) for j in top]; n_fol += 1
    json.dump(b, open(f, "w"), separators=(",", ":"))
rep.sort(reverse=True); json.dump(rep[:200], open(os.path.join(E, "report.json"), "w"), indent=0)
print("echoes for", n_echo, "phrases · foley for", n_fol, "shots · speech clips voiced", len(gender), "· sound clips", len(SOUND))
for r in rep[:8]: print(r)
