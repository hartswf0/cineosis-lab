"""The Shannon engine's library: every shot we hold, read for what an edit can do with it.

For each shot (archive 15,149 + presence forage + the poet's CDMX takes, local only):
  src/order   which film it comes from and where in that film (a scene can continue forward, a sequence can skip)
  place       a setting cluster (k-means over CLIP image embeddings): the film can return to a place, so a world accumulates
  events      its three strongest readings from a fixed vocabulary of visible events and states (waiting, leaving, an empty room ...)
  signs       its top periodic-table signs (the lab's affinity), scale
Writes shannon/library.json, shannon/emb.bin (int8, rows = library order), shannon/events.json (the vocabulary and its text embeddings),
(shannon/embed_texts.py embeds the preset phrases so the page runs without the local server.)"""
import json, os, sys
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(H)
EVENTS = ["a person waiting, standing still", "a person sitting alone", "a person looking out of a window", "a person standing at a door",
  "a person walking away from the camera", "a person walking toward the camera", "people leaving with luggage", "a train departing from a station",
  "a ship leaving a harbor", "a car driving away down a road", "people arriving and greeting each other", "two people embracing",
  "an empty room", "an empty street", "the outside of a house", "inside a home, a kitchen or living room", "a busy city street",
  "a city skyline", "a crowd of people", "a close-up of a face", "hands at work", "a person working", "children playing",
  "a person speaking to the camera", "a person reading or writing", "a bed in a bedroom", "a street at night with lights",
  "the sea, waves on a shore", "boats in a harbor", "fire and smoke", "ruins after destruction", "a long road",
  "a hallway or staircase", "a clock", "a television screen", "a church congregation", "a musician playing", "people dancing",
  "a mother holding a child", "an old man", "a Black man", "a Black woman", "a sunset sky", "rain and storm", "a farm field",
  "a factory with machines", "money and banknotes", "a hospital, a doctor", "a funeral, people mourning", "a parade, a celebration",
  "a door closing", "a window", "a telephone call", "people eating together", "a person sleeping", "a person running",
  "a person falling", "a person alone at night", "an airplane in the sky", "a bridge",
  "a man", "a woman", "a boy or a girl", "a group of men", "a group of women",
  "an intertitle card with printed words", "a title card with text on a plain background", "a diagram, a chart or a map", "a black screen"]
def model():
    import open_clip, torch
    m, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); m.eval()
    tok = open_clip.get_tokenizer("ViT-B-32")
    def enc(texts):
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), 256):
                e = m.encode_text(tok(texts[i:i + 256])).float(); out.append((e / e.norm(dim=-1, keepdim=True)).numpy())
        return np.concatenate(out)
    return enc
def kmeans(X, k, it=25, seed=0):
    rng = np.random.default_rng(seed); C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(it):
        a = np.argmax(X @ C.T, 1)
        for j in range(k):
            m = X[a == j]
            if len(m): c = m.mean(0); C[j] = c / np.linalg.norm(c)
    return a, C
def main():
    enc = model()
    corpus = json.load(open(os.path.join(LAB, "cache/corpus.json"))); ana = json.load(open(os.path.join(LAB, "cache/analysis.json")))
    aff = json.load(open(os.path.join(LAB, "cache/affinity.json"))); rt = json.load(open(os.path.join(LAB, "cache/read_t.json")))
    ids = json.load(open(os.path.join(LAB, "cache/emb_ids.json"))); E = [np.load(os.path.join(LAB, "cache/emb.npy")).astype(np.float32)]
    lib = []
    for i in ids:
        c = corpus[i]; a = ana.get(i, {})
        lib.append({"id": i, "kind": "archive", "src": c["sourceSlug"], "title": c["sourceTitle"], "year": c.get("sourceYear"),
                    "st": c["startSeconds"], "dur": round(c["endSeconds"] - c["startSeconds"], 2), "video": c["videoUrl"],
                    "thumb": f"thumbs/{i}.jpg", "in": rt.get(i, {}).get("t", 0), "scale": a.get("scale"),
                    "signs": [s for s, _ in aff.get(i, {}).get("top", [])[:3]]})
    pool = json.load(open(os.path.join(LAB, "presence/pool.json")))
    fids = json.load(open(os.path.join(LAB, "presence/forage-ids.json"))); fe = np.load(os.path.join(LAB, "presence/forage-emb.npy")).astype(np.float32)
    keep = [j for j, i in enumerate(fids) if i in pool and i not in corpus]
    for j in keep:
        i = fids[j]; p = pool[i]
        lib.append({"id": i, "kind": "presence", "src": p["source"], "title": p["title"], "year": p.get("year"), "st": None, "dur": p.get("dur") or 10,
                    "video": p["video"], "thumb": f"presence/thumbs/{i}.jpg", "in": p.get("read_t") or 0, "scale": None, "signs": []})
    E.append(fe[keep])
    # the poet: his own takes in Mexico City, one shot per second of each clip (local only; never published)
    items = json.load(open(os.path.join(LAB, "cdmx/items.json"))); ce = np.load(os.path.join(LAB, "cdmx/cdmx-emb.npy")).astype(np.float32)
    poet = [j for j, x in enumerate(items) if x["kind"] == "frame" and os.path.exists(os.path.join(LAB, "cdmx/clips", x["clip"] + ".mp4")) and int(x["sec"]) % 2 == 0]
    for j in poet:
        x = items[j]
        lib.append({"id": x["key"], "kind": "poet", "src": "cdmx:" + x["clip"], "title": "CDMX · the poet", "year": 2025, "st": x["sec"], "dur": x["dur"],
                    "video": f"cdmx/clips/{x['clip']}.mp4", "thumb": f"cdmx/t240/{x['key']}.jpg", "in": max(0, x["sec"] - .5), "scale": None, "signs": []})
    E.append(ce[poet])
    X = np.concatenate(E); X /= np.linalg.norm(X, axis=1, keepdims=True)
    print(len(lib), "shots:", sum(1 for l in lib if l["kind"] == "archive"), "archive,", len(keep), "presence,", len(poet), "poet", flush=True)
    TE = enc([f"a film still of {e}" for e in EVENTS]); S = X @ TE.T
    Z = (S - S.mean(0)) / S.std(0)                               # an event reading is relative: how much more this shot shows it than shots in general
    for n, l in enumerate(lib):
        top = np.argsort(-Z[n])[:3]; l["ev"] = [[int(t), round(float(Z[n, t]), 2)] for t in top]
    a, C = kmeans(X, 320)
    for n, l in enumerate(lib): l["place"] = int(a[n])
    q = np.clip(np.round(X * 127 / np.abs(X).max()), -127, 127).astype(np.int8)
    q.tofile(os.path.join(H, "emb-laion.bin"))   # the laion reading feeds events and places; the engine's emb.bin is OpenAI CLIP (embed_openai.py)
    json.dump({"scale_laion": float(np.abs(X).max() / 127), "dim": 512, "n": len(lib), "shots": lib}, open(os.path.join(H, "library.json"), "w"), separators=(",", ":"))
    json.dump({"events": EVENTS, "emb": [[round(float(v), 4) for v in r] for r in TE]}, open(os.path.join(H, "events.json"), "w"), separators=(",", ":"))
    print("ok")
if __name__ == "__main__": main()
