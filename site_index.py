"""The Cineosis Lab front page, built from data: every project has one colour, every door says what you do there (WATCH, PLAY,
MAKE, READ, TOOL), and every page the lab publishes has a door. Door texts that already existed are kept as written (read from
the current index.html); new doors are written here. The moving-image previews on doors are kept (lab/doors/doors.json, and
lab/doors/extra.json for the new doors).
usage: python3 site_index.py      (writes index.html; then publish as usual)"""
import html, json, os, re
H = os.path.dirname(os.path.abspath(__file__))
OLD = open(os.path.join(H, "index.html")).read()
KEEP = {}                                        # href -> (title, text, call) of every door the page already had
for m in re.finditer(r'<a ([^>]*class="door[^"]*"[^>]*)>(.*?)</a>', OLD, re.S):
    href = re.search(r'href="([^"]+)"', m.group(1)).group(1); body = m.group(2)
    b = re.search(r"<b>(.*?)</b>", body, re.S); sp = re.search(r"<span>(.*?)</span>", body, re.S); em = re.search(r"<em>(.*?)</em>", body, re.S)
    if b: KEEP[href] = (b.group(1).strip(), sp.group(1).strip() if sp else "", em.group(1).strip() if em else "Open →")
STYLE = re.search(r"<style>(.*?)</style>", OLD, re.S).group(1).split("/* ---- the front page's order")[0].rstrip() + "\n"   # re-runnable: our own additions are added fresh
SCRIPTS = [x for x in re.findall(r"<script>.*?</script>", OLD, re.S) if "the bar: jump to a project" not in x]
# the previews also read the new doors' clips (extra.json), and a door with only a still keeps its still
SCRIPTS = [x.replace("let D; try { D = await fetch('lab/doors/doors.json').then(r => r.json()); } catch (e) { return; }",
                     "let D; try { D = await fetch('lab/doors/doors.json').then(r => r.json()); } catch (e) { return; } try { Object.assign(D, await fetch('lab/doors/extra.json').then(r => r.json())); } catch (e) { }")
             .replace("a.prepend(dv);", "(a.querySelector('.ui') || a).appendChild(dv);")
             .replace("function show(a) { const c = a._c[a._i % a._c.length],", "function show(a) { if (!a._c.some(x => x.v)) return; const c = a._c[a._i % a._c.length],") if "extra.json" not in x else x.replace("a.prepend(dv);", "(a.querySelector('.ui') || a).appendChild(dv);") for x in SCRIPTS]
