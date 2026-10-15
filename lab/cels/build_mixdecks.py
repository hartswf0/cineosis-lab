#!/usr/bin/env python3
"""THE MIXER'S DECKS: each of the two main cel cuts (Cels, Spine-Cut Cels) as one video that carries its own layers, for cel-mixer.html.
Every frame is 960×1080: the cel on top (960×540), and under it four masks in grey, 480×270 each, so a picture and its masks can
never drift apart:
    person │ skin
    sky    │ ground
The masks are SAM 3's, asked in words ("person", "skin", "sky", "ground") twice a second; the frames between carry the
nearest two masks along the picture's own motion (optical flow), blended by time. 12 frames a second (the cels are drawn on twos).
  wygwyl/cuts/<slug>/mix.mp4   (local; on the release as wygwyl-mix-<slug>.mp4)
Resumable by the minute. Run from lab/ with wygwyl-world-arch's venv:
  HF_HUB_OFFLINE=1 …/.venv-shots/bin/python cels/build_mixdecks.py [cels spinecels]
For the web (--web): each deck cut into the suite's 14 chapters at 640×720, served from this site (cels/mix/<slug>/NN.mp4), since
WebGL may only read video from its own origin and the release does not allow others; cels/mix/index.json lists them. Without a
deck yet (--web --plain) the cut itself is used, with empty masks."""
import os, sys, glob, shutil, subprocess, numpy as np, cv2, torch
from PIL import Image

LAB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS, W, H, MW, MH, EVERY, PART = 12, 960, 540, 480, 270, 6, 60
PROMPTS = ['person', 'skin', 'sky', 'ground']
DEV = 'mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'
_M = None

def model():
    global _M
    if _M is None:
        from transformers import Sam3Processor, Sam3Model
        _M = (Sam3Processor.from_pretrained('facebook/sam3'), Sam3Model.from_pretrained('facebook/sam3').to(DEV).eval())
    return _M

def masks(frames):
    """SAM 3 on a few frames at once: for each, the four layers as 480×270 uint8 (255 = in the layer)"""
    P, M = model(); ims = [Image.fromarray(f) for f in frames]; out = [np.zeros((len(PROMPTS), MH, MW), np.uint8) for _ in frames]
    with torch.no_grad():
        x = P(images=ims, return_tensors='pt').to(DEV); V = M.get_vision_features(pixel_values=x['pixel_values'])
        for j, q in enumerate(PROMPTS):
            tx = P(text=[q] * len(ims), return_tensors='pt').to(DEV)
            o = M(vision_embeds=V, input_ids=tx['input_ids'], attention_mask=tx['attention_mask'])
            R = P.post_process_instance_segmentation(o, threshold=0.4, mask_threshold=0.5, target_sizes=[(MH, MW)] * len(ims))
            for i, r in enumerate(R):
                if len(r['masks']): out[i][j] = (r['masks'].any(0).cpu().numpy() * 255).astype(np.uint8)
    return [cv2.GaussianBlur(m.transpose(1, 2, 0), (0, 0), 1.0).transpose(2, 0, 1) for m in out]

