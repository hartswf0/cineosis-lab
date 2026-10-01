"""Every studio voice recording of the Odyssey, heard word by word (faster-whisper small.en, word timestamps), so the subtitles can be
placed on the words as spoken rather than estimated. Resumable. Writes cache/voice-words/<scene>.json.
usage: ../.venv/bin/python voice_words.py [path to odyssey-halfworld]"""
import json, os, sys, glob
from faster_whisper import WhisperModel
H = os.path.dirname(os.path.abspath(__file__)); HW = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads/odyssey-halfworld")
O = os.path.join(H, "cache", "voice-words"); os.makedirs(O, exist_ok=True)
m = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=6)
files = sorted(glob.glob(os.path.join(HW, "drive", "voice", "OD-*.m4a")))
for n, f in enumerate(files, 1):
    out = os.path.join(O, os.path.basename(f)[:-4] + ".json")
    if os.path.exists(out): continue
    segs, _ = m.transcribe(f, word_timestamps=True, vad_filter=False, beam_size=1)
    words = [{"w": w.word.strip(), "t0": round(w.start, 2), "t1": round(w.end, 2)} for s in segs for w in (s.words or [])]
    json.dump(words, open(out, "w")); print(n, len(files), os.path.basename(f), len(words), flush=True)
print("DONE")
