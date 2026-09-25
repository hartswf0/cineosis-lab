# ABC FLIX · Cineosis

[ABC FLIX](https://github.com/hartswf0/abc-flix) (the ICARO-PRO pixel engine and the ARC-TUNNEL clip editor on one message bus) fed with the lab's own footage instead of a video file from your disk.

Open `lab/abc-flix/`. The **REEL** button on the bus strip opens the loader.

## What it rips

| source | what fills the four tracks |
|---|---|
| **Cineosis sign** | the sign's read shots, by the confidence of their reading: PREFERRED ≥ 70, PROBABLE 55–69, PLAUSIBLE 40–54, POSSIBLE < 40 |
| **WYGWYL beat** | PREFERRED the shot the beat's review chose and the suite cut's pick · PROBABLE reviewed candidates (graded F or P) · PLAUSIBLE the scenes, cineosis and drift cuts' picks · POSSIBLE unreviewed candidates and forage |
| **My Videotext film** | PREFERRED your couplings (read from this browser's storage, same origin as Videotext) · then what the beats under them had, one tier down |

Each shot becomes 6, 12 or 24 frames (½, 1 or 2 s at the engine's 12 fps), starting where its reading or its cut starts. The engine's own cap of 144 frames sets how many shots fit. *Weave the tracks* alternates PREFERRED → POSSIBLE so every track fills along the barrel; *strongest first* runs the tracks in order.

## Making it work: pixels need the same origin

The engine turns every frame into a 7-level BEFLIX grid by reading its pixels (`getImageData`). A browser only allows that for video from the page's own origin or from a host that sends CORS headers; anything else "taints" the canvas. So each shot is resolved in this order:

1. **LOCAL**: one of the 333 read shots that ship in `lab/clips/`. Always works, on GitHub Pages too.
2. **SERVER**: when `python3 lab/server.py` is running, `/media/<shot id>.mp4` serves a same-origin copy of any of the 15,149 shots (fetched once from the CDN into `lab/cache/remote/`). Every source works in full.
3. **CDN**: the archive's CDN, requested with `crossOrigin="anonymous"`. The loader probes it once with a two-byte ranged request. If the CDN sends no CORS headers, its shots are marked `CDN ✕` and left out of the reel instead of failing mid-rip.

Any shot that still cannot be read is skipped, and the loader lists it with the reason after the rip.

On the static site, the signs always work. The WYGWYL beats and the Videotext film depend on the CDN's CORS headers, and work in full under `lab/server.py`.

## What changed from abc-flix

- `index.html` is `harness.html` (which, unlike abc-flix's current `index.html`, routes `CLIP_ARRANGE` and `STRIP_REORDER`, so the tunnel's arrangement reaches the engine) plus the REEL loader and `REEL_STATUS` routing. The bus strip shows the current shot and its track.
- `icaro-pro-bus.html`: a `LOAD_REEL` message and `loadReel()`, which rips by seeking rather than by realtime playback so remote shots rip at their own pace. Each shot starts a clip (`clipBoundary`) and carries its title and tier. `FRAMES_SYNC` adds per-frame `meta` and a `reset` flag.
- `c-bus.html`: on `reset` the tunnel reseeds; a reel frame goes on its evidence track instead of `i % 4`, and its clip is named after the shot.
- `reels.json` comes from `build_reels.py` (`python3 lab/abc-flix/build_reels.py`), from `lab-data.json` and `wygwyl/collage-data.json`.

Everything else (BEFLIX drawing and scripting, the film leader, the five tunnel views, the tools) is abc-flix as it was. GIF export still loads gif.js from jsDelivr.
