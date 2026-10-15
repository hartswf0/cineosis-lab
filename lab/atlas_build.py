"""THE ATLAS · an excavation of the Cineosis Lab repository. Reads the published repo (default ~/cineosis-lab) and its git history and
writes lab/atlas.json, which lab/atlas.html draws. For every page: what it is (title, a line from its own header), where it sits in
the taxonomy (kingdom > family > kind), when it was born and last changed and by which commit messages, what it links to and what
links to it, the data it reads and the scripts that write that data, and how many clicks it is from the front door. Also every
page that existed and was later removed (the buried), every script with its first docstring line, and the commits day by day.
Taxonomy: the five kingdoms of the Web of Cineosis (bolas set 13: Archive, Machines, Operations, Readings, Films) plus the House;
families are the projects; kinds say what a page is for. Rules below, overrides for the pages the rules get wrong.
usage: python3 lab/atlas_build.py [repo]"""
import json, os, re, subprocess, sys, collections, html as H
REPO = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/cineosis-lab')
SKIP = re.compile(r'(^|/)(\.git|node_modules|\.venv|clips|thumbs|frames|cache|models)(/|$)')
KINGDOMS = [('archive', 'Archive', 'What there is to look at: the shots, the films they came from, and ways to browse them.'),
            ('machines', 'Machines', 'The models that look, listen and write, and what they give back.'),
            ('operations', 'Operations', 'Benches where shots are found, asked, scored, cut and assembled.'),
            ('readings', 'Readings', 'The signs, the theories and the papers: ways an image can be read.'),
            ('films', 'Films', 'What comes out: explainers about the lab and the films made with it.'),
            ('house', 'House', 'Front doors, indexes, the mark, notes, and pages that only point elsewhere.')]
# family: (id, name, colour, path patterns)
FAMILIES = [
  ('origin', 'The periodic table', '#d9b44a', [r'^(index|periodic-table|signs-in-motion|review|contact|404|table\.template)\.html$']),
  ('bolas', 'Bolas, the mark', '#e0483a', [r'^lab/bolas/', r'^lab/idents\.html$']),
  ('lessons', 'Explainers', '#c4f46a', [r'^lab/(lesson-\d|episode-1|machines|how-it-sees|operative|myth|series|papers)\.html$']),
  ('rooms', 'Rooms, filmed', '#7fd6e8', [r'^lab/room-']),
  ('wygwyl', 'Where You Go When You Leave', '#9fd36a', [r'^lab/(wygwyl|cel-cuts|spine|cutting-room|videotext|cascade-engine|episode-5)', r'^lab/wygwyl/']),
  ('poet', 'Markov poet and Shannon', '#b48ead', [r'^lab/(markov-(poet|engine|sam|sea|transcripts|watch)|shannon)']),
  ('odyssey', 'The Odyssey', '#6f8cff', [r'^lab/(markov-(odyssey|found-odyssey|radio-odyssey)|found-odyssey|episode-4)', r'^lab/odyssey/']),
  ('republic', 'The Republic', '#e0572a', [r'^lab/(markov-(republic|found-republic|sam-republic)|episode-7)', r'^lab/republic/']),
  ('norse', 'Norse Half Moon', '#6cc4d6', [r'^lab/(norse|markov-sam-norse)', r'^lab/norse/']),
  ('wargames', 'WarGames', '#5fbf8f', [r'(wargames|bumblebee)']),
  ('slop', 'Slopfeeder', '#ff6b5b', [r'^lab/(slopfeeder|blacktop|griddle)']),
  ('monte', 'Monte Carlo', '#e6a23c', [r'^lab/(monte|mcts|casino|pictures|patch)']),
  ('chem', 'Narrative chemistry', '#b9cfa0', [r'^lab/(chemistry|compounds)']),
  ('syntagm', 'Syntagm and theory', '#c9a4ff', [r'^lab/(syntagm|source-|metz|deleuze)', r'^lab/synthesis/']),
  ('sound', 'Sound', '#f4a3c0', [r'^lab/sound-']),
  ('wes', 'Wes and aspect', '#f4c7d0', [r'^lab/(wes|aspect)\.html$']),
  ('syzygy', 'Syzygy', '#7fd6e8', [r'^lab/syzygy/']),
  ('bets', 'Bets and theories', '#a8a196', [r'^lab/(bets|program-theories)/']),
  ('play', 'Games and flix', '#f2c14e', [r'^lab/(ludens|abc-flix)/']),
  ('archive', 'The lab itself', '#d8d0c0', [r'^lab/(index|rushes|takes|film|narrative|recurring-cast|talk-back|party|calltime|live|cineosis)\.html$', r'^lab/tools/']),
]
FAM = {f[0]: f for f in FAMILIES}
# kind: what a page is for -> kingdom
KINDS = {'explainer': ('Explainer film', 'films'), 'film': ('Film or player', 'films'), 'series': ('Series episode', 'films'),
         'browser': ('Archive browser', 'archive'), 'machine': ('Machine view', 'machines'), 'bench': ('Bench or instrument', 'operations'),
         'reading': ('Reading or paper', 'readings'), 'index': ('Index or front door', 'house'), 'mark': ('Mark and identity', 'house'),
         'template': ('Template', 'house'), 'pointer': ('Pointer or superseded', 'house'), 'game': ('Game', 'operations')}
