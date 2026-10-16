"""Builds lab/bolas/ in the cineosis-lab repo: one page per Bolas test, a minimal index, and a notes page.
Each page gets one quiet strip at the top: previous, the set, next. Nothing else is added."""
import os, re, shutil, json, html
SCR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.expanduser('~/cineosis-lab/lab')
OUT = os.path.join(REPO, 'bolas')

SET = [  # slug, source file in the scratchpad (None = page already on the site), title, one line
    ('sign-marks', 'cineosis-signs', 'Sign Marks', 'One mark for each of the 45 signs, and a first avatar.'),
    ('bolas', 'bolas', 'Bolas', 'The spider from Spider Engineers, 1956, and the red thread.'),
    ('system', 'bolas-system', 'Bolas, as a System', 'Brands, materials, scales, the spider turning into the OA.'),
    ('bible', 'bolas-bible', 'Operations Bible', 'Forty-four operations in five drawing styles.'),
    ('screen-test', 'bolas-screentest', 'Screen Test', 'A countdown in the O, expressions, twitch against wink.'),
    ('line-circle-dot', 'oa-eternal', 'Line, Circle, Dot', 'Three elements; one line read as reel, timeline and web.'),
    ('wink-blink', 'wink-blink', 'Wink, Not Blink', 'A blink is the machine and the cut; a wink is a reading.'),
    ('wink-blink-studio', 'wink-blink-studio', 'Wink Blink Studio', 'Ten animated shorts and twenty-four constructions.'),
    ('../idents', None, 'Idents', 'Sixty-two idents, one per film and sign, on archive footage.'),
    ('at-work', 'bolas-scenes', 'Bolas at Work', 'The body becomes the operation; scenes, a wall, teams.'),
    ('pixel', 'bolas-pixel', 'Bolas Pixel', 'Thirty-two pixel icons; body symbols and web symbols.'),
    ('webs-that-matter', 'webs-that-matter', 'Webs That Matter', 'Signs as their differences; film webs spun from data.'),
    ('web-of-cineosis', 'web-of-cineosis', 'The Web of Cineosis', 'The whole ontology as a circle, web types and radars.'),
    ('webs-of-significance', 'webs-of-significance', 'Webs of Significance', 'One real line, its questions, finds and choices.'),
    ('editing-table', None, 'The Editing Table', 'One shot placed while another waits: a scene you steer, and your own cut.'),
]

NAV_CSS = """<style>
.bset{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:10px 20px;font:13px/1.3 "IBM Plex Mono",ui-monospace,Menlo,monospace;border-bottom:1px solid rgba(128,120,108,.35);background:inherit}
.bset a{color:inherit;text-decoration:none;padding:4px 0;border-bottom:1px solid transparent}
.bset a:hover,.bset a:focus-visible{border-bottom-color:#e0483a;outline:none}
.bset .here{opacity:.6;margin-right:auto}
.bset [aria-disabled]{opacity:.3}
</style>"""

def nav(i, depth=''):
    prev_ = SET[i - 1] if i > 0 else None
    next_ = SET[i + 1] if i < len(SET) - 1 else None
    link = lambda s: f"{depth}{s[0]}.html"
    p = f'<a href="{link(prev_)}" rel="prev">← {html.escape(prev_[2])}</a>' if prev_ else '<span aria-disabled="true">←</span>'
    n = f'<a href="{link(next_)}" rel="next">{html.escape(next_[2])} →</a>' if next_ else '<span aria-disabled="true">→</span>'
    return (NAV_CSS + f'<nav class="bset" aria-label="Bolas set">'
            f'<a href="{depth}index.html">Bolas set</a><span class="here">{i + 1:02d} / {len(SET)}</span>{p}{n}</nav>')

def page(raw, i):
    raw = raw.replace('poster="idents/', 'poster="../idents/').replace('src="idents/', 'src="../idents/')
    head_end = raw.find('</style>')
    # the page's own <meta>, <title>, fonts and <style> stay as they are; the strip goes in front of the content
    cut = raw.find('\n', head_end) + 1 if head_end >= 0 else 0
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + raw[:cut] + '</head>\n<body>\n' + nav(i) + '\n' + raw[cut:] + '\n</body>\n</html>\n')

os.makedirs(OUT, exist_ok=True)
for i, (slug, src, title, line) in enumerate(SET):
    if not src: continue
    raw = open(os.path.join(SCR, src + '.html')).read()
    open(os.path.join(OUT, slug + '.html'), 'w').write(page(raw, i))

