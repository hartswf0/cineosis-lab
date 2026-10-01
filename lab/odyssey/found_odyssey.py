"""The found Odyssey: every spoken line of the poem assembled from what archival people actually said.
From the archive's transcripts (archive_words.py: every speaking clip, every word with its seconds) each Odyssey phrase is covered,
left to right, by the longest run of its own words spoken consecutively in one clip (one breath, one voice), then shorter runs,
then single words; a word the archive never says is left as a gap (silence) and counted against the line.
For each phrase: the fragments in order {clip, t0, t1, words}, and coverage (share of the line's words the archive really says).
Also the transcript index the pages search (every clip's words with their times).
Writes found.json and transcripts.json (published).   usage: python3 found_odyssey.py"""
import glob, json, os, re
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears")
words = json.load(open(os.path.join(E, "words.json")))
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")
# the archive's words: an index from each word to every place it is said (clip, position)
seq = {}; at = {}
for i, v in words.items():
    ws = [w for w in (v.get("words") or []) if norm(w[0]) and (len(w) < 4 or w[3] >= .45)]
    if not ws or i not in lib: continue
    seq[i] = ws
    for p, w in enumerate(ws): at.setdefault(norm(w[0]), []).append((i, p))
def run_len(tokens, k, i, p):
    """How many of tokens[k:] are said in clip i from position p on, word for word."""
    n = 0; ws = seq[i]
    while k + n < len(tokens) and p + n < len(ws) and norm(ws[p + n][0]) == tokens[k + n]: n += 1
    return n
def assemble(text):
    tokens = [norm(w) for w in text.split() if norm(w)]; k = 0; frags = []; said = 0
    while k < len(tokens):
        best = None
        for i, p in at.get(tokens[k], [])[:4000]:
            n = run_len(tokens, k, i, p)
            if not best or n > best[0] or (n == best[0] and seq[i][p][3] > seq[best[1]][best[2]][3] if len(seq[i][p]) > 3 else False): best = (n, i, p)
        if not best: frags.append({"gap": tokens[k]}); k += 1; continue
        n, i, p = best; ws = seq[i][p:p + n]
        frags.append({"id": i, "t0": round(max(0, ws[0][1] - .04), 2), "t1": round(ws[-1][2] + .06, 2), "words": " ".join(w[0] for w in ws)}); said += n; k += n
    return frags, (said / len(tokens) if tokens else 0)
found = {}; cov = []
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    for s in json.load(open(f))["scenes"]:
        out = []
        for u in s["subs"]:
            if u["kind"] == "SCENE_HEADER": continue
            frags, c = assemble(u["text"]); cov.append(c)
            out.append({"t0": u["t0"], "t1": u["t1"], "who": u["who"], "text": u["text"], "coverage": round(c, 2), "runs": len([x for x in frags if "id" in x]), "frags": frags})
        found[s["id"]] = out
clips = {x["id"] for v in found.values() for u in v for x in u["frags"] if "id" in x}
json.dump({"clips": {i: {"video": lib[i]["video"], "thumb": lib[i]["thumb"], "title": lib[i].get("title"), "year": lib[i].get("year")} for i in clips}, "scenes": found}, open(os.path.join(H, "found.json"), "w"), separators=(",", ":"))
json.dump({i: {"title": lib[i].get("title"), "year": lib[i].get("year"), "video": lib[i]["video"], "thumb": lib[i]["thumb"], "words": [[w[0], w[1]] for w in ws]} for i, ws in seq.items()}, open(os.path.join(H, "transcripts.json"), "w"), separators=(",", ":"))
import statistics as st
print("archive: clips with words", len(seq), "· distinct words", len(at), "· words", sum(len(v) for v in seq.values()))
print("Odyssey phrases", len(cov), "· mean coverage", round(st.mean(cov), 2) if cov else 0, "· fully said", sum(1 for c in cov if c >= .999), "· fragments drawn from", len(clips), "clips")
