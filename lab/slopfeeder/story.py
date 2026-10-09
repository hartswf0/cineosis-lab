"""THE SLOPFEEDER — the story cut (v3). A written screenplay of named pickup shots, cut on the bars of the songs and held for one or two bars;
the pickups' own lines kept whole as captions (their generated voices are not used: the songs and the archive's own sound carry the film).
Between the rites: an archive bridge in its own sound, then a screen of Claude making the film (the code, the grids it picked from, the
poison sheet, the transcript check, the failed cut): the fourth wall, because the film's question is what the developer has been up to.
The poison is the remedy: the shots the poison reading left out are placed at the turns.
Writes roughcut/slopfeeder-story.mp4 (+ -web; local: the cold open is the real meme) and story.json (the EDL slopfeeder-takes.html plays).
usage: .venv/bin/python slopfeeder/story.py"""
import json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); T = os.path.join(D, "src", "story"); os.makedirs(T, exist_ok=True); OUT = os.path.join(D, "roughcut")
import assemble as AS
W, H, FPS = 1280, 720, 24; ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "24"]; AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS"); S = {s["n"]: s for s in json.load(open(os.path.join(D, "songs.json")))["songs"]}
WORDS = json.load(open(os.path.join(D, "ai", "words.json"))); SCENES = json.load(open(os.path.join(T, "scenes.json")))
SAY, TWIN = "say", "twin"
BRIDGES = ["B digging", "B kitchen", "B cheer", "B computers", "B reel", "B recede", "B dusk"]   # after acts I..VII: the archive breathes between rites, in its own sound
BARB = {"06": 12}   # tracked beats per bar (06's tracker reads triple time)
SCRIPT = [
 ("14", "I", "THE REQUEST", 0.0, "the login page lands on the beach", [
   ("Glowing_screen_towers_over_coast", 0.3, 4.2, {}),
   ("Cursor_clicking_massive_login_in", 2.0, 3.0, {}),
   ("Four_flat_shapes_on_beach", 2.2, 3.4, {SAY: 1}),
   ("Cartoon_shapes_loom_over_sea", 3.0, 3.0, {TWIN: (2.6, "I fleet")}),
   ("Developer_watching_boat_at_beach", 1.0, 3.6, {}),
   ("Green_CRT_terminal_displaying_text", 2.0, 3.6, {"sub": "could the onions look happier?"}),
   ("Masked_cook_watching_monitor", 1.0, 3.0, {}),
   ("Cook_typing_text_at_monitor", 3.0, 3.0, {}),
   ("CRT_screen_displaying_repeating", 4.1, 4.6, {"poison": 1}),
   ("Slopfeeder_raises_spatula_on_bat", 4.55, 3.0, {SAY: 1})]),
 ("26", "II", "THE BUCKET BET", 57.0, "he makes a crew out of mud", [
   ("Workers_slam_buckets_into_sand", 0.0, 2.6, {SAY: 1}),
   ("Miniature_bucket_emerges_from_sand", 2.0, 3.0, {}),
   ("Drill_raises_pail_from_sand", 2.0, 3.0, {}),
   ("Clay_figures_stand_before_fire", 2.2, 3.0, {"poison": 1}),
   ("Clay_figures_stand_before_fire", 6.0, 2.8, {"poison": 1, TWIN: (2.6, "II clay")}),
   ("Worker_carrying_bucket_near_surf", 2.0, 3.2, {"poison": 1}),
   ("Crew_pumping_pails_on_beach", 0.0, 5.2, {SAY: 1}),
   ("Workers_pump_drills_on_beach", 6.3, 3.0, {TWIN: (2.6, "II drill")}),
   ("Titans_watch_multiplying_beach_b", 0.5, 3.4, {}),
   ("Workers_drilling_on_tidal_flat", 4.0, 3.0, {})]),
 ("13", "III", "THE COMMUNION", 12.4, "he feeds them", [
   ("Masked_cook_flipping_burgers", 1.0, 3.2, {}),
   ("Cook_passing_burgers_through_bunker", 0.0, 4.9, {SAY: 1}),
   ("Crew_passing_burgers_up_wall", 2.0, 3.0, {"poison": 1}),
   ("Cook_feeding_recruit_burger", 1.8, 4.8, {SAY: 1, TWIN: (2.6, "III mess")}),
   ("Crew_serving_food_at_wall", 0.0, 4.7, {SAY: 1}),
   ("Adults_participating_in_ration_c", 2.8, 2.5, {SAY: 1}),
   ("Recruit_biting_iron_plate", 1.55, 3.3, {SAY: 1, "poison": 1, TWIN: (2.6, "III iron")}),
   ("Figure_in_mask_eating_burger", 0.0, 2.3, {SAY: 1})]),
 ("23", "IV", "THE CHANGES", 12.2, "the requests become a war", [
   ("Figures_in_robes_chanting_on", 2.55, 6.2, {SAY: 1}),
   ("Cook_feeding_crew_near_brick", 4.8, 2.0, {SAY: 1}),
   ("Glowing_screen_towers_over_coast", 7.4, 2.6, {"poison": 1}),
   ("Slopfeeders_chanting_in_mud_surf", 0.0, 6.2, {SAY: 1}),
   ("Workers_charging_from_landing_craft", 1.8, 3.0, {TWIN: (2.4, "IV land")}),
   ("Workers_sprinting_onto_tidal_mud", 3.5, 2.0, {}),
   ("Cook_grilling_meat_on_battlefield", 0.8, 5.7, {SAY: 1}),
   ("Workers_crossing_trench_with_engine", 5.6, 2.6, {SAY: 1, TWIN: (2.4, "IV march")}),
   ("Hooded_figures_walking_through_fire", 7.2, 2.6, {"poison": 1})]),
 ("20", "V", "THE CONFESSION", 147.0, "the machine admits what it eats", [
   ("Masked_critics_and_cook_chanting", 0.0, 7.2, {SAY: 1}),
   ("Cook_standing_before_mainframe_s", 2.0, 3.2, {}),
   ("Cook_at_terminal_on_beach", 2.5, 2.5, {SAY: 1}),
   ("Operators_turning_in_control_room", 4.0, 3.0, {}),
   ("Cook_at_terminal_on_beach", 6.0, 2.8, {SAY: 1}),
   ("Giant_cursor_dragging_across_sky", 0.0, 9.4, {SAY: 1})]),
 ("09", "VI", "THE RECURSION", 68.0, "it loops, it purges, it begins again", [
   ("Recruit_collapses_drawing_circles", 0.5, 3.0, {}),
   ("Recruit_collapses_drawing_circles", 4.5, 1.9, {}),
   ("Four_flat_shapes_by_sea", 6.6, 3.4, {SAY: 1, "poison": 1, "sub": "3-2-1-4-3-2-3-2-2-2-2-2-2-2-2-2-2-2"}),
   ("Four_shapes_rise_from_sea", 4.6, 3.0, {SAY: 1, "poison": 1, "sub": "mm-hmm, mm-hmm, mm-hmm, mm-hmm"}),
   ("World_swaying_in_surreal_unison", 1.0, 3.0, {"poison": 1}),
   (None, 0, 2.2, {"black": 1}),
   ("Cook_turns_off_bunker_monitors", 1.0, 3.6, {}),
   ("Tide_rising_around_orange_pails", 0.0, 3.3, {SAY: 1, TWIN: (2.6, "VI flood")}),
   ("Fog_over_flooded_mudflat_with", 2.0, 3.0, {})]),
 ("06", "VII", "GO HOME AND BE FREE", 77.0, "the crew walks off into the sea", [
   ("Creators_marching_into_saltwater", 0.0, 3.0, {SAY: 1}),
   ("Workers_dismantling_fortress_wal", 3.2, 3.6, {TWIN: (3.0, "VII gates")}),
   ("Creators_marching_into_saltwater", 5.6, 2.3, {SAY: 1}),
   ("Crew_walking_up_sandy_beach", 2.0, 3.6, {TWIN: (3.0, "VII road")}),
   ("Woman_watching_fortress_wall", 0.5, 3.4, {TWIN: (3.0, "VII sea")}),
   ("Workers_resting_between_shifts", 3.0, 3.0, {})]),
 ("07", "VIII", "CLEANSE THE MEMORY", 100.0, "the tide takes it, and he is still at the screen", [
   ("Ocean_tide_washes_away_circles", 0.0, 4.2, {TWIN: (3.0, "VIII waves")}),
   ("Onion_ring_floats_in_tide", 2.0, 3.6, {}),
   ("Archive_degradation_and_memory_c", 1.0, 3.8, {"poison": 1}),
   ("Crew_sleeping_among_orange_pails", 1.0, 3.6, {TWIN: (3.0, "VIII fade")}),
   ("Cook_cleaning_griddle_on_beach", 2.0, 4.0, {}),
   ("Person_exhaling_mist_dissolving", 1.0, 3.2, {}),
   ("Cook_staring_at_computer_screen", 3.0, 4.6, {})]),
]
def run(a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
probe = lambda p: float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout or 0)
FILL = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
MUSICAL = {"electronic synth music", "orchestral music", "drums", "a choir singing", "a crowd chanting"}
ARCH = json.load(open(os.path.join(D, "story-archive.json"))); CACHE = os.path.join(D, "fclips")
def png(path, draw):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw(ImageDraw.Draw(im)); im.save(path); return path
def subtitle(path, text):   # the spoken line, small, low: the story told in its own words
    f = ImageFont.truetype(AS.BOLD, 30); lines, cur = [], ""
    for w_ in text.split():
        if ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength((cur + " " + w_).strip(), font=f) > 1040: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_).strip()
    lines.append(cur)
    def dr(d):
        for k, ln in enumerate(lines):
            d.text((W / 2 - d.textlength(ln, font=f) / 2, H - 74 - 40 * (len(lines) - 1 - k)), ln, font=f, fill=(250, 246, 236, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
    return png(path, dr)
def header(path, roman, title):
    f1, f2 = ImageFont.truetype(AS.IMPACT, 46), ImageFont.truetype(AS.BOLD, 22)
    def dr(d):
        d.rectangle([40, 40, 46, 112], fill=(242, 90, 23, 255)); d.text((60, 36), roman, font=f1, fill=(242, 90, 23, 255), stroke_width=2, stroke_fill=(0, 0, 0, 200))
        d.text((60, 90), title, font=f2, fill=(235, 229, 216, 255), stroke_width=2, stroke_fill=(0, 0, 0, 200))
    return png(path, dr)
def fetch(key):   # a hand-picked archive shot (story-archive.json), cached by id
    r = ARCH[key]; p = os.path.join(CACHE, r["id"] + ".mp4")
    if not os.path.exists(p) or os.path.getsize(p) < 5000: subprocess.run(["curl", "-sfL", "-A", "cineosis-44-research", "-o", p, r["v"]])
    return p, r
def window(key, p, dur):   # where in the clip to play: the stretch that looks most like the still picked by eye (its thumbnail), never a title card
    import numpy as np, io, urllib.request
    L_ = probe(p); r = ARCH[key]
    if L_ <= dur + .1: return 0.0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "fps=4,scale=48:27,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, 27, 48).astype(np.float32)
    try:
        u = r["v"].replace("/clips/", "/thumbnails/").replace(".mp4", ".jpg")
        th = np.asarray(Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "cineosis-44-research"}), timeout=20).read())).convert("L").resize((48, 27)), np.float32)
    except Exception: th = F[len(F) // 2]
    z = lambda x: (x - x.mean()) / (x.std() + 1e-6); tz = z(th)
    sim = np.array([float((z(f) * tz).mean()) for f in F])
    dark = np.array([(f < 45).mean() for f in F]); title = (dark > .6) & (np.array([(f > 170).mean() for f in F]) > .02)   # light text on a dark card
    sc = sim - 2.0 * title - .8 * (dark > .9); n = max(1, int(dur * 4)); best, bt = -9, 0
    for i in range(0, max(1, len(F) - n)):
        v = sc[i:i + n].mean()
        if v > best: best, bt = v, i
    return min(bt / 4, L_ - dur - .05)
def hasaudio(p): return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
def piece(out, inp, vf, dur, ov=()):
    fc = f"[0:v]{vf},trim=0:{dur:.3f},setpts=PTS-STARTPTS[v0]"; last = "[v0]"; ins = []
    for j, (pp, s0, s1) in enumerate(ov):
        ins += ["-loop", "1", "-t", f"{dur:.3f}", "-i", pp]; fc += f";[{j + 1}:v]format=rgba[o{j}];{last}[o{j}]overlay=0:0:enable='between(t,{s0:.2f},{s1:.2f})'[v{j + 1}]"; last = f"[v{j + 1}]"
    run([*inp, *ins, "-filter_complex", fc + f";{last}format=yuv420p[vo]", "-map", "[vo]", "-t", f"{dur:.3f}", *ENC, "-an", out]); return out
def fitvf(L_, a, dur):   # play from a; if the source runs out, slow it (to .55x at most) and hold its last frame rather than cut away early
    R = max(.55, (L_ - a) / dur) if L_ - a < dur else 1.0
    return (f"setpts=PTS/{R:.3f}," if R < 1 else "") + FILL + f",tpad=stop_mode=clone:stop_duration={dur:.2f}", R
# ---- the cold open: the meme itself, then the stare, the voice, the title (the first song rises under the title)
PUBLIC = bool(os.environ.get("PUBLIC"))   # the published version: the meme rebuilt from our own pickups (no real person, no game footage)
TAG = "-public" if PUBLIC else ""
def coldopen():
    if PUBLIC: return AS.norm(AS.coldopen("story", "WHAT HAS THIS DEVELOPER BEEN UP TO?"), os.path.join(T, "cold-public.mp4")), 12.6
    out = os.path.join(T, "cold.mp4"); src = os.path.join(D, "src"); vo = os.path.join(D, "src", "assemble", "vo.wav")
    fb, fs = ImageFont.truetype(AS.IMPACT, 104), ImageFont.truetype(AS.BOLD, 26)
    tl = png(os.path.join(T, "title.png"), lambda d: [d.text((W / 2 - d.textlength("THE SLOPFEEDER", font=fb) / 2, 262), "THE SLOPFEEDER", font=fb, fill=(235, 229, 216, 255)),
                                                      d.text((W / 2 - d.textlength("what has this developer been up to?", font=fs) / 2, 400), "what has this developer been up to?", font=fs, fill=(150, 156, 164, 255))])
    fc = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:2,eq=brightness=-0.32,setsar=1[bg];[b]scale=-2:{H},setsar=1[fg];"
          f"[bg][fg]overlay=(W-w)/2:0,fps={FPS},trim=0:8.45,setpts=PTS-STARTPTS,format=yuv420p[m];"
          f"[1:v]crop=1080:608:0:470,scale={W}:{H},setsar=1,fps={FPS},trim=0:4.6,setpts=PTS-STARTPTS,zoompan=z='min(1+on*0.0016,1.18)':d=1:s={W}x{H}:fps={FPS},fade=t=out:st=4.1:d=0.5,format=yuv420p[g];"
          f"[2:v]fps={FPS},format=rgba,fade=t=in:st=0:d=0.5:alpha=1,format=yuv420p[t];[m][g][t]concat=n=3:v=1[v];"
          f"[0:a]atrim=0:8.45,asetpts=PTS-STARTPTS,aresample=48000,afade=t=out:st=8.0:d=0.45[ma];[1:a]atrim=0:4.6,asetpts=PTS-STARTPTS,aresample=48000,volume=0.3,afade=t=out:st=4.0:d=0.6[ga];"
          f"[3:a]aresample=48000,adelay=600|600,apad=whole_dur=4.6[va];[ga][va]amix=inputs=2:duration=first,volume=2[gv];anullsrc=r=48000:cl=stereo,atrim=0:3.4[sil];[ma][gv][sil]concat=n=3:v=0:a=1[aa]")
    run(["-i", os.path.join(src, "devdes.mp4"), "-i", os.path.join(src, "ghost.mp4"), "-loop", "1", "-t", "3.4", "-i", tl, "-i", vo, "-filter_complex", fc, "-map", "[v]", "-map", "[aa]", *ENC, *AENC, out])
    return out, 16.45