# the idents page already on the site joins the sequence
idp = os.path.join(REPO, 'idents.html')
raw = open(idp).read()
raw = re.sub(r'<style>\n\.bset.*?</nav>\n', '', raw, flags=re.S)
i = next(k for k, s in enumerate(SET) if s[0] == '../idents')
strip = nav(i, depth='bolas/').replace('href="bolas/../idents.html"', 'href="idents.html"')
raw = raw.replace('<div class="wrap">', strip + '\n<div class="wrap">', 1)
open(idp, 'w').write(raw)

# assets
for d in ('sig/th', 'archive/shots'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
    for f in os.listdir(os.path.join(SCR, d)):
        if f.endswith('.jpg'): shutil.copy(os.path.join(SCR, d, f), os.path.join(OUT, d, f))

# notes: the long page, with links pointing at the pages on the site
notes = open(os.path.join(SCR, 'bolas-set.html')).read()
local = {src: (slug + '.html' if src else '../idents.html') for slug, src, *_ in SET}
local['idents-page'] = '../idents.html'
notes = notes.replace("const A='https://claude.ai/artifact/';", "const A='https://claude.ai/artifact/';const LOCAL=" + json.dumps(local) + ";")
notes = notes.replace('${A+s.id}', '${LOCAL[s.f]||A+s.id}').replace("a.href=A+s.id;a.target='_blank';", "a.href=LOCAL[s.f]||A+s.id;")
notes = notes.replace(' target="_blank"', '')
notes = notes.replace('<h1>The Bolas Set</h1>', '<p style="margin:0 0 6px"><a href="index.html" style="font-family:\'IBM Plex Mono\',monospace;font-size:13px">← Bolas set</a></p>\n  <h1>Notes on the set</h1>')
notes = notes.replace('<title>The Bolas Set</title>', '<title>Bolas Set Notes</title>')
cut = notes.find('\n', notes.find('</style>')) + 1
open(os.path.join(OUT, 'notes.html'), 'w').write('<!doctype html>\n<html lang="en">\n<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + notes[:cut] + '</head>\n<body>\n' + notes[cut:] + '\n</body>\n</html>\n')

# the index: one list, one action per item
items = '\n'.join(
    f'<li><a href="{slug}.html"><span class="n">{k + 1:02d}</span><span class="t">{html.escape(title)}</span><span class="l">{html.escape(line)}</span></a></li>'
    for k, (slug, src, title, line) in enumerate(SET))
INDEX = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bolas Set</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root{{--bg:#f4efe6;--ink:#17140f;--mute:#6e675c;--line:#d6cebf;--red:#c73a2d;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141210;--ink:#ece6da;--mute:#a59d90;--line:#36322b;--red:#ef6a5c;color-scheme:dark}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:20px/1.45 "Cormorant Garamond",Georgia,serif}}
main{{max-width:720px;margin:0 auto;padding:64px 20px 96px}}
h1{{font-weight:400;font-size:44px;line-height:1;margin:0 0 10px}}
.thread{{display:block;width:2px;height:48px;background:var(--red);margin:0 0 18px 1px}}
p{{margin:0 0 36px;color:var(--mute);max-width:52ch}}
ol{{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}}
li{{border-bottom:1px solid var(--line)}}
li a{{display:grid;grid-template-columns:3ch minmax(0,1fr);column-gap:16px;padding:14px 4px;color:inherit;text-decoration:none}}
li a:hover .t,li a:focus-visible .t{{text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:4px}}
li a:focus-visible{{outline:2px solid var(--red);outline-offset:2px}}
.n{{font:13px/2 "IBM Plex Mono",ui-monospace,Menlo,monospace;color:var(--mute);grid-row:span 2}}
.t{{font-size:24px;font-weight:500;line-height:1.2}}
.l{{color:var(--mute);font-size:18px}}
.more{{display:inline-block;margin-top:36px;font:14px "IBM Plex Mono",ui-monospace,Menlo,monospace;color:inherit}}
</style>
</head>
<body>
<main>
<span class="thread" aria-hidden="true"></span>
<h1>Bolas set</h1>
<p>Fourteen tests of the Cineosis mark, the character and the webs, in the order they were made. Each page has previous and next at the top.</p>
<ol>
{items}
</ol>
<a class="more" href="notes.html">Notes: what each test was asked, what was said, what held</a>
<a class="more" href="planned.html" style="display:block;margin-top:12px">Planned films: a plan for each, and screen tests of these sets against it</a>
</main>
</body>
</html>
'''
open(os.path.join(OUT, 'index.html'), 'w').write(INDEX)
print('built', len(os.listdir(OUT)), 'entries in', OUT)
