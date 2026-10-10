"""Icons and share cards for the one-button pages: an SVG favicon, 32 px and 180 px PNGs (the phone's home screen), and a 1200x630
share image (the page's own first picture, darkened, its title set over it) for link previews.   usage: python3 share_assets.py"""
import io, json, os, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
GOLD, INK, BG = (232, 192, 112), (239, 233, 221), (5, 5, 5)
SERIF = "/System/Library/Fonts/Supplemental/Baskerville.ttc"; MONO = "/System/Library/Fonts/Menlo.ttc"
# the marks: the Odyssey, a sun on the sea's line; Norse Half Moon, a half moon over the sea's line
SVG = {"odyssey": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#050505"/><circle cx="32" cy="34" r="13" fill="none" stroke="#e8c070" stroke-width="4"/><path d="M10 40h44" stroke="#efe9dd" stroke-width="4" stroke-linecap="round"/><path d="M18 49h28" stroke="#efe9dd" stroke-opacity=".45" stroke-width="3" stroke-linecap="round"/></svg>',
       "norse": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#050505"/><path d="M32 17a15 15 0 0 0 0 30z" fill="#e8c070"/><circle cx="32" cy="32" r="15" fill="none" stroke="#e8c070" stroke-width="2.5"/><path d="M10 49h44" stroke="#efe9dd" stroke-width="4" stroke-linecap="round"/></svg>'}
def mark(kind, n):
    s = 4; W = n * s; im = Image.new("RGB", (W, W), BG); d = ImageDraw.Draw(im); u = W / 64
    if kind == "odyssey":
        d.ellipse([(32 - 13) * u, (34 - 13) * u, (32 + 13) * u, (34 + 13) * u], outline=GOLD, width=int(4 * u)); d.line([10 * u, 40 * u, 54 * u, 40 * u], fill=INK, width=int(4 * u)); d.line([18 * u, 49 * u, 46 * u, 49 * u], fill=(120, 117, 111), width=int(3 * u))
    else:
        d.pieslice([17 * u, 17 * u, 47 * u, 47 * u], 90, 270, fill=GOLD); d.ellipse([17 * u, 17 * u, 47 * u, 47 * u], outline=GOLD, width=int(2.5 * u)); d.line([10 * u, 49 * u, 54 * u, 49 * u], fill=INK, width=int(4 * u))
    return im.resize((n, n), Image.LANCZOS)
def card(path, title, kicker, line, thumb):
    W, Hh = 1200, 630
    try: bg = Image.open(io.BytesIO(urllib.request.urlopen(urllib.request.Request(thumb, headers={"User-Agent": "cineosis-44-research"}), timeout=20).read())).convert("RGB")
    except Exception: bg = Image.new("RGB", (W, Hh), (22, 19, 15))
    r = max(W / bg.width, Hh / bg.height); bg = bg.resize((int(bg.width * r) + 1, int(bg.height * r) + 1), Image.LANCZOS); bg = bg.crop(((bg.width - W) // 2, (bg.height - Hh) // 2, (bg.width - W) // 2 + W, (bg.height - Hh) // 2 + Hh))
    bg = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(.6)).enhance(.42)
    shade = Image.new("L", (W, Hh)); ds = ImageDraw.Draw(shade)
    for x in range(W): ds.line([x, 0, x, Hh], fill=int(200 * max(0, 1 - x / (W * .85))))
    bg = Image.composite(Image.new("RGB", (W, Hh), BG), bg, shade); d = ImageDraw.Draw(bg)
    d.text((80, 150), kicker, font=ImageFont.truetype(MONO, 22), fill=GOLD, spacing=4)
    d.text((76, 196), title, font=ImageFont.truetype(SERIF, 104), fill=INK)
    f = ImageFont.truetype(SERIF, 34); y = 340; words = line.split(); cur = ""
    for w in words:
        if d.textlength(cur + " " + w, font=f) > 760: d.text((80, y), cur.strip(), font=f, fill=(207, 199, 184)); y += 46; cur = ""
        cur += " " + w
    d.text((80, y), cur.strip(), font=f, fill=(207, 199, 184))
    d.ellipse([80, 548, 94, 562], fill=INK); d.text((106, 543), "the line", font=ImageFont.truetype(MONO, 20), fill=(180, 174, 164))
    d.ellipse([250, 548, 264, 562], fill=GOLD); d.text((276, 543), "the archive answers", font=ImageFont.truetype(MONO, 20), fill=(180, 174, 164))
    bg.paste(mark("odyssey" if "Odyssey" in title else "norse", 72), (W - 80 - 72, 548 - 30)); bg.save(path, quality=88)
for kind, folder, prog, title, kicker, line in [("odyssey", H, "museum.json", "The Found Odyssey", "CINEOSIS LAB  ·  ONE BUTTON", "Homer's lines, said plainly, and answered by what archival people actually said."),
                                               ("norse", os.path.join(L, "norse"), "program.json", "Norse Half Moon", "CINEOSIS LAB  ·  ONE BUTTON", "A voice memo about a hand-built house on the Half Moon Bay coast, read like Homer and answered by the archive.")]:
    pre = "museum-" if kind == "odyssey" else ""
    open(os.path.join(folder, pre + "icon.svg"), "w").write(SVG[kind]); mark(kind, 32).save(os.path.join(folder, pre + "icon-32.png")); mark(kind, 180).save(os.path.join(folder, pre + "icon-180.png"))
    P = json.load(open(os.path.join(folder, prog))); th = (P["scenes"][3].get("thumb") if kind == "norse" else None) or next((s["thumb"] for s in P["scenes"] if s.get("thumb")), None)   # Norse: the coast
    card(os.path.join(folder, pre + "share.jpg"), title, kicker, line, th); print("wrote", kind)
