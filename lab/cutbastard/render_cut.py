"""CUTBASTARD · render: plan.json → cut.mp4 + the patch matrices.

    python3 render_cut.py <slug>

Picture: one shot per patch, full frame (letter/pillar-boxed to 1280×720, never cropped), straight cuts on the patch
edges; an 8-frame dip to black only at chapter seams. Frame counts come from the cumulative clock, so 169 patches never
drift against the suite record. Sound: the suite audio only.
Writes ../wygwyl/cuts/<slug>/: cut.mp4, patches.json (lab), matrix_A_patch_genome.yaml, matrix_B_story_map.md.
Matrix C (EDL) and D (OTIO) stay locked until asked for.
"""
import json, os, subprocess, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
FPS, W, H = 24, 1280, 720
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]

def smpte(t, base=3600):
    f = round((t + base) * FPS); return f"{f // (3600 * FPS):02d}:{f // (60 * FPS) % 60:02d}:{f // FPS % 60:02d}:{f % FPS:02d}"

def run(a):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *a], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-600:])

def main(slug):
    d = os.path.join(LAB, "wygwyl", "cuts", slug)
    plan = json.load(open(os.path.join(d, "plan.json")))
    P = plan["patches"]
    parts = os.path.join(d, "parts"); os.makedirs(parts, exist_ok=True)
    frames = [round(P[k + 1]["t0"] * FPS) - round(p["t0"] * FPS) if k + 1 < len(P) else round(p["t1"] * FPS) - round(p["t0"] * FPS) for k, p in enumerate(P)]
    files = []
    for k, (p, N) in enumerate(zip(P, frames)):
        first = k == 0 or P[k - 1]["chapter"] != p["chapter"]; last = k == len(P) - 1 or P[k + 1]["chapter"] != p["chapter"]
        fx = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps={FPS}"
        if first: fx += ",fade=in:0:8"
        if last: fx += f",fade=out:{max(0, N - 8)}:8"
        out = os.path.join(parts, f"{k:03d}.mp4")
        # a clip shorter than its window (rare rounding) holds its last frame rather than loop
        run(["-ss", f"{p['clip']['in']:.3f}", "-i", os.path.join(LAB, p["clip"]["clip"]), "-vf", fx + f",tpad=stop_mode=clone:stop_duration=1",
             "-frames:v", str(N), *ENC, out])
        files.append(out)
        if k % 20 == 0: print(f"{slug}: {k + 1}/{len(P)}", flush=True)
    lst = os.path.join(parts, "list.txt"); open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    silent = os.path.join(d, "silent.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
    run(["-i", silent, "-i", os.path.join(LAB, "wygwyl", "WYGWYL_Suite_Audio.mp3"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(d, "cut.mp4")])
    os.remove(silent)
    # ---- lab patches ----
    json.dump([{"id": p["id"], "t0": p["t0"], "t1": p["t1"], "chapter": p["chapter"], "film": p["film"], "line": p["line"], "why": p["why"],
                "codes": p["codes"], "clip": p["clip"]} for p in P], open(os.path.join(d, "patches.json"), "w"), ensure_ascii=False)
    # ---- Matrix A: YAML patch genome ----
    ana = json.load(open(os.path.join(LAB, "cache", "analysis.json")))
    corpus = json.load(open(os.path.join(LAB, "cache", "corpus.json")))
    cat = json.load(open(os.path.join(LAB, "wygwyl", "WYGWYL_Forage_Catalogue.json")))
    obs = {c["id"]: c.get("observed") for c in cat["catalogue"]}
    for b in cat["beats"]:
        for c in b["candidates"]:
            if c.get("observed") and c.get("grade") != "U": obs[c["id"]] = c["observed"]
    def cam(p):
        a = ana.get(p["clip"]["id"]) or {}
        mv = "moving camera" if p["clip"]["pan"] > 2.5 else ("drifting" if p["clip"]["pan"] > 1.2 else "locked-off")
        return f"{a.get('scale') or 'unknown scale'} · {mv} · motion {p['clip']['motion']:.3f}"
    def light(p):
        a = ana.get(p["clip"]["id"]) or {}
        stock = "black-and-white" if a.get("hue") is None else f"colour, hue {int(a['hue'])}°"
        return f"{stock}, luminance {a.get('lum', 0):.2f} · sound: suite score only, energy {p['energy']:.2f}"
    def ents(p):
        a = ana.get(p["clip"]["id"]) or {}
        return [s["label"] for s in (a.get("subjects") or [])[:3]]
    def action(p):
        o = obs.get(p["clip"]["id"])
        if o and not o.lower().startswith("unreviewed"): return o
        return f"{', '.join(ents(p)) or 'scene'} from '{p['clip']['title']}' ({p['clip']['year'] or 'n.d.'})"
    syntag = {"scenes": "continuous", "drift": "accumulative", "suite": "alternating", "cineosis": "insertive"}[slug]
    genome = {
        "title": f"WYGWYL · {plan['title']}",
        "seed": "Fourteen poem films on one 24-minute clock, cut from archival shots: one full-frame shot per patch, never repeated.",
        "diegesis": {"premise": "A poem suite read over a continuous score; images are found footage standing in for its situations.",
                     "world_rules": ["one shot per patch, full frame", "no shot repeats", "cuts fall on cue edges and score onsets",
                                     "found people are not the poem's characters"],
                     "core_entities": sorted({e for p in P for e in ents(p)})[:14],
                     "core_locations": sorted({p["clip"]["title"] for p in P})[:14]},
        "macro_structure": [{"unit_id": f"U{f['n']}", "kind": "sequence", "function": f"{f['title']}: {smpte(f['container'][0])}–{smpte(f['container'][1])}"} for f in cat["films"]],
        "beat_structure": [], "patch_timeline": []}
    seen = set()
    for p in P:
        key = (p["chapter"], p.get("line") or p["id"])
        if key not in seen:
            seen.add(key)
            genome["beat_structure"].append({"beat_id": f"B{len(seen):03d}", "parent_unit": f"U{p['chapter']}", "syntagma_type": syntag,
                                             "pressure_shift": (p["screen"] or p["movement"] or "instrumental").lower()})
        genome["patch_timeline"].append({
            "patch_id": p["id"], "start_time": smpte(p["t0"]), "end_time": smpte(p["t1"]), "location": f"{p['clip']['title']} ({p['clip']['year'] or 'n.d.'})",
            "entities_present": ents(p), "action_summary": action(p), "camera_relation": cam(p), "light_sound_state": light(p),
            "patch_trigger": {"cue": "poem cue begins", "onset": "score onset inside the line", "chapter": "chapter seam", "gap": "instrumental gap"}[p["trigger"]],
            "rehydration_seed": f"{action(p)}; {cam(p)}; carrying the line: “{(p['line'] or p['screen'] or p['movement'] or '').strip()[:140]}”",
            "source": {"clip": p["clip"]["id"], "in": p["clip"]["in"], "out": p["clip"]["out"], "page": p["clip"]["page"]}, "why": p["why"]})
    yaml.safe_dump(genome, open(os.path.join(d, "matrix_A_patch_genome.yaml"), "w"), sort_keys=False, allow_unicode=True, width=140)
    # ---- Matrix B: story map ----
    md = [f"# WYGWYL · {plan['title']}", "", plan["idea"], "", "# Diegesis", genome["diegesis"]["premise"], "", "# Macro Structure"]
    cur_ch, cur_line = None, None
    for p in P:
        if p["chapter"] != cur_ch:
            cur_ch = p["chapter"]; md += ["", f"## U{p['chapter']} · {p['film']}"]
        ln = p["line"] or p["screen"] or p["movement"] or "instrumental"
        if ln != cur_line:
            cur_line = ln; md += ["", f"### {ln[:110]}"]
        md += [f"#### {p['id']} - {smpte(p['t0'])} → {smpte(p['t1'])}",
               f"- **Action**: {action(p)}", f"- **Camera/Environment**: {cam(p)}; {light(p)}",
               f"- **Pressure Shift**: {p['trigger']} — {p['why']}", f"- **Seed**: {p['clip']['title']} [{p['clip']['id'][:8]}] {p['clip']['in']:.2f}–{p['clip']['out']:.2f}s"]
    open(os.path.join(d, "matrix_B_story_map.md"), "w").write("\n".join(md) + "\n")
    # ---- index ----
    ip = os.path.join(LAB, "wygwyl", "cuts", "index.json")
    idx = json.load(open(ip)) if os.path.exists(ip) else []
    idx = [c for c in idx if c["slug"] != slug] + [{"slug": slug, "title": plan["title"], "idea": plan["idea"], "film": f"wygwyl/cuts/{slug}/cut.mp4",
                                                   "duration": P[-1]["t1"], "patches": f"wygwyl/cuts/{slug}/patches.json",
                                                   "genome": f"wygwyl/cuts/{slug}/matrix_A_patch_genome.yaml", "story": f"wygwyl/cuts/{slug}/matrix_B_story_map.md"}]
    order = ["suite", "scenes", "cineosis", "drift"]
    idx.sort(key=lambda c: order.index(c["slug"]) if c["slug"] in order else 9)
    json.dump(idx, open(ip, "w"), indent=1)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", os.path.join(d, "cut.mp4")], capture_output=True, text=True).stdout.strip()
    print("DONE", slug, dur, "s")

if __name__ == "__main__":
    main(sys.argv[1])
