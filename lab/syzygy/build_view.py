"""Pack the vertebrae for the Syzygy Spine page: a slim view.json and sprite sheets.

    python3 lab/syzygy/build_view.py      # after build_vertebrae.py → lab/syzygy/view.json, lab/syzygy/sprites/*.jpg

Two sheet sets: g* holds every generated image a vertebra can show (all variants, storyboard boards), 160×90;
a* holds every archive shot the page can show that has a local thumb (lab/thumbs), 128×72. A picture without a local
file is left out rather than stood in for. Archive clips keep their video URL so the lab page can play them where the
host allows it.
"""
import json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
CUTS = ["suite", "scenes", "cineosis", "drift"]
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


def main():
    V = json.load(open(os.path.join(HERE, "vertebrae.json")))["vertebrae"]
    LD = {s["id"]: s for s in json.load(open(os.path.join(LAB, "lab-data.json")))["shots"]}
    SC = json.load(open(os.path.join(LAB, "spinecut", "spinecut-data.json")))["shots"]
    signs = {s["n"]: [s["symbol"], s["name"], s["dom"]] for s in json.load(open(os.path.join(LAB, "lab-data.json")))["signs"]}
    films = [[f["n"], f["title"], f["t0"], f["t1"]] for f in json.load(open(os.path.join(LAB, "bets", "kernel-data.json")))["films"]]
    os.makedirs(os.path.join(HERE, "sprites"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "sprites")): os.remove(os.path.join(HERE, "sprites", f))
    G, A = Sheets("g", 160, 90), Sheets("a", 128, 72)
    arch = {}

    def shot(i):
        """An archive shot the page can show: [sprite cell, title, year, sign, video] or None without a local thumb."""
        if not i: return None
        k = A.add(i, os.path.join(LAB, "thumbs", f"{i}.jpg"))
        if k is None: return None
        s = LD.get(i) or SC.get(i) or {}
        arch[i] = [k, s.get("title"), s.get("year"), (s.get("aff_top") or [[s.get("sg")]])[0][0], s.get("video")]
        return i

    out = []
    for v in V:
        it = v.get("intended") or {}
        gen = [G.add(x["thumb"], os.path.join(LAB, x["thumb"])) for x in v.get("image", []) if x.get("thumb")]
        img0 = (v.get("image") or [{}])[0]
        boards = [G.add(b["thumb"], os.path.join(LAB, b["thumb"])) for b in v["beat"]["board"] if b.get("thumb")]
        near = [n["id"] for x in v.get("image", [])[:1] for n in x.get("near", []) if shot(n["id"])][:3]
        cuts = [[shot((v["cuts"][c]["shot"] or {}).get("id")), v["cuts"][c]["metz"]] for c in CUTS]
        sc = v.get("spinecut") or {}
        pick = shot(sc.get("clean") or sc.get("echo"))
        fo = shot((v.get("forage") or {}).get("shot"))
        a = v["agree"]
        out.append({
            "v": v["v"], "k": v["kind"], "id": v["id"], "t0": v["t0"], "t1": v["t1"], "p": v["placed"], "f": v["film"], "w": v["clock"]["words"],
            "au": (v.get("sound") or {}).get("reading"),
            "g": [x for x in gen if x is not None], "rd": [n for n, _ in (img0.get("aff") or [])],
            "it": [it.get("syntagmaType"), it.get("cineosisFunction"), it.get("operativeEkphrasis")] if it.get("syntagmaType") or it.get("operativeEkphrasis") else None,
            "b": [v["beat"]["n"], v["beat"]["title"], v["beat"]["asks"], [x for x in boards if x is not None]],
            "cu": cuts, "sp": pick, "sn": sc.get("note"), "fo": fo, "nr": near,
            "ag": [a["image_sign"], [CUTS.index(c) for c in a["cut_sign"]], None if a["metz"] is None else [CUTS.index(c) for c in a["metz"]]],
            "re": 1 if v.get("replaced") else 0})
    ng, na = G.save(), A.save()
    json.dump({"films": films, "signs": signs, "cuts": CUTS, "sheets": {"g": [ng, 160, 90], "a": [na, 128, 72]}, "arch": arch, "v": out},
              open(os.path.join(HERE, "view.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print(len(out), "vertebrae ·", len(G.idx), "generated images in", ng, "sheets ·", len(A.idx), "archive shots in", na, "sheets")


if __name__ == "__main__":
    main()
