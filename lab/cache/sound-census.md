# SOUND CENSUS

Clips measured: 2013 (`lab/clips/*.mp4`). Script: `lab/sound_census.py`; per-clip caches `lab/cache/sound/<id>.json`; merged `lab/cache/sound-census.json`.

## Counts

| kind | clips |
|---|---|
| none | 178 |
| silence | 396 |
| speech | 557 |
| music | 180 |
| mixed | 611 |
| noise | 91 |

Clips with music >= 0.4 (tempo/key/beats attached): 736. Clips with speech >= 0.4 (speech spans attached): 1123.

## Method

ffmpeg mono 22050 Hz. Loudness: ITU-R BS.1770-4 K-weighting (shelf+HPF biquads re-derived for 22.05 kHz, scipy sosfilt), 400 ms blocks/75% overlap, -70 LUFS abs + -10 LU rel gates; mono downmix, so correlated stereo reads ~3 LU below a stereo meter. LRA = p95-p10 of 3 s short-term loudness (abs -70, rel -20 gates). Silence = fraction of 93 ms frames (23 ms hop) under -50 dBFS. Classifier (signal features, no models): per second over a 3 s window; a gate (harmonic-chroma peakiness, 60-5000 Hz spectral flatness, voice-band share) sends hiss/rain/wind/engine/hum/rumble to noise; then two independent logistic scores, sign-constrained and fitted on a synthetic listen-free calibration set: speech (+envelope depth, +ZCR variation, -pitch steadiness, -HPSS harmonic ratio, -beat strength, -chroma stability, -harmonicity of the inter-syllable floor) and music (+YIN pitch steadiness, +harmonic ratio, +beat strength, +harmonicity/tonality of the inter-syllable floor, -depth, -ZCR variation, -4 Hz syllabic modulation). Both high = mixed, neither = noise. Clip kind from the per-second timeline (mixed when >= 25 % of sounding seconds carry each). Key: Krumhansl-Schmuckler on energy-weighted harmonic chroma. Tempo/beats: librosa beat_track; beat_conf = normalised onset autocorrelation peak 45-220 bpm. Speech spans: 10 Hz voice-band (300-3400 Hz) level > clip floor + 6 dB inside speech/mixed seconds, gaps < 0.5 s closed.

## Validation

Compared with the existing `audio.kind` labels on 253 read shots in `lab-data.json`. Those labels are themselves a cruder heuristic (clipwork.py: 16 kHz, flatness + 3-7 Hz modulation, no mixed class), not human ground truth, so agreement measures consistency, not accuracy.

- strict agreement (noise=sound; mixed counted wrong): 120/253 = 47.4%
- lenient (mixed accepted for speech or music): 163/253 = 64.4%
- coarse 'carries voice or music' yes/no: 175/253 = 69.2%

Confusion (rows old label, columns census kind):

| old \ census | speech | music | mixed | noise | silence | none |
|---|---|---|---|---|---|---|
| speech | 46 | 6 | 39 | 4 | 0 | 0 |
| music | 6 | 4 | 4 | 1 | 0 | 0 |
| sound | 42 | 4 | 27 | 5 | 0 | 0 |
| silence | 0 | 0 | 0 | 0 | 47 | 0 |
| none | 0 | 0 | 0 | 0 | 0 | 18 |

### Listen-free calibration (ground truth by construction)

| set | what | clips | census kinds |
|---|---|---|---|
| held out | clean TTS narration (8 voices x 3 texts) | 24 | speech 24 |
| held out | TTS narration over pre-1927 archive music beds, bed -4..-8 dB | 24 | mixed 16, speech 5, music 3 |
| held out | noise: hiss, pink, rumble, 60 Hz hum, crackle, rain, wind, engine, crowd babble | 9 | noise 8, mixed 1 (babble) |
| fitted | degraded narration (reverb, 150-4k Hz, hiss 12-20 dB SNR, hum) | 24 | speech 18, mixed 6 |
| fitted | narration + noise at 10 dB SNR | 24 | speech 21, noise 2, mixed 1 |
| fitted | degraded narration over beds / synthetic score, -5..-11 dB | 24 | mixed 24 |
| fitted | synthetic score alone (chords, melody, +/- drums) | 8 | music 8 |
| fitted | pre-1927 archive music beds (+/- added noise) | 12 | music 8, mixed 4 |
| fitted | sung TTS (Cellos, Good News, Bells) | 3 | mixed 3 |

Per second on the held-out narration-over-bed set: 'carries speech' right 72 %, 'carries music' right 65 % (music under loud narration is the weak spot). Held-out clean narration: 100 % of seconds speech. Degraded narration alone: ~20 % of seconds wrongly also flagged music (mixed).

### Consistency checks on the archive

- Within one source film (sources with >= 3 sounding clips, n=146), clips agree on 'carries speech' 88.5% of the time (films rarely switch between narrated and un-narrated).
- Title anchors: `Master Hands` (1936, symphonic score, no narration): music 27, mixed 1; `Communications Primer` (1953 Eames film, narrated): speech 6, mixed 2; `River, The` (1937, Thomson score under Lorentz narration): mixed 3, music 2

### How good is it, honestly

- none / silence are exact (stream probe; -50 dBFS frames). The loudness numbers are measurements, not guesses (K-filter checked: 1 kHz sine at -20 dBFS peak reads -23.28 LUFS vs -23.01 reference, 0.27 dB of 22.05 kHz bilinear warping; a 20 dB step reads LRA 20.0).
- speech vs not-speech is the reliable split (clean narration 100 %, degraded 75-88 % speech-only, rest tagged mixed, which still carries speech). Use `p.speech` and `speech_spans` to duck.
- music under narration is the weak spot: roughly a third of such seconds are missed and ~20 % of bare narration seconds are over-flagged as mixed. Treat `mixed` as 'speech, probably with a bed', and trust `music` (music without speech) more than `mixed` for music.
- the old lab-data labels are a cruder heuristic (no mixed class; 'sound' mostly = noisy narration by our reading), so the low strict agreement is mainly definitional; the coarse carries-voice-or-music agreement is the fairer number.
- tempo comes from librosa beat_track and is quantised by the 23 ms hop (values like 123.0/136.0/143.6 recur); only trust it when `beat_conf` > ~0.35 (median across music clips is ~0.16: most archive scores are rubato orchestral). Key confidence (`key_conf` = margin between best and 2nd-best Krumhansl correlation) is usually < 0.1, i.e. weak.

## WYGWYL cut patches carrying music or speech

