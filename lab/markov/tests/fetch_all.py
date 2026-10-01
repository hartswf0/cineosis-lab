import os, sys, time, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import fetch_pd as F
H = os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(H, "pd"), exist_ok=True)
JOBS = {"keats": "The Poetical Works of John Keats/Ode on a Grecian Urn", "coleridge": "Christabel; Kubla Khan; The Pains of Sleep (1816)/Kubla Khan",
        "frost": "Mountain Interval/The Road Not Taken", "stevens": "Harmonium (Stevens)/Thirteen Ways of Looking at a Blackbird",
        "hopkins": "Poems of Gerard Manley Hopkins/Felix Randal", "macleish": "Ars Poetica", "williams": "Spring and All/Chapter XXII",
        "iliad18": "The Iliad (Butler)/Book XVIII", "giles3": "Chuang Tzŭ (Giles)/Chapter III",
        "george": "de:Das Wort (George)", "holderlin": "de:In lieblicher Bläue"}
for k, t in JOBS.items():
    out = os.path.join(H, "pd", k + ".txt")
    if os.path.exists(out): continue
    host, _, tt = t.partition(":") if t.startswith("de:") else ("en", "", t)
    for a in range(4):
        try:
            x = F.page(tt, host); open(out, "w").write(x or "MISSING"); print(k, "ok" if x else "missing", len(x or ""), flush=True); break
        except Exception as e: print(k, e, flush=True); time.sleep(40)
    time.sleep(12)
