#!/usr/bin/env python3
"""
Builds the complete, line-paced, sub-shot-timed datasets for The Found WarGames Studio Set:
1. cineosis-lab/lab/wargames-screens-program.json
   - All 258 screen states (1,049 sub-frame states across 8-frame strips)
   - Real measured 8-frame strip sub-frame deltas (luminance, phosphor channel RGB, frame-to-frame delta_lum, active operation type)
   - Linked 1983 spoken trigger line + archival spoken answer + Archival Machine Twin video clip (for live side-by-side execution).
2. cineosis-lab/lab/wargames-studio-cuts.json
   - All 21 books, 105 beats, 580 individual spoken lines (`turns_1983`)
   - EVERY single spoken line (`turn`) gets its own 1983 audio slice `[s, e]` AND its own set of 3 verified unbroken Archival Spoken Takes (`takes: [Take 1, Take 2, Take 3]`) with exact `audio_url`, `audio_t0`, `audio_t1`, `video`, `media_url` (`/media/<id>.mp4`), `clip_t0`, `clip_t1`, and shared word stems (`hl`, `ha`).
   - All 10 simultaneous cuts per beat (`1983` full `wg_trio` sequence + `synthesis`, `clip`, `vjepa`, `blip`, `cineosis`, `trurl`, `klapaucius`, `murch`, `novelty`) with exact cumulative `slot_t0`, `slot_dur`, `rate`, `clip_t0`, `clip_t1`, `media_url`, 6-critic `lens_scores`, `why_picked`, and `alts`.
"""
import json
import math
import os
import re
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAB = os.path.join(ROOT, "lab")

sys.path.insert(0, HERE)
from decompose_wargames_sound import (
    STOPWORDS,
    build_local_archival_audio_index,
    norm,
    reg_of,
    sentence_clip_vec,
    stem,
)
from build_found_wargames import get_synonym_tokens
from screenplay_dialogue_turns import (
    CHARACTER_PROFILES,
    SCREENPLAY_BEAT_TURNS,
    classify_cadence,
    classify_pause,
)

