"""Fill the one-button player (player-template.html) for each standalone page, with its program inside the page so nothing waits, its
icons and its share card. Run after the program's own builder, fix_thumbs.py and envelope.py.   usage: python3 make_pages.py"""
import html, json, os
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); T = open(os.path.join(H, "player-template.html")).read()
SITE = "https://hartswf0.github.io/cineosis-lab/lab/"
PAGES = [dict(file="found-odyssey-museum.html", prog="odyssey/museum.json", title="The Found Odyssey", short="Found Odyssey", kicker="Cineosis Lab · one button",
              sub="The Odyssey, line by line: each of Homer's lines said plainly, then answered by what archival people actually said on film.",
              desc="Homer's Odyssey, every line said plainly and answered by the words of real people on archival film. One button, full screen, four and a half hours in twenty-four books.",
              callname="Homer", callwho="<b style=\"font-weight:400;color:#efe9dd\">Homer</b> says each line, plainly.",
              icon="odyssey/museum-icon.svg", icon32="odyssey/museum-icon-32.png", touch="odyssey/museum-icon-180.png", og="odyssey/museum-share.jpg",
              foot="The archive's words come from the transcripts of tens of thousands of public-domain and archival clips; every answer is something a person actually said on film. Made in the Cineosis Lab."),
         dict(file="norse-half-moon.html", prog="norse/program.json", title="Norse Half Moon", short="Half Moon", kicker="Cineosis Lab · a found epic",
              sub="A voice memo about a hand-built house on the Half Moon Bay coast, read like Homer: seven books, each line answered by the archive.",
              desc="A voice memo about a hand-built Norse house on the Half Moon Bay coast, read like Homer in seven books, each line answered by the words of real people on archival film.",
              callname="The memo", callwho="<b style=\"font-weight:400;color:#efe9dd\">The memo</b> says each line, in its own voice.",
              icon="norse/icon.svg", icon32="norse/icon-32.png", touch="norse/icon-180.png", og="norse/share.jpg",
              foot="The memo is heard as it was recorded. The archive's words come from the transcripts of tens of thousands of archival clips; every answer is something a person actually said on film. Made in the Cineosis Lab.")]
for p in PAGES:
    prog = json.load(open(os.path.join(L, p["prog"]))); assert all("env" in s for s in prog["scenes"]), "run envelope.py first"
    blob = json.dumps(prog, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    out = T
    for k, v in {"TITLE": html.escape(p["title"]), "SHORT": html.escape(p["short"]), "DESC": html.escape(p["desc"]), "SUB": html.escape(p["sub"]), "KICKER": html.escape(p["kicker"]),
                 "CALLNAME": p["callname"], "CALLWHO": p["callwho"], "FOOT": html.escape(p["foot"]), "ICON": p["icon"], "ICON32": p["icon32"], "TOUCH": p["touch"],
                 "URL": SITE + p["file"], "OG": SITE + p["og"], "FIRSTAS": "video" if prog["scenes"][0].get("film") else "audio", "FIRSTAUDIO": prog["scenes"][0].get("film") or prog["scenes"][0]["audio"]}.items(): out = out.replace("{{" + k + "}}", v)
    if prog["scenes"][0].get("film"): out = out.replace('<link rel="preload" as="video" href="' + prog["scenes"][0]["film"] + '">', "")   # the film element buffers its own start
    out = out.replace("{{PROGRAM}}", blob)
    open(os.path.join(L, p["file"]), "w").write(out); print("wrote", p["file"], os.path.getsize(os.path.join(L, p["file"])) // 1024, "KB")
