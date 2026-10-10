"""MARKOV SAM · NORSE, for writing your own: the page reads new words without a model.
Every word a filmmaker is likely to write (the archive's own spoken vocabulary, the memo's words, and a list of things a camera sees)
gets its CLIP text vector ("a film still of a …"); every picture in a broad pool of the archive and every cut-out figure keeps its CLIP
image vector. In the page, a typed line is the mean of its words' vectors, ranked against the pictures and figures as you type.
All vectors are kept whole (512) as int8. The pool leans toward the house's world (thirty themes of the film), and no picture may answer for more than two words.
Writes norse/wordmap.json and norse/wordmap.bin.   usage: ../.venv/bin/python norse/wordmap.py"""
import collections, glob, json, os, re, urllib.request, concurrent.futures as cf
import numpy as np, torch, open_clip
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N); OD = os.path.join(L, "odyssey")
SB = json.load(open(os.path.join(N, "storyboard.json")))
lib = {x["id"]: x for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"]}
ids = json.load(open(os.path.join(OD, "cache", "ids.json"))); EM = np.load(os.path.join(OD, "cache", "emb-openai.npy")).astype(np.float32); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
row = {i: n for n, i in enumerate(ids)}
SAM = json.load(open(os.path.join(L, "markov", "sam.json"))); SE = np.fromfile(os.path.join(L, "markov", "sam-emb.bin"), np.int8).reshape(SAM["n"], SAM["dim"]).astype(np.float32); SE /= np.linalg.norm(SE, axis=1, keepdims=True) + 1e-9
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that these those i you he she we they me him her us them my your his our their not no so if then than there here what who whom which when where how all any some one into out up down over under again very can will just do did does have has had am shall would should could may might must oh let now upon yeah okay well also because about like know think get got going gonna really thing things kind sort lot little much many more most way even still back right good mean said say says see look make made want come came go went take took give put tell told been being every other another same such only own".split())
# ---- the words: what archival people said most, the memo's words, and what a camera sees
cnt = collections.Counter()
for f in glob.glob(os.path.join(OD, "cache", "ears", "words*.json")):
    for v in json.load(open(f)).values():
        for w in v.get("words") or []:
            t = re.sub(r"[^a-z]", "", w[0].lower())
            if len(t) >= 3 and t not in STOP: cnt[t] += 1
memo = {re.sub(r"[^a-z]", "", w.lower()) for B in SB["books"] for l in B["lines"] for w in l["text"].split()} - STOP
SEES = """fog mist dawn dusk sunset sunrise night moon stars sky clouds rain storm snow wind sea ocean waves surf beach cliff coast rocks shore harbor boat ship kayak canoe sail
river lake forest trees woods field meadow hill mountain valley desert road path bridge town city street village house home roof dome tower church chapel temple door window
wall stairs garden fence barn cabin hut tent fire smoke candle lamp light shadow dark kitchen table chair bed room hall fireplace workshop tools hammer saw chisel wood timber
stone brick carving statue sculpture painting photograph camera book letters sign map flag man woman child children boy girl baby old young face hands eyes crowd people friends family
couple dancer dancing music guitar drum singing band party feast dinner wedding funeral grave cross prayer monk priest worker builder sailor fisherman farmer photographer artist
horse dog cat bird gull eagle fish whale cow sheep car truck train plane bicycle running walking climbing swimming falling laughing crying sleeping working building carving painting
reading writing talking listening waiting looking viking norse norway nepal mongolia patagonia mountains snow ice glacier fjord temple prayer flags mantra symbols geometry spiral
circle salvage ruins burned hotel wreck junk scrap metal glass gold silver red blue green white black""".split()
vocab = list(dict.fromkeys([w for w in SEES] + sorted(memo) + [w for w, _ in cnt.most_common(5000)]))[:4000]
# the house's world: what this film is about, so every suggestion leans toward it
THEMES = ["a hand-built wooden house with domes on the California coast", "a man carving a wooden statue by hand", "a Viking stave church with a steep carved roof", "carved words and mantras on wooden walls",
          "sacred geometry, circles and symbols carved in wood", "fog over the coast at dawn", "a rocky California coastline with big surf", "waves breaking on a beach at Half Moon Bay", "a hotel burning down",
          "salvaged wood and scrap built into a house", "a photographer with an old camera", "travel photographs of mountains and temples", "sea kayaks in heavy surf", "Norwegian fjords and wooden boats",
          "mountains of Nepal with prayer flags", "the steppe of Mongolia with horses", "Patagonia, wind and mountains", "people gathered in a house playing music and dancing", "friends at a long table at night",
          "an old man alone in a quiet house", "an empty room at sunset", "light through a window onto wood", "hands working with wood and tools", "a dome rising over trees", "a garden of statues",
          "a workshop full of tools", "a candle in the dark", "a greeting card with text over a photograph", "the sea seen from a high window", "smoke from a chimney in the fog"]
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def tx(ts):
    out = []
    for k in range(0, len(ts), 256):
        with torch.no_grad(): v = m.encode_text(tok(ts[k:k + 256])).float(); out.append((v / v.norm(dim=-1, keepdim=True)).numpy())
    return np.concatenate(out)
WV = tx([f"a film still of {w}" for w in vocab]); print(len(vocab), "words read", flush=True)
# ---- the picture pool: the storyboard's own pictures, then the best few for every word, all with a still that loads
def still(i):
    s = lib.get(i) or {}; t = s.get("thumb") or ""
    if t.startswith("http"): return t
    v = s.get("video") or ""
    return re.sub(r"/clips/([^/]+)\.mp4$", r"/thumbnails/\1.jpg", v) if re.search(r"/clips/[^/]+\.mp4$", v) else None
good = np.array([i in lib and lib[i].get("kind") != "poet" and bool(still(i)) for i in ids])
TV = tx(["a film still of " + t for t in THEMES])
credit = collections.Counter(); general = []
for w in range(len(vocab)):   # every word brings its best few, but no picture may answer for more than two words (the archive's 'hub' pictures would answer for all)
    took = 0
    for k in np.argsort(-np.where(good, EM @ WV[w], -9))[:40]:
        if credit[k] < 2: credit[k] += 1; general.append(ids[k]); took += 1
        if took == 2: break
themed = [ids[k] for t in range(len(THEMES)) for k in np.argsort(-np.where(good, EM @ TV[t], -9))[:45]]
pool = list(dict.fromkeys(list(SB["pics"]) + themed + general))
def ok(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "cineosis-44-research"}), timeout=15).status == 200
    except Exception: return False