NOTES = re.findall(r'<p class="note[^"]*">.*?</p>', OLD, re.S)
STRIP = re.search(r'<div class="strip".*?</div>', OLD, re.S).group(0)
MODES = {"WATCH": "#f4e9dc", "PLAY": "#ffd23f", "MAKE": "#9fe870", "READ": "#d9b8d2", "TOOL": "#a8a29a"}
# ---- the projects, in the order a visitor should meet them; each door: (href, mode, title?, text?, call?, new?)
P = [
 ("republic", "The Republic", "#e0572a", "Seventeen Republics from a writers' room, cut as short films from the archive: a narrator, figures cut from archival films (each introduced where the archive found it), and the archive's citizens.", [
   ("lab/markov-republic.html", "WATCH", "The Republic · all seventeen", "Press play and the series runs on: episode after episode, up next, resumes where you stopped. Fifty-odd minutes.", "Watch →", 1),
   ("lab/markov-republic-ep01.html", "WATCH", "Episode one · The Ergon of Big Hank", "A harvester machine on Mars refuses to work; a rusted barbecue robot with Plato in his chest asks it what it is for. The pilot.", "Watch →", 1),
   ("lab/markov-found-republic.html", "WATCH", "The Republic · four versions", "One script, four rules over the same patches: the screenplay voiced, the archive's own speakers, the archive by montage, and the mixed cut; the script always in view, scored by D-A-E.", "Compare →", 1),
   ("lab/markov-sam-republic.html", "MAKE", "The Republic · multiplane", "The seventeen as multiplane films: archive frames split by depth into glass planes, cut-out cast, AI voices; an x-sheet to change place, cast, voice, camera and join.", "Open →", 1)]),
 ("norse", "Norse Half Moon", "#6cc4d6", "A voice memo about a hand-built Norse house on the Half Moon Bay coast, read like Homer and answered by the archive; and a storyboard to shape it like a sculptor.", [
   ("lab/norse-half-moon.html", "WATCH", "Norse Half Moon · the film", "Seven books, each line of the memo answered by the words of real people on archival film. One button.", "Watch →", 1),
   ("lab/markov-sam-norse.html", "MAKE", "Markov SAM · Norse", "A storyboard for a filmmaker who has never made one: write or say each shot, the archive offers pictures and voices; join, tune, play it LIVE with its D-A-E score.", "Make →", 1)]),
 ("odyssey", "The Odyssey", "#6f8cff", "Homer's Odyssey through the archive: foraged scenes, the archive speaking the lines, radio, sea and road.", [
   ("lab/found-odyssey-museum.html", "WATCH", "The Found Odyssey · museum", "Every line said plainly and answered by real people on archival film. One button, full screen, twenty-four books.", "Watch →", 1),
   ("lab/markov-found-odyssey.html", "WATCH"), ("lab/markov-odyssey-drive.html", "WATCH"), ("lab/markov-radio-odyssey.html", "WATCH"),
   ("lab/markov-sea-steersman.html", "PLAY"), ("lab/markov-sea.html", "PLAY"), ("lab/markov-odyssey.html", "MAKE"), ("lab/markov-transcripts.html", "READ")]),
 ("wygwyl", "WYGWYL", "#c4f46a", "Where You Go When You Leave, Mark Anthony Thomas's poem suite: cut from the archive four ways, edited by its own words, and taken apart.", [
   ("lab/wygwyl.html", "WATCH"), ("lab/wygwyl.html#grid", "WATCH"), ("https://github.com/hartswf0/cineosis-lab/releases/download/wygwyl-v1/wygwyl-forage-cut.mp4", "WATCH"),
   ("lab/videotext.html", "MAKE"), ("lab/videotext-studio.html", "MAKE"), ("lab/tools/hand-butter.html?tempest=1", "MAKE"), ("lab/cutting-room-tempest.html", "PLAY"),
   ("lab/wygwyl-collage.html", "MAKE"), ("lab/cutting-room-floor.html", "TOOL"), ("lab/narrative.html", "READ"), ("lab/sound-cineosis.html", "READ"),
   ("lab/spine-cut.html", "WATCH"), ("lab/spine.html", "READ"), ("lab/syntagma.html", "READ"), ("lab/chemistry.html", "MAKE"), ("lab/chemistry-trials.html", "READ"), ("lab/compounds.html", "READ"),
   ("lab/abc-flix/", "PLAY"), ("lab/abc-flix/film.html", "WATCH"), ("lab/syzygy/", "WATCH"), ("lab/#wygwyl", "READ"), ("lab/wygwyl/player.html", "WATCH"),
   ("lab/bets/", "MAKE", "Nine Bets · WYGWYL", None, None, 0)]),
 ("poet", "The Markov Poet", "#f0b9a4", "Any words, typed, said or recorded, answered by the archive with a film: the engine, the poet, the storyboard, and how it works.", [
   ("lab/shannon-poet.html", "MAKE"), ("lab/shannon-engine.html", "MAKE"), ("lab/shannon-narrative.html", "WATCH"), ("lab/markov-sam.html", "MAKE"),
   ("lab/markov-engine.html", "MAKE"), ("lab/markov-watch.html", "WATCH", "A Markov Poet film", "A film cut from the archive by someone's words. Watch it, then remix it.", "Watch →", 0),
   ("lab/markov-poet.html", "READ"), ("lab/shannon-engine.html?tests=1", "READ")]),
 ("ludens", "Play · Ludens and the Party", "#ffd23f", "Editing as play, over any of the lab's films. The ball's path is the cut and the lab's critic is the physics; or a room of phones making one film together.", [
   ("lab/ludens/tennis.html", "PLAY", "Ludens · Tennis", "Tennis for Two over any of the lab's films (the Republic, the Odyssey, Norse, the Signs, Slopfeeder): twenty-four shots around the ring like a clock. Send the ball to the shot you want next; when it arrives it is cut in, and plays until the next one lands.", "Play →", 1),
   ("lab/ludens/putt.html", "PLAY", "Ludens · Putt-Off", "Editing as golf over any world's field of shots: aim a line of flight; every shot the ball crosses is cut in, for as long as the ball is over it. See the exact cut before you swing.", "Play →", 1),
   ("lab/ludens/open-cut.html", "PLAY", "Ludens · Open Cut", "Golf and tennis in one: players around a round field of shots putt in turn, and every shot a ball rests on must answer the last shot of the one film you are making together.", "Play →", 1),
   ("lab/ludens/", "PLAY", "Ludens · all the games, any world", "Choose a world (Slopfeeder, the Republic, the Odyssey, Norse Half Moon, the Signs), then Putt-Off, Tennis or Open Cut; and The Table on phones: bridge the film so far to the story's next beat with up to three shots, then vote.", "Play →", 1),
   ("lab/party.html", "PLAY"), ("lab/party.html?play=jam", "PLAY"), ("lab/party.html?play=show", "PLAY"), ("lab/party.html?play=cut", "PLAY"), ("lab/party.html?play=calltime", "PLAY"),
   ("lab/party.html?play=pictures", "PLAY"), ("lab/party.html?play=quiz", "PLAY"), ("lab/party.html?play=precisely", "PLAY"), ("lab/party.html?play=odyssey", "PLAY"),
   ("lab/party.html?play=machine", "PLAY"), ("lab/party.html?play=breed", "PLAY"), ("lab/live.html", "PLAY"), ("lab/cineosis.html", "PLAY"), ("lab/casino-tables.html", "PLAY"),
   ("lab/casino.html", "PLAY"), ("lab/calltime.html", "PLAY", "Call Time · solo", "Make today's movie with whatever survived yesterday: the call sheet, the TV guide, the hot remote.", "Play →", 0)]),
 ("talkback", "The archive talks back", "#ff9f43", "What happens when the archive is allowed to change the film instead of illustrating it: who it keeps sending back across every film, and a desk where a narration is answered by contradiction, duration and the images the films leave out.", [
   ("lab/rushes.html#myth", "WATCH", "The Myth", "One narrative from every lab film, told by the archive films they keep returning to. Six acts (the promise, the instruction, the selling, the fear, the dream, the witness): what each film was made for, by whom, and what our Odyssey, Republic and WYGWYL made of it. Two narrators; the people in the films answer back.", "Watch →", 1),
   ("lab/rushes.html", "MAKE", "Rushes", "Start from the footage, on your phone. Every one of 19,821 clips offers four ways on: keep watching, a voice that answers it, an echo, somewhere the films never go. Keep what you want, say a line in one of eight narrator voices, score it with D-A-E, share the reel as a link.", "Start →", 1),
   ("lab/talk-back.html", "MAKE", "The Talk-Back Desk", "Essay first: a narration in four moves, four narrators. Every line is answered by the matching picture, a voice that doubts it, the footage left running, and an image no film has used. Rewrite, follow, cut, and see what the archive changed.", "Shape →", 0),
   ("lab/recurring-cast.html", "READ", "The Recurring Cast", "Every archive film, clip and voice across the Odyssey, Norse, the Republic and WYGWYL: who appears most, what each image is asked to do, what we reach for and what we leave out.", "Read →", 1)]),
 ("monte", "Monte Carlo cinema", "#b39ddb", "Machines that make films: rules that evolve, a critic that scores, a tree search that imagines futures, and the galleries they leave.", [
   ("lab/monte.html", "MAKE"), ("lab/monte-gallery.html", "WATCH", "Monte Carlo Gallery", "The printed films and the ones you kept, each with its found title and chapters, to watch, save or send.", "Watch →", 0),
   ("lab/mcts.html", "WATCH"), ("lab/pictures.html", "PLAY"), ("lab/takes.html", "PLAY"), ("lab/cascade-engine.html", "MAKE"), ("lab/patch.html", "TOOL"),]),
 ("slopfeeder", "SLOPFEEDER", "#ff6f91", "A meme-born beach siege read from inside the lab: eight songs, eight films, the cartoons drawn in code, and the editors they were cut on.", [
   ("lab/slopfeeder-films.html", "WATCH", "Slopfeeder Films", "The eight films, one for each song of The Liturgy of the Two Buttons, each cut from the song's own lyric, with its logline and how it was made.", "Watch →", 1),
   ("lab/slopfeeder.html", "READ", "Slopfeeder in the lab", "The memes it comes from taken apart, its world segmented and named, and the archive's rhymes for every piece, beat and frame.", "Read →", 1),
   ("lab/slopfeeder-chapters.html", "READ", "Slopfeeder Chapters", "The eight music videos as eight chapters and eight bets on how Cineosis makes meaning.", "Read →", 1),
   ("lab/slopfeeder-studio.html", "MAKE", "Slopfeeder Studio", "Music videos built from the archive, moving SAM cut-outs, code and AI prompts: each song a rough arc through the world.", "Make →", 1),
   ("lab/slopfeeder-cartoon.html", "WATCH", "Slopfeeder Multiplane", "The cartoons, one per part of the world, drawn in code as a multiplane animation department would.", "Watch →", 1),
   ("lab/slopfeeder-takes.html", "PLAY", "Sea of Takes", "Every alternative of every shot as one lattice: watch your path play, scrub it, let a tree search pick the next shot.", "Play →", 1),
   ("lab/blacktop.html", "TOOL", "Blacktop", "The flat-top: every shot moving at once, chains of possible cuts lighting up from any shot, many films of a song playing side by side.", "Open →", 1),
   ("lab/griddle.html", "TOOL", "The Griddle", "The editor: a shared timeline per song, a searchable deck of every asset, and a duel between versions.", "Open →", 0),
   ("lab/slopfeeder-storyshots.html", "READ", "Slopfeeder Story Shots", "The shots the archive cannot carry, each with a full generation prompt and its reference stills.", "Read →", 0)]),
 ("signs", "Cineosis · the signs", "#d9b8d2", "Where the lab began: Deleuze's cinematic signs, after Deamer, as a periodic table to read, a wall of archive shots to find them, a table of sounds, and a reel.", [
   ("periodic-table.html", "READ"), ("lab/", "TOOL"), ("lab/sound-table.html", "READ"), ("https://github.com/hartswf0/cineosis-lab/releases/latest", "WATCH"), ("lab/wes.html", "READ")]),
 ("studies", "Studies and benches", "#a9c9c9", "Theory at the bench: Metz and Deleuze run live on footage, syntagms played and re-cut, source passages audited, wagers tested, and every program theory compared.", [
   ("lab/metz-synthesis.html", "MAKE"), ("lab/deleuze-synthesis.html", "MAKE"), ("lab/syntagm.html", "READ"), ("lab/source-patterns.html", "READ"), ("lab/syntagm-bench.html", "READ"),
   ("lab/source-audit.html", "READ"), ("lab/aspect.html", "READ"),
   ("lab/program-theories/", "READ", "What We Have Made", "Ninety-two word-to-clip binding sketches, each read as its own program theory, compared through sixty shared primitives.", "Read →", 1),
   ("lab/synthesis/shell.html", "TOOL", "Cineosis Synthesis · engine", "The synthesis engine's shell: the operations behind the live Metz and Deleuze benches.", "Open →", 0)]),
 ("tools", "Tools", "#d9d3c7", "The editors underneath: the frame with depth as time, the plate as space-time, and the instruments that drive them live.", [
   ("lab/tools/cut.html", "TOOL"), ("lab/tools/hand-butter.html", "TOOL"), ("lab/tools/cut.html?load=wygwyl", "TOOL"), ("lab/tools/hand-butter.html?load=wygwyl", "TOOL"),
   ("lab/abc-flix/c-bus.html", "TOOL", "Arc-Tunnel Operator", "A live video instrument: the ARC-TUNNEL fed with lab footage, played by hand.", "Open →", 0),
   ("lab/abc-flix/icaro-pro-bus.html", "TOOL", "ICARO · Worldtext instrument", "The unified worldtext instrument behind ABC FLIX.", "Open →", 0)]),
]
START = [("periodic-table.html", "READ", "signs", "The periodic table", "Forty-four ways an image can think. Click an element: its deciding test, the signs it is confused with, the shots that show it."),
         ("lab/", "TOOL", "signs", "The explorer", "Thousands of archive shots on one wall. Pick a sign, a decade, a colour or a subject; the wall shows only those."),
         ("lab/found-odyssey-museum.html", "WATCH", "odyssey", "The Found Odyssey", "Homer said plainly, every line answered by real people on archival film. One button, full screen, twenty-four books."),
         ("lab/markov-sam.html", "MAKE", "poet", "Markov SAM", "A storyboard by hand: each line gets a ground from the archive and figures SAM has cut out of it. Drag them into place.")]
