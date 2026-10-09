"""HOMO LUDENS — plates of the editing-as-a-ball-game world, drawn from the real corpus, not imagined: every picture is a Slopfeeder
card at its real place in the field (slopfeeder/field.json: UMAP of CLIP with the AI/archive gap removed), every ball path is computed
with the lab's own critic (a cut scores as monte/sim.js scores one: a Gaussian of CLIP cosine around .72, as sea-core.js does), every
forecast cloud is a Monte Carlo of jittered shots (as putt-op-off.html forecasts), every rally answers the shot before it.
usage: python3 lab/ludens/plates.py   -> lab/ludens/plates/*.jpg"""
import json, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SF = os.path.join(L, "slopfeeder"); OUT = os.path.join(L, "ludens", "plates"); os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080; BG = (12, 13, 15); INK = (235, 229, 216); DIM = (133, 139, 147); HOT = (242, 90, 23)
P = [(90, 205, 230), (240, 110, 100), (240, 205, 70), (170, 130, 240), (120, 210, 150)]   # players
MONO = "/System/Library/Fonts/Menlo.ttc"; F = lambda n: ImageFont.truetype(MONO, n)
FD = json.load(open(os.path.join(SF, "field.json"))); A = json.load(open(os.path.join(SF, "atlas.json")))["cards"]
E = np.fromfile(os.path.join(SF, "atlas-emb.bin"), np.int8).reshape(len(A), -1).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
IX = {c["id"]: i for i, c in enumerate(A)}
cards = [c for c in FD["cards"] if c["id"] in IX and os.path.exists(os.path.join(SF, c["th"]))]
_th = {}
def thumb(c, w, h):
    k = (c["id"], w, h)
    if k not in _th:
        im = Image.open(os.path.join(SF, c["th"])).convert("RGB"); r = max(w / im.width, h / im.height); im = im.resize((max(w, int(im.width * r)), max(h, int(im.height * r))))
        _th[k] = im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width - w) // 2 + w, (im.height - h) // 2 + h))
    return _th[k]
def rpaste(im, t, deg, x, y):   # a rotated card with clean corners
    r = t.convert("RGBA").rotate(deg, expand=True, resample=Image.BICUBIC); im.paste(r, (int(x - r.width / 2), int(y - r.height / 2)), r)
def join(a, b):   # the lab's cut score
    c = float(E[IX[a["id"]]] @ E[IX[b["id"]]]); return math.exp(-(((c - .72) / .12) ** 2) / 2)
def grid(cols, rows, x0, y0, x1, y1, pool=None):   # the field, decluttered: one card per cell (the strongest chain), at its UMAP place
    pool = pool or cards; G = {}
    for c in pool:
        i, j = min(cols - 1, int(c["xy"][0] * cols)), min(rows - 1, int(c["xy"][1] * rows))
        if (i, j) not in G or c.get("mc", 0) > G[(i, j)].get("mc", 0): G[(i, j)] = c
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    return {k: (c, x0 + (k[0] + .5) * cw, y0 + (k[1] + .5) * ch) for k, c in G.items()}, cw, ch
def paste_field(im, G, cw, ch, dim=.55, pad=3):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for (i, j), (c, x, y) in G.items():
        t = thumb(c, int(cw - pad), int(ch - pad)); im.paste(Image.blend(Image.new("RGB", t.size, BG), t, dim), (int(x - t.width / 2), int(y - t.height / 2)))
def lift(im, c, x, y, w, h, col, width=3):   # a card the ball touched: full brightness, outlined in the player's colour
    t = thumb(c, int(w), int(h)); im.paste(t, (int(x - w / 2), int(y - h / 2))); ImageDraw.Draw(im).rectangle([x - w / 2 - 2, y - h / 2 - 2, x + w / 2 + 1, y + h / 2 + 1], outline=col, width=width)
