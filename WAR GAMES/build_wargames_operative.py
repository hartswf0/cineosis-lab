#!/usr/bin/env python3
"""
Build the 8 WarGames (1983) Operative Syntagm Specimens for lab/syntagm/operative/examples.json
and extract their playable 480p H.264/AAC MP4 passages + poster frames.

Covers all 8 categories of Christian Metz's Grand Syntagmatique:
1. wg_silo_key       — alternate    (Missile silo turn-key standoff: Jerry's hand on the launch key ↔ John drawing his .38 revolver)
2. wg_arcade_warroom — parallel     (20-cent Galaga arcade cabinet ↔ NORAD Crystal Palace war-room screens)
3. wg_crystal_palace — autonomous   (David and Jennifer enter the NORAD Crystal Palace command floor in one sweeping establishing pass)
4. wg_imsai_setup    — descriptive  (David's bedroom workstation: IMSAI 8080 front panel, acoustic coupler modem, CRT prompt, voice synthesizer)
5. wg_shall_we_play  — scene        ("Shall We Play a Game?": WOPR lists games from chess to Global Thermonuclear War in real-time dialogue)
6. wg_falken_search  — episodic     (Compressed research progression: library microfiche → password deduction → Falken's obituary → Hume's trace)
7. wg_norad_escape   — ordinary     (David's escape from NORAD detention: tape recorder trick → lockpick wire → tour corridor → payphone hack)
8. wg_cpe_scenarios  — bracket      (WOPR's rapid cascade of nuclear war scenarios: US FIRST STRIKE, USSR FIRST STRIKE, NATO/WARSAW, ZERO WINNER)
"""
import hashlib, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VIDEO = os.path.join(HERE, "WarGames_1983_H264.mp4")
EX_PATH = os.path.join(ROOT, "lab", "syntagm", "operative", "examples.json")
MEDIA_DIR = os.path.join(ROOT, "lab", "syntagm", "operative", "media")

