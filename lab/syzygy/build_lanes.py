"""Lanes for the Syzygy page: every body on her clock, clip by clip, so the page can slide them under one line.

    python3 lab/syzygy/build_lanes.py     # after build_vertebrae.py → lab/syzygy/lanes.json, lab/syzygy/sprites/l*.jpg

Bodies (lanes), each a list of [t0, t1, sprite cell | null, sign | null, id]:
  voice      her words                                  bets/kernel-data.json
  spine      the generated images (first variant)       syzygy/vertebrae.json (spine vertebrae)
  board      the storyboard frame of each beat           vertebrae (board of the beat)
  suite · scenes · cineosis · drift   the plan.py cuts   syntagma/syntagma-data.json
  spinecut   Spine-Cut's clean film                      spinecut/spinecut-data.json
  forage     the forage cut                              wygwyl/WYGWYL_Forage_Cut.json
Beats carry the signs they ask for; a body is in line when its sign is one of them.
Sprites: lg* generated frames 320×180, la* archive shots with a local thumb 128×72. No local thumb, no picture.
"""
import json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
PER = 100


class Sheets:
    def __init__(self, prefix, w, h):
        self.prefix, self.w, self.h, self.idx, self.sheets = prefix, w, h, {}, []

    def add(self, key, path):
        if key in self.idx: return self.idx[key]
        if not path or not os.path.exists(path): return None
        k = len(self.idx)
        if k % PER == 0: self.sheets.append(Image.new("RGB", (self.w * 10, self.h * 10), (8, 8, 8)))
        im = Image.open(path).convert("RGB")
        r = max(self.w / im.width, self.h / im.height); im = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))))
        l, t = (im.width - self.w) // 2, (im.height - self.h) // 2
        self.sheets[-1].paste(im.crop((l, t, l + self.w, t + self.h)), ((k % PER) % 10 * self.w, (k % PER) // 10 * self.h))
        self.idx[key] = k
        return k

    def save(self):
        for n, s in enumerate(self.sheets): s.save(os.path.join(HERE, "sprites", f"{self.prefix}{n}.jpg"), quality=74)
        return len(self.sheets)



J = lambda *p: json.load(open(os.path.join(LAB, *p)))


def main():
    V = json.load(open(os.path.join(HERE, "vertebrae.json")))["vertebrae"]
    K = J("bets", "kernel-data.json"); SD = J("syntagma", "syntagma-data.json"); SC = J("spinecut", "spinecut-data.json")
    FC = J("wygwyl", "WYGWYL_Forage_Cut.json")["shots"]; LDd = J("lab-data.json")
    LD = {s["id"]: s for s in LDd["shots"]}
    sign_of = lambda i: ((LD.get(i) or {}).get("aff_top") or [[(SC["shots"].get(i) or {}).get("sg")]])[0][0]
    for f in os.listdir(os.path.join(HERE, "sprites")):
        if f.startswith("l"): os.remove(os.path.join(HERE, "sprites", f))
    G, A = Sheets("lg", 320, 180), Sheets("la", 128, 72)
    meta = {}

    def arch(i):
        if not i: return None
        k = A.add(i, os.path.join(LAB, "thumbs", f"{i}.jpg"))
        if k is not None and i not in meta:
            s = LD.get(i) or SC["shots"].get(i) or {}
            meta[i] = [s.get("title"), s.get("year"), s.get("video")]
        return k

    lanes = {}
    lanes["voice"] = [[round(w["t0"], 2), round(w["t1"], 2), None, None, w["w"]] for L in K["lines"] for w in L["words"]]
    sp, prompts = [], {}
    for v in V:
        if v["kind"] != "spine": continue
        th = (v.get("image") or [{}])[0].get("thumb")
        k = G.add(th, os.path.join(LAB, th)) if th else None
        rd = [a[0] for a in ((v.get("image") or [{}])[0].get("aff") or [])]
        sp.append([v["t0"], v["t1"], k, rd, v["id"]])
        it = v.get("intended") or {}
        prompts[v["id"]] = [it.get("syntagmaType"), it.get("cineosisFunction"), it.get("operativeEkphrasis"), v["clock"]["words"]]
    lanes["spine"] = sorted(sp)
    bd, seen = [], set()
    for b in K["beats"]:
        vb = next((v for v in V if v["beat"]["n"] == b["id"] and v["beat"]["board"]), None)
        if not vb: continue
        x = vb["beat"]["board"][0]
        if x.get("thumb"): bd.append([b["t0"], b["t1"], G.add(x["thumb"], os.path.join(LAB, x["thumb"])), None, x["id"]])
    lanes["board"] = bd
    for ver in SD["versions"]:
        lanes[ver["slug"]] = [[s[0], s[1], arch(s[2]), s[9], s[2]] for s in ver["shots"]]
    lanes["spinecut"] = [[s["t0"], s["t1"], arch(s.get("clean")), sign_of(s.get("clean")), s.get("clean")] for s in SC["sections"] if s.get("clean")]
    lanes["forage"] = [[s["start"], s["end"], arch(s.get("selected")), sign_of(s.get("selected")), s.get("selected")] for s in FC if s.get("selected")]

    ng, na = G.save(), A.save()
    signs = {s["n"]: [s["symbol"], s["name"], s["dom"]] for s in LDd["signs"]}
    out = {"dur": SD["duration"], "films": [[f["n"], f["title"], f["t0"], f["t1"]] for f in K["films"]],
           "beats": [[b["t0"], b["t1"], b["codes"], b["title"], b["id"]] for b in K["beats"]],
           "order": ["voice", "spine", "board", "suite", "scenes", "cineosis", "drift", "spinecut", "forage"],
           "lanes": lanes, "sheets": {"lg": [ng, 320, 180], "la": [na, 128, 72]}, "meta": meta, "prompts": prompts, "signs": signs}
    json.dump(out, open(os.path.join(HERE, "lanes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print({k: len(v) for k, v in lanes.items()}, "·", len(G.idx), "generated,", len(A.idx), "archive pictures")


if __name__ == "__main__":
    main()
