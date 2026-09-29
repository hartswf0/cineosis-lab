// CLIP byte-pair tokenizer, using OpenCLIP's exact merge vocabulary.
export function createTokenizer(mergeText){
 const bytes=[];for(let b=33;b<=126;b++)bytes.push(b);for(let b=161;b<=172;b++)bytes.push(b);for(let b=174;b<=255;b++)bytes.push(b);
 const chars=bytes.map(b=>b);let n=0;for(let b=0;b<256;b++)if(!bytes.includes(b)){bytes.push(b);chars.push(256+n++);}
 const map=new Map(bytes.map((b,i)=>[b,String.fromCodePoint(chars[i])])),v=[...map.values()],merges=mergeText.split('\n').slice(1,49152-256-2+1).map(s=>s.trim().split(/\s+/));
 const vocab=[...v,...v.map(x=>x+'</w>'),...merges.map(x=>x.join('')),'<start_of_text>','<end_of_text>'],encoder=new Map(vocab.map((x,i)=>[x,i])),ranks=new Map(merges.map((x,i)=>[x.join(' '),i])),cache=new Map();
 function bpe(token){if(cache.has(token))return cache.get(token);let w=[...token];w[w.length-1]+='</w>';while(w.length>1){let best=Infinity,at=-1;for(let i=0;i<w.length-1;i++){const r=ranks.get(w[i]+' '+w[i+1]);if(r!==undefined&&r<best){best=r;at=i;}}if(at<0)break;const a=w[at],b=w[at+1],next=[];for(let i=0;i<w.length;i++){if(w[i]===a&&w[i+1]===b){next.push(a+b);i++;}else next.push(w[i]);}w=next;}const ids=w.map(x=>encoder.get(x));cache.set(token,ids);return ids;}
 const encode=text=>{const ids=[];text=text.normalize('NFC').replace(/\s+/g,' ').trim().toLowerCase();for(const word of text.match(/<start_of_text>|<end_of_text>|'s|'t|'re|'ve|'m|'ll|'d|[\p{L}]+|[\p{N}]|[^\s\p{L}\p{N}]+/giu)||[]){if(encoder.has(word)&&word.startsWith('<'))ids.push(encoder.get(word));else ids.push(...bpe([...new TextEncoder().encode(word)].map(b=>map.get(b)).join('')));}return ids;};
 const tokenize=text=>{const ids=[49406,...encode(text).slice(0,75),49407];while(ids.length<77)ids.push(0);return ids;};
 tokenize.segments=text=>{const all=encode(text),out=[];for(let i=0;i<Math.max(1,all.length);i+=75){const row=[49406,...all.slice(i,i+75),49407];while(row.length<77)row.push(0);out.push(row);}return out;};return tokenize;
}