RULES = [(r'^lab/(lesson-\d|episode-\d|machines|how-it-sees|operative|myth|room-[a-z]+)\.html$', 'explainer'),
         (r'markov-republic-ep\d+|markov-republic-pilot', 'series'), (r'template', 'template'),
         (r'^lab/bolas/|idents\.html$', 'mark'), (r'(^|/)index\.html$|series\.html$|papers\.html$|404\.html$|contact\.html$', 'index'),
         (r'(synthesis|wygwyl-spine|source-audit|program-theories|periodic-table|signs-in-motion|compounds|chemistry-trials|deleuze|metz|syntagma\.html)', 'reading'),
         (r'(rushes|takes|narrative|recurring-cast|aspect|talk-back|review)\.html$', 'browser'),
         (r'(sound-|syzygy|cascade-engine|how-it-sees|machines)', 'machine'),
         (r'(ludens|abc-flix)/', 'game'),
         (r'(found-|markov-(found|watch|odyssey|radio|republic\.html|sam)|episode|films|museum|-cuts|cel-cuts|spine-cut|film\.html|wygwyl\.html|player|storyboard|norse-half-moon|wes\.html|monte-gallery|pictures|cartoon|chapters|storyshots)', 'film')]
OVERRIDE = {'lab/index.html': ('archive', 'index'), 'index.html': ('origin', 'index'), 'lab/griddle.html': ('slop', 'pointer'), 'lab/calltime.html': ('archive', 'pointer'),
            'lab/live.html': ('archive', 'pointer'), 'lab/cineosis.html': ('archive', 'pointer'), 'lab/party.html': ('archive', 'bench'),
            'lab/myth.html': ('lessons', 'explainer'), 'lab/series.html': ('lessons', 'index'), 'lab/papers.html': ('lessons', 'reading'),
            'lab/syzygy/syzygy.part.html': ('syzygy', 'template'), 'lab/episode-5.html': ('wygwyl', 'explainer'), 'lab/episode-4.html': ('odyssey', 'explainer'),
            'lab/episode-7.html': ('republic', 'explainer'), 'lab/room-syzygy.html': ('rooms', 'explainer'), 'lab/norse-half-moon.html': ('norse', 'film'),
            'lab/wygwyl-collage.html': ('wygwyl', 'bench'), 'lab/cutting-room-floor.html': ('wygwyl', 'bench'), 'lab/cutting-room-tempest.html': ('wygwyl', 'bench'),
            'lab/videotext.html': ('wygwyl', 'bench'), 'lab/videotext-studio.html': ('wygwyl', 'bench'), 'lab/wygwyl-take.html': ('wygwyl', 'explainer'),
            'lab/blacktop.html': ('slop', 'bench'), 'lab/slopfeeder-studio.html': ('slop', 'bench'), 'lab/slopfeeder.html': ('slop', 'bench'), 'lab/slopfeeder-takes.html': ('slop', 'film'),
            'lab/monte.html': ('monte', 'bench'), 'lab/mcts.html': ('monte', 'bench'), 'lab/casino.html': ('monte', 'bench'), 'lab/casino-tables.html': ('monte', 'bench'), 'lab/patch.html': ('monte', 'bench'),
            'lab/syntagm.html': ('syntagm', 'bench'), 'lab/syntagm-bench.html': ('syntagm', 'bench'), 'lab/source-patterns.html': ('syntagm', 'bench'),
            'lab/chemistry.html': ('chem', 'bench'), 'lab/markov-engine.html': ('poet', 'bench'), 'lab/shannon-engine.html': ('poet', 'bench'), 'lab/shannon.html': ('poet', 'bench'),
            'lab/markov-poet.html': ('poet', 'bench'), 'lab/shannon-poet.html': ('poet', 'film'), 'lab/shannon-narrative.html': ('poet', 'film'), 'lab/markov-transcripts.html': ('poet', 'browser'),
            'lab/wargames-os.html': ('wargames', 'bench'), 'lab/wargames-web.html': ('wargames', 'reading'), 'lab/wargames.html': ('wargames', 'browser'), 'lab/vj-wargames.html': ('wargames', 'film'),
            'wargames-periodic-table.html': ('wargames', 'reading'), 'lab/tools/cut.html': ('archive', 'bench'), 'lab/tools/hand-butter.html': ('archive', 'bench'),
            'lab/bets/index.html': ('bets', 'index'), 'lab/program-theories/index.html': ('bets', 'reading'), 'lab/spine.html': ('wygwyl', 'pointer'),
            'lab/markov-republic.html': ('republic', 'film'), 'lab/wes.html': ('wes', 'film'), 'lab/aspect.html': ('wes', 'browser'), 'lab/bumblebee-dilemma.html': ('wargames', 'machine')}
