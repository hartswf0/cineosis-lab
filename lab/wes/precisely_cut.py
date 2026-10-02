"""PRECISELY SO: the most Andersonian film the archive can make, using nothing but the archive: every shot and every title card is
archival, chosen by the strict judge (wes/judge: four judges, one rubric, 906 candidates, 50 kept) and verified against its own
footage. No text is added and no colour is graded. The story is told by the archive's own intertitles, in their order here:
an invitation, a voyage, a door that will not open without evening clothes, the film stopping itself, that night, and the King.
Title cards are held as freezes of their archival frame (long enough to read); shots play their real motion around the judged
moment. Sound: the archive's own music (CLAP), silent where the film stops itself. Writes wes/precisely-so.mp4, wes/precisely-cut.json."""
import json, os, subprocess
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); J = os.path.join(D, "judge"); T = os.path.join(D, "film-cache"); W_, H_, FPS = 960, 720, 24
judged = {p["n"]: p for p in json.load(open(os.path.join(J, "judged.json")))}; M = {int(k): v for k, v in json.load(open(os.path.join(J, "matches.json"))).items()}
# (judge number, how: card | shot | live (a card that holds by itself), seconds, job)
EDIT = [
  (286, "card", 2.4, "the presentation: 'Mother Goose presents'"),
  (146, "card", 3.0, "the title: PRECISELY SO (A Jam Handy Organization card)"),
  (29, "card", 3.4, "the undertaking: \"You must come to my party and bring a friend\""),
  (589, "shot", 2.8, "the friends: three men in jumpsuits, facing us"),
  (66, "card", 3.6, "the voyage: \"Bill and I sail for Europe aboard the Vulcania, March 21st!\""),
  (528, "shot", 2.6, "a car, dead centre, on the road"),
  (465, "shot", 2.4, "a pastel pavilion, frontal"),
  (657, "shot", 2.4, "a brick facade, steps, flower pots"),
  (407, "shot", 2.4, "an espaliered pear on a pink wall: arrival"),
  (10, "card", 3.2, "the obstruction: \"You can't get in without Evening Clothes.\""),
  (523, "shot", 2.8, "three guards before a symmetrical gate"),
  (506, "shot", 2.4, "the first wrong clothes: a row of bathing caps, facing us"),
  (680, "shot", 2.1, "the second: space helmets, facing us"),
  (891, "shot", 2.6, "a closed door: Division Superintendent"),
  (16, "live", 3.2, "the film stops itself: STOP PROJECTOR — DISCUSS FILM (silence)"),
  (102, "card", 2.2, "\"That night.\""),
  (358, "shot", 2.6, "and yet: a man in swimming trunks, inside, centred in a floral room"),
  (393, "shot", 2.4, "the room, its shelf, its wallpaper"),
  (518, "shot", 2.2, "the oven, open, dead on"),
  (462, "shot", 2.4, "hot cross buns, centred: 'A Lenten Treat'"),
  (321, "card", 2.4, "DRIVE-IN REFRESHMENTS"),
  (7, "card", 3.2, "the arrival announced: \"The King is coming down to meet the Yanks ---\""),
  (472, "shot", 2.6, "a monument, centred on a flat wall"),
  (193, "card", 3.0, "ALL THE KING'S HORSES AND ALL THE KING'S MEN"),
  (840, "shot", 2.8, "the King's men: a row of uniforms, facing us"),
  (512, "shot", 2.8, "the King's horses: the fire station's red trucks"),
  (232, "card", 3.0, "The End · A Jam Handy Picture"),
]
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
VF = f"scale={W_}:{H_}:force_original_aspect_ratio=decrease,pad={W_}:{H_}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS},format=yuv420p"   # no grade
parts, table, t, silent = [], [], 0.0, []
for n, (num, how, dur, job) in enumerate(EDIT):
    m = M[num]; src = os.path.join(J, "clips", m["id"] + ".mp4"); out = os.path.join(T, f"ps_{n:02d}.mp4")
    if how == "card":   # the archival frame itself, held to be read
        png = os.path.join(T, f"ps_{n:02d}.png"); at = m["match"]
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{at:.2f}", "-i", src, "-frames:v", "1", "-update", "1", png], check=True)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-t", f"{dur}", "-i", png, "-vf", VF, *ENC, out], check=True); v0, v1 = at, at
    else:               # real motion around the judged moment (a live card from its first held frame)
        c = m["from"] + .1 if how == "live" else max(0.0, min(m["match"] - dur / 2, m["dur"] - dur - .05))
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{c:.2f}", "-t", f"{dur}", "-i", src, "-an", "-vf", VF, "-t", f"{dur}", *ENC, out], check=True); v0, v1 = round(c, 2), round(c + dur, 2)
        if how == "live": silent.append((t, t + dur))
    parts.append(out); p = judged[num]
    table.append({"pos": n + 1, "at": round(t, 1), "dur": dur, "judge_no": num, "score": p.get("score"), "film": p.get("film"), "year": p.get("year"), "id": m["id"],
                  "source": [v0, v1] if v1 > v0 else f"frame at {v0} s, held", "text": p.get("text") or None, "job": job})
    t += dur
