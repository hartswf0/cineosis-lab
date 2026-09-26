"""Align the WGY storyboard (one generated shot per story beat) to the suite's 88 beats on her clock.

Both lists follow the suite in order and are the same length, but the storyboard splits beat 1 (bedroom, then the
reading) and beat 88 (the crowd, then the door), so it runs one ahead and one behind. The alignment is monotonic:
a shot keeps to its beat or the next one, and pays for stacking two shots on one beat or leaving a beat empty.
Similarity is the share of a beat title's words found in the shot's content and ekphrasis.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
STOP = set("the a an of to in on and with at from into as is are his her their its by for than then this that".split())
STACK, SKIP = 0.35, 0.45


def tok(s):
    return {w.rstrip("'s") for w in re.findall(r"[a-z']+", s.lower()) if w not in STOP and len(w) > 2}


def storyboard():
    seen, W = set(), []
    for r in json.load(open(os.path.join(LAB, "spine", "storyboard.json"))):
        if r["id"] not in seen: seen.add(r["id"]); W.append(r)
    return sorted(W, key=lambda r: int(r["id"][3:]))


def align(W, B):
    sim = lambda r, b: len(tok(r["content"] + " " + r["operativeEkphrasis"]) & tok(b[4])) / max(1, len(tok(b[4])))
    n, m, NEG = len(W), len(B), -1e9
    dp = [[NEG] * m for _ in range(n)]; bk = [[-1] * m for _ in range(n)]
    for j in range(m): dp[0][j] = sim(W[0], B[j]) - SKIP * j
    for i in range(1, n):
        for j in range(m):
            for jp, pen in ((j - 1, 0.0), (j, -STACK), (j - 2, -SKIP), (j - 3, -2 * SKIP)):
                if 0 <= jp and dp[i - 1][jp] > NEG and dp[i - 1][jp] + pen > dp[i][j]:
                    dp[i][j] = dp[i - 1][jp] + pen; bk[i][j] = jp
            dp[i][j] += sim(W[i], B[j])
    j = max(range(m), key=lambda j: dp[n - 1][j] - SKIP * (m - 1 - j)); path = [0] * n
    for i in range(n - 1, -1, -1): path[i] = j; j = bk[i][j]
    return path, [round(sim(W[i], B[path[i]]), 2) for i in range(n)]


if __name__ == "__main__":
    import collections
    W = storyboard(); B = json.load(open(os.path.join(LAB, "syntagma", "syntagma-data.json")))["beats"]
    path, s = align(W, B)
    c = collections.Counter(path)
    print("empty beats:", [B[k][0] for k in range(len(B)) if k not in c], " stacked:", [(B[k][0], v) for k, v in c.items() if v > 1])
    print("mean word overlap %.2f, zero-overlap shots %d" % (sum(s) / len(s), sum(x == 0 for x in s)))
    for i, (w, j) in enumerate(zip(W, path)):
        if s[i] == 0: print(" ", w["id"], "→ beat", B[j][0], "|", w["content"][:48], "||", B[j][4][:48])
