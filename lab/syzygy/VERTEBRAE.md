# Syzygy · the spine's vertebrae

Every generated spine element placed on her clock, with every other asset of the lab aligned to it. Built by `lab/syzygy/build_vertebrae.py`; the data is `vertebrae.json`.

## Placement

| how | vertebrae | meaning |
|---|---|---|
| words | 422 | the element's line matched to her word timings (Spine-Cut) |
| ts | 81 | not matched (or, for 7, matched to the wrong repeat of a word and out of order); its timestamp on the other master interpolated between its poem's matched elements (leave-one-out error ≈ 0.5 s) |
| span | 102 | its poem has too few matched elements (NM, HT); timestamps scaled onto the poem's voice |
| board | 77 | storyboard shot filling time between lines |

All 605 spine ids are placed (422 by her words). The other master ran the poems in another order (SH, FL, HT, NM, BE, AT, DJ, NS, YH, MR, RU, HM); within each poem its timestamps keep the suite's order.

## What each vertebra carries

| layer | spine vertebrae with it | source |
|---|---|---|
| clock · her words inside it | 588 of 605 | `bets/kernel-data.json` |
| sound · her line's recording, pauses, pitch, hooks | 593 of 605 | `sound-cineosis.json` |
| intended · syntagma, function, prompt | 536 of 605 | `spine/total-cinome.json` |
| image · generated images, sign reading, nearest archive shots | 605 of 605 | `spine/spine-data.json` |
| cuts · the four plan.py cuts' shots and Metz's reading | 605 of 605 | `syntagma-data + metz.js` |
| spinecut · Spine-Cut picks and review note | 429 of 605 | `spinecut/spinecut-data.json` |
| pool · the beat's candidates | 605 of 605 | `wygwyl/candidate-ranks.json` |
| forage · forage cut shot and edit note | 605 of 605 | `wygwyl/WYGWYL_Forage_Cut.json` |
| patch · suite genome patch | 605 of 605 | `wygwyl/cuts/suite/patches.json` |
| beat · suite beat, asked signs, Save the Cat, storyboard | 605 of 605 | `syntagma-data.json`, `matrix/align.py` |

## Where the layers agree

- **The image reads as a sign its beat asks for** (one of its top three): 121 of 605.
- **suite's archive shot carries an asked sign:** 62 of 605.
- **scenes's archive shot carries an asked sign:** 35 of 605.
- **cineosis's archive shot carries an asked sign:** 297 of 605.
- **drift's archive shot carries an asked sign:** 61 of 605.
- **Metz's reading of the beat realises the intended syntagma** (only for Metz-family labels, 283 vertebrae): suite 3, scenes 46, cineosis 3, drift 3.

## Per poem

| poem | spine | words | ts | span | boards |
|---|---|---|---|---|---|
| 01 · OUT OF LIFE | 24 | 21 | 3 | 0 | 14 |
| 02 · FLASHING LIGHTS | 47 | 42 | 5 | 0 | 6 |
| 03 · HOW TO BREAK OFF AN ENGAGEMENT | 33 | 31 | 2 | 0 | 2 |
| 04 · NEVERMORE | 69 | 0 | 0 | 69 | 8 |
| 05 · BLOODLINES | 0 | 0 | 0 | 0 | 4 |
| 06 · RESURRECTING ATLANTIS | 43 | 41 | 2 | 0 | 7 |
| 07 · DJ TURN ME UP | 69 | 43 | 26 | 0 | 6 |
| 08 · NEWLY SINGLE | 64 | 50 | 14 | 0 | 5 |
| 09 · YET, HEARD | 68 | 59 | 9 | 0 | 3 |
| 10 · MAGIC RIDE | 68 | 61 | 7 | 0 | 3 |
| 11 · NEW DAY | 0 | 0 | 0 | 0 | 5 |
| 12 · REUNION | 35 | 33 | 2 | 0 | 2 |
| 13 · HOW TO WIN MY HEART | 35 | 2 | 0 | 33 | 9 |
| 14 · HOT MINUTE | 50 | 39 | 11 | 0 | 3 |

Bloodlines (05) and New Day (11) have no spine elements; their time is held by storyboard boards only.

## Record fixes this alignment settles

- **BE** records set the words of *How to Break Off an Engagement* (03); **HT** records are *How To Win My Heart* (13). The `poem` field is right; the code comment in `extract_poem_content.py` (BE = Bloodline) is not.
- **NM** (Nevermore, 04) has no line text; its 69 elements are placed by timestamp over the poem's voice (`span`).
- The 210 repeated ids are image variants; each vertebra lists all of them under `image`.

## One vertebra, whole

