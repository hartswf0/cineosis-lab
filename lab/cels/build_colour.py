#!/usr/bin/env python3
"""COLOUR AND LEGIBILITY OF EVERY CEL: each patch of both cel cuts (Cels, Spine-Cut Cels) measured the same way as the footage it
was drawn from and as wygwyl-world-arch's own cels (the reference), and set against the palettes we have: the twelve districts'
measured body and glow palettes (city_data.js). In OKLab, the space where equal distances look equally different.
  value       L mean, the 5th–95th percentile range, crushed blacks (L < .2), clipped whites; the notan (the frame split into a light
              and a dark mass, Otsu): how far apart the two masses are, and how big the light one is
  colour      chroma mean and 90th percentile, colourfulness (Hasler & Süsstrunk), a 12-bin hue histogram, six dominant colours
  texture     edge density, flat share (no gradient), regions (connected flats after snapping to the six colours), mean region size
  legibility  figure against ground: SAM 3 finds the people ("person"); their difference from what is around them in L and in ΔE;
              structure kept: edge F of the cel against its footage; and one score, 0–100
  palettes    the nearest district palette, and the distance to it (a palette distance: each colour to its nearest in the other,
              weighted by share, both ways)
  the fix     for each patch, the grade that would make it legible, the reference's own rules: stretch the value range, lift what is
              crushed, and where a figure merges with its ground, flip it toward the opposite of its surround (notan); chroma to a
              floor. Before/after stills for the weakest.
Writes cels/colour/analysis.json and cels/colour/{thumbs,fix}/*.jpg. Run from lab/ with wygwyl-world-arch's venv:
  HF_HUB_OFFLINE=1 …/.venv-shots/bin/python cels/build_colour.py"""
import os, re, sys, json, glob, numpy as np, cv2, torch
from PIL import Image

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, 'cels', 'colour')
for d in ('thumbs', 'fix'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
VD = '/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH/shots/video'; REF = '/Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots'
W = 320

# ---------- OKLab ----------
def oklab(bgr):
    c = bgr[..., ::-1].astype(np.float32) / 255; c = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
    M1 = np.array([[.4122214708, .5363325363, .0514459929], [.2119034982, .6806995451, .1073969566], [.0883024619, .2817188376, .6299787005]], np.float32)
    M2 = np.array([[.2104542553, .7936177850, -.0040720468], [1.9779984951, -2.4285922050, .4505937099], [.0259040371, .7827717662, -.8086757660]], np.float32)
    return np.cbrt(c @ M1.T) @ M2.T
def from_oklab(lab):
    M2i = np.array([[1, .3963377774, .2158037573], [1, -.1055613458, -.0638541728], [1, -.0894841775, -1.2914855480]], np.float32)
    M1i = np.array([[4.0767416621, -3.3077115913, .2309699292], [-1.2684380046, 2.6097574011, -.3413193965], [-.0041960863, -.7034186147, 1.7076147010]], np.float32)
    c = np.clip((lab @ M2i.T) ** 3 @ M1i.T, 0, 1); c = np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)
    return (np.clip(c, 0, 1)[..., ::-1] * 255).astype(np.uint8)
hexlab = lambda h: oklab(np.array([[[int(h[5:7], 16), int(h[3:5], 16), int(h[1:3], 16)]]], np.uint8))[0, 0]

def palette(lab, k=6):
    """six dominant colours (OKLab k-means) and their shares, dark to light"""
    X = lab.reshape(-1, 3)[::3].astype(np.float32)
    _, lb, C = cv2.kmeans(X, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1e-3), 3, cv2.KMEANS_PP_CENTERS)
    sh = np.bincount(lb.ravel(), minlength=k) / len(lb); o = np.argsort(C[:, 0]); return C[o], sh[o]
def paldist(A, a, B, b):
    """palette distance: each colour to its nearest in the other (ΔE OK ×100), weighted by share, both ways"""
    D = np.linalg.norm(A[:, None] - B[None], axis=-1) * 100
    return float((D.min(1) * a).sum() / a.sum() + (D.min(0) * b).sum() / b.sum()) / 2

# ---------- the palettes we have ----------
city = json.loads(re.sub(r'^window\.CITY\s*=\s*', '', open(f'{REF}/city_data.js').read().strip().rstrip(';')))
DISTRICTS = []
for d in city['districts']:
    cols = d['body'] + d['glow']; g = d.get('glow_share', .05)
    DISTRICTS.append({'id': d['id'], 'name': d['name'], 'colors': cols, 'lab': np.array([hexlab(h) for h in cols]),
                      'share': np.array([(1 - g) / len(d['body'])] * len(d['body']) + [g / len(d['glow'])] * len(d['glow']))})

