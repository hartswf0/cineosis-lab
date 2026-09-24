"""Per-clip work on the downloaded (read) clips: filmstrips, matched frames, audio analysis.

Writes strips/<id>.jpg (8 frames side by side), frames/<id>.jpg (the matched frame, full size),
cache/strips.json and cache/audio.json.
"""
import json, os, subprocess
import numpy as np

LAB = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(LAB, "cache")
N = 8

def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                        "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    dur = float(j.get("format", {}).get("duration", 0) or 0)
    kinds = {s.get("codec_type") for s in j.get("streams", [])}
    return dur, "audio" in kinds

def audio_stats(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    if x.size < 1600:
        return {"has_audio": True, "rms_db": None, "silence": 1.0, "flatness": None, "kind": "silence"}
    fr = 512
    frames = x[: len(x) // fr * fr].reshape(-1, fr)
    rms = np.sqrt((frames ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    silence = float((db < -50).mean())
    loud = frames[db >= -50]
    if len(loud) == 0:
        return {"has_audio": True, "rms_db": round(float(db.mean()), 1), "silence": 1.0, "flatness": None, "kind": "silence"}
    spec = np.abs(np.fft.rfft(loud * np.hanning(fr), axis=1)) + 1e-9
    flat = float(np.median(np.exp(np.log(spec).mean(1)) / spec.mean(1)))
    # syllabic modulation (3–7 Hz) of the loudness envelope suggests speech
    env = rms - rms.mean()
    fs_env = 16000 / fr
    E = np.abs(np.fft.rfft(env)) ** 2
    f = np.fft.rfftfreq(len(env), 1 / fs_env)
    band = E[(f >= 3) & (f <= 7)].sum() / (E[(f > 0.5)].sum() + 1e-9)
    if silence > 0.85:
        kind = "silence"
    elif band > 0.35 and flat > 0.05:
        kind = "speech"
    elif flat < 0.06:
        kind = "music"
    else:
        kind = "sound"
    return {"has_audio": True, "rms_db": round(float(20 * np.log10(np.sqrt((loud ** 2).mean()) + 1e-9)), 1),
            "silence": round(silence, 3), "flatness": round(flat, 3), "speech_band": round(float(band), 3), "kind": kind}

def main():
    corpus = json.load(open(os.path.join(C, "corpus.json")))
    strips, audio = {}, {}
    os.makedirs(os.path.join(LAB, "strips"), exist_ok=True); os.makedirs(os.path.join(LAB, "frames"), exist_ok=True)
    clips = sorted(f[:-4] for f in os.listdir(os.path.join(LAB, "clips")) if f.endswith(".mp4"))
    for k, i in enumerate(clips):
        p = os.path.join(LAB, "clips", i + ".mp4")
        dur, has_a = probe(p)
        if dur <= 0:
            continue
        s = os.path.join(LAB, "strips", i + ".jpg")
        if not os.path.exists(s):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-vf",
                            f"fps={N}/{dur:.3f},scale=240:-2,tile={N}x1", "-frames:v", "1", "-q:v", "4", s])
        if os.path.exists(s):
            strips[i] = {"strip": f"strips/{i}.jpg", "frames": N}
        c = corpus[i]
        off = max(0.0, min(dur - 0.05, (c.get("matchTimestampSeconds") or c["startSeconds"]) - c["startSeconds"]))
        fpath = os.path.join(LAB, "frames", i + ".jpg")
        if not os.path.exists(fpath):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{off:.3f}", "-i", p, "-frames:v", "1", "-q:v", "2", fpath])
        audio[i] = audio_stats(p) if has_a else {"has_audio": False, "kind": "none"}
        if k % 25 == 0:
            print(f"{k + 1}/{len(clips)}", flush=True)
    json.dump(strips, open(os.path.join(C, "strips.json"), "w"))
    json.dump(audio, open(os.path.join(C, "audio.json"), "w"))
    from collections import Counter
    print("DONE", len(strips), "strips;", Counter(a["kind"] for a in audio.values()), flush=True)

if __name__ == "__main__":
    main()
