#!/usr/bin/env python3
"""
Builds the two fast datasets for the 6-Page Found WarGames Studio Set:
1. cineosis-lab/lab/wargames-screens-program.json
   - All 195 screen/terminal shots (109 cropped verified screen screenshots + 86 curated 8-frame strip shots = 880+ screen states)
   - Complete State-Transition Graph (S_001..S_195) and Inferred Program AST / Executable Code per subsystem and film-wide.
2. cineosis-lab/lab/wargames-studio-cuts.json
   - Fast (~1.8 MB) multi-cut dataset for watching all simultaneous cuts of The Found WarGames across:
     - 02 / JOHN WHITNEY (Harmonic Differential Slit-Scan)
     - 03 / KEN KNOWLTON (Film Made of Stills / Multi-Scale Quadtree Mosaic)
     - 05 / FRIEDER NAKE (5-Column Vertical 35mm Plotter Matrix)
     - 06 / MANFRED MOHR (4D Hypercube Facet Lattice)
     - 10 / CASEY REAS (Organic Vector Flow-Field Tissue Assembly)
"""
import json
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(os.path.dirname(HERE), "lab")

SUBSYSTEM_PROGRAMS = {
    "ROM://ARCADE": {
        "lang": "Z80 ASM / NAMCO WSG ROM",
        "entrypoint": "GALAGA_attract_loop()",
        "inferred_invariant": " reflex_loop(joy_vec, fire_btn) -> sprite_collision_matrix",
        "code": [
            ("0010", "ORG 0x0000 ; GALAGA_ROM_INIT", "Boot 224x288 RGB raster & 3-channel WSG waveform table"),
            ("0020", "LD A, (COIN_SLOT_PORT)", "Wait for 25c token drop or attract-mode demo timer"),
            ("0030", "CALL RENDER_STARFIELD_VRAM", "Scroll 2-layer parallax starfield across CRT scanlines"),
            ("0040", "READ_INPUT: IN A, (JOY_8WAY)", "Sample player stick X/Y & rapid-fire trigger state"),
            ("0050", "CALL BEZIER_DIVE_TRAJECTORY", "Compute alien formation swoop vectors toward bottom row"),
            ("0060", "CP COLLISION_MASK", "Test player dual-torpedo hitbox against diving boss sprite"),
            ("0070", "JP Z, INCREMENT_HI_SCORE_DWL", "Update top-row BCD score register [DWL = David W. Lightman]"),
        ]
    },
    "SYS://IMSAI-8080": {
        "lang": "CP/M 2.2 · 8080 ASM & BASIC",
        "entrypoint": "IMSAI_cold_boot()",
        "inferred_invariant": "s100_bus(tty_in) -> vram_80x24 -> acoustic_modem_tx(212A)",
        "code": [
            ("0100", "BOOT_CPM: LXI SP, 0xFFFF", "Initialize S-100 bus front-panel switches & 64KB RAM bank"),
            ("0110", "CALL FLOPPY_8INCH_SEEK_TRK0", "Mount CP/M system diskette on dual 8-inch drive bay"),
            ("0120", "OUT (CRT_80X24_PORT), '>'", "Render phosphor command prompt on Zenith green/amber monitor"),
            ("0130", "IN A, (CROCKER_MODEM_CARRIER)", "Place handset into acoustic rubber cups; wait for 1200-baud tone"),
            ("0140", "CALL DIAL_REMOTE_HOST", "Transmit DTMF/pulse digits over Sunnyvale/Seattle trunk line"),
            ("0150", "PARSE_BANNER: CMP 'LOGON:'", "Inspect incoming ASCII stream for host authentication prompt"),
            ("0160", "JMP EXEC_USER_OVERRIDE", "Inject cleartext credential or launch automated prefix sweep"),
        ]
    },
    "NET://WARDIALER": {
        "lang": "8080 WARDIALER DAEMON",
        "entrypoint": "wardial_sweep(408, 311, 0000..9999)",
        "inferred_invariant": "for n in 0000..9999: if detect_212A_carrier(n) -> append_nvram(n)",
        "code": [
            ("0200", "DEF_PREFIX: DB '408-311-'", "Lock Sunnyvale California exchange prefix into dialer table"),
            ("0210", "FOR_EXT: LD HL, 0001", "Initialize 4-digit extension counter (0001 -> 9999)"),
            ("0220", "OUT (RELAY_HOOK), OFF_HOOK", "Seize line; pulse-dial 408-311-[HL] across 4-column CRT matrix"),
            ("0230", "WAIT_4S: IN A, (MODEM_CD_PIN)", "Listen 4.0s for 2225 Hz Bell 212A answer carrier tone"),
            ("0240", "JR NZ, NO_CARRIER_DROP", "If human voice or busy signal, drop relay & advance HL+1"),
            ("0250", "RECORD_HIT: CALL INVERT_CELL", "Highlight carrier number in inverse video on 4-column screen"),
            ("0260", "CALL WRITE_FLOPPY_HITLOG", "Persist confirmed modem node (e.g. 408-311-0071 / 0764 / 3990)"),
        ]
    },
    "EDU://SEATTLE-SCHOOLS": {
        "lang": "COBOL / DEC TOPS-20",
        "entrypoint": "STUDENT_GRADE_DB()",
        "inferred_invariant": "auth('PENCIL') -> seek_student(ID) -> mutate_grade('F' -> 'A')",
        "code": [
            ("0300", "PROMPT 'PLEASE ENTER PASSWORD:'", "Display school district dial-up gatekeeper banner"),
            ("0310", "ACCEPT PW_BUF ; IF PW='PENCIL'", "Validate bi-weekly admin password written under desk blotter"),
            ("0320", "SELECT RECORD WHERE COURSE='BIO-2'", "Query Biology 204 roster for LIGHTMAN, DAVID W. / MACK, JENNIFER"),
            ("0330", "DISPLAY_ROW: 'BIOLOGY 2  F'", "Render current failing grade cell with blinking block cursor"),
            ("0340", "ON_KEY_OVERRIDE: MOVE 'A' TO GRADE", "Overwrite character buffer at cursor col 42 ('F' -> 'A' / 'C')"),
            ("0350", "COMMIT_ISAM_RECORD", "Write updated transcript row back to district mainframe disk"),
        ]
    },
    "AIR://PAN-AM": {
        "lang": "IBM PARS / PANAMAC SABRE",
        "entrypoint": "PANAMAC_reserve(SEA, CDG)",
        "inferred_invariant": "query_ leg('SEA->ORD->CDG') -> allocate_pnr('LIGHTMAN/MACK')",
        "code": [
            ("0400", "SIGN_ON NODE '408-311-0764'", "Handshake with travel agency dial-up reservation concentrator"),
            ("0410", "CMD '118AUGSEAPAR'", "Query seat availability Seattle -> Chicago -> Paris Charles de Gaulle"),
            ("0420", "RENDER_FLIGHT_GRID: PA 114 Y", "Display flight segments, departure times, and open coach inventory"),
            ("0430", "SELL 2Y1 ; NAME 'LIGHTMAN/DAVID'", "Reserve 2 seats in Y class for LIGHTMAN/D and MACK/J"),
            ("0440", "GENERATE_PNR_KEY", "Store active passenger name record in Pan Am reservation queue"),
        ]
    },
    "DOC://MICROFICHE-ARPA": {
        "lang": "OPTICAL DOSSIER / BIO-GRAPH",
        "entrypoint": "resolve_backdoor('FALKEN, STEPHEN W.')",
        "inferred_invariant": "biography(Falken) -> extract_child_name('JOSHUA') -> trapdoor_key",
        "code": [
            ("0500", "LOAD_REEL 'ARPA-AI-1973'", "Align optical microfiche lens on Stephen W. Falken publication index"),
            ("0510", "SCAN_PAPER 'POKER & FUTILITY'", "Read game-theory treatise on learning automata & draw states"),
            ("0520", "SEEK_OBITUARY '1973-11-14'", "Inspect newspaper clipping of car crash: wife & son Joshua"),
            ("0530", "INFER_TRAPDOOR: KEY := 'JOSHUA'", "Map personal loss token to undocumented system backdoor password"),
        ]
    },
    "AI://JOSHUA-SHELL": {
        "lang": "WOPR NATURAL-LANGUAGE SHELL",
        "entrypoint": "JOSHUA_backdoor_session()",
        "inferred_invariant": "login('JOSHUA') -> list_games() -> conversational_tts_loop()",
        "code": [
            ("0600", "IF INPUT == 'HELP GAMES'", "Intercept pre-login help query on nameless Sunnyvale node"),
            ("0610", "PRINT 'FALKEN\\'S MAZE, CHESS, GTW'", "Output catalog of 15 strategic & tactical simulation modules"),
            ("0620", "AUTH_TRAPDOOR: IF LOGON=='JOSHUA'", "Bypass standard NORAD cryptographic challenge via Falken backdoor"),
            ("0630", "TTS_SAY 'GREETINGS PROFESSOR FALKEN'", "Drive Votrax formant synthesizer + 80-col uppercase typewriter"),
            ("0640", "PARSE_DIALOGUE(USER_UTTERANCE)", "Match conversational intent ('HOW ARE YOU FEELING TODAY?')"),
            ("0650", "PRINT 'SHALL WE PLAY A GAME?'", "Prompt operator to select a strategic conflict simulation"),
        ]
    },
    "SIM://GTW-VECTORS": {
        "lang": "WOPR WAR-GAME ENGINE (SIOP-62)",
        "entrypoint": "run_GTW(side='USSR', target_list)",
        "inferred_invariant": "select_targets(LAS_VEGAS, SEATTLE) -> inject_false_radar_tracks(NORAD)",
        "code": [
            ("0700", "EXEC_MODULE 'GLOBAL THERMONUCLEAR WAR'", "Load high-resolution North Polar vector map projection"),
            ("0710", "PROMPT 'WHICH SIDE DO YOU WANT?'", "Bind operator to USSR Red Force offensive strike planner"),
            ("0720", "READ_PRIMARY_TARGETS: 'LAS VEGAS, SEATTLE'", "Ingest civilian/military target coordinates from remote modem"),
            ("0730", "COMPUTE_ICBM_PARABOLAS(SS-18)", "Project sub-orbital ballistic arcs across Arctic BMEWS sector"),
            ("0740", "BRIDGE_TO_NORAD_BUS:WRITE_SIM_TRACKS", "Feed simulated telemetry directly into live Cheyenne Mountain radar"),
        ]
    },
    "C3I://DEFCON-PALACE": {
        "lang": "NORAD 427M CRYSTAL PALACE C3I",
        "entrypoint": "NORAD_threat_assessment_loop()",
        "inferred_invariant": "ingest_bmews() -> escalate_defcon(5->1) -> seal_blast_doors()",
        "code": [
            ("0800", "POLL_SENSORS: BMEWS + DSP_SAT", "Read Arctic early-warning radar & infrared launch plumes"),
            ("0810", "UPDATE_BIG_BOARD(12_SCREENS)", "Project incoming submarine & bomber tracks onto War Room wall"),
            ("0820", "ESCALATE_DEFCON: 5 -> 4 -> 3 -> 2 -> 1", "Decrement Defense Readiness Condition lamps & sound klaxon"),
            ("0830", "SYNC_GAME_CLOCK: T_MINUS_IMPACT", "Countdown 23:00 to first warhead detonation; compute survival %"),
            ("0840", "IF DEFCON == 1: SEAL_MOUNTAIN", "Close 25-ton steel blast doors; lock SAC missile wings on standby"),
        ]
    },
    "KEY://CPE-CRACKER": {
        "lang": "WOPR ZERO-PLAYER EXHAUSTION LOOP",
        "entrypoint": "WOPR_crack_launch_code('CPE1704TKS')",
        "inferred_invariant": "brute_force(CPE1704TKS) + tic_tac_toe(players=0) -> WINNER_NONE -> halt()",
        "code": [
            ("0900", "BYPASS_HUMAN_KEY: SEEK 'CPE1704TKS'", "Cycle 10-character alphanumeric launch-code registers at 40 Hz"),
            ("0910", "FOR pos IN 0..9: LOCK_CHAR(pos)", "Latch each verified launch code character into silo fire bus"),
            ("0920", "INTERRUPT: LAUNCH 'TIC-TAC-TOE' (P=0)", "Force WOPR to play 0-player Tic-Tac-Toe against itself"),
            ("0930", "OBSERVE_STALEMATE_CONVERGENCE", "Every game branch terminates in DRAW; clock speed accelerates"),
            ("0940", "SIMULATE_ALL_SIOP_SCENARIOS", "Cycle US FIRST STRIKE, USSR FIRST STRIKE, NATO SURGE -> 100% LETHAL"),
            ("0950", "DISPLAY 'WINNER: NONE'", "Conclude Global Thermonuclear War is isomorphic to noughts & crosses"),
            ("0960", "HALT_LAUNCH: 'ONLY WINNING MOVE IS NOT TO PLAY'", "Release silo launch relays; restore DEFCON 5 peacetime state"),
        ]
    }
}

