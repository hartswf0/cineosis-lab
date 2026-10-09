"""THE SLOPFEEDER, assembled. A cold open (the meme quoted with its own captions; the stare full frame; a voice asks 'With A.I... what has this
developer been up to?'; the title on black), standalone raw versions of the eight films with it, and the MEGAFILM: the cold open once, the
eight in the chapters' order (I-VIII) behind short black chapter cards, and an ending that returns to the developer.
usage: python3 slopfeeder/assemble.py            (needs the raw-v2 renders in roughcut/)"""
import json, os, subprocess, glob
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); T = os.path.join(D, "src", "assemble"); os.makedirs(T, exist_ok=True); OUT = os.path.join(D, "roughcut")
W, H = 1280, 720; ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "24"]; AENC = ["-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
BOLD, IMPACT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf"
AI = lambda n: os.path.join(D, "ai", "src", n + ".mp4")
CHAPTERS = [("26", "I", "THE BUCKET BET"), ("14", "II", "THE RENDER FLEET"), ("13", "III", "THE COMMUNION"), ("23", "IV", "THE CHORUS"),
            ("20", "V", "THE MAINFRAME CONFESSION"), ("09", "VI", "THE RECURSION"), ("06", "VII", "GO HOME AND BE FREE"), ("07", "VIII", "CLEANSE THE MEMORY")]
SONG = {s["n"]: s["title"] for s in json.load(open(os.path.join(D, "songs.json")))["songs"]}
def run(a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
def card(path, lines):   # text on black or transparent: (text, font, size, y, colour, spacing)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0 if path.endswith("-t.png") else 255)); d = ImageDraw.Draw(im)
    for text, font, size, y, col, sp in lines:
        if any("\u1200" <= ch <= "\u139f" for ch in text): font = "/System/Library/Fonts/Supplemental/Kefa.ttc"   # Ethiopic: Arial has no glyphs for the Amharic title
        f = ImageFont.truetype(font, size); x = W / 2 - (sum(d.textlength(ch, font=f) for ch in text) + sp * (len(text) - 1)) / 2
        for ch in text:
            d.text((x, y), ch, font=f, fill=col, stroke_width=3 if path.endswith("-t.png") else 0, stroke_fill=(0, 0, 0, 255)); x += d.textlength(ch, font=f) + sp
    im.save(path)
# ---- the voice
vo = os.path.join(T, "vo.wav")
if not os.path.exists(vo):
    subprocess.run(f'echo "With A.I. ... what has this developer been up to?" | "{L}/.venv/bin/piper" --model "{L}/models/piper/en_US-ryan-high.onnx" --output_file "{T}/vo-raw.wav"', shell=True, check=True, capture_output=True)
    run(["-i", os.path.join(T, "vo-raw.wav"), "-af", "asetrate=22050*0.9,aresample=48000,volume=1.6", "-ac", "2", vo])
def coldopen(key, title):
    """12.6 s: 0-5.7 the meme quoted (captions as the meme had them); 5.7-9.6 the stare full frame, the voice; 9.6-12.6 the title"""
    out = os.path.join(T, f"cold-{key}.mp4")
    caps = [os.path.join(T, f"cap{k}-t.png") for k in range(3)]
    for k, mid in enumerate(["The Developer:", "The designer:", "The Developer:"]):
        card(caps[k], [("Creative login screen design", BOLD, 22, 8, (255, 255, 255, 255), 0), (mid, BOLD, 30, 352, (255, 255, 255, 255), 0)])
    tl = os.path.join(T, f"title-{key}.png"); card(tl, [("THE SLOPFEEDER", IMPACT, 96, 270, (235, 229, 216, 255), 6), (title, BOLD, 26, 400, (133, 139, 147, 255), 8)])
    cell = "scale=405:330:force_original_aspect_ratio=increase,crop=405:330,setsar=1,fps=24"
    fc = (f"[0:v]{cell},trim=0:5.7,setpts=PTS-STARTPTS[t];[1:v]{cell},split[d1][d2];[d1]trim=0:1.78,setpts=PTS-STARTPTS[a];[d2]trim=1.78:3.31,setpts=PTS-STARTPTS[c];"
          f"[2:v]{cell},trim=0:2.39,setpts=PTS-STARTPTS[b];[a][b][c]concat=n=3:v=1[bot];[t]pad=405:360:0:30:black[t2];[t2][bot]vstack,pad=405:720:0:0:black,pad={W}:{H}:(ow-iw)/2:0:black,format=rgba[m0];"
          f"[m0][5:v]overlay=0:0:enable='lt(t,1.78)'[m1];[m1][6:v]overlay=0:0:enable='between(t,1.78,4.17)'[m2];[m2][7:v]overlay=0:0:enable='gte(t,4.17)',trim=0:5.7,setpts=PTS-STARTPTS[meme];"
          f"[3:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=24,trim=0:3.9,setpts=PTS-STARTPTS[stare];"
          f"[4:v]trim=0:3,setpts=PTS-STARTPTS,format=rgba[ttl];[meme][stare][ttl]concat=n=3:v=1,format=yuv420p[v];"
          f"[3:a]atrim=0:3.9,asetpts=PTS-STARTPTS,volume=0.35,adelay=5700|5700[sa];[8:a]adelay=6100|6100[va];anullsrc=r=48000:cl=stereo,atrim=0:12.6[sil];[sil][sa][va]amix=inputs=3:duration=first,volume=3[a]")
    run(["-ss", "1", "-t", "6", "-i", AI("Cursor_clicking_massive_login_in"), "-ss", "5", "-t", "4", "-i", AI("Soldier_in_mask_staring_deadpan"), "-ss", "0.5", "-t", "2.5", "-i", AI("Recruit_staring_at_autonomous_drill"),
         "-ss", "1", "-t", "4", "-i", AI("Soldier_in_mask_staring_deadpan"), "-loop", "1", "-t", "3", "-i", tl, "-loop", "1", "-t", "6", "-i", caps[0], "-loop", "1", "-t", "6", "-i", caps[1], "-loop", "1", "-t", "6", "-i", caps[2],
         "-i", vo, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", "12.6", *ENC, *AENC, out])
    return out
def chapter_card(n, roman, name):
    p = os.path.join(T, f"ch-{n}.png"); card(p, [(roman, IMPACT, 120, 220, (242, 90, 23, 255), 4), (name, BOLD, 34, 380, (235, 229, 216, 255), 8), (SONG.get(n, ""), BOLD, 20, 440, (133, 139, 147, 255), 2)])
    out = os.path.join(T, f"ch-{n}.mp4"); run(["-loop", "1", "-t", "3.2", "-i", p, "-f", "lavfi", "-t", "3.2", "-i", "anullsrc=r=48000:cl=stereo", "-vf", "fade=t=in:st=0:d=0.4,fade=t=out:st=2.8:d=0.4,format=yuv420p", *ENC, *AENC, "-shortest", out]); return out
def norm(src, out):   # every piece to one stream shape so they join without drift
    run(["-i", src, "-vf", f"scale={W}:{H},setsar=1,fps=24,format=yuv420p", *ENC, *AENC, out]); return out
def join(parts, out):
    lst = out + ".txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in parts)); run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out])
if __name__ == "__main__":
    films = {}
    for n, roman, name in CHAPTERS:
        src = os.path.join(OUT, f"blacktop-{n}-cutbastard-raw-v2.mp4")
        if not os.path.exists(src): print("missing", src); continue
        fn = os.path.join(T, f"film-{n}.mp4"); films[n] = fn if os.path.exists(fn) and os.path.getmtime(fn) > os.path.getmtime(src) else norm(src, fn)
        solo = os.path.join(OUT, f"slopfeeder-{n}-{name.lower().replace(' ', '-')}.mp4")
        join([norm(coldopen(n, f"{roman} · {name}"), os.path.join(T, f"coldn-{n}.mp4")), films[n]], solo); print("standalone", os.path.basename(solo), flush=True)
    if len(films) == len(CHAPTERS):
        parts = [norm(coldopen("mega", "EIGHT RITES"), os.path.join(T, "coldn-mega.mp4"))]
        for n, roman, name in CHAPTERS: parts += [chapter_card(n, roman, name), films[n]]
        end = os.path.join(T, "end.png"); card(end, [("THE DEVELOPER", IMPACT, 64, 250, (235, 229, 216, 255), 6), ("is still up.", BOLD, 30, 350, (133, 139, 147, 255), 4),
            ("songs: The Liturgy of the Two Buttons · archive: public-domain films from the Moving Image Archive · made in the Cineosis Lab", BOLD, 15, 640, (90, 95, 100, 255), 1)])
        ec = os.path.join(T, "end.mp4"); run(["-ss", "1", "-t", "4", "-i", AI("Soldier_in_mask_staring_deadpan"), "-loop", "1", "-t", "6", "-i", end, "-f", "lavfi", "-t", "10", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=24,trim=0:4,setpts=PTS-STARTPTS,fade=t=out:st=3.4:d=0.6[s];[1:v]fps=24,format=yuv420p,fade=t=in:st=0:d=0.6[e];[s][e]concat=n=2:v=1,format=yuv420p[v]",
            "-map", "[v]", "-map", "2:a", "-t", "10", *ENC, *AENC, ec]); parts.append(ec)
        join(parts, os.path.join(OUT, "slopfeeder-megafilm.mp4")); print("megafilm written", flush=True)
