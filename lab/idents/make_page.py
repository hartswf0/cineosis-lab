"""Writes lab/idents.html: the 17 film idents and the 45 sign idents, each card in its own colour and naming the web it
weaves, with a reel that plays either set in order."""
import json, os, re, html, sys
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import render as R
SITE = 'https://hartswf0.github.io/cineosis-lab/lab/'
plan = {p['i']: p for p in json.load(open(os.path.join(HERE, 'plan.json')))}
E = lambda s: html.escape(str(s))

def source_name(clip, title):
    if title: return title
    m = re.search(r'/sources/([a-z][a-z0-9-]+)/', clip)
    if m and not re.match(r'^[0-9a-f]{8}-', m.group(1)): return m.group(1).replace('-', ' ').title()
    if clip.startswith('republic/'): return 'The Republic, scored episode'
    return 'unnamed archive reel'

films = [s for s in R.film_specs() if os.path.exists(os.path.join(HERE, s['key'] + '.mp4'))]
signs = [s for s in R.sign_specs() if os.path.exists(os.path.join(HERE, s['key'] + '.mp4'))]

out, unit = [], None
for s in films:
    p = plan[s['i']]
    if p['unit'] != unit:
        if unit is not None: out.append('</div>')
        unit = p['unit']; out.append(f'<h3 class="unit">{E(unit)}</h3><div class="grid">')
    names = [source_name(c, t) for c, t in zip(p['clips'], p['titles'])]
    out.append(f'''<article class="id" id="{s['key']}" style="--a:{s['accent']}">
  <video src="idents/{s['key']}.mp4" poster="idents/{s['key']}.jpg" muted playsinline loop preload="none"></video>
  <div class="meta"><div class="top"><span class="o"></span><span class="badge">{E(s['corner'])}</span><span class="web">{E(s['fig_note'])}</span></div>
  <h4>{E(s['title'])}</h4><p class="v">Makes visible {E(p['v'])}.</p>
  <p class="src"><b>Blinked past</b> {E(' · '.join(dict.fromkeys(names[:-1])))}</p>
  <p class="src"><b>Winked at</b> {E(names[-1])}</p>
  <a class="go" href="{E(SITE + p['href'])}">Watch the film</a></div></article>''')
if unit is not None: out.append('</div>')
film_html = ''.join(out)

DOM_ORDER = ['perception', 'affect', 'action', 'reflection', 'mental', 'time', 'break', 'read']
DOM_NAME = {'perception': 'Perception', 'affect': 'Affection', 'action': 'Action', 'reflection': 'Reflection', 'mental': 'Mental',
            'time': 'Time', 'break': 'Break', 'read': 'Readable'}
out = []
for dom in DOM_ORDER:
    group = [s for s in signs if s['dom'] == dom]
    if not group: continue
    out.append(f'<h3 class="unit" style="--a:{group[0]["accent"]}"><i></i>{E(DOM_NAME[dom])} <span>{E(R.FIG_NOTE[dom])}</span></h3><div class="grid signs">')
    for s in group:
        out.append(f'''<article class="id sign" id="{s['key']}" style="--a:{s['accent']}">
  <video src="idents/{s['key']}.mp4" poster="idents/{s['key']}.jpg" muted playsinline loop preload="none"></video>
  <div class="meta"><div class="top"><span class="o"></span><span class="tile"><small>{E(s['n'])}</small>{E(s['corner'])}</span><h4>{E(s['title'])}</h4></div>
  <p class="v">{E(s['gloss'][0].upper() + s['gloss'][1:])}.</p>
  <p class="q">{E(s['question'])}</p>
  <p class="src"><b>Winked at</b> {E(s['notes'][-1])}</p></div></article>''')
    out.append('</div>')
sign_html = ''.join(out)

sheet_html = ''.join(f'<a href="#{x["key"]}"><img src="idents/{x["key"]}.jpg" alt="" loading="lazy"><span>{E(x["corner"])} · {E(x["title"])}</span></a>' for x in films + signs)
reel = {'films': [dict(k=s['key'], t=f"{s['corner']}  {s['title']}", a=s['accent']) for s in films],
        'signs': [dict(k=s['key'], t=f"{s['n']} {s['corner']}  {s['title']}", a=s['accent']) for s in signs]}