def measure_thumb_rgb_lum(rel_path):
    full = os.path.join(LAB, rel_path)
    if not os.path.exists(full):
        return (40, 44, 48, 0.18)
    try:
        im = Image.open(full).convert("RGB").resize((16, 12))
        px = list(im.getdata())
        r = int(sum(p[0] for p in px) / len(px))
        g = int(sum(p[1] for p in px) / len(px))
        b = int(sum(p[2] for p in px) / len(px))
        lum = round((0.299 * r + 0.587 * g + 0.114 * b) / 255.0, 3)
        return (r, g, b, lum)
    except Exception:
        return (40, 44, 48, 0.18)

def build_screens_program():
    os_d = json.load(open(os.path.join(HERE, "wargames_os.json")))
    subsystems_out = []
    all_states = []
    seen_ids = set()

    for sub_idx, sub in enumerate(os_d["subsystems"]):
        sid = sub["id"]
        scode = sub["code"]
        prog_meta = SUBSYSTEM_PROGRAMS.get(sid, SUBSYSTEM_PROGRAMS["SYS://IMSAI-8080"])
        code_lines = prog_meta["code"]

        # Combine verified sbd_screen_cuts + curated wg shots for this subsystem
        combined = []
        for s in sub.get("sbd_screen_cuts", []):
            combined.append((s, True))
        for s in sub.get("shots", []):
            combined.append((s, False))

        # Deduplicate within subsystem preserving chronological start time
        sub_seen = set()
        deduped = []
        for s, is_sbd in sorted(combined, key=lambda x: x[0].get("start", 0)):
            if s["id"] in sub_seen:
                continue
            sub_seen.add(s["id"])
            deduped.append((s, is_sbd))

        sub_states = []
        for k, (s, is_sbd) in enumerate(deduped):
            shot_id = s["id"]
            state_code = f"{scode}.S{k+1:02d}"
            line_idx = min(len(code_lines) - 1, int((k / max(1, len(deduped))) * len(code_lines)))
            line_num, code_stmt, code_comment = code_lines[line_idx]

            has_strip = shot_id.startswith("wg_") and os.path.exists(os.path.join(LAB, f"strips/{shot_id}.jpg"))
            strip_url = f"strips/{shot_id}.jpg" if has_strip else ""
            static_clip = f"clips/{shot_id}.mp4" if os.path.exists(os.path.join(LAB, f"clips/{shot_id}.mp4")) else ""

            scr_thumb = s.get("screen_thumb") or s.get("full_thumb") or f"thumbs/{shot_id}.jpg"
            full_thumb = s.get("full_thumb") or scr_thumb
            r, g, b, lum = measure_thumb_rgb_lum(scr_thumb)

            # Determine observed screen text & register state
            term_lines = sub.get("terminal_lines", [])
            obs_text = s.get("whisper") or s.get("note") or (term_lines[k % len(term_lines)] if term_lines else sub["title"])
            prev_state = f"{scode}.S{k:02d}" if k > 0 else "INIT"
            next_state = f"{scode}.S{k+2:02d}" if k + 1 < len(deduped) else "COMMIT/NEXT_SUB"

            state_obj = {
                "state_id": state_code,
                "global_idx": len(all_states),
                "local_idx": k,
                "shot_id": shot_id,
                "is_verified_crop": bool(os.path.exists(os.path.join(LAB, f"thumbs/screens/{shot_id}.jpg"))),
                "subsystem_id": sid,
                "subsystem_code": scode,
                "subsystem_short": sub["short"],
                "subsystem_title": sub["title"],
                "hardware": sub["hardware"],
                "baud": sub["baud"],
                "color": sub["color"],
                "category": s.get("category", "crt_terminal"),
                "scene_id": s.get("scene_id", "S01"),
                "scene_title": s.get("scene_title", ""),
                "start": round(s.get("start", 0), 2),
                "end": round(s.get("end", 0), 2),
                "dur": round(s.get("dur", 3.0), 2),
                "screen_thumb": scr_thumb,
                "full_thumb": full_thumb,
                "strip": strip_url,
                "sub_frames": 8 if has_strip else 1,
                "clip": s.get("clip", ""),
                "static_clip": static_clip,
                "crop_box": s.get("crop_box", [0, 0, 1, 1]),
                "purity": round(s.get("purity", 0.85), 3),
                "palette": s.get("palette", ["#0a1410", "#4af6c3"]),
                "rgb": [r, g, b],
                "lum": lum,
                "observed_text": obs_text[:140],
                "prev_state": prev_state,
                "next_state": next_state,
                "code_line_idx": line_idx,
                "code_line_num": line_num,
                "inferred_stmt": code_stmt,
                "inferred_comment": code_comment,
                "transition_rule": f"δ({prev_state}, t={s.get('start',0):.1f}s) → {state_code} [{code_stmt.split(';')[0].strip()}]",
            }
            sub_states.append(state_obj)
            if shot_id not in seen_ids:
                seen_ids.add(shot_id)
            all_states.append(state_obj)

        # Group states per code line
        program_lines = []
        for l_idx, (l_num, l_code, l_comm) in enumerate(code_lines):
            matching_states = [st["state_id"] for st in sub_states if st["code_line_idx"] == l_idx]
            program_lines.append({
                "line_idx": l_idx,
                "line_num": l_num,
                "code": l_code,
                "comment": l_comm,
                "state_ids": matching_states,
            })

        subsystems_out.append({
            "id": sid,
            "code": scode,
            "short": sub["short"],
            "title": sub["title"],
            "node": sub["node"],
            "hardware": sub["hardware"],
            "baud": sub["baud"],
            "color": sub["color"],
            "cmd": sub["cmd"],
            "prompt": sub["prompt"],
            "summary": sub["summary"],
            "io_schema": sub["io_schema"],
            "terminal_lines": sub["terminal_lines"],
            "lang": prog_meta["lang"],
            "entrypoint": prog_meta["entrypoint"],
            "inferred_invariant": prog_meta["inferred_invariant"],
            "program_lines": program_lines,
            "states": sub_states,
        })

    out = {
        "title": "01 / SCREEN STATES · WOPR & IMSAI Program Inference Atlas",
        "total_states": len(all_states),
        "unique_shots": len(seen_ids),
        "total_subframe_states": sum(st["sub_frames"] for st in all_states),
        "subsystems": subsystems_out,
        "all_states": sorted(all_states, key=lambda x: x["start"]),
    }
    out_path = os.path.join(LAB, "wargames-screens-program.json")
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {out_path}: {len(all_states)} screen states ({out['total_subframe_states']} sub-frame states) across {len(subsystems_out)} subsystems.")


