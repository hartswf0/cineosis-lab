"""THE SLOPFEEDER — the final cut. CUTBASTARD across the whole film, not song by song: one story in eight acts, each act the strongest stretch
of its song (where that song's part of the story happens), cut from the act's CUTBASTARD patches in ONE pass so that no shot family appears
twice in the film; the pickups carry the story (the cook, the crew, the four, the pails), the archive comes in where a patch asks for memory or
history; a story spine opens each act; pounds locked to the beat; hard cuts on the downbeat from song to song; a small act header over each
act's first shot; the cold open before, the developer after.
usage: python3 slopfeeder/final.py            -> roughcut/slopfeeder-final.mp4 (+ -web), films/final.jpg"""
import json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(D); T = os.path.join(D, "src", "final"); os.makedirs(T, exist_ok=True); OUT = os.path.join(D, "roughcut")
import assemble as AS
ALB = os.path.expanduser("~/moto/THE LITURGY OF THE TWO BUTTONS")
ACTS = [("26", "I", "THE BUCKET BET", 57, 126, "the crew is made out of mud"), ("14", "II", "THE RENDER FLEET", 0, 59.4, "four flat shapes offshore want changes"),
        ("13", "III", "THE COMMUNION", 12.4, 88, "he feeds them"), ("23", "IV", "THE CHORUS", 12.2, 87, "fed, they become an army"),
        ("20", "V", "THE MAINFRAME CONFESSION", 26, 98, "nobody stops the rig"), ("09", "VI", "THE RECURSION", 68, 125, "purge, and come back"),
        ("06", "VII", "GO HOME AND BE FREE", 77, 143, "the crew walks off toward free ground"), ("07", "VIII", "CLEANSE THE MEMORY", 96, 147.4, "the memory washed")]
A = json.load(open(os.path.join(D, "atlas.json"))); C = A["cards"]; byId = {c["id"]: c for c in C}; S = {s["n"]: s for s in json.load(open(os.path.join(D, "songs.json")))["songs"]}
CB = json.load(open(os.path.join(D, "cutbastard.json")))["songs"]; V = json.load(open(os.path.join(D, "voice.json")))
K = np.fromfile(os.path.join(D, "comp-emb.bin"), np.int8).reshape(len(C), -1).astype(np.float32); K /= np.linalg.norm(K, axis=1, keepdims=True) + 1e-9; kix = {c["id"]: i for i, c in enumerate(C)}
MUSICAL = {"electronic synth music", "orchestral music", "drums", "a choir singing", "a crowd chanting"}
WORLD_SND = {"THE LANDING": {"an explosion", "artillery gunfire"}, "THE KITCHEN": {"a sizzling griddle frying meat", "fire crackling"}, "THE DRILL LINE": {"machinery clanking", "footsteps in mud"},
             "THE TIDE": {"ocean surf and waves", "rain", "wind howling"}, "THE SCREEN": {"a computer beep"}, "THE RENDER": {"a laser zap"}, "THE FLEET": {"ocean surf and waves"}, "THE AFTERMATH": {"wind howling", "fire crackling", "rain"}}
FA = {c["id"]: c.get("fa") for c in json.load(open(os.path.join(D, "field.json")))["cards"]}
fam = lambda c: FA.get(c["id"]) or c["id"]   # the field's families (CLIP > .85): near-identical pickups count as one
def lock(c, s0, dur, beats, tempo):   # beat lock, as Blacktop does it: a pound on the slot's first beat
    rate = 1.0; tp = c.get("tempo")
    if tp and tp.get("strength", 0) > .2:
        bl = 60 / tempo; tgt = min([bl * .5, bl, bl * 2], key=lambda x: abs(x - tp["period"])); rate = float(np.clip(tp["period"] / tgt, .6, 1.6))
    best = (c.get("in"), rate, 0); bt = [b for b in beats if s0 <= b < s0 + dur]
    if not c.get("pound") or not bt: return best
    for h in c["pound"]:
        at = h - (bt[0] - s0) * rate
        if at < (c.get("in") or 0) - .05 or at + dur * rate > (c.get("out") or at + dur) + 1.5: continue
        n = sum(1 for h2 in c["pound"] if s0 <= s0 + (h2 - at) / rate < s0 + dur and any(abs(b - (s0 + (h2 - at) / rate)) < .09 for b in bt))
        if n > best[2]: best = (at, rate, n)
    return best
