# Trials of Narrative Chemistry v1

Run `python3 lab/chemistry/trials.py`; the results are in `trials.json` and shown in `lab/chemistry-trials.html`. The ontology under test is frozen in `ONTOLOGY-v1.md`. The four predictions were fixed in the script before the first run.

**Question.** Can Narrative Chemistry predict, generate or distinguish films that the ordinary Cineosis taxonomy cannot?

**Instrument.** Every shot is labelled with its highest-affinity sign (`lab-data.json` `aff_top`). For all 1,408 pool candidates this equals the sign the pool curated them for, so the four WYGWYL cuts and the generated films are read the same way.

**The four cuts are machine cuts.** Suite, scenes, cineosis and drift were made by `lab/cutbastard/plan.py`, which fills each patch greedily from CLIP scores with one rule per strategy: drift adds visual continuity, scenes walks one source film, cineosis adds sign affinity, suite adds the forager's reviewed picks. They are called the plan.py cuts below. Every verdict that compares against them, or reads their adjacency, describes plan.py's strategies, not human editing (see `lab/syntagm/SWAP.md`, "What was cut by whom"). The predictions were written as if the cuts were human; their wording below is corrected, their numbers are unchanged.

**Blind synthesis.** The four plan.py cuts are hidden. Seven films per poem are built from the poem's clock, beats and candidate pools only, with two slots per beat:
- two baselines: random, and the ordinary taxonomy (the best-ranked candidate per slot);
- five chemistry generators: strongest lawful bond, resonance, one break, a blind compound laid over the slots, and that compound's isomer.

## Results

**Distance to the plan.py cuts** (mean over 14 poems × 4 cuts; lower is nearer):

| film | transitions | image types | signs | in time |
|---|---|---|---|---|
| B-random | 0.309 | 0.3967 | 0.5925 | 0.8487 |
| B-taxonomy | 0.3579 | 0.4369 | 0.6149 | 0.8518 |
| G-bond | 0.4816 | 0.4703 | 0.6109 | 0.8438 |
| G-resonance | 0.6256 | 0.4565 | 0.6196 | 0.8424 |
| G-break | 0.4147 | 0.4449 | 0.5953 | 0.8478 |
| G-compound | 0.381 | 0.4274 | 0.5762 | 0.842 |
| G-isomer | 0.3542 | 0.4134 | 0.5874 | 0.8478 |
| plan.py cuts to each other | 0.3211 | 0.4381 | 0.6119 | 0.8637 |

**Adjacency.** Each plan.py cut's adjacent pairs against 2,000 shuffles of its own shots, as z-scores:

| cut | same sign | rhyme | resonance | break → | back ← | within |
|---|---|---|---|---|---|---|
| suite | +3.62 ▲ | -0.57 | +0.84 | +0.55 | -1.78 | -1.33 |
| scenes | +6.57 ▲ | -1.51 | -0.49 | -3.36 ▼ | -1.92 ▼ | +0.62 |
| cineosis | +7.18 ▲ | -1.72 | +0.89 | -1.30 | +0.43 | -4.09 ▼ |
| drift | +0.96 | -1.08 | +3.04 ▲ | +0.36 | -0.02 | -2.17 ▼ |

## Verdicts
- **P1: refuted.** The claim was that chemistry films sit nearer the plan.py cuts' transitions than random films. Every chemistry generator is farther away: strongest bond 0.4816, resonance 0.6256, against random 0.309. Random films sit as near the plan.py cuts as those cuts sit to each other (0.3211).
- **P2: refuted.** No chemistry generator beats the ordinary taxonomy on transitions or on time-aligned image type in a significant number of poems (sign test, p < 0.05).
- **P3: refuted.**
  - Rhyme (two different signs of one image type side by side) falls below chance in all four cuts.
  - The break into time is at chance, and below it in scenes (-3.36).
  - Resonance is over-represented only in drift (+3.04).
- **P4: holds.** The isomer keeps the compound's signs and reorders only its bonds. That moves the transition spectrum as far as a different inventory does: 0.3132 against 0.3132. (The two means coincide; the per-poem values differ.) The signs themselves stay closer: 0.1631 against 0.327. The isomer's inventory is not exactly the compound's, because a slot without its sign falls back to a neighbour.

## What this means
- **v1 is nearly vacuous as a law of linear cuts.** A single cut may join any two signs, so no pair in the plan.py cuts breaks it (0 of 644). It speaks only through the bonds it favours, and the four cuts refute those preferences.
- **The strongest signal in the plan.py cuts is one v1 has no word for: the same sign held across a cut.** Suite +3.62, scenes +6.57, cineosis +7.18. v1 files it under rhyme, together with the different-sign rhyme these cuts avoid. It is plan.py's habit, not an editorial one: in the archive films' own order, cut by people, the same machine sign held across a cut is at chance (0.486, `lab/syntagm/SWAP.md`).
- **Ordering is real.** Same atoms, different film (P4). This is the one chemical idea the trials support.
- **Resonance distinguishes drift from the other three cuts.** It is a signature of one of plan.py's strategies, not a general law.

## What v2 would have to earn (and the test for each)
1. **A continuity bond:** the same sign kept apart from rhyme. Test: a generator using it moves nearer human-cut order than random. The plan.py cuts can't serve as that target; the archive films' own order or people's choices can.
2. **Bond strengths learned from measured order**, not asserted. These z-scores describe plan.py, so strengths meant to model editing have to be learned from human order. Test: that generator beats random and the taxonomy on transitions (P1 and P2 re-run).
3. **A drift mode:** raise resonance and lower within-regime cuts. Test: its spectrum sits nearer the drift cut than the other three do.
4. **People, not the instrument:** the blind screening room in `chemistry-trials.html`. Eight films per poem, the plan.py suite cut among them, each rated 1–5 as recognizable, surprising and usable, with a guess at which one is the suite cut. The ratings export as JSON.

## Limits
- One label per shot.
- Generators pick only from the beat pools.
- Slots are equal in length, and the plan.py cuts' are not.
- The four plan.py cuts follow four different strategies, so the "ceiling" is their spread, not a single target. None of them is a human cut.
