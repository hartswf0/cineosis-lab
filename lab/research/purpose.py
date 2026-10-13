"""From each source's records (research/sources.json) to four things the narrator can say without inventing:
  sponsor   who paid for or made it (the archive.org sponsor, else its producer or creator; uploaders, sites and 'N/A' dropped)
  kind      what sort of maker: government, corporation, school or institute, broadcaster, studio, amateur, unknown
  purpose   one sentence from the film's own catalogue description saying what it is for (credits and links removed)
  act       which part of the myth it belongs to, from what the description says it does:
            PROMISE (progress, industry, the future) · INSTRUCTION (how to live, work, behave) · SELLING (products, public relations)
            FEAR (war, danger, security) · DREAM (cartoons, features, fantasy) · WITNESS (people filming themselves, local life, testimony)
usage: python3 lab/research/purpose.py   ->  research/purpose.json"""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__))
db = json.load(open(os.path.join(H, "sources.json")))
JUNK = re.compile(r"^(n/?a|none|unknown|various|movie powder.*|.*free online movies.*|internet archive|prelinger.*|national archives?( and records admin.*)?|nara|archive\.org|public domain.*|.*\.(com|org|net).*|.*youtube.*)$", re.I)
def clean(v):
    if not v: return None
    v = re.sub(r"\s+", " ", str(v)).strip(" ;,.")
    v = re.sub(r"^\s*(sponsor|producer|produced by|creator)\s*:\s*", "", v, flags=re.I)
    if JUNK.match(v) or len(v) < 3 or v.count(",") >= 2: return None
    v = re.sub(r"\s*\((student film|uploader|editor)\)", "", v, flags=re.I)
    m = re.match(r"^([^,(]+), \(?([A-Z][^)]*?)\)?$", v)        # 'Sloan (Alfred P.) Foundation' style stays; 'Bryan (Julien)' -> Julien Bryan
    n = re.match(r"^(\w+) \(([^)]+)\)$", v)
    if n and not re.search(r"Foundation|Company|Corporation|Inc|Agency", v): v = f"{n.group(2)} {n.group(1)}"
    return v
def kind(s, rec):
    t = " ".join(str(x or "") for x in (s, rec.get("creator"), (rec.get("ia") or {}).get("collection"), rec.get("collection"), rec.get("title"))).lower()
    if re.search(r"\bu\.?s\.?\b|department|agency|office of|bureau|national|federal|army|navy|air force|government|council|congress|committee|administration|service\b|ministry|state of|city of|commission", t): return "government"
    if re.search(r"historical society|graduation|town day|woman's club|belmont|home movie|amateur|family films|collection: ", t): return "people"
    if re.search(r"university|college|institute|school|foundation|museum|association|society|church|league", t): return "institution"
    if re.search(r"tv|television|broadcast|news|cbs|nbc|abc\b|pbs|wgbh|radio", t): return "broadcaster"
    if re.search(r"pictures|studios?|productions?|film(s)? inc|disney|fleischer|terrytoons|paramount|universal|warner|mgm|rko", t): return "studio"
    if re.search(r"company|corporation|corp\b|inc\b|motors|electric|oil|steel|chevrolet|ford|bell|westinghouse|dupont|chrysler|shell|esso|kodak|ibm|at&t|public relations|co\.", t): return "corporation"
    return "unknown" if not s else "maker"
SKIP = re.compile(r"^(director|producer|sponsor|writer|music|narrator|cast|credits|camera|photography|animation|editor|production company|copyright|run ?time|source|keywords?|ia collection)\b", re.I)
def purpose(rec):
    for txt in ((rec.get("ia") or {}).get("description"), rec.get("synopsis")):
        if not txt: continue
        txt = re.sub(r"https?://\S+", "", txt); txt = re.sub(r"\([^)]*\d{4}[^)]*\)", "", txt)
        txt = re.sub(r"^.*?\b[A-Z]{2,}\d{3,}\w*,?\s*(\d{4})?\s*", "", txt)   # 'National Park Service National Parks ... AVA19377VNB1, 1992 The video ...'
        txt = re.sub(r"National Archives - .*? - .*?\(\d\d/\d\d/\d{4} - \d\d/\d\d/\d{4}\)\.\s*-?\s*", "", txt)
        parts, buf = [], ""
        for piece in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", txt):   # rejoin after initials and abbreviations: 'John H. Glenn', 'U.S. Army'
            buf = (buf + " " + piece).strip() if buf else piece
            if re.search(r"(\b[A-Z]\.|\b(Mr|Mrs|Dr|St|Jr|Sr|Gen|Lt|Col|Capt|Rev|No|Co|Inc|vs|Mt)\.)$", buf): continue
            parts.append(buf); buf = ""
        if buf: parts.append(buf)
        for s in parts:
            s = s.strip(" -–—")
            if re.search(r"sourced|transferr|digiti[sz]|upload|this (copy|version|print)|clocking in|runtime|running time|courtesy of|imdb|reel \d|part \d of|copyright|www\.|\b(I|I'm|my|we|our)\b", s): continue
            if len(s) < 25 or SKIP.match(s) or re.match(r"^[A-Z][\w .&']+ - ", s) or "National Security Council" in s or s.count(":") > 1: continue
            return re.sub(r"\s+", " ", s)[:260]
    return None
