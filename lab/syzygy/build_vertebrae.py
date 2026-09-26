"""Syzygy: the prompt spine as vertebrae, every other asset of the lab aligned to them on her clock.

    python3 lab/syzygy/build_vertebrae.py        # → lab/syzygy/vertebrae.json, lab/syzygy/VERTEBRAE.md

A vertebra is one spine element (a prompt id and its generated images) placed on her clock, or one storyboard board
filling the time between her lines. Each carries every layer that can be joined to it, and says how it was joined.

Placement (how a vertebra gets its time):
  words     the element's line matched to her word timings (lab/spinecut/spinecut-data.json, main's Spine-Cut)
  ts        not matched, but the record's timestamp runs in order with its poem's matched elements on another master;
            interpolated between them (leave-one-out error ≈ 0.5 s in every poem with anchors)
  span      the poem has too few matched elements (NM, HT): its timestamps scaled onto the span of that poem's voice
  board     storyboard (WGY) filling time between lines, from Spine-Cut

Layers:
  clock     poem, line, the words she speaks inside the vertebra                      bets/kernel-data.json
  sound     her line's recording, pauses and pitch events inside it, hooks (chops)     sound-cineosis.json
  beat      the suite beat, its asked signs, its Save the Cat position, its storyboard shot(s)   syntagma-data, matrix/align.py
  intended  syntagmaType, cineosisFunction, imageType, the prompt, the line fragment   spine/total-cinome.json
  image     every variant: thumb, sign affinity on the archive's scale, fit, 6 nearest archive shots   spine/spine-data.json
  cuts      the shot each plan.py cut plays here, and Metz's reading of the beat in that cut   syntagma-data, syntagma/metz.js
  spinecut  the Spine-Cut films' picks (echo, clean, quad, blend) and review note     spinecut/spinecut-data.json
  pool      the beat's top candidates                                                  wygwyl/candidate-ranks.json
  forage    the forage cut's shot for the beat and its edit note                       wygwyl/WYGWYL_Forage_Cut.json
  patch     the suite genome patch playing here                                        wygwyl/cuts/suite/patches.json
Agreements (the syzygy): does the image read as a sign the beat asks for; does a cut's shot carry one; does Metz's
reading of the beat realise the intended syntagma.
"""
import collections, json, os, re, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(LAB, "matrix"))
from align import storyboard, align
from build_storymap import STC, AGREE

J = lambda *p: json.load(open(os.path.join(LAB, *p)))
CUTS = ["suite", "scenes", "cineosis", "drift"]
FILM_OF_CODE = {"NM": "04", "HT": "13"}   # no or too few matched lines: Nevermore by the author's word; HT by its content
tok = lambda s: re.findall(r"[a-z0-9']+", (s or "").lower().replace("’", "'"))


def lis(items, key):
    """Longest run of items (in id order) whose times never go backwards."""
    best, prev = [], {}
    tails = []
    for k, it in enumerate(items):
        v = key(it); lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if key(items[tails[mid]]) <= v: lo = mid + 1
            else: hi = mid
        prev[k] = tails[lo - 1] if lo else None
        if lo == len(tails): tails.append(k)
        else: tails[lo] = k
    out, k = [], tails[-1] if tails else None
    while k is not None: out.append(items[k]); k = prev[k]
    return out[::-1]


def ts(t):
    a, b, c = map(int, t.split(":")); return a * 60 + b + c / 30      # MM:SS:FF on the other master