page = f'''<meta charset="utf-8">
<title>Cineosis Idents</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#ece7dd;--paper:#f4efe6;--card:#f8f4ed;--ink:#17140f;--mute:#857e72;--line:#d8d0c2;--red:#e0483a;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#121110;--paper:#1c1a17;--card:#1f1d19;--ink:#ece6da;--mute:#8d867a;--line:#36322b;--red:#ea5444;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#121110;--paper:#1c1a17;--card:#1f1d19;--ink:#ece6da;--mute:#8d867a;--line:#36322b;--red:#ea5444;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:19px/1.5 "Cormorant Garamond",Georgia,serif;margin:0}}
.wrap{{max-width:1180px;margin:0 auto;padding-inline:20px;padding-block:52px 110px}}
.mono{{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--mute)}}
h1{{font-weight:400;font-size:clamp(42px,7vw,76px);line-height:1;margin:12px 0 16px}}
h2{{font-weight:400;font-size:40px;margin:80px 0 6px;text-wrap:balance}}
h3.unit{{font-weight:400;font-size:26px;margin:44px 0 0;padding-top:12px;border-top:1px solid var(--line);display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}}
h3.unit i{{width:13px;height:13px;border-radius:50%;background:var(--a);box-shadow:0 0 0 2px var(--bg),0 0 0 3.5px var(--ink);display:inline-block;align-self:center}}
h3.unit span{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.1em;color:var(--mute);text-transform:uppercase}}
h4{{font-weight:500;font-size:25px;line-height:1.1;margin:4px 0 6px;text-wrap:balance}}
p{{margin:0 0 10px;max-width:64ch}}
.lede{{font-size:22px}}
.reel{{margin-top:28px;border:1px solid var(--line);background:#f4efe6}}
.reel video{{display:block;width:100%;aspect-ratio:16/9;height:auto;background:#f4efe6}}
.bar{{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:10px 12px;background:var(--card);border-top:1px solid var(--line);font-family:"IBM Plex Mono",monospace;font-size:12px}}
.bar button{{font:inherit;background:var(--ink);color:var(--paper);border:0;padding:6px 12px;cursor:pointer}}
.bar button.set{{background:none;color:var(--mute);border:1px solid var(--line)}}
.bar button.set.on{{color:var(--ink);border-color:var(--ink)}}
.bar .now{{color:var(--mute);min-width:0;flex:1 1 220px}}
.dots{{display:flex;gap:4px;flex-wrap:wrap;padding:0 12px 12px;background:var(--card)}}
.dots i{{width:12px;height:12px;border-radius:50%;border:1.5px solid var(--ink);cursor:pointer;display:block}}
.dots i.on{{background:var(--c)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:16px;margin-top:14px}}
.grid.signs{{grid-template-columns:repeat(auto-fill,minmax(min(100%,270px),1fr))}}
.id{{background:var(--card);border:1px solid var(--line);min-width:0;display:flex;flex-direction:column}}
.id video{{display:block;width:100%;aspect-ratio:16/9;height:auto;background:#f4efe6;cursor:pointer}}
.meta{{padding:12px 14px 16px;display:flex;flex-direction:column;flex:1}}
.top{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.badge{{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink);border:1px solid var(--ink);padding:1px 7px}}
.o{{width:13px;height:13px;border-radius:50%;background:var(--a);box-shadow:0 0 0 2px var(--card),0 0 0 3.5px var(--ink);flex:none}}
.web{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;color:var(--mute);text-transform:uppercase}}
.tile{{width:46px;height:46px;flex:none;border:1px solid var(--ink);display:grid;place-items:center;position:relative;font-size:22px}}
.tile small{{position:absolute;left:3px;top:0;font-family:"IBM Plex Mono",monospace;font-size:9px}}
.sign h4{{font-size:21px;margin:0;flex:1;min-width:0}}
.v{{font-style:italic;font-size:17.5px;margin-top:6px}}
.q{{font-size:16px;color:var(--mute)}}
.src{{font-size:15px;color:var(--mute);line-height:1.35;margin-bottom:6px}}
.src b{{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;font-weight:500;color:var(--ink);margin-right:6px}}
.go{{margin-top:auto;padding-top:8px;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink);text-decoration:none;border-bottom:1px solid var(--red);align-self:flex-start}}
.rule{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 28px;margin-top:22px;font-size:17px}}
.rule div{{min-width:0}}
.rule b{{display:block;font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;font-weight:500}}
.sheet{{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:6px;margin-top:28px}}
.sheet a{{display:block;position:relative;text-decoration:none;color:var(--ink)}}
.sheet img{{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;border:1px solid var(--line)}}
.sheet span{{font-family:"IBM Plex Mono",monospace;font-size:9.5px;color:var(--mute);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.foot{{margin-top:64px;padding-top:14px;border-top:1px solid var(--line);font-size:16px;color:var(--mute)}}
</style>
<div class="wrap">
  <div class="mono">Cineosis Lab · Idents</div>
  <h1>Sixty-two idents</h1>
  <p class="lede">A short for each of the 17 films and each of the 45 signs. In every one the mark comes down on its thread holding its number or symbol, then opens its eye onto archive shots and cuts between them by blinking. It holds on one shot and winks at it, then names itself.</p>
  <div class="rule">
    <div><b>Colour lives in the O</b>Each film has its own colour; each sign takes its family's colour from the periodic table. It appears only inside the O, as the tone of the archive shots. Outside the O there is only paper, ink and the red thread.</div>
    <div><b>Figure</b>What tells them apart at a glance is the figure: how many Os, where they sit, how big, and the path the red thread takes. Nine eyes around one O for the machines, three Os racing for choosing, a voyage thread for the Odyssey, a broken O for a break.</div>
    <div><b>Rhythm</b>The cuts keep the film's own time. Choosing cuts fast, Drift slows down, the voice cuts on an uneven beat.</div>
    <div><b>Blink and wink</b>Every cut is a blink. The one shot the ident holds is winked at. Red is only the thread, and nothing is drawn over a picture.</div>
  </div>
  <div class="sheet">{sheet_html}</div>
  <div class="reel"><video id="reel" playsinline muted preload="metadata"></video>
    <div class="bar"><button id="rp">play all</button><button class="set on" data-s="films">17 films</button><button class="set" data-s="signs">45 signs</button><span class="now" id="now"></span></div>
    <div class="dots" id="dots"></div></div>
  <h2>The films</h2>
  {film_html}
  <h2>The signs</h2>
  <p>Each sign blinks through five of its six vetted archive shots and winks at the sixth. The note under each card says why that shot carries the sign.</p>
  {sign_html}
  <div class="foot">The idents are silent. Archive shots come from each film's own data, or from each sign's vetted reference picks. Where a reel has no recorded title it is listed as unnamed. The sign glosses and questions are the lab's own wording.</div>
</div>
<script>
const SETS={json.dumps(reel)};
const reel=document.getElementById('reel'),now=document.getElementById('now'),dots=document.getElementById('dots'),rp=document.getElementById('rp');
let set='films',k=0;
function build(){{dots.innerHTML='';SETS[set].forEach((f,j)=>{{const d=document.createElement('i');d.style.setProperty('--c',f.a);d.title=f.t;d.onclick=()=>{{load(j);reel.play().catch(()=>{{}})}};dots.appendChild(d)}});load(0);}}
function load(j){{k=j;const f=SETS[set][j];reel.src='idents/'+f.k+'.mp4';reel.poster='idents/'+f.k+'.jpg';
  now.textContent=(j+1)+' / '+SETS[set].length+'  ·  '+f.t;[...dots.children].forEach((d,i)=>d.classList.toggle('on',i===j));}}
document.querySelectorAll('.set').forEach(b=>b.onclick=()=>{{set=b.dataset.s;document.querySelectorAll('.set').forEach(x=>x.classList.toggle('on',x===b));build();}});
build();
rp.onclick=()=>{{if(reel.paused)reel.play().catch(()=>{{}});else reel.pause();}};
reel.onplay=()=>rp.textContent='pause';reel.onpause=()=>rp.textContent='play all';
reel.onended=()=>{{if(k<SETS[set].length-1){{load(k+1);reel.play().catch(()=>{{}});}}else load(0);}};
const io=new IntersectionObserver(es=>es.forEach(e=>{{const v=e.target;if(e.isIntersecting){{v.preload='auto';v.play().catch(()=>{{}});}}else v.pause();}}),{{threshold:.6}});
document.querySelectorAll('.id video').forEach(v=>{{io.observe(v);v.onclick=()=>{{v.currentTime=0;v.play().catch(()=>{{}})}};}});
</script>
'''
open(os.path.join(LAB, 'idents.html'), 'w').write(page)
print('idents.html', len(films), 'films', len(signs), 'signs')
