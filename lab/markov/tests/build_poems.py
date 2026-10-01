"""The Shannon engine's test library: every text the engine is asked to make a film from.
Public-domain texts come from Wikisource (tests/pd/, fetched by fetch_all.py); translations marked 'this lab' are ours, from public-domain originals;
copyrighted poems are listed without their text ('bring your own'): paste them in the page (kept in your browser) or drop them in tests/local/<id>.txt."""
import json, os, random, re
H = os.path.dirname(os.path.abspath(__file__))
def pd(k):
    t = open(os.path.join(H, "pd", k + ".txt")).read().replace("​", "").strip()
    return t
def keats():
    t = pd("keats"); t = re.sub(r"^ODE ON A GRECIAN URN\.\s*", "", t); return t.strip()
def coleridge():
    t = pd("coleridge"); i = t.find("In Xanadu"); return t[i:].strip()
def stevens():
    t = pd("stevens"); t = re.sub(r"^Thirteen Ways of Looking at a Blackbird\s*", "", t)
    return re.sub(r"(?m)^[IVX]+\n", "", t).strip()                     # the section numerals are stanza breaks already
def hopkins():
    t = pd("hopkins"); i = t.find("Felix Randal the farrier"); return t[i:].strip()
def iliad():
    t = pd("iliad18"); a = t.find("First he shaped the shield"); b = t.find("river Oceanus.", a) + len("river Oceanus."); return t[a:b].strip()
def giles():
    t = pd("giles3"); a = t.find("Prince Hui's cook"); b = t.find("how to take care of my life.", a) + len("how to take care of my life.\""); return t[a:b].strip()
def house_of_dust(n=10, seed=1967):
    # the four-line form of Knowles and Tenney's 1967 program, with this lab's own word lists (not theirs)
    M = ["brick", "glass", "dust", "paper", "tin", "salt", "leaves", "stone", "wood", "mud", "bone", "straw", "rope", "sand"]
    L = ["in a river valley", "in a city at night", "in a desert", "by the harbor", "in a cold forest", "on an island", "in a field of corn", "in the mountains", "in a burning town", "on a flooded street"]
    G = ["candles", "the moon", "lanterns", "the television", "streetlights", "firelight", "a single bulb", "the headlights of passing cars"]
    P = ["old women", "children playing", "fishermen and their families", "people who work at night", "musicians", "farmers", "strangers", "a man and a woman", "horses and birds", "lovers", "the poet"]
    r = random.Random(seed)
    return "\n\n".join(f"A house of {r.choice(M)}\n{r.choice(L)}\nusing {r.choice(G)}\ninhabited by {r.choice(P)}" for _ in range(n))
