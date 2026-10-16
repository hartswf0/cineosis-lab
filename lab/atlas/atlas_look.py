"""ATLAS LOOK · what each page looks like, to a machine. Reads the frames that frames.cjs filmed (lab/atlas/frames/), embeds each
frame with CLIP (ViT-B/32, the lab's own model) and averages a page's frames into one vector. From it:
  tags   the words from a fixed vocabulary of screens and footage that the page's frames sit nearest (CLIP zero-shot), so a page can
         be searched for by what you remember seeing ("a timeline", "black and white film footage", "a spider web")
  looks  the eight pages that look most alike
  xy     a 2D map of the whole lab by look (PCA of the page vectors), for finders that lay pages out by resemblance
Writes lab/atlas/look.json. usage: python3 lab/atlas/atlas_look.py [repo]"""
import json, os, sys, glob
import numpy as np, torch, open_clip
from PIL import Image
REPO = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/cineosis-lab'); D = os.path.join(REPO, 'lab', 'atlas')
meta = json.load(open(os.path.join(D, 'frames.json')))
VOCAB = ['a dark interface', 'a light paper page with text', 'a grid of film thumbnails', 'a wall of video tiles', 'a single film frame', 'black and white film footage',
         'colour film footage', 'a timeline', 'a map', 'a diagram of circles', 'a network graph', 'a table of numbers', 'a bar chart', 'a periodic table of coloured squares',
         'a cartoon character', 'pixel art', 'a large title on a dark screen', 'a page of text', 'a video player with controls', 'a 3d scene', 'a spider web', 'a sound waveform',
         'a storyboard', 'colourful tiles', 'a mostly empty dark screen', 'playing cards', 'a game board', 'a collage of photographs', "a person's face", 'a landscape',
         'a city street', 'the sea', 'a crowd of people', 'animals', 'a rocket or outer space', 'buttons and a menu', 'computer code', 'hand-drawn lines', 'a red line hanging from the top',
         'a ring with two eyes', 'a film strip', 'a calendar of days', 'a scatter of dots', 'a terminal with green text', 'a retro computer screen', 'a dashboard with panels',
         'a poster', 'lego bricks', 'a book page', 'subtitles over a film']
dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
model, _, pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k'); model = model.to(dev).eval(); tok = open_clip.get_tokenizer('ViT-B-32')
with torch.no_grad():
    T = model.encode_text(tok([f'a screenshot of {v}' for v in VOCAB]).to(dev)).float(); T = (T / T.norm(dim=-1, keepdim=True)).cpu().numpy()
paths, V = [], []
for p, m in meta.items():
    fs = [os.path.join(D, 'frames', f) for f in m.get('frames', []) if os.path.exists(os.path.join(D, 'frames', f))]
    if not fs: continue
    with torch.no_grad():
        x = torch.stack([pre(Image.open(f).convert('RGB')) for f in fs]).to(dev); e = model.encode_image(x).float(); e = e / e.norm(dim=-1, keepdim=True)
    v = e.mean(0); v = v / v.norm(); paths.append(p); V.append(v.cpu().numpy())
V = np.array(V); S = V @ V.T; np.fill_diagonal(S, -1)
Z = (V @ T.T) * 100; Pz = np.exp(Z - Z.max(1, keepdims=True)); Pz /= Pz.sum(1, keepdims=True)
C = V - V.mean(0); _, _, Wt = np.linalg.svd(C, full_matrices=False); XY = C @ Wt[:2].T; XY = (XY - XY.min(0)) / (XY.max(0) - XY.min(0) + 1e-9)
out = {}
for i, p in enumerate(paths):
    order = np.argsort(-Pz[i]); tags = [VOCAB[k] for k in order[:5] if Pz[i, k] >= .06][:4] or [VOCAB[order[0]]]
    out[p] = {'tags': tags, 'looks': [[paths[j], round(float(S[i, j]), 3)] for j in np.argsort(-S[i])[:8]], 'xy': [round(float(XY[i, 0]), 4), round(float(XY[i, 1]), 4)]}
json.dump(out, open(os.path.join(D, 'look.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print('pages', len(out), 'tags', Counter(t for o in out.values() for t in o['tags']).most_common(12))