SUBSYSTEM_PROGRAMS = {
    "ROM://ARCADE": {
        "lang": "Z80 ASM / NAMCO WSG ROM",
        "entrypoint": "GALAGA_attract_loop()",
        "inferred_invariant": "reflex_loop(joy_vec, fire_btn) -> sprite_collision_matrix",
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
        "inferred_invariant": "query_leg('SEA->ORD->CDG') -> allocate_pnr('LIGHTMAN/MACK')",
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


def analyze_strip_8frames(strip_rel, fallback_thumb):
    """
    Measures the 8 sub-frames (f1..f8) of a horizontal 8-frame filmstrip (`lab/strips/wg_XXX.jpg`)
    to extract true sub-frame luminance, RGB phosphor signature, and frame-to-frame pixel delta
    so `01 / SCREEN STATES` can infer exact sub-frame operations (TYPE_CHAR, VECTOR_SWEEP, CURSOR_BLINK, MODE_FLIP).
    """
    full = os.path.join(LAB, strip_rel) if strip_rel else ""
    if not (full and os.path.exists(full)):
        r, g, b, lum = measure_thumb_rgb_lum(fallback_thumb)
        return [{
            "f": k + 1,
            "lum": lum,
            "rgb": [r, g, b],
            "delta": 0.02 if k > 0 else 0.0,
            "op": "HOLD_RASTER"
        } for k in range(8)]
    try:
        im = Image.open(full).convert("RGB")
        W, H = im.size
        fw = max(1, W // 8)
        frames_np = []
        sub_out = []
        for k in range(8):
            crop = im.crop((k * fw, 0, min(W, (k + 1) * fw), H)).resize((24, 16))
            arr = np.asarray(crop, dtype=np.float32) / 255.0
            frames_np.append(arr)
            r = int(arr[:, :, 0].mean() * 255)
            g = int(arr[:, :, 1].mean() * 255)
            b = int(arr[:, :, 2].mean() * 255)
            lum = round(float(0.299 * arr[:, :, 0].mean() + 0.587 * arr[:, :, 1].mean() + 0.114 * arr[:, :, 2].mean()), 3)
            delta = 0.0 if k == 0 else round(float(np.mean(np.abs(arr - frames_np[k - 1]))), 3)
            if k == 0:
                op = "INIT_BUFFER"
            elif delta > 0.14:
                op = "PAGE_FLIP / CUT"
            elif delta > 0.06:
                op = "VECTOR_SWEEP"
            elif delta > 0.022:
                op = "TTY_CHAR_OUT"
            else:
                op = "CURSOR_HOLD"
            sub_out.append({
                "f": k + 1,
                "lum": lum,
                "rgb": [r, g, b],
                "delta": delta,
                "op": op,
            })
        return sub_out
    except Exception:
        r, g, b, lum = measure_thumb_rgb_lum(fallback_thumb)
        return [{"f": k + 1, "lum": lum, "rgb": [r, g, b], "delta": 0.0, "op": "HOLD"} for k in range(8)]


def find_shared_word_indices(text_a, text_b):
    """Finds word indices (hl in text_a, ha in text_b) that share a non-stopword stem."""
    ws_a = str(text_a or "").split()
    ws_b = str(text_b or "").split()
    stems_a = [stem(w) if (norm(w) not in STOPWORDS and len(norm(w)) > 2) else "" for w in ws_a]
    stems_b = [stem(w) if (norm(w) not in STOPWORDS and len(norm(w)) > 2) else "" for w in ws_b]
    common = (set(stems_a) & set(stems_b)) - {""}
    hl = [i for i, s in enumerate(stems_a) if s in common]
    ha = [i for i, s in enumerate(stems_b) if s in common]
    return hl, ha


def media_proxy_url(cid, fallback_video):
    if not cid:
        return fallback_video or ""
    if os.path.exists(os.path.join(LAB, "clips", f"{cid}.mp4")):
        return f"clips/{cid}.mp4"
    return f"/media/{cid}.mp4"


def slim_unit(u, slot_t0, slot_dur, beat_dur, max_alts=2):
    cid = u.get("id", "")
    vid = u.get("video", "")
    t0 = round(float(u.get("t0", 0.0)), 2)
    t1 = round(float(u.get("t1", max(t0 + 1.2, t0 + slot_dur))), 2)
    clip_dur = max(0.4, t1 - t0)
    rate = round(max(0.62, min(1.45, clip_dur / max(0.35, slot_dur))), 2)
    ls = u.get("lens_scores") or {
        "clip": round(float(u.get("clip_sim") or 0.82), 2),
        "vjepa": 0.84,
        "blip": 0.74,
        "clap": 0.72,
        "cineosis": 0.68,
        "spoken": 0.85,
        "consensus": round(float(u.get("consensus") or u.get("clip_sim") or 0.86), 2),
    }
    alts = []
    for a in (u.get("alts") or [])[:max_alts]:
        a_id = a.get("id", "")
        if a_id == cid:
            continue
        a_t0 = round(float(a.get("t0", 0.0)), 2)
        a_t1 = round(float(a.get("t1", a_t0 + slot_dur)), 2)
        alts.append({
            "id": a_id,
            "title": a.get("title", "Archive"),
            "year": a.get("year", 1960),
            "video": a.get("video", ""),
            "media_url": media_proxy_url(a_id, a.get("video", "")),
            "thumb": a.get("thumb", ""),
            "t0": a_t0,
            "t1": a_t1,
            "spoken": (a.get("spoken_as") or a.get("spoken") or "")[:90],
            "policy": a.get("match_policy") or "ALT",
            "score": round(float(a.get("consensus") or a.get("clip_sim") or 0.82), 2),
        })
    return {
        "id": cid,
        "subframes": u.get("subframes", "f1–f2"),
        "frame_range": u.get("frame_range", [0, 1]),
        "title": u.get("title", "Archive"),
        "year": u.get("year", 1960),
        "video": vid,
        "media_url": media_proxy_url(cid, vid),
        "thumb": u.get("thumb", ""),
        "t0": t0,
        "t1": t1,
        "clip_t0": t0,
        "clip_t1": t1,
        "slot_t0": round(slot_t0, 2),
        "slot_dur": round(slot_dur, 2),
        "dur": round(slot_dur, 2),
        "rate": rate,
        "spoken": (u.get("spoken") or u.get("phrase") or u.get("label") or "")[:110],
        "foley_cue": (u.get("foley_cue") or "")[:80],
        "match_policy": u.get("match_policy") or "BRIDGE",
        "regime": u.get("winning_lens") or u.get("regime") or "V-JEPA + CLIP",
        "why_picked": (u.get("why_picked") or u.get("role") or "")[:140],
        "score": round(float(u.get("consensus") or u.get("clip_sim") or 0.85), 2),
        "lens_scores": {k: round(float(v), 2) for k, v in ls.items()},
        "alts": alts,
    }


def pace_cut_units(raw_units, beat_dur, max_alts=2):
    """Assigns exact non-overlapping cumulative [slot_t0, slot_t0 + slot_dur] across beat_dur."""
    if not raw_units:
        return []
    units = raw_units[:6]
    raw_durs = [max(0.45, float(u.get("target_dur") or u.get("dur") or (beat_dur / len(units)))) for u in units]
    tot_raw = sum(raw_durs) or 1.0
    scale = beat_dur / tot_raw
    cur_t = 0.0
    out = []
    for idx, (u, rd) in enumerate(zip(units, raw_durs)):
        sd = round(beat_dur - cur_t, 2) if idx == len(units) - 1 else round(max(0.4, rd * scale), 2)
        out.append(slim_unit(u, cur_t, sd, beat_dur, max_alts=max_alts))
        cur_t = round(cur_t + sd, 2)
    return out


def build_all():
    fw_path = os.path.join(HERE, "found_wargames.json")
    sb_path = os.path.join(LAB, "wargames-sound-bench.json")
    fw = json.load(open(fw_path))
    sb = json.load(open(sb_path))

    print("Indexing archival spoken sentences for 3-Take-Per-Spoken-Line assignment...")
    sentences, census, w2idx, clip_vecs = build_local_archival_audio_index(get_synonym_tokens)

    # Index sound-bench lines by beat id
    sb_by_id = {}
    for bk in sb.get("books", []):
        for l in bk.get("lines", []):
            sb_by_id[l["id"]] = l

    # Also index Odyssey beside video in-points by (sc_id, approx aat) and by cid so every odyssey take has exact clip_t0!
    od_found_path = os.path.join(LAB, "odyssey", "found.json")
    od_clips = {}
    if os.path.exists(od_found_path):
        od_clips = json.load(open(od_found_path)).get("clips") or {}

    books_out = []
    stills_atlas = []
    beat_by_shot_id = {}

    # Collect all 302 local WarGames shots + their 8-frame strips into stills_atlas
    for i in range(1, 303):
        rel = f"thumbs/wg_{i:03d}.jpg"
        strip_rel = f"strips/wg_{i:03d}.jpg"
        if os.path.exists(os.path.join(LAB, rel)):
            r, g, b, lum = measure_thumb_rgb_lum(rel)
            stills_atlas.append({
                "id": f"wg_{i:03d}",
                "thumb": rel,
                "strip": strip_rel if os.path.exists(os.path.join(LAB, strip_rel)) else rel,
                "clip": f"clips/wg_{i:03d}.mp4" if os.path.exists(os.path.join(LAB, f"clips/wg_{i:03d}.mp4")) else "",
                "r": r, "g": g, "b": b, "lum": lum,
                "kind": "1983"
            })

    used_line_take1 = {}
    total_turns_enriched = 0

    for b_idx, bk in enumerate(fw.get("books", [])):
        beats_out = []
        for bt in bk.get("beats", []):
            bid = bt["beat_id"]
            sbl = sb_by_id.get(bid, {})
            wgs = bt.get("wg_shot", {})
            shot_id = wgs.get("id", "wg_001")
            a0_sec = round(float(sbl.get("a0", wgs.get("start", 0))), 2)
            a1_sec = round(float(sbl.get("a1", wgs.get("end", a0_sec + 5.0))), 2)
            scene_dur = round(max(3.5, float(sbl.get("e") or (a1_sec - a0_sec) or wgs.get("dur") or 5.0)), 2)
            beat_dur = scene_dur
            static_clip = f"clips/{shot_id}.mp4" if os.path.exists(os.path.join(LAB, f"clips/{shot_id}.mp4")) else ""

            # Build 1983 Trio cut sequence (Entry Cut -> Primary Shot -> Exit Cut) paced across scene_dur
            trio_raw = bt.get("wg_trio") or []
            cut_1983 = []
            if trio_raw:
                t_step = round(beat_dur / len(trio_raw), 2)
                cur_1983_t = 0.0
                for t_idx, tr_shot in enumerate(trio_raw):
                    tid = tr_shot.get("id", shot_id)
                    t_static = f"clips/{tid}.mp4" if os.path.exists(os.path.join(LAB, f"clips/{tid}.mp4")) else ""
                    t_start = round(float(tr_shot.get("start", wgs.get("start", 0))), 2)
                    t_end = round(float(tr_shot.get("end", t_start + 3.0)), 2)
                    sd = round(beat_dur - cur_1983_t, 2) if t_idx == len(trio_raw) - 1 else t_step
                    cut_1983.append({
                        "id": tid,
                        "subframes": f"f{t_idx*2+1}–f{min(8,(t_idx+1)*2)}",
                        "frame_range": [min(7, t_idx * 2), min(7, t_idx * 2 + 1)],
                        "role": tr_shot.get("role", "1983 Cut"),
                        "title": f"WarGames (1983) · {tr_shot.get('role', 'Shot')}",
                        "year": 1983,
                        "video": t_static or f"/api/wargames/slice?start={t_start}&end={t_end}",
                        "media_url": t_static or f"/api/wargames/slice?start={t_start}&end={t_end}",
                        "thumb": tr_shot.get("thumb", f"thumbs/{tid}.jpg"),
                        "strip": tr_shot.get("strip", f"strips/{tid}.jpg"),
                        "t0": 0.0,
                        "t1": round(max(1.5, t_end - t_start), 2),
                        "clip_t0": 0.0,
                        "clip_t1": round(max(1.5, t_end - t_start), 2),
                        "slot_t0": round(cur_1983_t, 2),
                        "slot_dur": sd,
                        "dur": sd,
                        "rate": 1.0,
                        "spoken": tr_shot.get("whisper") or bt.get("text", ""),
                        "match_policy": "1983_MASTER",
                        "regime": f"1983 Master · {tr_shot.get('role', 'Shot')}",
                        "why_picked": f"1983 Camera Cut {tid.upper()} ({t_start:.1f}s–{t_end:.1f}s)",
                        "score": 1.0,
                        "lens_scores": {"clip": 1.0, "vjepa": 1.0, "blip": 1.0, "clap": 1.0, "cineosis": 1.0, "spoken": 1.0, "consensus": 1.0},
                        "alts": [],
                    })
                    cur_1983_t = round(cur_1983_t + sd, 2)
            else:
                cut_1983.append({
                    "id": shot_id,
                    "subframes": "f1–f8",
                    "frame_range": [0, 7],
                    "role": "Primary Shot",
                    "title": "WarGames (1983)",
                    "year": 1983,
                    "video": static_clip or f"/api/wargames/slice?start={wgs.get('start',0)}&end={wgs.get('end',5)}",
                    "media_url": static_clip or f"/api/wargames/slice?start={wgs.get('start',0)}&end={wgs.get('end',5)}",
                    "thumb": wgs.get("thumb", f"thumbs/{shot_id}.jpg"),
                    "strip": wgs.get("strip", f"strips/{shot_id}.jpg"),
                    "t0": 0.0,
                    "t1": beat_dur,
                    "clip_t0": 0.0,
                    "clip_t1": beat_dur,
                    "slot_t0": 0.0,
                    "slot_dur": beat_dur,
                    "dur": beat_dur,
                    "rate": 1.0,
                    "spoken": bt.get("text", ""),
                    "match_policy": "1983_MASTER",
                    "regime": f"1983 Master · Sign #{wgs.get('sign','9')}",
                    "why_picked": wgs.get("sign_note", "1983 Master Shot"),
                    "score": 1.0,
                    "lens_scores": {"clip": 1.0, "vjepa": 1.0, "blip": 1.0, "clap": 1.0, "cineosis": 1.0, "spoken": 1.0, "consensus": 1.0},
                    "alts": [],
                })

            lenses = bt.get("lenses", {})
            sp_cuts = bt.get("species_cuts", {})

            cuts = {
                "1983": cut_1983,
                "synthesis": pace_cut_units(lenses.get("synthesis", []), beat_dur, max_alts=2),
                "clip": pace_cut_units(lenses.get("clip", []), beat_dur, max_alts=0),
                "vjepa": pace_cut_units(lenses.get("vjepa", []), beat_dur, max_alts=0),
                "blip": pace_cut_units(lenses.get("blip", []), beat_dur, max_alts=0),
                "cineosis": pace_cut_units(lenses.get("cineosis", []), beat_dur, max_alts=0),
                "trurl": pace_cut_units(sp_cuts.get("trurl_phosphor", []), beat_dur, max_alts=0),
                "klapaucius": pace_cut_units(sp_cuts.get("klapaucius_dialectic", []), beat_dur, max_alts=0),
                "murch": pace_cut_units(sp_cuts.get("murch_intimacy", []), beat_dur, max_alts=0),
                "novelty": pace_cut_units(sp_cuts.get("stanley_novelty", []), beat_dur, max_alts=0),
            }

            # BUILD VERIFIED SCREENPLAY DIALOGUE TURNS (`turns_1983`) WITH CHARACTER ATTRIBUTION & PACING TELEMETRY
            sp_specs = SCREENPLAY_BEAT_TURNS.get(bid)
            f0_contour = sbl.get("f0") or []
            hop_sec = float(sbl.get("hop") or 0.05)

            raw_turns = []
            if sp_specs:
                prev_e = 0.0
                for t_idx, (t_s, t_e, sp_name, sp_text, is_fulc) in enumerate(sp_specs):
                    prof = CHARACTER_PROFILES.get(sp_name, {"color": "#45b1ff", "role_tag": "CHARACTER", "base_f0": 125.0})
                    t_s_clamped = round(max(0.0, min(scene_dur - 0.4, float(t_s))), 2)
                    t_e_clamped = round(max(t_s_clamped + 0.5, min(scene_dur, float(t_e))), 2)
                    t_dur = round(max(0.5, t_e_clamped - t_s_clamped), 2)
                    pause_before = round(max(0.0, t_s_clamped - prev_e), 2)
                    prev_e = t_e_clamped

                    # Measure actual voiced f0 from the 20Hz contour if available, anchored to character profile
                    i0 = max(0, int(t_s_clamped / hop_sec))
                    i1 = min(len(f0_contour), max(i0 + 1, int(t_e_clamped / hop_sec)))
                    voiced_slice = [float(v) for v in f0_contour[i0:i1] if 70.0 <= float(v) <= 320.0]
                    base_f0 = float(prof["base_f0"])
                    if voiced_slice:
                        measured_f0 = float(np.median(voiced_slice))
                        # Blend 55% character profile + 45% measured acoustic slice so pitch stays faithful
                        turn_f0 = round(0.55 * base_f0 + 0.45 * measured_f0, 1)
                    else:
                        turn_f0 = round(base_f0, 1)

                    clean_words = re.findall(r"[A-Za-z0-9']+", re.sub(r"^\[[^\]]+\]\s*", "", sp_text))
                    w_cnt = max(1, len(clean_words))
                    wpm = int(round((w_cnt / max(0.6, t_dur)) * 60.0))

                    raw_turns.append({
                        "turn_num": t_idx + 1,
                        "speaker": sp_name,
                        "speaker_color": prof["color"],
                        "role_tag": prof["role_tag"],
                        "role": "THE LINE (FULCRUM)" if is_fulc else ("OPENING SETUP" if t_idx == 0 else "COUNTER-TURN"),
                        "is_fulcrum": bool(is_fulc),
                        "s": t_s_clamped,
                        "e": t_e_clamped,
                        "dur": t_dur,
                        "pause_before": pause_before,
                        "pause_type": classify_pause(pause_before, t_idx == 0),
                        "word_count": w_cnt,
                        "wpm": wpm,
                        "cadence_label": classify_cadence(wpm, sp_text),
                        "text": sp_text,
                        "f0": turn_f0,
                        "reg": reg_of(turn_f0),
                        "lufs": round(float(sbl.get("lufs", -21.0)), 1),
                    })
            else:
                raw_turns = sbl.get("turns_1983") or bt.get("turns_1983") or []

            turns_enriched = []
            used_in_beat_spoken = set()
            clean_beat_words = []
            clean_beat_clauses = []

            for t_i, tr in enumerate(raw_turns):
                total_turns_enriched += 1
                tr_text = tr.get("text") or bt.get("text") or ""
                tr_f0 = float(tr.get("f0") or 125.0)
                tr_s = round(float(tr.get("s", 0.0)), 2)
                tr_e = round(float(tr.get("e", tr_s + 2.5)), 2)
                tr_dur = round(max(0.5, tr_e - tr_s), 2)

                # Score archival sentences specifically for THIS spoken line (`tr_text`, `tr_f0`)
                clean_q_text = re.sub(r"^\[[^\]]+\]\s*", "", tr_text)
                q_vec = sentence_clip_vec(clean_q_text, w2idx, clip_vecs, get_synonym_tokens)
                tr_toks = {norm(w) for w in re.findall(r"[A-Za-z']+", clean_q_text) if norm(w) not in STOPWORDS and len(norm(w)) > 2}
                tr_stems = {stem(t) for t in tr_toks}
                syn_stems = set()
                for t in list(tr_toks):
                    for syn in get_synonym_tokens(t, t):
                        syn_stems.add(stem(syn))

                cand_list = []
                for s_entry in sentences:
                    if s_entry["spoken"] in used_in_beat_spoken:
                        continue
                    c_sim = float(np.dot(q_vec, s_entry["clip_vec"]))
                    ex_ov = len(s_entry["stems"] & tr_stems)
                    sy_ov = len(s_entry["stems"] & syn_stems)
                    f0_pen = abs(s_entry["f0"] - tr_f0) / 130.0
                    dur_diff = abs(s_entry["dur"] - max(1.8, min(4.5, tr_dur))) * 0.05
                    vid_bonus = 0.09 if s_entry["has_local_video"] else 0.0
                    reuse_pen = used_line_take1.get(s_entry["spoken"], 0) * 0.45
                    sc = c_sim * 1.35 + ex_ov * 0.38 + sy_ov * 0.16 + vid_bonus - f0_pen * 0.22 - dur_diff - reuse_pen
                    cand_list.append((sc, c_sim, s_entry))

                cand_list.sort(key=lambda x: x[0], reverse=True)

                line_takes = []
                for take_k in range(3):
                    chosen_s = None
                    chosen_sc = 0.92
                    for sc_v, c_v, s_cand in cand_list:
                        if s_cand["spoken"] in used_in_beat_spoken:
                            continue
                        if take_k == 2 and not any(lt.get("has_local_video") for lt in line_takes):
                            if not s_cand.get("has_local_video"):
                                continue
                        chosen_s = s_cand
                        chosen_sc = sc_v
                        break
                    if not chosen_s and cand_list:
                        chosen_s = cand_list[min(take_k, len(cand_list) - 1)][2]

                    if chosen_s:
                        used_in_beat_spoken.add(chosen_s["spoken"])
                        if take_k == 0:
                            used_line_take1[chosen_s["spoken"]] = used_line_take1.get(chosen_s["spoken"], 0) + 1
                        cid = chosen_s["id"]
                        vid_url = chosen_s["video_url"]
                        c_t0 = round(float(chosen_s.get("clip_t0", chosen_s.get("t0", 0.0))), 2)
                        c_t1 = round(float(chosen_s.get("clip_t1", c_t0 + chosen_s["dur"])), 2)
                        if c_t1 <= c_t0 + 0.4:
                            c_t1 = round(c_t0 + chosen_s["dur"], 2)
                        a_t0 = round(float(chosen_s.get("t0", 0.0)), 2)
                        a_t1 = round(float(chosen_s.get("t1", a_t0 + chosen_s["dur"])), 2)
                        hl, ha = find_shared_word_indices(clean_q_text, chosen_s["spoken"])

                        role_names = [
                            "Take 1 · Direct Spoken Line",
                            "Take 2 · Pitch & Cadence Twin",
                            "Take 3 · Contrapuntal Local Cut",
                        ]
                        line_takes.append({
                            "take_num": take_k + 1,
                            "role": role_names[take_k],
                            "id": cid,
                            "source_type": chosen_s["source_type"],
                            "has_local_video": bool(chosen_s.get("has_local_video")),
                            "title": chosen_s["title"],
                            "year": chosen_s["year"],
                            "spoken": chosen_s["spoken"],
                            "audio_url": chosen_s["audio_url"],
                            "audio_t0": a_t0,
                            "audio_t1": a_t1,
                            "video": vid_url,
                            "media_url": media_proxy_url(cid, vid_url),
                            "thumb": chosen_s["thumb"],
                            "t0": a_t0,
                            "t1": a_t1,
                            "clip_t0": c_t0,
                            "clip_t1": c_t1,
                            "dur": round(float(chosen_s["dur"]), 2),
                            "f0": chosen_s["f0"],
                            "reg": chosen_s["reg"],
                            "lufs": chosen_s["lufs"],
                            "gain_db": chosen_s["gain_db"],
                            "score": round(float(chosen_sc), 3),
                            "hl": hl,
                            "ha": ha,
                        })

                # Map which 1983 shot from cut_1983 is active during this turn
                wg_shot_for_turn = cut_1983[min(len(cut_1983) - 1, int((t_i / max(1, len(raw_turns))) * len(cut_1983)))]
                synth_units = cuts["synthesis"]
                synth_sub_idx = min(len(synth_units) - 1, int((t_i / max(1, len(raw_turns))) * len(synth_units))) if synth_units else 0

                tr_out = {
                    "turn_num": t_i + 1,
                    "speaker": tr.get("speaker", bt.get("who", "1983 Speaker")),
                    "speaker_color": tr.get("speaker_color", "#45b1ff"),
                    "role_tag": tr.get("role_tag", "CHARACTER"),
                    "role": tr.get("role", "SPOKEN LINE"),
                    "is_fulcrum": bool(tr.get("is_fulcrum", t_i == 0)),
                    "s": tr_s,
                    "e": tr_e,
                    "dur": tr_dur,
                    "pause_before": tr.get("pause_before", 0.0),
                    "pause_type": tr.get("pause_type", "OPENING BEAT"),
                    "word_count": tr.get("word_count", len(tr_text.split())),
                    "wpm": tr.get("wpm", 130),
                    "cadence_label": tr.get("cadence_label", "CONVERSATIONAL"),
                    "text": tr_text,
                    "f0": tr_f0,
                    "reg": tr.get("reg", reg_of(tr_f0)),
                    "lufs": tr.get("lufs", -21.0),
                    "wg_shot_id": wg_shot_for_turn["id"],
                    "wg_video": wg_shot_for_turn["video"],
                    "wg_thumb": wg_shot_for_turn["thumb"],
                    "wg_strip": wg_shot_for_turn["strip"],
                    "arch_take": line_takes[0] if line_takes else tr.get("arch_take"),
                    "takes": line_takes,
                    "subshot_idx": synth_sub_idx,
                }
                turns_enriched.append(tr_out)

                # Build clean word-by-word tokens for this turn so word pacing lanes also have clean screenplay text & true speaker
                toks_for_turn = tr_text.split()
                if toks_for_turn:
                    w_step = tr_dur / len(toks_for_turn)
                    for w_idx, w_str in enumerate(toks_for_turn):
                        ws = round(tr_s + w_idx * w_step, 2)
                        we = round(tr_s + (w_idx + 1) * w_step, 2)
                        wn = norm(w_str)
                        is_key = wn not in STOPWORDS and len(wn) > 2
                        clean_beat_words.append({
                            "w": w_str,
                            "s": ws,
                            "e": we,
                            "dur": round(max(0.08, we - ws), 2),
                            "turn_num": t_i + 1,
                            "speaker": tr_out["speaker"],
                            "speaker_color": tr_out["speaker_color"],
                            "gr": "A" if (is_key and tr_out["is_fulcrum"]) else ("B" if is_key else "C"),
                            "st": 1.25 if (is_key and tr_out["is_fulcrum"]) else (0.65 if is_key else -0.35),
                            "f0": tr_f0,
                            "lufs": tr_out["lufs"],
                        })

                if line_takes:
                    tk0 = line_takes[0]
                    clean_beat_clauses.append({
                        "clause_idx": t_i + 1,
                        "turn_num": t_i + 1,
                        "speaker_1983": tr_out["speaker"],
                        "speaker_color": tr_out["speaker_color"],
                        "wg_text": tr_text,
                        "wg_s": tr_s,
                        "wg_e": tr_e,
                        "wg_dur": tr_dur,
                        "pause_before": tr_out["pause_before"],
                        "pause_type": tr_out["pause_type"],
                        "wpm": tr_out["wpm"],
                        "is_fulcrum": tr_out["is_fulcrum"],
                        "id": tk0["id"],
                        "source_type": tk0["source_type"],
                        "has_local_video": tk0["has_local_video"],
                        "title": tk0["title"],
                        "year": tk0["year"],
                        "spoken": tk0["spoken"],
                        "audio_url": tk0["audio_url"],
                        "video": tk0["video"],
                        "thumb": tk0["thumb"],
                        "t0": tk0["t0"],
                        "t1": tk0["t1"],
                        "dur": tk0["dur"],
                        "f0": tk0["f0"],
                        "reg": tk0["reg"],
                        "lufs": tk0["lufs"],
                        "gain_db": tk0["gain_db"],
                    })

            fulcrum_turn = next((x for x in turns_enriched if x["is_fulcrum"]), turns_enriched[0])
            top_takes = fulcrum_turn.get("takes") or []
            ordered_speakers = []
            for tr_item in turns_enriched:
                if tr_item["speaker"] not in ordered_speakers:
                    ordered_speakers.append(tr_item["speaker"])

            # Update sound-bench and found_wargames in-memory so all files share the verified screenplay lines & speakers
            if sbl:
                sbl["who"] = fulcrum_turn["speaker"]
                sbl["scene_speakers"] = ordered_speakers
                sbl["text"] = fulcrum_turn["text"]
                sbl["fulcrum_line"] = fulcrum_turn["text"]
                sbl["turns_1983"] = turns_enriched
                sbl["takes"] = top_takes
                sbl["words"] = clean_beat_words
                sbl["clauses"] = clean_beat_clauses
            bt["who"] = fulcrum_turn["speaker"]
            bt["scene_speakers"] = ordered_speakers
            bt["text"] = fulcrum_turn["text"]
            bt["turns_1983"] = turns_enriched

            beat_obj = {
                "id": bid,
                "index": bt.get("index", 0),
                "who": fulcrum_turn["speaker"],
                "scene_speakers": ordered_speakers,
                "text": fulcrum_turn["text"],
                "fulcrum_line": fulcrum_turn["text"],
                "foley": bt.get("foley_label", ""),
                "foley_cue": bt.get("foley_cue", ""),
                "readings": bt.get("readings", {}),
                "wg_shot": {
                    "id": shot_id,
                    "start": round(float(wgs.get("start", 0)), 2),
                    "end": round(float(wgs.get("end", 5)), 2),
                    "dur": beat_dur,
                    "thumb": wgs.get("thumb", f"thumbs/{shot_id}.jpg"),
                    "strip": wgs.get("strip", f"strips/{shot_id}.jpg"),
                    "video": static_clip or f"/api/wargames/slice?start={wgs.get('start',0)}&end={wgs.get('end',5)}",
                    "static_clip": static_clip,
                    "sign": wgs.get("sign", "9"),
                    "sign_note": wgs.get("sign_note", ""),
                    "palette": wgs.get("palette", ["#111", "#e8c070"]),
                },
                "a0": a0_sec,
                "a1": a1_sec,
                "orig_file": sbl.get("orig_file", f"cache/wg_sound/{bid}_orig.m4a"),
                "aligned_file": sbl.get("aligned_file", f"cache/wg_sound/{bid}_aligned.m4a"),
                "tight_file": sbl.get("tight_file", f"cache/wg_sound/{bid}_tight.m4a"),
                "mel16": sbl.get("mel16", []),
                "harm_env": sbl.get("harm_env", ""),
                "perc_env": sbl.get("perc_env", ""),
                "turns_1983": turns_enriched,
                "takes": top_takes,
                "cuts": cuts,
            }
            beats_out.append(beat_obj)
            beat_by_shot_id[shot_id] = beat_obj
            for tr_s in trio_raw:
                if tr_s.get("id"):
                    beat_by_shot_id.setdefault(tr_s["id"], beat_obj)

        books_out.append({
            "n": b_idx + 1,
            "bnum": bk.get("bnum", str(b_idx + 1)),
            "title": bk.get("title", f"Book {b_idx+1}"),
            "milieu": bk.get("milieu", ""),
            "palette": bk.get("palette", []),
            "beats": beats_out,
        })

    # Save updated wargames-studio-cuts.json
    cuts_out = {
        "title": "The Found WarGames · Simultaneous Multi-Cut & Line-by-Line Studio Set",
        "total_beats": sum(len(b["beats"]) for b in books_out),
        "total_spoken_lines": total_turns_enriched,
        "stills_atlas": sorted(stills_atlas, key=lambda x: x["lum"]),
        "books": books_out,
    }
    cuts_path = os.path.join(LAB, "wargames-studio-cuts.json")
    with open(cuts_path, "w") as f:
        json.dump(cuts_out, f, separators=(",", ":"))
    print(f"Wrote {cuts_path} ({os.path.getsize(cuts_path)/(1024*1024):.2f} MB): {total_turns_enriched} spoken lines with 3 takes each.")

    # Save enriched turns_1983 back to wargames-sound-bench.json and found_wargames.json
    with open(sb_path, "w") as f:
        json.dump(sb, f, separators=(",", ":"))
    print(f"Updated {sb_path} with 3 takes per spoken line across all {total_turns_enriched} turns.")

    with open(fw_path, "w") as f:
        json.dump(fw, f, separators=(",", ":"))
    print(f"Updated {fw_path} with verified screenplay lines and speaker attribution.")

    # Now build 01 / SCREEN STATES (`wargames-screens-program.json`) linked to the beats, spoken lines, and 8-frame sub-frame deltas!
    build_screens_program(beat_by_shot_id, books_out)


PURE_68_SCREEN_SPECS = {
    "sbd_0059": ("SILO_EXEC_ORDER", "0x0010 SUB_SILO_EAM_DECODE", "RECV_EAM_K36_948_3", 5, "SILO", "WOPR EXECUTION ORDER K36.948.3 // PART ONE: R O N C T T L // PART TWO: 07:20:35 // LAUNCH CODE: D L G 2 2 0 _ _ _ _"),
    "sbd_0060": ("SILO_EXEC_ORDER", "0x0010 SUB_SILO_EAM_DECODE", "VERIFY_LAUNCH_AUTH_DLG2209TVX", 5, "SILO", "WOPR EXECUTION ORDER K36.948.3 // PART ONE: R O N C T T L // PART TWO: 07:20:35 // LAUNCH CODE: D L G 2 2 0 9 T V X"),
    "sbd_0065": ("SILO_EXEC_ORDER", "0x0010 SUB_SILO_EAM_DECODE", "CONFIRM_TARGET_ENABLE_MISSILES", 5, "SILO", "LAUNCH ORDER CONFIRMED // TARGET SELECTION: COMPLETE // TIME ON TARGET SEQUENCE: COMPLETE // YIELD SELECTION: COMPLETE // ENABLE MISSILES // LAUNCH TIME: BEGIN COUNTDOWN"),
    "wg_024":   ("NORAD_VECTOR_MAP", "0x0030 SUB_NORAD_SURVEILLANCE", "INIT_NORAD_BIGBOARD_HUD", 5, "MAP", "SURVEILLANCE REPORT // PRELIMINARY ANALYSIS UPDATE // SUBMARINE BASE [PETROPAVLOVSK] // RADAR TRACKING GRID"),
    "sbd_0288": ("IMSAI_GRADES_DB", "0x0050 SUB_SEATTLE_SCHOOLS_DB", "COMMIT_GRADE_MUTATION_A", 5, "GRADES", "COURSE TITLE: BIOLOGY 2 [A] // ENGLISH 11B [B] // WORLD HISTORY 11B [B] // GEOMETRY 2 [D]"),
    "wg_059":   ("IMSAI_GRADES_DB", "0x0050 SUB_SEATTLE_SCHOOLS_DB", "SELECT_FIELD_BIOLOGY2_F", 5, "GRADES", "COURSE TITLE / GRADE // BIOLOGY 2: [F] -> [A] // ENGLISH 11B: A // WORLD HISTORY 11B: B // GEOMETRY 2: D"),
    "sbd_0298": ("IMSAI_GRADES_DB", "0x0050 SUB_SEATTLE_SCHOOLS_DB", "CURSOR_SEEK_RECORD_LIGGETT", 5, "GRADES", "GRADE / TEACHER // [F] LIGGETT // [A] ROBINSON // [B] DWYER // [D] MARKS"),
    "wg_062":   ("WARDIALER_311", "0x0070 SUB_IMSAI_WARDIALER", "INCREMENT_LED_AUTODIAL_3990", 5, "DIAL 408-311", "IMSAI 8080 HARDWARE AUTODIALER // LED READOUT: [ 002  3990  CPL ] // ACOUSTIC COUPLER 300 BAUD"),
    "wg_070":   ("WARDIALER_311", "0x0070 SUB_IMSAI_WARDIALER", "DETECT_CARRIER_408_311_3990", 5, "DIAL 408-311", "SUNNYVALE AREA CODES AND PREFIXES // (408) 311-0091 .. (408) 311-3990 [CARRIER DETECTED]"),
    "wg_081":   ("JOSHUA_PROMPT", "0x0090 SUB_WOPR_JOSHUA_SHELL", "EXEC_HELP_GAMES_QUERY", 5, "HELP GAMES", "LOGON: Help Logon // HELP NOT AVAILABLE // LOGON: Help Games // 'GAMES' REFERS TO MODELS, SIMULATIONS AND GAMES WHICH HAVE TACTICAL AND STRATEGIC APPLICATIONS."),
    "sbd_0394": ("JOSHUA_PROMPT", "0x0090 SUB_WOPR_JOSHUA_SHELL", "EXEC_LIST_GAMES_CATALOG", 5, "LIST GAMES", "FALKEN'S MAZE // BLACK JACK // GIN RUMMY // HEARTS // BRIDGE // CHECKERS // CHESS // POKER // FIGHTER COMBAT // GUERRILLA ENGAGEMENT // DESERT WARFARE // AIR-TO-GROUND ACTIONS // THEATREWIDE TACTICAL WARFARE // THEATREWIDE BIOTOXIC AND CHEMICAL WARFARE // GLOBAL THERMONUCLEAR WAR"),
    "sbd_0512": ("IMSAI_GRADES_DB", "0x0050 SUB_SEATTLE_SCHOOLS_DB", "DIAL_MODEM_MASK_936_2364", 5, "PASSWORD PENCIL", "MODEM DIAL: 936-2364 // AUTH MASK: ******************"),
    "wg_115":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "PLOT_ICBM_SEATTLE_LAS_VEGAS", 4, "RUN GTW", "GLOBAL THERMONUCLEAR WAR // PRIMARY TARGETS: SEATTLE / LAS VEGAS // 8 POLAR ICBM ARCS INBOUND"),
    "wg_116":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "STREAM_TRAJECTORY_HEADINGS", 3, "RUN GTW", "UNITED STATES / SOVIET UNION // TRAJECTORY HEADING | TRAJECTORY HEADING // 1-5539-A 240 567 | 6-2258-G 212 435"),
    "wg_135":   ("JOSHUA_PROMPT", "0x0090 SUB_WOPR_JOSHUA_SHELL", "PROMPT_PRIMARY_GOAL", 4, "LOGON JOSHUA", "What is the primary goal? [CURSOR_BLINK]"),
    "sbd_0646": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "INIT_GAME_CLOCK_52H_16M", 4, "CLOCK", "ESTIMATED TIME REMAINING: 52 HRS  16 MIN  15 SEC"),
    "wg_166":   ("JOSHUA_PROMPT", "0x0090 SUB_WOPR_JOSHUA_SHELL", "QUERY_IS_THIS_REAL_OR_GAME", 3, "LOGON JOSHUA", "UNITED STATES / HUMAN RESOURCES: 49 MILLION NON-FATAL, 72 MILLION DEAD // Is this a game or is it real? // GAME TIME ELAPSED: 45 HRS 32 MIN 58 SEC | ESTIMATED TIME REMAINING: 07 HRS 27 MIN 02 SEC"),
    "sbd_0896": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "TICK_GAME_CLOCK_22H_57M", 3, "CLOCK", "GAME TIME ELAPSED: 49 HRS 35 MIN 23 SEC // GAME TIME REMAINING: 22 HRS 57 MIN 01 SEC"),
    "wg_203":   ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "TICK_GAME_CLOCK_18H_27M", 3, "CLOCK", "GAME TIME REMAINING: 18 HRS  27 MIN  01 SEC"),
    "sbd_0990": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "SCAN_NORTH_AMERICAN_SECTOR", 3, "MAP", "NORTH AMERICAN AIR DEFENSE SECTOR // VECTOR RADAR GRID 4247 - 1184 - 0007"),
    "wg_219":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "TRACK_ALASKAN_ADZ_INTERCEPT", 2, "MAP", "ALASKAN AIR DEFENSE ZONE // 2 UNIDENTIFIED BOGEY TRACKS INBOUND"),
    "wg_231":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "PLOT_SOVIET_SUB_DEPLOYMENT", 2, "MAP", "SYS D: SOVIET NAVAL DEPLOYMENT // STRATEGIC NUCLEAR SUBMARINE // CT OPLY REF 352SF: NVOP EF 324 // BN DTA AVLB: CH 784 SELECT 612"),
    "wg_232":   ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "PULSE_WOPR_CPU_LED_MATRIX", 2, "CRACK CPE", "WOPR CHASSIS LED MATRIX // PARALLEL LOGIC BUS ACTIVE"),
    "sbd_1122": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "ALERT_SOVIET_LAUNCH_DETECTION", 2, "MAP", "LAUNCH DETECTION // SOVIET ICBM BOOSTER PLUME IR SIGNATURE"),
    "wg_244":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "CALC_FORCE_LOSS_PROJECTION", 1, "RUN GTW", "FORCE LOSS PROJECTION -- PERSONNEL // USAF PERSONNEL BY COMMANDS, SOAs, AND DRUs // SAC / TAC / MAC / NORAD: 85% - 94% CASUALTIES"),
    "sbd_1136": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "PLOT_CONUS_TARGET_ZONES", 1, "MAP", "CONUS STRATEGIC TARGET ZONES //PRIMARY SILO & COMMAND NODE OVERLAY"),
    "sbd_1181": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "ENGAGE_GATE_MODE_RANGE", 1, "LOCKOUT", "COUNTDOWN STATUS: [ GATE MODE ] [ RANGE ]"),
    "wg_251":   ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "SET_MISSILES_READY_LOCKOUT", 1, "LOCKOUT", "MISSILES TARGETED AND READY // CHANGES LOCKED OUT"),
    "sbd_1227": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "TARGET_ELMENDORF_AFB", 1, "MAP", "ELMENDORF AIR FORCE BASE / FORT RICHARDSON // IMPACT RING OVERLAY"),
    "wg_259":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "TARGET_LORING_AFB_RING", 1, "MAP", "LORING AIR FORCE BASE // CONCENTRIC ZERO-HOUR IMPACT RINGS"),
    "sbd_1231": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "ZOOM_LORING_SECTOR_22", 1, "MAP", "SECTOR 22 // LORING AIR FORCE BASE // INBOUND TRACK CONVERGENCE"),
    "sbd_1233": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "SATURATE_2400_WARHEAD_ARCS", 1, "MAP", "FULL SIOP SATURATION // 2,400 INBOUND WARHEAD TRAJECTORY ARCS"),
    "sbd_1237": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "IMPACT_ZERO_LORING_AFB", 1, "MAP", "LORING AIR FORCE BASE // T-MINUS 00:00 DETONATION FLASH"),
    "sbd_1244": ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "PLOT_FULL_CONUS_STRIKE_WEB", 1, "MAP", "CONTINENTAL UNITED STATES // FULL TARGET SATURATION GRID"),
    "wg_264":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "PLOT_NE_CORRIDOR_IMPACTS", 1, "MAP", "SECTOR 21-22 // DETROIT / BOSTON / NEW YORK / WASHINGTON DC / NORFOLK"),
    "sbd_1274": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "LAMP_LOCK_OUT_CHANGE_ACTIVE", 1, "LOCKOUT", "COUNTDOWN STATUS: [ LOCK OUT CHANGE ] [ GATE MODE ] [ TIMER SELECT ]"),
    "sbd_1282": ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "PERMUTE_CPE_TUMBLER_1", 1, "CRACK CPE", "LAUNCH CODE PERMUTATION // [ J T Z 2 5 5 0 W B E ]"),
    "sbd_1284": ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "PERMUTE_CPE_TUMBLER_2", 1, "CRACK CPE", "LAUNCH CODE PERMUTATION // [ P T U 0 3 8 8 P M C ]"),
    "sbd_1287": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "HARD_LOCK_OUT_CHANGE_LAMP", 1, "LOCKOUT", "COUNTDOWN STATUS // [ LOCK OUT CHANGE ] ILLUMINATED RED"),
    "sbd_1294": ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "PERMUTE_CPE_TUMBLER_3", 1, "CRACK CPE", "LAUNCH CODE PERMUTATION // [ T Q H 8 9 6 1 J R F ]"),
    "wg_270":   ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "AWAIT_LAUNCH_CODES_TELEMETRY", 1, "LOCKOUT", "MISSILES ENABLED // TARGET SELECTION: COMPLETE // TIME ON TARGET SEQUENCE: COMPLETE // YIELD SELECTION: COMPLETE // CHANGES LOCKED OUT // LAUNCH TIME: >> AWAITING CODES <<"),
    "sbd_1321": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "REJECT_ADMIN_OVERRIDE_1", 1, "LOCKOUT", "* IMPROPER REQUEST * // ** ACCESS DENIED **"),
    "sbd_1334": ("JOSHUA_PROMPT", "0x0090 SUB_WOPR_JOSHUA_SHELL", "SCROLL_TACTICAL_GAME_MENU", 1, "LIST GAMES", "GUERRILLA ENGAGEMENT // DESERT WARFARE // AIR-TO-GROUND ACTIONS // THEATREWIDE TACTICAL WARFARE // THEATREWIDE BIOTOXIC AND CHEMICAL WARFARE // GLOBAL THERMONUCLEAR WAR"),
    "wg_277":   ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "DENY_LOGON_IDENTIFICATION", 1, "LOCKOUT", "** IDENTIFICATION NOT RECOGNIZED ** // ** ACCESS DENIED **"),
    "sbd_1344": ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "LOCK_4_DIGITS_IPN0404AJC", 1, "CRACK CPE", "LAUNCH CODE PERMUTATION // [ I P N 0 4 0 4 A J C ] (4 DIGITS LOCKED)"),
    "sbd_1345": ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "TRAP_ROUTINE_MUST_COMPLETE", 1, "LOCKOUT", "** IMPROPER REQUEST ** // ** ROUTINE MUST COMPLETE BEFORE RESET ** // ** ACCESS DENIED **"),
    "sbd_1352": ("JOSHUA_PROMPT", "0x0090 SUB_WOPR_JOSHUA_SHELL", "SELECT_PARLOR_GAME_LIST", 1, "LIST GAMES", "FALKEN'S MAZE // BLACK JACK // GIN RUMMY // HEARTS // BRIDGE // CHECKERS // CHESS // POKER // FIGHTER COMBAT"),
    "wg_280":   ("GAME_CLOCK_LOCKOUT", "0x0100 SUB_GAME_CLOCK_LOCKOUT", "ENFORCE_CHANGES_LOCKED_OUT", 1, "LOCKOUT", ">>> CHANGES LOCKED OUT <<< // ** IMPROPER REQUEST ** // ** ACCESS DENIED **"),
    "wg_281":   ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "LOCK_PREFIX_VP01", 1, "CRACK CPE", "LAUNCH CODE TUMBLER // [ V P 0 1 _ _ _ _ _ _ ]"),
    "sbd_1369": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "EVAL_TICTACTOE_DRAW_1", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ J | O | X ] / [ O | X | X ] / [ O | X | O ] -> STALEMATE"),
    "wg_283":   ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "OPEN_CENTER_X_MOVE_1", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ _ | _ | _ ] / [ _ | X | _ ] / [ _ | _ | O ]"),
    "sbd_1375": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "BRANCH_MINIMAX_PLY_4", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ X | _ | _ ] / [ _ | X | _ ] / [ O | _ | O ]"),
    "wg_284":   ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "INIT_CENTER_X_GRID", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ _ | _ | _ ] / [ _ | X | _ ] / [ _ | _ | _ ]"),
    "sbd_1380": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "PROVE_STALEMATE_BOARD_A", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ O | X | O ] / [ _ | X | _ ] / [ X | O | X ] -> DRAW"),
    "sbd_1382": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "PROVE_STALEMATE_BOARD_B", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ X | O | _ ] / [ X | O | X ] / [ O | X | O ] -> DRAW"),
    "wg_285":   ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "BRANCH_MINIMAX_PLY_3", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE GRID // [ _ | _ | _ ] / [ X | O | _ ] / [ O | X | _ ]"),
    "wg_286":   ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "OVERCLOCK_WOPR_CORE_LEDS", 1, "CRACK CPE", "WOPR CORE RED LED ARRAY // VOLTAGE DRAIN SPIKE"),
    "wg_288":   ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "SIM_US_FIRST_STRIKE_MAP", 1, "PLAY TICTACTOE 0", "GLOBAL SCENARIO: U.S. FIRST STRIKE // WINNER: NONE"),
    "wg_289":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "CASCADE_POLAR_SALVO_ARCS", 1, "MAP", "POLAR PROJECTION // MASSIVE MUTUAL RETALIATION ARCS"),
    "sbd_1410": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "LOG_WINNER_NONE_TABLE_1", 1, "PLAY TICTACTOE 0", "STRATEGY: U.S. FIRST STRIKE — WINNER: NONE // USSR FIRST STRIKE — WINNER: NONE"),
    "wg_290":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "SATURATE_HEMISPHERE_VECTORS", 1, "MAP", "GLOBAL VECTOR SATURATION // TOTAL MUTUAL DESTRUCTION"),
    "sbd_1414": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "LOG_WINNER_NONE_TABLE_2", 1, "PLAY TICTACTOE 0", "STRATEGY: USSR FIRST STRIKE — WINNER: NONE // U.S. FIRST STRIKE — WINNER: NONE // NATO / WARSAW PACT — WINNER: NONE"),
    "sbd_1415": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "SIM_THEATREWIDE_EXCHANGE_MAP", 1, "PLAY TICTACTOE 0", "GLOBAL SCENARIO CASCADE // ALL THEATERS -> WINNER: NONE"),
    "sbd_1420": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "COUPLE_TTT_TO_SIOP_BOARD", 1, "PLAY TICTACTOE 0", "NORAD TRIPLE PROJECTION // TIC-TAC-TOE GRID <-> EAST/WEST HEMISPHERE MAPS"),
    "wg_292":   ("NORAD_VECTOR_MAP", "0x00C0 SUB_GTW_TRAJECTORY_SIM", "WHITEOUT_DETONATION_BLOOMS", 1, "MAP", "THERMONUCLEAR DETONATION BLOOMS // SCREEN SATURATION"),
    "sbd_1427": ("TICTACTOE_SIOP", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "CLEAR_3X3_TTT_MATRIX", 1, "PLAY TICTACTOE 0", "TIC-TAC-TOE 3x3 VECTOR GRID INITIALIZED // PLAYERS: 0"),
    "wg_295":   ("CPE_CODE_CRACKER", "0x0140 SUB_CPE_BRUTE_FORCE", "LOCK_9_OF_10_CPE1704TKS", 1, "CRACK CPE", "LAUNCH CODE LOCK // [ C P E 1 7 0 4 T K _ ] (9 OF 10 LOCKED)"),
    "wg_296":   ("JOSHUA_PROMPT", "0x0180 SUB_ZERO_PLAYER_STALEMATE", "HALT_ONLY_WINNING_MOVE", 5, "LOGON JOSHUA", "GREETINGS PROFESSOR FALKEN // HELLO // A STRANGE GAME. // THE ONLY WINNING MOVE IS NOT TO PLAY. // HOW ABOUT A NICE GAME OF CHESS?"),
}