### cineosis — 169 patches: mixed 54, speech 44, silence 29, none 23, music 15, noise 4

| patch | clip | title | kind | p speech | p music |
|---|---|---|---|---|---|
| P000 | `577428e2` | Sleep for Health | mixed | 0.677 | 0.687 |
| P001 | `136239c1` | All My Babies | speech | 0.779 | 0.185 |
| P002 | `d5fd2249` | THE PHOTOGRAPHER | speech | 0.867 | 0.093 |
| P004 | `518c4990` | Broadway Limited | speech | 0.529 | 0.159 |
| P005 | `33491c0b` | Looking Ahead Through Plexiglas A | speech | 0.88 | 0.148 |
| P006 | `642c98e9` | Master Hands | music | 0.261 | 0.904 |
| P010 | `348178ba` | All My Babies | mixed | 0.816 | 0.565 |
| P011 | `28f527d2` | Back-Room Boy | speech | 0.688 | 0.034 |
| P012 | `7c142971` | Years of Grandeur: Alexander Hamilton U.S. Custom House, New York, NY | speech | 0.943 | 0.145 |
| P013 | `a2f22d30` | Laboratory Design for Microbiological Safety | speech | 0.82 | 0.12 |
| P014 | `a95bb4f0` | Cataloochee - The Center of the World | mixed | 0.836 | 0.397 |
| P015 | `19112ce1` | Knights on the Highway | speech | 0.86 | 0.074 |
| P016 | `12c2bfef` | Moonwalk One, ca. 1970 | mixed | 0.594 | 0.41 |
| P017 | `23e1327d` | ABCs of Walking Wisely | mixed | 0.75 | 0.603 |
| P018 | `4bb3d3a6` | Scrooge | music | 0.376 | 0.847 |
| P019 | `5d528b30` | All My Babies | mixed | 0.567 | 0.65 |
| P023 | `ff41c369` | Fastax-tion | mixed | 0.397 | 0.923 |
| P024 | `d7a7f1dd` | Sound Waves And Their Sources | mixed | 0.545 | 0.696 |
| P026 | `9926d773` | SPACE AGE RAILROAD | speech | 0.841 | 0.081 |
| P027 | `10c897d3` | Great American Chocolate Factory, The | mixed | 0.687 | 0.517 |
| P030 | `6620e523` | Visions of the wild | mixed | 0.826 | 0.433 |
| P031 | `05ad473c` | Road Runners | mixed | 0.746 | 0.546 |
| P034 | `d9220162` | Alaska's Silver Millions (Part I) | mixed | 0.753 | 0.498 |
| P035 | `2aa46bbe` | Celebrating Chincoteague National Wildlife Refuge | speech | 0.926 | 0.261 |
| P036 | `ad0235a8` | Garden Wise (Pt 2) | mixed | 0.455 | 0.744 |
| P037 | `7408c21e` | Mobile Lab : Any Questions? | speech | 0.897 | 0.095 |
| P038 | `cbce572a` | Victory Gardens | speech | 0.675 | 0.12 |
| P039 | `27417db1` | Frontiers of the Future (A Screen Editorial With Lowell Thomas) | speech | 0.918 | 0.234 |
| P040 | `d2912920` | Promise of Pakistan Geography | mixed | 0.621 | 0.618 |
| P041 | `60828987` | Garden Wise (Pt 1) | mixed | 0.554 | 0.757 |
| P042 | `ef1ae8f5` | Alcohol and the Human Body | speech | 0.612 | 0.092 |
| P044 | `cee71cbd` | Moonwalk One, ca. 1970 | speech | 0.973 | 0.142 |
| P045 | `db6f4815` | All My Babies | speech | 0.662 | 0.012 |
| P046 | `058430e4` | Have I Told You Lately That I Love You? | speech | 0.588 | 0.174 |
| P047 | `af3580ab` | THE PHOTOGRAPHER | mixed | 0.706 | 0.368 |
| P050 | `79e72447` | Space Ship Takeoff, a Technical Fantasy | mixed | 0.499 | 0.482 |
| P052 | `70c8ca82` | Modesta | speech | 0.918 | 0.152 |
| P053 | `6c23e59a` | Precisely So (Part I) | speech | 0.747 | 0.075 |
| P054 | `8f57e985` | Moonwalk One, ca. 1970 | speech | 0.931 | 0.351 |
| P055 | `2591153a` | Eat for Health | mixed | 0.677 | 0.582 |
| P057 | `d558d30e` | Valley Town | mixed | 0.327 | 0.871 |
| P058 | `f1b37876` | Master Hands | music | 0.155 | 0.962 |
| P059 | `cb6b8c2f` | Watershed wildfire | mixed | 0.65 | 0.668 |
| P061 | `1b015573` | Moonwalk One, ca. 1970 | music | 0.38 | 0.597 |
| P064 | `c97f952a` | Straight Talk | speech | 0.951 | 0.057 |
| P065 | `c730b43e` | Moonwalk One, ca. 1970 | mixed | 0.468 | 0.801 |
| P066 | `012bbc5b` | Taiwan | mixed | 0.76 | 0.591 |
| P067 | `c3a35945` | Destruction: Fun or Dumb? | speech | 0.71 | 0.282 |
| P068 | `2319744b` | ABCs of Walking Wisely | mixed | 0.783 | 0.491 |
| P069 | `25603a60` | Spot News | speech | 0.925 | 0.155 |
| P070 | `47b158ae` | SPACE AGE RAILROAD | mixed | 0.561 | 0.741 |
| P072 | `24d31621` | Friendship Seven | mixed | 0.606 | 0.683 |
| P075 | `6b143fd4` | All My Babies | speech | 0.559 | 0.143 |
| P077 | `b66fef61` | Under Western Stars | speech | 0.797 | 0.189 |
| P079 | `97cda27d` | Henry Ford's Mirror of America (Part II) | mixed | 0.67 | 0.309 |
| P082 | `814e3e9c` | Duck and Cover | speech | 0.893 | 0.074 |
| P083 | `34b9469d` | Master Hands | music | 0.131 | 0.955 |
| P084 | `414b9985` | Mental Hospital | mixed | 0.501 | 0.805 |
| P085 | `b7da880c` | Care of the Hair and Nails | mixed | 0.738 | 0.734 |
| P086 | `8721827b` | Under Western Stars | mixed | 0.61 | 0.423 |
| P087 | `c0c9a9ee` | Moonwalk One, ca. 1970 | speech | 0.855 | 0.017 |
| P088 | `2c2401f2` | Beginning to Date | music | 0.15 | 0.96 |
| P089 | `06e023b6` | Frigidaire Finale 1957 | music | 0.181 | 0.967 |
| P090 | `449c850d` | Small Steps...Giant Strides | speech | 0.755 | 0.009 |
| P091 | `d18e8ea5` | Moonwalk One, ca. 1970 | speech | 0.895 | 0.045 |
| P093 | `e5dfacfb` | SPACE AGE RAILROAD | music | 0.333 | 0.888 |
| P094 | `e890e360` | Naturally - a Girl | mixed | 0.719 | 0.719 |
| P095 | `8323b4ae` | Moonwalk One, ca. 1970 | speech | 0.936 | 0.22 |
| P096 | `aa431677` | Fate of the forests, ca. 1980 - ca. 1985 | mixed | 0.572 | 0.54 |
| P098 | `7b65d798` | Friendship Seven | music | 0.134 | 0.978 |
| P099 | `4937833a` | The Eagle Has Landed: The Flight of Apollo 11 | speech | 0.868 | 0.219 |
| P100 | `1d5f1026` | Moonwalk One, ca. 1970 | mixed | 0.473 | 0.413 |
| P101 | `89edb74e` | 'Till It Helps! | mixed | 0.698 | 0.727 |
| P102 | `36f08d09` | Garden Wise (Pt 1) | mixed | 0.607 | 0.819 |
| P103 | `11a12585` | Big Train, The (Part I) | mixed | 0.827 | 0.375 |
| P104 | `c9512664` | Sound And The Story | music | 0.365 | 0.832 |
| P105 | `242ff926` | Moonwalk One, ca. 1970 | mixed | 0.635 | 0.765 |
| P106 | `83170c1a` | WJR: One of a Kind | speech | 0.888 | 0.067 |
| P107 | `82d6404d` | Court to Court (October 2004) | speech | 0.985 | 0.007 |
| P108 | `8cb448cc` | Big Train, The (Part II) | speech | 0.852 | 0.079 |
| P109 | `b381a75b` | No Time for Ugliness (Part I) | music | 0.161 | 0.978 |
| P110 | `43149768` | Visibility and Communications: Off-Road and Highway Trucks | speech | 0.947 | 0.125 |
| P113 | `35fde33f` | Let's Go To The Movies | mixed | 0.462 | 0.778 |
| P116 | `66b520a3` | Moonwalk One, ca. 1970 | music | 0.323 | 0.78 |
| P117 | `2aaf5cbd` | SPACE AGE RAILROAD | mixed | 0.622 | 0.445 |
| P118 | `e29c80c9` | Dusk to Dawn | mixed | 0.493 | 0.408 |
| P119 | `b25fa309` | Uncle Walt | speech | 0.776 | 0.248 |
| P120 | `1b347163` | EMAP: America's Ecological Report Card | speech | 0.918 | 0.077 |
| P121 | `0895ffd5` | Big Train, The (Part II) | music | 0.135 | 0.98 |
| P123 | `3f9d9185` | Moonwalk One, ca. 1970 | speech | 0.883 | 0.117 |
| P124 | `49e405d4` | Show 'Em the Road (Part II) | mixed | 0.403 | 0.863 |
| P125 | `54edee0e` | Of Ice and Fire: The Mono Basin | mixed | 0.763 | 0.312 |
| P130 | `aee7ac70` | No Time for Ugliness (Part I) | music | 0.281 | 0.88 |
| P133 | `413af513` | Schedadxw: (pronounced cha-da-duch) | speech | 0.868 | 0.055 |
| P135 | `6e43c240` | All My Babies | mixed | 0.374 | 0.862 |
| P137 | `e0947362` | Onbekende film legerparade | mixed | 0.381 | 0.739 |
| P142 | `f762768d` | Facts About Film | speech | 0.614 | 0.023 |
| P144 | `0a7d7714` | Consumers Want to Know (Part I) | mixed | 0.803 | 0.425 |
| P146 | `6610500c` | Wonderful World (Part III) | mixed | 0.468 | 0.9 |
| P148 | `963cb372` | Gateways to the Mind | mixed | 0.675 | 0.725 |
| P149 | `344ecde2` | Moonwalk One, ca. 1970 | mixed | 0.742 | 0.617 |
| P151 | `ad62f7db` | Parks as Classrooms | speech | 0.971 | 0.034 |
| P153 | `02cb6d19` | Your Town: A Story of America | mixed | 0.641 | 0.817 |
| P154 | `c2ff8b13` | All My Babies | speech | 0.664 | 0.055 |
| P156 | `5262fef3` | Garden Wise (Pt 2) | mixed | 0.635 | 0.733 |
| P157 | `5557791a` | Dial Comes To Town | speech | 0.725 | 0.238 |
| P161 | `de2133ee` | Duck and Cover | speech | 0.825 | 0.029 |
| P162 | `c7ae0e60` | Master Hands | music | 0.148 | 0.942 |
| P163 | `640e4e63` | Plastics | mixed | 0.689 | 0.696 |
| P165 | `78eebdee` | All-American Soap Box Derby, The (1936) | mixed | 0.73 | 0.546 |
| P166 | `f520f81c` | Brooklyn Goes to San Francisco | mixed | 0.628 | 0.641 |
| P167 | `3ca01566` | Back-Room Boy | mixed | 0.527 | 0.355 |
| P168 | `8b20a7e8` | Under Western Stars | mixed | 0.588 | 0.692 |

