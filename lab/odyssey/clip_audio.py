"""What each clip in the cuts sounds like, so the radio cut can decide when to let the archive be heard.
For every clip a cut uses (and its first alternatives): does it have sound, how loud (integrated loudness, EBU R128), how much
of it is silence, and how much of its energy sits in the voice band (300-3400 Hz) against the whole: a rough talk-vs-ambience cue.
Streams each clip through ffmpeg (nothing is kept); resumable. Writes cache/audio.json {id: {...}}.   usage: python3 clip_audio.py"""
import json, os, re, subprocess, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, "cache", "audio.json")
out = json.load(open(P)) if os.path.exists(P) else {}
cuts = json.load(open(os.path.join(H, "cuts.json")))["cuts"]
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
main = {s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"]}
want = []
for v in cuts.values():
    for x in v["shots"]:
        for i in ([x["clip"]] if x["clip"] else []) + x["alts"][:3]:
            if i not in out and i not in want: want.append(i)
def url(i): s = lib.get(i) or main.get(i); return s and s.get("video")
def measure(i):
    u = url(i)
    if not u or not u.startswith("http"): return i, None
    try:
        p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name", "-of", "csv=p=0", u], capture_output=True, text=True, timeout=60)
        if not p.stdout.strip(): return i, {"audio": False}
        a = subprocess.run(["ffmpeg", "-nostats", "-i", u, "-vn", "-filter_complex",
                            "[0:a]asplit=3[a][b][c];[a]ebur128=peak=none[o1];[b]silencedetect=n=-45dB:d=0.4[o2];[c]highpass=f=300,lowpass=f=3400,volumedetect[o3]",
                            "-map", "[o1]", "-f", "null", "-map", "[o2]", "-f", "null", "-map", "[o3]", "-f", "null", "-"], capture_output=True, text=True, timeout=120).stderr
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", a); sil = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", a))
        d = re.search(r"Duration: (\d+):(\d+):([\d.]+)", a); dur = (int(d[1]) * 3600 + int(d[2]) * 60 + float(d[3])) if d else 0
        band = re.findall(r"mean_volume: (-?[\d.]+) dB", a)
        return i, {"audio": True, "lufs": float(I[-1]) if I else None, "silent": round(sil / dur, 2) if dur else None, "band_db": float(band[-1]) if band else None}
    except Exception as e: return i, None
print(len(want), "clips to hear", flush=True)
with cf.ThreadPoolExecutor(8) as ex:
    for n, (i, r) in enumerate(ex.map(measure, want), 1):
        if r is not None: out[i] = r
        if n % 100 == 0: json.dump(out, open(P, "w")); print(n, flush=True)
json.dump(out, open(P, "w"))
v = [x for x in out.values() if x.get("audio")]
print("heard", len(out), "· with sound", len(v), "· loud enough (> -35 LUFS)", sum(1 for x in v if (x.get("lufs") or -99) > -35))
