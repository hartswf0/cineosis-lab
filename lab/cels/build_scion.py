#!/usr/bin/env python3
"""THE CELS AS A MULTIPLANE & EXPOSURE STATE GRAPH (after the SCION multiplane animation prompt), measured from what the cels are:
footage redrawn as cels (a drawing every 3 s and at every cut, EbSynth between, 12 frames a second). For every shot of the Cels cut:
  multiplane stack   wygwyl-world-arch's seven planes for the shot's first drawing (P0 lens mask … P6 sky), each with its median depth,
                     its depth relative to the character plane (Z, P2 = 1) and its parallax coefficient
  x-sheet            one row per frame (12 fps = on twos at 24): which drawing it is (a drawn key, or EbSynth between), the character
                     plane's area, centre and lowest point (from SAM 3's people mask), the camera vector (the background's own motion),
                     the character's motion with the camera taken out, in the cel and in its footage, and contact
  motion keys        where the footage's own performance has its extremes: the character slows to a stop or turns (keys) and moves
                     fastest between (breakdowns); and how many of them our drawings, made on a clock, actually land on
  the five gates     G1 silhouette: does each drawn key read as a black shape (contrast with its ground, negative space)
                     G2 volume: does the drawing boil (change inside the figure that its own motion does not explain), against the footage
                     G3 contact: does a planted lowest point slide, beyond what the footage does
                     G4 arcs: does the drawing's motion zigzag more than the footage's, and does it follow it
                     G5 vitality: is the cel as alive as its footage, the rough (motion energy, silhouette punch), and the first way or the
                        second the peak checkpoint
Writes cels/scion/<shot>.json, cels/scion/<shot>.jpg (every frame, 240×135, an atlas 16 across) and cels/scion/index.json.
Run from lab/ with wygwyl-world-arch's venv:  …/.venv-shots/bin/python cels/build_scion.py [P01-002 …]"""
import os, re, sys, json, glob, subprocess, numpy as np, cv2

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, 'cels', 'scion'); os.makedirs(OUT, exist_ok=True)
VD = '/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH/shots/video'; DECK = os.path.join(LAB, 'wygwyl', 'cuts', 'cels', 'mix.mp4')
W, H, FW, FH, FPS = 480, 270, 240, 135, 12
PLANE_Z = {'P0': .2, 'P1': .5, 'P2': 1.0, 'P3': 1.2, 'P4': 2.5, 'P5': 6.0, 'P6': None}     # the prompt's nominal stack

def read(fs, w=W, h=H): return [cv2.resize(cv2.imread(f), (w, h), interpolation=cv2.INTER_AREA) for f in fs]
def deck(t, n):
    """the deck from t for n frames: picture (480×270) and the people / ground masks (bool, 480×270)"""
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{max(0, t):.3f}', '-i', DECK, '-frames:v', str(n), '-vf', f'fps={FPS},scale=480:540', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    D = np.frombuffer(r.stdout, np.uint8).reshape(-1, 540, 480, 3)
    pic = D[:, :270]; low = D[:, 270:, :, 0]
    up = lambda q: np.stack([cv2.resize(x, (W, H), interpolation=cv2.INTER_LINEAR) > 128 for x in q])
    return pic, up(low[:, :135, :240]), up(low[:, 135:, 240:])
def offset(cel, t0):
    """the deck's time for this shot's first frame: the placement of each poem in the suite moves shots by up to half a second"""
    n = len(cel); mid = n // 2; best = (0.0, 1e9)
    pic, _, _ = deck(t0 - 1.0 + mid / FPS, 25)
    for k in range(len(pic)):
        e = float(np.abs(pic[k].astype(np.float32) - cel[mid]).mean())
        if e < best[1]: best = (-1.0 + k / FPS, e)
    return best
flow = lambda a, b: cv2.resize(cv2.calcOpticalFlowFarneback(cv2.resize(a, (FW, FH)), cv2.resize(b, (FW, FH)), None, .5, 3, 13, 3, 5, 1.1, 0), (W, H)) * (W / FW)

def multiplane(pid):
    k = sorted(glob.glob(f'{VD}/{pid}/out/*/multiplane/multiplane.json'))
    if not k: return None
    m = json.load(open(k[0])); z2 = next((p['z_median_m'] for p in m['planes'] if p['id'] == 'P2' and p.get('z_median_m')), None)
    return {'camera': m.get('camera'), 'silhouette': m.get('silhouette'), 'planes': [{'id': p['id'], 'name': p['name'], 'area': p['area_frac'], 'z_m': p.get('z_median_m'),
            'Z': round(p['z_median_m'] / z2, 2) if z2 and p.get('z_median_m') else PLANE_Z.get(p['id']), 'parallax': p.get('parallax'), 'contents': p.get('contents', [])[:6],
            'motion': p.get('motion', [])[:2]} for p in m['planes']]}

