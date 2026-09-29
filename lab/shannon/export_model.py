"""Export the matching text tower, quantize, and check embedding agreement."""
from pathlib import Path
import numpy as np, torch, open_clip
from onnxruntime.quantization import quantize_dynamic, QuantType
import onnxruntime as ort
P=Path(__file__).parent;torch.set_num_threads(4)
m,_,_=open_clip.create_model_and_transforms('ViT-B-32',pretrained='laion2b_s34b_b79k',cache_dir=str(P.parent/'models'));m.eval()
class Text(torch.nn.Module):
 def __init__(self,m):super().__init__();self.m=m
 def forward(self,tokens):return self.m.encode_text(tokens,normalize=True)
w=Text(m).eval();tokens=open_clip.get_tokenizer('ViT-B-32')(['a person waits beside a window','water ripples around a frog','a crowd leaves an empty square'])
raw=P.parent/'models/text-fp32.onnx';out=P/'text-int8.onnx'
with torch.inference_mode():
 torch.onnx.export(w,(tokens[:1],),str(raw),input_names=['tokens'],output_names=['embedding'],dynamic_axes={'tokens':{0:'batch'},'embedding':{0:'batch'}},opset_version=17,dynamo=False)

import onnx
from onnx import numpy_helper,helper
m=onnx.load(str(raw));prefix=[]
for weight in list(m.graph.initializer):
 w=numpy_helper.to_array(weight)
 if w.dtype!=np.float32 or w.ndim!=2 or w.size<200000:continue
 scale=np.maximum(np.max(np.abs(w),axis=1)/127,1e-10).astype('float32');q=np.round(w/scale[:,None]).clip(-127,127).astype('int8');m.graph.initializer.remove(weight)
 m.graph.initializer.extend([numpy_helper.from_array(q,weight.name+'.q'),numpy_helper.from_array(scale,weight.name+'.scale'),numpy_helper.from_array(np.zeros(w.shape[0],dtype='int8'),weight.name+'.zero')]);prefix.append(helper.make_node('DequantizeLinear',[weight.name+'.q',weight.name+'.scale',weight.name+'.zero'],[weight.name],axis=0))
for n in reversed(prefix):m.graph.node.insert(0,n)
onnx.save(m,str(P/'text-int8.onnx'))
t=open_clip.get_tokenizer('ViT-B-32')(['a person waits beside a window','water ripples around a frog','a crowd leaves an empty square']).numpy();a=ort.InferenceSession(str(P/'text-int8.onnx')).run(None,{'tokens':t})[0];b=ort.InferenceSession(str(raw)).run(None,{'tokens':t})[0];cos=(a*b).sum(1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1));print(cos,'bytes', (P/'text-int8.onnx').stat().st_size,flush=True);assert min(cos)>.985
E=np.load(P.parent/'cache/emb.npy').astype('float32');E/=np.linalg.norm(E,axis=1,keepdims=True);np.round(E*127).clip(-127,127).astype('int8').tofile(P/'image-vectors.i8')
import open_clip.tokenizer
(P/'bpe.txt').write_text(gzip.open(open_clip.tokenizer.default_bpe(),'rt').read())

# Split below common API transport limits without changing model bytes.
data=out.read_bytes();size=4*1024*1024
for i,start in enumerate(range(0,len(data),size)):(P/f"text-model-{i:02}.bin").write_bytes(data[start:start+size])
import json
(P/"text-model.json").write_text(json.dumps({"parts":[f"text-model-{i:02}.bin" for i in range((len(data)+size-1)//size)],"bytes":len(data)}))
out.unlink()
