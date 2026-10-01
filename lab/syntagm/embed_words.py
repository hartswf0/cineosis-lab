"""Embed the words under every shot of the poem cuts with CLIP's text tower → words-emb.npy, words-keys.json.

    python3 lab/syntagm/embed_words.py

Same model as cache/emb.npy (ViT-B-32, laion2b_s34b_b79k), same prompt as cutbastard/plan.py. Needs the weights
(huggingface.co). swap_test.py reads the result and runs its word terms only when it exists.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from swap_test import load_sequences

def main():
    import torch, open_clip
    texts = sorted({s["words"] for seq in load_sequences()["poem"] for s in seq["shots"] if s["words"]})
    model, _, _ = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k"); model.eval()
    tok = open_clip.get_tokenizer("ViT-B-32")
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 64):
            t = model.encode_text(tok([f"a film still: {x}"[:300] for x in texts[i:i + 64]])).float()
            out.append((t / t.norm(dim=-1, keepdim=True)).numpy())
    np.save(os.path.join(HERE, "words-emb.npy"), np.concatenate(out).astype(np.float32))
    json.dump(texts, open(os.path.join(HERE, "words-keys.json"), "w"), ensure_ascii=False)
    print(f"{len(texts)} word spans embedded")

if __name__ == "__main__":
    main()
