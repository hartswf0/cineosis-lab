"""Fill the one-button player (player-template.html) for each standalone page.   usage: python3 make_pages.py"""
import os
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H); T = open(os.path.join(H, "player-template.html")).read()
PAGES = [("found-odyssey-museum.html", "odyssey/museum.json", "The Found Odyssey",
          "Homer's lines, said plainly, and answered by what archival people actually said.",
          "The whole found Odyssey with one button: each line of Homer said plainly, then answered by the archive's own voices, full screen with subtitles, from the first book to the last."),
         ("norse-half-moon.html", "norse/program.json", "Norse Half Moon",
          "A voice memo about a house on the Half Moon Bay coast, parsed like Homer into books and lines, and answered line by line by what archival people actually said.",
          "A found epic: a voice memo about a hand-built Norse house on the California coast, read like Homer, each line answered by the archive's voices, full screen, one button.")]
for f, prog, title, sub, desc in PAGES:
    open(os.path.join(L, f), "w").write(T.replace("{{PROGRAM}}", prog).replace("{{TITLE}}", title).replace("{{SUB}}", sub).replace("{{DESC}}", desc)); print("wrote", f)
