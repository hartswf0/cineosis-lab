"""The poem spoken by a Piper voice, phrase by phrase, so the film knows exactly when each phrase is said.

    python markov/speak.py job.json            one job: {"phrases":[...], "gaps":[...], "voice":"en_US-ryan-high", "out":"markov/voice/x", "at":[t0...]?}
    python markov/speak.py --batch jobs.json   many jobs (the prerender for the published site)

gaps[i] is the silence after phrase i (a line end is longer than a comma, a stanza longer than a line).
With "at", each phrase is placed at that time instead (aligned to a recorded reading, for mixing with it).
Writes <out>.mp3 and <out>.json {"voice", "times": [[t0, t1], ...], "duration"}. Runs in its own process (onnxruntime)."""
import json, os, subprocess, sys
import numpy as np
from piper import PiperVoice
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
VOICES = {}
def voice(name):
    if name not in VOICES: VOICES[name] = PiperVoice.load(os.path.join(LAB, "models", "piper", name + ".onnx"))
    return VOICES[name]
def say(v, text):
    a = [c.audio_float_array for c in v.synthesize(text)]
    return np.concatenate(a) if a else np.zeros(1, np.float32)
def render(job):
    v = voice(job.get("voice", "en_US-ryan-high")); sr = v.config.sample_rate
    clips = [say(v, p) for p in job["phrases"]]
    times, t = [], .6
    if job.get("at"):
        end = max(a + len(c) / sr for a, c in zip(job["at"], clips)) + 1
        buf = np.zeros(int(max(end, job.get("duration", 0)) * sr), np.float32)
        for a, c in zip(job["at"], clips):
            i = int(a * sr); buf[i:i + len(c)] += c[:len(buf) - i]; times.append([round(a, 3), round(a + len(c) / sr, 3)])
    else:
        parts = [np.zeros(int(t * sr), np.float32)]
        for c, g in zip(clips, job.get("gaps") or [.35] * len(clips)):
            times.append([round(t, 3), round(t + len(c) / sr, 3)]); parts += [c, np.zeros(int(g * sr), np.float32)]; t += len(c) / sr + g
        buf = np.concatenate(parts)
    buf = np.clip(buf, -1, 1)
    out = os.path.join(LAB, job["out"]); os.makedirs(os.path.dirname(out), exist_ok=True)
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-c:a", "libmp3lame", "-b:a", "64k", out + ".mp3"], input=buf.astype(np.float32).tobytes())
    if p.returncode: raise RuntimeError("ffmpeg failed")
    meta = {"voice": job.get("voice", "en_US-ryan-high"), "times": times, "duration": round(len(buf) / sr, 3)}
    json.dump(meta, open(out + ".json", "w"))
    return meta
if __name__ == "__main__":
    if sys.argv[1] == "--batch":
        jobs = json.load(open(sys.argv[2]))
        for j in jobs:
            if os.path.exists(os.path.join(LAB, j["out"] + ".json")) and not j.get("force"): continue
            m = render(j); print(j["out"], len(m["times"]), "phrases", m["duration"], "s", flush=True)
    else:
        print(json.dumps(render(json.load(open(sys.argv[1])))))
