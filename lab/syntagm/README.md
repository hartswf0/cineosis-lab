# Syntagm Lab

Open `../syntagm.html`, or the **Syntagm Lab** door on the home page.

The separate **Grand Syntagmatique** viewer (`../syntagma.html`) compares whole WYGWYL cuts against the voice. Its **rearrange ↗** button opens the selected cut and beat here, clipping boundary occurrences to the exact requested interval. Its heuristic category is not imported as a reviewed reading. This bench's menu links back to that viewer at the same suite offset. Browser-kept bet films are not currently transferable through this link.

## Purpose and theory before code

The lab tests what an arrangement establishes about time, space and action. It is a companion to the Deleuze–Deamer periodic table, not an extension of chemistry v1's valences. A Metz category is a passage reading, not a property calculated from a shot's sign affinity.

**Entities:** `<source clip>`, `<occurrence>`, `<passage>`, `<relation judgement>`, `<reading>`, `<revision>`. The same clip may have several occurrences with different trims, neighbors and functions. `{passage occurrences}` are ordered; `{source records}` preserve provenance.

**Operations:** [load], [trim], [assign strand], [reorder], [duplicate], [append], [remove], [compare], [read], [save], [export]. Ordinary source browsing becomes an experiment when a user keeps the materials fixed and changes their arrangement. The tension is between the intended construction and the reading supported by the result. Alternate and Group manipulate annotated strands; they do not declare a syntagm.

**Conditions and invariants:** all trims lie within their clips; occurrence IDs are unique; reordering preserves identities, trims and total screen duration; source, record and inferred story time are distinct; missing source intervals are retrieval gaps; unknown is a valid reading. The `segments` object in the existing shot data remains the visual object-tracking record and is not repurposed.

**State transitions:** initial candidate → relation judgements → proposed type → recorded reading → reviewed. Review requires evidence and a named reader. Editing an arrangement returns its reading to `needs-review`; it retains the previous evidence for reconsideration. A proposal is deterministic from the reader's answers, not an automatic visual classification. Original comparison is read-only. Undo restores the passage and its reading together. Saving is explicit.

**Assumptions and failure modes:** archive clips are not verified cinematic shot boundaries; a selected window may cross autonomous segments. A/B groups initially partition source films in WYGWYL and do not prove narrative strands. The same source can contain multiple places/times, and different sources can be edited into a fictional shared space. Source manifests may be incomplete. Video availability and browser codecs vary; local clips fall back to their recorded remote media URL and failures appear on the stage. The browser does not silently skip failed footage. Source sound can be auditioned; the WYGWYL poem soundtrack is not mixed here. No classification of the full audiovisual WYGWYL film is claimed.

**Change scenarios:** restoring a passage resets the comparison baseline to that restored revision; export preserves the edit history, current occurrences and source records. Appending different footage makes a new experiment; the same-inventory invariant applies specifically to reordering operations. A future model can suggest relation annotations with its provenance, but should not replace the reader's evidence or collapse unknown relations.

## Material and interaction

- Four WYGWYL cut plans: select a poem, a first occurrence, and a window of 1–24 occurrences. Their original suite offset is preserved for EDL export.
- Sixty cached source-film manifests load on demand. Select source material from the top menu or inspect the selected shot's original neighborhood. Coverage reports the union of retrieved intervals divided by the cached first-to-last span, not the whole film's running time.
- The 45-element periodic table shades duration-weighted **top-eight** machine affinity where available. Values outside that stored top eight are omitted, not treated as measured zero; the interface reports coverage. Clicking an element shows its deciding test, editor readings in the current passage and read examples to append. This is not a new sign classifier.
- Timeline tiles select occurrences. Assign A/B/C strands, reorder or trim, then compare against the original arrangement. The phone layout keeps the screen and timeline visible above one workspace pane; swipe or tap between Arrange, Read relations, and Signs & sources. Lists scroll inside their pane.
- Space toggles playback; arrows step clips; Cmd/Ctrl+Z undoes. Source sound is off until enabled.

## Portable passage format

`cineosis-syntagm/1` contains `id`, `title`, `context`, `offset`, `revision`, `items`, `reading`, `history`, and (on export) `shots`.

Each item has a unique occurrence `id`, source `shotId`, clip-relative `in`/`out`, and optional `strand`, `words`, and `originalRecord`. Current record intervals are recalculated cumulatively from `offset`. The source-film position is `shot.start + item.in`. Inferred story time is unresolved, not represented by either timestamp.

`reading` separates `intended`, `type`, `rival`, `scope`, `answers`, `evidence`, `counterevidence`, `analyst`, and `status`. `context` distinguishes an original source passage from a WYGWYL edit. A reading is not automatically propagated between them.

Passage JSON round-trips through Import and includes required source records. Browser saves use `cineosis.syntagm.v1`, capped at 30 passages, with quota failures visible. Export `cineosis-edl/1` provides `rec`, `src`, absolute clip URLs, occurrence IDs and a `syntagm` metadata extension. In Videotext Studio use Review → import: events become a reviewable branch and must overlap its spoken words. Generic source passages begin at zero; set an appropriate record offset before importing to the suite. The EDL is a picture edit, not a rendered video or a synchronized poem soundtrack.

## First experiment

1. Select an original source neighborhood or a WYGWYL passage. Check source coverage and passage boundaries.
2. Record the current relation evidence and a rival reading; leave unresolved fields unknown.
3. Assign strands based on evidence. Export the baseline passage.
4. Keep occurrences and trims fixed. Compare grouping, alternation and a seeded shuffle. Record which construction was intended and what the rearrangement actually supports.
5. Inspect changes in duration, source adjacency and strand recurrence separately from changes in the reading. A shuffle always changing a transition statistic is not proof of a meaningful change in interpretation.
6. Repeat on other source films and passages. If fitting a future classifier, split by source film and hold out examples. Do not infer archive-wide category prevalence from query-selected material.

The proposal logic covers the eight revised categories. It requires an autonomy judgement before assigning a type and distinguishes unspecified chronology from unknown evidence, comparison from simultaneity, and scattered ellipsis from organized phase summaries. A reader may retain a different recorded interpretation with counterevidence.

## Sources

Christian Metz, *Film Language: A Semiotics of the Cinema*, translated by Michael Taylor (1974), “Problems of Denotation in the Fiction Film,” especially pp. 119–133. The user's supplied chapter is the basis for the eight-type definitions. The earlier [1966 article](https://doi.org/10.3406/comm.1966.1119) has six major types; this interface uses the revised eight-type classification.

Footage and source metadata: [Moving Image Archive](https://www.movingimagearchive.com/), as already recorded in Cineosis Lab. Original source links accompany each occurrence.

## Build and verification

```
python3 lab/syntagm/build_data.py
node --test lab/syntagm/model.test.mjs
python3 lab/server.py 8765
```

Open `/lab/syntagm.html` on the local server, which serves the repository root and supports byte-range seeking. GitHub Pages uses `/cineosis-lab/lab/syntagm.html`. Do not use Python's basic `http.server` for playback checks: it does not honor the byte-range requests needed to seek to clip in-points. The player reports a failed seek instead of silently playing from zero. The build creates a compact entry point containing cut occurrences, their source records, read exemplars and the source manifest index. It does not modify the chemistry ontology, source footage or existing edits. Source manifests remain lazy-loaded. Tests cover all eight inference paths, insufficient evidence, coverage gaps/overlaps, occurrence identity, reorder preservation, source-time separation, EDL offsets, and invalid imports.