### drift — 169 patches: mixed 59, speech 44, silence 29, music 25, none 8, noise 4

| patch | clip | title | kind | p speech | p music |
|---|---|---|---|---|---|
| P000 | `a2cd3366` | Light Of Your Life A | mixed | 0.803 | 0.532 |
| P002 | `ca1eac8e` | Moonwalk One, ca. 1970 | speech | 0.811 | 0.129 |
| P003 | `d163e8cc` | Apollo 12: Pinpoint for Science | music | 0.329 | 0.705 |
| P004 | `967b8b9f` | Ripley's Believe it or Not Museum - Gatlinburg, Tennessee | mixed | 0.776 | 0.523 |
| P005 | `9da97e0c` | Rochester: A City of Quality (Part I) | music | 0.216 | 0.602 |
| P006 | `e7b46e81` | Moonwalk One, ca. 1970 | speech | 0.882 | 0.165 |
| P008 | `7ee2fb8e` | Harvest Of The Years | speech | 0.832 | 0.287 |
| P009 | `3f8ac397` | Master Hands | music | 0.179 | 0.959 |
| P010 | `20b7360e` | ALASKAN EARTHQUAKE | speech | 0.807 | 0.258 |
| P011 | `c89d78b9` | Fashion's Favorite (Part I) | speech | 0.894 | 0.071 |
| P012 | `8b6bda0f` | Valley Town | mixed | 0.332 | 0.895 |
| P013 | `4bac9903` | River, The (Part I) | music | 0.044 | 0.974 |
| P017 | `38b5808e` | Plastics | mixed | 0.717 | 0.735 |
| P018 | `5d81b644` | Knights on the Highway | speech | 0.827 | 0.126 |
| P019 | `908c2493` | APOLLO 16MM ONBOARD SELECT VIEWS FROM HDTV TRANSFERS: APOLLO 202 TO 17 (LAUNCH / ONBOARDS) | music | 0.054 | 0.924 |
| P021 | `37d530cd` | Ripley's Believe it or Not Museum - Gatlinburg, Tennessee | mixed | 0.604 | 0.379 |
| P022 | `6801f722` | Apollo 12: Pinpoint for Science | mixed | 0.577 | 0.549 |
| P023 | `cc3622e5` | Communications Primer, A | speech | 0.817 | 0.045 |
| P025 | `b9bbcf68` | Spider Engineers | speech | 0.712 | 0.208 |
| P026 | `dc8b8137` | FIVE ARTISTS | music | 0.089 | 0.981 |
| P027 | `f448c7f5` | Place to Live, A | music | 0.361 | 0.782 |
| P030 | `d9731108` | South Chile | speech | 0.845 | 0.259 |
| P032 | `20d5b220` | American Frontier (Part I) | mixed | 0.442 | 0.854 |
| P033 | `0777051d` | Apollo 12: Pinpoint for Science | mixed | 0.796 | 0.361 |
| P034 | `4d04ae14` | A Very Special Place | mixed | 0.605 | 0.571 |
| P035 | `388c7045` | Vision of the Wild | mixed | 0.791 | 0.388 |
| P038 | `2be9689f` | Liberty | music | 0.342 | 0.652 |
| P039 | `608f2683` | Watershed wildfire | mixed | 0.733 | 0.52 |
| P040 | `c9fc936a` | Cabeza Prieta National Wildlife Refuge Desert Wilderness | speech | 0.964 | 0.031 |
| P041 | `8ac5a957` | House of the woods: A forest trilogy | music | 0.28 | 0.82 |
| P042 | `fbc3af1b` | Legacy for Wings | speech | 0.708 | 0.038 |
| P045 | `50b23b0d` | Garden Wise (Pt 1) | mixed | 0.362 | 0.857 |
| P046 | `4209b033` | Garden Wise (Pt 2) | mixed | 0.774 | 0.562 |
| P047 | `16443622` | House of the woods: A forest trilogy | music | 0.254 | 0.636 |
| P048 | `ce4e5ac7` | Who's Out There? | mixed | 0.732 | 0.613 |
| P049 | `64a508b1` | Moonwalk One, ca. 1970 | speech | 0.868 | 0.014 |
| P050 | `632b2d55` | Communications Primer, A | mixed | 0.494 | 0.925 |
| P051 | `0517d08a` | Assignment: Shoot the Moon | mixed | 0.562 | 0.626 |
| P052 | `e2a64c7a` | Apollo 12: Pinpoint for Science | music | 0.366 | 0.737 |
| P053 | `6f56e00a` | Anthracite: Pre-Shift Examinations of Underground Mines | speech | 0.535 | 0.057 |
| P055 | `8ac7c601` | A Very Special Place | mixed | 0.591 | 0.384 |
| P056 | `021ef298` | Parks as Classrooms | speech | 0.965 | 0.121 |
| P057 | `1f4f101b` | Moonwalk One, ca. 1970 | speech | 0.952 | 0.031 |
| P058 | `4db753a1` | Big Train, The (Part I) | music | 0.306 | 0.903 |
| P059 | `4cc9f977` | Walk In - Coming Soon - Theater Audience | mixed | 0.882 | 0.369 |
| P060 | `6eb767a2` | Apollo 12: Pinpoint for Science | mixed | 0.458 | 0.679 |
| P061 | `9278e205` | Airport America | mixed | 0.724 | 0.482 |
| P064 | `85d03481` | Middle America | mixed | 0.445 | 0.744 |
| P065 | `43ccbf61` | Coffee House Rendezvous (Part I) | mixed | 0.435 | 0.246 |
| P066 | `580e3e95` | Friendship Seven | mixed | 0.703 | 0.529 |
| P067 | `87060243` | Wheels of Progress | speech | 0.829 | 0.318 |
| P068 | `839b133d` | Dynamic American City, The (Part I) | speech | 0.891 | 0.194 |
| P070 | `63981edf` | Apollo 13 Splashdown and Recovery | speech | 0.527 | 0.254 |
| P073 | `64db067c` | SPACE AGE RAILROAD | speech | 0.881 | 0.102 |
| P074 | `80b5da26` | Moonwalk One, ca. 1970 | music | 0.119 | 0.901 |
| P075 | `fb79cba3` | Man of Action | mixed | 0.696 | 0.489 |
| P076 | `9e60212f` | American Road, The (Part III) | mixed | 0.644 | 0.77 |
| P077 | `b866e9f6` | Small Steps...Giant Strides | speech | 0.911 | 0.017 |
| P078 | `d9b8357a` | Moonwalk One, ca. 1970 | speech | 0.802 | 0.086 |
| P079 | `e3f8ebd3` | SPACE AGE RAILROAD | speech | 0.864 | 0.086 |
| P080 | `3e92f423` | This Is My Railroad (Part I) | speech | 0.651 | 0.019 |
| P081 | `d4e44ba7` | Big Train, The (Part II) | mixed | 0.687 | 0.64 |
| P082 | `1a2b4ab0` | Friendship Seven | mixed | 0.477 | 0.832 |
| P083 | `86196546` | Fantastic Yellowstone | mixed | 0.65 | 0.524 |
| P084 | `d726e7e2` | They Call It All-States | mixed | 0.646 | 0.529 |
| P086 | `57b68583` | This is Russia (Reel 1 of 2) | music | 0.25 | 0.757 |
| P087 | `e795ecac` | Moonwalk One, ca. 1970 | speech | 0.666 | 0.205 |
| P088 | `8ae00f9f` | Four in the Cosmos | mixed | 0.52 | 0.79 |
| P089 | `dc37b5a0` | Spider Engineers | speech | 0.687 | 0.238 |
| P090 | `bb70c999` | Apollo 12: Pinpoint for Science | speech | 0.669 | 0.22 |
| P091 | `6a1a6708` | White Wonder | mixed | 0.687 | 0.454 |
| P093 | `7a3ca423` | Who's Out There? | speech | 0.615 | 0.013 |
| P094 | `c83ba560` | Assignment: Shoot the Moon | mixed | 0.485 | 0.808 |
| P095 | `b1d05923` | Moonwalk One, ca. 1970 | music | 0.184 | 0.941 |
| P096 | `37253093` | RESEARCH PROJECT X-15 THE DEVELOPMENT OF THE X-15 | speech | 0.881 | 0.064 |
| P097 | `b5c58932` | Third Avenue El | music | 0.278 | 0.951 |
| P098 | `b5092eb5` | Your Fire Department (Part I) | music | 0.223 | 0.903 |
| P100 | `455b01fb` | Friendship Seven | speech | 0.779 | 0.264 |
| P101 | `93eb24c4` | Space Shuttle: A Remarkable Flying Machine | mixed | 0.805 | 0.576 |
| P102 | `b7ecccb6` | Space Flight: Application of Orbital Mechanics | speech | 0.9 | 0.05 |
| P103 | `1965dbb2` | Mirror of America | music | 0.077 | 0.53 |
| P105 | `e20e481a` | All My Babies | speech | 0.88 | 0.065 |
| P106 | `bd999966` | Eat for Health | music | 0.339 | 0.447 |
| P107 | `11bb2e14` | Have I Told You Lately That I Love You? | speech | 0.757 | 0.244 |
| P108 | `30f4b99e` | Bosque del Apache National Wildlife Refuge | speech | 0.975 | 0.108 |
| P109 | `01c9c08f` | South Dakota Saga (Part II) | speech | 0.765 | 0.067 |
| P110 | `9c01b799` | Alaska's Silver Millions (Part II) | mixed | 0.786 | 0.658 |
| P112 | `1e64eb45` | Valley Town | mixed | 0.369 | 0.609 |
| P113 | `7280b027` | South Chile | mixed | 0.827 | 0.604 |
| P114 | `b130f938` | Belo Horizonte | mixed | 0.585 | 0.651 |
| P115 | `2fbf7db5` | Brooklyn Goes to San Francisco | mixed | 0.819 | 0.538 |
| P116 | `7a496531` | Singing Wheels | mixed | 0.711 | 0.485 |
| P118 | `5b8e6fcf` | Space Ship Takeoff, a Technical Fantasy | mixed | 0.713 | 0.546 |
| P119 | `5194d42e` | THE PHOTOGRAPHER | speech | 0.919 | 0.177 |
| P120 | `ab9dfe7f` | Ant City | mixed | 0.699 | 0.589 |
| P124 | `93412ac5` | South Chile | mixed | 0.545 | 0.708 |
| P125 | `bc95af13` | Park Conscious | mixed | 0.603 | 0.644 |
| P126 | `aa02dd5d` | Moonwalk One, ca. 1970 | music | 0.114 | 0.965 |
| P127 | `6f0798e5` | Adelante Cubanos (Part I) | mixed | 0.76 | 0.576 |
| P128 | `de732920` | Aluminum on the March (Part II) | music | 0.178 | 0.907 |
| P130 | `fa366423` | Schedadxw: (pronounced cha-da-duch) | mixed | 0.74 | 0.519 |
| P132 | `d4a3d6bd` | Friendship Seven | mixed | 0.431 | 0.822 |
| P133 | `2cbeccf8` | River, The (Part I) | mixed | 0.549 | 0.787 |
| P134 | `e3bcea35` | Forestry and Forest Industries | speech | 0.783 | 0.031 |
| P135 | `a4191eff` | Visions of the wild | speech | 0.911 | 0.085 |
| P136 | `2477ecfa` | Japan | mixed | 0.386 | 0.824 |
| P137 | `fac33a23` | All My Babies | mixed | 0.459 | 0.855 |
| P139 | `eb72a2ca` | Under Western Stars | mixed | 0.774 | 0.651 |
| P142 | `fce0493b` | Moonwalk One, ca. 1970 | speech | 0.898 | 0.087 |
| P143 | `93dbe868` | Best Food In Town | speech | 0.69 | 0.042 |
| P144 | `fe240298` | Scatter radar: Space research from the ground | mixed | 0.765 | 0.605 |
| P145 | `e37a406f` | Cataloochee - The Center of the World | speech | 0.947 | 0.128 |
| P146 | `d51a32fa` | Wind: An Energy Alternative | mixed | 0.839 | 0.473 |
| P152 | `a0f20c0c` | Spring Comes to a Pond | speech | 0.917 | 0.105 |
| P153 | `2ceeb208` | Garden Wise (Pt 1) | mixed | 0.534 | 0.738 |
| P154 | `8f1ade6c` | Gift of Green | music | 0.225 | 0.971 |
| P155 | `d2234d4c` | Small Steps...Giant Strides | mixed | 0.692 | 0.392 |
| P156 | `9481e434` | House of the woods: A forest trilogy | music | 0.152 | 0.961 |
| P157 | `7408c21e` | Mobile Lab : Any Questions? | speech | 0.897 | 0.095 |
| P158 | `d4502f1a` | Friendship Seven | mixed | 0.375 | 0.874 |
| P159 | `e5dfacfb` | SPACE AGE RAILROAD | music | 0.333 | 0.888 |
| P160 | `d69a0d4b` | Eagle Has Landed: The Flight of Apollo 11 | speech | 0.679 | 0.06 |
| P163 | `a134989d` | RCA 16mm Sound Projector, The | mixed | 0.708 | 0.614 |
| P164 | `a20a26c8` | Safety: Harm Hides at Home | speech | 0.898 | 0.049 |
| P165 | `8942630a` | Spider Engineers | mixed | 0.708 | 0.386 |
| P166 | `dad9aa62` | Adelante Cubanos (Part II) | mixed | 0.613 | 0.622 |
| P167 | `6c83f23f` | Friendship Seven | music | 0.127 | 0.976 |
| P168 | `73b06371` | Living Stereo | mixed | 0.564 | 0.774 |

