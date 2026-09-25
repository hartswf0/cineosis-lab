"""CUTBASTARD · timeline: carve the WYGWYL suite clock into patches.

Segments are the poem's cue intervals and the instrumental gaps between them (the suite's own boundaries — every
segment edge is a hard cut). Each segment is split into patches of 6–12 s (target 9); internal patch cuts are
snapped to the strongest audio onset within ±0.6 s so the picture breathes with the score. A gap shorter than
6 s is folded into its neighbour. Audio energy (RMS per patch, normalised per chapter) is kept for pacing.

Writes cutbastard/patches.json.
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
W = os.path.join(LAB, "wygwyl")
TARGET, LO, HI, SNAP = 9.0, 6.0, 12.0, 0.6
SR, HOP = 11025, 256

def audio_features(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = len(x) // HOP
    fr = x[: n * HOP].reshape(n, HOP)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    spec = np.abs(np.fft.rfft(fr * np.hanning(HOP), axis=1))
    flux = np.maximum(0, np.diff(spec, axis=0, prepend=spec[:1])).sum(1)
    flux = (flux - np.median(flux)) / (flux.std() + 1e-9)
    return rms, flux, HOP / SR

def main():
    cat = json.load(open(os.path.join(W, "WYGWYL_Forage_Catalogue.json")))
    cut = json.load(open(os.path.join(W, "WYGWYL_Forage_Cut.json")))
    films, cues, worlds, beats = cat["films"], cat["cues"], {w["n"]: w for w in cat["worlds"]}, cat["beats"]
    T = cut["duration"]
    rms, flux, dt = audio_features(os.path.join(W, "WYGWYL_Suite_Audio.mp3"))
    # --- segments: cue intervals + gaps, hard edges ---
    bounds = sorted({0.0, T} | {round(c["start"], 3) for c in cues} | {round(c["start"] + c["duration"], 3) for c in cues if c["start"] + c["duration"] < T} | {round(f["container"][0], 3) for f in films})
    segs = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a < 0.05:
            continue
        cue = next((c for c in cues if c["start"] - 1e-3 <= a < c["start"] + c["duration"] - 1e-3), None)
        segs.append({"t0": a, "t1": b, "cue": cues.index(cue) if cue else None})
    # fold short gaps (no cue) into the previous segment of the same chapter
    film_of = lambda t: next(f for f in reversed(films) if t >= f["container"][0] - 1e-3)
    merged = []
    for s in segs:
        if merged and (s["t1"] - s["t0"] < LO) and film_of(s["t0"])["n"] == film_of(merged[-1]["t0"])["n"]:
            merged[-1]["t1"] = s["t1"]
        else:
            merged.append(s)
    # a leading short segment folds forward
    out = []
    for s in merged:
        if out and out[-1]["t1"] - out[-1]["t0"] < LO and film_of(out[-1]["t0"])["n"] == film_of(s["t0"])["n"]:
            s["t0"] = out.pop()["t0"]
        out.append(s)
    # --- patches ---
    patches, pid = [], 0
    for si, s in enumerate(out):
        L = s["t1"] - s["t0"]
        n = max(1, round(L / TARGET))
        while L / n > HI: n += 1
        while n > 1 and L / n < LO: n -= 1
        edges = [s["t0"] + L * k / n for k in range(n + 1)]
        for k in range(1, n):                           # snap internal cuts to onsets
            e = edges[k]; i0, i1 = int((e - SNAP) / dt), int((e + SNAP) / dt)
            if i1 > i0:
                j = i0 + int(np.argmax(flux[i0:i1]))
                cand = j * dt
                if edges[k - 1] + LO * .8 < cand < edges[k + 1] - LO * .8:
                    edges[k] = cand
        f = film_of(s["t0"]); w = worlds[f["n"]]
        cue = cues[s["cue"]] if s["cue"] is not None else None
        for k in range(n):
            a, b = edges[k], edges[k + 1]
            e = rms[int(a / dt): max(int(a / dt) + 1, int(b / dt))].mean()
            beat = next((x for x in beats if cut["shots"][x["id"] - 1]["start"] - 1e-3 <= (a + b) / 2 < cut["shots"][x["id"] - 1]["end"]), None)
            mv = None
            if w.get("movements"):
                win = f["container"]; tot = sum(m["seconds"] for m in w["movements"]); sc = (win[1] - win[0]) / tot
                loc = ((a + b) / 2 - win[0]) / sc
                mv = next((m for m in reversed(w["movements"]) if m["start"] <= loc), w["movements"][0])
            patches.append({"id": f"P{pid:03d}", "t0": round(a, 3), "t1": round(b, 3), "dur": round(b - a, 3),
                            "segment": si, "k": k, "of": n, "chapter": f["n"], "film": f["title"],
                            "cue": s["cue"], "line": cue["text"] if cue else "", "screen": cue.get("screen") if cue else "",
                            "movement": mv["label"] if mv else None, "beat": beat["id"] if beat else None,
                            "beat_title": beat["title"] if beat else None, "codes": [{"34O": "34a", "34S": "34b"}.get(str(c), str(c)) for c in beat.get("codes", [])] if beat else [],
                            "energy": float(e), "trigger": "cue" if k == 0 and cue else ("chapter" if k == 0 and abs(a - f["container"][0]) < .05 else ("gap" if k == 0 else "onset"))})
            pid += 1
    patches[-1]["t1"] = round(T, 3); patches[-1]["dur"] = round(T - patches[-1]["t0"], 3)   # the last cut ends with the record
    # energy normalised within chapter (0..1) for pacing
    for n_ in {p["chapter"] for p in patches}:
        ps = [p for p in patches if p["chapter"] == n_]
        lo, hi = min(p["energy"] for p in ps), max(p["energy"] for p in ps)
        for p in ps: p["energy"] = round((p["energy"] - lo) / (hi - lo + 1e-9), 3)
    json.dump({"duration": T, "patches": patches}, open(os.path.join(HERE, "patches.json"), "w"), indent=1, ensure_ascii=False)
    d = [p["dur"] for p in patches]
    print(len(out), "segments →", len(patches), "patches; dur min", round(min(d), 1), "median", round(float(np.median(d)), 1), "max", round(max(d), 1),
          "; total", round(sum(d), 2), "of", T)

if __name__ == "__main__":
    main()
