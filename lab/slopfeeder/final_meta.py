"""The final cut's entry in films.json (the release page's hero).   usage: python3 slopfeeder/final_meta.py"""
import json, os, subprocess
D = os.path.dirname(os.path.abspath(__file__)); J = json.load(open(os.path.join(D, "films.json"))); F = json.load(open(os.path.join(D, "final.json")))
mp = os.path.join(D, "roughcut", "slopfeeder-final-web.mp4"); dur = float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", mp], capture_output=True, text=True).stdout or 0)
shots = sum(len(a["shots"]) for a in F); ai = sum(1 for a in F for s in a["shots"] if s["type"] == "ai")
J["final"] = {"video": "slopfeeder/roughcut/slopfeeder-final-web.mp4", "thumb": "slopfeeder/films/final.jpg", "dur": round(dur, 1),
  "logline": "What has this developer been up to? In nine minutes and eight rites, a skull-masked cook makes a crew out of mud, feeds it, drafts it, confesses what his machine eats, purges it, and lets it walk free; and he is still up.",
  "arc": f"One film, cut as one: each act is the strongest stretch of its song, and the acts run in the order of the story, with hard cuts on the downbeat from song to song. {shots} shots, {ai} of them the pickups that carry the cook, the crew, the four and the pails; the archive only where it answers. No shot, and no source clip used twice in the same act. It opens on the meme it came from and ends on the developer.",
  "chapters": [{"roman": a["act"], "title": a["title"], "beat": a["beat"]} for a in F]}
json.dump(J, open(os.path.join(D, "films.json"), "w"), ensure_ascii=False, indent=1); print("final:", round(dur), "s ·", shots, "shots ·", ai, "AI")
