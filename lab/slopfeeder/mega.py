"""After assemble.py: the megafilm's entry (arc, chapters, duration, thumbnail) and each film's versions, into films.json.
usage: python3 slopfeeder/mega.py"""
import json, os, subprocess
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(D, "roughcut")
from assemble import CHAPTERS
J = json.load(open(os.path.join(D, "films.json"))); CB = json.load(open(os.path.join(D, "cutbastard.json")))["songs"]
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
mp = os.path.join(R, "slopfeeder-megafilm.mp4")
if os.path.exists(mp):
    th = os.path.join(D, "films", "mega.jpg"); subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "8", "-i", mp, "-frames:v", "1", "-q:v", "3", th], check=True)
    J["mega"] = {"video": "slopfeeder/roughcut/slopfeeder-megafilm-web.mp4", "thumb": "slopfeeder/films/mega.jpg", "dur": round(dur(mp), 1),
                 "logline": "What has this developer been up to? A developer's long night in eight rites: he makes a crew out of mud, renders for four flat shapes offshore, feeds his crew, drafts them, confesses, purges, lets them go, and washes the memory clean.",
                 "arc": "The meme asks the question; the eight films answer it in order. The crew is made (I) and put to work for the fleet offshore (II); it is fed (III) and, fed, becomes an army (IV); the machine admits what it eats (V), purges itself and comes back (VI); the crew walks off toward free ground (VII); and the developer cleanses the memory (VIII). The last image returns to his face: he is still up.",
                 "chapters": [{"n": n, "roman": r, "title": t, "beat": CB[n]["story"]["logline"]} for n, r, t in CHAPTERS]}
for f in J["films"]:
    n = f["n"]; name = next(t for k, r, t in CHAPTERS if k == n)
    solo = os.path.join(R, f"slopfeeder-{n}-{name.lower().replace(' ', '-')}.mp4"); v = [{"label": f"colour ({f['numbers']['look']})", "video": f["video"]}]
    if os.path.exists(solo): v.insert(0, {"label": "plain colour, with the cold open", "video": f"slopfeeder/roughcut/{os.path.basename(solo)}"})
    f["versions"] = v
json.dump(J, open(os.path.join(D, "films.json"), "w"), ensure_ascii=False, indent=1); print("films.json:", "megafilm" if "mega" in J else "no megafilm yet", "·", sum(len(f["versions"]) for f in J["films"]), "versions")