def run(p):
    pid = p['id']; cf = sorted(glob.glob(f'{VD}/{pid}/cel_v2/*.png')); sf = sorted(glob.glob(f'{VD}/{pid}/frames/*.png'))
    if not cf or not sf: return None
    n = min(len(cf), len(sf)); cel = read(cf[:n]); src = read(sf[:n])
    off, err = offset(cel, p['t0']); _, PM, GM = deck(p['t0'] + off, n)
    if len(PM) < n: PM = np.concatenate([PM, np.repeat(PM[-1:], n - len(PM), 0)]); GM = np.concatenate([GM, np.repeat(GM[-1:], n - len(GM), 0)])
    v1f = sorted(glob.glob(f'{VD}/{pid}/cel_frames/*.png'))[:n]; v1 = read(v1f) if len(v1f) == n else None
    keys = sorted({int(re.search(r'kf(\d+)', d).group(1)) for d in glob.glob(f'{VD}/{pid}/v2/*kf*')})
    gray = lambda X: [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) for x in X]
    Gc, Gs = gray(cel), gray(src); Gv = gray(v1) if v1 else None
    rows, ke_c, ke_s, ke_v, boil_c, boil_s, boil_v, vel_c, vel_s = [], [], [], [], [], [], [], [], []
    for i in range(n):
        m = PM[i]; a = float(m.mean()); ys, xs = np.nonzero(m)
        row = {'f': i, 'f24': 2 * i, 'ex': 2, 'drawing': f'K{keys.index(i) + 1:02d}' if i in keys else 'eb', 'area': round(a, 4)}
        if a > .004:
            row.update(cx=round(float(xs.mean()) / W, 3), cy=round(float(ys.mean()) / H, 3), top=[round(float(xs[ys.argmin()]) / W, 3), round(float(ys.min()) / H, 3)],
                       foot=[round(float(xs[ys.argmax()]) / W, 3), round(float(ys.max()) / H, 3)])
        if i:
            fs_ = flow(Gs[i - 1], Gs[i]); fc = flow(Gc[i - 1], Gc[i]); bg = ~PM[i] & ~PM[i - 1]
            cam = np.median(fs_[bg], 0) if bg.sum() > 500 else np.zeros(2)
            row['cam'] = [round(float(cam[0]), 2), round(float(cam[1]), 2)]
            def warp_res(G, f):                    # what changed inside the figure that its own motion does not explain
                gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
                w = cv2.remap(G[i - 1], gx - f[..., 0], gy - f[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                return float(np.abs(w.astype(np.float32) - G[i].astype(np.float32))[m].mean()) if m.sum() > 200 else None
            if m.sum() > 200:
                vc = np.median(fc[m], 0) - cam; vs = np.median(fs_[m], 0) - cam
                ke_c.append(float(np.linalg.norm(fc[m] - cam, axis=1).mean())); ke_s.append(float(np.linalg.norm(fs_[m] - cam, axis=1).mean()))
                vel_c.append(vc); vel_s.append(vs); row['v_cel'] = [round(float(vc[0]), 2), round(float(vc[1]), 2)]; row['v_src'] = [round(float(vs[0]), 2), round(float(vs[1]), 2)]
                boil_c.append(warp_res(Gc, fs_)); boil_s.append(warp_res(Gs, fs_))
                if Gv: boil_v.append(warp_res(Gv, fs_)); ke_v.append(float(np.linalg.norm(flow(Gv[i - 1], Gv[i])[m] - cam, axis=1).mean()))
        rows.append(row)
    # contact: a lowest point inside the frame that stops moving vertically for 4+ frames
    pins, slide_c = [], []
    feet = [(r['f'], r['foot']) for r in rows if 'foot' in r and r['foot'][1] < .985]
    run_ = []
    for k in range(1, len(feet)):
        (f0, a0), (f1, a1) = feet[k - 1], feet[k]
        if f1 == f0 + 1 and abs(a1[1] - a0[1]) * H < .6: run_.append((f1, (a1[0] - a0[0]) * W - rows[f1].get('cam', [0, 0])[0]))
        else:
            if len(run_) >= 4: pins.append(run_)
            run_ = []
    if len(run_) >= 4: pins.append(run_)
    for r_ in pins:
        for f, sl in r_: rows[f]['pin'] = True; slide_c.append(abs(sl))
    # motion keys from the footage: the character slows to a stop or turns (keys); fastest between (breakdowns)
    sp = np.array([np.linalg.norm(v) for v in vel_s]) if vel_s else np.array([])
    mkeys, mbreaks = [], []
    if len(sp) > 6:
        s = np.convolve(sp, np.ones(3) / 3, 'same'); ang = [np.degrees(np.arctan2(v[1], v[0])) for v in vel_s]
        for k in range(1, len(s) - 1):
            turn = abs(((ang[k] - ang[k - 1]) + 180) % 360 - 180) > 60 and s[k] > .8
            if (s[k] < s[k - 1] and s[k] <= s[k + 1] and s[k] < .6 * max(s.max(), 1e-6)) or turn: mkeys.append(k + 1)
        mkeys = [k for i, k in enumerate(mkeys) if not i or k - mkeys[i - 1] > 3]
        for a_, b_ in zip(mkeys, mkeys[1:]):
            if b_ - a_ > 3: mbreaks.append(int(a_ + np.argmax(s[a_:b_ - 1])))
    for k in mkeys: rows[k]['motion_key'] = 'K'
    for k in mbreaks: rows[k]['motion_key'] = 'B'
    coverage = round(float(np.mean([min(abs(k - d) for d in keys) <= 3 for k in mkeys])), 2) if mkeys and keys else None
    # the gates
    lab = lambda bgr: cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32) / 255
    g1 = []
    for k in keys:
        if k >= n: continue
        m = PM[k]
        if m.mean() < .004: g1.append({'key': k, 'figure': False}); continue
        ring = cv2.dilate(m.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~m; L = lab(cel[k])
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea)
        hull = cv2.convexHull(c, returnPoints=False); notches = 0
        try:
            d = cv2.convexityDefects(c, hull); notches = int((d.reshape(-1, 4)[:, 3] / 256 > 8).sum()) if d is not None else 0
        except cv2.error: pass
        solidity = cv2.contourArea(c) / max(cv2.contourArea(cv2.convexHull(c)), 1)
        contrast = abs(float(np.median(L[m]) - np.median(L[ring]))) if ring.any() else 0
        cv2.imwrite(f'{OUT}/{pid}_K{keys.index(k) + 1:02d}.png', np.where(m, 0, 255).astype(np.uint8)[::2, ::2])
        g1.append({'key': k, 'figure': True, 'contrast': round(contrast, 3), 'solidity': round(float(solidity), 3), 'notches': notches,
                   'pass': bool(contrast >= .12 and (solidity <= .88 or notches >= 2))})
    nz = lambda X: [x for x in X if x is not None]
    bc, bs, bv = np.mean(nz(boil_c)) if nz(boil_c) else None, np.mean(nz(boil_s)) if nz(boil_s) else None, np.mean(nz(boil_v)) if nz(boil_v) else None
    def reversals(V):
        if len(V) < 4: return 0
        A = np.diff(np.array(V), axis=0); c = 0
        for k in range(1, len(A)):
            if np.linalg.norm(A[k]) > .4 and np.linalg.norm(A[k - 1]) > .4 and np.dot(A[k], A[k - 1]) < 0: c += 1
        return c / (len(V) / FPS)
    rc, rs = reversals(vel_c), reversals(vel_s)
    follow = float(np.corrcoef(np.array(vel_c).ravel(), np.array(vel_s).ravel())[0, 1]) if len(vel_c) > 4 and np.std(vel_s) > 1e-3 else None
    kc, ks, kv = (float(np.mean(x)) if x else None for x in (ke_c, ke_s, ke_v))
    G = {
      'G1': {'name': 'silhouette', 'keys': g1, 'pass': all(k['pass'] for k in g1 if k['figure']) if any(k['figure'] for k in g1) else None},
      'G2': {'name': 'volume', 'boil_cel': round(bc, 2) if bc is not None else None, 'boil_footage': round(bs, 2) if bs is not None else None, 'boil_first_way': round(bv, 2) if bv is not None else None,
             'ratio': round(bc / max(bs, .5), 2) if bc is not None and bs is not None else None},
      'G3': {'name': 'contact', 'pins': len(pins), 'pinned_frames': sum(len(r_) for r_ in pins), 'slide_px_per_frame': round(float(np.median(slide_c)), 2) if slide_c else None},
      'G4': {'name': 'arcs', 'reversals_per_s_cel': round(rc, 2), 'reversals_per_s_footage': round(rs, 2), 'follows_footage': round(follow, 2) if follow is not None else None},
      'G5': {'name': 'vitality', 'energy_cel': round(kc, 2) if kc else None, 'energy_footage': round(ks, 2) if ks else None, 'energy_first_way': round(kv, 2) if kv else None,
             'ratio': round(kc / ks, 2) if kc and ks else None}}
    G['G2']['pass'] = None if G['G2']['ratio'] is None else bool(G['G2']['ratio'] <= 1.5)
    G['G3']['pass'] = None if not slide_c else bool(G['G3']['slide_px_per_frame'] <= 1.5)
    moving = bool(ks and ks >= .3)                            # under .3 px a frame the footage holds: arcs and vitality are noise
    G['G4']['held'] = G['G5']['held'] = not moving
    G['G4']['pass'] = None if not vel_c or not moving else bool(not (rc > 1 and rc > 1.5 * max(rs, .3)) and (follow is None or follow >= .5))
    G['G5']['pass'] = None if not (kc and ks) or not moving else bool(.7 <= kc / ks <= 1.6)
    peak = None
    if kv and kc and ks and bv is not None and bc is not None:
        sc2 = -abs(np.log(kc / ks)) - max(0, bc / max(bs, .5) - 1); sc1 = -abs(np.log(kv / ks)) - max(0, bv / max(bs, .5) - 1); peak = 'second way' if sc2 >= sc1 else 'first way'
    G['G5']['peak_checkpoint'] = peak
    # the atlas: every cel frame, 240×135, 16 across
    cols = 16; rws = (n + cols - 1) // cols; A = np.zeros((rws * FH, cols * FW, 3), np.uint8)
    for i in range(n): A[(i // cols) * FH:(i // cols + 1) * FH, (i % cols) * FW:(i % cols + 1) * FW] = cv2.resize(cel[i], (FW, FH), interpolation=cv2.INTER_AREA)
    cv2.imwrite(f'{OUT}/{pid}.jpg', A, [cv2.IMWRITE_JPEG_QUALITY, 72])
    rec = {'id': pid, 'poem': p['poem'], 't0': p['t0'], 't1': p['t1'], 'scene': p.get('scene'), 'name': p.get('name'), 'what': p.get('what'), 'line': p.get('line'), 'title': p.get('title'), 'year': p.get('year'),
           'frames': n, 'fps': FPS, 'deck_offset': round(off, 3), 'deck_match': round(err, 1), 'drawn_keys': keys, 'motion_keys': mkeys, 'breakdowns': mbreaks, 'key_coverage': coverage,
           'multiplane': multiplane(pid), 'gates': G, 'xsheet': rows, 'atlas': {'file': f'cels/scion/{pid}.jpg', 'cols': cols, 'w': FW, 'h': FH}}
    json.dump(rec, open(f'{OUT}/{pid}.json', 'w'), default=float); return rec

if __name__ == '__main__':
    C = [p for p in json.load(open(os.path.join(LAB, 'cels', 'cels.json')))['patches'] if p['status'] == 'drawn']
    want = [a for a in sys.argv[1:] if not a.startswith('-')]
    idx = []
    for p in C:
        if want and p['id'] not in want: continue
        r = run(p)
        if not r: continue
        g = r['gates']; idx.append({'id': r['id'], 'poem': r['poem'], 't0': r['t0'], 't1': r['t1'], 'name': r['name'], 'frames': r['frames'], 'key_coverage': r['key_coverage'],
                                    'drawn': len(r['drawn_keys']), 'motion_keys': len(r['motion_keys']), 'gates': {k: v['pass'] for k, v in g.items()},
                                    'g': {'boil': g['G2']['ratio'], 'slide': g['G3']['slide_px_per_frame'], 'rev': g['G4']['reversals_per_s_cel'], 'follow': g['G4']['follows_footage'], 'vital': g['G5']['ratio'], 'peak': g['G5']['peak_checkpoint']}})
        print(r['id'], {k: v['pass'] for k, v in g.items()}, 'keys', len(r['drawn_keys']), 'motion keys', len(r['motion_keys']), 'coverage', r['key_coverage'], flush=True)
    if not want: json.dump({'about': 'the Cels cut as a multiplane & exposure state graph, with the five gates (cels/build_scion.py)', 'shots': idx}, open(f'{OUT}/index.json', 'w'))
