"""archive_words.py on the Mac's GPU (mlx-whisper, base.en): the same transcripts, written to words.<k>.json for shard k of n.
Runs beside the CPU workers.   usage: ~/.cache/mlxw-venv/bin/python archive_words_mlx.py k n"""
import json, os, sys, glob
import numpy as np, soundfile as sf, mlx_whisper
from scipy.signal import resample_poly
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears"); A = os.path.join(H, "cache", "aud")
k, n = int(sys.argv[1]), int(sys.argv[2]); P = os.path.join(E, f"words.{k}.json")
done = json.load(open(os.path.join(E, "words.json")))
for f in glob.glob(os.path.join(E, "words.*.json")): done.update(json.load(open(f)))
out = json.load(open(P)) if os.path.exists(P) else {}
todo = [f[:-5] for f in sorted(os.listdir(A)) if f.endswith(".flac") and f[:-5] not in done][k::n]
print(len(todo), "clips to transcribe on the GPU", flush=True)
for c, i in enumerate(todo, 1):
    try: a, sr = sf.read(os.path.join(A, i + ".flac"), dtype="float32"); a = resample_poly(a, 1, 3).astype(np.float32) if sr == 48000 else a
    except Exception: continue
    if len(a) < 8000: out[i] = {"text": "", "words": []}; continue
    r = mlx_whisper.transcribe(a, path_or_hf_repo="mlx-community/whisper-base.en-mlx", word_timestamps=True, condition_on_previous_text=False)
    ws = [[w["word"].strip(), round(w["start"], 2), round(w["end"], 2), round(w["probability"], 2)] for s in r["segments"] for w in s.get("words", [])
          if not s.get("no_speech_prob", 0) > .6]
    out[i] = {"text": " ".join(w[0] for w in ws), "words": ws, "conf": round(float(np.mean([w[3] for w in ws])), 2) if ws else 0}
    if c % 100 == 0: json.dump(out, open(P, "w")); print(c, "of", len(todo), "·", out[i]["text"][:70], flush=True)
json.dump(out, open(P, "w")); print("DONE", len(out))
