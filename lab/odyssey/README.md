# The Odyssey collection

Footage foraged from the Moving Image Archive (movingimagearchive.com) for the 152 scenes of the Odyssey film
(tractor-dce-gyo: `odyssey/kits/locations.json`, `odyssey/cineosis/score.json`, copied into `src/`).

## How it was gathered

1. **Searches** (`src/q_*.json`). Every scene has searches of four kinds:
   - **ground:** the place, nearly empty;
   - **action:** what happens in its beats, names replaced by what a camera sees;
   - **figures:** single subjects worth cutting out;
   - **sign:** its primary cinematic sign's operation.

   Each of the 68 locations and 36 kinds of motion the film still has to make has its own searches too.
2. **Forage** (`forage.py`). Every search runs against the archive's shot search, one at a time; every clip returned is kept
   with the searches that found it (`results/clips.json`).
3. **Reading** (`ingest.py`). Each clip's thumbnail is read with both CLIP models the lab uses: OpenAI ViT-B/32 for the pages,
   LAION for events and places.
4. **Collection** (`build_library.py` → `library.json` + `emb.bin`). New clips join the Cineosis archive as a collection any room
   can load with `SH.load({extra: ['odyssey']})`. Clips the main library already held stay there.
5. **Scenes** (`build_scenes.py` → `scenes.json`). For every beat, the grounds and actions that fit best, ranked by CLIP against
   the beat and the searches that found them, with a light pull toward timeless footage. For every figure the scene needs, the
   clips to cut it from. `report.json` lists the weakest scenes first.
6. **Figures** (`seg_jobs.py`, then `../seg_track.py --jobs=odyssey/cache/seg-jobs.json`, then `../markov/sam_build.py`).
   SAM 2.1 cuts the figures out and tracks them. They join the storyboard's cast.

## The room

`../markov-odyssey.html` (the storyboard, `markov-sam.html?od=<scene>`): choose a scene, each beat is a panel, its ground drawn
from that beat's own forage, figures to move by hand, voice or camera hands, the scene's sign and its operation beneath.