def curve(d, pts, col, width=4, dash=False):   # Catmull-Rom through the touched cards
    if len(pts) < 2: return
    P_ = [pts[0]] + pts + [pts[-1]]; out = []
    for k in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[k - 1], P_[k], P_[k + 1], P_[k + 2]
        for s in range(14):
            t = s / 14; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[q]) + (-p0[q] + p2[q]) * t + (2 * p0[q] - 5 * p1[q] + 4 * p2[q] - p3[q]) * t2 + (-p0[q] + 3 * p1[q] - 3 * p2[q] + p3[q]) * t3) for q in (0, 1)))
    out.append(pts[-1])
    for a, b in zip(out, out[1:]):
        if dash and (int(math.hypot(a[0] - out[0][0], a[1] - out[0][1])) // 14) % 2: continue
        d.line([a, b], fill=col, width=width)
def ball(d, x, y, col, r=11):
    for k in range(5, 0, -1): d.ellipse([x - r - k * 3, y - r - k * 3, x + r + k * 3, y + r + k * 3], outline=tuple(int(v * (.15 + .1 * (5 - k))) for v in col), width=2)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col); d.ellipse([x - r * .45, y - r * .6, x - r * .05, y - r * .2], fill=(255, 255, 255))
def shoot(G, start, angle, steps=7, reach=3.2, cone=1.0, seed=0, avoid=()):   # a putt across the field: each next card is the best cut within reach, ahead of the ball
    rnd = random.Random(seed); keys = list(G); at = start; path = [start]; used = set(avoid) | {start}; ang = angle
    for _ in range(steps):
        c0, x0, y0 = G[at]; best, bs = None, -9
        for k in keys:
            if k in used: continue
            c, x, y = G[k]; dx, dy = k[0] - at[0], k[1] - at[1]; dist = math.hypot(dx, dy)
            if dist < .9 or dist > reach: continue
            da = abs((math.atan2(dy, dx) - ang + math.pi) % (2 * math.pi) - math.pi)
            if da > cone: continue
            s = join(c0, c) - .15 * da + rnd.random() * .05
            if s > bs: bs, best = s, k
        if not best: break
        ang = .7 * ang + .3 * math.atan2(best[1] - at[1], best[0] - at[0]); path.append(best); used.add(best); at = best
    return path
def strip(im, d, x, y, cs, col, label, w=118, h=66):
    d.text((x, y + h / 2 - 16), label, font=F(30), fill=col); x += 70
    for c in cs: lift(im, c, x + w / 2, y + h / 2, w, h, col, 2); x += w + 6
    return x
def title(d, a, b=""):
    d.text((44, 30), a, font=F(26), fill=INK); d.text((44, 66), b, font=F(17), fill=DIM)
def save(im, name): im.save(os.path.join(OUT, name), quality=88); print("plate", name)
# ---------------------------------------------------------------------------------------------------------------------------------
def p_putt_off():   # 01 · PUTT-OFF: three players putt across the field; each ball collects the cuts it rolls through; the flag is a story beat
    im = Image.new("RGB", (W, H), BG); G, cw, ch = grid(26, 13, 40, 110, 1880, 820); paste_field(im, G, cw, ch); d = ImageDraw.Draw(im, "RGBA")
    title(d, "CINEOSIS · PUTT-OFF", "three players, one field of 1,477 shots laid out by meaning · each ball rolls through the cuts that join best ahead of it")
    flag = min(G, key=lambda k: abs(k[0] - 13) + abs(k[1] - 2)); fc, fx, fy = G[flag]
    for r in range(5, 0, -1): d.ellipse([fx - r * 16, fy - r * 10, fx + r * 16, fy + r * 10], outline=(240, 110, 100, 60 + 25 * (5 - r)), width=2)
    starts = [(min(G, key=lambda k: abs(k[0] - 2) + abs(k[1] - 6)), -.4), (min(G, key=lambda k: abs(k[0] - 4) + abs(k[1] - 11)), -.7), (min(G, key=lambda k: abs(k[0] - 24) + abs(k[1] - 11)), -2.3)]
    used = set(); paths = []
    for p, (s, a) in enumerate(starts): pa = shoot(G, s, a, steps=6, seed=p, avoid=used); used |= set(pa); paths.append(pa)
    for p, pa in enumerate(paths):
        pts = [G[k][1:] for k in pa]; curve(d, pts, P[p] + (230,), 4)
        for k in pa[1:]: lift(im, G[k][0], G[k][1], G[k][2], cw - 3, ch - 3, P[p])
        ball(d, *pts[-1], P[p]); d = ImageDraw.Draw(im, "RGBA")
    d.line([fx, fy, fx, fy - 70], fill=INK, width=3); d.polygon([(fx, fy - 70), (fx + 34, fy - 60), (fx, fy - 50)], fill=HOT)
    x = 44
    for p, pa in enumerate(paths): x = strip(im, d, x, 900, [G[k][0] for k in pa[:4]], P[p], f"0{p + 1}", 100, 56) + 40
    save(im, "01-putt-off.jpg")