### scenes — 169 patches: speech 47, mixed 35, silence 34, none 27, noise 16, music 10

| patch | clip | title | kind | p speech | p music |
|---|---|---|---|---|---|
| P001 | `d33cbb8d` | All My Babies | speech | 0.733 | 0.233 |
| P002 | `1fd14e7b` | All My Babies | speech | 0.134 | 0.005 |
| P006 | `e589e99f` | The Green Promise | speech | 0.515 | 0.338 |
| P007 | `92dff0fb` | The Green Promise | speech | 0.429 | 0.242 |
| P008 | `12132de9` | Moonwalk One, ca. 1970 | music | 0.092 | 0.889 |
| P009 | `6a1a305b` | Moonwalk One, ca. 1970 | mixed | 0.259 | 0.828 |
| P010 | `8260ff4f` | All My Babies | speech | 0.657 | 0.336 |
| P011 | `811b2f17` | All My Babies | speech | 0.489 | 0.033 |
| P012 | `ba629ae0` | Adelante Cubanos (Part I) | mixed | 0.815 | 0.422 |
| P013 | `0bb6ca5c` | Adelante Cubanos (Part I) | mixed | 0.497 | 0.696 |
| P016 | `2f4c7c5d` | Moonwalk One, ca. 1970 | speech | 0.841 | 0.163 |
| P017 | `e60a94c6` | Who's Out There? | speech | 0.465 | 0.004 |
| P018 | `ed5ddece` | SPACE AGE RAILROAD | speech | 0.724 | 0.156 |
| P019 | `6ef60f82` | SPACE AGE RAILROAD | speech | 0.883 | 0.078 |
| P024 | `497a71c8` | Space Ship Takeoff, a Technical Fantasy | speech | 0.436 | 0.273 |
| P030 | `a62a0aca` | American Frontier (Part I) | mixed | 0.639 | 0.813 |
| P031 | `84aa2822` | Apollo 12: Pinpoint for Science | mixed | 0.588 | 0.432 |
| P032 | `64314e4a` | Apollo 12: Pinpoint for Science | speech | 0.783 | 0.266 |
| P033 | `2d3bb538` | Watershed wildfire | speech | 0.707 | 0.349 |
| P034 | `e477b1fc` | Watershed wildfire | mixed | 0.548 | 0.652 |
| P035 | `337a403c` | Watershed wildfire | mixed | 0.752 | 0.406 |
| P038 | `cb3249a7` | Garden Wise (Pt 1) | mixed | 0.567 | 0.686 |
| P039 | `07754a86` | Garden Wise (Pt 1) | mixed | 0.493 | 0.815 |
| P043 | `3c4b74ef` | Apollo 12: Pinpoint for Science | mixed | 0.427 | 0.608 |
| P044 | `b9c7e55d` | Apollo 12: Pinpoint for Science | mixed | 0.612 | 0.458 |
| P045 | `1702537b` | Master Hands | music | 0.079 | 0.943 |
| P046 | `db4f1c89` | Master Hands | music | 0.09 | 0.939 |
| P047 | `24f30c1f` | Master Hands | music | 0.166 | 0.928 |
| P048 | `700fd8b9` | Space Ship Takeoff, a Technical Fantasy | speech | 0.867 | 0.03 |
| P049 | `07a81b62` | Space Ship Takeoff, a Technical Fantasy | speech | 0.795 | 0.198 |
| P050 | `53af9aca` | Moonwalk One, ca. 1970 | speech | 0.46 | 0.077 |
| P051 | `8403c3ff` | Moonwalk One, ca. 1970 | mixed | 0.703 | 0.493 |
| P064 | `2d62a582` | Under Western Stars | speech | 0.877 | 0.203 |
| P065 | `e4d46b18` | Under Western Stars | speech | 0.251 | 0.028 |
| P066 | `9a3a8f78` | Street of Memory | speech | 0.509 | 0.38 |
| P067 | `a1e8fd53` | Street of Memory | speech | 0.471 | 0.279 |
| P068 | `215acf65` | Moonwalk One, ca. 1970 | mixed | 0.731 | 0.497 |
| P069 | `344ecde2` | Moonwalk One, ca. 1970 | mixed | 0.742 | 0.617 |
| P074 | `946db961` | Alaska's Silver Millions (Part I) | mixed | 0.36 | 0.821 |
| P075 | `8cf0f0b0` | Alaska's Silver Millions (Part I) | music | 0.148 | 0.982 |
| P076 | `da67e5d3` | Space Ship Takeoff, a Technical Fantasy | mixed | 0.562 | 0.656 |
| P077 | `d9b69b9c` | Space Ship Takeoff, a Technical Fantasy | mixed | 0.534 | 0.573 |
| P080 | `7cc49276` | Gardening | speech | 0.685 | 0.089 |
| P081 | `fd3ebfbc` | Gardening | speech | 0.692 | 0.144 |
| P083 | `d715aad1` | THE PHOTOGRAPHER | speech | 0.879 | 0.268 |
| P084 | `f9d9f50c` | Space Ship Takeoff, a Technical Fantasy | speech | 0.683 | 0.057 |
| P085 | `43e3bce2` | Space Ship Takeoff, a Technical Fantasy | speech | 0.94 | 0.034 |
| P088 | `2c18b6df` | Moonwalk One, ca. 1970 | speech | 0.973 | 0.244 |
| P089 | `72f7f4a3` | Moonwalk One, ca. 1970 | mixed | 0.769 | 0.355 |
| P092 | `dfb90fc2` | Legacy for Wings | music | 0.257 | 0.929 |
| P093 | `3ee92cb6` | Legacy for Wings | speech | 0.694 | 0.186 |
| P100 | `ca91a379` | Duck and Cover | speech | 0.842 | 0.025 |
| P101 | `b6055857` | Duck and Cover | speech | 0.872 | 0.051 |
| P102 | `7beab63b` | Moonwalk One, ca. 1970 | speech | 0.781 | 0.137 |
| P103 | `30841587` | Moonwalk One, ca. 1970 | speech | 0.525 | 0.043 |
| P109 | `19dfa6fd` | Gardening | speech | 0.714 | 0.117 |
| P110 | `2d361007` | Gardening | speech | 0.581 | 0.175 |
| P111 | `158d1d69` | ALASKAN EARTHQUAKE | speech | 0.676 | 0.136 |
| P112 | `421922ea` | ALASKAN EARTHQUAKE | speech | 0.566 | 0.117 |
| P115 | `6bbb6bae` | SPACE AGE RAILROAD | speech | 0.912 | 0.055 |
| P116 | `2aaf5cbd` | SPACE AGE RAILROAD | mixed | 0.622 | 0.445 |
| P117 | `3ff38ed1` | Moonwalk One, ca. 1970 | mixed | 0.499 | 0.891 |
| P118 | `0dc4c1b6` | Moonwalk One, ca. 1970 | mixed | 0.74 | 0.612 |
| P119 | `880356b0` | House of the woods: A forest trilogy | music | 0.121 | 0.943 |
| P120 | `d44d98d1` | House of the woods: A forest trilogy | mixed | 0.292 | 0.793 |
| P121 | `c30d92fb` | Scatter radar: Space research from the ground | mixed | 0.787 | 0.499 |
| P122 | `7a24b945` | Scatter radar: Space research from the ground | mixed | 0.627 | 0.65 |
| P123 | `1dfa8a28` | This Is My Railroad (Part II) | mixed | 0.899 | 0.358 |
| P124 | `09a44528` | This Is My Railroad (Part II) | mixed | 0.658 | 0.472 |
| P125 | `d9b15c8a` | Watershed wildfire | mixed | 0.624 | 0.673 |
| P126 | `d359a943` | Watershed wildfire | mixed | 0.781 | 0.459 |
| P131 | `f93b72d8` | House of the woods: A forest trilogy | music | 0.1 | 0.969 |
| P132 | `9481e434` | House of the woods: A forest trilogy | music | 0.152 | 0.961 |
| P133 | `efd279c5` | Garden Wise (Pt 1) | mixed | 0.446 | 0.787 |
| P134 | `50439afb` | Garden Wise (Pt 1) | mixed | 0.454 | 0.704 |
| P138 | `4b6f22cf` | All My Babies | speech | 0.491 | 0.017 |
| P139 | `afae4e45` | Duck and Cover | speech | 0.768 | 0.02 |
| P140 | `05255d0e` | Duck and Cover | speech | 0.894 | 0.06 |
| P141 | `1bf67e90` | American Frontier (Part I) | mixed | 0.602 | 0.589 |
| P144 | `cad4cc3e` | Under Western Stars | mixed | 0.504 | 0.721 |
| P145 | `c8c7e9a1` | Under Western Stars | mixed | 0.423 | 0.71 |
| P152 | `9a339eb1` | Gardening | speech | 0.54 | 0.057 |
| P153 | `92f51cee` | Gardening | speech | 0.658 | 0.083 |
| P154 | `5e066608` | ALASKAN EARTHQUAKE | mixed | 0.56 | 0.508 |
| P155 | `c02dfc7f` | ALASKAN EARTHQUAKE | mixed | 0.553 | 0.409 |
| P160 | `6f152095` | Master Hands | music | 0.082 | 0.937 |
| P161 | `9859ca55` | Space Ship Takeoff, a Technical Fantasy | speech | 0.888 | 0.113 |
| P162 | `a66d1b8d` | Sound And The Story | speech | 0.544 | 0.013 |
| P163 | `93265ca5` | Sound And The Story | speech | 0.934 | 0.029 |
| P164 | `d69a0d4b` | Eagle Has Landed: The Flight of Apollo 11 | speech | 0.679 | 0.06 |
| P167 | `6d8ef29d` | All My Babies | speech | 0.716 | 0.143 |
| P168 | `f2b05316` | All My Babies | speech | 0.862 | 0.031 |