# ---------- the measures ----------
def measure(bgr, person=None, src=None):
    lab = oklab(bgr); L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]; C = np.hypot(a, b); H = (np.degrees(np.arctan2(b, a)) + 360) % 360
    p5, p50, p95 = np.percentile(L, [5, 50, 95])
    L8 = np.clip(L * 255, 0, 255).astype(np.uint8); t, _ = cv2.threshold(L8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU); lightm = L8 > t
    notan = float(L[lightm].mean() - L[~lightm].mean()) if lightm.any() and (~lightm).any() else 0.0
    rgb = bgr[..., ::-1].astype(np.float32); rg = rgb[..., 0] - rgb[..., 1]; yb = .5 * (rgb[..., 0] + rgb[..., 1]) - rgb[..., 2]
    colourful = float(np.hypot(rg.std(), yb.std()) + .3 * np.hypot(rg.mean(), yb.mean()))
    hh = np.histogram(H, 12, (0, 360), weights=C)[0]; hh = hh / max(hh.sum(), 1e-6)
    P, sh = palette(lab)
    e = cv2.Canny(L8, 40, 110) > 0; gx = cv2.Sobel(L, cv2.CV_32F, 1, 0); gy = cv2.Sobel(L, cv2.CV_32F, 0, 1); g = np.hypot(gx, gy)
    q = np.argmin(np.linalg.norm(lab[..., None, :] - P[None, None], axis=-1), -1); nreg = 0; sizes = []
    for k in range(len(P)):
        n, lb, st, _ = cv2.connectedComponentsWithStats((q == k).astype(np.uint8), 8); big = st[1:, 4] >= 12; nreg += int(big.sum()); sizes += list(st[1:, 4][big])
    m = {'L': round(float(L.mean()), 3), 'L5': round(float(p5), 3), 'L95': round(float(p95), 3), 'range': round(float(p95 - p5), 3), 'crushed': round(float((L < .2).mean()), 3),
         'clipped': round(float((L > .95).mean()), 3), 'notan': round(notan, 3), 'light_share': round(float(lightm.mean()), 3),
         'chroma': round(float(C.mean()), 4), 'chroma90': round(float(np.percentile(C, 90)), 4), 'colourful': round(colourful, 1), 'hue': [round(float(x), 3) for x in hh],
         'palette': [from_oklab(c[None, None])[0, 0][::-1].tolist() for c in P], 'shares': [round(float(s), 3) for s in sh], '_P': P, '_sh': sh,
         'edges': round(float(e.mean()), 4), 'flat': round(float((g < .02).mean()), 3), 'regions': nreg, 'region_px': round(float(np.mean(sizes)), 1) if sizes else 0}
    if person is not None and person.mean() > .01 and person.mean() < .9:
        ring = cv2.dilate(person.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~person
        if ring.any():
            m['fig_dL'] = round(float(abs(np.median(L[person]) - np.median(L[ring]))), 3)
            m['fig_dE'] = round(float(np.linalg.norm(np.median(lab[person], 0) - np.median(lab[ring], 0)) * 100), 1)
            m['person'] = round(float(person.mean()), 3)
    if src is not None:
        es = cv2.Canny(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY), 60, 140) > 0
        if es.any() and e.any():
            ds = cv2.distanceTransform((~es).astype(np.uint8), cv2.DIST_L2, 3); dc = cv2.distanceTransform((~e).astype(np.uint8), cv2.DIST_L2, 3)
            pr, rc = float((ds[e] <= 2).mean()), float((dc[es] <= 2).mean()); m['structure'] = round(2 * pr * rc / max(pr + rc, 1e-6), 3)
    m['district'], m['district_d'] = min(((d['id'], paldist(P, sh, d['lab'], d['share'])) for d in DISTRICTS), key=lambda x: x[1]); m['district_d'] = round(m['district_d'], 1)
    return m

def score(m):
    """legibility, 0–100, weighted by what makes wygwyl-world-arch's cels read: the figure standing off its ground, nothing crushed to
    black, a clear notan, flat areas, few regions, the footage's structure kept"""
    fg = min(1, m['fig_dL'] / .2) if m.get('fig_dL') is not None else .6
    s = 25 * fg + 20 * (1 - min(1, m['crushed'] / .3)) + 20 * min(1, m['notan'] / .3) + 15 * min(1, m['flat'] / .7) + 10 * (1 - min(1, max(0, m['regions'] - 50) / 150)) + 10 * min(1, (m.get('structure') or .3) / .5)
    return round(float(np.clip(s, 0, 100)), 1)

