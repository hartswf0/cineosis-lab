"""Build markov-sam-norse.html: the storyboard page with its suggestions inside it (so it opens at once), and its share card.
usage: python3 norse/make_storyboard_page.py   (after storyboard.py)"""
import json, os, sys
N = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(N)
D = json.load(open(os.path.join(N, "storyboard.json"))); T = open(os.path.join(N, "storyboard-template.html")).read()
open(os.path.join(L, "markov-sam-norse.html"), "w").write(T.replace("{{DATA}}", json.dumps(D, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")))
sys.path.insert(0, os.path.join(L, "odyssey")); import importlib.util
spec = importlib.util.spec_from_file_location("sa", os.path.join(L, "odyssey", "share_assets.py"))
src = open(os.path.join(L, "odyssey", "share_assets.py")).read(); src = src[: src.index("for kind, folder, prog")]   # the card maker only
g = {"__file__": os.path.join(L, "odyssey", "share_assets.py")}; exec(src, g)
th = D["pics"][D["books"][3]["lines"][0]["grounds"][0]]["img"]
g["card"](os.path.join(N, "storyboard-share.jpg"), "Norse Half Moon", "CINEOSIS LAB  ·  STORYBOARD", "Every line of the memo is a panel. Pick a picture, add figures, drag them into place, hear it in your own voice.", th)
print("wrote markov-sam-norse.html", os.path.getsize(os.path.join(L, "markov-sam-norse.html")) // 1024, "KB")