src = lambda c: ("ai:" + c["clip"]) if c["type"] == "ai" else ("ar:" + (c.get("title") or c["id"])[:16])   # a film series counts as one source
CLIPUSE = {}   # a pickup clip may come back once, as a different shot, in a different act   # one source clip / one source film: never twice in the film
# each pickup belongs to the act whose meaning it answers best (its best rank in that act's patches): the story is spread over all eight acts
HOME = {}
for ai_, (n, roman, title, a, b, beat) in enumerate(ACTS):
    for p in CB[n]["patches"]:
        if p["t1"] <= a or p["t0"] >= b: continue
        for r, i in enumerate(p["cands"]):
            c = byId.get(i)
            if c and c["type"] == "ai" and (src(c) not in HOME or r < HOME[src(c)][1]): HOME[src(c)] = (ai_, r)
    for r, i in enumerate(CB[n]["spine"]):
        c = byId.get(i)
        if c and (src(c) not in HOME or r - 1 < HOME[src(c)][1]): HOME[src(c)] = (ai_, r - 1)
used, plan, punct = set(), [], 0
for ACT, (n, roman, title, a, b, beat) in enumerate(ACTS):
    s = S[n]; beats = s["beats"]; snap = lambda t: min(beats, key=lambda x: abs(x - t)); a2, b2 = (snap(a) if a > 0 else 0.0), min(snap(b), s["dur"])
    pats = [p for p in CB[n]["patches"] if p["t1"] > a2 + .3 and p["t0"] < b2 - .3]; spine = [i for i in CB[n]["spine"] if i in byId]
    free = V[n]["free"]; isfree = lambda t0, t1: any(t0 >= x - .2 and t1 <= y + .2 for x, y in free)
    slots, prev, airun = [], None, 0
    for pi, p in enumerate(pats):
        t0, t1 = max(p["t0"], a2), min(p["t1"], b2)
        if p["flags"] and "null" in p["flags"]: slots.append({"t0": t0, "dur": t1 - t0, "w": p["world"], "nul": True}); continue
        t, nb = t0, max(1, p["beats"], int(np.ceil((3.4 if ACT in (2, 7) else 2.6) / (60 / s["tempo"])))); first = True   # a shot holds long enough to be read
        while t < t1 - .3:
            nxt = [x for x in beats if x > t + .05]; end = nxt[nb - 1] if len(nxt) >= nb else t1
            if end > t1 - .3 or end <= t + .3: end = t1
            dur = end - t; spineslot = first and (pi == 0 or p["phase"] != pats[pi - 1]["phase"]); first = False
            pool = ([byId[i] for i in spine] if spineslot else []) + [byId[i] for i in p["cands"] if i in byId] + [byId[i] for i in p.get("ai_cands", []) if i in byId and i not in p["cands"]]
            span_of = lambda c: (c.get("out", 0) - c.get("in", 0)) if c["type"] == "ai" else (c.get("dur") or 6)
            best = None
            for relax in (0, 1, 2):
              bs = -1e9
              for r, c in enumerate(pool):
                if fam(c) in used or c["id"] in used or c["type"] == "drawn": continue
                if span_of(c) < dur * .6: continue   # it cannot cover its place even slowed: it would freeze
                if c["type"] == "archive" and src(c) in used: continue
                if c["type"] == "ai" and (len(CLIPUSE.get(src(c), [])) >= 2 or ACT in CLIPUSE.get(src(c), [])): continue
                if relax < 1 and c["type"] == "ai" and not CLIPUSE.get(src(c)) and HOME.get(src(c), (ACT,))[0] != ACT: continue   # first use: saved for the act it belongs to
                if c["type"] == "archive" and r > ((5 if ACT >= 6 else 2) + 4 * relax + (len(spine) if spineslot else 0)): continue   # archive only where it truly answers (wider in the freedom and memory acts)
                po = c.get("poison") or 0
                if c["type"] == "ai" and po > .5 and not (punct < 1 and po < .8 and r < 4): continue
                if c["type"] == "ai" and airun >= (5 if "pound" in p["flags"] else 3): continue
                span = (c.get("out", 0) - c.get("in", 0)) if c["type"] == "ai" else (c.get("dur") or 6)
                sc = (4.5 if spineslot and c["id"] in spine else 0) + 3.2 - .14 * (r if not spineslot else max(0, r - len(spine)))
                sc += .9 if c["type"] == "ai" else (.6 if "archive" in p["flags"] else -.3)   # the pickups carry the story
                sc -= 2.5 * max(0, 1 - span / dur) if span < dur else 0                       # a shot shorter than its place would freeze or run on
                if prev is not None: sc += .8 * float(K[kix[c["id"]]] @ K[kix[prev["id"]]])   # frame rhyme with the shot before
                if "pound" in p["flags"] and len(c.get("pound") or []) >= 2: sc += 1
                if sc > bs: bs, best = sc, c
              if best is not None: break
              if relax == 0 and slots and not slots[-1].get("nul") and slots[-1].get("c") and span_of(slots[-1]["c"]) >= (slots[-1]["dur"] + dur) * .6: break   # the shot before can hold
            if best is None and slots and not slots[-1].get("nul") and slots[-1].get("c") and span_of(slots[-1]["c"]) >= (slots[-1]["dur"] + dur) * .6: slots[-1]["dur"] += dur; t = end; continue
            if best is None: best = next((c for c in pool if c["id"] not in used), pool[0])
            used.add(best["id"]); used.add(fam(best)); used.add(src(best)) if best["type"] == "archive" else CLIPUSE.setdefault(src(best), []).append(ACT); prev = best; airun = airun + 1 if best["type"] == "ai" else 0
            if best["type"] == "ai" and (best.get("poison") or 0) > .5: punct += 1
            at, rate, locked = lock(best, t, dur, beats, s["tempo"]) if best["type"] == "ai" else (None, 1.0, 0)
            snd = best["type"] == "ai" and not (set((best.get("sound") or [])[:2]) & MUSICAL) and ((best.get("words") and isfree(t, end)) or (not best.get("words") and set(best.get("sound") or []) & WORLD_SND.get(p["world"], set())))
            slots.append({"t0": t, "dur": dur, "w": p["world"], "c": best, "at": at, "rate": rate, "locked": locked, "sound": bool(snd), "patch": p["id"]}); t = end
    plan.append((n, roman, title, a2, b2, beat, slots))
    print(f"{roman:>4} {title:26s} {b2 - a2:5.1f}s {len(slots):3d} shots · AI {sum(1 for x in slots if x.get('c') and x['c']['type'] == 'ai'):2d} · locked {sum(x.get('locked', 0) for x in slots)}", flush=True)
