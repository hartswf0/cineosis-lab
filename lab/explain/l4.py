"""LESSON 4 · THE VOICE IS THE CLOCK. What a recorded voice adds to a printed line, measured on the suite's real word timings
(bets/kernel-data.json: 267 lines, 2,799 words, each with start, end and stress), and drawn the way Videotext's views draw it.
  score     one stanza: each line's words at their spoken times (Elastic Spacing / Word Duration), with stress
  remap     the stanza's time curve (Time Remap) against Videotext's own guess when it has no recording: a word lasts as long as its
            letters plus two, a full stop rests six, a comma three (videotext.html tokenize)
  speed     words per second for every line of the poem; the fastest and slowest lines; the longest silences
  bridge    every cut of the cut films against the spoken lines (Bridge Bar): how many land inside a line, by what set them
  bind      a stretch of the Suite's cut with its words, for the playhead (Playhead Bind)
Writes explain/lesson/l4.json.   usage: python3 lab/explain/l4.py"""
import json, os, re
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H); J = lambda p: json.load(open(os.path.join(LAB, p)))
K = J("bets/kernel-data.json"); L = K["lines"]; P = J("cutbastard/patches.json")["patches"]; SU = J("wygwyl/cuts/suite/plan.json")["patches"]
def guess(line):
    """Videotext's fallback: a word's weight is its letters + 2, +6 after . ? ! : ;  and +3 after a comma or dash; spread over the line's span."""
    toks = line["words"]; wts = []
    for w in toks:
        t = w["w"]; x = len(re.sub(r"[^A-Za-z']", "", t)) + 2
        if re.search(r"[.?!:;]$", t): x += 6
        elif re.search(r"[,—-]$", t): x += 3
        wts.append(x)
    span = line["t1"] - line["t0"]; c = np.cumsum([0] + wts)[:-1] / sum(wts) * span + line["t0"]
    return [round(float(x), 3) for x in c]
BLOCK = ("kinderen naar buiten", "all my babies", "jfk exhibit")
def clean(a, b): return not any(t in p["clip"]["title"].lower() for p in SU if p["t1"] > a and p["t0"] < b for t in BLOCK)
def pauses(l): return [round(b["t0"] - a["t1"], 3) for a, b in zip(l["words"], l["words"][1:])]
out = {"audio": "wygwyl/WYGWYL_Suite_Audio.mp3", "dur": K["duration"], "n_lines": len(L), "n_words": sum(len(l["words"]) for l in L), "films": K["films"]}
# a stanza: the run of consecutive lines with the most expressive timing (largest inside-line pauses), 4 lines, in one film
best, bi = -1, 0
for i in range(len(L) - 3):
    run = L[i:i + 4]
    if len({l["film"] for l in run}) > 1 or run[-1]["t1"] - run[0]["t0"] > 32 or not clean(run[0]["t0"] - .5, run[-1]["t1"] + .5): continue
    v = sum(max(pauses(l) or [0]) for l in run) + np.std([len(l["words"]) / (l["t1"] - l["t0"]) for l in run])
    if v > best: best, bi = v, i
def pack(l): return {"id": l["id"], "film": l["film"], "text": l["text"], "t0": l["t0"], "t1": l["t1"], "words": l["words"], "guess": guess(l), "pauses": pauses(l)}
out["stanza"] = [pack(l) for l in L[bi:bi + 4]]
err = [abs(g - w["t0"]) for l in L for g, w in zip(guess(l), l["words"])]
out["guess_err"] = {"mean": round(float(np.mean(err)), 3), "p90": round(float(np.percentile(err, 90)), 3), "max": round(float(np.max(err)), 3)}
sp = [{"id": l["id"], "film": l["film"], "t0": l["t0"], "t1": l["t1"], "wps": round(len(l["words"]) / (l["t1"] - l["t0"]), 3), "text": l["text"]} for l in L]
out["speed"] = sp
srt = sorted([x for x in sp if len(x["text"].split()) >= 8], key=lambda x: x["wps"]); out["slowest"], out["fastest"] = srt[0], srt[-1]
sil = sorted([{"t0": L[i]["t1"], "t1": L[i + 1]["t0"], "s": round(L[i + 1]["t0"] - L[i]["t1"], 2), "before": L[i]["text"], "after": L[i + 1]["text"]} for i in range(len(L) - 1)], key=lambda x: -x["s"])
out["silences"] = sil[:6]; out["inside_pauses"] = sum(1 for l in L for p in pauses(l) if p > .5)
cuts = [{"t": p["t0"], "trigger": p["trigger"], "inside": any(l["t0"] + .3 < p["t0"] < l["t1"] - .3 for l in L)} for p in P[1:]]
out["bridge"] = {"cuts": cuts, "n": len(cuts), "inside": sum(c["inside"] for c in cuts), "cue": sum(1 for c in cuts if c["trigger"] == "cue"), "cue_inside": sum(1 for c in cuts if c["trigger"] == "cue" and c["inside"]),
                 "onset": sum(1 for c in cuts if c["trigger"] == "onset"), "onset_inside": sum(1 for c in cuts if c["trigger"] == "onset" and c["inside"])}
# the stanza's own stretch of the Suite cut, for the bridge bar and the playhead
a, b = out["stanza"][0]["t0"] - .5, out["stanza"][-1]["t1"] + .5
out["bind"] = {"a": round(a, 2), "b": round(b, 2), "pics": [{"sw": p["t0"], "end": p["t1"], "video": p["clip"]["clip"], "in": p["clip"]["in"], "title": p["clip"]["title"], "thumb": p["clip"]["thumb"], "trigger": p["trigger"]} for p in SU if p["t1"] > a and p["t0"] < b]}
# practice: another stanza, from a different chapter
pj = max(range(len(L) - 3), key=lambda i: -1 if (len({l["film"] for l in L[i:i + 4]}) > 1 or L[i]["film"] == L[bi]["film"] or L[i + 3]["t1"] - L[i]["t0"] > 26 or not clean(L[i]["t0"] - .5, L[i + 3]["t1"] + .5)) else sum(max(pauses(l) or [0]) for l in L[i:i + 4]))
out["practice"] = [pack(l) for l in L[pj:pj + 4]]
a2, b2 = out["practice"][0]["t0"] - .5, out["practice"][-1]["t1"] + .5
out["practice_bind"] = {"a": round(a2, 2), "b": round(b2, 2), "pics": [{"sw": p["t0"], "end": p["t1"], "video": p["clip"]["clip"], "in": p["clip"]["in"], "title": p["clip"]["title"], "thumb": p["clip"]["thumb"], "trigger": p["trigger"]} for p in SU if p["t1"] > a2 and p["t0"] < b2]}
json.dump(out, open(os.path.join(H, "lesson", "l4.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("stanza", [(l["id"], l["text"][:50], max(l["pauses"] or [0])) for l in out["stanza"]], out["stanza"][0]["t0"], out["stanza"][-1]["t1"])
print("guess err", out["guess_err"]); print("slowest", out["slowest"]["wps"], out["slowest"]["text"][:60]); print("fastest", out["fastest"]["wps"], out["fastest"]["text"][:60])
print("silences", [(s["s"], s["before"][:30]) for s in out["silences"][:4]]); print("bridge", {k: v for k, v in out["bridge"].items() if k != "cuts"})
print("bind pics", [(p["title"][:20], p["sw"], p["trigger"]) for p in out["bind"]["pics"]]); print("practice", [l["text"][:40] for l in out["practice"]], out["practice"][0]["t0"])
