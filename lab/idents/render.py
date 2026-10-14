"""CINEOSIS IDENTS v3. One short per film and one per sign, each recognisable at a glance.
Brand, the same in all of them: paper, ink, the red thread, the O with two eyes. Colour lives only inside an O, as the tone
of the archive shots. Red is only ever thread. Nothing is drawn over a picture.
What tells them apart is the FIGURE: how many Os there are, where they sit, how big they are, and the path the thread takes.
  Machines - one O ringed by nine small eyes.      Choosing - three Os racing on red lanes.     Syzygy - three Os sliding into line.
  Odyssey  - an O over the sea at the end of a long voyage thread.      Republic - an O and its shadow on the cave wall.  ...
Signs take their family's figure (a giant close-up O for affect, mirrored twins for reflection, a broken O for break...)
and their symbol in the corner. Films carry their number in the corner.
The hero O cuts between five archive shots by blinking, holds the sixth and winks at it, then names itself.
usage: python3 idents/render.py films [i ...] | signs [n ...]"""
import json, os, sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE); C44 = os.path.dirname(LAB)
FONTS = os.environ.get('IDENT_FONTS', '/private/tmp/claude-502/-Users-gaia-resurrecting-atlantis/18b19393-4aff-4925-a915-75f1664883b3/scratchpad/fonts')
W, H, SS, FPS = 1280, 720, 2, 24
PAPER, INK, MUTE, RED = (244, 239, 230), (23, 20, 15), (139, 132, 120), (224, 72, 58)
HOLD = 44
LO = .4

def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def mix(a, b, t): t = max(0, min(1, t)); return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def kv(f, ks):
    if f <= ks[0][0]: return ks[0][1]
    for (a, va), (b, vb) in zip(ks, ks[1:]):
        if f <= b:
            t = ease((f - a) / max(1, b - a))
            return tuple(lerp(x, y, t) for x, y in zip(va, vb)) if isinstance(va, tuple) else lerp(va, vb, t)
    return ks[-1][1]
def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), int(size * SS))
def blinkC(f, at): return {0: .55, 1: 1.0, 2: .45}.get(f - at, 0.0)
def winkC(f, at, c=6, h=16, o=8):
    k = f - at
    if k < 0: return 0
    if k < c: return ease(k / c)
    if k < c + h: return 1
    if k < c + h + o: return 1 - ease((k - c - h) / o)
    return 0
def sw(r): return max(3.0, r * 26 / 210)          # ring stroke, in proportion to the canonical mark

# ---------------------------------------------------------------- footage
def probe(src):
    try:
        return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                                    capture_output=True, text=True, timeout=60).stdout.strip())
    except Exception: return 0.0
def frames_of(src, n, size):
    path = src if src.startswith('http') else os.path.join(LAB, src)
    d = probe(path); start = max(0.0, d * 0.35) if d > 2 else 0.0
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{start:.2f}', '-i', path, '-frames:v', str(n),
           '-vf', f'fps={FPS},scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size},format=gray',
           '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    raw = subprocess.run(cmd, capture_output=True, timeout=240).stdout
    k = len(raw) // (size * size)
    if k == 0: return None
    arr = np.frombuffer(raw[:k * size * size], np.uint8).reshape(k, size, size)
    return [arr[i % k] for i in range(n)]
def toner(accent):
    ink, pap = np.array(INK, np.float32), np.array(PAPER, np.float32)
    acc = np.array(mix(accent, (118, 110, 98), .3), np.float32)
    def tone(g):
        t = np.clip((g.astype(np.float32) / 255.0 - 0.04) / 0.92, 0, 1)[..., None]
        lo = ink + (acc - ink) * np.clip(t * 2, 0, 1); hi = acc + (pap - acc) * np.clip(t * 2 - 1, 0, 1)
        return np.where(t < .5, lo, hi).astype(np.uint8)
    return tone

def eye_mask(size, q, w=0.0):
    m = Image.new('L', (size, size), 0); d = ImageDraw.Draw(m); r = size / 2
    if q <= 0.01: return m
    d.ellipse([0, r - r * q, size, r + r * q], fill=255)
    if w > 0:
        pts = [(-2, -2)] + [(t / 24 * size, (size * .06 + size * .86 * (t / 24) ** 1.6) * w - (1 - w) * 2 + math.sin(t / 24 * math.pi) * size * .05 * w) for t in range(25)] + [(size + 2, -2)]
        d.polygon(pts, fill=0)
        d.polygon([(-2, size + 2)] + [(t / 24 * size, size - size * .16 * w * (t / 24) ** 2) for t in range(25)] + [(size + 2, size + 2)], fill=0)
    return m
