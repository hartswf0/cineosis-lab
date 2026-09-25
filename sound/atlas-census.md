# WYGWYL · ATLAS — sound census

Source: https://hartswf0.github.io/butterfly-halfworld/wygwyl/atlas.html (fetched 2026-09-25). Only JSON, HTML, MJS and MD files were read; no audio was downloaded. The full data is in `atlas-census.json`: 30 classification schemes, 135 voice records, 34 element types, 40 mix rules and 29 experiments.

## 1. What kinds of sound exist

The genome gives the atlas's own verdict on its material: **one substance**. Almost everything is the poet's voice in different states, set over a drone and other people's songs. Counts below come from the files.

| family | element types (count) |
|---|---|
| **the poet (RY)** | reading ×14 (1,269 s; 267 lines, 397 phrases, 2,799 words) · line sample ×267 · word cut ×2,799 (A 398 / B 1,161 / C 1,240) · chop/VOX power phrase ×439 (79 hooks) · take "dressings": 492 files that reduce to 82 takes (410 redundant copies; T001 alone ×243) |
| **other mouths** | codex sung line ×157 (codex 83, song 54, dolphin 11, combined 9; 143 pass the rewhisper check) · carrier songs ×80 (740 read↔sung pairs, median coverage 0.46; poem 11 has none) · line variants (852 instances) · isolated demucs vocals ×34 (never mixed) |
| **drone** | unified drone ×1: 1,440.1 s, split into 14 poem spans. It is the corpus clock |
| **mined pack** (210) | LOOP 60 · BED 40 · HIT 60 · TEXTURE 30 · RISER 20. Of these, 62 were cut from video soundtracks and 37 carry speech |
| **songs (VOLHOLLA)** | 34 songs from 11 albums · 744 section segments in 19 families · 516 bar-quantized elements (2-bar 384 / 4-bar 132) · 223 songloop "orchestra chairs" (DRUMS 82, PIANO 80, SYNTH 32, VOCALS 12, BASS 8, STRINGS 7, SFX 2) · 68 bass+drums stems · 34 OTHER stems (never used) |
| **placed events** | ghost (35 in radio v2) · coda sung 26 · coda 14 · hit-on-cue/foley · whisper (a pool of 40 poet chops) · silence/breath gap (606 prosody events, 176 BREATH cuts) |
| **synthesised** | scan-synthesis bandbank (56 bands × 64 columns; 14 prosodic engines × 11 modes) · water/flood interference field · key-bed · disintegrating tape loops (transmission) · words drifted two octaves down · radio dial drift · ES+ seal fallback synth |
| **unplayed** | MANTA variant mixes ×88 · butterfly foley kit ×33 + themes ×9 · Markov archive audio (43 per the genome, 0 per audit.json) |

## 2. The voices

- **RY, the spring**: f0 111.1 Hz, poet_dist 1.0. This is the reference that every other distance is measured from.
- **cast.json, 80 named mouths.** Each name is REGISTER + HABITAT + ordinal.
  - **Register comes from f0:** ABYSSAL 24 (59.9–75.4 Hz), DEEP 37 (78.5–101.7), LOW 13 (120.6–138.3), HIGH 6 (146.4–188.2).
  - **Habitat is the kind of carrier:** SINGER = song 19, CANTOR = codex 13, DOLPHIN 13, ELDER = ancient 13, CHORUS = combined 11, FRAGMENT = segment 11.
  - **Distance from the poet** ranges 6.72–17.83.
- **voicehunt.json**: 141 clean items fall into 11 clusters (silhouette 0.287), ranked by distance from the poet:
  - H6 is the poet (1.0)
  - H2 contains the ElevenLabs mortician (5.55)
  - H9 is other mouths on MANTA lines (6.52)
  - H3 is mixed narration (6.89)
  - H5, H8, H4, H1, H10 and H7 are AI singers (8.06 up to 13.54)
  - It also lists the 40 farthest strangers (9.21–14.24).
- **voices.json**: a take census of V1 and V2. The genome calls it unreliable: MFCC+F0 on mixed audio gives silhouette 0.237.

## 3. Axes the atlas already measures

- **Spectral**: centroid (Hz) and flatness (pack.json, sonic.json); tilt, flux, F1 and F2 (voice lanes); band balance sub/low/lowmid/mid/pres/air (cut book).
- **Loudness**: pack loud, sonic loud (dB) and density (dens), plus LUFS and LRA in the cut book.
- **Envelope**: a 24-point contour on every pack segment and every sonic sound (1,442 `c` arrays). The genome notes these are used only as decoration.
- **Time**: bpm, bars, bar_s and phase, seam score, duration, onsets/min, rests.
- **Pitch and key**: key and key confidence (pack and songloops); per-word f0 (median 106 Hz); poem root folded into 32–64 Hz plus a mode.
- **Voice**: f0, poet_dist, voicing, stress, zcr, attack, cut grade, and word recovery (rewhisper).
- **Meaning**: CLAP instrument/mood labels, 847 ekphrasis phrases matched to shots, DINOv2 "form" layout, CLAP "meaning" layout.
- **Ecology**: the Schafer/Truax roles in sonic.json: soundmark 490, song 778, keynote 54, rhythm 60, signal 60.

The Schafer/Truax mapping is mechanical:

- **keynote** = BED 27 + TEXTURE 26 + the drone
- **signal** = HIT 44 + RISER 16
- **rhythm** = the 60 LOOPs
- **soundmark** = voice: 439 chops, 14 readings, and 37 pack segments that carry speech
- **song** = the 34 songs plus their 744 segments. Their centroid and flatness are placeholders (0), not measurements.

The pack classes separate cleanly on the measured medians:

