# The flip test

`python3 lab/syntagm/swap_test.py` → `swap.json`. Runs in about 12 s with numpy only.

**Question.** In a sequence someone cut, does the real order of two adjacent shots beat the same two shots swapped?
Everything else stays in place: the words under each slot and the shots before and after.
This is the first step toward *Bellman cineosis*: a next-shot value Q(s, a) is only worth learning if some signal can tell A→B from B→A.

**Method.**
- Each term scores the local window (three cuts, two slots) in both orders. The real order wins, loses or ties.
- Accuracy is wins ÷ (wins + losses). Chance is 0.5.
- Each result has an exact sign test, a Wilson 95% interval, and a permutation null (every sequence shuffled within its chapters, 200×) confirming the test sits at 0.5 when order means nothing. It does: every null mean is 0.49–0.51.

| term | reads | source |
|---|---|---|
| V visual continuity | cos of CLIP image embeddings across each cut | `cache/emb.npy` |
| S sign held | the top machine sign is the same on both sides of a cut | `lab-data.json` `aff_top` |
| F forward in source | same source film, later in-point (Metz's asserted chronology) | clip in-points |
| W words under shot | image · text of the words her voice speaks inside the shot | `words-emb.npy` |
| D cut direction | cos(e_b − e_a, t_b − t_a): the picture moves the way the words move | `words-emb.npy` |

**W and D have not run yet.** They need CLIP's text weights from huggingface.co, which this session's network policy blocks.
To run them, allow that host (or run anywhere the lab's other CLIP scripts run):
1. `python3 lab/syntagm/embed_words.py` writes `words-emb.npy` and `words-keys.json`.
2. Re-run `swap_test.py`.

## What was cut by whom

The four WYGWYL cuts were **not** cut by a person. `cutbastard/plan.py` fills each patch greedily from CLIP scores, with one rule per strategy:
- **drift:** add visual continuity with the previous shot;
- **scenes:** walk one source film in its own order;
- **cineosis:** add the beat's sign affinity;
- **suite:** add the forager's reviewed picks.

The forage cut has 88 shots, one per beat, with an edit note on each; who authored it is not recorded.

The only sequences in the repo that people certainly edited are the **archive films' own order**: 367 runs of ≥4 lab shots that abut in their source (5,744 shots, 150 films).

## Results

**The poem cuts** (accuracy [95% CI], decided pairs):

| cut | V visual | S sign held | F forward in source |
|---|---|---|---|
| suite | **0.658** [0.58–0.73] n=155 | **0.759** [0.58–0.88] n=29 | — |
| scenes | **0.742** [0.67–0.80] n=155 | **0.861** [0.71–0.94] n=36 | **0.650** [0.56–0.73] n=117 |
| cineosis | **0.658** [0.58–0.73] n=155 | **0.875** [0.74–0.94] n=40 | — |
| drift | **0.779** [0.71–0.84] n=154 | 0.513 [0.36–0.66] n=39 | — |
| forage | 0.549 [0.43–0.66] n=71 | 0.400 [0.20–0.64] n=15 | — |

Bold: p < 0.01.

**The archive films' own order:**

| slice | V visual | S sign held |
|---|---|---|
| all 367 runs | **0.551** [0.54–0.56] n=5,377 | 0.486 [0.46–0.51] n=1,730 |
| intertitles removed (415 runs) | **0.560** n=4,585, p < 10⁻¹⁵ | — |
| 1910s (almost all *Alice in Wonderland*, 1915) | **0.319** [0.26–0.38] n=216 | — |
| 1920s / 1930s / 1970s | 0.617 / 0.590 / 0.618 | — |
| 1940s | 0.499 | — |

## What it shows

1. **The test works: it recovers how each machine cut was built.**
   - Drift was built on visual continuity and scores highest on V (0.779). It was not built on signs, and its S is at chance.
   - Scenes is the only cut where F is defined, and it wins (0.650).
   - Cineosis was built on signs and scores highest on S (0.875).

   A flip signal that can tell four strategies apart can serve as a Bellman reward. But on these cuts it is circular: it reads back the rule that made them. These cuts are not evidence about editors.
2. **People editing real films keep visual continuity, a little.** V = 0.56 over 4,585 decided pairs, far past chance. CLIP similarity carries real order information, but most of what decides order is elsewhere.
3. **The machine sign does not see human order** (S = 0.486). Signs held across a cut predicted the machine cuts, not the people.
   The trials' strongest editorial signal (same sign held, z +3.6 to +7.2) was measured on these same machine cuts, so it too describes plan.py, not editors.
4. **Silent intertitles invert continuity.** In the 1915 *Alice* runs, text card → image → text card is an ABAB alternation, so the real order is *less* continuous than the swap (0.319).
   This is a Metz structure (a verbal code interleaved with the image track) that a visual-continuity reward would destroy. Any learned reward has to allow alternation.
5. **The forage cut shows nothing yet** (n=71).

## What follows for Bellman cineosis

- **Rewards.** Visual continuity is a real but weak prior (0.56). The machine sign is not a reward for human-like order. The poem terms (W, D) are untested.
- **Training data.** The four cuts cannot be demonstrations for inverse RL: they are plan.py's demonstrations. Human order has to come from:
  - the archive films (no poem);
  - flips made by people in the Studio (with the poem).
- **Next:** embed the words and run W and D. On the machine cuts, W should win for every strategy except drift, since each put the line in its patch intent. That is a check, not a finding. The finding needs human flips under her words.

## Limits

- Signs are machine readings (`aff_top`).
- Archive runs are shots the lab happened to find, not whole films.
- The decade slices are small and often one film per decade.
- Adjacent swaps only. Substitution flips (A→B against A→B′ from the pool) are the next test.