print(len(pool), "pictures before the check", flush=True)
samp = pool[::25]   # the archive's stills follow one pattern; a sample is heard, not every one (a full sweep is throttled)
with cf.ThreadPoolExecutor(6) as ex: alive = list(ex.map(lambda i: ok(still(i)), samp))
print(f"sampled {len(samp)} stills: {sum(alive)} load", flush=True)
pool = [i for i in pool if i in row][:4500]; print(len(pool), "pictures in the pool", flush=True)
figs = [k for k in range(SAM["n"]) if SAM["figs"][k].get("present", 1) >= .5 and SAM["figs"][k].get("png")]
PV, FV = EM[[row[i] for i in pool]], SE[figs]
# ---- one shared space of 256 dimensions; int8
def fold(A): return np.clip(np.round(A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-9) * 127), -127, 127).astype(np.int8)   # full 512, int8
Wq, Pq, Fq = fold(WV), fold(PV), fold(FV)
# how much the fold keeps: rank agreement of each word's top picture
full = np.argmax(WV[:300] @ PV.T, 1); small = np.argmax(Wq[:300].astype(np.float32) @ Pq.T.astype(np.float32), 1); print("top picture kept for", round(float((full == small).mean()) * 100), "% of words", flush=True)
open(os.path.join(N, "wordmap.bin"), "wb").write(Wq.tobytes() + Pq.tobytes() + Fq.tobytes())
HOUSE = tx(["a film still of a hand-built Norse house of wood and domes on the foggy California coast"])[0]; CH = tx(["a film still: " + c for c in json.load(open(os.path.join(N, "poem.json")))and [b["see"] for b in json.load(open(os.path.join(N, "poem.json")))["books"]]])
q8 = lambda v: [int(x) for x in fold(v[None])[0]]
# hubness: some archive pictures sit near every word and would answer every line; each picture's mean similarity to its ten nearest words
# is subtracted in the page (CSLS, as in word translation), so a picture must fit THIS line better than it fits lines in general
def hub(V): S = V @ WV.T; return np.round(np.sort(S, 1)[:, -10:].mean(1), 3).tolist()
PROMPT = tx(["a film still of"])[0]   # every word vector shares this prompt; the page subtracts it so the words, not the prompt, decide
meta = {"dim": 512, "prompt": q8(PROMPT), "phub": hub(PV), "fhub": hub(FV), "house": q8(HOUSE), "chapters": [q8(c) for c in CH], "themes": THEMES, "words": vocab, "pics": [{"id": i, "img": still(i), "video": lib[i].get("video") or "", "in": lib[i].get("in") or 0, "title": lib[i].get("title") or "", "year": lib[i].get("year")} for i in pool], "figs": figs}
for x in meta["pics"]:   # the still is derived from the video URL where it follows the archive's pattern; the page does the same
    if x["img"] == re.sub(r"/clips/([^/]+)\.mp4$", r"/thumbnails/\1.jpg", x["video"] or ""): x.pop("img")
    x.pop("id")
json.dump(meta, open(os.path.join(N, "wordmap.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("wordmap:", os.path.getsize(os.path.join(N, "wordmap.bin")) // 1024, "KB vectors ·", os.path.getsize(os.path.join(N, "wordmap.json")) // 1024, "KB words and pictures")