def disc(size, alpha=255):
    m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=alpha); return m

# ---------------------------------------------------------------- drawing kit (1x coordinates)
class K:
    def __init__(s, im, alpha=1.0): s.im, s.d, s.al = im, ImageDraw.Draw(im), alpha
    def c(s, a=1.0, col=INK): return mix(PAPER, col, a * s.al)
    def line(s, pts, w=1.2, a=LO, col=INK):
        if len(pts) >= 2 and a * s.al > 0.004:
            s.d.line([(x * SS, y * SS) for x, y in pts], fill=s.c(a, col), width=max(1, round(w * SS)), joint='curve')
    def thread(s, pts, a=1.0): s.line(pts, 3.0, a, RED)
    def ringline(s, x, y, r, a=1.0, w=None):
        if a * s.al > .004:
            w = w or sw(r); s.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], outline=s.c(a), width=max(1, round(w * SS)))
    def fill(s, x, y, r, col):
        s.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=col)
    def rect(s, x, y, w, h, a=LO, lw=1.2):
        s.d.rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], outline=s.c(a), width=max(1, round(lw * SS)))
    def bar(s, x, y, w, h, a=LO):
        if w > 0: s.d.rectangle([x * SS, y * SS, (x + w) * SS, (y + h) * SS], fill=s.c(a))
    def eyes(s, x, y, r, l=0, rr=0, rc=0, look=(0, 0), a=1.0):
        ex, rx = r * .34, r * .17
        for sx, q, cv in ((-1, l, 0.0), (1, rr, rc)):
            cx, cy = x + sx * ex + look[0] * r * .18, y + look[1] * r * .18
            if q < .8:
                ry = max(.8, rx * (1 - q))
                s.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=s.c(a))
            else:
                s.line([(cx - rx * 1.1 + 2.2 * rx * t, cy + 4 * t * (1 - t) * rx * 1.3 * cv) for t in (i / 16 for i in range(17))], max(1.5, r * .075), a)
    def pic(s, img, x, y, r, a=1.0):
        size = int(2 * r * SS)
        if size < 4: return
        p = img.resize((size, size), Image.LANCZOS)
        s.im.paste(p, (int((x - r) * SS), int((y - r) * SS)), disc(size, int(255 * a * s.al)))

def top(x): return (x, -12)

# ---------------------------------------------------------------- figures
# A figure is a function of the frame: the hero O (x, y, r), satellites, threads and ink.
# satellite: (x, y, r, kind, arg, alpha[, look]); kind 'pic' (still of shot arg), 'pic_col' (still in another take's colour),
# 'eyes' (a small mark; arg = blink), 'dom' (a family colour swatch), 'ghost' (the hero's picture as a shadow), 'mirror'.
FIG_R = {'machines': 165, 'archive': 150, 'voice': 160, 'asking': 150, 'choosing': 112, 'syntagma': 118, 'poem': 150,
         'suite': 140, 'scenes': 190, 'cineosis': 140, 'drift': 150, 'compare': 128, 'syzygy': 118, 'cast': 150,
         'chemistry': 145, 'odyssey': 130, 'republic': 135,
         'perception': 165, 'affect': 285, 'action': 135, 'reflection': 145, 'mental': 125, 'time': 150, 'break': 165, 'read': 150}
DOMS = ['perception', 'affect', 'action', 'reflection', 'mental', 'time', 'break', 'read']

