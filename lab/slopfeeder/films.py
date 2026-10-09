"""THE EIGHT FILMS, released: for each CUTBASTARD render, a thumbnail chosen by CLIP (past the meme opening: the frame closest to the film's
story spine and logline, weighted toward the characters' colours, away from dark and blurred frames), and a logline, a description and
how it was made, with the real numbers from its cut list and render log. Writes films.json and films/<n>.jpg (1280x720) + <n>-s.jpg.
usage: .venv/bin/python slopfeeder/films.py"""
import glob, json, os, re, subprocess
import numpy as np, cv2, torch, open_clip
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); OUT = os.path.join(D, "films"); os.makedirs(OUT, exist_ok=True)
CB = json.load(open(os.path.join(D, "cutbastard.json")))["songs"]
DESC = {
 "26": "Opening the Slopfeeder cycle on an Amharic throat chant, a skull-masked cook drives a crew of mud through fire and iron. The song's commands (protect your breath from the law, erase the record, tear down the wall) are cut against archive labour and AI pickups of upturned orange pails pounded into the sand on the beat. Three times the song asks who will cross, take the land, receive the fire; three times the answer is the whole army, and the picture widens each time. It ends quietly, on the cooled iron and the tide.",
 "06": "A freedom chant built on the 'Oh, Freedom!' refrain. The film keeps its distance from spectacle: hands, water, earth and morning carry the refusal ('before I'd be a slave'), archive crowds and a film about Frederick Douglass answer the chorus, and the crew who carried the load wades the muddy water toward free ground. What breaks is iron, never a body; the hammer drops and they stand.",
 "07": "An Icelandic rite of memory. The archive is cast as remembrance itself (old film of sea, forge and crowd) and the pickups do the washing: the tide over circles in the sand, an outcast company breaking the gate. Mostly drone, the film holds its shots long; cleansing here is not erasing.",
 "09": "In an invented liturgy a crew recites what made it (coal gave bone, slop gave weight, the iron hand guards the small), purges itself into four beats of black, and comes back as the whole crew. The last phase calls back the first, changed: the recursion of the title.",
 "13": "The shortest rite: a meal on the beach. The cook serves, the crew eats, a held breath before the serving, the swallow at the end. Close on hands and mouths, in newsreel black and white with the pails' orange kept.",
 "14": "The same rite under a new title. Offshore, four flat shapes stand in the sea like warships and request changes; on the sand the crew renders them. Mostly wordless, the film cuts by frame and colour so that workers and machines rhyme: producer and product at once.",
 "20": "Eat the slop, drill baby drill, feed the fire: a dark-comic work song from a kitchen on a battlefield. The cook's griddle, drill rigs locked to the beat, archival oil fields. 'Who stops the rig?' 'Nobody.' In the word-free stretch the pickups' own voices confess what keeps the machine running, and the film ends on what it costs.",
 "23": "Ancient Greek for a new rite. The chorus of the title is both a dancing company and an army: born of mire, it passes in, through and out of the fire, tears the woven mesh, brings down the wall, and answers as one."}
m, _, prep = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
def ct(ts):
    with torch.no_grad(): e = m.encode_text(tok(ts)).float(); return (e / e.norm(dim=-1, keepdim=True)).numpy()
