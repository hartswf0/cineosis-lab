"""Fold the steersman into the sea: the instruments (steer_build.py: every possibility's confidence against line, beat, sign, role;
the blend partner a sign asks for) and the captain's verdicts (cache/steer/captain_*.json: what is seen, KEEP / REPLACE / NOTHING,
the pick, a harsh confidence, the reason; per scene what it asks, a diagnosis, coherence, mood) into each book's sea/b<nn>.json.
usage: python3 steer_merge.py"""
import glob, json, os
H = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(H, "sea")
inst = json.load(open(os.path.join(H, "cache", "steer-inst.json"))); order = json.load(open(os.path.join(H, "cache", "captain-order.json")))   # the order the captains saw, frozen with their verdicts
cap = {}
for f in glob.glob(os.path.join(H, "cache", "steer", "captain_*.json")):
    try: cap.update(json.load(open(f)))
    except Exception as e: print("unreadable", f, e)
n_cap = n_shot = 0
for f in sorted(glob.glob(os.path.join(D, "b*.json"))):
    b = json.load(open(f))
    for s in b["scenes"]:
        I = inst.get(s["id"], {}); C = cap.get(s["id"]); O = order.get(s["id"], {})
        if C: s["captain"] = {k: C.get(k) for k in ("asks", "diagnosis", "coherence", "mood")}; n_cap += 1
        byk = {x.get("k"): x for x in (C or {}).get("shots", [])}
        for k, sh in enumerate(s["shots"]):
            conf = I.get(str(k), {}); sh["conf"] = conf.get(sh["id"])
            for c in sh.get("sea", []): c["conf"] = conf.get(c["id"])
            bl = I.get("_blend", {}).get(str(k))
            if bl: sh["blend"] = bl
            v = byk.get(k + 1)
            if v:
                ids = O.get(str(k), []); p = v.get("pick")
                pick = ids[p] if isinstance(p, int) and 0 <= p < len(ids) else None
                sh["captain"] = {"seen": v.get("seen"), "verdict": v.get("verdict"), "pick": pick, "conf": v.get("conf"), "why": v.get("why")}; n_shot += 1
    json.dump(b, open(f, "w"), separators=(",", ":"))
print("captain on", n_cap, "scenes,", n_shot, "shots")