lst = os.path.join(T, "ps_list.txt"); open(lst, "w").write("".join(f"file '{x}'\n" for x in parts))
pic = os.path.join(T, "ps_picture.mp4"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", pic], check=True)
# ---- the score: the archive's own music, chosen by CLAP, silent where the film stops itself
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
import torch
from transformers import ClapModel, ClapProcessor
L = os.path.dirname(D); E = os.path.join(L, "odyssey", "cache", "ears"); eids = json.load(open(os.path.join(E, "ids.json"))); CL = np.load(os.path.join(E, "clap.npy")).astype(np.float32)
kind = json.load(open(os.path.join(E, "kind.json"))); V = json.load(open(os.path.join(L, "aspect", "video.json")))
cm = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); cp = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
Q = ["light comic pizzicato strings and woodwinds", "a jaunty harpsichord melody", "a playful small orchestra march with glockenspiel"]
NEG = ["a man speaking", "a woman speaking", "loud rock music", "noise"]
with torch.no_grad():
    q = cm.get_text_features(**cp(text=Q + NEG, return_tensors="pt", padding=True)); q = (q / q.norm(dim=-1, keepdim=True)).numpy()
mus = [k for k, i in enumerate(eids) if kind.get(i, {}).get("k") == "music" and os.path.exists(os.path.join(L, "odyssey", "cache", "aud", i + ".flac"))]
X = CL[mus]; X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9; S = (X @ q[:len(Q)].T).max(1) - .6 * (X @ q[len(Q):].T).max(1)
music, seen = [], set()
for j in np.argsort(-S):
    i = eids[mus[j]]; folder = V.get(i, [""])[0].split("/clips/")[0]
    if folder in seen: continue
    seen.add(folder); music.append(i)
    if len(music) * 26 > t + 6: break
ins = sum([["-i", os.path.join(L, "odyssey", "cache", "aud", i + ".flac")] for i in music], [])
fc = "".join(f"[{k}:a]atrim=0:27,asetpts=PTS-STARTPTS,loudnorm=I=-20:TP=-2,aformat=sample_rates=48000:channel_layouts=stereo[a{k}];" for k in range(len(music))); ch = "[a0]"   # each piece levelled before they meet
for k in range(1, len(music)): fc += f"{ch}[a{k}]acrossfade=d=2.5:c1=tri:c2=tri[x{k}];"; ch = f"[x{k}]"
mute = "+".join(f"between(t,{a - .15:.2f},{b + .1:.2f})" for a, b in silent) or "0"
fc += f"{ch}atrim=0:{t:.2f},volume='if({mute},0,1)':eval=frame,afade=t=in:d=1.2,afade=t=out:st={t - 2.5:.2f}:d=2.5[m]"
wav = os.path.join(T, "ps_score.wav"); subprocess.run(["ffmpeg", "-v", "quiet", "-y", *ins, "-filter_complex", fc, "-map", "[m]", wav], check=True)
_m = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "loudnorm=I=-18:TP=-1.5:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
_j = json.loads(_m[_m.rindex("{"):_m.rindex("}") + 1])
LN = f"loudnorm=I=-18:TP=-1.5:linear=true:measured_I={_j['input_i']}:measured_TP={_j['input_tp']}:measured_LRA={_j['input_lra']}:measured_thresh={_j['input_thresh']}:offset={_j['target_offset']}"
out = os.path.join(D, "precisely-so.mp4")
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-af", LN, "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-maxrate", "1800k", "-bufsize", "3600k",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
json.dump({"title": "Precisely So", "seconds": round(t, 1), "music": music, "edit": table}, open(os.path.join(D, "precisely-cut.json"), "w"), ensure_ascii=False, indent=1)
print(f"wrote {out} · {t:.1f} s · {len(EDIT)} pieces · music {music} · {os.path.getsize(out) / 1e6:.1f} MB")
