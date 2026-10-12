"""THE REPUBLIC · the episode pages. Each rendered episode gets its own page (the film, scored or voices only, switching in place;
the cast as found in the archive; the score and why), and markov-republic.html lists them all.
usage: republic/.tts/bin/python republic/pilot/make_episodes.py"""
import json, os, re, subprocess, html
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); L = os.path.dirname(R)
PL = json.load(open(os.path.join(R, "planes.json")))
WORDS = "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE THIRTEEN FOURTEEN FIFTEEN SIXTEEN SEVENTEEN".split()
esc = html.escape
def dur(p):
    try: return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())
    except Exception: return 0
eps = []
for n in range(1, 18):
    j = os.path.join(H, f"ep{n:02d}.picked.json"); mp = os.path.join(H, f"ep{n:02d}-score.mp4")
    if not (os.path.exists(j) and os.path.exists(mp)): continue
    c = json.load(open(j)); d = dur(mp); poster = os.path.join(H, f"ep{n:02d}-poster.jpg")
    if not os.path.exists(poster):
        t = next((b.get("_t", 0) for b in []), 0) or d * .42
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.1f}", "-i", mp, "-frames:v", "1", "-q:v", "3", poster])
    eps.append({"n": n, "c": c, "d": d})
SCR = json.load(open(os.path.join(R, "script.json")))["episodes"]; series = {e["id"]: e.get("series") or "" for e in SCR}
CSS = """:root{--bg:#0c0806;--ink:#f4e9dc;--dim:#a8968a;--line:#2e211b;--gold:#f2c14e}
*{box-sizing:border-box;margin:0;padding:0}html,body{background:var(--bg);color:var(--ink);font:13px/1.55 ui-monospace,'IBM Plex Mono',monospace}
a{color:var(--gold)}main{max-width:1100px;margin:0 auto;padding:18px 16px 60px;display:flex;flex-direction:column;gap:16px}
.k{font-size:10.5px;letter-spacing:.22em;color:#e0572a}h1{font:clamp(20px,3.4vw,34px)/1.05 'Arial Black',Impact,sans-serif}
video{width:100%;aspect-ratio:16/9;background:#000;display:block}
.ver{display:flex;gap:6px;flex-wrap:wrap}.ver button{font:600 10.5px ui-monospace,monospace;letter-spacing:.12em;color:var(--dim);background:none;border:1px solid var(--line);padding:8px 12px;border-radius:18px;cursor:pointer}
.ver button.on{color:#0c0806;background:var(--gold);border-color:var(--gold)}
h2{font:11px ui-monospace,monospace;letter-spacing:.2em;color:var(--dim);margin-top:8px}
.cast{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.cast div{border:1px solid var(--line);border-radius:6px;padding:10px;display:flex;flex-direction:column;gap:6px;align-items:flex-start}
.cast img{height:110px;max-width:100%;object-fit:contain;filter:drop-shadow(0 0 1px #f1e6d2) drop-shadow(0 6px 10px rgba(0,0,0,.5))}
.cast b{font-size:11px;letter-spacing:.12em}.cast small{color:var(--dim);font-size:10.5px}
.score{display:flex;flex-direction:column;gap:4px;color:var(--dim)}.score b{color:var(--ink);font-weight:600}
.nav{display:flex;justify-content:space-between;gap:10px;border-top:1px solid var(--line);padding-top:14px}
p{color:var(--dim);max-width:62em}"""
HEAD = lambda title, desc, img: f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="https://hartswf0.github.io/cineosis-lab/lab/{img}"><meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0c0806">
<link rel="icon" href="republic/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="republic/icon-180.png"><style>{CSS}</style></head><body><main>"""
page = lambda n: f"markov-republic-ep{n:02d}.html"
for i, e in enumerate(eps):
    c, n = e["c"], e["n"]; stage = [b["who"] for b in c["beats"] if b["k"] == "intro"]
    cast = "".join(f"""<div><img src="{esc(PL['cast'][w][0]['f'].split('?')[0])}" alt="{esc(w)}"><b>{esc(w)}</b><small>as found in {esc(PL['cast'][w][0].get('title', ''))}{' · ' + str(PL['cast'][w][0]['year']) if PL['cast'][w][0].get('year') else ''}</small></div>""" for w in stage if PL["cast"].get(w))
    seen, sc = set(), []
    for p in c.get("score", []):
        if p["title"] not in seen: seen.add(p["title"]); sc.append(f"<div><b>{esc(p['title'])}</b> · {esc(', '.join(p['mood']))}</div>")
    prev_ = f'<a href="{page(eps[i - 1]["n"])}">← {esc(eps[i - 1]["c"]["title"])}</a>' if i else '<span></span>'
    next_ = f'<a href="{page(eps[i + 1]["n"])}">{esc(eps[i + 1]["c"]["title"])} →</a>' if i + 1 < len(eps) else '<span></span>'
    out = HEAD(f"The Republic · {c['title'].title()}", f"THE REPUBLIC, episode {n}: {c['title']}. A narrator, cut-out figures on one stage, and the archive's citizens. {round(e['d'] / 60, 1)} minutes.", f"republic/pilot/ep{n:02d}-poster.jpg") + f"""
<div class="k">THE REPUBLIC · EPISODE {WORDS[n - 1]}{' · ' + esc(series.get(c['id'], '')) if series.get(c['id']) else ''} · <a href="markov-republic.html">ALL EPISODES</a></div>
<h1>{esc(c['title'])}</h1>
<div class="ver"><button data-f="republic/pilot/ep{n:02d}-score.mp4" class="on">WITH SCORE · D-A-E</button><button data-f="republic/pilot/ep{n:02d}.mp4">VOICES ONLY</button></div>
<video src="republic/pilot/ep{n:02d}-score.mp4" poster="republic/pilot/ep{n:02d}-poster.jpg" controls playsinline preload="metadata"></video>
<p>A narrator tells the story. The characters are figures cut from archival films, each first shown where the archive found it, then lifted onto one stage to speak the screenplay's lines. The archive speaks as the Republic's citizens, in their own pictures and voices.</p>
<h2>THE CAST, AS FOUND</h2><div class="cast">{cast}</div>
<h2>THE SCORE · D-A-E · HONED FOR FILM, CHOSEN BY WHAT EACH MOVEMENT SAYS AND SHOULD FEEL</h2><div class="score">{''.join(sc)}</div>
<div class="nav">{prev_}{next_}</div>
</main><script>const v=document.querySelector('video');document.querySelectorAll('.ver button').forEach(b=>b.onclick=()=>{{const t=v.currentTime,p=!v.paused;v.src=b.dataset.f;v.addEventListener('loadedmetadata',()=>{{v.currentTime=t;if(p)v.play()}},{{once:true}});document.querySelectorAll('.ver button').forEach(x=>x.classList.toggle('on',x===b))}});</script></body></html>"""
    open(os.path.join(L, page(n)), "w").write(out)