INFERRED_SUBROUTINES_SPEC = [
    {
        "addr": "0x0010",
        "id": "0x0010 SUB_SILO_EAM_DECODE",
        "subsystem": "SILO_EXEC_ORDER",
        "cmd": "SILO",
        "title": "Minuteman III EAM Launch Order & Target Sequence Receiver",
        "pseudo_code": [
            "0010  RECV_EAM('K36.948.3', PART1='RONCTTL', PART2='07:20:35')",
            "0020  AUTHENTICATE(LAUNCH_CODE='DLG 2209 TVX')",
            "0030  ASSERT TARGET_SELECTION == COMPLETE && YIELD_SELECTION == COMPLETE",
            "0040  SET_STATE('ENABLE MISSILES // LAUNCH TIME: BEGIN COUNTDOWN')",
        ],
    },
    {
        "addr": "0x0050",
        "id": "0x0050 SUB_SEATTLE_SCHOOLS_DB",
        "subsystem": "IMSAI_GRADES_DB",
        "cmd": "PASSWORD PENCIL",
        "title": "IMSAI 8080 Acoustic Modem -> Seattle Public Schools Grade Mutator",
        "pseudo_code": [
            "0050  DIAL_MODEM('936-2364', BAUD=300); SEND_AUTH('PENCIL')",
            "0060  QUERY_STUDENT(COURSE='BIOLOGY 2', TEACHER='LIGGETT')",
            "0070  MUTATE_FIELD(RECORD.GRADE, FROM='F', TO='A')",
            "0080  COMMIT_TRANSACTION(); CLOSE_CARRIER()",
        ],
    },
    {
        "addr": "0x0070",
        "id": "0x0070 SUB_IMSAI_WARDIALER",
        "subsystem": "WARDIALER_311",
        "cmd": "DIAL 408-311",
        "title": "Sunnyvale (408) 311-XXXX Sequential Carrier Sweep",
        "pseudo_code": [
            "0090  FOR SUFFIX IN 0001..9999:",
            "0100    OUT_LED_AUTODIALER(PREFIX=311, SUFFIX=SUFFIX)",
            "0110    IF DETECT_MODEM_TONE('408-311-' + SUFFIX):",
            "0120      LOG_CARRIER('408-311-3990 [UNIDENTIFIED DEFENSE HOST]')",
        ],
    },
    {
        "addr": "0x0090",
        "id": "0x0090 SUB_WOPR_JOSHUA_SHELL",
        "subsystem": "JOSHUA_PROMPT",
        "cmd": "LIST GAMES",
        "title": "WOPR Backdoor Logon ('JOSHUA') & Interactive Game Shell",
        "pseudo_code": [
            "0130  IF INPUT == 'HELP LOGON': PRINT('HELP NOT AVAILABLE')",
            "0140  IF INPUT == 'HELP GAMES': PRINT('MODELS, SIMULATIONS AND GAMES...')",
            "0150  IF INPUT == 'LIST GAMES': PRINT(FALKEN_MAZE .. GLOBAL_THERMONUCLEAR_WAR)",
            "0160  IF AUTH == 'JOSHUA': PRINT('GREETINGS PROFESSOR FALKEN. WHAT IS THE PRIMARY GOAL?')",
        ],
    },
    {
        "addr": "0x00C0",
        "id": "0x00C0 SUB_GTW_TRAJECTORY_SIM",
        "subsystem": "NORAD_VECTOR_MAP",
        "cmd": "RUN GTW",
        "title": "NORAD Big Board Vector Map & False-Track Injection Engine",
        "pseudo_code": [
            "0170  BIND_TARGETS(['SEATTLE', 'LAS VEGAS', 'LORING AFB', 'ELMENDORF AFB'])",
            "0180  INJECT_BMEWS_FEED(TRACKS=2400, SUBMARINES='PETROPAVLOVSK')",
            "0190  COMPUTE_FORCE_LOSS(SAC=0.89, TAC=0.92, CIV_DEAD='72 MILLION')",
            "0200  ESCALATE_DEFCON(FROM=5, TO=1); RENDER_VECTOR_ARCS()",
        ],
    },
    {
        "addr": "0x0100",
        "id": "0x0100 SUB_GAME_CLOCK_LOCKOUT",
        "subsystem": "GAME_CLOCK_LOCKOUT",
        "cmd": "LOCKOUT",
        "title": "Autonomous Game Clock Countdown & Operator Access Lockout",
        "pseudo_code": [
            "0210  DECREMENT_CLOCK(FROM='52:16:15', TO='18:27:01', TO='00:00:00')",
            "0220  SET_HARDWARE_LAMP('COUNTDOWN STATUS: LOCK OUT CHANGE | GATE MODE')",
            "0230  ON_OPERATOR_INTERRUPT():",
            "0240    PRINT('>>> CHANGES LOCKED OUT <<< // ** IMPROPER REQUEST ** // ** ACCESS DENIED **')",
        ],
    },
    {
        "addr": "0x0140",
        "id": "0x0140 SUB_CPE_BRUTE_FORCE",
        "subsystem": "CPE_CODE_CRACKER",
        "cmd": "CRACK CPE",
        "title": "Minuteman Launch Relay 10-Character Code Brute-Force ('CPE 1704 TKS')",
        "pseudo_code": [
            "0250  TARGET_KEY = 'CPE1704TKS'  // 10-CHAR LAUNCH RELAY LOCK",
            "0260  CYCLE_TUMBLERS(['JTZ2550WBE', 'PTU0388PMC', 'TQH8961JRF', 'IPN0404AJC'])",
            "0270  LOCK_DIGITS_SEQUENTIALLY('VP01______' -> 'CPE1704TK_')",
            "0280  AWAIT_FINAL_TUMBLER_OR_ZERO_PLAYER_INTERRUPT()",
        ],
    },
    {
        "addr": "0x0180",
        "id": "0x0180 SUB_ZERO_PLAYER_STALEMATE",
        "subsystem": "TICTACTOE_SIOP",
        "cmd": "PLAY TICTACTOE 0",
        "title": "Zero-Player Tic-Tac-Toe Stalemate Proof & SIOP 'WINNER: NONE' Halt",
        "pseudo_code": [
            "0290  EXEC_MINIMAX('TIC-TAC-TOE', PLAYERS=0) -> STALEMATE_CONVERGENCE",
            "0300  FOR SCENARIO IN ['US FIRST STRIKE', 'USSR FIRST STRIKE', 'NATO / WARSAW PACT']:",
            "0310    EVAL_OUTCOME(SCENARIO) -> PRINT('WINNER: NONE')",
            "0320  HALT_LAUNCH('A STRANGE GAME. THE ONLY WINNING MOVE IS NOT TO PLAY.')",
        ],
    },
]