GOOD = ct(["a striking cinematic film still with a strong composition"])[0]; BAD = ct(["a blurry dark underexposed frame", "a black screen"]).mean(0)
films = []
for n, sp in CB.items():
    cands = sorted(glob.glob(os.path.join(D, "roughcut", f"blacktop-{n}-cutbastard-*.mp4")), key=os.path.getmtime)
    if not cands: print(n, "no render yet"); continue
    mp4 = cands[-1]; dur = float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout or 0)
    r = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", "6", "-i", mp4, "-vf", "fps=1,scale=320:180", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(r, np.uint8).reshape(-1, 180, 320, 3)
    with torch.no_grad(): F = m.encode_image(torch.stack([prep(Image.fromarray(x)) for x in fr])).float()
    F = (F / F.norm(dim=-1, keepdim=True)).numpy(); st = sp["story"]; T = ct([st["spine"], st["logline"]]).mean(0); T /= np.linalg.norm(T)
    hsv = [cv2.cvtColor(x, cv2.COLOR_RGB2HSV) for x in fr]
    colour = np.array([(((h[..., 0] < 12) | (h[..., 0] > 172)) & (h[..., 1] > 140) & (h[..., 2] > 120)).mean() + (((h[..., 0] > 120) & (h[..., 0] < 148)) & (h[..., 1] > 110)).mean() for h in hsv])
    sharp = np.array([cv2.Laplacian(cv2.cvtColor(x, cv2.COLOR_RGB2GRAY), cv2.CV_32F).var() for x in fr]); lum = fr.mean((1, 2, 3)) / 255
    contrast = fr.reshape(len(fr), -1).std(1) / 255
    score = F @ T + .5 * (F @ GOOD) - .5 * (F @ BAD) + .6 * np.minimum(colour, .15) + .05 * np.log1p(sharp) - .4 * (lum < .12) + .6 * np.minimum(contrast, .25) - .3 * (sharp < 80)   # a thumbnail must hold at small size: contrast and focus
    k = int(np.argmax(score)); at = 6 + k
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", mp4, "-frames:v", "1", "-q:v", "3", os.path.join(OUT, f"{n}.jpg")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", mp4, "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", os.path.join(OUT, f"{n}-s.jpg")], check=True)
    # the numbers, from the cut list and the render log
    cl = next((json.load(open(f)) for f in sorted(glob.glob(os.path.join(L, "edits", "*blacktop.json")), key=os.path.getmtime, reverse=True)
               if (lambda e: e.get("song") == n and e.get("recipe", {}).get("bet") == "CUTBASTARD")(json.load(open(f)))), {})
    S = cl.get("slots", []); log = "".join(open(f).read() for f in glob.glob(os.path.join(D, "cb2-*.log")) if f"{len(S)} shots" in open(f).read() and f"-{n}-" in open(f).read())
    fol = re.search(r"foley stem: (\d+) thuds on locked pounds, (\d+) archive", log)
    srcs = {s["plate"]["id"] for s in S if s["plate"]["type"] == "archive"}
    nums = {"shots": len(S), "ai": sum(s["plate"]["type"] == "ai" for s in S), "archive": len(srcs), "black": sum(s["plate"]["type"] == "black" for s in S),
            "locked": sum(s.get("locked") or 0 for s in S), "patches": len(sp["patches"]), "generate": sum(1 for p in sp["patches"] if p.get("generate")),
            "thuds": int(fol.group(1)) if fol else None, "heard": int(fol.group(2)) if fol else None, "look": sp["look"], "dur": round(dur, 1), "thumb_at": at}
    how = (f"Made with Blacktop in the Cineosis Lab. The song was read first (Whisper for its words, CLAP for where it has none, librosa for its {len(S) and 'beats'}); "
           f"CUTBASTARD carved its lyric into phases and {nums['patches']} patches of 6-12 s, each with the shots it asks for, ranked by CLIP from public-domain films in the Moving Image Archive "
           f"and the Slopfeeder's AI pickups. {nums['shots']} shots: {nums['ai']} AI pickups and {nums['shots'] - nums['ai'] - nums['black']} archive shots from {nums['archive']} films"
           + (f", {nums['black']} of black" if nums["black"] else "") + f"; {nums['locked']} pounds locked to the beat"
           + (f", {nums['thuds']} foley thuds placed on beats and {nums['heard']} archive shots heard as the world" if nums["thuds"] is not None else "")
           + f". A story spine ({st['spine']}) opens every phase and closes the film. One look across it all: {nums['look']}. It opens on the meme it came from, quoted in its own footage. "
           f"{nums['generate']} patches are still waiting for AI shots to be generated.")
    films.append({"n": n, "song": sp["title"], "title": st["title"], "logline": st["logline"], "story": {k: st[k] for k in ("want", "turn", "end")}, "description": DESC[n], "how": how,
                  "video": f"slopfeeder/roughcut/{os.path.basename(mp4)}", "thumb": f"slopfeeder/films/{n}.jpg", "thumb_s": f"slopfeeder/films/{n}-s.jpg", "numbers": nums})
    print(n, st["title"], f"thumb at {at}s", nums, flush=True)
json.dump({"films": films}, open(os.path.join(D, "films.json"), "w"), ensure_ascii=False, indent=1)