print("shots in the film:", sum(len(x[6]) for x in plan), "· families used once:", len(used) // 2, flush=True)
if os.environ.get("DRY"):
    for n, roman, title, a2, b2, beat, slots in plan: print(roman, "|", " / ".join(((x.get("c") or {}).get("title") or "■ black")[:22] + ("·A" if (x.get("c") or {}).get("type") == "ai" else "") for x in slots[:14]))
    raise SystemExit
# ---- render each act through cut.py (song excerpt as its sound), then assemble
def run(a): subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)
acts = []
for n, roman, title, a2, b2, beat, slots in plan:
    ex = os.path.join(T, f"act-{n}.wav"); L_ = b2 - a2
    run(["-ss", f"{a2:.3f}", "-t", f"{L_:.3f}", "-i", os.path.join(ALB, S[n]["file"]), "-af", f"afade=t=in:d=0.02,afade=t=out:st={L_ - .06:.3f}:d=0.06", "-ar", "48000", "-ac", "2", ex])
    bf = os.path.join(T, f"beats-{n}.json"); json.dump([round(x - a2, 3) for x in S[n]["beats"] if a2 <= x < b2], open(bf, "w"))
    cl = {"tool": "blacktop", "song": n, "title": title, "file": ex, "register": "raw", "bet": "FINAL", "version": f"act-{roman}", "meme": False, "beats_file": bf,
          "slots": [{"t0": round(x["t0"] - a2, 3), "dur": round(x["dur"], 3), "world": x["w"], "cut_in": "cut", "look": "raw",
                     "plate": ({"id": "black", "type": "black", "media": "", "in": None, "rate": 1} if x.get("nul") else
                               {"id": x["c"]["id"], "type": x["c"]["type"], "media": x["c"]["src"] if x["c"]["type"] == "ai" else x["c"]["media"], "in": x["at"], "out": x["c"].get("out") if x["c"]["type"] == "ai" else x["c"].get("dur"), "rate": x["rate"]}),
                     "figure": None, "sound": x.get("sound", False), "locked": x.get("locked", 0)} for x in slots]}
    p = os.path.join(T, f"act-{n}.json"); json.dump(cl, open(p, "w"), ensure_ascii=False)
    subprocess.run(["python3", os.path.join(D, "cut.py"), "--cutlist", p], check=True, capture_output=True)
    acts.append((n, roman, title, beat, os.path.join(OUT, f"blacktop-{n}-final-act-{roman}.mp4"))); print("rendered act", roman, flush=True)