```json
{
 "v": 5,
 "kind": "spine",
 "id": "SH001",
 "t0": 29.812,
 "t1": 30.872,
 "placed": "words",
 "film": "01",
 "poem": "OUT OF LIFE",
 "clock": {
  "line": "01_L01",
  "words": "What we've made"
 },
 "sound": {
  "line": "01_L01",
  "reading": "https://hartswf0.github.io/butterfly-halfworld/wygwyl/samples/01/L01.mp3",
  "sung": "https://hartswf0.github.io/butterfly-halfworld/wygwyl/codex/01/line_00.mp3",
  "events": [
   "PITCH_HIGH"
  ],
  "chops": [
   "we've made",
   "we've sold"
  ]
 },
 "beat": {
  "n": 4,
  "title": "Vapour erases the room",
  "asks": [
   "6",
   "34a"
  ],
  "stc": "Set-Up",
  "board": []
 },
 "intended": {
  "content": "What we’ve made—",
  "syntagmaType": "Descriptive Syntagma (DS)",
  "cineosisFunction": "Mood Environment Stabilizer",
  "imageType": "Descriptive Image",
  "operativeEkphrasis": "A symbolic tableau rendered through chiaroscuro lighting."
 },
 "image": [
  {
   "thumb": "spine/thumbs/SH001-6ca4cd0.webp",
   "aff": [
    [
     "18",
     8.4
    ],
    [
     "6",
     7.0
    ],
    [
     "26",
     5.1
    ]
   ],
   "fit": 0.222,
   "near": [
    {
     "id": "a278e38c-f45c-5168-8172-7f7413aa90d6",
     "title": "New World Through Chemistry",
     "year": null,
     "thumb": "thumbs/a278e38c-f45c-5168-8172-7f7413aa90d6.jpg",
     "sg": "18",
     "sim": 0.587
    },
    {
     "id": "b762c586-1d5f-5ef2-b8e4-c0dcc8f82449",
     "title": "Television Tomorrow",
     "year": null,
     "thumb": "thumbs/b762c586-1d5f-5ef2-b8e4-c0dcc8f82449.jpg",
     "sg": "18",
     "sim": 0.587
    },
    {
     "id": "e2143a49-bd1d-5f9e-b466-89f89daf3a32",
     "title": "Eagle Has Landed: The Flight of Apollo 11",
     "year": 1969,
     "thumb": "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/eagle-has-landed-the-flight-of-apollo-11/thumbnails/0000001969-0000059660.jpg",
     "sg": "18",
     "sim": 0.581
    }
   ]
  },
  {
   "thumb": "spine/thumbs/SH001-6ca4cd3.webp",
   "aff": [
    [
     "6",
     13.0
    ],
    [
     "43",
     6.3
    ],
    [
     "27",
     4.8
    ]
   ],
   "fit": 0.251,
   "near": [
    {
     "id": "109a12e4-5454-5cb8-a656-15b2817bcec1",
     "title": "Moonwalk One, ca. 1970",
     "year": 1970,
     "thumb": "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/moonwalk-one-ca-1970/thumbnails/0000234034-0000237771.jpg",
     "sg": "27",
     "sim": 0.614
    },
    {
     "id": "e389199f-ead5-551d-80c8-bd07f81b9aae",
     "title": "Apollo 12: Pinpoint for Science",
     "year": 1969,
     "thumb": "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/apollo-12-pinpoint-for-science/thumbnails/0000854354-0000856489.jpg",
     "sg": "6",
     "sim": 0.589
    },
    {
     "id": "55e95d57-21a5-5575-8826-755c1b8a350b",
     "title": "Moonwalk One, ca. 1970",
     "year": 1970,
     "thumb": "https://pub-075ff01374c04555b51c9bc50f258b42.r2.dev/sources/moonwalk-one-ca-1970/thumbnails/0000224925-0000228295.jpg",
     "sg": "44",
     "sim": 0.565
    }
   ]
  }
 ],
 "cuts": {
  "suite": {
   "shot": {
    "id": "37dfa009-821f-511c-861f-3f57e307d220",
    "title": "Moonwalk One, ca. 1970",
    "year": 1970,
    "sg": "24"
   },
   "metz": "BR",
   "why": "shots from 2 films, no time between them: a category"
  },
  "scenes": {
   "shot": {
    "id": "057d4cfe-2264-527b-9c55-daa67044dfd5",
    "title": "JFK EXHIBIT 3: RECONSTRUCTION FILM",
    "year": 1943,
    "sg": "39"
   },
   "metz": "BR",
   "why": "shots from 2 films, no time between them: a category"
  },
  "cineosis": {
   "shot": {
    "id": "9f8a240d-f97f-561a-8974-9719d07a3754",
    "title": "Robinson Crusoe C",
    "year": 1927,
    "sg": "34a"
   },
   "metz": "BR",
   "why": "shots from 2 films, no time between them: a category"
  },
  "drift": {
   "shot": {
    "id": "d163e8cc-dd42-56be-b31a-c33ab72901d9",
    "title": "Apollo 12: Pinpoint for Science",
    "year": 1969,
    "sg": "36"
   },
   "metz": "BR",
   "why": "shots from 2 films, no time between them: a category"
  }
 },

```