"""The words a line and its answer share (by stem, content words only): what the matcher found, made visible on the page."""
import re
STOP = set("a an the and or but of to in on at by for with from as is are was were be been it its this that these those i you he she we they me him her us them my your his our their not no so if then than there here what who whom which when where how all any some one into out up down over under again very can will just do did does have has had am shall would should could may might must o oh let now upon thy thee thou ye like yeah um uh know get got gonna going really thing things kind sort".split())
def stem(w):
    w = re.sub(r"[^a-z']", "", w.lower()).strip("'")
    for suf in ("ings", "ing", "edly", "ed", "es", "s", "ly"):
        if len(w) > len(suf) + 3 and w.endswith(suf): return w[: -len(suf)]
    return w
def marks(a, b):
    A, B = a.split(), b.split(); sa = {stem(w) for w in A if stem(w) and stem(w) not in STOP}; sb = {stem(w) for w in B if stem(w) and stem(w) not in STOP}; both = sa & sb
    return [k for k, w in enumerate(A) if stem(w) in both], [k for k, w in enumerate(B) if stem(w) in both]
