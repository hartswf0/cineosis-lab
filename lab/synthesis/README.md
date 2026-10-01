# Live synthesis: Metz and Deleuze

Two additive pages: `lab/metz-synthesis.html` and `lab/deleuze-synthesis.html`. These are experimental applications of the theories, not claimed implementations of the theorists' own generative rules.

## Entities and operations

The input is arbitrary text or browser speech recognition. A transparent lexical parser proposes a construction; the editor can override it. The record is an ordered list of media intervals, source references, record times, explicit held frames, proposed signs and reasons. Synthesis is debounced while typing. During playback the next score replaces the queue at an interval boundary; the current interval is not interrupted. This prototype exports the current score, not a complete history of every live revision.

Metz operations: alternate, ordinary sequence, scene, parallel, bracket, descriptive, episodic and autonomous shot. Deleuze-inspired operations: action/response, suspend response, return/difference, separate voice/image and attend to intensity. They make actual changes to order, duration, repetition and gaps. A proposed type is not awarded as a verified property of the generated passage. Source order supports only the relations the existing annotations justify. A reordered passage must be read again.

The sign palette is the existing 45-entry Deamer-derived catalogue. Selected signs bias free retrieval through existing editorial annotations. It does not convert a label into evidence of a new sign. Source-locked passages retain their original ordering for the operation to transform; palette choices do not replace blocks there.

## Material and limits

`build_catalog.py` gathers only local clips, measures durations with ffprobe, and adds source-bound blocks from the six operative syntagm specimens. The catalogue contains 361 playable intervals at build time. No `narrative-data.json` rankings or WYGWYL beat-to-shot assignments are used. Existing descriptions and original search hints still reflect historical foraging; search hints are weighted less and labelled separately. This is not a corpus-independent or learned semantic engine.

Free retrieval uses token overlap in descriptions, titles and subjects plus optional sign matches. It cannot establish identity, negation, causality or story-time from arbitrary language. Unknown vocabulary is reported as structural fallback. Word cues detect broad operations; they do not fully parse propositions. In particular before/after both request succession, without a general semantic role solver. The eight Metz proposals have unequal evidential support: scene requires actual source neighbours, descriptive requires evidence of spatial coexistence, episodic requires evidence of stages. The UI exposes these limits.

A/B keeps the available material fixed and compares interval order or response suspension. It reports cut counts, duration and explicit held-frame time, not artistic quality or semantic accuracy. No entropy is displayed because retrieval weights are not calibrated probabilities.

Speech recognition starts only after Speak, uses the browser's implementation/service, and may be unavailable. The user can always type. Optional read-aloud is browser synthetic speech independent of picture time; no voice recording is saved. Source sound is muted initially and can be enabled. Playback cuts are browser mediated, not frame-accurate. Exports contain source and record timing for a subsequent render.

## Verification

```
python3 lab/synthesis/build_catalog.py
node --test lab/synthesis/model.test.mjs
python3 -m http.server 8765
```

Tests cover meaningful differences under minimal language changes, source bounds across all modes, explicit held-frame accounting, recurrence, black intervals, unsupported vocabulary and actual sign-guided retrieval. No original ontology, media, annotations or saved edits are mutated.
