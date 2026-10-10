"""MARKOV SAM · NORSE: what each archival voice sounds like, so voices can be seen and chosen as pictures are.
For every utterance in voices.json:
  shape   from its own seconds of sound: loudness over time in 40 steps (the waveform drawn on its card and in the timeline), and how
          fast it speaks
  voice   a man, a woman, a child, or several voices        from the clip's CLAP embedding (archive_ears.py: the clip's sound as a
  way     narration, conversation, interview, announcer,     whole, already heard), zero-shot against these descriptions. Man or
          a speech to a crowd, singing                       woman by margin, as the found Odyssey casts; child and several only when
  under   music, a quiet room, outdoors                      clearly ahead; the others by their lead over each label's corpus mean.
          (Hearing each sentence alone with CLAP is better and takes about 1.7 s a sentence here: hours for the whole set.)
Adds e (shape), vc, wy, un, ws (words a second) to every utterance in voices.json.   usage: ../.venv/bin/python norse/voicekinds.py [limit]"""
import json, os, sys, time
import numpy as np, soundfile as sf, torch
from scipy.signal import resample_poly
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N); A = os.path.join(L, "odyssey", "cache", "aud")
V = json.load(open(os.path.join(N, "voices.json")))
VID = {x.get("video"): x["id"] for f in ("odyssey/all/library.json", "markov/library.json") for x in json.load(open(os.path.join(L, f)))["shots"] if x.get("video")}
LIM = int(sys.argv[1]) if len(sys.argv) > 1 else len(V["utts"])
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
LABELS = {"vc": [("man", "a man speaking"), ("woman", "a woman speaking"), ("child", "a child speaking"), ("many", "several people talking at once")],
          "wy": [("narration", "a narrator reading calmly, voice-over"), ("conversation", "two people having a conversation"), ("interview", "a person answering questions in an interview"),
                 ("announcer", "an excited radio or newsreel announcer"), ("speech", "a man giving a speech to a crowd through a microphone"), ("song", "a person singing")],
          "un": [("music", "speech with music playing underneath"), ("quiet", "speech in a quiet room"), ("outdoors", "speech outdoors with wind and street noise")]}
with torch.no_grad():
    TX = {g: cm.get_text_features(**cp(text=[p for _, p in v], return_tensors="pt", padding=True)) for g, v in LABELS.items()}
    TX = {g: (t / t.norm(dim=-1, keepdim=True)).numpy() for g, t in TX.items()}
D36 = "0123456789abcdefghijklmnopqrstuvwxyz"
def seg(u):
    i = VID.get(u["v"]); p = os.path.join(A, (i or "") + ".flac")
    if not i or not os.path.exists(p): return None, None
    info = sf.info(p); a, sr = sf.read(p, start=int(max(0, u["t0"] - .05) * info.samplerate), stop=int((u["t1"] + .05) * info.samplerate), dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    return (a, sr) if len(a) > sr * .3 else (None, None)
def shape(a):
    n = 40; k = max(1, len(a) // n); r = np.sqrt((a[: k * n].reshape(n, k) ** 2).mean(1)); db = 20 * np.log10(r + 1e-6); top = np.percentile(db, 95)
    return "".join(D36[int(round(x * 35))] for x in np.clip((db - (top - 36)) / 36, 0, 1))
eids = json.load(open(os.path.join(L, "odyssey", "cache", "ears", "ids.json"))); CL = np.load(os.path.join(L, "odyssey", "cache", "ears", "clap.npy")).astype(np.float32); erow = {i: n for n, i in enumerate(eids)}
CL /= np.linalg.norm(CL, axis=1, keepdims=True) + 1e-9
ok, rows = [], []; t0 = time.time()
for k, u in enumerate(V["utts"][:LIM]):
    a, sr = seg(u)
    if a is not None: u["e"] = shape(a)
    u["ws"] = round(len(u["s"].split()) / max(.3, u["t1"] - u["t0"]), 1)
    r = erow.get(VID.get(u["v"]))
    if r is not None and np.abs(CL[r]).sum() > 0: ok.append(k); rows.append(r)
    if k and k % 2000 == 0: print(f"  {k} · {time.time() - t0:.0f}s", flush=True)
E = CL[rows]; S = {g: E @ T.T for g, T in TX.items()}
for n, k in enumerate(ok):
    u = V["utts"][k]; v = S["vc"][n]; d = v[0] - v[1]
    u["vc"] = "child" if v[2] > max(v[0], v[1]) + .02 else "many" if v[3] > max(v[0], v[1]) + .03 else ("man" if d > .005 else "woman" if d < -.005 else "")
for g in ("wy", "un"):
    C = S[g] - S[g].mean(0)
    for n, k in enumerate(ok): V["utts"][k][g] = LABELS[g][int(C[n].argmax())][0]
json.dump(V, open(os.path.join(N, "voices.json"), "w"), separators=(",", ":"), ensure_ascii=False)
import collections
for g in LABELS: print(g, collections.Counter(V["utts"][k][g] for k in ok).most_common())
print(len(ok), "voices heard ·", f"{time.time() - t0:.0f}s")
