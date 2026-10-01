"""Put subtitles on the words as spoken. The script's phrases (what we show) are aligned token by token to the recording's
own words (voice_words.py: faster-whisper word timestamps); each phrase starts at its first heard word and ends at its last.
Phrases with no heard words keep their estimate, nudged to sit between their aligned neighbours.
align(subs, words) -> subs with t0/t1 from the voice, and "sync": share of a phrase's words found in the recording."""
import difflib, re
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
def align(subs, words):
    if not words or not subs: return subs
    ours = []                                   # (sub index, token)
    for k, s in enumerate(subs):
        for w in s["text"].split():
            n = norm(w)
            if n: ours.append((k, n))
    heard = [norm(w["w"]) for w in words]
    sm = difflib.SequenceMatcher(a=[t for _, t in ours], b=heard, autojunk=False)
    hit = {}                                    # our token index -> heard word index
    for a, b, size in sm.get_matching_blocks():
        for j in range(size): hit[a + j] = b + j
    out = []
    for k, s in enumerate(subs):
        idx = [i for i, (kk, _) in enumerate(ours) if kk == k]
        got = [hit[i] for i in idx if i in hit]
        x = dict(s)
        if got:
            x["t0"] = round(words[min(got)]["t0"], 2); x["t1"] = round(max(words[max(got)]["t1"], x["t0"] + .6), 2)
        x["sync"] = round(len(got) / len(idx), 2) if idx else 0
        out.append(x)
    # unaligned phrases: keep their order between aligned neighbours
    for k, x in enumerate(out):
        if x["sync"] == 0:
            lo = max([y["t1"] for y in out[:k] if y["sync"] > 0] or [x["t0"]]); hi = min([y["t0"] for y in out[k + 1:] if y["sync"] > 0] or [x["t1"]])
            if lo < hi: d = x["t1"] - x["t0"]; x["t0"] = round(max(lo, min(x["t0"], hi - d)), 2); x["t1"] = round(min(hi, x["t0"] + d), 2)
    # a phrase holds until the next begins (no flicker in short gaps), but not across a long silence
    for k in range(len(out) - 1):
        gap = out[k + 1]["t0"] - out[k]["t1"]
        if 0 < gap < .9: out[k]["t1"] = out[k + 1]["t0"]
    return out
