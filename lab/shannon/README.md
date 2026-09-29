# Cineosis Lab · Shannon Engine

A scene composer and archive search tool at `../shannon-engine.html`.

## Use

Choose a work, paste text, import a transcript/SRT/VTT, or dictate with browser speech recognition. Choose a compositional direction and an ending. Compose, watch, replace and lock scene anchors, then compare with independent retrieval in Test. Export preserves source IDs, source intervals, record timing, held frames and the input. Attached recordings remain local and are not embedded in the export. Audio transcription and final video rendering are not implemented.

The shelf contains all 23 requested literary works, 14 WYGWYL editorial scene scores, a traditional nursery rhyme and an original meeting transcript. Full texts are explicitly distinguished from original study briefs. A study brief does not constitute a trial of its source poem. Sources and publication statements are retained in tests.json. Reviews are user judgements, never computed semantic scores.

## Retrieval

The 15,149 image vectors are those in cache/emb.npy, indexed by cache/emb_ids.json. Text uses OpenCLIP ViT-B-32, laion2b_s34b_b79k. The browser tokenizer uses the same merge vocabulary. Long inputs are divided into 75-token chunks; their normalized vectors are averaged and normalized so the end of a stanza is not silently discarded.

The browser lazily loads a 64.9 MB weight-only quantized ONNX text tower, 7.8 MB image vectors and ONNX Runtime Web 1.22.0. Inference and archive scanning run in a dedicated worker. This avoids a hosted text service and keeps new text on the device. The first new query is a substantial download; cached shelf queries avoid it. English retrieval is strongest. Mobile memory availability can limit model loading; errors retain the current cut and leave cached studies usable.

Quantized text vectors agreed with the float32 ONNX encoder at cosine 0.993–0.995 on three held-out phrases. This is numerical validation, not language comprehension validation. The browser tokenizer was compared against Python on punctuation, English, Chinese and accented names. Image vectors are int8 approximations. Cached rows use the original full-precision encoder, so small ranking differences are expected.

The local server also exposes POST /api/shannon/retrieve with `texts`. Install `open_clip_torch` to enable it. The browser uses that endpoint on localhost and otherwise uses its worker. No new network service or credential is required.

## Composition

Beam search retains twelve partial paths across the scene sequence. Candidate affinity is combined with repetition penalties, source progression, explicit mode constraints, locks and increasing destination affinity. Arrival mode can introduce ending candidates directly from the destination query. Return reprises the opening anchor; Interweave preserves A/B anchors. Explicit locks take priority. These are editorial heuristics; no claim of a complete language parser or of Metz/Deleuze classification is made.

Each anchor can extend into up to two forward source neighbours, only when their source intervals are non-overlapping and separated by less than ten seconds. Missing duration is represented as an explicit held final frame. The independent baseline selects a single source interval per scene without the path constraints. Entropy is conditional on the top-64 retrieval pool and a fixed softmax temperature, not calibrated uncertainty about meaning. A screening judgement remains necessary.

## Rebuild / verify

```
python lab/shannon/make_tests.py
python lab/shannon/build.py
python lab/shannon/export_model.py
node --test lab/shannon/model.test.mjs
python lab/server.py 8765
```

`public_texts.py` is an optional source refresh; check line and stanza boundaries against the publisher before rebuilding. Current stanza boundaries are curated in public-texts.json. `export_model.py` requires torch, open_clip_torch, onnx and onnxruntime. Raw full-precision weights stay in ignored lab/models. Browser model and retrieval assets are repository-backed.

The structural tests cover every shelf cut, duration and source bounds, recurrence, alternation, lock precedence, ending changes under a fixed input, baseline differences and correct entropy. Browser checks covered 390×844 playback, desktop layout, worker-based unseen-text retrieval and zero JavaScript exceptions. These checks do not award artistic success to the poems.

## Licences

OpenCLIP model/export uses the OpenCLIP MIT licence in MODEL-LICENSE. ONNX Runtime Web is vendored with its MIT licence under vendor/LICENSE. Archive media retain their source provenance and are streamed from their existing URLs; no new licence is asserted over them. Literary text status and sources are stated per test.
