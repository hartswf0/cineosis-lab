"""MARKOV FOUND · REPUBLIC: puppets. For each character's cut-out still:
  face   where the face is (OpenCV's frontal, then profile, cascade on the figure itself), so the page can cut the jaw along the
         mouth line and flap it with the voice, the way paper cut-out animation speaks
  kind   what the figure is to the eye (CLIP: a man, a woman, a child, a machine, an animal, a cartoon, a thing), so a woman's voice
         is never put in a man's mouth: the page lets a figure speak only when its kind agrees with its character
Adds "face" [x, y, w, h] (fractions of the still) and "kind" to each figure in planes.json.   usage: republic/.tts/bin/python republic/faces.py"""
import json, os
import numpy as np, cv2, torch, open_clip
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
P = json.load(open(os.path.join(H, "planes.json")))
FR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); PR = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
m, _, pre = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
KINDS = [("m", "a photo of a man"), ("f", "a photo of a woman"), ("child", "a photo of a child"), ("machine", "a photo of a machine or a robot"), ("animal", "a photo of an animal"), ("cartoon", "a cartoon drawing of a character"), ("thing", "a photo of an object")]
with torch.no_grad(): T = m.encode_text(tok([t for _, t in KINDS])).float(); T = (T / T.norm(dim=-1, keepdim=True)).numpy()
for name, figs in P["cast"].items():
    for f in figs[:1]:
        im = np.array(Image.open(os.path.join(L, f["f"].split("?")[0])).convert("RGBA")); h, w = im.shape[:2]
        a = im[..., 3:] / 255.; rgb = (im[..., :3] * a + 128 * (1 - a)).astype(np.uint8)
        with torch.no_grad(): v = m.encode_image(pre(Image.fromarray(rgb)).unsqueeze(0)).float(); v = (v / v.norm()).numpy()[0]
        f["kind"] = KINDS[int(np.argmax(T @ v))][0]
        g = cv2.equalizeHist(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)); ms = max(16, int(min(h, w) * .08))
        faces = list(FR.detectMultiScale(g, 1.08, 4, minSize=(ms, ms))) or list(PR.detectMultiScale(g, 1.08, 4, minSize=(ms, ms))) or list(PR.detectMultiScale(cv2.flip(g, 1), 1.08, 4, minSize=(ms, ms)))
        if faces and len(faces[0]) and faces is not None and not isinstance(faces, tuple):
            x, y, fw, fh = max(faces, key=lambda b: b[2] * b[3] * (1.4 if b[1] < h * .55 else .6))
            if a[int(y + fh * .7), int(x + fw / 2)] > .5: f["face"] = [round(x / w, 3), round(y / h, 3), round(fw / w, 3), round(fh / h, 3)]
            else: f.pop("face", None)
        else: f.pop("face", None)
        print(f"{name:20} {f['kind']:8} {'face' if f.get('face') else '—'}")
json.dump(P, open(os.path.join(H, "planes.json"), "w"), ensure_ascii=False, separators=(",", ":"))
