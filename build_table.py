"""Assemble periodic-table.html from grounding + Deamer's figure captions + vetted picks.

picks.json: {"<n>": [["<clip id>", "<one-line note on what the shot does>"], ...]}
"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.movingimagearchive.com"

QUESTIONS = {
 1:"Whose world is this?", 2:"Does perception migrate?", 3:"Can the world perceive without a human center?",
 4:"Where does intensity become a face?", 5:"Is the feeling mine, ours, or both?", 6:"Has place stopped functioning as ordinary geography?",
 7:"What force is acting through this body?", 8:"What object has become charged?", 9:"What ancient or pre-social force underlies this milieu?",
 10:"What missing situation does this action let us infer?", 11:"What two worlds could explain the same action?", 12:"How do several incomplete situations compose a world?",
 13:"What world produces these actions?", 14:"Where has the world become a duel?", 15:"How has the world gotten inside the character?",
 16:"What greater situation does this action unexpectedly imply?", 17:"What real action is being rehearsed through fiction?", 18:"Is one action-world nested inside another?",
 19:"Is the action bigger than the world requires?", 20:"Is the actor tiny compared with the world disclosed?", 21:"Has everyday life become both ridiculous and heroic?",
 22:"What hidden question does this world contain?", 23:"Why do the clues refuse to settle the situation?", 24:"Has action itself stopped being an adequate solution?",
 25:"Can we clearly tell when the dream begins?", 26:"Are we unsure whether waking has ended?", 27:"What if nobody ever wakes up?",
 28:"Does the remembered past command what happens next?", 29:"Does memory color the present without dictating it?", 30:"Which past, if any, actually explains the present?",
 31:"What recurring thing has become meaningful because it repeats?", 32:"What breaks the pattern?", 33:"What idea is being thought through this thing?",
 "34a":"Can this sight still be discharged into action?", "34b":"Does this sound stand alone as a situation, answered by no action?", 35:"Which image is original?", 36:"Which side of the image is becoming real?",
 37:"What future world lies virtually inside this image?", 38:"What if several presents are simultaneously valid?", 39:"Which layer of the past are we inhabiting?",
 40:"What if contradiction generates rather than obstructs the story?", 41:"What does the body think before it acts?", 42:"How do postures become social relations?",
 43:"Has the screen itself become a thinking system?", 44:"What must I read here that I cannot simply see?",
}

def skey(n):
    s = str(n); d = "".join(c for c in s if c.isdigit())
    return (int(d), s[len(d):])

def glosses():
    lines = open(os.path.join(HERE, "deamer.txt")).read().splitlines()[180:256]
    t = "\n".join(l.replace("\x08","") for l in lines if "Deleuze’s Cinema Books" not in l and "Figures and frames" not in l)
    out = {}
    for k, v in re.findall(r"II\.(\d[\dI])\s+(.+?)(?=\n\s*II\.\d|\n\s*Cartography|\s*\t+\s*Cartography|\n\s*Section III|\Z)", t, re.S):
        v = " ".join(v.split())
        m = re.match(r"(.*?)\s*(\d{2,3})$", v)
        n = int(k.replace("I", "1"))
        text, page = (m.group(1), m.group(2)) if m else (v, "")
        out[n] = {"gloss": text.split(":", 1)[1].strip() if ":" in text else text, "fig": f"II.{n:02d}, p. {page}" if page else f"II.{n:02d}"}
    # the last page of the figure list defeats the layout parse; captions copied from it
    tail = {41: ("a dispersed individuation of the body", 158), 42: ("the linkage of attitudes creating differentiation", 159),
            43: ("the screen as a cerebral space", 160), 44: ("the infinite of the time-image", 163)}
    for n, (g, p) in tail.items():
        out.setdefault(n, {"gloss": g, "fig": f"II.{n}, p. {p}"})
    return out

def main():
    signs = []
    for f in sorted(glob.glob(os.path.join(HERE, "grounding", "g*.json"))):
        signs += json.load(open(f))
    signs.sort(key=lambda s: skey(s["n"]))
    G = glosses()
    picks = json.load(open(os.path.join(HERE, "picks.json"))) if os.path.exists(os.path.join(HERE, "picks.json")) else {}
    clips = {}
    for f in glob.glob(os.path.join(HERE, "results", "*.json")):
        for q, cs in json.load(open(f)).items():
            for c in cs:
                clips.setdefault(c["id"], {**c, "query": q})
    rt_path = os.path.join(HERE, "lab", "cache", "read_t.json")
    READ_T = json.load(open(rt_path)) if os.path.exists(rt_path) else {}
    missing = []
    diffs = {}
    for f in glob.glob(os.path.join(HERE, "grounding", "diff*.json")):
        for d in json.load(open(f)):
            diffs[str(d["n"])] = d
    reads = {}
    for f in sorted(glob.glob(os.path.join(HERE, "readings", "r*.json"))):
        reads.update(json.load(open(f)))
    for s in signs:
        s["n"] = str(s["n"])
        num = skey(s["n"])[0]
        s.update(G.get(num, {}))
        if s["n"] == "34a": s["gloss"] = "the zeroness of the time-image: a pure optical situation"
        if s["n"] == "34b": s["gloss"] = "the zeroness of the time-image: a pure sound situation"
        s["question"] = QUESTIONS.get(num, QUESTIONS.get(s["n"]))
        s["diff"] = diffs.get(s["n"], {})
        ceiling = s["diff"].get("single_shot_ceiling", 100)
        ex = []
        for cid, note in picks.get(str(s["n"]), []):
            c = clips.get(cid)
            if not c:
                missing.append((s["n"], cid)); continue
            ex.append({"title": c["sourceTitle"], "year": c["sourceYear"], "note": note,
                       "page": f"{SITE}/sources/{c['sourceSlug']}?clip={c['id']}",
                       "video": c["videoUrl"], "thumb": c["thumbnailUrl"],
                       "start": round(c["startSeconds"], 2), "end": round(c["endSeconds"], 2),
                       "match": round(c["matchTimestampSeconds"] or c["startSeconds"], 2), "query": c["query"],
                       "read_t": READ_T.get(cid, {}).get("t")})
        for e, r in zip(ex, reads.get(s["n"], [])):
            conf, alt, alt_conf, flip = r
            e.update(conf=conf, shot=min(conf, ceiling), alt=alt, alt_conf=alt_conf, flip=flip)
        s["examples"] = ex
        confs = [e["conf"] for e in ex if "conf" in e]
        s["mean_conf"] = round(sum(confs) / len(confs)) if confs else None
        s.pop("queries", None)
    data = {"signs": signs}
    json.dump(data, open(os.path.join(HERE, "cineosis-table.json"), "w"), indent=1, ensure_ascii=False)
    tpl = open(os.path.join(HERE, "table.template.html")).read()
    open(os.path.join(HERE, "periodic-table.html"), "w").write(tpl.replace("/*DATA*/{}", json.dumps(data, ensure_ascii=False)))
    print(len(signs), "signs;", sum(len(s["examples"]) for s in signs), "examples; missing:", missing)

if __name__ == "__main__":
    main()