def figure(name, f, P):
    g, ch, wk, ci, seed = P['grow'], P['chosen'], P['win_k'], P['cut_i'], P['seed']
    HR = FIG_R[name]; S, T, I = [], [], []
    appear = lambda i: ease((f - 10 - i * 3) / 10)
    hx, hy = 640, 360
    if name == 'machines':
        hx, hy = 640, 380
        for i in range(9):
            a = -math.pi / 2 + (i + .5) * 2 * math.pi / 9; x, y = hx + math.cos(a) * 290, hy + math.sin(a) * 262
            S.append((x, y, 25, 'eyes', blinkC(f % 54, i * 6) + (1 if ci % 9 == i and not ch and f > 42 else 0), appear(i)))
            I.append(lambda k, x=x, y=y, a=a, i=i: k.line([(hx + math.cos(a) * (HR + 14), hy + math.sin(a) * (HR + 14)), (x - math.cos(a) * 32, y - math.sin(a) * 32)], 1.2, LO * appear(i)))
        T.append([top(hx), 'HERO'])
    elif name == 'archive':
        hx, hy = 640, 450
        tips = [(250, 260), (430, 200), (850, 200), (1030, 260)]
        T.append([top(640), (640, 120), 'HERO'])
        for j, (x, y) in enumerate(tips):
            k = ease(g * 3 - j * .3)
            T.append([(640, 120), (lerp(640, x, .45), 128), (lerp(640, x, k), lerp(120, y - 28, k))])
            S.append((x, y, 28, 'pic', j, k))
    elif name == 'voice':
        hx, hy = 640, 410
        pts = []
        for i in range(0, 1281, 8):
            env = max(0, math.sin(i * .009 + 1.0)) * (0.5 + 0.5 * math.sin(i * .031)) * g
            pts.append((i, 120 + math.sin(i * .07 + f * .5) * 44 * env))
        T.append(pts); T.append([(hx, 120), 'HERO'])
    elif name == 'asking':
        hx, hy = 700, 440
        T.append([top(600), (600, 80)] + [(700 + math.cos(math.radians(a)) * 100, 160 + math.sin(math.radians(a)) * 80) for a in range(200, 451, 10)] + ['HERO'])
    elif name == 'choosing':
        hx = kv(f, [(0, 170), (P['T_CHOSEN'] - 30, 760), (P['T_CHOSEN'] + 10, 1010)]); hy = 360
        for j, y in enumerate((140, 580)):
            x = kv(f, [(0, 170), (P['T_CHOSEN'] - 30, 860 - j * 40), (P['T_CHOSEN'] + 10, 900 - j * 50)])
            S.append((x, y, 80, 'pic', j, 1)); T.append([(0, y), (1280, y)])
        T.append([(0, hy), (1280, hy)])
        I.append(lambda k: k.line([(1150, 40), (1150, 680)], 1.2, LO))
    elif name == 'syntagma':
        xs = [150, 360, 920, 1130]
        T.append([top(hx), 'HERO'])
        for j, x in enumerate(xs): S.append((x, hy, 74, 'pic', j, appear(j)))
        for j, (a, b) in enumerate([(224, 286), (434, 522), (758, 846), (1004, 1056)]):
            kind = j % 4
            if kind == 0: T.append([(a, hy), (b, hy)])
            elif kind == 1: T.append([(a, hy), ((a + b) / 2 - 9, hy)]); T.append([((a + b) / 2 + 9, hy), (b, hy)])
            elif kind == 2: T.append([(a, hy - 6), (b, hy - 6)]); T.append([(a, hy + 6), (b, hy + 6)])
            else: T.append([(a, hy), ((a + b) / 2, hy - 20), (b, hy)])
    elif name == 'poem':
        hx, hy = 900, 360
        T.append([top(hx), 'HERO'])
        for i in range(8):
            y = 150 + i * 56; w = 150 + (i * 53) % 130; k = ease(g * 3 - i * .25)
            I.append(lambda kk, y=y, w=w, k=k: kk.bar(110, y - 3, w * k, 6, .55))
            if i in (1, 4, 6) and k > .95:
                T.append([(110 + w + 10, y), (lerp(110 + w, hx - HR, .6), y), (hx - HR * .97, hy + (y - hy) * .3)])
    elif name == 'suite':
        for i in range(5): I.append(lambda k, i=i: k.line([(40, 300 + i * 30), (1240, 300 + i * 30)], 1.2, LO))
        for j, (x, y) in enumerate([(140, 300), (250, 345), (360, 270), (900, 315), (1020, 390), (1140, 285)]):
            S.append((x, y, 30, 'pic', j % 5, appear(j)))
        T.append([top(hx), 'HERO'])
    elif name == 'scenes':
        hx, hy = 800, 380; sx, sy, sr = 250, 250, 58
        S.append((sx, sy, sr, 'eyes', blinkC(f % 40, 20), 1, (1, .3)))
        T.append([top(sx), (sx, sy - sr)]); T.append([top(hx), 'HERO'])
        I.append(lambda k: k.line([(sx + sr + 10, sy + 10), ((sx + hx) / 2, sy + 70), (hx - HR - 12, hy)], 1.2, LO))
    elif name == 'cineosis':
        for i in range(45):
            col, row = i % 9, i // 9; x, y = 280 + col * 90, 180 + row * 90
            if math.hypot(x - hx, y - hy) < HR + 30: continue
            hot = (ci * 7 + i) % 9 == 0
            S.append((x, y, 22 if hot else 15, 'dom', DOMS[(col + row * 2) % 8], appear(i * .3)))
        T.append([top(hx), 'HERO'])
    elif name == 'drift':
        chain = [(150, 110, 30), (290, 175, 42), (450, 250, 58), (630, 335, 78)]
        hx, hy = 910, 450
        T.append([top(150), (150, 80)])
        for j, c in enumerate(chain): S.append((c[0], c[1], c[2], 'pic', j, appear(j)))
        for a, b in zip(chain, chain[1:] + [(hx, hy, HR)]):
            T.append([(a[0] + a[2] * .72, a[1] + a[2] * .72), ((a[0] + b[0]) / 2 + 20, (a[1] + b[1]) / 2 - 12), (b[0] - b[2] * .72, b[1] - b[2] * .72)])
    elif name == 'compare':
        hx, hy = 470, 205
        cols = ['#94702a', '#5d6b8a', '#3f8f7a']
        T.append([top(hx), 'HERO']); T.append([top(810), (810, 205 - HR)])
        T.append([(hx, hy + HR), (470, 525 - HR)]); T.append([(810, 205 + HR), (810, 525 - HR)])
        for j, (x, y) in enumerate([(810, 205), (470, 525), (810, 525)]): S.append((x, y, HR, 'pic_col', (j, cols[j]), appear(j)))
    elif name == 'syzygy':
        al = ease((f - P['T_CHOSEN'] + 30) / 30)
        a, b = (lerp(330, 640, al), 118), (lerp(950, 640, al), 602)
        S.append((a[0], a[1], 92, 'pic', 0, 1)); S.append((b[0], b[1], 92, 'pic', 1, 1))
        T.append([top(a[0]), (a[0], a[1] - 92)])
        T.append([(a[0], a[1] + 92), 'HERO']); T.append([(hx, hy + HR), (b[0], b[1] - 92)])
    elif name == 'cast':
        T.append([top(hx), 'HERO'])
        I.append(lambda k: k.line([(hx + math.cos(t / 60 * 2 * math.pi) * 400, hy + math.sin(t / 60 * 2 * math.pi) * 262) for t in range(61)], 1.2, LO * .7))
        for j in range(6):
            t = f * .02 + j * math.pi / 3
            S.append((hx + math.cos(t) * 400, hy + math.sin(t) * 262, 36, 'pic', 'chosen', appear(j)))
    elif name == 'chemistry':
        hx, hy = 520, 380
        T.append([top(hx), 'HERO'])
        for j, (x, y, r) in enumerate([(880, 190, 82), (900, 570, 82)]):
            S.append((x, y, r, 'pic', j, appear(j)))
            ang = math.atan2(y - hy, x - hx); nx, ny = -math.sin(ang) * 7, math.cos(ang) * 7
            p0 = (hx + math.cos(ang) * (HR + 10), hy + math.sin(ang) * (HR + 10)); p1 = (x - math.cos(ang) * (r + 10), y - math.sin(ang) * (r + 10))
            k = ease(g * 3 - j * .5)
            for s_ in (-1, 1):
                I.append(lambda kk, s_=s_, p0=p0, p1=p1, nx=nx, ny=ny, k=k: kk.line([(p0[0] + s_ * nx, p0[1] + s_ * ny), (lerp(p0[0], p1[0], k) + s_ * nx, lerp(p0[1], p1[1], k) + s_ * ny)], 2.2, .85))
    elif name == 'odyssey':
        hx, hy = 920, 230
        for kk in range(6):
            I.append(lambda k, kk=kk: k.line([(x, 470 + kk * 36 + math.sin(x * .016 + f * .06 + kk) * 7) for x in range(0, 1281, 12)], 1.2, LO - kk * .04))
        r_ = random.Random(9); path = []; x, y = 60, 600
        for i in range(62):
            x += 12; y += math.sin(i * .35) * 14 - 4.6 + (r_.random() - .5) * 6; path.append((x, y))
        n = max(2, int(len(path) * g))
        T.append(path[:n] + ([(hx - HR * .72, hy + HR * .72)] if g >= 1 else []))
        S.append((path[n - 1][0], path[n - 1][1], 13, 'empty', 0, 1))
        T.append([top(hx), 'HERO'])
    elif name == 'republic':
        hx, hy = 470, 400
        arch = [(640 + math.cos(math.radians(a)) * 610, 770 + math.sin(math.radians(a)) * 720) for a in range(180, 361, 4)]
        I.append(lambda k: k.line(arch, 2.2, .8))
        S.append((900, 390, HR * 1.12, 'ghost', None, ease((f - 30) / 20)))
        T.append([top(hx), 'HERO'])
    # ---- the sign families
    elif name == 'perception':
        hx, hy = 760, 390; sx, sy = 240, 220
        S.append((sx, sy, 48, 'eyes', blinkC(f % 50, 30), 1, (1, .4)))
        T.append([top(sx), (sx, sy - 48)]); T.append([top(hx), 'HERO'])
        for t in (-1, 0, 1):
            I.append(lambda k, t=t: k.line([(sx + 54, sy + 18 + t * 10), (lerp(sx + 54, hx - HR - 10, g), lerp(sy + 18 + t * 10, hy + t * 60, g))], 1.2, LO))
    elif name == 'affect':
        hx, hy = 640, 380; T.append([top(hx), 'HERO'])
    elif name == 'action':
        hx = kv(f, [(0, 250), (P['T_CHOSEN'], 520)]); hy = 400
        T.append([(0, hy), (hx - HR, hy)]); T.append([top(hx), 'HERO'])
        S.append((1050, 400, 120, 'eyes', blinkC(f % 60, 40), 1, (-1, 0)))
        T.append([top(1050), (1050, 280)]); T.append([(hx + HR, hy), (930, hy)])
    elif name == 'reflection':
        hx, hy = 420, 360
        I.append(lambda k: k.line([(640, 80), (640, 640)], 1.2, LO))
        S.append((860, 360, HR, 'mirror', None, ease((f - 20) / 14)))
        T.append([top(hx), 'HERO']); T.append([top(860), (860, 360 - HR)])
    elif name == 'mental':
        hx, hy = 640, 250
        T.append([top(hx), 'HERO'])
        for j, (x, y) in enumerate([(330, 560), (950, 560)]):
            S.append((x, y, 82, 'pic', j, appear(j)))
            I.append(lambda k, x=x, y=y, j=j: k.line([(hx + (x - hx) * .32, hy + HR * .92), (x + (hx - x) * .2, y - 90)], 1.4, .7 * appear(j)))
        I.append(lambda k: k.line([(420, 560), (860, 560)], 1.4, .7 * appear(2)))
    elif name == 'time':
        hx, hy = 600, 380; a = f * .012 + seed
        I.append(lambda k: k.ringline(hx + math.cos(a) * 70, hy + math.sin(a) * 40, HR + 70, .55, 2))
        I.append(lambda k: k.ringline(hx - math.cos(a) * 40, hy - math.sin(a) * 30, HR + 150, .28, 1.5))
        T.append([top(hx), 'HERO'])
    elif name == 'break':
        hx, hy = 640, 400
        T.append([top(hx), (hx, 130)]); T.append([(hx + 8, 158), 'HERO'])
    elif name == 'read':
        hx, hy = 880, 360
        T.append([top(hx), 'HERO'])
        I.append(lambda k: k.rect(90, 100, 360, 520, .5))
        for i in range(10):
            y = 140 + i * 48; w = 280 - (i * 47) % 130; k = ease(g * 3 - i * .2)
            I.append(lambda kk, y=y, w=w, k=k: kk.bar(120, y - 3, w * k, 6, .5))
    else:
        T.append([top(hx), 'HERO'])
    return dict(hero=(hx, hy, HR), sats=S, threads=T, ink=I)