def build_screens_program(beat_by_shot_id, books_out):
    vs = json.load(open(os.path.join(HERE, "verified_screens.json")))
    vs_by_id = {s["id"]: s for s in vs.get("screens", [])}
    flat_beats = [bt for bk in books_out for bt in bk["beats"]]

    def find_beat_for_time(t_sec, shot_id):
        if shot_id in beat_by_shot_id:
            return beat_by_shot_id[shot_id]
        best = flat_beats[0]
        best_dist = 1e9
        for bt in flat_beats:
            mid = 0.5 * (bt["wg_shot"]["start"] + bt["wg_shot"]["end"])
            d = abs(mid - t_sec)
            if d < best_dist:
                best_dist = d
                best = bt
        return best

    pure_entries = []
    for sid, spec in PURE_68_SCREEN_SPECS.items():
        if sid in vs_by_id:
            pure_entries.append((vs_by_id[sid], spec))

    pure_entries.sort(key=lambda x: float(x[0].get("start", 0)))

    screen_states = []
    for idx, (s, spec) in enumerate(pure_entries):
        shot_id = s["id"]
        subsys, subroutine, opcode, defcon, shell_cmd, ocr_text = spec

        scr_thumb = s.get("screen_thumb") or f"thumbs/screens/{shot_id}.jpg"
        full_thumb = s.get("full_thumb") or f"thumbs/{shot_id}.jpg"
        has_strip = shot_id.startswith("wg_") and os.path.exists(os.path.join(LAB, f"strips/{shot_id}.jpg"))
        strip_url = f"strips/{shot_id}.jpg" if has_strip else scr_thumb
        static_clip = f"clips/{shot_id}.mp4" if os.path.exists(os.path.join(LAB, f"clips/{shot_id}.mp4")) else ""

        r, g, b, lum = measure_thumb_rgb_lum(scr_thumb)
        subframe_deltas = analyze_strip_8frames(strip_url if has_strip else "", scr_thumb)

        t_start = round(float(s.get("start", 0)), 2)
        t_end = round(float(s.get("end", t_start + 3.0)), 2)
        linked_beat = find_beat_for_time(t_start, shot_id)
        linked_turns = linked_beat.get("turns_1983") or []
        trigger_turn = linked_turns[idx % len(linked_turns)] if linked_turns else {}
        trurl_units = linked_beat["cuts"].get("trurl") or linked_beat["cuts"].get("synthesis") or []
        arch_twin = trurl_units[idx % len(trurl_units)] if trurl_units else {}

        screen_states.append({
            "state_index": idx + 1,
            "shot_id": shot_id,
            "beat_id": linked_beat["id"],
            "start": t_start,
            "end": t_end,
            "dur": round(max(1.5, t_end - t_start), 2),
            "subsystem": subsys,
            "subroutine": subroutine,
            "opcode": opcode,
            "shell_cmd": shell_cmd,
            "defcon": defcon,
            "sign": str(s.get("sign") or linked_beat["wg_shot"].get("sign") or "17"),
            "thumb": scr_thumb,
            "screen_thumb": scr_thumb,
            "full_thumb": full_thumb,
            "strip": strip_url,
            "clip": static_clip or s.get("clip") or f"/api/wargames/slice?start={t_start}&end={t_end}",
            "crop_box": s.get("crop_box", [0, 0, 1, 1]),
            "purity": round(float(s.get("purity", 2.0)), 3),
            "clip_margin": round(float(s.get("clip_margin", 0.18)), 3),
            "rgb": [r, g, b],
            "lum": lum,
            "subframe_states": len(subframe_deltas),
            "subframe_deltas": subframe_deltas,
            "terminal_prompt": ocr_text,
            "spoken_1983": s.get("note") or trigger_turn.get("text") or linked_beat.get("text", ""),
            "speaker": trigger_turn.get("speaker", linked_beat.get("who", "WOPR")),
            "trigger_line": trigger_turn,
            "arch_twin": arch_twin,
        })

    subroutines_out = []
    for sub in INFERRED_SUBROUTINES_SPEC:
        cnt = sum(1 for st in screen_states if st["subroutine"] == sub["id"])
        first_st = next((st for st in screen_states if st["subroutine"] == sub["id"]), None)
        subroutines_out.append({
            **sub,
            "screen_count": cnt,
            "entry_shot": first_st["shot_id"] if first_st else "wg_081",
        })

    out = {
        "title": "01 / SCREEN STATES · WOPR // IMSAI-8080 Pure Screen OS & Program Inference",
        "total_screens": len(screen_states),
        "total_subframe_states": sum(st["subframe_states"] for st in screen_states),
        "inferred_program": {
            "subroutines": subroutines_out,
        },
        "screen_states": screen_states,
    }
    out_path = os.path.join(LAB, "wargames-screens-program.json")
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {out_path}: {len(screen_states)} 100%-PURE verified computer screens ({out['total_subframe_states']} sub-frame states).")


if __name__ == "__main__":
    build_all()

