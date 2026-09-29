"""Exact-model retrieval shared by the offline builder and the local API."""
from pathlib import Path
import json, threading
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
_model=None
_lock=threading.Lock()
def retrieve(texts, count=64):
 global _model
 with _lock:
  import torch, open_clip
  if _model is None:
   torch.set_num_threads(4)
   model,_,_=open_clip.create_model_and_transforms('ViT-B-32',pretrained='laion2b_s34b_b79k',cache_dir=str(ROOT/'models'))
   model.eval()
   E=np.load(ROOT/'cache/emb.npy').astype('float32');E/=np.maximum(np.linalg.norm(E,axis=1,keepdims=True),1e-9)
   _model=(model,open_clip.get_tokenizer('ViT-B-32'),E,json.load(open(ROOT/'cache/emb_ids.json')))
  model,tok,E,ids=_model
  out=[]
  with torch.inference_mode():
   for text in texts:
    # Long scenes must not silently lose their ending at CLIP's 77-token limit.
    words=tok.encode(text); chunks=[words[i:i+75] for i in range(0,len(words),75)] or [[]]
    batches=[]
    for chunk in chunks:
     row=[tok.sot_token_id]+chunk+[tok.eot_token_id]; batches.append(row+[0]*(77-len(row)))
    v=model.encode_text(torch.tensor(batches)); v=v/v.norm(dim=-1,keepdim=True)
    v=v.mean(dim=0);v=v/v.norm()
    scores=E@v.numpy();ix=np.argsort(-scores)[:count]
    out.append([[ids[i],round(float(scores[i]),5)] for i in ix])
  return out
