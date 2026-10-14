import json,re,os,collections
U=re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
M=re.compile(r'(https://pub-[^"\s]+?\.mp4|republic/[^"\s]+?\.mp4)')
BAN=re.compile(r'kinderen|all my babies|exhibit 3|jfk',re.I)
have=set(f[:-4] for f in os.listdir('clips') if f.endswith('.mp4'))
titles={s['id']:s.get('title','') for s in json.load(open('lab-data.json'))['shots']}
def refs(text):
  out=[]
  for m in M.finditer(text): out.append((m.group(1),text[max(0,m.start()-500):m.end()+300]))
  for m in U.finditer(text):
    u=m.group(0)
    if u in have: out.append(('clips/'+u+'.mp4',text[max(0,m.start()-500):m.end()+300]+titles.get(u,'')))
  return out
used=set()
def pick(texts,n=6,cap=99):
  out=[];seen=set()
  for t in texts:
    k0=len(out)
    rs=refs(t);c=collections.Counter(r for r,_ in rs);ctx={};first={}
    for i,(r,x) in enumerate(rs): ctx.setdefault(r,'');ctx[r]+=x;first.setdefault(r,i)
    ranked=sorted(c,key=lambda r:(r in used,-c[r],first[r]))
    for r in ranked:
      if BAN.search(ctx[r]): continue
      key=r.split('/sources/')[1].split('/')[0] if '/sources/' in r else r
      if key in seen: continue
      seen.add(key);out.append(r)
      if len(out)==n: return out
      if len(out)-k0>=cap: break
  return out
R=lambda p:open(p).read()
tk=json.load(open('explain/ep/takes.json'))
films=json.load(open('idents/films.json'))
src={'machines.html':[R('explain/machines/machines.json'),R('explain/machines/pick.json')],'episode-1.html':[R('explain/ep/ep1.json')],'lesson-4.html':[R('explain/lesson/l4.json'),R('explain/ep/ep5.json')],'lesson-7.html':[R('explain/lesson/l7.json')],'lesson-8.html':[R('explain/lesson/l8.json')],'room-syntagma.html':[R('explain/ep/metz.json'),R('explain/ep/ep5.json')],'episode-5.html':[R('explain/ep/ep5.json')],'room-syzygy.html':[R('explain/lesson/syz.json')],'room-cast.html':[R('explain/lesson/cast.json')],'room-chemistry.html':[R('explain/lesson/chem.json')],'episode-4.html':[R('explain/ep/ep4.json')],'episode-7.html':[R('explain/ep/ep7.json')]}
for t in ['suite','scenes','cineosis','drift']: src['wygwyl-take.html?t='+t]=[json.dumps(tk[t])]
src['episode-5.html?part=compare']=[json.dumps(tk[t]) for t in ['suite','scenes','cineosis','drift']]
plan=[]
for i,f in enumerate(films):
  cl=pick(src[f['href']],cap=2 if 'compare' in f['href'] else 99);used.update(cl)
  plan.append(dict(i=i+1,**f,clips=cl,titles=[titles.get(U.search(c).group(0),'') if U.search(c) and c.startswith('clips/') else '' for c in cl]))
  print(f['n'],f['t'],len(cl),[c[-20:] for c in cl[:3]])
json.dump(plan,open('idents/plan.json','w'),indent=1,ensure_ascii=False)