def p_forecast():   # 02 · REHEARSE: aim, and the forecast fans out — 25 jittered putts (putt-op's probability space) over wells (story beats) and ridges (poison)
    im = Image.new("RGB", (W, H), BG); G, cw, ch = grid(26, 15, 40, 110, 1880, 1040); paste_field(im, G, cw, ch, .4); d = ImageDraw.Draw(im, "RGBA")
    title(d, "CINEOSIS · REHEARSE", "aim and hold: 25 imagined putts narrow as you focus · wells pull toward story beats, ridges push away from poison · release to commit")
    wells = [k for k, (c, x, y) in G.items() if c.get("ca", 0) > .985][:3] or list(G)[:3]
    for k in wells:
        c, x, y = G[k]
        for r in range(7, 0, -1): d.ellipse([x - r * 22, y - r * 14, x + r * 22, y + r * 14], outline=(90, 205, 230, 30 + 14 * (7 - r)), width=2)
    start = min(G, key=lambda k: abs(k[0] - 3) + abs(k[1] - 12)); sx, sy = G[start][1:]
    for j in range(25):
        pa = shoot(G, start, -.55 + (j - 12) * .045, steps=6, reach=3.6, cone=.7, seed=100 + j); pts = [G[k][1:] for k in pa]
        curve(d, pts, (235, 229, 216, 40 if j else 255), 2 if j else 4, dash=bool(j))
        if not j:
            for k in pa[1:]: lift(im, G[k][0], G[k][1], G[k][2], cw - 3, ch - 3, P[0])
    d = ImageDraw.Draw(im, "RGBA"); ball(d, sx, sy, P[0], 13)
    d.line([sx, sy, sx - 160, sy + 90], fill=P[0] + (180,), width=3); d.text((sx - 330, sy + 100), "pull back to aim · the cloud is the machine's rollouts", font=F(16), fill=DIM)
    save(im, "02-rehearse.jpg")
