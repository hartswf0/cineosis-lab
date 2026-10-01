"""Matrix-Editor: WYGWYL as Diegesis → Acts → Beats → Syntagmas → Shots, read from the lab's own assets.

    python3 lab/matrix/build_storymap.py            # → lab/matrix/Storymap.md, lab/matrix/matrix.json
    python3 lab/matrix/build_storymap.py --shotlist # also lab/matrix/Shotlist.js
    python3 lab/matrix/build_storymap.py --chart    # also lab/matrix/chart-data.js (the Chart.d3 tree)

Where each level comes from (nothing is invented; what is imposed says so):
  Diegesis   wygwyl/cuts/suite/matrix_A_patch_genome.yaml (premise, world rules), the storyboard's characters and
             settings (spine/storyboard.json), the 14 poems on her clock (syntagma/syntagma-data.json films)
  Acts, Beats  Save the Cat's positions laid over the 24-minute clock by proportion (BS2's 110 pages). Imposed:
             the suite is 14 poems, not a three-act feature; each beat names the poems it falls across.
  Syntagmas  runs of consecutive shots with the same intended syntagmaType (the storyboard prompt), each checked
             against Metz's reading of the same beats in the four archive cuts (syntagma/metz.js, via metz_read.js)
  Shots      one per storyboard record (WGY001–088), aligned to the suite's 88 beats (align.py): the generated
             image (spine/thumbs), the prompt that made it, her words under it, its duration on her clock, and the
             archive shots the four plan.py cuts put there.
"""
import collections, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from align import storyboard, align

# Save the Cat (Blake Snyder, 110 pages): (name, act, start page, end page, what the beat does)
STC = [
    ("Opening Image", 1, 0, 1, "A snapshot of the world and the hero before anything changes."),
    ("Set-Up", 1, 1, 12, "The hero's world, what is missing from it, and what is at stake."),
    ("Catalyst", 1, 12, 13, "The event that knocks the hero's world off its axis."),
    ("Debate", 1, 13, 25, "The hero resists or doubts the call."),
    ("Break into Two", 2, 25, 26, "The hero chooses to enter the upside-down world."),
    ("B Story", 2, 26, 30, "A second thread, often a relationship, that carries the theme."),
    ("Fun and Games", 2, 30, 55, "The promise of the premise: the new world explored."),
    ("Midpoint", 2, 55, 56, "A false victory or false defeat; the stakes rise."),
    ("Bad Guys Close In", 2, 56, 75, "Pressure from outside and doubt from inside tighten."),
    ("All Is Lost", 2, 75, 76, "The lowest point; something dies."),
    ("Dark Night of the Soul", 2, 76, 85, "The hero sits with the loss."),
    ("Break into Three", 3, 85, 86, "The answer arrives, drawn from A and B stories together."),
    ("Finale", 3, 86, 109, "The hero acts on what was learned; the world is remade."),
    ("Final Image", 3, 109, 110, "The opposite of the Opening Image: proof of change."),
]
ACTS = {1: ("Setup", "The world before, and the call out of it."), 2: ("Confrontation", "The other world, its promise and its cost."),
        3: ("Resolution", "What comes back, and what is left behind.")}
CUTS = ["suite", "scenes", "cineosis", "drift"]
METZ_FAMILY = {  # the storyboard's intended types, on Metz's table where they have a place
    "Descriptive Syntagma (DS)": "DESC", "Chronological Syntagma (CS)": "chronological (SC · SEQ · EP · ALT)",
    "Autonomous Syntagma (AS)": "AS", "Thematic Montage (TM)": "achronological (PAR · BR)", "Flashback Syntagma": "not in Metz's table (an insert or alternate flashback)"}
AGREE = {"Descriptive Syntagma (DS)": {"DESC"}, "Chronological Syntagma (CS)": {"SC", "SEQ", "EP", "ALT"},
         "Autonomous Syntagma (AS)": {"AS"}, "Thematic Montage (TM)": {"PAR", "BR"}, "Flashback Syntagma": set()}
ANGLES = ["extreme close-up", "close-up", "medium shot", "wide shot", "long shot", "aerial", "overhead", "bird's-eye",
          "low angle", "low-angle", "high angle", "high-angle", "eye-level", "point of view", "pov", "over-the-shoulder",
          "silhouette", "back to camera", "from back", "dutch"]
MOVES = ["slow motion", "dolly", "tracking", "pan", "tilt", "zoom", "crane", "handheld", "static", "locked", "push in",
         "pull back", "orbit", "fpv", "dynamic", "timelapse", "floating", "falling", "descending", "rising", "slowly"]


