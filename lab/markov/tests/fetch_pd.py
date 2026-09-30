"""Fetch the public-domain test texts from Wikisource (rendered page -> plain lines). Copyrighted poems are never fetched:
they are 'bring your own text' in the page and in tests/local/."""
import json, re, sys, urllib.parse, urllib.request, html
def page(title, host="en"):
    u = f"https://{host}.wikisource.org/w/api.php?action=parse&page={urllib.parse.quote(title)}&prop=text&format=json&redirects=1"
    j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "CineosisLab/1.0 (local research tool; python-urllib)"}), timeout=60))
    if "error" in j: return None
    h = j["parse"]["text"]["*"].replace("\n", " ")
    h = re.sub(r'(?s)<(style|script|table)[^>]*>.*?</\1>', '', h)
    h = re.sub(r'(?s)<div class="(?:ws-noexport|licenseContainer|wst-header)[^"]*".*?</div>', '', h)
    h = re.sub(r'<br\s*/?>', '\n', h); h = re.sub(r'</(p|div|dd|li|h\d)>', '\n\n', h)
    t = html.unescape(re.sub(r'<[^>]+>', '', h))
    t = re.sub(r'\[\d+\]', '', t); t = re.sub(r'[ \t ]+', ' ', t)
    t = re.sub(r'\n\s*\n\s*\n+', '\n\n', "\n".join(l.strip() for l in t.split("\n"))).strip()
    t = re.split(r'This work is in the public domain|This work was published before|Public domainPublic domain', t)[0]
    t = re.sub(r'^For other versions of this work, see[^\n]*\n', '', t).strip()
    return t
if __name__ == "__main__":
    for title in sys.argv[1:]:
        host, _, t = title.partition(":") if title.startswith(("de:", "en:")) else ("en", "", title)
        print("=====", title); print((page(t, host) or "MISSING")[:6000])