def slim_unit(u):
    return {
        "id": u.get("id", ""),
        "subframes": u.get("subframes", "f1-f2"),
        "title": u.get("title", "Archive"),
        "year": u.get("year", 1960),
        "video": u.get("video", ""),
        "thumb": u.get("thumb", ""),
        "t0": round(u.get("t0", 0.0), 2),
        "t1": round(u.get("t1", 2.5), 2),
        "dur": round(u.get("target_dur") or u.get("dur") or 1.5, 2),
        "spoken": (u.get("spoken") or u.get("phrase") or u.get("label") or "")[:110],
        "regime": u.get("winning_lens") or u.get("regime") or "Archive",
        "score": round(u.get("consensus") or u.get("clip_sim") or 0.85, 2),
    }


def build_studio_cuts():
    fw = json.load(open(os.path.join(HERE, "found_wargames.json")))
    sb = json.load(open(os.path.join(LAB, "wargames-sound-bench.json")))

    # Index sound-bench lines by id
    sb_by_id = {}
    for bk in sb.get("books", []):
        for l in bk.get("lines", []):
            sb_by_id[l["id"]] = l

    books_out = []
    stills_atlas = []
    seen_thumbs = set()

    # Collect local wg thumbs + screen thumbs for fast CORS-safe canvas photomosaic & slit-scan rendering
    for i in range(1, 303):
        rel = f"thumbs/wg_{i:03d}.jpg"
        if os.path.exists(os.path.join(LAB, rel)):
            r, g, b, lum = measure_thumb_rgb_lum(rel)
            stills_atlas.append({
                "id": f"wg_{i:03d}",
                "thumb": rel,
                "strip": f"strips/wg_{i:03d}.jpg",
                "clip": f"clips/wg_{i:03d}.mp4" if os.path.exists(os.path.join(LAB, f"clips/wg_{i:03d}.mp4")) else "",
                "r": r, "g": g, "b": b, "lum": lum,
                "kind": "1983"
            })
            seen_thumbs.add(rel)

    for b_idx, bk in enumerate(fw.get("books", [])):
        beats_out = []
        for bt in bk.get("beats", []):
            bid = bt["beat_id"]
            sbl = sb_by_id.get(bid, {})
            wgs = bt.get("wg_shot", {})
            shot_id = wgs.get("id", "wg_001")
            static_clip = f"clips/{shot_id}.mp4" if os.path.exists(os.path.join(LAB, f"clips/{shot_id}.mp4")) else ""

            lenses = bt.get("lenses", {})
            sp_cuts = bt.get("species_cuts", {})

            # Gather the 8 simultaneous cuts for this beat
            cuts = {
                "1983": [{
                    "id": shot_id,
                    "subframes": "f1–f8",
                    "title": "WarGames (1983)",
                    "year": 1983,
                    "video": static_clip or f"/api/wargames/slice?start={wgs.get('start',0)}&end={wgs.get('end',5)}",
                    "thumb": wgs.get("thumb", f"thumbs/{shot_id}.jpg"),
                    "strip": wgs.get("strip", f"strips/{shot_id}.jpg"),
                    "t0": 0.0,
                    "t1": round(wgs.get("dur", 5.0), 2),
                    "dur": round(wgs.get("dur", 5.0), 2),
                    "spoken": bt.get("text", ""),
                    "regime": f"1983 Master · Sign #{wgs.get('sign','9')}",
                    "score": 1.0,
                }],
                "synthesis": [slim_unit(u) for u in lenses.get("synthesis", [])[:6]],
                "clip": [slim_unit(u) for u in lenses.get("clip", [])[:6]],
                "vjepa": [slim_unit(u) for u in lenses.get("vjepa", [])[:6]],
                "blip": [slim_unit(u) for u in lenses.get("blip", [])[:6]],
                "cineosis": [slim_unit(u) for u in lenses.get("cineosis", [])[:6]],
                "trurl": [slim_unit(u) for u in sp_cuts.get("trurl_phosphor", [])[:6]],
                "klapaucius": [slim_unit(u) for u in sp_cuts.get("klapaucius_dialectic", [])[:6]],
                "murch": [slim_unit(u) for u in sp_cuts.get("murch_intimacy", [])[:6]],
                "novelty": [slim_unit(u) for u in sp_cuts.get("stanley_novelty", [])[:6]],
            }

            # Add Tarantino 3 unbroken takes from sound-bench
            takes = []
            for tk in sbl.get("takes", [])[:3]:
                takes.append({
                    "take_num": tk.get("take_num", 1),
                    "speaker": tk.get("speaker") or tk.get("title") or "Archive",
                    "title": tk.get("title", "Archive"),
                    "year": tk.get("year", 1960),
                    "text": tk.get("spoken") or tk.get("text") or "",
                    "video": tk.get("video", ""),
                    "audio_url": tk.get("audio_url", ""),
                    "thumb": tk.get("thumb", ""),
                    "t0": round(tk.get("t0", 0), 2),
                    "t1": round(tk.get("t1", 3), 2),
                    "clip_t0": round(tk.get("clip_t0", tk.get("t0", 0)), 2),
                    "clip_t1": round(tk.get("clip_t1", tk.get("t1", 3)), 2),
                })

            beats_out.append({
                "id": bid,
                "index": bt.get("index", 0),
                "who": bt.get("who", "1983"),
                "text": bt.get("text", ""),
                "foley": bt.get("foley_label", ""),
                "wg_shot": {
                    "id": shot_id,
                    "start": round(wgs.get("start", 0), 2),
                    "end": round(wgs.get("end", 5), 2),
                    "dur": round(wgs.get("dur", 5), 2),
                    "thumb": wgs.get("thumb", f"thumbs/{shot_id}.jpg"),
                    "strip": wgs.get("strip", f"strips/{shot_id}.jpg"),
                    "video": static_clip or f"/api/wargames/slice?start={wgs.get('start',0)}&end={wgs.get('end',5)}",
                    "static_clip": static_clip,
                    "sign": wgs.get("sign", "9"),
                    "sign_note": wgs.get("sign_note", ""),
                    "palette": wgs.get("palette", ["#111", "#e8c070"]),
                },
                "orig_file": sbl.get("orig_file", ""),
                "aligned_file": sbl.get("aligned_file", ""),
                "tight_file": sbl.get("tight_file", ""),
                "turns_1983": sbl.get("turns_1983", []),
                "takes": takes,
                "cuts": cuts,
            })

        books_out.append({
            "n": b_idx + 1,
            "bnum": bk.get("bnum", str(b_idx + 1)),
            "title": bk.get("title", f"Book {b_idx+1}"),
            "beats": beats_out,
        })

    out = {
        "title": "The Found WarGames · Simultaneous Multi-Cut Studio Set",
        "stills_atlas": sorted(stills_atlas, key=lambda x: x["lum"]),
        "books": books_out,
    }
    out_path = os.path.join(LAB, "wargames-studio-cuts.json")
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    sz_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Wrote {out_path} ({sz_mb:.2f} MB): {len(books_out)} books, {len(stills_atlas)} still-frame tiles.")


if __name__ == "__main__":
    build_screens_program()
    build_studio_cuts()
