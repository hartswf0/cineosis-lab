# Cineosis Lab · data contract

`lab-data.json` (built by `build_lab.py`, served by `server.py` at `/lab-data.json`). Paths are relative to `lab/`.

```
{
  "signs": [ {                      // 45 elements of the periodic table
    "n": "32", "symbol": "Dm", "name": "Demark",
    "col": 10, "row": 1,            // grid position: 16 columns × 3 rows (lectosign row 0, tall)
    "image": "Relation", "code": "333",
    "dom": "mental",                // perception | affect | action | reflection | mental | break | time | read (colour family)
    "gloss": "...", "difference": "the deciding test, one sentence",
    "ceiling": 10,                  // max % one shot can carry
    "confusions": ["31","11","40"], "question": "..."
  } ],
  "shots": [ {                      // ~4,788 shots: the whole searched corpus
    "id": "uuid", "title": "Film title", "year": 1948|null, "decade": 1940|null,
    "slug": "...", "page": "archive clip page URL",
    "video": "remote mp4 URL", "clip": "clips/<id>.mp4" | null,   // local copy exists for the 253 read shots
    "thumb": "thumbs/<id>.jpg",     // local (falls back to remote URL until downloaded)
    "start": 12.3, "end": 18.9, "match": 14.1,   // seconds in the source film; the clip mp4 itself starts at 0 = start
    "read_t": 2.25 | null,          // seconds INTO THE CLIP of the frame the editor read (= archive thumbnail). Default position for
                                    // stills/inspector/reel on read shots; label it R. Differs from match by >2 s in half the clips.
    "bw": true,
    "palette": ["#aabbcc", ...5] | null,        // dominant colours, largest first
    "hue": 0-360 | null (null = near-greyscale), "lum": 0-1, "sat": 0-1,
    "subjects": [ {"label":"face close-up","p":0.62}, ... ] | null,   // CLIP zero-shot, top 3
    "scale": "extreme close-up|close-up|medium shot|long shot|extreme long shot" | null,
    "xy": [x, y] | null,            // 2-D similarity map (CLIP embedding, t-SNE), each in 0..1
    "sim": int | null,              // 1-D similarity order (neighbours are visually alike)
    "signs": [ {                    // editor's readings: only on the 253 chosen shots (a shot may serve 2 signs)
      "n": "32", "note": "one-line reading", "conf": 60, "shot": 10,
      "alt": "31", "alt_conf": 15, "flip": "condition that would make it the alt sign"
    } ],
    "found": [ {"n":"32","q":"search query","rank":0} ],   // which sign's search surfaced it
    "strip": "strips/<id>.jpg" | null, "frames": 8,         // horizontal sprite of N equally spaced frames
    "cutouts": [ {"png":"cutouts/<id>_0.png","label":"person","bbox":[x,y,w,h] (0..1 of frame),"area":0.12} ],
    "audio": {"has_audio":true,"rms_db":-28.1,"silence":0.12,"flatness":0.31,"kind":"sound|music|speech|silence|none"} | null
  } ],
  // NEW — every shot:
  //   "affinity": {"1": 2.4, ..., "44": 0.8}   machine sign-affinity %, sums to 100 over the 45 signs (CLIP vs each
  //                sign's criteria text + its read exemplars; leave-one-out). NOT a reading. Own sign in top-5 for 51% of read shots.
  //   "aff_top": [["32", 14.1], ...8]           top 8 of the above
  // NEW — read shots (filling in over ~3 h):
  //   "segments": {"fps": 6, "t0": 1.5, "frames": 29, "read_idx": 9, "objects": [ {
  //        "k": 0, "role": "reading" | "figure",   // reading = the thing the editor's note is about (directed by CLIP)
  //        "desc": "A crop-duster low over a field" (reading) | "man"/"clock"/"figure" (others),
  //        "label": "...", "src": "directed" | "detector" | "auto", "match": 0.31,   // CLIP match to the reading
  //        "png": "seg/<id>/0.png" (still cut-out at the read frame), "bbox": [x,y,w,h] (0..1, read frame),
  //        "sprite": "seg/<id>/0_track.png", "sw": 160, "sh": 120,   // horizontal RGBA sprite: `frames` cells of sw×sh,
  //                                                                  //   cropped to "union" box [x,y,w,h] (0..1)
  //        "boxes": [[x,y,w,h] | null, ...frames],   // per-frame box; frame f is at clip time t0 + f/fps
  //        "present": 0.97 } ] } | null
  // "cutouts" (older undirected single-frame SAM pass) stays for now; prefer "segments" when present.
  "assignments": [ {"id":"uuid","n":"32","note":"...","a":1.2,"b":3.4,"ts":"iso"} ]   // user's saves
}
```

## Server API (`server.py`, http://localhost:8765)
- `GET /…` static files from `lab/` (so `/lab-data.json`, `/thumbs/..`, `/clips/..`, `/cutouts/..`).
  Also `GET /table/…` serves the parent `CINEOSIS_44/` folder (e.g. `/table/periodic-table.html`).
- `POST /api/search {"query": "..."}` → `{"clips":[...]}`: proxied live to the archive's shot search (same clip
  fields as the archive: id, sourceTitle, sourceYear, sourceSlug, startSeconds, endSeconds, matchTimestampSeconds,
  videoUrl, thumbnailUrl, colorMode, score). Cached; rate-limited server-side. Can return 429 → show "wait".
- `POST /api/assign {"id","n","note","a","b"}` → appends to `assignments.json`, returns the saved row.
  `a`/`b` are in/out points in seconds relative to the clip (optional).
- `GET /api/assignments` → list.