def clock(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def find(words, text):
    t = text.lower()
    return [w for w in words if w in t]


def load():
    D = json.load(open(os.path.join(LAB, "syntagma", "syntagma-data.json")))
    B, lines, films = D["beats"], D["lines"], D["films"]
    W = storyboard(); path, score = align(W, B)
    thumbs = {r["id"]: r["thumb"] for r in json.load(open(os.path.join(LAB, "spine", "spine-data.json")))["records"]
              if r.get("src") == "storyboard"}
    metz = json.loads(subprocess.run(["node", os.path.join(HERE, "metz_read.js")], capture_output=True, text=True, check=True).stdout)
    import yaml
    genome = yaml.safe_load(open(os.path.join(LAB, "wygwyl", "cuts", "suite", "matrix_A_patch_genome.yaml")))
    return D, B, lines, films, W, path, score, thumbs, metz, genome


def build():
    D, B, lines, films, W, path, score, thumbs, metz, genome = load()
    dur = D["duration"]; per_beat = collections.Counter(path)
    film_of = {f[0] if isinstance(f, list) else f["n"]: f for f in films}
    fname = lambda n: next((f[1] if isinstance(f, list) else f["title"]) for f in films if (f[0] if isinstance(f, list) else f["n"]) == n)

    shots = []
    for i, (w, j) in enumerate(zip(W, path)):
        b = B[j]; k = sum(1 for p in path[:i] if p == j); n = per_beat[j]
        t0 = b[2] + (b[3] - b[2]) * k / n; t1 = b[2] + (b[3] - b[2]) * (k + 1) / n
        words = " / ".join(L[4] for L in lines if L[2] < t1 and L[3] > t0)
        text = w["operativeEkphrasis"] + " " + w.get("styleConditioning", "")
        reads = {c: metz[c][j] for c in CUTS}
        agree = [c for c in CUTS if reads[c]["key"] in AGREE.get(w["syntagmaType"], set())]
        shots.append({
            "sh": i + 1, "id": w["id"], "beat": b[0], "beat_title": b[4], "poem": b[1], "poem_title": fname(b[1]),
            "t0": round(t0, 2), "t1": round(t1, 2), "dur": round(t1 - t0, 1), "match": score[i],
            "scene": w["content"], "content": w["operativeEkphrasis"], "style": w.get("styleConditioning", ""),
            "prompt": w.get("full_prompt", ""), "syntagma": w["syntagmaType"], "function": w["cineosisFunction"], "image_type": w["imageType"],
            "angle": find(ANGLES, text), "movement": find(MOVES, text), "words": words,
            "image": thumbs.get(w["id"]), "reads": {c: {"key": reads[c]["key"], "name": reads[c]["name"], "why": reads[c]["why"],
                                                          "shots": [f"{s['title']} ({s['year'] or 'n.d.'})" for s in reads[c]["shots"]],
                                                          "thumbs": [s["thumb"] for s in reads[c]["shots"]]} for c in CUTS},
            "agree": agree})

    for s in shots:
        pos = s["t0"] / dur * 110
        s["stc"] = next(k for k, x in enumerate(STC) if x[2] <= pos < x[3] or k == len(STC) - 1)
    # point beats hold at least their nearest shot
    for k, x in enumerate(STC):
        if x[3] - x[2] <= 1 and not any(s["stc"] == k for s in shots):
            near = min(shots, key=lambda s: abs(s["t0"] / dur * 110 - x[2])); near["stc"] = k

    # syntagmas: runs of the same intended type inside one Save the Cat beat
    sy, cur = [], None
    for s in shots:
        if cur and cur["stc"] == s["stc"] and cur["type"] == s["syntagma"]: cur["shots"].append(s)
        else: cur = {"stc": s["stc"], "type": s["syntagma"], "shots": [s]}; sy.append(cur)
    for n, x in enumerate(sy, 1):
        x["sy"] = n
        x["functions"] = list(dict.fromkeys(s["function"] for s in x["shots"]))
        x["read"] = {c: collections.Counter(s["reads"][c]["key"] for s in x["shots"]).most_common() for c in CUTS}
        x["agree"] = sum(len(s["agree"]) for s in x["shots"]) / (4 * len(x["shots"]))
        for s in x["shots"]: s["sy"] = n

    card = lambda s: re.search(r"\b(title|subtitle|card|fades to black)\b", s["scene"], re.I)
    chars = collections.Counter(); first = {}
    for s in shots:
        if card(s): continue
        for c in re.findall(r"\b[A-Z]{2,}\b", s["scene"]):
            if c in {"TV"}: continue
            chars[c] += 1; first.setdefault(c, s["sh"])
    settings = [s for s in shots if s["syntagma"].startswith("Descriptive") and not card(s)]
    cards = [s for s in shots if card(s)]
    return {"duration": dur, "genome": genome, "films": films, "shots": shots, "syntagmas": sy, "chars": chars, "first": first,
            "settings": settings, "cards": cards, "stc": STC}


def md(M):
    g = M["genome"]; shots = M["shots"]; sy = M["syntagmas"]; dur = M["duration"]
    o = []; w = o.append
    total_agree = sum(len(s["agree"]) for s in shots) / (4 * len(shots))
    intended = collections.Counter(s["syntagma"] for s in shots)
    read = {c: collections.Counter(s["reads"][c]["key"] for s in shots) for c in CUTS}
    w("# WYGWYL · Storymap\n")
    w("Built by `lab/matrix/build_storymap.py` from the lab's assets. Every shot is a storyboard prompt (`spine/storyboard.json`) "
      "that made a generated image, placed on her clock and set against what the four archive cuts put there. "
      "The Save the Cat acts and beats are laid over the clock by proportion; the suite itself is 14 poems.\n")
    w("## How the assets coordinate\n")
    w("| level | source | joined on |\n|---|---|---|")
    w("| Diegesis | `wygwyl/cuts/suite/matrix_A_patch_genome.yaml`, storyboard characters and settings | the suite |")
    w("| Acts, Beats | Save the Cat positions over the 24-minute clock | time on her clock |")
    w("| Syntagma (intended) | `syntagmaType` in each storyboard prompt | run of consecutive shots |")
    w("| Syntagma (read) | Metz's classifier (`syntagma/metz.js`) on each archive cut | the suite's 88 beats |")
    w("| Shot | storyboard record → generated image (`spine/thumbs/`) | `align.py`: storyboard shot → beat |")
    w("| Her words | `syntagma/syntagma-data.json` lines | time |")
    w("| Archive shots | the four `plan.py` cuts | time |\n")
    w(f"**Intended against read.** The storyboard intends {', '.join(f'{v} {k}' for k, v in intended.most_common())}. "
      f"Read by Metz's classifier, the archive cuts give: " + "; ".join(f"{c} " + ", ".join(f"{k} {v}" for k, v in read[c].most_common()) for c in CUTS) +
      f". The intended type is realised in {total_agree:.0%} of shot-by-cut pairs. Cuts that mix films read as bracket almost "
      "everywhere, so a chronological or descriptive intention is carried only where one source film holds the beat (mostly the scenes cut).\n")
    w("**Reading a shot entry** (the Opening Image, SH1, is the worked example below): *Content* is the prompt's scene, "
      "*Scene* the storyboard line, *Angle* and *Movement* the camera words the prompt itself uses (blank when it names none), "
      "*Duration* the shot's share of its beat on her clock, *Her words* what she says under it, *Image* the generated frame, "
      "*In the cuts* the archive shots each cut put there with Metz's reading of that beat, and *Match* how many of the beat title's "
      "words the storyboard line shares (0 = placed by order alone).\n")

    w("# Diegesis (D)\n")
    w(f"**Purpose:** {g['diegesis']['premise']}\n")
    w("**World rules:**")
    for r in g["diegesis"]["world_rules"]: w(f"- {r}")
    w("\n**Characters** (named in the storyboard):")
    for c, n in M["chars"].most_common():
        w(f"- **{c}** — in {n} shots, first at SH{M['first'][c]}")
    w("\n**Settings** (the descriptive shots that establish a place):")
    for s in M["settings"][:24]:
        w(f"- SH{s['sh']} · {s['scene']}")
    if len(M["settings"]) > 24: w(f"- … {len(M['settings']) - 24} more descriptive shots below")
    w("\n**Title cards and black** (text on screen, not places):")
    for s in M["cards"]: w(f"- SH{s['sh']} · {s['scene']}")
    w("\n**Events** (the 14 poems on her clock):")
    for f in M["films"]:
        n, t, a, b = (f[0], f[1], f[2], f[3]) if isinstance(f, list) else (f["n"], f["title"], f["t0"], f["t1"])
        w(f"- {n} · {t} ({clock(a)}–{clock(b)})")
    w("")

    for act in (1, 2, 3):
        name, purpose = ACTS[act]
        w(f"# Act {act} (A{act}): {name}\n")
        ks = [k for k, x in enumerate(STC) if x[1] == act]
        a0, a1 = STC[ks[0]][2] / 110 * dur, STC[ks[-1]][3] / 110 * dur
        poems = list(dict.fromkeys(s["poem_title"] for s in shots if STC[s["stc"]][1] == act))
        w(f"**Purpose:** {purpose} On the clock {clock(a0)}–{clock(a1)}, across: {', '.join(poems) or '—'}.\n")
        for k in ks:
            x = STC[k]; here = [z for z in sy if z["stc"] == k]
            if not here: continue
            hs = [s for z in here for s in z["shots"]]
            w(f"## {x[0]}\n")
            w(f"**Purpose:** {x[4]} Here: SH{hs[0]['sh']}–SH{hs[-1]['sh']}, {clock(hs[0]['t0'])}–{clock(hs[-1]['t1'])}, "
              f"{', '.join(dict.fromkeys(s['poem_title'] for s in hs))}.\n")
            for z in here:
                a, b = z["shots"][0]["sh"], z["shots"][-1]["sh"]
                w(f"### Syntagma {z['sy']} (SY{z['sy']})")
                w(f"- **Type (intended):** {z['type']} [{a}{'–' + str(b) if b != a else ''}] · on Metz's table: {METZ_FAMILY.get(z['type'], '—')}")
                w(f"- **Purpose:** {'; '.join(z['functions'])}")
                w("- **Read in the cuts:** " + " · ".join(f"{c} " + ", ".join(f"{k2}×{v}" if v > 1 else k2 for k2, v in z["read"][c]) for c in CUTS))
                w(f"- **Intended type realised:** {z['agree']:.0%} of shot-by-cut pairs\n")
                for s in z["shots"]:
                    w(f"#### Shot {s['sh']} (SH{s['sh']}) · {s['id']}")
                    w(f"- **Content:** {s['content']}")
                    w(f"- **Scene:** {s['scene']}")
                    w(f"- **Angle:** {', '.join(s['angle']) or '—'}")
                    w(f"- **Duration:** {s['dur']} s ({clock(s['t0'])}–{clock(s['t1'])}, beat {s['beat']} · {s['beat_title']} · match {s['match']})")
                    w(f"- **Movement:** {', '.join(s['movement']) or '—'}")
                    w(f"- **Function:** {s['function']} · {s['image_type']}")
                    w(f"- **Her words:** {('“' + s['words'] + '”') if s['words'] else '— (instrumental)'}")
                    if s["image"]: w(f"- **Image:** ![{s['id']}](../{s['image']})")
                    w(f"- **Prompt:** `{s['prompt']}`")
                    w("- **In the cuts:**")
                    for c in CUTS:
                        r = s["reads"][c]
                        w(f"  - {c}: {r['key']} ({r['why']}) · {'; '.join(r['shots']) or '—'}")
                    w("")
    return "\n".join(o)


def cineprompt(s):
    """[camera movement]: [establishing scene]. [additional details] — CinePrompt's base structure."""
    cam = ", ".join(s["angle"] + s["movement"]) or "Static shot"
    return f"{cam[0].upper() + cam[1:]}: {s['content'].rstrip('.')}. {s['style']}".strip()


def shotlist(M):
    o = ["const prompts = ["]
    for s in M["shots"]:
        o.append(f"  // Shot {s['sh']} (SH{s['sh']}) · {s['id']} · {s['syntagma']} · {s['function']}")
        o.append("  " + json.dumps(cineprompt(s), ensure_ascii=False) + ",\n")
    o.append("];")
    return "\n".join(o)


def chart(M):
    sy = M["syntagmas"]; dur = M["duration"]
    root = {"name": "Diegesis", "content": M["genome"]["diegesis"]["premise"], "children": []}
    for act in (1, 2, 3):
        A = {"name": f"Act {act}: {ACTS[act][0]}", "children": []}
        for k, x in enumerate(STC):
            if x[1] != act: continue
            here = [z for z in sy if z["stc"] == k]
            if not here: continue
            Bn = {"name": f"Beat {k + 1}: {x[0]}", "children": []}
            for z in here:
                Bn["children"].append({"name": f"Syntagma: {z['type']}", "read": {c: z["read"][c] for c in CUTS}, "agree": round(z["agree"], 2),
                                       "children": [{"name": f"Shot {s['sh']} (SH{s['sh']})", "content": s["content"], "image": s["image"],
                                                     "t0": s["t0"], "t1": s["t1"], "words": s["words"]} for s in z["shots"]]})
            A["children"].append(Bn)
        root["children"].append(A)
    return "// Data structure representing the narrative hierarchy\nconst data = " + json.dumps(root, ensure_ascii=False, indent=2) + ";\n"


def main():
    M = build()
    open(os.path.join(HERE, "Storymap.md"), "w").write(md(M))
    slim = {k: v for k, v in M.items() if k not in ("genome",)}
    slim["chars"] = dict(M["chars"]); slim["settings"] = [s["sh"] for s in M["settings"]]; slim["cards"] = [s["sh"] for s in M["cards"]]
    json.dump(slim, open(os.path.join(HERE, "matrix.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    if "--shotlist" in sys.argv: open(os.path.join(HERE, "Shotlist.js"), "w").write(shotlist(M))
    if "--chart" in sys.argv: open(os.path.join(HERE, "chart-data.js"), "w").write(chart(M))
    print(f"{len(M['shots'])} shots, {len(M['syntagmas'])} syntagmas → Storymap.md, matrix.json")


if __name__ == "__main__":
    main()
