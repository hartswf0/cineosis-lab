"""Pack the vertebrae for syzygy.html: a slim view.json and sprite sheets of each vertebra's lead image.

    python3 lab/syzygy/build_view.py      # after build_vertebrae.py → lab/syzygy/view.json, lab/syzygy/sprites/s*.jpg
"""
import json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
CW, CH, PER = 160, 90, 100          # cell size, cells per sheet (10 × 10)
CUTS = ["suite", "scenes", "cineosis", "drift"]


def main():
    V = json.load(open(os.path.join(HERE, "vertebrae.json")))["vertebrae"]
    signs = {s["n"]: [s["symbol"], s["name"], s["dom"]] for s in json.load(open(os.path.join(LAB, "lab-data.json")))["signs"]}
    films = [[f["n"], f["title"], f["t0"], f["t1"]] for f in json.load(open(os.path.join(LAB, "bets", "kernel-data.json")))["films"]]
    os.makedirs(os.path.join(HERE, "sprites"), exist_ok=True)
    sheets, cur, out = [], None, []
    for i, v in enumerate(V):
        thumb = (v.get("image") or [{}])[0].get("thumb")
        cell = None
        if thumb and os.path.exists(os.path.join(LAB, thumb)):
            k = len([x for x in out if x.get("px") is not None])
            if k % PER == 0:
                cur = Image.new("RGB", (CW * 10, CH * 10), (8, 8, 8)); sheets.append(cur)
            im = Image.open(os.path.join(LAB, thumb)).convert("RGB"); im.thumbnail((CW, CH))
            cur.paste(im, ((k % PER) % 10 * CW + (CW - im.width) // 2, (k % PER) // 10 * CH + (CH - im.height) // 2))
            cell = k
        a = v["agree"]; it = v.get("intended") or {}
        out.append({
            "v": v["v"], "k": v["kind"], "id": v["id"], "t0": v["t0"], "t1": v["t1"], "p": v["placed"], "f": v["film"],
            "w": v["clock"]["words"], "ln": v["clock"]["line"],
            "snd": ({"r": v["sound"]["reading"], "ev": v["sound"]["events"], "ch": v["sound"]["chops"]} if v.get("sound") else None),
            "b": [v["beat"]["n"], v["beat"]["title"], v["beat"]["asks"], v["beat"]["stc"], [x["id"] for x in v["beat"]["board"]]],
            "it": [it.get("content"), it.get("syntagmaType"), it.get("cineosisFunction"), it.get("operativeEkphrasis")] if any(it.values()) else None,
            "im": [[x.get("aff") and [a_[0] for a_ in x["aff"]], x.get("fit"), [[n["title"], n["year"], n["sg"], n["sim"]] for n in x.get("near", [])[:3]]] for x in v.get("image", [])],
            "cu": [[(v["cuts"][c]["shot"] or {}).get("title"), (v["cuts"][c]["shot"] or {}).get("year"), (v["cuts"][c]["shot"] or {}).get("sg"), v["cuts"][c]["metz"], v["cuts"][c]["why"]] for c in CUTS],
            "sc": ([v["spinecut"].get("note"), v["spinecut"].get("blend")] if v.get("spinecut") else None),
            "po": [[p["title"], p["tag"]] for p in v.get("pool", [])[:3]],
            "fo": ([v["forage"].get("mode"), v["forage"].get("edit")] if v.get("forage") else None),
            "pa": v.get("patch"),
            "ag": [a["image_sign"], [CUTS.index(c) for c in a["cut_sign"]], None if a["metz"] is None else [CUTS.index(c) for c in a["metz"]]],
            "re": v.get("replaced"), "px": cell})
    for n, s in enumerate(sheets):
        s.save(os.path.join(HERE, "sprites", f"s{n}.jpg"), quality=72)
    json.dump({"films": films, "signs": signs, "cuts": CUTS, "cell": [CW, CH, PER], "sheets": len(sheets), "v": out},
              open(os.path.join(HERE, "view.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print(len(out), "vertebrae,", len(sheets), "sheets")


if __name__ == "__main__":
    main()
