"""THE READING: every card on the blacktop typed the ways an editor thinks with it. Adds to atlas.json (run after atlas.py and look.py):
  signs      the 45 Cineosis signs (cineosis-table.json): each sign's prototype = its grounding (shot criteria + search queries, CLIP text)
             averaged with the editor's own exemplars (picks.json, CLIP image), the lab's affinity.py method moved into this CLIP space;
             scores z-scored per sign across the cards (so a sign CLIP likes everywhere doesn't win everywhere), softmax; top three kept
  comp       the composition as a vector (where the light and the edges sit, 16x9 luma + 8x4 edges + 4x3 colour), for match cuts
  bridges    for every AI shot, the archive shots closest to it by meaning (CLIP with the AI-vs-archive difference taken out: the
             'modality gap' that keeps the two on separate continents) and by composition: where a seam can hide
  poison     for every AI shot, what makes it a liability in an edit, with reasons: artefacts (melting hands/faces, garbled text),
             the forbidden (plush or 3-D characters, logos, captions, game characters), morphing (CLIP drift between four frames),
             and slop gloss (how far it leans toward 'AI' rather than 'film' in CLIP)
  pails      how much it shows the orange upturned pails (CLIP + the pails' orange), for AI and archive alike
  pound      for AI shots, the moments the motion hits (peaks of frame difference): a hit can be put on a song's beat
  cartoon    from looks.json: how cartoon it becomes under the evolved look, how much it still reads, how speckled
Writes atlas.json (in place), comp-emb.bin (int8), sign-emb.bin (int8 45 per card).  usage: .venv/bin/python slopfeeder/read.py"""
import glob, json, os, subprocess
import numpy as np, cv2, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); R = os.path.dirname(L)
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
def ci(ims):
    out = []
    for k in range(0, len(ims), 48):
        with torch.no_grad(): e = m.encode_image(torch.stack([prep(i) for i in ims[k:k + 48]])).float()
        out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
    return np.concatenate(out)
AT = json.load(open(os.path.join(D, "atlas.json"))); C = AT["cards"]
E = np.fromfile(os.path.join(D, "atlas-emb.bin"), np.int8).reshape(-1, 512).astype(np.float32) * AT["scale"]; E /= np.linalg.norm(E, axis=1, keepdims=True)
typ = np.array([c["type"] for c in C]); ai = np.where(typ == "ai")[0]; ar = np.where(typ == "archive")[0]
# ---- signs
T = json.load(open(os.path.join(R, "cineosis-table.json")))["signs"]; G = {str(s["n"]): s for f in sorted(glob.glob(os.path.join(R, "grounding", "g*.json"))) for s in json.load(open(f))}
picks = json.load(open(os.path.join(R, "picks.json"))); P = []
for s in T:
    g = G.get(str(s["n"]), {}); txt = [f"a film still: {(g.get('shot_criteria') or s['definition'])[:280]}"] + [f"a film still of {q}" for q in g.get("queries", [])[:6]]
    tv = ct(txt).mean(0); ims = [Image.open(p).convert("RGB") for p in (os.path.join(L, "thumbs", i + ".jpg") for i, _ in picks.get(str(s["n"]), [])) if os.path.exists(p)]
    v = tv / np.linalg.norm(tv)
    if ims: iv = ci(ims).mean(0); v = .5 * v + .5 * iv / np.linalg.norm(iv)
    P.append(v / np.linalg.norm(v))