def flow_to(src_g, dst_g):                                     # for each pixel of dst, where it was in src (at mask size)
    f = cv2.calcOpticalFlowFarneback(dst_g, src_g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    gx, gy = np.meshgrid(np.arange(MW, dtype=np.float32), np.arange(MH, dtype=np.float32)); return gx + f[..., 0], gy + f[..., 1]

def warp(m, mp): return np.stack([cv2.remap(c, mp[0], mp[1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE) for c in m])

def part(src, k, out):
    """one minute of the deck: frames k·60 … (k+1)·60 s, plus one key past the end so the last frames have a mask on both sides"""
    t0 = k * PART; n_want = PART * FPS
    r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-i', src, '-t', f'{PART + EVERY / FPS + 0.05:.3f}', '-vf', f'fps={FPS},scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True, check=True)
    F = np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W, 3)
    if not len(F): return False
    n = min(n_want, len(F)); keys = list(range(0, len(F), EVERY))
    if keys[-1] < n - 1 and len(F) - 1 not in keys: keys.append(len(F) - 1)
    G = [cv2.cvtColor(cv2.resize(f, (MW, MH), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY) for f in F]
    K = {}
    for b in range(0, len(keys), 4):
        ks = keys[b:b + 4]
        for kk, m in zip(ks, masks([F[i] for i in ks])): K[kk] = m
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{2 * H}', '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-crf', '21', '-preset', 'medium', '-g', str(2 * FPS), '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(n):
        a = max(x for x in keys if x <= i); b = min((x for x in keys if x >= i), default=a)
        if i == a: m = K[a]
        elif i == b: m = K[b]
        else:
            w = (i - a) / (b - a); m = ((1 - w) * warp(K[a], flow_to(G[a], G[i])) + w * warp(K[b], flow_to(G[b], G[i]))).astype(np.uint8)
        low = np.vstack([np.hstack([m[0], m[1]]), np.hstack([m[2], m[3]])])
        enc.stdin.write(np.vstack([F[i], np.repeat(low[..., None], 3, 2)]).tobytes())
    enc.stdin.close(); enc.wait(); return n == n_want

def deck(slug):
    src = os.path.join(LAB, 'wygwyl', 'cuts', slug, 'cut.mp4'); tmp = os.path.join(LAB, 'wygwyl', 'cuts', slug, '_mix'); os.makedirs(tmp, exist_ok=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    parts = []
    for k in range(int(np.ceil(dur / PART))):
        o = f'{tmp}/{k:03d}.mp4'; parts.append(o)
        if os.path.exists(o) and os.path.getsize(o) > 1000: continue
        part(src, k, o + '.tmp.mp4'); os.replace(o + '.tmp.mp4', o); print(slug, 'minute', k, flush=True)
    open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    out = os.path.join(LAB, 'wygwyl', 'cuts', slug, 'mix.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-i', src, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    shutil.rmtree(tmp); print(slug, 'deck', out, flush=True)

def web(slugs, plain=False):
    import json
    D = json.load(open(os.path.join(LAB, 'spinecut', 'spinecut-data.json'))); CH = [{'n': f['n'], 'title': f['title'].title(), 't0': f['t0'], 't1': f['t1']} for f in D['films']]
    idx = {'about': 'the cel mixer’s decks (cels/build_mixdecks.py --web)', 'size': [640, 720], 'layers': PROMPTS, 'fps': FPS, 'audio': D['audio'], 'duration': D['duration'], 'chapters': CH, 'decks': {}}
    ip = os.path.join(LAB, 'cels', 'mix', 'index.json')
    if os.path.exists(ip): idx['decks'] = json.load(open(ip)).get('decks', {})
    for slug in slugs:
        mix = os.path.join(LAB, 'wygwyl', 'cuts', slug, 'mix.mp4'); od = os.path.join(LAB, 'cels', 'mix', slug); os.makedirs(od, exist_ok=True)
        masks_ok = os.path.exists(mix) and not plain; src = mix if masks_ok else os.path.join(LAB, 'wygwyl', 'cuts', slug, 'cut.mp4')
        vf = 'scale=640:720' if masks_ok else 'scale=640:360,pad=640:720:0:0:black'
        for ch in CH:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{ch['t0']:.3f}", '-i', src, '-t', f"{ch['t1'] - ch['t0']:.3f}", '-vf', f'fps={FPS},{vf}', '-an',
                            '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-g', str(FPS), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f"{od}/{ch['n']}.mp4"], check=True)
        idx['decks'][slug] = {'masks': masks_ok, 'files': [f"cels/mix/{slug}/{ch['n']}.mp4" for ch in CH]}; print('web', slug, 'masks' if masks_ok else 'plain', flush=True)
    json.dump(idx, open(ip, 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    S = [a for a in sys.argv[1:] if not a.startswith('-')] or ['cels', 'spinecels']
    if '--web' in sys.argv: web(S, plain='--plain' in sys.argv)
    else:
        for s in S: deck(s)
