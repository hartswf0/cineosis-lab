"""python3 markov/transcribe.py <audio> <out.json> — a recording becomes timed words, in its own process (the lab server calls it).
faster-whisper (small.en, cached locally) gives word timestamps; openai-whisper's word timing crashes here (numba), so it is the fallback without words."""
import json, sys
src, out = sys.argv[1], sys.argv[2]
try:
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(src, word_timestamps=True, vad_filter=True)
    res = [{"t0": round(s.start, 2), "t1": round(s.end, 2), "text": s.text.strip(),
            "words": [{"w": w.word.strip(), "t0": round(w.start, 2), "t1": round(w.end, 2)} for w in (s.words or [])]} for s in segs]
except Exception as e:
    import whisper
    r = whisper.load_model("small.en").transcribe(src, fp16=False)
    res = [{"t0": round(s["start"], 2), "t1": round(s["end"], 2), "text": s["text"].strip(), "words": []} for s in r["segments"]]
json.dump({"segments": res}, open(out, "w"))
