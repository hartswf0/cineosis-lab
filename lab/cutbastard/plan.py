"""CUTBASTARD · plan: fill every patch with one full-frame shot, four ways.

    python3 plan.py shortlist            # → shortlist.txt (clip ids to download + watch), sources.txt (films to expand)
    python3 plan.py cut <strategy>       # → ../wygwyl/cuts/<slug>/plan.json    strategies: suite scenes cineosis drift

Shared law (all four):
  one patch = one shot, full frame, no overlays · a shot is never used twice in a cut (and is avoided if an earlier cut
  already used it) · a shot must be long enough for its patch (no slowing, no looping) · no title cards, leaders or dead
  frames · the same source film does not return within 3 patches (except where a strategy wants a scene) · black-and-white
  and colour do not flip back and forth inside a chapter · shot motion follows the score's energy · in-point = the
  liveliest clean window of the right length.
Strategies differ only in what a patch is asked to show:
  suite     the suite's own intentions: the beat's title + treatment query + the poem line (+ the forager's reviewed picks)
  scenes    a poem line plays as one scene: consecutive shots of ONE source film, in the film's own order
  cineosis  the beat's cineosis signs (sign affinity) shown through the poem line
  drift     the chapter's moods, each shot chosen to follow the last (visual continuity), the poem as a faint pull
"""
import glob, json, math, os, sys
import numpy as np, torch, open_clip

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
CUTS = os.path.join(LAB, "wygwyl", "cuts")
SLUGS = {"suite": "suite", "scenes": "scenes", "cineosis": "cineosis", "drift": "drift"}
TITLES = {"suite": "Suite", "scenes": "Scenes", "cineosis": "Cineosis", "drift": "Drift"}
IDEAS = {"suite": "Closest to the suite: each patch shows what the treatment asks of its beat and the poem line under it.",
         "scenes": "Each poem line plays as one continuous passage from a single archive film, shot after shot in that film's order.",
         "cineosis": "Each patch is chosen for the cineosis signs the suite assigns its beat, seen through the poem line.",
         "drift": "A dérive through the chapter's moods: every shot is chosen to follow the one before it."}

def load_pool():
    corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
    E = np.load(os.path.join(LAB, "cache", "emb.npy")); ids = json.load(open(os.path.join(LAB, "cache", "emb_ids.json")))
    ana = json.load(open(os.path.join(LAB, "cache", "analysis.json")))
    aff = json.load(open(os.path.join(LAB, "cache", "affinity.json"))) if os.path.exists(os.path.join(LAB, "cache", "affinity.json")) else {}
    return corpus, E, ids, ana, aff

_clip = {}
def text_emb(texts):
    if not _clip:
        m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); m.eval()
        _clip["m"], _clip["t"] = m, open_clip.get_tokenizer("ViT-B-32")
    with torch.no_grad():
        t = _clip["m"].encode_text(_clip["t"]([f"a film still: {x}"[:300] for x in texts]))
        return (t / t.norm(dim=-1, keepdim=True)).numpy()

def intents(patches, strategy):
    q = json.load(open(os.path.join(HERE, "queries.json")))
    qc = {c["i"]: c for c in q["cues"]}; mood = {c["n"]: c["mood"] for c in q["chapters"]}
    cat = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Catalogue.json")))
    beats = {b["id"]: b for b in cat["beats"]}
    out = []
    for p in patches:
        c = qc.get(p["cue"]) if p["cue"] is not None else None
        b = beats.get(p["beat"]) or {}
        if strategy == "suite":
            parts = [b.get("title"), b.get("query"), c and c["literal"], c and c["place"]]
        elif strategy == "scenes":
            parts = [c and c["literal"], c and c["oblique"], c and c["place"]]
        elif strategy == "cineosis":
            parts = [c and c["literal"], b.get("title")]
        else:
            ms = mood.get(p["chapter"], []); parts = [ms[(p["k"] + p["segment"]) % len(ms)] if ms else None, c and c["oblique"]]
        parts = [x for x in parts if x] or [p["film"].lower()]
        v = text_emb(parts).mean(0); out.append(v / np.linalg.norm(v))
    return np.stack(out)

