"""Record vetted picks: letters from contact.html -> clip ids in picks.json.

usage: python3 pick.py picks_batch.json   (batch: {"<n>": [["C", "note"], ...]})
"""
import json, os, string, sys

HERE = os.path.dirname(os.path.abspath(__file__))
cands = json.load(open(os.path.join(HERE, "candidates.json")))
path = os.path.join(HERE, "picks.json")
picks = json.load(open(path)) if os.path.exists(path) else {}
batch = json.load(open(sys.argv[1]))
for n, rows in batch.items():
    pool = cands[n]
    picks[n] = [[pool[string.ascii_uppercase.index(L)]["id"], note] for L, note in rows]
    print(n, [pool[string.ascii_uppercase.index(L)]["sourceTitle"][:28] for L, _ in rows])
json.dump(picks, open(path, "w"), indent=1, ensure_ascii=False)