# ---------------------------------------------------------------- one ident
def wrap(text, fnt, width):
    lines, cur = [], ''
    for w_ in text.split():
        t = (cur + ' ' + w_).strip()
        if fnt.getlength(t) <= width: cur = t
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

DOMC = {k: hexc(v) for k, v in dict(perception='#b0952f', affect='#c0674a', action='#c06a32', reflection='#6e9445',
                                      mental='#4f8f8f', time='#6b63b0', read='#a0648f').items()}
DOMC['break'] = hexc('#8a8274')

def render(spec, out_mp4, poster):
    A = hexc(spec['accent']); tone = toner(A); name = spec['figure']; HR = FIG_R[name]
    RA = HR - sw(HR) / 2 - 1; size = int(RA * 2 * SS)
    clips = []
    for j, src in enumerate(spec['clips']):
        n = HOLD if j == len(spec['clips']) - 1 else spec['rhythm'][min(j, len(spec['rhythm']) - 1)]
        fr = frames_of(src, n, size)
        if fr: clips.append(fr)
    if len(clips) < 3: print('  too few clips', spec['title']); return 0
    *blinks, chosen = clips
    stills = [Image.fromarray(tone(fr[len(fr) // 2])) for fr in clips]
    durs = [len(b) for b in blinks]
    T_OPEN = 34; t_cuts = T_OPEN + 8
    cut_at = [t_cuts + sum(durs[:i]) for i in range(len(durs))]
    T_CHOSEN = t_cuts + sum(durs); T_IRIS = T_CHOSEN + HOLD; T_WINK = T_IRIS + 10
    T_TITLE = T_WINK + 30; T_END = T_TITLE + 72
    F = dict(mono=font('IBMPlexMono-Regular.ttf', 13), mono_s=font('IBMPlexMono-Regular.ttf', 11), title=font('CormorantGaramond.ttf', 58),
             ital=font('CormorantGaramond-Italic.ttf', 25), corner=font('CormorantGaramond.ttf', 84))
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out_mp4], stdin=subprocess.PIPE)
    thumbs = [s.resize((44 * SS, 44 * SS), Image.LANCZOS) for s in stills]
    other_tone = {}
    def live(f, ci):
        if T_CHOSEN <= f < T_IRIS: return chosen[min(f - T_CHOSEN, HOLD - 1)]
        if t_cuts <= f < T_CHOSEN: return blinks[ci][min(f - cut_at[ci], durs[ci] - 1)]
        return None
    for f in range(T_END):
        im = Image.new('RGB', (W * SS, H * SS), PAPER)
        ci = max(0, sum(1 for c in cut_at if f >= c) - 1)
        P = dict(grow=min(1, f / (T_CHOSEN * .75)), chosen=f >= T_CHOSEN, win_k=ease((f - T_CHOSEN) / 20) if f >= T_CHOSEN else 0,
                 cut_i=ci, seed=spec.get('seed', 0), T_CHOSEN=T_CHOSEN)
        fig = figure(name, f, P)
        hx, hy, _ = fig['hero']
        if f < 19: hy += kv(f, [(0, -hy - HR - 40), (12, 16), (15, -8), (19, 0)])
        out = ease((f - T_TITLE) / 10) if f >= T_TITLE else 0.0
        k = K(im, 1 - out)
        hr = HR
        if f >= T_TITLE:
            t = ease((f - T_TITLE) / 16); hx, hy, hr = lerp(hx, 260, t), lerp(hy, 360, t), lerp(HR, 88, t)
        for fn in fig['ink']: fn(k)
        for t in fig['threads']:
            pts = [(hx, hy - hr) if p == 'HERO' else p for p in t]
            k.thread(pts)
        if f >= T_TITLE: K(im).thread([top(hx), (hx, hy - hr)])
        for s in fig['sats']:
            x, y, r, kind, arg, a = s[:6]
            if a <= 0.01 or k.al <= 0.01: continue
            rr = r * (.6 + .4 * a)
            k.fill(x, y, rr, mix(PAPER, PAPER, 0))
            if kind == 'pic':
                img = stills[-1] if arg == 'chosen' else stills[arg % (len(stills) - 1)]
                k.pic(img, x, y, rr - sw(rr) / 2, a)
            elif kind == 'pic_col':
                j, col = arg
                if col not in other_tone: other_tone[col] = Image.fromarray(toner(hexc(col))(np.array(stills[j].convert('L'))))
                k.pic(other_tone[col], x, y, rr - sw(rr) / 2, a)
            elif kind == 'eyes':
                k.eyes(x, y, rr, arg, arg, look=s[6] if len(s) > 6 else (0, 0), a=a)
            elif kind == 'dom':
                k.fill(x, y, rr, mix(PAPER, DOMC[arg], .85 * a * k.al)); k.ringline(x, y, rr, a, 2.2); continue
            elif kind == 'ghost':
                src = live(f, ci)
                if src is not None:
                    gimg = Image.fromarray(tone(src)).filter(ImageFilter.GaussianBlur(12))
                    k.pic(Image.blend(Image.new('RGB', gimg.size, mix(PAPER, INK, .6)), gimg, .4), x, y, rr, a * .9)
                else: k.fill(x, y, rr, mix(PAPER, INK, .2 * a * k.al))
                continue
            elif kind == 'mirror':
                src = live(f, ci)
                if src is not None: k.pic(Image.fromarray(tone(src)).transpose(Image.FLIP_LEFT_RIGHT), x, y, rr - sw(rr) / 2, a * .5)
                else: k.eyes(x, y, rr, blinkC(f, 26), blinkC(f, 26), look=(-1, 0), a=a * .5)
                k.ringline(x, y, rr, a * .5); continue
            k.ringline(x, y, rr, a)
        hk = K(im, 1.0)
        hk.fill(hx, hy, hr, PAPER)
        if T_OPEN <= f < T_IRIS:
            if f < T_CHOSEN:
                if f < t_cuts: i, local, q = 0, 0, ease((f - T_OPEN) / 8)
                else:
                    i = ci; local = f - cut_at[i]; q = 1.0; to_next = durs[i] - local
                    if to_next == 2: q = .55
                    if to_next == 1: q = 0
                    if i > 0 and local == 0: q = 0
                    if i > 0 and local == 1: q = .5
                img, w = blinks[i][min(local, durs[i] - 1)], 0.0
            else:
                kk = f - T_CHOSEN; q = .5 if kk == 0 else 1.0; img = chosen[min(kk, HOLD - 1)]; w = winkC(kk, 14, 6, 12, 7) * .86
            if q > .01: im.paste(Image.fromarray(tone(img)), (int((hx - RA) * SS), int((hy - RA) * SS)), eye_mask(size, q, w))
        if T_IRIS <= f < T_IRIS + 6:
            rr = RA * (1 - ease((f - T_IRIS) / 6))
            if rr > 2: hk.pic(Image.fromarray(tone(chosen[-1])), hx, hy, rr)
        if name == 'break' and f < T_TITLE:
            wpx = round(sw(hr) * SS)
            hk.d.arc([(hx - hr) * SS, (hy - hr) * SS, (hx + hr) * SS, (hy + hr) * SS], -76, 232, fill=INK, width=wpx)
            hk.d.arc([(hx - hr + 10) * SS, (hy - hr - 8) * SS, (hx + hr + 10) * SS, (hy + hr - 8) * SS], 242, 278, fill=INK, width=wpx)
        else: hk.ringline(hx, hy, hr)
        l = r = 0.0; rc = 0.0; look = (0, 0); show = True
        if f < T_OPEN:
            look = (kv(f, [(20, 0), (24, -1), (27, -1), (30, 1), (33, 1)]), 0); l = r = blinkC(f, 26)
        elif f < T_IRIS + 6: show = False
        else:
            l = r = 1 - ease((f - T_IRIS - 6) / 6); r = max(r, winkC(f, T_WINK, 6, 14, 7)); rc = .9 if f >= T_WINK else 0; look = (0, .12)
        if show: hk.eyes(hx, hy, hr, l, r, rc, look)
        ca = ease(f / 12); d = hk.d
        d.text((52 * SS, 30 * SS), spec['corner'], font=F['corner'], fill=mix(PAPER, INK, ca))
        d.text((56 * SS, 128 * SS), spec['corner_sub'], font=F['mono_s'], fill=mix(PAPER, MUTE, ca))
        if f >= T_TITLE + 8:
            a = ease((f - T_TITLE - 8) / 14); col = lambda c: mix(PAPER, c, a); x0 = 420 * SS
            d.text((x0, 262 * SS), spec['eyebrow'], font=F['mono'], fill=col(MUTE))
            d.text((x0, 282 * SS), spec['title'], font=F['title'], fill=col(INK))
            yy = 362
            for ln_ in wrap(spec['line'], F['ital'], 760 * SS)[:2]:
                d.text((x0, yy * SS), ln_, font=F['ital'], fill=col(INK)); yy += 31
            yy += 12; cy_t = yy * SS + thumbs[0].size[1] // 2
            d.line([(x0 - 30 * SS, cy_t), (x0 + (len(thumbs) - 1) * 54 * SS + thumbs[0].size[0] + 30 * SS, cy_t)], fill=col(RED), width=SS)
            for j, th in enumerate(thumbs):
                tx = x0 + j * 54 * SS
                im.paste(th, (tx, yy * SS), disc(th.size[0], int(255 * a)))
                d.ellipse([tx, yy * SS, tx + th.size[0], yy * SS + th.size[1]], outline=col(INK), width=(3 if j == len(thumbs) - 1 else 1) * SS)
            d.text((x0, (yy + 60) * SS), spec['foot'], font=F['mono_s'], fill=col(MUTE))
        fr = im.resize((W, H), Image.LANCZOS)
        if f == T_CHOSEN + 8: fr.save(poster, quality=88)
        if f == T_END - 1: fr.save(poster.replace('.jpg', '-card.jpg'), quality=88)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait()
    return T_END

# ---------------------------------------------------------------- the two sets
FILM_STYLE = {  # href: (colour, figure, frames for each of the five blinked shots)
    'machines.html': ('#6a4fa0', 'machines', [14, 14, 14, 14, 14]),
    'episode-1.html': ('#4f8a2a', 'archive', [16, 13, 17, 12, 15]),
    'lesson-4.html': ('#1f8aa6', 'voice', [12, 19, 10, 21, 14]),
    'lesson-7.html': ('#b07a1a', 'asking', [15, 15, 15, 15, 15]),
    'lesson-8.html': ('#7d9a14', 'choosing', [9, 9, 9, 9, 9]),
    'room-syntagma.html': ('#7a5a44', 'syntagma', [18, 10, 18, 10, 18]),
    'episode-5.html': ('#a8456c', 'poem', [16, 16, 16, 16, 16]),
    'wygwyl-take.html?t=suite': ('#3d6fb0', 'suite', [12, 12, 24, 12, 12]),
    'wygwyl-take.html?t=scenes': ('#94702a', 'scenes', [20, 20, 20, 20, 20]),
    'wygwyl-take.html?t=cineosis': ('#5d6b8a', 'cineosis', [13, 13, 13, 13, 13]),
    'wygwyl-take.html?t=drift': ('#3f8f7a', 'drift', [16, 18, 20, 22, 24]),
    'episode-5.html?part=compare': ('#3d6fb0', 'compare', [12, 12, 12, 12, 12]),
    'room-syzygy.html': ('#b8860b', 'syzygy', [15, 15, 15, 15, 15]),
    'room-cast.html': ('#a0522d', 'cast', [14, 14, 14, 14, 14]),
    'room-chemistry.html': ('#8a3f8f', 'chemistry', [11, 17, 11, 17, 11]),
    'episode-4.html': ('#3b55c4', 'odyssey', [18, 18, 18, 18, 18]),
    'episode-7.html': ('#b36a1c', 'republic', [16, 16, 16, 16, 16]),
}
FIG_NOTE = {'machines': 'one eye ringed by nine machines', 'archive': 'the thread branches like a search',
            'voice': 'the thread is the voice', 'asking': 'the thread curls into a question', 'choosing': 'three Os racing on their lanes',
            'syntagma': 'shots strung together by different joins', 'poem': "the poem's lines threaded to one O",
            'suite': 'an O on a stave, among notes', 'scenes': 'a small O answered by a big one', 'cineosis': 'an O set into the table of signs',
            'drift': 'a chain of Os, each knowing only the last', 'compare': 'four Os, four takes', 'syzygy': 'three Os sliding into line',
            'cast': 'the same shot coming round again', 'chemistry': 'an O bonded to two others', 'odyssey': 'a long voyage thread across the sea',
            'republic': 'an O and its shadow on the cave wall', 'perception': 'a small O watching a large one', 'affect': 'one O, as close as a face',
            'action': 'an O moving along its line toward another', 'reflection': 'an O and its mirror', 'mental': 'three Os held in relation',
            'time': 'an O inside turning rings of time', 'break': 'a broken O on a snapped thread', 'read': 'an O beside a page'}

def film_specs():
    out = []
    for p in json.load(open(os.path.join(HERE, 'plan.json'))):
        acc, fig, rh = FILM_STYLE[p['href']]
        out.append(dict(kind='film', key=f"film-{p['i']:02d}", i=p['i'], clips=p['clips'], accent=acc, figure=fig, rhythm=rh,
                        corner=p['n'], corner_sub=p['unit'].upper(), title=p['t'], eyebrow=f"CINEOSIS LAB  ·  {p['unit'].upper()}  ·  {p['n']}",
                        line='makes visible ' + p['v'], fig_note=FIG_NOTE[fig], foot='5 BLINKED  ·  1 WINKED'))
    return out

def sign_specs():
    picks = json.load(open(os.path.join(C44, 'picks.json')))
    signs = json.load(open(os.path.join(LAB, 'lab-data.json')))['signs']
    order = sorted(picks, key=lambda k: (int(''.join(c for c in k if c.isdigit())), k))
    out = []
    for idx, n in enumerate(order):
        s = next(x for x in signs if x['n'] == n); pk = picks[n]
        clips = ['clips/' + u + '.mp4' for u, _ in pk][:6]
        rh = [[14, 14, 14, 14, 14], [11, 16, 11, 16, 11], [18, 12, 18, 12, 18], [13, 13, 20, 13, 13]][idx % 4]
        out.append(dict(kind='sign', key=f"sign-{n}", n=n, clips=clips, accent='#%02x%02x%02x' % DOMC[s['dom']],
                        dom=s['dom'], figure=s['dom'], seed=idx * 7 + 3, rhythm=rh, symbol=s['symbol'], title=s['name'],
                        corner=s['symbol'], corner_sub=f"SIGN {n}", eyebrow=f"CINEOSIS SIGN {n}  ·  {s['symbol']}  ·  {s['image'].upper()}",
                        fig_note=FIG_NOTE[s['dom']], line=s['gloss'][0].upper() + s['gloss'][1:] + '. ' + s.get('question', ''),
                        foot='5 BLINKED  ·  1 WINKED', notes=[c for _, c in pk[:len(clips)]], gloss=s['gloss'], question=s.get('question', '')))
    return out

if __name__ == '__main__':
    kind = sys.argv[1] if len(sys.argv) > 1 else 'films'
    want = set(sys.argv[2:])
    for sp in (film_specs() if kind == 'films' else sign_specs()):
        if want and str(sp.get('i', sp.get('n'))) not in want: continue
        n = render(sp, os.path.join(HERE, sp['key'] + '.mp4'), os.path.join(HERE, sp['key'] + '.jpg'))
        print(sp['key'], sp['title'], n, flush=True)
