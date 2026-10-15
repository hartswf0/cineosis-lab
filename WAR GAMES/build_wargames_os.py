#!/usr/bin/env python3
"""
Build 'WOPR // SYSTEM-83' Inferred Operating System Catalog (cineosis-lab/WAR GAMES/wargames_os.json)
Powered by verified_screens.json (109 contrastive LAION CLIP ViT-B/32 verified screen & game shots
with cropped screen-only images in lab/thumbs/screens/<id>.jpg — zero non-screen false positives).
Also includes the complete catalog of every game shown on screen, listed on WOPR, or spoken in WarGames.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

SUBSYSTEM_DEFS = [
    {
        "id": "ROM://ARCADE",
        "code": "SYS-01",
        "short": "ARCADE.ROM",
        "title": "Galaga & Harbor Arcade Vector/Raster ROMs",
        "node": "HARBOR GAMES · SEATTLE WA",
        "hardware": "Namco Galaga Z80 Triple-CPU Cabinet · Bally Midway Tron · Nintendo Donkey Kong / Mario Bros.",
        "baud": "60 Hz RGB Raster CRT",
        "color": "#ff5c4d",
        "categories": ["arcade_game"],
        "scenes": ["S03"],
        "cmd": "RUN GALAGA",
        "prompt": "ARCADE/ROM> INSERT COIN [1 PLAYER]",
        "summary": "Coin-op arcade cabinets at Harbor Games (Galaga, Tron, Donkey Kong/Mario Bros.) where David Lightman's somatic joystick reflexes prefigure NORAD's strategic war-room screens.",
        "terminal_lines": [
            "NAMCO GALAGA ROM v1981 · TRIPLE Z80 BUS OK",
            "1UP: 048210   HIGH SCORE: 124900 (D. LIGHTMAN)",
            "CABINETS PRESENT: GALAGA (PLAYED) · TRON · DONKEY KONG · MARIO BROS.",
            "SINE-SIGN #23: IMPULSE-IMAGE → TACTILE REFLEX LOOP",
        ],
        "io_schema": {
            "input": "8-Way Sanwa Joystick + Rapid-Fire Button",
            "output": "224×288 RGB CRT Sprite Field + 3-Channel WSG Sound",
            "auth": "25¢ Token / High-Score Initials [DWL]",
        },
    },
    {
        "id": "SYS://IMSAI-8080",
        "code": "SYS-02",
        "short": "IMSAI.SYS",
        "title": "IMSAI 8080 CP/M Workstation & CRT Prompts",
        "node": "LIGHTMAN BEDROOM · SEATTLE (206-555-4821)",
        "hardware": "IMSAI 8080 S-100 Bus · Dual CalComp 8\" Floppy · Electrohome 19\" CRT · Cermetek 212A Acoustic Coupler",
        "baud": "300 / 1200 Baud Bell 103",
        "color": "#4af6c3",
        "categories": ["crt_terminal"],
        "scenes": ["S04", "S05", "S06", "S08", "S09", "S11"],
        "cmd": "MOUNT IMSAI",
        "prompt": "A0:CP/M-80> STAT DEV:",
        "summary": "David's bedroom S-100 microcomputer with red/blue toggle paddles, dual 8-inch floppy drives, and 19-inch monochrome monitor displaying uppercase terminal prompts.",
        "terminal_lines": [
            "64K CP/M VERS. 2.2 (IMSAI 8080 S-100 BIOS v3.4)",
            "A: DRIVE READY [8-INCH SINGLE DENSITY · 256KB]",
            "MODEM PORT: 02F8H · ACOUSTIC COUPLER CARRIER DETECTED",
            "CON:=CRT   RDR:=MODEM   PUN:=MODEM   LST:=DIABLO-1620",
        ],
        "io_schema": {
            "input": "ASCII Mechanical Keyboard + S-100 Front-Panel Address Switches",
            "output": "80×24 Phosphor Character Matrix + Daisy-Wheel Paper Printout",
            "auth": "Local Physical Boot Floppy (CP/M System Disk)",
        },
    },
    {
        "id": "NET://WARDIALER",
        "code": "SYS-03",
        "short": "WARDIAL.NET",
        "title": "Sunnyvale 408-311-xxxx Auto-Dialer & Carrier Matrix",
        "node": "BELL SYSTEM PSTN · SUNNYVALE CA (AREA 408)",
        "hardware": "IMSAI Auto-Dialer Script · Bell 103 Carrier Tone Detector",
        "baud": "300 Baud FSK (1070/1270 Hz)",
        "color": "#f6c14a",
        "categories": ["wardialer_modem", "crt_terminal"],
        "scenes": ["S05", "S06", "S14"],
        "cmd": "DIAL 408-311",
        "prompt": "WARDIAL> SCAN 408-311-0001..9999",
        "summary": "Four-column telephone number matrix sweeping every number in Sunnyvale, California (408-311-xxxx) and highlighting numbers that answer with a modem carrier tone.",
        "terminal_lines": [
            "TARGET EXCHANGE: (408) 311-0001 TO (408) 311-9999 [SUNNYVALE, CA]",
            "311-0041   311-0042   311-0043   [311-0318 CARRIER]",
            "311-0762   311-0763   [311-0764 PAN AM]   311-0765",
            "311-3988   311-3989   [311-3990 WOPR HOST — LOGON PLEASE]",
        ],
        "io_schema": {
            "input": "Prefix Table (408-311-XXXX) + Off-Hook Relay Timer",
            "output": "4-Column CRT Dialing Matrix + Disk Log of Carrier Nodes",
            "auth": "Unauthenticated PSTN Tone Sweep + Payphone Pull-Tab Phreak",
        },
    },
    {
        "id": "EDU://SEATTLE-SCHOOLS",
        "code": "SYS-04",
        "short": "GRADES.EDU",
        "title": "Seattle Public Schools Central Grade Database",
        "node": "SEATTLE SCHOOL DISTRICT ADMIN MAINFRAME",
        "hardware": "DEC PDP-11/70 Timesharing Host · Student Records DB",
        "baud": "300 Baud Remote Terminal",
        "color": "#5ad2ff",
        "categories": ["crt_terminal"],
        "scenes": ["S04"],
        "cmd": "GRADE LIGHTMAN A",
        "prompt": "SEATTLE-SCHOOLS> ENTER ADMIN PASSWORD: PENCIL",
        "summary": "District academic record CRT accessed via Mr. Liggett's desk-drawer password ('PENCIL') to mutate David Lightman's and Jennifer Mack's Biology grades from F/C to A.",
        "terminal_lines": [
            "SEATTLE PUBLIC SCHOOLS — STUDENT COURSE RECORD",
            "AUTH PASSWORD ACCEPTED: PENCIL [USER: LIGGETT, R. · BIOLOGY 204]",
            "STUDENT: LIGHTMAN, DAVID L.  |  COURSE: BIO-204  |  OLD: F  →  NEW: A",
            "STUDENT: MACK, JENNIFER K.   |  COURSE: BIO-204  |  OLD: C  →  NEW: A",
        ],
        "io_schema": {
            "input": "Student Name + Course ID + Grade Override",
            "output": "Formatted CRT Grade Table",
            "auth": "Bi-weekly cleartext password: PENCIL",
        },
    },
    {
        "id": "AIR://PAN-AM",
        "code": "SYS-05",
        "short": "PANAM.AIR",
        "title": "Pan Am PANAMAC Flight 114 Paris Reservation Screen",
        "node": "PAN AMERICAN WORLD AIRWAYS · SEATTLE / PARIS",
        "hardware": "IBM 3033 Airline Reservation Mainframe (PANAMAC II)",
        "baud": "1200 Baud Dial-Up Agency Port",
        "color": "#7ea8ff",
        "categories": ["crt_terminal"],
        "scenes": ["S06", "S12"],
        "cmd": "BOOK PARIS 114",
        "prompt": "PANAMAC> SELL 2 F SEA-CDG FLT 114",
        "summary": "Commercial airline booking CRT screen where David reserves two first-class seats to Paris on Flight 114—later displayed on McKittrick's FBI interrogation screen.",
        "terminal_lines": [
            "PAN AMERICAN WORLD AIRWAYS — RESERVATION SYSTEM",
            "FLT 114 · SEATTLE (SEA) → PARIS ORLY (ORY) · DEPART 18 AUG 08:30",
            "PASSENGER 1: LIGHTMAN / DAVID MR   [CLASS F · CONFIRMED]",
            "PASSENGER 2: MACK / JENNIFER MS    [CLASS F · CONFIRMED]",
        ],
        "io_schema": {
            "input": "City Pair + Flight Number + Passenger Names",
            "output": "PNR Itinerary Screen",
            "auth": "Travel Agency Dial-Up Node (408-311-0764)",
        },
    },
    {
        "id": "DOC://MICROFICHE-ARPA",
        "code": "SYS-06",
        "short": "FALKEN.DOC",
        "title": "Optical Microfiche Reader & Falken Obituary Dossier",
        "node": "LIBRARY MICROFICHE STATION / ARPA BIOGRAPHICAL INDEX",
        "hardware": "Bell & Howell Optical Microfiche Projection Screen",
        "baud": "Optical Film Index + 300 Baud Query",
        "color": "#e8c070",
        "categories": ["microfiche_dossier", "crt_terminal"],
        "scenes": ["S07", "S08"],
        "cmd": "WHOIS FALKEN",
        "prompt": "ARCHIVE/DOC> QUERY 'FALKEN, STEPHEN W.'",
        "summary": "Backlit microfiche reader screen displaying Stephen W. Falken's 1973 obituary, his treatise 'Poker and Armageddon', and the name of his son, Joshua.",
        "terminal_lines": [
            "SUBJECT: FALKEN, STEPHEN W. (BORN 1941 — REPORTED DECEASED 1973)",
            "PAPER: 'POKER AND ARMAGEDDON: THE ROLE OF BLUFFING IN A NUCLEAR STANDOFF'",
            "FAMILY RECORD: WIFE & SON (JOSHUA FALKEN) KILLED IN AUTO ACCIDENT, 1972",
            "INFERRED BACKDOOR CREDENTIAL → 'JOSHUA'",
        ],
        "io_schema": {
            "input": "Author Surname + Obituary Microfilm Reel #73-11",
            "output": "Backdoor Password Discovery: JOSHUA",
            "auth": "Public Library Microfiche + Trapdoor Password Convention",
        },
    },
    {
        "id": "AI://JOSHUA-SHELL",
        "code": "SYS-07",
        "short": "JOSHUA.AI",
        "title": "WOPR Backdoor Dialogue Screen & `LIST GAMES` Menu",
        "node": "CHEYENNE MOUNTAIN · SUNNYVALE AI PORT (408-311-3990)",
        "hardware": "WOPR Heuristic Command Processor + Votrax Type-'N-Talk Formant Synth",
        "baud": "300 Baud Full-Duplex + Formant Voice Out",
        "color": "#4af6c3",
        "categories": ["crt_terminal"],
        "scenes": ["S06", "S08", "S09", "S11", "S13", "S21"],
        "cmd": "LOGON JOSHUA",
        "prompt": "LOGON: JOSHUA",
        "summary": "Stephen Falken's heuristic backdoor CRT prompt inside the WOPR, displaying `LIST GAMES`, `SHALL WE PLAY A GAME?`, and `WHAT'S THE DIFFERENCE?`.",
        "terminal_lines": [
            "LOGON: JOSHUA",
            "GREETINGS PROFESSOR FALKEN. HELLO. SHALL WE PLAY A GAME?",
            "LIST GAMES: FALKEN'S MAZE, BLACK JACK, GIN RUMMY, HEARTS, BRIDGE, CHECKERS, CHESS, POKER, FIGHTER COMBAT, GUERRILLA ENGAGEMENT, DESERT WARFARE, AIR-TO-GROUND ACTIONS, THEATREWIDE TACTICAL WARFARE, THEATREWIDE BIOTOXIC AND CHEMICAL WARFARE, GLOBAL THERMONUCLEAR WAR.",
            "> IS THIS A GAME, OR IS IT REAL?   →   WHAT'S THE DIFFERENCE?",
        ],
        "io_schema": {
            "input": "Natural-Language Uppercase Prompt + Game Selection",
            "output": "CRT Uppercase Response + Votrax Formant Speech Synthesis",
            "auth": "Trapdoor Password: JOSHUA (Left by S. W. Falken)",
        },
    },
    {
        "id": "SIM://GTW-VECTORS",
        "code": "SYS-08",
        "short": "GTW.SIM",
        "title": "Global Thermonuclear War Vector Trajectory Screens",
        "node": "WOPR SIMULATION CORE · NORAD WAR ROOM BIG BOARD",
        "hardware": "WOPR Vector Graphics Generator · Polar Mercator Projection Grid",
        "baud": "High-Speed Internal Bus (DMA to Big Board)",
        "color": "#ff5c4d",
        "categories": ["vector_war_map"],
        "scenes": ["S09", "S10", "S17", "S18"],
        "cmd": "RUN GTW",
        "prompt": "GTW> SELECT PRIMARY TARGETS [SOVIET FIRST STRIKE]",
        "summary": "Glowing cyan, amber, and red vector projection screens plotting parabolic ICBM and submarine-launched missile trajectories across North America and the pole.",
        "terminal_lines": [
            "GAME SELECTED: GLOBAL THERMONUCLEAR WAR",
            "WHICH SIDE DO YOU WANT?  1. UNITED STATES   2. SOVIET UNION  → [2]",
            "PRIMARY TARGETS: LAS VEGAS, NEVADA  |  SEATTLE, WASHINGTON",
            "VECTOR PROJECTION: 72 ICBM + 24 SLBM ARCS ON NORAD MAIN BOARD",
        ],
        "io_schema": {
            "input": "Side Selection (US/USSR) + City/Military Target Coordinates",
            "output": "Parabolic Ballistic Vector Arcs + Impact Rings",
            "auth": "JOSHUA Session Escalation",
        },
    },
    {
        "id": "C3I://DEFCON-PALACE",
        "code": "SYS-09",
        "short": "DEFCON.C3I",
        "title": "NORAD Crystal Palace Telemetry, Clocks & DEFCON Readouts",
        "node": "CHEYENNE MOUNTAIN COMPLEX · COLORADO SPRINGS",
        "hardware": "12 Overhead Rear-Projection Screens + DEFCON 5..1 Neon Matrix + Game Elapsed Clocks",
        "baud": "AUTOVON / SAC Encrypted C3I Multiplex",
        "color": "#ff9e3b",
        "categories": ["defcon_readout"],
        "scenes": ["S01", "S02", "S10", "S11", "S17", "S18"],
        "cmd": "STATUS DEFCON",
        "prompt": "NORAD/C3I> QUERY DEFCON & GAME CLOCK",
        "summary": "Digital countdown clocks (`GAME TIME ELAPSED / ESTIMATED TIME REMAINING`), DEFCON 5→1 neon signs, and SAC base status tables inside Cheyenne Mountain.",
        "terminal_lines": [
            "DEFCON STATUS: 5 → 4 → 3 → 2 → 1 (MAXIMUM FORCE READINESS)",
            "GAME TIME ELAPSED: 31 HRS 12 MIN · ESTIMATED TIME REMAINING: 52 HRS 17 MIN",
            "BMEWS CLEAR / THULE: 340 INBOUND TRACKS · SAC BOMBER WINGS: LAUNCHED",
            "LORING AFB / ELMENDORF / GRAND FORKS: TELEMETRY VERIFICATION",
        ],
        "io_schema": {
            "input": "BMEWS Radar + DSP Satellites + WOPR Simulation Clock",
            "output": "12 Overhead Projection Boards + LED Countdown Readouts",
            "auth": "Two-Man Command Authority (General Beringer / SAC)",
        },
    },
    {
        "id": "KEY://CPE-CRACKER",
        "code": "SYS-10",
        "short": "CPE-TTT.KEY",
        "title": "CPE 1704 TKS Launch-Code Lock & 0-Player Tic-Tac-Toe Screens",
        "node": "WOPR LAUNCH RELAY BUS · MINUTEMAN III SILO WINGS",
        "hardware": "WOPR Permutation Register + Tic-Tac-Toe Vector Grid + Scenario Cascade Matrix",
        "baud": "Core Overload (100% Mountain Power Draw)",
        "color": "#ffffff",
        "categories": ["tictactoe_scenarios", "defcon_readout"],
        "scenes": ["S16", "S19", "S20", "S21"],
        "cmd": "PLAY TICTACTOE 0",
        "prompt": "WOPR/KERNEL> TIC-TAC-TOE -PLAYERS 0",
        "summary": "The climax screens: WOPR locking the 10-character nuclear launch code (`CPE 1704 TKS`), the glowing 3×3 Tic-Tac-Toe grid set to `0 PLAYERS`, and the rapid cascade of 200+ nuclear war scenarios all flashing `WINNER: NONE`.",
        "terminal_lines": [
            "LAUNCH CODE PERMUTATION LOCK: [C] [P] [E] [1] [7] [0] [4] [T] [K] [S]",
            "INTERRUPT: GAME SELECTED — TIC-TAC-TOE — NUMBER OF PLAYERS: 0",
            "STALEMATE. STALEMATE. STALEMATE. ESCALATING TO GLOBAL SCENARIO MATRIX...",
            "U.S. FIRST STRIKE: WINNER: NONE  |  NATO INCURSION: WINNER: NONE",
            "A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY. HOW ABOUT A NICE GAME OF CHESS?",
        ],
        "io_schema": {
            "input": "0-Player Self-Play Loop (Tic-Tac-Toe → Global Scenario Exhaustion)",
            "output": "Aborted Launch Sequence + 'WINNER: NONE' Epistemological Discovery",
            "auth": "Direct Console Terminal in NORAD War Room",
        },
    },
]

# Complete taxonomy of EVERY game shown on screen, listed on WOPR, or spoken in WarGames (1983)
ALL_GAMES_TAXONOMY = [
    # I. Coin-Op Arcade Games (Shown/Heard in Scene S03 Harbor Arcade)
    {"id": "galaga", "name": "GALAGA (Namco, 1981)", "tier": "1. Coin-Op Arcade (Shown on Screen)", "status": "PLAYED ON SCREEN", "where": "Scene S03 · Harbor Arcade (David Lightman high score)", "type": "Fixed Shooter / Reflex Loop", "cmd": "RUN GALAGA"},
    {"id": "tron", "name": "TRON (Bally Midway, 1982)", "tier": "1. Coin-Op Arcade (Shown on Screen)", "status": "CABINET IN ARCADE", "where": "Scene S03 · Harbor Arcade background cabinet", "type": "Grid Action / Light Cycles", "cmd": "RUN GALAGA"},
    {"id": "donkey_kong", "name": "DONKEY KONG / MARIO BROS. (Nintendo)", "tier": "1. Coin-Op Arcade (Shown on Screen)", "status": "CABINET & AUDIO", "where": "Scene S03 · Harbor Arcade cabinet & soundscape", "type": "Platformer", "cmd": "RUN GALAGA"},

    # II. Abstract / Parlor Strategy Games (Listed on WOPR 'LIST GAMES' & Spoken by Falken/David)
    {"id": "falkens_maze", "name": "FALKEN'S MAZE", "tier": "2. Heuristic & Parlor Games (WOPR List #1)", "status": "LISTED & SPOKEN", "where": "Scene S06/S07 · 1st entry in WOPR `LIST GAMES`; Malvin says 'Go right through Falken's Maze'", "type": "Heuristic Pathfinding / Learning", "cmd": "LOGON JOSHUA"},
    {"id": "black_jack", "name": "BLACK JACK", "tier": "2. Heuristic & Parlor Games (WOPR List #2)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 2nd entry in WOPR `LIST GAMES`", "type": "Stochastic Card / Risk", "cmd": "LOGON JOSHUA"},
    {"id": "gin_rummy", "name": "GIN RUMMY", "tier": "2. Heuristic & Parlor Games (WOPR List #3)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 3rd entry in WOPR `LIST GAMES`", "type": "Imperfect-Info Card", "cmd": "LOGON JOSHUA"},
    {"id": "hearts", "name": "HEARTS", "tier": "2. Heuristic & Parlor Games (WOPR List #4)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 4th entry in WOPR `LIST GAMES`", "type": "Multi-Agent Penalty Avoidance", "cmd": "LOGON JOSHUA"},
    {"id": "bridge", "name": "BRIDGE", "tier": "2. Heuristic & Parlor Games (WOPR List #5)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 5th entry in WOPR `LIST GAMES`", "type": "Partnership Signaling & Bidding", "cmd": "LOGON JOSHUA"},
    {"id": "checkers", "name": "CHECKERS", "tier": "2. Heuristic & Parlor Games (WOPR List #6)", "status": "LISTED & SPOKEN", "where": "Scene S06/S07 · WOPR `LIST GAMES` + David asks 'Why does it have games like checkers and backgammon?'", "type": "Complete-Info Zero-Sum Tree", "cmd": "LOGON JOSHUA"},
    {"id": "chess", "name": "CHESS", "tier": "2. Heuristic & Parlor Games (WOPR List #7)", "status": "PROPOSED BY JOSHUA TWICE", "where": "Scene S06, S09 ('Wouldn't you prefer a good game of chess?'), S21 ('How about a nice game of chess?')", "type": "Complete-Info Strategic Tree", "cmd": "PLAY TICTACTOE 0"},
    {"id": "poker", "name": "POKER", "tier": "2. Heuristic & Parlor Games (WOPR List #8)", "status": "LISTED & THEORIZED", "where": "Scene S06/S08 · WOPR `LIST GAMES` + Falken's paper 'Poker and Armageddon: The Role of Bluffing in a Nuclear Standoff'", "type": "Deception / Deterrence Bluffing", "cmd": "WHOIS FALKEN"},
    {"id": "backgammon", "name": "BACKGAMMON", "tier": "2. Heuristic & Parlor Games (Spoken in Dialogue)", "status": "SPOKEN BY DAVID", "where": "Scene S07 · David asks Jim & Malvin: 'If it's military, why does it have games like checkers and backgammon?'", "type": "Probabilistic Bearing-Off Strategy", "cmd": "LOGON JOSHUA"},
    {"id": "tic_tac_toe", "name": "TIC-TAC-TOE (0-PLAYER OVERRIDE)", "tier": "2. Heuristic & Parlor Games (Played on Screen)", "status": "PLAYED ON SCREEN (S16 & S20)", "where": "Scene S16 (Falken's chalkboard lesson) & Scene S20 (NORAD console 0-player stalemate loop that stops World War III)", "type": "Solved Futility / Stalemate Proof", "cmd": "PLAY TICTACTOE 0"},

    # III. Conventional & Theater Military Simulations (WOPR 'LIST GAMES' #9–#14)
    {"id": "fighter_combat", "name": "FIGHTER COMBAT", "tier": "3. Tactical & Theater War Simulations (WOPR #9)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 9th entry in WOPR `LIST GAMES` (transition from parlor games to military war games)", "type": "Air-to-Air Dogfight Model", "cmd": "LOGON JOSHUA"},
    {"id": "guerrilla_engagement", "name": "GUERRILLA ENGAGEMENT", "tier": "3. Tactical & Theater War Simulations (WOPR #10)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 10th entry in WOPR `LIST GAMES`", "type": "Asymmetric Counter-Insurgency", "cmd": "LOGON JOSHUA"},
    {"id": "desert_warfare", "name": "DESERT WARFARE", "tier": "3. Tactical & Theater War Simulations (WOPR #11)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 11th entry in WOPR `LIST GAMES`", "type": "Armored Maneuver Simulation", "cmd": "LOGON JOSHUA"},
    {"id": "air_to_ground", "name": "AIR-TO-GROUND ACTIONS", "tier": "3. Tactical & Theater War Simulations (WOPR #12)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 12th entry in WOPR `LIST GAMES`", "type": "Strike Interdiction", "cmd": "LOGON JOSHUA"},
    {"id": "theatrewide_tactical", "name": "THEATREWIDE TACTICAL WARFARE", "tier": "3. Tactical & Theater War Simulations (WOPR #13)", "status": "LISTED ON SCREEN", "where": "Scene S06 · 13th entry in WOPR `LIST GAMES`", "type": "Combined-Arms Theater", "cmd": "LOGON JOSHUA"},
    {"id": "biotoxic_chemical", "name": "THEATREWIDE BIOTOXIC AND CHEMICAL WARFARE", "tier": "3. Tactical & Theater War Simulations (WOPR #14)", "status": "LISTED & SPOKEN", "where": "Scene S06/S07 · 14th entry in WOPR `LIST GAMES` (read aloud by David to Jim & Malvin)", "type": "CBRN Escalation Simulation", "cmd": "LOGON JOSHUA"},

    # IV. Strategic Nuclear War & SIOP Endgame Scenarios (Played on Screen S09–S20)
    {"id": "gtw", "name": "GLOBAL THERMONUCLEAR WAR", "tier": "4. Strategic Nuclear Exchange (WOPR #15 · Played)", "status": "PLAYED ON SCREEN (S09–S20)", "where": "Scene S06, S09–S20 · Selected by David ('Las Vegas / Seattle'), driving NORAD to DEFCON 1", "type": "Full SIOP Nuclear Exchange", "cmd": "RUN GTW"},
    {"id": "siop_scenarios", "name": "200+ SIOP NUCLEAR SCENARIOS ('WINNER: NONE')", "tier": "4. Strategic Nuclear Exchange (Played in S20)", "status": "PLAYED ON SCREEN (S20)", "where": "Scene S20 · US First Strike, USSR First Strike, NATO/Warsaw Pact, Far East Strategy, Cuban Provocation, SEATO Decapitation, Hong Kong Variant, Turkish Decoy...", "type": "Exhaustive Monte Carlo War Plan Cascade", "cmd": "PLAY TICTACTOE 0"},
]


def main():
    vdata = json.load(open(os.path.join(HERE, "verified_screens.json")))
    vscreens = vdata["screens"]

    subsystems_out = []
    for sub in SUBSYSTEM_DEFS:
        cat_set = set(sub["categories"])
        sc_set = set(sub["scenes"])

        # Match ONLY CLIP-verified pure screens
        matched = []
        for s in vscreens:
            in_cat = s["category"] in cat_set
            in_sc = s["scene_id"] in sc_set
            if in_cat and in_sc:
                rank = s["purity"] + 1.5
                matched.append((rank, s))
            elif in_cat:
                rank = s["purity"] + 0.4
                matched.append((rank, s))
            elif in_sc and s["purity"] >= 0.48:
                rank = s["purity"]
                matched.append((rank, s))

        matched.sort(key=lambda x: (-x[0], x[1]["start"]))
        curated_shots = [m[1] for m in matched if m[1]["source_type"] == "curated"]
        sbd_shots = [m[1] for m in matched if m[1]["source_type"] == "sbd"]
        all_sub_shots = [m[1] for m in matched]

        sub_copy = dict(sub)
        sub_copy["shots"] = all_sub_shots[:24]
        sub_copy["lead_thumb"] = all_sub_shots[0]["screen_thumb"] if all_sub_shots else "thumbs/wg_001.jpg"
        sub_copy["sbd_screen_cuts"] = sbd_shots
        sub_copy["sbd_count"] = len(sbd_shots)
        subsystems_out.append(sub_copy)

    out = {
        "os_name": "WOPR // SYSTEM-83",
        "version": "CLIP-VERIFIED PURE SCREEN & GAME ATLAS v2.0",
        "subtitle": "Every verified computer screen, arcade game, terminal prompt, wardialer matrix, radar map, and launch-code lock in WarGames (1983)—cropped to the screen bezel with zero non-screen false positives.",
        "stats": {
            "subsystems": len(subsystems_out),
            "wopr_games": len(ALL_GAMES_TAXONOMY),
            "verified_screen_shots": len(vscreens),
            "curated_screen_shots": sum(1 for x in vscreens if x["source_type"] == "curated"),
            "sbd_screen_cuts": sum(1 for x in vscreens if x["source_type"] == "sbd"),
        },
        "wopr_games": ALL_GAMES_TAXONOMY,
        "all_verified_screens": vscreens,
        "subsystems": subsystems_out,
    }

    out_path = os.path.join(HERE, "wargames_os.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {out_path}: {len(vscreens)} CLIP-verified pure screens across {len(subsystems_out)} subsystems and {len(ALL_GAMES_TAXONOMY)} cataloged games.")


if __name__ == "__main__":
    main()
