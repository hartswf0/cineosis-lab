"""THE MYTH. One narrative woven from every lab film, told by its recurring cast: the archive films that the Odyssey, Norse,
the Republic and WYGWYL keep returning to. Each scene sets what a film was made for (its sponsor, year and purpose, from the
research pass) against what the lab made it into (the role the lab's films gave the same footage, from the census), and lets
its own people speak in between. Six acts, ordered as the sponsors' purposes run: PROMISE, INSTRUCTION, SELLING, FEAR, DREAM,
WITNESS. Two narrators: one for the history (what it was made for), one for the myth (what we made of it).
Writes myth/myth.json (a Rushes reel) and renders the narration with Kokoro into myth/narr/.
usage: python3 lab/myth/build.py   then   lab/republic/.tts/bin/python lab/myth/build.py --voice"""
import json, os, re, sys, collections, subprocess
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
J = lambda p: json.load(open(os.path.join(L, p)))
HIST, MYTH = "bm_george", "am_michael"

if "--voice" in sys.argv:
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    P = {}; os.makedirs(os.path.join(H, "narr"), exist_ok=True); M = J("myth/myth.json")
    for n, it in enumerate(M["reel"]):
        if not it.get("line"): continue
        vo = it["voice"]; p = P.setdefault(vo[0], KPipeline(lang_code=vo[0], repo_id="hexgrad/Kokoro-82M"))
        a = np.concatenate([np.asarray(x, np.float32) for _, _, x in p(it["line"], voice=vo, speed=.9)])
        wav = os.path.join(H, "narr", f"{n:02d}.wav"); sf.write(wav, np.concatenate([a, np.zeros(int(24000 * .35), np.float32)]), 24000)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "aac", "-b:a", "112k", wav[:-3] + "m4a"]); os.unlink(wav)
        it["a"] = f"myth/narr/{n:02d}.m4a"
    json.dump(M, open(os.path.join(H, "myth.json"), "w"), ensure_ascii=False, separators=(",", ":")); print("narration rendered"); sys.exit()

PUR = J("research/purpose.json"); C = J("rushes/clips.json"); K = J("rushes/keys.json")["keys"]; UT = J("rushes/utts.json")["utts"]
row = {k: i for i, k in enumerate(K)}
uses = J("census/uses.json")
slug_of = {}
for f in ("markov/library.json", "odyssey/library.json"):
    for s in J(f)["shots"]:
        if s.get("src"): slug_of.setdefault(s["id"], s["src"])
for s in J("lab-data.json")["shots"]: slug_of.setdefault(s["id"], s.get("slug"))
FILMNAME = {"Found Odyssey": "our Odyssey", "Markov Odyssey": "our Odyssey", "Norse Half Moon": "Norse Half Moon", "The Republic": "the Republic", "Found Republic": "the Republic", "WYGWYL": "Where You Go When You Leave"}
weight, roles, clipuse, films = collections.Counter(), collections.defaultdict(list), collections.defaultdict(collections.Counter), collections.defaultdict(set)
for u in uses:
    s = slug_of.get(u.get("clip"))
    if not s or u["role"] == "word": continue
    weight[s] += 1; films[s].add(FILMNAME[u["film"]]); clipuse[s][u["clip"]] += 1
    if u["role"] in ("picture", "place", "character") and u.get("job"): roles[s].append((u["film"], u["job"]))
USED_ROLES, USED_TITLES = set(), set()
def role_line(s):
    """what the lab made of it, in the lab's own words: Homer's line it carried, the place it became, the beat it played"""
    best = None
    for film, job in roles[s]:
        j = job.strip()
        if film == "Found Odyssey":
            if len(j.split()) < 7: continue
            line = f"In our Odyssey, it carried Homer's line: {j.rstrip('.;,—- ')}."; rank = 2
        elif film == "Markov Odyssey":
            br = re.sub(r"^\w+:\s*", "", j)
            if len(br.split()) < 4: continue
            line = f"In our Odyssey, it was cast as {br.rstrip('.')}."; rank = 1
        elif film == "The Republic":
            q, _, narr = j.partition(" | ")
            line = (f"In the Republic, it set the scene: {narr.split('.')[0]}." if q.startswith("establishing") else f"In the Republic, it stood for {q.rstrip('.')}."); rank = 1
        elif film == "Found Republic":
            t = re.sub(r"^(act|line|card|title):\s*", "", j); t = re.sub(r"^[A-Z .\-']+ says: ", "", t)
            if len(t.split()) < 5: continue
            line = f"In the Republic, it carried this: {t.rstrip('.')}."; rank = 3
        elif film == "WYGWYL":
            line = f"In Where You Go When You Leave, it played this: {j.split(': ', 1)[-1].rstrip('.')}."; rank = 0
        elif film == "Norse Half Moon":
            if len(j.split()) < 5: continue
            line = f"In Norse Half Moon, it answered this: {j.rstrip('.')}."; rank = 2
        else: continue
        if len(line.split()) > 34 or line in USED_ROLES: continue
        if best is None or rank < best[0] or (rank == best[0] and len(line) > len(best[1])): best = (rank, line)
    if best: USED_ROLES.add(best[1])
    return best[1] if best else None