def shortlist():
    corpus, E, ids, ana, aff = load_pool()
    patches = json.load(open(os.path.join(HERE, "patches.json")))["patches"]
    keep = set(); srcs = {}
    for strat in ("suite", "scenes", "cineosis", "drift"):
        I = intents(patches, strat)
        S = I @ E.T                                            # patches × pool
        for pi, p in enumerate(patches):
            top = np.argsort(-S[pi])[:24 if strat != "scenes" else 12]
            for j in top:
                i = ids[j]; c = corpus.get(i, {})
                if (c.get("endSeconds", 0) - c.get("startSeconds", 0)) < p["dur"] * .9: continue
                keep.add(i)
                if strat == "scenes" and c.get("sourceSlug"): srcs[c["sourceSlug"]] = srcs.get(c["sourceSlug"], 0) + float(S[pi, j])
    # scenes: if source films were expanded, keep each segment's best 4 runs of consecutive shots (scored on thumbnails)
    row = {i: k for k, i in enumerate(ids)}
    lists = {}
    for f in glob.glob(os.path.join(HERE, "forage", "sources", "*.json")):
        d = json.load(open(f)); lists[d["slug"]] = [c["id"] for c in d["clips"] if c["id"] in row]
    if lists:
        I = intents(patches, "scenes")
        segs = {}
        for pi, p in enumerate(patches): segs.setdefault(p["segment"], []).append(pi)
        for seg, pis in segs.items():
            runs = []
            for slug, lst in lists.items():
                for s0 in range(0, max(0, len(lst) - len(pis)) + 1):
                    run = lst[s0:s0 + len(pis)]
                    if len(run) < len(pis): continue
                    if any((corpus[c]["endSeconds"] - corpus[c]["startSeconds"]) < patches[q]["dur"] for c, q in zip(run, pis)): continue
                    runs.append((float(np.mean([I[q] @ E[row[c]] for c, q in zip(run, pis)])), run))
            for _, run in sorted(runs, key=lambda r: -r[0])[:4]: keep.update(run)
    open(os.path.join(HERE, "shortlist.txt"), "w").write("\n".join(sorted(keep)) + "\n")
    top_src = [s for s, _ in sorted(srcs.items(), key=lambda kv: -kv[1])[:60]]
    open(os.path.join(HERE, "sources.txt"), "w").write("\n".join(top_src) + "\n")
    print(len(keep), "clips shortlisted;", len(top_src), "source films to expand")

# ------------------------------------------------------------------ planning
def watched(i):
    p = os.path.join(LAB, "cache", "watch", i + ".json")
    return json.load(open(p)) if os.path.exists(p) else None

def window(w, dur):
    """liveliest clean window of `dur` seconds: skip the first 0.3 s, prefer steady motion, avoid the tail."""
    L = w["dur"]
    if L < dur: return None
    mt = w.get("motion_t") or []
    best, bs = 0.3 if L - dur > .6 else 0.0, -1
    for s in np.arange(0.3 if L - dur > .6 else 0.0, max(0.0, L - dur - .15) + 1e-6, 0.5):
        seg = mt[int(s): int(s + dur)] or [0]
        score = float(np.mean(seg)) - float(np.std(seg)) * .5
        if score > bs: bs, best = score, s
    return round(float(best), 2)