P = np.stack(P); S = E @ P.T; Z = (S - S.mean(0)) / (S.std(0) + 1e-9); Pz = np.exp(Z * 1.5); Pz /= Pz.sum(1, keepdims=True)
for i, c in enumerate(C): c["signs"] = [[T[j]["symbol"], round(float(Pz[i, j]), 3)] for j in np.argsort(-Pz[i])[:3]]
sc = float(np.abs(Z).max() / 127); np.clip(np.round(Z / sc), -127, 127).astype(np.int8).tofile(os.path.join(D, "sign-emb.bin"))
AT["signs"] = [{"symbol": s["symbol"], "name": s["name"], "type": s["image_type"], "n": s["n"]} for s in T]; AT["sign_scale"] = sc
print("signs typed; most common lead signs:", sorted(((sum(1 for c in C if c["signs"][0][0] == s["symbol"]), s["symbol"]) for s in T), reverse=True)[:8], flush=True)
# ---- composition
def comp(p):
    im = cv2.imread(p)
    if im is None: return np.zeros(144 + 32 + 24, np.float32)
    im = cv2.resize(im, (160, 90)); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    lum = cv2.resize(g, (16, 9), interpolation=cv2.INTER_AREA).ravel(); lum = (lum - lum.mean()) / (lum.std() + 1e-6)
    ed = cv2.resize(cv2.Canny((g * 255).astype(np.uint8), 60, 160).astype(np.float32) / 255, (8, 4), interpolation=cv2.INTER_AREA).ravel(); ed = (ed - ed.mean()) / (ed.std() + 1e-6)
    lab = cv2.resize(cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32), (4, 3), interpolation=cv2.INTER_AREA)[..., 1:].ravel(); lab = (lab - 128) / 24
    v = np.concatenate([lum * 1.0, ed * .8, lab * .6]); return v / (np.linalg.norm(v) + 1e-9)
K = np.stack([comp(os.path.join(D, c["thumb"])) for c in C]).astype(np.float32)
csc = float(np.abs(K).max() / 127); np.clip(np.round(K / csc), -127, 127).astype(np.int8).tofile(os.path.join(D, "comp-emb.bin")); AT["comp_scale"] = csc; AT["comp_dim"] = K.shape[1]
# ---- bridges: the modality gap taken out
Ec = E.copy(); Ec[ai] -= E[ai].mean(0); Ec[ar] -= E[ar].mean(0); Ec /= np.linalg.norm(Ec, axis=1, keepdims=True) + 1e-9
for i in ai:
    s1 = Ec[ar] @ Ec[i]; s2 = K[ar] @ K[i]
    C[i]["bridges"] = {"meaning": [C[ar[j]]["id"] for j in np.argsort(-s1)[:8]], "frame": [C[ar[j]]["id"] for j in np.argsort(-s2)[:8]],
                       "both": [C[ar[j]]["id"] for j in np.argsort(-(s1 / s1.std() + s2 / s2.std()))[:8]]}
for i in ar: s1 = Ec[ai] @ Ec[i]; C[i]["bridges"] = {"meaning": [C[ai[j]]["id"] for j in np.argsort(-s1)[:6]]}
gap_before = float(np.mean(E[ai] @ E[ar].mean(0))); print("bridges built (modality gap removed)", flush=True)
# ---- pails (all cards)
pt = ct(["orange plastic buckets turned upside down in wet sand", "people pounding buckets into the ground", "a row of orange pails on a beach"]).mean(0); pt /= np.linalg.norm(pt)
nt = ct(["a beach", "a film still", "people working"]).mean(0); nt /= np.linalg.norm(nt)
pv = E @ pt - E @ nt; pv = (pv - np.quantile(pv, .5)) / (np.quantile(pv, .98) - np.quantile(pv, .5) + 1e-9)
for i, c in enumerate(C): c["pails"] = round(float(np.clip(.75 * pv[i] + .25 * min(1, (c.get("colour") or {}).get("chars", {}).get("orange", 0) * 12), 0, 1)), 3)
# ---- poison (AI)
BAD = {"artefact": ["an AI generated video frame with distorted melting hands and faces", "garbled nonsense text and warped letters", "a glitchy morphing deformed image"],
       "plush": ["3D plush toy characters", "clay figurines", "a cute 3D cartoon mascot", "a video game character render"],
       "logo": ["a brand logo printed on a bucket", "a corporate logo", "subtitles and captions on screen"],
       "gloss": ["a glossy cinematic AI video still, hyper detailed, trailer polish"]}
GOOD = ct(["a frame from an old documentary film", "a plain photograph", "a flat 2D vector illustration"]).mean(0); GOOD /= np.linalg.norm(GOOD)
BT = {k: ct(v) for k, v in BAD.items()}; raw = {}
for k, v in BT.items():
    s = (E[ai] @ v.T).max(1) - E[ai] @ GOOD; raw[k] = (s - np.median(s)) / (np.quantile(s, .95) - np.median(s) + 1e-9)