cards = "".join(f"""<a class="ep" href="{page(e['n'])}"><img src="republic/pilot/ep{e['n']:02d}-poster.jpg" alt="" loading="lazy"><span><i>{e['n']:02d} · {round(e['d'] / 60, 1)} MIN</i><b>{esc(e['c']['title'])}</b><small>{esc(series.get(e['c']['id'], ''))}</small></span></a>""" for e in eps)
idx = HEAD("The Republic", "THE REPUBLIC: seventeen episodes from the writers' room, cut from the archive. A narrator, cut-out figures, and the archive's citizens.", "republic/pilot/ep01-poster.jpg").replace("</style>", """.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.ep{display:flex;flex-direction:column;gap:8px;text-decoration:none;color:var(--ink);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.ep img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}.ep span{padding:0 12px 12px;display:flex;flex-direction:column;gap:3px}
.ep i{font-style:normal;font-size:10px;letter-spacing:.16em;color:#e0572a}.ep b{font:14px/1.15 'Arial Black',Impact,sans-serif}.ep small{color:var(--dim);font-size:10.5px}</style>""") + f"""
<div class="k">CINEOSIS LAB · MARKOV FOUND</div><h1>THE REPUBLIC</h1>
<p>Seventeen Republics from the writers' room, each cut as a short film from the archive: a narrator tells the story; the characters are figures cut from archival films, each introduced where the archive found it; the archive speaks as the Republic's citizens; the score is D-A-E · Honed for Film, chosen by what each scene says. Also: <a href="markov-found-republic.html">the four versions</a> · <a href="markov-sam-republic.html">the multiplane</a> · <a href="https://hartswf0.github.io/the-republic/screenplay.html">the screenplay</a>.</p>
<div class="grid">{cards}</div></main></body></html>"""
open(os.path.join(L, "markov-republic.html"), "w").write(idx)
open(os.path.join(L, "markov-republic-pilot.html"), "w").write('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=markov-republic-ep01.html"><link rel="canonical" href="markov-republic-ep01.html"><a href="markov-republic-ep01.html">The Republic · Episode One</a>')
print(len(eps), "episode pages · index")
