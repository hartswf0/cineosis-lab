"""The museum program: the whole found Odyssey in CALL mode, as one list a single PLAY button runs from the beginning to the end.
Each scene: its rendered call track (our voice says Homer's line plainly, the archive answers), the picture track and the
answering voice's own footage beside it, and the words as subtitles (the line, then the answer). Nothing to choose.
Writes museum.json (read by ../found-odyssey-museum.html).   usage: python3 museum_program.py"""
import json, os, re
import numpy as np
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that these those i you he she we they me him her us them my your his our their not no so if then than there here what who whom which when where how all any some one into out up down over under again very can will just do did does have has had am shall would should could may might must o oh let now upon thy thee thou ye like yeah um uh know get got gonna going really thing things kind sort".split())
def stem(w):
    w = re.sub(r"[^a-z']", "", w.lower()).strip("'")
    for suf in ("ings", "ing", "edly", "ed", "es", "s", "ly"):
        if len(w) > len(suf) + 3 and w.endswith(suf): return w[: -len(suf)]
    return w
def marks(a, b):
    """The words the line and its answer share (by stem, content words only): what the matcher found, made visible."""
    A, B = a.split(), b.split(); sa = {stem(w) for w in A if stem(w) and stem(w) not in STOP}; sb = {stem(w) for w in B if stem(w) and stem(w) not in STOP}; both = sa & sb
    return A, [k for k, w in enumerate(A) if stem(w) in both], B, [k for k, w in enumerate(B) if stem(w) in both]
H = os.path.dirname(os.path.abspath(__file__))
found = json.load(open(os.path.join(H, "found.json"))); pics = json.load(open(os.path.join(H, "found-pics.json"))); radio = json.load(open(os.path.join(H, "radio.json")))
NUM = "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE THIRTEEN FOURTEEN FIFTEEN SIXTEEN SEVENTEEN EIGHTEEN NINETEEN TWENTY".split() + ["TWENTY-ONE", "TWENTY-TWO", "TWENTY-THREE", "TWENTY-FOUR"]
P = lambda p: {k: p[k] for k in ("sw", "dd", "video", "in", "rate") if k in p} | ({"tr": p["tr"]} if p.get("tr") else {})
LIB = {x["id"]: x for f in ("all/library.json", "../markov/library.json") for x in json.load(open(os.path.join(H, f)))["shots"]}
thumb = lambda i: (LIB.get(i) or {}).get("thumb") or (found["clips"].get(i) or {}).get("thumb")
out = []
for b in radio["books"]:
    for s in b["scenes"]:
        sid = s["id"]; tr = found["scene_tracks"].get(sid, {}).get("call"); us = found["scenes"].get(sid)
        if not tr or not us or not os.path.exists(os.path.join(H, "found-audio", "call", sid + ".m4a")): print("skip", sid); continue
        calls = {e["li"]: e for e in tr["ev"] if e.get("call")}; ans = {}
        for e in tr["ev"]:
            if not e.get("call") and "id" in e: a = ans.setdefault(e["li"], [e["at"], e["end"]]); a[1] = max(a[1], e["end"])
        lines = []
        for l in tr["lines"]:
            u = us[l["li"]]; sp = (u.get("modes", {}).get("spoken") or {}).get("frags") or []; c = calls.get(l["li"], {"at": l["at"], "end": l["at"]}); a = ans.get(l["li"], [c["end"], l["end"]])
            atext = " ".join(f["words"] for f in sp if "words" in f); lw, hl, aw, ha = marks(u["text"], atext); fc = found["clips"].get(sp[0]["id"], {}) if sp and sp[0].get("id") else {}
            lines.append({"at": c["at"], "end": c["end"], "text": u["text"], "who": u.get("who", ""), "ans": atext, "aat": a[0], "aend": a[1], "hl": hl, "ha": ha,
                          "src": ", ".join(str(x) for x in (fc.get("title"), fc.get("year")) if x), "sc": round(float(np.mean([f.get("score", 0) for f in sp])) if sp else 0, 2)})
        out.append({"id": sid, "book": b["n"], "bnum": NUM[b["n"] - 1], "btitle": b["title"], "title": s["title"], "card": s.get("card", ""), "audio": "odyssey/found-audio/call/" + sid + ".m4a", "dur": tr["dur"],
                    "lines": lines, "pics": [P(p) for p in pics.get(sid, {}).get("call", [])], "beside": [{k: x[k] for k in ("sw", "end", "video", "in")} for x in pics.get(sid, {}).get("call_beside", [])],
                    "prologue": b.get("prologue", "") if s is b["scenes"][0] else "", "thumb": next((thumb(p["id"]) for p in pics.get(sid, {}).get("call", []) if thumb(p.get("id"))), None)})
prog = {"title": "The Found Odyssey", "sub": "Homer's lines, said plainly, and answered by what archival people actually said.", "root": "", "scenes": out}
json.dump(prog, open(os.path.join(H, "museum.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print(len(out), "scenes ·", round(sum(s["dur"] for s in out) / 3600, 2), "hours ·", os.path.getsize(os.path.join(H, "museum.json")) // 1024, "KB")
