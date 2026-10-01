# Source Pattern Atlas

Open `lab/source-patterns.html` on GitHub Pages, or use the Source Pattern Atlas door on the home page. This atlas reads **original archive order**. It does not propagate a WYGWYL interpretation back into the original film.

## What exists now

- Coverage audits of 60 cached source manifests. Coverage is the union of retrieved intervals divided by the cached first-to-last span; full-film completeness is unknown.
- 24 candidate windows across six source films: Master Hands, Moonwalk One, The Photographer, JFK Exhibit 3: Reconstruction Film, Duck and Cover, and All My Babies.
- Observations from 34 locally available silent excerpts. Codex inspected frames at 0%, 40% and 80% of each excerpt on 2026-09-26. These observations are in `observations.json` and remain separate from category readings.
- **Zero fully reviewed seed syntagms.** Full archive media requests returned HTTP 403 in the execution environment. The cropped, silent Tempest excerpts do not establish complete actions, soundtrack relations or autonomous boundaries. Their precise offsets inside source clips were not recorded by the existing pack. They are clearly labeled as excerpts and are never played as if they were complete source clips.
- Named-reader annotations with source times, relation, abstract structure, type, rival, evidence and counterevidence. Reviewed status records the reader's explicit assertion that they inspected the full interval, available sound, boundaries and surrounding context. It is not independent verification.

## Theory and conditions

Entities: `<source film>`, `<archive clip>`, `<candidate passage>`, `<visual observation>`, `<relation>`, `<reading>`, `<review provenance>`. Archive clips are not verified camera shots: frame samples from Duck and Cover and All My Babies contain visibly different imagery inside one clip.

Operations: [audit], [inspect excerpt], [play original], [read context], [encode relation], [save draft], [attest review], [export], [import], [rearrange in bench]. The initial experiment compares a supported description with its rival while preserving the exact source interval and membership. Intended forms are questions to test, not labels inferred from visual resemblance.

Invariants: missing records are retrieval gaps, not diegetic ellipses; sample observations do not automatically become classifications; source timestamps do not become story time; original order is preserved; imports must match the current passage's exact clip IDs and interval. Unknown and Outside this scheme are available. A generic clip count does not prove an autonomous shot or a montage type.

State progression: frame-sampled candidate → reader draft → reader-attested reviewed annotation. Changes are explicit saves. The candidate evidence stays intact beside the reader's annotation. Reopening an annotation restores its provenance. Annotation JSON can be committed as a separate reviewed dataset after editorial review; the UI does not pretend to write to Moving Image Archive's database.

## Seed selection and limitations

`build_atlas.py` deterministically selects four non-overlapping three-clip windows from each of six chosen films. Each window must have consecutive archive positions and touching source timestamps (50 ms tolerance). Windows are ranked by available local previews; ties use source order. Selection is biased toward footage already chosen for WYGWYL. This set is for discovery, not archive-wide prevalence estimates or classifier evaluation.

Candidate boundaries are arbitrary windows, not claimed autonomous segments. `questionsToTest` holds plausible rival constructions suggested by the partial observations; the recorded seed `reading.type` is always `unknown`. A pattern detector should eventually propose boundaries and relation hypotheses using full source audiovisual material, with film-level holdouts and calibrated abstention.

`data.json` retains every candidate's source clip records and exact source interval, source coverage audit, sampling method, date, analyst, missing-context flags and deciding question. The source audits include missing time intervals, nonconsecutive positions and overlaps. The source manifests remain authoritative originals and are not edited.

## Persistence and reuse

Browser annotations use `cineosis.source-patterns.v1`. Export writes `cineosis-source-patterns-review/1`: a portable annotation map with exact member IDs, interval, reader, timestamps, full-context attestation, and seed commit. Import validates every annotation before updating storage. Quota failures and invalid imports are visible. The UI does not silently submit reviews externally.

The Syntagm Lab handoff uses `source`, `first` and `count` URL parameters to load the original source neighborhood. An original-source passage starts at record time zero while keeping its source timestamps. Its reading remains unresolved. Full-film source access is also linked directly on the atlas player. Local previews never silently replace failed original playback.

## Verification

```
python3 lab/source-patterns/build_atlas.py
python3 -m unittest discover -s lab/source-patterns -p 'test_*.py'
node --test lab/source-patterns/review.test.mjs lab/syntagm/model.test.mjs
python3 lab/server.py 8765
```

Use the repo server for media byte-range support. The atlas is at `/lab/source-patterns.html`. Model tests separate gaps and overlaps, check seed provenance and deterministic window integrity, and reject imported reviews with altered source intervals or unsupported reviewed states.

Next data work: restore full source access; recover missing intervals; inspect all camera boundaries and soundtrack; refine candidate windows to autonomous passages; publish an editorially reviewed annotation dataset. Only then use the seed labels to assess automated classification.
