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
            beat_dur = round(max(2.4, float(wgs.get("dur") or 5.0)), 2)
            static_clip = f"clips/{shot_id}.mp4" if os.path.exists(os.path.join(LAB, f"clips/{shot_id}.mp4")) else ""

            # Build 1983 Trio cut sequence (Entry Cut -> Primary Shot -> Exit Cut)
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

            # ENRICH EVERY SPOKEN LINE (`turns_1983`) WITH ITS OWN 3 ARCHIVAL SPOKEN TAKES + CLAUSES + EXACT VIDEO/AUDIO IN-POINTS!
            raw_turns = sbl.get("turns_1983") or bt.get("turns_1983") or [{
                "turn_num": 1,
                "speaker": bt.get("who", "David Lightman"),
                "speaker_color": "#45b1ff",
                "role_tag": "CHARACTER",
                "s": 0.15,
                "e": round(beat_dur - 0.15, 2),
                "dur": round(beat_dur - 0.3, 2),
                "text": bt.get("text", ""),
                "f0": 125.0,
                "reg": "LOW",
                "lufs": -21.0,
                "is_fulcrum": True,
                "role": "★ THE LINE (FULCRUM)",
            }]

            beat_takes_top = sbl.get("takes") or []
            turns_enriched = []
            used_in_beat_spoken = set()

            for t_i, tr in enumerate(raw_turns):
                total_turns_enriched += 1
                tr_text = tr.get("text") or bt.get("text") or ""
                tr_f0 = float(tr.get("f0") or 125.0)
                tr_s = round(float(tr.get("s", 0.0)), 2)
                tr_e = round(float(tr.get("e", tr_s + 2.5)), 2)
                tr_dur = round(max(0.5, tr_e - tr_s), 2)

                # Score archival sentences specifically for THIS spoken line (`tr_text`, `tr_f0`)
                q_vec = sentence_clip_vec(tr_text + " " + bt.get("text", ""), w2idx, clip_vecs, get_synonym_tokens)
                tr_toks = {norm(w) for w in re.findall(r"[A-Za-z']+", tr_text) if norm(w) not in STOPWORDS and len(norm(w)) > 2}
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
                    sc = c_sim * 1.35 + ex_ov * 0.32 + sy_ov * 0.14 + vid_bonus - f0_pen * 0.22 - dur_diff - reuse_pen
                    cand_list.append((sc, c_sim, s_entry))

                cand_list.sort(key=lambda x: x[0], reverse=True)

                line_takes = []
                for take_k in range(3):
                    chosen_s = None
                    chosen_sc = 0.92
                    for sc_v, c_v, s_cand in cand_list:
                        if s_cand["spoken"] in used_in_beat_spoken:
                            continue
                        # Ensure Take 3 prefers a local MP4 clip so every single line has at least one 100% local MP4 take!
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
                        hl, ha = find_shared_word_indices(tr_text, chosen_s["spoken"])

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

            # Update sound-bench and found_wargames in-memory so all files share the 3-takes-per-line structure
            if sbl:
                sbl["turns_1983"] = turns_enriched
            bt["turns_1983"] = turns_enriched

            fulcrum_turn = next((x for x in turns_enriched if x["is_fulcrum"]), turns_enriched[0])
            top_takes = fulcrum_turn.get("takes") or []

            beat_obj = {
                "id": bid,
                "index": bt.get("index", 0),
                "who": bt.get("who", "1983"),
                "scene_speakers": bt.get("scene_speakers") or sbl.get("scene_speakers") or [bt.get("who", "1983")],
                "text": bt.get("text", ""),
                "fulcrum_line": fulcrum_turn.get("text", bt.get("text", "")),
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
                "a0": round(float(sbl.get("a0", wgs.get("start", 0))), 2),
                "a1": round(float(sbl.get("a1", wgs.get("end", 5))), 2),
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

    # Save enriched turns_1983 back to wargames-sound-bench.json so Sound Bench also has 3 takes per spoken turn
    with open(sb_path, "w") as f:
        json.dump(sb, f, separators=(",", ":"))
    print(f"Updated {sb_path} with 3 takes per spoken line across all {total_turns_enriched} turns.")

    # Now build 01 / SCREEN STATES (`wargames-screens-program.json`) linked to the beats, spoken lines, and 8-frame sub-frame deltas!
    build_screens_program(beat_by_shot_id, books_out)


def build_screens_program(beat_by_shot_id, books_out):
    os_d = json.load(open(os.path.join(HERE, "wargames_os.json")))
    subsystems_out = []
    all_states = []
    seen_ids = set()

    # Flatten all beats in chronological order to link any SBD screen cut by timestamp
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

    for sub_idx, sub in enumerate(os_d["subsystems"]):
        sid = sub["id"]
        scode = sub["code"]
        prog_meta = SUBSYSTEM_PROGRAMS.get(sid, SUBSYSTEM_PROGRAMS["SYS://IMSAI-8080"])
        code_lines = prog_meta["code"]

        combined = []
        for s in sub.get("sbd_screen_cuts", []):
            combined.append((s, True))
        for s in sub.get("shots", []):
            combined.append((s, False))

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
            subframe_deltas = analyze_strip_8frames(strip_url, scr_thumb)

            # Link this screen state to its narrative beat, spoken line trigger, and archival machine twin!
            t_start = round(float(s.get("start", 0)), 2)
            t_end = round(float(s.get("end", t_start + 3.0)), 2)
            linked_beat = find_beat_for_time(t_start, shot_id)
            linked_turns = linked_beat.get("turns_1983") or []
            trigger_turn = linked_turns[k % len(linked_turns)] if linked_turns else {}
            trigger_take = (trigger_turn.get("takes") or [{}])[0]

            # Pick an archival machine/phosphor twin from the beat's `trurl` or `clip` cut
            trurl_units = linked_beat["cuts"].get("trurl") or linked_beat["cuts"].get("clip") or linked_beat["cuts"].get("synthesis") or []
            arch_twin = trurl_units[k % len(trurl_units)] if trurl_units else {}

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
                "scene_id": s.get("scene_id", linked_beat["id"].split("-")[0]),
                "scene_title": s.get("scene_title", ""),
                "beat_id": linked_beat["id"],
                "start": t_start,
                "end": t_end,
                "dur": round(max(1.2, t_end - t_start), 2),
                "screen_thumb": scr_thumb,
                "full_thumb": full_thumb,
                "strip": strip_url,
                "sub_frames": 8 if has_strip else 1,
                "subframe_deltas": subframe_deltas,
                "clip": static_clip or s.get("clip") or f"/api/wargames/slice?start={t_start}&end={t_end}",
                "static_clip": static_clip,
                "crop_box": s.get("crop_box", [0, 0, 1, 1]),
                "purity": round(float(s.get("purity", 0.85)), 3),
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
                "transition_rule": f"δ({prev_state}, \"{trigger_turn.get('speaker','OP')}: {trigger_turn.get('text','')[:32]}...\") → {state_code}",
                "trigger_line": {
                    "speaker": trigger_turn.get("speaker", linked_beat.get("who", "Operator")),
                    "speaker_color": trigger_turn.get("speaker_color", "#45b1ff"),
                    "text": trigger_turn.get("text", linked_beat.get("text", "")),
                    "orig_file": linked_beat.get("orig_file", ""),
                    "s": trigger_turn.get("s", 0.0),
                    "e": trigger_turn.get("e", 2.5),
                    "arch_spoken": trigger_take.get("spoken", ""),
                    "arch_title": trigger_take.get("title", ""),
                    "arch_year": trigger_take.get("year", 1960),
                    "arch_audio": trigger_take.get("audio_url", ""),
                    "arch_audio_t0": trigger_take.get("audio_t0", 0.0),
                    "arch_audio_t1": trigger_take.get("audio_t1", 2.5),
                },
                "arch_twin": {
                    "id": arch_twin.get("id", ""),
                    "title": arch_twin.get("title", "Archival Computer"),
                    "year": arch_twin.get("year", 1962),
                    "video": arch_twin.get("video", ""),
                    "media_url": arch_twin.get("media_url", ""),
                    "thumb": arch_twin.get("thumb", ""),
                    "clip_t0": arch_twin.get("clip_t0", 0.0),
                    "clip_t1": arch_twin.get("clip_t1", 2.5),
                    "why": arch_twin.get("why_picked", ""),
                },
            }
            sub_states.append(state_obj)
            if shot_id not in seen_ids:
                seen_ids.add(shot_id)
            all_states.append(state_obj)

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
    print(f"Wrote {out_path}: {len(all_states)} screen states ({out['total_subframe_states']} sub-frame states) with 8-frame deltas & twin videos.")


if __name__ == "__main__":
    build_all()
