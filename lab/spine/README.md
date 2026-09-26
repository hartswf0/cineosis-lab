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
- **Duplicate ids:** 210 ids appear more than once in `total-cinome.json`.
- **Provenance unknown:** nothing on disk shows whether a person or a model set the order and the `syntagmaType` of each record. Settle that before using these as examples of human judgment.
