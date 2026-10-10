"""NORSE HALF MOON, stage one: the voice memo read like Homer, and answered by the archive.
  the poem   source.mp3 (a voice memo about a hand-built Norse house on the Half Moon Bay coast), heard by Whisper with word times
             (whisper.json), cut into lines the way the found Odyssey's lines are cut: a sentence's end, a held breath, at most
             sixteen words (backing off to the speaker's own pause), and into books where the memo itself turns (its five chapters,
             with the invocation before them and the sign-off after)
  the call   each line is said by the memo's own voice, from its own seconds: the memo is our Homer
  answer     each line is given the one archival utterance that best says it, by the found Odyssey's own matcher (spoken_odyssey.py:
             meaning by sentence embedding, the line's words said or said in kind, a whole sentence about as long as the line,
             a voice that sounds like the one before it, no utterance used twice), long lines answered clause by clause
  picture    what we see under each line: archive footage chosen by CLIP for the line and its book, never shown twice, each
             picture joined to the one before it by look
Writes poem.json (the books, lines and answers in found.json's shape) and pics.json. Stage two is render.py (the sound).
usage: ../.venv/bin/python norse/build.py"""
import json, os, re, sys
import numpy as np
N = os.path.dirname(os.path.abspath(__file__)); OD = os.path.join(os.path.dirname(N), "odyssey")
# ---- the poem: lines and books
W = [w for s in json.load(open(os.path.join(N, "whisper.json")))["segments"] for w in s["words"]]
for w in W: w["w"] = w["word"].strip()
lw = lambda k: re.sub(r"[^a-z]", "", W[k]["w"].lower())
def anchor(phrase):   # where a book begins: the phrase, backed over the 'and', 'then', 'so' that lead into it
    ps = phrase.split()
    for k in range(len(W) - len(ps)):
        if all(lw(k + j) == p for j, p in enumerate(ps)):
            while k > 0 and lw(k - 1) in ("and", "then", "so", "um"): k -= 1
            return k
    raise SystemExit("no anchor: " + phrase)
BOOKS = [("The Invocation", None, "Before the song, the singer: nervous, honest, asking a machine to help find the shape of the film.",
          "a person alone at night with a microphone and notes, thinking"),
         ("The House as Autobiography", "about the house", "Everything Michael saw and believed on his travels, readable in the walls, the domes and the statue he built by hand.",
          "a hand built wooden house with domes, carvings and a statue, built by one man"),
         ("The Cold Open", "essentially right now", "No words. Fog, early morning: the house revealed as something the land grew, rather than something dropped into it.",
          "fog over the coast at dawn, close textures of weathered wood, stone and earth"),
         ("Why Half Moon Bay", "the second chapter", "The wild California coast, raw and unclaimed in the sixties. A hotel burned; out of what was left, a young photographer began raising something by hand.",
          "the wild California coast, surf on rocky cliffs, a burned building, the 1960s"),
         ("The Adventures That Built the Compound", "three is the", "Norway, Patagonia, Nepal, Mongolia; the Tsunami Rangers; salvage, and mantras pasted over photographs.",
          "travel: fjords of Norway, mountains of Nepal, the steppe of Mongolia, sea kayaks in heavy surf, a Viking stave church"),
         ("The House That Gathers People", "chapter four", "A party on Sunday, if it comes together: people, music and dancing.",
          "people gathered in a house playing music and dancing together"),
         ("The Reflection", "the last chapter", "Michael on his own mortality, and what he hopes happens to the house after he is gone. The house standing quiet at sunset.",
          "an old man in a quiet house at sunset, empty rooms, the light going")]
starts = [0] + [anchor(b[1]) for b in BOOKS[1:]] + [len(W)]
def cut_lines(a, b):
    out, cur = [], []
    for k in range(a, b):
        cur.append(k); t = W[k]["w"]; nxt = W[k + 1]["start"] if k + 1 < b else 1e9
        if (re.search(r"[.!?]$", t) and len(cur) >= 4) or (nxt - W[k]["end"] > .7 and len(cur) >= 3) or k == b - 1: out.append(cur); cur = []
        elif len(cur) >= 16:   # too long for one breath: back off to the speaker's own longest pause in the last eight words
            j = max(range(len(cur) - 8, len(cur) - 1), key=lambda j: W[cur[j + 1]]["start"] - W[cur[j]]["end"] + (.15 if lw(cur[j + 1]) in ("and", "so", "but", "like", "then") else 0))
            out.append(cur[: j + 1]); cur = cur[j + 1:]
    merged = []   # a scrap of two words leans on its neighbour
    for l in out:
        if merged and (len(l) < 3 or len(merged[-1]) < 3) and W[l[0]]["start"] - W[merged[-1][-1]]["end"] < 2.5 and len(merged[-1]) + len(l) <= 20: merged[-1] += l
        else: merged.append(l)
    return merged