# ---- headers over each act's first 2.6 s, then join: cold open + acts (hard cuts on the downbeat) + the developer
def header(roman, title, beat):
    p = os.path.join(T, f"hdr-{roman}.png"); im = Image.new("RGBA", (AS.W, AS.H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f1, f2, f3 = ImageFont.truetype(AS.IMPACT, 54), ImageFont.truetype(AS.BOLD, 24), ImageFont.truetype(AS.BOLD, 17)
    d.rectangle([40, 560, 48, 676], fill=(242, 90, 23, 255)); d.text((64, 556), roman, font=f1, fill=(242, 90, 23, 255), stroke_width=2, stroke_fill=(0, 0, 0, 200))
    d.text((64, 620), title, font=f2, fill=(235, 229, 216, 255), stroke_width=2, stroke_fill=(0, 0, 0, 200)); d.text((64, 652), beat, font=f3, fill=(200, 196, 186, 255), stroke_width=2, stroke_fill=(0, 0, 0, 200))
    im.save(p); return p
parts = [AS.norm(AS.coldopen("final", "A FILM IN EIGHT RITES"), os.path.join(T, "cold.mp4"))]
for n, roman, title, beat, mp4 in acts:
    o = os.path.join(T, f"act-{roman}.mp4")
    run(["-i", mp4, "-loop", "1", "-t", "3", "-i", header(roman, title, beat), "-filter_complex",
         f"[0:v]scale={AS.W}:{AS.H},setsar=1,fps=24[b];[1:v]format=rgba,fade=t=in:st=0.15:d=0.3:alpha=1,fade=t=out:st=2.3:d=0.4:alpha=1[h];[b][h]overlay=0:0:enable='lt(t,2.8)',format=yuv420p[v]",
         "-map", "[v]", "-map", "0:a", *AS.ENC, *AS.AENC, o]); parts.append(o)
end = os.path.join(T, "end.png"); AS.card(end, [("THE DEVELOPER", AS.IMPACT, 64, 250, (235, 229, 216, 255), 6), ("is still up.", AS.BOLD, 30, 350, (133, 139, 147, 255), 4),
    ("songs: The Liturgy of the Two Buttons · archive: public-domain films from the Moving Image Archive · made in the Cineosis Lab", AS.BOLD, 15, 640, (90, 95, 100, 255), 1)])
ec = os.path.join(T, "end.mp4"); run(["-ss", "1", "-t", "4", "-i", AS.AI("Soldier_in_mask_staring_deadpan"), "-loop", "1", "-t", "6", "-i", end, "-f", "lavfi", "-t", "10", "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
    f"[0:v]scale={AS.W}:{AS.H}:force_original_aspect_ratio=increase,crop={AS.W}:{AS.H},setsar=1,fps=24,trim=0:4,setpts=PTS-STARTPTS,fade=t=out:st=3.4:d=0.6[s];[1:v]fps=24,format=yuv420p,fade=t=in:st=0:d=0.6[e];[s][e]concat=n=2:v=1,format=yuv420p[v]",
    "-map", "[v]", "-map", "2:a", "-t", "10", *AS.ENC, *AS.AENC, ec]); parts.append(ec)
final = os.path.join(OUT, "slopfeeder-final.mp4"); AS.join(parts, final)
run(["-i", final, "-c:v", "libx264", "-preset", "slow", "-b:v", "1250k", "-maxrate", "1700k", "-bufsize", "3400k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(OUT, "slopfeeder-final-web.mp4")])
json.dump([{"act": r, "song": n, "title": t, "beat": bt, "window": [round(a, 2), round(b, 2)], "shots": [{"t0": round(x["t0"], 2), "id": (x.get("c") or {}).get("id", "black"), "type": (x.get("c") or {}).get("type", "black"), "patch": x.get("patch")} for x in sl]} for n, r, t, a, b, bt, sl in plan],
          open(os.path.join(D, "final.json"), "w"), ensure_ascii=False, indent=0)
print("final:", final, flush=True)
