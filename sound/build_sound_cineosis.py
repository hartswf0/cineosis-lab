"""The sound-cineosis bench, word level → lab/sound-cineosis.json.

Per poem line of the WYGWYL readings (the atlas's RY session):
  words      w, tight in/out on the reading (ts/te from cuts.json), cut grade A/B/C, stress, pitch
  events     PAUSE / BREATH / ACCENT / PLOSIVE / PITCH_HIGH from lanes/NN.json (prosody)
  lanes      rms and f0 across the line (every 2nd hop, 0.06 s)
  sung       the codex sung twin of the line, if any (mouth, register, distance from the poet)
  chops      her power-phrase chops whose words are in this line
  picture    where the line falls on the suite clock, the Suite-cut shot on screen then, and the beat's picture signs
    python3 sound/build_sound_cineosis.py
"""
import json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(os.path.dirname(HERE), "lab")
ATLAS = "https://hartswf0.github.io/butterfly-halfworld/wygwyl/"
CACHE = os.path.join(HERE, "atlas-cache")

def atlas(path):
    p = os.path.join(CACHE, path.replace("/", "__"))
    if not os.path.exists(p):
        with urllib.request.urlopen(ATLAS + path, timeout=60) as r: open(p, "wb").write(r.read())
    return json.load(open(p))
url = lambda f: ATLAS + urllib.request.quote(f)
norm = lambda s: re.sub(r"[^a-z' ]", " ", s.lower())

samples = atlas("samples.json")
cuts = atlas("cuts.json")["tracks"]
codex = {p["num"]: p for p in atlas("codex/lines.json")["poems"]}
sonic = atlas("sonic/sonic.json")["sounds"]
collage = json.load(open(os.path.join(LAB, "wygwyl", "collage-data.json")))
films = {f["n"]: f for f in collage["films"]}
REG = lambda f0: "ABYSSAL" if f0 < 77 else "DEEP" if f0 < 110 else "LOW" if f0 < 140 else "HIGH"

poems = []
for tr in samples["tracks"]:
    n = tr["num"]; lanes = atlas(f"lanes/{n}.json"); p0 = films[n]["poem"][0]
    words = (cuts.get(n) or {}).get("words", [])
    hop = lanes["hop"]; R = lanes["lanes"]["rms"]; F = lanes["lanes"]["f0"]
    chops = [s for s in sonic if s.get("cls") == "VOX" and s["id"].startswith(n + "_")]
    lines = []
    for L in tr["lines"]:
        s, e = L["s"], L["e"]
        W = [{"w": w["w"], "s": w["s"], "e": w["e"], "ts": w.get("ts", w["s"]), "te": w.get("te", w["e"]), "gr": w.get("gr"), "st": w.get("stress"), "f0": w.get("f0m")}
             for w in words if w.get("line") == L["n"]]
        ev = [x for x in lanes["events"] if s - .05 <= x["t"] <= e + 1.5]
        i0, i1 = int(s / hop), int(e / hop) + 1
        sung = next((c for c in codex.get(n, {}).get("lines", []) if c.get("sung_clip") and c.get("read") and abs(c["read"][0] - s) < .6), None)
        text = norm(L["text"])
        ch = [{"id": c["id"], "label": c["label"], "file": url(c["file"]), "dur": c.get("dur"), "hook": c.get("hook", 0)} for c in chops
              if c.get("label") and norm(c["label"]).strip() and norm(c["label"]).strip() in text][:8]
        t_clock = p0 + s
        shot = next((c for c in collage["cuts"]["suite"] if c["t0"] <= t_clock < c["t1"]), None)
        beat = next((b for b in collage["beats"] if b["start"] <= t_clock < b["end"]), None)
        lines.append({"id": L["id"], "n": L["n"], "text": L["text"], "s": s, "e": e, "clock": round(t_clock, 3), "file": url(L["file"]),
                      "words": W, "events": ev,
                      "rms": [round(x, 3) for x in R[i0:i1:2]], "f0": [round(x) if x else 0 for x in F[i0:i1:2]], "hop": hop * 2,
                      "sung": {"file": url(sung["sung_clip"]), "dur": sung.get("sung_dur"), "kind": sung.get("kind"), "f0": sung["voice"]["f0"],
                               "dist": sung["voice"]["poet_dist"], "reg": REG(sung["voice"]["f0"]), "recovery": sung.get("recovery")} if sung and sung.get("voice") else None,
                      "chops": ch,
                      "picture": {"shot": shot, "beat": {"id": beat["id"], "title": beat["title"], "codes": beat["codes"], "mode": beat["mode"]} if beat else None}})
    poems.append({"n": n, "title": tr["title"], "reading": url(tr["mp3"]), "dur": tr["dur"], "f0_median": lanes.get("f0_median"), "lines": lines})

signs = {k: {"symbol": v["symbol"], "name": v["name"], "dom": v["dom"]} for k, v in collage["signs"].items()}
json.dump({"atlas": ATLAS, "poems": poems, "signs": signs, "gaps": atlas("cuts.json")["gaps"]}, open(os.path.join(LAB, "sound-cineosis.json"), "w"), ensure_ascii=False, separators=(",", ":"))
nl = sum(len(p["lines"]) for p in poems)
print(len(poems), "poems ·", nl, "lines ·", sum(len(l["words"]) for p in poems for l in p["lines"]), "words ·",
      sum(1 for p in poems for l in p["lines"] if l["sung"]), "sung twins ·", sum(len(l["chops"]) for p in poems for l in p["lines"]), "chops ·",
      os.path.getsize(os.path.join(LAB, "sound-cineosis.json")) // 1024, "KB")
