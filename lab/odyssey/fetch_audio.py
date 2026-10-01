"""Fetch each clip's own sound once, to a local file the listening and transcribing stages read (no model in this process: Python
threads plus a loaded model deadlocked). First 30 s, 48 kHz mono FLAC; clips with no audio stream are marked. Resumable.
The archive's server rate-limits parallel streams, so four at a time.   usage: python3 fetch_audio.py [all]"""
import glob, json, os, subprocess, sys, time, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(H, "cache", "aud"); os.makedirs(A, exist_ok=True)
lib = {s["id"]: s for s in json.load(open(os.path.join(H, "all", "library.json")))["shots"]}
lib.update({s["id"]: s for s in json.load(open(os.path.join(os.path.dirname(H), "markov", "library.json")))["shots"] if s.get("kind") != "poet"})
clips = {c["id"]: c for c in json.load(open(os.path.join(H, "results", "clips.json")))}
url = lambda i: (lib.get(i) or {}).get("video") or (clips.get(i) or {}).get("videoUrl")
want = []
for f in sorted(glob.glob(os.path.join(H, "sea", "b*.json"))):
    for s in json.load(open(f))["scenes"]:
        for sh in s["shots"]: want += [sh["id"]] + [c["id"] for c in sh.get("sea", [])]
for v in json.load(open(os.path.join(H, "sea", "index.json")))["cast"].values(): want += [c["id"] for c in v]
if "all" in sys.argv: want += json.load(open(os.path.join(H, "cache", "ids.json")))
want = [i for i in dict.fromkeys(want) if url(i)]
done = lambda i: os.path.exists(os.path.join(A, i + ".flac")) or os.path.exists(os.path.join(A, i + ".none"))
todo = [i for i in want if not done(i)]
print(len(want), "wanted ·", len(todo), "to fetch", flush=True)
def get(i):
    out = os.path.join(A, i + ".flac")
    try:
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-rw_timeout", "20000000", "-i", url(i), "-t", "30", "-vn", "-ac", "1", "-ar", "48000", "-c:a", "flac", "-y", out + ".tmp.flac"],
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=120)
        if os.path.exists(out + ".tmp.flac") and os.path.getsize(out + ".tmp.flac") > 2000: os.replace(out + ".tmp.flac", out); return "ok"
        if os.path.exists(out + ".tmp.flac"): os.remove(out + ".tmp.flac")
        if b"does not contain any stream" in r.stderr or b"Output file #0 does not contain" in r.stderr or b"matches no streams" in r.stderr: open(os.path.join(A, i + ".none"), "w").close(); return "none"
        open(os.path.join(A, i + ".none"), "w").close(); return "none"
    except Exception as e: return "fail"
t0 = time.time(); c = {"ok": 0, "none": 0, "fail": 0}
with cf.ThreadPoolExecutor(4) as ex:
    for n, r in enumerate(ex.map(get, todo), 1):
        c[r] += 1
        if n % 100 == 0: print(n, "of", len(todo), c, f"{n / (time.time() - t0):.2f}/s", flush=True)
print("DONE", c, flush=True)