### suite — 169 patches: mixed 43, none 36, silence 35, speech 32, music 17, noise 6

| patch | clip | title | kind | p speech | p music |
|---|---|---|---|---|---|
| P000 | `8f8f18e8` | All My Babies | mixed | 0.526 | 0.753 |
| P005 | `fa9b10b1` | Duck and Cover | speech | 0.863 | 0.033 |
| P007 | `7987f81b` | Master Hands | music | 0.132 | 0.937 |
| P009 | `c2ff8b13` | All My Babies | speech | 0.664 | 0.055 |
| P010 | `ba92aa05` | Children Must Learn, The | music | 0.106 | 0.664 |
| P012 | `4ccc0378` | Duck and Cover | speech | 0.858 | 0.026 |
| P013 | `699c5e5b` | All My Babies | speech | 0.445 | 0.123 |
| P015 | `59dbacc1` | Master Hands | music | 0.093 | 0.94 |
| P017 | `ce9c888a` | Singing Wheels | mixed | 0.627 | 0.68 |
| P018 | `fbbe77ff` | All My Babies | speech | 0.514 | 0.098 |
| P019 | `72be546d` | Don't Talk to Strangers | mixed | 0.629 | 0.443 |
| P020 | `22ba9c11` | Beginning to Date | mixed | 0.65 | 0.373 |
| P021 | `8f2b07fc` | Moonwalk One, ca. 1970 | speech | 0.921 | 0.202 |
| P024 | `d7a7f1dd` | Sound Waves And Their Sources | mixed | 0.545 | 0.696 |
| P025 | `e07370d2` | Panama-Pacific International Exposition | mixed | 0.517 | 0.899 |
| P032 | `7dc2787c` | All My Babies | mixed | 0.581 | 0.716 |
| P035 | `5359c639` | Mother Mack Trains Her Seven Puppies | speech | 0.845 | 0.111 |
| P036 | `13cd9ffe` | Oil Across Arabia | mixed | 0.656 | 0.643 |
| P038 | `05a0c70c` | Garden Wise (Pt 2) | mixed | 0.395 | 0.849 |
| P040 | `de312d4e` | Wheels of Progress | mixed | 0.612 | 0.622 |
| P041 | `cdf331dd` | Bacteria: Friend and Foe | speech | 0.744 | 0.108 |
| P042 | `ce4e5ac7` | Who's Out There? | mixed | 0.732 | 0.613 |
| P043 | `69e96a5f` | Moonwalk One, ca. 1970 | mixed | 0.376 | 0.798 |
| P046 | `fc03708d` | EVOLUTION OF THE OIL INDUSTRY, THE | mixed | 0.612 | 0.624 |
| P047 | `2b34c11d` | Moonwalk One, ca. 1970 | speech | 0.594 | 0.241 |
| P050 | `2c2401f2` | Beginning to Date | music | 0.15 | 0.96 |
| P051 | `c0c9a9ee` | Moonwalk One, ca. 1970 | speech | 0.855 | 0.017 |
| P053 | `3764806f` | Appreciating Our Parents | speech | 0.734 | 0.042 |
| P055 | `8a88c574` | Looking Ahead Through Plexiglas A | speech | 0.871 | 0.199 |
| P058 | `98ef04be` | Moonwalk One, ca. 1970 | music | 0.243 | 0.917 |
| P059 | `7b39c5dc` | Towers, The | music | 0.086 | 0.962 |
| P060 | `6327b659` | The Middleton Family at the New York World's Fair | music | 0.237 | 0.921 |
| P061 | `6d49940b` | Miss Clark Introduces Panorama | speech | 0.726 | 0.047 |
| P063 | `580e3e95` | Friendship Seven | mixed | 0.703 | 0.529 |
| P067 | `89edb74e` | 'Till It Helps! | mixed | 0.698 | 0.727 |
| P068 | `5d62ea84` | Moonwalk One, ca. 1970 | mixed | 0.29 | 0.951 |
| P070 | `c595eefe` | Third Avenue El | music | 0.106 | 0.97 |
| P073 | `60dd29ed` | Moonwalk One, ca. 1970 | speech | 0.955 | 0.099 |
| P074 | `fa04c614` | Spider Engineers | mixed | 0.439 | 0.68 |
| P075 | `284f7354` | Schedadxw: (pronounced cha-da-duch) | music | 0.151 | 0.975 |
| P077 | `223ce855` | Moonwalk One, ca. 1970 | speech | 0.865 | 0.035 |
| P078 | `cd333c55` | The Middleton Family at the New York World's Fair | mixed | 0.572 | 0.592 |
| P079 | `48aeecdd` | Dating: Do's and Don'ts | speech | 0.47 | 0.206 |
| P080 | `f1260747` | Garden Wise (Pt 1) | mixed | 0.572 | 0.779 |
| P082 | `4cffd1b2` | Friendship Seven | music | 0.099 | 0.967 |
| P083 | `e7b46e81` | Moonwalk One, ca. 1970 | speech | 0.882 | 0.165 |
| P086 | `62789b6b` | Under Western Stars | speech | 0.907 | 0.208 |
| P092 | `2fd4cb30` | Friendship Seven | mixed | 0.703 | 0.541 |
| P093 | `c02dfc7f` | ALASKAN EARTHQUAKE | mixed | 0.553 | 0.409 |
| P094 | `01c9c08f` | South Dakota Saga (Part II) | speech | 0.765 | 0.067 |
| P096 | `f4f01202` | Master Hands | music | 0.035 | 0.969 |
| P098 | `6bb6d333` | Eagle Has Landed: The Flight of Apollo 11 | speech | 0.938 | 0.106 |
| P099 | `b5c58932` | Third Avenue El | music | 0.278 | 0.951 |
| P100 | `ceca9354` | Schedadxw: (pronounced cha-da-duch) | mixed | 0.73 | 0.235 |
| P102 | `36f08d09` | Garden Wise (Pt 1) | mixed | 0.607 | 0.819 |
| P103 | `b2b5df13` | Moonwalk One, ca. 1970 | speech | 0.714 | 0.285 |
| P104 | `575666be` | Town and the Telephone, The | mixed | 0.842 | 0.466 |
| P105 | `32f06d37` | They Call It All-States | mixed | 0.604 | 0.708 |
| P106 | `deb488b8` | Duck and Cover | speech | 0.864 | 0.033 |
| P107 | `8315fd8e` | Manhattan Waterfront | mixed | 0.704 | 0.429 |
| P109 | `2b386b7f` | Boy in Court | speech | 0.748 | 0.182 |
| P110 | `6389c954` | Duck and Cover | mixed | 0.63 | 0.686 |
| P113 | `80565bbe` | Industries of the United States: Steel - The Hardest Metal in the World | music | 0.396 | 0.884 |
| P114 | `3137838a` | Master Hands | music | 0.065 | 0.962 |
| P115 | `ca407ef2` | Your Permit to Drive | mixed | 0.634 | 0.294 |
| P116 | `8d5bb8ab` | Speaking of Rubber (Part II) | mixed | 0.488 | 0.826 |
| P118 | `75803cc7` | Cancer | speech | 0.813 | 0.03 |
| P120 | `93412ac5` | South Chile | mixed | 0.545 | 0.708 |
| P121 | `035256dc` | Show 'Em the Road (Part II) | mixed | 0.364 | 0.773 |
| P122 | `c30d92fb` | Scatter radar: Space research from the ground | mixed | 0.787 | 0.499 |
| P124 | `f6abf039` | SPACE AGE RAILROAD | speech | 0.751 | 0.126 |
| P125 | `2daf772a` | Moonwalk One, ca. 1970 | mixed | 0.775 | 0.462 |
| P126 | `340884cb` | Scatter radar: Space research from the ground | mixed | 0.718 | 0.566 |
| P129 | `a75d29ae` | Moonwalk One, ca. 1970 | speech | 0.585 | 0.281 |
| P131 | `35dea94e` | Powering One Corner of the World | mixed | 0.698 | 0.453 |
| P132 | `fe0a419d` | Taiwan | mixed | 0.532 | 0.613 |
| P134 | `fc18ad96` | Middle America | mixed | 0.618 | 0.348 |
| P135 | `55f7af30` | No Time for Ugliness (Part I) | mixed | 0.411 | 0.758 |
| P136 | `4c58941d` | St. John Virgin Islands National park | speech | 0.962 | 0.211 |
| P137 | `8287ae9d` | Under Western Stars | speech | 0.873 | 0.149 |
| P145 | `e518d4dd` | Duck and Cover | speech | 0.899 | 0.04 |
| P146 | `98877a46` | Park Conscious | music | 0.362 | 0.968 |
| P148 | `cb6d95da` | Family Life | speech | 0.812 | 0.041 |
| P150 | `df0223a0` | All My Babies | music | 0.282 | 0.921 |
| P156 | `9a339eb1` | Gardening | speech | 0.54 | 0.057 |
| P157 | `8d3fc2fa` | All My Babies | speech | 0.533 | 0.049 |
| P161 | `73c16614` | Master Hands | music | 0.261 | 0.921 |
| P162 | `ead99a2b` | Let's Go To The Movies | mixed | 0.596 | 0.659 |
| P163 | `019e25f6` | Care of the Hair and Nails | mixed | 0.573 | 0.75 |
| P164 | `647a6a51` | Meet Your Federal Government | mixed | 0.698 | 0.626 |
| P166 | `c8eeee5b` | Under Western Stars | mixed | 0.439 | 0.715 |
| P167 | `6a336c56` | Door to Heaven, The | mixed | 0.733 | 0.505 |