def p_tennis():   # 03 · TENNIS: the ring of the lab's Ring view; each return must answer the shot before it (the cut score); each player collects the shots they hit from
    im = Image.new("RGB", (W, H), (244, 240, 232)); d = ImageDraw.Draw(im, "RGBA"); cx, cy, R = 760, 590, 380
    d.text((44, 30), "CINEOSIS · TENNIS", font=F(26), fill=(30, 30, 30)); d.text((44, 66), "two players on the ring · a return lands on the shot that answers the last one · a jarring cut is a fault", font=F(17), fill=(110, 110, 110))
    ring = sorted(random.Random(4).sample(cards, 40), key=lambda c: math.atan2(c["xy"][1] - .5, c["xy"][0] - .5)); n = len(ring)
    d.ellipse([cx - R - 62, cy - R - 62, cx + R + 62, cy + R + 62], fill=(10, 10, 12)); d.ellipse([cx - R + 52, cy - R + 52, cx + R - 52, cy + R - 52], fill=(0, 0, 0))
    pos = []
    for k, c in enumerate(ring):
        a = k / n * 2 * math.pi - math.pi / 2; x, y = cx + R * math.cos(a), cy + R * math.sin(a); pos.append((x, y)); rpaste(im, thumb(c, 88, 56), -math.degrees(a) - 90, x, y)
    d = ImageDraw.Draw(im, "RGBA"); at, side, hits = 3, 0, [[], []]; seen = {3}
    for r in range(9):   # the rally: the opponent's half of the ring, the best answer to the last shot
        lo = (n // 2) * (1 - side); cand = [(join(ring[at], ring[k]), k) for k in range(lo + 2, lo + n // 2 - 2) if k not in seen]; s, nxt = max(cand); seen.add(nxt)
        d.line([pos[at], pos[nxt]], fill=P[side] + (150 if r < 8 else 255,), width=2 if r < 8 else 4); hits[side].append(ring[at]); at, side = nxt, 1 - side
    for p in (0, 1):
        for c in hits[p][:4]:
            k = ring.index(c); x, y = pos[k]; d.rectangle([x - 50, y - 34, x + 50, y + 34], outline=P[p], width=4)
    ball(d, *pos[at], (255, 255, 255), 12); last = ring[at]; t = thumb(last, 470, 264); im.paste(t, (cx - 235, cy - 132))
    for p, x0 in ((0, 1300), (1, 1300)):
        y0 = 300 if p == 0 else 640; d.text((x0, y0 - 40), f"0{p + 1} · collected", font=F(20), fill=P[p] if p else (40, 140, 170)); x = x0
        for c in hits[p][:4]: t = thumb(c, 140, 80); im.paste(t, (x, y0)); d.rectangle([x - 2, y0 - 2, x + 141, y0 + 81], outline=P[p], width=3); x += 148
    save(im, "03-tennis.jpg")
def p_course():   # 04 · THE COURSE: nine holes = the nine Slopfeeder films; the cinema in the middle plays the round
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im, "RGBA"); title(d, "CINEOSIS · THE COURSE", "nine holes, nine films: each island is a film's own field of takes · the round you play is screened in the middle")
    films = json.load(open(os.path.join(SF, "lattice", "index.json")))[:9]; cx, cy = 960, 580
    for k, fm in enumerate(films):
        a = k / 9 * 2 * math.pi - math.pi / 2; x, y = cx + 690 * math.cos(a), cy + 380 * math.sin(a)
        Lt = json.load(open(os.path.join(SF, "lattice", fm["id"] + ".json"))); ids = [x_["id"] for c in Lt["cols"][:40] for x_ in c["cands"][:1] if x_.get("id") in IX]
        pool = [c for c in cards if c["id"] in set(ids)][:24]; gx = 6
        d.rounded_rectangle([x - 175, y - 95, x + 175, y + 95], radius=40, fill=(30, 40, 30), outline=(120, 160, 110), width=3)
        for j, c in enumerate(pool[:18]): t = thumb(c, 52, 30); im.paste(t, (int(x - 165 + (j % gx) * 56), int(y - 70 + (j // gx) * 34)))
        d.text((x - 165, y + 40), f"{k + 1} · {fm['title'][:34]}", font=F(14), fill=INK); d.line([x + 140, y - 60, x + 140, y - 110], fill=INK, width=2); d.polygon([(x + 140, y - 110), (x + 166, y - 102), (x + 140, y - 94)], fill=HOT)
        d.line([(x, y), (cx + (x - cx) * .42, cy + (y - cy) * .42)], fill=(235, 229, 216, 60), width=2)
    d.ellipse([cx - 260, cy - 160, cx + 260, cy + 160], fill=(5, 5, 6), outline=(80, 80, 80), width=3)
    st = json.load(open(os.path.join(SF, "lattice", "story.json"))); sc = [c for c in cards if c["id"] == st["cols"][5]["cands"][0].get("id")] or cards[:1]; t = thumb(sc[0], 380, 214); im.paste(t, (cx - 190, cy - 107))
    save(im, "04-course.jpg")
def p_join():   # 05 · JOIN: four players' paths through the story cut's lattice (the lanes of Syzygy) meet where they agree; OUR FILM is the consensus
    Lt = json.load(open(os.path.join(SF, "lattice", "story.json"))); cols = [c for c in Lt["cols"] if c["kind"] == "ai"][:16]
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im, "RGBA"); title(d, "CINEOSIS · JOIN", "four players' paths through the same 16 shots of the story cut · where they agree the paths join · OUR FILM is the take most of them chose")
    rnd = random.Random(7); paths = [[0] * len(cols)]
    for p in range(3): paths.append([0 if rnd.random() < .45 else rnd.randrange(min(6, len(c["cands"]))) for c in cols])
    x0, y0, cw, ch = 60, 150, 110, 62
    for i, c in enumerate(cols):
        for k, x in enumerate(c["cands"][:6]):
            cc = next((q for q in cards if q["id"] == x.get("id")), None)
            if cc: t = thumb(cc, cw - 6, ch - 6); im.paste(Image.blend(Image.new("RGB", t.size, BG), t, .45), (x0 + i * cw, y0 + k * ch))
    d = ImageDraw.Draw(im, "RGBA")
    for p, pa in enumerate(paths):
        pts = [(x0 + i * cw + cw / 2 - 3 + (p - 1.5) * 4, y0 + k * ch + ch / 2 - 3) for i, k in enumerate(pa)]; curve(d, pts, P[p] + (220,), 3)
        for i, k in enumerate(pa): d.rectangle([x0 + i * cw - 1, y0 + k * ch - 1, x0 + i * cw + cw - 6, y0 + k * ch + ch - 6], outline=P[p], width=2)
    cons = [max(set(col), key=col.count) for col in zip(*paths)]; d.text((60, 560), "OUR FILM", font=F(22), fill=INK); x = 60
    for i, k in enumerate(cons):
        x_ = cols[i]["cands"][k]; cc = next((q for q in cards if q["id"] == x_.get("id")), None)
        if cc: im.paste(thumb(cc, 104, 58), (x, 600)); n = sum(1 for pa in paths if pa[i] == k); d.text((x + 4, 662), "●" * n, font=F(14), fill=HOT)
        x += 110
    for p, nm in enumerate(["the cut", "you", "ren", "scout"]): d.text((60 + p * 200, 720), "━ " + nm, font=F(18), fill=P[p])
    save(im, "05-join.jpg")
def p_open_cut():   # 06 · OPEN CUT: four players at the rim of the ring, the machine as a fifth (dashed); the centre plays the shot in play
    im = Image.new("RGB", (W, H), (244, 240, 232)); d = ImageDraw.Draw(im, "RGBA"); cx, cy, R = 900, 540, 400
    d.text((44, 30), "CINEOSIS · OPEN CUT", font=F(26), fill=(30, 30, 30)); d.text((44, 66), "four players and the machine around one ring · whoever reaches the next shot first cuts it in · the strip below is the film so far", font=F(17), fill=(110, 110, 110))
    ring = sorted(random.Random(11).sample(cards, 14), key=lambda c: c["xy"][0]); n = len(ring)
    d.ellipse([cx - R - 60, cy - R - 60, cx + R + 60, cy + R + 60], fill=(10, 10, 12)); d.ellipse([cx - R + 90, cy - R + 90, cx + R - 90, cy + R - 90], fill=(0, 0, 0))
    for k, c in enumerate(ring):
        a = k / n * 2 * math.pi - math.pi / 2; x, y = cx + (R - 15) * math.cos(a), cy + (R - 15) * math.sin(a); rpaste(im, thumb(c, 150, 96), -math.degrees(a) - 90, x, y)
    d = ImageDraw.Draw(im, "RGBA"); t = thumb(ring[3], 440, 250); im.paste(t, (cx - 220, cy - 125))
    for p, a in enumerate([-2.35, -.8, .8, 2.35]):
        x, y = cx + (R + 120) * math.cos(a), cy + (R + 120) * math.sin(a); c = ring[(p * 4 + 2) % n]; t = thumb(c, 150, 100); im.paste(t, (int(x - t.width / 2), int(y - t.height / 2)))
        d.rectangle([x - t.width / 2, y - t.height / 2, x + t.width / 2, y + t.height / 2], outline=P[p], width=5); d.text((x - 12, y - t.height / 2 - 34), f"0{p + 1}", font=F(22), fill=(30, 30, 30))
        d.arc([cx - R - 40, cy - R - 40, cx + R + 40, cy + R + 40], math.degrees(a) - 12, math.degrees(a) + 12, fill=P[p], width=12)
    curve(d, [(cx + 180, cy + 150), (cx + 260, cy + 220), (cx + 300, cy + 300)], (170, 130, 240, 255), 4, dash=True); d.text((cx + 130, cy + 140), "AI", font=F(18), fill=(170, 130, 240))
    x = cx - 360
    for k in (3, 5, 9, 12): im.paste(thumb(ring[k], 170, 96), (x, 990)); x += 180
    save(im, "06-open-cut.jpg")
def p_table():   # 07 · THE LIGHT TABLE: the party version — the stand shows the branches; phones hold each player's hand of takes; LOCK commits
    im = Image.new("RGB", (W, H), (236, 232, 222)); d = ImageDraw.Draw(im, "RGBA"); d.text((44, 30), "CINEOSIS · THE LIGHT TABLE", font=F(26), fill=(30, 30, 30)); d.text((44, 66), "the stand is the table: branches from one shot, one per player · each phone holds a hand of three takes and a LOCK · WATCH plays the branch that wins", font=F(17), fill=(110, 110, 110))
    d.rounded_rectangle([140, 120, 1780, 980], radius=24, fill=(250, 248, 242), outline=(200, 196, 186), width=3)
    rnd = random.Random(3); start = rnd.choice(cards); im.paste(thumb(start, 300, 170), (220, 470)); d.rectangle([218, 468, 522, 642], outline=(240, 110, 100), width=3)
    for p in range(4):
        y = 180 + p * 190; pa = [start]
        for _ in range(4):
            nxt = max(rnd.sample(cards, 60), key=lambda c: join(pa[-1], c)); pa.append(nxt)
        curve(d, [(522, 555), (600, y + 60), (660, y + 60)], P[p] + (255,), 4, dash=(p == 1))
        for j, c in enumerate(pa[1:]): im.paste(thumb(c, 190, 108), (660 + j * 200, y + 6)); d.rectangle([658 + j * 200, y + 4, 852 + j * 200, y + 116], outline=P[p], width=3)
        d.ellipse([610, y + 40, 650, y + 80], fill=P[p]); d.text((622, y + 48), "ARLT"[p], font=F(18), fill=(255, 255, 255))
    for (x, y), p in zip([(20, 140), (1790, 140), (20, 640), (1790, 640)], range(4)):
        d.rounded_rectangle([x, y, x + 120, y + 260], radius=18, fill=(30, 30, 32));
        for j in range(3): c = rnd.choice(cards); im.paste(thumb(c, 100, 56), (x + 10, y + 16 + j * 62))
        d.rounded_rectangle([x + 14, y + 210, x + 106, y + 244], radius=14, fill=P[p]); d.text((x + 38, y + 216), "LOCK", font=F(16), fill=(255, 255, 255))
    d.ellipse([920, 990, 1000, 1070], fill=(40, 90, 70)); d.polygon([(948, 1010), (948, 1050), (980, 1030)], fill=(255, 255, 255))
    save(im, "07-light-table.jpg")
if __name__ == "__main__":
    for f in (p_putt_off, p_forecast, p_tennis, p_course, p_join, p_open_cut, p_table): f()