ACTS = [("FEAR", r"war\b|wartime|bomb|atomic|nuclear|civil defense|enemy|danger|disaster|accident|crime|drug|disease|propaganda|security|military|army|navy|soldier|invasion|fire\b|warning|threat|attack|safety"),
        ("SELLING", r"advertis|commercial|sales|salesm|product|brand|buy|shopping|consumer|public relations|promot|market|customer|store\b|retail"),
        ("INSTRUCTION", r"how to|teach|lesson|learn|training|instruct|guidance|manners|etiquette|posture|hygiene|health|student|classroom|educational|explains|demonstrat|proper|should|habits|behavio"),
        ("PROMISE", r"progress|future|industr|engineer|technolog|science|scientific|power|electric|dam\b|construction|build|rocket|space|aviation|airplane|railroad|highway|modern|research|develop|production|machine|steel|oil|atom"),
        ("DREAM", r"cartoon|animat|comedy|feature film|musical|drama|fantasy|fairy|plays the part|starring|story of a|adventure|romance|silent film|novel"),
        ("WITNESS", r"home movie|amateur|town|neighborhood|community|historical society|remembers|interview|oral history|family|documentary|depression|unemploy|workers|residents|daily life|graduation|parade|people of")]
def act(rec, k, pur):
    t = " ".join(str(x or "") for x in (rec.get("title"), pur, rec.get("synopsis"), (rec.get("ia") or {}).get("subject"))).lower()
    t = re.sub(r"national security council|central intelligence agency", "", t)
    if k == "people": return "WITNESS", 3
    if k == "studio" and re.search(ACTS[4][1], t): return "DREAM", 3
    scores = sorted(((len(re.findall(p, t)), a) for a, p in ACTS), reverse=True)
    if scores[0][0]: return scores[0][1], scores[0][0] - (scores[1][0] if len(scores) > 1 else 0) * .5
    return {"government": "INSTRUCTION", "corporation": "SELLING", "studio": "DREAM", "broadcaster": "WITNESS", "institution": "INSTRUCTION"}.get(k, "WITNESS"), 0
out = {}
for slug, rec in db.items():
    ia = rec.get("ia") or {}
    sp = clean(ia.get("sponsor")) or clean(ia.get("producer")) or clean(rec.get("creator")) or clean(ia.get("creator"))
    k = kind(sp, rec); pu = purpose(rec); a, sc = act(rec, k, pu)
    ti = re.sub(r"^(.*), (The|A|An)(\s*\(.*\))?$", lambda m: f"{m.group(2)} {m.group(1)}{m.group(3) or ''}", rec.get("title") or "")
    out[slug] = {"title": ti, "year": rec.get("year"), "sponsor": sp, "kind": k, "purpose": pu, "act": a, "fit": sc,
                 "film": rec.get("film"), "origin": rec.get("origin")}
json.dump(out, open(os.path.join(H, "purpose.json"), "w"), ensure_ascii=False, indent=0)
import collections
print(len(out), "sources ·", sum(1 for v in out.values() if v["sponsor"]), "with a sponsor ·", sum(1 for v in out.values() if v["purpose"]), "with a purpose")
print(collections.Counter(v["act"] for v in out.values()), collections.Counter(v["kind"] for v in out.values()))
for v in list(out.values())[:14]: print(f"  {v['year']} {v['title'][:34]:34} | {str(v['sponsor'])[:34]:34} | {v['kind']:11} | {v['act']:11} | {(v['purpose'] or '')[:90]}")
