"""The archive's ears. Every clip's own sound read by CLAP (laion/clap-htsat-unfused): a 512-d audio embedding that can be searched
by words ("waves on rocks", "sheep bleating", "a man shouting"), and a reading of what kind of sound it is (speech, music, field,
silence). The clips the sea and the cast use come first, then the whole forage. Resumable; streams audio, keeps nothing but numbers.
Writes cache/ears/ids.json + cache/ears/clap.npy (float16) + cache/ears/kind.json.   usage: ../.venv/bin/python archive_ears.py [all]"""
import glob, json, os, subprocess, sys, concurrent.futures as cf
import numpy as np, torch
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from transformers import ClapModel, ClapProcessor
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears"); os.makedirs(E, exist_ok=True)
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
want = []
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    for s in json.load(open(f))["scenes"]:
        for sh in s["shots"]: want += [sh["id"]] + [c["id"] for c in sh.get("sea", [])]
for v in json.load(open(os.path.join(H, "sea", "index.json")))["cast"].values(): want += [c["id"] for c in v]
if "all" in sys.argv: want += json.load(open(os.path.join(H, "cache", "ids.json")))
want = list(dict.fromkeys(want))
url = lambda i: (lib.get(i) or {}).get("video") or (clips.get(i) or {}).get("videoUrl")
ids = json.load(open(os.path.join(E, "ids.json"))) if os.path.exists(os.path.join(E, "ids.json")) else []
X = list(np.load(os.path.join(E, "clap.npy")).astype(np.float32)) if ids else []
kind = json.load(open(os.path.join(E, "kind.json"))) if os.path.exists(os.path.join(E, "kind.json")) else {}
have = set(ids); todo = [i for i in want if i not in have and url(i) and (os.path.exists(os.path.join(H, 'cache', 'aud', i + '.flac')) or os.path.exists(os.path.join(H, 'cache', 'aud', i + '.none')))]
print(len(want), "wanted ·", len(todo), "to hear", flush=True)
m = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); p = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
KINDS = {"speech": ["a man speaking", "a woman speaking", "people talking", "a narrator speaking"], "music": ["music playing", "an orchestra", "a song"],
         "field": ["wind", "water and waves", "birds and animals", "a crowd", "machines and engines", "footsteps"], "silence": ["silence", "film hiss and crackle"]}
with torch.no_grad():
    kt = p(text=[t for v in KINDS.values() for t in v], return_tensors="pt", padding=True); KT = m.get_text_features(**kt); KT = KT / KT.norm(dim=-1, keepdim=True)
kname = [k for k, v in KINDS.items() for _ in v]
import soundfile as sf
A = os.path.join(H, "cache", "aud")
def pcm(i):                                        # the local file fetch_audio.py wrote (first 12 s are enough for CLAP)
    f = os.path.join(A, i + ".flac")
    if not os.path.exists(f): return i, (np.zeros(0, np.float32) if os.path.exists(os.path.join(A, i + ".none")) else None)
    try: a, sr = sf.read(f, dtype="float32", frames=48000 * 12); return i, a
    except Exception: return i, None
def save():
    json.dump(ids, open(os.path.join(E, "ids.json"), "w")); np.save(os.path.join(E, "clap.npy"), np.array(X, np.float16)); json.dump(kind, open(os.path.join(E, "kind.json"), "w"))
torch.set_num_threads(6)
if True:
    batch = []
    for n, (i, a) in enumerate(map(pcm, todo), 1):
        if a is None: continue
        if len(a) < 4800 or float(np.abs(a).max() if len(a) else 0) < 1e-4:   # no sound at all
            kind[i] = {"k": "none"}; ids.append(i); X.append(np.zeros(512, np.float32))
        else: batch.append((i, a))
        if len(batch) >= 24 or (n == len(todo) and batch):
            with torch.no_grad():
                ia = p(audios=[b for _, b in batch], sampling_rate=48000, return_tensors="pt"); ea = m.get_audio_features(**ia); ea = ea / ea.norm(dim=-1, keepdim=True)
                s = (ea @ KT.T).numpy()
            for (j, _), e, row in zip(batch, ea.numpy(), s):
                best = {k: float(max(row[q] for q, kk in enumerate(kname) if kk == k)) for k in KINDS}
                kind[j] = {"k": max(best, key=best.get), **{k: round(v, 3) for k, v in best.items()}}; ids.append(j); X.append(e)
            batch = []
        if n % 300 == 0: save(); print(n, "of", len(todo), flush=True)
save()
import collections; print("DONE", len(ids), dict(collections.Counter(v["k"] for v in kind.values())))
