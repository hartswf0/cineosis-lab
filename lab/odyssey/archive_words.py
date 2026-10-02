"""What the archive's people actually say. Every clip CLAP heard as speech (archive_ears.py) is transcribed with word timestamps
(faster-whisper base.en, int8), so an Odyssey line can find the archival clip whose real words echo it. Resumable.
Writes cache/ears/words.json {id: {"text", "words": [[w, t0, t1]...], "lang_p"}}.   usage: ../.venv/bin/python archive_words.py [k n]
With k n it transcribes only every n-th clip from the k-th (parallel workers) into words.<k>.json; "merge" folds those into words.json."""
import json, os, sys, glob, subprocess, concurrent.futures as cf
import numpy as np
from faster_whisper import WhisperModel
H = os.path.dirname(os.path.abspath(__file__)); E = os.path.join(H, "cache", "ears"); P = os.path.join(E, "words.json")
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
url = lambda i: (lib.get(i) or {}).get("video") or (clips.get(i) or {}).get("videoUrl")
out = json.load(open(P)) if os.path.exists(P) else {}
if sys.argv[1:] == ["merge"]:
    for f in glob.glob(os.path.join(E, "words.*.json")): out.update(json.load(open(f)))
    json.dump(out, open(P, "w")); print("merged", len(out)); sys.exit()
SH = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else None
if SH:
    P = os.path.join(E, f"words.{SH[0]}.json"); mine = json.load(open(P)) if os.path.exists(P) else {}
    out.update(mine)
A = os.path.join(H, "cache", "aud")
todo = [f[:-5] for f in sorted(os.listdir(A)) if f.endswith(".flac") and f[:-5] not in out]
if SH: todo = todo[SH[0]::SH[1]]; out = mine   # every clip with sound: a transcript for each (the voice filter skips silence)
print(len(todo), "speaking clips to transcribe", flush=True)
m = WhisperModel("base.en", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("WT", 6)))
import soundfile as sf
def pcm(i):
    try:
        a, sr = sf.read(os.path.join(A, i + ".flac"), dtype="float32")
        from scipy.signal import resample_poly; return i, (resample_poly(a, 1, 3).astype(np.float32) if sr == 48000 else a)   # 48 kHz to 16 kHz, filtered
    except Exception: return i, None
if True:
    for n, (i, a) in enumerate(map(pcm, todo), 1):
        if a is None or len(a) < 8000: out[i] = {"text": "", "words": []}; continue
        segs, info = m.transcribe(a, word_timestamps=True, vad_filter=True, beam_size=1, condition_on_previous_text=False)
        ws = [[w.word.strip(), round(w.start, 2), round(w.end, 2), round(w.probability, 2)] for s in segs for w in (s.words or [])]
        text = " ".join(w[0] for w in ws).strip()
        out[i] = {"text": text, "words": ws, "conf": round(float(np.mean([w[3] for w in ws])), 2) if ws else 0}
        if n % 100 == 0: json.dump(out, open(P, "w")); print(n, "of", len(todo), "·", text[:70], flush=True)
json.dump(out, open(P, "w")); print("DONE", len(out), "· with words", sum(1 for v in out.values() if v["text"]))
