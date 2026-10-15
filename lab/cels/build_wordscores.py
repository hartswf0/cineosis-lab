#!/usr/bin/env python3
"""WHICH CEL CUT MATCHES THE WORDS: both main cel cuts watched by machines, frame by frame, against the line under each moment.
  CLIP          every half second of each cut against the line on screen at that moment (the Spine-Cut section's line: what he
                says, or the storyboard beat between spoken lines), by two models that learnt differently:
                OpenAI ViT-B/16 and LAION-2B ViT-B/32
  BLIP          what the machine says it sees, once a second (BLIP-large captions); the caption read against the line (CLIP text)
  V-JEPA 2      a video model with no words: for every patch, 16 frames of the cel against 16 frames of the footage it was drawn
                from; how much of the footage's action the drawing keeps (1 = the same motion)
Each model's scores are standardised over both cuts together, so the cuts can be compared at every moment.
  cels/mix/words.json   per half second: the line, each cut's score per model and combined; captions; per patch fidelity
Run from lab/:  …/.venv-shots/bin/python cels/build_wordscores.py --clip16 --blip --vjepa
                anaconda python3 cels/build_wordscores.py --laion        (open_clip)
                python3 cels/build_wordscores.py --merge"""
import os, sys, json, glob, subprocess, numpy as np

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(LAB, 'cels', 'mix'); os.makedirs(OUT, exist_ok=True)
VD = '/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH/shots/video'; DECKS = ['cels', 'spinecels']; STEP = 0.5
D = json.load(open(os.path.join(LAB, 'spinecut', 'spinecut-data.json'))); SEC = D['sections']
DUR = 1440.0; T = [round(x, 2) for x in np.arange(0.25, DUR, STEP)]
def line_at(t):
    lo, hi = 0, len(SEC) - 1
    while lo < hi:
        m = (lo + hi + 1) // 2
        if SEC[m]['t0'] <= t: lo = m
        else: hi = m - 1
    return lo
LINES = [line_at(t) for t in T]; TEXT = [(SEC[i].get('line') or '').strip() or 'a dark screen' for i in range(len(SEC))]

def frames(slug, size, times):
    """the cut's frames at the given times, size×size, centre-cropped"""
    src = os.path.join(LAB, 'wygwyl', 'cuts', slug, 'cut.mp4'); step = times[1] - times[0]
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{times[0]:.3f}', '-i', src, '-vf', f'fps={1 / step},scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size}',
                        '-frames:v', str(len(times)), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True)
    F = np.frombuffer(r.stdout, np.uint8).reshape(-1, size, size, 3)
    return np.concatenate([F, np.repeat(F[-1:], len(times) - len(F), 0)]) if len(F) < len(times) else F

def feat(o):                                               # transformers 5 wraps CLIP features in an output object
    o = o if hasattr(o, 'norm') else (o.pooler_output if getattr(o, 'pooler_output', None) is not None else o[0]); return o / o.norm(dim=-1, keepdim=True)

def dev():
    import torch; return 'mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'

def clip16():
    import torch; from transformers import CLIPModel, CLIPProcessor
    M = CLIPModel.from_pretrained('openai/clip-vit-base-patch16').to(dev()).eval(); P = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch16')
    with torch.no_grad():
        te = feat(M.get_text_features(**P(text=TEXT, return_tensors='pt', padding=True, truncation=True, max_length=77).to(dev())))
        out = {}
        for s in DECKS:
            F = frames(s, 224, T); sc = []
            for b in range(0, len(F), 64):
                ie = feat(M.get_image_features(**P(images=list(F[b:b + 64]), return_tensors='pt').to(dev())))
                sc += (ie * te[LINES[b:b + 64]]).sum(-1).cpu().tolist()
            out[s] = [round(x, 4) for x in sc]; print('clip16', s, flush=True)
    json.dump(out, open(f'{OUT}/_clip16.json', 'w'))

def laion():
    import torch, open_clip
    M, _, pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); M = M.to(dev()).eval(); tok = open_clip.get_tokenizer('ViT-B-32')
    from PIL import Image
    with torch.no_grad():
        te = M.encode_text(tok(TEXT).to(dev())); te = te / te.norm(dim=-1, keepdim=True); out = {}
        for s in DECKS:
            F = frames(s, 224, T); sc = []
            for b in range(0, len(F), 64):
                ie = M.encode_image(torch.stack([pre(Image.fromarray(f)) for f in F[b:b + 64]]).to(dev())); ie = ie / ie.norm(dim=-1, keepdim=True)
                sc += (ie * te[LINES[b:b + 64]]).sum(-1).cpu().tolist()
            out[s] = [round(x, 4) for x in sc]; print('laion', s, flush=True)
    json.dump(out, open(f'{OUT}/_laion.json', 'w'))

