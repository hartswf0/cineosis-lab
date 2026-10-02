"""The Greek under the found Odyssey: every scene placed on Homer's own lines, and one line per scene taught word by word.
  sources   Homer's Greek (Murray's 1919 text) and Murray's 1919 English, line-numbered (Perseus, public domain); the Ancient
            Greek Dependency Treebank (Perseus, CC BY-SA) for every word's dictionary form and grammar; the LSJ lexicon (Perseus,
            CC BY-SA) for its meaning
  placing   each line of our Odyssey is matched (sentence embedding) to the passage of Murray's English that says it, in the same
            book; a scene's Greek is the run of lines its lines land on
  the key   one line per scene to carry home: the Greek line of the scene's most striking speech, read and then taken apart
  the word  one word per scene from Homer's great themes (guest-friendship, homecoming, glory, cunning...), the one the scene
            actually uses, preferring the theme least recently heard, so the themes come back the way Homer's formulas do
Writes greek.json.   usage: ../.venv/bin/python greek_odyssey.py"""
import glob, json, os, re, unicodedata
import numpy as np, torch
from transformers import AutoTokenizer, AutoModel
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.join(H, "src", "greek")
strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
# ---- Homer's lines
GRC = {}
src = open(os.path.join(G, "grc.xml")).read()
for bm in re.finditer(r'<div n="(\d+)" type="textpart" subtype="book">(.*?)</div>', src, re.S):
    b = int(bm.group(1))
    for lm in re.finditer(r'<l n="(\d+)"[^>]*>(.*?)</l>', bm.group(2), re.S): GRC[(b, int(lm.group(1)))] = strip(lm.group(2))
# ---- Murray's English, in passages from one line number to the next
ENG = []
src = open(os.path.join(G, "eng3.xml")).read()
for bm in re.finditer(r'<div type="textpart" subtype="book" n="(\d+)">(.*?)(?=<div type="textpart" subtype="book"|</body>)', src, re.S):
    b = int(bm.group(1)); parts = re.split(r'<milestone ed="p" n="(\d+)" unit="line"\s*/>', bm.group(2)); cur = 1
    for k in range(0, len(parts)):
        if k % 2 == 1: cur = int(parts[k]); continue
        t = strip(parts[k])
        if len(t) > 20: ENG.append({"b": b, "l0": cur, "text": t})
for k, e in enumerate(ENG): e["l1"] = (ENG[k + 1]["l0"] - 1) if k + 1 < len(ENG) and ENG[k + 1]["b"] == e["b"] else max(l for (bb, l) in GRC if bb == e["b"])
print(len(GRC), "Greek lines ·", len(ENG), "English passages", flush=True)
# ---- every word: its dictionary form and grammar
TB = {}
for m in re.finditer(r'<word [^>]*form="([^"]*)" lemma="([^"]*)" postag="([^"]*)"[^>]*cite="urn:cts:greekLit:tlg0012.tlg002:(\d+)\.(\d+)"', open(os.path.join(G, "tb.xml")).read()):
    TB.setdefault((int(m.group(4)), int(m.group(5))), []).append((m.group(1), re.sub(r"\d+$", "", m.group(2)), m.group(3)))
