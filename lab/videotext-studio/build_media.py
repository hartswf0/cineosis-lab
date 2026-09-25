"""Which shots Videotext Studio can play from this site itself: the Tempest loops (3 s, 240x180, the shot's
in-point) and the lab's local clips. Everything else plays from the archive's CDN.

    python3 lab/videotext-studio/build_media.py     -> lab/videotext-studio/media.json
"""
import json, os
LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ids = lambda d: sorted(f[:-4] for f in os.listdir(os.path.join(LAB, d)) if f.endswith(".mp4"))
out = {"loops": ids("wygwyl/tempest"), "local": ids("clips")}
json.dump(out, open(os.path.join(LAB, "videotext-studio", "media.json"), "w"), separators=(",", ":"))
print(len(out["loops"]), "loops,", len(out["local"]), "local clips")
