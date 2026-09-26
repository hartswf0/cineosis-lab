# The prompt spine

The records that steered the generated images for the WYGWYL poems, copied from the author's machine
(`ANT/`, `CAT/` and three per-poem files). The images stay local.

| file | records | from |
|---|---|---|
| `total-cinome.json` | 847 | `ANT/total-cinome.json`, every poem |
| `storyboard-cinome.json` | 89 | `ANT/storyboard-cinome.json`, WGY001–WGY089 |
| `storyboard.json` | 89 | `CAT/storyboard.json` |
| `storyboard-sequence.json` | 1 | `CAT/storyboard-sequence.json` |
| `resurrecting-atlantis.json` | 63 | AT records |
| `departure.json` | 70 | SH records onward |
| `notice-me.json` | 83 | HT records onward |

**Record:** `id` (poem code + shot number, the order), `poem`, `timestamp`, `content` (the line the shot sets),
`imageType`, `syntagmaType`, `cineosisFunction`, `operativeEkphrasis` (the prompt), `image_path`.
`image_path` is cut to the filename. The filename carries the key:
`MR001__DS__Mood_Environment_Stabilizer__Title_arcs__<uuid>.png`.

## Known problems

- **"CS" is two classes:** Crystal Syntagma (72) and Chronological Syntagma (29). Use the full string, not the code.
- **`syntagmaType` mixes two vocabularies:**
  - Metz types: Descriptive 285, Chronological 29, Thematic Montage 4. (Crystal is not in Metz's table.)
  - Deleuze image types: Affection-Image 121, Action-Image 68, Perception-Image 64, Sonsign 62, Recollection-Image 52.
- **Poem codes don't all match `extract_poem_content.py`:**
  - BE records are "How to break off an engagement" (the script says BE = Bloodline, HT = the engagement).
  - HT records here are "How To Win My Heart" (4), plus line fragments misfiled into the `poem` field.
- **Missing labels:** the 90 NM (Nevermore) records have no `poem` or labels.
- **Duplicate ids:** 210 ids appear more than once in `total-cinome.json`. They are not errors: in all 210 the record is identical and only the image differs (`…_0.png`, `…_3.png`), i.e. 2–4 generated variants of one prompt. Each slot is a small set of alternatives.
- **Provenance unknown:** nothing on disk shows whether a person or a model set the order and the `syntagmaType` of each record. Settle that before using these as examples of human judgment.

## What the records already show (no images needed)

- **`syntagmaType` labels shots, not segments.** Metz's types span a run of shots. Here the type changes almost every shot:
  it is held to the next shot *less* often than in shuffled order (96 of 525 cuts, against 115 ± 8, z −2.4), like a
  rotation rule. Only SH has runs (`DDDDDDHHHH…`).
- **`imageType` and `cineosisFunction` are one label with two names**, paired one to one (Descriptive Image ↔ Mood
  Environment Stabilizer, Affection-Image ↔ Emotion Relay, Crystal-Image ↔ Temporal Reflection Loop, …).
- **The label is written into the prompt.** `full_prompt` begins with it (`DS · Mood Environment Stabilizer · …`), so
  images steered by the class are steered through the prompt text.

## Embedding the images (on the machine that has them)

```bash
pip install torch open_clip_torch pillow numpy
python3 lab/spine/embed_spine.py /path/to/the/images      # several folders allowed
python3 lab/spine/spine_test.py                            # → spine.json
python3 lab/syntagm/swap_test.py                           # now with the word terms
git add lab/spine/*.npy lab/spine/*-keys.json lab/spine/spine.json lab/syntagm/words-* lab/syntagm/swap.json
```

`embed_spine.py` finds the images by filename, embeds them with the lab's CLIP (the model of `lab/cache/emb.npy`), and
embeds every line and prompt, plus the words under each shot of the poem cuts (which the cloud session cannot fetch).
Unfound images are listed in `img-missing.json`. The outputs are float16 and small.

`spine_test.py` asks two things:
1. **The listener:** can the label a shot was made under be read back from the picture alone, on a poem held out?
   Also from the prompt text alone, to see how much of the label the prompt already carried.
2. **The flip:** along each poem, does the real order of two neighbouring shots beat the swap (visual continuity, the
   line each shot sets, the cut's direction against the lines)?