UI = json.load(open(os.path.join(H, "lab", "doors", "ui.json"))) if os.path.exists(os.path.join(H, "lab", "doors", "ui.json")) else {}
for h in ("lab/abc-flix/icaro-pro-bus.html",): UI.pop(h, None)          # its still is a blank panel: the archive preview says more
E = html.escape
def door(proj, color, d):
    href, mode = d[0], d[1]; t, x, c, new = (d + (None, None, None, 0))[2:6]
    k = KEEP.get(href, (None, None, None))
    t = t or k[0] or href; x = x if x is not None else (k[1] or ""); c = c or k[2] or "Open →"
    if not d[2:3] and href not in KEEP: print("  no text for", href)
    rid = ' id="reelDoor"' if href.endswith("/releases/latest") else ""
    ui = f'<span class="ui"><img src="{UI[href]}" alt="" loading="lazy"></span>' if href in UI else ""
    return (f'<a class="door" data-p="{proj}" data-m="{mode}" href="{E(href)}"{rid} style="--c:{color}">{ui}<u>{mode}{" · NEW" if new else ""}</u>'
            f'<b>{t}</b><span>{x}</span><em>{c}</em></a>')
nav = "".join(f'<a href="#{k}" style="--c:{c}"><i></i>{E(n)}</a>' for k, n, c, _, _ in P)
modes = "".join(f'<button data-m="{m}" style="--c:{c}">{m}</button>' for m, c in MODES.items())
def start_door(n, h, m, p, t, x):
    col = next(c for k, _, c, _, _ in P if k == p); ui = '<span class="ui"><img src="%s" alt="" loading="lazy"></span>' % UI[h] if h in UI else ""
    return f'<a class="door big" data-p="{p}" data-m="{m}" href="{h}" style="--c:{col}">{ui}<u>{n + 1} · {m}</u><b>{E(t)}</b><span>{E(x)}</span><em>Go →</em></a>'
