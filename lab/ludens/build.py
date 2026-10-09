"""HOMO LUDENS data: the Slopfeeder field as a playing surface for the ball games (putt.html, tennis.html).
Each shot: its place in the field (UMAP, slopfeeder/field.json), its picture, its playable media and in-point, its flipbook, poison,
and a 32-d PCA of its CLIP vector calibrated back to full cosine, so a page can score any cut live as the lab does (sea-core.js:
a Gaussian of cosine around .72). Holes: the story cut's riverbed shots (they carry a line, or are a poison turn) that live in the field.
Writes ludens/corpus.json.   usage: python3 lab/ludens/build.py"""
import json, os
import numpy as np
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SF = os.path.join(L, "slopfeeder")
FD = json.load(open(os.path.join(SF, "field.json"))); A = json.load(open(os.path.join(SF, "atlas.json")))["cards"]; IX = {c["id"]: i for i, c in enumerate(A)}
E = np.fromfile(os.path.join(SF, "atlas-emb.bin"), np.int8).reshape(len(A), -1).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
SP = json.load(open(os.path.join(SF, "sprites.json")))["at"]
cards = [c for c in FD["cards"] if c["id"] in IX and c["t"] in ("ai", "archive") and os.path.exists(os.path.join(SF, c["th"]))]
V = np.stack([E[IX[c["id"]]] for c in cards]); mu = V.mean(0); _, _, Wt = np.linalg.svd(V - mu, full_matrices=False); P = (V - mu) @ Wt[:32].T; P /= np.linalg.norm(P, axis=1, keepdims=True) + 1e-9
pr = np.random.default_rng(0).integers(0, len(cards), (6000, 2)); a, b = np.polyfit((P[pr[:, 0]] * P[pr[:, 1]]).sum(1), (V[pr[:, 0]] * V[pr[:, 1]]).sum(1), 1)
AF = [c["aff"] for c in cards if c.get("aff")]; AM = {k: sum(x[k] for x in AF) / len(AF) for k in AF[0]}   # chapter: the song a shot fits best relative to how all shots fit it
out = []
for c, p in zip(cards, P):
    a_ = A[IX[c["id"]]]; ai = c["t"] == "ai"
    out.append({"id": c["id"], "k": "ai" if ai else "ar", "x": round(c["xy"][0], 4), "y": round(c["xy"][1], 4), "th": "slopfeeder/" + c["th"],
                "m": ("slopfeeder/" + c["m"]) if ai else c["m"], "ss": round(a_.get("in") or 0, 2) if ai else None, "du": round((a_.get("out", 0) - a_.get("in", 0)) if ai else (c.get("du") or 4), 2),
                "ti": c.get("ti", "")[:60], "w": c.get("w"), "ch": max(c["aff"], key=lambda k: c["aff"][k] - AM[k]) if c.get("aff") else None, "src": (c.get("ti") or "")[:24] if not ai else "AI pickups", "y0": c.get("y"), "po": round(a_.get("poison") or 0, 2), "mc": round(c.get("mc", 0), 3), "sp": SP.get(c["id"]), "e": [int(round(v * 127)) for v in p]})
# holes: riverbed shots of the story cut (a line, or a poison turn), in story order, that are in the field
st = json.load(open(os.path.join(SF, "lattice", "story.json"))); have = {c["id"] for c in out}; holes = []
for col in st["cols"]:
    x = col["cands"][0]
    if col.get("hold") and x.get("id") in have and x["id"] not in [h["id"] for h in holes]: holes.append({"id": x["id"], "act": col["act"], "cap": col.get("cap", "")})
CH = [["26", "I", "THE BUCKET BET"], ["14", "II", "THE RENDER FLEET"], ["13", "III", "THE COMMUNION"], ["23", "IV", "THE CHORUS"], ["20", "V", "THE MAINFRAME CONFESSION"], ["09", "VI", "THE RECURSION"], ["06", "VII", "GO HOME AND BE FREE"], ["07", "VIII", "CLEANSE THE MEMORY"]]
json.dump({"chapters": CH, "cal": [round(float(a), 4), round(float(b), 4)], "sprites": {"fw": 128, "fh": 72, "nf": 12, "path": "slopfeeder/sprites/s%03d.jpg"}, "cards": out, "holes": holes}, open(os.path.join(L, "ludens", "corpus.json"), "w"), separators=(",", ":"))
print(len(out), "shots ·", len(holes), "holes ·", f"cal {a:.3f}x+{b:.3f}", "·", os.path.getsize(os.path.join(L, "ludens", "corpus.json")) // 1024, "KB")