| class | duration | centroid | flatness |
|---|---|---|---|
| LOOP | 2.56 s | 346 Hz | 0.008 |
| BED | 7.99 s | 966 Hz | 0.10 |
| RISER | 3.99 s | 1,011 Hz | 0.17 |
| HIT | 1.16 s | 2,017 Hz | 0.29 |
| TEXTURE | 4.99 s | 3,495 Hz | 0.74 |

Read from LOOP down to TEXTURE, this is a clean line from tonal to noisy.

## 4. The mixing rules (exact constants in the JSON)

- **Sidechain duck (poemworlds)**:
  - The voice counts as speaking when rms > 0.012.
  - The world bus drops to 1 − 0.9·amt. It bows with time constant 0.03 s and rises with 0.16 s.
  - A mid-band dip (peaking 1400 Hz, Q 0.7) deepens to −7·amt dB while she speaks.
  - Other mouths on the vox bus drop to 0.12.
  - The master compressor is −18 dB, 3:1.
  - Depth: lowpass = 800 + 12000·(1−d)^1.6.
- **Radio v2 gate**:
  - voice-band SNR ≥ 13 dB during every measured word
  - zero collisions in the silences
  - the outro sits ≥ 6 dB below the body
  - CLAP juror margin > 0.02
  - The offline sidechain carves 200–4500 Hz with a 30 ms attack and 300 ms rise, while bass keeps 88%.
  - Across 44 passes, every revision was attenuation.
- **Rewhisper gate**:
  - ≥ 85% of the words must survive the mix. The measured result was 0.925–0.99, with 119 words lost in total.
  - A ceiling baseline divides by whisper's result on the clean master (kept_of_possible 0.943–1.0).
- **Water table laws**:
  - No other mouth may start until she is done and has been quiet (rms < 0.015) for more than 2 s.
  - Voice priority is absolute: yielding to 0 uses time constant 0.045.
  - The key-bed never leaves. Its gain is 0.045 while she speaks, 0.09 in breaths, 0.13 after she finishes.
  - Wear: lowpass = 8000·e^(−w/900) + 300 Hz, dropout probability ≤ 0.35.
  - Key matching picks a PIANO/STRINGS/SYNTH element whose tonic matches the poem's root, or else its fifth.
- **Radio-scapes flood**: 0.10 under her words, 0.85–1.0 in her silences. It bows with time constant 0.05 s and blooms with 0.55 s. Crests above 0.55 count as construction.
- **Snap to breath (pacing desk)**:
  - A hit stays on a cut that is already inside a silence. Otherwise it moves to the next silence within 3.0 s that lasts ≥ 1.0 s.
  - Hits are at least 7 s apart.
  - Whispers go only into silences ≥ 3.5 s, at least 18 s apart, and duck the film to 42%.
- **World score**: a cue that lands under her words moves to the line end + 0.15 s. A ghost is placed only if there is ≥ 4 s of room; ghost gain 0.3, bed gain 0.12.
- **Bar and tempo**:
  - Song elements are cut as 2- or 4-bar windows on the song's own grid, each with a seam score.
  - The ES+ seal matches tempo with playbackRate = tempo / sourceTempo.
  - Cut-book cut types: BAR 542, BREATH 176, SECTION 77.
- **Reconstitute**: scores each word by grade (A 4 / B 2 / C 0) minus |Δf0|/25. Gaps between words use the poet's own pause statistics × 0.7 × pace.

The genome's verdict: the proven spine is ONE CLOCK + VOICE UNTOUCHED + MEASURED GATE (rewhisper) + SNAP TO BREATH. Every approach that failed repeatedly had one thing in common: it cut the voice with a razor (CUT AND PLACE).

## 5. Candidate axes for a periodic table of sound (supported by the data)

1. **Source**: poet voice / other mouth / music (song, instrument) / noise (texture, hit) / synthesis (bandbank). This comes from sonic `cls`, the pack `speech` flag, and `kind`.
2. **Eco role**: keynote / signal / rhythm / soundmark / song (sonic.json, all 1,442 sounds).
3. **Distance from the poet**: poet_dist 1.0 up to 17.83 (cast, voicehunt, codex). This works as a group number: the poet, then narration kin, then MANTA mouths, then the AI singers.
4. **Register**: f0 bands ABYSSAL / DEEP / LOW / HIGH, with RY at 111 Hz between DEEP and LOW.
5. **Temporal shape**: drone / loop / bed / riser / hit / chop / line / reading, using pack class, duration, and the 24-point contour.
6. **Tonal ↔ noisy**: spectral flatness, from 0.003 (drone) to 0.74 (texture). Centroid, from 205 Hz up to about 3,500 Hz, supplies a brightness axis alongside it.
7. **Periodicity and grid**: bpm, bars, and seam score for loops and song elements. Everything else has bpm 0.
8. **Tonality**: key and key confidence, available only on the pack, the songloops, and the song key regions.
9. **Energy contour**: rising (riser) / falling / flat (bed) / impulsive (hit), taken from the `c` and `contour` arrays.
10. **Intelligibility / integrity**: cut grade A/B/C, rewhisper recovery, and `fit`. These say how much of the word survives.
11. **Mix behaviour** (what a sound does in a mix): owns the front / ducks / yields / kneels / snaps to breath / fills silence. This comes from the rules in section 4.
12. **Wear state**: fresh vs. worn (watertable's wear ledger) and the 410 existing dressings. This is the decay axis the genome says was never built.

**Data caveats before building on these** (details in `discrepancies` in the JSON):

- pack `loud` is unnormalised on 8 rows.
- song rows in sonic.json have no measured centroid or flatness.
- atlantis-standard has tempo −1 on every row except the 60 loops.
- The genome says "~277" poem lines; the files say 267.
- The audit's Markov count (0) and the genome's (43) disagree.
