"""MARKOV SAM · REPUBLIC: the screenplay. The Republic's writers' room (github.com/hartswf0/the-republic: megamap + screenplay) holds 17
pitches of THE REPUBLIC, each answered by several witnesses (ma, character, world, matrix, legos, slugline) with a scene. This reads
them the way megamap.html does (a Prompt and the Response after it; the same pitch is one case) and keeps, for each case, the witness
whose answer is most a screenplay (most speaker cues per thousand characters, enough lines), parsed into beats:
  slug   a place and a time (INT./EXT. or a heading)          act   what we see (kept short: the first sentence or two)
  line   a speaker, how (the parenthetical), and what is said
Each episode keeps its slug, at most 6 acts and 22 lines, in story order, so the whole film runs about half an hour.
Writes republic/script.json.   usage: python3 republic/script.py [path to the-republic checkout]"""
import json, os, re, sys, hashlib, collections
H = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/hartswf0_repo_audit/repos/the-republic")
FILES = ["ma-52.json", "character-comp-52.json", "world-prompt-52.json", "matrix-editor-52.json", "legos-cog-arch-52.json", "legos-gpt-52.json", "slugline-seq-52.json"]
WIT = {"ma-52.json": "MA", "character-comp-52.json": "CHARACTER", "world-prompt-52.json": "WORLD", "matrix-editor-52.json": "MATRIX", "legos-cog-arch-52.json": "LEGOS", "legos-gpt-52.json": "LEGOS-GPT", "slugline-seq-52.json": "SLUGLINE"}
cases = collections.OrderedDict()
for f in FILES:
    p = os.path.join(SRC, f)
    if not os.path.exists(p): continue
    m = json.load(open(p))["messages"]
    for i, x in enumerate(m):
        if x.get("role") == "Prompt" and i + 1 < len(m) and m[i + 1].get("role") == "Response" and m[i + 1].get("say"):
            k = re.sub(r"\s+", " ", x["say"].strip())
            cases.setdefault(k, []).append((f, m[i + 1]["say"]))
EMO = re.compile("[\U0001F000-\U0001FFFF☀-➿️]")
CUE = re.compile(r"^([A-Z][A-Z0-9 .'\-’&/]{1,38}?)((?:\s*\([^)]{1,32}\))*)$")
SLUG = re.compile(r"^(INT\.|EXT\.|INT/EXT|I/E\.)", re.I)
NOTCUE = {"THE END", "FADE OUT", "FADE IN", "CUT TO", "SMASH CUT", "BLACKOUT", "END SCENE", "TITLE CARD", "SUPER", "MONTAGE", "LATER", "CONTINUOUS", "BEAT", "SILENCE", "END OF SCENE", "FADE TO BLACK", "INTERCUT"}
def clean(s): return EMO.sub("", s).replace("**", "").replace("__", "").strip()
def first(s, n=2):
    parts = re.split(r"(?<=[.!?])\s+", s.strip()); return " ".join(parts[:n])
def parse(text):
    L = [clean(l) for l in text.replace("\r", "").split("\n")]
    beats, i, title = [], 0, ""
    while i < len(L):
        l = L[i].strip(); i += 1
        if not l or re.match(r"^Thought for \d+s", l) or l.startswith("#") and not title and False: continue
        if re.match(r"^(SCENE|TITLE)\s*:", l, re.I):
            t = re.sub(r"^(SCENE|TITLE)\s*:\s*", "", l, flags=re.I).strip(" “”\"")
            if l.upper().startswith("SCENE"): title = t
            continue
        if SLUG.match(l) or (re.search(r" — | – ", l) and l.upper() == l and len(l) < 120):
            beats.append({"k": "slug", "text": l.strip(" .")}); continue
        mc = CUE.match(l)
        sign = re.search(r"[.!?]$", l) and not re.match(r"^([A-Z]\.)+", l) or len(l.split()) > 3 and re.search(r"\b(THE|YOUR|OF|TO|IS|NOT|IN|AND|FOR)\b", l)
        if mc and l.upper() == l and mc.group(1).strip(" .") not in NOTCUE and len(l.split()) <= 5 and not l.endswith(":") and not sign:
            who = mc.group(1).strip(); how, said = "", []
            while i < len(L) and L[i].strip():
                s = L[i].strip(); i += 1
                if s.startswith("(") and s.endswith(")") and not said: how = s.strip("()"); continue
                if s.startswith("(") and s.endswith(")"): continue
                said.append(s)
            if said: beats.append({"k": "line", "who": who, "how": how, "text": " ".join(said)})
            elif not mc.group(2) and len(l) < 90 and not re.match(r"^(THE REP|INSERT|SUPER|[A-Z ]+ MOMENT)", l): beats.append({"k": "card", "text": l})
            continue
        if len(l) > 25 and not l.endswith(":") and not l.startswith(("Purpose", "Absolutely", "Yes", "Yeah", "Here", "Want", "Would", "If you", "Let me", "Let’s", "Let's")):
            if l.startswith("(") or re.search(r"I can(’|')t|EPISODE \d|\||Round \d|Fidelity:|^PANEL \d", l): continue
            if l.upper() == l and (re.match(r"^(THE REP|INSERT|SUPER|[A-Z ]+ MOMENT)", l) or re.search(r"\([A-Z .\-0-9]+\)$", l)): continue
            beats.append({"k": "card" if l.upper() == l and len(l) < 90 else "act", "text": l})
    return title, beats
