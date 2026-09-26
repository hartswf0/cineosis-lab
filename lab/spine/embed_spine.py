"""Embed the spine's images and texts with the lab's CLIP, on the machine that has the images.

    pip install torch open_clip_torch pillow numpy
    python3 lab/spine/embed_spine.py /path/to/images [/another/folder ...]

Walks the folders for .png/.jpg, keeps the files whose name is an image_path in lab/spine/*.json, and embeds them with
ViT-B-32 laion2b_s34b_b79k (the model of lab/cache/emb.npy, so spine images and archive shots share one space).
It also embeds, with the same model's text tower:
  - every record's content (the line) and operativeEkphrasis (the prompt);
  - the words under each shot of the poem cuts (lab/syntagm/embed_words.py), which the cloud session cannot fetch.

Writes (commit these; they are small):
  lab/spine/img-emb.npy     float16 [n, 512], L2-normalised     lab/spine/img-keys.json    filenames, same order
  lab/spine/text-emb.npy    float16 [m, 512]                    lab/spine/text-keys.json   texts, same order
  lab/syntagm/words-emb.npy, lab/syntagm/words-keys.json
"""
import glob, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)


def main(folders):
    import torch, open_clip
    from PIL import Image
    dev = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    model = model.to(dev).eval()
    tok = open_clip.get_tokenizer("ViT-B-32")

    records = []
    for f in sorted(glob.glob(os.path.join(HERE, "*.json"))):
        d = json.load(open(f))
        if isinstance(d, list): records += [r for r in d if isinstance(r, dict)]
    wanted = {r["image_path"] for r in records if r.get("image_path")}

    found = {}
    for folder in folders:
        for p in glob.glob(os.path.join(os.path.expanduser(folder), "**", "*"), recursive=True):
            name = os.path.basename(p)
            if name in wanted and name not in found and p.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                found[name] = p
    keys = sorted(found)
    print(f"{len(keys)} of {len(wanted)} spine images found on {dev}")

    embs = []
    with torch.no_grad():
        for i in range(0, len(keys), 32):
            batch = torch.stack([pre(Image.open(found[k]).convert("RGB")) for k in keys[i:i + 32]]).to(dev)
            e = model.encode_image(batch).float(); embs.append((e / e.norm(dim=-1, keepdim=True)).cpu().numpy())
            print(f"  images {min(i + 32, len(keys))}/{len(keys)}", end="\r")
    if keys:
        np.save(os.path.join(HERE, "img-emb.npy"), np.concatenate(embs).astype(np.float16))
        json.dump(keys, open(os.path.join(HERE, "img-keys.json"), "w"))
    missing = sorted(wanted - set(keys))
    if missing:
        json.dump(missing, open(os.path.join(HERE, "img-missing.json"), "w"), indent=0)
        print(f"\n{len(missing)} not found, listed in lab/spine/img-missing.json")

    def encode_texts(texts):
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), 64):
                t = model.encode_text(tok([f"a film still: {x}"[:300] for x in texts[i:i + 64]]).to(dev)).float()
                out.append((t / t.norm(dim=-1, keepdim=True)).cpu().numpy())
        return np.concatenate(out).astype(np.float16)

    texts = sorted({r[k].strip() for r in records for k in ("content", "operativeEkphrasis") if isinstance(r.get(k), str) and r[k].strip()})
    np.save(os.path.join(HERE, "text-emb.npy"), encode_texts(texts))
    json.dump(texts, open(os.path.join(HERE, "text-keys.json"), "w"), ensure_ascii=False)
    print(f"\n{len(texts)} spine texts embedded")

    sys.path.insert(0, os.path.join(LAB, "syntagm"))
    from swap_test import load_sequences
    spans = sorted({s["words"] for seq in load_sequences()["poem"] for s in seq["shots"] if s["words"]})
    np.save(os.path.join(LAB, "syntagm", "words-emb.npy"), encode_texts(spans).astype(np.float32))
    json.dump(spans, open(os.path.join(LAB, "syntagm", "words-keys.json"), "w"), ensure_ascii=False)
    print(f"{len(spans)} word spans under the poem cuts embedded")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