POINTER = re.compile(r'now lives in|superseded by|has moved|moved to', re.I)

def git(*a): return subprocess.run(['git', '-C', REPO, *a], capture_output=True, text=True).stdout
# ---- history: one pass
hist = collections.defaultdict(list); days = collections.defaultdict(list); gone = {}
for block in git('log', '--name-status', '--format=@@%h|%ad|%s', '--date=iso-strict', '--no-renames').split('@@')[1:]:
    head, *files = block.strip('\n').split('\n'); h, d, msg = head.split('|', 2); day = d[:10]; days[day].append({'h': h, 't': d[11:16], 'm': msg[:140], 'n': 0})
    for f in files:
        if '\t' not in f: continue
        st, p = f.split('\t', 1); p = p.strip('"')
        hist[p].append((d, st, msg[:140], h)); days[day][-1]['n'] += 1
        if st == 'D' and p not in gone: gone[p] = (d, msg[:140])
for p in hist: hist[p].sort()
# ---- the files on disk
files = []
for root, ds, fs in os.walk(REPO):
    rel = os.path.relpath(root, REPO); rel = '' if rel == '.' else rel
    if SKIP.search(rel + '/'): ds[:] = []; continue
    ds[:] = [d for d in ds if not SKIP.search(os.path.join(rel, d) + '/')]
    for f in fs: files.append(os.path.join(rel, f) if rel else f)
pages = sorted(f for f in files if f.endswith('.html') and ' ' not in f)
scripts = sorted(f for f in files if f.endswith('.py'))
datas = set(f for f in files if f.endswith('.json'))
def read(p):
    try: return open(os.path.join(REPO, p), encoding='utf-8', errors='ignore').read()
    except Exception: return ''
def clean(t, n=230): t = H.unescape(re.sub(r'\s+', ' ', t)).strip(); return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'
def describe(t):
    c = re.search(r'<!--([\s\S]*?)-->', t)
    if c and len(c.group(1).strip()) > 40 and not re.match(r'\s*[═=\-]{5}', c.group(1)): return clean(re.sub(r'^[A-Z0-9 ·:,\'&\-]{6,}[.:]\s*', '', clean(c.group(1), 900)))
    m = re.search(r'<meta name="description" content="([^"]+)"', t)
    if m: return clean(m.group(1))
    b = re.sub(r'<(script|style|svg)[\s\S]*?</\1>', ' ', t); b = re.sub(r'<!--[\s\S]*?-->', ' ', b)
    return clean(re.sub(r'<[^>]+>', ' ', b))
