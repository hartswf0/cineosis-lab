"""THE CHICKEN OF TOMORROW, IN SEVEN STEPS: a recut of one 1948 sponsored film (Chicken of Tomorrow, Bay State Film Productions,
narrated by Lowell Thomas), reordered and shortened. Every spoken word is the film's own narration, cut by Whisper word times; the
step cards are added. Every source window was checked against frame sheets of the clip before it was used.
Writes wes/chicken-of-tomorrow-in-seven-steps.mp4 and wes/chicken-cut.json (the edit list, with source in/out).
usage: python3 wes/chicken_cut.py"""
import json, os, subprocess, urllib.request
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(D, "chicken"); T = os.path.join(D, "film-cache"); W_, H_, FPS = 960, 720, 24
clip = lambda k: next(os.path.join(C, f) for f in os.listdir(C) if f.startswith(k) and f.endswith(".mp4"))
FT = os.path.join(T, "Jost.ttf")
if not os.path.exists(FT): urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/jost/Jost%5Bwght%5D.ttf", FT)
# (kind, asset, video in, video out, audio in, audio out or None for near silence, card text, job in the cut)
EDIT = [
  ("card", None, 0, 3.0, None, None, ("A PROCEDURE IN SEVEN STEPS", "THE CHICKEN OF TOMORROW"), "orients: names the procedure the film will follow"),
  ("shot", "21037f09", 0.0, 3.2, 0.0, 3.2, None, "the subject and the promise: a chick, 'into a new world'"),
  ("card", None, 0, 1.3, None, None, ("STEP ONE", "ARRIVE"), "a repeated duration begins the procedure"),
  ("shot", "074c0867", 0.0, 6.8, 0.0, 6.8, None, "eggs arrive by air, rail and private car: the seriousness of the undertaking"),
  ("card", None, 0, 1.3, None, None, ("STEP TWO", "BE COUNTED"), "the procedure repeats"),
  ("shot", "354b897b", 9.6, 13.5, 15.5, 19.4, None, "two men in white coats band chicks; '16,000 birds in record time': each bird becomes a number"),
  ("shot", "2b899969", 0.4, 2.8, 0.0, 2.4, None, "judges in suits praise the chicks: judging is set up, to be answered at step six"),
  ("card", None, 0, 1.3, None, None, ("STEP THREE", "EAT"), "the procedure repeats"),
  ("shot", "86c8f287", 8.3, 11.6, 8.3, 11.6, None, "'no lapse in the attention given to the birds' over a record sheet: attention means bookkeeping"),
  ("card", None, 0, 1.3, None, None, ("STEP FOUR", "BE WEIGHED"), "the procedure repeats"),
  ("shot", "22ba0988", 0.0, 6.7, 0.0, 6.7, None, "the coops weighed: live weight becomes pounds of feed per pound of gain"),
  ("shot", "c6c26518", 5.0, 7.4, 5.0, None, None, "a boy watches over the coop, silent: a pending response, held"),
  ("card", None, 0, 1.4, None, None, ("STEP FIVE", "GET DRESSED"), "the procedure repeats, in the industry's own euphemism"),
  ("shot", "78f6be4d", 8.4, 10.8, 8.4, None, None, "the answer, without a word: the carcasses on the line (the exception that ends what the birds can do)"),
  ("shot", "5b9b1059", 0.0, 3.6, 0.0, 3.6, None, "'prepared ready to cook and subjected to government inspection', to an inspector's straight face"),
  ("card", None, 0, 1.3, None, None, ("STEP SIX", "BE JUDGED"), "the procedure repeats"),
  ("shot", "30a76cab", 0.0, 6.0, 0.0, 6.0, None, "the return of the judges, now in white coats, among carcasses: the same judging, its object changed"),
  ("shot", "0266b8b5", 0.0, 3.4, 0.0, 3.4, None, "'a box of dressed poultry representing each entry': the entrants, as exhibits"),
  ("card", None, 0, 1.3, None, None, ("STEP SEVEN", "CELEBRATE"), "the last step"),
  ("shot", "77eb8d54", 2.4, 7.6, 7.0, 12.2, None, "the Chicken Queen in her gown (a second meaning of 'dressed'); 'And who wouldn't?'"),
  ("shot", "77eb8d54", 15.4, 20.4, 12.8, 17.8, None, "the prize, and who holds it: two men, a live hen, a certificate, 'a double reason to celebrate'"),
  ("shot", "e31e12f6", 1.0, 4.2, 1.0, None, None, "the question, silent: a chicken-shaped map with a question mark"),
  ("shot", "b997da4c", 0.4, 6.9, 0.4, 6.9, None, "the answer, spoken: 'Make mine chicken. Chicken of tomorrow, that is.'"),
  ("shot", "b997da4c", 11.8, 14.2, 11.8, None, None, "THE END (the original film's own card)"),
  ("shot", "21037f09", 3.5, 6.8, 3.5, None, None, "the return: the same chick, after the end; 'a new world' now means step one"),
]
def card(png, small, big):
    im = Image.new("RGB", (W_, H_), (24, 20, 18)); d = ImageDraw.Draw(im); ink = (236, 226, 208)
    fs = ImageFont.truetype(FT, 24); fs.set_variation_by_axes([400]); fb = ImageFont.truetype(FT, 74); fb.set_variation_by_axes([500])
    t = " ".join(small); w = d.textlength(t, font=fs); d.text(((W_ - w) / 2, H_ / 2 - 74), t, font=fs, fill=(200, 184, 150))
    sz = 74
    while d.textlength(big, font=fb) > W_ - 140 and sz > 30: sz -= 4; fb = ImageFont.truetype(FT, sz); fb.set_variation_by_axes([500])   # fit the frame
    w = d.textlength(big, font=fb); d.text(((W_ - w) / 2, H_ / 2 - 30), big, font=fb, fill=ink); im.save(png)
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
VF = f"scale={W_}:{H_}:force_original_aspect_ratio=decrease,pad={W_}:{H_}:(ow-iw)/2:(oh-ih)/2,normalize=blackpt=black:whitept=white:smoothing=48:independence=0.4,setsar=1,fps={FPS},format=yuv420p"
parts, table, t = [], [], 0.0
for n, (kind, a, v0, v1, a0, a1, txt, job) in enumerate(EDIT):
    out = os.path.join(T, f"ck_{n:02d}.mp4"); dur = v1 - v0
    if kind == "card":
        png = os.path.join(T, f"ck_{n:02d}.png"); card(png, *txt)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-loop", "1", "-t", f"{dur}", "-i", png, "-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=stereo",
                        "-vf", f"setsar=1,fps={FPS},format=yuv420p", *ENC, "-shortest", out], check=True)
    else:
        src = clip(a)
        if a1 is None:   # a held silence: the clip's own room, 45 dB down: no words, but no dead air
            af = f"volume=-45dB,afade=t=in:d=0.08,afade=t=out:st={dur - 0.1:.2f}:d=0.1"; alen = dur
        else:            # the narration, from its own words; laid under this picture (sometimes the picture of the next moment)
            alen = a1 - a0; af = f"apad,afade=t=in:d=0.04,afade=t=out:st={min(alen, dur) - 0.08:.2f}:d=0.08"
        # picture and sound are separate inputs, each sought to its own place and held to the piece's length, so they cannot drift
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-ss", f"{v0}", "-t", f"{dur}", "-i", src, "-ss", f"{a0}", "-t", f"{min(alen, dur)}", "-i", src,
                        "-filter_complex", f"[0:v]setpts=PTS-STARTPTS,{VF}[v];[1:a]asetpts=PTS-STARTPTS,{af},atrim=0:{dur},aformat=sample_rates=48000:channel_layouts=stereo[a]",
                        "-map", "[v]", "-map", "[a]", "-t", f"{dur}", *ENC, out], check=True)
    parts.append(out)
    table.append({"pos": n + 1, "at": round(t, 1), "dur": round(dur, 1), "asset": a or "added card", "video_src": None if kind == "card" else [v0, v1],
                  "audio_src": None if kind == "card" else ([a0, a1] if a1 is not None else "room, -26 dB"), "card": " · ".join(txt) if txt else None, "job": job})
    t += dur
lst = os.path.join(T, "ck_list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
out = os.path.join(D, "chicken-of-tomorrow-in-seven-steps.mp4")
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-af", "loudnorm=I=-17:TP=-1.5", "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-maxrate", "1600k", "-bufsize", "3200k", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
json.dump({"title": "The Chicken of Tomorrow, in Seven Steps", "source": "Chicken of Tomorrow (1948), Bay State Film Productions, narrated by Lowell Thomas", "seconds": round(t, 1), "edit": table},
          open(os.path.join(D, "chicken-cut.json"), "w"), indent=1)
print(f"wrote {out} · {t:.1f} s · {len(EDIT)} pieces · {os.path.getsize(out) / 1e6:.1f} MB")
