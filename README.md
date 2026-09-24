# Cineosis Lab

*Forty-four ways an image can think.*

A working instrument for Gilles Deleuze's taxonomy of cinematic signs — the **cineosis** — as systematised by David Deamer in *Deleuze's Cinema Books: Three Introductions to the Taxonomy of Images* (Edinburgh University Press, 2016). It has two parts:

- **[The Periodic Table of Cinematic Signs](https://hartswf0.github.io/cineosis-lab/periodic-table.html)** — the 44 signs (with opsign and sonsign split into two elements, 34a and 34b) laid out on Deamer's own structure: sixteen image types as columns, two signs of composition and one sign of genesis as rows, the movement-image's Peircean codes (111 … 333) and the time-image's 0 · 1 · 2 · 3 · ∞. Each element carries the test that decides it against its neighbours, the three signs it is most often confused with and what would flip a shot to each, a counterfeit, a confidence rubric with a single-shot ceiling, and a family of 4–6 archival shots, each with a reading and a confidence bar.
- **[The Lab](https://hartswf0.github.io/cineosis-lab/lab/)** — 4,788 shots from 1,075 films, sortable by sign, colour, era, subject, shot scale and visual similarity, in six modes: **wall**, **similarity map**, **ring**, **strata** (shots as stacks of frames), **cut-outs** (SAM 2.1 figures tracked through their shots, recombinable on a black table) and **reel** (a film that walks the table). The **inspector** scrubs any shot with a source-film timecode, frame stepping, R/M/A/B markers and sub-shot saving, shows a heat-mapped mini periodic table of machine sign-affinity, and overlays tracked segments that move with the video.
- **The film** — `cineosis-reel.mp4` (10 min) in the [Releases](https://github.com/hartswf0/cineosis-lab/releases): every sign as a title card with its deciding test, then its strongest shots with their readings.

## Run it locally

```bash
python3 lab/server.py 8765          # then open http://localhost:8765/lab/  (table: /periodic-table.html)
```

The local server adds what the static site can't: **live search** of movingimagearchive.com's shot index (the archive sends no CORS headers, so it is proxied and rate-limited) and **saving sub-shots** to `lab/assignments.json`. On GitHub Pages the lab runs in static mode: corpus search only, sub-shots kept in your browser with an export button.

## How it was made

| step | script | what it does |
|---|---|---|
| grounding | `grounding/g*.json`, `grounding/diff*.json` | Per sign: definition, a short Deamer quote with page, the scenes Deamer analyses in Section III, an operation, shot criteria, 8 visual search queries; then the differential: the deciding test, axis, 3 confusions with flip conditions, counterfeit, confidence rubric, single-shot ceiling. |
| search | `search.py` → `results/` | 366 queries against the archive's CLIP-style shot search (rate-limited, resumable). |
| vetting | `candidates.py`, `pick.py` → `picks.json` | Round-robin pools of ≤18 candidates per sign, one per film, chosen by eye from contact sheets. |
| readings | `readings/r*.json` | Per shot: confidence for its sign, a rival sign and its share, and the condition that would flip it. |
| table | `build_table.py` → `periodic-table.html`, `cineosis-table.json` | |
| colour · CLIP · similarity | `lab/analyze.py` | 5-colour palette and hue, CLIP ViT-B/32 zero-shot subjects and shot scale, t-SNE map. |
| sign affinity | `lab/affinity.py` | Every shot vs every sign (criteria text + read exemplars, leave-one-out). |
| clips | `lab/clipwork.py`, `lab/locate_thumb.py` | Filmstrips, audio analysis, and the exact frame each reading was made from (`read_t`). |
| segments | `lab/seg_track.py` | SAM 2.1 proposals directed by CLIP toward what the reading is about, plus face/person detector prompts; chosen objects tracked through the shot with SAM 2's video predictor. |
| film | `lab/render_reel.py` | Title cards + shots + captions → `cineosis-reel.mp4`. |
| lab data | `lab/build_lab.py` → `lab/lab-data.json` | Contract in `lab/DATA_CONTRACT.md`. |

To re-run the Python pipeline: `sh setup.sh` (creates `lab/.venv`, installs SAM 2, downloads the SAM 2.1 small checkpoint from Meta).

## Read this before citing anything

- **Readings are an editor's judgements, not measurements.** The confidence bars say how strongly a shot reads as a sign; the solid part is what the shot alone can show (capped by the sign's single-shot ceiling), the hatched part what the surrounding sequence would have to supply.
- **Machine affinity is a pointer, not a reading.** It puts the editor's own sign in its top five for about half the read shots (chance is 11%).
- **"In Deleuze's Cinema books" examples are recalled, not taken from Deamer.** Deamer's Section II names no films; check them against *Cinema 1* and *Cinema 2*.
- **Opsign and sonsign are two elements here; Deamer treats them as one sign.** They are separated because they differ in modality and a shot can be one without the other.
- **Deamer's book is quoted only in short phrases.** Its text is not in this repository.
- Some signs (mark, demark, destiny, peaks of the present, the discourse limits) are relations across shots; a single shot can only be one pole of them.

## Sources and credits

- David Deamer, *Deleuze's Cinema Books: Three Introductions to the Taxonomy of Images*, Edinburgh University Press, 2016.
- Gilles Deleuze, *Cinema 1: The Movement-Image* (1983) and *Cinema 2: The Time-Image* (1985).
- Shots from [movingimagearchive.com](https://www.movingimagearchive.com), largely public-domain educational, industrial, amateur and newsreel film (Prelinger and similar collections). Each shot links back to its page there; rights remain with their holders. Open an issue to have any item removed.
- [SAM 2.1](https://github.com/facebookresearch/sam2) (Meta, Apache-2.0), [OpenCLIP](https://github.com/mlfoundations/open_clip) ViT-B/32 LAION-2B weights, OpenCV, ffmpeg.