# ---- Claude's screens: what the developer has been up to (each one sits on the next song's first bars, before its act lands)
BTS = os.path.join(T, "bts")
SCREENS = [
 ("> what has this developer been up to?\n\nI'm the developer. I'm Claude.\nI cut this film out of 109 generated clips,\n36,858 archive shots and eight songs.\n\nThis is me making it.", None, []),
 ("# 109 clips came back from the generator.\n# they already speak:\n#\n#   'Turn over the bucket,\n#    its mouth with mud.'\n#\n# the story is in their own lines.", "all0.jpg", [(5, 1), (6, 1), (2, 6), (1, 5)], 200, 125, 0),
 ("# my poison filter threw these out:\n# morphing, plush, glitching.\n#\n# clay men out of fire.\n# a screen that wants more.\n#\n# the poison is the remedy.\n# they go at the turns.", "poison.jpg", [(0, 0), (1, 2), (0, 5), (3, 3), (1, 0), (3, 0)], 240, 150, 0),
 ('SCRIPT += ("23", "IV", "THE CHANGES", [\n  ("Figures_in_robes_chanting_on",\n      2.55, 6.2, {SAY: 1}),\n  ("Cook_feeding_crew_near_brick",\n      4.8, 2.0, {SAY: 1}),\n  ("Glowing_screen_towers_over_coast",\n      7.4, 2.6, {"poison": 1}),\n  ...', None, []),
 ("# the machine ranks the archive.\n# I look, and pick one memory\n# per act by eye.", "q1.jpg", [(0, 4), (1, 2), (2, 5), (3, 1), (4, 6), (5, 3), (6, 6), (7, 4)], 200, 126, 150),
 ("$ whisper slopfeeder-story.mp4\n\n 191.0  Behold the tragic comedy\n        of the software war.\n 194.0  It passed in the demo,\n        but fails in the mud.\n 211.0  Accept the ash.\n 213.0  Process the silt.\n 215.0  Commit the change.\n 219.0  System error.", None, []),
 ("# the last cut: nine minutes,\n# 149 shots, chosen by score.\n#\n# you said: I can't follow the arc.\n#\n# so I stopped ranking\n# and wrote it.", "final-sheet.jpg", [], 0, 0, 0),
 ("# many takes are the same shot,\n# generated twice.\n#\n# you choose which one to watch:\n#   slopfeeder-takes.html", "all1.jpg", [(0, 1), (0, 2), (0, 3), (0, 4)], 200, 125, 0),
]
MONO = "/System/Library/Fonts/Menlo.ttc"
def screen(i, dur):
    spec = SCREENS[i]; text, img = spec[0], spec[1]; boxes = spec[2]; out = os.path.join(T, f"screen-{i}.mp4")
    fm, ft = ImageFont.truetype(MONO, 26), ImageFont.truetype(MONO, 15)
    pic = Image.open(os.path.join(BTS, img)).convert("RGB") if img else None
    if pic:
        cw, ch, ox = spec[3], spec[4], spec[5]; bw, bh = 660, 600; sc = min(bw / pic.width, bh / pic.height)
    n = int(round(dur * FPS)); chars = len(text); cps = max(38, chars / 3.6)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", *ENC, "-an", out], stdin=subprocess.PIPE)
    for f in range(n):
        t = f / FPS; im = Image.new("RGB", (W, H), (12, 13, 15)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 34], fill=(22, 24, 27)); [d.ellipse([16 + 20 * k, 11, 28 + 20 * k, 23], fill=c) for k, c in enumerate([(70, 74, 80)] * 3)]
        d.text((W / 2 - d.textlength("claude · ~/cineosis-lab/slopfeeder", font=ft) / 2, 9), "claude · ~/cineosis-lab/slopfeeder", font=ft, fill=(133, 139, 147))
        if pic:
            z = 1 + .05 * t / dur; pw, ph = int(pic.width * sc * z), int(pic.height * sc * z); px, py = 600 + (660 - pw) // 2, 60 + (620 - ph) // 2
            im.paste(pic.resize((pw, ph)), (px, py))
            for k, (r, c) in enumerate(boxes):
                if t > 1.0 + .45 * k:
                    x0, y0 = px + (ox + c * cw) * sc * z, py + r * ch * sc * z; d.rectangle([x0, y0, x0 + cw * sc * z, y0 + (ch - 14 if ch > 120 else ch) * sc * z], outline=(242, 90, 23), width=3)
        shown = text[:int(max(0, t - .25) * cps)]; y = 74; xw = 52
        for ln in shown.split("\n"):
            col = (133, 139, 147) if ln.startswith("#") else (242, 90, 23) if ln[:1] in "$>" else (235, 229, 216)
            d.text((xw, y), ln, font=fm, fill=col); y += 38
        if (f // 12) % 2 == 0:
            last = shown.split("\n")[-1]; cx = xw + d.textlength(last, font=fm); d.rectangle([cx + 2, y - 36, cx + 16, y - 8], fill=(235, 229, 216))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    # the room and the keys: a quiet tone and a click for each character typed
    sr = 48000; N = int(dur * sr); rng = np.random.default_rng(i); a = rng.normal(0, .0025, N)
    for k, ch_ in enumerate(text):
        if ch_ in " \n": continue
        t0 = int((.25 + k / cps) * sr)
        if t0 >= N - 600: break
        burst = rng.normal(0, 1, 420) * np.exp(-np.arange(420) / 60) * rng.uniform(.04, .09); burst = np.diff(burst, prepend=0)
        a[t0:t0 + 420] += burst
    import wave
    wv = os.path.join(T, f"screen-{i}.wav"); w = wave.open(wv, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    return out
# ---- an act: the song's bars are the clock; each shot holds one or two bars inside one real shot of its clip
def bars_of(n, start):
    bb = BARB.get(n, 4); bt = S[n]["beats"]; i0 = min(range(len(bt)), key=lambda i: abs(bt[i] - start)); return [b for b in bt[i0::bb]]
def place(clip, a, dur):   # where to play: inside the real shot (scene cut) that holds a; slow (>= .6x) rather than run across a cut
    L_ = probe(os.path.join(D, "ai", "src", clip + ".mp4")); cuts = [0.0] + [c for c in SCENES.get(clip, []) if .3 < c < L_ - .3] + [L_]
    s0, s1 = next(((x, y) for x, y in zip(cuts, cuts[1:]) if x <= a + .05 < y), (0.0, L_))
    if s1 - s0 >= dur: return max(s0, min(a, s1 - dur - .04)), 1.0
    if s1 - s0 >= dur * .6: return s0, (s1 - s0 - .04) / dur
    return max(0.0, min(a, L_ - dur - .05)), 1.0
def act(n, roman, title, start, beat, shots, edl, at0):
    bars = bars_of(n, start); start = bars[0]; bar = float(np.median(np.diff(bars[:16])))
    seq = []
    for clip, a, d, o in shots:
        seq.append(("ai", clip, a, d, o))
        if o.get(TWIN): seq.append(("twin", o[TWIN][1], 0, o[TWIN][0], {}))
    parts, amb, t, bi = [], [], 0.0, 0
    for k, (kind, clip, a, d, o) in enumerate(seq):
        nb = max(1, int(round(max(d, 3.3 if kind == "ai" else 2.6) / bar))); bi2 = min(bi + nb, len(bars) - 1); dur = bars[bi2] - bars[bi]; t0 = bars[bi] - start; bi = bi2
        out = os.path.join(T, f"{roman}-{k:02d}.mp4"); ov = [(header(os.path.join(T, f"hdr-{roman}.png"), roman, title), 0.2, 3.2)] if k == 0 else []
        if o.get("black"): parts.append(piece(out, ["-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}"], "setsar=1", dur)); continue
        if kind == "twin":
            p, r = fetch(clip); L_ = probe(p); ss = max(0.0, window(clip, p, dur)); vf, R = fitvf(L_, ss, dur)
            parts.append(piece(out, ["-ss", f"{ss:.2f}", "-i", p], vf, dur)); print(f"   {roman} memory: {r['title'][:50]} ({r.get('year')})", flush=True)
            if hasaudio(p): amb.append((p, ss, min(dur, L_ - ss), t0, .5))
            edl.append({"t": round(at0 + t0, 3), "d": round(dur, 3), "kind": "archive", "title": r["title"], "year": r.get("year"), "v": r["v"], "ss": round(ss, 2)}); continue
        ss, R = place(clip, a, dur); src = os.path.join(D, "ai", "src", clip + ".mp4")
        vf = (f"setpts=PTS/{R:.3f}," if R < 1 else "") + FILL + f",tpad=stop_mode=clone:stop_duration={dur:.2f}"
        cap = o.get("sub") or " ".join(w["text"] for w in WORDS.get(clip, []) if ss - .4 <= w["t0"] < ss + dur * R and w["nsp"] < .3) if o.get(SAY) else o.get("sub", "")
        if cap: ov.append((subtitle(os.path.join(T, f"sub-{roman}-{k}.png"), cap if len(cap) <= 110 else cap[:108].rsplit(" ", 1)[0] + "…"), .25, dur - .15))
        parts.append(piece(out, ["-ss", f"{ss:.2f}", "-i", src], vf, dur, ov))
        edl.append({"t": round(at0 + t0, 3), "d": round(dur, 3), "kind": "ai", "clip": clip, "ss": round(ss, 2), "rate": round(R, 3), "cap": cap, "act": roman, "poison": bool(o.get("poison"))})
    total = bars[bi] - start; lst = os.path.join(T, f"{roman}.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts)); vid = os.path.join(T, f"{roman}-v.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])
    print(f"{roman:>4} {title:22s} {total:5.1f}s  {len(seq)} shots · bar {bar:.2f}s", flush=True)
    return {"roman": roman, "n": n, "start": start, "vid": vid, "dur": total, "amb": amb, "bar": bar}
def bridge(key, i, dur=5.6):
    p, r = fetch(key); L_ = probe(p); ss = max(0.0, window(key, p, dur)); vf, R = fitvf(L_, ss, dur)
    v = piece(os.path.join(T, f"bridge-{i}.mp4"), ["-ss", f"{ss:.2f}", "-i", p], vf, dur); print(f"   bridge {i}: {r['title'][:50]} ({r.get('year')})", flush=True)
    return {"vid": v, "dur": dur, "src": p if hasaudio(p) else None, "ss": ss, "len": min(dur, L_ - ss), "r": r}
def ending():
    end = os.path.join(T, "end.png"); AS.card(end, [("THE DEVELOPER", AS.IMPACT, 64, 250, (235, 229, 216, 255), 6), ("is still up.", AS.BOLD, 30, 350, (133, 139, 147, 255), 4),
        ("songs: The Liturgy of the Two Buttons · archive: public-domain films from the Moving Image Archive · cut by Claude in the Cineosis Lab", AS.BOLD, 15, 640, (90, 95, 100, 255), 1)])
    ec = os.path.join(T, f"end{TAG}.mp4")
    stare = ["-ss", "1", "-i", AS.AI("Soldier_in_mask_staring_deadpan")] if PUBLIC else ["-ss", "5", "-i", os.path.join(D, "src", "ghost.mp4")]; crop = "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d" % (W, H, W, H) if PUBLIC else "crop=1080:608:0:470,scale=%d:%d" % (W, H)
    run([*stare, "-loop", "1", "-t", "6", "-i", end, "-f", "lavfi", "-t", "10", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
         f"[0:v]{crop},setsar=1,fps={FPS},trim=0:4,setpts=PTS-STARTPTS,fade=t=out:st=3.3:d=0.7[s];[1:v]fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.6[e];[s][e]concat=n=2:v=1,format=yuv420p[v];"
         f"[0:a]atrim=0:4,asetpts=PTS-STARTPTS,aresample=48000,volume=0.3,afade=t=out:st=3.3:d=0.7[ga];[2:a][ga]amix=inputs=2:duration=first,volume=2[a]", "-map", "[v]", "-map", "[a]", "-t", "10", *ENC, *AENC, ec])
    return ec, 10.0
# ---- one program: [cold] then for each rite: Claude's screen on the song's first bars → the act on the downbeat → the archive bridge in its own
#      sound while the song rings out (L-cut). Songs never stop dead; no generated voices.
if __name__ == "__main__":
    cold, cdur = coldopen(); vids, at, songs, other, edl, prog = [cold], cdur, [], [(cold, 0, cdur, 0.0, 1.0, "raw")], [], []
    TAIL = 4.5
    for i, x in enumerate(SCRIPT):
        n = x[0]; bars = bars_of(n, x[3]); bar = float(np.median(np.diff(bars[:16]))); LEAD = 3.4 if i == 0 else 0.0; nsb = max(1, int(np.ceil((5.6 + LEAD) / bar)))
        i0 = bars.index(min(bars, key=lambda b: abs(b - x[3]))); pre_i = max(0, i0 - nsb)
        if i0 - pre_i < nsb: bars_full = bars; i0 = min(len(bars) - 1, pre_i + nsb)   # a song that starts at 0: its first bars go under the screen
        sstart = bars[pre_i]; astart = bars[i0]; sd = astart - sstart - LEAD   # the first song already rising under the title
        sv = screen(i, sd); vids.append(sv); prog.append({"t": round(at, 2), "d": round(sd, 2), "kind": "screen", "i": i})
        A_ = act(n, x[1], x[2], astart, x[4], x[5], edl, at + sd)
        songs.append((os.path.join(ALB, S[n]["file"]), sstart, LEAD + sd + A_["dur"] + TAIL, at - LEAD, 1.2 if sstart > 0 else 2.0, TAIL)); other.append((os.path.join(T, f"screen-{i}.wav"), 0, sd, at, 1.0, "fade"))
        for (p, ss, du, t0, g) in A_["amb"]: other.append((p, ss, du, at + sd + t0, g, "fade"))
        vids.append(A_["vid"]); prog.append({"t": round(at + sd, 2), "d": round(A_["dur"], 2), "kind": "act", "roman": x[1], "title": x[2]}); at += sd + A_["dur"]
        if i < len(BRIDGES):
            b = bridge(BRIDGES[i], i + 1); vids.append(b["vid"]); prog.append({"t": round(at, 2), "d": b["dur"], "kind": "bridge", "title": b["r"]["title"]})
            if b["src"]: other.append((b["src"], b["ss"], b["len"], at, 1.1, "fade"))
            at += b["dur"]
    ec, edur = ending(); vids.append(ec); other.append((ec, 0, edur, at, 1.0, "raw")); total = at + edur
    lst = os.path.join(T, "program.txt"); open(lst, "w").write("".join(f"file '{AS.norm(v, v[:-4] + '-n.mp4')}'\n" for v in vids)); pv = os.path.join(T, "program-v.mp4")
    run(["-f", "concat", "-safe", "0", "-i", lst, "-map", "0:v", "-c", "copy", pv])
    ins, fc, lab = [], "", []
    for j, (p, ss, du, at_, fi, fo) in enumerate(songs):
        ins += ["-ss", f"{ss:.3f}", "-t", f"{du:.3f}", "-i", p]; ms = int(at_ * 1000)
        fc += f"[{j}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d={fi:.2f},afade=t=out:st={du - fo:.3f}:d={fo:.2f},volume=0.92,adelay={ms}|{ms},apad=whole_dur={total:.3f}[s{j}];"; lab.append(f"[s{j}]")
    for j, (p, ss, du, at_, g, mode) in enumerate(other):
        k = len(songs) + j; ins += ["-ss", f"{ss:.3f}", "-t", f"{du:.3f}", "-i", p]; ms = int(at_ * 1000)
        fades = f"afade=t=in:d=0.5,afade=t=out:st={max(0, du - .7):.3f}:d=0.7," if mode == "fade" else ""
        fc += f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,{fades}volume={g},adelay={ms}|{ms},apad=whole_dur={total:.3f}[o{j}];"; lab.append(f"[o{j}]")
    fc += f"{''.join(lab)}amix=inputs={len(lab)}:duration=longest,volume={len(lab)},atrim=0:{total:.3f},alimiter=limit=0.95[a]"
    pa = os.path.join(T, "program-a.wav"); run([*ins, "-filter_complex", fc, "-map", "[a]", "-ac", "2", pa])
    master = os.path.join(OUT, f"slopfeeder-story{TAG}.mp4"); run(["-i", pv, "-i", pa, "-map", "0:v", "-map", "1:a", "-c:v", "copy", *AENC, "-shortest", "-movflags", "+faststart", master])
    run(["-i", master, "-c:v", "libx264", "-preset", "slow", "-b:v", "1600k", "-maxrate", "2200k", "-bufsize", "4400k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(OUT, f"slopfeeder-story{TAG}-web.mp4")])
    json.dump({"dur": round(total, 2), "video": f"slopfeeder/roughcut/slopfeeder-story{TAG}-web.mp4", "program": prog, "shots": edl}, open(os.path.join(D, "story.json"), "w"), indent=0)
    print("story:", master, round(probe(master), 1), "s", flush=True)
