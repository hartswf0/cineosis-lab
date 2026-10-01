# Routing: archive clips to vertebrae

Made by `route.py` (read its docstring for the method). 682 vertebrae, a pool of 36,144 archive clips.

**The bridge.** A ridge map from LAION CLIP to OpenAI CLIP, fitted on the 15,149 clips read both ways. On
1,500 held-out clips the mapped vector finds its own clip first 95% of the time and in the top ten
99%. The map is fitted on images; words go through it too, which is weaker, so words count half.

**The route** uses 585 different clips from 293 films. Mean fit (z-score of affinity over the pool)
3.48, against 3.75 for the affinity-only pick: what the route gives up to cut the way the syntagmas ask.

How often each rule is realised on the cut into its vertebra:

| rule | route | affinity only |
|---|---|---|
| ACTION | 15/49 (31%) | 0/49 (0%) |
| AFFECTION | 89/89 (100%) | 55/89 (62%) |
| AS | 1/1 (100%) | 0/1 (0%) |
| CRYSTAL | 37/51 (73%) | 3/51 (6%) |
| CS | 20/61 (33%) | 0/61 (0%) |
| DS | 201/217 (93%) | 148/217 (68%) |
| FLASHBACK | 3/3 (100%) | 0/3 (0%) |
| PERCEPTION | 33/43 (77%) | 17/43 (40%) |
| RECALL | 19/36 (53%) | 8/36 (22%) |
| SONSIGN | 24/45 (53%) | 1/45 (2%) |
| TM | 3/4 (75%) | 0/4 (0%) |

What this does not show: that the cuts read as their syntagmas to a viewer. The rules are operational stand-ins (same
film later in it for chronological; a returning clip for crystal and recollection; close-ups for affection). A screening
says the rest.