# ---- meanings (LSJ): the first few English renderings of each headword
def plain(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().replace("ς", "σ")
BETA = dict(zip("abgdezhqiklmncoprstufxywv", "αβγδεζηθικλμνξοπρστυφχψωϝ"))
def unbeta(k): return "".join(BETA.get(c, "") for c in k.lower())   # LSJ's headwords are Betacode: letters only, marks dropped
LSJ, LSJN = {}, {}
CORE = {plain(k): v for k, v in json.load(open(os.path.join(G, "core_glosses.json"))).items()}   # the 160 commonest words, glossed by hand
for f in glob.glob(os.path.join(G, "lsj", "*.xml")):
    for m in re.finditer(r'<entryFree[^>]*>.*?</entryFree>', open(f).read(), re.S):
        e = m.group(0); kk = re.search(r'key="([^"]*)"', m.group(0)[:200])
        w = unbeta(re.sub(r"\d", "", kk.group(1))) if kk else ""
        body = re.sub(r"<etym.*?</etym>|<cit.*?</cit>|<bibl.*?</bibl>", " ", e, flags=re.S); sense = re.search(r"<sense.*", body, re.S)
        trs = [strip(t).strip(" ,;:.") for t in re.findall(r"<tr[^>]*>(.*?)</tr>", sense.group(0) if sense else "", re.S)]
        trs = [t for t in trs if 1 < len(t) < 40 and not re.search(r"[\[\]\u0300-\u036f]|[^\x00-\x7f]", t)]
        if w and trs and len(e) > LSJN.get(w, 0): LSJ[w] = trs[:3]; LSJN[w] = len(e)   # of entries spelled alike, the main (longest) one
print(len(LSJ), "headwords with meanings", flush=True)
POS = {"n": "noun", "v": "verb", "a": "adjective", "d": "adverb", "l": "article", "g": "particle", "c": "conjunction", "r": "preposition", "p": "pronoun", "m": "numeral", "i": "interjection", "u": "punctuation"}
CASE = {"n": "subject", "g": "of", "d": "to/for", "a": "object", "v": "addressed"}
def gloss(lemma):
    p = plain(lemma)
    if p in CORE: return CORE[p]
    t = LSJ.get(p); return ", ".join(t[:2]) if t else None
def words_of(b, l):
    out = []
    for form, lemma, tag in TB.get((b, l), []):
        if tag[:1] == "u": continue
        g = {"w": form, "lemma": lemma, "pos": POS.get(tag[:1], ""), "means": gloss(lemma)}
        if tag[:1] in "nap" and len(tag) > 7 and tag[7] in CASE: g["case"] = CASE[tag[7]]
        if tag[:1] == "v" and len(tag) > 3: g["form"] = {"i": "is doing", "a": "did", "f": "will do", "p": "is doing", "r": "has done", "l": "had done"}.get(tag[3], "")
        out.append(g)
    return out
# ---- Homer's themes: the words to carry home, each with what it means for the poem
THEMES = [
    ("ξεῖνος", "xeinos", "stranger, guest, guest-friend: one word for all three. To receive the stranger is sacred, and the whole poem is a test of who keeps that law"),
    ("ξείνιον", "xeinion", "the guest-gift, the present a host gives a stranger to seal their bond"),
    ("νόστος", "nostos", "the homecoming. The Odyssey is the poem of one man's nostos; our word nostalgia is the ache for it"),
    ("κλέος", "kleos", "glory, what is heard of a man: fame that outlives him in song"),
    ("μῆτις", "mētis", "cunning intelligence, the craft of the mind. Odysseus's own gift, and Athena's"),
    ("πολύτροπος", "polytropos", "of many turns: the first epithet of Odysseus, the man of many ways and many wanderings"),
    ("δόλος", "dolos", "a trick, a snare: the horse, the bed, the web Penelope weaves and unweaves"),
    ("θυμός", "thūmos", "the spirit, the heart that surges: where anger, courage and longing live"),
    ("νήπιος", "nēpios", "a fool, a child: the one who does not see what is coming"),
    ("ἀτασθαλία", "atasthaliē", "reckless folly, the arrogance that brings its own ruin: the crews', the suitors'"),
    ("αἰδώς", "aidōs", "shame, reverence: the sense that stops a man from doing wrong before others and the gods"),
    ("ὅρκος", "horkos", "an oath, sworn on the gods"),
    ("Οὖτις", "Outis", "Nobody: the name Odysseus gives the Cyclops, and a pun on mētis, cunning"),
    ("ἀοιδός", "aoidos", "the singer, the bard: the poem's own maker inside the poem"),
    ("τλήμων", "tlēmōn", "enduring, wretched: the man who bears it. Odysseus is polytlas, much-enduring"),
    ("πατρίς", "patris", "the fatherland, home ground"),
    ("ἄλοχος", "alochos", "the wife, she who shares the bed"),
    ("μνηστήρ", "mnēstēr", "a suitor, the men eating Odysseus's house away"),
    ("γλαυκῶπις", "glaukōpis", "grey-eyed, bright-eyed: Athena's epithet"),
    ("ῥοδοδάκτυλος", "rhododaktylos", "rosy-fingered: the dawn's epithet, the formula that opens a new day"),
    ("πόντος", "pontos", "the open sea"),
    ("δαίμων", "daimōn", "a god, a power, a fate: something divine at work you cannot name"),
    ("μοῖρα", "moira", "a portion, one's share, fate"),
    ("τίσις", "tisis", "payment, vengeance: the price paid for a wrong"),
    ("σῆμα", "sēma", "a sign, a token, a grave-marker: the scar and the bed are sēmata by which Odysseus is known"),
]
TPLAIN = {plain(t[0]): t for t in THEMES}
# ---- placing our Odyssey on Homer's lines
tk = AutoTokenizer.from_pretrained(os.path.expanduser("~/.cache/mpnet")); em = AutoModel.from_pretrained(os.path.expanduser("~/.cache/mpnet")).eval()
def embed(ts):
    out = []
    for k in range(0, len(ts), 64):
        with torch.no_grad():
            b = tk(ts[k:k + 64], padding=True, truncation=True, max_length=256, return_tensors="pt"); h = em(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1).float(); out.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1), dim=-1).numpy())
    return np.concatenate(out)
