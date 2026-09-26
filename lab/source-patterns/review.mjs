export function validateReviews(payload, data, types){
  if(payload?.format!=='cineosis-source-patterns-review/1'||!payload.annotations||typeof payload.annotations!=='object'||Array.isArray(payload.annotations))throw Error('Expected a source-pattern review export.');
  const out={};
  for(const [id,r] of Object.entries(payload.annotations)){
    const p=data.passages.find(x=>x.id===id);
    if(!p||JSON.stringify(r.members)!==JSON.stringify(p.members)||JSON.stringify(r.interval)!==JSON.stringify(p.interval))throw Error('Source interval or members do not match: '+id);
    if(!types.includes(r.type)||!types.includes(r.rival)||!['draft','reviewed'].includes(r.status))throw Error('Invalid reading state.');
    for(const k of ['evidence','counterevidence','reader','structure'])if(typeof r[k]!=='string'||r[k].length>20000)throw Error('Invalid '+k);
    if(!['unknown','unspecified','successive','simultaneous','coexisting'].includes(r.relation))throw Error('Invalid relation.');
    if(r.status==='reviewed'&&(!r.fullContextAttested||!r.reader.trim()||!r.evidence.trim()))throw Error('A reviewed reading requires evidence, reader and context attestation.');
    out[id]=structuredClone(r);
  }
  return out;
}