def label(prompt):
    m = re.search(r"THE REP[A-Z]*:?\s*([A-Z0-9 ,'&\-:!?.“”\"]{4,60})(?:\s{2,}|\s+The |\s+Logline| \(|$)", prompt)
    if m and m.group(1).strip(" :") not in ("", "THE"): return m.group(1).strip(" :.“”\"")
    m = re.search(r"\"THE REP\w*:\s*([^\"]+)\"", prompt)
    return m.group(1).strip() if m else ""
def genre(prompt):
    m = re.search(r"This is the (?:ultimate |Ultimate )?(.{6,90}?)(?: that| for| Netflix|\.)", prompt)
    if m: return m.group(1).strip(" ,")
    m = re.search(r"The (?:Vibe|Pitch|Mashup)\s*:\s*(.{10,120}?)[.,]", prompt)
    return m.group(1).strip() if m else "Sovereign satire"
def logline(prompt):
    m = re.search(r"(?:Logline|The Pitch|The Logline)\s*:\s*(.{20,400}?[.!?])\s", prompt)
    return m.group(1) if m else first(re.sub(r"^This is the [^.]+\.\s*", "", prompt), 2)[:400]
eps = []
for n, (prompt, wits) in enumerate(cases.items()):
    best = None
    for f, say in wits:
        title, beats = parse(say); nl = sum(b["k"] == "line" for b in beats)
        score = nl / max(1, len(say) / 1000) + min(nl, 30) / 10
        if nl >= 8 and (best is None or score > best[0]): best = (score, f, title, beats)
    if not best: print("no screenplay for case", n, prompt[:60]); continue
    _, f, title, beats = best
    slug = next((b for b in beats if b["k"] == "slug"), None)
    keep, nl, na = [], 0, 0
    for b in beats:
        if b["k"] == "slug": continue
        if b["k"] == "line" and nl < 22 and len(b["text"]) <= 320: keep.append(b); nl += 1
        elif b["k"] == "card" and not re.search(r"CUTAWAY|STYLE|ESCALATION|GAG|^[A-Z’']+$", b["text"]) and nl < 22 and sum(x["k"] == "card" for x in keep) < 2: keep.append(b)
        elif b["k"] == "act" and na < 6 and nl < 22 and (not keep or keep[-1]["k"] != "act"):
            keep.append({"k": "act", "text": first(b["text"], 2)[:260]}); na += 1
    cast = collections.Counter(b["who"] for b in keep if b["k"] == "line")
    eid = hashlib.md5(prompt.encode()).hexdigest()[:6]
    lab = label(prompt); lab = lab if lab and len(lab) > 5 else ""
    eps.append({"id": eid, "name": re.sub(r"[”\"].*$", "", (title or lab or f"EPISODE {n + 1}").upper()).strip(" “”\""), "series": lab, "scene": title, "genre": genre(prompt), "logline": logline(prompt),
                "witness": WIT[f], "takes": [WIT[w] for w, _ in wits], "slug": slug["text"] if slug else "", "beats": keep, "cast": [w for w, _ in cast.most_common()]})
# the first pitch (RED DUST & REASON) opens; the rest keep the writers' room order
json.dump({"title": "THE REPUBLIC", "source": "github.com/hartswf0/the-republic", "episodes": eps}, open(os.path.join(H, "script.json"), "w"), ensure_ascii=False, indent=1)
for e in eps: print(f"{e['id']} {e['name'][:34]:34} {e['witness']:9} {sum(b['k']=='line' for b in e['beats']):2} lines · cast {', '.join(e['cast'][:5])}")
print(len(eps), "episodes ·", sum(len(b.get("text", "").split()) for e in eps for b in e["beats"]), "words")