EV = embed([e["text"][:900] for e in ENG]); print("English embedded", flush=True)
radio = json.load(open(os.path.join(H, "radio.json"))); used = {}; out = {}
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    bk = int(re.search(r"b(\d+)", f).group(1))
    rows = [k for k, e in enumerate(ENG) if e["b"] == bk]
    for sc in json.load(open(f))["scenes"]:
        subs = [u for u in sc["subs"] if u["kind"] != "SCENE_HEADER" and len(u["text"].split()) >= 4]
        if not subs: continue
        Q = embed([u["text"] for u in subs]); S = Q @ EV[rows].T
        hits = [(rows[int(np.argmax(s))], float(np.max(s)), u) for s, u in zip(S, subs)]
        mid = np.median([ENG[r]["l0"] for r, _, _ in hits])
        good = [(r, c, u) for r, c, u in hits if c > .4 and abs(ENG[r]["l0"] - mid) < 160] or hits
        l0, l1 = min(ENG[r]["l0"] for r, _, _ in good), max(ENG[r]["l1"] for r, _, _ in good)
        # the key: the passage that best matches the scene's most striking speech, and in it the line that shares most with it
        sp = [h for h in good if h[2]["kind"] == "DIALOGUE"] or good; r, c, u = max(sp, key=lambda h: h[1])
        ew = {w.lower() for w in re.findall(r"[A-Za-z]+", u["text"]) if len(w) > 3}
        def share(l): return sum(1 for g in words_of(bk, l) if g["means"] and ew & {w.lower() for w in re.findall(r"[A-Za-z]+", g["means"])}) + .01 * len(words_of(bk, l))
        cand = [l for l in range(ENG[r]["l0"], ENG[r]["l1"] + 1) if (bk, l) in GRC]
        key = max(cand, key=share) if cand else l0
        # the theme: one the scene's Greek truly uses, the least recently heard
        lem = {plain(g["lemma"]) for l in range(l0, l1 + 1) for g in words_of(bk, l)}
        cnt = {}
        for l in range(l0, l1 + 1):
            for g in words_of(bk, l): cnt[plain(g["lemma"])] = cnt.get(plain(g["lemma"]), 0) + 1
        th = [TPLAIN[p] for p in TPLAIN if p in lem]; pos = len(out)
        theme = min(th, key=lambda t: (used.get(t[0], -99), -cnt.get(plain(t[0]), 0))) if th else None   # not heard lately; most used here
        if theme: used[theme[0]] = pos
        line_at = {}
        for (rr, cc, uu) in hits: line_at[uu["text"]] = [ENG[rr]["l0"], ENG[rr]["l1"], round(cc, 2)]
        out[sc["id"]] = {"book": bk, "lines": [l0, l1], "key": {"n": key, "greek": GRC.get((bk, key), ""), "english": u["text"], "who": u["who"], "words": words_of(bk, key)},
                         "theme": {"word": theme[0], "say": theme[1], "means": theme[2], "where": next((g["w"] for l in range(l0, l1 + 1) for g in words_of(bk, l) if plain(g["lemma"]) == plain(theme[0])), theme[0])} if theme else None,
                         "murray": " ".join(e["text"] for e in ENG if e["b"] == bk and e["l0"] <= key <= e["l1"])[:900], "line_at": line_at}
json.dump(out, open(os.path.join(H, "greek.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "scenes placed on Homer's lines ·", sum(1 for v in out.values() if v["theme"]), "with a theme ·", len({v["theme"]["word"] for v in out.values() if v["theme"]}), "themes used")
for sid in ("OD-B01-S01", "OD-B09-S09", "OD-B23-S03"):
    v = out.get(sid)
    if v: print(sid, f"{v['book']}.{v['lines'][0]}-{v['lines'][1]} · key {v['book']}.{v['key']['n']}: {v['key']['greek']}\n   ", " ".join(f"{g['w']}={g['means'] or '?'}" for g in v["key"]["words"][:8]), "\n    theme:", v["theme"] and v["theme"]["word"])