# morphing: CLIP of four frames across the shot
def frames(c):
    a, b = c["in"], c["out"]; ims = []
    for t in np.linspace(a + .15, b - .15, 4):
        r = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{t:.2f}", "-i", os.path.join(D, c["src"]), "-frames:v", "1", "-vf", "scale=320:180", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(r) == 320 * 180 * 3: ims.append(Image.fromarray(np.frombuffer(r, np.uint8).reshape(180, 320, 3)))
    return ims
def hits(c):   # moments the motion hits, in source time
    a, b = c["in"], c["out"]
    r = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{a:.2f}", "-i", os.path.join(D, c["src"]), "-t", f"{b - a:.2f}", "-vf", "fps=24,scale=96:54,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(r, np.uint8).reshape(-1, 54, 96).astype(np.float32)
    if len(f) < 12: return []
    e = np.abs(np.diff(f, axis=0)).mean((1, 2)); d = e - np.convolve(e, np.ones(9) / 9, "same"); thr = d.mean() + 1.2 * d.std(); out = []
    for k in range(2, len(d) - 2):
        if d[k] > thr and d[k] == d[k - 2:k + 3].max() and (not out or k / 24 - (out[-1] - a) > .25): out.append(round(a + (k + 1) / 24, 3))
    return out
morph = []
for n, i in enumerate(ai):
    c = C[i]; ims = frames(c)
    if len(ims) >= 3: F = ci(ims); morph.append(float(np.mean(1 - (F[1:] * F[:-1]).sum(1))))
    else: morph.append(0.0)
    c["pound"] = hits(c)
    if n % 50 == 0: print(f"  {n}/{len(ai)} pickups read for morphing and hits", flush=True)
morph = np.array(morph); mz = (morph - np.median(morph)) / (np.quantile(morph, .95) - np.median(morph) + 1e-9)
for n, i in enumerate(ai):
    parts = {"artefacts": raw["artefact"][n], "plush or 3-D": raw["plush"][n], "logo or captions": raw["logo"][n], "slop gloss": raw["gloss"][n] * .6, "morphing": mz[n]}
    p = float(np.clip(np.mean(sorted(parts.values())[-2:]) * .55, 0, 1))
    C[i]["poison"] = round(p, 3); C[i]["why"] = [k for k, v in sorted(parts.items(), key=lambda x: -x[1]) if v > .7][:3]
# ---- cartoon (from looks.json)
LK = json.load(open(os.path.join(D, "looks.json")))["cards"] if os.path.exists(os.path.join(D, "looks.json")) else {}
if LK:   # a rank across the corpus: how cartoon it becomes, how much it still reads, how little speckle (1 = the best candidate)
    ks = [c for c in C if c["id"] in LK]; z = lambda v: (np.array(v) - np.mean(v)) / (np.std(v) + 1e-9)
    sc_ = z([LK[c["id"]]["becomes"] for c in ks]) + .7 * z([LK[c["id"]]["reads"] for c in ks]) - z([LK[c["id"]]["speckle"] for c in ks]); rk = sc_.argsort().argsort() / max(1, len(ks) - 1)
    for c, r_ in zip(ks, rk): c["cartoon"] = round(float(r_), 3)
json.dump(AT, open(os.path.join(D, "atlas.json"), "w"), ensure_ascii=False, separators=(",", ":"))
srt = sorted((C[i] for i in ai), key=lambda c: -c["poison"])
print("poison, worst:", [(c["title"], c["poison"], c["why"]) for c in srt[:6]], flush=True)
print("pails, most:", [(c["type"], (c["title"] or "")[:30], c["pails"]) for c in sorted(C, key=lambda c: -c["pails"])[:8]], flush=True)
print("archive with pails > .5:", sum(1 for i in ar if C[i]["pails"] > .5), "· AI shots with pound hits:", sum(1 for i in ai if len(C[i]["pound"]) >= 2), flush=True)
