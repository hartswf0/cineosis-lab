"""Forage the Moving Image Archive for the Odyssey: run every query in src/q_*.json against the archive's shot search, one at a
time (it rate-limits: never parallel), and keep every clip it returns. Resumable: results/raw.json holds each query's answer.
Each clip remembers which scene / location / motion and which role (ground, action, figures, sign) asked for it.
usage: python3 forage.py        (writes results/raw.json and results/clips.json)"""
import glob, json, os, sys, time, urllib.request, urllib.error
API = "https://www.movingimagearchive.com/api/search"
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, "results"); os.makedirs(R, exist_ok=True)
RAW = os.path.join(R, "raw.json"); GAP = 1.4
KEEP = ("id", "sourceId", "sourceSlug", "sourceTitle", "sourceYear", "startSeconds", "endSeconds", "durationSeconds", "matchTimestampSeconds", "videoUrl", "thumbnailUrl", "colorMode", "aspectRatio", "score")

def search(q):
    tries = 0
    while True:
        req = urllib.request.Request(API, data=json.dumps({"query": q}).encode(), headers={"content-type": "application/json", "user-agent": "cineosis-44-research"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r: return json.load(r).get("clips", [])
        except urllib.error.HTTPError as e:
            tries += 1
            if e.code == 429 or e.code >= 500:
                w = float(e.headers.get("retry-after") or 0) or min(60, 5 * tries); print(f"  {time.strftime('%X')} {e.code} wait {w}s", flush=True); time.sleep(w); continue
            raise
        except Exception as e:
            tries += 1                                                  # the network went away: wait it out, never give up the run
            print(f"  {time.strftime('%X')} {e} retry", flush=True); time.sleep(min(300, 10 * tries))

def jobs():
    out = []
    for f in sorted(glob.glob(os.path.join(H, "src", "q_*.json"))):
        for key, v in json.load(open(f)).items():
            if isinstance(v, list): v = {"ground" if key.startswith("loc:") else "motion": v}
            elif "beats" in v:                                           # a scene spec: every shot's own searches, role shot:<beat>:<shot>
                v = {f"shot:{bi}:{si}": sh.get("q", []) for bi, b in enumerate(v["beats"]) for si, sh in enumerate(b.get("shots", []))}
            for role, qs in v.items():
                for q in qs: out.append((key, role, q.strip()))
    return out

def collect(raw, J):
    clips = {}
    for key, role, q in J:
        for rank, c in enumerate(raw.get(q, [])):
            x = clips.setdefault(c["id"], {**c, "asks": []})
            x["asks"].append([key, role, q, rank, c.get("score")])
    json.dump(list(clips.values()), open(os.path.join(R, "clips.json"), "w"))
    return clips

def main():
    raw = json.load(open(RAW)) if os.path.exists(RAW) else {}
    J = jobs(); todo = [j for j in J if j[2] not in raw]; qs = list(dict.fromkeys(j[2] for j in todo))
    print(f"{len(J)} asks, {len(qs)} queries to run", flush=True)
    for n, q in enumerate(qs, 1):
        raw[q] = [{k: c.get(k) for k in KEEP} for c in search(q)]
        if n % 10 == 0 or n == len(qs):
            json.dump(raw, open(RAW + ".tmp", "w")); os.replace(RAW + ".tmp", RAW)
            cl = collect(raw, jobs()); print(f"{time.strftime('%X')} [{n}/{len(qs)}] {len(raw[q]):2d}  {q}   · {len(cl)} unique clips", flush=True)
        time.sleep(GAP)
    json.dump(raw, open(RAW, "w")); cl = collect(raw, jobs()); print("DONE", len(cl), "unique clips", flush=True)

if __name__ == "__main__": main()