POEMS = [
 dict(id="wygwyl", title="Where You Go When You Leave", author="the WYGWYL suite", year=2025, kind="suite", status="the lab's own poems, timed by the recorded voice", source="w01", note="Open it from the WYGWYL list: the suite's voice keeps the clock."),
 dict(id="keats", title="Ode on a Grecian Urn", author="John Keats", year=1819, kind="poem", status="public domain (Wikisource, 1820 text)", text=keats()),
 dict(id="berry", title="The Peace of Wild Things", author="Wendell Berry", year=1968, kind="poem", status="bring your own"),
 dict(id="cavafy", title="Ithaka", author="C. P. Cavafy", year=1911, kind="poem", status="bring your own (an English translation)"),
 dict(id="coleridge", title="Kubla Khan", author="Samuel Taylor Coleridge", year=1816, kind="poem", status="public domain (Wikisource, 1816 text)", text=coleridge()),
 dict(id="schleicher", title="The Sheep and the Horses", author="August Schleicher", year=1868, kind="fable", status="translation: this lab, from Schleicher's German", text=
  "On a hill, a sheep that had no wool saw horses.\nOne was pulling a heavy wagon, one was carrying a great load, and one was carrying a man quickly.\n\nThe sheep said to the horses: my heart aches, seeing a man drive horses.\n\nThe horses said: listen, sheep, our hearts ache when we see this:\na man, the master, makes the wool of the sheep into a warm coat for himself,\nand the sheep has no wool.\n\nHearing this, the sheep fled into the plain."),
 dict(id="basho", title="Old Pond", author="Matsuo Bashō", year=1686, kind="poem", status="translation: this lab", text="An old pond.\nA frog jumps in.\nThe sound of water."),
 dict(id="zhuangzi", title="Cook Ding (Prince Hui's cook)", author="Zhuangzi, tr. Herbert Giles", year=1889, kind="prose", status="public domain (Wikisource, Giles 1889)", text=giles()),
 dict(id="williams", title="The Red Wheelbarrow", author="William Carlos Williams", year=1923, kind="poem", status="public domain (1923); entered by hand, check against a printed source", text=
  "so much depends\nupon\n\na red wheel\nbarrow\n\nglazed with rain\nwater\n\nbeside the white\nchickens"),
 dict(id="wilbur", title="Mind", author="Richard Wilbur", year=1956, kind="poem", status="bring your own"),
 dict(id="auden", title="The Shield of Achilles", author="W. H. Auden", year=1952, kind="poem", status="bring your own"),
 dict(id="iliad18", title="Iliad 18: the Shield of Achilles", author="Homer, tr. Samuel Butler", year=1898, kind="epic", status="public domain (Wikisource, Butler 1898)", text=iliad()),
 dict(id="lem", title="Love and Tensor Algebra (Trurl's Electronic Bard)", author="Stanisław Lem, The Cyberiad", year=1965, kind="poem", status="bring your own"),
 dict(id="mon", title="non/tot III", author="Franz Mon", year=None, kind="concrete poem", status="bring your own"),
 dict(id="angelou", title="Still I Rise", author="Maya Angelou", year=1978, kind="poem", status="bring your own"),
 dict(id="dthomas", title="Do Not Go Gentle Into That Good Night", author="Dylan Thomas", year=1951, kind="poem", status="bring your own"),
 dict(id="frost", title="The Road Not Taken", author="Robert Frost", year=1916, kind="poem", status="public domain (Wikisource, Mountain Interval 1916)", text=pd("frost")),
 dict(id="holderlin", title="In Lovely Blueness", author="Friedrich Hölderlin", year=None, kind="prose poem", status="bring your own (an English translation)"),
 dict(id="george", title="The Word (Das Wort)", author="Stefan George, read by Heidegger", year=1919, kind="poem", status="translation: this lab, from the public-domain German (Wikisource)", text=
  "Wonder from far away, or dream,\nI brought to the border of my land\n\nand waited till the grey norn\nfound the name in her well.\n\nThen I could grasp it, dense and strong;\nnow it blooms and shines through the borderland.\n\nOnce I arrived after a good voyage\nwith a jewel, rich and delicate.\n\nShe searched a long time and told me:\n'Nothing like this sleeps here on the deep ground.'\n\nAt that it slipped from my hand\nand my land never won the treasure.\n\nSo I learned, sadly, to renounce:\nlet no thing be where the word breaks off."),
 dict(id="stevens", title="Thirteen Ways of Looking at a Blackbird", author="Wallace Stevens", year=1917, kind="poem", status="public domain (Wikisource, Harmonium)", text=stevens()),
 dict(id="macleish", title="Ars Poetica", author="Archibald MacLeish", year=1926, kind="poem", status="public domain in the US (1926); entered by hand, check against a printed source", text=
  "A poem should be palpable and mute\nAs a globed fruit,\n\nDumb\nAs old medallions to the thumb,\n\nSilent as the sleeve-worn stone\nOf casement ledges where the moss has grown—\n\nA poem should be wordless\nAs the flight of birds.\n\nA poem should be motionless in time\nAs the moon climbs,\n\nLeaving, as the moon releases\nTwig by twig the night-entangled trees,\n\nLeaving, as the moon behind the winter leaves,\nMemory by memory the mind—\n\nA poem should be motionless in time\nAs the moon climbs.\n\nA poem should be equal to:\nNot true.\n\nFor all the history of grief\nAn empty doorway and a maple leaf.\n\nFor love\nThe leaning grasses and two lights above the sea—\n\nA poem should not mean\nBut be."),
 dict(id="hopkins", title="Felix Randal", author="Gerard Manley Hopkins", year=1880, kind="poem", status="public domain (Wikisource)", text=hopkins()),
 dict(id="houseofdust", title="A House of Dust (the form, with this lab's words)", author="after Alison Knowles and James Tenney", year=1967, kind="generator", status="the four-line form, generated here with the lab's own word lists; the original lists are not used", text=house_of_dust()),
 dict(id="brautigan", title="All Watched Over by Machines of Loving Grace", author="Richard Brautigan", year=1967, kind="poem", status="bring your own"),
 dict(id="jackjill", title="Jack and Jill", author="nursery rhyme", year=1765, kind="rhyme", status="public domain", text=
  "Jack and Jill went up the hill\nTo fetch a pail of water;\nJack fell down and broke his crown,\nAnd Jill came tumbling after.\n\nUp Jack got, and home did trot,\nAs fast as he could caper;\nHe went to bed to mend his head\nWith vinegar and brown paper."),
 dict(id="meeting", title="A site meeting (transcript)", author="written for this lab", year=2026, kind="meeting", status="the lab's own example of a transcript: speakers become strands", text=
  "Maya: Thanks for coming in early. The river project is behind, and the bridge crew is waiting on our drawings.\nDev: We sent the drawings on Friday. They never arrived.\nMaya: Then someone has to drive them out to the site this morning.\nDev: I can leave now. The road along the water should be clear.\nRuth: While Dev drives, I'll call the foreman and tell him to hold the pour.\nMaya: Good. After the bridge is done, we meet again, here, at the same table."),
]
local = os.path.join(H, "local")
for p in POEMS:
    f = os.path.join(local, p["id"] + ".txt")
    if not p.get("text") and os.path.exists(f): p["text"] = open(f).read().strip(); p["status"] += " (from tests/local)"
json.dump({"poems": POEMS}, open(os.path.join(H, "poems.json"), "w"), indent=1, ensure_ascii=False)
print(len(POEMS), "entries,", sum(1 for p in POEMS if p.get("text")), "with text")
