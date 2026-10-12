"""The front page's doors show each page's own interface: a headless browser opens every door's page on the local lab server and
keeps a still of what it looks like (lab/doors/ui/<key>.jpg, 640x400). A throwaway browser profile; nothing of the user's.
usage: python3 lab/doors/ui_shots.py [--only href,...]   (the lab server on :8779)"""
import json, os, re, subprocess, sys, tempfile, hashlib, concurrent.futures as cf
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(H))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
idx = open(os.path.join(ROOT, "index.html")).read()
hrefs = sorted(set(re.findall(r'class="door[^"]*"[^>]*href="([^"]+)"', idx)))
hrefs = [h for h in hrefs if not h.startswith("http")]
if "--only" in sys.argv: hrefs = sys.argv[sys.argv.index("--only") + 1].split(",")
key = lambda h: re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-") or "lab"
from PIL import Image
def shot(h):
    out = os.path.join(H, "ui", key(h) + ".jpg"); png = tempfile.mktemp(suffix=".png"); prof = tempfile.mkdtemp(prefix="cineosis-shot-")
    url = "http://localhost:8779/" + h
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio", "--no-first-run", "--no-default-browser-check", f"--user-data-dir={prof}",
                        "--window-size=1280,800", "--virtual-time-budget=9000", f"--screenshot={png}", url], capture_output=True, timeout=90)
        im = Image.open(png).convert("RGB"); im.thumbnail((640, 400)); im.save(out, quality=78); os.unlink(png); return h, "ok"
    except Exception as e: return h, f"fail {str(e)[:60]}"
    finally: subprocess.run(["rm", "-rf", prof])
with cf.ThreadPoolExecutor(3) as ex:
    for h, r in ex.map(shot, hrefs): print(f"{r:4} {h}", flush=True)
UJ = os.path.join(H, "ui.json"); have = json.load(open(UJ)) if os.path.exists(UJ) else {}   # --only adds to the stills already kept
have.update({h: f"lab/doors/ui/{key(h)}.jpg" for h in hrefs if os.path.exists(os.path.join(H, "ui", key(h) + ".jpg"))})
json.dump(have, open(UJ, "w"), indent=0)
