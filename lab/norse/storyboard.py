"""MARKOV SAM · NORSE: the storyboard's suggestions, worked out ahead so the page needs no model and opens at once.
For every line of the memo (seven books, one panel a line):
  pictures   twelve archive stills that fit the line and its book (CLIP: the line and the book's own description), the one the film
             uses first; each a published image URL, checked
  figures    ten cut-out figures (SAM, from the lab's cast) that fit the line, and the first two placed on the panel to begin with,
             where SAM found them in their own shot
  words      every figure and picture also carries plain words (its description, title, year) so the page can search them by typing
Writes norse/storyboard.json.   usage: ../.venv/bin/python norse/storyboard.py"""
import json, os, re, urllib.request, concurrent.futures as cf
import numpy as np, torch, open_clip
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N); OD = os.path.join(L, "odyssey")
poem = json.load(open(os.path.join(N, "poem.json"))); prog = json.load(open(os.path.join(N, "program.json"))); pics = json.load(open(os.path.join(N, "pics.json")))
lib = {x["id"]: x for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"]}
ids = json.load(open(os.path.join(OD, "cache", "ids.json"))); EM = np.load(os.path.join(OD, "cache", "emb-openai.npy")).astype(np.float32); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
SAM = json.load(open(os.path.join(L, "markov", "sam.json"))); SE = np.fromfile(os.path.join(L, "markov", "sam-emb.bin"), np.int8).reshape(SAM["n"], SAM["dim"]).astype(np.float32); SE /= np.linalg.norm(SE, axis=1, keepdims=True) + 1e-9
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def tx(ts):
    with torch.no_grad(): v = m.encode_text(tok(ts)).float(); return (v / v.norm(dim=-1, keepdim=True)).numpy()
def still(i):
    s = lib.get(i) or {}; t = s.get("thumb") or ""
    if t.startswith("http"): return t
    v = s.get("video") or ""
    return re.sub(r"/clips/([^/]+)\.mp4$", r"/thumbnails/\1.jpg", v) if re.search(r"/clips/[^/]+\.mp4$", v) else None
ok_ = {}
def ok(u):
    if u in ok_: return ok_[u]
    try: r = urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "cineosis-44-research"}), timeout=15).status == 200
    except Exception: r = False
    ok_[u] = r; return r
good = np.array([i in lib and lib[i].get("kind") != "poet" and bool(still(i)) for i in ids])
figok = np.array([f.get("present", 1) >= .5 and bool(f.get("png")) for f in SAM["figs"]])
books, used_figs, used_pics = [], set(), {}
for B, PB in zip(poem["books"], prog["scenes"]):
    g = tx(["a film still: " + B["see"]])[0]; LV = tx(["a film still: " + u["say"][:200] for u in B["lines"]]); lines = []
    calls = {round(l["at"], 2): l for l in PB["lines"]}
    for li, (u, lv) in enumerate(zip(B["lines"], LV)):
        q = .55 * lv + .45 * g; q /= np.linalg.norm(q)
        s = EM @ q; s[~good] = -9; top = [ids[k] for k in np.argsort(-s)[:40]]
        first = pics[B["id"]][li]["id"] if li < len(pics[B["id"]]) else None
        cand = ([first] if first else []) + [i for i in top if i != first]
        lines.append({"q": q, "cand": cand, "u": u, "li": li})
    # check the stills in parallel, keep twelve that load
    allc = {still(i) for l in lines for i in l["cand"][:24] if still(i)}
    with cf.ThreadPoolExecutor(16) as ex: list(ex.map(ok, allc))
    out = []
    for l, P in zip(lines, PB["lines"]):
        gr = [i for i in l["cand"] if still(i) and ok(still(i))][:12]
        for i in gr: used_pics[i] = {"img": still(i), "title": lib[i].get("title") or "", "year": lib[i].get("year")}
        fs = SE @ l["q"]; fs[~figok] = -9; ft = [int(k) for k in np.argsort(-fs)[:10]]; used_figs.update(ft)
        place = []
        for n, f in enumerate(ft[:2]):   # begin with the two best, where SAM found them in their own shot, a little apart
            F = SAM["figs"][f]; w = min(.42, (.62 - .12 * n) * (9 / 16) * F["w"] / F["h"])   # sized by height: the first about two thirds of the panel, the second a little farther off
            place.append({"f": f, "x": round(.3 + .4 * n, 3), "y": round(.93 - .05 * n, 3), "w": round(w, 3)})
        out.append({"text": P["text"], "at": P["at"], "end": P["end"], "aat": P["aat"], "aend": P["aend"], "ans": P["ans"], "grounds": gr, "figs": ft, "start": {"g": 0, "figs": place}})
    books.append({"n": B["n"], "num": PB["bnum"], "title": B["title"], "card": B["card"], "audio": PB["audio"], "lines": out})
    print(B["title"], len(out), "panels", flush=True)
figs = {}
for f in sorted(set(used_figs) | {k for k in range(SAM['n']) if figok[k]}):   # the whole cast, so typing can find any figure
    F = SAM["figs"][f]; png = F["png"]; figs[f] = {"img": png[:-4] + ".webp", "sprite": (F.get("sprite") or "")[:-4] + ".webp" if F.get("sprite") else "", "w": F["w"], "h": F["h"],
                                                   "sw": F.get("sw"), "sh": F.get("sh"), "fps": F.get("fps", 6), "desc": F.get("desc") or "", "title": F.get("title") or "", "year": F.get("year")}
json.dump({"title": "Norse Half Moon", "books": books, "pics": used_pics, "figs": figs}, open(os.path.join(N, "storyboard.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(len(used_pics), "pictures ·", len(figs), "figures ·", os.path.getsize(os.path.join(N, "storyboard.json")) // 1024, "KB")