def main():
    K = J("bets", "kernel-data.json"); SD = J("syntagma", "syntagma-data.json"); SC = J("spinecut", "spinecut-data.json")
    SP = J("spine", "spine-data.json"); SND = J("sound-cineosis.json"); CR = J("wygwyl", "candidate-ranks.json")["beats"]
    FC = J("wygwyl", "WYGWYL_Forage_Cut.json")["shots"]; PATCH = J("wygwyl", "cuts", "suite", "patches.json")
    LD = {s["id"]: s for s in J("lab-data.json")["shots"]}
    metz = json.loads(subprocess.run(["node", os.path.join(LAB, "matrix", "metz_read.js")], capture_output=True, text=True, check=True).stdout)
    dur = SD["duration"]; films = {f["n"]: f for f in K["films"]}; beats = K["beats"]
    words = [dict(w, film=L["film"], line=L["id"]) for L in K["lines"] for w in L["words"]]

    # ---- the elements and their records
    recs = collections.defaultdict(list)
    for r in J("spine", "total-cinome.json"): recs[r["id"]].append(r)
    imgs = collections.defaultdict(list)
    for r in SP["records"]:
        if r["src"] == "cinome": imgs[r["id"]].append(r)
    sb_imgs = {r["id"]: r for r in SP["records"] if r["src"] == "storyboard"}

    # ---- placement
    timed = {s["id"]: s for s in SC["sections"] if not s["board"]}
    by_code = collections.defaultdict(list)
    for i in recs: by_code[re.sub(r"\d+$", "", i)].append(i)
    place, moved = {}, set()
    for code, ids in by_code.items():
        ids.sort(key=lambda i: int(re.search(r"\d+$", i).group()))
        x = {i: ts(recs[i][0]["timestamp"]) for i in ids}
        # word matches that break the poem's order (a one-word fragment matched to the wrong repeat) are not anchors
        wm = [i for i in ids if i in timed]
        keep = set(lis(wm, lambda i: timed[i]["t0"]))
        for i in wm:
            if i not in keep: moved.add(i)
        anc = sorted((x[i], timed[i]["t0"], timed[i]["t1"], timed[i]["film"]) for i in ids if i in keep)
        film = collections.Counter(a[3] for a in anc).most_common(1)[0][0] if len(anc) >= 3 else FILM_OF_CODE.get(code)
        fw = [w for w in words if w["film"] == film]
        v0, v1 = (fw[0]["t0"], fw[-1]["t1"]) if fw else (films[film]["t0"], films[film]["t1"])
        durs = [a[2] - a[1] for a in anc] or [3.0]; md = statistics.median(durs)
        for i in ids:
            if i in timed and i not in moved:
                place[i] = (timed[i]["t0"], timed[i]["t1"], film, "words"); continue
            if len(anc) >= 3:
                lo = [a for a in anc if a[0] <= x[i]]; hi = [a for a in anc if a[0] >= x[i]]
                if lo and hi and hi[0][0] > lo[-1][0]:
                    a, b = lo[-1], hi[0]; t = a[1] + (b[1] - a[1]) * (x[i] - a[0]) / (b[0] - a[0])
                else:
                    a, b = (anc[0], anc[1]) if not lo else (anc[-2], anc[-1])
                    slope = (b[1] - a[1]) / (b[0] - a[0]) if b[0] > a[0] else 1
                    t = min(max(a[1] + slope * (x[i] - a[0]), films[film]["t0"]), films[film]["t1"] - 1)
                how = "ts"
            else:
                xs = [x[k] for k in ids]            # the poem's voice span, passing through whatever anchors it has
                knots = [(min(xs), v0)] + [(a[0], a[1]) for a in anc if min(xs) < a[0] < max(xs)] + [(max(xs), v1)]
                a, b = next(((a, b) for a, b in zip(knots, knots[1:]) if a[0] <= x[i] <= b[0]), (knots[0], knots[-1]))
                t = a[1] + (b[1] - a[1]) * (x[i] - a[0]) / max(1e-6, b[0] - a[0]); how = "span"
            place[i] = (t, t + md, film, how)
    # an interpolated element ends where the next element of its poem begins (at most its poem's median length)
    for code, ids in by_code.items():
        order = sorted(ids, key=lambda i: place[i][0])
        for a, b in zip(order, order[1:]):
            t0, t1, f, how = place[a]
            if how != "words": place[a] = (t0, max(t0 + .4, min(t1, place[b][0])), f, how)

    # ---- helpers on the clock
    def beat_at(t):
        return next((b for b in beats if b["t0"] <= t < b["t1"]), beats[-1])
    cutshots = {v["slug"]: v["shots"] for v in SD["versions"]}
    def cut_at(c, t):
        return next((s for s in cutshots[c] if s[0] <= t < s[1]), None)
    lines_by_film = collections.defaultdict(list)
    for p in SND["poems"]:
        for L in p["lines"]: lines_by_film[p["n"]].append(L)
    W, path, score = storyboard(), *align(storyboard(), SD["beats"])
    wgy_of_beat = collections.defaultdict(list)
    for w, j, sc in zip(W, path, score): wgy_of_beat[SD["beats"][j][0]].append({"id": w["id"], "syntagma": w["syntagmaType"], "match": sc, "thumb": (sb_imgs.get(w["id"]) or {}).get("thumb")})
    arch = lambda i: ({"id": i, "title": LD[i]["title"], "year": LD[i]["year"], "thumb": LD[i]["thumb"], "sg": (LD[i].get("aff_top") or [[None]])[0][0]}
                      if i in LD else {"id": i, **{k: SC["shots"].get(i, {}).get(k) for k in ("title", "year", "thumb", "sg")}})

    V = []
    def vertebra(kind, vid, t0, t1, film, how, rec=None, sec=None):
        tm = (t0 + t1) / 2; b = beat_at(tm)
        v = {"v": None, "kind": kind, "id": vid, "t0": round(t0, 3), "t1": round(t1, 3), "placed": how, "film": film,
             "poem": films[film]["title"] if film in films else None}
        ws = [w for w in words if t0 <= (w["t0"] + w["t1"]) / 2 < t1]
        v["clock"] = {"line": ws[0]["line"] if ws else None, "words": " ".join(w["w"] for w in ws)}
        L = next((L for L in lines_by_film.get(film, []) if L["clock"] <= tm <= L["clock"] + L["e"] - L["s"] + 1), None)
        if L:
            off = L["clock"] - L["s"]
            v["sound"] = {"line": L["id"], "reading": L["file"], "sung": (L.get("sung") or {}).get("file"),
                          "events": [e["type"] for e in L["events"] if t0 <= off + e["t"] < t1],
                          "chops": [c["label"] for c in L.get("chops", []) if set(tok(c["label"])) & set(tok(v["clock"]["words"]))]}
        pos = tm / dur * 110
        v["beat"] = {"n": b["id"], "title": b["title"], "asks": b["codes"], "stc": next(x[0] for x in STC if x[2] <= pos < x[3] or x is STC[-1]),
                     "board": wgy_of_beat.get(b["id"], [])}
        if rec:
            v["intended"] = {k: rec.get(k) for k in ("content", "syntagmaType", "cineosisFunction", "imageType", "operativeEkphrasis")}
            v["image"] = [{"thumb": r["thumb"], "aff": r["aff"][:3], "fit": r.get("fit"), "near": [arch(n[0]) | {"sim": n[1]} for n in r.get("near", [])[:3]]}
                          for r in imgs.get(vid, [])]
        v["cuts"] = {}
        for c in CUTS:
            s = cut_at(c, tm); m = metz[c][b["id"] - 1]
            v["cuts"][c] = {"shot": ({"id": s[2], "title": s[3], "year": s[4], "sg": s[9]} if s else None), "metz": m["key"], "why": m["why"]}
        if sec:
            v["spinecut"] = {k: sec.get(k) for k in ("echo", "clean", "note", "machine")} | {"quad": sec.get("quad"), "blend": (sec.get("blend") or {}).get("mode")}
        pr = CR.get(str(b["id"]))
        if pr: v["pool"] = [{"id": r["id"], "title": r.get("title"), "tag": r.get("tag")} for r in pr["ranked"][:5]]
        f = next((s for s in FC if s["start"] <= tm < s["end"]), None)
        if f: v["forage"] = {"shot": f.get("selected"), "mode": f.get("mode"), "edit": f.get("edit")}
        p = next((p for p in PATCH if p["t0"] <= tm < p["t1"]), None)
        if p: v["patch"] = p["id"]
        # the syzygy: where the layers agree
        asks = set(b["codes"]); read = {a[0] for im in v.get("image", []) for a in im["aff"]}
        intended = (rec or {}).get("syntagmaType") or next((x["syntagma"] for x in v["beat"]["board"]), None)
        v["agree"] = {"image_sign": bool(asks & read) if rec else None,
                      "cut_sign": [c for c in CUTS if v["cuts"][c]["shot"] and v["cuts"][c]["shot"]["sg"] in asks],
                      "metz": ([c for c in CUTS if v["cuts"][c]["metz"] in AGREE[intended]] if intended in AGREE else None)}
        V.append(v)

    for i in recs:
        t0, t1, film, how = place[i]
        vertebra("spine", i, t0, t1, film, how, rec=recs[i][0], sec=timed.get(i))
    for s in SC["sections"]:
        if s["board"]:
            b = beat_at((s["t0"] + s["t1"]) / 2)
            vertebra("board", s["id"], s["t0"], s["t1"], next(f["n"] for f in K["films"] if f["t0"] <= s["t0"] < f["t1"] + 1), "board", rec=None, sec=s)
            V[-1]["intended"] = {"content": s.get("line"), "syntagmaType": s.get("syntagma"), "cineosisFunction": s.get("function"),
                                 "imageType": s.get("declared"), "operativeEkphrasis": s.get("prompt")}
            V[-1]["image"] = [{"thumb": h} for h in s.get("hers", [])]
    V.sort(key=lambda v: (v["t0"], v["kind"] != "board"))
    for n, v in enumerate(V, 1): v["v"] = n
    for v in V:
        if v["id"] in moved: v["replaced"] = "its word match broke its poem's order; placed by timestamp"
    json.dump({"duration": dur, "vertebrae": V}, open(os.path.join(HERE, "vertebrae.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    open(os.path.join(HERE, "VERTEBRAE.md"), "w").write(report(V, films))
    print(f"{len(V)} vertebrae · placed {dict(collections.Counter(v['placed'] for v in V))}")


def report(V, films):
    sp = [v for v in V if v["kind"] == "spine"]
    cov = lambda key, vs: sum(1 for v in vs if v.get(key))
    o = []; w = o.append
    w("# Syzygy · the spine's vertebrae\n")
    w("Every generated spine element placed on her clock, with every other asset of the lab aligned to it. "
      "Built by `lab/syzygy/build_vertebrae.py`; the data is `vertebrae.json`.\n")
    pl = collections.Counter(v["placed"] for v in V)
    w("## Placement\n")
    w("| how | vertebrae | meaning |\n|---|---|---|")
    w(f"| words | {pl['words']} | the element's line matched to her word timings (Spine-Cut) |")
    w(f"| ts | {pl['ts']} | not matched (or, for {sum(1 for v in V if v.get('replaced'))}, matched to the wrong repeat of a word and out of order); its timestamp on the other master interpolated between its poem's matched elements (leave-one-out error ≈ 0.5 s) |")
    w(f"| span | {pl['span']} | its poem has too few matched elements (NM, HT); timestamps scaled onto the poem's voice |")
    w(f"| board | {pl['board']} | storyboard shot filling time between lines |")
    w(f"\nAll {len(sp)} spine ids are placed ({pl['words']} by her words). The other master ran the poems in another order "
      "(SH, FL, HT, NM, BE, AT, DJ, NS, YH, MR, RU, HM); within each poem its timestamps keep the suite's order.\n")
    w("## What each vertebra carries\n")
    w("| layer | spine vertebrae with it | source |\n|---|---|---|")
    for key, label, src in [("clock", "her words inside it", "bets/kernel-data.json"), ("sound", "her line's recording, pauses, pitch, hooks", "sound-cineosis.json"),
                            ("intended", "syntagma, function, prompt", "spine/total-cinome.json"), ("image", "generated images, sign reading, nearest archive shots", "spine/spine-data.json"),
                            ("cuts", "the four plan.py cuts' shots and Metz's reading", "syntagma-data + metz.js"), ("spinecut", "Spine-Cut picks and review note", "spinecut/spinecut-data.json"),
                            ("pool", "the beat's candidates", "wygwyl/candidate-ranks.json"), ("forage", "forage cut shot and edit note", "wygwyl/WYGWYL_Forage_Cut.json"),
                            ("patch", "suite genome patch", "wygwyl/cuts/suite/patches.json")]:
        n = sum(1 for v in sp if (v.get(key) and (key != "clock" or v["clock"]["words"]) and (key != "intended" or v["intended"].get("syntagmaType"))))
        w(f"| {key} · {label} | {n} of {len(sp)} | `{src}` |")
    w(f"| beat · suite beat, asked signs, Save the Cat, storyboard | {len(sp)} of {len(sp)} | `syntagma-data.json`, `matrix/align.py` |\n")
    w("## Where the layers agree\n")
    ims = [v for v in sp if v["agree"]["image_sign"] is not None and v.get("image")]
    w(f"- **The image reads as a sign its beat asks for** (one of its top three): {sum(v['agree']['image_sign'] for v in ims)} of {len(ims)}.")
    for c in CUTS:
        w(f"- **{c}'s archive shot carries an asked sign:** {sum(c in v['agree']['cut_sign'] for v in sp)} of {len(sp)}.")
    mz = [v for v in sp if v["agree"]["metz"] is not None]
    w(f"- **Metz's reading of the beat realises the intended syntagma** (only for Metz-family labels, {len(mz)} vertebrae): "
      + ", ".join(f"{c} {sum(c in v['agree']['metz'] for v in mz)}" for c in CUTS) + ".\n")
    w("## Per poem\n")
    w("| poem | spine | words | ts | span | boards |\n|---|---|---|---|---|---|")
    for n, f in films.items():
        vs = [v for v in V if v["film"] == n]; c = collections.Counter(v["placed"] for v in vs)
        w(f"| {n} · {f['title']} | {sum(1 for v in vs if v['kind'] == 'spine')} | {c['words']} | {c['ts']} | {c['span']} | {c['board']} |")
    w("\nBloodlines (05) and New Day (11) have no spine elements; their time is held by storyboard boards only.\n")
    w("## Record fixes this alignment settles\n")
    w("- **BE** records set the words of *How to Break Off an Engagement* (03); **HT** records are *How To Win My Heart* (13). "
      "The `poem` field is right; the code comment in `extract_poem_content.py` (BE = Bloodline) is not.")
    w("- **NM** (Nevermore, 04) has no line text; its 69 elements are placed by timestamp over the poem's voice (`span`).")
    w("- The 210 repeated ids are image variants; each vertebra lists all of them under `image`.\n")
    ex = next(v for v in sp if v["id"] == "SH001")
    w("## One vertebra, whole\n")
    w("```json\n" + json.dumps(ex, ensure_ascii=False, indent=1)[:4000] + "\n```")
    return "\n".join(o)


if __name__ == "__main__":
    main()