def fix(bgr, m, person):
    """toward the reference: stretch L to .06–.94, bring the mids up to the reference's lightness, push a merged figure off its ground
    (the notan rule: the hero flips toward the opposite of its surround), chroma up to the reference's, and flatten (mean shift)"""
    lab = oklab(bgr); L = lab[..., 0]; lo, hi = m['L5'], m['L95']
    if hi < .2: return bgr                                   # a black frame (a fade, a card) is black on purpose
    Ln = np.clip((L - lo) / max(hi - lo, .25), 0, 1); g = gamma_for(m); Ln = .06 + .88 * Ln ** g
    if person is not None and person.any() and 'fig_dL' in m and m['fig_dL'] < .15:
        ring = cv2.dilate(person.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~person
        up = np.median(Ln[person]) <= np.median(Ln[ring]) if ring.any() else np.median(Ln[person]) < .5
        soft = cv2.GaussianBlur(person.astype(np.float32), (0, 0), 3); push = (.2 - m['fig_dL']) * (-1 if up else 1)
        Ln = np.clip(Ln + soft * push * .6 - (1 - soft) * push * .4, 0, 1)
    lab[..., 0] = Ln; lab[..., 1:] *= np.clip(.042 / max(m['chroma'], 1e-3), 1, 1.8)
    return cv2.pyrMeanShiftFiltering(from_oklab(lab), 6, 14)

def gamma_for(m):
    """the power that brings this frame's mean lightness, once stretched, to the reference's (.48)"""
    if m['L95'] < .2: return 1.0
    mid = np.clip((m['L'] - m['L5']) / max(m['L95'] - m['L5'], .25), .05, .95)
    return float(np.clip(np.log(.48) / np.log(mid), .55, 1.3))

# ---------- what is measured ----------
def frames_of(pid, which, n=3):
    fs = sorted(glob.glob(f'{VD}/{pid}/{which}/*.png'))
    return [fs[int(i)] for i in np.linspace(0, len(fs) - 1, n).round()] if fs else []
def units():
    C = json.load(open(os.path.join(LAB, 'cels', 'cels.json')))['patches']; plan = json.load(open('/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH/spinecut_cels_plan.json'))
    U = [('cels', p['id'], p['t0'], p['t1'], p.get('title') or '', p.get('line') or '') for p in C if p['status'] == 'drawn']
    U += [('spinecels', p['pid'], p['t0'], p['t1'], p.get('title') or '', p.get('line') or '') for p in plan]
    return U

_M = None
def people(bgr):
    global _M
    if _M is None:
        from transformers import Sam3Processor, Sam3Model
        dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
        _M = (Sam3Processor.from_pretrained('facebook/sam3'), Sam3Model.from_pretrained('facebook/sam3').to(dev).eval(), dev)
    P, M, dev = _M
    with torch.no_grad():
        x = P(images=Image.fromarray(bgr[..., ::-1]), text='person', return_tensors='pt').to(dev); o = M(**x)
        r = P.post_process_instance_segmentation(o, threshold=.4, mask_threshold=.5, target_sizes=[bgr.shape[:2]])[0]
    return r['masks'].any(0).cpu().numpy() if len(r['masks']) else np.zeros(bgr.shape[:2], bool)

rd = lambda f: (lambda im: cv2.resize(im, (W, int(W * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA))(cv2.imread(f))
strip = lambda m: {k: v for k, v in m.items() if not k.startswith('_')}
def fixjson():
    """cels/colour/fix.json: each patch's fix for the mixer, on the suite clock: its value range in display luma (from OKLab L,
    luma ≈ L^1.36), a lift for crushed frames, and how far to push a merged figure off its ground"""
    A = json.load(open(f'{OUT}/analysis.json')); F = {}
    for d in ('cels', 'spinecels'):
        F[d] = sorted([{'t0': r['t0'], 't1': r['t1'], 'id': r['id'], 'lo': round(r['L5'] ** 1.36, 3) if r['L95'] >= .2 else 0, 'hi': round(max(r['L95'], r['L5'] + .25) ** 1.36, 3) if r['L95'] >= .2 else 1,
                        'g': round(gamma_for(r), 3), 'push': round(max(0, .2 - r['fig_dL']) * .6, 3) if r.get('fig_dL') is not None and r['fig_dL'] < .15 else 0,
                        'legibility': r['legibility']} for r in A['patches'] if r['deck'] == d], key=lambda x: x['t0'])
    json.dump(F, open(f'{OUT}/fix.json', 'w')); print('fix.json', {d: len(v) for d, v in F.items()})

if __name__ == '__main__' and '--fixjson' in sys.argv: fixjson(); raise SystemExit
if __name__ == '__main__':
    rows = []; CP = f'{OUT}/_cache.jsonl'                    # finished patches, so a rerun resumes
    cache = {json.loads(l)['id']: json.loads(l) for l in open(CP)} if os.path.exists(CP) else {}
    for deck, pid, t0, t1, title, line in units()[:int(os.environ.get('LIMIT', 10 ** 6))]:
        if pid in cache: r = cache[pid]; r['legibility'] = score(r); r.pop('fixed', None); rows.append(r); continue
        cf, sf = frames_of(pid, 'cel_v2'), frames_of(pid, 'frames')
        if not cf: continue
        ms, ss = [], []
        for i, f in enumerate(cf):
            im = rd(f); src = rd(sf[i]) if i < len(sf) else None
            if src is not None and src.shape != im.shape: src = cv2.resize(src, im.shape[1::-1])
            per = people(im) if i == 1 else None
            ms.append(measure(im, per, src)); ss.append(measure(src) if src is not None else None)
            if i == 1:
                cv2.imwrite(f'{OUT}/thumbs/{pid}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 82]); mid, mper = im, per
        mm = ms[1] if len(ms) > 1 else ms[0]
        avg = lambda k, R: round(float(np.mean([r[k] for r in R if r and k in r])), 3) if any(r and k in r for r in R) else None
        row = {'deck': deck, 'id': pid, 't0': t0, 't1': t1, 'title': title, 'line': line[:140], **{k: v for k, v in strip(mm).items()},
               **{f'{k}': avg(k, ms) for k in ('L', 'range', 'crushed', 'notan', 'chroma', 'colourful', 'edges', 'flat', 'regions', 'structure')},
               'src': {k: avg(k, ss) for k in ('L', 'range', 'crushed', 'notan', 'chroma', 'colourful', 'edges', 'flat', 'regions')}}
        row['src_palette_shift'] = round(paldist(ms[1]['_P'] if len(ms) > 1 else ms[0]['_P'], mm['_sh'], ss[1]['_P'], ss[1]['_sh']), 1) if len(ss) > 1 and ss[1] else None
        row['legibility'] = score(row); rows.append(row)
        with open(CP, 'a') as fh: fh.write(json.dumps(row, default=float) + '\n')
        print(deck, pid, row['legibility'], flush=True)
    # the reference: wygwyl-world-arch's own cels
    ref = []
    for f in sorted(glob.glob(f'{REF}/out/*/cartoon/cel.png'))[:int(os.environ.get('LIMIT', 10 ** 6))]:
        im = rd(f); src = rd(os.path.join(os.path.dirname(os.path.dirname(f)), 'image.jpg')) if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(f)), 'image.jpg')) else None
        if src is not None and src.shape != im.shape: src = cv2.resize(src, im.shape[1::-1])
        m = strip(measure(im, people(im), src)); m['legibility'] = score(m); m['id'] = f.split('/')[-3]; ref.append(m)
        cv2.imwrite(f'{OUT}/thumbs/ref_{m["id"][:8]}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 82])
    print('reference', len(ref), flush=True)
    # the fix, for the weakest third
    weak = {r['id'] for r in sorted([r for r in rows if r['L95'] >= .2], key=lambda r: r['legibility'])[:max(24, len(rows) // 3)]}
    for r in rows:
        if r['id'] in weak:
            im = cv2.imread(f'{OUT}/thumbs/{r["id"]}.jpg'); per = people(im); mm = measure(im, per)
            fx = fix(im, mm, per); cv2.imwrite(f'{OUT}/fix/{r["id"]}.jpg', fx, [cv2.IMWRITE_JPEG_QUALITY, 82])
            after = strip(measure(fx, per)); r['fixed'] = {'legibility': score({**after, 'structure': r.get('structure') or .3}), 'range': after['range'], 'notan': after['notan'], 'fig_dL': after.get('fig_dL')}
    def summ(R):
        ks = ['legibility', 'L', 'range', 'crushed', 'notan', 'chroma', 'colourful', 'edges', 'flat', 'regions', 'structure', 'fig_dL', 'district_d']
        return {k: round(float(np.median([r[k] for r in R if r.get(k) is not None])), 3) for k in ks if any(r.get(k) is not None for r in R)} | {'n': len(R)}
    srcs = [r['src'] for r in rows if r['src'].get('L') is not None]
    S = {'cels': summ([r for r in rows if r['deck'] == 'cels']), 'spinecels': summ([r for r in rows if r['deck'] == 'spinecels']), 'reference': summ(ref),
         'footage': {k: round(float(np.median([s[k] for s in srcs if s.get(k) is not None])), 3) for k in srcs[0]}}
    json.dump({'about': 'colour and legibility of every cel (cels/build_colour.py)', 'districts': [{'id': d['id'], 'name': d['name'], 'colors': d['colors']} for d in DISTRICTS],
               'summary': S, 'patches': rows, 'reference': ref}, open(f'{OUT}/analysis.json', 'w'), ensure_ascii=False)
    print(json.dumps(S, indent=1)); fixjson()