def resolve(base, ref):
    ref = ref.split('#')[0].split('?')[0]
    if not ref or re.match(r'^(https?:|mailto:|data:|javascript:|\$\{)', ref): return None
    p = os.path.normpath(os.path.join(os.path.dirname(base), ref)).replace('\\', '/')
    if ref.endswith('/') or os.path.isdir(os.path.join(REPO, p)): p = p.rstrip('/') + '/index.html'
    return p
P = {}
for p in pages:
    t = read(p); ti = re.search(r'<title>([^<]*)</title>', t)
    refs = set(re.findall(r'(?:href|src)\s*=\s*["\']([^"\'<>]+)["\']', t)) | set(re.findall(r'["\'`(]([\w./-]+\.(?:html|json|js)(?:\?[^"\'`)]*)?)["\'`)]', t))
    out, data, js = set(), set(), set()
    for r in refs:
        q = resolve(p, r)
        if not q: continue
        if q.endswith('.html') and q != p: out.add(q)
        elif q.endswith('.json'): data.add(q)
        elif q.endswith('.js'): js.add(q)
    fam = next((f[0] for f in FAMILIES for pat in f[3] if re.search(pat, p)), 'archive'); kind = next((k for pat, k in RULES if re.search(pat, p)), 'bench')
    if POINTER.search(clean(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)[\s\S]*?</\1>', '', t)), 400)) and len(t) < 6000: kind = 'pointer'
    if p in OVERRIDE: fam, kind = OVERRIDE[p]
    h = hist.get(p, [])
    P[p] = {'path': p, 'title': clean(ti.group(1), 90) if ti else os.path.basename(p), 'desc': describe(t), 'family': fam, 'kind': kind, 'kingdom': KINDS[kind][1],
            'born': h[0][0][:10] if h else None, 'last': h[-1][0][:10] if h else None, 'commits': len(h), 'firstMsg': h[0][2] if h else '', 'lastMsg': h[-1][2] if h else '',
            'bytes': len(t), 'out': sorted(q for q in out if q in pages or q in [x for x in pages]), 'broken': sorted(q for q in out if q not in pages and not q.endswith('index.html'))[:12],
            'data': sorted(d for d in data if d in datas), 'js': sorted(j for j in js if os.path.exists(os.path.join(REPO, j)))}
# the films menu: every page that runs explain/player.js links to every film in explain/films.js
FILMS = [resolve('lab/x.html', h) for h in re.findall(r"href:\s*'([^']+)'", read('lab/explain/films.js'))]
for p, x in P.items():
    if 'lab/explain/player.js' in x['js']: x['out'] = sorted(set(x['out']) | {f for f in FILMS if f in P and f != p}); x['menu'] = True
# titles that repeat, or were never filled in, get the file name
tc = collections.Counter(x['title'] for x in P.values())
for p, x in P.items():
    if '{{' in x['title'] or not x['title'].strip(): x['title'] = os.path.basename(p)
    elif tc[x['title']] > 1: x['title'] = f"{x['title']} · {os.path.basename(os.path.dirname(p)) + '/' if '/' in p else ''}{os.path.basename(p)}"
inb = collections.defaultdict(set)
for p, x in P.items():
    for q in x['out']: inb[q].add(p)
for p, x in P.items(): x['in'] = sorted(inb[p])
# clicks from the front doors
depth = {}; via = {}; fr = [d for d in ('lab/index.html',) if d in P]   # the root index.html is a generated directory of every page: not a way anyone navigates
for d in fr: depth[d] = 0
q = list(fr)
while q:
    a = q.pop(0)
    for b in P[a]['out']:
        if b not in depth and b != 'index.html': depth[b] = depth[a] + 1; via[b] = a; q.append(b)
for p, x in P.items():
    real = [q for q in x['in'] if q != 'index.html']
    route = []; c = p
    while c in via: c = via[c]; route.insert(0, c)
    x['route'] = route if p in depth else []
    x['depth'] = depth.get(p); x['status'] = 'pointer' if x['kind'] == 'pointer' else 'template' if x['kind'] == 'template' else 'reachable' if p in depth or p == 'index.html' else 'orphan' if not real else 'hidden' if 'index.html' in x['in'] or not [q for q in real if q in depth] else 'island'
# scripts: what they say they are, what data they write and read
S = []; writes = collections.defaultdict(set)
for s in scripts:
    t = read(s); doc = re.match(r'\s*(?:#.*\n)*\s*(?:r?"""|r?\'\'\')([\s\S]*?)(?:"""|\'\'\')', t); h = hist.get(s, [])
    names = set(re.findall(r'["\']([\w./-]+\.json)["\']', t)); w = set()
    for n in names:
        if re.search(re.escape(n) + r'["\'][^\n]{0,40}["\']w["\']', t) or re.search(r'(dump|write)[^\n]{0,160}' + re.escape(n), t) or re.search(re.escape(n) + r'[^\n]{0,160}["\']w["\']\)', t): w.add(n)
    full = lambda n: next((d for d in datas if d.endswith('/' + n.split('/')[-1]) and (n.count('/') == 0 or d.endswith(n))), None)
    wf = sorted(filter(None, (full(n) for n in w))); rf = sorted(filter(None, (full(n) for n in names - w)))
    for d in wf: writes[d].add(s)
    S.append({'path': s, 'desc': clean(doc.group(1), 200) if doc else clean(' '.join(l.lstrip('# ') for l in t.split('\n')[:3] if l.startswith('#')), 200),
              'writes': wf[:20], 'reads': rf[:20], 'born': h[0][0][:10] if h else None, 'last': h[-1][0][:10] if h else None, 'commits': len(h), 'lines': t.count('\n')})
for x in P.values(): x['madeBy'] = sorted({s for d in x['data'] for s in writes.get(d, ())})
buried = [{'path': p, 'born': hist[p][0][0][:10], 'died': d[:10], 'msg': m, 'lastTitle': ''} for p, (d, m) in gone.items() if p.endswith('.html') and p not in P and ' ' not in p]
fams = collections.Counter(x['family'] for x in P.values())
out = {'built': subprocess.run(['date', '+%Y-%m-%d %H:%M'], capture_output=True, text=True).stdout.strip(), 'repo': os.path.basename(REPO),
       'kingdoms': [{'id': k, 'name': n, 'desc': d} for k, n, d in KINGDOMS], 'kinds': {k: v[0] for k, v in KINDS.items()},
       'families': [{'id': f[0], 'name': f[1], 'color': f[2], 'n': fams[f[0]]} for f in FAMILIES if fams[f[0]]],
       'pages': sorted(P.values(), key=lambda x: (x['born'] or '9', x['path'])), 'buried': sorted(buried, key=lambda x: x['died']), 'scripts': S,
       'days': [{'date': d, 'commits': list(reversed(v))} for d, v in sorted(days.items())],
       'totals': {'pages': len(P), 'scripts': len(S), 'data': len(datas), 'commits': sum(len(v) for v in days.values()), 'buried': len(buried)}}
dst = os.path.join(REPO, 'lab', 'atlas.json'); json.dump(out, open(dst, 'w'), ensure_ascii=False, separators=(',', ':'))
st = collections.Counter(x['status'] for x in P.values()); print('pages', len(P), dict(st), 'scripts', len(S), 'buried', len(buried), 'commits', out['totals']['commits'], '->', dst, os.path.getsize(dst) // 1024, 'KB')
print('families', dict(fams)); print('kinds', dict(collections.Counter(x['kind'] for x in P.values())))
print('orphans', [p for p, x in P.items() if x['status'] == 'orphan']); print('hidden', [p for p, x in P.items() if x['status'] in ('hidden', 'island')])
