# Cineosis Lab

Deleuze's 44 cinematic signs, after David Deamer: a periodic table to read them, a lab of archive shots to find them, and films cut from those shots.

**Open it:** https://hartswf0.github.io/cineosis-lab/ — nothing to install.

## Use it in three moves

1. **Read a sign.** Open the [periodic table](https://hartswf0.github.io/cineosis-lab/periodic-table.html) and click an element. You get the test that decides the sign, the three signs it is confused with and what would flip a shot to each, and 4–6 archive shots with a reading and a confidence bar.
2. **Find shots.** Open the [lab](https://hartswf0.github.io/cineosis-lab/lab/). Click a sign in the small table on the left: the wall keeps only its shots. Add a decade, a colour band or a subject to narrow it; the line under the top bar lists every filter with a ✕ to drop it. Click a shot: the inspector plays it from the frame its reading was made from. Keys `1`–`8` switch views (wall, similarity map, ring, strata, cut-outs, reel, montage, WYGWYL); `?` lists every key.
3. **Watch a film.** Open [WYGWYL · four cuts](https://hartswf0.github.io/cineosis-lab/lab/wygwyl.html). Pick Suite, Scenes, Cineosis or Drift, or `G` for all four in one frame, and press play. The poem line, the shot's source film and the signs of its beat follow the picture. `←`/`→` step shot by shot; switching cuts keeps the time.

## What is in it

- **The periodic table** — 45 elements: the 44 signs, with opsign and sonsign split into 34a and 34b, on Deamer's structure (sixteen image types as columns; two signs of composition and one of genesis as rows; the movement-image's Peircean codes 111 … 333 and the time-image's 0 · 1 · 2 · 3 · ∞).
- **The lab** — 15,149 shots in two collections: *cineosis* (4,788 shots found sign by sign, 253 of them read) and *wygwyl* (the WYGWYL Forage Suite's candidates). Filter by sign, colour, era, subject, shot scale and visual similarity. The inspector scrubs with a source-film timecode, frame stepping, R/M/A/B markers and sub-shot saving, shows the machine's sign affinity as a heat-mapped mini table, and overlays SAM 2.1 segments tracked through the shot.
- **WYGWYL** — a 24-minute poem suite (14 films, 88 beats) cut four ways from archive footage, one full-frame shot per 6–12 s patch, no shot repeated: **Suite** (closest to the suite's treatment), **Scenes** (each line from one film, in that film's order), **Cineosis** (chosen for the beat's signs), **Drift** (each shot follows the one before). The films stream from the [wygwyl-v1 release](https://github.com/hartswf0/cineosis-lab/releases/tag/wygwyl-v1); each cut's shot list, story map and patch genome are in `lab/wygwyl/cuts/<cut>/`.
- **Videotext** (`lab/videotext.html`) — the whole poem as the editor, after the Videotext sheets (grip the text · open the archive · couple word and shot · turn text into time · assemble and release). Grip a word, phrase, line, stanza or passage (keys `1`–`5`); the archive opens on shots whose reviews match the words, shots under the beat at that time, and the four cuts' picks; couple one (`C`) and it plays at those words over the cut you choose. Word times are spread across each spoken stanza by length and punctuation. Your film stays in the browser; a share link, an edit list (.json), a marker file (.vtt) and numbered versions release it. Every cell of the sheets that is a way of seeing is a view (127 of them, in `lab/videotext/views-*.js`): pick one for the archive pane, or press `V` for the view wall, which shows them full size by sheet: 02 Open the archive (trees, rings, spirals, strips, funnels, facets, concordance, KWIC, similarity maps, depth stacks), 04 Couple word and shot (drag to couple, clip basket, matrix bind, pin to an in-point, reassign), 05 Turn text into time (word duration, parallel channels, time remap, and live views that follow the playhead) and 06 Assemble and release (transitions the player performs, match cuts, beat cuts, auto sequence, reels, versions). The words keep her real timing, from the spoken alignment in `bets/kernel-data.json`. They are no longer spread evenly over each screen cue, which put them a median of 6.8 s off her voice. Saved work and old share links move onto the same words as spoken, by their text. The picture follows the voice by nudging its speed (a jump only past 0.5 s), and Videotext shares the lab's clock (`lab/clock.js`) with the Studio, ABC FLIX and the Bets.
- **Videotext Studio** (`lab/videotext-studio.html`, `lab/videotext-studio/`) — Videotext with the 127 views from the sheets (pick one for the archive pane, or `V` for the view wall). Every view plays its shots as live loops (the Tempest loops and local clips from this site, the CDN otherwise, within a decoding budget) and, while the film plays, moves with the poem: what you hold follows her voice (`W` toggles). Touching a view puts the stage on that view's branch of the film: couplings, lifts and transitions made there change only the branch. The stage shows the branch; *▷ changes* plays what it changed; *merge into main* writes those changes into the main film at their times; *discard* drops it. Branches with no changes vanish. A site can hold a **stack** of shots (Shift+C, Shift-drop, or drop on “add to the stack”): they take turns across its words, or play all at once as a mosaic. The **tray** (`T`, or drop a shot on it) keeps shots for later in the lab's shared bin (`cineosis.bin.v1`, which the Bets read too). **Drag** any shot (from a view, the archive or the tray; long-press on a phone) onto a word, the timeline, the view wall's **cut ribbon** (the film on the stage around you, with the playhead) or the monitor. Tiles keep playing through redraws, and while the film plays the next line's shots are fetched ahead. Coupling stays **loose**: drag a coupling on the timeline or ribbon to slide it off its words, or drag an end to trim it. It snaps gently to word edges, the other shots and the playhead; Alt places it freely. It still belongs to its words (⇤ puts it back, ⇲ re-seats it under where it sits). Its edges can be hard, soft, softer or fuzzy (a crossfade in and out). A shot you just **like** (♡ on any tile, `H`, or drop it on a stanza's gutter) stays near those words without going into the film. It floats under its stanza, shows as a heart on the timeline and ribbon, and is gathered in the *Loose Associations* view. Drag it onto words when it's time. **Timing:** the words keep her real timing, taken from the spoken alignment in `bets/kernel-data.json`. Word times used to be spread evenly across each screen cue, which put them a median of 6.8 s off her voice; saved work moves onto the spoken words by their text. Pictures follow the voice by nudging their speed (a hard jump only past 0.5 s), wait while the audio buffers, and the transport shows the measured sync. The **wall** holds 1–4 views at once (`Q`), and views too wide for their box zoom to fit. **Review the film** (`R`) shows:
- what the main film holds, per poem;
- open branches that are not merged;
- whether every source loads;
- the film's fingerprint, and whether it has changed since the last export;
- every cut in order, clickable to screen from.

It exports the lab's `cineosis-edl/1` (every event, your couplings, the text cards), CMX 3600 for an editor, and markers. An EDL imports back onto a branch you can screen before merging. ⌘Z / ⌘⇧Z undo and redo any change to the film.

**On the wall, the phone first:**
- Every touch shows a ring.
- A shot you touch opens big in the **peek** (couple, stack, like, tray, full screen).
- The player comes small, medium or large (`B`).
- The timeline under the title zooms from the whole poem to the passage to 36 s with her words under the shots (pinch, ⌘/Ctrl-scroll, or − / +). Drag along it to scrub, and it ticks at each word.
- Views zoom from 50% to 300% (pinch, ⌘/Ctrl-scroll, − / +).

**Feel (`lab/feel.js`, shared with ABC FLIX):** short synthesised sounds and haptics for select, grab, snap, drop, couple, like, merge, undo and warnings. On iPhone it uses Safari's switch haptic. The sounds step back under her voice. `S` cycles sound + touch, touch only, or off. Kept in `vtstudio.*` storage, separate from Videotext's.
- **ABC FLIX** (`lab/abc-flix/`) — the ABC FLIX harness (ICARO-PRO engine + ARC-TUNNEL) ripping lab footage: a sign's read shots, a WYGWYL beat or the Studio film, each shot filed on the probability track its evidence earns. See `lab/abc-flix/README.md`.
- **Narrative Chemistry** (`lab/chemistry.html`, `lab/chemistry/`) — each poem as a compound.
  - **Atoms and valence:** the 45 signs are the atoms. Composition holds 2, genesis holds 3, opsign and sonsign hold 1, and the lectosign holds 4.
  - **Bonds are cuts:** − a cut, = shared time, ≡ a rhyme within one image type, ⇌ resonance between signs a shot can flip between (the confusion table), → the break from movement-image into time-image, ··· a loose association.
  - **Ligands** are the sound table's elements, bound IN, OFF or OUT; her voice binds OUT.
  - **Reactions:** flip (the table's conditions), condense (composition into genesis), break (a sound move from Deamer p.168 as catalyst), crystallise and read.
  - **Natural compounds** are measured: `chemistry/build_chemistry.py` builds them from each poem's beat pools and suite cut.
  - **Syntheses:** each natural compound has a name and reading, plus one new synthesis per poem, in `chemistry/author.py`, which checks every bond and valence.
  - **The bench** makes new compounds and saves them in `cineosis.compounds.v1`. A synthesis lays a compound over the poem's lines with a shot for each sign. Screen it, send it to the Studio as a branch, add it to the CHEM film the Bets can take from, or export an EDL. **Write-up** (`W`) prints all 28.
- **Chemistry trials** (`lab/chemistry-trials.html`, `lab/chemistry/trials.py`, `TRIALS.md`) — Narrative Chemistry v1 (frozen in `ONTOLOGY-v1.md`) put to the test.
  - **Method:** one instrument reads every film. Seven films per poem are synthesised blind to the four WYGWYL cuts and measured against them, with random and ordinary-taxonomy baselines and pre-registered predictions. Those four are machine cuts made by `cutbastard/plan.py`, so the verdicts describe its strategies, not human editing.
  - **Refuted:** the bond preferences. Chemistry films sit farther from the plan.py cuts than random ones, and those cuts avoid v1's rhyme.
  - **Holds:** isomers. The same atoms in a different order make a different film.
  - **Found:** the strongest signal in the plan.py cuts is the same sign held across a cut, which v1 has no bond for. It is plan.py's habit: in the archive films' own order it is at chance.
  - **The screening room:** a blind room where people rate eight films per poem, one of them the plan.py suite cut.
- **Syzygy · the spine's vertebrae** (`lab/syzygy/build_vertebrae.py`, `vertebrae.json`, `VERTEBRAE.md`) — every one of the 605 spine elements placed on her clock (422 by her own words; the rest by their timestamps on another master, interpolated between matched neighbours, ≈0.5 s leave-one-out error), plus 77 storyboard boards between lines. Each vertebra carries her words and line recording, the beat and its asked signs, the prompt and syntagma it was generated under, every image variant with its sign reading and nearest archive shots, the four `plan.py` cuts' shots with Metz's reading, the Spine-Cut picks, the beat's pool, the forage cut's shot and the genome patch, and where those layers agree.
- **Matrix-Editor storymap** (`lab/matrix/Storymap.md`, `build_storymap.py`) — WYGWYL as Diegesis → Acts → Save the Cat beats → Syntagmas → Shots, read from the lab's assets: each shot is a storyboard prompt (`spine/storyboard.json`) with its generated image, aligned to the suite's beats on her clock (`align.py`), with her words, the archive shots each `plan.py` cut put there, and Metz's reading of that beat (`metz_read.js`, the Grand Syntagmatique's classifier). Intended syntagmas are realised in 9% of shot-by-cut pairs: cuts that mix films read as bracket almost everywhere. The acts and beats are laid over the clock by proportion. `--shotlist` writes `Shotlist.js` (CinePrompt-form prompts) and `--chart` the Chart.d3 tree.
- **The flip test** (`lab/syntagm/swap_test.py`, `lab/syntagm/SWAP.md`) — does the order a sequence was cut in beat the same two shots swapped? Visual continuity, signs held, forward-in-source, and (once the words are embedded with `embed_words.py`) the words under each shot and the cut's direction against her words. The first step toward next-shot prediction with a value function. It recovers how each of the four WYGWYL cuts was built (they are `plan.py`'s, not a person's). On the archive films' own order people keep visual continuity only a little (0.56), and the machine sign does not predict their order at all.
- **One clock** (`lab/clock.js`) — the Studio, ABC FLIX · Whole Film and the Bets share her clock. Open another tool while the film plays and it carries on at the same moment (muted until a tap, if the browser insists). With several open side by side, the one you play leads and the rest follow it in silence.
- **ABC FLIX · Whole Film** (`lab/abc-flix/film.html`) — ABC FLIX rebuilt on the kernel clock: the whole film as a tunnel under her voice, a POSSIBLE → PREFERRED decision ladder (pool, machine draft, audition, film), a BEFLIX lens ripping ±6 s around the playhead, and the film out as `cineosis-edl/1` and `cineosis.film.FLIX.v1`.
- **The cineosis reel** — `cineosis-reel.mp4` (10 min) in [Releases](https://github.com/hartswf0/cineosis-lab/releases/tag/v0.1): every sign as a title card with its deciding test, then its strongest shots.

Static site limits: only the 253 read shots ship as local clips; every other shot plays from the archive's CDN. Chrome and Firefox stream the WYGWYL films from the release; if Safari refuses, the page offers the file to download.

## Syntagm Lab

Open [Syntagm Lab](https://hartswf0.github.io/cineosis-lab/lab/syntagm.html) to screen and rearrange passages from the four WYGWYL cuts or 60 cached source-film manifests. Keep playback above the timeline, inspect source coverage and neighboring clips, and compare edits while preserving occurrence identities and trims. The 45-sign table remains available with its deciding tests and read examples.

Metz's eight categories are proposed from explicit judgements about autonomy, chronology, coexistence, progression and ellipsis. Intended construction, recorded interpretation, rival reading and evidence stay separate. Rearranging a reviewed passage marks it for review. Save locally, round-trip passage JSON, or export the existing `cineosis-edl/1` format for the Studio. Source sound can be auditioned; this bench does not mix the poem soundtrack. [Method, data model and verification](lab/syntagm/README.md).

## Run it locally

```bash
git clone https://github.com/hartswf0/cineosis-lab && cd cineosis-lab
python3 lab/server.py 8765          # then open http://localhost:8765/
```

The local server adds what the static site can't: the two editors (**CUT** and **WAG**, the Cutting Room, each with the periodic table as its clip bin, `lab/tools/`), **live search** of movingimagearchive.com's shot index (the archive sends no CORS headers, so it is proxied and rate-limited) and **saving sub-shots** to `lab/assignments.json`. On GitHub Pages the lab runs in static mode: corpus search only, sub-shots kept in your browser with an export button.

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
| WYGWYL patches | `lab/cutbastard/timeline.py` | The suite clock cut into 169 patches of 6–12 s on cue edges, internal cuts snapped to score onsets. |
| WYGWYL forage | `lab/cutbastard/forage.py`, `queries.json` | 417 archive queries from the suite's lines and beats, then whole source films expanded. |
| WYGWYL watching | `lab/cutbastard/watch.py` | Per clip: motion, camera travel, dead frames, title-card probability, CLIP fingerprint. |
| WYGWYL cuts | `lab/cutbastard/plan.py`, `render_cut.py`, `render_grid.py` | Four strategies choose one unrepeated shot per patch; frame-exact render to the suite audio; the 2×2 grid. |

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
