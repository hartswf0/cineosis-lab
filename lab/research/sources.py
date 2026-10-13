"""SPONSOR AND PURPOSE. For every source film behind Rushes (1,540), who made it and what for:
  1. its Moving Image Archive page: creator (the sponsor or producer as the archive records it), date, original collection,
     synopsis, running time, the whole film's file, and where the archive got it (often an archive.org item)
  2. that archive.org item's own record, when there is one: sponsor, producer, description, subjects
Polite and resumable: one request at a time, a pause between, cached in research/sources.json. The films the lab's own films
use most go first, so the recurring cast is researched before the rest.
usage: python3 lab/research/sources.py"""
import json, os, re, time, urllib.request, urllib.error, collections
H = os.path.dirname(os.path.abspath(__file__)); L = os.path.dirname(H)
OUT = os.path.join(H, "sources.json")
UA = {"user-agent": "cineosis-lab (research; contact via github.com/hartswf0/cineosis-lab)"}
MIA = "https://www.movingimagearchive.com/sources/"
db = json.load(open(OUT)) if os.path.exists(OUT) else {}

def get(url, tries=0):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (429, 500, 502, 503, 504) and tries < 6:
            time.sleep(float(e.headers.get("retry-after") or 0) or 6 * (tries + 1)); return get(url, tries + 1)
        if e.code == 404: return None
        raise
    except Exception:
        if tries < 6: time.sleep(10 * (tries + 1)); return get(url, tries + 1)
        raise

# ---- which sources, in what order
keys = json.load(open(os.path.join(L, "rushes/keys.json")))["keys"]
slug = {}
for f in ("markov/library.json", "odyssey/library.json"):
    for s in json.load(open(os.path.join(L, f)))["shots"]:
        if s.get("src"): slug.setdefault(s["id"], s["src"])
for s in json.load(open(os.path.join(L, "lab-data.json")))["shots"]: slug.setdefault(s["id"], s.get("slug"))
weight = collections.Counter()
try:
    for u in json.load(open(os.path.join(L, "census/uses.json"))):
        if u.get("clip") in slug: weight[slug[u["clip"]]] += 1 if u["role"] != "word" else .05
except Exception: pass
order = sorted({slug[k] for k in keys if slug.get(k)}, key=lambda s: -weight[s])
todo = [s for s in order if s not in db]
print(len(order), "sources ·", len(db), "done ·", len(todo), "to read", flush=True)

def field(t, k):
    m = re.search(r'"' + k + r'":("(?:[^"\\]|\\.)*"|null|-?\d+)', t)
    if not m or m.group(1) == "null": return None
    v = m.group(1)
    return json.loads(v) if v.startswith('"') else int(v)
import concurrent.futures as cf
IA = cf.ThreadPoolExecutor(2)   # archive.org records are read alongside, never more than two at once
pending = []
def ia_read(rec, ident):
    j = get("https://archive.org/metadata/" + ident)
    if not j: return
    try:
        md = json.loads(j).get("metadata", {})
        pick = lambda k: (md.get(k) if isinstance(md.get(k), str) else "; ".join(map(str, md.get(k)))) if md.get(k) else None
        desc = re.sub(r"<[^>]+>", " ", pick("description") or ""); desc = re.sub(r"\s+", " ", desc).strip()
        rec["ia"] = {"sponsor": pick("sponsor"), "producer": pick("producer"), "creator": pick("creator"), "date": pick("date"),
                     "subject": pick("subject"), "description": desc[:2400] or None, "collection": pick("collection")}
    except Exception: pass
for n, s in enumerate(todo):
    rec = {"slug": s}
    html = get(MIA + s)
    if html:
        t = html.replace('\\"', '"')
        i = t.find('"metadata":{')
        meta = {}
        if i >= 0:
            blob = t[i + 11: t.find("}", i) + 1]
            try: meta = json.loads(blob)
            except Exception: meta = {k: field(blob, k) for k in ("creator", "source_url", "source_date", "original_collection", "public_domain_status")}
        rec.update({"title": field(t, "sourceTitle"), "year": field(t, "sourceYear"), "creator": meta.get("creator"), "date": meta.get("source_date"),
                    "collection": meta.get("original_collection"), "origin": meta.get("source_url"), "rights": meta.get("public_domain_status"),
                    "synopsis": field(t, "synopsis"), "running": field(t, "runningTime"), "film": (field(t, "sourceUrl") or "").split("?")[0] or None})
    time.sleep(1.5)
    o = rec.get("origin") or ""
    m = re.match(r"https?://archive\.org/details/([^/?#]+)", o)
    if m: pending.append(IA.submit(ia_read, rec, m.group(1)))
    db[s] = rec
    if n % 10 == 0 or n == len(todo) - 1:
        pending = [f for f in pending if not f.done()]
        json.dump(db, open(OUT, "w"), ensure_ascii=False, indent=0)
        print(f"[{n + 1}/{len(todo)}] {rec.get('title')} · {rec.get('creator')} · {(rec.get('ia') or {}).get('sponsor')}", flush=True)
IA.shutdown(wait=True)
json.dump(db, open(OUT, "w"), ensure_ascii=False, indent=0)
print("DONE", len(db), flush=True)