os.makedirs(MEDIA_DIR, exist_ok=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


SPECIMENS = [
    {
        "id": "wg_silo_key",
        "source": "wargames",
        "type": "alternate",
        "title": "Turn-key standoff in the missile silo",
        "claim": "Capt. Jerry Lawson (Strand A) and Lt. John Spencer (Strand B) occupy two stations 12 feet apart inside the sealed ICBM launch capsule while the EAM authentication clock (Strand C) forces simultaneous decision. Each cut alternates between Jerry reaching for the brass launch key and John unholstering his .38 revolver to stop an unverified nuclear launch.",
        "rival": "Scene (continuous space-time) is a strong rival because both officers share one subterranean capsule, but the camera splits the capsule into two non-overlapping operational poles bridged by the synchronous turn-key countdown.",
        "limit": "Covers the 36-second authentication and gun-draw climax inside the cold-launch drill (04:30.0–05:06.0) rather than the entire 5-minute prologue.",
        "question": "Does grouping Jerry's console shots and John's refusal shots destroy the simultaneous turn-key deadline?",
        "operation": "group",
        "start": 270.0,
        "end": 306.0,
        "relationKind": "simultaneous action",
        "blocks": [
            {
                "id": "sk1", "start": 270.0, "end": 275.2, "strand": "C",
                "label": "Launch capsule red alert & EAM authentication",
                "sign": "13",
                "signEvidence": "Flashing red annunciators and klaxons saturate the sealed missile capsule as a totalizing situation."
            },
            {
                "id": "sk2", "start": 275.2, "end": 280.4, "strand": "A",
                "label": "Jerry locks his launch key into the switch",
                "sign": "15",
                "signEvidence": "A trained hand inserts the physical brass launch switch to cross the threshold from readiness to firing."
            },
            {
                "id": "sk3", "start": 280.4, "end": 285.8, "strand": "B",
                "label": "John demands phone verification from SAC",
                "sign": "4",
                "signEvidence": "Sweat-beaded close-up held between institutional obedience and terror of killing twenty million people."
            },
            {
                "id": "sk4", "start": 285.8, "end": 290.6, "strand": "A",
                "label": "Jerry orders 'Turn your key, sir!'",
                "sign": "14",
                "signEvidence": "Direct two-pole confrontation across the twelve-foot span between the two launch locks."
            },
            {
                "id": "sk5", "start": 290.6, "end": 295.4, "strand": "B",
                "label": "John's hand freezes over the second switch",
                "sign": "11",
                "signEvidence": "The trembling hand above the un-turned key functions as the visible index of human hesitation."
            },
            {
                "id": "sk6", "start": 295.4, "end": 300.6, "strand": "A",
                "label": "Jerry unholsters his .38 service revolver",
                "sign": "8",
                "signEvidence": "The revolver emerges as a charged fetish of command compulsion inside the nuclear capsule."
            },
            {
                "id": "sk7", "start": 300.6, "end": 306.0, "strand": "B",
                "label": "Cocked hammer aimed at John's head at the switch",
                "sign": "14",
                "signEvidence": "Point-blank duel between mechanical protocol and human conscience at the moment of launch."
            }
        ]
    },
    {
        "id": "wg_arcade_warroom",
        "source": "wargames",
        "type": "parallel",
        "claim": "The cut juxtaposes two regimes of vector simulation without asserting simultaneous action: David Lightman's glowing arcade cabinet at 20 cents a token (Strand A) and NORAD's strategic projection boards tracking Soviet bomber corridors (Strand B). The montage compares play-abstraction and military abstraction as isomorphic vector worlds.",
        "title": "Arcade vectors and war-room vectors",
        "rival": "Bracket syntagma would treat both spaces as examples of one single category ('screens'), whereas this passage alternates the two poles to stage an explicit thematic comparison between teenage coin-op play and nuclear command.",
        "limit": "Constructed from the contiguous transition window (06:18.0–06:54.0) bridging Cheyenne Mountain's briefing transition and the Seattle arcade sequence.",
        "question": "What happens to the comparison between coin-op play and nuclear command when the strands are grouped?",
        "operation": "group",
        "start": 378.0,
        "end": 414.0,
        "relationKind": "thematic comparison",
        "blocks": [
            {
                "id": "aw1", "start": 378.0, "end": 384.5, "strand": "B",
                "label": "Cheyenne Mountain tunnel & strategic transition",
                "sign": "13",
                "signEvidence": "The fortified granite bunker establishes the institutional encompassers of Cold War command."
            },
            {
                "id": "aw2", "start": 384.5, "end": 390.8, "strand": "A",
                "label": "Galaga vector bursts on the arcade CRT",
                "sign": "3",
                "signEvidence": "Pure acentred phosphor vectors fire and explode in a black electronic field without human gravity."
            },
            {
                "id": "aw3", "start": 390.8, "end": 397.2, "strand": "B",
                "label": "Phosphor score readout & vector grid geometry",
                "sign": "44",
                "signEvidence": "The graphic grid must be read simultaneously as spatial trajectory and numerical score table."
            },
            {
                "id": "aw4", "start": 397.2, "end": 405.5, "strand": "A",
                "label": "David immersed in arcade joystick reflexes",
                "sign": "1",
                "signEvidence": "David's body and hands anchor the frame as the privileged sensory hub of the cabinet's neon world."
            },
            {
                "id": "aw5", "start": 405.5, "end": 414.0, "strand": "B",
                "label": "Crowd of high-school spectators around the screen",
                "sign": "5",
                "signEvidence": "Faces bathed in shared CRT glow merge into a single collective affect of wonder."
            }
        ]
    },
    {
        "id": "wg_crystal_palace",
        "source": "wargames",
        "type": "autonomous",
        "title": "Entering the NORAD Crystal Palace",
        "claim": "A single continuous camera movement and sustained architectural reveal introduces the multi-tier NORAD War Room ('The Crystal Palace'): overhead status Mercator projections, tiered radar consoles, and glowing DEFCON indicators cohere inside one uninterrupted spatiotemporal take before the tour breaks into analytical reverse shots.",
        "rival": "Descriptive syntagma would achieve this survey through a chain of discrete detail cuts; here the camera's own reframing performs the synthesis inside an autonomous span.",
        "limit": "Bounded by the tour group stepping through the blast doors into the War Room overlook (07:32.0–07:56.0).",
        "question": "If the duration of this establishing movement is halved, does the command center still register as an encompassing world?",
        "operation": "halve",
        "start": 452.0,
        "end": 476.0,
        "relationKind": "continuous reframing",
        "blocks": [
            {
                "id": "cp1", "start": 452.0, "end": 460.0, "strand": "A",
                "label": "Threshold of the Crystal Palace balcony",
                "sign": "2",
                "signEvidence": "Liquid camera movement flows from the observers at the rail into the vast glowing command amphitheater."
            },
            {
                "id": "cp2", "start": 460.0, "end": 468.0, "strand": "A",
                "label": "Pan across the giant Mercator projection boards",
                "sign": "13",
                "signEvidence": "The monumental geopolitical maps and DEFCON displays dwarf every individual operator on the floor."
            },
            {
                "id": "cp3", "start": 468.0, "end": 476.0, "strand": "A",
                "label": "Tiered consoles and WOPR mainframe housing",
                "sign": "43",
                "signEvidence": "The command room itself is laid out as an externalized electronic brain processing planetary state."
            }
        ]
    },
    {
        "id": "wg_imsai_setup",
        "source": "wargames",
        "type": "descriptive",
        "title": "David's IMSAI 8080 bedroom workstation",
        "claim": "Successive shots inventory the objects coexisting in David's bedroom workstation at the same moment — the IMSAI 8080 front-panel toggle switches, the 17-inch monochrome CRT monitor, the acoustic coupler cradle, and the floppy drive — without advancing an irreversible causal plot beat.",
        "rival": "Scene would require a continuous dramatic interaction whose order cannot be commuted; here the shots catalog the co-present apparatus of a 1983 phreaker bedroom.",
        "limit": "Drawn from David's initial workstation setup and grade-change preparation in his bedroom (10:42.0–11:14.0).",
        "question": "Does reversing the order of these workstation details change our understanding of the room, or do they remain co-present objects?",
        "operation": "reverse",
        "start": 642.0,
        "end": 674.0,
        "relationKind": "spatial coexistence",
        "blocks": [
            {
                "id": "im1", "start": 642.0, "end": 650.0, "strand": "A",
                "label": "IMSAI 8080 front panel & bedroom desk",
                "sign": "10",
                "signEvidence": "Red-and-blue toggle switches, reference binders, and stacked hardware define a functional hacker habitus."
            },
            {
                "id": "im2", "start": 650.0, "end": 658.0, "strand": "B",
                "label": "Acoustic coupler modem & rotary handset",
                "sign": "8",
                "signEvidence": "The rubber modem cups waiting for the telephone handset hold the latent charge of network intrusion."
            },
            {
                "id": "im3", "start": 658.0, "end": 666.0, "strand": "A",
                "label": "Phosphor CRT screen & keyboard prompt",
                "sign": "44",
                "signEvidence": "Monospace terminal characters turn the television tube into an operative text surface."
            },
            {
                "id": "im4", "start": 666.0, "end": 674.0, "strand": "B",
                "label": "David and Jennifer framed by the glowing terminal",
                "sign": "4",
                "signEvidence": "Blue-white phosphor light models both faces as surfaces of curiosity before the dial-up begins."
            }
        ]
    },
    {
        "id": "wg_shall_we_play",
        "source": "wargames",
        "type": "scene",
        "title": "Shall We Play a Game? · WOPR's game list",
        "claim": "Continuous real-time exchange in David's bedroom as the Sunnyvale dial-up connects to Joshua/WOPR: each cut between the scrolling CRT text (Strand A), the Votrax voice synthesizer (Strand C), and David & Jennifer's reactions (Strand B) preserves unbroken acoustic and dramatic time without temporal ellipsis.",
        "rival": "Alternate syntagma is a rival if one treats the Sunnyvale/Cheyenne mainframe as a distant simultaneous space, but the film restricts the visual field entirely to David's room so that the remote machine speaks inside one continuous bedroom scene.",
        "limit": "Spans the discovery of the game list and the appearance of 'GLOBAL THERMONUCLEAR WAR' on the CRT (27:30.0–28:10.0).",
        "question": "If you reverse the blocks of this dialogue scene, does the causal progression from 'LIST GAMES' to 'GLOBAL THERMONUCLEAR WAR' collapse?",
        "operation": "reverse",
        "start": 1650.0,
        "end": 1690.0,
        "relationKind": "continuous scene",
        "blocks": [
            {
                "id": "sp1", "start": 1650.0, "end": 1658.0, "strand": "A",
                "label": "CRT prints FALKENS MAZE, BLACK JACK, CHESS",
                "sign": "44",
                "signEvidence": "We must read the scrolling ASCII catalog line by line to grasp the escalation from parlor games to war."
            },
            {
                "id": "sp2", "start": 1658.0, "end": 1666.0, "strand": "B",
                "label": "David and Jennifer watch the scrolling games",
                "sign": "4",
                "signEvidence": "Close two-shot in CRT glow registers the shift from disappointment to excitement as strategic titles appear."
            },
            {
                "id": "sp3", "start": 1666.0, "end": 1674.0, "strand": "A",
                "label": "THEATERWIDE BIOTOXIC AND CHEMICAL WARFARE",
                "sign": "11",
                "signEvidence": "Military-grade nomenclature inside a supposed toy company directory acts as an index of a disguised system."
            },
            {
                "id": "sp4", "start": 1674.0, "end": 1682.0, "strand": "C",
                "label": "GLOBAL THERMONUCLEAR WAR appears at the bottom",
                "sign": "32",
                "signEvidence": "The ultimate catastrophe appears as the aberrant final term in a series that began with Tic-Tac-Toe."
            },
            {
                "id": "sp5", "start": 1682.0, "end": 1690.0, "strand": "B",
                "label": "David types 'GLOBAL THERMONUCLEAR WAR'",
                "sign": "15",
                "signEvidence": "A single decisive keystroke crosses the threshold from browsing a menu to initiating a war simulation."
            }
        ]
    },
    {
        "id": "wg_falken_search",
        "source": "wargames",
        "type": "episodic",
        "title": "Tracing Stephen W. Falken & 'Joshua'",
        "claim": "Separate chronological episodes of David's investigation — library microfiche research (Strand A), newspaper obituary discovery (Strand B), and testing the backdoor password 'JOSHUA' at the terminal (Strand C) — are compressed into a progression where each brief phase yields the clue that unlocks the next.",
        "rival": "Ordinary sequence compresses a single continuous action by dropping dead time; here distinct investigative episodes across different hours/places are chained as stages of one epistemic quest.",
        "limit": "Selects the culminating research-to-password transition (34:05.0–34:45.0) where Falken's family history yields the 'JOSHUA' logon.",
        "question": "Does reversing the investigative stages break the deduction that turns a dead child's name into a military backdoor password?",
        "operation": "reverse",
        "start": 2045.0,
        "end": 2085.0,
        "relationKind": "episodic progression",
        "blocks": [
            {
                "id": "fs1", "start": 2045.0, "end": 2055.0, "strand": "A",
                "label": "Clues assembled from Falken's life and papers",
                "sign": "22",
                "signEvidence": "Biographical fragments hang together as a riddle: what single word did Falken leave in the system?"
            },
            {
                "id": "fs2", "start": 2055.0, "end": 2065.0, "strand": "B",
                "label": "Deduction of the son's name: JOSHUA",
                "sign": "29",
                "signEvidence": "The memory of Falken's dead son permeates the present investigation as the key to the machine's identity."
            },
            {
                "id": "fs3", "start": 2065.0, "end": 2075.0, "strand": "C",
                "label": "Typing 'JOSHUA' at the LOGON prompt",
                "sign": "12",
                "signEvidence": "The deduced name is tested directly on the keyboard to force the locked mainframe open."
            },
            {
                "id": "fs4", "start": 2075.0, "end": 2085.0, "strand": "C",
                "label": "GREETINGS PROFESSOR FALKEN · SHALL WE PLAY A GAME?",
                "sign": "34b",
                "signEvidence": "The metallic Votrax voice speaking to a dead man creates a pure acoustic situation that arrests the room."
            }
        ]
    },
    {
        "id": "wg_norad_escape",
        "source": "wargames",
        "type": "ordinary",
        "title": "Escaping the NORAD infirmary lockup",
        "claim": "A single linear escape action is told chronologically with small temporal ellipses that skip the waiting intervals: David inspects the electronic door lock (Strand A), records the keypad tones on a micro-cassette (Strand B), rigs the wire contact, and slips into the Cheyenne Mountain tour corridor (Strand C).",
        "rival": "Scene would hold real duration without ellipsis; here the cuts trim away the repetitive mechanics of the escape while preserving strict chronological order.",
        "limit": "Covers the infirmary lock-mechanism bypass and door release (63:35.0–64:15.0).",
        "question": "If you shuffle or reverse these blocks, does the mechanical cause-and-effect of bypassing the lock still read as one action?",
        "operation": "reverse",
        "start": 3815.0,
        "end": 3855.0,
        "relationKind": "action with omission",
        "blocks": [
            {
                "id": "ne1", "start": 3815.0, "end": 3825.0, "strand": "A",
                "label": "Alone in the locked NORAD infirmary",
                "sign": "10",
                "signEvidence": "Medical cabinets, tape recorder, and sealed steel door define a tactical problem-space."
            },
            {
                "id": "ne2", "start": 3825.0, "end": 3835.0, "strand": "B",
                "label": "Using the tape recorder & metal probe at the latch",
                "sign": "12",
                "signEvidence": "Improvised small-form action adapts everyday objects to defeat a military security lock."
            },
            {
                "id": "ne3", "start": 3835.0, "end": 3845.0, "strand": "B",
                "label": "Latch clicks open; David checks the corridor",
                "sign": "11",
                "signEvidence": "The mechanical click and cracked doorway serve as the index of a breached perimeter."
            },
            {
                "id": "ne4", "start": 3845.0, "end": 3855.0, "strand": "C",
                "label": "Blending into the civilian Cheyenne Mountain tour",
                "sign": "19",
                "signEvidence": "The fugitive escapes the high-security fortress by hiding in plain sight among sightseers."
            }
        ]
    },
    {
        "id": "wg_cpe_scenarios",
        "source": "wargames",
        "type": "bracket",
        "title": "WOPR's nuclear war scenario cascade · WINNER: NONE",
        "claim": "At the climax, WOPR cycles through scores of named nuclear war plans — 'U.S. FIRST STRIKE', 'USSR FIRST STRIKE', 'NATO / WARSAW PACT', 'FAR EAST STRATEGY' — as equivalent instances of a single concept: every possible nuclear exchange ends in mutual annihilation ('WINNER: NONE'). Chronology between the individual scenarios does not exist; they are samples from a combinatorial set.",
        "rival": "Episodic sequence would imply that Scenario 1 causes Scenario 2 in story time. Instead, each scenario resets the map to zero and repeats the same test under a new strategic title.",
        "limit": "Covers the 40-second high-speed simulation montage before WOPR returns to Tic-Tac-Toe comprehension (104:40.0–105:20.0).",
        "question": "Because a bracket syntagma groups equivalent examples without chronological causality, does grouping or shuffling the map bursts preserve the 'WINNER: NONE' concept?",
        "operation": "group",
        "start": 6280.0,
        "end": 6320.0,
        "relationKind": "typical example",
        "blocks": [
            {
                "id": "cs1", "start": 6280.0, "end": 6288.0, "strand": "A",
                "label": "STRATEGY: U.S. FIRST STRIKE · WINNER: NONE",
                "sign": "3",
                "signEvidence": "Rapid-fire vector arcs and flash-white detonation rings reduce the planet to acentred light."
            },
            {
                "id": "cs2", "start": 6288.0, "end": 6296.0, "strand": "B",
                "label": "War Room faces frozen in the stroboscopic glare",
                "sign": "34a",
                "signEvidence": "Generals and technicians become pure seers unable to intervene in the machine's optical storm."
            },
            {
                "id": "cs3", "start": 6296.0, "end": 6304.0, "strand": "A",
                "label": "USSR FIRST STRIKE / NATO / FAR EAST · WINNER: NONE",
                "sign": "40",
                "signEvidence": "Exhaustive serial iteration ungrounds the military claim that any winning nuclear strategy exists."
            },
            {
                "id": "cs4", "start": 6304.0, "end": 6312.0, "strand": "C",
                "label": "43",
                "sign": "43",
                "label": "Global Mercator screen saturated by zero-sum flashes",
                "signEvidence": "The giant screen functions directly as a cerebral space thinking through self-extinction."
            },
            {
                "id": "cs5", "start": 6312.0, "end": 6320.0, "strand": "B",
                "label": "The simulation halts: 'A STRANGE GAME'",
                "sign": "44",
                "signEvidence": "Audio-visual synthesis requires reading the entire bracket of failed wars against the lesson of Tic-Tac-Toe."
            }
        ]
    }
]


def main():
    data = json.load(open(EX_PATH))
    print("Loaded examples.json with", len(data["examples"]), "examples.")

    # Add wargames source metadata
    data["sources"]["wargames"] = {
        "title": "WarGames",
        "year": 1983,
        "creator": "John Badham / Lawrence Lasker & Walter F. Parkes",
        "url": "../wargames-periodic-table.html",
        "download": "../WAR GAMES/WarGames_1983_H264.mp4",
        "sound": "Original stereo soundtrack retained; full-film Whisper ASR (1,930 segments) and 43-page screenplay aligned.",
        "archive": "wargames.html",
        "fileSha256": "ee649c6fc3bc4ab27e20c7f22e9d63f18c78a7c7684b53578a5d8e5f143a241b"
    }

    # Keep the original 6 examples intact (telephone MUST remain index 0 for model.test.mjs)
    orig_examples = [ex for ex in data["examples"] if ex.get("source") != "wargames"]
    assert orig_examples[0]["id"] == "telephone", "First example must be telephone!"

    wg_examples = []
    for spec in SPECIMENS:
        sid = spec["id"]
        mp4_path = os.path.join(MEDIA_DIR, f"{sid}.mp4")
        jpg_path = os.path.join(MEDIA_DIR, f"{sid}.jpg")
        dur = round(spec["end"] - spec["start"], 3)

        if not os.path.exists(mp4_path) or os.path.getsize(mp4_path) < 10000:
            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{spec['start']:.3f}",
                "-i", VIDEO,
                "-t", f"{dur:.3f}",
                "-vf", "scale=-2:480",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                mp4_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        mid_t = spec["start"] + dur * 0.45
        if not os.path.exists(jpg_path) or os.path.getsize(jpg_path) < 1000:
            cmd_jpg = [
                "ffmpeg", "-y",
                "-ss", f"{mid_t:.3f}",
                "-i", VIDEO,
                "-frames:v", "1",
                "-vf", "scale=640:-2",
                "-q:v", "3",
                jpg_path
            ]
            subprocess.run(cmd_jpg, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        blocks = []
        for b in spec["blocks"]:
            blocks.append({
                "id": b["id"],
                "start": b["start"],
                "end": b["end"],
                "strand": b["strand"],
                "label": b["label"],
                "sign": b["sign"],
                "signEvidence": b["signEvidence"],
                "unit": "shot"
            })

        relations = []
        for i in range(len(blocks) - 1):
            relations.append({
                "left": blocks[i]["id"],
                "right": blocks[i + 1]["id"],
                "kind": spec["relationKind"],
                "evidence": spec["claim"]
            })

        wg_examples.append({
            "id": sid,
            "source": "wargames",
            "type": spec["type"],
            "title": spec["title"],
            "claim": spec["claim"],
            "rival": spec["rival"],
            "limit": spec["limit"],
            "question": spec["question"],
            "operation": spec["operation"],
            "blocks": blocks,
            "start": spec["start"],
            "end": spec["end"],
            "readingStatus": "editorial working reading",
            "reader": "Cineosis WarGames Archive · 2026-10-14",
            "inspection": "Full 6,764s master file segmented into 1,464 SBD shots + 302 curated shots; contact sheets, Whisper ASR, and 43-page script aligned.",
            "media": f"syntagm/operative/media/{sid}.mp4",
            "poster": f"syntagm/operative/media/{sid}.jpg",
            "relations": relations,
            "mediaSha256": sha256_file(mp4_path)
        })
        print(f"  Built operative specimen {sid} ({spec['type']}) -> {dur:.1f}s, {len(blocks)} blocks")

    data["examples"] = orig_examples + wg_examples
    with open(EX_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data['examples'])} total operative examples to {EX_PATH}")


if __name__ == "__main__":
    main()
