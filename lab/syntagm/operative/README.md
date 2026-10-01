# Syntagm Lab: film ↔ structure

The operative surface replaces the default at both `lab/syntagm.html` and `lab/source-patterns.html`. The earlier coverage/annotation tool remains at `lab/source-audit.html`; the general archive passage bench remains at `lab/syntagm-bench.html`. Old `source/first/count` URLs redirect to the latter.

## Theory before implementation

Purpose: make a syntagm reading inspectable and manipulable on actual footage. Entities are a source edition, an interval, a block, a proposed cinematic sign, an ordered join, a passage reading, and an experimental variant. A block can be a camera shot, a title plus shot, or a multi-shot demonstration; the dataset says which. The six specimens are not a dataset of automatically classified camera shots.

Operations: find a worked reading, play a block or join, group/reverse/shuffle/repeat/remove/move blocks, shorten a duration, substitute a real realization from the sign palette, compare original and variant, and export/import the edit. The formula follows the currently playing arrangement. Moving to BOND restores the editable arrangement. On phones the film remains visible and the work stages can be swiped horizontally.

Invariants: the original is immutable; source time and edit time remain distinct; a new order does not inherit the original syntagm; the annotated image sign does not logically imply a syntagm; source data do not imply story time. The 45-sign ontology and Narrative Chemistry v1 bond laws are not modified. Symbols on nodes are proposed readings from the existing palette, each with a reason. All joins are actual hard playback cuts, with a strand-change notation; arrows are not claims of new chemical bond laws.

States: annotated original → editable realization → timed playback → original/variant comparison. Every edit is undoable; drafts are saved per specimen in local storage and can be exported. Failures to load media or import a source range are visible. No original archive metadata is overwritten.

## Six worked readings

| Type | Film and selected source interval | Evidence | Scope |
|---|---|---|---|
| Alternate | The Lonely Villa (1909), 336.60–384.75 | Connected telephone exchange, interrupted by cutting the wire | Selected passage within a larger siege |
| Parallel | A Corner in Wheat (1909), 327.494–497.764 | Recurring banquet / bread-shop comparison without a specified common clock | Shop title retained with its image block |
| Autonomous shot | A Corner in Wheat, 64.865–133.10 | Uninterrupted field tableau, between distinct episodes | Autonomy argued from surrounding images |
| Scene | Duck and Cover (1951), 356.49–386.80 | Alley approach, reaction and protective postures across views | Instructional extension; ends before the doorway dissolve |
| Bracket | Duck and Cover, 309.75–345.00 | Corridor and lunchroom are alternative instructional situations | Multi-shot blocks; didactic extension beyond fiction |
| Ordinary sequence | Duck and Cover, 102.669–114.50 | Pole → engine → departure omits the transfer to the vehicle | Qualified reading; scene is an explicit rival |

These are **Codex editorial working readings**, dated 2026-09-26. They are not attributed to Metz and are not independent ground truth. Complete source files were downloaded. Temporal contact sheets and cut candidates were inspected, including fine samples through the selected actions; the archive Duck and Cover transcript was also consulted. No claim of an uninterrupted human audiovisual viewing is made. The interface gives the reading, evidence, rival, scope and source instead of presenting an empty annotation form.

Descriptive and episodic specimens are deliberately unfilled. The revised eight-type system comes from Metz's later scheme. His 1966 article used an earlier six-type version. Reference: Christian Metz and Raymond Bellour, “Interview on Film Semiology,” in *Conversations with Christian Metz* (Amsterdam University Press, 2017), pp. 90–92. [Open book](https://tile.loc.gov/storage-services/master/gdc/gdcebookspublic/20/19/66/69/24/2019666924/2019666924.pdf#page=91).

## Media and provenance

The six included MP4 files are uncropped access derivatives, 480 pixels wide, H.264/AAC, with source audio retained. No soundtrack was added. Timings refer to these specific Internet Archive source files:

- [The Lonely Villa](https://archive.org/details/LonelyVilla): `LonelyVilla_512kb.mp4` → `villa.mp4`
- [A Corner in Wheat](https://archive.org/details/ACornerInWheat): `CornerInWheat_512kb.mp4` → `wheat.mp4`
- [Duck and Cover](https://archive.org/details/DuckandC1951): `DuckandC1951_512kb.mp4` → `duck.mp4`

The JSON records download URLs, SHA-256 hashes of complete input editions and published derivatives, source intervals, block boundaries, reading reasons and proposed signs. Posters come from the packaged video. The downloaded complete sources are not committed.

Duck and Cover is also in the existing Moving Image Archive corpus. The interface links that title, but does **not** transfer these edition-specific timestamps to its clips. The two Griffith films extend the reference corpus. No fabricated archive clip IDs or false matches are introduced. Annotation transfer back onto MIA requires matching frames between editions and checking each mapped boundary.

Rebuild from the three named input files in a directory:

```
python3 lab/syntagm/operative/build_examples.py /path/to/source-files
node --test lab/syntagm/operative/model.test.mjs
python3 lab/server.py 8765
```

## What TEST measures

The default comparison preserves the same blocks and durations and groups or reverses them. The autonomous-shot test halves duration. The displayed shuffle mean and range come from 499 seeded permutations of the original blocks. This is an arrangement control for **strand switches**, conditional on editorial strand assignments. It is not a significance test, a score of film quality, or evidence that Metz's theory is true. The original and variant play under A/B labels whose identities can be revealed. This is a local comparison aid, not a controlled blind study.

Every new join is clickable and plays from 1.5 seconds before that cut. Node substitution can cross films; the player loads the actual destination media. Audio follows each interval and may become discontinuous. There is no invented smooth soundtrack. Playback seeks are browser mediated, so live cuts are not promised to be frame-accurate. Exported ranges are the source for a frame-accurate offline render.

Export format: `cineosis-operative/1`, with baseline reading, ordered blocks, source and record ranges, proposed signs and reasons. Imports validate the source membership, bounds, minimum duration, strand identity and unique occurrence IDs. They do not submit anything to an archive or shared database.