def blip():
    import torch; from transformers import BlipForConditionalGeneration, BlipProcessor, CLIPModel, CLIPProcessor
    B = BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-large').to(dev()).eval(); BP = BlipProcessor.from_pretrained('Salesforce/blip-image-captioning-large')
    C = CLIPModel.from_pretrained('openai/clip-vit-base-patch16').to(dev()).eval(); CP = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch16')
    T1 = T[::2]; L1 = LINES[::2]; out = {}
    with torch.no_grad():
        te = feat(C.get_text_features(**CP(text=TEXT, return_tensors='pt', padding=True, truncation=True, max_length=77).to(dev())))
        for s in DECKS:
            F = frames(s, 384, T1); caps = []
            for b in range(0, len(F), 16):
                g = B.generate(**BP(images=list(F[b:b + 16]), return_tensors='pt').to(dev()), max_new_tokens=24, num_beams=3)
                caps += [c.strip() for c in BP.batch_decode(g, skip_special_tokens=True)]
            ce = feat(C.get_text_features(**CP(text=caps, return_tensors='pt', padding=True, truncation=True, max_length=77).to(dev())))
            out[s] = {'captions': caps, 'score': [round(x, 4) for x in (ce * te[L1]).sum(-1).cpu().tolist()]}; print('blip', s, flush=True)
    json.dump(out, open(f'{OUT}/_blip.json', 'w'))

def patches():
    """each cut's patches on the suite clock, with their working folders (source frames, cel frames)"""
    C = json.load(open(os.path.join(LAB, 'cels', 'cels.json')))['patches']; plan = json.load(open('/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH/spinecut_cels_plan.json'))
    return {'cels': [(p['id'], p['t0'], p['t1']) for p in C if p['status'] == 'drawn'], 'spinecels': [(p['pid'], p['t0'], p['t1']) for p in plan]}

def vjepa():
    import torch, cv2; from transformers import AutoModel, AutoVideoProcessor
    M = AutoModel.from_pretrained('facebook/vjepa2-vitl-fpc64-256').to(dev()).eval(); P = AutoVideoProcessor.from_pretrained('facebook/vjepa2-vitl-fpc64-256')
    def emb(paths):
        idx = np.linspace(0, len(paths) - 1, 16).round().astype(int); v = np.stack([cv2.cvtColor(cv2.imread(paths[i]), cv2.COLOR_BGR2RGB) for i in idx])
        with torch.no_grad():
            x = P(v, return_tensors='pt').to(dev()); h = M.get_vision_features(**x) if hasattr(M, 'get_vision_features') else M(**x).last_hidden_state
        e = h.mean(1)[0]; return e / e.norm()
    out = {}
    for s, ps in patches().items():
        rows = []
        for pid, t0, t1 in ps:
            src = sorted(glob.glob(f'{VD}/{pid}/frames/*.png')); cel = sorted(glob.glob(f'{VD}/{pid}/cel_v2/*.png'))
            if len(src) < 2 or len(cel) < 2: continue
            n = min(len(src), len(cel)); rows.append({'id': pid, 't0': t0, 't1': t1, 'fid': round(float((emb(src[:n]) * emb(cel[:n])).sum()), 4)})
        out[s] = rows; print('vjepa', s, len(rows), flush=True)
    json.dump(out, open(f'{OUT}/_vjepa.json', 'w'))

def merge():
    get = lambda n: json.load(open(f'{OUT}/_{n}.json')) if os.path.exists(f'{OUT}/_{n}.json') else None
    c16, la, bl, vj = get('clip16'), get('laion'), get('blip'), get('vjepa')
    def z(both):                                               # standardise one model over both cuts together
        a = np.array(both, float); return (a - np.nanmean(a)) / (np.nanstd(a) or 1)
    models = {}
    if c16: models['clip16'] = {s: c16[s] for s in DECKS}
    if la: models['laion'] = {s: la[s] for s in DECKS}
    if bl: models['blip'] = {s: [x for v in bl[s]['score'] for x in (v, v)][:len(T)] for s in DECKS}     # once a second → every half second
    Z = {m: dict(zip(DECKS, np.split(z(np.concatenate([v[s] for s in DECKS])), len(DECKS)))) for m, v in models.items()}
    comb = {s: [round(float(x), 3) for x in np.mean([Z[m][s] for m in Z], 0)] for s in DECKS} if Z else {}
    W = {'about': 'which cel cut matches the words (cels/build_wordscores.py)', 'step': STEP, 't': T, 'line': LINES, 'text': TEXT,
         'models': {m: {'raw': models[m], 'z': {s: [round(float(x), 3) for x in Z[m][s]] for s in DECKS}} for m in models}, 'combined': comb,
         'captions': {s: bl[s]['captions'] for s in DECKS} if bl else None, 'fidelity': vj,
         'summary': {s: {'combined_mean': round(float(np.mean(comb[s])), 3) if comb else None, 'wins': round(float(np.mean(np.array(comb[s]) > np.array(comb[[x for x in DECKS if x != s][0]]))), 3) if comb else None,
                         'fidelity_median': round(float(np.median([r['fid'] for r in vj[s]])), 3) if vj else None} for s in DECKS}}
    W['per_model'] = {m: {s: round(float(np.mean(np.array(models[m][s]) > np.array(models[m][[x for x in DECKS if x != s][0]]))), 3) for s in DECKS} for m in models}
    W['caveat'] = ('Spine-Cut chose its shots by CLIP (LAION ViT-B/32, the line against the archive), so CLIP leans towards Spine-Cut Cels by '
                   'construction; BLIP, which only describes what it sees, is the most independent of the three readings.')
    json.dump(W, open(f'{OUT}/words.json', 'w'), ensure_ascii=False); print(json.dumps(W['summary']), json.dumps(W['per_model']))

if __name__ == '__main__':
    for f in ('clip16', 'laion', 'blip', 'vjepa', 'merge'):
        if '--' + f in sys.argv: globals()[f]()