def plan(strategy):
    corpus, E, ids, ana, aff = load_pool()
    row = {i: k for k, i in enumerate(ids)}
    patches = json.load(open(os.path.join(HERE, "patches.json")))["patches"]
    I = intents(patches, strategy)
    used_before = set()
    for f in glob.glob(os.path.join(CUTS, "*", "plan.json")):
        if os.path.basename(os.path.dirname(f)) != SLUGS[strategy]:
            used_before |= {x["clip"]["id"] for x in json.load(open(f))["patches"]}
    W = {i: watched(i) for i in corpus}
    W = {i: w for i, w in W.items() if w and not w.get("bad") and w["dead"] < .15 and w["card"] < .35}
    pool = [i for i in W if i in row]
    pidx = {i: j for j, i in enumerate(pool)}
    Epool = np.stack([np.array(W[i]["emb"]) for i in pool])      # watched embeddings (3 frames), better than thumbs
    motion = np.array([W[i]["motion"] for i in pool]); mz = (motion - motion.mean()) / (motion.std() + 1e-9)
    bw = np.array([bool((ana.get(i) or {}).get("hue") is None) for i in pool])
    src = [corpus[i].get("sourceSlug") for i in pool]
    reviewed = {}
    if strategy == "suite":
        cat = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Catalogue.json")))
        for b in cat["beats"]:
            for c in b["candidates"]:
                if c.get("grade") and c["grade"] not in ("U", "X", "R"): reviewed[(b["id"], c["id"])] = 1.0
    codes_aff = None
    if strategy == "cineosis":
        codes_aff = lambda p, i: np.mean([((aff.get(i) or {}).get("all") or {}).get(str(c), 0) for c in p["codes"]]) if p["codes"] else 0
    sim = I @ Epool.T                                            # patch × pool
    used, out, last_src, prev_e, prev_bw = set(), [], [], None, None
    # scenes: choose one source per segment, then walk its clips in order
    src_lists = {}
    if strategy == "scenes":
        for f in glob.glob(os.path.join(HERE, "forage", "sources", "*.json")):
            d = json.load(open(f)); src_lists[d["slug"]] = [c["id"] for c in d["clips"]]
    seg_plan = {}
    for pi, p in enumerate(patches):
        dur = p["t1"] - p["t0"]
        e = p["energy"]
        if strategy == "scenes" and p["k"] == 0:
            seg = [q for q in patches if q["segment"] == p["segment"]]
            best, bscore = None, -9
            for slug, lst in src_lists.items():
                if slug in last_src[-6:]: continue
                for s0 in range(len(lst)):
                    run = lst[s0:s0 + len(seg)]
                    if len(run) < len(seg) or any(c not in pidx or c in used for c in run): continue
                    if any(W[c]["dur"] < q["t1"] - q["t0"] for c, q in zip(run, seg)): continue
                    js = [pidx[c] for c in run]
                    sc = float(np.mean([sim[patches.index(q), j] for q, j in zip(seg, js)])) - .05 * sum(c in used_before for c in run)
                    if prev_bw is not None and bw[js[0]] != prev_bw: sc -= .02
                    if sc > bscore: bscore, best = sc, run
            seg_plan[p["segment"]] = best
        choice, why = None, ""
        if strategy == "scenes" and seg_plan.get(p["segment"]):
            choice = seg_plan[p["segment"]][p["k"]]; why = f"scene: consecutive shot {p['k'] + 1}/{p['of']} of one film for this line"
        else:
            sc = sim[pi].copy()
            sc -= .06 * np.abs(mz / 3 - (e - .5))                 # pacing: calm score → calmer shots
            if strategy == "drift" and prev_e is not None: sc += .35 * (Epool @ prev_e) - .1
            if prev_bw is not None: sc -= .03 * (bw != prev_bw)   # keep the chapter's stock
            if strategy == "cineosis": sc += np.array([codes_aff(p, i) for i in pool]) / 100 * 1.5
            if strategy == "suite" and p["beat"]: sc += np.array([.04 * reviewed.get((p["beat"], i), 0) for i in pool])
            for j, i in enumerate(pool):
                if i in used or W[i]["dur"] < dur or src[j] in last_src[-3:]: sc[j] = -9
                elif i in used_before: sc[j] -= .05
            j = int(np.argmax(sc)); choice = pool[j]
            why = {"suite": "matches the beat's treatment and the line", "cineosis": f"reads as {', '.join(p['codes']) or '—'} through the line",
                   "drift": "follows the previous shot through the chapter's mood", "scenes": "no scene run fitted; best single shot"}[strategy]
        j = pidx[choice]; w = W[choice]; c = corpus[choice]
        used.add(choice); last_src.append(src[j]); prev_e, prev_bw = Epool[j], bw[j]
        inn = window(w, dur) or 0.0
        out.append({"id": p["id"], "t0": p["t0"], "t1": p["t1"], "chapter": p["chapter"], "film": p["film"], "line": p["line"],
                    "screen": p["screen"], "movement": p["movement"], "beat": p["beat"], "codes": p["codes"], "trigger": p["trigger"],
                    "energy": p["energy"], "why": why, "match": round(float(sim[pi, j]), 3),
                    "clip": {"id": choice, "title": c.get("sourceTitle"), "year": c.get("sourceYear"), "source": c.get("sourceSlug"),
                             "thumb": f"thumbs/{choice}.jpg", "clip": f"clips/{choice}.mp4", "in": inn, "out": round(inn + dur, 3),
                             "dur": w["dur"], "motion": w["motion"], "pan": w["pan"], "page": f"https://www.movingimagearchive.com/sources/{c.get('sourceSlug')}?clip={choice}"}})
    d = os.path.join(CUTS, SLUGS[strategy]); os.makedirs(d, exist_ok=True)
    json.dump({"slug": SLUGS[strategy], "title": TITLES[strategy], "idea": IDEAS[strategy], "patches": out}, open(os.path.join(d, "plan.json"), "w"), indent=1, ensure_ascii=False)
    films = len({x["clip"]["source"] for x in out}); scenes = sum(1 for x in out if x["why"].startswith("scene"))
    print(f"{strategy}: {len(out)} patches · {len({x['clip']['id'] for x in out})} distinct shots · {films} source films · scene patches {scenes} · mean match {np.mean([x['match'] for x in out]):.3f}")

if __name__ == "__main__":
    if sys.argv[1] == "shortlist": shortlist()
    else: plan(sys.argv[2])