start = "".join(start_door(n, *d) for n, d in enumerate(START))
sections = "".join(f'<section id="{k}" style="--c:{c}"><header><h2><i></i>{E(n)}</h2><p>{E(intro)}</p></header><div class="doors">{"".join(door(k, c, d) for d in ds)}</div></section>' for k, n, c, intro, ds in P)
count = sum(len(ds) for *_, ds in P)
CSS = STYLE + """
/* ---- the front page's order: projects by colour, doors by what you do there ---- */
.lede{max-width:52em;color:var(--dim)}
.start{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin:18px 0 8px}
#bar{position:sticky;top:0;z-index:20;background:rgba(11,10,9,.94);backdrop-filter:blur(6px);border-bottom:1px solid var(--rule);margin:18px -16px 0;padding:10px 16px;display:flex;flex-direction:column;gap:8px}
#bar nav{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none}
#bar nav a{flex:0 0 auto;display:flex;align-items:center;gap:6px;font-size:11px;letter-spacing:.06em;color:var(--ink);text-decoration:none;border:1px solid var(--rule);padding:6px 10px;border-radius:16px;white-space:nowrap}
#bar nav a i{width:9px;height:9px;border-radius:50%;background:var(--c)}
#bar nav a:hover,#bar nav a.on{border-color:var(--c);background:color-mix(in srgb,var(--c) 14%,transparent)}
#bar .modes{display:flex;gap:6px;flex-wrap:wrap;align-items:center;font-size:10px;letter-spacing:.14em;color:var(--dim)}
#bar .modes button{font:inherit;letter-spacing:.14em;color:var(--dim);background:none;border:1px solid var(--rule);padding:5px 9px;border-radius:14px;cursor:pointer}
#bar .modes button.on{color:#0b0a09;background:var(--c);border-color:var(--c)}
section{margin:34px 0 0;scroll-margin-top:110px}
section header{border-left:4px solid var(--c);padding-left:12px;margin-bottom:12px}
section h2{display:flex;align-items:center;gap:10px;margin:0;color:var(--c)}
section h2 i{display:none}
section header p{margin:4px 0 0;color:var(--dim);max-width:60em;font-size:13.5px}
a.door{position:relative;border-top:3px solid var(--c)!important}
a.door u{display:inline-block;text-decoration:none;font-size:9.5px;letter-spacing:.16em;color:var(--c);margin-bottom:4px}
a.door.big{border-top-width:5px!important}
a.door.big b{font-size:1.15em}
a.door[hidden]{display:none}
section.empty{display:none}
.count{color:var(--dim);font-size:12px}
#find{font:inherit;font-size:12px;color:var(--ink);background:#14120f;border:1px solid var(--rule);border-radius:14px;padding:5px 11px;min-width:170px;margin-left:6px}
#find:focus{outline:none;border-color:var(--ink)}
a.door .ui{position:relative;display:block;margin:-20px -18px 12px;aspect-ratio:16/10;background:#000;border-radius:5px 5px 0 0;overflow:hidden}
a.door .ui > img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top;display:block;opacity:.92}
a.door .ui .dv{position:absolute;right:8px;bottom:8px;width:40%;margin:0;border:1px solid rgba(255,255,255,.45);border-radius:4px;box-shadow:0 4px 14px rgba(0,0,0,.6)}
a.door .ui .dv i{display:none}
@media (max-width:600px){#bar{padding:6px 12px;gap:6px;margin:14px -12px 0}#bar .modes{gap:4px}#bar .modes button{padding:4px 7px}.count{display:none}section{scroll-margin-top:96px}}
"""
OUT = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cineosis Lab</title>
<meta name="description" content="A laboratory of the moving-image archive: films cut from it (The Republic, Norse Half Moon, the Odyssey, WYGWYL), games that edit with it, tools to make your own, and the cinematic signs it began with.">
<meta property="og:title" content="Cineosis Lab"><meta property="og:description" content="Films cut from the archive, games that edit with it, tools to make your own, and the signs it began with.">
<meta property="og:image" content="https://hartswf0.github.io/cineosis-lab/lab/republic/pilot/ep01-poster.jpg"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700;9..144,800&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<main>
<h1>Cineosis Lab</h1>
<p class="sub">A laboratory of the moving-image archive. Films cut from it, games that edit with it, tools to make your own, and the cinematic signs it began with (Deleuze's, after Deamer).</p>
{STRIP}
<div class="start">{start}</div>
<div id="bar"><nav>{nav}</nav><div class="modes">SHOW <button data-m="ALL" class="on" style="--c:#ece6da">ALL</button>{modes}<input id="find" type="search" placeholder="find a door…" aria-label="Find a door"><span class="count" id="count">{count} doors</span></div></div>
{sections}
{''.join(NOTES)}
</main>
{''.join(SCRIPTS)}
<script>
/* the bar: jump to a project (its chip lights as you pass it); show only one kind of door */
const secs = [...document.querySelectorAll('section')], chips = [...document.querySelectorAll('#bar nav a')];
const io = new IntersectionObserver(es => es.forEach(e => {{ if (e.isIntersecting) chips.forEach(c => c.classList.toggle('on', c.getAttribute('href') === '#' + e.target.id)); }}), {{rootMargin: '-40% 0px -55% 0px'}});
secs.forEach(s => io.observe(s));
let MODE = 'ALL';
function filter() {{
  const q = document.getElementById('find').value.trim().toLowerCase(); let n = 0;
  document.querySelectorAll('section a.door').forEach(a => {{ const on = (MODE === 'ALL' || a.dataset.m === MODE) && (!q || a.textContent.toLowerCase().includes(q)); a.hidden = !on; n += on; }});
  secs.forEach(s => s.classList.toggle('empty', !s.querySelector('a.door:not([hidden])'))); document.getElementById('count').textContent = n + ' doors';
}}
document.querySelectorAll('#bar .modes button').forEach(b => b.onclick = () => {{ MODE = b.dataset.m; document.querySelectorAll('#bar .modes button').forEach(x => x.classList.toggle('on', x === b)); filter(); }});
document.getElementById('find').oninput = filter;
</script>
</body>
</html>
"""
open(os.path.join(H, "index.html"), "w").write(OUT)
print(len(P), "projects ·", count, "doors")
