"""The light reader, corrected. The 8-bit CLIP text model (62 MB) reads a little differently from the exact one (121 MB).
A 512x512 linear map, fitted on a few thousand phrases, carries its output onto the exact model's, so every device can use the
small download. Writes markov/reader-fix.bin (float32, row-major W: exact ≈ normalise(q8 @ W)) and prints held-out agreement."""
import json, os, random, sys
import numpy as np, onnxruntime as ort, open_clip, torch
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
texts = set(json.load(open(os.path.join(H, "phrases.json"))))
L = json.load(open(os.path.join(H, "library.json")))["shots"]; texts |= {s["title"] for s in L if s.get("title")}
texts |= set(json.load(open(os.path.join(H, "events.json")))["events"])
for p in json.load(open(os.path.join(H, "tests/poems.json")))["poems"]:
    for l in (p.get("text") or "").split("\n"):
        if l.strip(): texts.add(l.strip())
K = json.load(open(os.path.join(LAB, "bets/kernel-data.json")))
texts |= {l["text"] for l in K["lines"]} | {b["title"] for b in K["beats"]}
r = random.Random(3); subj = ["a man", "a woman", "a child", "two people", "a crowd", "an old man", "a girl", "workers", "a family", "a dog", "a horse", "a ship", "a train", "the city", "a house", "a river", "the sea", "a field", "a street at night", "a door", "a window", "hands", "a face"]
verb = ["waits", "walks away", "runs", "is leaving", "returns", "sleeps", "laughs", "is working", "looks out", "falls", "dances", "sings", "is burning", "stands still", "opens", "closes", "is empty", "in the rain", "at dawn", "in the snow"]
texts |= {f"{r.choice(subj)} {r.choice(verb)}" for _ in range(900)} | {f"{a} and {b}" for a in subj[:12] for b in subj[12:]}
texts = sorted(t for t in texts if t and len(t) < 300); r.shuffle(texts); print(len(texts), "phrases", flush=True)
m, _, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai"); m.eval(); tok = open_clip.get_tokenizer("ViT-B-32-quickgelu")
with torch.no_grad():
    E = np.concatenate([(lambda e: (e / e.norm(dim=-1, keepdim=True)).numpy())(m.encode_text(tok(texts[i:i + 256])).float()) for i in range(0, len(texts), 256)])
sess = ort.InferenceSession(os.path.join(LAB, "models/clip-q8/text_model_quantized.onnx"))
Q = []
for t in texts:
    ids = tok([t])[0].numpy(); n = int(ids.argmax()) + 1                    # [sot] … [eot], unpadded, as the browser sends one text
    q = sess.run(None, {"input_ids": ids[:n][None].astype(np.int64)})[0][0]; Q.append(q / np.linalg.norm(q))
Q = np.stack(Q).astype(np.float64); E = E.astype(np.float64)
n = int(len(texts) * .85); lam = 1e-2
W = np.linalg.solve(Q[:n].T @ Q[:n] + lam * np.eye(512), Q[:n].T @ E[:n])
def cos(A, B): return (A * B).sum(1) / (np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1))
raw, fix = cos(Q[n:], E[n:]), cos(Q[n:] @ W, E[n:])
print("held-out cosine to the exact reader: raw %.3f (min %.3f)  corrected %.3f (min %.3f)" % (raw.mean(), raw.min(), fix.mean(), fix.min()))
X = np.fromfile(os.path.join(H, "emb.bin"), dtype=np.int8).reshape(-1, 512).astype(np.float32)
def top(V, k=8): return np.argsort(-(X @ V.T.astype(np.float32)), axis=0)[:k].T
te, tr, tf = top(E[n:n + 300]), top(Q[n:n + 300]), top(Q[n:n + 300] @ W)
agree = lambda a, b: (np.mean([x[0] == y[0] for x, y in zip(a, b)]), np.mean([len(set(x) & set(y)) / 8 for x, y in zip(a, b)]))
print("same first shot / overlap of the top 8:  raw %.2f / %.2f   corrected %.2f / %.2f" % (*agree(te, tr), *agree(te, tf)))
W2 = np.linalg.solve(Q.T @ Q + lam * np.eye(512), Q.T @ E)               # the shipped map uses every phrase
W2.astype(np.float32).tofile(os.path.join(H, "reader-fix.bin")); print("wrote reader-fix.bin", W2.shape)