FILL = re.compile(r"\b(um+|uh+|erm)\b[,.]?\s*", re.I)
poem = {"title": "Norse Half Moon", "source": "source.mp3", "books": []}
for n, (title, _, card, see) in enumerate(BOOKS):
    lines = []
    for l in cut_lines(starts[n], starts[n + 1]):
        text = " ".join(W[k]["w"] for k in l); clean = re.sub(r"\s+", " ", FILL.sub("", text)).strip()
        if not re.sub(r"[^a-z]", "", clean.lower()): continue
        lines.append({"t0": round(max(0, W[l[0]]["start"] - .02), 2), "t1": round(W[l[-1]]["end"] + .04, 2), "who": "the memo", "text": text, "say": clean[:1].upper() + clean[1:], "modes": {}})
    poem["books"].append({"n": n + 1, "id": f"NHM-B{n + 1:02d}", "title": title, "card": card, "see": see, "lines": lines})
print(len(poem["books"]), "books ·", sum(len(b["lines"]) for b in poem["books"]), "lines", flush=True)
# ---- the answer: the found Odyssey's matcher, run as written up to its Odyssey loop
src = open(os.path.join(OD, "spoken_odyssey.py")).read(); src = src[: src.index('found = json.load(open(os.path.join(H, "found.json"))); clips')]
G = {"__file__": os.path.join(OD, "spoken_odyssey.py"), "__name__": "spoken_norse"}; exec(compile(src, "spoken_odyssey.py", "exec"), G)
U, embed, best, clauses, lib, used_u, gender = G["U"], G["embed"], G["best"], G["clauses"], G["lib"], G["used_u"], G["gender"]
clips = {}; stats = []
for B in poem["books"]:
    used_clip, cast, prev = set(), {}, None
    for u in B["lines"]:
        whole = [u["say"]]; parts = clauses(u["say"]); Q = embed(whole + (parts if len(parts) > 1 else [])).astype(np.float32)
        a = best(u["say"], "Epic Narrator", used_clip, Q[0], cast, prev); pick = [(u["say"], a)]
        if len(parts) > 1:
            bs = [best(p, "Epic Narrator", used_clip, q, cast, prev) for p, q in zip(parts, Q[1:])]
            if all(bs) and np.mean([b[0] for b in bs]) > a[0] + .05: pick = list(zip(parts, bs))
        frags = []
        for h, (s, j) in pick:
            i, t0, t1, text, nw, conf, wh, cold = U[j]; used_u.add(j); used_clip.add(i); prev = i
            frags.append({"id": i, "t0": t0, "t1": t1, "words": text, "homer": h, "score": round(float(s), 3), "voice": gender.get(i)})
            L = lib[i]; clips[i] = {"video": L["video"], "thumb": L["thumb"], "title": L.get("title"), "year": L.get("year")}
        u["modes"]["spoken"] = {"frags": frags, "score": round(float(np.mean([x["score"] for x in frags])), 3)}
        stats.append((u["modes"]["spoken"]["score"], u["say"], " / ".join(x["words"] for x in frags)))
poem["clips"] = clips
print(f"answers: {len(stats)} lines · match {np.mean([s[0] for s in stats]):.2f}", flush=True)
for s in sorted(stats, reverse=True)[:5]: print(f"  {s[0]:.2f} {s[1][:70]}\n       -> {s[2][:120]}")
# ---- the picture: CLIP, the line and its book, nothing twice, each joined to the one before by look
import torch, open_clip
ids = json.load(open(os.path.join(OD, "cache", "ids.json"))); EM = np.load(os.path.join(OD, "cache", "emb-openai.npy")).astype(np.float32); EM /= np.linalg.norm(EM, axis=1, keepdims=True) + 1e-9
ok = np.array([i in lib and lib[i].get("kind") != "poet" and (lib[i].get("dur") or 0) >= 4 for i in ids])
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def tx(ts):
    with torch.no_grad(): v = m.encode_text(tok(ts)).float(); return (v / v.norm(dim=-1, keepdim=True)).numpy()
used = set(answering := {x["id"] for B in poem["books"] for u in B["lines"] for x in u["modes"]["spoken"]["frags"]}); pics = {}
for B in poem["books"]:
    g = tx(["a film still: " + B["see"]])[0]; L_ = tx(["a film still: " + u["say"][:200] for u in B["lines"]]); prev = None; out = []
    for u, lv in zip(B["lines"], L_):
        q = .5 * lv + .5 * g; q /= np.linalg.norm(q); s = EM @ q; s[~ok] = -9
        if prev is not None: s = s + .25 * (EM @ EM[prev])
        for k in np.argsort(-s)[:60]:
            if ids[k] not in used: break
        used.add(ids[k]); prev = k; i = ids[k]; d = lib[i].get("dur") or 8
        out.append({"li": len(out), "id": i, "video": lib[i]["video"], "in": round(min(2.0, d * .15), 2), "dur": d, "score": round(float(s[k]), 3)})
    pics[B["id"]] = out
json.dump(poem, open(os.path.join(N, "poem.json"), "w"), ensure_ascii=False, indent=0); json.dump(pics, open(os.path.join(N, "pics.json"), "w"), indent=0)
print("pictures:", sum(len(v) for v in pics.values()), "· wrote poem.json, pics.json")