def sponsor_phrase(p):
    sp = p["sponsor"]
    if sp: return ("the " + sp) if re.match(r"(U\.S\.|United States|Department|Office|Bureau|National|Federal|Ministry|State|City|Army|Navy|Air Force|Educational Film|Federal)", sp) and not sp.lower().startswith("the ") else sp
    return {"government": "the United States government", "corporation": "a company", "studio": "a film studio", "people": "people in a small town"}.get(p["kind"], "someone")
def spoken_title(t):
    t = re.sub(r"\s*\((Part|Reel) [IVX\d]+\)", "", t or ""); t = re.sub(r"\s*\d{1,2}/\d{1,2}/\d{2,4}\b", "", t); t = re.sub(r"^.*? Presents:?\s*", "", t).strip()
    return t
def base_title(t): return re.sub(r"\W+", " ", spoken_title(t).lower()).strip()
def purpose_line(p):
    t = p["purpose"]
    if not t: return ""
    w = t.split()
    if len(w) > 30:   # a long catalogue sentence is cut at a clause, never mid-thought
        cut = max((i for i, x in enumerate(w[:30]) if x.endswith((",", ";", ":"))), default=29); t = " ".join(w[:cut + 1]).rstrip(",;:")
    t = re.sub(r"^This (\d{4} )?(U\.S\. government |archival |black-and-white |color |short |educational |promotional )*(film|documentary|newsreel|short)\s+(presents|documents|depicts|shows|surveys|follows|explains|describes|records|is about)\b", r"It \4", t)
    return t if t.endswith((".", "!", "?")) else t + "."
ACTS = [("PROMISE", "First, they promised a future."), ("INSTRUCTION", "Then they explained how to live in it."), ("SELLING", "And they sold it."),
        ("FEAR", "But the future came with a warning."), ("DREAM", "So people went into the dark, and dreamed."), ("WITNESS", "And then ordinary people turned the camera on themselves.")]
ROMAN = ["I", "II", "III", "IV", "V", "VI"]
reel, used_src, used_u = [], set(), set()
def pick_clip(s):
    """the source's clip the lab used most, if Rushes holds it; else its clip with the most to say"""
    for cid, _ in clipuse[s].most_common():
        if cid in row: return row[cid]
    cand = [row[k] for k in K if slug_of.get(k) == s]
    cand.sort(key=lambda i: (C["rows"][i][7] < 0, -(C["rows"][i][3] or 0)))
    return cand[0] if cand else None
for ai, (act, opener) in enumerate(ACTS):
    cands = [s for s, p in PUR.items() if p["act"] == act and s not in used_src and weight[s] and (p["sponsor"] or p["purpose"])]
    cands.sort(key=lambda s: (-min(PUR[s].get("fit", 0), 3), -len(films[s]), -weight[s]))   # films that are clearly of this act, then the most recurring
    scenes = 0
    for s in cands:
        if scenes == 3: break
        p = PUR[s]; r0 = pick_clip(s)
        if r0 is None or base_title(p["title"]) in USED_TITLES: continue
        USED_TITLES.add(base_title(p["title"]))
        used_src.add(s); scenes += 1
        am = re.match(r"\[Amateur films?: (?:(.+?) collection: )?(.+?)\s*(\d{4}(?:-\d+)?)?\]", p["title"] or "")
        if am: hist = f"In {p['year']}, {am.group(1) or 'someone'} filmed his town: {am.group(2).rstrip(', ')}."
        elif p.get("year"): hist = f"In {p['year']}, {sponsor_phrase(p)} made a film called {spoken_title(p['title'])}."
        else: hist = f"{sponsor_phrase(p)} made a film called {spoken_title(p['title'])}."
        pl = purpose_line(p)
        ln = hist + (" " + pl if pl else ""); ln = ln[0].upper() + ln[1:]
        first = {"k": "c", "r": r0, "line": (f"{opener} " if scenes == 1 else "") + ln, "voice": HIST}
        if scenes == 1: first["card"] = f"{ROMAN[ai]} · THE {act}"
        reel.append(first)
        nx = C["rows"][r0][6]; ml = role_line(s)
        if nx >= 0: reel.append({"k": "c", "r": nx, **({"line": ml, "voice": MYTH} if ml else {})})
        elif ml:   # another clip from the same film carries the myth's line
            other = [i for i, k in enumerate(K) if slug_of.get(k) == s and i != r0]
            if other: reel.append({"k": "c", "r": other[0], "line": ml, "voice": MYTH})
        if scenes == 2:   # mid-act, the archive answers back in someone else's voice
            ans = [u for u in C["rows"][r0][10] if u not in used_u]
            if ans: used_u.add(ans[0]); reel.append({"k": "u", "u": ans[0]})
    print(f"{act:11} {scenes} scenes")
reel.append({"k": "c", "r": reel[0]["r"], "line": "These films were made to explain the future. We made them play gods, settlers and ghosts. The people in them are still talking.", "voice": MYTH, "card": "THE MYTH"})
json.dump({"title": "THE MYTH", "sub": "One narrative from every lab film, told by the archive films they keep returning to.", "reel": reel},
          open(os.path.join(H, "myth.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(reel), "items ·", sum(1 for x in reel if x.get("line")), "lines")
for it in reel[:12]: print(" ", it.get("card", ""), "|", it.get("voice", "voice") , "|", (it.get("line") or ("ANSWER: " + UT[it["u"]][3] if it["k"] == "u" else "(its own sound)"))[:150])
